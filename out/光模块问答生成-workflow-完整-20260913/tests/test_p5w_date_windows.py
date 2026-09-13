"""Date-window behavior of the official P5W question-list adapter."""
import datetime
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class Response:
    def __init__(self, payload=None, text=''):
        self.payload = payload
        self.text = text

    def json(self):
        return self.payload


class P5WDateWindowTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('p5w_window_test', Path(__file__).resolve().parents[1] / 'corpus/_fetch_qa.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.module.ROOT = self.temp.name

    def test_recent_window_is_sent_before_requesting_history(self):
        requests = []
        def request(method, url, **kwargs):
            if '/c/' in url:
                return Response(text='id="pid" value="P123"')
            data = kwargs['data']
            requests.append(data)
            if len(requests) == 1:
                self.assertEqual(data.get('questionerTimeBegin'), '2026-08-29')
                self.assertEqual(data.get('questionerTimeEnd'), datetime.date.today().isoformat())
            return Response({'rows': [], 'total': 0})
        with patch.object(self.module, 'request', side_effect=request):
            self.assertEqual(self.module.fetch_p5w('000988', '2026-08-29'), 0)
        self.assertEqual(len(requests), 2)  # date query plus latest-reply coverage check
        self.assertFalse(self.module._trunc['v'])

    def run_source(self, handler, since, until):
        def request(method, url, **kwargs):
            if '/c/' in url:
                return Response(text='id="pid" value="P123"')
            return Response(handler(kwargs['data']))
        with patch.object(self.module, 'request', side_effect=request):
            return self.module.fetch_p5w('000988', since, until)

    @staticmethod
    def row(key, ask, reply=None):
        return {'pid':key, 'companyShortname':'测试公司', 'content':'问题',
                'replyContent':'公司回答', 'questionerTimeStr':ask,
                'replyerTimeStr':reply or ask}

    def filtered_source(self, rows, requests):
        def timestamp(value):
            value=datetime.datetime.fromisoformat(value)
            return value
        def handler(data):
            requests.append(dict(data))
            begin=data.get('questionerTimeBegin');end=data.get('questionerTimeEnd')
            def within(row):
                ask=timestamp(row['questionerTimeStr'])
                lower=timestamp(begin) if begin else datetime.datetime.min
                upper=timestamp(end) if end else datetime.datetime.max
                if end and len(end)==10:upper+=datetime.timedelta(days=1)-datetime.timedelta(microseconds=1)
                return lower<=ask<=upper
            selected=sorted([r for r in rows if within(r)],key=lambda r:r['replyerTimeStr'],reverse=True)
            total=min(len(selected),100)
            return {'success':True,'total':total,'rows':selected[:100][data['page']*10:(data['page']+1)*10]}
        return handler

    def test_busy_day_splits_times_and_preserves_boundary_record_once(self):
        rows=[self.row(str(i),'2026-07-09 09:00:00') for i in range(50)]
        rows+=[self.row('boundary','2026-07-09 12:00:00')]
        rows+=[self.row(str(i),'2026-07-09 15:00:00') for i in range(50,101)]
        requests=[]
        self.assertEqual(self.run_source(self.filtered_source(rows,requests),'2026-07-09','2026-07-09'),102)
        self.assertFalse(self.module._trunc['v'])
        self.assertTrue(any(len(d.get('questionerTimeBegin',''))>10 for d in requests))
        saved=(Path(self.temp.name)/'corpus/qa/000988/qa.jsonl').read_text().splitlines()
        self.assertEqual(sum(json.loads(r)['index_id']=='boundary' for r in saved),1)

    def test_old_question_guard_filters_prior_ask_dates_and_splits_cap(self):
        rows=[self.row(str(i),'2026-07-01 09:00:00','2026-08-07 15:00:00') for i in range(60)]
        rows+=[self.row(str(i),'2026-07-02 09:00:00','2026-08-07 15:00:00') for i in range(60,120)]
        requests=[]
        self.assertEqual(self.run_source(self.filtered_source(rows,requests),'2026-08-07','2026-08-07'),120)
        self.assertFalse(self.module._trunc['v'])
        self.assertTrue(all(d.get('questionerTimeEnd') for d in requests))

    def test_old_question_new_reply_is_preserved(self):
        row = self.row('old-question', '2026-05-19', '2026-05-20')
        def handler(data):
            return {'total':0, 'rows':[]} if data.get('questionerTimeBegin') else {'total':1,'rows':[row]}
        self.assertEqual(self.run_source(handler, '2026-05-20', '2026-05-20'), 1)
        self.assertFalse(self.module._trunc['v'])
        saved = json.loads((Path(self.temp.name)/'corpus/qa/000988/qa.jsonl').read_text())
        self.assertEqual((saved['ask_date'], saved['answer_date']), ('2026-05-19','2026-05-20'))

    def test_exact_filtered_total_stops_before_repeated_extra_page(self):
        rows = [self.row(str(i), '2026-08-07') for i in range(11)]
        pages = []
        def handler(data):
            pages.append((bool(data.get('questionerTimeBegin')), data['page']))
            self.assertLess(data['page'], 2)
            if not data.get('questionerTimeBegin'):return {'total':0,'rows':[]}
            return {'total':11, 'rows':rows[data['page']*10:(data['page']+1)*10]}
        self.assertEqual(self.run_source(handler, '2026-08-07','2026-08-07'),11)
        self.assertFalse(self.module._trunc['v'])
        self.assertEqual(pages, [(True,0),(True,1),(False,0)])

    def test_capped_interval_is_split_not_treated_as_all_history(self):
        a = self.row('a','2026-08-06')
        b = self.row('b','2026-08-07')
        ranges = []
        def handler(data):
            begin,end=data.get('questionerTimeBegin'),data.get('questionerTimeEnd')
            if begin:
                ranges.append((begin,end))
                if begin!=end:return {'total':100,'rows':[b,a]}
                return {'total':1,'rows':[a if begin=='2026-08-06' else b]}
            return {'total':0,'rows':[]}
        self.assertEqual(self.run_source(handler,'2026-08-06','2026-08-07'),2)
        self.assertFalse(self.module._trunc['v'])
        self.assertEqual(set(ranges),{('2026-08-06','2026-08-07'),('2026-08-06','2026-08-06'),('2026-08-07','2026-08-07')})

    def test_minimum_time_window_cap_preserves_rows_but_stays_incomplete(self):
        rows=[self.row(str(i),'2026-08-07 09:00:00') for i in range(100)]
        # Allow the full descent to a one-second query and its ten result pages.
        self.module.MAX_PAGES=60
        self.assertEqual(self.run_source(self.filtered_source(rows,[]),'2026-08-07','2026-08-07'),100)
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('100',self.module._trunc['reason'])

    def test_capped_old_questions_cannot_hide_a_request_budget_failure(self):
        rows=[self.row(str(i),'2026-07-01 09:00:00','2026-08-07 15:00:00') for i in range(100)]
        self.module.MAX_PAGES=3
        self.assertEqual(self.run_source(self.filtered_source(rows,[]),'2026-08-07','2026-08-07'),10)
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('请求上限',self.module._trunc['reason'])

    def test_latest_reply_boundary_prevents_scanning_old_twenty_pages(self):
        count=[]
        def handler(data):
            count.append(data)
            if data.get('questionerTimeBegin'):return {'total':0,'rows':[]}
            self.assertEqual(data['page'],0)
            return {'total':100,'rows':[self.row('old','2026-08-07')]}
        self.assertEqual(self.run_source(handler,'2026-08-29','2026-09-11'),0)
        self.assertEqual(len(count),2)
        self.assertFalse(self.module._trunc['v'])

    def test_request_failure_after_a_page_preserves_completed_rows(self):
        rows=[self.row(str(i),'2026-08-07') for i in range(10)]
        def handler(data):
            if data['page']:raise ConnectionError('network down')
            return {'total':11,'rows':rows}
        with self.assertRaises(ConnectionError):self.run_source(handler,'2026-08-07','2026-08-07')
        self.assertEqual(len((Path(self.temp.name)/'corpus/qa/000988/qa.jsonl').read_text().splitlines()),10)

    def test_budget_exhausted_before_latest_reply_check_is_incomplete(self):
        with patch.object(self.module, 'MAX_PAGES', 1):
            self.run_source(lambda data: {'total':0,'rows':[]}, '2026-08-07','2026-08-07')
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('上限', self.module._trunc['reason'])

    def test_unordered_latest_replies_cannot_establish_date_boundary(self):
        rows=[self.row('old','2026-08-01'),self.row('new','2026-08-01','2026-08-07')]
        def handler(data):
            return {'total':0,'rows':[]} if data.get('questionerTimeBegin') else {'total':100,'rows':rows}
        self.assertEqual(self.run_source(handler,'2026-08-07','2026-08-07'),1)
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('倒序',self.module._trunc['reason'])

    def test_total_changing_mid_query_keeps_rows_but_is_incomplete(self):
        rows=[self.row(str(i),'2026-08-07') for i in range(12)]
        def handler(data):
            return {'total':11 if data['page']==0 else 12,
                    'rows':rows[data['page']*10:(data['page']+1)*10]}
        self.assertEqual(self.run_source(handler,'2026-08-07','2026-08-07'),12)
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('总数改变',self.module._trunc['reason'])

    def test_real_huagong_capture_retains_all_69_records(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/p5w/huagong-20260807.json').read_text())
        def key(data):return (data.get('questionerTimeBegin'),data.get('questionerTimeEnd'),data['page'])
        responses={key(x['data']):x['response'] for x in fixture['requests']}
        expected={str(row['pid']) for x in fixture['requests'] if x['data'].get('questionerTimeBegin') for row in x['response']['rows']}
        def replay(data):
            # This fixture covers the seven filtered pages. Older-question
            # responses are separately exercised by the late-reply tests.
            if not data.get('questionerTimeBegin'):return {'total':0,'rows':[]}
            return responses[key(data)]
        self.assertEqual(self.run_source(replay,'2026-08-07','2026-08-07'),69)
        self.assertFalse(self.module._trunc['v'])
        saved=[json.loads(line) for line in (Path(self.temp.name)/'corpus/qa/000988/qa.jsonl').read_text().splitlines()]
        self.assertEqual({row['index_id'] for row in saved},expected)
        self.assertEqual(len(saved),69)

    def test_bad_envelope_and_ignored_filter_cannot_be_successful_empty(self):
        for payload in ({'success':False,'total':0,'rows':[]}, {'total':0},
                        {'total':1,'rows':[self.row('outside','2026-01-01')]}):
            with self.subTest(payload=payload):
                self.module._trunc.update(v=False,reason='')
                self.run_source(lambda data:payload,'2026-08-07','2026-08-07')
                self.assertTrue(self.module._trunc['v'])

    def test_real_native_capture_includes_two_old_questions_answered_on_may20(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/p5w/fushida-20260520.json').read_text())
        def key(data):return (data.get('questionerTimeBegin'),data.get('questionerTimeEnd'),data['page'])
        responses={key(x['data']):x['response'] for x in fixture['requests']}
        self.assertEqual(self.run_source(lambda data:responses[key(data)],'2026-05-20','2026-05-20'),35)
        self.assertFalse(self.module._trunc['v'])
        saved=[json.loads(line) for line in (Path(self.temp.name)/'corpus/qa/000988/qa.jsonl').read_text().splitlines()]
        late={r['index_id'] for r in saved if r['ask_date']<'2026-05-20'}
        self.assertEqual(late,{'e74db67b4a7349109254932cf57b3a7b','5f4c4690af244e9192da224f62edbd87'})

    def test_ignored_subday_filter_is_incomplete_even_if_the_day_matches(self):
        rows=[self.row(str(i),'2026-07-09 09:00:00') for i in range(100)]
        def handler(data):
            if not data.get('questionerTimeBegin'):return {'total':0,'rows':[]}
            return {'total':100,'rows':rows[data['page']*10:(data['page']+1)*10]}
        self.run_source(handler,'2026-07-09','2026-07-09')
        self.assertTrue(self.module._trunc['v'])
        self.assertIn('时间筛选未生效',self.module._trunc['reason'])


if __name__ == '__main__':
    unittest.main()
