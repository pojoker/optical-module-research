"""One-off extraction view of the existing company coverage. Does not edit ledgers."""
import csv, json, html
from pathlib import Path
B=Path(__file__).resolve().parent
R=B.parents[1]
def read(n): return list(csv.DictReader((R/n).open(encoding='utf-8-sig')))
def j(n): return json.loads((B/n).read_text())
def dump(n,v): (B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
def urls(v):
    return list(dict.fromkeys((x.get('url','') if isinstance(x,dict) else x) for x in v if x))

items=[]
for g in range(1,4): items+=j(f'company_group{g}_products.json')
points=read('points.csv'); uni=read('calls/universe.csv'); watch=read('calls/watch_entities.csv')
sources={x['source_id']:x for x in read('calls/sources.csv')}
disclosures={x['disclosure_id']:x for x in read('calls/disclosures.csv')}
byname={x['company']:x for x in items}
for row in items:
    row['input_refs']=['points:'+r['point_id'] for r in points if r['公司']==row['company']]
    row['identity_note']='保留现有资料原名；集团、子公司和历史名称不据名称相似自动合并。'
    row['source_scope']='现有 points 原文摘录；本轮未逐篇重新打开原始文件'
    for p in row['products']:
        p.setdefault('evidence_status',row.get('evidence_status','现有摘录支持'))
        p.setdefault('date','见对应 points 检索/判定日期；不等于产品发布日期')

# Explicit same-name translations used only for this reader view. Acquisition targets remain separate.
alias={'AVGO':'博通(Broadcom)','AAOI':'Applied Optoelectronics(AAOI)','MRVL':'Marvell','FN':'Fabrinet',
       'WATCH_SOURCEPHOTONICS':'索尔思(Source Photonics)','WATCH_SAMCO':'Samco',
       'AIXA':'AIXTRON','VECO':'Veeco','OXIG':'Oxford Instruments'}
pool_products={
'COHR':('激光器；光电器件；高速光模块；光路交换机（OCS）','芯片/器件/模块/系统'),
'LITE':('激光器；光通信器件；800G/1.6T光模块；光路交换','芯片/器件/模块/系统'),
'AAOI':('800G光模块；1.6T光模块线索；InP激光器','模块/芯片'),
'FN':('光通信精密制造服务；800G模块制造项目；CPO项目','制造服务'),
'NVDA':('Spectrum-X网络平台；AI集群互连需求','系统/客户应用'),
'ANET':('数据中心交换系统；800GbE部署；1.6T未来计划','系统'),
'CSCO':('交换系统；Silicon One芯片；1.6T OSFP；800G LPO；相干光学','系统/芯片/模块'),
'META':('AI数据中心、服务器和网络部署；无自售光器件产品证据','客户应用'),
'AVGO':('交换ASIC；SerDes；光DSP；EML；CPO平台','芯片/平台'),
'MRVL':('光DSP；硅光平台；交换芯片；定制互连','芯片/平台'),
'NOK':('光线路系统；800G ZR/ZR+相干可插拔模块；下一代光DSP线索','系统/模块/芯片'),
'CIEN':('WaveLogic 6 Extreme；WaveLogic 6 Nano 800G；Vesta 200 6.4T CPX；Hyper-Rail','系统/模块/光引擎'),
'MTSI':('高速调制器驱动器；TIA；CW激光器；448G PAM4调制器驱动器','芯片/器件'),
'CRDO':('SerDes；AEC；光DSP；ZeroFlap光模块；Cardinal 1.6T DSP；ALC；OmniConnect gearbox','芯片/模块/有源线缆'),
'MXL':('200G TIA；PAM4 DSP','芯片'),
'JBL':('光模块设计制造服务；1.6T可插拔产品线索','制造服务/模块'),
'VECO':('InP MOCVD设备；离子束设备；LUMINA+ MOCVD','设备'),
'FORM':('硅光/CPO晶圆级测试与自动对准平台','设备'),
'AXTI':('InP晶圆衬底；GaAs衬底；Ge衬底','材料'),
'GFS':('硅光代工；SiGe代工；CPO工艺平台','制造服务/工艺能力'),
'TSEM':('硅光代工；模拟混合信号代工','制造服务/工艺能力'),
'SMTC':('200G/lane PMD；TIA；驱动器','芯片'),
'AIXA':('InP/GaAs MOCVD设备','设备'),
'ASMPT':('光子芯片贴装、耦合、键合和CPO装配设备','设备'),
'SOI':('Photonics-SOI材料平台','材料'),
'SUMITOMO':('InP激光器；FAU光纤阵列；光纤连接','芯片/器件'),
'FURUKAWA':('光纤；激光器；数据中心光连接','材料/器件'),
'POET':('晶圆级光引擎；1.6T光引擎；EOI光引擎','光引擎'),
'SIVERS':('DFB激光器；CW激光器','芯片'),
'SANM':('光子设计、封装和制造服务；云AI基础设施交付','制造服务'),
'CLS':('AI网络硬件；高速交换系统；制造交付服务','系统/制造服务'),
'MYCRONIC':('光通信芯片贴装机（die bonder）','设备'),
'OXIG':('化合物半导体等离子处理设备','设备'),
'VIAV':('1.6T测试与验证设备','设备'),
'ADTN':('800G低功耗模块线索；开放光传输系统','模块/系统'),
'WIWYNN':('机架级AI系统；CPO互连需求','系统/客户应用'),
'GLW':('光纤；无源光连接','材料/器件'),
'LWLG':('电光聚合物调制材料与调制器','材料/器件'),
'SMOP':('开放光传输系统；数据中心互联系统','系统'),
'WATCH_IQE':('化合物半导体外延供应','材料/制造服务'),
'WATCH_DUST':('硅光产品平台线索','芯片/平台'),
'WATCH_IIVI':('历史主体；能力并入Coherent索引','历史身份'),
'WATCH_FINISAR':('历史通信光器件/模块能力','历史身份'),
'WATCH_OCLARO':('历史光通信器件能力','历史身份'),
'WATCH_NEOPHOTONICS':('历史高速光器件能力','历史身份'),
'WATCH_CLOUDLIGHT':('历史高速数据中心模块能力','历史身份'),
'WATCH_ACACIA':('相干光学；DSP；PIC','历史身份/芯片/模块'),
'WATCH_INPHI':('高速电光互连平台','历史身份/芯片'),
'WATCH_POLARITON':('等离激元调制器技术','器件/工艺能力'),
'WATCH_INFINERA':('光网络系统；光子半导体','历史身份/系统/芯片'),
'WATCH_NUBIS':('低功耗光电互连','历史身份/光引擎'),
'WATCH_HYPERLUME':('microLED光互连','历史身份/光引擎'),
'WATCH_FUJIKURA':('光纤；高密度光连接','材料/器件'),
'WATCH_MELCO':('EML激光器','芯片'),
'WATCH_ASE':('硅光封装；OSAT封装测试服务','制造服务'),
'WATCH_SUSS':('永久键合；异质集成设备','设备'),
'WATCH_SAMCO':('InP刻蚀与沉积设备','设备'),
'WATCH_KEYS':('224G与1.6T验证设备','设备'),
'WATCH_ACCTON':('800G LPO应用系统；光交换系统','系统'),
'WATCH_FREIBERGER':('GaAs与InP衬底线索','材料'),
'WATCH_NTTID':('相干DSP','芯片'),
'WATCH_FUJITSUOC':('相干收发器；光器件','模块/器件'),
'WATCH_OPENLIGHT':('集成激光器硅光平台及PDK','工艺平台'),
'WATCH_SICOYA':('硅光芯片；收发组件','芯片/器件'),
'WATCH_SCINTIL':('异质集成硅光芯片平台','芯片/工艺平台'),
'WATCH_XSCAPE':('FalconX多波长光引擎','光引擎'),
'WATCH_AVICENA':('microLED光互连评估套件','光引擎/评估套件'),
'WATCH_AYAR':('光I/O芯粒；UCIe光芯粒；外置光源','芯片/器件'),
'WATCH_LIGHTMATTER':('Passage光互连平台','光互连平台'),
'WATCH_RANOVUS':('Odin CPO光引擎','光引擎'),
'WATCH_SOURCEPHOTONICS':('800G和1.6T光模块','模块'),
'WATCH_MOLEX':('CPO光连接；光路交换平台','器件/系统'),
'WATCH_SENKO':('MPC系列高密度光连接器','器件'),
'WATCH_TERAMOUNT':('PhotonicPlug光纤连接产品','器件'),
'WATCH_FICONTEC':('光子装配和测试自动化设备','设备'),
'WATCH_PI':('光子自动对准系统','设备'),
'WATCH_EVG':('die-to-wafer键合系统','设备'),
'WATCH_EXFO':('FTBx-88800系列800G网络协议测试平台','设备'),
'WATCH_GOOGL':('云与数据中心带宽需求；无自售光器件证据','客户应用'),
'WATCH_MSFT':('AI云与数据中心容量需求；无自售光器件证据','客户应用'),
'WATCH_AMZN':('AWS基础设施需求；无自售光器件证据','客户应用'),
'WATCH_ORCL':('云基础设施容量需求；无自售光器件证据','客户应用'),
'WATCH_AMD':('Helios机架级AI平台；互连需求','系统/客户应用'),
'WATCH_ENNOSTAR':('化合物半导体业务；LUMINA+设备使用/验收方','客户应用'),
'WATCH_LUMILENS':('EOI光引擎采购和联合开发应用；当前材料无具体自售型号','客户应用'),
'WATCH_MCHP':('高速Ethernet PHY；PCIe/CXL retimer','芯片')}

pool_index={}
# Keep pool reasons broad; concrete branded products below have their own claim anchors.
pool_products.update({
 'COHR':('光器件；高速光模块','器件/模块'),
 'LITE':('激光器；光通信器件','芯片/器件'),
 'AAOI':('800G和1.6T光模块','模块'),
 'FN':('光通信制造交付服务','制造服务'),
 'ANET':('数据中心交换网络','系统'),
 'NOK':('光传输；相干可插拔；AI数据中心网络系统','模块/系统'),
 'META':('超大规模数据中心部署与资本开支需求；本条不是产品目录','客户应用'),
 'WATCH_IQE':('MACOM外延供应安排的具名对手方；具体材料体系待核','供应角色线索'),
 'WATCH_DUST':('硅光收购对手方；具体产品名待核','技术角色线索'),
 'WATCH_SCINTIL':('异质集成硅光路线；具体产品名待核','工艺能力线索'),
 'NVDA':('AI集群架构与互连需求','系统/客户应用'),
 'CSCO':('交换系统及光学产品','系统/模块'),
 'CIEN':('相干光系统；DCI；CPO光引擎','系统/光引擎'),
 'MTSI':('高速驱动器；TIA；CW激光器；光电模拟器件','芯片/器件'),
 'CRDO':('SerDes；AEC；光DSP；高速光收发器平台','芯片/模块/有源线缆'),
 'VECO':('InP MOCVD；离子束设备','设备'),
 'POET':('晶圆级光引擎；1.6T产品线索','光引擎'),
 'WATCH_XSCAPE':('多波长光引擎','光引擎'),
 'WATCH_SENKO':('高密度光连接产品','器件'),
 'WATCH_EXFO':('800G实验室与制造测试产品','设备'),
 'WATCH_AYAR':('光I/O芯粒；外置光源','芯片/器件'),
 'WATCH_AMD':('机架级平台与互连需求','系统/客户应用'),
 'WATCH_ENNOSTAR':('化合物半导体设备验收/资格的具名对手方；当前记录无具体自售产品','客户应用'),
 'WATCH_LUMILENS':('光引擎采购和联合开发方；当前记录无具体自售产品','客户应用')})
for r in uni+watch:
    id=r.get('company_id') or r['entity_id'];name=r.get('company_name') or r['entity_name'];key=alias.get(id,name)
    if key not in byname:
        item=dict(company=key,products=[],role=r.get('role','观察对象'),gaps=[],evidence_status='公司池/观察对象中的产品线索，非本轮产品规格核验',input_refs=[],identity_note=r.get('notes',''),source_scope='calls公司池/观察对象，及已摘录主张')
        items.append(item);byname[key]=item
    item=byname[key];pool_index[id]=item
    item['input_refs'].append(('calls/universe:' if 'company_id' in r else 'calls/watch:')+id)
    src=[r['source_ref']] if r.get('source_ref') else []
    if not src:src=['calls/universe.csv：'+id+'，纳入理由；无逐产品原文锚']
    name,kind=pool_products[id]
    item['products'].append(dict(name='[线索] '+name,kind=kind,route=r['inclusion_reason'],record_ids=[id],sources=src,evidence_status='现有公司池/观察理由线索；尚未逐产品核验',date='公司池资料日期未标；不冒充产品发布日期'))
    item['gaps'].append('公司池纳入理由不能替代产品说明书；需继续对齐型号、配置和阶段。')

# Preserve actual extracted claims independently of the weaker pool-level leads.
claim_selection={'CL001':'800G光模块','CL008':'1.6T OSFP可插拔模块','CL012':'800G LPO可插拔模块','CL010':'Silicon One交换芯片','CL017':'搭载Lumentum激光器的NVIDIA 1.6T 2DR4演示模块','CL018':'4×400G EML可插拔演示','CL019':'800mW SHP激光器','CL020':'200G EML激光器','CL030':'EML/CW激光器/光电二极管','CL031':'OCS光路交换机','CL034':'800G scale-out模块制造项目','CL035':'CPO制造项目','CL037':'800GbE系统部署','CL040':'Spectrum-X网络平台','CL051':'800G ZR/ZR+相干可插拔','CL065':'WaveLogic 6 Nano 800G相干可插拔','CL074':'ZeroFlap/ALC/OmniConnect产品族'}
for c in read('calls/claims.csv'):
    if c['claim_id'] not in claim_selection:continue
    s=sources[c['source_id']];item=pool_index[s['company_id']]
    item['products'].append(dict(name=claim_selection[c['claim_id']],kind='具体产品/项目主张',route=c['summary'],record_ids=[c['claim_id'],c['source_id']],sources=[s['url']],evidence_status='现有已审主张摘录；'+c['statement_type']+'；非本轮重新核验',date=s['published_date'],anchor=c['anchor'],quote=c['quote']))
event_selection={'ECL006':'WaveLogic 6 Extreme 1.6T单光通道试验','ECL007':'448G PAM4调制器驱动器','ECL008':'800G 2DR4 ZeroFlap光模块','ECL012':'Vesta 200 6.4T CPX光引擎','ECL017':'ZeroFlap产品族','ECL018':'Cardinal 1.6T光DSP','ECL024':'InP晶圆衬底','ECL027':'LUMINA+ MOCVD','ECL031':'EOI光引擎'}
for c in read('calls/event_claims.csv'):
    if c['event_claim_id'] not in event_selection:continue
    s=disclosures[c['disclosure_id']];item=pool_index[c['claimant_entity_id']]
    item['products'].append(dict(name=event_selection[c['event_claim_id']],kind='具体产品/项目主张',route=c['summary'],record_ids=[c['event_claim_id'],c['disclosure_id']],sources=[s['canonical_url']],evidence_status='现有事件摘录；'+c['statement_kind']+'；'+c['notes'],date=s['published_at'],anchor=c['anchor'],quote=c['quote']))

# Freshly inspected six-company catalogs sit alongside the complete legacy extracts.
for fname in ['domestic_gap_repair.json','overseas_gap_repair.json']:
    data=j(fname)
    # The two research files retain their independent formats; normalized additions are supplied below.
    if fname.startswith('domestic'):
        for c in data['catalog']:
            key=next(x for x in byname if x in c['company'])
            item=byname[key]
            for f in c['families']:
                ss=[data['sources'][x] for x in f['sources']]
                item['products'].append(dict(name=f.get('rate','')+' '+f.get('package','')+'：'+'；'.join(f['variants']),kind='模块',route='；'.join(f.get(x,'') for x in ['route','electrical','stage'] if f.get(x)),record_ids=f['sources'],sources=[s['url'] for s in ss],evidence_status='本轮核对原厂目录/发布资料；SKU、演示与族按正文区分',date='；'.join(s.get('date','未标') for s in ss)))
            if c.get('other_categories'):
                ss=[data['sources'][x] for x in c['sources']]
                item['products'].append(dict(name=c['other_categories'],kind='其他产品族',route='详规与型号仍需逐产品补齐',record_ids=c['sources'],sources=[s['url'] for s in ss],evidence_status='本轮核对目录/年报分类',date='；'.join(s.get('date','未标') for s in ss)))
            for f in c.get('older_official_cache',[]):
                item['products'].append(dict(name='；'.join(f['items']),kind='历史/缓存产品配置',route=f.get('family_route',f.get('boundary','')),record_ids=f['sources'],sources=[data['sources'][x]['url'] for x in f['sources']],evidence_status='原厂搜索缓存支持；当前页面取回失败',date='缓存日期见研究记录'))
            for f in c.get('historical_release_families',[]):
                item['products'].append(dict(name=f['rate']+' '+'；'.join(f['variants']),kind='历史演示/产品族',route=f['route'],record_ids=f['sources'],sources=[data['sources'][x]['url'] for x in f['sources']],evidence_status='历史原厂发布稿；不自动对应现型号',date='；'.join(data['sources'][x]['date'] for x in f['sources'])))
            for f in c.get('ordering_tables',[]):
                s=data['sources'][f['source']]
                for r in f['rows']:
                    item['products'].append(dict(name=r[0]+' '+r[1],kind='目录型号标签',route=f['package']+'；'+'；'.join(r[2:]),record_ids=[f['source']],sources=[s['url']],evidence_status='本轮原厂订货表；型号模式不是全部完整订货后缀',date=s['date']))
        for f in data['implementation_details']:
            item=byname['新易盛'];ss=[data['sources'][x] for x in f['source']]
            item['products'].append(dict(name=f['product'],kind='模块',route='；'.join(f.get(x,'') for x in ['electrical','optical','dsp_driver_tia','photonic','connector','power'] if f.get(x)),record_ids=f['source'],sources=[s['url'] for s in ss],evidence_status='本轮核对原厂PDF的内部实现；型号别名冲突保留',date='；'.join(s['date'] for s in ss)))
        s=data['sources']['EL']
        byname['新易盛']['products'].append(dict(name='800G LPO：MMF VCSEL；SMF SiPh/EML/TFLN四种光学路线',kind='模块产品族',route='无DSP/CDR；OSFP/QSFP-DD800；逐路线完整型号未对齐',record_ids=['EL'],sources=[s['url']],evidence_status='本轮浏览器核对2023原厂发布稿；历史演示不等于当前量产',date=s['date']))
    else:
        sl={x['id']:x for x in data['sources']}
        for c in data['catalogues']:
            item=byname['索尔思(Source Photonics)' if c['company']=='Source Photonics' else c['company']]
            for f in c['families']+c['other_categories']:
                if f.get('id')=='CF08':
                    f=dict(f,name='1.6T SiPh/CW平台与FRO/TRO名单（各配置未配对）',optical_route='SiPh＋高功率InP CW是族级平台名单；不是每款FRO/TRO型号的组合证明')
                ss=[sl[x] for x in f['source']]
                weak=(c['company']=='Lumentum' and f['name'].startswith('EML/')) or (c['company']=='Source Photonics' and f['name'].startswith('400G/'))
                item['products'].append(dict(name=('[导航线索] ' if weak else '')+f['name']+' '+f.get('model',''),kind='多对象导航线索' if weak else f['kind'],route='；'.join(f.get(x,'') for x in ['optical_route','electrical_route','route','spec','stage','boundary'] if f.get(x)),record_ids=f['source'],sources=[s['url'] for s in ss],evidence_status='导航/类别线索；现有锚未逐类证明，需补产品原文' if weak else '本轮核对原厂资料；型号/产品族/演示按正文区分',date='；'.join(s['published_date'] for s in ss)))
            for f in c.get('directory_sku_labels',[])+c.get('directory_1600_sku_labels',[]):
                item['products'].append(dict(name=f['label']+' '+f.get('family',''),kind='目录型号标签',route=f['form']+'；'+f['reach'],record_ids=f['source'],sources=[sl[x]['url'] for x in f['source']],evidence_status=f['status'],date='页面未标'))
            item['gaps']+=c['gaps']

for c in j('补充公司产品.json'):
    key=c['company'];item=byname[key]
    item['products']+=c['products'];item['gaps']+=c.get('gaps',[])

for p in j('nonmodule_verified_additions.json')+j('nonmodule_existing_additions.json'):
    item=byname[p['company']]
    item['products'].append({k:v for k,v in p.items() if k not in ['company','gap']})
    if p.get('gap'):item['gaps'].append(p['name']+'：'+p['gap'])

from product_views import load_module_expansion, company_key, config_kind
for c in load_module_expansion():
    key=company_key(c['company'])
    if key not in byname:raise ValueError('新增模块归属须在当前公司目录对齐：'+key)
    item=byname[key]
    for p in c.get('configs',[]):
        src=p.get('sources',[])
        item['products'].append(dict(name=p['product']+' '+p.get('model',''),kind=config_kind(p),route='；'.join(p.get(k,'') for k in ['electrical','optical','dsp','light','mux','receiver','package','reach','power','stage'] if p.get(k))+'；对象边界：'+'；'.join(p.get('boundary',[])),record_ids=['产品扩展:'+c['company']],sources=[s['url'] for s in src],evidence_status=p.get('bucket','产品族/型号；具体阶段见主张')+'；'+c.get('evidence_scope','本轮归集；原文复核范围见来源标题')+'；来源定位：'+'；'.join(s['title'] for s in src),date='；'.join(s.get('date','未标') for s in src)))
    item['gaps']+=c.get('gaps',[])

for i,item in enumerate(items,1):
    item['id']=f'C{i:03d}'
    item['gaps']=list(dict.fromkeys(item.get('gaps',[])))
    for p in item['products']:
        p['sources']=urls(p.get('sources',[]));p.setdefault('route','');p.setdefault('record_ids',[])
    item['products_count']=len(item['products'])
    if any('本轮' in p.get('evidence_status','') and ('核对' in p.get('evidence_status','') or '浏览器' in p.get('evidence_status','')) for p in item['products']):
        item['source_scope']='既有摘录与本轮补核可能并存；以每行证据标签为准，不相互覆盖。'
dump('全部公司产品清单.json',items)
with (B/'全部公司产品清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['公司记录','公司原名/展示名','角色','产品/材料/器件/设备/服务','对象类型','路线或既有主张','证据状态','原记录','原始来源','资料日期','核对说明','逐公司缺口'])
    for c in items:
        for p in c['products'] or [dict(name='现有材料没有具体产品名',kind='待补',route='',record_ids=c['input_refs'],sources=[],evidence_status=c['evidence_status'])]:
            w.writerow([c['id'],c['company'],c['role'],p['name'],p['kind'],p['route'],p.get('evidence_status',c['evidence_status']),'；'.join(p['record_ids']),'\n'.join(p['sources']),p.get('date','未标'),p.get('evidence_status',c['source_scope']),'；'.join(c['gaps'])])
with (B/'公司名称覆盖核对.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['输入范围','原名','输入ID','读者目录名','目录ID'])
    for n in dict.fromkeys(x['公司'] for x in points): w.writerow(['points',n,'；'.join(x['point_id'] for x in points if x['公司']==n),n,byname[n]['id']])
    for r in uni+watch:
        id=r.get('company_id') or r['entity_id'];c=pool_index[id]
        w.writerow(['calls/universe' if 'company_id' in r else 'calls/watch',r.get('company_name') or r['entity_name'],id,c['company'],c['id']])

esc=lambda s:html.escape(str(s),quote=True)
parts=['<h2>全部公司：现有材料中有哪些产品？</h2>',f'<p>已逐名覆盖 points 的155个原名、calls 公司池39条、观察对象47条，共241条输入名称记录，合并明确同名/译名后显示{len(items)}个目录入口。集团、子公司、历史名称仍可能并存，入口数不是独立经营企业数。范围是上述当前资料中出现的光通信相关产品与能力，不声称穷尽各公司全部在售SKU。</p>', '<p>先查公司再看产品。材料、制造服务、设备、下游客户和历史身份各自标明；公司池线索与已核原厂产品分列，不能把名单中的纳入理由读成已核产品事实。</p>', '<div class="filters"><input id="catalog-query" aria-label="搜索全部公司产品" placeholder="搜索全部公司、产品、材料或设备"><select id="catalog-kind" aria-label="筛选产品类别"><option value="">全部类别</option>'+''.join('<option>'+x+'</option>' for x in ['材料','芯片','器件','模块','光引擎','设备','制造服务','系统','客户应用','历史身份'])+'</select></div><p id="catalog-count"></p>']
md=['# 全部公司产品清单','',f'核对日2026-10-03。241条输入名称记录 → {len(items)}个读者入口；不是去重企业数或完整在售SKU数。详见公司名称覆盖核对.csv。','']
for c in items:
    body=''
    md+=['## '+c['id']+' '+c['company'],'',c['role']+'。'+c['source_scope'],'','| 产品或能力 | 类型 | 技术路线/主张 | 证据与来源 |','|---|---|---|---|']
    for p in c['products']:
        status=p.get('evidence_status',c['evidence_status']);links=' '.join(('<a href="'+esc(u)+'">来源'+str(n)+'</a>') if u.startswith(('https://','http://')) else esc(u) for n,u in enumerate(p['sources'],1))
        body+='<tr><td>'+esc(p['name'])+'</td><td>'+esc(p['kind'])+'</td><td>'+esc(p['route'])+'</td><td>'+esc(status)+'<br>'+links+'<br>'+esc(' / '.join(p['record_ids']))+'<br>'+esc(p.get('date','未标'))+'</td></tr>'
        clean=lambda x:str(x).replace('|',' / ').replace('\n','；')
        md+=['| '+' | '.join(clean(x) for x in [p['name'],p['kind'],p['route'],status+' '+' '.join(('[来源'+str(n)+']('+u+')') if u.startswith(('https://','http://')) else u for n,u in enumerate(p['sources'],1))])+' |']
    gaps='；'.join(c['gaps']) or '需继续建立具体产品—环节—实现—来源的对应；没有逐项证据的部分不推定。'
    if not body:body='<tr><td colspan="4">现有引语未含可提取的具体产品名；该公司保留在目录中，缺口见下方。</td></tr>'
    kinds='；'.join(p['kind'] for p in c['products'])
    parts+=['<details class="company-catalog" data-kinds="'+esc(kinds)+'" id="'+c['id']+'"><summary>'+esc(c['company'])+' · '+esc(c['role'])+' · '+str(len(c['products']))+'组摘录</summary><p>'+esc(c['identity_note'])+'</p><div class="scroll"><table><thead><tr><th>产品或能力</th><th>对象</th><th>路线/主张</th><th>证据与来源</th></tr></thead><tbody>'+body+'</tbody></table></div><p class="boundary">待补：'+esc(gaps)+'</p></details>']
    md+=['','待补：'+gaps,'']
(B/'全部公司目录片段.html').write_text('\n'.join(parts));(B/'全部公司产品清单.md').write_text('\n'.join(md))
dump('公司覆盖统计.json',dict(points_original_names=155,universe_records=39,watch_records=47,input_names=241,display_entries=len(items),product_excerpt_groups=sum(len(c['products']) for c in items),missing_input_names=[],boundary='名称归集完整性，不等于产品SKU、技术环节或最新状态已全部核验'))
print(json.dumps(j('公司覆盖统计.json'),ensure_ascii=False))
