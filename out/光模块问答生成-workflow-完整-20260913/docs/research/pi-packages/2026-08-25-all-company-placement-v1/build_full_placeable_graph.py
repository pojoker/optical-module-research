#!/Users/jowang/miniconda3/bin/python3
"""Compile the full draft graph summary from tree and attachment proposals."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def collect_tree_cells(nodes: list, ancestors: list[str] | None = None) -> list[dict]:
    ancestors = ancestors or []
    records = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        group_name = node.get("名称")
        next_ancestors = ancestors + ([group_name] if group_name else [])
        if "cell_id" in node:
            records.append(
                {
                    "physical_cell": node["cell_id"],
                    "cell_name": node.get("名称"),
                    "tree_path": ancestors + [node.get("名称")],
                    "tree_route_label": node.get("路线"),
                }
            )
        if isinstance(node.get("children"), list):
            records.extend(collect_tree_cells(node["children"], next_ancestors))
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--attachments", required=True)
    parser.add_argument("--registry", required=True)
    args = parser.parse_args()

    tree = yaml.safe_load(Path(args.tree).read_text(encoding="utf-8"))
    attachments = yaml.safe_load(Path(args.attachments).read_text(encoding="utf-8"))
    registry = yaml.safe_load(Path(args.registry).read_text(encoding="utf-8"))
    proposals = attachments["point_attachment_proposals"]
    by_cell: defaultdict[str, list[dict]] = defaultdict(list)
    for proposal in proposals:
        by_cell[proposal["physical_cell"]].append(proposal)

    cell_nodes = []
    for record in collect_tree_cells(tree["tree"]):
        cell = record["physical_cell"]
        items = by_cell.get(cell, [])
        facets = sorted({facet["facet"] for item in items for facet in item["facet_assertions"]})
        roles = sorted({role["role"] for item in items for role in item["role_assertions"]})
        maturity_types = sorted(
            {
                marker["marker_type"]
                for item in items
                if item["attachment_eligible"]
                for marker in item["maturity_markers"]
            }
        )
        cell_nodes.append(
            {
                **record,
                "point_count": len(items),
                "eligible_attachment_count": sum(item["attachment_eligible"] for item in items),
                "blocked_attachment_count": sum(not item["attachment_eligible"] for item in items),
                "company_string_count": len({item["company_string"] for item in items}),
                "facet_explicit_point_count": sum(bool(item["facet_assertions"]) for item in items),
                "cell_only_point_count": sum(not item["facet_assertions"] for item in items),
                "observed_facets": facets,
                "observed_roles": roles,
                "observed_maturity_marker_types": maturity_types,
                "facet_registry_status": "covered" if cell in registry["cells"] else ("not_required_unoccupied" if not items else "missing"),
            }
        )

    facet_assertion_count = sum(len(item["facet_assertions"]) for item in proposals)
    role_assertion_count = sum(len(item["role_assertions"]) for item in proposals)
    route_requirement_edges = sum(
        len(item["route_relation"]["requirement_candidates"])
        for item in proposals
        if item["route_relation"] is not None
    )
    route_related_edges = sum(
        len(item["route_relation"]["related_facet_evidence"])
        for item in proposals
        if item["route_relation"] is not None
    )
    subject_scopes = Counter(item["subject_scope"] for item in proposals)
    output = {
        "meta": {
            "mode": "draft_only",
            "purpose": "full_current_company_data_placeable_graph",
            "physical_tree_source": "tree.yaml",
            "attachment_source": "all-company-attachments-draft.yaml",
            "route_relation_source": "../2026-08-25-tq010-tq014-delta-tradeoff-v1/company-capability-match-pilot.yaml",
            "canonical_write_performed": False,
        },
        "placement_readiness": {
            "source_point_count": len(proposals),
            "declared_cell_edge_count": len(proposals),
            "eligible_company_attachment_count": sum(item["attachment_eligible"] for item in proposals),
            "blocked_review_queue_count": sum(not item["attachment_eligible"] for item in proposals),
            "facet_assertion_count": facet_assertion_count,
            "unique_observed_facet_count": len({facet["facet"] for item in proposals for facet in item["facet_assertions"]}),
            "role_assertion_count": role_assertion_count,
            "route_pilot_linked_point_count": sum(item["route_relation"] is not None for item in proposals),
            "route_requirement_candidate_edge_count": route_requirement_edges,
            "route_related_facet_edge_count": route_related_edges,
            "why_causal_edge_count": 0,
            "route_service_edge_count": 0,
            "all_source_points_have_a_graph_disposition": True,
        },
        "knowledge_systems": {
            "physical": {
                "node_types": ["physical_cell", "capability_facet", "company_capability_role"],
                "source": "tree.yaml + full-facet-registry-draft.yaml",
            },
            "technology_route": {
                "node_types": ["route_profile_seed", "route_axis_observation", "route_product_attribute", "physical_capability_requirement", "validation_gap"],
                "source": "../2026-08-25-tq010-tq014-delta-tradeoff-v1/",
            },
            "why_bridge": {
                "required_chain": ["scenario_constraint", "engineering_mechanism", "tradeoff_or_bottleneck", "route_requirement", "physical_capability_or_product_attribute"],
                "current_status": "schema_only_blocked_by_missing_controlled_tradeoff_evidence",
                "instantiated_causal_edges": 0,
            },
            "company_evidence": {
                "node_types": ["company_string", "company_identity_candidate", "company_evidence_point", "company_capability_assertion", "attachment_review_item"],
                "source": "points.csv + all-company-attachments-draft.yaml",
            },
        },
        "edge_contract": [
            {"edge_type": "POINT_DECLARED_CELL", "count": len(proposals), "meaning": "source row's existing cell, not a newly inferred capability"},
            {"edge_type": "POINT_ELIGIBLE_ATTACHMENT", "count": sum(item["attachment_eligible"] for item in proposals), "meaning": "eligible for facet/role review; not canonical promotion"},
            {"edge_type": "POINT_BLOCKED_ATTACHMENT", "count": sum(not item["attachment_eligible"] for item in proposals), "meaning": "kept in review queue, not attached as company capability"},
            {"edge_type": "POINT_PROPOSES_FACET", "count": facet_assertion_count, "meaning": "span-backed draft facet assertion"},
            {"edge_type": "POINT_PROPOSES_ROLE", "count": role_assertion_count, "meaning": "span-backed draft role assertion"},
            {"edge_type": "ASSERTION_CANDIDATE_MATCHES_REQUIREMENT", "count": route_requirement_edges, "meaning": "generic-scope or single-attribute candidate; not route service"},
            {"edge_type": "ASSERTION_RELATED_FACET_ONLY", "count": route_related_edges, "meaning": "does not create a requirement match"},
            {"edge_type": "COMPANY_SERVES_ROUTE", "count": 0, "meaning": "requires separate Route Service Evidence"},
            {"edge_type": "CONSTRAINT_EXPLAINS_REQUIREMENT", "count": 0, "meaning": "requires controlled tradeoff evidence"},
        ],
        "identity_and_scope_audit": {
            "company_string_count": attachments["summary"]["company_string_count"],
            "company_identity_key_count": attachments["summary"]["company_identity_key_count"],
            "alias_candidate_cluster_count": attachments["summary"]["alias_candidate_cluster_count"],
            "subject_scope_counts": dict(sorted(subject_scopes.items())),
            "company_id_status": "missing_stable_company_id",
            "automatic_alias_merge_performed": False,
        },
        "remaining_gaps": {
            "cell_only_point_count": attachments["summary"]["cell_only_point_count"],
            "role_unknown_or_blocked_point_count": attachments["summary"]["role_unknown_or_blocked_point_count"],
            "facet_maturity_state": "not_inferred_for_all_facets",
            "mixed_or_multiple_maturity_marker_point_count": sum(len(item["maturity_markers"]) > 1 for item in proposals),
            "unoccupied_tree_cells": sorted(record["physical_cell"] for record in cell_nodes if record["point_count"] == 0),
            "canonical_promotion_status": "not_requested_and_not_performed",
        },
        "physical_cell_nodes": cell_nodes,
    }
    print(yaml.safe_dump(output, allow_unicode=True, sort_keys=False, width=180))


if __name__ == "__main__":
    main()
