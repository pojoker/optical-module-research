#!/usr/bin/env python3
"""Stage2 年报表格抽取器：PDF → extracted.json（标准库 + pdftotext）。

CLI:
    python3 demo/src/extract_tables.py --data-dir demo/data --out demo/out/extracted.json

自测摘要（2026-07-23，深交所 12/12；2026-07-23 v1.1 扩上交所后 30 份）:
  - 300308/2025 客户1 pct=24.06 amount=9201495755.91；客户E=3096780769.22；
    related_party_pct=8.10；供应商1 pct=35.76；
    related_party_sales=[{PINEWAVE, 43378, 万美元}]
  - 300394/2025 客户1 实名 Fabrinet pct=63.31 amount=3268843594.94；客户2 匿名「第二名」
  - 300502/2023 客户1 pct=36.79 amount=1139711326.47；收入确认含「浙江粮油」
  - 300502/2024-2025 收入确认全称「浙江省粮油食品进出口股份有限公司」；2024客户pct
    31.74/12.39/12.15/9.14/5.68
  - 002281/2023-2025 三份不 crash，客户/供应商均 5 行；无收入确认实名时 warnings 如实记录
  - SSE 奥特维2024 客户1 pct=13.25 amount=1219060100.00 related_flag=否
  - SSE 博众2024 客户1 pct=26.04 amount=1289933500.00
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


PDFTOTEXT = Path("/opt/homebrew/bin/pdftotext")

# 匿名客户/供应商名称（压平空白后）
ANON_NAME_RE = re.compile(
    r"^(?:"
    r"客户\s*[A-E1-5一二三四五]|"
    r"供应商\s*[A-E1-5一二三四五]|"
    r"第[一二三四五]名"
    r")$"
)

# 拉丁实名：保留 Co.,Ltd. / Inc. 等后缀，不在空格处截断
LATIN_NAME_RE = (
    r"[A-Za-z][A-Za-z0-9.&'’\-]*"
    r"(?:\s+Co\.,?\s*Ltd\.?"
    r"|\s+Inc\.?"
    r"|\s+LLC\.?"
    r"|\s+Ltd\.?"
    r"|\s+Corp\.?"
    r"|\s+Limited)?"
)

# 排名行：允许姓名与金额之间夹杂页眉/「合计 --」等噪声
RANK_ROW_RE = re.compile(
    r"(?<![0-9.])([1-5])\s+"
    r"("
    r"客户\s*[A-E1-5一二三四五]|"
    r"供应商\s*[A-E1-5一二三四五]|"
    r"第[一二三四五]名|"
    + LATIN_NAME_RE
    + r"|"
    r"[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9（）()\-·.&]{0,40}"
    r")"
    r"(?:(?![1-5]\s+(?:客户|供应商|第[一二三四五]名|[A-Za-z])).){0,120}?"
    r"([\d,]+\.\d{2})\s+"
    r"(\d+(?:\.\d+)?)\s*%"
)

AMOUNT_RE = re.compile(r"[\d,]+\.\d{2}")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

PAGE_HEADER_RE = re.compile(
    r"(?:-\s*\d+\s*-\s*)?"
    r"[\u4e00-\u9fffA-Za-z0-9（）()]{2,40}?"
    r"(?:股份有限公司|有限公司)?"
    r"\s*\d{4}\s*年\s*年度报告全文"
)

# 上交所页眉常无「全文」；仅 SSE 路径使用，避免扰动深交所 normalize
PAGE_HEADER_SSE_RE = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9（）()]{2,40}(?:股份有限公司|有限公司)\s*\d{4}\s*年?\s*年度报告"
)
# 页码「33 / 306」；禁止吞掉「客户 5 / 73,754.35」中的 5 / 73
PAGE_NUM_RE = re.compile(r"(?<![,\d])\b\d{1,3}\s*/\s*\d{2,4}\b(?!\s*,)")

CJK_SPACE_RE = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
CJK_PUNCT_SPACE_RE = re.compile(
    r"(?<=[\u4e00-\u9fff])\s+(?=[（）%：:])|(?<=[（：:])\s+(?=[\u4e00-\u9fff])"
)

# 收入确认实名：锚定「与…的销售」或「与…（以下简称」——避免「与资产相关…本公司」误抽
REV_SALES_RE = re.compile(
    r"与\s*([\u4e00-\u9fff]{2,40}?(?:股份有限公司|有限公司|公司|粮油))"
    r"(?:\s*的销售|\s*[（(]以下简称)"
)
REV_ABBR_RE = re.compile(
    r"与?\s*([\u4e00-\u9fff]{2,40}(?:股份有限公司|有限公司|公司))"
    r"[（(]以下简称([\u4e00-\u9fffA-Za-z0-9]{2,20})[）)]"
)
REV_NOISE_RE = re.compile(
    r"相关|判断|会计|方法|政府|补助|依据|处理|本公|详见|关于|内容|公告|披露"
)

# 关联交易段内拉丁大写词 / 中文实体
RP_LATIN_RE = re.compile(r"\b([A-Z]{2,}[A-Z0-9]*)\b")
RP_CN_RE = re.compile(
    r"([\u4e00-\u9fff]{2,30}(?:股份有限公司|有限公司|有限合伙))"
)
RP_AMOUNT_AFTER_RE = re.compile(
    r"关联交易金额[（(]万元[）)]\s*([\d,]+(?:\.\d+)?)"
)
RP_NAME_NOISE_RE = re.compile(r"详见|关于|内容|公告|披露|具体|年度报告|本公司")

LATIN_STOPWORDS = {
    "FOB",
    "FCA",
    "DDP",
    "DAP",
    "PDF",
    "USD",
    "CNY",
    "IPO",
    "CEO",
    "CFO",
    "RSU",
    "ADR",
    "ETF",
    "GDP",
    "AI",
    "IT",
    "ID",
    "OK",
    "NO",
    "YES",
    "HTTP",
    "HTTPS",
    "WWW",
    "LTD",
    "LLC",
    "INC",
    "CO",
    "A",
    "B",
    "C",
    "D",
    "E",
}

SSE_NUM = r"[\d,]+(?:\.\d+)?"
SSE_ROW_RE = re.compile(
    r"(?<![0-9.])([1-5])\s+"
    r"("
    r"客户\s*[A-E1-5一二三四五]|"
    r"供应商\s*[A-E1-5一二三四五]|"
    + LATIN_NAME_RE
    + r"|"
    r"[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9（）()\-·.&]{0,40}"
    r")"
    r"\s+([\d,]+\.\d{2})\s+(\d+(?:\.\d+)?)\s*%?\s*(是|否)?"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage2: extract tables from annual report PDFs")
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    return p.parse_args()


def strip_em_tags(text: str) -> str:
    return re.sub(r"</?em>", "", text or "").strip()


def normalize_text(raw: str) -> str:
    """压平空白并去掉 CJK 间空格，缓解 pdftotext 列错位/逐字拆散。深交所路径专用。"""
    text = raw.replace("\x0c", "\n")
    text = PAGE_HEADER_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    text = CJK_SPACE_RE.sub("", text)
    text = CJK_PUNCT_SPACE_RE.sub("", text)
    # 全角括号旁残留空格
    text = re.sub(r"\s+([）)])", r"\1", text)
    text = re.sub(r"([（(])\s+", r"\1", text)
    return text.strip()


def normalize_text_sse(raw: str) -> str:
    """上交所路径：额外剥无「全文」的页眉与页码，且不误伤「客户 5 / 73,754」。"""
    text = raw.replace("\x0c", "\n")
    text = PAGE_HEADER_RE.sub(" ", text)
    text = PAGE_HEADER_SSE_RE.sub(" ", text)
    text = PAGE_NUM_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    text = CJK_SPACE_RE.sub("", text)
    text = CJK_PUNCT_SPACE_RE.sub("", text)
    text = re.sub(r"\s+([）)])", r"\1", text)
    text = re.sub(r"([（(])\s+", r"\1", text)
    return text.strip()


def strip_commas(amount: str) -> str:
    return amount.replace(",", "")


def wan_to_yuan(amount_wan: str) -> str:
    """万元 → 元，Decimal 字符串，保留两位小数。"""
    return f"{Decimal(strip_commas(amount_wan)) * Decimal('10000'):.2f}"


def is_anonymous_name(name: str) -> bool:
    compact = re.sub(r"\s+", "", name.strip())
    spaced = re.sub(r"\s+", " ", name.strip())
    return bool(ANON_NAME_RE.match(spaced) or ANON_NAME_RE.match(compact))


def scrub_sticky_heji(name: str) -> str:
    """跨页黏行：名称末尾被挤入的「合计」剥掉后再判匿名（通用，非个案）。"""
    name = name.strip()
    if name.endswith("合计") and name != "合计":
        name = name[: -len("合计")].strip()
    return name


def pdftotext(pdf_path: Path) -> str:
    if not PDFTOTEXT.exists():
        raise FileNotFoundError(f"pdftotext not found: {PDFTOTEXT}")
    proc = subprocess.run(
        [str(PDFTOTEXT), "-q", str(pdf_path), "-"],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"pdftotext failed ({proc.returncode}): {err}")
    return proc.stdout.decode("utf-8", errors="replace")


def detect_template(raw: str) -> str:
    """按正文措辞分流：深交所「合计销售金额」优先于上交所「销售额X万元」。"""
    # 轻量压平即可判定，避免 SSE 专用 normalize 扰动深交所
    flat = re.sub(r"\s+", " ", raw.replace("\x0c", " "))
    if re.search(r"前五名客户合计销售金额", flat):
        return "szse"
    if re.search(r"前五名客户销售额\s*[\d,]+\.?\d*\s*万元", flat):
        return "sse"
    if re.search(r"前五名供应商合计采购金额", flat):
        return "szse"
    if re.search(r"前五名供应商采购额\s*[\d,]+\.?\d*\s*万元", flat):
        return "sse"
    return "szse"


def pick_best_section(text: str, anchor: str, window: int = 2200) -> str | None:
    """同一关键词可能命中目录/摘要/正文；选含完整排名行最多的窗口。"""
    hits = [m.start() for m in re.finditer(re.escape(anchor), text)]
    if not hits:
        # 宽松：去掉括号变体
        loose = anchor.replace("（", "[（(]?").replace("）", "[）)]?")
        hits = [m.start() for m in re.finditer(loose, text)]
    if not hits:
        return None

    best: tuple[int, str] | None = None
    for start in hits:
        chunk = text[start : start + window]
        score = len(RANK_ROW_RE.findall(chunk))
        # 正文通常带「公司前5大/名…资料」
        if re.search(r"公司前\s*5\s*(?:大客户|名供应商)资料", chunk):
            score += 5
        if "序号" in chunk:
            score += 1
        if best is None or score > best[0]:
            best = (score, chunk)
    return best[1] if best else None


def parse_top5_block(section: str, kind: str, warnings: list[str]) -> dict[str, Any]:
    """kind: customers | suppliers（深交所模板）"""
    empty = {
        "rows": [],
        "total_amount": None,
        "total_pct": None,
        "related_party_pct": None,
    }
    if not section:
        warnings.append(f"{kind}: 未定位到合计金额段")
        return empty

    related_party_pct = None
    if kind == "customers":
        m = re.search(
            r"前五名客户销售额中关联方销售额占年度销售总额比例\s*(\d+(?:\.\d+)?)\s*%",
            section,
        )
        if m:
            related_party_pct = m.group(1)
        else:
            warnings.append("customers: 未抽到 related_party_pct")
    else:
        m = re.search(
            r"前五名供应商采购额中关联方采购额占年度采购总额比例\s*(\d+(?:\.\d+)?)\s*%",
            section,
        )
        if m:
            related_party_pct = m.group(1)
        else:
            warnings.append("suppliers: 未抽到 related_party_pct")

    total_amount = None
    total_pct = None
    if kind == "customers":
        tm = re.search(
            r"前五名客户合计销售金额[（(]元[）)]\s*([\d,]+\.\d{2})?",
            section,
        )
        tp = re.search(
            r"前五名客户合计销售金额占年度销售总额比例\s*(\d+(?:\.\d+)?)\s*%",
            section,
        )
        # 分页：合计金额落在标签之前
        if not (tm and tm.group(1)):
            tm_before = re.search(
                r"([\d,]+\.\d{2})\s*前五名客户合计销售金额[（(]元[）)]",
                section,
            )
            if tm_before:
                tm = tm_before
    else:
        tm = re.search(
            r"前五名供应商合计采购金额[（(]元[）)]\s*([\d,]+\.\d{2})?",
            section,
        )
        tp = re.search(
            r"前五名供应商合计采购金额占年度采购总额比例\s*(\d+(?:\.\d+)?)\s*%",
            section,
        )
        if not (tm and tm.group(1)):
            tm_before = re.search(
                r"([\d,]+\.\d{2})\s*前五名供应商合计采购金额[（(]元[）)]",
                section,
            )
            if tm_before:
                tm = tm_before
    if tm and tm.group(1):
        total_amount = strip_commas(tm.group(1))
    if tp:
        total_pct = tp.group(1)

    # 表格区：优先从「公司前5…资料」起，否则整段
    table_m = re.search(r"公司前\s*5\s*(?:大客户|名供应商)资料", section)
    table = section[table_m.start() :] if table_m else section

    rows: list[dict[str, Any]] = []
    seen_ranks: set[int] = set()
    for m in RANK_ROW_RE.finditer(table):
        rank = int(m.group(1))
        if rank in seen_ranks:
            continue
        name_raw = re.sub(r"\s+", " ", m.group(2)).strip()
        # 截断误吞的后缀噪声（含无空格黏连的「合计」）
        name_raw = re.split(r"\s+(?:合计|占年度|主要)", name_raw)[0].strip()
        name_raw = scrub_sticky_heji(name_raw)
        amount = strip_commas(m.group(3))
        pct = m.group(4)
        rows.append(
            {
                "rank": rank,
                "name_raw": name_raw,
                "is_anonymous": is_anonymous_name(name_raw),
                "amount_yuan": amount,
                "pct": pct,
            }
        )
        seen_ranks.add(rank)
        if len(rows) >= 5:
            break

    rows.sort(key=lambda r: r["rank"])

    # 合计行兜底（含「金额 pct% -- 合计」分页错序）
    if total_amount is None or total_pct is None:
        sum_m = re.search(
            r"合计\s*(?:--|—|－)?\s*([\d,]+\.\d{2})\s+(\d+(?:\.\d+)?)\s*%",
            table,
        )
        if not sum_m:
            sum_m = re.search(
                r"([\d,]+\.\d{2})\s+(\d+(?:\.\d+)?)\s*%\s*(?:--|—|－)?\s*合计",
                table,
            )
        if sum_m:
            if total_amount is None:
                total_amount = strip_commas(sum_m.group(1))
            if total_pct is None:
                total_pct = sum_m.group(2)

    if len(rows) < 5:
        warnings.append(f"{kind}: 仅抽到 {len(rows)}/5 行")
    if total_amount is None:
        warnings.append(f"{kind}: 未抽到 total_amount")
    if total_pct is None:
        warnings.append(f"{kind}: 未抽到 total_pct")

    return {
        "rows": rows,
        "total_amount": total_amount,
        "total_pct": total_pct,
        "related_party_pct": related_party_pct,
    }


def parse_sse_narr(text: str, kind: str) -> tuple[str, str, str] | None:
    """叙述句 → (total_amount_yuan, total_pct, related_party_pct)。"""
    if kind == "customers":
        m = re.search(
            rf"前五名客户销售额\s*({SSE_NUM})\s*万元[，,]\s*占年度销售总额\s*(\d+(?:\.\d+)?)\s*%"
            rf".*?其中前五名客户销售额中关联\s*方销售额\s*({SSE_NUM})\s*万元[，,]\s*占年度销售总额\s*(\d+(?:\.\d+)?)\s*%?",
            text,
        )
    else:
        m = re.search(
            rf"前五名供应商采购额\s*({SSE_NUM})\s*万元[，,]\s*占年度采购总额\s*(\d+(?:\.\d+)?)\s*%"
            rf".*?其中前五名供应商采购额中关\s*联\s*方采购额\s*({SSE_NUM})\s*万元[，,]\s*占年度采购总额\s*(\d+(?:\.\d+)?)\s*%?",
            text,
        )
    if not m:
        return None
    return wan_to_yuan(m.group(1)), m.group(2), m.group(4)


def detect_sse_unit_wan(section: str) -> bool:
    for m in re.finditer(r"单位\s*[:：]\s*(万元|元)", section):
        window = section[max(0, m.start() - 80) : m.start() + 120]
        if any(k in window for k in ("客户", "供应商", "序号", "销售额", "采购额")):
            return m.group(1) == "万元"
    m = re.search(r"单位\s*[:：]\s*(万元|元)", section)
    if m:
        return m.group(1) == "万元"
    return True


def pick_sse_section(text: str, kind: str) -> str | None:
    if kind == "customers":
        anchors = ["公司前五名客户", "前五名客户销售额", "客户名称"]
    else:
        anchors = ["公司前五名供应商", "前五名供应商采购额", "供应商名称"]
    best: tuple[int, str] | None = None
    for a in anchors:
        for m in re.finditer(a, text):
            start = max(0, m.start() - 80) if a.endswith("名称") else m.start()
            chunk = text[start : start + 3200]
            score = 0
            if "序号" in chunk:
                score += 2
            if "客户名称" in chunk or "供应商名称" in chunk:
                score += 3
            if re.search(r"(?:客户|供应商)\s*[1-5一二三四五]", chunk):
                score += 5
            if re.search(r"1\s+客户|1\s+供应商", chunk):
                score += 6
            if "单位" in chunk:
                score += 1
            if a.startswith("公司前五名"):
                score += 2
            if best is None or score > best[0]:
                best = (score, chunk)
    return best[1] if best else None


def sse_table_region(section: str, kind: str) -> str:
    region = section
    if kind == "customers":
        cut = re.search(
            r"公司前五名供应商|B\.?公司主要供应商情况|报告期内向单个供应商",
            region,
        )
        if cut:
            region = region[: cut.start()]
    markers: list[int] = []
    for pat in [
        r"公司前五名(?:客户|供应商)",
        r"序号",
        r"单位\s*[:：]\s*(?:万元|元)",
    ]:
        m = re.search(pat, region)
        if m:
            markers.append(m.start())
    if markers:
        region = region[min(markers) :]
    # 去掉表头「是否…」避免拆成关联标志
    region = re.sub(r"是否与上市公司存在(?:关联关系)?", " ", region)
    region = re.sub(r"关联关系", " ", region)
    return region


def sse_extract_anon_names(section: str, kind: str) -> list[str] | None:
    prefix = "客户" if kind == "customers" else "供应商"
    names = re.findall(rf"{prefix}\s*[1-5一二三四五]", section)
    out: list[str] = []
    seen: set[str] = set()
    for n in names:
        n = re.sub(r"\s+", " ", n.strip())
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
        if len(out) >= 5:
            return out
    return out if len(out) == 5 else None


def sse_extract_amounts_grouped(section: str, kind: str) -> list[str] | None:
    region = sse_table_region(section, kind)
    names = sse_extract_anon_names(region, kind)
    if names:
        first_idx = region.find(names[0])
        last_idx = region.find(names[-1], first_idx)
        between = region[first_idx:last_idx]
        # 名称组连续、金额组在后
        if not re.search(r"[\d,]+\.\d{2}", between):
            start = last_idx + len(names[-1])
            amounts = re.findall(r"[\d,]+\.\d{2}", region[start : start + 700])
            if len(amounts) >= 5:
                return amounts[:5]
    # 分页打断：序号后收集金额序列
    m = re.search(r"序号", region)
    search = region[m.start() :] if m else region
    amounts = re.findall(r"[\d,]+\.\d{2}", search)
    if len(amounts) >= 5:
        return amounts[:5]
    return None


def sse_extract_pct_flags(
    section: str, kind: str
) -> tuple[list[str], list[str | None]] | None:
    region = sse_table_region(section, kind)
    # 13.25 否 / 11.70% 否；(?<![,\d]) 避免 25,079.08 → 079.08
    pairs = re.findall(r"(?<![,\d])(\d+\.\d+)\s*%?\s*(是|否)", region)
    cleaned = [(p, f) for p, f in pairs if Decimal(p) <= Decimal("100")]
    if len(cleaned) >= 5:
        return [c[0] for c in cleaned[:5]], [c[1] for c in cleaned[:5]]

    pcts = [
        p
        for p in re.findall(r"(?<![,\d])(\d+\.\d+)\s*%", region)
        if Decimal(p) <= Decimal("100")
    ]
    flags = re.findall(r"[是否]", region)
    if len(pcts) >= 5:
        return pcts[:5], (flags[:5] + [None] * 5)[:5]

    tokens = re.findall(r"(?<![,\d])(\d+\.\d+)\s*%?\s*(是|否)?", region)
    pcts2: list[str] = []
    flags2: list[str | None] = []
    for p, f in tokens:
        if Decimal(p) > Decimal("100"):
            continue
        pcts2.append(p)
        flags2.append(f if f else None)
        if len(pcts2) >= 5:
            break
    if len(pcts2) >= 5:
        if all(f is None for f in flags2):
            flags2 = (re.findall(r"[是否]", region) + [None] * 5)[:5]
        return pcts2[:5], flags2[:5]
    return None


def parse_sse_grouped(
    section: str, kind: str, unit_wan: bool
) -> list[dict[str, Any]] | None:
    region = sse_table_region(section, kind)
    names = sse_extract_anon_names(region, kind) or sse_extract_anon_names(section, kind)
    amounts = sse_extract_amounts_grouped(section, kind)
    pf = sse_extract_pct_flags(section, kind)
    if not names or not amounts or not pf:
        return None
    pcts, flags = pf
    rows: list[dict[str, Any]] = []
    for i in range(5):
        amt = strip_commas(amounts[i])
        if unit_wan:
            amt = wan_to_yuan(amt)
        flag = flags[i] if flags else None
        if flag == "":
            flag = None
        name = scrub_sticky_heji(names[i])
        rows.append(
            {
                "rank": i + 1,
                "name_raw": name,
                "is_anonymous": is_anonymous_name(name),
                "amount_yuan": amt,
                "pct": pcts[i],
                "related_flag": flag,
            }
        )
    return rows


def parse_sse_rows(
    section: str, kind: str, unit_wan: bool
) -> list[dict[str, Any]] | None:
    region = section
    if kind == "customers":
        m = re.search(r"1\s+客户", section)
        if m:
            region = section[max(0, m.start() - 200) : m.start() + 1200]
        else:
            cut = re.search(
                r"报告期内向单个供应商|公司前五名供应商|B\.?公司主要供应商情况",
                section,
            )
            if cut and cut.start() > 500:
                region = section[: cut.start()]
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for m in SSE_ROW_RE.finditer(region):
        rank = int(m.group(1))
        if rank in seen:
            continue
        name = scrub_sticky_heji(re.sub(r"\s+", " ", m.group(2)).strip())
        if kind == "customers" and name.startswith("供应商"):
            continue
        if kind == "suppliers" and name.startswith("客户"):
            continue
        if name in ("序号", "合计", "销售额", "采购额"):
            continue
        raw_amt = strip_commas(m.group(3))
        amt = wan_to_yuan(raw_amt) if unit_wan else raw_amt
        rows.append(
            {
                "rank": rank,
                "name_raw": name,
                "is_anonymous": is_anonymous_name(name),
                "amount_yuan": amt,
                "pct": m.group(4),
                "related_flag": m.group(5),
            }
        )
        seen.add(rank)
        if len(rows) >= 5:
            break
    return rows if len(rows) == 5 else None


def parse_sse_top5_block(text: str, kind: str, warnings: list[str]) -> dict[str, Any]:
    empty = {
        "rows": [],
        "total_amount": None,
        "total_pct": None,
        "related_party_pct": None,
    }
    narr = parse_sse_narr(text, kind)
    section = pick_sse_section(text, kind)
    if not section:
        warnings.append(f"{kind}: 未定位到合计金额段")
        if narr:
            return {
                "rows": [],
                "total_amount": narr[0],
                "total_pct": narr[1],
                "related_party_pct": narr[2],
            }
        return empty

    total_amount = narr[0] if narr else None
    total_pct = narr[1] if narr else None
    related_party_pct = narr[2] if narr else None
    if not narr:
        warnings.append(
            f"{kind}: 未抽到叙述句合计"
            + ("/related_party_pct" if kind == "customers" else "")
        )

    unit_wan = detect_sse_unit_wan(section)
    rows = parse_sse_rows(section, kind, unit_wan)
    if not rows:
        rows = parse_sse_grouped(section, kind, unit_wan)

    if not rows:
        warnings.append(f"{kind}: 仅抽到 0/5 行")
        rows = []
    elif len(rows) < 5:
        warnings.append(f"{kind}: 仅抽到 {len(rows)}/5 行")

    if total_amount is None:
        warnings.append(f"{kind}: 未抽到 total_amount")
    if total_pct is None:
        warnings.append(f"{kind}: 未抽到 total_pct")
    if related_party_pct is None and kind == "customers":
        warnings.append("customers: 未抽到 related_party_pct")
    elif related_party_pct is None and kind == "suppliers":
        warnings.append("suppliers: 未抽到 related_party_pct")

    return {
        "rows": rows,
        "total_amount": total_amount,
        "total_pct": total_pct,
        "related_party_pct": related_party_pct,
    }


def prefer_full_names(names: list[str], abbr_of: dict[str, str]) -> list[str]:
    """去重：简称让位于全称；全称优先输出。"""
    cleaned: list[str] = []
    for n in names:
        n = n.strip().lstrip("与").rstrip("的")
        if not n or n in ("本公司", "公司", "客户", "供应商"):
            continue
        if REV_NOISE_RE.search(n):
            continue
        n = re.sub(r"(的销售|销售)$", "", n)
        if len(n) < 2:
            continue
        cleaned.append(n)

    expanded: list[str] = []
    for n in cleaned:
        full = abbr_of.get(n, n)
        full = full.lstrip("与")
        if REV_NOISE_RE.search(full):
            expanded.append(n)
        else:
            expanded.append(full)

    uniq: list[str] = []
    for n in expanded:
        if n not in uniq:
            uniq.append(n)

    kept: list[str] = []
    for n in sorted(uniq, key=len, reverse=True):
        if any(n != k and n in k for k in kept):
            continue
        kept.append(n)

    # 全称优先；同实体简称已由 abbr_of 合并
    kept.sort(key=lambda x: (0 if x.endswith(("公司", "企业", "合伙")) else 1, -len(x), x))
    return kept


def extract_revenue_recognition_names(text: str, warnings: list[str]) -> list[str]:
    windows: list[str] = []
    for m in re.finditer(r"收入确认", text):
        windows.append(text[max(0, m.start() - 80) : m.start() + 900])
    if not windows:
        windows = [text]

    abbr_of: dict[str, str] = {}
    names: list[str] = []
    for w in windows:
        for full, abbr in REV_ABBR_RE.findall(w):
            full = full.lstrip("与")
            abbr_of[abbr] = full
            names.append(full)
            names.append(abbr)
        names.extend(REV_SALES_RE.findall(w))

    result = prefer_full_names(names, abbr_of)
    if not result:
        warnings.append("procedural: 收入确认段未抽到实名主体")
    return result


def detect_rp_unit(section: str) -> str:
    unit_m = re.search(r"单位[:：]\s*(美元|万元|元)", section[:200])
    has_wan_col = bool(re.search(r"关联交易金额[（(]万元[）)]", section[:800]))
    base = unit_m.group(1) if unit_m else None
    if base == "美元" and has_wan_col:
        return "万美元"
    if base == "美元":
        return "美元"
    if has_wan_col or base == "万元":
        return "万元"
    return "元"


def extract_related_party_sales(text: str, warnings: list[str]) -> list[dict[str, str]]:
    anchor = None
    for key in ("与日常经营相关的关联交易", "重大关联交易"):
        if key in text:
            anchor = key
            break
    if not anchor:
        warnings.append("procedural: 未定位重大关联交易段")
        return []

    # 取带表格数据的最佳命中
    starts = [m.start() for m in re.finditer(re.escape(anchor), text)]
    best_sec = ""
    best_score = -1
    for s in starts:
        sec = text[s : s + 3500]
        score = 0
        if re.search(r"[☑]\s*适用", sec[:120]) or re.search(r"适用\s*□不适用", sec[:120]):
            score += 2
        if RP_LATIN_RE.search(sec) or RP_CN_RE.search(sec):
            score += 2
        if "关联交易金额" in sec:
            score += 3
        if re.search(r"[☑]\s*不适用|□适用\s*[☑]不适用", sec[:100]):
            score -= 1
        if score > best_score:
            best_score = score
            best_sec = sec

    section = best_sec
    # 截到下一节
    cut = re.search(r"2、(?:资产或股权|资产收购|共同对外|关联债权)", section[80:])
    if cut:
        section = section[: 80 + cut.start()]

    if re.search(r"公司报告期未发生与日常经营相关的关联交易|未发生.*关联交易", section):
        return []
    if re.search(r"□适用\s*[☑]不适用", section[:150]) and "关联交易金额" not in section:
        return []

    if "关联交易金额" not in section:
        return []

    unit = detect_rp_unit(section)
    sales: list[dict[str, str]] = []
    seen: set[str] = set()

    def plausible_amount(raw: str) -> str | None:
        amount = strip_commas(raw)
        if not amount:
            return None
        # 拒年份/公告编号类：纯 4 位 20xx，或过短
        if re.fullmatch(r"20\d{2}", amount):
            return None
        if amount.isdigit() and len(amount) <= 3:
            return None
        return amount

    # 拉丁大写关联方（如 PINEWAVE）
    for m in RP_LATIN_RE.finditer(section):
        name = m.group(1)
        if name in LATIN_STOPWORDS or len(name) < 3:
            continue
        window = section[m.start() : m.start() + 800]
        am = RP_AMOUNT_AFTER_RE.search(window)
        if not am:
            continue
        amount = plausible_amount(am.group(1))
        if amount is None:
            continue
        key = f"{name}|{amount}"
        if key in seen:
            continue
        seen.add(key)
        sales.append({"name": name, "amount": amount, "unit": unit})

    # 中文关联方：仅认带「股份有限公司/有限公司/有限合伙」且金额紧跟交易金额列
    for m in RP_CN_RE.finditer(section):
        name = m.group(1).lstrip("与")
        if RP_NAME_NOISE_RE.search(name) or len(name) < 4:
            continue
        window = section[m.start() : m.start() + 800]
        am = RP_AMOUNT_AFTER_RE.search(window)
        if not am:
            continue
        amount = plausible_amount(am.group(1))
        if amount is None:
            continue
        key = f"{name}|{amount}"
        if key in seen:
            continue
        seen.add(key)
        sales.append({"name": name, "amount": amount, "unit": unit})

    return sales


def extract_from_text_szse(
    text: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    flat = normalize_text(text)

    cust_sec = pick_best_section(flat, "前五名客户合计销售金额")
    # 供应商段：从客户段之后找，避免串台
    search_from = 0
    if cust_sec:
        idx = flat.find(cust_sec[:60]) if len(cust_sec) >= 60 else -1
        if idx >= 0:
            search_from = idx
    supplier_region = flat[search_from:]
    # 供应商合计金额可能因分页落在标签前：扩大搜索起点
    if search_from > 80:
        supplier_region = flat[search_from - 80 :]
    sup_sec = pick_best_section(supplier_region, "前五名供应商合计采购金额")
    if sup_sec is None:
        # 全篇再找，并尝试带前置金额的窗口
        hits = [m.start() for m in re.finditer(r"前五名供应商合计采购金额", flat)]
        best: tuple[int, str] | None = None
        for h in hits:
            start = max(0, h - 40)
            chunk = flat[start : h + 2200]
            score = len(RANK_ROW_RE.findall(chunk))
            if re.search(r"公司前\s*5\s*名供应商资料", chunk):
                score += 5
            if best is None or score > best[0]:
                best = (score, chunk)
        if best:
            # 规范化为从标签起，但保留前置金额：拼回标签前 40 字
            label_at = best[1].find("前五名供应商合计采购金额")
            if label_at > 0:
                # pick_best_section 风格：用含前置金额的 chunk，parse 时 before-label 能命中
                sup_sec = best[1]
            else:
                sup_sec = best[1]
        else:
            sup_sec = pick_best_section(flat, "前五名供应商合计采购金额")

    # 客户段同样：若标签前可能有金额，回退 40 字
    if cust_sec:
        idx = flat.find(cust_sec[: min(60, len(cust_sec))])
        if idx > 40:
            # 检查标签前是否紧邻金额
            prefix = flat[idx - 40 : idx]
            if re.search(r"[\d,]+\.\d{2}\s*$", prefix.strip()[:40]) or re.search(
                r"[\d,]+\.\d{2}", prefix
            ):
                cust_sec = flat[idx - 40 : idx + 2200]

    customers = parse_top5_block(cust_sec or "", "customers", warnings)
    suppliers = parse_top5_block(sup_sec or "", "suppliers", warnings)

    procedural = {
        "revenue_recognition_names": extract_revenue_recognition_names(flat, warnings),
        "related_party_sales": extract_related_party_sales(flat, warnings),
    }
    return customers, suppliers, procedural, warnings


def extract_from_text_sse(
    text: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    flat = normalize_text_sse(text)
    customers = parse_sse_top5_block(flat, "customers", warnings)
    suppliers = parse_sse_top5_block(flat, "suppliers", warnings)
    procedural = {
        "revenue_recognition_names": extract_revenue_recognition_names(flat, warnings),
        "related_party_sales": extract_related_party_sales(flat, warnings),
    }
    return customers, suppliers, procedural, warnings


def extract_from_text(
    text: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str], str]:
    template = detect_template(text)
    if template == "sse":
        customers, suppliers, procedural, warnings = extract_from_text_sse(text)
    else:
        customers, suppliers, procedural, warnings = extract_from_text_szse(text)
    return customers, suppliers, procedural, warnings, template


def resolve_pdf_path(data_dir: Path, row: dict[str, str]) -> Path | None:
    local = (row.get("local_path") or "").strip()
    if local:
        p = Path(local)
        if p.is_file():
            return p
    code = (row.get("stock_code") or "").strip()
    year = (row.get("fiscal_year") or "").strip()
    company_dir = data_dir / code
    if not company_dir.is_dir():
        return None
    # 文件名含年报年份
    cands = sorted(company_dir.glob(f"*_{year}_*.pdf")) + sorted(
        company_dir.glob(f"*{year}*年度报告*.pdf")
    )
    for c in cands:
        if c.is_file():
            return c
    pdfs = list(company_dir.glob("*.pdf"))
    return pdfs[0] if len(pdfs) == 1 else None


def load_metadata_rows(data_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for csv_path in sorted(data_dir.glob("*/annual_reports.csv")):
        with csv_path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    return rows


def relative_source(pdf: Path, cwd: Path) -> str:
    try:
        return str(pdf.resolve().relative_to(cwd.resolve()))
    except ValueError:
        return str(pdf)


def process_report(data_dir: Path, row: dict[str, str], cwd: Path) -> dict[str, Any]:
    code = (row.get("stock_code") or "").strip()
    company = strip_em_tags(row.get("company_name") or "")
    # 文件名里的 _em_残留兜底
    if not company or "em" in company.lower() and len(company) < 2:
        company = strip_em_tags(re.sub(r"_?em_?", "", company))
    try:
        year = int(str(row.get("fiscal_year")).strip())
    except (TypeError, ValueError):
        year = None

    pdf_url = (row.get("pdf_url") or "").strip()
    warnings: list[str] = []
    pdf = resolve_pdf_path(data_dir, row)

    report: dict[str, Any] = {
        "stock_code": code,
        "company": company,
        "fiscal_year": year,
        "source_pdf": relative_source(pdf, cwd) if pdf else None,
        "pdf_url": pdf_url or None,
        "template": None,
        "customers": {
            "rows": [],
            "total_amount": None,
            "total_pct": None,
            "related_party_pct": None,
        },
        "suppliers": {
            "rows": [],
            "total_amount": None,
            "total_pct": None,
            "related_party_pct": None,
        },
        "procedural": {
            "revenue_recognition_names": [],
            "related_party_sales": [],
        },
        "warnings": warnings,
    }

    if pdf is None:
        warnings.append("PDF 文件未找到")
        return report

    try:
        raw = pdftotext(pdf)
    except (OSError, RuntimeError) as exc:
        warnings.append(f"pdftotext 失败: {exc}")
        return report

    if not raw.strip():
        warnings.append("pdftotext 输出为空")
        return report

    customers, suppliers, procedural, extract_warnings, template = extract_from_text(raw)
    warnings.extend(extract_warnings)
    report["template"] = template
    report["customers"] = customers
    report["suppliers"] = suppliers
    report["procedural"] = procedural
    return report


def main() -> int:
    args = parse_args()
    data_dir: Path = args.data_dir
    out_path: Path = args.out
    cwd = Path.cwd()

    if not data_dir.is_dir():
        print(f"extract_tables.py: data-dir not found: {data_dir}", file=sys.stderr)
        return 1

    meta_rows = load_metadata_rows(data_dir)
    if not meta_rows:
        print("extract_tables.py: no annual_reports.csv under data-dir", file=sys.stderr)
        return 1

    reports = [process_report(data_dir, row, cwd) for row in meta_rows]
    # 稳定排序：代码 + 财年
    reports.sort(
        key=lambda r: (
            str(r.get("stock_code") or ""),
            int(r.get("fiscal_year") or 0),
        )
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"reports": reports}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    ok = sum(1 for r in reports if r.get("customers", {}).get("rows"))
    print(f"wrote {out_path} ({len(reports)} reports, {ok} with customer rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
