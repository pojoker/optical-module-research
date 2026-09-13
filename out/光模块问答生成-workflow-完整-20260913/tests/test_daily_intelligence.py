from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from daily_intelligence import combine_daily_reports, publish_daily_artifacts
from daily_intelligence.cli import main as cli_main
from daily_intelligence.core import _int_field


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
                    "run_status": "complete",
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
                    "configured_entity_count": 82,
                    "endpoint_count": 8,
                    "endpoint_succeeded": 8,
                    "endpoint_failed": 0,
                    "missing_endpoint_count": 0,
                    "disclosure_candidates": 9,
                    "claim_candidates": 10,
                    "event_candidates": 8,
                    "evidence_candidates": 9,
                    "corroboration_suggestions": 1,
                    "promoted": 0,
                    "failure_types": {},
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
        self.assertEqual(result["collection_status"], "complete")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        original = inputs[0].read_text(encoding="utf-8").rstrip()
        self.assertTrue(report.startswith(original))
        self.assertIn("## 海外事件增量 1 条", report)
        self.assertIn("- LITE | 商业采用·首次出货 | 2026-09-01 | 已声称；建议交叉确认", report)
        self.assertIn("海外数据模式：fixture 演练数据，不代表当日真实采集", report)
        self.assertIn("- 端点 8 个：成功 8 / 失败 0", report)
        self.assertIn("已配置端点覆盖 82/82 个监控实体（配置覆盖，不代表采集成功或研究覆盖）", report)
        self.assertIn("- 组装状态 assembly_status：complete", report)
        self.assertIn("- 采集状态 collection_status：complete", report)
        self.assertIn("- 国内采集状态：complete（manifest run_status=complete）", report)
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
        self.assertEqual(result["collection_status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertTrue(report.startswith("# 国内日报"))
        self.assertIn("## 海外事件增量 未生成", report)
        self.assertIn("缺少海外日报", report)
        self.assertIn("- 采集状态 collection_status：unknown", report)
        self.assertIn("缺少海外 run-summary，采集健康度未知，不推断采集成功", report)
        self.assertIn("国内输入未提供 run_status 完成字段，不推断采集成功", report)
        self.assertNotIn("汇总状态：partial", report)
        payload = json.loads(Path(result["json_path"]).read_text(encoding="utf-8"))
        self.assertFalse(payload["overseas"]["available"])
        self.assertEqual(payload["collection"]["overseas"]["status"], "unknown")

    def test_stale_manifest_is_not_treated_as_today_success(self) -> None:
        self._write_complete_inputs()
        # 模拟昨天的 manifest：日期不匹配时不能当作今日成功输入。
        (self.domestic / "manifest.json").write_text(
            json.dumps({"date": "2026-09-01", "run_status": "complete", "digest": {}}),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "partial")
        self.assertEqual(result["collection_status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("manifest date mismatch", report)
        self.assertIn("- 国内采集状态：unknown", report)
        self.assertIn("国内输入未提供 run_status 完成字段，不推断采集成功", report)

    def test_domestic_incomplete_run_shows_progress_without_claiming_alive_or_killed(self) -> None:
        # 当日国内运行中断：遗留 run-status=running 只证明未完成。
        self._write_complete_inputs()
        (self.domestic / "daily" / "2026-09-02.txt").unlink()
        (self.domestic / "manifest.json").unlink()
        (self.domestic / "run-status.json").write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "status": "running",
                    "processed": 11,
                    "total": 93,
                    "updated_at": "2026-09-05T08:00:00",
                    "errors": ["002281 fetch failed"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "partial")
        self.assertEqual(result["collection_status"], "partial")
        domestic_collection = result["collection"]["domestic"]
        self.assertEqual(domestic_collection["status"], "partial")
        self.assertEqual(domestic_collection["processed"], 11)
        self.assertEqual(domestic_collection["total"], 93)
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("> 国内日报未生成", report)
        self.assertIn("- 国内采集状态：partial（run-status=running，已处理 11/93，更新于 2026-09-05T08:00:00）", report)
        self.assertIn("不能推断进程仍在运行或已被终止", report)

    def test_overseas_partial_failure_with_zero_events_is_not_reported_as_no_news(self) -> None:
        self._write_complete_inputs()
        # 真实形状：8 端点 5 失败、缺端点 74、详情失败与格式拒收另列。
        (self.overseas / "staging" / "2026-09-02" / "run-summary.json").write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "fetch_mode": "http",
                    "monitored_entity_count": 81,
                    "configured_entity_count": 7,
                    "endpoint_count": 8,
                    "endpoint_failed": 5,
                    "missing_endpoint_count": 74,
                    "disclosure_candidates": 1,
                    "claim_candidates": 0,
                    "event_candidates": 0,
                    "evidence_candidates": 0,
                    "corroboration_suggestions": 0,
                    "promoted": 0,
                    "failure_types": {
                        "fetch_failure": 5,
                        "invalid_item": 12,
                        "missing_endpoint": 74,
                        "no_relevant_content": 1,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.overseas / "staging" / "2026-09-02" / "candidates.json").write_text(
            json.dumps({"run_date": "2026-09-02", "fetch_mode": "http", "event_candidates": []}),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "complete")
        self.assertEqual(result["collection_status"], "partial")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("- 本次未提取到事件，采集不完整，不能判断无新消息", report)
        self.assertIn("- 端点 8 个：成功 UNKNOWN / 失败 5", report)
        self.assertIn("已配置端点覆盖 7/81 个监控实体（配置覆盖，不代表采集成功或研究覆盖）", report)
        self.assertIn("缺端点 74 个", report)
        self.assertIn("- 详情抓取失败 UNKNOWN 条；格式拒收（invalid_item）12 条", report)
        self.assertIn("endpoint_succeeded 未提供：端点成功数为 UNKNOWN（已配置不等于成功）", report)

    def test_legacy_fields_stay_unknown_instead_of_inferred_success(self) -> None:
        self._write_complete_inputs()
        # 旧版字段缺失：不推断成功，也不推断端点全部成功。
        (self.overseas / "staging" / "2026-09-02" / "run-summary.json").write_text(
            json.dumps({"run_date": "2026-09-02", "fetch_mode": "http"}),
            encoding="utf-8",
        )
        domestic_manifest = json.loads((self.domestic / "manifest.json").read_text(encoding="utf-8"))
        domestic_manifest.pop("run_status")
        (self.domestic / "manifest.json").write_text(
            json.dumps(domestic_manifest, ensure_ascii=False), encoding="utf-8"
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["assembly_status"], "complete")
        self.assertEqual(result["collection_status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("- 端点 UNKNOWN 个：成功 UNKNOWN / 失败 UNKNOWN", report)
        self.assertIn("不能默认端点全部成功", report)
        self.assertIn("- 国内采集状态：unknown", report)
        self.assertIn("国内输入未提供 run_status 完成字段，不推断采集成功", report)
        self.assertIn("- 采集状态 collection_status：unknown", report)

    def test_manifest_complete_masked_by_current_running_run_status(self) -> None:
        # 控制器反例 1：manifest complete + 当日 rerun run-status=running → 不得冒充 complete。
        self._write_complete_inputs()
        (self.domestic / "run-status.json").write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "status": "running",
                    "processed": 3,
                    "total": 93,
                    "updated_at": "2026-09-05T09:00:00",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["collection"]["domestic"]["status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn(
            "manifest 声称 complete 但当前 run-status=running：running 只证明未完成，完成度存疑",
            report,
        )

    def test_run_status_without_current_run_date_is_rejected(self) -> None:
        # 控制器要求：缺 run_date 的 run-status 不得当作当日有效输入。
        self._write_complete_inputs()
        (self.domestic / "run-status.json").write_text(
            json.dumps({"status": "complete", "processed": 93, "total": 93}),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertIn(
            "run-status date mismatch: expected 2026-09-02, got None",
            result["domestic"]["errors"],
        )
        self.assertEqual(result["assembly_status"], "partial")

    def test_run_status_and_manifest_log_errors_degrade_complete(self) -> None:
        # 控制器要求：run-status errors 与 manifest logs 失败条目不得被 complete 吸收。
        self._write_complete_inputs()
        (self.domestic / "run-status.json").write_text(
            json.dumps(
                {
                    "run_date": "2026-09-02",
                    "status": "complete",
                    "processed": 93,
                    "total": 93,
                    "errors": ["002281 fetch failed"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        manifest = json.loads((self.domestic / "manifest.json").read_text(encoding="utf-8"))
        manifest["logs"] = ["[互动易] 002281 抓取失败: timeout", "[重筛] 本月已存在标记,跳过"]
        (self.domestic / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["collection"]["domestic"]["status"], "partial")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("- 国内采集状态：partial（run-status=complete，manifest run_status=complete，已处理 93/93）", report)
        self.assertIn("run-status 记录 1 条错误摘要，完成度存疑", report)
        self.assertIn("manifest logs 记录 1 条失败条目，完成度存疑", report)

    def test_overseas_missing_coverage_fields_stay_unknown(self) -> None:
        # 控制器反例 2：endpoint_failed=0/missing=0 但缺 endpoint_count/configured/monitored → unknown。
        self._write_complete_inputs()
        (self.overseas / "staging" / "2026-09-02" / "run-summary.json").write_text(
            json.dumps({"run_date": "2026-09-02", "endpoint_failed": 0, "missing_endpoint_count": 0}),
            encoding="utf-8",
        )

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["collection"]["overseas"]["status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("run-summary 缺少 endpoint_count，采集覆盖不完整程度未知", report)

    def test_overseas_unclassified_failure_types_degrade_complete(self) -> None:
        # 控制器反例 3：failure_types 未归类失败类型 → partial；no_relevant_content 不算失败。
        self._write_complete_inputs()
        summary_path = self.overseas / "staging" / "2026-09-02" / "run-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["failure_types"] = {"unsupported_response": 1}
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["collection"]["overseas"]["status"], "partial")
        self.assertEqual(result["collection_status"], "partial")

        summary["failure_types"] = {"no_relevant_content": 3}
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")

        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )

        self.assertEqual(result["collection"]["overseas"]["status"], "complete")

    def test_overseas_missing_or_malformed_failure_types_stay_unknown(self) -> None:
        # 第三审反例：齐全 COVERAGE_FIELDS 但缺 failure_types → 不把缺失诊断当空。
        self._write_complete_inputs()
        summary_path = self.overseas / "staging" / "2026-09-02" / "run-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        summary.pop("failure_types")
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )
        self.assertEqual(result["collection"]["overseas"]["status"], "unknown")
        report = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("run-summary 缺少 failure_types 或格式异常，失败诊断未知，不推断无失败", report)

        summary["failure_types"] = "none"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )
        self.assertEqual(result["collection"]["overseas"]["status"], "unknown")

        # 显式空对象可表示无记录失败：恢复 complete。
        summary["failure_types"] = {}
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )
        self.assertEqual(result["collection"]["overseas"]["status"], "complete")

    def test_int_field_rejects_negative_and_non_integer_counts(self) -> None:
        # 负数计数不是有效诊断，视同缺失而不是可信的零。
        self.assertIsNone(_int_field({"n": -1}, "n"))
        self.assertIsNone(_int_field({"n": True}, "n"))
        self.assertIsNone(_int_field({"n": "3"}, "n"))
        self.assertEqual(_int_field({"n": 3}, "n"), 3)
        summary = {
            "run_date": "2026-09-02",
            "endpoint_count": 8,
            "endpoint_failed": -1,
            "endpoint_succeeded": 8,
            "configured_entity_count": 8,
            "monitored_entity_count": 8,
            "missing_endpoint_count": 0,
            "failure_types": {},
        }
        self._write_complete_inputs()
        (self.overseas / "staging" / "2026-09-02" / "run-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False), encoding="utf-8"
        )
        result = combine_daily_reports(
            run_date="2026-09-02",
            domestic_state_root=self.domestic,
            overseas_state_root=self.overseas,
            output_root=self.output,
        )
        self.assertEqual(result["collection"]["overseas"]["status"], "unknown")

    def test_cli_publish_returns_zero(self) -> None:
        domestic_txt = self.root / "2026-09-02.txt"
        overseas_html = self.root / "overseas.html"
        domestic_txt.write_text("# 日报 2026-09-02\n", encoding="utf-8")
        overseas_html.write_text("<html></html>", encoding="utf-8")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(
                cli_main(
                    [
                        "publish",
                        "--date",
                        "2026-09-02",
                        "--domestic-txt",
                        str(domestic_txt),
                        "--overseas-html",
                        str(overseas_html),
                        "--output-root",
                        str(self.output),
                    ]
                ),
                0,
            )
        self.assertIn("OK: published original artifacts 2026-09-02", buffer.getvalue())

    def test_cli_exit_code_reflects_assembly_and_collection_status(self) -> None:
        self._write_complete_inputs()
        argv = [
            "combine",
            "--date",
            "2026-09-02",
            "--domestic-state-root",
            str(self.domestic),
            "--overseas-state-root",
            str(self.overseas),
            "--output-root",
            str(self.output),
        ]
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(cli_main(argv), 0)
        self.assertIn("OK: combined daily 2026-09-02: complete ->", buffer.getvalue())

        # 移除海外日报后：组装 partial，退出码非零且不冒充 OK。
        (self.overseas / "daily" / "2026-09-02.txt").unlink()
        second = io.StringIO()
        with redirect_stdout(second):
            self.assertEqual(cli_main(argv), 1)
        printed = second.getvalue()
        self.assertIn("PARTIAL: combined daily 2026-09-02: assembly=partial", printed)
        self.assertNotIn("OK:", printed)

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
