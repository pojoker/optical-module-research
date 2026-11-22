#!/usr/bin/env python3
"""scan.py — 扫描+不变量①-⑭。用法: python3 scan.py [--check]
--check: 只跑不变量(<10s)。扫描分母=corpus/annual(_frozen登记);legacy-input=证据库不参与扫描。"""
import sys,os,csv,re,glob,time,subprocess

ROOT=os.path.dirname(os.path.abspath(__file__))
ERR=[]
def fail(k,msg): ERR.append(f"[{k}] {msg}")

def rows(f):
    p=os.path.join(ROOT,f)
    return list(csv.DictReader(open(p,encoding='utf-8-sig'))) if os.path.exists(p) else []

def observation_names():
    """Read the small observation-list contract without requiring PyYAML."""
    text=open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8').read()
    match=re.search(r'^observation_list:.*?^tree:',text,flags=re.M|re.S)
    if not match: return set()
    return set(re.findall(r'\{名称:\s*([^,}]+)',match.group(0)))

E_状态={'生产中','在建','传闻','宇宙外观察'}
E_标签={'A股','美股','港股','台股','日股','欧股','新三板','未上市私企','未上市国企','未上市(母上市)','未解析'}
E_数值类型={'占比','金额'}
E_单位={'元','万元','亿元','美元','万美元','百万美元','亿美元','欧元','万欧元'}
E_边等级={'实边','半边','推断A','推断B','推断C'}
E_来源={'扫描','线索','人工'}
E_处置={'已入点','已入边候选','驳回-碰撞','驳回-非本格','驳回-证据不足','待判','驳回-移交海外','驳回-主体退出'}  # 2026-08-23 +2: A类境外待判核销(codex对表rev39,细分与指针进理由列)
U2Y={'元':1,'万元':1e4,'亿元':1e8,'美元':7,'万美元':7e4,'百万美元':7e6,'亿美元':7e8,'欧元':8,'万欧元':8e4}

def staleness():
    fs=glob.glob(os.path.join(ROOT,'corpus/annual/**/*.pdf'),recursive=True)
    if not fs: print('[饥饿] corpus/annual 无语料'); return
    n=(time.time()-max(os.path.getmtime(f) for f in fs))/86400
    frozen={r['代码'] for r in rows('corpus/_frozen.csv')}
    # 有目录≠有语料: 须真含pdf才算覆盖(否则空目录静默冒充已覆盖,实测曾把31家缺口谎报成3家)
    have={os.path.basename(d) for d in glob.glob(os.path.join(ROOT,'corpus/annual/*'))
          if os.path.isdir(d) and glob.glob(d+'/**/*.pdf',recursive=True)}
    miss=sorted(frozen-have)
    print(f"[语料] 最新文件距今{n:.0f}天; 宇宙内缺席年报 {len(miss)} 家"+(f"(样例:{','.join(miss[:5])})" if miss else ''))
    if n>120: print("[黄灯] 语料距今>120天,该投喂了(README年报季提示)")

def _check_shipment_row(r):
    """⑪ 出货量推断层行级校验(ADR-0001). 行为与原内联循环逐字一致, 供主循环与 --selftest 调用."""
    if not re.fullmatch(r'SE\d{3}',r.get('row_id','?')): fail('⑪',f"shipments row_id须为SE###: {r.get('row_id')}")
    lv = r.get('证据等级','')
    if lv not in ('B','C','D'): fail('⑪',f"{r.get('row_id')} 证据等级{lv}非法(推断层封顶C,B仅直接披露,禁A)")
    if str(r.get('情景标记','')).startswith('scenario') and lv!='D': fail('⑪',f"{r.get('row_id')} 情景行必须为D级")
    if r.get('单位','') not in ('只','颗','件','支','片','只/个','支/套','片/个','台','台/套','千克','千只','KK','万只','万颗','万个','万件','万支','万片','万平方米','万美元'): fail('⑪',f"{r.get('row_id')} 单位非法: {r.get('单位')}")
    # 出货量必须为数值(收入事实不入本表,见⑫;2026-08-16评审R1/R2返修;REVLINE-R6-01:NaN/Inf拦截)
    try: _qv=float(str(r.get('出货量','')).replace(',',''))
    except ValueError: fail('⑪',f"{r.get('row_id')} 出货量非数值: {r.get('出货量')}")
    else:
        import math
        if not math.isfinite(_qv): fail('⑪',f"{r.get('row_id')} 出货量非有限值: {r.get('出货量')}")
    _check_shipment_arith(r)

# ---- ⑪ 算术/单位/口径硬门(Step1 2026-11-21): 下列列在 --selftest 基础5列 fixture 中可缺省, 缺省即跳过 ----
_SCI_RE=re.compile(r'(?<![A-Za-z0-9_.])\d+(?:\.\d+)?[eE][+-]?\d+(?![A-Za-z0-9_])')
_REV_RE=re.compile(r'^\s*([\d,]+(?:\.\d+)?)\s*(亿元|万元|元)')
_ASP_RE=re.compile(r'ASP≈?\s*([\d,]+(?:\.\d+)?)\s*(万?元)/([A-Za-z\u4e00-\u9fff]+)')
_REV_SCALE={'元':1.0,'万元':1e4,'亿元':1e8}
_PIECE_BASES=('只','颗','个','件','支','片','套')

def _unit_scale(u):
    """单位 → (倍率, 基本单位元组). 千*=1e3, 万*=1e4, KK=1e6(泛计件,基本单位为通用件名); 斜杠复合单位(只/个)各分量均为合法基本单位."""
    u=(u or '').strip()
    if u=='KK': return 1e6, _PIECE_BASES
    parts=[p for p in u.split('/') if p]
    if not parts: return 1.0, ()
    first=parts[0]
    scale={'千':1e3,'万':1e4}.get(first[0],1.0) if len(first)>1 else 1.0
    bases=tuple(p[1:] if len(p)>1 and p[0] in '千万' else p for p in parts)
    return scale, bases

def _num(s):
    return float(str(s).replace(',',''))

def _check_shipment_arith(r):
    """⑪ 硬门: 科学计数法 / 同比反算禁B / 利用率须基于产量 / 隐含ASP算术交叉校验 / ASP计价单位须与行单位一致."""
    rid=r.get('row_id','?')
    rev=str(r.get('收入输入') or '')
    asp=str(r.get('ASP输入') or '')
    for col,v in (('收入输入',rev),('ASP输入',asp)):
        m=_SCI_RE.search(v)
        if m: fail('⑪',f'{rid} {col}含科学计数法 {m.group(0)}(须写成可复核的十进制数)')
    if '同比反算' in str(r.get('推导式') or '') and r.get('证据等级','')=='B':
        fail('⑪',f'{rid} 推导式含同比反算属推断值, 证据等级须封顶C/D, 不得为B')
    cap=str(r.get('产能天顶检') or '')
    if '利用率' in cap and '产量' not in cap:
        fail('⑪',f'{rid} 产能天顶检写利用率却未写产量(销量÷产能≠产能利用率, 须产量÷产能或改称销量/产能比)')
    am=_ASP_RE.search(asp)
    if not am: return
    asp_v=_num(am.group(1))*(1e4 if am.group(2)=='万元' else 1.0)
    denom=am.group(3)
    d_scale=1.0
    if len(denom)>1 and denom[0] in '千万':
        d_scale={'千':1e3,'万':1e4}[denom[0]]; denom=denom[1:]
    q_scale,bases=_unit_scale(r.get('单位',''))
    if bases and not any(denom.startswith(b) for b in bases):
        fail('⑪',f"{rid} ASP计价单位 元/{am.group(3)} 与行单位 {r.get('单位','')} 不一致(疑硬编码模板)")
        return
    rm=_REV_RE.match(rev)
    if not rm: return
    try:
        rev_v=_num(rm.group(1))*_REV_SCALE[rm.group(2)]
        qty=_num(r.get('出货量',''))*q_scale/d_scale
    except (ValueError,TypeError): return
    import math
    if not (math.isfinite(qty) and qty>0 and math.isfinite(rev_v)): return
    implied=rev_v/qty
    diff=abs(implied-asp_v)
    if diff>0.05 and diff>0.05*abs(implied):
        fail('⑪',f'{rid} 隐含ASP算术不符: 收入{rev_v:,.2f}元÷出货{qty:,.4g}{am.group(3)}={implied:,.4g}元, 而ASP输入标{asp_v:,.4g}元(偏差{diff/abs(implied):.1%})')

# ---- ①/⑦ 同步与完整性纯函数 ----
def _check_tree_universe(tree, n_frozen):
    """① tree.yaml 必须为映射, 且 universe.count == corpus/_frozen.csv 唯一代码数."""
    if not isinstance(tree, dict): fail('①','tree.yaml 顶层非映射'); return
    cnt=(tree.get('universe') or {}).get('count') if isinstance(tree.get('universe'),dict) else None
    if cnt!=n_frozen: fail('①',f'tree.yaml universe.count={cnt} ≠ corpus/_frozen.csv 代码数 {n_frozen}(扩容须同步)')

def _tree_leaf_cells(tree):
    out=set()
    def walk(ns):
        if isinstance(ns,dict): ns=[ns]
        if not isinstance(ns,list): return
        for n in ns:
            if not isinstance(n,dict): continue
            if n.get('cell_id') is not None: out.add(str(n['cell_id']).strip())
            walk(n.get('children'))
    walk((tree or {}).get('tree',[]) if isinstance(tree,dict) else [])
    return out

def _check_triage_ids(trg):
    """⑦ triage.csv hit_id 非空且唯一."""
    seen=set()
    for t in trg:
        hid=(t.get('hit_id') or '').strip()
        if not hid: fail('⑦','triage hit_id 空'); continue
        if hid in seen: fail('⑦',f'triage hit_id重复: {hid}'); continue
        seen.add(hid)

def _check_watchlist(rs, leaf_cells):
    """⑦ corpus/_restart_watchlist.csv: 非空且非ANY的cell_id(允许/、,分隔多格)必须是tree叶格."""
    for i,r in enumerate(rs):
        raw=(r.get('cell_id') or '').strip()
        if not raw or raw=='ANY': continue
        for c in re.split(r'[/,，、;；|]',raw):
            c=c.strip()
            if c and c!='ANY' and c not in leaf_cells:
                fail('⑦',f"_restart_watchlist 第{i+2}行({r.get('公司','?')}) cell_id {c} 不在tree叶格")

# ---- ②/④ edges 截断与悬空底稿指针 ----
_STALE_REFS=('deanonymization-cases.md','seed findings','jituanyi-leads.md')
def _check_edge_integrity(r):
    eid=r.get('edge_id','?')
    for col in ('占比或金额原文','验证状态'):
        v=(r.get(col) or '').strip()
        if not v or v=='-': continue
        lo=v.count('(')+v.count('（'); hi=v.count(')')+v.count('）')
        if lo!=hi: fail('④',f'{eid} {col} 括号不平衡(左{lo}/右{hi}),疑半截截断: …{v[-30:]}')
        elif v[-1] in '，；,;-': fail('④',f'{eid} {col} 以{v[-1]!r}结尾,疑半截截断: …{v[-30:]}')
    blob=' '.join(str(x or '') for x in r.values())
    for s in _STALE_REFS:
        if s in blob: fail('②',f'{eid} 引用已迁出/悬空底稿 {s!r}(须改指当前可达文件或删除)')

# ---- ⑧/⑨/⑩ 锚点与URL卫士 ----
_URL_AUTH_RE=re.compile(r'https?://[^/\s]*@')
_URL_SEARCH_RE=re.compile(r'baidu\.com/s\?|google\.com/search\?|bing\.com/search\?',re.I)
_CORPUS_PATH_RE=re.compile(r'corpus/(?:annual-2023|annual-2024|annual|ir|qa|legacy-input|web|customs|content_ledger|relationships|salvaged|daily_review)/[^\s；;，,）)]+')
_CNINFO_PDF_RE=re.compile(r'cninfo\.com\.cn/finalpage/[^\s#"]+?\.pdf',re.I)
_SHARED_OK_RE=re.compile(r'同业|客户|供应商|并购|重组|控股|子公司|参股')

def _check_url_hygiene(text, ctx, k):
    t=str(text or '')
    for m in _URL_AUTH_RE.finditer(t): fail(k,f'{ctx} URL含basic-auth畸形符号 {m.group(0)}(须还原真实链接)')
    for m in _URL_SEARCH_RE.finditer(t): fail(k,f'{ctx} URL为搜索占位链接 {m.group(0)}(非证据锚)')

def _check_macro_row(r):
    """⑨ macro_evidence 行: URL卫士 + A/B级(非内部可重算)须至少1个合法http(s)链接."""
    cid=r.get('claim_id','?')
    _check_url_hygiene(' '.join(str(x or '') for x in r.values()), f'macro {cid}', '⑨')
    if r.get('证据等级') in ('A','B') and (r.get('证据类型') or '').strip()!='内部证据账本可重算':
        urls=re.findall(r'https?://[^\s，,；;）)]+',f"{r.get('链接') or ''} {r.get('来源描述') or ''}")
        ok=[u for u in urls if not _URL_AUTH_RE.match(u) and not _URL_SEARCH_RE.search(u)]
        if not ok: fail('⑨',f"macro {cid} 证据等级{r.get('证据等级')}却无合法http(s)链接")

def _check_point_row(r, exists=None):
    """⑧/⑩ points 行: URL卫士 + 锚点中 corpus/ 本地路径必须真实存在."""
    if exists is None: exists=lambda rel: os.path.exists(os.path.join(ROOT,rel))
    pid=r.get('point_id','?')
    _check_url_hygiene(' '.join(str(x or '') for x in r.values()), f'points {pid}', '⑧')
    for m in _CORPUS_PATH_RE.finditer(r.get('锚点URL') or ''):
        rel=m.group(0).split('#')[0].rstrip('。."\'”’')
        if not exists(rel): fail('⑩',f'points {pid} 锚点本地路径不存在: {rel}')

def _same_company(a, b):
    na=re.sub(r'[（(].*?[）)]','',a or '').strip(); nb=re.sub(r'[（(].*?[）)]','',b or '').strip()
    if not na or not nb: return na==nb
    return na==nb or (min(len(na),len(nb))>=2 and (na in nb or nb in na))

def _check_point_table(pts):
    """⑧ 同一巨潮 finalpage PDF(忽略#page)被两家不同A股公司共用, 且两行判定等级/命中引语均无关联关系说明 → 疑错贴他司年报URL."""
    by={}
    for p in pts:
        if p.get('上市标签')!='A股': continue
        for u in {m.group(0).lower() for m in _CNINFO_PDF_RE.finditer(p.get('锚点URL') or '')}:
            by.setdefault(u,[]).append(p)
    for u,ps in by.items():
        for i in range(len(ps)):
            for j in range(i+1,len(ps)):
                a,b=ps[i],ps[j]
                if _same_company(a.get('公司'),b.get('公司')): continue
                ctx=' '.join(str(x.get(c) or '') for x in (a,b) for c in ('判定等级','命中引语'))
                if _SHARED_OK_RE.search(ctx): continue
                fail('⑧',f"points {a.get('point_id')}({a.get('公司')}) 与 {b.get('point_id')}({b.get('公司')}) 共用同一巨潮PDF {u} 且无关联关系说明,疑错贴他司URL")

