from pathlib import Path
from html import escape
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / '光模块知识体系/光模块基础知识-图文合并版-10图105问.html'
soup = BeautifulSoup(ORIGINAL.read_text(), 'html.parser')
old = '../光模块知识体系/' + ORIGINAL.name
sources = {}
for a in soup.select('a.qa-cite'):
    label = a.get_text(' ', strip=True).split(']')[0].strip('[')
    if label.isdigit():
        sources.setdefault(int(label), (a.get('href'), a.get('title') or a.get_text(' ',strip=True)))

def cite(*nums):
    return ' '.join(f'<a class="cite" href="#source-{n}">[{n}]</a>' for n in nums)

def origin(*nums):
    return '<p class="origin">取材于合并版：' + ' · '.join(f'<a href="{old}#qa-{n}">Q{n:02d}</a>' for n in nums) + '</p>'

def table(head, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+h+'</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+c+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'

sources.update({
38:('https://www.hamamatsu.com/us/en/product/optical-sensors/apd.html','Hamamatsu：Avalanche photodiodes (APDs)，内部增益与配套电路'),
37:('https://www.intel.com/content/www/us/en/newsroom/news/intel-unveils-first-integrated-optical-io-chiplet.html','Intel：集成光学 I/O 芯粒演示，2024 年'),
3:('https://www.lpo-msa.org/home/faqs.html','LPO MSA：Frequently Asked Questions'),
10:('https://www.marvell.com/company/newsroom/marvell-introduces-1-6-tbps-lpo-chipset.html','Marvell：1.6 Tbps LPO TIA 与驱动器芯片组，2024-12-10'),
34:('https://www.coherent.com/news/glossary/vcsel-array','Coherent：What is a VCSEL Array?'),
35:('https://www.coherent.com/news/press-releases/coherent-introduces-100g-pam4-vcsel-and-photodiode-arrays','Coherent：100G PAM4 VCSEL 与探测器阵列，2023-02-28'),
36:('https://blogs.cisco.com/sp/cisco-demonstrates-co-packaged-optics-cpo-system-at-ofc-2023','Cisco：OFC 2023 共封装光学系统演示，2023-03-07'),
28:('https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/silicon-photonics-wp.html','Cisco：Silicon Photonics in Pluggable Optics，2021-12-06'),
29:('https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/solution-overview-c22-743387.html','Cisco：Single-Lambda 100G，2023-02-04，What is PAM4'),
30:('https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/400g-qsfp-transceiver-modules-ds.html','Cisco：400G QSFP 产品规格，DR4 / FR4'),
32:('https://blogs.cisco.com/sp/fiberopticspt2singlemultifiber','Cisco：Single-Mode Fiber vs. Multi-Mode Fiber'),
33:('https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/21_HPE/featured-products-and-technologies/photodiodes-exposed-unlocking-the-characteristics-of-these-crucial-sensors.pdf','Hamamatsu：Photodiodes，工作原理')
})
sources.update({39: ('https://www.coherent.com/resources/white-paper/networking/swdm-lowest-total-cost-for-40g-100g-wp.pdf', 'Coherent：SWDM，40G/100G企业数据中心白皮书，版权2023'), 40: ('https://www.intel.com/content/www/us/en/ark/products/series/96621/intel-silicon-photonics-pluggable-optical-transceivers.html', 'Intel：硅光可插拔光模块产品目录'), 41: ('https://www.intel.com/content/dam/www/public/us/en/documents/product-briefs/silicon-photonics-the-key-to-data-centre-connectivity-robert-blum.pdf', 'Robert Blum / Intel：Silicon Photonics—The Key to Data Center Connectivity，2017 Q3'), 42: ('https://www.ficontec.com/applications/', 'ficonTEC：装配应用与阵列耦合能力')})
sections=[(HERE/'content.html').read_text().replace('{{old}}',old)]
used=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42]
source_notes={
7:'恢复历史Q16：OSFP Rev5.0，2022-10-02，尺寸与散热要求；不推断加工方法。',
9:'恢复历史Q06：Ho等1995年PIN论文，Device structure；本轮未重新获取全文，沿用原问答的定位，不当作现代量产工艺。',
11:'2026-09-28复核Eurocircuits公开制造步骤；普通多层PCB实例。',
12:'2026-09-28复核Corning OEM-039-AEN，2019-09-03，第1、2、5页；FAU实例。',
18:'恢复历史Q23引用的100G-DR-LPO固定版本测试要求；不声称为最新标准。',
19:'恢复历史Q15：Newport App Note6，测光、运动与固定的实例，不指定参考模块设备。',
20:'2026-09-28复核Oxford公开入口正文：p-mesa刻蚀与氧化孔径；未取得需表单下载的白皮书全文。',
21:'恢复历史Q09：Coherent 2024-03-25研发公告，光刻孔径方向；不是当前量产确认。',
24:'2026-09-28复核Edmund Asphere Manufacturing Methods与Metrology；非球面制造示例。',

38:'本轮复核产品原理与 APD modules 段：内部增益、高压供电与温度补偿。仅解释探测选择，不把目录波长范围或灵敏度宣传泛化为所有高速通信接收器。',
37:'本轮复核 How It Works：硅光 PIC 包含片上激光器与放大器；仅说明光源集成可以不同。原文将该 OCI 定义为原型，不代表参考模块 BOM 或当前部署状态。',
3:'2026-09-16 复核：LPO 定义、主机均衡、线性路径和系统条件；不采用旧 FAQ 中的标准发布时间预测。',
10:'2026-09-16 复核：LPO 仍需 TIA 与驱动器，支持短且可控的主机通道；不据此推算通用节电比例。',
34:'2026-09-16 新增：表面出光、直接电流调制、阵列与耦合；限原理解释，不作为后文模块 BOM。',
35:'2026-09-16 新增：八单元 VCSEL 与配套探测器阵列的短距器件实例，不是后文 EML 模块的器件清单。',
36:'2026-09-16 新增：2023 年 Cisco 演示的共封装、远置光源、供电散热安排；不泛化为全部 CPO 实现或当前商用规模。',
1:'沿用前次已核验产品表：仅支持具体型号公开参数。',
2:'沿用 Lumentum 器件说明：支持 DFB 与 EAM 的集成和作用，不指定参考型号供应商。',
4:'本次重读 Device fabrication：2010 年 1.55 μm EML 实例，不是参考模块量产工艺。',
5:'本次复核 AIM Low-Loss PDK：平台可用结构，不是某只 PIC 的完整配方。',
6:'沿用已核验的 March Rev B2：第 1 页产品与接口，第 3–4 页电光参数；年份未标。',
8:'本次补读 ASML 制造说明：光刻与刻蚀的分工，仅支持通用工艺解释。',
15:'沿用已复核的 2019 年 Vol.168，印刷页 5–6，光学系统与结构。',
22:'合并版已有的 ficonTEC 能力说明：支持对准原理，不证明本型号采用其设备。',
23:'沿用已复核的 2025-12-08 Product Overview：POET 厂商披露，限该发射 PIC，非量产良率证明。',
26:'合并版的 TI 原理电路，300 kHz 示例只解释电流转电压，不用于高速器件选型。',
27:'合并版的 ASMPT 工序分类；解释固晶和互连，不指定参考产品工艺。',
28:'本轮新增；Basics of silicon photonics 与 Manufacturing efficiency。仅取工作路径和制造动机，不泛化厂商成本优势。',
29:'本轮新增；What is PAM4 段，支持四档、每符号两位与噪声权衡。',
30:'本轮新增；用产品规格说明并行与波分的纤芯/连接差别，不把距离差异单独归因于合波。',
32:'本轮新增；支持短距多模光纤与 VCSEL 的关联，不穷举路线。',
33:'本轮新增；光电转换的一般原理，文中硅光电二极管图不代表参考模块 PIN 的材料结构。'}
source_notes.update({39: '2026-09-28复核第2–3页：VCSEL、四波长、MUX/DEMUX及多模双纤结构；不采纳成本排名。', 40: '2026-09-28复核PSM4与CWDM4型号存在；不据目录状态声称当前在售或部署。', 41: '2026-09-28复核第1页四激光器、调制器与MUX集成，第2页PSM4并行说明；历史实例，不作为800G模块结构。', 42: '2026-09-28复核光纤阵列与激光阵列耦合能力；VCSEL实例位于汽车应用说明，仅用于设备能力，不证明通信产品采用其设备。'})
refs=''.join(f'<li id="source-{n}"><a href="{escape(sources[n][0],quote=True)}">[{n}] {escape(sources[n][1])}</a><p>{source_notes[n]}</p></li>' for n in used)
sections.append(f'''<section id="evidence"><p class="eyebrow">资料、原题与尚未知晓的部分</p><h2>继续查证时，从哪里接上？</h2><p>本页沿组成、连接、制造和路线变化这些原始问题展开。已有材料取自<a href="{old}">10 图 105 问合并版</a>；补充资料用于解释原理及其原因，来源编号延续合并版。</p><aside class="unknown"><strong>本页仍未回答的产品细节</strong><p>Coherent 参考模块的完整 BOM、实际连接工艺，以及两种合波实现的同条件成本与良率，仍缺直接资料。这些资料决定了能否列出具体产品的设备清单、比较经济性。正文采用注明对象的器件实例解释原理，功能图和工艺示例不代表该型号的完整拆解。</p></aside><details><summary>来源与适用范围 · {len(used)} 项</summary><ol class="sources">{refs}</ol></details><details><summary>本轮补充记录</summary><p>2026-09-14：新增 Cisco 硅光白皮书、PAM4 说明、DR4/FR4 产品规格、单模/多模介绍和 Hamamatsu 光电探测原理；复核 AIM 平台结构、NTT 制造段及 ASML 工艺说明。2026-09-15：补入功能分解与本例功能分配，将 PAM4 移到具体产品之后，沿用已核验资料。2026-09-16：调整段落、措辞和衔接，随后展开 VCSEL、LPO、CPO 的功能实现对照，补入 Coherent、LPO MSA、Marvell 与 Cisco 一手资料。随后据 Cisco 与 Intel 原始资料区分硅光平台和具体发射结构，新增来源 [37]。本轮将 03 按 02 的五项功能重组，补入探测器选择及 TIA 衔接，新增 Hamamatsu 来源 [38]。本轮补明硅光方案实物与片内结构，04沿五步填写产品选择，05聚焦连接，06与07明确同类制造和路线扩展。 2026-09-28：补充路线层级、参考产品导读、实现选择条件及路线到制造的对应；沿用已引用技术来源，借鉴 Cisco 同视角比较和逐段解释的写法。本轮按三条页面注释把硅光实物介绍并入调制路线、补充搭配规则，并恢复历史Q06–Q16的器件与设备内容。历史来源的恢复不等于全部重新验证，具体范围见各来源说明。本页包含产品事实、原理解释、历史工艺实例与条件推论；没有新增 canonical 条目。2026-09-28再次按注释补入VCSEL与硅光的并行/波分实例，并按六种实现展开装配对象和设备任务，新增来源[39]–[42]。</p></details></section>''')

