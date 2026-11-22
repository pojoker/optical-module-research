# -*- coding: utf-8 -*-
"""Step 1 账本确定性修复脚本 (OPTICAL-STEP1-LEDGER-AND-GATES-20261121, opus-ledger).

运行:  PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 \
        out/step1-ledger-remediation-20261121/remediate_ledgers.py
设计:
  * 只写工作包授权的账本; 读 archive/output/edges.csv 仅用于逐字恢复截断字段.
  * CSV 按字节流保留 BOM 与 \n / \r\n; 未改动记录原样保留原始文本(含多行字段),
    只有被改动的记录用 csv QUOTE_MINIMAL 重新序列化, 保证 git diff 只落在改动行.
  * 所有修改是"设定为目标值"或"已含则跳过", 重复运行幂等(第二次运行 changes=0).
  * 每处修改写入 ledger-changes.json (before/after/reason/evidence).
"""
import csv, io, json, os, re, sys, glob, hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
TODAY = '2026-11-21'
CHANGES = []
VERIFY = []


def log(file, rid, field, before, after, reason, evidence=None):
    CHANGES.append({'file': file, 'id': rid, 'field': field, 'before': before,
                    'after': after, 'reason': reason, 'evidence': evidence or ''})


def verify(item, result, evidence):
    VERIFY.append({'item': item, 'result': result, 'evidence': evidence})


# ------------------------------------------------------------------ CSV I/O
class Ledger:
    def __init__(self, path):
        self.path = path
        raw = open(path, 'rb').read()
        self.bom = raw.startswith(b'\xef\xbb\xbf')
        text = raw[3:].decode('utf-8') if self.bom else raw.decode('utf-8')
        self.eol = '\r\n' if '\r\n' in text else '\n'
        self.trailing = text.endswith(self.eol)
        lines = text.split(self.eol)
        if self.trailing:
            lines = lines[:-1]
        recs, buf = [], None
        for ln in lines:
            buf = ln if buf is None else buf + self.eol + ln
            if buf.count('"') % 2 == 0:
                recs.append(buf)
                buf = None
        assert buf is None, f'{path}: unbalanced quotes at EOF'
        self.header_raw = recs[0]
        self.header = next(csv.reader(io.StringIO(recs[0], newline='')))
        self.rows = []
        for r in recs[1:]:
            vals = next(csv.reader(io.StringIO(r, newline='')))
            d = {h: (vals[i] if i < len(vals) else None) for i, h in enumerate(self.header)}
            self.rows.append({'raw': r, 'n': len(vals), 'd': d, 'orig': dict(d), 'dirty': False})
        self.key = self.header[0]
        self.orig_bytes = raw

    def get(self, rid):
        hits = [r for r in self.rows if r['d'][self.key] == rid]
        return hits

    def one(self, rid):
        h = self.get(rid)
        assert len(h) == 1, f'{self.path}: {rid} matches {len(h)} rows'
        return h[0]

    def set(self, rid, field, value, reason, evidence=None, row=None):
        r = row or self.one(rid)
        old = r['d'][field]
        if old == value:
            return False
        r['d'][field] = value
        r['dirty'] = True
        log(self.path, rid, field, old, value, reason, evidence)
        return True

    def delete(self, row, reason, evidence=None):
        self.rows.remove(row)
        log(self.path, row['d'][self.key], '<row deleted>', row['raw'], None, reason, evidence)

    def insert_after(self, anchor_row, values, reason):
        d = {h: values.get(h, '') for h in self.header}
        nr = {'raw': None, 'n': len(self.header), 'd': d, 'orig': {}, 'dirty': True}
        idx = self.rows.index(anchor_row) + 1 if anchor_row else len(self.rows)
        self.rows.insert(idx, nr)
        log(self.path, d[self.key], '<row inserted>', None, d, reason)
        return nr

    def ser(self, d):
        s = io.StringIO()
        w = csv.writer(s, lineterminator='', quoting=csv.QUOTE_MINIMAL)
        w.writerow([d[h] if d[h] is not None else '' for h in self.header])
        out = s.getvalue()
        return out.replace('\r\n', self.eol) if self.eol == '\r\n' else out

    def save(self):
        parts = [self.header_raw] + [self.ser(r['d']) if r['dirty'] else r['raw'] for r in self.rows]
        text = self.eol.join(parts) + (self.eol if self.trailing else '')
        data = (b'\xef\xbb\xbf' if self.bom else b'') + text.encode('utf-8')
        if data != self.orig_bytes:
            open(self.path, 'wb').write(data)
            return True
        return False


def grep_lines(path, needle):
    out = []
    for i, l in enumerate(open(path, encoding='utf-8', errors='ignore').read().split('\n')):
        if needle in l:
            out.append((i + 1, l.strip()))
    return out


def pct(a, b):
    return f'{a / b * 100:.1f}%'


# ================================================================ 1. shipments
S = Ledger('shipments.csv')
SHIP = 'shipments.csv'

# 1a. SE056 意华 2024: 千只漏乘 + 出处表名
ann = glob.glob('corpus/annual-2024/002897/*.pdf.txt')[0]
ev644 = [x for x in grep_lines(ann, '2,464,381,267.00') if x[0] == 644]
assert ev644 and ev644[0][1].startswith('连接器'), 'SE056 年报第644行不是分行业-连接器'
asp = 2464381267.00 / (3726893.686 * 1000)
verify('SE056 收入出处', '2024年报第644行=分行业-连接器全口径(第648行通讯连接器产品=1,038,329,920.82另列)',
       f'{ann}:644 {ev644[0][1]}')
S.set('SE056', '收入输入', '2,464,381,267.00元(意华股份2024年报同节分行业表-连接器全口径)',
      '出处括号误标"分产品表";24.64亿元实为2024年报第644行分行业-连接器全口径', f'{ann}:644')
S.set('SE056', 'ASP输入', f'隐含混合ASP≈{asp:.2f}元/只(即{asp*1000:.1f}元/千只;2024连接器全口径量价同表)',
      f'漏乘千只致1000倍错:2,464,381,267.00÷(3,726,893.686×1000)={asp:.5f}元/只', f'{ann}:644')

# 1b. 产能利用率口径纠偏: 产量÷产能 / 销量÷产能 / 销量÷产量
CAP = {  # row: (产能, 产量, 销量, 显示单位, 附注)
    'SE001': (2806, 2376, 2109, '万只', ''),
    'SE002': (1747, 1634, 1603, '万只', ''),
    'SE003': (63654.49, 47383.50, 25423.34, '万个', ';注:年报注明产能、产量含内部产品线间领用'),
    'SE007': (2338, 1564.25, 1301.99, '万件', ''),
    'SE008': (1254, 572.26, 551.08, '万件', ''),
    'SE009': (27702.55, 25613.31, 23836.87, '万个', ''),
    'SE010': (5200000, 5169575, 5048760, '件', ';接近满产'),
    'SE011': (418, 302, 286, '万只', ''),
    'SE012': (505093448, 129039479, 127334475, '件', ';新增产线投入产能大增'),
    'SE042': (59200, 33232.09, 20876.67, '万个', ';注:年报注明产能、产量含内部产品线间领用'),
}


def fmtn(x):
    if float(x).is_integer():
        return f'{int(x):,}'
    return f'{x:,.2f}'


for rid, (cap, prod, sold, u, note) in CAP.items():
    r = S.one(rid)
    if rid != 'SE042':
        d = r['d']['推导式']
        for v in (cap, prod, sold):
            assert fmtn(v) in d, f'{rid} 推导式缺 {fmtn(v)}'
    val = (f'产量{fmtn(prod)}{u}≤产能{fmtn(cap)}{u}(产能利用率{pct(prod, cap)};'
           f'销量/产能比{pct(sold, cap)};产销率{pct(sold, prod)}{note}),通过')
    S.set(rid, '产能天顶检', val,
          '产能利用率=产量÷产能;原值把销量÷产能当利用率或未标口径(11/19审阅C06)',
          '数值取自同行推导式所载年报产销表')

