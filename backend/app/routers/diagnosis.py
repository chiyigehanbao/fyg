"""AI 共创官：两阶段访谈、初步诊断报告与最终落地方案。"""

from __future__ import annotations

import json
import uuid
from io import BytesIO
from datetime import UTC, datetime
from urllib.parse import quote
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select

from app.deps import DbSession
from app.models import DiagnosisCase, DiagnosisReport, DiagnosisReportRevision, InterviewSession
from app.schemas import (
    DiagnosisCaseCreate,
    DiagnosisCaseRead,
    DiagnosisReportRead,
    InterviewPatchRequest,
    InterviewQuestion,
    InterviewRead,
    ReportGenerateRequest,
)
from app.services.diagnosis import (
    BASIC_QUESTIONS,
    _answer_text,
    generate_advanced_questions,
    generate_basic_report,
    generate_final_report,
)
from app.services.report_export import build_report_docx, build_report_pdf

router = APIRouter(prefix="/cases", tags=["diagnosis"])

CASE_NOT_FOUND = "diagnosis case not found"
INTERVIEW_NOT_FOUND = "interview session not found"
REPORT_NOT_FOUND = "diagnosis report not found"


def _loads_object(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _loads_list(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def _dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _require_case(db: DbSession, case_id: str) -> DiagnosisCase:
    row = db.get(DiagnosisCase, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=CASE_NOT_FOUND)
    return row


def _session(
    db: DbSession,
    case_id: str,
    stage: Literal["basic", "advanced"],
) -> InterviewSession | None:
    stmt = select(InterviewSession).where(
        InterviewSession.case_id == case_id,
        InterviewSession.stage == stage,
    )
    return db.execute(stmt).scalar_one_or_none()


def _report(
    db: DbSession,
    case_id: str,
    stage: Literal["basic", "final"],
) -> DiagnosisReport | None:
    stmt = select(DiagnosisReport).where(
        DiagnosisReport.case_id == case_id,
        DiagnosisReport.stage == stage,
    )
    return db.execute(stmt).scalar_one_or_none()


def _interview_read(row: InterviewSession) -> InterviewRead:
    questions = [InterviewQuestion.model_validate(item) for item in _loads_list(row.questions_json)]
    answers = _loads_object(row.answers_json)
    return InterviewRead(
        case_id=row.case_id,
        stage=row.stage,  # type: ignore[arg-type]
        questions=questions,
        answers=answers,
    )


def _report_read(row: DiagnosisReport) -> DiagnosisReportRead:
    return DiagnosisReportRead(
        case_id=row.case_id,
        stage=row.stage,  # type: ignore[arg-type]
        title=row.title,
        summary=row.summary or "",
        content=_loads_object(row.content_json),
        version=row.version,
        updated_at=row.updated_at,
    )


def _revision_read(row: DiagnosisReportRevision) -> DiagnosisReportRead:
    return DiagnosisReportRead(
        case_id=row.case_id,
        stage=row.stage,  # type: ignore[arg-type]
        title=row.title,
        summary=row.summary or "",
        content=_loads_object(row.content_json),
        version=row.version,
        updated_at=row.archived_at,
    )


def _report_version(
    db: DbSession,
    case_id: str,
    stage: Literal["basic", "final"],
    version: int,
) -> DiagnosisReport | DiagnosisReportRevision | None:
    current = _report(db, case_id, stage)
    if current is not None and current.version == version:
        return current
    stmt = select(DiagnosisReportRevision).where(
        DiagnosisReportRevision.case_id == case_id,
        DiagnosisReportRevision.stage == stage,
        DiagnosisReportRevision.version == version,
    )
    return db.execute(stmt).scalar_one_or_none()


def _missing_required(row: InterviewSession) -> list[str]:
    questions = _loads_list(row.questions_json)
    answers = _loads_object(row.answers_json)
    missing: list[str] = []
    for item in questions:
        if not item.get("required", True):
            continue
        value = answers.get(str(item.get("id", "")), "")
        present = bool(_answer_text(value))
        if not present:
            missing.append(str(item.get("id", "")))
    return missing


def _upsert_report(
    db: DbSession,
    case_id: str,
    stage: Literal["basic", "final"],
    title: str,
    summary: str,
    content: dict[str, Any],
) -> DiagnosisReport:
    row = _report(db, case_id, stage)
    if row is None:
        row = DiagnosisReport(
            case_id=case_id,
            stage=stage,
            title=title,
            summary=summary,
            content_json=_dumps(content),
            version=1,
        )
        db.add(row)
    else:
        db.add(
            DiagnosisReportRevision(
                case_id=row.case_id,
                stage=row.stage,
                title=row.title,
                summary=row.summary,
                content_json=row.content_json,
                version=row.version,
            ),
        )
        row.title = title
        row.summary = summary
        row.content_json = _dumps(content)
        row.version += 1
    return row


def _clone_stage_report(row: DiagnosisReport, case_id: str) -> DiagnosisReport:
    return DiagnosisReport(
        case_id=case_id,
        stage=row.stage,
        title=row.title,
        summary=row.summary,
        content_json=row.content_json,
        version=row.version,
    )


def _clone_report_revision(row: DiagnosisReportRevision, case_id: str) -> DiagnosisReportRevision:
    return DiagnosisReportRevision(
        case_id=case_id,
        stage=row.stage,
        title=row.title,
        summary=row.summary,
        content_json=row.content_json,
        version=row.version,
    )


def _dt(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _case_export_payload(db: DbSession, row: DiagnosisCase) -> dict[str, Any]:
    sessions = db.execute(
        select(InterviewSession)
        .where(InterviewSession.case_id == row.id)
        .order_by(InterviewSession.stage),
    ).scalars().all()
    reports = db.execute(
        select(DiagnosisReport)
        .where(DiagnosisReport.case_id == row.id)
        .order_by(DiagnosisReport.stage),
    ).scalars().all()
    revisions = db.execute(
        select(DiagnosisReportRevision)
        .where(DiagnosisReportRevision.case_id == row.id)
        .order_by(DiagnosisReportRevision.stage, DiagnosisReportRevision.version),
    ).scalars().all()
    return {
        "schema": "ai-cocreator.case-export.v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "case": {
            "id": row.id,
            "scenario": row.scenario,
            "challenge": row.challenge,
            "subject_label": row.subject_label,
            "status": row.status,
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        },
        "interview_sessions": [
            {
                "stage": item.stage,
                "questions": _loads_list(item.questions_json),
                "answers": _loads_object(item.answers_json),
                "updated_at": _dt(item.updated_at),
            }
            for item in sessions
        ],
        "reports": [
            {
                "stage": item.stage,
                "title": item.title,
                "summary": item.summary,
                "content": _loads_object(item.content_json),
                "version": item.version,
                "created_at": _dt(item.created_at),
                "updated_at": _dt(item.updated_at),
            }
            for item in reports
        ],
        "report_revisions": [
            {
                "stage": item.stage,
                "title": item.title,
                "summary": item.summary,
                "content": _loads_object(item.content_json),
                "version": item.version,
                "archived_at": _dt(item.archived_at),
            }
            for item in revisions
        ],
    }


@router.post("")
def create_case(body: DiagnosisCaseCreate, db: DbSession) -> DiagnosisCaseRead:
    case_id = str(uuid.uuid4())
    row = DiagnosisCase(
        id=case_id,
        scenario=body.scenario.strip(),
        challenge=body.challenge.strip(),
        subject_label=body.subject_label.strip(),
        status="basic_collecting",
    )
    interview = InterviewSession(
        case_id=case_id,
        stage="basic",
        questions_json=_dumps(BASIC_QUESTIONS),
        answers_json="{}",
    )
    db.add(row)
    db.add(interview)
    db.commit()
    db.refresh(row)
    return row


@router.get("")
def list_cases(db: DbSession) -> list[DiagnosisCaseRead]:
    stmt = select(DiagnosisCase).order_by(DiagnosisCase.updated_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.get("/{case_id}", responses={404: {"description": "诊断不存在"}})
def get_case(case_id: str, db: DbSession) -> DiagnosisCaseRead:
    return _require_case(db, case_id)


@router.delete("/{case_id}", status_code=204, responses={404: {"description": "诊断不存在"}})
def delete_case(case_id: str, db: DbSession) -> Response:
    _require_case(db, case_id)
    db.execute(delete(DiagnosisReportRevision).where(DiagnosisReportRevision.case_id == case_id))
    db.execute(delete(DiagnosisReport).where(DiagnosisReport.case_id == case_id))
    db.execute(delete(InterviewSession).where(InterviewSession.case_id == case_id))
    db.execute(delete(DiagnosisCase).where(DiagnosisCase.id == case_id))
    db.commit()
    return Response(status_code=204)


@router.get("/{case_id}/export.json", responses={404: {"description": "诊断不存在"}})
def export_case_json(case_id: str, db: DbSession) -> StreamingResponse:
    row = _require_case(db, case_id)
    payload = _case_export_payload(db, row)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%SZ")
    filename = f"ai-cocreator-case-{case_id}-{timestamp}.json"
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return StreamingResponse(
        BytesIO(data),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post("/{case_id}/duplicate", responses={404: {"description": "诊断不存在"}})
def duplicate_case(case_id: str, db: DbSession) -> DiagnosisCaseRead:
    source = _require_case(db, case_id)
    next_id = str(uuid.uuid4())
    clone = DiagnosisCase(
        id=next_id,
        scenario=source.scenario,
        challenge=source.challenge,
        subject_label=f"{source.subject_label} 副本".strip()[:255],
        status=source.status,
    )
    db.add(clone)

    sessions = db.execute(
        select(InterviewSession).where(InterviewSession.case_id == case_id),
    ).scalars()
    for row in sessions:
        db.add(
            InterviewSession(
                case_id=next_id,
                stage=row.stage,
                questions_json=row.questions_json,
                answers_json=row.answers_json,
            ),
        )

    reports = db.execute(
        select(DiagnosisReport).where(DiagnosisReport.case_id == case_id),
    ).scalars()
    for row in reports:
        db.add(_clone_stage_report(row, next_id))

    revisions = db.execute(
        select(DiagnosisReportRevision).where(DiagnosisReportRevision.case_id == case_id),
    ).scalars()
    for row in revisions:
        db.add(_clone_report_revision(row, next_id))

    db.commit()
    db.refresh(clone)
    return clone


@router.get("/{case_id}/interviews/{stage}")
def get_interview(
    case_id: str,
    stage: Literal["basic", "advanced"],
    db: DbSession,
) -> InterviewRead:
    _require_case(db, case_id)
    row = _session(db, case_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
    return _interview_read(row)


@router.patch("/{case_id}/interviews/{stage}")
def patch_interview(
    case_id: str,
    stage: Literal["basic", "advanced"],
    body: InterviewPatchRequest,
    db: DbSession,
) -> InterviewRead:
    case = _require_case(db, case_id)
    row = _session(db, case_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)

    allowed_ids = {str(item.get("id")) for item in _loads_list(row.questions_json)}
    current = _loads_object(row.answers_json)
    for key, value in body.answers.items():
        if key in allowed_ids:
            current[key] = value
    row.answers_json = _dumps(current)
    case.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return _interview_read(row)


@router.post("/{case_id}/reports/basic/generate")
async def generate_basic(
    case_id: str,
    body: ReportGenerateRequest,
    db: DbSession,
) -> DiagnosisReportRead:
    case = _require_case(db, case_id)
    interview = _session(db, case_id, "basic")
    if interview is None:
        raise HTTPException(status_code=404, detail=INTERVIEW_NOT_FOUND)
    missing = _missing_required(interview)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "required answers missing", "question_ids": missing},
        )

    previous_status = case.status
    case.status = "basic_generating"
    db.commit()
    try:
        answers = _loads_object(interview.answers_json)
        content = await generate_basic_report(
            case.scenario,
            case.challenge,
            answers,
            body.note,
        )
        summary = str(content.get("diagnosis", ""))
        report = _upsert_report(
            db,
            case_id,
            "basic",
            "AI 机会诊断报告",
            summary,
            content,
        )
        case.status = "basic_report_ready"
        db.commit()
    except Exception:
        db.rollback()
        case.status = previous_status
        case.updated_at = datetime.now(UTC)
        db.commit()
        raise
    db.refresh(report)
    return _report_read(report)


@router.get("/{case_id}/reports/{stage}")
def get_report(
    case_id: str,
    stage: Literal["basic", "final"],
    db: DbSession,
) -> DiagnosisReportRead:
    _require_case(db, case_id)
    row = _report(db, case_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    return _report_read(row)


@router.get("/{case_id}/reports/{stage}/versions")
def list_report_versions(
    case_id: str,
    stage: Literal["basic", "final"],
    db: DbSession,
) -> list[DiagnosisReportRead]:
    _require_case(db, case_id)
    current = _report(db, case_id, stage)
    if current is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    stmt = (
        select(DiagnosisReportRevision)
        .where(
            DiagnosisReportRevision.case_id == case_id,
            DiagnosisReportRevision.stage == stage,
        )
        .order_by(DiagnosisReportRevision.version.desc())
    )
    previous = [_revision_read(row) for row in db.execute(stmt).scalars().all()]
    return [_report_read(current), *previous]


@router.get("/{case_id}/reports/{stage}/versions/{version}")
def get_report_version(
    case_id: str,
    stage: Literal["basic", "final"],
    version: int,
    db: DbSession,
) -> DiagnosisReportRead:
    _require_case(db, case_id)
    row = _report_version(db, case_id, stage, version)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    if isinstance(row, DiagnosisReportRevision):
        return _revision_read(row)
    return _report_read(row)


def _export_report_file(
    *,
    case: DiagnosisCase,
    row: DiagnosisReport | DiagnosisReportRevision,
    file_format: Literal["docx", "pdf"],
) -> StreamingResponse:
    builders = {
        "docx": (
            build_report_docx,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        "pdf": (build_report_pdf, "application/pdf"),
    }
    builder, media_type = builders[file_format]
    data = builder(
        title=row.title,
        stage=row.stage,
        scenario=case.scenario,
        challenge=case.challenge,
        summary=row.summary or "",
        version=row.version,
        content=_loads_object(row.content_json),
    )
    filename = f"{row.title}-第{row.version}版.{file_format}"
    return StreamingResponse(
        BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/{case_id}/reports/{stage}/export.docx")
def export_report_docx(
    case_id: str,
    stage: Literal["basic", "final"],
    db: DbSession,
) -> StreamingResponse:
    case = _require_case(db, case_id)
    row = _report(db, case_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    return _export_report_file(case=case, row=row, file_format="docx")


@router.get("/{case_id}/reports/{stage}/export.pdf")
def export_report_pdf(
    case_id: str,
    stage: Literal["basic", "final"],
    db: DbSession,
) -> StreamingResponse:
    case = _require_case(db, case_id)
    row = _report(db, case_id, stage)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    return _export_report_file(case=case, row=row, file_format="pdf")


@router.get("/{case_id}/reports/{stage}/versions/{version}/export.docx")
def export_report_version_docx(
    case_id: str,
    stage: Literal["basic", "final"],
    version: int,
    db: DbSession,
) -> StreamingResponse:
    case = _require_case(db, case_id)
    row = _report_version(db, case_id, stage, version)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    return _export_report_file(case=case, row=row, file_format="docx")


@router.get("/{case_id}/reports/{stage}/versions/{version}/export.pdf")
def export_report_version_pdf(
    case_id: str,
    stage: Literal["basic", "final"],
    version: int,
    db: DbSession,
) -> StreamingResponse:
    case = _require_case(db, case_id)
    row = _report_version(db, case_id, stage, version)
    if row is None:
        raise HTTPException(status_code=404, detail=REPORT_NOT_FOUND)
    return _export_report_file(case=case, row=row, file_format="pdf")


@router.post("/{case_id}/advanced/start")
async def start_advanced(case_id: str, db: DbSession) -> InterviewRead:
    case = _require_case(db, case_id)
    basic_interview = _session(db, case_id, "basic")
    basic_report = _report(db, case_id, "basic")
    if basic_interview is None or basic_report is None:
        raise HTTPException(status_code=400, detail="basic report must be ready first")

    existing = _session(db, case_id, "advanced")
    if existing is not None:
        case.status = "advanced_collecting"
        db.commit()
        return _interview_read(existing)

    questions = await generate_advanced_questions(
        case.scenario,
        case.challenge,
        _loads_object(basic_interview.answers_json),
        _loads_object(basic_report.content_json),
    )
    row = InterviewSession(
        case_id=case_id,
        stage="advanced",
        questions_json=_dumps(questions),
        answers_json="{}",
    )
    case.status = "advanced_collecting"
    db.add(row)
    db.commit()
    db.refresh(row)
    return _interview_read(row)


@router.post("/{case_id}/advanced/rebuild")
async def rebuild_advanced(case_id: str, db: DbSession) -> InterviewRead:
    """在尚未作答时重新生成进阶问题，避免误删用户答案。"""
    case = _require_case(db, case_id)
    basic_interview = _session(db, case_id, "basic")
    basic_report = _report(db, case_id, "basic")
    if basic_interview is None or basic_report is None:
        raise HTTPException(status_code=400, detail="basic report must be ready first")

    existing = _session(db, case_id, "advanced")
    if existing is not None:
        current_answers = _loads_object(existing.answers_json)
        if any(
            any(str(item).strip() for item in value) if isinstance(value, list) else bool(str(value).strip())
            for value in current_answers.values()
        ):
            raise HTTPException(status_code=409, detail="advanced answers already exist")

    questions = await generate_advanced_questions(
        case.scenario,
        case.challenge,
        _loads_object(basic_interview.answers_json),
        _loads_object(basic_report.content_json),
    )
    if existing is None:
        existing = InterviewSession(
            case_id=case_id,
            stage="advanced",
            questions_json=_dumps(questions),
            answers_json="{}",
        )
        db.add(existing)
    else:
        existing.questions_json = _dumps(questions)
        existing.answers_json = "{}"
    case.status = "advanced_collecting"
    case.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(existing)
    return _interview_read(existing)


@router.post("/{case_id}/reports/final/generate")
async def generate_final(
    case_id: str,
    body: ReportGenerateRequest,
    db: DbSession,
) -> DiagnosisReportRead:
    case = _require_case(db, case_id)
    basic_interview = _session(db, case_id, "basic")
    advanced_interview = _session(db, case_id, "advanced")
    basic_report = _report(db, case_id, "basic")
    if basic_interview is None or advanced_interview is None or basic_report is None:
        raise HTTPException(status_code=400, detail="advanced interview is not ready")
    missing = _missing_required(advanced_interview)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "required answers missing", "question_ids": missing},
        )

    previous_status = case.status
    case.status = "final_generating"
    db.commit()
    try:
        content = await generate_final_report(
            case.scenario,
            case.challenge,
            _loads_object(basic_interview.answers_json),
            _loads_object(basic_report.content_json),
            _loads_object(advanced_interview.answers_json),
            note=body.note,
            advanced_questions=_loads_list(advanced_interview.questions_json),
        )
        summary = str(content.get("executive_summary", ""))
        report = _upsert_report(
            db,
            case_id,
            "final",
            "专属 AI 落地方案",
            summary,
            content,
        )
        case.status = "final_report_ready"
        db.commit()
    except Exception:
        db.rollback()
        case.status = previous_status
        case.updated_at = datetime.now(UTC)
        db.commit()
        raise
    db.refresh(report)
    return _report_read(report)
