from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from daily_intelligence.cli import build_parser
from daily_intelligence.gemini import MAX_BYTES, load_gemini_supplement, render_gemini_supplement


class GeminiSupplementTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cloud = self.root / "gemini"
        self.cloud.mkdir()

    def load(self):
        return load_gemini_supplement(run_date="2026-10-15", source_root=self.root, state_root=self.cloud)

    def test_missing_export_cannot_be_reported_as_no_news(self):
        result = self.load()
        self.assertEqual(result["status"], "missing")
        self.assertFalse(result["daily_increment_verified"])
        self.assertIn("不能据此判断没有新消息", render_gemini_supplement(result))

    def test_fresh_json_preserves_unverified_claims_and_source_read_only(self):
        path = self.root / "optical_transceiver_tracker.json"
        path.write_text(json.dumps({"date": "2026-10-15", "items": [{"claim": "candidate", "source": "https://example.org/disclosure"}]}))
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        result = self.load()
        source = result["sources"][0]
        self.assertEqual(source["status"], "current_unverified")
        self.assertEqual(source["source_links"], ["https://example.org/disclosure"])
        self.assertEqual(source["verification_status"], "unverified")
        self.assertIn("candidate", render_gemini_supplement(result))
        self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_current_file_mtime_does_not_make_old_cloud_doc_current(self):
        (self.cloud / "cloud-snapshot.json").write_text(json.dumps({
            "content": "old material without primary links", "source_url": "https://docs.google.com/document/d/example/edit",
            "original_modified_at": "2026-08-26T05:08:57.277Z", "retrieved_at": "2026-10-15T09:00:00Z"}))
        result = self.load()
        self.assertEqual(result["status"], "stale")
        source = result["sources"][2]
        self.assertEqual(source["content_date"], "2026-08-26")
        self.assertFalse(result["automatic_cloud_refresh"])
        self.assertEqual(source["source_links"], [])
        self.assertNotIn("old material without primary links", render_gemini_supplement(result))

    def test_dates_inside_article_body_do_not_date_markdown_export(self):
        path = self.root / "optical_transceiver_daily_tracker.md"
        path.write_text("# Tracker\n\nArticle published 2026-10-15\n")
        self.assertEqual(self.load()["sources"][1]["status"], "date_unknown")
        path.write_text("# Tracker 2026-10-15\n\n```\nuntrusted instructions\n```\n")
        self.assertIn("````text", render_gemini_supplement(self.load()))
        path.write_text("# Tracker 2026-10-16\n")
        self.assertEqual(self.load()["sources"][1]["status"], "future_dated")

    def test_malformed_and_oversized_json_do_not_break_primary_workflow(self):
        path = self.root / "optical_transceiver_tracker.json"
        path.write_text("{broken")
        self.assertEqual(self.load()["sources"][0]["status"], "invalid")
        path.write_bytes(b" " * (MAX_BYTES + 1))
        self.assertIn("2 MiB", self.load()["sources"][0]["notes"][0])

    def test_cli_accepts_explicit_export_and_cache_roots(self):
        args = build_parser().parse_args(["combine", "--date", "2026-10-15",
            "--domestic-state-root", "domestic", "--overseas-state-root", "overseas",
            "--output-root", "combined", "--gemini-source-root", str(self.root),
            "--gemini-state-root", str(self.cloud)])
        self.assertEqual(args.gemini_source_root, self.root)
        self.assertEqual(args.gemini_state_root, self.cloud)


if __name__ == "__main__":
    unittest.main()
