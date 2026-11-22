#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3 Shard Overseas & Relationship Timeline Increment (2026-11-21)

严格写入路径白名单（仅限以下文件，零触碰其他任何路径）：
  - calls/sources.csv
  - calls/claims.csv
  - calls/commitments.csv
  - calls/disclosures.csv
  - calls/events.csv
  - calls/event_claims.csv
  - calls/event_evidence.csv
  - calls/watch_entities.csv
  - corpus/relationships/relationship_timeline.csv
  - out/step3-daily-and-v6-20261121/shard-overseas-summary.json

幂等设计：所有表均按主键原地更新或有序追加，重跑多次输出字节级一致。
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scan  # noqa: E402
from calls.event_intelligence import derive_event_projection, load_event_facts  # noqa: E402
from calls.positioning import scan_forbidden_words  # noqa: E402
from calls.schema import FILES  # noqa: E402
from calls.validator import FROZEN_SOLUTION_LINKS, validate  # noqa: E402

TIMELINE_FIELDS = (
    "timeline_id",
    "relation_id",
    "supplier",
    "customer",
    "supplier_point_id",
    "customer_point_id",
    "period",
    "period_type",
    "event_date",
    "source_channel",
    "metric_kind",
    "value_raw",
    "numeric_value",
    "unit",
    "observe_type",
    "edge_grade",
    "source_edge_ids",
    "daily_ref_id",
    "anchor_url",
    "conflict",
    "notes",
)


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def format_csv_row(fieldnames: tuple[str, ...], row: dict[str, str], lineterminator: str) -> str:
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator=lineterminator)
    writer.writerow({field: row.get(field, "") for field in fieldnames})
    return buf.getvalue()


def read_csv_with_raw(
    path: Path, expected_fields: tuple[str, ...]
) -> tuple[str, list[tuple[dict[str, str], str]]]:
    raw_text = path.read_text(encoding="utf-8-sig")
    # Preserve exact physical lines when there are no embedded newlines
    phys_lines = raw_text.splitlines(keepends=True)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        actual = tuple(reader.fieldnames or ())
        if actual != expected_fields:
            raise ValueError(f"{path}: header mismatch: got {actual}, expected {expected_fields}")
        parsed = list(reader)
    if len(phys_lines) != len(parsed) + 1:
        raise ValueError(f"{path}: physical lines {len(phys_lines)} != parsed {len(parsed) + 1}")
    return phys_lines[0], list(zip(parsed, phys_lines[1:]))


def read_csv_rows(path: Path, expected_fields: tuple[str, ...]) -> list[dict[str, str]]:
    _, pairs = read_csv_with_raw(path, expected_fields)
    return [row for row, _ in pairs]


def write_csv_preserving_untouched(
    path: Path,
    fieldnames: tuple[str, ...],
    pk_field: str,
    rows: list[dict[str, str]],
    touched_pks: set[str],
    lineterminator: str,
) -> None:
    raw_by_pk: dict[str, str] = {}
    header_line = ",".join(fieldnames) + lineterminator
    if path.exists():
        hdr, pairs = read_csv_with_raw(path, fieldnames)
        if hdr.endswith(lineterminator):
            header_line = hdr
        for old_row, raw_line in pairs:
            pk = old_row[pk_field]
            if pk not in touched_pks and raw_line.endswith(lineterminator):
                raw_by_pk[pk] = raw_line

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(header_line)
        for row in rows:
            pk = row[pk_field]
            if pk in raw_by_pk:
                fh.write(raw_by_pk[pk])
            else:
                fh.write(format_csv_row(fieldnames, row, lineterminator))


def upsert_rows(
    rows: list[dict[str, str]],
    pk_field: str,
    updates: dict[str, dict[str, str]],
    append_order: list[str],
) -> tuple[list[str], list[str]]:
    index_by_pk = {row[pk_field]: idx for idx, row in enumerate(rows)}
    updated_ids: list[str] = []
    inserted_ids: list[str] = []

    for pk, changes in updates.items():
        if pk in index_by_pk:
            target = dict(rows[index_by_pk[pk]])
            target.update(changes)
            rows[index_by_pk[pk]] = target
            updated_ids.append(pk)

    for pk in append_order:
        record = updates[pk]
        if pk in index_by_pk:
            # Already present on re-run: ensure exact full-row idempotency
            target = dict(rows[index_by_pk[pk]])
            target.update(record)
            rows[index_by_pk[pk]] = target
        else:
            rows.append(dict(record))
            index_by_pk[pk] = len(rows) - 1
            inserted_ids.append(pk)

    return updated_ids, inserted_ids


