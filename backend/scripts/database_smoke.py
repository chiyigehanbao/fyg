"""Verify the configured database connection and schema without exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, inspect, select, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.database import _engine_options
from app.models import DiagnosisCase, DiagnosisReport, DiagnosisReportRevision, InterviewSession

load_dotenv(BACKEND_DIR / ".env")

REQUIRED_TABLES = (
    DiagnosisCase.__tablename__,
    InterviewSession.__tablename__,
    DiagnosisReport.__tablename__,
    DiagnosisReportRevision.__tablename__,
)


def mask_database_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.username and not parsed.password:
        return database_url
    username = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    auth = f"{username}:***@" if username else "***@"
    return urlunparse(
        (
            parsed.scheme,
            f"{auth}{host}{port}",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ),
    )


def table_counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            "cases": int(connection.scalar(select(func.count()).select_from(DiagnosisCase)) or 0),
            "interview_sessions": int(connection.scalar(select(func.count()).select_from(InterviewSession)) or 0),
            "reports": int(connection.scalar(select(func.count()).select_from(DiagnosisReport)) or 0),
            "report_revisions": int(connection.scalar(select(func.count()).select_from(DiagnosisReportRevision)) or 0),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL") or f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}",
        help="Override DATABASE_URL for this check only.",
    )
    args = parser.parse_args()

    database_url = str(args.database_url)
    engine = create_engine(database_url, **_engine_options(database_url))
    parsed = urlparse(database_url)
    result: dict[str, object] = {
        "connected": False,
        "driver": parsed.scheme or "unknown",
        "database_url": mask_database_url(database_url),
        "required_tables": list(REQUIRED_TABLES),
        "missing_tables": list(REQUIRED_TABLES),
        "counts": {},
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        result["connected"] = True
        existing_tables = set(inspect(engine).get_table_names())
        missing_tables = [name for name in REQUIRED_TABLES if name not in existing_tables]
        result["missing_tables"] = missing_tables
        if not missing_tables:
            result["counts"] = table_counts(engine)
    finally:
        engine.dispose()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["connected"] and not result["missing_tables"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