# SE042 推导式补产能与库存恒等式缺口注记
t24 = glob.glob('corpus/annual-2024/300394/*.pdf.txt')[0]
cap_ev = grep_lines(t24, '33,232.09')
note042 = (';口径注记:FY2024年报"生产经营和投资项目情况"表同披露产能59,200万个,且注明"以上产能、产量数据中包含了公司内部产品线间领用的产品"'
           '(年报第1068-1076行);故期初10,602.07+产33,232.09-销20,876.67=22,957.49万个≠期末6,866.51万个,差额系内部领用,存量恒等式不可直接勾稽')
r = S.one('SE042')
if '内部产品线间领用' not in r['d']['推导式']:
    S.set('SE042', '推导式', r['d']['推导式'] + note042, '库存恒等式缺口口径注记+产能来源', f'{t24}:1068-1076 {cap_ev[:2]}')

# SE039 三安: 利用率字段须写明产量
S.set('SE039', '产能天顶检',
      '产量356.37KK/销量381.82KK(产销率107.14%复算吻合);产能利用率39.08%系问询函同表直接披露(照录,非本表复算),通过',
      '机器门要求"利用率"字段同时写明产量;数值不变', '同行推导式')

# 1c. SE016 舍入
r = S.one('SE016')
if '101.3%' in r['d']['产能天顶检']:
    S.set('SE016', '产能天顶检', r['d']['产能天顶检'].replace('101.3%', f'{911160/899963*100:.1f}%'),
          f'911,160÷899,963={911160/899963*100:.3f}%,四舍五入为101.2%')

# 1d. ASP 科学计数法与单位标签
MULT = lambda u: 1e6 if u == 'KK' else 1e3 if u.startswith('千') and u != '千克' else 1e4 if u.startswith('万') else 1
UNIT_LABEL = {'万个': '个', '台': '台', '台/套': '台套', '支/套': '支套', '片/个': '片', '万片': '片', '万支': '支',
              '万平方米': '平方米', '千克': '千克', '万件': '件', '件': '件', '万只': '只', '千只': '只', 'KK': '只'}


def parse_rev(s):
    m = re.match(r'\s*([\d,]+(?:\.\d+)?)\s*(亿元|万元|元)', s or '')
    if not m:
        return None
    return float(m.group(1).replace(',', '')) * {'元': 1, '万元': 1e4, '亿元': 1e8}[m.group(2)]


ASP_RE = re.compile(r'ASP≈?([\d,]+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(万?元)/([A-Za-z\u4e00-\u9fff]+)')
for r in S.rows:
    d = r['d']
    m = ASP_RE.search(d['ASP输入'] or '')
    if not m:
        continue
    rid, u = d['row_id'], d['单位']
    want = UNIT_LABEL.get(u)
    num, cur_unit = m.group(1), m.group(3)
    rev = parse_rev(d['收入输入'])
    q = float(d['出货量']) * MULT(u)
    newnum = num
    if 'e' in num.lower():
        v = rev / q
        newnum = f'{v:,.0f}' if v >= 1000 else f'{v:.4g}'
    newunit = want if (want and cur_unit != want) else cur_unit
    if newnum != num or newunit != cur_unit:
        new = d['ASP输入'][:m.start(1)] + newnum + m.group(2) + '/' + newunit + d['ASP输入'][m.end(3):]
        why = []
        if newnum != num:
            why.append(f'科学计数法{num}→按收入÷(出货量×倍率)={rev:,.2f}÷{q:,.0f}重算')
        if newunit != cur_unit:
            why.append(f'单位标签元/{cur_unit}与单位列[{u}]不符→元/{newunit}')
        S.set(rid, 'ASP输入', new, ';'.join(why))

# 1e. "(同比反算)" 错标核验: annual-2024 原文直接印出绝对值则删标并留证; 否则降 C
YOY_IDS = 'SE050 SE051 SE052 SE054 SE055 SE060 SE061 SE063 SE064 SE065 SE066 SE067 SE068 SE069 SE070 SE089'.split()
CODE = {'仕佳光子': '688313', '德科立': '688205', '剑桥科技': '603083', '蓝特光学': '688127', '腾景科技': '688195',
        '快克智能': '603203', '博敏电子': '603936', '拓荆科技': '688072', '博众精工': '688097', '沪硅产业': '688126',
        '炬光科技': '688167', '燕东微': '688172', '普源精电': '688337', '新益昌': '688383', '奥特维': '688516', '芯源微': '688037'}
for rid in YOY_IDS:
    r = S.one(rid)
    d = r['d']
    code = CODE[d['公司']]
    f = glob.glob(f'corpus/annual-2024/{code}/*.pdf.txt')[0]
    nums = re.findall(r'(销|产|存)([\d,]+(?:\.\d+)?)', d['推导式'].split(');与')[0])
    lines = open(f, encoding='utf-8', errors='ignore').read().split('\n')
    hit = None
    if d['期间'] == '2024年度' and nums:
        # 同一行同时印出 产/销/存 三个绝对值(容忍 .00 格式差)
        def norm(x):
            return x.replace(',', '').rstrip('0').rstrip('.') if '.' in x else x.replace(',', '')
        need = [norm(n) for _, n in nums]
        for i, l in enumerate(lines):
            toks = [norm(t) for t in re.findall(r'[\d,]+(?:\.\d+)?', l)]
            if all(n in toks for n in need):
                hit = (i + 1, l.strip())
                break
    if hit:
        verify(f'{rid} 同比反算错标', 'FY2024年报产销量表原文直接印出产/销/存绝对值,非同比反算,保留B并删错标',
               f'{f}:{hit[0]} {hit[1]}')
        if '(同比反算)' in d['推导式']:
            new = d['推导式'].replace('(同比反算)', '')
            new += f';核验({TODAY}):产/销/存绝对值见{f}第{hit[0]}行原文直接印出,属年报直接披露,原反算模板错标已删'
            S.set(rid, '推导式', new, '删除"(同比反算)"错标(annual-2024原文行证据见evidence)', f'{f}:{hit[0]} {hit[1]}')
    else:
        verify(f'{rid} 同比反算', '2023年度绝对值确系FY2024年报同比列反算,FY2023年报不在库→证据等级降C',
               f'{f} (无同行三值直接披露)')
        S.set(rid, '证据等级', 'C', '推导式含同比反算(2023绝对值由FY2024年报同比列反算),按ADR-0001与SE071/SE072同标准封顶C')

# 1f. 库存恒等式缺口口径注记
N050 = (';口径注记:FY2024年报产销表另列自用量2,487.64万只(内部领用),'
        '期初1,933.39+产12,312.00-自用2,487.64-销10,711.97=期末1,045.78万只吻合')
N070 = (';口径注记:2023口径为"铝线键合机"(存14台,见SE104),2024扩为"键合机/AOI设备",'
        '期初14+产166-销60=120台≠期末4台,系产品口径变化,存量恒等式不可跨年勾稽')
for rid, note, key in (('SE050', N050, '自用量2,487.64'), ('SE070', N070, '铝线键合机"(存14台')):
    r = S.one(rid)
    if key not in r['d']['推导式']:
        S.set(rid, '推导式', r['d']['推导式'] + note, '库存恒等式缺口口径注记')

