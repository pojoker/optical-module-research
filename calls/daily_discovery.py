"""Daily discovery mirror for the overseas event ledger.

The module scans per-entity official / regulatory / counterparty / government
endpoints and writes only schema-shaped *candidates* into an isolated state
root.  It never edits ``calls/*.csv``, ``calls/out/`` or root canonical files,
never writes ``anchor_reviewed`` claims, never writes anything but ``asserted``
into ``event_status``, and never promotes a candidate into the curated ledger.

Public seam::

    run_daily_discovery(source_root, state_root, run_date, config_path, fetcher)
    verify_staging(source_root, state_root, run_date)

CLI::

    python3 -m calls.daily_discovery run --source-root <repo> --state-root <dir> \
        --date YYYY-MM-DD --config <file>
    # add --fixtures <dir> only for deterministic offline rehearsal/tests
    python3 -m calls.daily_discovery verify --source-root <repo> --state-root <dir> \
        --date YYYY-MM-DD
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlparse

from .schema import ENUMS, FILES


class DailyDiscoveryError(ValueError):
    """Raised when the daily mirror violates its read-only / permission contract."""


LOCK_NAME = ".daily-discovery.lock"
STAGING_DIR = "staging"
DAILY_DIR = "daily"

MATURE_COMMERCIAL_STAGES = frozenset({"volume_order", "first_shipment", "ramping", "scaled"})
INDEPENDENT_CLASSES = frozenset({"counterparty", "regulator", "observable_result"})
BLOG_CONTENT_CLASSES = frozenset({"demonstration_disclosure"})
BLOG_DISCLOSURE_TYPES = frozenset({"technical_blog", "product_page", "datasheet"})
# 技术博客/演示不得推导的量级：量产、客户采用、订单规模、供货关系与需求规模。
BLOG_BLOCKED_CATEGORIES = frozenset({"commercial_adoption", "supply_chain_arrangement"})

ENDPOINT_KINDS = {
    "official_ir": "company investor-relations release feed",
    "official_blog": "company-signed technical blog",
    "regulatory_filing": "regulator or exchange hosted filing",
    "counterparty_release": "named customer or counterparty release",
    "government_record": "government record",
    "product_page": "company product or datasheet page",
}
REJECTED_ENDPOINT_KINDS = frozenset({"media", "generic_news", "aggregator", "macro_news"})

INDEPENDENCE_BY_PROVENANCE = {
    "first_party": "first_party",
    "counterparty": "counterparty",
    "regulator": "regulator",
    "government": "observable_result",
    "third_party": "third_party",
    "unknown": "same_origin",
}
PROVENANCE_ALLOWED_BY_INDEPENDENCE = {
    "first_party": frozenset({"first_party"}),
    "counterparty": frozenset({"counterparty"}),
    "regulator": frozenset({"regulator", "government"}),
    "third_party": frozenset({"third_party"}),
    "observable_result": frozenset({"counterparty", "regulator", "government", "third_party"}),
    "same_origin": frozenset({"first_party", "counterparty", "regulator", "government", "third_party", "unknown"}),
}
IDENTITY_RELATIONSHIPS = frozenset({
    "parent_of", "subsidiary_of", "acquired_by", "brand_of",
    "predecessor_of", "business_transferred_to",
})

STAGING_TABLES = {
    "disclosure_candidates.csv": "disclosures.csv",
    "claim_candidates.csv": "event_claims.csv",
    "event_candidates.csv": "events.csv",
    "evidence_candidates.csv": "event_evidence.csv",
}
DEDUPE_FIELDS = (
    "run_date", "item_url", "endpoint_id", "decision", "detail",
    "target_id", "origin_group", "content_hash",
)
FAILURE_FIELDS = ("run_date", "failure_type", "endpoint_id", "item_url", "entity_id", "detail")


# --------------------------------------------------------------------------
# text / id helpers
# --------------------------------------------------------------------------


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def content_hash(paragraphs: Sequence[tuple[str, str]]) -> str:
    """Deterministic content hash over ordered (anchor, text) paragraphs."""
    payload = "\n".join(f"{anchor}\n{_normalize_text(text)}" for anchor, text in paragraphs)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _digest12(*parts: str) -> str:
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12].upper()


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_{_digest12(*parts)}"


def _url_ok(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _iso_date(value: str, field_name: str, where: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise DailyDiscoveryError(f"{where}: invalid {field_name}={value!r}") from exc
    return value


def _quote_sentence(text: str, needle_start: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    position = 0
    for sentence in sentences:
        end = position + len(sentence)
        if position <= needle_start < end:
            return _clip(sentence.strip())
        position = end + 1
    return _clip(text.strip())


def _clip(value: str, limit: int = 300) -> str:
    return value if len(value) <= limit else value[:limit].rstrip() + "…"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


# --------------------------------------------------------------------------
# monitoring pool and entity identity
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str
    name: str
    tier: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class EntityRegistry:
    entities: dict[str, EntityRecord]
    monitored: tuple[str, ...]
    alias_index: tuple[tuple[str, str], ...]
    canonical: dict[str, str]

    def resolve_mentions(self, text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Return (canonical entity ids, matched alias needles) found in text."""
        lowered = text.lower()
        matched: dict[str, str] = {}
        for needle, entity_id in self.alias_index:
            if entity_id in matched:
                continue
            pattern = re.compile(r"(?<![0-9a-z])" + re.escape(needle) + r"(?![0-9a-z])")
            if pattern.search(lowered):
                matched[entity_id] = needle
        canonical_ids = sorted({self.canonical.get(eid, eid) for eid in matched})
        aliases = tuple(sorted({needle for eid, needle in matched.items()
                                if self.canonical.get(eid, eid) in canonical_ids}))
        return tuple(canonical_ids), aliases


