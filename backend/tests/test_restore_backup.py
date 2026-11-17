import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

import pytest


def _backup_payload(case_id: str = "case-restore-1") -> dict:
    return {
        "schema": "ai-cocreator.backup.v1",
        "created_at": "2026-09-12T00:00:00+00:00",
        "database": {"type": "sqlite"},
        "counts": {
            "cases": 1,
            "interview_sessions": 1,
            "reports": 1,
            "report_revisions": 1,
        },
        "cases": [
            {
                "id": case_id,
                "scenario": "business_growth",
                "challenge": "线索充足但转化率低，销售流程缺少稳定复盘。",
                "subject_label": "本地服务团队",
                "status": "final_report_ready",
                "created_at": "2026-09-12T00:01:00+00:00",
                "updated_at": "2026-09-12T00:02:00+00:00",
            }
        ],
        "interview_sessions": [
            {
                "case_id": case_id,
                "stage": "basic",
                "questions_json": '[{"id":"q1","prompt":"问题"}]',
                "answers_json": '{"q1":"每周复盘转化漏斗"}',
                "updated_at": "2026-09-12T00:03:00+00:00",
            }
        ],
        "reports": [
            {
                "case_id": case_id,
                "stage": "final",
                "title": "增长诊断方案",
                "summary": "聚焦线索分层和成交动作。",
                "content_json": '{"sections":[]}',
                "version": 2,
                "created_at": "2026-09-12T00:04:00+00:00",
                "updated_at": "2026-09-12T00:05:00+00:00",
            }
        ],
        "report_revisions": [
            {
                "case_id": case_id,
                "stage": "final",
                "title": "增长诊断方案 v1",
                "summary": "旧版本。",
                "content_json": '{"sections":["old"]}',
                "version": 1,
                "archived_at": "2026-09-12T00:06:00+00:00",
            }
        ],
    }


def _case_export_payload(case_id: str = "case-restore-1") -> dict:
    return {
        "schema": "ai-cocreator.case-export.v1",
        "exported_at": "2026-09-12T00:00:00+00:00",
        "case": {
            "id": case_id,
            "scenario": "business_growth",
            "challenge": "线索充足但转化率低，销售流程缺少稳定复盘。",
            "subject_label": "本地服务团队",
            "status": "final_report_ready",
            "created_at": "2026-09-12T00:01:00+00:00",
            "updated_at": "2026-09-12T00:02:00+00:00",
        },
        "interview_sessions": [
            {
                "stage": "basic",
                "questions": [{"id": "q1", "prompt": "问题"}],
                "answers": {"q1": "每周复盘转化漏斗"},
                "updated_at": "2026-09-12T00:03:00+00:00",
            }
        ],
        "reports": [
            {
                "stage": "final",
                "title": "增长诊断方案",
                "summary": "聚焦线索分层和成交动作。",
                "content": {"sections": []},
                "version": 2,
                "created_at": "2026-09-12T00:04:00+00:00",
                "updated_at": "2026-09-12T00:05:00+00:00",
            }
        ],
        "report_revisions": [
            {
                "stage": "final",
                "title": "增长诊断方案 v1",
                "summary": "旧版本。",
                "content": {"sections": ["old"]},
                "version": 1,
                "archived_at": "2026-09-12T00:06:00+00:00",
            }
        ],
    }


def _workspace_tmp(name: str) -> Path:
    root = Path(__file__).resolve().parents[1] / ".test-tmp" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


@pytest.fixture
def restore_dir():
    root = Path(__file__).resolve().parents[1] / ".test-tmp"
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="restore-", dir=root) as work_dir:
        yield Path(work_dir)


