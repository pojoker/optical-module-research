"""Daily discovery mirror: monitoring pool, dedupe, permission guards and isolation.

The suite proves three things the contract depends on:

1. discovery produces schema-shaped *candidates* only and never an
   ``anchor_reviewed`` claim or a non-``asserted`` event status;
2. first-party material is never independent evidence, and ``corroborated``
   is only ever a suggestion that requires human approval;
3. running the mirror leaves ``calls/*.csv``, ``calls/out/`` and the root
   canonical files byte-identical.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from calls import daily_discovery as dd
from calls.schema import CANONICAL_FILES, FILES

REPO_ROOT = Path(__file__).resolve().parents[2]
CALLS_DIR = Path(__file__).resolve().parents[1]
FIXTURES = CALLS_DIR / "fixtures" / "daily_discovery"
CONFIG = CALLS_DIR / "discovery_config.json"
RUN_DATE = "2026-09-01"

CANDIDATE_FILES = (
    "disclosure_candidates.csv",
    "claim_candidates.csv",
    "event_candidates.csv",
    "evidence_candidates.csv",
    "dedupe-manifest.csv",
    "failures.csv",
    "candidates.json",
)


def _row(name: str, **values: str) -> dict[str, str]:
    row = {field: "" for field in FILES[name]}
    row.update(values)
    return row


def _write_table(path: Path, name: str, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FILES[name]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FILES[name]})


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _build_source(root: Path, disclosures=()) -> Path:
    """Small but contract-shaped read-only source root for isolated runs."""
    calls = root / "calls"
    _write_table(calls / "universe.csv", "universe.csv", [
        _row("universe.csv", company_id="AAOI", company_name="Applied Optoelectronics",
             role="core_peer", enabled="yes"),
        _row("universe.csv", company_id="LITE", company_name="Lumentum",
             role="core_peer", enabled="yes"),
        _row("universe.csv", company_id="CSCO", company_name="Cisco",
             role="downstream", enabled="yes"),
        _row("universe.csv", company_id="MTSI", company_name="MACOM",
             role="upstream_enabler", enabled="yes"),
        _row("universe.csv", company_id="POET", company_name="POET Technologies",
             role="core_peer", enabled="yes"),
        _row("universe.csv", company_id="SLEEPING", company_name="Disabled Peer",
             role="core_peer", enabled="no"),
    ])
    _write_table(calls / "watch_entities.csv", "watch_entities.csv", [
        _row("watch_entities.csv", entity_id="WATCH_IQE", entity_name="IQE plc",
             entity_type="company", aliases="IQE;IQE plc", monitoring_status="active"),
        _row("watch_entities.csv", entity_id="WATCH_OCLARO", entity_name="Oclaro Inc.",
             entity_type="company", aliases="Oclaro", monitoring_status="active"),
        _row("watch_entities.csv", entity_id="WATCH_OLD", entity_name="Retired Watch",
             entity_type="company", monitoring_status="promoted",
             promoted_company_id="LITE"),
        _row("watch_entities.csv", entity_id="WATCH_PAUSED", entity_name="Paused Watch",
             entity_type="company", monitoring_status="paused"),
    ])
    _write_table(calls / "company_candidates.csv", "company_candidates.csv", [
        _row("company_candidates.csv", candidate_id="CAND_HAMAMATSU",
             entity_name="Hamamatsu Photonics", entity_type="company",
             suggested_role="upstream_enabler", suggested_tier="watch",
             priority="P2", verification_status="source_verified"),
        _row("company_candidates.csv", candidate_id="CAND_DONE",
             entity_name="Already Promoted", entity_type="company",
             suggested_role="core_peer", suggested_tier="quarterly",
             priority="P1", verification_status="promoted",
             promoted_entity_id="AAOI"),
    ])
    _write_table(calls / "entity_relationships.csv", "entity_relationships.csv", [
        _row("entity_relationships.csv", relationship_id="REL_OCLARO_LITE",
             subject_entity_id="WATCH_OCLARO", object_entity_id="LITE",
             relationship_type="acquired_by", effective_from="2018-12-10",
             review_status="reviewed"),
        _row("entity_relationships.csv", relationship_id="REL_BRAND_CANDIDATE",
             subject_entity_id="CAND_DONE", object_entity_id="AAOI",
             relationship_type="brand_of", review_status="candidate"),
    ])
    _write_table(calls / "disclosures.csv", "disclosures.csv", list(disclosures))
    for name in ("event_claims.csv", "events.csv", "event_evidence.csv"):
        _write_table(calls / name, name, [])
    (calls / "out").mkdir(parents=True, exist_ok=True)
    (calls / "out" / "README.md").write_text("read-only render output\n", encoding="utf-8")
    return root


def _run(source: Path, state: Path, date: str = RUN_DATE) -> dict:
    return dd.run_daily_discovery(source, state, date, CONFIG, dd.FixtureFetcher(FIXTURES))


def _source_item(source: Path, text: str) -> "dd.SourceItem":
    endpoint = dd.load_discovery_config(CONFIG, dd.load_entity_registry(source))[0]
    return dd.SourceItem(
        endpoint=endpoint, url="https://example.com/statement", title="statement",
        published_at=RUN_DATE, origin_key="unit-test",
        paragraphs=(("p1", text),), disclosure_type="official_release",
        content_class="commercial_disclosure", provenance_class="first_party", note="",
    )


def _manifest_decisions(state: Path, date: str = RUN_DATE) -> dict[str, list[dict[str, str]]]:
    rows = _read_csv(state / "staging" / date / "dedupe-manifest.csv")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["decision"], []).append(row)
    return grouped


def _failure_types(state: Path, date: str = RUN_DATE) -> set[str]:
    return {row["failure_type"] for row in _read_csv(state / "staging" / date / "failures.csv")}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DailyDiscoveryTestCase(unittest.TestCase):
    """Shared temp-dir plumbing; every run writes to an isolated state root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.source = _build_source(self.tmp / "source")
        self.state = self.tmp / "state"
        self.addCleanup(self._tmp.cleanup)


