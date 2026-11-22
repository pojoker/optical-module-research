"""Reader sections for the same one-off draft; never writes research ledgers."""
import csv,html,json
from pathlib import Path
B=Path(__file__).resolve().parent
esc=lambda s:html.escape(str(s),quote=True)
def company_key(name):
    aliases={'华工正源':'华工科技','华工科技 / 华工正源':'华工科技','华工科技/华工正源':'华工科技','华工正源 / 华工科技':'华工科技',
        '海信宽带 / Ligent':'青岛海信宽带多媒体技术有限公司','海信宽带（现官网Ligent/纳真科技）':'青岛海信宽带多媒体技术有限公司',
        '海信宽带/Ligent':'青岛海信宽带多媒体技术有限公司','Ligent':'青岛海信宽带多媒体技术有限公司',
        '青岛海信宽带多媒体技术有限公司（旧资料名；当前官网入口Ligent/纳真）':'青岛海信宽带多媒体技术有限公司',
        '剑桥科技 / CIG':'剑桥科技',
        'AAOI':'Applied Optoelectronics(AAOI)','Applied Optoelectronics':'Applied Optoelectronics(AAOI)',
        '泰科电子':'泰科电子(含关联方)','TE Connectivity':'泰科电子(含关联方)',
        '四川光恒':'四川光恒通信技术有限公司','武汉钧恒':'武汉钧恒科技有限公司',
        '通宇通讯 / 四川光为':'通宇通讯','通宇通讯（参股四川光为）':'通宇通讯'}
    return aliases.get(name,name)
def load_module_expansion():
    rows=[]
    for n in ['domestic_other_modules.json','domestic_module_families.json','overseas_other_modules.json']:
        p=B/n
        if p.exists():rows+=json.loads(p.read_text())['companies']
    return rows
def config_kind(p):
    if '光引擎' in p['bucket']:return '光引擎'
    if '制造服务' in p['bucket']:return '制造服务'
    return '模块'
def module_cards():
    ans=[]
    for c in load_module_expansion():
        for p in c.get('configs',[]):
            if config_kind(p)!='模块':continue
            q=dict(p);q['company']=company_key(c['company']);q['source_map']={};q['status_map']={};q['compact']=True
            q['context_role']=c.get('role','');q['boundary']=p.get('boundary',[])
            for k in ['electrical','optical','dsp','light','mux','receiver','package','power','reach']:
                q.setdefault(k,'待提取：本稿尚未取得该产品的此项资料')
            q.setdefault('model','产品族；型号未取得');q.setdefault('bucket','现有资料产品族');q.setdefault('stage','所核资料未给逐型号阶段')
            original_bucket=q['bucket'];q['boundary']=['资料对象：'+original_bucket]+q['boundary']
            if any('未回读' in s['title'] or '现有points' in s['title'] for s in q['sources']):q['bucket']='既有摘录/产品族'
            elif '具体' in original_bucket:q['bucket']='产品页/规格书'
            elif '历史送样' in original_bucket:q['bucket']='历史计划/待更新'
            elif '演示' in original_bucket or '发布' in original_bucket:q['bucket']='演示/发布配置'
            else:q['bucket']='产品族披露'
            ans.append(q)
    return ans
def source_links(sources):
    return '；'.join('<a href="'+esc(s)+'">来源'+str(i)+'</a>' if s.startswith(('https://','http://')) else esc(s) for i,s in enumerate(sources,1))
