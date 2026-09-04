#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Industry-chain v2 CSV model validator (Python standard library only).

Validates the canonical CSV files described in ``schema/CONTRACT.md``.

Checks performed
----------------
* Header / field presence            (exact column set per table)
* ID prefix + intra-file uniqueness   (SN-/SE-/ORG-/CAP-/TR-/EV-/GAP-)
* Enumerations                        (node_type, relation_type, status, ...)
* Legal relations                     (source -> target type table in CONTRACT)
* Layer coherence                    (part_of must not point to a child node)
* References / orphans               (edges, capabilities, trades, gaps, evidence)
* Evidence-use matching              (structure / capability / trade must match)
* Importance discipline              (CONTRACT §8)
* State-machine invariants           (verified needs evidence, resolved needs
                                       evidence, capability review states, ...)

The validator is snapshot based: it checks that a record *in its current state*
satisfies the legal-transition *endpoints* defined by the contract (e.g. a node
may not claim ``status=verified`` without a supporting structure evidence). It
cannot observe the history of transitions; that is by design.

Exit code is non-zero when at least one error is found.
"""

import argparse
import csv
import json
import os
import sys

# --------------------------------------------------------------------------
# Schema constants (straight from schema/CONTRACT.md)
# --------------------------------------------------------------------------

NODE_TYPES = {
    "application", "product_route", "function", "component",
    "material", "process", "equipment_category",
}

# relation_type -> (allowed source node_types, allowed target node_types)
#   None means a special rule implemented in relation_legal().
RELATION_RULES = {
    "drives":         ({"application"}, {"product_route"}),
    "implements":     ({"product_route"}, {"function"}),
    "requires":       ({"product_route", "function"}, {"component", "material"}),
    "uses_process":   ({"product_route", "component"}, {"process"}),
    "uses_material":  ({"component", "process"}, {"material"}),
    "enabled_by":     ({"process"}, {"equipment_category"}),
    "precedes":       ({"process"}, {"process"}),
    "alternative_to": None,   # same node_type on both ends
    "part_of":        None,   # same type OR a strictly higher-level node
}

# Relation types that belong to the *mandatory structure skeleton* used by the
# IMP_SC_NOT_MANDATORY reachability check (CONTRACT §8 discipline). A
# structural_critical node is valid only if it is reachable from some
# product_route by walking these edges while they are marked
# requiredness='mandatory' (and their route_scope is 'all' or the route being
# traversed). ``drives`` is handled separately in reverse to locate the
# application that drives a route.
SC_PROP_RELATIONS = {
    "implements", "requires", "uses_process", "uses_material",
    "part_of", "precedes", "enabled_by",
}

REQUIREDNESS = {"mandatory", "route_specific", "optional", "unknown"}
ORG_TYPES = {"company", "institute", "standards_body", "customer", "distributor"}
CAPABILITY_STATUS = {
    "production", "sampling", "development", "planned",
    "agent_or_distributor", "historical", "unknown",
}
NODE_STATUS = {"proposed", "admitted", "verified", "deprecated"}
CAP_REVIEW_STATUS = {
    "proposed", "evidenced", "reviewed", "admitted", "rejected", "stale",
}
EVIDENCE_USE = {"structure", "capability", "trade"}
SOURCE_TIER = {"T1", "T2", "T3"}
STANCE = {"standard", "issuer_self", "counterparty", "regulator", "third_party"}
VERDICT = {"supports", "partial", "conflicts", "inaccessible", "pending"}
GAP_TYPE = {
    "structure_gap", "player_gap", "capability_gap",
    "trade_gap", "currentness_gap", "comparability_gap",
}
PRIORITY = {"P0", "P1", "P2", "monitor"}
GAP_STATUS = {
    "identified", "scoped", "researching", "evidenced",
    "resolved", "blocked", "out_of_scope",
}
IMPORTANCE_CLASS = {
    "structural_critical", "bottleneck_candidate",
    "enabling", "supporting", "unknown",
}
IMPORTANCE_CONF = {"verified", "hypothesis", "unknown"}
# Trade edge grade (from AGENTS.md four-tier admission discipline; not
# enumerated in CONTRACT, so only validated when present).
GRADE = {"real", "half", "inferred", "forbidden"}

ID_PREFIXES = {
    "structure_nodes": "SN-",
    "structure_edges": "SE-",
    "organizations": "ORG-",
    "capabilities": "CAP-",
    "trade_observations": "TR-",
    "evidence": "EV-",
    "gaps": "GAP-",
}
ID_COLUMN = {
    "structure_nodes": "node_id",
    "structure_edges": "edge_id",
    "organizations": "org_id",
    "capabilities": "capability_id",
    "trade_observations": "observation_id",
    "evidence": "evidence_id",
    "gaps": "gap_id",
}
EXPECTED_HEADERS = {
    "structure_nodes": [
        "node_id", "node_type", "name_zh", "name_en", "definition", "status",
        "importance_class", "importance_confidence", "importance_basis",
        "evidence_ids", "as_of", "notes",
    ],
    "structure_edges": [
        "edge_id", "source_node_id", "target_node_id", "relation_type",
        "route_scope", "requiredness", "evidence_ids", "notes",
    ],
    "organizations": [
        "org_id", "canonical_name", "org_type", "country", "identifiers",
        "aliases", "status", "notes",
    ],
    "capabilities": [
        "capability_id", "org_id", "node_id", "capability_status",
        "route_scope", "evidence_ids", "as_of", "review_status", "notes",
    ],
    "trade_observations": [
        "observation_id", "supplier_org_id", "customer_org_id",
        "anonymous_endpoint", "product_or_node_id", "period", "amount_or_share",
        "evidence_ids", "grade", "review_status", "notes",
    ],
    "evidence": [
        "evidence_id", "evidence_use", "source_tier", "title", "publisher",
        "url", "publication_date", "retrieved_at", "as_of", "quote", "stance",
        "verdict", "notes",
    ],
    "gaps": [
        "gap_id", "node_id", "route_scope", "gap_type", "priority", "status",
        "reason", "next_question", "completion_condition", "owner",
        "evidence_ids", "updated_at", "notes",
    ],
}

# Expected evidence_use for each table that references evidence.
EXPECTED_EVIDENCE_USE = {
    "structure_nodes": "structure",
    "structure_edges": "structure",
    "capabilities": "capability",
    "trade_observations": "trade",
}

# Structure level (for layer-coherence checks). Lower = higher in the stack.
LEVEL = {
    "application": 0,
    "product_route": 1,
    "function": 2,
    "component": 3,
    "material": 3,
    "process": 3,
    "equipment_category": 3,
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def split_multi(value):
    """Split a semicolon-separated multi-value field into a clean list."""
    if value is None:
        return []
    text = value.strip()
    if text == "":
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def level_of(node_type):
    return LEVEL.get(node_type, 99)


def route_applies(route_scope, route_id):
    """Whether a semicolon-delimited route_scope applies to route_id."""
    scopes = split_multi(route_scope)
    return not scopes or "all" in scopes or route_id in scopes


def sc_mandatory_reachable(node_type, edges):
    """Return the set of structure-node ids that lie on the mandatory
    structure skeleton of *some* product_route.

    Reachability starts from every ``product_route`` (each route is itself its
    own seed) and, via the reverse of ``drives``, from the application that
    drives it. It then propagates forward along the mandatory structure edges
    listed in ``SC_PROP_RELATIONS``. An edge participates only when its
    ``requiredness == 'mandatory'`` and its semicolon-delimited
    ``route_scope`` contains ``'all'`` or the route currently being traversed
    (CONTRACT route_scope discipline). This lets ``structural_critical`` sit on
    application / product_route / function / process / equipment_category
    nodes instead of only on direct mandatory ``requires`` targets.
    """
    routes = [nid for nid, t in node_type.items() if t == "product_route"]
    if not routes:
        return set()

    # adjacency: source -> list of (target, requiredness, route_scope).
    # ``part_of`` is represented child -> parent in the contract, so mandatory
    # membership must also be traversable parent -> child when expanding a
    # route's process/component hierarchy.
    fwd = {}
    # reverse drives: route(target) -> list of (application source, route_scope)
    rev_drives = {}
    for e in edges:
        rt = (e.get("relation_type") or "").strip()
        s = (e.get("source_node_id") or "").strip()
        t = (e.get("target_node_id") or "").strip()
        req = (e.get("requiredness") or "").strip()
        rscope = (e.get("route_scope") or "").strip()
        if rt in SC_PROP_RELATIONS:
            fwd.setdefault(s, []).append((t, req, rscope))
            if rt == "part_of":
                fwd.setdefault(t, []).append((s, req, rscope))
        elif rt == "drives":
            rev_drives.setdefault(t, []).append((s, rscope))

    reachable = set()
    for R in routes:
        seen = {R}
        stack = [R]
        # seed the application(s) that drive this route (reverse drives)
        for (app, rscope) in rev_drives.get(R, []):
            if route_applies(rscope, R) and app not in seen:
                seen.add(app)
                stack.append(app)
        while stack:
            u = stack.pop()
            for (tgt, req, rscope) in fwd.get(u, []):
                if req == "mandatory" and route_applies(rscope, R) and tgt not in seen:
                    seen.add(tgt)
                    stack.append(tgt)
        reachable |= seen
    return reachable


def relation_legal(relation_type, src_type, tgt_type):
    """True if the relation is legal for the given endpoint node types."""
    rule = RELATION_RULES.get(relation_type)
    if rule is None:
        if relation_type == "alternative_to":
            return src_type == tgt_type
        if relation_type == "part_of":
            # same type, or target is a strictly higher-level structure node
            return src_type == tgt_type or level_of(tgt_type) < level_of(src_type)
        return False
    src_ok, tgt_ok = rule
    return src_type in src_ok and tgt_type in tgt_ok


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader), reader.fieldnames or []


def load_dataset(directory):
    """Read every known canonical CSV present under *directory*."""
    dataset = {}
    for name in EXPECTED_HEADERS:
        path = os.path.join(directory, name + ".csv")
        if os.path.exists(path):
            rows, fieldnames = read_csv(path)
            dataset[name] = (fieldnames, rows)
    return dataset


# --------------------------------------------------------------------------
# Core validation
# --------------------------------------------------------------------------

def validate_dataset(dataset, source="dataset"):
    """Validate an in-memory dataset.

    *dataset* maps table name -> (fieldnames, rows).
    Returns (errors, warnings); each entry is a dict with keys
    code / severity / message / file / row.
    """
    errors = []
    warnings = []

    def err(code, message, file=None, row=None):
        errors.append({"code": code, "severity": "error",
                       "message": message, "file": file, "row": row})

    def warn(code, message, file=None, row=None):
        warnings.append({"code": code, "severity": "warning",
                         "message": message, "file": file, "row": row})

    present = {k: v for k, v in dataset.items() if v is not None}

    # --- 1. headers -------------------------------------------------------
    for name, (fieldnames, _rows) in present.items():
        exp = EXPECTED_HEADERS.get(name)
        if exp is None:
            continue
        fn = fieldnames or []
        missing = [c for c in exp if c not in fn]
        extra = [c for c in fn if c not in exp]
        if missing:
            err("HEADER_MISSING", "%s: missing columns %s" % (name, missing), name)
        if extra:
            err("HEADER_EXTRA", "%s: unexpected columns %s" % (name, extra), name)

    # --- 2. ID prefix + intra-file uniqueness -----------------------------
    id_sets = {}
    for name, (fieldnames, rows) in present.items():
        if name not in ID_COLUMN:
            continue
        col = ID_COLUMN[name]
        prefix = ID_PREFIXES[name]
        seen = {}
        ids = []
        for i, row in enumerate(rows, 1):
            val = (row.get(col) or "").strip()
            if val == "":
                err("ID_EMPTY", "%s row %d: empty %s" % (name, i, col), name, i)
                continue
            if not val.startswith(prefix):
                err("ID_PREFIX",
                    "%s row %d: %s=%s must start with %s"
                    % (name, i, col, val, prefix), name, i)
            if val in seen:
                err("ID_DUP",
                    "%s: duplicate %s=%s (rows %d,%d)"
                    % (name, col, val, seen[val], i), name, i)
            else:
                seen[val] = i
            ids.append(val)
        id_sets[name] = set(ids)

    node_ids = id_sets.get("structure_nodes", set())
    org_ids = id_sets.get("organizations", set())
    ev_ids = id_sets.get("evidence", set())

    # node_type + route maps (needed by relation & importance checks)
    node_type = {}
    for (_fn, rows) in [present.get("structure_nodes", (None, []))]:
        for row in rows:
            nid = (row.get("node_id") or "").strip()
            node_type[nid] = (row.get("node_type") or "").strip()
    route_ids = {nid for nid, t in node_type.items() if t == "product_route"}

    # --- 3. evidence table ------------------------------------------------
    ev_use = {}
    ev_verdict = {}
    if "evidence" in present:
        for i, row in enumerate(present["evidence"][1], 1):
            use = (row.get("evidence_use") or "").strip()
            if use not in EVIDENCE_USE:
                err("ENUM", "evidence row %d: bad evidence_use=%s" % (i, use),
                    "evidence", i)
            tier = (row.get("source_tier") or "").strip()
            if tier not in SOURCE_TIER:
                err("ENUM", "evidence row %d: bad source_tier=%s" % (i, tier),
                    "evidence", i)
            stance = (row.get("stance") or "").strip()
            if stance not in STANCE:
                err("ENUM", "evidence row %d: bad stance=%s" % (i, stance),
                    "evidence", i)
            verdict = (row.get("verdict") or "").strip()
            if verdict not in VERDICT:
                err("ENUM", "evidence row %d: bad verdict=%s" % (i, verdict),
                    "evidence", i)
            url = (row.get("url") or "").strip()
            quote = (row.get("quote") or "").strip()
            retrieved = (row.get("retrieved_at") or "").strip()
            if verdict != "inaccessible" and url == "":
                err("EVID_NO_URL",
                    "evidence row %d: verdict=%s but url empty" % (i, verdict),
                    "evidence", i)
            if verdict in {"supports", "partial", "conflicts"} and (
                    quote == "" or retrieved == ""):
                err("EVID_FACT_INCOMPLETE",
                    "evidence row %d: verdict=%s requires quote+retrieved_at (四件套)"
                    % (i, verdict), "evidence", i)
            eid = (row.get("evidence_id") or "").strip()
            ev_use[eid] = use
            ev_verdict[eid] = verdict

    # --- 4. structure_nodes (types, importance, status) -------------------
    if "structure_nodes" in present:
        for i, row in enumerate(present["structure_nodes"][1], 1):
            nt = (row.get("node_type") or "").strip()
            if nt not in NODE_TYPES:
                err("ENUM", "structure_nodes row %d: bad node_type=%s" % (i, nt),
                    "structure_nodes", i)
            st = (row.get("status") or "").strip()
            if st not in NODE_STATUS:
                err("ENUM", "structure_nodes row %d: bad status=%s" % (i, st),
                    "structure_nodes", i)
            ic = (row.get("importance_class") or "").strip()
            if ic not in IMPORTANCE_CLASS:
                err("ENUM",
                    "structure_nodes row %d: bad importance_class=%s" % (i, ic),
                    "structure_nodes", i)
            conf = (row.get("importance_confidence") or "").strip()
            if conf not in IMPORTANCE_CONF:
                err("ENUM",
                    "structure_nodes row %d: bad importance_confidence=%s"
                    % (i, conf), "structure_nodes", i)

            # 4a. importance discipline (CONTRACT §8)
            if ic != "" and ic != "unknown" and conf == "unknown":
                err("IMP_NO_BASIS",
                    "structure_nodes row %d: importance_class=%s but "
                    "confidence=unknown (no basis may upgrade from unknown)"
                    % (i, ic), "structure_nodes", i)
            if ic == "bottleneck_candidate":
                if conf not in ("verified", "hypothesis"):
                    err("IMP_BN_CONF",
                        "structure_nodes row %d: bottleneck_candidate needs "
                        "verified/hypothesis, got %s" % (i, conf),
                        "structure_nodes", i)
                elif conf == "verified":
                    ok = False
                    for e in split_multi(row.get("evidence_ids")):
                        if (e in ev_use and ev_use[e] == "structure"
                                and ev_verdict.get(e) in {"supports", "partial"}):
                            ok = True
                            break
                    if not ok:
                        err("IMP_BN_EVID",
                            "structure_nodes row %d: bottleneck_candidate verified "
                            "needs structure evidence with supports/partial verdict"
                            % i, "structure_nodes", i)
                elif conf == "hypothesis":
                    basis = (row.get("importance_basis") or "").strip()
                    notes = (row.get("notes") or "").strip()
                    if basis == "" and notes == "":
                        err("IMP_BN_HYP",
                            "structure_nodes row %d: hypothesis needs basis text "
                            "in importance_basis or notes" % i,
                            "structure_nodes", i)

            # 4b. status-machine invariant: verified needs structure evidence
            if st == "verified":
                ok = False
                for e in split_multi(row.get("evidence_ids")):
                    if (e in ev_use and ev_use[e] == "structure"
                            and ev_verdict.get(e) in {"supports", "partial"}):
                        ok = True
                        break
                if not ok:
                    err("STATE_VERIFIED_NO_EVID",
                        "structure_nodes row %d: status=verified requires "
                        "structure evidence with supports/partial verdict"
                        % i, "structure_nodes", i)

            # 4c. evidence-use matching for this node's evidence
            for e in split_multi(row.get("evidence_ids")):
                if e == "":
                    continue
                if e not in ev_ids:
                    err("REF_ORPHAN",
                        "structure_nodes row %d: evidence %s not found" % (i, e),
                        "structure_nodes", i)
                elif ev_use.get(e) != "structure":
                    err("EVID_USE_MISMATCH",
                        "structure_nodes row %d: evidence %s use=%s != structure"
                        % (i, e, ev_use.get(e)), "structure_nodes", i)

    # --- 5. structure_edges (relation legality, references) ---------------
    if "structure_edges" in present:
        for i, row in enumerate(present["structure_edges"][1], 1):
            rt = (row.get("relation_type") or "").strip()
            if rt not in RELATION_RULES:
                err("ENUM",
                    "structure_edges row %d: bad relation_type=%s" % (i, rt),
                    "structure_edges", i)
            src = (row.get("source_node_id") or "").strip()
            tgt = (row.get("target_node_id") or "").strip()
            if src and src not in node_ids:
                err("REF_ORPHAN",
                    "structure_edges row %d: source %s not found" % (i, src),
                    "structure_edges", i)
            if tgt and tgt not in node_ids:
                err("REF_ORPHAN",
                    "structure_edges row %d: target %s not found" % (i, tgt),
                    "structure_edges", i)
            req = (row.get("requiredness") or "").strip()
            if req != "" and req not in REQUIREDNESS:
                err("ENUM",
                    "structure_edges row %d: bad requiredness=%s" % (i, req),
                    "structure_edges", i)
            if src in node_ids and tgt in node_ids and rt in RELATION_RULES:
                st_ = node_type.get(src)
                tt = node_type.get(tgt)
                if not relation_legal(rt, st_, tt):
                    if rt == "part_of" and level_of(tt) > level_of(st_):
                        err("LAYER_MIX",
                            "structure_edges row %d: part_of from %s to child %s "
                            "mixes layers" % (i, st_, tt),
                            "structure_edges", i)
                    else:
                        err("REL_ILLEGAL",
                            "structure_edges row %d: %s %s->%s not allowed"
                            % (i, rt, st_, tt), "structure_edges", i)
            for e in split_multi(row.get("evidence_ids")):
                if e == "":
                    continue
                if e not in ev_ids:
                    err("REF_ORPHAN",
                        "structure_edges row %d: evidence %s not found" % (i, e),
                        "structure_edges", i)
                elif ev_use.get(e) != "structure":
                    err("EVID_USE_MISMATCH",
                        "structure_edges row %d: evidence %s use=%s != structure"
                        % (i, e, ev_use.get(e)), "structure_edges", i)

    # --- 5b. importance: structural_critical must sit on the mandatory
    #         structure skeleton of some route --------------------------
    if "structure_nodes" in present and "structure_edges" in present:
        sc_nodes = {
            (row.get("node_id") or "").strip()
            for row in present["structure_nodes"][1]
            if (row.get("importance_class") or "").strip() == "structural_critical"
        }
        if sc_nodes:
            reachable = sc_mandatory_reachable(
                node_type, present["structure_edges"][1])
            for nid in sc_nodes:
                if nid not in reachable:
                    err("IMP_SC_NOT_MANDATORY",
                        "structure_nodes: structural_critical %s is not "
                        "reachable from any product_route via mandatory "
                        "structure edges (implements/requires/uses_process/"
                        "uses_material/part_of/precedes/enabled_by, plus "
                        "reverse drives to application; route_scope must be "
                        "'all' or the matching route)" % nid,
                        "structure_nodes")

    # --- 6. capabilities --------------------------------------------------
    if "capabilities" in present:
        for i, row in enumerate(present["capabilities"][1], 1):
            oid = (row.get("org_id") or "").strip()
            nid = (row.get("node_id") or "").strip()
            if oid and oid not in org_ids:
                err("REF_ORPHAN",
                    "capabilities row %d: org %s not found" % (i, oid),
                    "capabilities", i)
            if nid and nid not in node_ids:
                err("REF_ORPHAN",
                    "capabilities row %d: node %s not found" % (i, nid),
                    "capabilities", i)
            cs = (row.get("capability_status") or "").strip()
            if cs not in CAPABILITY_STATUS:
                err("ENUM",
                    "capabilities row %d: bad capability_status=%s" % (i, cs),
                    "capabilities", i)
            rs = (row.get("review_status") or "").strip()
            if rs != "" and rs not in CAP_REVIEW_STATUS:
                err("ENUM",
                    "capabilities row %d: bad review_status=%s" % (i, rs),
                    "capabilities", i)
            if rs in {"evidenced", "reviewed", "admitted", "rejected", "stale"}:
                ok = any(
                    e in ev_use and ev_use[e] == "capability"
                    for e in split_multi(row.get("evidence_ids"))
                )
                if not ok:
                    err("STATE_CAP_NO_EVID",
                        "capabilities row %d: review_status=%s requires "
                        "capability evidence" % (i, rs), "capabilities", i)
            for e in split_multi(row.get("evidence_ids")):
                if e == "":
                    continue
                if e not in ev_ids:
                    err("REF_ORPHAN",
                        "capabilities row %d: evidence %s not found" % (i, e),
                        "capabilities", i)
                elif ev_use.get(e) != "capability":
                    err("EVID_USE_MISMATCH",
                        "capabilities row %d: evidence %s use=%s != capability"
                        % (i, e, ev_use.get(e)), "capabilities", i)

    # --- 7. trade_observations -------------------------------------------
    if "trade_observations" in present:
        for i, row in enumerate(present["trade_observations"][1], 1):
            sup = (row.get("supplier_org_id") or "").strip()
            cus = (row.get("customer_org_id") or "").strip()
            anon = (row.get("anonymous_endpoint") or "").strip()
            if sup and sup not in org_ids:
                err("REF_ORPHAN",
                    "trade_observations row %d: supplier %s not found" % (i, sup),
                    "trade_observations", i)
            if cus and cus not in org_ids:
                err("REF_ORPHAN",
                    "trade_observations row %d: customer %s not found" % (i, cus),
                    "trade_observations", i)
            if anon != "" and (sup != "" or cus != ""):
                err("TRADE_ANON_FAB",
                    "trade_observations row %d: anonymous_endpoint set but org "
                    "ids present (fabricated org_id)" % i, "trade_observations", i)
            pn = (row.get("product_or_node_id") or "").strip()
            if pn and pn not in node_ids:
                err("REF_ORPHAN",
                    "trade_observations row %d: product_or_node_id %s not found"
                    % (i, pn), "trade_observations", i)
            g = (row.get("grade") or "").strip()
            if g != "" and g not in GRADE:
                err("ENUM",
                    "trade_observations row %d: bad grade=%s (allowed %s)"
                    % (i, g, sorted(GRADE)), "trade_observations", i)
            for e in split_multi(row.get("evidence_ids")):
                if e == "":
                    continue
                if e not in ev_ids:
                    err("REF_ORPHAN",
                        "trade_observations row %d: evidence %s not found"
                        % (i, e), "trade_observations", i)
                elif ev_use.get(e) != "trade":
                    err("EVID_USE_MISMATCH",
                        "trade_observations row %d: evidence %s use=%s != trade"
                        % (i, e, ev_use.get(e)), "trade_observations", i)

    # --- 8. gaps ----------------------------------------------------------
    if "gaps" in present:
        for i, row in enumerate(present["gaps"][1], 1):
            gt = (row.get("gap_type") or "").strip()
            if gt not in GAP_TYPE:
                err("ENUM", "gaps row %d: bad gap_type=%s" % (i, gt), "gaps", i)
            pr = (row.get("priority") or "").strip()
            if pr not in PRIORITY:
                err("ENUM", "gaps row %d: bad priority=%s" % (i, pr), "gaps", i)
            st = (row.get("status") or "").strip()
            if st not in GAP_STATUS:
                err("ENUM", "gaps row %d: bad status=%s" % (i, st), "gaps", i)
            nid = (row.get("node_id") or "").strip()
            if nid and nid not in node_ids:
                err("GAP_ORPHAN",
                    "gaps row %d: node %s not found" % (i, nid), "gaps", i)
            rs = (row.get("route_scope") or "").strip()
            if rs and (rs not in node_ids or node_type.get(rs) != "product_route"):
                err("GAP_BAD_ROUTE",
                    "gaps row %d: route_scope %s not a product_route node "
                    "(comparability denominator missing)" % (i, rs),
                    "gaps", i)
            if st == "resolved" and not split_multi(row.get("evidence_ids")):
                err("GAP_RESOLVED_NO_EVID",
                    "gaps row %d: status=resolved requires evidence" % i,
                    "gaps", i)
            for e in split_multi(row.get("evidence_ids")):
                if e == "":
                    continue
                if e not in ev_ids:
                    err("REF_ORPHAN",
                        "gaps row %d: evidence %s not found" % (i, e),
                        "gaps", i)

    # --- 9. completeness warning: are the canonical tables present? -------
    for name in ("structure_nodes", "structure_edges", "evidence"):
        if name not in present:
            warn("MISSING_TABLE",
                 "%s not found in %s; cross-table checks skipped" % (name, source))

    return errors, warnings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate industry-chain v2 canonical CSVs against CONTRACT.md")
    parser.add_argument("directory", nargs="?", default="data",
                        help="directory containing the canonical *.csv files")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    dataset = load_dataset(args.directory)
    errors, warnings = validate_dataset(dataset, args.directory)

    if args.json:
        payload = {"errors": errors, "warnings": warnings,
                   "error_count": len(errors), "warning_count": len(warnings)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print("[W:%s] %s: %s" % (w["code"], w["file"], w["message"]))
        for e in errors:
            print("[E:%s] %s: %s" % (e["code"], e["file"], e["message"]))
        print("\n%d error(s), %d warning(s)." % (len(errors), len(warnings)),
              file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
