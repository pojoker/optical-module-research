#!/usr/bin/env python3
"""render.py — tree.yaml+csv→out/全景.md+.html 幂等确定性渲染。

--verify 在两个临时目录独立重建并比较，验证生成确定性；out/ 不是 canonical。
"""
import os,csv,sys,re,yaml,filecmp,tempfile,shutil
from collections import namedtuple, Counter
from datetime import date
ROOT=os.path.dirname(os.path.abspath(__file__))
def rows(f):
    p=os.path.join(ROOT,f)
    return list(csv.DictReader(open(p,encoding='utf-8-sig'))) if os.path.exists(p) else []

# ---- 问题队列派生（v1，详见 docs/plans/2026-08-question-queue.md / codebuddy-handoff）----
# QE 白名单：逐字精确匹配的已核取值；新取值默认未验证（fail-safe）。冻结于此，改须记维护。
VERIFIED_EDGE_STATUSES = {
    'P2原文复核-修正转录值36.3%→36.79%',
    'P2原文已验证-全称"浙江省粮油食品进出口股份有限公司"逐字命中',
    'P3判例#003-A级',
    'P3判例#004-B级终态(R2审查:U门闭合$1272M上界/L门客户级归类不',
    'v1.3管线抽取+人工原文复核通过',
    'v1.6r终验(10-K原文)',
    'v1.6r终验(单位感知重装)',
    'v1.6r终验(原文核验)',
    '会话端已验证',
    '会话端已验证+抽检交叉',
    '会话端已验证-SEC原文命中',
    '会话端抽检命中',
    '会话端抽检逐字命中',
    '本轮P1-SEC原文命中',
    '本轮P2原文命中',
    '本轮P3-SEC原文命中',
    '正式版管线产出-人工原文复核通过',
}
QN_KIND_ORDER={'QD':0,'QA':1,'QB':2,'QC':3,'QE':4}
def _q_unlock(period):
    """期间解锁日；无法解析返回 None（fail-open：仍生成问题，排序沉底）。"""
    period=(period or '').strip()
    m=re.fullmatch(r'(\d{4})年度', period)
    if m: return date(int(m.group(1))+1,5,1)
    m=re.fullmatch(r'(\d{4})H1.*', period)
    if m: return date(int(m.group(1)),9,1)
    return None

def _filled(v):
    return (v or '').strip()!=''

# 派生问题封装：稳定携带显式 question_id（前缀-来源ID），供人工裁决对齐
Q = namedtuple('Q', ['kind','q','acc','wb','src','seq','qid'])
def _mkq(kind,q,acc,wb,src,seq):
    return Q(kind,q,acc,wb,src,seq,f"{kind}-{src.split(':',1)[1]}")

def _parse_date(v):
    """严格 YYYY-MM-DD；否则 None。"""
    v=(v or '').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        try: return date.fromisoformat(v)
        except ValueError: return None
    return None

def _parse_qid(qid):
    """只按第一个连字符切分前缀与来源ID（QD 的 hit_id 可含连字符）。"""
    qid=(qid or '').strip()
    if '-' not in qid: return None,None
    i=qid.index('-')
    return qid[:i], qid[i+1:]

def _src_exists(prefix, src, cell_ids, ship_ids, edge_ids):
    """来源ID是否仍真实存在于对应 canonical 文件。"""
    if prefix in ('QA','QB'): return src in cell_ids
    if prefix=='QC': return src in ship_ids
    if prefix=='QE': return src in edge_ids
    return False

# 真零双通道：严格整串匹配两通道，各四键(关键词/语料范围/检索日期/命中数)
_CHAN_RE=re.compile(
    r'通道A\{(关键词)=([^;}]*);(语料范围)=([^;}]*);(检索日期)=([^;}]*);(命中数)=([^;}]*)\}'
    r'\|通道B\{(关键词)=([^;}]*);(语料范围)=([^;}]*);(检索日期)=([^;}]*);(命中数)=([^;}]*)\}')

