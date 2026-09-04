#!/usr/bin/env python3
"""Fetch monthly China Customs export quantity/value data by HS code.

The public GACC statistics site currently puts a JavaScript challenge in
front of the query application.  This program deliberately does not solve or
bypass that challenge.  It records every attempted URL, parameters and
response summary in a channel-notes file, and writes only rows actually
returned by the official query result page.

Default HS codes:
  85177950  光通信设备的激光收发模块
  85176229  其他光通讯设备（broader than optical transceiver modules）

Examples:
  python flows/src/fetch_customs.py
  python flows/src/fetch_customs.py --hs-codes 85177950 --start 2024-01
  python flows/src/fetch_customs.py --end 2025-12 --delay 3
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

import pandas as pd
import requests


DEFAULT_BASE_URL = "http://stats.customs.gov.cn"
DEFAULT_HS_CODES = ("85177950", "85176229")
DEFAULT_OUTPUT = Path("flows/out/customs-monthly.csv")
DEFAULT_NOTES = Path("flows/out/customs-CHANNEL-NOTES.md")
MIN_DELAY_SECONDS = 2.0

CSV_FIELDS = (
    "月份",
    "HS编码",
    "商品名称",
    "出口量",
    "量单位",
    "出口额美元",
    "均价",
    "来源URL",
    "抓取日期",
)

KNOWN_NAMES = {
    "85177950": "光通信设备的激光收发模块",
    "85176229": "其他光通讯设备",
    "85177990": "税目8517所列设备用的其它零件",
}

TARIFF_SOURCES = (
    (
        "2024税则公告",
        "https://gss.mof.gov.cn/gzdt/zhengcefabu/202312/"
        "t20231229_3924577.htm",
    ),
    (
        "2024官方税率附件（列出85176229、85177950、85177990）",
        "https://gss.mof.gov.cn/gzdt/zhengcefabu/202404/"
        "P020240419426389451413.pdf",
    ),
    (
        "2026官方税率附件（用于检查编码延续）",
        "https://gss.mof.gov.cn/gzdt/zhengcefabu/202603/"
        "P020260326610286964491.pdf",
    ),
)

RETIRED_IP_NOTICE = (
    "http://www.customs.gov.cn/customs/302249/302266/302267/"
    "4835768/index.html"
)


class ChannelUnavailable(RuntimeError):
    """Raised when the official channel cannot be reached without bypassing it."""


class ParseFailure(RuntimeError):
    """Raised when a page is reachable but cannot be parsed without guessing."""


class InputParser(HTMLParser):
    """Collect named HTML input values without adding a BeautifulSoup dependency."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "input":
            return
        attributes = dict(attrs)
        name = attributes.get("name")
        if name:
            self.values[name] = attributes.get("value") or ""


@dataclass
class Probe:
    purpose: str
    url: str
    params: dict[str, Any] | None
    status: int | None
    content_type: str
    result: str


class RateLimitedClient:
    """A transparent requests client with a site-friendly minimum interval."""

    def __init__(self, delay: float, timeout: float) -> None:
        if delay < MIN_DELAY_SECONDS:
            raise ValueError(
                f"--delay must be at least {MIN_DELAY_SECONDS:g} seconds"
            )
        self.delay = delay
        self.timeout = timeout
        self.last_request_at: float | None = None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "workflow-rehearsal-customs/1.1 "
                    "(public-statistics research; requests)"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            }
        )
        self.probes: list[Probe] = []

    def get(
        self,
        url: str,
        *,
        purpose: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        if self.last_request_at is not None:
            remaining = self.delay - (time.monotonic() - self.last_request_at)
            if remaining > 0:
                time.sleep(remaining)

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                allow_redirects=True,
            )
            self.last_request_at = time.monotonic()
        except requests.RequestException as exc:
            self.last_request_at = time.monotonic()
            prepared = requests.Request("GET", url, params=params).prepare()
            self.probes.append(
                Probe(
                    purpose=purpose,
                    url=prepared.url or url,
                    params=params,
                    status=None,
                    content_type="",
                    result=f"{type(exc).__name__}: {exc}",
                )
            )
            raise ChannelUnavailable(f"{purpose}: {exc}") from exc

        result = summarize_response(response)
        self.probes.append(
            Probe(
                purpose=purpose,
                url=response.url,
                params=params,
                status=response.status_code,
                content_type=response.headers.get("Content-Type", ""),
                result=result,
            )
        )
        return response


