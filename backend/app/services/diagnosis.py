"""两阶段 AI 赋能诊断：问题设计、初步报告与最终方案生成。"""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import load_settings
from app.services.answer_quality import answer_text as _answer_text
from app.services.answer_quality import is_low_information_text as _is_low_information_text
from app.services.llm import ModelError, chat_completion

BASIC_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "role_and_context",
        "title": "你与这个问题",
        "prompt": "你目前的角色是什么？这个问题发生在怎样的团队或业务场景中？",
        "hint": "例如：门店负责人、销售团队、内容工作室、个人创作者。",
        "type": "textarea",
        "options": [],
        "required": True,
    },
    {
        "id": "current_workflow",
        "title": "目前怎样处理",
        "prompt": "从问题出现到处理完成，现在大致要经过哪些步骤？",
        "hint": "按先后顺序描述即可，不需要使用专业术语。",
        "type": "textarea",
        "options": [],
        "required": True,
    },
    {
        "id": "impact",
        "title": "真正造成的影响",
        "prompt": "它主要造成了哪些时间、质量、成本、体验或决策上的影响？",
        "hint": "如果没有准确数字，可以描述频率和体感，不必估算。",
        "type": "textarea",
        "options": [],
        "required": True,
    },
    {
        "id": "people",
        "title": "涉及哪些人",
        "prompt": "谁在处理这个问题？谁会使用结果？还有谁会受到影响？",
        "hint": "例如：一线员工、主管、客户、合作伙伴。",
        "type": "textarea",
        "options": [],
        "required": True,
    },
    {
        "id": "data_and_tools",
        "title": "已有资料和工具",
        "prompt": "目前有哪些文档、数据、知识、软件或设备可能与这个问题有关？",
        "hint": "不确定是否能使用也可以写出来，进阶阶段会继续判断。",
        "type": "textarea",
        "options": [],
        "required": False,
    },
    {
        "id": "desired_outcome",
        "title": "希望看到的改变",
        "prompt": "如果这件事被明显改善，你最希望出现什么具体变化？",
        "hint": "描述可观察的结果，例如更快、更准、更一致或更容易决策。",
        "type": "textarea",
        "options": [],
        "required": True,
    },
    {
        "id": "constraints",
        "title": "不能忽略的边界",
        "prompt": "有哪些隐私、安全、合规、预算、时间或人工审核要求必须遵守？",
        "hint": "暂时没有也可以填写“暂未明确”。",
        "type": "textarea",
        "options": [],
        "required": False,
    },
]


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_object(raw: str) -> dict[str, Any]:
    data = json.loads(_strip_json_fence(raw))
    if not isinstance(data, dict):
        raise ValueError("model output root must be an object")
    return data


def _answer_lines(answers: dict[str, str | list[str]]) -> str:
    lines: list[str] = []
    for question in BASIC_QUESTIONS:
        rendered = _answer_text(answers.get(question["id"], ""))
        lines.append(f"- {question['title']}：{rendered or '未提供'}")
    return "\n".join(lines)


