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
