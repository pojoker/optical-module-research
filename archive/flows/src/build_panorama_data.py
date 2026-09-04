#!/usr/bin/env python3
"""Build the machine-readable data layer for the optical-module panorama.

The build is deterministic: the script never reads the clock.  Callers must
provide ``--generated-at`` explicitly, so identical inputs and arguments
produce byte-identical JSON.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PANORAMA = ROOT / "output" / "光模块供应链全景-v1.1.md"
DEFAULT_NODES = ROOT / "output" / "nodes.csv"
DEFAULT_EDGES = ROOT / "output" / "edges.csv"
DEFAULT_OUTPUT = ROOT / "output" / "panorama-data.json"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
NODE_PREFIX_RE = re.compile(r"^(N\d+)\s+")
MARKET_ANNOTATION_RE = re.compile(r"\[([^\[\]]+)\]")
URL_RE = re.compile(r"https?://[^\s)>]+")

IDENTITY_HEADERS = ("身份依据一句", "身份依据引语", "身份判定引语")
ANCHOR_HEADERS = ("锚", "锚URL", "来源")
STATUS_HEADERS = ("关系台账有边?", "状态")

NODE_REQUIRED_HEADERS = ("node_id", "名称", "类型", "国别", "代码", "备注")
EDGE_REQUIRED_HEADERS = (
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
)

ADMISSION_TIER_DEFINITIONS = {
    "edge_backed": "关系台账状态明确为有边；仅表示存在台账边，不替代该边证据等级。",
    "node_wide_gate": "按节点层宽闸收入全景，状态明确含“节点层宽闸”。",
    "no_ledger_edge": "公司身份进入全景，但状态明确为无关系台账边或未入关系台账。",
    "lead_only": "仅为线索、待核或候选，尚未完成节点/关系准入。",
    "cross_reference": "该行只交叉引用另一叶的同一公司记录，不重复计算身份准入。",
    "context_only": "该行只证明工序/能力覆盖，不构成专产主体或关系边准入。",
    "unclassified": "原表状态不足以机械判定准入层级；原文保留并产生解析警告。",
}


def warning(
    warnings: list[dict[str, Any]],
    *,
    source: Path,
    line: int | None,
    code: str,
    message: str,
    raw: str = "",
) -> None:
    """Append a structured warning; callers must never silently drop a row."""
    item: dict[str, Any] = {
        "source": str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source),
        "code": code,
        "message": message,
    }
    if line is not None:
        item["line"] = line
    if raw:
        item["raw"] = raw
    warnings.append(item)


def split_markdown_row(line: str) -> list[str]:
    """Split a Markdown table row while honoring backslash-escaped pipes."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith(r"\|"):
        body = body[:-1]

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(SEPARATOR_CELL_RE.fullmatch(cell.strip()) for cell in cells)


def first_header(headers: list[str], aliases: tuple[str, ...]) -> str | None:
    return next((name for name in aliases if name in headers), None)


def extract_company_name(
    raw_name: str,
    *,
    source: Path,
    line_number: int,
    warnings: list[dict[str, Any]],
) -> tuple[str, str, str, str]:
    """Return clean name, market annotation, node id, and raw annotation."""
    value = raw_name.strip()
    raw_annotation = ""
    node_id = ""
    prefix_match = NODE_PREFIX_RE.match(value)
    if prefix_match:
        node_id = prefix_match.group(1)
        value = value[prefix_match.end() :].strip()

    market_code = ""
    market_matches = list(MARKET_ANNOTATION_RE.finditer(value))
    if market_matches:
        market_match = market_matches[-1]
        market_code = market_match.group(1).strip()
        before_market = value[: market_match.start()].strip()
        after_market = value[market_match.end() :].strip()
        raw_annotation = after_market
        # Chinese full-width parentheses here describe a parent/subsidiary
        # relationship; the text before that parenthesis is the entity name.
        value = before_market.split("（", 1)[0].strip()
    else:
        warning(
            warnings,
            source=source,
            line=line_number,
            code="company_market_annotation_missing",
            message="公司名称单元格未找到末尾的 [市场:代码] 或 [未上市/未识别] 标注；公司仍保留。",
            raw=raw_name,
        )

    if not value:
        warning(
            warnings,
            source=source,
            line=line_number,
            code="company_name_empty_after_parse",
            message="去除节点编号和市场标注后公司名称为空。",
            raw=raw_name,
        )
    return value, market_code, node_id, raw_annotation