class TestMonitoringPool(DailyDiscoveryTestCase):
    def test_pool_is_union_of_enabled_universe_active_watch_and_open_candidates(self) -> None:
        registry = dd.load_entity_registry(self.source)
        self.assertEqual(
            set(registry.monitored),
            {"AAOI", "LITE", "CSCO", "MTSI", "POET", "WATCH_IQE", "WATCH_OCLARO", "CAND_HAMAMATSU"},
        )
        self.assertNotIn("SLEEPING", registry.monitored)     # universe enabled=no
        self.assertNotIn("WATCH_PAUSED", registry.monitored)  # watch paused
        self.assertNotIn("WATCH_OLD", registry.monitored)     # watch promoted
        self.assertNotIn("CAND_DONE", registry.monitored)     # candidate already promoted

    def test_real_ledger_pool_excludes_promoted_rows(self) -> None:
        registry = dd.load_entity_registry(REPO_ROOT)
        self.assertIn("AAOI", registry.monitored)
        self.assertIn("WATCH_IQE", registry.monitored)
        self.assertIn("CAND_HAMAMATSU", registry.monitored)
        self.assertEqual(registry.canonical["WATCH_OCLARO"], "LITE")  # acquired_by, reviewed
        self.assertEqual(registry.canonical["WATCH_IQE"], "WATCH_IQE")  # own identity

    def test_alias_resolution_maps_brand_to_canonical_entity(self) -> None:
        registry = dd.load_entity_registry(REPO_ROOT)
        resolved, needles = registry.resolve_mentions(
            "Oclaro shipped 800G modules to a hyperscale customer this quarter."
        )
        self.assertEqual(resolved, ("LITE",))
        self.assertEqual(needles, ("oclaro",))

    def test_unrelated_text_resolves_to_nothing(self) -> None:
        registry = dd.load_entity_registry(self.source)
        self.assertEqual(registry.resolve_mentions("No tracked company appears here."), ((), ()))

    def test_candidate_relationship_is_not_used_for_identity(self) -> None:
        registry = dd.load_entity_registry(self.source)
        # brand_of is still review_status=candidate, so it must not merge identities.
        self.assertEqual(registry.canonical["CAND_DONE"], "CAND_DONE")