# ---- Step2 扩展机器门(2026-11-21): 海关四维表(⑨) · 内容台账(⑧) · 关系时间线与负记忆(②) ----
_CUSTOMS_RECON_MONTHS=tuple([f'2025{m:02d}' for m in range(1,13)]+[f'2026{m:02d}' for m in range(1,7)])
_CUSTOMS_PK_COLS={
    'monthly':('月份','HS编码'),
    'partners':('月份','贸易伙伴'),
    'province':('月份','注册地','贸易伙伴'),
    'trademode':('月份','贸易伙伴','贸易方式'),
}
def _check_customs_tables(tables=None, raw_texts=None):
    """⑨扩展 海关四维表校验: 无引号内/字段内嵌入换行符\\n/\\r、无重复主键、202501–202606(18个月)美元汇总与customs_monthly偏差<0.01%."""
    import io, math
    if tables is None:
        tables={}; raw_texts={} if raw_texts is None else dict(raw_texts)
        missing=False
        for t in ('monthly','partners','province','trademode'):
            p=os.path.join(ROOT,'corpus','customs',f'customs_{t}.csv')
            if not os.path.exists(p):
                fail('⑨',f'corpus/customs/customs_{t}.csv 缺失'); missing=True; continue
            with open(p,encoding='utf-8-sig',newline='') as fh:
                txt=fh.read()
            raw_texts.setdefault(t,txt)
            tables[t]=list(csv.DictReader(io.StringIO(txt)))
        if missing: return
    else:
        raw_texts={} if raw_texts is None else dict(raw_texts)
    usd_by_month={}
    for t in ('monthly','partners','province','trademode'):
        rs=tables.get(t)
        if not rs:
            fail('⑨',f'customs_{t} 为空或缺失'); return
        if t in raw_texts and raw_texts[t] is not None:
            norm_txt=raw_texts[t].replace('\r\n','\n')
            if '\r' in norm_txt:
                fail('⑨',f'customs_{t}.csv 含裸\\r换行符')
            phys=len(norm_txt.rstrip('\n').split('\n')) if norm_txt.strip() else 0
            if phys!=len(rs)+1:
                fail('⑨',f'customs_{t}.csv 物理行数({phys})≠表头+数据行({len(rs)+1}),存在引号内嵌入换行符')
        pk_cols=_CUSTOMS_PK_COLS[t]
        seen_pk=set()
        m_sums={}
        for idx,r in enumerate(rs,start=2):
            for col,val in r.items():
                ks,vs=str(col or ''),str(val or '')
                if '\n' in ks or '\r' in ks or '\n' in vs or '\r' in vs:
                    fail('⑨',f'customs_{t} 第{idx}行字段 {col} 含内嵌换行符')
            pk=tuple(str(r.get(c) or '').strip() for c in pk_cols)
            if any(not x for x in pk):
                fail('⑨',f'customs_{t} 第{idx}行主键列为空: {dict(zip(pk_cols,pk))}')
            elif pk in seen_pk:
                fail('⑨',f'customs_{t} 第{idx}行重复主键: {pk}')
            else:
                seen_pk.add(pk)
            amt_col='金额USD' if '金额USD' in r else '金额'
            raw_amt=str(r.get(amt_col) or '').replace(',','').strip()
            try:
                av=float(raw_amt)
                if not math.isfinite(av) or av<0: raise ValueError()
            except ValueError:
                fail('⑨',f'customs_{t} 第{idx}行金额非法: {r.get(amt_col)!r}'); continue
            ym=str(r.get('月份') or '').strip()
            m_sums[ym]=m_sums.get(ym,0.0)+av
        usd_by_month[t]=m_sums
    for ym in _CUSTOMS_RECON_MONTHS:
        base_usd=usd_by_month['monthly'].get(ym)
        if base_usd is None or base_usd<=0:
            fail('⑨',f'customs_monthly 缺少有效对账月份 {ym}'); continue
        for sub in ('partners','province','trademode'):
            sub_usd=usd_by_month[sub].get(ym)
            if sub_usd is None:
                fail('⑨',f'customs_{sub} 缺少对账月份 {ym}'); continue
            rel_err=abs(sub_usd-base_usd)/base_usd
            if rel_err>=1e-4:
                fail('⑨',f'customs_{sub} {ym} 美元汇总 {sub_usd:,.2f} 与 monthly {base_usd:,.2f} 偏差 {rel_err:.4%} >= 0.01%')

_CL_FACT_TYPES={'工序步骤','技术参数','产品构成','代际事件','设备-工序能力'}
_CL_STANCES={'issuer_self','industry','neutral'}
_CL_QUOTE_STATUSES={'verified_local','table_normalized','segmented_verified','inherited_v1_verified'}
def _check_content_ledger(rows, tree_cells, exists=None, read_text=None):
    """⑧扩展 content_ledger.csv 校验: cid唯一非空、fact_type五分枚举、stance三分枚举、cell_ids在tree_cells或通用、verbatim_quote非空、corpus/本地源路径存在、quote_verification_status四档枚举及verified_local全文连续+#Lx..y(\\n计行)闭环."""
    if exists is None: exists=lambda rel: os.path.exists(os.path.join(ROOT,rel))
    if not rows:
        fail('⑧','content_ledger 为空或缺失'); return
    seen_cid=set()
    _src_cache={}
    for idx,r in enumerate(rows,start=2):
        cid=str(r.get('cid') or '').strip()
        if not cid:
            fail('⑧',f'content_ledger 第{idx}行 cid 为空'); continue
        if cid in seen_cid:
            fail('⑧',f'content_ledger cid重复: {cid}')
        seen_cid.add(cid)
        ft=str(r.get('fact_type') or '').strip()
        if ft not in _CL_FACT_TYPES:
            fail('⑧',f'content_ledger {cid} fact_type非法: {ft!r}')
        st=str(r.get('stance') or '').strip()
        if st not in _CL_STANCES:
            fail('⑧',f'content_ledger {cid} stance非法: {st!r}')
        raw_cells=str(r.get('cell_ids') or '').strip()
        cs=[c.strip() for c in re.split(r'[,，/、;；|\s]+',raw_cells) if c.strip()]
        if not cs:
            fail('⑧',f'content_ledger {cid} cell_ids为空')
        for c in cs:
            if c!='通用' and c not in tree_cells:
                fail('⑧',f'content_ledger {cid} cell_id {c!r} 不在tree叶格或通用')
        vq=str(r.get('verbatim_quote') or '')
        if not vq.strip():
            fail('⑧',f'content_ledger {cid} verbatim_quote为空')
        has_qvs='quote_verification_status' in r
        qvs=str(r.get('quote_verification_status') or '').strip() if has_qvs else ''
        if has_qvs and qvs not in _CL_QUOTE_STATUSES:
            fail('⑧',f'content_ledger {cid} quote_verification_status非法: {qvs!r}')
        lsp=str(r.get('local_source_path') or '').strip()
        if lsp.startswith('corpus/'):
            parts=lsp.split('#',1)
            rel=parts[0].rstrip('。."\'”’')
            frag=parts[1].strip() if len(parts)>1 else ''
            if not exists(rel):
                fail('⑧',f'content_ledger {cid} local_source_path不存在: {rel}')
            elif has_qvs and qvs=='verified_local' and vq.strip():
                if rel not in _src_cache:
                    if read_text is not None:
                        raw_s=read_text(rel)
                    elif os.path.isfile(os.path.join(ROOT,rel)) and not rel.lower().endswith('.pdf'):
                        raw_s=open(os.path.join(ROOT,rel),encoding='utf-8',errors='ignore').read()
                    else:
                        raw_s=None
                    _src_cache[rel]=None if raw_s is None else (raw_s.split('\n'), re.sub(r'\s+','',raw_s))
                cached=_src_cache[rel]
                if cached is not None:
                    nl_lines,norm_full=cached
                    norm_q=re.sub(r'\s+','',vq)
                    if norm_q not in norm_full:
                        fail('⑧',f'content_ledger {cid} verified_local 引语未在原文连续命中(疑表格拼接/节略或改字)')
                    if frag:
                        lm=re.fullmatch(r'L(\d+)\.\.(\d+)',frag)
                        if lm:
                            s_ln,e_ln=int(lm.group(1)),int(lm.group(2))
                            if s_ln<1 or e_ln<s_ln or e_ln>len(nl_lines):
                                fail('⑧',f'content_ledger {cid} #L行号区间越界: #{frag}(总行数{len(nl_lines)})')
                            else:
                                sl_norm=re.sub(r'\s+','','\n'.join(nl_lines[s_ln-1:e_ln]))
                                if norm_q not in sl_norm:
                                    fail('⑧',f'content_ledger {cid} verified_local 引语未命中声明\\n行区间 #{frag}')

_RT_SOURCE_CHANNELS={'annual_report','prospectus','sec_10k','daily_ir','daily_qa','daily_announcement'}
_CUT_CATEGORIES={'consolidated_into_group_edge','non_supply_relation','non_optical_related_or_bad_debt','non_optical_counterparty'}
def _norm_co_name(s):
    """公司简称归一化: 剥离中英文括号内容及后缀 股份有限公司/有限责任公司/有限公司."""
    v=re.sub(r'[（(].*?[）)]','',str(s or '')).strip()
    v=re.sub(r'(?:股份有限公司|有限责任公司|有限公司)$','',v).strip()
    return v

def _check_relationship_tables(timeline_rows, edge_ids, cut_rows=None, active_edges=None):
    """②扩展 relationship_timeline.csv 与 edge_negative_cuts.csv 校验: timeline_id唯一、source_edge_ids存在、source_channel合法、括号平衡无截断、负向剔除按cut_category分类防碰撞与简称归一零泄漏."""
    if not timeline_rows:
        fail('②','relationship_timeline 为空或缺失'); return
    seen_tid=set()
    for idx,r in enumerate(timeline_rows,start=2):
        tid=str(r.get('timeline_id') or '').strip()
        if not tid:
            fail('②',f'relationship_timeline 第{idx}行 timeline_id为空'); continue
        if tid in seen_tid:
            fail('②',f'relationship_timeline timeline_id重复: {tid}')
        seen_tid.add(tid)
        raw_eids=str(r.get('source_edge_ids') or '').strip()
        if raw_eids:
            for tok in [x.strip() for x in re.split(r'[;,，/\s|]+',raw_eids) if x.strip()]:
                base_eid=tok.split('#')[0].strip()
                if not re.fullmatch(r'E\d{3}',base_eid) or base_eid not in edge_ids:
                    fail('②',f'relationship_timeline {tid} source_edge_ids 引用悬空或非法边: {tok}')
        sc=str(r.get('source_channel') or '').strip()
        if sc not in _RT_SOURCE_CHANNELS:
            fail('②',f'relationship_timeline {tid} source_channel非法: {sc!r}')
        for col,val in r.items():
            v=str(val or '').strip()
            if not v or v=='-': continue
            lo=v.count('(')+v.count('（'); hi=v.count(')')+v.count('）')
            if lo!=hi:
                fail('②',f'relationship_timeline {tid} {col} 括号不平衡(左{lo}/右{hi}),疑半截截断: …{v[-30:]}')
            elif col in ('supplier','customer','value_raw','notes') and v[-1] in '，；,;-':
                fail('②',f'relationship_timeline {tid} {col} 以{v[-1]!r}结尾,疑半截截断: …{v[-30:]}')
    if cut_rows is not None:
        if not cut_rows:
            fail('②','edge_negative_cuts 为空'); return
        if active_edges is None:
            active_edges=rows('edges.csv')
        active_undir=set()
        active_norm_undir=set()
        for e in active_edges:
            s=str(e.get('供方') or e.get('supplier') or '').strip()
            d=str(e.get('需方') or e.get('customer') or '').strip()
            if s and d:
                active_undir.add((s,d)); active_undir.add((d,s))
            ns,nd=_norm_co_name(s),_norm_co_name(d)
            if ns and nd:
                active_norm_undir.add((ns,nd)); active_norm_undir.add((nd,ns))
        seen_cut=set()
        for idx,c in enumerate(cut_rows,start=2):
            if 'cut_id' in c:
                cid=str(c.get('cut_id') or '').strip()
                if not cid: fail('②',f'edge_negative_cuts 第{idx}行 cut_id为空')
                elif cid in seen_cut: fail('②',f'edge_negative_cuts cut_id重复: {cid}')
                else: seen_cut.add(cid)
            else:
                cid=f'第{idx}行'
            comp=str(c.get('company') or '').strip()
            cp=str(c.get('counterparty') or '').strip()
            cpn=str(c.get('counterparty_normalized') or cp).strip()
            isup=str(c.get('implied_supplier') or '').strip()
            icus=str(c.get('implied_customer') or '').strip()
            flag_leak=str(c.get('leaked_in_edges_csv') or '').strip().lower()=='true'
            has_cat='cut_category' in c
            cat=str(c.get('cut_category') or '').strip() if has_cat else ''
            if has_cat and cat not in _CUT_CATEGORIES:
                fail('②',f'edge_negative_cuts {cid} cut_category非法: {cat!r}')
            elif has_cat and cat=='consolidated_into_group_edge':
                if flag_leak:
                    fail('②',f'edge_negative_cuts {cid} ({comp}↔{cpn or cp}) 泄漏至活跃 edges.csv')
                reps=[x.strip() for x in re.split(r'[;,，/\s|]+',str(c.get('replacement_edge_ids') or '').strip()) if x.strip()]
                if not reps:
                    fail('②',f'edge_negative_cuts {cid} consolidated_into_group_edge 缺 replacement_edge_ids')
                else:
                    for reid in reps:
                        if not re.fullmatch(r'E\d{3}',reid) or reid not in edge_ids:
                            fail('②',f'edge_negative_cuts {cid} replacement_edge_ids 引用悬空或非法边: {reid}')
            elif has_cat and cat=='non_supply_relation':
                if flag_leak:
                    fail('②',f'edge_negative_cuts {cid} ({comp}↔{cpn or cp}) 泄漏至活跃 edges.csv')
            else:
                cand_pairs=((comp,cp),(comp,cpn),(isup,icus))
                pair_leak=any(a and b and (a,b) in active_undir for a,b in cand_pairs)
                norm_leak=any(_norm_co_name(a) and _norm_co_name(b) and (_norm_co_name(a),_norm_co_name(b)) in active_norm_undir for a,b in cand_pairs)
                if flag_leak or pair_leak or norm_leak:
                    fail('②',f'edge_negative_cuts {cid} ({comp}↔{cpn or cp}) 泄漏至活跃 edges.csv')

_DQ_PRIORITIES={'P0','P1','P2'}
_DQ_TRIGGER_TYPES={'T1_lifecycle_shift','T2_supply_relationship_or_ma','T3_commitment_verification','T4_universe_blindspot'}
_DQ_STATUSES={'ingested_to_kb','pending_primary_text','pending_filing_anchor','watch_deferred'}
_CALLS_ID_FILES=(
    ('sources.csv','source_id'),
    ('claims.csv','claim_id'),
    ('commitments.csv','commitment_id'),
    ('disclosures.csv','disclosure_id'),
    ('events.csv','event_id'),
    ('event_claims.csv','event_claim_id'),
    ('event_evidence.csv','evidence_id'),
    ('watch_entities.csv','entity_id'),
    ('universe.csv','company_id'),
)
def _load_calls_ids():
    out=set()
    for fn,pk in _CALLS_ID_FILES:
        for r in rows(os.path.join('calls',fn)):
            v=str(r.get(pk) or '').strip()
            if v: out.add(v)
    return out

def _load_kn_ids():
    kp=os.path.join(ROOT,'knowledge.yaml')
    if not os.path.exists(kp): return set()
    try:
        import yaml
        kb=(yaml.safe_load(open(kp,encoding='utf-8')) or {}).get('knowledge',[]) or []
        return {str(k.get('id') or '').strip() for k in kb if isinstance(k,dict) and str(k.get('id') or '').strip()}
    except Exception:
        return set()