# 1g. 全表 ASP 算术与单位复核(<5%)
ship_check = []
for r in S.rows:
    d = r['d']
    m = ASP_RE.search(d['ASP输入'] or '')
    rev = parse_rev(d['收入输入'])
    if not (m and rev):
        continue
    v = float(m.group(1).replace(',', '')) * (1e4 if m.group(2) == '万元' else 1)
    calc = rev / (float(d['出货量']) * MULT(d['单位']))
    err = abs(v - calc) / calc
    ship_check.append({'row': d['row_id'], 'asp': v, 'calc': round(calc, 4), 'rel_err': round(err, 5),
                       'unit': d['单位'], 'asp_unit': m.group(3)})
    assert err < 0.05 or abs(v - calc) <= 0.05, f"{d['row_id']} ASP偏差{err:.2%}"
    assert 'e+' not in d['ASP输入'] and 'e+' not in d['收入输入']
verify('shipments ASP算术复核', f'{len(ship_check)}行均<5%且无科学计数法', ship_check)
for r in S.rows:
    d = r['d']
    assert not ('同比反算' in d['推导式'] and d['证据等级'] == 'B'), d['row_id']
    if '利用率' in (d['产能天顶检'] or ''):
        assert '产量' in d['产能天顶检'], d['row_id']

# ================================================================ 2. edges
E = Ledger('edges.csv')
arc = {}
with open('archive/output/edges.csv', encoding='utf-8-sig', newline='') as fh:
    for a in csv.DictReader(fh):
        arc[a['edge_id']] = a
FMAP = {'占比或金额原文': '占比或金额'}
SUFFIX = re.compile(r'(\|多期打包待展开|\|原等级:|;codex复核|\|智禾=)')
for r in E.rows:
    d = r['d']
    a = arc.get(d['edge_id'])
    if not a:
        continue
    for k in ('占比或金额原文', '验证状态', '备注'):
        av = a.get(FMAP.get(k, k))
        cv = d[k]
        if av is None or cv == av:
            continue
        m = SUFFIX.search(cv)
        base, suf = (cv[:m.start()], cv[m.start():]) if m else (cv, '')
        if base != av and av.startswith(base) and len(av) > len(base):
            E.set(d['edge_id'], k, av + suf, '恢复迁移时被硬截断的字段(以archive/output/edges.csv逐字为据,保留其后新增注记)',
                  f'archive/output/edges.csv {d["edge_id"]}.{FMAP.get(k, k)}', row=r)

# 需方被嵌套括号切断(E128/E231): 按招股书注释逐字补全
pros = 'corpus/legacy-input/v16/prospectus/688313_仕佳光子_招股说明书_注册稿.txt'
pros2 = 'corpus/legacy-input/v16/prospectus/688048_长光华芯_招股说明书_注册稿.txt'
assert grep_lines(pros, '注 5：金信诺及其关联方包括') and grep_lines(pros2, '注 3：飞顿国际包括')
E.set('E128', '需方', '金信诺及其关联方（深圳金信诺高新技术股份有限公司、深圳金信诺光电技术有限公司、金信诺（常州）轨道信号系统科技有限公司、赣州金信诺电缆技术有限公司、金信诺光纤光缆（赣州）有限公司、东莞金信诺电子有限公司）',
      '需方名在嵌套括号处被切断(左括号丢失),按招股书客户表注5逐字补全', f'{pros}:8016-8018')
E.set('E231', '需方', '飞顿国际（飞顿贸易（北京）有限公司及飞顿国际科技（北京）有限公司）',
      '需方名在嵌套括号处被切断(主名与左括号丢失),按招股书客户表注3逐字补全', f'{pros2}:8207-8211')

# 悬空引用
assert grep_lines('refs/解匿判例库.md', '## 判例#003') and grep_lines('refs/解匿判例库.md', '## 判例#006')
r = E.one('E036')
E.set('E036', '备注', r['d']['备注'].replace('判例见deanonymization-cases.md', '判例见refs/解匿判例库.md(判例#003,A级)'),
      '悬空旧底稿引用改指现存判例库', 'refs/解匿判例库.md:58 ## 判例#003')
r = E.one('E096')
E.set('E096', '备注', r['d']['备注'].replace('线索见jituanyi-leads.md', '判例候选见refs/解匿判例库.md(判例#006,C级候选不点名,侦察完成待判定)'),
      '悬空旧底稿引用改指现存判例库', 'refs/解匿判例库.md:161 ## 判例#006')
r = E.one('E008')
E.set('E008', '备注', r['d']['备注'].replace('死亡序列见seed findings', '死亡序列:2019-05美国BIS实体清单管制后逐步终止供货,2021归零(原载历史底稿)'),
      '悬空seed findings引用内联为实锤事实')

# E044 PINEWAVE 金额化
x308 = glob.glob('corpus/annual/300308/300308/*2025*.pdf.txt')[0]
evE = grep_lines(x308, '3,096,780,769.22') + grep_lines(x308, 'PINEWAVE')
E.set('E044', '数值类型', '金额', '补齐结构化金额(scan.py E_单位原生支持万美元)')
E.set('E044', '数值', '43378', '补齐结构化金额')
E.set('E044', '单位', '万美元', '补齐结构化金额')
r = E.one('E044')
if '3,096,780,769.22' not in r['d']['备注']:
    E.set('E044', '备注', r['d']['备注'] + ';2025年报核验:关联交易表PINEWAVE销售43,378万美元(第3937行),前五大客户表客户E=3,096,780,769.22元(8.10%,第1265行)',
          '补人民币金额核验', f'{x308} {evE}')

# point_id 指针
for eid, col in (('E165', '供方point_id'), ('E232', '供方point_id')):
    r = E.one(eid)
    if r['d'][col] == 'P026':
        E.set(eid, col, 'P156', '太辰光主业光纤连接器生产点在P156@D9;P026为在研AWG@D8')
        E.set(eid, '备注', r['d']['备注'] + ';原误挂在研点P026@D8,改挂P156@D9', '记录改挂')
for eid, col in (('E137', '需方point_id'), ('E141', '供方point_id')):
    if E.one(eid)['d'][col] == 'P036':
        E.set(eid, col, 'P037', 'P036(武汉云岭光电有限公司)并入P037,供需方列保留当年公告原称谓')

# 复核: 截断/悬空
for r in E.rows:
    d = r['d']
    for k in ('占比或金额原文', '验证状态'):
        v = d[k] or ''
        assert v.count('(') + v.count('（') == v.count(')') + v.count('）'), (d['edge_id'], k)
        assert not v.strip().endswith(('，', '；', '-')), (d['edge_id'], k)
    s = ' '.join(x or '' for x in d.values())
    for bad in ('deanonymization-cases.md', 'seed findings', 'jituanyi-leads.md'):
        assert bad not in s, (d['edge_id'], bad)

# ================================================================ 3. points
P = Ledger('points.csv')
PROTECT = {k: dict(P.one(k)['d']) for k in ('P031', 'P209')}

P.set('P026', '状态', '在建', '自身引语"AWG为在研项目,尚未量产"且注明"不构成生产中锚",状态与证据不符')

# P084 徕木: 错贴深南电路年报URL
lm = 'corpus/annual/603633/603633__em_徕木股份_em__2025_徕木股份2025年年度报告.pdf.txt'
lm_url = [r for r in csv.DictReader(open('corpus/annual/603633/annual_reports.csv', encoding='utf-8-sig'))][0]['pdf_url']
assert lm_url == 'https://static.cninfo.com.cn/finalpage/2026-04-28/1225206931.PDF'
_lmt = open(lm, encoding='utf-8').read()
for n in ('加大连接器业务投入，在汽车电子、新能源、机器人、光模块等技术上实现突破', '重点培育机器人、光模块产业，力推新项目加速转量产上规模',
          '持续开展在储能、光模块、数据中心、机器人等方向连接器产品的开发和市场拓展工作'):
    assert n in _lmt, n
