#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Y4 时间观察模型 (Time-Observation Model) — edge_timeline.py

读取 output/edges.csv (99 边)，将每条边里被压缩的"多年占比序列"展开成
关系事件表 (relationship event table)，六列：

    edge_id, 供方, 需方, year, pct_or_amt, observe_type

observe_type ∈ {first_observed, observed, last_observed,
                confirmed_started, confirmed_ended, censored}

设计原则（来自 SPEC-v1.4 Y4 契约 + Codex 批判 #4 "首次实名≠关系诞生"）：
- 严格区分"披露可见性"与"经济关系的生死"。
- 仅 E008 (NeoPhotonics-华为, 有明确季度归零 + 终止依赖披露) 标 confirmed_ended。
- 其余边的多年序列：最早年 first_observed、最晚年 last_observed、中间 observed。
- 单年观测（无边内序列）只标 observed——不把"首次看见"谎称为"关系诞生"。
- 备注中"跌出前五 / 跌破10%表 / 归零(非 E008 管制死亡)"标 censored，不标 ended。
- confirmed_started 仅当备注/证据明示合作起始年（本批数据实测为 0 条，不硬造）。
- 解析不了的备注序列格式如实写入 warnings，禁止硬凑年份或数值。

仅用标准库。不修改 output/ 下任何文件。
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # flows/src -> flows -> repo root
EDGES_CSV = os.path.join(ROOT, "output", "edges.csv")
OUT_DIR = os.path.join(ROOT, "flows", "out")
OUT_CSV = os.path.join(OUT_DIR, "edge-timeline.csv")

# E008 是唯一被允许标记 confirmed_ended 的边（有明确死亡披露）
CONFIRMED_ENDED_EDGE = "E008"

# ---------------------------------------------------------------------------
# 解析器：从一段文本中提取 (year, value) 正常占比序列对
# 覆盖数据中出现过的所有格式：
#   A. 2021:14.1%             B. FY2023:42.5%
#   C. 2024第一名31.74%        D. 62.19%(2023)  (值在年后括号里)
#   E. 2021/2022均为0         (显式 0，记为正常观测值 0%)
# ---------------------------------------------------------------------------
def parse_sequence_pairs(text):
    pairs = []
    # A / B: YEAR:VALUE% 或 FY+YEAR:VALUE%
    for m in re.finditer(r'(?:FY)?(\d{4})\s*[:：]\s*([\d.]+)\s*%', text):
        pairs.append((m.group(1), m.group(2) + '%'))
    # C: YEAR第X名VALUE%
    for m in re.finditer(r'(\d{4})第[一二三四五六七八九十]+名\s*([\d.]+)\s*%', text):
        pairs.append((m.group(1), m.group(2) + '%'))
    # D: VALUE%(YEAR) 或 VALUE%(FY+YEAR)
    for m in re.finditer(r'([\d.]+)\s*%\s*\((?:FY)?(\d{4})\)', text):
        pairs.append((m.group(2), m.group(1) + '%'))
    # E: YEAR/YEAR均为0  -> 显式 0%，视为正常观测值
    for m in re.finditer(r'(\d{4})\s*/\s*(\d{4})\s*均为0', text):
        pairs.append((m.group(1), '0%'))
        pairs.append((m.group(2), '0%'))
    return pairs


# ---------------------------------------------------------------------------
# 解析器：从备注中提取"受披露阈值影响、真实状态未知"的 censored 标记年
#   - YEAR年跌出前五 / YEAR/YEAR跌出前五
#   - FY+YEAR起<10%退出表
#   - YEAR归零  (除 E008 外，归零按 censored 处理；E008 在主流程改标 confirmed_ended)
# ---------------------------------------------------------------------------
def parse_censored(text):
    """返回 (year, marker_text) 列表；不重复计数。
    用 seen 集合防止 '2024/2025跌出前五' 被斜杠规则与裸规则重复命中同一年。"""
    cens = []
    seen = set()

    def add(y, marker):
        if y not in seen:
            seen.add(y)
            cens.append((y, marker))

    # YEAR/YEAR年?跌出前五  (含 "2024/2025跌出前五" 与 "2024/2025年跌出前五")
    for m in re.finditer(r'(\d{4})\s*/\s*(\d{4})年?跌出前五', text):
        add(m.group(1), '跌出前五')
        add(m.group(2), '跌出前五')
    # YEAR年跌出前五
    for m in re.finditer(r'(\d{4})年跌出前五', text):
        add(m.group(1), '跌出前五')
    # 裸 YEAR跌出前五 (排除已在上一条含"年"匹配的，靠 seen 去重即可)
    for m in re.finditer(r'(\d{4})跌出前五', text):
        add(m.group(1), '跌出前五')
    # FY+YEAR起<10%[退出表]  (跌破 10% 表，无论是否写"退出表")
    for m in re.finditer(r'FY(\d{4})起\s*<\s*10%', text):
        add(m.group(1), '<10%退出表')
    # YEAR归零 (管制死亡标记；E008 除外在主流程升级为 confirmed_ended)
    for m in re.finditer(r'(\d{4})归零', text):
        add(m.group(1), '归零')
    return cens


