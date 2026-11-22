"""Regression cases from the September 9 discovery audit."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from calls import daily_discovery as dd
from calls.http_discovery import HttpFetcher, discover_article_links
from calls.tests.test_daily_discovery import _build_source, _read_csv


class CoverageRegressionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = _build_source(self.root / 'source')
        self.registry = dd.load_entity_registry(self.source)
        self.endpoint = dd.Endpoint('WATCH_IQE', 'IQE', 'counterparty_release',
            'https://www.iqep.com/media/press-releases', 'official_release',
            'commercial_disclosure', 'counterparty', ('LITE', 'MTSI'), publisher_fallback=True)

    def item(self, text, endpoint=None):
        return dd._parse_item(endpoint or self.endpoint, {
            'url': 'https://www.iqep.com/media/press-releases/2026/sampling/',
            'title': 'IQE announces customer sampling', 'published_at': '2026-09-03',
            'paragraphs': [{'anchor': 'p1', 'text': text}]}, 'test')

    def test_iqe_customer_sampling_is_own_asserted_candidate_not_independent(self):
        endpoint = self.endpoint
        config = self.root / 'config.json'
        config.write_text(json.dumps({'version': 1, 'entities': {'WATCH_IQE': {'endpoints': [{
            'endpoint_id': endpoint.endpoint_id, 'endpoint_kind': endpoint.endpoint_kind,
            'url': endpoint.url, 'disclosure_type': endpoint.disclosure_type,
            'content_class': endpoint.content_class, 'provenance_class': endpoint.provenance_class,
            'corroborates_entity_ids': list(endpoint.corroborates), 'publisher_fallback': True}]}}}))
        class Fetcher:
            def fetch(self, ep):
                return dd.FetchResult(ep.endpoint_id, ({
                    'url': 'https://www.iqep.com/media/press-releases/2026/sampling/',
                    'title': 'IQE announces customer sampling', 'published_at': '2026-09-03',
                    'paragraphs': [{'anchor': 'p1', 'text': 'IQE quantum dot laser technology moves to customer sampling.'}]},), '')
        state = self.root / 'state'
        summary = dd.run_daily_discovery(self.source, state, '2026-09-09', config, Fetcher())
        dd.verify_staging(self.source, state, '2026-09-09')
        self.assertEqual(summary['event_candidates'], 1)
        self.assertEqual(summary['corroboration_suggestions'], 0)
        staging = state / 'staging' / '2026-09-09'
        self.assertEqual(_read_csv(staging / 'disclosure_candidates.csv')[0]['provenance_class'], 'first_party')
        event = _read_csv(staging / 'event_candidates.csv')[0]
        self.assertEqual(event['primary_subject_id'], 'WATCH_IQE')
        self.assertEqual(event['event_status'], 'asserted')

    def test_counterparty_match_keeps_distinct_subject_and_provenance(self):
        item = dd._route_publisher_material(self.item('MACOM began shipping the optical device.'), self.registry)
        self.assertEqual(item.provenance_class, 'counterparty')
        self.assertEqual(dd._event_subject(item.endpoint, item, self.registry)[0], 'MTSI')

    def test_cisco_own_release_falls_back_without_becoming_customer_confirmation(self):
        endpoint = replace(self.endpoint, entity_id='CSCO', corroborates=('AAOI', 'LITE'),
                           disclosure_type='customer_release')
        item = dd._route_publisher_material(self.item('Cisco began shipping a new switch.', endpoint), self.registry)
        self.assertEqual(item.provenance_class, 'first_party')
        self.assertEqual(item.disclosure_type, 'official_release')
        self.assertEqual(dd._event_subject(item.endpoint, item, self.registry)[0], 'CSCO')

    def test_business_demonstrated_ability_is_not_technical_demo(self):
        self.assertEqual(dd.extract_statements(self.item(
            'During the period, we have demonstrated our ability to capture long-term growth opportunities.')), ())
        self.assertEqual(dd.extract_statements(self.item(
            'IQE demonstrated an optical link at the exhibition.'))[0].signal_code, 'demonstration')

    def test_positive_article_paths_filter_before_limit(self):
        html = '<a href="/news-events/ir-calendar">IR Calendar</a><a href="/news-events/press-releases/detail/1/new-chip">New chip release</a>'
        self.assertEqual(discover_article_links(html, 'https://example.com/news', 1,
            r'^/news-events/press-releases/detail/'),
            [('https://example.com/news-events/press-releases/detail/1/new-chip', 'New chip release')])

    def test_filtered_list_meta_date_cannot_turn_list_into_article(self):
        endpoint = replace(self.endpoint, article_path_pattern=r'^/articles/[^/]+$')
        fetcher = HttpFetcher('2026-09-09')
        fetcher._get = lambda u: ('<meta name="date" content="2026-09-03"><p>Official news list with site text.</p>', 'text/html', u)
        result = fetcher.fetch(endpoint)
        self.assertFalse(result.items)
        self.assertIn('unsupported_listing', result.failure)

    def test_unknown_json_format_is_not_healthy_empty_list(self):
        fetcher = HttpFetcher('2026-09-09')
        fetcher._get = lambda u: ('{"filings":{"recent":{}}}', 'application/json', u)
        self.assertTrue(fetcher.fetch(self.endpoint).failure)

    def test_all_blog_links_filtered_is_not_healthy_zero(self):
        endpoint = replace(self.endpoint, article_path_pattern=r'^/blog/')
        fetcher = HttpFetcher('2026-09-09')
        fetcher._get = lambda u: ('<a href="/blog/technical-demo">Technical demo announcement</a>', 'text/html', u)
        result = fetcher.fetch(endpoint)
        self.assertFalse(result.items)
        self.assertIn('unsupported_listing', result.failure)

    def test_release_template_dates_and_plain_time(self):
        from calls.http_discovery import parse_html_item
        examples = [
            ('https://www.ff-opticalcomponents.com/en/information/releases_20250310.html',
             '<div class="m_page-meta"><p>March 10, 2025</p></div>', '2025-03-10'),
            ('https://lumilens.com/news-insights/lumilens-emerges-with-900m-in-funding',
             '<p>SAN JOSE, Calif. — August 6, 2026 — Lumilens, the connectivity platform for AI infrastructure, today emerged from stealth with funding.</p>', '2026-08-06'),
            ('https://soitec.com/home/group/corporate/newsroom/press-releases/content/2026/09/02/soitec-trading-update',
             '<div class="mt-3 pb-3 fw-normal text-gray-400"><span>September 2, 2026</soan></div>', '2026-09-02'),
            ('https://www.furukawaelectric.com/en/release/2026/kei_20260716.html',
             '<div class="m-text text-right"><p class="m-text__item">July 16, 2026</p></div>', '2026-07-16'),
            ('https://sumitomoelectric.com/press/2026/09/prs037',
             '<h1 class="a-subheadline">07 September 2026</h1>', '2026-09-07'),
            ('https://www.aixtron.com/en/press/press-releases/release_n14146',
             '<p>Herzogenrath, Germany, July 30, 2026 -- AIXTRON announced a new product with a long description that exceeds the generic dateline bound.</p>', '2026-07-30'),
            ('https://www.sivers-semiconductors.com/press/new-release/',
             '<p class="wp-block-paragraph"><time>September 3, 2026</time> | Category: Non Regulatory</p>', '2026-09-03'),
        ]
        for url, html, expected in examples:
            with self.subTest(url=url):
                self.assertEqual(parse_html_item(html, url)['published_at'], expected)
        self.assertEqual(parse_html_item('<time class="stock-update">September 9, 2026</time>', 'https://example.com/article')['published_at'], '')

    def test_sivers_official_html_envelope(self):
        endpoint = replace(self.endpoint,
            url='https://www.sivers-semiconductors.com/wp-json/sivers/v1/news-press?post_types=press',
            article_path_pattern=r'^/press/[^/]+/?$')
        fetcher = HttpFetcher('2026-09-09')
        def get(url):
            if '/wp-json/' in url:
                return json.dumps({'success': True, 'html': '<a href="/press/optical-expansion/">Optical factory expansion</a>'}), 'application/json', url
            return '<time>September 3, 2026</time><p>Sivers announced capacity expansion of its optical factory.</p>', 'text/html', url
        fetcher._get = get
        result = fetcher.fetch(endpoint)
        self.assertFalse(result.failure)
        self.assertEqual(result.items[0]['published_at'], '2026-09-03')

    def test_lumilens_press_cards_exclude_blog_and_external_media(self):
        from calls.http_discovery import _publisher_press_cards
        def card(category, href):
            return f'<div class="news-content"><div class="news-contant_block"><div class="refrence-text">{category}</div><h3>Company release headline</h3></div><div class="news-button_wrapper"><a href="{href}">Read more</a></div></div>'
        html = card('Blog', '/news-insights/blog') + card('Press release', '/news-insights/funding') + card('Press release', 'https://media.example/story')
        self.assertEqual(_publisher_press_cards(html, 'https://lumilens.com/news-insights'),
            [('https://lumilens.com/news-insights/funding', 'Company release headline')])

    def test_other_paragraph_or_mixed_actor_cannot_corroborate_target_shipping(self):
        config = self.root / 'counterparty-config.json'
        config.write_text(json.dumps({'version': 1, 'entities': {
            'WATCH_IQE': {'endpoints': [{'endpoint_id': 'IQE', 'endpoint_kind': 'counterparty_release',
                'url': 'https://www.iqep.com/media/press-releases', 'disclosure_type': 'official_release',
                'content_class': 'commercial_disclosure', 'provenance_class': 'counterparty',
                'corroborates_entity_ids': ['LITE'], 'publisher_fallback': True}]},
            'LITE': {'endpoints': [{'endpoint_id': 'LITE', 'endpoint_kind': 'official_ir',
                'url': 'https://example.com/lite/news', 'disclosure_type': 'official_release',
                'content_class': 'commercial_disclosure', 'provenance_class': 'first_party'}]}}}))
        for index, quote in enumerate((
            'IQE began shipping 1.6T optical modules.',
            'IQE began shipping optical modules to Lumentum.',
            'We began shipping optical modules to Lumentum.',
        )):
            with self.subTest(quote=quote):
                class Fetcher:
                    def fetch(self, ep):
                        paragraphs = ([{'anchor': 'p1', 'text': quote},
                            {'anchor': 'p2', 'text': 'Lumentum appears here only as an industry peer.'}]
                            if ep.entity_id == 'WATCH_IQE' else
                            [{'anchor': 'p1', 'text': 'Lumentum began shipping 1.6T optical modules.'}])
                        return dd.FetchResult(ep.endpoint_id, ({'url': ep.url + '/release',
                            'title': 'Official shipping announcement', 'published_at': '2026-09-03',
                            'paragraphs': paragraphs},), '')
                state = self.root / f'ambiguous-{index}'
                summary = dd.run_daily_discovery(self.source, state, '2026-09-09', config, Fetcher())
                self.assertEqual(summary['corroboration_suggestions'], 0)
                self.assertEqual(summary['claim_candidates'], 2)
                self.assertEqual(summary['failure_types']['unresolved_claim_subject'], 1)
                evidence = _read_csv(state / 'staging/2026-09-09/evidence_candidates.csv')
                self.assertTrue(all(row['independence_class'] == 'first_party' for row in evidence))

    def test_invalid_json_entries_are_reported_while_valid_entries_survive(self):
        valid = {'url': 'https://example.com/news/item', 'published_at': '2026-09-03',
                 'title': 'A release', 'paragraphs': [{'anchor': 'p1', 'text': 'A new product announcement.'}]}
        for raw in ([3], [valid, 3]):
            fetcher = HttpFetcher('2026-09-09')
            fetcher._get = lambda u: (json.dumps({'items': raw}), 'application/json', u)
            result = fetcher.fetch(self.endpoint)
            self.assertEqual(len(result.items), int(len(raw) == 2))
            self.assertEqual(len(result.article_failures), 1)

    def test_explicit_ir_article_pattern_preserves_descendants_only(self):
        url = 'https://www.asmpt.com/en/investor-relations/news-events/'
        body = '<a href="' + url + 'asmpt-announces-2026-interim-results/">ASMPT Interim Results</a>'
        body += '<a href="' + url + 'overview/">Company overview</a>'
        body += '<a href="' + url + 'results.pdf">Annual results</a>'
        self.assertEqual(discover_article_links(body, url), [])
        links = discover_article_links(body, url, path_pattern=r'^/en/investor-relations/news-events/[^/]+/?$')
        self.assertEqual(len(links), 1)
        self.assertIn('interim-results', links[0][0])

    def test_delta_inline_release_body_is_scoped_and_unambiguous(self):
        from calls.http_discovery import parse_html_item
        from html import escape
        url = 'https://www.deltaww.com/en-US/press/41092'
        body = '<h1>Delta August revenues</h1><span class="empty:hidden">09/09/2026</span><p>Navigation pollution is not article text.</p>'
        frame = '<iframe srcdoc="' + escape('<p>Delta Electronics reported consolidated sales revenues for August.</p>', quote=True) + '"></iframe>'
        result = parse_html_item(body + frame, url)
        self.assertEqual(result['published_at'], '2026-09-09')
        self.assertEqual(len(result['paragraphs']), 1)
        self.assertIn('consolidated sales', result['paragraphs'][0]['text'])
        for invalid in (body, body + frame + frame):
            result = parse_html_item(invalid, url)
            self.assertEqual(result['paragraphs'], [])
            self.assertEqual(result['published_at'], '')

    def test_malformed_ficontec_href_does_not_abort_valid_links(self):
        body = '<a href="https://masstart.eu]">MASSTART Project</a><a href="/news/new-product/">New optical product announcement</a>'
        links = discover_article_links(body, 'https://www.ficontec.com/news/')
        self.assertEqual(len(links), 1)
        self.assertIn('/news/new-product', links[0][0])

    def test_explicit_ase_article_path_allows_empty_card_anchor(self):
        body = '<a href="/press-room/ainos-and-ase-partner-to-power-ai-scent-digitization-in-semiconductor-manufacturing"></a><a href="/press-room/"></a>'
        links = discover_article_links(body, 'https://www.aseglobal.com/press-room', path_pattern=r'^/press-room/[^/]+/?$')
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0][1], '')
        self.assertEqual(discover_article_links(body, 'https://www.aseglobal.com/press-room'), [])

    def test_ase_semtech_publication_templates(self):
        from calls.http_discovery import parse_html_item
        ase = parse_html_item('<h1>ASE release</h1><div class="blog-mini-time">July 23, 2026</div><p>ASE and Ainos announced their collaboration.</p>', 'https://www.aseglobal.com/press-room/ainos-partnership')
        self.assertEqual(ase['published_at'], '2026-07-23')
        smtc = parse_html_item('<h1>Semtech release</h1><p>CAMARILLO, Calif., Aug.&nbsp;25, 2026 &ndash; Semtech Corporation announced a product for production in September 2026.</p>', 'https://www.semtech.com/company/press/new-chipset')
        self.assertEqual(smtc['published_at'], '2026-08-25')

    def test_mitsubishi_official_envelope_fetches_detail(self):
        url = 'https://www.mitsubishielectric.com/global/common/mel25/news-data/gws-news/global/www/en/news-article.json'
        e = replace(self.endpoint, url=url, article_path_pattern=r'^/en/pr/20\d{2}/[^/]+/?$')
        f = HttpFetcher('2026-09-09')
        def get(u):
            if u == url:
                return json.dumps({'news': [{'url': '/en/pr/2026/0908_hr/', 'title': 'Mitsubishi new optical technology'}]}), 'application/json', u
            return '<h1>Mitsubishi new optical technology</h1><time datetime="2026-09-08"></time><p>Mitsubishi announced a new optical technology product.</p>', 'text/html', u
        f._get = get
        result = f.fetch(e)
        self.assertEqual(result.failure, '')
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]['published_at'], '2026-09-08')

    def test_parse_deadline_preserves_completed_articles(self):
        import time
        from unittest.mock import patch
        from calls.http_discovery import parse_html_item
        e = replace(self.endpoint, url='https://example.com/news/', article_path_pattern=r'^/news/[^/]+$')
        f = HttpFetcher('2026-09-09', endpoint_budget=0.05)
        listing = '<a href="/news/first">First announcement</a><a href="/news/second">Second announcement</a>'
        f._get = lambda u: (listing if u == e.url else '<h1>Product news</h1><time datetime="2026-09-08"></time><p>Optical product sampling began with customers.</p>', 'text/html', u)
        def parse(body, url, *args):
            if url.endswith('/second'):
                time.sleep(0.1)
            return parse_html_item(body, url, *args)
        with patch('calls.http_discovery.parse_html_item', side_effect=parse):
            r = f.fetch(e)
        self.assertEqual(len(r.items), 1)
        self.assertIn('/first', r.items[0]['url'])
        self.assertIn('budget exhausted', r.article_failures[0]['detail'])

    def test_additional_official_date_templates(self):
        from calls.http_discovery import parse_html_item
        samples = [
            ('https://newsroom.ao-inc.com/news-releases/a-product/', '<p class="post-date-author">May 12, 2026</p>', '2026-05-12'),
            ('https://www.aixtron.com/en/press/press-releases/notice_n14136', '<p>27. Juli 2026 | Stimmrechtsmitteilungen</p><h1 class="h2">Notice</h1>', '2026-07-27'),
            ('https://www.evgroup.com/company/news/detail/partnership', '<p><strong>WARSAW, Poland and ST. FLORIAN, Austria, April 21, 2026&nbsp;</strong>– new partnership.</p>', '2026-04-21')]
        for url, body, expected in samples:
            self.assertEqual(parse_html_item(body, url)['published_at'], expected)
        url = 'https://openlightphotonics.com/newsroom/new-product'
        node = {'@type': 'WebSite', 'headline': 'New product', 'url': url, 'mainEntityOfPage': url, 'datePublished': '2026-06-23'}
        body = '<h1>New product</h1><script type="application/ld+json">' + json.dumps(node) + '</script>'
        self.assertEqual(parse_html_item(body, url)['published_at'], '2026-06-23')
        self.assertEqual(parse_html_item(body, 'https://other.example/newsroom/new-product')['published_at'], '')

    def test_nttid_and_legacy_alphabet_dates_not_current_copyright(self):
        from calls.http_discovery import parse_html_item
        for url, body, expected in [
            ('https://www.ntt-innovative-devices.com/en/news/2026/3/ofc.html', '<span class="text_s">March 9, 2026</span>', '2026-03-09'),
            ('https://abc.xyz/investor/news/news-details/2025/result/default.aspx', '<span class="evergreen-news-date-text" id="_ctrl0_ctl33_spanDate">May 1, 2025</span>', '2025-05-01')]:
            self.assertEqual(parse_html_item(body + '<p>Copyright 2026</p>', url)['published_at'], expected)
        fn = discover_article_links('<a href="/node/13541/pdf">Download press PDF</a><a href="/node/13541">Quarterly results</a>', 'https://investor.fabrinet.com/press-releases', path_pattern=r'/news-release-details/|^/node/\d+/?$')
        self.assertEqual(len(fn), 1)
        self.assertNotIn('/pdf', fn[0][0])

    def test_mycronic_suss_dates_and_senko_real_cards(self):
        from calls.http_discovery import parse_html_item, _publisher_press_cards
        my = '<div class="c-listing-item__meta-info-item"><svg><use href="#calendar-day"></use></svg> 6 MAY 2026 </div>'
        self.assertEqual(parse_html_item(my, 'https://www.mycronic.com/news-events/our-press-releases/results')['published_at'], '2026-05-06')
        su = '<br/>06.08.2026 / 07:30 CET/CEST<br/>The issuer is solely responsible for the content of this announcement.<br/>'
        self.assertEqual(parse_html_item(su, 'https://www.suss.com/en/news/results')['published_at'], '2026-08-06')
        se = '<a href="/tag/optics">Optics tag</a><a href="/product/connector">Connector product</a><div class="split-cont2 bg-transparent"><div class="aside"><h3>SENKO Collaborates with Lightmatter</h3><p>Official announcement.</p><div class="btn-out"><a href="/senko-collaborates-with-lightmatter/" class="btn">Learn More</a></div></div></div>'
        self.assertEqual(_publisher_press_cards(se, 'https://www.senko.com/news/'), [('https://www.senko.com/senko-collaborates-with-lightmatter', 'SENKO Collaborates with Lightmatter')])

    def test_q4_bad_records_preserve_valid_same_origin_releases(self):
        good = {'LinkToDetailPage': '/news-release/news-release-details/2026/results/default.aspx', 'Headline': 'Amazon quarterly results', 'PressReleaseDate': '09/08/2026 16:01:00', 'Body': '<p>Amazon announced quarterly financial results with consolidated revenue.</p>'}
        bad = [dict(good, LinkToDetailPage='https://www.ezodproxy.com/amazon/2026/proxy'), dict(good, LinkToDetailPage='/files/doc_financials/2026/ar/2025-Shareholder-Letter-Final.pdf'), dict(good, LinkToDetailPage='https://broken]'), 3]
        f = HttpFetcher('2026-09-09')
        e = replace(self.endpoint, url='https://ir.aboutamazon.com/feed/PressRelease.svc/GetPressReleaseList')
        f._get = lambda u: (json.dumps({'GetPressReleaseListResult': [good, *bad, dict(good, LinkToDetailPage='/news-release/another-release')]}), 'application/json', u)
        r = f.fetch(e)
        self.assertEqual(r.failure, '')
        self.assertEqual(len(r.items), 2)
        self.assertEqual(len(r.article_failures), 4)
        self.assertTrue(all(x['url'].startswith('https://ir.aboutamazon.com/') for x in r.items))