r = P.one('P084')
if r['d']['锚点URL'] != lm_url:
    P.set('P084', '命中引语', '加大连接器业务投入，在汽车电子、新能源、机器人、光模块等技术上实现突破……重点培育机器人、光模块产业，力推新项目加速转量产上规模……持续开展在储能、光模块、数据中心、机器人等方向连接器产品的开发和市场拓展工作',
          '原引语挂错URL;换为徕木2025年报原文', f'{lm}:450-453,561')
    P.set('P084', '锚点URL', lm_url, '原URL 1225006760.PDF 为深南电路2025年报(=P083),错贴', 'corpus/annual/603633/annual_reports.csv')
    P.set('P084', '检索日期', TODAY, '重新核锚')
    P.set('P084', '判定等级', '判定闸-在建(徕木2025年报第450-453/561行:光模块方向连接器开发与市场拓展、重点培育光模块产业力推新项目转量产,尚无量产/出货披露,维持在建;'
          f'{TODAY}勘误:原锚误贴深南电路2025年报1225006760.PDF即P083,已改挂徕木2025年报;历史线索保留:800G光模块的壳体产品技术开发-湖南徕木,2023年度投资项目计划表总预算220万元,原codex核锚为投资项目主张,原锚失配待补)',
          '更新判定依据并保留历史线索')

# P061 联讯: 1.6T 量产供货 + 上市状态(待v6)
P.set('P061', '命中引语', '通信测试仪器方面，面向 1.6T 高速光模块测试需求的 65GHz 采样示波器、120GBaud 时钟恢复单元、1.6Tbps 误码分析仪、1.6Tbps 光模块测试仪等核心产品向多家国内外知名用户量产供货',
      '11/19审阅V01:旧引语停留于早期申报稿业务描述;换为2026半年报第17页原文', 'https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF#page=17 (2026-11-21 pdftotext复核)')
P.set('P061', '锚点URL', 'https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF#page=17；2026-01-07更新申报稿 https://static.sse.com.cn/stock/disclosure/announcement/c/202601/002075_20260107_UL2D.pdf',
      '换一手锚')
P.set('P061', '检索日期', '2026-11-19', '11/19审阅V01核实日')
P.set('P061', '判定等级', '判定闸-生产中(1.6T光模块全部核心测试仪器即65GHz采样示波器/120GBaud时钟恢复单元/1.6Tbps误码分析仪及1.6Tbps光模块测试仪量产供货,2026半年报第17页,2026-01-07更新申报稿第1-1-23页已载同口径;11/19审阅V01,2026-11-21复核原文;'
      '[待v6扩容同步]公司已于2026-04-24登陆科创板688808,见半年报股份变动情况说明,待v6宇宙对称性补录入_frozen.csv后同步切为A股;Step1不扩_frozen故上市标签暂保持未上市私企;'
      '历史:原引语"电子测量仪器和半导体测试设备的研发、制造、销售及服务",招股书,检索2026-07-24,edge_backed)',
      '更新判定;上市日以半年报原文2026-04-24为准(工作包brief写2026-08系误记)',
      '半年报:公司首次公开发行...并于2026年4月24日在上海交易所科创板上市')
P.set('P061', '判定会话日期', TODAY, '本轮改判')

# P196 核验(不改)
ir = 'corpus/ir/688126/688126_2026-05-29_沪硅产业_2026年5月投资者关系活动记录表.docx'
q196 = P.one('P196')['d']['命中引语']
assert os.path.exists(ir) and q196 in open(ir + '.txt', encoding='utf-8').read()
verify('P196 corpus/ir 坐标', 'docx与.docx.txt均在库,命中引语逐字命中', ir + '.txt')

# P041 引语截断补全; P042/P043 "同上"显式化
yd = glob.glob('corpus/annual/600105/600105/*2025*.pdf.txt')[0]
yd_url = [r for r in csv.DictReader(open('corpus/annual/600105/600105/annual_reports.csv', encoding='utf-8-sig'))][0]['pdf_url'] \
    if os.path.exists('corpus/annual/600105/600105/annual_reports.csv') else \
    [r for r in csv.DictReader(open(glob.glob('corpus/annual/600105/**/annual_reports.csv', recursive=True)[0], encoding='utf-8-sig'))][0]['pdf_url']
r = P.one('P041')
q = r['d']['命中引语']
if q.rstrip('"').endswith('MT-FA（MT光纤阵'):
    P.set('P041', '命中引语', q.rstrip('"') + '列）、MUX/DEMUX（复用器/解复用器）组件，以及DWDM/CCWDM/CDWDM（密集波分复用/紧凑型粗波分复用/可调谐波分复用）、环形器、隔离器、Z-BLOCK（Z型滤波片组件）等数据中心光模块关键组件"',
          '引语在"MT光纤阵"处截断(括号未闭合);按永鼎2025年报原文补全(含P042/P043所指AWG/MT-FA/隔离器)', f'{yd}:507-515')
for pid in ('P042', 'P043'):
    if P.one(pid)['d']['锚点URL'] == '同上':
        P.set(pid, '锚点URL', f'同P041:S0a本地扫描2025年报（600105__em_永鼎股份_em__2025_永鼎股份2025年年度报告.pdf；{yd_url}）',
              '"同上"锚点显式化(前一行P041同件)')

# 括号截断闭合(原注记已截断,不可恢复,显式标注)
TRUNC = {
    'P040': ('命中引语', '非独立TOSA/ROSA/跨阻', '非独立TOSA/ROSA/跨阻…[原注截断]）'),
    'P152': ('判定等级', '光芯片场景为)', '光芯片场景为…[原注截断]）)'),
    'P158': ('判定等级', "原义为'应用于航空航天、光通信)", "原义为'应用于航空航天、光通信…[原注截断]'))"),
    'P161': ('判定等级', '（同比+75.65)', '（同比+75.65…[原注截断]）)'),
    'P168': ('判定等级', '复核可酌情要求营收/客)', '复核可酌情要求营收/客…[原注截断]）)'),
    'P203': ('判定等级', '光迅/源杰同为客户)', '光迅/源杰同为客户);公司全称:苏州猎奇智能设备股份有限公司)'),
}
for pid, (col, old, new) in TRUNC.items():
    v = P.one(pid)['d'][col]
    if v.endswith(old):
        P.set(pid, col, v[:-len(old)] + new, '字段截断致括号未闭合;原文不可恢复,显式标注[原注截断]并闭合'
              if pid != 'P203' else '外层括号未闭合+补注公司全称(公司名统一为猎奇智能)')

# P264/P265 台股
for pid in ('P264', 'P265'):
    P.set(pid, '上市标签', '台股', '锚为台股上柜公司年报(113_Annual_Report),E_标签已含台股;tree观察名单注台股上柜3163')

# 合并 P036→P037
r036 = P.get('P036')
if r036:
    P.delete(r036[0], '同公司同格重复点(武汉云岭光电有限公司=武汉云岭光电股份有限公司曾用名),并入P037;edges E137/E141已改指P037')
P.set('P037', '判定等级', 'edge_backed(曾用名/当年公告称谓:武汉云岭光电有限公司;原重复点P036已并入P037,2026-11-21)', '记录合并')

# 合并 P204→P055, P203 改名
r204 = P.get('P204')
if r204:
    s = r204[0]['d']
    P.set('P055', '命中引语', s['命中引语'], 'P204(同公司同格EQ4)2026-07-14招股书引语就地升级P055')
    P.set('P055', '锚点URL', s['锚点URL'], '同上')
    P.set('P055', '检索日期', s['检索日期'], '同上')
    P.set('P055', '判定等级', '判定闸-生产中(同P203同句双格;耦合设备配套800G/1.6T光模块生产自述;原重复点P204已并入P055,2026-11-21;'
          '历史引语:光通信/半导体/汽车自动化等领域智能生产装备；产品应用于贴片、光学耦合、老化测试三核心环节,招股书第五节,edge_backed,检索2026-07-24)',
          '同上并保留历史')
    P.set('P055', '判定会话日期', s['判定会话日期'], '同上')
    P.delete(r204[0], '与P055同公司同格(EQ4)重复,已并入P055')
