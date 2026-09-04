"""Standard-library HTML adapter for the WorkBuddy intelligence section."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path


def render_intelligence_section(
    path: Path,
    positioning_path: Path | None = None,
    event_path: Path | None = None,
) -> str:
    rows = []
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    positioning = None
    if positioning_path is not None and positioning_path.exists():
        with positioning_path.open(encoding="utf-8") as handle:
            positioning = json.load(handle)
    event_projection = None
    if event_path is not None and event_path.exists():
        with event_path.open(encoding="utf-8") as handle:
            event_projection = json.load(handle)
    if not rows and event_projection is None:
        return ""

    def esc(value: str) -> str:
        return html.escape(value or "", quote=True)

    cards = []
    for row in sorted(rows, key=lambda item: item.get("theme_id", "")):
        evidence = " / ".join(
            f"{label}={row.get(field) or 'insufficient'}"
            for label, field in (("可行性", "feasibility"), ("稀缺性", "scarcity"), ("可替代性", "substitutability"))
        )
        details = []
        if row.get("demand_evidence"):
            details.append(f"<li><b>需求侧：</b>{esc(row['demand_evidence'])}</li>")
        if row.get("supply_evidence"):
            details.append(f"<li><b>供给侧：</b>{esc(row['supply_evidence'])}</li>")
        if row.get("company_progress"):
            details.append(f"<li><b>公司进展：</b>{esc(row['company_progress'])}</li>")
        block = render_positioning_block(positioning, row.get("theme_id", "")) if positioning else ""
        cards.append(f"""
      <article class="calls-card">
        <div class="calls-head"><b>{esc(row.get('theme_id', ''))}　{esc(row.get('theme_name', ''))}</b><span>情报层 / 候选验证链</span></div>
        <div class="calls-meta">节点 {esc(row.get('cell_id') or row.get('route_item_id') or '未映射')} · 状态 {esc(row.get('bottleneck_status') or 'unknown')} · {esc(evidence)}</div>
        <ul>{''.join(details) or '<li>尚无已审核供需证据。</li>'}</ul>
        <div class="calls-gap"><b>尚缺证据：</b>{esc(row.get('missing_evidence') or '未登记')}<br><b>来源 ID：</b>{esc(row.get('source_ids') or '尚无已审核来源')}<br><b>canonical point 只读引用：</b>{esc(row.get('canonical_point_ids') or '无')} · as of {esc(row.get('as_of') or 'unknown')}</div>
        {block}
      </article>""")
    event_html = render_event_radar(event_projection) if event_projection else ""
    return f"""
    <div class="sec" id="s8">
      <h2><span class="tag">情报</span>海外电话会与官网技术情报</h2>
      <div class="desc"><b>这是独立情报层，不是 canonical 事实账本。</b>候选卡点、公司主张、技术演示和潜在能力匹配均保留证据状态；不得据此推导已解决卡点、供货关系或投资结论。</div>
      {event_html}
      {('<h3>主题与卡点视图</h3><div class="calls-grid">' + ''.join(cards) + '</div>') if cards else ''}
    </div>
