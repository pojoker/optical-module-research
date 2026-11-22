#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2 Shard C — 全量关系时间线(E001–E236 + 设备订单池 + Daily挂接口)
                + 边级负向剔除记忆 + 双侧对账台账 + 卖方验真闹钟
                + refs/解匿判例库.md (#005反面教材 / #004定量门 / #006克制注)

严格写入边界（零触碰其他分片路径）：
  - corpus/relationships/relationship_timeline.csv
  - corpus/relationships/edge_negative_cuts.csv
  - corpus/relationships/counterparty_audit.csv
  - corpus/relationships/sellside_watch_alarms.csv
  - corpus/relationships/README.md
  - refs/解匿判例库.md (原地幂等覆写，绝不新建临时文件，确保 len(os.listdir('refs')) == 8)
  - out/step2-archive-salvage-20261121/shard-c-summary.json
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# 只读输入路径
EDGES_CSV = os.path.join(REPO_ROOT, "edges.csv")
ARCHIVE_REL_TIMELINE = os.path.join(REPO_ROOT, "archive", "flows", "out", "relationship-timeline.csv")
ARCHIVE_EQ_POOL = os.path.join(REPO_ROOT, "archive", "flows", "out", "equipment-watch-pool.csv")
ARCHIVE_CUTS_LEDGER = os.path.join(REPO_ROOT, "archive", "flows", "out", "v16-cuts-ledger.csv")
ARCHIVE_AUDIT_CANDIDATES = os.path.join(REPO_ROOT, "archive", "flows", "out", "counterparty-audit-candidates.csv")
ARCHIVE_ABSENCE_WATCH = os.path.join(REPO_ROOT, "archive", "assets", "registries", "optics", "absence-watch.csv")
ENTITY_REGISTRY_YAML = os.path.join(REPO_ROOT, "refs", "entity-registry.yaml")

# 专属输出路径
REL_DIR = os.path.join(REPO_ROOT, "corpus", "relationships")
OUT_TIMELINE_CSV = os.path.join(REL_DIR, "relationship_timeline.csv")
OUT_CUTS_CSV = os.path.join(REL_DIR, "edge_negative_cuts.csv")
OUT_AUDIT_CSV = os.path.join(REL_DIR, "counterparty_audit.csv")
OUT_ALARMS_CSV = os.path.join(REL_DIR, "sellside_watch_alarms.csv")
OUT_README_MD = os.path.join(REL_DIR, "README.md")
REFS_CASES_MD = os.path.join(REPO_ROOT, "refs", "解匿判例库.md")
OUT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "shard-c-summary.json")

# ---------------------------------------------------------------------------
# 1. 实体归一化与夹层/特殊边常量
# ---------------------------------------------------------------------------
# 保持 E001-E099 R001-R070 关系键兼容，同时修补 E050 苏世博(德国SUSPA)被旧脚本误映射为索恩格(SEG)的问题，
# 并补齐 E100-E236 中已核实同一法人的股改/全简称/解匿归一（严格遵守 refs/entity-registry.yaml 不跨合并/单体硬并）。
ALIAS_MAP = {
    "Fabrinet(解匿)": "Fabrinet",
    "Ciena(解匿)": "Ciena",
    "Google(解匿)": "Google",
    "Corning(解匿)": "Corning Incorporated",
    "中际旭创(作为客户)": "中际旭创",
    "华为+海思": "华为(含海思)",
    "华为": "华为(含海思)",
    "博通(客户)": "博通(Broadcom)",
    "Broadcom": "博通(Broadcom)",
    "NVIDIA(客户)": "NVIDIA",
    "ficonTEC(罗博特科)": "罗博特科/ficonTEC",
    "罗博特科": "罗博特科/ficonTEC",
    "PINEWAVE(关联方)": "PINEWAVE",
    "浙江粮油(出口代理)": "浙江粮油",
    "索尔思(Source Photonics)": "索尔思(Source Photonics)",
    "博创科技股份有限公司": "博创科技",
    "武汉云岭光电有限公司": "武汉云岭光电股份有限公司",
}

EXCEPTION_ANON_CUSTOMER = "集团一(匿名)"

INTERMEDIARY_ENTITIES = {
    "PINEWAVE": "自设新加坡关联销售结算平台(判例#002)，下游终端买家不可见",
    "浙江粮油": "出口代理商(程序段落披露，取得货物出口汇总清单确认收入)，非终端买家",
    "Digicomm": "美国CATV分销商夹层，终端MSO不可见",
    "南央国际": "日本滑台类设备代理商夹层",
    "津微光电": "日本神津精机代理商夹层",
    "讯速信远": "测试设备经销商夹层(成都讯速信远科技等同一控制)",
    "陕西电子信息国际商务有限公司": "进口采购/委托加工商务代理夹层",
    "分销商A(匿名)": "分销渠道夹层(公司整体口径，非DSP专属)",
    "某分销商(匿名)": "半导体解决方案分销商夹层(公司整体口径)",
}


def normalize_entity(name: str) -> str:
    n = (name or "").strip()
    return ALIAS_MAP.get(n, n)


def is_anonymous(name: str) -> bool:
    return "匿名" in (name or "")


# ---------------------------------------------------------------------------
# 2. 期间与排序键（支持 year / half_year / quarter / month / snapshot / fiscal / year_range / event）
# ---------------------------------------------------------------------------
def derive_period_and_type(fy_col: str, raw_period: str):
    """根据边级财年列与拆出期间推导规范 (period, period_type, event_date)。"""
    fy = (fy_col or "").strip()
    p = (raw_period or "").strip()

    if re.match(r"^\d{4}-\d{2}-\d{2}$", p):
        return p, "snapshot", p
    if p.upper().startswith("FY"):
        m = re.match(r"^FY(\d{4})", p.upper())
        return (f"FY{m.group(1)}" if m else p), "fiscal", ""
    if fy.upper().startswith("FY") and re.match(r"^\d{4}$", p):
        return f"FY{p}", "fiscal", ""
    if re.match(r"^\d{4}H[12]$", p.upper()):
        return p.upper(), "half_year", ""
    if re.match(r"^\d{4}Q[1-4]$", p.upper()):
        return p.upper(), "quarter", ""
    if re.match(r"^\d{4}-\d{2}$", p):
        return p, "month", ""
    if re.match(r"^\d{4}-\d{4}$", p):
        return p, "year_range", ""
    return p, "year", ""


def period_sort_key(period: str, ptype: str) -> int:
    """统一折算为期末日整数 YYYYMMDD，确保 2020 < 2021H1 < 2021 < 2022H1 < 2023 < 2024-07-31 < 2024-12-13 < 2024 < 2025Q1 < 2025。"""
    p = (period or "").strip()
    if ptype == "fiscal":
        m = re.match(r"^FY(\d{4})$", p.upper())
        if m:
            return int(m.group(1)) * 10000 + 1231
    elif ptype == "snapshot" or ptype == "event":
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", p)
        if m:
            return int(m.group(1)) * 10000 + int(m.group(2)) * 100 + int(m.group(3))
    elif ptype == "half_year":
        m = re.match(r"^(\d{4})H([12])$", p.upper())
        if m:
            y, h = int(m.group(1)), int(m.group(2))
            return y * 10000 + (630 if h == 1 else 1231)
    elif ptype == "quarter":
        m = re.match(r"^(\d{4})Q([1-4])$", p.upper())
        if m:
            y, q = int(m.group(1)), int(m.group(2))
            mmdd = {1: 331, 2: 630, 3: 930, 4: 1231}[q]
            return y * 10000 + mmdd
    elif ptype == "month":
        m = re.match(r"^(\d{4})-(\d{2})$", p)
        if m:
            return int(m.group(1)) * 10000 + int(m.group(2)) * 100 + 28
    elif ptype == "year_range":
        m = re.match(r"^(\d{4})-(\d{4})$", p)
        if m:
            return int(m.group(2)) * 10000 + 1231
    elif ptype == "year":
        m = re.match(r"^(\d{4})$", p)
        if m:
            return int(m.group(1)) * 10000 + 1231
    return 0


def basis_of(ptype: str) -> str:
    return "fiscal" if ptype == "fiscal" else "calendar"


