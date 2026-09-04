#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""光模块产业链 v2 读者报告渲染器（Python 标准库 only）。

输入：符合 schema/CONTRACT.md 的七份 canonical CSV（data/ 目录）。
输出：自包含、零外链、确定性的 HTML 报告。

首屏必须回答：产业组成、三路线差异、关键节点、P0 缺口。
结构 / 能力 / 交易三层分层展示；unknown 与 P0 不可隐藏；
输入缺失时明确报错并返回非零退出码。
"""

import argparse
import csv
import hashlib
import html
import os
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

EXPECTED_FILES = [
    "structure_nodes.csv",
    "structure_edges.csv",
    "organizations.csv",
    "capabilities.csv",
    "trade_observations.csv",
    "evidence.csv",
    "gaps.csv",
]

REPORT_TITLE = "光模块产业链 v2 结构报告"
P0_SUMMARY_LIMIT = 10

NODE_TYPE_LABELS = {
    "application": "应用场景",
    "product_route": "产品路线",
    "function": "功能",
    "component": "部件",
    "material": "材料",
    "process": "工序",
    "equipment_category": "设备类别",
}

IMPORTANCE_LABELS = {
    "structural_critical": "结构关键",
    "bottleneck_candidate": "瓶颈候选",
    "enabling": "使能",
    "supporting": "支撑",
    "unknown": "未知",
}

GAP_TYPE_LABELS = {
    "structure_gap": "结构缺口",
    "player_gap": "玩家缺口",
    "capability_gap": "能力缺口",
    "trade_gap": "交易缺口",
    "currentness_gap": "时效缺口",
    "comparability_gap": "可比性缺口",
}
GAP_TYPE_ORDER = {
    "structure_gap": 0,
    "player_gap": 1,
    "capability_gap": 2,
    "trade_gap": 3,
    "currentness_gap": 4,
    "comparability_gap": 5,
}


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def split_multi(value):
    if value is None:
        return []
    text = value.strip()
    if text == "":
        return []
    return [p.strip() for p in text.split(";") if p.strip()]


def route_applies(scope, rid):
    """Return True if a route_scope value (empty/all/semicolon list) applies to rid."""
    if not scope:
        return True
    parts = [p.strip() for p in scope.split(";") if p.strip()]
    return "all" in parts or rid in parts


def e(text):
    """HTML 转义。"""
    return html.escape(str(text) if text is not None else "")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_dataset(directory):
    """读取全部七份 canonical CSV；缺失任一都报错。"""
    dataset = {}
    missing = []
    for name in EXPECTED_FILES:
        path = os.path.join(directory, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        dataset[name] = read_csv(path)
    if missing:
        print("ERROR: 缺少必需的 canonical CSV 输入文件：", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        print(f"预期目录: {directory}", file=sys.stderr)
        sys.exit(1)
    return dataset


def compute_input_hash(directory):
    """按字母序拼接七份 CSV 内容，返回 SHA-256。"""
    h = hashlib.sha256()
    for name in sorted(EXPECTED_FILES):
        path = os.path.join(directory, name)
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        with open(path, "rb") as fh:
            h.update(fh.read())
        h.update(b"\0")
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 索引构建
# ---------------------------------------------------------------------------

def build_indexes(dataset):
    nodes = dataset["structure_nodes.csv"]
    node_by_id = {r["node_id"]: r for r in nodes}
    node_type = {r["node_id"]: r["node_type"] for r in nodes}

    routes = sorted(
        nid for nid, nt in node_type.items() if nt == "product_route"
    )
    applications = sorted(
        nid for nid, nt in node_type.items() if nt == "application"
    )

    edges = dataset["structure_edges.csv"]
    edges_by_source = defaultdict(list)
    edges_by_target = defaultdict(list)
    for edge in edges:
        edges_by_source[edge["source_node_id"]].append(edge)
        edges_by_target[edge["target_node_id"]].append(edge)

    orgs = dataset["organizations.csv"]
    org_by_id = {r["org_id"]: r for r in orgs}

    caps = dataset["capabilities.csv"]
    caps_by_node = defaultdict(list)
    caps_by_org = defaultdict(list)
    for cap in caps:
        caps_by_node[cap["node_id"]].append(cap)
        caps_by_org[cap["org_id"]].append(cap)

    trades = dataset["trade_observations.csv"]
    evidence = dataset["evidence.csv"]
    ev_by_id = {r["evidence_id"]: r for r in evidence}

    gaps = dataset["gaps.csv"]

    return {
        "nodes": nodes,
        "node_by_id": node_by_id,
        "node_type": node_type,
        "routes": routes,
        "applications": applications,
        "edges": edges,
        "edges_by_source": edges_by_source,
        "edges_by_target": edges_by_target,
        "orgs": orgs,
        "org_by_id": org_by_id,
        "caps": caps,
        "caps_by_node": caps_by_node,
        "caps_by_org": caps_by_org,
        "trades": trades,
        "evidence": evidence,
        "ev_by_id": ev_by_id,
        "gaps": gaps,
    }


# ---------------------------------------------------------------------------
# HTML 片段生成
# ---------------------------------------------------------------------------

def badge(text, css_class=""):
    return f'<span class="badge {e(css_class)}">{e(text)}</span>'


def node_badge(nid, idx, show_id=True):
    r = idx["node_by_id"].get(nid)
    if r is None:
        return f'<span class="missing-ref">{e(nid)}</span>'
    nt = r["node_type"]
    label = NODE_TYPE_LABELS.get(nt, nt)
    text = r["name_zh"] or r["name_en"] or nid
    parts = [e(text)]
    if show_id:
        parts.append(f' <code class="nid">{e(nid)}</code>')
    return f'<span class="node-badge type-{e(nt)}">{label}</span>' + "".join(parts)


def route_name(rid, idx):
    r = idx["node_by_id"].get(rid)
    return e(r["name_zh"] or r["name_en"] or rid) if r else e(rid)


def org_name(oid, idx):
    r = idx["org_by_id"].get(oid)
    return e(r["canonical_name"] if r else oid)


def table(headers, rows, table_class=""):
    cls = f' class="{e(table_class)}"' if table_class else ""
    out = [f'<table{cls}>', "<thead><tr>"]
    for h in headers:
        out.append(f"<th>{e(h)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def list_group(items):
    if not items:
        return '<p class="empty">无</p>'
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def evidence_badges(evidence_ids, idx):
    ids = split_multi(evidence_ids)
    if not ids:
        return '<span class="no-evidence">—</span>'
    parts = []
    for eid in ids:
        ev = idx["ev_by_id"].get(eid)
        cls = ev["evidence_use"] if ev else "unknown"
        parts.append(f'<span class="evid-badge use-{e(cls)}">{e(eid)}</span>')
    return " ".join(parts)


# ---------------------------------------------------------------------------
# 执行摘要
# ---------------------------------------------------------------------------

def generate_summary(idx):
    parts = []

    # 产业组成
    stats = defaultdict(int)
    for n in idx["nodes"]:
        stats[n["node_type"]] += 1

    summary_text = (
        f"本报告覆盖 <strong>{stats['application']}</strong> 个应用场景、"
        f"<strong>{stats['product_route']}</strong> 条产品路线；"
        f"结构层分解为 <strong>{stats['function']}</strong> 项功能、"
        f"<strong>{stats['component']}</strong> 类部件、"
        f"<strong>{stats['material']}</strong> 种材料；"
        f"制造层包含 <strong>{stats['process']}</strong> 道工序、"
        f"<strong>{stats['equipment_category']}</strong> 类设备类别。"
    )
    parts.append(f'<section id="summary-composition"><h2>产业组成</h2><p>{summary_text}</p></section>')

    # 三路线差异
    diff_rows = []
    for rid in idx["routes"]:
        apps = [
            edge["source_node_id"]
            for edge in idx["edges"]
            if edge["relation_type"] == "drives" and edge["target_node_id"] == rid
        ]
        funcs = sorted(
            edge["target_node_id"]
            for edge in idx["edges"]
            if edge["relation_type"] == "implements" and edge["source_node_id"] == rid
        )
        comps = sorted({
            edge["target_node_id"]
            for edge in idx["edges"]
            if (edge["relation_type"] == "requires"
                and edge["source_node_id"] in funcs
                and route_applies(edge["route_scope"], rid))
        })
        app_names = ", ".join(node_badge(a, idx, show_id=False) for a in apps) or "—"
        func_names = ", ".join(node_badge(f, idx, show_id=False) for f in funcs) or "—"
        comp_names = ", ".join(node_badge(c, idx, show_id=False) for c in comps) or "—"
        diff_rows.append([
            route_name(rid, idx),
            app_names,
            func_names,
            comp_names,
        ])
    parts.append(
        '<section id="summary-routes"><h2>三路线差异</h2>'
        + table(["产品路线", "驱动场景", "核心功能", "典型部件/材料"], diff_rows)
        + "</section>"
    )

    # 关键节点
    key_nodes = [
        r
        for r in idx["nodes"]
        if r["importance_class"] in ("structural_critical", "bottleneck_candidate")
    ]
    key_nodes.sort(key=lambda r: (r["importance_class"], r["node_id"]))
    if not key_nodes:
        key_html = '<p class="empty">未发现关键节点</p>'
    else:
        rows = []
        for r in key_nodes:
            cls = r["importance_class"]
            conf = r["importance_confidence"]
            rows.append([
                node_badge(r["node_id"], idx, show_id=False),
                badge(IMPORTANCE_LABELS.get(cls, cls), cls),
                badge(conf, conf),
                e(r["importance_basis"] or "—"),
                evidence_badges(r["evidence_ids"], idx),
            ])
        key_html = table(
            ["节点", "重要性", "置信状态", "依据", "证据"], rows, "key-nodes"
        )
    parts.append(
        '<section id="summary-keynodes"><h2>关键节点</h2>' + key_html + "</section>"
    )

    # P0 缺口
    p0_gaps = [g for g in idx["gaps"] if g["priority"] == "P0"]
    p0_gaps.sort(key=lambda g: (
        GAP_TYPE_ORDER.get(g["gap_type"], 99), g["node_id"], g["gap_id"]
    ))
    if not p0_gaps:
        p0_html = '<p class="empty">当前无 P0 缺口</p>'
    else:
        rows = []
        for g in p0_gaps[:P0_SUMMARY_LIMIT]:
            rows.append([
                e(g["gap_id"]),
                badge(GAP_TYPE_LABELS.get(g["gap_type"], g["gap_type"]), g["gap_type"]),
                node_badge(g["node_id"], idx, show_id=False) if g["node_id"] else "—",
                route_name(g["route_scope"], idx) if g["route_scope"] else "—",
                e(g["reason"]),
                e(g["next_question"]),
            ])
        p0_html = table(
            ["缺口 ID", "类型", "节点", "路线", "原因", "下一步问题"], rows, "p0-gaps"
        )
        if len(p0_gaps) > P0_SUMMARY_LIMIT:
            p0_html = (
                f'<p class="summary-note">P0 共 <strong>{len(p0_gaps)}</strong> 项；'
                f'首屏显示前 {P0_SUMMARY_LIMIT} 项，完整队列见“缺口”页。</p>'
                + p0_html
            )
    parts.append(
        '<section id="summary-p0"><h2>P0 缺口</h2>' + p0_html + "</section>"
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 结构层
# ---------------------------------------------------------------------------

def generate_structure_section(idx):
    parts = ["<h2>结构层</h2>"]

    # 按类型聚合的节点表
    type_order = [
        "application", "product_route", "function", "component",
        "material", "process", "equipment_category",
    ]
    for nt in type_order:
        items = [r for r in idx["nodes"] if r["node_type"] == nt]
        if not items:
            continue
        items.sort(key=lambda r: r["node_id"])
        rows = []
        for r in items:
            rows.append([
                f'<code class="nid">{e(r["node_id"])}</code>',
                e(r["name_zh"] or r["name_en"] or "—"),
                badge(IMPORTANCE_LABELS.get(r["importance_class"], r["importance_class"]), r["importance_class"]),
                badge(r["importance_confidence"], r["importance_confidence"]),
                e(r["status"]),
                e(r["as_of"] or "—"),
                evidence_badges(r["evidence_ids"], idx),
            ])
        parts.append(
            f'<h3 id="struct-{e(nt)}">{e(NODE_TYPE_LABELS[nt])}</h3>'
            + table(["ID", "名称", "重要性", "置信", "状态", "as_of", "证据"], rows)
        )

    # 路线分解表
    parts.append("<h3>路线分解</h3>")
    for rid in idx["routes"]:
        parts.append(f'<h4 id="route-{e(rid)}">{route_name(rid, idx)}</h4>')
        # 应用
        apps = sorted(
            edge["source_node_id"]
            for edge in idx["edges"]
            if edge["relation_type"] == "drives" and edge["target_node_id"] == rid
        )
        # 功能
        funcs = sorted(
            edge["target_node_id"]
            for edge in idx["edges"]
            if edge["relation_type"] == "implements" and edge["source_node_id"] == rid
        )
        # 部件/材料
        comps = sorted({
            edge["target_node_id"]
            for edge in idx["edges"]
            if (edge["relation_type"] == "requires"
                and edge["source_node_id"] in funcs
                and route_applies(edge["route_scope"], rid))
        })
        # 工序
        procs = sorted({
            edge["target_node_id"]
            for edge in idx["edges"]
            if (edge["relation_type"] in ("uses_process", "enabled_by")
                and edge["source_node_id"] in (set(comps) | {rid})
                and route_applies(edge["route_scope"], rid))
        })
        parts.append(
            f'<p><strong>驱动场景：</strong>{"".join(node_badge(a, idx, show_id=False) for a in apps) or "—"}</p>'
        )
        parts.append(
            f'<p><strong>核心功能：</strong></p>' + list_group(
                [node_badge(f, idx) for f in funcs]
            )
        )
        parts.append(
            f'<p><strong>必需部件/材料：</strong></p>' + list_group(
                [node_badge(c, idx) for c in comps]
            )
        )
        parts.append(
            f'<p><strong>关联工序/设备：</strong></p>' + list_group(
                [node_badge(p, idx) for p in procs]
            )
        )

    # 结构边表
    edges_sorted = sorted(idx["edges"], key=lambda edge: edge["edge_id"])
    rows = []
    for edge in edges_sorted:
        rows.append([
            f'<code class="eid">{e(edge["edge_id"])}</code>',
            node_badge(edge["source_node_id"], idx),
            e(edge["relation_type"]),
            node_badge(edge["target_node_id"], idx),
            e(edge["route_scope"] or "all"),
            e(edge["requiredness"] or "—"),
            evidence_badges(edge["evidence_ids"], idx),
        ])
    parts.append(
        "<h3>结构边</h3>"
        + table(["ID", "源节点", "关系", "目标节点", "路线范围", "必需性", "证据"], rows)
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 能力层
# ---------------------------------------------------------------------------

def generate_capability_section(idx):
    parts = ["<h2>能力层</h2>"]

    if not idx["caps"]:
        parts.append('<p class="empty">无能力映射记录</p>')
        return "\n".join(parts)

    # 按公司分组
    orgs_with_caps = sorted(set(idx["caps_by_org"].keys()))
    for oid in orgs_with_caps:
        caps = sorted(idx["caps_by_org"][oid], key=lambda c: c["capability_id"])
        parts.append(f'<h3 id="cap-org-{e(oid)}">{org_name(oid, idx)}</h3>')
        rows = []
        for c in caps:
            rows.append([
                f'<code class="cid">{e(c["capability_id"])}</code>',
                node_badge(c["node_id"], idx),
                e(c["capability_status"]),
                e(c["route_scope"] or "—"),
                e(c["review_status"] or "—"),
                e(c["as_of"] or "—"),
                evidence_badges(c["evidence_ids"], idx),
            ])
        parts.append(
            table(["能力 ID", "节点", "能力状态", "路线范围", "审核状态", "as_of", "证据"], rows)
        )

    # 按节点分组
    parts.append("<h3>节点能力映射</h3>")
    nodes_with_caps = sorted(set(idx["caps_by_node"].keys()))
    for nid in nodes_with_caps:
        caps = sorted(idx["caps_by_node"][nid], key=lambda c: c["capability_id"])
        rows = []
        for c in caps:
            rows.append([
                f'<code class="cid">{e(c["capability_id"])}</code>',
                org_name(c["org_id"], idx),
                e(c["capability_status"]),
                e(c["route_scope"] or "—"),
                e(c["review_status"] or "—"),
            ])
        parts.append(
            f'<h4 id="cap-node-{e(nid)}">{node_badge(nid, idx, show_id=False)}</h4>'
            + table(["能力 ID", "公司", "能力状态", "路线范围", "审核状态"], rows)
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 交易层
# ---------------------------------------------------------------------------

def generate_trade_section(idx):
    parts = ["<h2>交易层</h2>"]

    if not idx["trades"]:
        parts.append('<p class="empty">无交易观察记录</p>')
        return "\n".join(parts)

    trades_sorted = sorted(idx["trades"], key=lambda t: t["observation_id"])
    rows = []
    for t in trades_sorted:
        sup = t["supplier_org_id"]
        cus = t["customer_org_id"]
        anon = t["anonymous_endpoint"]
        endpoint = ""
        if anon:
            endpoint = f'<span class="anon">匿名：{e(anon)}</span>'
        elif sup or cus:
            parts_ep = []
            if sup:
                parts_ep.append(f"供：{org_name(sup, idx)}")
            if cus:
                parts_ep.append(f"需：{org_name(cus, idx)}")
            endpoint = "；".join(parts_ep)
        else:
            endpoint = "—"
        rows.append([
            f'<code class="tid">{e(t["observation_id"])}</code>',
            endpoint,
            node_badge(t["product_or_node_id"], idx) if t["product_or_node_id"] else "—",
            e(t["period"] or "—"),
            e(t["amount_or_share"] or "—"),
            e(t["grade"] or "—"),
            evidence_badges(t["evidence_ids"], idx),
        ])
    parts.append(
        table(
            ["观察 ID", "交易端点", "产品/节点", "期间", "金额/占比", "边等级", "证据"],
            rows,
            "trade-table",
        )
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 证据层
# ---------------------------------------------------------------------------

def generate_evidence_section(idx):
    parts = ["<h2>证据层</h2>"]

    if not idx["evidence"]:
        parts.append('<p class="empty">无证据记录</p>')
        return "\n".join(parts)

    ev_sorted = sorted(idx["evidence"], key=lambda r: r["evidence_id"])
    rows = []
    for r in ev_sorted:
        url = r["url"] or ""
        if url:
            url_cell = f'<code>{e(url)}</code>'
        else:
            url_cell = "—"
        rows.append([
            f'<code class="eid">{e(r["evidence_id"])}</code>',
            badge(r["evidence_use"], r["evidence_use"]),
            e(r["source_tier"] or "—"),
            e(r["title"] or "—"),
            e(r["publisher"] or "—"),
            url_cell,
            e(r["publication_date"] or "—"),
            e(r["verdict"] or "—"),
            e(r["stance"] or "—"),
            e(r["quote"][:200] + "…" if len(r["quote"]) > 200 else (r["quote"] or "—")),
        ])
    parts.append(
        table(
            ["证据 ID", "用途", "来源等级", "标题", "发布方", "URL", "发布日期", "判定", "立场", "引语"],
            rows,
            "evidence-table",
        )
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 缺口层
# ---------------------------------------------------------------------------

def generate_gaps_section(idx):
    parts = ["<h2>研究缺口</h2>"]

    if not idx["gaps"]:
        parts.append('<p class="empty">无缺口记录</p>')
        return "\n".join(parts)

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "monitor": 3}
    gaps_sorted = sorted(
        idx["gaps"],
        key=lambda g: (
            priority_order.get(g["priority"], 99),
            GAP_TYPE_ORDER.get(g["gap_type"], 99),
            g["node_id"],
            g["gap_id"],
        ),
    )
    rows = []
    for g in gaps_sorted:
        rows.append([
            f'<code class="gid">{e(g["gap_id"])}</code>',
            badge(g["priority"], f"prio-{g['priority']}"),
            badge(GAP_TYPE_LABELS.get(g["gap_type"], g["gap_type"]), g["gap_type"]),
            node_badge(g["node_id"], idx) if g["node_id"] else "—",
            route_name(g["route_scope"], idx) if g["route_scope"] else "—",
            e(g["status"]),
            e(g["reason"]),
            e(g["next_question"]),
            e(g["completion_condition"]),
            evidence_badges(g["evidence_ids"], idx),
        ])
    parts.append(
        table(
            [
                "缺口 ID", "优先级", "类型", "节点", "路线", "状态", "原因",
                "下一步问题", "完成条件", "证据",
            ],
            rows,
            "gaps-table",
        )
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 主渲染
# ---------------------------------------------------------------------------

def render_report(dataset, template, input_hash):
    idx = build_indexes(dataset)
    sections = {
        "TITLE": REPORT_TITLE,
        "INPUT_HASH": input_hash,
        "EXECUTIVE_SUMMARY": generate_summary(idx),
        "STRUCTURE_SECTION": generate_structure_section(idx),
        "CAPABILITY_SECTION": generate_capability_section(idx),
        "TRADE_SECTION": generate_trade_section(idx),
        "EVIDENCE_SECTION": generate_evidence_section(idx),
        "GAPS_SECTION": generate_gaps_section(idx),
    }
    html_out = template
    for key, value in sections.items():
        html_out = html_out.replace(f"{{{{{key}}}}}", value)
    return html_out


def load_template(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render industry-chain v2 reader report")
    parser.add_argument("data_dir", help="directory containing the seven canonical CSVs")
    parser.add_argument("output", nargs="?", default="report.html", help="output HTML path")
    parser.add_argument(
        "--template",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_template.html"),
        help="path to HTML template",
    )
    args = parser.parse_args(argv)

    dataset = load_dataset(args.data_dir)
    input_hash = compute_input_hash(args.data_dir)
    template = load_template(args.template)
    html_out = render_report(dataset, template, input_hash)

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"wrote {len(html_out)} bytes to {args.output}")
    print(f"input SHA-256: {input_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
