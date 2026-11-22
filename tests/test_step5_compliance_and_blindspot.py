"""Step 5 regression tests: overseas compliance KB (KN011-KN014), DRQ0046 closure, blind-spot leads & Gemini watermark."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402
from corpus.daily_review import sync_daily_queue  # noqa: E402


def load_csv(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            h.update(chunk)
    return h.hexdigest()


class Step5ComplianceAndBlindspotTest(unittest.TestCase):
    def test_kn011_to_kn014_primary_evidence_and_no_forbidden_phrases(self) -> None:
        raw_yaml = (ROOT / "knowledge.yaml").read_text(encoding="utf-8")
        doc = yaml.safe_load(raw_yaml)
        kb = doc.get("knowledge") or []
        self.assertEqual(len(kb), 14)
        self.assertEqual([k["id"] for k in kb], [f"KN{i:03d}" for i in range(1, 15)])

        by_id = {k["id"]: k for k in kb}
        for kid in ("KN011", "KN012", "KN013", "KN014"):
            kn_blob = json.dumps(by_id[kid], ensure_ascii=False)
            for bad in ("已覆盖", "已完成", "已回答"):
                self.assertNotIn(bad, kn_blob)

        # KN011: 4 CBP rulings + USTR 2027-01-09 & China 2027-01-10 tariff window
        kn11 = by_id["KN011"]
        kn11_blob = json.dumps(kn11, ensure_ascii=False)
        for token in ("H335829", "N359369", "N344720", "N358465", "2027-01-09", "2027-01-10"):
            self.assertIn(token, kn11_blob)

        # KN012: FCC 26-50 / 91 FR 57798 (effective 2026-10-13), DA 26-1130A1, S.5548
        kn12_blob = json.dumps(by_id["KN012"], ensure_ascii=False)
        for token in ("91 FR 57798", "2.903(b)(2)", "2026-10-13", "FCC-26-50A1", "DA 26-1130A1", "BILLS-119s5548is"):
            self.assertIn(token, kn12_blob)

        # KN013: MOFCOM/MOST 2026 No.48 (266507X >=800 GB/s, >10,000 cards) + 301421 2026-037 + P202
        kn13 = by_id["KN013"]
        kn13_blob = json.dumps(kn13, ensure_ascii=False)
        for token in ("第 48 号", "266507X", "800", "10,000", "2026-037", "P202"):
            self.assertIn(token, kn13_blob)
        self.assertTrue(any("#L17..78" in str(ev.get("锚", "")) for ev in kn13["证据"]))

        # KN014: BIS EAR 734.9 & Part 744 + EU EED 2023/1791 Art.12 (WAF -> url anchor, EC HTTP-200 -> web_snapshot)
        kn14 = by_id["KN014"]
        kn14_blob = json.dumps(kn14, ensure_ascii=False)
        for token in ("734.9", "744", "2023/1791", "2024/1364", "C(2026) 3472"):
            self.assertIn(token, kn14_blob)
        eurlex_anchors = [ev for ev in kn14["证据"] if "eur-lex.europa.eu" in str(ev.get("锚", ""))]
        ec_snapshots = [ev for ev in kn14["证据"] if ev.get("锚型") == "web_snapshot" and "europa.eu" in str((ev.get("锚") or {}).get("原URL", ""))]
        self.assertGreaterEqual(len(eurlex_anchors), 2)
        self.assertTrue(all(ev["锚型"] == "url" for ev in eurlex_anchors))
        self.assertGreaterEqual(len(ec_snapshots), 2)

        # Every web_snapshot in KN011..KN014 must match its archived file's SHA-256 on disk
        for kn_id in ("KN011", "KN012", "KN013", "KN014"):
            for ev in by_id[kn_id]["证据"]:
                if ev["锚型"] == "web_snapshot":
                    anchor = ev["锚"]
                    arc = ROOT / anchor["存档路径"]
                    self.assertTrue(arc.is_file(), f"Missing snapshot for {kn_id}: {arc}")
                    self.assertEqual(sha256_file(arc), anchor["SHA256"])

    def test_scan_daily_review_knowledge_ref_validation(self) -> None:
        base_row = {
            "queue_id": "DRQ9001",
            "priority": "P1",
            "trigger_type": "T1_lifecycle_shift",
            "status": "ingested_to_kb",
            "entity_name": "测试合规条目",
            "kb_target_ref": "knowledge:KN011",
            "missing_verification_gate": "",
        }

        scan.ERR.clear()
        scan._check_daily_review_queue(
            [base_row],
            {"P275"},
            {"E012"},
            {"CLG0632"},
            {"TL9001"},
            call_ids={"EV061"},
            kn_ids={"KN011"},
        )
        self.assertEqual(scan.ERR, [])

        for bad_ref in ("knowledge:KN999", "knowledge:BAD"):
            scan.ERR.clear()
            scan._check_daily_review_queue(
                [dict(base_row, kb_target_ref=bad_ref)],
                {"P275"},
                {"E012"},
                {"CLG0632"},
                {"TL9001"},
                call_ids={"EV061"},
                kn_ids={"KN011"},
            )
            self.assertTrue(scan.ERR, f"Expected scan.ERR to reject {bad_ref}")
        scan.ERR.clear()

    def test_manifests_sha256_refs_cap_entity_nodes_and_drq_state(self) -> None:
        # 1. refs/ strict <= 8 files (exact 8)
        refs_files = [p for p in (ROOT / "refs").iterdir() if p.is_file()]
        self.assertEqual(len(refs_files), 8)

        # 2. Non-frozen codes 300916 / 301660 must NEVER create corpus/ir/<code>
        self.assertFalse((ROOT / "corpus/ir/300916").exists())
        self.assertFalse((ROOT / "corpus/ir/301660").exists())
        self.assertTrue((ROOT / "corpus/ir/301314").is_dir())
        self.assertTrue((ROOT / "corpus/ir/301421").is_dir())

        # 3. Compliance manifest: 24 HTTP-200 archived files SHA-256 verified
        cm = json.loads((ROOT / "out/step5-compliance-and-blindspot-20261122/compliance_manifest.json").read_text(encoding="utf-8"))
        c_archived = [x for x in cm["items"] if x.get("status") == "http_200_archived"]
        self.assertEqual(len(c_archived), 24)
        for it in c_archived:
            p = ROOT / it["saved_path"]
            self.assertTrue(p.is_file(), f"Missing archived compliance file: {p}")
            self.assertEqual(sha256_file(p), it["sha256"])
            if it.get("sidecar_txt_path"):
                sp = ROOT / it["sidecar_txt_path"]
                self.assertTrue(sp.is_file())
                self.assertEqual(sha256_file(sp), it["sidecar_txt_sha256"])

        # 4. Blind-spot manifest: 16 HTTP-200 archived files SHA-256 verified
        bv = json.loads((ROOT / "out/step5-compliance-and-blindspot-20261122/blindspot_leads_verdicts.json").read_text(encoding="utf-8"))
        b_archived = bv["archived_primary_files"]
        self.assertEqual(len(b_archived), 16)
        for it in b_archived:
            p = ROOT / it["primary_rel"]
            t = ROOT / it["txt_rel"]
            self.assertTrue(p.is_file(), f"Missing blindspot primary file: {p}")
            self.assertTrue(t.is_file(), f"Missing blindspot sidecar txt: {t}")
            self.assertEqual(sha256_file(p), it["primary_sha256"])
            self.assertEqual(sha256_file(t), it["txt_sha256"])

        # 5. Symmetric entity registration N174-N179 in both entity_nodes.csv and refs/entity-registry.yaml
        en_ids = {r["node_id"]: r for r in load_csv("corpus/salvaged/entity_nodes.csv")}
        reg = yaml.safe_load((ROOT / "refs/entity-registry.yaml").read_text(encoding="utf-8"))
        reg_nodes = {n["node_id"]: n for n in ((reg.get("node_directory") or {}).get("nodes") or [])}
        self.assertEqual(reg["node_directory"]["total_nodes"], len(en_ids))
        for nid in ("N174", "N175", "N176", "N177", "N178", "N179"):
            self.assertIn(nid, en_ids)
            self.assertIn(nid, reg_nodes)

        # 6. review_queue.csv: 105 rows, DRQ0046 closed, pending_primary_text == 1 (DRQ0037), DRQ0098..DRQ0105 enrolled
        q_rows = load_csv("corpus/daily_review/review_queue.csv")
        self.assertEqual(len(q_rows), 105)
        q_by_id = {r["queue_id"]: r for r in q_rows}

        pending_txt = [r for r in q_rows if r["status"] == "pending_primary_text"]
        self.assertEqual([r["queue_id"] for r in pending_txt], ["DRQ0037"])

        self.assertEqual(q_by_id["DRQ0046"]["status"], "ingested_to_kb")
        self.assertEqual(
            q_by_id["DRQ0046"]["kb_target_ref"],
            "knowledge:KN011;knowledge:KN012;knowledge:KN013;knowledge:KN014",
        )
        self.assertEqual(q_by_id["DRQ0046"]["missing_verification_gate"], "")

        expected_new = {
            "DRQ0098": ("朗特智能 / 成都奥捷", "pending_filing_anchor", ""),
            "DRQ0099": ("科瑞思 / 宏钢光电", "pending_filing_anchor", "points:P258"),
            "DRQ0100": ("波长光电", "ingested_to_kb", "knowledge:KN013"),
            "DRQ0101": ("上海羲禾科技", "pending_filing_anchor", ""),
            "DRQ0102": ("粤芯半导体", "watch_deferred", ""),
            "DRQ0103": ("Optical Internetworking Forum (OIF)", "watch_deferred", ""),
            "DRQ0104": (
                "NVIDIA × Lambda",
                "ingested_to_kb",
                "calls:WATCH_LAMBDA;calls:D_NVDA_20261116_LAMBDA_CPO;calls:D_LAMBDA_20261116_NVDA_CPO;calls:ECL064;calls:ECL065;calls:EV061;calls:EE064;calls:EE065",
            ),
            "DRQ0105": ("安费诺(Amphenol)", "watch_deferred", ""),
        }
        for qid, (ent, st, kb_ref) in expected_new.items():
            self.assertEqual(q_by_id[qid]["entity_name"], ent)
            self.assertEqual(q_by_id[qid]["status"], st)
            self.assertEqual(q_by_id[qid]["kb_target_ref"], kb_ref)

    def test_gemini_cloud_snapshot_watermark_and_future_untriaged_detection(self) -> None:
        stats = json.loads((ROOT / "corpus/daily_review/triage_stats.json").read_text(encoding="utf-8"))
        gcs = stats["gemini_cloud_snapshot"]
        self.assertEqual(gcs["triaged_through_date"], "2026-11-18")
        self.assertEqual(gcs["untriaged_entry_dates"], [])
        self.assertEqual(gcs["untriaged_entry_count"], 0)
        if gcs["available"]:
            self.assertEqual(gcs["latest_entry_date"], "2026-11-18")
            self.assertGreaterEqual(gcs["total_daily_entries"], 81)

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cloud-snapshot.json"
            p.write_text(
                json.dumps(
                    {
                        "title": "Test Doc",
                        "retrieved_at": "2026-11-23T01:00:00Z",
                        "original_modified_at": "2026-11-23T00:50:00Z",
                        "content": "[2026-11-18] baseline\n[2026-11-23] brand new blindspot item\n",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            res = sync_daily_queue.scan_gemini_cloud_snapshot(snapshot_path=p, triaged_through_date="2026-11-18")
            self.assertTrue(res["available"])
            self.assertEqual(res["latest_entry_date"], "2026-11-23")
            self.assertEqual(res["untriaged_entry_dates"], ["2026-11-23"])
            self.assertEqual(res["untriaged_entry_count"], 1)

            missing = sync_daily_queue.scan_gemini_cloud_snapshot(
                snapshot_path=Path(td) / "absent.json", triaged_through_date="2026-11-18"
            )
            self.assertFalse(missing["available"])
            self.assertEqual(missing["untriaged_entry_dates"], [])