def summarize_response(response: requests.Response) -> str:
    body = response.text
    if response.status_code == 412 and (
        "X-Via-JSL" in response.headers
        or "window['$_ts']" in body
        or "window[&#x27;$_ts&#x27;]" in body
    ):
        return (
            "WAF JavaScript challenge; "
            f"X-Via-JSL={response.headers.get('X-Via-JSL', '')!r}"
        )
    if "captcha" in body.lower() or "验证码" in body:
        return "captcha/验证码 page"
    compact = re.sub(r"\s+", " ", html.unescape(body)).strip()
    return compact[:300] if compact else "(empty body)"


def require_application_page(
    response: requests.Response, purpose: str
) -> requests.Response:
    summary = summarize_response(response)
    if response.status_code == 412 or summary.startswith("WAF JavaScript"):
        raise ChannelUnavailable(f"{purpose}: {summary}")
    if "captcha" in response.text.lower() or "验证码" in response.text:
        raise ChannelUnavailable(f"{purpose}: captcha/验证码 page")
    if not response.ok:
        raise ChannelUnavailable(
            f"{purpose}: HTTP {response.status_code}; {summary}"
        )
    return response


def parse_month(value: str) -> date:
    try:
        parsed = datetime.strptime(value, "%Y-%m").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid month {value!r}; expected YYYY-MM"
        ) from exc
    return parsed.replace(day=1)


def month_range(start: date, end: date) -> Iterable[date]:
    cursor = start
    while cursor <= end:
        yield cursor
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)


def yyyymm(value: date) -> int:
    return value.year * 100 + value.month


def parse_yyyymm(value: str, field: str) -> date:
    if not re.fullmatch(r"\d{6}", value):
        raise ParseFailure(f"{field} has unexpected value {value!r}")
    return date(int(value[:4]), int(value[4:]), 1)


def metadata_from_html(page: str) -> dict[str, str]:
    parser = InputParser()
    parser.feed(page)
    required = (
        "codeLength",
        "currentStartTime",
        "currentEndTime",
        "currentDateBySource",
    )
    missing = [name for name in required if not parser.values.get(name)]
    if missing:
        raise ParseFailure(
            "query form is missing metadata inputs: " + ", ".join(missing)
        )
    return {name: parser.values[name] for name in required}


def flatten_column(column: Any) -> str:
    if isinstance(column, tuple):
        parts: list[str] = []
        for part in column:
            text = str(part).strip()
            if not text or text.lower().startswith("unnamed:"):
                continue
            if not parts or parts[-1] != text:
                parts.append(text)
        return " ".join(parts)
    return str(column).strip()


def normalized_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", flatten_column(value).lower())


def find_column(
    columns: Iterable[Any],
    aliases: Iterable[str],
    *,
    forbidden: Iterable[str] = (),
) -> Any | None:
    normalized_aliases = tuple(normalized_header(alias) for alias in aliases)
    forbidden_tokens = tuple(normalized_header(item) for item in forbidden)
    candidates: list[tuple[Any, str]] = [
        (column, normalized_header(column)) for column in columns
    ]
    for column, header in candidates:
        if header in normalized_aliases:
            return column
    for column, header in candidates:
        if any(token and token in header for token in forbidden_tokens):
            continue
        if any(alias and alias in header for alias in normalized_aliases):
            return column
    return None


def tables_from_html(page: str) -> list[pd.DataFrame]:
    try:
        return pd.read_html(StringIO(page), attrs={"id": "table"})
    except (ValueError, ImportError) as exc:
        raise ParseFailure(f"cannot parse table#table: {exc}") from exc


