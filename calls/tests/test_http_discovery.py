from __future__ import annotations

import json
import unittest

from calls.daily_discovery import Endpoint
from calls.http_discovery import HttpFetcher, discover_article_links, parse_feed, parse_html_item


class HttpDiscoveryTest(unittest.TestCase):
    def test_html_article_keeps_canonical_date_title_and_anchors(self):
        body = """
        <html><head><link rel="canonical" href="/news/release-1">
        <meta property="og:title" content="First 1.6T shipment">
        <meta property="article:published_time" content="2026-09-01T08:00:00Z"></head>
        <body><p>Lumentum <a href="/products/1.6t">began shipping</a> its 1.6T modules this quarter.</p></body></html>
        """
        item = parse_html_item(body, "https://example.com/news")
        self.assertEqual(item["url"], "https://example.com/news/release-1")
        self.assertEqual(item["published_at"], "2026-09-01")
        self.assertEqual(item["title"], "First 1.6T shipment")
        self.assertEqual(item["paragraphs"][0]["anchor"], "p1")
        self.assertIn("began shipping", item["paragraphs"][0]["text"])

    def test_listing_only_follows_same_origin_article_links(self):
        body = """
        <a href="/press-releases/release-1">Company announces first shipment</a>
        <a href="https://other.example/news/release-2">External syndicated report</a>
        <a href="/images/photo.jpg">Press release photo download</a>
        """
        self.assertEqual(
            discover_article_links(body, "https://example.com/press-releases"),
            [("https://example.com/press-releases/release-1", "Company announces first shipment")],
        )

    def test_nav_faq_alerts_and_index_links_are_excluded(self):
        # 形状取自 investor.lumentum.com / ir.macom.com / newsroom.cisco.com 实测导航。
        body = """
        <a href="/financial-news-releases/default.aspx">News Releases</a>
        <a href="/sec-filings/default.aspx">SEC Filings</a>
        <a href="/resources/investor-email-alerts/default.aspx">Investor Email Alerts</a>
        <a href="/resources/investor-faqs/default.aspx">Investor FAQs</a>
        <a href="/overview">Investor Relations Home</a>
        <a href="/financial-information">Financial Results</a>
        <a href="/en/us/filter-results.html?pt=newsroom:topic/security">Security</a>
        <a href="/en/us/index.html">The Newsroom</a>
        <a href="/news-releases/news-release-details/macom-reports-fiscal-q3-2026-results">MACOM Reports Fiscal Q3 2026 Results</a>
        """
        self.assertEqual(
            discover_article_links(body, "https://example.com/news-releases"),
            [(
                "https://example.com/news-releases/news-release-details/macom-reports-fiscal-q3-2026-results",
                "MACOM Reports Fiscal Q3 2026 Results",
            )],
        )

    def test_share_price_time_widget_is_not_treated_as_publish_date(self):
        # IQE 实测反例：页面挂件 <time datetime> 是当日股价时间，不是文章发布日期；
        # 官方电头 "Cardiff, UK 28 May 2026" 才是发布日期。
        body = """
        <html><head><meta property="og:title" content="Completion of Fundraising"></head>
        <body>
        <span class="share-price"><time datetime="2026-09-04" class="share-price__text-time">22:06 GMT</time></span>
        <h1>Completion of Fundraising</h1>
        <p>THIS ANNOUNCEMENT AND THE INFORMATION CONTAINED HEREIN IS RESTRICTED AND IS NOT FOR RELEASE IN THE UNITED STATES.</p>
        <p>Cardiff, UK 28 May 2026</p>
        <p>IQE plc today announced the successful completion of its fundraising announced earlier.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://www.iqep.com/media/press-releases/2026/completion-of-fundraising/")
        self.assertEqual(item["published_at"], "2026-05-28")
        self.assertEqual(len(item["paragraphs"]), 3)

    def test_no_trusted_date_stays_empty_not_first_date_in_text(self):
        # 版权年份与正文叙述日期都不能冒充发布日期；无可信日期必须留空，
        # 由下游 invalid_item 显式拒收并报告。
        body = """
        <html><head><title>Investor Update</title></head><body>
        <h1>Investor Update</h1>
        <p>The board reviewed progress since the original announcement on 3 March 2026 and approved the plan.</p>
        <p>Additional context paragraphs follow here with more operational detail for readers.</p>
        <footer>© Example Corp 2026. All rights reserved.</footer>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/investor-update")
        self.assertEqual(item["published_at"], "")

    def test_embedded_json_field_date_beyond_first_20000_chars(self):
        # Lumentum 博客实测形状：Drupal 节点对象带 path.alias，与 canonical 路径
        # 等值（含语言前缀规范化）后才可用；field_date 位于正文 80041 字符附近。
        filler = "<p>" + "x" * 30000 + "</p>" * 3
        body = (
            '<html><body>' + filler
            + '<script>window.DATA={"node":{"path":{"alias":"/blog/backbone-example"},'
            + '"field_date":"2026-06-25","field_end_date":null}}}</script></body></html>'
        )
        item = parse_html_item(body, "https://www.lumentum.com/en/blog/backbone-example")
        self.assertEqual(item["published_at"], "2026-06-25")

    def test_unique_related_node_with_different_url_leaves_date_empty(self):
        # 唯一 field_date 出现也不得默认主文：所属对象 URL 与当前文章不同 → 留空。
        body = """
        <html><body>
        <script>window.DATA={"title":"Peer story","url":"https://example.com/news/peer-story","field_date":"2026-01-01"}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_short_url_prefix_node_is_not_bound(self):
        # URL 只能等值匹配：/news/main-story-extra 是另一篇文章，不得绑定 /news/main-story。
        body = """
        <html><body>
        <script>window.DATA={"title":"Longer story","url":"https://example.com/news/main-story-extra","field_date":"2026-02-02"}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_peer_object_with_main_title_but_own_url_is_not_bound(self):
        # 邻域/对象内出现主文标题但对象 URL 明示属于别节点：URL 不匹配禁止标题兜底。
        body = """
        <html><body>
        <script>window.DATA={"title":"Main story","url":"https://example.com/news/peer-story","field_date":"2026-03-03"}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_unrecognized_drupal_structure_leaves_date_empty(self):
        # 无法识别的 Drupal/嵌入结构（无任何自标识字段）：宁可留空报 invalid，不猜日期。
        body = """
        <html><body>
        <script>window.DATA={"node":{"field_date":"2026-06-25","field_end_date":null}}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://www.lumentum.com/en/blog/example")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_single_typed_primary_without_locators_is_accepted(self):
        # 基线允许：无定位字段的单一 typed primary 文章节点可接受。
        body = """
        <html><body><script type="application/ld+json">
        {"@type":"NewsArticle","datePublished":"2026-08-06T07:31:09-0400"}
        </script></body></html>
        """
        item = parse_html_item(body, "https://ir.example.com/news/main-story")
        self.assertEqual(item["published_at"], "2026-08-06")

    def test_jsonld_single_typed_node_with_mismatched_url_is_rejected(self):
        # 唯一 typed 节点但 URL 明示属于别处：不得因唯一性接受。
        body = """
        <html><body><script type="application/ld+json">
        {"@type":"NewsArticle","url":"https://example.com/news/peer-story","datePublished":"2026-08-06"}
        </script></body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_single_typed_node_binds_by_equal_title(self):
        # MACOM 实测形状：无 URL 字段、headline 与页面标题等值。
        body = """
        <html><head><meta property="og:title" content="MACOM Reports Fiscal Third Quarter 2026 Financial Results"></head>
        <body><script type="application/ld+json">
        {"@type":"NewsArticle","headline":"MACOM Reports Fiscal Third Quarter 2026 Financial Results","datePublished":"2026-08-06T07:31:09-0400"}
        </script></body></html>
        """
        item = parse_html_item(body, "https://ir.macom.com/news-releases/news-release-details/x")
        self.assertEqual(item["published_at"], "2026-08-06")

    def test_related_article_json_before_main_binds_by_canonical_url(self):
        # 相关文章节点在前、主节点在后的实测风险形状：只有唯一绑定到
        # 当前 canonical URL 的节点才可用。
        body = """
        <html><body>
        <script>window.RELATED=[{"title":"Peer story","url":"https://example.com/news/peer-story","field_date":"2026-01-01"}]</script>
        <script>window.MAIN={"title":"Main story","url":"https://example.com/news/main-story","field_date":"2026-06-25"}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "2026-06-25")

    def test_unbindable_multiple_json_nodes_leave_date_empty(self):
        # 多个 field_date 节点都无法归属当前文章：不得猜首个，必须留空（下游报 invalid）。
        body = """
        <html><body>
        <script>window.A=[{"title":"Other one","url":"https://example.com/news/other-1","field_date":"2026-01-01"}]</script>
        <script>window.B={"title":"Other two","url":"https://example.com/news/other-2","field_date":"2026-02-02"}</script>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_related_article_before_main_binds_by_url(self):
        # MACOM 实测形状：ld+json @graph 多节点，只认文章类型节点且必须唯一绑定。
        body = """
        <html><head><link rel="canonical" href="https://example.com/news/main-story"></head>
        <body><script type="application/ld+json">{"@graph":[
          {"@type":"NewsArticle","headline":"Peer story","url":"https://example.com/news/peer-story","datePublished":"2026-01-01"},
          {"@type":"Organization","name":"Example Corp"},
          {"@type":"NewsArticle","headline":"Main story","url":"https://example.com/news/main-story","datePublished":"2026-06-25T07:31:09-0400"}
        ]}</script></body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "2026-06-25")

    def test_jsonld_unbindable_article_nodes_leave_date_empty(self):
        body = """
        <html><body><script type="application/ld+json">{"@graph":[
          {"@type":"BlogPosting","headline":"Peer one","url":"https://example.com/news/peer-1","datePublished":"2026-01-01"},
          {"@type":"BlogPosting","headline":"Peer two","url":"https://example.com/news/peer-2","datePublished":"2026-02-02"}
        ]}</script></body></html>
        """
        item = parse_html_item(body, "https://example.com/news/main-story")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_author_node_date_is_not_treated_as_publish_date(self):
        # 作者/组织节点上的 datePublished 不得冒充文章发布日期。
        body = """
        <html><body><script type="application/ld+json">
        {"@type":"Person","name":"Jane Analyst","datePublished":"2026-01-01"}
        </script>
        <h1>Company results</h1><p>Operational detail paragraphs follow here for the reader.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/results")
        self.assertEqual(item["published_at"], "")

    def test_article_bare_date_time_element_is_accepted(self):
        # 复核修正：正文主文章的裸日期 <time> 合法，不得一律拒绝。
        body = """
        <html><body><h1>Quarterly update</h1>
        <time datetime="2026-08-25">August 25, 2026</time>
        <p>Volume production of the new module ramped during the quarter.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/quarterly-update")
        self.assertEqual(item["published_at"], "2026-08-25")

    def test_update_class_date_element_is_not_trusted(self):
        # 复核修正：更新时间类 class（updated/modified）不得当作发布日期；不确定留空。
        body = """
        <html><body><h1>Quarterly update</h1>
        <span class="post-update-date">August 25, 2026</span>
        <p>Volume production of the new module ramped during the quarter.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/quarterly-update")
        self.assertEqual(item["published_at"], "")

    def test_market_class_full_timestamp_time_is_not_a_publish_date(self):
        # 复核反例①：<time class="stock-update"> 带时刻的完整时间戳同样不证明归属，
        # 行情/更新排除对所有 <time> 生效。
        body = """
        <html><body><h1>Quarterly update</h1>
        <time class="stock-update" datetime="2026-09-05T10:00:00">10:00</time>
        <p>Volume production of the new module ramped during the quarter.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/quarterly-update")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_nested_related_node_without_locators_is_rejected(self):
        # 复核反例②：嵌套在 related/author 属性下的唯一 NewsArticle（无 URL/标题）
        # 不是显式主节点，必须绑定或拒绝，不得默认接受。
        body = """
        <html><body><script type="application/ld+json">
        {"@type":"WebPage","author":{"@type":"Person","name":"Jane Analyst"},
         "relatedItem":[{"@type":"NewsArticle","datePublished":"2026-01-01"}]}
        </script>
        <h1>Company results</h1><p>Operational detail paragraphs follow here for the reader.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://example.com/news/results")
        self.assertEqual(item["published_at"], "")

    def test_jsonld_nested_related_node_with_matching_url_is_accepted(self):
        # 嵌套节点一旦等值绑定当前 URL/标题即可用（绑定优先于位置）。
        body = """
        <html><body><script type="application/ld+json">
        {"@type":"WebPage","relatedItem":[
          {"@type":"NewsArticle","url":"https://example.com/news/results","datePublished":"2026-08-06"}]}
        </script></body></html>
        """
        item = parse_html_item(body, "https://example.com/news/results")
        self.assertEqual(item["published_at"], "2026-08-06")

    def test_date_class_element_is_used_when_clean(self):
        # Hamamatsu "Col Type--Date" / POET "blog-post-header2_date" 的实测形状。
        body = """
        <html><body>
        <div class="Col Type--Date">June 25, 2026</div>
        <h1>Subsidiary name change</h1>
        <p>Hamamatsu Photonics announced that its subsidiary completed the corporate name change.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://www.hamamatsu.com/jp/en/news/announcements/2026/a.html")
        self.assertEqual(item["published_at"], "2026-06-25")

    def test_date_class_element_survives_nested_label_divs(self):
        # POET 实测形状：日期元素内嵌 "Published on" 标签与多层 div。
        body = """
        <html><body>
        <div class="blog-post-header2_date"><div class="margin-bottom margin-xxsmall">
        <div>Published on</div></div><div class="text-weight-medium">August 13, 2026</div></div>
        <h1>Second quarter results</h1>
        <p>POET Technologies reported second quarter revenue up year over year.</p>
        </body></html>
        """
        item = parse_html_item(body, "https://www.poet-technologies.com/news/example")
        self.assertEqual(item["published_at"], "2026-08-13")

    def test_unclosed_paragraphs_are_split(self):
        # IQE 实测：压缩 HTML 里 <p> 不闭合，正文必须仍能切出段落。
        body = (
            '<html><body><h1>Completion of Fundraising</h1>'
            '<p><strong>THIS ANNOUNCEMENT IS RESTRICTED AND NOT FOR RELEASE.</strong>'
            '<p>Cardiff, UK 28 May 2026'
            '<p>IQE plc announced the successful completion of the fundraising.'
        )
        item = parse_html_item(body, "https://www.iqep.com/media/press-releases/2026/completion-of-fundraising/")
        self.assertEqual(len(item["paragraphs"]), 3)
        self.assertEqual(item["published_at"], "2026-05-28")

    def test_fetcher_records_article_fetch_failures_alongside_partial_success(self):
        endpoint = Endpoint(
            entity_id="MTSI", endpoint_id="MTSI_IR_RELEASES", endpoint_kind="official_ir",
            url="https://example.com/news-releases", disclosure_type="official_release",
            content_class="commercial_disclosure", provenance_class="first_party", corroborates=(),
        )
        listing = """
        <a href="/news-releases/news-release-details/good-release">Company reports quarterly results</a>
        <a href="/news-releases/news-release-details/broken-release">Company announces capacity expansion</a>
        """
        article_ok = (
            "<html><head><meta property='article:published_time' content='2026-09-01T08:00:00Z'></head>"
            "<body><p>Volume production of the module ramped during the quarter.</p></body></html>"
        )

        def fake_get(url):
            if url == endpoint.url:
                return listing, "text/html", url
            if url.endswith("broken-release"):
                raise ConnectionResetError("reset")
            return article_ok, "text/html", url

        fetcher = HttpFetcher("2026-09-01")
        fetcher._get = fake_get
        result = fetcher.fetch(endpoint)
        self.assertEqual(result.failure, "")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.article_failures, ({
            "url": "https://example.com/news-releases/news-release-details/broken-release",
            "detail": "article GET failed: ConnectionResetError: reset",
        },))

    def test_fetcher_reports_unsupported_listing_instead_of_fake_zero(self):
        # JS 渲染列表（如 investor.lumentum.com 实测形状）：静态 HTML 只有导航，
        # 无文章链接也无日期化页面项，必须显式失败。
        endpoint = Endpoint(
            entity_id="LITE", endpoint_id="LITE_IR_RELEASES", endpoint_kind="official_ir",
            url="https://example.com/financial-news-releases", disclosure_type="official_release",
            content_class="corporate_narrative", provenance_class="first_party", corroborates=(),
        )
        js_listing = """
        <html><body>
        <a href="/financial-news-releases/default.aspx">News Releases</a>
        <a href="/sec-filings/default.aspx">SEC Filings</a>
        <div id="press-release-widget" data-lazy="true"></div>
        </body></html>
        """
        fetcher = HttpFetcher("2026-09-01")
        fetcher._get = lambda _url: (js_listing, "text/html", endpoint.url)
        result = fetcher.fetch(endpoint)
        self.assertEqual(result.items, ())
        self.assertTrue(result.failure.startswith("unsupported_listing"))

    def test_configured_unsupported_listing_fails_explicitly_before_fetch(self):
        # 复核修正：CSCO/AAOI 已证实 JS 渲染列表，由配置显式 unsupported；
        # 不做数量阈值猜测，也不得因个别嵌套旧文冒充健康零增量。
        endpoint = Endpoint(
            entity_id="CSCO", endpoint_id="CSCO_IR_RELEASES", endpoint_kind="counterparty_release",
            url="https://example.com/newsroom", disclosure_type="customer_release",
            content_class="commercial_disclosure", provenance_class="counterparty",
            corroborates=("AAOI",), unsupported_listing=True,
        )
        fetcher = HttpFetcher("2026-09-01")
        fetcher._get = lambda _url: (_ for _ in ()).throw(AssertionError("must not fetch"))
        result = fetcher.fetch(endpoint)
        self.assertEqual(result.items, ())
        self.assertTrue(result.failure.startswith("unsupported_listing"))

    def test_q4_news_details_default_aspx_article_link_is_kept(self):
        # 复核修正：Q4 平台真实文章形状（news-details/.../default.aspx）不得被
        # blanket 排除；FAQ 等导航仍拒绝。
        body = """
        <a href="/investors/news-details/2026/09/01/company-reports-quarterly-results/default.aspx">Company Reports Quarterly Results</a>
        <a href="/investors/faq/default.aspx">Investor FAQs</a>
        """
        self.assertEqual(
            discover_article_links(body, "https://example.com/investors"),
            [("https://example.com/investors/news-details/2026/09/01/company-reports-quarterly-results/default.aspx",
              "Company Reports Quarterly Results")],
        )

    def test_article_id_query_is_kept_but_pagination_rejected(self):
        body = """
        <a href="/news/story.asp?articleid=12345">Company announces first volume order</a>
        <a href="/news?articleId=67890">Company begins sampling 1.6T modules</a>
        <a href="/press-releases?page=2">Company press release archive page</a>
        <a href="/press-releases?a10324f9_page=2">Company press release more page</a>
        """
        self.assertEqual(
            [link for link, _ in discover_article_links(body, "https://example.com/press-releases")],
            [
                "https://example.com/news/story.asp?articleid=12345",
                "https://example.com/news?articleId=67890",
            ],
        )

    def test_atom_feed_is_normalized(self):
        feed = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
        <entry><title>Sampling update</title><link href="/news/1"/>
        <published>2026-09-01T00:00:00Z</published><summary>Company began sampling 1.6T DSPs.</summary></entry>
        </feed>"""
        items = parse_feed(feed, "https://example.com/feed")
        self.assertEqual(items[0]["url"], "https://example.com/news/1")
        self.assertEqual(items[0]["published_at"], "2026-09-01")
        self.assertIn("sampling", items[0]["paragraphs"][0]["text"])

    def test_fixture_shaped_public_json_uses_same_seam(self):
        endpoint = Endpoint(
            entity_id="AAOI", endpoint_id="AAOI", endpoint_kind="official_ir",
            url="https://example.com/feed.json", disclosure_type="official_release",
            content_class="commercial_disclosure", provenance_class="first_party", corroborates=(),
        )
        fetcher = HttpFetcher("2026-09-01")
        fetcher._get = lambda _url: (
            json.dumps({"items": [{"url": "https://example.com/1", "title": "x",
                                   "published_at": "2026-09-01", "paragraphs": []}]}),
            "application/json", endpoint.url,
        )
        result = fetcher.fetch(endpoint)
        self.assertEqual(result.failure, "")
        self.assertEqual(len(result.items), 1)


if __name__ == "__main__":
    unittest.main()
