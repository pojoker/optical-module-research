#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 4 工人 2 (carbon-s4-points-triage):
points.csv 历史旧锚全归一化、triage.csv 待判尾项裁决与 11 条国内 DRQ 一手核查落盘。

严格写路径白名单:
  - points.csv
  - triage.csv
  - corpus/ir/**
  - out/step4-backend-final-closure-20261122/remediate_points_and_domestic_drq.py
  - out/step4-backend-final-closure-20261122/domestic-drq-verdicts.json

运行方式 (幂等, 二次重跑 SHA-256 零漂移):
  PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 \
      out/step4-backend-final-closure-20261122/remediate_points_and_domestic_drq.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path("/Users/jowang/Downloads/optical-module-research")
POINTS_CSV = ROOT / "points.csv"
TRIAGE_CSV = ROOT / "triage.csv"
DST_IR = ROOT / "corpus" / "ir"
VERDICTS_JSON = ROOT / "out" / "step4-backend-final-closure-20261122" / "domestic-drq-verdicts.json"

SESSION_DATE = "2026-11-22"
CNINFO_QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_SE_DATE = "2026-08-01~2026-11-22"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402

POINTS_COLUMNS = [
    "point_id",
    "公司",
    "cell_id",
    "状态",
    "上市标签",
    "命中引语",
    "锚点URL",
    "检索日期",
    "判定等级",
    "判定会话日期",
]

TRIAGE_COLUMNS = [
    "hit_id",
    "公司",
    "cell_id",
    "来源",
    "引语或线索摘要",
    "处置",
    "理由",
    "会话日期",
]

# Known cninfo stock,orgId pairs for deterministic hisAnnouncement queries
CNINFO_STOCK_MAP = {
    "002384": ("szse", "002384,9900011647"),
    "001267": ("szse", "001267,gssz0000765"),
    "002463": ("szse", "002463,9900013929"),
    "301205": ("szse", "301205,9900052495"),
    "301165": ("szse", "301165,nssc1000760"),
    "603228": ("sse", "603228,9900029802"),
    "000988": ("szse", "000988,gssz0000988"),
    "002428": ("szse", "002428,9900012834"),
    "688003": ("sse", "688003,gfbj0833231"),
    "688135": ("sse", "688135,gfbj0833474"),
    "300120": ("szse", "300120,9900013694"),
}

# Primary cninfo PDFs to archive under corpus/ir/<code>/ with %PDF- check + pdftotext sidecars
CNINFO_PDF_ARCHIVES = [
    {
        "code": "000988",
        "filename": "000988_2026-10-30_2026年10月30日投资者关系活动记录表.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-10-30/1225647394.PDF",
        "drq_id": "DRQ0036",
    },
    {
        "code": "603228",
        "filename": "603228_2026-08-22_2026年半年度报告.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-08-22/1225493416.PDF",
        "drq_id": "DRQ0035",
    },
    {
        "code": "002428",
        "filename": "002428_2026-11-18_关于增加高品质磷化铟单晶片建设项目投资额的公告.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-11-18/1225676124.PDF",
        "drq_id": "DRQ0047",
    },
    {
        "code": "002428",
        "filename": "002428_2026-11-10_2026年11月10日投资者关系活动记录表.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-11-10/1225665965.PDF",
        "drq_id": "DRQ0047",
    },
    {
        "code": "688003",
        "filename": "688003_2026-08-20_2026年半年度报告.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-08-20/1225482975.PDF",
        "drq_id": "DRQ0051",
    },
    {
        "code": "688135",
        "filename": "688135_2026-11-14_关于签署股权收购协议的公告.pdf",
        "url": "https://static.cninfo.com.cn/finalpage/2026-11-14/1225671802.PDF",
        "drq_id": "DRQ0053",
    },
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bytes_if_changed(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def norm_nospace(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


# ---------------------------------------------------------------------------
# Line-number indexing strictly by text.split("\n") (1-based)
# ---------------------------------------------------------------------------
_INDEX_CACHE: dict[str, tuple[list[str], str, list[int]]] = {}


def get_indexed_file(rel_path: str) -> tuple[list[str], str, list[int]]:
    if rel_path not in _INDEX_CACHE:
        full = ROOT / rel_path
        if not full.is_file():
            raise FileNotFoundError(f"Missing local corpus text file: {rel_path}")
        text = full.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        norm_chars: list[str] = []
        char_line: list[int] = []
        for idx, ln in enumerate(lines, 1):
            for ch in ln:
                if not ch.isspace():
                    norm_chars.append(ch)
                    char_line.append(idx)
        _INDEX_CACHE[rel_path] = (lines, "".join(norm_chars), char_line)
    return _INDEX_CACHE[rel_path]


def locate_line_span(
    rel_path: str,
    needles: list[str],
    min_line: int = 1,
    max_line: int = 10**9,
) -> tuple[int, int]:
    """Find tightest 1-based \\n-split line span covering all needles within [min_line, max_line]."""
    lines, norm_text, char_line = get_indexed_file(rel_path)
    spans: list[tuple[int, int]] = []
    for needle in needles:
        nn = norm_nospace(needle)
        if not nn:
            continue
        pos = 0
        matched = False
        while True:
            hit = norm_text.find(nn, pos)
            if hit == -1:
                break
            l1 = char_line[hit]
            l2 = char_line[hit + len(nn) - 1]
            if min_line <= l1 and l2 <= max_line:
                spans.append((l1, l2))
                matched = True
                break
            pos = hit + 1
        if not matched:
            raise ValueError(
                f"Needle {needle!r} not found in {rel_path} within lines {min_line}..{max_line} "
                f"(file has {len(lines)} lines)"
            )
    if not spans:
        raise ValueError(f"Empty needles for {rel_path}")
    return min(s[0] for s in spans), max(s[1] for s in spans)


def fmt_corpus_span(rel_path: str, needles: list[str], min_line: int = 1, max_line: int = 10**9) -> str:
    l1, l2 = locate_line_span(rel_path, needles, min_line, max_line)
    return f"{rel_path}#L{l1}..{l2}"


def append_grade_note_once(grade: str, marker: str, note_body: str, sep: str = "；") -> str:
    """Idempotently append a note inside or onto 判定等级 while preserving admission_path prefix."""
    assert marker in note_body, f"Idempotency marker {marker!r} must appear in {note_body!r}"
    # Self-heal if an earlier pass appended sep + note_body more than once
    dup_tail = f"{sep}{note_body}"
    while grade.count(note_body) > 1 and dup_tail in grade:
        idx = grade.rfind(dup_tail)
        grade = grade[:idx] + grade[idx + len(dup_tail) :]
    if marker in grade:
        return grade
    # If grade has no brackets yet (e.g. 'node_wide_gate' or 'edge_backed'), attach fullwidth parens
    if "（" not in grade and "(" not in grade:
        return f"{grade}（{note_body}）"
    # If grade ends with ')' or '）', insert inside the trailing bracket if balanced, else append after
    if grade.endswith("）") and "（" in grade and grade.rfind("（") > grade.rfind("("):
        return f"{grade[:-1]}{sep}{note_body}）"
    if grade.endswith(")") and "(" in grade and grade.rfind("(") > grade.rfind("（"):
        return f"{grade[:-1]}{sep}{note_body})"
    return f"{grade}{sep}{note_body}"


# ---------------------------------------------------------------------------
# Step A: Archive verified CNINFO PDFs + .pdf.txt sidecars & query cninfo API
# ---------------------------------------------------------------------------
def sync_cninfo_ir_pdfs(session: requests.Session) -> list[dict[str, Any]]:
    archived: list[dict[str, Any]] = []
    for item in CNINFO_PDF_ARCHIVES:
        code = item["code"]
        fname = item["filename"]
        url = item["url"]
        dst_pdf = DST_IR / code / fname
        dst_txt = DST_IR / code / (fname + ".txt")
        dst_pdf.parent.mkdir(parents=True, exist_ok=True)

        if not (dst_pdf.is_file() and dst_pdf.read_bytes().startswith(b"%PDF-")):
            resp = session.get(
                url,
                headers={"Referer": "https://www.cninfo.com.cn/", "User-Agent": "Mozilla/5.0"},
                timeout=45,
            )
            if resp.status_code != 200 or not resp.content.startswith(b"%PDF-"):
                raise RuntimeError(
                    f"Failed to download valid PDF from {url}: HTTP {resp.status_code}, head={resp.content[:12]!r}"
                )
            write_bytes_if_changed(dst_pdf, resp.content)
            time.sleep(0.5)

        if not dst_txt.is_file() or dst_txt.stat().st_size == 0:
            subprocess.run(["pdftotext", "-layout", str(dst_pdf), str(dst_txt)], check=True)

        pdf_rel = str(dst_pdf.relative_to(ROOT))
        txt_rel = str(dst_txt.relative_to(ROOT))
        # Clear cache if newly generated
        _INDEX_CACHE.pop(txt_rel, None)
        txt_lines = dst_txt.read_text(encoding="utf-8", errors="ignore").split("\n")
        archived.append(
            {
                "drq_id": item["drq_id"],
                "code": code,
                "url": url,
                "local_pdf": pdf_rel,
                "local_txt": txt_rel,
                "pdf_sha256": sha256_file(dst_pdf),
                "txt_sha256": sha256_file(dst_txt),
                "txt_line_count_lf": len(txt_lines),
            }
        )
    return archived


def query_cninfo_public_api(
    session: requests.Session,
    existing_verdicts_path: Path,
) -> dict[str, dict[str, Any]]:
    """Polite rate-limited cninfo hisAnnouncement/query check with graceful 403/offline fallback."""
    cached_queries: dict[str, dict[str, Any]] = {}
    if existing_verdicts_path.is_file():
        try:
            prev = json.loads(existing_verdicts_path.read_text(encoding="utf-8"))
            cached_queries = prev.get("cninfo_api_queries") or {}
        except Exception:
            cached_queries = {}

    results: dict[str, dict[str, Any]] = {}
    for code, (column, stock_param) in CNINFO_STOCK_MAP.items():
        # Reuse deterministic 2026-11-22 query snapshot if already verified with HTTP 200
        prev_entry = cached_queries.get(code)
        if (
            prev_entry
            and prev_entry.get("checked_date") == SESSION_DATE
            and prev_entry.get("query_window") == CNINFO_SE_DATE
            and prev_entry.get("fulltext_status") == "ok_json"
            and prev_entry.get("relation_status") == "ok_json"
        ):
            results[code] = prev_entry
            continue

        code_res: dict[str, Any] = {
            "checked_date": SESSION_DATE,
            "query_window": CNINFO_SE_DATE,
            "stock_param": stock_param,
        }
        for tab in ("fulltext", "relation"):
            data = {
                "pageNum": "1",
                "pageSize": "30",
                "column": column,
                "tabName": tab,
                "plate": "",
                "stock": stock_param,
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "seDate": CNINFO_SE_DATE,
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = session.post(
                    CNINFO_QUERY_URL,
                    data=data,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
                        "Origin": "https://www.cninfo.com.cn",
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    timeout=20,
                )
                ct = resp.headers.get("Content-Type", "")
                if resp.status_code != 200 or "json" not in ct.lower():
                    code_res[f"{tab}_status"] = f"skipped_http_{resp.status_code}_or_non_json"
                    code_res[f"{tab}_total"] = None
                    code_res[f"{tab}_top_announcements"] = []
                else:
                    payload = resp.json()
                    anns = payload.get("announcements") or []
                    code_res[f"{tab}_status"] = "ok_json"
                    code_res[f"{tab}_total"] = int(payload.get("totalAnnouncement", len(anns)))
                    top_items = []
                    for a in anns[:8]:
                        ts = a.get("announcementTime", 0)
                        dt_s = time.strftime("%Y-%m-%d", time.localtime(ts / 1000)) if ts else ""
                        title = re.sub(r"<[^>]+>", "", str(a.get("announcementTitle") or "")).strip()
                        adj = str(a.get("adjunctUrl") or "").lstrip("/")
                        top_items.append(
                            {
                                "date": dt_s,
                                "title": title,
                                "url": f"https://static.cninfo.com.cn/{adj}" if adj else "",
                            }
                        )
                    code_res[f"{tab}_top_announcements"] = top_items
            except Exception as exc:
                code_res[f"{tab}_status"] = f"skipped_exception:{type(exc).__name__}"
                code_res[f"{tab}_total"] = None
                code_res[f"{tab}_top_announcements"] = []
            time.sleep(0.5)
        results[code] = code_res
    return results


# ---------------------------------------------------------------------------
# Step B: Task 1 + Task 3 deterministic remediation of points.csv
# ---------------------------------------------------------------------------
def remediate_points_csv() -> dict[str, Any]:
    with POINTS_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == POINTS_COLUMNS, f"Unexpected points.csv columns: {reader.fieldnames}"
        rows = list(reader)

    orig_quotes = {r["point_id"]: r["命中引语"] for r in rows if r["point_id"] != "P277"}
    by_id = {r["point_id"]: r for r in rows}
    assert by_id["P074"]["检索日期"] == "2026-11-21", "Baseline P074 检索日期 must be 2026-11-21"

    # 1. Pure URL unwraps (8 Markdown [title](url) + 3 US SEC 10-K + P042/P043/P058/P059)
    markdown_unwraps = {
        "P005": ("https://static.cninfo.com.cn/finalpage/2026-03-28/1225041594.PDF", "原锚注：2025年年度报告"),
        "P011": ("https://static.cninfo.com.cn/finalpage/2024-04-26/1219832754.PDF", "原锚注：2023年年度报告"),
        "P015": ("https://static.cninfo.com.cn/finalpage/2024-04-03/1219506244.PDF", "原锚注：2023年年度报告"),
        "P021": ("https://static.cninfo.com.cn/finalpage/2025-03-29/1222948563.PDF", "原锚注：2024年年度报告"),
        "P023": ("https://static.cninfo.com.cn/finalpage/2020-08-03/1208119960.PDF", "原锚注：2020年向特定对象发行股票募集说明书"),
        "P024": ("https://static.cninfo.com.cn/finalpage/2020-08-03/1208119960.PDF", "原锚注：2020年向特定对象发行股票募集说明书"),
        "P030": ("https://static.cninfo.com.cn/finalpage/2026-04-28/1225214766.PDF", "原锚注：2025年年度报告"),
        "P033": ("https://static.cninfo.com.cn/finalpage/2026-04-29/1225228204.PDF", "原锚注：2025年年度报告"),
    }
    for pid, (clean_url, note) in markdown_unwraps.items():
        r = by_id[pid]
        r["锚点URL"] = clean_url
        r["判定等级"] = append_grade_note_once(r["判定等级"], "原锚注：", note)

    # US SEC 10-K items: P001 (Fabrinet), P003 (Marvell), P020 (Broadcom)
    by_id["P001"]["锚点URL"] = "https://www.sec.gov/Archives/edgar/data/1408710/000140871025000039/fn-20250627.htm"
    by_id["P001"]["判定等级"] = append_grade_note_once(
        by_id["P001"]["判定等级"],
        "Fabrinet FY2025 10-K",
        "原注：发行人自述 Fabrinet FY2025 10-K，同E001 SEC原件及本地 corpus/legacy-input/fn/fn-20250627.htm",
    )

    by_id["P003"]["锚点URL"] = "https://www.sec.gov/Archives/edgar/data/1835632/000183563226000011/mrvl-20260131.htm"
    by_id["P003"]["判定等级"] = append_grade_note_once(
        by_id["P003"]["判定等级"],
        "mrvl-20260131.htm",
        "原注：FY2026 10-K产品段 sec.gov mrvl-20260131.htm，补锚2026-07-24",
    )

    by_id["P020"]["锚点URL"] = "https://www.sec.gov/Archives/edgar/data/1730168/000173016825000121/avgo-20251102.htm"
    by_id["P020"]["判定等级"] = append_grade_note_once(
        by_id["P020"]["判定等级"],
        "avgo-20251102.htm",
        "原注：FY2025 10-K产品段 sec.gov avgo-20251102.htm，共识结构层补锚2026-07-24",
    )

    # P042 & P043 永鼎股份 cross_reference -> pure cninfo URL + verified local #L508..515 note
    yd_span = fmt_corpus_span(
        "corpus/annual/600105/600105/600105__em_永鼎股份_em__2025_永鼎股份2025年年度报告.pdf.txt",
        ["芯片-光器件-MPO", "无源光器件：涵盖阵列波导光栅（AWG）", "数据中心光模块关键组件"],
        500,
        525,
    )
    for pid in ("P042", "P043"):
        by_id[pid]["锚点URL"] = "https://static.cninfo.com.cn/finalpage/2026-04-21/1225133679.PDF"
        by_id[pid]["判定等级"] = append_grade_note_once(
            by_id[pid]["判定等级"],
            "同P041",
            f"同P041，2025年年度报告本地全文见 {yd_span}",
        )

    # P058 福晶科技 -> pure cninfo URL + verified local #L289..293 note
    fj_span = fmt_corpus_span(
        "corpus/annual/002222/002222/002222__em_福晶科技_em__2025_2025年年度报告.pdf.txt",
        ["精密光学元件涵盖窗口片、反射镜、球面透镜、柱面透镜、非球面透镜", "光通信波分复用器"],
        285,
        296,
    )
    by_id["P058"]["锚点URL"] = "https://static.cninfo.com.cn/finalpage/2026-04-29/1225227139.pdf"
    by_id["P058"]["判定等级"] = append_grade_note_once(
        by_id["P058"]["判定等级"],
        "不宣称其透镜专供光模块",
        f"部分证实；披露方产品列：2025年年度报告，不宣称其透镜专供光模块，本地全文见 {fj_span}，历史T1叶格补强批次",
    )

    # P059 罗博特科/ficonTEC -> leading clickable URL + verified corpus/ir path
    by_id["P059"]["锚点URL"] = (
        "https://static.cninfo.com.cn/finalpage/2026-08-26/1225507370.PDF#page=12；"
        "corpus/ir/300757/300757_2026-10-29_300757罗博特科投资者关系管理信息20261029.pdf "
        "（原注：发行人披露及BOM词表E011/E012标注CPO耦合设备；C35内容台账补充基于硅光/CPO研发激光辅助键合、倒装热压等先进封装工艺）"
    )

    # 2. Local annual report & prospectus rows -> corpus/<path>#L<start>..<end> （原注：...）
    CG_PROSP = "corpus/legacy-input/v16/prospectus/688048_长光华芯_招股说明书_注册稿.txt"
    SJ_PROSP = "corpus/legacy-input/v16/prospectus/688313_仕佳光子_招股说明书_注册稿.txt"
    YJ_PROSP = "corpus/legacy-input/v16/prospectus/688498_源杰科技_招股说明书_注册稿.txt"

    local_single_specs: dict[str, tuple[str, list[str], int, int, str]] = {
        # 14 S0a 2025 annual report rows
        "P009": (
            "corpus/annual/002384/002384/002384__em_东山精密_em__2025_2025年年度报告.pdf.txt",
            ["索尔思光电拥有覆盖磷化铟衬底、外延材料至光芯片的全流程研发与工艺体系，技术壁垒持续夯实"],
            1940,
            1955,
            "S0a本地扫描2025年报 002384__em_东山精密_em__2025_2025年年度报告.pdf",
        ),
        "P010": (
            "corpus/annual/301183/301183/301183__em_东田微_em__2025_2025年年度报告.pdf.txt",
            ["已完成光隔离器、WDM滤光片及组件等多类产品的布局", "在光隔离器、WDM滤光片等高端器件领域迅速跻身稀缺供应商行列"],
            420,
            440,
            "S0a本地扫描2025年报 301183__em_东田微_em__2025_2025年年度报告.pdf",
        ),
        "P014": (
            "corpus/annual/688807/688807/688807__em_优迅股份_em__2025_优迅股份：2025年年度报告.pdf.txt",
            ["优迅股份作为国内光通信电芯片领域的领军企业", "专注于光通信前端收发电芯片的研发、设计与销售", "高带宽、低噪声、宽动态跨阻放大"],
            650,
            1240,
            "S0a本地扫描2025年报 688807__em_优迅股份_em__2025_优迅股份：2025年年度报告.pdf，全文扩看核实",
        ),
        "P019": (
            "corpus/annual/603936/603936/603936__em_博敏电子_em__2025_博敏电子2025年年度报告.pdf.txt",
            ["已实现400G、800G光模块PCB批量供货，同时积极推动1.6T光模块PCB量产工作"],
            635,
            650,
            "S0a本地扫描2025年报 603936__em_博敏电子_em__2025_博敏电子2025年年度报告.pdf",
        ),
        "P028": (
            "corpus/annual/301479/301479/301479__em_弘景光电_em__2025_2025年年度报告.pdf.txt",
            ["光学设计、精密制造等方面的优势，成功开发了多款光通信中的光无源器件", "非球面透镜、光纤阵列组件等"],
            758,
            768,
            "S0a本地扫描2025年报 301479__em_弘景光电_em__2025_2025年年度报告.pdf",
        ),
        "P039": (
            "corpus/annual/001267/001267/001267__em_汇绿生态_em__2025_2025年年度报告.pdf.txt",
            ["光模块业务的营业收入比重大于50%", "武汉钧恒为公司的控股子公司，武汉钧恒2012年成立"],
            395,
            405,
            "S0a本地扫描2025年报 001267__em_汇绿生态_em__2025_2025年年度报告.pdf 管理层讨论与分析·一、报告期内公司从事的主要业务",
        ),
        "P040": (
            "corpus/annual/001267/001267/001267__em_汇绿生态_em__2025_2025年年度报告.pdf.txt",
            ["光模块由光器件、功能电路和光接口等构成", "通过跨阻放大器后将此电流信号转换成电压信号"],
            405,
            420,
            "S0a本地扫描2025年报 001267__em_汇绿生态_em__2025_2025年年度报告.pdf",
        ),
        "P041": (
            "corpus/annual/600105/600105/600105__em_永鼎股份_em__2025_永鼎股份2025年年度报告.pdf.txt",
            ["芯片-光器件-MPO", "无源光器件：涵盖阵列波导光栅（AWG）", "数据中心光模块关键组件"],
            505,
            520,
            "S0a本地扫描2025年报 600105__em_永鼎股份_em__2025_永鼎股份2025年年度报告.pdf",
        ),
        "P056": (
            "corpus/annual/688183/688183/688183__em_生益电子_em__2025_生益电子2025年年度报告.pdf.txt",
            ["研究开发高速光模块PCB产品", "PCB产品，并实现产业化"],
            998,
            1008,
            "S0a本地扫描2025年报 688183__em_生益电子_em__2025_生益电子2025年年度报告.pdf",
        ),
        "P057": (
            "corpus/annual/600183/600183/600183__em_生益科技_em__2025_生益科技2025年年度报告.pdf.txt",
            ["研究开发高速光模块PCB产品制作工艺技术，攻克技术难点，并实现产业化"],
            908,
            916,
            "S0a本地扫描2025年报 600183__em_生益科技_em__2025_生益科技2025年年度报告.pdf",
        ),
        "P060": (
            "corpus/annual/301205/301205/301205__em_联特科技_em__2025_2025年年度报告.pdf.txt",
            ["公司生产工序包括光芯片集成（COC）、光器件及光模块的生产", "光器件的生产工序包括软板焊接、元件贴装、COC贴装、金丝键合、耦合、高低温循环、测试、检验等"],
            702,
            710,
            "S0a本地扫描2025年报 301205__em_联特科技_em__2025_2025年年度报告.pdf",
        ),
        "P065": (
            "corpus/annual/688655/688655/688655__em_迅捷兴_em__2025_2025年年度报告.pdf.txt",
            ["公司完成任意互联HDI结构的800G光模块PCB、1.6T光模块PCB技术研发", "400G光模块PCB生产工艺技术自主研发"],
            875,
            1138,
            "S0a本地扫描2025年报 688655__em_迅捷兴_em__2025_2025年年度报告.pdf",
        ),
        "P068": (
            "corpus/annual/688143/688143/688143__em_长盈通_em__2025_2025年年度报告.pdf.txt",
            ["AWG器件：CWDM及LANWDMAWG器件具备小尺寸", "低损耗和低成本特征"],
            1480,
            1486,
            "S0a本地扫描2025年报 688143__em_长盈通_em__2025_2025年年度报告.pdf",
        ),
        "P069": (
            "corpus/annual/688143/688143/688143__em_长盈通_em__2025_2025年年度报告.pdf.txt",
            ["公司以发行股份及支付现金方式并购", "快速构建起光模块用无源内连光器件和光纤阵列器件的研发、生产、销售能力"],
            1796,
            1803,
            "S0a本地扫描2025年报 688143__em_长盈通_em__2025_2025年年度报告.pdf",
        ),
        # 5 issuer-self rows (P016, P052, P066, P159, P160)
        "P016": (
            "corpus/legacy-input/gx/002281/gx_2023.txt",
            ["光收发模块、有源光缆、光放大器、波长管理器件、光通信器件、子系统等"],
            434,
            440,
            "发行人自述：光迅科技2023年年度报告",
        ),
        "P052": (
            YJ_PROSP,
            ["光芯片的研发、设计、生产与销售"],
            250,
            258,
            "发行人自述：源杰科技招股书主营句",
        ),
        "P066": (
            CG_PROSP,
            ["半导体激光芯片、器件及模块等激光行业核心元器件的研发、生产与销售"],
            7275,
            7280,
            "发行人自述：长光华芯招股书；CGHX内容台账补充光纤耦合模块工艺流程含快轴/慢轴准直透镜组装，自用于封装非透镜生产者",
        ),
        "P159": (
            "corpus/annual/688205/688205/688205_德科立_2025年年度报告.pdf.txt",
            ["电信传输类光收发模块包括从155M、1.25G、10G、100G到400G及以上速率相干和非相干光收发模块，支持10km、40km、80km及以上传输距离"],
            500,
            507,
            "德科立2025年年度报告本地扫描",
        ),
        "P160": (
            "corpus/annual/688205/688205/688205_德科立_2025年年度报告.pdf.txt",
            ["宽带接入产品有GPONOLT、COMBOPON及BOSA等。无线接入产品主要包括前传子系统及各种10G、25G灰光和彩光光收发模块"],
            505,
            512,
            "德科立2025年年度报告本地扫描",
        ),
        # Single-prospectus supplier / outsource / peer rows (27 rows; P018 & P032 dual-prospectus below)
        "P002": (CG_PROSP, ["MaruwaCo.,Ltd热沉"], 8305, 8325, "披露方产品列：长光华芯招股书供应商表"),
        "P004": (SJ_PROSP, ["OharaQuartzCo.,Ltd.石英片"], 8283, 8289, "披露方产品列：仕佳光子招股书供应商表"),
        "P006": (YJ_PROSP, ["显影液、增粘", "上海函泰电子科技有限公司", "剂、光刻胶等"], 6618, 6623, "披露方产品列：源杰招股书供应商表"),
        "P007": (SJ_PROSP, ["上海普恩化工有限公司EVA树脂"], 8269, 8273, "披露方产品列：仕佳光子招股书供应商表"),
        "P008": (SJ_PROSP, ["上海景仓通信技术有限公司光纤"], 8275, 8279, "披露方产品列：仕佳光子招股书供应商表"),
        "P012": (CG_PROSP, ["京瓷（中国）商贸有限公司热沉"], 8315, 8332, "披露方产品列：长光华芯招股书供应商表"),
        "P017": (YJ_PROSP, ["北京康特睿科光电科技有限公司芯片封装"], 6700, 6710, "披露方产品列：源杰招股书委托加工表"),
        "P022": (YJ_PROSP, ["大阳日酸特殊气体（上海）磷化氢、砷化", "有限公司氢"], 6644, 6648, "披露方产品列：源杰招股书供应商表"),
        "P027": (YJ_PROSP, ["广东瑞谷光网通信股份有限公司芯片封装"], 6698, 6706, "披露方产品列：源杰招股书委托加工表"),
        "P029": (SJ_PROSP, ["成都中住光纤有限公司光纤"], 8268, 8276, "披露方产品列：仕佳光子招股书供应商表"),
        "P034": (SJ_PROSP, ["杜邦及其关联方芳纶纱"], 8265, 8278, "披露方产品列：仕佳光子招股书供应商表"),
        "P035": (YJ_PROSP, ["桂林芯飞光电子科技有限公司芯片封装"], 6672, 6686, "披露方产品列：源杰招股书委托加工表"),
        "P037": (YJ_PROSP, ["武汉云岭光电有限公司成立于2018年", "光通信用激光器和探测器芯片"], 5543, 5548, "同业描述：源杰招股书同业段"),
        "P038": (
            YJ_PROSP,
            ["武汉昱升光器件有限公司芯片封装"],
            6700,
            6711,
            "披露方产品列：源杰招股书委托加工表；entity-evidence-q3工商统一社会信用代码一致确认同一法人更名",
        ),
        "P044": (
            YJ_PROSP,
            ["磷烷、三甲基", "江苏南大光电材料股份有限", "铟、三甲基镓", "公司"],
            6621,
            6627,
            "披露方产品列：源杰招股书供应商表；pilot-s0a三甲基铟检索确认其为核心生产主体",
        ),
        "P045": (YJ_PROSP, ["泛孟新材料（上海）有限公异丙醇、光刻", "司胶去除液"], 6605, 6609, "披露方产品列：源杰招股书供应商表"),
        "P046": (CG_PROSP, ["泰库尼思科电子（苏州）有限公司热沉"], 8320, 8341, "披露方产品列：长光华芯招股书供应商表"),
        "P047": (SJ_PROSP, ["洛阳中超新材料股份有限公司氢氧化铝"], 8267, 8280, "披露方产品列：仕佳光子招股书供应商表"),
        "P048": (YJ_PROSP, ["深圳市东飞凌科技有限公司芯片封装"], 6672, 6685, "披露方产品列：源杰招股书委托加工表"),
        "P049": (YJ_PROSP, ["深圳市力子光电科技有限公司芯片封装"], 6679, 6697, "披露方产品列：源杰招股书委托加工表"),
        "P050": (YJ_PROSP, ["深圳市路维光电股份有限公", "光刻掩模板", "司"], 6594, 6598, "披露方产品列：源杰招股书供应商表"),
        "P051": (YJ_PROSP, ["湖北安一辰光电科技有限公司芯片封装"], 6706, 6709, "披露方产品列：源杰招股书委托加工表"),
        "P053": (CG_PROSP, ["炬光（东莞）微光学有限公司光学件"], 8309, 8321, "半锚；披露方产品列：长光华芯招股书外协采购表，未专锚透镜/准直透镜字样"),
        "P062": (YJ_PROSP, ["芯思杰技术（深圳）股份有限公司芯片封装"], 6693, 6696, "披露方产品列：源杰招股书委托加工表"),
        "P063": (YJ_PROSP, ["氮气、氢气、", "西安卫光气体有限公司", "氧气、氩气等"], 6638, 6642, "披露方产品列：源杰招股书供应商表"),
        "P064": (YJ_PROSP, ["诺力昂化学品（宁波）有限", "金属有机物", "公司"], 6591, 6595, "披露方产品列：源杰招股书供应商表"),
        "P070": (YJ_PROSP, ["陕西兴化集团有限责任公司氢气、氮气"], 6608, 6611, "披露方产品列：源杰招股书供应商表"),
    }

    for pid, (rel, needles, mn, mx, old_note) in local_single_specs.items():
        span_ref = fmt_corpus_span(rel, needles, mn, mx)
        by_id[pid]["锚点URL"] = f"{span_ref} （原注：{old_note}）"

    # Dual-prospectus rows: P018 (北京通美晶体) & P032 (有研亿金新材料有限公司)
    p018_yj = fmt_corpus_span(YJ_PROSP, ["北京通美晶体技术有限公司衬底"], 6584, 6601)
    p018_cg = fmt_corpus_span(CG_PROSP, ["北京通美晶体技术股份有限公司衬底"], 8305, 8308)
    by_id["P018"]["锚点URL"] = (
        f"{p018_yj}；{p018_cg} "
        "（原注：披露方产品列：源杰/长光华芯招股书供应商表；另pilot-s0a确认其现行InP substrate供货 AXT 2026-06-17 Form 8-K）"
    )

    p032_yj = fmt_corpus_span(YJ_PROSP, ["金靶、铂靶、", "有研亿金新材料有限公司", "金锗靶"], 6602, 6606)
    p032_cg = fmt_corpus_span(CG_PROSP, ["有研亿金新材料有限公司"], 8311, 8314)
    by_id["P032"]["锚点URL"] = f"{p032_yj}；{p032_cg} （原注：披露方产品列：源杰/长光华芯招股书供应商表）"

    # Normalize P013, P025, P026 so they also start cleanly with corpus/<path>#Lx..y
    p013_sj_prosp = fmt_corpus_span(SJ_PROSP, ["公司主要产品包括光芯片及器件、室内光缆、线缆材料等"], 5246, 5250)
    p013_sj_2024 = fmt_corpus_span(
        "corpus/annual-2024/688313/688313__em_仕佳光子_em__2024_2024年年度报告.pdf.txt",
        ["应用于400G和800G光模块的CWDM/LANWDMAWG组件大批量出货"],
        546,
        550,
    )
    by_id["P013"]["锚点URL"] = (
        f"{p013_sj_prosp}；{p013_sj_2024}；corpus/content_ledger/content_ledger.csv#SJZ24 "
        "（原注：发行人自述产品构成条目升级及2024年报CWDM/LAN WDM AWG大批量出货与60通道100GHz AWG相干批量出货；供货边E110）"
    )

    p025_tcg = fmt_corpus_span(
        "corpus/annual-2024/300570/300570__em_太辰光_em__2024_2024年年度报告.pdf.txt",
        ["陶瓷插芯、MT插芯保证光纤定位"],
        445,
        448,
    )
    by_id["P025"]["锚点URL"] = (
        f"{p025_tcg}；corpus/content_ledger/content_ledger.csv#TCG24-09 "
        "（原注：发行人自述2024年报产品应用表直证，升级前为仕佳光子招股书同业描述）"
    )

    p026_tcg = fmt_corpus_span(
        "corpus/annual-2024/300570/300570__em_太辰光_em__2024_2024年年度报告.pdf.txt",
        ["AWG芯片开发持续进行中产品实现批量产销"],
        859,
        862,
    )
    by_id["P026"]["锚点URL"] = (
        f"{p026_tcg}；corpus/content_ledger/content_ledger.csv#TCG24-19 "
        "（原注：2024年报研发投入表在研阶段登记，不构成生产中锚，仅作技术布局线索）"
    )

    # -----------------------------------------------------------------------
    # 3. Task 3 Domestic DRQ primary-source boundary updates on points.csv
    # -----------------------------------------------------------------------
    # DRQ0020: 东山精密 (002384) 2026-11-02 IR Q3/Q8/Q9 -> P130 & P133
    ds_ir_q3 = fmt_corpus_span(
        "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt",
        ["问题3：公司光芯片明后年外售的规划以及后续CW产品的销售规划如何", "公司今年已有小批量光芯片外售，为优先保障自用，尚未大规模对外销售"],
        53,
        62,
    )
    ds_ir_q89 = fmt_corpus_span(
        "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt",
        ["公司今年三季度1.6T产品主要做客户测试验证，四季度起进入相对批量出货", "公司CPO产品已完成内部可靠性验证，正在做后端封装，后续将向客户送样"],
        102,
        122,
    )
    by_id["P130"]["锚点URL"] = f"https://static.cninfo.com.cn/finalpage/2026-04-22/1225139318.PDF；{ds_ir_q3}"
    by_id["P130"]["判定等级"] = append_grade_note_once(
        by_id["P130"]["判定等级"],
        "2026-11-02投关第3问核实",
        f"2026-11-02投关第3问核实({ds_ir_q3})：虽提问涉及CW产品销售规划，公司回复仅泛称\"公司今年已有小批量光芯片外售，为优先保障自用，尚未大规模对外销售\"，未细分外售芯片系CW/EML/DFB且未具名外部客户，严禁将外售泛称直接缩窄等同于P130 CW外售实绩",
    )

    by_id["P133"]["锚点URL"] = f"https://static.cninfo.com.cn/finalpage/2026-04-22/1225139318.PDF；{ds_ir_q89}"
    by_id["P133"]["判定等级"] = append_grade_note_once(
        by_id["P133"]["判定等级"],
        "2026-11-02投关第8/9问核实",
        f"2026-11-02投关第8/9问核实({ds_ir_q89})：2026Q3 1.6T主要做客户测试验证、Q4起进入相对批量出货；CPO产品已完成内部可靠性验证正做后端封装、后续向客户送样(节奏取决于客户)，NPO仍处定制研发探索",
    )

    # DRQ0031: 汇绿生态/武汉钧恒 (001267) 2026-11-03 & 11-06 IR -> P039
    hl_p039_ann = fmt_corpus_span(
        "corpus/annual/001267/001267/001267__em_汇绿生态_em__2025_2025年年度报告.pdf.txt",
        ["光模块业务的营业收入比重大于50%", "武汉钧恒为公司的控股子公司，武汉钧恒2012年成立"],
        395,
        405,
    )
    hl_ir_1103 = fmt_corpus_span(
        "corpus/ir/001267/001267_2026-11-03_001267汇绿生态投资者关系管理信息20261103.pdf.txt",
        ["其中400G、800G产品为当前主力出货产品", "武汉本部约300万支/年、2025年年底投产的鄂州工厂一期约150万支/年", "武汉区域预计合计达350万支高速率光模块年产能"],
        51,
        78,
    )
    hl_ir_1106 = fmt_corpus_span(
        "corpus/ir/001267/001267_2026-11-06_001267汇绿生态投资者关系管理信息20261106.pdf.txt",
        ["钧恒科技产品结构已调整为以400G至800G为主，其中800G正在上量", "NPO是钧恒科技在高速率光互联方向的前沿技术布局，目前处于新产品导入早期阶段"],
        37,
        50,
    )
    by_id["P039"]["锚点URL"] = (
        f"{hl_p039_ann}；{hl_ir_1103}；{hl_ir_1106} "
        "（原注：S0a本地扫描2025年报 001267__em_汇绿生态_em__2025_2025年年度报告.pdf 管理层讨论与分析·一、报告期内公司从事的主要业务）"
    )
    by_id["P039"]["判定等级"] = append_grade_note_once(
        by_id["P039"]["判定等级"],
        "2026-11-03(编号2026-008)",
        "2026-11-03(编号2026-008)及11-06(编号2026-009)投关核实：严格拆分已投产产能(武汉本部约300万支/年+2025年底投产鄂州一期约150万支/年+2026年4月底投产马来西亚工厂约100万-150万支/年)与远期扩建规划(拟总投资3.09亿元设研发生产基地，建成后现有150万支产线升级+新增200万支高速率产线，武汉区域预计合计350万支/年且旧厂房停用)；当前以400G/800G为主力出货(800G正上量，未披露精确分速率占比)，NPO处新产品导入早期阶段，剩余49%股权收购仍在交易所审核中",
    )

    # DRQ0033: 联特科技 (301205) 2026-10-28 IR -> P174
    lt_ir_1028 = fmt_corpus_span(
        "corpus/ir/301205/301205_2026-10-28_301205联特科技投资者关系管理信息20261028.pdf.txt",
        ["公司的800G产品已经实现批量发货，发货量每个季度都环比提升", "已经成功送样给北美大型csp客户", "已获一些客户验证通过"],
        55,
        76,
    )
    by_id["P174"]["锚点URL"] = f"https://static.cninfo.com.cn/finalpage/2026-04-29/1225239616.pdf；{lt_ir_1028}"
    by_id["P174"]["判定等级"] = append_grade_note_once(
        by_id["P174"]["判定等级"],
        "2026-10-28投关(编号2026-003",
        f"2026-10-28投关(编号2026-003,{lt_ir_1028})核实：800G产品已实现批量发货且季度环比提升(驱动前三季度营收12.74亿元,+50.57%)；1.6T涵盖FRO/LRO/LPO多元方案，已成功送样北美大型CSP客户并获部分客户验证通过及实机演示1.6T LPO(严格区分800G批量发货与1.6T送样验证时态)；NPO预计2028年落地",
    )

    # DRQ0034: 锐捷网络 (301165) 2026-10-21 IR -> P187
    rj_ir_1021_a = fmt_corpus_span(
        "corpus/ir/301165/301165_2026-10-21_2026年10月19日至10月21日投资者关系活动记录表.pdf.txt",
        ["LPO已规模量产交付400G产品，1.6TLPO已推出原型样品", "3.2TNPO模组已推出原型样品"],
        134,
        139,
    )
    rj_ir_1021_q9 = fmt_corpus_span(
        "corpus/ir/301165/301165_2026-10-21_2026年10月19日至10月21日投资者关系活动记录表.pdf.txt",
        ["公司LPO光模块产品均搭配自有交换机完成适配后销售，目前出货量较大的是400GLPO产品，与400G交换机搭配销售，不作为通用配件单独销售"],
        276,
        287,
    )
    by_id["P187"]["锚点URL"] = (
        f"corpus/qa/301165/qa.jsonl#indexId=2301891159369191424；{rj_ir_1021_a}；{rj_ir_1021_q9} "
        "（原注：irm.cninfo.com.cn互动易准披露渠道及2026-10-21投关纪要）"
    )
    by_id["P187"]["判定等级"] = append_grade_note_once(
        by_id["P187"]["判定等级"],
        "2026-10-21投关(编号2026-04",
        f"2026-10-21投关(编号2026-04,{rj_ir_1021_q9})核实并纠偏：目前规模量产交付仅限400G LPO(1.6T LPO与3.2T NPO模组为原型样品，800G/1.6T LPO属下一步推出计划)；且公司LPO光模块均搭配自有交换机联合测试适配后捆绑销售，\"不作为通用配件单独销售\"，严禁混同于独立对外销售的第三方光模块厂口径",
    )

    # DRQ0035: 景旺电子 (603228) 2026半年报 p.11 精确页码与行号核查 -> P031
    jw_h1_p11 = fmt_corpus_span(
        "corpus/ir/603228/603228_2026-08-22_2026年半年度报告.pdf.txt",
        ["随着公司新增mSAP产线安装调试完成，大批量产能落地，报告期内公司已批量交付800G、1.6T光模块PCB，2026年二季度，800G及以上速率光模块收入环比增长近1500%"],
        491,
        497,
    )
    # Clean raw markdown link inside P031["判定等级"] if present, then append DRQ0035 verified note
    by_id["P031"]["判定等级"] = by_id["P031"]["判定等级"].replace(
        "[2024年年度报告](https://static.cninfo.com.cn/finalpage/2025-04-29/1223377812.PDF)",
        "2024年年度报告 https://static.cninfo.com.cn/finalpage/2025-04-29/1223377812.PDF",
    )
    by_id["P031"]["判定等级"] = append_grade_note_once(
        by_id["P031"]["判定等级"],
        "DRQ0035原件核实",
        f"DRQ0035原件核实({jw_h1_p11})：确认2026半年报第11页逐字载明新增mSAP产线落地并批量交付800G、1.6T光模块PCB(2026Q2 800G及以上收入环比增长近1500%)，衔接10-13/16上证e互动(CLG0624/CLG0625)珠海金湾基地在手订单饱满口径，同时彻底剥离同期S.5548法案二手传闻",
        sep="。",
    )

    # DRQ0036: 华工科技 (000988) 2026-10-30 投关原件核查 -> P209 (preserve all Step 3 asserted substrings!)
    hg_ir_1030 = fmt_corpus_span(
        "corpus/ir/000988/000988_2026-10-30_2026年10月30日投资者关系活动记录表.pdf.txt",
        ["800GLPO产品已在下半年开始提量交付，目前泰国工厂月出货量约10万只", "1.6TLPO系列产品正在快速送样测试", "已在北美获得一家知名客户的6.4TNPO产品供应商资格"],
        168,
        205,
    )
    by_id["P209"]["判定等级"] = append_grade_note_once(
        by_id["P209"]["判定等级"],
        "DRQ0036法定投关原件核实",
        f"DRQ0036法定投关原件核实({hg_ir_1030})：巨潮正式披露的2026-10-30投关表(编号2026-04)p.6第2问确载\"目前泰国工厂月出货量约10万只\"及1.6T LPO快速送样测试(预计2027Q1完成测试)、p.7第5问获北美知名客户6.4T NPO供应商资格并预计2027年7月批量交付；全文零提及\"原产地实质性改变/关税豁免\"，外部合规推演严格剔除",
        sep="。",
    )

    # DRQ0047: 云南锗业 (002428) 2026-11-18 增资公告 2026-057 & 2026-11-10 投关 -> P202
    yng_ann_1118 = fmt_corpus_span(
        "corpus/ir/002428/002428_2026-11-18_关于增加高品质磷化铟单晶片建设项目投资额的公告.pdf.txt",
        ["同意将“高品质磷化铟单晶片建设项目”的总投资额增加至26,999万元", "项目总投资26,999万元（调整前为18,856万元）"],
        17,
        48,
    )
    yng_ir_1110 = fmt_corpus_span(
        "corpus/ir/002428/002428_2026-11-10_2026年11月10日投资者关系活动记录表.pdf.txt",
        ["最终达到年产45万片（折合4英寸）高品质磷化铟单晶片的产能", "云南鑫耀6英寸磷化铟晶片在手订单约1.3万片，金额合计约3亿元人民币"],
        31,
        58,
    )
    by_id["P202"]["锚点URL"] = (
        "https://static.cninfo.com.cn/finalpage/2026-04-23/1225152695.PDF；"
        "https://static.cninfo.com.cn/finalpage/2026-11-18/1225676124.PDF；"
        f"{yng_ann_1118}；{yng_ir_1110}"
    )
    by_id["P202"]["判定等级"] = append_grade_note_once(
        by_id["P202"]["判定等级"],
        "2026-11-18正式公告2026-057",
        f"2026-11-18正式公告2026-057({yng_ann_1118})核实：第九届董事会第九次会议批准将云南鑫耀\"高品质磷化铟单晶片建设项目\"总投资由18,856万元调增8,143万元至精确值26,999万元(固定资产投资23,393万元+铺底流动资金3,606万元，纠正媒体约数2.7亿元)，新增设备294台(套)提高大尺寸产出占比，扩建后目标总产能45万片/年(折合4英寸，在建扩产与现有15万片/年产能分列)；2026-11-10投关({yng_ir_1110})披露6英寸磷化铟晶片在手订单约1.3万片(约3亿元)，部分已获出口许可持续交付",
    )

    # DRQ0051: 天准科技 (688003) 2026半年报 p.14 光模块/CPO在线AOI实证 -> Upsert P277
    tz_h1_p14 = fmt_corpus_span(
        "corpus/ir/688003/688003_2026-08-20_2026年半年度报告.pdf.txt",
        [
            "在光通信领域，天准为800G、1.6T等光模块提供精密量检测装备，覆盖了光模块领域大部分客户，长期服务于中际旭创、新易盛、天孚通信等头部客户",
            "2026年，天准获得工业富联CPO量产项目的在线AOI检测设备首批小批量订单，部分设备已交付客户现场",
        ],
        679,
        684,
    )
    tz_y25_p18 = fmt_corpus_span(
        "corpus/annual/688003/688003/688003__em_天准科技_em__2025_2025年年度报告.pdf.txt",
        ["天准为光通讯器件及光通讯模组提供精密量检测装备，覆盖了光通讯领域大部分客户，包括中际旭创、新易盛、天孚通信等"],
        815,
        818,
    )
    p277_row = {
        "point_id": "P277",
        "公司": "天准科技",
        "cell_id": "EQ6",
        "状态": "生产中",
        "上市标签": "A股",
        "命中引语": (
            "\"在光通信领域，天准为 800G、1.6T 等光模块提供精密量检测装备，覆盖了光模块领域大部分客户，"
            "长期服务于中际旭创、新易盛、天孚通信等头部客户。2026 年，天准获得工业富联 CPO 量产项目的在线 "
            "AOI 检测设备首批小批量订单，部分设备已交付客户现场\""
        ),
        "锚点URL": "https://static.cninfo.com.cn/finalpage/2026-08-20/1225482975.PDF#page=14",
        "检索日期": SESSION_DATE,
        "判定等级": (
            f"判定闸-生产中（2026半年报p.14即{tz_h1_p14}及2025年报p.18即{tz_y25_p18}逐字核验："
            "800G/1.6T光模块精密量检测装备长期服务中际旭创、新易盛、天孚通信等头部客户，且2026年获工业富联CPO量产项目"
            "在线AOI检测设备首批小批量订单并部分交付客户现场，满足KN001准入①光通信专属应用与具名客户双重实证；"
            "注记：CPO在线AOI属首批小批量交付阶段，与800G/1.6T常规光模块检测分列，不单列专项收入）"
        ),
        "判定会话日期": SESSION_DATE,
    }
    if "P277" in by_id:
        by_id["P277"].update(p277_row)
    else:
        rows.append(p277_row)
        by_id["P277"] = p277_row

    # -----------------------------------------------------------------------
    # 4. Strict Gates on points.csv before writing
    # -----------------------------------------------------------------------
    # Gate A: Zero mutation of existing 命中引语 and P074 检索日期
    for pid, expected_q in orig_quotes.items():
        if by_id[pid]["命中引语"] != expected_q:
            raise AssertionError(f"Forbidden mutation of 命中引语 in {pid}!")
    if by_id["P074"]["检索日期"] != "2026-11-21":
        raise AssertionError(f"Forbidden mutation of P074 检索日期: {by_id['P074']['检索日期']}")

    # Gate B: Zero bare-text anchors, zero Markdown [title](url) anchors, 100% leading http(s) or corpus/
    bare_rows: list[str] = []
    md_rows: list[str] = []
    corpus_line_verified = 0
    for r in rows:
        pid = r["point_id"]
        for col, val in r.items():
            if "\n" in (val or "") or "\r" in (val or ""):
                raise ValueError(f"Embedded newline in points.csv {pid}.{col}")
        a = (r.get("锚点URL") or "").strip()
        if not a.startswith(("http://", "https://", "corpus/")):
            bare_rows.append(pid)
        if re.search(r"\[[^\]]+\]\(https?://", a):
            md_rows.append(pid)
        for m in scan._CORPUS_PATH_RE.finditer(a):
            tok = m.group(0)
            rel_part = tok.split("#")[0].rstrip('。."\'”’')
            if not (ROOT / rel_part).is_file():
                raise FileNotFoundError(f"points.csv {pid} corpus path missing: {rel_part} (from token {tok!r})")
            if "#L" in tok:
                lm = re.search(r"#L(\d+)(?:\.\.(\d+))?$", tok)
                if not lm:
                    raise ValueError(f"Malformed #L fragment in {pid}: {tok!r}")
                l_start = int(lm.group(1))
                l_end = int(lm.group(2) or lm.group(1))
                file_lines = (ROOT / rel_part).read_text(encoding="utf-8", errors="ignore").split("\n")
                if not (1 <= l_start <= l_end <= len(file_lines)):
                    raise ValueError(
                        f"Out-of-bounds #L{l_start}..{l_end} in {pid} for {rel_part} ({len(file_lines)} lines)"
                    )
                corpus_line_verified += 1

    assert not bare_rows, f"Remaining non-leading http/corpus anchors in points.csv: {bare_rows}"
    assert not md_rows, f"Remaining Markdown links in points.csv 锚点URL: {md_rows}"

    # Gate C: scan._check_point_row & scan._check_point_table
    del scan.ERR[:]
    for r in rows:
        scan._check_point_row(r)
    scan._check_point_table(rows)
    if scan.ERR:
        errs = list(scan.ERR)
        del scan.ERR[:]
        raise AssertionError(f"scan point checks failed: {errs}")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=POINTS_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = ("\ufeff" + buf.getvalue()).encode("utf-8")

    phys_lines = payload.decode("utf-8-sig").splitlines()
    assert len(phys_lines) == len(rows) + 1, f"points.csv physical lines {len(phys_lines)} != {len(rows) + 1}"

    changed = write_bytes_if_changed(POINTS_CSV, payload)
    pure_http_count = sum(
        1 for r in rows if re.fullmatch(r"https?://[^\s，；。<>\[\]]+", (r["锚点URL"] or "").strip())
    )
    leading_http_multi_count = sum(
        1
        for r in rows
        if (r["锚点URL"] or "").strip().startswith(("http://", "https://"))
        and not re.fullmatch(r"https?://[^\s，；。<>\[\]]+", (r["锚点URL"] or "").strip())
    )
    leading_corpus_count = sum(1 for r in rows if (r["锚点URL"] or "").strip().startswith("corpus/"))

    return {
        "changed_this_run": changed,
        "sha256": sha256_bytes(payload),
        "total_rows": len(rows),
        "added_point_ids": ["P277"],
        "pure_http_anchor_rows": pure_http_count,
        "leading_http_multi_anchor_rows": leading_http_multi_count,
        "leading_corpus_anchor_rows": leading_corpus_count,
        "bare_text_anchor_rows": len(bare_rows),
        "markdown_wrapped_anchor_rows": len(md_rows),
        "verified_corpus_lf_line_spans": corpus_line_verified,
        "p074_as_of_preserved": by_id["P074"]["检索日期"],
    }


# ---------------------------------------------------------------------------
# Step C: Task 2 + Task 3 deterministic adjudication of triage.csv
# ---------------------------------------------------------------------------
def remediate_triage_csv(point_company_names: set[str]) -> dict[str, Any]:
    with TRIAGE_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == TRIAGE_COLUMNS, f"Unexpected triage.csv columns: {reader.fieldnames}"
        rows = list(reader)

    ks_span = fmt_corpus_span(
        "corpus/annual/600552/600552/600552__em_凯盛科技_em__2025_凯盛科技股份有限公司2025年年度报告.pdf.txt",
        ["为LGD、亚马逊、三星、京瓷、华硕，宏碁、京东方、华星光电、科大讯飞、陶丽西、维苏威等国际国内知名企业提供服务"],
        450,
        455,
    )
    zr_rd_span = fmt_corpus_span(
        "corpus/annual/688307/688307/688307__em_中润光学_em__2025_2025年年度报告.pdf.txt",
        ["本项目拟攻克隔离器、声光调制器、光开关、高功率光学元件等核心器件技术", "工业激光", "激光加工", "消费类激光", "打标"],
        1430,
        1443,
    )
    zr_strat_span = fmt_corpus_span(
        "corpus/annual/688307/688307/688307__em_中润光学_em__2025_2025年年度报告.pdf.txt",
        ["公司将光通信与光互联作为未来重要的战略增长极予以重点布局", "力争进入头部光模块与光通信设备厂商的核心供应链"],
        2437,
        2444,
    )
    fit_cpo_span = fmt_corpus_span(
        "corpus/annual/FIT/FIT/FIT_2025_Annual_Report.pdf.txt",
        ["collaborated with Broadcom on Co-packaged Optics (CPO), positioning FIT for early participation in next-generation computing architectures"],
        283,
        289,
    )
    fit_mda_span = fmt_corpus_span(
        "corpus/annual/FIT/FIT/FIT_2025_Annual_Report.pdf.txt",
        ["continued to deploy core component technologies for optical communications, and deepened cooperation opportunities with leading chip manufacturers"],
        473,
        480,
    )
    fit_sub_span = fmt_corpus_span(
        "corpus/annual/FIT/FIT/FIT_2025_Annual_Report.pdf.txt",
        ["Foxconn Optical Interconnect Technologies Inc."],
        7955,
        7960,
    )
    tz_h1_p14 = fmt_corpus_span(
        "corpus/ir/688003/688003_2026-08-20_2026年半年度报告.pdf.txt",
        ["天准为800G、1.6T等光模块提供精密量检测装备", "获得工业富联CPO量产项目的在线AOI检测设备首批小批量订单"],
        679,
        684,
    )

    updates_by_hid = {
        "凯盛科技客户京瓷+M3+互查矩阵": {
            "处置": "驳回-非本格",
            "理由": (
                f"2025年报p.10({ks_span})原文\"为LGD、亚马逊、三星、京瓷、华硕，宏碁、京东方、华星光电、"
                "科大讯飞、陶丽西、维苏威等国际国内知名企业提供服务\"，京瓷与消费电子/显示面板终端客户并列于显示触控模组及通用材料营销网络，"
                "全文零提及光通信陶瓷管壳或M3光芯片热沉供应，非光通信M3本格"
            ),
            "会话日期": SESSION_DATE,
        },
        "中润光学+D6+2025年报": {
            "处置": "驳回-非本格",
            "理由": (
                f"2025年报p.34在研项目16\"高性能激光器件研究与开发\"({zr_rd_span}，小批试制)原文\"本项目拟攻克隔离器、"
                "声光调制器、光开关、高功率光学元件等核心器件技术，实现中高功率激光系统关键部件自主开发\"，右栏具体应用前景明确限定为"
                "\"工业激光、激光加工、消费类激光打标\"而非光通信D6光隔离器；p.13(L608..609)声光/磁光器件亦面向超快激光器客户，"
                f"p.54({zr_strat_span})光通信与光互联仅为未来战略展望(\"力争进入头部光模块与光通信设备厂商的核心供应链\")、"
                "p.52(L2317)三石园为参股产业基金润扬基金594.79万元财务投资，均无公司自建或量产光通信D6隔离器产线实证"
            ),
            "会话日期": SESSION_DATE,
        },
        "FIT+ANY+FIT_2025_Annual_Report.pdf": {
            "处置": "待判",
            "理由": (
                f"2026-11-22通读港交所2025年报全文复核维持待判：主席报告p.7({fit_cpo_span})仅披露展会推出224G CPC液冷方案及"
                f"\"collaborated with Broadcom on Co-packaged Optics (CPO), positioning FIT for early participation\"，"
                f"业务展望p.11({fit_mda_span})仅述\"continued to deploy core component technologies for optical communications\"，"
                f"附属公司表({fit_sub_span})列美国子公司Foxconn Optical Interconnect Technologies Inc.(研发与销售)；"
                "全文10,332行无800G/1.6T光模块或CPO产品量产出货及在建产线自述(外部研报所称800G出货+45%无一手锚支撑)，严禁硬拔高；"
                "可重启条件：HKEX正式公告或定期报告披露光模块/CPO组件量产出货或产线建设实证"
            ),
            "会话日期": SESSION_DATE,
        },
        "天准科技+EQ6+688003__em_天准科技_em__2025_2025年年度报告.pdf": {
            "处置": "已入点",
            "理由": (
                f"2026-11-22核出2026半年报p.14({tz_h1_p14}，https://static.cninfo.com.cn/finalpage/2026-08-20/1225482975.PDF#page=14)"
                "及2025年报p.18(L816..817)一手实证：800G/1.6T光模块精密量检测装备长期服务中际旭创、新易盛、天孚通信等头部客户，"
                "且2026年获工业富联CPO量产项目在线AOI检测设备首批小批量订单并部分交付客户现场，满足KN001准入①，已入点P277@EQ6"
            ),
            "会话日期": SESSION_DATE,
        },
    }

    by_hid = {r["hit_id"]: r for r in rows}
    for hid, patch in updates_by_hid.items():
        if hid not in by_hid:
            raise KeyError(f"Expected triage hit_id missing: {hid}")
        by_hid[hid].update(patch)

    # Strict triage gates
    del scan.ERR[:]
    scan._check_triage_ids(rows)
    for r in rows:
        for col, val in r.items():
            if "\n" in (val or "") or "\r" in (val or ""):
                raise ValueError(f"Embedded newline in triage.csv {r['hit_id']}.{col}")
        if r["来源"] not in scan.E_来源:
            raise ValueError(f"Illegal triage 来源 in {r['hit_id']}: {r['来源']}")
        if r["处置"] not in scan.E_处置:
            raise ValueError(f"Illegal triage 处置 in {r['hit_id']}: {r['处置']}")
        if r["处置"] == "已入点" and r["公司"] not in point_company_names:
            raise ValueError(f"triage {r['hit_id']} marked 已入点 but {r['公司']} missing from points.csv")
    if scan.ERR:
        errs = list(scan.ERR)
        del scan.ERR[:]
        raise AssertionError(f"scan._check_triage_ids failed: {errs}")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=TRIAGE_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = ("\ufeff" + buf.getvalue()).encode("utf-8")

    phys_lines = payload.decode("utf-8-sig").splitlines()
    assert len(phys_lines) == len(rows) + 1, f"triage.csv physical lines {len(phys_lines)} != {len(rows) + 1}"

    changed = write_bytes_if_changed(TRIAGE_CSV, payload)
    pending_all = [r["hit_id"] for r in rows if r["处置"] == "待判"]
    pending_scan = [r["hit_id"] for r in rows if r["处置"] == "待判" and r["来源"] == "扫描"]

    return {
        "changed_this_run": changed,
        "sha256": sha256_bytes(payload),
        "total_rows": len(rows),
        "adjudicated_items": {hid: updates_by_hid[hid]["处置"] for hid in updates_by_hid},
        "remaining_pending_total": len(pending_all),
        "remaining_pending_scan_qd": pending_scan,
    }


# ---------------------------------------------------------------------------
# Step D: Build structured 11-item domestic-drq-verdicts.json
# ---------------------------------------------------------------------------
def build_domestic_drq_verdicts(
    archived_pdfs: list[dict[str, Any]],
    cninfo_queries: dict[str, dict[str, Any]],
    points_summary: dict[str, Any],
    triage_summary: dict[str, Any],
) -> dict[str, Any]:
    verdicts = [
        {
            "queue_id": "DRQ0020",
            "entity_name": "东山精密",
            "stock_code": "002384",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P130;points:P133",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-11-02/1225654366.PDF",
            "local_corpus_refs": [
                "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt#L54..60",
                "corpus/ir/002384/002384_2026-11-02_002384投资者关系活动记录表20261102.pdf.txt#L102..122",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["002384"].get("fulltext_total"),
                "relation_total": cninfo_queries["002384"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "问题 3：公司光芯片明后年外售的规划以及后续 CW 产品的销售规划如何？ 回复：感谢您对公司的关注与支持。"
                "公司今年已有小批量光芯片外售，为优先保障自用，尚未大规模对外销售。光芯片大规模外售取决于柜内互联等下一代技术普及进度，"
                "预计后续需求逐步起量。 / 问题 8：公司今年三季度 1.6T 产品主要做客户测试验证，四季度起进入相对批量出货。"
            ),
            "factual_boundary_and_action": (
                "已回读2026-11-02投关原件全文：虽提问含CW字样，公司正式回复仅泛称“小批量光芯片外售”而未细分CW/EML/DFB品类或客户范围；"
                "已将该严格边界写入P130(C1)与P133(MOD1)注记，保留原引语不变，杜绝把泛称光芯片外售直接缩窄为CW外售。"
            ),
        },
        {
            "queue_id": "DRQ0031",
            "entity_name": "汇绿生态(武汉钧恒)",
            "stock_code": "001267",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P039;content:CLG0631",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-11-03/1225655440.PDF",
            "local_corpus_refs": [
                "corpus/ir/001267/001267_2026-11-03_001267汇绿生态投资者关系管理信息20261103.pdf.txt#L51..77",
                "corpus/ir/001267/001267_2026-11-06_001267汇绿生态投资者关系管理信息20261106.pdf.txt#L37..49",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["001267"].get("fulltext_total"),
                "relation_total": cninfo_queries["001267"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "公司目前光模块产能为：武汉本部约 300 万支/年、2025 年年底投产的鄂州工厂一期约 150 万支/年、"
                "2026 年 4 月底投产的马来西亚工厂约 100 万-150 万支/年。根据公告，公司计划总投资 3.09 亿元设立研发生产基地。"
                "建成后现有 150 万支产线全面技术升级、新增 200 万支高速率产线，武汉区域预计合计达 350 万支高速率光模块年产能，现有厂房停止使用。"
            ),
            "factual_boundary_and_action": (
                "已精读11/03(编号2026-008)及11/06(编号2026-009)投关原件：严格拆分现有已投产产能(武汉300万+鄂州一期150万+大马100-150万支/年)"
                "与3.09亿元武汉新基地远期扩建规划(建成后合计350万支/年且旧厂停用)；400G/800G为主力出货(800G正上量，未披露精确占比)，"
                "NPO处导入早期阶段；已同步更新P039本地行号锚点与判定注记。"
            ),
        },
        {
            "queue_id": "DRQ0032",
            "entity_name": "沪电股份",
            "stock_code": "002463",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "confirmed_deferred_no_filing",
            "recommended_queue_status": "watch_deferred",
            "recommended_kb_target_ref": "",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-10-16/1225608881.PDF",
            "local_corpus_refs": [
                "corpus/ir/002463/002463_2026-10-15_2026年10月15日投资者关系活动记录表.pdf.txt#L42..51",
                "corpus/ir/002463/002463_2026-10-16_2026年10月16日投资者关系活动记录表.pdf.txt#L42..51",
                "corpus/ir/002463/002463_2026-11-19_2026年11月19日投资者关系活动记录表.pdf.txt#L42..51",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["002463"].get("fulltext_total"),
                "relation_total": cninfo_queries["002463"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "在算力产品领域，公司围绕各类超节点架构，统筹推进计算、交换、互连方向核心技术攻关及产品落地，适配 224Gbps 传输速率的核心产品已实现小批量供货，"
                "并启动支持 448Gbps 传输速率的产品预研；在高速网络交换机方面，应用于 1.6T 交换机的产品已实现批量出货，并推进 3.2T 交换机配套的产品预研。"
            ),
            "factual_boundary_and_action": (
                "核查巨潮14份投关记录表(含10/15、10/16至11/19最新表)及39份正式公告：全部“适配224Gbps小批量供货”与“1.6T批量出货”均明确归属"
                "超节点计算/交换互连与1.6T高速网络交换机PCB(树外系统板/背板)，全文“光模块”零命中，未见B1光模块内部PCB披露；"
                "严守B1边界不入points.csv，建议转为watch_deferred。"
            ),
        },
        {
            "queue_id": "DRQ0033",
            "entity_name": "联特科技",
            "stock_code": "301205",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P174",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-10-28/1225635041.PDF",
            "local_corpus_refs": [
                "corpus/ir/301205/301205_2026-10-28_301205联特科技投资者关系管理信息20261028.pdf.txt#L55..76",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["301205"].get("fulltext_total"),
                "relation_total": cninfo_queries["301205"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "公司的800G产品已经实现批量发货，发货量每个季度都环比提升。1.6T的产品方案多元化，包括FRO、LRO、LPO等全系列产品，"
                "并已经成功送样给北美大型csp客户，并取得积极反馈。公司也在近期实机演示了1.6T LPO产品……800G、1.6T产品在客户端验证进展顺利，已获一些客户验证通过。"
            ),
            "factual_boundary_and_action": (
                "已精读10/28投关原件(编号2026-003)：严格拆分800G批量发货环比提升与1.6T(FRO/LRO/LPO)北美CSP送样/部分客户验证通过/实机演示时态，"
                "已更新P174(MOD1)锚点与注记。"
            ),
        },
        {
            "queue_id": "DRQ0034",
            "entity_name": "锐捷网络",
            "stock_code": "301165",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P187",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-10-21/1225614287.PDF",
            "local_corpus_refs": [
                "corpus/ir/301165/301165_2026-10-21_2026年10月19日至10月21日投资者关系活动记录表.pdf.txt#L135..138",
                "corpus/ir/301165/301165_2026-10-21_2026年10月19日至10月21日投资者关系活动记录表.pdf.txt#L276..286",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["301165"].get("fulltext_total"),
                "relation_total": cninfo_queries["301165"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "LPO 已规模量产交付 400G 产品，1.6T LPO 已推出原型样品……Q9 A: 公司 LPO 光模块产品均搭配自有交换机完成适配后销售，"
                "目前出货量较大的是 400G LPO 产品，与 400G 交换机搭配销售，不作为通用配件单独销售……因此公司下一步推出的 800G 甚至 1.6T LPO 产品，仍将主要搭配自有交换机销售。"
            ),
            "factual_boundary_and_action": (
                "已核对10/19-21投关原件(编号2026-04)并完成两项关键纠偏：①目前规模量产交付仅400G LPO(800G/1.6T LPO属下一步推出，1.6T LPO为原型样品)；"
                "②明确全部LPO光模块均搭配自有交换机适配捆绑销售、“不作为通用配件单独销售”；已写入P187(MOD1)锚点与注记。"
            ),
        },
        {
            "queue_id": "DRQ0035",
            "entity_name": "景旺电子",
            "stock_code": "603228",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P031;content:CLG0624;content:CLG0625",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-08-22/1225493416.PDF#page=11",
            "local_corpus_refs": [
                "corpus/ir/603228/603228_2026-08-22_2026年半年度报告.pdf",
                "corpus/ir/603228/603228_2026-08-22_2026年半年度报告.pdf.txt#L493..495",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["603228"].get("fulltext_total"),
                "relation_total": cninfo_queries["603228"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "高速光模块领域，随着公司新增 mSAP 产线安装调试完成，大批量产能落地，报告期内公司已批量交付 800G、1.6T 光模块 PCB，"
                "2026 年二季度，800G 及以上速率光模块收入环比增长近 1500%。公司深度参与多家全球领先客户的高速光模块 PCB 供应。"
            ),
            "factual_boundary_and_action": (
                "已下载归档景旺电子2026年半年度报告PDF及旁车文本至corpus/ir/603228/，精准核实第11页(#L493..495)逐字匹配P031引语，"
                "并在P031判定注记补齐本地行号定位与S.5548二手传闻剥离说明。"
            ),
        },
        {
            "queue_id": "DRQ0036",
            "entity_name": "华工科技",
            "stock_code": "000988",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P209;content:CLG0612;content:CLG0613",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-10-30/1225647394.PDF#page=6",
            "local_corpus_refs": [
                "corpus/ir/000988/000988_2026-10-30_2026年10月30日投资者关系活动记录表.pdf",
                "corpus/ir/000988/000988_2026-10-30_2026年10月30日投资者关系活动记录表.pdf.txt#L169..204",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["000988"].get("fulltext_total"),
                "relation_total": cninfo_queries["000988"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "800G LPO 产品已在下半年开始提量交付，目前泰国工厂月出货量约 10 万只，并已签订长单，明年 800G 系列 LPO 交付量预计为 120 万-150 万只，"
                "1.6T LPO 系列产品正在快速送样测试，预计 Q1 完成测试……已在北美获得一家知名客户的 6.4T NPO 产品供应商资格，产品已定型完成，正在推进送样测试，预计明年 7 月进入批量交付。"
            ),
            "factual_boundary_and_action": (
                "已从巨潮下载归档000988 2026-10-30正式投关记录表(编号2026-04)至corpus/ir/000988/：证实p.6第2问确有泰国工厂800G LPO月出货约10万只及1.6T LPO送样定量原话，"
                "同时核实全文无任何“原产地实质性改变/关税豁免”表述；已在P209注记补入本地原件行号并剔除关税外推。"
            ),
        },
        {
            "queue_id": "DRQ0047",
            "entity_name": "云南锗业(云南鑫耀)",
            "stock_code": "002428",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P202",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-11-18/1225676124.PDF",
            "local_corpus_refs": [
                "corpus/ir/002428/002428_2026-11-18_关于增加高品质磷化铟单晶片建设项目投资额的公告.pdf",
                "corpus/ir/002428/002428_2026-11-18_关于增加高品质磷化铟单晶片建设项目投资额的公告.pdf.txt#L14..48",
                "corpus/ir/002428/002428_2026-11-10_2026年11月10日投资者关系活动记录表.pdf.txt#L31..58",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["002428"].get("fulltext_total"),
                "relation_total": cninfo_queries["002428"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "2026 年 11 月 16 日，公司第九届董事会第九次会议审议通过《关于增加“高品质磷化铟单晶片建设项目”投资额的议案》……"
                "同意将“高品质磷化铟单晶片建设项目”的总投资额增加至 26,999 万元（调整前为 18,856 万元），其中：固定资产投资 23,393 万元（调整前为 15,250 万元），"
                "铺底流动资金 3,606 万元……合计新增机器设备 294 台（套），最终达到年产 45 万片（折合 4 英寸）高品质磷化铟单晶片的产能。"
            ),
            "factual_boundary_and_action": (
                "巨潮查获深交所2026-11-18正式公告《关于增加高品质磷化铟单晶片建设项目投资额的公告》(公告编号2026-057)及2026-11-10投关记录表并已落盘corpus/ir/002428/！"
                "一手原件将媒体概数“1.89亿调至2.7亿元”校准为精确法定数值“18,856万元调增8,143万元至26,999万元”(在董事会权限内无需股东会审议)，"
                "并同步披露6英寸磷化铟在手订单约1.3万片(约3亿元)、部分已获出口许可持续交付；已更新P202锚点与判定注记。"
            ),
        },
        {
            "queue_id": "DRQ0051",
            "entity_name": "天准科技",
            "stock_code": "688003",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "verified_ingested",
            "recommended_queue_status": "ingested_to_kb",
            "recommended_kb_target_ref": "points:P277",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-08-20/1225482975.PDF#page=14",
            "local_corpus_refs": [
                "corpus/ir/688003/688003_2026-08-20_2026年半年度报告.pdf",
                "corpus/ir/688003/688003_2026-08-20_2026年半年度报告.pdf.txt#L680..683",
                "corpus/annual/688003/688003/688003__em_天准科技_em__2025_2025年年度报告.pdf.txt#L816..817",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["688003"].get("fulltext_total"),
                "relation_total": cninfo_queries["688003"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "在光通信领域，天准为 800G、1.6T 等光模块提供精密量检测装备，覆盖了光模块领域大部分客户，长期服务于中际旭创、新易盛、天孚通信等头部客户。"
                "2026 年，天准获得工业富联 CPO 量产项目的在线 AOI 检测设备首批小批量订单，部分设备已交付客户现场，打开了 CPO、NPO 等光通信新领域量检测装备的增量市场空间。"
            ),
            "factual_boundary_and_action": (
                "巨潮核出688003《2026年半年度报告》(1225482975.PDF)第14页及2025年报第18页光模块与CPO在线AOI专属交付一手原文并落盘corpus/ir/688003/！"
                "满足KN001准入①及DRQ0051全部门槛(688003已在_frozen.csv v3分母)，已新增能力点P277(EQ6,生产中,A股)并同步将triage天准科技+EQ6更新为已入点。"
            ),
        },
        {
            "queue_id": "DRQ0053",
            "entity_name": "利扬芯片(拟收购众望达光电)",
            "stock_code": "688135",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "still_pending",
            "recommended_queue_status": "pending_filing_anchor",
            "recommended_kb_target_ref": "",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-11-14/1225671802.PDF",
            "local_corpus_refs": [
                "corpus/ir/688135/688135_2026-11-14_关于签署股权收购协议的公告.pdf",
                "corpus/ir/688135/688135_2026-11-14_关于签署股权收购协议的公告.pdf.txt#L9..27",
                "corpus/ir/688135/688135_2026-11-14_关于签署股权收购协议的公告.pdf.txt#L171..198",
                "corpus/ir/688135/688135_2026-11-14_关于签署股权收购协议的公告.pdf.txt#L675..679",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["688135"].get("fulltext_total"),
                "relation_total": cninfo_queries["688135"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "公司与深圳市众望达光电有限公司股东郑鸿章、邓荣辉签署了《股权收购协议》，拟筹划以现金方式收购众望达 51%的股权（整体估值 6.00 亿元，交易对价 30,600.00 万元）……"
                "众望达专注光通讯检测、自动化测试技术、自动化耦合的研发、设计、生产、销售与技术服务，面向光器件、光模块、硅光、CPO、光纤传感、光纤激光行业客户……"
                "截至本公告披露日，标的资产相关的审计、资产评估工作尚未完成……本次交易尚需提交公司股东会审议批准……存在不能按期顺利完成交割的风险。"
            ),
            "factual_boundary_and_action": (
                "巨潮查获2026-11-14正式公告(2026-071,1225671802.PDF)及11-17临时股东会资料并已落盘corpus/ir/688135/；"
                "但原件明确截至2026-11-22：①审计评估尚未完成(2026H1营收10,466.48万元未经审计)；②尚待股东会审议批准；③尚未完成股权交割并表且无具名客户披露。"
                "严格维持pending_filing_anchor，未交割前禁入points.csv EQ7/EQ4。"
            ),
        },
        {
            "queue_id": "DRQ0054",
            "entity_name": "经纬辉开(参股铱加科技)",
            "stock_code": "300120",
            "checked_date": SESSION_DATE,
            "recommended_verdict": "confirmed_deferred_no_filing",
            "recommended_queue_status": "watch_deferred",
            "recommended_kb_target_ref": "",
            "official_source_url": "https://static.cninfo.com.cn/finalpage/2026-11-17/1225676140.PDF",
            "local_corpus_refs": [
                "corpus/ir/300120/300120_2026-11-17_300120经纬辉开投资者关系管理信息20261117.pdf.txt#L61..93",
            ],
            "cninfo_announcement_counts": {
                "fulltext_total": cninfo_queries["300120"].get("fulltext_total"),
                "relation_total": cninfo_queries["300120"].get("relation_total"),
            },
            "verbatim_excerpt": (
                "公司全资子公司中兴系统持有铱加科技 7.71%股权……铱加目前不在上市公司合并报表内。研发上，铱加 1.6T/3.2T CPO 项目已通过深圳市科创委专项项目阶段性验收，"
                "完成硅光芯片、2.5D/3D 封装及原型验证，已有 25G-800G 光组件产品……目前公司对铱加持股比例较小，其营收规模也较小，对公司业绩基本无贡献。"
            ),
            "factual_boundary_and_action": (
                "巨潮检索47条正式公告未见铱加科技专项公告；2026-11-17正式投关表(编号2026-03)明确证实：①仅通过中兴系统间接参股7.71%且不在合并报表内；"
                "②1.6T/3.2T CPO仅属深圳市科创委科研专项阶段性验收(原型验证)，对上市公司业绩基本无贡献。按规则非控股参股+原型验证严禁入points.csv，建议转为watch_deferred。"
            ),
        },
    ]

    verdict_counts: dict[str, int] = {}
    for v in verdicts:
        verdict_counts[v["recommended_verdict"]] = verdict_counts.get(v["recommended_verdict"], 0) + 1

    return {
        "shard": "Step 4 Worker 2 (carbon-s4-points-triage)",
        "workpack_id": "OPTICAL-STEP4-BACKEND-FINAL-CLOSURE-20261122",
        "checked_date": SESSION_DATE,
        "script": "out/step4-backend-final-closure-20261122/remediate_points_and_domestic_drq.py",
        "points_remediation_summary": {
            k: v for k, v in points_summary.items() if k != "changed_this_run"
        },
        "triage_adjudication_summary": {
            k: v for k, v in triage_summary.items() if k != "changed_this_run"
        },
        "newly_archived_cninfo_ir_files": archived_pdfs,
        "cninfo_api_queries": cninfo_queries,
        "domestic_drq_verdict_counts": verdict_counts,
        "domestic_drq_verdicts": verdicts,
        "verifier_handoff_notes": {
            "participation_projection_delta": (
                "新增 P277 天准科技(688003, EQ6, 生产中, A股)使参与识别“已确认参与”由 93 增至 94 家；"
                "triage 裁决 600552 凯盛科技与 688307 中润光学为“驳回-非本格”(FIT 维持待判并刷新 2026-11-22 核查理由)，"
                "使参与识别“待确认”由 15 减至 13 家；请 carbon-s4-verifier 重跑 participation.py / render.py / "
                "build_detailed_capability_report.py 并同步对齐 tests/test_step3_daily_and_v6.py:344 及 review_queue.csv / entity_nodes.csv。"
            ),
            "review_queue_sync_suggestions": {
                "ingested_to_kb": ["DRQ0020", "DRQ0031", "DRQ0033", "DRQ0034", "DRQ0035", "DRQ0036", "DRQ0047", "DRQ0051"],
                "watch_deferred": ["DRQ0032", "DRQ0054"],
                "pending_filing_anchor": ["DRQ0053"],
            },
        },
    }


def main() -> None:
    session = requests.Session()
    archived_pdfs = sync_cninfo_ir_pdfs(session)
    cninfo_queries = query_cninfo_public_api(session, VERDICTS_JSON)
    points_summary = remediate_points_csv()

    with POINTS_CSV.open("r", encoding="utf-8-sig", newline="") as fh:
        pnames = {r["公司"] for r in csv.DictReader(fh)}
    triage_summary = remediate_triage_csv(pnames)

    verdicts_doc = build_domestic_drq_verdicts(
        archived_pdfs=archived_pdfs,
        cninfo_queries=cninfo_queries,
        points_summary=points_summary,
        triage_summary=triage_summary,
    )
    verdicts_bytes = (json.dumps(verdicts_doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    verdicts_changed = write_bytes_if_changed(VERDICTS_JSON, verdicts_bytes)

    print(
        f"[OK] points.csv: {points_summary['total_rows']} rows "
        f"(pure_http={points_summary['pure_http_anchor_rows']}, "
        f"leading_http={points_summary['leading_http_multi_anchor_rows']}, "
        f"leading_corpus={points_summary['leading_corpus_anchor_rows']}, "
        f"bare={points_summary['bare_text_anchor_rows']}, "
        f"changed={points_summary['changed_this_run']}, sha256={points_summary['sha256'][:12]}) | "
        f"triage.csv: {triage_summary['total_rows']} rows "
        f"(pending={triage_summary['remaining_pending_total']}, "
        f"changed={triage_summary['changed_this_run']}, sha256={triage_summary['sha256'][:12]}) | "
        f"domestic-drq-verdicts.json: {verdicts_doc['domestic_drq_verdict_counts']} "
        f"(changed={verdicts_changed}, sha256={sha256_bytes(verdicts_bytes)[:12]})"
    )


if __name__ == "__main__":
    main()
