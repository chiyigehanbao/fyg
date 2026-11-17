"""Shared low-information answer detection."""

from __future__ import annotations

import re
from typing import Any

LOW_INFORMATION_PATTERNS = (
    "暂不确定",
    "暂未明确",
    "待确认",
    "不知道",
    "不清楚",
    "没有",
    "无",
    "随便",
    "测试",
)


def is_low_information_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    compact = re.sub(r"\s+", "", text)
    semantic_chars = re.findall(r"[\u4e00-\u9fffA-Za-z]", compact)
    if len(semantic_chars) < 4:
        return True
    if re.fullmatch(r"[\d\W_]+", compact):
        return True
    if len(set(compact)) <= 2 and len(compact) >= 4:
        return True
    lowered = compact.lower()
    if lowered in {"na", "n/a", "none", "null", "todo", "test"}:
        return True
    if any(pattern in compact for pattern in LOW_INFORMATION_PATTERNS) and len(semantic_chars) < 10:
        return True
    if re.fullmatch(r"这是关于.+的(?:真实|进阶)?回答", compact):
        return True
    return False


def answer_text(value: Any) -> str:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if not is_low_information_text(str(item))]
        return "、".join(parts)
    text = str(value or "").strip()
    return "" if is_low_information_text(text) else text
