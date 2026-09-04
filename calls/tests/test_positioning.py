"""Tests for the domestic capability positioning layer (POSITIONING-SPEC)."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from calls.positioning import (
    derive_positioning,
    load_positioning_facts,
    scan_forbidden_words,
)
from calls.renderer import render
from calls.schema import FILES
from calls.validator import ValidationError, validate
from calls.workbuddy import (
    render_all_positioning_blocks,
    render_intelligence_section,
    render_positioning_block,
)


ROOT = Path(__file__).resolve().parents[2]


class PositioningTest(unittest.TestCase):
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

    def read_csv(self, filename: str) -> list[dict[str, str]]:
        with (self.root / "calls" / filename).open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def write_csv(self, filename: str, rows: list[dict[str, str]]) -> None:
        path = self.root / "calls" / filename
        fields = list(rows[0])
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def mutate_csv(self, filename: str, predicate, changes: dict[str, str]) -> None:
        rows = self.read_csv(filename)
        for row in rows:
            if predicate(row):
                row.update(changes)
                break
        else:
            self.fail(f"no row matched in {filename}")
        self.write_csv(filename, rows)

    def mutate_csv_root(self, filename: str, predicate, changes: dict[str, str]) -> None:
        path = self.root / filename
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

    def append_requirement(self, row: dict[str, str]) -> None:
        rows = self.read_csv("constraint_requirements.csv")
        rows.append(row)
        self.write_csv("constraint_requirements.csv", rows)

    def append_point_metric(self, row: dict[str, str]) -> None:
        rows = self.read_csv("point_metrics.csv")
        rows.append(row)
        self.write_csv("point_metrics.csv", rows)

    def append_point(self, row: dict[str, str]) -> None:
        path = self.root / "points.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        rows.append(row)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def assert_invalid(self, text: str) -> None:
        with self.assertRaisesRegex(ValidationError, text):
            validate(self.root)

    def projection(self) -> dict:
        return derive_positioning(load_positioning_facts(self.root))

    # ---- 1. schema, ID and reference closure ----

    def test_requirements_validate_on_clean_sample(self) -> None:
        messages = validate(self.root)
        self.assertEqual(len(messages), 3)

    def test_duplicate_requirement_id_is_rejected(self) -> None:
        self.append_requirement({
            "requirement_id": "CRQ001", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "重复ID", "comparator": "", "target_value": "",
            "unit": "", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("duplicate requirement_id")

    def test_requirement_id_must_start_with_crq(self) -> None:
        self.append_requirement({
            "requirement_id": "RQX", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "某指标", "comparator": "", "target_value": "",
            "unit": "", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("must start with CRQ")

    def test_requirement_unknown_theme_is_rejected(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"theme_id": "T999"})
        self.assert_invalid("unknown theme_id")

    def test_requirement_unknown_cell_is_rejected(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"cell_id": "ZZ9"})
        self.assert_invalid("unknown cell_id")

    def test_requirement_unknown_route_item_is_rejected(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"route_item_id": "RB999"})
        self.assert_invalid("unknown route_item_id")

    def test_requirement_dimension_must_reuse_enum(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"dimension": "quality"})
        self.assert_invalid("invalid dimension")

    # ---- 2. numeric triple all-or-none; qualitative accepted ----

    def test_half_empty_numeric_triple_is_rejected(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"comparator": ">="})
        self.assert_invalid("all empty or all non-empty")

    def test_unsupported_comparator_is_rejected(self) -> None:
        self._add_fixture_point()
        self.append_requirement({
            "requirement_id": "CRQ910", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "月产能", "comparator": "approx", "target_value": "50000",
            "unit": "只", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "测试用",
        })
        self.assert_invalid("unsupported comparator")

    def test_non_numeric_target_value_is_rejected(self) -> None:
        self._add_fixture_point()
        self.append_requirement({
            "requirement_id": "CRQ911", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "月产能", "comparator": ">=", "target_value": "高产能",
            "unit": "只", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "测试用",
        })
        self.assert_invalid("target_value must be numeric")

    def test_qualitative_requirement_is_accepted(self) -> None:
        validate(self.root)
        self.assertEqual(
            self.read_csv("constraint_requirements.csv")[0]["metric_name"],
            "800G数通模块稳定量产与交付能力",
        )

    def _add_fixture_point(self) -> None:
        self.append_point({
            "point_id": "P910", "公司": "测试光模块公司", "cell_id": "MOD1", "状态": "生产中",
            "上市标签": "A股", "命中引语": "月产能 60000 只；已通过批量交付验证", "锚点URL": "https://example.com/2026-07-25",
            "检索日期": "2026-07-25", "判定等级": "edge_backed", "判定会话日期": "2026-07-25",
        })

    def test_point_metric_value_requires_unit_and_as_of(self) -> None:
        self._add_fixture_point()
        self.append_point_metric({
            "metric_id": "PM900", "point_id": "P910", "metric_name": "月产能",
            "value": "60000", "unit": "", "as_of": "", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("value requires unit and as_of")

    def test_point_metric_all_empty_row_is_rejected(self) -> None:
        self._add_fixture_point()
        self.append_point_metric({
            "metric_id": "PM899", "point_id": "P910", "metric_name": "月产能",
            "value": "", "unit": "", "as_of": "", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("value requires unit and as_of on a metric data row")

    def test_point_metric_non_numeric_value_is_rejected(self) -> None:
        self._add_fixture_point()
        self.append_point_metric({
            "metric_id": "PM901", "point_id": "P910", "metric_name": "月产能",
            "value": "many", "unit": "只", "as_of": "2026-07-25", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("value must be numeric")

    def test_point_metric_value_must_appear_in_point_quote(self) -> None:
        self._add_fixture_point()
        self.append_point_metric({
            "metric_id": "PM902", "point_id": "P910", "metric_name": "月产能",
            "value": "99999", "unit": "只", "as_of": "2026-07-25", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("not found verbatim in point P910 quote")

    def test_point_metric_value_requires_point_anchor(self) -> None:
        self._add_fixture_point()
        self.mutate_csv_root("points.csv", lambda r: r["point_id"] == "P910", {"锚点URL": ""})
        self.append_point_metric({
            "metric_id": "PM903", "point_id": "P910", "metric_name": "月产能",
            "value": "60000", "unit": "只", "as_of": "2026-07-25", "review_status": "reviewed", "notes": "",
        })
        self.assert_invalid("lacks anchor")

    # ---- 3. evidence must be a reviewed management claim ----

    def test_analyst_claim_cannot_be_requirement_evidence(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"evidence_claim_ids": "CL004"})
        self.assert_invalid("reviewed management claim")

    def test_corporate_author_claim_cannot_be_requirement_evidence(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"evidence_claim_ids": "CL017"})
        self.assert_invalid("reviewed management claim")

    def test_unknown_claim_cannot_be_requirement_evidence(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"evidence_claim_ids": "CL999"})
        self.assert_invalid("unknown claim CL999")

    def test_candidate_claim_cannot_be_requirement_evidence(self) -> None:
        self.mutate_csv("claims.csv", lambda r: r["claim_id"] == "CL006", {"review_status": "candidate"})
        self.assert_invalid("reviewed management claim")

    def test_evidence_claim_must_share_requirement_theme_and_cell(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"evidence_claim_ids": "CL013"})
        self.assert_invalid("must share requirement theme_id/cell_id")

    def test_evidence_claim_must_share_requirement_cell_even_with_same_theme(self) -> None:
        self.mutate_csv("constraint_requirements.csv", lambda r: r["requirement_id"] == "CRQ001", {"evidence_claim_ids": "CL007"})
        self.assert_invalid("must share requirement theme_id/cell_id")

    # ---- 4. legacy solution links frozen at exact snapshot ----

    def test_solution_links_new_row_is_rejected(self) -> None:
        rows = self.read_csv("solution_links.csv")
        rows.append({
            "link_id": "SL003", "bottleneck_theme_id": "T002", "solution_theme_id": "T003",
            "required_capability": "新匹配", "point_id": "P074", "match_stage": "node_overlap",
            "evidence_status": "insufficient", "missing_evidence": "缺证", "conclusion": "尚无结论",
        })
        self.write_csv("solution_links.csv", rows)
        self.assert_invalid("frozen at exactly SL001/SL002")

    def test_solution_links_legal_field_change_is_rejected(self) -> None:
        self.mutate_csv("solution_links.csv", lambda r: r["link_id"] == "SL001", {"required_capability": "合法改文案"})
        self.assert_invalid("frozen field 'required_capability' changed")

    def test_solution_links_legal_enum_change_is_rejected(self) -> None:
        self.mutate_csv("solution_links.csv", lambda r: r["link_id"] == "SL002", {"evidence_status": "verified"})
        self.assert_invalid("frozen field 'evidence_status' changed")

    def test_solution_links_id_change_is_rejected(self) -> None:
        self.mutate_csv("solution_links.csv", lambda r: r["link_id"] == "SL002", {"link_id": "SL009"})
        self.assert_invalid("frozen at exactly SL001/SL002")

    # ---- 5. requirement_match only by cell, basis cell_only ----

    def test_requirement_match_is_cell_only(self) -> None:
        projection = self.projection()
        matches = [m for m in projection["requirement_matches"] if m["requirement_id"] == "CRQ001"]
        self.assertTrue(matches)
        for match in matches:
            self.assertEqual(match["cell_id"], "MOD1")
            self.assertEqual(match["basis"], "cell_only")
            self.assertEqual(match["route_item_id"], "")
        crq2 = [m for m in projection["requirement_matches"] if m["requirement_id"] == "CRQ002"]
        self.assertTrue(crq2)
        for match in crq2:
            self.assertEqual(match["cell_id"], "C1")
            self.assertEqual(match["basis"], "cell_only")

    # ---- 6. domestic universe filter ----

    def test_overseas_and_unparsed_points_do_not_enter_positioning(self) -> None:
        self.append_point({
            "point_id": "P900", "公司": "海外厂商", "cell_id": "MOD1", "状态": "生产中",
            "上市标签": "美股", "命中引语": "海外语料", "锚点URL": "无",
            "检索日期": "2026-07-25", "判定等级": "edge_backed", "判定会话日期": "2026-07-25",
        })
        self.append_point({
            "point_id": "P901", "公司": "未解析厂商", "cell_id": "MOD1", "状态": "生产中",
            "上市标签": "未解析", "命中引语": "未知国别", "锚点URL": "无",
            "检索日期": "2026-07-25", "判定等级": "edge_backed", "判定会话日期": "2026-07-25",
        })
        projection = self.projection()
        point_ids = {m["point_id"] for m in projection["requirement_matches"] if m["requirement_id"] == "CRQ001"}
        self.assertNotIn("P900", point_ids)
        self.assertNotIn("P901", point_ids)

    def test_universe_outside_observation_does_not_enter_positioning(self) -> None:
        self.append_point({
            "point_id": "P902", "公司": "观察中厂商", "cell_id": "MOD1", "状态": "宇宙外观察",
            "上市标签": "A股", "命中引语": "观察名单", "锚点URL": "无",
            "检索日期": "2026-07-25", "判定等级": "edge_backed", "判定会话日期": "2026-07-25",
        })
        projection = self.projection()
        point_ids = {m["point_id"] for m in projection["requirement_matches"] if m["requirement_id"] == "CRQ001"}
        self.assertNotIn("P902", point_ids)

    # ---- 7/8. metric comparison ----

    def test_qualitative_requirement_produces_no_metric_comparison(self) -> None:
        projection = self.projection()
        self.assertTrue(projection["requirement_matches"])
        self.assertEqual(projection["metric_comparisons"], [])

    def _add_numeric_requirement_and_metric(
        self,
        requirement_name: str = "月产能",
        point_name: str = "月产能",
        requirement_unit: str = "只",
        point_unit: str = "只",
        requirement_target: str = "50000",
    ) -> None:
        self._add_fixture_point()
        self.append_requirement({
            "requirement_id": "CRQ900", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": requirement_name, "comparator": ">=", "target_value": requirement_target,
            "unit": requirement_unit, "evidence_claim_ids": "CL006",
            "review_status": "reviewed", "notes": "测试用",
        })
        self.append_point_metric({
            "metric_id": "PM910", "point_id": "P910", "metric_name": point_name,
            "value": "60000", "unit": point_unit, "as_of": "2026-07-25",
            "review_status": "reviewed", "notes": "测试用",
        })

    def test_unit_mismatch_produces_skipped_reason(self) -> None:
        self._add_numeric_requirement_and_metric(requirement_unit="只", point_unit="只/月")
        projection = self.projection()
        entry = next(
            c for c in projection["metric_comparisons"]
            if c["requirement_id"] == "CRQ900" and c["point_id"] == "P910"
        )
        self.assertEqual(entry["status"], "skipped")
        self.assertEqual(entry["skipped_reason"], "unit_mismatch")

    def test_metric_name_mismatch_produces_skipped_reason(self) -> None:
        self._add_numeric_requirement_and_metric(requirement_name="月产能", point_name="周产能")
        projection = self.projection()
        entry = next(
            c for c in projection["metric_comparisons"]
            if c["requirement_id"] == "CRQ900" and c["point_id"] == "P910"
        )
        self.assertEqual(entry["status"], "skipped")
        self.assertEqual(entry["skipped_reason"], "metric_name_mismatch")

    def test_matching_metric_produces_comparison(self) -> None:
        self._add_numeric_requirement_and_metric()
        projection = self.projection()
        compared = [c for c in projection["metric_comparisons"] if c["requirement_id"] == "CRQ900" and c["status"] == "compared"]
        self.assertEqual(len(compared), 1)
        self.assertEqual(compared[0]["point_id"], "P910")
        self.assertIs(compared[0]["passes"], True)

    def test_false_passes_renders_explicitly_in_block(self) -> None:
        self._add_numeric_requirement_and_metric(requirement_target="70000")
        projection = self.projection()
        compared = [c for c in projection["metric_comparisons"] if c["requirement_id"] == "CRQ900" and c["status"] == "compared"]
        self.assertEqual(len(compared), 1)
        self.assertIs(compared[0]["passes"], False)
        block = render_positioning_block(projection, "T002")
        self.assertIn("通过=False", block)

    def test_skipped_metrics_kept_in_json_but_hidden_from_page(self) -> None:
        self._add_numeric_requirement_and_metric(requirement_unit="只", point_unit="只/月")
        projection = self.projection()
        skipped = [c for c in projection["metric_comparisons"] if c["requirement_id"] == "CRQ900" and c["status"] == "skipped"]
        self.assertTrue(skipped)
        block = render_positioning_block(projection, "T002")
        self.assertNotIn("数值对比", block)
        self.assertNotIn("60000", block)

    def test_numeric_requirement_without_point_metric_is_skipped(self) -> None:
        self.append_requirement({
            "requirement_id": "CRQ901", "theme_id": "T002", "cell_id": "MOD1",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "月产能", "comparator": ">=", "target_value": "50000",
            "unit": "只", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "测试用",
        })
        projection = self.projection()
        skipped = [c for c in projection["metric_comparisons"] if c["requirement_id"] == "CRQ901"]
        self.assertTrue(skipped)
        self.assertEqual({c["skipped_reason"] for c in skipped}, {"missing_point_metric"})

    # ---- 9. no point -> evidence coverage gap ----

    def test_no_point_produces_only_coverage_gap(self) -> None:
        self.append_requirement({
            "requirement_id": "CRQ902", "theme_id": "T002", "cell_id": "EQ8",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "设备产能", "comparator": "", "target_value": "",
            "unit": "", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "测试用",
        })
        projection = self.projection()
        gap = [g for g in projection["evidence_coverage_gaps"] if g["requirement_id"] == "CRQ902"]
        self.assertEqual(len(gap), 1)
        self.assertIn("未覆盖", gap[0]["message"])
        self.assertNotIn("国内没有能力", gap[0]["message"])
        self.assertNotIn("产业能力缺失", gap[0]["message"])
        self.assertFalse([m for m in projection["requirement_matches"] if m["requirement_id"] == "CRQ902"])

    # ---- 10. structural views always unsupported ----

    def test_structural_views_are_empty_with_fixed_reason(self) -> None:
        projection = self.projection()
        self.assertEqual(projection["structural_alternatives"], [])
        self.assertEqual(projection["co_required"], [])
        self.assertTrue(projection["structural_alternatives_unsupported_reason"])
        self.assertTrue(projection["co_required_unsupported_reason"])

    # ---- 11. capability overlap is a company set, not pairs ----

    def test_capability_overlap_is_company_set_not_pairs(self) -> None:
        projection = self.projection()
        overlaps = [o for o in projection["capability_overlaps"] if o["requirement_id"] == "CRQ001"]
        self.assertEqual(len(overlaps), 1)
        overlap = overlaps[0]
        self.assertGreaterEqual(len(overlap["companies"]), 2)
        self.assertEqual(len(overlap["companies"]), len(set(overlap["companies"])))
        self.assertEqual(overlap["basis"], "cell_only")
        self.assertEqual(overlap["comparability"], "unverified")
        self.assertEqual(overlap["point_ids"], sorted(overlap["point_ids"]))

    def test_single_company_does_not_produce_overlap(self) -> None:
        self.append_requirement({
            "requirement_id": "CRQ903", "theme_id": "T002", "cell_id": "M2b",
            "route_item_id": "", "dimension": "yield_capacity",
            "metric_name": "外延能力", "comparator": "", "target_value": "",
            "unit": "", "evidence_claim_ids": "CL006", "review_status": "reviewed", "notes": "测试用",
        })
        projection = self.projection()
        self.assertFalse([o for o in projection["capability_overlaps"] if o["requirement_id"] == "CRQ903"])

    # ---- 12. dual dates into projection and page ----

    def test_dual_dates_flow_into_projection_and_page(self) -> None:
        projection = self.projection()
        match = next(m for m in projection["requirement_matches"] if m["point_id"] == "P074")
        self.assertEqual(match["requirement_as_of"], "2026-08-04")
        self.assertEqual(match["point_as_of"], "2026-07-25")
        block = render_positioning_block(projection, "T002")
        self.assertIn("requirement as of 2026-08-04", block)
        self.assertIn("point as of 2026-07-25", block)
        self.assertIn("cell_only", block)

    # ---- 13. deterministic derivation ----

    def test_derive_is_deterministic(self) -> None:
        first = json.dumps(self.projection(), ensure_ascii=False, sort_keys=True)
        second = json.dumps(self.projection(), ensure_ascii=False, sort_keys=True)
        self.assertEqual(first, second)

    def test_rendered_positioning_json_is_deterministic(self) -> None:
        render(self.root)
        path = self.root / "calls" / "out" / "positioning.json"
        first = path.read_bytes()
        render(self.root)
        self.assertEqual(first, path.read_bytes())

    # ---- 14. WorkBuddy optional positioning block ----

    def test_workbuddy_skip_without_positioning_file(self) -> None:
        render(self.root)
        section = render_intelligence_section(self.root / "calls" / "out" / "panorama-intelligence.csv")
        self.assertNotIn("国内能力定位", section)

    def test_workbuddy_shows_block_with_positioning_file(self) -> None:
        render(self.root)
        positioning = self.root / "calls" / "out" / "positioning.json"
        section = render_intelligence_section(
            self.root / "calls" / "out" / "panorama-intelligence.csv",
            positioning_path=positioning,
        )
        self.assertIn("国内能力定位", section)
        self.assertIn("T002", section)
        self.assertIn("同节点能力证据", section)
        self.assertIn("requirement as of", section)
        self.assertIn("结构视图 structural_alternative", section)

    def test_every_theme_card_gets_a_positioning_tail_block(self) -> None:
        render(self.root)
        positioning = self.root / "calls" / "out" / "positioning.json"
        section = render_intelligence_section(
            self.root / "calls" / "out" / "panorama-intelligence.csv",
            positioning_path=positioning,
        )
        theme_ids = {row["theme_id"] for row in self.read_csv("themes.csv")}
        for theme_id in sorted(theme_ids):
            card_marker = f"{theme_id}\u3000"
            start = section.index(card_marker)
            self.assertIn("国内能力定位", section[start:start + 4000])

    def test_no_requirement_theme_shows_explicit_note_not_gap(self) -> None:
        render(self.root)
        positioning = self.root / "calls" / "out" / "positioning.json"
        section = render_intelligence_section(
            self.root / "calls" / "out" / "panorama-intelligence.csv",
            positioning_path=positioning,
        )
        card = section[section.index("T009\u3000"):section.index("T010\u3000")]
        self.assertIn("本主题尚无 reviewed constraint requirement", card)
        self.assertNotIn("证据覆盖缺口", card)
        self.assertIn("结构视图 structural_alternative", card)
        self.assertIn("结构视图 co_required", card)

    def test_block_rows_show_requirement_id_and_source_claims(self) -> None:
        projection = self.projection()
        block = render_positioning_block(projection, "T002")
        self.assertIn("requirement=CRQ001", block)
        self.assertIn("证据 CL006", block)
        block_c1 = render_positioning_block(projection, "T007")
        self.assertIn("requirement=CRQ002", block_c1)
        self.assertIn("证据 CL015;CL027;CL028", block_c1)

    def test_workbuddy_missing_everything_is_safe(self) -> None:
        self.assertEqual(render_intelligence_section(self.root / "missing.csv"), "")
        self.assertEqual(render_intelligence_section(self.root / "missing.csv", positioning_path=self.root / "missing.json"), "")

    # ---- 15. forbidden business words ----

    def test_derived_fields_and_block_have_no_forbidden_words(self) -> None:
        projection = self.projection()
        json_text = json.dumps(projection, ensure_ascii=False, sort_keys=True)
        self.assertEqual(scan_forbidden_words(json_text), [])
        theme_ids = [row["theme_id"] for row in self.read_csv("themes.csv")]
        self.assertEqual(scan_forbidden_words(render_all_positioning_blocks(projection, theme_ids)), [])

    def test_forbidden_word_scanner_catches_violations(self) -> None:
        self.assertIn("供货", scan_forbidden_words("本厂商负责供货"))
        self.assertIn("competition", scan_forbidden_words("fierce competition"))
        self.assertIn("解决卡点", scan_forbidden_words("该方案解决卡点"))

    # ---- 16/17. canonical integrity, output count and legacy report ----

    def test_rendered_output_count_tracks_enabled_company_pool(self) -> None:
        paths = render(self.root)
        with (self.root / "calls" / "universe.csv").open(encoding="utf-8-sig", newline="") as handle:
            company_count = sum(1 for _ in csv.DictReader(handle))
        self.assertEqual(len(paths), company_count + 8)
        self.assertIn(self.root / "calls" / "out" / "positioning.json", paths)

    def test_legacy_solution_link_report_still_exists(self) -> None:
        render(self.root)
        chains = (self.root / "calls" / "out" / "limited-demand-chains.md").read_text(encoding="utf-8")
        self.assertIn("canonical `P074`", chains)
        self.assertIn("canonical `P095`", chains)
        links = self.read_csv("solution_links.csv")
        self.assertEqual(len(links), 2)
        self.assertEqual({row["link_id"] for row in links}, {"SL001", "SL002"})


if __name__ == "__main__":
    unittest.main()
