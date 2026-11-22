"""Evidence-specific corrections for the one-off draft; no canonical writes."""
import json,csv
from pathlib import Path
B=Path(__file__).resolve().parent
def apply_repairs(products,U):
    d=json.loads((B/'domestic_gap_repair.json').read_text());o=json.loads((B/'overseas_gap_repair.json').read_text())
    os={s['id']:s for s in o['sources']}
    def ds(ids):return [dict(url=d['sources'][x]['url'],title=x+' '+d['sources'][x].get('anchor','原厂资料'),date=d['sources'][x].get('date','未标')) for x in ids]
    def ovs(ids):return [dict(url=os[x]['url'],title=x+' '+os[x]['title']+' / '+os[x]['anchor'],date=os[x]['published_date']) for x in ids]
    def extra(p,i,value,sources):
        status='所核来源未列该项' if value.startswith(('本PDF未列','所核产品页未列')) else '部分披露；具体边界见主张' if any(x in value for x in ['未知','未披露','未取得','未列','不能','冲突']) else '厂商直接披露'
        p.setdefault('extra_stages',{})[i]=dict(value=value,urls=[s['url'] for s in sources],status=status)
        for s in sources:
            if s['url'] not in [x['url'] for x in p['sources']]:p['sources'].append(s)
    for n,p in enumerate(products,1):
        # Preserve original R01–R28 identities; append new exact configurations after them.
        p['legacy_id']=f'R{n:02d}'
        if n in [1,2,3]:
            ss=ds(['I4' if n==3 else 'I1'])
            extra(p,13,'CMIS 5.x管理接口；MCU芯片及内部实现未取得',ss)
            extra(p,18,p['power']+'；0–70°C；散热结构与材料未取得',ss)
        if n==12:extra(p,13,'CMIS 5.0；DDMI数字诊断；MCU型号与存储器实现未取得',p['sources'])
        if n in [10,11]:
            extra(p,11,'PIN探测器；材料、颗数与芯片型号未披露',p['sources'])
            extra(p,12,'TIA阵列；具体通道组织与型号未披露',p['sources'])
        if n==12:
            extra(p,11,'本PDF未列PD结构/材料',p['sources'])
            extra(p,12,'TIA集成进DSP；具体型号未列',p['sources'])
        if n in [17,25,26]:
            extra(p,11,'PIN探测器；材料/芯片型号未披露',p['sources'])
            extra(p,12,'本PDF未列TIA具体型号与集成位置' if n==17 else '所核产品页未列TIA型号与集成位置',p['sources'])
        if n in [17,18,25,26]:
            extra(p,18,p['power']+'；封装/温区原规格：'+p['package']+'；具体热结构未披露',p['sources'])
        if n==17:
            extra(p,13,'I2C管理；CMIS 4.0（CMIS 5.x可选）；MCU型号未披露',ovs(['OG27']))
            extra(p,15,'外部供电3.3V；内部PMIC、调压和各支路用电未披露',ovs(['OG27']))
        if n in [22,23,24]:
            ss=ovs([{22:'OG11',23:'OG12',24:'OG13'}[n]])
            if n>22:
                p['light']='SiPh硅光平台＋1311nm CW DFB连续波激光器；颗数和调制器结构未披露'
                p['source_map']['light']=[s['url'] for s in ss]
                p['status_map']['light']='vendor_disclosed'
                p['boundary']=[x for x in p['boundary'] if not any(t in x for t in ['光源','CW激光','CW 激光'])]+['1.6T CW激光器颗数、调制器和内部器件型号待补']
            cmis='5.2' if n==22 else '5.3'
            extra(p,13,'CMIS '+cmis+'；RSSI与发射功率监测'+('、VDM' if n==22 else '')+'；MCU/内部存储型号未知',ss)
            temp={22:'0–70°C',23:'20–70°C',24:'20–60°C'}[n]
            extra(p,18,p['power']+'；温区'+temp+'；不能把温区不同的22W与16W当作同条件实测因果差',ss)
    def add(company,name,model,sources,**kw):
        p={x:U for x in ['electrical','optical','dsp','light','mux','receiver','package','power','reach']}
        p.update(company=company,product=name,model=model,bucket='产品页/规格书',stage='原厂产品页/规格书登记；不等于逐型号当前量产',boundary=['内部芯片厂商/型号、材料、设备与量产采用证据尚待补'],sources=sources,source_map={},status_map={})
        p.update(kw);products.append(p);return p
    p=add('新易盛','800G FR8','EOLO-168HG-02-P / V1.b',ds(['EFR']),electrical='8×106.25Gbps PAM4',optical='8个CWDM波长；单模光纤',dsp='双向PAM4 retimer ASIC；集成EML/modulator Driver',light='8路EML发射',mux='8波长波分功能；MUX/DEMUX具体工艺未披露',receiver='8个PD；两组4通道TIA；Features明确PIN；接收重定时',package='OSFP；LC',power='<16W（规格书条件）',reach='2km')
    extra(p,3,'EML/modulator Driver与PAM4 retimer ASIC集成；不等于激光器与CMOS在同一芯片',ds(['EFR']))
    extra(p,11,'8个PD；PIN结构，材料/型号未披露',ds(['EFR']));extra(p,12,'两组4通道TIA；具体型号未知',ds(['EFR']))
    for k in d['implementation_details']:
        src=ds(k['source']);n=k['product']
        light=k['photonic'] if 'photonic' in k else ('8路850nm VCSEL' if 'VR8' in n else '8路EML发射')
        mux='并行光路；无波分合分波需求（按所列并行配置作功能解释）' if '2FR4' not in n else '2个MUX＋2个DEMUX；具体器件工艺未披露'
        if 'DR8' in n:
            dsp='Driver与TIA集成在DSP中；DSP品牌/制程未列';driver='Driver集成DSP；具体型号未列';pd='本PDF未列探测器结构/材料';tia='TIA集成DSP；具体型号未列'
        elif 'VR8' in n:
            dsp='PAM4收发retimer；具体芯片未列';driver='两组4通道Driver；连接PAM4 retimer';pd='8个PIN/PD，材料未列';tia='两组4通道TIA，接收方向连接retimer'
        elif '2FR4' in n:
            dsp='双向PAM4 retimer；具体芯片未列';driver='8通道调制器Driver，与retimer集成';pd='8个PD；PIN结构，材料未列';tia='两组4通道TIA，接收方向连接retimer'
        else:
            dsp='双向PAM4 retimer；Driver/TIA集成DSP';driver='8通道Driver；集成DSP';pd='8个PD；结构/材料未列';tia='集成TIA；具体型号未列'
        p=add('新易盛',n,n,src,electrical=k['electrical'],optical=k['optical'],dsp=dsp,light=light,mux=mux,receiver=pd+'；'+tia,package='OSFP；'+k['connector'],power=k['power'],reach='2km' if '2FR4' in n else '10km' if ' LR' in n else '30m OM3/50m OM4' if 'VR8' in n else '500m')
        extra(p,3,driver,src);extra(p,11,pd,src);extra(p,12,tia,src)
    p=add('光迅科技','800G OSFP224 DR4','RTXM700-546',ds(['ADR4']),electrical='UNKNOWN：本轮所核型号页未列电通道，不能按封装名补写',dsp='UNKNOWN：所核型号页未列DSP实现',receiver='UNKNOWN：所核型号页未列PD/TIA',optical='4双工光通道；每通道212.5Gbps PAM4',light='SiPh modulator硅光调制器；激光器未列',mux='DR4并行配置；内部光路器件未披露',package='OSFP224；MPO12/APC',power='16W；0–70°C',reach='500m')
    p=add('光迅科技','1.6T OSFP224 2FR4','RTXM700-532',ds(['A2FR']),electrical='8×200G；1600GAUI-8',dsp='UNKNOWN：所核型号页未列DSP实现；不能套展会产品族3nm',receiver='UNKNOWN：所核型号页未列PD/TIA',optical='8×200G PAM4；CWDM',light='SiPh CWDM发射',mux='2FR4波分功能；器件实现未列',package='OSFP224；双duplex LC',power='26W；0–70°C',reach='2km')
    # Exact EML product; does not import a SiPh family route into this model.
    p=add('Coherent','800G 2FR4 EML','FTCE4717E1PCB',ovs(['OG02','OG03']),electrical='8×106.25Gbps PAM4；重定时',optical='8×100G CWDM',dsp='收发电接口重定时；DSP型号/工艺未知',light='8×100G CWDM EML',mux='两组四波长波分；MUX/DEMUX具体器件未知',receiver='PIN；TIA型号与集成位置未披露',package='OSFP；双LC',power='17W最大值；规格书15–70°C/网页0–70°C冲突',reach='2km')
    extra(p,15,'外部供电3.3V；内部电源管理器件未知',ovs(['OG03']))
    extra(p,11,'PIN探测器；材料/型号未列',ovs(['OG02','OG03']))
    extra(p,12,'所核产品页未列TIA具体型号与集成位置',ovs(['OG02','OG03']))
    p['boundary'].append('温区网页与规格书冲突保留；不合并不同版本')
    return products