def _sanitize_answers(answers: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
    cleaned: dict[str, str | list[str]] = {}
    for key, value in answers.items():
        if isinstance(value, list):
            items = [str(item).strip() for item in value if not _is_low_information_text(str(item))]
            if items:
                cleaned[key] = items
        else:
            text = _answer_text(value)
            if text:
                cleaned[key] = text
    return cleaned


def _nonempty_answer(
    answers: dict[str, str | list[str]],
    key: str,
    fallback: str,
) -> str:
    text = _answer_text(answers.get(key, ""))
    return text or fallback


def _basic_fallback(
    scenario: str,
    challenge: str,
    answers: dict[str, str | list[str]],
    note: str = "",
) -> dict[str, Any]:
    workflow = _nonempty_answer(answers, "current_workflow", "现有处理流程仍待补充")
    impact = _nonempty_answer(answers, "impact", "影响范围和发生频率仍待确认")
    people = _nonempty_answer(answers, "people", "涉及角色仍待确认")
    outcome = _nonempty_answer(answers, "desired_outcome", "期望成果仍待进一步量化")
    data = _nonempty_answer(answers, "data_and_tools", "可用数据与工具仍待盘点")
    constraints = _nonempty_answer(answers, "constraints", "关键边界尚未明确")
    return {
        "diagnosis": f"当前最值得优先验证的，不是直接采购某个 AI 工具，而是围绕“{challenge[:80]}”找到可重复、可衡量且有人负责的切入点。",
        "pain_points": [
            {"title": "处理过程依赖人工经验", "detail": workflow, "evidence": "来自当前处理方式"},
            {"title": "问题已经影响实际结果", "detail": impact, "evidence": "来自影响描述"},
            {"title": "协作和结果标准可能不一致", "detail": people, "evidence": "来自涉及角色"},
        ],
        "opportunities": [
            {
                "title": "先建立可重复的 AI 辅助流程",
                "description": f"围绕“{scenario}”把输入、判断、输出和人工确认点整理为稳定流程。",
                "priority": "优先验证",
                "why": "能先验证价值，同时避免一次性改造范围过大。",
            },
            {
                "title": "让资料与知识真正可被调用",
                "description": data,
                "priority": "同步准备",
                "why": "AI 的稳定性取决于可用资料、数据质量和权限边界。",
            },
            {
                "title": "用结果指标而不是功能数量验收",
                "description": outcome,
                "priority": "进阶确认",
                "why": "先定义变化，才能决定使用自动化、知识库、分析还是智能助手。",
            },
        ],
        "quick_start": {
            "title": "建议从一个高频场景的小范围验证开始",
            "steps": [
                "选择一段边界清晰、能够人工复核的真实流程",
                "准备少量真实输入与当前处理结果作为对照",
                "定义准确性、耗时、采用率或满意度中的关键指标",
                "完成验证后再决定是否集成现有系统并扩大范围",
            ],
        },
        "readiness": {
            "level": "具备进入深度共创的基础",
            "detail": f"方向已经出现，但仍需确认数据可用性、流程例外与约束。当前边界：{constraints}",
        },
        "missing_information": [
            "真实输入与期望输出的代表性样本",
            "流程中必须由人工判断或审批的节点",
            "当前结果基线与可接受的质量标准",
        ],
        "conclusion": "当前信息足以判断机会方向，但还不足以直接承诺技术形态、周期、预算或收益数字。进入深度共创后再形成专属落地方案。"
        + (f" 本版重点回应：{note.strip()[:240]}" if note.strip() else ""),
        "generation_mode": "guided_fallback",
    }


def _text(value: Any, fallback: str = "") -> str:
    rendered = str(value).strip() if value is not None else ""
    return rendered or fallback


def _string_list(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    items: list[str] = []
    for item in value:
        if isinstance(item, dict):
            heading = next(
                (_text(item.get(key)) for key in ("action", "name", "title", "step") if _text(item.get(key))),
                "",
            )
            detail = next(
                (_text(item.get(key)) for key in ("description", "detail", "goal", "text") if _text(item.get(key))),
                "",
            )
            rendered = "：".join(part for part in (heading, detail) if part)
        else:
            rendered = _text(item)
        items.append(rendered)
    cleaned = [item for item in items if item]
    return cleaned or fallback


def _normalize_basic_report(
    data: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(fallback)
    normalized["diagnosis"] = _text(data.get("diagnosis"), fallback["diagnosis"])

    pain_source = data.get("pain_points") if isinstance(data.get("pain_points"), list) else []
    pains: list[dict[str, str]] = []
    for index, default in enumerate(fallback["pain_points"]):
        candidate = pain_source[index] if index < len(pain_source) and isinstance(pain_source[index], dict) else {}
        pains.append(
            {
                "title": _text(candidate.get("title"), default["title"]),
                "detail": _text(candidate.get("detail"), default["detail"]),
                "evidence": _text(candidate.get("evidence"), default["evidence"]),
            },
        )
    normalized["pain_points"] = pains

    opportunity_source = data.get("opportunities") if isinstance(data.get("opportunities"), list) else []
    opportunities: list[dict[str, str]] = []
    for index, default in enumerate(fallback["opportunities"]):
        candidate = opportunity_source[index] if index < len(opportunity_source) and isinstance(opportunity_source[index], dict) else {}
        opportunities.append(
            {
                "title": _text(candidate.get("title"), default["title"]),
                "description": _text(candidate.get("description"), default["description"]),
                "priority": _text(candidate.get("priority"), default["priority"]),
                "why": _text(candidate.get("why"), default["why"]),
            },
        )
    normalized["opportunities"] = opportunities

    quick = data.get("quick_start") if isinstance(data.get("quick_start"), dict) else {}
    normalized["quick_start"] = {
        "title": _text(quick.get("title"), fallback["quick_start"]["title"]),
        "steps": _string_list(quick.get("steps"), fallback["quick_start"]["steps"]),
    }
    readiness = data.get("readiness") if isinstance(data.get("readiness"), dict) else {}
    normalized["readiness"] = {
        "level": _text(readiness.get("level"), fallback["readiness"]["level"]),
        "detail": _text(readiness.get("detail"), fallback["readiness"]["detail"]),
    }
    normalized["missing_information"] = _string_list(
        data.get("missing_information"),
        fallback["missing_information"],
    )
    normalized["conclusion"] = _text(data.get("conclusion"), fallback["conclusion"])
    normalized["generation_mode"] = "local_ai"
    return normalized


async def generate_basic_report(
    scenario: str,
    challenge: str,
    answers: dict[str, str | list[str]],
    note: str = "",
) -> dict[str, Any]:
    evidence_answers = _sanitize_answers(answers)
    prompt = f"""你是「AI 共创官」的 AI 赋能诊断顾问。请基于用户真实回答输出一份直击痛点、面向用户阅读的初步诊断报告。

场景：{scenario}
最想解决的问题：{challenge}
基础回答：
{_answer_lines(evidence_answers)}
补充偏好：{note or '无'}

只输出 JSON，不要 Markdown。必须严格包含：
{{
  "diagnosis":"一句话核心判断",
  "pain_points":[{{"title":"痛点标题","detail":"具体解释","evidence":"来自哪项回答"}}],
  "opportunities":[{{"title":"机会标题","description":"建议","priority":"优先验证/同步准备/进阶确认","why":"原因"}}],
  "quick_start":{{"title":"建议标题","steps":["步骤"]}},
  "readiness":{{"level":"准备度判断","detail":"说明"}},
  "missing_information":["进阶阶段需要确认的信息"],
  "conclusion":"结论"
}}
约束：pain_points 和 opportunities 各 3 条；quick_start.steps 为 3～5 条；不得编造用户未提供的数字、客户、系统、预算、周期和收益；不确定内容明确写待确认；不要把所有问题都归结为开发软件。"""
    try:
        raw = await chat_completion(
            load_settings(),
            system="你是严谨的 AI 赋能咨询顾问，只根据证据判断，并严格输出 JSON。",
            user=prompt,
            timeout_s=75.0,
            num_predict=2200,
        )
        data = _parse_object(raw)
        return _normalize_basic_report(
            data,
            _basic_fallback(scenario, challenge, evidence_answers, note),
        )
    except (ModelError, ValueError, json.JSONDecodeError, TypeError):
        return _basic_fallback(scenario, challenge, evidence_answers, note)


def _advanced_fallback(
    scenario: str,
    challenge: str,
    basic_answers: dict[str, str | list[str]],
) -> list[dict[str, Any]]:
    desired = _nonempty_answer(basic_answers, "desired_outcome", "期望结果")
    return [
        {
            "id": "advanced_real_example",
            "title": "用真实案例校准",
            "prompt": f"请提供一个最近发生的“{challenge[:60]}”真实案例：输入是什么、怎样处理、最后得到什么结果？",
            "hint": "可隐去敏感信息，重点是让方案理解真实输入与输出。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_rules",
            "title": "业务规则与例外",
            "prompt": "处理过程中有哪些必须遵守的判断规则？最常见的例外情况是什么？",
            "hint": "尤其说明不能让 AI 自行决定的部分。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_data",
            "title": "数据与知识可用性",
            "prompt": f"围绕“{scenario}”，哪些数据或资料可以用于 AI？由谁维护、多久更新、是否包含敏感信息？",
            "hint": "例如表格、文档、聊天记录、业务系统、图片或音视频。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_integration",
            "title": "系统与工作入口",
            "prompt": "方案需要在哪些现有工具或业务系统中工作？用户最自然的使用入口在哪里？",
            "hint": "例如企业微信、网页、客服系统、CRM、内部管理系统。",
            "type": "textarea",
            "options": [],
            "required": False,
        },
        {
            "id": "advanced_human_review",
            "title": "人工确认与失败兜底",
            "prompt": "哪些结果必须人工审核？如果 AI 不确定、答错或服务不可用，应怎样处理？",
            "hint": "说明负责人、升级路径和可接受的等待方式。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_metrics",
            "title": "验收与成功标准",
            "prompt": f"针对“{desired[:80]}”，第一阶段验证成功需要观察哪些指标？目前基线如何？",
            "hint": "没有数字可先说明怎样采集基线，不要猜测。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_scope",
            "title": "首期范围与资源",
            "prompt": "首期最希望覆盖哪些人和场景？明确不做什么？谁负责提供资料、确认规则和验收？",
            "hint": "范围越清楚，方案越容易真正落地。",
            "type": "textarea",
            "options": [],
            "required": True,
        },
        {
            "id": "advanced_constraints",
            "title": "周期、预算与治理",
            "prompt": "对于周期、预算、部署方式、隐私、安全或合规，还有哪些硬性要求？",
            "hint": "暂未确定的内容可以直接说明待确认。",
            "type": "textarea",
            "options": [],
            "required": False,
        },
    ]


async def generate_advanced_questions(
    scenario: str,
    challenge: str,
    basic_answers: dict[str, str | list[str]],
    basic_report: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_answers = _sanitize_answers(basic_answers)
    prompt = f"""根据下面的基础诊断，为深度共创建议恰好 8 个不重复、具体且可作答的问题。
场景：{scenario}
问题：{challenge}
基础回答：{json.dumps(evidence_answers, ensure_ascii=False)}
初步报告：{json.dumps(basic_report, ensure_ascii=False)}

按这个顺序覆盖：真实案例、规则与例外、数据与知识、系统入口、人工复核、验收方式、首期范围、约束与治理。前 6 个为核心必答，后 2 个可选。已经明确的信息不要重复问。
用户原文可能包含测试文字、随机数字、口语错字或低信息回答。不要把无语义数字串、随手输入的人名或不完整短语当成业务事实，也不要在问题中机械复述；信息不足时改用中立、自然的问法。
不要使用 Edge Case、MVP、人天、Prompt 等术语；不要强迫用户编造百分比、预算或周期。没有基线时，应允许用户回答如何建立基线或直接写“待确认”。每个标题不超过 14 个汉字。
只输出 JSON：{{"questions":[{{"id":"英文蛇形唯一id","title":"短标题","prompt":"结合已有信息的具体问题","hint":"说明可填写待确认的作答提示","type":"textarea","options":[],"required":true}}]}}。不得要求用户先懂 AI 技术。"""
    try:
        raw = await chat_completion(
            load_settings(),
            system="你是高级 AI 解决方案顾问，擅长基于已有信息做自适应深度访谈。只输出 JSON。",
            user=prompt,
            timeout_s=45.0,
            num_predict=1400,
        )
        data = _parse_object(raw)
        questions = data.get("questions")
        if not isinstance(questions, list) or len(questions) < 8:
            raise ValueError("advanced question count invalid")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for i, item in enumerate(questions[:8]):
            if not isinstance(item, dict):
                raise ValueError("invalid question item")
            qid = str(item.get("id") or f"advanced_{i + 1}").strip()
            if qid in seen:
                qid = f"{qid}_{i + 1}"
            seen.add(qid)
            normalized.append(
                {
                    "id": qid,
                    "title": str(item.get("title") or f"进阶问题 {i + 1}").strip()[:18],
                    "prompt": str(item.get("prompt") or "").strip(),
                    "hint": str(item.get("hint") or "").strip(),
                    "type": str(item.get("type") or "textarea"),
                    "options": item.get("options") if isinstance(item.get("options"), list) else [],
                    "required": i < 6,
                },
            )
        if any(not q["prompt"] for q in normalized):
            raise ValueError("empty advanced prompt")
        return normalized
    except (ModelError, ValueError, json.JSONDecodeError, TypeError):
        return _advanced_fallback(scenario, challenge, evidence_answers)


def _advanced_answer_by_topic(
    questions: list[dict[str, Any]],
    answers: dict[str, str | list[str]],
    keywords: tuple[str, ...],
    fallback: str,
) -> str:
    """从动态生成的问题中按题意找到回答，避免依赖固定问题 id。"""
    for question in questions:
        if not isinstance(question, dict):
            continue
        searchable = " ".join(
            str(question.get(key) or "")
            for key in ("title", "prompt", "hint")
        )
        if not any(keyword in searchable for keyword in keywords):
            continue
        qid = str(question.get("id") or "")
        text = _answer_text(answers.get(qid))
        if text:
            return text
    return fallback


def _advanced_answer_lines(
    questions: list[dict[str, Any]],
    answers: dict[str, str | list[str]],
) -> str:
    lines: list[str] = []
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or "")
        answer = _answer_text(answers.get(qid))
        if answer:
            title = str(question.get("title") or question.get("prompt") or f"问题 {index + 1}").strip()
            lines.append(f"- {title}：{answer}")
    return "\n".join(lines) or "- 暂无有效进阶回答"


def _final_fallback(
    scenario: str,
    challenge: str,
    basic_report: dict[str, Any],
    advanced_answers: dict[str, str | list[str]],
    advanced_questions: list[dict[str, Any]] | None = None,
    note: str = "",
) -> dict[str, Any]:
    questions = advanced_questions or []
    sample = _advanced_answer_by_topic(questions, advanced_answers, ("案例", "最近发生", "真实"), _nonempty_answer(advanced_answers, "advanced_real_example", "真实案例待补充"))
    rules = _advanced_answer_by_topic(questions, advanced_answers, ("规则", "例外", "判断"), _nonempty_answer(advanced_answers, "advanced_rules", "业务规则与例外待确认"))
    data = _advanced_answer_by_topic(questions, advanced_answers, ("数据", "资料", "知识", "敏感"), _nonempty_answer(advanced_answers, "advanced_data", "可用数据待盘点"))
    integration = _advanced_answer_by_topic(questions, advanced_answers, ("系统", "入口", "工具", "集成"), _nonempty_answer(advanced_answers, "advanced_integration", "工作入口与系统集成待确认"))
    review = _advanced_answer_by_topic(questions, advanced_answers, ("人工", "审核", "兜底", "失败", "不确定"), _nonempty_answer(advanced_answers, "advanced_human_review", "人工审核与失败兜底待确认"))
    metrics = _advanced_answer_by_topic(questions, advanced_answers, ("验收", "指标", "基线", "成功"), _nonempty_answer(advanced_answers, "advanced_metrics", "需要先建立基线再确定验收阈值"))
    scope = _advanced_answer_by_topic(questions, advanced_answers, ("首期", "范围", "资源", "不做", "负责人"), _nonempty_answer(advanced_answers, "advanced_scope", "首期范围与负责人待确认"))
    constraints = _advanced_answer_by_topic(questions, advanced_answers, ("周期", "预算", "部署", "隐私", "安全", "合规", "治理"), _nonempty_answer(advanced_answers, "advanced_constraints", "周期、预算与治理边界待确认"))
    return {
        "executive_summary": f"建议围绕“{challenge[:100]}”建设一个人机协同的 AI 辅助流程，先从边界清晰的真实场景验证，再根据数据和指标决定扩展范围。"
        + (f" 本版重点回应：{note.strip()[:240]}" if note.strip() else ""),
        "solution": {
            "name": f"{scenario} AI 协同方案",
            "positioning": "以真实业务流程为中心的人机协同能力",
            "description": f"方案以真实案例为输入，依据明确规则处理，并在关键节点保留人工确认。代表性案例：{sample}",
        },
        "capabilities": [
            {"title": "信息理解与整理", "detail": "统一接收真实输入，识别关键信息并形成结构化上下文。"},
            {"title": "规则辅助与内容生成", "detail": rules},
            {"title": "人工复核与反馈闭环", "detail": review},
            {"title": "过程记录与效果分析", "detail": "保留输入、AI 建议、人工修改和最终结果，支持持续改进。"},
        ],
        "target_journey": [
            "用户从最自然的工作入口提交真实任务",
            "系统补齐上下文并检索获准使用的数据或知识",
            "AI 给出带依据的建议、草稿或分析结果",
            "高风险或不确定结果进入人工确认",
            "最终结果回到业务流程并沉淀反馈",
        ],
        "data_and_integrations": [data, integration],
        "implementation_phases": [
            {"name": "验证准备", "goal": "确认流程边界、样本、规则和基线", "deliverables": ["代表性样本集", "流程与规则清单", "验收指标草案"]},
            {"name": "小范围验证", "goal": "用真实任务验证质量与采用方式", "deliverables": ["可用原型", "人工复核流程", "验证记录"]},
            {"name": "集成与扩展", "goal": "在验证通过后接入正式工作入口", "deliverables": ["系统集成", "权限与审计", "运营反馈机制"]},
        ],
        "success_metrics": [metrics, "人工修改率或升级率", "任务完成时间与采用率", "关键用户的结果满意度"],
        "risks": [
            {"risk": "数据或知识不足", "mitigation": "先做资料盘点和样本验证，不用提示词掩盖数据问题。"},
            {"risk": "AI 结果不稳定", "mitigation": review},
            {"risk": "范围持续扩大", "mitigation": scope},
            {"risk": "治理边界不清", "mitigation": constraints},
        ],
        "deliverables": ["流程与场景蓝图", "数据与知识清单", "AI 能力原型", "人工复核与治理规则", "验收报告与扩展建议"],
        "next_action": "确认首期范围、负责人和可用样本后，即可进入验证准备。"
        + (f" 后续评审请重点检查：{note.strip()[:180]}" if note.strip() else ""),
        "source_diagnosis": basic_report.get("diagnosis", ""),
        "generation_mode": "guided_fallback",
    }


def _normalize_final_report(
    data: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(fallback)
    normalized["executive_summary"] = _text(
        data.get("executive_summary"),
        fallback["executive_summary"],
    )
    solution = data.get("solution") if isinstance(data.get("solution"), dict) else {}
    normalized["solution"] = {
        "name": _text(solution.get("name"), fallback["solution"]["name"]),
        "positioning": _text(solution.get("positioning"), fallback["solution"]["positioning"]),
        "description": _text(solution.get("description"), fallback["solution"]["description"]),
    }

    capability_source = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    capabilities: list[dict[str, str]] = []
    for index, default in enumerate(fallback["capabilities"]):
        candidate = capability_source[index] if index < len(capability_source) and isinstance(capability_source[index], dict) else {}
        capabilities.append(
            {
                "title": _text(candidate.get("title"), default["title"]),
                "detail": _text(candidate.get("detail"), default["detail"]),
            },
        )
    normalized["capabilities"] = capabilities
    normalized["target_journey"] = _string_list(data.get("target_journey"), fallback["target_journey"])
    normalized["data_and_integrations"] = _string_list(
        data.get("data_and_integrations"),
        fallback["data_and_integrations"],
    )

    phase_source = data.get("implementation_phases") if isinstance(data.get("implementation_phases"), list) else []
    phases: list[dict[str, Any]] = []
    for index, default in enumerate(fallback["implementation_phases"]):
        candidate = phase_source[index] if index < len(phase_source) and isinstance(phase_source[index], dict) else {}
        phases.append(
            {
                "name": _text(candidate.get("name"), default["name"]),
                "goal": _text(candidate.get("goal"), default["goal"]),
                "deliverables": _string_list(candidate.get("deliverables"), default["deliverables"]),
            },
        )
    normalized["implementation_phases"] = phases
    normalized["success_metrics"] = _string_list(data.get("success_metrics"), fallback["success_metrics"])

    risk_source = data.get("risks") if isinstance(data.get("risks"), list) else []
    risks: list[dict[str, str]] = []
    for index, default in enumerate(fallback["risks"]):
        candidate = risk_source[index] if index < len(risk_source) and isinstance(risk_source[index], dict) else {}
        risks.append(
            {
                "risk": _text(candidate.get("risk"), default["risk"]),
                "mitigation": _text(candidate.get("mitigation"), default["mitigation"]),
            },
        )
    normalized["risks"] = risks
    normalized["deliverables"] = _string_list(data.get("deliverables"), fallback["deliverables"])
    normalized["next_action"] = _text(data.get("next_action"), fallback["next_action"])
    normalized["source_diagnosis"] = _text(data.get("source_diagnosis"), fallback.get("source_diagnosis", ""))
    normalized["generation_mode"] = "local_ai"
    return normalized


async def generate_final_report(
    scenario: str,
    challenge: str,
    basic_answers: dict[str, str | list[str]],
    basic_report: dict[str, Any],
    advanced_answers: dict[str, str | list[str]],
    note: str = "",
    advanced_questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    questions = advanced_questions or []
    evidence_basic_answers = _sanitize_answers(basic_answers)
    evidence_advanced_answers = _sanitize_answers(advanced_answers)
    prompt = f"""你是「AI 共创官」的高级 AI 解决方案顾问。请基于基础诊断和深度共创回答，生成一份可执行但不夸大承诺的专属 AI 落地方案。
场景：{scenario}
核心问题：{challenge}
基础回答：{json.dumps(evidence_basic_answers, ensure_ascii=False)}
初步报告：{json.dumps(basic_report, ensure_ascii=False)}
进阶问答：
{_advanced_answer_lines(questions, evidence_advanced_answers)}
补充偏好：{note or '无'}

只输出 JSON，包含：executive_summary；solution(name, positioning, description)；capabilities(title, detail)；target_journey（字符串数组，每项直接写一个流程步骤，不要输出对象）；data_and_integrations（字符串数组）；implementation_phases(name, goal, deliverables)；success_metrics（字符串数组）；risks(risk, mitigation)；deliverables（字符串数组）；next_action。
约束：不得编造数字、预算、周期、接口或现有系统；缺失内容标记待确认；明确人工确认与失败兜底；实施顺序必须先小范围验证再扩展；建议必须回应用户真实答案。"""
    try:
        raw = await chat_completion(
            load_settings(),
            system="你是谨慎、务实的 AI 解决方案架构师，只根据用户证据输出严格 JSON。",
            user=prompt,
            timeout_s=60.0,
            num_predict=2400,
        )
        data = _parse_object(raw)
        return _normalize_final_report(
            data,
            _final_fallback(scenario, challenge, basic_report, evidence_advanced_answers, questions, note),
        )
    except (ModelError, ValueError, json.JSONDecodeError, TypeError):
        return _final_fallback(scenario, challenge, basic_report, evidence_advanced_answers, questions, note)
