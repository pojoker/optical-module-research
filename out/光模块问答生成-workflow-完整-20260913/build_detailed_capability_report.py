#!/usr/bin/env python3
"""Build a granular company capability ledger, PDF, and merged HTML.

The evidence ledger remains points.csv. This script normalizes confirmed points
into capability_details.csv, then renders both deliverables from that same file.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import participation
from calls.renderer import render as render_calls
from calls.validator import validate as validate_calls
from calls.workbuddy import render_intelligence_section


ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "capability_details.csv"
ROUTE_BOM_CSV = ROOT / "route_bom.csv"
MACRO_EVIDENCE_CSV = ROOT / "macro_evidence.csv"
EDGES_CSV = ROOT / "edges.csv"
CALLS_INTELLIGENCE_CSV = ROOT / "calls" / "out" / "panorama-intelligence.csv"
CALLS_POSITIONING_JSON = ROOT / "calls" / "out" / "positioning.json"
CALLS_EVENT_JSON = ROOT / "calls" / "out" / "event-intelligence.json"
DEFAULT_PDF = ROOT / "output" / "pdf" / "光模块产业链公司能力明细.pdf"
DEFAULT_TEMPLATE = Path(
    "/Users/jowang/Workbuddy/2026-07-26-11-49-54/"
    "光模块产业链全景图_产业链优先版.html"
)
DEFAULT_HTML = Path(
    "/Users/jowang/Workbuddy/2026-07-26-11-49-54/"
    "光模块产业链全景图_公司能力细化版.html"
)
FONT_PATH = Path("/System/Library/Fonts/STHeiti Light.ttc")

# Reader-facing edges are deliberately curated: only named, original-source,
# verified "实边" records are eligible.  The full edge ledger remains backend
# audit data and is not dumped into the reader.
READER_EDGE_IDS = {
    "E001",
    "E003",
    "E043",
    "E045",
    "E048",
    "E049",
    "E074",
    "E083",
    "E085",
    "E088",
}

STAGES = [
    ("材料层", ("M",), "#2C6E8F"),
    ("芯片层", ("C",), "#3D63A8"),
    ("芯片封装", ("P",), "#6750A4"),
    ("光器件层", ("D",), "#8B4D94"),
    ("电路与结构", ("B",), "#A05B36"),
    ("模块层", ("MOD",), "#147A68"),
    ("制造与代工", ("EMS",), "#25745D"),
    ("设备与仪器", ("EQ",), "#6B7280"),
]

PRODUCT_PATTERNS = [
    ("InP衬底", r"\bInP\b|磷化铟衬底"),
    ("GaAs衬底/外延", r"\bGaAs\b|砷化镓"),
    ("SOI/硅光平台", r"\bSOI\b|硅光PIC|硅光芯片|silicon phot"),
    ("EML", r"\bEML\b"),
    ("DFB", r"\bDFB\b"),
    ("CW光源", r"\bCW\b|连续波"),
    ("VCSEL", r"\bVCSEL\b"),
    ("PIN/PD", r"\bPIN\b|\bPD\b|探测器芯片"),
    ("APD", r"\bAPD\b"),
    ("DSP", r"\bDSP\b"),
    ("Driver", r"\bDriver\b|激光驱动"),
    ("TIA", r"\bTIA\b|跨阻放大"),
    ("CDR", r"\bCDR\b|时钟恢复"),
    ("MCU", r"\bMCU\b|主控"),
    ("SerDes/PHY", r"\bSerDes\b|\bPHY\b"),
    ("TOSA", r"\bTOSA\b"),
    ("ROSA", r"\bROSA\b"),
    ("BOSA", r"\bBOSA\b"),
    ("COC/COB光组件", r"\bCOC\b|\bCOB\b|光引擎"),
    ("AWG", r"\bAWG\b|阵列波导光栅"),
    ("WDM滤光片/组件", r"\bWDM\b|\bCWDM\b|\bDWDM\b|\bLWDM\b|滤光片"),
    ("FAU/光纤阵列", r"\bFAU\b|光纤阵列|\bMT-FA\b"),
    ("MPO/MTP连接", r"\bMPO\b|\bMTP\b|MT插芯"),
    ("陶瓷插芯/套管", r"陶瓷插芯|陶瓷套"),
    ("陶瓷管壳/TO管座", r"陶瓷管壳|陶瓷封装管壳|光通信器件外壳|TO管座"),
    ("透镜/微光学", r"透镜|微光学|光学件"),
    ("光模块PCB", r"光模块PCB|高速PCB"),
    ("高速板材/覆铜板", r"高速覆铜板|LowDK|高速板"),
    ("结构件/散热", r"基座|壳体|散热"),
    ("数通光模块", r"数通光模块|高速光模块|光通信收发模块"),
    ("相干模块", r"相干模块|ZR/ZR\+|400ZR"),
    ("接入/电信模块", r"PON|FTTx|电信.*光模块|承载传输"),
    ("AOC", r"有源光缆|\bAOC\b"),
    ("MOCVD/外延设备", r"\bMOCVD\b|\bMBE\b|外延设备"),
    ("光刻/刻蚀设备", r"光刻设备|刻蚀设备|\bICP\b|\bCCP\b"),
    ("耦合/微组装设备", r"耦合设备|微组装|光学耦合"),
    ("测试/老化设备", r"测试设备|测试仪器|老化测试|\bATE\b"),
    ("AOI检测设备", r"\bAOI\b|在线检测"),
]

PROCESS_PATTERNS = [
    ("产品设计", r"研发|设计|自主开发|自研"),
    ("外延生长", r"外延生长|\bMOCVD\b|\bMBE\b"),
    ("晶圆制造/处理", r"晶圆处理|晶圆制造|FAB|流片"),
    ("光刻/刻蚀", r"光刻|刻蚀|光栅"),
    ("薄膜/镀膜", r"薄膜|镀膜|金属化"),
    ("固晶/贴片", r"固晶|贴片|贴装|共晶|COC贴装"),
    ("引线/混合键合", r"金丝键合|引线键合|混合键合|键合"),
    ("光学耦合", r"光学耦合|耦合"),
    ("封装/密封", r"封装|气密|缝焊|激光焊"),
    ("焊接/组装", r"焊接|组装|装配"),
    ("测试/检验", r"测试|检验|分选|眼图|误码"),
    ("老化/可靠性", r"老化|高低温|温循|可靠性"),
    ("委托加工/代工", r"委托加工|代工|OEM|EMS"),
    ("规模制造", r"生产|量产|批量|产业化"),
]

SPEC_PATTERNS = [
    ("1.6T", r"1\.6T"),
    ("800G", r"800G"),
    ("400G", r"400G"),
    ("200G", r"200G"),
    ("100G", r"100G"),
    ("50G", r"50G"),
    ("25G", r"25G"),
    ("10G", r"10G"),
    ("AI/智算数据中心", r"人工智能|AI|智算|云计算|数据中心|算力"),
    ("5G/移动承载", r"\b5G\b|\b4G\b|前传|中回传|承载"),
    ("PON/FTTx接入", r"PON|FTTx|OLT|ONU|固网接入"),
    ("相干/DCI/骨干", r"相干|ZR\+?|DCI|骨干|城域|WSS|OXC"),
]

# `points.csv.判定等级` is an admission path plus an optional parenthesized
# process note ("判定闸-生产中(kimi取证;锚待复核)"). Ranking must key on the
# path alone, otherwise the 195 bracketed rows miss the enumeration and fall
# back to the unknown default rank.
ADMISSION_RANK = {
    "判定闸-生产中": 5,
    "node_wide_gate": 5,
    "edge_backed": 4,
    "cross_reference": 3,
    "context_only": 2,
}
UNKNOWN_ADMISSION_RANK = 1
UNKNOWN_ADMISSION_LABEL = "未标注准入路径"
PARENTHETICAL = re.compile(r"[（(][^)）]*[)）]")

# Coarse tree cells merge sub-capabilities whose design difficulty and route
# relevance differ: C5 merges several kinds of electrical chip, M1 merges
# several substrate/epitaxy platforms, MOD1 merges several rate generations
# (the enumerations live in tree.yaml and are never reproduced here). Their
# parenthetical enumeration is a navigation aid, not evidence: matching
# products or materials against it credits every company in the cell with every
# sub-capability. Overlap with a coarse cell is a navigation fact only — it
# never implies product supply or full route capability, so neither the cell's
# member list nor any undisclosed sub-capability may reach the product field.
# Splitting the cells themselves is an architecture decision, not done here.
COARSE_CELLS = {
    "C5": "多类电芯片子能力同格",
    "M1": "多种衬底与外延平台同格",
    "MOD1": "多个速率代际同格",
}
COARSE_CELL_BOUNDARY = (
    "粗粒度格：本行只表示公司能力与该格发生交集，"
    "不推出具体产品供货，也不构成完整路线能力"
)
COARSE_CELL_REQUIREMENT = "子能力须逐条披露支撑"

FIELDNAMES = [
    "公司代码",
    "公司",
    "市场",
    "行业分类",
    "主环节",
    "cell_id",
    "细分节点",
    "技术路线",
    "具体产品",
    "材料与技术",
    "工艺能力",
    "规格与应用",
    "当前阶段",
    "产业角色",
    # 保持 capability_details.csv 的既有 canonical schema；reader 将该列
    # 解释为准入路径，并在展示时去除括号内过程备注。
    "证据等级",
    "证据日期",
    "来源锚点",
    "原始披露摘要",
]


def clean(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip().strip('"')
    return value


def extract_url(value: str) -> str:
    match = re.search(r"https?://[^\s\]）)>,，；;`]+", value or "")
    return match.group(0).rstrip(".,") if match else ""


def tree_metadata() -> dict[str, dict[str, str]]:
    text = (ROOT / "tree.yaml").read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r"\{cell_id:\s*([^,\s]+),\s*名称:\s*(.*?),\s*路线:\s*([^,}]+)"
        r"(?:,\s*工艺备注:\s*(.*?))?\}"
    )
    for match in pattern.finditer(text):
        cell_id, name, route, process_note = match.groups()
        result[cell_id] = {
            "name": clean(name),
            "route": clean(route),
            "process_note": clean(process_note or ""),
        }
    return result


def stage_for(cell_id: str) -> str:
    for stage, prefixes, _ in reversed(STAGES):
        if any(cell_id.startswith(prefix) for prefix in prefixes):
            return stage
    return "其他"


def unique_matches(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    found = []
    for label, pattern in patterns:
        if re.search(pattern, text, flags=re.I) and label not in found:
            found.append(label)
    return found


def admission_path(value: str) -> str:
    """Admission path without the parenthesized review-process note.

    The note is trailing and may itself contain brackets, so everything from
    the first bracket is dropped instead of matching a balanced pair — a
    balanced match would leave a nested note's tail glued to the path.
    """
    text = clean(value)
    return re.split(r"[（(]", text, maxsplit=1)[0].strip() or text


def admission_rank(value: str) -> int:
    return ADMISSION_RANK.get(admission_path(value), UNKNOWN_ADMISSION_RANK)


def coarse_cell_note(cell_id: str) -> str:
    """Fixed boundary line for coarse cells.

    Names the cell but never its members: reproducing the merged sub-capability
    enumeration here would put undisclosed tokens (e.g. MCU next to a
    disclosure-backed DSP) into the product field.
    """
    merged = COARSE_CELLS.get(cell_id)
    if not merged:
        return ""
    return f"{COARSE_CELL_BOUNDARY}（{cell_id} {merged}；{COARSE_CELL_REQUIREMENT}）"


def cell_label(cell_id: str, node_name: str) -> str:
    """Node name with the sub-capability enumeration of coarse cells removed."""
    if cell_id not in COARSE_CELLS:
        return node_name
    return PARENTHETICAL.sub("", node_name).strip() or node_name


def stage_detail(text: str, point_status: str) -> str:
    checks = [
        ("规模量产/批量交付", r"规模量产|大批量|批量供货|批量出货|批量销售|批量产销"),
        ("量产/产业化", r"已实现量产|实现量产|量产线|产业化|成熟应用|生产中"),
        ("小批量/试产", r"小批量|试产"),
        ("送样/验证/导入", r"送样|验证|导入"),
        (
            "生产经营中",
            r"研发[、与及/]*生产|研发[、与及/]*制造|研发.*销售|生产.*销售|"
            r"提供.*光模块|主营业务|业务.*涵盖.*销售|营业收入",
        ),
        ("研发/建设中", r"在研|研发|开发中|在建|持续进行中"),
    ]
    for label, pattern in checks:
        if re.search(pattern, text, flags=re.I):
            return label
    return point_status or "披露未细分"


def role_for(cell_id: str, text: str) -> str:
    if re.search(r"委托加工|OEM|EMS|代工", text, flags=re.I):
        return "专业代工/制造服务"
    if cell_id.startswith("MOD"):
        return "光模块设计与制造"
    if cell_id.startswith("EMS"):
        return "模块代工与系统制造"
    if cell_id.startswith("EQ"):
        return "生产设备/检测工具"
    if cell_id.startswith("M"):
        return "材料或晶圆工艺参与者"
    if cell_id.startswith("C"):
        if re.search(r"外部代工|流片采用外部", text):
            return "芯片设计与产品定义（外部流片）"
        if re.search(r"外延|晶圆|FAB|全流程", text, flags=re.I):
            return "芯片IDM/制造平台"
        return "芯片设计或制造"
    if cell_id.startswith("P"):
        return "芯片封装与筛选"
    if cell_id.startswith("D"):
        return "光器件/光组件制造"
    if cell_id.startswith("B"):
        return "电路板或结构材料制造"
    return "产业链参与者"


def material_technology(text: str, node_name: str) -> str:
    tokens = unique_matches(
        text,
        [
            ("InP", r"\bInP\b|磷化铟"),
            ("GaAs", r"\bGaAs\b|砷化镓"),
            ("Si/SOI", r"\bSOI\b|硅光|硅基"),
            ("SiN", r"\bSiN\b"),
            ("PLC", r"\bPLC\b"),
            ("TFLN/铌酸锂", r"铌酸锂|\bTFLN\b"),
            ("陶瓷", r"陶瓷"),
            ("石英", r"石英"),
            ("高频高速覆铜板", r"覆铜板|LowDK|高速板"),
            ("金属有机源/特气", r"MO源|三甲基|磷烷|砷烷|磷化氢|砷化氢"),
        ],
    )
    if tokens:
        return "、".join(tokens)
    if any(word in node_name for word in ("材料", "衬底", "外延", "陶瓷", "板材")):
        return node_name
    return "披露未细分"


def granular_rows() -> list[dict[str, str]]:
    meta = tree_metadata()
    universe = participation.unique_universe()
    universe_names = {row["名称"] for row in universe}
    universe_by_name = {row["名称"]: row for row in universe}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for point in participation.read_rows("points.csv"):
        if point["状态"] != "生产中":
            continue
        company = participation.resolve_company(point["公司"], universe_names)
        if company:
            grouped[(company, point["cell_id"])].append(point)

    result = []
    for (company, cell_id), points in grouped.items():
        company_meta = universe_by_name[company]
        node = meta.get(cell_id, {"name": cell_id, "route": "未标", "process_note": ""})
        quotes = []
        for point in points:
            quote = clean(point.get("命中引语", ""))
            if quote and quote not in quotes:
                quotes.append(quote)
        quote_text = "；".join(quotes)
        label = cell_label(cell_id, node["name"])
        combined = f"{label} {node['process_note']} {quote_text}"
        evidence_and_process = f"{node['process_note']} {quote_text}"
        products = unique_matches(combined, PRODUCT_PATTERNS)
        processes = unique_matches(evidence_and_process, PROCESS_PATTERNS)
        specs = unique_matches(quote_text, SPEC_PATTERNS)
        if not products:
            products = [label]
        if not processes and node["process_note"]:
            processes = [node["process_note"]]
        best_point = max(points, key=lambda point: admission_rank(point.get("判定等级", "")))
        anchors = [extract_url(point.get("锚点URL", "")) for point in points]
        anchor = next((value for value in anchors if value), clean(best_point.get("锚点URL", "")))
        dates = [point.get("检索日期", "") for point in points if point.get("检索日期")]
        product_value = "、".join(products)
        note = coarse_cell_note(cell_id)
        if note:
            product_value = f"{product_value}｜{note}"
        result.append(
            {
                "公司代码": company_meta["代码"],
                "公司": company,
                "市场": company_meta["市场"],
                "行业分类": company_meta["行业分类"],
                "主环节": stage_for(cell_id),
                "cell_id": cell_id,
                "细分节点": node["name"],
                "技术路线": node["route"],
                "具体产品": product_value,
                "材料与技术": material_technology(combined, label),
                "工艺能力": "、".join(processes) if processes else "披露未细分",
                "规格与应用": "、".join(specs) if specs else "披露未细分",
                "当前阶段": stage_detail(quote_text, best_point.get("状态", "")),
                "产业角色": role_for(cell_id, combined),
                "证据等级": best_point.get("判定等级", ""),
                "证据日期": max(dates) if dates else "",
                "来源锚点": anchor,
                "原始披露摘要": quote_text,
            }
        )

    stage_index = {stage: index for index, (stage, _, _) in enumerate(STAGES)}
    return sorted(
        result,
        key=lambda row: (
            row["公司代码"],
            stage_index.get(row["主环节"], 99),
            row["cell_id"],
        ),
    )


def write_capability_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def register_font() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"中文字体不存在: {FONT_PATH}")
    pdfmetrics.registerFont(TTFont("CN", str(FONT_PATH)))


def pdf_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN",
            parent=base["Title"],
            fontName="CN",
            fontSize=24,
            leading=33,
            textColor=colors.HexColor("#102A43"),
            spaceAfter=7 * mm,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCN",
            fontName="CN",
            fontSize=9.5,
            leading=15,
            textColor=colors.HexColor("#526777"),
        ),
        "company": ParagraphStyle(
            "CompanyCN",
            fontName="CN",
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#102A43"),
        ),
        "meta": ParagraphStyle(
            "MetaCN",
            fontName="CN",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#6B7885"),
        ),
        "label": ParagraphStyle(
            "LabelCN",
            fontName="CN",
            fontSize=7.4,
            leading=10,
            textColor=colors.HexColor("#5B6670"),
        ),
        "body": ParagraphStyle(
            "BodyCN",
            fontName="CN",
            fontSize=8,
            leading=11.4,
            textColor=colors.HexColor("#273746"),
        ),
        "quote": ParagraphStyle(
            "QuoteCN",
            fontName="CN",
            fontSize=7.2,
            leading=10.2,
            textColor=colors.HexColor("#667481"),
        ),
        "center": ParagraphStyle(
            "CenterCN",
            fontName="CN",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#25445A"),
        ),
    }


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def evidence_badge(grade: str, label: str | None = None) -> str:
    grade = (grade or "D").upper()
    safe_grade = grade if grade in {"A", "B", "C", "D"} else "D"
    return (
        f'<span class="ev ev-{safe_grade.lower()}" '
        f'title="证据等级 {esc(safe_grade)}">{esc(label or safe_grade)}</span>'
    )


def route_section() -> str:
    rows = read_csv(ROUTE_BOM_CSV)
    routes: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        routes[row["产品路线"]].append(row)

    axis_rows = [
        (
            "产品 / 标准轴",
            "800G DR8、1.6T DR8、400ZR",
            "定义速率、距离、调制与互操作边界；本节按这一轴拆 BOM。",
        ),
        (
            "电接口 / 重定时轴",
            "FRO、LRO、LPO",
            "描述模块是否保留完整 DSP / Retimer，不能与产品标准并列替代。",
        ),
        (
            "封装 / 系统架构轴",
            "可插拔、NPO、CPO",
            "描述光引擎与交换 ASIC 的物理位置、维护与散热方式。",
        ),
        (
            "光子平台轴",
            "离散 EML、硅光、相干光子集成",
            "描述光器件实现平台；硅光可跨越多种产品与封装架构。",
        ),
    ]
    axis_html = "".join(
        f"<tr><td><b>{esc(axis)}</b></td><td>{esc(examples)}</td><td>{esc(boundary)}</td></tr>"
        for axis, examples, boundary in axis_rows
    )

    route_cards = []
    for route_name in ("800G DR8", "1.6T DR8", "400ZR"):
        route_rows = routes[route_name]
        first = route_rows[0]
        bom_rows = []
        for row in route_rows:
            source = row["来源"]
            source_html = (
                f'<a href="{esc(source)}" target="_blank" rel="noreferrer">标准材料</a>'
                if source.startswith(("http://", "https://"))
                else "来源待补"
            )
            bom_rows.append(
                "<tr>"
                f"<td><b>{esc(row['BOM分组'])}</b></td>"
                f"<td>{esc(row['关键组成'])}</td>"
                f"<td>{esc(row['说明'])}</td>"
                f"<td>{evidence_badge(row['证据等级'])} {source_html}</td>"
                "</tr>"
            )
        route_cards.append(
            f"""
            <article class="route-card">
              <div class="route-title">
                <div><b>{esc(route_name)}</b><span>{esc(first['应用边界'])}</span></div>
                <small>{esc(first['产品标准轴'])}</small>
              </div>
              <div class="route-meta">
                <span><b>电接口</b>{esc(first['电接口轴'])}</span>
                <span><b>封装</b>{esc(first['封装架构轴'])}</span>
                <span><b>光子平台</b>{esc(first['光子平台轴'])}</span>
              </div>
              <table class="route-bom">
                <tr><th>BOM 分组</th><th>关键组成</th><th>边界说明</th><th>证据</th></tr>
                {''.join(bom_rows)}
              </table>
            </article>
            """
        )

    return f"""
  <!-- 3 产品路线 BOM -->
  <div class="sec" id="s3">
    <h2><span class="tag">路线</span>先分比较轴，再按产品路线拆 BOM</h2>
    <div class="desc">800G DR8、1.6T DR8、400ZR属于产品 / 标准轴；LPO属于电接口实现轴，CPO属于封装与系统架构轴，硅光属于光子平台轴。四个轴可以组合，但不能放在同一列表中互相替代。</div>
    <h3 class="sub">3.0 四个正交比较轴</h3>
    <table class="axis-table">
      <tr><th>比较轴</th><th>典型选项</th><th>回答的问题</th></tr>
      {axis_html}
    </table>
    <div class="route-grid">{''.join(route_cards)}</div>
    <div class="note">证据口径：A = 已发布标准 / Implementation Agreement；B = 制定中的 IEEE 项目材料或标准未限定的工程实现。路线 BOM 只描述“典型组成与标准边界”，不把某一厂商方案写成全行业唯一配置。</div>
  </div>
