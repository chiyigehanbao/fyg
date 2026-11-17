from app.services.diagnosis import _answer_text, _sanitize_answers


def test_answer_text_rejects_low_information_values() -> None:
    assert _answer_text("123456789") == ""
    assert _answer_text("测试") == ""
    assert _answer_text("暂不确定") == ""
    assert _answer_text("这是关于用真实案例校准的进阶回答") == ""


def test_sanitize_answers_keeps_specific_business_context() -> None:
    cleaned = _sanitize_answers(
        {
            "current_workflow": "客服每天从企业微信导出咨询记录，再手工汇总到 Excel 给主管复盘",
            "impact": "123456",
            "tools": ["企业微信", "测试", "Excel 表格"],
        },
    )

    assert cleaned == {
        "current_workflow": "客服每天从企业微信导出咨询记录，再手工汇总到 Excel 给主管复盘",
        "tools": ["企业微信", "Excel 表格"],
    }
