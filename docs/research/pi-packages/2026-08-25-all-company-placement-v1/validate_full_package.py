#!/Users/jowang/miniconda3/bin/python3
"""Validate the draft-only all-company placement package."""

from __future__ import annotations

import csv
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


EXPECTED_PYTHON = "/Users/jowang/miniconda3/bin/python3"
ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
ROUTE_PACKAGE = PACKAGE.parent / "2026-08-25-tq010-tq014-delta-tradeoff-v1"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def collect_cells(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("cell_id"), str):
            result.add(value["cell_id"])
        for child in value.values():
            result |= collect_cells(child)
    elif isinstance(value, list):
        for child in value:
            result |= collect_cells(child)
    return result


def add(checks: list[dict], name: str, passed: bool, **details: object) -> None:
    checks.append({"check": name, "passed": bool(passed), **details})


def compile_registry_patterns(registry: dict) -> list[str]:
    errors: list[str] = []
    pattern_groups: list[tuple[str, object]] = []
    for cell, config in registry["cells"].items():
        for namespace, values in config.get("facets", {}).items():
            for value, patterns in values.items():
                pattern_groups.append((f"cells.{cell}.{namespace}.{value}", patterns))
    for family, roles in registry.get("role_rules", {}).items():
        for role, patterns in roles.items():
            pattern_groups.append((f"role_rules.{family}.{role}", patterns))
    for role, patterns in registry.get("role_negative_patterns", {}).items():
        pattern_groups.append((f"role_negative_patterns.{role}", patterns))
    for marker, patterns in registry.get("maturity_rules", {}).items():
        pattern_groups.append((f"maturity_rules.{marker}", patterns))
    for label, patterns in pattern_groups:
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"{label}: {pattern!r}: {exc}")
    return errors


