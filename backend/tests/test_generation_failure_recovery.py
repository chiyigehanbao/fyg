from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.database import engine
from app.routers import diagnosis as diagnosis_router


def _create_case_with_basic_answers(client: TestClient) -> str:
    created = client.post(
        "/api/cases",
        json={
            "scenario": "流程效率",
            "challenge": "客服每天手工整理客户反馈，无法稳定发现最该优先处理的问题",
        },
    )
    assert created.status_code == 200
    case_id = created.json()["id"]

    interview = client.get(f"/api/cases/{case_id}/interviews/basic")
    assert interview.status_code == 200
    answers = {
        question["id"]: f"客服主管会结合企业微信记录和订单信息整理反馈优先级：{question['title']}"
        for question in interview.json()["questions"]
    }
    saved = client.patch(f"/api/cases/{case_id}/interviews/basic", json={"answers": answers})
    assert saved.status_code == 200
    return case_id


def test_basic_report_failure_restores_collecting_status(monkeypatch) -> None:
    async def broken_generate_basic_report(*args, **kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("simulated report generation failure")

    monkeypatch.setattr(diagnosis_router, "generate_basic_report", broken_generate_basic_report)

    with TestClient(app, raise_server_exceptions=False) as client:
        case_id = _create_case_with_basic_answers(client)

        failed = client.post(f"/api/cases/{case_id}/reports/basic/generate", json={"note": ""})
        assert failed.status_code == 500

        row = client.get(f"/api/cases/{case_id}")
        assert row.status_code == 200
        assert row.json()["status"] == "basic_collecting"

    engine.dispose()


def test_final_report_failure_restores_advanced_collecting_status(monkeypatch) -> None:
    async def broken_generate_final_report(*args, **kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("simulated final report generation failure")

    monkeypatch.setattr(diagnosis_router, "generate_final_report", broken_generate_final_report)

    with TestClient(app, raise_server_exceptions=False) as client:
        case_id = _create_case_with_basic_answers(client)

        basic_report = client.post(f"/api/cases/{case_id}/reports/basic/generate", json={"note": ""})
        assert basic_report.status_code == 200
        advanced = client.post(f"/api/cases/{case_id}/advanced/start")
        assert advanced.status_code == 200
        advanced_answers = {
            question["id"]: f"先用导出的客户反馈和订单数据做本地分类，再由主管确认处理动作：{question['title']}"
            for question in advanced.json()["questions"]
        }
        advanced_saved = client.patch(
            f"/api/cases/{case_id}/interviews/advanced",
            json={"answers": advanced_answers},
        )
        assert advanced_saved.status_code == 200

        failed = client.post(f"/api/cases/{case_id}/reports/final/generate", json={"note": ""})
        assert failed.status_code == 500

        row = client.get(f"/api/cases/{case_id}")
        assert row.status_code == 200
        assert row.json()["status"] == "advanced_collecting"

    engine.dispose()
