"""Render a one-off review draft. Reads snapshots; never updates canonical ledgers."""
import csv
import html
import json
import re
from pathlib import Path
from repair_draft import apply_repairs, write_comparison
from product_views import module_cards, nonmodule_view, module_directory_view
from reader_layout import render_reader

BASE = Path(__file__).resolve().parent
U = '待提取：本稿尚未取得该环节专项资料；不能据此断言厂商未披露'
STAGES = ['主机电接口','PCB与电连接','电处理','驱动','发光与调制','载体与芯片互连','发射耦合','合波','外部光接口','分波','接收耦合','探测器','接收放大','控制','非易失存储','电源','时钟','无源电子件','热管理','总体封装']

def esc(s): return html.escape(str(s), quote=True)
def inline(s):
    s = esc(s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)

def markdown(src):
    lines=src.splitlines(); out=[]; para=[]; i=0
    def flush():
        if para: out.append('<p>'+inline(' '.join(para))+'</p>'); para.clear()
    while i<len(lines):
        line=lines[i]
        if line.startswith('|'):
            flush(); rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', x.replace(' ','')) for x in cells): rows.append(cells)
                i+=1
            out.append('<div class="scroll"><table><thead><tr>'+''.join('<th>'+inline(x)+'</th>' for x in rows[0])+'</tr></thead><tbody>')
            for row in rows[1:]: out.append('<tr>'+''.join('<td>'+inline(x)+'</td>' for x in row)+'</tr>')
            out.append('</tbody></table></div>'); continue
        if line.startswith('#'):
            flush(); n=min(len(line)-len(line.lstrip('#')),4); out.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>')
        elif not line.strip(): flush()
        else: para.append(line)
        i+=1
    flush(); return '\n'.join(out)

def status(value):
    if value.startswith('待提取'): return '未提取/待检索'
    if '不适用' in value: return '不适用（见适用条件）'
    if value.startswith('UNKNOWN') or value=='UNKNOWN': return 'UNKNOWN'
    if '暂仅线索' in value or '暂线索' in value: return '未核线索；采用情况UNKNOWN'
    if any(x in value for x in ['推导','推算','合并解释','推断','架构解释','结构解释','功能解释']): return '含工程推断，待型号规格确认'
    if any(x in value for x in ['UNKNOWN','未知','未披露','未列','未取得','冲突']): return '部分披露/有保留'
    return '厂商直接披露'

dom=json.loads((BASE/'domestic_verified.json').read_text())
ov=json.loads((BASE/'overseas_verified.json').read_text())
products=[]
for p in dom['products']:
    if 'OFC 2023' in p['product']: continue
    bucket='产品页/规格书'
    if '演示' in p['maturity'] or '展示' in p['maturity']: bucket='演示/发布配置'
    if 'family' in p['product'] or '产品族' in p['evidence_level']: bucket='产品族披露'
    sources=[dict(url=s['url'],title=s.get('location','厂商资料'),date=p['source_date']) for s in p['sources']]
    q=dict(company=p['company'],product=p['product'],model=p['sku'],bucket=bucket,
           electrical=p['electrical_lanes'],optical=p['optical_lanes'],dsp=p['dsp_architecture'],light=p['light_source_modulation'],
           mux=p['mux_demux'],receiver=p['pd_tia'],package=p['package_connector'],power=p.get('power',U),reach=p.get('reach','UNKNOWN'),
           stage=p['maturity'],sources=sources,boundary=p.get('unknowns',[]),source_map={})
    # A family sheet covers distinct parallel and wavelength-multiplexed products.
    if '800G DR8 / 2×FR4 LPO family' in p['product']:
        for variant,reach,optic in [('DR8','500m SMF','DR8 并行配置；资料给106.25Gbps PAM4/通道，完整通道对应仍需SKU规格'),('2×FR4','2km SMF','2×FR4 波分配置；资料给106.25Gbps PAM4/通道，完整通道对应仍需SKU规格')]:
            z=q.copy();z['product']='800G '+variant+' LPO（OFC 2024产品族）';z['reach']=reach;z['optical']=optic
            z['electrical']='资料给每通道106.25Gbps PAM4；该 '+variant+' 版本完整电通道表与SKU对应UNKNOWN'
            z['boundary']=['精确SKU','完整电通道对应','CW激光器规格','调制器','MUX实现','该版本连接器','量产']
            z['mux']='UNKNOWN：具体合分波器件、材料和集成位置未披露；两个产品的光路不合并'
            z['package']='OSFP / QSFP112-DD产品族；该配置精确形态与连接器待SKU确认'
            products.append(z)
    elif 'Gen2 1.6T' in p['product'] and 'SiPh/EML变体' in p['product']:
        for platform in ['EML','SiPh']:
            z=q.copy();z['product']=p['product'].replace('SiPh/EML变体',platform+'变体，完整后缀未知')
            z['light']=('EML发射版本；裸片型号及内部封装UNKNOWN' if platform=='EML' else 'SiPh发射版本；光源与具体调制器结构UNKNOWN')
            z['bucket']='产品族披露';products.append(z)
    else: products.append(q)

