#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X5 路（晋级预检）草稿生成器 —— v1.3 SPEC 契约

读 flows/out/lianxun-extract.json 的 customers.periods / suppliers.periods，
把 2022-2025Q1 各期客户/供应商行转为 output/edges.csv 的 10 列 schema 草稿。

纪律（来自 AGENTS.md 与 SPEC-v1.3 X5 契约）：
- edge_id 留空占位 EXXX（晋级由 X6 人工执行，不在此分配真实 E0XX 编号）
- 不碰 output/edges.csv
- 每条边必须带 {证据文件, 财年, 披露方=联讯仪器, 占比或金额, 锚点, 边等级}
- 实名→实边；匿名（集团一/集团二）→半边槽位
- 锚点取 meta.anchor_url；若为空回退 flows/input/lianxun_prospectus.pdf 并在备注注明"本地件-锚点待补"
- 验证状态统一 "v1.3待人工复核"
- 备注含 name_full 与期间序列（该客户/供应商出现的各期）

运行：python3 flows/src/lianxun_to_edges.py
"""
import csv
import json
import os
import sys

# ── 路径解析（脚本位于 flows/src/，repo 根 = parents[1]）────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_PATH = os.path.join(REPO_ROOT, "flows", "out", "lianxun-extract.json")
OUTPUT_PATH = os.path.join(REPO_ROOT, "flows", "out", "lianxun-edges-draft.csv")

# ── 常量（契约写死）──────────────────────────────────────────────
SUPPLIER_NODE = "联讯仪器"                       # 招股书披露方（固定供方/需方节点）
EVIDENCE_FILE = "联讯仪器IPO招股书申报稿"         # 证据文件
VERIFY_STATUS = "v1.3待人工复核"                  # 验证状态
LOCAL_FALLBACK_ANCHOR = "flows/input/lianxun_prospectus.pdf"
EDGE_ID_PLACEHOLDER = "EXXX"

CSV_HEADER = [
    "edge_id", "供方", "需方", "占比或金额", "财年",
    "边等级", "证据文件", "锚点", "验证状态", "备注",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def period_sequence(index_map, name_raw):
    """返回该 name_raw 出现的所有期间，按原序去重。"""
    seq = index_map.get(name_raw, [])
    return "/".join(seq)


def build_edges(data):
    meta = data.get("meta", {})
    anchor = (meta.get("anchor_url") or meta.get("source_url") or "").strip()
    anchor_is_local = not anchor
    if anchor_is_local:
        anchor = LOCAL_FALLBACK_ANCHOR

    # 预建：name_raw -> 出现期间序列（客户侧 / 供应商侧分别计，避免互相污染）
    cust_periods = {}
    for p in data["customers"]["periods"]:
        for r in p["rows"]:
            cust_periods.setdefault(r["name_raw"], [])
            if p["period"] not in cust_periods[r["name_raw"]]:
                cust_periods[r["name_raw"]].append(p["period"])

    supp_periods = {}
    for p in data["suppliers"]["periods"]:
        for r in p["rows"]:
            supp_periods.setdefault(r["name_raw"], [])
            if p["period"] not in supp_periods[r["name_raw"]]:
                supp_periods[r["name_raw"]].append(p["period"])

    edges = []

    # ── 客户侧：联讯仪器(供方) → 客户(需方) ──────────────────────
    for p in data["customers"]["periods"]:
        period = p["period"]
        for r in p["rows"]:
            is_anon = bool(r.get("is_anonymous"))
            name_raw = r["name_raw"]
            pct = (r.get("pct") or "").strip()
            amount = f"{pct}%" if pct else ""
            if is_anon:
                demand = f"{name_raw}(匿名)"
                edge_level = "半边"
                nf = ""
                note_parts = [f"（招股书匿名标签，未披露实名）",
                              f"出现期间：{period_sequence(cust_periods, name_raw)}"]
            else:
                demand = name_raw
                edge_level = "实边"
                nf = r.get("name_full", "")
                note_parts = [nf,
                              f"出现期间：{period_sequence(cust_periods, name_raw)}"]
            if anchor_is_local:
                note_parts.append("本地件-锚点待补")
            edges.append({
                "edge_id": EDGE_ID_PLACEHOLDER,
                "供方": SUPPLIER_NODE,
                "需方": demand,
                "占比或金额": amount,
                "财年": period,
                "边等级": edge_level,
                "证据文件": EVIDENCE_FILE,
                "锚点": anchor,
                "验证状态": VERIFY_STATUS,
                "备注": "｜".join([x for x in note_parts if x]),
            })

    # ── 供应商侧：供应商(供方) → 联讯仪器(需方)，方向反转 ──────────
    for p in data["suppliers"]["periods"]:
        period = p["period"]
        for r in p["rows"]:
            is_anon = bool(r.get("is_anonymous"))
            name_raw = r["name_raw"]
            pct = (r.get("pct") or "").strip()
            amount = f"{pct}%" if pct else ""
            # 供应商侧全部实名披露 → 实边；匿名不会出现，仍按 is_anonymous 守纪律
            edge_level = "半边" if is_anon else "实边"
            nf = r.get("name_full", "") if not is_anon else ""
            note_parts = [f"（方向：供应商→{SUPPLIER_NODE}）"]
            if nf:
                note_parts.append(nf)
            note_parts.append(f"出现期间：{period_sequence(supp_periods, name_raw)}")
            if anchor_is_local:
                note_parts.append("本地件-锚点待补")
            edges.append({
                "edge_id": EDGE_ID_PLACEHOLDER,
                "供方": name_raw,
                "需方": SUPPLIER_NODE,
                "占比或金额": amount,
                "财年": period,
                "边等级": edge_level,
                "证据文件": EVIDENCE_FILE,
                "锚点": anchor,
                "验证状态": VERIFY_STATUS,
                "备注": "｜".join([x for x in note_parts if x]),
            })

    return edges


def write_csv(edges, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        w.writeheader()
        for e in edges:
            w.writerow(e)


def self_test(edges):
    total = len(edges)
    real = sum(1 for e in edges if e["边等级"] == "实边")
    half = sum(1 for e in edges if e["边等级"] == "半边")
    print("=== X5 自测 ===")
    print(f"草稿总行数      : {total}")
    print(f"实边计数        : {real}")
    print(f"半边槽位计数    : {half}")
    print(f"边等级合计校验  : {real + half} (应为 {total})")
    # 方向分布
    cust_edges = sum(1 for e in edges if e["供方"] == SUPPLIER_NODE)
    supp_edges = sum(1 for e in edges if e["需方"] == SUPPLIER_NODE)
    print(f"客户侧边(供方=联讯) : {cust_edges}")
    print(f"供应商侧边(需方=联讯): {supp_edges}")
    print("--- 抽印 3 行 ---")
    for e in edges[:3]:
        print(" | ".join(f"{k}={e[k]}" for k in CSV_HEADER))
    print("=== 完毕 ===")


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[错误] 输入文件不存在: {INPUT_PATH}", file=sys.stderr)
        sys.exit(1)
    data = load_json(INPUT_PATH)
    edges = build_edges(data)
    write_csv(edges, OUTPUT_PATH)
    print(f"[产出] 已写入: {OUTPUT_PATH}")
    self_test(edges)


if __name__ == "__main__":
    main()
