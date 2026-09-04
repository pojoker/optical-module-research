"""Deterministic derivation of domestic capability positioning.

Reads reviewed constraint requirements (``calls/constraint_requirements.csv``)
and aligns them mechanically to the domestic capability universe (root
``points.csv``). Pure functions only: never writes canonical tables, never
emits business claims (competition, substitution, collaboration, supply,
satisfaction, benefit).  The two unstable structural views
(``structural_alternatives`` / ``co_required``) are always empty with a fixed
unsupported reason because ``route_bom.csv`` lacks evidence-verified
functional-equivalence and requiredness data.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

DOMESTIC_LISTING_LABELS = frozenset({
    "A股", "新三板", "未上市私企", "未上市(母上市)", "未上市国企",
})
VALID_POINT_STATUSES = frozenset({"生产中", "在建"})

# Auto-output forbidden business words.  Validator scans derived positioning
# fields and the WorkBuddy positioning block; original claim quotes are exempt.
FORBIDDEN_WORDS = (
    "竞争", "competition",
    "替代", "substitute",
    "合作", "collaboration", "partnership",
    "供应商", "供货",
    "满足需求", "解决卡点", "受益于",
)

STRUCTURAL_ALTERNATIVES_REASON = (
    "route_bom.csv 缺少经证据核验的功能等价组与 requiredness，"
    "本轮不提供该结构视图，等待独立结构证据工包。"
)
CO_REQUIRED_REASON = (
    "route_bom.csv 缺少经证据核验的必需共同组与 requiredness，"
    "本轮不提供该结构视图，等待独立结构证据工包。"
)

COMPARATORS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "=": lambda a, b: a == b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}

SUPPORTED_COMPARATORS = frozenset(COMPARATORS)


def is_domestic_point(point: dict[str, str]) -> bool:
    """True when a point belongs to the domestic capability universe."""
    return (
        point["上市标签"] in DOMESTIC_LISTING_LABELS
        and point["状态"] in VALID_POINT_STATUSES
    )


def scan_forbidden_words(text: str) -> list[str]:
    """Return forbidden business words found in derived output text."""
    lowered = text.lower()
    return [
        word for word in FORBIDDEN_WORDS
        if word in text or word.lower() in lowered
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_positioning_facts(root: Path) -> dict:
    """Load read-only facts needed to derive the positioning projection."""
    calls_dir = root / "calls"
    points = _read_csv(root / "points.csv")
    tree_text = (root / "tree.yaml").read_text(encoding="utf-8-sig")
    route_rows = _read_csv(root / "route_bom.csv")
    return {
        "requirements": _read_csv(calls_dir / "constraint_requirements.csv"),
        "point_metrics": _read_csv(calls_dir / "point_metrics.csv"),
        "claims": {row["claim_id"]: row for row in _read_csv(calls_dir / "claims.csv")},
        "sources": {row["source_id"]: row for row in _read_csv(calls_dir / "sources.csv")},
        "themes": {row["theme_id"]: row for row in _read_csv(calls_dir / "themes.csv")},
        "points": points,
        "point_ids": {row["point_id"] for row in points},
        "cell_ids": set(re.findall(r"cell_id:\s*([A-Za-z0-9_-]+)", tree_text)),
        "route_ids": {row["route_item_id"] for row in route_rows},
    }


def _requirement_as_of(req: dict, facts: dict) -> str:
    """Latest accessed_date across the requirement's evidence claim sources."""
    dates: list[str] = []
    for claim_id in req["evidence_claim_ids"].split(";"):
        claim_id = claim_id.strip()
        claim = facts["claims"].get(claim_id)
        if not claim:
            continue
        source = facts["sources"].get(claim["source_id"])
        if source and source["accessed_date"]:
            dates.append(source["accessed_date"])
    return max(dates) if dates else ""


def _numeric_triple(req: dict) -> bool:
    return all(req[field].strip() for field in ("comparator", "target_value", "unit"))


def _compare(value: str, comparator: str, target: str) -> bool | None:
    op = COMPARATORS.get(comparator.strip())
    if op is None:
        return None
    try:
        return bool(op(float(value), float(target)))
    except ValueError:
        return None


