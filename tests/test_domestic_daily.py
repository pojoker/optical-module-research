import json
import re
import tempfile
import unittest
from pathlib import Path

from domestic_daily import DailyMirror, FixtureClient
from domestic_daily.core import RequestsClient


ROOT = Path(__file__).parents[1]


class MirrorTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
