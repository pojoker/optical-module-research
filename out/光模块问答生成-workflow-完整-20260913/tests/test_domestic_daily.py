import importlib.util
import json
import re
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

from domestic_daily import DailyMirror, FixtureClient, core
from domestic_daily.core import RequestsClient


ROOT = Path(__file__).parents[1]


class MirrorTests(unittest.TestCase):
    def test_completed_backfill_continues_with_overlap_and_retains_history(self):
        source=self.make_source();state=Path(tempfile.mkdtemp())
        row=json.loads((source/'corpus/qa/000001/qa.jsonl').read_text())
        historical=dict(row,index_id='backfilled',answer='历史正文\u2028保持完整')
        qpath=state/'qa/000001/qa.jsonl';qpath.parent.mkdir(parents=True)
        qpath.write_text(json.dumps(historical,ensure_ascii=False)+'\n')
        (state/'qa_watermarks.json').write_text(json.dumps({'000001':'2026-09-11'}))
        client=FixtureClient()
        result=DailyMirror(source,state,client).run('2026-09-12')
        self.assertEqual(client.qa_since['000001'],'2026-09-04')
        self.assertEqual(result['manifest']['digest']['qa_new'],[])
        self.assertEqual(json.loads((state/'qa_watermarks.json').read_text())['000001'],'2026-09-12')
        self.assertIn(historical,DailyMirror._read_qa(qpath))

    def test_unicode_line_separators_survive_daily_write_and_read(self):
        source=self.make_source()
        state=Path(tempfile.mkdtemp())
        row=json.loads((source/'corpus/qa/000001/qa.jsonl').read_text())
        row.update(index_id='unicode',answer='正文\u2028仍属于同一回答\u2029下一段\u0085结束')
        client=FixtureClient(qa={'000001':[row]})
        DailyMirror(source,state,client).run('2026-09-11')
        saved=DailyMirror._read_qa(state/'qa/000001/qa.jsonl')
        self.assertIn(row,saved)

    def make_source(self):
        root = Path(tempfile.mkdtemp())
        (root / "corpus/ir/000001").mkdir(parents=True)
        (root / "corpus/qa/000001").mkdir(parents=True)
        (root / "corpus/_frozen.csv").write_text("代码,名称\n000001,公司甲\n", encoding="utf-8")
        (root / "corpus/_restart_watchlist.csv").write_text(
            "公司,代码,类别,cell_id,重启条件,触发词,窗口,引用,车道\n",
            encoding="utf-8",
        )
        (root / "triage.csv").write_text("hit_id,公司,cell_id,来源,引语或线索摘要,处置,理由,会话日期\n", encoding="utf-8")
        (root / "points.csv").write_text(
            "point_id,公司,cell_id,状态,上市标签,命中引语,锚点URL,检索日期,判定等级,判定会话日期\n"
            "P001,公司甲,D1,生产中,A股,x,x,2026-01-01,x,2026-01-01\n",
            encoding="utf-8",
        )
        (root / "words.txt").write_text("光模块|C4||\nQAONLY|C5||\n", encoding="utf-8")
        (root / "corpus/ir/000001/a.pdf").write_bytes(b"%PDF-fixture")
        (root / "corpus/ir/000001/a.pdf.txt").write_text("已有投关光模块内容", encoding="utf-8")
        qa = {"code": "000001", "question": "q", "answer": "QAONLY", "answer_date": "2026-01-01",
              "ask_date": "2026-01-01", "index_id": "q1", "empty": False, "fetch_date": "2026-01-01", "source": "fixture"}
        (root / "corpus/qa/000001/qa.jsonl").write_text(json.dumps(qa) + "\n", encoding="utf-8")
        return root

    def run_mirror(self, client, date="2026-09-01"):
        state = Path(tempfile.mkdtemp())
        return state, DailyMirror(ROOT, state, client).run(date)

    def test_primary_zero_fallback_unavailable_does_not_advance_watermark(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        module = _load_fetch_qa()
        module._primary = lambda *_: (0, "primary completed")
        module._p5w_down = {"v": True, "reason": "connection failed"}
        adapter = RequestsClient(source)
        adapter._fetch_module_cache = module
        client = FixtureClient()
        client.fetch_qa = adapter.fetch_qa
        result = DailyMirror(source, state, client).run("2026-09-09")
        self.assertEqual(result["manifest"]["qa_failed_codes"], ["000001"])
        self.assertNotIn("000001", json.loads((state / "qa_watermarks.json").read_text()))

    def test_both_channels_zero_still_advance_success_watermark(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        module = _load_fetch_qa()
        module._primary = lambda *_: (0, "primary completed")
        module._p5w_guarded = lambda *_: 0
        adapter = RequestsClient(source)
        adapter._fetch_module_cache = module
        client = FixtureClient()
        client.fetch_qa = adapter.fetch_qa
        result = DailyMirror(source, state, client).run("2026-09-09")
        self.assertEqual(result["manifest"]["qa_failed_codes"], [])
        self.assertEqual(json.loads((state / "qa_watermarks.json").read_text())["000001"], "2026-09-09")

    def test_failed_adapter_keeps_partial_rows_without_success_watermark(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        row = json.loads((source / "corpus/qa/000001/qa.jsonl").read_text())
        class PartialModule:
            def fetch(self, code, since):
                path = Path(self.ROOT) / "corpus/qa" / code / "qa.jsonl"
                with path.open("a") as stream:
                    stream.write(json.dumps(dict(row, index_id="partial-new", answer_date="2026-09-09")) + "\n")
                raise RuntimeError("分页截断")
        adapter = RequestsClient(source)
        adapter._fetch_module_cache = PartialModule()
        client = FixtureClient()
        client.fetch_qa = adapter.fetch_qa
        result = DailyMirror(source, state, client).run("2026-09-09")
        saved = [json.loads(x) for x in (state / "qa/000001/qa.jsonl").read_text().splitlines()]
        self.assertIn("partial-new", [x["index_id"] for x in saved])
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertEqual(result["manifest"]["qa_failed_codes"], ["000001"])
        self.assertNotIn("000001", json.loads((state / "qa_watermarks.json").read_text()))
        self.assertIn("部分保留", result["manifest"]["errors"][0])

    def test_company_budget_continues_and_restores_alarm(self):
        import signal
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient()
        client.fetch_qa = lambda *args: time.sleep(0.2)
        old = signal.getsignal(signal.SIGALRM)
        result = DailyMirror(source, state, client, qa_timeout=0.02).run("2026-09-09")
        self.assertEqual(result["manifest"]["qa_failed_codes"], ["000001"])
        self.assertIn("预算", result["manifest"]["errors"][0])
        self.assertIs(signal.getsignal(signal.SIGALRM), old)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        self.assertTrue((state / "daily/2026-09-09.txt").exists())

    def test_interruption_resumes_success_without_losing_daily_delta(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        row = json.loads((source / "corpus/qa/000001/qa.jsonl").read_text())
        client = FixtureClient(qa={"000001": [dict(row, index_id="new", answer_date="2026-09-09")]})
        client.query_announcements = mock.Mock(side_effect=KeyboardInterrupt)
        with self.assertRaises(KeyboardInterrupt):
            DailyMirror(source, state, client).run("2026-09-09")
        self.assertEqual(json.loads((state / "run-status.json").read_text())["status"], "failed")
        self.assertTrue(json.loads((state / "run-status.json").read_text())["interrupted"])
        client.query_announcements = mock.Mock(return_value=[])
        client.fetch_qa = mock.Mock(side_effect=AssertionError("successful company must resume"))
        result = DailyMirror(source, state, client).run("2026-09-09")
        client.fetch_qa.assert_not_called()
        self.assertEqual(result["manifest"]["digest"]["qa_new"], [("公司甲", 1)])
        self.assertFalse((state / "qa-resume.json").exists())

    def test_sigterm_marks_failed_and_restores_handlers(self):
        import signal
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient()
        client.fetch_qa = lambda *args: signal.raise_signal(signal.SIGTERM)
        old_term, old_alarm = signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGALRM)
        with self.assertRaises(KeyboardInterrupt):
            DailyMirror(source, state, client).run("2026-09-09")
        status = json.loads((state / "run-status.json").read_text())
        self.assertEqual(status["status"], "failed")
        self.assertTrue(status["interrupted"])
        self.assertIn("SIGTERM", status["termination_reason"])
        self.assertIs(signal.getsignal(signal.SIGTERM), old_term)
        self.assertIs(signal.getsignal(signal.SIGALRM), old_alarm)
        self.assertFalse(list(state.glob(".run-*")))

    def test_resume_does_not_reuse_other_date(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient()
        client.query_announcements = mock.Mock(side_effect=KeyboardInterrupt)
        with self.assertRaises(KeyboardInterrupt):
            DailyMirror(source, state, client).run("2026-09-08")
        client.query_announcements = mock.Mock(return_value=[])
        client.fetch_qa = mock.Mock(return_value=[])
        DailyMirror(source, state, client).run("2026-09-09")
        client.fetch_qa.assert_called_once()

    def test_request_progress_keeps_url_page_and_complete_error(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient()
        def fail(*args):
            client.progress_callback({"url": "https://example.test/list", "page": 20})
            status = json.loads((state / "run-status.json").read_text())
            self.assertEqual(status["current_request"]["page"], 20)
            self.assertEqual(status["current_company"], "000001")
            raise RuntimeError("x" * 150 + "END")
        client.fetch_qa = fail
        result = DailyMirror(source, state, client).run("2026-09-09")
        self.assertTrue(result["manifest"]["errors"][0].endswith("END"))

    def test_watched_union_and_protected_source(self):
        client = FixtureClient(qa={}, announcements={}, ir={"relation": [], "fulltext": []})
        state, result = self.run_mirror(client)
        self.assertIn("300308", result["manifest"]["watched_codes"])
        self.assertIn("600114", result["manifest"]["watched_codes"])
        self.assertNotIn("AAOI", result["manifest"]["watched_codes"])
        self.assertTrue(all(re.fullmatch(r"\d{6}", code) for code in result["manifest"]["watched_codes"]))
        self.assertTrue((state / "daily/2026-09-01.txt").exists())

    def test_qa_union_does_not_shrink_and_fixture_filters(self):
        source = ROOT / "corpus/qa/300308/qa.jsonl"
        old = json.loads(source.read_text().splitlines()[0])
        client = FixtureClient(qa={"300308": [dict(old, answer="new metadata"), {**old, "index_id": "fixture-new"}]}, announcements={})
        state, result = self.run_mirror(client)
        rows = [json.loads(x) for x in (state / "qa/300308/qa.jsonl").read_text().splitlines()]
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(result["manifest"]["digest"]["qa_new"][0][1], 1)

    def test_announcement_restart_and_atomic_repeat(self):
        client = FixtureClient(
            ir={"relation": [{"secCode": "300308", "secName": "中际旭创", "announcementTitle": "投资者关系活动记录表", "adjunctUrl": "x.pdf", "text": "自研硅光芯片"}], "fulltext": []},
            downloads={"x.pdf": b"%PDF-fixture"},
            announcements={"300308": [{"secCode": "300308", "announcementTitle": "重大合同公告", "announcementTime": "2026-09-01", "adjunctUrl": "a.pdf"}, {"secCode": "300308", "announcementTitle": "普通公告", "announcementTime": "2026-09-01", "adjunctUrl": "b.pdf"}]}, qa={})
        state, first = self.run_mirror(client)
        daily = (state / "daily/2026-09-01.txt").read_bytes()
        self.assertIn("公告流(关注公司) 1 条", daily.decode())
        self.assertIn("机械匹配，不构成判定", daily.decode())
        second = DailyMirror(ROOT, state, client).run("2026-09-01")
        self.assertEqual(daily, (state / "daily/2026-09-01.txt").read_bytes())
        self.assertEqual(first["manifest"]["watched_codes"], second["manifest"]["watched_codes"])

    def test_lock_rejects_concurrent_run(self):
        import fcntl
        state = Path(tempfile.mkdtemp())
        lock = (state / ".lock"); lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open("w") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(RuntimeError):
                DailyMirror(ROOT, state, FixtureClient()).run("2026-09-01")

    def test_scan_reads_existing_ir_but_never_scans_qa(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        queue = (state / "daily/queue-latest.txt").read_text(encoding="utf-8")
        self.assertIn("公司甲|C4|光模块", queue)
        self.assertNotIn("QAONLY", queue)

    def test_first_run_seeds_queue_without_false_daily_delta(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-01")

        self.assertTrue(result["manifest"]["queue_baseline_initialized"])
        self.assertEqual(result["manifest"]["digest"]["q_delta_new"], [])
        report = (state / "daily/2026-09-01.txt").read_text(encoding="utf-8")
        self.assertIn("召回队列基线初始化: 1 条（不计为当日新增）", report)
        self.assertIn("> 判定闸建议: 无实质增量,今日免开闸", report)

    def test_rescreen_401_short_circuits_without_marker(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient(rescreen={"000001": RuntimeError("p_stock2110 需token(401)")})
        result = DailyMirror(source, state, client).run("2026-09-01")
        self.assertTrue(result["manifest"]["rescreen"]["blocked"])
        self.assertFalse((state / "monthly/.rescreen-2026-09.done").exists())
        self.assertEqual([call[0] for call in client.calls].count("rescreen"), 1)

    def test_qa_since_backfills_once_then_uses_overlap_window(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        first = FixtureClient()
        DailyMirror(source, state, first).run("2026-09-01")
        self.assertEqual(first.qa_since["000001"], "2023-01-01")
        self.assertEqual(json.loads((state / "qa_watermarks.json").read_text(encoding="utf-8")), {"000001": "2026-09-01"})
        second = FixtureClient()
        DailyMirror(source, state, second).run("2026-09-02")
        self.assertEqual(second.qa_since["000001"], "2026-08-25")  # 水位 2026-09-01 - 7 天重叠

    def test_qa_failure_keeps_watermark_and_marks_partial(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        failing = FixtureClient(qa={"000001": RuntimeError("irm 502")})
        result = DailyMirror(source, state, failing).run("2026-09-02")
        self.assertEqual(failing.qa_since["000001"], "2026-08-25")
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertEqual(result["manifest"]["qa_failed_codes"], ["000001"])
        # 抓取失败不推进水位
        self.assertEqual(json.loads((state / "qa_watermarks.json").read_text(encoding="utf-8"))["000001"], "2026-09-01")
        status = json.loads((state / "run-status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "partial")
        self.assertEqual(status["error_count"], 1)
        self.assertEqual(status["processed"], status["total"])
        self.assertIn("[互动易] 000001 抓取失败", (state / "run.log").read_text(encoding="utf-8"))
        retry = FixtureClient()
        DailyMirror(source, state, retry).run("2026-09-03")
        self.assertEqual(retry.qa_since["000001"], "2026-08-25")  # 失败窗口下次仍会重抓

    def test_explicit_backfill_since_overrides_watermark(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        client = FixtureClient()
        DailyMirror(source, state, client).run("2026-09-02", backfill_since="2024-06-01")
        self.assertEqual(client.qa_since["000001"], "2024-06-01")

    def test_complete_run_reports_complete_status(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "complete")
        status = json.loads((state / "run-status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "complete")
        self.assertEqual(status["run_date"], "2026-09-01")
        self.assertEqual(status["error_count"], 0)
        self.assertEqual(status["processed"], status["total"])
        report = (state / "daily/2026-09-01.txt").read_text(encoding="utf-8")
        self.assertIn("## 运行状态 complete", report)
        self.assertIn("> 判定闸建议: 无实质增量,今日免开闸", report)

    def test_partial_run_report_avoids_no_news_claim(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        client = FixtureClient(announcements={"000001": RuntimeError("cninfo 500")})
        result = DailyMirror(source, state, client).run("2026-09-02")
        report = (state / "daily/2026-09-02.txt").read_text(encoding="utf-8")
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertIn("## 运行状态 partial", report)
        self.assertIn("不能据此判断今日无新增", report)
        self.assertIn("本次运行不完整，不能判断无新增", report)
        self.assertIn("[公告流] 000001 查询失败", report)
        self.assertIn("[公告流] 000001 查询失败", (state / "run.log").read_text(encoding="utf-8"))

    def test_interrupted_prior_run_is_reported_without_blaming_a_process(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        (state / "run-status.json").write_text(json.dumps(
            {"run_date": "2026-09-01", "status": "running", "updated_at": "2026-09-01T09:00:00+08:00",
             "processed": 3, "total": 5, "stage": "互动易"}), encoding="utf-8")
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-02")
        self.assertTrue(result["manifest"]["prior_run_interrupted"])
        self.assertEqual(result["manifest"]["run_status"], "complete")  # 遗留 running 不使本轮降级
        report = (state / "daily/2026-09-02.txt").read_text(encoding="utf-8")
        self.assertIn("上一次运行未正常结束", report)
        self.assertIn("不据此推断终止原因", report)

    def test_fatal_failure_marks_failed_and_keeps_prior_snapshot(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        kept = (state / "daily/2026-09-01.txt").read_bytes()
        mirror = DailyMirror(source, state, FixtureClient(announcements={"000001": RuntimeError("cninfo 500")}))

        def boom():
            raise RuntimeError("日报渲染中断")

        mirror._source_check_lines = boom
        with self.assertRaises(RuntimeError):
            mirror.run("2026-09-02")  # 同月，重筛标记已存在，中断点在采集之后、日报写出之前
        status = json.loads((state / "run-status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["error_count"], 1)
        self.assertEqual(status["stage"], "公告流")
        self.assertNotIn("daily_path", status)
        self.assertFalse((state / "daily/2026-09-02.txt").exists())
        # 轮次结束前发生的失败已经落盘可见
        self.assertIn("[公告流] 000001 查询失败", (state / "run.log").read_text(encoding="utf-8"))
        # 中断不破坏上一次完整快照
        self.assertEqual(kept, (state / "daily/2026-09-01.txt").read_bytes())

    def test_non_pdf_ir_response_is_registered_as_degradation(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient(
            ir={"relation": [{"secCode": "000001", "secName": "公司甲", "announcementTitle": "投资者关系活动记录表",
                              "adjunctUrl": "x.pdf"}], "fulltext": []},
            downloads={"x.pdf": b"<html>error page</html>"})
        result = DailyMirror(source, state, client).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertIn("[投关表] 000001 非PDF响应,未入库", (state / "run.log").read_text(encoding="utf-8"))

    def test_pdf_text_extraction_failure_is_registered_as_degradation(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient(
            ir={"relation": [{"secCode": "000001", "secName": "公司甲", "announcementTitle": "投资者关系活动记录表",
                              "adjunctUrl": "x.pdf"}], "fulltext": []},
            downloads={"x.pdf": b"%PDF-fixture"})
        real_run = core.subprocess.run

        def fake_run(cmd, *args, **kwargs):
            if cmd and cmd[0] == "pdftotext":
                return types.SimpleNamespace(returncode=1)
            return real_run(cmd, *args, **kwargs)

        with mock.patch.object(core.subprocess, "run", fake_run):
            result = DailyMirror(source, state, client).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertIn("PDF文本提取失败", (state / "run.log").read_text(encoding="utf-8"))

    def test_rescreen_401_is_registered_as_degradation(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient(rescreen={"000001": RuntimeError("p_stock2110 需token(401)")})
        result = DailyMirror(source, state, client).run("2026-09-01")
        self.assertTrue(result["manifest"]["rescreen"]["blocked"])
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertIn("本月重筛未完成", (state / "run.log").read_text(encoding="utf-8"))

    def test_stale_partial_manifest_is_rewritten_not_reused(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        partial = DailyMirror(source, state, FixtureClient(
            announcements={"000001": RuntimeError("cninfo 500")})).run("2026-09-01")
        self.assertEqual(partial["manifest"]["run_status"], "partial")
        # 同日重跑且恢复：旧的 partial 产物不能复用，必须重写为一致状态
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "complete")
        persisted = json.loads((state / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["run_status"], "complete")
        report = (state / "daily/2026-09-01.txt").read_text(encoding="utf-8")
        self.assertIn("## 运行状态 complete", report)
        self.assertNotIn("## 运行状态 partial", report)

    def test_legacy_manifest_without_run_status_is_rewritten(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        first = DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        legacy = {k: v for k, v in first["manifest"].items() if k not in
                  ("run_status", "errors", "qa_failed_codes", "qa_backfill_codes", "prior_run_interrupted")}
        (state / "manifest.json").write_text(json.dumps(legacy, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "complete")
        persisted = json.loads((state / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(persisted["run_status"], "complete")  # 遗留无状态产物被重写

    def test_manifest_non_dict_list_is_rewritten_not_crashed(self):
        """遗留 manifest 是 list（非法形状）：prior_manifest 走 _read_json 必须不崩，
        prior_complete 回落 False，本轮重写为一致的 dict 产物（2026-09-05 复审漏网#2）。
        """
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        (state / "manifest.json").write_text(json.dumps([{"date": "2026-09-01"}]), encoding="utf-8")
        result = DailyMirror(source, state, FixtureClient()).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "complete")
        persisted = json.loads((state / "manifest.json").read_text(encoding="utf-8"))
        self.assertIsInstance(persisted, dict)  # 非 dict 不被当作可复用 manifest
        self.assertEqual(persisted["run_status"], "complete")

    def test_pdf_empty_text_layer_is_registered_as_degradation(self):
        """pdftotext 退出码 0 但无文本层（扫描件空白正文）：必须降级，不能当成功。"""
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        client = FixtureClient(
            ir={"relation": [{"secCode": "000001", "secName": "公司甲", "announcementTitle": "投资者关系活动记录表",
                              "adjunctUrl": "x.pdf"}], "fulltext": []},
            downloads={"x.pdf": b"%PDF-fixture"})
        real_run = core.subprocess.run

        def empty_run(cmd, *a, **k):
            if cmd and cmd[0] == "pdftotext":
                out = cmd[3]  # pdftotext 输出是 cmd[3]（输入 PDF 是 cmd[2]）
                Path(out).write_text("", encoding="utf-8")  # 退出 0 但空白正文（无文本层）
                return types.SimpleNamespace(returncode=0)
            return real_run(cmd, *a, **k)

        with mock.patch.object(core.subprocess, "run", empty_run):
            result = DailyMirror(source, state, client).run("2026-09-01")
        self.assertEqual(result["manifest"]["run_status"], "partial")
        self.assertIn("PDF无文本层", (state / "run.log").read_text(encoding="utf-8"))

    def test_pdf_extraction_failure_rerun_recovers_not_permanently_skipped(self):
        """Day1 提取失败留空 txt；Day2 重跑必须重试提取而非被 existing_path 永久跳过
        （2026-09-05 复审漏网#3：失败落空 txt 后下次 existing_path.exists 就跳过，下一天反而 complete）。
        """
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        ir = {"relation": [{"secCode": "000001", "secName": "公司甲", "announcementTitle": "投资者关系活动记录表",
                            "adjunctUrl": "x.pdf"}], "fulltext": []}
        real_run = core.subprocess.run

        def fail_run(cmd, *a, **k):
            if cmd and cmd[0] == "pdftotext":
                return types.SimpleNamespace(returncode=1)  # Day1 提取失败
            return real_run(cmd, *a, **k)

        with mock.patch.object(core.subprocess, "run", fail_run):
            r1 = DailyMirror(source, state, FixtureClient(ir=ir, downloads={"x.pdf": b"%PDF-fixture"})).run("2026-09-01")
        self.assertEqual(r1["manifest"]["run_status"], "partial")  # 失败登记为降级
        pdf_path = list((state / "ir/000001").glob("*.pdf"))[0]
        txt_path = pdf_path.with_suffix(pdf_path.suffix + ".txt")
        self.assertEqual(txt_path.stat().st_size, 0)  # 失败留空 txt

        def ok_run(cmd, *a, **k):
            if cmd and cmd[0] == "pdftotext":
                out = cmd[3]  # pdftotext 输出是 cmd[3]（输入 PDF 是 cmd[2]）
                Path(out).write_text("重跑恢复的光模块投关内容", encoding="utf-8")  # 真实写出非空正文证明恢复
                return types.SimpleNamespace(returncode=0)
            return real_run(cmd, *a, **k)

        with mock.patch.object(core.subprocess, "run", ok_run):
            DailyMirror(source, state, FixtureClient(ir=ir, downloads={"x.pdf": b"%PDF-fixture"})).run("2026-09-02")
        # Day2 不应被空 txt 永久跳过，必须重新提取并落正文
        self.assertGreater(txt_path.stat().st_size, 0)
        queue = (state / "daily/queue-latest.txt").read_text(encoding="utf-8")
        self.assertIn("公司甲|C4|光模块", queue)  # 正文被扫描召回，未丢失

    def test_future_watermark_does_not_skip_backfill_interval(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        (state / "qa_watermarks.json").write_text(json.dumps({"000001": "2027-01-01"}), encoding="utf-8")
        client = FixtureClient()
        DailyMirror(source, state, client).run("2026-09-01")
        # 不返回零宽/未来窗口，退回以 run_date 为终点的 7 天重叠窗口
        self.assertEqual(client.qa_since["000001"], "2026-08-25")

    def test_corrupt_or_non_dict_state_files_are_not_trusted(self):
        source = self.make_source()
        state = Path(tempfile.mkdtemp())
        (state / "qa_watermarks.json").write_text("[1,2,3]", encoding="utf-8")  # 非 dict
        client = FixtureClient()
        DailyMirror(source, state, client).run("2026-09-01")
        self.assertEqual(client.qa_since["000001"], "2023-01-01")  # 坏水位 → 全量回填

        state2 = Path(tempfile.mkdtemp())
        (state2 / "qa_watermarks.json").write_text('{"000001": "not-a-date"}', encoding="utf-8")
        client2 = FixtureClient()
        DailyMirror(source, state2, client2).run("2026-09-01")
        self.assertEqual(client2.qa_since["000001"], "2023-01-01")  # 非法日期 → 全量回填

    def test_requests_client_keeps_run_level_p5w_breaker(self):
        client = RequestsClient.__new__(RequestsClient)
        calls = []

        class FakeModule:
            ROOT = None
            _p5w_down = {"v": False, "reason": ""}

            def fetch(self, code, since):
                calls.append(code)
                FakeModule._p5w_down["v"] = True  # 模拟 p5w 连接失败触发熔断

        client.source_root = ROOT
        client._fetch_module_cache = FakeModule()
        client.fetch_qa("000001", "2023-01-01", [])
        client.fetch_qa("000002", "2023-01-01", [])
        self.assertEqual(calls, ["000001", "000002"])
        self.assertTrue(FakeModule._p5w_down["v"])  # 熔断跨公司保留，未被逐家重置
        self.assertIs(client._fetch_module(), client._fetch_module())  # 模块按运行缓存

    def test_ir_client_reads_original_three_page_window(self):
        client = RequestsClient.__new__(RequestsClient)
        pages = []

        def post(data):
            pages.append(data["pageNum"])
            return [{"page": data["pageNum"]}] if data["pageNum"] != "3" else []

        client._post = post
        rows = client.query_ir("relation", "category_dyhd_szdy", "2026-08-29", "2026-09-01")
        self.assertEqual(pages, ["1", "2", "3"])
        self.assertEqual(len(rows), 2)


def _load_fetch_qa():
    spec = importlib.util.spec_from_file_location("_test_domestic_fetch_qa", ROOT / "corpus/_fetch_qa.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload = payload if payload is not None else {}
        self.text = text
        self.encoding = "utf-8"

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class FetchQaChannelTests(unittest.TestCase):
    """corpus/_fetch_qa.py：抓取失败不能冒充零条，分页必须有界。"""

    def setUp(self):
        try:
            import requests  # noqa: F401  模块加载时依赖
        except ImportError as exc:
            self.skipTest(f"requests 不可用: {exc}")
        self.module = _load_fetch_qa()
        self.module.ROOT = str(Path(tempfile.mkdtemp()))
        self.module.time = types.SimpleNamespace(sleep=lambda *_a, **_k: None, monotonic=time.monotonic)
        self.module._p5w_down["v"] = False
        self.module._p5w_down["reason"] = ""

    def _irm_handler(self, pages, rows_for):
        def handler(method, url, **kw):
            if "queryKeyboardInfo" in url:
                return _FakeResponse({"data": [{"stockCode": "000001", "secid": "9900023"}]})
            pages["n"] += 1
            return _FakeResponse({"data": {"results": rows_for(pages["n"]), "totalPage": 99999}})
        return handler

    def test_p5w_zero_based_first_page_is_not_lost(self):
        pages = []
        def handler(method, url, **kw):
            if "/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            page = kw["data"]["page"]
            pages.append(page)
            if not kw['data'].get('questionerTimeBegin'):
                return _FakeResponse({'rows':[], 'total':0})
            rows = [{"pid": "latest", "replyContent": "最新回答", "replyerTimeStr": "2026-09-09", "questionerTimeStr": "2026-09-09"}] if page == 0 else []
            return _FakeResponse({"rows": rows, "total": 1})
        self.module.request = handler
        self.assertEqual(self.module.fetch("920001", "2026-09-01"), 1)
        self.assertEqual(pages, [0, 0])  # filtered list and latest replies both start at 0
        path = Path(self.module.ROOT) / "corpus/qa/920001/qa.jsonl"
        self.assertEqual(json.loads(path.read_text())["index_id"], "latest")

    def test_existing_irm_and_p5w_mirror_are_not_counted_twice(self):
        row={'code':'000001','index_id':'irm-1','question':'同一个问题','answer':'同一个回答',
             'ask_date':'2026-09-01','answer_date':'2026-09-09','source':'irm.cninfo.com.cn searchResult(infoTypes=11)'}
        self.module._merge_write('000001',[row])
        mirror=dict(row,index_id='p5w-1',answer='同一个回答 (来自：深交所互动易)',source='ir.p5w.net interaction/getNewR.shtml')
        self.assertEqual(self.module._merge_write('000001',[mirror]),1)
        path=Path(self.module.ROOT)/'corpus/qa/000001/qa.jsonl'
        self.assertEqual(json.loads(path.read_text()),row)
        # A changed answer is an update, not a duplicate to discard.
        changed=dict(row,answer='更新后的回答')
        self.module._merge_write('000001',[changed])
        self.assertEqual(json.loads(path.read_text())['answer'],'更新后的回答')

    def test_p5w_date_splitting_shares_request_budget(self):
        pages = []
        self.module.MAX_PAGES = 5
        def handler(method, url, **kw):
            if "/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            page = kw["data"]["page"]
            pages.append(page)
            day = kw['data'].get('questionerTimeBegin', '2026-09-09')
            return _FakeResponse({"rows": [{"pid": str(len(pages)), "replyContent": "回答", "replyerTimeStr": day, "questionerTimeStr": day}], "total": 100})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("920001", "2026-09-01")
        self.assertEqual(len(pages), self.module.MAX_PAGES)
        self.assertIn('请求上限', self.module._trunc['reason'])

    def test_all_channels_unavailable_raises_fetch_failure(self):
        self.module.request = lambda method, url, **kw: _FakeResponse({"data": [], "obj": []}, text="")
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2026-01-01")

    def test_page_cap_raises_fetch_failure(self):
        pages = {"n": 0}

        def rows_for(page):
            return [{"indexId": f"p{page}-{i}", "mainContent": "问", "attachedContent": "答",
                     "attachedPubDate": 1780000000000 + page * 1000 + i, "pubDate": 1780000000000}
                    for i in range(30)]

        self.module.request = self._irm_handler(pages, rows_for)
        # 截断不是成功：必须报错，调用方据此不推进水位
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2026-01-01")
        self.assertEqual(pages["n"], self.module.MAX_PAGES)

    def test_repeated_page_raises_fetch_failure(self):
        pages = {"n": 0}

        def rows_for(page):
            return [{"indexId": "same-page", "mainContent": "问", "attachedContent": "答",
                     "attachedPubDate": 1780000000000, "pubDate": 1780000000000} for _ in range(30)]

        self.module.request = self._irm_handler(pages, rows_for)
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2026-01-01")
        self.assertEqual(pages["n"], 2)  # 第二页与上一页同签名即停，且同样计为不完整

    def test_p5w_repeat_page_raises_fetch_failure(self):
        """北交所原生通道 fetch_p5w 翻页重复：必须截断并失败，不推进水位（2026-09-05 复审漏网#1）。"""
        def handler(method, url, **kw):
            if "ir.p5w.net/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            if "getNewR.shtml" in url:
                return _FakeResponse({"rows": [{"pid": "1", "content": "问", "replyContent": "答",
                                               "replyerTimeStr": "2026-09-01", "questionerTimeStr": "2026-09-01"}], "total": 20})
            return _FakeResponse({})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("920001", "2026-08-25")
        self.assertTrue(self.module._trunc["v"])
        self.assertIn('重复', self.module._trunc['reason'])

    def test_p5w_fallback_truncation_raises_fetch_failure(self):
        """SZ 主通道 0 条 → p5w 兜底翻页重复(m>0)：仍须失败不推进水位（2026-09-05 复审漏网#1）。"""
        def handler(method, url, **kw):
            if "queryKeyboardInfo" in url:
                return _FakeResponse({"data": [{"stockCode": "000001", "secid": "9900023"}]})
            if "searchResult" in url:
                return _FakeResponse({"data": {"results": [], "totalPage": 0}})
            if "ir.p5w.net/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            if "getNewR.shtml" in url:
                return _FakeResponse({"rows": [{"pid": "1", "content": "问", "replyContent": "答",
                                               "replyerTimeStr": "2026-09-01", "questionerTimeStr": "2026-09-01"}], "total": 20})
            return _FakeResponse({})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2023-01-01")
        self.assertTrue(self.module._trunc["v"])

    def test_shrink_fallback_truncation_raises_fetch_failure(self):
        """全量快照请求下主通道缩水 → p5w 兜底翻页重复(m>0)：仍须失败不推进水位（2026-09-05 复审漏网#1）。"""
        qa_dir = Path(self.module.ROOT) / "corpus/qa/000001"
        qa_dir.mkdir(parents=True, exist_ok=True)
        rows = [json.dumps({"code": "000001", "secid": "x", "question": f"q{i}", "answer": "a",
                            "answer_date": "2026-01-01", "ask_date": "2026-01-01", "index_id": f"s{i}",
                            "empty": False, "fetch_date": "2026-01-01", "source": "x"}) for i in range(30)]
        (qa_dir / "qa.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

        def handler(method, url, **kw):
            if "queryKeyboardInfo" in url:
                return _FakeResponse({"data": [{"stockCode": "000001", "secid": "9900023"}]})
            if "searchResult" in url:
                return _FakeResponse({"data": {"results": [{"indexId": "new1", "mainContent": "问",
                                                            "attachedContent": "答", "attachedPubDate": 1788220800000,
                                                            "pubDate": 1788220800000}], "totalPage": 1}})
            if "ir.p5w.net/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            if "getNewR.shtml" in url:
                return _FakeResponse({"rows": [{"pid": "1", "content": "问", "replyContent": "答",
                                               "replyerTimeStr": "2026-09-01", "questionerTimeStr": "2026-09-01"}], "total": 20})
            return _FakeResponse({})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2023-01-01")
        self.assertTrue(self.module._trunc["v"])

    def test_incremental_window_does_not_trigger_snapshot_shrink_fallback(self):
        """增量窗口天然小于历史快照：不能触发 p5w 缩水兜底。"""
        calls = {"p5w": 0}
        real_p5w = self.module.fetch_p5w

        def counting_p5w(code, since):
            calls["p5w"] += 1
            return real_p5w(code, since)

        self.module.fetch_p5w = counting_p5w

        def make_rows(page, size, ts):
            return [{"indexId": f"p{page}-{i}", "mainContent": "问", "attachedContent": "答",
                     "attachedPubDate": ts + page * 1000 + i, "pubDate": ts}
                    for i in range(size)]

        def only_first_page(size, ts):
            return lambda page: make_rows(page, size, ts) if page == 1 else []

        # 全量快照：一页 30 条后正常结束（回答日 2026-05-28，晚于 since）
        self.module.request = self._irm_handler({"n": 0}, only_first_page(30, 1780000000000))
        self.assertEqual(self.module.fetch("000001", "2023-01-01"), 30)
        # 增量窗口：1 条新问答（回答日 2026-09-01，落在 since=2026-08-25 之后），
        # 条数远小于快照 30 条，但 since > FULL_SNAPSHOT_SINCE，不做缩水比较
        self.module.request = self._irm_handler({"n": 0}, only_first_page(1, 1788220800000))
        self.assertEqual(self.module.fetch("000001", "2026-08-25"), 1)
        self.assertEqual(calls["p5w"], 0)  # 增量小结果不再被当成快照缩水

    def test_p5w_ignored_date_filter_with_zero_retained_still_fails(self):
        """主通道0条且P5W忽略日期筛选：不能把本地过滤后的0当成查全。"""
        def handler(method, url, **kw):
            if "queryKeyboardInfo" in url:
                return _FakeResponse({"data": [{"stockCode": "000001", "secid": "9900023"}]})
            if "searchResult" in url:
                return _FakeResponse({"data": {"results": [], "totalPage": 0}})
            if "ir.p5w.net/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            if "getNewR.shtml" in url:
                # 翻页重复(截断)，且全部早于 since，过滤后 m=0
                return _FakeResponse({"rows": [{"pid": "1", "content": "问", "replyContent": "答",
                                               "replyerTimeStr": "2026-01-01", "questionerTimeStr": "2026-01-01"}], "total": 20})
            return _FakeResponse({})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2026-08-25")
        self.assertTrue(self.module._trunc["v"])
        self.assertIn('筛选未生效', self.module._trunc['reason'])

    def test_shrink_fallback_ignored_date_filter_with_zero_retained_still_fails(self):
        """全量快照请求下主通道缩水 → p5w 兜底翻页截断且 since 过滤后 m=0：
        仍须失败，不能因 m=0 漏过 _trunc（2026-09-05 第三稿预检漏网）。
        """
        qa_dir = Path(self.module.ROOT) / "corpus/qa/000001"
        qa_dir.mkdir(parents=True, exist_ok=True)
        rows = [json.dumps({"code": "000001", "secid": "x", "question": f"q{i}", "answer": "a",
                            "answer_date": "2026-01-01", "ask_date": "2026-01-01", "index_id": f"s{i}",
                            "empty": False, "fetch_date": "2026-01-01", "source": "x"}) for i in range(30)]
        (qa_dir / "qa.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

        def handler(method, url, **kw):
            if "queryKeyboardInfo" in url:
                return _FakeResponse({"data": [{"stockCode": "000001", "secid": "9900023"}]})
            if "searchResult" in url:
                return _FakeResponse({"data": {"results": [{"indexId": "new1", "mainContent": "问",
                                                            "attachedContent": "答", "attachedPubDate": 1788220800000,
                                                            "pubDate": 1788220800000}], "totalPage": 1}})
            if "ir.p5w.net/c/" in url:
                return _FakeResponse(text='id="pid" value="P123"')
            if "getNewR.shtml" in url:
                # 翻页重复(截断)，且全部早于 2023-01-01 过滤后 m=0
                return _FakeResponse({"rows": [{"pid": "1", "content": "问", "replyContent": "答",
                                               "replyerTimeStr": "2022-01-01", "questionerTimeStr": "2022-01-01"}], "total": 20})
            return _FakeResponse({})
        self.module.request = handler
        with self.assertRaises(self.module.FetchFailure):
            self.module.fetch("000001", "2023-01-01")
        self.assertTrue(self.module._trunc["v"])


if __name__ == "__main__":
    unittest.main()
