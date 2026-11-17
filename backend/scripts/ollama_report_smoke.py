"""手动验证本地模型能生成符合页面结构的基础报告。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.diagnosis import generate_basic_report


async def main() -> None:
    answers = {
        "role_and_context": "我负责一家小型内容团队的日常运营。",
        "current_workflow": "同事把客户反馈发到群里，我每天下班前手工整理到表格并分类。",
        "impact": "反馈经常遗漏，重复问题不能及时发现，也很难判断优先级。",
        "people": "内容编辑、客户运营和我都会使用整理结果。",
        "data_and_tools": "目前有聊天记录、Excel 表格和历史处理结果。",
        "desired_outcome": "希望自动汇总反馈、识别重复主题并给出有依据的优先级建议。",
        "constraints": "客户信息不能离开本地，重要判断必须人工确认。",
    }
    report = await generate_basic_report(
        "内容与知识",
        "每天人工整理大量客户反馈，难以及时发现真正重要的问题",
        answers,
    )
    print(
        {
            "generation_mode": report.get("generation_mode"),
            "pain_points": len(report.get("pain_points", [])),
            "opportunities": len(report.get("opportunities", [])),
            "has_diagnosis": bool(report.get("diagnosis")),
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
