#!/Users/jowang/miniconda3/bin/python3
"""Build span-backed draft company attachments for every points.csv row."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def evidence_spans(text: str, patterns: list[str]) -> list[dict]:
    spans: list[dict] = []
    seen: set[tuple[int, int, str]] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            key = (match.start(), match.end(), match.group(0))
            if key in seen:
                continue
            seen.add(key)
            spans.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                }
            )
    return sorted(spans, key=lambda item: (item["start"], item["end"], item["text"]))


def collect_maturity_markers(text: str, registry: dict) -> list[dict]:
    markers = []
    for marker_type, patterns in registry.get("maturity_rules", {}).items():
        spans = evidence_spans(text, patterns)
        if spans:
            markers.append({"marker_type": marker_type, "evidence_spans": spans})
    return markers


def local_maturity_types(facet_spans: list[dict], maturity_markers: list[dict], radius: int = 70) -> list[str]:
    types: set[str] = set()
    for facet_span in facet_spans:
        for marker in maturity_markers:
            for marker_span in marker["evidence_spans"]:
                if marker_span["end"] >= facet_span["start"] - radius and marker_span["start"] <= facet_span["end"] + radius:
                    types.add(marker["marker_type"])
    return sorted(types)


def collect_facets(text: str, cell_config: dict, maturity_markers: list[dict]) -> list[dict]:
    assertions = []
    for namespace, values in cell_config.get("facets", {}).items():
        for value, patterns in values.items():
            spans = evidence_spans(text, patterns)
            if not spans:
                continue
            assertions.append(
                {
                    "facet": f"{namespace}.{value}",
                    "evidence_spans": spans,
                    "local_maturity_markers": local_maturity_types(spans, maturity_markers),
                    "facet_maturity_state": "not_inferred",
                    "review_status": "needs_human_review",
                }
            )
    return assertions


def role_match_is_title_only(role: str, span: dict, text: str) -> bool:
    if role != "component_manufacture" or span["text"] not in {"制造", "生产"}:
        return False
    context = text[max(0, span["start"] - 20) : min(len(text), span["end"] + 20)]
    return "制造业单项冠军" in context


def collect_roles(
    point_id: str,
    text: str,
    family: str,
    registry: dict,
    attachment_eligible: bool,
    blocked_roles: set[str],
) -> list[dict]:
    if not attachment_eligible:
        return []
    assertions = []
    for role, patterns in registry.get("role_rules", {}).get(family, {}).items():
        if role in blocked_roles:
            continue
        if any(re.search(pattern, text) for pattern in registry.get("role_negative_patterns", {}).get(role, [])):
            continue
        spans = [span for span in evidence_spans(text, patterns) if not role_match_is_title_only(role, span, text)]
        if spans:
            assertions.append(
                {
                    "role": role,
                    "evidence_spans": spans,
                    "review_status": "needs_human_review",
                }
            )
    return assertions


def normalize_company_key(name: str) -> str:
    value = unicodedata.normalize("NFKC", name).lower()
    value = re.sub(r"[（(].*?[）)]", "", value)
    value = re.sub(r"(?:股份有限公司|有限责任公司|有限公司|co\.?[,]?\s* ltd\.?|corporation|corp\.?|inc\.?)$", "", value)
    value = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)
    return value


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


def route_index(route_pilot_path: Path | None) -> dict[str, dict]:
    if route_pilot_path is None:
        return {}
    data = yaml.safe_load(route_pilot_path.read_text(encoding="utf-8"))
    return {item["point_id"]: item for item in data["point_facet_proposals"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--points", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--route-pilot")
    args = parser.parse_args()

    registry = yaml.safe_load(Path(args.registry).read_text(encoding="utf-8"))
    tree = yaml.safe_load(Path(args.tree).read_text(encoding="utf-8"))
    valid_cells = collect_cell_ids(tree)
    route_points = route_index(Path(args.route_pilot) if args.route_pilot else None)

    with Path(args.points).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    proposals = []
    identity_names: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        point_id = row["point_id"]
        cell = row["cell_id"]
        if cell not in valid_cells:
            raise ValueError(f"point {point_id} references unknown tree cell {cell}")
        if cell not in registry["cells"]:
            raise ValueError(f"point {point_id} cell {cell} missing from facet registry")
        quote = row["命中引语"]
        override = registry.get("subject_overrides", {}).get(point_id, {})
        subject_scope = override.get("subject_scope", "direct_or_unresolved")
        attachment_eligible = override.get("attachment_eligible", True)
        cell_config = registry["cells"][cell]
        maturity_markers = collect_maturity_markers(quote, registry) if attachment_eligible else []
        facets = collect_facets(quote, cell_config, maturity_markers) if attachment_eligible else []
        roles = collect_roles(
            point_id,
            quote,
            cell_config["family"],
            registry,
            attachment_eligible,
            set(override.get("blocked_roles", [])),
        )
        company_key = normalize_company_key(row["公司"])
        identity_names[company_key].add(row["公司"])
        route_item = route_points.get(point_id)
        route_relation = None
        if route_item:
            route_relation = {
                "route_pilot_ref": f"../2026-08-25-tq010-tq014-delta-tradeoff-v1/company-capability-match-pilot.yaml#{point_id}",
                "requirement_candidates": route_item.get("requirement_matches", []),
                "related_facet_evidence": route_item.get("related_facet_evidence", []),
                "route_service_conclusion": False,
            }
        proposals.append(
            {
                "point_id": point_id,
                "company_string": row["公司"],
                "company_identity_key": company_key,
                "physical_cell": cell,
                "cell_family": cell_config["family"],
                "point_status": row["状态"],
                "point_status_inherited_by_facets": False,
                "quote_ref": f"points.csv#{point_id}",
                "source_anchor": row["锚点URL"],
                "subject_scope": subject_scope,
                "attachment_eligible": attachment_eligible,
                "scope_note": override.get("reason"),
                "block_type": override.get("block_type") if not attachment_eligible else None,
                "facet_assertions": facets,
                "facet_specificity": "facet_explicit" if facets else "cell_only",
                "role_assertions": roles,
                "role_specificity": "role_explicit" if roles else "role_unknown_or_blocked",
                "maturity_markers": maturity_markers,
                "route_relation": route_relation,
                "review_status": "blocked_attachment_scope" if not attachment_eligible else "needs_human_review",
            }
        )

    alias_candidates = [
        {"company_identity_key": key, "company_strings": sorted(names), "merge_status": "needs_human_review"}
        for key, names in sorted(identity_names.items())
        if len(names) > 1
    ]
    occupied_counts = Counter(item["physical_cell"] for item in proposals)
    facet_counts = Counter(item["physical_cell"] for item in proposals if item["facet_assertions"])
    role_counts = Counter(item["physical_cell"] for item in proposals if item["role_assertions"])
    cell_coverage = []
    for cell in sorted(occupied_counts):
        cell_coverage.append(
            {
                "physical_cell": cell,
                "point_count": occupied_counts[cell],
                "facet_explicit_point_count": facet_counts[cell],
                "cell_only_point_count": occupied_counts[cell] - facet_counts[cell],
                "role_explicit_point_count": role_counts[cell],
                "registry_status": "covered",
            }
        )

    output = {
        "meta": {
            "mode": "draft_only",
            "method": "deterministic_span_backed_facet_and_role_proposal",
            "python_interpreter": "/Users/jowang/miniconda3/bin/python3",
            "canonical_write_performed": False,
            "warning": "proposals require human review and do not establish route service, supply, customer, or adoption",
        },
        "summary": {
            "point_count": len(proposals),
            "unique_point_count": len({item["point_id"] for item in proposals}),
            "company_string_count": len({item["company_string"] for item in proposals}),
            "company_identity_key_count": len(identity_names),
            "alias_candidate_cluster_count": len(alias_candidates),
            "occupied_cell_count": len(occupied_counts),
            "registry_cell_count": len(registry["cells"]),
            "facet_explicit_point_count": sum(bool(item["facet_assertions"]) for item in proposals),
            "cell_only_point_count": sum(not item["facet_assertions"] for item in proposals),
            "role_explicit_point_count": sum(bool(item["role_assertions"]) for item in proposals),
            "role_unknown_or_blocked_point_count": sum(not item["role_assertions"] for item in proposals),
            "attachment_blocked_point_count": sum(not item["attachment_eligible"] for item in proposals),
            "subject_scope_blocked_point_count": sum(item["block_type"] == "subject_scope" for item in proposals),
            "evidence_scope_blocked_point_count": sum(item["block_type"] == "evidence_scope" for item in proposals),
            "route_pilot_linked_point_count": sum(item["route_relation"] is not None for item in proposals),
            "route_service_conclusion_count": 0,
        },
        "company_alias_candidates": alias_candidates,
        "cell_coverage": cell_coverage,
        "point_attachment_proposals": proposals,
    }
    print(yaml.safe_dump(output, allow_unicode=True, sort_keys=False, width=180))


if __name__ == "__main__":
    main()
