"""One-time Daily review builder. Run from any cwd; only writes beside this file."""
import argparse
from collections import Counter
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

import domestic
import overseas
import supplement

STATE = REPO.parent / 'workflow-rehearsal-daily-state'
FIELDS = ['id','stream','category','dates','subject','claim','quote','anchors','target','proposal','gap','disposition']
NOTES = [
 '日期范围以现存生产产物为界。日期没有产物或采集状态缺失，意味着覆盖未知；不能解读为没有新增。',
 '国内历史问答的累计快照与日报逐日计数不构成一一映射。只有可以归属的日期才进入观察日期列。',
 '海外同一候选跨日报重现不等于新增事件或多份独立证据；候选校验不是主张核验。',
 'Gemini 合规包含带日期的监测条目和无日期背景。纪要日期、观察日期和原始披露日期分别记录。',
]


def protected(repo):
    return {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(repo.glob('*.csv')) | set(repo.glob('*.yaml')) | set((repo/'calls').glob('*.csv')))}


def date_ok(v):
    try:
        return bool(re.fullmatch(r'20\d\d-\d\d-\d\d', v) and dt.date.fromisoformat(v))
    except (TypeError,ValueError):
        return False


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def calendar(state, cutoff):
    dr = state/'domestic/daily'; od = state/'overseas/daily'; st=state/'overseas/staging'; cd=state/'combined/daily'
    dates = {p.stem for root in (dr,od,st,cd) for p in root.iterdir() if date_ok(p.stem) and p.stem<=cutoff}
    first=dt.date.fromisoformat(min(dates)); last=dt.date.fromisoformat(cutoff)
    def status(path):
        return '有' if path.is_file() else '缺'
    result=[]
    for i in range((last-first).days+1):
        day=(first+dt.timedelta(days=i)).isoformat(); cp=cd/f'{day}.json'
        c=read(cp) if cp.is_file() else {}
        if c and c.get('run_date') != day:
            raise ValueError(f'mismatched dated report: {cp}')
        result.append(dict(date=day,domestic_report=status(dr/f'{day}.txt'),overseas_report=status(od/f'{day}.txt'),
          overseas_staging='有' if (st/day/'run-summary.json').is_file() else '缺',
          combined_report=status(cp), assembly_status=c.get('assembly_status'),collection_status=c.get('collection_status'),
          gemini_status=(c.get('gemini') or {}).get('status')))
    return result


def validate(rows,repo,cutoff):
    ids=set()
    line_counts={}
    anchor_counts=Counter()
    root_question_ids=set(re.findall(r'^  - id: ([A-Z]+\d+)\s*$',(repo/'research_questions.yaml').read_text(),re.M))
    with (repo/'points.csv').open(encoding='utf-8-sig',newline='') as f:
        points={row['point_id'] for row in csv.DictReader(f)}
    with (repo/'calls/events.csv').open(encoding='utf-8-sig',newline='') as f:
        events={row['event_id'] for row in csv.DictReader(f)}
    with (repo/'calls/themes.csv').open(encoding='utf-8-sig',newline='') as f:
        themes={row['theme_id'] for row in csv.DictReader(f)}
    for r in rows:
        assert all(k in r for k in FIELDS), r.keys()
        rid=r['id']
        assert rid not in ids and re.fullmatch(r'[DOG]-[a-zA-Z0-9_-]+',rid), rid
        ids.add(rid)
        assert all(isinstance(r[k],str) and r[k].strip() for k in ('stream','category','subject','claim','target','proposal','gap','disposition')), rid
        assert isinstance(r['quote'],str) and isinstance(r['anchors'],list) and r['anchors'], rid
        assert isinstance(r['dates'],list) and all(date_ok(d) and d<=cutoff for d in r['dates']), rid
        r['dates']=sorted(set(r['dates']))
        for q in re.findall(r'\b(?:PQ|TQ|WQ|RQ)\d+\b',r['target']):
            assert q in root_question_ids,(rid,q)
        for pattern, values in [(r'\bpoints\.csv (P\d+)\b',points),(r'\bEV\d+\b',events),(r'\bcalls/themes\.csv · (T\d+)\b',themes)]:
            for ref_id in re.findall(pattern,r['target']):
                assert ref_id in values,(rid,ref_id)
        for a in r['anchors']+r.get('target_anchors',[]):
            assert a.get('label') and a.get('ref'), (rid,a)
            ref=a['ref']
            if ref.startswith(('http://','https://')):
                assert urlsplit(ref).hostname, (rid,ref)
                anchor_counts['web_reference']+=1
            elif ref.startswith('/'):
                # Allow a # locator, but prefer an exact path where a filename itself has #.
                path=Path(ref)
                if not path.is_file() and '#' in ref: path=Path(ref.split('#',1)[0])
                assert path.is_file(),(rid,ref)
                m=re.search(r'#L(\d+)(?:-L?(\d+))?$',ref)
                if m:
                    if path not in line_counts:
                        with path.open('rb') as f:
                            line_counts[path]=sum(1 for _ in f)
                    start=int(m[1]); end=int(m[2] or m[1])
                    assert 1<=start<=end<=line_counts[path],(rid,ref)
                    anchor_counts['valid_line_reference']+=1
                anchor_counts['existing_local_reference']+=1
            else:
                raise AssertionError((rid,ref))
    return dict(anchor_counts)