"""


def macro_evidence_panel() -> str:
    """全量宏观结论审计表(macro_evidence.csv 新schema):编号/等级/结论/出处描述/可点链接/口径备注。
    模式源自codex 2026-07-28证据升级稿,内容以csv为唯一数据源(纪律6)。"""
    rows = read_csv(MACRO_EVIDENCE_CSV)
    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    rows.sort(key=lambda r: (order.get(r.get("证据等级", "D"), 9), r.get("claim_id", "")))
    audit_rows = []
    for row in rows:
        links = [u for u in (row.get("链接") or "").split() if u.startswith(("http://", "https://"))]
        links_html = " ".join(
            f'<a href="{esc(u)}" target="_blank" rel="noreferrer" class="srclnk">原文{i+1}</a>'
            for i, u in enumerate(links)
        ) or '<span class="source-gap">无一手链接</span>'
        audit_rows.append(
            "<tr>"
            f'<td class="rid">{esc(row["claim_id"])}</td>'
            f"<td>{evidence_badge(row['证据等级'])}</td>"
            f"<td>{esc(row['量化结论'])}</td>"
            f"<td>{esc(row.get('来源描述',''))} {links_html}</td>"
            f"<td>{esc(row.get('口径备注','') or row.get('处理方式',''))}</td>"
            "</tr>"
        )
    return f"""
  <div class="sec evidence-audit" id="evidence-audit">
    <h2><span class="tag">审计</span>量化结论证据分级（逐条出处可点）</h2>
    <div class="desc">首页 headline 只用 A 级（可重算账本/已发布标准）。B=机构一手或厂商规格（附口径引用）；C=二手汇总仅方向性参考——多家二手互引是回声室不是一手，B5/B6/B7 类升级已按此标准压回 C；D 不采用。</div>
    <table class="evidence-table">
      <tr><th>ID</th><th>级</th><th>结论</th><th>出处</th><th>口径备注</th></tr>
      {''.join(audit_rows)}
    </table>
  </div>
