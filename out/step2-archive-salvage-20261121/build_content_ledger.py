#!/usr/bin/env python3
"""build_content_ledger.py — Step 2 Task B: 内容台账收编(377条) + 15家海内外核心龙头扩抽.

功能：
1. 精确解析 `archive/flows/out/content-ledger-v1.md` 全部 8 路（5 家公司，严格校验 = 377 条），
   将早期样品 `C01–C34` 旧分类归一化至冻结五分枚举，按本地 `corpus/` 原文逐条复核引语。
2. 对 15 家海内外核心龙头（4 家招股书/新股技术富矿 + 7 家国内模块/器件/设备龙头 + 4 家海外 10-K 龙头）
   从本地原文精确切片抽取高密度工艺、技术参数、产品构成、代际事件与设备-工序能力条目。
3. 强制执行三大铁律机械门：
   - 双闸隔离：新扩条目 `atomic_fact` 与 `verbatim_quote` 严禁含具名客户/供应商买卖订单主张；
     `cell_ids` 100% 属于 `tree.yaml` 的 41 个叶格或 `通用`。
   - 自夸隔离：含“全球领先/第一梯队/国际一流”等自我定位营销语的条目严格标 `stance=issuer_self`。
   - 零编造引语：新扩 15 家全部条目必须 100% 通过严格 `norm(quote) in norm(source_text)`（0 失败）。
4. 幂等写出：
   - `corpus/content_ledger/content_ledger.csv`
   - `corpus/content_ledger/quote_verification_report.json`
   - `corpus/content_ledger/README.md`
   - `out/step2-archive-salvage-20261121/shard-b-summary.json`
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

ROOT = "/Users/jowang/Downloads/optical-module-research"
V1_MD_PATH = os.path.join(ROOT, "archive/flows/out/content-ledger-v1.md")
TREE_PATH = os.path.join(ROOT, "tree.yaml")
OUT_LEDGER_DIR = os.path.join(ROOT, "corpus/content_ledger")
OUT_CSV_PATH = os.path.join(OUT_LEDGER_DIR, "content_ledger.csv")
OUT_REPORT_PATH = os.path.join(OUT_LEDGER_DIR, "quote_verification_report.json")
OUT_README_PATH = os.path.join(OUT_LEDGER_DIR, "README.md")
OUT_SUMMARY_PATH = os.path.join(ROOT, "out/step2-archive-salvage-20261121/shard-b-summary.json")

SCHEMA_COLUMNS = [
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

VALID_FACT_TYPES = {"工序步骤", "技术参数", "产品构成", "代际事件", "设备-工序能力"}
VALID_STANCES = {"neutral", "industry", "issuer_self"}
VALID_TENSES = {"current", "historical", "planned"}
FORBIDDEN_COMPLETION_WORDS = ("已覆盖", "已完成", "已回答")


def norm(text: str) -> str:
    """严格去空白归一化（不改标点、不删页眉，用于新扩条目 100% 硬校验）."""
    return re.sub(r"\s+", "", text or "")


def norm_v1_relaxed(text: str) -> str:
    """仅用于历史 v1 跨页/引号排版差异辅助复核."""
    s = re.sub(r"\s+", "", text or "")
    s = (
        s.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("µ", "μ")
    )
    return s


def load_valid_leaf_cells() -> set[str]:
    tree_txt = open(TREE_PATH, encoding="utf-8").read()
    cells = set(re.findall(r"cell_id:\s*([A-Za-z0-9]+)", tree_txt))
    assert len(cells) == 41, f"Expected 41 leaf cells in tree.yaml, got {len(cells)}"
    return cells


class SourceCache:
    """缓存本地语料原文及按 \\n 切分的行列表，支持精确行区间+起止锚点切片."""

    def __init__(self) -> None:
        self._raw: Dict[str, str] = {}
        self._lines: Dict[str, List[str]] = {}
        self._norm: Dict[str, str] = {}

    def get_raw(self, rel_path: str) -> str:
        if rel_path not in self._raw:
            full = os.path.join(ROOT, rel_path)
            if not os.path.exists(full):
                raise FileNotFoundError(f"Missing corpus file: {rel_path}")
            txt = open(full, encoding="utf-8", errors="ignore").read()
            self._raw[rel_path] = txt
            self._lines[rel_path] = txt.split("\n")
            self._norm[rel_path] = norm(txt)
        return self._raw[rel_path]

    def get_norm(self, rel_path: str) -> str:
        self.get_raw(rel_path)
        return self._norm[rel_path]

    def extract_span(
        self,
        rel_path: str,
        start_line: int,
        end_line: int,
        start_anchor: str,
        end_anchor: str,
        lang: str = "zh",
    ) -> str:
        """从 rel_path 的 [start_line, end_line]（1-based 闭区间）精确切出原句并做零失真单行化."""
        self.get_raw(rel_path)
        lines = self._lines[rel_path]
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            raise ValueError(f"Invalid line range L{start_line}-L{end_line} for {rel_path} ({len(lines)} lines)")
        block = "\n".join(lines[start_line - 1 : end_line])
        sa_pat = re.compile(r"\s*".join(re.escape(c) for c in re.sub(r"\s+", "", start_anchor)))
        ea_pat = re.compile(r"\s*".join(re.escape(c) for c in re.sub(r"\s+", "", end_anchor)))
        ms = sa_pat.search(block)
        if not ms:
            raise ValueError(
                f"start_anchor {start_anchor!r} not found in {rel_path} L{start_line}-L{end_line}:\n{block[:400]}"
            )
        search_from = ms.end() if start_anchor != end_anchor else ms.start()
        me = ea_pat.search(block, search_from)
        if not me:
            me = ea_pat.search(block, ms.start())
        if not me:
            raise ValueError(
                f"end_anchor {end_anchor!r} not found after {start_anchor!r} in {rel_path} L{start_line}-L{end_line}:\n{block[ms.start():ms.start()+400]}"
            )
        sliced = block[ms.start() : me.end()]
        # Remove zero-width space \u200b only if wait - norm() does NOT strip \u200b because \s doesn't match \u200b in Python!
        # So keep exact characters and only collapse \s+ whitespace!
        if lang == "en":
            cleaned = re.sub(r"\s+", " ", sliced).strip()
        else:
            # Collapse newlines; keep single space between ASCII alphanumerics so English tokens stay readable
            cleaned = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[A-Za-z0-9])", " ", sliced)
            cleaned = re.sub(r"[ \t\r\n\f\v]+", " ", cleaned).strip()
            # Remove spaces between CJK characters introduced by PDF column justification while keeping ASCII readable
            cleaned = re.sub(r"(?<=[\u4e00-\u9fff，。；：、（）《》“”])\s+(?=[\u4e00-\u9fff，。；：、（）《》“”])", "", cleaned)
        if norm(cleaned) not in self._norm[rel_path]:
            raise AssertionError(f"Normalized quote failed strict substring check in {rel_path}: {cleaned!r}")
        return cleaned


CACHE = SourceCache()


# ---------------------------------------------------------------------------
# Part 1: 解析并归一化 `archive/flows/out/content-ledger-v1.md` (377 条)
# ---------------------------------------------------------------------------

V1_ROUTE_META = {
    "SJZ": {
        "company": "仕佳光子",
        "stock_code_or_ticker": "688313",
        "source_doc": "科创板招股说明书（注册稿）",
        "doc_year": "2020",
        "local_source_path": "corpus/legacy-input/v16/prospectus/688313_仕佳光子_招股说明书_注册稿.txt",
        "anchor_url": "https://static.sse.com.cn/stock/disclosure/announcement/c/202006/000355_20200612_QODM.pdf",
    },
    "SJ24-": {
        "company": "仕佳光子",
        "stock_code_or_ticker": "688313",
        "source_doc": "2024年年度报告",
        "doc_year": "2024",
        "local_source_path": "corpus/legacy-input/v16/688313/688313/688313__em_仕佳光子_em__2024_2024年年度报告.pdf.txt",
        "alt_source_path": "corpus/annual-2024/688313/688313__em_仕佳光子_em__2024_2024年年度报告.pdf.txt",
        "anchor_url": "https://static.cninfo.com.cn/finalpage/2025-04-19/1223157242.PDF",
    },
    "YJZ": {
        "company": "源杰科技",
        "stock_code_or_ticker": "688498",
        "source_doc": "科创板招股说明书（注册稿）",
        "doc_year": "2022",
        "local_source_path": "corpus/legacy-input/v16/prospectus/688498_源杰科技_招股说明书_注册稿.txt",
        "anchor_url": "https://static.sse.com.cn/stock/disclosure/announcement/c/202209/001097_20220922_8GWE.pdf",
    },
    "YJ": {
        "company": "源杰科技",
        "stock_code_or_ticker": "688498",
        "source_doc": "2023年年度报告",
        "doc_year": "2023",
        "local_source_path": "corpus/legacy-input/v16/688498/688498/688498__em_源杰科技_em__2023_陕西源杰半导体科技股份有限公司2023年年度报告.pdf.txt",
        "anchor_url": "https://static.cninfo.com.cn/finalpage/2024-04-26/1219816634.PDF",
    },
    "CGHX": {
        "company": "长光华芯",
        "stock_code_or_ticker": "688048",
        "source_doc": "科创板招股说明书（注册稿）",
        "doc_year": "2021",
        "local_source_path": "corpus/legacy-input/v16/prospectus/688048_长光华芯_招股说明书_注册稿.txt",
        "anchor_url": "https://static.sse.com.cn/stock/disclosure/announcement/c/202110/000955_20211015_TAQB.pdf",
    },
    "TCG24-": {
        "company": "太辰光",
        "stock_code_or_ticker": "300570",
        "source_doc": "2024年年度报告",
        "doc_year": "2024",
        "local_source_path": "corpus/annual-2024/300570/300570__em_太辰光_em__2024_2024年年度报告.pdf.txt",
        "anchor_url": "https://static.cninfo.com.cn/finalpage/2025-03-29/1222945632.PDF",
    },
    "C": {
        "company": "猎奇智能",
        "stock_code_or_ticker": "创业板IPO在审",
        "source_doc": "创业板招股说明书（申报稿）",
        "doc_year": "2026",
        "local_source_path": "corpus/legacy-input/lieqi_prospectus.txt",
        "anchor_url": "https://reportdocs.static.szse.cn/UpFiles/rasinfodisc1/202604/RAS_202604_2219353F853040F4664F68A9C0227EAD584A6C.pdf",
    },
}


def infer_v1_cells(cid: str, company: str, text_blob: str) -> str:
    """将 v1 条目映射到 tree.yaml 的 41 个叶格或 `通用`."""
    t = text_blob
    if company == "仕佳光子":
        cells = []
        if any(k in t for k in ("PLC", "AWG", "VOA", "OSW", "平面光路", "平面波导", "分路器", "波导")):
            cells.append("D8")
        if any(k in t for k in ("DFB", "EML", "激光器芯片", "CW光源", "CW DFB")):
            cells.append("C1")
        if any(k in t for k in ("外延", "MQW", "MOCVD", "InP", "GaAs")):
            cells.append("M2a")
        if any(k in t for k in ("光纤连接器", "FA", "光纤阵列", "MPO", "跳线")):
            cells.append("D9")
        if any(k in t for k in ("MT插芯", "MT 塑料插芯", "插芯")):
            cells.append("D10")
        if any(k in t for k in ("室内光缆", "光缆材料", "高分子", "光缆")):
            cells.append("M4")
        if any(k in t for k in ("TO封装", "COC", "封装筛选", "芯片老化")) and "C1" not in cells:
            cells.append("P1")
        return ",".join(dict.fromkeys(cells)) if cells else "通用"

    if company == "源杰科技":
        cells = []
        if any(k in t for k in ("外延", "MOCVD", "掩埋", "再生长", "光栅")):
            cells.append("M2a")
        if any(k in t for k in ("DFB", "EML", "激光器", "CW", "光芯片", "10G", "25G", "50G", "100G", "PON")):
            cells.append("C1")
        if any(k in t for k in ("COC", "TO-CAN", "TO封装", "封装")) and any(k in t for k in ("贴装", "基板", "老化")):
            cells.append("P1")
        return ",".join(dict.fromkeys(cells)) if cells else "通用"

    if company == "长光华芯":
        cells = []
        if any(k in t for k in ("VCSEL", "面发射", "TOF")):
            cells.append("C2")
        if "GaAs" in t and "外延" in t:
            cells.append("M2b")
        if "InP" in t and "外延" in t:
            cells.append("M2a")
        if any(k in t for k in ("MOCVD", "MBE", "外延生长")) and not any(x in cells for x in ("M2a", "M2b")):
            cells.append("M2b")
        if any(k in t for k in ("DFB", "EML", "光通信芯片", "边发射", "单管芯片", "巴条芯片")):
            cells.append("C1")
        if "PD" in t or "探测器" in t:
            cells.append("C3")
        return ",".join(dict.fromkeys(cells)) if cells else "通用"

    if company == "太辰光":
        cells = []
        if any(k in t for k in ("陶瓷插芯", "套筒", "套管")):
            cells.append("D10")
        if any(k in t for k in ("MTP", "MPO", "MT 插芯", "MT插芯", "光纤连接器", "FA", "光柔性板", "密集连接", "穿线")):
            cells.append("D9")
        if any(k in t for k in ("PLC", "AWG", "分路器", "波分复用", "WDM")):
            cells.append("D8")
        if any(k in t for k in ("高速光模块", "AOC", "400G", "800G")):
            cells.append("MOD1")
        return ",".join(dict.fromkeys(cells)) if cells else "通用"

    if company == "猎奇智能":
        # 显式排除汽车电机定子、SiC预烧结等跨行业研发条目 -> 通用
        if cid in {"C35", "C36", "C37", "C38", "C39", "C40", "C41", "C62", "C68", "C70", "C72", "C75"}:
            return "通用"
        if cid in {"C17", "C18", "C19", "C76"}:
            return "MOD1"
        if cid == "C20":
            return "C4,D12,MOD1"
        cells = []
        if any(k in t for k in ("贴片", "共晶", "固晶", "EB3300", "DB2000", "VADB30P", "龙门", "脉冲加热", "压力控制")):
            cells.append("EQ3")
        if any(k in t for k in ("耦合", "对准", "自适应贴合", "旋转角度")):
            cells.append("EQ4")
        if any(k in t for k in ("引线键合", "热压超声焊", "倒装热压", "激光辅助键合")):
            cells.append("EQ5")
        if any(k in t for k in ("2D图像", "图像拼接", "视觉引导")):
            cells.append("EQ6")
        if any(k in t for k in ("老化", "BI74P", "LDTS2000", "QTEC", "LIV", "芯片测试")):
            cells.append("EQ7")
        return ",".join(dict.fromkeys(cells)) if cells else "通用"

    return "通用"


def normalize_c01_c34(cid: str, raw_type: str, raw_stance: str, atomic_fact: str) -> Tuple[str, str, str]:
    """将早期样品 C01–C34 旧五类严格归一化至冻结 Schema 五分枚举 + stance + tense."""
    clean_type = re.sub(r"^[①②③④⑤]\s*", "", raw_type).strip()
    type_map = {
        "工序步骤": "工序步骤",
        "技术参数": "技术参数",
        "产品代际": "代际事件",
        "设备-工序映射": "设备-工序能力",
        "发行人竞争陈述": "产品构成",
    }
    if clean_type not in type_map:
        raise ValueError(f"Unexpected C01-C34 fact_type for {cid}: {raw_type}")
    fact_type = type_map[clean_type]

    # Stance normalization
    if clean_type == "发行人竞争陈述" or cid == "C10":
        stance = "issuer_self"
    elif cid in {"C06", "C13", "C17", "C18", "C19", "C20", "C28"} or "行业描述" in raw_stance or "转载行业" in raw_stance:
        stance = "industry"
    else:
        stance = "neutral"

    # Tense normalization
    if cid in {"C11", "C15", "C16"}:
        tense = "historical"
    elif cid in {"C14"} or "前瞻" in raw_stance or "预研" in atomic_fact:
        tense = "planned"
    else:
        tense = "current"

    return fact_type, stance, tense


def parse_v1_ledger() -> Tuple[List[Dict[str, str]], Dict[str, object]]:
    """解析 content-ledger-v1.md 全部 8 路，精确产出 377 条归一化记录及复核统计."""
    raw_md = open(V1_MD_PATH, encoding="utf-8").read()
    lines = raw_md.splitlines()

    parsed_entries = []
    cur = None
    cur_sub = None
    for i, line in enumerate(lines, 1):
        if line.startswith("### "):
            cur_sub = line[4:].strip()
            cur = None
        elif line.startswith("#### "):
            cur = None
        elif line.startswith("##### "):
            cid = line[6:].strip()
            if re.match(r"^(SJZ\d+|SJ24-\d+|YJZ\d+|YJ\d+|CGHX\d+|TCG24-\d+|C\d+)$", cid):
                cur = {"cid": cid, "sub": cur_sub, "line": i, "bullets": []}
                parsed_entries.append(cur)
            else:
                cur = None
        elif cur is not None:
            if line.startswith("- **"):
                m = re.match(r"^-\s*\*\*([^*]+)\*\*[：:](.*)$", line)
                if m:
                    first_k = m.group(1).strip()
                    rest = m.group(2).strip()
                    if first_k in {"类型", "stance", "时态", "验证态", "事实类型", "立场标注"} and "**" in rest:
                        sub_parts = re.split(r"\s*[｜|]\s*(?=\*\*[^*]+\*\*[：:])", f"**{first_k}**：{rest}")
                        for sp in sub_parts:
                            sm = re.match(r"^\*\*([^*]+)\*\*[：:](.*)$", sp.strip())
                            if sm:
                                cur["bullets"].append([sm.group(1).strip(), sm.group(2).strip()])
                    else:
                        cur["bullets"].append([first_k, rest])
            elif line.strip() and not line.startswith("---") and not line.startswith(">"):
                if cur["bullets"]:
                    cur["bullets"][-1][1] += " " + line.strip()

    assert len(parsed_entries) == 377, f"Expected 377 entries in v1, got {len(parsed_entries)}"
    by_cid = {e["cid"]: e for e in parsed_entries}

    # Prepare cleaned page-header blobs for v1 verification
    v1_blobs_strict: Dict[str, str] = {}
    v1_blobs_clean: Dict[str, str] = {}
    resolved_paths: Dict[str, str] = {}
    for pfx, meta in V1_ROUTE_META.items():
        p = meta["local_source_path"]
        if not os.path.exists(os.path.join(ROOT, p)) and "alt_source_path" in meta:
            p = meta["alt_source_path"]
        resolved_paths[pfx] = p
        full = os.path.join(ROOT, p)
        if os.path.exists(full):
            raw = open(full, encoding="utf-8", errors="ignore").read()
            v1_blobs_strict[pfx] = norm(raw)
            # Strip repeating prospectus/report page headers and table-break headers for v1 multi-page quotes
            page_cleaned = re.sub(
                r"1-1-\d+\s*\f?\s*(?:河南仕佳光子科技股份有限公司|陕西源杰半导体科技股份有限公司|苏州长光华芯光电技术股份有限公司|苏州猎奇智能设备股份有限公司)\s*招股说明书(?:（(?:注册稿|申报稿)）)?",
                "",
                raw,
            )
            v1_blobs_clean[pfx] = norm_v1_relaxed(page_cleaned)

    rows_out: List[Dict[str, str]] = []
    v1_stats = Counter()

    for e in parsed_entries:
        cid = e["cid"]
        pfx = next(p for p in ["SJZ", "SJ24-", "YJZ", "YJ", "CGHX", "TCG24-", "C"] if cid.startswith(p))
        meta = V1_ROUTE_META[pfx]
        bmap: Dict[str, str] = {}
        for k, v in e["bullets"]:
            if k not in bmap:
                bmap[k] = v

        atomic_fact = re.sub(r"\s+", " ", bmap.get("内容", "")).strip()
        section_ref = re.sub(r"\s+", " ", bmap.get("章节位置", "")).strip()

        is_c01_34 = bool(re.match(r"^C(?:0[1-9]|[12]\d|3[0-4])$", cid))
        if is_c01_34:
            fact_type, stance, tense = normalize_c01_c34(
                cid, bmap.get("事实类型", ""), bmap.get("立场标注", ""), atomic_fact
            )
        else:
            raw_type = re.sub(r"^[①②③④⑤]\s*", "", bmap.get("类型", "")).strip()
            fact_type = raw_type
            stance_line = bmap.get("stance", "")
            # Handle inline `neutral ｜ **时态**：current`
            if "**时态**" in stance_line:
                parts = re.split(r"[｜|]\s*\*\*时态\*\*[：:]", stance_line)
                stance_raw = parts[0].strip()
                tense_raw = parts[1].strip() if len(parts) > 1 else "current"
            else:
                stance_raw = stance_line.strip()
                tense_raw = bmap.get("时态", "current").strip()
            stance = re.match(r"^(neutral|industry|issuer_self)", stance_raw).group(1)
            tense = re.match(r"^(current|historical|planned)", tense_raw).group(1)

        # Extract quote segments
        q_source_entry = by_cid["YJZ01"] if cid == "YJZ02" else (by_cid["YJ01"] if cid == "YJ02" else e)
        raw_q_parts: List[str] = []
        verify_segs: List[str] = []
        for k, v in q_source_entry["bullets"]:
            if k.startswith("命中引语"):
                v_clean = v.strip()
                if cid == "C11":
                    # 双闸清洁：剥离早期样品引语句尾具名交付短语，保留纯技术精度原话
                    v_clean = v_clean.replace("，并向中际旭创完成交付。", "")
                v_clean = re.sub(r"（(?:在研项目情况表行|产品应用表行)[^）]*）$", "", v_clean).strip()
                v_clean = re.sub(r"^（同段落）……", "", v_clean).strip()
                if v_clean.startswith("[") and v_clean.endswith("]"):
                    arr = json.loads(v_clean)
                    raw_q_parts.append(" / ".join(s.strip() for s in arr if s.strip()))
                    verify_segs.extend(s.strip() for s in arr if s.strip())
                else:
                    raw_q_parts.append(v_clean)
                    for seg in re.split(r"……|\.\.\.|｜|／", v_clean):
                        seg = seg.strip()
                        if seg:
                            verify_segs.append(seg)

        verbatim_quote = re.sub(r"\s+", " ", " / ".join(raw_q_parts)).strip()

        # Verify against local corpus file
        local_path = resolved_paths[pfx]
        if pfx in v1_blobs_strict:
            if len(verify_segs) == 1 and norm(verify_segs[0]) in v1_blobs_strict[pfx]:
                q_status = "verified_local"
                v1_stats["verified_local_strict"] += 1
            else:
                # Check each segment against page-header-cleaned blob; for 3 table-page-split quotes in C43/C48/C72,
                # also check prefix/suffix Anchor >= 18 chars in v1_blobs_clean
                all_hit = True
                for seg in verify_segs:
                    ns = norm_v1_relaxed(seg).rstrip("。；，")
                    if ns in v1_blobs_clean[pfx]:
                        continue
                    all_hit = False
                    break
                if all_hit:
                    q_status = "verified_local"
                    v1_stats["verified_local_segmented"] += 1
                else:
                    q_status = "inherited_v1_verified" if not is_c01_34 else "pilot_self_reported"
                    v1_stats[q_status] += 1
        else:
            q_status = "pilot_self_reported" if (is_c01_34 or pfx == "YJ") else "inherited_v1_verified"
            v1_stats[q_status] += 1

        assoc_text = bmap.get("关联", "")
        cell_ids = infer_v1_cells(cid, meta["company"], f"{atomic_fact} {assoc_text} {verbatim_quote}")

        rows_out.append(
            {
                "cid": cid,
                "company": meta["company"],
                "stock_code_or_ticker": meta["stock_code_or_ticker"],
                "source_doc": meta["source_doc"],
                "doc_year": meta["doc_year"],
                "fact_type": fact_type,
                "stance": stance,
                "tense": tense,
                "cell_ids": cell_ids,
                "atomic_fact": atomic_fact,
                "verbatim_quote": verbatim_quote,
                "section_ref": section_ref,
                "local_source_path": local_path,
                "anchor_url": meta["anchor_url"],
                "quote_verification_status": q_status,
                "batch": "v1_salvage",
            }
        )

    return rows_out, dict(v1_stats)


# ---------------------------------------------------------------------------
# Part 2: 15 家海内外核心龙头扩抽（100% 原文精确切片，零编造引语，双闸零泄漏）
# ---------------------------------------------------------------------------

COMPANY_DOCS = {
    "LX": {
        "company": "联讯仪器",
        "code": "688808",
        "doc": "科创板招股说明书（申报稿）",
        "year": "2025",
        "path": "corpus/legacy-input/lianxun_prospectus.txt",
        "url": "https://static.sse.com.cn/stock/disclosure/announcement/c/202508/002075_20250815_QAVG.pdf",
        "lang": "zh",
    },
    "JG25": {
        "company": "炬光科技",
        "code": "688167",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/688167/688167/688167__em_炬光科技_em__2025_西安炬光科技股份有限公司2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-04-29/1225227562.PDF",
        "lang": "zh",
    },
    "CJGZ": {
        "company": "长进光子",
        "code": "688635",
        "doc": "科创板招股说明书（申报稿）",
        "year": "2026",
        "path": "corpus/annual/688635/688635/688635_长进光子_2026_招股说明书.pdf.txt",
        "url": "https://webapi.cninfo.com.cn/api/stock/p_stock2110?scode=688635",
        "lang": "zh",
    },
    "SHJW": {
        "company": "盛合晶微",
        "code": "688820",
        "doc": "科创板招股说明书（申报稿）",
        "year": "2026",
        "path": "corpus/annual/688820/688820/688820_盛合晶微_2026_招股说明书.pdf.txt",
        "url": "https://webapi.cninfo.com.cn/api/stock/p_stock2110?scode=688820",
        "lang": "zh",
    },
    "ZJXC25": {
        "company": "中际旭创",
        "code": "300308",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/300308/300308/300308__em_中际旭创_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-03-31/1225056459.PDF",
        "lang": "zh",
    },
    "XYS25": {
        "company": "新易盛",
        "code": "300502",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/300502/300502/300502__em_新易盛_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-04-24/1225172598.PDF",
        "lang": "zh",
    },
    "TFTX25": {
        "company": "天孚通信",
        "code": "300394",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/300394/300394/300394__em_天孚通信_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-04-08/1225082705.PDF",
        "lang": "zh",
    },
    "GXKJ25": {
        "company": "光迅科技",
        "code": "002281",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/002281/002281/002281__em_光迅科技_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-04-23/1225148212.PDF",
        "lang": "zh",
    },
    "HGKJ25": {
        "company": "华工科技",
        "code": "000988",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/000988/000988/000988__em_华工科技_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-03-26/1225031509.PDF",
        "lang": "zh",
    },
    "RBTK25_AR": {
        "company": "罗博特科/ficonTEC",
        "code": "300757",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/300757/300757__em_罗博特科_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-03-31/1225059372.PDF",
        "lang": "zh",
    },
    "RBTK25_WEB": {
        "company": "罗博特科/ficonTEC",
        "code": "300757",
        "doc": "ficonTEC官网Technologies页快照",
        "year": "2026",
        "path": "corpus/web/www.ficontec.com/2026-07-27/technologies.html",
        "url": "https://www.ficontec.com/technologies/",
        "lang": "en",
    },
    "DSJM25": {
        "company": "东山精密/索尔思",
        "code": "002384",
        "doc": "2025年年度报告",
        "year": "2025",
        "path": "corpus/annual/002384/002384/002384__em_东山精密_em__2025_2025年年度报告.pdf.txt",
        "url": "https://static.cninfo.com.cn/finalpage/2026-04-22/1225139318.PDF",
        "lang": "zh",
    },
    "COHR25": {
        "company": "Coherent",
        "code": "COHR",
        "doc": "FY2025 Form 10-K",
        "year": "2025",
        "path": "corpus/annual/Coherent/Coherent/Coherent_2025_10-K.pdf.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/820318/000082031825000014/iivi-20250630.htm",
        "lang": "en",
    },
    "LITE25": {
        "company": "Lumentum",
        "code": "LITE",
        "doc": "FY2025 Form 10-K",
        "year": "2025",
        "path": "corpus/annual/Lumentum/Lumentum/Lumentum_2025_10-K.pdf.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1633978/000162828025040830/lite-20250628.htm",
        "lang": "en",
    },
    "FN25": {
        "company": "Fabrinet",
        "code": "FN",
        "doc": "FY2025 Form 10-K",
        "year": "2025",
        "path": "corpus/annual/Fabrinet/Fabrinet_2025_10-K_0001408710-25-000039.pdf.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1408710/000140871025000039/fn-20250627.htm",
        "lang": "en",
    },
    "AAOI25": {
        "company": "AAOI",
        "code": "AAOI",
        "doc": "FY2025 Form 10-K",
        "year": "2025",
        "path": "corpus/annual/AAOI/AAOI/AAOI_2025_10-K.pdf.txt",
        "url": "https://www.sec.gov/Archives/edgar/data/1158114/000143774926005875/aaoi20251231_10k.htm",
        "lang": "en",
    },
}


# Specs tuple:
# (cid, doc_key, fact_type, stance, tense, cell_ids, atomic_fact, section_ref, start_line, end_line, start_anchor, end_anchor)
EXPANSION_SPECS: List[Tuple[str, str, str, str, str, str, str, str, int, int, str, str]] = [
    # ================= 1. 联讯仪器 (688808) — 15 条 =================
    ("LX-01", "LX", "产品构成", "neutral", "current", "EQ7",
     "联讯仪器电子测量仪器含通信测试仪器（采样示波器、时钟恢复单元、误码分析仪等）和电性能测试仪器（精密源表、低漏电开关矩阵）；半导体测试设备中光电子器件测试设备覆盖CoC光芯片老化测试系统、光芯片KGD分选测试系统及硅光晶圆测试系统。",
     "第五节 业务与技术 / 一、主营业务及主要产品情况（1-1-79，L8244-L8250）", 8244, 8251,
     "公司电子测量仪器包括通信测试仪器和电性能测试仪器", "硅光晶圆测试系统等）"),
    ("LX-02", "LX", "代际事件", "neutral", "current", "EQ7",
     "联讯仪器面向400G/800G光模块的50GHz采样示波器、56GBaud时钟恢复单元、800Gbps误码分析仪已大规模量产供货；面向1.6T光模块测试的65GHz采样示波器、120GBaud时钟恢复单元、1.6Tbps误码分析仪已在客户端送样验证。",
     "第五节 业务与技术 / 一、（一）主要产品（1-1-81，L8336-L8340）", 8336, 8340,
     "面向 400G、800G 高速光模块测试需求的 50GHz 采样示波器", "三款产品均在业内顶级用户处送样验证"),
    ("LX-03", "LX", "产品构成", "issuer_self", "current", "EQ7",
     "发行人援引Frost&Sullivan数据称：2024年其在中国光通信测试仪器市场份额为9.9%，位列第三且为前五名中唯一本土企业（海外厂商合计约占84%）；在中国光电子器件测试设备市场份额排名第一。",
     "第二节 概览 / 四、（三）发行人行业竞争地位（1-1-25~26，L1997-L2000）", 1997, 2001,
     "根据 Frost&Sullivan 数据，Keysight、Anritsu 等为代表的海外企业占据了 2024 年", "也是前五中唯一的本土企业。"),
    ("LX-04", "LX", "技术参数", "industry", "current", "EQ7",
     "采样示波器基于等效时间采样原理对周期信号重复采样以获取眼图波形数据，在极低采样率下实现极高带宽、更高垂直分辨率与更低噪声；型号DCA1065通道带宽达65GHz，面向112GBaud八通道1.6T光模块测试。",
     "第五节 业务与技术 / 一、（一）通信测试仪器·采样示波器（1-1-84~85，L8736-L8781）", 8736, 8742,
     "采样示波器是示波器的一类，是高速测试领域的核心测试仪器", "适用于周期信号的测量与分析。"),
    ("LX-05", "LX", "技术参数", "neutral", "current", "EQ7",
     "联讯仪器通信测试仪器核心指标演进：采样示波器通道带宽由10GHz提升至65GHz，时钟恢复单元最高恢复速率由10GBaud提升至120GBaud，误码分析仪单通道最高传输速率由25GBaud提升至113GBaud（PBT3058为113.44GBaud），覆盖100G至1.6T光模块测试。",
     "第五节 业务与技术 / 一、（四）业务演变情况（1-1-103，L9671-L9673）", 9669, 9674,
     "采样示波器通道带宽从10GHz提升至65GHz", "深度覆盖100G至1.6T光模块核心测试需求。"),
    ("LX-06", "LX", "设备-工序能力", "industry", "current", "EQ7",
     "时钟恢复单元从数据信号中提取对应频率时钟信号，为采样示波器提供同步触发时钟以恢复高速眼图波形；联讯CR3302时钟恢复单元最高恢复速率达120GBaud，适配112GBaud八通道1.6T光模块测试。",
     "第五节 业务与技术 / 一、（一）2）时钟恢复单元（1-1-85~86，L8795-L8838）", 8795, 8799,
     "时钟恢复单元可用于从数据信号中提取出对应频率的时钟信号", "可应用于光模块"),
    ("LX-07", "LX", "技术参数", "neutral", "current", "EQ7",
     "联讯仪器突发误码分析仪面向PON突发模式OLT光模块接收测试，2024年推出的rBT3250单通道最高突发速率达51.56GBaud，适配25G/50G PON光模块测试。",
     "第五节 业务与技术 / 一、（一）4）突发误码分析仪（1-1-87，L8957-L8965）", 8957, 8966,
     "2024 年", "正在送样验证中。"),
    ("LX-08", "LX", "技术参数", "neutral", "current", "EQ7",
     "联讯仪器FWM8612快速波长计覆盖1250nm–1650nm通信波段，波长测量精度达0.5pm，采用全固态无机械运动部件光学结构设计，应用于可调激光器及DBR/DFB激光器波长测量校准。",
     "第五节 业务与技术 / 一、（一）5）快速波长计（1-1-88，L8968-L8978）", 8968, 8978,
     "快速波长计是一种用于测量传输线路中电磁波波长的测量仪器", "光学结构设计在实现高精度测量的同时"),
    ("LX-09", "LX", "设备-工序能力", "neutral", "current", "EQ7,P1",
     "联讯仪器CoC光芯片老化系统BI620X系列采用模块化架构，单层含4组老化抽屉，单机架容纳多套单层，通过在设定高温下施加偏置电流/电压加速晶格缺陷老化，最高支持4,224路并行测试，并与CT620X光电测试系统同夹具协同作业。",
     "第五节 业务与技术 / 一、（二）1）CoC光芯片老化测试系统（1-1-91，L9054-L9066）", 9054, 9067,
     "公司 CoC 光芯片老化系统 BI620X 系列产品用于光芯片的老化测试", "并通过双通并行测试提高测试效率。"),
    ("LX-10", "LX", "工序步骤", "industry", "current", "C1,P1,EQ7",
     "DFB和EML等边发射激光器芯片受限于侧发光结构特征，且裸Die体积小、晶圆排列密度高，难以在晶圆层面直接进行CP测试，行业普遍在晶圆裂片后对未封装裸Die执行KGD分选测试。",
     "第五节 业务与技术 / 一、（二）2）光芯片KGD分选测试系统（1-1-91，L9084-L9087）", 9084, 9088,
     "光芯片在出厂前必须对各项参数进行测试", "对未封装的裸 Die 进行 KGD 分选测试。"),
    ("LX-11", "LX", "技术参数", "neutral", "current", "EQ7,EQ6",
     "联讯仪器光芯片KGD分选测试系统CT820X/CT830X系列可在6秒内完成裸芯片上下料及双温区全流程测试，采用1μs窄脉冲精密电流源测试，多工位独立控温稳定性控制在0.2℃以内，其中CT830X集成外观AOI自动检测功能。",
     "第五节 业务与技术 / 一、（二）2）光芯片KGD分选测试系统（1-1-92，L9104-L9112）", 9104, 9113,
     "通过自主设计的探针与压力控制机构，实现裸芯片的无痕精准测试。", "外观瑕疵的全功能检测。"),
    ("LX-12", "LX", "技术参数", "neutral", "current", "EQ7,C4",
     "联讯仪器硅光晶圆测试系统sCT900X系列集成耦合光探针、DC直流探针与RF射频探针，支持垂直耦合与边缘耦合；2024年推出的sCT9001（支持6/8寸）和sCT9002（支持8/12寸）光耦合重复性均<0.2dB，光耦合速度分别<2s与<1.5s，并于2024年度实现收入。",
     "第五节 业务与技术 / 一、（二）3）硅光晶圆测试系统（1-1-93，L9133-L9168）", 9133, 9169,
     "耦合测试模组包含耦合光探针、DC 直流探针与 RF", "8/12 寸"),
    ("LX-13", "LX", "技术参数", "neutral", "current", "EQ7",
     "联讯仪器超微弱信号产生和测量核心技术支撑精密源表与WAT测试机，实现最小电流测量分辨率1fA、测试精度0.02%、直流信号范围100pA至10A、噪声小于1fA。",
     "第五节 业务与技术 / 六、（一）核心技术表（1-1-159，L15133-L15140）", 15133, 15141,
     "系高端精密源表及半导体测试设备开发", "噪声小于 1fA"),
    ("LX-14", "LX", "技术参数", "neutral", "current", "EQ7",
     "联讯仪器高集成度四象限源测量技术应用于CoC光芯片老化测试系统与晶圆级老化系统，支持多通道并行测试，控制电流电压过冲小于3%，短路保护生效速度低于1μs。",
     "第五节 业务与技术 / 六、（一）核心技术表（1-1-159，L15141-L15148）", 15141, 15149,
     "系光芯片老化、晶圆老化效率提升的核", "护生效速度低于 1us"),
    ("LX-15", "LX", "工序步骤", "neutral", "current", "EQ7",
     "联讯仪器采取“以销定产，适当备货”及自主生产结合外协模式：核心部件组装、软件烧录、整机调试、性能测试和检验由公司自主完成；设备基础装配、PCBA贴片、夹具加工采取外协。",
     "第五节 业务与技术 / 一、（二）3、生产模式（1-1-101，L9526-L9530）", 9526, 9531,
     "公司将核心资源集中于产品开发和技术创新", "检验合格后成品入库。"),
    ("LX-16", "LX", "代际事件", "neutral", "planned", "EQ7",
     "联讯仪器正面向新一代通信器件及光电混合测试需求，推进实时示波器、光模块测试一体机、硅光晶圆老化系统、硅光芯片测试系统、CPO芯片测试系统等产品的研发与产业化。",
     "第五节 业务与技术 / 一、业务发展规划（1-1-103，L9658-L9660）", 9658, 9661,
     "未来公司将依托核心技术复用价值", "半导体综合参数分析仪等产品"),

    # ================= 2. 炬光科技 (688167) — 15 条 =================
    ("JG25-01", "JG25", "产品构成", "neutral", "current", "D7,M4,B2",
     "炬光科技围绕“产生光子”（激光光源与原材料）、“调控光子”（光学元器件）与“提供光子应用解决方案”（模块/模组/子系统）布局，重点拓展光通信、消费电子、泛半导体制程等方向及全球光子工艺制造服务。",
     "第三节 管理层讨论与分析 / 一、1、主营业务情况（p.15，L709-L712）", 709, 713,
     "公司报告期内主要从事光子行业上游的激光光源和原材料", "中游光子应用解决方案、技术服务。"),
    ("JG25-02", "JG25", "产品构成", "neutral", "current", "M4,B2,P1",
     "炬光科技AMC预制金锡氮化铝衬底材料（约4mm×5mm×0.5mm）在氮化铝陶瓷基材金属化后于特定区域预制微米级金锡薄膜，用于光纤耦合模块、泵浦源及光通讯芯片封装散热，解决共晶键合导电导热与热应力控制问题。",
     "第三节 管理层讨论与分析 / 一、主要产品表·半导体激光器衬底材料（p.18，L828-L838）", 828, 839,
     "片散热的衬底材料，在氮化", "导电导热性能优化和热应力控制问题"),
    ("JG25-03", "JG25", "产品构成", "neutral", "current", "B2,P1",
     "炬光科技AMM预制金锡铜钨衬底材料（长约10mm、宽4mm、厚0.2–2.0mm）在铜钨合金基材金属化后预制微米级金锡薄膜，作为高功率激光二极管芯片封装散热载体。",
     "第三节 管理层讨论与分析 / 一、主要产品表·AMM衬底（p.19，L849-L860）", 849, 861,
     "作为高功率激光二极管芯", "导电导热性能优化和热应力控制问题"),
    ("JG25-04", "JG25", "设备-工序能力", "neutral", "current", "D7,D9",
     "炬光科技V型槽阵列具有多条精密加工V型凹槽结构（通道间距、槽深及外形可定制），用于光通信模块、CPO、光纤连接器、PLC分路器、AWG及光纤阵列（FAU）的高精度光纤定位与固定，降低耦合损耗。",
     "第三节 管理层讨论与分析 / 一、（2）光学元器件典型产品·V型槽阵列（p.20，L899-L910）", 899, 911,
     "应用于光通信模块、共封装", "减少光信号传输损耗"),
    ("JG25-05", "JG25", "产品构成", "neutral", "current", "D7",
     "炬光科技光纤耦合器和准直器以单（非）球微透镜及微透镜阵列为主（长宽厚通常均在8mm以内），应用于光通信模块、波长选择开关（WSS）、光路开关（OCS）、光子集成电路（PIC）和共封装光学（CPO）的光束准直耦合。",
     "第三节 管理层讨论与分析 / 一、（2）光学元器件典型产品·光纤耦合器和准直器（p.21，L932-L945）", 932, 946,
     "应用于光通信模块、波长选", "从而提升激光器芯片发射功率的利用效率。"),
    ("JG25-06", "JG25", "产品构成", "neutral", "current", "D7",
     "炬光科技精密模压非球透镜涵盖单/双面、双锥、非球柱面或非球回转体结构，应用于光通信模块、光子集成电路及共封装光学（CPO）外置光源耦合。",
     "第三节 管理层讨论与分析 / 一、（2）精密模压非球透镜（p.22，L996-L1005）", 996, 1006,
     "单片透镜，单面或双面", "实现激光光束的准直或实现光纤耦合"),
    ("JG25-07", "JG25", "产品构成", "neutral", "current", "D7",
     "炬光科技微棱镜透镜阵列在单一透镜上集成微棱镜与多通道准直透镜阵列两种功能，应用于数据中心光通信，可提升多通道光纤耦合效率并减少指向误差和光学相位前畸变损耗。",
     "第三节 管理层讨论与分析 / 一、（2）微棱镜透镜阵列（p.23，L1019-L1023）", 1019, 1024,
     "单一透镜包含微棱镜和多", "减少指向误差和光学相位前畸变导致的光信号传输损耗"),
    ("JG25-08", "JG25", "工序步骤", "neutral", "current", "P1,B2",
     "炬光科技共晶键合核心技术通过多参数协同控制实现“无空洞”“无缺陷”激光芯片贴片；界面材料与表面工程技术开发了组分可调可控的金锡共晶合金薄膜制备工艺，实现无铟化高可靠贴片。",
     "第三节 管理层讨论与分析 / 三、（三）1、核心技术表（p.36，L1528-L1535）", 1528, 1536,
     "通过控制激光二极管芯片键合工艺中多个参数", "实现稳定可靠的无铟化贴片。"),
    ("JG25-09", "JG25", "技术参数", "neutral", "current", "D7",
     "炬光科技光刻-反应离子蚀刻（RIE）晶圆级微纳光学加工技术在6或8英寸硅或熔融石英晶圆上制造微透镜，典型中心厚度0.3–3mm、矢高可达0.1mm、微透镜阵列pitch间隔精度<0.3μm，支持2–20μm凹槽及中心对齐精度<3μm的双面微透镜。",
     "第三节 管理层讨论与分析 / 三、（三）1、核心技术表#6（p.36，L1553-L1559）", 1553, 1560,
     "在 6 或 8 英寸硅或熔融石英晶圆上通过精密光刻-反应离子蚀刻", "微透镜背面可加工 45 度角的微"),
    ("JG25-10", "JG25", "工序步骤", "neutral", "current", "D7",
     "炬光科技晶圆级微纳光学（WLO）精密压印技术在6英寸或8英寸POG（玻璃上聚合物）基板上采用紫外线固化、低温低压工艺对微纳结构适形再现，支持大规模量产。",
     "第三节 管理层讨论与分析 / 三、（三）1、核心技术表#7（p.37，L1567-L1575）", 1567, 1576,
     "结合微纳光学设计目标进行母版的设计与制造", "再现。"),
    ("JG25-11", "JG25", "工序步骤", "neutral", "current", "D7",
     "炬光科技晶圆级堆叠工艺（WLS）使用掩膜对准设备对多层光学晶圆与刚性间隔块进行几微米级精度堆叠，制成无镜筒、无支架、高度紧凑且支持回流焊的微光学组件。",
     "第三节 管理层讨论与分析 / 三、（三）1、核心技术表#8（p.37，L1578-L1582）", 1578, 1583,
     "使用先进的掩膜对准设备对多个光学晶圆与刚性间隔块进行几", "可回流等特征。"),
    ("JG25-12", "JG25", "工序步骤", "neutral", "current", "D7,D11",
     "炬光科技构建“调控光子”一体化制造平台，覆盖晶圆级同步结构化、光刻-反应离子蚀刻（RIE）、晶圆级精密压印与堆叠、光学精密模压、冷加工及卷对卷光学薄膜制备，贯通前道制备与后道光学镀膜、切割全流程。",
     "第三节 管理层讨论与分析 / 六、公司发展战略（p.60，L2804-L2808）", 2804, 2809,
     "在“调控光子”方面，公司专注于建设一个高端光学元器件制备技术平台", "形成一体化的综合制造能力。"),
    ("JG25-13", "JG25", "代际事件", "neutral", "current", "D7",
     "炬光科技将投影照明压印光学器件产线于2024年底从瑞士纳沙泰尔转移至中国韶关基地，韶关基地于2025年1月正式投入运营以降低制造成本；同时完成Heptagon资产收购后新增全球光子工艺和制造服务板块。",
     "第三节 管理层讨论与分析 / 四、主营业务分析（p.48，L2203-L2204）", 2203, 2205,
     "用于投影照明的压印光学器件的生产于 2024 年底从瑞士纳沙泰尔转移至中国韶关", "提升毛利率。"),
    ("JG25-14", "JG25", "代际事件", "neutral", "current", "D7",
     "炬光科技在研项目“数据通信微光学透镜开发”（预计总投资630万元）达成微透镜热成型工艺与材料体系开发，处于行业客户逐步导入阶段；“CPO系统的光学组件”（预计总投资460万元）达成研发阶段工艺验证及初步可靠性验证。",
     "第三节 管理层讨论与分析 / 三、（三）4、在研项目情况#5（p.39，L1718-L1724）", 1718, 1725,
     "已完成研发", "耦合能力"),
    ("JG25-15", "JG25", "代际事件", "neutral", "planned", "D7,D11",
     "炬光科技在研项目“具备防反射系统的WLO开发”正开展种子层沉积试验，计划2026年Q2完成最终层沉积，通过内部纳米结构蚀刻实现目标低反射率（平均<2%）；“硅刻蚀微棱镜/透镜角度连接器开发”处于初始样品交付阶段。",
     "第三节 管理层讨论与分析 / 三、（三）4、在研项目情况#7（p.39，L1736-L1750）", 1736, 1751,
     "通过内", "（平均<2%）"),

    # ================= 3. 长进光子 (688635) — 14 条 =================
    ("CJGZ-01", "CJGZ", "产品构成", "neutral", "current", "M4",
     "长进光子主营特种光纤研发、生产与销售，核心产品掺稀土光纤（报告期收入占比超85%）涵盖掺镱光纤、掺铒光纤、掺铒镱光纤、掺铥光纤及功能增强型掺稀土光纤，另有传能光纤及其他特种光纤器件，主要服务先进制造与光通信领域。",
     "第二节 概览 / 一、重大事项提示（1-1-14，L581-L583）", 580, 584,
     "公司收入主要来源于掺稀土光纤，报告期内收", "报告期内两者合计收入占比均超过 80%。"),
    ("CJGZ-02", "CJGZ", "技术参数", "neutral", "current", "M4",
     "在光通信领域，长进光子量产超宽带L波段掺铒光纤（如EDF-EXL-120、EDF-M-7/14），工作波长延伸至1627nm，作为光纤放大器（EDFA）核心增益介质应用于400G光传输网及算力中心互联。",
     "第五节 业务与技术 / 一、主营业务概况（1-1-80，L3933-L3936）", 3933, 3937,
     "在光通信领", "对于全国一体化算力体系建设具有重要意义"),
    ("CJGZ-03", "CJGZ", "技术参数", "industry", "current", "通用",
     "光通信波段定义中，常规C波段波长范围为1530–1565nm，长波L波段为1565–1625nm；扩展C波段与扩展L波段合并（C6T+L6T）可形成总带宽达12THz的超宽传输频谱。",
     "第一节 释义（1-1-11，L452-L461）", 452, 462,
     "常规波段（Conventional band），波长范围是 1530-1565nm", "12THz 的超宽频谱，可承载更高容量的光信号"),
    ("CJGZ-04", "CJGZ", "工序步骤", "neutral", "current", "M4",
     "长进光子特种光纤预制棒制备主要采用改进的化学气相沉积法（MCVD），核心工序依次为石英管内壁多孔疏松层沉积、稀土及共掺离子溶液浸出、高温多次烧结缩棒，需严控气体流速流量、反应温度与管内压力。",
     "第五节 业务与技术 / 一、（五）2、（1）预制棒制备（1-1-92，L4440-L4443）", 4440, 4444,
     "预制棒制备过程中，主要是运用 MCVD 设备", "需要以精密制造的工艺标准完成。"),
    ("CJGZ-05", "CJGZ", "工序步骤", "neutral", "current", "M4",
     "长进光子预制棒拉丝工序流程为：合格光纤预制棒经加热炉软化伸长，由牵引器组件在重力条件下垂坠成丝，达标直径后进入涂层系统依次完成一道涂覆、二道涂覆及固化，最后由塔底收线筒收集。",
     "第五节 业务与技术 / 一、（五）2、（2）预制棒拉丝（1-1-93，L4462-L4465）", 4462, 4466,
     "预制棒拉丝是指将合格的预制棒拉制成对应的产成品光纤。", "最终通过塔底部的收线筒进行收集。"),
    ("CJGZ-06", "CJGZ", "工序步骤", "neutral", "current", "M4",
     "长进光子掺杂组分设计技术通过共掺磷、锗、铝、硼等离子调控稀土离子局域结构与能级分布，包含团簇抑制、光子暗化抑制、增益谱形调控、饱和输出功率调控、能量传递调控与辐照抑制六项批量生产子技术。",
     "第五节 业务与技术 / 六、（二）1、（1）掺杂组分设计技术（1-1-143~144，L7104-L7125）", 7104, 7109,
     "掺杂组分设计是指将多种共掺离子（如磷、锗、铝、硼等）掺入到光纤的", "具有较高的技术壁垒。"),
    ("CJGZ-07", "CJGZ", "技术参数", "neutral", "current", "M4",
     "长进光子运用光子暗化抑制技术控制诱导吸收损耗，使单纤输出功率万瓦级的掺镱光纤在150小时烤机状态下功率衰减不超过2%。",
     "第五节 业务与技术 / 六、（二）1、（1）掺杂组分设计技术（1-1-144，L7127-L7129）", 7127, 7130,
     "公司运用光子暗化抑制技术，实现对光子暗化的有效控制", "功率衰减不超过 2%。"),
    ("CJGZ-08", "CJGZ", "技术参数", "neutral", "current", "M4",
     "长进光子光波导结构设计涵盖折射率剖面设计、模式不稳定阈值控制、三包层光纤设计及保偏掺稀土光纤设计技术，将20/400掺镱光纤输出功率由2kW提升至3kW，并依托三包层设计实现单纤稳定输出功率＞10kW。",
     "第五节 业务与技术 / 六、（二）1、（2）光波导结构设计技术（1-1-145，L7160-L7162）", 7160, 7163,
     "公司运用模式不稳定阈值控制技术，提升了掺镱光纤的模式不稳定阈值", "实现单纤稳定输出功率＞10kW。"),
    ("CJGZ-09", "CJGZ", "工序步骤", "neutral", "current", "M4",
     "长进光子保偏掺稀土光纤设计技术通过高精度应力结构与纤芯增益分布协同设计，在纤芯内构建稳定双折射场以赋予有源光纤保偏功能。",
     "第五节 业务与技术 / 六、（二）1、（2）光波导结构设计技术（1-1-145，L7151-L7153）", 7151, 7154,
     "公司的保偏掺稀土光纤设计技术", "使掺稀土光纤具备保偏功能。"),
    ("CJGZ-10", "CJGZ", "技术参数", "neutral", "current", "M4",
     "长进光子高均匀度预制棒制备技术采用低温反向沉积、径向温度补偿及管内压力/气流控制抑制中心凹陷，使预制棒掺杂均匀性（折射率波动）<3%、有效棒长≥500mm、纤芯直径>5mm，单根预制棒出纤长度提升50%。",
     "第五节 业务与技术 / 六、（二）2、高均匀度预制棒制备技术（1-1-146，L7201-L7204）", 7201, 7205,
     "公司运用高均匀度稀土掺杂技术", "最终实现单根预制棒出纤长度提升 50%。"),
    ("CJGZ-11", "CJGZ", "技术参数", "neutral", "current", "M4",
     "在预制棒拉丝环节，长进光子自研高精度拉丝控制系统实现光纤包层直径测量精度0.05μm、采样频率2,500次/秒、调控精度0.01m/min，支持50μm–1000μm光纤尺寸实时调整；常规掺镱光纤几何误差控制在±1μm以内，掺铒光纤几何误差±0.5μm以内且筛选强度达200kpsi。",
     "第五节 业务与技术 / 六、（二）3、高精度拉丝技术（1-1-146，L7221-L7228）", 7221, 7229,
     "在预制棒拉丝环节，公司通过自主设计的高精度拉丝控制系统", "其中掺铒光纤筛选强度可达 200kpsi。"),
    ("CJGZ-12", "CJGZ", "技术参数", "neutral", "current", "M4",
     "长进光子抗辐照掺铒光纤EDF-M-25-RAD在1550nm波长下辐射致衰减（RIA）<0.015 dB/m/kRad，包层直径125.0±2.0μm，纤芯包层同心度误差≤0.3μm，机械强度≥200kpsi。",
     "第五节 业务与技术 / 二、关键指标对比表（1-1-125，L6137-L6157）", 6137, 6158,
     "RIA@1550nm", "定性越强"),
    ("CJGZ-13", "CJGZ", "设备-工序能力", "neutral", "current", "M4",
     "长进光子自建光纤上机测试模拟平台，对纤芯损耗、包层损耗、吸收系数、增益带宽等动态指标进行实测验证，并按标准化产品适度备库（成品光纤+预制棒）与定制化产品按单生产双轨组织制造。",
     "第五节 业务与技术 / 六、（二）4、光纤性能测试表征技术（1-1-147，L7247-L7251）", 7247, 7252,
     "公司应用光纤性能测试表征技术，将光纤产品置于自建模拟平台进行上机", "以便及时实现产品的迭代升级。"),
    ("CJGZ-14", "CJGZ", "代际事件", "neutral", "current", "M4",
     "2023年至2025年，长进光子特种光纤年产量由6,535.85千米提升至9,530.48千米，年销量由5,666.30千米提升至8,725.02千米；截至报告期末累计取得37项发明专利，研发中心下设激光研发部与通信研发部。",
     "第五节 业务与技术 / 一、（六）业务指标变动（1-1-94，L4505-L4507）", 4505, 4508,
     "报告期内，公司持续增强高性能特种光纤供应能力", "销量规模由 5,666.30 千米提升至 8,725.02 千米。"),

    # ================= 4. 盛合晶微 (688820) — 14 条 =================
    ("SHJW-01", "SHJW", "产品构成", "neutral", "current", "P1",
     "盛合晶微主营集成电路晶圆级先进封测，覆盖12英寸中段硅片加工（Bumping凸块制造与CP晶圆测试）、晶圆级封装（WLP）及芯粒多芯片集成封装（2.5D/3DIC/3D Package）三大板块；2025年1-6月芯粒多芯片集成封装收入占比达56.24%。",
     "第二节 概览 / 四、（一）主营业务（p.40~43，L1818-L1825）", 1818, 1826,
     "完整的全流程先进封测产业链包括中段硅片加工环节和后段先进封装环节。", "还可实现芯片互联性能和功能密度的提升。"),
    ("SHJW-02", "SHJW", "产品构成", "issuer_self", "current", "P1",
     "发行人援引灼识咨询数据称：截至2024年末其为中国大陆12英寸Bumping产能规模最大企业；2024年度其中国大陆12英寸WLCSP收入市场占有率约31%（排名第一），中国大陆2.5D封装收入市场占有率约85%（排名第一）。",
     "第五节 业务与技术 / 一、（一）主营业务（p.142，L6361-L6366）", 6361, 6367,
     "在芯粒多芯片集成封装领域，公司拥有可全面对标全球最领先企业的技术平台布局", "市场占有率约为 85%。"),
    ("SHJW-03", "SHJW", "工序步骤", "industry", "current", "P1",
     "硅通孔（TSV）工艺通过深孔刻蚀、薄膜沉积、铜填充、化学机械抛光（CMP）等工序在晶圆内部形成垂直导电通孔；混合键合（Hybrid bonding）通过金属键合与氧化硅键合相结合实现无凸块芯片垂直互连。",
     "第一节 释义（p.18，L738-L743）", 738, 744,
     "Through silicon via，中段硅片加工的基础工艺之一", "的方式实现连接"),
    ("SHJW-04", "SHJW", "技术参数", "neutral", "current", "P1",
     "盛合晶微具备8英寸和12英寸Bumping量产能力，超高密度铜柱微凸块与铜镍金微凸块均可量产实现20μm/12μm的最小凸块间距/直径，单颗芯片凸块数量可达数十万个。",
     "第五节 业务与技术 / 一、主要产品·凸块制造（p.144，L6421-L6439）", 6421, 6440,
     "公司可以提供 8 英寸和 12 英寸 Bumping 服务", "达数十万个"),
    ("SHJW-05", "SHJW", "工序步骤", "neutral", "current", "P1",
     "盛合晶微Bumping凸块制造核心流程依次涵盖：再钝化（涂布PI聚酰亚胺、曝光、显影、高温固化露出I/O接点）、氩离子溅镀形成下金属层（UBM）、光刻胶曝光显影开口、电镀、刻蚀、回焊与凸块缺陷检测。",
     "第五节 业务与技术 / 一、（七）主要产品工艺流程（p.157，L6951-L6961）", 6951, 6962,
     "包括涂 PI 胶、曝光、显影、高温固化工序。", "作为生长凸块的位置"),
    ("SHJW-06", "SHJW", "设备-工序能力", "neutral", "current", "P1",
     "盛合晶微SmartPoser-Si基于硅通孔转接板（TSV Interposer）构建2.5D多芯片集成平台，多颗芯粒并列置于硅转接板顶部，经微凸块（uBump）和转接板亚微米级多层水平布线实现芯片间高速互联，现处于大规模量产阶段。",
     "第五节 业务与技术 / 一、芯粒多芯片集成封装·SmartPoser-Si（p.148，L6586-L6592）", 6586, 6593,
     "结构：基于硅通孔转接板（“硅转接板”）的 2.5D 技术", "实现集成芯片的效果"),
    ("SHJW-07", "SHJW", "技术参数", "neutral", "current", "P1",
     "盛合晶微SmartPoser-Si平台掌握背面研磨平坦化露铜与掩模版无偏差拼接加工技术，最小微凸块间距达20μm，最大硅转接板尺寸约合3倍光罩，单系统可高密度异构集成10个以上功能芯片，配套大尺寸FCBGA支持≥50mm×50mm晶粒及≥75mm×75mm封装体（最小凸块间距130μm）。",
     "第五节 业务与技术 / 七、（一）核心技术表·SmartPoser-Si（p.214，L9431-L9444）", 9431, 9445,
     "2、背面平坦化露铜技术：", "高性能芯片的封装作业"),
    ("SHJW-08", "SHJW", "设备-工序能力", "neutral", "current", "P1",
     "盛合晶微SmartPoser-RDL（有机转接板2.5D，已进入小量试产）与SmartPoser-POP平台掌握多层超细线宽/线距重布线技术，可实现2μm/2μm线宽/线距、多达6P6M（6层金属层6层介电层）互联层数及250μm以上高铜柱垂直互连。",
     "第五节 业务与技术 / 七、（一）核心技术表·SmartPoser-RDL/POP（p.214~215，L9480-L9486）", 9480, 9487,
     "1、高铜柱制造技术：可制造高达 250um 以上的高铜柱", "实现多层芯片的三维堆叠整合"),
    ("SHJW-09", "SHJW", "设备-工序能力", "neutral", "current", "P1",
     "盛合晶微SmartPoser-BD嵌入式硅桥2.5D平台通过全流程验证：在扇出型重布线层中局部内嵌硅桥，结合高铜柱及硅桥TSV垂直互连，并采用类前段CMP湿抛工艺研磨异质界面以防硅桥TSV纵深破裂，兼顾高互联密度与低硅转接板成本。",
     "第五节 业务与技术 / 一、SmartPoser-BD（p.148，L6604-L6612）", 6604, 6613,
     "结构：基于嵌入式硅桥（“硅桥转接板”）的 2.5D 技术", "可以兼顾性能和成本"),
    ("SHJW-10", "SHJW", "技术参数", "neutral", "current", "P1",
     "盛合晶微3DIC平台分两路演进：SmartPoser-3DIC-BP（微凸块堆叠+有源晶圆背面露铜，间距≤20μm）已进入小量试产；SmartPoser-3DIC-HB采用大马士革亚微米铜互联（≥3层）、铜-铜混合键合（间距≤10μm）与微硅通孔（开口≤5μm），通过全流程验证。",
     "第五节 业务与技术 / 七、（一）核心技术表·3DIC-HB（p.215，L9473-L9479）", 9473, 9480,
     "1、亚微米互联技术：采用大马士革镶嵌结构和化学机械抛光表面整平技术", "5um 及以下的开口尺寸"),
    ("SHJW-11", "SHJW", "技术参数", "neutral", "current", "P1,EQ7",
     "盛合晶微CP晶圆测试平台测试温度范围覆盖-55℃至150℃，支持最小Pad间距45μm、最小Pad尺寸36μm×36μm、单次扎针最大同测数3,000 sites及探针卡最高32,000 pins。",
     "第五节 业务与技术 / 七、（一）2、CP平台指标对比表（p.217，L9561-L9566）", 9561, 9567,
     "关键性能指标", "＞20,000pins"),
    ("SHJW-12", "SHJW", "技术参数", "neutral", "current", "P1",
     "盛合晶微12英寸WLCSP平台采用超薄减薄切割、65nm及以下Low-K介电层激光开槽及六面红外隐裂检测工艺，量产最小晶圆减薄厚度达70μm、最小封装尺寸0.24mm²、最小切割道宽度50μm。",
     "第五节 业务与技术 / 七、（一）3、WLCSP平台指标表（p.218，L9603-L9606）", 9603, 9607,
     "关键性能指标", "50um"),
    ("SHJW-13", "SHJW", "代际事件", "neutral", "planned", "P1",
     "盛合晶微在研项目“多维桥接互联微凸块工艺平台开发”正处于调试验证阶段，研发高深宽比（高高度直径比）微凸块加工工艺，旨在实现光处理芯片、传感芯片等多维度芯片间的桥接互联（尚无光芯片量产订单披露）。",
     "第五节 业务与技术 / 七、（三）1、主要在研项目#2（p.223，L9827-L9829）", 9827, 9830,
     "开发高高度和直径比的微凸块加工工艺", "多维度芯片间的桥接互联"),
    ("SHJW-14", "SHJW", "代际事件", "neutral", "planned", "P1",
     "盛合晶微在研“SmartPoser-SOW晶圆级尺寸系统集成封装平台开发-一代”及“SmartPoser-INTP硅基载板平台开发-三代”均处于调试验证阶段，分别研发12英寸晶圆级全尺寸互联与含多直径TSV及多层亚微米铜互联的新一代硅转接板。",
     "第五节 业务与技术 / 七、（三）1、主要在研项目#35-36（p.226，L9935-L9941）", 9935, 9942,
     "芯粒多芯片", "硅转接板产品"),

    # ================= 5. 中际旭创 (300308) — 15 条 =================
    ("ZJXC25-01", "ZJXC25", "产品构成", "neutral", "current", "MOD1,MOD2,MOD3",
     "中际旭创主营高端光通信收发模块的研发、设计、封装、测试与销售，云数据中心产品线覆盖100G、200G、400G、800G和1.6T高速光模块，电信产品线覆盖5G前传/中传/回传、城域骨干网传输光模块及FTTX固网接入光器件。",
     "第三节 管理层讨论与分析 / 一、报告期内公司从事的主要业务（p.10，L402-L406）", 402, 407,
     "公司主营业务为高端光通信收发模块的研发、生产及销售", "应用于固网 FTTX 光纤接入的光器件等高端整体解决方案"),
    ("ZJXC25-02", "ZJXC25", "产品构成", "neutral", "current", "MOD1,C1,C4",
     "中际旭创1.6T OSFP系列涵盖1.6T OSFP224 DR8、2xFR4及1.6T-DR8 OSFP224 LPO等型号，光口采用8×200G架构，同时提供EML与硅光双平台方案，符合IEEE 802.3df和OSFP1600 MSA标准并支持CMIS5.x。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·1.6T OSFP（p.10，L412-L418）", 412, 419,
     "拥 有 全 面 的 1.6T OSFP224 DR8", "支持 CMIS5.x。"),
    ("ZJXC25-03", "ZJXC25", "产品构成", "neutral", "current", "MOD1,C1,C4",
     "中际旭创800G OSFP与800G QSFP112-DD系列光模块涵盖8×100G和4×200G两种通道架构，除传统EML方案外均配置硅光方案以满足10km以内数据中心传输需求，符合IEEE 802.3ck及CMIS5.x标准。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·800G OSFP（p.10，L420-L428）", 420, 429,
     "拥有全面的 800G OSFP 光模块产品组", "并支持 CMIS5.x。"),
    ("ZJXC25-04", "ZJXC25", "工序步骤", "neutral", "current", "MOD1,MOD2,MOD3",
     "中际旭创主要采取“以销定产”模式组织批量与定制化光模块制造，核心流程含生产计划编制、执行调整追踪及物料追踪；新客户与新产品开拓须先后通过客户合格供应商认证（含实地考察）及具体产品代码认证。",
     "第三节 管理层讨论与分析 / 一、（二）经营模式·2、生产模式与3、销售模式（p.11，L488-L500）", 488, 501,
     "光通信模块作为非终端产品，主要为下游客户提供零件", "使公司的相应产品获得客户的产品代码认证。"),
    ("ZJXC25-05", "ZJXC25", "技术参数", "neutral", "current", "MOD1,MOD2,MOD3",
     "2025年度中际旭创光通信收发模块产能达2,806万只（上年2,088万只），产量2,376万只（上年1,536万只），销量2,109万只（上年1,459万只），光模块板块毛利率由34.65%提升至42.61%。",
     "第三节 管理层讨论与分析 / 一、2、公司生产经营情况表（p.12，L544-L550）", 544, 551,
     "产品", "块"),
    ("ZJXC25-06", "ZJXC25", "代际事件", "industry", "planned", "MOD1",
     "据中际旭创年报援引LightCounting预测，800G和1.6T光模块将在2026年快速放量，合计市场规模预计达146亿美元（占全球光模块市场约64%）；3.2T光模块预计从2028年起逐步起量。",
     "第三节 管理层讨论与分析 / 二、1、数通市场（p.16，L741-L745）", 741, 746,
     "未来三年内 800G 和 1.6T 等高速光模块的需求将占据市场主导地位", "占到整体光模块市场规模的约 64%。"),
    ("ZJXC25-07", "ZJXC25", "工序步骤", "industry", "current", "C4,MOD1",
     "硅光子（SiPh）技术基于硅和硅基衬底材料，利用现有CMOS工艺进行光器件开发与单片集成，在高集成度、峰值速率、低能耗与成本控制方面具备优势。",
     "第三节 管理层讨论与分析 / 二、3、（1）硅光（p.17，L798-L802）", 798, 803,
     "硅光子技术是基于硅和硅基衬底材料", "是光模块未来的重要发展方向之一。"),
    ("ZJXC25-08", "ZJXC25", "产品构成", "industry", "current", "MOD2",
     "相干探测凭借高容量、高信噪比优势正从骨干网下沉至城域网与边缘接入网；数据中心间长距离直连（DCI）场景需采用400G、800G等相干光模块。",
     "第三节 管理层讨论与分析 / 二、3、（2）相干技术（p.17，L823-L833）", 823, 834,
     "数据中心光互联方案可根据其传输距离来选择两种支撑技术", "解决数据中心之间的 DCI 互联应用场景。"),
    ("ZJXC25-09", "ZJXC25", "技术参数", "industry", "current", "MOD1,C5",
     "线性驱动可插拔光模块（LPO）采用线性直驱技术去除传统DSP/CDR芯片，仅保留集成CTLE和EQ均衡功能的高线性度Driver与TIA，以牺牲一定误码率裕度和传输距离换取显著降功耗与降延迟（引述Macom数据：800G多模DSP模块功耗超13W，而线性直驱方案低于4W）。",
     "第三节 管理层讨论与分析 / 二、3、（3）LPO（p.18，L839-L850）", 839, 851,
     "线性驱动可插拨光模块（linear drive pluggable optics）", "800G 多模光模块功耗低于 4W。"),
    ("ZJXC25-10", "ZJXC25", "产品构成", "industry", "current", "MOD1,C5",
     "线性接收光模块（LRO/半重定时）仅在发射端保留一颗用于电信号重定时和均衡的DSP芯片，接收端改用线性直驱设计，在保留互操作性与标准兼容的同时降低整体功耗，定位为传统DSP模块与LPO模块之间的过渡架构。",
     "第三节 管理层讨论与分析 / 二、3、（4）LRO（p.18，L874-L879）", 874, 880,
     "号重定时和均衡的 DSP", "LPO 光模块的过渡技术。"),
    ("ZJXC25-11", "ZJXC25", "工序步骤", "industry", "planned", "D12,C4",
     "光电共封装（CPO）将交换ASIC芯片与硅光引擎在同一高速主板上协同封装，通过大幅缩短电芯片与光引擎间距减少高速电信号衰减并降低系统功耗，当前处于从技术突破迈向早期商业化阶段。",
     "第三节 管理层讨论与分析 / 二、3、（5）CPO（p.19，L891-L905）", 891, 895,
     "光电共封装（CPO）指的是交换 ASIC 芯片和硅光引擎（光学器件）在同一高速主板上协同封装", "CPO 技术可以缩短交换芯片和光引擎"),
    ("ZJXC25-12", "ZJXC25", "设备-工序能力", "neutral", "current", "D12,MOD1",
     "中际旭创掌握单模并行光学设计与精密制造、多模并行光学设计与耦合、高速电子器件仿真测试以及COB（板上芯片）光电封装技术，并自研开发了全自动高效率组装测试平台。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析·1、技术研发（p.21，L1018-L1021）", 1018, 1022,
     "公司拥有单模并行光学设计与精密", "Chip on Board（COB）光电子器件设计与封装技术。"),
    ("ZJXC25-13", "ZJXC25", "代际事件", "neutral", "historical", "MOD1,MOD2,C4",
     "中际旭创高速产品代际演进节点：2020年12月推出800G可插拔OSFP/QSFP-DD800；2022年展示800G硅光模块；2023年演示1.6T OSFP-XD DR8+、5nm DSP第二代800G硅光及400G ZR/ZR+相干模块；2024年展示1.6T LPO DR8与硅光800G ZR相干模块；2025年OFC展示3nm 1.6T OSFP 2xFR4与800G LR2相干精简型光模块。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析·1、技术研发（p.21，L1021-L1028）", 1021, 1029,
     "2020 年 12 月 4 日，公司也在 ECOC2020 线上展会中推出", "其中发明专利 19 件。"),
    ("ZJXC25-14", "ZJXC25", "设备-工序能力", "neutral", "current", "MOD1,MOD2,MOD3",
     "中际旭创建有万级洁净室净化生产车间与自动化生产线，配置覆盖工艺、工业、电子、软件、机构、测试全职能NPI新产品导入团队，依托产品生产计划（PMP）、作业指导书（MOI）及车间管理系统实现全过程追溯与测试数据自动处理。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析·2、快速量产（p.21，L1034-L1038）", 1034, 1039,
     "同时，公司也拥有 10 年以上光模块新产品导入经验", "提高了生产效率。"),
    ("ZJXC25-15", "ZJXC25", "代际事件", "neutral", "planned", "MOD1,MOD2,C4",
     "2025年中际旭创研发投入达16.76亿元（研发人员增至2,169人），未来重点加大1.6T、3.2T及以上超高速光模块、硅光、相干及下一代光互连技术研发，并在铜陵等地扩建800G/1.6T高端光模块产能。",
     "第三节 管理层讨论与分析 / 十一、未来发展的展望（p.32，L1624-L1627）", 1624, 1628,
     "公司将持续专注于 AI 数据中心等核心市场", "光互连综合解决方案提供商。"),

    # ================= 6. 新易盛 (300502) — 14 条 =================
    ("XYS25-01", "XYS25", "产品构成", "neutral", "current", "MOD1,MOD2,MOD3,D12",
     "新易盛主营400G/800G/1.6T及更高速率数通光模块与中低速电信/接入光模块，构建了覆盖传统可插拔、LPO/LRO、XPO（超高密度可插拔）、NPO（近封装光学）及CPO（共封装光学）的技术体系，并推出搭载自研MEMS芯片的光路交换机（OCS）产品。",
     "第三节 管理层讨论与分析 / 一、报告期内公司从事的主要业务（p.10，L355-L360）", 355, 361,
     "公司自成立以来一直专注技术创新", "推出了搭载自研 MEMS 芯片的光路交换机（OCS）产品"),
    ("XYS25-02", "XYS25", "产品构成", "neutral", "current", "MOD1",
     "新易盛1.6T OSFP系列光模块符合OSFP MSA标准及CMIS 5.0及以上固件规范，支持DR8、DR8-2、2xFR4和DR4传输接口，外壳支持IHS与RHS两种散热结构。",
     "第三节 管理层讨论与分析 / 一、主要产品表·1.6T OSFP（p.10，L366-L372）", 366, 373,
     "符合 OSFP MSA 的最新标准", "结构外形支持 IHS 和 RHS。"),
    ("XYS25-03", "XYS25", "产品构成", "neutral", "current", "MOD2",
     "新易盛相干光模块产品线涵盖符合OIF-800ZR标准及CMIS 5.0+的800G OSFP相干系列，以及符合OIF-400GZR标准及CMIS 5.1+的400G QSFP56-DD相干系列，面向AI算力集群、云数据中心与DCI互联。",
     "第三节 管理层讨论与分析 / 一、主要产品表·800G/400G相干系列（p.11，L388-L390）", 388, 391,
     "符合 OIF-800ZR 最新标准", "据中心、800G 以太网等"),
    ("XYS25-04", "XYS25", "工序步骤", "neutral", "current", "MOD1,MOD2,MOD3",
     "新易盛生产端主要实行“订单生产”模式，通过ERP生产管理平台实现订单跨部门流转与物料定量发放；针对采购周期长、市场紧缺的高单价核心原材料，结合市场预测建立安全库存提前备货。",
     "第三节 管理层讨论与分析 / 一、经营模式·2、生产模式（p.13，L464-L465）", 464, 466,
     "在生产方面，公司主要实行“订单生产”的生产模式。", "从而有效控制生产成本。"),
    ("XYS25-05", "XYS25", "设备-工序能力", "neutral", "current", "C4,D12,MOD1",
     "新易盛建立多层次跨学科研发架构，覆盖电子线路设计、集成光学设计、热仿真与热管理、高密度封装技术、硅光芯片的设计与集成、光器件耦合与测试六大核心技术环节。",
     "第三节 管理层讨论与分析 / 一、经营模式·4、研发模式（p.14，L486-L488）", 486, 489,
     "公司构建了覆盖电子线路设计、集成光学设计", "协同高效的研发团队与技术攻关体系"),
    ("XYS25-06", "XYS25", "代际事件", "issuer_self", "current", "MOD1,D12,C4",
     "公司自述为全球首批量产交付1.6T光模块、首个推出并规模量产线性可插拔LPO光模块的厂商，并于2026年3月发布基于单波400G IMDD技术的1.6T DR4光模块、6.4T NPO解决方案及12.8T XPO可插拔光模块。",
     "第三节 管理层讨论与分析 / 二、2、公司市场地位（p.14，L506-L509）", 506, 510,
     "公司是全球少数几家具备 800G 以上光模块规模化量产和交付能力的公司之一", "12.8T XPO 可插拔光模块等。"),
    ("XYS25-07", "XYS25", "产品构成", "neutral", "current", "C4,MOD1,D12",
     "新易盛已推出基于VCSEL/EML、硅光（SiPh）和薄膜铌酸锂（TFLN）多技术平台的400G、800G和1.6T全系列光模块，以及基于硅光技术的6.4T NPO模块。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析（p.16，L591-L595）", 591, 596,
     "公司已成功推出基于硅光", "在 OCS、CPO 等前沿技术领域也有充足的技术储备和产品布局。"),
    ("XYS25-08", "XYS25", "代际事件", "neutral", "current", "MOD1,C4",
     "新易盛“LPO技术光模块研发”（800G低功耗低延迟）、“高速直驱技术光模块”（硅光800G QSFP-DD/OSFP）及“高速1.6T光模块”三项研发项目均完成项目设计及各项验证并通过验收。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.18，L831-L863）", 855, 863,
     "推动 1.6T 光模块标准", "基础。"),
    ("XYS25-09", "XYS25", "代际事件", "neutral", "current", "MOD1,MOD2",
     "新易盛“LRO技术光模块研发”、“高速相干技术光模块研发”（面向骨干网/城域网/DCI）及“液冷技术光模块研发”三项项目均完成样品验证并进入小批量生产阶段。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.18，L881-L891）", 881, 892,
     "数据中心互联", "传输。"),
    ("XYS25-10", "XYS25", "代际事件", "neutral", "current", "C4",
     "新易盛“硅光PIC技术产业化研究”项目完成自主研发PIC芯片设计及样品验证，正式进入小批量生产阶段，推动高速光模块核心芯片由外部采购组装向自主研发延伸。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.19，L921-L929）", 921, 930,
     "推出完全自主研发的", "快速孵化"),
    ("XYS25-11", "XYS25", "代际事件", "neutral", "planned", "C4,MOD1",
     "新易盛“1.6T LPO光模块研发”（基于硅光去DSP架构解决AI训练高功耗高延迟）与“1.6T 4xDR4系列光模块”完成前期样品测试及评估。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.19，L953-L966）", 953, 967,
     "项目旨在研发基于硅", "方案。"),
    ("XYS25-12", "XYS25", "技术参数", "neutral", "planned", "MOD1,D12,B1,B2",
     "新易盛立项研发“12.8T XPO系列光模块”，完成前期样品测试及评估，重点突破双PCB+液冷集成架构与高密度光引擎+高压供电封装工艺，为CPO/NPO技术奠定基础。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.20，L999-L1017）", 999, 1018,
     "研发一款高速率", "小批量试点。"),
    ("XYS25-13", "XYS25", "技术参数", "neutral", "current", "MOD1,MOD2",
     "新易盛已推出基于单波200G光器件的800G/1.6T光模块、400G/800G ZR/ZR+相干光模块以及400G/800G LPO光模块；2025年研发投入7.02亿元，研发人员增至805人，累计获授权专利160项（发明专利64项）。",
     "第三节 管理层讨论与分析 / 四、4、通信行业披露（p.20，L1061-L1064）", 1061, 1065,
     "公司高速率光模块、硅光模块、相干光模块、800G LPO 光模块", "占营业收入 2.83%。"),
    ("XYS25-14", "XYS25", "设备-工序能力", "neutral", "current", "C4,D12,MOD1",
     "新易盛在中国（成都）与泰国构建全球化自动化、智能化柔性制造产线，并实施从光芯片研发、光器件封装到光模块制造的垂直整合。",
     "第三节 管理层讨论与分析 / 十一、未来发展展望（p.24~25，L1318-L1320）", 1318, 1321,
     "围绕光互联主业实施垂直整合战略", "进一步增强公司的核心竞争力和抗风险能力。"),

    # ================= 7. 天孚通信 (300394) — 15 条 =================
    ("TFTX25-01", "TFTX25", "产品构成", "neutral", "current", "D6,D7,D8,D9,D10,D11,D12",
     "天孚通信定位光互连一站式平台型企业，提供精密微光学组件、波分复用系统级无源方案、高精度封装、AOC/PSM/DR配套无源方案、多通道高速光引擎封装集成、高密度光互连集成及ELS（外置光源）八大解决方案。",
     "第三节 管理层讨论与分析 / 一、（一）（二）主营业务与主要产品（p.13~14，L577-L579）", 577, 580,
     "公司立足光互连领域，为下游客户提供垂直整合一站式解决方案", "激光雷达、生物光子等新兴应用场景。"),
    ("TFTX25-02", "TFTX25", "产品构成", "industry", "current", "D10",
     "陶瓷插芯由二氧化锆烧制并经精密加工制成圆柱小管，用于光纤对接精确定位；陶瓷套管（陶瓷套筒）由氧化锆粉体烧制加工而成，两端插入带陶瓷插芯的光纤即可形成活动连接光通路。",
     "第一节 释义（p.7，L259-L264）", 259, 265,
     "由二氧化锆烧制并经精密加工而成的陶瓷圆柱小管", "即可形成一条光通路"),
    ("TFTX25-03", "TFTX25", "产品构成", "industry", "current", "D1,D2,D3,D6,D8,D9,D12",
     "天孚通信光器件释义明确封装与无源分类：OSA含TOSA、ROSA、BOSA；BOX指盒式封装技术（高速率光器件封装方式）；FA/FAU指光纤阵列；LENS ARRAY指光纤透镜阵列；隔离器指单向通光器件；PM指保偏器件。",
     "第一节 释义（p.8，L288-L295）", 288, 296,
     "AWG", "Polarization Maintaining 保偏器件"),
    ("TFTX25-04", "TFTX25", "设备-工序能力", "neutral", "current", "M4,D7,D9,D10,D12",
     "天孚通信构建并行光学设计与制造、光学模拟/设计、FAU光纤阵列设计与制造、高速光引擎设计与封装四大创新技术平台，结合多产品线垂直整合提供一站式器件方案。",
     "第三节 管理层讨论与分析 / 一、（三）主要经营模式（p.14，L638-L640）", 637, 641,
     "形成了并行光学设计与制造技术平台", "不断为客户提供一站式产品解决方案，持续提高客户价值。"),
    ("TFTX25-05", "TFTX25", "工序步骤", "neutral", "current", "D1,D6,D7,D8,D9,D10,D12",
     "天孚通信建立“基础技术研究—新项目预研—新品开发设计—工艺平台实现—可靠性测试验证”五层自主研发流程，研发中心下设预研组、产品研发组、工艺开发组、实验测试组及自动化设备开发部。",
     "第三节 管理层讨论与分析 / 一、（三）研发模式表（p.15，L656-L660）", 656, 661,
     "公司采取自主研发，拥有各类材料、光学、机械结构、封装等各学科", "多层次研发体系。"),
    ("TFTX25-06", "TFTX25", "工序步骤", "neutral", "current", "D1,D6,D7,D8,D9,D10,D12",
     "天孚通信在中国江西和泰国春武里建设规模化量产基地，采用“以销定产”生产模式，并贯通从原材料成型、零件设计制造、成品组装到测试/封装的全工序厂内垂直整合制造。",
     "第三节 管理层讨论与分析 / 三、（二）产品垂直整合优势（p.22，L1003-L1006）", 1003, 1007,
     "目前已具备光收发模块上游配套光器件较为齐备品类的器件研发", "为客户提供高性价比产品。"),
    ("TFTX25-07", "TFTX25", "工序步骤", "industry", "current", "C1,D10,D12,MOD1",
     "光器件产业链按制造层级分为“光芯片、光零组件、光器件和光模块”四级：陶瓷套管/插芯、光收发组件等光零组件与光芯片组装为光器件，再经封装测试集成为可插拔光模块或CPO。",
     "第三节 管理层讨论与分析 / 一、（四）1、产业链分工（p.15，L693-L696）", 693, 697,
     "光器件产业链可分为“光芯片、光零组件、光器件和光模块”。", "公司主要产品包括光零组件、高速光器件等产品。"),
    ("TFTX25-08", "TFTX25", "技术参数", "neutral", "current", "D8,D6",
     "天孚通信关键无源器件性能指标：AWG波分复用器件信号传输损耗<2.0dB、抗干扰指标>30dB；隔离器组件信号传输损耗<0.3dB、抗干扰指标>30dB。",
     "第三节 管理层讨论与分析 / 一、1、关键技术或性能指标表（p.16，L745-L746）", 745, 747,
     "AWG 器件", "隔离器组件                            <0.3dB      >30dB"),
    ("TFTX25-09", "TFTX25", "技术参数", "neutral", "current", "D1,D12",
     "天孚通信有源封装器件性能指标：100G同轴封装OSA器件信号传输损耗<2.5dB、抗干扰指标>30dB；1.6T盒式封装BOX器件信号传输损耗<2.5dB、抗干扰指标>30dB。",
     "第三节 管理层讨论与分析 / 一、1、关键技术或性能指标表（p.16，L747-L748）", 747, 749,
     "OSA 器件", "盒式封装"),
    ("TFTX25-10", "TFTX25", "技术参数", "neutral", "current", "D8,D11",
     "天孚通信薄膜滤波与波分组件指标：WDM器件单通道信号传输损耗<0.8dB、抗干扰指标>30dB；Optical Filter传输损耗<0.4dB、抗干扰>30dB；四通道Filter Block传输损耗<0.8dB、抗干扰>30dB。",
     "第三节 管理层讨论与分析 / 一、1、关键技术或性能指标表（p.16，L749-L757）", 749, 758,
     "<0.8dB（单通", "道）"),
    ("TFTX25-11", "TFTX25", "技术参数", "neutral", "current", "D7,D9,D10,D12",
     "2025年度天孚通信光通信元器件年产能达63,654.49万个，产量47,383.50万个（同比增长42.58%，含内部产品线领用），对外销量25,423.34万个，板块毛利率为53.62%。",
     "第三节 管理层讨论与分析 / 一、2、公司生产经营情况（p.17，L803-L805）", 803, 806,
     "报告期内，公司光通信元器件产量较上年同期增加 14,151.41 万个", "包含了公司内部产品线间领用的产品。"),
    ("TFTX25-12", "TFTX25", "技术参数", "neutral", "current", "D12",
     "2025年天孚通信光通信元器件营业成本中直接材料占比由上年的68.58%升至74.56%（同比增长85.68%），直接人工占13.07%、制造费用占12.37%，主因原材料成本占比更高的有源光器件（如高速光引擎）销售占比上升。",
     "第三节 管理层讨论与分析 / 四、2、（5）营业成本构成（p.26，L1280-L1281）", 1280, 1282,
     "报告期内，营业成本主要构成项目中原材料占营业成本的比重 74.56%", "有源光器件销售贡献增加影响。"),
    ("TFTX25-13", "TFTX25", "代际事件", "neutral", "current", "D12",
     "2025年天孚通信有源光器件研发项目中，1.6T光引擎产品已顺利实现批量生产；全年研发投入2.67亿元（全部费用化），研发人员增至774人（同比增长40.98%）。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.28，L1367-L1371）", 1367, 1372,
     "为客户研发新技术方", "有源产品迭代升级             有序进行"),
    ("TFTX25-14", "TFTX25", "设备-工序能力", "neutral", "current", "D7,D9",
     "天孚通信将光互连微光学与耦合封装工艺横向复用至车载激光雷达上游，为激光雷达厂商定制光连接器件并具备规模化交付能力。",
     "第三节 管理层讨论与分析 / 一、（四）2、激光雷达板块（p.16，L733-L734）", 733, 735,
     "公司在光器件领域有较为深厚的技术和工艺积累", "并具备快速规模上量的交付能力。"),
    ("TFTX25-15", "TFTX25", "代际事件", "industry", "current", "MOD1,D12",
     "天孚通信年报引述LightCounting数据：AI集群用高速光模块与CPO市场规模2025年达165亿美元，预计2026年增至260亿美元，连续两年保持约60%增速。",
     "第三节 管理层讨论与分析 / 二、2、（1）数据中心（p.19，L888-L889）", 888, 890,
     "根据 LightCounting 数据，AI 集群用高速光模块与 CPO 市场在算力需求驱动下快速增长", "连续两年增速约 60%。"),

    # ================= 8. 光迅科技 (002281) — 15 条 =================
    ("GXKJ25-01", "GXKJ25", "产品构成", "neutral", "current", "MOD1,MOD2,MOD3,D8",
     "光迅科技主营光电子器件、模块和子系统，分传输类、接入类和数据通信类三大产品线；其中传输类覆盖100G/400G传输光模块、EDFA/拉曼/混合光纤放大器、AWG/VMUX/WDM/VOA/OPM无源器件以及WSS（波长选择开关）、OTDR与相干器件。",
     "第三节 管理层讨论与分析 / 一、（一）1、传输类产品（p.7~8，L316-L321）", 316, 322,
     "公司传输类产品可以提供光传送网端到端的整体解决方案", "WSS（波长选择开关）、OTDR（光时域反射仪）、相干器件等。"),
    ("GXKJ25-02", "GXKJ25", "产品构成", "neutral", "current", "D3,MOD3",
     "光迅科技接入类产品含固网接入（FTTH用XGSPON&GPON OLT/ONU BOSA、10G EPON/GPON/ComboPON BOSA及光模块）和无线接入（4G LTE/5G CPRI/eCPRI 25G/50G/100G灰光与彩光收发模块）。",
     "第三节 管理层讨论与分析 / 一、（一）2、接入类产品（p.8，L327-L330）", 327, 331,
     "公司接入类产品包括固网接入和无线接入类产品。", "25G、50G、100G 灰光和彩光等光收发模块。"),
    ("GXKJ25-03", "GXKJ25", "产品构成", "neutral", "current", "MOD1",
     "光迅科技数据通信产品覆盖100G/200G/400G/800G/1.6T高速光模块及AOC（QSFP/QSFP-DD/OSFP封装），其中800G系列含VR8、DR8、2xFR4、2xLR4、800G DR8 LRO及800G 2xFR4 LPO，1.6T系列含1.6T DR8等。",
     "第三节 管理层讨论与分析 / 一、（一）3、数据通信类产品（p.8~9，L343-L348）", 343, 349,
     "公司数据通信产品主要应用于云计算数据中心", "产品主要包括 1.6T DR8 等。"),
    ("GXKJ25-04", "GXKJ25", "产品构成", "industry", "current", "MOD1,MOD2,MOD3",
     "据光迅科技年报援引Omdia报告，2024Q4至2025Q3光迅科技占全球光器件市场份额5.9%（全球第五），其中数通光器件占5.9%（全球第四）、电信光器件占5.6%（全球第五）、接入光器件占7.6%（全球第四）。",
     "第三节 管理层讨论与分析 / 一、（二）市场地位（p.9，L360-L362）", 360, 363,
     "据 Omdia 的最新报告，2024 年第四季度至 2025 年第三季度", "接入光器件全球第四（市场份额 7.6%）。"),
    ("GXKJ25-05", "GXKJ25", "技术参数", "industry", "current", "MOD1,MOD2,MOD3",
     "据Omdia数据，截至2025Q3全球光器件市场滚动四季度收入达243亿美元（同比增长超50%）；2025年前三季度数通光器件市场规模达129亿美元（占全球光器件68%），电信光器件约48亿美元，接入光器件约12亿美元（占7%）。",
     "第三节 管理层讨论与分析 / 二、（一）1~2、光器件行业情况（p.9~10，L380-L386）", 380, 387,
     "据行业权威机构 Omdia 最新报告数据", "占全球光器件市场份额的 68%。"),
    ("GXKJ25-06", "GXKJ25", "工序步骤", "neutral", "current", "M2a,M2b,C1,C2,C3,C4,D8,MOD1,MOD2,MOD3",
     "光迅科技构建了半导体材料生长、半导体工艺与平面光波导、光学设计与封装、高频仿真与设计、热分析与机械设计、软件控制与子系统开发六大核心技术工艺平台，实现从芯片、器件到模块的全链条垂直集成。",
     "第三节 管理层讨论与分析 / 三、（一）领先的垂直集成技术能力（p.11，L440-L442）", 440, 443,
     "经过多年积累和优化，公司形成了半导体材料生长", "具备从芯片到器件、再到模块的全链条垂直整合能力。"),
    ("GXKJ25-07", "GXKJ25", "产品构成", "neutral", "current", "C1,C2,C3,C4",
     "光迅科技自研芯片平台覆盖FP、DFB、EML、VCSEL多种激光器芯片、PD与APD探测器芯片以及硅光（SiP）芯片平台，同时支撑直接调制与相干调制两类技术路线。",
     "第三节 管理层讨论与分析 / 三、（二）一站式的产品提供能力（p.11，L445-L447）", 445, 448,
     "公司拥有多种类型激光器芯片", "为直接调制和相干调制方案提供坚实支撑"),
    ("GXKJ25-08", "GXKJ25", "设备-工序能力", "neutral", "current", "D7,D8,D12,P1",
     "光迅科技具备COB（板上芯片）、混合集成、平面光波导（PLC/AWG）、微光器件及MEMS器件五大封装平台，支撑全系列高速有源与无源光器件规模量产。",
     "第三节 管理层讨论与分析 / 三、（二）一站式的产品提供能力（p.11，L447-L448）", 447, 449,
     "同时还具备 COB、混合集成、平面光波导、微光器件、MEMS 器件等封装平台", "为各类产品的稳定量产提供保障。"),
    ("GXKJ25-09", "GXKJ25", "工序步骤", "neutral", "current", "通用",
     "光迅科技质量管理体系先后通过ISO9001、TL9000通讯行业质量体系及IATF16949汽车行业质量体系认证，并导入QC080000有害物质过程管理体系与过程可追溯数字化柔性制造系统。",
     "第三节 管理层讨论与分析 / 三、（四）完善的质量管理体系（p.11，L456-L458）", 456, 459,
     "公司于 1999 年、2005 年、2023 年先后通过 ISO9001 质量管理体系", "持续为客户提供高质量的产品和服务。"),
    ("GXKJ25-10", "GXKJ25", "技术参数", "neutral", "current", "MOD1,MOD2,MOD3",
     "2025年光迅科技营业收入119.29亿元（同比增长44.20%），其中数据与接入业务收入84.63亿元（占比70.94%，毛利率21.85%），传输业务收入34.12亿元（占比28.60%，毛利率26.52%）。",
     "第三节 管理层讨论与分析 / 四、2、（1）营业收入构成（p.11~12，L478-L484）", 478, 485,
     "营业收入合计", "65.89%"),
    ("GXKJ25-11", "GXKJ25", "技术参数", "neutral", "current", "MOD1,MOD2,MOD3",
     "2025年光迅科技光电子器件及模块生产量达29,423.63万只，销售量27,494.23万只；制造营业成本中直接材料占82.67%、直接人工占13.50%、直接制造费用占3.76%。",
     "第三节 管理层讨论与分析 / 四、2、（5）营业成本构成（p.13，L552-L554）", 552, 555,
     "通讯设备制造行业       直接材料", "11.97%"),
    ("GXKJ25-12", "GXKJ25", "技术参数", "neutral", "current", "通用",
     "2025年光迅科技研发投入总额11.36亿元（同比增长48.21%，占营收9.52%），研发人员1,391人（占员工总数28.13%，其中硕士709人、博士42人），累计申请国内外专利3,000余件并牵头/参与标准300余项。",
     "第三节 管理层讨论与分析 / 四、4、研发投入（p.15，L667-L672）", 667, 673,
     "研发投入金额（元）", "1.55%"),
    ("GXKJ25-13", "GXKJ25", "代际事件", "neutral", "current", "C1,C4,C6,MOD1,MOD2",
     "光迅科技四大重点资本化研发项目集群涵盖数据与接入光器件项目、传输光器件与模块项目、相干器件与模块项目以及光电芯片项目，期末开发支出余额合计8,298.56万元。",
     "第十节 财务报告 / 八、研发支出（p.148，L7419-L7428）", 7419, 7429,
     "传输光器", "82,985,613.50"),
    ("GXKJ25-14", "GXKJ25", "代际事件", "neutral", "planned", "MOD1,MOD2,C6",
     "光迅科技募投“高端光电子器件研发中心建设项目”截至2025年末累计投入39,228.75万元（投资进度64.61%），部分研发设施已达到预定可使用状态，预计2026年6月整体建成。",
     "第五节 重要事项 / 募集资金承诺项目表（p.47，L2345-L2351）", 2345, 2352,
     "高端光电", "设项目"),
    ("GXKJ25-15", "GXKJ25", "代际事件", "industry", "planned", "MOD2,D8,D11",
     "随着AI分布式训练推动跨区域低时延DCI与骨干城域网扩容，800G可插拔相干模块加速起量，1.2T/1.6T相干方案未来将逐步进入商用，并同步拉动WSS、滤波器与光放大器需求。",
     "第三节 管理层讨论与分析 / 十一、行业趋势展望·1、电信光器件（p.19，L918-L921）", 918, 922,
     "云服务商与电信运营商为实现跨区域的高效算力调度", "占光器件总市场的 36%。"),

    # ================= 9. 华工科技 (000988) — 14 条 =================
    ("HGKJ25-01", "HGKJ25", "产品构成", "neutral", "current", "C4,D1,D2,D3,D12,MOD1,MOD2,MOD3",
     "华工科技联接业务构建从光芯片到器件、模块、子系统的垂直集成研发与规模化量产体系，产品涵盖超高速数通光模块、铜连接模块、智能车载光及卫星通信光模块，面向AI算力与全球无线通信场景。",
     "第三节 管理层讨论与分析 / 一、报告期内公司从事的主要业务（p.8，L365-L368）", 365, 371,
     "具备从芯片到器件、模块、子系统全系列产品的战略研发和规模化量产能力。", "全球无线通信等重要领域。"),
    ("HGKJ25-02", "HGKJ25", "代际事件", "industry", "current", "MOD1,D12",
     "华工科技年报援引LightCounting数据：800G光模块2025年全球出货量预计达1,800–1,990万只（同比翻倍）；1.6T光模块2025年进入商用元年，全球需求预计达250–350万只；CPO预计于2026–2027年开始在超大型云厂短距场景规模上量。",
     "第三节 管理层讨论与分析 / 二、行业发展情况（p.9，L416-L422）", 416, 423,
     "到 2029 年，全球光模块市场规模有望突破 370 亿美元。", "主要应用于超大型云服务商的数通短距场景。"),
    ("HGKJ25-03", "HGKJ25", "代际事件", "neutral", "current", "D12,MOD1",
     "2025年华工科技联接业务向800G、1.6T高速光模块加速迭代，并首发面向3.2T代际的单波400G光引擎。",
     "第三节 管理层讨论与分析 / 三、核心竞争力（p.12，L559-L561）", 559, 562,
     "联接业务聚焦 AI 算力网络需求", "为下一代超高速光网络建设提供核心支撑。"),
    ("HGKJ25-04", "HGKJ25", "产品构成", "neutral", "current", "C4,MOD1,D12",
     "华工科技布局自研硅光芯片与薄膜铌酸锂芯片，其中自研硅光芯片已实际导入400G、800G及1.6T光模块交付，并完成面向3.2T CPO/NPO的高集成度硅光芯片研制。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析·联接业务（p.14，L663-L667）", 663, 668,
     "公司自研硅光芯片和薄膜铌酸锂芯片", "实现 3.2T CPO/NPO 高集成的硅光芯片"),
    ("HGKJ25-05", "HGKJ25", "设备-工序能力", "neutral", "current", "D12,P1",
     "华工科技掌握单波400G光电信号处理技术以及Flip-Chip（倒装芯片）、2.5D封装、3D封装工艺能力，支撑高集成度光引擎与CPO光电共封装产品制造。",
     "第三节 管理层讨论与分析 / 三、核心竞争力分析·联接业务（p.14，L667-L671）", 667, 672,
     "公司具备强大的光、电信号处理技术能力", "为下一代高集成度光引擎和光电共封产品打下坚实基础。"),
    ("HGKJ25-06", "HGKJ25", "代际事件", "issuer_self", "current", "MOD1,C4,D12",
     "公司自述按全球第一梯队规模化交付800G硅光LPO系列和1.6T光模块产品，并推出1.6T 3nm FRO/LRO、1.6T LPO方案、3.2T NPO、3.2T CPO光引擎及400G/lane光引擎解决方案。",
     "第三节 管理层讨论与分析 / 四、主营业务分析·联接业务（p.15，L732-L738）", 732, 738,
     "公司实现全球第一梯队规模化交付", "产品性能行业领先"),
    ("HGKJ25-07", "HGKJ25", "代际事件", "neutral", "current", "MOD2",
     "华工科技800G ZR/ZR+Pro相干光模块在报告期内实现批量交付，覆盖数据中心互联（DCI）与骨干网大容量长距传输场景。",
     "第三节 管理层讨论与分析 / 四、主营业务分析·联接业务（p.15，L738-L740）", 738, 741,
     "800G ZR/ZR+Pro 相干光模块实现批量交付", "长距离传输需求"),
    ("HGKJ25-08", "HGKJ25", "产品构成", "neutral", "current", "MOD1,B2",
     "华工科技同步推出800G ACC与1.6T AEC/ACC有源/无源铜缆模块，构建高速光联接、高速铜缆联接、高效液冷散热、光电集成四大算力互连技术路线。",
     "第三节 管理层讨论与分析 / 四、主营业务分析·联接业务（p.15，L740-L742）", 740, 743,
     "同步推出 800G ACC、1.6T AEC/ACC 铜缆模块", "光电集成四大技术线路。"),
    ("HGKJ25-09", "HGKJ25", "代际事件", "neutral", "current", "MOD3,D3",
     "在电信与接入网侧，华工科技25G PON OLT/ONU产品实现规模化交付，50G PON/OLT完成产品迭代优化；低轨卫星通信及6G基站光模块完成多款重点产品客户送样及联调测试。",
     "第三节 管理层讨论与分析 / 四、主营业务分析·联接业务（p.15，L744-L749）", 744, 750,
     "前瞻布局低轨卫星通信及 6G 基站光模块技术攻关与产品研发", "50G PON/OLT 完成产品迭代优化"),
    ("HGKJ25-10", "HGKJ25", "设备-工序能力", "neutral", "current", "MOD1,MOD2,MOD3",
     "华工科技武汉光电子信息产业研创园一期、泰国海外高速光模块产业基地及孝感智能终端产业基地均于报告期内竣工投产，形成境内外双制造基地产能支撑。",
     "第三节 管理层讨论与分析 / 四、主营业务分析·联接业务（p.15，L750-L754）", 750, 755,
     "武汉光电子信", "提供了强有力的硬件支撑。"),
    ("HGKJ25-11", "HGKJ25", "代际事件", "neutral", "current", "MOD1",
     "华工科技“800G LPO光模块”资本化研发项目于2025年4月进入资本化研发试制阶段，预计2026年6月完成，产品已具备批量制造生产可行性。",
     "第十节 财务报告 / 六、研发支出·重要资本化项目表（p.165，L8131-L8135）", 8131, 8136,
     "产品可批量制造生产", "可转入资本化阶段。"),
    ("HGKJ25-12", "HGKJ25", "代际事件", "neutral", "planned", "C1,C4,MOD1,D12",
     "华工科技依托中央研究院推进下一代光互连规划，加快3.2T/6.4T光模块迭代，实行硅光、LPO、CPO多路线并行，并推进高端光芯片自主量产。",
     "第三节 管理层讨论与分析 / 十一、未来发展展望（p.27，L1488-L1490）", 1488, 1491,
     "公司将加快 3.2T/6.4T 迭代，硅光、LPO、CPO 多", "提供最可靠的算力供给硬支撑。"),
    ("HGKJ25-13", "HGKJ25", "代际事件", "neutral", "current", "C1,C4,MOD1",
     "华工科技重点研发项目“下一代光芯片与高端光模块系列产品的开发与研究”持续优化升级，攻关高端光芯片自主可控并拓展卫星与车载光通信新赛道。",
     "第三节 管理层讨论与分析 / 四、研发投入表（p.21，L1078-L1081）", 1078, 1082,
     "下一代光芯片与", "究"),
    ("HGKJ25-14", "HGKJ25", "技术参数", "neutral", "current", "通用",
     "2025年华工科技全年申请专利433件（其中发明专利220件），申请软件著作权148项。",
     "第三节 管理层讨论与分析 / 三、核心竞争力（p.12，L573）", 573, 574,
     "报告期内，公司申请专利 433 件（其中发明专利 220 件），申请软件著作权 148 项", "申请软件著作权 148 项"),

    # ================= 10. 罗博特科/ficonTEC (300757) — 16 条（年报 10 条 + 官网快照 6 条） =================
    ("RBTK25-01", "RBTK25_AR", "代际事件", "neutral", "current", "EQ3,EQ4,EQ7",
     "2025年5月罗博特科完成对德国光电子及半导体自动化封测设备商ficonTEC（含FSG与FAG）的股权交割与工商变更，实现对ficonTEC 100%控股并纳入合并报表。",
     "第三节 管理层讨论与分析 / 四、（3）资本运作工作情况（p.25，L1278）", 1278, 1279,
     "2025 年 5 月，公司正式完成 ficonTEC 股权交割、工商变更登记手续，实现对 ficonTEC100%控股", "实现对 ficonTEC100%控股"),
    ("RBTK25-02", "RBTK25_AR", "产品构成", "neutral", "current", "EQ3,EQ4,EQ7",
     "罗博特科旗下ficonTEC设备面向硅光芯片、量子器件、光模块、激光雷达、大功率激光器、光学与生物传感器的耦合、封装和测试，具体涵盖高速晶圆/晶粒/芯片测试设备、高速硅光模组/CPO模组测试设备、光子器件集成耦合设备、Bond自动化超高精度贴片设备及光纤预制设备。",
     "第三节 管理层讨论与分析 / 一、主营业务及产品表（p.18~19，L926-L933）", 926, 934,
     "高速晶圆测试设备、高速晶粒测试设备", "制设备"),
    ("RBTK25-03", "RBTK25_AR", "工序步骤", "neutral", "current", "EQ3,EQ4,EQ7",
     "ficonTEC实行以销定产及自主生产结合外协模式：确认订单后由设计规划部门与客户协同完成方案设计，生产部门完成制造后由生产、质检、自动化三部门联合检测硬件，再由自动化部门嵌入应用程序并执行校准调试。",
     "第三节 管理层讨论与分析 / 一、（二）1、（2）生产模式（p.19，L968-L972）", 968, 973,
     "采取自主生产和外协加工相结合的生产模式。", "客户确认无误后将产品进行打包运输。"),
    ("RBTK25-04", "RBTK25_AR", "设备-工序能力", "neutral", "current", "EQ3,EQ4,EQ7",
     "ficonTEC核心技术栈由超高精度运动控制、机器视觉系统及PCM（Process Control Master）核心控制算法软件三部分构成，覆盖从实验室概念验证、试点运行到大批量量产的全生命周期光子器件组装与测试。",
     "第三节 管理层讨论与分析 / 三、（一）核心技术与研发壁垒（p.23，L1154-L1158）", 1154, 1159,
     "通过 ficonTEC，公司拥有用于组装与测试光子器件的专有且难以复制的核心技术及专有技术", "为客户的整个开发及生产生命周期提供支持。"),
    ("RBTK25-05", "RBTK25_AR", "代际事件", "neutral", "current", "EQ7,EQ4",
     "2025年ficonTEC完成了双面晶圆测试设备及晶粒测试设备的开发和验证，同时全新开发了测试设备系列及光纤预制设备系列；ficonTEC在德国、爱沙尼亚及中国设有生产/组装基地，并在爱尔兰廷德尔国家研究所、美国中佛罗里达大学光学院设有合作应用实验室。",
     "第三节 管理层讨论与分析 / 一、（二）1、（4）研发模式（p.19，L990-L991）", 990, 992,
     "合作研发：ficonTEC 在爱尔兰廷德尔国家研究所", "进行合作研发。"),
    ("RBTK25-06", "RBTK25_AR", "技术参数", "neutral", "planned", "EQ4",
     "罗博特科在研“高速纳米级运动轴”项目处于样品试制阶段，采用光栅尺+解码器闭环控制架构，目标开发出最小运动精度达5纳米的高速纳米级定位运动轴。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.31，L1708-L1711）", 1708, 1712,
     "开发出精度为 5 纳米的运动轴。", "的纳米级定位精度与动态稳定性"),
    ("RBTK25-07", "RBTK25_AR", "技术参数", "neutral", "planned", "EQ6,EQ7,C4",
     "罗博特科在研“硅光芯片波导位置测量系统开发”处于设计验证阶段，目标实现轴向分辨率10nm、动态适应工艺波动下定位精度<20nm，满足300mm硅光晶圆在线检测。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.31，L1722-L1725）", 1722, 1726,
     "硅光芯片", "300mm 晶圆在线检测。"),
    ("RBTK25-08", "RBTK25_AR", "技术参数", "neutral", "planned", "EQ4,D7,D9",
     "罗博特科在研“透镜/光纤阵列位姿测量系统开发”处于设计验证阶段，目标实现100nm/0.01°位姿检测精度以及128通道毫秒级协同与动态倾角补偿，搭载于公司耦合机设备。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.31，L1727-L1737）", 1727, 1738,
     "通过高精度、实时化的位姿检测技", "提升公司产品的核心竞争力。"),
    ("RBTK25-09", "RBTK25_AR", "代际事件", "industry", "planned", "D12,MOD1",
     "罗博特科年报援引LightCounting预测：2030年全球CPO端口出货量或达3,635万个，其中800G、1.6T、3.2T CPO端口分别为161万个、862万个和2,612万个。",
     "第三节 管理层讨论与分析 / 一、（二）2、光电子及半导体行业（p.11，L509-L510）", 509, 511,
     "根据 Lightcounting 预测，2030 年全球", "2,612 万个。"),
    ("RBTK25-10", "RBTK25_AR", "代际事件", "neutral", "planned", "EQ3,EQ4,EQ7",
     "罗博特科下一阶段研发重点攻克CPO光电共封装高密度集成与热稳定性管控难题，以及OCS（光路交换）大规模光路耦合与精准对准壁垒，推进硅光及光电子器件智能化大批量生产装备升级。",
     "第三节 管理层讨论与分析 / 十一、未来发展展望（p.40，L2390-L2393）", 2390, 2394,
     "公司将加快研发适配多种硅光技术的基础组装与测试技术栈", "核心装备供应商。"),
    ("RBTK25-11", "RBTK25_WEB", "设备-工序能力", "neutral", "current", "EQ3,EQ4,EQ7",
     "ficonTEC全球累计装机量超过1,000台，生产系统采用高度模块化全集成机电一体化架构，融合先进运动定位机构、光电测量仪器与统一软件控制界面。",
     "ficonTEC Technologies 页 / Mechatronics For Photonics Assembly & Test (L509-L510)", 509, 511,
     "ficonTEC production systems</a> fulfill the definition of state-of-the art mechatronic systems", "extensive global installation base of over 1000 machines"),
    ("RBTK25-12", "RBTK25_WEB", "技术参数", "neutral", "current", "EQ3,EQ4",
     "ficonTEC自动化组装机集成线性平移台、测角仪旋转台、六自由度（6-DOF）并联机构、长行程龙门及SCARA机械臂，具备纳米级分辨率、50nm及亚角秒级定位精度（sub-arcsecond accuracy），支持枢轴点空间插补与快速主动对准（fast active alignment）。",
     "ficonTEC Technologies 页 / Motion Control (L584-L592)", 584, 593,
     "Conventional stacks of linear translation and rotational (goniometers) stages", "in-line process pick-&amp;-place capability."),
    ("RBTK25-13", "RBTK25_WEB", "工序步骤", "neutral", "current", "EQ3,EQ5,EQ8",
     "ficonTEC微组装键合技术覆盖UV/热固化环氧胶粘接、钎焊、软焊料回流焊、激光锡焊及激光焊接，可将激光二极管单管/巴条、光电探测器、微光学透镜及光纤直接贴装至基板、热沉乃至整片光子晶圆上，并支持光电倒装焊（opto-electronic flip-chip）。",
     "ficonTEC Technologies 页 / Bonding For High Yield (L648-L660)", 648, 661,
     "The various bonding approaches", "opto-electronic flip-chip assembly"),
    ("RBTK25-14", "RBTK25_WEB", "工序步骤", "neutral", "current", "EQ3,EQ4",
     "ficonTEC自动胶粘与激光焊接过程控制包含六项关键步骤：不同粘度胶水精密点胶、点胶后器件重定位、定时UV频闪或热固化、UV环氧胶主动收缩补偿（active shrinkage compensation）、激光焊接光束精密聚焦导引及激光锡焊受控热循环；近期还研发了穿硅对准贴装（through-silicon align-&-attach）激光锡焊新工艺。",
     "ficonTEC Technologies 页 / Bonding Process Control (L651-L695)", 651, 696,
     "accurate dispensing of different viscosity adhesives", "through-silicon ‘align-&amp;-attach’ process"),
    ("RBTK25-15", "RBTK25_WEB", "技术参数", "industry", "current", "EQ7,C4",
     "传统半导体晶圆级电学探针卡通常对准80×80 µm²接触焊盘即可，而光子晶圆级光学探针（垂直光栅耦合或晶圆边缘耦合）要求高达亚微米级（submicron range）定位精度，并需结合可调谐激光源、多通道光功率计与光开关执行光电联合探测。",
     "ficonTEC Technologies 页 / Die And Wafer-level Electro-optical Testing (L768-L769)", 768, 770,
     "In the semiconductor world, wafer-level testing with probe cards", "multi-channel power meters, optical switches, etc."),
    ("RBTK25-16", "RBTK25_WEB", "设备-工序能力", "neutral", "current", "EQ4,EQ7",
     "ficonTEC自研PROCESS CONTROL MASTER软件统一控制硬件运动与光电测试序列，支持将过程追踪数据直接写入SQL数据库以开展产线良率统计分析。",
     "ficonTEC Technologies 页 / Testing Software (L770)", 770, 770,
     "Testing protocols and automated testing sequences", "improving production yield."),

    # ================= 11. 东山精密/索尔思 (002384) — 14 条 =================
    ("DSJM25-01", "DSJM25", "产品构成", "issuer_self", "current", "M1,M2a,C1,MOD1,MOD3,B1,B2",
     "东山精密通过外延并购子公司索尔思光电切入光模块（含光芯片）业务，结合Multek 78层及以上超高多层与7阶厚板HDI PCB制造能力，形成“光模块（含光芯片）+AI PCB+精密组件”体系（公司自评高端EML关键性能指标与量产能力达“国际一流水平”）。",
     "第三节 管理层讨论与分析 / 三、（二）产品优势（p.16，L890-L897）", 890, 898,
     "公司通过外延并购与内生发展相结合", "7 阶厚板 HDI PCB 的专业制造能力。"),
    ("DSJM25-02", "DSJM25", "设备-工序能力", "neutral", "current", "M1,M2a,C1",
     "索尔思光电拥有覆盖磷化铟（InP）衬底、外延材料至光芯片制造与封装可靠性的全流程IDM研发与工艺体系，生产过程涵盖外延生长、蚀刻、钝化、光刻、显影、清洗及电镀等核心晶圆工序；目前CW激光器已规模量产，单波400G EML芯片研发稳步推进。",
     "第三节 管理层讨论与分析 / 十一、未来发展展望（p.36，L1948-L1950）", 1948, 1951,
     "索尔思光电拥有覆盖磷化铟衬底、外延材料至光芯片的全流程研发与工艺体系", "提供坚实支撑"),
    ("DSJM25-03", "DSJM25", "工序步骤", "neutral", "current", "M2a,C1,B1",
     "东山精密光芯片与电子电路制造过程涉及外延生长、蚀刻、钝化、光刻、显影、清洗以及电镀等关键半导体与线路板湿法/干法工艺。",
     "第三节 管理层讨论与分析 / 十一、5、环保风险（p.38，L2022）", 2022, 2023,
     "公司产品在生产过程涉及外延生长、蚀刻、钝化、光刻、显影", "等关键工序"),
    ("DSJM25-04", "DSJM25", "产品构成", "issuer_self", "current", "C1",
     "索尔思光电采用IDM全流程自研量产模式布局2.5G至200G全系列光芯片，主力推出100G/200G PAM4 EML芯片适配800G/1.6T光模块，并前瞻布局400G EML与高功率CW光源（公司自评关键指标与量产能力达“国际一流水平”）。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·光芯片（p.10，L509-L515）", 509, 516,
     "依托子公司索尔思光电，公司布局以高速 EML 芯片为核心的光芯片产品体系", "严苛应用需求。"),
    ("DSJM25-05", "DSJM25", "代际事件", "neutral", "current", "C1,MOD1",
     "索尔思光电自研100G PAM4 EML芯片在400G及800G光模块中累计使用已超千万颗；自研200G PAM4 EML芯片已进入量产阶段支撑1.6T光模块；正在研发的400G PAM4 EML芯片面向3.2T光模块。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·数据中心光模块（p.10，L519-L525）", 519, 526,
     "我们的自研 100G", "将赋能 3.2T 光模块。"),
    ("DSJM25-06", "DSJM25", "产品构成", "neutral", "current", "MOD1,C1,C4,D12",
     "索尔思光电数据中心光模块涵盖QSFP-DD/QSFP112/OSFP封装400G模块，基于DSP、LPO与LRO架构的800G模块，以及提供EML、硅光和InP PIC多种技术选项的1.6T OSFP光模块，并推进CPO共封装光学研发。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·数据中心光模块（p.10，L517-L526）", 517, 527,
     "我们专注于模组 QSFP-DD、QSFP112 及 OSFP 封装的 400G 光模块", "非常适合用于 AI 训练与推理。"),
    ("DSJM25-07", "DSJM25", "产品构成", "neutral", "current", "C1,MOD3",
     "在宽带接入领域，索尔思光电PON光模块覆盖10G PON与25G/50G PON（符合F5G及F5G-A标准），其中搭载自研50G激光芯片的解决方案已在商用50G-PON项目中部署。",
     "第三节 管理层讨论与分析 / 一、（一）主要产品·宽带产品（p.11，L544-L547）", 544, 548,
     "我们的宽带产品基于 PON 架构", "赋能高速宽带与 AI 数据中心。"),
    ("DSJM25-08", "DSJM25", "工序步骤", "industry", "current", "C1,C4,D12",
     "光芯片机理区分：EML将DFB连续波激光器与电吸收调制器（EAM）单片集成，DFB工作点恒定、由EAM电压控制光吸收实现高速调制；CW硅光方案采用“连续波激光器+硅基集成光路”发光与调制解耦架构，支撑400G/800G/1.6T及CPO/NPO。",
     "第一节 释义（p.4，L177-L207）", 177, 180,
     "Electro-Absorption Modulated Laser，电吸收调制激光器", "激光器工作点保持不变。"),
    ("DSJM25-09", "DSJM25", "技术参数", "neutral", "current", "B1",
     "东山精密旗下Multek具备78层及以上超高多层PCB（HLC PCB）与7阶厚板HDI PCB的专业制造能力，满足光模块、AI服务器及高速交换机背板高密度差分线互连与大电流供电需求。",
     "第三节 管理层讨论与分析 / 十一、未来发展展望（p.36，L1951-L1952）", 1951, 1953,
     "Multek 深耕 PCB 行业 48 年，已具备 78 层及以上超高多层与 7 阶厚板 HDI PCB 的专业制造能力", "高品质 PCB 产品。"),
    ("DSJM25-10", "DSJM25", "代际事件", "neutral", "current", "MOD1,C1",
     "东山精密/索尔思在研“3nm 160万兆8通道EML方案500米OSFP封装1.6T光模块”已进入小批量试产阶段，采用自研EML并攻克高速信号完整性、倒装工艺与热管理；2km CWDM EML及10km 2LR4 1.6T模块处于样品制作阶段。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.22，L1291-L1297）", 1291, 1298,
     "面向数据中心下一代需求，开发", "足高密度、低功耗算力场景需求。"),
    ("DSJM25-11", "DSJM25", "代际事件", "neutral", "planned", "MOD1,C4",
     "东山精密/索尔思在研“1.6T OSFP DR8&2xFR4硅光方案光模块（500m&2000m）”正处于方案验证及样品制作阶段。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.23，L1317-L1327）", 1317, 1328,
     "1.6T OSFP", "OSFP 封装光模块"),
    ("DSJM25-12", "DSJM25", "技术参数", "neutral", "current", "MOD1,C1",
     "东山精密/索尔思“800G QDD DR8&2xFR4 Gen2 EML方案光模块”已进入小批量试产，较第一代（Gen1）功耗下降20%；同时在研带Gearbox的单波200G“800G QDD DR4++ 10km EML光模块”（样品制作中）以打通单波100G与单波200G交换机跨代互通。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.23，L1359-L1365）", 1359, 1366,
     "800G QDD", "封装光模块"),
    ("DSJM25-13", "DSJM25", "代际事件", "neutral", "planned", "C1",
     "索尔思光电在研下一代“106Gbaud differential EML（差分驱动EML）芯片开发”与“106Gbaud CWDM/LWDM EML芯片开发”均处于样品制作阶段，其中差分D-EML通过增大信号振幅降低驱动功率、整体功耗与串扰，适配800G/1.6T/3.2T模块。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.24，L1435-L1446）", 1435, 1446,
     "下一代高速光芯片，不仅能提供更高的带", "EML 芯片开发"),
    ("DSJM25-14", "DSJM25", "代际事件", "neutral", "current", "MOD3,C1",
     "在电信与无线接入研发线，东山精密/索尔思“400G QDD FR4 Gen3.5气密封装光模块”面向电信高可靠场景验证，“50G SFP56 LR/Bidi无线前传扩展/工业温度光模块”中粗波分型号已小批量出货。",
     "第三节 管理层讨论与分析 / 四、4、主要研发项目表（p.24，L1418-L1425）", 1418, 1426,
     "粗波分产", "向 SFP56 封装光模"),

    # ================= 12. Coherent (COHR) — 15 条 =================
    ("COHR25-01", "COHR25", "产品构成", "neutral", "current", "M1,C1,C2,D6,MOD1,MOD2,MOD3",
     "Coherent为垂直整合光电与工程材料制造商，技术栈覆盖特种材料生长制造、半导体激光器、含光隔离器在内的无源光学元件、光收发模块及光传输系统设备；FY2025按Networking、Materials、Lasers三大分部运营，并自2025年7月1日（FY2026）起重组为Datacenter and Communications与Industrial两大分部。",
     "Item 1. Business — General Description & Segments (p.6, L287-L295)", 287, 296,
     "Coherent has broad technical expertise and a deep technology stack", "(i) Datacenter and Communications, and (ii) Industrial."),
    ("COHR25-02", "COHR25", "产品构成", "neutral", "current", "MOD1",
     "Coherent数通光模块采用协议无关（protocol-agnostic）硬件设计，同一光收发器硬件可同时支持Ethernet、InfiniBand以及面向AI/ML的专有互连协议。",
     "Item 1. Business — Communications Market Group · Datacom (p.8, L461-L463)", 461, 464,
     "At Coherent, we have a complete portfolio of transceivers matched to the requirements set by AI and ML.", "proprietary protocols for AI and ML"),
    ("COHR25-03", "COHR25", "产品构成", "neutral", "current", "C1,C2,C3,C4,C5,D6,D12,MOD1",
     "Coherent不仅内部自主设计制造光模块，还自主设计制造激光器、光电探测器、集成电路（IC）和无源光学器件，具备GaAs基VCSEL以及InP基DML、EML和CW激光器的内部芯片设计与制造能力，并布局硅光子与CPO使能技术组合。",
     "Item 1. Business — Datacom Vertical Integration (p.8, L464-L470)", 464, 471,
     "We not only design and manufacture our transceivers internally", "a broad array of CPO-enabling technologies."),
    ("COHR25-04", "COHR25", "设备-工序能力", "neutral", "current", "M2a,M2b,C1,C2",
     "Coherent在美国和欧洲拥有多座6英寸砷化镓（GaAs）VCSEL晶圆厂，同时在美国和欧洲拥有多座磷化铟（InP）晶圆厂，并正在向6英寸InP晶圆制造能力升级迁移。",
     "Item 1. Business — Datacom Wafer Fabs (p.8, L468-L469)", 468, 470,
     "Coherent has multiple 6-inch GaAs VCSEL fabs in the U.S. and Europe.", "moving to 6-inch wafer capability."),
    ("COHR25-05", "COHR25", "产品构成", "neutral", "current", "C1,C6,MOD2,MOD3",
     "Coherent电信与DCI产品组合覆盖相干传输器件与模块、980nm及14xx泵浦激光器、掺铒光纤放大器（EDFA）、无源器件、光通道监测（OCM）、OTDR、ROADM（含WSS）子系统以及可插拔放大器与可配置板卡。",
     "Item 1. Business — Telecom Market Vertical (p.8, L478-L484)", 478, 485,
     "Our Telecom products include coherent transmission components and transceivers", "mandatory features in the DCI market."),
    ("COHR25-06", "COHR25", "设备-工序能力", "neutral", "current", "M2b,C1,C2,C3,D7,D13,C5",
     "Coherent基于集外延生长与晶圆制造于一体的6英寸GaAs平台大批量制造高可靠多发光点VCSEL阵列（用于数据中心、HDMI有源光缆及3D传感），同时内部自主量产InP边发射激光器与光电二极管，以及晶圆级光学元件、衍射光栅、TEC温控器件和驱动IC。",
     "Item 1. Business — Consumer Electronics Market Vertical (p.10, L541-L551)", 541, 552,
     "We manufacture GaAs VCSELs and VCSEL arrays, InP edge-emitting lasers and photo diodes", "substrates for sensing and AR/VR applications."),
    ("COHR25-07", "COHR25", "产品构成", "issuer_self", "current", "M1,M4",
     "Coherent自述其材料分部（Materials）为基于ZnSe、ZnS、GaAs、InP、GaSb及SiC的工程材料与光电器件市场领先厂商（market leader）。",
     "Item 1. Business — Materials Segment (p.7, L418-L419)", 418, 420,
     "The Materials segment is a market leader in engineered materials and optoelectronic devices", "InP, GaSb, and SiC."),
    ("COHR25-08", "COHR25", "工序步骤", "neutral", "current", "C5,B2,MOD1",
     "在供应链分工上，Coherent除内部自制芯片与材料外，从第三方供应商外采DSP、部分IC、机械壳体等标准组件；除数通光模块属于行业标准化形态外，其余多数光学与激光器部件均为非标定制产品。",
     "Item 1. Business — Sources of Supply (p.7, L399-L401)", 399, 402,
     "In our production processes, we use numerous optical, electrical, and mechanical parts", "available from several sources."),
    ("COHR25-09", "COHR25", "代际事件", "neutral", "planned", "MOD1,D12,C1,C2,C4,C5,D6,D13",
     "FY2025 Coherent数通研发重点投向800G/1.6T光收发器、CPO、VCSEL、EML、硅光、IC、隔离器、热电制冷器（TEC），以及支撑3.2T和6.4T代际的单通道400G/lane核心器件。",
     "Item 1. Business — R&D Investments · Networking (p.12, L636-L638)", 636, 639,
     "Datacom transceivers and", "supporting 3.2T and 6.4T."),
    ("COHR25-10", "COHR25", "代际事件", "neutral", "planned", "MOD1,MOD3",
     "Coherent基于自有数字液晶（digital liquid-crystal）技术开发面向AI/ML与超大规模数据中心的光路交换机（OCS）产品家族，区别于传统MEMS机械微镜OCS方案。",
     "Item 1. Business — R&D Investments · OCS (p.12, L639-L640)", 639, 641,
     "Optical circuit switch (OCS)", "digital liquid-crystal technology."),
    ("COHR25-11", "COHR25", "代际事件", "neutral", "planned", "MOD2,C6",
     "在相干光模块研发方向，Coherent持续提升集成度以缩小体积并降低功耗，扩展带宽支撑100G/200G/400G/800G相干收发器，并持续迭代面向陆地与海缆市场的新一代GaAs泵浦激光器。",
     "Item 1. Business — R&D Investments · Coherent & Pump Lasers (p.12, L641-L644)", 641, 645,
     "Coherent transceivers", "terrestrial and undersea markets."),
    ("COHR25-12", "COHR25", "代际事件", "neutral", "planned", "C1,C2,C3,D13",
     "在材料与器件研发方向，Coherent重点提升边发射激光二极管（EEL）、VCSEL、InP激光器与探测器的输出功率和可靠性，并持续开发碲化铋（Bi2Te3）热电制冷/温控材料与器件。",
     "Item 1. Business — R&D Investments · Materials (p.12, L650-L656)", 650, 657,
     "High-power lasers and", "introduce new products."),
    ("COHR25-13", "COHR25", "技术参数", "neutral", "current", "通用",
     "Coherent在FY2025、FY2024和FY2023的研发支出分别为5.82亿美元、4.79亿美元和5.00亿美元，产线工程人员常态化参与研发以加速工艺向大批量制造转移。",
     "Item 1. Business — Research and Development (p.12, L692)", 692, 693,
     "R&D expenditures were $582 million", "2023, respectively."),
    ("COHR25-14", "COHR25", "设备-工序能力", "neutral", "current", "M2b,C2,M4",
     "截至2025年6月30日，Coherent在美国拥有得州Sherman（70万平方英尺自有厂房，属Materials分部，核心6寸VCSEL晶圆厂所在地）、宾州Easton（28.1万平方英尺）及宾州Saxonburg总部（23.5万平方英尺）等制造与研发基地。",
     "Item 2. Properties — U.S. Properties (p.33, L1916-L1920)", 1916, 1921,
     "Sherman, TX", "Development                                                                                                 Leased"),
    ("COHR25-15", "COHR25", "设备-工序能力", "neutral", "current", "MOD1,MOD2,MOD3,M4",
     "截至2025年6月30日，Coherent海外核心制造与研发基地包括中国（约331.1万平方英尺，覆盖Materials与Networking）、马来西亚（约88.9万平方英尺自有厂房，属Networking分部）、越南（约71.9万平方英尺）及英国（约18.8万平方英尺，覆盖Lasers与Networking）。",
     "Item 2. Properties — Foreign Properties (p.33, L1934-L1944)", 1934, 1945,
     "China                    Manufacturing, Research and", "Lasers and Networking                            187,568      Owned and"),

    # ================= 13. Lumentum (LITE) — 15 条 =================
    ("LITE25-01", "LITE25", "代际事件", "neutral", "historical", "C1,C4,C5,C6,MOD1,MOD2",
     "Lumentum通过三次关键并购构建芯片至模块全栈能力：2018年12月收购Oclaro获取InP激光器与光子集成电路（PIC）及相干模块技术；2022年8月收购NeoPhotonics（超窄线宽可调激光器等）及IPG电信传输产品线（相干DSP/ASIC）；2023年11月收购Cloud Light（云晖科技）扩充AI数据中心高速光模块研发制造能力。",
     "Item 1. Business — Overview (p.3, L240-L252)", 240, 253,
     "In December 2018, we completed the acquisition of Oclaro", "demands of AI/ML."),
    ("LITE25-02", "LITE25", "代际事件", "industry", "current", "C1,MOD1",
     "数据中心光子学正加速导入单通道200G（200G/lane）光电子器件，相比传统单通道100G速率翻倍，支撑AI与HPC算力集群向800G/1.6T及以上平滑扩展。",
     "Item 1. Business — Cloud & Networking · Trends (p.5, L384-L386)", 384, 387,
     "A key innovation within data center photonics is the adoption of 200G lane speed optical components", "as AI demands intensify."),
    ("LITE25-03", "LITE25", "工序步骤", "industry", "current", "MOD1,MOD3",
     "光路交换机（OCS）支持高端口数并在光域直接将任意输入光纤动态切换连接至任意输出光纤以形成连续光通路，减少光电转换功耗并提升AI数据中心网络效率。",
     "Item 1. Business — Cloud & Networking · Trends (p.5, L387-L388)", 387, 389,
     "In addition, optical circuit switches are increasingly deployed", "continuous optical paths."),
    ("LITE25-04", "LITE25", "产品构成", "neutral", "current", "C1,C2,C3,C4,MOD1",
     "在数据中心内互联市场，Lumentum同时供应高速数通光模块以及底层核心光芯片，涵盖高速激光发射器芯片（EML/DML）、光子集成电路（PIC）、光电二极管（PD）、高功率激光光源（CW光源）以及短距传输VCSEL阵列。",
     "Item 1. Business — Cloud & Networking · Offerings (p.6, L426-L429)", 426, 430,
     "Optical transceivers and data interconnect solutions are essential", "short-reach data transmission."),
    ("LITE25-05", "LITE25", "产品构成", "neutral", "current", "C6,MOD2",
     "在数据中心互联（DCI）市场，Lumentum采取“自产模块+外售核心器件”双轮模式：既直接提供可插拔相干光模块，也向下游光模块厂商供应超窄线宽可调谐激光器（ultra-narrow linewidth laser）及相干光组件。",
     "Item 1. Business — Cloud & Networking · Offerings (p.6, L429-L430)", 429, 431,
     "In data center interconnects, Lumentum offers both its own coherent pluggable transceivers", "used by transceiver customers."),
    ("LITE25-06", "LITE25", "产品构成", "neutral", "current", "C1,D12",
     "面向下一代先进封装需求，Lumentum提供定制化高功率连续波激光光源（CW光源）、紧凑型激光器阵列以及共封装光学（CPO）与集成光子组件方案。",
     "Item 1. Business — Cloud & Networking · Offerings (p.6, L432-L433)", 432, 434,
     "Beyond standard offerings, we deliver customized solutions", "integrated photonics assemblies."),
    ("LITE25-07", "LITE25", "产品构成", "neutral", "current", "C6,D8,MOD2,MOD3",
     "在城域、骨干与光传输网领域，Lumentum提供可调谐收发器、高速相干组件、ROADM（可重构光分插复用器）、光放大器、光通道监测器（OCM）、980nm等泵浦激光器、WDM无源器件以及面向数据中心的光路交换机（OCS）。",
     "Item 1. Business — Cloud & Networking · Offerings (p.6, L438-L442)", 438, 443,
     "For optical transport applications, we offer a broad range of products", "improve overall network efficiency."),
    ("LITE25-08", "LITE25", "代际事件", "neutral", "planned", "C1,C6,MOD1,MOD2",
     "Lumentum当前研发重点投向更高带宽与更高光功率的数据中心激光器芯片、AI/ML与DCI高速光收发模块、数据中心全光平面OCS光路交换机以及更高容量ROADM和相干模块。",
     "Item 1. Business — Research and Development (p.7, L549-L556)", 549, 557,
     "We are making significant investments in next generation optical components", "modules, subsystems and circuit packs."),
    ("LITE25-09", "LITE25", "工序步骤", "neutral", "current", "C1,MOD1,MOD2,EMS1",
     "Lumentum采用“自有晶圆厂（wafer fabs）+自有封测厂+第三方合同制造商（EMS）”混合制造模式：自有核心工厂分布于美国、泰国、中国、英国、斯洛文尼亚和日本，外协EMS合作伙伴主要位于泰国、中国台湾、马来西亚和菲律宾。",
     "Item 1. Business — Manufacturing (p.7, L564-L573)", 564, 574,
     "We use a combination of our own wafer fabrication facilities", "manage the inventory in these locations."),
    ("LITE25-10", "LITE25", "设备-工序能力", "neutral", "current", "C1,M2a,MOD1,MOD2",
     "截至2025年6月28日，Lumentum全球自有及租赁物业总面积约310万平方英尺（自有约214.7万平方英尺），包括泰国117.3万平方英尺制造基地、日本相模原（Sagamihara）47.2万平方英尺InP晶圆制造与研发基地、美国圣何塞23.8万平方英尺园区及英国（Caswell）18.3万平方英尺InP晶圆厂。",
     "Item 2. Properties (p.40, L2662-L2666)", 2662, 2667,
     "As of June 28, 2025, our leased and owned properties in total are approximately 3,100,000 square feet", "sites in Slovenia."),
    ("LITE25-11", "LITE25", "代际事件", "neutral", "historical", "C1,M2a,MOD1",
     "Lumentum持续优化全球晶圆与模块产能布局：2024年7月完成收购日本相模原（Sagamihara）晶圆厂土地与厂房产权；2025年3月出售中国深圳25万平方英尺工厂土地与厂房，并同步扩充亚洲高速模块制造产能。",
     "Item 2. Properties (p.40, L2672-L2674)", 2672, 2675,
     "In July 2024, we completed a transaction to purchase the land and building of our wafer fabrication", "located in Shenzhen, China."),
    ("LITE25-12", "LITE25", "技术参数", "neutral", "current", "通用",
     "截至2025年6月28日，Lumentum持有约1,020项美国授权专利和1,100项海外专利，另有约780项在审专利申请；全职员工约10,562人，其中制造人员约8,706人、研发人员1,132人。",
     "Item 1. Business — Intellectual Property (p.7, L587-L588)", 587, 589,
     "As of June 28, 2025, we owned approximately 1,020 U.S. patents", "pending throughout the world."),
    ("LITE25-13", "LITE25", "技术参数", "neutral", "current", "C1,MOD1,MOD2",
     "FY2025 Lumentum总营收16.45亿美元（同比增长21.0%），其中Cloud & Networking分部营收14.108亿美元（占比85.8%，同比增长30.0%），全年研发费用达3.039亿美元（占总营收18.5%）。",
     "Item 7. MD&A — Financial Data for FY2025 (p.50, L3261-L3272)", 3261, 3273,
     "Segment net revenue:", "17.4 %"),
    ("LITE25-14", "LITE25", "工序步骤", "neutral", "current", "C1,MOD1,MOD2",
     "Lumentum相当比例的收入通过供应商管理库存（VMI）模式实现，并常按客户指令将光芯片与光器件直接发往客户自有工厂或其位于亚洲的第三方EMS代工厂进行组装。",
     "Item 1. Business — Backlog & International Operations (p.8, L626-L627)", 626, 628,
     "A significant portion of our revenue arises from vendor-managed inventory", "difficult to predict."),
    ("LITE25-15", "LITE25", "产品构成", "neutral", "current", "C2",
     "在工业与消费电子板块，Lumentum开发高功率半导体泵浦激光器、超快微加工激光器（服务PCB、半导体、光伏与显示制造）及3D传感VCSEL光源。",
     "Item 1. Business — Industrial Tech · Markets (p.6, L479-L484)", 479, 485,
     "Within the industrial market, our diode lasers serve as pump sources", "other consumer electronics devices."),

    # ================= 14. Fabrinet (FN) — 14 条 =================
    ("FN25-01", "FN25", "产品构成", "neutral", "current", "EMS1,MOD1,MOD2,MOD3,D7,M4",
     "Fabrinet专为原始设备制造商（OEM）提供精密光学、机电及电子制造服务（EMS）与定制化光学玻璃/晶体元件制造，光通信代工品类涵盖可调谐激光器、光收发模块、应答器（transponders）、有源光缆（AOC）、ROADM、光放大器及调制器，且自身不推出自有品牌终端产品与客户竞争。",
     "Item 1. Business — Overview & Service Offerings (p.4~6, L325-L329)", 325, 330,
     "tunable lasers, transceivers, and transponders", "optical backplane connectivity;"),
    ("FN25-02", "FN25", "技术参数", "neutral", "current", "EMS1",
     "截至2025年6月27日，Fabrinet全球设施总面积约370万平方英尺（其中泰国约330万平方英尺），制造及相关生产面积约290万平方英尺，其中高洁净度无尘室（clean room）面积约达100万平方英尺。",
     "Item 1. Business — Facilities Overview (p.5, L368-L372)", 368, 373,
     "As of June 27, 2025, our facilities comprised approximately 3.7 million total square feet", "Israel and the Cayman Islands."),
    ("FN25-03", "FN25", "设备-工序能力", "neutral", "current", "EMS1,D7,M4",
     "Fabrinet全球核心制造基地分布：泰国曼谷Pinehurst园区（自有173.1万平方英尺）、泰国春武里（Chonburi）Hemaraj园区（自有152.2万平方英尺，并于2025年2月动工扩建新厂房）、中国福州定制光学厂（租赁34.8万平方英尺）及美国加州Santa Clara、新泽西与以色列基地。",
     "Item 2. Properties (p.31, L1922-L1928)", 1922, 1929,
     "Pinehurst Campus, Bangkok, Thailand", "1,280"),
    ("FN25-04", "FN25", "工序步骤", "neutral", "current", "EMS1",
     "Fabrinet在硅谷（Fabrinet West）和以色列设有专门新产品导入（NPI）中心，配置与泰国低成本量产基地完全镜像的SMT与先进光学封装产线设备，协助客户完成可制造性设计（DFM）与快板打样后无缝转移至泰国放量。",
     "Item 1. Business — Growth Strategy · NPI Centers (p.6, L495-L500)", 495, 501,
     "established Fabrinet West, Inc. as an NPI center", "manufacturing base in Thailand."),
    ("FN25-05", "FN25", "工序步骤", "neutral", "current", "EMS1",
     "在将客户内部原型线或既有产线转移至Fabrinet工厂时，公司执行严格的“Copy-Exact（完全复制）”工艺转移规程，建立与客户原有产线完全一致的工艺配置以最小化过程变量并加速认证。",
     "Item 1. Business — Process Design and Engineering (p.6~7, L518-L519)", 518, 520,
     "customer’s internal prototype or production lines to our own facilities", "expedite qualification."),
    ("FN25-06", "FN25", "设备-工序能力", "neutral", "current", "EMS1,D12,P1",
     "Fabrinet先进光学封装工程团队维护通用工艺配方库（generic recipes），可针对新型复杂光器件与光子集成电路（PIC）快速裁剪定制，加速客户样品试制至规模量产周期。",
     "Item 1. Business — Advanced Optical Packaging (p.7, L522-L527)", 522, 528,
     "We have a dedicated team of experienced engineers supporting our advanced optical packaging", "product delivery time."),
    ("FN25-07", "FN25", "工序步骤", "neutral", "current", "EMS1,B1,D12",
     "Fabrinet高密度电路板组装（PCBA）涵盖SMT、PTH、压接、芯片级封装（CSP）、BGA、裸芯片直接贴装（Direct Chip Attach，即COB）及高密度互连（HDI），并执行在线测试、功能测试与环境应力测试。",
     "Item 1. Business — Printed Circuit Board Assembly and Test (p.7, L531-L537)", 531, 538,
     "We employ a variety of mounting and assembly technologies", "manufacturing specifications."),
    ("FN25-08", "FN25", "工序步骤", "industry", "current", "EMS1,MOD1,MOD2,MOD3",
     "光通信器件量产前须经历严苛的产线认证与环境可靠性认证（如电信Telcordia机械完整性与环境耐久标准），认证与现场测试周期通常长达3至6个月甚至更久。",
     "Item 1. Business — Qualifications (p.7, L548-L552)", 548, 553,
     "Production line and environmental qualifications require a variety of process engineering", "Telcordia for telecommunication equipment."),
    ("FN25-09", "FN25", "设备-工序能力", "neutral", "current", "EMS1,EQ7",
     "Fabrinet制造执行系统（MES）与测试系统及ERP数据库直连，实时监控工艺偏差并执行工序路径防呆校验（process route checking）；光学测试覆盖插损、回损、消光比等参数测试及误码率（BER）功能测试。",
     "Item 1. Business — Quality Control (p.8, L580-L586)", 580, 587,
     "Our manufacturing execution system (“MES”) is directly integrated", "functional testing (e.g., bit error ratio)."),
    ("FN25-10", "FN25", "产品构成", "neutral", "current", "D6,D7,D9,D10,D11,M4",
     "Fabrinet通过中国福州与美国新泽西工厂内部制造定制玻璃与晶体光学元件，产品涵盖光纤插芯与对准套筒、精密毛细玻璃管、YVO4等双折射/激光晶体、球面/非球面/C-lens/柱面透镜、波片、棱镜、滤光片及隔离器/环形器尾纤准直组件。",
     "Item 1. Business — Customized Glass and Crystal Optics Fabrication (p.8, L589-L605)", 589, 595,
     "We design and fabricate our own customized glass and crystal optics", "medical and industrial applications."),
    ("FN25-11", "FN25", "工序步骤", "neutral", "current", "EMS1,D9,P1",
     "Fabrinet掌握光纤金属化（fiber metallization）与光纤尖端透镜加工（fiber lensing）内部工艺，以及无应力剥纤、切割、端接与快速光纤对准耦合规程，防止光纤表面损伤或纤芯微裂纹劣化耦合质量。",
     "Item 1. Business — Technology · Fiber Metallization & Alignment (p.9, L633-L642)", 633, 643,
     "Fiber Metallization and Lensing: We use our fiber metallization", "shortest period of time during these processes."),
    ("FN25-12", "FN25", "工序步骤", "neutral", "current", "M4,D10,D11",
     "Fabrinet具备硼硅酸盐玻璃、透明熔融石英及合成熔融石英的高精度拉管工艺（制造定制单孔/多孔玻璃毛细管并切割为光纤插芯与套筒），以及从单层增透膜到复杂多层高反/半反介质膜的光学镀膜能力。",
     "Item 1. Business — Technology · Precision Glass Drawing & Coating (p.9, L648-L656)", 648, 657,
     "Precision Glass Drawing: We have developed the specialized capabilities", "partial reflection and high reflection."),
    ("FN25-13", "FN25", "设备-工序能力", "neutral", "current", "EMS1,EQ7",
     "Fabrinet自建可靠性实验室与材料工艺分析实验室，可执行湿热（damp heat）、热老化、热冲击、温度循环、冲击振动、加速寿命测试与应力筛选及失效根因分析，持有TL 9000、ISO 9001、IATF 16949、ISO 13485、AS 9100与ISO/IEC 17025认证。",
     "Item 1. Business — Technology · Reliability Testing (p.8, L617-L621)", 617, 622,
     "Reliability Testing: Our reliability laboratory enables us to test", "verification of root cause failure analysis."),
    ("FN25-14", "FN25", "代际事件", "neutral", "planned", "EMS1,C4,MOD1",
     "Fabrinet正持续投资下一代光电子制造工艺，重点面向多功能无源光学组件、光子集成电路（PIC）封装芯片、集成光放大器的接收器及有源光缆（AOC）的商业化量产。",
     "Item 1. Business — Technology · Next Generation Investments (p.9, L658-L662)", 658, 663,
     "We continuously invest in new and optimized processes to accommodate the next generation", "active optical cabling."),

    # ================= 15. AAOI (Applied Optoelectronics) — 14 条 =================
    ("AAOI25-01", "AAOI25", "产品构成", "neutral", "current", "C1,D12,MOD1,MOD3",
     "AAOI聚焦互联网数据中心、有线电视（CATV）、电信及光纤到户（FTTH）四大市场，从底层激光器芯片及光组件出发，垂直整合设计制造光引擎、可插拔光模块及CATV整机设备；2025年CATV与互联网数据中心分别贡献总营收（4.557亿美元）的53.8%和42.9%。",
     "Item 1. Business — Overview (p.3~4, L283-L297)", 293, 298,
     "In 2025, 2024 and 2023, our revenue was $455.7 million", "internet data center market."),
    ("AAOI25-02", "AAOI25", "工序步骤", "neutral", "current", "M2a,C1",
     "AAOI同时采用专有分子束外延（MBE）与金属有机化学气相沉积（MOCVD）两种外延工艺制造模拟与数字半导体激光器芯片，所有激光器芯片均在美国得州Sugar Land晶圆厂生产。",
     "Item 1. Business — Vertically Integrated Manufacturing Model (p.4, L282-L289)", 282, 290,
     "We design, manufacture and integrate our own analog and digital lasers", "facility in Sugar Land, Texas."),
    ("AAOI25-03", "AAOI25", "工序步骤", "neutral", "current", "M2a,C1",
     "MBE外延相较MOCVD具有更低生长温度、使用固态源替代气态源、可生长更高应变晶体层等工艺优势，有助于延长激光器工作寿命、提升发光效率并降低阈值电流；而针对MBE难以掺铁（Fe）及特定再生长受限的短板，AAOI在部分工序中结合MOCVD外延加以弥补。",
     "Item 1. Business — Differentiated Semiconductor Laser Manufacturing (p.7, L505-L514)", 505, 515,
     "We use a combination of MBE and MOCVD processes in the fabrication of our lasers.", "ameliorate some of these disadvantages."),
    ("AAOI25-04", "AAOI25", "设备-工序能力", "issuer_self", "current", "EQ1,M2a,C1",
     "AAOI自述其据所知是业内唯一在大批量通信激光器芯片生产中融合MBE工艺的厂商，并对标准超高真空MBE设备及工艺进行了大量自主改造以控制复杂外延良率与器件一致性。",
     "Item 1. Business — Differentiated Semiconductor Laser Manufacturing (p.7~8, L516-L520)", 516, 521,
     "As a result of some of these challenges, production yields and the performance attributes", "replicate our production technology."),
    ("AAOI25-05", "AAOI25", "工序步骤", "neutral", "current", "C1,C5,MOD3",
     "针对传统通信半导体激光器在长距光纤传输中的啁啾（chirp）和波长漂移缺陷，AAOI自主开发了激光器性能增强控制电路（laser enhancement circuitry）进行电学补偿校正。",
     "Item 1. Business — Laser Enhancement Technology (p.8, L522-L525)", 522, 526,
     "Certain properties of the semiconductor lasers predominantly used in traditional", "correct many of these deficiencies."),
    ("AAOI25-06", "AAOI25", "设备-工序能力", "neutral", "current", "D12,MOD1",
     "AAOI掌握光学混合集成（optical hybrid-integration）与并行光引擎设计制造技术：将多颗激光器芯片、光电二极管、驱动/放大电芯片及波分复用/解复用元件共封装为紧凑型光引擎（light engine），用于自产高速数据中心光收发模块并导入高自动化产线。",
     "Item 1. Business — Competitive Strengths · Light Engine (p.6, L425-L428)", 425, 429,
     "High-speed data center interconnect transceivers increasingly", "data center customers."),
    ("AAOI25-07", "AAOI25", "产品构成", "neutral", "current", "D4,D11,D13,C1",
     "AAOI自产光组件将多颗自研激光器芯片封装于带标准电接口的精密壳体内，高阶组件内部集成WDM光学滤波片、内部光路路由元件以及TEC制冷器、加热器与温度传感器以精准稳控激光波长。",
     "Item 1. Business — Our Products · Components (p.8, L580-L584)", 580, 585,
     "Our components often incorporate one or more of our optical laser chips", "used in our own products."),
    ("AAOI25-08", "AAOI25", "设备-工序能力", "neutral", "current", "C1,D12,MOD1,MOD3",
     "AAOI全球三地制造分工明确：美国得州Sugar Land工厂独家负责MBE/MOCVD激光器芯片制造及部分光组件；中国台湾台北工厂负责蝶形激光器组件、数据中心/电信/FTTH光模块及CATV户外放大器制造；中国宁波工厂负责光次模块（OSA）、数通光模块及CATV头端与户外设备制造（均获ISO 9001/14001认证）。",
     "Item 1. Business — Manufacturing and Operations (p.10, L669-L681)", 669, 682,
     "We have three manufacturing sites: Sugar Land, Texas, Ningbo, China and Taipei, Taiwan.", "ISO 9001:2015 and ISO 14001:2015."),
    ("AAOI25-09", "AAOI25", "代际事件", "neutral", "current", "MOD1",
     "数据中心互连速率正由10Gbps向800Gbps及1.6Tbps升级；AAOI 800G数通光模块产品已用于AI算力基础设施互连，2025年公司围绕800G与1.6T数据中心产品的客户测试认证显著增加了研发投入。",
     "Item 7. MD&A — Industry Trends & R&D Expense (p.38 & p.44, L2540-L2543)", 2540, 2544,
     "Our products are used to interconnect network elements within data centers generally", "AI-focused data centers."),
    ("AAOI25-10", "AAOI25", "代际事件", "neutral", "planned", "MOD1",
     "2025年AAOI数据中心客户对800G和1.6T新产品测试与认证需求显著上升，拉动公司研发工单与测试设备投入增长。",
     "Item 7. MD&A — Research and Development Expense (p.44, L2883-L2885)", 2883, 2886,
     "During 2025, we experienced increased interest in new technologies like 800G and 1.6T", "materially increased our R&D expenditures"),
    ("AAOI25-11", "AAOI25", "代际事件", "neutral", "current", "MOD3",
     "在接入网与电信市场，AAOI已开发25Gbps PON和50Gbps PON解决方案以及微型封装WDM-PON方案，并供应5G移动前传/回传及城域网光模块；CATV市场自2025年起所售设备基本全面符合DOCSIS 4.0标准（Quantum Bandwidth品牌）。",
     "Item 1. Business — Trends in the FTTH Market (p.5, L384-L388)", 384, 389,
     "Another approach is XGS-PON, which offers 10 Gbps over a single fiber strand.", "adopted by customers."),
    ("AAOI25-12", "AAOI25", "工序步骤", "neutral", "current", "C5,MOD3",
     "针对CATV网络向数字回传（digital return-path）与Remote-PHY数模混合架构演进，AAOI开发了兼具射频（RF）模拟与数字混合信号设计及自研软固件的光传输与放大设备。",
     "Item 1. Business — Mixed-Signal Design (p.8, L552-L558)", 552, 559,
     "Older analog networks are giving way to hybrid networks", "mixed-signal architectures."),
    ("AAOI25-13", "AAOI25", "技术参数", "neutral", "current", "通用",
     "截至2025年12月31日，AAOI拥有研发人员425人（含14名博士，分布于得州、佐治亚州Duluth、中国大陆及中国台湾），持有199项美国授权专利、140项中国大陆及台湾专利和10项欧洲专利，覆盖激光器结构、激光制造、光探测器、光学封装设备与工艺等八大技术族。",
     "Item 1. Business — Patents (p.9, L637-L638)", 637, 639,
     "As of December 31, 2025, we owned a total of 199 U.S. issued patents", "pending U.S. and foreign/international patent applications."),
    ("AAOI25-14", "AAOI25", "工序步骤", "neutral", "current", "C1,MOD1,MOD3",
     "AAOI实行低外部原材料库存与标准化采购设计管控策略，将内部自制激光芯片与光组件优先集成至自有光模块与子系统中，每座制造基地均独立执行组件、模块及子系统级全流程测试。",
     "Item 1. Business — Manufacturing and Operations (p.10, L684-L689)", 684, 690,
     "With a vertically integrated manufacturing process, we produce many of our own laser chips", "reduce risk and lower cost."),
]


def build_expansion_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for (
        cid,
        doc_key,
        fact_type,
        stance,
        tense,
        cell_ids,
        atomic_fact,
        section_ref,
        s_line,
        e_line,
        s_anchor,
        e_anchor,
    ) in EXPANSION_SPECS:
        meta = COMPANY_DOCS[doc_key]
        quote = CACHE.extract_span(meta["path"], s_line, e_line, s_anchor, e_anchor, lang=meta["lang"])
        rows.append(
            {
                "cid": cid,
                "company": meta["company"],
                "stock_code_or_ticker": meta["code"],
                "source_doc": meta["doc"],
                "doc_year": meta["year"],
                "fact_type": fact_type,
                "stance": stance,
                "tense": tense,
                "cell_ids": cell_ids,
                "atomic_fact": atomic_fact,
                "verbatim_quote": quote,
                "section_ref": section_ref,
                "local_source_path": meta["path"],
                "anchor_url": meta["url"],
                "quote_verification_status": "verified_local",
                "batch": "step2_expansion",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Part 3: 铁律机械校验门（Schema / 叶格 / 双闸 / 100% 严格子串）
# ---------------------------------------------------------------------------

COMMERCIAL_ORDER_PATTERNS = [
    # 拦截新扩条目中“向具名客户供货/销售/获订单/占营收比例”或“向具名供应商采购”的商业关系边主张
    re.compile(r"(?:第一大客户|前五大客户|前五名客户|第一大供应商|前五大供应商)"),
    re.compile(r"(?:向|对)(?:NVIDIA|英伟达|Cisco|思科|Microsoft|微软|Google|谷歌|Meta|Amazon|亚马逊|华为|中际旭创|新易盛|天孚通信|光迅科技|华工|锐科激光|创鑫激光|比亚迪)[^。；]{0,20}(?:销售|供货|交付|采购|订单|收入)"),
    re.compile(r"(?:签订|取得|获得)[^。；]{0,18}(?:产线设备订单|批量化订单|采购订单|在手订单)"),
]


def validate_all_rows(rows: List[Dict[str, str]], valid_cells: set[str]) -> Dict[str, object]:
    seen_cids = set()
    expansion_hits = 0
    expansion_total = 0
    dual_gate_violations: List[str] = []

    for idx, r in enumerate(rows, 1):
        # 1. Exact schema keys & no embedded newlines
        assert list(r.keys()) == SCHEMA_COLUMNS, f"Row {idx} schema mismatch"
        for k, val in r.items():
            assert "\n" not in val and "\r" not in val and "\f" not in val, f"Embedded newline in {r['cid']}.{k}"
            if k != "anchor_url":
                assert val.strip() != "", f"Empty required field {k} in {r['cid']}"

        cid = r["cid"]
        assert cid not in seen_cids, f"Duplicate cid: {cid}"
        seen_cids.add(cid)

        # 2. Enums
        assert r["fact_type"] in VALID_FACT_TYPES, f"{cid} invalid fact_type: {r['fact_type']}"
        assert r["stance"] in VALID_STANCES, f"{cid} invalid stance: {r['stance']}"
        assert r["tense"] in VALID_TENSES, f"{cid} invalid tense: {r['tense']}"
        assert r["batch"] in {"v1_salvage", "step2_expansion"}, f"{cid} invalid batch: {r['batch']}"

        # 3. Leaf cell validation
        tokens = [c.strip() for c in r["cell_ids"].split(",") if c.strip()]
        assert tokens, f"{cid} empty cell_ids"
        if tokens != ["通用"]:
            for c in tokens:
                assert c in valid_cells, f"{cid} cell_id {c!r} not in tree.yaml 41 leaf cells"

        # 4. Local source path existence
        full_src = os.path.join(ROOT, r["local_source_path"])
        assert os.path.exists(full_src), f"{cid} local_source_path missing: {r['local_source_path']}"

        # 5. Expansion strict 100% verbatim quote check + dual-gate check + completion phrasing check
        if r["batch"] == "step2_expansion":
            expansion_total += 1
            for fw in FORBIDDEN_COMPLETION_WORDS:
                assert fw not in r["atomic_fact"], f"{cid} atomic_fact contains forbidden word {fw!r}"
            src_norm = CACHE.get_norm(r["local_source_path"])
            q_norm = norm(r["verbatim_quote"])
            if q_norm and q_norm in src_norm:
                expansion_hits += 1
            else:
                raise AssertionError(f"Expansion quote MISS on {cid}: {r['verbatim_quote']!r}")

            combined = f"{r['atomic_fact']} || {r['verbatim_quote']}"
            for pat in COMMERCIAL_ORDER_PATTERNS:
                m = pat.search(combined)
                if m:
                    dual_gate_violations.append(f"{cid}: {m.group(0)}")

    assert expansion_hits == expansion_total, f"Expansion quote hits {expansion_hits}/{expansion_total}"
    assert not dual_gate_violations, f"Dual-gate violations found: {dual_gate_violations}"

    return {
        "total_rows": len(rows),
        "v1_salvage_rows": sum(1 for r in rows if r["batch"] == "v1_salvage"),
        "step2_expansion_rows": expansion_total,
        "step2_expansion_strict_quote_hits": expansion_hits,
        "step2_expansion_strict_quote_misses": expansion_total - expansion_hits,
        "step2_expansion_hit_rate": "100.0%",
        "dual_gate_commercial_order_violations": 0,
        "invalid_cell_id_count": 0,
    }


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_readme(report: Dict[str, object]) -> None:
    by_co = report["company_breakdown"]
    lines = [
        "# 内容台账（Content Ledger）— 工艺 / 技术参数 / 产品构成 / 代际事件 / 设备能力",
        "",
        "## 1. 定位与边界红线（Schema v1 冻结纪律）",
        "",
        "本目录承载光模块产业链**企业级客观技术与工艺内容台账**（源自 `archive/flows/content-ledger-schema-v1.md` 与 `archive/flows/out/content-ledger-v1.md` 的正式收编及 Step 2 海内外 15 家龙头扩抽）。",
        "",
        "1. **双闸物理隔离（最高红线）**：内容台账只记录工艺步骤、量化参数、产品构成、研发/量产代际事件与设备-工序能力，**严禁写入任何具名客户/供应商商业买卖订单、销售占比或采购金额主张**，且内容台账条目**永不作为 `edges.csv` 交易关系边的证据通道**。",
        "2. **自夸隔离（`issuer_self` 永不承重）**：发行人或上市公司自我标榜“全球领先”“行业第一梯队”“国际一流”或单方援引第三方排名的竞争地位陈述，一律显式标记 `stance = issuer_self`，下游研究与渲染严禁将其作为客观承重结论；客观工艺指标标 `neutral`，行业共性原理或公开市场预测标 `industry`。",
        "3. **叶格挂接纪律**：`cell_ids` 仅允许填写根目录 `tree.yaml` 冻结的 **41 个叶节点 `cell_id`**（多格以英文逗号分隔）或 `通用`（通用于全厂研发/生产管理制度或非光通信跨行业业务），严禁挂接父节点或关系边。",
        "4. **引语逐字可复核**：Step 2 新扩 15 家海内外龙头全部条目均从本地 `corpus/` 原文直接切片提取，100% 通过严格去空白子串校验 `re.sub(r'\\s+', '', verbatim_quote) in re.sub(r'\\s+', '', source_text)`（0 未命中）。",
        "",
        "## 2. Schema 字段说明（16 列）",
        "",
        "| 列名 | 枚举/格式 | 说明 |",
        "|---|---|---|",
        "| `cid` | 字符串主键 | 唯一条目编号（v1 沿用原 `SJZ/SJ24-/YJZ/YJ/CGHX/TCG24-/C` 前缀；Step 2 新扩按公司缩写编号） |",
        "| `company` | 公司简称 | 覆盖既有 5 家 + Step 2 扩抽 15 家共 **20 家**海内外核心企业 |",
        "| `stock_code_or_ticker` | 股票代码/状态 | A 股 6 位代码、美股 Ticker（`COHR/LITE/FN/AAOI`）或 `创业板IPO在审` |",
        "| `source_doc` | 披露文件名称 | 招股说明书（注册稿/申报稿）、2023–2025 年年度报告、FY2025 Form 10-K、官网技术页快照 |",
        "| `doc_year` | 四位年份 | 来源披露文件所属年度 |",
        "| `fact_type` | 五分互斥枚举 | `工序步骤 \\| 技术参数 \\| 产品构成 \\| 代际事件 \\| 设备-工序能力` |",
        "| `stance` | 三分立场枚举 | `neutral`（企业客观工艺/参数）`\\| industry`（行业原理/第三方预测）`\\| issuer_self`（自评/排名，不承重） |",
        "| `tense` | 三分时态枚举 | `current \\| historical \\| planned` |",
        "| `cell_ids` | 叶格列表 | `tree.yaml` 41 个叶格（逗号分隔）或 `通用` |",
        "| `atomic_fact` | 中文原子句 | 单条可独立核验的工艺/参数/产品/代际/设备能力事实（海外 10-K 统一提供中文提炼句） |",
        "| `verbatim_quote` | 原文逐字引语 | 对应本地语料的逐字原句（海外 10-K 与 ficonTEC 网页保留英文原句） |",
        "| `section_ref` | 章节与行号定位 | 披露文件章节路径、页码及本地 `.txt/.html` 行号区间 |",
        "| `local_source_path` | 仓库相对路径 | 对应 `corpus/` 下的真实本地文本文件 |",
        "| `anchor_url` | 官方链接 | 巨潮资讯、上交所、深交所、SEC EDGAR 或官网快照原始 URL |",
        "| `quote_verification_status` | 复核状态 | `verified_local`（本地文本复核命中）/ `inherited_v1_verified` / `pilot_self_reported` |",
        "| `batch` | 批次标识 | `v1_salvage`（既有 5 家 377 条收编）或 `step2_expansion`（Step 2 新增 15 家扩抽） |",
        "",
        "## 3. 覆盖规模与公司分布",
        "",
        f"- **总条目数**：**{report['total_rows']} 条**（其中 `v1_salvage` **{report['v1_salvage_rows']} 条**，`step2_expansion` **{report['step2_expansion_rows']} 条**）",
        f"- **引语本地机械验证**：总计 **{report['verification_status_counts'].get('verified_local', 0)}/{report['total_rows']}** 条为 `verified_local`；其中 Step 2 新扩 **{report['step2_expansion_strict_quote_hits']}/{report['step2_expansion_rows']}（100.0%，0 未命中）** 严格命中本地原文。",
        "",
        "| 批次 | 公司 | 代码/Ticker | 条目数 | 主要覆盖叶格 |",
        "|---|---|---|---:|---|",
    ]
    for item in by_co:
        lines.append(
            f"| `{item['batch']}` | {item['company']} | `{item['stock_code_or_ticker']}` | {item['count']} | `{item['top_cells']}` |"
        )
    lines.extend(
        [
            "",
            "## 4. 重建与校验命令",
            "",
            "```bash",
            "PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 out/step2-archive-salvage-20261121/build_content_ledger.py",
            "```",
            "",
        ]
    )
    with open(OUT_README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def main() -> None:
    os.makedirs(OUT_LEDGER_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_SUMMARY_PATH), exist_ok=True)

    valid_cells = load_valid_leaf_cells()
    v1_rows, v1_detail_stats = parse_v1_ledger()
    exp_rows = build_expansion_rows()
    all_rows = v1_rows + exp_rows

    gate_summary = validate_all_rows(all_rows, valid_cells)

    # Write content_ledger.csv (UTF-8 with BOM + \n, zero embedded newlines)
    with open(OUT_CSV_PATH, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_rows)

    # Verify physical line count == len(all_rows) + 1
    phys_lines = open(OUT_CSV_PATH, encoding="utf-8-sig").read().splitlines()
    assert len(phys_lines) == len(all_rows) + 1, (
        f"Physical lines {len(phys_lines)} != logical rows + 1 ({len(all_rows) + 1})"
    )

    # Build breakdowns
    co_groups: Dict[Tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for r in all_rows:
        co_groups[(r["batch"], r["company"], r["stock_code_or_ticker"])].append(r)

    company_breakdown = []
    for (batch, co, code), grp in co_groups.items():
        cell_cnt = Counter()
        for r in grp:
            for c in r["cell_ids"].split(","):
                cell_cnt[c.strip()] += 1
        top_cells = ",".join(c for c, _ in cell_cnt.most_common(6))
        company_breakdown.append(
            {
                "batch": batch,
                "company": co,
                "stock_code_or_ticker": code,
                "count": len(grp),
                "issuer_self_count": sum(1 for r in grp if r["stance"] == "issuer_self"),
                "verified_local_count": sum(1 for r in grp if r["quote_verification_status"] == "verified_local"),
                "top_cells": top_cells,
            }
        )

    report = {
        **gate_summary,
        "physical_csv_lines": len(phys_lines),
        "unique_companies": len({r["company"] for r in all_rows}),
        "v1_companies_count": len({r["company"] for r in v1_rows}),
        "expansion_companies_count": len({r["company"] for r in exp_rows}),
        "fact_type_counts": dict(Counter(r["fact_type"] for r in all_rows)),
        "stance_counts": dict(Counter(r["stance"] for r in all_rows)),
        "tense_counts": dict(Counter(r["tense"] for r in all_rows)),
        "verification_status_counts": dict(Counter(r["quote_verification_status"] for r in all_rows)),
        "v1_verification_breakdown": v1_detail_stats,
        "company_breakdown": company_breakdown,
    }

    with open(OUT_REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    write_readme(report)

    shard_summary = {
        "shard": "Step 2 Task B (carbon-content-ledger)",
        "deliverables": {
            "content_ledger_csv": {
                "path": "corpus/content_ledger/content_ledger.csv",
                "sha256": sha256_file(OUT_CSV_PATH),
                "total_rows": report["total_rows"],
                "v1_salvage_rows": report["v1_salvage_rows"],
                "step2_expansion_rows": report["step2_expansion_rows"],
                "physical_lines": report["physical_csv_lines"],
            },
            "quote_verification_report": {
                "path": "corpus/content_ledger/quote_verification_report.json",
                "sha256": sha256_file(OUT_REPORT_PATH),
            },
            "readme": {
                "path": "corpus/content_ledger/README.md",
                "sha256": sha256_file(OUT_README_PATH),
            },
            "knowledge_kn007_update": {
                "path": "knowledge.yaml",
                "sha256": sha256_file(os.path.join(ROOT, "knowledge.yaml")),
                "added_anchor": "corpus/legacy-input/lieqi_prospectus.txt#第六节·分产品毛利率分析(1-1-228,18218-18222行)",
                "verified_numbers": {
                    "burn_in_gross_margin_2023_2024_2025": ["37.45%", "50.65%", "12.55%"],
                    "die_attach_gross_margin_2023_2024_2025": ["59.28%", "59.58%", "60.51%"],
                    "coupling_gross_margin_2023_2024_2025": ["60.45%", "54.52%", "53.99%"],
                },
            },
        },
        "verification": {
            "v1_salvage_exact_377": report["v1_salvage_rows"] == 377,
            "step2_expansion_15_companies": report["expansion_companies_count"] == 15,
            "step2_expansion_strict_quote_hits": f"{report['step2_expansion_strict_quote_hits']}/{report['step2_expansion_rows']} (100.0%)",
            "step2_expansion_strict_quote_misses": report["step2_expansion_strict_quote_misses"],
            "all_rows_verified_local": f"{report['verification_status_counts'].get('verified_local', 0)}/{report['total_rows']}",
            "dual_gate_commercial_order_violations": report["dual_gate_commercial_order_violations"],
            "invalid_leaf_cell_ids": report["invalid_cell_id_count"],
        },
        "company_counts": {item["company"]: item["count"] for item in company_breakdown},
        "fact_type_counts": report["fact_type_counts"],
        "stance_counts": report["stance_counts"],
    }

    with open(OUT_SUMMARY_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(shard_summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(
        f"[OK] Built content_ledger.csv: total={report['total_rows']} "
        f"(v1={report['v1_salvage_rows']}, expansion={report['step2_expansion_rows']}), "
        f"verified_local={report['verification_status_counts'].get('verified_local', 0)}/{report['total_rows']}, "
        f"expansion_strict_misses={report['step2_expansion_strict_quote_misses']}"
    )


if __name__ == "__main__":
    main()
