from pathlib import Path
import sys
import yaml


PACKAGE = Path(__file__).resolve().parent
WORKSPACE = PACKAGE.parents[3]
DRAFT = PACKAGE / "route-chain-draft.yaml"
QUESTIONS = WORKSPACE / "research_questions.yaml"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


with DRAFT.open(encoding="utf-8") as handle:
    draft = yaml.safe_load(handle)
with QUESTIONS.open(encoding="utf-8") as handle:
    questions = yaml.safe_load(handle)

meta = draft["meta"]
required_false = [
    "canonical_write_performed",
    "coverage_status_changed",
    "formal_route_profile_created",
    "why_links_written",
    "confirmed_company_group_created",
]
if meta.get("mode") != "draft_only":
    fail("meta.mode must remain draft_only")
for field in required_false:
    if meta.get(field) is not False:
        fail(f"meta.{field} must be false")

question_ids = {
    item["id"]
    for section in ("questions", "why_questions")
    for item in questions.get(section, [])
}
used_question_ids = set(draft["knowledge_systems"]["route"]["axes"])
used_question_ids.update(draft["knowledge_systems"]["why_bridge"]["candidate_questions"])
for edge in draft["causal_chain_candidates"]:
    qid = edge.get("question_id") or edge.get("attachment_question_id")
    used_question_ids.add(qid)
unknown_qids = sorted(used_question_ids - question_ids)
if unknown_qids:
    fail(f"unknown question IDs: {unknown_qids}")

if draft["tradeoffs"]["product_power_observations"]["comparison_status"] != "not_comparable":
    fail("target/baseline product power must remain not_comparable")
if draft["physical_deltas"]["process"]["status"] != "UNKNOWN_COMPARATIVE_DELTA":
    fail("process comparative delta must remain UNKNOWN")
if draft["physical_deltas"]["equipment"]["status"] != "UNKNOWN_PRODUCTION_EQUIPMENT_DELTA":
    fail("production equipment delta must remain UNKNOWN")
if draft["company_service_evidence"]["exact_target_shipment"] != "UNKNOWN":
    fail("exact-target shipment must remain UNKNOWN")
if draft["company_service_evidence"]["exact_target_named_customer_adoption"] != "UNKNOWN":
    fail("exact-target named-customer adoption must remain UNKNOWN")

known_sources = set(draft["sources"])
referenced_sources = set()


def collect_sources(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence":
                if isinstance(child, list):
                    referenced_sources.update(child)
                else:
                    referenced_sources.add(child)
            else:
                collect_sources(child)
    elif isinstance(value, list):
        for child in value:
            collect_sources(child)


collect_sources(draft)
unknown_sources = sorted(referenced_sources - known_sources)
if unknown_sources:
    fail(f"unknown source IDs: {unknown_sources}")

missing_local = []
for source_id, source in draft["sources"].items():
    locators = source["locator"] if isinstance(source["locator"], list) else [source["locator"]]
    for locator in locators:
        if not str(locator).startswith(("http://", "https://")):
            candidate = WORKSPACE / locator
            if not candidate.exists():
                missing_local.append(f"{source_id}:{locator}")
if missing_local:
    fail(f"missing local source locators: {missing_local}")

print(
    "PASS: draft-only route chain is YAML-valid; question/source references resolve; "
    "promotion guards and UNKNOWN boundaries remain intact"
)
