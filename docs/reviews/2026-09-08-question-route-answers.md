# 光模块：从一次传输，走到零件、制造和技术路线

2026-09-08｜首轮有据问答稿，待用户审阅｜未晋升 canonical

本文以用户提供的《光模块技术需求》《光模块技术路线梳理》《光模块构成介绍1》为问题起点。GPT问答提供问题，不作为事实来源。本轮由三个 gpt-5.6-luna 子代理研究，主控整合并复查关键原始资料；未使用原国内、海外知识库组织内容。以下“事实”表示指定来源直接支持的内容，厂商披露不等于第三方性能验证；“解释/推论”给出条件；“未知”表示本轮证据未能回答，不能理解为行业没有答案。

阅读顺序是：先定位模块，再沿信号认识零件，把连接变成制造动作，最后对照速率和路线。各问末尾说明下一步为什么要问。

## 1. 我们先看哪一只模块？它连接什么？

**事实。**选择 Coherent FTCE4527E1PCA（FTCE4527E1PxA系列）800G-DR8+ OSFP 作为接口与器件类型的参考对象。厂商产品表明确列出：EML发射器、PIN接收器、Dual MPO12光接口、2 km单模链路。选择它是因为资料明确，不代表它市场份额最高。[产品页参数表，日期未标](https://www.coherent.com/networking/transceivers/datacom/FTCE4527E1PxA)

把它放在两台网络设备之间理解：设备中的交换ASIC（专用交换芯片）负责交换处理；设备A通过电接口把信号交给模块A，模块A送出光；光纤连接模块B，模块B再向设备B交付电信号。该型号规格书给出电接口及单模光纤链路用途；这是接口层面的链路示意，不是内部拆机图。[FTCE4527E1PxA规格书，第1页，March Rev B2，年份未标](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-transceiver-ds.pdf)

**未知。**本轮没有拿到这只模块的完整内部BOM、封装剖面和生产流程。接下来应先问每个功能怎么完成，不能直接给未知芯片指定型号。

## 2. 电信号在哪里变成光？EML究竟是什么？

**器件原理事实。**Lumentum对其EML的说明把两个功能分开：DFB激光器连续地产生光；与其单片集成的电吸收调制器EAM对光进行调制。因此数据经过驱动电路作用于调制器，形成携带数据的光强变化。光的能量由供电支持的激光器提供，不能把信号线想成直接“变成光纤”。[Lumentum EMLs，Overview第1—2段，日期未标](https://www.lumentum.com/en/optical-communications/products/source-lasers-ics-and-photodiodes/emls)

**边界。**这是EML功能解释，不是证明参考模块使用Lumentum芯片。下一问需区分：既然EML负责调光，Driver和DSP分别还做什么？

## 3. Driver、DSP和retimer可以当成同一个东西吗？

**事实与功能解释。**Driver负责把电信号调整为发射器件所需的驱动条件；Coherent的驱动器资料列出偏置、调制幅度等可配置功能。这里不指定EAM一定由“调制电流”驱动，也不把该驱动器指定给参考模块。[Coherent Laser Driver Amplifiers，功能说明，日期未标](https://www.coherent.com/networking/optoelectronic-devices/integrated-circuits/56-gbps-laser-drivers)

参考模块规格书明确写电接口具有retimed特征，重定时是已披露功能。LPO MSA对传统retimed模块的解释指出，其模块内DSP承担数字处理和判决；LPO则调整这一分工。这些概念分别描述驱动、数字处理与重定时，不能互换。[参考规格书第1页](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-transceiver-ds.pdf)；[LPO MSA FAQ，How does LPO work / different to retimers，日期未标](https://www.lpo-msa.org/home/faqs.html)

**未知。**参考模块的DSP/retimer芯片型号和集成方式未披露。也不能由“有DSP”就断定以太网FEC一定在模块内完成。下一步沿光纤到另一端，看看接收需要什么不同功能。

## 4. 光到达另一端后，PD和TIA怎样接力？

**器件原理。**光电探测器PD把入射光变化转为光电流；跨阻放大器TIA将光电流转为电压信号。TI的光电二极管放大电路展示了这种连接及功能。它是原理依据，不是800G接收器选型依据。[TI CIRCUIT060041，Description及电路资料，日期未标](https://www.ti.com/tool/CIRCUIT060041)

结合参考产品已披露的PIN接收器，可把功能路径概括为：

```text
发射：设备电接口 → 信号处理/驱动功能 → EML → 光耦合结构 → 光纤
接收：光纤 → 光耦合结构 → PIN探测功能 → 跨阻放大/信号处理功能 → 设备电接口
```

这张图综合第1—4问的接口和器件功能；框表示功能，不保证对应一颗独立芯片，也没有给透镜、FAU或键合方式指定固定BOM。接下来要回答图上的箭头到底怎样在工厂里做出来。

## 5. 一根箭头能直接对应一台设备吗？

**不能，连接关系与制造步骤需要分别说明。**电连接要建立导电互连；光连接要把光有效地送进接收波导或光纤。CPO封装综述讨论了电互连、光纤连接及其不同封装选项，支持把两类任务分开；它并不提供这只EML模块的制造清单。[Tan等，Co-packaged optics: status, challenges, and solutions，2023-03-20，封装与互连章节](https://doi.org/10.1007/s12200-022-00055-y)

**制造实例。**PI的光子装配说明展示了搜索初始光耦合、调整位置、对准多个光学件，以及胶固化过程中继续校正位置。这说明“耦合”可能跨越测量、运动和固定多个动作。[PI Assembly & Packaging of Photonic Devices，Fast Multi-Channel Active Alignment，日期未标](https://www.pi-usa.us/en/knowledge-center/product-and-system-demonstrators/photonics-assembly-and-packaging)

**未知。**参考型号到底用何种贴装、引线键合或倒装、何种胶或焊接固定，本轮没有产品级证据。不能从“需要电互连”跳到“必然采购某种键合设备”。下一问先解释已经有公开实例的主动对准。

## 6. 主动对准在做什么？为什么不是“把光纤插上”就结束？

**事实。**PI说明主动对准以实际性能测量作为反馈；在光纤和芯片耦合中，可用光功率计测量输出，再调整位置以优化耦合。它寻找的是实际光学性能合适的位置，而不只是机械坐标对上。[PI Active Alignment，光功率作为评价指标的段落，日期未标](https://www.pi-usa.us/en/expertise/technology/controllers-software/active-alignment/)

**解释。**所以理解工序至少要知道：移动哪个对象、测哪个信号、合格标准是什么、固定后是否保持。被动对准则需要另查其定位结构和容差；本轮不能判断参考模块使用哪种方法，也不能从速率标签推出一律要求亚微米或更高精度。

从这里进入速率升级：必须先知道800G到底由哪些通道构成，才能讨论哪些连接条件变了。

## 7. 800G是八根光纤吗？为什么规格书还有850 Gb/s？

**事实。**参考规格书电接口为8×100G级PAM4，标出每lane 106.25 Gb/s以及850 Gb/s电侧聚合比特率（8×106.25，不能当作以太网有效负载吞吐）；“800G”是应用速率名称，不能把它和所有物理线速数字等同。规格中的电lane、光lane及收发方向需要分别读。[FTCE4527E1PxA规格书，第1、3—4页](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-transceiver-ds.pdf)

另一个更明确的对照：Coherent在2024-09-23披露的800G DR4演示是8×100G电接口、4×200G光接口，采用差分EML。可见800G并不固定等于8个光通道。[Coherent ECOC 2024，800G-DR4条目](https://www.coherent.com/news/press-releases/broad-portfolio-showcase-ecoc-2024)

**解释边界。**通道、波长、光纤根数、连接器孔位不是可随意互换的计数；2×400G DR4与4×200G DR4不能仅凭总速率视为同一光学配置，还需核对每组接口、波长及纤芯定义。下一步比较1.6T时，电侧和光侧应各列一栏。

## 8. 从800G到1.6T，能确认的变化是什么？

| 公开对象 | 电接口 | 光接口 | 来源状态 |
|---|---|---|---|
| Coherent 800G DR4 | 8×100G | 4×200G | 2024年演示披露，差分EML |
| Coherent 1.6T DR8 | 8×200G | 8×200G | 同场演示披露，SiPh |
| InnoLight 1.6T-DR8 OSFP224 | 8×200G | 8×200G并行 | 产品页声明，500 m，日期未标 |

依据：[Coherent ECOC 2024两个演示条目](https://www.coherent.com/news/press-releases/broad-portfolio-showcase-ecoc-2024)；[InnoLight 1.6T-OSFP224产品说明](https://www.innolight.com/data-center-networking/1.6t-osfp224)。这里使用厂商标称lane速率。

**条件解释。**这些对象说明总速率可由不同lane组合实现。但前两项同时改变了总速率、光lane数量和光学路线，不能作为只改变速率的工艺实验。若要证明贴装精度、良率或功耗因速率而变，仍需同路线、同距离等条件下的可比设计和数据。产品页本身也不证明量产规模。

## 9. 为什么需要1.6T，而不是继续用更多800G？

**先给一个可检验的容量解释。**OIF的3.2T CPO规范以51.2T交换机为系统例子，安排16个3.2T模块靠近交换ASIC，说明模块带宽要与系统聚合容量一起考察。[OIF 3.2T CPO IA，2023-03-29，第7—9页](https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf)

**算术示例，不是特定交换机配置声明。**若目标聚合容量固定为51.2 Tb/s，则64×0.8与32×1.6都等于51.2。选择更高速端口可以减少达到该聚合容量所需的端口数；是否有利还取决于对端速率、拓扑和实际链路需求。

**未知。**本轮没有具体集群的通信量、利用率、拥塞及成本数据，因此不能认定它的800G“不够”，更不能由GPU数量直接推导所需速率。后续要用一个具体训练/推理通信案例回答“多少数据、必须多久传完、经过哪段网络”。

## 10. 3.2T是不是下一代同一种模块？

**需要先说清对象。**OIF 2023年3.2T CPO规范中的光学选项包括8×400GBASE-DR4或8×400GBASE-FR4。这是一个共封装模块的聚合容量，不等于已经证明一个通用3.2TbE可插拔端口成熟。[OIF IA，第7—10页及图4](https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf)

另一条器件证据是Coherent在2025-03-27宣布展示400G D-EML，面向1.6T和未来3.2T连接，措辞为演示及受控供货。它支持“400G器件路线已有公开演示”，不能支持“3.2T整机已广泛量产部署”。[Coherent 400G Differential EML公告，演示及供货状态段](https://www.coherent.com/news/press-releases/400g-differential-eml)

本轮未对截至今日的全部3.2T产品做穷尽调查，保留实际量产与部署为待查。下一步需要把“速率”和“技术路线”分开。

## 11. SiPh、LPO、CPO分别改变哪一部分？

| 名词 | 沿前文功能图看变化 | 本轮依据与边界 |
|---|---|---|
| SiPh（硅光） | 在硅光平台组织光子功能；具体集成哪些调制、波导、探测等功能需看设计 | Coherent公开展示SiPh MZM PIC及EML器件，证明它们是不同实现对象，不证明任一份额领先 |
| LPO（线性可插拔光学） | 模块不含传统DSP/retimer功能，链路均衡依赖主机能力及配套设计；仍是可插拔 | LPO MSA明确解释这种处理分工，不能推成任何主机均可替换 |
| CPO（共封装光学） | 把光学功能移近并与交换ASIC共封装，改变高速电路径和封装位置 | NVIDIA给出其SiPh CPO实例；该实例中激光源仍位于前面板外置光源模块 |

来源：[Coherent ECOC 2022，SiPh MZM PIC及200G EML演示条目，2022-09-19](https://www.coherent.com/news/press-releases/coherent-thought-leaders-to-present-at-ecoc-2022)；[LPO MSA FAQ，定义及系统要求](https://www.lpo-msa.org/home/faqs.html)；[NVIDIA技术博客，A New Era in Data Center Networking，2025年发布，封装与外置光源段](https://developer.nvidia.com/blog/?p=97917)。

**解释。**SiPh讨论光学集成平台，LPO讨论信号处理分工，CPO讨论封装位置；不能画成三个互斥的“升级下一站”。也不能把CW连续光源和EML当成同一器件：第2问中EML已包含调制功能。

## 12. 技术路线解决旧问题后，还需要查什么新条件？

**有依据的例子。**本文引用的100G-DR-LPO规范参考架构明确主机使用带DSP的SerDes及RS(544,514) FEC，并定义主机与模块的接口。这说明去掉模块DSP后仍需系统级信号处理与配套约束。[LPO 100G-DR-LPO规范，正文标Rev 1.0、2025-03-19，第1页及第5章](https://www.lpo-msa.org/files/live/sites/lpomsa/files/specs/LPO_MSA_Specification_v1p01.pdf)

CPO综述则讨论封装、热管理和光纤连接等挑战。这支持逐项追问如何制造和维护，不支持将CPO判定为唯一必然路线。[Tan等综述，2023，挑战与解决方案章节](https://doi.org/10.1007/s12200-022-00055-y)

**后续路线问题。**对任何方案都依次问：它缩短了哪段路径或移除了哪项处理？对主机、光源、散热、耦合和维修提出什么要求？有没有系统测试？不要只列优点。

## 13. 工序变难，设备收入就一定增加吗？

**不能直接推出。**PI的装配实例同时展示了对准及自动化改进，说明工艺要求与生产效率需要同时观察；这类资料不是设备订单或市场规模证据。[PI装配应用说明](https://www.pi-usa.us/en/knowledge-center/product-and-system-demonstrators/photonics-assembly-and-packaging)

**分析框架（不是测算结果）。**在固定工序、单机加工口径一致且不考虑库存波动时，可用“目标合格产量 ÷ 单机有效合格产能”估计设备需求；有效产能受节拍、并行工位、开机时间、利用率和良率影响。收入还要看新增采购、设备价格、替换周期与供应商份额。精度提高、自动化提速和工序合并可能同时发生，不能只看一个箭头。

**未知。**没有具体产品的工序清单、设备节拍、良率、存量可用产能和采购价格，本轮不量化设备价值增幅，也不推出公司受益排名。

## 本轮之后最值得继续追的三个问题

1. **实际耦合结构是什么？**为参考产品找到能公开引用的剖面或工艺说明，判断是否含透镜、阵列、怎样固定。验收是把第4问的一段“光耦合结构”展开成确证实物；找不到则继续明确未知。
2. **单lane升级怎样影响连接？**找同一路线100G与200G器件的可比驱动/封装资料，分别核实带宽、寄生、热和测试约束。不能把单lane电性能变化直接等同于光学定位精度变化。
3. **具体网络什么时候需要升级？**选定一个通信任务和网络位置，用数据量、时间要求、链路利用率及拓扑建立算例，再检查原国内、海外知识库是否有对应材料可关联。

## 复核范围

主控已重新打开并检查本文所用的关键产品页、规格书、EML说明、LPO资料、OIF 3.2T IA、Coherent演示公告和工艺说明。未引用打不开正文的Broadcom页面来证明端口配置，未采用代理草稿中的OSFP-XD必然迁移、DSP必含FEC或设备价值乘数等泛化。只做来源和解释边界核对，不宣称完成行业穷尽核验。动态页面未注明发布日期时已明确标注；未使用网页版权年份冒充发布日期。

复审记录：Luna语义复审后补充了850 Gb/s与有效负载的区分及DR4配置说明。OIF原文第7页直接写出16个模块以及8×400GBASE-DR4/FR4，保留其确切表述，不将其误降为仅算术假设。来源链接存在与格式检查不等于领域结论已获人工认可。