def _validate_adjudication(row, today, cell_ids, ship_ids, edge_ids):
    """校验人工裁决行；返回 (valid, status, prefix, qid, src, note)。
    status∈{豁免,真零}；仅完全有效才 valid=True。"""
    qid=(row.get('question_id') or '').strip()
    disp=(row.get('处置') or '').strip()
    reason=(row.get('理由') or '').strip()
    acc=(row.get('验收锚型') or '').strip()
    dual=(row.get('双通道记录') or '').strip()
    recheck=(row.get('复核日期') or '').strip()
    sess=(row.get('会话日期') or '').strip()
    prefix,src=_parse_qid(qid)
    if prefix not in ('QA','QB','QC','QE'): return (False,None,None,qid,src,'前缀非法(QD不可人工裁决)')
    if disp not in ('豁免','真零'): return (False,None,prefix,qid,src,'处置非法')
    if not (reason and acc and recheck and sess): return (False,None,prefix,qid,src,'必填缺')
    rd=_parse_date(recheck); sd=_parse_date(sess)
    if rd is None or sd is None: return (False,None,prefix,qid,src,'日期格式非法(须YYYY-MM-DD)')
    if not (sd <= today < rd): return (False,None,prefix,qid,src,'日期区间非法(会话日期<=今天<复核日期)')
    if disp=='豁免':
        if dual!='': return (False,None,prefix,qid,src,'豁免双通道必须空')
        return (True,'豁免',prefix,qid,src,'')
    m=_CHAN_RE.fullmatch(dual)
    if not m: return (False,None,prefix,qid,src,'真零双通道格式非法')
    a_kw,a_scope,a_date,a_hits,b_kw,b_scope,b_date,b_hits=(
        m.group(2),m.group(4),m.group(6),m.group(8),
        m.group(10),m.group(12),m.group(14),m.group(16))
    if any(v.strip()=='' for v in (a_kw,a_scope,a_date,a_hits,b_kw,b_scope,b_date,b_hits)):
        return (False,None,prefix,qid,src,'真零四键值须非空')
    ad=_parse_date(a_date); bd=_parse_date(b_date)
    if ad is None or bd is None: return (False,None,prefix,qid,src,'真零检索日期格式非法')
    if ad>sd or bd>sd: return (False,None,prefix,qid,src,'检索日期>会话日期')
    if a_scope.strip()==b_scope.strip(): return (False,None,prefix,qid,src,'AB语料范围须不同')
    return (True,'真零',prefix,qid,src,'')