"""


def errata_section() -> str:
    """勘误与撤点区:从triage渲染否认性关案与撤点记录——账本敢撤回,是可信度而非缺陷。"""
    rows = read_csv(ROOT / "triage.csv" if False else "triage.csv") if False else []
    import csv as _csv
    with open(ROOT / "triage.csv", encoding="utf-8-sig") as fh:
        rows = list(_csv.DictReader(fh))
    hits = [r for r in rows if re.search(r"撤点|撤销|关案", (r.get("理由") or "") + (r.get("引语或线索摘要") or ""))]
    seen, items = set(), []
    for r in hits:
        key = r.get("公司")
        if key in seen:
            continue
        seen.add(key)
        items.append(
            f'<div class="k-card"><div class="k-head"><b>{esc(r.get("公司",""))}</b>'
            f'<span class="k-cells">{esc(r.get("处置",""))} · {esc(r.get("会话日期",""))}</span></div>'
            f'<div class="k-plain">{esc((r.get("引语或线索摘要") or "").strip(chr(34))[:160])}\n→ {esc((r.get("理由") or "")[:200])}</div></div>'
        )
    if not items:
        return ""
    return f"""
    <div class="sec" id="s10">
      <h2><span class="tag">勘误</span>勘误与撤点：我们撤回过什么、为什么</h2>
      <div class="desc">否认性证据（公司自己说"没做/未量产"）优先于暧昧文本。账本因此变小的每一次，都让剩下的每一行更硬。</div>
      {''.join(items)}
    </div>