def derive_positioning(facts: dict) -> dict:
    """Derive the positioning projection from already-loaded facts.

    Returns a dict (JSON-serializable) with deterministic, stable-key-sorted
    lists and the fixed unsupported reasons for the structural views.
    """
    matches: list[dict] = []
    overlaps: list[dict] = []
    metric_comparisons: list[dict] = []
    gaps: list[dict] = []

    for req in sorted(facts["requirements"], key=lambda r: r["requirement_id"]):
        if req["review_status"] != "reviewed":
            continue
        cell_id = req["cell_id"]
        valid_points = sorted(
            (p for p in facts["points"] if is_domestic_point(p) and p["cell_id"] == cell_id),
            key=lambda p: p["point_id"],
        )
        if not valid_points:
            gaps.append({
                "requirement_id": req["requirement_id"],
                "theme_id": req["theme_id"],
                "cell_id": cell_id,
                "message": "当前 canonical 能力证据未覆盖该约束节点，仅表示现有能力点尚未落格",
            })
            continue

        requirement_as_of = _requirement_as_of(req, facts)
        for point in valid_points:
            matches.append({
                "requirement_id": req["requirement_id"],
                "theme_id": req["theme_id"],
                "company": point["公司"],
                "listing_label": point["上市标签"],
                "point_id": point["point_id"],
                "point_status": point["状态"],
                "cell_id": cell_id,
                "route_item_id": req["route_item_id"],
                "basis": "cell_only",
                "source_claim_ids": req["evidence_claim_ids"],
                "requirement_as_of": requirement_as_of,
                "point_as_of": point["检索日期"],
            })

        companies = sorted({p["公司"] for p in valid_points})
        if len(companies) >= 2:
            overlaps.append({
                "requirement_id": req["requirement_id"],
                "theme_id": req["theme_id"],
                "cell_id": cell_id,
                "companies": companies,
                "point_ids": [p["point_id"] for p in valid_points],
                "basis": "cell_only",
                "comparability": "unverified",
            })

        if _numeric_triple(req):
            metric_comparisons.extend(_metric_comparisons_for(req, valid_points, facts))

    return {
        "requirement_matches": matches,
        "capability_overlaps": overlaps,
        "metric_comparisons": metric_comparisons,
        "evidence_coverage_gaps": gaps,
        "structural_alternatives": [],
        "structural_alternatives_unsupported_reason": STRUCTURAL_ALTERNATIVES_REASON,
        "co_required": [],
        "co_required_unsupported_reason": CO_REQUIRED_REASON,
    }


def _metric_comparisons_for(req: dict, valid_points: list[dict], facts: dict) -> list[dict]:
    results: list[dict] = []
    base = {
        "requirement_id": req["requirement_id"],
        "theme_id": req["theme_id"],
        "cell_id": req["cell_id"],
        "metric_name": req["metric_name"],
        "comparator": req["comparator"],
        "target_value": req["target_value"],
        "unit": req["unit"],
    }
    for point in valid_points:
        reviewed = [
            m for m in facts["point_metrics"]
            if m["point_id"] == point["point_id"] and m["review_status"] == "reviewed"
        ]
        if not reviewed:
            results.append({
                **base,
                "point_id": point["point_id"], "company": point["公司"],
                "metric_value": "", "metric_unit": "", "metric_as_of": "",
                "passes": None, "status": "skipped",
                "skipped_reason": "missing_point_metric",
            })
            continue
        for metric in sorted(reviewed, key=lambda m: m["metric_id"]):
            entry = {
                **base,
                "point_id": point["point_id"], "company": point["公司"],
                "metric_value": metric["value"], "metric_unit": metric["unit"],
                "metric_as_of": metric["as_of"],
            }
            if metric["metric_name"].strip() != req["metric_name"].strip():
                entry.update(status="skipped", skipped_reason="metric_name_mismatch", passes=None)
            elif metric["unit"].strip() != req["unit"].strip():
                entry.update(status="skipped", skipped_reason="unit_mismatch", passes=None)
            else:
                passed = _compare(metric["value"], req["comparator"], req["target_value"])
                if passed is None:
                    entry.update(status="skipped", skipped_reason="non_comparable_value", passes=None)
                else:
                    entry.update(status="compared", skipped_reason="", passes=passed)
            results.append(entry)
    return results
