#!/usr/bin/env python3
"""Build a mechanical domain relation view and human-review leads.

The module reads existing canonical ledgers.  It never writes back to them,
computes no question state, and emits no canonical assertion.  Output files are
created only when the caller explicitly supplies an output path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


RELATION_TYPES = {
    "part_of",
    "connects_to",
    "requires",
    "has_capability",
    "offers_product",
    "implements_route",
    "has_stage",
    "supported_by",
}
DISCIPLINES = {
    "source_encoded != derived_candidate",
    "actual != planned",
    "lead != formal_question",
    "generated_output != canonical_data",
}
CANONICAL_INPUTS = {
    "tree.yaml",
    "route_bom.csv",
    "points.csv",
    "knowledge.yaml",
    "calls/events.csv",
    "calls/event_claims.csv",
    "calls/event_evidence.csv",
}


class DomainRelationError(ValueError):
    """Raised when a canonical source or the small relation contract is invalid."""


def _csv_rows(root: Path, relative_path: str) -> list[dict[str, str]]:
    path = root / relative_path
    if not path.is_file():
        raise DomainRelationError(f"missing canonical input: {relative_path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _yaml(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        raise DomainRelationError(f"missing canonical input: {relative_path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise DomainRelationError(f"{relative_path}: expected mapping")
    return data


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _relation(
    relation_type: str,
    subject_ref: str,
    object_ref: str,
    source_refs: list[str],
    *,
    modality: str = "unspecified",
) -> dict[str, Any]:
    if relation_type not in RELATION_TYPES:
        raise DomainRelationError(f"unregistered relation type: {relation_type}")
    if modality not in {"actual", "planned", "unspecified"}:
        raise DomainRelationError(f"unsupported modality: {modality}")
    sources = sorted(set(source_refs))
    return {
        "relation_id": _stable_id(
            "DR", relation_type, subject_ref, object_ref, sources, modality
        ),
        "relation_type": relation_type,
        "subject_ref": subject_ref,
        "object_ref": object_ref,
        "origin": "source_encoded",
        "modality": modality,
        "source_refs": sources,
    }


def _validate_contract(root: Path) -> None:
    contract = _yaml(root, "contracts/domain_relation_types.yaml")
    names = {
        row.get("name")
        for row in contract.get("relation_types", [])
        if isinstance(row, dict)
    }
    if names != RELATION_TYPES:
        raise DomainRelationError(
            f"relation contract must define exactly {sorted(RELATION_TYPES)}; got {sorted(names)}"
        )
    disciplines = set(contract.get("disciplines", []))
    if disciplines != DISCIPLINES:
        raise DomainRelationError("relation contract does not preserve the four disciplines")


def _tree_relations(root: Path) -> list[dict[str, Any]]:
    data = _yaml(root, "tree.yaml")
    relations: list[dict[str, Any]] = []

    def ref(node: dict[str, Any]) -> str:
        if node.get("cell_id"):
            return f"cell:{node['cell_id']}"
        if node.get("id"):
            return f"tree_node:{node['id']}"
        raise DomainRelationError("tree.yaml: node lacks id/cell_id")

    def walk(nodes: list[dict[str, Any]], parent_ref: str | None = None) -> None:
        for node in nodes:
            node_ref = ref(node)
            if parent_ref:
                relations.append(
                    _relation(
                        "part_of",
                        node_ref,
                        parent_ref,
                        [f"tree.yaml#{node_ref}"],
                    )
                )
            children = node.get("children") or []
            if children:
                if not isinstance(children, list):
                    raise DomainRelationError(f"tree.yaml: children for {node_ref} must be a list")
                walk(children, node_ref)

    walk(data.get("tree") or [])
    for flow_index, flow in enumerate(data.get("flows") or [], start=1):
        source = flow.get("from")
        targets = flow.get("to") or []
        if not source or not isinstance(targets, list):
            raise DomainRelationError(f"tree.yaml: invalid flow #{flow_index}")
        for target in targets:
            relations.append(
                _relation(
                    "connects_to",
                    f"cell:{source}",
                    f"cell:{target}",
                    [f"tree.yaml#flow:{flow_index}"],
                )
            )
    return relations


def _route_relations(root: Path) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for row in _csv_rows(root, "route_bom.csv"):
        route_item_id = row["route_item_id"].strip()
        cells = [cell.strip() for cell in row.get("cell_ids", "").split(",") if cell.strip()]
        for cell_id in cells:
            relations.append(
                _relation(
                    "requires",
                    f"route_item:{route_item_id}",
                    f"cell:{cell_id}",
                    [f"route_bom.csv#{route_item_id}"],
                )
            )
    return relations


def _point_modality(status: str) -> str:
    if status == "生产中":
        return "actual"
    if status == "在建":
        return "planned"
    return "unspecified"


def _capability_relations(root: Path) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for row in _csv_rows(root, "points.csv"):
        point_id = row["point_id"].strip()
        relations.append(
            _relation(
                "has_capability",
                f"company:{row['公司'].strip()}",
                f"cell:{row['cell_id'].strip()}",
                [f"points.csv#{point_id}"],
                modality=_point_modality(row.get("状态", "").strip()),
            )
        )
    return relations


def _evidence_object(kn_id: str, index: int, evidence: dict[str, Any]) -> str:
    anchor = evidence.get("锚")
    payload = json.dumps(anchor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"evidence:{_stable_id('EVR', kn_id, index, evidence.get('锚型'), payload)}"


def _knowledge_relations(root: Path) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    knowledge = _yaml(root, "knowledge.yaml").get("knowledge") or []
    for item in knowledge:
        kn_id = item.get("id")
        for index, evidence in enumerate(item.get("证据") or []):
            relations.append(
                _relation(
                    "supported_by",
                    f"knowledge:{kn_id}",
                    _evidence_object(str(kn_id), index, evidence),
                    [f"knowledge.yaml#{kn_id}/evidence/{index}"],
                )
            )
    return relations


def _stage_relations(root: Path) -> list[dict[str, Any]]:
    claims = {
        row["event_claim_id"]: row
        for row in _csv_rows(root, "calls/event_claims.csv")
    }
    evidence_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _csv_rows(root, "calls/event_evidence.csv"):
        if row.get("relationship") in {"reports", "supports"}:
            evidence_by_event[row["event_id"]].append(row)

    relations: list[dict[str, Any]] = []
    for event in _csv_rows(root, "calls/events.csv"):
        if event.get("event_category") != "product_stage":
            continue
        event_id = event["event_id"]
        program_id = event.get("program_id", "").strip()
        stage = event.get("lifecycle_stage", "").strip()
        if not program_id or not stage or stage == "not_applicable":
            continue
        links = evidence_by_event.get(event_id, [])
        linked_claims = [claims[row["event_claim_id"]] for row in links]
        modality = "unspecified"
        if linked_claims:
            modality = (
                "planned"
                if all(row.get("statement_kind") == "forward_looking" for row in linked_claims)
                else "actual"
            )
        source_refs = [f"calls/events.csv#{event_id}"]
        source_refs.extend(f"calls/event_evidence.csv#{row['evidence_id']}" for row in links)
        source_refs.extend(
            f"calls/event_claims.csv#{row['event_claim_id']}" for row in links
        )
        relations.append(
            _relation(
                "has_stage",
                f"program:{program_id}",
                f"lifecycle_stage:{stage}",
                source_refs,
                modality=modality,
            )
        )
    return relations


def _lead_rows(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = [row for row in relations if row["relation_type"] == "requires"]
    capabilities_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in relations:
        if row["relation_type"] == "has_capability":
            capabilities_by_cell[row["object_ref"]].append(row)

    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for requirement in requirements:
        route_ref = requirement["subject_ref"]
        cell_ref = requirement["object_ref"]
        for capability in capabilities_by_cell.get(cell_ref, []):
            key = (capability["subject_ref"], route_ref, cell_ref)
            row = grouped.setdefault(
                key,
                {
                    "lead_kind": "capability_requirement_overlap",
                    "subject_ref": capability["subject_ref"],
                    "route_item_ref": route_ref,
                    "matched_cell_ref": cell_ref,
                    "observed_modalities": set(),
                    "source_refs": set(requirement["source_refs"]),
                },
            )
            row["observed_modalities"].add(capability["modality"])
            row["source_refs"].update(capability["source_refs"])

    leads: list[dict[str, Any]] = []
    for key in sorted(grouped):
        row = grouped[key]
        modalities = sorted(row["observed_modalities"])
        sources = sorted(row["source_refs"])
        leads.append(
            {
                "lead_id": _stable_id("DL", *key),
                "lead_kind": row["lead_kind"],
                "subject_ref": row["subject_ref"],
                "route_item_ref": row["route_item_ref"],
                "matched_cell_ref": row["matched_cell_ref"],
                "observed_modalities": modalities,
                "source_refs": sources,
                "reason": (
                    "公司证据点与路线条目的一个物理格发生交集；"
                    "这不等于完整路线能力、具名产品、路线实现或客户采用。"
                ),
                "human_review_required": True,
            }
        )
    return leads


def build_domain_projection(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Return deterministic source-encoded relations and non-canonical leads."""
    root = repo_root.resolve()
    _validate_contract(root)
    relations = (
        _tree_relations(root)
        + _route_relations(root)
        + _capability_relations(root)
        + _knowledge_relations(root)
        + _stage_relations(root)
    )
    relations.sort(
        key=lambda row: (
            row["relation_type"], row["subject_ref"], row["object_ref"], row["relation_id"]
        )
    )
    if any(row["origin"] != "source_encoded" for row in relations):
        raise DomainRelationError("mechanical relation view may contain only source_encoded rows")
    return {"relations": relations, "leads": _lead_rows(relations)}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--relations-output", type=Path)
    parser.add_argument("--leads-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    projection = build_domain_projection(args.repo_root)
    if args.relations_output:
        _write_jsonl(args.relations_output, projection["relations"])
    if args.leads_output:
        _write_jsonl(args.leads_output, projection["leads"])
    print(
        json.dumps(
            {
                "relation_count": len(projection["relations"]),
                "lead_count": len(projection["leads"]),
                "canonical_inputs": sorted(CANONICAL_INPUTS),
                "generated_output_is_canonical": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
