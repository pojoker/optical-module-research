#!/usr/bin/env python3
"""持久 Daily 状态跃迁过滤（种子 + 正向标题规则 + 高置信噪音 + unclassified）与审核队列同步器 (sync_daily_queue.py).

用法:
    PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --build
    PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --check

只读扫描源:
    1. /Users/jowang/Downloads/workflow-rehearsal-daily-state/overseas/staging/2026-* (全量历史快照)
    2. out/daily-backfill-review-20261109/review.json & compliance-audit/audit.json (D-/O-/G- 全量回填审阅)
    3. corpus/_frozen.csv & corpus/annual/ & calls/{universe,watch_entities,company_candidates}.csv

确定性幂等产物 (位于 corpus/daily_review/):
    - review_queue.csv
    - triage_stats.json
    - README.md
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import csv
import glob
import io
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
DAILY_STATE_ROOT = Path("/Users/jowang/Downloads/workflow-rehearsal-daily-state")
OVERSEAS_STAGING_ROOT = DAILY_STATE_ROOT / "overseas" / "staging"
GEMINI_CLOUD_SNAPSHOT_JSON = DAILY_STATE_ROOT / "gemini" / "cloud-snapshot.json"
GEMINI_TRIAGED_THROUGH_DATE = "2026-11-18"
BACKFILL_REVIEW_JSON = ROOT / "out" / "daily-backfill-review-20261109" / "review.json"
COMPLIANCE_AUDIT_JSON = (
    ROOT / "out" / "daily-backfill-review-20261109" / "compliance-audit" / "audit.json"
)

QUEUE_COLUMNS = [
    "queue_id",
    "priority",
    "trigger_type",
    "status",
    "entity_name",
    "stock_or_ticker",
    "source_channel",
    "source_date",
    "title_or_claim",
    "candidate_or_qa_ref",
    "source_url",
    "kb_target_ref",
    "missing_verification_gate",
    "first_seen_at",
    "last_seen_at",
    "resolution_note",
]

VALID_PRIORITIES = {"P0", "P1", "P2"}
VALID_TRIGGER_TYPES = {
    "T1_lifecycle_shift",
    "T2_supply_relationship_or_ma",
    "T3_commitment_verification",
    "T4_universe_blindspot",
}
VALID_STATUSES = {
    "ingested_to_kb",
    "pending_primary_text",
    "pending_filing_anchor",
    "watch_deferred",
}
VALID_KB_PREFIXES = {"points", "edges", "content", "timeline", "calls", "knowledge"}
HIGH_CONFIDENCE_NOISE_CLASSES = {
    "award_ranking_hr_csr",
    "investor_lawsuit_spam",
    "ir_calendar_or_index_page",
    "non_optical_corporate_line",
}
FORBIDDEN_PHRASES = ("已覆盖", "已完成", "已回答")

# 历史人工种子池中的海外 staging 唯一披露 ID 集合 (25 条唯一 DC_*)
SEEDED_OVERSEAS_DC_IDS: dict[str, str] = {
    "DC_66D313EC13F4": "T1_lifecycle_shift",
    "DC_430D7977BA22": "T2_supply_relationship_or_ma",
    "DC_501FC1F61B62": "T2_supply_relationship_or_ma",
    "DC_573401DC530B": "T3_commitment_verification",
    "DC_3841FCD60F32": "T1_lifecycle_shift",
    "DC_FD32C455D502": "T1_lifecycle_shift",
    "DC_7B475AB0DF5A": "T3_commitment_verification",
    "DC_4FAA980A3027": "T1_lifecycle_shift",
    "DC_9B16CE64F492": "T3_commitment_verification",
    "DC_BF393C7C7BE8": "T1_lifecycle_shift",
    "DC_A038F7C2DD93": "T1_lifecycle_shift",
    "DC_286D42235853": "T1_lifecycle_shift",
    "DC_DC1ABE67C305": "T4_universe_blindspot",
    "DC_7CED25D6E66F": "T1_lifecycle_shift",
    "DC_535D459775E6": "T1_lifecycle_shift",
    "DC_741EFE5BF486": "T2_supply_relationship_or_ma",
    "DC_4B0F75924A65": "T1_lifecycle_shift",
    "DC_839378F484E4": "T4_universe_blindspot",
    "DC_D527C3DC5ED2": "T1_lifecycle_shift",
    "DC_E1BEF90B2480": "T1_lifecycle_shift",
    "DC_4A9C0B800414": "T1_lifecycle_shift",
    "DC_DFCE4B441F6E": "T1_lifecycle_shift",
    "DC_91F3D715F522": "T1_lifecycle_shift",
    "DC_4FACD43C676E": "T1_lifecycle_shift",
    "DC_425841A754F4": "T1_lifecycle_shift",
}
# 保留旧名别名以兼容既有调用/测试引用
TRIGGERED_OVERSEAS_DC_IDS = SEEDED_OVERSEAS_DC_IDS

# Step 4 从此前误折叠池挽救入列的核心 10–11 月海外财报/并购/标准披露 (9 条)
RESCUED_OCT_NOV_FOCAL_DC_IDS: tuple[str, ...] = (
    "DC_A6ADDA0BAFA7",  # MTSI FY26Q4
    "DC_58448CDF4801",  # TSEM 2026Q3
    "DC_DB6E7B2D27BB",  # GFS 2026Q3
    "DC_25B37F48DF71",  # VECO 2026Q3
    "DC_6B392C92DA0A",  # VECO x ACLS Merger Closing Update
    "DC_86F8DBF8F95E",  # SOI FY27 H1
    "DC_C85C91649A7A",  # ANET 2026Q3
    "DC_89DB234EEA46",  # CRDO x ORCL OCP Transceiver Telemetry
    "DC_35C4F1F433DF",  # KEYS FY26Q4
)

# 确定性正向标题触发规则：M&A / 代际光互连规格 / 正式财报与 SEC 定期披露
_POS_MA_RE = re.compile(
    r"\b(?:merger|acquire|acquires|acquiring|acquisition|combine|combines|combining)\b",
    re.I,
)
_POS_OPTICAL_TECH_RE = re.compile(
    r"(?:\b800g\b|\b800\s*gb/s\b|\b1\.6t\b|\b3\.2t\b|\b6\.4t\b|"
    r"\bcpo\b|\bnpo\b|\binp\b|indium\s+phosphide|\beml\b|"
    r"silicon\s+photonics|co-packaged|near-package|transceiver)",
    re.I,
)
_POS_EARNINGS_FILING_RE = re.compile(
    r"(?:financial\s+results|quarter(?:ly)?\s+(?:record\s+)?results|"
    r"first[- ]quarter\s+results|second[- ]quarter\s+results|"
    r"third[- ]quarter\s+results|fourth[- ]quarter\s+results|"
    r"fourth\s+quarter\s+and\s+fiscal\s+(?:year\s+)?\d{4}\s+(?:financial\s+)?results|"
    r"half-year\s+results|interim\s+results|full-year\s+results|"
    r"\b10-q\b|\b10-k\b|\b8-k\b)",
    re.I,
)

# 其余已人工初筛确认为非当期核心光芯片/光模块状态跃迁的正向规则命中项 -> watch_deferred 留痕备查
_TRIAGED_DEFERRED_POSITIVE_DC_NOTES: dict[str, str] = {
    "DC_E163D383E32D": "正向标题规则入池(NVDA FY27Q2)：已被更新一期FY27Q3财报(DRQ0023/S_NVDA_2027Q3)接替，归watch_deferred留痕",
    "DC_89ACAD67D4ED": "正向标题规则入池(MRVL FY27Q2)：8月末历史季报快照留痕，待与下一期季报及并购披露滚动对账，归watch_deferred",
    "DC_4C972DDC4FE5": "正向标题规则入池(WATCH_EVG CPO键合综述)：观察池跨行业设备商技术观点稿，无新增客户订单或量产跃迁，归watch_deferred",
    "DC_D0EC3F203C31": "正向标题规则入池(CRDO FY27Q1)：9月初季报快照留痕(AEC电缆为主，光侧1.6T ALC与OCP遥测已单列DRQ0028/DRQ0063)，归watch_deferred",
    "DC_0E691BA9279E": "正向标题规则入池(WATCH_IQE 2026中报)：观察池主体(按watch_entities规则不设四季度槽位，QDL外延协议已单列DRQ0030)，归watch_deferred",
    "DC_662DA8464407": "正向标题规则入池(VIAV ECOC 2026展前预告)：测试仪表展会参展预热稿，无客户认证或商业订单跃迁，归watch_deferred",
    "DC_A58C08820879": "正向标题规则入池(TSEM ECOC 2026展前预告)：晶圆厂展会常规亮点预热(实质NPO/PIC进展已单列DRQ0019/DRQ0025/DRQ0057)，归watch_deferred",
    "DC_DFF557D7FFB5": "正向标题规则入池(CRDO 224G 1.6T光模块扩品)：产品组合扩展通稿留痕(已由既有EV008/EV047体系跟踪)，归watch_deferred",
    "DC_D00353C6F1AA": "正向标题规则入池(WATCH_EXFO LTS-1600发布)：观察池测试设备商通用新品通稿，无具名客户采纳实证，归watch_deferred",
    "DC_4CC6D59845E1": "正向标题规则入池(CRDO ECOC 2026展前预告)：展会参展预热稿，无新增量产状态跃迁，归watch_deferred",
    "DC_81E85DAFD918": "正向标题规则入池(JBL FY26Q4)：综合EMS代工集团财报未单列光模块业务分部，归watch_deferred留痕",
    "DC_5F9601994D31": "正向标题规则入池(CLS DS6005 CPO交换机)：下游交换机整机ODM系统发布(属系统层树外硬件)，归watch_deferred留痕",
    "DC_3B91608B02BC": "正向标题规则入池(WATCH_EXFO 800G验证方案)：观察池测试设备商通用方案发布，无下游模块厂量产绑定披露，归watch_deferred",
    "DC_F002371EBE17": "正向标题规则入池(MRVL 3.2T Retimer与1.6T AEC DSP)：电侧Retimer与有源铜缆AEC DSP芯片发布(非光模块内部oDSP)，归watch_deferred",
    "DC_CCC799AC1E56": "正向标题规则入池(MXL 2026Q3)：综合射频与宽带芯片季报留痕(光侧Jeju PMIC已单列DRQ0042)，归watch_deferred",
    "DC_8FA4374E8CBB": "正向标题规则入池(CAND_AMKR 2026Q3)：候选池通用OSAT封测财报未拆分光学封装收入，归watch_deferred",
    "DC_B4AD13C2BB5A": "正向标题规则入池(CLS 2026Q3)：硬件平台ODM综合季报未单列光器件制造数据，归watch_deferred",
    "DC_1D34B0B79EC8": "正向标题规则入池(CAND_RBBN 2026Q3)：候选池电信传输设备商季报，归watch_deferred留痕",
    "DC_34A699E641E0": "正向标题规则入池(GLW 2026Q3)：康宁集团综合季报留痕(光通信分部口径含运营商光缆，AI合作已单列DRQ0040)，归watch_deferred",
    "DC_4742BF9D9AB4": "正向标题规则入池(ASMPT 2026Q3)：泛半导体与SMT装备综合季报未单列光模块设备订单，归watch_deferred",
    "DC_495585B683DC": "正向标题规则入池(CAND_DELTA 2026Q3)：候选池电源与散热集团季报，归watch_deferred留痕",
    "DC_55807AE9FFD3": "正向标题规则入池(WATCH_MSFT FY27Q1)：云巨头观察池主体(按watch_entities边界不设光学季度槽位，一般CapEx不映射光模块)，归watch_deferred",
    "DC_D989B8044EE7": "正向标题规则入池(FORM 2026Q3)：半导体探针卡综合季报未单列硅光晶圆测试收入，归watch_deferred",
    "DC_5BE0AA94B61E": "正向标题规则入池(SMOP 2026Q3)：区域开放光网络设备商季报留痕，归watch_deferred",
    "DC_999409CE7860": "正向标题规则入池(WATCH_AMZN 2026Q3)：AWS观察池主体(按watch_entities边界无光学细节时不建事件)，归watch_deferred",
    "DC_54E9F3CCB09D": "正向标题规则入池(WATCH_MELCO FY27H1)：三菱电机集团合并财报无法分离EML光器件收入(见watch_entities边界)，归watch_deferred",
    "DC_6F79EB0E2059": "正向标题规则入池(ADTN 2026Q3)：接入与城域电信传输设备季报留痕，归watch_deferred",
    "DC_7351A647DA52": "正向标题规则入池(WATCH_AMD 2026Q3)：算力平台观察池主体(集团季报不含具体光学BOM)，归watch_deferred",
    "DC_B1A977AE0CA6": "正向标题规则入池(WATCH_MCHP FY27Q2)：电侧PHY/Retimer观察池主体(按watch_entities边界不建光侧事件)，归watch_deferred",
    "DC_5F8463A3354D": "正向标题规则入池(SANM FY26Q4)：综合电子制造服务EMS季报未单列光模块代工数据，归watch_deferred",
    "DC_8A0DEBAD0244": "正向标题规则入池(WIWYNN 2026Q3)：AI服务器ODM综合季报(OCP光互连演示已单列DRQ0026/DRQ0041)，归watch_deferred",
    "DC_2FCCEE890B99": "正向标题规则入池(OXIG FY27H1)：精密等离子体与科学仪器集团半年报未单列InP光芯片刻蚀收入，归watch_deferred",
    "DC_6C5812B7A496": "正向标题规则入池(OXIG FY26年报重发项)：已被同日披露的FY27H1半年报(DC_2FCCEE890B99)接替，归watch_deferred",
}


def _load_tracked_overseas_entities() -> tuple[set[str], dict[str, str]]:
    """读取 calls/{universe,watch_entities,company_candidates}.csv 中的受追踪海外实体集合与显示名称."""
    tracked: set[str] = set()
    names: dict[str, str] = {}
    specs = (
        ("universe.csv", "company_id", "company_name"),
        ("watch_entities.csv", "entity_id", "canonical_name"),
        ("company_candidates.csv", "candidate_id", "canonical_name"),
    )
    for fname, id_col, name_col in specs:
        p = ROOT / "calls" / fname
        if p.exists():
            with p.open("r", encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    eid = (r.get(id_col) or "").strip()
                    nm = (r.get(name_col) or eid).strip()
                    if eid:
                        tracked.add(eid)
                        names.setdefault(eid, nm)
    return tracked, names


def _classify_overseas_noise(row: dict[str, str]) -> str:
    """仅识别四类明确高置信噪音；凡未命中高置信噪音规则的条目一律返回 'unclassified'（严禁默认静默归入噪音）."""
    title_l = (row.get("title") or "").lower()
    url_l = (row.get("canonical_url") or "").lower()

    if any(
        kw in title_l
        for kw in (
            "investigation",
            "lawsuit",
            "class action",
            "securities investors",
            "encouraged to contact",
            "llp",
            "suewallst",
            "bronstein",
            "kirby mcinerney",
        )
    ):
        return "investor_lawsuit_spam"

    if any(
        kw in title_l
        for kw in (
            "forbes",
            "time's",
            "best companies",
            "top manufacturers",
            "honored",
            "award",
            "appoints",
            "adds former ",
            "chief ",
            "cfo succession",
            "board of directors",
            "independent directors",
            "career",
            "mentorship",
            "donation",
            "sustainability",
        )
    ):
        return "award_ranking_hr_csr"

    if any(
        kw in title_l
        for kw in (
            "sec filings",
            "reporting date",
            "upcoming event",
            "upcoming investor",
            "upcoming financial conference",
            "sets conference call",
            "sets the date",
            "schedules ",
            "to webcast",
            "to release ",
            "to hold ",
            "announces conference call",
            "announces date for",
            "announces timing of",
            "announces third quarter 2026 financial results and conference call",
            "to participate in",
            "to present at",
            "to announce ",
            "to report ",
            "change of date",
            "ändrat datum",
            "annual meeting of stockholders",
            "investor day meeting to be held",
            "availability of ",
            "web broadcast",
            "media alert",
            "financial community",
        )
    ) or url_l.endswith("/sec-filings"):
        return "ir_calendar_or_index_page"

    if any(
        kw in title_l
        for kw in (
            "vmware",
            "tanzu",
            "spring security",
            "splunk",
            "webex",
            "agentminder",
            "deepfield",
            "patent license",
            "5g ",
            "fixed wireless access",
            "broadband cooperative",
            "healthcare",
            "mining",
            "geforce",
            "gaming",
            "dlss",
            "robotics",
            "omniverse",
            "automotive",
            "spaceflight",
            "vorago",
            "hailo",
            "world labs",
        )
    ):
        return "non_optical_corporate_line"

    return "unclassified"


def _classify_overseas_positive_rule(
    row: dict[str, str],
    tracked_entities: set[str] | None = None,
) -> str | None:
    """对非高置信噪音的在册/观察/候选实体执行确定性正向标题触发规则."""
    if _classify_overseas_noise(row) != "unclassified":
        return None
    pub = (row.get("publisher_entity_id") or "").strip()
    if tracked_entities is not None and pub and pub not in tracked_entities:
        return None
    title = (row.get("title") or "").strip()
    if not title:
        return None
    if _POS_MA_RE.search(title):
        return "T2_supply_relationship_or_ma"
    if _POS_OPTICAL_TECH_RE.search(title):
        if pub.startswith(("WATCH_", "CAND_")):
            return "T4_universe_blindspot"
        return "T1_lifecycle_shift"
    if _POS_EARNINGS_FILING_RE.search(title):
        if pub.startswith(("WATCH_", "CAND_")):
            return "T4_universe_blindspot"
        return "T1_lifecycle_shift"
    return None


def scan_overseas_staging() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """全量扫描 overseas/staging/ 全部历史快照目录，返回唯一 DC 索引与四桶透明分流统计."""
    snap_dirs = sorted(
        Path(p)
        for p in glob.glob(str(OVERSEAS_STAGING_ROOT / "2026-*"))
        if os.path.isdir(p)
    )
    if not snap_dirs:
        raise FileNotFoundError(f"未找到海外 staging 快照目录: {OVERSEAS_STAGING_ROOT}")

    tracked_entities, _ = _load_tracked_overseas_entities()

    dc_index: dict[str, dict[str, Any]] = {}
    claim_cand_ids: set[str] = set()
    event_cand_ids: set[str] = set()
    claim_cands_by_dc: dict[str, list[dict[str, str]]] = {}

    for sd in snap_dirs:
        snap_date = sd.name
        dc_file = sd / "disclosure_candidates.csv"
        if dc_file.exists():
            with dc_file.open("r", encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    did = (r.get("disclosure_id") or "").strip()
                    if not did:
                        continue
                    if did not in dc_index:
                        dc_index[did] = {
                            "row": r,
                            "first_seen": snap_date,
                            "last_seen": snap_date,
                            "snapshot_Appearances": 1,
                        }
                    else:
                        dc_index[did]["last_seen"] = snap_date
                        dc_index[did]["snapshot_Appearances"] += 1
                        dc_index[did]["row"] = r

        cc_file = sd / "claim_candidates.csv"
        if cc_file.exists():
            with cc_file.open("r", encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    cid = (r.get("event_claim_id") or "").strip()
                    did = (r.get("disclosure_id") or "").strip()
                    if cid and cid not in claim_cand_ids:
                        claim_cand_ids.add(cid)
                        if did:
                            claim_cands_by_dc.setdefault(did, []).append(r)

        ec_file = sd / "event_candidates.csv"
        if ec_file.exists():
            with ec_file.open("r", encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    eid = (r.get(next(iter(r.keys()))) or "").strip() if r else ""
                    if eid:
                        event_cand_ids.add(eid)

    latest_dir = snap_dirs[-1]
    latest_date = latest_dir.name
    latest_dids: set[str] = set()
    latest_dc_file = latest_dir / "disclosure_candidates.csv"
    if latest_dc_file.exists():
        with latest_dc_file.open("r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                did = (r.get("disclosure_id") or "").strip()
                if did:
                    latest_dids.add(did)

    noise_counter_all: Counter[str] = Counter()
    noise_counter_sep_nov: Counter[str] = Counter()
    trigger_counter_all: Counter[str] = Counter()
    trigger_counter_sep_nov: Counter[str] = Counter()
    seeded_all = 0
    seeded_sep_nov = 0
    pos_rule_all = 0
    pos_rule_sep_nov = 0
    unclassified_all = 0
    unclassified_sep_nov = 0
    sep_nov_total = 0
    positive_rule_dc_ids: list[str] = []

    for did, info in sorted(dc_index.items()):
        r = info["row"]
        pub_date = (r.get("published_at") or "").strip()
        is_sep_nov = pub_date >= "2026-09-01"
        if is_sep_nov:
            sep_nov_total += 1
        if did in SEEDED_OVERSEAS_DC_IDS:
            ttype = SEEDED_OVERSEAS_DC_IDS[did]
            info["triage_bucket"] = "seeded"
            info["trigger_type"] = ttype
            seeded_all += 1
            trigger_counter_all[ttype] += 1
            if is_sep_nov:
                seeded_sep_nov += 1
                trigger_counter_sep_nov[ttype] += 1
        else:
            pos_ttype = _classify_overseas_positive_rule(r, tracked_entities=tracked_entities)
            if pos_ttype is not None:
                info["triage_bucket"] = "positive_rule"
                info["trigger_type"] = pos_ttype
                positive_rule_dc_ids.append(did)
                pos_rule_all += 1
                trigger_counter_all[pos_ttype] += 1
                if is_sep_nov:
                    pos_rule_sep_nov += 1
                    trigger_counter_sep_nov[pos_ttype] += 1
            else:
                nreason = _classify_overseas_noise(r)
                info["triage_bucket"] = nreason
                if nreason == "unclassified":
                    unclassified_all += 1
                    if is_sep_nov:
                        unclassified_sep_nov += 1
                else:
                    noise_counter_all[nreason] += 1
                    if is_sep_nov:
                        noise_counter_sep_nov[nreason] += 1

    total_all = len(dc_index)
    trig_all = seeded_all + pos_rule_all
    noise_all = sum(noise_counter_all.values())
    trig_sep_nov = seeded_sep_nov + pos_rule_sep_nov
    noise_sep_nov = sum(noise_counter_sep_nov.values())

    if trig_all + noise_all + unclassified_all != total_all:
        raise AssertionError("全量海外分流计数不闭合")
    if trig_sep_nov + noise_sep_nov + unclassified_sep_nov != sep_nov_total:
        raise AssertionError("9-11月海外分流计数不闭合")

    all_triggered_set = set(SEEDED_OVERSEAS_DC_IDS) | set(positive_rule_dc_ids)
    slid_out_triggered = sorted(
        did for did in all_triggered_set if did in dc_index and did not in latest_dids
    )

    missing_focal = [did for did in RESCUED_OCT_NOV_FOCAL_DC_IDS if did not in positive_rule_dc_ids]
    if missing_focal:
        raise ValueError(f"正向标题规则未命中必救 10-11 月重点披露: {missing_focal}")

    stats = {
        "snapshot_count": len(snap_dirs),
        "snapshot_start_date": snap_dirs[0].name,
        "snapshot_end_date": latest_date,
        "unique_disclosure_candidates_all": total_all,
        "unique_claim_candidates_all": len(claim_cand_ids),
        "unique_event_candidates_all": len(event_cand_ids),
        "active_in_latest_rolling_window": len(latest_dids),
        "slid_out_of_rolling_window_total": total_all - len(latest_dids),
        "seeded_plus_positive_rules_split": {
            "total_unique_disclosures": total_all,
            "seeded_triggered_count": seeded_all,
            "positive_rule_triggered_count": pos_rule_all,
            "triggered_total_count": trig_all,
            "triggered_total_pct": round(trig_all / total_all * 100.0, 2),
            "high_confidence_noise_count": noise_all,
            "high_confidence_noise_pct": round(noise_all / total_all * 100.0, 2),
            "unclassified_count": unclassified_all,
            "unclassified_pct": round(unclassified_all / total_all * 100.0, 2),
            "noise_breakdown": dict(sorted(noise_counter_all.items())),
            "trigger_breakdown": dict(sorted(trigger_counter_all.items())),
        },
        "sep_to_nov_2026_seeded_plus_positive_rules_split": {
            "total_unique_disclosures": sep_nov_total,
            "seeded_triggered_count": seeded_sep_nov,
            "positive_rule_triggered_count": pos_rule_sep_nov,
            "triggered_total_count": trig_sep_nov,
            "triggered_total_pct": round(trig_sep_nov / sep_nov_total * 100.0, 2),
            "high_confidence_noise_count": noise_sep_nov,
            "high_confidence_noise_pct": round(noise_sep_nov / sep_nov_total * 100.0, 2),
            "unclassified_count": unclassified_sep_nov,
            "unclassified_pct": round(unclassified_sep_nov / sep_nov_total * 100.0, 2),
            "noise_breakdown": dict(sorted(noise_counter_sep_nov.items())),
            "trigger_breakdown": dict(sorted(trigger_counter_sep_nov.items())),
        },
        "rescued_oct_nov_focal_count": len(RESCUED_OCT_NOV_FOCAL_DC_IDS),
        "rescued_oct_nov_focal_dc_ids": list(RESCUED_OCT_NOV_FOCAL_DC_IDS),
        "positive_rule_triggered_dc_ids": positive_rule_dc_ids,
        "slid_out_triggered_rescued_count": len(slid_out_triggered),
        "slid_out_triggered_rescued_dc_ids": slid_out_triggered,
    }
    for did, ccs in claim_cands_by_dc.items():
        if did in dc_index:
            dc_index[did]["claim_candidates"] = ccs
    return dc_index, stats


def scan_backfill_review() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """读取 out/daily-backfill-review-20261109/review.json 与 compliance-audit/audit.json 并统计."""
    items = json.loads(BACKFILL_REVIEW_JSON.read_text(encoding="utf-8"))
    comp_items = json.loads(COMPLIANCE_AUDIT_JSON.read_text(encoding="utf-8"))

    by_id: dict[str, dict[str, Any]] = {x["id"]: x for x in items}
    prefix_counts = Counter(x["id"].split("-")[0] + "-" for x in items)
    disp_counts = Counter(x.get("disposition", "") for x in items)
    stream_counts = Counter(x.get("stream", "") for x in items)

    rev_items = [x for x in items if x.get("disposition") == "待逐条复核"]
    o_rev = [x for x in rev_items if x["id"].startswith("O-")]
    d_rev = [x for x in rev_items if x["id"].startswith("D-")]

    o_unique_dcs = {x.get("source_disclosure_id") or x["id"] for x in o_rev}
    d_unique_groups = {
        (
            x.get("subject", ""),
            x.get("category", ""),
            re.sub(r"\s+", "", (x.get("quote") or x.get("claim") or ""))[:80],
        )
        for x in d_rev
    }
    d_non_recall_groups = {k for k in d_unique_groups if k[1] != "召回候选"}

    generic_templates = {
        "核对公司回复是否明确覆盖同一产品、工序和阶段，再选择补证或修正旧点。",
        "核对该段的披露主体、产品和阶段，符合原判定口径时补充相应点的带日期证据。",
        "先区分发行人自有业务、客户业务与技术名词，再判断是否补充现有叶格。",
    }
    bespoke_rev_ids = sorted(
        x["id"] for x in rev_items if (x.get("proposal") or "") not in generic_templates
    )

    folded_backfill = sum(
        1 for x in items if x.get("disposition") in ("仅作线索", "待定位", "缺锚点")
    ) + sum(1 for x in d_rev if x.get("category") == "召回候选")

    stats = {
        "source_file": "out/daily-backfill-review-20261109/review.json",
        "total_rows": len(items),
        "by_prefix": dict(sorted(prefix_counts.items())),
        "by_stream": dict(sorted(stream_counts.items())),
        "by_disposition": dict(sorted(disp_counts.items())),
        "compliance_audit_g_items": len(comp_items),
        "review_disposition_total": len(rev_items),
        "overseas_o_review_rows": len(o_rev),
        "overseas_o_deduplicated_disclosures": len(o_unique_dcs),
        "domestic_d_review_rows": len(d_rev),
        "domestic_d_deduplicated_groups": len(d_unique_groups),
        "domestic_d_non_mechanical_groups": len(d_non_recall_groups),
        "bespoke_high_signal_review_rows": len(bespoke_rev_ids),
        "auto_folded_clue_or_mechanical_rows": folded_backfill,
        "auto_folded_pct": round(folded_backfill / len(items) * 100.0, 2),
    }
    return by_id, stats


def scan_gemini_cloud_snapshot(
    snapshot_path: Path | None = None,
    triaged_through_date: str = GEMINI_TRIAGED_THROUGH_DATE,
) -> dict[str, Any]:
    """只读检查 Gemini 云端日更快照水位（文件缺失或异常时优雅降级返回 available=False）."""
    path = snapshot_path if snapshot_path is not None else GEMINI_CLOUD_SNAPSHOT_JSON
    if not path.is_file():
        return {
            "available": False,
            "snapshot_path": str(path),
            "triaged_through_date": triaged_through_date,
            "total_daily_entries": 0,
            "unique_entry_dates_count": 0,
            "entry_dates": [],
            "earliest_entry_date": None,
            "latest_entry_date": None,
            "untriaged_entry_dates": [],
            "untriaged_entry_count": 0,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "available": False,
            "snapshot_path": str(path),
            "error": str(exc),
            "triaged_through_date": triaged_through_date,
            "total_daily_entries": 0,
            "unique_entry_dates_count": 0,
            "entry_dates": [],
            "earliest_entry_date": None,
            "latest_entry_date": None,
            "untriaged_entry_dates": [],
            "untriaged_entry_count": 0,
        }

    content = str(payload.get("content") or "")
    raw_dates = re.findall(r"\[(\d{4}-\d{2}-\d{2})\]", content)
    unique_dates = sorted(set(raw_dates))
    untriaged_dates = [d for d in unique_dates if d > triaged_through_date]
    return {
        "available": True,
        "snapshot_path": str(path),
        "title": str(payload.get("title") or ""),
        "retrieved_at": str(payload.get("retrieved_at") or ""),
        "original_modified_at": str(payload.get("original_modified_at") or ""),
        "total_daily_entries": len(raw_dates),
        "unique_entry_dates_count": len(unique_dates),
        "entry_dates": unique_dates,
        "earliest_entry_date": unique_dates[0] if unique_dates else None,
        "latest_entry_date": unique_dates[-1] if unique_dates else None,
        "triaged_through_date": triaged_through_date,
        "untriaged_entry_dates": untriaged_dates,
        "untriaged_entry_count": len(untriaged_dates),
    }


def _check_kerui_in_frozen_and_annual() -> bool:
    """检查 002957 科瑞技术 是否已在 corpus/_frozen.csv 且 corpus/annual/002957 含有效 PDF."""
    frozen_path = ROOT / "corpus" / "_frozen.csv"
    in_frozen = False
    if frozen_path.exists():
        with frozen_path.open("r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("代码") or "").strip() == "002957":
                    in_frozen = True
                    break
    annual_002957 = ROOT / "corpus" / "annual" / "002957"
    has_pdf = False
    if annual_002957.is_dir():
        for dp, _, fns in os.walk(annual_002957, followlinks=True):
            for fn in fns:
                if fn.lower().endswith(".pdf"):
                    fp = Path(dp) / fn
                    if fp.stat().st_size > 10000:
                        has_pdf = True
                        break
    return in_frozen and has_pdf


def _dc_meta(
    dc_index: dict[str, dict[str, Any]],
    did: str,
    fallback_date: str,
    fallback_url: str,
    fallback_title: str,
) -> tuple[str, str, str, str, str]:
    info = dc_index.get(did)
    if not info:
        return fallback_date, fallback_title, fallback_url, fallback_date, fallback_date
    r = info["row"]
    return (
        (r.get("published_at") or fallback_date).strip(),
        (r.get("title") or fallback_title).strip(),
        (r.get("canonical_url") or fallback_url).strip(),
        info["first_seen"],
        info["last_seen"],
    )


def build_queue_rows(
    dc_index: dict[str, dict[str, Any]],
    kerui_in_frozen: bool,
) -> list[dict[str, str]]:
    """构造确定性持久审核队列行 (保持 DRQ0001..DRQ0055 编号稳定，新增 DRQ0056+ 挽救项)."""
    _, entity_names = _load_tracked_overseas_entities()
    raw_specs: list[dict[str, str]] = []

    def add(
        priority: str,
        trigger_type: str,
        status: str,
        entity_name: str,
        stock_or_ticker: str,
        source_channel: str,
        source_date: str,
        title_or_claim: str,
        candidate_or_qa_ref: str,
        source_url: str,
        kb_target_ref: str,
        missing_verification_gate: str,
        first_seen_at: str,
        last_seen_at: str,
        resolution_note: str,
    ) -> None:
        raw_specs.append(
            {
                "priority": priority,
                "trigger_type": trigger_type,
                "status": status,
                "entity_name": entity_name,
                "stock_or_ticker": stock_or_ticker,
                "source_channel": source_channel,
                "source_date": source_date,
                "title_or_claim": title_or_claim.replace("\n", " ").replace("\r", " ").strip(),
                "candidate_or_qa_ref": candidate_or_qa_ref.strip(),
                "source_url": source_url.strip(),
                "kb_target_ref": kb_target_ref.strip(),
                "missing_verification_gate": missing_verification_gate.replace("\n", " ").strip(),
                "first_seen_at": first_seen_at.strip(),
                "last_seen_at": last_seen_at.strip(),
                "resolution_note": resolution_note.replace("\n", " ").strip(),
            }
        )

    # =========================================================================
    # DRQ0001 .. DRQ0014 (既有已入库高优项，保持原位编号)
    # =========================================================================
    add(
        "P0",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "联讯仪器",
        "688808",
        "cninfo_ipo_and_h1",
        "2026-08-27",
        "科创板2026-04-24上市(688808)转正入v6宇宙分母；2026半年报第17页证实1.6T光模块测试核心四件套量产供货",
        "V01_20261119;IPO_688808_2026",
        "https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF#page=17",
        "points:P061",
        "",
        "2026-08-27",
        "2026-11-21",
        "v6分母纳入688808并落盘招股书与半年报旁车(corpus/annual/688808)，points.csv P061上市标签由未上市私企更新为A股",
    )
    add(
        "P0",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "云南锗业",
        "002428",
        "cninfo_annual_report",
        "2026-04-23",
        "母公司云南锗业(002428)纳入v6宇宙分母并建立子公司云南鑫耀(P202)别名归并；2025年报披露全年生产磷化铟晶片10.01万片",
        "N01_20261119;ANNUAL_002428_2025",
        "https://static.cninfo.com.cn/finalpage/2026-04-23/1225152695.PDF",
        "points:P202",
        "",
        "2026-04-23",
        "2026-11-21",
        "2025/2024年报PDF与.pdf.txt旁车已入corpus/annual/002428并纳入_frozen.csv，participation.py归并云南鑫耀P202至云南锗业",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "罗博特科",
        "300757",
        "domestic_ir_and_qa",
        "2026-11-16",
        "10/29投关与11/02-16互动易：现款INS2/INS3已批量交付(辟谣取消传闻)、INS4处NPI；11/16首次书面确认英伟达系ficonTEC客户之一(批量归属受NDA限制)；瑞士7867万元整线属OCS非CPO",
        "D-8672aa1efe029f;QA_300757_20261116_L1464;QA_300757_20250915_L563",
        "http://www.cninfo.com.cn/new/disclosure/stock?stockCode=300757",
        "points:P059;points:P172;points:P173;content:CLG0602;content:CLG0603;content:CLG0604;content:CLG0605;timeline:TL9001;timeline:TL9004",
        "",
        "2026-10-29",
        "2026-11-16",
        "已同步300757投关与去重问答，更新P059/P172/P173进展边界、写入CLG0602-CLG0605与关系时间线TL9001/TL9004",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "天孚通信",
        "300394",
        "domestic_ir_and_qa",
        "2026-10-29",
        "10/29投关纪要：CPO配套FAU/ELS进入稳定量产交付；NPO配套仍处客户前期开发送样、预计2027年逐步上量(CPO与NPO严格分账)",
        "D-0901bdece090a3;D-90425e894cef11;D-3ab755e13ffaf0",
        "http://www.cninfo.com.cn/new/disclosure/stock?stockCode=300394",
        "points:P271;points:P155;content:CLG0606;content:CLG0607;content:CLG0608",
        "",
        "2026-10-22",
        "2026-10-29",
        "已同步300394 10月系列投关PDF与旁车文本，按CPO稳定交付与NPO 2027预期分列更新P271/P155与CLG0606-CLG0608",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "中际旭创",
        "300308",
        "domestic_ir_and_qa",
        "2026-11-03",
        "10/29及11/03投关纪要：定调NPO 2027年处NPI爬坡、2027H2逐步上量、2028年规模释放(否证2026起量传言)；9月底泰国强降雨致部分发货顺延至10月初，约30亿美元存货主要系提前备料",
        "D-9745b1e90af732;D-5eb517c4d2f5ea",
        "http://www.cninfo.com.cn/new/disclosure/stock?stockCode=300308",
        "points:P074;points:P138;content:CLG0598;content:CLG0599;content:CLG0600;content:CLG0601;timeline:TL9002",
        "",
        "2026-10-29",
        "2026-11-03",
        "已同步300308 10/29与11/03投关原件及问答，更新P074/P138、写入CLG0598-CLG0601并作为TL9002起量时点硬约束",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "新易盛",
        "300502",
        "domestic_ir_and_qa",
        "2026-11-12",
        "10/29投关及11/10-12互动易：9月末受泰国洪灾物流扰动部分发运顺延至10月确收，Q3产量环比增长、1.6T于Q4放量明显、NPO预计2027年批量",
        "D-63589e7953f6b9;D-02f691b20048d5;QA_300502_20261112",
        "http://www.cninfo.com.cn/new/disclosure/stock?stockCode=300502",
        "points:P073;content:CLG0609;content:CLG0610;content:CLG0611",
        "",
        "2026-09-11",
        "2026-11-12",
        "已同步300502 09/11与10/29投关及11月互动易快照，更新P073跨期确收与1.6T/NPO节奏并写入CLG0609-CLG0611",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "剑桥科技",
        "603083",
        "domestic_qa",
        "2026-11-10",
        "11/10互动易：越南部分产线已通过客户审核落地，9月初高速光模块设计产能约100万支/月，1.6T产品已在3家客户测试",
        "QA_603083_20261110",
        "https://sns.sseinfo.com/",
        "points:P077;content:CLG0614;content:CLG0615;content:CLG0616",
        "",
        "2026-11-10",
        "2026-11-10",
        "已同步603083问答并剔除同文重复行，更新P077越南产线过审产能与1.6T三家客户测试进展并写入CLG0614-CLG0616",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "炬光科技",
        "688167",
        "cninfo_offering_prospectus",
        "2026-11-05",
        "11/05定增募集说明书第86页：大于36通道光纤定位V型槽部分客户由验证转入批量交付；MPLA微棱镜透镜阵列与核心客户签署并执行技术许可协议(严格区隔授权与硬件销量)",
        "FILING_688167_20261105_P86",
        "https://static.cninfo.com.cn/finalpage/2026-11-05/1225658451.PDF#page=86",
        "points:P117;points:P169;content:CLG0626;timeline:TL9003",
        "",
        "2026-11-05",
        "2026-11-19",
        "已核对募集说明书第86页原文，更新P117/P169、写入CLG0626并记入关系时间线TL9003",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "博众精工",
        "688097",
        "cninfo_h1_and_qa",
        "2026-11-17",
        "2026半年报p.54/p.211与10/16、11/17互动易：2.86亿元控股收购中南鸿思60%股权已于2026-02-28交割，获NPO/CPO自动耦合设备订单即将交付；与苏州博众半导体共晶贴片分主体建档并保留订单不等同收入警示",
        "FILING_688097_2026H1_P54;QA_688097_20261117",
        "https://sns.sseinfo.com/",
        "points:P206;content:CLG0617;content:CLG0618;timeline:TL9005",
        "",
        "2026-08-25",
        "2026-11-17",
        "已去重同步688097问答并核实半年报交割页码，分主体更新P206、写入CLG0617-CLG0618与关系时间线TL9005",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "华工科技",
        "000988",
        "domestic_qa",
        "2026-11-05",
        "11/05互动易：2026前三季度光互联业务营收65.39亿元(+26%)、净利5.66亿元(+30%)、Q3单季净利2.9亿元(+201% QoQ)及上游核心物料偏紧，同时标明与2025年报光电器件系列产品统计边界差异",
        "QA_000988_20261105",
        "https://irm.cninfo.com.cn/",
        "points:P209;content:CLG0612;content:CLG0613",
        "",
        "2026-11-05",
        "2026-11-05",
        "仅在P209备注追加11/05互动易光互联口径数据与年报分部边界说明并写入CLG0612-CLG0613，未改动P209原引语及核心历史数字",
    )

    csco_dt, csco_title, csco_url, csco_fs, csco_ls = _dc_meta(
        dc_index,
        "DC_66D313EC13F4",
        "2026-10-12",
        "https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m10/cisco-advances-scalability-and-openness-at-ocp-2026.html",
        "Cisco Advances Scalability and Openness at OCP 2026",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Cisco",
        "CSCO",
        "overseas_official_release",
        csco_dt,
        f"{csco_title}：OCP 2026官方确认搭载102.4T Silicon One G300的首批交换系统正在向客户发货(currently shipping to customers)",
        "DC_66D313EC13F4;O-4419fb50d94d248a0759",
        csco_url,
        "calls:D_CSCO_20261012_OCP_G300;calls:ECL038;calls:EV035;calls:EE038",
        "",
        csco_fs,
        csco_ls,
        "经Cisco新闻室一手原文逐字核验并入海外事件账本D_CSCO_20261012_OCP_G300/EV035",
    )
    add(
        "P0",
        "T3_commitment_verification",
        "ingested_to_kb",
        "Applied Optoelectronics(AAOI)",
        "AAOI",
        "overseas_earnings_call",
        "2026-08-06",
        "CM002承诺到期裁决：AAOI 2026Q2官方新闻稿CEO引语证实800G出货量环比翻倍以上增长(strong volume ramp... more than doubled sequentially)，兑现Q2放量承诺",
        "COMMITMENT_CM002;S_AAOI_2026Q2",
        "https://investors.ao-inc.com/2026-05-07-Applied-Optoelectronics-Reports-First-Quarter-2026-Results",
        "calls:CM002;calls:S_AAOI_2026Q2;calls:CL075;calls:S_AAOI_Q1_RESULT_A",
        "",
        "2026-08-06",
        "2026-11-11",
        "修复S_AAOI_Q1_RESULT_A永久官方URL，新增CL075并将CM002裁决为fulfilled(Q3后续扩产延期单列说明)",
    )
    add(
        "P0",
        "T3_commitment_verification",
        "ingested_to_kb",
        "Ciena",
        "CIEN",
        "overseas_investor_forum",
        "2026-09-16",
        "CM007承诺到期裁决：Ciena 2026-09-16 Investor Forum逐字稿p.24证实Vesta 200 CPX正面向多家关键客户送样评估(sampling devices for multiple key customers)",
        "COMMITMENT_CM007;S_CIEN_2026_FORUM",
        "https://investor.ciena.com/",
        "calls:CM007;calls:S_CIEN_2026_FORUM;calls:CL076",
        "",
        "2026-09-16",
        "2026-11-11",
        "新增S_CIEN_2026_FORUM与CL076，CM007由not_observed更新为partially_fulfilled(Q2首次可提供日仍未知)",
    )

    tsem_dt, tsem_title, tsem_url, tsem_fs, tsem_ls = _dc_meta(
        dc_index,
        "DC_430D7977BA22",
        "2026-11-03",
        "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/",
        "Tower Semiconductor and Innolight Advance High-Performance Near-Package Optics for AI Infrastructure",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "Tower Semiconductor × 中际旭创",
        "TSEM/300308",
        "overseas_official_release",
        tsem_dt,
        f"{tsem_title}（官网全文第3/7段逐字锚定PH18M 200mm早期生产与300mm多款流片，配中际旭创11/03投关NPO 2027H2起量边界）",
        "DC_430D7977BA22",
        tsem_url,
        "calls:D_TSEM_20261103_INNOLIGHT_NPO;calls:ECL039;calls:EV036;calls:EE039;timeline:TL9002",
        "",
        tsem_fs,
        tsem_ls,
        "已协同DRQ0019归档Tower官网全文(tsem_20261103_innolight_npo.txt)并升级D_TSEM_20261103_INNOLIGHT_NPO/EV036/TL9002为正文逐字引语",
    )

    # =========================================================================
    # DRQ0015 .. DRQ0046 (Step 4 原文抓核与国内投关回读裁决刷新，保持原位编号)
    # =========================================================================
    mrvl_dt, mrvl_title, mrvl_url, mrvl_fs, _ = _dc_meta(
        dc_index,
        "DC_501FC1F61B62",
        "2026-11-02",
        "https://investor.marvell.com/news-events/press-releases/detail/1040/marvell-and-lumentum-to-combine-creating-a-category-leader-in-ai-connectivity",
        "Marvell and Lumentum to Combine, Creating a Category Leader in AI Connectivity",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "Marvell × Lumentum",
        "MRVL/LITE",
        "overseas_official_release",
        mrvl_dt,
        f"{mrvl_title}（全股票协议1股LITE换4.500股MRVL，隐含企业价值1150亿美元，预计H1 CY2028交割、当前未交割）",
        "DC_501FC1F61B62;DC_BD1AE46B11A4;CC_F167AEB73169;CC_F985E395CBFC",
        mrvl_url,
        "calls:D_MRVL_20261102_LITE_MERGE;calls:ECL040;calls:EV037;calls:EE040;timeline:TL9006",
        "",
        mrvl_fs,
        "2026-11-22",
        "HTTP 200归档官网全文(mrvl_20261102_lumentum_combine.txt)并入EV037(capital_relationship/announced)与TL9006，明确待股东与反垄断审批未交割",
    )

    lite_dt, lite_title, lite_url, lite_fs, _ = _dc_meta(
        dc_index,
        "DC_573401DC530B",
        "2026-11-02",
        "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Announces-First-Quarter-of-Fiscal-Year-2027-Financial-Results/default.aspx",
        "Lumentum Announces First Quarter of Fiscal Year 2027 Financial Results",
    )
    add(
        "P0",
        "T3_commitment_verification",
        "ingested_to_kb",
        "Lumentum",
        "LITE",
        "overseas_official_release",
        lite_dt,
        f"{lite_title}（CEO首段原句证实second major NPO/CPO win backed by purchase commitments exceeding $5B，FY27Q1合并营收12.626亿美元）",
        "DC_573401DC530B",
        lite_url,
        "calls:S_LITE_2027Q1;calls:CL077;calls:D_LITE_20261102_FY27Q1;calls:ECL041;calls:EV038;calls:EE041;timeline:TL9012",
        "",
        lite_fs,
        "2026-11-22",
        "HTTP 200归档FY27Q1全文(lite_20261102_fy27q1_results.txt)并入CL077/EV038/TL9012；严格锁定四边界：NPO/CPO合并定语非纯CPO、未具名客户与年限、属跨期承诺非当季收入、无200G EML专项积压拆分",
    )

    axt1_dt, axt1_title, axt1_url, axt1_fs, _ = _dc_meta(
        dc_index,
        "DC_3841FCD60F32",
        "2026-10-29",
        "https://investors.axt.com/Investors/news/news-details/2026/AXT-Inc--Announces-Third-Quarter-2026-Financial-Results/default.aspx",
        "AXT, Inc. Announces Third Quarter 2026 Financial Results",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "AXT",
        "AXTI",
        "overseas_official_release",
        axt1_dt,
        f"{axt1_title}（Q3营收7341万美元创纪录、毛利率56.0%，CEO确认超额达成2026年内InP产能翻倍目标）",
        "DC_3841FCD60F32;CC_0755C04CF75A",
        axt1_url,
        "calls:S_AXTI_2026Q3;calls:CL078;calls:D_AXTI_20261029_Q3;calls:ECL042;calls:EV039;calls:EE042",
        "",
        axt1_fs,
        "2026-11-22",
        "HTTP 200归档Q3全文(axti_20261029_2026q3_results.txt)推进S_AXTI_2026Q3并入CL078/EV039；注明正文未单列InP分项收入与商务部出口许可证笔数",
    )

    axt2_dt, axt2_title, axt2_url, axt2_fs, _ = _dc_meta(
        dc_index,
        "DC_FD32C455D502",
        "2026-10-28",
        "https://investors.axt.com/Investors/news/news-details/2026/AXT-Inc--Announces-Up-to-RMB-3-67-Billion-Approximately-US545-Million-in-Private-Equity-Financing-for-Subsidiary-Tongmei/default.aspx",
        "AXT, Inc. Announces Up to RMB 3.67 Billion (Approximately US$545 Million) in Private Equity Financing for Subsidiary Tongmei",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "AXT / 北京通美晶体",
        "AXTI",
        "overseas_official_release",
        axt2_dt,
        f"{axt2_title}（北京通美签署19.12亿至36.69亿元私募股权融资协议扩产InP衬底，预计2026-12交割、待政府备案）",
        "DC_FD32C455D502;O-c5e488679ff29f47e3fa;CC_7A7EB3BF6986;CC_CC77D69D82A1",
        axt2_url,
        "calls:D_AXTI_20261028_TONGMEI_PE;calls:ECL043;calls:EV040;calls:EE043",
        "",
        axt2_fs,
        "2026-11-22",
        "HTTP 200归档官网全文(axti_20261028_tongmei_financing.txt)并入EV040，明确上限稀释后AXT约持股73.40%且未交割前不计落地新增产能",
    )

    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "Tower Semiconductor × 中际旭创",
        "TSEM/300308",
        "overseas_official_release",
        tsem_dt,
        f"{tsem_title}（正文核实首款NPO在Tower美加州厂PH18M 200mm进入early production，多款下一代NPO在300mm硅光平台流片）",
        "DC_430D7977BA22",
        tsem_url,
        "calls:D_TSEM_20261103_INNOLIGHT_NPO;calls:ECL039;calls:EV036;calls:EE039;timeline:TL9002",
        "",
        tsem_fs,
        "2026-11-22",
        "HTTP 200归档官网全文(tsem_20261103_innolight_npo.txt)，将EV036/TL9002由标题锚升级为第3/7段逐字引语，与中际2027H2上量口径闭环一致",
    )

    # DRQ0020: 东山精密 (002384) -> ingested_to_kb
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "东山精密",
        "002384",
        "domestic_backfill_ir",
        "2026-11-02",
        "002384投资者关系活动记录表20261102(#L54..60/#L102..122)：正式回复泛称小批量光芯片外售优先自用(未细分CW/EML/DFB)，1.6T Q4进入相对批量出货",
        "D-394c94777fd5c6",
        "https://static.cninfo.com.cn/finalpage/2026-11-02/1225654366.PDF",
        "points:P130;points:P133",
        "",
        "2026-11-04",
        "2026-11-22",
        "2026-11-22回读11-02投关原件全文核实：虽提问含CW字样，正式回复仅泛称小批量光芯片外售，已将严格品类边界写入P130与P133注记",
    )

    nok_dt, nok_title, nok_url, nok_fs, _ = _dc_meta(
        dc_index,
        "DC_BF393C7C7BE8",
        "2026-09-15",
        "https://www.nokia.com/newsroom/telxius-boosts-global-network-capacity-and-efficiency-with-nokia-800g-coherent-pluggable-deployment/",
        "Telxius boosts global network capacity and efficiency with Nokia 800G Coherent Pluggable deployment",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Nokia × Telxius",
        "NOK",
        "overseas_official_release",
        nok_dt,
        f"{nok_title}（核实为Telxius在欧美及拉美陆地传输网推进ICE-X 800G ZR/ZR+现网部署，区别于此前BRUSA海缆试验）",
        "DC_BF393C7C7BE8;O-e7f841fc059d4922f456;O-bbce634d8ce7439774d4",
        nok_url,
        "calls:D_NOK_20260915_TELXIUS_800G;calls:ECL044;calls:EV041;calls:EE044;timeline:TL9010",
        "",
        nok_fs,
        "2026-11-22",
        "HTTP 200归档Nokia新闻室原文(nok_20260915_telxius_800g.txt)并入EV041与TL9010，严格区分陆地现网部署与海缆历史试验",
    )

    fn_dt, fn_title, fn_url, fn_fs, _ = _dc_meta(
        dc_index,
        "DC_7B475AB0DF5A",
        "2026-11-02",
        "https://investor.fabrinet.com/news-releases/news-release-details/fabrinet-announces-first-quarter-fiscal-year-2027-financial",
        "Fabrinet Announces First Quarter Fiscal Year 2027 Financial Results",
    )
    add(
        "P1",
        "T3_commitment_verification",
        "ingested_to_kb",
        "Fabrinet",
        "FN",
        "overseas_official_release",
        fn_dt,
        f"{fn_title}（FY27Q1合并营收14.745亿美元+51% YoY、Q2指引16.0-16.5亿美元；新闻稿未单列1.6T代工与Building 10）",
        "DC_7B475AB0DF5A;COMMITMENT_CM008;COMMITMENT_CM009",
        fn_url,
        "calls:S_FN_2027Q1;calls:D_FN_20261102_FY27Q1",
        "",
        fn_fs,
        "2026-11-22",
        "HTTP 200归档FY27Q1全文(fn_20261102_fy27q1_results.txt)推进S_FN_2027Q1，D_FN_20261102_FY27Q1诚实标no_relevant_claims",
    )

    nvda_dt, nvda_title, nvda_url, nvda_fs, _ = _dc_meta(
        dc_index,
        "DC_4FAA980A3027",
        "2026-11-17",
        "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2027",
        "NVIDIA Announces Financial Results for Third Quarter Fiscal 2027",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "NVIDIA",
        "NVDA",
        "overseas_official_release",
        nvda_dt,
        f"{nvda_title}（FY27Q3总营收1158.44亿美元，披露与Cisco推进USFP新光模块形态计划，未披露CPO交换机客户交付时点）",
        "DC_4FAA980A3027",
        nvda_url,
        "calls:S_NVDA_2027Q3;calls:D_NVDA_20261117_FY27Q3;calls:ECL045;calls:EV042;calls:EE045",
        "",
        nvda_fs,
        "2026-11-22",
        "HTTP 200归档FY27Q3全文(nvda_20261117_fy27q3_results.txt)推进S_NVDA_2027Q3并录入EV042(USFP形态计划)",
    )

    cien_q3_dt, cien_q3_title, cien_q3_url, cien_q3_fs, _ = _dc_meta(
        dc_index,
        "DC_9B16CE64F492",
        "2026-09-03",
        "https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-Third-Quarter-2026-Financial-Results/default.aspx",
        "Ciena Reports Fiscal Third Quarter 2026 Financial Results",
    )
    add(
        "P1",
        "T3_commitment_verification",
        "ingested_to_kb",
        "Ciena",
        "CIEN",
        "overseas_official_release",
        cien_q3_dt,
        f"{cien_q3_title}（FY26Q3营收16.711亿美元、光网络分部11.913亿美元；业绩稿未单列800GZR出货或Vesta Q2可提供日）",
        "DC_9B16CE64F492",
        cien_q3_url,
        "calls:S_CIEN_2026Q3_PR;calls:D_CIEN_20260903_FY26Q3;calls:CM008;calls:CM009",
        "",
        cien_q3_fs,
        "2026-11-22",
        "HTTP 200归档FY26Q3全文(cien_20260903_fy26q3_results.txt)按interquarter入S_CIEN_2026Q3_PR并刷新CM008/CM009评估备注",
    )

    tsem2_dt, tsem2_title, tsem2_url, tsem2_fs, _ = _dc_meta(
        dc_index,
        "DC_A038F7C2DD93",
        "2026-09-17",
        "https://ir.towersemi.com/news-releases/news-release-details/newphotonicsr-and-tower-semiconductor-begin-high-volume/",
        "NewPhotonics and Tower Semiconductor Begin High-Volume Shipments of Laser-Integrated Silicon Photonics",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Tower Semiconductor × NewPhotonics",
        "TSEM",
        "overseas_official_release",
        tsem2_dt,
        f"{tsem2_title}（拆分为EV043 800G/1.6T NPG102当期批量出货与EV044 6.4T NPC505预计2027H1出货两条独立记录）",
        "DC_A038F7C2DD93;O-e15b3b1d0e5034fcdb57;O-df782ffa8e620ce640f1",
        tsem2_url,
        "calls:WATCH_NEWPHOTONICS;calls:D_TSEM_20260917_NEWPHOTONICS;calls:ECL046;calls:ECL047;calls:EV043;calls:EV044;calls:EE046;calls:EE047;timeline:TL9007",
        "",
        tsem2_fs,
        "2026-11-22",
        "HTTP 200归档全文(tsem_20260917_newphotonics_pic.txt)，新增WATCH_NEWPHOTONICS并分列事实出货(EV043)与2027H1前瞻(EV044)及TL9007",
    )

    wiw_dt, wiw_title, wiw_url, wiw_fs, _ = _dc_meta(
        dc_index,
        "DC_286D42235853",
        "2026-10-13",
        "https://www.wiwynn.com/news/wiwynn-ayar-labs-and-guc-advance-co-packaged-optics-with-live-demonstration-of-integrated-optical-compute-system-at-ocp-global-summit-2026",
        "Wiwynn, Ayar Labs, and GUC Advance Co-Packaged Optics with Live Demonstration",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Wiwynn × Ayar Labs × GUC",
        "WIWYNN",
        "overseas_official_release",
        wiw_dt,
        f"{wiw_title}（核明Wiwynn ORv3系统、GUC多芯片ASIC与Ayar TeraPHY+SuperNova分工，严格标demonstrated）",
        "DC_286D42235853;O-febf734013d2297db2f7;O-96264b63c5d82e67b7f5",
        wiw_url,
        "calls:D_WIWYNN_20261013_OCP_CPO_DEMO;calls:ECL048;calls:EV045;calls:EE048",
        "",
        wiw_fs,
        "2026-11-22",
        "HTTP 200归档全文(wiwynn_20261013_ayar_guc_cpo_demo.txt)并入EV045，严格限定为OCP现场演示",
    )

    lm_dt, lm_title, lm_url, lm_fs, _ = _dc_meta(
        dc_index,
        "DC_DC1ABE67C305",
        "2026-10-12",
        "https://lightmatter.com/press-release/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners/",
        "Lightmatter Delivers Open Rack CPO Switch and XPU Scale-Up Server",
    )
    add(
        "P1",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "Lightmatter",
        "WATCH_LIGHTMATTER",
        "overseas_official_release",
        lm_dt,
        f"{lm_title}（核清204.8T交换托盘为Flex联合生产验证平台、102.4T计算托盘为概念验证原型，OCP展台展示）",
        "DC_DC1ABE67C305;O-c75f8fd66ee62f89ffa3",
        lm_url,
        "calls:D_LIGHTMATTER_20261012_OCP_CPO;calls:ECL049;calls:EV046;calls:EE049",
        "",
        lm_fs,
        "2026-11-22",
        "HTTP 200归档全文(lightmatter_20261012_open_rack_cpo.txt)并入EV046(demonstrated)，厘清Delivers语境非商业部署交付",
    )

    crdo_dt, crdo_title, crdo_url, crdo_fs, _ = _dc_meta(
        dc_index,
        "DC_7CED25D6E66F",
        "2026-10-12",
        "https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Unveils-1-6T-ZeroFlap-Active-Light-Cable-Industrys-First-Row-Scale-Wide-Parallel-Optical-Interconnect-for-AI-Data-Centers/default.aspx",
        "Credo Unveils 1.6T ZeroFlap Active Light Cable",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Credo",
        "CRDO",
        "overseas_official_release",
        crdo_dt,
        f"{crdo_title}（微发光器阵列多通道NRZ无DSP方案，端功耗12W/距离50m，原文明确预计2027年开始出货）",
        "DC_7CED25D6E66F;O-33fafe31d322dc9a9336",
        crdo_url,
        "calls:D_CRDO_20261012_1P6T_ALC;calls:ECL050;calls:EV047;calls:EE050",
        "",
        crdo_fs,
        "2026-11-22",
        "HTTP 200归档全文(crdo_20261012_1p6t_alc.txt)并入EV047(announced)，锁定2027年出货前瞻时态",
    )

    mtsi_dt, mtsi_title, mtsi_url, mtsi_fs, _ = _dc_meta(
        dc_index,
        "DC_535D459775E6",
        "2026-09-17",
        "https://ir.macom.com/news-releases/news-release-details/macom-introduces-32t-chipset-solution-high-speed-optical/",
        "MACOM Introduces 3.2T Chipset Solution for High Speed Optical Connectivity",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "MACOM",
        "MTSI",
        "overseas_official_release",
        mtsi_dt,
        f"{mtsi_title}（核明新增MATA-42754/41754四通道线性TIA与MARP-BP224背照式PIN PD，配EV007驱动芯片组成8x448G套片）",
        "DC_535D459775E6;O-81b000ec2d7132b273cf",
        mtsi_url,
        "calls:D_MTSI_20260917_3P2T_CHIPSET;calls:ECL051;calls:EV048;calls:EE051",
        "",
        mtsi_fs,
        "2026-11-22",
        "HTTP 200归档全文(mtsi_20260917_3p2t_chipset.txt)，以previous_event_id=EV007单列新品事件EV048",
    )

    iqe_dt, iqe_title, iqe_url, iqe_fs, _ = _dc_meta(
        dc_index,
        "DC_741EFE5BF486",
        "2026-09-03",
        "https://www.iqep.com/media/press-releases/2026/iqe-announces-purchase-agreement-with-quintessent-as-quantum-dot-laser-technology-moves-to-customer-sampling/",
        "IQE announces purchase agreement with Quintessent as Quantum Dot Laser technology advances",
    )
    add(
        "P1",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "IQE × Quintessent",
        "WATCH_IQE",
        "overseas_official_release",
        iqe_dt,
        f"{iqe_title}（拆分为EV049 6英寸GaAs量子点激光外延片采购协议与EV050下游客户送样两条独立记录）",
        "DC_741EFE5BF486;O-bda966e9d75a82f6132e;O-638398cab3e6f3ef8f3b",
        iqe_url,
        "calls:WATCH_QUINTESSENT;calls:D_IQE_20260903_QUINTESSENT_QDL;calls:ECL052;calls:ECL053;calls:EV049;calls:EV050;calls:EE052;calls:EE053;timeline:TL9009",
        "",
        iqe_fs,
        "2026-11-22",
        "HTTP 200归档全文(iqe_20260903_quintessent_qdl.txt)，新增WATCH_QUINTESSENT并分列EV049/EV050及TL9009",
    )

    # DRQ0031: 汇绿生态(武汉钧恒) -> ingested_to_kb
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "汇绿生态(武汉钧恒)",
        "001267",
        "domestic_backfill_ir",
        "2026-11-06",
        "001267投关11/03(#L51..77)与11/06(#L37..49)：现有产能武汉300万+鄂州一期150万+大马100-150万支/年，另拟3.09亿元建武汉350万支新基地(建成后旧厂停用)",
        "D-91daae63a0b9f9;D-f5fb3232794fee;D-7e1516c1847de2",
        "https://static.cninfo.com.cn/finalpage/2026-11-03/1225655440.PDF",
        "points:P039;content:CLG0631",
        "",
        "2026-11-03",
        "2026-11-22",
        "2026-11-22精读11/03及11/06投关原件，严格拆分已投产产能与3.09亿元替代扩建规划并更新P039锚点与注记",
    )

    # DRQ0032: 沪电股份 -> watch_deferred (树外交换机/超节点PCB)
    add(
        "P1",
        "T1_lifecycle_shift",
        "watch_deferred",
        "沪电股份",
        "002463",
        "domestic_backfill_ir",
        "2026-10-16",
        "002463投关纪要(10/15至11/19共14份)及39份公告核实：适配224Gbps小批量供货与1.6T批量出货均属超节点及高速网络交换机PCB(树外系统板)",
        "D-246cdd17e2e30a;D-ab513df71b04b4",
        "https://static.cninfo.com.cn/finalpage/2026-10-16/1225608881.PDF",
        "",
        "全文检索光模块零命中，未见B1光模块内部PCB披露；后续仅在出现明确光模块板级披露时再重评",
        "2026-10-15",
        "2026-11-22",
        "2026-11-22核查巨潮14份投关记录表与39份正式公告确认均属交换机/超节点主板背板(树外)，严守B1边界不入points.csv，转watch_deferred",
    )

    # DRQ0033: 联特科技 -> ingested_to_kb
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "联特科技",
        "301205",
        "domestic_backfill_ir",
        "2026-10-28",
        "301205投关2026-10-28(#L55..76)：800G批量发货季度环比提升，1.6T(FRO/LRO/LPO)已送样北美大型CSP并获部分客户验证通过及实机演示",
        "D-34fd44909151da",
        "https://static.cninfo.com.cn/finalpage/2026-10-28/1225635041.PDF",
        "points:P174",
        "",
        "2026-10-28",
        "2026-11-22",
        "2026-11-22精读10/28投关原件(编号2026-003)，严格拆分800G批量发货与1.6T送样验证时态并更新P174",
    )

    # DRQ0034: 锐捷网络 -> ingested_to_kb
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "锐捷网络",
        "301165",
        "domestic_backfill_ir",
        "2026-10-21",
        "301165投关10/19-21(#L135..138/#L276..286)：目前规模量产交付仅400G LPO(1.6T LPO为原型样品)，且全部搭配自有交换机销售、不作为通用配件单独销售",
        "D-d6726c33048b36",
        "https://static.cninfo.com.cn/finalpage/2026-10-21/1225614287.PDF",
        "points:P187",
        "",
        "2026-10-21",
        "2026-11-22",
        "2026-11-22核对10/19-21投关原件Q9纠偏400G量产与1.6T原型边界及整机捆绑销售不单独外售口径，已写入P187",
    )

    # DRQ0035: 景旺电子 -> ingested_to_kb
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "景旺电子",
        "603228",
        "gemini_compliance_audit",
        "2026-09-29",
        "603228 2026半年报第11页(#L493..495)逐字核实：新增mSAP产线落地，已批量交付800G、1.6T光模块PCB，2026Q2收入环比增近1500%(剥离S.5548二手传闻)",
        "G-cf34d3f9017c9f88",
        "https://static.cninfo.com.cn/finalpage/2026-08-22/1225493416.PDF#page=11",
        "points:P031;content:CLG0624;content:CLG0625",
        "",
        "2026-09-29",
        "2026-11-22",
        "2026-11-22下载归档603228 2026半年报PDF及旁车(corpus/ir/603228)，精准核实p.11逐字命中P031引语并剥离二手传闻",
    )

    # DRQ0036: 华工科技 -> ingested_to_kb
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "华工科技",
        "000988",
        "gemini_compliance_audit",
        "2026-10-30",
        "000988法定投关2026-10-30第6页(#L169..204)核实：泰国工厂800G LPO月出货约10万只、1.6T LPO送样测试、6.4T NPO预计2027-07批量，全文零原产地关税豁免表述",
        "G-c0308a66e32bf867",
        "https://static.cninfo.com.cn/finalpage/2026-10-30/1225647394.PDF#page=6",
        "points:P209;content:CLG0612;content:CLG0613",
        "",
        "2026-10-30",
        "2026-11-22",
        "2026-11-22从巨潮归档000988 10-30正式投关记录表(corpus/ir/000988)，核实定量自述并剔除无据原产地关税外推，已更新P209",
    )

    # DRQ0037: LWLG x 鸿海 -> 维持 pending_primary_text (空 JS 壳)
    lwlg_dt, lwlg_title, lwlg_url, lwlg_fs, _ = _dc_meta(
        dc_index,
        "DC_4B0F75924A65",
        "2026-10-29",
        "https://api.quotemedia.com/supplement/news-story/?webmasterId=102691&storyId=8438787577882246",
        "Lightwave Logic Electro-Optic Polymer Technology Integrated into Hon Hai Transceiver",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "pending_primary_text",
        "Lightwave Logic × 鸿海",
        "LWLG/FIT",
        "overseas_staging_rescued",
        lwlg_dt,
        f"{lwlg_title}（2026-11-22实测源URL返回p_chars=0空JS壳且LWLG官网新闻页为Issuer Direct动态嵌入组件）",
        "DC_4B0F75924A65;O-4bf93a7b108949dbaeeb",
        lwlg_url,
        "",
        "源链api.quotemedia.com静态HTTP返回空JS壳且lightwavelogic.com/press-releases无静态正文(blocked_http_or_js_shell)；待SEC 10-Q/8-K或第一方静态稿披露后再核实是否关联FIT(06088.HK)",
        lwlg_fs,
        "2026-11-22",
        "2026-11-22严守不绕动态组件红线维持pending_primary_text(公开元数据指向Hon Hai Tech Group旗下Siphcomm部门科技日SOH样机演示，非FIT量产)",
    )

    opl_dt, opl_title, opl_url, opl_fs, _ = _dc_meta(
        dc_index,
        "DC_839378F484E4",
        "2026-10-07",
        "https://openlightphotonics.com/newsroom/openlight-advances-heterogeneous-silicon-photonics-toward-volume-production",
        "OpenLight Advances Heterogeneous Silicon Photonics Toward Volume",
    )
    add(
        "P2",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "OpenLight",
        "WATCH_OPENLIGHT",
        "overseas_official_release",
        opl_dt,
        f"{opl_title}（官网页面核实为ECOC后媒体专访导读短摘要，未披露晶圆厂PDK冻结或商业量产出货实证）",
        "DC_839378F484E4;O-9184103547e7f3803990",
        opl_url,
        "calls:D_OPENLIGHT_20261007_HETERO_SIPHO",
        "",
        opl_fs,
        "2026-11-22",
        "HTTP 200归档全文(openlight_20261007_heterogeneous_sipho.txt)，在calls/disclosures.csv以no_relevant_claims闭合归档",
    )

    lite_dwdm_dt, lite_dwdm_title, lite_dwdm_url, lite_dwdm_fs, _ = _dc_meta(
        dc_index,
        "DC_D527C3DC5ED2",
        "2026-09-21",
        "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-to-Demonstrate-DWDM-ELSFP-Laser-Module-for-OCI-MSA-Applications-at-ECOC-2026/default.aspx",
        "Lumentum to Demonstrate DWDM ELSFP Laser Module for OCI MSA Applications at ECOC",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Lumentum",
        "LITE",
        "overseas_official_release",
        lite_dwdm_dt,
        f"{lite_dwdm_title}（8通道DWDM ELSFP展前演示预告，原文明确预计2027H1初始可提供initial availability）",
        "DC_D527C3DC5ED2;O-c30ecaa7ba13d26cd98e;O-29f396a00749e907b0fd",
        lite_dwdm_url,
        "calls:D_LITE_20260921_ECOC_ELSFP;calls:ECL054;calls:EV051;calls:EE054",
        "",
        lite_dwdm_fs,
        "2026-11-22",
        "HTTP 200归档全文(lite_20260921_ecoc_dwdm_elsfp.txt)并入EV051(announced)，锁定2027H1可提供时间表",
    )

    lite_vcsel_dt, lite_vcsel_title, lite_vcsel_url, lite_vcsel_fs, _ = _dc_meta(
        dc_index,
        "DC_E1BEF90B2480",
        "2026-09-21",
        "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Qualcomm-and-Corning-to-Demonstrate-High-Density-1060-nm-VCSEL-Optical-D2D-Connectivity-for-AI-Scale-Up-at-ECOC-2026/default.aspx",
        "Lumentum, Qualcomm, and Corning to Demonstrate High-Density 1060 nm VCSEL Optical Interconnect",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Lumentum × Qualcomm × Corning",
        "LITE",
        "overseas_official_release",
        lite_vcsel_dt,
        f"{lite_vcsel_title}（核实为单通道32 Gb/s NRZ 1060nm VCSEL配Corning多模插芯概念验证演示计划）",
        "DC_E1BEF90B2480;O-bfe68347c095042d1e48;O-abfc42c6cac6a5edefa8",
        lite_vcsel_url,
        "calls:D_LITE_20260921_ECOC_VCSEL_D2D;calls:ECL055;calls:EV052;calls:EE055",
        "",
        lite_vcsel_fs,
        "2026-11-22",
        "HTTP 200归档全文(lite_20260921_ecoc_1060nm_vcsel.txt)并入EV052，严格限定为proof-of-concept不升格C2商业点",
    )

    wiw2_dt, wiw2_title, wiw2_url, wiw2_fs, _ = _dc_meta(
        dc_index,
        "DC_4A9C0B800414",
        "2026-10-12",
        "https://www.wiwynn.com/news/wiwynn-showcases-next-gen-ai-platforms-thermal-engineering-and-optical-interconnect-technologies-at-2026-ocp-global-summit",
        "Wiwynn Showcases Next-Gen AI Platforms, Thermal Engineering, and Optical Interconnect",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Wiwynn",
        "WIWYNN",
        "overseas_official_release",
        wiw2_dt,
        f"{wiw2_title}（核实为ODM展台总览预热稿，具体CPO系统演示已由次日专项稿EV045建档）",
        "DC_4A9C0B800414;O-51432ea38512dc2f2116",
        wiw2_url,
        "calls:D_WIWYNN_20261012_OCP_SHOWCASE",
        "",
        wiw2_fs,
        "2026-11-22",
        "HTTP 200归档全文(wiwynn_20261012_ocp_showcase.txt)，标no_relevant_claims防与EV045同源双计",
    )

    mxl_dt, mxl_title, mxl_url, mxl_fs, _ = _dc_meta(
        dc_index,
        "DC_DFCE4B441F6E",
        "2026-11-10",
        "https://investors.maxlinear.com/press-releases/detail/630/maxlinear-unveils-jeju-custom-pmic-engineered-for-peak",
        "MaxLinear Unveils Jeju Custom PMIC, Engineered for Peak Efficiency with 1.6T Optical Transceivers",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "MaxLinear",
        "MXL",
        "overseas_official_release",
        mxl_dt,
        f"{mxl_title}（核清Jeju MxL77904定制PMIC预计2027年2月向客户送样，并非已随DSP捆绑量产出货）",
        "DC_DFCE4B441F6E",
        mxl_url,
        "calls:D_MXL_20261110_JEJU_PMIC;calls:ECL056;calls:EV053;calls:EE056",
        "",
        mxl_fs,
        "2026-11-22",
        "HTTP 200归档全文(mxl_20261110_jeju_pmic.txt)并入EV053(announced)，锁定2027-02预计送样时态",
    )

    cien_i2_dt, cien_i2_title, cien_i2_url, cien_i2_fs, _ = _dc_meta(
        dc_index,
        "DC_91F3D715F522",
        "2026-11-17",
        "https://investor.ciena.com/news/news-details/2026/Ciena-and-Internet2-Reach-Industry-Record-for-Longest-Terrestrial-800-Gbs-Coherent-Pluggable-Link/default.aspx",
        "Ciena and Internet2 Reach Industry Record for Longest Terrestrial 800 Gb/s Coherent Pluggable",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Ciena × Internet2",
        "CIEN",
        "overseas_official_release",
        cien_i2_dt,
        f"{cien_i2_title}（核明WaveLogic 6 Nano 135 GBaud在SC26芝加哥至堪萨斯城往返2104公里科研网现网试验）",
        "DC_91F3D715F522",
        cien_i2_url,
        "calls:D_CIEN_20261117_INTERNET2_800G;calls:ECL057;calls:EV054;calls:EE057",
        "",
        cien_i2_fs,
        "2026-11-22",
        "HTTP 200归档全文(cien_20261117_internet2_800g.txt)并入EV054(demonstrated)，明确科研骨干网试验非批量订单",
    )

    poet_dt, poet_title, _, poet_fs, _ = _dc_meta(
        dc_index,
        "DC_4FACD43C676E",
        "2026-11-16",
        "https://www.poet-technologies.com/news/poet-technologies-reports-record-q3-2026-revenue-of-1-03m-up-244",
        "POET Technologies Reports Record Q3 2026 Revenue of $1.03M, Up 244%",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "POET Technologies",
        "POET",
        "overseas_official_release",
        poet_dt,
        f"{poet_title}（官网正式稿核清：Q3营收102.6万美元、净亏756万美元，原定2026年目标3万只光引擎顺延至2027Q2前交付）",
        "DC_4FACD43C676E",
        "https://www.poet-technologies.com/news/poet-technologies-reports-record-q3-2026-revenue-of-1-03m-up-244",
        "calls:S_POET_2026Q3;calls:CL079;calls:D_POET_20261116_Q3;calls:ECL058;calls:EV055;calls:EE058",
        "",
        poet_fs,
        "2026-11-22",
        "HTTP 200抓回POET官网第一方正式稿(poet_20261116_2026q3_official.txt)推进S_POET_2026Q3并入CL079/EV055(delayed)",
    )

    avgo_dt, avgo_title, avgo_url, avgo_fs, _ = _dc_meta(
        dc_index,
        "DC_425841A754F4",
        "2026-09-02",
        "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial",
        "Broadcom Inc. Announces Third Quarter Fiscal Year 2026 Financial Results",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "博通(Broadcom)",
        "AVGO",
        "overseas_official_release",
        avgo_dt,
        f"{avgo_title}（FY26Q3总营收296亿美元、AI半导体收入167亿美元+221% YoY；新闻稿未拆分Tomahawk 6 CPO或光DSP份额）",
        "DC_425841A754F4",
        avgo_url,
        "calls:S_AVGO_2026Q3;calls:CL080;calls:D_AVGO_20260902_Q3",
        "",
        avgo_fs,
        "2026-11-22",
        "HTTP 200归档FY26Q3全文(avgo_20260902_fy26q3_results.txt)推进S_AVGO_2026Q3并入CL080/D_AVGO_20260902_Q3",
    )

    # DRQ0046: 北美CSP与进出口合规政策池 -> Step 5 调取一手法规与CBP裁定正式结案入 KN011-KN014
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "北美CSP与进出口合规政策池",
        "EXT_POLICY",
        "gemini_compliance_audit",
        "2026-11-17",
        "合规核查G-cb80feb5485f402e/G-d6ee1cb32ece68e2/G-9ab4ac6f52ae4f02：CBP原产地正反四裁定、FCC 26-50/S.5548法律边界、我国2026年第48号公告及BIS EAR/欧盟EED一手核定",
        "G-cb80feb5485f402e;G-d6ee1cb32ece68e2;G-9ab4ac6f52ae4f02",
        "https://docs.fcc.gov/public/attachments/FCC-26-50A1.pdf",
        "knowledge:KN011;knowledge:KN012;knowledge:KN013;knowledge:KN014",
        "",
        "2026-08-27",
        "2026-11-22",
        "2026-11-22已调取FCC/Congress/CBP/MOFCOM/USTR/EAR/EED一手原件逐款核实并写入knowledge.yaml KN011-KN014及refs合规专章办结",
    )

    # =========================================================================
    # DRQ0047 .. DRQ0055 (国内法定公告核查刷新，保持原位编号)
    # =========================================================================
    # DRQ0047: 云南锗业 (002428) -> ingested_to_kb (查获 2026-057 正式公告)
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "云南锗业",
        "002428",
        "cninfo_filing_and_ir",
        "2026-11-18",
        "深交所公告2026-057(#L14..48)证实：高品质磷化铟单晶片项目总投资由18,856万元调增8,143万元至26,999万元(年产折合4英寸45万片)；11-10投关披露6英寸在手订单约1.3万片(约3亿元)",
        "CLOUD_20261119_YNG_270M;FILING_002428_20261118_057",
        "https://static.cninfo.com.cn/finalpage/2026-11-18/1225676124.PDF",
        "points:P202",
        "",
        "2026-11-18",
        "2026-11-22",
        "2026-11-22巨潮抓回1225676124.PDF与11-10投关1225665965.PDF落盘corpus/ir/002428，将媒体概数2.7亿元校准为法定精确值18,856->26,999万元并更新P202",
    )

    # DRQ0048: 微见智能 -> 维持 pending_filing_anchor
    add(
        "P0",
        "T4_universe_blindspot",
        "pending_filing_anchor",
        "微见智能",
        "UNLISTED_MV",
        "kb_audit_20261119_n03",
        "2026-11-19",
        "微见智能封装技术(深圳)有限公司：高精度光模块共晶贴片/固晶设备厂商(已入tree.yaml observation_list)",
        "AUDIT_1119_N03_WEIJIAN",
        "corpus/legacy-input/lieqi_prospectus.txt",
        "",
        "未上市私企不入_frozen.csv；截至2026-11-22核查仍仅见猎奇招股书释义及卖方研报转述，缺公司官网产品规格书存档、IPO申报稿或上市客户法定公告一手锚，未满点准入路径②前禁入points.csv EQ3",
        "2026-11-19",
        "2026-11-22",
        "2026-11-22复核维持pending_filing_anchor：已纳管于tree.yaml观察名单、entity_nodes.csv及entity-registry.yaml",
    )

    # DRQ0049: 镭神技术 -> 维持 pending_filing_anchor
    add(
        "P0",
        "T4_universe_blindspot",
        "pending_filing_anchor",
        "镭神技术",
        "UNLISTED_LS",
        "kb_audit_20261119_n03",
        "2026-11-19",
        "镭神技术(深圳)有限公司：高精度光耦合封装设备厂商(猎奇招股书引F&S列其2024全球光耦合设备台数份额27%居首，已入tree.yaml observation_list)",
        "AUDIT_1119_N03_LEISHEN",
        "corpus/legacy-input/lieqi_prospectus.txt",
        "",
        "未上市私企不入_frozen.csv；截至2026-11-22核查猎奇招股书27%系竞品转引第三方顾问估算，缺镭神技术官网产品规格书存档或独立上市文件直接能力锚，待补齐一手锚后按路径②入points.csv EQ4",
        "2026-11-19",
        "2026-11-22",
        "2026-11-22复核维持pending_filing_anchor：已纳管于tree.yaml观察名单、entity_nodes.csv及entity-registry.yaml",
    )

    # DRQ0050: 科瑞技术 U11 -> 维持 pending_filing_anchor
    kerui_gate = (
        "截至2026-11-22复核，2025年报仅匿名披露“海外头部客户/海外光器件品牌企业”，Lumentum/Coherent具名供应链边仍属商业保密未见双方监管文件(巨潮公告/互动易书面具名确认或SEC 10-K/8-K)；未获监管具名印证前严禁写入edges.csv或relationship_timeline.csv"
    )
    kerui_note = (
        "2025年报p.15光模块芯片共晶贴片(P275)与50nm光耦合(P276)能力点已入库(见DRQ0055，CLG0633精确校准为#L630..631)；Lumentum/Coherent具名归属(U11)维持pending_filing_anchor持续盯防"
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "pending_filing_anchor",
        "科瑞技术",
        "002957",
        "kb_audit_20261119_u11",
        "2026-11-19",
        "深圳科瑞技术股份有限公司(002957)具名客户归属核查(U11)：市场传闻指向Lumentum/Coherent，但2025年报仅匿名披露“海外头部客户/海外光器件品牌企业”",
        "AUDIT_1119_N03_KERUI;U11_KERUI_LUMENTUM_COHERENT",
        "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        "points:P275;points:P276" if kerui_in_frozen else "",
        kerui_gate,
        "2026-11-19",
        "2026-11-22",
        kerui_note,
    )

    # DRQ0051: 天准科技 (688003) -> ingested_to_kb (新增 P277)
    add(
        "P1",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "天准科技",
        "688003",
        "cninfo_h1_and_annual",
        "2026-08-20",
        "688003 2026半年报第14页(#L680..683)一手证实：为800G/1.6T光模块提供精密量检测装备(长期服务中际旭创/新易盛/天孚通信)，获工业富联CPO量产项目在线AOI首批小批量订单且部分已交付现场",
        "AUDIT_1119_N03_TIANZHUN;H1_688003_2026_P14",
        "https://static.cninfo.com.cn/finalpage/2026-08-20/1225482975.PDF#page=14",
        "points:P277",
        "",
        "2026-07-26",
        "2026-11-22",
        "2026-11-22巨潮抓回688003 2026半年报1225482975.PDF落盘corpus/ir/688003，新增能力点P277(EQ6,生产中,A股)并将triage更新为已入点",
    )

    # DRQ0052: 长光华芯 (688048) -> 维持 pending_filing_anchor
    add(
        "P1",
        "T1_lifecycle_shift",
        "pending_filing_anchor",
        "长光华芯",
        "688048",
        "domestic_qa_followup",
        "2026-09-08",
        "长光华芯(688048) 200G EML光芯片客户验证转量产核查(09/08互动易明确200G EML仍在验证阶段、未获大单)",
        "QA_688048_20260908",
        "https://sns.sseinfo.com/",
        "points:P066;content:CLG0620;content:CLG0621",
        "截至2026-11-22复核尚无200G PAM4 EML通过客户端认证并获批量订单之法定报告或正式投关披露，须待2026年报或正式投关纪要书面确认后方可升格阶段",
        "2026-09-08",
        "2026-11-22",
        "2026-11-22复核维持pending_filing_anchor：09/08验证未获大单事实已入content_ledger，严防采信传言提前标量产",
    )

    # DRQ0053: 利扬芯片 (688135) -> 维持 pending_filing_anchor (已签协议但未过会未交割)
    add(
        "P1",
        "T2_supply_relationship_or_ma",
        "pending_filing_anchor",
        "利扬芯片",
        "688135",
        "cninfo_filing_lead",
        "2026-11-14",
        "上交所公告2026-071(#L9..27/#L675..679)：签署协议拟现金3.06亿元收购深圳众望达光电51%股权(面向光模块/硅光/CPO检测与自动耦合)，截至2026-11-22审计评估未完、待股东会审议且未交割",
        "CLOUD_20261119_LIYANG_306M;FILING_688135_20261114_071",
        "https://static.cninfo.com.cn/finalpage/2026-11-14/1225671802.PDF",
        "",
        "已落盘1225671802.PDF原件(corpus/ir/688135)，但标的审计评估尚未定稿、尚待临时股东会批准且未办理股权交割过户及具名客户披露；未交割前严禁入points.csv EQ7/EQ4",
        "2026-11-15",
        "2026-11-22",
        "2026-11-22归档11-14股权收购协议公告并核清未过会未交割法律边界，维持pending_filing_anchor盯防交割进展",
    )

    # DRQ0054: 经纬辉开 (300120) -> watch_deferred (仅参股7.71%不并表 + 科创委阶段验收)
    add(
        "P2",
        "T1_lifecycle_shift",
        "watch_deferred",
        "经纬辉开(参股铱加科技)",
        "300120",
        "cninfo_ir_verified",
        "2026-11-17",
        "300120投关2026-11-17(#L61..93)证实：仅通过全资子公司中兴系统间接持有铱加科技7.71%股权(不并表)，铱加1.6T/3.2T CPO属深圳市科创委专项阶段性验收(原型验证)，对业绩基本无贡献",
        "CLOUD_20261119_JWHK_YIJIA;IR_300120_20261117",
        "https://static.cninfo.com.cn/finalpage/2026-11-17/1225676140.PDF",
        "",
        "非控股参股(7.71%不并表)且仅处科研专项原型验证阶段，除非后续控股权变更并实现量产交付否则不入points.csv",
        "2026-11-18",
        "2026-11-22",
        "2026-11-22核实47条正式公告与11-17投关原件(2026-03)，按非控股参股+原型验证边界转watch_deferred隔离",
    )

    # DRQ0055: 科瑞技术 (002957)
    add(
        "P0",
        "T4_universe_blindspot",
        "ingested_to_kb",
        "科瑞技术",
        "002957",
        "cninfo_annual_report",
        "2026-04-24",
        "科瑞技术(002957)2025年报p.15一手披露光模块芯片共晶贴片设备(P275@EQ3,#L642..648)与50nm精度光耦合设备(P276@EQ4,#L630..631)并获海外头部客户验证认可",
        "ANNUAL_002957_2025_P15",
        "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        "points:P275;points:P276;content:CLG0632;content:CLG0633",
        "",
        "2026-11-19",
        "2026-11-22",
        "v6分母纳入002957并补入P275/P276及CLG0632(#L642..648)/CLG0633(#L630..631精确\\n行号)；Lumentum/Coherent具名边仍留DRQ0050盯防",
    )

    # =========================================================================
    # DRQ0056 .. DRQ0064: 正向标题规则挽救的 9 项 10–11 月重点海外财报/并购/标准披露
    # =========================================================================
    mtsi4_dt, mtsi4_title, mtsi4_url, mtsi4_fs, _ = _dc_meta(
        dc_index,
        "DC_A6ADDA0BAFA7",
        "2026-11-05",
        "https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-fourth-quarter-and-fiscal-year-2026/",
        "MACOM Reports Fiscal Fourth Quarter and Fiscal Year 2026 Financial Results",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "MACOM",
        "MTSI",
        "overseas_positive_rule_rescued",
        mtsi4_dt,
        f"{mtsi4_title}（FY26Q4营收4.248亿美元+62.7% YoY、FY27Q1指引4.50-4.60亿美元，补齐11月最新季度槽位）",
        "DC_A6ADDA0BAFA7",
        mtsi4_url,
        "calls:S_MTSI_2026Q4;calls:D_MTSI_20261105_Q4",
        "",
        mtsi4_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(mtsi_20261105_fy26q4_results.txt)，滚动入quarterly槽位S_MTSI_2026Q4(新闻稿正文标no_relevant_claims)",
    )

    tsem_q3_dt, tsem_q3_title, tsem_q3_url, tsem_q3_fs, _ = _dc_meta(
        dc_index,
        "DC_58448CDF4801",
        "2026-11-02",
        "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-reports-third-quarter-record-results/",
        "Tower Semiconductor Reports Third Quarter Record Results",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Tower Semiconductor",
        "TSEM",
        "overseas_positive_rule_rescued",
        tsem_q3_dt,
        f"{tsem_q3_title}（Q3营收5.26亿美元，CEO提出2026Q4硅光单项年化收入11亿美元目标即2025年的5倍，日本300mm扩产超前且客户长约延至2029）",
        "DC_58448CDF4801",
        tsem_q3_url,
        "calls:S_TSEM_2026Q3;calls:CL081;calls:D_TSEM_20261102_Q3;calls:ECL059;calls:EV056;calls:EE059",
        "",
        tsem_q3_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(tsem_20261102_2026q3_results.txt)，滚动入S_TSEM_2026Q3并写入CL081/EV056",
    )

    gfs_q3_dt, gfs_q3_title, gfs_q3_url, gfs_q3_fs, _ = _dc_meta(
        dc_index,
        "DC_DB6E7B2D27BB",
        "2026-11-04",
        "https://investors.gf.com/news-releases/news-release-details/globalfoundries-reports-third-quarter-2026-financial-results",
        "GlobalFoundries Reports Third Quarter 2026 Financial Results",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "GlobalFoundries × Marvell",
        "GFS/MRVL",
        "overseas_positive_rule_rescued",
        gfs_q3_dt,
        f"{gfs_q3_title}（Q3营收18.99亿美元；披露2026年9月与Marvell扩大美国Burlington厂SiGe多年制造产能协议，支撑可插拔/NPO/CPO）",
        "DC_DB6E7B2D27BB",
        gfs_q3_url,
        "calls:S_GFS_2026Q3;calls:D_GFS_20261104_Q3;calls:ECL060;calls:EV057;calls:EE060;timeline:TL9008",
        "",
        gfs_q3_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(gfs_20261104_2026q3_results.txt)，滚动入S_GFS_2026Q3并写入EV057与关系时间线TL9008",
    )

    veco_q3_dt, veco_q3_title, veco_q3_url, veco_q3_fs, _ = _dc_meta(
        dc_index,
        "DC_25B37F48DF71",
        "2026-11-04",
        "https://ir.veeco.com/news-and-events/news-details/2026/Veeco-Reports-Third-Quarter-2026-Financial-Results/default.aspx",
        "Veeco Reports Third Quarter 2026 Financial Results",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Veeco",
        "VECO",
        "overseas_positive_rule_rescued",
        veco_q3_dt,
        f"{veco_q3_title}（Q3营收2.094亿美元、Q4指引2.30-2.60亿美元，CEO指出高速光连接与先进封装共同拉动设备订单）",
        "DC_25B37F48DF71",
        veco_q3_url,
        "calls:S_VECO_2026Q3;calls:CL082;calls:D_VECO_20261104_Q3",
        "",
        veco_q3_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(veco_20261104_2026q3_results.txt)，滚动入S_VECO_2026Q3并写入CL082/D_VECO_20261104_Q3",
    )

    veco_m_dt, veco_m_title, veco_m_url, veco_m_fs, _ = _dc_meta(
        dc_index,
        "DC_6B392C92DA0A",
        "2026-11-02",
        "https://ir.veeco.com/news-and-events/news-details/2026/Axcelis-Technologies-and-Veeco-Instruments-Provide-Update-on-Expected-Timing-of-Merger-Closing/default.aspx",
        "Axcelis Technologies and Veeco Instruments Provide Update on Expected Timing of Merger Closing",
    )
    add(
        "P1",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "Veeco × Axcelis",
        "VECO/ACLS",
        "overseas_positive_rule_rescued",
        veco_m_dt,
        f"{veco_m_title}（全股票合并1股VECO换0.3575股ACLS预计交割日顺延至2027Q1末，仍待中国SAMR反垄断审批及美国HSR重报）",
        "DC_6B392C92DA0A",
        veco_m_url,
        "calls:WATCH_AXCELIS;calls:D_VECO_20261102_ACLS_MERGER;calls:ECL061;calls:EV058;calls:EE061",
        "",
        veco_m_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(veco_20261102_axcelis_merger_update.txt)，新增WATCH_AXCELIS并写入EV058",
    )

    soi_dt, soi_title, soi_url, soi_fs, _ = _dc_meta(
        dc_index,
        "DC_86F8DBF8F95E",
        "2026-11-18",
        "https://www.soitec.com/home/group/corporate/newsroom/press-releases/content/2026/11/18/soitec-reports-second-quarter-revenue-and-half-year-results-of-fiscal-year-2027",
        "Soitec Reports Second Quarter Revenue And Half-Year Results Of Fiscal Year 2027",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Soitec",
        "SOI",
        "overseas_positive_rule_rescued",
        soi_dt,
        f"{soi_title}（Photonics-SOI H1收入约1.25亿美元、客户签约约12亿美元带现金定金产能预留协议至2028，Bernin 4厂转向SOI扩产）",
        "DC_86F8DBF8F95E",
        soi_url,
        "calls:S_SOI_2027H1;calls:CL083;calls:D_SOI_20261118_FY27H1;calls:ECL062;calls:EV059;calls:EE062",
        "",
        soi_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(soi_20261118_fy27h1_results.txt)，将calls/sources.csv最新财报推进至2026-11-18(S_SOI_2027H1)并写入CL083/EV059",
    )

    anet_dt, anet_title, anet_url, anet_fs, _ = _dc_meta(
        dc_index,
        "DC_C85C91649A7A",
        "2026-11-03",
        "https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Third-Quarter-2026-Financial-Results/default.aspx",
        "Arista Networks, Inc. Reports Third Quarter 2026 Financial Results",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "Arista Networks",
        "ANET",
        "overseas_positive_rule_rescued",
        anet_dt,
        f"{anet_title}（Q3营收36.576亿美元+58.5% YoY、Q4指引39-40亿美元；业绩稿聚焦ESUN交换机架构未拆分光模块或CPO口径）",
        "DC_C85C91649A7A",
        anet_url,
        "calls:S_ANET_2026Q3;calls:D_ANET_20261103_Q3",
        "",
        anet_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(anet_20261103_2026q3_results.txt)，滚动入S_ANET_2026Q3并以no_relevant_claims登记D_ANET_20261103_Q3",
    )

    crdo_o_dt, crdo_o_title, crdo_o_url, crdo_o_fs, _ = _dc_meta(
        dc_index,
        "DC_89DB234EEA46",
        "2026-11-04",
        "https://investors.credosemi.com/news-events/news/news-details/2026/Credo-and-Oracle-Advance-Optical-Transceiver-Telemetry-Standardization-with-OCP-Community/default.aspx",
        "Credo and Oracle Advance Optical Transceiver Telemetry Standardization with OCP Community",
    )
    add(
        "P1",
        "T2_supply_relationship_or_ma",
        "ingested_to_kb",
        "Credo × Oracle",
        "CRDO/WATCH_ORCL",
        "overseas_positive_rule_rescued",
        crdo_o_dt,
        f"{crdo_o_title}（OCP社区正式批准双方联合主导的两项光模块增强遥测开放规范，严格限定为标准合作不外推商业采购份额）",
        "DC_89DB234EEA46",
        crdo_o_url,
        "calls:D_CRDO_20261104_ORCL_OCP;calls:ECL063;calls:EV060;calls:EE063;timeline:TL9011",
        "",
        crdo_o_fs,
        "2026-11-22",
        "正向标题规则挽救并HTTP 200归档全文(crdo_20261104_oracle_ocp_telemetry.txt)，写入EV060与关系时间线TL9011",
    )

    keys_dt, keys_title, keys_url, keys_fs, keys_ls = _dc_meta(
        dc_index,
        "DC_35C4F1F433DF",
        "2026-11-19",
        "https://investor.keysight.com/investor-news-and-events/financial-press-releases/press-release-details/2026/Keysight-Technologies-Reports-Fourth-Quarter-and-Fiscal-Year-2026-Results/default.aspx",
        "Keysight Technologies Reports Fourth Quarter and Fiscal Year 2026 Results",
    )
    add(
        "P2",
        "T4_universe_blindspot",
        "watch_deferred",
        "Keysight Technologies",
        "WATCH_KEYS",
        "overseas_positive_rule_rescued",
        keys_dt,
        f"{keys_title}（观察池测试设备商FY26Q4综合财报留痕：按WATCH_KEYS边界通信测试总收入不等同800G/1.6T光模块测试收入）",
        "DC_35C4F1F433DF",
        keys_url,
        "",
        "WATCH_KEYS属事件监控观察主体(不在universe.csv 39家季度槽位池内)，仅在后续发布明确224G/1.6T/3.2T光测试客户采纳专项公告时再抓核建事件",
        keys_fs,
        keys_ls,
        "正向标题规则挽救入队防滚动窗丢失：严守calls/watch_entities.csv口径不虚挂calls引用，归watch_deferred留痕备查",
    )

    # =========================================================================
    # 自动兜底闭环：凡在 dc_index 命中 positive_rule 但尚未出现在上文引用中的 DC_* 一律确定性入队
    # =========================================================================
    enrolled_refs_blob = "\n".join(spec["candidate_or_qa_ref"] for spec in raw_specs)
    remaining_positive_dcs = [
        (did, info)
        for did, info in sorted(
            dc_index.items(),
            key=lambda kv: ((kv[1]["row"].get("published_at") or "").strip(), kv[0]),
        )
        if info.get("triage_bucket") == "positive_rule" and did not in enrolled_refs_blob
    ]
    for did, info in remaining_positive_dcs:
        r = info["row"]
        pub = (r.get("publisher_entity_id") or "UNKNOWN").strip()
        ent_name = entity_names.get(pub, pub)
        pub_dt = (r.get("published_at") or info["first_seen"]).strip()
        title = (r.get("title") or did).strip()
        url = (r.get("canonical_url") or "").strip()
        ttype = str(info.get("trigger_type") or "T1_lifecycle_shift")
        if did in _TRIAGED_DEFERRED_POSITIVE_DC_NOTES:
            add(
                "P2",
                ttype,
                "watch_deferred",
                ent_name,
                pub,
                "overseas_positive_rule_triaged",
                pub_dt,
                title,
                did,
                url,
                "",
                "待出现明确光模块/光芯片细分定量或具名客户状态跃迁时再拉取全文升格",
                info["first_seen"],
                info["last_seen"],
                _TRIAGED_DEFERRED_POSITIVE_DC_NOTES[did],
            )
        else:
            # 未来新快照若出现未人工初筛的正向规则命中项，自动进 pending_primary_text 绝不静默丢弃
            add(
                "P1",
                ttype,
                "pending_primary_text",
                ent_name,
                pub,
                "overseas_positive_rule_auto",
                pub_dt,
                title,
                did,
                url,
                "",
                "正向标题规则自动命中新披露：需拉取第一方官网全文核实光模块/光器件细分口径与生命周期阶段后裁决",
                info["first_seen"],
                info["last_seen"],
                "防静默丢噪音自动入列保护：未人工核阅前严禁归入噪音或直接写正史",
            )

    # =========================================================================
    # DRQ0098 .. DRQ0105: Step 5 11月中旬四大盲区新线索一手核查与波长光电两用物项诉讼入列
    # =========================================================================
    add(
        "P1",
        "T2_supply_relationship_or_ma",
        "pending_filing_anchor",
        "朗特智能 / 成都奥捷",
        "300916",
        "cninfo_filing_blindspot",
        "2026-11-17",
        "深交所公告2026-042(1225674762.PDF)：朗特智能拟现金6.63亿元收购成都奥捷通信技术有限公司51%股权(10G-3.2T光无源连接器件/光隔离器，2026年1-7月审计营收3.58亿元/归母净利5,081.67万元，2026-2028承诺净利0.8/1.2/1.6亿元)",
        "CLOUD_20261117_LONGTECH_AOJIE;FILING_300916_20261117_042",
        "https://static.cninfo.com.cn/finalpage/2026-11-17/1225674762.PDF",
        "",
        "300916不在v6 _frozen分母内(一手原件已归档corpus/web/step5_20261122/blindspots/)；2026-11-16签署的附条件生效《股权收购协议》尚待2026-12-02第三次临时股东会审议批准及工商交割过户，未交割前严禁入points.csv D6/D9",
        "2026-11-17",
        "2026-11-22",
        "2026-11-22巨潮抓回2026-042公告及董事会决议核清法定全称成都奥捷通信技术有限公司并补入tree.yaml观察池(N174/N179)，留置pending_filing_anchor跟踪股东会与交割进展",
    )
    add(
        "P0",
        "T2_supply_relationship_or_ma",
        "pending_filing_anchor",
        "科瑞思 / 宏钢光电",
        "301314",
        "cninfo_filing_blindspot",
        "2026-10-26",
        "301314重大资产重组预案(1225620972.PDF)：拟发行股份及支付现金购买深圳市宏钢光电封装技术股份有限公司100%股份(光通信金属与HTCC陶瓷气密管壳/TO封装外壳/预置金锡热沉，2026H1未经审计营收2.89亿元/净利2,463.77万元)",
        "CLOUD_20261026_KERUISI_HONGGANG;FILING_301314_20261026_PREPLAN",
        "https://static.cninfo.com.cn/finalpage/2026-10-26/1225620972.PDF",
        "points:P258",
        "已落盘1225620972.PDF重组预案至corpus/ir/301314/，但截至2026-11-22标的审计评估尚未办结、交易作价与业绩补偿协议未定、暂未召开股东会且未获深交所审核与证监会注册交割；未交割前严禁并入301314上市公司能力点",
        "2026-10-26",
        "2026-11-22",
        "2026-11-22归档301314重组预案核实P258/N138股份制现名深圳市宏钢光电封装技术股份有限公司并同步更新tree.yaml与entity-registry.yaml，留置pending_filing_anchor盯防正式重组报告书及交割",
    )
    add(
        "P1",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "波长光电",
        "301421",
        "cninfo_filing_compliance",
        "2026-10-08",
        "深交所公告2026-037(1225597511.PDF)：收到沪检三分刑诉〔2026〕176号起诉书，因2023-08至2025-04出口光学镜片2,010.85万元未按规定办理两用物项出口许可证进入公诉起诉阶段(尚未审理判决)",
        "CLOUD_20261012_BOCHANG_DUALUSE;FILING_301421_20261008_037",
        "https://static.cninfo.com.cn/finalpage/2026-10-08/1225597511.PDF",
        "knowledge:KN013",
        "",
        "2026-10-12",
        "2026-11-22",
        "2026-11-22归档301421 2026-037起诉书公告原件(corpus/ir/301421/)，核准涉案光学镜片金额20,108,512.11元与未办两用物项出口许可证公诉阶段事实，写入knowledge.yaml KN013办结",
    )
    add(
        "P0",
        "T4_universe_blindspot",
        "pending_filing_anchor",
        "上海羲禾科技",
        "IPO_STAR_XIHE",
        "sse_ipo_prospectus",
        "2026-10-23",
        "科创板招股书注册稿(002212_20261014_U3DB.pdf)与证监许可〔2026〕2940号批复：2026H1营收5.69亿元/归母净利1.61亿元，400G/800G/1.6T硅光芯片及1.6T NPO/CPO芯片实现销售，单芯片3.2T/6.4T处终端验证与募投在研阶段",
        "CLOUD_20261025_XIHE_IPO_REG;SSE_AUDIT_2212",
        "https://static.sse.com.cn/stock/disclosure/announcement/c/202610/002212_20261014_U3DB.pdf",
        "",
        "已落盘上交所招股书注册稿及证监会注册批复至blindspots/并补入tree.yaml观察池(N175)；截至2026-11-22尚未发行挂牌分配688股票代码且前五大客户匿名披露(占比92.26%)，待正式挂牌与v7分母扩容审阅后入points.csv C4",
        "2026-10-12",
        "2026-11-22",
        "2026-11-22核实上交所一手注册稿与证监许可〔2026〕2940号原件，严格区分1.6T已实现销售与单波400G样品展示/3.2T-6.4T终端验证及18.30亿元募投边界",
    )
    add(
        "P1",
        "T4_universe_blindspot",
        "watch_deferred",
        "粤芯半导体",
        "301660",
        "cninfo_ipo_prospectus",
        "2026-10-12",
        "301660招股书(1225590835.PDF)与上市公告书(2026-10-13上市)：主营12英寸模拟及功率晶圆代工(2025营收25.11亿元未单列硅光)，90nm SiPho累计投片超7,000片支持400G-1.6T，3.2T NPO正在导入且65nm硅光/CPO属7.70亿元募投在研",
        "CLOUD_20261029_CANSEMI_SIPHO;FILING_301660_20261008_PROSPECTUS",
        "https://static.cninfo.com.cn/finalpage/2026-10-08/1225590835.PDF",
        "",
        "301660系v6冻结后创业板新上市综合晶圆代工厂(不在_frozen.csv内，一手原件存blindspots/)，定期财报(含2026Q3季报)未拆分硅光代工收入且3.2T NPO仅处导入阶段，暂列tree.yaml观察池归watch_deferred备v7扩容评估",
        "2026-09-16",
        "2026-11-22",
        "2026-11-22抓回301660招股书/上市公告书/募投说明/三季报逐字核实，纠偏媒体夸大口径(3.2T NPO实为正在导入、65nm硅光及光电共封实为募投研发项目)并补入观察池(N176)",
    )
    add(
        "P2",
        "T1_lifecycle_shift",
        "watch_deferred",
        "Optical Internetworking Forum (OIF)",
        "STD_OIF",
        "overseas_standards_release",
        "2026-11-11",
        "OIF Launches Seven New Technical Projects at Q4 Member Meeting(曼谷会议正式立项EEI-448G RTLR半重定时电接口、O波段单模BiDi 200G/Lane、ELSFP IA 3.0及支持40W Class 8高功率模式的Type-3加长型ELSFP等7项标准)",
        "CLOUD_20261114_OIF_448G_40W_ELSFP",
        "https://www.oiforum.com/oif-launches-seven-new-technical-projects-at-q4-member-meeting-reflecting-accelerating-demand-for-next-generation-connectivity/",
        "",
        "OIF属行业标准组织(非calls公司主体)，7项规范均处新启动标准起草立项阶段而非商业芯片/模块出货，归watch_deferred留存一手标准锚",
        "2026-11-14",
        "2026-11-22",
        "2026-11-22 HTTP 200归档oiforum.com曼谷Q4官稿全文(oif_2026-11-11_q4_seven_new_projects_448g_rtlr_40w_elsfp.txt)，锁定单波400G电接口与40W外置光源标准立项时态",
    )
    add(
        "P0",
        "T1_lifecycle_shift",
        "ingested_to_kb",
        "NVIDIA × Lambda",
        "NVDA/WATCH_LAMBDA",
        "overseas_official_release",
        "2026-11-16",
        "SC26双源官宣：Lambda在加拿大魁北克142MW园区规模化部署NVIDIA Photonics CPO交换机(单机144×800Gb/s端口+18个可更换外置光源)连接超10,000颗Blackwell Ultra GPU(GB300 NVL72)，光学中位温度36°C(可插拔51°C)、Pod级延迟降10.1%",
        "CLOUD_20261117_NVDA_LAMBDA_SC26_CPO",
        "https://blogs.nvidia.com/blog/lambda-photonics/",
        "calls:WATCH_LAMBDA;calls:D_NVDA_20261116_LAMBDA_CPO;calls:D_LAMBDA_20261116_NVDA_CPO;calls:ECL064;calls:ECL065;calls:EV061;calls:EE064;calls:EE065",
        "",
        "2026-11-17",
        "2026-11-22",
        "2026-11-22同时抓回NVIDIA官网博客与Lambda官网客户公告两份HTTP 200原稿(BusinessWire镜像403)，通过calls check写入双源互证corroborated事件EV061并补入观察池(N178)",
    )
    add(
        "P2",
        "T4_universe_blindspot",
        "watch_deferred",
        "安费诺(Amphenol)",
        "APH",
        "overseas_conference_showcase",
        "2026-11-16",
        "SC26展台(Booth 2546)展示12.8T XPO-LPO线性可插拔光模块(64×224Gb/s PAM4，约80W液冷)与448G OverPass/CPC互连方案(amphenol-cs.com返回HTTP 403，investors.amphenol.com未发SC26正式稿)",
        "CLOUD_20261116_APH_SC26_XPO_LPO",
        "https://www.amphenol-cs.com/connect/super-computing-2026.html",
        "",
        "NYSE:APH不在_frozen分母及calls池内；amphenol-cs.com活动页与规格书CDN均返回HTTP 403且IR站无SC26正式新闻稿，已对称补入tree.yaml观察池(N177)，待后续SEC年报或开放静态官方稿披露客户采纳后再升格",
        "2026-11-16",
        "2026-11-22",
        "2026-11-22实测amphenol-cs.com返回HTTP 403严守红线零绕过，与泰科电子对称补入tree.yaml观察池并以宇宙外展会演示线索归入watch_deferred备查",
    )

    rows_out: list[dict[str, str]] = []
    for idx, spec in enumerate(raw_specs, start=1):
        row = {"queue_id": f"DRQ{idx:04d}"}
        row.update(spec)
        rows_out.append(row)
    return rows_out


def _load_known_kn_ids() -> set[str]:
    """读取 knowledge.yaml 中已注册的 KN### 编号集合（缺失或无 yaml 时返回空集）."""
    kp = ROOT / "knowledge.yaml"
    if not kp.is_file():
        return set()
    try:
        import yaml  # type: ignore

        kb = (yaml.safe_load(kp.read_text(encoding="utf-8")) or {}).get("knowledge") or []
        return {
            str(item.get("id") or "").strip()
            for item in kb
            if isinstance(item, dict) and str(item.get("id") or "").strip()
        }
    except Exception:
        return set()


