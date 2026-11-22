"""Extract Gemini leads from historical summaries and saved Drive snapshots."""
import hashlib
import json
import re
from pathlib import Path

import compliance

DAY = re.compile(r'^\s*(?:[*-]\s*)?\[(20\d\d-\d\d-\d\d)\]\s*(.*)')
NESTED = re.compile(r'^\s+\*\s+(.*)')
DOC = 'https://docs.google.com/document/d/1BxeKVaHKMDXMy8vgI2t_ieIF3Meb2ctUlIeHExZ3Hz8/edit'

# Question routing is a review suggestion, never a semantic match to an existing fact.
RULES = [
    (r'模场|\bFAU\b|光纤阵列|对准机台|耦合机台', 'PQ005 / PQ009（接口与接口验证；候选路由）',
     '可为接口问题补一条同一器件的耦合设计与验收条件；分开几何尺寸、模场和损耗，不混用。',
     '具体型号的光学结构、工作波长、模场口径及插损/回损实测；供货说法需同型号的一手披露。'),
    (r'\b448G\b|\b224G\b|单波.{0,3}400G|802\.3|\bMSA\b|CEI-', 'TQ005 / TQ006（标准与电接口；候选路由）',
     '补具体规范的光 lane、电 lane、总吞吐、距离和版本；区分提案、演示和已发布标准。',
     '标准组织原文、发布日期、文档状态和对应章节/表；验证对象需型号和测试条件。'),
    (r'订单|量产|批量|出货|回片|送样|产能|净利|募资|回购|上市|目标价|股价|评级', 'UNKNOWN：未绑定同公司、同型号或同期间的正式账本条目',
     '拆开订单、送样、产线规划、出货、公司财务和市场观点；仅保留对原问题有用且可证的子主张。',
     '公司或交易所原文和页段；需核对报告期、型号、单位及实际兑现与计划的区别。'),
    (r'\b(?:CPO|NPO|OOI|CPX)\b|共封装|近封装', 'TQ008（封装架构；候选路由）',
     '拟补具体参考设计的光引擎位置、电接口和可维护性边界；设计说明不能证明量产。',
     '设计方原始架构图、型号/场景、测试条件和阶段；比较功耗时需同口径基线。'),
    (r'\b(?:DSP|LPO|LRO)\b|线性直驱|重定时', 'TQ006（电接口架构；候选路由）',
     '若有原文，补信号处理位置及链路约束；区分无模块 DSP 与无系统补偿。',
     '设计方规范或框图、DSP/均衡位置及距离、速率和误码条件。'),
    (r'硅光|\b(?:EML|TFLN|InP|VCSEL|CW|SiPh)\b|薄膜铌酸锂|调制器', 'TQ007（光子平台；候选路由）',
     '拟补该实例如何产生、调制或接收光，限定材料与性能条件。',
     '具体器件和原始规格/论文、图表或试验条件；产业化口径需另证。'),
]
FALLBACK = ('UNKNOWN：未定位到同对象的既有问题或账本条目', '先拆出可核验的独立主张，明确行业相关性后再提出对应写入。', '须回到最初披露/原始数据，定位标题、日期、页段及适用对象。')


def units(raw):
    lines = raw.splitlines()
    dated = [(i, m[1], m[2]) for i, line in enumerate(lines) if (m := DAY.match(line))]
    before_daily = dated[0][0] if dated else len(lines)
    for i, line in enumerate(lines[:before_daily]):
        lead = re.sub(r'^\d+\.\s+', '', line.strip().removeprefix('* ').strip())
        # Exclude titles, section headings and bibliography labels.
        if len(lead) >= 36 and lead.endswith(('。', '；')):
            if compliance.matches(lead):
                yield i, None, lead, line
    for j, (i, entry_date, header) in enumerate(dated):
        end = dated[j+1][0] if j+1 < len(dated) else len(lines)
        detail = [(ix, m[1]) for ix in range(i+1, end) if (m := NESTED.match(lines[ix]))]
        expanded_format = not lines[i].lstrip().startswith('*')
        if detail:
            for ix, q in detail:
                if not expanded_format or compliance.matches(q):
                    yield ix, entry_date, q, q
        else:
            content = header.partition('来源：')[0]
            for q in re.split('[；;]', content):
                if q.strip() and (not expanded_format or compliance.matches(q)):
                    yield i, entry_date, q.strip(), header


