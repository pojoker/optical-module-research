#!/Users/jowang/miniconda3/bin/python3
"""Mechanical verifier for draft-only Best-of-N candidate YAML files."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


DELTA_KEYS = {
    "delta_id", "comparison_id", "basis_fields", "left_observation",
    "right_observation", "delta_status", "existing_physical_cells",
    "candidate_facets", "unmodeled_dimension", "component_delta",
    "interface_delta", "process_delta", "equipment_delta", "test_delta",
    "evidence_refs",
}
REQ_KEYS = {
    "requirement_id", "comparison_id", "basis_type", "basis_fields",
    "target_physical_cell", "candidate_facet", "capability_action",
    "requirement_statement", "acceptance_metric_state",
    "existing_points_matchable", "match_basis", "evidence_refs",
}
COMPARISONS = {"CMP-D02-D03", "CMP-D04-D05"}
DELTA_STATUSES = {
    "observed_difference", "normalized_difference", "engineering_inference", "unknown"
}
BASIS_TYPES = {"axis_direct", "delta_direct", "engineering_inference", "unknown"}
ACTIONS = {"design", "manufacture", "integrate", "test"}
METRIC_STATES = {"observed", "defined_but_value_missing", "unknown"}
MATCH_STATES = {"yes", "partial", "no"}
UNMODELED = {None, "form_factor", "electrical_responsibility", "photonic_device_detail", "other"}


def collect_cell_ids(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("cell_id"), str):
            found.add(value["cell_id"])
        for child in value.values():
            found |= collect_cell_ids(child)
    elif isinstance(value, list):
        for child in value:
            found |= collect_cell_ids(child)
    return found


def fail(errors: list[str], where: str, message: str) -> None:
    errors.append(f"{where}: {message}")


def verify(path: Path, fields: set[str], cells: set[str]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {"file": path.name, "valid": False, "errors": [f"YAML parse: {exc}"], "warnings": []}

    if not isinstance(data, dict):
        return {"file": path.name, "valid": False, "errors": ["top level is not a mapping"], "warnings": []}

    meta = data.get("meta", {})
    expected_id = path.stem.removeprefix("candidate-").upper()
    if meta.get("generator_id") != expected_id:
        fail(errors, "meta.generator_id", f"expected {expected_id!r}, got {meta.get('generator_id')!r}")
    if meta.get("mode") != "draft_only":
        fail(errors, "meta.mode", "must be draft_only")
    if meta.get("canonical_write_performed") is not False:
        fail(errors, "meta.canonical_write_performed", "must be boolean false")

    deltas = data.get("physical_delta_candidates")
    if not isinstance(deltas, list):
        fail(errors, "physical_delta_candidates", "must be a list")
        deltas = []
    for index, item in enumerate(deltas):
        where = f"physical_delta_candidates[{index}]"
        if not isinstance(item, dict):
            fail(errors, where, "must be a mapping")
            continue
        missing = DELTA_KEYS - set(item)
        extra = set(item) - DELTA_KEYS
        if missing:
            fail(errors, where, f"missing keys {sorted(missing)}")
        if extra:
            fail(errors, where, f"extra keys {sorted(extra)}")
        if item.get("comparison_id") not in COMPARISONS:
            fail(errors, where, "invalid comparison_id")
        if item.get("delta_status") not in DELTA_STATUSES:
            fail(errors, where, "invalid delta_status")
        basis = item.get("basis_fields", [])
        if not isinstance(basis, list) or any(field not in fields for field in basis):
            fail(errors, where, f"unknown basis field(s): {basis!r}")
        mapped = item.get("existing_physical_cells", [])
        if not isinstance(mapped, list) or any(cell not in cells for cell in mapped):
            fail(errors, where, f"unknown physical cell(s): {mapped!r}")
        if item.get("unmodeled_dimension") not in UNMODELED:
            fail(errors, where, "invalid unmodeled_dimension")
        for field in ("process_delta", "equipment_delta", "test_delta"):
            if item.get(field) != "UNKNOWN":
                fail(errors, f"{where}.{field}", "must remain literal UNKNOWN")
        if item.get("comparison_id") == "CMP-D02-D03" and item.get("delta_status") in {"observed_difference", "normalized_difference"}:
            fail(errors, where, "D02/D03 has no equal-grain observed/normalized difference; raw labels are not_comparable")
        if item.get("unmodeled_dimension") == "form_factor" and mapped:
            fail(errors, where, "form_factor must remain UNMODELED and cannot map to an existing physical cell")

    cards = data.get("tradeoff_cards")
    if not isinstance(cards, list) or len(cards) != 2:
        fail(errors, "tradeoff_cards", "must contain exactly two cards")
        cards = cards if isinstance(cards, list) else []
    seen_cards: set[str] = set()
    for index, card in enumerate(cards):
        where = f"tradeoff_cards[{index}]"
        if not isinstance(card, dict):
            fail(errors, where, "must be a mapping")
            continue
        comparison_id = card.get("comparison_id")
        seen_cards.add(comparison_id)
        if comparison_id not in COMPARISONS:
            fail(errors, where, "invalid comparison_id")
        if card.get("comparison_status") not in {"partially_comparable", "not_comparable"}:
            fail(errors, where, "comparison_status must be partially_comparable or not_comparable")
        for field in ("advantages", "costs_and_disadvantages", "new_bottlenecks", "alternatives"):
            if card.get(field) != []:
                fail(errors, f"{where}.{field}", "must be an empty list")
        if card.get("no_unconditional_ranking") is not True:
            fail(errors, f"{where}.no_unconditional_ranking", "must be boolean true")
    if seen_cards != COMPARISONS:
        fail(errors, "tradeoff_cards", f"must cover {sorted(COMPARISONS)} exactly")

    reqs = data.get("capability_requirement_candidates")
    if not isinstance(reqs, list):
        fail(errors, "capability_requirement_candidates", "must be a list")
        reqs = []
    for index, item in enumerate(reqs):
        where = f"capability_requirement_candidates[{index}]"
        if not isinstance(item, dict):
            fail(errors, where, "must be a mapping")
            continue
        missing = REQ_KEYS - set(item)
        extra = set(item) - REQ_KEYS
        if missing:
            fail(errors, where, f"missing keys {sorted(missing)}")
        if extra:
            fail(errors, where, f"extra keys {sorted(extra)}")
        if item.get("comparison_id") not in COMPARISONS:
            fail(errors, where, "invalid comparison_id")
        if item.get("basis_type") not in BASIS_TYPES:
            fail(errors, where, "invalid basis_type")
        basis = item.get("basis_fields", [])
        if not isinstance(basis, list) or any(field not in fields for field in basis):
            fail(errors, where, f"unknown basis field(s): {basis!r}")
        target = item.get("target_physical_cell")
        if target != "UNMODELED" and target not in cells:
            fail(errors, where, f"unknown target physical cell {target!r}")
        if item.get("capability_action") not in ACTIONS:
            fail(errors, where, "invalid capability_action")
        if item.get("acceptance_metric_state") not in METRIC_STATES:
            fail(errors, where, "invalid acceptance_metric_state")
        match_state = item.get("existing_points_matchable")
        if match_state not in MATCH_STATES:
            fail(errors, where, f"existing_points_matchable must be one of {sorted(MATCH_STATES)}, not {match_state!r}")
        if item.get("basis_type") == "engineering_inference" and match_state == "yes":
            fail(errors, where, "engineering_inference cannot be directly matchable")

    text = path.read_text(encoding="utf-8")
    for forbidden in ("canonical_write_performed: true", "coverage_status_changed: true", "formal_route_profile", "company_group"):
        if forbidden in text:
            fail(errors, "document", f"forbidden marker {forbidden!r}")
    if "Coherent" in text or "相干公司" in text:
        warnings.append("company name appears; inspect whether it is merely a source label")

    return {
        "file": path.name,
        "valid": not errors,
        "counts": {
            "physical_delta_candidates": len(deltas),
            "tradeoff_cards": len(cards),
            "capability_requirement_candidates": len(reqs),
            "validation_questions": len(data.get("validation_questions", [])) if isinstance(data.get("validation_questions"), list) else 0,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("candidates", nargs="+")
    args = parser.parse_args()

    matrix = yaml.safe_load(Path(args.matrix).read_text(encoding="utf-8"))
    fields = {row["field"] for comparison in matrix["comparisons"] for row in comparison["rows"]}
    tree = yaml.safe_load(Path(args.tree).read_text(encoding="utf-8"))
    cells = collect_cell_ids(tree)
    report = {
        "meta": {
            "mode": "draft_only",
            "python_interpreter": "/Users/jowang/miniconda3/bin/python3",
            "verifier_type": "deterministic_mechanical",
            "canonical_write_performed": False,
        },
        "candidate_results": [verify(Path(path), fields, cells) for path in args.candidates],
    }
    report["summary"] = {
        "candidate_count": len(report["candidate_results"]),
        "valid_count": sum(item["valid"] for item in report["candidate_results"]),
        "candidate_valid_rate": sum(item["valid"] for item in report["candidate_results"]) / len(report["candidate_results"]),
    }
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False, width=160))


if __name__ == "__main__":
    main()