class TestDiscoveryConfig(DailyDiscoveryTestCase):
    def _config(self, entities: dict) -> Path:
        path = self.tmp / "config.json"
        path.write_text(
            json.dumps({"version": 1, "entities": entities}, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def _base_endpoint(self, **overrides) -> dict:
        endpoint = {
            "endpoint_id": "X_IR",
            "endpoint_kind": "official_ir",
            "url": "https://example.com/ir",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
        }
        endpoint.update(overrides)
        return endpoint

    def test_generic_news_feed_is_rejected(self) -> None:
        path = self._config({"AAOI": {"endpoints": [
            self._base_endpoint(endpoint_kind="generic_news"),
        ]}})
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "generic_news feeds are rejected"):
            dd.load_discovery_config(path, dd.load_entity_registry(self.source))

    def test_media_disclosure_type_is_rejected(self) -> None:
        path = self._config({"AAOI": {"endpoints": [
            self._base_endpoint(disclosure_type="media"),
        ]}})
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "media cannot be a discovery endpoint"):
            dd.load_discovery_config(path, dd.load_entity_registry(self.source))

    def test_entity_outside_monitoring_pool_is_rejected(self) -> None:
        path = self._config({"SLEEPING": {"endpoints": [self._base_endpoint()]}})
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "not in the monitoring pool"):
            dd.load_discovery_config(path, dd.load_entity_registry(self.source))

    def test_first_party_endpoint_cannot_declare_corroboration_targets(self) -> None:
        path = self._config({"AAOI": {"endpoints": [
            self._base_endpoint(corroborates_entity_ids=["LITE"]),
        ]}})
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "first-party endpoint cannot declare"):
            dd.load_discovery_config(path, dd.load_entity_registry(self.source))

    def test_independent_endpoint_must_declare_corroboration_targets(self) -> None:
        path = self._config({"AAOI": {"endpoints": [
            self._base_endpoint(provenance_class="counterparty"),
        ]}})
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "must declare corroborates_entity_ids"):
            dd.load_discovery_config(path, dd.load_entity_registry(self.source))

    def test_shipped_config_loads(self) -> None:
        endpoints = dd.load_discovery_config(CONFIG, dd.load_entity_registry(REPO_ROOT))
        self.assertTrue(endpoints)
        self.assertEqual({item.endpoint_kind for item in endpoints} <= set(dd.ENDPOINT_KINDS), True)


