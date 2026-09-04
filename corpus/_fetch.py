#!/usr/bin/env python3
"""从巨潮资讯查询并下载 A 股上市公司年度报告 PDF。

示例：
    python download_annual_reports.py --stock-code 002384 --start-year 2022 --end-year 2025
    python download_annual_reports.py --stock-code 600519 --year 2025 --output ./reports

说明：
- 使用巨潮资讯公开网页所调用的历史公告查询接口。
- 默认只保留“年度报告”正文，排除摘要、英文版、取消公告等。
- 自动尝试深交所、上交所、北交所栏目。
- 请合理限速，并遵守网站条款和适用法律法规。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE_URL = "https://static.cninfo.com.cn/"
ALLOWED_PDF_HOSTS = {"static.cninfo.com.cn", "www.cninfo.com.cn", "cninfo.com.cn"}
MARKET_COLUMNS = ("szse", "sse", "bj")
PAGE_SIZE = 30
ANNUAL_REPORT_CATEGORY = "category_ndbg_szsh"

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)


@dataclass(frozen=True)
class AnnualReport:
    announcement_id: str
    stock_code: str
    company_name: str
    title: str
    announcement_date: str
    market_column: str
    pdf_url: str
    adjunct_url: str
    fiscal_year: int | None


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            "Origin": "https://www.cninfo.com.cn",
            "Referer": "https://www.cninfo.com.cn/new/fulltextSearch?notautosubmit=",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    return session


def normalize_stock_code(stock_code: str) -> str:
    value = stock_code.strip().upper()
    match = re.search(r"(\d{6})", value)
    if not match:
        raise ValueError("股票代码必须包含 6 位数字，例如 002384 或 600519。")
    return match.group(1)


def clean_html_title(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title or "")
    title = title.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", title).strip()


def infer_fiscal_year(title: str) -> int | None:
    # 优先匹配“2025年年度报告”这类表达。
    match = re.search(r"(20\d{2})\s*年?\s*年度报告", title)
    if match:
        return int(match.group(1))
    match = re.search(r"(20\d{2})", title)
    return int(match.group(1)) if match else None


def is_full_annual_report(title: str, include_revised: bool) -> bool:
    """只保留年度报告正文。

    保留：2025年年度报告、2025年年度报告（修订版/更新后）
    排除：摘要、英文版、取消、提示性公告、关于披露年报的公告等。
    """
    normalized = re.sub(r"\s+", "", title)
    if "年度报告" not in normalized:
        return False

    excluded_terms = (
        "摘要",
        "英文版",
        "取消",
        "关于",
        "提示性公告",
        "披露公告",
        "审议",
        "问询函",
        "回复",
        "说明会",
        "更正公告",
    )
    if any(term in normalized for term in excluded_terms):
        return False

    revision_terms = ("修订", "更新", "更正后")
    if not include_revised and any(term in normalized for term in revision_terms):
        return False

    # 标题中需出现年度报告主体，允许括号中的修订标识。
    return bool(re.search(r"20\d{2}年?年度报告(?:（[^）]*）|\([^)]*\))?$", normalized))


def parse_announcement_date(value: Any) -> str:
    if isinstance(value, (int, float)):
        # 巨潮返回毫秒时间戳。
        return datetime.fromtimestamp(value / 1000).date().isoformat()
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit() and len(value) >= 10:
            return datetime.fromtimestamp(int(value) / 1000).date().isoformat()
        return value[:10]
    return ""


def build_pdf_url(adjunct_url: str) -> str:
    normalized = (adjunct_url or "").lstrip("/")
    return urljoin(PDF_BASE_URL, normalized)


def _post_query(
    session: requests.Session,
    *,
    stock_code: str,
    column: str,
    start_date: date,
    end_date: date,
    page_num: int,
    timeout: int,
) -> dict[str, Any]:
    payload = {
        "pageNum": str(page_num),
        "pageSize": str(PAGE_SIZE),
        "column": column,
        "tabName": "fulltext",
        "plate": "",
        # 不依赖 orgId，使用搜索词匹配证券代码；后续再严格校验 secCode。
        "stock": "",
        "searchkey": stock_code,
        "secid": "",
        "category": ANNUAL_REPORT_CATEGORY,
        "trade": "",
        "seDate": f"{start_date.isoformat()}~{end_date.isoformat()}",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    response = session.post(QUERY_URL, data=payload, timeout=timeout)
    response.raise_for_status()
    try:
        result = response.json()
    except requests.JSONDecodeError as exc:
        snippet = response.text[:200].replace("\n", " ")
        raise RuntimeError(f"巨潮接口未返回 JSON：{snippet}") from exc
    if not isinstance(result, dict):
        raise RuntimeError("巨潮接口返回格式异常。")
    return result


def query_reports(
    session: requests.Session,
    stock_code: str,
    start_year: int,
    end_year: int,
    *,
    include_revised: bool,
    request_interval: float,
    timeout: int,
) -> list[AnnualReport]:
    start_date = date(start_year, 1, 1)
    # 年报通常次年披露，因此查询到 end_year + 1 年末，之后按标题中的财年过滤。
    end_date = date(end_year + 1, 12, 31)
    found: dict[str, AnnualReport] = {}

    for column in MARKET_COLUMNS:
        page_num = 1
        total_pages = 1
        logging.debug("查询市场栏目 %s", column)

        while page_num <= total_pages:
            try:
                payload = _post_query(
                    session,
                    stock_code=stock_code,
                    column=column,
                    start_date=start_date,
                    end_date=end_date,
                    page_num=page_num,
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                logging.warning("栏目 %s 查询失败：%s", column, exc)
                break

            announcements = payload.get("announcements") or []
            total_pages_raw = payload.get("totalpages") or payload.get("totalPages") or 1
            try:
                total_pages = max(1, int(total_pages_raw))
            except (TypeError, ValueError):
                total_pages = 1

            for item in announcements:
                sec_code = str(item.get("secCode") or "").strip()
                if sec_code != stock_code:
                    continue

                title = clean_html_title(str(item.get("announcementTitle") or ""))
                if not is_full_annual_report(title, include_revised=include_revised):
                    continue

                fiscal_year = infer_fiscal_year(title)
                if fiscal_year is None or not (start_year <= fiscal_year <= end_year):
                    continue

                adjunct_url = str(item.get("adjunctUrl") or "").strip()
                if not adjunct_url.lower().endswith(".pdf"):
                    continue

                announcement_id = str(item.get("announcementId") or "").strip()
                unique_key = announcement_id or adjunct_url
                found[unique_key] = AnnualReport(
                    announcement_id=announcement_id,
                    stock_code=sec_code,
                    company_name=str(item.get("secName") or "").strip(),
                    title=title,
                    announcement_date=parse_announcement_date(item.get("announcementTime")),
                    market_column=column,
                    pdf_url=build_pdf_url(adjunct_url),
                    adjunct_url=adjunct_url,
                    fiscal_year=fiscal_year,
                )

            page_num += 1
            if page_num <= total_pages:
                time.sleep(request_interval + random.uniform(0.1, 0.5))

        time.sleep(request_interval + random.uniform(0.1, 0.5))

    return sorted(
        found.values(),
        key=lambda report: (report.fiscal_year or 0, report.announcement_date, report.title),
        reverse=True,
    )


def sanitize_filename(value: str, max_length: int = 180) -> str:
    value = re.sub(r"[\\/:*?\"<>|\r\n]+", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" ._")
    return value[:max_length] or "annual_report"


def validate_pdf_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_PDF_HOSTS:
        raise ValueError(f"拒绝下载非巨潮官方地址：{url}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for block in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_pdf(
    session: requests.Session,
    report: AnnualReport,
    output_dir: Path,
    *,
    overwrite: bool,
    timeout: int,
) -> tuple[Path, str, int]:
    validate_pdf_url(report.pdf_url)
    company_dir = output_dir / report.stock_code
    company_dir.mkdir(parents=True, exist_ok=True)

    year = report.fiscal_year or "unknown"
    filename = sanitize_filename(
        f"{report.stock_code}_{report.company_name}_{year}_{report.title}.pdf"
    )
    target_path = company_dir / filename

    if target_path.exists() and not overwrite:
        logging.info("已存在，跳过：%s", target_path)
        return target_path, sha256_file(target_path), target_path.stat().st_size

    temporary_path = target_path.with_suffix(".pdf.part")
    logging.info("下载：%s", report.title)

    headers = {
        "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
        "Referer": "https://www.cninfo.com.cn/",
    }
    with session.get(report.pdf_url, headers=headers, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        first_chunk = b""
        with temporary_path.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                if not first_chunk:
                    first_chunk = chunk[:8]
                file_obj.write(chunk)

    if not first_chunk.startswith(b"%PDF"):
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"下载内容不是有效 PDF（Content-Type={content_type or 'unknown'}）：{report.pdf_url}"
        )

    temporary_path.replace(target_path)
    return target_path, sha256_file(target_path), target_path.stat().st_size


def write_metadata(
    reports: Iterable[AnnualReport],
    download_results: dict[str, tuple[Path, str, int] | str],
    output_dir: Path,
    stock_code: str,
) -> tuple[Path, Path]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        key = report.announcement_id or report.adjunct_url
        result = download_results.get(key)
        row = asdict(report)
        if isinstance(result, tuple):
            path, checksum, size_bytes = result
            row.update(
                {
                    "download_status": "downloaded",
                    "local_path": str(path.resolve()),
                    "sha256": checksum,
                    "size_bytes": size_bytes,
                    "error": "",
                }
            )
        else:
            row.update(
                {
                    "download_status": "failed" if result else "not_downloaded",
                    "local_path": "",
                    "sha256": "",
                    "size_bytes": "",
                    "error": result or "",
                }
            )
        rows.append(row)

    metadata_dir = output_dir / stock_code
    metadata_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metadata_dir / "annual_reports.csv"
    json_path = metadata_dir / "annual_reports.json"

    fieldnames = [
        "announcement_id",
        "stock_code",
        "company_name",
        "title",
        "fiscal_year",
        "announcement_date",
        "market_column",
        "pdf_url",
        "adjunct_url",
        "download_status",
        "local_path",
        "sha256",
        "size_bytes",
        "error",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as file_obj:
        json.dump(rows, file_obj, ensure_ascii=False, indent=2)

    return csv_path, json_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    current_year = date.today().year
    parser = argparse.ArgumentParser(
        description="从巨潮资讯查询并下载指定 A 股公司的年度报告 PDF。"
    )
    parser.add_argument("--stock-code", required=True, help="6位股票代码，如 002384")
    parser.add_argument("--year", type=int, help="只下载一个财年，例如 2025")
    parser.add_argument("--start-year", type=int, default=current_year - 5, help="起始财年")
    parser.add_argument("--end-year", type=int, default=current_year, help="结束财年")
    parser.add_argument("--output", type=Path, default=Path("./annual_reports"), help="输出目录")
    parser.add_argument(
        "--include-revised",
        action="store_true",
        help="同时保留修订版/更新版年报；默认只下载原始正文版本",
    )
    parser.add_argument("--list-only", action="store_true", help="只查询并输出元数据，不下载 PDF")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 PDF")
    parser.add_argument("--interval", type=float, default=1.5, help="请求间隔秒数，默认 1.5")
    parser.add_argument("--timeout", type=int, default=40, help="单次请求超时秒数")
    parser.add_argument("--verbose", action="store_true", help="输出调试日志")
    args = parser.parse_args(argv)

    if args.year is not None:
        args.start_year = args.year
        args.end_year = args.year
    if args.start_year > args.end_year:
        parser.error("start-year 不能大于 end-year")
    if args.interval < 1.0:
        parser.error("为避免对源站造成压力，interval 不应低于 1 秒")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    try:
        stock_code = normalize_stock_code(args.stock_code)
    except ValueError as exc:
        logging.error(str(exc))
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    session = build_session()

    logging.info("查询 %s，财年 %s-%s", stock_code, args.start_year, args.end_year)
    try:
        reports = query_reports(
            session,
            stock_code,
            args.start_year,
            args.end_year,
            include_revised=args.include_revised,
            request_interval=args.interval,
            timeout=args.timeout,
        )
    except Exception as exc:  # 顶层给出清晰错误，详细栈由 --verbose 辅助定位
        logging.exception("查询失败：%s", exc) if args.verbose else logging.error("查询失败：%s", exc)
        return 1

    if not reports:
        logging.warning("没有找到符合条件的年度报告。可尝试扩大年份或使用 --include-revised。")
        write_metadata([], {}, args.output, stock_code)
        return 0

    logging.info("找到 %d 份年度报告正文", len(reports))
    for report in reports:
        logging.info(
            "  %s | %s | %s",
            report.fiscal_year,
            report.announcement_date,
            report.title,
        )

    results: dict[str, tuple[Path, str, int] | str] = {}
    if not args.list_only:
        for index, report in enumerate(reports, start=1):
            key = report.announcement_id or report.adjunct_url
            try:
                results[key] = download_pdf(
                    session,
                    report,
                    args.output,
                    overwrite=args.overwrite,
                    timeout=args.timeout,
                )
            except Exception as exc:
                logging.error("下载失败：%s | %s", report.title, exc)
                results[key] = str(exc)
            if index < len(reports):
                time.sleep(args.interval + random.uniform(0.1, 0.5))

    csv_path, json_path = write_metadata(reports, results, args.output, stock_code)
    logging.info("CSV 元数据：%s", csv_path)
    logging.info("JSON 元数据：%s", json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