def collect(repo, state, cutoff):
    items, dates, versions = {}, [], {}
    qpath = repo/'research_questions.yaml'
    question_lines = {m[1]:i for i,line in enumerate(qpath.read_text().splitlines(),1)
                      if (m:=re.match(r'^  - id: ([A-Z]+\d+)$',line))}

    def ingest(src, path, day, field, compliance_only):
        raw = src.get('content')
        if not raw:
            return 0
        version = hashlib.sha256(raw.encode()).hexdigest()
        src_ref = src.get('source_url') or (DOC if src.get('source_kind') == 'cloud_cache' else '')
        versions.setdefault(version, []).append({
            'date':day, 'ref':str(path), 'field':field, 'modified_at':src.get('original_modified_at')})
        n = 0
        for ix, entry_date, lead, quote in units(raw):
            if entry_date and entry_date > min(day, cutoff):
                continue
            topics = compliance.matches(lead)
            if not topics and (compliance_only or not entry_date):
                continue
            key = (entry_date, ' '.join(lead.split()))
            if key not in items:
                rid = 'G-'+hashlib.sha256(repr(key).encode()).hexdigest()[:16]
                target, proposal, gap = next(((t,a,b) for pat,t,a,b in RULES if re.search(pat, lead, re.I)), FALLBACK)
                subject = f'纪要标注 {entry_date}' if entry_date else 'Gemini 合规综述'
                items[key] = dict(id=rid, stream='补充', category='Gemini 逐日线索', dates=[],
                                  subject=subject, claim=lead, quote=quote, anchors=[],
                                  target=target, target_anchors=[{'label':f'既有问题 {q}','ref':f'{qpath}#L{question_lines[q]}'}
                                                                 for q in re.findall(r'\b(?:PQ|TQ)\d+\b',target)],
                                  proposal=proposal, gap='未绑定一手原文。'+gap,
                                  disposition='仅作线索', source_entry_date=entry_date or '',
                                  snapshot_versions=[])
                if topics:
                    compliance.apply(items[key], topics, entry_date)
            row = items[key]
            if not row['anchors'] or (topics and compliance_only and path.parent == Path(__file__).resolve().parent):
                row['anchors'].append({'label':f'Gemini 原文 · {field} 第 {ix+1} 行（解码后）','ref':str(path)})
            if src_ref and not any(a['ref']==src_ref for a in row['anchors']):
                row['anchors'].append({'label':'Google Drive 汇编文档','ref':src_ref})
            if day not in row['dates']:
                row['dates'].append(day)
            if version[:16] not in row['snapshot_versions']:
                row['snapshot_versions'].append(version[:16])
            n += 1
        return n

    for p in sorted((state/'combined/daily').glob('*.json')):
        if not re.fullmatch(r'20\d\d-\d\d-\d\d', p.stem) or p.stem > cutoff:
            continue
        g = (json.loads(p.read_text()).get('gemini') or {})
        source_states = []
        n = 0
        for idx, src in enumerate(g.get('sources', [])):
            source_states.append({'kind': src.get('source_kind'), 'status': src.get('status'), 'content_date': src.get('content_date')})
            n += ingest(src, p, p.stem, f'gemini.sources[{idx}].content', False)
        dates.append({'date':p.stem,'source_states':source_states,'lead_observations':n})
    extra = [(p,p.stem.removeprefix('cloud-snapshot-')) for p in sorted((state/'gemini').glob('cloud-snapshot-*.json'))]
    extra += [(p,p.parent.name) for p in sorted((state/'audit').glob('*/cloud-submitted-snapshot.json'))]
    extra += [(p,p.stem.removeprefix('gemini-compliance-drive-'))
              for p in sorted(Path(__file__).resolve().parent.glob('gemini-compliance-drive-*.json'))]
    for p, day in extra:
        if re.fullmatch(r'20\d\d-\d\d-\d\d',day) and day <= cutoff:
            ingest(json.loads(p.read_text()), p, day, 'content', True)
    rows = list(items.values())
    by_id = {r['id']:r for r in rows}
    pair = ('G-f2cf4505e36d44db', 'G-603d1e220d8b305e')
    if all(i in by_id for i in pair):
        for current, other in (pair, pair[::-1]):
            by_id[current]['gap'] += f' 同一汇编中对 3.2T 限制的说法有差异，建议同时核对 {other} 及研报原文。'
    regulatory = [r for r in rows if r['stream']=='Gemini 合规']
    return rows, {
        'snapshot_versions':len(versions), 'snapshot_refs_by_sha256':versions, 'per_date':dates,
        'compliance_dated':sum(bool(r['source_entry_date']) for r in regulatory),
        'compliance_undated':sum(not r['source_entry_date'] for r in regulatory),
        'scope':'逐日纪要按标注日和原文去重；未标日的合规背景单列。补充快照只提取合规。较晚快照补写旧日不能反推采集日期。组合段落须拆证后才可考虑入库。',
    }
