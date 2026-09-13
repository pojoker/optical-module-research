#!/usr/bin/env python3
"""Generate the confirmed optical-module supply-chain company PDF."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    CondPageBreak,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import participation

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "pdf" / "光模块供应链已确认公司清单.pdf"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Light.ttc")

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


def register_fonts() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"中文字体不存在: {FONT_PATH}")
    pdfmetrics.registerFont(TTFont("CN", str(FONT_PATH)))


def cell_names() -> dict[str, str]:
    text = (ROOT / "tree.yaml").read_text(encoding="utf-8")
    return {
        cell: name.strip()
        for cell, name in re.findall(
            r"\{cell_id:\s*([^,\s]+),\s*名称:\s*(.*?),\s*路线:", text
        )
    }


def stage_for(cell_id: str) -> str:
    # Long prefixes must win over their first character.
    for stage, prefixes, _ in reversed(STAGES):
        if any(cell_id.startswith(prefix) for prefix in prefixes):
            return stage
    return "其他"


def clean_quote(value: str, limit: int = 130) -> str:
    value = re.sub(r"\s+", " ", value).strip().strip('"')
    return value[:limit] + ("…" if len(value) > limit else "")


def build_companies() -> list[dict]:
    universe = participation.unique_universe()
    universe_names = {row["名称"] for row in universe}
    universe_by_name = {row["名称"]: row for row in universe}
    points_by_company: dict[str, list[dict[str, str]]] = defaultdict(list)

    for point in participation.read_rows("points.csv"):
        if point["状态"] != "生产中":
            continue
        company = participation.resolve_company(point["公司"], universe_names)
        if company:
            points_by_company[company].append(point)

    cells = cell_names()
    companies = []
    for company, points in points_by_company.items():
        meta = universe_by_name[company]
        by_cell: dict[str, list[dict[str, str]]] = defaultdict(list)
        for point in points:
            by_cell[point["cell_id"]].append(point)
        cell_ids = sorted(
            by_cell,
            key=lambda cell: (
                next(
                    (i for i, (stage, _, _) in enumerate(STAGES) if stage_for(cell) == stage),
                    99,
                ),
                cell,
            ),
        )
        descriptions = []
        anchors = []
        for cell_id in cell_ids:
            cell_points = by_cell[cell_id]
            quotes = []
            for point in cell_points:
                quote = clean_quote(point["命中引语"])
                if quote and quote not in quotes:
                    quotes.append(quote)
                if point.get("锚点URL"):
                    anchors.append(point["锚点URL"])
            descriptions.append(
                {
                    "cell_id": cell_id,
                    "cell_name": cells.get(cell_id, cell_id),
                    "stage": stage_for(cell_id),
                    "text": "；".join(quotes),
                }
            )
        primary_stage = descriptions[0]["stage"]
        dates = [point["检索日期"] for point in points if point.get("检索日期")]
        companies.append(
            {
                "code": meta["代码"],
                "name": company,
                "market": meta["市场"],
                "industry": meta["行业分类"],
                "primary_stage": primary_stage,
                "descriptions": descriptions,
                "date": max(dates) if dates else "",
                "anchor": next(
                    (participation.extract_url(anchor) for anchor in anchors if participation.extract_url(anchor)),
                    "",
                ),
            }
        )
    stage_index = {stage: index for index, (stage, _, _) in enumerate(STAGES)}
    return sorted(
        companies,
        key=lambda company: (
            stage_index.get(company["primary_stage"], 99),
            company["code"],
        ),
    )


class SupplyChainFlow(Flowable):
    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 45 * mm

    def draw(self):
        canvas = self.canv
        labels = ["材料", "芯片", "封装/器件", "电路结构", "光模块", "制造交付"]
        gap = 3 * mm
        box_width = (self.width - gap * (len(labels) - 1)) / len(labels)
        y = 18 * mm
        colors_list = [
            colors.HexColor("#DCECF3"),
            colors.HexColor("#DDE5F5"),
            colors.HexColor("#E8E1F2"),
            colors.HexColor("#F3E7DD"),
            colors.HexColor("#DCEFEA"),
            colors.HexColor("#DDEBE5"),
        ]
        for index, label in enumerate(labels):
            x = index * (box_width + gap)
            canvas.setFillColor(colors_list[index])
            canvas.roundRect(x, y, box_width, 13 * mm, 3 * mm, fill=1, stroke=0)
            canvas.setFillColor(colors.HexColor("#193042"))
            canvas.setFont("CN", 8.5)
            canvas.drawCentredString(x + box_width / 2, y + 4.8 * mm, label)
            if index < len(labels) - 1:
                canvas.setStrokeColor(colors.HexColor("#8193A2"))
                canvas.line(x + box_width, y + 6.5 * mm, x + box_width + gap - 1, y + 6.5 * mm)
        canvas.setFillColor(colors.HexColor("#EEF1F4"))
        canvas.roundRect(0, 1 * mm, self.width, 11 * mm, 3 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#536271"))
        canvas.setFont("CN", 8)
        canvas.drawCentredString(
            self.width / 2,
            5.2 * mm,
            "设备与仪器贯穿外延、光刻、固晶、耦合、键合、检测和测试",
        )


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCN",
            parent=base["Title"],
            fontName="CN",
            fontSize=25,
            leading=34,
            textColor=colors.HexColor("#102A43"),
            spaceAfter=8 * mm,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCN",
            fontName="CN",
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#526777"),
        ),
        "section": ParagraphStyle(
            "SectionCN",
            fontName="CN",
            fontSize=17,
            leading=23,
            textColor=colors.white,
            spaceBefore=3 * mm,
            spaceAfter=4 * mm,
        ),
        "company": ParagraphStyle(
            "CompanyCN",
            fontName="CN",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#12202F"),
        ),
        "meta": ParagraphStyle(
            "MetaCN",
            fontName="CN",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#6B7885"),
        ),
        "body": ParagraphStyle(
            "BodyCN",
            fontName="CN",
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor("#273746"),
        ),
        "small": ParagraphStyle(
            "SmallCN",
            fontName="CN",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#667481"),
        ),
    }


def safe(value: str) -> str:
    return html.escape(value, quote=True)


def company_card(company: dict, styles: dict) -> KeepTogether:
    company_label = (
        company["name"]
        if company["code"] == company["name"]
        else f"{company['name']}　{company['code']}"
    )
    header = Table(
        [
            [
                Paragraph(
                    f"<b>{safe(company_label)}</b>",
                    styles["company"],
                ),
                Paragraph(
                    f"{safe(company['market'])}<br/>{safe(company['industry'])}",
                    styles["meta"],
                ),
            ]
        ],
        colWidths=[125 * mm, 45 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F7F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7E0E7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    elements = [header, Spacer(1, 1.5 * mm)]
    for item in company["descriptions"]:
        elements.append(
            Paragraph(
                f"<b>{safe(item['cell_id'])} · {safe(item['cell_name'])}</b>：{safe(item['text'])}",
                styles["body"],
            )
        )
        elements.append(Spacer(1, 1 * mm))
    source = "原始披露锚点已登记"
    if company["anchor"]:
        source = f'<link href="{safe(company["anchor"])}" color="#165DFF">查看公开披露原文</link>'
    elements.extend(
        [
            Paragraph(
                f"证据日期：{safe(company['date'] or '—')}　|　{source}",
                styles["small"],
            ),
            Spacer(1, 4 * mm),
        ]
    )
    return KeepTogether(elements)


def page_decor(canvas, doc):
    canvas.saveState()
    width, height = A4
    if doc.page > 1:
        canvas.setFillColor(colors.HexColor("#102A43"))
        canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("CN", 8)
        canvas.drawString(18 * mm, height - 8.4 * mm, "光模块供应链已确认公司清单")
    canvas.setFillColor(colors.HexColor("#7A8792"))
    canvas.setFont("CN", 7)
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def build_pdf(output: Path = OUTPUT) -> Path:
    register_fonts()
    companies = build_companies()
    _, register_stats = participation.build_register()
    expected_confirmed = register_stats.get("已确认参与", 0)
    if len(companies) != expected_confirmed:
        raise ValueError(
            f"PDF公司数与参与识别不一致: PDF={len(companies)}, 名单={expected_confirmed}"
        )
    styles = make_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=17 * mm,
        title="光模块供应链已确认公司清单",
        author="光模块供应链参与识别",
    )
    story = [
        Spacer(1, 20 * mm),
        Paragraph("光模块供应链<br/>已确认公司清单", styles["title"]),
        Paragraph(
            "回答两个问题：哪些公司已经有披露证据确认参与；它们位于供应链什么位置、具体做什么。",
            styles["subtitle"],
        ),
        Spacer(1, 14 * mm),
    ]
    stats = [
        [Paragraph(f"<b>{expected_confirmed}</b><br/>已确认公司", styles["subtitle"])],
        [Paragraph("<b>8</b><br/>供应链位置", styles["subtitle"])],
        [
            Paragraph(
                f"<b>{register_stats['年报已覆盖']} / {register_stats['公司总数']}</b><br/>年报语料覆盖",
                styles["subtitle"],
            )
        ],
    ]
    stat_table = Table([[row[0] for row in stats]], colWidths=[54 * mm] * 3)
    stat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4F8")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5E1E8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5E1E8")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
            ]
        )
    )
    story.extend(
        [
            stat_table,
            Spacer(1, 12 * mm),
            SupplyChainFlow(170 * mm),
            Spacer(1, 8 * mm),
            Paragraph(
                "判定口径：至少存在一条“生产中”的过闸证据才进入本报告。在建、送样、客户验证和仅有待判线索的公司不计入49家。"
                "同一公司可能横跨多个环节，正文会逐项列出。数据截至2026-07-25。",
                styles["small"],
            ),
            PageBreak(),
        ]
    )

    stage_color = {stage: color for stage, _, color in STAGES}
    for stage, _, color in STAGES:
        stage_companies = [company for company in companies if company["primary_stage"] == stage]
        if not stage_companies:
            continue
        title_table = Table(
            [[Paragraph(f"{safe(stage)}　{len(stage_companies)}家公司", styles["section"])]],
            colWidths=[170 * mm],
        )
        title_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                ]
            )
        )
        story.extend([CondPageBreak(60 * mm), title_table, Spacer(1, 3 * mm)])
        for company in stage_companies:
            story.append(company_card(company, styles))

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    return output


if __name__ == "__main__":
    print(build_pdf())
