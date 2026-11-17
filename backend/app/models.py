"""
SQLAlchemy 模型定义。

说明：首期仅「项目/会话」实体，字段对应管理端列表与详情所需展示。
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiagnosisCase(Base):
    """一次完整的 AI 赋能诊断，贯穿基础报告与最终方案。"""

    __tablename__ = "diagnosis_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario: Mapped[str] = mapped_column(String(128))
    challenge: Mapped[str] = mapped_column(Text)
    subject_label: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(48), default="basic_collecting", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class InterviewSession(Base):
    """基础或进阶访谈；问题与答案均为结构化 JSON。"""

    __tablename__ = "interview_sessions"
    __table_args__ = (
        UniqueConstraint("case_id", "stage", name="uq_interview_case_stage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnosis_cases.id", ondelete="CASCADE"),
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(24))
    questions_json: Mapped[str] = mapped_column(Text, default="[]")
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DiagnosisReport(Base):
    """结构化在线报告；Word/PDF 等导出均从同一内容派生。"""

    __tablename__ = "diagnosis_reports"
    __table_args__ = (
        UniqueConstraint("case_id", "stage", name="uq_report_case_stage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnosis_cases.id", ondelete="CASCADE"),
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DiagnosisReportRevision(Base):
    """报告旧版本快照，用于保留每次重新生成前的内容。"""

    __tablename__ = "diagnosis_report_revisions"
    __table_args__ = (
        UniqueConstraint("case_id", "stage", "version", name="uq_report_revision_case_stage_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("diagnosis_cases.id", ondelete="CASCADE"),
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
