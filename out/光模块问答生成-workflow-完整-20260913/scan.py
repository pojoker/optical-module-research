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
    # ②端点闭合
    pid={p['point_id'] for p in pts}|{'ANON','EXT'}
    for e in egs:
        for col in ('供方point_id','需方point_id'):
            if e.get(col,'') and e[col] not in pid: fail('②',f"{e.get('edge_id')} {col}={e[col]} 悬空")
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
        'research_questions.yaml','questions_manual.csv',
        'RESTART-v2.md','CONTEXT.md','.gitignore','.gitattributes','.git','.DS_Store'}
    for f in os.listdir(ROOT):
        if os.path.isfile(os.path.join(ROOT,f)) and f not in WL: fail('⑥',f'根目录白名单外文件: {f}')
    refs=os.listdir(os.path.join(ROOT,'refs')) if os.path.isdir(os.path.join(ROOT,'refs')) else []
    if len(refs)>8: fail('⑥',f'refs/文件数{len(refs)}>8(2026-08-04由6放宽,纪律4)')
    for m in glob.glob(os.path.join(ROOT,'**/*.md'),recursive=True):
        rel=os.path.relpath(m,ROOT)
        if not rel.startswith(('archive/','refs/','out/','corpus/','calls/','docs/')) and rel not in ('README.md','CLAUDE.md','AGENTS.md','RESTART-v2.md','CONTEXT.md'):
            fail('⑥',f'越位md: {rel}')
    # ⑦triage一致性
    pnames={p['公司'] for p in pts}
    for t in trg:
        if t['处置']=='已入点' and t['公司'] not in pnames: fail('⑦',f"triage {t['hit_id']} 已入点但points无此公司")
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