def _write_queue(meta, bycell, kbycell, ships, tri, egs, outdir):
    """从 tree/points/knowledge/shipments/triage/edges 确定性派生 QA–QE，生成 out/问题队列.md。"""
    today=date.today()
    cell_order=list(meta.keys())
    dfs={c:i for i,c in enumerate(cell_order)}
    qs=[]
    # QD：triage.csv 处置==“待判”（原始行序）
    for i,r in enumerate(tri):
        if (r.get('处置') or '').strip()=='待判':
            qs.append(_mkq('QD', f"{r['公司']}+{r['cell_id']}判不判？",
                       'triage.csv 处置变为非“待判”的合法枚举值',
                       'triage.csv', f"triage.csv:{r['hit_id']}", i))
    # QA：空叶格（非“共用”路线优先，再按 DFS 叶格顺序）
    qa=[c for c in cell_order if not bycell.get(c)]
    qa.sort(key=lambda c:(1 if meta[c][1]=='共用' else 0, dfs[c]))
    for c in qa:
        qs.append(_mkq('QA', f"{meta[c][0]}谁在做？",
                   '自家披露件或互动易/e互动回答引语 + 合法锚点',
                   'points.csv', f"tree.yaml:{c}",
                   (1 if meta[c][1]=='共用' else 0, dfs[c])))
    # QB：有点但无知识覆盖（按 DFS 叶格顺序）
    qb=[c for c in cell_order if bycell.get(c) and c not in kbycell]
    qb.sort(key=lambda c:dfs[c])
    for c in qb:
        qs.append(_mkq('QB', f"{meta[c][0]}是干嘛的、为什么难、怎么判断谁够格？",
                   '该格进入至少一条带合法类型化锚(KN)的 knowledge.yaml 条目',
                   'knowledge.yaml', f"tree.yaml:{c}", dfs[c]))
    # QC：C 级 + base，校准三字段未齐，且已到解锁日（不可解析期间 fail-open，排后）
    qc=[]
    for i,r in enumerate(ships):
        if (r.get('证据等级') or '').strip()!='C': continue
        if (r.get('情景标记') or '').strip()!='base': continue
        # 三字段完整(销号)须: 校准实际值非空 且 误差非空 且 校准日期非空且为合法YYYY-MM-DD；
        # 校准日期非空但非法 → 不算完整 → 仍须生成QC(销号口径收紧为合法日期)
        if _filled(r.get('校准实际值')) and _filled(r.get('误差')) and _parse_date(r.get('校准日期')) is not None: continue
        u=_q_unlock(r.get('期间'))
        if u is not None and today<u: continue
        qc.append((r,i,u))
    # seq 必须携带完整解锁序键(可解析优先, 解锁日, 原行序), 否则最终 qs.sort 会用纯行序覆盖解锁序
    qc.sort(key=lambda x:(1 if x[2] is None else 0, x[2] or date.max, x[1]))
    for r,i,u in qc:
        qs.append(_mkq('QC', f"{r['公司']}{r['期间']}推断值该回算了吗？",
                   '校准实际值/误差/校准日期三字段全非空(校准日期为YYYY-MM-DD)',
                   'shipments.csv', f"shipments.csv:{r['row_id']}",
                   (1 if u is None else 0, u or date.max, i)))
    # QE：验证状态未入17项白名单 或 锚点空（edges.csv 原始行序）
    # 验证状态用未 strip 原值逐字比对白名单（首尾空白变体即未验证）；锚点仍 strip 判非空
    for i,e in enumerate(egs):
        st=e.get('验证状态') or ''
        anc=(e.get('锚点') or '').strip()
        if st in VERIFIED_EDGE_STATUSES and anc: continue
        qs.append(_mkq('QE', f"{e['供方']}→{e['需方']}这条边核过原文吗？",
                   '验证状态进入17项白名单且锚点非空',
                   'edges.csv', f"edges.csv:{e['edge_id']}", i))
    # 全局类型顺序 QD→QA→QB→QC→QE，类型内保持源顺序
    qs.sort(key=lambda x:(QN_KIND_ORDER[x.kind], x.seq))
    # ---- 人工裁决合并：先派生排序，再读 questions_manual.csv ----
    # 仅 QA/QB/QC/QE 允许处置；完全有效且 question_id 仍在 raw 集合才 suppress 并计有效裁决；
    # 完全有效、来源ID仍存在但问题已不再派生 → 待清理；来源ID不存在留给 scan 报错，不算待清理。
    cell_ids=set(meta.keys()); ship_ids={r['row_id'] for r in ships}; edge_ids={e['edge_id'] for e in egs}
    raw_qids={q.qid for q in qs}
    # 人工裁决仅当表头逐字等于下列七列时才参与 suppress；空文件/错误表头/未知列一律不 suppress
    REQUIRED_MAN_HEADER=['question_id','处置','理由','验收锚型','双通道记录','复核日期','会话日期']
    man=[]; man_header_ok=False
    mp=os.path.join(ROOT,'questions_manual.csv')
    if os.path.exists(mp):
        with open(mp,encoding='utf-8-sig') as _f:
            _rd=csv.DictReader(_f)
            if list(_rd.fieldnames or [])==REQUIRED_MAN_HEADER:
                man=list(_rd); man_header_ok=True
    suppressed=set(); exempt=0; zero=0; cleanup=[]
    if man_header_ok:
        # 任何重复 question_id 使其全部重复行无效: 不 suppress、不计有效裁决、不计待清理
        _qcount=Counter((r.get('question_id') or '').strip() for r in man)
        dup_qids={q for q,c in _qcount.items() if c>1}
        for r in man:
            qid=(r.get('question_id') or '').strip()
            if qid in dup_qids: continue
            valid,status,prefix,qid,src,note=_validate_adjudication(r,today,cell_ids,ship_ids,edge_ids)
            if not valid: continue
            if qid in raw_qids:
                suppressed.add(qid)
                if status=='豁免': exempt+=1
                else: zero+=1
            elif _src_exists(prefix,src,cell_ids,ship_ids,edge_ids):
                cleanup.append(qid)
    qs=[q for q in qs if q.qid not in suppressed]
    counts={'QA':0,'QB':0,'QC':0,'QD':0,'QE':0}
    for x in qs: counts[x.kind]+=1
    LQ=['# 问题队列','','> 本页由 render.py 从 canonical 账本派生，勿手改（--verify 会拒绝）。',
        '> v1 只展示当前 canonical 账本维护欠账；制造工序、装配接口、正交路线覆盖和投资推论尚未纳入，不等于完整研究问题空间。','']
    LQ+=['## 回填合同（五类问题 → canonical 回填目标）','',
         '| 类型 | 回填目标文件 | 验收锚型 |','|---|---|---|',
         '| QA | points.csv | 该格出现至少一个合法点(披露件/互动易引语+合法锚点) |',
         '| QB | knowledge.yaml（可选同步 tree.yaml.knowledge_ids） | 该格进入至少一条带合法类型化锚(KN)的 knowledge.yaml 条目 |',
         '| QC | shipments.csv | 校准实际值/误差/校准日期三字段全非空(校准日期为YYYY-MM-DD) |',
         '| QD | triage.csv | 处置变为非“待判”的合法枚举值 |',
         '| QE | edges.csv | 验证状态进入17项白名单且锚点非空 |','']
    LQ+=['### QB 研究交付合同（追加到 knowledge.yaml 顶层 knowledge: 列表的 KN 条目）','',
         'QB 销号只看 `knowledge.yaml` 实际 `格` 列表；`tree.yaml.knowledge_ids` 仅是反向展示索引（可选同步），不是销号第二口径。',
         '交付必须为 append-ready YAML（按最大现有 KN 顺延 ID），不能只交 prose：','',
         '```yaml','- id: KN###','  格: [目标cell_id]','  标题: ...','  一句话: ...','  说细点: ...','  怎么用它判断: ...','  证据:','  - 谁: ...','    原话: ...','    出处: ...','    锚型: url|local_file|ledger_ref|search_protocol|web_snapshot','    锚: ...','  录入日期: \'YYYY-MM-DD\'','```','',
         '五种合法锚型：`url`、`local_file`、`ledger_ref`、`search_protocol`、`web_snapshot`。','']
    LQ+=['## 问题队列','',
         '| 顺位 | question_id | 问题 | 验收锚型 | 回填目标 | 来源 |','|---:|---|---|---|---|---|']
    for n,q in enumerate(qs,1):
        LQ.append(f"| {n} | {q.qid} | {q.q} | {q.acc} | {q.wb} | {q.src} |")
    LQ.append('')
    LQ+=['---',
         f"页脚：问题队列={len(qs)}条(QA:{counts['QA']} QB:{counts['QB']} QC:{counts['QC']} QD:{counts['QD']} QE:{counts['QE']}) | 有效裁决:豁免{exempt} 真零{zero} | 待清理裁决{len(cleanup)}"]
    if cleanup:
        LQ.append('待清理裁决（完全有效、来源ID仍存在但问题已不再派生，建议人工删行）：'+', '.join(cleanup))
    qmd='\n'.join(LQ)+'\n'
    open(os.path.join(outdir,'问题队列.md'),'w',encoding='utf-8').write(qmd)

