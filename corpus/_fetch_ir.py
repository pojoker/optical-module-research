#!/usr/bin/env python3
"""车道F：巨潮"投资者关系活动记录表"抓取（投关表=法定披露件，T1）。

用法: python3 corpus/_fetch_ir.py <代码...> [--since 2024-01-01] [--top 2]
约定:
- 类别码 category_dyhd_szdy + tabName=relation（2026-07-30 codex 探得），标题须含"投资者关系"。
- 落盘 corpus/ir/<代码>/，每家取最近 top 份；已有有效 PDF 跳过（纪律:空目录不如实建）。
- 限速 ≥1.2s；PDF 校验 %PDF 头 + pdftotext 非空；失败/未找到如实打印，不伪造。
"""
import argparse, os, re, subprocess, sys, time
import importlib.util

spec = importlib.util.spec_from_file_location('_fetch', os.path.join(os.path.dirname(__file__), '_fetch.py'))
fetch = importlib.util.module_from_spec(spec); sys.modules['_fetch'] = fetch; spec.loader.exec_module(fetch)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _solve_dfcfw(session, url):
    """东财 pdf.dfcfw.com 反爬挑战: 解析 __tst_status(三数求和)+EO_Bot_Ssid 后重取。"""
    EH = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://data.eastmoney.com/', 'Origin': ''}
    r = session.get(url, headers=EH, timeout=30)
    if r.content[:5] == b'%PDF-':
        return r
    txt = r.text
    w = re.search(r'WTKkN:(\d+)', txt); b = re.search(r'bOYDu:(\d+)', txt); y = re.search(r'wyeCN:(\d+)', txt)
    arg = re.search(r't=a\[_0x649a\("0x7"\)\]\(t,(\d+)\)', txt)
    if not (w and b and y and arg):
        return r
    tst = int(w.group(1)) + int(b.group(1)) + int(y.group(1))
    session.cookies.set('__tst_status', f'{tst}#', domain='pdf.dfcfw.com')
    session.cookies.set('EO_Bot_Ssid', arg.group(1), domain='pdf.dfcfw.com')
    time.sleep(1.2)
    return session.get(url, headers=EH, timeout=120)

