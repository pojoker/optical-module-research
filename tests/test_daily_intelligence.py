from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from daily_intelligence import combine_daily_reports, publish_daily_artifacts


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CombinedDailyIntelligenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.domestic = self.root / "domestic"
        self.overseas = self.root / "overseas"
        self.output = self.root / "combined"
        (self.domestic / "daily").mkdir(parents=True)
        (self.overseas / "daily").mkdir(parents=True)
        (self.overseas / "staging" / "2026-09-02").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_complete_inputs(self) -> list[Path]:
        domestic_report = self.domestic / "daily" / "2026-09-02.txt"
        domestic_manifest = self.domestic / "manifest.json"
        overseas_report = self.overseas / "daily" / "2026-09-02.txt"
        overseas_summary = self.overseas / "staging" / "2026-09-02" / "run-summary.json"
        domestic_report.write_text(
            "# 日报 2026-09-02\n\n"
            "## 语料\n- [语料] 最新文件距今1天; 宇宙内缺席年报 0 家\n\n"
            "## 投关表新增 1 份\n- 公司甲 | 2026-09-02 | 投资者关系活动记录表\n\n"
            "## 互动易增量 2 条\n- 公司甲 +2条\n\n"
            "## 公告流(关注公司) 0 条\n\n"
            "## 召回净队列差分: 新增1 / 消失0\n- [公司甲|C4] 光模块 | 新增内容\n\n"
            "## 校验\n- 不变量全绿(①-⑭)\n\n"
            "> 判定闸建议: 有增量,值得开闸复核\n\n"
            "## 补录候选(宇宙外·光通信命中) 0 条\n- 无\n",
            encoding="utf-8",
        )
        domestic_manifest.write_text(
            json.dumps(
                {
                    "date": "2026-09-02",
                    "watched_codes": 102,
                    "digest": {
                        "ir_new": ["ir"],
                        "qa_new": ["qa1", "qa2"],
                        "ann": [],
                        "q_delta_new": ["queue"],
                        "q_delta_gone": [],
                    },
                    "restart_hits": 0,
                    "outlier_hits": 0,
                    "logs": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        overseas_report.write_text("# 海外日报\n\n## 事件\n- LITE first shipment\n", encoding="utf-8")
        overseas_summary.write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "fetch_mode": "fixture",
                    "monitored_entity_count": 82,
                    "configured_entity_count": 7,
                    "missing_endpoint_count": 75,
                    "endpoint_failed": 1,
                    "disclosure_candidates": 9,
                    "claim_candidates": 10,
                    "event_candidates": 8,
                    "evidence_candidates": 9,
                    "corroboration_suggestions": 1,
                    "promoted": 0,
                    "failure_types": {"missing_endpoint": 75, "fetch_failure": 1},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        overseas_candidates = self.overseas / "staging" / "2026-09-02" / "candidates.json"
        overseas_candidates.write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "fetch_mode": "fixture",
                    "event_candidates": [
                        {
                            "event_id": "EC_001",
                            "primary_subject_id": "LITE",
                            "event_category": "commercial_adoption",
                            "lifecycle_stage": "first_shipment",
                            "occurred_start": "2026-09-01",
                            "event_status": "asserted",
                            "suggested_event_status": "corroborated",
                            "blocked_reason": "",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return [domestic_report, domestic_manifest, overseas_report, overseas_summary, overseas_candidates]

    def test_combines_both_reports_and_keeps_inputs_read_only(self) -> None:
        inputs = self._write_complete_inputs()
        before = {path: _sha256(path) for path in inputs}

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "complete")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        original = inputs[0].read_text(encoding="utf-8").rstrip()
        self.assertTrue(report.startswith(original))
        self.assertIn("## 海外事件增量 1 条", report)
        self.assertIn("- LITE | 商业采用·首次出货 | 2026-09-01 | 已声称；建议交叉确认", report)
        self.assertIn("海外数据模式：fixture 演练数据，不代表当日真实采集", report)
        self.assertNotIn("国内与海外每日情报总览", report)
        self.assertNotIn("commercial_adoption", report)
        self.assertNotIn("first_shipment", report)
        self.assertNotIn("status=asserted", report)
        self.assertEqual(before, {path: _sha256(path) for path in inputs})

    def test_missing_source_still_writes_an_explicit_partial_report(self) -> None:
        domestic_report = self.domestic / "daily" / "2026-09-02.txt"
        domestic_report.write_text("# 国内日报\n", encoding="utf-8")
        (self.domestic / "manifest.json").write_text(
            json.dumps({"date": "2026-09-02", "digest": {}}), encoding="utf-8"
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "partial")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertTrue(report.startswith("# 国内日报"))
        self.assertIn("## 海外事件增量 未生成", report)
        self.assertIn("缺少海外日报", report)
        self.assertNotIn("汇总状态：partial", report)
        payload = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
        self.assertFalse(payload["overseas"]["available"])

    def test_rejects_invalid_date_and_overlapping_output(self) -> None:
        self._write_complete_inputs()
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            combine_daily_reports(
                run_date="09/02/2026",
                domestic_state_root=self.domestic,
                overseas_state_root=self.overseas,
                output_root=self.output,
            )
        with self.assertRaisesRegex(ValueError, "disjoint"):
            combine_daily_reports(
                run_date="2026-09-02",
                domestic_state_root=self.domestic,
                overseas_state_root=self.overseas,
                output_root=self.domestic / "combined",
            )

    def test_publishes_original_txt_and_html_without_rewriting_them(self) -> None:
        domestic_txt = self.root / "2026-08-22.txt"
        overseas_html = self.root / "海外情报更新_2026-08-23.html"
        domestic_txt.write_text(
            "# 日报 2026-08-22\n\n## 语料\n- 原始国内日报\n",
            encoding="utf-8",
        )
        overseas_html.write_text(
            "<!doctype html><html><head><title>光模块行业产业链全景图 · 公司能力细化版</title></head>"
            "<body><h1>海外电话会与官网技术情报</h1><a href=\"#events\">本期公司事件</a></body></html>",
            encoding="utf-8",
        )
        source_hashes = {_sha256(domestic_txt), _sha256(overseas_html)}

        result = publish_daily_artifacts(
            run_date="2026-09-02",
            domestic_txt=domestic_txt,
            overseas_html=overseas_html,
            output_root=self.output,
        )

        published_txt = Path(result["domestic_path"])
        published_html = Path(result["overseas_path"])
        self.assertEqual(source_hashes, {_sha256(published_txt), _sha256(published_html)})
        index = Path(result["index_path"]).read_text(encoding="utf-8")
        self.assertIn("国内增量日报（原始 TXT）", index)
        self.assertIn("海外情报全景（原始 HTML）", index)
        self.assertIn("domestic.txt", index)
        self.assertIn("overseas.html", index)
        self.assertNotIn("海外事件增量", published_txt.read_text(encoding="utf-8"))

    def test_publish_rejects_output_that_contains_a_source(self) -> None:
        source_root = self.root / "source"
        source_root.mkdir()
        domestic_txt = source_root / "daily.txt"
        overseas_html = source_root / "overseas.html"
        domestic_txt.write_text("daily", encoding="utf-8")
        overseas_html.write_text("<html></html>", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "disjoint"):
            publish_daily_artifacts(
                run_date="2026-09-02",
                domestic_txt=domestic_txt,
                overseas_html=overseas_html,
                output_root=source_root,
            )


if __name__ == "__main__":
    unittest.main()