# ---------------------------------------------------------------------------
# 3. 锚点与证据文件解引用 + 信源渠道/指标类型判定
# ---------------------------------------------------------------------------
def load_edges():
    with open(EDGES_CSV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows, {r["edge_id"].strip(): r for r in rows}


def deref_doc(eid: str, edge_map: dict) -> str:
    doc = (edge_map[eid]["证据文件"] or "").strip()
    m = re.match(r"^同(E\d{3})(.*)$", doc)
    if m and m.group(1) in edge_map:
        return deref_doc(m.group(1), edge_map) + m.group(2)
    return doc


def deref_anchor(eid: str, edge_map: dict) -> str:
    anc = (edge_map[eid]["锚点"] or "").strip()
    if not anc:
        return f"edges.csv#{eid}"
    parts = [p.strip() for p in anc.split(";") if p.strip()]
    resolved = []
    for p in parts:
        m = re.match(r"^同(E\d{3})$", p)
        if m and m.group(1) in edge_map:
            resolved.append(deref_anchor(m.group(1), edge_map))
        elif p.startswith("http://") or p.startswith("https://"):
            resolved.append(p)
        elif "file.finance.qq.com/1222144802.PDF" in p:
            resolved.append(f"edges.csv#{eid};https://file.finance.qq.com/1222144802.PDF")
        else:
            resolved.append(f"edges.csv#{eid}")
    # 去重保序
    flat = []
    for item in resolved:
        for sub in item.split(";"):
            if sub and sub not in flat:
                flat.append(sub)
    return ";".join(flat)


def infer_source_channel(eid: str, period: str, value_raw: str, edge_map: dict) -> str:
    """严格映射历史财报行为 annual_report | prospectus | sec_10k。
    注意：E188/E189/E200（源杰2022-09招股书+2023/2024年报）与 E222（长光华芯2021-10招股书+2023/2025年报）
    跨招股书与上市后年报两类文件，按期间精确区分！"""
    doc = deref_doc(eid, edge_map)
    if "10-K" in doc:
        return "sec_10k"
    if eid in ("E188", "E189", "E200") and period in ("2023", "2024", "2025"):
        return "annual_report"
    if eid == "E222" and period in ("2023", "2024", "2025"):
        return "annual_report"
    if "招股" in doc:
        return "prospectus"
    if "年报" in doc or "年度报告" in doc:
        return "annual_report"
    # E011/E012 为并购重组审核问询文件（注册制申报体系同级归入 prospectus），
    # E013/E014 为早期基线样本，历史基线行统一保持在 {annual_report, prospectus, sec_10k} 受控集内，并在 notes 标明原始载体。
    if eid in ("E011", "E012"):
        return "prospectus"
    return "annual_report"


def is_customer_discloser(edge_row: dict, doc_resolved: str) -> bool:
    """判断该边的披露主体是否为需方（客户披露供应商 -> purchase_share）。"""
    eid = edge_row["edge_id"].strip()
    sup = edge_row["供方"].strip()
    cus = edge_row["需方"].strip()
    if eid == "E038":
        return True  # Lumentum 10-K 披露 Contract Manufacturer A
    if "供应商" in sup:
        return True
    # 对比证据文件名中的发行人简称与供方/需方
    issuer_prefixes = [
        "仕佳光子", "源杰科技", "长光华芯", "博创科技", "华工科技",
        "太辰光", "剑桥科技", "猎奇智能", "联讯仪器", "中际旭创",
        "新易盛", "天孚通信", "光迅科技", "罗博特科", "凯格精机",
        "快克智能", "普源精电", "奥特维", "博众精工",
    ]
    if eid in ("E051", "E052", "E053", "E054"):
        return True  # 猎奇智能招股书供应商表
    for iss in issuer_prefixes:
        if iss in doc_resolved:
            if iss in cus and iss not in sup:
                return True
            if iss in sup and iss not in cus:
                return False
    return False


def parse_metric_fields(eid: str, value_raw: str, is_purchase: bool):
    """从单期 value_raw 解析 (metric_kind, numeric_value_str, unit_str, extra_amount_note)。"""
    v = (value_raw or "").strip()

    if eid == "E016":
        return "intermediary_disclosure", "", "", ""
    if eid == "E146":
        # 2023:100.00%(10,765,805.50元) -> 坏账单项计提100%，核心数值取人民币坏账余额
        m_amt = re.search(r"\(([-+]?[\d,]+(?:\.\d+)?)(万元|万美元|万欧元|元)\)", v)
        if m_amt:
            num = m_amt.group(1).replace(",", "")
            return "bad_debt_writeoff", num, m_amt.group(2), "单项计提比例100.00%"
        return "bad_debt_writeoff", "100.00", "%", ""
    if eid == "E044":
        return "amount_usd", "43378", "万美元", ""
    if "在手订单" in v:
        m_ob = re.search(r"([\d,]+(?:\.\d+)?)\s*(万欧元|万美元|万元|元)", v)
        if m_ob:
            return "order_backlog", m_ob.group(1).replace(",", ""), m_ob.group(2), ""
    if eid == "E011":
        return "order_backlog", "14", "台", "已交付14台CPO耦合设备(设备交付实绩)"
    if eid == "E013":
        return "amount_rmb", "815", "万元", "中标公示金额"
    if eid == "E014":
        return "order_backlog", "", "", "800G/1.6T组装产线交付(未披露金额，条数3条vs2条待核)"

    # 截尾/归零特殊文本
    if v == "归零":
        mk = "purchase_share" if is_purchase else "sales_share"
        return mk, "0", "%", ""
    if v in ("跌出前五", "<10%退出表", "<10%"):
        mk = "purchase_share" if is_purchase else "sales_share"
        unit = "%" if "10%" in v else ""
        return mk, "", unit, "低于披露阈值右截尾(禁止当成0)"

    # 检查是否同时含百分比与括号金额，例如:
    #   3.35%(1,112.70万元)
    #   12.51%（占境外主营业务收入）(169.33万元)
    #   20.13%(97,071.67(万元))
    #   5.61%（占收入）；33.03%（占境外主营业务收入）(3,063.70万元)
    m_amt_nested = re.search(r"\(([-+]?[\d,]+(?:\.\d+)?)\(?((?:万元|万美元|万欧元|元))\)?\)", v)
    amt_note = ""
    if m_amt_nested:
        amt_val = m_amt_nested.group(1).replace(",", "")
        amt_unit = m_amt_nested.group(2)
        amt_note = f"同源披露金额={amt_val}{amt_unit}"

    # 若以“未单列”开头 -> 主指标为金额！
    if v.startswith("未单列"):
        if m_amt_nested:
            mk = "amount_usd" if m_amt_nested.group(2) == "万美元" else "amount_rmb"
            return mk, m_amt_nested.group(1).replace(",", ""), m_amt_nested.group(2), "占比原表未单列"
        return "amount_rmb", "", "", "占比未单列"

    # 若含百分比（含“约40%”）
    m_pct = re.search(r"(?:约)?([\d.]+)\s*%", v)
    if m_pct and not v.startswith("("):
        mk = "purchase_share" if is_purchase else "sales_share"
        approx_note = "近似值(原文约)" if "约" in v.split("%")[0] else ""
        extra = "; ".join(x for x in [amt_note, approx_note] if x)
        return mk, m_pct.group(1), "%", extra

    # 纯括号金额或纯金额，如 (3,405,309.69元)
    if m_amt_nested:
        u = m_amt_nested.group(2)
        mk = "amount_usd" if u == "万美元" else "amount_rmb"
        return mk, m_amt_nested.group(1).replace(",", ""), u, ""

    m_plain_amt = re.search(r"([-+]?[\d,]+(?:\.\d+)?)\s*(万元|万美元|万欧元|元)", v)
    if m_plain_amt:
        u = m_plain_amt.group(2)
        mk = "amount_usd" if u == "万美元" else "amount_rmb"
        return mk, m_plain_amt.group(1).replace(",", ""), u, ""

    return ("purchase_share" if is_purchase else "sales_share"), "", "", ""


# ---------------------------------------------------------------------------
# 4. 拆解 E001–E099（对齐 relationship-timeline.csv 基线并补齐完整金额/备注）
#    与 E100–E236（无损拆解全部打包多期/同表分项/跨表序列）
# ---------------------------------------------------------------------------
def unpack_e001_e099(edges_099: list, edge_map: dict):
    """以 archive/flows/out/relationship-timeline.csv (70对145行) 为精确基线，
    结合当前 Step 1 修复后的 edges.csv E001–E099 补齐完整原文字段（如 E045 2025 万元额、
    E060 2024 元额、E044 客户E人民币额对齐、E050 苏世博正名、E012 两期在手订单快照对接）。"""
    with open(ARCHIVE_REL_TIMELINE, encoding="utf-8-sig", newline="") as f:
        baseline_rows = list(csv.DictReader(f))

    enriched_events = []
    for r in baseline_rows:
        rid = r["relation_id"].strip()
        sup = r["供方"].strip()
        cus = r["需方"].strip()
        period = r["period"].strip()
        ptype = r["period_type"].strip()
        val_raw = r["pct_or_amt"].strip()
        obs_type = r["observe_type"].strip()
        eids = [x.strip() for x in r["source_edge_ids"].split(";") if x.strip()]
        conflict = r["conflict"].strip().lower() == "true"

        primary_eid = eids[0]
        erow = edge_map[primary_eid]

        # 修复旧脚本将 E050 "苏世博"(德国SUSPA) 误映射成 "索恩格(SEG Automotive)" 的历史笔误，保持 R056 槽位不变
        extra_notes = []
        if primary_eid == "E050" and cus == "索恩格(SEG Automotive)":
            cus = "苏世博"
            extra_notes.append("正名:招股书释义苏世博=苏世博(南京)减振系统有限公司(德国SUSPA在华全资子)，修旧版误映射索恩格SEG")

        # E012 在基线中为单行 2024 在手订单2433.83万欧元(至2024-07-31)：
        # 此处直接升级为精确快照 2024-07-31 (对接 FT-OB-20240731)，避免与观察池重复计行！
        event_date = ""
        if primary_eid == "E012":
            period = "2024-07-31"
            ptype = "snapshot"
            event_date = "2024-07-31"
            obs_type = "first_observed"
            extra_notes.append("eq_watch_series_id=FT-OB-20240731; 时点快照(非订单签署日序列); 观察池警示:不同口径不可直接横向比较")

        # 补齐旧脚本因正则只抓百分比而丢掉的同源括号金额
        if primary_eid == "E045" and period == "2025":
            val_raw = erow["占比或金额原文"].strip()  # 53.42%(37277.97万元)
        elif primary_eid == "E060" and period == "2024":
            val_raw = "31.74%(2744287306.63元)"

        # 特殊生命周期/性质标签升级
        if primary_eid == "E016":
            obs_type = "procedural_intermediary"
            ptype = "year_range"
            extra_notes.append("程序段落披露:取得货物出口汇总清单时确认收入; 严禁当成终端供货边")
        elif primary_eid == "E008" and obs_type == "confirmed_ended":
            extra_notes.append("2019-05美国BIS实体清单管制后逐步终止供货，2021归零确认终结")

        # E044 强制对齐 43,378万美元 与 客户E 3,096,780,769.22元(8.10%)
        if primary_eid == "E044":
            extra_notes.append(
                "2025年报双重锚定:重大关联交易表向PINEWAVE销售43,378万美元(占同类交易100%，第3937行，折合3,097,151,244.97元) "
                "↔ 前五大客户表客户E=3,096,780,769.22元(占年度销售总额8.10%，第1265行，差37.05万元系服务/口径微差，判例#002 A级)"
            )

        # R012 双侧分母差异说明
        if rid == "R012" and conflict:
            if primary_eid == "E038":
                extra_notes.append("Lumentum侧披露占total net inventory purchases比例(判例#004 B级终态); 与E068分母口径不同")
            elif primary_eid == "E068":
                extra_notes.append("Fabrinet侧披露占Fabrinet总收入比例($407.4M); 与E038分母口径不同")

        if primary_eid == "E013":
            extra_notes.append("原始载体=中标公示(聚变域边界外Schema参考样本)")
        elif primary_eid == "E014":
            extra_notes.append("原始载体=互动平台回应(未点名)+财联社转述(半边待核)")

        doc_resolved = deref_doc(primary_eid, edge_map)
        is_purch = is_customer_discloser(erow, doc_resolved)
        mk, num_val, unit, amt_note = parse_metric_fields(primary_eid, val_raw, is_purch)
        if amt_note:
            extra_notes.append(amt_note)

        # 夹层警示
        for ent in (sup, cus):
            if ent in INTERMEDIARY_ENTITIES and primary_eid != "E016":
                extra_notes.append(f"intermediary_layer:{INTERMEDIARY_ENTITIES[ent]}")

        anchors = []
        for eid in eids:
            a = deref_anchor(eid, edge_map)
            if a and a not in anchors:
                anchors.append(a)

        enriched_events.append({
            "relation_id": rid,
            "supplier": sup,
            "customer": cus,
            "supplier_point_id": erow["供方point_id"].strip(),
            "customer_point_id": erow["需方point_id"].strip(),
            "period": period,
            "period_type": ptype,
            "event_date": event_date,
            "source_channel": infer_source_channel(primary_eid, period, val_raw, edge_map),
            "metric_kind": mk,
            "value_raw": val_raw,
            "numeric_value": num_val,
            "unit": unit,
            "observe_type": obs_type,
            "edge_grade": erow["边等级"].strip(),
            "source_edge_ids": ";".join(eids),
            "daily_ref_id": "",
            "anchor_url": ";".join(anchors),
            "conflict": conflict,
            "notes": "; ".join(extra_notes),
        })

    return enriched_events


def split_top_level_segments(raw_str: str):
    """在括号深度 0 处按 '/' 或 '|' 切分顶层片段，保留分隔符语义（'|' 同年并列分项，'/' 跨期或跨表序列）。"""
    segs = []
    buf = []
    depth = 0
    prev_sep = ""
    for ch in raw_str:
        if ch in "（(":
            depth += 1
            buf.append(ch)
        elif ch in "）)":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch in "/|" and depth == 0:
            segs.append(("".join(buf).strip(), prev_sep))
            prev_sep = ch
            buf = []
        else:
            buf.append(ch)
    if buf:
        segs.append(("".join(buf).strip(), prev_sep))
    return segs


def unpack_single_v16_edge(edge_row: dict, edge_map: dict):
    """无损拆解单条 E100–E236 边为单期原子事件列表。"""
    eid = edge_row["edge_id"].strip()
    raw_sup = edge_row["供方"].strip()
    raw_cus = edge_row["需方"].strip()
    sup = normalize_entity(raw_sup)
    cus = normalize_entity(raw_cus)
    fy_col = edge_row["财年"].strip()
    raw_str = edge_row["占比或金额原文"].strip()
    note_col = edge_row["备注"].strip()
    doc_resolved = deref_doc(eid, edge_map)
    is_purch = is_customer_discloser(edge_row, doc_resolved)
    anchor_resolved = deref_anchor(eid, edge_map)

    # 提取章节线索（用于多表/同表分项说明）
    sec_parts = []
    for part in note_col.split(";"):
        pt = part.strip()
        if pt and not pt.startswith("v1.6") and not pt.startswith("单位继承") and "多期打包" not in pt and not pt.startswith("codex复核") and not pt.startswith("scope="):
            sec_parts.append(pt)
    scope_notes = [pt.strip() for pt in note_col.split(";") if pt.strip().startswith("scope=")]

    segs = split_top_level_segments(raw_str)
    raw_items = []
    for seg_idx, (seg_text, sep_before) in enumerate(segs):
        m = re.match(r"^([^:：]+)[:：](.+)$", seg_text)
        if not m:
            raise ValueError(f"[{eid}] 无法解析片段: {seg_text!r}")
        p_part, v_part = m.group(1).strip(), m.group(2).strip()
        periods = [p.strip() for p in p_part.split("；") if p.strip()]
        if len(periods) == 1:
            raw_items.append((periods[0], v_part, seg_idx, sep_before))
        else:
            m2 = re.match(r"^([^（(]*?)(?:（([^）]+)）)?\(([^()]+?)(万元|万美元|万欧元|元)\)$", v_part)
            if not m2:
                raise ValueError(f"[{eid}] 多期片段格式异常: {v_part!r}")
            pct_part, basis_note, amt_part, unit = (
                m2.group(1).strip(),
                m2.group(2),
                m2.group(3).strip(),
                m2.group(4),
            )
            pcts = [x.strip() for x in pct_part.split("；")]
            amts = [x.strip() for x in amt_part.split("；")]
            if len(pcts) != len(periods) or len(amts) != len(periods):
                raise ValueError(f"[{eid}] 期数与数值个数不一致: {periods} vs {pcts} vs {amts}")
            for p_i, pct_i, amt_i in zip(periods, pcts, amts):
                basis_str = f"（{basis_note}）" if basis_note else ""
                item_raw = f"{pct_i}{basis_str}({amt_i}{unit})"
                raw_items.append((p_i, item_raw, seg_idx, sep_before))

    # 识别同边同期完全同额的“前五大表 + 经常性关联交易表”重复列示（如 E222 2021H1=1,181.58万元、E229 2018/2019/2021H1）
    # 合并保留含占比的完整行，并在 notes 标注双表同额互验，防止同一笔金额翻倍！
    by_period = defaultdict(list)
    for p_i, v_i, seg_idx, sep_before in raw_items:
        by_period[p_i].append((v_i, seg_idx, sep_before))

    events = []
    for p_i, item_list in by_period.items():
        period, ptype, ev_date = derive_period_and_type(fy_col, p_i)

        # 检查是否恰好 2 条且括号内金额+单位逐字完全相等、一条有%一条为“未单列”
        if len(item_list) == 2:
            v0, _, _ = item_list[0]
            v1, _, _ = item_list[1]
            m0 = re.search(r"\(([-+]?[\d,]+(?:\.\d+)?(?:万元|元))\)", v0)
            m1 = re.search(r"\(([-+]?[\d,]+(?:\.\d+)?(?:万元|元))\)", v1)
            if m0 and m1 and m0.group(1) == m1.group(1) and ("未单列" in v1 and "%" in v0):
                item_list = [(v0, item_list[0][1], "merged_same_amt")]

        # 判断同边同期多条是“跨口径冲突(前五大合并 vs 关联交易单体/净额)”还是“同表并列分项(购销 vs 劳务/租赁/委外)”
        is_same_period_conflict = False
        if len(item_list) > 1 and eid in ("E154", "E163", "E184", "E190"):
            is_same_period_conflict = True

        for sub_pos, (v_i, seg_idx, sep_tag) in enumerate(item_list, start=1):
            mk, num_val, unit, amt_note = parse_metric_fields(eid, v_i, is_purch)
            notes = []
            if raw_sup != sup:
                notes.append(f"原供方披露名={raw_sup}")
            if raw_cus != cus:
                notes.append(f"原需方披露名={raw_cus}")
            if scope_notes:
                notes.extend(scope_notes)
            if amt_note:
                notes.append(amt_note)
            if sep_tag == "merged_same_amt":
                notes.append("前五大客户表与经常性关联交易表同额互验合并")
            elif len(item_list) > 1:
                if is_same_period_conflict:
                    notes.append(f"同边同期跨表口径差异(第{sub_pos}/{len(item_list)}项: 前五大合并表 vs 关联交易表)")
                elif eid in ("E137", "E138", "E139", "E140", "E142") and sub_pos == 2:
                    notes.append("同表分项2/2: 关联租赁情况(出租/承租，非商品购销)")
                elif eid == "E199":
                    tbl = "前五大委托加工" if sub_pos == 2 else "前五大供应商"
                    notes.append(f"同招股书双表并行分项({sub_pos}/2: {tbl})")
                else:
                    notes.append(f"关联交易同表并行分项({sub_pos}/{len(item_list)}: 商品/劳务或细分主体行)")

            if eid == "E146":
                notes.append("应收账款按单项100%计提坏账准备期末余额(非当期供货交易，跨年微差系外币折算)，Kaiam破产冻结")
            if eid in ("E233", "E234", "E235", "E236"):
                notes.append("公司整体客户集中度口径(非DSP专属槽位)")

            for ent in (sup, cus):
                if ent in INTERMEDIARY_ENTITIES:
                    notes.append(f"intermediary_layer:{INTERMEDIARY_ENTITIES[ent]}")

            events.append({
                "edge_id": eid,
                "supplier": sup,
                "customer": cus,
                "supplier_point_id": edge_row["供方point_id"].strip(),
                "customer_point_id": edge_row["需方point_id"].strip(),
                "period": period,
                "period_type": ptype,
                "event_date": ev_date,
                "source_channel": infer_source_channel(eid, period, v_i, edge_map),
                "metric_kind": mk,
                "value_raw": v_i,
                "numeric_value": num_val,
                "unit": unit,
                "observe_type": "bad_debt_frozen" if eid == "E146" else "pending",
                "edge_grade": edge_row["边等级"].strip(),
                "source_edge_ids": eid,
                "daily_ref_id": "",
                "anchor_url": anchor_resolved,
                "conflict": is_same_period_conflict,
                "notes": "; ".join(dict.fromkeys(n for n in notes if n)),
            })
    return events


def assign_lifecycle_states(rel_events: list, is_anon_independent: bool):
    """在关系级别按 (calendar | fiscal) 序列重算 first_observed / observed / last_observed，
    严格保护 confirmed_ended / procedural_intermediary / bad_debt_frozen / censored 不被覆盖。"""
    SPECIAL_FIXED = {"confirmed_ended", "procedural_intermediary", "bad_debt_frozen", "censored"}
    if is_anon_independent:
        for ev in rel_events:
            if ev["observe_type"] not in SPECIAL_FIXED:
                ev["observe_type"] = "observed"
        return

    # 按财年基准分组计算正常活跃观测首尾期
    by_basis = defaultdict(list)
    for ev in rel_events:
        if ev["observe_type"] not in SPECIAL_FIXED:
            by_basis[basis_of(ev["period_type"])].append(ev)

    for b, evs in by_basis.items():
        distinct_periods = sorted(
            {ev["period"] for ev in evs},
            key=lambda p: (
                period_sort_key(p, next(x["period_type"] for x in evs if x["period"] == p)),
                p,
            ),
        )
        # 检查同一基准内是否还存在更晚的 confirmed_ended / censored 期（例如 E008 2017..2020 + 2021归零 confirmed_ended，
        # 或 E048 2024 observed + 2025 跌出前五 censored）
        all_basis_evs = [e for e in rel_events if basis_of(e["period_type"]) == b]
        max_all_sort = max(period_sort_key(e["period"], e["period_type"]) for e in all_basis_evs)
        min_all_sort = min(period_sort_key(e["period"], e["period_type"]) for e in all_basis_evs)

        if len(distinct_periods) == 1 and len(all_basis_evs) == len(evs):
            # 单期活跃观测（含同年双分项如 E115/E139/E224）：若原基线已赋态则保持，新增边一律标 observed（不虚构跨期首尾）
            for ev0 in evs:
                if ev0["observe_type"] == "pending":
                    ev0["observe_type"] = "observed"
            continue

        first_p = distinct_periods[0]
        last_p = distinct_periods[-1]
        last_p_sort = period_sort_key(last_p, next(x["period_type"] for x in evs if x["period"] == last_p))
        first_p_sort = period_sort_key(first_p, next(x["period_type"] for x in evs if x["period"] == first_p))

        for ev in evs:
            p = ev["period"]
            if p == first_p and first_p_sort <= min_all_sort:
                ev["observe_type"] = "first_observed"
            elif p == last_p and last_p_sort >= max_all_sort:
                ev["observe_type"] = "last_observed"
            else:
                ev["observe_type"] = "observed"


# ---------------------------------------------------------------------------
# 5. 清洗并并入 equipment-watch-pool.csv (跳过第1行#注释后25行)
# ---------------------------------------------------------------------------
def parse_equipment_watch_pool():
    with open(ARCHIVE_EQ_POOL, encoding="utf-8-sig") as f:
        clean_lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    return list(csv.DictReader(clean_lines))


def canonicalize_eq_anchor(raw_anchor: str, supplier: str) -> str:
    """将 flows/out/...、flows/input/...、assets/... 规范改写为 edges.csv#E### 或 corpus/legacy-input/*.txt。"""
    parts = [p.strip() for p in (raw_anchor or "").split(";") if p.strip()]
    out = []
    for p in parts:
        m_e = re.match(r"^(E\d{3})", p)
        if m_e:
            tag = f"edges.csv#{m_e.group(1)}"
            if tag not in out:
                out.append(tag)
        elif "lianxun" in p:
            tag = "corpus/legacy-input/lianxun_prospectus.txt"
            if tag not in out:
                out.append(tag)
        elif "lieqi" in p:
            tag = "corpus/legacy-input/lieqi_prospectus.txt"
            if tag not in out:
                out.append(tag)
        elif "assets/registries/optics" in p:
            # 均已由 E012 承载
            if "edges.csv#E012" not in out:
                out.append("edges.csv#E012")
    if not out:
        if "联讯" in supplier:
            out.append("corpus/legacy-input/lianxun_prospectus.txt")
        elif "猎奇" in supplier:
            out.append("corpus/legacy-input/lieqi_prospectus.txt")
    return ";".join(out)


def integrate_equipment_pool(all_rel_map: dict, edge_map: dict):
    """处理 equipment-watch-pool.csv 全部 25 行：
    - 13 条已在 edges.csv 同边同期完整包含(占比+万元)的确认收入行：在对应时间线行 notes 标注 eq_watch_series_id，零重复计行；
    - 1 条 FT-OB-20240731 (2433.83万欧元)：已在 unpack_e001_e099 中与 E012 主行精准合流为 2024-07-31 快照行；
    - 1 条 FT-OB-20241213 (4800万欧元，原仅藏于 E012 备注)：作为 2024-12-13 在手订单快照补充行正式并入 R057；
    - 10 条 edges.csv 完全未单列数值的观测（LX-GX-2025Q1、LX-XSXY-2022 两条未入前五边 + LQ-ZX-2023/2024 及联讯 2023/2024 6条缺人民币额行）：
      作为补充观测行正式并入对应 relation_id！
    返回统计字典。"""
    eq_rows = parse_equipment_watch_pool()
    assert len(eq_rows) == 25, f"equipment-watch-pool 有效数据行应为25，实测={len(eq_rows)}"

    target_map = {
        "对NVIDIA在手订单余额": "NVIDIA",
        "对集团一销售收入": "集团一(匿名)",
        "对Power Master销售收入": "Power Master",
        "对新易盛销售收入": "新易盛",
        "对讯速信远销售收入": "讯速信远",
        "对光迅科技销售收入": "光迅科技",
        "对士兰微销售收入": "士兰微",
        "对海信集团销售收入": "海信集团",
        "对中际旭创销售收入": "中际旭创",
        "对三安光电销售收入": "三安光电",
        "对集团二销售收入": "集团二(匿名)",
        "对Broadcom销售收入": "博通(Broadcom)",
    }

    linked_existing = []
    added_rows = []

    for r in eq_rows:
        sid = r["series_id"].strip()
        sup = normalize_entity(r["主体"].strip())
        cus = target_map[r["指标名"].strip()]
        period_raw = r["期间"].strip()
        val_num = r["数值"].strip()
        unit = r["单位"].strip()
        clean_anchor = canonicalize_eq_anchor(r["证据锚点"], sup)
        orig_note = r["备注"].strip()

        # 查找对应关系桶
        matched_rel = None
        for rel in all_rel_map.values():
            if rel["supplier"] == sup and rel["customer"] == cus:
                matched_rel = rel
                break
        assert matched_rel is not None, f"未找到观察池 {sid} 对应的关系桶 ({sup} -> {cus})"

        # FT-OB-20240731 已与 E012 2024-07-31 主行合流
        if sid == "FT-OB-20240731":
            for ev in matched_rel["events"]:
                if ev["period"] == "2024-07-31":
                    ev["anchor_url"] = clean_anchor
            linked_existing.append(sid)
            continue

        # 检查是否已有同期间且 value_raw 已含该金额数值的行（13条已覆盖行）
        existing_hit = None
        for ev in matched_rel["events"]:
            if ev["period"] == period_raw and val_num in ev["value_raw"].replace(",", ""):
                existing_hit = ev
                break

        if existing_hit is not None:
            tag = f"eq_watch_series_id={sid}"
            if tag not in existing_hit["notes"]:
                existing_hit["notes"] = "; ".join(x for x in [existing_hit["notes"], tag] if x)
            linked_existing.append(sid)
            continue

        # 其余 11 条（FT-OB-20241213 + 10 条 edges.csv 缺失数值）正式并入时间线！
        m_eids = re.findall(r"E\d{3}", r["证据锚点"] or "")
        eids_str = ";".join(dict.fromkeys(m_eids))

        # 继承同关系已有端点 point_id
        sup_pid = next((e["supplier_point_id"] for e in matched_rel["events"] if e["supplier_point_id"]), "")
        cus_pid = next((e["customer_point_id"] for e in matched_rel["events"] if e["customer_point_id"]), "")
        grade = next((e["edge_grade"] for e in matched_rel["events"] if e["edge_grade"]), "实边")

        if sid == "FT-OB-20241213":
            period, ptype, ev_date = "2024-12-13", "snapshot", "2024-12-13"
            mk = "order_backlog"
            val_raw = f"在手订单{val_num}{unit}(至2024-12-13)"
            src_ch = "prospectus"
            note_txt = (
                f"eq_watch_series_id={sid}; E012备注升级(超50台/在手4800万欧元); {orig_note}; "
                "观察池警示:不同口径不可直接横向比较"
            )
        else:
            period, ptype, ev_date = derive_period_and_type("", period_raw)
            mk = "amount_rmb"
            # 提取备注里的占比提示（如 占比4.31%）保留在 value_raw 或 notes
            m_pct_hint = re.search(r"占比([\d.]+%)", orig_note)
            if not eids_str and m_pct_hint:
                # LX-GX-2025Q1 / LX-XSXY-2022 为招股书披露但未入当期前五主边集的完整补充观测
                val_raw = f"{val_num}{unit}(占比{m_pct_hint.group(1)})"
                note_txt = f"eq_watch_series_id={sid}; {orig_note}; 招股书原文补充观测(edges.csv未单列)"
            else:
                # 同边同期在 edges.csv 仅录入了占比%，此处补齐招股书披露的精确人民币确认收入额
                val_raw = f"{val_num}{unit}"
                note_txt = (
                    f"eq_watch_series_id={sid}; {orig_note}; "
                    f"补充同边({eids_str})同期缺失人民币额(与同边sales_share占比行同源互补，勿重复计次)"
                )
            if cus in INTERMEDIARY_ENTITIES:
                note_txt += f"; intermediary_layer:{INTERMEDIARY_ENTITIES[cus]}"
            src_ch = "prospectus"

        matched_rel["events"].append({
            "relation_id": matched_rel["relation_id"],
            "supplier": sup,
            "customer": cus,
            "supplier_point_id": sup_pid,
            "customer_point_id": cus_pid,
            "period": period,
            "period_type": ptype,
            "event_date": ev_date,
            "source_channel": src_ch,
            "metric_kind": mk,
            "value_raw": val_raw,
            "numeric_value": val_num,
            "unit": unit,
            "observe_type": "pending",
            "edge_grade": grade,
            "source_edge_ids": eids_str,
            "daily_ref_id": "",
            "anchor_url": clean_anchor,
            "conflict": False,
            "notes": note_txt,
        })
        added_rows.append(sid)

    return {
        "total_eq_pool_rows": len(eq_rows),
        "linked_existing_count": len(linked_existing),
        "linked_existing_ids": linked_existing,
        "added_supplementary_count": len(added_rows),
        "added_supplementary_ids": added_rows,
    }


def build_relationship_timeline():
    edges, edge_map = load_edges()
    assert len(edges) == 236, f"edges.csv 应为236行，实测={len(edges)}"

    # 1) 加载并升级 E001-E099 基线 (R001-R070)
    e099_events = unpack_e001_e099(edges[:99], edge_map)
    rel_buckets = {}
    for ev in e099_events:
        rid = ev["relation_id"]
        if rid not in rel_buckets:
            sup, cus = ev["supplier"], ev["customer"]
            is_anon_ind = (is_anonymous(sup) or is_anonymous(cus)) and (cus != EXCEPTION_ANON_CUSTOMER)
            rel_buckets[rid] = {
                "relation_id": rid,
                "supplier": sup,
                "customer": cus,
                "anon_independent": is_anon_ind,
                "events": [],
            }
        rel_buckets[rid]["events"].append(ev)

    # 传播同关系内已知 point_id（如 罗博特科/ficonTEC E076 有 P059、博通 E094 有 P020）
    entity_point_hint = {}
    for e in edges:
        s_norm = normalize_entity(e["供方"])
        c_norm = normalize_entity(e["需方"])
        sp = e["供方point_id"].strip()
        cp = e["需方point_id"].strip()
        if sp.startswith("P") and s_norm in ("罗博特科/ficonTEC", "博通(Broadcom)", "光迅科技", "联讯仪器", "猎奇智能", "天孚通信", "Fabrinet", "仕佳光子", "源杰科技", "长光华芯", "太辰光", "Marvell", "武汉云岭光电股份有限公司"):
            entity_point_hint[s_norm] = sp
        if cp.startswith("P") and c_norm in ("罗博特科/ficonTEC", "博通(Broadcom)", "光迅科技", "联讯仪器", "猎奇智能", "天孚通信", "Fabrinet", "仕佳光子", "源杰科技", "长光华芯", "太辰光", "Marvell", "武汉云岭光电股份有限公司"):
            entity_point_hint[c_norm] = cp

    # 2) 拆解全部 E100-E236 (137条边)
    e100_unpacked_raw_count = 0
    new_rel_groups = defaultdict(list)
    for erow in edges[99:]:
        evs = unpack_single_v16_edge(erow, edge_map)
        e100_unpacked_raw_count += len(evs)
        for ev in evs:
            sup, cus = ev["supplier"], ev["customer"]
            is_anon_ind = (is_anonymous(sup) or is_anonymous(cus)) and (cus != EXCEPTION_ANON_CUSTOMER)
            key = (sup, cus, ev["edge_id"] if is_anon_ind else "")
            new_rel_groups[key].append((ev, is_anon_ind))

    next_r_num = 71
    for key in sorted(new_rel_groups.keys()):
        rid = f"R{next_r_num:03d}"
        next_r_num += 1
        items = new_rel_groups[key]
        is_anon_ind = items[0][1]
        evs = []
        for ev, _ in items:
            ev["relation_id"] = rid
            evs.append(ev)
        # 检查跨边同关系同期间合并/冲突（如 E165+E232 为 2024+2025 不同期；E137+E138 为 2023+2024/2025 不同期；E141+E142 为 2023+2024/2025 不同期）
        rel_buckets[rid] = {
            "relation_id": rid,
            "supplier": key[0],
            "customer": key[1],
            "anon_independent": is_anon_ind,
            "events": evs,
        }

    # 3) 并入 equipment-watch-pool.csv 25 行
    eq_stats = integrate_equipment_pool(rel_buckets, edge_map)

    # 4) 补齐同实体唯一明确 point_id（仅限单点映射清晰主体，不篡改 EXT/ANON）并重算关系生命周期状态与时间排序
    final_rows = []
    for rid in sorted(rel_buckets.keys(), key=lambda x: int(x[1:])):
        rel = rel_buckets[rid]
        evs = rel["events"]
        for ev in evs:
            if not ev["supplier_point_id"] and ev["supplier"] in entity_point_hint:
                ev["supplier_point_id"] = entity_point_hint[ev["supplier"]]
            if not ev["customer_point_id"] and ev["customer"] in entity_point_hint:
                ev["customer_point_id"] = entity_point_hint[ev["customer"]]

        assign_lifecycle_states(evs, rel["anon_independent"])
        # 关系内稳定排序：先按财年基准(calendar vs fiscal)，再按期末日整数键，再按 metric_kind (占比先于补充金额)
        mk_rank = {
            "sales_share": 0,
            "purchase_share": 0,
            "amount_usd": 1,
            "amount_rmb": 2,
            "order_backlog": 3,
            "intermediary_disclosure": 4,
            "bad_debt_writeoff": 5,
        }
        evs.sort(
            key=lambda x: (
                0 if basis_of(x["period_type"]) == "calendar" else 1,
                period_sort_key(x["period"], x["period_type"]),
                x["period"],
                mk_rank.get(x["metric_kind"], 9),
                x["source_edge_ids"],
            )
        )
        final_rows.extend(evs)

    # 5) 赋唯一 timeline_id 并写出 UTF-8 CSV
    os.makedirs(REL_DIR, exist_ok=True)
    fieldnames = [
        "timeline_id", "relation_id", "supplier", "customer",
        "supplier_point_id", "customer_point_id", "period", "period_type",
        "event_date", "source_channel", "metric_kind", "value_raw",
        "numeric_value", "unit", "observe_type", "edge_grade",
        "source_edge_ids", "daily_ref_id", "anchor_url", "conflict", "notes",
    ]
    with open(OUT_TIMELINE_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for idx, row in enumerate(final_rows, start=1):
            out_row = {"timeline_id": f"TL{idx:04d}"}
            for k in fieldnames[1:]:
                if k == "conflict":
                    out_row[k] = "true" if row[k] else "false"
                else:
                    out_row[k] = row[k]
            w.writerow(out_row)

    return final_rows, rel_buckets, e100_unpacked_raw_count, eq_stats


# ---------------------------------------------------------------------------
# 6. 边级负向剔除记忆表 edge_negative_cuts.csv（74行 + 0泄漏程序化核验）
# ---------------------------------------------------------------------------
def build_edge_negative_cuts():
    edges, _ = load_edges()
    with open(ARCHIVE_CUTS_LEDGER, encoding="utf-8-sig", newline="") as f:
        raw_cuts = list(csv.DictReader(f))
    assert len(raw_cuts) == 74, f"v16-cuts-ledger.csv 应为74行，实测={len(raw_cuts)}"

    exact_edge_pairs_undir = set()
    exact_edge_pairs_dir = set()
    for e in edges:
        s, c = e["供方"].strip(), e["需方"].strip()
        exact_edge_pairs_dir.add((s, c))
        exact_edge_pairs_undir.add((s, c))
        exact_edge_pairs_undir.add((c, s))

    cat_map = {
        "长飞系个体行,由合并边承载": "consolidated_into_group_edge",
        "非供货方向": "non_supply_relation",
        "华工非光链关联方/坏账": "non_optical_related_or_bad_debt",
        "非光链主体": "non_optical_counterparty",
    }

    seen_first = {}
    out_rows = []
    leak_count = 0

    for idx, r in enumerate(raw_cuts, start=1):
        cid = f"CUT{idx:03d}"
        comp = r["公司"].strip()
        cp_raw = r["对手方"].strip()
        cp_norm = re.sub(r"\s+", " ", cp_raw).strip()
        direction = r["方向"].strip()
        rule = r["剔除规则"].strip()
        category = cat_map.get(rule, "other")

        # 推导隐含供需方向（若为股权/担保/子公司则标记非供货）
        if "采购" in direction or direction.startswith("供应商"):
            imp_sup, imp_cus = cp_norm, comp
        elif "销售" in direction or direction == "客户":
            imp_sup, imp_cus = comp, cp_norm
        else:
            imp_sup, imp_cus = "", ""

        # 承载合并边指引
        repl_edges = ""
        if category == "consolidated_into_group_edge":
            repl_edges = "E163" if imp_cus == "博创科技" else "E154"

        dedupe_key = (comp, cp_norm.lower(), direction)
        dup_of = seen_first.get(dedupe_key, "")
        if not dup_of:
            seen_first[dedupe_key] = cid

        # 程序化核验是否泄漏进当前 edges.csv
        is_leaked = (comp, cp_raw) in exact_edge_pairs_undir or (comp, cp_norm) in exact_edge_pairs_undir
        if is_leaked:
            leak_count += 1

        v_note = "edges.csv零泄漏核验通过"
        if comp == "源杰科技" and "中际旭创" in cp_norm:
            v_note += "; 注:E184为源杰→中际旭创商品销售实边，本条仅剔除'间接持股5%以上股东'非供货股权边(零股权边泄漏)"
        elif repl_edges:
            v_note += f"; 个体子公司行已由合并口径边 {repl_edges} 统一承载，防重扫双计"
        elif "房屋租赁" in direction:
            v_note += "; 房产出租方非BOM供应链主体"

        out_rows.append({
            "cut_id": cid,
            "company": comp,
            "counterparty": cp_raw,
            "counterparty_normalized": cp_norm,
            "raw_direction": direction,
            "implied_supplier": imp_sup,
            "implied_customer": imp_cus,
            "cut_rule": rule,
            "cut_category": category,
            "replacement_edge_ids": repl_edges,
            "duplicate_of_cut_id": dup_of,
            "leaked_in_edges_csv": "true" if is_leaked else "false",
            "verification_note": v_note,
        })

    assert leak_count == 0, f"发现 {leak_count} 条负向剔除对泄漏至 edges.csv！"

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CUTS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    return out_rows, leak_count


# ---------------------------------------------------------------------------
# 7. 双侧对账台账 counterparty_audit.csv（P01–P15 + Run1 P01/P03 & R2 P02 核查结论）
# ---------------------------------------------------------------------------
def build_counterparty_audit():
    _, edge_map = load_edges()
    with open(ARCHIVE_AUDIT_CANDIDATES, encoding="utf-8-sig", newline="") as f:
        cands = list(csv.DictReader(f))
    assert len(cands) == 15, f"counterparty-audit-candidates.csv 应为15行，实测={len(cands)}"

    audited_details = {
        "P01": {
            "audit_status": "audited_run1",
            "audit_verdict": "弱一致（不升级）",
            "party_a_verified_figures": (
                "天孚通信2025年报前五大客户实名Fabrinet: 3,268,843,594.94元(占年度销售63.31%，折约4.48–4.54亿美元@7.2–7.3)；"
                "2024: 2,005,917,035.59元(61.69%)；2023: 1,039,308,855.95元(53.61%)"
            ),
            "party_b_verified_figures": (
                "Fabrinet FY2025(至2025-06-27) 10-K: Revenues $3,419.327M(其中光通信$2,619.4M/76.6%)，"
                "Cost of revenues $3,005.978M；10-K向数千家供应商采购标准件，制度性不实名供应商"
            ),
            "discrepancy_pct_or_note": "量级相容(天孚销售额约占Fabrinet FY2025营收13.2% / COGS 15.0%@7.25)；B方供应商实名制度性不可见",
            "reconciliation_detail": (
                "自然年2025 vs FY2025(6月末止)错期重叠；光通信器件组件→EMS料单及福州Casix运营叙述相容。"
                "严守红线：单侧未见实名≠否定，弱一致不升格为双侧确认(2026-07-24核查)"
            ),
            "anchor_urls": (
                "edges.csv#E043;edges.csv#E072;edges.csv#E073;"
                "https://www.sec.gov/Archives/edgar/data/1408710/000140871025000039/fn-20250627.htm"
            ),
        },
        "P02": {
            "audit_status": "audited_r2_case004",
            "audit_verdict": "口径不可比（判例#004 B级终态：U门闭合/L门不可得）",
            "party_a_verified_figures": (
                "Fabrinet FY2023 10-K Significant customers实名Lumentum Operations LLC占收入15.4%($407.4M = $2,645.2M×15.4%)；"
                "FY2022:10.3% / FY2021:13.6% / FY2020:19%"
            ),
            "party_b_verified_figures": (
                "Lumentum 10-K Contract Manufacturer A占total net inventory purchases: FY2023 42.5%(初报43%)→FY2024 30.3%→FY2025 25.1%；"
                "FY2023净存货采购保守上界U1=COGS $1,113.6M+Δ存货$158.5M=$1,272.1M(10%门槛$127.2M)"
            ),
            "discrepancy_pct_or_note": "分母口径不同(确认收入 vs 净存货采购)；$407.4M若全额入分母占32.0%远超10%，但L门客户级收入构成拆分不可得",
            "reconciliation_detail": (
                "已并入refs/解匿判例库.md#判例004终态审查：Fabrinet供货Lumentum实名关系由A方10-K确定；"
                "其等同于Contract Manufacturer A维持B级高置信候选终态"
            ),
            "anchor_urls": (
                "edges.csv#E005;edges.csv#E038;edges.csv#E068;"
                "https://www.sec.gov/Archives/edgar/data/1408710/000140871023000028/fn-20230630.htm;"
                "https://www.sec.gov/Archives/edgar/data/1633978/000162828023030374/lite-20230701.htm"
            ),
        },
        "P03": {
            "audit_status": "audited_run1",
            "audit_verdict": "口径不可比（技术服务逐位双侧确认；商品含税+并表还原后仍差~4.9%）",
            "party_a_verified_figures": (
                "光迅科技2023年报前五大客户表「烽火通信科技股份有限公司」含税销售额369,224,117.92元(占年度销售总额5.59%)；"
                "关联交易附注不含税销售商品326,747,006.96元(×1.13=369,224,117.86元，差0.06元舍入)；另提供技术服务17,462,500.00元"
            ),
            "party_b_verified_figures": (
                "烽火通信2023年报关联采购商品(光迅母公司)217,747,419.95元 + 采购商品(光迅100%全资子武汉电信器件)125,019,191.39元 "
                "= 光迅集团商品合计342,766,611.34元；另接受劳务(光迅及其子公司)17,462,500.00元"
            ),
            "discrepancy_pct_or_note": "技术服务差额0.00元(双侧逐位确认)；不含税商品并入全资子武汉电信器件后差额-16,019,604.38元(约4.9%)",
            "reconciliation_detail": (
                "五层拆解：①客户表含税额÷1.13还原不含税商品；②剔除不入E074但双方逐位相等的1,746.25万元技术服务；"
                "③加回烽火分列的光迅100%子公司武汉电信器件1.25亿元采购，表面差额从~33%(1.34亿元)收窄至~4.9%(1,602万元)；"
                "残差未排除截止日/退货/其他孙公司口径，不升格双侧确认亦不判实质矛盾(2026-07-24核查)"
            ),
            "anchor_urls": (
                "edges.csv#E074;"
                "https://static.cninfo.com.cn/finalpage/2024-04-26/1219826062.PDF;"
                "https://static.cninfo.com.cn/finalpage/2024-04-27/1219875788.PDF"
            ),
        },
    }

    out_rows = []
    for c in cands:
        pid = c["pair_id"].strip()
        eids = [x.strip() for x in c["A方披露(边ID)"].split(";") if x.strip()]
        for eid in eids:
            assert eid in edge_map, f"counterparty_audit {pid} 引用了不存在的边 {eid}"
        default_anchors = ";".join(f"edges.csv#{eid}" for eid in eids)
        detail = audited_details.get(
            pid,
            {
                "audit_status": "candidate_pending",
                "audit_verdict": "制度性或会计科目预期不可见（待扫资本开支/关联附注）",
                "party_a_verified_figures": "; ".join(
                    f"{eid}:{edge_map[eid]['财年']}={edge_map[eid]['占比或金额原文']}" for eid in eids
                ),
                "party_b_verified_figures": "",
                "discrepancy_pct_or_note": "设备采购通常计入固定资产/在建工程或低于B方前五大供应商门槛，单侧未见不构成否定",
                "reconciliation_detail": c["理由"].strip(),
                "anchor_urls": default_anchors,
            },
        )
        out_rows.append({
            "pair_id": pid,
            "party_a": c["A方"].strip(),
            "party_b": c["B方"].strip(),
            "party_a_edge_ids": ";".join(eids),
            "party_b_has_channel": c["B方是否有披露渠道"].strip(),
            "product_fit": c["产品匹配度"].strip(),
            "period_overlap": c["期间重叠"].strip(),
            "passes_party_b_threshold": c["金额是否可能过B方披露阈值"].strip(),
            "expected_accounting_account": c["会计科目预判"].strip(),
            "priority": c["优先级"].strip(),
            "candidate_rationale": c["理由"].strip(),
            **detail,
        })

    fieldnames = list(out_rows[0].keys())
    with open(OUT_AUDIT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    return out_rows


# ---------------------------------------------------------------------------
# 8. 卖方验真与缺席监测闹钟表 sellside_watch_alarms.csv（W01–W07）
# ---------------------------------------------------------------------------
def build_sellside_watch_alarms():
    with open(ARCHIVE_ABSENCE_WATCH, encoding="utf-8-sig", newline="") as f:
        raw_watches = list(csv.DictReader(f))
    assert len(raw_watches) == 7, f"absence-watch.csv 应为7行，实测={len(raw_watches)}"

    updates = {
        "W01": {
            "expected_window": "2026年报季(2027-04前)",
            "alarm_status": "active_alarm_2026_2027",
            "resolution_date": "",
            "canonical_ref": "points.csv#P059;edges.csv#E011;edges.csv#E012",
            "verification_notes": (
                "保留为2027-04前到期验真闹钟：卖方曾预测ficonTEC 2025营收6.37亿/净利0.83亿"
                "(罗博特科2025业绩预告亏损9000万-1.3亿元、设备交付验收周期拉长已触发早期偏差信号)；"
                "待并表后完整年度分部营收披露结算偏差是否>30%"
            ),
        },
        "W02": {
            "expected_window": "2026-2027滚动(创业板IPO审核期)",
            "alarm_status": "active_alarm_2026_2027",
            "resolution_date": "",
            "canonical_ref": "points.csv#P055;edges.csv#E045;knowledge.yaml#KN001;knowledge.yaml#KN007",
            "verification_notes": (
                "保留为2026-2027滚动验真闹钟：2026-04新版申报稿已核实对中际旭创占比由62.19%(2023)/58.85%(2024)降至53.42%(2025)，"
                "且老化测试设备毛利率由50.65%降至12.55%；后续每轮问询回复与注册稿继续作为T1脉冲源验收"
            ),
        },
        "W03": {
            "expected_window": "已触发里程碑(2026-04-24上市)",
            "alarm_status": "verified_updated",
            "resolution_date": "2026-04-24",
            "canonical_ref": "points.csv#P061;refs/entity-registry.yaml;edges.csv#E082",
            "verification_notes": (
                "已核实更新：联讯仪器已于2026-04-24正式登陆科创板(证券代码688808，见2026-08-27半年度报告1225511954.PDF股份变动说明)，"
                "且2026-01-07更新版招股书申报稿(002075_20260107_UL2D.pdf)在案锚定历史占比；"
                "注:集团一仍维持代号豁免未实名，points.csv P061待v6宇宙扩容补入corpus/_frozen.csv后同步切为A股"
            ),
        },
        "W04": {
            "expected_window": "2026年报季(2027-04前)",
            "alarm_status": "active_alarm_2026_2027",
            "resolution_date": "",
            "canonical_ref": "edges.csv#E014;edges.csv#E077",
            "verification_notes": (
                "保留为2026年报到期验真闹钟：官方互动平台未点名Fabrinet且外部转述存在3条vs2条产线口径分歧；"
                "2025年报前五集中度仅27.65%(第一名匿名8.51%)，若2026年报仍不具名则严禁将E014半边升格为实边"
            ),
        },
        "W05": {
            "expected_window": "2026年报季(2027-04前)",
            "alarm_status": "active_alarm_2026_2027",
            "resolution_date": "",
            "canonical_ref": "corpus/customs/;macro_evidence.csv",
            "verification_notes": (
                "保留为2026年报季到期验真闹钟：GGII等第三方泰国产能估计vs公司'以定期报告为准'；"
                "待中际旭创/新易盛2026年报披露境外生产基地产能或子公司财务数据后结算偏差是否>30%"
            ),
        },
        "W06": {
            "expected_window": "已核实结案(2026-07-09)",
            "alarm_status": "verified_closed",
            "resolution_date": "2026-07-09",
            "canonical_ref": "macro_evidence.csv#MC035",
            "verification_notes": (
                "已核实结案并指向macro_evidence.csv#MC035：经原diff-log#D002/D003穿透核对，卖方研报引用的'2030年54亿美元 / 121% CAGR'"
                "为Yole报告内自洽的Scale-Up细分口径，而Yole公开新闻稿'81亿美元 / 137% CAGR'系跨子口径拼接体；"
                "解除东吴'选择性引用'污染嫌疑，后续引用须强制标注Scale-Up vs 全口径边界"
            ),
        },
        "W07": {
            "expected_window": "2027-H1(路径中点)",
            "alarm_status": "active_alarm_2026_2027",
            "resolution_date": "",
            "canonical_ref": "corpus/relationships/relationship_timeline.csv",
            "verification_notes": (
                "保留为2027-H1中期验真闹钟：针对卖方自建模型'2028年光模块设备需求超400亿元'，"
                "届时汇总罗博特科/猎奇智能/联讯仪器/凯格精机/奥特维/博众精工等光通信设备板块年化确认收入检验是否显著偏离路径"
            ),
        },
    }

    out_rows = []
    for r in raw_watches:
        wid = r["watch_id"].strip()
        upd = updates[wid]
        out_rows.append({
            "watch_id": wid,
            "expected_event": r["预期事件"].strip(),
            "origin_basis": r["依据(溯源报告条目)"].strip(),
            "expected_window": upd["expected_window"],
            "legacy_status": r["状态"].strip(),
            "alarm_status": upd["alarm_status"],
            "escalation_rule": r["升级规则"].strip(),
            "resolution_date": upd["resolution_date"],
            "canonical_ref": upd["canonical_ref"],
            "verification_notes": upd["verification_notes"],
        })

    fieldnames = list(out_rows[0].keys())
    with open(OUT_ALARMS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    return out_rows


# ---------------------------------------------------------------------------
# 9. 写出 corpus/relationships/README.md（含 Step 3 Daily 高频事件挂接契约）
# ---------------------------------------------------------------------------
def build_relationships_readme(stats: dict):
    md = rf"""# 供应链关系时间线与边级治理台账 (`corpus/relationships/`)

本目录承载光模块知识库 **关系层（Supply-Chain & Counterparty Layer）** 的四张核心结构化台账，连接根级静态快照 [`edges.csv`](../../edges.csv)（236 条边 `E001–E236`）与 Step 3 日更情报流（`domestic_daily` / `daily_intelligence` / `calls`）。

---

## 一、目录文件清单与统计快照

| 文件名 | 记录数 | 定位与核心作用 |
|---|---:|---|
| `relationship_timeline.csv` | **{stats['timeline_rows']} 行**（覆盖 **{stats['relation_count']} 对**关系） | 统一关系时间线主表：完整整合 `E001–E099` 基线、无损拆解 `E100–E236` 多期打包行（拆出 **{stats['e100_e236_unpacked_rows']} 条**分期行），并入设备观察池补充行（**{stats['eq_added_count']} 条**）且预留 Step 3 Daily 挂接列 |
| `edge_negative_cuts.csv` | **{stats['cuts_rows']} 行** | 边级负向剔除记忆表：收录长飞系个体合并承载（25 条）、华工非光链/坏账（40 条）、非供货方向（6 条）、非光链主体（3 条），经程序化核验在当前 `edges.csv` 中 **`0` 泄漏** |
| `counterparty_audit.csv` | **{stats['audit_rows']} 行**（`P01–P15`） | 跨主体双侧对账台账：含会计科目错位预判（原材料 vs 固定资产/在建工程）及已完结的 `P01`（天孚→Fabrinet 弱一致）、`P02`（Fabrinet↔Lumentum B级终态）、`P03`（光迅↔烽火服务费逐位确认、商品含税+并表还原后差 `~4.9%`） |
| `sellside_watch_alarms.csv` | **{stats['alarms_rows']} 行**（`W01–W07`） | 卖方预测与缺席验真闹钟：`W03`（联讯仪器 `688808` 已于 `2026-04-24` 科创板上市）与 `W06`（Yole CPO `54亿/121%` Scale-Up 口径已结案并归入 `macro_evidence.csv#MC035`）已核实更新；`W01/W02/W04/W05/W07` 作为 2026–2027 到期验真闹钟持续生效 |

---

## 二、`relationship_timeline.csv` 统一 Schema（21 列）与生命周期红线

### 2.1 字段定义

| 列名 | 必填 | 受控枚举 / 格式 | 规则说明 |
|---|---|---|---|
| `timeline_id` | 是 | `TL0001`..`TL9999` | 时间线原子观测全局唯一主键 |
| `relation_id` | 是 | `R001`..`R999` | 归一化有向关系键（`R001–R070` 与历史基线严格兼容；默认匿名槽位按边独立不跨年串接，唯一同文件恒定代号例外为 `联讯仪器 -> 集团一(匿名)`） |
| `supplier` | 是 | 规范化供方名 | 经别名表归一化，严格遵守 `refs/entity-registry.yaml`（合并口径与法人单体分列，不硬并） |
| `customer` | 是 | 规范化需方名 | 同上，方向敏感（`A→B` 与 `B→A` 为不同 `relation_id`） |
| `supplier_point_id` | 否 | `P###` / `EXT` / `ANON` / 空 | 对齐 `points.csv` 能力点或边界外/匿名标识 |
| `customer_point_id` | 否 | `P###` / `EXT` / `ANON` / 空 | 同上 |
| `period` | 是 | `2025` / `2022H1` / `2025Q1` / `FY2025` / `2024-12-13` | 会计期间或时点日期，自然年与 `FY` 财年严禁混同 |
| `period_type` | 是 | `year \| half_year \| quarter \| month \| snapshot \| fiscal \| year_range \| event` | 历史财报用前七类；Step 3 高频日更事件统一填 `event`（或明确季度 `quarter`） |
| `event_date` | 否 | `YYYY-MM-DD` 或空 | 时点快照（如在手订单截止日）与 Step 3 日更事件必填精确发生/答复日；年度/半年度区间留空，严禁拿年报披露日冒充业务发生日 |
| `source_channel` | 是 | 历史：`annual_report \| prospectus \| sec_10k`<br>日更：`daily_ir \| daily_qa \| daily_announcement` | 区分定期财报/招股书静态基线与 Step 3 高频脉冲信源 |
| `metric_kind` | 是 | 历史：`sales_share \| purchase_share \| amount_rmb \| amount_usd \| order_backlog \| intermediary_disclosure \| bad_debt_writeoff`<br>日更扩展：`order_progress \| partnership_milestone \| qualification_status \| capacity_co_investment` | 明确区分**供方披露占营收比（`sales_share`）**与**需方披露占采购/成本比（`purchase_share`）**，防止分母倒置 |
| `value_raw` | 是 | 原文数值或事件摘要 | 完整保留原始披露字面串（如 `53.42%(37277.97万元)`），不丢单位、不丢口径括注 |
| `numeric_value` | 否 | 纯十进制数字或空 | 去千分位后的主数值；不等式（如 `<10%`）、跌出前五或定性事件留空，严禁把 `<10%` 写成 `10` |
| `unit` | 否 | `% \| 元 \| 万元 \| 万美元 \| 万欧元 \| 台` 或空 | 与 `numeric_value` 严格配对 |
| `observe_type` | 是 | 常规：`first_observed \| observed \| last_observed \| censored`<br>特殊：`confirmed_ended \| procedural_intermediary \| bad_debt_frozen`<br>日更：`event_disclosed` | **核心防误判闸门**（见 §2.2） |
| `edge_grade` | 是 | `实边 \| 推断A \| 推断B \| 半边` | 继承或按信源证据强度赋级 |
| `source_edge_ids` | 否 | `E###`（多边以 `;` 分隔） | 关联 `edges.csv` 边号；观察池未入前五补充行或纯日更事件可留空 |
| `daily_ref_id` | 否 | 上游事件唯一键或空 | 历史财报行固定为空 `""`；Step 3 日更事件必填（见 §3） |
| `anchor_url` | 是 | URL 或仓内规范锚点 | 统一指向一手 URL、`edges.csv#E###` 或 `corpus/...`，零归档悬空路径 |
| `conflict` | 是 | `true \| false` | 同关系同期间出现跨表/双侧口径冲突（如 `R012` `E038` vs `E068`、`E154` 前五大合并 vs 关联交易表）标 `true`；同源占比+补充金额或商品+劳务并行分项标 `false` |
| `notes` | 否 | 自由文本（分号分隔） | 记录同源配对金额、夹层警示（`intermediary_layer`）、观察池 `eq_watch_series_id` 及口径约束 |

### 2.2 三类特殊关系生命周期/性质标签（下游前端硬过滤红线）

任何下游图谱渲染、集中度统计或“当前活跃供应商”查询，**必须过滤以下三类特殊 `observe_type`**，严禁将其与常规活跃边混算：

1. **`confirmed_ended`（确认终结边）**：有明确监管断供或官方终止披露（如 `E008` `NeoPhotonics -> 华为(含海思)` 2019-05 BIS 实体清单管制后于 `2021` 归零）。注意：单纯“跌出前五 / `<10%` 退出披露表”只标 **`censored`（右截尾不可见）**，严禁误判为关系死亡！
2. **`procedural_intermediary`（程序性代理夹层）**：仅在收入确认政策等程序段落点名的出口代理/通关通道（如 `E016` `新易盛 -> 浙江粮油`），并非真实终端买家。对于有明确金额的结算平台/分销商（如 `PINEWAVE`、`Digicomm`、`讯速信远`、`南央国际`、`津微光电`、`陕西电子信息国际商务有限公司`），保留其时序 `observe_type` 并在 `notes` 强制打标 `intermediary_layer:...`。
3. **`bad_debt_frozen`（坏账核销/冻结遗留项）**：来自资产负债表应收账款单项计提坏账准备附注（如 `E146` `Kaiam Corporation -> 博创科技` 2023–2025 连续三年 `100.00%` 单项计提坏账约 `1,059–1,093 万元`），代表历史破产冻结余额而非当期供货交易。

---

## 三、Step 3 Daily 高频事件挂接契约（Insertion Contract）

Step 3 日更管线（境内互动易 `corpus/qa/`、投资者关系活动记录表 `corpus/ir/`、巨潮公告及海外新闻稿/季报电话会 `calls/` / `workflow-rehearsal-daily-state/`）在捕获到具名供应链合作、订单进展、客户验证或联合扩产事件时，**无需另建孤立事件表，直接按以下契约追加至 `relationship_timeline.csv` 同一根时间线上**：

### 3.1 写入与幂等挂接规则

1. **关系键复用与新开（`relation_id`）**：
   - 先将事件供需双方按 `ALIAS_MAP` 与 `refs/entity-registry.yaml` 归一化：
     - 若归一化 `(supplier, customer)` 已存在于非匿名 `relation_id` 中（例如 `罗博特科/ficonTEC -> NVIDIA` 已存在 **`R057`**），**必须直接复用该 `relation_id`**，使高频事件自然接续在历史年报/招股书/在手订单序列之后！
     - 若为历史财报尚未覆盖的新具名组合（例如晶圆代工厂 `Tower Semiconductor -> 中际旭创`），按序分配新 `R###`（建议日更分配区间或顺延最大 `R###`）。
2. **必填高频溯源四件套**：
   - `source_channel`：严格取值 `daily_qa`（深交所互动易/上证e互动）、`daily_ir`（投资者关系活动记录表/路演纪要）、`daily_announcement`（上市公司正式公告、海外发行人官网 Press Release / SEC 8-K）。二手媒体传闻未获一手段落印证前**严禁入表**。
   - `daily_ref_id`：**非空唯一上游事件幂等键**（如互动易 `qa:<stock_code>:<index_id>`、海外披露候选 `DC_<hash>` 或正式事件 `EV###`）。重跑日更同步脚本时以 `(source_channel, daily_ref_id)` 唯一键幂等更新（Upsert），防止重复追加。
   - `period` / `period_type` / `event_date`：日更点事件统一填 `period = YYYY-MM-DD`、`period_type = event`、`event_date = YYYY-MM-DD`（**必须填官方答复日 `answer_date` 或新闻稿发布日 `published_date`**，严禁填爬虫抓取日 `fetch_date` 或提问日 `ask_date`）。
   - `observe_type`：日更定性/脉冲事件统一填 **`event_disclosed`**（除非公告明确宣布合作终止填 `confirmed_ended`），**不篡改**同关系下历史财报序列原有的 `first_observed` / `last_observed` 边界，确保财报定量序列与高频事件脉冲同轴展示、互不污染。
3. **数值克制纪律**：
   - 若互动易/新闻稿仅确认合作或量产交付状态而未披露具体金额/台数，`metric_kind` 填 `order_progress` / `partnership_milestone` / `qualification_status`，`numeric_value` 与 `unit` **必须留空 `""`**，摘要原话写入 `value_raw`；若正式公告披露精确合同金额，则填 `amount_rmb` / `amount_usd` / `order_backlog` 并提取精确数值与单位。

### 3.2 标准挂接实例（可直接作为 Step 3 测试样例）

#### 实例 A：罗博特科 × 英伟达 `2026-11-16` 深交所互动易确认量产订单交付与收入确认（接续既有 `R057`）
- **上游原件**：`domestic/qa/300757/qa.jsonl`（`index_id = 2402040011815366656`, `answer_date = 2026-11-16`）
- **与历史序列同轴效果**：直接挂入 **`R057`（`罗博特科/ficonTEC -> NVIDIA`）**，排在 `2024-07-31`（在手订单 `2433.83万欧元`）与 `2024-12-13`（在手订单 `4800万欧元`）之后，形成“2024 在手订单快照 → 2026-11 晶圆/晶粒测试设备多笔量产订单陆续交付确收”的完整证据链：

```csv
timeline_id,relation_id,supplier,customer,supplier_point_id,customer_point_id,period,period_type,event_date,source_channel,metric_kind,value_raw,numeric_value,unit,observe_type,edge_grade,source_edge_ids,daily_ref_id,anchor_url,conflict,notes
TL9001,R057,罗博特科/ficonTEC,NVIDIA,P059,EXT,2026-11-16,event,2026-11-16,daily_qa,order_progress,"英伟达系ficonTEC客户之一；2025年配合完成双面晶圆及晶粒测试设备开发验证后相继取得多笔量产化订单，部分已完成交付及收入确认",,,event_disclosed,实边,E012,qa:300757:2402040011815366656,corpus/qa/300757/qa.jsonl#indexId=2402040011815366656,false,"深交所互动易官方回复(ask_date=2026-11-11,answer_date=2026-11-16)；定性确认量产订单交付确收，具体金额涉密未披露"
```

#### 实例 B：Tower Semiconductor × 中际旭创(Innolight) `2026-11-03` 联合新闻稿推进 AI 近封装光学（NPO）合作（新开关系号）
- **上游原件**：`overseas/staging/2026-11-10/disclosure_candidates.csv`（`DC_430D7977BA22`, `published = 2026-11-03`）
- **挂接写法**：供方为硅光代工厂 `Tower Semiconductor`，需方归一化为 `中际旭创`，`source_channel = daily_announcement`，`daily_ref_id = DC_430D7977BA22`：

```csv
timeline_id,relation_id,supplier,customer,supplier_point_id,customer_point_id,period,period_type,event_date,source_channel,metric_kind,value_raw,numeric_value,unit,observe_type,edge_grade,source_edge_ids,daily_ref_id,anchor_url,conflict,notes
TL9002,R205,Tower Semiconductor,中际旭创,EXT,,2026-11-03,event,2026-11-03,daily_announcement,partnership_milestone,"Tower Semiconductor与中际旭创(Innolight)宣布联合推进面向AI基础设施的高性能近封装光学(NPO)产品合作",,,event_disclosed,实边,,DC_430D7977BA22,https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/,false,"Tower官网一手新闻稿(2026-11-03)；技术与商业生态合作里程碑，不含定量采购额"
```
"""
    with open(OUT_README_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)


# ---------------------------------------------------------------------------
# 10. 原地幂等更新 refs/解匿判例库.md（严格维持 len(os.listdir('refs')) == 8）
# ---------------------------------------------------------------------------
CANONICAL_REFS_CASES_MD = """# 解匿判例库 — 彩排 P3 产出（2026-07-21，2026-11-21 Step 2 合入 #005 反面教材与终态定量注）

B工序阶梯：披露史考古 → 程序段落 → 中标合同 → 金额指纹（按序升级，够用即停）。
判定等级：A=多源硬证据互锁，实务当实名用 / B=单一硬证据+一致性验证 / C=推断，
需显式标注且不得承重 / D=不足以判定。每判例附五项陷阱排除（直接/终端客户口径、
会计期、汇率、多实体、贸易商夹层）与可推翻条件。

**当前判定（经红队 Y1 复核 2026-07-23、R2 终态审查及 v1.6r 增补）**：判例#002 PINEWAVE **A级**、
判例#003 Lumentum考古 **A级**、判例#004 Fabrinet反照 **B级终态**（原A级，因排他性分母口径未闭合经 RT-006 降级，
R2 闭合 U 门 `$1,272.1M` 上界但 L 门客户级归类不可得）、判例#005“旭创双流” **已推翻（反面教材留档，RT-011/RT-014 证伪）**、
判例#006 联讯仪器“集团一” **C级候选（严禁点名，含 RT-009/RT-010 口径克制红线）**、
判例#007 太辰光“客户第一名”=Corning **B级**、判例#001 留档待跑。
**身份指纹成立≠物流穿透成立** 是红队的统一铁律：所有判例只解“计费/披露对手方是谁”，不证明货物实际物理流向。

---

## 判例#002 中际旭创"客户E"(2025, 8.10%, 30.97亿元) = PINEWAVE PTE. LTD 【A级】

**槽位**：edges.csv E044 关联；旭创2025年报前五大客户表第5名匿名。

**工序路径**：程序段落（关联交易章节）→ 金额指纹。未动用检索升级即锁定。

**证据链**：
1. 旭创2025年报前五大表：客户E 3,096,780,769.22元、占比8.10%；同表"前五名客户
   销售额中关联方销售额占年度销售总额比例 8.10%"——占比逐位相等。（红队 Y1-F01：
   "前五中只有一个关联方"不是数学事实——理论上可有两个关联方经两位小数舍入合计仍为
   8.10%；但占比相等叠加下条金额指纹使该替代解释概率极低。）
   锚：http://static.cninfo.com.cn/finalpage/2026-03-31/1225056459.PDF（检索日 2026-07-21）
2. 同年报重大关联交易表：关联方 PINEWAVE，向关联人销售产品 43,378 万美元，
   占同类交易 100%。金额指纹：4.3378亿美元 × 年均汇率≈7.14 ≈ 30.97亿元，
   与客户E金额吻合（关联交易明细表 3,097,151,244.97 元与前五大表 3,096,780,769.22
   元差 37 万元，量级为服务项/口径差，不动摇判定）。
3. 公告2026-005（2026-01-13）：PINEWAVE PTE. LTD，新加坡 202432405D，成立
   2024-08-08；股东 TERAHOP PTE. LTD（旭创控股孙公司）59.52% + TELIO 25.48% +
   PRIMAXE 15.00%；"公司董事长、总裁刘圣先生担任 PINEWAVE 的董事"；2026年度
   预计交易上限 100,000 万美元。
   锚：http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2026/2026-1/2026-01-13/11911961.PDF（承载页，本体为巨潮公告；检索日 2026-07-21）

**陷阱排除**：
- [x] 直接/终端客户口径：**触发并识别**——PINEWAVE 是旭创自设海外关联销售平台，
  不是终端客户。客户E解匿完成，但其身后的终端买家不可见（见"剩余不可知"）。
- [x] 会计期：年报与关联交易公告同为2025自然年度，一致。
- [x] 汇率：美元→人民币按年均汇率折算吻合（0.01%级差异在汇率波动带内）。
- [x] 汇率与分母提醒（RT-001/四.3）：43,378万美元“占同类交易100%”分母为该类关联交易，客户E“8.10%”分母为年度销售总额，两分母不同，系通过金额+关联汇总占比互锁匹配。
- [x] 多实体：PINEWAVE 单一新加坡主体，无同名混淆。
- [x] 贸易商夹层：即本判例主发现——夹层实体本身就是答案。

**判定**：客户E = PINEWAVE PTE. LTD，**A级**（在现有披露精度下，占比相等+金额指纹+身份公告构成唯一合理互锁）。

**剩余不可知（诚实边界）**：PINEWAVE 的下游终端客户公开信息不可判定（D级）；
2026年度关联交易预计上限升至10亿美元，显示公司为经 PINEWAVE 扩大销售预留额度
（红队 Y1-RT-002/RT-003：预计上限≠收入预测或系统性平台化定论，实际发生额及其占海外直销比例待后续年报验证），
年报前五大表的终端可穿透性可能受此夹层影响。

**可推翻条件**：若旭创披露前五大中另有关联方（与"8.10%=8.10%"矛盾）；若关联
交易金额重述；若 PINEWAVE 股权结构变更导致会计口径改变。

---

## 判例#003 Lumentum FY2025 "Customer A/B/C/D" = Ciena/Google/Apple/Nokia 【A级】

**槽位**：E036(Customer A 16.0%)、E037(Customer B 15.4%)；C/D 未及10%线仅具名。

**工序路径**：披露史考古（一步命中，未升级）。

**证据链**：Lumentum FY2025 10-K 客户表匿名化为 Customer A-D，但同表保留
FY2024/FY2023 两列历史占比；与 FY2024/FY2023 10-K 实名表逐位比对：
- Customer A：FY2024 11.4% / FY2023 15.3% ←→ Ciena 11.4% / 15.3%（完全一致）
- Customer B：FY2024 18.9% ←→ Google 18.9%（完全一致）
- Customer C：FY2023 12.1% ←→ Apple 12.1%（完全一致）
- Customer D：FY2023 10.5% ←→ Nokia 10.5%（完全一致）
四行历史占比与此前实名表形成唯一无冲突匹配（在0.1个百分点披露精度下仍存在理论
碰撞可能，但均超过10%法定披露线，若另有同占比客户前一年10-K亦应列出；A/B 有多年度指纹，
替代解释需多次巧合同时发生——红队 Y1-RT-004）。
锚：FY2025 10-K https://www.sec.gov/Archives/edgar/data/1633978/000162828025040830/lite-20250628.htm；
FY2024 10-K https://www.sec.gov/Archives/edgar/data/1633978/000162828024038024/lite-20240629.htm；
FY2023 10-K https://www.sec.gov/Archives/edgar/data/1633978/000162828023030374/lite-20230701.htm（检索日 2026-07-21）

**陷阱排除**：
- [x] 直接/终端口径：同一公司同一披露序列的同一口径（net revenue 10%+ 表），无口径切换。
- [x] 会计期：同一财年序列自比，无错位。
- [x] 汇率：同为美元报表，不涉及。
- [x] 多实体：指纹匹配在披露表层面完成，不依赖实体主体判断。
- [x] 贸易商夹层：客户表的计费客户可识别为 Ciena/Google/Apple/Nokia（身份指纹
  成立）；但实际收货主体、合同制造商（EMS）夹层、VMI 仓与最终使用地未由该 10-K 表披露——
  身份成立≠物流穿透成立（红队 Y1-RT-005，删除原"无夹层迹象"断言）。

**判定**：A=Ciena（FY2025 16.0%）、B=Google（15.4%）、C=Apple、D=Nokia，**A级**。
FY2025 匿名化事件本身记入 anomalies——实名窗口会关闭，考古须趁早。

**可推翻条件**：若 Lumentum 后续文件重述历史占比；若公司说明匿名标签并非跨期恒定标签（RT-004）；
若出现两客户占比在0.1精度上碰撞的年份（本序列无）。

---

## 判例#004 Lumentum "Contract Manufacturer A"(FY2023采购42.5%) = Fabrinet 【B级】

> **红队 Y1-RT-006 降级（A→B）**：Fabrinet 对 Lumentum 的 4.074 亿美元是 Fabrinet
> 确认的*收入*，Lumentum 表中 42.5% 的分母是 *total net inventory purchases*，
> 两者会计口径不同且初始版本未构造同口径采购分母桥接（COGS 仅作量级参照，非
> 净存货采购）。因此 Fabrinet=匿名代工A 是**高置信候选**而非严格排他证明。
> **R2 终态审查已完成（2026-07-23，U门闭合 `$1,272M` 上界 / L门客户级归类不可得）**：
> 净存货采购保守上界 `U₁ = $1,272.1M` 已由 10-K 原文逐数闭合，Fabrinet `$407.4M` 若全额进入分母占 `32.0%`，
> 量级排除较原论证显著强化；但 L 门（客户级会计归类）公开材料不可得。**B 级为终态**，关系本身
> （Fabrinet 供货 Lumentum）由 Fabrinet 实名披露确定，不受降级影响。

**槽位**：E038。供应商侧匿名（美股同样只实名客户不实名供应商）。

**工序路径**：对手方反照（利用客户侧强制披露解供应商槽位——seed 方法论结论#2 的教科书应用）。

**证据链**：
1. Fabrinet FY2023 10-K Significant customers 表（命中引语）："Cisco Systems Inc.,
   Lumentum Operations LLC, Nvidia Corporation, and Infinera Corporation contributed
   15.6%, 15.4%, 12.5%, and 12.4% respectively, of our revenues"；表格另列
   Lumentum FY2022:10.3% / FY2021:13.6%。Fabrinet FY2023 总营收 `$2,645.2M` × `15.4%` = **`$407.4M`**。
   锚：https://www.sec.gov/Archives/edgar/data/1408710/000140871023000028/fn-20230630.htm（检索日 2026-07-21）
2. **U/L 双门定量推导注（R2 终态复核，Lumentum FY2023 10-K 原文逐数核实）**：
   严格数学排他需证明 `L > 10% × U`（即 Fabrinet 对 Lumentum 收入中进入净存货采购分母的最低额 `L` 超过分母上界 `U` 的 10%，结合 Lumentum 明示“仅一家代工≥10%”即可唯一锁定）：
   - **U 门（Lumentum 净存货采购上界 —— 已闭合，`$1,272.1M`）**：核对 Lumentum FY2023 10-K 利润表与存货/并购附注原文：
     `Net revenue = $1,767.0M`、`Cost of sales (COGS) = $1,113.6M`（=63.0%×收入）、`期末存货 = $408.6M`、`期初存货 = $250.1M`（另含 NeoPhotonics 并购带入存货 `$84.3M`、公允价值 step-up `$17.8M`）。故意不扣并购带入存货、不剔除内部人工与制造费用，构造偏高保守上界：
     `U₁ = COGS + (期末存货 - 期初存货) = $1,113.6M + ($408.6M - $250.1M) = $1,272.1M`（若极端加回无形摊销 `$84.4M`，更宽上界 `U₂ = $1,356.5M`）。对应 **10% 披露门槛仅为 `$127.2M ~ $135.7M`**（彻底取代早期粗算的“分母须超 40.7 亿美元”）。Fabrinet 实名收入 `$407.4M` 若全额进入该分母，占比达 **`32.0%`**，远超 10% 门槛。
   - **L 门（Fabrinet 收入进入该采购分母的下界 —— 公开材料不可得，未闭合）**：要完成无漏洞数学排他，还需证明 `$407.4M` 中至少 `~$127.2M`（约 `31%`）在 Lumentum 账上计入 `total net inventory purchases`。但 Fabrinet 10-K 无 Lumentum 客户级收入拆分（产品交付 vs 制造服务费 / 工具 / NRE / 客户供料净额处理），Lumentum 10-K 亦未披露该分母明细构成。故 L 门无法从公开财报闭合。
3. 地理一致：Lumentum 称代工位于泰国/台湾/马来西亚，Fabrinet 主基地泰国。
   （红队 Y1-RT-007：Lumentum 泰国长期资产增长是 Lumentum 自有/控制资产，非外部
   EMS 资产，对 Fabrinet 身份无排他力，已从证据链删除，至多作"Lumentum 自身泰国
   制造暴露增加"旁注。）
4. 历史一致：seed E005（Fabrinet FY2020 实名 Lumentum 19%）。

**陷阱排除**：
- [x] 直接/终端口径：代工关系为直接供货，无终端歧义。
- [x] 会计期：Fabrinet 财年6月末止、Lumentum 财年6月末-7月初止，重叠≈100%，
  换算无需调整（金额指纹纪律中"先换算重叠期"在此天然满足）。
- [x] 汇率：双方美元报表。
- [x] 多实体："Lumentum Operations LLC"为 Lumentum Holdings 运营子公司，
  披露主体归属明确。
- [x] 贸易商夹层：EMS代工直接交易，无夹层。

**判定**：Contract Manufacturer A = Fabrinet，**B级终态**（高置信候选：对手方实名 + U门 `$1,272.1M` 上界量级排除强化 + 地理与历史一致，惟 L 门客户级会计归类不可得）。
占比序列：FY2023 42.5%→FY2024 30.3%→FY2025 25.1%（Lumentum 对该代工厂净存货采购占比下降；
同期 NVIDIA 占 Fabrinet 收入比例上升。两序列方向相反，但两个不同分母的占比序列不能证明存在产能转移替代关系——红队 Y1-RT-008 删除"互为镜像"暗示）。

**可推翻/升级条件**：① **升级为 A 级条件**：任一方后续披露客户级收入构成或采购分母明细（或取得合同级证据），使 `L > $127.2M` 可审计；② **推翻条件**：若发现 Lumentum 另有一家年净存货采购额 `>$127.2M` 的代工且 Fabrinet 计入分母部分 `<$127.2M`，或 Fabrinet 重述客户表。

---

## 判例#001 新易盛"客户一"(2023, 36.79%) —— 本轮未跑，留档

**理由**：云巨头直销槽位，seed 方法论已判上限C级；本轮P3预算内优先跑证据密度
更高的三案。已就位的输入：2023:36.79%(11.40亿元)、2024:31.74%(27.44亿元)、
2025:22.97%(57.07亿元)金额序列；2025年报销售模式段客户三分类先验（通信设备商/
互联网厂商/经销商）；浙江粮油出口代理线索（E016）可作报关侧旁证起点。
**下一步路径（SOP候选）**：客户类型先验 → 云厂商capex节奏比对（金额指纹C级） →
浙江粮油报关方向线索 → 明示C级判定与可推翻条件。禁止：论坛式断言直接点名。

---

## 判例#005（已推翻反面教材）“旭创双流”假设为何不成立【RT-011 证伪留档】

> **归档定位**：本条是知识库**“严禁跨维度硬拼宏观海关流与公司财报流”的标准反面教材**。早期彩排（v1.3）曾试图将判例#002（中际旭创向新加坡关联平台 PINEWAVE 销售 `43,378 万美元`）与海关 HS `85177950` 江苏省对马来西亚出口数据合拢为所谓“钱走新加坡结算、货走江苏→马来”的判例#005，经独立红队（RT-011 至 RT-015）逐条复算证伪，**正式取消判例资格，降格为待检验假设 H5（严禁承重）**。

**原假设错误叙事还原**：
早期草稿声称：“2026-06 中国对马来西亚光模块出口 `$222M` 几乎全部来自江苏省注册主体且与进料加工贸易同额；对马出口在 `2025-04` 出现精确产能迁移拐点首次反超美国；进料加工占比高证明马来端系真产能迁移而非纸面转口，与旭创 PINEWAVE 平台构成钱货双流闭环。”

**红队四重证伪链（大白话 + 海关底表精确复算数字）**：

1. **三口径分母混为一谈（RT-014 算术直接证伪）**：
   复算本地海关四维底表（HS `85177950`），`2026-06` 三个真实数字根本不是同一个数，而是来自三张不同维度的边际汇总表：
   - 全国对马来西亚出口总额 = **`$260,431,342`（`$260.431M`）**（`customs_partners.csv`）；
   - **江苏省注册主体**对马出口额 = **`$221,642,573`（`$221.643M`）**，占全国对马总额 **`85.11%`**（`customs_province.csv`）；
   - 全国对马**进料加工贸易**出口额 = **`$222,295,216`（`$222.295M`）**，占全国对马总额 **`85.36%`**（`customs_trademode.csv`）。
   **大白话拆穿**：海关公开统计不提供“省份 × 贸易方式”联合交叉明细表！江苏的 `$221.643M` 与全国进料加工的 `$222.295M` 只是两个维度各自占 `$260.431M` 约 85% 带来的数值接近，根本不能逐行画等号说“对马总额就是 `$222M` 且全由江苏进料加工构成”。
2. **零企业级连接键（缺报关单/提单 join key，RT-011 & RT-015）**：
   “PINEWAVE 2025 全年关联结算额 `43,378 万美元`”与“江苏省月度海关出口汇总额”之间**没有任何交易级、主体级或期间金额桥（join key）**：
   - PINEWAVE 完全可以结算发往泰国、美国或其他目的地的货物，也可以采购自非江苏主体（如泰国工厂、境内其他省市子公司）；
   - 海关“境内货源地/注册地 = 江苏”绝不等于“中际旭创苏州工厂”——江苏省内同时聚集了天孚通信、亨通、中天、外资模块/器件商、集团内不同报关法人及第三方进出口贸易商，`85.11%` 的省域占比不能当成单一企业份额。两股流最多只是宏观方向互不冲突的平行观察，拼不出闭环。
3. **进料加工只能排除“纯保税仓空转”，不能证明“真产能迁移/非纸面转口”（RT-013）**：
   `2025-01` 至 `2026-06` 期间，全国对马出口中进料加工占比 `70.16%–89.23%`，海关特殊监管区域物流货物与保税监管场所进出境货物两项合计仅 `0.0077%–4.7895%`。
   **诚实边界**：这只能证明**“中国报关侧存在加工贸易保税料件核销，与纯保税物流仓储模式不符”**；至于货物运抵马来西亚后究竟是深度制造、第三方封测、低增值组装后再出口，还是客户海外周转仓调拨，中国出口贸易方式字段完全无法穿透。
4. **“2025-04 迁移拐点”只是样本内月度交叉事实（RT-012）**：
   分伙伴国月度序列仅自 `2025-01` 起算（`2025-01` 对美 `$193.80M` vs 对马 `$73.15M`；`2025-04` 对美 `$95.27M` vs 对马 `$122.97M`，首次反超 `+$27.71M`；`2026-06` 对美 `$61.60M` vs 对马 `$260.43M`）。因缺少 2024 年及更早的分国别月度底稿，且未做统计结构断点或对照品类检验，只允许表述为**“在 2025-01 起的现有分国别序列中，2025-04 首次观察到对马月出口额超过对美”**，严禁渲染为“历史首次”或“精确迁移拐点”。

**终态裁决与重开硬门槛**：
- **判定**：**已推翻（D 级 / 未验证假设 H5）**，不得进入任何承重推论或公司级去向归因。
- **可升级/重开条件**：未来除非拿到以下至少一项硬证据，否则永不恢复判例编号：① 中际旭创马来西亚实体或 PINEWAVE 公告披露具体交易对手方与物理收货地；② 可核验的企业级海关报关单或海运提单（B/L）连接键；③ 同会计期间、同币种口径下经审计闭合的结算流—物流金额桥。

---

## 判例#006 联讯仪器"集团一"（2025Q1 35.51%，通信测试仪器采购方）—— 侦察完成待判定

**槽位**：E096(2025Q1 35.51%)/E097-E098 三年序列（E082 是 Power Master 实名边，
非集团一——红队 Y1-F07 纠正边号事实错误）。**工序阶段**：披露史考古已做（无历史实名
列可比，联讯首次IPO无往年实名年报；公司已于 `2026-04-24` 登陆科创板 `688808`，`2026-01-07` 更新申报稿及 `2026-08-27` 半年报仍维持代号豁免披露未点名）；转金额指纹+产品指纹+程序段落。

**已就位指纹（全部招股书及问询回复 T1 原文）**：
- **金额序列**：472.41(2022)→2,730.72(2023)→13,342.41(2024)→7,140.45(2025Q1) / 10,093.39(2025.1-9)万元，
  应收 6,513.92万元@2025-03-31
- **产品指纹**：采样示波器+时钟恢复单元采购方；50GHz/56GBaud 2023量产验证；
  1.6T三件套(65GHz/120GBaud/1.6Tbps)已验证+正式订单；2018年起合作
- **产能指纹**：400G(单通道100Gbps)光模块2024扩产、下单集中2024Q2-Q3
- **制度事实**：代号披露+毛利豁免+"同一控制下主体合并披露"

**RT-009 / RT-010 口径克制注（方法论硬红线）**：
1. **RT-010 严禁把“未进前五”写成 `0`**：招股书前五大客户表与问询回复之间出现的 `2022 年未列示 vs 472.41 万元` 属于**未解释的产品子表/新老客户统计口径差异**——绝不能因为某年未进入前五大客户披露表，就把真实交易额 `472.41 万元` 写成 `0`（未达披露阈值仅代表右截尾 `censored`，绝非零交易！）。在表注口径完全闭合前，不得擅自定性为单纯“阈值问题”，且**任何跨年增长倍数计算必须从 `2023 年（2,730.72 万元）` 起算**。
2. **RT-009 不可从占比较高或通信仪器指纹推断“必然只对应单一光模块主体”**：
   - 招股书明示按**“同一控制下相关主体合并披露”**，且 `E098`（2023 年）明确记载向集团一销售**“通信测试仪器 + 功率器件测试设备”**——集团一完全可能是横跨光通信与功率半导体的综合电子/通信产业集团、大型 ODM/EMS 代工集团，或集团级共享研发测试平台，严禁越级收敛为“必系某单一纯光模块厂”（更不能因合并披露规则反推其必然由多个法人组成，实体数量公开不可知，Y1-F08）。
   - 联讯侧销售占比高（`2025Q1 35.51%` vs `2025.1-9 12.53%`，系分母期间不同而非数据矛盾）不代表买方侧市场份额排名；且测试仪器在买方账上通常计入**固定资产/在建工程**而非原材料前五大供应商表，外部镜像可见性极低（Y1-F09）。

**陷阱排除**：
- [x] 口径坑1：招股书2025Q1 35.51% vs 二轮问询回复2025.1-9 12.53%（数据期不同，非矛盾）。
- [x] 口径坑2：2022年未进前五表 vs 问询472.41万——按 RT-010 列为未闭合口径差异，严禁写 0，增速自2023起算。
- [x] 直接/终端与多实体：按同一控制下主体合并披露，集团内包含光通信与功率器件需求，具体法人数与拆分不可得。

**判定**：**维持 C 级集团候选（不点名）**——可判断该匿名集团**包含较大规模的 400G/1.6T 光模块及功率器件测试需求，但具体集团身份不可判定**。
**可推翻/升级条件**：① 联讯后续定期报告或专项公告披露集团一区域/主体构成；② 下游买方在固定资产/在建工程或重大合同附注中实名披露联讯仪器采购额并形成唯一金额互锁。
**红线**：严禁点名猜测。产品指纹清晰但排他链未闭合，停在 C 级候选。

---

## 判例#007 太辰光"客户第一名"(2025, 68.48%, 10.59亿元) = Corning 【B级】(v1.6新增)

**槽位**：E232（基准年实边 E165，均挂接太辰光无源器件点 P156）。太辰光2025年报前五大客户表第一名匿名。

**工序路径**：披露史考古（一步，单年实名锚）。

**证据链**：
1. 太辰光2024年报前五大客户表**实名**：Corning Incorporated，965,808,265.22元，
   占比70.10%（E165，原文逐位核验，修复轮F04订正）。锚：https://static.cninfo.com.cn/finalpage/2025-03-29/1222945632.PDF。
2. 太辰光2025年报同表第一名**匿名**：1,059,257,383.43元，占比68.48%（E232）。锚：https://static.cninfo.com.cn/finalpage/2026-03-31/1225061015.PDF。
3. 量级连续：70.10%→68.48%，金额9.658亿→10.59亿，相邻年份高位连续。

**陷阱排除**：
- [x] 会计期：同为自然年年报同表口径。
- [x] 汇率：人民币报表内比对，不涉及。
- [x] 直接/终端：Corning为直接计费客户；其下游用途不可见（身份≠物流穿透）。
- [x] 多实体：Corning Incorporated单一披露主体。
- [x] 含税口径（第六项陷阱）：同公司同表跨年自比，口径一致。
- [ ] **替代解释未严格排除**：2025年第一名理论上可为另一家客户跃升至68.48%
  ——无第二数据源锁定，故不到A级。

**判定**：2025客户第一名 = Corning，**B级**（单一硬证据[2024实名]+量级连续性验证；
无多源互锁）。**2023年第一名（35.70%，3.16亿元）不判定**：与2024年70.10%份额
翻倍，量级不连续，是否同一主体证据不足（D级，留档）。

**可推翻条件**：任何后续披露显示2025年第一名为其他主体；或太辰光重述客户表。
**升级条件**：出现第二独立数据源（如Corning侧披露、出口数据实名匹配）。

**方法论注**：与判例#003（Lumentum同表历史列逐位锁定=A级）对照，本例只有相邻年
单点实名锚，天然封顶B级——"实名窗口关闭前后的考古强度取决于表内是否保留历史列"。
"""


def update_refs_cases_inplace():
    refs_dir = os.path.join(REPO_ROOT, "refs")
    before_files = sorted(os.listdir(refs_dir))
    assert len(before_files) == 8, f"写入前 refs/ 文件数异常: {len(before_files)} -> {before_files}"
    assert "解匿判例库.md" in before_files, "refs/解匿判例库.md 不存在！"

    # 直接原地覆写同一路径（绝不创建 .tmp/.bak 新文件名，保证任意时刻 os.listdir('refs') 恒为 8）
    with open(REFS_CASES_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(CANONICAL_REFS_CASES_MD)

    after_files = sorted(os.listdir(refs_dir))
    assert before_files == after_files and len(after_files) == 8, (
        f"写入后 refs/ 文件列表变化: {after_files}"
    )

    # 校验未破坏 refs/entity-registry.yaml
    with open(ENTITY_REGISTRY_YAML, encoding="utf-8") as yf:
        parsed_yaml = yaml.safe_load(yf)
    assert isinstance(parsed_yaml, dict) and "identity_layer" in parsed_yaml, "entity-registry.yaml 解析异常！"

    return {
        "refs_file_count": len(after_files),
        "refs_files": after_files,
        "entity_registry_yaml_valid": True,
        "cases_md_lines": len(CANONICAL_REFS_CASES_MD.splitlines()),
        "cases_covered": ["#002(A)", "#003(A)", "#004(B终态+U/L定量注)", "#001(留档)", "#005(已推翻反面教材RT-011/014)", "#006(C候选+RT-009/010克制注)", "#007(B)"],
    }


# ---------------------------------------------------------------------------
# 11. 自测断言与汇总输出
# ---------------------------------------------------------------------------
def run_assertions(timeline_rows, cuts_rows, audit_rows, alarm_rows, refs_info):
    # 1) 覆盖全部 E001-E236 零遗漏
    covered_edges = set()
    for r in timeline_rows:
        for eid in (r["source_edge_ids"] or "").split(";"):
            if eid.strip():
                covered_edges.add(eid.strip())
    expected_edges = {f"E{i:03d}" for i in range(1, 237)}
    missing_edges = sorted(expected_edges - covered_edges)
    assert not missing_edges, f"时间线遗漏了 edges.csv 边号: {missing_edges}"

    # 2) 零 flows/out 或 assets/ 归档悬空锚点
    dangling = [
        (r["relation_id"], r["period"], r["anchor_url"])
        for r in timeline_rows
        if "flows/" in r["anchor_url"] or "assets/" in r["anchor_url"] or r["anchor_url"].startswith("同E")
    ]
    assert not dangling, f"存在未清洗悬空锚点: {dangling[:5]}"

    # 3) 三类特殊边显式标签存在且准确
    obs_counts = Counter(r["observe_type"] for r in timeline_rows)
    assert obs_counts["confirmed_ended"] >= 1, "缺失 confirmed_ended 标签(E008)"
    assert obs_counts["procedural_intermediary"] >= 1, "缺失 procedural_intermediary 标签(E016)"
    assert obs_counts["bad_debt_frozen"] == 3, f"E146 bad_debt_frozen 应为3期，实测={obs_counts['bad_debt_frozen']}"

    # 4) E044 双口径对齐核验
    e044_rows = [r for r in timeline_rows if "E044" in r["source_edge_ids"]]
    assert len(e044_rows) == 1
    assert e044_rows[0]["numeric_value"] == "43378" and e044_rows[0]["unit"] == "万美元"
    assert "3,096,780,769.22" in e044_rows[0]["notes"]

    # 5) 期间排序自洽（2020 < 2021H1 < 2021 < 2022H1 < 2023 < 2024 < 2025Q1 < 2025）
    assert (
        period_sort_key("2020", "year")
        < period_sort_key("2021H1", "half_year")
        < period_sort_key("2021", "year")
        < period_sort_key("2022H1", "half_year")
        < period_sort_key("2023", "year")
        < period_sort_key("2024-07-31", "snapshot")
        < period_sort_key("2024-12-13", "snapshot")
        < period_sort_key("2024", "year")
        < period_sort_key("2025Q1", "quarter")
        < period_sort_key("2025", "year")
    ), "期间排序键顺序断言失败！"

    # 6) 负向剔除 74 行 0 泄漏
    assert len(cuts_rows) == 74
    assert all(r["leaked_in_edges_csv"] == "false" for r in cuts_rows)

    # 7) 双侧对账 15 行 & 卖方闹钟 7 行
    assert len(audit_rows) == 15
    assert len(alarm_rows) == 7

    # 8) 解匿判例库必含核心关键词与数字
    with open(REFS_CASES_MD, encoding="utf-8") as f:
        md_txt = f.read()
    for must_have in [
        "## 判例#005（已推翻反面教材）“旭创双流”假设为何不成立【RT-011 证伪留档】",
        "260.431M",
        "221.643M",
        "222.295M",
        "1,272.1M",
        "RT-009",
        "RT-010",
    ]:
        assert must_have in md_txt, f"refs/解匿判例库.md 缺少关键要素: {must_have}"

    assert refs_info["refs_file_count"] == 8


def main():
    timeline_rows, rel_buckets, e100_unpacked_count, eq_stats = build_relationship_timeline()
    cuts_rows, leak_count = build_edge_negative_cuts()
    audit_rows = build_counterparty_audit()
    alarm_rows = build_sellside_watch_alarms()
    refs_info = update_refs_cases_inplace()

    stats_for_readme = {
        "timeline_rows": len(timeline_rows),
        "relation_count": len(rel_buckets),
        "e100_e236_unpacked_rows": e100_unpacked_count,
        "eq_added_count": eq_stats["added_supplementary_count"],
        "cuts_rows": len(cuts_rows),
        "audit_rows": len(audit_rows),
        "alarms_rows": len(alarm_rows),
    }
    build_relationships_readme(stats_for_readme)
    run_assertions(timeline_rows, cuts_rows, audit_rows, alarm_rows, refs_info)

    obs_dist = dict(Counter(r["observe_type"] for r in timeline_rows))
    mk_dist = dict(Counter(r["metric_kind"] for r in timeline_rows))
    ch_dist = dict(Counter(r["source_channel"] for r in timeline_rows))
    cut_cat_dist = dict(Counter(r["cut_category"] for r in cuts_rows))
    alarm_status_dist = dict(Counter(r["alarm_status"] for r in alarm_rows))

    summary = {
        "shard": "Step 2 Task C — Relationships Timeline, Negative Cuts, Audit, Alarms & Refs Case #005",
        "generated_by": "out/step2-archive-salvage-20261121/build_timelines_and_refs.py",
        "outputs": {
            "relationship_timeline_csv": {
                "path": "corpus/relationships/relationship_timeline.csv",
                "total_rows": len(timeline_rows),
                "unique_relations": len(rel_buckets),
                "baseline_r001_r070_rows": 145,
                "e100_e236_edges_count": 137,
                "e100_e236_unpacked_period_rows": e100_unpacked_count,
                "equipment_watch_pool": eq_stats,
                "all_236_edges_covered": True,
                "conflict_rows_count": sum(1 for r in timeline_rows if r["conflict"]),
                "observe_type_distribution": obs_dist,
                "metric_kind_distribution": mk_dist,
                "source_channel_distribution": ch_dist,
            },
            "edge_negative_cuts_csv": {
                "path": "corpus/relationships/edge_negative_cuts.csv",
                "total_rows": len(cuts_rows),
                "unique_directional_pairs": sum(1 for r in cuts_rows if not r["duplicate_of_cut_id"]),
                "leaked_in_edges_csv_count": leak_count,
                "category_distribution": cut_cat_dist,
            },
            "counterparty_audit_csv": {
                "path": "corpus/relationships/counterparty_audit.csv",
                "total_rows": len(audit_rows),
                "audited_pairs": ["P01(弱一致)", "P02(口径不可比_判例#004_B级终态)", "P03(口径不可比_服务费逐位确认_商品并表还原后差~4.9%)"],
                "pending_candidate_pairs": 12,
            },
            "sellside_watch_alarms_csv": {
                "path": "corpus/relationships/sellside_watch_alarms.csv",
                "total_rows": len(alarm_rows),
                "status_distribution": alarm_status_dist,
                "resolved_or_updated": {
                    "W03": "联讯仪器已于2026-04-24登陆科创板(688808)，2026-01-07更新申报稿在案",
                    "W06": "Yole CPO 54亿/121%(Scale-Up自洽口径) vs 81亿/137%(跨子口径拼接)已核实结案 -> macro_evidence.csv#MC035",
                },
                "active_2026_2027_alarms": ["W01", "W02", "W04", "W05", "W07"],
            },
            "relationships_readme_md": {
                "path": "corpus/relationships/README.md",
                "step3_daily_insertion_contract_documented": True,
                "worked_examples": [
                    "罗博特科×NVIDIA 2026-11-16 深交所互动易(qa:300757:2402040011815366656 -> 接续 R057)",
                    "Tower Semiconductor×中际旭创 2026-11-03 官网新闻稿(DC_430D7977BA22 -> NPO合作)",
                ],
            },
            "refs_deanonymization_cases_md": {
                "path": "refs/解匿判例库.md",
                **refs_info,
            },
        },
    }

    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("=" * 72)
    print("Step 2 Shard C 构建与自测全部通过！")
    print(f"  1. relationship_timeline.csv : {len(timeline_rows)} 行 / {len(rel_buckets)} 对关系")
    print(f"     - E001-E099 基线行数      : 145 行 (R001-R070)")
    print(f"     - E100-E236 拆解时序行数  : {e100_unpacked_count} 行 (覆盖全部 137 条边)")
    print(f"     - 设备池补充新增行数      : {eq_stats['added_supplementary_count']} 行 (另 {eq_stats['linked_existing_count']} 行原位关联免重计)")
    print(f"     - observe_type 分布       : {obs_dist}")
    print(f"  2. edge_negative_cuts.csv    : {len(cuts_rows)} 行 (edges.csv 泄漏数 = {leak_count})")
    print(f"  3. counterparty_audit.csv    : {len(audit_rows)} 行 (P01-P15)")
    print(f"  4. sellside_watch_alarms.csv : {len(alarm_rows)} 行 (W01-W07)")
    print(f"  5. refs/解匿判例库.md        : {refs_info['cases_md_lines']} 行 (len(os.listdir('refs')) == {refs_info['refs_file_count']})")
    print("=" * 72)


if __name__ == "__main__":
    main()