def query_ir_em(session, code, since):
    """东财兜底: 巨潮对沪市投关表收录不全(2026-07-30实测), 东财公告API标题检索。"""
    r = session.get('https://np-anotice-stock.eastmoney.com/api/security/ann',
        params={'sr': '-1', 'page_size': '100', 'page_index': '1', 'ann_type': 'A',
                'client_source': 'web', 'stock_list': code, 'f_node': '0', 's_node': '0'},
        headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://data.eastmoney.com/', 'Origin': ''}, timeout=20)
    r.raise_for_status()
    hits = []
    for it in (r.json().get('data') or {}).get('list') or []:
        t = it.get('title', '')
        if '投资者关系活动记录表' not in t:
            continue
        d = (it.get('notice_date') or '')[:10]
        if d < since:
            continue
        hits.append((d, t, f"https://pdf.dfcfw.com/pdf/H2_{it['art_code']}_1.pdf"))
    return sorted(hits, reverse=True)


def query_ir(session, code, since, today):
    payload = {
        'pageNum': '1', 'pageSize': '30', 'column': '', 'tabName': 'relation', 'plate': '',
        'stock': '', 'searchkey': code, 'secid': '', 'category': 'category_dyhd_szdy', 'trade': '',
        'seDate': f'{since}~{today}', 'sortName': '', 'sortType': '', 'isHLtitle': 'true',
    }
    hits = []
    # 主通道: 调研类别(category_dyhd_szdy 仅覆盖深市); 兜底: 全文检索(沪市/北交所投关表只能这么命中)
    for column in ('szse', 'sse', 'bj'):
        payload['column'] = column
        r = session.post(fetch.QUERY_URL, data=payload, timeout=40)
        r.raise_for_status()
        for a in r.json().get('announcements') or []:
            if str(a.get('secCode') or '') != code:
                continue
            title = fetch.clean_html_title(str(a.get('announcementTitle') or ''))
            if '投资者关系' not in title:
                continue
            url = str(a.get('adjunctUrl') or '')
            if not url.lower().endswith('.pdf'):
                continue
            hits.append((fetch.parse_announcement_date(a.get('announcementTime')), title, url))
        time.sleep(1.3)
    if not hits:
        fb = dict(payload, tabName='fulltext', category='')
        for column in ('szse', 'sse', 'bj'):
            fb['column'] = column
            r = session.post(fetch.QUERY_URL, data=fb, timeout=40)
            r.raise_for_status()
            for a in r.json().get('announcements') or []:
                if str(a.get('secCode') or '') != code:
                    continue
                title = fetch.clean_html_title(str(a.get('announcementTitle') or ''))
                if '投资者关系' not in title:
                    continue
                url = str(a.get('adjunctUrl') or '')
                if not url.lower().endswith('.pdf'):
                    continue
                hits.append((fetch.parse_announcement_date(a.get('announcementTime')), title, url))
            time.sleep(1.3)
    # 去重+按日期倒序
    seen, out = set(), []
    for h in sorted(hits, reverse=True):
        if h[2] in seen:
            continue
        seen.add(h[2]); out.append(h)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('codes', nargs='+')
    ap.add_argument('--since', default='2024-01-01')
    ap.add_argument('--top', type=int, default=2)
    ns = ap.parse_args()
    today = time.strftime('%Y-%m-%d')
    session = fetch.build_session()
    summary = []
    for code in ns.codes:
        try:
            hits = query_ir(session, code, ns.since, today)
            if not hits:
                hits = query_ir_em(session, code, ns.since)
                if hits:
                    print(f'[{code}] 巨潮0命中,东财兜底{len(hits)}份')
        except Exception as exc:
            print(f'[{code}] 查询失败: {exc}'); summary.append((code, '查询失败')); continue
        got = 0
        for d, title, url in hits[: ns.top]:
            base = fetch.sanitize_filename(f'{code}_{d}_{title}')
            dst_pdf = os.path.join(ROOT, 'corpus', 'ir', code, base + '.pdf')
            dst_docx = os.path.join(ROOT, 'corpus', 'ir', code, base + '.docx')
            if (os.path.exists(dst_pdf) and os.path.getsize(dst_pdf) > 20000) or \
               (os.path.exists(dst_docx) and os.path.getsize(dst_docx) > 5000):
                got += 1; continue
            os.makedirs(os.path.dirname(dst_pdf), exist_ok=True)
            try:
                if url.startswith('http'):
                    r = _solve_dfcfw(session, url) if 'dfcfw' in url else session.get(url, timeout=60)
                else:
                    full = fetch.build_pdf_url(url)
                    r = session.get(full, headers={'Referer': 'https://www.cninfo.com.cn/'}, timeout=60)
                if r.content.startswith(b'%PDF'):
                    dst = dst_pdf
                    with open(dst, 'wb') as f:
                        f.write(r.content)
                    chk = dst + '.chk'
                    subprocess.run(['pdftotext', '-layout', dst, chk], capture_output=True)
                    ok = os.path.exists(chk) and os.path.getsize(chk) > 200
                    if os.path.exists(chk):
                        os.remove(chk)
                elif r.content[:2] == b'PK':
                    # 东财托管的 docx 原件(沪市投关表常见): 存原件+stdlib解出纯文本快照
                    dst = dst_docx
                    with open(dst, 'wb') as f:
                        f.write(r.content)
                    import zipfile
                    with zipfile.ZipFile(dst) as z:
                        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
                    text = re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml))
                    with open(dst + '.txt', 'w', encoding='utf-8') as f:
                        f.write(text)
                    ok = len(text) > 200
                else:
                    raise ValueError('非PDF/DOCX')
                if not ok:
                    os.remove(dst); raise ValueError('文本抽出为空')
                got += 1
            except Exception as exc:
                print(f'[{code}] 下载失败 {d}: {exc}')
            time.sleep(1.3)
        print(f'[{code}] 命中{len(hits)}份 取{min(len(hits), ns.top)} 实得{got}')
        summary.append((code, f'命中{len(hits)} 实得{got}'))
        time.sleep(1.5)
    print('\n== 汇总 ==')
    for c, s in summary:
        print(c, s)

if __name__ == '__main__':
    main()
