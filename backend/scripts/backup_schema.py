"""Validate persisted backup data before opening the restore target."""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, Json, StringConstraints, model_validator

CaseId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=36)]
Version = Annotated[int, Field(strict=True, gt=0)]


class CaseRow(BaseModel):
    id: CaseId
    scenario: str = Field(min_length=1, max_length=128)
    challenge: str
    subject_label: str = Field(max_length=255)
    status: str = Field(min_length=1, max_length=48)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InterviewRow(BaseModel):
    case_id: CaseId
    stage: Literal["basic", "advanced"]
    questions_json: Json[list[dict[str, Any]]]
    answers_json: Json[dict[str, str | list[str]]]
    updated_at: datetime | None = None


class ReportFields(BaseModel):
    case_id: CaseId
    stage: Literal["basic", "final"]
    title: str = Field(max_length=512)
    summary: str
    content_json: Json[dict[str, Any]]
    version: Version


class ReportRow(ReportFields):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RevisionRow(ReportFields):
    archived_at: datetime | None = None


class BackupData(BaseModel):
    # Missing sections must not be interpreted as an intentionally empty backup.
    cases: list[CaseRow]
    interview_sessions: list[InterviewRow]
    reports: list[ReportRow]
    report_revisions: list[RevisionRow]
    counts: dict[str, Annotated[int, Field(strict=True, ge=0)]] | None = None

    @model_validator(mode="after")
    def validate_relations(self) -> "BackupData":
        case_ids = {row.id for row in self.cases}
        for section, fields in (
            ("cases", ("id",)),
            ("interview_sessions", ("case_id", "stage")),
            ("reports", ("case_id", "stage")),
            ("report_revisions", ("case_id", "stage", "version")),
        ):
            rows = getattr(self, section)
            seen: set[tuple[Any, ...]] = set()
            for index, row in enumerate(rows):
                if section != "cases" and row.case_id not in case_ids:
                    raise ValueError(f"{section}[{index}] references unknown case_id {row.case_id}")
                key = tuple(getattr(row, field) for field in fields)
                if key in seen:
                    raise ValueError(f"{section}[{index}] has duplicate key {key}")
                seen.add(key)

        if self.counts is not None:
            for section in ("cases", "interview_sessions", "reports", "report_revisions"):
                if self.counts.get(section) != len(getattr(self, section)):
                    raise ValueError(f"counts.{section} does not match the number of rows")
        return self