"""


def render_event_radar(projection: dict) -> str:
    """Render traceable reviewed events without recomputing evidence policy."""
    events = projection.get("radar_events", [])
    coverage = projection.get("coverage_summary", {})

    def esc(value: object) -> str:
        return html.escape(str(value or ""), quote=True)

    def badge(evidence: list[dict]) -> str:
        kinds = {item.get("statement_kind") for item in evidence}
        if "technical_demo" in kinds:
            return "Demo"
        if "forward_looking" in kinds:
            return "Guidance"
        if "corporate_narrative" in kinds:
            return "Narrative"
        return "Actual"

    cards = []
    for event in events:
        evidence = event.get("evidence", [])
        details = []
        for item in evidence:
            source = (
                f'<a href="{esc(item.get("url"))}" target="_blank" rel="noopener noreferrer">'
                f'{esc(item.get("title") or item.get("disclosure_id"))}</a>'
                if item.get("url") else esc(item.get("title") or item.get("disclosure_id"))
            )
            details.append(
                "<details><summary>查看原文与证据</summary>"
                f'<div><b>原文短引：</b>“{esc(item.get("quote"))}”</div>'
                f'<div><b>锚点：</b>{esc(item.get("anchor"))}</div>'
                f'<div><b>来源：</b>{source} · {esc(item.get("content_class"))} · {esc(item.get("provenance_class"))}</div>'
                f'<div><b>披露/检索/复核：</b>{esc(item.get("published_at"))} / {esc(item.get("retrieved_at"))} / {esc(item.get("claim_reviewed_at"))}</div>'
                "</details>"
            )
        cards.append(
            '<article class="event-card">'
            f'<div class="event-head"><span class="event-kind">{badge(evidence)}</span>'
            f'<b>{esc(event.get("primary_subject_id"))} · {esc(event.get("summary"))}</b>'
            f'<span class="event-status {esc(event.get("event_status"))}">{esc(event.get("event_status"))}</span></div>'
            f'<div class="event-meta">事件时间 {esc(event.get("occurred_start") or "unknown")} · '
            f'{esc(event.get("event_category"))} / {esc(event.get("lifecycle_stage"))} · '
            f'主题 {esc(";".join(event.get("theme_ids", [])) or "未映射")}</div>'
            + "".join(details)
            + "</article>"
        )
    counts = coverage.get("processing_status_counts", {})
    coverage_text = " / ".join(f"{esc(key)}={esc(value)}" for key, value in sorted(counts.items())) or "无披露件"
    data_version = (
        f"disclosures={esc(coverage.get('disclosure_count', 0))} · "
        f"latest_reviewed={esc(coverage.get('latest_reviewed_at') or 'unknown')}"
    )
    return (
        '<div class="event-radar">'
        '<h3>本期公司事件</h3>'
        '<div class="event-policy">新闻只是证据入口：<code>asserted</code> 表示第一方已披露，'
        '<code>corroborated</code> 才表示已有独立来源支持。</div>'
        f'<div class="event-coverage">处理覆盖：{coverage_text} · 最新披露 {esc(coverage.get("latest_disclosure_at") or "unknown")} · 最新复核 {esc(coverage.get("latest_reviewed_at") or "unknown")}</div>'
        f'<div class="event-version" data-event-version="{data_version}">数据版本：{data_version}</div>'
        f'<div class="event-list">{"".join(cards) or "尚无已完成锚点复核的事件。"}</div>'
        '</div>'
    )


def render_positioning_block(positioning: dict, theme_id: str) -> str:
    """Domestic capability positioning block appended to one theme card.

    Runs for every theme card when a positioning projection is available.
    Themes with no reviewed requirement state that explicitly (not as an
    evidence-coverage gap) and still carry the two fixed unsupported reasons
    for the structural views.  Shows same-node capability evidence (cell_only),
    truly comparable metric records only, and evidence-coverage gaps.  Never
    states competition, substitution, collaboration, supply, satisfaction or
    benefit.
    """
    matches = [
        m for m in positioning.get("requirement_matches", [])
        if m.get("theme_id") == theme_id
    ]
    comparisons = [
        c for c in positioning.get("metric_comparisons", [])
        if c.get("theme_id") == theme_id and c.get("status") == "compared"
    ]
    gaps = [
        g for g in positioning.get("evidence_coverage_gaps", [])
        if g.get("theme_id") == theme_id
    ]

    def esc(value: object) -> str:
        if value is None:
            return ""
        return html.escape(str(value), quote=True)

    parts = []
    if not (matches or comparisons or gaps):
        parts.append(
            "<li>本主题尚无 reviewed constraint requirement，不生成同节点定位或能力缺口判断。</li>"
        )
    else:
        if matches:
            rows = "".join(
                f"<li>{esc(m['company'])} · <code>{esc(m['point_id'])}</code> · {esc(m['point_status'])} · {esc(m['listing_label'])} · basis={esc(m['basis'])} · requirement={esc(m['requirement_id'])} · 证据 {esc(m['source_claim_ids'])}（requirement as of {esc(m['requirement_as_of'])} / point as of {esc(m['point_as_of'])}）</li>"
                for m in sorted(matches, key=lambda x: (x["company"], x["point_id"]))
            )
            parts.append(f"<li><b>同节点能力证据：</b><ul>{rows}</ul></li>")
        if comparisons:
            rows = "".join(
                f"<li>{esc(c['company'])} · <code>{esc(c['point_id'])}</code> {esc(c['metric_name'])}={esc(c['metric_value'])} {esc(c['metric_unit'])} vs {esc(c['target_value'])} {esc(c['unit'])}（{esc(c['comparator'])}，通过={esc(c['passes'])}，as of {esc(c['metric_as_of'])}）</li>"
                for c in sorted(comparisons, key=lambda x: (x["company"], x["point_id"]))
            )
            parts.append(f"<li><b>数值对比（仅真正可比）：</b><ul>{rows}</ul></li>")
        if gaps:
            rows = "".join(
                f"<li>{esc(g['message'])}（{esc(g['requirement_id'])}）</li>"
                for g in sorted(gaps, key=lambda x: x["requirement_id"])
            )
            parts.append(f"<li><b>证据覆盖缺口：</b><ul>{rows}</ul></li>")
    parts.append(
        f"<li><b>结构视图 structural_alternative：</b>{esc(positioning.get('structural_alternatives_unsupported_reason', ''))}</li>"
    )
    parts.append(
        f"<li><b>结构视图 co_required：</b>{esc(positioning.get('co_required_unsupported_reason', ''))}</li>"
    )
    return (
        '<div class="calls-positioning"><b>国内能力定位（basis=cell_only，不推导商业结论）：</b>'
        f"<ul>{''.join(parts)}</ul></div>"
    )


def render_all_positioning_blocks(positioning: dict, theme_ids: list[str] | None = None) -> str:
    """Concatenate positioning blocks for the given theme cards.

    When ``theme_ids`` is omitted, only themes present in the projection are
    rendered.  Validator passes the full theme set so every WorkBuddy card block
    (including no-requirement cards) is covered by the forbidden-word scan.
    """
    if theme_ids is None:
        theme_ids = set()
        for view in ("requirement_matches", "metric_comparisons", "evidence_coverage_gaps"):
            for entry in positioning.get(view, []):
                theme_ids.add(entry.get("theme_id", ""))
    return "".join(render_positioning_block(positioning, t) for t in sorted(theme_ids))
