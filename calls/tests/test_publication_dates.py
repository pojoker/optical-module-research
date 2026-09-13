"""Minimized real publisher pages captured 2026-09-10."""
import json
import unittest
from pathlib import Path
from calls.http_discovery import parse_html_item, discover_article_links, HttpFetcher
from calls.daily_discovery import Endpoint
from urllib.error import HTTPError
from email.message import Message

class PublicationDateCases(unittest.TestCase):
    def test_real_pages(self):
        for row in json.loads(Path(__file__).with_name('publication_date_cases.json').read_text()):
            with self.subTest(url=row['url']):
                self.assertEqual(parse_html_item(row['html'], row['url'])['published_at'], row['expected'])

    def test_unrelated_suss_header_is_not_publication_date(self):
        body = '<header><p class="mb-2">Sep 1, 2026 10:00:00</p></header><h1>A report</h1>'
        self.assertEqual(parse_html_item(body, 'https://www.suss.com/en/news/corporate-news/report')['published_at'], '')

    def test_source_dates_outside_article_and_event_dates_are_not_publication(self):
        body = '<p>Los Angeles, California, March 17, 2026 – Source Photonics Inc.</p><div class="entry-content"><p>When: September 29 – October 1, 2025</p></div>'
        self.assertEqual(parse_html_item(body, 'https://www.sourcephotonics.com/news/example/')['published_at'], '')

    def test_openlight_wrong_page_url_stays_rejected(self):
        rows = json.loads(Path(__file__).with_name('publication_date_cases.json').read_text())
        row = next(r for r in rows if 'advantest-partners' in r['url'])
        body = row['html'].replace(row['url'], 'https://openlightphotonics.com/newsroom/different-story')
        self.assertEqual(parse_html_item(body, row['url'])['published_at'], '')

    def test_te_published_field_is_not_replaced_with_body_date(self):
        body = '<h1>COMPUTEX 2026</h1><div class="published-date"><h4>Published</h4><p>05/27/26</p></div><h2>June 1, 2026</h2>'
        self.assertEqual(parse_html_item(body, 'https://www.te.com/en/about-te/news-center/computex-2026.html')['published_at'], '2026-05-27')
        self.assertEqual(parse_html_item(body, 'https://example.org/news/story')['published_at'], '')

    def test_te_explicit_published_precedes_generic_dateline(self):
        body = '<h1>Article</h1><div class="published-date"><h4>Published</h4><p>07/23/26</p></div><p>Cambridge, UK, 1 September 2026</p>'
        self.assertEqual(parse_html_item(body, 'https://www.te.com/en/about-te/news-center/release.html')['published_at'], '2026-07-23')

    def test_aaoi_home_logo_is_not_an_article(self):
        body = '<a href="home"><img alt="Newsroom"></a><a href="a-new-release">A new official release</a>'
        links = discover_article_links(body, 'https://newsroom.ao-inc.com/news-releases/', 20, r'/news-releases/[^/]+')
        self.assertEqual([x[0] for x in links], ['https://newsroom.ao-inc.com/news-releases/a-new-release'])

    def test_rate_limit_stops_remaining_articles_and_preserves_completed_item(self):
        endpoint = Endpoint('LITE', 'TEST', 'official_ir', 'https://example.org/news/',
                            'official_release', 'corporate_narrative', 'first_party', ())
        requested = []
        headers = Message()
        headers['Retry-After'] = '120'
        class Fetcher(HttpFetcher):
            def _get(self, url):
                requested.append(url)
                if url == endpoint.url:
                    return '<a href="first-release">First official release</a><a href="second-release">Second official release</a><a href="third-release">Third official release</a>', 'text/html', url
                if url.endswith('first-release'):
                    return '<h1>First release</h1><meta property="article:published_time" content="2026-09-08"><p>A complete first official article with sufficient body.</p>', 'text/html', url
                raise HTTPError(url, 429, 'Too Many Requests', headers, None)
        result = Fetcher('2026-09-09').fetch(endpoint)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(len(requested), 3)
        self.assertEqual(len(result.article_failures), 1)
        self.assertIn('Retry-After=120', result.article_failures[0]['detail'])
