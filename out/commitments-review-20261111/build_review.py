"""Render nine existing commitments and the evidence proposed for human review."""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AS_OF = '2026-11-11'
LABELS = {
    'fulfilled':'已兑现',
    'delayed':'明确延期',
    'pending':'未到期，继续跟踪',
    'not_observed':'到期但缺兑现证据',
    'partially_supported':'部分进展，兑现仍缺证',
    'partially_fulfilled':'部分兑现',
    'withdrawn':'已撤回',
}


def read_csv(name):
    with (ROOT/'calls'/name).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def text(value):
    return html.escape(str(value),quote=True)


def display(value):
    return '；'.join(str(v) for v in value) if isinstance(value,list) else str(value)


def load_rows():
    original={r['commitment_id']:r for r in read_csv('commitments.csv')}
    claims={r['claim_id']:r for r in read_csv('claims.csv')}
    sources={r['source_id']:r for r in read_csv('sources.csv')}
    assembled={}
    for part in ('cisco-aaoi','nokia','ciena'):
        for row in json.loads((HERE/f'{part}.json').read_text()):
            key=row['id']
            assert key in original and key not in assembled,key
            assert row['verdict'] in LABELS,(key,row['verdict'])
            old=original[key]
            assert row['due_date']==old['due_date'],(key,row['due_date'])
            assert row['old_status']==old['status'],key
            assert row['assessment'] and row['missing'] and row['proposal'] and row['positions'] and row['search'],key
            claim=claims[old['claim_id']]
            source=sources[claim['source_id']]
            row['original']={'claim_id':old['claim_id'],'source_id':source['source_id'],'date':source['published_date'],'url':source['url'],'quote':claim['quote'],'locator':claim['anchor']}
            row['checked_at']=AS_OF
            assert row['evidence'],key
            for e in row['evidence']:
                assert e['url'].startswith(('https://','http://')) and e['locator'] and e['title'],(key,e)
            for d in row['daily']:
                ref=d['ref'].split('#',1)[0]
                assert Path(ref).is_file(),(key,d)
                assert d['match'],(key,d)
            assembled[key]=row
    assert assembled.keys()==original.keys()
    before=json.loads((HERE/'ledger-fingerprints.json').read_text())
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in before.items())
    seen_quotes = {}
    for key in sorted(assembled):
        for evidence in assembled[key]['evidence']:
            url = evidence['url']
            quote = evidence.get('quote','')
            if url in seen_quotes:
                evidence['quote'] = ''
                evidence['quote_reference'] = seen_quotes[url]
            else:
                words = quote.split()
                if len(words) > 20:
                    evidence['quote'] = ' '.join(words[:20]) + '…'
                seen_quotes[url] = key
    return [assembled[k] for k in sorted(assembled)]


def source_line(e):
    if e.get('quote_reference'):
        suffix=f'<a href="#{e["quote_reference"]}">短引见 {e["quote_reference"]}</a>'
    else:
        suffix=f'<q>{text(e.get("quote",""))}</q>'
    return f'<li><b>{text(e["date"])}</b> · {text(e["locator"])} · <a href="{text(e["url"])}" target="_blank" rel="noopener">{text(e["title"])}</a><br>{suffix}</li>'


def card(row):
    o=row['original']
    original=f'<p>{text(o["date"])} · {text(o["claim_id"])} · {text(o["locator"])} · <a href="{text(o["url"])}">最初披露</a></p><blockquote>{text(o["quote"])}</blockquote>'
    fields=[('核查结果',row['assessment']),('缺证与判断边界',row['missing']),('建议更新内容',row['proposal']),('建议位置',display(row['positions']))]
    details=''.join(f'<dt>{text(k)}</dt><dd>{text(v)}</dd>' for k,v in fields)
    events=''.join(f'<li><b>观察日 {text(d["date"])}</b> · {text(d["claim"])}<br>{text(d["match"])}<br>披露日期 {text(d.get("published_date","待核"))} · 留存观察日 {text("、".join(d.get("observed_dates",[d["date"]])))}<br><code>{text(d["ref"])}</code>'+ (f'<br><a href="{text(d["url"])}">候选原始链接</a>' if d.get('url') else '')+'</li>' for d in row['daily'])
    if not events:
        events='<li>所查 Daily 中未定位到同对象事件，检索词与范围见下。</li>'
    trail=''.join(f'<li>{text(x)}</li>' for x in row['search'])
    return f'<article id="{row["id"]}"><h2>{row["id"]} · {text(LABELS[row["verdict"]])}</h2><h3>{text(row["target"])}</h3><p>账本目标窗口 {text(row["due_date"])} · 原状态 {text(row["old_status"])}</p>{original}<dl>{details}</dl><h3>后续原始披露</h3><ul>{"".join(source_line(e) for e in row["evidence"])}</ul><details><summary>相关 Daily 观察 {len(row["daily"])} 项</summary><ul>{events}</ul></details><details><summary>检索范围和路径</summary><ul>{trail}</ul></details></article>'


def main():
    rows=load_rows()
    (HERE/'review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    columns=['id','target','due_date','old_status','verdict','assessment','missing','proposal','positions','evidence','daily','search','decision','decision_note']
    with (HERE/'review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(list,dict)) else row.get(k,'') for k in columns})
    summary=' · '.join(f'{LABELS[k]} {v} 条' for k,v in Counter(r['verdict'] for r in rows).items())
    table=''.join(f'<tr><td><a href="#{r["id"]}">{r["id"]}</a></td><td>{text(r["target"])}</td><td>{text(r["due_date"])}</td><td>{text(LABELS[r["verdict"]])}</td></tr>' for r in rows)
    page=(HERE/'template.html').read_text().replace('__COUNTS__',text(summary)).replace('__TABLE__',table).replace('__CARDS__',''.join(card(r) for r in rows))
    (HERE/'index.html').write_text(page,encoding='utf-8')
    print(summary)


if __name__=='__main__':
    main()
