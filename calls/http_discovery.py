"""Public HTTP adapter for the overseas daily-discovery seam.

It supports fixture-shaped JSON, RSS/Atom and ordinary public HTML listing
pages.  It performs plain unauthenticated GETs only; it does not bypass login,
paywall or anti-bot controls.  Unparseable/dynamic sites return an explicit
endpoint failure for the human queue.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any, TYPE_CHECKING
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from .daily_discovery import Endpoint


@dataclass(frozen=True)
class HttpFetchResult:
    endpoint_id: str
    items: tuple[dict[str, Any], ...]
    failure: str


ARTICLE_HINT = re.compile(
    r"(?:news|press|release|article|blog|filing|financial|investor|node|detail|20\d{2})",
    re.I,
)
DATE_KEYS = {
    "article:published_time", "date", "datepublished", "date_published",
    "publishdate", "publish_date", "citation_publication_date",
}


def _date_only(value: str) -> str:
    value = (value or "").strip()
    match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", value)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
        except ValueError:
            return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


class _HTML(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.time_values: list[str] = []
        self.paragraphs: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._href = ""
        self._link_buffer: list[str] = []
        self._json_ld = False
        self._json_buffer: list[str] = []
        self.json_ld: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "meta":
            key = (values.get("property") or values.get("name") or values.get("itemprop") or "").lower()
            if key and values.get("content"):
                self.meta[key] = values["content"].strip()
        elif tag == "link" and "canonical" in values.get("rel", "").lower():
            self.canonical = urljoin(self.base_url, values.get("href", ""))
        elif tag == "time" and values.get("datetime"):
            self.time_values.append(values["datetime"])
        if tag in {"title", "h1", "p"} and self._capture is None:
            self._capture = tag
            self._buffer = []
        if tag == "a":
            self._href = values.get("href", "")
            self._link_buffer = []
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._json_ld = True
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)
        if self._href:
            self._link_buffer.append(data)
        if self._json_ld:
            self._json_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._json_ld and tag == "script":
            payload = "".join(self._json_buffer).strip()
            if payload:
                self.json_ld.append(payload)
            self._json_ld = False
            self._json_buffer = []
            return
        if tag == "a" and self._href:
            text = re.sub(r"\s+", " ", "".join(self._link_buffer)).strip()
            if text:
                self.links.append((urljoin(self.base_url, self._href), text))
            self._href = ""
            self._link_buffer = []
        if tag != self._capture:
            return
        text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
        if tag in {"title", "h1"} and text:
            self.meta.setdefault(tag, text)
        elif tag == "p" and len(text) >= 20:
            self.paragraphs.append(text)
        self._capture = None
        self._buffer = []


def _json_ld_date(blocks: list[str]) -> str:
    def walk(value: Any) -> str:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() == "datepublished":
                    found = _date_only(str(item))
                    if found:
                        return found
            for item in value.values():
                found = walk(item)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = walk(item)
                if found:
                    return found
        return ""

    for block in blocks:
        try:
            found = walk(json.loads(block))
        except json.JSONDecodeError:
            continue
        if found:
            return found
    return ""


def parse_html_item(body: str, url: str, fallback_title: str = "") -> dict[str, Any]:
    parser = _HTML(url)
    parser.feed(body)
    published = ""
    for key, value in parser.meta.items():
        if key in DATE_KEYS:
            published = _date_only(value)
            if published:
                break
    if not published:
        published = next((found for found in map(_date_only, parser.time_values) if found), "")
    if not published:
        published = _json_ld_date(parser.json_ld)
    if not published:
        published = _date_only(body[:20000])
    title = (
        parser.meta.get("og:title") or parser.meta.get("twitter:title")
        or parser.meta.get("h1") or fallback_title or parser.meta.get("title") or ""
    )
    canonical = parser.canonical or url
    return {
        "url": canonical,
        "title": title,
        "published_at": published,
        "origin_key": canonical,
        "paragraphs": [
            {"anchor": f"p{index}", "text": text}
            for index, text in enumerate(parser.paragraphs[:120], 1)
        ],
    }


def discover_article_links(body: str, url: str, limit: int = 20) -> list[tuple[str, str]]:
    parser = _HTML(url)
    parser.feed(body)
    origin = urlparse(url).netloc.lower()
    found: list[tuple[str, str]] = []
    seen: set[str] = {url.rstrip("/")}
    for link, title in parser.links:
        parsed = urlparse(link)
        normalized = link.split("#", 1)[0].rstrip("/")
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != origin:
            continue
        if normalized in seen or len(title) < 8 or not ARTICLE_HINT.search(parsed.path + " " + title):
            continue
        if parsed.path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".zip")):
            continue
        seen.add(normalized)
        found.append((normalized, title))
        if len(found) >= limit:
            break
    return found


def _strip_html(value: str) -> str:
    parser = _HTML("https://invalid.local/")
    parser.feed(f"<p>{value}</p>")
    return " ".join(parser.paragraphs)


def parse_feed(body: str, base_url: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    items: list[dict[str, Any]] = []
    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{*}entry")
    for index, entry in enumerate(entries, 1):
        def text(*names: str) -> str:
            for name in names:
                node = entry.find(name)
                if node is None:
                    node = entry.find("{*}" + name)
                if node is not None and node.text:
                    return node.text.strip()
            return ""

        link = text("link")
        if not link:
            node = entry.find("{*}link")
            if node is not None:
                link = node.attrib.get("href", "")
        description = text("description", "summary", "content")
        paragraph = _strip_html(description) or description.strip()
        items.append({
            "url": urljoin(base_url, link),
            "title": text("title"),
            "published_at": _date_only(text("pubDate", "published", "updated")),
            "origin_key": urljoin(base_url, link),
            "paragraphs": ([{"anchor": f"feed-item-{index}", "text": paragraph}] if paragraph else []),
        })
    return items


class HttpFetcher:
    """Fetch public entity endpoints and normalize them to fixture-shaped items."""

    fetch_mode = "http"

    def __init__(self, run_date: str, timeout: int = 30, lookback_days: int = 14, max_items: int = 20) -> None:
        self.run_date = date.fromisoformat(run_date)
        self.timeout = timeout
        self.lookback_days = lookback_days
        self.max_items = max_items

    def _get(self, url: str) -> tuple[str, str, str]:
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; calls-daily-discovery/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/json,application/rss+xml,application/atom+xml",
        })
        with urlopen(request, timeout=self.timeout) as response:
            body = response.read(8_000_000)
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace"), content_type, response.geturl()

    def _in_window(self, item: dict[str, Any]) -> bool:
        published = _date_only(str(item.get("published_at", "")))
        if not published:
            return True  # retained so _parse_item records an explicit invalid_item
        when = date.fromisoformat(published)
        return self.run_date - timedelta(days=self.lookback_days) <= when <= self.run_date

    def fetch(self, endpoint: "Endpoint") -> HttpFetchResult:
        try:
            body, content_type, final_url = self._get(endpoint.url)
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public GET failed: {type(exc).__name__}: {exc}")
        stripped = body.lstrip()
        try:
            if content_type == "application/json" or stripped.startswith(("{", "[")):
                payload = json.loads(body)
                raw_items = payload.get("items", ()) if isinstance(payload, dict) else payload
                items = [dict(item) for item in raw_items if isinstance(item, dict)]
            elif "xml" in content_type or stripped.startswith("<?xml") or "<rss" in stripped[:200].lower():
                items = parse_feed(body, final_url)
            else:
                items = []
                page = parse_html_item(body, final_url)
                if page["published_at"] and page["paragraphs"]:
                    items.append(page)
                for link, title in discover_article_links(body, final_url, self.max_items):
                    try:
                        article_body, article_type, article_url = self._get(link)
                    except Exception:
                        continue
                    if "json" in article_type:
                        continue
                    item = parse_html_item(article_body, article_url, title)
                    if item["paragraphs"]:
                        items.append(item)
            filtered = tuple(item for item in items if self._in_window(item))
            return HttpFetchResult(endpoint.endpoint_id, filtered, "")
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public response parse failed: {type(exc).__name__}: {exc}")
