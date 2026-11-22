#!/Users/jowang/miniconda3/bin/python3
"""Build a deterministic field-evidence matrix from reviewed route-profile seeds."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml


COMPARISONS = {
    "CMP-D02-D03": ("RPS-D02", "RPS-D03"),
    "CMP-D04-D05": ("RPS-D04", "RPS-D05"),
}


def compare(left: dict, right: dict) -> str:
    left_unknown = left["observation_state"] == "unknown"
    right_unknown = right["observation_state"] == "unknown"
    if left_unknown and right_unknown:
        return "unknown_both"
    if left_unknown:
        return "unknown_left"
    if right_unknown:
        return "unknown_right"
    if left["value"] == right["value"]:
        return "same"
    return "different"


def load_overrides(path: str | None) -> dict[tuple[str, str], dict]:
    if path is None:
        return {}
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    overrides = {}
    for item in data.get("overrides", []):
        key = (item["comparison_id"], item["field"])
        if key in overrides:
            raise ValueError(f"duplicate comparison override: {key}")
        overrides[key] = item
    return overrides


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--rules")
    args = parser.parse_args()

    data = yaml.safe_load(Path(args.input).read_text(encoding="utf-8"))
    overrides = load_overrides(args.rules)
    seeds = {item["seed_id"]: item for item in data["route_profile_seeds"]}
    output = {
        "meta": {
            "mode": "draft_only",
            "method": "deterministic_field_evidence_comparison",
            "physical_delta_inferred": False,
            "canonical_write_performed": False,
        },
        "comparisons": [],
    }

    for comparison_id, (left_id, right_id) in COMPARISONS.items():
        left = seeds[left_id]
        right = seeds[right_id]
        rows = []
        counts: Counter[str] = Counter()
        for axis_name, left_fields in left["axes"].items():
            right_fields = right["axes"][axis_name]
            if list(left_fields) != list(right_fields):
                raise ValueError(f"schema mismatch: {comparison_id} {axis_name}")
            for field_name, left_leaf in left_fields.items():
                right_leaf = right_fields[field_name]
                field = f"{axis_name}.{field_name}"
                override = overrides.get((comparison_id, field))
                status = override["field_status"] if override else compare(left_leaf, right_leaf)
                counts[status] += 1
                row = {
                    "field": field,
                    "left": left_leaf,
                    "right": right_leaf,
                    "field_status": status,
                }
                if override:
                    row["comparison_override"] = {
                        "reason": override["reason"],
                        "evidence_refs": override.get("evidence_refs", []),
                    }
                rows.append(row)
        if len(rows) != 36:
            raise ValueError(f"expected 36 rows: {comparison_id} got {len(rows)}")
        output["comparisons"].append(
            {
                "comparison_id": comparison_id,
                "left_seed": left_id,
                "right_seed": right_id,
                "counts": dict(sorted(counts.items())),
                "rows": rows,
            }
        )

    sys.stdout.write(yaml.safe_dump(output, allow_unicode=True, sort_keys=False, width=160))


if __name__ == "__main__":
    main()
