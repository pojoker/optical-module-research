#!/usr/bin/env python3
"""Build a company-level optical-module supply-chain participation register."""

from __future__ import annotations

import csv
import html
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OUTPUTS = ("参与识别.csv", "参与识别.md", "参与识别.html")

# Public-company rows whose evidence is recorded under a subsidiary or combined label.
COMPANY_ALIASES = {
    "武汉钧恒科技有限公司": "汇绿生态",
    "罗博特科/ficonTEC": "罗博特科",
    "炬光": "炬光科技",
}

STATUS_ORDER = {
    "已确认参与": 0,
    "待确认": 1,
    "尚未发现已过闸证据": 2,
    "未覆盖": 3,
}


def read_rows(relative_path: str) -> list[dict[str, str]]:
    path = ROOT / relative_path
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def unique_universe() -> list[dict[str, str]]:
    """Deduplicate supplement rows by code while preserving first-seen order."""
    merged: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for row in read_rows("corpus/_frozen.csv"):
        code = row["代码"].strip()
        if code not in merged:
            order.append(code)
            merged[code] = dict(row)
        else:
            # Later supplement rows carry the more specific classification/source.
            merged[code].update({k: v for k, v in row.items() if v})
    return [merged[code] for code in order]


def resolve_company(name: str, universe_names: set[str]) -> str | None:
    name = name.strip()
    if name in universe_names:
        return name
    alias = COMPANY_ALIASES.get(name)
    if alias in universe_names:
        return alias
    matches = [candidate for candidate in universe_names if len(candidate) >= 3 and candidate in name]
    if len(matches) == 1:
        return matches[0]
    return None


def is_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}

def extract_url(value: str) -> str:
    match = re.search(r"https?://[^\s\]]+", value)
    return match.group(0).rstrip(").,，。；;") if match else ""


def build_register() -> tuple[list[dict[str, str]], dict[str, int]]:
    universe = unique_universe()
    points = read_rows("points.csv")
    triage = read_rows("triage.csv")
    universe_names = {row["名称"] for row in universe}

    point_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for point in points:
        company = resolve_company(point["公司"], universe_names)
        if company:
            point_map[company].append(point)

    pending_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in triage:
        if item.get("处置") != "待判":
            continue
        company = resolve_company(item["公司"], universe_names)
        if company:
            pending_map[company].append(item)

    register: list[dict[str, str]] = []
    for company in universe:
        name = company["名称"]
        company_points = point_map.get(name, [])
        production = [p for p in company_points if p["状态"] == "生产中"]
        provisional = [p for p in company_points if p["状态"] != "生产中"]
        pending = pending_map.get(name, [])
        covered = (ROOT / "corpus" / "annual" / company["代码"]).is_dir()

        if production:
            conclusion = "已确认参与"
            evidence = production
        elif provisional or pending:
            conclusion = "待确认"
            evidence = provisional
        elif covered:
            conclusion = "尚未发现已过闸证据"
            evidence = []
        else:
            conclusion = "未覆盖"
            evidence = []

        cells = sorted({p["cell_id"] for p in evidence})
        quotes = [p["命中引语"].strip() for p in evidence if p.get("命中引语")]
        anchors = [p["锚点URL"].strip() for p in evidence if p.get("锚点URL")]
        dates = [p["检索日期"] for p in company_points if p.get("检索日期")]
        pending_summary = pending[0].get("引语或线索摘要", "") if pending else ""

        register.append(
            {
                "代码": company["代码"],
                "公司": name,
                "市场": company["市场"],
                "行业分类": company["行业分类"],
                "年报覆盖": "已覆盖" if covered else "未覆盖",
                "结论": conclusion,
                "参与环节": "、".join(cells),
                "证据状态": (
                    f"{len(production)}条生产中证据"
                    if production
                    else f"{len(provisional)}条非量产证据/{len(pending)}条待判"
                    if provisional or pending
                    else "无已过闸证据"
                ),
                "关键原文": "；".join(dict.fromkeys(quotes)) or pending_summary,
                "锚点": next((extract_url(anchor) for anchor in anchors if extract_url(anchor)), anchors[0] if anchors else ""),
                "数据日期": max(dates) if dates else "",
            }
        )

    register.sort(key=lambda row: (STATUS_ORDER[row["结论"]], row["市场"], row["代码"]))
    stats = Counter(row["结论"] for row in register)
    stats["公司总数"] = len(register)
    stats["年报已覆盖"] = sum(row["年报覆盖"] == "已覆盖" for row in register)
    return register, dict(stats)


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    fields = list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| 代码 | 公司 | 结论 | 参与环节 | 证据状态 | 关键原文 |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        quote = row["关键原文"].replace("|", "｜").replace("\n", " ")[:100]
        lines.append(
            f"| {row['代码']} | {row['公司']} | {row['结论']} | "
            f"{row['参与环节'] or '—'} | {row['证据状态']} | {quote or '—'} |"
        )
    return lines


