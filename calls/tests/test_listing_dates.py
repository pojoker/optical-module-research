"""Reduced publisher markup captured 2026-09-10; dates belong to cards."""
import unittest
from unittest.mock import patch
from calls import http_discovery as http
from calls.daily_discovery import Endpoint, _parse_item

ASMPT = 'https://www.asmpt.com/en/investor-relations/news-events/'
ACCTON = 'https://www.accton.com/express/'
SMTC = 'https://www.semtech.com/company/press/'


def asmpt_card(slug, day):
    return f'''<div class="card graybg25"><a href="{slug}/"><img></a>
      <div class="card-body"><small class="text-muted">{day} | Press Release</small>
      <h4 class="card-title"><a href="{slug}/">{slug}</a></h4></div></div>'''


def semtech_card(slug, day):
    return f'''<div class="row"><div class="col-sm-4"><a href="/company/press/{slug}"><img></a></div>
      <div class="col-sm-8"><span class="entry-meta">{day}</span>
      <h3><a href="/company/press/{slug}">{slug}</a></h3></div></div>'''


def accton_story(slug, title, day, year=''):
    marker = f'<span class="ctl-year-container" data-section-title="{year}"></span>' if year else ''
    return f'''<div class="ctl-story ctl-story-right">{marker}<div class="ctl-content">
      <div class="ctl-title" role="heading">{title}</div><div class="ctl-media">
      <a class="story-link" href="/{slug}/" title="{title}"><img></a></div>
      <div class="ctl-labels"><div class="ctl-label-big story-date">{day}</div></div></div></div>'''