def write_research_tree(outdir):
    """生成 out/研究问题树.md（上游方案 §8）。从 research_questions.yaml 取导航，从 knowledge.yaml
    取覆盖与 Why 链，从 route_bom.csv×points.csv 推导路线能力群。所有数字实时重算，不写死。
    两套知识体系：物理知识 + 技术路线；Why 是两者间可验证因果关系，不挂第三主干。"""
    rp=os.path.join(ROOT,'research_questions.yaml')
    if not os.path.exists(rp): return
    rq=yaml.safe_load(open(rp,encoding='utf-8')) or {}
    questions=rq.get('questions',[]) or []
    wqs=rq.get('why_questions',[]) or []
    qmap={q['id']:q for q in questions if 'id' in q}
    children={}
    for q in questions:
        pid=q.get('parent_id')
        if pid and pid in qmap:
            children.setdefault(pid,[]).append(q['id'])
    for k in children:
        children[k].sort(key=lambda i:qmap[i].get('order',0))
    # knowledge + why
    kp=os.path.join(ROOT,'knowledge.yaml')
    kb=[]; why_links=[]
    if os.path.exists(kp):
        kd=yaml.safe_load(open(kp,encoding='utf-8')) or {}
        kb=kd.get('knowledge',[]) or []
        why_links=kd.get('why_links',[]) or []
    # 覆盖：question_id -> {KN ids}（仅 RQ/PQ/TQ）
    cov={}
    for k in kb:
        for r in (k.get('研究问题') or []):
            if r[:2] in ('RQ','PQ','TQ'):
                cov.setdefault(r,set()).add(k['id'])
    # WQ 覆盖：WQ id -> {WHY ids}
    why_cov={}
    for w in why_links:
        ref=w.get('研究问题')
        if ref and ref[:2]=='WQ':
            why_cov.setdefault(ref,set()).add(w['id'])
    # 实时基线分母
    tree_text=open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8').read()
    cells=set(re.findall(r'cell_id:\s*([A-Za-z0-9]+)',tree_text))
    pts=rows('points.csv'); rb=rows('route_bom.csv')
    routes=sorted(set(r['产品路线'] for r in rb))
    L=[]
    L+=['# 光模块研究问题图 v3（树形展示 + 多依赖）','','> 本页由 render.py 生成，勿手改（--verify 会拒绝）。',
        '> 这是主研究导航：从“什么是光模块？”逐层生长，明确区分两套知识：',
        '>  · 物理知识体系：系统功能 → 组件 → 接口 → 制造 → 设备。',
        '>  · 技术路线体系：需求/约束 → 瓶颈 → 正交轴 → 路线画像 → 能力 → 公司能力群。',
        '>  · 两套体系之间不是第三棵树，而是一组 Why 关联（需求/瓶颈 → 工程选择 → 物理变化 → 公司能力）。',
        '> 研究答案回填 knowledge.yaml（物理/路线 KN）；跨体系因果写入同一文件 why_links:。本页不保存事实答案。',
        '> **状态措辞**：`[已有材料: KN…]` 只表示至少有一条通过校验的 KN/WHY 引用该问题；',
        '> 它**不是**“已覆盖 / 已完成 / 已回答”。问题是否完成只由人工复核判定，本页不计算完成状态。','']
    # 实时基线
    L+=['## 实时基线（每次渲染从当前 YAML/CSV 重算，不写死）','',
        f'- 研究问题：{len(questions)} 个（RQ/PQ/TQ）+ Why 桥 {len(wqs)} 个（WQ）',
        f'- 知识条目 knowledge.yaml：{len(kb)} 条（问题的“已有材料”来自其 研究问题 引用）',
        f'- Why 关联 why_links：{len(why_links)} 条（首版允许为空）',
        f'- tree.yaml 物理格：{len(cells)} 个',
        f'- 产品路线框架 route_bom.csv：{len(routes)} 条（{", ".join(routes)}）',
        f'- 能力点 points.csv：{len(pts)} 个','']
    # 问题主干
    root_id=rq.get('meta',{}).get('root_id','RQ000')
    root=cov.get(root_id,set())
    root_status=f'[已有材料: {",".join(sorted(root))}]' if root else '[待研究]'
    L+=['## 问题主干（从 RQ000 逐层生长）','',
        f'**{root_id}** {qmap.get(root_id,{}).get("question","")} {root_status}','','**物理知识体系**']
    def _emit(qid,depth):
        q=qmap[qid]; kn=sorted(cov.get(qid,set()))
        status=f'[已有材料: {",".join(kn)}]' if kn else '[待研究]'
        deps=q.get('depends_on') or []
        dep_text=f"（理解依赖：{', '.join(deps)}）" if deps else ''
        L.append(f"{'  '*depth}- **{qid}** {q['question']} {status}{dep_text}")
        for c in children.get(qid,[]): _emit(c,depth+1)
    for c in children.get(root_id,[]):
        if qmap.get(c,{}).get('system')=='physical': _emit(c,1)
    L.append('')
    L.append('**技术路线体系**')
    for c in children.get(root_id,[]):
        if qmap.get(c,{}).get('system')=='route': _emit(c,1)
    L.append('')
    # Why 桥
    L+=['## Why 桥（跨主干关系，不是第三主干）','',
        '> WQ 只表示技术路线体系与物理知识体系之间的跨体系因果关系，不挂进第三主干。',
        '> 每张 WQ 显示其连接：路线侧（TQ）→ 物理侧（PQ），以及关系类型。',
        '> 已有材料的 WQ 展示通过校验的 WHY 因果链；首版若无 WHY，显示“尚无已验证 Why 关联”。',
        '> “已有材料”只表示至少有一条通过校验的 KN/WHY 引用该问题，**不等于问题已回答或已完成**；',
        '> 问题是否完成只由人工复核判定，本页不显示、也不计算任何完成状态。','']
    any_why=False
    for w in sorted(wqs,key=lambda x:x.get('order',0)):
        wid=w['id']; whyids=sorted(why_cov.get(wid,set()))
        status=f'[已有材料: {",".join(whyids)}]' if whyids else '[待研究]'
        L.append(f'### {wid} {w["question"]} {status}')
        L.append(f'- 路线侧（TQ）：{", ".join(w.get("route_question_ids",[]))}')
        L.append(f'- 物理侧（PQ）：{", ".join(w.get("physical_question_ids",[]))}')
        L.append(f'- 关系类型：{w.get("relation_type","—")}')
        if whyids:
            any_why=True
            for wy in whyids:
                wyobj=next((x for x in why_links if x.get('id')==wy),None)
                if not wyobj: continue
                L.append(f'- WHY 链（{wy}）：')
                for step in wyobj.get('因果链',[]):
                    L.append(f'    {step.get("顺序")}. [{step.get("层级")}/{step.get("主张类型")}] {step.get("陈述","")}（证据：{", ".join(step.get("证据引用",[]))}）')
                L.append(f'  - 条件：{"; ".join(wyobj.get("条件",[]))}')
                L.append(f'  - 取舍：{"; ".join(wyobj.get("取舍",[]))}')
                L.append(f'  - 替代方案：{"; ".join(wyobj.get("替代方案",[]))}')
        else:
            L.append('- 尚无已验证 Why 关联')
        L.append('')
    if not any_why:
        L.append('> 首版 Why 关联为空是允许状态；4 个待研究桥问题见上。')
        L.append('')
    # 路线能力群快照
    L+=['## 路线能力群快照（产品路线框架）','',
        '> 重要边界：route_bom.csv 当前是“产品路线框架”，不是完整正交组合路线画像；',
        '> 一条产品路线框架下可列出多个兼容选择轴取值，并非唯一具体路线。',
        '> **候选能力群 = 路线所需物理格 × points.csv 过闸能力点 推导的能力匹配，不是路线采用/供货证据。**',
        '> **确认服务群 = 技术路线 KN 显式关联该路线 RB 且关联真实 point 的公司群；首版可能为空。**',
        '> 任何候选/确认群都不自动构成供货关系；供货只读 edges.csv。','']
    # 每条路线的候选格集合（用于检测相同）
    route_cells={}
    for route in routes:
        cs=set()
        for r in rb:
            if r['产品路线']==route and r['mapping_status']=='mapped':
                cs|=set(x.strip() for x in r['cell_ids'].split(',') if x.strip())
        route_cells[route]=cs
    pm={p['point_id']:p for p in pts}
    for route in routes:
        cs=route_cells[route]
        rrow=next(r for r in rb if r['产品路线']==route)
        L.append(f'### {route}（{rrow.get("应用边界","")}）')
        # 路线级顶层提示：物理映射能否区分路线（与候选格集合相同的其它路线对比）
        same=[o for o in routes if o!=route and route_cells[o] and route_cells[o]==cs]
        if same:
            L.append(f'- ⚠ 当前物理映射无法区分路线：{route} 与 {", ".join(same)} 候选格集合相同（{sorted(cs)}）；差异须由 TQ010/TQ013 等路线画像研究给出。')
        L.append(f'- 选择轴：产品标准轴={rrow.get("产品标准轴","")}；电接口轴={rrow.get("电接口轴","")}；封装架构轴={rrow.get("封装架构轴","")}；光子平台轴={rrow.get("光子平台轴","")}')
        L.append('- BOM 分组与映射格：')
        for r in rb:
            if r['产品路线']!=route: continue
            if r['mapping_status']=='mapped':
                L.append(f'  - {r["BOM分组"]}（{r["route_item_id"]}）：{r["cell_ids"]}')
            else:
                L.append(f'  - {r["BOM分组"]}（{r["route_item_id"]}，{r["mapping_status"]}）：不映射格（{r.get("mapping_note","")}）')
        # 候选能力群
        L.append('- 候选能力群（能力匹配，不是路线采用/供货证据）：')
        cell_companies={}
        for c in sorted(cs):
            comps=sorted({p['公司'] for p in pts if p['cell_id']==c})
            cell_companies[c]=comps
            L.append(f'  - {c}：{", ".join(comps) if comps else "（空格）"}')
        overall=sorted({co for comps in cell_companies.values() for co in comps})
        L.append(f'  - 去重公司合计：{len(overall)} 家')
        # 确认服务群
        L.append('- 确认服务群（仅技术路线 KN 显式关联本路线 RB 且关联真实 point 才计入）：')
        rb_ids={r['route_item_id'] for r in rb if r['产品路线']==route}
        conf={}
        for k in kb:
            if k.get('体系')!='技术路线': continue
            if not (set(k.get('路线条目') or []) & rb_ids): continue
            for p_ in (k.get('关联点') or []):
                if p_ in pm:
                    conf.setdefault(pm[p_]['公司'],set()).add(k['id'])
        if not conf:
            L.append('  - 尚无路线级直接证据条目')
        else:
            for comp in sorted(conf):
                L.append(f'  - {comp}：支撑KN={",".join(sorted(conf[comp]))}')
        L.append('')
    # 回填模板
    L+=['## 回填模板（append-ready YAML，模板不是答案）','',
        '> 以下三段是追加到 knowledge.yaml 的模板，须替换为真实一手证据后才能进入 canonical；模板本身不是答案。','',
        '### 物理 KN 模板','',
        '```yaml','knowledge:','- id: KN###','  体系: 物理知识','  研究问题: [PQ###]','  格: [cell_id]','  标题: ...','  一句话: ...','  说细点: ...','  怎么用它判断: ...','  证据:','  - 谁: ...','    原话: ...','    出处: ...','    锚型: url|local_file|ledger_ref|search_protocol|web_snapshot','    锚: ...','  录入日期: \'YYYY-MM-DD\'','```','',
        '### 路线 KN 模板（进入确认服务群须显式填 关联点 指向真实 point）','',
        '```yaml','knowledge:','- id: KN###','  体系: 技术路线','  研究问题: [TQ###]','  路线条目: [RB###]','  标题: ...','  一句话: ...','  说细点: ...','  怎么用它判断: ...','  证据:','  - 谁: ...','    原话: ...','    出处: ...','    锚型: url|local_file|ledger_ref|search_protocol|web_snapshot','    锚: ...','  关联点: [P###]   # 仅当证据明确把公司与路线联系起来才填','  录入日期: \'YYYY-MM-DD\'','```','',
        '### Why 关联模板（写入 knowledge.yaml 顶层 why_links:）','',
        '```yaml','why_links:','- id: WHY###','  研究问题: WQ###','  路线条目: [RB###]','  物理格: [cell_id]','  因果链:','  - 顺序: 1','    层级: SystemNeed | Physics | Engineering | PhysicalDelta | Capability | CommercialAdoption | Economics | Investment','    主张类型: 事实 | 行业共识 | 工程推论 | 经济推论 | 投资假设','    陈述: ...','    证据引用: [KN### | RB###]','  条件: [...]','  取舍: [...]','  替代方案: [...]','```','']
    L+=['---','',
        '> 后台维护入口：`out/问题队列.md`（QA–QE 维护欠账，由 canonical 账本确定性派生，不承担基础研究问题层级导航）。',
        f'页脚：研究问题={len(questions)+len(wqs)}（问题{len(questions)} + Why桥{len(wqs)}） | KN={len(kb)} | Why={len(why_links)} | 物理格={len(cells)} | 路线框架={len(routes)} | 能力点={len(pts)}']
    md='\n'.join(L)+'\n'
    open(os.path.join(outdir,'研究问题树.md'),'w',encoding='utf-8').write(md)