class TestDedupe(DailyDiscoveryTestCase):
    def test_url_hash_and_origin_dedupe_are_recorded(self) -> None:
        _run(self.source, self.state)
        decisions = _manifest_decisions(self.state)
        self.assertEqual(len(decisions["duplicate_url"]), 1)
        self.assertEqual(len(decisions["duplicate_hash"]), 1)
        self.assertEqual(len(decisions["duplicate_origin_group"]), 1)
        self.assertEqual(len(decisions["new_disclosure_candidate"]), 9)

    def test_syndicated_repost_shares_the_origin_group(self) -> None:
        _run(self.source, self.state)
        row = _manifest_decisions(self.state)["duplicate_origin_group"][0]
        self.assertIn("syndicated repost", row["detail"])
        urls = {
            item["canonical_url"]
            for item in _read_csv(self.state / "staging" / RUN_DATE / "disclosure_candidates.csv")
        }
        self.assertNotIn("https://www.globenewswire.com/news-release/2026/09/01/aaoi-first-volume-order-800g", urls)

    def test_url_already_curated_in_the_ledger_is_deduped(self) -> None:
        curated_url = "https://investor.lumentum.com/financial-news-releases/lumentum-first-shipment-1-6t-2026-09-01"
        source = _build_source(
            self.tmp / "curated-source",
            disclosures=[_row(
                "disclosures.csv", disclosure_id="D_EXISTING", publisher_entity_id="LITE",
                title="Lumentum Begins Shipment of 1.6T Pluggable Optics",
                disclosure_type="official_release", content_class="corporate_narrative",
                provenance_class="first_party", canonical_url=curated_url,
                content_hash="deadbeef", origin_group="OGC_EXISTING",
                published_at="2026-08-01", discovered_at="2026-08-01",
                retrieved_at="2026-08-01", retrieval_status="retrieved",
                processing_status="unprocessed",
            )],
        )
        _run(source, self.state)
        decisions = _manifest_decisions(self.state)
        self.assertEqual(len(decisions["duplicate_url"]), 2)  # ledger hit + in-run hit
        urls = {
            item["canonical_url"]
            for item in _read_csv(self.state / "staging" / RUN_DATE / "disclosure_candidates.csv")
        }
        self.assertNotIn(curated_url, urls)

    def test_content_hash_is_deterministic(self) -> None:
        paragraphs = (("p1", "Same  text"), ("p2", "Body"))
        self.assertEqual(dd.content_hash(paragraphs), dd.content_hash(paragraphs))
        self.assertNotEqual(
            dd.content_hash(paragraphs),
            dd.content_hash((("p1", "Different text"), ("p2", "Body"))),
        )


