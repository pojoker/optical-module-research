#!/Users/jowang/miniconda3/bin/python3
"""Propose point facets and requirement matches without changing canonical data."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import yaml


def matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def collect_facets(cell: str, quote: str, rules: dict) -> list[str]:
    facets: list[str] = []
    for namespace, values in rules.get("facet_rules", {}).get(cell, {}).items():
        for value, patterns in values.items():
            if matches(quote, patterns):
                facets.append(f"{namespace}.{value}")
    return sorted(facets)


def collect_roles(point_id: str, cell: str, quote: str, rules: dict) -> list[dict]:
    roles: list[dict] = []
    role_text = quote.replace("制造业单项冠军", "")
    role_cells = {
        "component_design": {"C1", "C3", "C4", "C5"},
        "component_manufacture": {"C1", "C3", "C4", "C5"},
        "process_enable": {"C4"},
        "module_integrate": {"MOD1"},
        "product_offer": {"C1", "C3", "C4", "C5", "MOD1"},
    }
    for role, patterns in rules.get("role_rules", {}).items():
        if cell not in role_cells.get(role, set()):
            continue
        negative_patterns = rules.get("role_negative_patterns", {}).get(role, [])
        override = rules.get("point_overrides", {}).get(point_id, {})
        if role in override.get("suppress_roles", []) or any(re.search(pattern, role_text) for pattern in negative_patterns):
            continue
        hit_patterns = [pattern for pattern in patterns if re.search(pattern, role_text)]
        if hit_patterns:
            roles.append({"role": role, "basis_patterns": hit_patterns})
    if not roles:
        roles.append({"role": "role_unknown", "basis_patterns": []})
    return roles


def requirement_disposition(cell: str, facets: set[str], rules: dict) -> tuple[list[dict], list[dict]]:
    matches: list[dict] = []
    related: list[dict] = []
    for rule in rules.get("requirement_match_rules", []):
        if rule["cell"] != cell:
            continue
        exact_all = set(rule.get("exact_all", []))
        generic_any = set(rule.get("generic_any", []))
        attribute_exact_any = set(rule.get("attribute_exact_any", []))
        related_any = set(rule.get("related_any", []))
        if exact_all and exact_all <= facets:
            level = "exact_keyword_candidate"
            matched = sorted(exact_all)
        elif generic_any and generic_any & facets:
            level = "generic_scope_candidate"
            matched = sorted(generic_any & facets)
        elif attribute_exact_any and attribute_exact_any & facets:
            level = "attribute_exact_candidate"
            matched = sorted(attribute_exact_any & facets)
        elif related_any and related_any & facets:
            related.append(
                {
                    "requirement_id": rule["requirement_id"],
                    "relation": "related_facet_only",
                    "matched_facets": sorted(related_any & facets),
                    "limitation": rule["limitation"],
                    "promotion_status": "not_a_requirement_match",
                }
            )
            continue
        else:
            continue
        limitation = rule["limitation"]
        conflicts = [note for facet, note in rule.get("conflict_notes", {}).items() if facet in facets]
        if conflicts:
            limitation = f"{limitation}; " + "; ".join(conflicts)
        matches.append(
            {
                "requirement_id": rule["requirement_id"],
                "match_level": level,
                "matched_facets": matched,
                "limitation": limitation,
                "promotion_status": "needs_human_review",
            }
        )
    return matches, related


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--points", required=True)
    parser.add_argument("--rules", required=True)
    args = parser.parse_args()

    rules = yaml.safe_load(Path(args.rules).read_text(encoding="utf-8"))
    target_cells = set(rules.get("facet_rules", {}))
    proposals: list[dict] = []
    with Path(args.points).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["cell_id"] not in target_cells:
                continue
            quote = row["命中引语"]
            facets = collect_facets(row["cell_id"], quote, rules)
            override = rules.get("point_overrides", {}).get(row["point_id"], {})
            attachment_eligible = override.get("attachment_eligible", True)
            matches_for_point, related_for_point = requirement_disposition(row["cell_id"], set(facets), rules)
            if not attachment_eligible:
                matches_for_point = []
                related_for_point = []
            proposed_roles = collect_roles(row["point_id"], row["cell_id"], quote, rules) if attachment_eligible else []
            proposals.append(
                {
                    "point_id": row["point_id"],
                    "company": row["公司"],
                    "physical_cell": row["cell_id"],
                    "point_status": row["状态"],
                    "quote": quote,
                    "subject_scope": override.get("subject_scope", "direct_or_unresolved"),
                    "attachment_eligible": attachment_eligible,
                    "scope_note": override.get("reason"),
                    "proposed_facets": facets,
                    "facet_specificity": "facet_explicit" if facets else "cell_only",
                    "facet_maturity_state": "not_inferred_from_point_status",
                    "proposed_roles": proposed_roles,
                    "role_promotion_status": "blocked_subject_scope" if not attachment_eligible else "needs_human_review",
                    "requirement_matches": matches_for_point,
                    "related_facet_evidence": related_for_point,
                    "promotion_status": "blocked_subject_scope" if not attachment_eligible else "needs_human_review",
                }
            )

    per_requirement: dict[str, Counter[str]] = {}
    related_per_requirement: Counter[str] = Counter()
    companies_per_requirement: dict[str, set[str]] = {}
    for proposal in proposals:
        for match in proposal["requirement_matches"]:
            requirement_id = match["requirement_id"]
            per_requirement.setdefault(requirement_id, Counter())[match["match_level"]] += 1
            companies_per_requirement.setdefault(requirement_id, set()).add(proposal["company"])
        for related in proposal["related_facet_evidence"]:
            related_per_requirement[related["requirement_id"]] += 1
    all_requirement_ids = [item["requirement_id"] for item in rules.get("requirement_match_rules", [])]
    coverage = []
    for requirement_id in all_requirement_ids:
        counts = per_requirement.get(requirement_id, Counter())
        match_total = sum(counts.values())
        coverage.append(
            {
                "requirement_id": requirement_id,
                "exact_keyword_candidate_points": counts["exact_keyword_candidate"],
                "generic_scope_candidate_points": counts["generic_scope_candidate"],
                "attribute_exact_candidate_points": counts["attribute_exact_candidate"],
                "related_facet_only_points": related_per_requirement[requirement_id],
                "unique_candidate_companies": len(companies_per_requirement.get(requirement_id, set())),
                "gap_status": "no_candidate_point" if match_total == 0 else "candidate_points_need_review",
            }
        )

    output = {
        "meta": {
            "mode": "draft_only",
            "method": "deterministic_keyword_proposal",
            "python_interpreter": "/Users/jowang/miniconda3/bin/python3",
            "canonical_write_performed": False,
            "warning": "keyword hits are proposals, not company-route service conclusions",
            "maturity_warning": "point_status is not inherited by individual facets; mixed in-production and in-development quotes require facet-level review",
        },
        "summary": {
            "target_point_count": len(proposals),
            "unique_company_count": len({item["company"] for item in proposals}),
            "facet_explicit_point_count": sum(item["facet_specificity"] == "facet_explicit" for item in proposals),
            "cell_only_point_count": sum(item["facet_specificity"] == "cell_only" for item in proposals),
            "candidate_match_point_count": sum(bool(item["requirement_matches"]) for item in proposals),
            "related_facet_only_point_count": sum(bool(item["related_facet_evidence"]) for item in proposals),
            "blocked_subject_scope_point_count": sum(not item["attachment_eligible"] for item in proposals),
        },
        "requirement_coverage": coverage,
        "point_facet_proposals": proposals,
    }
    sys.stdout.write(yaml.safe_dump(output, allow_unicode=True, sort_keys=False, width=180))


if __name__ == "__main__":
    main()