def build(outdir):
    tr=yaml.safe_load(open(os.path.join(ROOT,'tree.yaml'),encoding='utf-8'))
    pts,egs=rows('points.csv'),rows('edges.csv')
    ships,tri=rows('shipments.csv'),rows('triage.csv')
    bycell={}
    for p in pts: bycell.setdefault(p['cell_id'],[]).append(p)
    # 知识库: 为什么层(须带证据引语+出处)。按格索引,渲进对应格 + 独立页
    kb=[]
    kp=os.path.join(ROOT,'knowledge.yaml')
    if os.path.exists(kp): kb=yaml.safe_load(open(kp,encoding='utf-8')).get('knowledge',[]) or []
    kb=sorted(kb,key=lambda k:k['id'])
    kbycell={}
    for k in kb:
        for c in (k.get('格') or []): kbycell.setdefault(c,[]).append(k)
    L=['# 光模块产业结构与公司能力地图（点先行 v2）','',
       '> 本页由 render.py 生成，勿手改（--verify 会拒绝）。',
       '> 回答三问：①产业由哪些环节构成 ②不同技术路线异同 ③每格谁在做、证据是什么。',
       '> 不回答"A是不是B的供应商"——公司按证据挂结构节点，不因同格而声称供货关系。','']
    # 先收元数据(名称+路线),供路线投影与流向复用
    meta={}
    def collect(n):
        if isinstance(n,list):
            for x in n: collect(x)
        elif isinstance(n,dict):
            if 'cell_id' in n: meta[n['cell_id']]=(n['名称'].strip(),(n.get('路线') or '未标').strip())
            for c in n.get('children',[]): collect(c)
    collect(tr['tree'])
    # 路线对比:39格按路线标签投影(纯渲染,零数据变更——标签本就在tree上)
    routes={}
    for cid,(_,rt) in meta.items(): routes.setdefault(rt,[]).append(cid)
    order=(['共用'] if '共用' in routes else [])+sorted(k for k in routes if k!='共用')
    L+=['## 技术路线对比（tree.yaml 路线标签投影）','',
        '共用骨干=三条路线都要经过的环节；独有格=该路线区别于其他路线之处。','',
        '| 路线 | 格数 | 有公司 | 空格 |','|---|---|---|---|']
    for r in order:
        cs=sorted(routes[r]); e=[c for c in cs if not bycell.get(c)]
        L.append(f"| {r} | {len(cs)} | {len(cs)-len(e)} | {','.join(e) if e else '—'} |")
    L.append('')
    for r in order:
        cs=sorted(routes[r])
        L.append(f"**{r}**（{len(cs)}格）："+'；'.join(f"{c} {meta[c][0]}({len(bycell.get(c,[]))}家)" for c in cs))
        L.append('')
    empty=[]
    def walk(n,dep):
        if isinstance(n,list):
            for x in n: walk(x,dep)
        elif isinstance(n,dict):
            if 'cell_id' in n:
                cs=bycell.get(n['cell_id'],[])
                L.append(f"{'#'*min(dep+1,6)} {n['cell_id']} {n['名称']}  ·路线:{n.get('路线','')}  ·{len(cs)}家")
                if cs:
                    L.append('| 公司 | 状态 | 上市 | 引语 | 锚 |'); L.append('|---|---|---|---|---|')
                    for p in sorted(cs,key=lambda x:x['公司']):
                        L.append(f"| {p['公司']} | {p['状态']} | {p['上市标签']} | {p['命中引语'][:60]} | [锚]({p['锚点URL']}) |")
                else:
                    empty.append(n['cell_id']); L.append('（空格——未有公司过闸）')
                for k in kbycell.get(n['cell_id'],[]):
                    # 主格(格列表首位)出全文,其余格只给指针,避免同一条知识重复刷屏
                    if (k.get('格') or [None])[0]==n['cell_id']:
                        L.append(f"> 📖 **{k['标题']}**（{k['id']}，全文见 out/知识库.md）")
                        for ln in k['一句话'].strip().split('\n'): L.append(f"> {ln}")
                    else:
                        L.append(f"> 📖 参见 {k['id']}　{k['标题']}（主格 {k['格'][0]}，全文见 out/知识库.md）")
                L.append('')
            else:
                L.append(f"{'#'*min(dep,6)} {n.get('名称',n.get('id',''))}"); L.append('')
                for c in n.get('children',[]): walk(c,dep+1)
    walk(tr['tree'],2)
    # BOM流向:骨架(常识层)+已证边计数(edges.csv经point_id→cell聚合)
    names={c:m[0] for c,m in meta.items()}
    pid2cell={p['point_id']:p['cell_id'] for p in pts}
    cnt={}
    for e in egs:
        sc,dc=pid2cell.get(e.get('供方point_id','')),pid2cell.get(e.get('需方point_id',''))
        if sc and dc and sc!=dc: cnt[(sc,dc)]=cnt.get((sc,dc),0)+1
    L+=['---','## BOM流向（骨架=常识层免锚；括号=已证公司级边数，来自edges.csv）','']
    skel=set()
    for f in tr.get('flows',[]):
        s=f['from']
        for d in f['to']:
            skel.add((s,d))
            c=cnt.get((s,d),0)
            L.append(f"- {s} {names.get(s,'')} → {d} {names.get(d,'')}"+(f"  **(已证{c}边)**" if c else ''))
    extra=sorted((k,v) for k,v in cnt.items() if k not in skel)
    if extra:
        L+=['','骨架外已证流向（现实先于常识，待并入骨架或复核归格）：']
        for (s,d),c in extra: L.append(f"- {s} {names.get(s,'')} → {d} {names.get(d,'')} ({c}边)")
    L.append('')
    dates=[p['检索日期'] for p in pts if p.get('检索日期')]
    cov=f"{len(pts)}点/{len(egs)}边"
    L+=['---',f"页脚：宇宙={tr['universe']['count']}家(冻结{tr['universe']['frozen_date']}) | 数据截至={max(dates) if dates else '—'} | 覆盖={cov} | 空叶格={len(empty)}/{len(meta)}: {','.join(empty) if empty else '无'}（纪律第8条 commit 取此数）"]
    os.makedirs(outdir,exist_ok=True)
    md='\n'.join(L)+'\n'
    open(os.path.join(outdir,'全景.md'),'w',encoding='utf-8').write(md)
    html='<!DOCTYPE html><meta charset="utf-8"><title>光模块供应链全景v2</title><body style="font-family:sans-serif;max-width:960px;margin:2em auto"><pre style="white-space:pre-wrap">'+md.replace('&','&amp;').replace('<','&lt;')+'</pre></body>'
    open(os.path.join(outdir,'全景.html'),'w',encoding='utf-8').write(html)
    # 知识库独立页: 每条=大白话结论+细说+判定用法+逐条证据(引语+出处+锚)
    K=['# 光模块产业知识库','',
       '> 本页由 render.py 从 knowledge.yaml 生成，勿手改（--verify 会拒绝）。',
       '> 回答"这个环节到底是干嘛的、为什么难、怎么判断谁够格"。每条都带证据引语与出处；没证据的常识不进本库。','']
    if not kb: K.append('（knowledge.yaml 为空）')
    for k in kb:
        cells='、'.join(k.get('格') or []) or '通用（不限某一格）'
        K+=[f"## {k['id']}　{k['标题']}",'',f"**适用环节**：{cells}　|　**录入**：{k.get('录入日期','—')}",'',
            '### 一句话','',k['一句话'].strip(),'']
        if k.get('说细点'): K+=['### 说细点','',k['说细点'].strip(),'']
        if k.get('怎么用它判断'): K+=['### 怎么用它判断','',k['怎么用它判断'].strip(),'']
        K+=['### 证据','']
        for e in (k.get('证据') or []):
            K.append(f"**{e['谁']}**")
            if e.get('原话'): K.append(f"> {e['原话']}")
            K.append(f"　出处：{e.get('出处','—')}")
            a=e.get('锚','—')
            if isinstance(a,dict):  # search_protocol 负证据协议
                a='；'.join(f"{x}：{a[x]}" for x in ('关键词','语料范围','检索日期','命中数') if x in a)
            K.append(f"　锚（{e.get('锚型','?')}）：{a}")
            if e.get('说明'): K.append(f"　为什么算证据：{e['说明']}")
            K.append('')
        if k.get('关联点'): K+=[f"**关联点**：{'、'.join(k['关联点'])}",'']
        if k.get('关联判例'): K+=[f"**关联判例**：{k['关联判例']}",'']
        K+=['---','']
    K.append(f"页脚：知识条目 {len(kb)} 条 | 覆盖环节 {len(kbycell)} 个")
    kmd='\n'.join(K)+'\n'
    open(os.path.join(outdir,'知识库.md'),'w',encoding='utf-8').write(kmd)
    khtml='<!DOCTYPE html><meta charset="utf-8"><title>光模块产业知识库</title><body style="font-family:sans-serif;max-width:900px;margin:2em auto;line-height:1.7"><pre style="white-space:pre-wrap">'+kmd.replace('&','&amp;').replace('<','&lt;')+'</pre></body>'
    open(os.path.join(outdir,'知识库.html'),'w',encoding='utf-8').write(khtml)
    # 问题队列：从现有账本确定性派生 QA–QE
    _write_queue(meta, bycell, kbycell, ships, tri, egs, outdir)
    # 研究问题树 v2（ADR-0009）：双知识体系 + Why 关联
    write_research_tree(outdir)
if __name__=='__main__':
    if '--verify' in sys.argv:
        left=tempfile.mkdtemp(); right=tempfile.mkdtemp()
        try:
            build(left); build(right)
            # 生成物不是事实源；只校验同一 canonical 输入能否两次得到完全相同的六个读者文件。
            ok=True
            for f in ('全景.md','全景.html','知识库.md','知识库.html','问题队列.md','研究问题树.md'):
                lp=os.path.join(left,f); rp=os.path.join(right,f)
                if not (os.path.exists(lp) and os.path.exists(rp) and filecmp.cmp(lp,rp,shallow=False)):
                    ok=False; break
        finally:
            shutil.rmtree(left); shutil.rmtree(right)
        if not ok: print('\033[31m[--verify] 两次临时重建不一致或文件缺失\033[0m'); sys.exit(1)
        print('--verify: 两次临时重建一致(out/非canonical)')
    else:
        build(os.path.join(ROOT,'out')); print('out/ 已重建')