def write_comparison():
    ds=json.loads((B/'domestic_gap_repair.json').read_text());os=json.loads((B/'overseas_gap_repair.json').read_text())
    sources={**ds['sources'],**{s['id']:s for s in os['sources']}}
    rows=ds['corrections']+os['claim_repairs']
    intro='''# 为什么前稿缺产品、内部实现又有大量 UNKNOWN

前稿存在整理错误。它把六家公司的一部分代表配置做成主稿，却没有先展开完整的资料内产品目录；还把八类环节固定初始化为空，再用“资料未披露”解释空值。旧28张卡的560条检查中，372条被标UNKNOWN，311条来自统一默认句，八类永不赋值的字段就占224条。这个数字反映抽取方式，不能用来判断厂商公开程度。

本次保留完整读过的原对话为问题线索，并逐项找回原厂依据。网页抽取遗漏不等于原厂没有资料；产品族路线已知也不应因为缺SKU而整项未知。以下原对话主张为便于核对的概括，不是逐字引语。

| 缺口类别 | 修订后的表达 | 例子 |
|---|---|---|
| 漏收产品、漏读规格 | 补回已披露内容，撤销对应未知 | 新易盛FR8、Coherent 2FR4 EML/PIN |
| 网页读取或动态内容漏取 | 标明提取方式问题并补原页内容 | Lumentum 1.6T CW DFB；光迅JS规格表 |
| 产品族已知、具体型号未对齐 | 同时列族级已知路线和型号级缺口 | Source 1.6T EML/SiPh/InP PIC变体 |
| 本稿未取得环节资料 | 标为未提取/待检索，不称厂商未披露 | PCB、载体、时钟等没有专项资料的项目 |
| 所核来源未写、或来源相互冲突 | 写清已读哪份资料、缺哪项或冲突何处 | 激光颗数、具体驱动料号；Source 2FR4距离冲突 |
| 功能不适用 | 不计成未知 | 铜缆AEC不涉及激光器或光电探测器 |

这次“补全”有两个可核对层次：当前三份公司清单的名称均有目录入口；六家公司新增核对的产品族和型号进入产品目录及逐项纠错表。它没有证明各公司所有定制SKU、全部内部BOM或所有量产状态已公开。

## 原对话与前稿逐项对照
'''
    out=[intro]
    for i,r in enumerate(rows,1):
        clean=lambda v:str(v).replace('|',' / ').replace('\n','；')
        out+=['### D'+str(i).zfill(2)+' '+r['company']+' · '+r['product_claim'],'','| 对照项 | 内容 |','|---|---|']
        for key,label in [('original_dialogue_claim','原对话主张'),('previous_gap','前稿遗漏/未知'),('verified_now','本次补回或修正'),('cause','差异原因'),('remaining','剩余缺口')]:out+=['| '+label+' | '+clean(r.get(key,''))+' |']
        out+=['','来源：'+'；'.join('['+sid+']('+sources[sid]['url']+')' for sid in r['source']),'']
    out+=['## 仍缺什么','', '当前资料只给公司角色或工艺能力的条目，仍缺具体产品目录；目录已有产品但没有规格书的，缺环节路线；环节路线已知的，可能仍缺器件型号、材料牌号、制造设备、测试条件和量产状态。各项放在公司目录与型号卡边界中，不再统一归为“内部实现未知”。','', '目标3仍须同速率、距离、温区、主机条件和误码率要求的对比资料。例如Lumentum的22W与16W是不同版本典型值，温区亦不同，不能直接把6W全部归因于TRO。目标4还需产品与实际工序、设备、材料、测试逐条关联；某设备商有相关设备，不等于已证明某模块采用它。']
    (B/'对话与UNKNOWN纠错.md').write_text('\n'.join(out))
    with (B/'对话主张差异表.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['公司','产品/主张','原对话主张概括','前稿缺口','本次核对','原因','剩余缺口','来源'])
        for r in rows:w.writerow([r.get(k,'') for k in ['company','product_claim','original_dialogue_claim','previous_gap','verified_now','cause','remaining']]+['\n'.join(sources[s]['url'] for s in r['source'])])
    return len(rows)
if __name__=='__main__':print(write_comparison())
