"""Report export helpers."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from docx import Document


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _add_list(document: Document, items: list[Any], *, ordered: bool = False) -> None:
    style = "List Number" if ordered else "List Bullet"
    for item in items:
        if isinstance(item, dict):
            parts = [
                _text(item.get(key))
                for key in ("title", "name", "goal", "detail", "description", "risk", "mitigation")
                if _text(item.get(key))
            ]
            rendered = "：".join(parts)
        else:
            rendered = _text(item)
        if rendered:
            document.add_paragraph(rendered, style=style)


def _add_basic_report(document: Document, content: dict[str, Any]) -> None:
    document.add_heading("真正值得优先解决的痛点", level=2)
    _add_list(document, content.get("pain_points", []))

    document.add_heading("AI 最可能发挥价值的方向", level=2)
    _add_list(document, content.get("opportunities", []), ordered=True)

    quick_start = content.get("quick_start") if isinstance(content.get("quick_start"), dict) else {}
    document.add_heading(_text(quick_start.get("title")) or "建议行动", level=2)
    _add_list(document, quick_start.get("steps", []), ordered=True)

    readiness = content.get("readiness") if isinstance(content.get("readiness"), dict) else {}
    document.add_heading("当前准备度", level=2)
    document.add_paragraph(_text(readiness.get("level")))
    document.add_paragraph(_text(readiness.get("detail")))

    document.add_heading("还需要进一步确认的信息", level=2)
    _add_list(document, content.get("missing_information", []))
    conclusion = _text(content.get("conclusion"))
    if conclusion:
        document.add_heading("结论", level=2)
        document.add_paragraph(conclusion)


def _add_final_report(document: Document, content: dict[str, Any]) -> None:
    solution = content.get("solution") if isinstance(content.get("solution"), dict) else {}
    document.add_heading(_text(solution.get("name")) or "方案蓝图", level=2)
    document.add_paragraph(_text(solution.get("positioning")))
    document.add_paragraph(_text(solution.get("description")))

    document.add_heading("核心能力", level=2)
    _add_list(document, content.get("capabilities", []))

    document.add_heading("目标流程", level=2)
    _add_list(document, content.get("target_journey", []), ordered=True)

    document.add_heading("数据与集成", level=2)
    _add_list(document, content.get("data_and_integrations", []))

    document.add_heading("实施路径", level=2)
    for phase in content.get("implementation_phases", []):
        if not isinstance(phase, dict):
            continue
        document.add_heading(_text(phase.get("name")) or "实施阶段", level=3)
        document.add_paragraph(_text(phase.get("goal")))
        _add_list(document, phase.get("deliverables", []))

    document.add_heading("成功与验收", level=2)
    _add_list(document, content.get("success_metrics", []))

    document.add_heading("风险与治理", level=2)
    _add_list(document, content.get("risks", []))

    document.add_heading("交付结果", level=2)
    _add_list(document, content.get("deliverables", []))
    next_action = _text(content.get("next_action"))
    if next_action:
        document.add_heading("下一步", level=2)
        document.add_paragraph(next_action)


def _render_list_items(items: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            parts = [
                _text(item.get(key))
                for key in ("title", "name", "goal", "detail", "description", "risk", "mitigation", "why", "priority")
                if _text(item.get(key))
            ]
            rendered = "：".join(parts)
        else:
            rendered = _text(item)
        if rendered:
            lines.append(rendered)
    return lines


def _report_lines(
    *,
    title: str,
    stage: str,
    scenario: str,
    challenge: str,
    summary: str,
    version: int,
    content: dict[str, Any],
) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = [
        ("title", title),
        ("meta", f"阶段：{'基础诊断' if stage == 'basic' else '深度共创'}"),
        ("meta", f"版本：第 {version} 版"),
        ("meta", f"场景：{scenario}"),
        ("meta", f"问题：{challenge}"),
        ("heading", "核心结论"),
        ("body", summary),
    ]

    def add_section(name: str, items: list[Any], *, ordered: bool = False) -> None:
        lines.append(("heading", name))
        for index, item in enumerate(_render_list_items(items), start=1):
            prefix = f"{index}. " if ordered else "- "
            lines.append(("body", f"{prefix}{item}"))

    if stage == "basic":
        add_section("真正值得优先解决的痛点", content.get("pain_points", []))
        add_section("AI 最可能发挥价值的方向", content.get("opportunities", []), ordered=True)
        quick_start = content.get("quick_start") if isinstance(content.get("quick_start"), dict) else {}
        add_section(_text(quick_start.get("title")) or "建议行动", quick_start.get("steps", []), ordered=True)
        readiness = content.get("readiness") if isinstance(content.get("readiness"), dict) else {}
        lines.append(("heading", "当前准备度"))
        lines.append(("body", _text(readiness.get("level"))))
        lines.append(("body", _text(readiness.get("detail"))))
        add_section("还需要进一步确认的信息", content.get("missing_information", []))
        conclusion = _text(content.get("conclusion"))
        if conclusion:
            lines.append(("heading", "结论"))
            lines.append(("body", conclusion))
    else:
        solution = content.get("solution") if isinstance(content.get("solution"), dict) else {}
        lines.append(("heading", _text(solution.get("name")) or "方案蓝图"))
        lines.append(("body", _text(solution.get("positioning"))))
        lines.append(("body", _text(solution.get("description"))))
        add_section("核心能力", content.get("capabilities", []))
        add_section("目标流程", content.get("target_journey", []), ordered=True)
        add_section("数据与集成", content.get("data_and_integrations", []))
        lines.append(("heading", "实施路径"))
        for phase in content.get("implementation_phases", []):
            if not isinstance(phase, dict):
                continue
            lines.append(("subheading", _text(phase.get("name")) or "实施阶段"))
            lines.append(("body", _text(phase.get("goal"))))
            for item in _render_list_items(phase.get("deliverables", [])):
                lines.append(("body", f"- {item}"))
        add_section("成功与验收", content.get("success_metrics", []))
        add_section("风险与治理", content.get("risks", []))
        add_section("交付结果", content.get("deliverables", []))
        next_action = _text(content.get("next_action"))
        if next_action:
            lines.append(("heading", "下一步"))
            lines.append(("body", next_action))

    return [(kind, text) for kind, text in lines if text]


def _wrap_text(text: str, width: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= width or char in "。；;":
            chunks.append(current.strip())
            current = ""
    if current.strip():
        chunks.append(current.strip())
    return chunks or [""]


def _pdf_hex(text: str) -> str:
    return text.encode("utf-16-be", errors="ignore").hex().upper()


def build_report_pdf(
    *,
    title: str,
    stage: str,
    scenario: str,
    challenge: str,
    summary: str,
    version: int,
    content: dict[str, Any],
) -> bytes:
    page_width = 595
    page_height = 842
    margin_x = 54
    top_y = 790
    bottom_y = 58
    pages: list[list[str]] = [[]]
    y = top_y

    def add_text(kind: str, text: str) -> None:
        nonlocal y
        font_size = {"title": 18, "heading": 14, "subheading": 12, "meta": 10}.get(kind, 11)
        line_height = font_size + 8
        wrap_width = {"title": 24, "heading": 30, "subheading": 34, "meta": 44}.get(kind, 42)
        if kind in {"heading", "subheading"}:
            y -= 8
        for chunk in _wrap_text(text, wrap_width):
            if y < bottom_y:
                pages.append([])
                y = top_y
            pages[-1].append(f"BT /F1 {font_size} Tf {margin_x} {y} Td <{_pdf_hex(chunk)}> Tj ET")
            y -= line_height

    for kind, text in _report_lines(
        title=title,
        stage=stage,
        scenario=scenario,
        challenge=challenge,
        summary=summary,
        version=version,
        content=content,
    ):
        add_text(kind, text)

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [PAGES_KIDS] /Count PAGES_COUNT >>",
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Encoding /UniGB-UCS2-H /DescendantFonts [4 0 R] >>",
        b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light /CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 2 >> >>",
    ]
    page_object_ids: list[int] = []
    for page in pages:
        content_stream = "\n".join(page).encode("ascii")
        content_object_id = len(objects) + 2
        page_object_ids.append(len(objects) + 1)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_object_id} 0 R >>".encode("ascii"),
        )
        objects.append(b"<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\nstream\n" + content_stream + b"\nendstream")

    kids = " ".join(f"{object_id} 0 R" for object_id in page_object_ids).encode("ascii")
    objects[1] = objects[1].replace(b"PAGES_KIDS", kids).replace(b"PAGES_COUNT", str(len(pages)).encode("ascii"))

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_at = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii"),
    )
    return bytes(output)


def build_report_docx(
    *,
    title: str,
    stage: str,
    scenario: str,
    challenge: str,
    summary: str,
    version: int,
    content: dict[str, Any],
) -> bytes:
    document = Document()
    document.add_heading(title, level=0)
    document.add_paragraph(f"阶段：{'基础诊断' if stage == 'basic' else '深度共创'}")
    document.add_paragraph(f"版本：第 {version} 版")
    document.add_paragraph(f"场景：{scenario}")
    document.add_paragraph(f"问题：{challenge}")

    document.add_heading("核心结论", level=1)
    document.add_paragraph(summary)

    if stage == "basic":
        _add_basic_report(document, content)
    else:
        _add_final_report(document, content)

    output = BytesIO()
    document.save(output)
    return output.getvalue()