def _run_restore(work_dir: Path, backup_path: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    db_path = work_dir / "restore.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    return subprocess.run(
        [
            sys.executable,
            "scripts/restore_backup.py",
            "--input",
            str(backup_path),
            *args,
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


def _summary(output: str) -> dict:
    return json.loads(output.split("\nDry run only.")[0])


def test_restore_backup_dry_run_does_not_write() -> None:
    work_dir = _workspace_tmp("restore-dry-run")
    try:
        backup_path = work_dir / "backup.json"
        backup_path.write_text(json.dumps(_backup_payload(), ensure_ascii=False), encoding="utf-8")

        first = _summary(_run_restore(work_dir, backup_path).stdout)
        second = _summary(_run_restore(work_dir, backup_path).stdout)

        assert first["mode"] == "dry-run"
        assert first["incoming"]["cases"] == 1
        assert first["before"]["cases"] == 0
        assert second["before"]["cases"] == 0
        with closing(sqlite3.connect(work_dir / "restore.db")) as db:
            assert db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall() == []
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_restore_backup_apply_is_idempotent_and_replace_clears_extra_rows() -> None:
    work_dir = _workspace_tmp("restore-apply")
    try:
        backup_path = work_dir / "backup.json"
        backup_path.write_text(json.dumps(_backup_payload(), ensure_ascii=False), encoding="utf-8")
        extra_path = work_dir / "extra-backup.json"
        extra_path.write_text(json.dumps(_backup_payload("case-extra"), ensure_ascii=False), encoding="utf-8")

        first = _summary(_run_restore(work_dir, backup_path, "--apply").stdout)
        second = _summary(_run_restore(work_dir, backup_path, "--apply").stdout)
        with_extra = _summary(_run_restore(work_dir, extra_path, "--apply").stdout)
        preview = _summary(_run_restore(work_dir, backup_path, "--replace").stdout)
        replaced = _summary(_run_restore(work_dir, backup_path, "--apply", "--replace").stdout)

        assert first["after"]["cases"] == 1
        assert second["after"]["cases"] == 1
        assert second["after"]["reports"] == 1
        assert with_extra["after"]["cases"] == 2
        assert replaced["replace"] is True
        assert replaced["after"]["cases"] == 1
        assert preview["replacement_scope"] == "all"
        assert preview["before"] == preview["after"] == preview["to_delete"]
        assert replaced["to_delete"] == preview["to_delete"]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_restore_accepts_single_case_export_payload() -> None:
    work_dir = _workspace_tmp("restore-case-export")
    try:
        backup_path = work_dir / "case-export.json"
        backup_path.write_text(json.dumps(_case_export_payload(), ensure_ascii=False), encoding="utf-8")

        dry_run = _summary(_run_restore(work_dir, backup_path).stdout)
        applied = _summary(_run_restore(work_dir, backup_path, "--apply").stdout)
        second_apply = _summary(_run_restore(work_dir, backup_path, "--apply").stdout)

        assert dry_run["incoming"] == {
            "cases": 1,
            "interview_sessions": 1,
            "reports": 1,
            "report_revisions": 1,
        }
        assert applied["after"]["cases"] == 1
        assert applied["after"]["reports"] == 1
        assert applied["after"]["report_revisions"] == 1
        assert second_apply["after"] == applied["after"]
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def test_restore_backup_rejects_orphan_related_rows_before_writing() -> None:
    work_dir = _workspace_tmp("restore-invalid")
    try:
        payload = _backup_payload()
        payload["cases"] = []
        backup_path = work_dir / "invalid-backup.json"
        backup_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        db_path = work_dir / "restore.db"
        env = os.environ.copy()
        env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/restore_backup.py",
                "--input",
                str(backup_path),
                "--apply",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            text=True,
            capture_output=True,
        )

        assert result.returncode != 0
        assert "references unknown case_id case-restore-1" in result.stderr

        valid_backup_path = work_dir / "valid-backup.json"
        valid_backup_path.write_text(json.dumps(_backup_payload(), ensure_ascii=False), encoding="utf-8")
        dry_run = _summary(_run_restore(work_dir, valid_backup_path).stdout)
        assert dry_run["before"]["cases"] == 0
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _write_backup(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _snapshot(work_dir: Path, case_id: str | None = None) -> dict:
    with closing(sqlite3.connect(work_dir / "restore.db")) as db:
        return {
            table: db.execute(
                f"SELECT * FROM {table}" + (f" WHERE {column} = ?" if case_id else "") + " ORDER BY id",
                (case_id,) if case_id else (),
            ).fetchall()
            for table, column in (
                ("diagnosis_cases", "id"),
                ("interview_sessions", "case_id"),
                ("diagnosis_reports", "case_id"),
                ("diagnosis_report_revisions", "case_id"),
            )
        }


def test_replace_single_case_preserves_every_other_case_and_removes_stale_rows(restore_dir: Path) -> None:
    target = _backup_payload()
    for section, stage in (("interview_sessions", "advanced"), ("reports", "basic"), ("report_revisions", "basic")):
        target[section].append({**target[section][0], "stage": stage})
        target["counts"][section] += 1
    _run_restore(restore_dir, _write_backup(restore_dir / "target.json", target), "--apply")
    _run_restore(restore_dir, _write_backup(restore_dir / "other.json", _backup_payload("other-case")), "--apply")
    before = _snapshot(restore_dir)
    other_before = _snapshot(restore_dir, "other-case")

    incoming = _case_export_payload()
    incoming["case"]["subject_label"] = "Restored customer"
    incoming["reports"][0]["title"] = "Restored report"
    path = _write_backup(restore_dir / "case-export.json", incoming)
    preview = _summary(_run_restore(restore_dir, path, "--replace").stdout)
    assert preview["mode"] == "dry-run"
    assert preview["replacement_scope"] == "cases"
    assert preview["replacement_case_ids"] == ["case-restore-1"]
    assert preview["to_delete"] == {"cases": 1, "interview_sessions": 2, "reports": 2, "report_revisions": 2}
    assert _snapshot(restore_dir) == before

    result = _summary(_run_restore(restore_dir, path, "--apply", "--replace").stdout)
    assert result["to_delete"] == preview["to_delete"]
    assert result["after"] == {"cases": 2, "interview_sessions": 2, "reports": 2, "report_revisions": 2}
    assert _snapshot(restore_dir, "other-case") == other_before
    with closing(sqlite3.connect(restore_dir / "restore.db")) as db:
        assert db.execute("SELECT subject_label FROM diagnosis_cases WHERE id = ?", ("case-restore-1",)).fetchone() == ("Restored customer",)
        assert db.execute("SELECT stage, title FROM diagnosis_reports WHERE case_id = ?", ("case-restore-1",)).fetchall() == [("final", "Restored report")]


@pytest.mark.parametrize("corruption", [
    "missing_section", "null_section", "invalid_case", "missing_case_id", "duplicate_case",
    "duplicate_report", "wrong_counts", "invalid_json", "wrong_json_type", "invalid_stage",
    "invalid_version", "invalid_timestamp", "case_export_invalid_row", "case_export_missing_section",
    "case_export_missing_content",
])
def test_invalid_backup_cannot_delete_existing_data(restore_dir: Path, corruption: str) -> None:
    _run_restore(restore_dir, _write_backup(restore_dir / "valid.json", _backup_payload()), "--apply")
    before = _snapshot(restore_dir)
    payload = _case_export_payload() if corruption.startswith("case_export") else _backup_payload()
    if corruption == "missing_section":
        del payload["cases"]
    elif corruption == "null_section":
        payload["cases"] = None
    elif corruption == "invalid_case":
        payload["cases"] = [42]
    elif corruption == "missing_case_id":
        del payload["cases"][0]["id"]
    elif corruption == "duplicate_case":
        payload["cases"].append(payload["cases"][0].copy())
    elif corruption == "duplicate_report":
        payload["reports"].append(payload["reports"][0].copy())
    elif corruption == "wrong_counts":
        payload["counts"]["reports"] = 0
    elif corruption == "invalid_json":
        payload["reports"][0]["content_json"] = "{broken"
    elif corruption == "wrong_json_type":
        payload["interview_sessions"][0]["answers_json"] = "[]"
    elif corruption == "invalid_stage":
        payload["reports"][0]["stage"] = "advanced"
    elif corruption == "invalid_version":
        payload["reports"][0]["version"] = "not-a-version"
    elif corruption == "invalid_timestamp":
        payload["cases"][0]["created_at"] = "not-a-date"
    elif corruption == "case_export_invalid_row":
        payload["reports"].append(None)
    elif corruption == "case_export_missing_section":
        del payload["report_revisions"]
    elif corruption == "case_export_missing_content":
        del payload["reports"][0]["content"]
    path = _write_backup(restore_dir / "invalid.json", payload)
    for flags in (("--replace",), ("--apply", "--replace")):
        result = _run_restore(restore_dir, path, *flags, check=False)
        assert result.returncode != 0, result.stdout
        assert _snapshot(restore_dir) == before


def test_replacement_rolls_back_deletes_when_a_later_insert_fails(restore_dir: Path) -> None:
    _run_restore(restore_dir, _write_backup(restore_dir / "before.json", _backup_payload()), "--apply")
    before = _snapshot(restore_dir)
    with closing(sqlite3.connect(restore_dir / "restore.db")) as db, db:
        db.execute("""
            CREATE TRIGGER reject_restore_report BEFORE INSERT ON diagnosis_reports
            BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END
        """)
    path = _write_backup(restore_dir / "replacement.json", _backup_payload("new-case"))
    result = _run_restore(restore_dir, path, "--apply", "--replace", check=False)
    assert result.returncode != 0
    assert "simulated storage failure" in result.stderr
    assert _snapshot(restore_dir) == before