def check_spans(proposals: list[dict], quotes: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for item in proposals:
        quote = quotes[item["point_id"]]
        groups = [
            *(facet["evidence_spans"] for facet in item["facet_assertions"]),
            *(role["evidence_spans"] for role in item["role_assertions"]),
            *(marker["evidence_spans"] for marker in item["maturity_markers"]),
        ]
        for spans in groups:
            for span in spans:
                if quote[span["start"] : span["end"]] != span["text"]:
                    errors.append(f"{item['point_id']} bad span {span}")
    return errors


def reproduce_attachments() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "attachments.yaml"
        command = [
            EXPECTED_PYTHON,
            str(PACKAGE / "build_all_company_attachments.py"),
            "--points", str(ROOT / "points.csv"),
            "--tree", str(ROOT / "tree.yaml"),
            "--registry", str(PACKAGE / "full-facet-registry-draft.yaml"),
            "--route-pilot", str(ROUTE_PACKAGE / "company-capability-match-pilot.yaml"),
        ]
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode:
            return False, result.stderr
        output.write_text(result.stdout, encoding="utf-8")
        return load(output) == load(PACKAGE / "all-company-attachments-draft.yaml"), ""


def reproduce_graph() -> tuple[bool, str]:
    command = [
        EXPECTED_PYTHON,
        str(PACKAGE / "build_full_placeable_graph.py"),
        "--tree", str(ROOT / "tree.yaml"),
        "--attachments", str(PACKAGE / "all-company-attachments-draft.yaml"),
        "--registry", str(PACKAGE / "full-facet-registry-draft.yaml"),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        return False, result.stderr
    return yaml.safe_load(result.stdout) == load(PACKAGE / "full-company-placeable-graph-draft.yaml"), ""


def main() -> None:
    checks: list[dict] = []
    add(checks, "miniconda_interpreter", sys.executable == EXPECTED_PYTHON, observed=sys.executable)

    yaml_errors: list[str] = []
    yaml_files = sorted(PACKAGE.glob("*.yaml"))
    for path in yaml_files:
        try:
            load(path)
        except Exception as exc:  # validation report needs all parse failures
            yaml_errors.append(f"{path.name}: {exc}")
    add(checks, "all_package_yaml_parse", not yaml_errors, yaml_file_count=len(yaml_files), errors=yaml_errors)

    compile_errors: list[str] = []
    python_files = sorted(PACKAGE.glob("*.py"))
    for path in python_files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            compile_errors.append(f"{path.name}: {exc}")
    add(checks, "all_package_python_compile", not compile_errors, script_count=len(python_files), errors=compile_errors)

    registry = load(PACKAGE / "full-facet-registry-draft.yaml")
    regex_errors = compile_registry_patterns(registry)
    add(checks, "registry_regex_compile", not regex_errors, errors=regex_errors)

    with (ROOT / "points.csv").open(encoding="utf-8-sig", newline="") as handle:
        point_rows = list(csv.DictReader(handle))
    point_ids = {row["point_id"] for row in point_rows}
    quotes = {row["point_id"]: row["命中引语"] for row in point_rows}
    occupied_cells = {row["cell_id"] for row in point_rows}
    tree_cells = collect_cells(load(ROOT / "tree.yaml"))

    attachments = load(PACKAGE / "all-company-attachments-draft.yaml")
    proposals = attachments["point_attachment_proposals"]
    proposal_ids = [item["point_id"] for item in proposals]
    add(
        checks,
        "point_proposal_bijection",
        len(proposals) == 271 and len(set(proposal_ids)) == 271 and set(proposal_ids) == point_ids,
        point_count=len(proposals),
        unique_point_count=len(set(proposal_ids)),
    )
    add(
        checks,
        "registry_and_tree_cell_closure",
        occupied_cells == set(registry["cells"]) and occupied_cells <= tree_cells and len(tree_cells) == 41,
        occupied_cell_count=len(occupied_cells),
        registry_cell_count=len(registry["cells"]),
        tree_cell_count=len(tree_cells),
        unoccupied_tree_cells=sorted(tree_cells - occupied_cells),
    )

    span_errors = check_spans(proposals, quotes)
    add(checks, "all_assertion_spans_reproduce", not span_errors, error_count=len(span_errors), errors=span_errors[:20])

    blocked = {item["point_id"]: item for item in proposals if not item["attachment_eligible"]}
    blocked_ok = set(blocked) == {"P040", "P193"} and all(
        not item["facet_assertions"] and not item["role_assertions"] and not item["maturity_markers"]
        for item in blocked.values()
    )
    add(checks, "blocked_scope_invariants", blocked_ok, blocked_points=sorted(blocked))

    by_id = {item["point_id"]: item for item in proposals}
    reviewer_fix_invariants = {
        "P039_no_cross_quote_module_span": [
            span["text"]
            for role in by_id["P039"]["role_assertions"]
            if role["role"] == "module_integrate"
            for span in role["evidence_spans"]
        ] == ["光模块为主的光通信产品的研发、制造"],
        "P193_blocked_has_no_maturity": not by_id["P193"]["maturity_markers"],
        "P199_subsidiary_and_no_foundry_facet": by_id["P199"]["subject_scope"] == "controlled_subsidiary"
        and "manufacturing_mode.foundry_platform" not in {f["facet"] for f in by_id["P199"]["facet_assertions"]},
        "P217_incomplete_revenue_has_no_role": not by_id["P217"]["role_assertions"],
        "P244_module_role_is_object_anchored": [
            span["text"]
            for role in by_id["P244"]["role_assertions"]
            if role["role"] == "module_integrate"
            for span in role["evidence_spans"]
        ] == ["光模块全产业链生产制造"],
        "P245_no_truncated_sleeve_facet": "ferrule_type.sleeve"
        not in {f["facet"] for f in by_id["P245"]["facet_assertions"]},
        "P256_future_production_has_no_current_role": not by_id["P256"]["role_assertions"],
    }
    add(
        checks,
        "semantic_review_fix_invariants",
        all(reviewer_fix_invariants.values()),
        invariants=reviewer_fix_invariants,
    )

    maturity_ok = all(
        not item["point_status_inherited_by_facets"]
        and all(facet["facet_maturity_state"] == "not_inferred" for facet in item["facet_assertions"])
        for item in proposals
    )
    add(checks, "maturity_not_inherited", maturity_ok)

    expected_summary = {
        "point_count": 271,
        "unique_point_count": 271,
        "company_string_count": 155,
        "company_identity_key_count": 154,
        "alias_candidate_cluster_count": 1,
        "occupied_cell_count": 39,
        "registry_cell_count": 39,
        "facet_explicit_point_count": 258,
        "cell_only_point_count": 13,
        "role_explicit_point_count": 170,
        "role_unknown_or_blocked_point_count": 101,
        "attachment_blocked_point_count": 2,
        "subject_scope_blocked_point_count": 1,
        "evidence_scope_blocked_point_count": 1,
        "route_pilot_linked_point_count": 56,
        "route_service_conclusion_count": 0,
    }
    add(checks, "attachment_expected_summary", attachments["summary"] == expected_summary, observed=attachments["summary"])

    attachments_ok, attachments_error = reproduce_attachments()
    add(checks, "attachments_reproducible", attachments_ok, error=attachments_error)
    graph_ok, graph_error = reproduce_graph()
    add(checks, "graph_reproducible", graph_ok, error=graph_error)

    graph = load(PACKAGE / "full-company-placeable-graph-draft.yaml")
    expected_readiness = {
        "source_point_count": 271,
        "declared_cell_edge_count": 271,
        "eligible_company_attachment_count": 269,
        "blocked_review_queue_count": 2,
        "facet_assertion_count": 484,
        "unique_observed_facet_count": 216,
        "role_assertion_count": 272,
        "route_pilot_linked_point_count": 56,
        "route_requirement_candidate_edge_count": 6,
        "route_related_facet_edge_count": 16,
        "why_causal_edge_count": 0,
        "route_service_edge_count": 0,
        "all_source_points_have_a_graph_disposition": True,
    }
    add(checks, "graph_expected_readiness", graph["placement_readiness"] == expected_readiness, observed=graph["placement_readiness"])

    tree_doc = (PACKAGE / "full-company-placeable-tree.md").read_text(encoding="utf-8")
    doc_cell_counts = {
        match.group(1): tuple(map(int, match.groups()[1:]))
        for match in re.finditer(r"^[├└]─ ([A-Za-z0-9]+) .*?\((\d+)/(\d+)/(\d+)\)", tree_doc, re.MULTILINE)
    }
    graph_cell_counts = {
        item["physical_cell"]: (
            item["point_count"], item["facet_explicit_point_count"], item["cell_only_point_count"]
        )
        for item in graph["physical_cell_nodes"]
    }
    add(
        checks,
        "tree_document_cell_counts_match_graph",
        doc_cell_counts == graph_cell_counts,
        documented_cell_count=len(doc_cell_counts),
        graph_cell_count=len(graph_cell_counts),
    )

    audit_doc = (PACKAGE / "coverage-and-gap-audit.md").read_text(encoding="utf-8")
    expected_family_rows = [
        "| 材料 | M1–M5 | 37 |",
        "| 芯片 | C1–C7 | 45 |",
        "| 封装 | P1 | 9 |",
        "| 光/结构组件 | D1–D13、B1–B2 | 104 |",
        "| 模块 | MOD1–MOD3 | 46 |",
        "| EMS | EMS1 | 3 |",
        "| 设备 | EQ1–EQ8 | 27 |",
    ]
    add(
        checks,
        "audit_document_family_counts",
        all(row in audit_doc for row in expected_family_rows) and sum([37, 45, 9, 104, 46, 3, 27]) == 271,
    )

    canonical_targets = [
        "knowledge.yaml", "research_questions.yaml", "points.csv", "edges.csv",
        "route_bom.csv", "tree.yaml", "questions_manual.csv",
    ]
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *canonical_targets],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    add(checks, "canonical_targets_zero_diff", not status, observed=status)

    source_mentions_archive = []
    for path in python_files:
        if path.name == Path(__file__).name:
            continue
        if "archive/" in path.read_text(encoding="utf-8"):
            source_mentions_archive.append(path.name)
    add(checks, "no_archive_source_path", not source_mentions_archive, files=source_mentions_archive)

    report = {
        "meta": {
            "mode": "draft_only",
            "python_interpreter": EXPECTED_PYTHON,
            "canonical_write_performed": False,
        },
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "passed_count": sum(item["passed"] for item in checks),
            "all_passed": all(item["passed"] for item in checks),
        },
    }
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False, width=180))
    raise SystemExit(0 if report["summary"]["all_passed"] else 1)


if __name__ == "__main__":
    main()