class TestPermissionGuards(DailyDiscoveryTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.summary = _run(self.source, self.state)
        self.staging = self.state / "staging" / RUN_DATE
        self.details = json.loads((self.staging / "candidates.json").read_text(encoding="utf-8"))

    def test_claims_are_always_candidate(self) -> None:
        claims = _read_csv(self.staging / "claim_candidates.csv")
        self.assertTrue(claims)
        for row in claims:
            self.assertEqual(row["review_status"], "candidate")
            self.assertEqual(row["reviewed_at"], "")
            self.assertNotEqual(row["review_status"], "anchor_reviewed")

    def test_events_never_exceed_asserted(self) -> None:
        events = _read_csv(self.staging / "event_candidates.csv")
        self.assertTrue(events)
        for row in events:
            self.assertEqual(row["event_status"], "asserted")
            self.assertEqual(row["previous_event_id"], "")

    def test_first_party_material_is_never_independent_evidence(self) -> None:
        disclosures = {
            row["disclosure_id"]: row
            for row in _read_csv(self.staging / "disclosure_candidates.csv")
        }
        claims = {
            row["event_claim_id"]: row
            for row in _read_csv(self.staging / "claim_candidates.csv")
        }
        evidence = _read_csv(self.staging / "evidence_candidates.csv")
        self.assertTrue(evidence)
        for row in evidence:
            disclosure = disclosures[claims[row["event_claim_id"]]["disclosure_id"]]
            self.assertEqual(row["origin_group"], disclosure["origin_group"])
            if disclosure["provenance_class"] == "first_party":
                self.assertEqual(row["independence_class"], "first_party")

    def test_corroboration_is_only_a_suggestion(self) -> None:
        suggested = [
            event for event in self.details["event_candidates"]
            if event["suggested_event_status"] == "corroborated"
        ]
        self.assertEqual(len(suggested), 1)
        event = suggested[0]
        self.assertEqual(event["primary_subject_id"], "LITE")
        self.assertTrue(event["requires_human_approval"])
        origins = event["corroboration_origins"]
        self.assertTrue(origins["first_party"])
        self.assertTrue(origins["independent"])
        self.assertFalse(set(origins["first_party"]) & set(origins["independent"]))
        # the written status stays asserted even where corroborated is suggested
        written = {
            row["event_id"]: row["event_status"]
            for row in _read_csv(self.staging / "event_candidates.csv")
        }
        self.assertEqual(written[event["event_id"]], "asserted")
        self.assertEqual(self.summary["corroboration_suggestions"], 1)

    def test_independent_evidence_without_first_party_stays_asserted(self) -> None:
        by_id = {event["event_id"]: event for event in self.details["event_candidates"]}
        blocked = [
            event for event in by_id.values()
            if event["blocked_reason"] == "missing_first_party_asserted_origin"
        ]
        self.assertTrue(blocked)
        for event in blocked:
            self.assertEqual(event["suggested_event_status"], "asserted")

    def test_technical_blog_cannot_derive_mature_commercial_stage(self) -> None:
        failures = _read_csv(self.staging / "failures.csv")
        denied = [row for row in failures if row["failure_type"] == "permission_denied"]
        self.assertEqual(len(denied), 1)
        self.assertEqual(denied[0]["endpoint_id"], "LITE_TECH_BLOG")
        self.assertIn("technical_or_demo_material_cannot_support_mature_commercial_stage", denied[0]["detail"])
        stages = {
            (row["primary_subject_id"], row["lifecycle_stage"])
            for row in _read_csv(self.staging / "event_candidates.csv")
        }
        self.assertNotIn(("LITE", "ramping"), stages)
        # the demo itself is still a legal candidate
        self.assertIn(("LITE", "demonstrated"), stages)

    def test_formal_release_is_not_blocked_by_narrative_content_class(self) -> None:
        stages = {
            (row["primary_subject_id"], row["lifecycle_stage"])
            for row in _read_csv(self.staging / "event_candidates.csv")
        }
        self.assertIn(("LITE", "first_shipment"), stages)

    def test_forward_looking_is_downgraded_and_never_realized(self) -> None:
        claims = {
            row["event_claim_id"]: row
            for row in _read_csv(self.staging / "claim_candidates.csv")
        }
        forward = [row for row in claims.values() if row["statement_kind"] == "forward_looking"]
        self.assertTrue(forward)
        for row in forward:
            details = [
                item for item in self.details["claim_candidates"]
                if item["claim_id"] == row["event_claim_id"]
            ][0]
            self.assertFalse(details["realized"])
            self.assertEqual(details["lifecycle_stage"], "announced")
            self.assertNotIn(details["lifecycle_stage"], dd.MATURE_COMMERCIAL_STAGES)
            self.assertIn("前瞻", row["notes"])

    def test_forward_looking_sentence_does_not_produce_a_realized_stage(self) -> None:
        statements = dd.extract_statements(_source_item(
            self.source,
            "MACOM expects to begin volume production of the driver by Q4 2026.",
        ))
        self.assertEqual(len(statements), 1)
        self.assertFalse(statements[0].realized)
        self.assertEqual(statements[0].statement_kind, "forward_looking")
        self.assertEqual(statements[0].lifecycle_stage, "announced")
        self.assertNotIn(statements[0].lifecycle_stage, dd.MATURE_COMMERCIAL_STAGES)

    def test_realized_statement_stays_realized(self) -> None:
        statements = dd.extract_statements(_source_item(
            self.source,
            "The company began shipping the module this quarter.",
        ))
        self.assertEqual(statements[0].statement_kind, "fact_assertion")
        self.assertTrue(statements[0].realized)
        self.assertEqual(statements[0].lifecycle_stage, "first_shipment")

    def test_independent_confirmation_on_later_date_can_only_suggest_corroboration(self) -> None:
        fixtures = self.tmp / "fixtures"
        shutil.copytree(FIXTURES, fixtures)
        path = fixtures / "CSCO_IR_RELEASES.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["items"][0]["published_at"] = "2026-08-28"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        summary = dd.run_daily_discovery(
            self.source, self.state, RUN_DATE, CONFIG, dd.FixtureFetcher(fixtures)
        )
        self.assertEqual(summary["corroboration_suggestions"], 1)
        events = json.loads(
            (self.state / "staging" / RUN_DATE / "candidates.json").read_text(encoding="utf-8")
        )["event_candidates"]
        suggested = [row for row in events if row["suggested_event_status"] == "corroborated"]
        self.assertEqual(len(suggested), 1)
        self.assertEqual(suggested[0]["event_status"], "asserted")


