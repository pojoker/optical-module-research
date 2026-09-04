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
import sys,os,json,time,re,datetime
import requests

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
   'Referer':'https://irm.cninfo.com.cn/'}
EMPTY_PAT=re.compile(r'^(尊敬的投资者[，,]?)?(您好[！!。]?)?(感谢您?的?(关注|提问)[和与及]?(支持)?[！!。，,]?)*(请|敬请)?(您)?(关注|参考|以)公司?(定期报告|公告|披露)(为准)?[。！!]?(谢谢[！!。]?)?$')
MIN_INTERVAL=1.25
_LAST_REQUEST=0.0

def request(method,url,**kwargs):
    """全站统一限速；HTTP/连接失败抛错，不能与“真实零结果”混淆。"""
    global _LAST_REQUEST
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
    merged=dict(existing)
    for o in out: merged[key(o)]=o
    final=[]; seen=set()
    for k in order:
        if k not in seen:
            final.append(merged[k]); seen.add(k)
    for o in out:
        k=key(o)
        if k not in seen:
            final.append(o); seen.add(k)
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



def fetch_p5w(code,since):
    """北交所: 全景网投资者关系互动平台 ir.p5w.net (interaction/getNewR.shtml, JSON直出)"""
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
    items=[];page=1;seen=set()
    while page<=60:
        r=request('POST','https://ir.p5w.net/interaction/getNewR.shtml',
            data={'companyBaseinfoId':pid,'isPagination':'1','page':page,'rows':10},headers=HP,timeout=20)
        rows=(r.json().get('rows') or [])
        new=[x for x in rows if x.get('pid') not in seen]
        if not new: break
        for x in new: seen.add(x.get('pid'))
        items+=new; page+=1; time.sleep(1.5)
    out=[];today=datetime.date.today().isoformat();name=''
    for a in items:
        name=a.get('companyShortname') or name
        ans=(a.get('replyContent') or '').strip()
        ad=(a.get('replyerTimeStr') or '')[:10]
        if ad and ad<since: continue
        out.append({'code':code,'secid':f'p5w_{code}','question':(a.get('content') or '').strip(),
            'answer':ans,'answer_date':ad,'ask_date':(a.get('questionerTimeStr') or '')[:10],
            'index_id':str(a.get('pid') or ''),
            'empty':bool(not ans or EMPTY_PAT.match(re.sub(r'\s','',ans)) or (len(ans)<75 and ('披露为准' in ans or '公告为准' in ans or '定期报告' in ans))),
            'fetch_date':today,'source':'ir.p5w.net interaction/getNewR.shtml(全景网投关平台,全市场镜像)'})
    _merge_write(code,out)
    print(f'[{code} {name}] {len(out)}条(空回答{sum(1 for o in out if o["empty"])})')
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
        if page>40: break
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
    rows=[];page=1
    while True:
        r=request('GET','https://irm.cninfo.com.cn/newircs/search/searchResult',params={
            'stockCodes':f'{secid}_{code}','keywords':'','infoTypes':'11',
            'startDate':f'{since} 00:00:00',
            'endDate':datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59',
            'pageNum':page,'pageSize':30,'onlyAttentionCompany':2},headers=H,timeout=20)
        d=r.json().get('data') or {}
        res=d.get('results') or []
        rows+=res
        if page>=int(d.get('totalPage') or 0) or not res: break
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

_p5w_down = {'v': False}  # 熔断: p5w首个连接失败后本轮跳过(2026-08-21: p5w不可达×重试预算→日更60min超时事故)

def _p5w_guarded(code, since):
    """p5w调用带熔断; 失败置down并记日志, 本轮后续直接跳过。"""
    if _p5w_down['v']:
        print(f'[{code}] p5w已熔断,跳过')
        return None
    try:
        return fetch_p5w(code, since)
    except Exception as e:
        _p5w_down['v'] = True
        print(f'[{code}] p5w失败触发熔断,本轮后续跳过: {str(e)[:60]}')
        return None

def fetch(code,since):
    """主通道按市场分派；0条/失败时全景网兜底(全市场镜像,含沪深,纪律9双通道)。
    2026-08-15勘误: 主通道"部分返回"(非零但远低于历史)也会绕过兜底并覆盖写入丢历史;
    故非零也按"缩水"判定走p5w, 且各通道改并集合并落盘(见_merge_write)。
    2026-08-21: p5w调用改经_p5w_guarded熔断(连接失败一次本轮不再尝试)。"""
    if code.startswith('6'):
        n=fetch_sse(code,since)
    elif code.startswith('92') or code.startswith('8'):
        return _p5w_guarded(code,since)   # 勘误2026-07-28:北交所有平台=全景网ir.p5w.net(原生通道即此)
    else:
        n=fetch_irm(code,since)
    if not n:
        m=_p5w_guarded(code,since)
        if m: print(f'[{code}] 主通道{n},p5w兜底{m}条(前科:002792/600641/688079主通道假阴性)')
        return m if m is not None else n
    # 兜底加宽: 主通道非零但缩水(<现有快照50%且快照>20)也走p5w, 两通道并集合并落盘
    snap=_snapshot_count(code)
    if snap>20 and n<0.5*snap:
        m=_p5w_guarded(code,since)
        if m: print(f'[{code}] 主通道{n}条缩水触发p5w兜底{m}条(前科:002792/600641/688079主通道假阴性)')
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
