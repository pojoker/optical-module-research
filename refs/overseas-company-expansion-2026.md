# 海外公司扩展研究底稿（2026）

研究截止日：2026-08-11

用途：把现有海外季度覆盖池 `LITE / AAOI / COHR / FN / NVDA / CSCO / ANET / META` 扩展到其他有代表性的海外公司，为后续录入 `calls/` 提供一手资料清单和保守主题候选。

结论：优先研究的六家公司均适合纳入，不需要替换。

## 1. 证据口径

- 本文只采用公司 IR、公司官网、SEC/监管申报或公司发布的正式结果材料。搜索结果仅用于定位，未作为事实证据。
- 每个季度槽位只登记截至研究截止日已经披露的材料；尚未披露的季度不得用管理层指引替代。
- 本文的 `fact` 表示材料能够直接证明“公司已经披露、发布、完成、报告或声称发生”该事项；若事实来自公司自己的公告，仍只是第一方 `asserted`，不自动升级为独立验证。
- `forward-looking` 表示计划、预期、指引、目标、未来采样或未来量产。
- `technical demo` 分为“已完成演示/试验”和“计划演示”。预告将在展会演示，不能记录为已经演示。
- `corporate narrative` 表示公司对需求、性能、市场地位、客户价值或行业趋势的解释，不能单独证明需求规模、客户采用、供货关系、稀缺性或卡点已经解决。
- 公司产品、系统收入或匿名客户披露不得自动产生与现有国内公司的合作、竞争、供货或替代关系。关系仍需双边公告、客户 BOM、监管材料或可核验出货证据。
- 下文的 theme 仅为待人工复核的候选映射；它不是 canonical 事实，也不改变现有 theme 的证据等级。

## 2. 扩展池总览

