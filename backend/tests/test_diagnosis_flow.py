from __future__ import annotations

import json
import os
import unittest
import zipfile
from io import BytesIO

os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
os.environ["OLLAMA_MODEL"] = "test-model"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.database import engine  # noqa: E402


class DiagnosisFlowTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        engine.dispose()

    def test_two_stage_flow(self) -> None:
        with TestClient(app) as client:
            system_status = client.get("/api/system/status")
            self.assertEqual(system_status.status_code, 200)
            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            self.assertIn("model_status_error", health.json()["capabilities"])
            self.assertIn("report_pdf_export", health.json()["capabilities"])
            self.assertIn("frontend_static_hosting", health.json()["capabilities"])
            self.assertEqual(system_status.json()["api"]["status"], "ok")
            self.assertIn("model_status_error", system_status.json()["api"]["capabilities"])
            self.assertIn("report_pdf_export", system_status.json()["api"]["capabilities"])
            self.assertIn("http://127.0.0.1:5173", system_status.json()["config"]["cors_allowed_origins"])
            self.assertEqual(system_status.json()["database"]["name"], "diagnosis-test-suite.db")
            self.assertEqual(system_status.json()["data"]["cases"], 0)
            self.assertEqual(system_status.json()["data"]["reports"], 0)
            self.assertFalse(system_status.json()["model"]["connected"])
            self.assertIn(system_status.json()["model"]["error"], {"connect_error", "timeout"})

            invalid = client.post(
                "/api/cases",
                json={"scenario": "流程效率", "challenge": "123456789"},
            )
            self.assertEqual(invalid.status_code, 422)
            placeholder = client.post(
                "/api/cases",
                json={"scenario": "流程效率", "challenge": "测试测试测试测试"},
            )
            self.assertEqual(placeholder.status_code, 422)

            created = client.post(
                "/api/cases",
                json={
                    "scenario": "流程效率",
                    "challenge": "每天人工整理大量客户反馈，难以判断真正优先级",
                },
            )
            self.assertEqual(created.status_code, 200)
            case_id = created.json()["id"]

            basic = client.get(f"/api/cases/{case_id}/interviews/basic")
            self.assertEqual(basic.status_code, 200)
            answers = {
                question["id"]: f"客服主管每晚整理企业微信咨询记录，结合订单表标记高频投诉，并在次日晨会安排处理优先级。字段：{question['title']}"
                for question in basic.json()["questions"]
            }
            answers["role_and_context"] = "我是客服团队主管，负责把企业微信里的售后咨询整理成主管可执行的改进清单。"
            answers["current_workflow"] = "每天先导出聊天记录，再人工复制到 Excel，最后按投诉类型和订单金额排序给运营复盘。"
            answers["impact"] = "每天约花两小时整理，重要投诉有时要到第二天才被发现，客户体验和补偿成本都受影响。"
            answers["people"] = "一线客服负责记录，客服主管负责判断优先级，运营和仓库会根据结论调整处理动作。"
            answers["desired_outcome"] = "希望系统能自动归类问题、标出高风险客户，并生成当天可执行的跟进清单。"
            saved = client.patch(
                f"/api/cases/{case_id}/interviews/basic",
                json={"answers": answers},
            )
            self.assertEqual(saved.status_code, 200)

            basic_report = client.post(
                f"/api/cases/{case_id}/reports/basic/generate",
                json={"note": ""},
            )
            self.assertEqual(basic_report.status_code, 200)
            self.assertEqual(basic_report.json()["stage"], "basic")
            self.assertEqual(len(basic_report.json()["content"]["pain_points"]), 3)
            self.assertNotIn("这是关于", json.dumps(basic_report.json(), ensure_ascii=False))

            advanced = client.post(f"/api/cases/{case_id}/advanced/start")
            self.assertEqual(advanced.status_code, 200)
            rebuilt = client.post(f"/api/cases/{case_id}/advanced/rebuild")
            self.assertEqual(rebuilt.status_code, 200)
            self.assertEqual(len(rebuilt.json()["questions"]), 8)
            advanced_answers = {
                question["id"]: f"我们会先接入企业微信导出的 CSV 和订单明细，用本地模型做分类摘要，再由主管确认后推送执行清单。字段：{question['title']}"
                for question in rebuilt.json()["questions"]
            }
            advanced_saved = client.patch(
                f"/api/cases/{case_id}/interviews/advanced",
                json={"answers": advanced_answers},
            )
            self.assertEqual(advanced_saved.status_code, 200)
            protected = client.post(f"/api/cases/{case_id}/advanced/rebuild")
            self.assertEqual(protected.status_code, 409)

            final_report = client.post(
                f"/api/cases/{case_id}/reports/final/generate",
                json={"note": ""},
            )
            self.assertEqual(final_report.status_code, 200)
            self.assertEqual(final_report.json()["stage"], "final")
            self.assertTrue(final_report.json()["content"]["implementation_phases"])
            self.assertNotIn("这是关于", json.dumps(final_report.json(), ensure_ascii=False))

            revised = client.post(
                f"/api/cases/{case_id}/reports/final/generate",
                json={"note": "更关注本地部署和数据安全"},
            )
            self.assertEqual(revised.status_code, 200)
            self.assertEqual(revised.json()["version"], 2)
            self.assertIn("本地部署", revised.json()["summary"])
            versions = client.get(f"/api/cases/{case_id}/reports/final/versions")
            self.assertEqual(versions.status_code, 200)
            self.assertEqual([item["version"] for item in versions.json()], [2, 1])
            old_version = client.get(f"/api/cases/{case_id}/reports/final/versions/1")
            self.assertEqual(old_version.status_code, 200)
            self.assertEqual(old_version.json()["version"], 1)

            duplicated = client.post(f"/api/cases/{case_id}/duplicate")
            self.assertEqual(duplicated.status_code, 200)
            duplicate_id = duplicated.json()["id"]
            self.assertNotEqual(duplicate_id, case_id)
            duplicate_report = client.get(f"/api/cases/{duplicate_id}/reports/final")
            self.assertEqual(duplicate_report.status_code, 200)
            self.assertEqual(duplicate_report.json()["version"], 2)
            duplicate_versions = client.get(f"/api/cases/{duplicate_id}/reports/final/versions")
            self.assertEqual(duplicate_versions.status_code, 200)
            self.assertEqual([item["version"] for item in duplicate_versions.json()], [2, 1])

            case_export = client.get(f"/api/cases/{case_id}/export.json")
            self.assertEqual(case_export.status_code, 200)
            self.assertIn("application/json", case_export.headers["content-type"])
            self.assertIn(f"ai-cocreator-case-{case_id}", case_export.headers["content-disposition"])
            case_export_json = case_export.json()
            self.assertEqual(case_export_json["schema"], "ai-cocreator.case-export.v1")
            self.assertEqual(case_export_json["case"]["id"], case_id)
            self.assertTrue(case_export_json["interview_sessions"])
            self.assertTrue(case_export_json["reports"])
            self.assertTrue(case_export_json["report_revisions"])

            backup = client.get("/api/system/backup")
            self.assertEqual(backup.status_code, 200)
            self.assertIn("application/json", backup.headers["content-type"])
            self.assertIn("ai-cocreator-backup", backup.headers["content-disposition"])
            backup_json = backup.json()
            self.assertEqual(backup_json["schema"], "ai-cocreator.backup.v1")
            self.assertGreaterEqual(backup_json["counts"]["cases"], 2)
            self.assertGreaterEqual(backup_json["counts"]["reports"], 2)
            self.assertTrue(any(item["id"] == case_id for item in backup_json["cases"]))

            system_status_after_reports = client.get("/api/system/status")
            self.assertGreaterEqual(system_status_after_reports.json()["data"]["cases"], 2)
            self.assertGreaterEqual(system_status_after_reports.json()["data"]["reports"], 2)

            exported = client.get(f"/api/cases/{case_id}/reports/final/export.docx")
            self.assertEqual(exported.status_code, 200)
            self.assertEqual(
                exported.headers["content-type"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            with zipfile.ZipFile(BytesIO(exported.content)) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            self.assertIn("专属 AI 落地方案", document_xml)
            self.assertIn("核心结论", document_xml)
            exported_old = client.get(f"/api/cases/{case_id}/reports/final/versions/1/export.docx")
            self.assertEqual(exported_old.status_code, 200)
            self.assertTrue(exported_old.content.startswith(b"PK"))
            exported_pdf = client.get(f"/api/cases/{case_id}/reports/final/export.pdf")
            self.assertEqual(exported_pdf.status_code, 200)
            self.assertEqual(exported_pdf.headers["content-type"], "application/pdf")
            self.assertTrue(exported_pdf.content.startswith(b"%PDF-1.4"))
            exported_old_pdf = client.get(f"/api/cases/{case_id}/reports/final/versions/1/export.pdf")
            self.assertEqual(exported_old_pdf.status_code, 200)
            self.assertTrue(exported_old_pdf.content.startswith(b"%PDF-1.4"))

            deleted = client.delete(f"/api/cases/{duplicate_id}")
            self.assertEqual(deleted.status_code, 204)
            missing_duplicate = client.get(f"/api/cases/{duplicate_id}")
            self.assertEqual(missing_duplicate.status_code, 404)
            missing_duplicate_export = client.get(f"/api/cases/{duplicate_id}/export.json")
            self.assertEqual(missing_duplicate_export.status_code, 404)

    def test_basic_report_rejects_low_information_required_answers(self) -> None:
        with TestClient(app) as client:
            created = client.post(
                "/api/cases",
                json={
                    "scenario": "客户服务",
                    "challenge": "售后咨询量增长后，主管难以及时判断优先级",
                },
            )
            self.assertEqual(created.status_code, 200)
            case_id = created.json()["id"]

            basic = client.get(f"/api/cases/{case_id}/interviews/basic")
            self.assertEqual(basic.status_code, 200)
            low_information_answers = {
                question["id"]: "测试" if index % 2 == 0 else "123456"
                for index, question in enumerate(basic.json()["questions"])
            }
            saved = client.patch(
                f"/api/cases/{case_id}/interviews/basic",
                json={"answers": low_information_answers},
            )
            self.assertEqual(saved.status_code, 200)

            blocked = client.post(
                f"/api/cases/{case_id}/reports/basic/generate",
                json={"note": ""},
            )
            self.assertEqual(blocked.status_code, 400)
            self.assertEqual(blocked.json()["detail"]["message"], "required answers missing")
            self.assertIn("role_and_context", blocked.json()["detail"]["question_ids"])
            deleted = client.delete(f"/api/cases/{case_id}")
            self.assertEqual(deleted.status_code, 204)


if __name__ == "__main__":
    unittest.main()