class TestExplicitFailures(DailyDiscoveryTestCase):
    def setUp(self) -> None:
        super().setUp()
        _run(self.source, self.state)
        self.staging = self.state / "staging" / RUN_DATE

    def test_every_failure_class_is_recorded(self) -> None:
        self.assertEqual(
            _failure_types(self.state),
            {
                "fetch_failure", "invalid_item", "future_published_at",
                "no_relevant_content", "unresolved_entity",
                "low_confidence_entity_mapping", "permission_denied",
            },
        )

    def test_failures_reach_the_queue(self) -> None:
        queue = json.loads((self.state / "queue-latest.json").read_text(encoding="utf-8"))
        self.assertEqual(queue["run_date"], RUN_DATE)
        types = {entry["queue_type"] for entry in queue["entries"]}
        for failure_type in _failure_types(self.state):
            self.assertIn(failure_type, types)
        self.assertIn("claim_candidate_pending_anchor_review", types)
        self.assertIn("corroboration_suggestion_pending_approval", types)

    def test_unresolved_entity_still_keeps_a_disclosure_candidate(self) -> None:
        disclosures = _read_csv(self.staging / "disclosure_candidates.csv")
        unresolved = [
            row for row in disclosures
            if row["canonical_url"] == "https://www.iqep.com/media/press-releases/2026/research-collaboration-optics-company"
        ]
        self.assertEqual(len(unresolved), 1)
        self.assertIn("实体未解析", unresolved[0]["notes"])
        claims = _read_csv(self.staging / "claim_candidates.csv")
        self.assertNotIn(unresolved[0]["disclosure_id"], {row["disclosure_id"] for row in claims})

    def test_low_confidence_mapping_is_flagged_not_silently_chosen(self) -> None:
        disclosures = _read_csv(self.staging / "disclosure_candidates.csv")
        flagged = [row for row in disclosures if "低置信度映射" in row["notes"]]
        self.assertEqual(len(flagged), 1)
        self.assertIn("AAOI;LITE", flagged[0]["notes"])

    def test_fetch_failure_is_not_rewritten_as_no_content(self) -> None:
        rows = [
            row for row in _read_csv(self.staging / "failures.csv")
            if row["failure_type"] == "fetch_failure"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["endpoint_id"], "HAMAMATSU_IR_RELEASES")
        self.assertIn("504", rows[0]["detail"])

    def test_no_content_disclosure_stays_unprocessed(self) -> None:
        disclosures = {
            row["disclosure_id"]: row
            for row in _read_csv(self.staging / "disclosure_candidates.csv")
        }
        unprocessed = [row for row in disclosures.values() if row["processing_status"] == "unprocessed"]
        self.assertTrue(unprocessed)
        for row in unprocessed:
            self.assertEqual(row["reviewed_at"], "")


class TestStateRootIsolation(DailyDiscoveryTestCase):
    def test_state_root_inside_calls_is_rejected(self) -> None:
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "must not write into calls/"):
            _run(self.source, self.source / "calls" / "state")

    def test_state_root_inside_calls_out_is_rejected(self) -> None:
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "must not write into calls/out/"):
            _run(self.source, self.source / "calls" / "out" / "state")

    def test_state_root_inside_source_root_is_rejected(self) -> None:
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "outside the read-only source root"):
            _run(self.source, self.source / "state")

    def test_lock_blocks_a_second_run(self) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / dd.LOCK_NAME).write_text('{"pid": 1}', encoding="utf-8")
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "lock is held"):
            _run(self.source, self.state)

    def test_lock_is_released_after_a_successful_run(self) -> None:
        _run(self.source, self.state)
        self.assertFalse((self.state / dd.LOCK_NAME).exists())

    def test_lock_is_released_after_a_failed_run(self) -> None:
        with self.assertRaises(dd.DailyDiscoveryError):
            dd.run_daily_discovery(
                self.source, self.state, "not-a-date", CONFIG, dd.FixtureFetcher(FIXTURES)
            )
        self.assertFalse((self.state / dd.LOCK_NAME).exists())

    def test_no_temporary_files_are_left_behind(self) -> None:
        _run(self.source, self.state)
        leftovers = sorted(str(path) for path in self.state.rglob("*.tmp"))
        self.assertEqual(leftovers, [])