def validate_queue_rows(
    rows: list[dict[str, str]],
    fieldnames: list[str] | None = None,
    expected_triggered_dc_ids: set[str] | None = None,
    known_kn_ids: set[str] | None = None,
) -> list[str]:
    """校验 review_queue.csv 行级与表级硬门约束，返回错误列表(空列表表示全绿)."""
    errors: list[str] = []
    if fieldnames is not None and list(fieldnames) != QUEUE_COLUMNS:
        errors.append(f"表头不匹配: 期望 {QUEUE_COLUMNS}, 实际 {list(fieldnames)}")
    if not rows:
        errors.append("review_queue.csv 为空")
        return errors

    resolved_kns = _load_known_kn_ids() if known_kn_ids is None else set(known_kn_ids)

    seen_ids: set[str] = set()
    for idx, r in enumerate(rows, start=2):
        qid = (r.get("queue_id") or "").strip()
        if not re.fullmatch(r"DRQ\d{4}", qid):
            errors.append(f"第{idx}行 queue_id 非法(须为 DRQ####): {qid!r}")
        elif qid in seen_ids:
            errors.append(f"第{idx}行 queue_id 重复: {qid}")
        else:
            seen_ids.add(qid)

        for col in QUEUE_COLUMNS:
            val = str(r.get(col) or "")
            if "\n" in val or "\r" in val:
                errors.append(f"{qid or idx} 字段 {col} 含内嵌换行符")
            for bad in FORBIDDEN_PHRASES:
                if bad in val:
                    errors.append(f"{qid or idx} 字段 {col} 含禁用完结词 {bad!r}")

        prio = (r.get("priority") or "").strip()
        if prio not in VALID_PRIORITIES:
            errors.append(f"{qid} priority 非法: {prio!r}")

        ttype = (r.get("trigger_type") or "").strip()
        if ttype not in VALID_TRIGGER_TYPES:
            errors.append(f"{qid} trigger_type 非法: {ttype!r}")

        st = (r.get("status") or "").strip()
        if st not in VALID_STATUSES:
            errors.append(f"{qid} status 非法: {st!r}")

        if st.startswith("pending_") and not (r.get("missing_verification_gate") or "").strip():
            errors.append(f"{qid} status={st} 必须填写非空 missing_verification_gate")

        kb_ref = (r.get("kb_target_ref") or "").strip()
        if st == "ingested_to_kb" and not kb_ref:
            errors.append(f"{qid} status=ingested_to_kb 必须填写非空 kb_target_ref")
        if kb_ref:
            toks = [x.strip() for x in kb_ref.split(";")]
            if any(not x for x in toks):
                errors.append(f"{qid} kb_target_ref 含空分号项: {kb_ref!r}")
            for tok in (x for x in toks if x):
                if ":" not in tok:
                    errors.append(f"{qid} kb_target_ref 缺少 prefix:id 冒号: {tok!r}")
                    continue
                pfx, tid = [p.strip() for p in tok.split(":", 1)]
                if pfx not in VALID_KB_PREFIXES:
                    errors.append(f"{qid} kb_target_ref 前缀非法: {tok!r}")
                elif pfx == "points" and not re.fullmatch(r"P\d{3}", tid):
                    errors.append(f"{qid} kb_target_ref points 编号格式非法: {tok!r}")
                elif pfx == "edges" and not re.fullmatch(r"E\d{3}", tid):
                    errors.append(f"{qid} kb_target_ref edges 编号格式非法: {tok!r}")
                elif pfx == "timeline" and not re.fullmatch(r"TL\d{4}", tid):
                    errors.append(f"{qid} kb_target_ref timeline 编号格式非法: {tok!r}")
                elif pfx == "knowledge":
                    if not re.fullmatch(r"KN\d{3}", tid):
                        errors.append(f"{qid} kb_target_ref knowledge 编号格式非法(须为 KN###): {tok!r}")
                    elif resolved_kns and tid not in resolved_kns:
                        errors.append(f"{qid} kb_target_ref knowledge 引用悬空: {tok!r}")
                elif not tid:
                    errors.append(f"{qid} kb_target_ref 目标 ID 为空: {tok!r}")

        if not (r.get("entity_name") or "").strip():
            errors.append(f"{qid} entity_name 为空")
        if not (r.get("title_or_claim") or "").strip():
            errors.append(f"{qid} title_or_claim 为空")

    # 必备高优锚定项与 9 项 10-11 月挽救项存在性自检
    ref_blob = "\n".join((r.get("candidate_or_qa_ref") or "") for r in rows)
    must_refs = (
        "DC_501FC1F61B62",
        "DC_573401DC530B",
        "DC_3841FCD60F32",
        "DC_FD32C455D502",
        "DC_430D7977BA22",
        "D-394c94777fd5c6",
        "O-e7f841fc059d4922f456",
        *RESCUED_OCT_NOV_FOCAL_DC_IDS,
    )
    for must_ref in must_refs:
        if must_ref not in ref_blob:
            errors.append(f"review_queue.csv 缺少必保高优/挽救引用: {must_ref}")

    if expected_triggered_dc_ids is not None:
        missing_dc = sorted(did for did in expected_triggered_dc_ids if did not in ref_blob)
        if missing_dc:
            errors.append(f"review_queue.csv 遗漏已触发(seeded+positive_rule)海外披露: {missing_dc}")

    return errors