def _read_table(path: Path, name: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise DailyDiscoveryError(f"missing required read-only table: calls/{name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FILES[name]:
            raise DailyDiscoveryError(f"calls/{name}: header must match calls/schema.py")
        return list(reader)


def load_entity_registry(source_root: Path) -> EntityRegistry:
    """Union of enabled universe companies, active watch entities and open candidates."""
    calls_dir = source_root / "calls"
    universe_rows = _read_table(calls_dir / "universe.csv", "universe.csv")
    watch_rows = _read_table(calls_dir / "watch_entities.csv", "watch_entities.csv")
    candidate_rows = _read_table(calls_dir / "company_candidates.csv", "company_candidates.csv")
    relationship_rows = _read_table(calls_dir / "entity_relationships.csv", "entity_relationships.csv")

    entities: dict[str, EntityRecord] = {}
    monitored: set[str] = set()
    for row in universe_rows:
        entities[row["company_id"]] = EntityRecord(row["company_id"], row["company_name"], "quarterly", ())
        if row["enabled"] == "yes":
            monitored.add(row["company_id"])
    for row in watch_rows:
        aliases = tuple(item.strip() for item in row["aliases"].split(";") if item.strip())
        entities[row["entity_id"]] = EntityRecord(row["entity_id"], row["entity_name"], "watch", aliases)
        if row["monitoring_status"] == "active":
            monitored.add(row["entity_id"])
    for row in candidate_rows:
        entities[row["candidate_id"]] = EntityRecord(row["candidate_id"], row["entity_name"], "candidate", ())
        if row["verification_status"] != "promoted":
            monitored.add(row["candidate_id"])

    universe_ids = {row["company_id"] for row in universe_rows}
    watch_by_id = {row["entity_id"]: row for row in watch_rows}

    def rank(entity_id: str) -> tuple[int, str]:
        if entity_id in universe_ids:
            return (0, entity_id)
        row = watch_by_id.get(entity_id)
        if row is not None:
            return (2 if row["monitoring_status"] == "promoted" else 1, entity_id)
        return (3, entity_id)

    parent: dict[str, str] = {entity_id: entity_id for entity_id in entities}

    def find(entity_id: str) -> str:
        root = entity_id
        while parent.get(root, root) != root:
            root = parent[root]
        current = entity_id
        while parent.get(current, current) != root:
            current, parent[current] = root, root
        return root

    for row in sorted(relationship_rows, key=lambda item: item["relationship_id"]):
        if row["review_status"] != "reviewed":
            continue
        if row["relationship_type"] not in IDENTITY_RELATIONSHIPS:
            continue
        subject, obj = row["subject_entity_id"], row["object_entity_id"]
        if subject not in parent or obj not in parent:
            continue
        left, right = find(subject), find(obj)
        if left == right:
            continue
        if rank(left) <= rank(right):
            parent[right] = left
        else:
            parent[left] = right
    canonical = {entity_id: find(entity_id) for entity_id in entities}

    alias_index: list[tuple[str, str]] = []
    for entity_id in sorted(entities):
        record = entities[entity_id]
        needles = [record.name, *record.aliases]
        for needle in sorted({_normalize_text(item) for item in needles if item.strip()},
                             key=lambda item: (-len(item), item)):
            alias_index.append((needle, entity_id))
    return EntityRegistry(
        entities=entities,
        monitored=tuple(sorted(monitored)),
        alias_index=tuple(alias_index),
        canonical=canonical,
    )


def load_ledger_index(source_root: Path) -> dict[str, set[str]]:
    """Read-only dedupe index over the curated event ledger."""
    calls_dir = source_root / "calls"
    disclosures = _read_table(calls_dir / "disclosures.csv", "disclosures.csv")
    claims = _read_table(calls_dir / "event_claims.csv", "event_claims.csv")
    events = _read_table(calls_dir / "events.csv", "events.csv")
    return {
        "urls": {row["canonical_url"] for row in disclosures if row["canonical_url"]},
        "hashes": {row["content_hash"] for row in disclosures if row["content_hash"]},
        "origins": {row["origin_group"] for row in disclosures if row["origin_group"]},
        "claims": {
            (row["quote"].strip(), row["anchor"].strip()) for row in claims
        },
        "events": {
            (
                row["primary_subject_id"], row["event_category"],
                row["lifecycle_stage"], row["occurred_start"],
            )
            for row in events
        },
    }


# --------------------------------------------------------------------------
# discovery configuration
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Endpoint:
    entity_id: str
    endpoint_id: str
    endpoint_kind: str
    url: str
    disclosure_type: str
    content_class: str
    provenance_class: str
    corroborates: tuple[str, ...]


def load_discovery_config(path: Path, registry: EntityRegistry) -> tuple[Endpoint, ...]:
    """Load per-entity discovery endpoints; generic news feeds are rejected."""
    if not path.is_file():
        raise DailyDiscoveryError(f"missing discovery config: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise DailyDiscoveryError("discovery config: unsupported version; expected 1")
    endpoints: list[Endpoint] = []
    seen_ids: set[str] = set()
    for entity_id in sorted(payload.get("entities", {})):
        block = payload["entities"][entity_id]
        if entity_id not in registry.entities:
            raise DailyDiscoveryError(f"discovery config: unknown entity {entity_id}")
        if entity_id not in registry.monitored:
            raise DailyDiscoveryError(
                f"discovery config: {entity_id} is not in the monitoring pool "
                "(needs enabled quarterly company, active watch entity or open candidate)"
            )
        for raw in block.get("endpoints", ()):
            endpoint_id = str(raw.get("endpoint_id", "")).strip()
            if not endpoint_id:
                raise DailyDiscoveryError(f"discovery config:{entity_id}: endpoint_id is required")
            if endpoint_id in seen_ids:
                raise DailyDiscoveryError(f"discovery config: duplicate endpoint_id {endpoint_id}")
            seen_ids.add(endpoint_id)
            kind = str(raw.get("endpoint_kind", "")).strip()
            if kind in REJECTED_ENDPOINT_KINDS:
                raise DailyDiscoveryError(
                    f"discovery config:{endpoint_id}: {kind} feeds are rejected; "
                    "discovery must use entity-specific official, regulatory, "
                    "counterparty or government endpoints"
                )
            if kind not in ENDPOINT_KINDS:
                raise DailyDiscoveryError(f"discovery config:{endpoint_id}: invalid endpoint_kind={kind!r}")
            url = str(raw.get("url", "")).strip()
            if not _url_ok(url):
                raise DailyDiscoveryError(f"discovery config:{endpoint_id}: invalid url={url!r}")
            disclosure_type = str(raw.get("disclosure_type", "")).strip()
            if disclosure_type not in ENUMS["disclosure_type"]:
                raise DailyDiscoveryError(f"discovery config:{endpoint_id}: invalid disclosure_type")
            if disclosure_type == "media":
                raise DailyDiscoveryError(
                    f"discovery config:{endpoint_id}: media cannot be a discovery endpoint type"
                )
            content_class = str(raw.get("content_class", "")).strip()
            if content_class not in ENUMS["content_class"]:
                raise DailyDiscoveryError(f"discovery config:{endpoint_id}: invalid content_class")
            provenance = str(raw.get("provenance_class", "")).strip()
            if provenance not in ENUMS["provenance_class"]:
                raise DailyDiscoveryError(f"discovery config:{endpoint_id}: invalid provenance_class")
            corroborates = tuple(sorted({
                str(item).strip() for item in raw.get("corroborates_entity_ids", ()) if str(item).strip()
            }))
            for target in corroborates:
                if target not in registry.entities:
                    raise DailyDiscoveryError(
                        f"discovery config:{endpoint_id}: unknown corroborates entity {target}"
                    )
            if provenance == "first_party" and corroborates:
                raise DailyDiscoveryError(
                    f"discovery config:{endpoint_id}: first-party endpoint cannot declare corroborates_entity_ids"
                )
            if provenance != "first_party" and not corroborates:
                raise DailyDiscoveryError(
                    f"discovery config:{endpoint_id}: independent endpoint must declare corroborates_entity_ids"
                )
            endpoints.append(Endpoint(
                entity_id=entity_id,
                endpoint_id=endpoint_id,
                endpoint_kind=kind,
                url=url,
                disclosure_type=disclosure_type,
                content_class=content_class,
                provenance_class=provenance,
                corroborates=corroborates,
            ))
    if not endpoints:
        raise DailyDiscoveryError("discovery config: no endpoints declared")
    return tuple(sorted(endpoints, key=lambda item: (item.entity_id, item.endpoint_id)))


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FetchResult:
    endpoint_id: str
    items: tuple[dict[str, Any], ...]
    failure: str


class FixtureFetcher:
    """Offline deterministic fetcher: ``<fixture_dir>/<endpoint_id>.json``.

    The live CLI uses ``HttpFetcher``; this adapter keeps tests deterministic.
    Nothing in this module installs or triggers a scheduler.
    """

    fetch_mode = "fixture"

    def __init__(self, fixture_dir: Path) -> None:
        self.fixture_dir = fixture_dir

    def fetch(self, endpoint: Endpoint) -> FetchResult:
        path = self.fixture_dir / f"{endpoint.endpoint_id}.json"
        if not path.is_file():
            return FetchResult(endpoint.endpoint_id, (), f"fixture missing: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        failure = str(payload.get("failure") or "").strip()
        if failure:
            return FetchResult(endpoint.endpoint_id, (), failure)
        items = tuple(payload.get("items", ()))
        return FetchResult(endpoint.endpoint_id, items, "")


@dataclass(frozen=True)
class SourceItem:
    endpoint: Endpoint
    url: str
    title: str
    published_at: str
    origin_key: str
    paragraphs: tuple[tuple[str, str], ...]
    disclosure_type: str
    content_class: str
    provenance_class: str
    note: str


def _parse_item(endpoint: Endpoint, raw: dict[str, Any], where: str) -> SourceItem:
    url = str(raw.get("url", "")).strip()
    if not _url_ok(url):
        raise DailyDiscoveryError(f"{where}: invalid url={url!r}")
    published = str(raw.get("published_at", "")).strip()
    if not published:
        raise DailyDiscoveryError(f"{where}: published_at is required")
    _iso_date(published, "published_at", where)
    disclosure_type = str(raw.get("disclosure_type") or endpoint.disclosure_type)
    if disclosure_type not in ENUMS["disclosure_type"]:
        raise DailyDiscoveryError(f"{where}: invalid disclosure_type={disclosure_type!r}")
    content_class = str(raw.get("content_class") or endpoint.content_class)
    if content_class not in ENUMS["content_class"]:
        raise DailyDiscoveryError(f"{where}: invalid content_class={content_class!r}")
    provenance = str(raw.get("provenance_class") or endpoint.provenance_class)
    if provenance not in ENUMS["provenance_class"]:
        raise DailyDiscoveryError(f"{where}: invalid provenance_class={provenance!r}")
    paragraphs: list[tuple[str, str]] = []
    for index, block in enumerate(raw.get("paragraphs", ())):
        anchor = str(block.get("anchor", "")).strip()
        text = str(block.get("text", "")).strip()
        if not anchor or not text:
            raise DailyDiscoveryError(f"{where}: paragraph {index + 1} needs anchor and text")
        paragraphs.append((anchor, text))
    return SourceItem(
        endpoint=endpoint,
        url=url,
        title=str(raw.get("title", "")).strip(),
        published_at=published,
        origin_key=str(raw.get("origin_key", "")).strip() or url,
        paragraphs=tuple(paragraphs),
        disclosure_type=disclosure_type,
        content_class=content_class,
        provenance_class=provenance,
        note=str(raw.get("note", "")).strip(),
    )


# --------------------------------------------------------------------------
# statement extraction
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SignalRule:
    code: str
    pattern: str
    event_category: str
    lifecycle_stage: str
    statement_kind: str
    realized: bool


SIGNAL_RULES: tuple[SignalRule, ...] = (
    SignalRule("first_volume_order", r"\bfirst volume order\b|\breceived (?:its |an? )?volume order\b",
               "commercial_adoption", "volume_order", "fact_assertion", True),
    SignalRule("first_shipment", r"\bfirst shipment\b|\bbegan shipping\b|\bstarts? shipping\b",
               "commercial_adoption", "first_shipment", "fact_assertion", True),
    SignalRule("ramping", r"\bramping\b|\bramp(?:ed|ing)? up\b|\bvolume production\b",
               "commercial_adoption", "ramping", "fact_assertion", True),
    SignalRule("qualifying", r"\bqualification\b|\bqualifying\b|\bqualified\b",
               "product_stage", "qualifying", "fact_assertion", True),
    SignalRule("sampling", r"\bbeg(?:an|un|ins|inning)? sampling\b|\bis sampling\b|\bsampling (?:to|of)\b",
               "product_stage", "sampling", "fact_assertion", True),
    SignalRule("demonstration", r"\bdemonstrated\b|\bdemonstration\b|\blive demo\w*\b|\bshowcased\b",
               "product_stage", "demonstrated", "technical_demo", True),
    SignalRule("capacity_constraint", r"\bcapacity constrain\w*\b|\bsupply constrain\w*\b|\btight supply\b",
               "capacity_constraint", "not_applicable", "corporate_narrative", True),
    SignalRule("capacity_expansion", r"\bexpand\w* (?:its |the )?capacity\b|\bcapacity expansion\b",
               "capacity_constraint", "announced", "forward_looking", False),
    SignalRule("future_delivery",
               r"\bexpects? to\b|\bplan(?:s|ned)? to\b|\bwill (?:begin|ship|start|deliver)\b"
               r"|\bon track to\b|\bby (?:the end of )?(?:20\d\d|Q[1-4])\b",
               "product_stage", "announced", "forward_looking", False),
)

_COMPILED_RULES = tuple((rule, re.compile(rule.pattern)) for rule in SIGNAL_RULES)

# 命中成熟商业动词但整句带前瞻语气时（"expects to begin volume production"），
# 必须降级为 announced/forward_looking，不能写成已兑现。
FORWARD_LOOKING_CUE = re.compile(
    r"\bexpects?\b|\banticipat\w*\b|\bplan(?:s|ned|ning)?\b|\bintends?\b|\bwill\b"
    r"|\bon track\b|\btargets?\b|\baims? to\b|\bforecast\w*\b|\bby (?:the end of )?(?:20\d\d|Q[1-4])\b",
)


@dataclass(frozen=True)
class ExtractedStatement:
    anchor: str
    quote: str
    signal_code: str
    statement_kind: str
    event_category: str
    lifecycle_stage: str
    realized: bool


def extract_statements(item: SourceItem) -> tuple[ExtractedStatement, ...]:
    """Deterministic first-match-per-paragraph signal extraction."""
    statements: list[ExtractedStatement] = []
    for anchor, text in item.paragraphs:
        lowered = text.lower()
        for rule, regex in _COMPILED_RULES:
            match = regex.search(lowered)
            if not match:
                continue
            quote = _quote_sentence(text, match.start())
            stage = rule.lifecycle_stage
            kind = rule.statement_kind
            realized = rule.realized
            if realized and FORWARD_LOOKING_CUE.search(quote.lower()):
                stage, kind, realized = "announced", "forward_looking", False
            statements.append(ExtractedStatement(
                anchor=anchor,
                quote=quote,
                signal_code=rule.code,
                statement_kind=kind,
                event_category=rule.event_category,
                lifecycle_stage=stage,
                realized=realized,
            ))
            break
    return tuple(statements)


# --------------------------------------------------------------------------
# candidate building
# --------------------------------------------------------------------------


@dataclass
class DisclosureCandidate:
    disclosure_id: str
    item: SourceItem
    origin_group: str
    content_hash: str
    statements: tuple[ExtractedStatement, ...]
    entity_ids: tuple[str, ...]
    matched_aliases: tuple[str, ...]
    low_confidence: bool
    unresolved: bool
    notes: list[str] = field(default_factory=list)


def _claimant_role(item: SourceItem) -> str:
    if item.provenance_class == "first_party":
        return "corporate_author" if item.disclosure_type == "technical_blog" else "corporate_disclosure"
    if item.provenance_class == "counterparty":
        return "customer" if item.disclosure_type == "customer_release" else "counterparty"
    if item.provenance_class in {"regulator", "government"}:
        return "regulator"
    return "other"


def _origin_group(endpoint: Endpoint, item: SourceItem, subject_id: str) -> str:
    # Deliberately omit the discovery endpoint. Reposts that preserve the
    # underlying origin_key must collapse even when found through another feed.
    return "OGC_" + _digest12(subject_id, item.origin_key)


def _mention_hits(text: str, needles: Iterable[str]) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(sorted({
        _normalize_text(needle) for needle in needles
        if needle.strip() and re.search(
            r"(?<![0-9a-z])" + re.escape(_normalize_text(needle)) + r"(?![0-9a-z])", lowered,
        )
    }))


def _event_subject(
    endpoint: Endpoint,
    item: SourceItem,
    registry: EntityRegistry,
) -> tuple[str, tuple[str, ...], tuple[str, ...], bool, bool]:
    """Resolve which monitored entity an independently-sourced statement is about."""
    if endpoint.provenance_class == "first_party":
        canonical = registry.canonical.get(endpoint.entity_id, endpoint.entity_id)
        return canonical, (canonical,), (registry.entities[canonical].name,), False, False
    haystack = " ".join([item.title, *[text for _, text in item.paragraphs]])
    entity_ids: set[str] = set()
    aliases: set[str] = set()
    for entity_id in endpoint.corroborates:
        record = registry.entities[entity_id]
        hits = _mention_hits(haystack, [record.name, *record.aliases])
        if hits:
            entity_ids.add(registry.canonical.get(entity_id, entity_id))
            aliases.update(hits)
    resolved = tuple(sorted(entity_ids))
    if not resolved:
        return "", (), (), False, True
    if len(resolved) > 1:
        return resolved[0], resolved, tuple(sorted(aliases)), True, False
    return resolved[0], resolved, tuple(sorted(aliases)), False, False


def _permission_blocked(disclosure_type: str, content_class: str, statement: ExtractedStatement) -> str:
    """Return a reason code when a statement may not become an event candidate."""
    if not statement.realized and statement.lifecycle_stage in MATURE_COMMERCIAL_STAGES:
        return "forward_looking_cannot_be_written_as_realized"
    blog_like = disclosure_type in BLOG_DISCLOSURE_TYPES or content_class in BLOG_CONTENT_CLASSES
    if blog_like:
        if statement.lifecycle_stage in MATURE_COMMERCIAL_STAGES:
            return "technical_or_demo_material_cannot_support_mature_commercial_stage"
        if statement.event_category in BLOG_BLOCKED_CATEGORIES:
            return "technical_or_demo_material_cannot_derive_commercial_adoption_or_supply_scale"
    return ""


@dataclass
class RunOutcome:
    disclosure_rows: list[dict[str, str]]
    claim_rows: list[dict[str, str]]
    event_rows: list[dict[str, str]]
    evidence_rows: list[dict[str, str]]
    manifest_rows: list[dict[str, str]]
    failure_rows: list[dict[str, str]]
    details: dict[str, Any]
    queue_entries: list[dict[str, Any]]


def _build_candidates(
    registry: EntityRegistry,
    ledger: dict[str, set[str]],
    endpoints: Sequence[Endpoint],
    fetcher: Any,
    run_date: str,
) -> RunOutcome:
    disclosure_rows: list[dict[str, str]] = []
    claim_rows: list[dict[str, str]] = []
    event_rows: list[dict[str, str]] = []
    evidence_rows: list[dict[str, str]] = []
    manifest_rows: list[dict[str, str]] = []
    failure_rows: list[dict[str, str]] = []
    detail_disclosures: list[dict[str, Any]] = []
    detail_claims: list[dict[str, Any]] = []
    detail_events: list[dict[str, Any]] = []
    detail_evidence: list[dict[str, Any]] = []
    queue_entries: list[dict[str, Any]] = []

    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    origin_owner: dict[str, str] = {}
    endpoint_stats = {"ok": 0, "failed": 0}
    item_total = 0
    decision_counts: dict[str, int] = defaultdict(int)

    def manifest(item_url: str, endpoint_id: str, decision: str, detail: str,
                 target_id: str = "", origin_group: str = "", item_hash: str = "") -> None:
        decision_counts[decision] += 1
        manifest_rows.append({
            "run_date": run_date,
            "item_url": item_url,
            "endpoint_id": endpoint_id,
            "decision": decision,
            "detail": detail,
            "target_id": target_id,
            "origin_group": origin_group,
            "content_hash": item_hash,
        })

    def failure(failure_type: str, endpoint_id: str, item_url: str, entity_id: str, detail: str) -> None:
        failure_rows.append({
            "run_date": run_date,
            "failure_type": failure_type,
            "endpoint_id": endpoint_id,
            "item_url": item_url,
            "entity_id": entity_id,
            "detail": detail,
        })
        queue_entries.append({
            "queue_type": failure_type,
            "endpoint_id": endpoint_id,
            "item_url": item_url,
            "entity_id": entity_id,
            "detail": detail,
        })

    candidates: list[DisclosureCandidate] = []
    configured = {registry.canonical.get(endpoint.entity_id, endpoint.entity_id) for endpoint in endpoints}
    monitored = {registry.canonical.get(entity_id, entity_id) for entity_id in registry.monitored}
    for entity_id in sorted(monitored - configured):
        failure(
            "missing_endpoint", "", "", entity_id,
            "monitored entity has no official/regulatory/counterparty/government discovery endpoint",
        )
    for endpoint in endpoints:
        result = fetcher.fetch(endpoint)
        if result.failure:
            endpoint_stats["failed"] += 1
            failure("fetch_failure", endpoint.endpoint_id, endpoint.url, endpoint.entity_id, result.failure)
            continue
        endpoint_stats["ok"] += 1
        for index, raw in enumerate(result.items, 1):
            item_total += 1
            where = f"{endpoint.endpoint_id}[{index}]"
            label = str(raw.get("url", ""))
            try:
                item = _parse_item(endpoint, raw, where)
            except DailyDiscoveryError as exc:
                failure("invalid_item", endpoint.endpoint_id, label, endpoint.entity_id, str(exc))
                continue
            if item.published_at > run_date:
                failure("future_published_at", endpoint.endpoint_id, item.url, endpoint.entity_id,
                        f"published_at {item.published_at} is after run date {run_date}")
                continue
            item_hash = content_hash(item.paragraphs)
            if item.url in ledger["urls"] or item.url in seen_urls:
                manifest(item.url, endpoint.endpoint_id, "duplicate_url",
                         "canonical URL already present in the ledger or this run",
                         origin_group="", item_hash=item_hash)
                continue
            if item_hash in ledger["hashes"] or item_hash in seen_hashes:
                manifest(item.url, endpoint.endpoint_id, "duplicate_hash",
                         "content hash already present in the ledger or this run",
                         item_hash=item_hash)
                continue
            subject_id, entity_ids, aliases, low_confidence, unresolved = _event_subject(
                endpoint, item, registry
            )
            origin_group = _origin_group(endpoint, item, subject_id or endpoint.entity_id)
            if origin_group in origin_owner:
                manifest(item.url, endpoint.endpoint_id, "duplicate_origin_group",
                         f"same origin group as {origin_owner[origin_group]}; syndicated repost is not "
                         "counted as an independent source",
                         target_id=origin_owner[origin_group], origin_group=origin_group,
                         item_hash=item_hash)
                continue
            if origin_group in ledger["origins"]:
                manifest(item.url, endpoint.endpoint_id, "duplicate_origin_group",
                         "origin group already curated in the ledger", origin_group=origin_group,
                         item_hash=item_hash)
                continue
            statements = extract_statements(item)
            if unresolved:
                failure("unresolved_entity", endpoint.endpoint_id, item.url, endpoint.entity_id,
                        "no corroborated entity alias matched this independent material")
            if low_confidence:
                failure("low_confidence_entity_mapping", endpoint.endpoint_id, item.url,
                        subject_id, f"multiple corroborated entities matched: {';'.join(entity_ids)}")
            if not statements:
                failure("no_relevant_content", endpoint.endpoint_id, item.url,
                        subject_id or endpoint.entity_id, "no event signal matched the retrieved text")
            seen_urls.add(item.url)
            seen_hashes.add(item_hash)
            origin_owner[origin_group] = _stable_id("DC", item.url)
            manifest(item.url, endpoint.endpoint_id, "new_disclosure_candidate",
                     "" if statements else "no event signal matched; kept for manual review",
                     target_id=origin_owner[origin_group], origin_group=origin_group, item_hash=item_hash)
            candidates.append(DisclosureCandidate(
                disclosure_id=origin_owner[origin_group],
                item=item,
                origin_group=origin_group,
                content_hash=item_hash,
                statements=statements,
                entity_ids=entity_ids,
                matched_aliases=aliases,
                low_confidence=low_confidence,
                unresolved=unresolved,
            ))

    # --- disclosure + claim candidates -------------------------------------
    claim_index: dict[str, dict[str, Any]] = {}
    for candidate in sorted(candidates, key=lambda item: item.disclosure_id):
        item = candidate.item
        endpoint = item.endpoint
        publisher = registry.canonical.get(endpoint.entity_id, endpoint.entity_id)
        notes = list(candidate.notes)
        if candidate.unresolved:
            notes.append("实体未解析：不生成事件候选，等待人工确认")
        if candidate.low_confidence:
            notes.append(f"低置信度映射：{';'.join(candidate.entity_ids)}")
        if item.note:
            notes.append(item.note)
        disclosure_rows.append({
            "disclosure_id": candidate.disclosure_id,
            "publisher_entity_id": publisher,
            "legacy_source_id": "",
            "title": item.title,
            "disclosure_type": item.disclosure_type,
            "content_class": item.content_class,
            "provenance_class": item.provenance_class,
            "canonical_url": item.url,
            "local_path": "",
            "content_hash": candidate.content_hash,
            "origin_group": candidate.origin_group,
            "published_at": item.published_at,
            "updated_at": "",
            "discovered_at": run_date,
            "retrieved_at": run_date,
            "reviewed_at": "",
            "retrieval_status": "retrieved",
            "processing_status": "candidate_extracted" if candidate.statements else "unprocessed",
            "review_scope": "",
            "notes": "；".join(notes),
        })
        detail_disclosures.append({
            "disclosure_id": candidate.disclosure_id,
            "endpoint_id": endpoint.endpoint_id,
            "endpoint_kind": endpoint.endpoint_kind,
            "publisher_entity_id": publisher,
            "resolved_entity_ids": list(candidate.entity_ids),
            "matched_aliases": list(candidate.matched_aliases),
            "origin_key": item.origin_key,
            "provenance_class": item.provenance_class,
            "statement_count": len(candidate.statements),
            "notes": list(notes),
        })
        for statement in candidate.statements:
            claim_id = _stable_id("CC", candidate.disclosure_id, statement.anchor, statement.quote)
            claim_key = (statement.quote.strip(), statement.anchor.strip())
            if claim_key in ledger["claims"]:
                manifest(item.url, endpoint.endpoint_id, "duplicate_claim",
                         "quote/anchor already curated in event_claims.csv", target_id=claim_id,
                         origin_group=candidate.origin_group, item_hash=candidate.content_hash)
                continue
            claim_notes = ["自动候选：review_status 固定为 candidate，未经人工锚点核验"]
            if not statement.realized:
                claim_notes.append("前瞻/未兑现表述：不得写成已发生事件")
            claim_rows.append({
                "event_claim_id": claim_id,
                "legacy_claim_id": "",
                "disclosure_id": candidate.disclosure_id,
                "claimant_entity_id": publisher,
                "claimant_role": _claimant_role(item),
                "statement_kind": statement.statement_kind,
                "quote": statement.quote,
                "anchor": statement.anchor,
                "summary": f"{publisher}材料出现 {statement.signal_code} 信号，待人工锚点核验",
                "review_status": "candidate",
                "reviewed_at": "",
                "notes": "；".join(claim_notes),
            })
            claim_index[claim_id] = {
                "claim_id": claim_id,
                "disclosure_id": candidate.disclosure_id,
                "statement": statement,
                "independent": candidate.disclosure_id,
                "origin_group": candidate.origin_group,
                "provenance_class": item.provenance_class,
                "publisher": publisher,
                "endpoint_id": endpoint.endpoint_id,
                "published_at": item.published_at,
                "disclosure_type": item.disclosure_type,
                "content_class": item.content_class,
                "subject_id": candidate.entity_ids[0] if candidate.entity_ids else publisher,
                "entity_ids": list(candidate.entity_ids),
                "low_confidence": candidate.low_confidence,
                "unresolved": candidate.unresolved,
                "notes": claim_notes,
            }
            queue_entries.append({
                "queue_type": "claim_candidate_pending_anchor_review",
                "claim_id": claim_id,
                "disclosure_id": candidate.disclosure_id,
                "endpoint_id": endpoint.endpoint_id,
                "item_url": item.url,
                "entity_id": publisher,
                "statement_kind": statement.statement_kind,
            })

    for claim_id in sorted(claim_index):
        detail_claims.append(_claim_detail(claim_index[claim_id]))

    # --- event candidate grouping ------------------------------------------
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for claim_id in sorted(claim_index):
        row = claim_index[claim_id]
        if row["unresolved"]:
            continue
        statement: ExtractedStatement = row["statement"]
        blocked = _permission_blocked(row["disclosure_type"], row["content_class"], statement)
        if blocked:
            failure("permission_denied", row["endpoint_id"], row["disclosure_id"], row["subject_id"],
                    f"{blocked}: {statement.signal_code} ({statement.lifecycle_stage})")
            continue
        key = (row["subject_id"], statement.event_category, statement.lifecycle_stage, row["published_at"])
        buckets[key].append(row)

    # Independent confirmation commonly appears days after the first-party
    # disclosure. Attach an independent-only bucket to the nearest first-party
    # bucket for the same subject/category/stage within 45 days. This produces
    # only a corroboration suggestion; human review still decides event identity.
    first_party_keys = [
        key for key, rows in buckets.items()
        if any(row["provenance_class"] == "first_party" for row in rows)
    ]
    for key in sorted(list(buckets)):
        rows = buckets.get(key, [])
        if not rows or any(row["provenance_class"] == "first_party" for row in rows):
            continue
        subject, category, stage, occurred = key
        candidates_for_merge = []
        for target in first_party_keys:
            if target[:3] != (subject, category, stage):
                continue
            distance = abs((date.fromisoformat(target[3]) - date.fromisoformat(occurred)).days)
            if distance <= 45:
                candidates_for_merge.append((distance, target[3], target))
        if candidates_for_merge:
            target = min(candidates_for_merge)[2]
            buckets[target].extend(rows)
            del buckets[key]

    for key in sorted(buckets):
        subject_id, category, stage, occurred = key
        rows = sorted(
            buckets[key],
            key=lambda row: (0 if row["provenance_class"] == "first_party" else 1,
                             row["published_at"], row["disclosure_id"], row["claim_id"]),
        )
        event_key = (subject_id, category, stage, occurred)
        if event_key in ledger["events"]:
            manifest("", rows[0]["endpoint_id"], "duplicate_event",
                     "same subject/category/stage/date already curated in events.csv")
            continue
        event_id = _stable_id("EC", subject_id, category, stage, occurred)
        program_id = f"PRGC_{_slug(subject_id)}_{_slug(category)}"
        first_party_rows = [row for row in rows if row["provenance_class"] == "first_party"]
        reporter = first_party_rows[0] if first_party_rows else rows[0]
        evidence: list[dict[str, Any]] = []
        counterparties: list[str] = []
        caveats: list[str] = []
        for row in rows:
            relationship = "reports" if row["claim_id"] == reporter["claim_id"] else "supports"
            independence = INDEPENDENCE_BY_PROVENANCE[row["provenance_class"]]
            evidence_id = _stable_id("VC", event_id, row["claim_id"], relationship)
            evidence_notes = "第一方材料不能作为独立证据" if independence == "first_party" else "不同 origin 的独立证据候选"
            evidence_rows.append({
                "evidence_id": evidence_id,
                "event_id": event_id,
                "event_claim_id": row["claim_id"],
                "relationship": relationship,
                "independence_class": independence,
                "origin_group": row["origin_group"],
                "notes": evidence_notes,
            })
            evidence.append({
                "evidence_id": evidence_id,
                "event_claim_id": row["claim_id"],
                "relationship": relationship,
                "independence_class": independence,
                "origin_group": row["origin_group"],
                "provenance_class": row["provenance_class"],
                "endpoint_id": row["endpoint_id"],
            })
            if independence != "first_party" and row["publisher"] != subject_id:
                counterparties.append(row["publisher"])
            if row["low_confidence"]:
                caveats.append(f"low_confidence_entity_mapping:{row['claim_id']}")
            if row["statement"].statement_kind == "forward_looking":
                caveats.append(f"forward_looking_not_realized:{row['claim_id']}")
        counterparty_ids = sorted(set(counterparties))
        first_party_origins = {
            item["origin_group"] for item in evidence
            if item["independence_class"] in {"first_party", "same_origin"}
            and item["relationship"] in {"reports", "supports"}
        }
        independent_origins = {
            item["origin_group"] for item in evidence
            if item["relationship"] in {"reports", "supports"}
            and item["independence_class"] in INDEPENDENT_CLASSES
            and item["origin_group"] not in first_party_origins
        }
        if first_party_origins and independent_origins:
            suggested, blocked_reason = "corroborated", ""
        elif not first_party_origins:
            suggested, blocked_reason = "asserted", "missing_first_party_asserted_origin"
        else:
            suggested, blocked_reason = "asserted", "independent_origin_required_for_corroboration"
        summary = f"{subject_id} {category}/{stage} 候选（{occurred}，自动发现待人工判定）"
        event_rows.append({
            "event_id": event_id,
            "program_id": program_id,
            "event_category": category,
            "lifecycle_stage": stage,
            "event_status": "asserted",
            "primary_subject_id": subject_id,
            "counterparty_ids": ";".join(counterparty_ids),
            "theme_ids": "",
            "occurred_start": occurred,
            "occurred_end": occurred,
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "",
            "target_market": "",
            "policy_jurisdiction": "",
            "summary": summary,
            "notes": "自动候选：event_status 固定为 asserted；corroborated 仅为建议且需人工批准",
        })
        detail_events.append({
            "event_id": event_id,
            "program_id": program_id,
            "event_category": category,
            "lifecycle_stage": stage,
            "event_status": "asserted",
            "suggested_event_status": suggested,
            "requires_human_approval": suggested != "asserted",
            "blocked_reason": blocked_reason,
            "corroboration_origins": {
                "first_party": sorted(first_party_origins),
                "independent": sorted(independent_origins),
            },
            "caveats": sorted(set(caveats)),
            "primary_subject_id": subject_id,
            "counterparty_ids": counterparty_ids,
            "occurred_start": occurred,
            "summary": summary,
            "evidence_candidate_ids": [item["evidence_id"] for item in evidence],
        })
        detail_evidence.extend(evidence)
        if suggested != "asserted":
            queue_entries.append({
                "queue_type": "corroboration_suggestion_pending_approval",
                "event_id": event_id,
                "suggested_event_status": suggested,
                "entity_id": subject_id,
                "detail": summary,
            })

    details = {
        "run_date": run_date,
        "endpoint_count": len(endpoints),
        "endpoint_ok": endpoint_stats["ok"],
        "endpoint_failed": endpoint_stats["failed"],
        "monitored_entity_count": len(monitored),
        "configured_entity_count": len(configured & monitored),
        "missing_endpoint_count": len(monitored - configured),
        "item_count": item_total,
        "decision_counts": dict(sorted(decision_counts.items())),
        "disclosure_candidates": detail_disclosures,
        "claim_candidates": detail_claims,
        "event_candidates": detail_events,
        "evidence_candidates": detail_evidence,
    }
    return RunOutcome(
        disclosure_rows=sorted(disclosure_rows, key=lambda row: row["disclosure_id"]),
        claim_rows=sorted(claim_rows, key=lambda row: row["event_claim_id"]),
        event_rows=sorted(event_rows, key=lambda row: row["event_id"]),
        evidence_rows=sorted(evidence_rows, key=lambda row: row["evidence_id"]),
        manifest_rows=sorted(manifest_rows, key=lambda row: (row["item_url"], row["endpoint_id"], row["decision"])),
        failure_rows=sorted(failure_rows, key=lambda row: (row["failure_type"], row["item_url"], row["detail"])),
        details=details,
        queue_entries=queue_entries,
    )


def _claim_detail(row: dict[str, Any]) -> dict[str, Any]:
    statement: ExtractedStatement = row["statement"]
    return {
        "claim_id": row["claim_id"],
        "disclosure_id": row["disclosure_id"],
        "claimant_entity_id": row["publisher"],
        "statement_kind": statement.statement_kind,
        "signal_code": statement.signal_code,
        "anchor": statement.anchor,
        "quote": statement.quote,
        "review_status": "candidate",
        "reviewed_at": "",
        "realized": statement.realized,
        "lifecycle_stage": statement.lifecycle_stage,
        "endpoint_id": row["endpoint_id"],
        "low_confidence": row["low_confidence"],
        "unresolved": row["unresolved"],
        "notes": list(row["notes"]),
    }


# --------------------------------------------------------------------------
# atomic state writing
# --------------------------------------------------------------------------


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="",
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False,
    )
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise


def _atomic_write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(fieldnames), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    _atomic_write_text(path, buffer.getvalue())


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


class _RunLock:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> "_RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise DailyDiscoveryError(
                f"daily discovery lock is held: {self.path}; another run is in progress"
            ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid()}, sort_keys=True))
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.path.unlink(missing_ok=True)


