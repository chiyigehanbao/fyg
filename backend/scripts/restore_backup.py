"""Restore an ai-cocreator JSON backup into the configured database.

The command is intentionally conservative:
- default mode is a dry run;
- writes require --apply;
- --replace previews the deletion scope; writes still require --apply;
- single-case exports only replace their own case and related rows.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.backup_schema import BackupData


def _configure_database_url(database_url: str | None) -> None:
    if database_url:
        os.environ["DATABASE_URL"] = database_url


def _load_app_modules():
    from app.database import Base, SessionLocal, engine
    from app.models import DiagnosisCase, DiagnosisReport, DiagnosisReportRevision, InterviewSession

    return Base, SessionLocal, engine, DiagnosisCase, InterviewSession, DiagnosisReport, DiagnosisReportRevision


def _load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Invalid backup payload: root must be an object.")
    schema = payload.get("schema")
    if schema == "ai-cocreator.backup.v1":
        return {**payload, "source_schema": schema}
    if schema == "ai-cocreator.case-export.v1":
        return _case_export_to_backup_payload(payload)
    raise ValueError("Unsupported backup schema. Expected ai-cocreator.backup.v1 or ai-cocreator.case-export.v1.")


def _json_text(value: Any, fallback: str) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return fallback
    return json.dumps(value, ensure_ascii=False)


def _case_export_to_backup_payload(payload: dict[str, Any]) -> dict[str, Any]:
    row = payload.get("case")
    if not isinstance(row, dict):
        raise ValueError("Invalid case export payload: case must be an object.")
    case_id = _as_text(row.get("id")).strip()
    if not case_id:
        raise ValueError("Invalid case export payload: case.id is required.")

    for section, fields in (
        ("interview_sessions", {"questions": list, "answers": dict}),
        ("reports", {"content": dict}),
        ("report_revisions", {"content": dict}),
    ):
        items = payload.get(section)
        if not isinstance(items, list):
            raise ValueError(f"Invalid case export payload: {section} must be an array.")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"Invalid case export payload: {section}[{index}] must be an object.")
            for field, expected_type in fields.items():
                if not isinstance(item.get(field), expected_type):
                    raise ValueError(f"Invalid case export payload: {section}[{index}].{field} has an invalid type.")

    sessions = [
        {
            "case_id": case_id,
            "stage": item.get("stage"),
            "questions_json": _json_text(item.get("questions"), "[]"),
            "answers_json": _json_text(item.get("answers"), "{}"),
            "updated_at": item.get("updated_at"),
        }
        for item in payload.get("interview_sessions") or []
    ]
    reports = [
        {
            "case_id": case_id,
            "stage": item.get("stage"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "content_json": _json_text(item.get("content"), "{}"),
            "version": item.get("version"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }
        for item in payload.get("reports") or []
    ]
    revisions = [
        {
            "case_id": case_id,
            "stage": item.get("stage"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "content_json": _json_text(item.get("content"), "{}"),
            "version": item.get("version"),
            "archived_at": item.get("archived_at"),
        }
        for item in payload.get("report_revisions") or []
    ]
    return {
        "schema": "ai-cocreator.backup.v1",
        "created_at": payload.get("exported_at"),
        "source_schema": "ai-cocreator.case-export.v1",
        "counts": {
            "cases": 1,
            "interview_sessions": len(sessions),
            "reports": len(reports),
            "report_revisions": len(revisions),
        },
        "cases": [row],
        "interview_sessions": sessions,
        "reports": reports,
        "report_revisions": revisions,
    }


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _as_int(value: Any, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _counts(payload: dict[str, Any]) -> dict[str, int]:
    return {
        "cases": len(payload.get("cases") or []),
        "interview_sessions": len(payload.get("interview_sessions") or []),
        "reports": len(payload.get("reports") or []),
        "report_revisions": len(payload.get("report_revisions") or []),
    }


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    validated = BackupData.model_validate(payload)
    return {**payload, **validated.model_dump(mode="json", round_trip=True)}


def _scoped_query(db: Any, model: Any, case_ids: list[str] | None) -> Any:
    query = db.query(model)
    if case_ids is not None:
        column = model.case_id if hasattr(model, "case_id") else model.id
        query = query.filter(column.in_(case_ids))
    return query


def _row_counts(db: Any, models: tuple[Any, ...], case_ids: list[str] | None = None) -> dict[str, int]:
    existing_tables = set(inspect(db.connection()).get_table_names())
    sections = ("cases", "interview_sessions", "reports", "report_revisions")
    return {
        section: _scoped_query(db, model, case_ids).count() if model.__tablename__ in existing_tables else 0
        for section, model in zip(sections, models)
    }


def _upsert_case(db: Any, model: Any, item: dict[str, Any]) -> None:
    case_id = _as_text(item.get("id")).strip()
    if not case_id:
        raise ValueError("Case row is missing id.")
    row = db.get(model, case_id) or model(id=case_id)
    row.scenario = _as_text(item.get("scenario"))
    row.challenge = _as_text(item.get("challenge"))
    row.subject_label = _as_text(item.get("subject_label"))
    row.status = _as_text(item.get("status"), "basic_collecting")
    row.created_at = _parse_dt(item.get("created_at")) or row.created_at
    row.updated_at = _parse_dt(item.get("updated_at")) or row.updated_at
    db.add(row)


def _upsert_by_keys(db: Any, model: Any, keys: dict[str, Any], values: dict[str, Any]) -> None:
    row = db.query(model).filter_by(**keys).one_or_none()
    if row is None:
        row = model(**keys)
    for key, value in values.items():
        if value is None:
            continue
        setattr(row, key, value)
    db.add(row)


def restore_backup(input_path: Path, *, database_url: str | None = None, apply: bool = False, replace: bool = False) -> dict[str, Any]:
    """Restore a backup payload and return a small operation summary."""

    _configure_database_url(database_url)
    payload = _load_payload(input_path)
    payload = _validate_payload(payload)
    incoming = _counts(payload)
    source_schema = payload["source_schema"]
    replacement_case_ids = [item["id"] for item in payload["cases"]] if source_schema == "ai-cocreator.case-export.v1" else None
    Base, SessionLocal, engine, DiagnosisCase, InterviewSession, DiagnosisReport, DiagnosisReportRevision = _load_app_modules()
    models = (DiagnosisCase, InterviewSession, DiagnosisReport, DiagnosisReportRevision)

    if apply:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        before = _row_counts(db, models)
        summary = {
            "mode": "apply" if apply else "dry-run",
            "replace": replace,
            "source_schema": source_schema,
            "replacement_scope": ("cases" if replacement_case_ids is not None else "all") if replace else "none",
            "replacement_case_ids": replacement_case_ids if replace else [],
            "to_delete": _row_counts(db, models, replacement_case_ids) if replace else {key: 0 for key in incoming},
            "incoming": incoming,
            "before": before,
            "after": before,
        }
        if not apply:
            return summary

        if replace:
            for model in (DiagnosisReportRevision, DiagnosisReport, InterviewSession, DiagnosisCase):
                _scoped_query(db, model, replacement_case_ids).delete(synchronize_session=False)
            db.flush()

        for item in payload.get("cases") or []:
            _upsert_case(db, DiagnosisCase, item)
        db.flush()

        for item in payload.get("interview_sessions") or []:
            keys = {
                "case_id": _as_text(item.get("case_id")),
                "stage": _as_text(item.get("stage")),
            }
            _upsert_by_keys(
                db,
                InterviewSession,
                keys,
                {
                    "questions_json": _as_text(item.get("questions_json"), "[]"),
                    "answers_json": _as_text(item.get("answers_json"), "{}"),
                    "updated_at": _parse_dt(item.get("updated_at")),
                },
            )

        for item in payload.get("reports") or []:
            keys = {
                "case_id": _as_text(item.get("case_id")),
                "stage": _as_text(item.get("stage")),
            }
            _upsert_by_keys(
                db,
                DiagnosisReport,
                keys,
                {
                    "title": _as_text(item.get("title")),
                    "summary": _as_text(item.get("summary")),
                    "content_json": _as_text(item.get("content_json"), "{}"),
                    "version": _as_int(item.get("version")),
                    "created_at": _parse_dt(item.get("created_at")),
                    "updated_at": _parse_dt(item.get("updated_at")),
                },
            )

        for item in payload.get("report_revisions") or []:
            keys = {
                "case_id": _as_text(item.get("case_id")),
                "stage": _as_text(item.get("stage")),
                "version": _as_int(item.get("version")),
            }
            _upsert_by_keys(
                db,
                DiagnosisReportRevision,
                keys,
                {
                    "title": _as_text(item.get("title")),
                    "summary": _as_text(item.get("summary")),
                    "content_json": _as_text(item.get("content_json"), "{}"),
                    "archived_at": _parse_dt(item.get("archived_at")),
                },
            )

        db.commit()
        summary["after"] = _row_counts(db, models)
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restore an ai-cocreator JSON backup.")
    parser.add_argument("--input", required=True, type=Path, help="Path to backup JSON.")
    parser.add_argument("--database-url", help="Override DATABASE_URL, e.g. sqlite:///tmp.db.")
    parser.add_argument("--apply", action="store_true", help="Write data. Omit for dry-run.")
    parser.add_argument("--replace", action="store_true", help="Replace the exported case, or all diagnosis data for a full backup. Omit --apply to preview.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    summary = restore_backup(args.input, database_url=args.database_url, apply=args.apply, replace=args.replace)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Dry run only. Re-run with --apply to write data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
