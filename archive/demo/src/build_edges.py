#!/usr/bin/env python3
"""Build Stage3 supply-chain edges and nodes from Stage2 JSON.

Self-test (run from the repository root):
    python3 demo/src/build_edges.py \
      --extracted demo/out/extracted.sample.json \
      --out-edges /tmp/demo_test_edges.csv \
      --out-nodes /tmp/demo_test_nodes.csv
    python3 - <<'PY'
    import csv
    with open('/tmp/demo_test_edges.csv', encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert all(len(row) == 10 for row in rows)
    assert '解匿线索:PINEWAVE' in next(
        row['备注'] for row in rows
        if row['需方'] == '客户第5名(匿名)' and row['占比或金额'].startswith('8.10%')
    )
    assert next(row['边等级'] for row in rows if row['需方'] == 'Fabrinet') == '实边'
    print('PASS: PINEWAVE clue; Fabrinet real edge; every data row has 10 columns')
    PY

Result: PASS: PINEWAVE clue; Fabrinet real edge; every data row has 10 columns
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


EDGE_FIELDS = [
    "edge_id",
    "供方",
    "需方",
    "占比或金额",
    "财年",
    "边等级",
    "证据文件",
    "锚点",
    "验证状态",
    "备注",
]
NODE_FIELDS = ["node_id", "名称", "类型", "国别", "代码", "备注"]
VERIFICATION_STATUS = "demo管线自动生成-未人工复核"
COMPANIES = {
    "300308": ("中际旭创", "光模块厂"),
    "300502": ("新易盛", "光模块厂"),
    "300394": ("天孚通信", "光器件厂"),
    "002281": ("光迅科技", "光模块厂"),
    "300757": ("罗博特科", "耦合封装设备商"),
    "688516": ("奥特维", "组件封装设备商"),
    "301338": ("凯格精机", "组装设备商"),
    "688097": ("博众精工", "自动化设备商"),
    "603203": ("快克智能", "焊接设备商"),
    "688337": ("普源精电", "测试测量仪器"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Stage3 edges.csv and nodes.csv from extracted.json."
    )
    parser.add_argument("--extracted", required=True, type=Path)
    parser.add_argument("--out-edges", required=True, type=Path)
    parser.add_argument("--out-nodes", required=True, type=Path)
    return parser.parse_args()


def as_decimal(value: Any) -> Decimal | None:
    """Convert JSON scalars to Decimal without ever passing through float."""
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip().replace(",", "").removesuffix("%")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def decimal_text(value: Any, suffix: str) -> str:
    number = as_decimal(value)
    return f"{number}{suffix}" if number is not None else f"未知{suffix}"


def amount_display(row: dict[str, Any]) -> str:
    return (
        f"{decimal_text(row.get('pct'), '%')}"
        f"({decimal_text(row.get('amount_yuan'), '元')})"
    )


def is_related_party_candidate(related_pct: Any, customer_pct: Any) -> bool:
    related = as_decimal(related_pct)
    customer = as_decimal(customer_pct)
    return (
        related is not None
        and customer is not None
        and abs(related - customer) < Decimal("0.005")
    )


def first_value(record: dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        value = record.get(name)
        if value is not None:
            return value
    return None


def related_party_clues(
    sales: Any, customer_amount: Any
) -> list[str]:
    """Return names whose USD-10k fingerprint can match at CNY/USD 6.5--7.5."""
    target = as_decimal(customer_amount)
    if target is None or target <= 0 or not isinstance(sales, list):
        return []

    lower_target = target * Decimal("0.97")
    upper_target = target * Decimal("1.03")
    matches: list[str] = []
    for sale in sales:
        if not isinstance(sale, dict):
            continue
        unit = first_value(sale, ("unit", "currency", "币种", "单位"))
        if unit is None or "万美元" not in str(unit).replace(" ", ""):
            continue
        amount = as_decimal(first_value(sale, ("amount", "金额")))
        name = first_value(sale, ("name", "关联方名", "名称"))
        if amount is None or amount <= 0 or not str(name or "").strip():
            continue

        usd_yuan_base = amount * Decimal("10000")
        band_low = usd_yuan_base * Decimal("6.5")
        band_high = usd_yuan_base * Decimal("7.5")
        # Both intervals are continuous.  A non-empty intersection means some
        # exchange rate in the permitted band produces a difference below 3%.
        if band_low < upper_target and band_high > lower_target:
            clean_name = str(name).strip()
            if clean_name not in matches:
                matches.append(clean_name)
    return matches


def normalized_code(value: Any) -> str:
    text = str(value or "").strip()
    return text.zfill(6) if text.isdigit() and len(text) < 6 else text


def add_node(
    nodes: list[dict[str, str]],
    node_names: set[str],
    name: str,
    node_type: str,
    country: str = "",
    code: str = "",
    note: str = "",
) -> None:
    if not name or name in node_names:
        return
    node_names.add(name)
    nodes.append(
        {
            "node_id": f"DN{len(nodes) + 1:02d}",
            "名称": name,
            "类型": node_type,
            "国别": country,
            "代码": code,
            "备注": note,
        }
    )


def build(data: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    reports = data.get("reports")
    if not isinstance(reports, list):
        raise ValueError("extracted JSON must contain a 'reports' list")

    edges: list[dict[str, str]] = []
    nodes: list[dict[str, str]] = []
    node_names: set[str] = set()

    for report_index, report in enumerate(reports, start=1):
        if not isinstance(report, dict):
            raise ValueError(f"reports[{report_index - 1}] must be an object")
        code = normalized_code(report.get("stock_code"))
        mapped_name, mapped_type = COMPANIES.get(
            code, (str(report.get("company") or "").strip(), "待分类")
        )
        company = str(report.get("company") or mapped_name).strip()
        if not company:
            raise ValueError(f"reports[{report_index - 1}] has no company name")
        # The built-in mapping is authoritative for known stock codes.
        if code in COMPANIES:
            company, mapped_type = COMPANIES[code]
        add_node(nodes, node_names, company, mapped_type, "中国", code)

        fiscal_year = str(report.get("fiscal_year") or "")
        source_pdf = str(report.get("source_pdf") or "")
        pdf_url = str(report.get("pdf_url") or "")
        procedural = report.get("procedural")
        if not isinstance(procedural, dict):
            procedural = {}
        sales = procedural.get("related_party_sales", [])

        for relation_key, anonymous_label in (
            ("customers", "客户"),
            ("suppliers", "供应商"),
        ):
            relation = report.get(relation_key)
            if not isinstance(relation, dict):
                continue
            rows = relation.get("rows")
            if not isinstance(rows, list):
                continue
            related_pct = relation.get("related_party_pct")

            for position, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    continue
                rank = row.get("rank")
                rank_text = str(rank if rank is not None else position)
                raw_name = str(row.get("name_raw") or "").strip()
                anonymous = row.get("is_anonymous") is True
                notes: list[str] = []

                if anonymous:
                    slot = f"{anonymous_label}第{rank_text}名(匿名)"
                    supplier = slot if relation_key == "suppliers" else company
                    customer = company if relation_key == "suppliers" else slot
                    edge_level = "半边槽位"
                    if raw_name:
                        notes.append(f"原始名称:{raw_name}")
                else:
                    counterparty = raw_name or f"{anonymous_label}第{rank_text}名"
                    supplier = counterparty if relation_key == "suppliers" else company
                    customer = company if relation_key == "suppliers" else counterparty
                    edge_level = "实边"
                    add_node(nodes, node_names, counterparty, "待分类")

                if relation_key == "customers" and is_related_party_candidate(
                    related_pct, row.get("pct")
                ):
                    notes.append("关联方锁定候选")
                    for clue in related_party_clues(sales, row.get("amount_yuan")):
                        notes.append(f"解匿线索:{clue}")

                if row.get("related_flag") == "是":
                    notes.append("年报关联关系列=是")

                edges.append(
                    {
                        "edge_id": f"D{len(edges) + 1:03d}",
                        "供方": supplier,
                        "需方": customer,
                        "占比或金额": amount_display(row),
                        "财年": fiscal_year,
                        "边等级": edge_level,
                        "证据文件": source_pdf,
                        "锚点": pdf_url,
                        "验证状态": VERIFICATION_STATUS,
                        "备注": ";".join(notes),
                    }
                )
    return edges, nodes


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    try:
        with args.extracted.open(encoding="utf-8") as handle:
            data = json.load(handle, parse_float=Decimal)
        if not isinstance(data, dict):
            raise ValueError("extracted JSON root must be an object")
        edges, nodes = build(data)
        write_csv(args.out_edges, EDGE_FIELDS, edges)
        write_csv(args.out_nodes, NODE_FIELDS, nodes)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"build_edges.py: error: {exc}", file=sys.stderr)
        return 1

    print(f"edges: {args.out_edges} ({len(edges)} rows)")
    print(f"nodes: {args.out_nodes} ({len(nodes)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