# ---------------------------------------------------------------------------
# 解析器：从备注中检测"明示合作起始年" -> confirmed_started
# 本批数据实测无此类表述，返回空；不硬造。
# ---------------------------------------------------------------------------
def parse_confirmed_started(text):
    years = set()
    for m in re.finditer(r'(?:自)?(\d{4})年(?:起|开始|起合作|起供货|合作起始)', text):
        years.add(m.group(1))
    for m in re.finditer(r'起始于(\d{4})', text):
        years.add(m.group(1))
    return years


# ---------------------------------------------------------------------------
# 财年 -> 规范 year 字符串
#   FY2025(至2025-06) -> 2025
#   2019              -> 2019
#   2025-09           -> 2025-09   (保留日期，便于溯源)
#   2023-2025         -> 2023-2025 (区间，程序段落泄漏类)
# ---------------------------------------------------------------------------
def normalize_fy(fy):
    fy = (fy or '').strip()
    m = re.search(r'FY(\d{4})', fy)
    if m:
        return m.group(1)
    return fy


def fy_sort_key(year_str):
    m = re.search(r'(\d{4})', year_str or '')
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# 主处理：单个边 -> 事件列表
# ---------------------------------------------------------------------------
def process_edge(edge, warnings):
    eid = edge['edge_id'].strip()
    sup = edge['供方'].strip()
    dem = edge['需方'].strip()
    fy = edge['财年'].strip()
    pct = edge['占比或金额'].strip()
    note = edge['备注'].strip()

    events = []  # (year, pct_or_amt, is_normal_value:bool, provisional_type:str or None)

    # 1) 占比或金额字段里是否本身藏了序列（如 E038）
    pct_pairs = parse_sequence_pairs(pct)
    note_pairs = parse_sequence_pairs(note)

    # 2) 主观测（财年 + 占比单行值）
    main_year = normalize_fy(fy)
    if pct_pairs:
        # 占比字段已经是序列，主观测年份由序列覆盖，丢弃单行主值以免重复
        pass
    else:
        events.append((main_year, pct, True, None))

    # 3) 序列对（占比 + 备注），按年去重；同一年优先保留序列值（更干净）
    seq_by_year = {}
    for y, v in pct_pairs + note_pairs:
        seq_by_year[y] = v
    for y, v in seq_by_year.items():
        # 若主观测同年已加入，用序列值覆盖
        replaced = False
        for i, ev in enumerate(events):
            if ev[0] == y and ev[2]:  # 同年正常观测
                events[i] = (y, v, True, None)
                replaced = True
                break
        if not replaced:
            events.append((y, v, True, None))

    # 4) censored 标记年
    started_years = parse_confirmed_started(note)
    for y, marker in parse_censored(note):
        if eid == CONFIRMED_ENDED_EDGE and marker == '归零':
            events.append((y, '归零', False, 'confirmed_ended'))
        else:
            events.append((y, marker, False, 'censored'))

    # 5) confirmed_started
    for y in started_years:
        events.append((y, '合作起始年(明示)', False, 'confirmed_started'))

    # 6) 判定 observe_type
    normal_years = [ev[0] for ev in events if ev[2]]
    normal_sorted = sorted(set(normal_years), key=fy_sort_key)
    n_normal = len(normal_sorted)

    for i, ev in enumerate(events):
        y, val, is_normal, prov = ev
        if prov in ('confirmed_ended', 'censored', 'confirmed_started'):
            events[i] = (y, val, is_normal, prov)
            continue
        # 正常占比观测
        if n_normal >= 2:
            if y == normal_sorted[0]:
                typ = 'first_observed'
            elif y == normal_sorted[-1]:
                typ = 'last_observed'
            else:
                typ = 'observed'
        else:
            # 单年观测：不谎称首/尾，仅 observed
            typ = 'observed'
        events[i] = (y, val, is_normal, typ)

    # 7) 解析残差告警：备注中疑似"年份锚定序列"却未被解析的部分
    #    - 年份锚定模式（应已被上面解析，若有残留说明漏解析）
    residual_patterns = [
        r'(?:FY)?\d{4}\s*[:：]\s*[\d.]+%',
        r'\d{4}第[一二三四五六七八九十]+名\s*[\d.]+%',
        r'[\d.]+%\s*\((?:FY)?\d{4}\)',
        r'\d{4}\s*/\s*\d{4}\s*均为0',
        r'\d{4}归零',
        r'\d{4}年?跌出前五',
        r'FY\d{4}起\s*<\s*10%\s*退出表',
    ]
    # 已在上面提取的年份集合
    extracted_years = set(y for y, _, _, _ in events)
    residual_hit = False
    for pat in residual_patterns:
        for m in re.finditer(pat, note):
            # 取该匹配里的 4 位年份
            ym = re.search(r'(\d{4})', m.group(0))
            if ym and ym.group(1) not in extracted_years:
                residual_hit = True
    # 纯数值序列（无年份 token，如 E019 "28.8/43.7/46.6"）
    if ('序列' in note) and re.search(r'[\d.]+\s*/\s*[\d.]+\s*/\s*[\d.]+', note) \
            and len(note_pairs) == 0 and len(pct_pairs) == 0:
        warnings.append(
            f"[{eid}] 备注含纯数值序列(无年份 token)，未硬凑年份展开；"
            f"其年份已由 E017/E018/E019 主行表示: {note}"
        )
    if residual_hit:
        warnings.append(
            f"[{eid}] 备注存在未被解析的年份锚定序列片段，已如实保留未硬凑: {note}"
        )

    # 排序并按最终结构返回
    events.sort(key=lambda e: fy_sort_key(e[0]))
    out = []
    for y, val, is_normal, typ in events:
        out.append({
            'edge_id': eid, '供方': sup, '需方': dem,
            'year': y, 'pct_or_amt': val, 'observe_type': typ,
        })
    return out


