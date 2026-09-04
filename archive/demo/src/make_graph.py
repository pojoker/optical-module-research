#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo/src/make_graph.py — Stage4 可视化：edges.csv/nodes.csv → 自包含 graph.html

CLI:
    python3 demo/src/make_graph.py --edges <edges.csv> --nodes <nodes.csv> --out <graph.html>

契约来源：demo/SPEC.md 「Stage4 可视化契约」+「开发纪律」。
只用 Python 3.11+ 标准库（argparse/csv/json/re/html），不引入任何第三方依赖，
不生成外链/CDN 资源——SVG + 内联 CSS/JS，浏览器双击即可打开。

── 自测（按 SPEC 要求，命令与结果写在此处）──────────────────────────────
命令：
    python3 demo/src/make_graph.py \
        --edges output/edges.csv --nodes output/nodes.csv \
        --out /tmp/graph_test.html

结果（2026-07-23 本机跑通）：
    - 退出码 0，无异常抛出。
    - 输出文件 /tmp/graph_test.html 非空（约 90KB+），
      grep 确认包含 <svg ...> 根元素、37 个真实节点 + 若干合成的
      "虚拟节点"（见下方假设 3）、以及按 供方+需方 合并后的边（71 行
      edges.csv 合并为约 60 条可视化边，同一 供方/需方 对的多财年记录
      合并进同一条边的 hover tooltip）。
    - 用 python3 -c "import re,pathlib; s=pathlib.Path('/tmp/graph_test.html')
      .read_text(encoding='utf-8'); assert '<svg' in s and s.count('class=\"edge-line\"')>0"
      验证通过。

── 对 edges.csv / nodes.csv 数据的假设（重要，供下游复核）──────────────
1. 【实体名对不齐】edges.csv 的 供方/需方 列里，约有 20 个名字在
   nodes.csv 的 名称 列里找不到精确匹配（例如 "AAOI" vs 节点表的
   "Applied Optoelectronics(AAOI)"；"华为+海思" vs "华为(含海思)"；
   "ficonTEC(罗博特科)" vs "罗博特科/ficonTEC"；"NVIDIA(客户)"/"Fabrinet(解匿)"
   这类在名字后加了槽位注记的写法）。本脚本做了两层归一化匹配：
     a) 截断第一个 "(" / "（" / "+" 之后的后缀，按核心名做精确匹配；
     b) 对节点名按 "/" "、" 切分成 token 再匹配（如 "罗博特科/ficonTEC"
        产出 token "ficonTEC"）；
     c) 对纯 ASCII 缩写（如 "AAOI"）额外做一次原始子串包含匹配。
   这样能把 34 处未对齐的名字里的绝大多数（20+）正确指回已有节点，
   避免图上出现大量本该是同一家公司的重复节点。
2. 【合并后仍无法解析的名字】上述归一化后仍找不到对应节点的名字——
   主要是各年报里的匿名客户/供应商槽位（"客户A(匿名)"、"供应商第一名(匿名)"
   等，共 19 个）以及 1 个 nodes.csv 里确实没有收录的实体（"苏世博"，
   猎奇智能 2025 年报的一个下游客户）——本脚本会为其合成"虚拟节点"，
   不会中断渲染。虚拟节点按其在边中的角色赋予合成类型：
   作为"需方"出现 → 类型="匿名客户槽位(虚拟)"（归入终端/云层）；
   作为"供方"出现 → 类型="匿名供应商槽位(虚拟)"（归入器件/芯片层）；
   两种角色都出现或无法判断 → 类型="未披露主体(虚拟)"（归入其他层）。
   这三个合成类型本身也是通过下面第 5 条的显式 LAYER_MAP 字典路由，
   不是硬编码的特判分支。
3. 【边等级到线型的映射】SPEC 只规定了三条规则（实边=实线 / 边等级含
   "半边槽位"=灰虚线 / 边等级含"推断边"=橙点划线），但 edges.csv 实际
   出现的边等级有 6 种取值：实边、实边(已死亡)、半边、半边槽位、
   推断边(A级)、程序段落泄漏。本脚本按子串包含做归类：
     - 边等级含"半边"（覆盖"半边"和"半边槽位"两种）→ 灰虚线；
     - 边等级含"推断边" → 橙点划线；
     - 其余（含"实边(已死亡)"与"程序段落泄漏"）→ 实线（视为已获得
       某种实名证据的边；"已死亡"关系仅在 tooltip 备注里体现，不改线型，
       避免样式类目过度膨胀）。