P.set('P203', '公司', '猎奇智能', '公司名统一(全称注于判定等级)')

# P200/P201 索尔思时效注记
OLD200 = '时效注记:披露时点2023-11,框架协议后未见进展或终止披露(2026-07-30检索),万通发展重组标的未完成'
NEWS = '原2023万通发展框架公告历史锚；注：东山精密(002384)已完成收购索尔思光电并表(见P130-P133)'
for pid, old in (('P200', OLD200), ('P201', '时效注记同上')):
    v = P.one(pid)['d']['判定等级']
    if old in v:
        P.set(pid, '判定等级', v.replace(old, NEWS), '陈旧"重组标的未完成"注记更新:东山精密已收购并表')

assert all(P.one(k)['d'] == PROTECT[k] for k in PROTECT), 'P031/P209 11/10 更新被改动'
for r in P.rows:
    for k, v in r['d'].items():
        v = v or ''
        assert v.count('(') + v.count('（') == v.count(')') + v.count('）'), ('points括号不平衡', r['d']['point_id'], k)
# 指针完整性
pids = {r['d']['point_id'] for r in P.rows} | {'ANON', 'EXT'}
for r in E.rows:
    for c in ('供方point_id', '需方point_id'):
        assert not r['d'][c] or r['d'][c] in pids, (r['d']['edge_id'], c)
for r in P.rows:
    for col in ('锚点URL',):
        for m in re.findall(r'corpus/(?:annual|annual-2024|ir|qa|legacy-input|web)/[^\s；;，,）)#]+', r['d'][col]):
            assert os.path.exists(m), (r['d']['point_id'], m)

# ================================================================ 4. triage / watchlist
T = Ledger('triage.csv')
for hid, keep_hint in (('仕佳光子+D8+2025年报', '基于平面光路技术解决方案的器件包括'), ('仕佳光子+D9+2025年报', '术语定义句(批量启发式,抽检确认)')):
    rows = T.get(hid)
    if len(rows) > 1:
        keep = [x for x in rows if keep_hint in x['d']['引语或线索摘要'] or keep_hint in x['d']['理由']][0]
        for x in rows:
            if x is not keep:
                T.delete(x, f'重复hit_id;保留信息更完整一行(含"{keep_hint}")')
r = T.one('新易盛C4专利+C4+kimi客户端')
if r['d']['处置'] != '已入点':
    T.set('新易盛C4专利+C4+kimi客户端', '处置', '已入点', '消除与P102跨表矛盾')
    T.set('新易盛C4专利+C4+kimi客户端', '理由', r['d']['理由'] + f'｜{TODAY} Step1:已入点P102(2025年报自研PIC厂内集成小批量,非裸芯片外售);重启跟踪改为裸硅光芯片外售或大规模放量(见_restart_watchlist)',
          '同上')
T.set('猎奇边归格+EQ4+codex', '公司', '猎奇智能', '公司名统一(P203改名猎奇智能,P204并入P055)')
T.set('猎奇边归格+EQ4+codex', '理由', '已入点:P203@EQ3+P055@EQ4(创业板IPO申报稿:贴片/耦合设备配套800G/1.6T,KN001准入①;原P204已并入P055)', '同上')
for r in T.rows:
    d = r['d']
    if '增量已入P203/P204' in (d['理由'] or ''):
        T.set(d['hit_id'], '理由', d['理由'].replace('增量已入P203/P204', '增量已入P203/P055(原P204已并入P055)'), 'P204并入P055', row=r)
    if 'corpus/qa/688313/qa.jsonl(sns.sseinfo.com e互动)' in (d['理由'] or ''):
        T.set(d['hit_id'], '理由', d['理由'].replace('corpus/qa/688313/qa.jsonl(sns.sseinfo.com e互动)', 'corpus/qa/688313/qa.jsonl ；来源sns.sseinfo.com e互动'),
              '路径与括号粘连,分隔清楚', row=r)
    if '语料corpus/annual/FIT/(2025年报在库)' in (d['理由'] or ''):
        T.set(d['hit_id'], '理由', d['理由'].replace('语料corpus/annual/FIT/(2025年报在库)', '语料corpus/annual/FIT/FIT/FIT_2025_Annual_Report.pdf.txt (2025年报在库)'),
              '路径与括号粘连且非文件,改为真实文件路径', row=r)
assert os.path.exists('corpus/annual/FIT/FIT/FIT_2025_Annual_Report.pdf.txt')
from collections import Counter
assert not [k for k, v in Counter(r['d']['hit_id'] for r in T.rows).items() if v > 1]

W = Ledger('corpus/_restart_watchlist.csv')
r = [x for x in W.rows if x['d']['公司'] == '新易盛' and x['d']['cell_id'] == 'C4'][0]
W.set('新易盛', '重启条件', '裸硅光芯片(PIC)对外销售或大规模放量自述(2025年报厂内集成PIC小批量已入P102,非裸芯片外售;专利=设计证据不足)',
      '与triage已入点对齐,跟踪目标改为外售/放量', row=r)
W.set('新易盛', '触发词', '硅光芯片外售|PIC|硅光放量|大规模量产', '同上', row=r)
r = [x for x in W.rows if x['d']['公司'] == '光迅科技' and x['d']['cell_id'] == 'EQ7边']
if r:
    r = r[0]
    W.set('光迅科技', 'cell_id', 'EQ7', '非标准cell_id规范化(边候选保留在重启条件)', row=r)
    W.set('光迅科技', '重启条件', '边候选(矽电→光迅,EQ7)—' + r['d']['重启条件'], '同上', row=r)
r = [x for x in W.rows if x['d']['公司'] == '顺络电子' and x['d']['cell_id'] == 'D4/M4']
if r:
    r = r[0]
    W.set('顺络电子', 'cell_id', 'D4', '拆为两行合法cell_id(D4陶瓷管壳)', row=r)
    W.set('顺络电子', '重启条件', '陶瓷管壳光模块应用从"可用于"到送样/订单', '拆行', row=r)
    nd = dict(r['d']); nd['cell_id'] = 'M4'; nd['重启条件'] = '磁珠/结构陶瓷材料光模块应用从"可用于"到送样/订单'
    W.insert_after(r, nd, '顺络D4/M4拆出M4行')

# ================================================================ 5. macro_evidence
M = Ledger('macro_evidence.csv')
XC25 = 'https://static.cninfo.com.cn/finalpage/2026-03-31/1225056459.PDF'
assert grep_lines(x308, '228 亿美元') and grep_lines(x308, '146 亿美元') and grep_lines(x308, '53 亿美元')
M.set('MC001', '量化结论', '2026年全球数通光模块市场约228亿美元（800G+1.6T合计146亿美元）', '11/19审阅C10:228亿与260亿两套口径拆分')
M.set('MC001', '来源描述', '中际旭创2025年年度报告(第737-745行)援引LightCounting预测:2026年全球数通光模块市场规模有望达228亿美元,800G和1.6T合计146亿美元(约占64%);2030年414亿美元', '改挂一手年报', f'{x308}:737-745')
M.set('MC001', '链接', XC25, '一手年报PDF')
M.set('MC001', '口径备注', '口径=数通光模块(非全品类、非以太网+CPO收发器口径);260亿美元以太网+CPO口径另见MC032;中金/新浪转引同数', '口径拆分')
if not M.get('MC032'):
    M.insert_after(M.one('MC031'), {
        'claim_id': 'MC032', '量化结论': '2026年以太网+CPO光收发器市场预测约260亿美元', '证据等级': 'B',
        '证据类型': '机构报告/厂商规格', '处理方式': '机构一手或厂商规格,可引用需附口径',
        '来源描述': 'LightCounting《Optics for AI》2026-01月报(以太网+CPO光收发器2026预测约260亿美元,原载MC001来源描述,本轮拆出);另附2026-05月报全收发器约400亿美元口径',
        '链接': 'https://lightcounting.com/newsletter/en/january-2026-optics-for-ai-clusters-366 https://www.lightcounting.com/newsletter/en/may-2026-silicon-photonics-lpolro-and-npocpo-377',
        '口径备注': '口径=以太网+CPO光收发器(1月月报);5月月报400亿美元为全收发器口径;二者均不得与MC001数通228亿口径混用'},
        '11/19审阅C10:260亿以太网+CPO口径拆成独立记录')