css='''.three-options{grid-template-columns:repeat(3,minmax(0,1fr))!important}.three-options article{padding:18px}.three-options .stack{overflow-wrap:anywhere}@media(max-width:1100px){.three-options{grid-template-columns:1fr!important}}.levels{display:flex;justify-content:center;gap:30px;padding:20px;background:#fff;border-radius:8px;align-items:flex-end}.levels div{display:flex;flex-direction:column;align-items:center;gap:8px}.levels i{display:block;width:45px;background:#548470;border-radius:4px 4px 0 0}.levels small{font-size:12px}.lanes{font-size:14px;color:#427660;line-height:2.3}.steps{padding-left:26px}.steps li{padding-left:10px}.steps h3{margin-bottom:8px}.steps p{margin-top:0}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:26px}body{margin:0;background:#f6f5ef;color:#223530;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.85}a{color:#246a59;text-underline-offset:4px}a:hover{color:#a4592d}aside.nav{position:fixed;inset:0 auto 0 0;width:240px;padding:42px 25px;border-right:1px solid #d8ded5;background:#eef1e9;overflow:auto}.brand{font-size:22px;font-weight:700;line-height:1.5;margin-bottom:28px}nav a{display:block;padding:10px 12px;text-decoration:none;border-radius:6px;font-size:14px}nav a.active{background:#d7e3d8;font-weight:700}.nav small{display:block;margin-top:30px;color:#66766d}main{margin-left:240px;max-width:1250px;padding:55px 64px 80px}.hero{padding:24px 0 45px;border-bottom:2px solid #315d4c}.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;font-weight:700;color:#597566}h1{font-family:Georgia,"Songti SC",serif;font-size:48px;line-height:1.35;letter-spacing:-1px;margin:16px 0 24px}h2{font-size:29px;line-height:1.5;margin:8px 0 20px}h3{font-size:20px;margin-top:30px}.lead,.intro{font-size:19px;color:#52665b}.hero .lead{max-width:750px}.pill{display:inline-block;padding:3px 10px;background:#e6ece2;border-radius:4px;font-size:12px;color:#4b6855}section{padding:42px 0;border-bottom:1px solid #d8ded5}.flow{display:flex;align-items:center;justify-content:center;gap:9px;flex-wrap:wrap;background:white;border:1px solid #d9e1d7;border-radius:10px;padding:25px 16px;margin:25px 0 12px}.flow b{padding:12px;border:1px solid #809c8c;border-radius:6px;background:#e5eee6;font-size:14px;text-align:center}.flow .inferred{border:1px dashed #9a9e95;background:#fafaf6}.flow small{display:block;color:#62766a;font-weight:400;font-size:12px}.table-wrap{overflow-x:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px;min-width:560px}th,td{text-align:left;vertical-align:top;padding:14px 16px;border-bottom:1px solid #d9dfd6}th{background:#e8ede3;font-weight:600}td:first-child{font-weight:600;width:23%}tr:nth-child(even){background:#f0f2eb}.unknown{background:#f4ecdc;border-left:3px solid #b18a4d;padding:18px 22px;margin:25px 0}.unknown p{margin:8px 0 0}.bridge{padding:17px 0;color:#37634f;font-weight:600}.origin,.caption,.evidence{font-size:13px;color:#647269}.origin{margin:15px 0}.cite{font-size:12px;text-decoration:none;white-space:nowrap}.product{background:#e8eee3;border-radius:10px;padding:24px 28px;margin:25px 0}.product h3{margin:12px 0;font-family:monospace;font-size:27px}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:25px 0}.compare article{border:1px solid #d2dbce;background:#fff;padding:24px;border-radius:10px}.compare h3{margin:12px 0}.stack{border-top:1px solid #d8ded5;border-bottom:1px solid #d8ded5;padding:15px 0;font-size:14px;color:#3a6854}details{border:1px solid #d8ded5;border-radius:6px;padding:15px 18px;margin:22px 0}summary{cursor:pointer;font-weight:600}.sources{padding-left:22px;font-size:13px;overflow-wrap:anywhere}.sources li{margin:23px 0}.sources p{margin:6px 0;color:#69766d}.back{display:inline-block;margin-top:20px}.skip{position:absolute;left:-9999px}.skip:focus{left:10px;top:10px;background:white;z-index:2}footer{font-size:12px;color:#68766b;margin-top:30px}@media(max-width:1050px){main{padding:35px;margin-left:200px}.nav{width:200px!important}h1{font-size:38px}}@media(max-width:760px){aside.nav{position:static;width:100%!important;padding:20px;border-right:0}.brand{font-size:18px;margin:0 0 12px}nav{display:flex;flex-wrap:wrap}nav a{padding:5px 10px}.nav small{display:none}main{margin:0;padding:22px}h1{font-size:34px}h2{font-size:25px}.compare{grid-template-columns:1fr}section{padding:30px 0}.product{padding:20px}.product h3{font-size:23px}}@media print{aside.nav,.skip{display:none}main{margin:0;padding:0;max-width:none}body{background:white;font-size:11pt}details>*{display:block}section{break-inside:auto}.compare article,.unknown{break-inside:avoid}a{color:inherit}.flow{break-inside:avoid}}'''
nav=[('task','01 数据怎样变成光'),('functions','02 必须完成哪些工作'),('route','03 五步实现与零件'),('product','04 产品怎样分配功能'),('parts','05 器件怎样连接'),('manufacture','06 零件怎样做出来'),('compare','07 换路线后的制造'),('evidence','资料与 UNKNOWN')]
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光模块为什么用这些零件？从路线到制造</title><meta name="description" content="从一只具体光模块出发，沿任务、路线、产品、零件、制造与路线差异理解光模块。"><style>'''+css+'''</style></head><body><a class="skip" href="#main">跳到正文</a><aside class="nav"><div class="brand">光模块问答<br>从路线到零件</div><nav aria-label="阅读目录">'''+''.join(f'<a href="#{i}">{t}</a>' for i,t in nav)+'''</nav><small>一只参考模块<br>一个功能的两种实现<br>2026 · 09 · 28</small></aside><main id="main"><header class="hero"><p class="eyebrow">一条有具体对象的阅读路径</p><h1>为什么这只光模块，<br>需要这些零件？</h1><p class="lead">技术路线决定产品怎样工作，也决定它需要哪些零件。先理解传输过程和必需功能，再看一只真实产品怎样实现这些功能，逐步追到器件的连接与制造。</p><span class="pill">原问答重组 + 外部原理补充 · 2026-09-28 注释修订：路线搭配与制造设备</span></header>'''+''.join(sections)+'''<footer>正文与示意离线可读。外部依据需要联网；原题链接指向同一仓库中的合并版。<br>本页不代表完整 BOM、量产工艺披露或设备投资结论。</footer></main><script>function revealSource(){const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!el)return;for(let p=el.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}}window.addEventListener('hashchange',revealSource);revealSource();const links=[...document.querySelectorAll('nav a')];const observer=new IntersectionObserver(entries=>{for(const e of entries){if(e.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id));}}},{rootMargin:'-10% 0px -65% 0px'});document.querySelectorAll('main section').forEach(s=>observer.observe(s));</script></body></html>'''
(HERE/'index.html').write_text(html)
print(HERE/'index.html')
