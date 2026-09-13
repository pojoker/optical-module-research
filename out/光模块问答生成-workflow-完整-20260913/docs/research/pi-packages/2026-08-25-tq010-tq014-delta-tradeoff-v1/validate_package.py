#!/Users/jowang/miniconda3/bin/python3
"""Final reproducibility and invariant checks for the draft-only package."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


EXPECTED_PYTHON = "/Users/jowang/miniconda3/bin/python3"


def run_python(script: Path, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    package = Path(args.package).resolve()
    workspace = Path(args.workspace).resolve()
    checks: list[dict] = []

    checks.append(
        {
            "check": "miniconda_interpreter",
            "passed": sys.executable == EXPECTED_PYTHON,
            "observed": sys.executable,
        }
    )

    yaml_files = sorted(path for path in package.glob("*.yaml") if path.name != "validation-final.yaml")
    yaml_errors = []
    for path in yaml_files:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report all parse failures
            yaml_errors.append(f"{path.name}: {exc}")
    checks.append(
        {
            "check": "all_package_yaml_parse",
            "passed": not yaml_errors,
            "yaml_file_count": len(yaml_files),
            "errors": yaml_errors,
        }
    )

    script_errors = []
    scripts = sorted(package.glob("*.py"))
    for path in scripts:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:  # noqa: BLE001
            script_errors.append(f"{path.name}: {exc}")
    checks.append(
        {
            "check": "all_package_python_compile",
            "passed": not script_errors,
            "script_count": len(scripts),
            "errors": script_errors,
        }
    )

    matrix_output = run_python(
        package / "build_comparison_matrix.py",
        "--input",
        str(package.parent / "2026-08-24-tq009-route-profile-seeds-v1" / "route-profile-seeds-effective.yaml"),
        "--rules",
        str(package / "comparison-rules.yaml"),
    )
    checks.append(
        {
            "check": "comparison_matrix_reproducible",
            "passed": matrix_output == (package / "comparison-matrix.yaml").read_text(encoding="utf-8"),
        }
    )

    pilot_output = run_python(
        package / "build_company_match_pilot.py",
        "--points",
        str(workspace / "points.csv"),
        "--rules",
        str(package / "company-facet-rules-draft.yaml"),
    )
    checks.append(
        {
            "check": "company_match_pilot_reproducible",
            "passed": pilot_output == (package / "company-capability-match-pilot.yaml").read_text(encoding="utf-8"),
        }
    )

    pilot = yaml.safe_load(pilot_output)
    expected_summary = {
        "target_point_count": 56,
        "unique_company_count": 40,
        "facet_explicit_point_count": 39,
        "cell_only_point_count": 17,
        "candidate_match_point_count": 6,
        "related_facet_only_point_count": 14,
        "blocked_subject_scope_point_count": 1,
    }
    checks.append(
        {
            "check": "company_pilot_expected_summary",
            "passed": pilot["summary"] == expected_summary,
            "observed": pilot["summary"],
        }
    )

    proposals = {item["point_id"]: item for item in pilot["point_facet_proposals"]}
    invariant_results = {
        "P193_affiliate_blocked_and_no_roles": (
            proposals["P193"]["attachment_eligible"] is False
            and proposals["P193"]["proposed_roles"] == []
            and proposals["P193"]["requirement_matches"] == []
        ),
        "P195_no_product_offer": "product_offer" not in {item["role"] for item in proposals["P195"]["proposed_roles"]},
        "P119_no_module_integrate": "module_integrate" not in {item["role"] for item in proposals["P119"]["proposed_roles"]},
        "P101_related_only_not_requirement_match": (
            proposals["P101"]["requirement_matches"] == []
            and any(item["requirement_id"] == "PCR-D04-C4-001" for item in proposals["P101"]["related_facet_evidence"])
        ),
        "P254_OSFP_attribute_only_with_rate_conflict": (
            len(proposals["P254"]["requirement_matches"]) == 1
            and proposals["P254"]["requirement_matches"][0]["match_level"] == "attribute_exact_candidate"
            and "1.6T" in proposals["P254"]["requirement_matches"][0]["limitation"]
            and "800 Gbps" in proposals["P254"]["requirement_matches"][0]["limitation"]
        ),
    }
    checks.append(
        {
            "check": "review_fix_invariants",
            "passed": all(invariant_results.values()),
            "invariants": invariant_results,
        }
    )

    graph = yaml.safe_load((package / "company-placeable-graph-draft.yaml").read_text(encoding="utf-8"))
    graph_summary = graph["current_attachment_summary"]
    summary_mapping = {
        "point_count": expected_summary["target_point_count"],
        "unique_company_strings": expected_summary["unique_company_count"],
        "facet_explicit_points": expected_summary["facet_explicit_point_count"],
        "cell_only_points": expected_summary["cell_only_point_count"],
        "points_with_candidate_requirement_match": expected_summary["candidate_match_point_count"],
        "points_with_related_facet_only": expected_summary["related_facet_only_point_count"],
        "blocked_subject_scope_points": expected_summary["blocked_subject_scope_point_count"],
    }
    checks.append(
        {
            "check": "graph_summary_matches_pilot",
            "passed": all(graph_summary.get(key) == value for key, value in summary_mapping.items()),
            "observed": graph_summary,
        }
    )

    report = {
        "meta": {
            "mode": "draft_only",
            "python_interpreter": sys.executable,
            "canonical_write_performed": False,
        },
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "passed_count": sum(item["passed"] for item in checks),
            "all_passed": all(item["passed"] for item in checks),
        },
    }
    sys.stdout.write(yaml.safe_dump(report, allow_unicode=True, sort_keys=False, width=180))
    raise SystemExit(0 if report["summary"]["all_passed"] else 1)


if __name__ == "__main__":
    main()
