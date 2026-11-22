#!/usr/bin/env python3
"""从深交所互动易抓取公司问答 → corpus/qa/<代码>/qa.jsonl
用法: python3 corpus/_fetch_qa.py 代码1 代码2 ... [--since 2023-01-01]
- 互动易/董秘回答=准披露渠道,可作点锚(计划文档已批准);只有"回答"是证据,提问不是。
- 空回答("以公告为准"式)落地时打 empty 标记,扫描跳过。
- 单线程限速(纪律5);链路: queryKeyboardInfo→secid; searchResult(infoTypes=11)分页。
- 沪市(sns.sseinfo.com)未接入,调用沪市代码时如实报错。
jsonl 行: {code,secid,question,answer,answer_date,ask_date,index_id,empty,fetch_date,source}
- 事故教训(2026-08-15): 覆盖式写入 + 兜底仅"零条触发"双重缺陷导致丢历史。
  主通道部分返回(如002792仅2条、非零未触发兜底; 000063丢45条)时, 整体重写
  qa.jsonl 把190/45条历史问答直接抹掉, 被 scan.py ⑩点锚不变量当场拦截。
  修复=两层: (1)各通道改并集合并落盘(_merge_write, 按 index_id 并集, 行数只增不减, 宁多勿缺);
  (2)兜底触发条件加宽(fetch): 主通道返回条数 < 现有快照50% 且快照>20时, 即使非零也走 p5w 兜底。
"""
import argparse
import sys,os,json,time,re,datetime,html
import requests

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
   'Referer':'https://irm.cninfo.com.cn/'}
EMPTY_PAT=re.compile(r'^(尊敬的投资者[，,]?)?(您好[！!。]?)?(感谢您?的?(关注|提问)[和与及]?(支持)?[！!。，,]?)*(请|敬请)?(您)?(关注|参考|以)公司?(定期报告|公告|披露)(为准)?[。！!]?(谢谢[！!。]?)?$')
MIN_INTERVAL=1.25
MAX_PAGES=40
_LAST_REQUEST=0.0
PROGRESS_CALLBACK=None
FULL_SNAPSHOT_SINCE='2023-01-01'  # 该起点视为全量快照；增量窗口不做"快照缩水"比较
_trunc={'v':False,'reason':''}    # 本轮分页被截断(达上限/重复页)：结果不完整，必须报错不能当成功

class FetchFailure(RuntimeError):
    """所有通道都没有产出，与"真实零条"区分开。

    事故教训(2026-09-05): fetch() 曾把"主通道不可用 + p5w 兜底也无产出"返回成 None/0,
    调用方 `or []` 之后与"确实没有新问答"不可区分, 抓取失败被当成成功无增量。
    """

def request(method,url,**kwargs):
    """全站统一限速；HTTP/连接失败抛错，不能与“真实零结果”混淆。"""
    global _LAST_REQUEST
    if PROGRESS_CALLBACK:
        params=kwargs.get('params') or kwargs.get('data') or {}
        PROGRESS_CALLBACK({'method':method,'url':url,'page':params.get('page',params.get('pageNum'))})
    wait=MIN_INTERVAL-(time.monotonic()-_LAST_REQUEST)
    if wait>0: time.sleep(wait)
    r=requests.request(method,url,timeout=kwargs.pop('timeout',20),**kwargs)
    _LAST_REQUEST=time.monotonic()
    r.raise_for_status()
    return r