M.set('MC002', '证据等级', 'C', '宏观审计:仅东方财富财富号转述+c-light行业网,无一手锚')
M.set('MC002', '证据类型', '二手汇总', '同上')
M.set('MC002', '处理方式', '二手汇总,仅方向性参考不上首页', '同上')
r = M.one('MC002')
if '等级复审(2026-11-21' not in r['d']['口径备注']:
    M.set('MC002', '口径备注', r['d']['口径备注'] + ';等级复审(2026-11-21 Step1):中际旭创2025年报未载中国厂商份额,现仅东方财富财富号/c-light二手转述,B→C', '同上')
M.set('MC011', '来源描述', '中际旭创2025年年度报告援引LightCounting:2026年全球数通光模块228亿美元(第737行)、电信光模块53亿美元(第774行),数通占二者合计≈81%', '改挂一手年报', f'{x308}:737,774')
M.set('MC011', '链接', XC25, '一手年报PDF替换新浪/c-light转述')
M.set('MC011', '口径备注', '分母仅数通+电信两类(不含新兴市场),≈81%为本库按年报两数自算;原新浪/c-light转述链接已替换为一手年报', '口径说明')
M.set('MC005', '来源描述', '出自英伟达2025-08官方技术博客《Scaling AI Factories with Co-Packaged Optics for Better Power Efficiency》图3:1.6Tb/s单接口示例,可插拔约30W vs CPO约9W(约-70%);缺含外置激光源(ELS)与液冷整机的跨厂同边界可比实测', '11/19审阅C11补出处')
M.set('MC005', '链接', 'https://developer.nvidia.com/blog/scaling-ai-factories-with-co-packaged-optics-for-better-power-efficiency/', '补原文链接')
M.set('MC005', '口径备注', '维持D:单厂单接口示例,禁作全行业整机结论;从正文删除,仅作诚实标注(11/19审阅C11补出处)', '同上')
for cid in ('MC009', 'MC010'):
    M.set(cid, '口径备注', '内部证据账本可重算:由capability_details.csv实时重算(首页headline规则必需A级,非外部链接)', '写明A级依据')
M.set('MC012', '来源描述', 'NVIDIA GB200 NVL72官网规格(72 Blackwell GPU/72 IB NIC);SemiAnalysis拆解原无可核URL(搜索占位链接已删除),仅作背景不作锚', '去搜索占位')
M.set('MC012', '链接', 'https://www.nvidia.com/en-us/data-center/gb200-nvl72/', '修正笔误gb200-nvl2并删除baidu搜索占位')
for cid, note in (('MC022', '(原搜索占位链接已删除,无可核一手URL)'), ('MC027', '(原搜索占位链接已删除,无可核一手URL)'),
                  ('MC029', '(英伟达锁产能一说原挂搜索占位链接,已删除)')):
    r = M.one(cid)
    links = ' '.join(u for u in r['d']['链接'].split() if 'baidu.com/s?' not in u)
    if links != r['d']['链接']:
        M.set(cid, '链接', links, '删除baidu搜索占位链接')
        M.set(cid, '来源描述', r['d']['来源描述'] + note, '同上')
for r in M.rows:
    v = r['d']['链接'] or ''
    if 'ssgsmarketing@xueqiu.com' in v:
        M.set(r['d']['claim_id'], '链接', v.replace('https://ssgsmarketing@xueqiu.com/', 'https://xueqiu.com/'),
              'basic-auth畸形URL修复(ssgsmarketing@)', row=r)
for r in M.rows:
    d = r['d']
    assert not re.search(r'https?://[^/\s]*@', d['链接'] or '') and 'baidu.com/s?' not in (d['链接'] or '')
    if d['证据等级'] in ('A', 'B') and d['证据类型'] != '内部证据账本可重算':
        assert re.search(r'https?://', d['链接'] or ''), d['claim_id']

# ================================================================ 6. YAML (text-level, 保格式)
def edit_text(path, pairs, reason_prefix):
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-8')
    for old, new, why in pairs:
        if new in txt and old not in txt:
            continue
        assert txt.count(old) == 1, f'{path}: 目标串出现{txt.count(old)}次: {old[:60]}'
        txt = txt.replace(old, new)
        log(path, reason_prefix, 'text', old, new, why)
    if txt.encode('utf-8') != raw:
        open(path, 'wb').write(txt.encode('utf-8'))