"""


def edge_year(row: dict[str, str]) -> int:
    years = [int(value) for value in re.findall(r"20\d{2}", row.get("财年", ""))]
    return max(years) if years else 0


def resolve_edge_url(
    row: dict[str, str],
    by_id: dict[str, dict[str, str]],
    seen: set[str] | None = None,
) -> str:
    direct = extract_url(row.get("锚点", ""))
    if direct:
        return direct
    seen = set(seen or ())
    edge_id = row.get("edge_id", "")
    if edge_id in seen:
        return ""
    seen.add(edge_id)
    for ref in re.findall(r"E\d{3}", row.get("锚点", "")):
        if ref in by_id:
            resolved = resolve_edge_url(by_id[ref], by_id, seen)
            if resolved:
                return resolved
    return ""


def normalized_party(value: str) -> str:
    value = clean(value)
    aliases = {
        "中际旭创(作为客户)": "中际旭创",
        "Fabrinet(解匿)": "Fabrinet",
        "ficonTEC(罗博特科)": "罗博特科",
    }
    if value in aliases:
        return aliases[value]
    return re.sub(r"[（(].*?[）)]", "", value).strip()


def company_for_party(party: str, company_names: set[str]) -> str:
    normalized = normalized_party(party)
    if normalized in company_names:
        return normalized
    matches = [
        company
        for company in company_names
        if len(company) >= 3 and (company in normalized or normalized in company)
    ]
    return max(matches, key=len) if matches else ""


def verified_edges_by_company(
    rows: list[dict[str, str]],
) -> tuple[dict[str, list[dict[str, str]]], int]:
    company_names = {row["公司"] for row in rows}
    all_edges = read_csv(EDGES_CSV)
    by_id = {row["edge_id"]: row for row in all_edges}
    eligible = []
    for row in all_edges:
        if row["edge_id"] not in READER_EDGE_IDS or row.get("边等级") != "实边":
            continue
        if "待" in row.get("验证状态", "") or edge_year(row) < 2023:
            continue
        if "匿名" in row.get("供方", "") + row.get("需方", ""):
            continue
        if "跨行业" in row.get("备注", ""):
            continue
        url = resolve_edge_url(row, by_id)
        supplier = company_for_party(row["供方"], company_names)
        customer = company_for_party(row["需方"], company_names)
        if not url or not (supplier or customer):
            continue
        record = dict(row)
        record["_url"] = url
        record["_supplier_company"] = supplier
        record["_customer_company"] = customer
        eligible.append(record)

    # One reader edge per named supplier-customer pair; retain the newest filing.
    deduped: dict[tuple[str, str], dict[str, str]] = {}
    for row in sorted(eligible, key=edge_year, reverse=True):
        pair = (normalized_party(row["供方"]), normalized_party(row["需方"]))
        deduped.setdefault(pair, row)

    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in deduped.values():
        for company in {row["_supplier_company"], row["_customer_company"]} - {""}:
            if len(result[company]) < 2:
                result[company].append(row)
    displayed_ids = {
        row["edge_id"]
        for company_edges in result.values()
        for row in company_edges
    }
    return result, len(displayed_ids)


def edge_summary(row: dict[str, str]) -> str:
    metric = clean(row.get("占比或金额原文", ""))
    if not metric:
        bits = [clean(row.get("数值", "")), clean(row.get("单位", ""))]
        metric = "".join(bit for bit in bits if bit)
    return metric or "实名关系已在原始披露中核验"


def paragraph(value: str, style) -> Paragraph:
    normalized = (value or "").replace("<br/>", "\n")
    return Paragraph(esc(normalized).replace("\n", "<br/>"), style)


def page_decor(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(colors.HexColor("#102A43"))
    canvas.rect(0, height - 12 * mm, width, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("CN", 8)
    canvas.drawString(18 * mm, height - 7.8 * mm, "光模块产业链公司能力明细")
    canvas.setFillColor(colors.HexColor("#7A8792"))
    canvas.setFont("CN", 7)
    canvas.drawRightString(width - 18 * mm, 9 * mm, str(doc.page))
    canvas.restoreState()


def build_pdf(path: Path, rows: list[dict[str, str]]) -> None:
    register_font()
    styles = pdf_styles()
    companies: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        companies[row["公司"]].append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=18 * mm,
        bottomMargin=15 * mm,
        title="光模块产业链公司能力明细",
        author="光模块产业结构与公司能力地图",
    )
    story = [
        Spacer(1, 21 * mm),
        Paragraph("光模块产业链<br/>公司能力明细", styles["title"]),
        Paragraph(
            "以“公司 × 细分节点”为最小单元，逐项呈现具体产品、材料与技术、工艺、规格与应用、当前阶段、产业角色和披露证据。",
            styles["subtitle"],
        ),
        Spacer(1, 13 * mm),
    ]
    stats = [
        paragraph(f"{len(companies)} 家公司", styles["center"]),
        paragraph(f"{len(rows)} 条能力记录", styles["center"]),
        paragraph(f"{len({row['cell_id'] for row in rows})} 个细分节点", styles["center"]),
    ]
    stat_table = Table([stats], colWidths=[56 * mm] * 3)
    stat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4F8")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5E1E8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5E1E8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ]
        )
    )
    story += [
        stat_table,
        Spacer(1, 11 * mm),
        Paragraph(
            "阅读口径：只展示已进入“生产中”证据闸的公司；字段未被原始披露支撑时明确写“披露未细分”。本报告不讨论谁向谁供货。"
            "“准入依据”只说明该点以何种路径进入账本（判定闸 / 边支持 / 交叉引用等），不是 A–D 证据等级；"
            "C5 / M1 / MOD1 为粗粒度格，卡片只表示公司能力与该格发生交集，不推出具体产品供货或完整路线能力。",
            styles["subtitle"],
        ),
        PageBreak(),
    ]

    for company in sorted(companies, key=lambda name: (companies[name][0]["公司代码"], name)):
        caps = companies[company]
        first = caps[0]
        company_label = (
            company
            if first["公司代码"] == company
            else f"{company}　{first['公司代码']}"
        )
        story.append(CondPageBreak(60 * mm))
        header = Table(
            [
                [
                    Paragraph(
                        f"<b>{esc(company_label)}</b>",
                        styles["company"],
                    ),
                    Paragraph(
                        f"{esc(first['市场'])}<br/>{esc(first['行业分类'])}<br/>{len(caps)}项已确认能力",
                        styles["meta"],
                    ),
                ]
            ],
            colWidths=[128 * mm, 48 * mm],
        )
        header.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF1F6")),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C8D7E2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.8 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8 * mm),
                ]
            )
        )
        story += [header, Spacer(1, 2 * mm)]
        for cap in caps:
            detail_rows = [
                [
                    paragraph("节点", styles["label"]),
                    paragraph(
                        f"{cap['cell_id']} · {cap['细分节点']}｜{cap['技术路线']}",
                        styles["body"],
                    ),
                ],
                [paragraph("具体产品", styles["label"]), paragraph(cap["具体产品"], styles["body"])],
                [
                    paragraph("技术 / 工艺", styles["label"]),
                    paragraph(
                        f"材料与技术：{cap['材料与技术']}<br/>工艺能力：{cap['工艺能力']}",
                        styles["body"],
                    ),
                ],
                [
                    paragraph("规格 / 阶段", styles["label"]),
                    paragraph(
                        f"规格与应用：{cap['规格与应用']}<br/>当前阶段：{cap['当前阶段']}｜角色：{cap['产业角色']}",
                        styles["body"],
                    ),
                ],
                [
                    paragraph("披露证据", styles["label"]),
                    paragraph(cap["原始披露摘要"][:420], styles["quote"]),
                ],
            ]
            cap_table = Table(detail_rows, colWidths=[24 * mm, 152 * mm], splitByRow=1)
            cap_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F4F7F9")),
                        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#D7E0E7")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E1E7EC")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2.2 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2.2 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
                    ]
                )
            )
            story += [
                cap_table,
                Paragraph(
                    f"准入依据：{esc(admission_path(cap['证据等级']) or UNKNOWN_ADMISSION_LABEL)}　|　证据日期：{esc(cap['证据日期'] or '—')}　|　"
                    + (
                        f'<link href="{esc(cap["来源锚点"])}" color="#165DFF">查看来源</link>'
                        if cap["来源锚点"].startswith(("http://", "https://"))
                        else esc(cap["来源锚点"] or "来源锚点已登记")
                    ),
                    styles["meta"],
                ),
                Spacer(1, 3 * mm),
            ]
        story.append(Spacer(1, 2 * mm))

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)


def capability_section(
    rows: list[dict[str, str]],
    edges_by_company: dict[str, list[dict[str, str]]],
) -> str:
    companies: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        companies[row["公司"]].append(row)
    cards = []
    for company in sorted(companies, key=lambda name: (companies[name][0]["公司代码"], name)):
        caps = companies[company]
        first = caps[0]
        cap_html = []
        for cap in caps:
            source = esc(cap["来源锚点"] or "来源锚点已登记")
            if cap["来源锚点"].startswith(("http://", "https://")):
                source = (
                    f'<a href="{esc(cap["来源锚点"])}" target="_blank" rel="noreferrer">'
                    "查看原始披露</a>"
                )
            cap_html.append(
                f"""
                <div class="cap-item">
                  <div class="cap-head"><b>{esc(cap['cell_id'])} · {esc(cap['细分节点'])}</b>
                    <span>{esc(cap['技术路线'])}</span></div>
                  <dl>
                    <dt>具体产品</dt><dd>{esc(cap['具体产品'])}</dd>
                    <dt>材料与技术</dt><dd>{esc(cap['材料与技术'])}</dd>
                    <dt>工艺能力</dt><dd>{esc(cap['工艺能力'])}</dd>
                    <dt>规格与应用</dt><dd>{esc(cap['规格与应用'])}</dd>
                    <dt>阶段与角色</dt><dd>{esc(cap['当前阶段'])} · {esc(cap['产业角色'])}</dd>
                    <dt>披露摘要</dt><dd class="quote">{esc(cap['原始披露摘要'])}</dd>
                  </dl>
                  <div class="cap-source">{esc(admission_path(cap['证据等级']) or UNKNOWN_ADMISSION_LABEL)} · {esc(cap['证据日期'])} · {source}</div>
                </div>
                """
            )
        searchable = " ".join(
            [
                company,
                first["公司代码"],
                first["市场"],
                first["行业分类"],
                *[
                    " ".join(
                        cap[field]
                        for field in (
                            "主环节",
                            "细分节点",
                            "具体产品",
                            "材料与技术",
                            "工艺能力",
                            "规格与应用",
                        )
                    )
                    for cap in caps
                ],
            ]
        )
        edge_rows = []
        for edge in edges_by_company.get(company, []):
            supplier = normalized_party(edge["供方"])
            customer = normalized_party(edge["需方"])
            edge_rows.append(
                f"""
                <li>
                  <span class="edge-grade">实边</span>
                  <b>{esc(supplier)}</b><span class="edge-arrow">→</span><b>{esc(customer)}</b>
                  <small>{esc(edge['财年'])} · {esc(edge_summary(edge))}</small>
                  <a href="{esc(edge['_url'])}" target="_blank" rel="noreferrer">原始披露</a>
                </li>
                """
            )
        edge_html = (
            f"""
            <div class="verified-edges">
              <div class="verified-edges-title">已验证供货边 <span>仅展示实名、原文核验“实边”</span></div>
              <ul>{''.join(edge_rows)}</ul>
            </div>
            """
            if edge_rows
            else ""
        )
        cards.append(
            f"""
            <article class="company-cap" data-layer="{esc(caps[0]['主环节'])}"
              data-search="{esc(searchable.lower())}">
              <div class="company-cap-title">
                <div><b>{esc(company)}</b><span>{esc(first['公司代码'])}</span></div>
                <small>{esc(first['市场'])} · {esc(first['行业分类'])} · {len(caps)}项能力</small>
              </div>
              {edge_html}
              {''.join(cap_html)}
            </article>
            """
        )
    layers = "".join(
        f'<option value="{esc(stage)}">{esc(stage)}</option>'
        for stage, _, _ in STAGES
        if any(row["主环节"] == stage for row in rows)
    )
    return f"""
    <div class="sec" id="s7">
      <h2><span class="tag">能力卡</span>公司 × 细分节点能力明细</h2>
      <div class="desc">公司清单已并入能力卡，不再单列“企业越多越完整”的重复图谱。每项能力包含产品、技术、工艺、规格、阶段、角色与证据；卡片顶部仅叠加少量实名、原文核验供货实边，不由公司同处一条产业链推断供货关系。<br>“准入依据”只说明该点以何种路径进入账本（判定闸 / 边支持 / 交叉引用等），不是 A–D 证据等级；能力末尾的“准入依据 · 日期 · 来源”同理。<br>C5、M1 与 MOD1 是粗粒度格（各合入多种设计难度不同的子能力，成员枚举见 tree.yaml）：卡片上的产品与材料标签只来自原始披露，不来自格名枚举，边界提示也不复述成员；能力与该格发生交集不推出具体产品供货，也不构成完整路线能力。</div>
      <div class="cap-summary">
        <div><b>{len(companies)}</b><span>已确认公司</span></div>
        <div><b>{len(rows)}</b><span>能力记录</span></div>
        <div><b>{len({row['cell_id'] for row in rows})}</b><span>覆盖细分节点</span></div>
      </div>
      <div class="cap-tools">
        <input id="capSearch" type="search" placeholder="搜索公司、产品、工艺、规格或节点">
        <select id="capLayer"><option value="">全部环节</option>{layers}</select>
        <span id="capCount">{len(companies)} 家公司</span>
      </div>
      <div class="company-cap-grid" id="companyCaps">{''.join(cards)}</div>
    </div>
    """


CAPABILITY_CSS = """
  .ev{display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;padding:0 6px;border-radius:10px;font:700 10px/1 ui-monospace,SFMono-Regular,Menlo,monospace;vertical-align:middle}
  .ev-a{background:#dcfce7;color:#166534;border:1px solid #86efac}
  .ev-b{background:#dbeafe;color:#1e40af;border:1px solid #93c5fd}
  .ev-c{background:#fef3c7;color:#92400e;border:1px solid #fcd34d}
  .ev-d{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
  .evidence-legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin:12px 0;font-size:11px;color:var(--muted)}
  .evidence-legend>span{display:flex;align-items:center;gap:6px}
  .evidence-table td:nth-child(1){font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}
  .source-gap{color:#b45309}
  .axis-table td:first-child{white-space:nowrap}
  .route-grid{display:grid;grid-template-columns:1fr;gap:14px;margin-top:16px}
  .route-card{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
  .route-title{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:13px 15px;background:#eaf1f6;border-bottom:1px solid #d5e1e8}
  .route-title b{font-size:17px;color:var(--accent)}
  .route-title span{font-size:11px;color:var(--muted);margin-left:8px}
  .route-title small{color:var(--muted)}
  .route-meta{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:10px 14px;background:#f8fafc;border-bottom:1px solid #e2e8f0}
  .route-meta span{font-size:11px;color:#475569}
  .route-meta b{display:block;color:#64748b;margin-bottom:2px}
  .route-bom{margin:0;border:0;border-radius:0}
  .route-bom a{color:#2563eb;text-decoration:none;white-space:nowrap}
  .cap-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}
  .cap-summary div{background:#eef4f8;border:1px solid #d5e1e8;border-radius:12px;padding:12px;text-align:center}
  .cap-summary b{display:block;font-size:20px;color:var(--accent)}
  .cap-summary span{font-size:11px;color:var(--muted)}
  .cap-tools{position:sticky;top:8px;z-index:5;display:grid;grid-template-columns:1fr 220px auto;gap:10px;align-items:center;background:#fff;padding:10px;border:1px solid var(--line);border-radius:12px;margin:12px 0}
  .cap-tools input,.cap-tools select{width:100%;border:1px solid #cbd5e1;border-radius:8px;padding:9px 11px;background:#fff;color:var(--ink)}
  .cap-tools span{font-size:12px;color:var(--muted);white-space:nowrap}
  .company-cap-grid{display:grid;grid-template-columns:1fr;gap:14px}
  .company-cap{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
  .company-cap-title{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:13px 15px;background:#eaf1f6;border-bottom:1px solid #d5e1e8}
  .company-cap-title b{font-size:16px;color:var(--accent)}
  .company-cap-title span{font-size:11px;margin-left:8px;color:var(--muted)}
  .company-cap-title small{color:var(--muted)}
  .verified-edges{padding:10px 15px;background:#fffbeb;border-bottom:1px solid #fde68a}
  .verified-edges-title{font-size:11px;font-weight:700;color:#92400e;margin-bottom:6px}
  .verified-edges-title span{font-weight:400;color:#a16207;margin-left:6px}
  .verified-edges ul{list-style:none;padding:0;margin:0;display:grid;gap:5px}
  .verified-edges li{display:flex;align-items:center;gap:5px;flex-wrap:wrap;font-size:11px;color:#475569}
  .verified-edges li small{color:#78716c}
  .verified-edges li a{color:#2563eb;text-decoration:none;margin-left:auto}
  .edge-grade{border:1px solid #f59e0b;background:#fef3c7;color:#92400e;border-radius:8px;padding:1px 6px;font-size:9px;font-weight:700}
  .edge-arrow{color:#d97706}
  .cap-item{padding:13px 15px;border-bottom:1px dashed var(--line)}
  .cap-item:last-child{border-bottom:0}
  .cap-head{display:flex;justify-content:space-between;gap:12px;font-size:13px;margin-bottom:8px}
  .cap-head span{font-size:11px;color:#475569;background:#f1f5f9;padding:2px 8px;border-radius:10px}
  .cap-item dl{display:grid;grid-template-columns:94px 1fr;margin:0;font-size:12px}
  .cap-item dt{color:var(--muted);padding:5px 8px;background:#f8fafc;border-bottom:1px solid #eef2f7}
  .cap-item dd{margin:0;padding:5px 8px;border-bottom:1px solid #eef2f7}
  .cap-item dd.quote{color:#64748b}
  .cap-source{font-size:10.5px;color:#94a3b8;margin-top:8px}
  .cap-source a{color:#2563eb;text-decoration:none}
  @media(max-width:900px){.cap-tools{grid-template-columns:1fr}.cap-summary,.route-meta{grid-template-columns:1fr}.company-cap-title,.route-title{align-items:flex-start;flex-direction:column}.cap-item dl{grid-template-columns:1fr}.cap-item dt{font-weight:600}.route-card{overflow-x:auto}.route-bom{min-width:720px}.verified-edges li a{margin-left:0}}
"""

CAPABILITY_JS = """
<script>
(() => {
  const search = document.getElementById('capSearch');
  const layer = document.getElementById('capLayer');
  const count = document.getElementById('capCount');
  const cards = Array.from(document.querySelectorAll('.company-cap'));
  const apply = () => {
    const q = search.value.trim().toLowerCase();
    const selected = layer.value;
    let visible = 0;
    cards.forEach(card => {
      const ok = (!q || card.dataset.search.includes(q)) &&
        (!selected || card.dataset.layer === selected);
      card.style.display = ok ? '' : 'none';
      if (ok) visible += 1;
    });
    count.textContent = `${visible} 家公司`;
  };
  search.addEventListener('input', apply);
  layer.addEventListener('change', apply);
})();
</script>
"""


def legacy_quantitative_badges(source: str) -> str:
    """Mark legacy non-primary numeric claims without touching CSS percentages."""
    badge = ' <span class="ev ev-c" title="机构/二手口径，待逐项补原始锚点">C</span>'
    claims = [
        "100G→800G 用3年，800G→1.6T 仅2年",
        "40-56%",
        "60-65%",
        "50-70%",
        "30-50%",
        "25-40%",
        "15-20%",
        "70-80%",
        "40-50%",
        "30-40%",
        "5-10%",
        "800G 模块功耗近 50%",
        "数通占比&gt;70%",
        "模块&gt;1.5万只",
        "需求 &gt;1.5 万只",
        "份额 &gt;60%",
        "国产化 &gt;65%",
        "份额 &gt;30%",
        "市占 ~75%",
        "国产化 &lt;3%",
        "国产 &lt;20%",
        "市占&gt;80%",
        "占总投资 &gt;90%",
        "1.6T 达 60%+",
        "1.6T达60%+",
        "毛利 60%+",
        "毛利60%+",
        "毛利 50%+",
        "毛利 40-50%",
        "毛利40-50%",
        "毛利30-40%",
        "毛利~20%",
        "全球出货第一",
        "10G DFB 全球出货第一",
        "高端 EML &lt;10%",
        "合计 &gt;80%",
        "国产化 &lt;3%（最大短板）",
        "数通市场（&gt;70%）",
        "电信市场（≈30%，基本盘）",
        "72 个 800G/1.6T",
        "8-10 周压缩至 4 周以内",
        "约 2-3 年窗口",
        "交期排至 2027+",
    ]
    for claim in claims:
        source = source.replace(claim, claim + badge)
    return source


def homepage_kpis(rows: list[dict[str, str]], edge_count: int) -> str:
    companies = len({row["公司"] for row in rows})
    nodes = len({row["cell_id"] for row in rows})
    return f"""
  <!-- KPI：只展示可重算或已核验数据 -->
  <div class="kpis">
    <div class="kpi"><div class="v">{companies}</div><div class="l">已确认公司 {evidence_badge('A')}</div><div class="s">生产中证据闸</div></div>
    <div class="kpi"><div class="v">{len(rows)}</div><div class="l">能力记录 {evidence_badge('A')}</div><div class="s">公司 × 细分节点</div></div>
    <div class="kpi"><div class="v">{nodes}</div><div class="l">覆盖节点 {evidence_badge('A')}</div><div class="s">由账本实时重算</div></div>
    <div class="kpi"><div class="v">3</div><div class="l">产品路线 BOM {evidence_badge('A')}</div><div class="s">DR8 / 1.6T / 400ZR</div></div>
    <div class="kpi"><div class="v">{edge_count}</div><div class="l">已验证供货实边 {evidence_badge('A')}</div><div class="s">实名 + 原始披露</div></div>
  </div>
"""


def knowledge_section() -> str:
    """产业知识层(knowledge.yaml):大白话结论+判定用法+锚型证据。无证据条目已被 scan.py 不变量⑧拦在库外。"""
    kpath = ROOT / "knowledge.yaml"
    if not kpath.exists():
        return ""
    import yaml

    kb = yaml.safe_load(kpath.read_text(encoding="utf-8")).get("knowledge", []) or []
    cards = []
    for k in sorted(kb, key=lambda x: x["id"]):
        cells = "、".join(k.get("格") or []) or "通用"
        ev_html = []
        for e in k.get("证据") or []:
            a = e.get("锚", "")
            if isinstance(a, dict):
                a = "；".join(f"{x}：{a[x]}" for x in ("关键词", "语料范围", "检索日期", "命中数") if x in a)
            a = str(a)
            link = f'<a href="{html.escape(a)}" target="_blank">原文PDF</a>' if a.startswith("http") else html.escape(a[:110])
            ev_html.append(
                f'<li><b>{html.escape(e.get("谁",""))}</b>：{html.escape((e.get("原话") or "")[:120])}'
                f'<br><span class="k-anchor">锚（{html.escape(e.get("锚型","?"))}）：{link}</span></li>'
            )
        judge = (k.get("怎么用它判断") or "").strip()
        cards.append(f"""
      <div class="k-card">
        <div class="k-head"><b>{html.escape(k['id'])}</b>　{html.escape(k['标题'])}<span class="k-cells">适用：{html.escape(cells)}</span></div>
        <div class="k-plain">{html.escape(k['一句话'].strip())}</div>
        {f'<details><summary>怎么用它判断</summary><pre class="k-judge">{html.escape(judge)}</pre></details>' if judge else ''}
        <details><summary>证据（{len(k.get('证据') or [])} 条，逐条带锚）</summary><ul class="k-ev">{''.join(ev_html)}</ul></details>
      </div>""")
    return f"""
    <div class="sec" id="s9">
      <h2><span class="tag">知识</span>产业知识层：这环节干嘛的、为什么难、怎么判断谁够格</h2>
      <div class="desc">来自 knowledge.yaml。每条为大白话结论 + 判定用法 + 逐条证据（谁说的 / 原话 / 锚）。无证据的"常识"被校验器机器拦截，进不了本层；负证据（"查过没有"）必须附检索协议（关键词 / 语料范围 / 日期 / 命中数）。</div>
      {''.join(cards)}
    </div>
"""


def calls_intelligence_section(path: Path = CALLS_INTELLIGENCE_CSV) -> str:
    return render_intelligence_section(
        path,
        positioning_path=CALLS_POSITIONING_JSON,
        event_path=CALLS_EVENT_JSON,
    )


def assert_event_intelligence_html(output_path: Path, event_path: Path = CALLS_EVENT_JSON) -> None:
    """Fail the atomic build if reviewed event evidence silently disappears."""
    source = output_path.read_text(encoding="utf-8")
    required = ("本期公司事件", "数据版本：")
    missing = [marker for marker in required if marker not in source]
    with event_path.open(encoding="utf-8") as handle:
        projection = json.load(handle)
    for event in projection.get("radar_events", []):
        for evidence in event.get("evidence", []):
            url = evidence.get("url")
            if url and f'href="{html.escape(url, quote=True)}"' not in source:
                missing.append(f"source link for {event.get('event_id')}")
    if missing:
        raise RuntimeError(f"event intelligence HTML acceptance failed: {', '.join(missing)}")


KNOWLEDGE_CSS = """
  .k-card{border:1px solid var(--line);border-radius:12px;padding:14px;margin:10px 0;background:#fff}
  .k-head{font-size:14px;margin-bottom:6px}
  .k-cells{float:right;font-size:11px;color:var(--muted)}
  .k-plain{font-size:13px;color:#374151;white-space:pre-line;background:#f8fafc;border-left:3px solid var(--accent);padding:8px 12px;border-radius:6px}
  .k-card details{margin-top:8px;font-size:12.5px}
  .k-card summary{cursor:pointer;color:var(--accent)}
  .k-judge{white-space:pre-wrap;font-family:inherit;font-size:12.5px;background:#fffbeb;border:1px dashed #fde68a;border-radius:8px;padding:10px;margin:6px 0}
  .k-ev{margin:6px 0 0 18px}
  .k-ev li{margin:6px 0}
  .k-anchor{color:var(--muted);font-size:11.5px}
"""

CALLS_CSS = """
  .calls-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:12px}
  .calls-card{border:1px solid #bfdbfe;border-radius:12px;padding:13px;background:#f8fbff}
  .calls-head{display:flex;justify-content:space-between;gap:12px;font-size:13px}
  .calls-head span{font-size:10.5px;color:#1d4ed8;background:#dbeafe;padding:3px 7px;border-radius:999px;white-space:nowrap}
  .calls-meta{font-size:11.5px;color:var(--muted);margin:7px 0}
  .calls-card ul{font-size:12px;margin:7px 0 7px 18px;padding:0}
  .calls-gap{font-size:11px;line-height:1.5;background:#fff7ed;border-left:3px solid #fb923c;padding:7px 9px}
  .calls-positioning{font-size:11px;line-height:1.5;background:#f0fdf4;border-left:3px solid #22c55e;padding:7px 9px;margin-top:7px}
  .calls-positioning>ul{margin:5px 0 0 14px;padding:0}
  .calls-positioning li{margin:4px 0}
  .event-radar{margin:14px 0 20px}
  .event-policy,.event-coverage{font-size:11.5px;color:var(--muted);margin:6px 0}
  .event-list{display:grid;gap:10px;margin:10px 0}
  .event-card{border:1px solid #c7d2fe;border-radius:12px;padding:12px;background:#fff}
  .event-head{display:flex;align-items:center;gap:8px;font-size:13px;flex-wrap:wrap}
  .event-kind,.event-status{font-size:10.5px;padding:3px 7px;border-radius:999px;background:#e0e7ff;color:#3730a3}
  .event-status.asserted{background:#fff7ed;color:#9a3412}
  .event-status.corroborated{background:#ecfdf5;color:#047857}
  .event-meta{font-size:11.5px;color:var(--muted);margin:7px 0}
  .event-card details{font-size:11.5px;margin-top:6px;background:#f8fafc;padding:7px 9px;border-radius:8px}
  .event-card summary{cursor:pointer;color:#1d4ed8}
"""


def build_html(template_path: Path, output_path: Path, rows: list[dict[str, str]]) -> None:
    source = template_path.read_text(encoding="utf-8")
    edges_by_company, edge_count = verified_edges_by_company(rows)
    source = source.replace(
        "<title>光模块行业产业链全景图 · 产业链优先版</title>",
        "<title>光模块行业产业链全景图 · 公司能力细化版</title>",
    )
    source = source.replace(
        "<h1>光模块行业产业链全景图 · 产业链优先版</h1>",
        "<h1>光模块行业产业链全景图 · 公司能力细化版</h1>",
    )
    source = source.replace(
        '<a href="#s3">③ 技术路线对比</a>',
        '<a href="#s3">③ 产品路线 BOM</a>',
    )
    source = source.replace(
        '<a href="#s7">⑦ 企业图谱</a>',
        '<a href="#s7">⑦ 公司能力卡</a>',
    )
    source = re.sub(
        r"  <!-- KPI -->.*?(?=  <!-- 1 价值分布 -->)",
        homepage_kpis(rows, edge_count) + "\n" + macro_evidence_panel() + "\n",
        source,
        flags=re.S,
    )
    source = re.sub(
        r"  <!-- 3 技术路线 -->.*?(?=  <!-- 4 中游制造与产品 -->)",
        route_section() + "\n",
        source,
        flags=re.S,
    )
    source = re.sub(
        r"  <!-- 7 企业图谱 -->.*?(?=  <footer>)",
        "",
        source,
        flags=re.S,
    )
    source = source.replace(
        "厂商名称与上市公司映射统一放在第 7 节；本节只解释产业分工，不展开具体供货关系。",
        "厂商名称、细分能力与少量已验证供货实边统一放在第 7 节能力卡；本节只解释产业分工。",
    )
    source = legacy_quantitative_badges(source)
    intelligence_html = calls_intelligence_section()
    source = source.replace("</style>", CAPABILITY_CSS + KNOWLEDGE_CSS + CALLS_CSS + "\n</style>")
    extra_nav = ""
    if intelligence_html:
        extra_nav += '\n    <a href="#s8">⑧ 海外电话会与官网技术情报</a>'
    extra_nav += '\n    <a href="#s9">⑨ 产业知识</a>\n    <a href="#s10">⑩ 勘误与撤点</a>'
    source = source.replace(
        '<a href="#s7">⑦ 公司能力卡</a>',
        '<a href="#s7">⑦ 公司能力卡</a>' + extra_nav,
    )
    source = source.replace(
        "  <footer>",
        capability_section(rows, edges_by_company) + "\n  <footer>",
        1,
    )
    source = source.replace(
        "  <footer>",
        intelligence_html + "\n  <footer>",
        1,
    )
    source = source.replace(
        "  <footer>",
        knowledge_section() + "\n  <footer>",
        1,
    )
    source = source.replace(
        "  <footer>",
        errata_section() + "\n  <footer>",
        1,
    )
    source = source.replace("</body>", CAPABILITY_JS + "\n</body>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--pdf-output", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--html-template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--html-output", type=Path, default=DEFAULT_HTML)
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="validate and rebuild calls projections plus HTML without rewriting CSV/PDF",
    )
    args = parser.parse_args()

    validate_calls(ROOT)
    render_calls(ROOT)
    rows = granular_rows()
    if not args.html_only:
        write_capability_csv(args.csv_output, rows)
        build_pdf(args.pdf_output, rows)
    build_html(args.html_template, args.html_output, rows)
    assert_event_intelligence_html(args.html_output)
    print(
        f"companies={len({row['公司'] for row in rows})} "
        f"capabilities={len(rows)} nodes={len({row['cell_id'] for row in rows})}"
    )
    if not args.html_only:
        print(args.csv_output)
        print(args.pdf_output)
    print(args.html_output)


if __name__ == "__main__":
    main()
