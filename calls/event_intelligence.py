"""Evidence-gated overseas company event ledger.

The public seam is intentionally small: callers load validated facts once and
derive every reader-facing view from the same deterministic projection.  This
module never reads or writes canonical industry-chain tables or shipments.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .schema import ENUMS, FILES


class EventLedgerError(ValueError):
    """Raised when the event ledger violates its data contract."""


EVENT_FILES = (
    "watch_entities.csv",
    "company_candidates.csv",
    "company_tier_reviews.csv",
    "entity_relationships.csv",
    "disclosures.csv",
    "event_claims.csv",
    "events.csv",
    "event_evidence.csv",
)
MATURE_COMMERCIAL_STAGES = frozenset({
    "volume_order", "first_shipment", "ramping", "scaled",
})
INDEPENDENT_CLASSES = frozenset({
    "counterparty", "regulator", "observable_result",
})


def _read_csv(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected:
            raise EventLedgerError(
                f"{path.name}: header mismatch; expected {expected}"
            )
        return list(reader)


def _index(rows: list[dict[str, str]], field: str, filename: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for line, row in enumerate(rows, 2):
        value = row[field].strip()
        if not value:
            raise EventLedgerError(f"{filename}:{line}: empty {field}")
        if value in result:
            raise EventLedgerError(f"{filename}:{line}: duplicate {field} {value}")
        result[value] = row
    return result


def _enum(row: dict[str, str], field: str, enum_name: str, where: str) -> None:
    if row[field] not in ENUMS[enum_name]:
        raise EventLedgerError(f"{where}: invalid {field}={row[field]!r}")


def _split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _date(value: str, field: str, where: str) -> None:
    if not value:
        return
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise EventLedgerError(f"{where}: invalid {field}={value!r}") from exc


def _url_ok(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_event_facts(root: Path) -> dict:
    """Load and validate event-ledger facts behind one stable interface."""
    calls_dir = root / "calls"
    rows = {
        name: _read_csv(calls_dir / name, FILES[name])
        for name in EVENT_FILES
    }
    universe_rows = _read_csv(calls_dir / "universe.csv", FILES["universe.csv"])
    source_rows = _read_csv(calls_dir / "sources.csv", FILES["sources.csv"])
    claim_rows = _read_csv(calls_dir / "claims.csv", FILES["claims.csv"])
    theme_rows = _read_csv(calls_dir / "themes.csv", FILES["themes.csv"])

    universe = _index(universe_rows, "company_id", "universe.csv")
    watch = _index(rows["watch_entities.csv"], "entity_id", "watch_entities.csv")
    candidates = _index(
        rows["company_candidates.csv"], "candidate_id", "company_candidates.csv"
    )
    tier_reviews = _index(
        rows["company_tier_reviews.csv"], "review_id", "company_tier_reviews.csv"
    )
    relationships = _index(
        rows["entity_relationships.csv"],
        "relationship_id",
        "entity_relationships.csv",
    )
    sources = _index(source_rows, "source_id", "sources.csv")
    legacy_claims = _index(claim_rows, "claim_id", "claims.csv")
    themes = _index(theme_rows, "theme_id", "themes.csv")
    disclosures = _index(rows["disclosures.csv"], "disclosure_id", "disclosures.csv")
    event_claims = _index(rows["event_claims.csv"], "event_claim_id", "event_claims.csv")
    events = _index(rows["events.csv"], "event_id", "events.csv")
    evidence = _index(rows["event_evidence.csv"], "evidence_id", "event_evidence.csv")

    overlap = set(universe) & set(watch)
    if overlap:
        raise EventLedgerError(
            f"watch_entities.csv: entity_id collides with universe company_id: {sorted(overlap)}"
        )

    entities = dict(universe)
    for entity_id, row in watch.items():
        where = f"watch_entities:{entity_id}"
        _enum(row, "entity_type", "entity_type", where)
        _enum(row, "monitoring_status", "monitoring_status", where)
        promoted = row["promoted_company_id"]
        if row["monitoring_status"] == "promoted":
            if not promoted or promoted not in universe:
                raise EventLedgerError(f"{where}: promoted entity needs known promoted_company_id")
            continue
        if promoted:
            raise EventLedgerError(f"{where}: only promoted entities may set promoted_company_id")
        entities[entity_id] = row

    identity_entities = {**universe, **watch}
    candidate_overlap = set(candidates) & set(identity_entities)
    if candidate_overlap:
        raise EventLedgerError(
            "company_candidates.csv: candidate_id collides with tracked entity: "
            f"{sorted(candidate_overlap)}"
        )
    tier_reviews_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_review_periods: set[tuple[str, str]] = set()
    for review_id, row in tier_reviews.items():
        where = f"company_tier_reviews:{review_id}"
        candidate_id = row["candidate_id"]
        if candidate_id not in candidates:
            raise EventLedgerError(f"{where}: unknown candidate_id")
        if not row["period_label"]:
            raise EventLedgerError(f"{where}: period_label is required")
        period_key = (candidate_id, row["period_label"])
        if period_key in seen_review_periods:
            raise EventLedgerError(f"{where}: duplicate candidate period review")
        seen_review_periods.add(period_key)
        for field in ("published_date", "reviewed_at"):
            _date(row[field], field, where)
        if not row["published_date"] or not row["reviewed_at"]:
            raise EventLedgerError(f"{where}: published_date and reviewed_at are required")
        if not _url_ok(row["source_ref"]):
            raise EventLedgerError(f"{where}: invalid source_ref")
        _enum(row, "material_type", "material_type", where)
        if row["material_type"] in {"unknown", "official_technical_blog"}:
            raise EventLedgerError(f"{where}: tier review requires formal disclosure material")
        _enum(row, "signal_class", "tier_review_signal_class", where)
        if not row["signal_summary"]:
            raise EventLedgerError(f"{where}: signal_summary is required")
        tier_reviews_by_candidate[candidate_id].append(row)

    for candidate_id, row in candidates.items():
        where = f"company_candidates:{candidate_id}"
        for field, enum_name in (
            ("entity_type", "entity_type"),
            ("suggested_role", "role"),
            ("suggested_tier", "suggested_tier"),
            ("priority", "candidate_priority"),
            ("verification_status", "candidate_verification_status"),
        ):
            _enum(row, field, enum_name, where)
        _date(row["reviewed_at"], "reviewed_at", where)
        if row["source_ref"] and not _url_ok(row["source_ref"]):
            raise EventLedgerError(f"{where}: invalid source_ref")
        if row["verification_status"] in {
            "source_verified", "promotion_ready", "promoted",
        } and not (row["source_ref"] and row["reviewed_at"]):
            raise EventLedgerError(
                f"{where}: verified candidate needs source_ref and reviewed_at"
            )
        if row["verification_status"] == "promoted":
            if row["promoted_entity_id"] not in identity_entities:
                raise EventLedgerError(
                    f"{where}: promoted candidate needs known promoted_entity_id"
                )
        elif row["promoted_entity_id"]:
            raise EventLedgerError(
                f"{where}: only promoted candidate may set promoted_entity_id"
            )
        if (
            row["suggested_tier"] == "quarterly"
            and row["verification_status"] in {"promotion_ready", "promoted"}
        ):
            reviews = tier_reviews_by_candidate.get(candidate_id, [])
            if len(reviews) < 2:
                raise EventLedgerError(
                    f"{where}: quarterly promotion needs two formal tier reviews"
                )
            if all(item["signal_class"] == "no_relevant_signal" for item in reviews):
                raise EventLedgerError(
                    f"{where}: quarterly promotion lacks optical or adjacent signal"
                )

    for relationship_id, row in relationships.items():
        where = f"entity_relationships:{relationship_id}"
        _enum(row, "relationship_type", "entity_relationship_type", where)
        _enum(
            row,
            "review_status",
            "entity_relationship_review_status",
            where,
        )
        subject_id = row["subject_entity_id"]
        object_id = row["object_entity_id"]
        if subject_id not in identity_entities or object_id not in identity_entities:
            raise EventLedgerError(f"{where}: unknown relationship endpoint")
        if subject_id == object_id:
            raise EventLedgerError(f"{where}: self relationship is not allowed")
        for field in ("effective_from", "effective_to"):
            _date(row[field], field, where)
        if (
            row["effective_from"]
            and row["effective_to"]
            and row["effective_from"] > row["effective_to"]
        ):
            raise EventLedgerError(f"{where}: effective_from is after effective_to")
        if row["source_ref"] and not _url_ok(row["source_ref"]):
            raise EventLedgerError(f"{where}: invalid source_ref")
        if row["review_status"] == "reviewed" and not row["source_ref"]:
            raise EventLedgerError(f"{where}: reviewed relationship needs source_ref")

    for disclosure_id, row in disclosures.items():
        where = f"disclosures:{disclosure_id}"
        if row["publisher_entity_id"] not in entities:
            raise EventLedgerError(f"{where}: unknown publisher_entity_id")
        for field, enum_name in (
            ("disclosure_type", "disclosure_type"),
            ("content_class", "content_class"),
            ("provenance_class", "provenance_class"),
            ("retrieval_status", "retrieval_status"),
            ("processing_status", "processing_status"),
        ):
            _enum(row, field, enum_name, where)
        for field in ("published_at", "updated_at", "discovered_at", "retrieved_at", "reviewed_at"):
            _date(row[field], field, where)
        if row["canonical_url"] and not _url_ok(row["canonical_url"]):
            raise EventLedgerError(f"{where}: invalid canonical_url")
        if not row["origin_group"]:
            raise EventLedgerError(f"{where}: origin_group is required for deduplication")
        if row["local_path"] and not (calls_dir / row["local_path"]).is_file():
            raise EventLedgerError(f"{where}: local_path does not exist")
        if row["retrieval_status"] == "retrieved":
            if not row["retrieved_at"] or not (row["canonical_url"] or row["local_path"]):
                raise EventLedgerError(f"{where}: retrieved disclosure lacks retrieval time or anchor")
        if row["processing_status"] in {"anchor_reviewed", "no_relevant_claims"}:
            if not row["reviewed_at"] or not row["review_scope"]:
                raise EventLedgerError(f"{where}: reviewed processing state lacks reviewed_at/review_scope")
        legacy_source_id = row["legacy_source_id"]
        if legacy_source_id:
            source = sources.get(legacy_source_id)
            if not source:
                raise EventLedgerError(f"{where}: unknown legacy_source_id")
            if source["company_id"] != row["publisher_entity_id"]:
                raise EventLedgerError(f"{where}: legacy source publisher mismatch")

    for event_claim_id, row in event_claims.items():
        where = f"event_claims:{event_claim_id}"
        disclosure = disclosures.get(row["disclosure_id"])
        if not disclosure:
            raise EventLedgerError(f"{where}: unknown disclosure_id")
        if row["claimant_entity_id"] not in entities:
            raise EventLedgerError(f"{where}: unknown claimant_entity_id")
        for field, enum_name in (
            ("claimant_role", "event_claimant_role"),
            ("statement_kind", "event_statement_kind"),
            ("review_status", "event_review_status"),
        ):
            _enum(row, field, enum_name, where)
        _date(row["reviewed_at"], "reviewed_at", where)
        if row["review_status"] == "anchor_reviewed":
            if not row["quote"] or not row["anchor"] or not row["reviewed_at"]:
                raise EventLedgerError(f"{where}: anchor-reviewed claim lacks quote/anchor/reviewed_at")
            if disclosure["processing_status"] != "anchor_reviewed":
                raise EventLedgerError(f"{where}: reviewed claim requires anchor-reviewed disclosure")
        legacy_claim_id = row["legacy_claim_id"]
        if legacy_claim_id:
            legacy = legacy_claims.get(legacy_claim_id)
            if not legacy:
                raise EventLedgerError(f"{where}: unknown legacy_claim_id")
            if legacy["source_id"] != disclosure["legacy_source_id"]:
                raise EventLedgerError(f"{where}: legacy claim/source mismatch")
            if legacy["review_status"] == "reviewed" and row["review_status"] != "anchor_reviewed":
                raise EventLedgerError(f"{where}: reviewed legacy claim must map to anchor_reviewed")

    for event_id, row in events.items():
        where = f"events:{event_id}"
        for field, enum_name in (
            ("event_category", "event_category"),
            ("lifecycle_stage", "lifecycle_stage"),
            ("event_status", "event_status"),
            ("date_precision", "date_precision"),
        ):
            _enum(row, field, enum_name, where)
        if row["primary_subject_id"] not in entities:
            raise EventLedgerError(f"{where}: unknown primary_subject_id")
        for entity_id in _split_ids(row["counterparty_ids"]):
            if entity_id not in entities:
                raise EventLedgerError(f"{where}: unknown counterparty_id {entity_id}")
        for theme_id in _split_ids(row["theme_ids"]):
            if theme_id not in themes:
                raise EventLedgerError(f"{where}: unknown theme_id {theme_id}")
        for field in ("occurred_start", "occurred_end"):
            _date(row[field], field, where)
        if row["occurred_start"] and row["occurred_end"] and row["occurred_start"] > row["occurred_end"]:
            raise EventLedgerError(f"{where}: occurred_start is after occurred_end")
        previous_id = row["previous_event_id"]
        if previous_id:
            previous = events.get(previous_id)
            if not previous:
                raise EventLedgerError(f"{where}: unknown previous_event_id")
            if previous_id == event_id or previous["program_id"] != row["program_id"]:
                raise EventLedgerError(f"{where}: previous event must be distinct and in same program")

    for event_id in events:
        seen: set[str] = set()
        current_id = event_id
        while current_id:
            if current_id in seen:
                raise EventLedgerError(f"events:{event_id}: previous_event_id cycle detected")
            seen.add(current_id)
            current_id = events[current_id]["previous_event_id"]

    evidence_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    for evidence_id, row in evidence.items():
        where = f"event_evidence:{evidence_id}"
        event = events.get(row["event_id"])
        claim = event_claims.get(row["event_claim_id"])
        if not event or not claim:
            raise EventLedgerError(f"{where}: broken event/claim reference")
        _enum(row, "relationship", "event_relationship", where)
        _enum(row, "independence_class", "independence_class", where)
        disclosure = disclosures[claim["disclosure_id"]]
        if row["origin_group"] != disclosure["origin_group"]:
            raise EventLedgerError(f"{where}: origin_group differs from disclosure")
        provenance = disclosure["provenance_class"]
        expected_provenance = {
            "first_party": {"first_party"},
            "counterparty": {"counterparty"},
            "regulator": {"regulator", "government"},
            "third_party": {"third_party"},
            "observable_result": {"counterparty", "regulator", "government", "third_party"},
        }.get(row["independence_class"])
        if expected_provenance is not None and provenance not in expected_provenance:
            raise EventLedgerError(
                f"{where}: independence_class conflicts with disclosure provenance"
            )
        evidence_by_event[event["event_id"]].append(row)

    for event_id, event in events.items():
        where = f"events:{event_id}"
        event_links = evidence_by_event.get(event_id, [])
        reviewed_links = [
            link for link in event_links
            if event_claims[link["event_claim_id"]]["review_status"] == "anchor_reviewed"
        ]
        if not reviewed_links:
            # Candidate events remain legal but are excluded from the radar.
            continue
        if event["lifecycle_stage"] in MATURE_COMMERCIAL_STAGES:
            supporting_claims = [
                event_claims[link["event_claim_id"]]
                for link in reviewed_links
                if link["relationship"] in {"reports", "supports"}
            ]
            supporting_disclosures = [
                disclosures[claim["disclosure_id"]]
                for claim in supporting_claims
            ]
            if event["event_status"] in {"asserted", "corroborated"} and not supporting_disclosures:
                raise EventLedgerError(f"{where}: mature commercial stage lacks supporting report")
            if supporting_claims and all(
                claim["statement_kind"] == "forward_looking"
                for claim in supporting_claims
            ):
                raise EventLedgerError(
                    f"{where}: forward-looking claims alone cannot support mature commercial stage"
                )
            if supporting_disclosures and all(item["disclosure_type"] == "technical_blog" for item in supporting_disclosures):
                raise EventLedgerError(f"{where}: technical blog alone cannot support mature commercial stage")
        if event["event_status"] == "corroborated":
            first_party_origins = {
                link["origin_group"] for link in reviewed_links
                if link["independence_class"] in {"first_party", "same_origin"}
                and link["relationship"] in {"reports", "supports"}
            }
            independent = {
                link["origin_group"] for link in reviewed_links
                if link["relationship"] in {"reports", "supports"}
                and link["independence_class"] in INDEPENDENT_CLASSES
                and link["origin_group"] not in first_party_origins
            }
            if not first_party_origins:
                raise EventLedgerError(f"{where}: corroborated event lacks first-party asserted origin")
            if not independent:
                raise EventLedgerError(f"{where}: corroborated event lacks independent supporting origin")

    return {
        "entities": entities,
        "universe": universe,
        "watch_entities": watch,
        "company_candidates": candidates,
        "company_tier_reviews": tier_reviews,
        "entity_relationships": relationships,
        "sources": sources,
        "disclosures": disclosures,
        "event_claims": event_claims,
        "events": events,
        "evidence": evidence,
        "themes": themes,
    }


def derive_event_projection(facts: dict) -> dict:
    """Derive deterministic radar, timeline, theme, queue and coverage views."""
    disclosures = facts["disclosures"]
    claims = facts["event_claims"]
    events = facts["events"]
    evidence = facts["evidence"]
    universe = facts["universe"]
    watch = facts["watch_entities"]
    candidates = facts["company_candidates"]
    tier_reviews = facts["company_tier_reviews"]
    relationships = facts["entity_relationships"]
    sources = facts["sources"]

    evidence_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence.values():
        evidence_by_event[row["event_id"]].append(row)

    radar: list[dict] = []
    queue: list[dict] = []
    for event_id in sorted(events):
        event = events[event_id]
        links = sorted(evidence_by_event.get(event_id, []), key=lambda row: row["evidence_id"])
        unique_links: list[dict[str, str]] = []
        seen_origins: set[str] = set()
        for link in links:
            if link["origin_group"] in seen_origins:
                continue
            seen_origins.add(link["origin_group"])
            unique_links.append(link)
        reviewed = [
            link for link in unique_links
            if claims[link["event_claim_id"]]["review_status"] == "anchor_reviewed"
        ]
        if not reviewed:
            queue.append({
                "queue_type": "event_pending_anchor_review",
                "event_id": event_id,
                "summary": event["summary"],
            })
            continue

        evidence_rows = []
        for link in reviewed:
            claim = claims[link["event_claim_id"]]
            disclosure = disclosures[claim["disclosure_id"]]
            evidence_rows.append({
                "evidence_id": link["evidence_id"],
                "event_claim_id": claim["event_claim_id"],
                "relationship": link["relationship"],
                "independence_class": link["independence_class"],
                "origin_group": link["origin_group"],
                "statement_kind": claim["statement_kind"],
                "quote": claim["quote"],
                "anchor": claim["anchor"],
                "claim_reviewed_at": claim["reviewed_at"],
                "disclosure_id": disclosure["disclosure_id"],
                "title": disclosure["title"],
                "url": disclosure["canonical_url"],
                "disclosure_type": disclosure["disclosure_type"],
                "content_class": disclosure["content_class"],
                "provenance_class": disclosure["provenance_class"],
                "published_at": disclosure["published_at"],
                "retrieved_at": disclosure["retrieved_at"],
                "disclosure_reviewed_at": disclosure["reviewed_at"],
            })
        row = {
            "event_id": event_id,
            "program_id": event["program_id"],
            "event_category": event["event_category"],
            "lifecycle_stage": event["lifecycle_stage"],
            "event_status": event["event_status"],
            "primary_subject_id": event["primary_subject_id"],
            "counterparty_ids": _split_ids(event["counterparty_ids"]),
            "theme_ids": _split_ids(event["theme_ids"]),
            "occurred_start": event["occurred_start"],
            "occurred_end": event["occurred_end"],
            "date_precision": event["date_precision"],
            "previous_event_id": event["previous_event_id"],
            "summary": event["summary"],
            "evidence": evidence_rows,
        }
        radar.append(row)

    for disclosure_id in sorted(disclosures):
        disclosure = disclosures[disclosure_id]
        if disclosure["processing_status"] in {"unprocessed", "candidate_extracted"}:
            queue.append({
                "queue_type": "disclosure_processing",
                "disclosure_id": disclosure_id,
                "processing_status": disclosure["processing_status"],
                "title": disclosure["title"],
            })

    for candidate_id in sorted(candidates):
        candidate = candidates[candidate_id]
        if candidate["verification_status"] != "promoted":
            queue.append({
                "queue_type": "company_candidate_review",
                "candidate_id": candidate_id,
                "entity_name": candidate["entity_name"],
                "verification_status": candidate["verification_status"],
                "suggested_tier": candidate["suggested_tier"],
                "priority": candidate["priority"],
                "source_ref": candidate["source_ref"],
            })

    timelines: dict[str, list[dict]] = defaultdict(list)
    theme_impacts: dict[str, list[dict]] = defaultdict(list)
    for row in radar:
        timelines[row["primary_subject_id"]].append(row)
        for theme_id in row["theme_ids"]:
            theme_impacts[theme_id].append(row)
    timeline_rows = [
        {"primary_subject_id": entity_id, "events": sorted(items, key=lambda item: (item["occurred_start"], item["event_id"]))}
        for entity_id, items in sorted(timelines.items())
    ]
    theme_rows = [
        {"theme_id": theme_id, "events": sorted(items, key=lambda item: (item["occurred_start"], item["event_id"]))}
        for theme_id, items in sorted(theme_impacts.items())
    ]

    status_counts: dict[str, int] = defaultdict(int)
    for row in disclosures.values():
        status_counts[row["processing_status"]] += 1
    published = [row["published_at"] for row in disclosures.values() if row["published_at"]]
    retrieved = [row["retrieved_at"] for row in disclosures.values() if row["retrieved_at"]]
    reviewed = [row["reviewed_at"] for row in disclosures.values() if row["reviewed_at"]]
    coverage = {
        "disclosure_count": len(disclosures),
        "processing_status_counts": dict(sorted(status_counts.items())),
        "latest_disclosure_at": max(published) if published else "",
        "latest_retrieved_at": max(retrieved) if retrieved else "",
        "latest_reviewed_at": max(reviewed) if reviewed else "",
    }
    enabled_company_ids = {
        company_id
        for company_id, row in universe.items()
        if row["enabled"] == "yes"
    }
    quarterly_slots: dict[str, set[str]] = defaultdict(set)
    available_slots: dict[str, set[str]] = defaultdict(set)
    for source in sources.values():
        company_id = source["company_id"]
        if company_id not in enabled_company_ids or source["source_scope"] != "quarterly":
            continue
        quarterly_slots[company_id].add(source["slot_label"])
        if source["availability"] == "available":
            available_slots[company_id].add(source["slot_label"])
    candidate_status_counts: dict[str, int] = defaultdict(int)
    for row in candidates.values():
        candidate_status_counts[row["verification_status"]] += 1
    coverage.update({
        "quarterly_company_count": len(enabled_company_ids),
        "four_slot_complete_count": sum(
            len(quarterly_slots[company_id]) == 4
            for company_id in enabled_company_ids
        ),
        "four_available_slot_complete_count": sum(
            len(available_slots[company_id]) == 4
            for company_id in enabled_company_ids
        ),
        "active_watch_entity_count": sum(
            row["monitoring_status"] == "active" for row in watch.values()
        ),
        "candidate_status_counts": dict(sorted(candidate_status_counts.items())),
        "tier_review_count": len(tier_reviews),
        "tier_reviewed_candidate_count": len({
            row["candidate_id"] for row in tier_reviews.values()
        }),
    })
    return {
        "radar_events": radar,
        "company_timelines": timeline_rows,
        "theme_impacts": theme_rows,
        "discovery_queue": sorted(queue, key=lambda item: (
            item["queue_type"], item.get("candidate_id", ""),
            item.get("event_id", ""), item.get("disclosure_id", ""),
        )),
        "coverage_summary": coverage,
        "company_candidates": [candidates[key] for key in sorted(candidates)],
        "company_tier_reviews": [tier_reviews[key] for key in sorted(tier_reviews)],
        "entity_relationships": [relationships[key] for key in sorted(relationships)],
    }