def _check_daily_review_queue(q_rows, pids, eids, clg_ids, tl_ids, call_ids=None, raw_text=None, kn_ids=None):
    """⑦扩展 corpus/daily_review/review_queue.csv 校验: 非空、零内嵌\\n/\\r、DRQ####唯一、priority/trigger_type/status枚举、pending_*必填missing_verification_gate、ingested_to_kb必填kb_target_ref且按;拆分引用在对应主表真实存在."""
    if not q_rows:
        fail('⑦','daily_review/review_queue.csv 为空或缺失'); return
    if raw_text is not None:
        norm_txt=raw_text.replace('\r\n','\n')
        if '\r' in norm_txt:
            fail('⑦','daily_review/review_queue.csv 含裸\\r换行符')
        phys=len(norm_txt.rstrip('\n').split('\n')) if norm_txt.strip() else 0
        if phys!=len(q_rows)+1:
            fail('⑦',f'daily_review/review_queue.csv 物理行数({phys})≠表头+数据行({len(q_rows)+1}),存在引号内嵌入换行符')
    resolved_calls=_load_calls_ids() if call_ids is None else set(call_ids)
    resolved_kns=_load_kn_ids() if kn_ids is None else set(kn_ids)
    seen_qid=set()
    for idx,r in enumerate(q_rows,start=2):
        qid=str(r.get('queue_id') or '').strip()
        if not re.fullmatch(r'DRQ\d{4}',qid):
            fail('⑦',f'review_queue 第{idx}行 queue_id非法(须为DRQ####): {qid!r}')
        elif qid in seen_qid:
            fail('⑦',f'review_queue queue_id重复: {qid}')
        else:
            seen_qid.add(qid)
        ctx=qid or f'第{idx}行'
        for col,val in r.items():
            ks,vs=str(col or ''),str(val or '')
            if '\n' in ks or '\r' in ks or '\n' in vs or '\r' in vs:
                fail('⑦',f'review_queue {ctx} 字段 {col} 含内嵌换行符')
        pr=str(r.get('priority') or '').strip()
        if pr not in _DQ_PRIORITIES:
            fail('⑦',f'review_queue {ctx} priority非法: {pr!r}')
        tt=str(r.get('trigger_type') or '').strip()
        if tt not in _DQ_TRIGGER_TYPES:
            fail('⑦',f'review_queue {ctx} trigger_type非法: {tt!r}')
        st=str(r.get('status') or '').strip()
        if st not in _DQ_STATUSES:
            fail('⑦',f'review_queue {ctx} status非法: {st!r}')
        gate=str(r.get('missing_verification_gate') or '').strip()
        if st.startswith('pending_') and not gate:
            fail('⑦',f'review_queue {ctx} status={st} 缺非空 missing_verification_gate')
        kb_ref=str(r.get('kb_target_ref') or '').strip()
        if st=='ingested_to_kb' and not kb_ref:
            fail('⑦',f'review_queue {ctx} status=ingested_to_kb 缺非空 kb_target_ref')
        if kb_ref:
            toks=[x.strip() for x in kb_ref.split(';')]
            if any(not x for x in toks):
                fail('⑦',f'review_queue {ctx} kb_target_ref 含空分号项: {kb_ref!r}')
            for tok in [x for x in toks if x]:
                if ':' not in tok:
                    fail('⑦',f'review_queue {ctx} kb_target_ref 格式非法(须prefix:id): {tok!r}')
                    continue
                pfx,tid=tok.split(':',1)
                pfx,tid=pfx.strip(),tid.strip()
                if pfx=='points':
                    if not re.fullmatch(r'P\d{3}',tid) or tid not in pids:
                        fail('⑦',f'review_queue {ctx} kb_target_ref points引用悬空或非法: {tok}')
                elif pfx=='edges':
                    if not re.fullmatch(r'E\d{3}',tid) or tid not in eids:
                        fail('⑦',f'review_queue {ctx} kb_target_ref edges引用悬空或非法: {tok}')
                elif pfx=='content':
                    if not tid or tid not in clg_ids:
                        fail('⑦',f'review_queue {ctx} kb_target_ref content引用悬空或非法: {tok}')
                elif pfx=='timeline':
                    if not re.fullmatch(r'TL\d{4}',tid) or tid not in tl_ids:
                        fail('⑦',f'review_queue {ctx} kb_target_ref timeline引用悬空或非法: {tok}')
                elif pfx=='calls':
                    if not tid or tid not in resolved_calls:
                        fail('⑦',f'review_queue {ctx} kb_target_ref calls引用悬空或非法: {tok}')
                elif pfx=='knowledge':
                    if not re.fullmatch(r'KN\d{3}',tid) or tid not in resolved_kns:
                        fail('⑦',f'review_queue {ctx} kb_target_ref knowledge引用悬空或非法: {tok}')
                else:
                    fail('⑦',f'review_queue {ctx} kb_target_ref 前缀非法: {tok!r}')

def _check_revenue_row(r, cells):
    """⑫ 分部收入事实表行级校验(2026-08-16评审方案A). 行为与原内联循环逐字一致, 供主循环与 --selftest 调用."""
    rid=r.get('row_id','?')
    if not re.fullmatch(r'SR\d{3}',rid): fail('⑫',f'row_id须为SR###: {rid}')
    if r.get('evidence_grade','') not in ('B','C','D'): fail('⑫',f'{rid} 证据等级非法(禁A)')
    scope=r.get('mapping_scope','')
    if scope not in ('exact','mixed_scope','unmapped'): fail('⑫',f'{rid} mapping_scope非法: {scope}')
    try:
        _av=float(str(r.get('amount','')).replace(',',''))
        import math
        if not math.isfinite(_av) or _av<=0: fail('⑫',f'{rid} amount非有限正数: {r.get("amount")}')
    except ValueError: fail('⑫',f'{rid} amount非数值: {r.get("amount")}')
    if r.get('currency','') not in ('CNY','USD'): fail('⑫',f'{rid} currency非法')
    cs=[c.strip() for c in (r.get('cell_ids') or '').split(',') if c.strip()]
    if scope=='exact':
        if not cs: fail('⑫',f'{rid} exact但cell_ids为空')
        for c in cs:
            if c not in cells: fail('⑫',f'{rid} cell_id {c} 不在tree.yaml')
    elif cs: fail('⑫',f'{rid} {scope}不得挂cell_ids(混合/未映射口径)')

def _parse_date(s):
    """⑬ 严格YYYY-MM-DD(四位年-两位月-两位日, 拒绝2026-8-3); 失败返回None. 与render.py._parse_date逐字同口径."""
    from datetime import date as _date
    v=str(s or '').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        try: return _date.fromisoformat(v)
        except ValueError: return None
    return None

# 真零双通道: 严格整串匹配两通道,各四键(关键词/语料范围/检索日期/命中数),固定顺序,与render.py逐字一致
_CHAN_RE=re.compile(
    r'通道A\{(关键词)=([^;}]*);(语料范围)=([^;}]*);(检索日期)=([^;}]*);(命中数)=([^;}]*)\}'
    r'\|通道B\{(关键词)=([^;}]*);(语料范围)=([^;}]*);(检索日期)=([^;}]*);(命中数)=([^;}]*)\}')

def _check_questions_manual(cells, ship_ids, triage_ids, edge_ids, records=None, header=None, today=None):
    """⑬ questions_manual.csv 表级校验. 主调用缺省读取真实 questions_manual.csv; selftest 可传 records/header/today 走纯内存(不写临时或真实文件).
    校验: 表头逐字且无未知列 question_id,处置,理由,验收锚型,双通道记录,复核日期,会话日期; ID唯一且只按首个连字符分割;
    QA/QB→tree叶cell, QC→shipments row_id, QD→triage hit_id(无条件禁止人工裁决,并仍查ref真实),
    QE→edges edge_id; 处置仅豁免/真零; 理由/验收锚型/复核日期/会话日期必填; 日期YYYY-MM-DD且会话日期<=today<复核日期;
    豁免双通道空; 真零严格整串格式(通道A{...}|通道B{...})固定四键非空、检索日期<=会话日期、语料范围不同. 所有错误fail(⑬,...)."""
    from datetime import date as _date
    if today is None: today=_date.today()
    if records is None:
        p=os.path.join(ROOT,'questions_manual.csv')
        # 真实主调用: 文件缺失即 fail(不静默 return); 内存 selftest 走 records 分支不受影响
        if not os.path.exists(p):
            fail('⑬','questions_manual.csv 缺失(白名单内必备文件, 人工裁决车道须存在)')
            return
        rs=list(csv.DictReader(open(p,encoding='utf-8-sig')))
        with open(p,encoding='utf-8-sig') as _fh:
            try:
                _hdr=next(csv.reader(_fh))
            except StopIteration:
                fail('⑬','表头不符或缺失')
                return
    else:
        rs=records
        _hdr=header if header is not None else ['question_id','处置','理由','验收锚型','双通道记录','复核日期','会话日期']
    EXPECT=['question_id','处置','理由','验收锚型','双通道记录','复核日期','会话日期']
    if _hdr!=EXPECT:
        # 表头不符则列语义不可信, 直接返回避免次生噪音
        fail('⑬',f'表头不符(逐字须为{EXPECT}): {_hdr}')
        return
    seen=set()
    for r in rs:
        tid=(r.get('question_id') or '').strip()
        if not tid: fail('⑬','question_id 空'); continue
        if tid in seen: fail('⑬',f'question_id重复: {tid}'); continue
        seen.add(tid)
        if '-' not in tid: fail('⑬',f'{tid} 缺连字符(无法按首个连字符分割类型)'); continue
        typ,ref=tid.split('-',1)
        if typ not in ('QA','QB','QC','QD','QE'): fail('⑬',f'{tid} 类型{typ}非法(须QA/QB/QC/QD/QE)'); continue
        if typ in ('QA','QB'):
            if ref not in cells: fail('⑬',f'{tid} 引用tree叶cell {ref} 不存在')
        elif typ=='QC':
            if ref not in ship_ids: fail('⑬',f'{tid} 引用shipments row_id {ref} 不存在')
        elif typ=='QD':
            if ref not in triage_ids: fail('⑬',f'{tid} 引用triage hit_id {ref} 不存在')
            fail('⑬',f'{tid} 禁止人工裁决(QD无条件禁止人工裁决,不按triage来源判断)')
        elif typ=='QE':
            if ref not in edge_ids: fail('⑬',f'{tid} 引用edges edge_id {ref} 不存在')
        disp=(r.get('处置') or '').strip()
        if disp not in ('豁免','真零'): fail('⑬',f'{tid} 处置须为豁免/真零: {disp}')
        for col in ('理由','验收锚型','复核日期','会话日期'):
            if not (r.get(col) or '').strip(): fail('⑬',f'{tid} 必填列{col}空')
        sd=_parse_date(r.get('会话日期') or '')
        rd=_parse_date(r.get('复核日期') or '')
        if sd is None: fail('⑬',f'{tid} 会话日期格式须YYYY-MM-DD')
        if rd is None: fail('⑬',f'{tid} 复核日期格式须YYYY-MM-DD')
        if sd is not None and rd is not None:
            if not (sd<=today<rd): fail('⑬',f'{tid} 须 会话日期{sd}<=today{today}<复核日期{rd}')
        dc=(r.get('双通道记录') or '').strip()
        if disp=='豁免':
            if dc: fail('⑬',f'{tid} 豁免双通道记录须为空: {dc}')
        elif disp=='真零':
            if not dc: fail('⑬',f'{tid} 真零双通道记录必填'); continue
            m=_CHAN_RE.fullmatch(dc)
            if not m:
                fail('⑬',f'{tid} 真零双通道格式非法(须 通道A{{关键词=..;语料范围=..;检索日期=..;命中数=..}}|通道B{{...}})')
                continue
            a_kw,a_scope,a_date,a_hits,b_kw,b_scope,b_date,b_hits=(
                m.group(2),m.group(4),m.group(6),m.group(8),
                m.group(10),m.group(12),m.group(14),m.group(16))
            if any(v.strip()=='' for v in (a_kw,a_scope,a_date,a_hits,b_kw,b_scope,b_date,b_hits)):
                fail('⑬',f'{tid} 真零双通道四键值须非空'); continue
            ad=_parse_date(a_date); bd=_parse_date(b_date)
            if ad is None: fail('⑬',f'{tid} 通道A检索日期格式须YYYY-MM-DD')
            if bd is None: fail('⑬',f'{tid} 通道B检索日期格式须YYYY-MM-DD')
            if sd is not None:
                if ad is not None and ad>sd: fail('⑬',f'{tid} 通道A检索日期{ad}须<=会话日期{sd}')
                if bd is not None and bd>sd: fail('⑬',f'{tid} 通道B检索日期{bd}须<=会话日期{sd}')
            if a_scope.strip()==b_scope.strip(): fail('⑬',f'{tid} A/B语料范围须不同')

# ---- 不变量⑭：研究问题树 v2（ADR-0009）纯校验，可被 invariants() 与 --selftest 复用 ----
RQ_SYS={'root','physical','route'}
RQ_ID_RE=re.compile(r'^(RQ000|PQ\d{3}|TQ\d{3})$')
WQ_ID_RE=re.compile(r'^WQ\d{3}$')
WHY_ID_RE=re.compile(r'^WHY\d{3}$')
RB_ID_RE=re.compile(r'^RB\d{3}$')
KN_ID_RE=re.compile(r'^KN\d{3}$')
P_ID_RE=re.compile(r'^P\d{3}$')
WHY_LEVELS={'SystemNeed','Physics','Engineering','PhysicalDelta','Capability','CommercialAdoption','Economics','Investment'}
WHY_CLAIMS={'事实','行业共识','工程推论','经济推论','投资假设'}