def nonmodule_view():
    allrows=json.loads((B/'全部公司产品清单.json').read_text());records=[]
    cats=['材料','芯片','器件','光引擎','设备','工艺与制造服务']
    kinds={'材料':'材料','芯片':'芯片','器件':'器件','光引擎':'光引擎','设备':'设备','工艺':'工艺与制造服务','制造服务':'工艺与制造服务'}
    # Classification is scoped to the exact quoted record, never inferred from a company's name.
    record_layers={'CL010':'芯片','CL019':'器件','CL020':'器件','CL030':'芯片/器件',
        'CL034':'制造服务','CL035':'制造服务','ECL007':'芯片','ECL012':'光引擎',
        'ECL018':'芯片','ECL024':'材料','ECL027':'设备','ECL031':'光引擎'}
    mixed={
        ('德科立','P087'):('800G相干模块器件','器件'),
        ('青岛海信宽带多媒体技术有限公司','补充目录'):('光芯片（同一来源另列模块和终端）','芯片'),
        ('Coherent','COHR'):('[线索] 光器件','器件'),
        ('Ciena','CIEN'):('[线索] CPO光引擎','光引擎'),
        ('Credo','CRDO'):('[线索] SerDes、光DSP与AEC有源线缆','芯片/器件'),
        ('Credo','CL074'):('ALC有源线缆、OmniConnect gearbox（与ZeroFlap同列于爬坡计划）','芯片/器件'),
        ('Jabil','JBL'):('[线索] 光模块设计制造服务','制造服务'),
        ('Celestica','CLS'):('[线索] 制造交付服务','制造服务'),
        ('Fujitsu Optical Components','WATCH_FUJITSUOC'):('[线索] 光器件','器件'),
        ('Molex','WATCH_MOLEX'):('[线索] CPO光连接','器件')}
    for c in allrows:
        for p in c['products']:
            p=dict(p);kind=p['kind'];original_kind=kind
            if kind in ['其他产品族','多对象导航线索']:
                navigation={
                    '光迅科技':('光纤放大器；AWG/VMUX/WDM/VOA/OPM/WSS/OTDR；光连接器；OSA','器件'),
                    '新易盛':('OSA光组件（TOSA发射组件、ROSA接收组件）','器件'),
                    'Lumentum':('[导航线索] EML/DML/CW激光器、ELS外置光源、相干调制器与传输组件','器件'),
                    '索尔思(Source Photonics)':('[导航线索] 400G/lambda TOSA、ELSFP外置光源','器件')}
                if c['company'] in navigation:p['name'],kind=navigation[c['company']]
            for rid in p['record_ids']:
                if rid in record_layers:kind=record_layers[rid]
                if (c['company'],rid) in mixed:
                    p['name'],kind=mixed[(c['company'],rid)]
                    p['route']='非模块对象见标题；同一来源的上下文（包含其他对象，不自动归到本对象）：'+p['route']
            if any(s in kind for s in ['模块','系统','历史身份','客户应用']):continue
            layers=list(dict.fromkeys(v for k,v in kinds.items() if k in kind))
            if not layers:continue
            row=dict(p,company=c['company'],company_id=c['id'],layer=' / '.join(layers),layers=layers,original_kind=original_kind,kind=kind,gaps='；'.join(c.get('gaps',[])))
            row['evidence_status']=p.get('evidence_status',c['evidence_status'])
            row['lead']=p['name'].startswith(('[线索]','[导航线索]')) or '线索' in kind or '线索' in row['evidence_status']
            records.append(row)
    counts={x:sum(x in r['layers'] for r in records) for x in cats}
    head='''<h2>材料、芯片、器件与设备：它们本身也是产品</h2>
<p>资料库并不只有光模块成品。衬底、激光器芯片、DSP、TIA、AWG、封装件和生产测试设备都有各自的产品信息。以下按实际对象展示已知名称和路线；工艺能力、制造服务与待核线索另作标记。这里不套整模块的20环节表。</p>
<div class="layer-intro"><p><strong>材料：</strong>如InP衬底、工艺气体、覆铜板，重点看组成、工艺和适用条件。</p><p><strong>芯片与器件：</strong>如DSP、激光器、TIA、AWG和封装件，重点看实现的功能、接口和集成位置。</p><p><strong>设备与制造服务：</strong>重点看加工/测试对象、执行动作和可配置工艺；提供设备不等于已证明某模块厂使用它。</p></div>
<p>来源标签保留原有深度：本轮原厂核对、既有引语、公司池线索。列表也保留相邻用途和在研项目，具体光通信用途以每行说明为准。跨层级的摘录可在多个筛选中出现，但仍是同一组资料；层级计数不能相加当作独立SKU或量产产品数。</p>'''
    buttons='<div class="layer-buttons">'+''.join('<button type="button" data-layer-jump="'+x+'">'+x+' <small>'+str(counts[x])+'组</small></button>' for x in cats)+'</div>'
    filters='<div class="filters"><input id="part-query" aria-label="搜索非模块产品" placeholder="公司、产品或路线，例如 InP、TIA、AWG、TESTLINE"><select id="part-layer" aria-label="非模块产品层级"><option value="">全部层级</option>'+''.join('<option>'+x+'</option>' for x in cats)+'</select><label><input type="checkbox" id="part-leads" checked>包括待核线索</label></div><p id="part-count"></p>'
    body=[]
    fields=['公司','产品','层级','原对象类型','技术路线或资料描述','证据状态','来源','资料日期','原记录','缺口']
    with (B/'非模块产品与环节.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(fields)
        for i,p in enumerate(records,1):
            w.writerow([p['company'],p['name'],p['layer'],p['kind'],p['route'],p['evidence_status'],'\n'.join(p['sources']),p.get('date','未标'),'；'.join(p['record_ids']),p['gaps']])
            body.append('<details class="part-card" id="PVIEW'+str(i)+'" data-layer="'+esc(p['layer'])+'" data-lead="'+str(p['lead']).lower()+'"><summary>'+esc(p['company'])+' · '+esc(p['name'])+'</summary><div class="part-body"><p class="eyebrow">'+esc(p['layer']+' / '+p['kind'])+'</p><p><strong>实现与用途：</strong>'+esc(p['route'])+'</p><p><strong>证据范围：</strong>'+esc(p['evidence_status'])+'</p><p class="sources">'+source_links(p['sources'])+'<br>资料日期：'+esc(p.get('date','未标'))+'；记录：'+esc(' / '.join(p['record_ids']))+'</p><p class="boundary">该公司仍待补：'+esc(p['gaps'])+'</p><a href="#'+p['company_id']+'">查看公司全部资料</a></div></details>')
    (B/'非模块产品视图.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    stats={'rows':len(records),'layers':counts,'companies':len({p['company'] for p in records}),'lead_rows':sum(p['lead'] for p in records)}
    (B/'产品层级视图统计.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
    return head+buttons+filters+'<div class="part-list">'+''.join(body)+'</div>',stats
def module_directory_view(products):
    rows=load_module_expansion()
    out=['<h2>新增模块公司：先看产品范围与归属</h2><p>数通、相干、电信接入和无线模块分开阅读。制造服务、外购模块、参股公司产品与自有产品各自说明；公司级目录不自动证明每个型号量产。</p>','<div class="scroll"><table><thead><tr><th>公司/归属</th><th>现有资料中的模块产品范围</th><th>本稿展开与边界</th></tr></thead><tbody>']
    for c in rows:
        cat=c.get('catalog',[])
        text='；'.join(x if isinstance(x,str) else x.get('name',json.dumps(x,ensure_ascii=False)) for x in cat)
        nm=sum(config_kind(p)=='模块' for p in c.get('configs',[]));nc=len(c.get('configs',[]))-nm
        first=next((p['id'] for p in products if p['company']==company_key(c['company'])),None)
        link=('<a href="#'+first+'">查看模块卡片</a>') if first else '<a href="#components">查看制造服务</a>'
        out.append('<tr><td>'+esc(company_key(c['company']))+'<br><small>'+esc(c.get('role',''))+'</small><br>'+link+'</td><td>'+esc(text)+'</td><td>'+str(nm)+'条模块配置/族'+('；'+str(nc)+'条光引擎/服务在非模块区' if nc else '')+'；'+esc('；'.join(c.get('gaps',[])))+'</td></tr>')
    return ''.join(out)+'</tbody></table></div>'
VIEW_SCRIPT='''
const parts=[...document.querySelectorAll('.part-card')],pq=document.querySelector('#part-query'),pl=document.querySelector('#part-layer'),pt=document.querySelector('#part-leads');
function partFilter(){let n=0;for(const x of parts){const show=(!pl.value||x.dataset.layer.split(' / ').includes(pl.value))&&(pt.checked||x.dataset.lead!=='true')&&x.textContent.toLowerCase().includes(pq.value.toLowerCase());x.hidden=!show;if(show)n++;}document.querySelector('#part-count').textContent=`显示 ${n} / ${parts.length} 组资料；不是独立SKU数。`;}
[pq,pl,pt].forEach(x=>x.addEventListener('input',partFilter));document.querySelectorAll('[data-layer-jump]').forEach(x=>x.addEventListener('click',()=>{pl.value=x.dataset.layerJump;pq.value='';partFilter();}));partFilter();
'''