def build_readme(triage_stats: dict[str, Any]) -> str:
    """生成确定性 corpus/daily_review/README.md."""
    ov_all = triage_stats["overseas_staging"]["seeded_plus_positive_rules_split"]
    ov_sn = triage_stats["overseas_staging"]["sep_to_nov_2026_seeded_plus_positive_rules_split"]
    bf = triage_stats["historical_backfill_20261109"]
    qs = triage_stats["persistent_queue"]
    gm = triage_stats.get("gemini_cloud_snapshot") or {}
    if gm.get("available"):
        gm_line = (
            f"- **Gemini 云端日更快照水位监控（`cloud-snapshot.json` 只读对账）**：共检测到 "
            f"`{gm['total_daily_entries']}` 条 `[YYYY-MM-DD]` 逐日纪要（`{gm['earliest_entry_date']}` 至 "
            f"`{gm['latest_entry_date']}`），人工分流核对水位 `triaged_through_date={gm['triaged_through_date']}`，"
            f"水位后未分流新增日期 `untriaged_entry_dates={gm['untriaged_entry_dates']}`（`{gm['untriaged_entry_count']}` 条）。"
        )
    else:
        gm_line = (
            f"- **Gemini 云端日更快照水位监控（`cloud-snapshot.json` 只读对账）**：当前外部快照文件不可用"
            f"（`available=False`，基准水位 `triaged_through_date={gm.get('triaged_through_date', GEMINI_TRIAGED_THROUGH_DATE)}`）。"
        )

    return f"""# Daily 状态跃迁过滤（种子 + 正向规则 + 高置信噪音 + Unclassified）与持久审核池 (`corpus/daily_review/`)

## 1. 设计目标与三条硬边界铁律

日常监控流（海外官网/新闻室 RSS、国内深沪投关记录表与互动易问答、云端日更摘要）每日产生大量非结构化文本。本目录建立确定性的 **四桶透明分流 + 持久审核池** 机制，严格执行三条硬边界铁律：

1. **严禁未知条目静默归噪音**：`_classify_overseas_noise()` 仅识别四类高置信度明确噪音（律所征集、获奖/人事/CSR、IR 日历/电话会预告页、综合巨头非光业务线）；凡未命中正向规则亦未命中高置信噪音的条目，一律诚实标为 **`unclassified`** 单独统计（`{ov_all['unclassified_count']}` 条，`{ov_all['unclassified_pct']}%`），供人工定期抽检召回率，杜绝把未覆盖财报或并购伪装成已审噪音。
2. **防滚动窗滑出丢失（永不过期挂起）**：`overseas/staging/` 的 14 天滚动窗口仅作采集缓冲（全量 `{triage_stats['overseas_staging']['unique_disclosure_candidates_all']}` 条唯一披露候选中已有 `{triage_stats['overseas_staging']['slid_out_of_rolling_window_total']}` 条滑出最新日窗口）。全部 **`{ov_all['triggered_total_count']}`** 条触发项（历史种子 `{ov_all['seeded_triggered_count']}` 条 + 正向标题规则命中 `{ov_all['positive_rule_triggered_count']}` 条，含 10–11 月挽救的 `MTSI FY26Q4`、`TSEM Q3`、`GFS Q3`、`VECO Q3`、`VECO×ACLS`、`SOI FY27H1`、`ANET Q3`、`CRDO×ORCL`、`KEYS FY26Q4`）100% 固化入 `review_queue.csv`，退出滚动窗后永不自动删除。
3. **防未核传闻/动态空壳/未交割协议污染正史**：凡源站返回动态空 JS 壳（`DRQ0037` LWLG QuoteMedia）、未上市私企缺独立一手规格书/IPO 稿（`DRQ0048` 微见智能、`DRQ0049` 镭神技术）、具名客户保密未披露（`DRQ0050` 科瑞技术 U11）、股权收购/重组尚未过会交割（`DRQ0053` 利扬芯片拟购众望达 51%、`DRQ0098` 朗特智能拟购成都奥捷 51%、`DRQ0099` 科瑞思拟购宏钢光电 100% 预案）、科创板注册生效尚未挂牌（`DRQ0101` 上海羲禾科技）或仅处验证未获大单（`DRQ0052` 长光华芯 200G EML），一律诚实留置 `pending_*` 并写明 `missing_verification_gate`，严禁虚挂引用。

---

## 2. 海外 Staging 四桶透明分流规则 (`seeded_plus_positive_rules_split`)

- **正向入队桶（`SEEDED_OVERSEAS_DC_IDS` + `_classify_overseas_positive_rule`）**：除 `25` 条历史种子外，对全部受追踪海外实体执行确定性标题触发规则（命中 `Financial Results / Quarter / Half-Year / Full-Year / Interim Results / 10-Q / 10-K / 8-K / Merger / Acquire / Combine / 800G / 1.6T / 3.2T / 6.4T / CPO / NPO / InP / EML / Silicon Photonics / Transceiver / Co-packaged` 等），100% 纳入 `review_queue.csv`。
- **四类明确高置信噪音（`HIGH_CONFIDENCE_NOISE_CLASSES`）**：
  - `non_optical_corporate_line`：综合巨头非光通信产品线通稿（VMware/Splunk/Webex/游戏显卡/5G FWA/汽车电子等）。
  - `award_ranking_hr_csr`：企业获奖榜单（Forbes/TIME）、高管任免、高校捐赠、社会责任与招聘公关稿。
  - `investor_lawsuit_spam`：美股证券律所集体诉讼征集广告。
  - `ir_calendar_or_index_page`：财报发布日期预告、业绩电话会排期通知、静态 SEC Filings 列表页。
- **未分类抽检池（`unclassified`）**：未命中正向触发词亦不属于上述四类明确噪音的一般企业通稿，单独保留计数供召回率抽检。
{gm_line}

### 实测分流统计（截至 `{triage_stats['as_of_date']}`）

| 数据源分母 | 唯一候选总数 | 种子+正向规则触发数 (占比) | 高置信明确噪音数 (占比) | `unclassified` 待抽检数 (占比) |
|---|---:|---:|---:|---:|
| 海外 `staging/` 9–11月披露日口径 (`published_at >= 2026-09-01`) | `{ov_sn['total_unique_disclosures']}` | `{ov_sn['triggered_total_count']}` (`{ov_sn['triggered_total_pct']}%`: 种子 `{ov_sn['seeded_triggered_count']}` + 规则 `{ov_sn['positive_rule_triggered_count']}`) | `{ov_sn['high_confidence_noise_count']}` (`{ov_sn['high_confidence_noise_pct']}%`) | `{ov_sn['unclassified_count']}` (`{ov_sn['unclassified_pct']}%`) |
| 海外 `staging/` 全量 `{triage_stats['overseas_staging']['snapshot_count']}` 期快照唯一 `DC_*` | `{ov_all['total_unique_disclosures']}` | `{ov_all['triggered_total_count']}` (`{ov_all['triggered_total_pct']}%`: 种子 `{ov_all['seeded_triggered_count']}` + 规则 `{ov_all['positive_rule_triggered_count']}`) | `{ov_all['high_confidence_noise_count']}` (`{ov_all['high_confidence_noise_pct']}%`) | `{ov_all['unclassified_count']}` (`{ov_all['unclassified_pct']}%`) |
| 历史回填审阅 `daily-backfill-review-20261109` (`D-/O-/G-`) | `{bf['total_rows']}` | 去重高优样本全部并入持久队列（保留 `D-/O-/G-` 映射） | `{bf['auto_folded_clue_or_mechanical_rows']}` (`{bf['auto_folded_pct']}%` 线索/待定位/机械召回) | `0` |

---

## 3. 四类状态跃迁触发门槛 (`trigger_type`)

1. **`T1_lifecycle_shift`（代际/认证/量产/产能、合规法条与季度财报跃迁）**：800G/1.6T/3.2T/6.4T、200G EML、CPO/NPO、LPO/ALC、InP/Photonics-SOI 衬底扩产、进出口法规判例及最新季度正式财报（如 `DRQ0046` 挂 `KN011-KN014`、`DRQ0100` 波长光电两用镜片诉讼挂 `KN013`、`DRQ0104` NVIDIA×Lambda 魁北克万卡级 CPO 集群双源互证 `EV061`、云南锗业 `2026-057` 公告 `18,856->26,999万元`、Soitec `~12亿美元` 产能预留协议）。
2. **`T2_supply_relationship_or_ma`（供应链实名绑定、并购协议/交割与标准合作）**：具名上下游关系（GFS×Marvell SiGe 扩产长约、Tower×中际旭创 NPO 早期生产、IQE×Quintessent QDL 外延协议、Credo×Oracle OCP 遥测标准）及重大并购（Marvell×Lumentum 全股票协议未交割、Veeco×Axcelis 顺延至 `2027Q1` 末、利扬芯片拟购众望达 51% 未交割、朗特智能拟购成都奥捷 51% 待股东会与交割、科瑞思拟购宏钢光电 100% 预案审计评估进行中）。
3. **`T3_commitment_verification`（管理层公开承诺与长期采购承诺原文裁决）**：`calls/commitments.csv` 到期核验及 Lumentum FY27Q1 逾 `50亿美元` `NPO/CPO win` 四重边界锁定。
4. **`T4_universe_blindspot`（公司宇宙补录、设备层对称性与观察池纳管）**：联讯仪器 `688808`、云南锗业 `002428`、科瑞技术 `002957`、天准科技 `688003`（`P277` CPO 在线 AOI 小批量交付）及圈外新核实主体（上海羲禾科技、粤芯半导体 `301660`、成都奥捷、安费诺 `APH`、Lambda）观察池追踪。

---

## 4. 队列状态机与机器门约束 (`review_queue.csv`)

当前持久队列共 **`{qs['total_rows']}`** 行（`P0={qs['by_priority'].get('P0', 0)}`、`P1={qs['by_priority'].get('P1', 0)}`、`P2={qs['by_priority'].get('P2', 0)}`）：

- **`ingested_to_kb`（`{qs['by_status'].get('ingested_to_kb', 0)}` 行）**：经一手原件（巨潮 `%PDF-` / 政府公报 / 官网 HTTP 200 静态存档）逐字核对并写入主账本；**硬门要求 `kb_target_ref` 非空且在六类主表（`points` / `edges` / `content` / `timeline` / `calls` / `knowledge`）真实存在**。
- **`pending_primary_text`（`{qs['by_status'].get('pending_primary_text', 0)}` 行）**：受源站动态 JS 空壳限制暂未入正史（仅 `DRQ0037` LWLG 在列；原 `DRQ0046` 合规政策池已取一手公报写入 `KN011-KN014` 办结）；**硬门要求 `missing_verification_gate` 非空**。
- **`pending_filing_anchor`（`{qs['by_status'].get('pending_filing_anchor', 0)}` 行）**：客观受限于未上市私企披露、客户 NDA 保密、产品仍在客户端验证、科创板注册生效尚未挂牌或收购重组尚未过会交割（`DRQ0048/0049/0050/0052/0053/0098/0099/0101`）；**硬门要求 `missing_verification_gate` 非空**。
- **`watch_deferred`（`{qs['by_status'].get('watch_deferred', 0)}` 行）**：经核查属树外系统板（`DRQ0032` 沪电交换机 PCB）、极小比例不并表参股科研验收（`DRQ0054` 经纬辉开 7.71%）、观察池非季度槽主体（`DRQ0064` Keysight `WATCH_KEYS`）、圈外新上市综合晶圆代工/标准立项/展会演示线索（`DRQ0102` 粤芯半导体、`DRQ0103` OIF Q4 标准立项、`DRQ0105` 安费诺 SC26 展台）及正向标题规则入池留痕的泛半导体/EMS/展前预告项，永久保留防滑出丢失且零虚挂引用。

### 幂等构建与机器校验命令

```bash
# 确定性重建 review_queue.csv / triage_stats.json / README.md
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --build

# 零写入校验磁盘文件与重算结果字节级一致及全部硬门不变量
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --check
```
"""


