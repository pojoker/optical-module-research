"""Render the fixed 37-row Gemini compliance review for manual decisions."""
from collections import Counter
import csv
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
CHECKED = '2026-11-10'
PARTS = ('core', 'fcc', 'domestic', 'overseas')
# Set only after checking the suggested edit against an existing ledger item.
POINT_UPDATES = {
    'G-cf34d3f9017c9f88': ('P031', '景旺电子', '只审批景旺电子 2026 年上半年已批量交付 800G、1.6T 光模块 PCB 的发行人自述。'),
    'G-c0308a66e32bf867': ('P209', '华工科技', '只审批华工科技 10 月 30 日自述泰国工厂 800G LPO 月出货约 10 万只，以及同次交流中的 1.6T LPO 送样口径。'),
}
BUCKETS = ('可提交正式账本复核', '一手事实可留存 · 正式位置待定', '缺证或归并')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def merged_rows():
    original = {r['id']: r for r in load(HERE.parent/'review.json') if r['stream']=='Gemini 合规'}
    assert len(original)==37
    decisions = {}
    for part in PARTS:
        for row in load(HERE/f'{part}.json'):
            key = row['id']
            assert key in original and key not in decisions, key
            assert row['verdict'] and row['missing'] and row['target'] and row['search'], key
            for item in row['evidence']:
                assert item['title'] and item['locator'] and urlsplit(item['url']).scheme in ('http', 'https')
            if row['proposal']:
                assert any(e['quote'] for e in row['evidence']), key
            source = original[key]
            decisions[key] = {
                **row, 'checked':CHECKED, 'source_entry_date':source['source_entry_date'],
                'original_claim':source['claim'], 'original_anchors':source['anchors'], 'topics':source['topics'],
                'bucket':BUCKETS[0] if key in POINT_UPDATES else BUCKETS[1] if row['proposal'] else BUCKETS[2],
            }
    assert decisions.keys()==original.keys(), original.keys()-decisions.keys()
    with (HERE.parents[2]/'points.csv').open(encoding='utf-8-sig') as f:
        points = {r['point_id']:r['公司'] for r in csv.DictReader(f)}
    for key,(point,company,scope) in POINT_UPDATES.items():
        row=decisions[key]
        assert points[point]==company and point in row['target'] and row['proposal']
        row['approval_scope'] = scope
    return sorted(decisions.values(), key=lambda r: (BUCKETS.index(r['bucket']),r['source_entry_date'] or '9999',r['id']))


def esc(text):
    return html.escape(str(text),quote=True)


def card(row):
    fields = [('原线索',row['original_claim']), ('核实到的内容',row['confirmed']),
              ('缺证、纠正或适用边界',row['missing']), ('建议写入或保留的文字',row['proposal']),
              ('建议位置',row['target'])]
    if row.get('approval_scope'):
        fields.append(('可单独批准的范围',row['approval_scope']))
    body = ''.join(f'<dt>{esc(key)}</dt><dd>{esc(value) if value else "—"}</dd>' for key,value in fields)
    sources = []
    for e in row['evidence']:
        quote=f' <q>{esc(e["quote"])}</q>' if e['quote'] else ''
        sources.append(f'<li><a href="{esc(e["url"])}" target="_blank" rel="noopener">{esc(e["title"])}</a> · {esc(e["locator"])}{quote}</li>')
    trace = ''.join(f'<li>{esc(query)}</li>' for query in row['search'])
    original = ''.join(f'<li>{esc(a["label"])} · {esc(a["ref"])}</li>' for a in row['original_anchors'])
    return (f'<article id="{esc(row["id"])}"><h3>{esc(row["id"])}</h3>'
            f'<p>{esc(row["verdict"])} · {esc(row["source_entry_date"] or "背景，无纪要日期")} · {esc("、".join(row["topics"]))}</p>'
            f'<dl>{body}</dl><h4>原文依据</h4><ul>{"".join(sources) or "<li>暂缺可定位一手原文</li>"}</ul>'
            f'<details><summary>检索路径与 Gemini 原始位置</summary><ul>{trace}{original}</ul></details></article>')


def main():
    rows=merged_rows()
    counts=Counter(r['bucket'] for r in rows)
    (HERE/'audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=('id','bucket','verdict','source_entry_date','checked','original_claim','confirmed','missing','proposal','target','approval_scope','evidence','search','decision','decision_note')
    with (HERE/'audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),list) else r.get(k,'') for k in fields})
    summary=' · '.join(f'{b} {counts[b]} 条' for b in BUCKETS)
    sections=''.join(f'<section><h2>{esc(b)}（{counts[b]}）</h2>'+''.join(card(r) for r in rows if r['bucket']==b)+'</section>' for b in BUCKETS)
    template=(HERE/'audit-template.html').read_text(encoding='utf-8')
    page=template.replace('__COUNTS__',esc(summary)).replace('__CARDS__',sections)
    (HERE/'index.html').write_text(page,encoding='utf-8')
    print(dict(counts))


if __name__=='__main__':
    main()