def assert_no_forbidden_words(label: str, text: str) -> None:
    hits = scan_forbidden_words(text or "")
    if hits:
        raise AssertionError(f"{label} contains forbidden positioning business words {hits}: {text!r}")


def main() -> int:
    calls_dir = REPO_ROOT / "calls"
    rel_timeline_path = REPO_ROOT / "corpus" / "relationships" / "relationship_timeline.csv"
    cuts_path = REPO_ROOT / "corpus" / "relationships" / "edge_negative_cuts.csv"
    solution_links_path = calls_dir / "solution_links.csv"
    summary_path = SCRIPT_DIR / "shard-overseas-summary.json"

    sl_hash_before = sha256_bytes(solution_links_path)

    # ------------------------------------------------------------------
    # 1. Task 1: Sources, Claims & Commitments Adjudications (CM001-CM009)
    # ------------------------------------------------------------------
    sources = read_csv_rows(calls_dir / "sources.csv", FILES["sources.csv"])
    source_updates: dict[str, dict[str, str]] = {
        "S_AAOI_Q1_RESULT_A": {
            "url": "https://investors.ao-inc.com/2026-05-07-Applied-Optoelectronics-Reports-First-Quarter-2026-Results",
            "accessed_date": "2026-11-11",
            "acquisition_note": (
                "公司官方季度业绩材料；与C级逐字稿并列登记；"
                "原URL https://investors.ao-inc.com/node/17011 因IR站点迁移404，"
                "2026-11-11核验更新为同文官方带日期永久链接"
            ),
        },
        "S_CIEN_2026_FORUM": {
            "source_id": "S_CIEN_2026_FORUM",
            "company_id": "CIEN",
            "slot_label": "2026-InvestorForum",
            "period_end": "2026-09-16",
            "source_scope": "interquarter",
            "material_type": "transcript",
            "source_grade": "A",
            "url": "https://s25.q4cdn.com/550667411/files/doc_events/2026/09/16/Ciena-Investor-Forum-2026-Full-Transcript-of-the-Day-s-Events-Final.pdf",
            "local_path": "",
            "published_date": "2026-09-16",
            "accessed_date": "2026-11-11",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR托管的2026 Investor Forum完整官方逐字稿PDF；按interquarter登记以保持CIEN既有四季度槽闭合",
        },
    }
    upsert_rows(
        sources,
        "source_id",
        source_updates,
        append_order=["S_CIEN_2026_FORUM"],
    )

    claims = read_csv_rows(calls_dir / "claims.csv", FILES["claims.csv"])
    claim_updates: dict[str, dict[str, str]] = {
        "CL009": {
            "anchor": "p. 3, Demand for Silicon One",
        },
        "CL075": {
            "claim_id": "CL075",
            "source_id": "S_AAOI_2026Q2",
            "speaker": "Thompson Lin",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "ramping",
            "side": "supply",
            "theme_id": "T003",
            "quote": "we saw a strong volume ramp of our 800G products, which more than doubled sequentially",
            "anchor": "CEO quote, paragraph 1",
            "review_status": "reviewed",
            "mapping_track": "canonical",
            "cell_id": "MOD1",
            "route_item_id": "",
            "unmapped_theme": "",
            "unmapped_reason": "",
            "summary": "AAOI在2026Q2业绩稿确认截至6月30日季度800G模块实现强劲放量且环比翻倍以上；未单列出货只数或分产品收入",
        },
        "CL076": {
            "claim_id": "CL076",
            "source_id": "S_CIEN_2026_FORUM",
            "speaker": "Dino DiPerna",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "sampling",
            "side": "both",
            "theme_id": "T017",
            "quote": "we are sampling devices for multiple key customers",
            "anchor": "p. 24, lines 873-874, Vesta 200 CPX",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "CPO商业化与采用阶段",
            "unmapped_reason": "现有树与路线BOM未定义跨光源封装交换系统的CPO光引擎成熟度节点；送样评估不等于首次可用日期确认或规模量产",
            "summary": "Ciena在2026-09-16 Investor Forum确认正就Vesta 200 CPX向超大规模客户与交换机OEM等多家关键客户送样评估；未披露首次样品可用日",
        },
    }
    upsert_rows(
        claims,
        "claim_id",
        claim_updates,
        append_order=["CL075", "CL076"],
    )

    commitments = read_csv_rows(calls_dir / "commitments.csv", FILES["commitments.csv"])
    commitment_updates: dict[str, dict[str, str]] = {
        "CM001": {
            "status": "fulfilled",
            "evidence_source_id": "S_CSCO_2026Q2_A",
            "evidence_claim_id": "CL010",
            "assessment": (
                "FY26 Q2（截至2026-01-24）内按期兑现，2026-02-11由公司FY26 Q2官方prepared remarks"
                "确认已出货第100万颗Silicon One芯片，具体日未知；属CEO公司自述，缺客户侧独立收货确认，"
                "且不与后续10月G300单代送样及系统出货混同"
            ),
        },
        "CM002": {
            "status": "fulfilled",
            "evidence_source_id": "S_AAOI_2026Q2",
            "evidence_claim_id": "CL075",
            "assessment": (
                "事件窗口截至2026-06-30按期兑现，披露日2026-08-06由公司Q2业绩稿确认800G产品强劲放量且环比翻倍以上"
                "（公司自述，未单列800G精确出货只数或分产品收入）；2026-11-05 Q3披露的2027美国扩产延期属独立后续事件，"
                "不推翻Q2放量结果"
            ),
        },
        "CM003": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "截至2026-11-11目标窗口（2026-12-31）尚未结束；2025年报曾写预计2027投产，2026Q1称年内开始爬坡，"
                "2026Q2细化为Q4 2026后段按计划爬坡，2026Q3将部分制造投资现金支付移至2027并重申光学制造扩张按计划推进；"
                "须区分San Jose与Sunnyvale等厂区，尚缺实际启用或首批晶圆声明"
            ),
        },
        "CM004": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "指向OFC2026公布的4款DSP支撑13项相干光方案家族，原文窗口为mid-2027（账本2027-06-30为跟踪坐标而非逐日硬截止）；"
                "截至2026-11-11仍在未来窗口且未见改期或已送样陈述，既有旧800G ZR部署不计入该新家族送样"
            ),
        },
        "CM005": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "与CM004同属OFC2026四DSP/13方案相干光家族，2026-03-16发布预期H2 2027一般可用（GA），"
                "2026Q1管理层表述为同期开始volume production（账本2027-12-31为跟踪截止日）；"
                "量产窗口仍在未来，须与CM004送样阶段及同期H2 2026多轨线放大器计划严格区分"
            ),
        },
        "CM006": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "基于2026-07-23披露的2026Q2光网络与IP网络混合长期订单（同段AI&Cloud订单流入28亿欧元，"
                "但未界定全部为同一长约分母，2027-07-23为12个月跟踪坐标）；2026Q3仅披露AI&Cloud合计收入与新增订单，"
                "尚缺Q2同批次订单转确认收入对账桥"
            ),
        },
        "CM007": {
            "status": "partially_fulfilled",
            "evidence_source_id": "S_CIEN_2026_FORUM",
            "evidence_claim_id": "CL076",
            "assessment": (
                "2026-09-03 FY26 Q3电话会披露获多家核心客户样品订单，截至2026-09-16 Investor Forum官方逐字稿"
                "已确认正就Vesta 200 CPX进入多客户送样评估（涵盖超大规模客户与交换机OEM）；"
                "但日历2026Q2（截至2026-06-30）首次可提供日期仍未知，按期性待证"
            ),
        },
        "CM008": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "Q1所述begin standardization在2026-09-03 Q3电话会明确为initial customer standardization"
                "（客户平台选型与部署规范纳入，非IEEE/OIF组织标准且不混同Vesta相关Open CPX MSA），"
                "2026-09-16论坛仍预计年底推出首版；截至2026-11-11窗口未到期，Q2首单与ECOC演示不等于客户平台标准化完成"
            ),
        },
        "CM009": {
            "status": "pending",
            "evidence_source_id": "",
            "evidence_claim_id": "",
            "assessment": (
                "Q1预计2027年开始爬坡，2026-09-03 Q3细化为2027年内逐步形成有规模收入（scaling to material revenue），"
                "2026-09-16论坛仍列为未来增长来源（2027-12-31为年度跟踪坐标）；截至2026-11-11仍在未来窗口，"
                "既有RLS全系列收入、首单或WaveLogic部署不计入Hyper-Rail专项爬坡"
            ),
        },
    }
    upsert_rows(commitments, "commitment_id", commitment_updates, append_order=[])

    # ------------------------------------------------------------------
    # 2. Task 2: Overseas Event Ledger Additions (Sep-Nov 2026 Verified)
    # ------------------------------------------------------------------
    universe = read_csv_rows(calls_dir / "universe.csv", FILES["universe.csv"])
    universe_ids = {row["company_id"] for row in universe}
    if "TSEM" not in universe_ids or "CSCO" not in universe_ids:
        raise AssertionError("Expected CSCO and TSEM in calls/universe.csv")

    watch_entities = read_csv_rows(calls_dir / "watch_entities.csv", FILES["watch_entities.csv"])
    watch_updates: dict[str, dict[str, str]] = {
        "WATCH_INNOLIGHT": {
            "entity_id": "WATCH_INNOLIGHT",
            "entity_name": "InnoLight",
            "entity_type": "company",
            "aliases": "中际旭创;InnoLight Technology;Innolight",
            "inclusion_reason": "Tower Semiconductor NPO硅光联合公告的具名对手方（对应国内A股300308中际旭创）",
            "monitoring_status": "active",
            "promoted_company_id": "",
            "source_ref": "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/",
            "notes": "仅用于海外事件具名对手方挂接；国内能力主档见points.csv P074/P138，不进入海外四季度电话会覆盖池",
        },
    }
    upsert_rows(
        watch_entities,
        "entity_id",
        watch_updates,
        append_order=["WATCH_INNOLIGHT"],
    )

    disclosures = read_csv_rows(calls_dir / "disclosures.csv", FILES["disclosures.csv"])
    disclosure_updates: dict[str, dict[str, str]] = {
        "D_CSCO_20261012_OCP_G300": {
            "disclosure_id": "D_CSCO_20261012_OCP_G300",
            "publisher_entity_id": "CSCO",
            "legacy_source_id": "",
            "title": "Cisco Advances Scalability and Openness at OCP 2026",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": "https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m10/cisco-advances-scalability-and-openness-at-ocp-2026.html",
            "local_path": "",
            "content_hash": "71bc22daab585004023a0ee13d9613950ec6ddd1d370824d47ee83e8f2c1bfbc",
            "origin_group": "OG_CSCO_20261012_OCP_G300",
            "published_at": "2026-10-12",
            "updated_at": "",
            "discovered_at": "2026-10-13",
            "retrieved_at": "2026-10-13",
            "reviewed_at": "2026-11-11",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "Cisco Silicon One Portfolio Delivers段落中G300送样与首批系统出货句",
            "notes": "Cisco官网OCP 2026新闻稿（对应staging DC_66D313EC13F4）；102.4T G300属单代交换ASIC与系统进展，不混同CM001全系列百万颗里程碑，也不映射到光模块电芯片C5",
        },
        "D_TSEM_20261103_INNOLIGHT_NPO": {
            "disclosure_id": "D_TSEM_20261103_INNOLIGHT_NPO",
            "publisher_entity_id": "TSEM",
            "legacy_source_id": "",
            "title": "Tower Semiconductor and Innolight Advance High-Performance Near-Package Optics for AI Infrastructure",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/",
            "local_path": "",
            "content_hash": "3886b7df9f4c2309e04087bc746c2233a662ef19c51afe711096cc4f83b3a3cd",
            "origin_group": "OG_TSEM_20261103_INNOLIGHT_NPO",
            "published_at": "2026-11-03",
            "updated_at": "",
            "discovered_at": "2026-11-04",
            "retrieved_at": "2026-11-04",
            "reviewed_at": "2026-11-21",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "公告标题",
            "notes": "对应staging DC_430D7977BA22，仅按官方公告标题与URL建档；中际旭创10/29及11/03投关已定调NPO 2027H2才逐步上量，公告正文尚在corpus/daily_review/review_queue.csv待全文精读，不视作已量产",
        },
    }
    upsert_rows(
        disclosures,
        "disclosure_id",
        disclosure_updates,
        append_order=["D_CSCO_20261012_OCP_G300", "D_TSEM_20261103_INNOLIGHT_NPO"],
    )

    event_claims = read_csv_rows(calls_dir / "event_claims.csv", FILES["event_claims.csv"])
    event_claim_updates: dict[str, dict[str, str]] = {
        "ECL038": {
            "event_claim_id": "ECL038",
            "legacy_claim_id": "",
            "disclosure_id": "D_CSCO_20261012_OCP_G300",
            "claimant_entity_id": "CSCO",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Announced earlier this year, the 102.4T Silicon One G300 is now available for customer sampling, and the first G300-powered systems are currently shipping to customers.",
            "anchor": "Cisco Silicon One Portfolio Delivers > G300 paragraph (p10)",
            "summary": "Cisco披露102.4T Silicon One G300已开放客户送样且首批搭载G300的系统正开始向客户出货",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-11",
            "notes": "第一方公司新闻稿陈述（对应CC_B7D08360AB0B）；未披露具体客户名称、出货数量或对应光模块形态",
        },
        "ECL039": {
            "event_claim_id": "ECL039",
            "legacy_claim_id": "",
            "disclosure_id": "D_TSEM_20261103_INNOLIGHT_NPO",
            "claimant_entity_id": "TSEM",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Tower Semiconductor and Innolight Advance High-Performance Near-Package Optics for AI Infrastructure",
            "anchor": "公告标题",
            "summary": "Tower Semiconductor官网公告标题披露与中际旭创（Innolight）共同推进面向AI基础设施的近封装光学（NPO）",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-21",
            "notes": "仅锚定官方公告标题；中际旭创10/29及11/03投关已定调NPO 2027H2才逐步上量，公告正文尚在corpus/daily_review/review_queue.csv待全文精读，不视作已量产",
        },
    }
    upsert_rows(
        event_claims,
        "event_claim_id",
        event_claim_updates,
        append_order=["ECL038", "ECL039"],
    )

    events = read_csv_rows(calls_dir / "events.csv", FILES["events.csv"])
    event_updates: dict[str, dict[str, str]] = {
        "EV035": {
            "event_id": "EV035",
            "program_id": "PRG_CSCO_SILICON_ONE_G300",
            "event_category": "commercial_adoption",
            "lifecycle_stage": "first_shipment",
            "event_status": "asserted",
            "primary_subject_id": "CSCO",
            "counterparty_ids": "",
            "theme_ids": "T009;T018",
            "occurred_start": "2026-10-12",
            "occurred_end": "2026-10-12",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Cisco第一方披露102.4T Silicon One G300开放送样且首批G300系统向客户出货",
            "notes": "披露日2026-10-12，实际首批系统出货不晚于该日但具体日与客户未披露；交换ASIC系统进展不直接折算光模块出货量",
        },
        "EV036": {
            "event_id": "EV036",
            "program_id": "PRG_TSEM_INNOLIGHT_NPO",
            "event_category": "supply_chain_arrangement",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "TSEM",
            "counterparty_ids": "WATCH_INNOLIGHT",
            "theme_ids": "T015;T017",
            "occurred_start": "2026-11-03",
            "occurred_end": "2026-11-03",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Tower Semiconductor与中际旭创（Innolight）发布推进AI近封装光学（NPO）联合公告",
            "notes": "仅按官方公告标题建档；中际旭创10/29及11/03投关已定调NPO 2027H2才逐步上量，公告正文尚在corpus/daily_review/review_queue.csv待全文精读，不视作已量产",
        },
    }
    upsert_rows(
        events,
        "event_id",
        event_updates,
        append_order=["EV035", "EV036"],
    )

    event_evidence = read_csv_rows(calls_dir / "event_evidence.csv", FILES["event_evidence.csv"])
    evidence_updates: dict[str, dict[str, str]] = {
        "EE038": {
            "evidence_id": "EE038",
            "event_id": "EV035",
            "event_claim_id": "ECL038",
            "relationship": "reports",
            "independence_class": "first_party",
            "origin_group": "OG_CSCO_20261012_OCP_G300",
            "notes": "Cisco官网OCP 2026一手新闻稿；单方披露未获下游客户独立确认",
        },
        "EE039": {
            "evidence_id": "EE039",
            "event_id": "EV036",
            "event_claim_id": "ECL039",
            "relationship": "reports",
            "independence_class": "first_party",
            "origin_group": "OG_TSEM_20261103_INNOLIGHT_NPO",
            "notes": "Tower官网一手新闻稿标题级核定；中际旭创10/29及11/03投关已定调NPO 2027H2才逐步上量，公告正文尚在corpus/daily_review/review_queue.csv待全文精读，不视作已量产",
        },
    }
    upsert_rows(
        event_evidence,
        "evidence_id",
        evidence_updates,
        append_order=["EE038", "EE039"],
    )

    # Strict forbidden-word check across all modified/inserted calls rows
    for cid in ("CL009", "CL075", "CL076"):
        row = next(r for r in claims if r["claim_id"] == cid)
        for field in ("summary", "unmapped_theme", "unmapped_reason"):
            assert_no_forbidden_words(f"claims:{cid}.{field}", row[field])
    for row in commitments:
        assert_no_forbidden_words(f"commitments:{row['commitment_id']}.target", row["target"])
        assert_no_forbidden_words(f"commitments:{row['commitment_id']}.assessment", row["assessment"])
    for label, table_updates in (
        ("watch_entities", watch_updates),
        ("disclosures", disclosure_updates),
        ("event_claims", event_claim_updates),
        ("events", event_updates),
        ("event_evidence", evidence_updates),
    ):
        for pk, data in table_updates.items():
            for field, val in data.items():
                if field != "quote":
                    assert_no_forbidden_words(f"{label}:{pk}.{field}", val)

    # Honesty boundary assertion: unverified full-text candidates must NOT enter claims.csv
    claims_blob = json.dumps(claims, ensure_ascii=False)
    for blocked_token in ("DC_501FC1F61B62", "DC_573401DC530B", "DC_3841FCD60F32"):
        if blocked_token in claims_blob:
            raise AssertionError(f"Unverified staging candidate leaked into claims.csv: {blocked_token}")

    # ------------------------------------------------------------------
    # 3. Task 3: Relationship Timeline Additions (TL9001-TL9005)
    # ------------------------------------------------------------------
    timeline_rows = read_csv_rows(rel_timeline_path, TIMELINE_FIELDS)
    timeline_updates: dict[str, dict[str, str]] = {
        "TL9001": {
            "timeline_id": "TL9001",
            "relation_id": "R057",
            "supplier": "罗博特科/ficonTEC",
            "customer": "NVIDIA",
            "supplier_point_id": "P059",
            "customer_point_id": "EXT",
            "period": "2026-11-16",
            "period_type": "event",
            "event_date": "2026-11-16",
            "source_channel": "daily_qa",
            "metric_kind": "order_progress",
            "value_raw": "互动易首次书面确认\"英伟达系ficonTEC的客户之一\"；2025年配合核心客户完成双面晶圆及晶粒测试设备开发验证后取得多笔量产化订单且部分交付确收，但批量订单归属受NDA商业秘密限制未披露",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "E012",
            "daily_ref_id": "QA_300757_20261116_L1464",
            "anchor_url": "corpus/qa/300757/qa.jsonl#indexId=2402040011815366656",
            "conflict": "false",
            "notes": "深交所互动易官方答复(ask_date=2026-11-11,answer_date=2026-11-16,qa:300757:2402040011815366656)；仅确认客户关系存在，严禁将608.09万欧元等匿名量产大单直接归属英伟达",
        },
        "TL9002": {
            "timeline_id": "TL9002",
            "relation_id": "R205",
            "supplier": "Tower Semiconductor",
            "customer": "中际旭创",
            "supplier_point_id": "EXT",
            "customer_point_id": "P074",
            "period": "2026-11-03",
            "period_type": "event",
            "event_date": "2026-11-03",
            "source_channel": "daily_announcement",
            "metric_kind": "partnership_milestone",
            "value_raw": "Tower Semiconductor与中际旭创(Innolight)发布面向AI基础设施的高性能近封装光学(NPO)硅光联合公告；中际旭创11/03投关定调NPO于2027H2逐步上量",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_TSEM_20261103_INNOLIGHT_NPO",
            "anchor_url": "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/",
            "conflict": "false",
            "notes": "joint_rd/NPO硅光生态里程碑(对应DC_430D7977BA22与calls/events.csv#EV036)；仅核定官方标题，中际10/29与11/03投关明确NPO 2027年处NPI爬坡、2027H2才逐步上量，不视作已量产且无定量采购额",
        },
        "TL9003": {
            "timeline_id": "TL9003",
            "relation_id": "R206",
            "supplier": "炬光科技",
            "customer": "核心客户(匿名)",
            "supplier_point_id": "P117",
            "customer_point_id": "ANON",
            "period": "2026-11-05",
            "period_type": "event",
            "event_date": "2026-11-05",
            "source_channel": "daily_announcement",
            "metric_kind": "order_progress",
            "value_raw": "大于36通道光纤定位V型槽部分客户由小批量验证转入批量交付；MPLA微棱镜透镜阵列与核心客户正式签署并开始执行技术许可协议",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "半边",
            "source_edge_ids": "",
            "daily_ref_id": "FILING_688167_20261105_P86",
            "anchor_url": "https://static.cninfo.com.cn/finalpage/2026-11-05/1225658451.PDF#page=86",
            "conflict": "false",
            "notes": "2026-11-05向特定对象发行股票募集说明书申报稿第86页(印刷1-1-85，关联P117/P169)；严格区分大于36通道V型槽硬件批量交付与MPLA技术授权许可费(非硬件销售量)",
        },
        "TL9004": {
            "timeline_id": "TL9004",
            "relation_id": "R058",
            "supplier": "罗博特科/ficonTEC",
            "customer": "博通(Broadcom)",
            "supplier_point_id": "P059",
            "customer_point_id": "P020",
            "period": "2025-09-15",
            "period_type": "event",
            "event_date": "2025-09-15",
            "source_channel": "daily_qa",
            "metric_kind": "order_progress",
            "value_raw": "互动易重申ficonTEC帮助博通打造全球首批交换机侧CPO产品(重组注册稿p.440披露已交付至少14台耦合设备)；同日对下一代Tomahawk 6(TH6)是否续用及持续独供以商业秘密拒答",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "E011",
            "daily_ref_id": "QA_300757_20250915_L563",
            "anchor_url": "corpus/qa/300757/qa.jsonl#indexId=0001B86FB49A2CCC4C47B2ADDDBABB030606;https://static.cninfo.com.cn/finalpage/2025-04-18/1223130596.PDF#page=440",
            "conflict": "false",
            "notes": "深交所互动易2025-09-15同日答复(L563确认早期首批交换机侧CPO耦合独供，L561对TH6拒答)；严禁将早期首批14台独供外推为2026年或TH6永续独供",
        },
        "TL9005": {
            "timeline_id": "TL9005",
            "relation_id": "R207",
            "supplier": "博众精工",
            "customer": "NPO/CPO耦合客户(匿名)",
            "supplier_point_id": "P206",
            "customer_point_id": "ANON",
            "period": "2026-08-25",
            "period_type": "event",
            "event_date": "2026-08-25",
            "source_channel": "daily_announcement",
            "metric_kind": "order_progress",
            "value_raw": "2026半年报披露60%控股子公司中南鸿思已获NPO/CPO光引擎自动耦合设备订单并完成设计、即将进入交付阶段(与子公司苏州博众半导体共晶贴片业务分列)",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "半边",
            "source_edge_ids": "",
            "daily_ref_id": "FILING_688097_2026H1_P54",
            "anchor_url": "https://static.cninfo.com.cn/finalpage/2026-08-25/1225498439.PDF#page=54",
            "conflict": "false",
            "notes": "博众精工2026年半年度报告p.54及p.211合并附注(2.86亿元收购中南鸿思60%股权于2026-02-28交割)；中南鸿思(自动耦合获单待交付)与苏州博众半导体(11/17互动易确认共晶贴片排期饱满并警示订单不直接等同于收入)严格分主体管理",
        },
    }
    upsert_rows(
        timeline_rows,
        "timeline_id",
        timeline_updates,
        append_order=["TL9001", "TL9002", "TL9003", "TL9004", "TL9005"],
    )

    # Check zero collision between TL9001-TL9005 and 74 negative cuts
    with cuts_path.open("r", encoding="utf-8-sig", newline="") as fh:
        cut_rows = list(csv.DictReader(fh))
    neg_pairs: set[tuple[str, str]] = set()
    for c in cut_rows:
        comp = (c.get("company") or "").strip()
        cp = (c.get("counterparty") or "").strip()
        cpn = (c.get("counterparty_normalized") or cp).strip()
        isup = (c.get("implied_supplier") or "").strip()
        icus = (c.get("implied_customer") or "").strip()
        for a, b in ((comp, cp), (comp, cpn), (isup, icus)):
            if a and b:
                neg_pairs.add((a, b))
                neg_pairs.add((b, a))
    for tid in ("TL9001", "TL9002", "TL9003", "TL9004", "TL9005"):
        trow = timeline_updates[tid]
        if (trow["supplier"], trow["customer"]) in neg_pairs:
            raise AssertionError(f"{tid} collides with edge_negative_cuts.csv: {(trow['supplier'], trow['customer'])}")

    # ------------------------------------------------------------------
    # 4. Write Whitelisted CSV Outputs (Preserving Untouched Raw Lines)
    # ------------------------------------------------------------------
    write_csv_preserving_untouched(
        calls_dir / "sources.csv", FILES["sources.csv"], "source_id", sources, set(source_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "claims.csv", FILES["claims.csv"], "claim_id", claims, set(claim_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "commitments.csv", FILES["commitments.csv"], "commitment_id", commitments, set(commitment_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "watch_entities.csv", FILES["watch_entities.csv"], "entity_id", watch_entities, set(watch_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "disclosures.csv", FILES["disclosures.csv"], "disclosure_id", disclosures, set(disclosure_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "event_claims.csv", FILES["event_claims.csv"], "event_claim_id", event_claims, set(event_claim_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "events.csv", FILES["events.csv"], "event_id", events, set(event_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "event_evidence.csv", FILES["event_evidence.csv"], "evidence_id", event_evidence, set(evidence_updates), "\n"
    )
    write_csv_preserving_untouched(
        rel_timeline_path, TIMELINE_FIELDS, "timeline_id", timeline_rows, set(timeline_updates), "\r\n"
    )

    # ------------------------------------------------------------------
    # 5. Deterministic Verification Gates
    # ------------------------------------------------------------------
    sl_hash_after = sha256_bytes(solution_links_path)
    if sl_hash_after != sl_hash_before:
        raise AssertionError("calls/solution_links.csv byte hash changed (strictly frozen)!")
    sl_rows = read_csv_rows(solution_links_path, FILES["solution_links.csv"])
    if tuple(sl_rows) != FROZEN_SOLUTION_LINKS:
        raise AssertionError("calls/solution_links.csv content does not match FROZEN_SOLUTION_LINKS!")

    calls_messages = validate(REPO_ROOT)
    event_projection = derive_event_projection(load_event_facts(REPO_ROOT))

    with (REPO_ROOT / "edges.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        active_edges = list(csv.DictReader(fh))
    edge_ids = {e["edge_id"] for e in active_edges}
    del scan.ERR[:]
    scan._check_relationship_tables(timeline_rows, edge_ids, cut_rows=cut_rows, active_edges=active_edges)
    rel_errors = list(scan.ERR)
    del scan.ERR[:]
    if rel_errors:
        raise AssertionError(f"scan._check_relationship_tables failed: {rel_errors}")

    target_files = [
        "calls/sources.csv",
        "calls/claims.csv",
        "calls/commitments.csv",
        "calls/watch_entities.csv",
        "calls/disclosures.csv",
        "calls/event_claims.csv",
        "calls/events.csv",
        "calls/event_evidence.csv",
        "corpus/relationships/relationship_timeline.csv",
    ]
    file_hashes = {rel: sha256_bytes(REPO_ROOT / rel) for rel in target_files}

    summary = {
        "shard": "step3-overseas-and-relationship-timeline",
        "as_of_date": "2026-11-21",
        "commitments_adjudicated": {
            "fulfilled": {
                "CM001": {
                    "company_id": "CSCO",
                    "evidence_source_id": "S_CSCO_2026Q2_A",
                    "evidence_claim_id": "CL010",
                    "anchor_fix": "CL009 -> p. 3, Demand for Silicon One",
                },
                "CM002": {
                    "company_id": "AAOI",
                    "evidence_source_id": "S_AAOI_2026Q2",
                    "evidence_claim_id": "CL075",
                    "source_url_fix": "S_AAOI_Q1_RESULT_A -> https://investors.ao-inc.com/2026-05-07-Applied-Optoelectronics-Reports-First-Quarter-2026-Results",
                },
            },
            "partially_fulfilled": {
                "CM007": {
                    "company_id": "CIEN",
                    "evidence_source_id": "S_CIEN_2026_FORUM",
                    "evidence_claim_id": "CL076",
                },
            },
            "pending_refined": ["CM003", "CM004", "CM005", "CM006", "CM008", "CM009"],
        },
        "calls_ledger_changes": {
            "sources_updated": ["S_AAOI_Q1_RESULT_A"],
            "sources_inserted": ["S_CIEN_2026_FORUM"],
            "claims_updated": ["CL009"],
            "claims_inserted": ["CL075", "CL076"],
            "watch_entities_inserted": ["WATCH_INNOLIGHT"],
            "existing_universe_reused": ["CSCO", "TSEM"],
            "disclosures_inserted": ["D_CSCO_20261012_OCP_G300", "D_TSEM_20261103_INNOLIGHT_NPO"],
            "event_claims_inserted": ["ECL038", "ECL039"],
            "events_inserted": ["EV035", "EV036"],
            "event_evidence_inserted": ["EE038", "EE039"],
            "deferred_to_review_queue_not_in_claims": [
                "DC_501FC1F61B62 (Marvell x Lumentum boilerplate)",
                "DC_573401DC530B (Lumentum FY27Q1 unverified full text)",
                "DC_3841FCD60F32 (AXT Q3 / Tongmei financing unverified full text)",
            ],
            "row_counts": {
                "sources.csv": len(sources),
                "claims.csv": len(claims),
                "commitments.csv": len(commitments),
                "watch_entities.csv": len(watch_entities),
                "disclosures.csv": len(disclosures),
                "event_claims.csv": len(event_claims),
                "events.csv": len(events),
                "event_evidence.csv": len(event_evidence),
                "radar_events": len(event_projection["radar_events"]),
            },
        },
        "relationship_timeline_changes": {
            "inserted_timeline_ids": ["TL9001", "TL9002", "TL9003", "TL9004", "TL9005"],
            "reused_relation_ids": {"TL9001": "R057", "TL9004": "R058"},
            "new_relation_ids": {"TL9002": "R205", "TL9003": "R206", "TL9005": "R207"},
            "total_rows": len(timeline_rows),
            "unique_relations": len({r["relation_id"] for r in timeline_rows}),
            "negative_cuts_collision_count": 0,
        },
        "verification": {
            "calls_check_messages": calls_messages,
            "relationship_table_errors": rel_errors,
            "solution_links_frozen_sha256": sl_hash_after,
            "forbidden_words_hits": 0,
            "target_file_sha256": file_hashes,
        },
    }

    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for msg in calls_messages:
        print(f"OK: {msg}")
    print(f"OK: relationship_timeline validated ({len(timeline_rows)} rows, 0 negative-cut collisions)")
    print(f"OK: wrote {summary_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
