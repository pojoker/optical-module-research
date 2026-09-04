#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关系级时间聚合 (R3) —— 严格按 flows/relationship-timeline-contract.md v1.2 实现。

输入:
  - flows/out/edge-timeline.csv   (上轮 per-edge 产出: edge_id,供方,需方,year,pct_or_amt,observe_type)
  - output/edges.csv              (关系级 period_type 来源: edge_id -> 财年)

输出:
  - flows/out/relationship-timeline.csv
    schema: relation_id,供方,需方,period,period_type,pct_or_amt,observe_type,source_edge_ids,conflict

契约要点 (v1.2):
  1. 关系键经内置别名映射归一化(不按显示名 groupby)。
  2. 匿名端点(含"匿名")默认逐观测独立 —— 关系键追加 source_edge_id，每行 observe_type=observed，
     不赋 first/last/censored，跨期不做连续语义。
     例外(契约例外表, 联讯招股书同文件恒定代号, 身份连续性由文件本身保证): 需方=集团一(匿名)
     → 照常跨期聚合，first/last 正常计算。
  3. 排序键一律按"期末月数值键"：自然年 YYYY→YYYY*100+12；季度 YYYYQn→YYYY*100+3n；
     财年 FY+YYYY→YYYY*100+12；月份 YYYY-MM→YYYY*100+M。逐期间用其自身 period_type 计算，
     禁止用循环外泄变量推断类型。
  4. first/last 按 (关系键, period_type 归并基准) 分序列计算：fiscal 与自然年(years/quarter/month
     同属日历基准)各自独立首尾，不共用排序序列（红队 T03）。
  5. FY 与自然年不混同: period = "FY"+year (财年以 FY 开头时), period_type=fiscal。
  6. 同年同关系多边冲突: 金额/占比一致合并(列全来源边); 不一致保留多行 conflict=true。
  7. confirmed_ended 仅当该关系"全部有效来源边"均达 confirmed_ended(关系级, 红队 T06);
     observed 优先于 censored。
  8. 每个聚合事件行带 source_edge_ids(分号分隔), 不丢证据链。

