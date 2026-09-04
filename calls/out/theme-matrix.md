# 跨公司议题矩阵

> `analyst_question` 只显示关注点，不进入管理层事实列。冲突、未知和证据不足均显式保留。

| 议题 | 供给侧已审核陈述 | 需求侧已审核陈述 | 交叉验证 | 结论状态 |
|---|---|---|---|---|
| T001 AI集群800G光互连部署需求 | 未知 | 未知 | 未交叉验证 | candidate |
| T002 800G量产能力和制造周期 | CL005 管理层把名义产能到实际收入的时差归因于制造周期; CL006 AAOI称其2026收入水平受产能与供应链而非市场需求限制; CL021 Lumentum披露云光模块出货环比增长超过40% | CL007 Cisco披露Q2来自超大规模客户的AI基础设施合计订单为21亿美元 | independent/insufficient: AAOI供给侧明确称收入受产能与供应链限制；Cisco的21亿美元是硅片、系统与光学合计订单且未直接说光模块供给受限，故不足以交叉验证行业卡点 | candidate |
| T003 扩充800G模块制造能力并爬坡 | CL001 AAOI称Q1完成对一家大型超大规模客户的首次800G批量交付; CL002 AAOI称Q1末800G模块月产能接近10万只; CL003 AAOI预计800G从Q2开始明显放量; CL034 Fabrinet确认其向超大规模客户推进的两个datacom模块项目均为800G scale-out应用 | 未知 | same_source/partially_supported: 同一AAOI官方新闻稿同时给出首次批量交付和月产能，能支持公司级进展但不构成独立交叉验证; supports/partially_supported: AAOI完成800G首次批量交付且Fabrinet确认两个超大规模客户scale-out项目均为800G；支持800G制造项目扩散但Fabrinet没有披露交付规模 | solution_emerging |
| T004 高速可插拔光学新品发布 | CL008 Cisco宣布1.6T OSFP可插拔光模块；不与800G产品作跨代比较; CL012 Cisco宣布800G LPO可插拔光模块；按800G线性电链映射; CL074 Credo把ZeroFlap Optics列入多产品未来爬坡计划 | CL074 Credo把ZeroFlap Optics列入多产品未来爬坡计划 | same_source/insufficient: 同一句官方prepared remarks包含两个产品发布事件；拆成原子陈述后仍只是同源发布信息，不能互证部署规模 | not_applicable |
| T005 客户现场审核对产能转收入的滞后 | 未知 | 未知 | 未交叉验证 | candidate |
| T006 800G与1.6T 2xFR4模块交付需求 | 未知 | 未知 | 未交叉验证 | candidate |
| T007 高速InP激光器制造能力 | CL013 AAOI称800G或1.6T 2xFR4每只模块需要四颗激光器，使供给更难; CL014 AAOI称当时MOCVD设备处于全面积压状态; CL015 AAOI管理层称行业存在InP激光器制造产能短缺; CL020 Lumentum披露200G EML收入环比增长超过一倍; CL027 Lumentum在EML与激光器供给问答中称供需缺口可能超过30%; CL028 Coherent把InP称为行业范围约束并将扩产列为最高优先级之一; CL033 Fabrinet称激光器是datacom供给波动的主要来源之一；同段另提内存和部分ASIC但不映射到C1 | 未知 | same_source/company_claim_only: 同一AAOI电话会中CEO与CFO分别谈到多激光器需求和InP激光器产能短缺；仍是同公司同源主张; supports/partially_supported: AAOI与Lumentum两家公司独立支持高速InP或EML激光器有效产能偏紧；Lumentum没有提到MOCVD backlog，因此只加强产能约束候选而不验证AAOI的设备积压说法; supports/partially_supported: AAOI与Coherent独立称行业存在InP激光器制造能力约束；Coherent没有提到MOCVD设备积压，因此不能验证AAOI的具体设备卡点; supports/partially_supported: Lumentum称EML供需缺口超过30%且Coherent称InP为行业约束；两者共同增强高速InP或EML有效产能偏紧判断但未证明所有器件类别均短缺 | candidate |
| T008 扩建InP激光器外延与芯片产能 | CL025 Lumentum称Greensboro InP fab要到2028年初才可能形成显著收入贡献; CL029 Coherent预计到2027年底再次将内部InP产能提高一倍以上; CL030 Coherent称6英寸线上的EML、CW激光器和光电二极管良率均超过3英寸线; CL052 Nokia承诺在2026年底前于San Jose启用第二座InP半导体制造设施; CL057 Nokia重申San Jose新InP设施预计于2026年内开始爬坡 | 未知 | 未交叉验证 | solution_emerging |
| T009 Silicon One交换ASIC出货里程碑 | CL009 Cisco预计在FY26 Q2出货第100万颗Silicon One交换芯片; CL010 Cisco在下一季确认已出货第100万颗Silicon One交换芯片 | 未知 | 未交叉验证 | not_applicable |
| T010 1.6T可插拔双架构演示与商业爬坡 | CL022 Lumentum预计1.6T光模块在FY26 Q4爬坡; CL024 Lumentum称关键组件约束使1.6T相关段落中的模块出货显著低于客户需求 | 未知 | 未交叉验证 | solution_emerging |
| T011 4x400G EML演示与未来3.2T路径 | 未知 | 未知 | 未交叉验证 | not_applicable |
| T012 AI光学系统多维扩展约束 | 未知 | 未知 | 未交叉验证 | candidate |
| T013 CPO光源技术与商业化进度 | CL023 Lumentum预计UHP CPO激光器在2026年12月季度产生有意义收入 | 未知 | 未交叉验证 | solution_emerging |
| T014 OCS生产瓶颈解除与双厂爬坡 | CL031 Coherent称已解决OCS生产瓶颈并在两座工厂快速提高产出 | 未知 | 未交叉验证 | solution_emerging |
| T015 CPO精密光学封装商业进度 | 未知 | 未知 | 未交叉验证 | solution_emerging |
| T016 高速数通关键组件组合约束 | CL032 Fabrinet称datacom组件与材料短缺使出货和收入显著低于需求; CL036 Arista称行业范围多类关键组件短缺且需求超过当年供给; CL066 Ciena称光子部件供应形成约束; CL068 Ciena称供应约束实际压低第一季度可实现收入 | 未知 | supports/partially_supported: Fabrinet与Arista分别从制造服务商和网络系统商侧确认多类关键组件约束使供给低于需求；两者均未量化光学份额或具体速率缺口 | candidate |
| T017 CPO商业化与采用阶段 | CL026 Lumentum称scale-out CPO与OCS已有初始贡献但仍相对较小，scale-up CPO仍处早期; CL035 Fabrinet称已有少量CPO收入并正与三家客户推进项目; CL069 Ciena预计Vesta样品于2026年第二季度可提供 | CL039 Arista称当时CPO仍偏实验且各供应商方案高度专有并把开放CPO放在数年后; CL069 Ciena预计Vesta样品于2026年第二季度可提供 | supports/partially_supported: Lumentum与Fabrinet分别披露CPO或合并CPO相关业务已有初始但较小的收入贡献；支持早期商业化而非规模成熟; supports/partially_supported: Fabrinet已有少量CPO收入但Arista仍把开放CPO视为数年后的早期路径；显示不同产业环节进度不一且整体尚未成熟 | solution_emerging |
| T018 AI网络平台需求（非光学确认） | 未知 | CL040 NVIDIA称Spectrum-X规模已超过其他以太网网络同行合计; CL041 NVIDIA称数据中心网络收入约150亿美元并同比接近三倍; CL045 Broadcom称FY2025Q3 AI收入同比增长63%至52亿美元；只作为非光学需求背景; CL046 Broadcom称FY2025Q4 AI半导体收入同比增长74%；不能换算光模块需求; CL047 Broadcom称FY2026Q1 AI收入84亿美元并同比增长106%；只作为非光学需求背景; CL048 Broadcom称FY2026Q2 AI半导体收入108亿美元并同比增长143%；不能换算光模块需求; CL058 Nokia称2026Q2 AI与云订单流入28亿欧元且销售额同比翻倍以上；只能作混合网络需求证据; CL061 Nokia预计约一半相关订单在未来十二个月转化为收入 | supports/partially_supported: NVIDIA网络收入与Broadcom AI半导体收入均显示AI网络相关需求扩张；两者都未拆出光模块或光器件份额因此只能验证非光学需求背景 | candidate |
| T019 800GbE与1.6T下游系统部署 | 未知 | CL037 Arista称800GbE累计部署客户已超过100家; CL038 Arista预计1.6T于2027年进入生产规模 | 未交叉验证 | candidate |
| T020 AI数据中心容量建设（非光学确认） | 未知 | CL042 Meta称Q1资本开支包含服务器数据中心与网络基础设施投资; CL043 Meta称将显著扩大自有数据中心版图并通过供应链协议锁定未来组件; CL044 Meta称多年期云协议的容量将在2026年与2027年陆续上线 | 未交叉验证 | candidate |
| T021 相干光与AI数据中心互联采用阶段 | CL051 Nokia称800G ZR或ZR+相干可插拔已一般可用并开始向一家美国客户发货; CL056 Nokia预计相关产品在2027年中开始送样; CL062 Nokia预计相关产品在2027年下半年开始量产; CL063 Ciena称首个scale-across项目已开始产生收入出货; CL064 Ciena预计首个scale-across项目未来数季爬坡至数亿美元; CL065 Ciena称WL6 Nano 800G相干可插拔已进入初始收入出货; CL070 Ciena预计Hyper-Rail在2026年底开始标准化; CL071 Ciena预计Hyper-Rail于2027年开始爬坡 | CL051 Nokia称800G ZR或ZR+相干可插拔已一般可用并开始向一家美国客户发货; CL053 Nokia称2025Q4 Optical Networks净销售额同比增长17%；不能视作单一模块出货; CL054 Nokia称2026Q1取得多项AI与云设计定点及可插拔和线路系统订单; CL056 Nokia预计相关产品在2027年中开始送样; CL059 Nokia称2026Q2在光网络和IP网络均取得长期订单；不能换算相干模块数量; CL062 Nokia预计相关产品在2027年下半年开始量产; CL063 Ciena称首个scale-across项目已开始产生收入出货; CL064 Ciena预计首个scale-across项目未来数季爬坡至数亿美元; CL065 Ciena称WL6 Nano 800G相干可插拔已进入初始收入出货; CL067 Ciena称首个hyperscaler追加多个集群订单; CL070 Ciena预计Hyper-Rail在2026年底开始标准化; CL071 Ciena预计Hyper-Rail于2027年开始爬坡; CL072 Ciena称获得首个Hyper-Rail多轨订单; CL073 Ciena称赢得大型hyperscaler相干模块项目 | 未交叉验证 | solution_emerging |

## 冲突登记

- 当前样本没有经审核的直接冲突；这表示“尚未观察到”，不表示不存在冲突。