# ---------------------------------------------------------------------------
def main():
    warnings = []
    if not os.path.exists(EDGES_CSV):
        sys.exit(f"ERROR: {EDGES_CSV} 不存在")

    with open(EDGES_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    all_events = []
    for edge in rows:
        all_events.extend(process_edge(edge, warnings))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['edge_id', '供方', '需方', 'year', 'pct_or_amt', 'observe_type'])
        for ev in all_events:
            w.writerow([ev['edge_id'], ev['供方'], ev['需方'],
                        ev['year'], ev['pct_or_amt'], ev['observe_type']])

    # ---------------------- 自测打印 ----------------------
    from collections import Counter
    counts = Counter(ev['observe_type'] for ev in all_events)
    print("=" * 64)
    print("Y4 edge_timeline 自测报告")
    print("=" * 64)
    print(f"输入边总数        : {len(rows)}")
    print(f"产出事件总行数    : {len(all_events)}")
    print("-" * 64)
    print("observe_type 计数:")
    for k in ['first_observed', 'observed', 'last_observed',
              'confirmed_started', 'confirmed_ended', 'censored']:
        print(f"  {k:18s}: {counts.get(k, 0)}")
    print(f"  {'（合计）':16s}: {sum(counts.values())}")
    print("-" * 64)
    print("抽取样本展开核对:")
    sample_edges = ['E008', 'E017', 'E018', 'E019', 'E026', 'E027', 'E028']
    for eid in sample_edges:
        sub = [e for e in all_events if e['edge_id'] == eid]
        print(f"\n  [{eid}] {sub[0]['供方']} -> {sub[0]['需方']}  ({len(sub)} 事件)")
        for e in sub:
            print(f"      year={e['year']:>10}  pct_or_amt={e['pct_or_amt']:>14}  -> {e['observe_type']}")
    print("-" * 64)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for wmsg in warnings:
            print("  ! " + wmsg)
    else:
        print("WARNINGS: 无（所有备注序列均已解析或如实标注）")
    print("=" * 64)
    print(f"已写出: {OUT_CSV}")


if __name__ == '__main__':
    main()
