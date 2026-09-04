"""CSV contracts and controlled vocabularies for the calls intelligence layer."""

FILES = {
    "universe.csv": (
        "company_id", "company_name", "role", "inclusion_reason", "enabled",
    ),
    "sources.csv": (
        "source_id", "company_id", "slot_label", "period_end", "source_scope",
        "material_type", "source_grade", "url", "local_path", "published_date",
        "accessed_date", "availability", "missing_reason", "acquisition_note",
    ),
    "claims.csv": (
        "claim_id", "source_id", "speaker", "speaker_role", "statement_type",
        "event_type", "side", "theme_id", "quote", "anchor", "review_status",
        "mapping_track", "cell_id", "route_item_id", "unmapped_theme",
        "unmapped_reason", "summary",
    ),
    "themes.csv": (
        "theme_id", "theme_type", "theme_name", "parent_theme_id",
        "affected_dimension", "bottleneck_status", "mapping_track", "cell_id",
        "route_item_id", "unmapped_reason", "application_demand", "required_metric",
        "critical_node", "limiting_factor", "constrained_outcome", "candidate_solution",
        "progress_gap", "feasibility", "scarcity", "substitutability",
    ),
    "validations.csv": (
        "validation_id", "theme_id", "claim_a_id", "claim_b_id", "relationship",
        "result_status", "rationale",
    ),
    "commitments.csv": (
        "commitment_id", "claim_id", "target", "due_date", "status",
        "evidence_source_id", "evidence_claim_id", "assessment",
    ),
    "solution_links.csv": (
        "link_id", "bottleneck_theme_id", "solution_theme_id", "required_capability",
        "point_id", "match_stage", "evidence_status", "missing_evidence", "conclusion",
    ),
    "constraint_requirements.csv": (
        "requirement_id", "theme_id", "cell_id", "route_item_id", "dimension",
        "metric_name", "comparator", "target_value", "unit", "evidence_claim_ids",
        "review_status", "notes",
    ),
    "point_metrics.csv": (
        "metric_id", "point_id", "metric_name", "value", "unit", "as_of",
        "review_status", "notes",
    ),
    "technology_feedback.csv": (
        "feedback_id", "technology_claim_id", "commercial_claim_id", "theme_id",
        "feedback_status", "evidence_status", "stage_before", "stage_after", "rationale",
    ),
    "watch_entities.csv": (
        "entity_id", "entity_name", "entity_type", "aliases", "inclusion_reason",
        "monitoring_status", "promoted_company_id", "source_ref", "notes",
    ),
    "company_candidates.csv": (
        "candidate_id", "entity_name", "entity_type", "suggested_role",
        "suggested_tier", "priority", "capability_scope", "inclusion_reason",
        "source_ref", "verification_status", "promoted_entity_id",
        "reviewed_at", "notes",
    ),
    "company_tier_reviews.csv": (
        "review_id", "candidate_id", "period_label", "published_date",
        "source_ref", "material_type", "signal_class", "signal_summary",
        "reviewed_at", "notes",
    ),
    "entity_relationships.csv": (
        "relationship_id", "subject_entity_id", "object_entity_id",
        "relationship_type", "effective_from", "effective_to", "source_ref",
        "review_status", "notes",
    ),
    "disclosures.csv": (
        "disclosure_id", "publisher_entity_id", "legacy_source_id", "title",
        "disclosure_type", "content_class", "provenance_class", "canonical_url",
        "local_path", "content_hash", "origin_group", "published_at", "updated_at",
        "discovered_at", "retrieved_at", "reviewed_at", "retrieval_status",
        "processing_status", "review_scope", "notes",
    ),
    "event_claims.csv": (
        "event_claim_id", "legacy_claim_id", "disclosure_id", "claimant_entity_id",
        "claimant_role", "statement_kind", "quote", "anchor", "summary",
        "review_status", "reviewed_at", "notes",
    ),
    "events.csv": (
        "event_id", "program_id", "event_category", "lifecycle_stage", "event_status",
        "primary_subject_id", "counterparty_ids", "theme_ids", "occurred_start",
        "occurred_end", "date_precision", "previous_event_id", "site_country",
        "target_market", "policy_jurisdiction", "summary", "notes",
    ),
    "event_evidence.csv": (
        "evidence_id", "event_id", "event_claim_id", "relationship",
        "independence_class", "origin_group", "notes",
    ),
}