def dump(p,value):
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cutoff',default='2026-11-09')
    opts=parser.parse_args()
    assert date_ok(opts.cutoff)
    before=protected(REPO)
    rows=[]; audit={}
    for name,collector in [('国内',domestic),('海外',overseas),('补充',supplement)]:
        picked, coverage=collector.collect(REPO,STATE,opts.cutoff)
        rows.extend(picked)
        audit[name]=coverage
    anchors=validate(rows,REPO,opts.cutoff)
    priority={'待逐条复核':4,'待定位':3,'缺锚点':2,'仅作线索':1}
    rows.sort(key=lambda r:(priority.get(r['disposition'],0),r['dates'][-1] if r['dates'] else '',r['id']),reverse=True)
    calendar_rows=calendar(STATE,opts.cutoff)
    coverage={'cutoff':opts.cutoff,'notes':NOTES,'calendar':calendar_rows,'streams':audit,
              'counts':dict(Counter(r['stream'] for r in rows)),
              'disposition_counts':dict(Counter(r['disposition'] for r in rows))}
    payload={'cutoff':opts.cutoff,'$rows':rows,'$coverage':{k:coverage[k] for k in ('notes','calendar')}}
    safe=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(HERE/'review-template.html').read_text()
    assert template.count('__PAYLOAD__')==1
    (HERE/'review.html').write_text(template.replace('__PAYLOAD__',safe),encoding='utf-8')
    dump(HERE/'review.json',rows)
    dump(HERE/'coverage.json',coverage)
    with (HERE/'review.csv').open('w',encoding='utf-8-sig',newline='') as f:
        extra=['target_anchors','date_basis','publication_date','source_entry_date','topics']
        w=csv.DictWriter(f,fieldnames=FIELDS+extra+['review_decision','review_note'])
        w.writeheader()
        for r in rows:
            cells={}
            for k in FIELDS+extra:
                v=r.get(k,'')
                cells[k]=json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v
            # Protect spreadsheet viewers from source-controlled formula cells.
            w.writerow({k:"'"+v if v.lstrip().startswith(('=','+','-','@')) else v for k,v in cells.items()})
    assert before==protected(REPO),'protected ledgers changed during review build'
    assert read(HERE/'review.json')==rows
    embedded=re.search(r'<script type="application/json" id="payload">(.*?)</script>',(HERE/'review.html').read_text(),re.S)
    assert json.loads(embedded[1])==payload
    with (HERE/'review.csv').open(encoding='utf-8-sig',newline='') as f:
        assert [x['id'] for x in csv.DictReader(f)]==[r['id'] for r in rows]
    result={'rows':len(rows),'by_stream':coverage['counts'],'protected_files_unchanged':len(before),'anchor_refs':anchors,
            'days_in_range':len(calendar_rows),'combined_days':sum(x['combined_report']=='有' for x in calendar_rows)}
    dump(HERE/'verification.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