def _ensure_isolated_state_root(source_root: Path, state_root: Path) -> tuple[Path, Path]:
    source = source_root.resolve()
    state = state_root.resolve()
    calls_dir = (source / "calls").resolve()
    out_dir = (calls_dir / "out").resolve()
    # Most specific first: a state root under calls/out/ is also under the source
    # root, so the narrow message has to win.
    if state == out_dir or out_dir in state.parents:
        raise DailyDiscoveryError("state-root must not write into calls/out/")
    if state == calls_dir or calls_dir in state.parents:
        raise DailyDiscoveryError("state-root must not write into calls/")
    if state == source or source in state.parents:
        raise DailyDiscoveryError("state-root must sit outside the read-only source root")
    return source, state


def _queue_key(entry: dict[str, Any]) -> str:
    payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _build_queue(outcome: RunOutcome, run_date: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(outcome.queue_entries, key=lambda item: json.dumps(item, sort_keys=True)):
        key = _queue_key(entry)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"queue_key": key, **entry})
    return entries


def _queue_diff(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
    previous_keys = [entry["queue_key"] for entry in previous]
    current_keys = [entry["queue_key"] for entry in current]
    previous_set, current_set = set(previous_keys), set(current_keys)
    return {
        "added": [entry for entry in current if entry["queue_key"] not in previous_set],
        "removed": [entry for entry in previous if entry["queue_key"] not in current_set],
        "unchanged_count": len(previous_set & current_set),
        "previous_count": len(previous_keys),
        "current_count": len(current_keys),
    }


def _daily_report(outcome: RunOutcome, registry: EntityRegistry, run_date: str) -> str:
    details = outcome.details
    tiers: dict[str, int] = defaultdict(int)
    for entity_id in registry.monitored:
        tiers[registry.entities[entity_id].tier] += 1
    suggestions = [
        event for event in details["event_candidates"]
        if event["suggested_event_status"] != "asserted"
    ]
    failure_counts: dict[str, int] = defaultdict(int)
    for row in outcome.failure_rows:
        failure_counts[row["failure_type"]] += 1
    lines = [
        f"# 海外事件雷达日更镜像 {run_date}",
        "",
        "本产物只写独立 state_root；calls/*.csv、calls/out/ 与根 canonical 均为只读。",
        f"运行模式：{details.get('fetch_mode', 'unknown')}",
        "",
        "## 监控池并集",
        f"- 季度覆盖公司：{tiers['quarterly']}",
        f"- 事件监控实体：{tiers['watch']}",
        f"- 发现队列候选：{tiers['candidate']}",
        f"- 归一化监控主体：{details['monitored_entity_count']}；已配置：{details['configured_entity_count']}；缺端点：{details['missing_endpoint_count']}",
        f"- 声明端点：{details['endpoint_count']}（成功 {details['endpoint_ok']} / 失败 {details['endpoint_failed']} / 条目 {details['item_count']}）",
        "",
        "## 去重与候选",
    ]
    for decision, count in sorted(details["decision_counts"].items()):
        lines.append(f"- {decision}: {count}")
    lines.extend([
        f"- 披露候选：{len(outcome.disclosure_rows)}",
        f"- 原子主张候选：{len(outcome.claim_rows)}（全部 review_status=candidate）",
        f"- 事件候选：{len(outcome.event_rows)}（全部 event_status=asserted）",
        f"- 证据候选：{len(outcome.evidence_rows)}",
        f"- corroborated 建议：{len(suggestions)}（仍需人工批准，未写入任何正式事件状态）",
        "",
        "## 待人工处理",
    ])
    if failure_counts:
        for failure_type, count in sorted(failure_counts.items()):
            lines.append(f"- {failure_type}: {count}")
    else:
        lines.append("- 无未决事项")
    lines.extend([
        "",
        "## 事件候选明细",
    ])
    for event in details["event_candidates"]:
        lines.append(
            f"- {event['event_id']} {event['primary_subject_id']} {event['event_category']}"
            f"/{event['lifecycle_stage']} {event['occurred_start']}"
            f" | status=asserted | 建议={event['suggested_event_status']}"
            f" | {event['blocked_reason'] or 'first_party+independent origins'}"
        )
    lines.extend([
        "",
        "## 权限边界",
        "- 自动主张只能是 candidate；不得写 anchor_reviewed。",
        "- 自动事件默认至多 asserted；corroborated 只是建议，必须人工批准。",
        "- 第一方公告不是独立证据；同一底层公告的转载归入同一 origin group，不重复计票。",
        "- 技术博客/演示不能支撑量产、客户采用、订单规模、供货关系或需求规模。",
        "- forward-looking 不得写成已兑现。",
        "- 本命令不 promote、不改 canonical、不安装任何定时任务。",
        "",
    ])
    return "\n".join(lines)


# --------------------------------------------------------------------------
# public seam
# --------------------------------------------------------------------------


def run_daily_discovery(
    source_root: Path,
    state_root: Path,
    run_date: str,
    config_path: Path,
    fetcher: Any,
) -> dict[str, Any]:
    """Scan configured endpoints and write schema-shaped candidates to state_root."""
    _iso_date(run_date, "run_date", "daily discovery")
    source, state = _ensure_isolated_state_root(source_root, state_root)
    registry = load_entity_registry(source)
    ledger = load_ledger_index(source)
    endpoints = load_discovery_config(config_path, registry)
    with _RunLock(state / LOCK_NAME):
        outcome = _build_candidates(registry, ledger, endpoints, fetcher, run_date)
        outcome.details["fetch_mode"] = getattr(fetcher, "fetch_mode", "unknown")
        staging = state / STAGING_DIR / run_date
        staging.mkdir(parents=True, exist_ok=True)
        _atomic_write_csv(staging / "disclosure_candidates.csv",
                          FILES["disclosures.csv"], outcome.disclosure_rows)
        _atomic_write_csv(staging / "claim_candidates.csv",
                          FILES["event_claims.csv"], outcome.claim_rows)
        _atomic_write_csv(staging / "event_candidates.csv",
                          FILES["events.csv"], outcome.event_rows)
        _atomic_write_csv(staging / "evidence_candidates.csv",
                          FILES["event_evidence.csv"], outcome.evidence_rows)
        _atomic_write_csv(staging / "dedupe-manifest.csv", DEDUPE_FIELDS, outcome.manifest_rows)
        _atomic_write_csv(staging / "failures.csv", FAILURE_FIELDS, outcome.failure_rows)
        _atomic_write_json(staging / "candidates.json", outcome.details)
        _atomic_write_text(state / DAILY_DIR / f"{run_date}.txt", _daily_report(outcome, registry, run_date))

        current_queue = _build_queue(outcome, run_date)
        previous_path = state / "queue-latest.json"
        previous: list[dict[str, Any]] = []
        if previous_path.is_file():
            previous = json.loads(previous_path.read_text(encoding="utf-8"))["entries"]
        _atomic_write_json(state / "queue-prev.json", {"entries": previous})
        _atomic_write_json(state / "queue-latest.json", {"run_date": run_date, "entries": current_queue})
        _atomic_write_json(state / "queue-diff.json", _queue_diff(previous, current_queue))

        summary = {
            "run_date": run_date,
            "fetch_mode": outcome.details["fetch_mode"],
            "endpoint_count": outcome.details["endpoint_count"],
            "endpoint_failed": outcome.details["endpoint_failed"],
            "monitored_entity_count": outcome.details["monitored_entity_count"],
            "configured_entity_count": outcome.details["configured_entity_count"],
            "missing_endpoint_count": outcome.details["missing_endpoint_count"],
            "item_count": outcome.details["item_count"],
            "decision_counts": outcome.details["decision_counts"],
            "disclosure_candidates": len(outcome.disclosure_rows),
            "claim_candidates": len(outcome.claim_rows),
            "event_candidates": len(outcome.event_rows),
            "evidence_candidates": len(outcome.evidence_rows),
            "corroboration_suggestions": sum(
                1 for event in outcome.details["event_candidates"]
                if event["suggested_event_status"] != "asserted"
            ),
            "failure_types": dict(sorted(
                {row["failure_type"]: sum(1 for item in outcome.failure_rows
                                          if item["failure_type"] == row["failure_type"])
                 for row in outcome.failure_rows}.items()
            )),
            "promoted": 0,
            "queue_size": len(current_queue),
            "queue_added": len(_queue_diff(previous, current_queue)["added"]),
            "queue_removed": len(_queue_diff(previous, current_queue)["removed"]),
        }
        _atomic_write_json(staging / "run-summary.json", summary)
        return summary


def verify_staging(source_root: Path, state_root: Path, run_date: str) -> list[str]:
    """Read-only proof that staging maps onto the curated schema. Never promotes."""
    _iso_date(run_date, "run_date", "daily discovery verify")
    source, state = _ensure_isolated_state_root(source_root, state_root)
    staging = state / STAGING_DIR / run_date
    if not staging.is_dir():
        raise DailyDiscoveryError(f"no staging directory for {run_date}: {staging}")
    tables = {
        name: _read_staging(staging / name, schema)
        for name, schema in STAGING_TABLES.items()
    }
    for name, rows in tables.items():
        _check_ids(rows, FILES[STAGING_TABLES[name]][0], name)

    registry = load_entity_registry(source)
    disclosures = {row["disclosure_id"]: row for row in tables["disclosure_candidates.csv"]}
    claims = {row["event_claim_id"]: row for row in tables["claim_candidates.csv"]}
    events = {row["event_id"]: row for row in tables["event_candidates.csv"]}
    evidence = tables["evidence_candidates.csv"]
    details = json.loads((staging / "candidates.json").read_text(encoding="utf-8"))
    suggested = {
        event["event_id"]: event["suggested_event_status"]
        for event in details["event_candidates"]
    }

    for disclosure_id, row in disclosures.items():
        where = f"disclosure_candidates:{disclosure_id}"
        if row["publisher_entity_id"] not in registry.entities:
            raise DailyDiscoveryError(f"{where}: unknown publisher_entity_id")
        for name, enum_name in (
            ("disclosure_type", "disclosure_type"),
            ("content_class", "content_class"),
            ("provenance_class", "provenance_class"),
            ("retrieval_status", "retrieval_status"),
            ("processing_status", "processing_status"),
        ):
            if row[name] not in ENUMS[enum_name]:
                raise DailyDiscoveryError(f"{where}: invalid {name}={row[name]!r}")
        if not _url_ok(row["canonical_url"]):
            raise DailyDiscoveryError(f"{where}: invalid canonical_url")
        if not row["origin_group"]:
            raise DailyDiscoveryError(f"{where}: origin_group is required")
        if not row["content_hash"] or not row["published_at"] or not row["retrieved_at"]:
            raise DailyDiscoveryError(f"{where}: content_hash/published_at/retrieved_at are required")
        if row["reviewed_at"] or row["processing_status"] in {"anchor_reviewed", "no_relevant_claims"}:
            raise DailyDiscoveryError(f"{where}: automation cannot claim a human-reviewed state")

    for claim_id, row in claims.items():
        where = f"claim_candidates:{claim_id}"
        if row["disclosure_id"] not in disclosures:
            raise DailyDiscoveryError(f"{where}: broken disclosure reference")
        if row["claimant_entity_id"] not in registry.entities:
            raise DailyDiscoveryError(f"{where}: unknown claimant_entity_id")
        for name, enum_name in (
            ("claimant_role", "event_claimant_role"),
            ("statement_kind", "event_statement_kind"),
            ("review_status", "event_review_status"),
        ):
            if row[name] not in ENUMS[enum_name]:
                raise DailyDiscoveryError(f"{where}: invalid {name}={row[name]!r}")
        if row["review_status"] != "candidate" or row["reviewed_at"]:
            raise DailyDiscoveryError(f"{where}: automatic claims must stay candidate")
        if not row["quote"] or not row["anchor"]:
            raise DailyDiscoveryError(f"{where}: quote and anchor are required")

    support_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    for event_id, row in events.items():
        where = f"event_candidates:{event_id}"
        for name, enum_name in (
            ("event_category", "event_category"),
            ("lifecycle_stage", "lifecycle_stage"),
            ("event_status", "event_status"),
            ("date_precision", "date_precision"),
        ):
            if row[name] not in ENUMS[enum_name]:
                raise DailyDiscoveryError(f"{where}: invalid {name}={row[name]!r}")
        if row["primary_subject_id"] not in registry.entities:
            raise DailyDiscoveryError(f"{where}: unknown primary_subject_id")
        if row["event_status"] != "asserted":
            raise DailyDiscoveryError(f"{where}: automatic events cannot exceed asserted")
        if row["previous_event_id"]:
            raise DailyDiscoveryError(f"{where}: stage linkage is a human-gate decision")

    for row in evidence:
        where = f"evidence_candidates:{row['evidence_id']}"
        event = events.get(row["event_id"])
        claim = claims.get(row["event_claim_id"])
        if not event or not claim:
            raise DailyDiscoveryError(f"{where}: broken event/claim reference")
        if row["relationship"] not in ENUMS["event_relationship"]:
            raise DailyDiscoveryError(f"{where}: invalid relationship")
        if row["independence_class"] not in ENUMS["independence_class"]:
            raise DailyDiscoveryError(f"{where}: invalid independence_class")
        disclosure = disclosures[claim["disclosure_id"]]
        if row["origin_group"] != disclosure["origin_group"]:
            raise DailyDiscoveryError(f"{where}: origin_group differs from disclosure")
        allowed = PROVENANCE_ALLOWED_BY_INDEPENDENCE[row["independence_class"]]
        if disclosure["provenance_class"] not in allowed:
            raise DailyDiscoveryError(f"{where}: independence_class conflicts with disclosure provenance")
        if row["independence_class"] in INDEPENDENT_CLASSES and disclosure["provenance_class"] == "first_party":
            raise DailyDiscoveryError(f"{where}: first-party material cannot count as independent evidence")
        if row["relationship"] in {"reports", "supports"}:
            support_by_event[row["event_id"]].append({
                "independence_class": row["independence_class"],
                "origin_group": row["origin_group"],
                "statement_kind": claim["statement_kind"],
                "disclosure_type": disclosure["disclosure_type"],
                "content_class": disclosure["content_class"],
            })

    for event_id, supports in support_by_event.items():
        event = events[event_id]
        where = f"event_candidates:{event_id}"
        if event["lifecycle_stage"] in MATURE_COMMERCIAL_STAGES:
            if all(item["statement_kind"] == "forward_looking" for item in supports):
                raise DailyDiscoveryError(f"{where}: forward-looking claims alone cannot support a mature stage")
            if all(item["disclosure_type"] == "technical_blog" for item in supports):
                raise DailyDiscoveryError(f"{where}: technical blog alone cannot support a mature stage")
        if suggested.get(event_id) == "corroborated":
            first_party = {item["origin_group"] for item in supports
                           if item["independence_class"] in {"first_party", "same_origin"}}
            independent = {item["origin_group"] for item in supports
                           if item["independence_class"] in INDEPENDENT_CLASSES
                           and item["origin_group"] not in first_party}
            if not first_party or not independent:
                raise DailyDiscoveryError(f"{where}: corroboration suggestion lacks an independent origin")

    ledger_rows = {
        "disclosures.csv": len(_read_table(source / "calls" / "disclosures.csv", "disclosures.csv")),
        "event_claims.csv": len(_read_table(source / "calls" / "event_claims.csv", "event_claims.csv")),
        "events.csv": len(_read_table(source / "calls" / "events.csv", "events.csv")),
        "event_evidence.csv": len(_read_table(source / "calls" / "event_evidence.csv", "event_evidence.csv")),
    }
    suggestions = sum(1 for value in suggested.values() if value != "asserted")
    return [
        f"{len(disclosures)} disclosure candidates map onto calls/disclosures.csv "
        "(canonical URL, published/retrieved time, content hash, origin group, provenance)",
        f"{len(claims)} claim candidates map onto calls/event_claims.csv "
        "(all review_status=candidate, none anchor_reviewed)",
        f"{len(events)} event candidates map onto calls/events.csv "
        f"(all event_status=asserted; {suggestions} corroboration suggestion(s) pending human approval)",
        f"{len(evidence)} evidence candidates map onto calls/event_evidence.csv "
        "(origin groups match their disclosure; first-party never independent)",
        "curated ledger read-only: "
        + ", ".join(f"{name}={count}" for name, count in sorted(ledger_rows.items())),
        "verify never promotes: 0 rows written to calls/*.csv, calls/out/ or canonical files",
    ]


def _read_staging(path: Path, schema_name: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise DailyDiscoveryError(f"missing staging file: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FILES[schema_name]:
            raise DailyDiscoveryError(f"{path.name}: header must match calls/{schema_name}")
        return list(reader)


def _check_ids(rows: list[dict[str, str]], id_field: str, name: str) -> None:
    seen: set[str] = set()
    for row in rows:
        value = row[id_field]
        if not value:
            raise DailyDiscoveryError(f"{name}: empty {id_field}")
        if value in seen:
            raise DailyDiscoveryError(f"{name}: duplicate {id_field} {value}")
        seen.add(value)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Daily discovery mirror: read-only scanning, schema-shaped staging only"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="scan endpoints and write candidates to the state root")
    run_parser.add_argument("--source-root", required=True)
    run_parser.add_argument("--state-root", required=True)
    run_parser.add_argument("--date", required=True, help="run date, YYYY-MM-DD")
    run_parser.add_argument("--config", required=True, help="per-entity discovery endpoint config")
    run_parser.add_argument("--fixtures", help="offline fixture directory; omit for public HTTP")

    verify_parser = subparsers.add_parser("verify", help="read-only validation that staging maps to the schema")
    verify_parser.add_argument("--source-root", required=True)
    verify_parser.add_argument("--state-root", required=True)
    verify_parser.add_argument("--date", required=True, help="run date, YYYY-MM-DD")

    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            if args.fixtures:
                fetcher = FixtureFetcher(Path(args.fixtures))
            else:
                from .http_discovery import HttpFetcher
                fetcher = HttpFetcher(args.date)
            summary = run_daily_discovery(
                Path(args.source_root),
                Path(args.state_root),
                args.date,
                Path(args.config),
                fetcher,
            )
            print(f"OK: daily discovery {args.date}: "
                  f"{summary['disclosure_candidates']} disclosure / {summary['claim_candidates']} claim / "
                  f"{summary['event_candidates']} event / {summary['evidence_candidates']} evidence candidates")
            print(f"OK: promoted 0; corroboration suggestions {summary['corroboration_suggestions']} "
                  "await human approval")
            return 0
        for message in verify_staging(Path(args.source_root), Path(args.state_root), args.date):
            print(f"OK: {message}")
        return 0
    except (DailyDiscoveryError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