def admission_tier(status: str, anchor: str) -> str:
    text = f"{status} {anchor}"
    if "节点层宽闸" in text:
        return "node_wide_gate"
    if status.strip().startswith("交叉引用"):
        return "cross_reference"
    if any(token in status for token in ("工序覆盖", "非专产")):
        return "context_only"
    if re.search(r"(^|[，,；;])\s*有(?:（|\(|$)", status.strip()):
        return "edge_backed"
    if any(token in text for token in ("未入关系台账", "无（", "无(", "无关系台账")):
        return "no_ledger_edge"
    if any(token in text for token in ("线索", "待核", "候选", "待判定")):
        return "lead_only"
    return "unclassified"


def heading_path(stack: dict[int, str], current_level: int) -> list[dict[str, Any]]:
    return [
        {"level": level, "title": stack[level]}
        for level in sorted(stack)
        if 2 <= level <= current_level
    ]


def parse_panorama(
    path: Path, warnings: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    stack: dict[int, str] = {}
    branches: list[dict[str, Any]] = []
    branch_by_title: dict[str, dict[str, Any]] = {}
    leaves: list[dict[str, Any]] = []
    companies: list[dict[str, Any]] = []

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            for stale_level in [value for value in stack if value >= level]:
                del stack[stale_level]
            stack[level] = title
            line_index += 1
            continue

        if not line.lstrip().startswith("|") or line_index + 1 >= len(lines):
            line_index += 1
            continue

        headers = split_markdown_row(line)
        separator = split_markdown_row(lines[line_index + 1])
        if not (headers and headers[0] == "名称" and is_separator_row(separator)):
            line_index += 1
            continue

        table_start_line = line_index + 1
        identity_header = first_header(headers, IDENTITY_HEADERS)
        anchor_header = first_header(headers, ANCHOR_HEADERS)
        status_header = first_header(headers, STATUS_HEADERS)
        missing_semantic_headers = [
            label
            for label, header in (
                ("身份依据", identity_header),
                ("锚", anchor_header),
                ("状态", status_header),
            )
            if header is None
        ]
        if missing_semantic_headers:
            warning(
                warnings,
                source=path,
                line=table_start_line,
                code="company_table_headers_unrecognized",
                message="公司表缺少可识别的语义列：" + "、".join(missing_semantic_headers),
                raw=line,
            )

        active_levels = [level for level in stack if level >= 2]
        if not active_levels:
            warning(
                warnings,
                source=path,
                line=table_start_line,
                code="company_table_without_section",
                message="公司表之前没有二级或更深标题；该表使用未分类分支。",
                raw=line,
            )
            branch_title = "未分类"
            leaf_title = "未分类"
            leaf_level = 0
            path_items: list[dict[str, Any]] = []
        else:
            branch_title = stack.get(2, "未分类")
            leaf_level = max(active_levels)
            leaf_title = stack[leaf_level]
            path_items = heading_path(stack, leaf_level)

        if branch_title not in branch_by_title:
            branch = {
                "id": f"branch-{len(branches) + 1:02d}",
                "title": branch_title,
                "leaves": [],
            }
            branches.append(branch)
            branch_by_title[branch_title] = branch
        branch = branch_by_title[branch_title]
        leaf = {
            "id": f"leaf-{len(leaves) + 1:03d}",
            "title": leaf_title,
            "heading_level": leaf_level,
            "section_path": path_items,
            "source_line": table_start_line,
            "company_indices": [],
        }
        leaves.append(leaf)
        branch["leaves"].append(leaf)

        line_index += 2
        parsed_rows = 0
        while line_index < len(lines) and lines[line_index].lstrip().startswith("|"):
            raw_row = lines[line_index]
            row_line_number = line_index + 1
            cells = split_markdown_row(raw_row)
            if is_separator_row(cells):
                warning(
                    warnings,
                    source=path,
                    line=row_line_number,
                    code="unexpected_table_separator",
                    message="公司表数据区出现额外分隔行；该行未作为公司解析。",
                    raw=raw_row,
                )
                line_index += 1
                continue
            if len(cells) != len(headers):
                warning(
                    warnings,
                    source=path,
                    line=row_line_number,
                    code="company_row_column_count_mismatch",
                    message=f"公司行有 {len(cells)} 列，表头有 {len(headers)} 列；该行未进入 companies。",
                    raw=raw_row,
                )
                line_index += 1
                continue

            row = dict(zip(headers, cells))
            raw_name = row.get("名称", "").strip()
            if not raw_name:
                warning(
                    warnings,
                    source=path,
                    line=row_line_number,
                    code="company_row_name_empty",
                    message="公司行名称为空；该行未进入 companies。",
                    raw=raw_row,
                )
                line_index += 1
                continue

            name, market_code, node_id, raw_name_annotation = extract_company_name(
                raw_name,
                source=path,
                line_number=row_line_number,
                warnings=warnings,
            )
            identity_quote = row.get(identity_header, "").strip() if identity_header else ""
            anchor = row.get(anchor_header, "").strip() if anchor_header else ""
            status = row.get(status_header, "").strip() if status_header else ""
            tier = admission_tier(status, anchor)
            if tier == "unclassified":
                warning(
                    warnings,
                    source=path,
                    line=row_line_number,
                    code="admission_tier_unclassified",
                    message="无法从状态/锚机械判定 admission_tier；公司仍保留。",
                    raw=raw_row,
                )

            company = {
                "name": name,
                "market_code": market_code,
                "leaf": leaf["id"],
                "identity_quote": identity_quote,
                "anchor": anchor,
                "status": status,
                "admission_tier": tier,
                "node_id": node_id,
                "name_cell_raw": raw_name,
                "raw_name_annotation": raw_name_annotation,
                "anchor_urls": URL_RE.findall(anchor),
                "source_line": row_line_number,
            }
            company_index = len(companies)
            companies.append(company)
            leaf["company_indices"].append(company_index)
            parsed_rows += 1
            line_index += 1

        leaf["company_count"] = parsed_rows
        if parsed_rows == 0:
            warning(
                warnings,
                source=path,
                line=table_start_line,
                code="company_table_empty_after_parse",
                message="识别到公司表，但没有任何一行成功进入 companies。",
                raw=" | ".join(headers),
            )

    return {"branches": branches}, companies


def load_csv_rows(
    path: Path,
    required_headers: tuple[str, ...],
    warnings: list[dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ValueError(f"{path} 为空文件") from exc

        missing = [header for header in required_headers if header not in headers]
        if missing:
            raise ValueError(f"{path} 缺少必需字段: {', '.join(missing)}")

        for line_number, values in enumerate(reader, start=2):
            raw = ",".join(values)
            if len(values) != len(headers):
                warning(
                    warnings,
                    source=path,
                    line=line_number,
                    code="csv_row_column_count_mismatch",
                    message=f"CSV 行有 {len(values)} 列，表头有 {len(headers)} 列；该行未进入输出。",
                    raw=raw,
                )
                continue
            row = dict(zip(headers, values))
            primary_key = row[required_headers[0]].strip()
            if not primary_key:
                warning(
                    warnings,
                    source=path,
                    line=line_number,
                    code="csv_primary_key_empty",
                    message=f"CSV 行的 {required_headers[0]} 为空；该行未进入输出。",
                    raw=raw,
                )
                continue
            rows.append({key: value.strip() for key, value in row.items()})
    return rows


def build_network(
    nodes: list[dict[str, str]],
    edges: list[dict[str, str]],
    warnings: list[dict[str, Any]],
    nodes_path: Path,
    edges_path: Path,
) -> dict[str, Any]:
    node_names: dict[str, str] = {}
    duplicate_node_ids: set[str] = set()
    for row_number, node in enumerate(nodes, start=2):
        node_id = node["node_id"]
        if node_id in node_names:
            duplicate_node_ids.add(node_id)
            warning(
                warnings,
                source=nodes_path,
                line=row_number,
                code="duplicate_node_id",
                message=f"node_id {node_id} 重复；所有原行仍保留。",
                raw=json.dumps(node, ensure_ascii=False),
            )
        else:
            node_names[node_id] = node["名称"]

    seen_edge_ids: set[str] = set()
    relationship_index: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"as_supplier": [], "as_customer": []}
    )
    for row_number, edge in enumerate(edges, start=2):
        edge_id = edge["edge_id"]
        if edge_id in seen_edge_ids:
            warning(
                warnings,
                source=edges_path,
                line=row_number,
                code="duplicate_edge_id",
                message=f"edge_id {edge_id} 重复；所有原行仍保留并进入索引。",
                raw=json.dumps(edge, ensure_ascii=False),
            )
        seen_edge_ids.add(edge_id)
        relationship_index[edge["供方"]]["as_supplier"].append(edge_id)
        relationship_index[edge["需方"]]["as_customer"].append(edge_id)

    ordered_index = {
        name: relationship_index[name] for name in sorted(relationship_index)
    }
    return {
        "nodes": nodes,
        "edges": edges,
        "relationship_index": ordered_index,
        "edge_counts_by_tier": dict(sorted(Counter(edge["边等级"] for edge in edges).items())),
        "duplicate_node_ids": sorted(duplicate_node_ids),
    }


def validate_generated_at(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise argparse.ArgumentTypeError("--generated-at 不可为空")
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--generated-at 必须是 ISO 8601 时间，例如 2026-07-24T12:34:56+08:00"
        ) from exc
    return candidate


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build_payload(
    panorama_path: Path,
    nodes_path: Path,
    edges_path: Path,
    generated_at: str,
) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    tree, companies = parse_panorama(panorama_path, warnings)
    nodes = load_csv_rows(nodes_path, NODE_REQUIRED_HEADERS, warnings)
    edges = load_csv_rows(edges_path, EDGE_REQUIRED_HEADERS, warnings)
    network = build_network(nodes, edges, warnings, nodes_path, edges_path)

    leaf_count = sum(len(branch["leaves"]) for branch in tree["branches"])
    tier_counts = dict(sorted(Counter(c["admission_tier"] for c in companies).items()))
    payload = {
        "schema_version": "1.0",
        "tree": tree,
        "companies": companies,
        "network": network,
        "parse_warnings": warnings,
        "meta": {
            "generated_at": generated_at,
            "counts": {
                "branches": len(tree["branches"]),
                "leaves": leaf_count,
                "company_rows": len(companies),
                "unique_company_names": len({company["name"] for company in companies}),
                "nodes": len(nodes),
                "edges": len(edges),
                "relationship_index_companies": len(network["relationship_index"]),
                "parse_warnings": len(warnings),
                "companies_by_admission_tier": tier_counts,
            },
            "sources": {
                "panorama": {
                    "path": str(panorama_path.relative_to(ROOT)),
                    "sha256": file_sha256(panorama_path),
                },
                "nodes": {
                    "path": str(nodes_path.relative_to(ROOT)),
                    "sha256": file_sha256(nodes_path),
                },
                "edges": {
                    "path": str(edges_path.relative_to(ROOT)),
                    "sha256": file_sha256(edges_path),
                },
            },
            "admission_tier_definitions": ADMISSION_TIER_DEFINITIONS,
        },
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        required=True,
        type=validate_generated_at,
        help="由调用方传入的 ISO 8601 生成时间；脚本本身不读取时钟。",
    )
    parser.add_argument("--panorama", type=Path, default=DEFAULT_PANORAMA)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        args.panorama.resolve(),
        args.nodes.resolve(),
        args.edges.resolve(),
        args.generated_at,
    )
    write_json_atomic(args.output.resolve(), payload)
    counts = payload["meta"]["counts"]
    print(
        f"叶数={counts['leaves']} 公司数={counts['company_rows']} "
        f"警告数={counts['parse_warnings']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