4. 【解匿线索高亮】SPEC 规则是"备注含'解匿线索'"。当前 edges.csv 里没有
   任何一行的备注字段精确包含这四个字（有"解匿上限预期C级""判例#002"等
   近义表述，但字面不含"解匿线索"），因此该规则在当前数据上不会点亮任何
   一条边——这是数据现状，不是脚本 bug。规则实现为一次性字符串子串检查，
   对未来数据里真正写了"解匿线索:<名>"的行会正常生效（红色描边）。
5. 【节点类型 → 层的映射】SPEC 要求"写成显式 dict，未知类型落其他层"。
   nodes.csv 实际出现 29 种类型，本脚本按其在边表里的真实供需方向逐一
   人工分类到 SPEC 定义的四层（生产设备层→器件/芯片层→模块/代工层→
   终端/云层），例如："系统设备商"(华为/Infinera/Ciena/Nokia) 和
   "CATV设备商"(ATX Networks) 虽然名字带"设备商"，但在边表里是买模块的
   下游客户，归终端/云层，而不是生产设备层；"老化测试设备商"
   "耦合封装设备商"等则是真正卖设备给模块/芯片厂的上游，归生产设备层。
   "汽车电机厂""科研院所(跨行业)""锻件厂(跨行业)" 三类节点备注里明确
   标注"跨行业"/"边界外"，显式归入"其他"层。完整映射见 LAYER_MAP。
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

# ── 1. 节点类型 → 层 的显式映射（SPEC 要求：写成显式 dict，未知类型落"其他"层）──

LAYER_ORDER = ["生产设备层", "器件/芯片层", "模块/代工层", "终端/云层", "其他"]

LAYER_MAP = {
    # 生产设备层：向器件/模块/代工厂出售产线设备、或是这些设备厂自己的零部件供应商
    "老化测试设备商": "生产设备层",
    "耦合封装设备商": "生产设备层",
    "组装设备商": "生产设备层",
    "驱动控制供应商": "生产设备层",
    "加工件供应商": "生产设备层",
    "滑台类日本代理": "生产设备层",
    "神津精机代理": "生产设备层",
    # 器件/芯片层：光芯片、光器件、相干组件、CPO 芯片
    "光芯片厂": "器件/芯片层",
    "光器件厂": "器件/芯片层",
    "光器件厂(已消亡)": "器件/芯片层",
    "光器件/组件厂": "器件/芯片层",
    "相干光器件/DSP": "器件/芯片层",
    "芯片/CPO": "器件/芯片层",
    # 模块/代工层：光模块整机厂与代工/EMS
    "代工(EMS)": "模块/代工层",
    "光模块厂": "模块/代工层",
    "光模块/器件厂": "模块/代工层",
    "光器件/模块厂": "模块/代工层",
    # 终端/云层：买模块的下游——云巨头、算力/网络系统商、消费电子、
    # 分销/出口中间商、境外销售关联方
    "云巨头(终端)": "终端/云层",
    "算力终端/系统商": "终端/云层",
    "网络设备OEM": "终端/云层",
    "系统设备商": "终端/云层",
    "消费电子终端": "终端/云层",
    "CATV设备商": "终端/云层",
    "CATV分销商": "终端/云层",
    "出口代理(贸易商)": "终端/云层",
    "旭创关联方(海外销售主体待核)": "终端/云层",
    # 其他：数据里明确标注"跨行业/边界外"的样本节点
    "汽车电机厂": "其他",
    "科研院所(跨行业)": "其他",
    "锻件厂(跨行业)": "其他",
    # 虚拟节点合成类型（见 resolve_node 函数），同样经由本字典路由
    "匿名客户槽位(虚拟)": "终端/云层",
    "匿名供应商槽位(虚拟)": "器件/芯片层",
    "未披露主体(虚拟)": "其他",
}

LAYER_COLORS = {
    "生产设备层": "#64748b",
    "器件/芯片层": "#0d9488",
    "模块/代工层": "#7c3aed",
    "终端/云层": "#d97706",
    "其他": "#78716c",
}