ENUMS = {
    "role": {"core_peer", "upstream_enabler", "system_vendor", "downstream"},
    "enabled": {"yes", "no"},
    "source_scope": {"quarterly", "interquarter"},
    "material_type": {"unknown", "transcript", "prepared_remarks", "earnings_presentation", "webcast_transcript", "earnings_release", "regulatory_filing", "official_release", "official_technical_blog"},
    "source_grade": {"unknown", "A", "B", "C"},
    "availability": {"available", "not_collected", "unavailable"},
    "speaker_role": {"management", "analyst", "operator", "corporate_author"},
    "statement_type": {"fact", "forward_looking", "analyst_question", "technical_claim", "technical_demo"},
    "event_type": {"unknown", "announced", "sampling", "qualifying", "volume_order", "first_shipment", "ramping", "scaled", "demonstrated", "delayed", "withdrawn"},
    "side": {"supply", "demand", "both", "unknown"},
    "review_status": {"candidate", "reviewed", "rejected"},
    "mapping_track": {"canonical", "unmapped"},
    "theme_type": {"limited_demand", "bottleneck", "solution", "topic"},
    "affected_dimension": {"performance", "power_thermal", "cost", "yield_capacity", "reliability_operations", "standards_compatibility_certification", "unknown"},
    "bottleneck_status": {"candidate", "binding", "solution_emerging", "partially_relieved", "industry_resolved", "shifted", "not_applicable"},
    "evidence_state": {"verified", "partially_supported", "company_claim_only", "conflicting", "insufficient"},
    "relationship": {"supports", "contradicts", "independent", "same_source", "insufficient"},
    "commitment_status": {"pending", "fulfilled", "partially_fulfilled", "delayed", "withdrawn", "not_observed"},
    "match_stage": {"node_overlap", "mechanism_match", "metric_match", "customer_validation", "volume_validation"},
    "feedback_status": {"confirmed", "partially_confirmed", "not_mentioned", "contradicted", "pending"},
    "entity_type": {"company", "regulator", "government", "customer", "partner", "other"},
    "monitoring_status": {"active", "paused", "promoted"},
    "suggested_tier": {"quarterly", "watch"},
    "candidate_priority": {"P1", "P2", "P3"},
    "candidate_verification_status": {
        "discovered", "source_verified", "promotion_ready", "promoted", "rejected",
    },
    "tier_review_signal_class": {
        "direct_optical", "adjacent_segment", "no_relevant_signal",
    },
    "entity_relationship_type": {
        "parent_of", "subsidiary_of", "acquired_by", "brand_of",
        "predecessor_of", "business_transferred_to",
    },
    "entity_relationship_review_status": {"candidate", "reviewed", "rejected"},
    "disclosure_type": {"official_release", "regulatory_filing", "technical_blog", "product_page", "datasheet", "customer_release", "government_record", "media", "other"},
    "content_class": {"technical_disclosure", "demonstration_disclosure", "corporate_narrative", "commercial_disclosure", "regulatory_record"},
    "provenance_class": {"first_party", "counterparty", "regulator", "government", "third_party", "unknown"},
    "retrieval_status": {"discovered", "retrieved", "unavailable", "failed"},
    "processing_status": {"unprocessed", "candidate_extracted", "anchor_reviewed", "no_relevant_claims", "rejected"},
    "event_claimant_role": {"management", "corporate_author", "corporate_disclosure", "customer", "counterparty", "regulator", "other"},
    "event_statement_kind": {"fact_assertion", "forward_looking", "technical_claim", "technical_demo", "corporate_narrative"},
    "event_review_status": {"candidate", "anchor_reviewed", "rejected"},
    "event_category": {"product_stage", "capacity_constraint", "commercial_adoption", "capital_relationship", "supply_chain_arrangement", "policy_market_access"},
    "lifecycle_stage": {"announced", "demonstrated", "sampling", "qualifying", "volume_order", "first_shipment", "ramping", "scaled", "delayed", "withdrawn", "not_applicable"},
    "event_status": {"asserted", "corroborated", "contradicted", "corrected", "withdrawn"},
    "date_precision": {"exact", "month", "quarter", "window", "unknown"},
    "event_relationship": {"reports", "supports", "contradicts", "corrects", "withdraws"},
    "independence_class": {"same_origin", "first_party", "counterparty", "regulator", "observable_result", "third_party"},
}

PANORAMA_FIELDS = (
    "theme_id", "theme_type", "theme_name", "cell_id", "route_item_id",
    "bottleneck_status", "feasibility", "scarcity", "substitutability",
    "demand_evidence", "supply_evidence", "company_progress", "canonical_point_ids",
    "missing_evidence", "source_ids", "as_of",
)

CANONICAL_FILES = (
    "tree.yaml", "knowledge.yaml", "points.csv", "edges.csv", "route_bom.csv",
    "capability_details.csv", "corpus/_frozen.csv",
)