def _validate_research(rq, why_links, kb, rb_rows, pts, tree_cells, failfn):
    """不变量⑭ 纯校验（与 invariants()/selftest 同口径）。
    rq=研究问题YAML解析(dict, 含 meta/questions/why_questions);
    why_links=WHY列表(来自 knowledge.yaml 顶层); kb=KN列表;
    rb_rows=route_bom行; pts=points行; tree_cells=cell_id集合; failfn=收集式错误函数。"""
    if not isinstance(rq, dict):
        failfn('⑭','research_questions.yaml 结构非法(非映射)'); return
    meta=rq.get('meta') or {}
    questions=rq.get('questions') or []
    wqs=rq.get('why_questions') or []
    completion=meta.get('completion_semantics') or {}
    if completion.get('linked_kn_or_why_means')!='已有材料':
        failfn('⑭','meta.completion_semantics.linked_kn_or_why_means 必须为 已有材料')
    if completion.get('linked_kn_or_why_does_not_mean')!='已完成':
        failfn('⑭','meta.completion_semantics.linked_kn_or_why_does_not_mean 必须为 已完成')
    if '人工复核' not in str(completion.get('completion_is') or ''):
        failfn('⑭','meta.completion_semantics.completion_is 必须声明人工复核')

    def _check_writeback_contract(item, item_id):
        if 'acceptance' in item:
            failfn('⑭',f'{item_id} 不得使用旧字段 acceptance')
        if not str(item.get('minimum_writeback_contract') or '').strip():
            failfn('⑭',f'{item_id} minimum_writeback_contract 缺失或为空')

    # 2. 唯一根 RQ000 / ID 合法 / parent 闭合 / 无环 / system 合法 / 分支一致
    root_id=meta.get('root_id')
    qmap={}
    for q in questions:
        qid=q.get('id')
        if not RQ_ID_RE.match(str(qid or '')):
            failfn('⑭',f'问题id非法: {qid}'); continue
        if qid in qmap:
            failfn('⑭',f'问题id重复: {qid}'); continue
        qmap[qid]=q
    if (root_id or 'RQ000')!='RQ000':
        failfn('⑭',f'meta.root_id 必须为 RQ000: {root_id}')
    if list(qmap).count('RQ000')!=1:
        failfn('⑭',f'根 RQ000 必须唯一存在且恰好一个: 实际{list(qmap).count("RQ000")}')
    children={}
    dependencies={}
    for qid,q in qmap.items():
        _check_writeback_contract(q,qid)
        sys_=q.get('system')
        if sys_ not in RQ_SYS:
            failfn('⑭',f'{qid} system非法: {sys_}')
        pid=q.get('parent_id') or None
        if qid=='RQ000':
            if pid is not None:
                failfn('⑭',f'根 RQ000 不应有 parent_id: {pid}')
        else:
            if pid is None or pid not in qmap:
                failfn('⑭',f'{qid} parent_id 悬空或缺失: {pid}')
            else:
                children.setdefault(pid,[]).append(qid)
                # 分支一致：所有祖先须 root 或同体系（PQ 只在物理、TQ 只在路线）
                # visited guard：自父/多节点环须快速失败，否则祖先链遍历会无限循环
                anc=pid
                _seen_anc={qid}
                while anc is not None:
                    if anc in _seen_anc:
                        failfn('⑭',f'{qid} 祖先链出现环(回到 {anc}): 自父或跨节点环须快速失败')
                        break
                    if anc not in qmap:
                        failfn('⑭',f'{qid} 祖先 {anc} 悬空(非问题树ID): 受控失败避免 KeyError')
                        break
                    _seen_anc.add(anc)
                    asys=qmap[anc].get('system')
                    if asys!='root' and asys!=sys_:
                        failfn('⑭',f'{qid} 祖先 {anc} 体系 {asys} 与自身 {sys_} 不一致(跨主干误挂)')
                        break
                    anc=qmap[anc].get('parent_id') or None
        if not isinstance(q.get('order'), int):
            failfn('⑭',f'{qid} order 须为整数: {q.get("order")}')
        raw_deps=q.get('depends_on',[]) or []
        if not isinstance(raw_deps,list):
            failfn('⑭',f'{qid} depends_on 须为列表: {raw_deps}')
            raw_deps=[]
        deps=[]
        for dep in raw_deps:
            if dep==qid:
                failfn('⑭',f'{qid} depends_on 不得自指')
            elif dep not in qmap:
                failfn('⑭',f'{qid} depends_on 悬空: {dep}')
            elif dep in deps:
                failfn('⑭',f'{qid} depends_on 重复: {dep}')
            else:
                deps.append(dep)
        dependencies[qid]=deps
    # 无环 (DFS 着色)
    color={i:0 for i in qmap}
    def _dfs(u):
        color[u]=1
        for v in children.get(u,[]):
            if color[v]==1: failfn('⑭',f'问题树存在环: {u}→{v}')
            elif color[v]==0: _dfs(v)
        color[u]=2
    for i in qmap:
        if color[i]==0: _dfs(i)
    # 理解依赖是独立于页面父子的 DAG；允许跨物理/路线主干，但拒绝自指、悬空和循环。
    dep_color={i:0 for i in qmap}
    def _dep_dfs(u):
        dep_color[u]=1
        for v in dependencies.get(u,[]):
            if dep_color[v]==1:
                failfn('⑭',f'问题依赖图存在环: {u}→{v}')
            elif dep_color[v]==0:
                _dep_dfs(v)
        dep_color[u]=2
    for i in qmap:
        if dep_color[i]==0:
            _dep_dfs(i)
    # 3. PQ 仅物理 / TQ 仅路线
    for qid,q in qmap.items():
        if qid.startswith('PQ') and q.get('system')!='physical':
            failfn('⑭',f'{qid} 为物理问题但 system={q.get("system")}(须physical)')
        if qid.startswith('TQ') and q.get('system')!='route':
            failfn('⑭',f'{qid} 为路线问题但 system={q.get("system")}(须route)')
    # 4. WQ 唯一 / 路线侧仅TQ / 物理侧仅PQ / 引用闭合
    wqmap={}
    for w in wqs:
        wid=w.get('id')
        if not WQ_ID_RE.match(str(wid or '')):
            failfn('⑭',f'WQ id非法: {wid}'); continue
        if wid in wqmap:
            failfn('⑭',f'WQ id重复: {wid}'); continue
        wqmap[wid]=w
        _check_writeback_contract(w,wid)
        for rq_ in (w.get('route_question_ids') or []):
            if rq_ not in qmap or not rq_.startswith('TQ'):
                failfn('⑭',f'{wid} route_question_ids 引用非TQ或悬空: {rq_}')
        for pq_ in (w.get('physical_question_ids') or []):
            if pq_ not in qmap or not pq_.startswith('PQ'):
                failfn('⑭',f'{wid} physical_question_ids 引用非PQ或悬空: {pq_}')
    # 5/6/7. KN 新字段 / 兼容 / 路线条目 / 关联点 / 跨体系
    rbid={r.get('route_item_id') for r in rb_rows}
    pids={p.get('point_id') for p in pts}
    kn_ids=set()
    for k in kb:
        i=k.get('id')
        if not KN_ID_RE.match(str(i or '')):
            failfn('⑭',f'KN id非法: {i}'); continue
        if i in kn_ids:
            failfn('⑭',f'KN id重复: {i}'); continue
        kn_ids.add(i)
        sys_=k.get('体系')
        eff='物理知识' if sys_ not in ('物理知识','技术路线') else sys_
        if sys_ is not None and sys_ not in ('物理知识','技术路线'):
            failfn('⑭',f'{i} 体系非法: {sys_}')
        for r in (k.get('研究问题') or []):
            # KN 引 WQ 的专属判断放最前：WQ 不在 qmap，若不先判会被“悬空”误报成死分支
            if r is not None and str(r).startswith('WQ'):
                failfn('⑭',f'KN 研究问题不得直接引用WQ: {r}'); continue
            if r not in qmap:
                failfn('⑭',f'{i} 研究问题引用悬空: {r}'); continue
            if r.startswith('TQ') and eff=='物理知识':
                failfn('⑭',f'物理KN {i} 不得引用TQ: {r}'); continue
            if r.startswith('PQ') and eff=='技术路线':
                failfn('⑭',f'路线KN {i} 不得引用PQ: {r}'); continue
        rb_refs=k.get('路线条目') or []
        for r in rb_refs:
            if r not in rbid:
                failfn('⑭',f'{i} 路线条目引用悬空RB: {r}')
        if eff=='技术路线' and not rb_refs:
            failfn('⑭',f'路线KN {i} 至少须有一个真实RB')
        for r in (k.get('关联点') or []):
            if r not in pids:
                failfn('⑭',f'{i} 关联点引用悬空point: {r}')
    # 8/9/10. WHY 链
    why_ids=set()
    for w in (why_links or []):
        i=w.get('id')
        if not WHY_ID_RE.match(str(i or '')):
            failfn('⑭',f'WHY id非法: {i}'); continue
        if i in why_ids:
            failfn('⑭',f'WHY id重复: {i}'); continue
        why_ids.add(i)
        if w.get('研究问题') not in wqmap:
            failfn('⑭',f'{i} 研究问题须引用WQ: {w.get("研究问题")}')
        # 路线条目 / 物理格 均须为非空列表且引用真实 ID
        rb_refs=w.get('路线条目') or []
        if not isinstance(rb_refs,list) or len(rb_refs)==0:
            failfn('⑭',f'{i} 路线条目须为非空列表且引用真实RB')
        else:
            for r in rb_refs:
                if r not in rbid:
                    failfn('⑭',f'{i} 路线条目引用悬空RB: {r}')
        pc_refs=w.get('物理格') or []
        if not isinstance(pc_refs,list) or len(pc_refs)==0:
            failfn('⑭',f'{i} 物理格须为非空列表且引用真实cell')
        else:
            for c in pc_refs:
                if c not in tree_cells:
                    failfn('⑭',f'{i} 物理格引用悬空cell: {c}')
        chain=w.get('因果链') or []
        if len(chain)<2:
            failfn('⑭',f'{i} 因果链至少两步: 实际{len(chain)}')
        seen_ord=set(); last_ord=0; seen_comm=False; seen_eco=False
        for step in chain:
            o=step.get('顺序')
            if not isinstance(o,int) or o<1:
                failfn('⑭',f'{i} 步骤顺序非法: {o}'); continue
            if o in seen_ord:
                failfn('⑭',f'{i} 步骤顺序重复: {o}'); continue
            if o!=last_ord+1:
                failfn('⑭',f'{i} 步骤顺序不连续: {o}(期望{last_ord+1})'); continue
            seen_ord.add(o); last_ord=o
            if step.get('层级') not in WHY_LEVELS:
                failfn('⑭',f'{i} 步骤层级非法: {step.get("层级")}')
            if step.get('主张类型') not in WHY_CLAIMS:
                failfn('⑭',f'{i} 步骤主张类型非法: {step.get("主张类型")}')
            if not str(step.get('陈述') or '').strip():
                failfn('⑭',f'{i} 步骤陈述为空')
            ev=step.get('证据引用') or []
            if not ev:
                failfn('⑭',f'{i} 步骤证据引用为空')
            for e in ev:
                if e not in kn_ids and e not in rbid:
                    failfn('⑭',f'{i} 步骤证据引用悬空: {e}')
            if step.get('层级')=='CommercialAdoption': seen_comm=True
            if step.get('层级')=='Economics': seen_eco=True
            if step.get('层级')=='Investment' and not (seen_comm and seen_eco):
                failfn('⑭',f'{i} Investment 须晚于 CommercialAdoption 与 Economics')
        for key in ('条件','取舍','替代方案'):
            v=w.get(key)
            if not isinstance(v,list) or len(v)==0 or not all(str(x).strip() for x in v):
                failfn('⑭',f'{i} {key}须为非空列表(且元素非空)')

