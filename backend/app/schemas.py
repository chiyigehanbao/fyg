"""
Pydantic 模型：API 请求/响应边界校验。
"""

from datetime import datetime
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.services.answer_quality import answer_text


class DiagnosisCaseCreate(BaseModel):
    """创建一次 AI 赋能诊断。"""

    scenario: str = Field(min_length=1, max_length=128)
    challenge: str = Field(min_length=8, max_length=20_000)
    subject_label: str = Field(default="", max_length=255)

    @field_validator("challenge")
    @classmethod
    def challenge_must_describe_a_problem(cls, value: str) -> str:
        text = value.strip()
        semantic_chars = re.findall(r"[\u4e00-\u9fffA-Za-z]", text)
        if len(semantic_chars) < 4 or not answer_text(text):
            raise ValueError("请用一句话描述真实问题，不能只填写数字或符号")
        return text


class DiagnosisCaseRead(BaseModel):
    id: str
    scenario: str
    challenge: str
    subject_label: str = ""
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class InterviewQuestion(BaseModel):
    id: str
    title: str
    prompt: str
    hint: str = ""
    type: Literal["text", "textarea", "single", "multi"] = "textarea"
    options: list[str] = Field(default_factory=list)
    required: bool = True


class InterviewRead(BaseModel):
    case_id: str
    stage: Literal["basic", "advanced"]
    questions: list[InterviewQuestion] = Field(default_factory=list)
    answers: dict[str, str | list[str]] = Field(default_factory=dict)


class InterviewPatchRequest(BaseModel):
    answers: dict[str, str | list[str]] = Field(default_factory=dict)


class DiagnosisReportRead(BaseModel):
    case_id: str
    stage: Literal["basic", "final"]
    title: str
    summary: str = ""
    content: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime | None = None


class ReportGenerateRequest(BaseModel):
    note: str = Field(default="", max_length=8000)
