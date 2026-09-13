"""Public HTTP adapter for the overseas daily-discovery seam.

It supports fixture-shaped JSON, RSS/Atom and ordinary public HTML listing
pages.  It performs plain unauthenticated GETs only; it does not bypass login,
paywall or anti-bot controls.  Unparseable/dynamic sites return an explicit
endpoint failure for the human queue.
"""

from __future__ import annotations

import json
import math
import re
import signal
import ssl
import threading
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from html import escape
from typing import Any, TYPE_CHECKING
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

if TYPE_CHECKING:
    from .daily_discovery import Endpoint


@dataclass(frozen=True)
class HttpFetchResult:
    endpoint_id: str
    items: tuple[dict[str, Any], ...]
    failure: str
    # 端点级失败放在 failure；单篇文章的详情抓取/解析失败在这里逐条追踪，
    # 使部分成功不会把端点结果伪装成完全无错。
    article_failures: tuple[dict[str, str], ...] = ()


ARTICLE_HINT = re.compile(
    r"(?:news|press|release|article|blog|filing|financial|investor|node|detail|20\d{2})",
    re.I,
)
# 导航/索引/辅助页与附件，不得因同域被当作文章链接。
ARTICLE_PATH_EXCLUDE = re.compile(
    r"(?:^|/)(?:home|faq|faqs|index|overview|search|events?|webinars?|webcasts?|presentations?"
    r"|tag|category|privacy|terms|conditions|contact|careers|login|signin|subscribe|newsletters?"
    r"|latest-news|impressum|press-coverage|disclaimer|share-price(?:-tools)?|ir-calendar|live-events|news-events|annual-reports|quarterly-results)"
    r"(?:\.aspx?|\.html?)?/?$"
    r"|(?:^|/)(?:sec-filings|email-alerts|investor-faqs|financial-information|financial-reports"
    r"|rss-feeds|analyst-reports|analyst-relations|filter-results|articles|blogs|company|artificial-intelligence"
    r"|people|executives|podcasts|videos|featured-blogs|security|networking|innovation"
    r"|collaboration|observability)(?:\.aspx?|\.html?)?/?$"
    r"|(?:^|/)(?:press-releases|news-releases|financial-news-releases|media|investors?"
    r"|blog|newsroom|news|regulatory-news)(?:\.aspx?|\.html?)?/?$"
    r"|/(?:events?|webinars?|webcasts?|presentations?)/"
    r"|default\.aspx$"
    r"|\.(?:jpe?g|png|gif|zip|pdf|css|js)$",
    re.I,
)
ARTICLE_TITLE_EXCLUDE = re.compile(
    r"^(?:the )?(?:investors?|newsroom|media(?: centre| center)?|events?|webinars?|webcasts?"
    r"|presentations?|search|contact(?: us)?|privacy|terms|careers|log ?in|subscribe|newsletters?"
    r"|rss(?: feed)?|blog|blogs?|resources|about(?: us)?|support|leadership|strategy"
    r"|strategic review|investment case|business model|summary financials|regulatory news"
    r"|view all|analyst relations|aim rule|advisers|financial calendar|ir calendar|live events|share price tools|results, reports"
    r"|investor relations(?: home)?|investor faqs?|investor email alerts?|email alerts?"
    r"|sec filings?|financial results|financial reports|news releases?|press releases?)\b",
    re.I,
)
DATE_KEYS = {
    "article:published_time", "date", "datepublished", "date_published",
    "publishdate", "publish_date", "citation_publication_date",
    "publisheddate", "publication_date", "release_date", "dc.date",
}
# 嵌入 JSON 中的文章归属日期字段（如 Lumentum 博客节点 JSON 的 "field_date"）。
# datePublished 只由 ld+json 的类型化节点路径处理，避免未绑定类型的正文正则双计。
JSON_DATE_FIELDS = (
    "field_date", "published_at", "publish_date",
    "publication_date", "release_date", "date_posted",
)
_MONTHS = {name: index for index, name in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def _trusted_date_class(class_value: str) -> bool:
    """class 里的日期 token 必须明确指向文章发布日期（如 "date"、"Type--Date"）；
    行情/更新时间类 class（share-price、updated 等）不可信。"""
    for token in class_value.lower().split():
        if MARKER_CLASS_HINT.search(token):
            continue
        if token in {"date", "field_date", "publishdate", "published"} \
                or token.endswith(("-date", "_date", "--date")) or "publish" in token:
            return True
    return False


def _month_number(name: str) -> int:
    return _MONTHS.get(name.lower()[:3], 0)


def _date_only(value: str) -> str:
    value = (value or "").strip()
    match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", value)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
        except ValueError:
            return ""
    match = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(20\d{2})\b", value)  # 28 May 2026
    if match and _month_number(match.group(2)):
        try:
            return date(int(match.group(3)), _month_number(match.group(2)), int(match.group(1))).isoformat()
        except ValueError:
            return ""
    match = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(20\d{2})\b", value)  # June 25, 2026
    if match and _month_number(match.group(1)):
        try:
            return date(int(match.group(3)), _month_number(match.group(1)), int(match.group(2))).isoformat()
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
        self.time_values: list[tuple[str, str]] = []
        self.date_values: list[str] = []
        self.paragraphs: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._href = ""
        self._link_buffer: list[str] = []
        self._json_ld = False
        self._json_buffer: list[str] = []
        self.json_ld: list[str] = []
        self._date_capture_tag = ""
        self._date_depth = 0
        self._date_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "meta":
            key = (values.get("property") or values.get("name") or values.get("itemprop") or "").lower()
            if key and values.get("content"):
                self.meta[key] = values["content"].strip()
        elif tag == "link" and "canonical" in values.get("rel", "").lower():
            try:
                self.canonical = urljoin(self.base_url, values.get("href", ""))
            except ValueError:
                pass  # malformed external markup must not abort the page
        elif tag == "time" and values.get("datetime"):
            self.time_values.append((values["datetime"], values.get("class", "")))
        # 发布日期常出现在 class 含 date 的短元素中；只有可信的日期类 token 才收
        # （如 "Type--Date"、"blog-post-header2_date"），行情/更新时间类 class 不收。
        if not self._date_capture_tag and not values.get("datetime") \
                and (_trusted_date_class(values.get("class", "")) or
                     (tag == "time" and not MARKER_CLASS_HINT.search(values.get("class", "")))):
            self._date_capture_tag = tag
            self._date_depth = 1
            self._date_buffer = []
        elif self._date_capture_tag and tag == self._date_capture_tag:
            self._date_depth += 1
        if tag == "p" and self._capture == "p":
            self._flush_paragraph()  # 未闭合的 <p>（如 IQE 压缩 HTML）按下一段切分
        if tag in {"title", "h1", "p"} and self._capture is None:
            self._capture = tag
            self._buffer = []
        if tag == "a":
            self._href = values.get("href", "")
            self._link_buffer = []
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._json_ld = True
            self._json_buffer = []

    def _flush_paragraph(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
        if len(text) >= 20:
            self.paragraphs.append(text)
        self._capture = None
        self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)
        if self._href:
            self._link_buffer.append(data)
        if self._json_ld:
            self._json_buffer.append(data)
        if self._date_capture_tag:
            self._date_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._json_ld and tag == "script":
            payload = "".join(self._json_buffer).strip()
            if payload:
                self.json_ld.append(payload)
            self._json_ld = False
            self._json_buffer = []
            return
        if self._date_capture_tag and tag == self._date_capture_tag:
            self._date_depth -= 1
            if self._date_depth <= 0:
                text = re.sub(r"\s+", " ", " ".join(self._date_buffer)).strip()
                if text and len(text) <= 64:
                    self.date_values.append(text)
                self._date_capture_tag = ""
                self._date_buffer = []
        if tag == "a" and self._href:
            text = re.sub(r"\s+", " ", "".join(self._link_buffer)).strip()
            try:
                self.links.append((urljoin(self.base_url, self._href), text))
            except ValueError:
                pass  # e.g. real ficonTEC href https://masstart.eu]
            self._href = ""
            self._link_buffer = []
        if tag != self._capture:
            return
        if tag in {"title", "h1"}:
            text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
            if text:
                self.meta.setdefault(tag, text)
            self._capture = None
            self._buffer = []
        elif tag == "p":
            self._flush_paragraph()

    def _finalize(self) -> None:
        """收尾未闭合的捕获（压缩 HTML 的最后一个 <p> 可能没有结束标签）。"""
        if self._capture == "p":
            self._flush_paragraph()
        elif self._capture in {"title", "h1"}:
            text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
            if text:
                self.meta.setdefault(self._capture, text)
            self._capture = None
            self._buffer = []
        if self._date_capture_tag:
            text = re.sub(r"\s+", " ", " ".join(self._date_buffer)).strip()
            if text and len(text) <= 64:
                self.date_values.append(text)
            self._date_capture_tag = ""
            self._date_depth = 0
            self._date_buffer = []


ARTICLE_JSON_TYPES = frozenset({
    "article", "newsarticle", "blogposting", "techarticle", "pressrelease", "report",
})
MARKER_CLASS_HINT = re.compile(r"price|share|ticker|market|quote|stock|update|modified|revision", re.I)
# 分页/筛选类 query 拒绝；带文章 ID 的 query（如 articleId=、p=）保留。
ARTICLE_QUERY_EXCLUDE = re.compile(r"page=\d|(?:^|&)(?:pt|start|offset|sort|filterresults?)=", re.I)


def _node_types(node: dict[str, Any]) -> set[str]:
    raw = node.get("@type", ())
    items = raw if isinstance(raw, list) else [raw]
    return {str(item).lower() for item in items}


def _strip_lang_segment(path: str) -> str:
    """去掉单个语言前缀段（如 /en/、/jp/），其余不动；仅用于路径等值比较。"""
    parts = path.split("/")
    if len(parts) > 2 and len(parts[1]) == 2 and parts[1].isalpha():
        return "/" + "/".join(parts[2:])
    return path


def _norm_title_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _title_binds(node_title: str, page_title: str) -> bool:
    """标题等值匹配：去 "| 站点后缀" 后逐字符规范化全等，不做包含/前缀匹配。"""
    left = _norm_title_text(node_title.split("|")[0])
    right = _norm_title_text(page_title.split("|")[0])
    return bool(left) and bool(right) and left == right


def _url_binds(node_url: str, canonical_url: str) -> bool:
    """URL 等值匹配：绝对 URL 比较主机（去 www.）+ 语言规范化路径（+query）；
    路径/别名形式比较语言规范化路径全等。不做子串/前缀匹配。"""
    value = (node_url or "").strip()
    if not value or not canonical_url:
        return False
    canonical = urlparse(canonical_url)
    if value.startswith("/"):
        return _strip_lang_segment(canonical.path) == _strip_lang_segment(value)
    if "://" not in value:
        return False
    node = urlparse(value)
    node_host = node.netloc.lower().removeprefix("www.")
    canonical_host = canonical.netloc.lower().removeprefix("www.")
    if node_host != canonical_host:
        return False
    if _strip_lang_segment(node.path).rstrip("/") != _strip_lang_segment(canonical.path).rstrip("/"):
        return False
    if node.query or canonical.query:
        return node.query == canonical.query
    return True


def _node_binds_page(node: dict[str, Any], canonical_url: str, title: str,
                     require_locator: bool = False) -> bool:
    """JSON-LD 节点归属：有 URL/mainEntityOfPage/@id 字段时只认 URL 等值，
    明示 URL 不匹配时不得用标题兜底；无 URL 字段时标题等值。require_locator
    （嵌套 related/author 等位置的节点）时无定位字段一律拒绝，不得默认接受。"""
    url_values = []
    for key in ("url", "mainEntityOfPage", "@id"):
        value = node.get(key)
        if isinstance(value, dict):
            value = value.get("@id", "")
        if isinstance(value, str) and value.strip():
            url_values.append(value.strip())
    if url_values:
        return any(_url_binds(item, canonical_url) for item in url_values)
    headline = str(node.get("headline") or node.get("name") or "")
    if headline.strip():
        return _title_binds(headline, title)
    return not require_locator


def _collect_ld_nodes(payload: Any) -> list[tuple[dict[str, Any], bool]]:
    """收集 (datePublished 节点, 是否显式主节点)。主节点仅限块根、顶层列表元素、
    顶层 @graph 成员与顶层 mainEntity；嵌套在 related/author 等属性下的节点
    不算显式主节点，必须等值绑定才可接受。"""
    roots: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        roots.append(payload)
        graph = payload.get("@graph")
        if isinstance(graph, list):
            roots.extend(item for item in graph if isinstance(item, dict))
        main_entity = payload.get("mainEntity")
        if isinstance(main_entity, dict):
            roots.append(main_entity)
    elif isinstance(payload, list):
        roots.extend(item for item in payload if isinstance(item, dict))
    root_ids = {id(root) for root in roots}
    collected: list[tuple[dict[str, Any], bool]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("datePublished") is not None:
                collected.append((value, id(value) in root_ids))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return collected


def _json_ld_date(blocks: list[str], canonical_url: str, title: str) -> str:
    """只认 @type 为文章类型的节点。显式主节点（无定位）可接受；嵌套节点必须
    等值绑定。无法唯一绑定时留空，由 invalid_item 拒收并报告。"""
    article_nodes: list[tuple[dict[str, Any], bool]] = []
    for block in blocks:
        try:
            payload = json.loads(block)
        except json.JSONDecodeError:
            continue
        article_nodes.extend(
            (node, primary) for node, primary in _collect_ld_nodes(payload)
            if _node_types(node) & ARTICLE_JSON_TYPES
        )
    if not article_nodes:
        return ""
    bound = [
        node for node, primary in article_nodes
        if _node_binds_page(node, canonical_url, title, require_locator=not primary)
    ]
    if len(bound) == 1:
        return _date_only(str(bound[0]["datePublished"]))
    return ""  # 无法唯一绑定：留空并报告 invalid


def _json_object_binds(obj_text: str, canonical_url: str, title: str) -> bool:
    """嵌入 JSON 对象的归属：只看对象顶层自标识字段。有 URL 类字段时只认
    URL 等值（明示不匹配即拒绝，不用标题兜底）；无 URL 类字段时标题等值；
    两者皆无（无法识别的结构，如非标准 Drupal 嵌入）一律不绑定。"""
    try:
        payload = json.loads(obj_text)
    except (json.JSONDecodeError, ValueError):
        return False
    if not isinstance(payload, dict):
        return False
    url_values = []
    for key in ("url", "path", "alias", "@id", "slug", "mainEntityOfPage"):
        value = payload.get(key)
        if isinstance(value, dict):
            value = value.get("alias") or value.get("@id") or ""
        if isinstance(value, str) and value.strip():
            url_values.append(value.strip())
    if url_values:
        return any(_url_binds(item, canonical_url) for item in url_values)
    for key in ("title", "headline", "name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _title_binds(value, title)
    return False


def _enclosing_json_object(body: str, pos: int) -> str:
    """Locate the enclosing object without counting braces inside JSON strings.

    Real Drupal article nodes exceed 40k. Decode the complete object instead of
    returning a truncated prefix, while retaining the caller's URL binding gate.
    """
    script = body.rfind("<script", 0, pos)
    begin = body.find(">", script) + 1 if script >= 0 else 0
    stack: list[int] = []
    quoted = escaped = False
    for index in range(begin, pos):
        char = body[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "{":
            stack.append(index)
        elif char == "}" and stack:
            stack.pop()
    if not stack:
        return ""
    start = stack[-1]
    try:
        _, end = json.JSONDecoder().raw_decode(body, start)
    except (ValueError, RecursionError):
        return ""
    return body[start:end] if end > pos else ""


def _json_field_date(body: str, canonical_url: str, title: str) -> str:
    """嵌入 JSON 的文章日期字段：每个匹配都必须在其所属 JSON 对象内等值绑定
    当前 URL/标题；无法绑定（含唯一出现）一律留空，由 invalid_item 拒收并报告。"""
    body = _mask_ld_json(body)
    for key in JSON_DATE_FIELDS:
        matches = list(re.finditer(r'"' + key + r'"\s*:\s*"([^"]{4,64})"', body))
        if not matches:
            continue
        bound: list[str] = []
        for match in matches:
            obj = _enclosing_json_object(body, match.start())
            if obj and _json_object_binds(obj, canonical_url, title):
                found = _date_only(match.group(1))
                if found:
                    bound.append(found)
        if len(set(bound)) == 1:
            return bound[0]
        # 多个字段节点无法唯一归属，或唯一节点无法绑定：不猜，留空报 invalid。
    return ""


def _mask_ld_json(body: str) -> str:
    """屏蔽 ld+json 脚本内容，避免无类型正文正则重复消费 JSON-LD 的日期。"""
    spans = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>',
                       body, re.I | re.S)
    for span in spans:
        body = body.replace(span, " " * len(span))
    return body


# 电头（dateline）：整段必须是 "城市, 地区 日期" 形式的短段，才能归属当前文章。
# 整句锚定 + 逗号前缀避免了把正文叙述里的日期（如 "On 27 April 2026, ..."）当成发布日期。
_DATELINE = re.compile(
    r"^[A-Za-z][A-Za-z .,'&()\-]{0,50},\s*[A-Za-z .,'\-]{0,40}\s*"
    r"(?:(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(20\d{2})|([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(20\d{2}))\.?$",
    re.I,
)


def _dateline_date(paragraphs: list[str]) -> str:
    # 电头常排在前几段样板声明之后，只收足够短的段，避免误取正文叙述日期。
    for text in paragraphs[:8]:
        if len(text) > 120:
            continue
        match = _DATELINE.match(text)
        if not match:
            continue
        if match.group(2):
            month = _month_number(match.group(2))
            day, year = int(match.group(1)), int(match.group(3))
        else:
            month = _month_number(match.group(4))
            day, year = int(match.group(5)), int(match.group(6))
        if month:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return ""
    return ""



def _publication_region(body: str, tag: str, class_name: str) -> list[str]:
    """Read one publisher's visible date/body container, preserving nesting."""
    class Region(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.depth = 0
            self.chunks = []
            self.regions = []

        def handle_starttag(self, name, attrs):
            if name == tag and (self.depth or class_name in dict(attrs).get('class', '').split()):
                self.depth += 1
            if self.depth:
                self.chunks.append(self.get_starttag_text())

        def handle_endtag(self, name):
            if self.depth:
                self.chunks.append(f'</{name}>')
                if name == tag:
                    self.depth -= 1
                    if not self.depth:
                        self.regions.append(''.join(self.chunks))
                        self.chunks = []

        def handle_data(self, value):
            if self.depth:
                self.chunks.append(value)

        def handle_entityref(self, value):
            self.handle_data('&' + value + ';')

        def handle_charref(self, value):
            self.handle_data('&#' + value + ';')

    parser = Region()
    parser.feed(body)
    return parser.regions


def _sourcephotonics_publication_date(body: str, url: str) -> str:
    regions = _publication_region(body, 'div', 'entry-content')
    if len(regions) != 1:
        return ''
    parser = _HTML(url)
    parser.feed(regions[0])
    parser._finalize()
    dates = set()
    for paragraph in parser.paragraphs[:8]:
        # Only release datelines, not the adjacent "When: ..." event dates.
        match = re.match(
            r'(?:Los Angeles, California|West Hills and (?:San Francisco|Los Angeles), California'
            r'|Copenhagen, Denmark and West Hills, CA),\s*([A-Za-z]+ \d{1,2}, 20\d{2})'
            r'(?:\s*[–—-]\s*Source Photonics|\s*$)', paragraph)
        release = re.match(r'([A-Za-z]+ \d{1,2}, 20\d{2})\s+\d{1,2}:\d{2}\s+ET\s*\|\s*Source:\s*Source Photonics', paragraph)
        if match or release:
            dates.add(_date_only((match or release).group(1)))
    return next(iter(dates)) if len(dates) == 1 else ''


def _site_publication_date(body: str, url: str, paragraphs: list[str]) -> str:
    """Known official release templates only; never infer dates from URL paths."""
    parsed = urlparse(url)
    patterns = []
    if parsed.hostname == "newsroom.ao-inc.com" and parsed.path.startswith("/news-releases/"):
        patterns = [r'<p[^>]*class=["\']post-date-author["\'][^>]*>\s*([A-Za-z]+ \d{1,2}, 20\d{2})']
    elif parsed.hostname in {"www.evgroup.com", "evgroup.com"} and parsed.path.startswith("/company/news/detail/"):
        for paragraph in paragraphs:
            specific = re.match(r'(?:LEUVEN \(Belgium\),\s*|Toronto, ON\s*\|\s*)([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?, 20\d{2})', paragraph)
            if specific:
                return _date_only(re.sub(r'(\d)(?:st|nd|rd|th)\b', r'\1', specific.group(1)))
            match = re.match(r"[A-Z .,-]+[a-zA-Z .,-]*\b(?:Austria|Germany|USA|Taiwan),\s*([A-Za-z]+ \d{1,2}, 20\d{2})", paragraph)
            if match:
                return _date_only(match.group(1))
    elif parsed.hostname in {"www.furukawaelectric.com", "www.furukawa.co.jp"} and re.search(r"/en/release/20\d{2}/", parsed.path):
        patterns = [r'<div[^>]*class=["\'][^"\']*\btext-right\b[^"\']*["\'][^>]*>\s*<p[^>]*>([^<]+)</p>']
    elif parsed.hostname == "sumitomoelectric.com" and parsed.path.startswith("/press/"):
        patterns = [r'<h1[^>]*class=["\'][^"\']*\ba-subheadline\b[^"\']*["\'][^>]*>([^<]+)</h1>']
    elif parsed.hostname == "www.ff-opticalcomponents.com" and parsed.path.startswith("/en/information/"):
        patterns = [r'<div[^>]*class=["\']m_page-meta["\'][^>]*>\s*<p>([^<]+)</p>']
    elif parsed.hostname == "lumilens.com" and parsed.path.startswith("/news-insights/"):
        for paragraph in paragraphs:
            match = re.match(r"SAN JOSE,\s*Calif\.\s*[—–-]\s*([A-Za-z]+ \d{1,2}, 20\d{2})", paragraph)
            if match:
                return _date_only(match.group(1))
    elif parsed.hostname in {"soitec.com", "www.soitec.com"} and "/press-releases/content/" in parsed.path:
        patterns = [r'<div[^>]*class=["\'][^"\']*\btext-gray-400\b[^"\']*["\'][^>]*>\s*<span>\s*([A-Za-z]+ \d{1,2}, 20\d{2})\s*</s(?:pan|oan)>']
    elif parsed.hostname in {"www.mycronic.com", "mycronic.com"} and parsed.path.startswith("/news-events/our-press-releases/"):
        patterns = [r'<div[^>]*class=["\']c-listing-item__meta-info-item["\'][^>]*>\s*<svg\b[^>]*>.*?calendar-day.*?</svg>\s*(\d{1,2} [A-Z]+ 20\d{2})\s*</div>']
    elif parsed.hostname in {"www.suss.com", "suss.com"} and parsed.path.startswith("/en/news/"):
        headers = _publication_region(body, 'header', 'article-header')
        if len(headers) == 1 and re.search(r'<h1\b', headers[0]):
            matches = re.findall(r'<p[^>]*class=["\']mb-2["\'][^>]*>\s*([A-Za-z]+ \d{1,2}, 20\d{2} \d{2}:\d{2}:\d{2})\s*</p>', headers[0])
            if len(matches) == 1:
                return _date_only(matches[0])
        match = re.search(r'(\d{2}\.\d{2}\.20\d{2}) / \d{2}:\d{2} CET/CEST\s*<br\s*/?>\s*The issuer is solely responsible', body)
        if match:
            return datetime.strptime(match.group(1), "%d.%m.%Y").date().isoformat()
    elif parsed.hostname in {"www.ntt-innovative-devices.com", "www.ntt-id.com"} and re.search(r"/en/news/20\d{2}/", parsed.path):
        patterns = [r'<span[^>]*class=["\']text_s["\'][^>]*>([^<]+)</span>']
    elif parsed.hostname == "abc.xyz" and "/news-details/" in parsed.path:
        patterns = [r'<span[^>]*class=["\']evergreen-news-date-text["\'][^>]*>([^<]+)</span>']
    elif parsed.hostname == "www.aseglobal.com" and parsed.path.startswith("/press-room/"):
        patterns = [r'<div[^>]*class=["\']blog-mini-time["\'][^>]*>([^<]+)</div>']
    elif parsed.hostname == "www.semtech.com" and parsed.path.startswith("/company/press/"):
        for paragraph in paragraphs:
            match = re.match(r"CAMARILLO, Calif\.,\s*([A-Za-z]+)\.?\s+(\d{1,2}, 20\d{2})", paragraph)
            if match:
                return _date_only(match.group(1) + " " + match.group(2))
    elif parsed.hostname in {'www.sourcephotonics.com', 'sourcephotonics.com'} and parsed.path.startswith('/news/'):
        return _sourcephotonics_publication_date(body, url)
    elif parsed.hostname in {'www.te.com', 'te.com'} and re.fullmatch(r'/en/about-te/news-center/[^/]+\.html', parsed.path):
        regions = _publication_region(body, 'div', 'published-date')
        if len(regions) == 1 and re.search(r'<h4[^>]*>\s*Published\s*</h4>', regions[0]):
            dates = re.findall(r'<p[^>]*>\s*(\d{2}/\d{2}/\d{2})\s*</p>', regions[0])
            if len(dates) == 1:
                return datetime.strptime(dates[0], '%m/%d/%y').date().isoformat()
    elif parsed.hostname == "www.aixtron.com" and "/press/press-releases/" in parsed.path:
        german = re.search(r'<p[^>]*>\s*(\d{1,2})\.\s*([A-Za-zÄä]+)\s+(20\d{2})\s*\|[^<]+</p>\s*<h1\b', body)
        if german:
            months = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6, "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12}
            if german.group(2) in months:
                return date(int(german.group(3)), months[german.group(2)], int(german.group(1))).isoformat()
        for paragraph in paragraphs:
            match = re.match(r"Herzogenrath, Germany,\s*([A-Za-z]+ \d{1,2}, 20\d{2})", paragraph)
            if match:
                return _date_only(match.group(1))
    for pattern in patterns:
        match = re.search(pattern, body, re.I | re.S)
        if match:
            return _date_only(match.group(1))
    return ""


def parse_html_item(body: str, url: str, fallback_title: str = "") -> dict[str, Any]:
    parser = _HTML(url)
    parser.feed(body)
    parser.close()
    parser._finalize()
    canonical = parser.canonical or url
    title = (
        parser.meta.get("og:title") or parser.meta.get("twitter:title")
        or parser.meta.get("h1") or fallback_title or parser.meta.get("title") or ""
    )
    published = (_site_publication_date(body, canonical, parser.paragraphs)
                 if urlparse(canonical).hostname in {'www.te.com', 'te.com'} else '')
    for key, value in parser.meta.items():
        if published:
            break
        if key in DATE_KEYS:
            published = _date_only(value)
            if published:
                break
    if not published:
        # <time> 一律先过行情/更新 class 排除：时间精度不证明归属，
        # 带时刻的 stock-update 类时间戳同样不得当作发布日期。
        for value, class_value in parser.time_values:
            if MARKER_CLASS_HINT.search(class_value):
                continue
            found = _date_only(value)
            if found:
                published = found
                break
    if not published:
        published = _json_ld_date(parser.json_ld, canonical, title)
    if (not published and urlparse(canonical).hostname in {"openlightphotonics.com", "www.openlightphotonics.com"}
            and re.fullmatch(r"/newsroom/[^/]+/?", urlparse(canonical).path)):
        bound_dates = []
        for block in parser.json_ld:
            try:
                payload = json.loads(block)
            except ValueError:
                continue
            for node, _primary in _collect_ld_nodes(payload):
                locators = [node.get(key) for key in ('url', 'mainEntityOfPage') if node.get(key)]
                locators = [value.get('@id') or value.get('url') if isinstance(value, dict) else value for value in locators]
                if (_node_types(node) == {"website"} and _title_binds(str(node.get("headline", "")), parser.meta.get('h1') or title)
                        and locators and all(_url_binds(value, canonical) for value in locators)):
                    bound_dates.append(_date_only(str(node["datePublished"])))
        if len(bound_dates) == 1:
            published = bound_dates[0]
    if not published:
        published = _json_field_date(body, canonical, title)
    if not published:
        published = next((found for found in map(_date_only, parser.date_values) if found), "")
    if not published:
        published = _dateline_date(parser.paragraphs)
    if not published:
        published = _site_publication_date(body, canonical, parser.paragraphs)
    if (urlparse(canonical).hostname in {'www.sourcephotonics.com', 'sourcephotonics.com'}
            and urlparse(canonical).path.startswith('/news/')):
        # A short dateline must not bypass disagreement with the release-time line.
        published = _sourcephotonics_publication_date(body, canonical)
    # Delta official numeric press pages contain their release body in one
    # inline srcdoc iframe. Decode attributes with HTMLParser (no remote iframe
    # fetching); reject ambiguous bodies/dates instead of reading navigation.
    if (urlparse(url).hostname == "www.deltaww.com"
            and re.fullmatch(r"/en-US/press/\d+/?", urlparse(url).path)):
        class DeltaBody(HTMLParser):
            def __init__(self):
                super().__init__()
                self.bodies = []
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if tag == "iframe" and values.get("srcdoc"):
                    self.bodies.append(values["srcdoc"])
        delta = DeltaBody()
        delta.feed(body)
        dates = re.findall(r'<span\s+class=["\']empty:hidden["\'][^>]*>\s*(\d{2}/\d{2}/\d{4})\s*</span>', body)
        if len(delta.bodies) == 1 and len(dates) == 1 and parser.meta.get("h1"):
            release = _HTML(url)
            release.feed(delta.bodies[0])
            release.close()
            release._finalize()
            parser.paragraphs = release.paragraphs
            published = datetime.strptime(dates[0], "%m/%d/%Y").date().isoformat()
        else:
            parser.paragraphs = []
            published = ""
    # 注意：不做全文首个日期兜底——正文首个日期可能是版权年份、其他文章或作者注册日期。
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


def discover_article_links(body: str, url: str, limit: int = 20, path_pattern: str = "") -> list[tuple[str, str]]:
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
        if path_pattern and not re.search(path_pattern, parsed.path):
            continue
        if normalized in seen or (not path_pattern and (len(title) < 8 or not ARTICLE_HINT.search(parsed.path + " " + title))):
            continue
        has_article_id_query = False
        if "?" in normalized:
            query = urlparse(normalized).query
            if ARTICLE_QUERY_EXCLUDE.search(query):
                continue  # 分页/筛选 query 不是文章
            has_article_id_query = bool(
                re.search(r"(?:^|&)(?:articleid|id|p|story|post)=\w", query, re.I)
            )
            if not has_article_id_query:
                continue  # 无文章 ID 的裸 query 一并拒绝
        # Q4 平台真实文章路径（如 /news-details/2026/.../default.aspx）优先于
        # default.aspx 排除；带文章 ID query 的链接视为文章；FAQ/分页导航仍拒绝。
        path_excluded = bool(ARTICLE_PATH_EXCLUDE.search(parsed.path)) \
            and "news-details" not in parsed.path.lower() \
            and not has_article_id_query
        if (path_excluded or ARTICLE_TITLE_EXCLUDE.search(title)
                or (not path_pattern and re.search(r"/(?:investor-relations|financial-information)/", parsed.path, re.I))):
            continue
        seen.add(normalized)
        found.append((normalized, title))
        if len(found) >= limit:
            break
    return found


class _DatedListingHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': '', 'attrs': {}, 'children': [], 'text': []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': [], 'text': []}
        self.stack[-1]['children'].append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]['tag'] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node['text'].append(data)


def discover_dated_article_links(body, url):
    """Return card-bound dates; None means this URL has no supported template."""
    origin = urlparse(url)
    host, path = origin.hostname, origin.path.rstrip('/')
    if host == 'www.asmpt.com' and path == '/en/investor-relations/news-events':
        site, pattern = 'asmpt', r'/en/investor-relations/news-events/[^/]+/?'
    elif host == 'www.accton.com' and path == '/express':
        site, pattern = 'accton', r'/[^/]+/?'
    elif host == 'www.semtech.com' and path == '/company/press':
        site, pattern = 'semtech', r'/company/press/(?!P\d+/?$)[^/]+'
    else:
        return None
    parser = _DatedListingHTML()
    parser.feed(body)

    def walk(node):
        yield node
        for child in node['children']:
            yield from walk(child)

    def has(node, cls):
        return cls in node['attrs'].get('class', '').split()

    def text(node):
        return ' '.join(' '.join(node['text']).split())

    def target(node):
        try:
            link = urljoin(url, node['attrs'].get('href', ''))
            parsed = urlparse(link)
            if (node['tag'] == 'a' and parsed.scheme in {'https', 'http'}
                    and parsed.hostname == host and re.fullmatch(pattern, parsed.path)
                    and (site != 'accton' or has(node, 'story-link'))
                    and not parsed.query and not parsed.fragment):
                return link.rstrip('/')
        except ValueError:
            pass
        return ''

    def date_value(value, formats):
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date().isoformat()
            except ValueError:
                pass
        return ''

    records = {}
    def add(card, heading, published):
        anchors = [n for n in walk(heading) if target(n)]
        if not anchors:
            anchors = [n for n in walk(card) if target(n)]
        if not anchors:
            return
        link = target(anchors[0])
        title = text(heading) or anchors[0]['attrs'].get('title', '') or text(anchors[0])
        if title:
            records[link] = {'url': link, 'title': title, 'published_at': published}

    if site == 'accton':
        for timeline in (n for n in walk(parser.root) if has(n, 'ctl-timeline')):
            year = ''
            for node in walk(timeline):
                if has(node, 'ctl-year-container'):
                    marker = node['attrs'].get('data-section-title', '')
                    year = marker if re.fullmatch(r'\d{4}', marker) else ''
                if has(node, 'ctl-story'):
                    children = list(walk(node))
                    markers = [n for n in children if has(n, 'ctl-year-container')]
                    if markers:
                        marker = markers[0]['attrs'].get('data-section-title', '')
                        year = marker if re.fullmatch(r'\d{4}', marker) else ''
                    headings = [n for n in children if has(n, 'ctl-title')]
                    dates = [n for n in children if has(n, 'story-date')]
                    published = date_value(text(dates[0]) + ' ' + year, ('%b %d %Y',)) if len(dates) == 1 and year else ''
                    if headings:
                        add(node, headings[0], published)
    else:
        for node in walk(parser.root):
            if not has(node, 'card' if site == 'asmpt' else 'row'):
                continue
            children = list(walk(node))
            headings = [n for n in children if has(n, 'card-title')] if site == 'asmpt' else [n for n in children if n['tag'] == 'h3']
            dates = [n for n in children if has(n, 'text-muted' if site == 'asmpt' else 'entry-meta')]
            # A surrounding layout row cannot donate its first date to another link.
            if len(headings) != 1:
                continue
            raw = text(dates[0]) if len(dates) == 1 else ''
            published = date_value(raw.split('|')[0], ('%Y-%m-%d',)) if site == 'asmpt' else date_value(raw, ('%B %d, %Y', '%b %d, %Y'))
            add(node, headings[0], published)
    # A real detail URL outside cards is still an unknown-date candidate.
    for node in walk(parser.root):
        link = target(node)
        title = text(node) or node['attrs'].get('title', '')
        if link and title and link not in records:
            records[link] = {'url': link, 'title': title, 'published_at': ''}
    return list(records.values())


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



def _publisher_press_cards(body: str, url: str) -> list[tuple[str, str]] | None:
    """Lumilens cards mix media and blogs: only explicit Press release cards."""
    if urlparse(url).hostname == "www.senko.com" and urlparse(url).path.rstrip("/") == "/news":
        links = []
        for card in re.split(r'<div\s+class=["\']split-cont2[^"\']*["\'][^>]*>', body)[1:]:
            aside = re.search(r'<div\s+class=["\']aside["\'][^>]*>(.*?)</div>', card, re.S)
            if not aside:
                continue
            heading = re.search(r'<h3[^>]*>(.*?)</h3>', aside.group(1), re.S)
            if not heading:
                continue
            parser = _HTML(url)
            parser.feed(aside.group(1))
            for link, _label in parser.links:
                if (urlparse(link).hostname == "www.senko.com"
                        and re.fullmatch(r"/[^/]+/?", urlparse(link).path)):
                    links.append((link.rstrip("/"), _strip_html(heading.group(1))))
                    break
        return links
    if urlparse(url).hostname != "lumilens.com":
        return None
    starts = list(re.finditer(r'<div\b[^>]*class=["\'][^"\']*\bnews-content\b[^"\']*["\'][^>]*>', body, re.I))
    links = []
    for index, match in enumerate(starts):
        card = body[match.start():starts[index + 1].start() if index + 1 < len(starts) else len(body)]
        if not re.search(r'class=["\']refrence-text["\'][^>]*>\s*Press release\s*<', card, re.I):
            continue
        parser = _HTML(url)
        parser.feed(card)
        heading = re.search(r'<h3\b[^>]*>(.*?)</h3>', card, re.I | re.S)
        for link, title in parser.links:
            if urlparse(link).hostname == "lumilens.com" and urlparse(link).path.startswith("/news-insights/"):
                links.append((link, _strip_html(heading.group(1)) if heading else title))
                break
    return links


def _cisco_releases(body: str, url: str) -> list[dict[str, str]]:
    """Decode only the official pressRelease component, never execute scripts."""
    if urlparse(url).hostname != "newsroom.cisco.com":
        return []
    for script in re.findall(r"<script\b[^>]*>(.*?)</script>", body, re.I | re.S):
        if not re.search(r'getElementById\([\"\x27]pressRelease[\"\x27]\)', script):
            continue
        match = re.search(r'JSON\.parse\(("(?:\\.|[^"\\])*")\)', script)
        if not match:
            continue
        literal = re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\1", match.group(1))
        records = json.loads(json.loads(literal))
        if not isinstance(records, list):
            raise ValueError("Cisco pressRelease data is not a list")
        items = []
        for record in records:
            link = urljoin(url, str(record.get("path", "")))
            if urlparse(link).hostname != "newsroom.cisco.com" or "/a/y" not in urlparse(link).path:
                continue
            items.append({"url": link, "title": str(record.get("title", "")),
                          "published_at": _date_only(str(record.get("releaseDate", "")))})
        return items
    return []


def _q4_items(payload: dict[str, Any], url: str,
              article_failures: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    records = payload["GetPressReleaseListResult"]
    if not isinstance(records, list):
        raise ValueError("Q4 press release data is not a list")
    items = []
    for index, record in enumerate(records):
        link = url
        try:
            if not isinstance(record, dict):
                raise ValueError("Q4 press release record is not an object")
            raw_link = record.get("LinkToDetailPage")
            if not isinstance(raw_link, str) or not raw_link.strip():
                raise ValueError("Q4 press release has no article URL")
            link = urljoin(url, raw_link)
            parsed = urlparse(link)
            if parsed.scheme not in {"http", "https"} or parsed.netloc != urlparse(url).netloc:
                raise ValueError("Q4 press release has no same-origin article URL")
            if re.search(r"\.(?:pdf|zip|docx?)$", parsed.path, re.I):
                raise ValueError("Q4 release points to an unsupported attachment")
            item = parse_html_item(str(record.get("Body") or ""), link, str(record.get("Headline", "")))
            # Q4 explicitly dates each release; numeric US dates are local here.
            stamp = str(record.get("PressReleaseDate", ""))
            try:
                item["published_at"] = datetime.strptime(stamp, "%m/%d/%Y %H:%M:%S").date().isoformat()
            except ValueError:
                item["published_at"] = _date_only(stamp)
            items.append(item)
        except (ValueError, TypeError) as exc:
            if article_failures is None:
                raise
            article_failures.append({"url": link, "detail": f"invalid Q4 item at index {index}: {exc}"})
    return items


class EndpointBudgetExceeded(TimeoutError):
    pass


class HttpFetcher:
    """Fetch public entity endpoints and normalize them to fixture-shaped items."""

    fetch_mode = "http"

    def __init__(self, run_date: str, timeout: float = 15, lookback_days: int = 14,
                 max_items: int = 20, endpoint_budget: float = 60) -> None:
        if not all(math.isfinite(value) and value > 0 for value in (timeout, endpoint_budget)):
            raise ValueError("request timeout and endpoint budget must be positive")
        self.run_date = date.fromisoformat(run_date)
        self.timeout = timeout
        self.lookback_days = lookback_days
        self.max_items = max_items
        self.endpoint_budget = endpoint_budget
        self._deadline: float | None = None

    def _remaining(self) -> float:
        remaining = self.timeout if self._deadline is None else self._deadline - time.monotonic()
        if remaining <= 0:
            raise EndpointBudgetExceeded("endpoint time budget exhausted")
        return remaining

    @contextmanager
    def _request_timer(self, *, parsing: bool = False):
        """Bound DNS/headers as well as reads for the macOS/Linux CLI main thread.

        Library callers on other threads retain socket timeouts and deadline
        checks. Never overwrite another caller's active alarm.
        """
        can_arm = hasattr(signal, "setitimer") and threading.current_thread() is threading.main_thread()
        if not can_arm or signal.getitimer(signal.ITIMER_REAL)[0]:
            yield
            return
        previous = signal.getsignal(signal.SIGALRM)
        def expired(_signum, _frame):
            if parsing:
                raise EndpointBudgetExceeded("endpoint time budget exhausted during parsing")
            self._remaining()  # a deadline exception must not enter retry
            raise TimeoutError("public GET request timeout")
        signal.signal(signal.SIGALRM, expired)
        try:
            signal.setitimer(signal.ITIMER_REAL, self._remaining() if parsing else min(self.timeout, self._remaining()))
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def _parse(self, function, *args):
        self._remaining()
        with self._request_timer(parsing=True):
            result = function(*args)
        self._remaining()
        return result

    def _request(self, url: str) -> tuple[str, str, str]:
        for attempt in range(2):
            self._remaining()
            try:
                with self._request_timer():
                    return self._get(url)
            except EndpointBudgetExceeded:
                raise
            except Exception as exc:
                reason = exc.reason if isinstance(exc, URLError) else exc
                transient = isinstance(reason, (TimeoutError, ConnectionError, ssl.SSLEOFError))
                if isinstance(exc, HTTPError):
                    transient = exc.code in {408, 502, 503, 504}
                    exc.close()
                if attempt or not transient:
                    raise
        raise AssertionError("unreachable")

    def _get(self, url: str) -> tuple[str, str, str]:
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; calls-daily-discovery/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/json,application/rss+xml,application/atom+xml",
        })
        with urlopen(request, timeout=min(self.timeout, self._remaining())) as response:
            chunks: list[bytes] = []
            size = 0
            while size < 8_000_000:
                self._remaining()
                chunk = response.read1(min(64_000, 8_000_000 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            if size == 8_000_000:
                raise ValueError("public response exceeds 8 MB limit; refusing truncated content")
            body = b"".join(chunks)
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
        self._deadline = time.monotonic() + self.endpoint_budget
        if getattr(endpoint, "unsupported_listing", False):
            # 已证实 JS 渲染、无法静态采集的端点：显式 unsupported，不冒充健康零增量。
            return HttpFetchResult(
                endpoint.endpoint_id, (),
                "unsupported_listing: configured endpoint is a verified JavaScript-rendered "
                "listing; not statically collectable",
            )
        try:
            body, content_type, final_url = self._request(endpoint.url)
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public GET failed: {type(exc).__name__}: {exc}")
        if urlparse(final_url).hostname == "www.sivers-semiconductors.com" and "/wp-json/sivers/v1/news-press" in urlparse(final_url).path:
            try:
                envelope = self._parse(json.loads, body)
                if envelope.get("success") is not True or not isinstance(envelope.get("html"), str):
                    raise ValueError("invalid Sivers press-list response")
                body, content_type = envelope["html"], "text/html"
            except (ValueError, AttributeError, EndpointBudgetExceeded) as exc:
                return HttpFetchResult(endpoint.endpoint_id, (), f"invalid Sivers listing: {exc}")
        if (urlparse(final_url).hostname == "www.mitsubishielectric.com"
                and urlparse(final_url).path == "/global/common/mel25/news-data/gws-news/global/www/en/news-article.json"):
            try:
                records = self._parse(json.loads, body)["news"]
                if not isinstance(records, list) or not records:
                    raise ValueError("missing Mitsubishi release records")
                if any(not isinstance(row, dict) or not isinstance(row.get("url"), str)
                       or not isinstance(row.get("title"), str) for row in records):
                    raise ValueError("malformed Mitsubishi release record")
                body = "".join('<a href="' + escape(row["url"], quote=True) + '">' + escape(row["title"]) + '</a>' for row in records)
                content_type = "text/html"
            except (ValueError, KeyError, TypeError, EndpointBudgetExceeded) as exc:
                return HttpFetchResult(endpoint.endpoint_id, (), f"invalid Mitsubishi listing: {exc}")
        stripped = body.lstrip()
        article_failures: list[dict[str, str]] = []
        items: list[dict[str, Any]] = []
        try:
            if content_type == "application/json" or stripped.startswith(("{", "[")):
                payload = self._parse(json.loads, body)
                if isinstance(payload, dict) and "GetPressReleaseListResult" in payload:
                    items = self._parse(_q4_items, payload, final_url, article_failures)
                    for item in items:
                        if not item["paragraphs"]:
                            article_failures.append({"url": item["url"], "detail": "Q4 release has no usable article body"})
                    items = [item for item in items if item["paragraphs"]]
                else:
                    if isinstance(payload, dict) and "items" not in payload:
                        raise ValueError("unsupported JSON listing format (no items array)")
                    raw_items = payload["items"] if isinstance(payload, dict) else payload
                    if not isinstance(raw_items, list):
                        raise ValueError("JSON items must be a list")
                    items = []
                    for index, item in enumerate(raw_items):
                        if isinstance(item, dict):
                            items.append(dict(item))
                        else:
                            article_failures.append({"url": final_url, "detail": f"invalid JSON item at index {index}: expected object"})
            elif "xml" in content_type or stripped.startswith("<?xml") or "<rss" in stripped[:200].lower():
                items = self._parse(parse_feed, body, final_url)
            else:
                items = []
                press_cards = self._parse(_publisher_press_cards, body, final_url)
                embedded = self._parse(_cisco_releases, body, final_url)
                embedded_dates = {item["url"]: item["published_at"] for item in embedded}
                dated = self._parse(discover_dated_article_links, body, final_url)
                if dated is not None:
                    dated = [row for row in dated if not endpoint.article_path_pattern
                             or re.search(endpoint.article_path_pattern, urlparse(row['url']).path, re.I)]
                    eligible = [row for row in dated if self._in_window(row)]
                    if dated and not eligible:
                        return HttpFetchResult(endpoint.endpoint_id, (), '')
                    article_links = [(row['url'], row['title']) for row in eligible[:self.max_items]]
                    embedded_dates.update({row['url']: row['published_at'] for row in dated})
                else:
                    article_links = ([(item["url"], item["title"]) for item in embedded[:self.max_items]]
                                     if embedded else self._parse(discover_article_links, body, final_url, self.max_items, endpoint.article_path_pattern))
                    if press_cards is not None:
                        article_links = press_cards[:self.max_items]
                page = self._parse(parse_html_item, body, final_url)
                # 页面自身只有在没有其他文章链接时才可入候选（单篇文章页形状）；
                # 列表页的页面级 meta 日期不属于任何一篇文章，不得把列表页当文章。
                if not article_links and not endpoint.article_path_pattern and page["published_at"] and page["paragraphs"]:
                    items.append(page)
                for link, title in article_links:
                    if endpoint.endpoint_kind != "official_blog" \
                            and "/blog/" in urlparse(link).path.lower() \
                            and not endpoint.allow_blog_release_path:
                        # 博客文章只能来自声明的 official_blog 端点；
                        # 从新闻/IR 列表混入的博客不得冒充官方公告的披露类型。
                        continue
                    try:
                        article_body, article_type, article_url = self._request(link)
                    except EndpointBudgetExceeded as exc:
                        article_failures.append({"url": link, "detail": str(exc) + "; remaining articles not fetched"})
                        return HttpFetchResult(endpoint.endpoint_id, tuple(item for item in items if self._in_window(item)), "", tuple(article_failures))
                    except Exception as exc:
                        if isinstance(exc, HTTPError) and exc.code == 429:
                            retry_after = exc.headers.get('Retry-After', '') if exc.headers else ''
                            article_failures.append({"url": link,
                                "detail": "article HTTP 429; remaining articles not requested" + (f"; Retry-After={retry_after}" if retry_after else "")})
                            return HttpFetchResult(endpoint.endpoint_id, tuple(item for item in items if self._in_window(item)), "", tuple(article_failures))
                        article_failures.append({
                            "url": link,
                            "detail": f"article GET failed: {type(exc).__name__}: {exc}",
                        })
                        continue
                    if "json" in article_type:
                        continue
                    item = self._parse(parse_html_item, article_body, article_url, title)
                    if item["url"].rstrip("/") == link.rstrip("/"):
                        card_date = embedded_dates.get(link, '')
                        if dated is not None and card_date:
                            # The site's posting date and the release dateline may
                            # differ. Keep both; the daily window uses the former.
                            date_note = f"页面发布日期 {card_date} 取自官网同一文章 URL 的列表卡片"
                            if item['published_at'] and item['published_at'] != card_date:
                                item['detail_date_observed'] = item['published_at']
                                date_note += f"；详情另有日期 {item['published_at']}，不以页面发布日推定事件发生日"
                            item['published_at'] = card_date
                            item['published_at_basis'] = 'official_listing_card'
                            item['note'] = '；'.join(filter(None, (item.get('note', ''), date_note)))
                        elif not item['published_at']:
                            item['published_at'] = card_date
                    if item["paragraphs"]:
                        items.append(item)
                    else:
                        article_failures.append({
                            "url": link,
                            "detail": "article fetched but no usable paragraphs extracted",
                        })
                if article_links and not items and not article_failures:
                    return HttpFetchResult(endpoint.endpoint_id, (),
                        "unsupported_listing: no article matches the configured disclosure type")
                if not items and not article_links:
                    # 结构性零：静态 HTML 无任何可解析文章链接且页面自身不是日期化文章。
                    # 如实报 unsupported，不把 JS 渲染的空列表冒充为成功的零增量。
                    return HttpFetchResult(
                        endpoint.endpoint_id, (),
                        "unsupported_listing: no parseable article link or dated page item "
                        "in static HTML; listing may be JavaScript-rendered",
                    )
            self._remaining()
            filtered = tuple(item for item in items if self._in_window(item))
            return HttpFetchResult(endpoint.endpoint_id, filtered, "", tuple(article_failures))
        except EndpointBudgetExceeded as exc:
            article_failures.append({"url": final_url, "detail": str(exc) + "; remaining parsing skipped"})
            return HttpFetchResult(endpoint.endpoint_id, tuple(item for item in items if self._in_window(item)), "", tuple(article_failures))
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public response parse failed: {type(exc).__name__}: {exc}")