# knowledge.yaml
NEWQ55 = P.one('P055')['d']['命中引语']
OLDQ55 = '    原话: 光通信/半导体/汽车自动化等领域智能生产装备；产品应用于贴片、光学耦合、老化测试三核心环节\n'
kn = open('knowledge.yaml', encoding='utf-8').read()
kn_pairs = [
    ('  - 谁: 猎奇智能（专做光模块封测设备，科创板IPO在审）', '  - 谁: 猎奇智能（专做光模块封测设备，创业板IPO在审）', 'KN001:猎奇为创业板IPO(深交所prjid=1004231),非科创板'),
    ('    所以耦合设备的核心是高精密运动平台+视觉引导（猎奇的耦合设备最小运动增量做到 50 纳米）。\n',
     '    所以耦合设备的核心是高精密运动平台+视觉引导。说“精度”要分清三个不同的物理量，不能互换：\n'
     '    ①最小运动增量（电机最轻推一下能走的最小步长）：招股书行业段说“部分国产厂商……耦合设备已能达到\n'
     '      最小运动增量 50nm”（第五节，1-1-122，第 9759–9760 行，主语是行业而非猎奇自述），技术门槛段说\n'
     '      光学器件位姿“调整最小运动增量达 50-100nm”（1-1-129，第 9984 行）；\n'
     '    ②分辨率（相当于尺子的最小刻度）：猎奇 10 纳米 vs ficonTEC 5 纳米；\n'
     '    ③重复定位精度（反复回到同一个点的误差）：猎奇 ±0.05 微米（=±50 纳米）vs ficonTEC ±0.02 微米（=±20 纳米）。\n'
     '    ②③都出自猎奇招股书自己的竞品参数表（第五节，1-1-146，第 10760–10784 行）——ficonTEC 两项都高约 2～2.5 倍。\n'
     '    刻度细、步子小，不等于每次都能扎准同一个点。\n',
     'KN007(11/19审阅C07):删去"最小运动增量50nm互证"错误表述,分清最小运动增量/分辨率/重复定位精度'),
    ('    锚: corpus/legacy-input/lieqi_prospectus.txt#主营业务·耦合设备段(1-1-92)',
     '    锚: corpus/legacy-input/lieqi_prospectus.txt#第五节·主营业务·耦合设备段(1-1-93,第8495行)', 'KN007:页码/行号纠正(引语在1-1-93,第8495行)'),
    ('    锚: corpus/legacy-input/lieqi_prospectus.txt#主营业务·老化测试设备段\n',
     '    锚: corpus/legacy-input/lieqi_prospectus.txt#第五节·主营业务·老化测试设备段(1-1-93,第8527行)\n', 'KN007:补节段/行号'),
    ('    说明: 印证"耦合设备核心=高精密运动平台"且给出档位量级(50nm),与猎奇耦合设备最小运动增量50nm互证\n',
     '    说明: 印证"耦合设备核心=高精密运动平台";官网"50 nm accuracy"为ficonTEC自述定位精度口径,与猎奇招股书竞品表所列ficonTEC重复精度±0.02µm(=±20nm)/分辨率5nm口径不同,更不得与招股书行业段"最小运动增量50nm"互证(2026-11-21按11/19审阅C07撤回原互证句)\n',
     'KN007:撤回错误互证句'),
    ('    说明: 电/光两个世界的精度档位差由设备原厂直接说出——支撑KN001"同名设备不同档"的通用判断法\n  录入日期: \'2026-07-26\'\n',
     '    说明: 电/光两个世界的精度档位差由设备原厂直接说出——支撑KN001"同名设备不同档"的通用判断法\n'
     '  - 谁: 猎奇智能（招股书竞品参数表，自述）\n'
     '    原话: X/Y/Z 轴重复精度——发行人 ±0.05µm、镭神技术 ±0.05µm（单模）/±0.3µm（多模）、FiconTEC ±0.02µm；XYZ 轴分辨率——发行人 10nm、镭神技术 未披露、FiconTEC 5nm（表格逐格转录）\n'
     '    出处: 招股说明书（申报稿）·第五节 业务与技术·光耦合设备关键参数指标对比（1-1-146）\n'
     '    锚型: local_file\n'
     '    锚: corpus/legacy-input/lieqi_prospectus.txt#第五节·竞品参数表(10760-10784行)\n'
     '    说明: 重复定位精度猎奇±50nm vs ficonTEC±20nm、分辨率10nm vs 5nm——ficonTEC两项均高约2～2.5倍;分辨率≠重复定位精度≠最小运动增量\n'
     '  - 谁: 招股书行业段（非猎奇自述）\n'
     '    原话: 部分国产厂商的贴片机加工精度已达±3µm，支持多芯片贴装；耦合设备已能达到最小运动增量 50nm\n'
     '    出处: 招股说明书（申报稿）·第五节 业务与技术·行业技术发展趋势（1-1-122）\n'
     '    锚型: local_file\n'
     '    锚: corpus/legacy-input/lieqi_prospectus.txt#第五节·行业技术趋势段(9759-9760行)\n'
     '    说明: “最小运动增量”只讲步长,且主语是“部分国产厂商”,不得当作猎奇或ficonTEC的定位精度\n'
     '  录入日期: \'2026-07-26\'\n',
     'KN007:新增竞品参数表与行业段两条local_file证据(注:两段均在第五节业务与技术,brief所写"第六节"按原文纠正)'),
]
edit_text('knowledge.yaml', kn_pairs, 'KN001/KN007')
kn = open('knowledge.yaml', encoding='utf-8').read()
if OLDQ55 in kn:
    n = kn.count(OLDQ55)
    kn2 = kn.replace(OLDQ55, '    原话: ' + NEWQ55 + '\n')
    open('knowledge.yaml', 'w', encoding='utf-8', newline='').write(kn2)
    log('knowledge.yaml', 'KN001/KN007', 'P055 ledger_ref 原话', OLDQ55.strip(), NEWQ55, f'P055引语随P204并入升级,{n}处ledger_ref原话同步')
lp = open('corpus/legacy-input/lieqi_prospectus.txt', encoding='utf-8').read().split('\n')
assert '最小运动增' in lp[9758] and '50nm' in lp[9759] and '50-100nm' in lp[9983] and '±0.05µm' in '\n'.join(lp[10759:10784])
assert '耦合是光模块封装工时最长' in lp[8494] and '老化测试是光模块生产的核心工序之一' in lp[8526]

# tree.yaml
tr = open('tree.yaml', encoding='utf-8').read()
tpairs = [
    ('  frozen_date: "2026-07-30"\n  count: 461\n', '  frozen_date: "2026-08-16"\n  count: 463\n', 'universe同步_frozen实有463家(v5补录2家)'),
    ('唯一代码不变)\n  行业口径', '唯一代码不变), v5=2家(2026-08-16,港股专项FIT+汇聚科技,用户批准)\n  行业口径', '补录v5记录'),
]
edit_text('tree.yaml', tpairs, 'universe')
tr = open('tree.yaml', encoding='utf-8').read()
new_lines = []
OBS = re.compile(r'^(  - \{名称: )(.*?)(, 市场: )(.*?)(, 理由: )(.*)\}\s*$')
in_obs = False
for line in tr.split('\n'):
    if line.startswith('observation_list:'):
        in_obs = True
    elif line.startswith('tree:'):
        in_obs = False
    m = OBS.match(line) if in_obs else None
    if m:
        name, mkt, why = m.group(2), m.group(4), m.group(6)
        if name == '索尔思(Source Photonics)' and '东山精密' not in mkt:
            mkt = '未上市(东山精密002384已完成收购索尔思光电并表,见points P130-P133;原为2023-11万通发展重大资产重组框架协议标的,未完成)'
        if name == '波若威光纤通讯' and '有限公司' not in mkt:
            mkt = "台股(上柜3163;points.csv公司名用全称'波若威光纤通讯有限公司',P264/P265上市标签=台股)"
        q = lambda s: ('"' + s.replace('"', '\\"') + '"') if (',' in s and not s.startswith('"')) else s
        nl = m.group(1) + name + m.group(3) + q(mkt) + m.group(5) + q(why) + '}'
        if nl != line:
            log('tree.yaml', name, 'observation_list', line, nl, '流式映射值含逗号致safe_load拆出垃圾键→加引号;索尔思/波若威注记更新')
        line = nl
    new_lines.append(line)
tr2 = '\n'.join(new_lines)
if tr2 != tr:
    open('tree.yaml', 'w', encoding='utf-8', newline='').write(tr2)
import yaml
ty = yaml.safe_load(open('tree.yaml', encoding='utf-8'))
assert ty['universe']['count'] == sum(1 for _ in csv.DictReader(open('corpus/_frozen.csv', encoding='utf-8-sig')))
for o in ty['observation_list']:
    assert set(o) == {'名称', '市场', '理由'}, o

