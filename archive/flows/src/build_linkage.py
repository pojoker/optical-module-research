#!/usr/bin/env python3
"""Build the v1.2 company-product-HS linkage table from read-only inputs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "flows/out/catalog.csv"
FLOWS_PATH = ROOT / "flows/out/flows-seed.json"
EDGES_PATH = ROOT / "output/edges.csv"
CUSTOMS_PATH = ROOT / "flows/out/customs-partners.csv"
OUTPUT_PATH = ROOT / "flows/out/linkage.csv"

FIELDS = [
    "link_id",
    "公司",
    "公司代码",
    "产品线",
    "速率档",
    "HS编码",
    "出口相关性(直接/间接/无)",
    "去向佐证(伙伴国)",
    "证据锚点",
    "备注",
]

COMPANIES = {
    "中际旭创": ("中际旭创", "300308.SZ"),
    "新易盛": ("新易盛", "300502.SZ"),
    "光迅科技": ("光迅科技", "002281.SZ"),
    "天孚通信": ("天孚通信", "300394.SZ"),
}

HS_CODE = "85177950"
HS_NAME = "光通信设备的激光收发模块"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_company(raw_name: str) -> tuple[str, str] | None:
    for marker, company in COMPANIES.items():
        if marker in raw_name:
            return company
    return None


def composite_anchor(*parts: str) -> str:
    return " | ".join(part.strip() for part in parts if part and part.strip())


def build_rows() -> list[dict[str, str]]:
    catalog = read_csv(CATALOG_PATH)
    edges = read_csv(EDGES_PATH)
    customs = read_csv(CUSTOMS_PATH)
    with FLOWS_PATH.open("r", encoding="utf-8") as handle:
        flow_data = json.load(handle)

    if not catalog or not edges or not customs or not flow_data.get("flows"):
        raise ValueError("one or more required inputs are empty")

    rows: list[dict[str, str]] = []

    # Direct links require both an actual catalogued transceiver-module model and
    # the HS commodity-name anchor. AOC products are not forced into this HS code.
    for item in catalog:
        company_info = canonical_company(item.get("公司", ""))
        if company_info is None or company_info[0] not in {
            "中际旭创",
            "新易盛",
            "光迅科技",
        }:
            continue
        model = item.get("产品型号", "").strip()
        source_url = item.get("来源URL", "").strip()
        if not model or model.startswith("(") or "AOC" in model.upper():
            continue
        if not source_url.startswith(("http://", "https://")):
            continue
        company, code = company_info
        rows.append(
            {
                "公司": company,
                "公司代码": code,
                "产品线": model,
                "速率档": item.get("速率", "").strip(),
                "HS编码": HS_CODE,
                "出口相关性(直接/间接/无)": "直接",
                "去向佐证(伙伴国)": "",
                "证据锚点": composite_anchor(
                    f'海关商品名“{HS_NAME}”（HS {HS_CODE}；'
                    "数据：flows/out/customs-partners.csv）",
                    f"产品目录页：{source_url}",
                ),
                "备注": (
                    f"目录记录{item.get('cat_id', '').strip()}与HS商品名的产品级连接；"
                    "海关数据不分公司，不代表该公司出口事实、出口份额或具体去向。"
                ),
            }
        )

    # Tianfu is a component supplier rather than a complete transceiver-module
    # line. Its Thailand destination is only qualitative corroboration: the
    # named Tianfu→Fabrinet edge and Thailand customs flow coexist.
    tianfu_catalog = [
        item for item in catalog if "天孚通信" in item.get("公司", "")
    ]
    edge_e043 = next(
        (
            edge
            for edge in edges
            if edge.get("edge_id") == "E043"
            and edge.get("供方") == "天孚通信"
            and edge.get("需方") == "Fabrinet"
        ),
        None,
    )
    thailand_rows = [
        item for item in customs if item.get("贸易伙伴", "").strip() == "泰国"
    ]
    if tianfu_catalog and edge_e043 and thailand_rows:
        latest_thailand = max(thailand_rows, key=lambda item: item.get("月份", ""))
        catalog_anchor = tianfu_catalog[0].get("来源URL", "").strip()
        rows.append(
            {
                "公司": "天孚通信",
                "公司代码": "300394.SZ",
                "产品线": "光通信器件（非整模块；具体型号未抓取）",
                "速率档": "",
                "HS编码": HS_CODE,
                "出口相关性(直接/间接/无)": "间接",
                "去向佐证(伙伴国)": "泰国（佐证）",
                "证据锚点": composite_anchor(
                    f"目录记录{tianfu_catalog[0].get('cat_id', '').strip()}："
                    f"{catalog_anchor}",
                    f"E043：{edge_e043.get('锚点', '').strip()}",
                    "flows/out/customs-partners.csv"
                    f"#月份={latest_thailand.get('月份', '').strip()}"
                    "&贸易伙伴=泰国",
                ),
                "备注": (
                    "佐证逻辑：天孚→Fabrinet实名边E043与泰国流向共存；"
                    "仅作定性佐证，不表示货物必经Fabrinet，也不作任何公司级"
                    "出口额、出口量或份额分配。天孚为器件供应商，非整模块。"
                ),
            }
        )

    # flows-seed contains evidence-backed product lines for Lieqi. De-duplicate
    # annual observations and retain only actual equipment lines, not accessories.
    equipment_seen: set[str] = set()
    for flow in flow_data["flows"]:
        product_line = flow.get("构成项", "").strip()
        if (
            flow.get("产品") != "主营业务收入"
            or flow.get("构成类型") != "设备"
            or product_line == "配件及其他"
            or product_line in equipment_seen
        ):
            continue
        anchor = flow.get("锚点", "").strip()
        if not anchor:
            continue
        equipment_seen.add(product_line)
        rows.append(
            {
                "公司": "猎奇智能",
                "公司代码": "未上市",
                "产品线": product_line,
                "速率档": "",
                "HS编码": "",
                "出口相关性(直接/间接/无)": "无",
                "去向佐证(伙伴国)": "",
                "证据锚点": composite_anchor(
                    f"flows-seed {flow.get('flow_id', '').strip()}",
                    anchor,
                ),
                "备注": (
                    "设备产品线，不属于HS 85177950所指激光收发模块；"
                    "未建立公司出口或伙伴国去向连接。"
                ),
            }
        )

    for number, row in enumerate(rows, start=1):
        row["link_id"] = f"LNK{number:03d}"
        if not row["证据锚点"]:
            raise ValueError(f"{row['link_id']} has an empty evidence anchor")
        if row["出口相关性(直接/间接/无)"] not in {"直接", "间接", "无"}:
            raise ValueError(f"{row['link_id']} has an invalid export relevance")

    return rows


def main() -> None:
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["出口相关性(直接/间接/无)"] for row in rows)
    print(f"wrote {len(rows)} rows to {OUTPUT_PATH}")
    print(
        "出口相关性计数："
        + "，".join(f"{level}={counts[level]}" for level in ("直接", "间接", "无"))
    )


if __name__ == "__main__":
    main()
