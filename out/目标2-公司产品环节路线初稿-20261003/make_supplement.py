"""Save the three additional module-company catalog reads for this draft."""
import json
from pathlib import Path
B=Path(__file__).resolve().parent
def p(name,route,url,kind='模块',date='网页未标；2026-10-03取回',status='本轮原厂目录核对；目录登记不等于型号量产'):
    return dict(name=name,kind=kind,route=route,sources=[url],record_ids=['补充目录'],date=date,evidence_status=status)
linktel='https://disc.static.szse.cn/disc/disk03/finalpage/2026-04-29/eca187bd-8949-4a99-a323-fc77b30260b7.pdf'
hg='https://www.genuine-opto.com/dghfhdfghs/index.jhtml'
lig='https://www.ligent.com/products/products_module/16t/'
rows=[dict(company='联特科技',products=[
 p('800G OSFP：SR8；2FR4；2FR4 SiPho；2FR4 SiPho LPO；2LR4；DR4；2DR4；2DR4 TFLN','2025年报产品表印刷p12–13；SR8 850nm/100m；2FR4 CWDM/2km；2LR4 10km；DR4/2DR4 1311nm/500m。仅名称带SiPho/TFLN者直接识别平台，其余不可仅按规格猜EML。',linktel,date='2026-04-29（2025年报）'),
 p('800G QSFP-DD：2DR4；SR8','2DR4 1311nm/500m；SR8 850nm/50m；年报列名。',linktel,date='2026-04-29'),
 p('1.6T OSFP：2DR4；2FR4；2DR4 LRO；2FR4 LRO；2DR4 LPO','2DR4 1311nm/500m；2FR4 CWDM/2km；电处理变体按表名保留，不从LPO猜光平台。',linktel,date='2026-04-29'),
 p('ELSFP-VHP；ELSFP-UHP','外置光源产品；VHP 1311nm，UHP CWDM；具体内部芯片和功率待补。',linktel,kind='器件',date='2026-04-29'),
 p('1G–400G光模块；400G QSFP-DD SR8/FR4/LR4/ER4/DR4；QSFP112 FR4/SR4/LR4/DR4','年报列低速至400G各产品档位；此处为资料内类别，不穷尽历史/定制料号。',linktel,date='2026-04-29'),
 p('COC贴装、金丝键合、耦合、温循、老化、测试','年报印刷p14披露公司通用生产流程；不能据此认定每个800G/1.6T型号都同流程或设备。',linktel,kind='工艺能力',date='2026-04-29')],gaps=['各型号EML/SiPh/VCSEL具体光源、DSP、PD/TIA及制造工艺对应仍需规格書；通用流程不替代型号BOM。']),
 dict(company='华工科技',products=[
 p('华工正源 OSFP：800G 2FR4；SR8；DR8；1.6T/200G per lane','当前OSFP目录共4个入口；集团主体与实际产品发布方华工正源一起注明。',hg),
 p('1.6T DR8 OSFP AOC；1.6T DR8 OSFP（200G DSP）','页面按2024送样计划描述；自研SiPh，1310nm、212.5Gbps/通道；兼容TFLN调制器/量子点激光器不等于所有型号均采用。', 'https://www.genuine-opto.com/dghfhdfghs/451.jhtml',date='页面叙事为2024计划；本轮取回2026-10-03',status='历史送样计划/平台技术描述；当前量产需另证'),
 p('SFP/SFP+/TSFP+/SFP28；QSFP+/QSFP28/QSFP-DD；10G PON；光猫/路由器/物联网终端','当前产品导航大类；不同模块与终端层级分开，具体SKU待补。',hg,kind='模块/系统')],gaps=['旧网页送样计划与2025年报量产叙述须按日期区分；精确SKU及其芯片、内部连接、材料设备测试仍待对齐。']),
 dict(company='青岛海信宽带多媒体技术有限公司',products=[
 p('现官网入口说明：原海信宽带网站跳转Ligent/纳真科技','仅记录旧官网到当前官网的实际跳转，不据跳转推定每个法人、资产和历史产品都完全相同。','https://hbmt.hisense.com/',kind='身份入口'),
 p('1.6T OSFP DR4：LMS3981-PC+','8:4；500m；MPO12；32W；0–70°C；页面未列DSP和光平台。',lig),
 p('1.6T OSFP 2DR4：LMS3831S-PC+ / LMS3821S-PC2','8:8；500m；双MPO12；25W；IHS/RHS版本；页面未列光平台。',lig),
 p('1.6T OSFP 2FR4：LMS3836S-PC+ / LMS3826S-PC1','2km；双LC；26.5W；IHS/RHS；光源与DSP型号待补。',lig),
 p('1.6T OSFP 2DR4 LRO：LMS3831R-PC+ / LMS3831R-PC2','RTLR；500m；双MPO12；17W。',lig),
 p('1.6T OSFP 2FR4 LRO：LMS3836R-PC+ / LMS3836R-PC1','RTLR；2km；双LC；17.5W。',lig),
 p('1.6T OSFP 2LR4：LMS3838-PC1','8:8；10km；双LC；29W。',lig),
 p('800G OSFP/QSFP-DD：DR4/FR4/LR4；DR8/2DR4/2FR4/2LR4；VR8/SR8与AOC；LPO/LRO/TRO；800G ZR/ZR+','当前首页按200G与100G每光通道、并行与波分、线性/重定时、相干分组；不能把这些标签任意组合成全部已售配置。','https://www.ligent.com.cn/'),
 p('光芯片；400G/200G模块；PON；无线模块；光网络终端','当前网站导航与产品大类；光芯片具体EML/DFB/CW型号和各自成熟阶段需再对齐。','https://www.ligent.com.cn/',kind='芯片/模块/系统')],gaps=['旧海信公司原名保留；与纳真各法人/历史SKU归属未作法律主体合并。','具体模块光平台、驱动、PD/TIA、耦合、材料设备与量产阶段未由目录表证明。'])]
(B/'补充公司产品.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print(len(rows))