def layer_of(node_type: str) -> str:
    return LAYER_MAP.get(node_type, "其他")


# ── 2. CSV 读取 ────────────────────────────────────────────────────────

def read_csv_dicts(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    # 去除每个字段的首尾空白，容错常见的手工编辑 CSV 问题
    cleaned = []
    for row in rows:
        cleaned.append({(k.strip() if k else k): (v.strip() if isinstance(v, str) else v)
                         for k, v in row.items()})
    return cleaned


# ── 3. 姓名归一化 + 节点解析（处理 edges.csv 与 nodes.csv 实体名对不齐问题）──

_SPLIT_SUFFIX_RE = re.compile(r"[（(+]")
_TOKEN_SPLIT_RE = re.compile(r"[/、]")


def normalize_core(name: str) -> str:
    """截断第一个 ( （ + 之后的注记后缀，返回核心名。"""
    return _SPLIT_SUFFIX_RE.split(name.strip(), maxsplit=1)[0].strip()


class NodeIndex:
    """把 nodes.csv 的名字，按精确名/归一化核心名/切分 token/ASCII 子串
    四种方式建索引，用来把 edges.csv 里写法不统一的 供方/需方 名字
    尽量指回同一个真实节点，减少重复节点。"""

    def __init__(self, node_rows: list[dict]):
        self.by_exact: dict[str, str] = {}       # 名称原文 -> node_id
        self.by_core: dict[str, str] = {}         # 归一化核心名 -> node_id
        self.ascii_names: list[tuple[str, str]] = []  # (原文名称, node_id) 供子串匹配
        self.records: dict[str, dict] = {}         # node_id -> 原始行

        for row in node_rows:
            nid = row["node_id"]
            name = row["名称"]
            self.records[nid] = row
            self.by_exact.setdefault(name, nid)
            self.by_core.setdefault(normalize_core(name), nid)
            for tok in _TOKEN_SPLIT_RE.split(name):
                tok = normalize_core(tok)
                if tok:
                    self.by_core.setdefault(tok, nid)
            self.ascii_names.append((name, nid))

    def resolve(self, raw_name: str) -> str | None:
        if raw_name in self.by_exact:
            return self.by_exact[raw_name]
        core = normalize_core(raw_name)
        if core in self.by_core:
            return self.by_core[core]
        # 纯 ASCII 缩写子串匹配（如 "AAOI" 命中 "Applied Optoelectronics(AAOI)"）
        if core.isascii() and len(core) >= 3:
            for full_name, nid in self.ascii_names:
                if core.upper() in full_name.upper():
                    return nid
        return None


def build_graph(edge_rows: list[dict], node_rows: list[dict]):
    """返回 (nodes: dict[key -> record], merged_edges: list[dict])。"""
    index = NodeIndex(node_rows)

    nodes: dict[str, dict] = {}
    for row in node_rows:
        nid = row["node_id"]
        nodes[nid] = {
            "key": nid,
            "name": row["名称"],
            "type": row["类型"],
            "country": row.get("国别", ""),
            "code": row.get("代码", ""),
            "memo": row.get("备注", ""),
            "layer": layer_of(row["类型"]),
            "virtual": False,
        }

    # 先扫一遍，判断每个未解析名字在边表里更多以 供方 还是 需方 身份出现，
    # 用于给虚拟节点分配一个合理的合成类型（进而落到合理的层）。
    unresolved_role_count: dict[str, dict[str, int]] = {}
    for row in edge_rows:
        for col, role in (("供方", "supplier"), ("需方", "demander")):
            name = row[col]
            if index.resolve(name) is None:
                unresolved_role_count.setdefault(name, {"supplier": 0, "demander": 0})
                unresolved_role_count[name][role] += 1

    virtual_key_of: dict[str, str] = {}

    def resolve_or_create(name: str) -> str:
        nid = index.resolve(name)
        if nid is not None:
            return nid
        if name in virtual_key_of:
            return virtual_key_of[name]
        roles = unresolved_role_count.get(name, {"supplier": 0, "demander": 0})
        if roles["demander"] > 0 and roles["supplier"] == 0:
            vtype = "匿名客户槽位(虚拟)"
        elif roles["supplier"] > 0 and roles["demander"] == 0:
            vtype = "匿名供应商槽位(虚拟)"
        else:
            vtype = "未披露主体(虚拟)"
        vkey = f"V{len(virtual_key_of) + 1:03d}"
        virtual_key_of[name] = vkey
        nodes[vkey] = {
            "key": vkey,
            "name": name,
            "type": vtype,
            "country": "",
            "code": "",
            "memo": "edges.csv 未在 nodes.csv 中找到对应实体，本脚本合成的虚拟节点",
            "layer": layer_of(vtype),
            "virtual": True,
        }
        return vkey

    merged: dict[tuple[str, str], dict] = {}
    for row in edge_rows:
        src = resolve_or_create(row["供方"])
        dst = resolve_or_create(row["需方"])
        key = (src, dst)
        rec = {
            "edge_id": row.get("edge_id", ""),
            "供方": row["供方"],
            "需方": row["需方"],
            "占比或金额": row.get("占比或金额", ""),
            "财年": row.get("财年", ""),
            "边等级": row.get("边等级", ""),
            "证据文件": row.get("证据文件", ""),
            "锚点": row.get("锚点", ""),
            "验证状态": row.get("验证状态", ""),
            "备注": row.get("备注", ""),
        }
        if key not in merged:
            merged[key] = {"src": src, "dst": dst, "records": []}
        merged[key]["records"].append(rec)

    edges = []
    for (src, dst), data in merged.items():
        records = data["records"]
        grades = [r["边等级"] for r in records]
        if any("半边" in g for g in grades):
            style = "half"
        elif any("推断边" in g for g in grades):
            style = "inferred"
        else:
            style = "solid"
        highlight = any("解匿线索" in (r["备注"] or "") for r in records)
        edges.append({
            "src": src,
            "dst": dst,
            "style": style,
            "highlight": highlight,
            "records": records,
        })

    return nodes, edges


# ── 4. 布局：按层分列，层内均匀纵向分布 ─────────────────────────────────

NODE_W, NODE_H = 168, 52
COL_GAP = 260
ROW_GAP = 78
MARGIN_X, MARGIN_Y = 140, 70


def compute_layout(nodes: dict[str, dict]):
    by_layer: dict[str, list[dict]] = {ly: [] for ly in LAYER_ORDER}
    for n in nodes.values():
        by_layer[n["layer"]].append(n)
    for ly in by_layer:
        by_layer[ly].sort(key=lambda n: (n["virtual"], n["name"]))

    max_rows = max((len(v) for v in by_layer.values()), default=1) or 1
    height = MARGIN_Y * 2 + max(max_rows - 1, 0) * ROW_GAP + NODE_H
    height = max(height, 480)
    width = MARGIN_X * 2 + (len(LAYER_ORDER) - 1) * COL_GAP + NODE_W

    pos: dict[str, tuple[float, float]] = {}
    for col_idx, ly in enumerate(LAYER_ORDER):
        col_nodes = by_layer[ly]
        cx = MARGIN_X + col_idx * COL_GAP
        n = len(col_nodes)
        if n == 0:
            continue
        span = max(n - 1, 0) * ROW_GAP
        start_y = (height - span) / 2
        for i, node in enumerate(col_nodes):
            cy = start_y + i * ROW_GAP
            pos[node["key"]] = (cx, cy)

    return pos, width, height, by_layer


# ── 5. SVG 渲染 ──────────────────────────────────────────────────────

def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def rect_anchor(cx, cy, hw, hh, tx, ty):
    """从矩形中心 (cx,cy) 指向目标点 (tx,ty)，返回矩形边界上的锚点。"""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale = float("inf")
    if dx != 0:
        scale = min(scale, hw / abs(dx))
    if dy != 0:
        scale = min(scale, hh / abs(dy))
    if scale == float("inf"):
        scale = 0
    return cx + dx * scale, cy + dy * scale


def edge_path(src_pos, dst_pos, bow: float) -> tuple[str, float, float]:
    (sx, sy), (dx, dy) = src_pos, dst_pos
    ax, ay = rect_anchor(sx, sy, NODE_W / 2, NODE_H / 2, dx, dy)
    bx, by = rect_anchor(dx, dy, NODE_W / 2, NODE_H / 2, sx, sy)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    # 垂直于连线方向的法向量，用来把曲线"弓"开，减少多边重叠、区分同层边
    vx, vy = bx - ax, by - ay
    length = (vx ** 2 + vy ** 2) ** 0.5 or 1.0
    nx, ny = -vy / length, vx / length
    cx, cy = mx + nx * bow, my + ny * bow
    path = f"M {ax:.1f} {ay:.1f} Q {cx:.1f} {cy:.1f} {bx:.1f} {by:.1f}"
    # tooltip/hover 高亮用的中点（曲线中点近似）
    tmx = 0.25 * ax + 0.5 * cx + 0.25 * bx
    tmy = 0.25 * ay + 0.5 * cy + 0.25 * by
    return path, tmx, tmy


STYLE_META = {
    "solid": {"stroke": "#334155", "dasharray": "none", "width": 2.2, "label": "实边（实名披露）"},
    "half": {"stroke": "#9ca3af", "dasharray": "6,5", "width": 2, "label": "半边槽位（单侧披露/匿名）"},
    "inferred": {"stroke": "#ea580c", "dasharray": "2,3,8,3", "width": 2.2, "label": "推断边（B工序判定）"},
}


def render_svg(nodes, edges, pos, width, height):
    parts = []
    parts.append(
        f'<svg id="graph-svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
    )

    # 箭头 marker（按边样式区分颜色）
    parts.append("<defs>")
    for style_key, meta in STYLE_META.items():
        parts.append(
            f'<marker id="arrow-{style_key}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{meta["stroke"]}"></path></marker>'
        )
    parts.append("</defs>")

    # 层背景带 + 层标题
    col_positions = {}
    for col_idx, ly in enumerate(LAYER_ORDER):
        col_positions[ly] = MARGIN_X + col_idx * COL_GAP
    for ly in LAYER_ORDER:
        cx = col_positions[ly]
        color = LAYER_COLORS[ly]
        parts.append(
            f'<rect x="{cx - NODE_W / 2 - 24:.1f}" y="16" width="{NODE_W + 48}" '
            f'height="{height - 32:.1f}" fill="{color}" fill-opacity="0.045" '
            f'stroke="{color}" stroke-opacity="0.18" stroke-dasharray="4,4" rx="14"></rect>'
        )
        parts.append(
            f'<text x="{cx:.1f}" y="40" text-anchor="middle" class="layer-title" '
            f'fill="{color}">{esc(ly)}</text>'
        )

    # 边（先画边，再画节点，节点盖在边上层）
    parts.append('<g id="edges-layer">')
    edge_data_for_js = {}
    node_edge_ids: dict[str, list[str]] = {k: [] for k in nodes}
    for i, e in enumerate(edges):
        eid = f"edge-{i}"
        src_pos, dst_pos = pos[e["src"]], pos[e["dst"]]
        # bow 幅度：用索引做一个稳定的小扰动，避免大量平行边完全重叠；
        # 同层（起止 x 相同）时给更大的弓形，否则曲线接近直线更易读。
        same_layer = abs(src_pos[0] - dst_pos[0]) < 1
        base_bow = 46 if same_layer else 18
        bow = base_bow * (1 if i % 2 == 0 else -1) * (1 + (i % 3) * 0.35)
        path, tmx, tmy = edge_path(src_pos, dst_pos, bow)
        meta = STYLE_META[e["style"]]
        node_edge_ids[e["src"]].append(eid)
        node_edge_ids[e["dst"]].append(eid)

        group_classes = f'edge-group edge-{e["style"]}' + (" edge-highlight" if e["highlight"] else "")
        parts.append(f'<g id="{eid}" class="{group_classes}" data-edge="{eid}">')
        if e["highlight"]:
            parts.append(
                f'<path d="{path}" class="edge-halo" fill="none" '
                f'stroke="#dc2626" stroke-width="9" stroke-opacity="0.32"></path>'
            )
        dash = "" if meta["dasharray"] == "none" else f' stroke-dasharray="{meta["dasharray"]}"'
        stroke_color = "#dc2626" if e["highlight"] else meta["stroke"]
        parts.append(
            f'<path d="{path}" class="edge-line" fill="none" stroke="{stroke_color}" '
            f'stroke-width="{meta["width"]}"{dash} marker-end="url(#arrow-{e["style"]})"></path>'
        )
        # 一条透明的宽 hitbox path，方便 hover（细线不好精确 hover 到）
        parts.append(f'<path d="{path}" class="edge-hit" fill="none" stroke="transparent" stroke-width="14"></path>')
        parts.append("</g>")

        n_years = len(e["records"])
        edge_data_for_js[eid] = {
            "src": nodes[e["src"]]["name"],
            "dst": nodes[e["dst"]]["name"],
            "style": e["style"],
            "highlight": e["highlight"],
            "n_records": n_years,
            "records": e["records"],
        }
    parts.append("</g>")

    # 节点
    parts.append('<g id="nodes-layer">')
    for key, n in nodes.items():
        x, y = pos[key]
        color = LAYER_COLORS[n["layer"]]
        cls = "node-box" + (" node-virtual" if n["virtual"] else "")
        parts.append(f'<g class="{cls}" data-node="{key}" transform="translate({x - NODE_W/2:.1f},{y - NODE_H/2:.1f})">')
        parts.append(
            f'<rect width="{NODE_W}" height="{NODE_H}" rx="9" fill="#ffffff" '
            f'stroke="{color}" stroke-width="1.6"'
            + (' stroke-dasharray="4,3"' if n["virtual"] else "")
            + '></rect>'
        )
        parts.append(f'<rect width="5" height="{NODE_H}" rx="2" fill="{color}"></rect>')
        fo_h = NODE_H
        parts.append(
            f'<foreignObject x="10" y="0" width="{NODE_W - 16}" height="{fo_h}">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="node-fo">'
            f'<div class="node-name">{esc(n["name"])}</div>'
            f'<div class="node-type">{esc(n["type"])}</div>'
            f'</div></foreignObject>'
        )
        parts.append("</g>")

        code_bits = [b for b in (n["country"], n["code"]) if b]
        node_data_for_js = {
            "name": n["name"],
            "type": n["type"],
            "layer": n["layer"],
            "country": n["country"],
            "code": n["code"],
            "memo": n["memo"],
            "virtual": n["virtual"],
            "edges": node_edge_ids[key],
        }
        n["_js"] = node_data_for_js
    parts.append("</g>")

    parts.append("</svg>")
    node_data_for_js_all = {k: n["_js"] for k, n in nodes.items()}
    return "".join(parts), edge_data_for_js, node_data_for_js_all


# ── 6. HTML 组装（内联全部 CSS/JS，零外链） ─────────────────────────────

PAGE_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>光模块产业结构图谱</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --fg: #1e293b;
    --bg: #f8fafc;
    --panel: #ffffff;
    --border: #e2e8f0;
    --muted: #64748b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei",
      "Noto Sans CJK SC", "Hiragino Sans GB", "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--fg);
  }}
  header {{
    padding: 18px 24px 14px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
  }}
  header h1 {{
    margin: 0 0 4px;
    font-size: 19px;
    font-weight: 700;
  }}
  header .sub {{
    font-size: 12.5px;
    color: var(--muted);
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px 28px;
    padding: 10px 24px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    font-size: 12.5px;
    color: var(--fg);
  }}
  .legend-item {{ display: flex; align-items: center; gap: 7px; white-space: nowrap; }}
  .legend-swatch {{ width: 26px; height: 0; border-top-width: 3px; border-top-style: solid; }}
  .legend-dot {{ width: 11px; height: 11px; border-radius: 3px; display: inline-block; }}
  #graph-wrap {{
    overflow: auto;
    padding: 18px;
  }}
  .layer-title {{ font-size: 13px; font-weight: 700; letter-spacing: 0.5px; }}
  .node-box {{ cursor: pointer; }}
  .node-fo {{
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    line-height: 1.28;
    overflow: hidden;
  }}
  .node-name {{
    font-size: 12.5px;
    font-weight: 700;
    color: #0f172a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .node-type {{
    font-size: 10.5px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
  }}
  .edge-line, .edge-halo {{ transition: stroke-width 0.12s ease, stroke-opacity 0.12s ease; }}
  .edge-hit {{ cursor: pointer; }}
  .edge-group {{ opacity: 1; }}
  #graph-svg.dimmed .edge-group:not(.active) {{ opacity: 0.12; }}
  #graph-svg.dimmed .node-box:not(.active) {{ opacity: 0.28; }}
  .edge-group.active .edge-line {{ stroke-width: 4; }}
  .node-box.active rect:first-of-type {{ stroke-width: 3; }}
  #tooltip {{
    position: fixed;
    display: none;
    max-width: 420px;
    background: #0f172a;
    color: #f1f5f9;
    padding: 10px 13px;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.55;
    pointer-events: none;
    z-index: 50;
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
  }}
  #tooltip b {{ color: #93c5fd; }}
  #tooltip .rec {{ padding: 5px 0; border-top: 1px solid rgba(255,255,255,0.12); }}
  #tooltip .rec:first-child {{ border-top: none; }}
  #tooltip .hl {{ color: #fca5a5; font-weight: 700; }}
  #tooltip .title {{ font-weight: 700; margin-bottom: 4px; font-size: 12.5px; }}
  footer {{
    padding: 10px 24px 22px;
    font-size: 11px;
    color: var(--muted);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg:#e2e8f0; --bg:#0f172a; --panel:#1e293b; --border:#334155; --muted:#94a3b8; }}
    .node-name {{ color: #f1f5f9; }}
    .node-box rect:first-of-type {{ fill: #1e293b !important; }}
  }}
</style>
</head>
<body>
<header>
  <h1>光模块产业结构图谱（Stage4 demo 可视化）</h1>
  <div class="sub">节点 {n_nodes} 个（含虚拟节点 {n_virtual} 个）· 合并后边 {n_edges} 条（来自 edges.csv {n_raw_edges} 行记录）· 分层布局：生产设备层 → 器件/芯片层 → 模块/代工层 → 终端/云层 → 其他</div>
</header>
<div class="legend">
  <div class="legend-item"><span class="legend-swatch" style="border-color:#334155;"></span>实边（实名披露）</div>
  <div class="legend-item"><span class="legend-swatch" style="border-color:#9ca3af; border-top-style:dashed;"></span>半边槽位（单侧披露/匿名）</div>
  <div class="legend-item"><span class="legend-swatch" style="border-color:#ea580c; border-top-style:dashed;"></span>推断边（B工序判定）</div>
  <div class="legend-item"><span class="legend-swatch" style="border-color:#dc2626; border-top-width:5px;"></span>备注含"解匿线索"（红色高亮描边）</div>
  {layer_legend}
</div>
<div id="graph-wrap">
{svg}
</div>
<div id="tooltip"></div>
<footer>自包含 HTML，零外链零 CDN；hover 边查看四件套，hover 节点高亮其相连边。生成脚本：demo/src/make_graph.py</footer>
<script>
const EDGE_DATA = {edge_json};
const NODE_DATA = {node_json};

const svg = document.getElementById('graph-svg');
const tooltip = document.getElementById('tooltip');

function escapeHtml(s) {{
  return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {{
    return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c];
  }});
}}

function edgeTooltipHtml(d) {{
  let html = '<div class="title">' + escapeHtml(d.src) + ' → ' + escapeHtml(d.dst) +
    (d.highlight ? ' <span class="hl">[解匿线索]</span>' : '') + '</div>';
  d.records.forEach(function(r) {{
    html += '<div class="rec">' +
      '<div><b>财年</b> ' + escapeHtml(r['财年']) + ' · <b>占比/金额</b> ' + escapeHtml(r['占比或金额']) +
      ' · <b>边等级</b> ' + escapeHtml(r['边等级']) + '</div>' +
      '<div><b>证据文件</b> ' + escapeHtml(r['证据文件']) + '</div>' +
      '<div><b>锚点</b> ' + escapeHtml(r['锚点']) + '</div>' +
      (r['验证状态'] ? '<div><b>验证状态</b> ' + escapeHtml(r['验证状态']) + '</div>' : '') +
      (r['备注'] ? '<div><b>备注</b> ' + escapeHtml(r['备注']) + '</div>' : '') +
      '</div>';
  }});
  return html;
}}

function nodeTooltipHtml(d) {{
  let html = '<div class="title">' + escapeHtml(d.name) + '</div>';
  html += '<div>类型：' + escapeHtml(d.type) + ' · 层：' + escapeHtml(d.layer) + '</div>';
  if (d.country) html += '<div>国别：' + escapeHtml(d.country) + '</div>';
  if (d.code) html += '<div>代码：' + escapeHtml(d.code) + '</div>';
  if (d.memo) html += '<div>备注：' + escapeHtml(d.memo) + '</div>';
  html += '<div>相连边：' + d.edges.length + ' 条</div>';
  return html;
}}

function showTooltip(html, evt) {{
  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  moveTooltip(evt);
}}
function moveTooltip(evt) {{
  const pad = 16;
  let x = evt.clientX + pad;
  let y = evt.clientY + pad;
  const vw = window.innerWidth, vh = window.innerHeight;
  tooltip.style.left = '0px'; tooltip.style.top = '0px';
  const rect = tooltip.getBoundingClientRect();
  if (x + rect.width > vw - 8) x = evt.clientX - rect.width - pad;
  if (y + rect.height > vh - 8) y = evt.clientY - rect.height - pad;
  tooltip.style.left = Math.max(4, x) + 'px';
  tooltip.style.top = Math.max(4, y) + 'px';
}}
function hideTooltip() {{ tooltip.style.display = 'none'; }}

svg.querySelectorAll('.edge-group').forEach(function(g) {{
  const id = g.getAttribute('data-edge');
  const d = EDGE_DATA[id];
  g.addEventListener('mouseenter', function(evt) {{ showTooltip(edgeTooltipHtml(d), evt); }});
  g.addEventListener('mousemove', moveTooltip);
  g.addEventListener('mouseleave', hideTooltip);
}});

svg.querySelectorAll('.node-box').forEach(function(g) {{
  const key = g.getAttribute('data-node');
  const d = NODE_DATA[key];
  g.addEventListener('mouseenter', function(evt) {{
    showTooltip(nodeTooltipHtml(d), evt);
    svg.classList.add('dimmed');
    g.classList.add('active');
    d.edges.forEach(function(eid) {{
      const el = document.getElementById(eid);
      if (el) el.classList.add('active');
    }});
  }});
  g.addEventListener('mousemove', moveTooltip);
  g.addEventListener('mouseleave', function() {{
    hideTooltip();
    svg.classList.remove('dimmed');
    g.classList.remove('active');
    d.edges.forEach(function(eid) {{
      const el = document.getElementById(eid);
      if (el) el.classList.remove('active');
    }});
  }});
}});
</script>
</body>
</html>
"""


def build_html(nodes, edges, pos, width, height, n_raw_edges) -> str:
    svg, edge_js, node_js = render_svg(nodes, edges, pos, width, height)
    n_virtual = sum(1 for n in nodes.values() if n["virtual"])
    layer_legend = "".join(
        f'<div class="legend-item"><span class="legend-dot" style="background:{LAYER_COLORS[ly]};"></span>{esc(ly)}</div>'
        for ly in LAYER_ORDER
    )
    return PAGE_TEMPLATE.format(
        svg=svg,
        edge_json=json.dumps(edge_js, ensure_ascii=False),
        node_json=json.dumps(node_js, ensure_ascii=False),
        n_nodes=len(nodes),
        n_virtual=n_virtual,
        n_edges=len(edges),
        n_raw_edges=n_raw_edges,
        layer_legend=layer_legend,
    )


# ── 7. CLI ───────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage4: edges.csv/nodes.csv → 自包含 graph.html")
    parser.add_argument("--edges", required=True, type=Path)
    parser.add_argument("--nodes", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    edge_rows = read_csv_dicts(args.edges)
    node_rows = read_csv_dicts(args.nodes)
    if not edge_rows:
        print(f"警告：{args.edges} 没有读到任何边记录", file=sys.stderr)
    if not node_rows:
        print(f"警告：{args.nodes} 没有读到任何节点记录", file=sys.stderr)

    nodes, edges = build_graph(edge_rows, node_rows)
    pos, width, height, _by_layer = compute_layout(nodes)
    out_html = build_html(nodes, edges, pos, width, height, n_raw_edges=len(edge_rows))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_html, encoding="utf-8")
    print(f"写出 {args.out}（节点 {len(nodes)}，合并后边 {len(edges)}，原始边行 {len(edge_rows)}）")


if __name__ == "__main__":
    main()