class TestIdempotency(DailyDiscoveryTestCase):
    def test_same_day_rerun_produces_identical_candidates(self) -> None:
        _run(self.source, self.state)
        first = self.tmp / "first"
        shutil.copytree(self.state / "staging" / RUN_DATE, first)
        first_daily = (self.state / "daily" / f"{RUN_DATE}.txt").read_text(encoding="utf-8")
        _run(self.source, self.state)
        for name in CANDIDATE_FILES:
            self.assertEqual(
                (first / name).read_bytes(),
                (self.state / "staging" / RUN_DATE / name).read_bytes(),
                msg=f"{name} changed on a same-day rerun",
            )
        self.assertEqual(
            first_daily, (self.state / "daily" / f"{RUN_DATE}.txt").read_text(encoding="utf-8")
        )

    def test_queue_rotation_and_diff(self) -> None:
        _run(self.source, self.state)
        first = json.loads((self.state / "queue-latest.json").read_text(encoding="utf-8"))
        _run(self.source, self.state)
        diff = json.loads((self.state / "queue-diff.json").read_text(encoding="utf-8"))
        previous = json.loads((self.state / "queue-prev.json").read_text(encoding="utf-8"))
        self.assertEqual(previous["entries"], first["entries"])
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])
        self.assertEqual(diff["unchanged_count"], len(first["entries"]))
        self.assertEqual(diff["current_count"], diff["previous_count"])

    def test_daily_report_is_written(self) -> None:
        _run(self.source, self.state)
        report = (self.state / "daily" / f"{RUN_DATE}.txt").read_text(encoding="utf-8")
        self.assertIn(f"# 海外事件雷达日更镜像 {RUN_DATE}", report)
        self.assertIn("运行模式：fixture", report)
        self.assertIn("全部 review_status=candidate", report)
        self.assertIn("全部 event_status=asserted", report)
        summary = json.loads(
            (self.state / "staging" / RUN_DATE / "run-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(summary["fetch_mode"], "fixture")


class TestReadOnlyGuarantee(unittest.TestCase):
    """A full run against the real ledger must not change a single curated byte."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.state = Path(self._tmp.name) / "state"
        self.addCleanup(self._tmp.cleanup)

    @staticmethod
    def _snapshot() -> dict[str, str]:
        files = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "calls").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        files |= {
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "out").rglob("*")
            if path.is_file()
        }
        files |= {name for name in CANONICAL_FILES if (REPO_ROOT / name).is_file()}
        files |= {"shipments.csv", "macro_evidence.csv"}
        return {name: _sha(REPO_ROOT / name) for name in sorted(files) if (REPO_ROOT / name).is_file()}

    def test_curated_ledger_and_canonical_files_are_untouched(self) -> None:
        before = self._snapshot()
        summary = dd.run_daily_discovery(
            REPO_ROOT, self.state, RUN_DATE, CONFIG, dd.FixtureFetcher(FIXTURES)
        )
        dd.verify_staging(REPO_ROOT, self.state, RUN_DATE)
        self.assertEqual(self._snapshot(), before)
        self.assertEqual(summary["promoted"], 0)
        self.assertGreater(summary["failure_types"].get("missing_endpoint", 0), 0)

    def test_verify_never_promotes(self) -> None:
        _run_path = self.state
        dd.run_daily_discovery(REPO_ROOT, _run_path, RUN_DATE, CONFIG, dd.FixtureFetcher(FIXTURES))
        before = self._snapshot()
        messages = dd.verify_staging(REPO_ROOT, _run_path, RUN_DATE)
        self.assertEqual(self._snapshot(), before)
        self.assertTrue(any("verify never promotes" in message for message in messages))
        self.assertTrue(any("curated ledger read-only" in message for message in messages))


class TestVerifyStaging(DailyDiscoveryTestCase):
    def setUp(self) -> None:
        super().setUp()
        _run(self.source, self.state)
        self.staging = self.state / "staging" / RUN_DATE

    def _rewrite(self, name: str, schema: str, mutate) -> None:
        rows = _read_csv(self.staging / name)
        for row in rows:
            mutate(row)
        _write_table(self.staging / name, schema, rows)

    def test_verify_accepts_a_clean_run(self) -> None:
        messages = dd.verify_staging(self.source, self.state, RUN_DATE)
        self.assertEqual(len(messages), 6)

    def test_verify_rejects_a_promoted_event_status(self) -> None:
        self._rewrite(
            "event_candidates.csv", "events.csv",
            lambda row: row.update(event_status="corroborated"),
        )
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "cannot exceed asserted"):
            dd.verify_staging(self.source, self.state, RUN_DATE)

    def test_verify_rejects_an_anchor_reviewed_claim(self) -> None:
        self._rewrite(
            "claim_candidates.csv", "event_claims.csv",
            lambda row: row.update(review_status="anchor_reviewed", reviewed_at=RUN_DATE),
        )
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "must stay candidate"):
            dd.verify_staging(self.source, self.state, RUN_DATE)

    def test_verify_rejects_a_reviewed_disclosure_state(self) -> None:
        self._rewrite(
            "disclosure_candidates.csv", "disclosures.csv",
            lambda row: row.update(processing_status="anchor_reviewed", reviewed_at=RUN_DATE),
        )
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "human-reviewed state"):
            dd.verify_staging(self.source, self.state, RUN_DATE)

    def test_verify_rejects_first_party_marked_independent(self) -> None:
        self._rewrite(
            "evidence_candidates.csv", "event_evidence.csv",
            lambda row: row.update(independence_class="counterparty"),
        )
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "cannot count as independent|conflicts with disclosure"):
            dd.verify_staging(self.source, self.state, RUN_DATE)

    def test_verify_rejects_a_stage_linkage(self) -> None:
        self._rewrite(
            "event_candidates.csv", "events.csv",
            lambda row: row.update(previous_event_id="EC_OTHER"),
        )
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "human-gate decision"):
            dd.verify_staging(self.source, self.state, RUN_DATE)

    def test_verify_requires_a_staging_directory(self) -> None:
        with self.assertRaisesRegex(dd.DailyDiscoveryError, "no staging directory"):
            dd.verify_staging(self.source, self.state, "2020-01-01")


class TestCli(DailyDiscoveryTestCase):
    def test_run_and_verify_commands_succeed(self) -> None:
        self.assertEqual(dd.main([
            "run", "--source-root", str(self.source), "--state-root", str(self.state),
            "--date", RUN_DATE, "--config", str(CONFIG), "--fixtures", str(FIXTURES),
        ]), 0)
        self.assertEqual(dd.main([
            "verify", "--source-root", str(self.source), "--state-root", str(self.state),
            "--date", RUN_DATE,
        ]), 0)

    def test_cli_reports_a_bad_date(self) -> None:
        self.assertEqual(dd.main([
            "run", "--source-root", str(self.source), "--state-root", str(self.state),
            "--date", "09/01/2026", "--config", str(CONFIG), "--fixtures", str(FIXTURES),
        ]), 1)

    def test_cli_reports_a_forbidden_state_root(self) -> None:
        self.assertEqual(dd.main([
            "run", "--source-root", str(self.source),
            "--state-root", str(self.source / "calls"),
            "--date", RUN_DATE, "--config", str(CONFIG), "--fixtures", str(FIXTURES),
        ]), 1)


if __name__ == "__main__":
    unittest.main()
