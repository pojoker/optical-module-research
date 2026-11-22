from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from tools.research.build_relation_leads import build_domain_projection


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TYPES = {
    "part_of",
    "connects_to",
    "requires",
    "has_capability",
    "offers_product",
    "implements_route",
    "has_stage",
    "supported_by",
}


class DomainRelationViewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.projection = build_domain_projection(ROOT)

    def test_contract_is_exactly_the_small_domain_vocabulary(self) -> None:
        contract = yaml.safe_load(
            (ROOT / "contracts" / "domain_relation_types.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {row["name"] for row in contract["relation_types"]}, EXPECTED_TYPES
        )
        self.assertEqual(
            set(contract["disciplines"]),
            {
                "source_encoded != derived_candidate",
                "actual != planned",
                "lead != formal_question",
                "generated_output != canonical_data",
            },
        )

    def test_projection_is_deterministic_and_contains_no_state_machine_fields(self) -> None:
        second = build_domain_projection(ROOT)
        self.assertEqual(
            json.dumps(self.projection, ensure_ascii=False, sort_keys=True),
            json.dumps(second, ensure_ascii=False, sort_keys=True),
        )
        forbidden = {
            "workflow_status", "resolution_status", "slot_state", "snapshot",
            "manifest", "reopened", "satisfied", "receipt",
        }
        for row in self.projection["relations"] + self.projection["leads"]:
            self.assertFalse(forbidden & set(row))

    def test_automatic_view_never_claims_product_offer_or_route_implementation(self) -> None:
        emitted = {row["relation_type"] for row in self.projection["relations"]}
        self.assertTrue(emitted <= EXPECTED_TYPES)
        self.assertNotIn("offers_product", emitted)
        self.assertNotIn("implements_route", emitted)
        self.assertTrue(all(row["origin"] == "source_encoded" for row in self.projection["relations"]))

    def test_capability_overlap_stays_a_lead(self) -> None:
        lead = next(
            row for row in self.projection["leads"]
            if row["subject_ref"] == "company:Marvell"
            and row["route_item_ref"] == "route_item:RB004"
            and row["matched_cell_ref"] == "cell:C5"
        )
        self.assertTrue(lead["human_review_required"])
        self.assertEqual(lead["lead_kind"], "capability_requirement_overlap")
        self.assertIn("points.csv#P003", lead["source_refs"])
        self.assertIn("route_bom.csv#RB004", lead["source_refs"])
        self.assertIn("不等于完整路线能力", lead["reason"])
        self.assertNotIn("question_id", lead)

    def test_actual_and_planned_stage_relations_remain_distinct(self) -> None:
        stages = [
            row for row in self.projection["relations"]
            if row["relation_type"] == "has_stage"
        ]
        self.assertTrue(any(row["modality"] == "actual" for row in stages))
        self.assertTrue(any(row["modality"] == "planned" for row in stages))
        self.assertFalse(any(row["modality"] == "unspecified" for row in stages))


if __name__ == "__main__":
    unittest.main()
