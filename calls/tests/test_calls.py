from __future__ import annotations

import csv
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from calls.renderer import render
from calls.schema import CANONICAL_FILES, FILES, PANORAMA_FIELDS
from calls.validator import ValidationError, validate
from calls.workbuddy import render_intelligence_section


ROOT = Path(__file__).resolve().parents[2]


class CallsMvpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "calls").mkdir()
        for filename in FILES:
            shutil.copy2(ROOT / "calls" / filename, self.root / "calls" / filename)
        for filename in ("tree.yaml", "route_bom.csv", "points.csv"):
            shutil.copy2(ROOT / filename, self.root / filename)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def mutate(self, filename: str, predicate, changes: dict[str, str]) -> None:
        path = self.root / "calls" / filename
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        for row in rows:
            if predicate(row):
                row.update(changes)
                break
        else:
            self.fail(f"no row matched in {filename}")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def append_source(self, changes: dict[str, str]) -> None:
        path = self.root / "calls" / "sources.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        base = next(row.copy() for row in rows if row["source_id"] == "S_CSCO_2026Q2_A")
        base.update(changes)
        rows.append(base)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def assert_invalid(self, text: str) -> None:
        with self.assertRaisesRegex(ValidationError, text):
            validate(self.root)

    def test_valid_sample(self) -> None:
        self.assertEqual(len(validate(self.root)), 3)

    def test_multiple_materials_in_one_quarter_are_allowed(self) -> None:
        self.append_source({
            "source_id": "S_CSCO_2026Q2_B2",
            "material_type": "webcast_transcript",
            "source_grade": "B",
            "url": "https://investor.cisco.com/example-second-material",
        })
        validate(self.root)

    def test_duplicate_material_is_rejected(self) -> None:
        self.append_source({"source_id": "S_CSCO_2026Q2_DUP"})
        self.assert_invalid("duplicate material")

    def test_broken_claim_reference_is_rejected(self) -> None:
        self.mutate("validations.csv", lambda row: row["validation_id"] == "V001", {"claim_a_id": "CL999"})
        self.assert_invalid("broken claim reference")

    def test_illegal_enum_is_rejected(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL001", {"event_type": "massive_ramp"})
        self.assert_invalid("invalid event_type")

    def test_available_source_requires_anchor(self) -> None:
        self.mutate("sources.csv", lambda row: row["source_id"] == "S_AAOI_Q1_RESULT_A", {"url": "", "local_path": ""})
        self.assert_invalid("lacks URL/local anchor")

    def test_available_local_path_must_exist(self) -> None:
        self.mutate("sources.csv", lambda row: row["source_id"] == "S_AAOI_Q1_RESULT_A", {"url": "", "local_path": "raw/missing.txt"})
        self.assert_invalid("local_path does not exist")

    def test_analyst_cannot_be_management_fact(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL004", {"statement_type": "fact"})
        self.assert_invalid("analyst speech")

    def test_corporate_author_technical_claim_is_valid(self) -> None:
        validate(self.root)
        with (self.root / "calls" / "claims.csv").open(encoding="utf-8", newline="") as handle:
            claim = next(row for row in csv.DictReader(handle) if row["claim_id"] == "CL017")
        self.assertEqual((claim["speaker_role"], claim["statement_type"], claim["event_type"]), ("corporate_author", "technical_demo", "demonstrated"))

    def test_technical_claim_cannot_enter_management_validation(self) -> None:
        self.mutate("validations.csv", lambda row: row["validation_id"] == "V001", {"claim_a_id": "CL017"})
        self.assert_invalid("reviewed management claims")

    def test_technical_claim_cannot_enter_commitment(self) -> None:
        self.mutate("commitments.csv", lambda row: row["commitment_id"] == "CM002", {"claim_id": "CL017"})
        self.assert_invalid("reviewed management forward-looking claim")

    def test_cross_check_requires_matching_theme(self) -> None:
        self.mutate("validations.csv", lambda row: row["validation_id"] == "V001", {"theme_id": "T003"})
        self.assert_invalid("must belong to validation theme")

    def test_analyst_question_cannot_enter_validation(self) -> None:
        self.mutate("validations.csv", lambda row: row["validation_id"] == "V001", {"claim_a_id": "CL004"})
        self.assert_invalid("reviewed management claims")

    def test_candidate_claim_cannot_enter_validation(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL007", {"review_status": "candidate"})
        self.assert_invalid("reviewed management claims")

    def test_independent_cross_check_requires_distinct_companies(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL003", {"source_id": "S_AAOI_2026Q1_C"})
        self.mutate("validations.csv", lambda row: row["validation_id"] == "V002", {"claim_b_id": "CL003", "relationship": "independent"})
        self.assert_invalid("distinct companies")

    def test_available_source_cannot_be_unknown_grade(self) -> None:
        self.mutate("sources.csv", lambda row: row["source_id"] == "S_AAOI_Q1_RESULT_A", {"source_grade": "unknown"})
        self.assert_invalid("cannot have unknown grade/type")

    def test_fulfilled_commitment_requires_evidence(self) -> None:
        self.mutate("commitments.csv", lambda row: row["commitment_id"] == "CM001", {"evidence_source_id": "", "evidence_claim_id": ""})
        self.assert_invalid("lacks available evidence source")

    def test_commitment_origin_must_be_reviewed_management_forecast(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL009", {"speaker_role": "analyst", "statement_type": "analyst_question"})
        self.assert_invalid("reviewed management forward-looking claim")

    def test_fulfillment_evidence_must_be_reviewed_management_fact(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL010", {"statement_type": "forward_looking"})
        self.assert_invalid("fulfillment evidence must be a reviewed management fact")

    def test_resolved_commitment_claim_source_must_match(self) -> None:
        self.mutate("commitments.csv", lambda row: row["commitment_id"] == "CM001", {"evidence_source_id": "S_CSCO_2026Q1_A"})
        self.assert_invalid("evidence claim/source mismatch")

    def test_solution_must_be_child_of_bottleneck(self) -> None:
        self.mutate("themes.csv", lambda row: row["theme_id"] == "T003", {"parent_theme_id": "T001"})
        self.assert_invalid("not a child")

    def test_unknown_point_reference_is_rejected(self) -> None:
        self.mutate("solution_links.csv", lambda row: row["link_id"] == "SL001", {"point_id": "P999999"})
        self.assert_invalid("unknown canonical point_id")

    def test_feedback_broken_technology_claim_is_rejected(self) -> None:
        self.mutate("technology_feedback.csv", lambda row: row["feedback_id"] == "TF001", {"technology_claim_id": "CL999"})
        self.assert_invalid("broken technology claim reference")

    def test_feedback_wrong_technology_role_is_rejected(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL017", {"speaker_role": "management", "statement_type": "fact"})
        self.assert_invalid("reviewed corporate_author evidence")

    def test_feedback_broken_commercial_claim_is_rejected(self) -> None:
        self.mutate("technology_feedback.csv", lambda row: row["feedback_id"] == "TF001", {"commercial_claim_id": "CL999"})
        self.assert_invalid("broken commercial claim reference")

    def test_feedback_wrong_commercial_role_is_rejected(self) -> None:
        self.mutate("claims.csv", lambda row: row["claim_id"] == "CL022", {"speaker_role": "corporate_author", "statement_type": "technical_claim"})
        self.assert_invalid("commercial claim must be reviewed management evidence")

    def test_not_mentioned_feedback_cannot_carry_commercial_confirmation(self) -> None:
        self.mutate("technology_feedback.csv", lambda row: row["feedback_id"] == "TF001", {"feedback_status": "not_mentioned"})
        self.assert_invalid("not_mentioned cannot imply commercial confirmation")

    def test_partially_confirmed_feedback_requires_management_fact(self) -> None:
        self.mutate("technology_feedback.csv", lambda row: row["feedback_id"] == "TF001", {"feedback_status": "partially_confirmed"})
        self.assert_invalid("asserted feedback requires a reviewed management fact")

    def test_renderer_escapes_markdown_table_cells(self) -> None:
        self.mutate("themes.csv", lambda row: row["theme_id"] == "T001", {"theme_name": "需求|卡点\n第二行"})
        render(self.root)
        matrix = (self.root / "calls" / "out" / "theme-matrix.md").read_text(encoding="utf-8")
        self.assertIn("需求\\|卡点 第二行", matrix)

    def test_render_does_not_modify_canonical_files(self) -> None:
        before = {name: _sha256(ROOT / name) for name in CANONICAL_FILES}
        render(ROOT)
        after = {name: _sha256(ROOT / name) for name in CANONICAL_FILES}
        self.assertEqual(before, after)

    def test_render_is_deterministic(self) -> None:
        first_paths = render(self.root)
        first = {path.relative_to(self.root): _sha256(path) for path in first_paths}
        second_paths = render(self.root)
        second = {path.relative_to(self.root): _sha256(path) for path in second_paths}
        self.assertEqual(first, second)

    def test_panorama_projection_is_deterministic_and_source_traced(self) -> None:
        render(self.root)
        path = self.root / "calls" / "out" / "panorama-intelligence.csv"
        first = path.read_bytes()
        render(self.root)
        self.assertEqual(first, path.read_bytes())
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(tuple(reader.fieldnames or ()), PANORAMA_FIELDS)
            row = next(item for item in reader if item["theme_id"] == "T010")
        self.assertIn("S_LITE_BLOG_20260430", row["source_ids"])
        self.assertIn("S_LITE_2026Q3", row["source_ids"])

    def test_workbuddy_intelligence_section_present_and_optional(self) -> None:
        render(self.root)
        projection = self.root / "calls" / "out" / "panorama-intelligence.csv"
        section = render_intelligence_section(projection)
        self.assertIn("海外电话会与官网技术情报", section)
        self.assertIn("独立情报层", section)
        self.assertEqual(render_intelligence_section(self.root / "missing.csv"), "")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
