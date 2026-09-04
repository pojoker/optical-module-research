"""Reader-side semantics: five-level coverage and asserted/corroborated display."""

from __future__ import annotations

import csv
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from calls.renderer import render
from calls.schema import FILES


ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReaderSemanticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "calls").mkdir()
        for filename in FILES:
            shutil.copy2(ROOT / "calls" / filename, self.root / "calls" / filename)
        for filename in ("tree.yaml", "route_bom.csv", "points.csv"):
            shutil.copy2(ROOT / filename, self.root / filename)
        render(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _index(self) -> str:
        return (self.root / "calls" / "out" / "README.md").read_text(encoding="utf-8")

    def _card(self, company_id: str) -> str:
        _, universe = None, _load(self.root / "calls" / "universe.csv")
        name = next(row["company_name"] for row in universe if row["company_id"] == company_id)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        path = self.root / "calls" / "out" / "companies" / f"{company_id.lower()}-{slug}.md"
        return path.read_text(encoding="utf-8")

    def _expected_levels(self) -> dict[str, int]:
        universe = _load(self.root / "calls" / "universe.csv")
        sources = _load(self.root / "calls" / "sources.csv")
        claims = _load(self.root / "calls" / "claims.csv")
        events = _load(self.root / "calls" / "events.csv")
        evidence = _load(self.root / "calls" / "event_evidence.csv")
        event_claims = _load(self.root / "calls" / "event_claims.csv")
        enabled = {row["company_id"] for row in universe if row["enabled"] == "yes"}
        source_by_id = {row["source_id"]: row for row in sources}
        slots: dict[str, set[str]] = {}
        available: dict[str, set[str]] = {}
        for row in sources:
            if row["company_id"] in enabled and row["source_scope"] == "quarterly":
                slots.setdefault(row["company_id"], set()).add(row["slot_label"])
                if row["availability"] == "available":
                    available.setdefault(row["company_id"], set()).add(row["slot_label"])
        claim_companies = {source_by_id[row["source_id"]]["company_id"] for row in claims}
        reviewed_companies = {
            source_by_id[row["source_id"]]["company_id"]
            for row in claims if row["review_status"] == "reviewed"
        }
        anchor_reviewed_claims = {
            row["event_claim_id"] for row in event_claims if row["review_status"] == "anchor_reviewed"
        }
        event_companies = {
            row["primary_subject_id"] for row in events
            if row["primary_subject_id"] in enabled and any(
                link["event_id"] == row["event_id"] and link["event_claim_id"] in anchor_reviewed_claims
                for link in evidence
            )
        }
        return {
            "slot": sum(len(slots.get(c, set())) == 4 for c in enabled),
            "available_source": sum(len(available.get(c, set())) == 4 for c in enabled),
            "claim": len(claim_companies & enabled),
            "reviewed_claim": len(reviewed_companies & enabled),
            "reviewed_event": len(event_companies),
        }

    def test_five_level_coverage_denominators_are_recomputable(self) -> None:
        expected = self._expected_levels()
        self.assertEqual(
            expected,
            {"slot": 39, "available_source": 36, "claim": 12, "reviewed_claim": 12, "reviewed_event": 15},
        )
        index = self._index()
        self.assertIn("分母：正式季度池 39 家 enabled 公司", index)
        self.assertIn("| 季度槽登记 |", index)
        self.assertIn("| 可用来源 |", index)
        self.assertIn("| 陈述登记 |", index)
        self.assertIn("| 已核陈述 |", index)
        self.assertIn("| 已核事件 |", index)
        for count in expected.values():
            self.assertIn(f"| {count} | 39 |", index)
        self.assertNotIn("| 39 | 39 | 39 |\n", index)

    def test_source_inventory_is_not_conclusion_coverage(self) -> None:
        index = self._index()
        self.assertIn("信源底账：`sources.csv` 共 166 行", index)
        self.assertIn("季度槽材料 163 行", index)
        self.assertIn("季度槽位 156 个", index)
        self.assertIn("不能单独用“N 家公司、M 行来源”表达研究结论覆盖", index)
        self.assertIn("信源底账行数只是采集记录，不等于结论覆盖", index)

    def test_company_cards_show_five_levels_and_reviewed_semantics(self) -> None:
        self.assertIn("季度槽登记：4/4", self._card("LITE"))
        self.assertIn("可用来源：2/4", self._card("LITE"))
        self.assertIn("可用来源：2/4", self._card("AAOI"))
        self.assertIn("可用来源：3/4", self._card("AXTI"))
        for company_id in ("LITE", "AAOI", "AXTI"):
            card = self._card(company_id)
            self.assertIn("五级覆盖", card)
            self.assertIn("reviewed 仅表示原文已核，不代表独立来源交叉", card)
            self.assertIn("同源双证（同一 origin_group 的多份材料）不得升级为 corroborated", card)
            self.assertIn("asserted", card)
            self.assertIn("corroborated", card)
        self.assertIn("`reviewed` 仅表示原文已核", self._card("COHR"))

    def test_asserted_and_corroborated_are_listed_separately(self) -> None:
        index = self._index()
        self.assertIn("- asserted：32 条", index)
        self.assertIn("- corroborated：2 条", index)
        self.assertIn("EV013、EV014", index)
        self.assertIn("同源双证（同一 origin_group 的多份材料）不得升级为 corroborated", index)
        self.assertIn("asserted 不代表已确认", index)
        # corroborated display must rest on evidence with an origin independent
        # of the first-party origin, re-derived from the ledger.
        evidence = _load(ROOT / "calls" / "event_evidence.csv")
        event_claims = _load(ROOT / "calls" / "event_claims.csv")
        disclosures = _load(ROOT / "calls" / "disclosures.csv")
        claim_by_id = {row["event_claim_id"]: row for row in event_claims}
        for event_id in ("EV013", "EV014"):
            origins = {
                (row["independence_class"], row["origin_group"])
                for row in evidence if row["event_id"] == event_id
            }
            reviewed_origins = {
                origin for origin in origins
                if claim_by_id[
                    next(r["event_claim_id"] for r in evidence if r["event_id"] == event_id and r["origin_group"] == origin[1])
                ]["review_status"] == "anchor_reviewed"
            }
            first_party = {origin for origin in reviewed_origins if origin[0] in {"first_party", "same_origin"}}
            independent = reviewed_origins - first_party
            self.assertTrue(independent, event_id)
            disclosure_origins = {
                row["origin_group"] for row in disclosures
                if row["origin_group"] in {origin[1] for origin in independent}
            }
            self.assertTrue(disclosure_origins)

    def test_same_origin_double_evidence_cannot_reach_reader_as_corroborated(self) -> None:
        from calls.event_intelligence import load_event_facts

        # Give asserted EV001 a second, anchor-reviewed evidence row that shares
        # the first-party origin_group: same-source double support must not
        # upgrade the event to corroborated anywhere, including reader output.
        base_claim = next(
            row for row in _load(ROOT / "calls" / "event_claims.csv") if row["event_claim_id"] == "ECL001"
        )
        self._append("disclosures.csv", {
            "disclosure_id": "D_AAOI_SAME_ORIGIN_ECHO",
            "publisher_entity_id": "AAOI",
            "title": "Same-origin echo of the order announcement",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "counterparty",
            "canonical_url": "https://investors.ao-inc.com/node/16751-echo",
            "origin_group": "OG_AAOI_20260309_ORDER",
            "published_at": "2026-03-10",
            "discovered_at": "2026-08-09",
            "retrieved_at": "2026-08-09",
            "reviewed_at": "2026-08-09",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "echo paragraph",
        })
        self._append("event_claims.csv", {
            "event_claim_id": "ECL900",
            "disclosure_id": "D_AAOI_SAME_ORIGIN_ECHO",
            "claimant_entity_id": "AAOI",
            "claimant_role": "customer",
            "statement_kind": "fact_assertion",
            "quote": base_claim["quote"],
            "anchor": "echo paragraph",
            "summary": "同源转述",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-08-09",
        })
        self._append("event_evidence.csv", {
            "evidence_id": "EE900",
            "event_id": "EV001",
            "event_claim_id": "ECL900",
            "relationship": "supports",
            "independence_class": "counterparty",
            "origin_group": "OG_AAOI_20260309_ORDER",
        })
        self._mutate("events.csv", "EV001", {"event_status": "corroborated"})
        with self.assertRaisesRegex(Exception, "lacks independent supporting origin"):
            load_event_facts(self.root)

    def _append(self, filename: str, row: dict[str, str]) -> None:
        path = self.root / "calls" / filename
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = list(reader)
        rows.append({field: row.get(field, "") for field in fields})
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _mutate(self, filename: str, row_id: str, changes: dict[str, str]) -> None:
        path = self.root / "calls" / filename
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = list(reader)
        for row in rows:
            if row[fields[0]] == row_id:
                row.update(changes)
                break
        else:
            self.fail(f"no row matched in {filename}")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