仅用标准库。
"""

import csv
import os
import re
import sys

# ----------------------------------------------------------------------------
# 0. 路径 (相对脚本位置, 与 cwd 无关)
# ----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))          # .../workflow-rehearsal
EDGE_TIMELINE_CSV = os.path.join(REPO_ROOT, "flows", "out", "edge-timeline.csv")
EDGES_CSV = os.path.join(REPO_ROOT, "output", "edges.csv")
OUT_CSV = os.path.join(REPO_ROOT, "flows", "out", "relationship-timeline.csv")

# 契约 v1.2 例外表: 需方=集团一(匿名)(联讯招股书同文件恒定代号) 跨期聚合, 不触发匿名独立规则。
EXCEPTION_ANON_CON = "集团一(匿名)"

# ----------------------------------------------------------------------------
# 1. 关系键别名映射表 (契约 §1, 实现内置 dict)
# ----------------------------------------------------------------------------
ALIAS = {
    "Fabrinet(解匿)": "Fabrinet",
    "Ciena(解匿)": "Ciena",
    "Google(解匿)": "Google",
    "中际旭创(作为客户)": "中际旭创",
    "华为+海思": "华为(含海思)",
    "华为": "华为(含海思)",
    "博通(客户)": "博通(Broadcom)",
    "Broadcom": "博通(Broadcom)",
    "NVIDIA(客户)": "NVIDIA",
    "ficonTEC(罗博特科)": "罗博特科/ficonTEC",
    # 契约 v1.1 (2026-07-24) 补: 裸名 E076 与 E011/E012 同一主体
    "罗博特科": "罗博特科/ficonTEC",
    "PINEWAVE(关联方)": "PINEWAVE",
    "浙江粮油(出口代理)": "浙江粮油",
    "索尔思(Source Photonics)": "索尔思(Source Photonics)",
    "苏世博": "索恩格(SEG Automotive)",
}


def normalize(name):
    """应用契约别名映射; 匿名端点原样保留(靠完整键名天然不聚合)。"""
    return ALIAS.get(name, name)


def is_anonymous(name):
    return "匿名" in name


# ----------------------------------------------------------------------------
# 2. 期间键 / period_type 推导 (契约 §2)
# ----------------------------------------------------------------------------
def derive_period(fy_raw, year):
    """返回 (period, period_type)。

    fy_raw : output/edges.csv 的 财年 字段 (用于判定 FY 口径)
    year   : edge-timeline.csv 的 year 字段 (裸年如 '2023', 或 '2025Q1'/'2025-09'/'2023-2025')
    """
    fy_raw = (fy_raw or "").strip()
    if fy_raw.upper().startswith("FY"):
        # FY 口径: 给裸年加 FY 前缀, 与自年显式区分
        y = year.strip()
        period = y if y.upper().startswith("FY") else "FY" + y
        return period, "fiscal"
    # 自然年口径
    y = year.strip()
    if "Q" in y.upper():
        return y, "quarter"
    if re.match(r"^\d{4}-\d{2}$", y):
        return y, "month"
    return y, "year"


# ----------------------------------------------------------------------------
# 3. 期间排序键 (v1.2 修正, 红队 T02): 一律"期末月数值键"
# ----------------------------------------------------------------------------
def period_sort_value(period, ptype):
    """跨口径可比的期末月数值键 (仅用于关系内 first/last 判定)。

    自然年 YYYY          -> YYYY*100 + 12
    季度   YYYYQn        -> YYYY*100 + 3n
    月份   YYYY-MM       -> YYYY*100 + M
    财年   FY+YYYY       -> YYYY*100 + 12
    无法解析             -> 0
    """
    try:
        if ptype == "fiscal":
            m = re.match(r"FY(\d{4})", period)
            if m:
                return int(m.group(1)) * 100 + 12
        elif ptype == "year":
            y = period.split("-")[0] if "-" in period else period
            return int(y) * 100 + 12
        elif ptype == "quarter":
            m = re.match(r"(\d{4})Q(\d)", period)
            if m:
                return int(m.group(1)) * 100 + 3 * int(m.group(2))
        elif ptype == "month":
            m = re.match(r"(\d{4})-(\d{2})", period)
            if m:
                return int(m.group(1)) * 100 + int(m.group(2))
    except Exception:
        pass
    return 0


def basis_of(ptype):
    """红队 T03: 分序列基准。fiscal 独立成一条序列; year/quarter/month 同属日历基准,
    因为季度/月份与自然年共享同一日历时间轴(如 2025Q1 在 2024 之后、2025 之内),
    不应彼此拆成独立首尾。"""
    return "fiscal" if ptype == "fiscal" else "calendar"


# ----------------------------------------------------------------------------
# 4. 关系级 observe_type 裁决 (契约 §4, 红队 T06)
# ----------------------------------------------------------------------------
OBSERVED_TYPES = ("observed", "first_observed", "last_observed")


def resolve_observe_type(is_first, is_last, edge_obs, rel_all_ended):
    """is_first / is_last 已经按 (关系键, period_type 基准) 分序列算好 (红队 T03)。

    rel_all_ended: 关系级 —— 该关系"全部有效来源边"均达 confirmed_ended (红队 T06)。
    """
    has_observation = any(o in OBSERVED_TYPES for o in edge_obs)

    if is_first:
        return "first_observed" if has_observation else "censored"
    if is_last:
        if rel_all_ended:
            return "confirmed_ended"
        if has_observation:
            return "last_observed"
        return "censored"
    # 中间期: observed 优先 (契约 §4 同期间 observed 盖过 censored)
    if has_observation:
        return "observed"
    return "censored"


# ----------------------------------------------------------------------------
# 5. 主流程
# ----------------------------------------------------------------------------
def load_fy_map():
    """edge_id -> 财年 (output/edges.csv 第5列)。"""
    fy_map = {}
    with open(EDGES_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            eid = row["edge_id"].strip()
            if eid and eid not in fy_map:
                fy_map[eid] = row.get("财年", "")
    return fy_map


def load_events(fy_map, warnings):
    """读取 per-edge 时间线, 归一化 + 推导 period, 返回事件列表。

    匿名规则 (契约 v1.2 §1, 红队 T01):
      - 匿名端点且非例外 -> 关系键追加 source_edge_id, 逐观测独立 (anon_independent=True)。
      - 例外(需方=集团一(匿名))-> 照常 (sup, con) 聚合。
    """
    events = []
    missing_fy = []
    with open(EDGE_TIMELINE_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            eid = row["edge_id"].strip()
            sup_raw = row["供方"].strip()
            con_raw = row["需方"].strip()
            year = row["year"].strip()
            pct = row["pct_or_amt"].strip()
            obs = row["observe_type"].strip()

            sup = normalize(sup_raw)
            con = normalize(con_raw)

            is_anon = is_anonymous(sup) or is_anonymous(con)
            is_exception = (con == EXCEPTION_ANON_CON)
            anon_independent = is_anon and not is_exception

            if anon_independent:
                # 逐观测独立: 关系键追加 source_edge_id
                rel_key = (sup, con, eid)
            else:
                rel_key = (sup, con)

            fy_raw = fy_map.get(eid)
            if fy_raw is None:
                missing_fy.append(eid)
                fy_raw = ""  # 退化为按 year 内容判口径
            period, ptype = derive_period(fy_raw, year)

            events.append({
                "edge_id": eid,
                "sup": sup,
                "con": con,
                "rel_key": rel_key,
                "anon_independent": anon_independent,
                "period": period,
                "ptype": ptype,
                "pct": pct,
                "obs": obs,
                "anon": is_anon,
            })
    if missing_fy:
        warnings.append("边 %s 在 output/edges.csv 缺失 财年, 退化为按 year 判口径"
                        % ",".join(sorted(set(missing_fy))))
    return events


def aggregate(events, warnings):
    """关系级聚合。返回 (relationships, conflict_total, anon_independent_rows)。"""
    by_rel = {}
    for ev in events:
        by_rel.setdefault(ev["rel_key"], []).append(ev)

    relationships = []
    conflict_total = 0
    anon_independent_rows = 0

    for rel_key in sorted(by_rel.keys(), key=lambda k: (k[0], k[1])):
        sup, con = rel_key[0], rel_key[1]
        evs = by_rel[rel_key]
        anon_ind = evs[0].get("anon_independent", False)

        # 关系内按 (period 串, period_type) 分组
        period_keys = {}
        for ev in evs:
            pk = (ev["period"], ev["ptype"])
            period_keys.setdefault(pk, []).append(ev)
        ptype_of_period = {pk[0]: pk[1] for pk in period_keys}

        # ---- 匿名独立路径 (红队 T01) ----
        if anon_ind:
            rel_rows = []
            for pk, group in period_keys.items():
                period = pk[0]
                # 逐观测独立: 每行 observe_type=observed, 不赋 first/last/censored
                canonical = max((g["pct"] for g in group), key=len)
                edge_ids = sorted({g["edge_id"] for g in group})
                rel_rows.append({
                    "period": period,
                    "ptype": pk[1],
                    "pct": canonical,
                    "obs": "observed",
                    "edge_ids": edge_ids,
                    "conflict": False,
                })
                anon_independent_rows += 1
            rel_rows.sort(key=lambda r: (period_sort_value(r["period"], r["ptype"]), r["period"]))
            relationships.append({
                "sup": sup, "con": con, "anon": True,
                "anon_independent": True, "rows": rel_rows,
            })
            continue

        # ---- 正常聚合路径 ----
        # 分序列 first/last 基准 (红队 T03): fiscal 与 calendar 各自独立首尾
        basis_periods = {}
        for pk in period_keys:
            basis_periods.setdefault(basis_of(pk[1]), []).append(pk[0])
        sub_first = {}
        sub_last = {}
        for b, ps in basis_periods.items():
            ps_sorted = sorted({p for p in ps},
                               key=lambda p: (period_sort_value(p, ptype_of_period[p]), p))
            if ps_sorted:
                sub_first[ps_sorted[0]] = True
                sub_last[ps_sorted[-1]] = True

        # 关系级 confirmed_ended 就绪度 (红队 T06): 全部有效来源边均达 confirmed_ended
        edge_ids_in_rel = {ev["edge_id"] for ev in evs}
        edge_ended = {}
        for ev in evs:
            if ev["obs"] == "confirmed_ended":
                edge_ended[ev["edge_id"]] = True
        rel_all_ended = bool(edge_ids_in_rel) and all(
            edge_ended.get(e, False) for e in edge_ids_in_rel)

        rel_rows = []
        for pk, group in period_keys.items():
            period = pk[0]
            edge_obs = [g["obs"] for g in group]
            is_first = sub_first.get(period, False)
            is_last = sub_last.get(period, False)
            rel_obs = resolve_observe_type(is_first, is_last, edge_obs, rel_all_ended)

            # 按数值可比键分簇: 同值合并(列全来源边), 异值冲突
            clusters = {}  # value_key -> [canonical_pct, set(edge_ids)]
            for g in group:
                vk = value_key(g["pct"])
                if vk not in clusters:
                    clusters[vk] = [g["pct"], set()]
                if len(g["pct"]) > len(clusters[vk][0]):
                    clusters[vk][0] = g["pct"]
                clusters[vk][1].add(g["edge_id"])
            distinct = list(clusters.keys())
            if len(distinct) == 1:
                vk = distinct[0]
                edge_ids = sorted(clusters[vk][1])
                rel_rows.append({
                    "period": period,
                    "ptype": pk[1],
                    "pct": clusters[vk][0],
                    "obs": rel_obs,
                    "edge_ids": edge_ids,
                    "conflict": False,
                })
                # 字面值不同但数值一致 -> 合并(契约 §3); 透明记录
                lits = sorted({g["pct"] for g in group})
                if len(lits) > 1:
                    warnings.append(
                        "关系 %s→%s 期间 %s 字面值不同但占比一致, 已合并: %s (edges=%s)"
                        % (sup, con, period, " / ".join(lits), ",".join(edge_ids))
                    )
            else:
                # 冲突: 保留多行, 各标 conflict=true
                conflict_total += len(distinct)
                for vk in distinct:
                    edge_ids = sorted(clusters[vk][1])
                    rel_rows.append({
                        "period": period,
                        "ptype": pk[1],
                        "pct": clusters[vk][0],
                        "obs": rel_obs,
                        "edge_ids": edge_ids,
                        "conflict": True,
                    })
                warnings.append(
                    "关系 %s→%s 期间 %s 多边冲突(保留 %d 行): %s"
                    % (sup, con, period, len(distinct),
                       "; ".join("%s[%s]" % (clusters[v][0], ",".join(sorted(clusters[v][1])))
                                 for v in distinct))
                )

        rel_rows.sort(key=lambda r: (period_sort_value(r["period"], r["ptype"]), r["period"]))
        relationships.append({
            "sup": sup, "con": con, "anon": (is_anonymous(sup) or is_anonymous(con)),
            "anon_independent": False, "rows": rel_rows,
        })
    return relationships, conflict_total, anon_independent_rows


def value_key(pct):
    """契约 §3 '金额/占比一致则合并' —— 按数值而非字面值比较。

    提取首个数(占比优先取带 '%' 的数)作为可比键; 同键视为一致, 合并为一行。
    字面值不同但数值相同(如 '9.90%' 与 '9.90%(2730.72万元)')判为一致。
    """
    pct = (pct or "").strip()
    has_pct = "%" in pct
    nums = re.findall(r"\d+\.?\d*", pct)
    fnums = [float(n) for n in nums]
    primary = fnums[0] if fnums else None
    return (has_pct, primary)


def write_output(relationships):
    header = ["relation_id", "供方", "需方", "period", "period_type",
              "pct_or_amt", "observe_type", "source_edge_ids", "conflict"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for i, rel in enumerate(relationships, start=1):
            rid = "R%03d" % i
            for r in rel["rows"]:
                w.writerow([
                    rid, rel["sup"], rel["con"], r["period"], r["ptype"],
                    r["pct"], r["obs"], ";".join(r["edge_ids"]),
                    "true" if r["conflict"] else "false",
                ])


# ----------------------------------------------------------------------------
# 6. 自测
# ----------------------------------------------------------------------------
def self_test(relationships, conflict_total, anon_independent_rows, warnings):
    total_rows = sum(len(rel["rows"]) for rel in relationships)
    print("=" * 64)
    print("R3 关系级时间聚合 — 自测 (契约 v1.2 / 红队 T01-T03/T06)")
    print("=" * 64)
    print("关系数            : %d" % len(relationships))
    print("总事件行数        : %d" % total_rows)
    print("匿名独立行数      : %d" % anon_independent_rows)
    print("conflict 计数     : %d" % conflict_total)

    states = ["first_observed", "observed", "last_observed", "censored", "confirmed_ended"]
    dist = {s: 0 for s in states}
    for rel in relationships:
        for r in rel["rows"]:
            dist[r["obs"]] = dist.get(r["obs"], 0) + 1
    print("五态分布          : " + ", ".join("%s=%d" % (s, dist[s]) for s in states))

    # ---- 红队断言①: 联讯仪器→集团一(匿名) 例外聚合序列 2023 first→2024 observed→2025Q1 last ----
    print("-" * 64)
    print("断言① 联讯仪器→集团一(匿名) 序列 (契约例外, 跨期聚合)")
    g1 = _find_relation(relationships, "联讯仪器", "集团一(匿名)")
    assert g1 is not None, "未找到 联讯仪器→集团一(匿名) 关系"
    g1_rows = sorted(g1["rows"], key=lambda r: (period_sort_value(r["period"], r["ptype"]), r["period"]))
    for r in g1_rows:
        print("  %-8s %-8s %-12s %-14s %s  edges=%s"
              % (r["period"], r["ptype"], r["pct"], r["obs"],
                 "CONFLICT" if r["conflict"] else "", ";".join(r["edge_ids"])))
    seq = [(r["period"], r["obs"]) for r in g1_rows]
    # 顺序键: 2023 < 2024 < 2025Q1
    order_ok = (period_sort_value("2023", "year") < period_sort_value("2024", "year")
                < period_sort_value("2025Q1", "quarter"))
    firsts = [p for p, o in seq if o == "first_observed"]
    lasts = [p for p, o in seq if o == "last_observed"]
    assert order_ok, "联讯→集团一 期间排序非 2023<2024<2025Q1"
    assert seq[0] == ("2023", "first_observed"), "首期应为 2023 first_observed, 实为 %r" % (seq[0],)
    assert seq[-1] == ("2025Q1", "last_observed"), "末期应为 2025Q1 last_observed, 实为 %r" % (seq[-1],)
    assert len(firsts) == 1 and len(lasts) == 1, "first/last 应各仅一次, 实为 firsts=%r lasts=%r" % (firsts, lasts)
    assert ("2024", "observed") in seq, "2024 应为 observed(中间期)"
    print("  >> R069类排序断言通过: 2023 first → 2024 observed → 2025Q1 last, 顺序与首尾唯一正确")

    # ---- 红队断言②: Fabrinet→Lumentum FY2023 双行 conflict 保留 ----
    print("-" * 64)
    print("断言② Fabrinet→Lumentum FY2023 双行 conflict 保留")
    fl = _find_relation(relationships, "Fabrinet", "Lumentum")
    assert fl is not None, "未找到 Fabrinet→Lumentum 关系"
    fy2023_rows = [r for r in fl["rows"] if r["period"] == "FY2023"]
    fy2023_conflict = [r for r in fy2023_rows if r["conflict"]]
    for r in sorted(fy2023_rows, key=lambda r: r["pct"]):
        print("  %-8s %-8s %-12s %-14s %s  edges=%s"
              % (r["period"], r["ptype"], r["pct"], r["obs"],
                 "CONFLICT" if r["conflict"] else "", ";".join(r["edge_ids"])))
    assert len(fy2023_conflict) == 2, "FY2023 应保留 2 行 conflict, 实为 %d" % len(fy2023_conflict)
    all_edges = set()
    for r in fy2023_conflict:
        all_edges.update(r["edge_ids"])
    assert all_edges == {"E038", "E068"}, "FY2023 conflict 来源边应为 E038;E068, 实为 %r" % (sorted(all_edges),)
    print("  >> FY2023 双行 conflict 保留通过 (E038 + E068, 未被吞并合并)")

    # ---- 红队断言③: 猎奇智能→中际旭创 2024 合并 src=E010;E045 保留 ----
    print("-" * 64)
    print("断言③ 猎奇智能→中际旭创 2024 合并 src=E010;E045 保留")
    lx = _find_relation(relationships, "猎奇智能", "中际旭创")
    assert lx is not None, "未找到 猎奇智能→中际旭创 关系"
    r2024 = [r for r in lx["rows"] if r["period"] == "2024"]
    for r in r2024:
        print("  %-8s %-8s %-12s %-14s %s  edges=%s"
              % (r["period"], r["ptype"], r["pct"], r["obs"],
                 "CONFLICT" if r["conflict"] else "", ";".join(r["edge_ids"])))
    assert len(r2024) == 1, "2024 应为合并单行, 实为 %d 行" % len(r2024)
    assert r2024[0]["edge_ids"] == ["E010", "E045"], \
        "2024 来源边应为 E010;E045, 实为 %r" % (r2024[0]["edge_ids"],)
    print("  >> 2024 合并通过 (source_edge_ids=E010;E045, 占比一致 58.85% 合并单行)")

    # ---- 红队断言④: 匿名端点不再串接 first/last (抽查 猎奇→客户五(匿名)) ----
    print("-" * 64)
    print("断言④ 匿名端点逐观测独立 (猎奇智能→客户五(匿名), 无 first/last/censored)")
    c5 = _find_relation(relationships, "猎奇智能", "客户五(匿名)")
    if c5 is not None:
        for r in c5["rows"]:
            print("  %-8s %-8s %-12s %-14s edges=%s"
                  % (r["period"], r["ptype"], r["pct"], r["obs"], ";".join(r["edge_ids"])))
        assert all(r["obs"] == "observed" for r in c5["rows"]), "匿名关系不应出现 first/last/censored"
        print("  >> 匿名独立通过: 全部 observe_type=observed")
    else:
        print("  (未找到该匿名关系)")

    # 解析歧义 warnings
    print("-" * 64)
    print("解析歧义 / warnings (%d):" % len(warnings))
    if warnings:
        for w in warnings:
            print("  - " + w)
    else:
        print("  (无)")
    print("=" * 64)


def _find_relation(relationships, sup, con):
    for rel in relationships:
        if rel["sup"] == sup and rel["con"] == con:
            return rel
    return None


def _print_relation(relationships, sup, con):
    rel = _find_relation(relationships, sup, con)
    if rel is None:
        print("  (未在关系表中找到)")
        return
    for r in rel["rows"]:
        print("  %-8s %-8s %-12s %-10s %s  edges=%s"
              % (r["period"], r["ptype"], r["pct"], r["obs"],
                 "CONFLICT" if r["conflict"] else "", ";".join(r["edge_ids"])))


def main():
    warnings = []
    fy_map = load_fy_map()
    events = load_events(fy_map, warnings)

    # 契约歧义: 罗博特科 (裸名, E076) 与 罗博特科/ficonTEC (E011/E012) 实为同一主体,
    # 但契约别名表未将裸名 "罗博特科" 归一, 故保持为两条独立关系 —— 如实记录。
    norm_names = {ev["sup"] for ev in events} | {ev["con"] for ev in events}
    if "罗博特科" in norm_names and "罗博特科/ficonTEC" in norm_names:
        warnings.append("歧义: 裸名 '罗博特科'(E076) 与 '罗博特科/ficonTEC'(E011/E012) 域知识为同一主体, "
                        "但契约别名表未含裸名归一规则, 依契约保持为两条独立关系, 未硬凑合并。")

    relationships, conflict_total, anon_independent_rows = aggregate(events, warnings)
    write_output(relationships)
    self_test(relationships, conflict_total, anon_independent_rows, warnings)


if __name__ == "__main__":
    main()