source_lookup={s['id']:s for s in ov['sources']}
for p in ov['products']:
    def val(k): return p[k]['text']
    keys={'electrical':'electrical_channels','optical':'optical_channels','dsp':'dsp_electrical_processing','light':'light_source_modulation','mux':'mux_demux','receiver':'pd_tia','package':'package_connection','power':'power','stage':'stage'}
    q={k:val(v) for k,v in keys.items()}
    for k,v in keys.items():
        if 'engineering_inference' in p[v]['status']: q[k]='[工程推断] '+q[k]
    q.update(company=p['company'],product=p['product'],model=p['model'],boundary=p['evidence_boundary'],reach='见光通道规格',source_map={},status_map={k:p[v]['status'] for k,v in keys.items()})
    distance=re.search(r'(500\s*m|2\s*km)',q['optical'])
    q['reach']=distance.group() if distance else 'UNKNOWN：本稿未取得无冲突的该配置距离规格'
    q['bucket']='冲突待澄清' if 'CONFLICT' in p['id'] else '演示/发布配置' if '演示' in p['object_level'] else '产品族披露' if '产品族' in p['object_level'] else '产品页/规格书'
    q['sources']=[dict(url=source_lookup[s]['url'],title=source_lookup[s]['title']+' / '+source_lookup[s]['anchor'],date=source_lookup[s]['published_date']) for s in p['source_ids']]
    for k,v in keys.items(): q['source_map'][k]=[source_lookup[s]['url'] for s in p[v]['source_ids']]
    products.append(q)

order=['中际','光迅','新易盛','Coherent','Lumentum','Source']
products.sort(key=lambda x:next((i for i,k in enumerate(order) if k in x['company']),99))
products=apply_repairs(products,U)
for p in products:
    p['company']={'新易盛':'新易盛 / Eoptolink','光迅科技':'光迅科技 / Accelink'}.get(p['company'],p['company'])
products.extend(module_cards())
write_comparison()

def stage_rows(p):
    vals=[U]*20; field=[None]*20
    def put(i,v,k=None): vals[i]=v;field[i]=k
    put(0,p['electrical'],'electrical');put(2,p['dsp'],'dsp');put(4,p['light'],'light')
    if any(t in p['dsp'] for t in ['Driver','driver','驱动']): put(3,p['dsp']+'（本项仅提取驱动相关披露）','dsp')
    put(7,p['mux'],'mux');put(9,p['mux'],'mux')
    put(8,p['optical']+'；距离：'+p['reach']+'；光纤接口见封装字段：'+p['package'],'package')
    put(11,p['receiver']+'（探测器与接收放大联合披露，未给出部分保持UNKNOWN）','receiver')
    put(12,p['receiver']+'（探测器与接收放大联合披露，未给出部分保持UNKNOWN）','receiver')
    cmis=re.search(r'CMIS\s*[\d.]+',p['package'])
    if cmis:
        put(13,'管理接口：'+cmis.group()+'；MCU型号和集成位置UNKNOWN','package')
    put(18,p['power']+'；具体散热器、材料与热设计UNKNOWN','power')
    put(19,p['package'],'package')
    ans=[]
    for i,v in enumerate(vals):
        urls=p['source_map'].get(field[i],[s['url'] for s in p['sources']]) if field[i] else []
        # The optical-interface row combines two explicitly linked source fields.
        if i==8: urls=list(dict.fromkeys(urls+p['source_map'].get('optical',[])))
        s=status(v)
        if p.get('compact') and field[i] and any('未回读' in z['title'] or '未重新核验' in z['title'] for z in p['sources']):
            s='既有摘录；原文未重核 / '+s
        if 'engineering_inference' in p.get('status_map',{}).get(field[i],'') or (i==8 and 'engineering_inference' in p.get('status_map',{}).get('optical','')):
            s='含工程推断，待型号规格确认'
        if i in p.get('extra_stages',{}):
            ex=p['extra_stages'][i];v=ex['value'];s=ex['status'];urls=ex['urls']
        ans.append(dict(stage=f'{i+1:02d} {STAGES[i]}',value=v,status=s,urls=urls))
    return ans