def invariants():
    pts,egs,trg=rows('points.csv'),rows('edges.csv'),rows('triage.csv')
    # ①分母: annual/<code> 必在_frozen
    frozen={r['代码'] for r in rows('corpus/_frozen.csv')}
    if not frozen: fail('①','corpus/_frozen.csv 缺失或为空')
    for d in glob.glob(os.path.join(ROOT,'corpus/annual/*')):
        c=os.path.basename(d)
        if os.path.isdir(d) and c not in frozen: fail('①',f'语料目录无分母行: {c}')
    # ①补: tree.yaml / refs/*.yaml 必须可 safe_load, 且 universe.count 与 _frozen 同步
    tree_doc=None
    try:
        import yaml as _yt
        tree_doc=_yt.safe_load(open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8'))
    except Exception as e:
        fail('①',f'tree.yaml 不可 yaml.safe_load 解析: {e}')
    if tree_doc is not None: _check_tree_universe(tree_doc, len(frozen))
    for yf in sorted(glob.glob(os.path.join(ROOT,'refs','*.yaml'))+glob.glob(os.path.join(ROOT,'refs','*.yml'))):
        try:
            import yaml as _yr
            _yr.safe_load(open(yf,encoding='utf-8'))
        except Exception as e:
            fail('①',f'{os.path.relpath(yf,ROOT)} 不可 yaml.safe_load 解析: {str(e).splitlines()[0] if str(e) else e}')
    # ②端点闭合
    pid={p['point_id'] for p in pts}|{'ANON','EXT'}
    for e in egs:
        for col in ('供方point_id','需方point_id'):
            if e.get(col,'') and e[col] not in pid: fail('②',f"{e.get('edge_id')} {col}={e[col]} 悬空")
        _check_edge_integrity(e)
    rt_path=os.path.join(ROOT,'corpus/relationships/relationship_timeline.csv')
    cut_path=os.path.join(ROOT,'corpus/relationships/edge_negative_cuts.csv')
    if not os.path.exists(rt_path):
        fail('②','corpus/relationships/relationship_timeline.csv 缺失')
    elif not os.path.exists(cut_path):
        fail('②','corpus/relationships/edge_negative_cuts.csv 缺失')
    else:
        cut_rs=rows('corpus/relationships/edge_negative_cuts.csv')
        if len(cut_rs)<74: fail('②',f'edge_negative_cuts.csv 行数不足74: 实际{len(cut_rs)}')
        _check_relationship_tables(rows('corpus/relationships/relationship_timeline.csv'), {e['edge_id'] for e in egs}, cut_rows=cut_rs, active_edges=egs)
    # ③自指(零豁免): 上市且非宇宙外观察 ⇒ 公司须∈_frozen名称或代码; 宇宙外观察须在tree观察名单
    obs=observation_names()
    fro_names={r['名称'] for r in rows('corpus/_frozen.csv')}
    for p in pts:
        if p['状态']=='宇宙外观察':
            if p['公司'] not in obs: fail('③',f"{p['公司']} 宇宙外观察但不在tree观察名单")
        elif p['上市标签'] in ('A股',):
            if p['公司'] not in fro_names and not any(p['公司'] in n or n in p['公司'] for n in fro_names):
                fail('③',f"{p['公司']} A股生产点不在_frozen分母(零豁免,须先入corpus)")
    # ④单位量级
    for e in egs:
        t=e.get('数值类型','')
        if t=='金额':
            if e.get('单位','') not in E_单位: fail('④',f"{e.get('edge_id')} 金额行单位非法:[{e.get('单位')}]")
            else:
                try:
                    v=float(str(e['数值']).replace(',',''))*U2Y[e['单位']]
                    if not (1e3<=v<=5e11): fail('④',f"{e.get('edge_id')} 金额换算{v:.0f}元越界(疑单位错)")
                except: fail('④',f"{e.get('edge_id')} 数值不可解析")
        elif t=='占比':
            try:
                v=float(str(e['数值']))
                if not (0<v<=100): fail('④',f"{e.get('edge_id')} 占比{v}越界")
            except: fail('④',f"{e.get('edge_id')} 占比不可解析")
    # ⑤枚举
    for p in pts:
        if p['状态'] not in E_状态: fail('⑤',f"points {p.get('point_id')} 状态非法:{p['状态']}")
        if p['上市标签'] not in E_标签: fail('⑤',f"points {p.get('point_id')} 上市标签非法:{p['上市标签']}")
    for e in egs:
        if e.get('数值类型') and e['数值类型'] not in E_数值类型: fail('⑤',f"{e.get('edge_id')} 数值类型非法")
        if e.get('边等级') and e['边等级'] not in E_边等级: fail('⑤',f"{e.get('edge_id')} 边等级非法:{e['边等级']}")
    for t in trg:
        if t['来源'] not in E_来源: fail('⑤',f"triage {t.get('hit_id')} 来源非法")
        if t['处置'] not in E_处置: fail('⑤',f"triage {t.get('hit_id')} 处置非法")
    for i,l in enumerate(open(os.path.join(ROOT,'words.txt'),encoding='utf-8')) if os.path.exists(os.path.join(ROOT,'words.txt')) else []:
        if l.strip() and not l.startswith('#') and l.count('|')!=3: fail('⑤',f"words.txt 第{i+1}行竖线数≠3")
    # ⑥白名单
    # 白名单唯一来源就是本处：.githooks/pre-commit 只调用 scan.py --check，不再重复定义(曾因两处各写一份一天卡闸三次)。
    # '.git': worktree 下 .git 是文件不是目录,不列入则误报越位(远程代理绕闸根因)
    WL={'README.md','CLAUDE.md','AGENTS.md','tree.yaml','knowledge.yaml','points.csv','edges.csv','triage.csv','words.txt',
        'scan.py','render.py','participation.py','make_participation_pdf.py',
        'build_detailed_capability_report.py','capability_details.csv',
        'route_bom.csv','macro_evidence.csv','shipments.csv','company_segment_revenue.csv',
        'research_questions.yaml','questions_manual.csv','pytest.ini',
        'RESTART-v2.md','CONTEXT.md','.gitignore','.gitattributes','.git','.DS_Store'}
    for f in os.listdir(ROOT):
        if os.path.isfile(os.path.join(ROOT,f)) and f not in WL: fail('⑥',f'根目录白名单外文件: {f}')
    refs=os.listdir(os.path.join(ROOT,'refs')) if os.path.isdir(os.path.join(ROOT,'refs')) else []
    if len(refs)>8: fail('⑥',f'refs/文件数{len(refs)}>8(2026-08-04由6放宽,纪律4)')
    for m in glob.glob(os.path.join(ROOT,'**/*.md'),recursive=True):
        rel=os.path.relpath(m,ROOT)
        if not rel.startswith(('archive/','refs/','out/','corpus/','calls/','docs/','knowledge-daily/')) and rel not in ('README.md','CLAUDE.md','AGENTS.md','RESTART-v2.md','CONTEXT.md'):
            fail('⑥',f'越位md: {rel}')
    # ⑦triage一致性
    pnames={p['公司'] for p in pts}
    for t in trg:
        if t['处置']=='已入点' and t['公司'] not in pnames: fail('⑦',f"triage {t['hit_id']} 已入点但points无此公司")
    _check_triage_ids(trg)
    _wl_cells=_tree_leaf_cells(tree_doc) if tree_doc is not None else set(re.findall(r'cell_id:\s*([A-Za-z0-9]+)',open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8').read()))
    _check_watchlist(rows('corpus/_restart_watchlist.csv'), _wl_cells)
    # ⑧知识库: 无证据的"常识"不许入库;锚按型核验("已核验"三个字过不了闸)
    kp=os.path.join(ROOT,'knowledge.yaml')
    treetext=open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8').read()
    cells=set(re.findall(r'cell_id:\s*([A-Za-z0-9]+)',treetext))
    eids={e['edge_id'] for e in egs}
    pids={p['point_id'] for p in pts}
    kn_ids=set()
    if os.path.exists(kp):
        try:
            import yaml; kb=yaml.safe_load(open(kp,encoding='utf-8')).get('knowledge',[]) or []
        except Exception as e:
            kb=[]; fail('⑧',f'knowledge.yaml 不可解析: {e}')
        for k in kb:
            i=k.get('id','?')
            if not re.fullmatch(r'KN\d{3}',str(i)): fail('⑧',f'知识id须为KN###: {i}')
            if i in kn_ids: fail('⑧',f'知识id重复: {i}')
            kn_ids.add(i)
            for f_ in ('标题','一句话'):
                if not (k.get(f_) or '').strip(): fail('⑧',f'{i} 缺{f_}')
            ev=k.get('证据') or []
            if not ev: fail('⑧',f'{i} 无证据(无证据的常识不入知识库)')
            for j,e in enumerate(ev):
                for f_ in ('谁','出处','锚型','锚'):
                    if not str(e.get(f_,'') or '').strip(): fail('⑧',f'{i} 证据[{j}] 缺{f_}'); break
                else:
                    t,a=e['锚型'],e['锚']
                    if t=='url':
                        if not str(a).startswith(('http://','https://')): fail('⑧',f'{i} 证据[{j}] url锚非链接: {str(a)[:40]}')
                    elif t=='local_file':
                        if '#' not in str(a): fail('⑧',f'{i} 证据[{j}] local_file锚缺#定位: {str(a)[:60]}')
                        elif not os.path.exists(os.path.join(ROOT,str(a).split('#')[0])): fail('⑧',f'{i} 证据[{j}] 文件不存在: {str(a).split("#")[0]}')
                    elif t=='ledger_ref':
                        if str(a) not in pids|eids: fail('⑧',f'{i} 证据[{j}] ledger_ref {a} 不在points/edges')
                    elif t=='search_protocol':
                        if not isinstance(a,dict) or not all(x in a for x in ('关键词','语料范围','检索日期','命中数')):
                            fail('⑧',f'{i} 证据[{j}] search_protocol须含 关键词/语料范围/检索日期/命中数')
                    elif t=='web_snapshot':
                        if not isinstance(a,dict) or not all(x in a for x in ('原URL','存档路径','抓取日期')):
                            fail('⑧',f'{i} 证据[{j}] web_snapshot须含 原URL/存档路径/抓取日期')
                        else:
                            if not str(a['原URL']).startswith(('http://','https://')): fail('⑧',f'{i} 证据[{j}] web_snapshot原URL非法')
                            if not os.path.exists(os.path.join(ROOT,str(a['存档路径']))): fail('⑧',f'{i} 证据[{j}] web_snapshot存档不存在: {a["存档路径"]}')
                    else: fail('⑧',f'{i} 证据[{j}] 锚型非法: {t}')
            for c in (k.get('格') or []):
                if c not in cells: fail('⑧',f'{i} 格 {c} 不在tree.yaml')
    # tree引用闭合: knowledge_ids/decision_ref 必须指向真实知识条目
    for ref in re.findall(r'knowledge_ids:\s*\[([^\]]*)\]',treetext):
        for x in [y.strip() for y in ref.split(',') if y.strip()]:
            if x not in kn_ids: fail('⑧',f'tree knowledge_ids {x} 不在knowledge.yaml')
    for x in re.findall(r'decision_ref:\s*(\S+?)[,}]',treetext):
        if x not in kn_ids: fail('⑧',f'tree decision_ref {x} 不在knowledge.yaml')
    cl_path=os.path.join(ROOT,'corpus/content_ledger/content_ledger.csv')
    cl_rows=[]
    if not os.path.exists(cl_path):
        fail('⑧','corpus/content_ledger/content_ledger.csv 缺失')
    else:
        cl_rows=rows('corpus/content_ledger/content_ledger.csv')
        _check_content_ledger(cl_rows, _wl_cells)
    dq_path=os.path.join(ROOT,'corpus/daily_review/review_queue.csv')
    if not os.path.exists(dq_path):
        fail('⑦','corpus/daily_review/review_queue.csv 缺失')
    else:
        import io as _io
        dq_raw=open(dq_path,encoding='utf-8-sig',newline='').read()
        dq_rows=list(csv.DictReader(_io.StringIO(dq_raw)))
        clg_ids={str(r.get('cid') or '').strip() for r in cl_rows if str(r.get('cid') or '').strip()}
        tl_ids={str(r.get('timeline_id') or '').strip() for r in rows('corpus/relationships/relationship_timeline.csv') if str(r.get('timeline_id') or '').strip()}
        _check_daily_review_queue(dq_rows, pids, eids, clg_ids, tl_ids, call_ids=_load_calls_ids(), raw_text=dq_raw, kn_ids=kn_ids)
    # ⑨路线投影与宏观结论: route_bom每行必须映射或说明;宏观须MC###+A-D级
    rb=rows('route_bom.csv')
    rbid=set()
    for r in rb:
        i=r.get('route_item_id','?')
        if not re.fullmatch(r'RB\d{3}',i): fail('⑨',f'route_bom id须为RB###: {i}')
        if i in rbid: fail('⑨',f'route_bom id重复: {i}')
        rbid.add(i)
        st=r.get('mapping_status','')
        if st not in ('mapped','architecture_only','gap'): fail('⑨',f'{i} mapping_status非法: {st}')
        cs=[c.strip() for c in (r.get('cell_ids') or '').split(',') if c.strip()]
        for c in cs:
            if c not in cells: fail('⑨',f'{i} cell_id {c} 不在tree.yaml')
        if st=='mapped' and not cs: fail('⑨',f'{i} mapped但cell_ids为空')
        if st in ('architecture_only','gap') and not (r.get('mapping_note') or '').strip(): fail('⑨',f'{i} {st}须给mapping_note说明为何不映射')
    for r in rows('macro_evidence.csv'):
        if not re.fullmatch(r'MC\d{3}',r.get('claim_id','?')): fail('⑨',f"macro claim_id须为MC###: {r.get('claim_id')}")
        if r.get('证据等级') not in ('A','B','C','D'): fail('⑨',f"macro {r.get('claim_id')} 证据等级非法")
        _check_macro_row(r)
    _check_customs_tables()
    # ⑧/⑩ points 锚点卫士: URL畸形/搜索占位、本地 corpus 路径存在性、A股异司共用巨潮PDF
    for p in pts: _check_point_row(p)
    _check_point_table(pts)
    # ⑪出货量推断层: shipments.csv 行级校验(ADR-0001)
    if os.path.exists(os.path.join(ROOT,'shipments.csv')):
        for r in rows('shipments.csv'):
            _check_shipment_row(r)
    # ⑫分部收入事实表(2026-08-16评审方案A): 收入事实独立成层,与出货量数量事实机器可分
    if os.path.exists(os.path.join(ROOT,'company_segment_revenue.csv')):
        for r in rows('company_segment_revenue.csv'):
            _check_revenue_row(r, cells)
    # ⑩互动易qa车道: jsonl格式合法+必备键;点锚引用的qa快照必须存在且真含引语
    for qf in glob.glob(os.path.join(ROOT,'corpus/qa/*/qa.jsonl')):
        try:
            import json as _j
            for i,l in enumerate(open(qf,encoding='utf-8')):
                o=_j.loads(l)
                for k in ('code','question','answer','answer_date','index_id','empty','fetch_date'):
                    if k not in o: fail('⑩',f'{os.path.basename(os.path.dirname(qf))} qa.jsonl 第{i+1}行缺{k}'); break
        except Exception as e: fail('⑩',f'{qf} 不可解析: {e}')
    for p in pts:
        m=re.search(r'corpus/qa/(\d+)/qa\.jsonl',p.get('锚点URL','') or '')
        if m:
            qf=os.path.join(ROOT,f'corpus/qa/{m.group(1)}/qa.jsonl')
            if not os.path.exists(qf): fail('⑩',f"{p['point_id']} 引用qa快照不存在: {m.group(1)}"); continue
            quote=re.sub(r'\s+','',(p.get('命中引语') or '').strip('"').split('(互动易')[0].strip('"'))
            blob=re.sub(r'\s+','',open(qf,encoding='utf-8').read())
            if quote and quote not in blob: fail('⑩',f"{p['point_id']} 引语未在qa快照命中")
    # ⑬ questions_manual.csv 表级校验(从真实文件构造ID集合)
    ship_ids={r['row_id'] for r in rows('shipments.csv')}
    triage_ids={t['hit_id'] for t in trg}
    edge_ids={e['edge_id'] for e in egs}
    _check_questions_manual(cells, ship_ids, triage_ids, edge_ids)
    # ⑭ 研究问题树 v2（ADR-0009）：研究问题文件 + knowledge 新字段(体系/研究问题/路线条目/关联点/why_links)
    rq_path=os.path.join(ROOT,'research_questions.yaml')
    if not os.path.exists(rq_path):
        fail('⑭','research_questions.yaml 缺失(白名单内必备文件)')
    else:
        try:
            import yaml as _y
            rq=_y.safe_load(open(rq_path,encoding='utf-8'))
        except Exception as e:
            fail('⑭',f'research_questions.yaml 不可解析: {e}'); rq=None
        if rq is not None:
            kb2=[]; why_links=[]
            kp2=os.path.join(ROOT,'knowledge.yaml')
            if os.path.exists(kp2):
                try:
                    kd=_y.safe_load(open(kp2,encoding='utf-8')) or {}
                    kb2=kd.get('knowledge',[]) or []
                    why_links=kd.get('why_links',[]) or []
                except Exception as e:
                    fail('⑭',f'knowledge.yaml 不可解析: {e}')
            rb_rows=rows('route_bom.csv'); pts2=rows('points.csv')
            tree_text=open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8').read()
            tree_cells=set(re.findall(r'cell_id:\s*([A-Za-z0-9]+)',tree_text))
            _validate_research(rq, why_links, kb2, rb_rows, pts2, tree_cells, fail)



def scan():
    """全量扫描: words×corpus/annual → 净队列(剔除triage已处置), 空叶格优先(P6), hit_id=公司+cell+文件(P7)"""
    words=[]
    for l in open(os.path.join(ROOT,'words.txt'),encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            w,cell,ex,ctx=[x.strip() for x in l.split('|')]
            words.append((w,cell,ex,ctx))
    done={t['hit_id'] for t in rows('triage.csv')}
    pts=rows('points.csv'); filled={p['cell_id'] for p in pts}; known_companies={p['公司'] for p in pts}
    frozen={}
    fz_path=os.path.join(ROOT,'corpus/_frozen.csv')
    if os.path.exists(fz_path):
        for r in rows('corpus/_frozen.csv'): frozen[r['代码']]=r['名称']
    q=[]
    def recall_file(txt, co, fname):
        """单个语料文本跑词表,命中入净队列(公司名/代码双轨:annual按_em_文件名,ir按_frozen代码映射)"""
        try: t=re.sub(r'\s+','',open(txt,encoding='utf-8',errors='ignore').read())
        except: return
        for w,cell,ex,ctx in words:
            if cell=='ANY' and co in known_companies: continue
            for mm in list(re.finditer(re.escape(w),t))[:2]:
                seg=t[max(0,mm.start()-40):mm.end()+40]
                if ex and re.search(ex,seg): continue
                if ctx and ctx not in seg: continue
                hid=f'{co}+{cell}+{fname[:40]}'
                if hid in done: continue
                priority=1 if cell=='ANY' else (0 if cell not in filled else 2)
                q.append((priority,hid,co,cell,w,seg))
                break
    for d in sorted(glob.glob(os.path.join(ROOT,'corpus/annual/*/'))):
        for pdf in glob.glob(d+'**/*.pdf',recursive=True):
            txt=pdf+'.txt'
            if not os.path.exists(txt): subprocess.run(['pdftotext','-layout',pdf,txt],capture_output=True)
            m=re.search(r'_([^_]+)_em_',os.path.basename(pdf)); co=m.group(1) if m else os.path.basename(d.rstrip('/'))
            recall_file(txt, co, os.path.basename(pdf))
    # 投关表车道(2026-07-30接入): pdf现抽/docx读fetcher预解的.txt旁车
    for d in sorted(glob.glob(os.path.join(ROOT,'corpus/ir/*/'))):
        code=os.path.basename(d.rstrip('/')); co=frozen.get(code,code)
        for f in sorted(glob.glob(d+'*')):
            if f.endswith('.pdf'):
                txt=f+'.txt'
                if not os.path.exists(txt): subprocess.run(['pdftotext','-layout',f,txt],capture_output=True)
                recall_file(txt, co, os.path.basename(f))
            elif f.endswith('.docx') and os.path.exists(f+'.txt'):
                recall_file(f+'.txt', co, os.path.basename(f))
    q.sort()
    print(f'净队列 {len(q)} 条(空叶格优先排序)')
    labels={0:'空格',1:'参与',2:'  '}
    for pr,hid,co,cell,w,seg in q[:40]: print(f'  [{labels[pr]}] {co} | {cell} | {w} | {seg[:50]}')
    return q

def selftest():
    """--selftest: 纯内存 fixture 回归 ⑪/⑫/⑬ 校验, 不读写真实csv(⑬ 传内存 records/header, 不写临时或真实文件).
    fail() 为收集式(仅追加 ERR,不 sys.exit/不抛异常), 故逐用例直接调用校验函数,
    以调用前后 ERR 增量判定该用例是否触发拦截. 任一用例 FAIL 则返回非0."""
    total=0; fails=0
    def case(name, fn, expect_fail):
        nonlocal total, fails
        total+=1
        before=len(ERR)
        try:
            fn()
            added=ERR[before:]
        except Exception as e:  # 越界异常也视为校验未生效 → FAIL(防御性,不影响正常路径)
            added=[f'EXC: {e}']
        delta=len(added)
        ok=(delta>0) if expect_fail else (delta==0)
        if ok:
            print(f'[PASS] {name}')
        else:
            fails+=1
            print(f'[FAIL] {name} :: {"; ".join(added) if added else "(期望失败却无fail触发)"}')
        del ERR[before:]  # 隔离用例, 避免污染后续 delta 统计
    # ---- ⑪ shipments.csv ----
    def f_ship_good(): _check_shipment_row({'row_id':'SE001','证据等级':'B','情景标记':'','单位':'只','出货量':'1000'})
    case('⑪ 正例: 正常行通过', f_ship_good, expect_fail=False)
    for bad_qty in ('nan','inf','-','abc',''):
        def f(q=bad_qty): _check_shipment_row({'row_id':'SE002','证据等级':'B','情景标记':'','单位':'只','出货量':q})
        case(f'⑪ 反例: 出货量={bad_qty!r} 被拦', f, expect_fail=True)
    case('⑪ 反例: 单位=- 被拦', lambda: _check_shipment_row({'row_id':'SE003','证据等级':'B','情景标记':'','单位':'-','出货量':'1000'}), True)
    case('⑪ 反例: 证据等级=A 被拦', lambda: _check_shipment_row({'row_id':'SE004','证据等级':'A','情景标记':'','单位':'只','出货量':'1000'}), True)
    case('⑪ 反例: scenario非D 被拦', lambda: _check_shipment_row({'row_id':'SE005','证据等级':'C','情景标记':'scenario_abc','单位':'只','出货量':'1000'}), True)
    # ---- ⑫ company_segment_revenue.csv ----
    cells_full={'D1','MOD1','D9'}  # 含本组用例所需格
    def f_rev_exact(): _check_revenue_row({'row_id':'SR001','evidence_grade':'B','mapping_scope':'exact','amount':'100','currency':'CNY','cell_ids':'D1'}, cells_full)
    case('⑫ 正例: exact+有效cell通过', f_rev_exact, expect_fail=False)
    def f_rev_mixed(): _check_revenue_row({'row_id':'SR002','evidence_grade':'C','mapping_scope':'mixed_scope','amount':'50','currency':'USD','cell_ids':''}, cells_full)
    case('⑫ 正例: mixed_scope+空cell_ids通过', f_rev_mixed, expect_fail=False)
    for bad_amt in ('nan','inf','0','-5'):
        def f(a=bad_amt): _check_revenue_row({'row_id':'SR003','evidence_grade':'B','mapping_scope':'exact','amount':a,'currency':'CNY','cell_ids':'D1'}, cells_full)
        case(f'⑫ 反例: amount={bad_amt!r} 被拦', f, expect_fail=True)
    case('⑫ 反例: currency=JPY 被拦', lambda: _check_revenue_row({'row_id':'SR004','evidence_grade':'B','mapping_scope':'exact','amount':'100','currency':'JPY','cell_ids':'D1'}, cells_full), True)
    case('⑫ 反例: exact但cell_ids空 被拦', lambda: _check_revenue_row({'row_id':'SR005','evidence_grade':'B','mapping_scope':'exact','amount':'100','currency':'CNY','cell_ids':''}, cells_full), True)
    case('⑫ 反例: mixed_scope挂cell_ids 被拦', lambda: _check_revenue_row({'row_id':'SR006','evidence_grade':'B','mapping_scope':'mixed_scope','amount':'100','currency':'CNY','cell_ids':'D1'}, cells_full), True)
    case('⑫ 反例: cell_ids含树外格子 被拦', lambda: _check_revenue_row({'row_id':'SR007','evidence_grade':'B','mapping_scope':'exact','amount':'100','currency':'CNY','cell_ids':'ZZ1'}, {'MOD1','D9'}), True)
    # ---- ⑬ questions_manual.csv ----
    from datetime import date as _d, timedelta as _t
    T=_d.today()  # 动态基准日, 日期用例全部以 date.today + timedelta 构造
    def dstr(dt): return dt.isoformat()
    HDR=['question_id','处置','理由','验收锚型','双通道记录','复核日期','会话日期']
    cells_q={'D1'}      # 含本组用例所需格
    ship_q={'SE001'}    # 含本组用例所需出货量ID
    triage_q={'HIT-A-B'}# 含本组用例所需triage ID
    edge_q={'E001'}     # 含本组用例所需edge ID
    def qm_row(qid, disp, dc='', rd=None, sd=None):
        return {'question_id':qid,'处置':disp,'理由':'r','验收锚型':'a',
                '双通道记录':dc,
                '复核日期':rd if rd is not None else dstr(T+_t(days=1)),
                '会话日期':sd if sd is not None else dstr(T-_t(days=1))}
    def run_qm(rows): _check_questions_manual(cells_q, ship_q, triage_q, edge_q, records=rows, header=HDR, today=T)
    # 真零双通道正例串: A/B语料范围不同, 四键非空, 检索日期<=会话日期
    _cd=dstr(T-_t(days=2))
    DC_OK='通道A{关键词=kA;语料范围=scopeA;检索日期=%s;命中数=5}|通道B{关键词=kB;语料范围=scopeB;检索日期=%s;命中数=3}' % (_cd,_cd)
    # 正例1: 豁免 + 未来复核日期(sd<=today<rd) 放行
    def f_qm_exempt_future(): run_qm([qm_row('QA-D1','豁免')])
    case('⑬ 正例: 豁免 未来复核日期(sd<=today<rd)通过', f_qm_exempt_future, expect_fail=False)
    # 正例2: 真零 + A/B独立语料严格整串 放行
    def f_qm_truezero(): run_qm([qm_row('QA-D1','真零', dc=DC_OK)])
    case('⑬ 正例: 真零 A/B独立语料严格字符串通过', f_qm_truezero, expect_fail=False)
    # 反例: QD 无条件禁止人工裁决
    def f_qm_qd(): run_qm([qm_row('QD-HIT-A-B','豁免')])
    case('⑬ 反例: QD人工裁决被拦', f_qm_qd, expect_fail=True)
    # 反例: 重复 question_id
    def f_qm_dup(): run_qm([qm_row('QA-D1','豁免'), qm_row('QA-D1','豁免')])
    case('⑬ 反例: 重复question_id被拦', f_qm_dup, expect_fail=True)
    # 反例: 豁免缺复核日期(必填+格式双拦截)
    def f_qm_exempt_nord(): run_qm([qm_row('QA-D1','豁免', rd='')])
    case('⑬ 反例: 豁免缺复核日期被拦', f_qm_exempt_nord, expect_fail=True)
    # 反例: 复核日期等于今天(today<rd 不成立)
    def f_qm_rd_today(): run_qm([qm_row('QA-D1','豁免', rd=dstr(T))])
    case('⑬ 反例: 复核日期等于今天被拦', f_qm_rd_today, expect_fail=True)
    # 反例: 复核日期早于今天(today<rd 不成立)
    def f_qm_rd_past(): run_qm([qm_row('QA-D1','豁免', rd=dstr(T-_t(days=1)))])
    case('⑬ 反例: 复核日期早于今天被拦', f_qm_rd_past, expect_fail=True)
    # 反例: 日期未补零(2026-8-3 口径, 须与render.py一致拒绝)
    def f_qm_date_nopad(): run_qm([qm_row('QA-D1','豁免', rd='%d-8-3'%(T.year+1))])
    case('⑬ 反例: 复核日期未补零(YYYY-M-D)被拦', f_qm_date_nopad, expect_fail=True)
    # 反例: 豁免误填双通道
    def f_qm_exempt_chan(): run_qm([qm_row('QA-D1','豁免', dc=DC_OK)])
    case('⑬ 反例: 豁免误填双通道被拦', f_qm_exempt_chan, expect_fail=True)
    # 反例: 真零缺双通道记录
    def f_qm_truezero_nodc(): run_qm([qm_row('QA-D1','真零', dc='')])
    case('⑬ 反例: 真零缺通道被拦', f_qm_truezero_nodc, expect_fail=True)
    # 反例: 真零缺键(整串格式非法, 缺通道B)
    DC_MISSB='通道A{关键词=kA;语料范围=scopeA;检索日期=%s;命中数=5}' % _cd
    def f_qm_truezero_misskey(): run_qm([qm_row('QA-D1','真零', dc=DC_MISSB)])
    case('⑬ 反例: 真零缺键(格式非法)被拦', f_qm_truezero_misskey, expect_fail=True)
    # 反例: 真零四键值空(A命中数为空)
    DC_EMPTY='通道A{关键词=kA;语料范围=scopeA;检索日期=%s;命中数=}|通道B{关键词=kB;语料范围=scopeB;检索日期=%s;命中数=3}' % (_cd,_cd)
    def f_qm_truezero_emptyval(): run_qm([qm_row('QA-D1','真零', dc=DC_EMPTY)])
    case('⑬ 反例: 真零键值空被拦', f_qm_truezero_emptyval, expect_fail=True)
    # 反例: 真零 A/B语料范围相同
    DC_SAME='通道A{关键词=kA;语料范围=same;检索日期=%s;命中数=5}|通道B{关键词=kB;语料范围=same;检索日期=%s;命中数=3}' % (_cd,_cd)
    def f_qm_truezero_samescope(): run_qm([qm_row('QA-D1','真零', dc=DC_SAME)])
    case('⑬ 反例: 真零A/B语料范围相同被拦', f_qm_truezero_samescope, expect_fail=True)
    # 反例: 来源ID不存在(cell ZZ9 不在cells)
    def f_qm_badref(): run_qm([qm_row('QA-ZZ9','豁免')])
    case('⑬ 反例: 来源ID(cell ZZ9)不存在被拦', f_qm_badref, expect_fail=True)
    # ---- ⑭ research_questions.yaml + knowledge.yaml why_links ----
    def _rq_base():
        return {
            'meta':{
                'version':'v2','root_id':'RQ000','answer_target':'knowledge.yaml',
                'completion_semantics':{
                    'linked_kn_or_why_means':'已有材料',
                    'linked_kn_or_why_does_not_mean':'已完成',
                    'completion_is':'由人工复核判定',
                },
            },
            'questions':[
                {'id':'RQ000','parent_id':None,'system':'root','order':0,'question':'r','writeback':'knowledge','minimum_writeback_contract':'a'},
                {'id':'PQ001','parent_id':'RQ000','system':'physical','order':1,'question':'p','writeback':'knowledge','minimum_writeback_contract':'a'},
                {'id':'PQ002','parent_id':'PQ001','system':'physical','order':2,'question':'p2','writeback':'knowledge','minimum_writeback_contract':'a'},
                {'id':'TQ001','parent_id':'RQ000','system':'route','order':1,'question':'t','writeback':'knowledge','minimum_writeback_contract':'a'},
            ],
            'why_questions':[
                {'id':'WQ001','order':1,'route_question_ids':['TQ001'],'physical_question_ids':['PQ001'],
                 'relation_type':'need_to_constraint','question':'w','writeback':'why_links','minimum_writeback_contract':'a'},
            ],
        }
    def _kb_base():
        return [
            {'id':'KN001','体系':'物理知识','研究问题':['PQ001'],'格':['C1'],'关联点':['P001']},
            {'id':'KN002','体系':'技术路线','研究问题':['TQ001'],'路线条目':['RB001'],'关联点':['P001']},
        ]
    _RB=[{'route_item_id':'RB001'}]
    _PT=[{'point_id':'P001','cell_id':'C1','公司':'X'}]
    _CELL={'C1'}
    def _run14(rq=None,kb=None,why=None,rb=_RB,pts=_PT,cells=_CELL):
        rq=rq if rq is not None else _rq_base()
        kb=kb if kb is not None else _kb_base()
        why=why if why is not None else []
        _validate_research(rq, why, kb, rb, pts, cells, fail)
    # 正例：完整树 + 两个合法 KN + 空 why
    case('⑭ 正例: 完整问题树+合法KN通过', lambda:_run14(), expect_fail=False)
    def f_missing_writeback_contract():
        rq=_rq_base(); del rq['questions'][1]['minimum_writeback_contract']; _run14(rq=rq)
    case('⑭ 反例: minimum_writeback_contract 缺失被拦', f_missing_writeback_contract, expect_fail=True)
    def f_legacy_acceptance():
        rq=_rq_base(); rq['questions'][1]['acceptance']=rq['questions'][1].pop('minimum_writeback_contract'); _run14(rq=rq)
    case('⑭ 反例: 旧 acceptance 字段被拦', f_legacy_acceptance, expect_fail=True)
    # 反例：重复 ID
    def f_dup():
        rq=_rq_base(); rq['questions'].append({'id':'PQ001','parent_id':'RQ000','system':'physical','order':3,'question':'x','writeback':'knowledge','minimum_writeback_contract':'a'})
        _run14(rq=rq)
    case('⑭ 反例: 问题id重复被拦', f_dup, expect_fail=True)
    # 反例：悬空 parent
    def f_dparent():
        rq=_rq_base(); rq['questions'][1]['parent_id']='RQ999'; _run14(rq=rq)
    case('⑭ 反例: 悬空parent被拦', f_dparent, expect_fail=True)
    # 反例：环（自指）
    def f_cycle():
        rq=_rq_base(); rq['questions'][2]['parent_id']='PQ002'; _run14(rq=rq)
    case('⑭ 反例: 问题树成环被拦', f_cycle, expect_fail=True)
    # 正例：页面父子保持树形，真实理解依赖可跨主干且允许多依赖。
    def f_dep_ok():
        rq=_rq_base(); rq['questions'][2]['depends_on']=['PQ001','TQ001']; _run14(rq=rq)
    case('⑭ 正例: 问题多依赖跨主干通过', f_dep_ok, expect_fail=False)
    # 反例：依赖悬空。
    def f_dep_missing():
        rq=_rq_base(); rq['questions'][2]['depends_on']=['PQ999']; _run14(rq=rq)
    case('⑭ 反例: 问题依赖悬空被拦', f_dep_missing, expect_fail=True)
    # 反例：parent 树无环，但 depends_on 图形成循环。
    def f_dep_cycle():
        rq=_rq_base(); rq['questions'][1]['depends_on']=['PQ002']; rq['questions'][2]['depends_on']=['PQ001']; _run14(rq=rq)
    case('⑭ 反例: 问题依赖图成环被拦', f_dep_cycle, expect_fail=True)
    # 反例：WQ 跨侧（路线侧引用 PQ）
    def f_wqcross():
        rq=_rq_base(); rq['why_questions'][0]['route_question_ids']=['PQ001']; _run14(rq=rq)
    case('⑭ 反例: WQ路线侧误挂PQ被拦', f_wqcross, expect_fail=True)
    # 反例：KN 跨体系（物理 KN 引用 TQ）
    def f_kncross():
        kb=_kb_base(); kb[0]['研究问题']=['TQ001']; _run14(kb=kb)
    case('⑭ 反例: 物理KN引用TQ被拦', f_kncross, expect_fail=True)
    # 反例：悬空 RB
    def f_rb():
        kb=_kb_base(); kb[1]['路线条目']=['RB999']; _run14(kb=kb)
    case('⑭ 反例: 路线KN悬空RB被拦', f_rb, expect_fail=True)
    # 反例：悬空 point
    def f_pt():
        kb=_kb_base(); kb[0]['关联点']=['P999']; _run14(kb=kb)
    case('⑭ 反例: KN悬空point被拦', f_pt, expect_fail=True)
    # 反例：WHY 步骤乱序
    def f_whyorder():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
              '因果链':[{'顺序':2,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':1,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case('⑭ 反例: WHY因果链乱序被拦', f_whyorder, expect_fail=True)
    # 反例：WHY 空三项
    def f_whyempty():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
              '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
              '条件':[],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case('⑭ 反例: WHY条件为空被拦', f_whyempty, expect_fail=True)
    # 反例：Investment 越级（前无 CommercialAdoption/Economics）
    def f_inv():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
              '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'Investment','主张类型':'投资假设','陈述':'s2','证据引用':['KN002']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case('⑭ 反例: Investment越过CommercialAdoption/Economics被拦', f_inv, expect_fail=True)
    # 正例：WHY 完整且 Investment 顺序合法（含 CommercialAdoption+Economics 在前）
    def f_whyok():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
              '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'CommercialAdoption','主张类型':'事实','陈述':'s2','证据引用':['RB001']},
                        {'顺序':3,'层级':'Economics','主张类型':'经济推论','陈述':'s3','证据引用':['KN002']},
                        {'顺序':4,'层级':'Investment','主张类型':'投资假设','陈述':'s4','证据引用':['KN002']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case('⑭ 正例: WHY完整链+Investment顺序合法通过', f_whyok, expect_fail=False)
    # ---- 精确⑭用例（逐项对照 Kimi 评审 2/3/4/5）：要求触发「受控 failfn」而非异常 ----
    # 异常(EXC)会被 case() 的 except 误判为 delta>0 → 反例被算作 PASS，故这里单独判定：
    # 必须出现预期受控 fail 文案，且不得是 EXC（异常一律判 FAIL，杜绝伪装成通过）。
    def case_why(name, fn, expect_substr):
        nonlocal total, fails
        total+=1
        before=len(ERR)
        try:
            fn()
            added=ERR[before:]
        except Exception as e:
            fails+=1
            print(f'[FAIL] {name} :: 触发异常(应为受控fail而非EXC): {e}')
            del ERR[before:]
            return
        if any(expect_substr in a for a in added):
            print(f'[PASS] {name}')
        else:
            fails+=1
            print(f'[FAIL] {name} :: 期望含 {expect_substr!r}, 实际: {"; ".join(added) if added else "(无fail触发)"}')
        del ERR[before:]
    # 2) 空 路线条目：[待触发] f'{i} 路线条目须为非空列表且引用真实RB'
    def f_why_emptyrb():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':[],'物理格':['C1'],
              '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case_why('⑭ 反例: WHY路线条目为空列表被拦', f_why_emptyrb, '路线条目须为非空列表')
    # 2) 空 物理格：[待触发] f'{i} 物理格须为非空列表且引用真实cell'
    def f_why_emptycell():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':[],
              '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case_why('⑭ 反例: WHY物理格为空列表被拦', f_why_emptycell, '物理格须为非空列表')
    # 3) WHY id 重复：[待触发] f'WHY id重复: {i}'
    def f_why_dup():
        w={'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
           '因果链':[{'顺序':1,'层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                     {'顺序':2,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
           '条件':['c'],'取舍':['t'],'替代方案':['a']}
        _run14(why=[w,w])
    case_why('⑭ 反例: WHY id重复被拦', f_why_dup, 'WHY id重复')
    # 4) 悬空祖父（祖先链）：PQ002 的父 PQ001 之父 RQ999 悬空 → 受控 fail/break，不得 KeyError
    def f_dangling_gp():
        rq=_rq_base(); rq['questions'][1]['parent_id']='RQ999'  # PQ001 -> RQ999(悬空)
        _run14(rq=rq)
    case_why('⑭ 反例: WHY祖先链悬空祖父被拦(非KeyError)', f_dangling_gp, '祖先')
    # 5) 字符串顺序：步骤 顺序='1' 非 int → 不更新 last_ord/seen_ord，不得 TypeError
    def f_why_strord():
        why=[{'id':'WHY001','研究问题':'WQ001','路线条目':['RB001'],'物理格':['C1'],
              '因果链':[{'顺序':'1','层级':'SystemNeed','主张类型':'行业共识','陈述':'s','证据引用':['KN001']},
                        {'顺序':2,'层级':'Capability','主张类型':'事实','陈述':'s2','证据引用':['RB001']}],
              '条件':['c'],'取舍':['t'],'替代方案':['a']}]
        _run14(why=why)
    case_why('⑭ 反例: WHY步骤顺序为字符串被拦(非TypeError)', f_why_strord, '步骤顺序非法')
    # ---- Step1 硬门(2026-11-21): ⑪算术/单位/口径 · ①⑦同步完整性 · ②④edges截断 · ⑧⑨⑩URL锚点卫士 ----
    SE056={'row_id':'SE056','证据等级':'B','情景标记':'base','单位':'千只','出货量':'3726893.686',
           '推导式':'FY2024年报产销量表本期列直接披露','收入输入':'2,464,381,267.00元(意华股份2024年报同节分产品表)',
           'ASP输入':'隐含混合ASP≈661.2元/只(2024量价同表口径)','产能天顶检':'产销率98.55%复算(销/产),通过'}
    def ship(**kw): d=dict(SE056); d.update(kw); return d
    case('⑪ 反例: SE056 隐含ASP千倍错(661.2 vs 0.6612)被拦', lambda: _check_shipment_row(ship()), True)
    case('⑪ 正例: SE056 修正为0.66元/只(两位有效数字)通过', lambda: _check_shipment_row(ship(ASP输入='隐含混合ASP≈0.66元/只')), False)
    case('⑪ 正例: 万只+收入万元+ASP元/只算术一致通过', lambda: _check_shipment_row(ship(单位='万只',出货量='2109',收入输入='3,745,651.87万元',ASP输入='隐含混合ASP≈1,776元/只')), False)
    case('⑪ 反例: ASP元/件 错配单位=台 被拦', lambda: _check_shipment_row(ship(单位='台',出货量='100',收入输入='-',ASP输入='ASP≈1000元/件')), True)
    case('⑪ 反例: ASP元/件 错配单位=万片 被拦', lambda: _check_shipment_row(ship(单位='万片',出货量='100',收入输入='-',ASP输入='ASP≈10元/件')), True)
    case('⑪ 反例: ASP元/件 错配单位=千克 被拦', lambda: _check_shipment_row(ship(单位='千克',出货量='100',收入输入='-',ASP输入='ASP≈10元/件')), True)
    case('⑪ 正例: ASP元/件 配单位=万件 通过', lambda: _check_shipment_row(ship(单位='万件',出货量='1301.99',收入输入='2,038,769,308.96元',ASP输入='隐含混合ASP≈156.6元/件')), False)
    case('⑪ 反例: ASP输入科学计数法 被拦', lambda: _check_shipment_row(ship(ASP输入='隐含ASP 1.414e+05 元',收入输入='-')), True)
    case('⑪ 反例: 收入输入科学计数法 被拦', lambda: _check_shipment_row(ship(收入输入='2.46e+09元',ASP输入='-')), True)
    case('⑪ 反例: 同比反算却标B 被拦', lambda: _check_shipment_row(ship(推导式='2025销量按同比反算2024',ASP输入='-')), True)
    case('⑪ 正例: 同比反算标C 通过', lambda: _check_shipment_row(ship(推导式='2025销量按同比反算2024',证据等级='C',ASP输入='-')), False)
    case('⑪ 反例: 利用率未写产量(销量÷产能冒充) 被拦', lambda: _check_shipment_row(ship(ASP输入='-',产能天顶检='销量2,109万只≤产能2,806万只(隐含利用率75.2%),通过')), True)
    case('⑪ 正例: 利用率=产量÷产能 通过', lambda: _check_shipment_row(ship(ASP输入='-',产能天顶检='产量2,700万只/产能2,806万只(利用率96.2%),通过')), False)
    case('⑪ 正例: 销量/产能比(不称利用率) 通过', lambda: _check_shipment_row(ship(ASP输入='-',产能天顶检='销量/产能比75.2%,通过')), False)
    case('① 反例: universe.count 与 _frozen 不同步 被拦', lambda: _check_tree_universe({'universe':{'count':461}}, 463), True)
    case('① 正例: universe.count 同步 通过', lambda: _check_tree_universe({'universe':{'count':463}}, 463), False)
    case('⑦ 反例: triage重复hit_id 被拦', lambda: _check_triage_ids([{'hit_id':'甲+D8+2025年报'},{'hit_id':'甲+D8+2025年报'}]), True)
    case('⑦ 正例: triage hit_id唯一 通过', lambda: _check_triage_ids([{'hit_id':'甲+D8'},{'hit_id':'甲+D9'}]), False)
    case('⑦ 反例: watchlist cell_id非叶格(EQ7边) 被拦', lambda: _check_watchlist([{'公司':'甲','cell_id':'EQ7边'}], {'EQ7'}), True)
    case('⑦ 正例: watchlist 空/ANY/D4/M4 通过', lambda: _check_watchlist([{'cell_id':''},{'cell_id':'ANY'},{'cell_id':'D4/M4'}], {'D4','M4'}), False)
    EG={'edge_id':'E900','占比或金额原文':'27.6%','验证状态':'会话端已验证-SEC原文命中','备注':''}
    def edge(**kw): d=dict(EG); d.update(kw); return d
    case('②④ 正例: 完整edge通过', lambda: _check_edge_integrity(edge()), False)
    case('④ 反例: 验证状态左括号多余(半截截断) 被拦', lambda: _check_edge_integrity(edge(验证状态='P3判例#004-B级终态(R2审查:U门闭合/L门客户级归类不')), True)
    case('④ 反例: 占比原文以；截断 被拦', lambda: _check_edge_integrity(edge(占比或金额原文='11.86%；8.65%；')), True)
    case('② 反例: 引用悬空底稿 deanonymization-cases.md 被拦', lambda: _check_edge_integrity(edge(备注='见 deanonymization-cases.md #3')), True)
    case('⑨ 反例: macro 雪球basic-auth畸形URL 被拦', lambda: _check_macro_row({'claim_id':'MC900','证据等级':'C','证据类型':'二手汇总','链接':'https://ssgsmarketing@xueqiu.com/783/1'}), True)
    case('⑨ 反例: macro 百度搜索占位URL 被拦', lambda: _check_macro_row({'claim_id':'MC901','证据等级':'C','证据类型':'二手汇总','链接':'https://www.baidu.com/s?wd=x'}), True)
    case('⑨ 反例: macro B级无链接 被拦', lambda: _check_macro_row({'claim_id':'MC902','证据等级':'B','证据类型':'机构报告/厂商规格','链接':'','来源描述':'某报告'}), True)
    case('⑨ 正例: macro B级内部证据账本可重算免链接 通过', lambda: _check_macro_row({'claim_id':'MC903','证据等级':'B','证据类型':'内部证据账本可重算','链接':''}), False)
    case('⑨ 正例: macro B级含合法链接 通过', lambda: _check_macro_row({'claim_id':'MC904','证据等级':'B','证据类型':'机构报告/厂商规格','链接':'https://lightcounting.com/x'}), False)
    case('⑩ 反例: points 锚点 corpus/ir 路径不存在 被拦', lambda: _check_point_row({'point_id':'P900','锚点URL':'corpus/ir/000000/不存在.docx'}, exists=lambda rel: False), True)
    case('⑩ 正例: points 锚点 corpus/qa 路径存在(忽略#indexId) 通过', lambda: _check_point_row({'point_id':'P901','锚点URL':'corpus/qa/301165/qa.jsonl#indexId=1'}, exists=lambda rel: rel=='corpus/qa/301165/qa.jsonl'), False)
    PDF='https://static.cninfo.com.cn/finalpage/2026-03-13/1225006760.PDF'
    def pt(pid,co,url=PDF,q='',g='判定闸-生产中',tag='A股'): return {'point_id':pid,'公司':co,'上市标签':tag,'锚点URL':url,'命中引语':q,'判定等级':g}
    case('⑧ 反例: 两家A股异司共用同一巨潮PDF 被拦', lambda: _check_point_table([pt('P083','深南电路'),pt('P084','徕木股份',url=PDF+'#page=12')]), True)
    case('⑧ 正例: 共用PDF但注明客户关系 通过', lambda: _check_point_table([pt('P083','深南电路'),pt('P084','徕木股份',q='公司客户包括深南电路')]), False)
    case('⑧ 正例: 同一公司全称/简称共用PDF 通过', lambda: _check_point_table([pt('P1','江苏南大光电材料股份有限公司'),pt('P2','南大光电')]), False)
    case('⑧ 反例: points 雪球basic-auth畸形URL 被拦', lambda: _check_point_row({'point_id':'P902','锚点URL':'https://ssgsmarketing@xueqiu.com/1'}, exists=lambda rel: True), True)
    # ---- Step2 硬门(2026-11-21): _CORPUS_PATH_RE扩展 · ⑨海关四维表 · ⑧内容台账 · ②关系时间线与负记忆 ----
    for sub_p in ('corpus/annual-2023/300308/a.pdf','corpus/customs/customs_monthly.csv','corpus/content_ledger/content_ledger.csv#TCG24-09','corpus/relationships/relationship_timeline.csv','corpus/salvaged/entity_nodes.csv','corpus/daily_review/review_queue.csv'):
        case(f'⑩ 正例: _CORPUS_PATH_RE 识别存在路径 {sub_p.split("/")[1]} 通过', lambda p=sub_p: _check_point_row({'point_id':'P910','锚点URL':p}, exists=lambda rel,exp=sub_p.split('#')[0]: rel==exp), False)
        case(f'⑩ 反例: _CORPUS_PATH_RE 拦截缺失路径 {sub_p.split("/")[1]} 被拦', lambda p=sub_p: _check_point_row({'point_id':'P911','锚点URL':p}, exists=lambda rel: False), True)
    def _customs_ok():
        return {
            'monthly':[{'月份':ym,'HS编码':'85177950','金额':'100000'} for ym in _CUSTOMS_RECON_MONTHS],
            'partners':[{'月份':ym,'贸易伙伴':'马来西亚','金额':'100000'} for ym in _CUSTOMS_RECON_MONTHS],
            'province':[{'月份':ym,'注册地':'江苏省','贸易伙伴':'马来西亚','金额USD':'100000'} for ym in _CUSTOMS_RECON_MONTHS],
            'trademode':[{'月份':ym,'贸易伙伴':'马来西亚','贸易方式':'进料加工贸易','金额USD':'100000'} for ym in _CUSTOMS_RECON_MONTHS],
        }
    case('⑨ 正例: 海关四维表18个月0.000%对账+无换行+主键唯一 通过', lambda: _check_customs_tables(_customs_ok()), False)
    def _customs_sub_tiny_diff():
        d=_customs_ok(); d['partners'][0]=dict(d['partners'][0],金额='100005')  # 0.005% < 0.01%
        _check_customs_tables(d)
    case('⑨ 正例: 海关四维表微小舍入差(0.005%<0.01%) 通过', _customs_sub_tiny_diff, False)
    def _customs_newline():
        d=_customs_ok(); d['partners'][0]=dict(d['partners'][0],贸易伙伴='哥斯达黎\n加')
        _check_customs_tables(d)
    case('⑨ 反例: 海关表字段含内嵌换行符\\n 被拦', _customs_newline, True)
    def _customs_raw_newline():
        d={'monthly':[{'月份':ym,'HS编码':'85177950','金额':'100000'} for ym in _CUSTOMS_RECON_MONTHS],
           'partners':[{'月份':'202501','贸易伙伴':'美国','金额':'100000'}]+[{'月份':ym,'贸易伙伴':'美国','金额':'100000'} for ym in _CUSTOMS_RECON_MONTHS[1:]],
           'province':_customs_ok()['province'],'trademode':_customs_ok()['trademode']}
        raw_p='月份,贸易伙伴,金额\n202501,"美\n国",100000\n'+'\n'.join(f'{ym},美国,100000' for ym in _CUSTOMS_RECON_MONTHS[1:])+'\n'
        _check_customs_tables(d, raw_texts={'partners':raw_p})
    case('⑨ 反例: 海关表CSV原始文本物理行多于逻辑行(引号内换行) 被拦', _customs_raw_newline, True)
    def _customs_dup_pk():
        d=_customs_ok(); d['province'].append({'月份':'202501','注册地':'江苏省','贸易伙伴':'马来西亚','金额USD':'0'})
        _check_customs_tables(d)
    case('⑨ 反例: 海关表重复主键 被拦', _customs_dup_pk, True)
    def _customs_recon_drift():
        d=_customs_ok(); d['trademode'][0]=dict(d['trademode'][0],金额USD='100020')  # 0.02% >= 0.01%
        _check_customs_tables(d)
    case('⑨ 反例: 海关表月度美元汇总偏差>=0.01%(0.02%) 被拦', _customs_recon_drift, True)
    CL_BASE={'cid':'CL01','fact_type':'工序步骤','stance':'neutral','cell_ids':'D8,C1','verbatim_quote':'公司已建立IDM全流程业务体系。','local_source_path':'corpus/legacy-input/a.txt'}
    def cl_row(**kw): d=dict(CL_BASE); d.update(kw); return d
    case('⑧ 正例: content_ledger 合法条目(含多叶格与通用) 通过', lambda: _check_content_ledger([cl_row(),cl_row(cid='CL02',fact_type='技术参数',stance='issuer_self',cell_ids='通用')], {'D8','C1'}, exists=lambda rel: True), False)
    case('⑧ 反例: content_ledger cid重复 被拦', lambda: _check_content_ledger([cl_row(),cl_row()], {'D8','C1'}, exists=lambda rel: True), True)
    case('⑧ 反例: content_ledger fact_type非法 被拦', lambda: _check_content_ledger([cl_row(fact_type='客户订单')], {'D8','C1'}, exists=lambda rel: True), True)
    case('⑧ 反例: content_ledger stance非法 被拦', lambda: _check_content_ledger([cl_row(stance='positive')], {'D8','C1'}, exists=lambda rel: True), True)
    case('⑧ 反例: content_ledger cell_ids含非法格 被拦', lambda: _check_content_ledger([cl_row(cell_ids='D8,BAD9')], {'D8','C1'}, exists=lambda rel: True), True)
    case('⑧ 反例: content_ledger verbatim_quote为空 被拦', lambda: _check_content_ledger([cl_row(verbatim_quote='  ')], {'D8','C1'}, exists=lambda rel: True), True)
    case('⑧ 反例: content_ledger corpus/本地源路径不存在 被拦', lambda: _check_content_ledger([cl_row(local_source_path='corpus/legacy-input/missing.txt')], {'D8','C1'}, exists=lambda rel: False), True)
    RT_BASE={'timeline_id':'TL0001','supplier':'天孚通信','customer':'Fabrinet','source_channel':'annual_report','value_raw':'63.31%(326884.36万元)','source_edge_ids':'E043;E072#note','notes':'正常备注(已复核)'}
    def rt_row(**kw): d=dict(RT_BASE); d.update(kw); return d
    CUT_OK=[{'cut_id':'CUT001','company':'博创科技','counterparty':'长飞光纤光缆有限公司','counterparty_normalized':'长飞光纤光缆有限公司','implied_supplier':'长飞光纤光缆有限公司','implied_customer':'博创科技','leaked_in_edges_csv':'false'}]
    ACT_EDGES=[{'供方':'天孚通信','需方':'Fabrinet'}]
    case('② 正例: relationship_timeline+edge_negative_cuts 合法通过', lambda: _check_relationship_tables([rt_row(),rt_row(timeline_id='TL0002',source_edge_ids='',source_channel='daily_qa')], {'E043','E072'}, cut_rows=CUT_OK, active_edges=ACT_EDGES), False)
    case('② 反例: relationship_timeline timeline_id重复 被拦', lambda: _check_relationship_tables([rt_row(),rt_row()], {'E043','E072'}, active_edges=ACT_EDGES), True)
    case('② 反例: relationship_timeline source_edge_ids引用悬空E999 被拦', lambda: _check_relationship_tables([rt_row(source_edge_ids='E043;E999')], {'E043','E072'}, active_edges=ACT_EDGES), True)
    case('② 反例: relationship_timeline source_channel非法 被拦', lambda: _check_relationship_tables([rt_row(source_channel='wechat_rumor')], {'E043','E072'}, active_edges=ACT_EDGES), True)
    case('② 反例: relationship_timeline 括号不平衡半截截断 被拦', lambda: _check_relationship_tables([rt_row(value_raw='63.31%(326884.36万元')], {'E043','E072'}, active_edges=ACT_EDGES), True)
    case('② 反例: edge_negative_cuts 负向关系泄漏至活跃edges.csv 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072'}, cut_rows=[{'cut_id':'CUT999','company':'天孚通信','counterparty':'Fabrinet','implied_supplier':'天孚通信','implied_customer':'Fabrinet','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES), True)
    # ---- Step3 硬门(2026-11-21): ⑦ Daily 95/5 持久待审池 review_queue.csv ----
    DQ_ING={'queue_id':'DRQ0001','priority':'P0','trigger_type':'T4_universe_blindspot','status':'ingested_to_kb','entity_name':'科瑞技术','kb_target_ref':'points:P275;edges:E012;content:CLG0632;timeline:TL9001;calls:CM002','missing_verification_gate':''}
    DQ_PND={'queue_id':'DRQ0002','priority':'P0','trigger_type':'T2_supply_relationship_or_ma','status':'pending_primary_text','entity_name':'Marvell x Lumentum','kb_target_ref':'','missing_verification_gate':'需下载SEC 8-K与新闻稿正文'}
    DQ_ANC={'queue_id':'DRQ0003','priority':'P1','trigger_type':'T1_lifecycle_shift','status':'pending_filing_anchor','entity_name':'云南锗业','kb_target_ref':'points:P275','missing_verification_gate':'缺深交所正式公告PDF'}
    DQ_DEF={'queue_id':'DRQ0004','priority':'P2','trigger_type':'T3_commitment_verification','status':'watch_deferred','entity_name':'观察项','kb_target_ref':'','missing_verification_gate':''}
    def run_dq(rs, raw_t=None):
        _check_daily_review_queue(rs, {'P275'}, {'E012'}, {'CLG0632'}, {'TL9001'}, call_ids={'CM002'}, raw_text=raw_t, kn_ids={'KN011'})
    case('⑦ 正例: daily_review_queue 四状态+五主表闭环引用 通过', lambda: run_dq([DQ_ING,DQ_PND,DQ_ANC,DQ_DEF]), False)
    case('⑦ 正例: daily_review_queue knowledge:KN011 闭环引用 通过', lambda: run_dq([dict(DQ_ING, kb_target_ref='knowledge:KN011')]), False)
    case('⑦ 反例: daily_review_queue 空表 被拦', lambda: run_dq([]), True)
    case('⑦ 反例: daily_review_queue 字段含内嵌换行符 被拦', lambda: run_dq([dict(DQ_PND, missing_verification_gate='第一行\n第二行')]), True)
    case('⑦ 反例: daily_review_queue 原始CSV引号内换行(物理行多于逻辑行) 被拦', lambda: run_dq([DQ_PND], raw_t='queue_id,missing_verification_gate\nDRQ0002,"a\nb"\n'), True)
    case('⑦ 反例: daily_review_queue queue_id格式非法 被拦', lambda: run_dq([dict(DQ_ING, queue_id='DRQ01')]), True)
    case('⑦ 反例: daily_review_queue queue_id重复 被拦', lambda: run_dq([DQ_ING, dict(DQ_PND, queue_id='DRQ0001')]), True)
    case('⑦ 反例: daily_review_queue priority非法 被拦', lambda: run_dq([dict(DQ_ING, priority='P3')]), True)
    case('⑦ 反例: daily_review_queue trigger_type非法 被拦', lambda: run_dq([dict(DQ_ING, trigger_type='T9_unknown')]), True)
    case('⑦ 反例: daily_review_queue status非法 被拦', lambda: run_dq([dict(DQ_ING, status='done')]), True)
    case('⑦ 反例: daily_review_queue pending_*缺missing_verification_gate 被拦', lambda: run_dq([dict(DQ_PND, missing_verification_gate='  ')]), True)
    case('⑦ 反例: daily_review_queue ingested_to_kb缺kb_target_ref 被拦', lambda: run_dq([dict(DQ_ING, kb_target_ref='')]), True)
    for bad_ref in ('points:P999','edges:E999','content:CLG9999','timeline:TL9999','calls:CM999','knowledge:KN999','unknown:X1','P275'):
        case(f'⑦ 反例: daily_review_queue 悬空或非法kb_target_ref ({bad_ref}) 被拦', lambda r=bad_ref: run_dq([dict(DQ_ING, kb_target_ref=r)]), True)
    # ---- Step4 硬门(2026-11-22): ⑧ content_ledger verified_local 全文连续+#Lx..y(\\n计行) · ② edge_negative_cuts 按cut_category分类与简称归一 ----
    MOCK_DOC='第1行前言\n第2行前半\f跨页符同物理\\n行光耦合设备精度达50nm\n第3行获得海外头部客户验证和认可。\n第4行芯片共晶贴片设备稳定量产。'
    def run_cl4(rs):
        _check_content_ledger(rs, {'EQ3','EQ4'}, exists=lambda rel: rel=='corpus/annual/mock.txt', read_text=lambda rel: MOCK_DOC)
    case('⑧ 正例: content_ledger verified_local 全文连续+#L2..3(\\n计行含\\f不拆行)闭环 通过', lambda: run_cl4([cl_row(cid='CLG901',cell_ids='EQ4',verbatim_quote='光耦合设备精度达 50nm\n第3行获得海外头部客户验证和认可。',local_source_path='corpus/annual/mock.txt#L2..3',quote_verification_status='verified_local')]), False)
    case('⑧ 正例: content_ledger table_normalized/segmented_verified/inherited_v1_verified 诚实分级通过', lambda: run_cl4([
        cl_row(cid='CLG902',cell_ids='EQ3',verbatim_quote='第1行前言 / 芯片共晶贴片设备',local_source_path='corpus/annual/mock.txt',quote_verification_status='table_normalized'),
        cl_row(cid='CLG903',cell_ids='EQ3',verbatim_quote='第1行前言……芯片共晶贴片设备',local_source_path='corpus/annual/mock.txt',quote_verification_status='segmented_verified'),
        cl_row(cid='CLG904',cell_ids='EQ3',verbatim_quote='跨页嵌入表头历史行',local_source_path='corpus/annual/mock.txt',quote_verification_status='inherited_v1_verified'),
    ]), False)
    case('⑧ 反例: content_ledger quote_verification_status非法枚举 被拦', lambda: run_cl4([cl_row(cid='CLG905',cell_ids='EQ3',verbatim_quote='芯片共晶贴片设备',local_source_path='corpus/annual/mock.txt',quote_verification_status='auto_ok')]), True)
    case('⑧ 反例: content_ledger 伪table_normalized(斜杠拼接)冒充verified_local 被拦', lambda: run_cl4([cl_row(cid='CLG906',cell_ids='EQ3',verbatim_quote='第1行前言 / 芯片共晶贴片设备',local_source_path='corpus/annual/mock.txt',quote_verification_status='verified_local')]), True)
    case('⑧ 反例: content_ledger verified_local #L4..4区间错位(引语实为L2..3) 被拦', lambda: run_cl4([cl_row(cid='CLG907',cell_ids='EQ4',verbatim_quote='光耦合设备精度达50nm',local_source_path='corpus/annual/mock.txt#L4..4',quote_verification_status='verified_local')]), True)
    case('⑧ 反例: content_ledger verified_local 因\\f分页符按splitlines错算为#L3..4 被拦', lambda: run_cl4([cl_row(cid='CLG908',cell_ids='EQ4',verbatim_quote='光耦合设备精度达50nm',local_source_path='corpus/annual/mock.txt#L3..4',quote_verification_status='verified_local')]), True)
    case('⑧ 反例: content_ledger verified_local #L1..99行号越界 被拦', lambda: run_cl4([cl_row(cid='CLG909',cell_ids='EQ4',verbatim_quote='光耦合设备精度达50nm',local_source_path='corpus/annual/mock.txt#L1..99',quote_verification_status='verified_local')]), True)
    ACT_EDGES_S4=[{'供方':'源杰科技','需方':'中际旭创'},{'供方':'长飞光纤光缆','需方':'博创科技'},{'供方':'华工科技','需方':'某真客户'}]
    case('② 正例: edge_negative_cuts consolidated_into_group_edge 挂有效replacement_edge_ids(免撞合并边) 通过', lambda: _check_relationship_tables([rt_row()], {'E043','E072','E163'}, cut_rows=[{'cut_id':'CUT801','company':'博创科技','counterparty':'长飞光纤光缆有限公司','counterparty_normalized':'长飞光纤光缆有限公司','implied_supplier':'长飞光纤光缆有限公司','implied_customer':'博创科技','cut_category':'consolidated_into_group_edge','replacement_edge_ids':'E163','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), False)
    case('② 反例: edge_negative_cuts consolidated_into_group_edge 缺replacement_edge_ids 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072','E163'}, cut_rows=[{'cut_id':'CUT802','company':'博创科技','counterparty':'长飞光纤光缆有限公司','cut_category':'consolidated_into_group_edge','replacement_edge_ids':'','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), True)
    case('② 反例: edge_negative_cuts consolidated_into_group_edge replacement_edge_ids悬空E999 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072','E163'}, cut_rows=[{'cut_id':'CUT803','company':'博创科技','counterparty':'长飞光纤光缆有限公司','cut_category':'consolidated_into_group_edge','replacement_edge_ids':'E999','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), True)
    case('② 正例: edge_negative_cuts non_supply_relation(股东/担保)豁免供货边碰撞 通过', lambda: _check_relationship_tables([rt_row()], {'E043','E072'}, cut_rows=[{'cut_id':'CUT804','company':'源杰科技','counterparty':'中际旭创股份有限公司','counterparty_normalized':'中际旭创股份有限公司','cut_category':'non_supply_relation','replacement_edge_ids':'','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), False)
    case('② 反例: edge_negative_cuts non_supply_relation leaked_in_edges_csv=true 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072'}, cut_rows=[{'cut_id':'CUT805','company':'源杰科技','counterparty':'中际旭创股份有限公司','cut_category':'non_supply_relation','replacement_edge_ids':'','leaked_in_edges_csv':'true'}], active_edges=ACT_EDGES_S4), True)
    case('② 反例: edge_negative_cuts cut_category非法枚举 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072'}, cut_rows=[{'cut_id':'CUT806','company':'甲','counterparty':'乙','cut_category':'unknown_cat','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), True)
    case('② 反例: edge_negative_cuts 真否定经_norm_co_name剥离股份有限公司/括号后与活跃边碰撞 被拦', lambda: _check_relationship_tables([rt_row()], {'E043','E072'}, cut_rows=[{'cut_id':'CUT807','company':'华工科技（本部）','counterparty':'某真客户股份有限公司','counterparty_normalized':'某真客户股份有限公司','implied_supplier':'华工科技（本部）','implied_customer':'某真客户股份有限公司','cut_category':'non_optical_related_or_bad_debt','replacement_edge_ids':'','leaked_in_edges_csv':'false'}], active_edges=ACT_EDGES_S4), True)
    print(f'\n[selftest] 合计 {total} 用例, 通过 {total-fails}, 失败 {fails}')
    return 1 if fails else 0

if __name__=='__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    staleness()
    invariants()
    if ERR:
        print('\n'.join('\033[31m'+e+'\033[0m' for e in ERR)); sys.exit(1)
    print('不变量全绿(①-⑭)')
    if '--check' not in sys.argv: scan()
