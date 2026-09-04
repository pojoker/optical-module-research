#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_atlas_v12.py — v1.2 W1 流向图谱生成器（可复跑）

输入（只读）：
  output/edges.csv            81 行边
  output/nodes.csv            42 节点
  flows/out/customs-partners.csv   海关伙伴分拆（按契约取 202501 + 2026H1 共 7 个月）
  flows/out/customs-monthly.csv    月度合计（用于对账断言）

产出（全新文件，不改 v1.0 与任何输入）：
  output/光模块产业图谱-v1.2.html   自包含双层图谱：①关系层(81边) ②流向层(海关桑基)

契约：flows/SPEC-v1.2.md §W1。跑完打印自测断言结果。
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDGES_CSV = ROOT / "output" / "edges.csv"
NODES_CSV = ROOT / "output" / "nodes.csv"
PARTNERS_CSV = ROOT / "flows" / "out" / "customs-partners.csv"
MONTHLY_CSV = ROOT / "flows" / "out" / "customs-monthly.csv"
OUT_HTML = ROOT / "output" / "光模块产业图谱-v1.2.html"

# ───────────────────────── 关系层：层映射（沿用 v1.0 固化口径） ─────────────────────────
LAYER_ORDER = ["生产设备层", "器件/芯片层", "模块/代工层", "终端/云层", "其他"]
LAYER_MAP = {
    "老化测试设备商": "生产设备层", "耦合封装设备商": "生产设备层", "组装设备商": "生产设备层",
    "组件封装设备商": "生产设备层", "自动化设备商": "生产设备层", "焊接设备商": "生产设备层",
    "测试测量仪器": "生产设备层", "驱动控制供应商": "生产设备层", "加工件供应商": "生产设备层",
    "滑台类日本代理": "生产设备层", "神津精机代理": "生产设备层",
    "光芯片厂": "器件/芯片层", "光器件厂": "器件/芯片层", "光器件厂(已消亡)": "器件/芯片层",
    "光器件/组件厂": "器件/芯片层", "相干光器件/DSP": "器件/芯片层", "芯片/CPO": "器件/芯片层",
    "光模块厂": "模块/代工层", "光模块/器件厂": "模块/代工层", "光器件/模块厂": "模块/代工层",
    "代工(EMS)": "模块/代工层",
    "云巨头(终端)": "终端/云层", "算力终端/系统商": "终端/云层", "网络设备OEM": "终端/云层",
    "系统设备商": "终端/云层", "消费电子终端": "终端/云层", "CATV设备商": "终端/云层",
    "CATV分销商": "终端/云层", "出口代理(贸易商)": "终端/云层",
    "旭创关联方(海外销售主体待核)": "终端/云层",
    "汽车电机厂": "其他", "科研院所(跨行业)": "其他", "锻件厂(跨行业)": "其他", "未收录实体": "其他",
}
LAYER_COLORS = {"生产设备层": "#64748b", "器件/芯片层": "#0d9488", "模块/代工层": "#7c3aed",
                "终端/云层": "#d97706", "其他": "#a8a29e"}

# edges.csv 写法 → nodes.csv 实名（显式别名表，逐条来自 edges.csv 实际写法）
ALIAS = {
    "华为+海思": "华为(含海思)", "华为": "华为(含海思)",
    "ficonTEC(罗博特科)": "罗博特科/ficonTEC", "罗博特科": "罗博特科/ficonTEC",
    "索恩格": "索恩格(SEG Automotive)",
    "博通(客户)": "博通(Broadcom)", "NVIDIA(客户)": "NVIDIA",
    "等离子体所(客户)": "等离子体所", "PINEWAVE(关联方)": "PINEWAVE",
    "中际旭创(作为客户)": "中际旭创", "Fabrinet(疑似客户)": "Fabrinet",
    "Fabrinet(解匿)": "Fabrinet",
    "Ciena(解匿)": "Ciena", "Google(解匿)": "Google",
    "浙江粮油(出口代理)": "浙江粮油",
    "AAOI": "Applied Optoelectronics(AAOI)",
}

# 契约月份范围（SPEC-v1.2 §W1：取 202501 与 2026H1 各月；2025 全年月份不取）
MONTH_SCOPE = ["202501"] + [f"2026{i:02d}" for i in range(1, 7)]

# 边等级 → 样式；混合边按"最弱证据等级"着色（与 v1.0 同规）
GRADE_STYLE = {"实边": "solid", "实边(已死亡)": "dead", "半边": "half", "半边槽位": "half",
               "推断边(A级)": "inferred", "程序段落泄漏": "leak"}
GRADE_RANK = {"实边": 0, "实边(已死亡)": 1, "程序段落泄漏": 2, "推断边(A级)": 3, "半边": 4, "半边槽位": 4}
STYLE_LABEL = {"solid": "实边（实名披露）", "dead": "实边（已死亡）", "half": "半边 / 半边槽位（匿名）",
               "inferred": "推断边（A级）", "leak": "程序段落泄漏"}
STYLE_COLOR = {"solid": "#475569", "dead": "#9ca3af", "half": "#9ca3af",
               "inferred": "#ea580c", "leak": "#7c3aed"}

# 流向层常量
FOCUS_SRC = "中国"
HL_COLORS = {"马来西亚": "#059669", "美国": "#dc2626", "泰国": "#0ea5e9"}
OTHER_DEST_COLOR = "#94a3b8"
AGG_COLOR = "#cbd5e1"


