#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the self-contained v1.3 optical-module industry atlas.

Inputs are read-only:
  output/nodes.csv
  output/edges.csv
  flows/out/customs-monthly.csv
  flows/out/customs-partners.csv
  flows/out/customs-trademode.csv  (optional X1 delivery)

Output:
  output/光模块产业图谱-v1.3.html
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NODES_CSV = ROOT / "output" / "nodes.csv"
EDGES_CSV = ROOT / "output" / "edges.csv"
MONTHLY_CSV = ROOT / "flows" / "out" / "customs-monthly.csv"
PARTNERS_CSV = ROOT / "flows" / "out" / "customs-partners.csv"
TRADEMODE_CSV = ROOT / "flows" / "out" / "customs-trademode.csv"
OUT_HTML = ROOT / "output" / "光模块产业图谱-v1.3.html"

EXPECTED_MONTHS = [
    f"{year}{month:02d}"
    for year, months in ((2024, range(1, 13)), (2025, range(1, 13)), (2026, range(1, 7)))
    for month in months
]
TURNING_MONTH = "202504"
DIM_DESTINATIONS = ("马来西亚", "美国", "泰国")

LAYER_ORDER = ("生产设备层", "器件/芯片层", "模块/代工层", "终端/云层", "其他")
TYPE_TO_LAYER = {
    "老化测试设备商": "生产设备层",
    "耦合封装设备商": "生产设备层",
    "组装设备商": "生产设备层",
    "组件封装设备商": "生产设备层",
    "自动化设备商": "生产设备层",
    "焊接设备商": "生产设备层",
    "测试测量仪器": "生产设备层",
    "驱动控制供应商": "生产设备层",
    "加工件供应商": "生产设备层",
    "滑台类日本代理": "生产设备层",
    "神津精机代理": "生产设备层",
    "光芯片厂": "器件/芯片层",
    "光器件厂": "器件/芯片层",
    "光器件厂(已消亡)": "器件/芯片层",
    "光器件/组件厂": "器件/芯片层",
    "相干光器件/DSP": "器件/芯片层",
    "芯片/CPO": "器件/芯片层",
    "光模块厂": "模块/代工层",
    "光模块/器件厂": "模块/代工层",
    "光器件/模块厂": "模块/代工层",
    "代工(EMS)": "模块/代工层",
    "云巨头(终端)": "终端/云层",
    "算力终端/系统商": "终端/云层",
    "网络设备OEM": "终端/云层",
    "系统设备商": "终端/云层",
    "消费电子终端": "终端/云层",
    "CATV设备商": "终端/云层",
    "CATV分销商": "终端/云层",
    "出口代理(贸易商)": "终端/云层",
    "旭创关联方(海外销售主体待核)": "终端/云层",
}

ALIASES = {
    "华为+海思": "华为(含海思)",
    "华为": "华为(含海思)",
    "ficonTEC(罗博特科)": "罗博特科/ficonTEC",
    "罗博特科": "罗博特科/ficonTEC",
    "索恩格": "索恩格(SEG Automotive)",
    "博通(客户)": "博通(Broadcom)",
    "NVIDIA(客户)": "NVIDIA",
    "等离子体所(客户)": "等离子体所",
    "PINEWAVE(关联方)": "PINEWAVE",
    "中际旭创(作为客户)": "中际旭创",
    "Fabrinet(疑似客户)": "Fabrinet",
    "Fabrinet(解匿)": "Fabrinet",
    "Ciena(解匿)": "Ciena",
    "Google(解匿)": "Google",
    "浙江粮油(出口代理)": "浙江粮油",
    "AAOI": "Applied Optoelectronics(AAOI)",
}

GRADE_CLASS = {
    "实边": "solid",
    "半边": "half",
    "半边槽位": "half",
    "推断边(A级)": "inferred",
    "程序段落泄漏": "leak",
    "实边(已死亡)": "dead",
}

LAYER_X = {
    "生产设备层": 42,
    "器件/芯片层": 366,
    "模块/代工层": 690,
    "终端/云层": 1014,
    "其他": 1338,
}
LAYER_FILL = {
    "生产设备层": "#eaf0f5",
    "器件/芯片层": "#e3f3ef",
    "模块/代工层": "#eee8f7",
    "终端/云层": "#f8eddf",
    "其他": "#f1efec",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            (key.strip() if key else ""): (value.strip() if isinstance(value, str) else value)
            for key, value in row.items()
        }
        for row in rows
    ]


def number(value: str) -> float:
    text = (value or "").strip().replace(",", "")
    return float(text) if text else 0.0


