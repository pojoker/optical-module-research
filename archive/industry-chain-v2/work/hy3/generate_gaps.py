#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate research gaps across the six coverage types (stdlib only).

Reads the canonical CSVs and emits ``gaps.csv`` rows covering:

* structure_gap      - missing decomposition / key node without evidence
* player_gap         - a mappable key node with no organization mapping
* capability_gap     - a key node with mappings that are unknown, unreviewed,
                       or unsupported by capability evidence
* trade_gap          - a production capability with no observed supply relation
* currentness_gap    - missing or stale ``as_of`` timestamps
* comparability_gap  - asymmetry only for explicitly shared/common coverage;
                       plus the denominator guard when fewer than two routes exist

Important: this tool only *emits research gaps*. It never fabricates trade
observations or capability records from capability evidence (CONTRACT §5.1 /
WP-CLAUDE note). Output is deterministic and validates against
``validate_model.py``.

Usage:
    python generate_gaps.py <data_dir> [-o gaps.csv]
                            [--stale-days N] [--reference-date YYYY-MM-DD]
"""

import argparse
import csv
import os
import sys
from datetime import datetime

from validate_model import (
    split_multi,
    load_dataset,
    EXPECTED_HEADERS,
)

# Statuses that imply a real, market-relevant capability worth a trade check.
PRODUCTION_STATUSES = {"production", "sampling", "planned"}
PLAYER_MAPPABLE_NODE_TYPES = {
    "product_route", "component", "material", "process", "equipment_category",
}
def _build_indexes(dataset):
    nodes = dataset.get("structure_nodes", (None, []))[1]
    edges = dataset.get("structure_edges", (None, []))[1]
    orgs = dataset.get("organizations", (None, []))[1]
    caps = dataset.get("capabilities", (None, []))[1]
    trades = dataset.get("trade_observations", (None, []))[1]
    evidence = dataset.get("evidence", (None, []))[1]

    node_by_id = {(r.get("node_id") or "").strip(): r for r in nodes}
    node_type = {nid: (r.get("node_type") or "").strip()
                 for nid, r in node_by_id.items()}
    routes = [nid for nid, t in node_type.items() if t == "product_route"]

    implements = {}   # route -> set(function)
    requires = {}    # node -> set(component/material)
    for e in edges:
        rt = (e.get("relation_type") or "").strip()
        s = (e.get("source_node_id") or "").strip()
        t = (e.get("target_node_id") or "").strip()
        if rt == "implements":
            implements.setdefault(s, set()).add(t)
        elif rt == "requires":
            requires.setdefault(s, set()).add(t)
    return {
        "nodes": nodes, "edges": edges, "orgs": orgs, "caps": caps,
        "trades": trades, "evidence": evidence,
        "node_by_id": node_by_id, "node_type": node_type, "routes": routes,
        "implements": implements, "requires": requires,
    }


def _route_for_node(idx, nid):
    """Best-effort route scope for a node (first route that reaches it)."""
    for r in idx["routes"]:
        if nid in idx["implements"].get(r, set()) or nid in idx["requires"].get(r, set()):
            return r
    return ""


def _stale(a, ref_date, stale_days):
    """Return (is_stale, message_suffix) for a missing/unparseable/stale as_of."""
    if a == "":
        return True, "missing as_of timestamp"
    try:
        d = datetime.strptime(a, "%Y-%m-%d").date()
    except ValueError:
        return True, "as_of %s not ISO date" % a
    if (ref_date - d).days > stale_days:
        return True, "as_of %s older than %d days" % (a, stale_days)
    return False, ""


def build_gaps(dataset, reference_date=None, stale_days=365):
    """Return a list of gap row dicts (keys match gaps.csv schema).

    ``reference_date`` is mandatory: callers must pass an explicit date (the
    CLI exposes it as the required ``--reference-date`` flag). There is no
    ``date.today()`` fallback because a silent "now" would make gap output
    non-deterministic across runs (currentness thresholds shift daily).
    """
    if reference_date is None:
        raise ValueError(
            "reference_date is required and must be passed explicitly "
            "(e.g. build_gaps(dataset, reference_date=date(2024, 1, 1)) or "
            "via generate_gaps.py --reference-date YYYY-MM-DD); date.today() "
            "is forbidden to keep output deterministic.")
    ref = reference_date
    idx = _build_indexes(dataset)
    node_by_id = idx["node_by_id"]
    node_type = idx["node_type"]
    routes = idx["routes"]
    implements = idx["implements"]
    requires = idx["requires"]

    # Evidence maps are used to distinguish a real supporting record from a
    # merely present/pending citation.
    ev_use = {}
    ev_verdict = {}
    for e in idx["evidence"]:
        eid = (e.get("evidence_id") or "").strip()
        ev_use[eid] = (e.get("evidence_use") or "").strip()
        ev_verdict[eid] = (e.get("verdict") or "").strip()

    gaps = []

    def add(gtype, nid, rscope, reason, next_q, cond, prio):
        gaps.append({
            "gap_id": "",
            "node_id": nid,
            "route_scope": rscope,
            "gap_type": gtype,
            "priority": prio,
            "status": "identified",
            "reason": reason,
            "next_question": next_q,
            "completion_condition": cond,
            "owner": "WP-HY3",
            "evidence_ids": "",
            "updated_at": ref.isoformat(),
            "notes": "",
        })

    # --- structure_gap ---------------------------------------------------
    for r in routes:
        funcs = implements.get(r, set())
        if not funcs:
            add("structure_gap", r, r,
                "route %s has no decomposed functions (no implements edges)" % r,
                "Which functions must this route implement?",
                "At least one implements edge from route to a function node",
                "P1")
            continue
        for f in funcs:
            if not requires.get(f, set()):
                add("structure_gap", f, r,
                    "function %s in route %s has no required component/material" % (f, r),
                    "What components/materials does this function require?",
                    "At least one requires edge from function to component/material",
                    "P1")
    for nid, r in node_by_id.items():
        if (r.get("importance_class") or "").strip() == "structural_critical":
            has_support = any(
                ev_use.get(eid) == "structure"
                and ev_verdict.get(eid) in {"supports", "partial"}
                for eid in split_multi(r.get("evidence_ids"))
            )
            if not has_support:
                add("structure_gap", nid, "",
                    "structural_critical node %s has no supporting structure evidence" % nid,
                    "What evidence supports this critical node?",
                    "At least one supports/partial structure evidence referenced",
                    "P0")

    # --- player_gap ------------------------------------------------------
    # A player_gap anchors a KEY structural node (structural_critical /
    # bottleneck_candidate) for which NO organization has any capability
    # mapping at all. It is the "structural hole" case: nobody in the market
    # covers this node. It is deliberately disjoint from capability_gap
    # (which requires an existing but weak mapping), so a given node can only
    # ever produce one of the two.
    cap_nodes = {(c.get("node_id") or "").strip() for c in idx["caps"]}
    for nid, r in node_by_id.items():
        ic = (r.get("importance_class") or "").strip()
        nt = (r.get("node_type") or "").strip()
        if (ic in {"structural_critical", "bottleneck_candidate"}
                and nt in PLAYER_MAPPABLE_NODE_TYPES and nid not in cap_nodes):
            rscope = _route_for_node(idx, nid)
            add("player_gap", nid, rscope,
                "key node %s (%s) has no organization capability mapping "
                "(structural hole - no player covers it)" % (nid, ic),
                "Which organization can perform/produce this node?",
                "At least one capability record mapping an org to this node",
                "P0" if ic == "structural_critical" else "P1")

    # --- capability_gap --------------------------------------------------
    # A capability_gap anchors a KEY structural node that already has at least
    # one capability mapping, but every mapping is weak: the capability status
    # is "unknown", or it carries no capability evidence, or it has not been
    # reviewed (review_status empty / proposed). A node with no mapping at all
    # is handled by player_gap instead, so the two responsibilities never
    # overlap and never duplicate.
    cap_by_node = {}
    for c in idx["caps"]:
        cap_by_node.setdefault((c.get("node_id") or "").strip(), []).append(c)

    def _cap_is_strong(c):
        cs = (c.get("capability_status") or "").strip()
        rs = (c.get("review_status") or "").strip()
        has_cap_ev = any(
            e in ev_use and ev_use[e] == "capability"
            for e in split_multi(c.get("evidence_ids"))
        )
        reviewed = rs not in ("", "proposed")  # not-yet-reviewed excludes
        return cs != "unknown" and has_cap_ev and reviewed

    for nid, r in node_by_id.items():
        ic = (r.get("importance_class") or "").strip()
        nt = (r.get("node_type") or "").strip()
        if (ic not in {"structural_critical", "bottleneck_candidate"}
                or nt not in PLAYER_MAPPABLE_NODE_TYPES):
            continue
        mappings = cap_by_node.get(nid, [])
        if not mappings:
            continue  # no mapping -> player_gap owns this node, not here
        if not any(_cap_is_strong(c) for c in mappings):
            rscope = _route_for_node(idx, nid)
            add("capability_gap", nid, rscope,
                "key node %s (%s) has capability mapping(s) but all are weak "
                "(status=unknown / no capability evidence / not reviewed)"
                % (nid, ic),
                "What evidence supports this capability, and has it been "
                "reviewed?",
                "At least one capability record with a known status, "
                "capability evidence and a reviewed status",
                "P0" if ic == "structural_critical" else "P1")

    # --- trade_gap (research need only; no fabricated observation) -------
    trade_suppliers = {(t.get("supplier_org_id") or "").strip()
                       for t in idx["trades"]}
    trade_nodes = {(t.get("product_or_node_id") or "").strip()
                   for t in idx["trades"]}
    for c in idx["caps"]:
        cs = (c.get("capability_status") or "").strip()
        if cs in PRODUCTION_STATUSES:
            oid = (c.get("org_id") or "").strip()
            nid = (c.get("node_id") or "").strip()
            if oid not in trade_suppliers and nid not in trade_nodes:
                if nid == "":
                    continue
                rscope = _route_for_node(idx, nid)
                add("trade_gap", nid, rscope,
                    "capability %s (%s) has no observed trade relationship"
                    % (c.get("capability_id"), cs),
                    "Who supplies/demands this capability in the market?",
                    "At least one trade_observation for this org/node",
                    "P1")

    # --- currentness_gap -------------------------------------------------
    for r in idx["nodes"]:
        nid = (r.get("node_id") or "").strip()
        if nid == "":
            continue
        bad, msg = _stale((r.get("as_of") or "").strip(), ref, stale_days)
        if bad:
            add("currentness_gap", nid, "",
                "node %s %s" % (nid, msg),
                "When was this record last verified?",
                "as_of populated with a recent ISO date", "P2")
    for c in idx["caps"]:
        nid = (c.get("node_id") or "").strip()
        if nid == "":
            continue
        bad, msg = _stale((c.get("as_of") or "").strip(), ref, stale_days)
        if bad:
            add("currentness_gap", nid, _route_for_node(idx, nid),
                "capability %s %s" % (nid, msg),
                "When was this capability last verified?",
                "as_of populated with a recent ISO date", "P2")
    for e in idx["evidence"]:
        eid = (e.get("evidence_id") or "").strip()
        bad, msg = _stale((e.get("as_of") or "").strip(), ref, stale_days)
        if bad:
            # evidence has no natural structure node; leave node_id empty
            add("currentness_gap", "", "",
                "evidence %s %s" % (eid, msg),
                "When was this evidence retrieved/validated?",
                "as_of populated with a recent ISO date", "P2")

    # --- comparability_gap ----------------------------------------------
    if len(routes) < 2:
        if routes:
            add("comparability_gap", routes[0], routes[0],
                "only %d product route(s); comparability denominator insufficient"
                % len(routes),
                "Define additional product routes to enable comparison",
                "At least two product_route nodes exist", "P1")
        # with zero routes there is no valid anchor node of type route;
        # the structure/other gaps already cover the emptiness.
    else:
        # Per-route decomposition is built ONLY from *route-specific* edges
        # (route_scope == that route). route_scope == 'all' edges are shared
        # DECLARATIONS, not concrete per-route coverage; they define the
        # comparability denominator but are not assumed to be auto-present.
        route_down = {rr: set() for rr in routes}
        shared_declared = set()   # nodes declared common via route_scope='all'
        for e in idx["edges"]:
            rt = (e.get("relation_type") or "").strip()
            if rt not in ("implements", "requires"):
                continue
            tgt = (e.get("target_node_id") or "").strip()
            rscope = (e.get("route_scope") or "").strip()
            if rscope == "all":
                shared_declared.add(tgt)
            elif rscope in routes:   # route-specific edge, counted once
                route_down[rscope].add(tgt)
        # Comparability subjects = explicitly shared nodes (route_scope='all')
        # OR nodes present in every route's concrete decomposition. Legitimate
        # route_specific nodes (present in only some routes) are NOT subjects,
        # so their absence elsewhere is a real design difference, not a gap.
        subjects = set(shared_declared)
        all_nodes = set().union(*route_down.values()) if route_down else set()
        for nid in all_nodes:
            if all(nid in route_down[rr] for rr in routes):
                subjects.add(nid)
        for nid in sorted(subjects):
            present_in = [rr for rr in routes if nid in route_down[rr]]
            missing_in = [rr for rr in routes if nid not in route_down[rr]]
            for rr in missing_in:
                add("comparability_gap", rr, rr,
                    "shared node %s is absent in route %s but present in %s "
                    "(asymmetric coverage of a common node)"
                    % (nid, rr, ",".join(present_in)),
                    "Does route %s truly not require %s, or is coverage "
                    "incomplete?" % (rr, nid),
                    "Coverage confirmed equal across routes or gap explained",
                    "P2")

    # deterministic ordering + stable IDs
    gaps.sort(key=lambda g: (g["gap_type"], g["node_id"],
                             g["route_scope"], g["reason"]))
    for i, g in enumerate(gaps, 1):
        g["gap_id"] = "GAP-%04d" % i
    return gaps


def write_gaps(gaps, path):
    fieldnames = EXPECTED_HEADERS["gaps"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for g in gaps:
            writer.writerow({k: g.get(k, "") for k in fieldnames})


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate research gaps across six coverage types")
    parser.add_argument("directory", nargs="?", default="data",
                        help="directory with the canonical *.csv files")
    parser.add_argument("-o", "--output", default=None,
                        help="output gaps.csv path (default <dir>/gaps.csv)")
    parser.add_argument("--stale-days", type=int, default=365)
    parser.add_argument("--reference-date", required=True,
                        help="required YYYY-MM-DD snapshot date")
    args = parser.parse_args(argv)

    dataset = load_dataset(args.directory)
    ref = datetime.strptime(args.reference_date, "%Y-%m-%d").date()
    gaps = build_gaps(dataset, ref, args.stale_days)

    out = args.output or os.path.join(args.directory, "gaps.csv")
    write_gaps(gaps, out)
    print("wrote %d gaps to %s" % (len(gaps), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