def compute_all_artifacts() -> tuple[str, str, str, dict[str, Any]]:
    """纯内存计算全部三份产物文本与统计字典."""
    dc_index, ov_stats = scan_overseas_staging()
    _, bf_stats = scan_backfill_review()
    gemini_stats = scan_gemini_cloud_snapshot()
    kerui_in_frozen = _check_kerui_in_frozen_and_annual()

    rows = build_queue_rows(dc_index, kerui_in_frozen=kerui_in_frozen)
    expected_trig_dcs = set(SEEDED_OVERSEAS_DC_IDS) | set(ov_stats["positive_rule_triggered_dc_ids"])
    errs = validate_queue_rows(rows, QUEUE_COLUMNS, expected_triggered_dc_ids=expected_trig_dcs)
    if errs:
        raise ValueError("review_queue 硬门自检失败:\n  - " + "\n  - ".join(errs))

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_text = buf.getvalue()

    phys_lines = len(csv_text.split("\n")) - (1 if csv_text.endswith("\n") else 0)
    if phys_lines != len(rows) + 1:
        raise ValueError(f"review_queue.csv 物理行数({phys_lines}) != 逻辑行数+1({len(rows)+1})")

    by_status = Counter(r["status"] for r in rows)
    by_priority = Counter(r["priority"] for r in rows)
    by_trigger = Counter(r["trigger_type"] for r in rows)

    triage_stats: dict[str, Any] = {
        "schema_version": 2,
        "as_of_date": ov_stats["snapshot_end_date"],
        "kerui_002957_in_frozen_universe": kerui_in_frozen,
        "overseas_staging": ov_stats,
        "historical_backfill_20261109": bf_stats,
        "gemini_cloud_snapshot": gemini_stats,
        "persistent_queue": {
            "total_rows": len(rows),
            "by_status": dict(sorted(by_status.items())),
            "by_priority": dict(sorted(by_priority.items())),
            "by_trigger_type": dict(sorted(by_trigger.items())),
            "all_queue_ids_unique": True,
            "all_pending_have_verification_gate": True,
            "all_ingested_have_kb_target_ref": True,
            "all_triggered_overseas_dc_enrolled": True,
        },
    }
    stats_text = json.dumps(triage_stats, ensure_ascii=False, indent=2) + "\n"
    readme_text = build_readme(triage_stats)

    for fname, content in (
        ("review_queue.csv", csv_text),
        ("triage_stats.json", stats_text),
        ("README.md", readme_text),
    ):
        for bad in FORBIDDEN_PHRASES:
            if bad in content:
                raise ValueError(f"{fname} 出现禁用完结措辞 {bad!r}")

    return csv_text, stats_text, readme_text, triage_stats