def js_data(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def build_relationship_model(
    node_rows: list[dict[str, str]], edge_rows: list[dict[str, str]]
) -> tuple[list[dict], list[dict], int, int]:
    """Resolve aliases, create honest anonymous slots, and add missing real entities."""
    nodes: dict[str, dict] = {}
    by_name: dict[str, str] = {}
    for row in node_rows:
        key = f"N_{row['node_id']}"
        item = {
            "key": key,
            "name": row["名称"],
            "type": row["类型"],
            "country": row.get("国别", ""),
            "code": row.get("代码", ""),
            "memo": row.get("备注", ""),
            "layer": TYPE_TO_LAYER.get(row["类型"], "其他"),
            "slot": False,
            "virtual": False,
        }
        nodes[key] = item
        by_name[item["name"]] = key

    slot_keys: dict[tuple[str, str], str] = {}
    virtual_keys: dict[str, str] = {}

    def resolve(raw_name: str, peer_name: str) -> str:
        normalized = ALIASES.get(raw_name, raw_name)
        if normalized in by_name:
            return by_name[normalized]
        if "匿名" in raw_name:
            identity = (ALIASES.get(peer_name, peer_name), raw_name)
            if identity not in slot_keys:
                key = f"S_{len(slot_keys) + 1:02d}"
                slot_keys[identity] = key
                supply_slot = raw_name.startswith("供应商")
                nodes[key] = {
                    "key": key,
                    "name": raw_name,
                    "type": "匿名槽位",
                    "country": "",
                    "code": "",
                    "memo": f"{identity[0]}披露的匿名槽位；公开披露未给实名，不猜测",
                    "layer": "器件/芯片层" if supply_slot else "终端/云层",
                    "slot": True,
                    "virtual": False,
                }
            return slot_keys[identity]
        if normalized not in virtual_keys:
            key = f"V_{len(virtual_keys) + 1:02d}"
            virtual_keys[normalized] = key
            is_sushibo = normalized == "苏世博"
            nodes[key] = {
                "key": key,
                "name": normalized,
                "type": "自动化设备客户（补虚节点）" if is_sushibo else "未收录实体",
                "country": "",
                "code": "",
                "memo": (
                    "由 E050 实边补建虚节点；原 nodes.csv 未收录"
                    if is_sushibo
                    else "edges.csv 存在而 nodes.csv 未收录；如实补建虚节点"
                ),
                "layer": "终端/云层" if is_sushibo else "其他",
                "slot": False,
                "virtual": True,
            }
        return virtual_keys[normalized]

    edges: list[dict] = []
    pair_seen: Counter[tuple[str, str]] = Counter()
    for row in edge_rows:
        source = resolve(row["供方"], row["需方"])
        target = resolve(row["需方"], row["供方"])
        pair = (source, target)
        parallel_index = pair_seen[pair]
        pair_seen[pair] += 1
        grade = row["边等级"]
        edges.append(
            {
                "id": row["edge_id"],
                "source": source,
                "target": target,
                "sourceName": nodes[source]["name"],
                "targetName": nodes[target]["name"],
                "grade": grade,
                "style": GRADE_CLASS.get(grade, "half"),
                "amount": row.get("占比或金额", ""),
                "year": row.get("财年", ""),
                "evidence": row.get("证据文件", ""),
                "anchor": row.get("锚点", ""),
                "status": row.get("验证状态", ""),
                "memo": row.get("备注", ""),
                "parallel": parallel_index,
            }
        )

    return list(nodes.values()), edges, len(slot_keys), len(virtual_keys)


def relationship_layout(nodes: list[dict]) -> tuple[dict[str, tuple[float, float]], int, int, dict]:
    grouped = {layer: [] for layer in LAYER_ORDER}
    for node in nodes:
        grouped[node["layer"]].append(node)
    for layer in grouped:
        grouped[layer].sort(key=lambda item: (item["slot"], item["name"]))

    node_w, node_h, row_gap = 246, 44, 58
    max_count = max(len(grouped[layer]) for layer in LAYER_ORDER)
    height = max(760, 82 + max_count * row_gap + 58)
    positions: dict[str, tuple[float, float]] = {}
    boxes: dict[str, dict] = {}
    for layer in LAYER_ORDER:
        items = grouped[layer]
        x = LAYER_X[layer]
        used = max(1, len(items)) * row_gap
        top = 72 + (height - 120 - used) / 2
        boxes[layer] = {
            "x": x - 18,
            "y": max(14, top - 44),
            "w": node_w + 36,
            "h": min(height - 28, used + 62),
        }
        for index, node in enumerate(items):
            positions[node["key"]] = (x + node_w / 2, top + index * row_gap + node_h / 2)
    return positions, 1630, height, boxes


def relationship_svg(nodes: list[dict], edges: list[dict]) -> str:
    positions, width, height, boxes = relationship_layout(nodes)
    node_w, node_h = 246, 44
    node_by_key = {node["key"]: node for node in nodes}
    parts = [
        f'<svg id="relationship-svg" class="atlas-svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="rel-svg-title rel-svg-desc" xmlns="http://www.w3.org/2000/svg">',
        '<title id="rel-svg-title">光模块产业供需关系图</title>',
        '<desc id="rel-svg-desc">五列供应链层级，展示81条证据边及匿名槽位。</desc>',
        "<defs>",
    ]
    marker_colors = {
        "solid": "#263746",
        "half": "#8b96a0",
        "inferred": "#d56a2a",
        "leak": "#7253a6",
        "dead": "#a7adb3",
    }
    for style, color in marker_colors.items():
        parts.append(
            f'<marker id="arrow-{style}" viewBox="0 0 10 10" refX="8.2" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{color}"/></marker>'
        )
    parts.append("</defs>")

    for layer in LAYER_ORDER:
        box = boxes[layer]
        parts.append(
            f'<rect class="layer-box" x="{box["x"]:.1f}" y="{box["y"]:.1f}" '
            f'width="{box["w"]:.1f}" height="{box["h"]:.1f}" rx="18" fill="{LAYER_FILL[layer]}"/>'
        )
        parts.append(
            f'<text class="layer-title" x="{box["x"] + box["w"] / 2:.1f}" '
            f'y="{box["y"] + 28:.1f}" text-anchor="middle">{esc(layer)}</text>'
        )

    def border_point(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        if not dx and not dy:
            return ax, ay
        ratio = min(
            (node_w / 2) / abs(dx) if dx else float("inf"),
            (node_h / 2) / abs(dy) if dy else float("inf"),
        )
        return ax + dx * ratio, ay + dy * ratio

    for edge in edges:
        source = positions[edge["source"]]
        target = positions[edge["target"]]
        x1, y1 = border_point(source, target)
        x2, y2 = border_point(target, source)
        if abs(x2 - x1) < 40:
            bend = 74 + edge["parallel"] * 12
            path = (
                f"M{x1:.1f},{y1:.1f} C{x1 - bend:.1f},{y1:.1f} "
                f"{x2 - bend:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
            )
        else:
            midpoint = (x1 + x2) / 2 + edge["parallel"] * 7
            path = (
                f"M{x1:.1f},{y1:.1f} C{midpoint:.1f},{y1:.1f} "
                f"{midpoint:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
            )
        parts.append(
            f'<g class="rel-edge {edge["style"]}" data-edge-id="{esc(edge["id"])}" role="button" tabindex="0" '
            f'aria-label="关系 {esc(edge["id"])}：{esc(edge["sourceName"])} 到 {esc(edge["targetName"])}，{esc(edge["grade"])}">'
            f'<path class="edge-hit" d="{path}"/><path class="edge-line" d="{path}" '
            f'marker-end="url(#arrow-{edge["style"]})"/></g>'
        )

    for node in nodes:
        cx, cy = positions[node["key"]]
        x, y = cx - node_w / 2, cy - node_h / 2
        flags = (" slot" if node["slot"] else "") + (" virtual" if node["virtual"] else "")
        country = node["country"] or ("匿名" if node["slot"] else "待补")
        parts.append(
            f'<g class="rel-node{flags}" data-node-key="{esc(node["key"])}" role="button" tabindex="0" '
            f'aria-label="节点 {esc(node["name"])}">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{node_w}" height="{node_h}" rx="9"/>'
            f'<circle cx="{x + 14:.1f}" cy="{cy:.1f}" r="4.2"/>'
            f'<text class="node-name" x="{x + 26:.1f}" y="{cy - 2:.1f}">{esc(node["name"])}</text>'
            f'<text class="node-meta" x="{x + 26:.1f}" y="{cy + 13:.1f}">{esc(node["type"])} · {esc(country)}</text>'
            "</g>"
        )
    parts.append("</svg>")
    return "".join(parts)


def build_flow_model(
    monthly_rows: list[dict[str, str]], partner_rows: list[dict[str, str]]
) -> dict:
    monthly_by_key = {row["月份"]: row for row in monthly_rows}
    partner_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in partner_rows:
        partner_groups[row["月份"]].append(row)

    months: list[dict] = []
    for month in EXPECTED_MONTHS:
        row = monthly_by_key.get(month)
        if row is None:
            raise ValueError(f"customs-monthly.csv 缺月份 {month}")
        total = number(row["金额"])
        total_kg = number(row["出口量kg"])
        partners = partner_groups.get(month, [])
        ranked = sorted(partners, key=lambda item: number(item["金额"]), reverse=True)
        top = ranked[:10]
        remainder = ranked[10:]
        flows = [
            {
                "name": item["贸易伙伴"],
                "amount": number(item["金额"]),
                "kg": number(item["出口量kg"]),
            }
            for item in top
        ]
        if partners:
            flows.append(
                {
                    "name": "其他",
                    "amount": sum(number(item["金额"]) for item in remainder),
                    "kg": sum(number(item["出口量kg"]) for item in remainder),
                    "count": len(remainder),
                }
            )
        partner_sum = sum(number(item["金额"]) for item in partners)
        for flow in flows:
            flow["share"] = flow["amount"] / partner_sum if partner_sum else 0
        months.append(
            {
                "month": month,
                "label": f"{month[:4]}-{month[4:]}",
                "total": total,
                "kg": total_kg,
                "currency": row.get("币种", "USD"),
                "partners": flows,
                "partnerCount": len(partners),
                "partnerSum": partner_sum,
                "hasPartners": bool(partners),
                "turning": month == TURNING_MONTH,
            }
        )
    return {"months": months, "turningMonth": TURNING_MONTH}


def build_dimension_model() -> dict:
    if not TRADEMODE_CSV.exists():
        return {
            "status": "pending",
            "message": "数据待X1交付",
            "rows": [],
            "months": [],
            "modes": [],
            "destinations": list(DIM_DESTINATIONS),
        }

    rows = read_csv(TRADEMODE_CSV)
    required = {"月份", "贸易伙伴", "贸易方式", "出口量kg", "金额USD"}
    actual = set(rows[0]) if rows else set()
    if not rows or not required.issubset(actual):
        missing = sorted(required - actual)
        return {
            "status": "invalid",
            "message": f"X1数据字段不完整：{','.join(missing) if missing else '空文件'}",
            "rows": [],
            "months": [],
            "modes": [],
            "destinations": list(DIM_DESTINATIONS),
        }

    aggregated: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: {"amount": 0.0, "kg": 0.0}
    )
    for row in rows:
        destination = row["贸易伙伴"]
        if destination not in DIM_DESTINATIONS:
            continue
        key = (row["月份"], destination, row["贸易方式"])
        aggregated[key]["amount"] += number(row["金额USD"])
        aggregated[key]["kg"] += number(row["出口量kg"])
    output_rows = [
        {
            "month": month,
            "destination": destination,
            "mode": mode,
            "amount": values["amount"],
            "kg": values["kg"],
        }
        for (month, destination, mode), values in sorted(aggregated.items())
    ]
    return {
        "status": "ready",
        "message": "",
        "rows": output_rows,
        "months": sorted({row["month"] for row in output_rows}),
        "modes": sorted({row["mode"] for row in output_rows}),
        "destinations": list(DIM_DESTINATIONS),
        "sourceRows": len(rows),
    }


HTML_SHELL = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>光模块产业图谱 v1.3</title>
<style>
:root{
  --ink:#17222c;--muted:#60707d;--paper:#f7f4ee;--panel:#fffdf9;--line:#d9d5cd;
  --navy:#203a4e;--teal:#168174;--amber:#c77b28;--violet:#7253a6;--red:#a54b45;
  --blue:#4e7192;--soft:#ebe7de;--shadow:0 10px 34px rgba(38,47,55,.09);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif}
button,input{font:inherit}
button:focus-visible,input:focus-visible{outline:3px solid rgba(22,129,116,.35);outline-offset:2px}
.shell{max-width:1600px;margin:0 auto;padding:24px}
.masthead{display:flex;gap:22px;align-items:flex-end;justify-content:space-between;margin-bottom:18px}
.eyebrow{color:var(--teal);font-size:12px;letter-spacing:.16em;font-weight:700}
h1{font-family:Georgia,"Songti SC",serif;font-size:clamp(28px,4vw,50px);line-height:1.02;margin:6px 0 8px;font-weight:600}
.subtitle{color:var(--muted);font-size:14px}
.version{font-family:ui-monospace,monospace;border:1px solid var(--line);border-radius:999px;padding:8px 12px;background:var(--panel);white-space:nowrap}
.tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:7px;background:#e9e4da;border-radius:16px;position:sticky;top:8px;z-index:10;box-shadow:var(--shadow)}
.tab{border:0;background:transparent;color:var(--muted);border-radius:11px;padding:12px 16px;cursor:pointer;font-weight:700}
.tab[aria-selected="true"]{background:var(--panel);color:var(--ink);box-shadow:0 2px 10px rgba(38,47,55,.08)}
.layer{display:none;margin-top:18px}.layer.active{display:block}
.topline{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:12px}
.topline h2{font-family:Georgia,"Songti SC",serif;margin:0;font-size:24px}
.metrics{display:flex;gap:8px;flex-wrap:wrap}
.metric{padding:7px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel);font-size:12px;color:var(--muted)}
.metric b{color:var(--ink)}
.notice{border-left:4px solid var(--amber);background:#fbf0df;padding:12px 14px;margin:12px 0;color:#6e4a22;font-size:13px}
.stage{background:var(--panel);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);overflow:hidden}
.atlas-svg{display:block;width:100%;height:auto;min-width:980px}
.relation-scroll{overflow:auto}
.layer-box{stroke:#d4cfc5;stroke-width:1}
.layer-title{font-size:13px;font-weight:700;fill:#485661;letter-spacing:.08em}
.rel-node{cursor:pointer}.rel-node rect{fill:#fffdfa;stroke:#aeb7bd;stroke-width:1.2}
.rel-node circle{fill:var(--blue)}.rel-node.slot rect{stroke:#949ca3;stroke-dasharray:5 4;fill:#f4f2ed}
.rel-node.slot circle{fill:#969da2}.rel-node.virtual rect{stroke:var(--amber);stroke-dasharray:2 3}
.rel-node.virtual circle{fill:var(--amber)}.rel-node:hover rect,.rel-node:focus rect,.rel-node.selected rect{stroke:var(--teal);stroke-width:2.5}
.node-name{font-size:11.5px;font-weight:700;fill:var(--ink)}.node-meta{font-size:8.8px;fill:#73818b}
.rel-edge{cursor:pointer;opacity:.7}.rel-edge:hover,.rel-edge:focus,.rel-edge.selected{opacity:1}
.edge-hit{fill:none;stroke:transparent;stroke-width:13}.edge-line{fill:none;stroke-width:2}
.rel-edge.solid .edge-line{stroke:#263746}.rel-edge.half .edge-line{stroke:#8b96a0;stroke-dasharray:7 5}
.rel-edge.inferred .edge-line{stroke:#d56a2a;stroke-width:2.4;stroke-dasharray:11 4 2 4}
.rel-edge.leak .edge-line{stroke:#7253a6;stroke-width:2.4;stroke-dasharray:13 5}
.rel-edge.dead .edge-line{stroke:#a7adb3;stroke-width:1.7;stroke-dasharray:2 5}
.detail{margin-top:12px;padding:16px;background:var(--panel);border:1px solid var(--line);border-radius:14px;min-height:78px}
.detail h3{margin:0 0 8px;font-size:16px}.detail-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px 18px;font-size:12px}
.detail-grid div{min-width:0}.detail-grid span{display:block;color:var(--muted);font-size:10px;margin-bottom:2px}
.detail-grid .wide{grid-column:1/-1;overflow-wrap:anywhere}
.flow-layout{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(310px,.75fr);gap:14px}
.chart-panel,.partner-panel,.dim-panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:var(--shadow)}
.control-row{display:grid;grid-template-columns:140px minmax(220px,1fr);gap:16px;align-items:center;margin:10px 0 4px}
.month-readout{font-family:ui-monospace,monospace;font-size:22px;font-weight:700}
.range-wrap{position:relative;padding-top:22px}
.turn-label{position:absolute;left:51.72%;top:0;transform:translateX(-50%);font-size:10px;color:var(--amber);white-space:nowrap}
input[type="range"]{width:100%;accent-color:var(--teal)}
.range-ends{display:flex;justify-content:space-between;color:var(--muted);font:11px ui-monospace,monospace}
.flow-svg{display:block;width:100%;height:auto;margin-top:10px}
.gridline{stroke:#e7e3db;stroke-width:1}.axis-label{fill:#72808a;font-size:10px}.total-line{fill:none;stroke:var(--navy);stroke-width:3}
.total-area{fill:rgba(32,58,78,.08)}.total-dot{fill:var(--panel);stroke:var(--navy);stroke-width:2;cursor:pointer}
.total-dot.active{fill:var(--teal);stroke:var(--teal);r:5}.turn-line{stroke:var(--amber);stroke-width:2;stroke-dasharray:4 4}
.turn-text{fill:#9a5d1f;font-size:10px;font-weight:700}.chart-title{font-size:13px;font-weight:700;fill:var(--ink)}
.partner-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.partner-head h3{margin:0;font-size:18px}
.partner-total{font-size:12px;color:var(--muted);margin:5px 0 14px}.bars{display:grid;gap:7px}
.bar-row{display:grid;grid-template-columns:76px minmax(80px,1fr) 82px;gap:8px;align-items:center;font-size:11px}
.bar-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:10px;background:#ece8e0;border-radius:999px;overflow:hidden}
.bar-fill{height:100%;background:var(--blue);border-radius:999px}.bar-row[data-name="马来西亚"] .bar-fill{background:var(--teal)}
.bar-row[data-name="美国"] .bar-fill{background:var(--red)}.bar-row[data-name="泰国"] .bar-fill{background:#4d88a8}
.bar-row[data-name="其他"] .bar-fill{background:#a9afb3}.bar-value{text-align:right;font-variant-numeric:tabular-nums}
.empty{display:grid;place-items:center;min-height:330px;text-align:center;color:var(--muted);padding:24px}
.empty b{color:var(--ink);font-size:16px}
.special{display:inline-block;margin-left:6px;padding:3px 6px;background:#f5dfbf;color:#7b4c19;border-radius:5px;font-size:10px}
.dim-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.dim-panel h3{margin:0 0 4px}.dim-sub{font-size:11px;color:var(--muted);margin-bottom:8px}
.dim-svg{display:block;width:100%;height:auto}.dim-placeholder{display:grid;place-items:center;min-height:480px;text-align:center}
.waiting-mark{width:72px;height:72px;border-radius:50%;border:1px dashed var(--amber);display:grid;place-items:center;margin:0 auto 16px;color:var(--amber);font-size:24px}
.dim-placeholder h3{font-size:24px;margin:0 0 8px}.dim-placeholder p{color:var(--muted);max-width:520px}
.legend{display:flex;gap:12px 18px;flex-wrap:wrap;align-items:center;margin-top:14px;padding:14px;border-top:1px solid var(--line);font-size:11px;color:var(--muted)}
.legend strong{color:var(--ink)}.legend-item{display:inline-flex;gap:6px;align-items:center}
.swatch{width:28px;height:3px;background:#263746}.swatch.half{background:repeating-linear-gradient(90deg,#8b96a0 0 7px,transparent 7px 12px)}
.swatch.inferred{background:#d56a2a}.swatch.leak{background:#7253a6}.swatch.dead{background:#a7adb3;height:2px}
.legend-warning{flex:1 1 100%;color:#7a4d1e;background:#fbf0df;padding:9px 10px}
.footer{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:10px;margin:16px 2px 2px}
.tooltip{position:fixed;display:none;pointer-events:none;z-index:50;max-width:300px;padding:9px 11px;border-radius:9px;background:#17222c;color:#fff;font-size:11px;box-shadow:var(--shadow)}
@media(max-width:900px){
  .shell{padding:14px}.masthead{align-items:flex-start}.flow-layout,.dim-grid{grid-template-columns:1fr}
  .detail-grid{grid-template-columns:1fr 1fr}.tabs{position:static}.dim-placeholder{min-height:340px}
}
@media(max-width:560px){
  .masthead{display:block}.version{display:inline-block;margin-top:10px}.tab{padding:10px 6px;font-size:12px}
  .control-row{grid-template-columns:1fr}.detail-grid{grid-template-columns:1fr}.bar-row{grid-template-columns:68px 1fr 70px}
}
</style>
</head>
<body>
<main class="shell">
  <header class="masthead">
    <div>
      <div class="eyebrow">EVIDENCE ATLAS · HS 85177950</div>
      <h1>光模块产业图谱</h1>
      <div class="subtitle">供需证据、出口流向与贸易方式的三层观察 · 数据截至 2026-06</div>
    </div>
    <div class="version">v1.3 · 2026-07-23</div>
  </header>

  <nav class="tabs" role="tablist" aria-label="图谱层级">
    <button class="tab" id="tab-rel" role="tab" aria-selected="true" aria-controls="layer-rel" data-layer="rel">① 关系层</button>
    <button class="tab" id="tab-flow" role="tab" aria-selected="false" aria-controls="layer-flow" data-layer="flow">② 流向层</button>
    <button class="tab" id="tab-dim" role="tab" aria-selected="false" aria-controls="layer-dim" data-layer="dim">③ 维度层</button>
  </nav>

  <section class="layer active" id="layer-rel" role="tabpanel" aria-labelledby="tab-rel">
    <div class="topline">
      <h2>谁在给谁供货</h2>
      <div class="metrics">
        <span class="metric"><b id="rel-node-count"></b> 节点（含槽位/补虚）</span>
        <span class="metric"><b id="rel-edge-count"></b> 条披露记录</span>
        <span class="metric">点击节点或边查看证据</span>
      </div>
    </div>
    <div class="notice">图中箭头是“供方 → 需方”。匿名槽位保留匿名，E014 半边纳入；苏世博由 E050 实边补建虚节点。</div>
    <div class="stage relation-scroll">__RELATIONSHIP_SVG__</div>
    <div class="detail" id="rel-detail" aria-live="polite">
      <h3>证据详情</h3>
      <div class="subtitle">选择任一节点或关系边；证据锚点仅作文本展示，页面不发起外部请求。</div>
    </div>
    <div class="legend">
      <strong>数据等级</strong>
      <span class="legend-item"><i class="swatch"></i>实边（强制披露实名）</span>
      <span class="legend-item"><i class="swatch half"></i>半边 / 半边槽位</span>
      <span class="legend-item"><i class="swatch inferred"></i>推断边（A级判定）</span>
      <span class="legend-item"><i class="swatch leak"></i>程序段落泄漏</span>
      <span class="legend-item"><i class="swatch dead"></i>已死亡</span>
    </div>
  </section>

  <section class="layer" id="layer-flow" role="tabpanel" aria-labelledby="tab-flow" hidden>
    <div class="topline">
      <h2>30个月出口流向</h2>
      <div class="metrics">
        <span class="metric"><b>30</b> 月总量曲线</span>
        <span class="metric"><b id="partner-month-count"></b> 月伙伴分拆</span>
        <span class="metric">top10 + 其他</span>
      </div>
    </div>
    <div class="notice"><b>2025-04 拐点：</b>马来西亚当月出口金额首次超过美国。2024 年输入只有月度总量，伙伴榜从 2025-01 起展示。</div>
    <div class="control-row">
      <div>
        <div class="month-readout" id="month-readout">2025-04</div>
        <div class="subtitle" id="month-total"></div>
      </div>
      <div class="range-wrap">
        <span class="turn-label">▲ 2025-04 首超</span>
        <input id="month-slider" type="range" min="0" max="29" value="15" step="1" list="month-options" aria-label="选择月份">
        <datalist id="month-options">
          <option value="0" label="202401"></option><option value="3" label="202404"></option>
          <option value="11" label="202412"></option><option value="12" label="202501"></option>
          <option value="15" label="202504"></option><option value="23" label="202512"></option>
          <option value="24" label="202601"></option><option value="29" label="202606"></option>
        </datalist>
        <div class="range-ends"><span>202401</span><span>202504 · 拐点</span><span>202606</span></div>
      </div>
    </div>
    <div class="flow-layout">
      <div class="chart-panel">
        <svg id="total-chart" class="flow-svg" viewBox="0 0 920 390" role="img" aria-label="2024年1月至2026年6月出口金额总量曲线"></svg>
      </div>
      <aside class="partner-panel" id="partner-panel" aria-live="polite"></aside>
    </div>
    <div class="legend">
      <strong>数据等级</strong>
      <span>海关总量与伙伴维度：A级原始聚合 · HS 85177950 光通信设备的激光收发模块 · 金额 USD</span>
      <div class="legend-warning"><b>夹层警示｜目的地≠终端客户：</b>马来西亚、泰国、中国香港等去向可能包含转运、分销、封测或加工夹层；海关目的地不能直接归因为云厂商终端客户。</div>
    </div>
  </section>

  <section class="layer" id="layer-dim" role="tabpanel" aria-labelledby="tab-dim" hidden data-trademode-status="__DIM_STATUS__">
    <div class="topline">
      <h2>迁移是真产能还是转口</h2>
      <div class="metrics">
        <span class="metric">马来西亚</span><span class="metric">美国</span><span class="metric">泰国</span>
        <span class="metric">贸易方式 · 月度堆叠</span>
      </div>
    </div>
    <div id="dimension-content"></div>
    <div class="legend">
      <strong>判读边界</strong>
      <span>贸易方式拆解是产能迁移判定器，不自动等价于公司归属；一般贸易、特殊监管区域物流、进料加工等必须按月观察。</span>
      <div class="legend-warning"><b>夹层警示｜目的地≠终端客户：</b>贸易方式解释货物如何出境，不证明最终客户是谁；公司级映射仍需独立披露证据。</div>
    </div>
  </section>

  <footer class="footer">
    <span>关系：output/edges.csv + output/nodes.csv</span>
    <span>流向：customs-monthly.csv + customs-partners.csv</span>
    <span>维度：customs-trademode.csv（X1）</span>
  </footer>
</main>
<div class="tooltip" id="tooltip" role="status"></div>
<script>
"use strict";
const REL_NODES=__REL_NODES__;
const REL_EDGES=__REL_EDGES__;
const FLOW=__FLOW_DATA__;
const DIM=__DIM_DATA__;
const byId=(id)=>document.getElementById(id);
const esc=(value)=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money=(value)=>"$"+(Number(value)/1e8).toFixed(2)+"亿";
const integer=(value)=>Math.round(Number(value)).toLocaleString("zh-CN");

document.querySelectorAll(".tab").forEach(button=>{
  button.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(item=>item.setAttribute("aria-selected","false"));
    document.querySelectorAll(".layer").forEach(layer=>{layer.classList.remove("active");layer.hidden=true;});
    button.setAttribute("aria-selected","true");
    const layer=byId("layer-"+button.dataset.layer);layer.hidden=false;layer.classList.add("active");
  });
});

byId("rel-node-count").textContent=REL_NODES.length;
byId("rel-edge-count").textContent=REL_EDGES.length;
const nodeMap=Object.fromEntries(REL_NODES.map(item=>[item.key,item]));
const edgeMap=Object.fromEntries(REL_EDGES.map(item=>[item.id,item]));
function clearRelationshipSelection(){
  document.querySelectorAll(".rel-node.selected,.rel-edge.selected").forEach(el=>el.classList.remove("selected"));
}
function showNode(key){
  clearRelationshipSelection();
  const node=nodeMap[key],element=document.querySelector(`[data-node-key="${CSS.escape(key)}"]`);
  if(element)element.classList.add("selected");
  const attached=REL_EDGES.filter(edge=>edge.source===key||edge.target===key);
  byId("rel-detail").innerHTML=`<h3>${esc(node.name)}${node.slot?' · 匿名槽位':''}${node.virtual?' · 补虚节点':''}</h3>
    <div class="detail-grid"><div><span>类型</span>${esc(node.type)}</div><div><span>供应链层</span>${esc(node.layer)}</div>
    <div><span>国别 / 代码</span>${esc(node.country||"—")} · ${esc(node.code||"—")}</div>
    <div class="wide"><span>备注</span>${esc(node.memo||"—")}</div><div class="wide"><span>相连边</span>${attached.map(edge=>esc(edge.id)).join("、")||"—"}</div></div>`;
}
function showEdge(id){
  clearRelationshipSelection();
  const edge=edgeMap[id],element=document.querySelector(`[data-edge-id="${CSS.escape(id)}"]`);
  if(element)element.classList.add("selected");
  byId("rel-detail").innerHTML=`<h3>${esc(edge.id)} · ${esc(edge.sourceName)} → ${esc(edge.targetName)}</h3>
    <div class="detail-grid"><div><span>边等级</span>${esc(edge.grade)}</div><div><span>财年</span>${esc(edge.year)}</div>
    <div><span>占比或金额</span>${esc(edge.amount)}</div><div><span>证据文件</span>${esc(edge.evidence)}</div>
    <div><span>验证状态</span>${esc(edge.status)}</div><div class="wide"><span>披露锚点（文本）</span>${esc(edge.anchor)}</div>
    <div class="wide"><span>备注</span>${esc(edge.memo||"—")}</div></div>`;
}
document.querySelectorAll(".rel-node").forEach(el=>{
  el.addEventListener("click",()=>showNode(el.dataset.nodeKey));
  el.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();showNode(el.dataset.nodeKey);}});
});
document.querySelectorAll(".rel-edge").forEach(el=>{
  el.addEventListener("click",()=>showEdge(el.dataset.edgeId));
  el.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();showEdge(el.dataset.edgeId);}});
});

const tooltip=byId("tooltip");
function tipShow(event,markup){
  tooltip.innerHTML=markup;tooltip.style.display="block";
  const x=Math.min(event.clientX+14,window.innerWidth-tooltip.offsetWidth-12);
  const y=Math.min(event.clientY+14,window.innerHeight-tooltip.offsetHeight-12);
  tooltip.style.left=Math.max(8,x)+"px";tooltip.style.top=Math.max(8,y)+"px";
}
function tipHide(){tooltip.style.display="none";}

const months=FLOW.months;
byId("partner-month-count").textContent=months.filter(item=>item.hasPartners).length;
const chart=byId("total-chart"),slider=byId("month-slider");
const chartW=920,chartH=390,left=66,right=26,chartTop=34,chartBottom=58;
const plotW=chartW-left-right,plotH=chartH-chartTop-chartBottom;
const maxTotal=Math.max(...months.map(item=>item.total))*1.08;
const xAt=index=>left+plotW*index/(months.length-1);
const yAt=value=>chartTop+plotH*(1-value/maxTotal);
function renderTotalChart(){
  let markup=`<text class="chart-title" x="${left}" y="18">出口金额总量 · USD</text>`;
  for(let tick=0;tick<=4;tick++){
    const value=maxTotal*tick/4,y=yAt(value);
    markup+=`<line class="gridline" x1="${left}" y1="${y}" x2="${chartW-right}" y2="${y}"></line>
      <text class="axis-label" x="${left-8}" y="${y+4}" text-anchor="end">${(value/1e8).toFixed(1)}亿</text>`;
  }
  const line=months.map((item,index)=>`${xAt(index)},${yAt(item.total)}`).join(" ");
  const area=`${left},${chartTop+plotH} ${line} ${chartW-right},${chartTop+plotH}`;
  markup+=`<polygon class="total-area" points="${area}"></polygon><polyline class="total-line" points="${line}"></polyline>`;
  const turnIndex=months.findIndex(item=>item.month===FLOW.turningMonth),turnX=xAt(turnIndex);
  markup+=`<line class="turn-line" x1="${turnX}" y1="${chartTop}" x2="${turnX}" y2="${chartTop+plotH}"></line>
    <text class="turn-text" x="${turnX+7}" y="${chartTop+12}">2025-04 马来西亚首超美国</text>`;
  months.forEach((item,index)=>{
    markup+=`<circle class="total-dot" data-month-index="${index}" cx="${xAt(index)}" cy="${yAt(item.total)}" r="3.6"></circle>`;
    if(index%3===0||index===months.length-1){
      markup+=`<text class="axis-label" x="${xAt(index)}" y="${chartH-24}" text-anchor="middle">${item.month.slice(2,4)}.${item.month.slice(4)}</text>`;
    }
  });
  chart.innerHTML=markup;
  chart.querySelectorAll(".total-dot").forEach(dot=>{
    const index=Number(dot.dataset.monthIndex),item=months[index];
    dot.addEventListener("click",()=>{slider.value=index;selectMonth(index);});
    dot.addEventListener("mouseenter",event=>tipShow(event,`${item.label}<br><b>${integer(item.total)} USD</b><br>${integer(item.kg)} kg`));
    dot.addEventListener("mouseleave",tipHide);
  });
}
function partnerPanel(item){
  if(!item.hasPartners){
    return `<div class="partner-head"><h3>${item.label} · 伙伴去向</h3></div>
      <div class="empty"><div><b>本月仅有总量</b><p>customs-partners.csv 的伙伴分拆从 2025-01 开始；此处不补猜、不插值。</p></div></div>`;
  }
  const maximum=Math.max(...item.partners.map(flow=>flow.amount));
  const rows=item.partners.map((flow,index)=>`<div class="bar-row" data-name="${esc(flow.name)}">
    <div class="bar-name">${index<10?index+1:"—"} · ${esc(flow.name)}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${maximum?flow.amount/maximum*100:0}%"></div></div>
    <div class="bar-value">${(flow.share*100).toFixed(1)}%</div></div>`).join("");
  return `<div class="partner-head"><h3>${item.label} · 伙伴 top10</h3>${item.turning?'<span class="special">马来西亚首超美国</span>':''}</div>
    <div class="partner-total">${item.partnerCount} 个伙伴 · 分拆合计 ${money(item.partnerSum)}</div><div class="bars">${rows}</div>`;
}
function selectMonth(index){
  const item=months[index];
  byId("month-readout").textContent=item.label;
  byId("month-total").textContent=`${money(item.total)} · ${integer(item.kg)} kg`;
  byId("partner-panel").innerHTML=partnerPanel(item);
  chart.querySelectorAll(".total-dot").forEach((dot,i)=>dot.classList.toggle("active",i===index));
}
slider.addEventListener("input",()=>selectMonth(Number(slider.value)));
renderTotalChart();selectMonth(Number(slider.value));

const modeColors=["#168174","#4e7192","#c77b28","#7253a6","#a54b45","#8b96a0","#5f8062","#b09257"];
function renderDimension(){
  const root=byId("dimension-content");
  if(DIM.status!=="ready"){
    root.innerHTML=`<div class="stage dim-placeholder"><div><div class="waiting-mark">…</div>
      <h3>${esc(DIM.message||"数据待X1交付")}</h3>
      <p>维度层已预留安全降级：其余两层保持可用。X1 生成 customs-trademode.csv 后重新运行构建脚本即可自动装配。</p></div></div>`;
    return;
  }
  const colorMap=Object.fromEntries(DIM.modes.map((mode,index)=>[mode,modeColors[index%modeColors.length]]));
  const legend=DIM.modes.map(mode=>`<span class="legend-item"><i class="swatch" style="background:${colorMap[mode]}"></i>${esc(mode)}</span>`).join("");
  root.innerHTML=`<div class="dim-grid">${DIM.destinations.map(destination=>`<section class="dim-panel">
    <h3>${esc(destination)}</h3><div class="dim-sub">每月出口金额按贸易方式堆叠 · USD</div>
    <svg class="dim-svg" data-destination="${esc(destination)}" viewBox="0 0 480 340" role="img" aria-label="${esc(destination)}贸易方式月度堆叠条形图"></svg>
    </section>`).join("")}</div><div class="legend"><strong>贸易方式</strong>${legend}</div>`;
  document.querySelectorAll(".dim-svg").forEach(svg=>{
    const destination=svg.dataset.destination,W=480,H=340,L=48,R=12,T=22,B=52;
    const destinationRows=DIM.rows.filter(row=>row.destination===destination);
    const totals=Object.fromEntries(DIM.months.map(month=>[month,destinationRows.filter(row=>row.month===month).reduce((sum,row)=>sum+row.amount,0)]));
    const maximum=Math.max(1,...Object.values(totals)),barSpan=(W-L-R)/Math.max(1,DIM.months.length),barW=Math.max(4,barSpan*.68);
    let markup="";
    for(let tick=0;tick<=3;tick++){
      const value=maximum*tick/3,y=T+(H-T-B)*(1-value/maximum);
      markup+=`<line class="gridline" x1="${L}" y1="${y}" x2="${W-R}" y2="${y}"></line>
        <text class="axis-label" x="${L-6}" y="${y+4}" text-anchor="end">${(value/1e8).toFixed(1)}亿</text>`;
    }
    DIM.months.forEach((month,index)=>{
      const x=L+barSpan*index+(barSpan-barW)/2,total=totals[month]||0;let baseY=H-B;
      DIM.modes.forEach(mode=>{
        const row=destinationRows.find(item=>item.month===month&&item.mode===mode),amount=row?row.amount:0;
        const height=(H-T-B)*(amount/maximum);baseY-=height;
        if(height>0)markup+=`<rect class="dim-segment" data-month="${month}" data-mode="${esc(mode)}" data-amount="${amount}" x="${x}" y="${baseY}" width="${barW}" height="${height}" fill="${colorMap[mode]}"></rect>`;
      });
      if(index%3===0||index===DIM.months.length-1)markup+=`<text class="axis-label" x="${x+barW/2}" y="${H-28}" text-anchor="middle">${month.slice(2,4)}.${month.slice(4)}</text>`;
      if(total===0)markup+=`<line x1="${x}" y1="${H-B}" x2="${x+barW}" y2="${H-B}" stroke="#bfc3c5"></line>`;
    });
    svg.innerHTML=markup;
    svg.querySelectorAll(".dim-segment").forEach(segment=>{
      segment.addEventListener("mouseenter",event=>tipShow(event,`${destination} · ${segment.dataset.month}<br>${esc(segment.dataset.mode)}<br><b>${money(segment.dataset.amount)}</b>`));
      segment.addEventListener("mouseleave",tipHide);
    });
  });
}
renderDimension();
</script>
</body>
</html>
"""


def build_html(
    nodes: list[dict], edges: list[dict], relationship_markup: str, flow: dict, dimension: dict
) -> str:
    return (
        HTML_SHELL.replace("__RELATIONSHIP_SVG__", relationship_markup)
        .replace("__REL_NODES__", js_data(nodes))
        .replace("__REL_EDGES__", js_data(edges))
        .replace("__FLOW_DATA__", js_data(flow))
        .replace("__DIM_DATA__", js_data(dimension))
        .replace("__DIM_STATUS__", esc(dimension["status"]))
    )


def assertions(
    document: str,
    nodes: list[dict],
    edges: list[dict],
    flow: dict,
    dimension: dict,
) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        results.append((name, bool(condition), detail))

    external_pattern = re.compile(
        r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//|<link\b|@import\s|url\(\s*["']?\s*(?:https?:)?//|fetch\s*\(|XMLHttpRequest|WebSocket\s*\(""",
        re.IGNORECASE,
    )
    check("svg在位", document.count("<svg") >= 3, f"svg={document.count('<svg')}")
    check("零外链", not external_pattern.search(document))
    check("UTF-8中文", 'charset="utf-8"' in document and 'lang="zh-CN"' in document)
    check("关键实体「中际旭创」", "中际旭创" in document)
    check("关键目的地「马来西亚」", "马来西亚" in document)
    check("滑条含202404与202606", 'label="202404"' in document and 'label="202606"' in document)
    check("三层切换在位", all(marker in document for marker in ('id="tab-rel"', 'id="tab-flow"', 'id="tab-dim"')))
    check("关系层81边", len(edges) == 81, f"edges={len(edges)}")
    check("E014半边纳入", any(edge["id"] == "E014" and edge["style"] == "half" for edge in edges))
    check("苏世博补虚节点", any(node["name"] == "苏世博" and node["virtual"] for node in nodes))
    grades = {edge["style"] for edge in edges}
    check("五种边样式齐全", grades == {"solid", "half", "inferred", "leak", "dead"}, ",".join(sorted(grades)))
    months = [item["month"] for item in flow["months"]]
    check("流向层30月", months == EXPECTED_MONTHS, f"months={len(months)}")
    check("2025-04拐点标记", TURNING_MONTH in document and "马来西亚首超美国" in document)
    partner_months = [item for item in flow["months"] if item["hasPartners"]]
    check("伙伴月份top10+其他", all(len(item["partners"]) == 11 for item in partner_months), f"months={len(partner_months)}")
    check("目的地≠终端客户警示", "目的地≠终端客户" in document)
    if dimension["status"] == "pending":
        check(
            "trademode缺失占位逻辑",
            "数据待X1交付" in document and 'data-trademode-status="pending"' in document,
        )
    else:
        check(
            "trademode三目的地装配",
            dimension["status"] == "ready"
            and set(dimension["destinations"]) == set(DIM_DESTINATIONS)
            and bool(dimension["rows"]),
            f"rows={len(dimension['rows'])}",
        )
    return results


def main() -> int:
    node_rows = read_csv(NODES_CSV)
    edge_rows = read_csv(EDGES_CSV)
    monthly_rows = read_csv(MONTHLY_CSV)
    partner_rows = read_csv(PARTNERS_CSV)

    if len(edge_rows) != 81:
        raise ValueError(f"edges.csv 应为81行，实际 {len(edge_rows)}")
    nodes, edges, slot_count, virtual_count = build_relationship_model(node_rows, edge_rows)
    relationship_markup = relationship_svg(nodes, edges)
    flow = build_flow_model(monthly_rows, partner_rows)
    dimension = build_dimension_model()
    document = build_html(nodes, edges, relationship_markup, flow, dimension)
    OUT_HTML.write_text(document, encoding="utf-8")

    checks = assertions(document, nodes, edges, flow, dimension)
    failures = [item for item in checks if not item[1]]
    style_counts = Counter(edge["style"] for edge in edges)
    partner_months = [item for item in flow["months"] if item["hasPartners"]]
    partner_flows = sum(len(item["partners"]) for item in partner_months)
    dimension_size = (
        f"{len(dimension['rows'])} 条聚合记录 · {len(dimension['months'])} 月 · "
        f"{len(dimension['modes'])} 种贸易方式"
        if dimension["status"] == "ready"
        else "0 条（数据待X1交付占位）"
    )

    print("=" * 76)
    print(f"文件路径: {OUT_HTML}")
    print(
        f"关系层: {len(nodes)} 节点（nodes.csv {len(node_rows)} + 匿名槽位 {slot_count} + 补虚 {virtual_count}）"
        f" · {len(edges)} 边（实边 {style_counts['solid']} / 半边系 {style_counts['half']} / "
        f"推断 {style_counts['inferred']} / 程序泄漏 {style_counts['leak']} / 已死亡 {style_counts['dead']}）"
    )
    print(
        f"流向层: {len(flow['months'])} 月总量 · {len(partner_months)} 月伙伴分拆 · "
        f"{partner_flows} 条月度流向（top10+其他）"
    )
    print(f"维度层: {dimension_size}")
    print("-" * 76)
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
    print("-" * 76)
    print(f"断言结果: {len(checks) - len(failures)} PASS / {len(failures)} FAIL")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