def normalize_hs(value: Any) -> str:
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return re.sub(r"\D", "", text)


def validate_codes(page: str, requested: set[str]) -> dict[str, str]:
    tables = tables_from_html(page)
    if not tables:
        raise ParseFailure("HS selection page has no table#table")
    frame = tables[0]
    code_col = find_column(
        frame.columns, ("Commodity code", "商品编码", "HS code")
    )
    name_col = find_column(
        frame.columns, ("Commodity", "Commodity name", "商品名称")
    )
    if code_col is None:
        raise ParseFailure(
            "HS selection table has unknown headers: "
            + ", ".join(flatten_column(col) for col in frame.columns)
        )
    found: dict[str, str] = {}
    for _, row in frame.iterrows():
        code = normalize_hs(row[code_col])
        if code not in requested:
            continue
        name = ""
        if name_col is not None and not pd.isna(row[name_col]):
            name = str(row[name_col]).strip()
        found[code] = name or KNOWN_NAMES.get(code, "")
    return found


def select_table_state(target: date, metadata: dict[str, str]) -> str:
    current_start = int(metadata["currentStartTime"])
    current_end = int(metadata["currentEndTime"])
    selected = yyyymm(target)
    if selected >= current_start and current_end >= selected:
        return "1"
    if current_start > selected:
        return "2"
    return "3"


def result_params(
    target: date,
    hs_codes: Iterable[str],
    metadata: dict[str, str],
    *,
    page_num: int,
    page_size: int,
) -> dict[str, Any]:
    return {
        **metadata,
        "pageSize": str(page_size),
        "selectTableState": select_table_state(target, metadata),
        "currencyType": "usd",
        "year": str(target.year),
        "startMonth": str(target.month),
        "endMonth": str(target.month),
        "outerField1": "CODE_TS",
        "outerValue1": ",".join(hs_codes),
        "outerField2": "ORIGIN_COUNTRY",
        "outerValue2": "",
        "outerField3": "TRADE_MODE",
        "outerValue3": "",
        "outerField4": "TRADE_CO_PORT",
        "outerValue4": "",
        "monthFlag": "1",
        "pageNum": str(page_num),
        "orderType": "CODE ASC DEFAULT",
        "iEType": "0",
    }


def parse_decimal(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"", "-", "--", "—", "nan", "None"}:
        return None
    text = text.replace(",", "").replace(" ", "")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ParseFailure(f"non-numeric value {value!r}") from exc


def decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def unit_price(amount: Decimal | None, quantity: Decimal | None) -> str:
    if amount is None or quantity is None or quantity == 0:
        return ""
    with localcontext() as context:
        context.prec = 28
        price = amount / quantity
    return decimal_text(price.quantize(Decimal("0.000001")))


def total_size_from_html(page: str) -> int | None:
    parser = InputParser()
    parser.feed(page)
    raw = parser.values.get("totalSize")
    if raw is None or not raw.isdigit():
        return None
    return int(raw)


