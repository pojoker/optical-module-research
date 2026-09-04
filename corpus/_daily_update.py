#!/usr/bin/env python3
"""日更脚本(纯脚本零token,纪律2): 投关表/互动易/公告流三增量 + scan召回差分 + 待判/待确认重启监视 + 一页日报。
用法: python3 corpus/_daily_update.py   (产出 tmp/daily/YYYY-MM-DD.md + tmp/daily/queue-latest.txt)
重启监视清单: corpus/_restart_watchlist.csv(2026-08-22起); 本脚本只做机械匹配, 命中后由pi/codebuddy起草证据链、判定闸复核。
"""
import csv, datetime, glob, json, os, re, subprocess, sys, time
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location('_fetch', 'corpus/_fetch.py')
fetch = importlib.util.module_from_spec(spec); sys.modules['_fetch'] = fetch; spec.loader.exec_module(fetch)
spec2 = importlib.util.spec_from_file_location('_fetch_ir', 'corpus/_fetch_ir.py')
fir = importlib.util.module_from_spec(spec2); sys.modules['_fetch_ir'] = fir; spec2.loader.exec_module(fir)
spec3 = importlib.util.spec_from_file_location('_fetch_qa', 'corpus/_fetch_qa.py')
fqa = importlib.util.module_from_spec(spec3); sys.modules['_fetch_qa'] = spec3.loader and fqa
sys.modules['_fetch_qa'] = fqa; spec3.loader.exec_module(fqa)

TODAY = datetime.date.today().isoformat()
DAY3 = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
DAY14 = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
KW = re.compile(r'光模块|光通信|光器件|光引擎|光芯片|CPO|硅光|800G|1\.6T|相干|LPO|TOSA|ROSA|BOSA|FAU|MPO|AWG|DFB|EML|VCSEL|隔离器|插芯|耦合|固晶|贴片|键合|外延|MOCVD|磷化铟|InP', re.I)