def write_markdown(rows: list[dict[str, str]], stats: dict[str, int], path: Path) -> None:
    visible = [row for row in rows if row["结论"] in {"已确认参与", "待确认"}]
    lines = [
        "# 光模块供应链参与识别",
        "",
        "> 结论口径：有“生产中”过闸证据才算已确认；“尚未发现”不等于确认不参与。",
        "",
        f"- 公司宇宙：{stats['公司总数']} 家",
        f"- 年报已覆盖：{stats['年报已覆盖']} 家",
        f"- 已确认参与：{stats.get('已确认参与', 0)} 家",
        f"- 待确认：{stats.get('待确认', 0)} 家",
        f"- 尚未发现已过闸证据：{stats.get('尚未发现已过闸证据', 0)} 家",
        f"- 未覆盖：{stats.get('未覆盖', 0)} 家",
        "",
        "## 已确认与待确认名单",
        "",
        *markdown_table(visible),
        "",
        "完整分母见 `参与识别.csv`；本页由 `participation.py` 生成，勿手改。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def badge(conclusion: str) -> str:
    classes = {
        "已确认参与": "yes",
        "待确认": "pending",
        "尚未发现已过闸证据": "none",
        "未覆盖": "missing",
    }
    return f'<span class="badge {classes[conclusion]}">{html.escape(conclusion)}</span>'


def write_html(rows: list[dict[str, str]], stats: dict[str, int], path: Path) -> None:
    table_rows = []
    for row in rows:
        anchor = row["锚点"]
        quote = row["关键原文"]
        quote_preview = quote[:180] + ("…" if len(quote) > 180 else "")
        anchor_html = (
            f'<a href="{html.escape(anchor, quote=True)}" target="_blank" rel="noreferrer">查看原文</a>'
            if is_url(anchor)
            else f'<span class="muted" title="{html.escape(anchor, quote=True)}">文本锚</span>'
            if anchor
            else "—"
        )
        table_rows.append(
            "<tr "
            f'data-status="{html.escape(row["结论"], quote=True)}">'
            f"<td class=\"code\">{html.escape(row['代码'])}</td>"
            f"<td><strong>{html.escape(row['公司'])}</strong><small>{html.escape(row['市场'])} · {html.escape(row['行业分类'])}</small></td>"
            f"<td>{badge(row['结论'])}</td>"
            f"<td>{html.escape(row['参与环节'] or '—')}</td>"
            f"<td>{html.escape(row['证据状态'])}</td>"
            f"<td class=\"quote\" title=\"{html.escape(quote, quote=True)}\">{html.escape(quote_preview or '—')}</td>"
            f"<td>{anchor_html}</td>"
            "</tr>"
        )

    document = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>光模块供应链参与识别</title>
<style>
:root{--ink:#12202f;--muted:#687583;--line:#dde4ea;--paper:#fff;--wash:#f4f7f9;--blue:#165dff;--green:#137a4b;--amber:#9a5b00}
*{box-sizing:border-box}body{margin:0;background:var(--wash);color:var(--ink);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif}
header{background:linear-gradient(125deg,#0d2238,#173e62);color:#fff;padding:44px max(24px,calc((100vw - 1280px)/2))}
h1{font-size:32px;margin:0 0 8px}header p{margin:0;color:#c8d9e8}.wrap{max-width:1280px;margin:0 auto;padding:24px}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:-44px}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:0 8px 28px #10203012}.card b{display:block;font-size:26px}.card span{color:var(--muted)}
.panel{background:var(--paper);border:1px solid var(--line);border-radius:12px;margin-top:20px;overflow:hidden}.toolbar{display:flex;gap:10px;flex-wrap:wrap;padding:16px;border-bottom:1px solid var(--line)}
input,select{height:38px;border:1px solid #cbd5df;border-radius:8px;background:#fff;padding:0 12px;color:var(--ink)}input{min-width:280px;flex:1}.note{padding:12px 16px;background:#fff8e6;color:#6f4b00}
.table-wrap{overflow:auto;max-height:70vh}table{width:100%;border-collapse:collapse;min-width:1150px}th{position:sticky;top:0;background:#f8fafb;text-align:left;z-index:1}th,td{padding:12px;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:hover{background:#f7faff}
small{display:block;color:var(--muted);margin-top:2px}.code{font-variant-numeric:tabular-nums}.quote{max-width:360px}.badge{display:inline-block;white-space:nowrap;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:600}.yes{background:#e7f6ee;color:var(--green)}.pending{background:#fff1d6;color:var(--amber)}.none,.missing{background:#edf1f4;color:#596673}.muted{color:var(--muted)}a{color:var(--blue);text-decoration:none}
footer{padding:18px 0;color:var(--muted)}@media(max-width:800px){.cards{grid-template-columns:repeat(2,1fr)}h1{font-size:26px}.wrap{padding:16px}input{min-width:100%}}
</style>
</head>
<body>
<header><h1>光模块供应链参与识别</h1><p>公司级判断 · 一手披露可追溯 · “尚未发现”不等于确认不参与</p></header>
<main class="wrap">
<section class="cards">
<div class="card"><b>__TOTAL__</b><span>公司宇宙</span></div>
<div class="card"><b>__COVERED__</b><span>年报已覆盖</span></div>
<div class="card"><b>__YES__</b><span>已确认参与</span></div>
<div class="card"><b>__PENDING__</b><span>待确认</span></div>
<div class="card"><b>__NO_EVIDENCE__</b><span>尚未发现已过闸证据</span></div>
</section>
<section class="panel">
<div class="note">判定规则：至少一条“生产中”过闸证据才进入已确认；研发、送样、在建或未决线索进入待确认。</div>
<div class="toolbar">
<input id="search" type="search" placeholder="搜索公司、代码、行业、环节或原文">
<select id="status" aria-label="筛选结论">
<option value="">全部结论</option><option>已确认参与</option><option>待确认</option><option>尚未发现已过闸证据</option><option>未覆盖</option>
</select>
<span id="count" class="muted"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>代码</th><th>公司</th><th>结论</th><th>参与环节</th><th>证据状态</th><th>关键原文</th><th>锚点</th></tr></thead>
<tbody>__ROWS__</tbody>
</table></div>
</section>
<footer>数据来自 corpus/_frozen.csv、points.csv 与 triage.csv；页面由 participation.py 确定性生成。</footer>
</main>
<script>
const search=document.querySelector('#search'),status=document.querySelector('#status'),count=document.querySelector('#count'),rows=[...document.querySelectorAll('tbody tr')];
function filter(){const q=search.value.trim().toLowerCase(),s=status.value;let n=0;for(const row of rows){const show=(!s||row.dataset.status===s)&&(!q||row.innerText.toLowerCase().includes(q));row.hidden=!show;if(show)n++}count.textContent=`显示 ${n} / ${rows.length} 家`}
search.addEventListener('input',filter);status.addEventListener('change',filter);filter();
</script>
</body></html>"""
    replacements = {
        "__TOTAL__": str(stats["公司总数"]),
        "__COVERED__": str(stats["年报已覆盖"]),
        "__YES__": str(stats.get("已确认参与", 0)),
        "__PENDING__": str(stats.get("待确认", 0)),
        "__NO_EVIDENCE__": str(stats.get("尚未发现已过闸证据", 0)),
        "__ROWS__": "\n".join(table_rows),
    }
    for key, value in replacements.items():
        document = document.replace(key, value)
    path.write_text(document, encoding="utf-8")


def build(outdir: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows, stats = build_register()
    write_csv(rows, outdir / OUTPUTS[0])
    write_markdown(rows, stats, outdir / OUTPUTS[1])
    write_html(rows, stats, outdir / OUTPUTS[2])
    return rows, stats


def validate(rows: list[dict[str, str]], stats: dict[str, int]) -> list[str]:
    errors: list[str] = []
    codes = [row["代码"] for row in rows]
    if len(codes) != len(set(codes)):
        errors.append("输出存在重复代码")
    if len(rows) != len(unique_universe()):
        errors.append("输出行数与唯一公司宇宙不一致")
    for row in rows:
        if row["结论"] == "已确认参与" and (not row["关键原文"] or "生产中" not in row["证据状态"]):
            errors.append(f"{row['代码']} {row['公司']} 已确认但缺生产中证据")
    if sum(stats.get(status, 0) for status in STATUS_ORDER) != stats["公司总数"]:
        errors.append("结论统计与公司总数不闭合")
    return errors


def verify() -> int:
    with tempfile.TemporaryDirectory() as temp:
        rows, stats = build(Path(temp))
        errors = validate(rows, stats)
        for filename in OUTPUTS:
            current = ROOT / "out" / filename
            candidate = Path(temp) / filename
            if not current.exists() or current.read_bytes() != candidate.read_bytes():
                errors.append(f"out/{filename} 与重生成结果不一致")
    if errors:
        print("\n".join(f"[失败] {error}" for error in errors))
        return 1
    print(
        "参与识别: 全绿 | "
        f"宇宙 {stats['公司总数']} | 覆盖 {stats['年报已覆盖']} | "
        f"确认 {stats.get('已确认参与', 0)} | 待确认 {stats.get('待确认', 0)}"
    )
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(verify())
    rows, stats = build(ROOT / "out")
    errors = validate(rows, stats)
    if errors:
        print("\n".join(f"[失败] {error}" for error in errors))
        raise SystemExit(1)
    print(
        "out/参与识别.* 已重建 | "
        f"宇宙 {stats['公司总数']} | 覆盖 {stats['年报已覆盖']} | "
        f"确认 {stats.get('已确认参与', 0)} | 待确认 {stats.get('待确认', 0)}"
    )