def rows_from_result(
    page: str,
    *,
    target: date,
    requested: set[str],
    source_url: str,
    fetched_on: str,
) -> list[dict[str, str]]:
    tables = tables_from_html(page)
    if not tables:
        raise ParseFailure("result page has no table#table")
    frame = tables[0]
    columns = frame.columns
    hs_col = find_column(columns, ("Commodity code", "HS code", "商品编码"))
    name_col = find_column(
        columns, ("Commodity", "Commodity name", "商品名称", "商品")
    )
    quantity_col = find_column(
        columns,
        ("Quantity", "First quantity", "第一数量", "数量"),
        forbidden=("unit", "单位", "year-on-year", "同比"),
    )
    unit_col = find_column(
        columns,
        ("Quantity unit", "First quantity unit", "第一数量单位", "数量单位"),
    )
    amount_col = find_column(
        columns,
        (
            "US dollars",
            "US dollar",
            "USD",
            "Value USD",
            "Trade value USD",
            "美元",
        ),
        forbidden=("year-on-year", "同比"),
    )

    missing = [
        name
        for name, column in (
            ("HS code", hs_col),
            ("quantity", quantity_col),
            ("quantity unit", unit_col),
            ("USD value", amount_col),
        )
        if column is None
    ]
    if missing:
        headers = ", ".join(flatten_column(col) for col in columns)
        raise ParseFailure(
            f"result table missing {', '.join(missing)}; headers={headers}"
        )

    output: list[dict[str, str]] = []
    for _, row in frame.iterrows():
        code = normalize_hs(row[hs_col])
        if code not in requested:
            continue
        quantity = parse_decimal(row[quantity_col])
        amount = parse_decimal(row[amount_col])
        name = KNOWN_NAMES.get(code, "")
        if name_col is not None and not pd.isna(row[name_col]):
            candidate = str(row[name_col]).strip()
            if candidate:
                name = candidate
        unit = "" if pd.isna(row[unit_col]) else str(row[unit_col]).strip()
        output.append(
            {
                "月份": target.strftime("%Y-%m"),
                "HS编码": code,
                "商品名称": name,
                "出口量": decimal_text(quantity),
                "量单位": unit,
                "出口额美元": decimal_text(amount),
                "均价": unit_price(amount, quantity),
                "来源URL": source_url,
                "抓取日期": fetched_on,
            }
        )
    return output


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> int:
    materialized = list(rows)
    materialized.sort(key=lambda row: (row["月份"], row["HS编码"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(materialized)
    return len(materialized)


def probe_fallbacks(
    client: RateLimitedClient,
    base_url: str,
    *,
    start: date,
    end: date,
    hs_codes: tuple[str, ...],
) -> None:
    for path, purpose in (
        ("/easyquery.htm", "easy query page (.htm)"),
        ("/easyquery.html", "easy query page (.html)"),
    ):
        try:
            client.get(urljoin(base_url + "/", path.lstrip("/")), purpose=purpose)
        except ChannelUnavailable:
            pass

    diagnostic_metadata = {
        "codeLength": "8",
        "currentStartTime": str(yyyymm(start)),
        "currentEndTime": str(yyyymm(end)),
        "currentDateBySource": str(yyyymm(end)),
    }
    params = result_params(
        start,
        hs_codes,
        diagnostic_metadata,
        page_num=1,
        page_size=100,
    )
    try:
        client.get(
            urljoin(base_url + "/", "queryDataForEN/queryDataListEn"),
            purpose="result API diagnostic request (metadata values are placeholders)",
            params=params,
        )
    except ChannelUnavailable:
        pass

    try:
        client.get(
            "http://43.248.49.97/",
            purpose="retired IP mirror named in task",
        )
    except ChannelUnavailable:
        pass


def write_notes(
    path: Path,
    *,
    client: RateLimitedClient,
    base_url: str,
    hs_codes: tuple[str, ...],
    start: date,
    requested_end: date,
    effective_end: date | None,
    rows: list[dict[str, str]],
    error: str | None,
    warnings: list[str],
) -> None:
    months = sorted({row["月份"] for row in rows})
    returned_codes = sorted({row["HS编码"] for row in rows})
    lines = [
        "# 海关月度量价通道说明",
        "",
        f"- 抓取日期：{date.today().isoformat()}",
        "- 验证状态：v1.1管线产出-未人工复核",
        f"- 主站：`{base_url}`",
        f"- 请求区间：`{start:%Y-%m}` 至 `{requested_end:%Y-%m}`",
        (
            f"- 服务端有效截止月：`{effective_end:%Y-%m}`"
            if effective_end
            else "- 服务端有效截止月：未取得（入口页被拦截）"
        ),
        f"- 请求 HS 编码：`{','.join(hs_codes)}`",
        f"- 实得月份数：{len(months)}",
        f"- 实得编码：{','.join(returned_codes) if returned_codes else '无'}",
        f"- CSV 数据行数：{len(rows)}",
        "",
        "## 结论",
        "",
    ]
    if error:
        lines.extend(
            [
                f"通道未打通：{error}",
                "",
                (
                    "`customs-monthly.csv` 只有表头时，不代表相关商品出口为零；"
                    "只代表本次没有从官方查询接口取得可核验数据。"
                ),
            ]
        )
    else:
        lines.append("官方查询接口返回了可解析数据；均价由美元金额/出口量计算。")

    lines.extend(
        [
            "",
            "## 编码口径",
            "",
            "- `85177950`：光通信设备的激光收发模块（首选、最精确）。",
            "- `85176229`：其他光通讯设备（较宽口径，可能包含非模块设备）。",
            "- `85177990`：税目8517设备用其他零件（更宽，不作为默认抓取项）。",
            (
                "- 任务示例中的 `85176230/85177090` 不是 2024 年官方税则附件中"
                "对应的现行 8 位光收发号列，因此没有把示例直接当成查询事实。"
            ),
            "",
            "编码核验来源：",
            "",
        ]
    )
    for label, url in TARIFF_SOURCES:
        lines.append(f"- [{label}]({url})")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend(["", "## 探测轨迹", ""])
    for index, probe in enumerate(client.probes, start=1):
        lines.extend(
            [
                f"### {index}. {probe.purpose}",
                "",
                f"- URL：`{probe.url}`",
                (
                    "- 参数：`"
                    + repr(probe.params)
                    + "`"
                    if probe.params is not None
                    else "- 参数：无"
                ),
                f"- HTTP：{probe.status if probe.status is not None else '无响应'}",
                f"- Content-Type：`{probe.content_type}`",
                f"- 返回摘要：{probe.result}",
                "",
            ]
        )

    lines.extend(
        [
            "## 替代路径",
            "",
            (
                "- 在可正常打开该站点的人工浏览器中访问"
                " `http://stats.customs.gov.cn/queryDataForEN/queryDataByWhereEn`，"
                "通过正常页面查询并导出；若出现验证码，按站点规则人工处理。"
            ),
            (
                "- 若需要自动复跑，可在站点不再对 requests 返回 412 后直接运行本脚本；"
                "脚本已固化公开表单的真实参数格式。"
            ),
            (
                "- [`43.248.49.97` 已由海关总署 2023 年第6号公告宣布停止使用]"
                f"({RETIRED_IP_NOTICE})，本次仅按任务要求保留一次探测，"
                "不应再作为生产镜像。"
            ),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch monthly GACC export quantity/value data by HS code"
    )
    parser.add_argument(
        "--hs-codes",
        default=",".join(DEFAULT_HS_CODES),
        help="comma-separated 8-10 digit HS codes",
    )
    parser.add_argument(
        "--start",
        type=parse_month,
        default=parse_month("2024-01"),
        help="first month, YYYY-MM (default: 2024-01)",
    )
    parser.add_argument(
        "--end",
        type=parse_month,
        default=None,
        help="last requested month, YYYY-MM (default: current month; server-capped)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--delay", type=float, default=MIN_DELAY_SECONDS)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--notes", type=Path, default=DEFAULT_NOTES)
    return parser


def parse_hs_codes(raw: str) -> tuple[str, ...]:
    codes = tuple(dict.fromkeys(item.strip() for item in raw.split(",") if item.strip()))
    if not codes:
        raise ValueError("at least one HS code is required")
    invalid = [code for code in codes if not re.fullmatch(r"\d{8,10}", code)]
    if invalid:
        raise ValueError(
            "HS codes must contain 8-10 digits: " + ", ".join(invalid)
        )
    return codes


def fetch(args: argparse.Namespace) -> tuple[list[dict[str, str]], str | None]:
    hs_codes = parse_hs_codes(args.hs_codes)
    requested_end = args.end or date.today().replace(day=1)
    if args.start > requested_end:
        raise ValueError("--start must not be later than --end")
    client = RateLimitedClient(delay=args.delay, timeout=args.timeout)
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    error: str | None = None
    effective_end: date | None = None
    base_url = args.base_url.rstrip("/")
    fetched_on = date.today().isoformat()

    try:
        entry = client.get(
            urljoin(base_url + "/", "queryDataForEN/queryDataByWhereEn"),
            purpose="English query form / metadata",
        )
        require_application_page(entry, "English query form / metadata")
        metadata = metadata_from_html(entry.text)
        server_end = parse_yyyymm(metadata["currentEndTime"], "currentEndTime")
        effective_end = min(requested_end, server_end)
        if effective_end < args.start:
            raise ParseFailure(
                f"server latest month {server_end:%Y-%m} is before start month"
            )

        valid_by_year: dict[int, dict[str, str]] = {}
        for year in range(args.start.year, effective_end.year + 1):
            code_page = client.get(
                urljoin(base_url + "/", "queryDataForEN/selectCodeTs"),
                purpose=f"HS code selector for {year}",
                params={
                    "codeTsList": "",
                    "codeLength": "8",
                    "yearId": str(year),
                    "pageSize": "10000",
                },
            )
            require_application_page(code_page, f"HS code selector for {year}")
            found = validate_codes(code_page.text, set(hs_codes))
            valid_by_year[year] = found
            missing = sorted(set(hs_codes) - set(found))
            if missing:
                warnings.append(
                    f"{year} HS selector did not list: {','.join(missing)}"
                )

        for target in month_range(args.start, effective_end):
            valid_codes = tuple(
                code for code in hs_codes if code in valid_by_year[target.year]
            )
            if not valid_codes:
                warnings.append(
                    f"{target:%Y-%m}: no requested code validated for that year"
                )
                continue

            page_num = 1
            total_size: int | None = None
            month_rows: list[dict[str, str]] = []
            while True:
                params = result_params(
                    target,
                    valid_codes,
                    metadata,
                    page_num=page_num,
                    page_size=args.page_size,
                )
                result = client.get(
                    urljoin(base_url + "/", "queryDataForEN/queryDataListEn"),
                    purpose=f"export result {target:%Y-%m} page {page_num}",
                    params=params,
                )
                require_application_page(
                    result, f"export result {target:%Y-%m} page {page_num}"
                )
                parsed = rows_from_result(
                    result.text,
                    target=target,
                    requested=set(valid_codes),
                    source_url=result.url,
                    fetched_on=fetched_on,
                )
                month_rows.extend(parsed)
                if total_size is None:
                    total_size = total_size_from_html(result.text)
                if total_size is None or page_num * args.page_size >= total_size:
                    break
                page_num += 1

            deduplicated = {
                (row["月份"], row["HS编码"]): row for row in month_rows
            }
            rows.extend(deduplicated.values())
            if not deduplicated:
                warnings.append(
                    f"{target:%Y-%m}: result page returned no requested-code rows"
                )
    except (ChannelUnavailable, ParseFailure) as exc:
        error = str(exc)
        if not client.probes or client.probes[-1].status != 412:
            warnings.append("main path stopped before a 412 response was recorded")
        probe_fallbacks(
            client,
            base_url,
            start=args.start,
            end=requested_end,
            hs_codes=hs_codes,
        )
    finally:
        write_csv(args.output, rows)
        write_notes(
            args.notes,
            client=client,
            base_url=base_url,
            hs_codes=hs_codes,
            start=args.start,
            requested_end=requested_end,
            effective_end=effective_end,
            rows=rows,
            error=error,
            warnings=warnings,
        )

    return rows, error


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        rows, error = fetch(args)
        hs_codes = parse_hs_codes(args.hs_codes)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
        return 2

    months = sorted({row["月份"] for row in rows})
    returned_codes = sorted({row["HS编码"] for row in rows})
    if error:
        summary = f"未打通（{error}）"
    else:
        summary = "已取得官方查询结果"
    print(f"探测结果摘要：{summary}")
    print(
        "拿到的月份数与编码："
        f"{len(months)} 个月；"
        f"{','.join(returned_codes) if returned_codes else '无'}"
        f"（请求 {','.join(hs_codes)}）"
    )
    print(f"CSV 行数：{len(rows)}")
    return 0 if not error else 2


if __name__ == "__main__":
    sys.exit(main())