def read_csv_dicts(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [{(k.strip() if k else k): (v.strip() if isinstance(v, str) else v)
             for k, v in row.items()} for row in rows]


# ───────────────────────── 关系层建模 ─────────────────────────

def build_rel_model(edge_rows, node_rows):
    """返回 (nodes: dict key->dict, merged_edges: list[dict])。"""
    by_name = {r["名称"]: r for r in node_rows}
    nodes = {}

    def add_real(row):
        key = "N_" + row["node_id"]
        nodes[key] = {"key": key, "name": row["名称"], "type": row["类型"],
                      "country": row.get("国别", ""), "code": row.get("代码", ""),
                      "memo": row.get("备注", ""),
                      "layer": LAYER_MAP.get(row["类型"], "其他"), "slot": False}
        return key

    for r in node_rows:
        add_real(r)

    slot_keys = {}   # (company_name, raw_label) -> key
    extra_keys = {}  # 未收录实名实体 name -> key

    def resolve(raw, other_side):
        """把边端点名字解析到节点 key；匿名→槽位节点，未收录实名→补建节点。"""
        name = ALIAS.get(raw, raw)
        if name in by_name:
            return "N_" + by_name[name]["node_id"]
        if "匿名" in raw:
            skey = (other_side, raw)
            if skey not in slot_keys:
                key = f"S_{len(slot_keys) + 1:02d}"
                slot_keys[skey] = key
                layer = "器件/芯片层" if raw.startswith("供应商") else "终端/云层"
                nodes[key] = {"key": key, "name": raw, "type": "匿名槽位",
                              "country": "", "code": "",
                              "memo": f"{other_side} 年报匿名槽位（未披露实名，不猜测）",
                              "layer": layer, "slot": True, "host": other_side}
            return slot_keys[skey]
        if raw not in extra_keys:
            key = f"X_{len(extra_keys) + 1:02d}"
            extra_keys[raw] = key
            nodes[key] = {"key": key, "name": raw, "type": "未收录实体",
                          "country": "", "code": "",
                          "memo": "edges.csv 出现的实体，nodes.csv 未收录；如实补建",
                          "layer": "其他", "slot": False}
        return extra_keys[raw]

    merged = {}
    for row in edge_rows:
        src = resolve(row["供方"], row["需方"])
        dst = resolve(row["需方"], row["供方"])
        rec = {"edge_id": row.get("edge_id", ""), "占比或金额": row.get("占比或金额", ""),
               "财年": row.get("财年", ""), "边等级": row.get("边等级", ""),
               "证据文件": row.get("证据文件", ""), "锚点": row.get("锚点", ""),
               "验证状态": row.get("验证状态", ""), "备注": row.get("备注", "")}
        merged.setdefault((src, dst), {"src": src, "dst": dst, "records": []})
        merged[(src, dst)]["records"].append(rec)

    edges = []
    for (src, dst), d in merged.items():
        grades = [r["边等级"] for r in d["records"]]
        weakest = max(grades, key=lambda g: GRADE_RANK.get(g, 9))
        style = GRADE_STYLE.get(weakest, "half")
        edges.append({"src": src, "dst": dst, "style": style,
                      "styleLabel": STYLE_LABEL[style],
                      "mixed": len(set(grades)) > 1, "records": d["records"]})
    edges.sort(key=lambda e: e["records"][0]["edge_id"])
    return nodes, edges


# ───────────────────────── 关系层布局 + 静态 SVG ─────────────────────────
NODE_W, NODE_H, ROW_GAP, INNER_GAP = 216, 48, 66, 28
LAYER_GAP, MARGIN_X, MARGIN_TOP = 88, 44, 26
LAYER_TITLE_H = 46
TWO_COL_THRESHOLD = 16


def rel_layout(nodes):
    by_layer = {ly: [] for ly in LAYER_ORDER}
    for n in nodes.values():
        by_layer[n["layer"]].append(n)
    for ly in by_layer:
        by_layer[ly].sort(key=lambda n: (n["slot"], n.get("host", ""), n["name"]))

    cols = []   # (layer, x, width, node_list, ncols)
    x = MARGIN_X
    max_rows = 1
    for ly in LAYER_ORDER:
        ns = by_layer[ly]
        if not ns:
            continue
        ncols = 2 if len(ns) > TWO_COL_THRESHOLD else 1
        w = ncols * NODE_W + (ncols - 1) * INNER_GAP
        cols.append((ly, x, w, ns, ncols))
        rows = (len(ns) + ncols - 1) // ncols
        max_rows = max(max_rows, rows)
        x += w + LAYER_GAP
    width = x - LAYER_GAP + MARGIN_X
    height = MARGIN_TOP + LAYER_TITLE_H + max_rows * ROW_GAP + 40

    pos = {}
    layer_boxes = []
    for ly, lx, w, ns, ncols in cols:
        rows = (len(ns) + ncols - 1) // ncols
        span = rows * ROW_GAP
        start_y = MARGIN_TOP + LAYER_TITLE_H + (max_rows * ROW_GAP - span) / 2
        layer_boxes.append((ly, lx - 18, start_y - LAYER_TITLE_H + 8, w + 36,
                            LAYER_TITLE_H + span + 20))
        for i, n in enumerate(ns):
            c, r = divmod(i, rows) if ncols == 2 else (0, i)
            cx = lx + c * (NODE_W + INNER_GAP) + NODE_W / 2
            cy = start_y + r * ROW_GAP + NODE_H / 2
            pos[n["key"]] = (cx, cy)
    return pos, width, height, layer_boxes


def esc(s) -> str:
    import html as _h
    return _h.escape(str(s if s is not None else ""), quote=True)


def rect_anchor(cx, cy, hw, hh, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = hw / abs(dx) if dx else float("inf")
    sy = hh / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def edge_d(p1, p2, same_col, backward):
    x1, y1 = p1
    x2, y2 = p2
    if same_col:  # 同层边：向左绕弧
        off = 96
        return f"M{x1:.1f},{y1:.1f} C{x1 - off:.1f},{y1:.1f} {x2 - off:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
    if backward:  # 从右往左的边：向外弯
        bow = max(60, (x1 - x2) * 0.35)
        return (f"M{x1:.1f},{y1:.1f} C{x1 - bow:.1f},{y1:.1f} "
                f"{x2 + bow:.1f},{y2:.1f} {x2:.1f},{y2:.1f}")
    mx = (x1 + x2) / 2
    return f"M{x1:.1f},{y1:.1f} C{mx:.1f},{y1:.1f} {mx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"


def rel_svg(nodes, edges, pos, width, height, layer_boxes):
    parts = [f'<svg id="g" viewBox="0 0 {width} {height}" preserveAspectRatio="xMinYMin meet" '
             f'xmlns="http://www.w3.org/2000/svg">']
    parts.append('<defs>')
    for st, col in STYLE_COLOR.items():
        parts.append(f'<marker id="ah-{st}" viewBox="0 0 10 10" refX="8.5" refY="5" '
                     f'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
                     f'<path d="M0.5,0.5 L9.5,5 L0.5,9.5 z" fill="{col}"/></marker>')
    parts.append('</defs>')

    for ly, bx, by, bw, bh in layer_boxes:
        col = LAYER_COLORS[ly]
        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="16" '
                     f'fill="{col}" fill-opacity="0.05" stroke="{col}" stroke-opacity="0.22" '
                     f'stroke-width="1" stroke-dasharray="3 5"/>')
        parts.append(f'<text x="{bx + bw / 2}" y="{by + 30}" text-anchor="middle" class="lyr" '
                     f'fill="{col}">{esc(ly)}</text>')

    # 边
    for i, e in enumerate(edges):
        e["id"] = f"e{i}"
        sx, sy = pos[e["src"]]
        dx, dy = pos[e["dst"]]
        same_col = abs(dx - sx) < NODE_W
        backward = dx < sx - 1
        a = rect_anchor(sx, sy, NODE_W / 2, NODE_H / 2, dx, dy)
        b = rect_anchor(dx, dy, NODE_W / 2, NODE_H / 2, sx, sy)
        d = edge_d(a, b, same_col, backward)
        st = e["style"]
        col = STYLE_COLOR[st]
        dash = {"solid": "", "dead": "", "half": ' stroke-dasharray="7 5"',
                "inferred": ' stroke-dasharray="11 4 2 4"', "leak": ' stroke-dasharray="13 5"'}[st]
        sw = {"solid": 3.0, "dead": 1.9, "half": 2.6, "inferred": 3.0, "leak": 2.6}[st]
        parts.append(f'<g class="edge" data-e="{e["id"]}">'
                     f'<path class="hit" d="{d}" fill="none" stroke="transparent" stroke-width="14"/>'
                     f'<path class="eln" d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"'
                     f'{dash} marker-end="url(#ah-{st})"/></g>')

    # 节点
    for key, n in nodes.items():
        cx, cy = pos[key]
        x, y = cx - NODE_W / 2, cy - NODE_H / 2
        ctry = n["country"]
        border = "#dc2626" if ctry.startswith("中国") else ("#2563eb" if ctry == "美国" else "#6b7280")
        lcol = LAYER_COLORS[n["layer"]]
        name = n["name"]
        disp = name if len(name) <= 19 else name[:18] + "…"
        if n["slot"]:
            parts.append(
                f'<g class="node" data-n="{key}">'
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="9" fill="#f8fafc" '
                f'stroke="{border}" stroke-width="1.4" stroke-dasharray="5 4"/>'
                f'<rect x="{x}" y="{y + 6}" width="5" height="{NODE_H - 12}" rx="2.5" fill="{lcol}"/>'
                f'<text x="{x + 14}" y="{y + 20}" class="slot-lbl">{esc(disp)}</text>'
                f'<text x="{x + 14}" y="{y + 36}" class="slot-sub">匿名槽位 · {esc(n.get("host", ""))}</text>'
                f'<text x="{x + NODE_W - 16}" y="{y + 27}" class="slot-q">?</text></g>')
        else:
            sub = n["type"] + (f" · {n['code']}" if n["code"] and n["code"] != "—" else "")
            sub = sub if len(sub) <= 24 else sub[:23] + "…"
            parts.append(
                f'<g class="node" data-n="{key}">'
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="9" fill="#ffffff" '
                f'stroke="{border}" stroke-width="2"/>'
                f'<rect x="{x}" y="{y + 6}" width="5" height="{NODE_H - 12}" rx="2.5" fill="{lcol}"/>'
                f'<circle cx="{x + NODE_W - 15}" cy="{y + 13}" r="4.5" fill="{border}"/>'
                f'<text x="{x + 14}" y="{y + 20}" class="nname" font-size="12.5">{esc(disp)}</text>'
                f'<text x="{x + 14}" y="{y + 37}" class="ntype" font-size="10.5">{esc(sub)}</text></g>')
    parts.append('</svg>')
    return "".join(parts)


# ───────────────────────── 流向层建模 ─────────────────────────

def month_label(m: str) -> str:
    return f"{m[:4]}年{int(m[4:])}月"


def build_flow_model(partner_rows):
    months = {}
    for r in partner_rows:
        m = r["月份"]
        months.setdefault(m, []).append(
            {"name": r["贸易伙伴"], "kg": int(r["出口量kg"]),
             "amount": int(r["金额"]), "currency": r["币种"]})
    flows = {}
    for m, rs in sorted(months.items()):
        rs.sort(key=lambda x: -x["amount"])
        total = sum(x["amount"] for x in rs)
        total_kg = sum(x["kg"] for x in rs)
        cur = {x["currency"] for x in rs}
        assert len(cur) == 1, f"{m} 币种混杂: {cur}"
        top = rs[:10]
        rest = rs[10:]
        items = [{"name": x["name"], "amount": x["amount"], "kg": x["kg"]} for x in top]
        items.append({"name": "其他", "amount": sum(x["amount"] for x in rest),
                      "kg": sum(x["kg"] for x in rest), "n": len(rest)})
        for it in items:
            it["share"] = it["amount"] / total
        flows[m] = {"label": month_label(m), "currency": rs[0]["currency"],
                    "total": total, "total_kg": total_kg, "n_partners": len(rs),
                    "flows": items}
    return flows


# ───────────────────────── HTML 组装 ─────────────────────────

def js_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build_html(nodes, edges, rel_svg_str, rel_w, rel_h, flows, month_keys, stats, uniform, cur0):
    nodes_js = {k: {kk: vv for kk, vv in n.items()} for k, n in nodes.items()}
    for k, n in nodes_js.items():
        n["edges"] = [e["id"] for e in edges if e["src"] == k or e["dst"] == k]
    edges_js = {e["id"]: {"src": nodes[e["src"]]["name"], "dst": nodes[e["dst"]]["name"],
                          "style": e["style"], "styleLabel": e["styleLabel"],
                          "mixed": e["mixed"], "records": e["records"]} for e in edges}

    def share_of(m, name):
        for f in flows[m]["flows"]:
            if f["name"] == name:
                return round(f["share"] * 100, 1)
        return 0.0
    trend = {"months": month_keys,
             "labels": [flows[m]["label"] for m in month_keys],
             "美国": [share_of(m, "美国") for m in month_keys],
             "马来西亚": [share_of(m, "马来西亚") for m in month_keys],
             "泰国": [share_of(m, "泰国") for m in month_keys]}

    mig = stats["migration"]
    comp = stats["grade_comp"]
    if uniform:
        cur_note = f'口径：全期 {cur0}（202501 与 2026H1 同口径，份额与绝对额均可比）；海关数据不分公司，公司级归因为C级推断不承重'
        cur_note_aside = (f'202501 与 2026H1 同为 {cur0} 口径（四维分拆聚合），份额与绝对额均可比。')
        trend_note = f'全期 {cur0} 口径——份额与绝对额均可比'
        mig_card3 = '202501 → 202606 · 同口径可比'
    else:
        cur_note = ('⚠ 口径：月份间币种不一致，跨期只比份额与排名、不比绝对额；'
                    '海关数据不分公司，公司级归因为C级推断不承重')
        cur_note_aside = '月份间币种不一致；跨期只比较份额与排名，不比较绝对金额。'
        trend_note = '月份间币种不一致——走势读份额不读绝对额'
        mig_card3 = '202501 → 202606 · 份额口径（仅比结构）'

    legend_rel = (
        '<span class="grp">边等级</span>'
        '<span class="li"><svg width="52" height="14"><line x1="2" y1="7" x2="50" y2="7" stroke="#475569" stroke-width="3.0"/></svg>实边（实名披露）</span>'
        '<span class="li"><svg width="52" height="14"><line x1="2" y1="7" x2="50" y2="7" stroke="#9ca3af" stroke-width="1.9"/><circle cx="26" cy="7" r="5.5" fill="#fff" stroke="#9ca3af"/><path d="M23.4,4.4 L28.6,9.6 M28.6,4.4 L23.4,9.6" stroke="#6b7280" stroke-width="1.5"/></svg>实边（已死亡）</span>'
        '<span class="li"><svg width="52" height="14"><line x1="2" y1="7" x2="50" y2="7" stroke="#9ca3af" stroke-width="2.6" stroke-dasharray="7 5"/></svg>半边 / 半边槽位（匿名）</span>'
        '<span class="li"><svg width="52" height="14"><line x1="2" y1="7" x2="50" y2="7" stroke="#ea580c" stroke-width="3.0" stroke-dasharray="11 4 2 4"/></svg>推断边（A级）</span>'
        '<span class="li"><svg width="52" height="14"><line x1="2" y1="7" x2="50" y2="7" stroke="#7c3aed" stroke-width="2.6" stroke-dasharray="13 5"/></svg>程序段落泄漏</span>'
        '<span class="sep"></span><span class="grp">国别</span>'
        '<span class="li"><svg width="16" height="14"><circle cx="7" cy="7" r="5" fill="#dc2626"/></svg>中国</span>'
        '<span class="li"><svg width="16" height="14"><circle cx="7" cy="7" r="5" fill="#2563eb"/></svg>美国</span>'
        '<span class="li"><svg width="16" height="14"><circle cx="7" cy="7" r="5" fill="#6b7280"/></svg>其他</span>'
        '<span class="sep"></span><span class="grp">层</span>'
        + "".join(f'<span class="li"><svg width="14" height="14"><rect width="12" height="12" x="1" y="1" rx="3" fill="{LAYER_COLORS[ly]}"/></svg>{ly}</span>'
                  for ly in LAYER_ORDER))

    legend_flow = (
        '<span class="grp">流向层</span>'
        '<span class="li">数据源：中国海关总署出口数据 · <b>HS 85177950</b>（光通信设备的激光收发模块）· 四维分拆聚合 · <b>A级</b>（抓取日期 2026-07-23）</span>'
        '<span class="sep"></span>'
        '<span class="li"><svg width="16" height="14"><rect x="1" y="2" width="12" height="10" rx="2" fill="#dc2626"/></svg>美国</span>'
        '<span class="li"><svg width="16" height="14"><rect x="1" y="2" width="12" height="10" rx="2" fill="#059669"/></svg>马来西亚</span>'
        '<span class="li"><svg width="16" height="14"><rect x="1" y="2" width="12" height="10" rx="2" fill="#0ea5e9"/></svg>泰国</span>'
        '<span class="li"><svg width="16" height="14"><rect x="1" y="2" width="12" height="10" rx="2" fill="#94a3b8"/></svg>其他目的地</span>'
        '<span class="li"><svg width="16" height="14"><rect x="1" y="2" width="12" height="10" rx="2" fill="#cbd5e1"/></svg>"其他"（top10 外合并）</span>'
        '<span class="sep"></span>'
        '<span class="li">边宽∝金额（对比模式双面板同比例尺；最小显示 1.5px）</span>'
        '<span class="li warn">⚠ 目的地≠终端客户：存在转运/分销/封测中转夹层（马来西亚、泰国、中国香港等去向含中转成分），海关目的地不等于最终用户</span>'
        f'<span class="li warn">{cur_note}</span>')

    rel_aside = (
        f'<h2>关系层 · 供应链图谱</h2>'
        f'<div class="hint">节点 <b>{stats["n_nodes"]}</b> 个（nodes.csv 42 + 匿名槽位 {stats["n_slots"]} + 未收录补建 {stats["n_extra"]}）；'
        f'合并边 <b>{stats["n_edges"]}</b> 条（原始记录 81 行，同一供需对多财年合并）。</div>'
        f'<div class="rec"><div class="row"><span class="k">边构成</span>'
        f'实边（实名披露）×{comp["solid"]} · 实边（已死亡）×{comp["dead"]} · 半边/半边槽位×{comp["half"]} · '
        f'推断边（A级）×{comp["inferred"]} · 程序段落泄漏×{comp["leak"]}</div></div>'
        f'<div class="hint" style="margin-top:10px">操作：<br>'
        f'· <b>hover 节点</b>：高亮其全部相连边与对端节点<br>'
        f'· <b>hover 边</b>：tooltip 列出全部年份记录（占比+财年+边等级+锚点）<br>'
        f'· <b>点击边</b>：本栏显示完整四件套（证据文件/锚点/验证状态/备注）<br>'
        f'· <b>点击节点</b>：本栏显示节点档案与相连边清单<br>'
        f'· 滚轮缩放，拖拽空白处平移，左下角按钮复位</div>'
        f'<div class="rec" style="margin-top:12px"><div class="row"><span class="k">数据</span>'
        f'output/edges.csv（81 行）+ output/nodes.csv（42 节点）</div></div>')

    flow_aside = (
        f'<h2>流向层 · 海关出口流向</h2>'
        f'<div class="hint">中国 → 各出口目的地，HS 85177950（光通信设备的激光收发模块），'
        f'海关出口数据（<b>A级</b>）。伙伴取当月金额 top10 + "其他"合并。</div>'
        f'<div class="mixwarn"><b>夹层警示（照写）</b>：目的地≠终端客户。马来西亚、泰国、中国香港等去向含'
        f'转运/分销/封测中转成分；海关目的地不等于最终用户，不能据此把份额分配给任何公司或终端客户。</div>'
        f'<div class="rec"><div class="row"><span class="k">核心迁移</span>'
        f'美国：202501 第1名 {mig["us_2501_share"]} → 202606 第{mig["us_2606_rank"]}名 {mig["us_2606_share"]}；'
        f'马来西亚：202501 第{mig["my_2501_rank"]}名 {mig["my_2501_share"]} → 202606 <b>第1名 {mig["my_2606_share"]}</b>。'
        f'去向重心已从美国切换到马来西亚（数据A级）；归因（关税/东南亚封测中转）为C级推断，不承重。</div></div>'
        f'<div class="rec"><div class="row"><span class="k">口径</span>{cur_note_aside}</div></div>'
        f'<div class="hint" style="margin-top:10px">操作：<br>'
        f'· <b>对比模式</b>：202501 vs 202606 双面板并置（默认）<br>'
        f'· <b>单月模式</b>：拖动滑条切换 7 个月度快照<br>'
        f'· <b>hover 流带/目的地条</b>：月份 / kg / 金额 / 币种 / 占比<br>'
        f'· <b>点击流带</b>：本栏钉住该条流向记录</div>'
        f'<div class="rec" style="margin-top:12px"><div class="row"><span class="k">数据</span>'
        f'flows/out/customs-partners.csv（202501 + 2026H1，海关总署四维分拆聚合，抓取 2026-07-23）'
        f'；对账 flows/out/customs-monthly.csv 月度合计逐月相等</div></div>'
        f'<div class="hint" id="flow-pin" style="margin-top:12px"></div>')

    alias_comment = "\n".join(f'  "{k}" -> "{v}"' for k, v in sorted(ALIAS.items()))

    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>光模块产业图谱 v1.2</title>
<style>
:root{{--ink:#1e293b;--mut:#64748b;--line:#e2e8f0;--panel:#ffffff;--bg:#f1f5f9}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;background:var(--bg);color:var(--ink);overflow:hidden}}
header{{padding:10px 20px 8px;background:var(--panel);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;flex-wrap:wrap}}
header h1{{margin:0;font-size:18px}}
header .sub{{font-size:12px;color:var(--mut);margin-top:3px}}
#tabs{{display:flex;gap:8px}}
#tabs button{{border:1px solid var(--line);background:#f8fafc;border-radius:9px;padding:7px 16px;font-size:13px;font-weight:700;cursor:pointer;color:var(--mut)}}
#tabs button.active{{background:#0f172a;color:#fff;border-color:#0f172a}}
#legend{{display:flex;flex-wrap:wrap;gap:7px 20px;align-items:center;padding:7px 20px;background:var(--panel);border-bottom:1px solid var(--line);font-size:12px}}
#legend>span{{display:contents}}
.li{{display:flex;align-items:center;gap:6px;white-space:nowrap}}
.li svg{{display:block}}
.li.warn{{color:#9a3412;font-weight:600;white-space:normal}}
#legend .sep{{width:1px;height:18px;background:var(--line)}}
#legend .grp{{color:var(--mut);font-weight:700}}
.layer{{display:none;height:calc(100vh - 118px)}}
.layer.active{{display:flex}}
#stage{{flex:1;position:relative;overflow:hidden;cursor:grab}}
#stage.panning{{cursor:grabbing}}
#g{{width:100%;height:100%;display:block}}
#zoom{{position:absolute;left:14px;bottom:14px;display:flex;gap:6px;z-index:5}}
#zoom button{{width:34px;height:34px;border:1px solid var(--line);background:#fff;border-radius:8px;font-size:17px;cursor:pointer;color:var(--ink)}}
#zoom button:hover{{background:#f1f5f9}}
aside{{width:390px;min-width:390px;background:var(--panel);border-left:1px solid var(--line);overflow-y:auto;padding:16px 18px;font-size:12.5px;line-height:1.65}}
aside h2{{font-size:14px;margin:0 0 8px}}
aside .hint{{color:var(--mut)}}
.badge{{display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;font-weight:700;color:#fff;margin-left:6px}}
.rec{{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;background:#fbfdff}}
.rec .row{{margin:2px 0;word-break:break-all}}
.rec .k{{color:var(--mut);display:inline-block;min-width:62px;font-weight:700}}
.mixwarn{{background:#fff7ed;border:1px solid #fdba74;color:#9a3412;border-radius:8px;padding:8px 11px;font-size:11.5px;margin:8px 0;line-height:1.6}}
.lyr{{font-size:14.5px;font-weight:800;letter-spacing:1px}}
.nname{{font-weight:700;fill:#0f172a}}
.ntype{{fill:#64748b}}
.slot-lbl{{font-size:10.5px;font-weight:700;fill:#334155}}
.slot-sub{{font-size:9px;fill:#94a3b8}}
.slot-q{{font-size:15px;font-weight:800;fill:#94a3b8}}
.node{{cursor:pointer}}
#g.focusing .edge{{opacity:.06}}
#g.focusing .node{{opacity:.22}}
#g.focusing .edge.hot{{opacity:1}}
#g.focusing .node.hot{{opacity:1}}
.edge.hot .eln{{stroke-width:4 !important}}
.edge.sel .eln{{stroke-width:4.5 !important}}
.edge.sel .hit{{stroke:#0ea5e9;stroke-opacity:.18;stroke-width:18}}
.node.sel rect:first-of-type{{stroke-width:3.2}}
#tooltip{{position:fixed;display:none;max-width:460px;background:#0f172a;color:#e2e8f0;padding:10px 13px;border-radius:9px;font-size:11.5px;line-height:1.6;pointer-events:none;z-index:60;box-shadow:0 8px 24px rgba(0,0,0,.3)}}
#tooltip .t{{font-weight:800;margin-bottom:4px;color:#fff}}
#tooltip .r{{padding:4px 0;border-top:1px solid rgba(255,255,255,.13)}}
#tooltip .r:first-of-type{{border-top:none}}
#tooltip b{{color:#93c5fd}}
#tooltip .a{{color:#94a3b8;word-break:break-all}}
#tooltip .more{{color:#38bdf8;margin-top:5px;font-size:11px}}
/* ── 流向层 ── */
#layer-flow{{flex-direction:column}}
#flow-wrap{{flex:1;display:flex;min-height:0}}
#flow-main{{flex:1;display:flex;flex-direction:column;overflow-y:auto;padding:10px 18px}}
#flow-controls{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:6px}}
#flow-controls .mode button{{border:1px solid var(--line);background:#fff;border-radius:8px;padding:5px 12px;font-size:12px;font-weight:700;cursor:pointer;color:var(--mut)}}
#flow-controls .mode button.active{{background:#0f172a;color:#fff;border-color:#0f172a}}
#month-slider{{width:280px}}
#mig-strip{{display:flex;gap:14px;flex-wrap:wrap;margin:4px 0 10px}}
.mig-card{{border:1px solid var(--line);border-radius:10px;padding:8px 14px;background:#fff;font-size:12.5px;font-weight:600}}
.mig-card b{{font-size:14px}}
#panels{{display:flex;gap:18px;flex-wrap:wrap}}
.panel{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;flex:1;min-width:430px}}
.panel h3{{margin:2px 0 2px;font-size:13.5px}}
.panel .psub{{font-size:11px;color:var(--mut);margin-bottom:4px}}
.panel svg{{width:100%;display:block}}
.rib{{cursor:pointer;transition:opacity .12s}}
.dbar{{cursor:pointer}}
#trend-box{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin-bottom:12px}}
#trend-box h3{{margin:0 0 4px;font-size:13px}}
#trend-box svg{{width:100%;display:block}}
@media (max-width:1100px){{aside{{width:310px;min-width:310px}}}}
</style>
</head>
<body>
<header>
  <div>
    <h1>光模块产业图谱 <span style="font-size:12px;color:#64748b">v1.2 · 双层视图</span></h1>
    <div class="sub">①关系层＝81 边供应链图谱（v1.0 口径重新实现）｜②流向层＝HS 85177950 中国海关出口去向（202501 + 2026H1）</div>
  </div>
  <div id="tabs">
    <button id="tab-rel" class="active">① 关系层 · 供应链图谱（81边）</button>
    <button id="tab-flow">② 流向层 · 海关出口流向</button>
  </div>
</header>
<div id="legend"><span id="legend-rel">{legend_rel}</span><span id="legend-flow" style="display:none">{legend_flow}</span></div>

<div id="layer-rel" class="layer active">
  <div id="stage">
    {rel_svg_str}
    <div id="zoom"><button id="zin" title="放大">+</button><button id="zout" title="缩小">−</button><button id="zreset" title="复位">⌂</button></div>
  </div>
  <aside id="side-rel">{rel_aside}</aside>
</div>

<div id="layer-flow" class="layer">
  <div id="flow-wrap">
    <div id="flow-main">
      <div id="flow-controls">
        <span class="mode">
          <button id="mode-compare" class="active">对比模式 202501 vs 202606</button>
          <button id="mode-single">单月模式</button>
        </span>
        <span id="slider-box" style="display:none;align-items:center;gap:10px">
          <input type="range" id="month-slider" min="0" max="{len(month_keys) - 1}" step="1" value="{len(month_keys) - 1}">
          <b id="slider-label"></b>
        </span>
      </div>
      <div id="mig-strip">
        <span class="mig-card" style="border-left:5px solid #dc2626">美国 <b>#{mig["us_2501_rank"]} {mig["us_2501_share"]}</b> → <b>#{mig["us_2606_rank"]} {mig["us_2606_share"]}</b> ▼</span>
        <span class="mig-card" style="border-left:5px solid #059669">马来西亚 <b>#{mig["my_2501_rank"]} {mig["my_2501_share"]}</b> → <b>#{mig["my_2606_rank"]} {mig["my_2606_share"]}</b> ▲ 升至第一</span>
        <span class="mig-card" style="color:#64748b">{mig_card3}</span>
      </div>
      <div id="trend-box">
        <h3>月度份额走势：美国 vs 马来西亚 vs 泰国（占当月出口金额 %）</h3>
        <svg id="trend" viewBox="0 0 1120 168" preserveAspectRatio="xMinYMin meet" xmlns="http://www.w3.org/2000/svg"></svg>
      </div>
      <div id="panels"></div>
    </div>
    <aside id="side-flow">{flow_aside}</aside>
  </div>
</div>

<div id="tooltip"></div>
<!-- 显式归一化别名表（生成时固化，供审阅）：
{alias_comment}
匿名槽位规则：边端点含"匿名"→按(所属公司,原始标签)建槽位节点；标签以"供应商"开头→器件/芯片层，否则→终端/云层。
未收录实体：edges.csv 出现而 nodes.csv 未收录的实名实体→如实补建，层=其他。
-->
<script>
const NODES = {js_json(nodes_js)};
const EDGES = {js_json(edges_js)};
const FLOW_MONTHS = {js_json(month_keys)};
const FLOWS = {js_json(flows)};
const TREND = {js_json(trend)};

const tip = document.getElementById('tooltip');
function escH(s){{ return String(s==null?'':s).replace(/[&<>"']/g, c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function showTip(html,e){{ tip.innerHTML=html; tip.style.display='block'; moveTip(e); }}
function moveTip(e){{ const p=16; let x=e.clientX+p, y=e.clientY+p;
  tip.style.left='0px'; tip.style.top='0px';
  const r=tip.getBoundingClientRect();
  if(x+r.width>innerWidth-8) x=e.clientX-r.width-p;
  if(y+r.height>innerHeight-8) y=e.clientY-r.height-p;
  tip.style.left=Math.max(4,x)+'px'; tip.style.top=Math.max(4,y)+'px'; }}
function hideTip(){{ tip.style.display='none'; }}

/* ════════ 双层切换 ════════ */
const tabRel=document.getElementById('tab-rel'), tabFlow=document.getElementById('tab-flow'),
      layerRel=document.getElementById('layer-rel'), layerFlow=document.getElementById('layer-flow'),
      legendRel=document.getElementById('legend-rel'), legendFlow=document.getElementById('legend-flow');
function switchLayer(flow){{
  tabRel.classList.toggle('active',!flow); tabFlow.classList.toggle('active',flow);
  layerRel.classList.toggle('active',!flow); layerFlow.classList.toggle('active',flow);
  legendRel.style.display=flow?'none':''; legendFlow.style.display=flow?'':'none';
  hideTip();
}}
tabRel.onclick=()=>switchLayer(false);
tabFlow.onclick=()=>switchLayer(true);

/* ════════ 关系层 ════════ */
const svg=document.getElementById('g'), stage=document.getElementById('stage'), sideRel=document.getElementById('side-rel');
const VB={{x:0,y:0,w:{rel_w},h:{rel_h}}}, VB0=Object.assign({{}},VB);
function applyVB(){{ svg.setAttribute('viewBox',VB.x+' '+VB.y+' '+VB.w+' '+VB.h); }}
function svgPt(e){{ const r=svg.getBoundingClientRect();
  return {{x:VB.x+(e.clientX-r.left)/r.width*VB.w, y:VB.y+(e.clientY-r.top)/r.height*VB.h}}; }}
stage.addEventListener('wheel', e=>{{ e.preventDefault();
  const f=e.deltaY>0?1.14:0.877, p=svgPt(e);
  VB.x=p.x-(p.x-VB.x)*f; VB.y=p.y-(p.y-VB.y)*f; VB.w*=f; VB.h*=f; applyVB();
}},{{passive:false}});
let drag=null;
stage.addEventListener('mousedown', e=>{{ if(e.target.closest('.node,.edge,#zoom'))return;
  drag={{x:e.clientX,y:e.clientY}}; stage.classList.add('panning'); }});
window.addEventListener('mousemove', e=>{{ if(!drag)return;
  const r=svg.getBoundingClientRect();
  VB.x-=(e.clientX-drag.x)/r.width*VB.w; VB.y-=(e.clientY-drag.y)/r.height*VB.h;
  drag={{x:e.clientX,y:e.clientY}}; applyVB(); }});
window.addEventListener('mouseup', ()=>{{ drag=null; stage.classList.remove('panning'); }});
document.getElementById('zin').onclick=()=>{{ VB.w*=0.8; VB.h*=0.8; applyVB(); }};
document.getElementById('zout').onclick=()=>{{ VB.w*=1.25; VB.h*=1.25; applyVB(); }};
document.getElementById('zreset').onclick=()=>{{ Object.assign(VB,VB0); applyVB(); }};

function tipHtml(d){{
  let h='<div class="t">'+escH(d.src)+' → '+escH(d.dst)+'</div>';
  d.records.forEach(r=>{{
    h+='<div class="r"><b>'+escH(r['财年'])+'</b> ｜ '+escH(r['占比或金额'])+
       ' ｜ '+escH(r['边等级'])+'<div class="a">⚓ '+escH(r['锚点'])+'</div></div>';
  }});
  h+='<div class="more">点击边 → 侧栏查看完整四件套（证据文件/锚点/验证状态/备注）</div>';
  return h;
}}
function focusNode(key,on){{
  const d=NODES[key];
  svg.classList.toggle('focusing',on);
  d.edges.forEach(id=>{{ const g=svg.querySelector('[data-e="'+id+'"]'); if(g)g.classList.toggle('hot',on); }});
  const nb=new Set([key]);
  d.edges.forEach(id=>{{ const e=EDGES[id];
    Object.keys(NODES).forEach(k=>{{ if(NODES[k].name===e.src||NODES[k].name===e.dst) nb.add(k); }}); }});
  nb.forEach(k=>{{ const g=svg.querySelector('[data-n="'+k+'"]'); if(g)g.classList.toggle('hot',on); }});
}}
svg.querySelectorAll('.node').forEach(g=>{{
  const key=g.getAttribute('data-n');
  g.addEventListener('mouseenter',()=>focusNode(key,true));
  g.addEventListener('mouseleave',()=>focusNode(key,false));
  g.addEventListener('click',()=>selectNode(key));
}});
function clearSel(){{ svg.querySelectorAll('.sel').forEach(x=>x.classList.remove('sel')); }}
function selectEdge(id){{
  clearSel(); const g=svg.querySelector('[data-e="'+id+'"]'); if(g)g.classList.add('sel');
  const d=EDGES[id];
  const STYLE_COLOR={{solid:'#475569',dead:'#9ca3af',half:'#9ca3af',inferred:'#ea580c',leak:'#7c3aed'}};
  let h='<h2>边详情 '+escH(d.src)+' → '+escH(d.dst)+
        '<span class="badge" style="background:'+(STYLE_COLOR[d.style]||'#475569')+'">'+escH(d.styleLabel)+'</span></h2>';
  if(d.mixed) h+='<div class="mixwarn">本合并边含多种边等级，按"最弱证据等级"着色；逐年等级见下。</div>';
  h+='<div class="hint">合并 '+d.records.length+' 条记录（同一供需对多期合并为一条边）：</div>';
  d.records.forEach(r=>{{
    h+='<div class="rec">'+
      '<div class="row"><span class="k">编号</span>'+escH(r['edge_id'])+'</div>'+
      '<div class="row"><span class="k">财年</span>'+escH(r['财年'])+'</div>'+
      '<div class="row"><span class="k">占比/金额</span><b>'+escH(r['占比或金额'])+'</b></div>'+
      '<div class="row"><span class="k">边等级</span>'+escH(r['边等级'])+'</div>'+
      '<div class="row"><span class="k">证据文件</span>'+escH(r['证据文件'])+'</div>'+
      '<div class="row"><span class="k">锚点</span>'+escH(r['锚点'])+'</div>'+
      '<div class="row"><span class="k">验证状态</span>'+escH(r['验证状态'])+'</div>'+
      (r['备注']?'<div class="row"><span class="k">备注</span>'+escH(r['备注'])+'</div>':'')+'</div>';
  }});
  sideRel.innerHTML=h;
}}
function selectNode(key){{
  clearSel(); const g=svg.querySelector('[data-n="'+key+'"]'); if(g)g.classList.add('sel');
  const d=NODES[key];
  let h='<h2>节点 '+escH(d.name)+(d.slot?'<span class="badge" style="background:#6b7280">匿名槽位</span>':'')+'</h2>';
  h+='<div class="rec">'+
     '<div class="row"><span class="k">类型</span>'+escH(d.type)+'</div>'+
     '<div class="row"><span class="k">层</span>'+escH(d.layer)+'</div>'+
     (d.country?'<div class="row"><span class="k">国别</span>'+escH(d.country)+'</div>':'')+
     (d.code?'<div class="row"><span class="k">代码</span>'+escH(d.code)+'</div>':'')+
     (d.memo?'<div class="row"><span class="k">备注</span>'+escH(d.memo)+'</div>':'')+
     '<div class="row"><span class="k">相连边</span>'+d.edges.length+' 条（hover 节点可高亮）</div></div>';
  h+='<div class="hint">相连边：'+d.edges.map(id=>'<div>· '+escH(EDGES[id].src)+' → '+escH(EDGES[id].dst)+'（'+escH(EDGES[id].styleLabel)+'）</div>').join('')+'</div>';
  sideRel.innerHTML=h;
}}
svg.querySelectorAll('.edge').forEach(g=>{{
  const id=g.getAttribute('data-e');
  g.addEventListener('mouseenter',e=>showTip(tipHtml(EDGES[id]),e));
  g.addEventListener('mousemove',moveTip);
  g.addEventListener('mouseleave',hideTip);
  g.addEventListener('click',()=>{{ hideTip(); selectEdge(id); }});
}});

/* ════════ 流向层 ════════ */
const HL={{"马来西亚":"#059669","美国":"#dc2626","泰国":"#0ea5e9"}};
const OTHER_DEST="#94a3b8", AGG="#cbd5e1";
const UNIFORM={str(uniform).lower()};
function colorOf(name){{ return HL[name]||(name==="其他"?AGG:OTHER_DEST); }}
function fmtInt(n){{ return Number(n).toLocaleString('en-US'); }}
function humanAmt(a,cur){{
  if(cur==='RMB') return '≈'+(a/1e8).toFixed(2)+'亿元';
  return '≈$'+(a/1e8).toFixed(2)+'亿';
}}
function flowTip(m, f){{
  const d=FLOWS[m];
  return '<div class="t">'+d.label+' · 中国 → '+escH(f.name)+'</div>'+
    '<div class="r">月份 <b>'+m+'</b>（'+d.label+'）</div>'+
    '<div class="r">金额 <b>'+fmtInt(f.amount)+' '+d.currency+'</b>（'+humanAmt(f.amount,d.currency)+'）</div>'+
    '<div class="r">出口量 <b>'+fmtInt(f.kg)+' kg</b></div>'+
    '<div class="r">占当月 <b>'+(f.share*100).toFixed(1)+'%</b> ｜ 币种 '+d.currency+'</div>'+
    (f.n?'<div class="r">"其他"＝top10 外 '+f.n+' 个伙伴合并</div>':'')+
    '<div class="r a">HS 85177950 · 海关出口（A级）｜目的地≠终端客户</div>';
}}
function pinFlow(m, f){{
  const d=FLOWS[m];
  document.getElementById('flow-pin').innerHTML=
    '<b>已钉住流向</b><div class="rec">'+
    '<div class="row"><span class="k">月份</span>'+d.label+'（'+m+'）</div>'+
    '<div class="row"><span class="k">流向</span>中国 → <b>'+escH(f.name)+'</b></div>'+
    '<div class="row"><span class="k">金额</span><b>'+fmtInt(f.amount)+' '+d.currency+'</b>（'+humanAmt(f.amount,d.currency)+'）</div>'+
    '<div class="row"><span class="k">出口量</span>'+fmtInt(f.kg)+' kg</div>'+
    '<div class="row"><span class="k">占当月</span>'+(f.share*100).toFixed(1)+'%</div>'+
    '<div class="row"><span class="k">数据源</span>海关总署 HS 85177950 四维分拆聚合（A级）</div></div>';
}}
function sankeyPanel(m, sharedScale){{
  const d=FLOWS[m], W=880, H=Math.max(560, d.flows.length*46+40);
  const xSrc=24, wSrc=26, xDst=W-216, wDst=26;
  const innerH=H-56, top0=36;
  const scale=sharedScale||(innerH*0.94/d.total);
  const heights=d.flows.map(f=>Math.max(1.5, f.amount*scale));
  const used=heights.reduce((a,b)=>a+b,0);
  const gap=(innerH-used)/(d.flows.length-1);
  let s='<div class="panel"><h3>'+d.label+' <span class="badge" style="background:#0f172a">'+d.currency+'</span></h3>'+
    '<div class="psub">出口合计 <b>'+fmtInt(d.total)+' '+d.currency+'</b>（'+humanAmt(d.total,d.currency)+'）· '+
    fmtInt(d.total_kg)+' kg · '+d.n_partners+' 个伙伴（取 top10 + 其他）</div>'+
    '<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg">';
  // 源柱
  s+='<rect x="'+xSrc+'" y="'+top0+'" width="'+wSrc+'" height="'+innerH+'" rx="4" fill="#0f172a"/>'+
     '<text x="'+(xSrc+wSrc+8)+'" y="'+(top0+14)+'" font-size="12.5" font-weight="800" fill="#0f172a">中国（出口合计）</text>'+
     '<text x="'+(xSrc+wSrc+8)+'" y="'+(top0+30)+'" font-size="10.5" fill="#64748b">'+humanAmt(d.total,d.currency)+' · '+fmtInt(d.total_kg)+' kg</text>';
  // 流带与目的地条（两侧同序堆叠，无交叉）
  let y=top0;
  d.flows.forEach((f,i)=>{{
    const h=heights[i], col=colorOf(f.name);
    const y0=y, y1=y;
    const x0=xSrc+wSrc, x1=xDst;
    const mx=(x0+x1)/2;
    const path='M'+x0+','+y0.toFixed(1)+' C'+mx+','+y0.toFixed(1)+' '+mx+','+y1.toFixed(1)+' '+x1+','+y1.toFixed(1)+
               ' L'+x1+','+(y1+h).toFixed(1)+' C'+mx+','+(y1+h).toFixed(1)+' '+mx+','+(y0+h).toFixed(1)+
               ' '+x0+','+(y0+h).toFixed(1)+' Z';
    s+='<path class="rib" data-m="'+m+'" data-i="'+i+'" d="'+path+'" fill="'+col+'" fill-opacity="'+(HL[f.name]?0.72:0.5)+'"/>';
    y+=h+gap;
  }});
  y=top0;
  d.flows.forEach((f,i)=>{{
    const h=heights[i], col=colorOf(f.name);
    const rank=f.name==="其他"?'—':('#'+(i+1));
    const lab=rank+' '+f.name+' · '+(f.share*100).toFixed(1)+'%';
    s+='<rect class="dbar" data-m="'+m+'" data-i="'+i+'" x="'+xDst+'" y="'+y.toFixed(1)+'" width="'+wDst+'" height="'+h.toFixed(1)+'" rx="3" fill="'+col+'"/>'+
       '<text x="'+(xDst+wDst+8)+'" y="'+(y+Math.min(h-2,13))+'" font-size="11.5" font-weight="'+(HL[f.name]?800:600)+'" fill="'+(HL[f.name]?col:'#334155')+'">'+escH(lab)+'</text>'+
       '<text x="'+(xDst+wDst+8)+'" y="'+(y+Math.min(h-2,26))+'" font-size="9.5" fill="#94a3b8">'+humanAmt(f.amount,d.currency)+'</text>';
    y+=h+gap;
  }});
  s+='</svg></div>';
  return s;
}}
function bindFlowEvents(root){{
  root.querySelectorAll('.rib,.dbar').forEach(el=>{{
    const m=el.getAttribute('data-m'), i=+el.getAttribute('data-i');
    const f=FLOWS[m].flows[i];
    el.addEventListener('mouseenter',e=>{{ el.style.fillOpacity=0.95; showTip(flowTip(m,f),e); }});
    el.addEventListener('mousemove',moveTip);
    el.addEventListener('mouseleave',()=>{{ el.style.fillOpacity=''; hideTip(); }});
    el.addEventListener('click',()=>{{ hideTip(); pinFlow(m,f); }});
  }});
}}
const panels=document.getElementById('panels');
function renderCompare(){{
  let sc=null;
  if(UNIFORM){{
    const innerH=560-56;
    sc=innerH*0.94/Math.max(FLOWS['202501'].total,FLOWS['202606'].total);
  }}
  panels.innerHTML=sankeyPanel('202501',sc)+sankeyPanel('202606',sc);
  bindFlowEvents(panels);
}}
function renderSingle(idx){{
  const m=FLOW_MONTHS[idx];
  document.getElementById('slider-label').textContent=FLOWS[m].label+'（'+FLOWS[m].currency+'）';
  panels.innerHTML=sankeyPanel(m,null);
  bindFlowEvents(panels);
}}
const modeCmp=document.getElementById('mode-compare'), modeSgl=document.getElementById('mode-single'),
      sliderBox=document.getElementById('slider-box'), slider=document.getElementById('month-slider');
modeCmp.onclick=()=>{{ modeCmp.classList.add('active'); modeSgl.classList.remove('active');
  sliderBox.style.display='none'; renderCompare(); }};
modeSgl.onclick=()=>{{ modeSgl.classList.add('active'); modeCmp.classList.remove('active');
  sliderBox.style.display='inline-flex'; renderSingle(+slider.value); }};
slider.oninput=()=>renderSingle(+slider.value);

/* 月度份额走势 */
(function renderTrend(){{
  const svgT=document.getElementById('trend');
  const W=1120, H=168, L=46, R=120, T=14, B=30;
  const xs=i=>L+(W-L-R)*(i/(TREND.months.length-1));
  const maxV=Math.max(...TREND["美国"],...TREND["马来西亚"],...TREND["泰国"],50);
  const ys=v=>T+(H-T-B)*(1-v/maxV);
  let s='<line x1="'+L+'" y1="'+(H-B)+'" x2="'+(W-R+10)+'" y2="'+(H-B)+'" stroke="#e2e8f0"/>';
  [0,10,20,30,40,50].forEach(v=>{{
    s+='<line x1="'+L+'" y1="'+ys(v)+'" x2="'+(W-R+10)+'" y2="'+ys(v)+'" stroke="#f1f5f9"/>'+
       '<text x="'+(L-6)+'" y="'+(ys(v)+4)+'" text-anchor="end" font-size="9.5" fill="#94a3b8">'+v+'%</text>';
  }});
  TREND.labels.forEach((lb,i)=>{{
    s+='<text x="'+xs(i)+'" y="'+(H-10)+'" text-anchor="middle" font-size="10" fill="#64748b">'+TREND.months[i]+'</text>';
  }});
  [["美国","#dc2626"],["马来西亚","#059669"],["泰国","#0ea5e9"]].forEach(([name,col])=>{{
    const pts=TREND[name].map((v,i)=>xs(i)+','+ys(v)).join(' ');
    s+='<polyline points="'+pts+'" fill="none" stroke="'+col+'" stroke-width="2.6"/>';
    TREND[name].forEach((v,i)=>{{
      s+='<circle cx="'+xs(i)+'" cy="'+ys(v)+'" r="3.2" fill="'+col+'"/>';
      if(i===0||i===TREND[name].length-1)
        s+='<text x="'+xs(i)+'" y="'+(ys(v)-7)+'" text-anchor="middle" font-size="10" font-weight="700" fill="'+col+'">'+v+'%</text>';
    }});
    s+='<text x="'+(W-R+16)+'" y="'+ys(TREND[name][TREND[name].length-1])+ '" font-size="11" font-weight="700" fill="'+col+'">'+name+'</text>';
  }});
  s+='<text x="'+L+'" y="'+(T+2)+'" font-size="10" fill="#94a3b8">{trend_note}</text>';
  svgT.innerHTML=s;
}})();
renderCompare();
</script>
</body>
</html>'''


# ───────────────────────── 自测断言 ─────────────────────────

def run_assertions(html_text, nodes, edges, flows, month_keys):
    results = []

    def chk(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    out = OUT_HTML
    chk("文件已生成且非空", out.exists() and out.stat().st_size > 50000,
        f"{out.stat().st_size:,} bytes")
    chk("含字符串「马来西亚」", "马来西亚" in html_text)
    chk("含字符串「85177950」", "85177950" in html_text)
    chk("含「目的地≠终端客户」夹层警示", "目的地≠终端客户" in html_text)
    ext_pat = re.compile(r'(src|href)\s*=\s*["\']https?://|<link\b|@import|url\(\s*["\']?https?://'
                         r'|fetch\(|XMLHttpRequest|<a\s|srcset', re.IGNORECASE)
    chk("零外链（无外部资源/超链接/CDN）", not ext_pat.search(html_text))
    chk("双层切换控件在位", all(s in html_text for s in
        ('id="tab-rel"', 'id="tab-flow"', 'id="layer-rel"', 'id="layer-flow"')))
    chk("UTF-8 中文声明", 'charset="utf-8"' in html_text and 'lang="zh-CN"' in html_text)

    n_records = sum(len(e["records"]) for e in edges)
    chk("关系层：81 行记录全量入图", n_records == 81, f"records={n_records}")
    svg_nodes = html_text.count('class="node"')
    chk("关系层：SVG 节点数=模型节点数", svg_nodes == len(nodes),
        f"svg={svg_nodes} model={len(nodes)}")
    svg_edges = html_text.count('class="edge"')
    chk("关系层：SVG 边数=合并边数", svg_edges == len(edges),
        f"svg={svg_edges} merged={len(edges)}")
    chk("关系层：边等级构成合法", all(e["style"] in GRADE_STYLE.values() for e in edges))

    chk("流向层：月份=7（契约 202501+2026H1）", month_keys == sorted(MONTH_SCOPE),
        ",".join(month_keys))
    chk("流向层：每月 top10+其他=11 条流向", all(len(flows[m]["flows"]) == 11 for m in month_keys))
    monthly = {r["月份"]: (int(r["金额"]), r["币种"]) for r in read_csv_dicts(MONTHLY_CSV)}
    ok_recon = all(flows[m]["total"] == monthly[m][0] and flows[m]["currency"] == monthly[m][1]
                   for m in month_keys if m in monthly)
    chk("流向层：月度合计与 customs-monthly 对账相等", ok_recon)
    curs = {flows[m]["currency"] for m in month_keys}
    chk("流向层：币种可标注（RMB/USD）", curs <= {"RMB", "USD"},
        "统一" + next(iter(curs)) if len(curs) == 1 else "混用" + "/".join(sorted(curs)))
    chk("流向层：top10+其他 求和=当月总额",
        all(sum(f["amount"] for f in flows[m]["flows"]) == flows[m]["total"] for m in month_keys))
    chk("流向层：hover 四要素字段在位（月份/kg/金额/币种）",
        all(s in html_text for s in ("月份", " kg", "金额", "币种")))

    def rank_of(m, name):
        names = [f["name"] for f in flows[m]["flows"]]
        return names.index(name) + 1 if name in names else None
    us_2501 = flows["202501"]["flows"][0]["name"] == "美国"
    chk("迁移断言：202501 美国为第1大去向", us_2501,
        f"202501 #1={flows['202501']['flows'][0]['name']}")
    my_2606_first = flows["202606"]["flows"][0]["name"] == "马来西亚"
    us_2606_rank = rank_of("202606", "美国")
    chk("迁移断言：202606 马来西亚第1且美国跌出前3",
        my_2606_first and us_2606_rank and us_2606_rank > 3,
        f"202606 #1={flows['202606']['flows'][0]['name']} 美国=#{us_2606_rank}")
    chk("迁移断言：美国份额 202501→202606 大幅下降",
        flows["202606"]["flows"][us_2606_rank - 1]["share"] < flows["202501"]["flows"][0]["share"] * 0.5,
        f"{flows['202501']['flows'][0]['share']:.1%}→{flows['202606']['flows'][us_2606_rank-1]['share']:.1%}")
    chk("图例注明数据等级（A级）与 HS 商品名", "A级" in html_text and "光通信设备的激光收发模块" in html_text)
    return results


# ───────────────────────── main ─────────────────────────

def main():
    edge_rows = read_csv_dicts(EDGES_CSV)
    node_rows = read_csv_dicts(NODES_CSV)
    partner_rows = read_csv_dicts(PARTNERS_CSV)
    assert len(edge_rows) == 81, f"edges.csv 行数异常: {len(edge_rows)}"

    nodes, edges = build_rel_model(edge_rows, node_rows)
    pos, rel_w, rel_h, layer_boxes = rel_layout(nodes)
    svg_str = rel_svg(nodes, edges, pos, rel_w, rel_h, layer_boxes)

    flows = build_flow_model([r for r in partner_rows if r["月份"] in MONTH_SCOPE])
    month_keys = sorted(flows.keys())
    missing_scope = [m for m in MONTH_SCOPE if m not in flows]
    assert not missing_scope, f"customs-partners.csv 缺契约月份: {missing_scope}"
    currencies = {flows[m]["currency"] for m in month_keys}
    uniform = len(currencies) == 1
    cur0 = next(iter(currencies)) if uniform else ""

    n_slots = sum(1 for n in nodes.values() if n["slot"])
    n_extra = sum(1 for n in nodes.values() if n["type"] == "未收录实体")
    comp = {"solid": 0, "dead": 0, "half": 0, "inferred": 0, "leak": 0}
    for e in edges:
        comp[e["style"]] += 1

    def rank_share(m, name):
        for i, f in enumerate(flows[m]["flows"]):
            if f["name"] == name:
                return i + 1, f"{f['share'] * 100:.1f}%"
        return None, "0%"
    us_r1, us_s1 = rank_share("202501", "美国")
    us_r6, us_s6 = rank_share("202606", "美国")
    my_r1, my_s1 = rank_share("202501", "马来西亚")
    my_r6, my_s6 = rank_share("202606", "马来西亚")
    stats = {
        "n_nodes": len(nodes), "n_slots": n_slots, "n_extra": n_extra, "n_edges": len(edges),
        "grade_comp": comp,
        "migration": {"us_2501_rank": us_r1, "us_2501_share": us_s1,
                      "us_2606_rank": us_r6, "us_2606_share": us_s6,
                      "my_2501_rank": my_r1, "my_2501_share": my_s1,
                      "my_2606_rank": my_r6, "my_2606_share": my_s6},
    }

    html_text = build_html(nodes, edges, svg_str, rel_w, rel_h, flows, month_keys, stats,
                           uniform, cur0)
    OUT_HTML.write_text(html_text, encoding="utf-8")

    results = run_assertions(html_text, nodes, edges, flows, month_keys)

    # 流向层计数：节点=中国+去重目的地(含"其他")；边=月度流向77(7月×11)/去重
    dests = set()
    n_flow_edges = 0
    for m in month_keys:
        for f in flows[m]["flows"]:
            dests.add(f["name"])
            n_flow_edges += 1

    print("=" * 64)
    print(f"产出文件: {OUT_HTML}")
    print(f"关系层: 节点 {len(nodes)}（实名 {len(nodes) - n_slots} = nodes.csv 42 + 未收录补建 {n_extra}；"
          f"匿名槽位 {n_slots}）· 合并边 {len(edges)} 条（← edges.csv 81 行；"
          f"实边{comp['solid']}/死亡{comp['dead']}/半边系{comp['half']}/推断{comp['inferred']}/泄漏{comp['leak']}）")
    print(f"流向层: 节点 {1 + len(dests)}（中国 + 目的地 {len(dests)} 含\"其他\"）· "
          f"流向边 {n_flow_edges} 条（{len(month_keys)} 月 × top10+其他；去重 {len(dests)} 条中国→目的地）· "
          f"口径 {'统一' + cur0 if uniform else '混用' + '/'.join(sorted(currencies))}")
    print("-" * 64)
    n_fail = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            n_fail += 1
        print(f"[{mark}] {name}" + (f"  ({detail})" if detail else ""))
    print("-" * 64)
    print(f"断言 {len(results)} 项：{len(results) - n_fail} PASS / {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