def _write_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = text.encode("utf-8")
    if path.exists() and path.read_bytes() == raw:
        return False
    path.write_bytes(raw)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="同步与核验 Daily 持久审核池")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--build", action="store_true", help="幂等生成或更新持久审核池文件")
    group.add_argument("--check", action="store_true", help="零写入核验落盘文件与重算结果一致")
    args = parser.parse_args(argv)

    csv_text, stats_text, readme_text, stats = compute_all_artifacts()
    targets = [
        (OUT_DIR / "review_queue.csv", csv_text),
        (OUT_DIR / "triage_stats.json", stats_text),
        (OUT_DIR / "README.md", readme_text),
    ]

    if args.check:
        drift: list[str] = []
        for path, expected in targets:
            if not path.exists():
                drift.append(f"缺失文件: {path.relative_to(ROOT)}")
            elif path.read_bytes() != expected.encode("utf-8"):
                drift.append(f"内容漂移(与确定性重算不一致): {path.relative_to(ROOT)}")
        q_path = OUT_DIR / "review_queue.csv"
        if q_path.exists():
            with q_path.open("r", encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                disk_rows = list(reader)
                hdr = list(reader.fieldnames or [])
            expected_trig_dcs = set(SEEDED_OVERSEAS_DC_IDS) | set(
                stats["overseas_staging"]["positive_rule_triggered_dc_ids"]
            )
            errs = validate_queue_rows(disk_rows, hdr, expected_triggered_dc_ids=expected_trig_dcs)
            drift.extend(errs)
        if drift:
            for d in drift:
                print(f"[FAIL] {d}", file=sys.stderr)
            return 1
        pq = stats["persistent_queue"]
        ov = stats["overseas_staging"]["sep_to_nov_2026_seeded_plus_positive_rules_split"]
        print(
            "daily_review check OK | "
            f"queue={pq['total_rows']} (ingested={pq['by_status'].get('ingested_to_kb',0)}, "
            f"pending_text={pq['by_status'].get('pending_primary_text',0)}, "
            f"pending_anchor={pq['by_status'].get('pending_filing_anchor',0)}, "
            f"deferred={pq['by_status'].get('watch_deferred',0)}) | "
            f"staging_sep_nov={ov['total_unique_disclosures']} "
            f"(triggered={ov['triggered_total_count']}, noise={ov['high_confidence_noise_count']}, "
            f"unclassified={ov['unclassified_count']})"
        )
        return 0

    changed_files = []
    for path, content in targets:
        if _write_if_changed(path, content):
            changed_files.append(str(path.relative_to(ROOT)))
    pq = stats["persistent_queue"]
    print(
        f"daily_review build OK | rows={pq['total_rows']} | "
        f"updated={len(changed_files)} ({', '.join(changed_files) if changed_files else 'zero-drift'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