class ListingDatesTest(unittest.TestCase):
    def test_sicoya_ordinal_date_binds_to_own_article_not_url(self):
        body = '<article><h1><a href="/2026/08/27/a/">Release A</a></h1><p class="date">Published: Thursday August 27th, 2026 • In News</p></article>'
        body += '<article><h1><a href="/2024/09/17/b/">Unknown B</a></h1><p class="date">• In News</p></article>'
        rows = http.discover_dated_article_links(body, 'https://sicoya.com/news/')
        self.assertEqual([r['published_at'] for r in rows], ['2026-08-27', ''])

    def test_avicena_dateline_card_and_navigation_exclusion(self):
        body = '<a href="/avicena-technologies/">Avicena Technologies</a><div class="qodef-e-content"><h5><a href="/avicena-release/">Release A</a></h5><p class="qodef-e-excerpt">Sunnyvale, CA, September 3, 2025 — Avicena, the leader announces something.</p></div>'
        rows = http.discover_dated_article_links(body, 'https://avicena.tech/press-releases/')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['published_at'], '2025-09-03')

    def test_avicena_event_date_does_not_become_publication(self):
        body = '<div class="qodef-e-content"><h5><a href="/avicena-show/">Event</a></h5><p class="qodef-e-excerpt">Visit Avicena September 3, 2026 at our booth.</p></div>'
        self.assertEqual(http.discover_dated_article_links(body, 'https://avicena.tech/press-releases/')[0]['published_at'], '')

    def test_lightmatter_multiple_targets_cannot_borrow_heading_date(self):
        body = '<a class="group" href="/press-release/a/"><h3>Release A</h3><span class="allcaps-sm">Oct 12, 2026</span></a>'
        rows = http.discover_dated_article_links(body, 'https://lightmatter.com/press-releases/')
        self.assertEqual(rows[0]['published_at'], '2026-10-12')
        bad = '<div class="group"><h3>Release A</h3><span class="allcaps-sm">Oct 12, 2026</span><a href="/press-release/b/">Release B</a><a href="/press-release/a/">Release A</a></div>'
        rows = http.discover_dated_article_links(bad, 'https://lightmatter.com/press-releases/')
        self.assertTrue(rows)
        self.assertTrue(all(not r['published_at'] for r in rows))

    def test_coherent_card_date_binds_only_to_own_headline(self):
        body = '<article class="nir-widget-article"><div class="nir-widget--news--headline"><a href="/news-releases/news-release-details/a">Release A</a></div><div class="nir-widget--news--date-time">September 21, 2026</div></article>'
        rows = http.discover_dated_article_links(body, 'https://ir.coherent.com/news-events/corporate-releases')
        self.assertEqual(rows[0]['published_at'], '2026-09-21')

    def test_recent_dates_precede_unknown_and_old_is_never_requested(self):
        url = 'https://sicoya.com/news/'
        body = '<article><h1><a href="/2024/01/01/unknown/">Unknown</a></h1></article>'
        body += '<article><h1><a href="/2026/08/27/old/">Old</a></h1><p class="date">Published: August 27th, 2026 • In News</p></article>'
        body += '<article><h1><a href="/2026/10/12/current/">Current</a></h1><p class="date">Published: October 12th, 2026 • In News</p></article>'
        endpoint = Endpoint('WATCH_SICOYA', 'test', 'official_ir', url, 'official_release', 'commercial_disclosure', 'first_party', ())
        fetcher = http.HttpFetcher('2026-10-13', max_items=1)
        requested = []
        def request(u):
            requested.append(u)
            return (body if u == url else '<h1>Current</h1><p>This release describes a newly introduced silicon photonics product.</p>', 'text/html', u)
        fetcher._request = request
        result = fetcher.fetch(endpoint)
        self.assertEqual(requested, [url, 'https://sicoya.com/2026/10/12/current'])
        self.assertEqual(result.items[0]['published_at'], '2026-10-12')

    def test_asmpt_card_binding_and_unknown_nav(self):
        html = '<a href="home"><img alt="Logo"></a><a href="new-ceo/">CEO</a>'
        html += asmpt_card('asmpt-announces-2026-interim-results', '2026-07-29')
        html += asmpt_card('another-release', '2026-04-22')
        rows = http.discover_dated_article_links(html, ASMPT)
        self.assertEqual([(r['title'], r['published_at']) for r in rows], [
            ('asmpt-announces-2026-interim-results', '2026-07-29'),
            ('another-release', '2026-04-22'), ('CEO', '')])
        self.assertEqual(rows[0]['url'], ASMPT + 'asmpt-announces-2026-interim-results')

    def test_accton_publication_not_report_month_and_year_transition(self):
        html = '<div class="ctl-timeline ctl-timeline-container">'
        html += accton_story('accton-aug-2026-sales-revenue-report', 'Accton Aug 2026 sales revenue report', 'Sep 07', '2026')
        html += accton_story('accton-jul-2026-sales-revenue-report', 'Accton Jul 2026 sales revenue report', 'Aug 06')
        html += accton_story('accton-announce-800g-optimzed-products', '800G products', 'Oct 03', '2023')
        html += '</div><div class="ctl-timeline">' + accton_story('undated', 'Unknown', 'Jan 01') + '</div>'
        rows = http.discover_dated_article_links(html, ACCTON)
        self.assertEqual([r['published_at'] for r in rows], ['2026-09-07', '2026-08-06', '2023-10-03', ''])
        self.assertEqual(rows[2]['url'], 'https://www.accton.com/accton-announce-800g-optimzed-products')

    def test_semtech_pager_outer_row_and_logo_cannot_borrow_date(self):
        html = '<div class="row">' + semtech_card('lora-family', 'August 19, 2026')
        html += semtech_card('new-release', 'September 08, 2026')
        html += '<a class="page-link" href="/company/press/P10">2</a><a href="/company/press/P20">3</a><a href="/"><img alt="Logo"></a></div>'
        rows = http.discover_dated_article_links(html, SMTC)
        self.assertEqual([(r['url'], r['published_at']) for r in rows], [
            (SMTC+'lora-family', '2026-08-19'), (SMTC+'new-release', '2026-09-08')])

    def test_missing_date_is_unknown_and_other_site_not_supported(self):
        self.assertEqual(http.discover_dated_article_links(semtech_card('release', ''), SMTC)[0]['published_at'], '')
        self.assertIsNone(http.discover_dated_article_links('', 'https://example.com/company/press/'))

    def test_fetch_filters_before_detail_and_before_max_items(self):
        html = semtech_card('old-release', 'August 19, 2026') + semtech_card('current-release', 'September 08, 2026')
        endpoint = Endpoint('SMTC', 'test', 'official_release', SMTC, 'official_release', 'commercial_disclosure', 'first_party', ())
        fetcher = http.HttpFetcher('2026-09-09', max_items=1)
        requested = []
        def request(url):
            requested.append(url)
            if url == SMTC:
                return html, 'text/html', url
            return '<h1>Current release</h1><p>Semtech announces a new product for optical connectivity.</p>', 'text/html', url
        with patch.object(fetcher, '_request', side_effect=request):
            result = fetcher.fetch(endpoint)
        self.assertEqual(requested, [SMTC, SMTC+'current-release'])
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]['published_at'], '2026-09-08')

    def test_all_dated_cards_outside_window_returns_empty_success(self):
        endpoint = Endpoint('SMTC', 'test', 'official_release', SMTC, 'official_release', 'commercial_disclosure', 'first_party', ())
        fetcher = http.HttpFetcher('2026-09-09')
        with patch.object(fetcher, '_request', return_value=(semtech_card('old-release', 'August 19, 2026'), 'text/html', SMTC)) as request:
            result = fetcher.fetch(endpoint)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(result.items, ())
        self.assertFalse(result.failure)

    def test_publisher_card_date_is_distinct_from_old_news_dateline(self):
        html = semtech_card('new-optical-release', 'September 08, 2026')
        endpoint = Endpoint('SMTC', 'test', 'official_release', SMTC, 'official_release', 'commercial_disclosure', 'first_party', ())
        fetcher = http.HttpFetcher('2026-09-09')
        def request(url):
            if url == SMTC:
                return html, 'text/html', url
            return '<h1>Optical release</h1><p>CAMARILLO, Calif., Aug. 25, 2026 – Semtech Corporation announces new optical products.</p>', 'text/html', url
        with patch.object(fetcher, '_request', side_effect=request):
            result = fetcher.fetch(endpoint)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]['published_at'], '2026-09-08')
        self.assertEqual(result.items[0]['detail_date_observed'], '2026-08-25')
        # This audit context must survive SourceItem normalization into staging.
        normalized = _parse_item(endpoint, result.items[0], 'test')
        self.assertIn('2026-09-08', normalized.note)
        self.assertIn('2026-08-25', normalized.note)
