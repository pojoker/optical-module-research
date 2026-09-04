"""Deterministic Markdown renderer. CSV remains the sole fact source."""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

from .event_intelligence import derive_event_projection, load_event_facts
from .positioning import derive_positioning, load_positioning_facts
from .schema import FILES, PANORAMA_FIELDS


REVIEW_SEMANTICS_NOTE = (
    "> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看"
    "“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。"
    "`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在"
    "与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；"
    "同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。"
)


def _load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _md(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _link_source(source: dict[str, str]) -> str:
    if source["url"]:
        return f"[{_md(source['source_id'])}]({source['url']})"
    return _md(source["source_id"])


def render(project_root: Path) -> list[Path]:
    calls_dir = project_root / "calls"
    tables = {name: _load(calls_dir / name) for name in FILES}
    out = calls_dir / "out"
    company_dir = out / "companies"
    if out.exists():
        shutil.rmtree(out)
    company_dir.mkdir(parents=True)

    sources = {row["source_id"]: row for row in tables["sources.csv"]}
    claims_by_company: dict[str, list[dict[str, str]]] = defaultdict(list)
    for claim in tables["claims.csv"]:
        claims_by_company[sources[claim["source_id"]]["company_id"]].append(claim)

    event_projection = derive_event_projection(load_event_facts(project_root))
    coverage = _compute_coverage(tables, sources, event_projection)

    written: list[Path] = []
    for company in sorted(tables["universe.csv"], key=lambda row: row["company_id"]):
        company_sources = sorted(
            (row for row in tables["sources.csv"] if row["company_id"] == company["company_id"] and row["source_scope"] == "quarterly"),
            key=lambda row: (row["period_end"], row["source_id"]), reverse=True,
        )
        company_claims = claims_by_company[company["company_id"]]
        state = coverage["company_states"][company["company_id"]]
        lines = [
            f"# {company['company_name']}：季度电话会卡", "",
            f"角色：`{company['role']}`。纳入理由：{company['inclusion_reason']}",
            "",
            "## 五级覆盖（本公司在该公司数中可复算）",
            "",
            REVIEW_SEMANTICS_NOTE,
            "",
            f"- 季度槽登记：{state['slots']}/4 个季度槽已登记（含未采集槽位）",
            f"- 可用来源：{state['available']}/4 个季度槽有 `available` 材料",
            f"- 陈述登记：{state['claims']} 条 `claims.csv` 陈述（含 candidate/rejected）",
            f"- 已核陈述：{state['reviewed_claims']} 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）",
            f"- 已核事件：{state['events']} 条已审核雷达事件（asserted {state['asserted_events']} / corroborated {state['corroborated_events']}）",
            "",
            "## 四季度覆盖", "", "| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |", "|---|---|---:|---|---|",
        ]
        for source in company_sources:
            lines.append(f"| {_md(source['slot_label'])} | {_link_source(source)} | {_md(source['source_grade'])} | {_md(source['availability'])} | {_md(source['missing_reason'] or source['acquisition_note'])} |")
        reviewed_management = [row for row in company_claims if row["review_status"] == "reviewed" and row["speaker_role"] == "management"]
        reviewed_technical = [row for row in company_claims if row["review_status"] == "reviewed" and row["speaker_role"] == "corporate_author"]
        analyst = [row for row in company_claims if row["speaker_role"] == "analyst"]
        other = [row for row in company_claims if row not in reviewed_management and row not in reviewed_technical and row not in analyst]
        lines.extend(["", "## 已审核管理层陈述", "", "> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。", ""])
        if reviewed_management:
            for claim in sorted(reviewed_management, key=lambda row: row["claim_id"]):
                source = sources[claim["source_id"]]
                lines.extend([
                    f"- `{claim['claim_id']}` · {claim['statement_type']} · {claim['event_type']} · {_link_source(source)} `{claim['anchor']}`",
                    f"  - 归纳：{claim['summary']}",
                    f"  - 原文短引：“{claim['quote']}”",
                ])
        else:
            lines.append("未知：本 MVP 尚无已审核管理层陈述。")
        lines.extend(["", "## 公司官网技术作者陈述（与管理层商业确认隔离）", ""])
        if reviewed_technical:
            for claim in sorted(reviewed_technical, key=lambda row: row["claim_id"]):
                source = sources[claim["source_id"]]
                lines.extend([
                    f"- `{claim['claim_id']}` · {claim['statement_type']} · {claim['event_type']} · {_link_source(source)} `{claim['anchor']}`",
                    f"  - 技术归纳：{claim['summary']}",
                    f"  - 原文短引：“{claim['quote']}”",
                    "  - 权限：只能作为技术证据，不能进入管理层商业 validations/commitments。",
                ])
        else:
            lines.append("无已审核公司官网技术作者陈述。")
        lines.extend(["", "## 分析师问题（不得视为管理层确认）", ""])
        if analyst:
            for claim in sorted(analyst, key=lambda row: row["claim_id"]):
                lines.append(f"- `{claim['claim_id']}` {claim['speaker']}：{claim['summary']}（{_link_source(sources[claim['source_id']])} `{claim['anchor']}`）")
        else:
            lines.append("无已登记分析师问题；这不代表市场没有相关关注。")
        lines.extend(["", "## 候选、驳回与未知", ""])
        if other:
            for claim in sorted(other, key=lambda row: row["claim_id"]):
                lines.append(f"- `{claim['claim_id']}` `{claim['review_status']}`：{claim['summary']}")
        else:
            lines.append("无候选或驳回陈述。未采集季度仍保持未知。")
        path = company_dir / f"{company['company_id'].lower()}-{_slug(company['company_name'])}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)

    themes = {row["theme_id"]: row for row in tables["themes.csv"]}
    matrix = ["# 跨公司议题矩阵", "", "> `analyst_question` 只显示关注点，不进入管理层事实列。冲突、未知和证据不足均显式保留。", "", "| 议题 | 供给侧已审核陈述 | 需求侧已审核陈述 | 交叉验证 | 结论状态 |", "|---|---|---|---|---|"]
    for theme in sorted(tables["themes.csv"], key=lambda row: row["theme_id"]):
        theme_claims = [row for row in tables["claims.csv"] if row["theme_id"] == theme["theme_id"] and row["review_status"] == "reviewed" and row["speaker_role"] == "management"]
        supply = "; ".join(f"{row['claim_id']} {row['summary']}" for row in theme_claims if row["side"] in {"supply", "both"}) or "未知"
        demand = "; ".join(f"{row['claim_id']} {row['summary']}" for row in theme_claims if row["side"] in {"demand", "both"}) or "未知"
        checks = [row for row in tables["validations.csv"] if row["theme_id"] == theme["theme_id"]]
        check_text = "; ".join(f"{row['relationship']}/{row['result_status']}: {row['rationale']}" for row in checks) or "未交叉验证"
        matrix.append(f"| {_md(theme['theme_id'] + ' ' + theme['theme_name'])} | {_md(supply)} | {_md(demand)} | {_md(check_text)} | {_md(theme['bottleneck_status'])} |")
    matrix.extend(["", "## 冲突登记", ""])
    contradictions = [row for row in tables["validations.csv"] if row["relationship"] == "contradicts" or row["result_status"] == "conflicting"]
    matrix.extend((f"- `{row['validation_id']}` {row['rationale']}" for row in contradictions) if contradictions else ["- 当前样本没有经审核的直接冲突；这表示“尚未观察到”，不表示不存在冲突。"]) 
    matrix_path = out / "theme-matrix.md"
    matrix_path.write_text("\n".join(matrix) + "\n", encoding="utf-8")
    written.append(matrix_path)

    links = tables["solution_links.csv"]
    chains = ["# 受限需求—卡点—解法—国内能力潜在匹配", "", "> 本页是候选验证链，不回写 canonical 账本；`node_overlap` 绝不表述为已经解决卡点。", ""]
    for limited in (row for row in tables["themes.csv"] if row["theme_type"] == "limited_demand"):
        bottlenecks = [row for row in tables["themes.csv"] if row["parent_theme_id"] == limited["theme_id"] and row["theme_type"] == "bottleneck"]
        for bottleneck in bottlenecks:
            solutions = [row for row in tables["themes.csv"] if row["parent_theme_id"] == bottleneck["theme_id"] and row["theme_type"] == "solution"]
            chains.extend([
                f"## {limited['theme_name']}", "",
                f"- 应用需求：{limited['application_demand']}",
                f"- 所需指标：{limited['required_metric']}",
                f"- 关键节点：{limited['critical_node']}（`{limited['cell_id'] or limited['route_item_id']}`）",
                f"- 限制因素：{limited['limiting_factor']}",
                f"- 受限结果：{limited['constrained_outcome']}",
                f"- 卡点状态：`{bottleneck['bottleneck_status']}`；{bottleneck['progress_gap']}",
            ])
            for solution in solutions:
                chains.append(f"- 候选解法：{solution['theme_name']}；可行性 `{solution['feasibility']}` / 稀缺性 `{solution['scarcity']}` / 可替代性 `{solution['substitutability']}`")
                for link in (row for row in links if row["solution_theme_id"] == solution["theme_id"]):
                    chains.extend([
                        f"- 国内能力潜在匹配：canonical `{link['point_id']}`，阶段 `{link['match_stage']}`，证据 `{link['evidence_status']}`",
                        f"  - 当前只能说：{link['conclusion']}",
                        f"  - 尚缺证据：{link['missing_evidence']}",
                    ])
            chains.append("")
    chain_path = out / "limited-demand-chains.md"
    chain_path.write_text("\n".join(chains), encoding="utf-8")
    written.append(chain_path)

    commitments = ["# 承诺—兑现账本", "", "| 承诺 | 目标 | 截止 | 状态 | 兑现证据 | 判断 |", "|---|---|---|---|---|---|"]
    for row in sorted(tables["commitments.csv"], key=lambda item: item["commitment_id"]):
        evidence = _link_source(sources[row["evidence_source_id"]]) if row["evidence_source_id"] else "尚未观察到"
        commitments.append(f"| {_md(row['commitment_id'] + ' / ' + row['claim_id'])} | {_md(row['target'])} | {_md(row['due_date'])} | {_md(row['status'])} | {_md(evidence)} | {_md(row['assessment'])} |")
    commitment_path = out / "commitments.md"
    commitment_path.write_text("\n".join(commitments) + "\n", encoding="utf-8")
    written.append(commitment_path)

    feedback = ["# 技术陈述—商业反馈", "", "> 技术博客由 `corporate_author` 提供，只说明技术主张或演示。只有独立的已审核管理层陈述才能形成商业反馈；`not_mentioned` 和 `pending` 均不代表确认。", "", "| 反馈 | 主题 | 技术证据 | 商业证据 | 状态 | 阶段 | 判断 |", "|---|---|---|---|---|---|---|"]
    claims = {row["claim_id"]: row for row in tables["claims.csv"]}
    for row in sorted(tables["technology_feedback.csv"], key=lambda item: item["feedback_id"]):
        tech = claims[row["technology_claim_id"]]
        commercial = claims.get(row["commercial_claim_id"])
        tech_ref = f"{tech['claim_id']} {_link_source(sources[tech['source_id']])}"
        commercial_ref = f"{commercial['claim_id']} {_link_source(sources[commercial['source_id']])}" if commercial else "未提及/待观察"
        feedback.append(
            f"| {_md(row['feedback_id'])} | {_md(row['theme_id'])} | {_md(tech_ref)} | {_md(commercial_ref)} | "
            f"{_md(row['feedback_status'] + '/' + row['evidence_status'])} | {_md(row['stage_before'] + ' → ' + row['stage_after'])} | {_md(row['rationale'])} |"
        )
    feedback_path = out / "technology-feedback.md"
    feedback_path.write_text("\n".join(feedback) + "\n", encoding="utf-8")
    written.append(feedback_path)

    panorama_path = out / "panorama-intelligence.csv"
    _write_panorama(panorama_path, tables, sources)
    written.append(panorama_path)

    positioning_path = out / "positioning.json"
    projection = derive_positioning(load_positioning_facts(project_root))
    positioning_path.write_text(
        json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(positioning_path)

    event_path = out / "event-intelligence.json"
    event_path.write_text(
        json.dumps(event_projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(event_path)

    index = ["# 海外电话会与官网技术情报层 MVP", "", "数据源仅为 `calls/*.csv`；本目录全部由渲染器重建。", "", REVIEW_SEMANTICS_NOTE, "", "## 覆盖分级（五级，分母与公司数可复算）", "", coverage["denominator_line"], "", "| 覆盖级别 | 定义 | 公司数 | 分母 |", "|---|---|---:|---:|"]
    for level_id, label, definition in (
        ("slot", "季度槽登记", "4 个季度槽均已登记（含 not_collected/unavailable 槽位）"),
        ("available_source", "可用来源", "4 个季度槽均有 `available` 材料"),
        ("claim", "陈述登记", "在 `claims.csv` 有至少 1 条陈述（含 candidate/rejected）"),
        ("reviewed_claim", "已核陈述", "有至少 1 条 `reviewed` 陈述（reviewed 仅表示原文已核）"),
        ("reviewed_event", "已核事件", "有至少 1 条已审核雷达事件（证据经 `anchor_reviewed`）"),
    ):
        level = coverage["levels"][level_id]
        index.append(f"| {label} | {definition} | {level} | {coverage['enabled_company_count']} |")
    inventory = coverage["slot_inventory"]
    index.extend([
        "",
        f"信源底账：`sources.csv` 共 {inventory['total_source_rows']} 行（季度槽材料 {inventory['quarterly_source_rows']} 行、"
        f"季度槽位 {inventory['quarterly_slot_positions']} 个）。这些行数是采集底账，"
        "不能单独用“N 家公司、M 行来源”表达研究结论覆盖；结论覆盖以上表五级为准。",
        "",
        "## 事件状态（asserted / corroborated 分列）",
        "",
        f"- asserted：{coverage['event_status_counts'].get('asserted', 0)} 条 —— 第一方主张，原文已核，但没有独立来源交叉支持。",
        f"- corroborated：{coverage['event_status_counts'].get('corroborated', 0)} 条 —— 存在与第一方不同 origin_group 且独立于第一方的来源支持"
        f"（{coverage['corroborated_event_ids'] or '无'}）。",
        "- 同源双证（同一 origin_group 的多份材料）不得升级为 corroborated；asserted 不代表已确认，corroborated 也不代表产能或卡点变化。",
        "",
        "## 输出", "", "- [公司事件雷达（JSON）](event-intelligence.json)", "- [跨公司议题矩阵](theme-matrix.md)", "- [受限需求链](limited-demand-chains.md)", "- [承诺—兑现账本](commitments.md)", "- [技术陈述—商业反馈](technology-feedback.md)", "- [全景情报投影（CSV）](panorama-intelligence.csv)", "- [国内能力定位投影（JSON）](positioning.json)", "", "## 公司季度卡", "",
    ])
    for company in sorted(tables["universe.csv"], key=lambda row: row["company_name"]):
        index.append(f"- [{company['company_name']}](companies/{company['company_id'].lower()}-{_slug(company['company_name'])}.md)")
    index_path = out / "README.md"
    index_path.write_text("\n".join(index) + "\n", encoding="utf-8")
    written.append(index_path)
    return written


def _compute_coverage(
    tables: dict[str, list[dict[str, str]]],
    sources: dict[str, dict[str, str]],
    event_projection: dict,
) -> dict:
    enabled = [
        row for row in tables["universe.csv"] if row["enabled"] == "yes"
    ]
    enabled_ids = {row["company_id"] for row in enabled}
    slots: dict[str, set[str]] = defaultdict(set)
    available: dict[str, set[str]] = defaultdict(set)
    quarterly_rows = 0
    for source in sources.values():
        if source["company_id"] not in enabled_ids or source["source_scope"] != "quarterly":
            continue
        slots[source["company_id"]].add(source["slot_label"])
        if source["availability"] == "available":
            available[source["company_id"]].add(source["slot_label"])
        quarterly_rows += 1
    claims_count: dict[str, int] = defaultdict(int)
    reviewed_count: dict[str, int] = defaultdict(int)
    for claim in tables["claims.csv"]:
        company_id = sources[claim["source_id"]]["company_id"]
        if company_id not in enabled_ids:
            continue
        claims_count[company_id] += 1
        if claim["review_status"] == "reviewed":
            reviewed_count[company_id] += 1
    events_by_subject: dict[str, list[dict]] = defaultdict(list)
    for row in event_projection["radar_events"]:
        events_by_subject[row["primary_subject_id"]].append(row)
    status_counts: dict[str, int] = defaultdict(int)
    corroborated_ids: list[str] = []
    for row in event_projection["radar_events"]:
        status_counts[row["event_status"]] += 1
        if row["event_status"] == "corroborated":
            corroborated_ids.append(row["event_id"])
    company_states: dict[str, dict[str, int]] = {}
    for company_id in sorted(enabled_ids):
        subject_events = events_by_subject.get(company_id, [])
        company_states[company_id] = {
            "slots": len(slots[company_id]),
            "available": len(available[company_id]),
            "claims": claims_count[company_id],
            "reviewed_claims": reviewed_count[company_id],
            "events": len(subject_events),
            "asserted_events": sum(row["event_status"] == "asserted" for row in subject_events),
            "corroborated_events": sum(row["event_status"] == "corroborated" for row in subject_events),
        }
    levels = {
        "slot": sum(len(slots[c]) == 4 for c in enabled_ids),
        "available_source": sum(len(available[c]) == 4 for c in enabled_ids),
        "claim": sum(claims_count[c] > 0 for c in enabled_ids),
        "reviewed_claim": sum(reviewed_count[c] > 0 for c in enabled_ids),
        "reviewed_event": sum(bool(events_by_subject.get(c)) for c in enabled_ids),
    }
    return {
        "enabled_company_count": len(enabled_ids),
        "levels": levels,
        "slot_inventory": {
            "total_source_rows": len(sources),
            "quarterly_source_rows": quarterly_rows,
            "quarterly_slot_positions": 4 * len(enabled_ids),
        },
        "event_status_counts": dict(sorted(status_counts.items())),
        "corroborated_event_ids": "、".join(sorted(corroborated_ids)),
        "company_states": company_states,
        "denominator_line": (
            f"分母：正式季度池 {len(enabled_ids)} 家 enabled 公司"
            "（`universe.csv` 中 `enabled=yes`）；watch 实体与发现候选不计入本表。"
        ),
    }


def _write_panorama(
    path: Path,
    tables: dict[str, list[dict[str, str]]],
    sources: dict[str, dict[str, str]],
) -> None:
    children: dict[str, set[str]] = defaultdict(set)
    for theme in tables["themes.csv"]:
        if theme["parent_theme_id"]:
            children[theme["parent_theme_id"]].add(theme["theme_id"])

    def family(theme_id: str) -> set[str]:
        result = {theme_id}
        pending = list(children.get(theme_id, set()))
        while pending:
            child = pending.pop()
            if child not in result:
                result.add(child)
                pending.extend(children.get(child, set()))
        return result

    output: list[dict[str, str]] = []
    for theme in sorted(tables["themes.csv"], key=lambda row: row["theme_id"]):
        related = family(theme["theme_id"])
        claims = [
            row for row in tables["claims.csv"]
            if row["theme_id"] in related and row["review_status"] == "reviewed"
        ]
        management = [row for row in claims if row["speaker_role"] == "management"]
        demand = [row for row in management if row["side"] in {"demand", "both"}]
        supply = [row for row in management if row["side"] in {"supply", "both"}]
        progress = [
            row for row in claims
            if row["speaker_role"] in {"management", "corporate_author"}
            and (row["event_type"] != "unknown" or row["statement_type"] in {"technical_claim", "technical_demo"})
        ]
        source_ids = sorted({row["source_id"] for row in claims})
        links = [
            row for row in tables["solution_links.csv"]
            if row["bottleneck_theme_id"] in related or row["solution_theme_id"] in related
        ]
        missing = [theme["progress_gap"]] + [row["missing_evidence"] for row in links]
        output.append({
            "theme_id": theme["theme_id"],
            "theme_type": theme["theme_type"],
            "theme_name": theme["theme_name"],
            "cell_id": theme["cell_id"],
            "route_item_id": theme["route_item_id"],
            "bottleneck_status": theme["bottleneck_status"],
            "feasibility": theme["feasibility"],
            "scarcity": theme["scarcity"],
            "substitutability": theme["substitutability"],
            "demand_evidence": "; ".join(f"{row['claim_id']}:{row['summary']}" for row in demand),
            "supply_evidence": "; ".join(f"{row['claim_id']}:{row['summary']}" for row in supply),
            "company_progress": "; ".join(f"{row['claim_id']}[{row['speaker_role']}]:{row['summary']}" for row in progress),
            "canonical_point_ids": ";".join(sorted({row["point_id"] for row in links if row["point_id"]})),
            "missing_evidence": "; ".join(value for value in missing if value),
            "source_ids": ";".join(source_ids),
            "as_of": max((sources[source_id]["accessed_date"] for source_id in source_ids if sources[source_id]["accessed_date"]), default=""),
        })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PANORAMA_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
