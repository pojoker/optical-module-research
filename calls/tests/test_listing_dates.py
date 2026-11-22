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