def _merge_write(code, out):
    """合并落盘: 写入前读现有qa.jsonl, 按 index_id 做并集(空 index_id 退化为内容指纹),
    已有条目保留、新拉取的追加/更新(fetch_date 等元数据取新); 任何情况下行数只增不减(宁多勿缺)。"""
    d=os.path.join(ROOT,'corpus','qa',code); os.makedirs(d,exist_ok=True)
    fp=os.path.join(d,'qa.jsonl')
    def key(o):
        i=o.get('index_id')
        if i: return ('id',str(i))
        return ('c',o.get('question'),o.get('answer'),o.get('ask_date'),o.get('answer_date'))
    existing={}; order=[]
    if os.path.exists(fp):
        with open(fp,encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: e=json.loads(line)
                except Exception: continue
                k=key(e)
                if k not in existing:
                    existing[k]=e; order.append(k)
    def mirror_key(row):
        source=row.get('source') or ''; answer=row.get('answer') or ''
        suffix=r'\s*[（(]来自[：:]\s*深交所互动易[）)]\s*$'
        kind='irm' if source.startswith('irm.cninfo.com.cn') else 'p5w' if source.startswith('ir.p5w.net') and re.search(suffix,answer) else None
        if not kind or not row.get('question') or not answer or not row.get('answer_date'):return None
        clean=lambda text:re.sub(r'\s+','',html.unescape(text))
        return kind,(clean(row['question']),clean(re.sub(suffix,'',answer)),row['answer_date'])
    merged=dict(existing); mirrors={}
    for row in existing.values():
        match=mirror_key(row)
        if match:mirrors.setdefault(match[1],set()).add(match[0])
    for o in out:
        k=key(o); match=mirror_key(o)
        if k not in merged and match and mirrors.get(match[1],set())-{match[0]}:
            continue  # Same Q&A from IRM and its P5W mirror; preserve the existing ID.
        merged[k]=o
        if match:mirrors.setdefault(match[1],set()).add(match[0])
    final=[]; seen=set()
    for k in order:
        if k not in seen:
            final.append(merged[k]); seen.add(k)
    for o in out:
        k=key(o)
        if k not in seen and k in merged:
            final.append(merged[k]); seen.add(k)
    with open(fp,'w',encoding='utf-8') as f:
        for o in final: f.write(json.dumps(o,ensure_ascii=False)+'\n')
    return len(final)

def _snapshot_count(code):
    """现有 qa.jsonl 快照条数(用于缩水兜底判定)。"""
    fp=os.path.join(ROOT,'corpus','qa',code,'qa.jsonl')
    if not os.path.exists(fp): return 0
    n=0
    with open(fp,encoding='utf-8') as f:
        for _ in f: n+=1
    return n

def secid_of(code):
    r=request('POST','https://irm.cninfo.com.cn/newircs/index/queryKeyboardInfo',
              data={'keyWord':code},headers=H,timeout=15)
    for d in (r.json().get('data') or []):
        if str(d.get('stockCode') or d.get('secCode') or '')==code:
            return d.get('secid') or d.get('secId'),d.get('shortName') or d.get('secName')
    return None,None



def fetch_p5w(code,since,until=None):
    """官网提问日期筛选 + 最新回复补查；100条是查询上限，不是历史总量。"""
    begin=datetime.date.fromisoformat(since)
    end=datetime.date.fromisoformat(until or datetime.date.today().isoformat())
    if begin>end:
        raise ValueError('p5w开始日期晚于结束日期')
    until=end.isoformat()
    HP={'User-Agent':H['User-Agent'],'Referer':'https://ir.p5w.net/'}
    cp=request('GET',f'https://ir.p5w.net/c/{code}',headers=HP,timeout=20); cp.encoding='utf-8'
    mp=re.search(r'id="pid"\s+value="([\w]+)"',cp.text)
    pid=mp.group(1) if mp else None
    if not pid:  # 兜底:公司建议接口按代码解析pid
        rj=request('POST','https://ir.p5w.net/company/validCompanyJson.shtml',
                   data={'keyword':code},headers=HP,timeout=15).json()
        choices=rj.get('obj') or []
        for o in choices:
            shown=str(o.get('companyCode') or o.get('stockCode') or '')
            if shown==code:
                pid=o.get('pid') or o.get('companyBaseinfoId') or o.get('id')
                break
        # 北交所切换920代码后，建议接口可能仍返回旧代码；精确关键词只有一个候选时取其主键。
        if not pid and len(choices)==1:
            o=choices[0]
            pid=o.get('pid') or o.get('companyBaseinfoId') or o.get('id')
    if not pid: print(f'[{code}] p5w pid未找到(页面+建议接口均无)'); return None
    # companyMoreQuestion.js serializes questionerTimeBegin/End. A real native
    # reply (920640, asked May 19 / answered May 20) confirms these filter ASK
    # dates. Check older questions separately for late answers; otherwise a
    # busy recent day fills the latest-100 list before reaching older questions.
    cap=100; page_size=10; calls=0; collected={}
    today=datetime.date.today().isoformat()

    def incomplete(reason):
        if not _trunc['v']:
            _trunc.update(v=True,reason=reason)

    def day(value):
        try:
            return datetime.date.fromisoformat(str(value or '')[:10]).isoformat()
        except ValueError:
            return ''

    def remember(rows):
        for row in rows:
            ad=day(row.get('replyerTimeStr'))
            if ad and since<=ad<=until:
                collected[str(row['pid'])]=row

    def wire(value):
        return value.isoformat(sep=' ') if isinstance(value,datetime.datetime) else value.isoformat()

    def timestamp(value):
        try:
            result=datetime.datetime.fromisoformat(str(value or ''))
            return result if result.tzinfo is None else None
        except ValueError:
            return None

    def in_window(row, window):
        ask=timestamp(row.get('questionerTimeStr'))
        if ask is None:return False
        lo,hi=window
        lower=lo if isinstance(lo,datetime.datetime) else datetime.datetime.combine(lo,datetime.time.min) if lo else datetime.datetime.min
        if isinstance(hi,datetime.datetime):return lower<=ask<=hi
        return lower<=ask and ask.date()<=hi

    def split_window(window):
        lo,hi=window
        if lo is None:
            # Keep an unbounded earlier side: late replies to pre-2023 questions
            # must not disappear just because our normal backfill starts in 2023.
            if hi<=datetime.date.min:return None
            cut=max(datetime.date.min,hi-datetime.timedelta(days=min(365,(hi-datetime.date.min).days)))
            return [(None,cut),(cut+datetime.timedelta(days=1),hi)]
        if not isinstance(lo,datetime.datetime) and lo<hi:
            mid=lo+(hi-lo)//2
            return [(lo,mid),(mid+datetime.timedelta(days=1),hi)]
        start=lo if isinstance(lo,datetime.datetime) else datetime.datetime.combine(lo,datetime.time.min)
        stop=hi if isinstance(hi,datetime.datetime) else datetime.datetime.combine(hi+datetime.timedelta(days=1),datetime.time.min)
        seconds=int((stop-start).total_seconds())
        if seconds<=1:return None
        mid=start+datetime.timedelta(seconds=seconds//2)
        # Share the boundary so subsecond source timestamps cannot fall in a gap.
        return [(start,mid),(mid,stop)]

    def get_page(page, window):
        nonlocal calls
        if calls>=MAX_PAGES:
            incomplete(f'p5w日期分段/回复补查达到请求上限{MAX_PAGES}')
            return None
        data={'companyBaseinfoId':pid,'isPagination':'1','page':page,'rows':page_size,
              'questionerTimeEnd':wire(window[1])}
        if window[0] is not None:data['questionerTimeBegin']=wire(window[0])
        calls+=1
        payload=request('POST','https://ir.p5w.net/interaction/getNewR.shtml',data=data,headers=HP,timeout=20).json()
        if not isinstance(payload,dict) or payload.get('success') is False or not isinstance(payload.get('rows'),list):
            incomplete('p5w响应无有效rows或服务端报告失败')
            return None
        rows=payload['rows']
        if any(not isinstance(row,dict) or not row.get('pid') or not day(row.get('replyerTimeStr')) for row in rows):
            incomplete('p5w问答缺有效ID或回复日期')
            return None
        remember(rows)
        try:
            total=int(payload['total'])
            if total<0 or total!=float(payload['total']): raise ValueError
        except (KeyError,TypeError,ValueError,OverflowError):
            incomplete('p5w缺有效总数，无法确认分页范围')
            return None
        if len(rows)>total or (not rows and total):
            incomplete('p5w返回条数与总数不一致')
            return None
        if any(not in_window(row,window) for row in rows):
            incomplete('p5w提问日期/时间筛选未生效或日期缺失')
            return None
        return total,rows

    def pages(first, window, older_questions):
        total,rows=first; seen=set(); page=0; previous_reply=None
        while True:
            ids=[str(row['pid']) for row in rows]
            if len(set(ids))!=len(ids) or seen.intersection(ids):
                incomplete(f'p5w第{page}页重复或重叠，不能确认范围完整')
                return
            seen.update(ids)
            if older_questions:
                # Within each query, the official view is sorted by reply time.
                # Only this older-question pass may stop at a reply-date boundary.
                stamps=[timestamp(row['replyerTimeStr']) for row in rows]
                if any(stamp is None for stamp in stamps) or stamps!=sorted(stamps,reverse=True) or (previous_reply and stamps and stamps[0]>previous_reply):
                    incomplete('p5w最新回复未按回复时间倒序，不能提前结束')
                    return
                if stamps:
                    previous_reply=stamps[-1]
                    if previous_reply.date()<begin:return
            if page==0 and total>=cap:
                children=split_window(window)
                if children:
                    windows.extend((child,older_questions) for child in children)
                    return
            if len(seen)>=total:
                if total>=cap:incomplete('p5w最小时间窗仍达100条上限，无法确认回复完整')
                return
            if page+1>=cap//page_size:
                incomplete('p5w返回总数超出已核100条查询上限')
                return
            page+=1
            result=get_page(page,window)
            if result is None:return
            if result[0]!=total:
                incomplete('p5w翻页过程中总数改变，需重查')
                return
            rows=result[1]

    try:
        windows=[]
        if begin>datetime.date.min:
            windows.append(((None,begin-datetime.timedelta(days=1)),True))
        windows.append(((begin,end),False))
        while windows:
            window,older_questions=windows.pop()
            first=get_page(0,window)
            if first is None:continue
            pages(first,window,older_questions)
    finally:
        # Network failure or the outer company budget must not discard pages
        # already obtained; RequestsClient carries this partial file to staging.
        out=[]
        for a in collected.values():
            ans=(a.get('replyContent') or '').strip()
            out.append({'code':code,'secid':f'p5w_{code}','question':(a.get('content') or '').strip(),
                'answer':ans,'answer_date':day(a.get('replyerTimeStr')),'ask_date':day(a.get('questionerTimeStr')),
                'index_id':str(a['pid']),
                'empty':bool(not ans or EMPTY_PAT.match(re.sub(r'\s','',ans)) or (len(ans)<75 and ('披露为准' in ans or '公告为准' in ans or '定期报告' in ans))),
                'fetch_date':today,'source':'ir.p5w.net interaction/getNewR.shtml(全景网投关平台,全市场镜像)'})
        _merge_write(code,out)
    print(f'[{code}] p5w {since}~{until}：{len(out)}条，{calls}次查询'+(f'；不完整：{_trunc["reason"]}' if _trunc['v'] else ''))
    return len(out)

def fetch_sse(code,since):
    """上证e互动: company.do?stockcode= 取uid; userfeeds.do(typeCode=company,type=11)分页HTML解析"""
    r=request('GET','https://sns.sseinfo.com/company.do',params={'stockcode':code},
              headers={'User-Agent':H['User-Agent'],'Referer':'https://sns.sseinfo.com/'},timeout=15)
    m=re.search(r'uid=(\d+)',r.text)
    nm=re.search(r'companyName[^>]*>\s*([^<(（\s]+)',r.text) or re.search(r'<title>\s*([^<(（]+)',r.text)
    if not m: print(f'[{code}] e互动uid未找到'); return None
    uid=m.group(1); name=(nm.group(1).strip() if nm else code)
    items=[];page=1
    while True:
        rr=request('GET','https://sns.sseinfo.com/ajax/userfeeds.do',
            params={'typeCode':'company','type':11,'pageSize':20,'uid':uid,'page':page},
            headers={'User-Agent':H['User-Agent'],'Referer':'https://sns.sseinfo.com/'},timeout=20)
        chunk=re.split(r'id="item-\d+"',rr.text)[1:]
        if not chunk: break
        items+=chunk; page+=1; time.sleep(2)
        if page>MAX_PAGES:
            _trunc['v']=True; _trunc['reason']=f'上证e互动分页达到上限{MAX_PAGES}页'
            print(f'[{code}] {_trunc["reason"]},结果不完整')
            break
    out=[];today=datetime.date.today().isoformat()
    DATE=re.compile(r'(\d{4})年(\d{2})月(\d{2})日')
    for it in items:
        plain=re.sub(r'(§ *)+','§',re.sub(r'\s+',' ',re.sub(r'<[^>]+>','§',it)))
        dates=DATE.findall(plain)
        qm=re.search(r':[^§]*\('+code+r'\)§([^§]+)§',plain)
        am=re.search(r'◆§◆§([^§]{2,10})§([^§]{2,})§\|§收藏',plain)
        q=(qm.group(1).strip() if qm else '')
        a=(am.group(2).strip() if am else '')
        if am and name in ('上证e互动',code): name=am.group(1).strip()
        ad='-'.join(dates[1]) if len(dates)>1 else ''
        qd='-'.join(dates[0]) if dates else ''
        if ad and ad<since: continue
        out.append({'code':code,'secid':f'sse_uid{uid}','question':q,'answer':a,
            'answer_date':ad,'ask_date':qd,'index_id':'',
            'empty':bool(not a or EMPTY_PAT.match(re.sub(r'\s','',a)) or (len(a)<75 and ('披露为准' in a or '公告为准' in a))),
            'fetch_date':today,'source':'sns.sseinfo.com userfeeds.do(type=11)'})
    fp=os.path.join(ROOT,'corpus','qa',code,'qa.jsonl')
    _merge_write(code,out)
    print(f'[{code} {name}] {len(out)}条(空回答{sum(1 for o in out if o["empty"])}) → {fp}')
    return len(out)

def fetch_irm(code,since):
    if not (code.startswith('0') or code.startswith('3')):
        print(f'[{code}] 交易所归属未知,跳过'); return None
    secid,name=secid_of(code)
    if not secid:
        print(f'[{code}] secid未找到'); return None
    rows=[];page=1;prev_sig=None
    while True:
        r=request('GET','https://irm.cninfo.com.cn/newircs/search/searchResult',params={
            'stockCodes':f'{secid}_{code}','keywords':'','infoTypes':'11',
            'startDate':f'{since} 00:00:00',
            'endDate':datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59',
            'pageNum':page,'pageSize':30,'onlyAttentionCompany':2},headers=H,timeout=20)
        d=r.json().get('data') or {}
        res=d.get('results') or []
        rows+=res
        if not res: break
        # 服务端不翻页(重复返回同一页)时立即停止，避免 40 页 × 睡眠拖垮日更
        sig=tuple(str(x.get('indexId') or '') for x in res)
        if sig and sig==prev_sig:
            _trunc['v']=True; _trunc['reason']=f'主通道第{page}页与上一页重复,服务端未翻页'
            print(f'[{code}] {_trunc["reason"]},结果不完整')
            break
        prev_sig=sig
        total=int(d.get('totalPage') or 0)
        if total and page>=total: break
        if page>=MAX_PAGES:
            _trunc['v']=True; _trunc['reason']=f'主通道分页达到上限{MAX_PAGES}页(totalPage={total or "未知"})'
            print(f'[{code}] {_trunc["reason"]},结果不完整')
            break
        page+=1; time.sleep(2)
    out=[]
    today=datetime.date.today().isoformat()
    for a in rows:
        ans=(a.get('attachedContent') or '').strip()
        def toi(x):
            try: return int(x)
            except: return 0
        ts=toi(a.get('attachedPubDate')) or toi(a.get('updateDate'))
        out.append({'code':code,'secid':secid,
            'question':(a.get('mainContent') or '').strip(),
            'answer':ans,
            'answer_date':datetime.date.fromtimestamp(ts/1000).isoformat() if ts else '',
            'ask_date':datetime.date.fromtimestamp(toi(a.get('pubDate'))/1000).isoformat() if toi(a.get('pubDate')) else '',
            'index_id':str(a.get('indexId') or ''),
            'empty':bool(not ans or EMPTY_PAT.match(re.sub(r'\s','',ans))),
            'fetch_date':today,
            'source':'irm.cninfo.com.cn searchResult(infoTypes=11)'})
    fp=os.path.join(ROOT,'corpus','qa',code,'qa.jsonl')
    _merge_write(code,out)
    n_empty=sum(1 for o in out if o['empty'])
    print(f'[{code} {name}] {len(out)}条(空回答{n_empty}) → {fp}')
    return len(out)

_p5w_down = {'v': False, 'reason': ''}  # 熔断: p5w首个连接失败后本轮跳过(2026-08-21: p5w不可达×重试预算→日更60min超时事故)

def _p5w_guarded(code, since):
    """p5w调用带熔断; 失败置down并记原因, 本轮后续直接跳过。返回 None=无产出(不等于零条)。"""
    if _p5w_down['v']:
        print(f'[{code}] p5w已熔断,跳过({_p5w_down.get("reason","")})')
        return None
    try:
        return fetch_p5w(code, since)
    except Exception as e:
        _p5w_down['v'] = True
        _p5w_down['reason'] = f'{type(e).__name__}: {str(e)[:60]}'
        print(f'[{code}] p5w失败触发熔断,本轮后续跳过: {str(e)[:60]}')
        return None

def _primary(code,since):
    """主通道按市场分派。返回 (条数或None, 失败原因)：None=通道未产出(不可用), int=产出条数。"""
    if code.startswith('6'):
        return fetch_sse(code,since),'上证e互动uid未找到'
    if code.startswith('0') or code.startswith('3'):
        return fetch_irm(code,since),'互动易secid未找到'
    return None,'交易所归属未知'

def fetch(code,since):
    """主通道按市场分派；0条/失败时全景网兜底(全市场镜像,含沪深,纪律9双通道)。
    2026-08-15勘误: 主通道"部分返回"(非零但远低于历史)也会绕过兜底并覆盖写入丢历史;
    故非零也按"缩水"判定走p5w, 且各通道改并集合并落盘(见_merge_write)。
    2026-08-21: p5w调用改经_p5w_guarded熔断(连接失败一次本轮不再尝试)。
    2026-09-05勘误: 通道全部无产出(返回None)时抛 FetchFailure, 不再返回 0/None——
    否则调用方无法区分"抓取失败"和"确实没有新问答", 会把失败当成成功无增量。"""
    _trunc['v']=False; _trunc['reason']=''
    if code.startswith('92') or code.startswith('8'):
        n=_p5w_guarded(code,since)   # 勘误2026-07-28:北交所有平台=全景网ir.p5w.net(原生通道即此)
        if n is None:
            raise FetchFailure(f'[{code}] 北交所原生通道p5w无产出({_p5w_down.get("reason") or "pid未找到"})')
        if _trunc['v']:
            raise FetchFailure(f'[{code}] 北交所原生通道分页被截断({_trunc["reason"]}): 已抓{n}条已落盘,但不完整')
        return n
    n,reason=_primary(code,since)
    if _trunc['v']:
        raise FetchFailure(f'[{code}] 主通道分页被截断({_trunc["reason"]}): 已抓{n}条已落盘,但不完整,不得推进水位')
    if not n:
        m=_p5w_guarded(code,since)
        # 截断检查放在判断 m 之前：p5w 抓到历史但 since 过滤后 m=0 时，
        # 不能因 m 为假而漏过 _trunc（2026-09-05 第三稿预检漏网）。
        if _trunc['v']:
            raise FetchFailure(f'[{code}] p5w兜底分页被截断({_trunc["reason"]}): 已抓{m}条已落盘,但不完整,不得推进水位')
        if m:
            print(f'[{code}] 主通道{n},p5w兜底{m}条(前科:002792/600641/688079主通道假阴性)')
            return m
        if m is None:
            raise FetchFailure(f'[{code}] 主通道{n}条,但p5w兜底不可用({_p5w_down.get("reason") or "无产出或pid未找到"}): 无法确认零新增,不得推进水位')
        if n is None:
            raise FetchFailure(f'[{code}] 无通道产出: {reason}; p5w兜底({_p5w_down.get("reason") or "无产出或pid未找到"})')
        return 0
    # 缩水兜底只在全量快照请求时比较: 增量窗口天然远小于历史快照, 不能当成缩水(2026-09-05)
    if str(since)<=FULL_SNAPSHOT_SINCE:
        snap=_snapshot_count(code)
        if snap>20 and n<0.5*snap:
            m=_p5w_guarded(code,since)
            if _trunc['v']:
                raise FetchFailure(f'[{code}] p5w兜底分页被截断({_trunc["reason"]}): 已抓{m}条已落盘,但不完整,不得推进水位')
            if m:
                print(f'[{code}] 主通道{n}条缩水触发p5w兜底{m}条(前科:002792/600641/688079主通道假阴性)')
            elif _p5w_down['v']:
                raise FetchFailure(f'[{code}] 主通道{n}条较快照{snap}条缩水,且p5w兜底不可用({_p5w_down["reason"]}): 增量不完整')
            else:
                print(f'[{code}] 主通道{n}条较快照{snap}条缩水,p5w兜底无更多数据(已尽力,并非失败)')
    return n

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('codes',nargs='+')
    parser.add_argument('--since',default='2023-01-01')
    ns=parser.parse_args()
    for c in ns.codes:
        try: fetch(c,ns.since)
        except Exception as e: print(f'[{c}] 失败: {str(e)[:80]}')
        time.sleep(2.5)
