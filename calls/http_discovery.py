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
    # 端点级失败放在 failure；单篇文章的详情抓取/解析失败在这里逐条追踪，
    # 使部分成功不会把端点结果伪装成完全无错。
    article_failures: tuple[dict[str, str], ...] = ()


ARTICLE_HINT = re.compile(
    r"(?:news|press|release|article|blog|filing|financial|investor|node|detail|20\d{2})",
    re.I,
)
# 导航/索引/辅助页与附件，不得因同域被当作文章链接。
ARTICLE_PATH_EXCLUDE = re.compile(
    r"(?:^|/)(?:faq|faqs|index|overview|search|events?|webinars?|webcasts?|presentations?"
    r"|tag|category|privacy|terms|conditions|contact|careers|login|signin|subscribe|newsletters?"
    r"|disclaimer|share-price|news-events|annual-reports|quarterly-results)"
    r"(?:\.aspx?|\.html?)?/?$"
    r"|(?:^|/)(?:sec-filings|email-alerts|investor-faqs|financial-information|financial-reports"
    r"|rss-feeds|analyst-reports|analyst-relations|filter-results|articles|blogs|company|artificial-intelligence"
    r"|people|executives|podcasts|videos|featured-blogs|security|networking|innovation"
    r"|collaboration|observability)(?:\.aspx?|\.html?)?/?$"
    r"|(?:^|/)(?:press-releases|news-releases|financial-news-releases|media|investors?"
    r"|blog|newsroom|news|regulatory-news)(?:\.aspx?|\.html?)?/?$"
    r"|/(?:investor-relations|financial-information)/"
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
    r"|view all|analyst relations|aim rule|advisers|financial calendar|results, reports"
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
            self.canonical = urljoin(self.base_url, values.get("href", ""))
        elif tag == "time" and values.get("datetime"):
            self.time_values.append((values["datetime"], values.get("class", "")))
        # 发布日期常出现在 class 含 date 的短元素中；只有可信的日期类 token 才收
        # （如 "Type--Date"、"blog-post-header2_date"），行情/更新时间类 class 不收。
        if not self._date_capture_tag and not values.get("datetime") \
                and _trusted_date_class(values.get("class", "")):
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
            if text:
                self.links.append((urljoin(self.base_url, self._href), text))
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
    """返回包含 pos 的最内层 JSON 对象文本（字符串感知的括号平衡，
    忽略字符串字面量内的引号与花括号），用于把日期绑定到其所属节点。"""
    depth = 0
    in_string = False
    start = -1
    index = pos
    while index >= 0:
        char = body[index]
        if in_string:
            if char == '"' and not _escaped_at(body, index):
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "}":
            depth += 1
        elif char == "{":
            if depth == 0:
                start = index
                break
            depth -= 1
        index -= 1
    if start < 0:
        return ""
    level = 0
    in_string = False
    for index in range(start, min(len(body), start + 200_000)):
        char = body[index]
        if in_string:
            if char == '"' and not _escaped_at(body, index):
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            level += 1
        elif char == "}":
            level -= 1
            if level == 0:
                return body[start:index + 1]
    return body[start:start + 2000]


def _escaped_at(body: str, index: int) -> bool:
    """body[index] 处的引号是否被反斜杠转义（处理连续反斜杠的奇偶）。"""
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and body[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


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
    published = ""
    for key, value in parser.meta.items():
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
    if not published:
        published = _json_field_date(body, canonical, title)
    if not published:
        published = next((found for found in map(_date_only, parser.date_values) if found), "")
    if not published:
        published = _dateline_date(parser.paragraphs)
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
        if path_excluded or ARTICLE_TITLE_EXCLUDE.search(title):
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
        if getattr(endpoint, "unsupported_listing", False):
            # 已证实 JS 渲染、无法静态采集的端点：显式 unsupported，不冒充健康零增量。
            return HttpFetchResult(
                endpoint.endpoint_id, (),
                "unsupported_listing: configured endpoint is a verified JavaScript-rendered "
                "listing; not statically collectable",
            )
        try:
            body, content_type, final_url = self._get(endpoint.url)
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public GET failed: {type(exc).__name__}: {exc}")
        stripped = body.lstrip()
        article_failures: list[dict[str, str]] = []
        try:
            if content_type == "application/json" or stripped.startswith(("{", "[")):
                payload = json.loads(body)
                raw_items = payload.get("items", ()) if isinstance(payload, dict) else payload
                items = [dict(item) for item in raw_items if isinstance(item, dict)]
            elif "xml" in content_type or stripped.startswith("<?xml") or "<rss" in stripped[:200].lower():
                items = parse_feed(body, final_url)
            else:
                items = []
                article_links = discover_article_links(body, final_url, self.max_items)
                page = parse_html_item(body, final_url)
                # 页面自身只有在没有其他文章链接时才可入候选（单篇文章页形状）；
                # 列表页的页面级 meta 日期不属于任何一篇文章，不得把列表页当文章。
                if not article_links and page["published_at"] and page["paragraphs"]:
                    items.append(page)
                for link, title in article_links:
                    if endpoint.endpoint_kind != "official_blog" \
                            and "/blog/" in urlparse(link).path.lower():
                        # 博客文章只能来自声明的 official_blog 端点；
                        # 从新闻/IR 列表混入的博客不得冒充官方公告的披露类型。
                        continue
                    try:
                        article_body, article_type, article_url = self._get(link)
                    except Exception as exc:
                        article_failures.append({
                            "url": link,
                            "detail": f"article GET failed: {type(exc).__name__}: {exc}",
                        })
                        continue
                    if "json" in article_type:
                        continue
                    item = parse_html_item(article_body, article_url, title)
                    if item["paragraphs"]:
                        items.append(item)
                    else:
                        article_failures.append({
                            "url": link,
                            "detail": "article fetched but no usable paragraphs extracted",
                        })
                if not items and not article_links:
                    # 结构性零：静态 HTML 无任何可解析文章链接且页面自身不是日期化文章。
                    # 如实报 unsupported，不把 JS 渲染的空列表冒充为成功的零增量。
                    return HttpFetchResult(
                        endpoint.endpoint_id, (),
                        "unsupported_listing: no parseable article link or dated page item "
                        "in static HTML; listing may be JavaScript-rendered",
                    )
            filtered = tuple(item for item in items if self._in_window(item))
            return HttpFetchResult(endpoint.endpoint_id, filtered, "", tuple(article_failures))
        except Exception as exc:
            return HttpFetchResult(endpoint.endpoint_id, (), f"public response parse failed: {type(exc).__name__}: {exc}")