| 建议 ID | 实体与证券代码 | 产业链观察角色 | 为什么适合纳入 |
|---|---|---|---|
| AVGO | Broadcom Inc.; Nasdaq: AVGO | Ethernet 交换 ASIC、SerDes、光 PAM-4 DSP、EML/PD 与 CPO 平台 | 补足交换芯片与光 DSP/CPO 的上游技术、sampling 和生产阶段信号。实体和代码见[官方 IR](https://investors.broadcom.com/company-information/faqs)，产品边界见[官方 Taurus 公告](https://investors.broadcom.com/news-releases/news-release-details/broadcom-delivers-industrys-first-400glane-optical-dsp-next)。 |
| MRVL | Marvell Technology, Inc.; Nasdaq: MRVL | 光 DSP、电光器件、硅光、交换芯片和定制计算互连 | 能交叉观察 800G/1.6T scale-out、NPO/CPO、相干 DCI 和 3.2T 路线。实体、代码及业务边界见[官方托管 10-K](https://investor.marvell.com/sec-filings/all-sec-filings/content/0001835632-26-000011/mrvl-20260131.htm)。 |
| NOK | Nokia Corporation（Nokia Oyj）；Nasdaq Helsinki: NOKIA；NYSE ADR: NOK | IP/数据中心网络、光传输/DCI、相干可插拔、光组件和内部 InP 制造 | 补足系统侧采用、相干光学和内部 InP 产能信号，但系统销售不能换算成模块数量。证券信息见[Nokia 官方股票页](https://www.nokia.com/about-us/investors/stock-information/)。 |
| CIEN | Ciena Corporation; NYSE: CIEN | 光传输系统、相干 DSP/光引擎、DCI、CPO 光引擎及数据中心互连 | 能区分相干 1.6T、数据中心内部 CPO 与传统可插拔模块，不宜把不同形态合并计数。实体和代码见[官方季度结果](https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-Second-Quarter-2026-Financial-Results/default.aspx)，产品范围见[官方 OFC 公告](https://www.ciena.com/about/newsroom/press-releases/ciena-solidifies-ai-networking-leadership-unveils-new-innovations-for-high-speed-connectivity)。 |
| MTSI | MACOM Technology Solutions Holdings, Inc.; Nasdaq: MTSI | CW 激光器、驱动器、TIA/接收器、CDR 和其他模拟/混合信号光电半导体 | 补足模块内部模拟光电器件和外延供应保障观察。产品公告有时以运营主体 MACOM Technology Solutions Inc. 名义发布，不应另建第二家上市公司。实体、代码和业务范围见[官方季度结果](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-second-quarter-2026-financial-results)。 |
| CRDO | Credo Technology Group Holding Ltd; Nasdaq: CRDO | 高速 SerDes、光 DSP、AEC、800G 光收发器、遥测及 SiPho PIC | 补足 AEC 与光互连的路线竞争、1.6T DSP 及产品可得性信号。实体和代码见[官方季度结果](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Fourth-Quarter-and-Fiscal-Year-2026-Financial-Results/default.aspx)，产品范围见[官方 Cardinal 公告](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Introduces-Cardinal-A-LowPower-1-6T-Optical-DSP-Family-Engineered-for-MassiveScale-AI-Fabrics/default.aspx)。 |

建议把六家都放入季度覆盖池，而不是仅作为 `watch_entities`：它们均有连续四季度的官方结果材料，并且季度披露能够提供需求、产品阶段、产能或客户采用的重复观察点。公司官网产品公告仍作为跨季度 disclosure 单独登记。

## 3. Broadcom（AVGO）

### 3.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| FY2026 Q2 | 2026-05-03 | 2026-06-03 | [Broadcom Inc. Announces Second Quarter Fiscal Year 2026 Financial Results](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2026-financial) |
| FY2026 Q1 | 2026-02-01 | 2026-03-04 | [Broadcom Inc. Announces First Quarter Fiscal Year 2026 Financial Results](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial) |
| FY2025 Q4 / FY | 2025-11-02 | 2025-12-11 | [Broadcom Inc. Announces Fourth Quarter and Fiscal Year 2025 Financial Results](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2025) |
| FY2025 Q3 | 2025-08-03 | 2025-09-04 | [Broadcom Inc. Announces Third Quarter Fiscal Year 2025 Financial Results](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2025-financial) |

### 3.2 近十二个月事件候选

#### Taurus 400G/lane 光 DSP

来源：[Broadcom Delivers Industry’s First 400G/lane Optical DSP for Next-Generation AI Networks，2026-03-11](https://investors.broadcom.com/news-releases/news-release-details/broadcom-delivers-industrys-first-400glane-optical-dsp-next)

- `fact`：Broadcom 发布 Taurus BCM83640，并称产品已向 early-access customers and partners 开始 sampling。这里只能记为“发布/采样”，不能记为批量采用。
- `corporate narrative / technical claim`：3nm、400G/lane、集成 laser driver，以及面向 1.6T–3.2T 模块的 BER、功耗和互操作性描述均为公司技术主张。
- `forward-looking`：面向未来 3.2T 光学和 204.8T 交换系统的能力属于路线预期。
- `technical demo`：该公告不是已完成客户部署证据，不应生成 `demonstrated` 以上的客户采用状态。
- theme 候选：T004（高速可插拔光学新品）；T010（1.6T 路径，sampling 子阶段）；T011（400G/lane 与 3.2T 路径）。

#### Tomahawk 6 生产阶段

来源：[Broadcom Now Shipping World’s First 102.4 Tbps Switch in Production Volume，2026-03-12](https://investors.broadcom.com/news-releases/news-release-details/broadcom-now-shipping-worlds-first-1024-tbps-switch-production)

- `fact`：公司称 Tomahawk 6 交换芯片系列已经 production-volume shipping。这是第一方出货主张，不能外推到光模块出货。
- `corporate narrative`：减少网络层级、减少光学器件和改善功耗/成本的说法是公司对系统价值的解释。
- `forward-looking`：公告中的集群扩展能力或未来部署价值不得当作已实现客户规模。
- theme 候选：T018、T019 的下游系统邻接信号；不得据此推导光模块形态、数量、供应商或国内替代。

### 3.3 纳入边界

Broadcom 应作为“交换 ASIC + 光 DSP/CPO 上游平台”覆盖，不标为光模块厂。Taurus 的 sampling 与 Tomahawk 6 的生产出货是两个不同 program/产品阶段，不得合并成“Broadcom 1.6T 光模块已经量产”。

## 4. Marvell（MRVL）

### 4.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| FY2027 Q1 | 2026-05-02 | 2026-05-27 | [Marvell Reports First Quarter FY2027 Results](https://investor.marvell.com/news-events/press-releases/detail/1023/marvell-technology-inc-reports-first-quarter-of-fiscal-year-2027-financial-results) |
| FY2026 Q4 / FY | 2026-01-31 | 2026-03-05 | [Marvell Reports Fourth Quarter and FY2026 Results](https://investor.marvell.com/news-events/press-releases/detail/1011/marvell-technology-inc-reports-fourth-quarter-and-fiscal-year-2026-financial-results) |
| FY2026 Q3 | 2025-11-01 | 2025-12-02 | [Marvell Reports Third Quarter FY2026 Results](https://investor.marvell.com/news-events/press-releases/detail/999/marvell-technology-inc-reports-third-quarter-of-fiscal-year-2026-financial-results) |
| FY2026 Q2 | 2025-08-02 | 2025-08-28 | [Marvell Reports Second Quarter FY2026 Results](https://investor.marvell.com/news-events/press-releases/detail/989/marvell-technology-inc-reports-second-quarter-of-fiscal-year-2026-financial-results) |

### 4.2 近十二个月事件候选

#### FY2027 Q1 的 AI 光互连需求披露

来源：[FY2027 Q1 官方结果，2026-05-27](https://investor.marvell.com/news-events/press-releases/detail/1023/marvell-technology-inc-reports-first-quarter-of-fiscal-year-2027-financial-results)

- `fact`：公司报告本季收入 24.18 亿美元；财务结果与未来预期要分开记录。
- `corporate narrative`：管理层称看到 exceptional AI-related bookings，并把需求归因于 800G/1.6T scale-out optics、NPO/CPO、DCI 和定制 XPU 等多个产品组。该表述不能拆出单一产品的数量或客户。
- `forward-looking`：FY2027/FY2028 收入展望及预计持续加速属于前瞻。
- `technical demo`：结果公告未证明具体 1.6T/NPO/CPO 客户部署。
- theme 候选：T006、T010、T017、T018；不能升级为行业短缺、客户验证或特定模块厂供货关系。

#### 收购 Polariton

来源：[Marvell Announces Acquisition of Polariton Technologies，2026-04-22](https://investor.marvell.com/news-events/press-releases/detail/1020/marvell-announces-acquisition-of-polariton-technologies-advancing-optical-performance-scaling-to-3-2t-and-beyond)

- `fact`：Marvell 宣布已完成对 Polariton Technologies 的收购，交易价格未披露。
- `corporate narrative / technical claim`：等离子体调制技术可提高相干/DCI 链路的密度与能效，是公司对收购技术价值的主张。
- `forward-looking`：通向 3.2T 及以上光互连的路线属于未来产品方向；收购完成不等于产品已经部署。
- `technical demo`：公告本身不构成量产产品或客户部署演示。
- theme 候选：T011、T017；保持在技术/路线候选阶段。

### 4.3 纳入边界

Marvell 可同时观察光 DSP、硅光、交换与定制硅，但不能因产品组合完整就推导“端到端供货”。收购和 bookings 都不自动形成与现有国内公司之间的替代或竞争边。

## 5. Nokia（NOK / NOKIA）

### 5.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| 2026 Q2 / H1 | 2026-06-30 | 2026-07-23 | [Nokia Corporation Report for Q2 and Half Year 2026](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/) |
| 2026 Q1 | 2026-03-31 | 2026-04-23 | [Nokia Corporation Interim Report for Q1 2026](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) |
| 2025 Q4 / FY | 2025-12-31 | 2026-01-29 | [Nokia Corporation Financial Report for Q4 2025 and Full Year 2025](https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/) |
| 2025 Q3 / 9M | 2025-09-30 | 2025-10-23 | [Nokia Corporation Interim Report for Q3 2025](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/) |

### 5.2 近十二个月事件候选

#### 800G ZR/ZR+ 可得性、首个匿名客户与 InP 扩产计划

来源：[Nokia 2025 Q3 官方结果，2025-10-23](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/)

- `fact`：管理层称 800G ZR/ZR+ coherent pluggables 已 generally available，并已开始向“一家美国大型客户”发货。该客户未具名，仍是 Nokia 第一方 asserted 证据，不代表广泛采用。
- `forward-looking`：Nokia 称计划在 2026 年底前于 San Jose 开设第二座 InP 半导体制造设施。
- `corporate narrative`：Optical Networks 增长及 AI & Cloud 客户需求是组合层信号，不能换算为特定模块数量。
- `technical demo`：本材料不是客户独立确认，也未披露共同测试细节。
- theme 候选：T004/T019（800G GA 与第一方发货）；T007/T008（InP 产能计划）。不得猜测匿名客户。

#### 后续季度的需求与产能交叉观察

来源：[2025 Q4 官方结果](https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/)、[2026 Q1 官方结果](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/)、[2026 Q2 官方结果](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/)

- `fact`：Nokia 报告 Optical Networks 在 2025 Q4 增长 17%、2026 Q1 增长 20%、2026 Q2 增长 20%；2026 Q1/Q2 的 AI & Cloud 客户销售分别增长 49%/105%。这些均为公司报告的组合层实际增长率。
- `forward-looking`：2025 Q4 材料所述 2026 年资本开支与制造能力增加，以及 2026 Q1 所述新 InP 工厂稍后爬坡，均是未来动作。
- `corporate narrative`：公司把增长与 AI/Cloud 需求相联系，但不能据此证明特定产品短缺或卡点解决。
- `technical demo`：无客户独立部署数量或模块 BOM。
- theme 候选：T001（需求旁证，不是模块短缺结论）、T007/T008（产能动作）。

### 5.3 纳入边界

Nokia 的系统、相干可插拔和内部光组件应分层记录。网络系统收入不能自动转化为模块出货；“向一家美国大型客户发货”也不能生成未具名客户实体或供应关系。

## 6. Ciena（CIEN）

### 6.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| FY2026 Q2 | 2026-05-02 | 2026-06-04 | [Ciena Reports Fiscal Second Quarter 2026 Results](https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-Second-Quarter-2026-Financial-Results/default.aspx) |
| FY2026 Q1 | 2026-01-31 | 2026-03-05 | [Ciena Reports Fiscal First Quarter 2026 Results](https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-First-Quarter-2026-Financial-Results-03-05-2026/default.aspx) |
| FY2025 Q4 / FY | 2025-11-01 | 2025-12-11 | [Ciena Reports Fiscal Fourth Quarter and FY2025 Results](https://investor.ciena.com/news/news-details/2025/Ciena-Reports-Fiscal-Fourth-Quarter-2025-and-Year-End-Financial-Results-12-11-2025/default.aspx) |
| FY2025 Q3 | 2025-08-02 | 2025-09-04 | [Ciena Reports Fiscal Third Quarter 2025 Results](https://investor.ciena.com/news/news-details/2025/Ciena-Reports-Fiscal-Third-Quarter-2025-Financial-Results-09-04-2025/default.aspx) |

### 6.2 近十二个月事件候选

#### Vesta 200 6.4T CPX 光引擎

来源：[Ciena Unveils Vesta 200，2026-02-25](https://www.ciena.com/about/newsroom/press-releases/ciena-unveils-the-industrys-highest-density-lowest-power-pluggable-optical-engine-to-meet-data-center-ai-demands)

- `fact`：Ciena 发布 Vesta 200 6.4T CPX optical engine。
- `corporate narrative / technical claim`：200G/lane、retimer-free linear drive、最高 20dB loss budget 和最高节省 70% 功耗均为公司技术主张。
- `forward-looking`：公告称计划在 OFC 2026 演示。
- `technical demo`：这是 planned demo，不得仅据预告记为已完成演示、客户采用或量产。
- theme 候选：T017（CPO 商业化阶段）；与 T013 邻接但不能推导外置光源收入或开放生态已经形成。

#### Vodafone Idea 的 WL6e 试验/部署披露

来源：[Vodafone Idea Deploys Ciena WaveLogic 6 Extreme，2026-03-31](https://investor.ciena.com/news/news-details/2026/Vodafone-Idea-Deploys-Cienas-WaveLogic-6-Extreme-to-Deliver-High-Capacity-Connectivity-03-31-2026/default.aspx)

- `fact`：Ciena 公告称 Vodafone Idea 正使用 Ciena 6500/WaveLogic 6 Extreme 改造传输网络。
- `technical demo`：公告称两座数据中心之间已完成单光通道 1.6Tb/s line-rate trial；它是相干 DCI/传输试验，不是数据中心 1.6T 可插拔模块量产。
- `forward-looking`：支持未来流量增长及 400G/800G 服务机会属于预期。
- `corporate narrative`：性能、容量和运营价值仍是公告中的公司/客户表述。
- theme 候选：T010 的“1.6T 技术验证”邻接证据，但必须保留 coherent DCI 与 datacom pluggable 的形态差异。

### 6.3 纳入边界

Ciena 的 1.6T coherent wavelength、6.4T CPO engine 与 1.6T datacom module 不是同一产品层。录入时应保留形态、距离和应用域，不得只按“1.6T”合并事件。

## 7. MACOM（MTSI）

### 7.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| FY2026 Q3 | 2026-07-03 | 2026-08-06 | [MACOM Reports Fiscal Third Quarter 2026 Results](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-third-quarter-2026-financial-results) |
| FY2026 Q2 | 2026-04-03 | 2026-05-07 | [MACOM Reports Fiscal Second Quarter 2026 Results](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-second-quarter-2026-financial-results) |
| FY2026 Q1 | 2026-01-02 | 2026-02-05 | [MACOM Reports Fiscal First Quarter 2026 Results](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-first-quarter-2026-financial-results/) |
| FY2025 Q4 / FY | 2025-10-03 | 2025-11-06 | [MACOM Reports Fiscal Fourth Quarter and FY2025 Results](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-fourth-quarter-and-fiscal-year-2025/) |

### 7.2 近十二个月事件候选

#### OFC 2026 展示预告与 448G/lane driver 可得性

来源：[MACOM to Showcase Connectivity Solutions at OFC 2026，2026-03-11](https://ir.macom.com/news-releases/news-release-details/macom-showcase-innovative-connectivity-solutions-ofc-2026)、[MACOM Announces Two New 448G/lane Drivers，2026-03-17](https://ir.macom.com/news-releases/news-release-details/macom-announces-two-new-448g-lane-drivers-32t-data-center/)

- `fact`：MACOM 后一份公告称两款 448G/lane PAM4 driver 已 available。可得性不等于下游 3.2T 模块量产。
- `forward-looking`：OFC 预告中的 1.6T retimed optics、ACC、LPO、3.2T/400G-per-lane、800G LR2 以及 75mW/100mW CW laser 均是计划展示内容。
- `technical demo`：OFC 预告只能记为 planned demo，不能写成 demo completed。
- `corporate narrative / technical claim`：产品性能、功耗、带宽和应用价值为公司主张。
- theme 候选：T004、T010、T011；CW laser 能力只与 T007 邻接，不能证明有效产能或供货关系。

#### IQE 供应链安排

来源：[MACOM to Enter Agreements to Further Strengthen Supply Chain，2026-04-27](https://ir.macom.com/news-releases/news-release-details/macom-enter-agreements-further-strengthen-supply-chain)、[MACOM FY2026 Q3 官方结果，2026-08-06](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-third-quarter-2026-financial-results)

- `fact`：MACOM 明确把 IQE 称为重要供应商；FY2026 Q3 结果称对 IQE 的投资 recently completed。
- `forward-looking`：4 月公告中的长期外延服务协议是拟签安排，预期提高供应链韧性；不能因后续投资完成就自动把所有长期协议条款标为已经生效。
- `corporate narrative`：“强化供应链”是交易目的，不等于此前存在已量化短缺，也不等于卡点已经解决。
- `technical demo`：无。
- theme 候选：T016（供应保障动作）。公告覆盖多种技术的外延服务，不能在缺少明确字段时专门映射为 T007 的高速 InP 激光器约束。

### 7.3 纳入边界

MACOM 适合作为关键组件和供应链上游观察对象，而非光模块整机同业。技术展示、driver 可得性和外延供应安排应拆成不同 program，避免把器件发布推导为模块量产。

## 8. Credo（CRDO）

### 8.1 最近四个已披露季度

| slot_label | period_end | published_date | 官方材料 |
|---|---:|---:|---|
| FY2026 Q4 / FY | 2026-05-02 | 2026-06-01 | [Credo Reports Fourth Quarter and FY2026 Results](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Fourth-Quarter-and-Fiscal-Year-2026-Financial-Results/default.aspx) |
| FY2026 Q3 | 2026-01-31 | 2026-03-02 | [Credo Reports Third Quarter FY2026 Results](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Third-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx) |
| FY2026 Q2 | 2025-11-01 | 2025-12-01 | [Credo Reports Second Quarter FY2026 Results](https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-Second-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx) |
| FY2026 Q1 | 2025-08-02 | 2025-09-03 | [Credo Reports First Quarter FY2026 Results](https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-First-Quarter-of-Fiscal-Year-2026-Financial-Results/) |

### 8.2 近十二个月事件候选

#### 800G ZeroFlap 光收发器

来源：[Credo Launches 800G ZeroFlap Optical Transceivers，2026-03-17](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Launches-800G-ZeroFlap-Optical-Transceivers-Engineered-for-AI-Networks/default.aspx)

- `fact`：公司宣布 800G 2×DR4 ZeroFlap transceiver general availability / available now。GA 不等于规模出货或客户认证完成。
- `corporate narrative / technical claim`：遥测、故障定位、避免 link flap、可靠性和功耗效果均为公司主张。
- `forward-looking`：面向 AI 网络的部署价值不等于已经部署。
- `technical demo`：公告未提供独立客户部署或现场测试锚点。
- theme 候选：T004；对 T003 只能作为产品可得性旁证，不能作为产能、客户认证或稳定交付证据。

#### Cardinal 1.6T 光 DSP

来源：[Credo Introduces Cardinal 1.6T Optical DSP Family，2026-03-17](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Introduces-Cardinal-A-LowPower-1-6T-Optical-DSP-Family-Engineered-for-MassiveScale-AI-Fabrics/default.aspx)

- `fact`：Credo 发布第二代 1.6T、3nm、224G/lane DSP 产品族，覆盖 full-retimed 和 LRO 架构。
- `corporate narrative / technical claim`：LRO 低于 15W、低时延与可靠性等为第一方技术规格。
- `forward-looking`：面向 massive-scale AI fabrics 的价值与后续采用属于未来商业判断。
- `technical demo`：无特定模块厂或客户量产证据。
- theme 候选：T010 的上游 DSP 子环节、T004；不得推导特定模块厂采用。

补充观察：[TensorWave and Credo，2026-02-25](https://investors.credosemi.com/news-events/news/news-details/2026/TensorWave-Partners-with-Credo-to-Power-Next-Generation-AMD-Based-AI-Clusters/)称 TensorWave `will deploy` ZeroFlap AEC and Optics。这是具名客户的 `forward-looking adoption`，不是已部署事实；AEC 与 optics 未拆量，只能邻接 T018/T019，不能换算光模块数量。

### 8.3 纳入边界

Credo 同时覆盖 AEC、DSP 和光收发器，因此事件必须保留产品类型。AEC 客户采用不能自动转化为光模块需求，DSP 发布也不能自动转化为模块量产。

## 9. 建议的录入顺序

1. 先把六家公司加入 `universe.csv` 的季度覆盖池，并只录入本文件列出的 24 个官方季度槽位；材料类型统一从官方 earnings release / results material 起步。
2. 再把 12 个月事件作为独立 disclosure 进入候选队列，逐条保留发布者、主体、产品形态、原文锚点、披露时间和复核时间。
3. 事件进入主雷达前，必须按现有规则完成 anchor review。公司官网单边公告只能形成 `asserted`；具名客户出现在供应商公告中也不自动视为独立 counterparty evidence。
4. 对 `sampling / general availability / shipping / volume production / planned demo / completed trial` 使用不同 lifecycle stage，不用“已推出”一个词覆盖全部状态。
5. 先使用现有 T001–T020 的候选映射；若形态差异无法表达，例如 coherent 1.6T 与 datacom 1.6T 被迫落到同一主题，则创建 novel theme candidate，而不是错误归并。
6. 不从这些披露自动生成海外公司与国内产业链节点的合作、供货、竞争或替代关系。后续关系层需独立双边证据。

## 10. 预期新增的信息价值

- Broadcom、Marvell、Credo 可交叉观察同一代际中 switch / SerDes / DSP / AEC / optics 的不同商业阶段，减少只看模块厂的单点偏差。
- Nokia、Ciena 可补充 coherent DCI、系统部署和客户侧试验，但必须与短距 datacom pluggable 分开。
- MACOM 可观察 driver、TIA、CW laser 和外延供应保障，使“组件可得”与“模块产能”不再混为一个卡点。
- 六家公司共同覆盖技术可行性、sampling/GA、产能动作和客户采用四类证据，但目前材料仍不足以自动证明任何国内公司的技术稀缺性、不可替代性或直接供应关系。

## 附录 A：24 个季度 source 的可落库字段

以下 `material_type` 均为 `earnings_release`；URL 是公司 IR/官网正式结果页。ID 仅是建议，真正落库时仍应由维护者检查是否与现有 `source_id` 冲突。

```csv
source_id,company_id,slot_label,period_end,material_type,url,published_date
S_AVGO_2026Q2,AVGO,FY2026Q2,2026-05-03,earnings_release,https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2026-financial,2026-06-03
S_AVGO_2026Q1,AVGO,FY2026Q1,2026-02-01,earnings_release,https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial,2026-03-04
S_AVGO_2025Q4,AVGO,FY2025Q4,2025-11-02,earnings_release,https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2025,2025-12-11
S_AVGO_2025Q3,AVGO,FY2025Q3,2025-08-03,earnings_release,https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2025-financial,2025-09-04
S_MRVL_2027Q1,MRVL,FY2027Q1,2026-05-02,earnings_release,https://investor.marvell.com/news-events/press-releases/detail/1023/marvell-technology-inc-reports-first-quarter-of-fiscal-year-2027-financial-results,2026-05-27
S_MRVL_2026Q4,MRVL,FY2026Q4,2026-01-31,earnings_release,https://investor.marvell.com/news-events/press-releases/detail/1011/marvell-technology-inc-reports-fourth-quarter-and-fiscal-year-2026-financial-results,2026-03-05
S_MRVL_2026Q3,MRVL,FY2026Q3,2025-11-01,earnings_release,https://investor.marvell.com/news-events/press-releases/detail/999/marvell-technology-inc-reports-third-quarter-of-fiscal-year-2026-financial-results,2025-12-02
S_MRVL_2026Q2,MRVL,FY2026Q2,2025-08-02,earnings_release,https://investor.marvell.com/news-events/press-releases/detail/989/marvell-technology-inc-reports-second-quarter-of-fiscal-year-2026-financial-results,2025-08-28
S_NOK_2026Q2,NOK,2026Q2,2026-06-30,earnings_release,https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/,2026-07-23
S_NOK_2026Q1,NOK,2026Q1,2026-03-31,earnings_release,https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/,2026-04-23
S_NOK_2025Q4,NOK,2025Q4,2025-12-31,earnings_release,https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/,2026-01-29
S_NOK_2025Q3,NOK,2025Q3,2025-09-30,earnings_release,https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/,2025-10-23
S_CIEN_2026Q2,CIEN,FY2026Q2,2026-05-02,earnings_release,https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-Second-Quarter-2026-Financial-Results/default.aspx,2026-06-04
S_CIEN_2026Q1,CIEN,FY2026Q1,2026-01-31,earnings_release,https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-First-Quarter-2026-Financial-Results-03-05-2026/default.aspx,2026-03-05
S_CIEN_2025Q4,CIEN,FY2025Q4,2025-11-01,earnings_release,https://investor.ciena.com/news/news-details/2025/Ciena-Reports-Fiscal-Fourth-Quarter-2025-and-Year-End-Financial-Results-12-11-2025/default.aspx,2025-12-11
S_CIEN_2025Q3,CIEN,FY2025Q3,2025-08-02,earnings_release,https://investor.ciena.com/news/news-details/2025/Ciena-Reports-Fiscal-Third-Quarter-2025-Financial-Results-09-04-2025/default.aspx,2025-09-04
S_MTSI_2026Q3,MTSI,FY2026Q3,2026-07-03,earnings_release,https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-third-quarter-2026-financial-results,2026-08-06
S_MTSI_2026Q2,MTSI,FY2026Q2,2026-04-03,earnings_release,https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-second-quarter-2026-financial-results,2026-05-07
S_MTSI_2026Q1,MTSI,FY2026Q1,2026-01-02,earnings_release,https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-first-quarter-2026-financial-results/,2026-02-05
S_MTSI_2025Q4,MTSI,FY2025Q4,2025-10-03,earnings_release,https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-fourth-quarter-and-fiscal-year-2025/,2025-11-06
S_CRDO_2026Q4,CRDO,FY2026Q4,2026-05-02,earnings_release,https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Fourth-Quarter-and-Fiscal-Year-2026-Financial-Results/default.aspx,2026-06-01
S_CRDO_2026Q3,CRDO,FY2026Q3,2026-01-31,earnings_release,https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Third-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx,2026-03-02
S_CRDO_2026Q2,CRDO,FY2026Q2,2025-11-01,earnings_release,https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-Second-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx,2025-12-01
S_CRDO_2026Q1,CRDO,FY2026Q1,2025-08-02,earnings_release,https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-First-Quarter-of-Fiscal-Year-2026-Financial-Results/,2025-09-03
```

## 附录 B：首批六条事件 fixture

短引均少于 25 个英文单词。`anchor` 使用网页内稳定章节或段首，而不是搜索结果行号。它们均需再次人工 anchor review，默认状态只能是 `asserted`。

| company | published_date | disclosure / content | statement_kind | event_category / stage | themes | 原文短引与 anchor |
|---|---:|---|---|---|---|---|
| AVGO | 2026-03-11 | `official_release / technical_disclosure` | `fact_assertion` | `product_stage / sampling` | T010; T011 | “Broadcom has begun sampling its Taurus BCM83640 to its early access customers and partners.” — `Availability > paragraph 1`，[来源](https://investors.broadcom.com/news-releases/news-release-details/broadcom-delivers-industrys-first-400glane-optical-dsp-next) |
| MRVL | 2026-04-22 | `official_release / commercial_disclosure` | `fact_assertion` | `capital_relationship / not_applicable` | T011; T017 | “today announced the acquisition of Polariton Technologies” — `lead paragraph beginning SANTA CLARA`，[来源](https://investor.marvell.com/news-events/press-releases/detail/1020/marvell-announces-acquisition-of-polariton-technologies-advancing-optical-performance-scaling-to-3-2t-and-beyond) |
| NOK | 2025-10-23 | `regulatory_filing / commercial_disclosure` | `fact_assertion` | `commercial_adoption / first_shipment` | T004; T019 | “became generally available and have started shipping to a large US customer.” — `JUSTIN HOTARD…ON Q3 2025 RESULTS > Network Infrastructure paragraph`，[来源](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/) |
| CIEN | 2026-03-31 | `official_release / demonstration_disclosure` | `technical_demo` | `product_stage / demonstrated` | T010 | “Recent trial successfully transmitted 1.6 Tb/s line rate on a single optical channel across Vi’s two data centers” — `summary bullet 2`，[来源](https://investor.ciena.com/news/news-details/2026/Vodafone-Idea-Deploys-Cienas-WaveLogic-6-Extreme-to-Deliver-High-Capacity-Connectivity-03-31-2026/default.aspx) |
| MTSI | 2026-03-17 | `official_release / commercial_disclosure` | `fact_assertion` | `product_stage / announced` | T004; T011 | “today announced the availability of its new 448G PAM4 modulator drivers” — `lead paragraph beginning LOWELL`，[来源](https://ir.macom.com/news-releases/news-release-details/macom-announces-two-new-448g-lane-drivers-32t-data-center/) |
| CRDO | 2026-03-17 | `official_release / commercial_disclosure` | `fact_assertion` | `product_stage / announced` | T004 | “today announced the general availability of its revolutionary 800G 2 x DR4 ZeroFlap (ZF) transceiver products.” — `lead paragraph beginning SAN JOSE`，[来源](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Launches-800G-ZeroFlap-Optical-Transceivers-Engineered-for-AI-Networks/default.aspx) |

实现注意：现有 lifecycle 枚举没有 `general_availability`。MTSI/CRDO 暂用 `announced` 并在 notes 明确 GA，不能擅自升级为 `volume_order / first_shipment / ramping / scaled`。CIEN 是 coherent DCI 试验，不是 datacom 1.6T module。NOK 的客户未具名，不得创建猜测实体或关系。

### 实际落库取舍（2026-08-11）

首批实现中，MRVL 没有采用上表的 Polariton 收购候选，而采用公司 2026-03-12 对 Ara
1.6T 光 DSP 的 “Now shipping in mass volume to global customers” 披露，以便直接观察产品
商业阶段。该事件仍为 `first_party / asserted`；`scaled` 只复述公司自述的阶段，不代表客户
独立确认。NOK 与 CIEN 统一映射到新增相干光主题 T021，避免与短距数通模块混并。

## 11. 季度深挖（2026-08-11）

### 11.1 范围、材料权限与禁止提升

本轮逐一复核 AVGO、MRVL、NOK 已登记的最近四个季度，共 12 个公司 IR/正式季度结果页面，并检查公司 IR 是否提供官方书面逐字稿或准备稿。Broadcom 和 Marvell 的 IR 仅提供公司季度结果、SEC furnished material 和电话会 webcast/replay 入口，未找到可稳定引用的公司官方书面逐字稿；因此没有使用 webcast 音频的第三方转录。Nokia 的正式季度页面本身包含 CEO 书面结果评论、指引和产能事项，直接按公司正式披露处理。

本节把陈述分成三类：

- `fact`：公司报告已经发生的收入、订单、出货、协议或当期状态。它仍是公司第一方 `asserted`，不等于客户或产线独立验证。
- `forward_looking`：包含 `expect / will / on track / starting / before` 等未来期限或目标的陈述。
- `corporate_narrative`：公司对需求驱动、市场机会、产品组合贡献或行业约束的解释，不能单独证明数量、因果或行业普遍状态。

两类信息一律不得提升：

1. Broadcom/Marvell 的 safe-harbor 或监管风险因素中写到供应链中断、组件短缺或供应商依赖，只能证明公司识别了风险，不能证明该季度实际发生光学短缺。
2. 聚合的 `AI semiconductor / AI networking / data center` 收入、bookings 或增长不能拆成 optical DSP、光模块、CPO/NPO 或某一代际产品的收入与数量。

以下 anchor 使用页面标题、CEO quote 段首或正式小节名称；短引只保留落库所需的 8–20 个词。

### 11.2 Broadcom（AVGO）：四季度只有需求邻接，没有季度光学事实

| 季度/source | 原子陈述与短引 | 分类与主题候选 | 不可推导边界 |
|---|---|---|---|
| FY2025 Q3 / `S_AVGO_2025Q3` | 公司报告 Q3 AI revenue 同比增长 63% 至 52 亿美元，并把当季表现与 custom AI accelerators、networking 和 VMware 一并关联。短引：“Q3 AI revenue growth accelerated to 63% year-over-year to $5.2 billion.” [官方结果](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2025-financial)，anchor：`CEO quote beginning “Broadcom achieved record third quarter revenue”`。 | `fact`（聚合指标）+ `corporate_narrative`；最多邻接 T018。 | 没有 optical、DSP、400G/lane、800G/1.6T 或 CPO/NPO 分项；不得写成光学收入或出货增长。 |
| FY2025 Q4 / `S_AVGO_2025Q4` | 公司报告 Q4 AI semiconductor revenue 同比增长 74%，并预计 Q1 由 custom accelerators 与 Ethernet AI switches 驱动继续增长。短引：“AI semiconductor revenue increasing 74% year-over-year.” [官方结果](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2025)，anchor：`CEO quote beginning “In Q4, record revenue”`。 | `fact`（当季聚合增长）+ `forward_looking`（Q1 预测）；T018。 | Ethernet switch 不是光模块；当季实际值也未拆出 networking 或 optics。 |
| FY2026 Q1 / `S_AVGO_2026Q1` | 公司报告 Q1 AI revenue 为 84 亿美元、同比增长 106%，并称由 custom AI accelerators 和 AI networking 需求驱动。短引：“driven by robust demand for custom AI accelerators and AI networking.” [官方结果](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial)，anchor：`CEO quote beginning “Broadcom achieved record first quarter revenue”`。 | `corporate_narrative`；T018。 | `AI networking` 没有拆成交换 ASIC、SerDes、光 DSP 或 CPO；不应映射 T021，也不能与 Taurus sampling 自动合并。 |
| FY2026 Q2 / `S_AVGO_2026Q2` | 公司报告 Q2 AI semiconductor revenue 为 108 亿美元、同比增长 143%，并再次归因于 custom accelerators 与 AI networking。短引：“driven by increasing demand for custom AI accelerators and AI networking.” [官方结果](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2026-financial)，anchor：`CEO quote beginning “Broadcom achieved record revenue”`。 | `corporate_narrative`；T018。 | 与 Q1 同样是聚合口径；不能据此证明 Taurus 已由 sampling 进入 qualification、量产或客户部署。 |

结论：四个季度均检出 AI/networking 邻接信号，但**未检出可提升为光学产品阶段或光学收入的季度事实**。Taurus 400G/lane DSP sampling 仍只由独立的 2026-03-11 产品公告支持，不能倒灌到季度 revenue。

### 11.3 Marvell（MRVL）：两个季度可用、两个季度不应凑 claim

| 季度/source | 原子陈述与短引 | 分类与主题候选 | 不可推导边界 |
|---|---|---|---|
| FY2026 Q2 / `S_MRVL_2026Q2` | CEO 称公司增长由 custom silicon 与 electro-optics 产品的强劲 AI 需求共同推动。短引：“strong AI demand for our custom silicon and electro-optics products.” [官方结果](https://investor.marvell.com/news-events/press-releases/detail/989/marvell-technology-inc-reports-second-quarter-of-fiscal-year-2026-financial-results)，anchor：`CEO quote beginning “Marvell delivered record revenue”`。 | `corporate_narrative`；T018，可作为 T021 的邻接观察但不直接映射。 | 未披露 electro-optics 的收入、速率代际、客户或出货阶段；不能写成 800G/1.6T 放量事实。 |
| FY2026 Q3 / `S_MRVL_2026Q3` | 结果只说 strong demand for data center products，并讨论 Celestial AI 收购。 [官方结果](https://investor.marvell.com/news-events/press-releases/detail/999/marvell-technology-inc-reports-third-quarter-of-fiscal-year-2026-financial-results)，anchor：`CEO quote beginning “Marvell delivered record third-quarter revenue”`。 | **未检出可提升事实**；材料范围为正式季度结果和 CEO 书面引言。 | `data center products` 未拆产品，收购路线也不是当季 optical 出货；不凑 claim。 |
| FY2026 Q4 / `S_MRVL_2026Q4` | 结果只报告 robust AI demand、data center strength、bookings 和创纪录 design wins。 [官方结果](https://investor.marvell.com/news-events/press-releases/detail/1011/marvell-technology-inc-reports-fourth-quarter-and-fiscal-year-2026-financial-results)，anchor：`CEO quote beginning “Marvell delivered record fiscal 2026 revenue”`。 | **未检出可提升事实**；材料范围为正式季度结果和 CEO 书面引言。 | 无 optics、DSP、800G/1.6T、NPO/CPO 或 DCI 产品拆分；不得把总体 design wins 记为光学客户认证。 |
| FY2027 Q1 / `S_MRVL_2027Q1` | 公司称看到 exceptional AI-related bookings，并把改善后的展望归因于一组产品需求，其中明确包括 800G/1.6T scale-out optics、NPO/CPO 和 DCI。短引：“strong demand across a broad set of Marvell solutions, including 800G and 1.6T scale-out optics.” [官方结果](https://investor.marvell.com/news-events/press-releases/detail/1023/marvell-technology-inc-reports-first-quarter-of-fiscal-year-2027-financial-results)，anchor：`CEO quote lines beginning “We are seeing exceptional AI-related bookings”`。 | `corporate_narrative`；T021，NPO/CPO 邻接 T017。 | bookings 是 AI 组合层，公告未按产品拆量；不得把列表中的每一项都视为独立订单、客户采用或规模出货。 |

跨季度能确认的是**披露颗粒度变化**：FY2026 Q2 提到 electro-optics，Q3/Q4 回到泛 data-center/AI，FY2027 Q1 才重新明确列出 optics/NPO/CPO/DCI。不能仅凭披露变详细推导需求从无到有或突然加速。

### 11.4 Nokia（NOK）：产品、订单、约束与产能时间线均有可落库原子陈述

#### 2025 Q3 / `S_NOK_2025Q3`

- `fact`：800G ZR/ZR+ coherent pluggables 已 GA，并开始向一家未具名美国大型客户发货。短引复用附录 B 的同源原文，避免重复引用；[官方结果](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/)，anchor：`JUSTIN HOTARD…ON Q3 2025 RESULTS > Network Infrastructure paragraph`；主题 T021，事件阶段 `first_shipment`。
- `forward_looking`：公司称将在 2026 年底前于 San Jose 开设第二座 InP semiconductor fab。短引：“second Indium Phosphide semiconductor fabrication facility in San Jose.” 同源同 anchor；主题 T008。
- 边界：客户未具名，不得创建猜测实体；GA/首个客户发货不证明广泛采用。新 fab 是计划，不是已具备有效产能。

#### 2025 Q4 / `S_NOK_2025Q4`

- `fact`：Optical Networks 当季增长 17%，Optical/IP order intake 强、book-to-bill 高于 1，公司将其归因于 AI & Cloud demand。短引：“Order intake was strong across Optical and IP Networks.” [官方结果](https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/)，anchor：`JUSTIN HOTARD…ON Q4 AND FULL YEAR 2025 RESULTS > Network Infrastructure paragraph`；主题 T021。
- `forward_looking`：2026 capex 预计为 9–10 亿欧元，较高支出主要与支持 Optical Networks 增长的新增制造能力相关。短引：“investments in additional manufacturing capacity to support the growth outlook in Optical Networks.” 同源，anchor：`OUTLOOK > Capital expenditures`；主题 T008。
- 边界：订单组合没有拆成 coherent pluggables、line systems 或 components；capex 包含其他项目，不能全额换算为 InP 产能。

#### 2026 Q1 / `S_NOK_2026Q1`

- `fact`：公司称当季赢得一批 AI & Cloud design wins 与订单，明确覆盖 pluggables 和 line systems。短引：“pluggables and line systems.” [官方结果](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/)，anchor：`JUSTIN HOTARD…ON Q1 2026 RESULTS > Network Infrastructure paragraph`；主题 T021；因未披露订单数量，不升级为 `volume_order`。
- `corporate_narrative`：公司称供应链需求加速、lead times 延长。短引：“lead times are extending.” 同源，anchor：`CEO results quote > paragraph beginning “At our Capital Markets Day”`；仅作为未分解约束观察，不映射到具体器件卡点。
- `forward_looking`：四款新 DSP 所带动的 13 项方案预计 2027 年中开始 sampling，2027 年下半年开始 volume production。短引：“Products will begin sampling in mid-2027.” 同源，anchor：`CEO results quote > paragraph beginning “At the OFC optical conference”`；主题 T021；sampling 与 volume production 应拆为两个承诺里程碑。
- `forward_looking`：San Jose 新 InP fab 按计划将在 2026 年稍晚开始爬坡。短引：“begin ramping production later this year.” 同源，anchor：`CEO results quote > paragraph beginning “Our new indium phosphide”`；主题 T008。
- 边界：13 项方案的功耗/TCO 是公司主张；design wins/orders 没有客户、金额或模块数量；“lead times extending”不能定位到 InP、DSP、封装或测试中的某一节点。

#### 2026 Q2 / `S_NOK_2026Q2`

- `fact`：AI & Cloud order intake 为 28 亿欧元，公司称已在 Optical Networks 和 IP Networks 获得长期订单。短引：“long-term orders.” [官方结果](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/)，anchor：`Justin Hotard CEO quote > Q2 AI & Cloud order intake paragraph`；主题 T021。
- `corporate_narrative`：管理层称 supply 仍是主要行业约束，并称这促使客户下更长期订单。短引：“main industry constraint.” 同源同 anchor；建议保持 `unmapped`，名称可用“光网络供应约束（组件未分解）”。
- `forward_looking`：San Jose fab 的爬坡窗口进一步收窄至 2026 Q4 后段。短引：“ramping production later in Q4 2026.” 同源，anchor：`ADDITIONAL TOPICS > Nokia acquires further U.S. optical manufacturing capacity`；主题 T008。
- `forward_looking`：公司宣布将从 2026 Q3 起把 Pennsylvania advanced test/packaging capacity 提高 10 倍。短引：“test and packaging capacity ... by 10x.” 同源同 anchor；主题 T008，但这是启动窗口，不是已完成 10 倍扩容。
- `fact + forward_looking`：Nokia 已签 definitive agreement 收购 NXP Chandler fab；计划 2027 年初先租用部分产能并改造为 optical-components InP，完整收购预计 2029 Q1 完成。短引：“definitive agreement to acquire.” 同源同 anchor；主题 T008。
- 边界：28 亿欧元和“约一半十二个月内转收入”均是 Optical+IP+其他 AI & Cloud 的组合口径；行业 supply 约束没有节点拆分；美国 fab/test-pack 动作是计划或交易状态，不证明当前有效产能、良率或成本。

### 11.5 跨季度变化与承诺候选

1. **Broadcom**：聚合 AI revenue 从 FY2025 Q3 的 52 亿美元继续上升到 FY2026 Q1 的 84 亿和 Q2 的 108 亿，但口径始终混合 accelerator/networking，未形成可跟踪的光学承诺。Taurus sampling 应继续作为 interquarter event 单独跟踪。
2. **Marvell**：季度书面披露从 FY2026 Q2 的 `electro-optics` 泛化到 Q3/Q4 的 data-center/AI，再在 FY2027 Q1 具体列出 800G/1.6T optics、NPO/CPO、DCI。可确认的是管理层披露范围扩大，不是单项产品数量或客户采用跃迁。
3. **Nokia**：Q3 2025 已有 800G coherent pluggable GA/首个匿名客户发货；Q1 2026 增加 pluggables/line-systems orders 和下一代 DSP 产品时间表；Q2 2026 则把 supply constraint 与多处美国制造扩容窗口写得更具体。它说明公司在以产能投资响应需求，但卡点是否缓解仍需产线实际投产、良率、交付和客户侧确认。

建议进入 `commitments.csv` 或承诺观察队列的项目：

| commitment candidate | 首次/最新证据 | 目标窗口 | 截至 2026-08-11 状态 | 验证所需事实 |
|---|---|---|---|---|
| `NOK_SAN_JOSE_INP_RAMP` | 首见 2025 Q3；2026 Q1 重申；2026 Q2 收窄至 later Q4 2026 | 2026 Q4 | `pending` | 官方确认开始生产，而非仅厂房完成；最好补产能/良率或出货用途。 |
| `NOK_NEXTGEN_OPTICAL_SAMPLING` | 2026 Q1 | mid-2027 | `pending` | 官方 sampling 开始及产品/客户范围。 |
| `NOK_NEXTGEN_OPTICAL_VOLUME` | 2026 Q1 | 2027 H2 | `pending` | 官方 volume production 开始，且不能只用 sampling 兑现。 |
| `NOK_PA_TEST_PACK_EXPANSION_START` | 2026 Q2 | starting 2026 Q3 | `pending` | 扩产工程实际启动；“10x”最终能力另设完成指标。 |
| `NOK_ARIZONA_LEASE_AND_CONVERSION` | 2026 Q2 | early 2027 lease；转换期未披露 | `pending` | 租赁生效、实际改造启动及 InP 生产节点。 |
| `NOK_ARIZONA_ACQUISITION_CLOSE` | 2026 Q2 | 2029 Q1 | `pending` | 监管批准与交易完成。 |

### 11.6 可直接落库的 claim fixture

下表只列适合当前 legacy `claims.csv` 的 management `fact / forward_looking`；`corporate_narrative` 由于 legacy schema 没有该枚举，应放入 event claim 层或仅保留在研究底稿，不得伪装成 `fact`。ID 为建议值，落库前需检查冲突。

| 建议 claim_id | source_id | speaker | statement_type | event_type | side | theme | quote / anchor | summary |
|---|---|---|---|---|---|---|---|---|
| `CL_NOK_2025Q3_800G_SHIP` | `S_NOK_2025Q3` | Justin Hotard | `fact` | `first_shipment` | `both` | T021 | 见 11.4 对应短引 / `CEO Q3 results > Network Infrastructure` | Nokia 称 800G ZR/ZR+ 已 GA 并开始向一家未具名美国大型客户发货。 |
| `CL_NOK_2025Q3_INP_FAB` | `S_NOK_2025Q3` | Justin Hotard | `forward_looking` | `announced` | `supply` | T008 | 见 11.4 对应短引 / 同上 | Nokia 计划在 2026 年底前于 San Jose 开设第二座 InP fab。 |
| `CL_NOK_2025Q4_OPTICAL_ORDER` | `S_NOK_2025Q4` | Justin Hotard | `fact` | `announced` | `demand` | T021 | 见 11.4 对应短引 / `CEO Q4 results > Network Infrastructure` | Nokia 称 Optical/IP order intake 强且 book-to-bill 高于 1；未拆产品数量。 |
| `CL_NOK_2026Q1_PLUGGABLE_ORDERS` | `S_NOK_2026Q1` | Justin Hotard | `fact` | `announced` | `demand` | T021 | 见 11.4 对应短引 / `CEO Q1 results > Network Infrastructure` | Nokia 称当季获得 AI/Cloud pluggables 与 line systems 的 design wins 和订单。 |
| `CL_NOK_2026Q1_DSP_SAMPLE` | `S_NOK_2026Q1` | Justin Hotard | `forward_looking` | `sampling` | `both` | T021 | 见 11.4 对应短引 / `CEO Q1 results > OFC optical conference` | Nokia 预计下一代光网络方案 2027 年中开始 sampling。 |
| `CL_NOK_2026Q1_DSP_VOLUME` | `S_NOK_2026Q1` | Justin Hotard | `forward_looking` | `ramping` | `both` | T021 | 见同一 anchor；原文后半句，不在此重复 | Nokia 预计同批方案在 2027 年下半年开始 volume production。 |
| `CL_NOK_2026Q1_SJ_RAMP` | `S_NOK_2026Q1` | Justin Hotard | `forward_looking` | `ramping` | `supply` | T008 | 见 11.4 对应短引 / `CEO Q1 results > new indium phosphide facility` | Nokia 重申 San Jose 新 InP fab 将在 2026 年稍晚开始爬坡。 |
| `CL_NOK_2026Q2_LONG_ORDERS` | `S_NOK_2026Q2` | Justin Hotard | `fact` | `announced` | `demand` | T021 | 见 11.4 对应短引 / `CEO Q2 quote > AI & Cloud order intake` | Nokia 称已在 Optical/IP 获得长期订单；金额为组合口径。 |

仅观察、不直接落 legacy claim 的 fixture：AVGO 四季全部聚合 AI/networking 陈述；MRVL FY2026 Q2 和 FY2027 Q1 的产品组合需求解释；NOK Q1 `lead times extending` 与 Q2 `supply continues to be the main industry constraint`。此外，NOK Q4 capex、Q2 San Jose/PA/Arizona 产能事项由公司正式结果正文披露而非具名管理层短引，应该进入 event claim 层的 `corporate_disclosure / forward_looking`，不能为了通过 legacy schema 而伪装成 management。所有这些观察都不得作为行业卡点已被客观证实或已经解除的事实。

## 12. 其余公司四季度与官网材料深挖（2026-08-11）

### 12.1 结论与材料处理

本轮逐一复核 Ciena、MACOM、Credo 已登记的最近四个季度，共 12 个季度槽位；官网/IR、公司托管的电话会 transcript 与 SEC 原始申报是唯一证据权限。结果不是“每家公司都凑四条 claim”：

- **Ciena 四季均有可落 legacy 的管理层事实或前瞻**，且存在连续的“初始收入出货—追加集群/首单—供应约束影响收入”链，是本批最高价值公司。
- **MACOM 四份 earnings release 均没有光学特指**，应明确标为 `no_relevant_claims`。另行复核 SEC 10-Q 后可以观察 Data Center 光学相关产品驱动和 IQE 交易进展，但这些不是四份业绩稿里的管理层电话会 claim。
- **Credo 只有 FY2026 Q2 的产品爬坡前瞻适合提取；FY2026 Q3 只留 `corporate_narrative`；Q1、Q4 标为 `no_relevant_claims`**。产品公告显示 ZeroFlap 从 sampling 推进到特定 800G SKU 的 GA，但季度稿没有给出光学收入或规模出货。

Ciena 的现有 `S_CIEN_*` 行目前指向简短 earnings release；真正支撑下列管理层 claim 的是公司 IR 托管 transcript。若落库，应把四个季度槽位的 canonical legacy source **替换为 transcript**（`material_type=transcript`、URL 改为下表链接），不要让 claim 指向并不含原话的 earnings release，也不要新增第五个 `quarterly` source 破坏“四季度槽位”约束。业绩稿如仍需保留，可作为独立 disclosure，不承担 transcript claim 的 provenance。

### 12.2 十二个季度的精确处理状态

`review_scope` 以下给出可直接复制的建议文本。`anchor_reviewed` 表示检出了相关原子陈述；不代表陈述已被客户独立验证。`no_relevant_claims` 只表示指定业绩稿经指定范围复核后没有光学特定主张，不表示公司在其他材料中沉默。

| company / source | 建议处理材料 | processing_status | review_scope | 应保留的内容 |
|---|---|---|---|---|
| CIEN / `S_CIEN_2025Q3` | [官方托管 transcript](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q3/Transcript-Cienas-Fiscal-Third-Quarter-2025-Financial-Results-Conference-Call.pdf) | `anchor_reviewed` | `Gary Smith prepared remarks p.3；Scott McFeely Q&A p.14–15，复核 scale-across、400ZR+、pluggable shipment` | management `fact` + `forward_looking` |
| CIEN / `S_CIEN_2025Q4` | [官方托管 transcript](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q4/Cienas-Fiscal-4th-Quarter-and-Year-End-2025-Financial-Results-Conference-Call.pdf) | `anchor_reviewed` | `Gary Smith prepared remarks p.4；Marc Graff Q&A p.13–15，复核 WL6 Nano initial revenue 与 photonics constraint` | management `fact` |
| CIEN / `S_CIEN_2026Q1` | [官方托管 transcript](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) | `anchor_reviewed` | `Gary Smith prepared remarks p.3–5；Marc Graff prepared remarks/Q&A p.6–7，复核 hyperscaler orders、供应约束及产品时间表` | management `fact` + `forward_looking` |
| CIEN / `S_CIEN_2026Q2` | [官方托管 transcript](https://s25.q4cdn.com/550667411/files/content_files/Ciena-Fiscal-Q2-2026-Financial-Results-Call.pdf) | `anchor_reviewed` | `Gary Smith prepared remarks p.3–4；Marc Graff prepared remarks p.5，复核 Hyper-Rail order、coherent module win 与 supply-demand gap` | management `fact` + `forward_looking` |
| MTSI / `S_MTSI_2025Q4` | [官方业绩稿](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-fourth-quarter-and-fiscal-year-2025/) | `no_relevant_claims` | `Management Commentary、业绩稿正文按 optical/optics/coherent/800G/1.6T/data center 检索并通读` | 无；CEO 为泛化经营表述 |
| MTSI / `S_MTSI_2026Q1` | [官方业绩稿](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-first-quarter-2026-financial-results/) | `no_relevant_claims` | `Management Commentary、业绩稿正文按 optical/optics/coherent/800G/1.6T/data center 检索并通读` | 无；CEO 为泛化经营表述 |
| MTSI / `S_MTSI_2026Q2` | [官方业绩稿](https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-second-quarter-2026-financial-results) | `no_relevant_claims` | `Management Commentary、业绩稿正文按 optical/optics/coherent/800G/1.6T/data center 检索并通读` | 无；CEO 的 H2 增长展望未指向光学 |
| MTSI / `S_MTSI_2026Q3` | [SEC 官方 EX-99.1](https://www.sec.gov/Archives/edgar/data/1493594/000149359426000036/ex99_1earningsreleaseq3fy26.htm) | `no_relevant_claims` | `Management Commentary、业绩稿正文按 optical/optics/coherent/800G/1.6T/data center 检索并通读；IR 页面不可访问时由 SEC exhibit 核验同一业绩稿` | 无；不能把 10-Q 的产品收入解释倒灌为 CEO 电话会 claim |
| CRDO / `S_CRDO_2026Q1` | [官方业绩稿](https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-First-Quarter-of-Fiscal-Year-2026-Financial-Results/) | `no_relevant_claims` | `CEO quote 与业绩稿正文按 optical/optics/ZeroFlap/DSP/800G/1.6T 检索并通读` | 无；hyperscaler partnership 是公司整体口径 |
| CRDO / `S_CRDO_2026Q2` | [官方业绩稿](https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Technology-Group-Holding-Ltd-Reports-Second-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx) | `anchor_reviewed` | `Bill Brennan CEO quote 中 ZeroFlap Optics、ALC、OmniConnect upcoming ramps 句` | management `forward_looking`；产品组合混合 |
| CRDO / `S_CRDO_2026Q3` | [官方业绩稿](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Third-Quarter-of-Fiscal-Year-2026-Financial-Results/default.aspx) | `anchor_reviewed` | `Bill Brennan CEO quote 中 ZeroFlap optics、ALC、OmniConnect TAM expansion 句` | 只留 `corporate_narrative`，不落 legacy claim |
| CRDO / `S_CRDO_2026Q4` | [官方业绩稿](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Technology-Group-Holding-Ltd-Reports-Fourth-Quarter-and-Fiscal-Year-2026-Financial-Results/default.aspx) | `no_relevant_claims` | `CEO quote 与业绩稿正文按 optical/optics/ZeroFlap/DSP/800G/1.6T 检索并通读` | 无；vertical integration 未在该句中指向光学 |

汇总：`anchor_reviewed=6`，`no_relevant_claims=6`。不得把 MACOM 四季改成 `unprocessed`，也不得把 Credo Q3 的 TAM 叙事包装成订单或出货事实。

### 12.3 Ciena：可落 legacy 的原子短引与 anchor

以下每条短引均来自公司 IR 托管的电话会 transcript；客户均未具名，证据状态只能是第一方 `asserted`。

#### FY2025 Q3 / `S_CIEN_2025Q3`

- `fact`：Ciena 称 RLS 与 WL6 Nano 800G ZR 组成的首个 scale-across 项目已开始产生收入出货。短引：“Initial revenue shipments are underway.” anchor：`Gary Smith prepared remarks, p.3, paragraph beginning “The first is an industry-first project”`；`event_type=first_shipment`，`side=both`，主题 T021。
- `fact`：另一家 hyperscaler 首次下了 400ZR+ pluggable 大单。短引：“first large order for 400ZR+ pluggables.” 同页下一段；`event_type=announced`，`side=demand`，主题 T021。`large` 没有金额或数量，不应升级成 `volume_order`。
- `forward_looking`：首个项目预计未来数季爬坡到数亿美元。短引：“hundreds of millions of dollars.” 同页首个项目段落；`event_type=ramping`，主题 T021。`next several quarters` 没有精确截止日，当前 `commitments.csv` 只支持单一 `due_date`，不建议伪造日期。

#### FY2025 Q4 / `S_CIEN_2025Q4`

- `fact`：WL6 Nano 800G pluggable 已进入初始收入出货。短引：“shipped for initial revenue.” anchor：`Gary Smith prepared remarks, p.4, paragraph beginning “Across this full spectrum”`；`event_type=first_shipment`，主题 T021。
- `fact`：Ciena 报告 FY2025 pluggable revenue 超过 1.68 亿美元。短引：“more than $168 million.” 同页同段；`event_type=scaled` 仍不稳妥，建议用 `unknown`，因为这是全 pluggable 聚合收入，不是 800G 单品规模。
- `fact`：管理层把当期约束具体指向 photonics parts。短引：“constraint on the photonics parts.” anchor：`Marc Graff Q&A, p.13–15, supply discussion`；`event_type=unknown`，`side=supply`，主题 T016。不能继续推导为特定 laser、DSP、晶圆厂或国内供应商。

#### FY2026 Q1 / `S_CIEN_2026Q1`

- `fact`：三家 hyperscaler 均在爬坡，首个客户追加了多个集群订单。短引：“additional orders for multiple additional clusters.” anchor：`Gary Smith prepared remarks, p.3, hyperscaler scale-across paragraph`；`event_type=announced`，`side=demand`，主题 T021。订单没有客户名、金额或模块数量。
- `fact`：供应约束实际压低了 Q1 可实现收入。短引：“revenue ... higher but for these constraints.” anchor：`Marc Graff prepared remarks/Q&A, p.6–7, supply constraint discussion`；`event_type=unknown`，`side=supply`，主题 T016。管理层进一步指向 component vendors，但仍未识别具体组件。
- `forward_looking`：Vesta 样品窗口为 calendar Q2 2026。短引：“calendar Q2 2026.” anchor：`Gary Smith prepared remarks, p.5, Nubis/Vesta paragraph`；`event_type=sampling`，主题 T017。截至 2026-08-11，官网公告能证明产品发布和 OFC 展示，未找到明确“样品已交付”表述，因此状态应是 `not_observed`，不是 `fulfilled` 或 `delayed`。
- `forward_looking`：Hyper-Rail 预计 2026 年底开始标准化、2027 年爬坡。anchor：`Gary Smith prepared remarks, p.5, Hyper-Rail paragraph`；应拆为两个承诺，不能用 Q2 首单同时关闭标准化和规模爬坡。

#### FY2026 Q2 / `S_CIEN_2026Q2`

- `fact`：Ciena 获得首个 Hyper-Rail 多轨订单。短引：“first multi-rail order from a leading hyperscaler.” anchor：`Gary Smith prepared remarks, p.3, Hyper-Rail paragraph`；`event_type=announced`，主题 T021。`order` 不等于出货、GA 或收入确认。
- `fact`：Ciena 赢得一家大型 hyperscaler 的高性能 coherent module 项目。短引：“new win ... for our high-performance Coherent modules.” anchor：`Gary Smith prepared remarks, p.4, coherent modules paragraph`；`event_type=announced`，主题 T021。用途是 metro 与 long-haul DCI，不能写成短距 datacom 模块采用。
- `fact`：Ciena 另获一家大型 switch OEM 的 WL5/WL6 Nano pluggable 首胜。短引：“first win with a major switch OEM.” 同页 pluggable paragraph；`event_type=announced`，主题 T021。客户未具名且没有数量。
- `fact`：供应仍未跟上需求。anchor：`Marc Graff prepared remarks, p.5, backlog and supply paragraph`；`event_type=unknown`，`side=supply`，主题 T016。77 亿美元 backlog 是公司总体口径，不得换算成光模块 backlog。

#### 跨季度变化

`Q3 初始收入出货与首个 400ZR+ 大单 → Q4 WL6 Nano 800G 初始收入、更多云厂商测试认证 → Q1 三家 hyperscaler 爬坡且首客追加多集群订单 → Q2 Hyper-Rail 首单、coherent module hyperscaler win 与 switch-OEM win`

与此同时，约束链没有关闭：`Q4 photonics parts 被点名 → Q1 约束已压低可实现收入 → Q2 supply 仍追不上 demand`。这足以把“高速光学组件组合约束”继续保留为候选卡点，但不足以认定某个具体器件是唯一关键节点，更不能认定该卡点已被某家公司成熟解决。

### 12.4 MACOM：业绩稿应留空，SEC 与 IQE 事件单独建链

四份 earnings release 的 CEO 引语都只是整体执行、增长与盈利表述，**不生成 legacy management claim**。但 SEC 原始申报提供了两个有价值的研究观察：

1. [FY2026 Q3 10-Q](https://www.sec.gov/Archives/edgar/data/1493594/000149359426000038/mtsi-20260703.htm)把当季 Data Center 收入同比增长的主要驱动指向 100G–1.6T optical Data Center products。它说明光学相关产品参与了增长，但 Data Center 收入口径仍包含其他产品，不能写成纯光学收入，也不能证明 MACOM 出售完整光模块。
2. 2026-04-27 [MACOM 官方公告](https://ir.macom.com/node/21106/pdf)称拟向 IQE 投资 4,500 万英镑并订立覆盖多种技术的长期外延服务协议；[FY2026 Q3 10-Q](https://www.sec.gov/Archives/edgar/data/1493594/000149359426000038/mtsi-20260703.htm)在 `Note 4 — Investments > Long-Term Investments` 明确确认：投资、可转债与长期供应协议已于 **2026-05-28 完成/订立**。因此“预计 FY2026 Q3 完成”的公司披露已有后续官方季度锚，但只能关闭交易/签约节点，不能证明供给已经增加、成本下降或光学卡点解除。

另有独立对手方来源：[IQE FY2025 结果公告](https://www.iqep.com/media/press-releases/2026/full-year-2025-results/)同日确认 MACOM 的 4,500 万英镑战略投资，并明确称双方已订立长期供应协议。MACOM 申报与 IQE 官网属于两个不同 origin，可把“投资完成”和“协议订立”两个事件由单方 `asserted` 提升到 `corroborated`；但双方仍未披露实际晶圆量、技术份额、交付、良率或价格，所以不能把“供应效果”一并提升。

IQE 事件的精确边界：协议写的是 `epitaxial services spanning multiple technologies`，未披露 InP、GaAs、GaN 各自份额，也未说明光学产品对应的产能、晶圆量、良率或交付时间。不得把它专门映射为 T007 高速 InP 激光器约束的解决证据。

**建议新增 `supply_chain_arrangement` event category。** 理由是 IQE 同一披露同时包含资本投资和已签长期供应协议：只用 `capital_relationship` 会丢失最重要的供应保障语义。建议从同一 origin 拆成两个 event：

- `capital_relationship / not_applicable`：2026-05-28 投资完成；
- `supply_chain_arrangement / not_applicable`：2026-05-28 长期供应协议已订立。

该新类别只接受明示的 LTSA、capacity reservation、长期采购或正式第二供应源协议；普通 supplier 称呼、风险因素或采购意向不入列。它仍只是 event，不自动生成 canonical 供货关系，也不等于有效产能、实际采购或卡点缓解。当前 lifecycle 无需为了单例再加 `signed/active`；执行事实写入 `occurred_start` 与 summary，`event_status` 仍表示证据状态而非交易完成状态。

### 12.5 Credo：季度前瞻弱，产品阶段变化更有价值

#### 季度材料

- FY2026 Q1：CEO 所称 hyperscaler/key-customer partnership 是公司整体口径，没有 ZeroFlap、DSP 或光学收入锚，标 `no_relevant_claims`。
- FY2026 Q2：唯一可提取的 management forward-looking 是 “upcoming ramps ... ZeroFlap Optics, ALCs, and OmniConnect gearbox solutions”，anchor：`Bill Brennan CEO quote, paragraph beginning “Our strong Q2 results”`。若落 legacy，可用 `event_type=ramping`、`side=both`、主题 T004，但 notes 必须注明三类产品混合，不能把后续总收入增长归因给 ZeroFlap。
- FY2026 Q3：管理层所称三项 multi-billion-dollar TAM expansion 只证明公司扩展产品叙事，不证明订单、客户采用或出货；放 event claim 层的 `corporate_narrative`，不落 legacy。
- FY2026 Q4：vertical integration 是公司总体表述且未在该句中指向 optics，标 `no_relevant_claims`。

#### 只保留三个高价值状态变化

1. **ZeroFlap sampling → 特定 800G SKU GA。** [2025-10-13 产品公告](https://investors.credosemi.com/news-events/news/news-details/2025/Credo-Unveils-ZeroFlap-Optical-Transceivers--A-Reliability-Revolution-for-Optics-in-AI-Networks/default.aspx)称 400G/800G/1.6T ZeroFlap 产品族 “now sampling”；[2026-03-17 公告](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Launches-800G-ZeroFlap-Optical-Transceivers-Engineered-for-AI-Networks/default.aspx)仅能把 800G 2×DR4 SKU 提升到 GA。不能把 400G/1.6T 一并升级，也不能把 GA 写成规模出货。
2. **Cardinal 1.6T DSP sampling。** [2026-03-17 公告](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Introduces-Cardinal-A-LowPower-1-6T-Optical-DSP-Family-Engineered-for-MassiveScale-AI-Fabrics/default.aspx)称产品正向主要客户送样；状态为 `product_stage / sampling / asserted`。低功耗与可靠性是供应商技术主张，不是客户验证。
3. **DustPhotonics 收购完成。** [2026-04-13 收购公告](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Agrees-to-Acquire-DustPhotonics-Accelerating-Expansion-into-Silicon-Photonics-and-Next-Generation-Optical-Connectivity/default.aspx)提出硅光垂直整合和 FY2027 光学组合收入超过 5 亿美元的预测；[2026-05-28 完成公告](https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Completes-Acquisition-of-DustPhotonics/default.aspx)只关闭收购事件。收入预测覆盖 transceiver、DSP 与 silicon photonics，不能改写为纯光模块收入，且因不是当前 legacy schema 所需的具名 management quote，先放 event 观察而非 `commitments.csv`。

跨期只能得出：Credo 把 ZeroFlap 从产品族 sampling 推到一个 800G SKU 的 GA，并通过收购增加硅光能力；仍缺光学收入拆分、已部署客户数量和规模出货，因此不能判断其光学业务已经成熟解决可靠性或供应问题。

官网技术博客（包括 MicroLED、optical fabric observability）可作为 `technical_blog / corporate_narrative` 的卡点发现入口，但不得单独支持 `volume_order / first_shipment / ramping / scaled`。博客提出的故障损失、可靠性或功耗优势在没有方法、客户或可复现实验时仍是 company claim only。

### 12.6 承诺候选与截至 2026-08-11 的状态

| candidate | 证据与目标窗口 | 建议状态 | 处理理由 |
|---|---|---|---|
| `CIEN_VESTA_SAMPLE_CQ2_2026` | Ciena FY2026 Q1 transcript；2026-06-30 | `not_observed` | 已过窗口；只找到产品发布/演示，没有明确样品已提供的官方事实。没有官方延期陈述，故不标 `delayed`。 |
| `CIEN_HYPERRAIL_STANDARDIZATION_2026` | Ciena FY2026 Q1 transcript；2026-12-31 | `pending` | Q2 首单不等于标准化完成。 |
| `CIEN_HYPERRAIL_RAMP_2027` | Ciena FY2026 Q1 transcript；2027-12-31 | `pending` | Q2 仅称 2027 年逐步 rollout；没有规模收入或出货。 |
| `CIEN_PLUGGABLE_REVENUE_DOUBLE_FY26` | Ciena FY2026 Q2 transcript；2026-10-31 | `pending` | 等 FY2026 年报核对；指标是全部 pluggable revenue，不是 800G/1.6T 单项。 |

两项不应强塞入当前 `commitments.csv`：Ciena Q3 的“未来数季达到数亿美元”没有精确 due date；Credo FY2027 超过 5 亿美元的光学组合收入来自公司收购公告正文而非当前 schema 要求的具名 management forward-looking claim。它们应进入支持窗口日期的 event observation，待 schema 明确 `date_precision=window` 或具名管理层重申后再迁移。

### 12.7 可直接落库的 legacy claim 建议

ID 仅为建议，写入前仍需检查冲突。下表只放当前 schema 能承载的 management `fact / forward_looking`；MACOM 为零，Credo Q3 叙事不在此表。

| 建议 claim_id | source_id | speaker | statement_type | event_type | side | theme | quote / anchor | summary |
|---|---|---|---|---|---|---|---|---|
| `CL_CIEN_2025Q3_SCALE_SHIP` | `S_CIEN_2025Q3` | Gary Smith | `fact` | `first_shipment` | `both` | T021 | 见 12.3 对应短引 / `p.3 scale-across project` | RLS+WL6 Nano 800G 项目开始产生收入出货；客户未具名。 |
| `CL_CIEN_2025Q3_SCALE_RAMP` | `S_CIEN_2025Q3` | Gary Smith | `forward_looking` | `ramping` | `both` | T021 | 见 12.3 对应短引 / 同 anchor | 预计未来数季爬坡；期限不精确，先不进 commitments.csv。 |
| `CL_CIEN_2025Q4_WL6N_SHIP` | `S_CIEN_2025Q4` | Gary Smith | `fact` | `first_shipment` | `both` | T021 | 见 12.3 对应短引 / `p.4 WL6 Nano paragraph` | WL6 Nano 800G 进入初始收入出货。 |
| `CL_CIEN_2025Q4_PHOTONICS_LIMIT` | `S_CIEN_2025Q4` | Marc Graff | `fact` | `unknown` | `supply` | T016 | 见 12.3 对应短引 / `p.13–15 supply Q&A` | 光子部件受限；具体器件未披露。 |
| `CL_CIEN_2026Q1_CLUSTER_ORDERS` | `S_CIEN_2026Q1` | Gary Smith | `fact` | `announced` | `demand` | T021 | 见 12.3 对应短引 / `p.3 hyperscaler paragraph` | 首个 hyperscaler 追加多集群订单；数量未披露。 |
| `CL_CIEN_2026Q1_REVENUE_LIMIT` | `S_CIEN_2026Q1` | Marc Graff | `fact` | `unknown` | `supply` | T016 | 见 12.3 对应短引 / `p.6–7 supply discussion` | 供应约束实际压低可实现收入。 |
| `CL_CIEN_2026Q1_VESTA_SAMPLE` | `S_CIEN_2026Q1` | Gary Smith | `forward_looking` | `sampling` | `both` | T017 | 见 12.3 对应短引 / `p.5 Vesta paragraph` | Vesta 样品计划；截至复核日未观察到明确兑现。 |
| `CL_CIEN_2026Q1_HYPERRAIL_STD` | `S_CIEN_2026Q1` | Gary Smith | `forward_looking` | `announced` | `both` | T021 | 原文标准化期限短引 / `p.5 Hyper-Rail paragraph` | 预计 2026 年底开始标准化。 |
| `CL_CIEN_2026Q1_HYPERRAIL_RAMP` | `S_CIEN_2026Q1` | Gary Smith | `forward_looking` | `ramping` | `both` | T021 | 原文 2027 ramp 短引 / 同 anchor | 预计 2027 年开始爬坡。 |
| `CL_CIEN_2026Q2_HYPERRAIL_ORDER` | `S_CIEN_2026Q2` | Gary Smith | `fact` | `announced` | `demand` | T021 | 见 12.3 对应短引 / `p.3` | Hyper-Rail 首单；不是出货或收入事实。 |
| `CL_CIEN_2026Q2_COHERENT_WIN` | `S_CIEN_2026Q2` | Gary Smith | `fact` | `announced` | `demand` | T021 | 见 12.3 对应短引 / `p.4` | 大型 hyperscaler coherent module win；用于 DCI。 |
| `CL_CRDO_2026Q2_OPTICS_RAMP` | `S_CRDO_2026Q2` | Bill Brennan | `forward_looking` | `ramping` | `both` | T004 | 见 12.5 对应短引 / `CEO quote` | 只证明 ZeroFlap 被列入混合产品爬坡计划；无期限、客户或数量。 |

落库顺序建议：先替换 Ciena 四个 canonical source 的材料 URL/类型并录入上述 legacy claims；再录入 12 个季度 disclosure 状态；随后把 IQE 拆成资本与供应安排两个 event；最后录入 Credo 的 sampling→GA 与 DustPhotonics 事件。所有新增事件保持 `asserted`，不创建海外—国内供应、合作、竞争或替代 edge。