frozen = {}
with open('corpus/_frozen.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        frozen[r['代码']] = r['名称']

# 功能3: 待判/待确认重启监视清单(2026-08-22起; C+E队列的重启条件机械化盯梢)
WATCH = []
if os.path.exists('corpus/_restart_watchlist.csv'):
    with open('corpus/_restart_watchlist.csv', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            try:
                r['_pat'] = re.compile(r['触发词'], re.I)
            except re.error:
                continue
            WATCH.append(r)
WATCH_DAILY = [w for w in WATCH if w['车道'] == '日更' and w['代码']]

def watched_codes():
    """待判行公司 ∪ 全部已入点公司(生产中+在建, 宇宙内) ∪ 重启监视清单(日更车道)——2026-08-15起从在建/待判扩到全量已入点"""
    codes = set()
    for r in csv.DictReader(open('triage.csv', encoding='utf-8-sig')):
        if r['处置'] == '待判':
            for c, n in frozen.items():
                if n == r['公司']:
                    codes.add(c)
    for r in csv.DictReader(open('points.csv', encoding='utf-8-sig')):
        if r['状态'] in ('生产中', '在建'):
            for c, n in frozen.items():
                if n == r['公司']:
                    codes.add(c)
    for w in WATCH_DAILY:
        codes.add(w['代码'])
    return sorted(codes)

session = fetch.build_session()
digest = {'ir_new': [], 'qa_new': [], 'ann': [], 'q_delta_new': [], 'q_delta_gone': []}
new_ir_txt = []  # (code, 公司, title, txt路径)——供重启监视内容级匹配
log_lines = []  # 静默降级: 网络/解析异常记一行, 不拖垮主流程
FOUR = {'半导体', '光学光电子', '通信设备', '元件'}  # 申万四行业分母
CNINFO_API = 'https://webapi.cninfo.com.cn/api/stock/p_stock2110'
# 功能2: 宇宙外公司补录候选的光通信关键词(独立正则, 不污染 scan 的 KW)
OPT_KW = re.compile(r'光模块|光通信|光通讯|CPO|光芯片|光器件|光引擎|硅光|800G|1\.6T|相干', re.I)
frozen_names = set(frozen.values())  # 名称集合, 用于宇宙外判定

def parse_sw_industry(text):
    """从 p_stock2110 响应解析当前申万二级行业名(F005V)。失败/无当前记录返回 None。"""
    try:
        data = json.loads(text)
    except Exception:
        return None
    recs = data if isinstance(data, list) else (data.get('result') or data.get('data') or [])
    if isinstance(recs, dict):
        recs = [recs]
    cur = None
    for r in recs:  # 优先取当前有效申万记录 F001V=008003 & F008C=1
        if not isinstance(r, dict):
            continue
        if str(r.get('F001V') or r.get('f001v') or '') == '008003' and str(r.get('F008C') or r.get('f008c') or '') == '1':
            cur = r; break
    if cur is None:
        for r in recs:  # 兜底: 任意含 F005V 的记录
            if isinstance(r, dict) and (r.get('F005V') or r.get('f005v') or r.get('industryName')):
                cur = r; break
    if cur is None:
        return None
    return str(cur.get('F005V') or cur.get('f005v') or cur.get('industryName') or '').strip()

def rescreen_due():
    """每月1日, 或对当月首次运行(日报文件尚未生成)触发一次分母重筛。"""
    marker = f'tmp/daily/.rescreen-{TODAY[:7]}.done'
    if os.path.exists(marker):
        return False
    if datetime.date.today().day == 1:
        return True
    if not os.path.exists(f'tmp/daily/{TODAY}.txt'):  # 当月首次运行
        return True
    return False

def run_rescreen():
    """功能1-月度分母重筛(备选方案: 无全量行业接口, 仅复核存量+不新增)。
    逐家查 p_stock2110, 与 _frozen 对比, 仅输出 diff 提示, 不改 _frozen.csv。
    2026-08-17: p_stock2110 已需token(401 code_005_ipban_notoken), akshare三级成分接口/东财push2均不可用;
    探测到401即短路返回, 不再空跑463次。"""
    os.makedirs('tmp/daily', exist_ok=True)
    month = TODAY[:7]
    checked = 0; moved_out = []; unresolved = 0
    for code, name in frozen.items():
        try:
            r = session.get(CNINFO_API, params={'scode': code, 'sdate': '1990-01-01', 'edate': TODAY}, timeout=30)
            if '未经授权' in r.text or '"resultcode":401' in r.text:
                log_lines.append('[重筛] p_stock2110 需token(401), 本月重筛跳过; 备选接口(akshare sw/东财push2)同日均不可用')
                return {'month': month, 'checked': 0, 'moved_out': [], 'unresolved': len(frozen), 'blocked': True}
            ind = parse_sw_industry(r.text)
        except Exception as e:
            log_lines.append(f'[重筛] {code} p_stock2110 失败: {str(e)[:50]}')
            unresolved += 1
            time.sleep(1.0); continue
        checked += 1
        if not ind:
            unresolved += 1  # 无当前申万记录, 不妄判移出
        elif ind not in FOUR:
            moved_out.append((code, name, ind))
        time.sleep(1.0)
    try:  # 写月度标记, 本月仅跑一次(即使部分失败也不再重复整轮)
        open(f'tmp/daily/.rescreen-{month}.done', 'w', encoding='utf-8').write(TODAY)
    except Exception:
        pass
    return {'month': month, 'checked': checked, 'moved_out': moved_out, 'unresolved': unresolved}

rescreen_result = None
if rescreen_due():
    try:
        rescreen_result = run_rescreen()
    except Exception as e:
        log_lines.append(f'[重筛] 月度重筛整体失败: {str(e)[:60]}')

# ---------- 1) 投关表全局增量(近3天) ----------
seen_titles = set()
hits = []
seen_outlier = set()  # 功能2: 宇宙外补录候选去重
outlier_hits = []
for tab, cat, titlef in (('relation', 'category_dyhd_szdy', None), ('fulltext', '', '投资者关系')):
    for page in (1, 2, 3):
        payload = {'pageNum': str(page), 'pageSize': '30', 'column': '', 'tabName': tab, 'plate': '',
                   'stock': '', 'searchkey': '', 'secid': '', 'category': cat, 'trade': '',
                   'seDate': f'{DAY3}~{TODAY}', 'sortName': '', 'sortType': '', 'isHLtitle': 'true'}
        try:
            r = session.post(fetch.QUERY_URL, data=payload, timeout=40)
            anns = r.json().get('announcements') or []
        except Exception:
            anns = []
        if not anns:
            break
        for a in anns:
            code = str(a.get('secCode') or '')
            name = str(a.get('secName') or '')
            title = fetch.clean_html_title(str(a.get('announcementTitle') or ''))
            if titlef and titlef not in title:
                continue
            url = str(a.get('adjunctUrl') or '')
            if not url.lower().endswith('.pdf'):
                continue
            if code in frozen or name in frozen_names:  # 宇宙内: 原流程下载投关表
                key = code + title
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                hits.append((code, fetch.parse_announcement_date(a.get('announcementTime')), title, url))
                continue
            # 功能2: 宇宙外公司 + 光通信关键词 -> 补录候选(不下载, 仅标题提示)
            m = OPT_KW.search(title)
            if m:
                okey = name + title
                if okey in seen_outlier:
                    continue
                seen_outlier.add(okey)
                outlier_hits.append((name, fetch.parse_announcement_date(a.get('announcementTime')), m.group(0), title))
        time.sleep(1.3)

for code, d, title, url in hits:
    ddir = os.path.join('corpus/ir', code)
    base = fetch.sanitize_filename(f'{code}_{d}_{title}.pdf')
    dst = os.path.join(ddir, base)
    if os.path.exists(dst):
        continue
    os.makedirs(ddir, exist_ok=True)
    try:
        full = fetch.build_pdf_url(url)
        r = session.get(full, headers={'Referer': 'https://www.cninfo.com.cn/'}, timeout=60)
        if not r.content.startswith(b'%PDF'):
            continue
        open(dst, 'wb').write(r.content)
        subprocess.run(['pdftotext', '-layout', dst, dst + '.txt'], capture_output=True)
        digest['ir_new'].append((frozen[code], d, title))
        new_ir_txt.append((code, frozen[code], title, dst + '.txt'))
    except Exception:
        pass
    time.sleep(1.3)

# ---------- 2) 互动易增量(关注公司) ----------
# 教训2026-08-08: 曾用14天窗口抓取,fetch()会整体重写qa.jsonl,把窗口外的历史问答(含P195点锚)冲掉,
# 不变量⑩当场拦截。日更必须全量抓取(since=2023-01-01),由fetcher自身限速,文件仍是全量快照。
for c in watched_codes():
    try:
        before = 0
        fp = f'corpus/qa/{c}/qa.jsonl'
        if os.path.exists(fp):
            before = sum(1 for _ in open(fp, encoding='utf-8'))
        n = fqa.fetch(c, '2023-01-01')
        after = sum(1 for _ in open(fp, encoding='utf-8')) if os.path.exists(fp) else 0
        if n and after > before:
            digest['qa_new'].append((frozen[c], after - before))
    except Exception as e:
        print(f'[qa {c}] {str(e)[:60]}')
    time.sleep(1.5)

# ---------- 3) 公告流(关注公司近3天,标题模式) ----------
ANN_PAT = re.compile(r'重大合同|向特定对象|定增|业绩预告|业绩快报|问询|回复|收购|资产重组')
for c in watched_codes():
    payload = {'pageNum': '1', 'pageSize': '15', 'column': '', 'tabName': 'fulltext', 'plate': '',
               'stock': '', 'searchkey': c, 'secid': '', 'category': '', 'trade': '',
               'seDate': f'{DAY3}~{TODAY}', 'sortName': '', 'sortType': '', 'isHLtitle': 'true'}
    try:
        r = session.post(fetch.QUERY_URL, data=payload, timeout=30)
        for a in r.json().get('announcements') or []:
            if str(a.get('secCode') or '') != c:
                continue
            t = fetch.clean_html_title(str(a.get('announcementTitle') or ''))
            if ANN_PAT.search(t):
                digest['ann'].append((frozen[c], fetch.parse_announcement_date(a.get('announcementTime')), t,
                                      'https://static.cninfo.com.cn/' + str(a.get('adjunctUrl') or '').lstrip('/')))
    except Exception:
        pass
    time.sleep(1.3)

# ---------- 3.5) 重启监视匹配(机械匹配,不做判定) ----------
# 投关表新txt做内容级触发词匹配(带上下文);公告流标题已过ANN_PAT,监视公司全量提示;互动易只有增量计数,人工过内容
restart_hits = []
for code, nm, title, txt in new_ir_txt:
    for w in WATCH_DAILY:
        if w['代码'] != code:
            continue
        try:
            body = open(txt, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        m = w['_pat'].search(body)
        if m:
            i = max(0, m.start() - 50)
            ctx = re.sub(r'\s+', '', body[i:m.start() + 70])
            restart_hits.append((w, f'投关表《{title[:30]}》', ctx))
for n, d, t, u in digest['ann']:
    for w in WATCH_DAILY:
        if n == w['公司']:
            restart_hits.append((w, f'公告流({d}): {t[:40]}', u))
for n, k in digest['qa_new']:
    for w in WATCH_DAILY:
        if n == w['公司']:
            restart_hits.append((w, f'互动易+{k}条', '增量内容未逐条匹配,需人工过内容'))

# ---------- 4) scan 召回差分 ----------
prev_file = 'tmp/daily/queue-latest.txt'
prev = set()
if os.path.exists(prev_file):
    prev = set(open(prev_file, encoding='utf-8').read().splitlines())
os.makedirs('tmp/daily', exist_ok=True)
os.rename(prev_file, 'tmp/daily/queue-prev.txt') if os.path.exists(prev_file) else None
# scan()只print前40条(q[:40]),解析print输出会把"窗口移位"误报成新增/消失差分;
# 改为进程内import拿全量q(格式与历史文件一致:seg截50字符),2026-08-15修复
import io, contextlib
spec4 = importlib.util.spec_from_file_location('scan', os.path.join(ROOT, 'scan.py'))
_scan = importlib.util.module_from_spec(spec4); sys.modules['scan'] = _scan; spec4.loader.exec_module(_scan)
with contextlib.redirect_stdout(io.StringIO()):
    _q = _scan.scan()
cur = [f'{co}|{cell}|{w}|{seg[:50]}' for _pr, _hid, co, cell, w, seg in _q]
with open(prev_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(cur))
new_hits = [x for x in cur if x.split('|')[0] + '|' + x.split('|')[1] not in {p.split('|')[0] + '|' + p.split('|')[1] for p in prev}]
gone = [x for x in prev if x.split('|')[0] + '|' + x.split('|')[1] not in {c.split('|')[0] + '|' + c.split('|')[1] for c in cur}]
digest['q_delta_new'] = new_hits[:15]
digest['q_delta_gone'] = gone[:5]

chk = subprocess.run(['python3', 'scan.py', '--check'], capture_output=True, text=True).stdout
chk_line = [l for l in chk.splitlines() if '全绿' in l or '[' in l]
stale = [l for l in chk.splitlines() if '语料' in l]

# ---------- 5) 写日报 ----------
out = [f'# 日报 {TODAY}', '', '## 语料', *[f'- {l}' for l in stale], '']
out.append(f'## 投关表新增 {len(digest["ir_new"])} 份')
for n, d, t in digest['ir_new'][:20]:
    out.append(f'- {n} | {d} | {t[:60]}')
out.append(f'\n## 互动易增量 {sum(x[1] for x in digest["qa_new"])} 条')
for n, k in digest['qa_new']:
    out.append(f'- {n} +{k}条')
out.append(f'\n## 公告流(关注公司) {len(digest["ann"])} 条')
for n, d, t, u in digest['ann'][:15]:
    out.append(f'- {n} | {d} | [{t[:50]}]({u})')
out.append(f'\n## 重启复核(待判/待确认监视) {len(restart_hits)} 条')
if restart_hits:
    out.append('> 触发后处置: pi/codebuddy 起草证据链 → 判定闸复核(本段为机械匹配,不构成判定)')
    for w, src, ctx in restart_hits[:20]:
        out.append(f'- ⚑ {w["公司"]} [{w["类别"]}|{w["cell_id"]}] {src}')
        out.append(f'  重启条件: {w["重启条件"][:80]}')
        out.append(f'  命中: {ctx[:80]}')
else:
    out.append('- 无触发')
out.append(f'\n## 召回净队列差分: 新增{len(new_hits)} / 消失{len(gone)}')
for x in digest['q_delta_new']:
    co, cell, w, seg = x.split('|', 3)
    out.append(f'- [{co}|{cell}] {w} | {seg[:60]}')
out.append(f'\n## 校验')
for l in chk_line[:3]:
    out.append(f'- {l}')
evidence_hint = bool(digest['ir_new'] or digest['qa_new'] or digest['ann'] or new_hits or restart_hits)
out.append(f'\n> 判定闸建议: {"有增量,值得开闸复核" if evidence_hint else "无实质增量,今日免开闸"}')
# ---------- 功能2: 补录候选(宇宙外·光通信命中) ----------
out.append(f'\n## 补录候选(宇宙外·光通信命中) {len(outlier_hits)} 条')
if outlier_hits:
    for n, d, kw, ctx in outlier_hits[:30]:
        out.append(f'- {n} | {d} | 命中:{kw} | {ctx[:60]}')
else:
    out.append('- 无')
# ---------- 功能1: 分母差分(月度重筛) ----------
if rescreen_result:
    rr = rescreen_result
    out.append(f'\n## 分母差分(月度重筛 {rr["month"]})')
    out.append(f'- 复核存量 {rr["checked"]} 家 / 移出 {len(rr["moved_out"])} 家 / 新增 0 家(全量接口未取得)')
    out.append('- 方法: p_stock2110 逐家核验(F001V=008003 & F008C=1)取当前申万二级; 全量成分接口未取得, 本月仅复核存量')
    if rr['moved_out']:
        for c, n, ind in rr['moved_out'][:30]:
            out.append(f'- 移出候选: {c} {n} (现归类:{ind})')
    else:
        out.append('- 移出候选: 无')
    if rr['unresolved']:
        out.append(f'- 未成功核验: {rr["unresolved"]} 家(网络/解析失败, 见日志段, 未做移出判定)')
# ---------- 日志段(静默降级记录) ----------
if log_lines:
    out.append('\n## 日志')
    for l in log_lines:
        out.append(f'- {l}')
open(f'tmp/daily/{TODAY}.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:8]))
print(f'...\n日报: tmp/daily/{TODAY}.txt')