# refs/entity-registry.yaml
REG = 'refs/entity-registry.yaml'
rg = open(REG, encoding='utf-8').read()
TAIL_START = '# 2026-07-25 天眼查对外投资数据修正(聚合库,pending_primary)\n- entity_id: LEGAL_ZHIHE\n'
if TAIL_START in rg:
    i = rg.index(TAIL_START)
    tail_old = rg[i:]
    head = rg[:i].rstrip('\n') + '\n'
    zhihe = (
        '\n'
        '    # ---- 2026-07-25 天眼查对外投资数据修正(聚合库,pending_primary);2026-11-21 Step1 由文件尾游离列表迁入本层 ----\n'
        '    - entity_id: LEGAL_ZHIHE\n'
        '      identity_type: legal_entity\n'
        '      canonical_name: 成都智禾光通\n'
        '      legal_name: 成都智禾光通科技有限公司\n'
        '      identifiers: {信用代码: 91510100MA69GLFW85}\n'
        '      aliases:\n'
        '        - {name: 成都智禾光通科技有限公司, effective_from: "", effective_to: ""}\n'
        '      rename_evidence: {status: pending, anchor: "", retrieved: "2026-07-25"}\n'
        '      related:\n'
        '        member_of: [GROUP_INNOLIGHT]\n'
        '        parent_of: []\n'
        '        possible_same_as: []\n'
        '        predecessor_of: []\n'
        '      identity_decision: distinct_legal_entities\n'
        '      registry_ruling: "旭创系:中际旭创100%全资,天眼查对外投资,2021-01设立(聚合库,pending_primary)"\n'
        '      registry_status: 待补证\n'
        '      source_ruling: ""\n'
        '      notes: "修正:此前\'承继原成都旭创且脱离旭创系\'推断后半句错误,智禾在系内"\n')
    anchor = '      notes: "顺丰速运之子/分支，法人分列；观察可走 branch scope"\n'
    assert head.count(anchor) == 1
    head = head.replace(anchor, anchor + zhihe)
    supp = (
        '\n'
        '# ====================== 补充解析层（2026-07-25 会话；2026-11-21 Step1 迁入合法顶层键） ======================\n'
        'supplemental_resolutions:\n'
        '  曾用名补充:\n'
        '    天孚通信: 苏州天孚精密陶瓷有限公司\n'
        '    中际旭创: "龙口中际电工机械/山东中际电工装备"\n'
        '  # 2026-07-25 标签解析会话:母公司/上市状态解析(专家知识+搜索验证)\n'
        '  母公司关系:\n'
        '    北京通美晶体: {parent: "AXT Inc(NASDAQ:AXTI)", 持股: "85.51%", 备注: "科创板IPO2026-07终止注册拟转港股", 来源: "新浪财经/证券时报2026-07-10"}\n'
        '    有研亿金新材料: {parent: "有研新材(600206)", 持股: 全资, 来源: 专家知识}\n'
        '    大阳日酸特殊气体: {parent: "日本酸素HD(TSE:4091)", 来源: 专家知识}\n'
        '    OharaQuartz: {parent: "Ohara Inc(TSE:5218)", 来源: 专家知识}\n'
        '    陕西兴化集团: {子公司上市: "兴化股份(002109)", 自身: "未上市国企(延长石油系)", 来源: 专家知识}\n'
        '    索尔思光电: {parent: "东山精密(002384)", 持股: 已完成收购并表, 备注: "原2023-11万通发展重大资产重组框架协议标的(未完成);points P200/P201为历史锚,并表后能力点见P130-P133", 来源: "东山精密2025年年度报告 https://static.cninfo.com.cn/finalpage/2026-04-22/1225139318.PDF", 日期: "2026-11-21"}\n'
        '  上市状态解析:\n'
        '    广东瑞谷光网: {status: 新三板837597, 来源: 新浪新三板页}\n'
        '    武汉昱升光电: {status: "未上市(IPO辅导中,海通证券,哈勃投资)", 来源: 搜索2026-07-25}\n'
        '    洛阳中超新材料: {status: "未上市(创业板IPO 2024-09撤回,曾挂新三板)", 来源: 证券时报}\n'
        '    芯思杰技术: {status: "待核(疑曾挂新三板838275,中信证券IPO文件存在,未见代码确认)", 保持: 未解析}\n'
        '    西安卫光气体: {status: 待核, 保持: 未解析}\n'
        '    联讯仪器: {status: "科创板已上市688808(2026-04-24上市,见2026半年报股份变动情况说明)", 保持: "points.csv P061上市标签暂保持未上市私企;待v6扩容将688808补录入corpus/_frozen.csv后同步切为A股", 来源: "https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF", 日期: "2026-11-21"}\n'
        '    索尔思光电: {status: "东山精密(002384)并表子公司(未单独上市)", 来源: "东山精密2025年年度报告", 日期: "2026-11-21"}\n'
        '  光迅科技控股结构: {parent: 中国信科集团, 持股: "直接2.1%+经烽火科技间接36.13%=38.23%", 来源: "大唐电信2025年报(互查矩阵命中)", 日期: "2026-07-25"}\n')
    newrg = head + supp
    open(REG, 'w', encoding='utf-8', newline='').write(newrg)
    log(REG, 'tail(409-431)', 'text', tail_old, zhihe + supp, 'yaml.parser.ParserError修复:LEGAL_ZHIHE迁入identity_layer.entities;其余游离条目迁入supplemental_resolutions顶层键,信息全保留并补联讯/索尔思注记')
reg = yaml.safe_load(open(REG, encoding='utf-8'))
assert any(e['entity_id'] == 'LEGAL_ZHIHE' for e in reg['identity_layer']['entities'])
assert len(os.listdir('refs')) <= 8

# knowledge.yaml 可解析 + ledger_ref 完整
kb = yaml.safe_load(open('knowledge.yaml', encoding='utf-8'))
pidset = {r['d']['point_id'] for r in P.rows}
eidset = {r['d']['edge_id'] for r in E.rows}
for k in kb['knowledge']:
    for e in k.get('证据') or []:
        if e.get('锚型') == 'ledger_ref':
            assert e['锚'] in pidset | eidset, (k['id'], e['锚'])
        if e.get('锚型') == 'local_file':
            assert os.path.exists(str(e['锚']).split('#')[0]), (k['id'], e['锚'])
    for p in k.get('关联点') or []:
        assert p in pidset, (k['id'], p)

# ================================================================ save + report
quote_drift = []
for L in (S, E, P, T, W, M):
    for r in L.rows:
        if r['dirty'] and r['raw'] is not None and L.ser(r['orig']) != r['raw']:
            quote_drift.append((L.path, r['d'][L.key]))
verify('改动行原始引号风格与QUOTE_MINIMAL一致性', '不一致行(其diff会多出引号差异)' if quote_drift else '全部一致', quote_drift)
saved = [L.path for L in (S, E, P, T, W, M) if L.save()]
if not CHANGES and os.path.exists(os.path.join(OUTDIR, 'ledger-changes.json')):
    print(json.dumps({'idempotent_rerun': True, 'change_count': 0, 'files_written_this_run': saved}, ensure_ascii=False))
    sys.exit(0)
summary = {
    'workpack': 'OPTICAL-STEP1-LEDGER-AND-GATES-20261121', 'agent': 'opus-ledger', 'run_date': TODAY,
    'files_written_this_run': saved, 'change_count': len(CHANGES),
    'by_file': dict(Counter(c['file'] for c in CHANGES)),
    'notes_for_gates': [
        'SE056 ASP写为"隐含混合ASP≈0.66元/只(即661.2元/千只;...)",ASP正则首个命中0.66元/只,单位列=千只(倍率1e3)',
        '同比反算: 15行经annual-2024原文行证实为直接披露→删"(同比反算)"保留B; SE089(2023值确系同比列反算)→C',
        '产能天顶检统一格式"产量X≤产能Y(产能利用率A%;销量/产能比B%;产销率C%),通过"; SE039利用率字段已写明产量',
        'ASP单位标签按单位列: 万个→元/个,台→元/台,台/套→元/台套,支/套→元/支套,片/个→元/片,万片→元/片,万支→元/支,万平方米→元/平方米,千克→元/千克',
        'points.csv corpus/qa/<code>/qa.jsonl#indexId=... 路径: 文件均存在,存在性校验须先剥离#后缀',
        'MC032新增(以太网+CPO 260亿,B); MC002降C; MC011改挂旭创年报一手URL保持B; MC009/MC010证据类型=内部证据账本可重算',
        'P061上市标签保持未上市私企(不扩_frozen);半年报原文上市日为2026-04-24(非brief所写2026-08)',
        'P036→P037, P204→P055 已合并删除; edges E137/E141/E165/E232 指针已改; triage/knowledge无悬空',
    ],
    'verifications': VERIFY, 'changes': CHANGES,
}
os.makedirs(OUTDIR, exist_ok=True)
json.dump(summary, open(os.path.join(OUTDIR, 'ledger-changes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: summary[k] for k in ('files_written_this_run', 'change_count', 'by_file')}, ensure_ascii=False, indent=1))