for i,p in enumerate(products,1):
    p['id']=f'R{i:02d}';p['stages']=stage_rows(p)
(BASE/'产品卡片快照.json').write_text(json.dumps(products,ensure_ascii=False,indent=2))

wide_fields=['记录ID','公司','产品对象层级','资料对象范围','产品配置','型号或版本','电通道','光通道','距离','电处理','发光与调制','合分波','接收','封装连接','功耗','采用或成熟阶段','来源','资料日期','核对日期','缺口或边界']
with (BASE/'产品路线总表.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(wide_fields)
    for p in products: w.writerow([p['id'],p['company'],('AOC有源光缆' if 'AOC' in p['product'] else '整模块（型号/产品族/演示版本见范围）'),p['bucket'],p['product'],p['model'],p['electrical'],p['optical'],p['reach'],p['dsp'],p['light'],p['mux'],p['receiver'],p['package'],p['power'],p['stage'],'\n'.join(s['url']+' | '+s['title'] for s in p['sources']),'\n'.join(s['date'] for s in p['sources']),'2026-10-03','；'.join(p['boundary'])])

long_fields=['记录ID','公司','产品配置','型号或版本','环节','主张或待补项','判断状态','来源定位','产品资料日期','核对日期','成熟阶段','对象边界']
with (BASE/'逐环节标注表.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(long_fields)
    for p in products:
        anchors={s['url']:s['title'] for s in p['sources']}
        for r in p['stages']: w.writerow([p['id'],p['company'],p['product'],p['model'],r['stage'],r['value'],r['status'],'\n'.join(u+' | '+anchors.get(u,'') for u in r['urls']),'；'.join(dict.fromkeys(s['date'] for s in p['sources'])),'2026-10-03',p['stage'],p['bucket']])

def refs(p):
    return '<ul class="sources">'+''.join('<li>'+('<a href="'+esc(s['url'])+'">'+esc(s['title'])+'</a>' if s['url'].startswith(('http://','https://')) else esc(s['title']+'：'+s['url']))+' · 资料日期：'+esc(s['date'])+'</li>' for s in p['sources'])+'</ul>'
def card(p):
    labels=[('electrical','主机电接口'),('optical','光通道'),('reach','距离'),('dsp','电处理'),('light','发光与调制'),('mux','合波与分波'),('receiver','探测与接收放大'),('package','封装与连接'),('power','功耗口径'),('stage','成熟阶段')]
    pending=[(key,label) for key,label in labels if p[key].startswith(('UNKNOWN','待提取'))]
    rows=''.join('<tr><th>'+label+'</th><td>'+esc(p[key])+'</td></tr>' for key,label in labels if (key,label) not in pending)
    if p.get('context_role'):rows='<tr><th>产品归属</th><td>'+esc(p['context_role'])+'</td></tr>'+rows
    if pending:rows+='<tr><th>本稿尚未确认</th><td>'+esc('、'.join(label for _,label in pending))+'。逐项原因与待补内容保留在下方20环节表及CSV中。</td></tr>'
    allrows=''.join('<tr><td>'+esc(r['stage'])+'</td><td>'+esc(r['value'])+'</td><td>'+esc(r['status'])+'</td></tr>' for r in p['stages'])
    return '<details class="card" id="'+p['id']+'" data-company="'+esc(p['company'])+'" data-bucket="'+esc(p['bucket'])+'"><summary><strong>'+esc(p['company'])+' · '+esc(p['product'])+'</strong><span class="summary-meta">'+p['id']+' · '+esc(p['model'])+' · '+esc(p['bucket'])+'</span></summary><div class="card-body"><table class="facts">'+rows+'</table><p class="boundary">适用边界：'+esc('；'.join(p['boundary']))+'</p><details class="source-detail"><summary>来源与资料日期</summary>'+refs(p)+'</details><details><summary>20项检查：信号功能、辅助功能与封装（不是20道工序）</summary><div class="scroll"><table><thead><tr><th>检查项</th><th>已知实现或待补</th><th>判断状态</th></tr></thead><tbody>'+allrows+'</tbody></table></div></details></div></details>'

intro=(BASE/'阅读说明.md').read_text(); appendix=(BASE/'其他公司与部件.md').read_text()
parts_html,parts_stats=nonmodule_view()
module_directory=module_directory_view(products)
catalog=(BASE/'全部公司目录片段.html').read_text(); comparison=(BASE/'对话与UNKNOWN纠错.md').read_text()
comparison_parts=comparison.split('### ')
comparison_html=markdown(comparison_parts[0])+''.join('<details class="correction"><summary>'+inline(part.split('\n',1)[0])+'</summary>'+markdown(part.split('\n',1)[1])+'</details>' for part in comparison_parts[1:])
coverage=json.loads((BASE/'公司覆盖统计.json').read_text())
companies=list(dict.fromkeys(p['company'] for p in products)); buckets=list(dict.fromkeys(p['bucket'] for p in products))
cards='\n'.join(card(p) for p in products)
counts={b:sum(p['bucket']==b for p in products) for b in buckets}
overview='<div class="scroll"><table><thead><tr><th>公司</th><th>本稿配置</th><th>阅读入口</th></tr></thead><tbody>'
for c in companies:
    ps=[p for p in products if p['company']==c]
    overview+='<tr><td>'+esc(c)+'</td><td>'+str(len(ps))+' 条，可能包括演示或产品族</td><td>'+ ' / '.join('<a href="#'+p['id']+'">'+p['id']+' '+esc(p['product'])+'</a>' for p in ps)+'</td></tr>'
overview+='</tbody></table></div>'
page=render_reader(products=products,parts_html=parts_html,catalog=catalog,comparison_html=comparison_html,module_directory=module_directory,cards=cards)
(BASE/'index.html').write_text(page)

def cell(s): return str(s).replace('|',' / ').replace('\n','；')
md=['# 公司产品各环节技术路线：目标 2 初稿','',f'核对日：2026-10-03。{len(companies)}个模块产品归属入口，{len(products)}条产品/版本配置。非模块产品另见《非模块产品与环节.csv》。产品页、产品族、演示及冲突条目分别标注，不等于独立SKU或量产产品数量。','', '先读具体产品，方法评估及缺口清单见后文。','']
for p in products:
    md+=['## '+p['id']+' '+p['company']+' · '+p['product'],'', '对象：'+p['bucket']+'。型号/版本：'+p['model'],'','| 环节 | 已披露内容或缺口 |','|---|---|']
    for k,l in [('electrical','电接口'),('optical','光通道'),('reach','距离'),('dsp','电处理'),('light','发光/调制'),('mux','合/分波'),('receiver','接收'),('package','封装连接'),('power','功耗'),('stage','成熟阶段')]: md+=['| '+l+' | '+cell(p[k])+' |']
    md+=['','其余内部环节的已知项与待提取原因详见《逐环节标注表.csv》；不能据上述路径补完整BOM。','', '边界：'+'；'.join(p['boundary']), '']
    for s in p['sources']:md+=['来源：['+cell(s['title'])+']('+s['url']+')；资料日期：'+s['date']+'；核对日期：2026-10-03。','']
md+=['---','',comparison,'',intro,'',appendix]
(BASE/'初稿.md').write_text('\n'.join(md))
print(json.dumps({'companies':len(companies),'configurations':len(products),'stage_rows':20*len(products),'nonmodule':parts_stats,'buckets':counts},ensure_ascii=False))
