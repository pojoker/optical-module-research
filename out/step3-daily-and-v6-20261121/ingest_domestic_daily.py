#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 3 工人 1 (carbon-daily-domestic): 国内高价值 Daily 并库与内容台账增量.

严格写路径白名单:
  - corpus/ir/**
  - corpus/qa/**
  - points.csv
  - corpus/content_ledger/content_ledger.csv
  - out/step3-daily-and-v6-20261121/ingest_domestic_daily.py
  - out/step3-daily-and-v6-20261121/shard-domestic-summary.json

运行方式 (幂等, 二次重跑字节级零漂移):
  PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 \
      out/step3-daily-and-v6-20261121/ingest_domestic_daily.py
"""

from __future__ import annotations

import csv
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("/Users/jowang/Downloads/optical-module-research")
SRC_DOMESTIC = Path("/Users/jowang/Downloads/workflow-rehearsal-daily-state/domestic")
SRC_IR = SRC_DOMESTIC / "ir"
SRC_QA = SRC_DOMESTIC / "qa"
SRC_YNG_2025_PDF = Path(
    "/Users/jowang/Downloads/workflow-rehearsal/tmp/yng/002428/"
    "002428__em_云南锗业_em__2025_2025年年度报告.pdf"
)

DST_IR = ROOT / "corpus" / "ir"
DST_QA = ROOT / "corpus" / "qa"
POINTS_CSV = ROOT / "points.csv"
CONTENT_LEDGER_CSV = ROOT / "corpus" / "content_ledger" / "content_ledger.csv"
SUMMARY_JSON = ROOT / "out" / "step3-daily-and-v6-20261121" / "shard-domestic-summary.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402
import yaml  # noqa: E402

REQ_QA_KEYS = ("code", "question", "answer", "answer_date", "index_id", "empty", "fetch_date")
BATCH_ID = "step3_daily_2026q4"
SESSION_DATE = "2026-11-21"

KEY_FOCUS_QA_CODES = [
    "300308",
    "300757",
    "300394",
    "000988",
    "300502",
    "603083",
    "688097",
    "688167",
    "603228",
    "688048",
    "688498",
    "002281",
    "301338",
]

CONTENT_LEDGER_COLUMNS = [
    "cid",
    "company",
    "stock_code_or_ticker",
    "source_doc",
    "doc_year",
    "fact_type",
    "stance",
    "tense",
    "cell_ids",
    "atomic_fact",
    "verbatim_quote",
    "section_ref",
    "local_source_path",
    "anchor_url",
    "quote_verification_status",
    "batch",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_nospace(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def write_bytes_if_changed(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


# ---------------------------------------------------------------------------
# 1. Sync 2026-09~11 Domestic IR PDFs + .pdf.txt sidecars
# ---------------------------------------------------------------------------
def sync_domestic_ir() -> dict[str, Any]:
    if not SRC_IR.is_dir():
        raise FileNotFoundError(f"Missing read-only IR source directory: {SRC_IR}")

    synced_codes: list[str] = []
    files_written = 0
    files_unchanged = 0
    pdf_count = 0
    txt_count = 0
    key_ir_files: list[str] = []

    for code_dir in sorted(p for p in SRC_IR.iterdir() if p.is_dir()):
        code = code_dir.name
        synced_codes.append(code)
        dst_code_dir = DST_IR / code
        for src_file in sorted(p for p in code_dir.iterdir() if p.is_file()):
            if not (src_file.name.endswith(".pdf") or src_file.name.endswith(".pdf.txt")):
                continue
            raw = src_file.read_bytes()
            if src_file.name.endswith(".pdf"):
                if not raw.startswith(b"%PDF-"):
                    raise ValueError(f"Invalid PDF header in source IR file: {src_file}")
                pdf_count += 1
            else:
                txt_count += 1
            dst_file = dst_code_dir / src_file.name
            if write_bytes_if_changed(dst_file, raw):
                files_written += 1
            else:
                files_unchanged += 1
            if code in ("300308", "300757", "300394", "300502", "301338", "002384", "301205", "001267"):
                key_ir_files.append(str(dst_file.relative_to(ROOT)))

    # Assert required core IR snapshots are in place
    must_exist = [
        "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf",
        "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf.txt",
        "corpus/ir/300308/300308_2026-11-03_投资者关系活动记录表20261103.pdf",
        "corpus/ir/300308/300308_2026-11-03_投资者关系活动记录表20261103.pdf.txt",
        "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf",
        "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf.txt",
        "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf",
        "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf.txt",
        "corpus/ir/300502/300502_2026-09-12_300502新易盛投资者关系管理信息20260911.pdf",
        "corpus/ir/300502/300502_2026-09-12_300502新易盛投资者关系管理信息20260911.pdf.txt",
        "corpus/ir/300502/300502_2026-10-29_300502新易盛投资者关系管理信息20261029.pdf",
        "corpus/ir/300502/300502_2026-10-29_300502新易盛投资者关系管理信息20261029.pdf.txt",
    ]
    for rel in must_exist:
        if not (ROOT / rel).is_file():
            raise FileNotFoundError(f"Required synced IR file missing: {rel}")

    return {
        "synced_code_count": len(synced_codes),
        "pdf_count": pdf_count,
        "pdf_txt_count": txt_count,
        "total_synced_files": pdf_count + txt_count,
        "files_written_this_run": files_written,
        "files_unchanged_this_run": files_unchanged,
        "key_ir_files": key_ir_files,
        "note_688808_002428": "workflow-rehearsal-daily-state/domestic/{ir,qa} 暂未含 688808(联讯仪器) 与 002428(云南锗业) 日更子目录；两家一手年报/半年报/招股书已在 points.csv 完成锚定。",
    }


# ---------------------------------------------------------------------------
# 2. Sync & Deduplicate Domestic QA JSONL snapshots
# ---------------------------------------------------------------------------
def load_protected_qa_index_ids() -> set[str]:
    protected: set[str] = set()
    with POINTS_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            m = re.search(r"#indexId=([A-Za-z0-9]+)", row.get("锚点URL") or "")
            if m:
                protected.add(m.group(1))
    return protected


def dedupe_qa_records(records: list[dict[str, Any]], protected_ids: set[str]) -> list[dict[str, Any]]:
    """Deterministic deduplication over QA JSONL records:
    1) Drop undated (answer_date == '') scrape entries whenever an identical
       (norm_ws(question), norm_ws(answer)) entry with non-empty answer_date exists
       (eliminates SSE e-interaction undated pre-fetches such as 603083 L284 vs L292
       and 688097 L214 vs L221).
    2) Deduplicate identical (norm_ws(question), norm_ws(answer), answer_date) and
       identical non-empty index_id, preferring protected index_ids referenced by
       points.csv, then non-empty numeric/alphanumeric index_id, then latest fetch_date,
       while preserving original file order of the selected canonical records.
    """
    has_dated: set[tuple[str, str]] = set()
    for r in records:
        qk = (norm_ws(str(r.get("question") or "")), norm_ws(str(r.get("answer") or "")))
        if str(r.get("answer_date") or "").strip():
            has_dated.add(qk)

    filtered: list[tuple[int, dict[str, Any]]] = []
    for pos, r in enumerate(records):
        qk = (norm_ws(str(r.get("question") or "")), norm_ws(str(r.get("answer") or "")))
        ad = str(r.get("answer_date") or "").strip()
        if not ad and qk in has_dated:
            continue
        filtered.append((pos, r))

    groups: dict[tuple[str, str, str], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for pos, r in filtered:
        key = (
            norm_ws(str(r.get("question") or "")),
            norm_ws(str(r.get("answer") or "")),
            str(r.get("answer_date") or "").strip(),
        )
        groups[key].append((pos, r))

    chosen: list[tuple[int, dict[str, Any]]] = []
    seen_index_ids: set[str] = set()
    for items in groups.values():
        def rank(item: tuple[int, dict[str, Any]]) -> tuple[int, int, int, str, int]:
            pos, rec = item
            iid = str(rec.get("index_id") or "").strip()
            return (
                1 if iid in protected_ids else 0,
                1 if iid else 0,
                1 if iid.isdigit() else 0,
                str(rec.get("fetch_date") or "").strip(),
                -pos,
            )

        best_pos, best_rec = max(items, key=rank)
        iid = str(best_rec.get("index_id") or "").strip()
        if iid and iid in seen_index_ids:
            continue
        if iid:
            seen_index_ids.add(iid)
        chosen.append((best_pos, best_rec))

    chosen.sort(key=lambda x: x[0])
    return [rec for _, rec in chosen]


def sync_domestic_qa() -> dict[str, Any]:
    if not SRC_QA.is_dir():
        raise FileNotFoundError(f"Missing read-only QA source directory: {SRC_QA}")

    protected_ids = load_protected_qa_index_ids()
    code_stats: dict[str, dict[str, int]] = {}
    total_src_lines = 0
    total_dedup_lines = 0
    files_written = 0
    files_unchanged = 0

    for code_dir in sorted(p for p in SRC_QA.iterdir() if p.is_dir()):
        code = code_dir.name
        src_jsonl = code_dir / "qa.jsonl"
        if not src_jsonl.is_file():
            continue
        dst_jsonl = DST_QA / code / "qa.jsonl"

        with src_jsonl.open("r", encoding="utf-8") as fh:
            src_records = [json.loads(line) for line in fh if line.strip()]
        if dst_jsonl.is_file():
            with dst_jsonl.open("r", encoding="utf-8") as fh:
                dst_existing = [json.loads(line) for line in fh if line.strip()]
        else:
            dst_existing = []

        # Merge: source snapshot in canonical order + any legacy destination-only Q&A
        src_qa_pairs = {
            (norm_ws(str(r.get("question") or "")), norm_ws(str(r.get("answer") or "")))
            for r in src_records
        }
        legacy_only = [
            r
            for r in dst_existing
            if (norm_ws(str(r.get("question") or "")), norm_ws(str(r.get("answer") or ""))) not in src_qa_pairs
        ]
        merged_input = src_records + legacy_only
        deduped = dedupe_qa_records(merged_input, protected_ids)

        for idx, rec in enumerate(deduped, start=1):
            for req_key in REQ_QA_KEYS:
                if req_key not in rec:
                    raise ValueError(f"QA {code} record #{idx} missing required key {req_key}")

        payload = ("\n".join(json.dumps(rec, ensure_ascii=False) for rec in deduped) + "\n").encode("utf-8")
        if write_bytes_if_changed(dst_jsonl, payload):
            files_written += 1
        else:
            files_unchanged += 1

        total_src_lines += len(src_records)
        total_dedup_lines += len(deduped)
        code_stats[code] = {
            "source_lines": len(src_records),
            "deduped_lines": len(deduped),
            "duplicates_removed": len(src_records) - len(deduped),
            "legacy_only_preserved": len(legacy_only),
        }

    # Verify specific audit dedup assertions on 603083 and 688097
    with (DST_QA / "603083" / "qa.jsonl").open("r", encoding="utf-8") as fh:
        qa_603083 = [json.loads(l) for l in fh if l.strip()]
    vn_matches = [r for r in qa_603083 if "越南生产基地相关产线已通过客户审核认证" in r.get("answer", "")]
    assert len(vn_matches) == 1 and vn_matches[0]["answer_date"] == "2026-11-10", (
        f"Expected exactly 1 deduplicated dated Vietnam entry in 603083, got {len(vn_matches)}"
    )

    with (DST_QA / "688097" / "qa.jsonl").open("r", encoding="utf-8") as fh:
        qa_688097 = [json.loads(l) for l in fh if l.strip()]
    bz_matches = [r for r in qa_688097 if "订单并不直接等同于收入" in r.get("answer", "")]
    assert len(bz_matches) == 1 and bz_matches[0]["answer_date"] == "2026-11-17", (
        f"Expected exactly 1 deduplicated dated Suzhou Bozhon entry in 688097, got {len(bz_matches)}"
    )

    focus_stats = {c: code_stats[c] for c in KEY_FOCUS_QA_CODES if c in code_stats}
    return {
        "synced_qa_code_count": len(code_stats),
        "total_corpus_qa_dirs": len([p for p in DST_QA.iterdir() if p.is_dir() and (p / "qa.jsonl").is_file()]),
        "total_source_lines": total_src_lines,
        "total_deduped_lines": total_dedup_lines,
        "total_duplicates_removed": total_src_lines - total_dedup_lines,
        "files_written_this_run": files_written,
        "files_unchanged_this_run": files_unchanged,
        "focus_code_dedup_stats": focus_stats,
    }


# ---------------------------------------------------------------------------
# 3. Verify 002428 云南锗业 2025 Annual Report Verbatim Quote & Update points.csv
# ---------------------------------------------------------------------------
def verify_yng_2025_annual_quote() -> dict[str, Any]:
    if not SRC_YNG_2025_PDF.is_file():
        raise FileNotFoundError(f"Missing 002428 2025 annual report PDF: {SRC_YNG_2025_PDF}")
    res = subprocess.run(["pdftotext", "-layout", str(SRC_YNG_2025_PDF), "-"], capture_output=True, text=True, check=True)
    norm_txt = norm_nospace(res.stdout)
    quotes = {
        "capacity_quote": "砷化镓晶片产能为80万片/年（2—6英寸），磷化铟晶片产能为15万片/年（2—4英寸）。",
        "output_quote": "生产化合物半导体材料：砷化镓晶片7.63万片（1-6寸合计），磷化铟晶片10.01万片（2-4寸合计）。",
        "sales_growth_quote": "使得砷化镓产品（折合4寸）销量较上年上升33.18%，磷化铟产品（折合4寸）销量较上年上升73.77%所致。",
    }
    for k, q in quotes.items():
        if norm_nospace(q) not in norm_txt:
            raise AssertionError(f"002428 2025 annual report verbatim check failed for {k}: {q}")
    return quotes


class RawPreservingCsv:
    """Preserves UTF-8 BOM, LF line endings, and exact raw bytes of untouched rows."""

    def __init__(self, path: Path) -> None:
        self.path = path
        raw = path.read_bytes()
        self.orig_bytes = raw
        self.has_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw[3:].decode("utf-8") if self.has_bom else raw.decode("utf-8")
        if "\r" in text:
            raise ValueError(f"{path} contains unexpected CR characters")
        self.trailing_nl = text.endswith("\n")
        lines = text.split("\n")
        if self.trailing_nl:
            lines = lines[:-1]
        recs: list[str] = []
        buf: str | None = None
        for ln in lines:
            buf = ln if buf is None else buf + "\n" + ln
            if buf.count('"') % 2 == 0:
                recs.append(buf)
                buf = None
        if buf is not None:
            raise ValueError(f"{path} has unbalanced CSV quotes")
        self.header_raw = recs[0]
        self.header = next(csv.reader(io.StringIO(recs[0], newline="")))
        self.rows: list[dict[str, Any]] = []
        for idx, rec_raw in enumerate(recs[1:], start=2):
            vals = next(csv.reader(io.StringIO(rec_raw, newline="")))
            d = {h: (vals[i] if i < len(vals) else "") for i, h in enumerate(self.header)}
            self.rows.append({"line_no": idx, "raw": rec_raw, "d": d, "dirty": False})

    def by_id(self, pid: str) -> dict[str, Any]:
        matches = [r for r in self.rows if r["d"]["point_id"] == pid]
        if len(matches) != 1:
            raise KeyError(f"Expected 1 row for {pid} in {self.path}, found {len(matches)}")
        return matches[0]

    def update_fields(self, pid: str, updates: dict[str, str]) -> dict[str, Any]:
        row = self.by_id(pid)
        for col, new_val in updates.items():
            if col not in self.header:
                raise KeyError(f"Unknown column {col} in {self.path}")
            if "\n" in new_val or "\r" in new_val:
                raise ValueError(f"Embedded newline not allowed in {pid}.{col}")
            if row["d"][col] != new_val:
                row["d"][col] = new_val
                row["dirty"] = True
        return row

    def upsert_row(self, pid: str, full_row: dict[str, str]) -> dict[str, Any]:
        matches = [r for r in self.rows if r["d"]["point_id"] == pid]
        if len(matches) == 1:
            return self.update_fields(pid, full_row)
        if len(matches) > 1:
            raise KeyError(f"Duplicate rows for {pid} in {self.path}")
        d: dict[str, str] = {}
        for col in self.header:
            val = full_row.get(col, "")
            if "\n" in val or "\r" in val:
                raise ValueError(f"Embedded newline not allowed in {pid}.{col}")
            d[col] = val
        d["point_id"] = pid
        row_obj: dict[str, Any] = {
            "line_no": len(self.rows) + 2,
            "raw": self._serialize_row(self.header, d),
            "d": d,
            "dirty": True,
        }
        self.rows.append(row_obj)
        return row_obj

    @staticmethod
    def _serialize_row(header: list[str], d: dict[str, str]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([d.get(h, "") for h in header])
        return buf.getvalue()

    def save_if_changed(self) -> tuple[bool, bytes]:
        parts = [self.header_raw] + [
            self._serialize_row(self.header, r["d"]) if r["dirty"] else r["raw"]
            for r in self.rows
        ]
        text = "\n".join(parts) + ("\n" if self.trailing_nl else "")
        data = (b"\xef\xbb\xbf" if self.has_bom else b"") + text.encode("utf-8")
        if data != self.orig_bytes:
            self.path.write_bytes(data)
            return True, data
        return False, data


def update_points_csv(yng_quotes: dict[str, Any]) -> dict[str, Any]:
    ledger = RawPreservingCsv(POINTS_CSV)

    # Guardrail: P031 must remain completely untouched; P209 quote & anchor URL must remain untouched;
    # P257 is 珠海鼎泰芯源晶体有限公司 while P202 is 云南鑫耀半导体材料有限公司.
    p031_before = dict(ledger.by_id("P031")["d"])
    p209_before = dict(ledger.by_id("P209")["d"])
    p257_before = dict(ledger.by_id("P257")["d"])
    p202_before = dict(ledger.by_id("P202")["d"])
    assert p202_before["公司"] == "云南鑫耀半导体材料有限公司", f"Unexpected P202 company: {p202_before['公司']}"
    assert p257_before["公司"] == "珠海鼎泰芯源晶体有限公司", f"Unexpected P257 company: {p257_before['公司']}"

    # Deterministic target field specifications (idempotent across any number of re-runs)
    robtk_note = (
        "2026-10-29投关及11-02至11-16互动易核实：现款INS2(晶圆测试)与INS3(光引擎测试)已向核心客户批量交付量产设备"
        "(INS3获多批次订单，辟谣INS2取消传闻)，新一代INS2与集成热管理的INS4(全自动系统级测试)尚处设计开发或配合客户NPI阶段；"
        '11-16互动易首次书面确认"英伟达系ficonTEC的客户之一"，但批量订单归属及博通TH6是否续用/独供仍以商业秘密拒答；'
        "瑞士客户约7,867万元整线已于2026Q1交付确收，2026半年报p.12明确归属OCS(光电路交换机)设备产线而非CPO"
    )
    tf_note = (
        "2026-10-29投关(编号2026-013问答2/4/5)核实：为CPO架构配套的FAU、ELS等产品已实现稳定量产交付；"
        "NPO配套产品仍处于配合多个客户前期样品开发、送样和验证阶段，预计2027年逐步实现规模量产(CPO与NPO进度严格分账)"
    )
    zjxc_note = (
        "2026-10-29及11-03投关核实：NPO 2027年仍处新产品导入及制造/上游物料良率爬坡期、预计2027H2开始逐步上量、"
        "2028年大规模释放(否证2026起量传言)；9月底泰国强降雨影响物流致部分成品推后至10月初发货，"
        "约30亿美元存货中较大部分系为后续订单提前准备的原材料备料(不直接等价于抢份额)，并严格区分确定性PO与需求指引guidance；"
        "仍未量化1.6T等分速率收入占比"
    )
    jg_note = (
        "2026-11-05向特定对象发行股票募集说明书申报稿p.86核实：大于36通道光纤定位V型槽产品在部分客户由验证转入批量交付；"
        "MPLA微棱镜透镜阵列与核心客户签署技术许可协议并开始执行(严格区隔技术许可授权与硬件产品销量)"
    )

    target_updates: dict[str, dict[str, str]] = {
        # 1) P061 联讯仪器: 上市标签 未上市私企 -> A股 (688808, 2026-04-24 上市) + v6 & 2026H1 note
        "P061": {
            "上市标签": "A股",
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(1.6T光模块全部核心测试仪器即65GHz采样示波器/120GBaud时钟恢复单元/1.6Tbps误码分析仪及"
                "1.6Tbps光模块测试仪量产供货,2026半年报https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF#page=17,"
                "2026-01-07更新申报稿第1-1-23页已载同口径;[v6扩容同步]公司已于2026-04-24登陆科创板688808,"
                "v6已纳入corpus/_frozen.csv并将上市标签由未上市私企更新为A股;"
                '历史:原引语"电子测量仪器和半导体测试设备的研发、制造、销售及服务",招股书,检索2026-07-24,edge_backed)'
            ),
            "判定会话日期": SESSION_DATE,
        },
        # 2) P059 / P172 / P173 罗博特科/ficonTEC
        "P059": {
            "锚点URL": (
                "有锚；竞品描述（发行人披露）；BOM词表 E011/E012 标注CPO耦合设备；C35内容台账补充："
                "正基于硅光/CPO光模块技术需求研发激光辅助键合、倒装热压等先进封装工艺（发行人自述，设备-工序能力条目）；"
                "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf；"
                "2026半年报 https://static.cninfo.com.cn/finalpage/2026-08-26/1225507370.PDF#page=12"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"edge_backed({robtk_note})",
            "判定会话日期": SESSION_DATE,
        },
        "P172": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-03-31/1225059372.PDF；"
                "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf；"
                "2026半年报 https://static.cninfo.com.cn/finalpage/2026-08-26/1225507370.PDF#page=12"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(子代理起草+引语机械验证;ficonTEC耦合封装设备，光互连应用+Intel/Cisco/NVIDIA等光通信客户自述，"
                f"过EQ加严；{robtk_note})"
            ),
            "判定会话日期": SESSION_DATE,
        },
        "P173": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-03-31/1225059372.PDF；"
                "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf；"
                "2026半年报 https://static.cninfo.com.cn/finalpage/2026-08-26/1225507370.PDF#page=12"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"判定闸-生产中(子代理起草+引语机械验证;硅光模组/CPO模组测试设备为主营产品，光场景明确；{robtk_note})",
            "判定会话日期": SESSION_DATE,
        },
        # 3) P271 / P155 天孚通信
        "P271": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-08-19/1225483926.PDF；"
                "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(投关表2026-08-19:CPO配套产品量产交付阶段+良率满足规模量产;"
                "同表另述无源产线高稼动率下半年续扩/泰国产能稳步提产/存货+103%原材料备货;"
                f"D12已有P024(2020年OSA口径),本点为CPO时代新证据；{tf_note})"
            ),
            "判定会话日期": SESSION_DATE,
        },
        "P155": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-04-08/1225082705.PDF；"
                "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"判定闸-生产中(子代理起草+引语机械验证;FAU光纤阵列设计与制造平台+规模量产能力自述；{tf_note})",
            "判定会话日期": SESSION_DATE,
        },
        # 4) P074 / P138 中际旭创
        "P074": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-03-31/1225056459.PDF；"
                "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf；"
                "corpus/ir/300308/300308_2026-11-03_投资者关系活动记录表20261103.pdf"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"判定闸-生产中({zjxc_note})",
            "判定会话日期": SESSION_DATE,
        },
        "P138": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-03-31/1225056459.PDF；"
                "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf；"
                "corpus/ir/300308/300308_2026-11-03_投资者关系活动记录表20261103.pdf"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"判定闸-生产中(子代理起草+引语机械验证;主营自述明确电信前传/中传/回传模块供货；{zjxc_note})",
            "判定会话日期": SESSION_DATE,
        },
        # 5) P073 新易盛 & P077 剑桥科技 MOD1
        "P073": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-04-24/1225172598.PDF；"
                "corpus/ir/300502/300502_2026-09-12_300502新易盛投资者关系管理信息20260911.pdf；"
                "corpus/ir/300502/300502_2026-10-29_300502新易盛投资者关系管理信息20261029.pdf"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(2026-09-11/10-29投关及11-10至11-12互动易核实：9月底部分产品发货受泰国洪灾物流影响未能在9月确收、"
                "截至11月中旬已在10月确认收入且园区无货物损坏；Q3产量保持环比增长，成都与泰国同步扩产，"
                "1.6T产品Q4放量趋势更明显；NPO预计2027年实现批量出货、2028年规模化上量)"
            ),
            "判定会话日期": SESSION_DATE,
        },
        "P077": {
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(2026-11-10上证e互动核实：越南生产基地相关产线已通过客户审核认证并实现产能在海外落地，"
                "嘉善二厂二期高速光模块车间启用、墨西哥光模块洁净厂预计2027年初施工完成投产；"
                "截至2026年9月初设计产能约100万支/月且产能利用率持续保持高位；"
                "1.6T光模块已在三个客户测试，具体出货与量产节奏以公告为准)"
            ),
            "判定会话日期": SESSION_DATE,
        },
        # 6) P117 / P169 炬光科技
        "P117": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-04-29/1225227562.PDF；"
                "2026-11-05定增募集说明书申报稿 https://static.cninfo.com.cn/finalpage/2026-11-05/1225658451.PDF#page=86"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": f"判定闸-生产中(产品表列示;公司已在册P053@D7,本点为D9新能力；{jg_note})",
            "判定会话日期": SESSION_DATE,
        },
        "P169": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-04-29/1225227562.PDF；"
                "2026-11-05定增募集说明书申报稿 https://static.cninfo.com.cn/finalpage/2026-11-05/1225658451.PDF#page=86"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(子代理起草+引语机械验证;光学元器件典型产品表：V型槽阵列/光纤耦合准直微透镜/微棱镜透镜阵列，"
                f"自述应用于光通信模块、CPO、WSS/OCS、FA；{jg_note})"
            ),
            "判定会话日期": SESSION_DATE,
        },
        # 7) P206 博众精工
        "P206": {
            "锚点URL": (
                "https://static.cninfo.com.cn/finalpage/2026-04-11/1225096862.PDF；"
                "2026半年报 https://static.cninfo.com.cn/finalpage/2026-08-25/1225498439.PDF#page=54"
            ),
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(共晶贴片机400G/800G批量应用+批量订单+出口,2024/2025两期连续自述;"
                "注记:客户匿名(全球领军企业/国内头部),无专项收入;在研硅光微米级共晶机;EQ4耦合机为2026收购中南鸿思布局未来时,驳回；"
                "2026半年报p.54/p.211及2026-09-03/10-16/11-17上证e互动核实：控股收购中南鸿思60%股权已于2026-02-28交割(对价2.86亿元)，"
                "中南鸿思已取得客户NPO/CPO光引擎自动耦合设备订单并完成设计即将进入交付阶段(仍与EQ3成熟批量分离建档)；"
                '另一子公司苏州博众半导体负责共晶贴片设备且阶段性生产及订单排期饱满，保留公司主动警示"订单并不直接等同于收入")'
            ),
            "判定会话日期": SESSION_DATE,
        },
        # 8) P209 华工科技: ONLY append to 判定等级, strictly preserving 命中引语, 锚点URL, and prior 判定等级 prefix!
        "P209": {
            "判定等级": (
                "判定闸-生产中（2026-10-30投关第6页第2问，1.6T LPO为具体系列送样阶段，旧引语中的1.6T光模块为较宽产品口径）。"
                "历史证据（原检索日2026-07-30，原判定日2026-07-30）：公司实现全球第一梯队规模化交付800G硅光LPO系列和1.6T光模块产品。"
                "原锚：https://static.cninfo.com.cn/finalpage/2026-03-26/1225031509.PDF。"
                "原判定：判定闸-生产中(华工正源800G硅光LPO/1.6T规模化交付,2025联接业务营收60.97亿元(+53.39%);2024年报400G/800G规模交付跨年佐证)。"
                '2026-11-05互动易补充：2026年前三季度"光互联业务"实现营业收入65.39亿元(+26%)、净利润5.66亿元(+30%)、'
                "其中Q3单季净利润2.9亿元(环比+201%)，并提示上游核心物料供应呈结构性紧张态势；"
                '口径边界：互动易"光互联业务"与2025年报分部"光电器件系列产品"(60.97亿元)存在名称与核算边界差异，不直接跨期混算'
            ),
        },
        # 9) P202 云南鑫耀半导体材料有限公司 (Note: brief wrote P257 from memory, actual point_id is P202 at CSV L199)
        "P202": {
            "检索日期": SESSION_DATE,
            "判定等级": (
                "判定闸-生产中(路径②上市文件锚:母公司云南锗业2025年报披露;主体云南锗业控股84.53%+华为哈勃9.35%参股;子公司自述口径入点；"
                "母公司云南锗业(002428)2025年报p.15/p.23/p.33逐字核对挂接：磷化铟晶片产能15万片/年(2—4英寸)，"
                f'2025年"{yng_quotes["output_quote"]}"，磷化铟产品(折合4寸)销量同比上升73.77%)'
            ),
            "判定会话日期": SESSION_DATE,
        },
    }

    updated_rows_detail: list[dict[str, Any]] = []
    for pid, fields in target_updates.items():
        row_obj = ledger.update_fields(pid, fields)
        updated_rows_detail.append(
            {
                "point_id": pid,
                "csv_line_no": row_obj["line_no"],
                "company": row_obj["d"]["公司"],
                "cell_id": row_obj["d"]["cell_id"],
                "listing_tag": row_obj["d"]["上市标签"],
                "updated_columns": sorted(fields.keys()),
            }
        )

    # 10) Append P275 (EQ3) & P276 (EQ4) for 科瑞技术 (002957) from verified 2025 Annual Report p.15
    kerui_txt_path = ROOT / "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt"
    if not kerui_txt_path.is_file():
        raise FileNotFoundError(f"Missing 002957 2025 annual report sidecar: {kerui_txt_path}")
    kerui_norm_txt = norm_nospace(kerui_txt_path.read_text(encoding="utf-8", errors="ignore"))
    kerui_q_eq3 = "光模块芯片共晶贴片设备：适配光模块芯片贴装需求，实现高精度、高稳定性贴装，保障光模块性能"
    kerui_q_eq4 = "光耦合设备精度达 50nm，达到行业领先水平，技术产业化成果突出，在光模块领域提供多个核心工序的工艺设备并获得海外头部客户验证和认可"
    for kq in (kerui_q_eq3, kerui_q_eq4):
        if norm_nospace(kq) not in kerui_norm_txt:
            raise AssertionError(f"002957 2025 annual report verbatim check failed: {kq}")

    kerui_new_points = [
        (
            "P275",
            {
                "point_id": "P275",
                "公司": "科瑞技术",
                "cell_id": "EQ3",
                "状态": "生产中",
                "上市标签": "A股",
                "命中引语": kerui_q_eq3,
                "锚点URL": "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
                "检索日期": SESSION_DATE,
                "判定等级": (
                    "判定闸-生产中(2025年报p.15一手披露自主研发并规模化交付超高精度设备,共晶设备精度突破1um、"
                    "光模块芯片共晶贴片设备实现高精度贴装供货;"
                    '注记:2025年报仅匿名披露"国内行业标杆企业以及海外光器件品牌企业/海外头部客户",'
                    "全篇未具名Lumentum或Coherent,严格守住匿名客户边界)"
                ),
                "判定会话日期": SESSION_DATE,
            },
        ),
        (
            "P276",
            {
                "point_id": "P276",
                "公司": "科瑞技术",
                "cell_id": "EQ4",
                "状态": "生产中",
                "上市标签": "A股",
                "命中引语": kerui_q_eq4,
                "锚点URL": "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
                "检索日期": SESSION_DATE,
                "判定等级": (
                    "判定闸-生产中(2025年报p.15一手披露光器件耦合设备及50nm精度光耦合设备技术产业化成果突出并获海外头部客户验证和认可;"
                    '注记:2025年报全篇仅匿名表述"海外头部客户/海外光器件品牌企业",'
                    "严禁在未获监管具名印证前写Lumentum/Coherent供应链边)"
                ),
                "判定会话日期": SESSION_DATE,
            },
        ),
    ]
    for pid, full_row in kerui_new_points:
        row_obj = ledger.upsert_row(pid, full_row)
        updated_rows_detail.append(
            {
                "point_id": pid,
                "csv_line_no": row_obj["line_no"],
                "company": row_obj["d"]["公司"],
                "cell_id": row_obj["d"]["cell_id"],
                "listing_tag": row_obj["d"]["上市标签"],
                "updated_columns": sorted(full_row.keys()),
            }
        )

    # Hard assertions on P031, P209, P257
    assert ledger.by_id("P031")["d"] == p031_before and not ledger.by_id("P031")["dirty"], "P031 must not be modified!"
    assert ledger.by_id("P257")["d"] == p257_before and not ledger.by_id("P257")["dirty"], "P257 (珠海鼎泰芯源) must not be modified!"
    assert ledger.by_id("P209")["d"]["命中引语"] == p209_before["命中引语"], "P209 命中引语 must not be modified!"
    assert ledger.by_id("P209")["d"]["锚点URL"] == p209_before["锚点URL"], "P209 锚点URL must not be modified!"

    # Run scan.py point-level and QA-quote invariants across all 269 rows before saving
    all_pts = [r["d"] for r in ledger.rows]
    del scan.ERR[:]
    for pt in all_pts:
        scan._check_point_row(pt)
    scan._check_point_table(all_pts)
    for pt in all_pts:
        m = re.search(r"corpus/qa/(\d+)/qa\.jsonl", pt.get("锚点URL", "") or "")
        if m:
            qf = DST_QA / m.group(1) / "qa.jsonl"
            assert qf.is_file(), f"Missing QA file for {pt['point_id']}: {qf}"
            q_norm = norm_nospace((pt.get("命中引语") or "").strip('"').split("(互动易")[0].strip('"'))
            blob_norm = norm_nospace(qf.read_text(encoding="utf-8"))
            assert q_norm in blob_norm, f"{pt['point_id']} QA quote not found after QA sync!"
    if scan.ERR:
        errs = list(scan.ERR)
        del scan.ERR[:]
        raise AssertionError(f"scan.py point invariants failed: {errs}")

    changed, data = ledger.save_if_changed()
    return {
        "changed_this_run": changed,
        "sha256": sha256_bytes(data),
        "total_rows": len(ledger.rows),
        "updated_point_count": len(updated_rows_detail),
        "updated_points": updated_rows_detail,
        "id_mapping_note": (
            "points.csv 中 `云南鑫耀半导体材料有限公司` 精确行号为 L199 `P202`（母公司云南锗业 002428），"
            "而 L253 `P257` 为 `珠海鼎泰芯源晶体有限公司`（博杰股份参股）；已精确更新 `P202` 并保持 `P257` 零改动。"
        ),
    }


# ---------------------------------------------------------------------------
# 4. Append batch=step3_daily_2026q4 (CLG0598–CLG0631) to content_ledger.csv
# ---------------------------------------------------------------------------
def build_step3_content_ledger_rows() -> list[dict[str, str]]:
    """34 high-signal, strictly dual-gate isolated, 100% locally verbatim-verified atomic facts."""
    specs: list[tuple[str, str, str, str, str, str, str, str, str, str, str, str, str]] = [
        # (company, code, source_doc, doc_year, fact_type, stance, tense, cell_ids, atomic_fact, verbatim_quote, section_ref, local_source_path, anchor_url)
        (
            "中际旭创",
            "300308",
            "2026年10月29日投资者关系活动记录表（编号：2026-009）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "MOD1,D12",
            "中际旭创表示NPO等下一代新产品2027年仍处于新产品导入阶段，需经历产能与良率爬坡及上游物料扩产，预计2027年下半年开始逐步上量，2028年实现大规模部署。",
            "相关产品明年仍处于新产品导入阶段，需要经历产能和良率爬坡，相关原材料的供应商也需要逐步产能上量，客户下单时会综合考虑上述因素。预计 2027 年下半年新产品将开始逐步上量，2028 年放量速度将进一步加快，真正大规模部署预计在 2028 年。",
            "三、投资者问答环节·Q8（L179-L182）",
            "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "中际旭创",
            "300308",
            "2026年10月29日投资者关系活动记录表（编号：2026-009）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "MOD1",
            "2026年9月底受泰国降雨影响物流，中际旭创部分成品发货推后并于10月初恢复正常；约30亿美元存货中较大部分系为后续订单提前准备的原材料备料。",
            "一方面，泰国降雨影响物流，部分成品发货有所推后；另一方面，存货中的部分半成品和成品因在途或物流周转放缓形成库存。进入四季度后相关影响已经消除，10 月初发货已恢复正常。具体影响较难量化，公司存货约 30 亿美元，其中较大部分是为后续订单准备的原材料备料，洪水影响占存货增量的比重不高，对收入主要体现为时间性差异，整体影响可控，目前存货周转速度较为健康。",
            "三、投资者问答环节·Q4（L145-L150）",
            "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "中际旭创",
            "300308",
            "2026年10月29日投资者关系活动记录表（编号：2026-009）",
            "2026",
            "技术参数",
            "industry",
            "current",
            "C4,D12,MOD1",
            "2027至2028年行业一系列新光互连产品主要依托单波200G技术，同时行业正同步研发单波400G技术以支撑更高带宽与更丰富产品形态。",
            "单波 200G 技术预计仍将持续一段时间， 2027-2028 年的一系列新产品，主要将依托单波 200G 技术。行业也在开发单波 400G 技术等，后续围绕单波 400G 将出现更多新技术方案、更高带宽和更丰富的产品形态。",
            "三、投资者问答环节·Q14（L222-L225）",
            "corpus/ir/300308/300308_2026-10-29_投资者关系活动记录表20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "中际旭创",
            "300308",
            "2026年11月3日投资者关系活动记录表（编号：2026-010）",
            "2026",
            "工序步骤",
            "neutral",
            "planned",
            "C1,C5,D9,D12",
            "NPO新产品导入初期除产品制造良率爬坡外，更高功率CW光源、电芯片等全新上游物料均需经历良率爬坡；在CPO方案中公司现阶段参与最快的主要环节为FAU和ELS外置光源。",
            "NPO 预计于 2027 年下半年开始起量，更多需求预计在 2028 年释放。在新产品导入初期，产品的制造良率需要爬坡，此外更高功率的 CW 光源、电芯片等全新上游物料均需经历良率爬坡，这是新产品量产的正常过程。",
            "二、Q&A·Q7（L120-L123）",
            "corpus/ir/300308/300308_2026-11-03_投资者关系活动记录表20261103.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "罗博特科/ficonTEC",
            "300757",
            "2026年10月29日投资者关系活动记录表（编号：2026-06）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "EQ7",
            "罗博特科Insertion 4全自动系统级测试设备目前仍处于设计开发及客户协同推进阶段，除高精度测试外还需集成热管理等功能，尚未进入批量化阶段。",
            "Insertion 4 全自动系统级测试设备目前仍处于设计开发及客户协同推进阶段，尚未取得批量化订单。该设备除高精度测试外，还需要集成热管理等功能，公司正与客户及相关专业供应方共同推进。",
            "二、问题交流·问题7（L168-L171）",
            "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "罗博特科/ficonTEC",
            "300757",
            "2026年10月29日投资者关系活动记录表（编号：2026-06）",
            "2026",
            "设备-工序能力",
            "neutral",
            "current",
            "EQ4,EQ7",
            "罗博特科苏州基地处于满负荷运行并持续扩产，承担面向可插拔光模块的组装整线设备、FAU全自动产线设备及单面晶圆测试与晶粒测试设备的生产交付。",
            "苏州基地目前处于较满负荷运行状态，产能仍在持续扩张，包括面向可插拔光模块客户的各类组装系列的产品及相关整线设备需求、FAU 全自动产线设备及部分测试设备（目前主要为单面晶圆测试设备及部分晶粒测试设备）的生产交付任务。",
            "二、问题交流·问题2（L79-L83）",
            "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "罗博特科/ficonTEC",
            "300757",
            "深交所互动易问答快照（2026-11-02回复）",
            "2026",
            "工序步骤",
            "neutral",
            "current",
            "EQ7",
            "CPO晶圆级测试（Insertion 2）用于识别CPO光引擎中的失效芯片（bad die），为改进流片制程提供依据并防止后续制程损失；公司新一代Insertion 2设计工作基本就绪。",
            "下游客户存在ｉｎｓｅｒｔion 2测试需求。ｉｎｓｅｒｔion 2测试可帮助客户识别CPO光引擎中的相关失效芯片，并为改进流片制程提供依据，有助于提升产品良率。其次，INS2 测试过程中判断出bad die 可以有效防止后续制程损失，最后，客户产品升级带来了新的测试功能要求，对INS2的测试功能及适配能力提出了更高要求。",
            "互动易回复 2026-11-02（indexId=2395374488872419328）",
            "corpus/qa/300757/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "罗博特科/ficonTEC",
            "300757",
            "深交所互动易问答快照（2026-11-02回复）",
            "2026",
            "代际事件",
            "issuer_self",
            "current",
            "EQ7",
            "罗博特科自述在CPO测试环节Insertion 2与Insertion 3占据特殊市场地位并已向核心客户提供批量化量产设备，而Insertion 4系统级测试设备处于配合核心客户NPI开发进程中。",
            "在CPO测试环节，公司在ｉｎｓｅｒｔion2和ｉｎｓｅｒｔion3占据特殊的市场地位，已为核心客户提供批量化量产设备，并将按照其需求节奏的要求，持续为核心客户提供后续不断增加的量产设备，系CPO技术的商业化进程在测试设备端的核心支撑方。ｉｎｓｅｒｔion 4目前处在公司配合核心客户NPI的进程中，公司正在按照客户的需求加快推进该系统级测试设备的开发进程。",
            "互动易回复 2026-11-02（indexId=2387956814085226496）",
            "corpus/qa/300757/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "天孚通信",
            "300394",
            "2026年10月29日投资者关系活动记录表（编号：2026-013）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "D9,D12",
            "天孚通信为CPO架构配套的FAU、ELS等产品在性能、良率及交付保障方面已具备基础，目前已实现稳定量产交付。",
            "公司为 CPO 架构配套的 FAU、ELS 等产品在性能、良率及交付保障等方面已具备较好的基础，目前相关产品已实现稳定量产交付，预计 2027 年 CPO 配套产品在公司销售收入中占比会明显增加。",
            "投资者关系活动主要内容介绍·问题2（L49-L52）",
            "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "天孚通信",
            "300394",
            "2026年10月29日投资者关系活动记录表（编号：2026-013）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "D9",
            "与传统FAU相比，CPO用FAU产品具有高密度和多通道特征，对产品设计、制程工艺及配套设备提出更高要求，核心壁垒体现在良率效率、批量交付能力和量产稳定性。",
            "FAU 是 CPO 中的关键无源器件之一，与传统 FAU 相比，CPO 用 FAU 产品具有高密度和多通道的特征，对产品设计、制程工艺、配套设备均提出了更高要求，整体工艺难度明显增加。",
            "投资者关系活动主要内容介绍·问题3（L59-L61）",
            "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "天孚通信",
            "300394",
            "2026年10月29日投资者关系活动记录表（编号：2026-013）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "D9,D12",
            "天孚通信NPO配套产品目前仍处于研发推进、客户送样和验证阶段，若验证和导入顺利预计2027年有望实现规模量产。",
            "NPO 配套产品目前仍处于研发推进、客户送样和验证阶段，整体进度符合预期。若后续验证和客户导入顺利，预计 2027 年也有望实现规模量产。",
            "投资者关系活动主要内容介绍·问题5（L79-L81）",
            "corpus/ir/300394/300394_2026-10-29_2026年10月29日天孚通信投资者关系活动记录表.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "新易盛",
            "300502",
            "2026年10月29日投资者关系活动记录表（编号：2026-006）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "MOD1",
            "2026年9月下旬泰国洪灾对新易盛园区生产运营未产生影响、无货物损坏无需计提减值，主要影响物流环节导致9月下旬部分产品未能发出或报关出口。",
            "泰国 9 月下旬的洪灾对公司园区的生产运营未产生任何影响，公司无货物损坏，无需计提减值。洪灾主要影响物流环节。公司 9 月下旬为发货集中期，与洪灾时间高度重合，导致部分产品未能发出或报关出口。",
            "投资者关系活动主要内容介绍·问题10（L116-L118）",
            "corpus/ir/300502/300502_2026-10-29_300502新易盛投资者关系管理信息20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "新易盛",
            "300502",
            "2026年10月29日投资者关系活动记录表（编号：2026-006）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "MOD1,D12",
            "新易盛正推进NPO产品开发并提前规划产能，预计2027年实现批量出货、2028年有望进入大规模出货。",
            "公司正在顺利推进 NPO 产品开发，预计 2027 年实现批量出货，2028 年有望进入大规模出货。产能及材料端正与客户紧密配合，并提前规划产能，NPO 起量后将成为公司主要产品及重要业绩贡献点。",
            "投资者关系活动主要内容介绍·问题3（L84-L86）",
            "corpus/ir/300502/300502_2026-10-29_300502新易盛投资者关系管理信息20261029.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "新易盛",
            "300502",
            "深交所互动易问答快照（2026-11-11及11-12回复）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "MOD1",
            "2026年三季度原材料供给依旧紧张，新易盛三季度产量保持环比增长，受物流客观因素跨期的发货已在10月确认收入，且1.6T产品四季度放量趋势更明显。",
            "今年三季度原材料供给依旧紧张，公司三季度产量保持环比增长，受客观因素影响导致部分收入确认跨期，截止目前受影响部分的发货已在10月确认收入。",
            "互动易回复 2026-11-11（indexId=2392647581911461888）",
            "corpus/qa/300502/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "华工科技",
            "000988",
            "深交所互动易问答快照（2026-11-05回复）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "MOD1",
            "华工科技2026年前三季度光互联业务实现营业收入65.39亿元（同比增长26%）、净利润5.66亿元（同比增长30%），其中Q3单季净利润2.9亿元（环比增长201%）；上游核心物料呈结构性紧张。",
            "公司光互联业务前三季度实现营业收入65.39亿元，同比增长26%，净利润5.66亿元，同比增长30%，其中Q3净利润2.9亿元，环比大幅增加201%。当前行业整体处于供不应求的快速发展阶段，上游核心物料供应呈现结构性紧张态势，通过提前备货、客户背书、方案多元化及国产化协同，公司物料交付满足率将持续提升。",
            "互动易回复 2026-11-05（indexId=2384454200341168128）",
            "corpus/qa/000988/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "华工科技",
            "000988",
            "深交所互动易问答快照（2026-10-14回复）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "MOD1,D12",
            "华工科技已联合产业链开发单通道100G/Lane与200G/Lane的3.2T/6.4T NPO产品，目前正处于海内外头部AI厂商产品测试阶段。",
            "公司已联合产业链率先开发100G/Lane、200G/Lane的3.2T/6.4T NPO产品，目前已在国内和海外头部AI厂商进行产品测试中。",
            "互动易回复 2026-10-14（indexId=2370098641376337920）",
            "corpus/qa/000988/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "剑桥科技",
            "603083",
            "上证e互动问答快照（2026-11-10回复）",
            "2026",
            "设备-工序能力",
            "neutral",
            "current",
            "MOD1",
            "剑桥科技越南生产基地相关高速光模块产线已通过客户审核认证，实现海外产能落地。",
            "越南生产基地相关产线已通过客户审核认证，顺利实现产能在海外落地。",
            "上证e互动回复 2026-11-10（越南生产基地进展）",
            "corpus/qa/603083/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "剑桥科技",
            "603083",
            "上证e互动问答快照（2026-11-10回复）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "MOD1",
            "截至2026年9月初，剑桥科技已形成约100万支/月高速光模块设计产能且产能利用率保持高位；1.6T光模块已在三个客户开展测试。",
            "截至2026年9月初，公司已基本形成设计产能约100万支/月的生产能力，当前高速光模块订单需求旺盛，产能利用率持续保持高位，公司计划在未来约15个月继续推进产能大幅扩张，保障800G及1.6T产品交付。1.6T光模块方面，公司已经在三个客户测过了，具体出货和量产节奏，请您关注公司在指定信息披露媒体发布的公告。",
            "上证e互动回复 2026-11-10（设计产能与1.6T进展）",
            "corpus/qa/603083/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "剑桥科技",
            "603083",
            "上证e互动问答快照（2026-11-10回复）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "MOD1,D12,C4",
            "剑桥科技基于新一代硅光的800G光模块已于2026年上半年大批量发货；新一代1.6T OSFP 2xDR4/2xFR4与ELSFP预计2026年下半年批量发货，并启动12.8T XPO及3.2T/6.4T/7.2T NPO定制开发与送样。",
            "高速光模块方面，基于新一代硅光的800G相关光模块完成多家海外大客户的认证，已经在2026年上半年实现大批量发货；新一代1.6T OSFP 2xDR4和2xFR4光模块产品完成认证测试，预计2026年下半年实现大批量发货；ELSFP产品完成开发验证和客户送样，预计2026年下半年开始批量发货；公司还启动了12.8T XPO以及3.2T、6.4T、7.2T等多个NPO产品的多家客户定制化开发，已陆续进行研发验证和客户送样。",
            "上证e互动回复 2026-11-10（高速光模块与NPO/XPO布局）",
            "corpus/qa/603083/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "博众精工",
            "688097",
            "上证e互动问答快照（2026-09-03回复）",
            "2026",
            "设备-工序能力",
            "neutral",
            "current",
            "EQ3,EQ4",
            "博众精工收购控股子公司中南鸿思60%股权后形成芯片贴装、光学耦合到整线组装的光模块全流程自动化闭环能力；中南鸿思已取得NPO与CPO光引擎自动耦合设备订单并即将进入交付阶段。",
            "公司控股子公司中南鸿思主营耦合机设备，光学耦合是CPO封装环节的重要工艺环节，耦合机属于该领域的关键工艺装备。公司完成对中南鸿思收购后，将自身芯片贴装、整线自动化能力与中南鸿思光学耦合技术实现协同互补，已具备从贴片、耦合到组装的光模块全流程自动化闭环能力，可向客户提供一体化柔性解决方案。",
            "上证e互动回复 2026-09-03（indexId=0001C1AE1A91A5144DF394A41B68FB166AEC）",
            "corpus/qa/688097/qa.jsonl",
            "https://static.cninfo.com.cn/finalpage/2026-08-25/1225498439.PDF#page=54",
        ),
        (
            "博众精工",
            "688097",
            "上证e互动问答快照（2026-11-17回复）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "EQ3",
            "博众精工澄清光模块设备排期报道采访主体为子公司苏州博众半导体，如实反映其阶段性生产及订单排期现状，并提示订单存在变更或延期风险、订单并不直接等同于收入。",
            "该报道采访主体为公司下属子公司苏州博众半导体，相关表述如实反映了苏州博众半导体阶段性生产及订单排期现状。需要提示，订单存在客户变更、延期等不确定性风险，订单并不直接等同于收入，最终收入确认、经营业绩以公司后续披露的定期报告为准，请广大投资者注意投资风险。",
            "上证e互动回复 2026-11-17（苏州博众半导体订单排期澄清）",
            "corpus/qa/688097/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "长光华芯",
            "688048",
            "上证e互动问答快照（2026-09-08回复）",
            "2026",
            "产品构成",
            "neutral",
            "current",
            "C1",
            "2026年上半年长光华芯批量交付的光通信芯片产品主要为100G EML芯片。",
            "2026年上半年，公司批量交付的光通信产品主要为100G EML 芯片。",
            "上证e互动回复 2026-09-08（光通信业务收入结构）",
            "corpus/qa/688048/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "长光华芯",
            "688048",
            "上证e互动问答快照（2026-09-08回复）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "C1",
            "截至2026年9月8日官方回复，长光华芯200G EML芯片仍处于客户验证阶段，正在推进验证及客户订单对接。",
            "目前，公司 200G EML 芯片尚处于客户验证阶段，公司会持续积极推动相关产品验证及客户订单对接工作。",
            "上证e互动回复 2026-09-08（200G EML进展）",
            "corpus/qa/688048/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "长光华芯",
            "688048",
            "上证e互动问答快照（2026-05-29回复）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "C1",
            "长光华芯澄清200G EML芯片已送样客户但尚在客户验证中，暂未获得大客户订单。",
            "200GEML是公司全系列光通信芯片的重要组成部分，该产品已送样客户，目前尚在客户验证中，暂未获得您所述的大客户订单。",
            "上证e互动回复 2026-05-29（indexId=00019AD9A984ADBC4053A20FFD6D46C3B8C6）",
            "corpus/qa/688048/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "光迅科技",
            "002281",
            "深交所互动易问答快照（2026-05-14回复）",
            "2026",
            "产品构成",
            "neutral",
            "current",
            "C5,D6,MOD1",
            "光迅科技确认其光模块所用DSP芯片采用外购形式，且当前未生产光隔离器用法拉第旋光片。",
            "1、公司DSP芯片采用外购形式。2、公司高端光芯片进展顺利，相关情况以公司公告为准。3、公司当前未生产光隔离器用的法拉第旋片，感谢您的关注。",
            "互动易回复 2026-05-14（indexId=8d70f034763e4cdda796ce2621b52557）",
            "corpus/qa/002281/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "光迅科技",
            "002281",
            "深交所互动易问答快照（2026-05-14回复）",
            "2026",
            "代际事件",
            "neutral",
            "planned",
            "MOD1",
            "光迅科技3.2T和6.4T高速光模块处于研发及测试验证阶段。",
            "公司3.2T和6.4T光模块当前处于研发及测试验证阶段，感谢您的关注。",
            "互动易回复 2026-05-14（indexId=c204ab7f7e5f41f9b42c4ffbc63af9e1）",
            "corpus/qa/002281/qa.jsonl",
            "https://irm.cninfo.com.cn/",
        ),
        (
            "景旺电子",
            "603228",
            "上证e互动问答快照（2026-10-13回复）",
            "2026",
            "代际事件",
            "neutral",
            "current",
            "B1",
            "截至2026年三季度末，景旺电子在AI服务器与数据中心、高速光模块PCB领域的在手订单饱满，产能利用率及良率处于较高水平（与2026半年报批量交付800G/1.6T光模块PCB相衔接）。",
            "截至2026年三季度末，公司在AI服务器与数据中心、高速光模块领域的在手订单饱满，产能利用率及良率较高，公司正全力保障交付目标的达成。",
            "上证e互动回复 2026-10-13（高速光模块PCB订单与良率）",
            "corpus/qa/603228/qa.jsonl",
            "https://static.cninfo.com.cn/finalpage/2026-08-22/1225493416.PDF#page=11",
        ),
        (
            "景旺电子",
            "603228",
            "上证e互动问答快照（2026-10-16回复）",
            "2026",
            "产品构成",
            "neutral",
            "current",
            "B1",
            "景旺电子珠海金湾基地主要生产可用于AI服务器与数据中心、光模块、交换机等领域的高多层板（HLC）、高阶HDI及类载板（SLP）。",
            "目前，公司珠海金湾基地的主要产品为可以用于AI服务器与数据中心、光模块、交换机等领域的HLC、高阶HDI、SLP，具体产品信息请以公司公告为准。",
            "上证e互动回复 2026-10-16（珠海金湾基地光模块PCB产品构成）",
            "corpus/qa/603228/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "炬光科技",
            "688167",
            "上证e互动问答快照（光通信微光学产品构成）",
            "2025",
            "产品构成",
            "neutral",
            "current",
            "D7,D9",
            "炬光科技适用于光通信领域的产品涵盖微透镜及阵列、V型槽阵列、微棱镜透镜及阵列、快慢轴一体化准直耦合透镜、NxN大透镜阵列，用于TOSA/ROSA/PIC/CPO高效准直耦合（2026-11-05定增募集说明书p.86进一步披露大于36通道V型槽转批量及MPLA技术许可协议执行）。",
            "公司目前适用于光通信应用的产品涵盖微透镜及阵列、V型槽阵列、微棱镜透镜及阵列、快慢轴一体化准直耦合透镜、NxN大透镜阵列等多款产品，其中既有行业通用标准产品也有客户定制产品。",
            "上证e互动回复 2025-08-12（光通信元件品类；关联2026-11-05募集说明书p.86）",
            "corpus/qa/688167/qa.jsonl",
            "https://static.cninfo.com.cn/finalpage/2026-11-05/1225658451.PDF#page=86",
        ),
        (
            "凯格精机",
            "301338",
            "2026年9月3日投资者关系活动记录表（编号：2026-003）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "EQ3,EQ4",
            "凯格精机光模块自动化组装整线采用龙门双驱直线电机架构，最高产能（UPH）达400pcs，重复定位精度±5μm，组装精度±25μm，CPK≥1.67，已实现海外批量交付并推出用于COC/COS/TO的脉冲加热共晶机。",
            "光模块自动化整线方案覆盖多领域光模块场景，采用龙门双驱直线电机架构，经仿真优化，将 FMS 模块化标准设计理念与统一软件框架深度融合，最终实现光模块组装段全流程自动化。最高产能（UPH）达 400pcs；支持不停机换料，支持模块化切换执行单元；重复定位精度± 5μm，组装精度±25μm；符合 CE 安全标准；过程能力指数 CPK≥1.67，支持全流程智能化管控与远程运维。公司的光模块自动化整线解决方案已实现海外批量交付。同时，公司积极布局光通信领域，推出用于 COC/COS/TO 等产品的脉冲加热共晶机，计划推出隔离器、透镜类点胶设备，储备了光模块领域专用设备技术。",
            "投资者关系活动主要内容介绍·问题4（L73-L84）",
            "corpus/ir/301338/301338_2026-09-03_2026年9月3日投资者关系活动记录表.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "东山精密/索尔思",
            "002384",
            "2026年11月2日投资者关系活动记录表（编号：2026-11-02）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "C1,MOD1",
            "东山精密表示公司光模块业务所用光芯片部分为自研自产，在光模块整体BOM成本中占比不超过10%。",
            "公司光模块业务所用光芯片部分为自研自产，在光模块整体 BOM 成本中占比不超过 10%，其余绝大多数物料采购可更好适配原产地比例要求，整体合规空间充足，未来也可通过供应链优化进一步满足相关要求，同时公司未来不排除在美国布局产能。",
            "投资者提出的问题及公司回复情况·问题17（L195-L199）",
            "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "东山精密/索尔思",
            "002384",
            "2026年11月2日投资者关系活动记录表（编号：2026-11-02）",
            "2026",
            "工序步骤",
            "neutral",
            "current",
            "EQ1,M2a,C1",
            "东山精密指出光芯片扩产的真正瓶颈不在于MOCVD设备，而在于后续外延生长、多轮可靠性验证及光模块联调的工艺周期。",
            "MOCVD 设备不是长期扩产瓶颈。光芯片业务对供应稳定性和量产爬坡效率要求较高，现用 MOCVD 为市场主流设备，公司需优先保障产线稳定快速上量。本轮扩产完成后，公司预计未来 3 至 5 年的产能可得到保障。真正瓶颈不在设备，而在于后续外延、多轮可靠性验证及模块联调的工艺周期。",
            "投资者提出的问题及公司回复情况·问题7（L95-L103）",
            "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "仕佳光子",
            "688313",
            "上证e互动问答快照（2026-08-14回复）",
            "2026",
            "产品构成",
            "neutral",
            "current",
            "M1,D8",
            "仕佳光子澄清其AWG芯片产品原材料为二氧化硅系而不涉及高纯铟或磷化铟，且公司自身不生产磷化铟（InP）衬底，相关衬底原材料均为外部采购。",
            "公司不生产磷化铟（InP）衬底，相关衬底原材料均为外部采购。",
            "上证e互动回复 2026-08-14（磷化铟衬底边界澄清）",
            "corpus/qa/688313/qa.jsonl",
            "https://sns.sseinfo.com/",
        ),
        (
            "汇绿生态",
            "001267",
            "2026年11月3日投资者关系活动记录表（编号：2026-008）",
            "2026",
            "技术参数",
            "neutral",
            "current",
            "MOD1",
            "汇绿生态控股子公司武汉钧恒目前光模块年产能分布为：武汉本部约300万支/年、2025年底投产的鄂州工厂一期约150万支/年、2026年4月底投产的马来西亚工厂约100万-150万支/年。",
            "公司目前光模块产能为：武汉本部约 300 万支/年、2025 年年底投产的鄂州工厂一期约 150 万支/年、2026 年 4 月底投产的马来西亚工厂约 100 万-150 万支/年。",
            "投资者关系活动主要内容介绍·问题六（L71-L73）",
            "corpus/ir/001267/001267_2026-11-03_001267汇绿生态投资者关系管理信息20261103.pdf.txt",
            "https://www.cninfo.com.cn/",
        ),
        (
            "科瑞技术",
            "002957",
            "2025年年度报告",
            "2025",
            "设备-工序能力",
            "neutral",
            "current",
            "EQ3",
            "科瑞技术2025年报披露自主研发并规模化交付光模块芯片共晶贴片设备（共晶设备精度突破1um），适配光模块芯片高精度贴装需求；核心客户匿名表述为国内行业标杆企业及海外光器件品牌企业。",
            "光模块芯片共晶贴片设备：适配光模块芯片贴装需求，实现高精度、高稳定性贴装，保障光模块性能",
            "第三节 管理层讨论与分析·二、报告期内公司从事的主要业务（p.15，L642-L648）",
            "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt#L642..648",
            "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        ),
        (
            "科瑞技术",
            "002957",
            "2025年年度报告",
            "2025",
            "技术参数",
            "issuer_self",
            "current",
            "EQ4",
            "科瑞技术2025年报自述光耦合设备精度达50nm并在光模块多个核心工序提供工艺设备且获海外头部客户验证认可（全篇仅匿名表述海外头部客户/海外光器件品牌企业，未具名Lumentum或Coherent）。",
            "光耦合设备精度达 50nm，达到行业领先水平，技术产业化成果突出，在光模块领域提供多个核心工序的工艺设备并获得海外头部客户验证和认可",
            "第三节 管理层讨论与分析·二、报告期内公司从事的主要业务（p.15，L630-L648）",
            "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt#L642..648",
            "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        ),
    ]

    rows: list[dict[str, str]] = []
    for idx, spec in enumerate(specs, start=598):
        (
            company,
            code,
            source_doc,
            doc_year,
            fact_type,
            stance,
            tense,
            cell_ids,
            atomic_fact,
            verbatim_quote,
            section_ref,
            local_source_path,
            anchor_url,
        ) = spec
        rows.append(
            {
                "cid": f"CLG{idx:04d}",
                "company": company,
                "stock_code_or_ticker": code,
                "source_doc": source_doc,
                "doc_year": doc_year,
                "fact_type": fact_type,
                "stance": stance,
                "tense": tense,
                "cell_ids": cell_ids,
                "atomic_fact": atomic_fact,
                "verbatim_quote": verbatim_quote,
                "section_ref": section_ref,
                "local_source_path": local_source_path,
                "anchor_url": anchor_url,
                "quote_verification_status": "verified_local",
                "batch": BATCH_ID,
            }
        )
    return rows


def update_content_ledger_csv() -> dict[str, Any]:
    with CONTENT_LEDGER_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == CONTENT_LEDGER_COLUMNS, f"Unexpected columns: {reader.fieldnames}"
        existing_rows = list(reader)

    base_rows = [r for r in existing_rows if r.get("batch") != BATCH_ID]
    assert len(base_rows) == 597, f"Expected 597 pre-Step3 content_ledger rows, found {len(base_rows)}"

    new_rows = build_step3_content_ledger_rows()
    all_rows = base_rows + new_rows

    # Gate 1: scan._check_content_ledger against live tree.yaml leaf cells
    tree_doc = yaml.safe_load((ROOT / "tree.yaml").read_text(encoding="utf-8"))
    leaf_cells = scan._tree_leaf_cells(tree_doc)
    del scan.ERR[:]
    scan._check_content_ledger(all_rows, leaf_cells)
    if scan.ERR:
        errs = list(scan.ERR)
        del scan.ERR[:]
        raise AssertionError(f"scan._check_content_ledger failed: {errs}")

    # Gate 2: Single-line hygiene + forbidden phrasing + 100.0% local verbatim quote substring verification
    source_cache: dict[str, str] = {}
    quote_hits = 0
    for r in new_rows:
        for col, val in r.items():
            if "\n" in val or "\r" in val:
                raise ValueError(f"Embedded newline in {r['cid']}.{col}")
        for forbidden in ("已覆盖", "已完成", "已回答"):
            if forbidden in r["atomic_fact"] or forbidden in r["verbatim_quote"]:
                raise ValueError(f"Forbidden completion phrasing {forbidden!r} in {r['cid']}")
        rel_path = r["local_source_path"].split("#")[0]
        full_path = ROOT / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"{r['cid']} missing local_source_path: {rel_path}")
        if rel_path not in source_cache:
            source_cache[rel_path] = norm_nospace(full_path.read_text(encoding="utf-8", errors="ignore"))
        if norm_nospace(r["verbatim_quote"]) not in source_cache[rel_path]:
            raise AssertionError(f"Verbatim quote miss for {r['cid']} in {rel_path}: {r['verbatim_quote']}")
        quote_hits += 1

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CONTENT_LEDGER_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(all_rows)
    payload = ("\ufeff" + buf.getvalue()).encode("utf-8")

    # Verify physical line count == len(all_rows) + 1
    phys_lines = payload.decode("utf-8-sig").splitlines()
    assert len(phys_lines) == len(all_rows) + 1, (
        f"content_ledger.csv physical lines {len(phys_lines)} != {len(all_rows) + 1}"
    )

    changed = write_bytes_if_changed(CONTENT_LEDGER_CSV, payload)
    return {
        "changed_this_run": changed,
        "sha256": sha256_bytes(payload),
        "base_rows": len(base_rows),
        "added_rows": len(new_rows),
        "total_rows": len(all_rows),
        "physical_csv_lines": len(phys_lines),
        "batch": BATCH_ID,
        "added_cid_range": f"{new_rows[0]['cid']}..{new_rows[-1]['cid']}",
        "added_cids": [r["cid"] for r in new_rows],
        "added_csv_line_range": f"L{len(base_rows) + 2}..L{len(all_rows) + 1}",
        "verbatim_quote_hits": f"{quote_hits}/{len(new_rows)} (100.0%)",
        "companies_covered_in_batch": dict(Counter(f"{r['stock_code_or_ticker']} {r['company']}" for r in new_rows)),
        "fact_type_counts_in_batch": dict(Counter(r["fact_type"] for r in new_rows)),
        "stance_counts_in_batch": dict(Counter(r["stance"] for r in new_rows)),
    }


def main() -> None:
    ir_summary = sync_domestic_ir()
    qa_summary = sync_domestic_qa()
    yng_quotes = verify_yng_2025_annual_quote()
    points_summary = update_points_csv(yng_quotes)
    cl_summary = update_content_ledger_csv()

    summary_doc = {
        "shard": "Step 3 Worker 1 (carbon-daily-domestic)",
        "workpack_id": "OPTICAL-STEP3-DAILY-AND-V6-20261121",
        "script": "out/step3-daily-and-v6-20261121/ingest_domestic_daily.py",
        "domestic_ir_sync": {
            k: v for k, v in ir_summary.items() if k not in ("files_written_this_run", "files_unchanged_this_run")
        },
        "domestic_qa_sync": {
            k: v
            for k, v in qa_summary.items()
            if k not in ("files_written_this_run", "files_unchanged_this_run")
        },
        "yng_002428_2025_annual_verified_quotes": yng_quotes,
        "points_csv_update": {k: v for k, v in points_summary.items() if k != "changed_this_run"},
        "content_ledger_update": {k: v for k, v in cl_summary.items() if k != "changed_this_run"},
        "downstream_test_note": (
            "tests/test_step2_archive_salvage.py:202,205 此前对 content_ledger.csv 总行数写死 assertEqual(len(rows), 597) "
            "与 assertEqual(len(companies), 20)；本轮按指令追加 batch=step3_daily_2026q4 后总行数为 633、唯一公司数为 25 "
            "(其中 v1_salvage+step2_expansion 仍精确保持 597 行与 20 家公司)，供终验合成器在回归测试门对齐。"
        ),
    }
    summary_bytes = (json.dumps(summary_doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_bytes_if_changed(SUMMARY_JSON, summary_bytes)

    print(
        f"[OK] IR synced: {ir_summary['synced_code_count']} codes / {ir_summary['total_synced_files']} files | "
        f"QA synced: {qa_summary['synced_qa_code_count']} codes ({qa_summary['total_source_lines']} -> {qa_summary['total_deduped_lines']}, "
        f"-{qa_summary['total_duplicates_removed']} dups) | "
        f"points.csv updated: {points_summary['updated_point_count']} rows (sha256={points_summary['sha256'][:12]}) | "
        f"content_ledger.csv: +{cl_summary['added_rows']} ({cl_summary['added_cid_range']}, {cl_summary['verbatim_quote_hits']}, "
        f"sha256={cl_summary['sha256'][:12]})"
    )


if __name__ == "__main__":
    main()
