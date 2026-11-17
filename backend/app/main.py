"""
FastAPI 应用入口：挂载诊断路由、CORS，并在启动时创建数据表。
"""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy import text

from app.database import Base, DATABASE_URL, SessionLocal, engine
from app.config import load_settings
from app.models import DiagnosisCase, DiagnosisReport, DiagnosisReportRevision, InterviewSession  # noqa: F401
from app.routers import diagnosis
from app.services.llm import model_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：创建缺失的数据表。"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI 共创官 API", lifespan=lifespan)
settings = load_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api")

API_CAPABILITIES = [
    "diagnosis_v1",
    "system_status",
    "model_status_error",
    "report_docx_export",
    "report_pdf_export",
    "case_json_export",
    "frontend_static_hosting",
]


def _frontend_dist_dir() -> Path | None:
    configured = Path(settings.frontend_dist_dir)
    dist_dir = configured if configured.is_absolute() else (Path(__file__).resolve().parents[1] / configured)
    dist_dir = dist_dir.resolve()
    if (dist_dir / "index.html").is_file():
        return dist_dir
    return None


frontend_dist_dir = _frontend_dist_dir()
if frontend_dist_dir is not None and (frontend_dist_dir / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_dist_dir / "assets"),
        name="frontend-assets",
    )


@app.get("/api/health")
def health():
    """存活探测，便于脚本与网关检查。"""
    return {
        "status": "ok",
        "service": "ai-cocreator-api",
        "capabilities": API_CAPABILITIES,
    }


@app.get("/api/model/status")
async def local_model_status():
    """返回本地 Ollama 和所选模型的可用状态。"""
    return await model_status(load_settings())


def _database_overview() -> dict[str, object]:
    parsed = urlparse(DATABASE_URL)
    driver = parsed.scheme or "unknown"
    host = parsed.hostname
    name = parsed.path.lstrip("/") if parsed.path else ""
    if driver.startswith("sqlite"):
        host = "local-file"
        sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
        name = Path(sqlite_path).name or "app.db"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        connected = True
        error = None
    except Exception as exc:  # pragma: no cover - depends on local services
        connected = False
        error = exc.__class__.__name__

    return {
        "connected": connected,
        "driver": driver,
        "host": host,
        "name": name or None,
        "error": error,
    }


def _data_counts() -> dict[str, int]:
    db = SessionLocal()
    try:
        return {
            "cases": int(db.scalar(select(func.count()).select_from(DiagnosisCase)) or 0),
            "interview_sessions": int(db.scalar(select(func.count()).select_from(InterviewSession)) or 0),
            "reports": int(db.scalar(select(func.count()).select_from(DiagnosisReport)) or 0),
            "report_revisions": int(db.scalar(select(func.count()).select_from(DiagnosisReportRevision)) or 0),
        }
    finally:
        db.close()


@app.get("/api/system/status")
async def system_status():
    """运行状态总览，供前端设置页和部署检查使用。"""
    settings = load_settings()
    return {
        "api": {
            "connected": True,
            "status": "ok",
            "service": "ai-cocreator-api",
            "capabilities": API_CAPABILITIES,
        },
        "database": _database_overview(),
        "data": _data_counts(),
        "model": await model_status(settings),
        "config": {
            "ollama_base_url": settings.ollama_base_url,
            "ollama_model": settings.ollama_model,
            "ollama_keep_alive": settings.ollama_keep_alive,
            "cors_allowed_origins": list(settings.cors_allowed_origins),
            "frontend_dist_dir": str(frontend_dist_dir) if frontend_dist_dir else None,
        },
    }


def _dt(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _backup_payload() -> dict[str, object]:
    created_at = datetime.now(UTC)
    db = SessionLocal()
    try:
        cases = db.execute(select(DiagnosisCase).order_by(DiagnosisCase.created_at)).scalars().all()
        sessions = db.execute(select(InterviewSession).order_by(InterviewSession.case_id, InterviewSession.stage)).scalars().all()
        reports = db.execute(select(DiagnosisReport).order_by(DiagnosisReport.case_id, DiagnosisReport.stage)).scalars().all()
        revisions = db.execute(
            select(DiagnosisReportRevision).order_by(
                DiagnosisReportRevision.case_id,
                DiagnosisReportRevision.stage,
                DiagnosisReportRevision.version,
            ),
        ).scalars().all()
        return {
            "schema": "ai-cocreator.backup.v1",
            "created_at": created_at.isoformat(),
            "database": _database_overview(),
            "counts": {
                "cases": len(cases),
                "interview_sessions": len(sessions),
                "reports": len(reports),
                "report_revisions": len(revisions),
            },
            "cases": [
                {
                    "id": row.id,
                    "scenario": row.scenario,
                    "challenge": row.challenge,
                    "subject_label": row.subject_label,
                    "status": row.status,
                    "created_at": _dt(row.created_at),
                    "updated_at": _dt(row.updated_at),
                }
                for row in cases
            ],
            "interview_sessions": [
                {
                    "case_id": row.case_id,
                    "stage": row.stage,
                    "questions_json": row.questions_json,
                    "answers_json": row.answers_json,
                    "updated_at": _dt(row.updated_at),
                }
                for row in sessions
            ],
            "reports": [
                {
                    "case_id": row.case_id,
                    "stage": row.stage,
                    "title": row.title,
                    "summary": row.summary,
                    "content_json": row.content_json,
                    "version": row.version,
                    "created_at": _dt(row.created_at),
                    "updated_at": _dt(row.updated_at),
                }
                for row in reports
            ],
            "report_revisions": [
                {
                    "case_id": row.case_id,
                    "stage": row.stage,
                    "title": row.title,
                    "summary": row.summary,
                    "content_json": row.content_json,
                    "version": row.version,
                    "archived_at": _dt(row.archived_at),
                }
                for row in revisions
            ],
        }
    finally:
        db.close()


@app.get("/api/system/backup")
def system_backup() -> StreamingResponse:
    """导出本地诊断数据备份；只读，不修改数据库。"""
    payload = _backup_payload()
    created_at = datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ")
    filename = f"ai-cocreator-backup-{created_at}.json"
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return StreamingResponse(
        BytesIO(data),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str) -> FileResponse:
    """Serve the built React app when frontend/dist exists."""
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="api route not found")
    if frontend_dist_dir is None:
        raise HTTPException(status_code=404, detail="frontend dist not found")

    requested = (frontend_dist_dir / full_path).resolve()
    if requested.is_file() and requested.is_relative_to(frontend_dist_dir):
        return FileResponse(requested)
    return FileResponse(frontend_dist_dir / "index.html")
