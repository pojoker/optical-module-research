"""Referential and semantic checks for the independent calls ledger."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .event_intelligence import EventLedgerError, derive_event_projection, load_event_facts
from .positioning import SUPPORTED_COMPARATORS, derive_positioning, load_positioning_facts, scan_forbidden_words
from .schema import ENUMS, FILES
from .workbuddy import render_all_positioning_blocks


class ValidationError(Exception):
    pass


# Legacy solution_links is frozen at the exact current two rows.  Semantic
# per-row checks run first; any field change (even to a valid value) is then
# rejected by this byte-exact snapshot.
FROZEN_SOLUTION_LINKS = (
    {
        "link_id": "SL001",
        "bottleneck_theme_id": "T002",
        "solution_theme_id": "T003",
        "required_capability": "800G数通光模块的稳定量产和交付",
        "point_id": "P074",
        "match_stage": "node_overlap",
        "evidence_status": "insufficient",
        "missing_evidence": "缺少与该受限需求对应的增量产能、制造周期、客户认证及800G批量交付证据",
        "conclusion": "现有点仅证明中际旭创从事高端光通信收发模块研发生产销售并服务AI算力集群",
    },
    {
        "link_id": "SL002",
        "bottleneck_theme_id": "T007",
        "solution_theme_id": "T008",
        "required_capability": "高速InP激光器外延与芯片制造能力",
        "point_id": "P095",
        "match_stage": "node_overlap",
        "evidence_status": "insufficient",
        "missing_evidence": "缺少与800G/1.6T 2xFR4所需激光器规格对应的增量MOCVD产能、可靠性、客户认证和批量交付证据",
        "conclusion": "现有点只证明源杰科技具备MOCVD外延生长等内部生产线能力",
    },
)


def _read_csv(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected:
            raise ValidationError(f"{path.name}: header mismatch; expected {expected}")
        return list(reader)


def _ids(rows: list[dict[str, str]], field: str, filename: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for line, row in enumerate(rows, 2):
        value = row[field].strip()
        if not value:
            raise ValidationError(f"{filename}:{line}: empty {field}")
        if value in result:
            raise ValidationError(f"{filename}:{line}: duplicate {field} {value}")
        result[value] = row
    return result


def _enum(row: dict[str, str], field: str, enum_name: str, where: str) -> None:
    if row[field] not in ENUMS[enum_name]:
        raise ValidationError(f"{where}: invalid {field}={row[field]!r}")


def _url_ok(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate(project_root: Path) -> list[str]:
    calls_dir = project_root / "calls"
    tables = {name: _read_csv(calls_dir / name, fields) for name, fields in FILES.items()}
    universe = _ids(tables["universe.csv"], "company_id", "universe.csv")
    sources = _ids(tables["sources.csv"], "source_id", "sources.csv")
    claims = _ids(tables["claims.csv"], "claim_id", "claims.csv")
    themes = _ids(tables["themes.csv"], "theme_id", "themes.csv")
    _ids(tables["validations.csv"], "validation_id", "validations.csv")
    _ids(tables["commitments.csv"], "commitment_id", "commitments.csv")
    _ids(tables["solution_links.csv"], "link_id", "solution_links.csv")
    constraint_requirements = _ids(tables["constraint_requirements.csv"], "requirement_id", "constraint_requirements.csv")
    point_metrics = _ids(tables["point_metrics.csv"], "metric_id", "point_metrics.csv")
    _ids(tables["technology_feedback.csv"], "feedback_id", "technology_feedback.csv")

    tree_text = (project_root / "tree.yaml").read_text(encoding="utf-8-sig")
    cell_ids = set(re.findall(r"cell_id:\s*([A-Za-z0-9_-]+)", tree_text))
    route_rows = _read_any_csv(project_root / "route_bom.csv")
    route_ids = {row["route_item_id"] for row in route_rows}
    point_rows = _read_any_csv(project_root / "points.csv")
    point_ids = {row["point_id"] for row in point_rows}
    points_by_id = {row["point_id"]: row for row in point_rows}

    for row in tables["universe.csv"]:
        _enum(row, "role", "role", f"universe:{row['company_id']}")
        _enum(row, "enabled", "enabled", f"universe:{row['company_id']}")

    quarterly_slots: dict[str, set[str]] = {cid: set() for cid, row in universe.items() if row["enabled"] == "yes"}
    source_fingerprints: set[tuple[str, str, str, str]] = set()
    for row in tables["sources.csv"]:
        where = f"sources:{row['source_id']}"
        if row["company_id"] not in universe:
            raise ValidationError(f"{where}: unknown company_id {row['company_id']}")
        for field, enum_name in (("source_scope", "source_scope"), ("material_type", "material_type"), ("source_grade", "source_grade"), ("availability", "availability")):
            _enum(row, field, enum_name, where)
        if row["availability"] == "available":
            if row["source_grade"] == "unknown" or row["material_type"] == "unknown":
                raise ValidationError(f"{where}: available source cannot have unknown grade/type")
            if not (row["url"] or row["local_path"]):
                raise ValidationError(f"{where}: available source lacks URL/local anchor")
            if row["url"] and not _url_ok(row["url"]):
                raise ValidationError(f"{where}: invalid URL")
            if not row["accessed_date"]:
                raise ValidationError(f"{where}: available source lacks accessed_date")
            if row["local_path"] and not (calls_dir / row["local_path"]).is_file():
                raise ValidationError(f"{where}: local_path does not exist")
        elif not row["missing_reason"]:
            raise ValidationError(f"{where}: missing source must explain why")
        fingerprint = (row["company_id"], row["slot_label"], row["url"], row["local_path"])
        if row["availability"] == "available" and fingerprint in source_fingerprints:
            raise ValidationError(f"{where}: duplicate material in the same company/slot")
        source_fingerprints.add(fingerprint)
        if row["source_scope"] == "quarterly" and universe[row["company_id"]]["enabled"] == "yes":
            slots = quarterly_slots[row["company_id"]]
            slots.add(row["slot_label"])
    for company_id, slots in quarterly_slots.items():
        if len(slots) != 4:
            raise ValidationError(f"sources: enabled {company_id} has {len(slots)} quarterly slots, expected 4")

    for row in tables["themes.csv"]:
        where = f"themes:{row['theme_id']}"
        for field, enum_name in (("theme_type", "theme_type"), ("affected_dimension", "affected_dimension"), ("bottleneck_status", "bottleneck_status"), ("mapping_track", "mapping_track")):
            _enum(row, field, enum_name, where)
        for field in ("feasibility", "scarcity", "substitutability"):
            _enum(row, field, "evidence_state", where)
        if row["parent_theme_id"] and row["parent_theme_id"] not in themes:
            raise ValidationError(f"{where}: unknown parent_theme_id")
        _validate_mapping(row, where, cell_ids, route_ids)
        if row["theme_type"] == "limited_demand":
            required = ("application_demand", "required_metric", "critical_node", "limiting_factor", "constrained_outcome", "candidate_solution", "progress_gap")
            if any(not row[field] for field in required):
                raise ValidationError(f"{where}: incomplete limited-demand causal chain")

    for row in tables["claims.csv"]:
        where = f"claims:{row['claim_id']}"
        if row["source_id"] not in sources:
            raise ValidationError(f"{where}: unknown source_id")
        if row["theme_id"] not in themes:
            raise ValidationError(f"{where}: unknown theme_id")
        for field, enum_name in (("speaker_role", "speaker_role"), ("statement_type", "statement_type"), ("event_type", "event_type"), ("side", "side"), ("review_status", "review_status"), ("mapping_track", "mapping_track")):
            _enum(row, field, enum_name, where)
        if row["speaker_role"] == "analyst" and row["statement_type"] != "analyst_question":
            raise ValidationError(f"{where}: analyst speech cannot be a management fact/forecast")
        if row["statement_type"] == "analyst_question" and row["speaker_role"] != "analyst":
            raise ValidationError(f"{where}: analyst_question requires analyst role")
        if row["speaker_role"] == "corporate_author" and row["statement_type"] not in {"technical_claim", "technical_demo"}:
            raise ValidationError(f"{where}: corporate_author requires a technical claim/demo")
        if row["statement_type"] in {"technical_claim", "technical_demo"} and row["speaker_role"] != "corporate_author":
            raise ValidationError(f"{where}: technical claim/demo requires corporate_author role")
        if row["statement_type"] == "technical_demo" and row["event_type"] != "demonstrated":
            raise ValidationError(f"{where}: technical_demo requires demonstrated event")
        if row["review_status"] == "reviewed":
            if sources[row["source_id"]]["availability"] != "available":
                raise ValidationError(f"{where}: reviewed claim points to unavailable source")
            if not row["quote"] or not row["anchor"]:
                raise ValidationError(f"{where}: reviewed claim lacks quote/anchor")
        _validate_mapping(row, where, cell_ids, route_ids)

    for row in constraint_requirements.values():
        where = f"constraint_requirements:{row['requirement_id']}"
        if not row["requirement_id"].startswith("CRQ"):
            raise ValidationError(f"{where}: requirement_id must start with CRQ")
        if row["theme_id"] not in themes:
            raise ValidationError(f"{where}: unknown theme_id")
        if not row["cell_id"]:
            raise ValidationError(f"{where}: canonical requirement lacks cell_id")
        if row["cell_id"] not in cell_ids:
            raise ValidationError(f"{where}: unknown cell_id")
        if row["route_item_id"] and row["route_item_id"] not in route_ids:
            raise ValidationError(f"{where}: unknown route_item_id")
        _enum(row, "dimension", "affected_dimension", where)
        if not row["metric_name"].strip():
            raise ValidationError(f"{where}: metric_name required")
        triple = (row["comparator"].strip(), row["target_value"].strip(), row["unit"].strip())
        if not (all(triple) or not any(triple)):
            raise ValidationError(f"{where}: comparator/target_value/unit must be all empty or all non-empty")
        if any(triple):
            if row["comparator"] not in SUPPORTED_COMPARATORS:
                raise ValidationError(f"{where}: unsupported comparator {row['comparator']!r}")
            try:
                float(row["target_value"])
            except ValueError:
                raise ValidationError(f"{where}: target_value must be numeric")
        _enum(row, "review_status", "review_status", where)
        claim_ids = [item.strip() for item in row["evidence_claim_ids"].split(";") if item.strip()]
        if not claim_ids:
            raise ValidationError(f"{where}: evidence_claim_ids cannot be empty")
        for claim_id in claim_ids:
            claim = claims.get(claim_id)
            if not claim:
                raise ValidationError(f"{where}: unknown claim {claim_id}")
            if claim["review_status"] != "reviewed" or claim["speaker_role"] != "management" or claim["statement_type"] == "analyst_question":
                raise ValidationError(f"{where}: requirement evidence must be a reviewed management claim")
            if claim["theme_id"] != row["theme_id"] or claim["cell_id"] != row["cell_id"]:
                raise ValidationError(f"{where}: requirement evidence claim {claim_id} must share requirement theme_id/cell_id")

    for row in point_metrics.values():
        where = f"point_metrics:{row['metric_id']}"
        if not row["metric_id"].startswith("PM"):
            raise ValidationError(f"{where}: metric_id must start with PM")
        if row["point_id"] not in point_ids:
            raise ValidationError(f"{where}: unknown point_id")
        if not row["metric_name"].strip():
            raise ValidationError(f"{where}: metric_name required")
        _enum(row, "review_status", "review_status", where)
        if not row["value"].strip() or not row["unit"].strip() or not row["as_of"].strip():
            raise ValidationError(f"{where}: value requires unit and as_of on a metric data row")
        try:
            float(row["value"])
        except ValueError:
            raise ValidationError(f"{where}: value must be numeric")
        point = points_by_id[row["point_id"]]
        if not point["锚点URL"].strip():
            raise ValidationError(f"{where}: point {row['point_id']} lacks anchor; metric value unsupported")
        if row["value"].strip() not in point["命中引语"]:
            raise ValidationError(f"{where}: metric value {row['value']!r} not found verbatim in point {row['point_id']} quote")

    for row in tables["validations.csv"]:
        where = f"validations:{row['validation_id']}"
        if row["theme_id"] not in themes:
            raise ValidationError(f"{where}: unknown theme_id")
        if row["claim_a_id"] not in claims or row["claim_b_id"] not in claims:
            raise ValidationError(f"{where}: broken claim reference")
        if row["claim_a_id"] == row["claim_b_id"]:
            raise ValidationError(f"{where}: validation must compare two claims")
        _enum(row, "relationship", "relationship", where)
        _enum(row, "result_status", "evidence_state", where)
        claim_a = claims[row["claim_a_id"]]
        claim_b = claims[row["claim_b_id"]]
        for compared in (claim_a, claim_b):
            if compared["review_status"] != "reviewed" or compared["speaker_role"] != "management" or compared["statement_type"] == "analyst_question":
                raise ValidationError(f"{where}: validations require reviewed management claims")
        if claim_a["theme_id"] != row["theme_id"] or claim_b["theme_id"] != row["theme_id"]:
            raise ValidationError(f"{where}: compared claims must belong to validation theme")
        if row["relationship"] in {"supports", "contradicts", "independent"}:
            if claim_a["source_id"] == claim_b["source_id"]:
                raise ValidationError(f"{where}: cross-check relationship requires distinct sources")
            company_a = sources[claim_a["source_id"]]["company_id"]
            company_b = sources[claim_b["source_id"]]["company_id"]
            if company_a == company_b:
                raise ValidationError(f"{where}: cross-check relationship requires distinct companies")
        if row["relationship"] == "same_source" and claim_a["source_id"] != claim_b["source_id"]:
            raise ValidationError(f"{where}: same_source relationship requires one source")

    for row in tables["commitments.csv"]:
        where = f"commitments:{row['commitment_id']}"
        claim = claims.get(row["claim_id"])
        if not claim or claim["statement_type"] != "forward_looking" or claim["review_status"] != "reviewed" or claim["speaker_role"] != "management":
            raise ValidationError(f"{where}: commitment must reference a reviewed management forward-looking claim")
        _enum(row, "status", "commitment_status", where)
        if row["status"] not in {"pending", "not_observed"}:
            evidence = sources.get(row["evidence_source_id"])
            if not evidence or evidence["availability"] != "available":
                raise ValidationError(f"{where}: resolved status lacks available evidence source")
            if not row["evidence_claim_id"] or row["evidence_claim_id"] not in claims:
                raise ValidationError(f"{where}: resolved status lacks evidence claim")
            if claims[row["evidence_claim_id"]]["source_id"] != row["evidence_source_id"]:
                raise ValidationError(f"{where}: evidence claim/source mismatch")
            evidence_claim = claims[row["evidence_claim_id"]]
            if evidence_claim["review_status"] != "reviewed" or evidence_claim["speaker_role"] != "management" or evidence_claim["statement_type"] != "fact":
                raise ValidationError(f"{where}: fulfillment evidence must be a reviewed management fact")

    for row in tables["solution_links.csv"]:
        where = f"solution_links:{row['link_id']}"
        if row["bottleneck_theme_id"] not in themes or themes[row["bottleneck_theme_id"]]["theme_type"] != "bottleneck":
            raise ValidationError(f"{where}: invalid bottleneck theme")
        if row["solution_theme_id"] not in themes or themes[row["solution_theme_id"]]["theme_type"] != "solution":
            raise ValidationError(f"{where}: invalid solution theme")
        if themes[row["solution_theme_id"]]["parent_theme_id"] != row["bottleneck_theme_id"]:
            raise ValidationError(f"{where}: solution theme is not a child of bottleneck theme")
        if row["point_id"] and row["point_id"] not in point_ids:
            raise ValidationError(f"{where}: unknown canonical point_id {row['point_id']}")
        _enum(row, "match_stage", "match_stage", where)
        _enum(row, "evidence_status", "evidence_state", where)
        if row["match_stage"] in {"node_overlap", "mechanism_match"} and not row["missing_evidence"]:
            raise ValidationError(f"{where}: early-stage match must state missing evidence")

    frozen_by_id = {row["link_id"]: row for row in FROZEN_SOLUTION_LINKS}
    current_links = tables["solution_links.csv"]
    if [row["link_id"] for row in current_links] != ["SL001", "SL002"]:
        raise ValidationError("solution_links.csv: legacy rows frozen at exactly SL001/SL002; adding, removing or reordering is rejected")
    for row in current_links:
        frozen = frozen_by_id.get(row["link_id"])
        if frozen is None:
            raise ValidationError(f"solution_links:{row['link_id']}: unknown legacy link; only SL001/SL002 are allowed")
        for field in FILES["solution_links.csv"]:
            if row[field] != frozen[field]:
                raise ValidationError(f"solution_links:{row['link_id']}: frozen field {field!r} changed; legacy rows are byte-exact frozen")

    for row in tables["technology_feedback.csv"]:
        where = f"technology_feedback:{row['feedback_id']}"
        _enum(row, "feedback_status", "feedback_status", where)
        _enum(row, "evidence_status", "evidence_state", where)
        technology_claim = claims.get(row["technology_claim_id"])
        if not technology_claim:
            raise ValidationError(f"{where}: broken technology claim reference")
        if technology_claim["review_status"] != "reviewed" or technology_claim["speaker_role"] != "corporate_author" or technology_claim["statement_type"] not in {"technical_claim", "technical_demo"}:
            raise ValidationError(f"{where}: technology claim must be reviewed corporate_author evidence")
        if row["theme_id"] not in themes or technology_claim["theme_id"] != row["theme_id"]:
            raise ValidationError(f"{where}: technology claim and feedback must share one theme")
        commercial_id = row["commercial_claim_id"]
        commercial_claim = claims.get(commercial_id) if commercial_id else None
        if commercial_id and not commercial_claim:
            raise ValidationError(f"{where}: broken commercial claim reference")
        if row["feedback_status"] in {"confirmed", "partially_confirmed", "contradicted"} and not commercial_claim:
            raise ValidationError(f"{where}: asserted feedback status requires commercial claim")
        if commercial_claim:
            if commercial_claim["review_status"] != "reviewed" or commercial_claim["speaker_role"] != "management" or commercial_claim["statement_type"] not in {"fact", "forward_looking"}:
                raise ValidationError(f"{where}: commercial claim must be reviewed management evidence")
            if commercial_claim["theme_id"] != row["theme_id"]:
                raise ValidationError(f"{where}: technology and commercial claims must share one theme")
        if row["feedback_status"] in {"confirmed", "partially_confirmed", "contradicted"} and commercial_claim and commercial_claim["statement_type"] != "fact":
            raise ValidationError(f"{where}: asserted feedback requires a reviewed management fact")
        if row["feedback_status"] == "not_mentioned" and commercial_id:
            raise ValidationError(f"{where}: not_mentioned cannot imply commercial confirmation")
        if row["feedback_status"] == "confirmed" and row["evidence_status"] != "verified":
            raise ValidationError(f"{where}: confirmed feedback requires verified evidence")

    from .workbuddy import render_all_positioning_blocks
    projection = derive_positioning(load_positioning_facts(project_root))
    json_text = json.dumps(projection, ensure_ascii=False, sort_keys=True)
    hits = sorted(set(scan_forbidden_words(json_text)))
    if hits:
        raise ValidationError(f"positioning derived fields contain forbidden business words: {hits}")
    theme_ids = [row["theme_id"] for row in tables["themes.csv"]]
    hits = sorted(set(scan_forbidden_words(render_all_positioning_blocks(projection, theme_ids))))
    if hits:
        raise ValidationError(f"workbuddy positioning block contains forbidden business words: {hits}")

    try:
        event_projection = derive_event_projection(load_event_facts(project_root))
    except EventLedgerError as exc:
        raise ValidationError(f"event ledger: {exc}") from exc

    return [
        f"validated {len(universe)} companies / {len(sources)} sources / {len(claims)} claims",
        f"validated {len(themes)} themes / {len(tables['validations.csv'])} cross-checks / {len(tables['commitments.csv'])} commitments / {len(tables['technology_feedback.csv'])} technology feedback rows",
        f"event ledger validated / {len(event_projection['radar_events'])} reviewed radar events; canonical references are closed; no canonical file was written",
    ]


def _validate_mapping(row: dict[str, str], where: str, cell_ids: set[str], route_ids: set[str]) -> None:
    if row["mapping_track"] == "canonical":
        if not (row["cell_id"] or row["route_item_id"]):
            raise ValidationError(f"{where}: canonical mapping lacks cell_id/route_item_id")
        if row["cell_id"] and row["cell_id"] not in cell_ids:
            raise ValidationError(f"{where}: unknown cell_id {row['cell_id']}")
        if row["route_item_id"] and row["route_item_id"] not in route_ids:
            raise ValidationError(f"{where}: unknown route_item_id {row['route_item_id']}")
        if row.get("unmapped_theme") or row.get("unmapped_reason"):
            raise ValidationError(f"{where}: canonical mapping contains unmapped fields")
    else:
        theme = row.get("unmapped_theme", row.get("theme_name", ""))
        if not theme or not row["unmapped_reason"]:
            raise ValidationError(f"{where}: unmapped track needs a theme and reason")
        if row["cell_id"] or row["route_item_id"]:
            raise ValidationError(f"{where}: unmapped track cannot set canonical ids")


def _read_any_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))
