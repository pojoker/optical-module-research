#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-tests for the industry-chain v2 validator and gap generator.

Run with:  python test_validate_model.py

The suite contains at least one positive case and the six required negative
classes (illegal relation, orphan reference, duplicate ID, layer mixing,
bottleneck without basis, illegal state transition) plus a gap-denominator
case. No real optical-module company names are hard-coded; only synthetic
placeholders (e.g. "示例制造商甲") are used.

Exit code is non-zero if any test fails.
"""

import os
import sys
import unittest
from datetime import date

# Make sibling modules importable regardless of the invocation directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_model import validate_dataset, EXPECTED_HEADERS  # noqa: E402
from generate_gaps import build_gaps  # noqa: E402

REFERENCE_DATE = date(2024, 1, 2)


def _tbl(name, rows):
    """Build a (fieldnames, rows) tuple for a canonical table."""
    return (list(EXPECTED_HEADERS[name]), rows)


def _ev(eid, use):
    return {
        "evidence_id": eid, "evidence_use": use, "source_tier": "T1",
        "title": "t", "publisher": "p", "url": "https://example.com/%s" % eid,
        "publication_date": "2024-01-01", "retrieved_at": "2024-01-02",
        "as_of": "2024-01-01", "quote": "q", "stance": "standard",
        "verdict": "supports", "notes": "",
    }


def base_dataset():
    """A fully valid, minimal canonical dataset (no gaps table)."""
    ev = [_ev("EV-1", "structure"), _ev("EV-2", "capability"), _ev("EV-3", "trade")]
    nodes = [
        {"node_id": "SN-APP", "node_type": "application", "name_zh": "应用",
         "name_en": "app", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-R1", "node_type": "product_route", "name_zh": "路线一",
         "name_en": "route1", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-F1", "node_type": "function", "name_zh": "功能一",
         "name_en": "func1", "definition": "d", "status": "admitted",
         "importance_class": "supporting", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-C1", "node_type": "component", "name_zh": "部件一",
         "name_en": "comp1", "definition": "d", "status": "verified",
         "importance_class": "structural_critical", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-M1", "node_type": "material", "name_zh": "材料一",
         "name_en": "mat1", "definition": "d", "status": "admitted",
         "importance_class": "supporting", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-P1", "node_type": "process", "name_zh": "工序一",
         "name_en": "proc1", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-P2", "node_type": "process", "name_zh": "工序二",
         "name_en": "proc2", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-E1", "node_type": "equipment_category", "name_zh": "设备类一",
         "name_en": "eq1", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-C2", "node_type": "component", "name_zh": "部件二",
         "name_en": "comp2", "definition": "d", "status": "admitted",
         "importance_class": "supporting", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
    ]
    edges = [
        {"edge_id": "SE-1", "source_node_id": "SN-APP", "target_node_id": "SN-R1",
         "relation_type": "drives", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-2", "source_node_id": "SN-R1", "target_node_id": "SN-F1",
         "relation_type": "implements", "route_scope": "SN-R1", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-3", "source_node_id": "SN-R1", "target_node_id": "SN-C1",
         "relation_type": "requires", "route_scope": "SN-R1", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-4", "source_node_id": "SN-F1", "target_node_id": "SN-M1",
         "relation_type": "requires", "route_scope": "SN-R1", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-5", "source_node_id": "SN-R1", "target_node_id": "SN-P1",
         "relation_type": "uses_process", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-6", "source_node_id": "SN-P1", "target_node_id": "SN-M1",
         "relation_type": "uses_material", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-7", "source_node_id": "SN-P1", "target_node_id": "SN-E1",
         "relation_type": "enabled_by", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-8", "source_node_id": "SN-P1", "target_node_id": "SN-P2",
         "relation_type": "precedes", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-9", "source_node_id": "SN-C1", "target_node_id": "SN-F1",
         "relation_type": "part_of", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-10", "source_node_id": "SN-C1", "target_node_id": "SN-C2",
         "relation_type": "alternative_to", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
    ]
    orgs = [
        {"org_id": "ORG-1", "canonical_name": "示例制造商甲", "org_type": "company",
         "country": "CN", "identifiers": "", "aliases": "", "status": "active", "notes": ""},
        {"org_id": "ORG-2", "canonical_name": "示例客户乙", "org_type": "company",
         "country": "CN", "identifiers": "", "aliases": "", "status": "active", "notes": ""},
    ]
    caps = [
        {"capability_id": "CAP-1", "org_id": "ORG-1", "node_id": "SN-C1",
         "capability_status": "production", "route_scope": "SN-R1",
         "evidence_ids": "EV-2", "as_of": "2024-01-01", "review_status": "admitted", "notes": ""},
    ]
    trades = [
        {"observation_id": "TR-1", "supplier_org_id": "ORG-1", "customer_org_id": "ORG-2",
         "anonymous_endpoint": "", "product_or_node_id": "SN-C1", "period": "2024",
         "amount_or_share": "", "evidence_ids": "EV-3", "grade": "real",
         "review_status": "admitted", "notes": ""},
    ]
    return {
        "evidence": _tbl("evidence", ev),
        "structure_nodes": _tbl("structure_nodes", nodes),
        "structure_edges": _tbl("structure_edges", edges),
        "organizations": _tbl("organizations", orgs),
        "capabilities": _tbl("capabilities", caps),
        "trade_observations": _tbl("trade_observations", trades),
    }


def gap_rich_dataset():
    """A dataset engineered to trigger every one of the six gap types."""
    ev = [_ev("EV-1", "structure"), _ev("EV-2", "capability"), _ev("EV-3", "trade")]
    nodes = [
        {"node_id": "SN-APP", "node_type": "application", "name_zh": "应用",
         "name_en": "app", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-R1", "node_type": "product_route", "name_zh": "路线一",
         "name_en": "route1", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-R2", "node_type": "product_route", "name_zh": "路线二",
         "name_en": "route2", "definition": "d", "status": "admitted",
         "importance_class": "enabling", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "", "notes": ""},
        {"node_id": "SN-F1", "node_type": "function", "name_zh": "功能一",
         "name_en": "func1", "definition": "d", "status": "admitted",
         "importance_class": "supporting", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-C1", "node_type": "component", "name_zh": "部件一",
         "name_en": "comp1", "definition": "d", "status": "verified",
         "importance_class": "structural_critical", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
        {"node_id": "SN-C2", "node_type": "component", "name_zh": "部件二",
         "name_en": "comp2", "definition": "d", "status": "admitted",
         "importance_class": "supporting", "importance_confidence": "verified",
         "importance_basis": "b", "evidence_ids": "EV-1", "as_of": "2024-01-01", "notes": ""},
    ]
    edges = [
        {"edge_id": "SE-1", "source_node_id": "SN-APP", "target_node_id": "SN-R1",
         "relation_type": "drives", "route_scope": "SN-R1", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-2", "source_node_id": "SN-APP", "target_node_id": "SN-R2",
         "relation_type": "drives", "route_scope": "SN-R2", "requiredness": "unknown",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-3", "source_node_id": "SN-R1", "target_node_id": "SN-F1",
         "relation_type": "implements", "route_scope": "SN-R1", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-4", "source_node_id": "SN-R2", "target_node_id": "SN-F1",
         "relation_type": "implements", "route_scope": "SN-R2", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
        {"edge_id": "SE-5", "source_node_id": "SN-R1", "target_node_id": "SN-C1",
         "relation_type": "requires", "route_scope": "SN-R1", "requiredness": "mandatory",
         "evidence_ids": "EV-1", "notes": ""},
    ]
    orgs = [
        {"org_id": "ORG-1", "canonical_name": "示例制造商甲", "org_type": "company",
         "country": "CN", "identifiers": "", "aliases": "", "status": "active", "notes": ""},
        {"org_id": "ORG-2", "canonical_name": "示例客户乙", "org_type": "company",
         "country": "CN", "identifiers": "", "aliases": "", "status": "active", "notes": ""},
    ]
    caps = [
        {"capability_id": "CAP-1", "org_id": "ORG-1", "node_id": "SN-C2",
         "capability_status": "production", "route_scope": "SN-R1",
         "evidence_ids": "EV-2", "as_of": "2024-01-01", "review_status": "admitted", "notes": ""},
    ]
    trades = []  # intentionally empty -> trade_gap
    return {
        "evidence": _tbl("evidence", ev),
        "structure_nodes": _tbl("structure_nodes", nodes),
        "structure_edges": _tbl("structure_edges", edges),
        "organizations": _tbl("organizations", orgs),
        "capabilities": _tbl("capabilities", caps),
        "trade_observations": _tbl("trade_observations", trades),
    }


def codes(errors):
    return {e["code"] for e in errors}


class ValidatorPositiveTest(unittest.TestCase):
    def test_valid_dataset_passes(self):
        ds = base_dataset()
        errors, warnings = validate_dataset(ds)
        self.assertEqual(errors, [], msg="expected no errors, got: %s" % errors)

    def test_structural_critical_reachable_across_layers(self):
        ds = base_dataset()
        by_id = {r["node_id"]: r for r in ds["structure_nodes"][1]}
        for nid in ("SN-APP", "SN-R1", "SN-F1", "SN-P1", "SN-P2", "SN-E1"):
            by_id[nid]["importance_class"] = "structural_critical"
        for edge in ds["structure_edges"][1]:
            if edge["edge_id"] in ("SE-5", "SE-7", "SE-8"):
                edge["requiredness"] = "mandatory"
        errors, _ = validate_dataset(ds)
        self.assertNotIn("IMP_SC_NOT_MANDATORY", codes(errors))


class ValidatorNegativeTest(unittest.TestCase):
    def test_illegal_relation(self):
        ds = base_dataset()
        # drives requires application->product_route; here source is a route
        ds["structure_edges"][1][2]["relation_type"] = "drives"
        errors, _ = validate_dataset(ds)
        self.assertIn("REL_ILLEGAL", codes(errors))

    def test_orphan_reference(self):
        ds = base_dataset()
        ds["structure_edges"][1][0]["target_node_id"] = "SN-GHOST"
        errors, _ = validate_dataset(ds)
        self.assertIn("REF_ORPHAN", codes(errors))

    def test_duplicate_id(self):
        ds = base_dataset()
        dup = dict(ds["structure_nodes"][1][0])  # copy SN-APP
        ds["structure_nodes"][1].append(dup)
        errors, _ = validate_dataset(ds)
        self.assertIn("ID_DUP", codes(errors))

    def test_layer_mixing(self):
        ds = base_dataset()
        bad = {"edge_id": "SE-99", "source_node_id": "SN-F1",
               "target_node_id": "SN-C1", "relation_type": "part_of",
               "route_scope": "SN-R1", "requiredness": "unknown",
               "evidence_ids": "EV-1", "notes": ""}
        ds["structure_edges"][1].append(bad)
        errors, _ = validate_dataset(ds)
        self.assertIn("LAYER_MIX", codes(errors))

    def test_bottleneck_without_basis(self):
        ds = base_dataset()
        c1 = ds["structure_nodes"][1][3]  # SN-C1
        c1["importance_class"] = "bottleneck_candidate"
        c1["importance_confidence"] = "unknown"
        errors, _ = validate_dataset(ds)
        self.assertIn("IMP_NO_BASIS", codes(errors))

    def test_illegal_state_transition(self):
        ds = base_dataset()
        c1 = ds["structure_nodes"][1][3]  # SN-C1, status=verified
        c1["evidence_ids"] = ""  # verified but no structure evidence
        errors, _ = validate_dataset(ds)
        self.assertIn("STATE_VERIFIED_NO_EVID", codes(errors))

    def test_gap_denominator_vanished(self):
        ds = base_dataset()
        gap_row = {
            "gap_id": "GAP-1", "node_id": "SN-R1", "route_scope": "SN-FAKE",
            "gap_type": "capability_gap", "priority": "P1", "status": "identified",
            "reason": "r", "next_question": "q", "completion_condition": "c",
            "owner": "WP-HY3", "evidence_ids": "", "updated_at": "2024-01-01", "notes": "",
        }
        ds["gaps"] = _tbl("gaps", [gap_row])
        errors, _ = validate_dataset(ds)
        self.assertIn("GAP_BAD_ROUTE", codes(errors))

    def test_unreachable_structural_critical_rejected(self):
        ds = base_dataset()
        c2 = next(r for r in ds["structure_nodes"][1] if r["node_id"] == "SN-C2")
        c2["importance_class"] = "structural_critical"
        errors, _ = validate_dataset(ds)
        self.assertIn("IMP_SC_NOT_MANDATORY", codes(errors))


class GapGeneratorTest(unittest.TestCase):
    def test_all_six_gap_types_generated(self):
        ds = gap_rich_dataset()
        c2 = next(r for r in ds["structure_nodes"][1] if r["node_id"] == "SN-C2")
        c2["importance_class"] = "bottleneck_candidate"
        c2["importance_confidence"] = "hypothesis"
        c2["importance_basis"] = "explicit bottleneck hypothesis"
        c1 = next(r for r in ds["structure_nodes"][1] if r["node_id"] == "SN-C1")
        c1["status"] = "admitted"
        c1["importance_confidence"] = "hypothesis"
        c1["evidence_ids"] = ""
        cap = ds["capabilities"][1][0]
        cap["evidence_ids"] = ""
        cap["review_status"] = "proposed"
        ds["structure_edges"][1].append({
            "edge_id": "SE-6", "source_node_id": "SN-F1",
            "target_node_id": "SN-C1", "relation_type": "requires",
            "route_scope": "all", "requiredness": "mandatory",
            "evidence_ids": "EV-1", "notes": "explicit common declaration",
        })
        gaps = build_gaps(ds, REFERENCE_DATE)
        types = {g["gap_type"] for g in gaps}
        for expected in ("structure_gap", "player_gap", "capability_gap",
                         "trade_gap", "currentness_gap", "comparability_gap"):
            self.assertIn(expected, types,
                          msg="missing gap type %s; got %s" % (expected, types))

    def test_comparability_denominator_guard(self):
        # single-route dataset -> comparability denominator insufficient
        ds = base_dataset()
        gaps = build_gaps(ds, REFERENCE_DATE)
        comp = [g for g in gaps if g["gap_type"] == "comparability_gap"]
        self.assertTrue(comp, "expected a comparability_gap for a single route")

    def test_generated_gaps_validate_clean(self):
        ds = gap_rich_dataset()
        gaps = build_gaps(ds, REFERENCE_DATE)
        ds["gaps"] = _tbl("gaps", gaps)
        errors, _ = validate_dataset(ds)
        self.assertEqual(errors, [],
                         msg="generated gaps must validate: %s" % errors)

    def test_reference_date_is_required(self):
        with self.assertRaises(ValueError):
            build_gaps(base_dataset())

    def test_player_and_capability_gaps_are_disjoint(self):
        ds = gap_rich_dataset()
        gaps = build_gaps(ds, REFERENCE_DATE)
        c1 = [g["gap_type"] for g in gaps if g["node_id"] == "SN-C1"]
        self.assertIn("player_gap", c1)
        self.assertNotIn("capability_gap", c1)

        cap = ds["capabilities"][1][0]
        cap["node_id"] = "SN-C1"
        cap["capability_status"] = "unknown"
        cap["evidence_ids"] = ""
        cap["review_status"] = "proposed"
        gaps = build_gaps(ds, REFERENCE_DATE)
        c1 = [g["gap_type"] for g in gaps if g["node_id"] == "SN-C1"]
        self.assertIn("capability_gap", c1)
        self.assertNotIn("player_gap", c1)

    def test_route_specific_difference_is_not_comparability_gap(self):
        ds = gap_rich_dataset()
        gaps = build_gaps(ds, REFERENCE_DATE)
        comp = [g for g in gaps
                if g["gap_type"] == "comparability_gap"
                and "SN-C1" in g["reason"]]
        self.assertEqual(comp, [])

    def test_explicit_common_asymmetry_is_comparability_gap(self):
        ds = gap_rich_dataset()
        ds["structure_edges"][1].append({
            "edge_id": "SE-6", "source_node_id": "SN-F1",
            "target_node_id": "SN-C1", "relation_type": "requires",
            "route_scope": "all", "requiredness": "mandatory",
            "evidence_ids": "EV-1", "notes": "explicit common declaration",
        })
        gaps = build_gaps(ds, REFERENCE_DATE)
        comp = [g for g in gaps
                if g["gap_type"] == "comparability_gap"
                and "SN-C1" in g["reason"]]
        self.assertTrue(comp)

    def test_no_company_names_hardcoded(self):
        # Guard: the deliverable files must not contain real optical-module
        # brand names. The test file itself is allowed to list them as a
        # blacklist, so we scan only the three deliverables.
        here = os.path.dirname(os.path.abspath(__file__))
        targets = ["validate_model.py", "generate_gaps.py", "README.md"]
        forbidden = ["中际旭创", "Coherent", "Fabrinet", "Lumentum", "新易盛",
                     "光迅", "华工", "II-VI", "Innolight", "旭创"]
        for fname in targets:
            with open(os.path.join(here, fname), encoding="utf-8") as fh:
                src = fh.read()
            for name in forbidden:
                self.assertNotIn(name, src,
                                 msg="%s contains hard-coded %s" % (fname, name))


if __name__ == "__main__":
    unittest.main(verbosity=2)
