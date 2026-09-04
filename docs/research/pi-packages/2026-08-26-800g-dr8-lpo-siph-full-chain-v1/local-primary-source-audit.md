# 800G DR8 LPO + SiPh 本地一手来源审计

- 审计日期：2026-08-26
- 审计方式：只读优先；仅使用本轮已经检查的本地官方网页快照、标准、年报和招股书
- 目标路线：`800G + DR8 + LPO + SiPh`
- 输出状态：研究暂存，不落知识库，不修改 canonical、coverage、WHY、RP 或公司群
- 结论等级：`直接证实`、`部分证实`、`UNKNOWN（本轮未找到）`

## 一、结论先行

### 缺口 1：为什么可能选择 SiPh，而不是 EML/TFLN

本轮只能形成**条件性选择机制**，不能形成“SiPh 必然优于 EML/TFLN”的结论。

已证实：

1. LPO 的定义性变化是取消模块内 DSP/retimer，并利用主机 ASIC 的均衡能力；LPO MSA 没有把 LPO 绑定到某一种光子平台。
2. 官方演示证明 SiPh 与 EML 都可实现 800G DR8+，且两者可以互通。因此，`DR8` 和 `LPO` 本身都不足以推出“必须选择 SiPh”。
3. Intel 自有 SiPh 平台披露了适用于八通道设计的成本结构、晶圆级集成激光器、晶圆级测试与 KGD，以及大规模出货历史。这些可作为在八通道、高集成度、大批量条件下考虑 SiPh 的**机制候选**。
4. EML 具有成熟的 InP 单片 DFB+EAM 路线；联特科技还明确披露其 LPO 样品同时采用 EML 和 SiPh。
5. TFLN 也不是已被排除的路线。光库科技披露其用于数据中心/AI 高速互连的 PAM4 TFLN 调制器仍处于验证送样阶段，同时强调 TFLN 的大带宽潜力。该材料不能提供 SiPh 与 TFLN 的同边界比较。

因此当前应写为：

> 在 800G、八通道、短距、大批量和高集成度等约束下，SiPh 的晶圆级集成、晶圆级测试与平台规模经验可能成为选择理由；但本地一手材料没有证明它在同一 reach、lane、BER/FEC、温度、封装和产量边界下优于 EML 或 TFLN。

### 缺口 2：相对 retimed/EML 路线的制造工序和设备变化

本轮找到的是**候选变化**，不是完整的增删设备清单。

已证实：

1. 通用光模块封测骨干包括贴片、引线键合、光学耦合和老化测试；耦合设备可集成对准、点胶和 UV 固化。
2. SiPh 可把部分光电功能集成到 PIC，并支持晶圆级电光/光电性能测试、耦合测试和 KGD 筛选。对应设备包括测试机、耦合测试模组、探针台、晶圆上下料机以及光学、DC、RF 探针。
3. 设备厂披露正在针对 SiPh 集成推进激光辅助键合、局部激光回流和倒装热压等先进封装工艺。
4. LPO 将一部分链路均衡、FEC 和端到端 BER 验证责任移到主机与系统链路，且普通电通道 link training 不能直接照搬。该变化会改变测试对象和测试拓扑。

仍为 UNKNOWN：

- 没有找到一份本地一手材料，以同一款 800G DR8 产品为边界，对比 `SiPh LPO` 与 `retimed/EML` 两条量产线，并逐项说明哪些工序或设备被新增、删除、替代或只改变参数。
- 没有证据支持“采用 SiPh LPO 后不再需要主动耦合、模块老化、眼图或 BER 测试”。现有资料反而显示这些通用环节仍可能存在。
- 没有找到目标路线的设备数量、节拍、良率、CAPEX 或单位成本对照数据。

### 缺口 3：shipment、customer adoption 或真实供货

2025 年报带来了新的强证据，但仍没有闭合目标路线的全部四个轴。

已直接证实：

1. 剑桥科技披露其硅光 800G OSFP DR8/DR8+ 完成海外大客户认证，并在 2025 年实现大批量发货。
2. 剑桥科技的 800G、100G/lane SiPh 产品族同时列有 DR8 类产品和 800G LPO/TRO 模块。`LPO/TRO` 为年报原文，本包只做逐字保留，不规范化该术语，也不外推其含义。
3. 新易盛披露已规模量产 LPO 模块，并披露 800G LPO 项目及采用 SiPh 的 800G 直驱项目通过验收。
4. 联特科技披露与客户开展 LPO 联合设计，并完成 800G SiPh 2xDR4/2xFR4 LPO 的开发与 NPI 转产。

仍为 UNKNOWN：

- 没有找到明确写出“已认证/已批量发货的产品同时是 `800G + DR8 + LPO + SiPh`”的一手句子。
- 剑桥科技的 DR8/DR8+ 发货证据没有说明模块是 LPO 还是 retimed；产品表中的 DR8 与 LPO/TRO 是同一 SiPh 产品族下的并列项，不能自动求交集。
- 新易盛分别披露 LPO 量产和 SiPh 直驱研发，但没有披露已量产 LPO 产品的 PMD 是 DR8，也没有给出目标产品客户。
- 联特科技的真实 LPO 客户协作和 SiPh LPO NPI 对应 2xDR4/2xFR4，不是 DR8。
- 本轮没有找到可以公开点名、且能与目标产品 SKU 绑定的终端客户。

## 二、原子主张与证据边界

### A. 上游约束与光子平台选择

| ID | 结论 | 原子主张 | 文件与定位 | 可支持范围 | 不可支持范围 |
|---|---|---|---|---|---|
| A01 | 直接证实 | LPO 模块不包含 DSP，链路利用主机 ASIC 的均衡能力。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lpo-msa.org__faqs.html`，行 53-66 | LPO 与 retimed 的电架构差别；LPO 对主机 ASIC 和传输线的约束 | LPO 必须使用 SiPh；具体功耗或成本降幅 |
| A02 | 直接证实 | LPO MSA 同时覆盖 LPO-to-LPO、LPO-to-retimed 和 half-linear 架构。 | 同上，行 50-51、68-72 | LPO 是跨电/光接口的系统架构，允许多种链路组合 | 任一光子平台的优先级或市场份额 |
| A03 | 直接证实 | Coherent 演示了 SiPh MZM PIC 的 800G DR8+ 与 EML 的 800G DR8+ 互通。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html`，行 1963-1967 | SiPh 与 EML 都可用于 800G DR8+；二者至少在该演示中互通 | LPO；量产；SiPh 相对 EML 的成本、良率或功耗优势 |
| A04 | 直接证实 | 联特科技 2024 年披露其 LPO 样品同时采用 EML 和 SiPh。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual-2024/301205/301205__em_联特科技_em__2024_2024年年度报告.pdf`，PDF 第 24 页；对应 `.pdf.txt` 行 1280-1292 | 在该公司、该时点，LPO 不绑定单一光子平台 | 行业普遍做法；量产优劣；800G DR8 LPO 的具体出货 |
| A05 | 直接证实（厂商自述） | Intel SiPh 平台提供八通道设计成本结构、晶圆级集成激光器和晶圆级测试/KGD。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/intel.com__silicon-photonics.html`，行 3233-3242 | Intel 平台下，SiPh 面向八通道、高集成和晶圆级筛选的机制 | 对所有 SiPh 供应商的泛化；相对 EML/TFLN 的同口径量化优势 |
| A06 | 直接证实（厂商自述） | Intel 披露自 2016 年起出货超过 800 万颗 PIC，进入大型云服务商使用的可插拔模块。 | 同上，行 3487-3491 | Intel SiPh 平台具有真实规模出货和云数据中心部署历史 | 这些 PIC 属于 800G DR8 LPO；具体客户名称；全行业份额 |
| A07 | 直接证实 | Lumentum 的 EML 在 InP 晶圆厂制造，由 DFB 与单片集成 EAM 构成。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lumentum.com__emls.html`，行 1 的 description/canonical 元数据 | EML 的材料与器件结构基线 | EML 相对 SiPh 的成本、良率、功耗；特定 800G LPO 供货 |
| A08 | 部分证实 | 光库科技披露用于数据中心/AI 高速互连的 PAM4 TFLN 调制器仍在验证送样，并把大带宽列为后续优势。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/300620/300620/300620__em_光库科技_em__2025_2025年年度报告.pdf`，PDF 第 74 页；对应 `.pdf.txt` 行 4508-4536 | 该公司 TFLN 相关产品在该时点的成熟度；TFLN 是仍在推进的竞争路线 | TFLN 与 SiPh/EML 的同边界优劣；800G DR8 LPO 的 TFLN 可行性或成本 |
| A09 | UNKNOWN | 在完全相同的 reach、lane、BER/FEC、温度、封装、产量边界下，SiPh 优于 EML 或 TFLN。 | 本轮已检查材料未找到此类受控比较 | 只能保留为待研究问题 | 不得据厂商单点宣传形成路线胜负结论 |

### B. 制造工序与生产/测试设备

| ID | 结论 | 原子主张 | 文件与定位 | 可支持范围 | 不可支持范围 |
|---|---|---|---|---|---|
| B01 | 直接证实 | 光模块封测通常包括贴片、引线键合、光学耦合和老化测试。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/legacy-input/lieqi_prospectus.txt`，行 8293-8315，招股书页码 1-1-89 至 1-1-90 | 通用封测流程骨干；共晶/固晶贴片的典型对象 | 目标路线每一步的实际设备配置；SiPh 与 EML 的增删差异 |
| B02 | 直接证实 | 耦合流程一般含对准、透镜耦合、胶水固定和效率验证；设备可集成耦合、点胶、UV 固化。 | 同上，行 8484-8524，页码 1-1-92 至 1-1-93 | 通用光学耦合环节及对应设备功能 | 所有 SiPh 产品都必须使用独立透镜；LPO 会取消耦合 |
| B03 | 直接证实 | 光模块老化测试可覆盖芯片 LIV/光谱、CoC/OE 和模块级老化。 | 同上，行 8526-8595，页码 1-1-93 至 1-1-94 | 通用老化与筛选层级；DFB/EML/CW 芯片测试对象 | 目标 SiPh LPO 的具体老化条件、时长或设备数量 |
| B04 | 直接证实（研发状态） | 猎奇针对 SiPh 集成推进激光辅助键合、局部激光回流和倒装热压工艺。 | 同上，行 8974-8981，页码 1-1-102 | SiPh 先进封装的候选工艺和候选设备方向 | 已用于 800G DR8 LPO 量产；已替代哪些既有设备；实际节拍和良率 |
| B05 | 直接证实 | 联讯仪器的 SiPh 晶圆测试系统可在晶圆层面测量电光/光电转换、调制质量和接收灵敏度。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/legacy-input/lianxun_prospectus.txt`，行 9113-9126，页码 1-1-93 | SiPh 可新增或前移至晶圆级的测试能力 | 目标产品一定采用该设备；该测试完全取代模块级测试 |
| B06 | 直接证实 | 该 SiPh 晶圆测试系统由测试机、耦合模组、探针台和晶圆上下料机组成，并使用光学、DC、RF 探针。 | 同上，行 9124-9136，页码 1-1-93 | 具体设备组成和垂直/边缘耦合测试能力 | 相对 EML 产线的设备净增量或 CAPEX |
| B07 | 直接证实（发行人披露） | 联讯仪器的 SiPh 晶圆测试系统在 2024 年实现收入；800G 核心测试仪器已大规模量产供货。 | 同上，行 1915-1939，页码 1-1-22 至 1-1-23 | 设备已经商业化，而非只有概念样机 | 设备销量对应 800G DR8 LPO；客户与具体设备/产品的绑定关系 |
| B08 | 直接证实 | LPO 规范把八通道链路的 FEC 放在主机，并要求模块提供发送端均衡功能。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`，PDF 第 10、13 页 | LPO 的主机/模块功能责任与 retimed 不同 | 某一生产设备因此被删除；模块完全不需信号完整性测试 |
| B09 | 直接证实 | 普通电通道 link training 不能直接用于 LPO，主要原因是 driver/TIA 中的 AGC。 | 同上，PDF 第 11 页 | LPO 系统调试与链路训练需要专门处理 | 所有厂商的具体训练算法或量产测试脚本 |
| B10 | 直接证实 | LPO 规范给出 host-to-host 链路测试，并允许用 stress generator 注入压力信号后测 BER/错误统计。 | 同上，PDF 第 32 页 | LPO 需要端到端链路和 BER 类验证 | 具体测试台品牌、数量、节拍；是否替代所有模块级 BERT 测试 |
| B11 | UNKNOWN | 目标 `800G DR8 LPO + SiPh` 相对 `800G DR8 retimed + EML` 的逐工序、逐设备增删表。 | 本轮已检查材料未找到受控产线对照 | 只可列“候选变化”，不可写成已发生的净变化 | 不得声称取消主动耦合、老化、眼图或 BER 测试 |

### C. 公司出货、客户采用与真实供货

| ID | 结论 | 原子主张 | 文件与定位 | 可支持范围 | 不可支持范围 |
|---|---|---|---|---|---|
| C01 | 直接证实 | 剑桥科技的 800G、100G/lane SiPh 产品族列有 DR8 类模块，也列有 800G LPO/TRO 模块。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/603083/603083/603083__em_剑桥科技_em__2025_2025年年度报告.pdf`，PDF 第 12 页；对应 `.pdf.txt` 行 613-624 | 公司具备 SiPh 800G DR8 与 SiPh 800G LPO/TRO 产品布局 | 同一 SKU 同时是 DR8 和 LPO；产品已出货 |
| C02 | 直接证实（发行人披露） | 剑桥科技称全系列 SiPh 800G 产品已向海外核心客户批量发货。 | 同上，PDF 第 14 页；对应 `.pdf.txt` 行 768-779 | 公司层面的 SiPh 800G 批量发货及客户审核 | 每一款产品均批量发货；目标 DR8 LPO SKU；客户名称 |
| C03 | 直接证实（发行人披露） | 剑桥科技的 SiPh 800G OSFP DR8/DR8+ 完成海外大客户认证，并于 2025 年大批量发货。 | 同上，PDF 第 22 页；对应 `.pdf.txt` 行 1235-1243 | `SiPh + 800G + DR8/DR8+ + 客户认证/批量发货` | LPO/retimed 架构；命名客户；500m 等具体 reach |
| C04 | 直接证实（发行人披露） | 剑桥科技马来西亚基地通过北美 400G/800G 产品稽核并批量发货，且使用自研精密耦合机台。 | 同上，PDF 第 14、24 页；对应 `.pdf.txt` 行 775-779 | 公司具有经客户审核的 800G 制造交付与耦合设备能力 | 这些产线或设备专用于 SiPh DR8 LPO |
| C05 | 直接证实（发行人披露） | 新易盛称已规模量产 LPO 光模块。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/300502/300502/300502__em_新易盛_em__2025_2025年年度报告.pdf`，PDF 第 12 页；对应 `.pdf.txt` 行 501-508 | 公司层面的 LPO 规模量产 | 量产产品的速率、PMD、光子平台、客户或出货量 |
| C06 | 部分证实 | 新易盛的 800G LPO 项目与采用 SiPh 的 800G 直驱 QSFP-DD/OSFP 项目均通过验收，但被分成两个项目披露。 | 同上，PDF 第 18 页；对应 `.pdf.txt` 行 830-845 | 公司具备 800G LPO 和 800G SiPh 直驱研发成果 | 两项目属于同一 SKU；DR8；客户认证或批量发货 |
| C07 | 直接证实（发行人披露） | 联特科技与客户在 LPO 等方案上开展联合设计并参与客户预研。 | `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/301205/301205/301205__em_联特科技_em__2025_2025年年度报告.pdf`，PDF 第 22 页；对应 `.pdf.txt` 行 1178-1184 | LPO 已进入真实客户协作 | 客户名称；800G DR8；订单、认证或出货 |
| C08 | 直接证实（非目标 PMD） | 联特科技完成 800G SiPh 2xDR4/2xFR4 LPO 的开发与 NPI 转产。 | 同上，PDF 第 26 页；对应 `.pdf.txt` 行 1419-1430 | `800G + SiPh + LPO` 已在另一 PMD 进入 NPI | DR8；规模量产；客户认证；真实出货 |
| C09 | UNKNOWN | 已有一手材料把 `800G + DR8 + LPO + SiPh` 四轴绑定到同一已认证或已出货 SKU。 | 本轮已检查材料未找到 | 继续保留为最高优先级证据缺口 | 不得把同一公司不同段落、不同项目或同一产品族的并列项自动合并 |
| C10 | UNKNOWN | 可公开点名的终端客户采用并购买目标 SKU。 | 本轮已检查材料未找到 | 只能写“海外大客户/核心客户”等发行人原词 | 不得推定客户名称或客户产品部署 |

## 三、对当前路线链的可用更新

在不落库的前提下，当前路线链可临时采用以下状态：

```text
上游 WHY：PARTIAL
  - 可写：八通道集成、晶圆级制造/测试、平台规模经验是 SiPh 的条件性选择机制。
  - 不可写：SiPh 在 800G DR8 LPO 中必然优于 EML/TFLN。

制造/设备 DELTA：PARTIAL / UNKNOWN_COMPARATIVE_DELTA
  - 可写：SiPh 晶圆级测试/KGD、耦合测试、先进键合是候选新增或前移环节；
          LPO 增加主机侧均衡/FEC和端到端链路验证责任。
  - 不可写：已有完整设备增删表，或某些通用测试环节被取消。

公司采用：NEAR_ROUTE_PARTIAL_STRONG
  - 已闭合：SiPh + 800G + DR8/DR8+ + 海外客户认证 + 大批量发货（剑桥科技，自述）。
  - 已闭合：800G + SiPh + LPO + 2xDR4/2xFR4 + NPI（联特科技，自述）。
  - 未闭合：800G + DR8 + LPO + SiPh + 客户认证/批量发货。
```

## 四、证据拼接禁区

以下拼接均不允许：

1. `SiPh DR8 已发货` + `同公司有 SiPh LPO 产品` ≠ `SiPh DR8 LPO 已发货`。
2. `LPO 取消 DSP` ≠ `LPO 取消模块级眼图、BER、老化或耦合测试`。
3. `SiPh 支持晶圆级测试` ≠ `SiPh 的量产成本一定低于 EML/TFLN`。
4. `公司与 LPO 客户联合设计` ≠ `客户已认证、下单或部署目标 SKU`。
5. `2xDR4/2xFR4 SiPh LPO 已 NPI` ≠ `DR8 SiPh LPO 已 NPI`。
6. 厂商自述的“低成本、低功耗、领先”只能支持该厂商的技术主张，不能替代同边界横向验证。

## 五、本轮明确未找到

- 没有找到 EML、SiPh、TFLN 在同一个 800G DR8 LPO reference design 下的受控比较。
- 没有找到目标路线与 retimed/EML 路线的逐工序、逐设备、节拍、良率、CAPEX 对照。
- 没有找到公开点名的终端客户与目标 SKU 绑定证据。
- 没有找到一句能够直接证实“800G DR8 LPO + SiPh 已完成客户认证或批量出货”的本地一手表述。
- 当前目录中的 Hyper 等产品线索缺少本轮可核验的原始官方网页/PDF 快照，因此没有晋升为一手证据。

## 六、实际检查过的关键文件

### 标准与官方网页快照

1. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lpo-msa.org__faqs.html`
2. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`
3. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/intel.com__silicon-photonics.html`
4. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html`
5. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/2026-08-24/lumentum.com__emls.html`
6. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/www.ficontec.com/2026-07-27/machine-platforms.html`
7. `/Users/jowang/Downloads/workflow-rehearsal/corpus/web/www.ficontec.com/2026-07-27/technologies.html`

### 公司年报

8. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/603083/603083/603083__em_剑桥科技_em__2025_2025年年度报告.pdf`
9. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/300502/300502/300502__em_新易盛_em__2025_2025年年度报告.pdf`
10. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/301205/301205/301205__em_联特科技_em__2025_2025年年度报告.pdf`
11. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/300308/300308/300308__em_中际旭创_em__2025_2025年年度报告.pdf`
12. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/002281/002281/002281__em_光迅科技_em__2025_2025年年度报告.pdf`
13. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual/300620/300620/300620__em_光库科技_em__2025_2025年年度报告.pdf`
14. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual-2024/301205/301205__em_联特科技_em__2024_2024年年度报告.pdf`
15. `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual-2024/300308/300308__em_中际旭创_em__2024_2024年年度报告.pdf`

### 招股书文本

16. `/Users/jowang/Downloads/workflow-rehearsal/corpus/legacy-input/lieqi_prospectus.txt`
17. `/Users/jowang/Downloads/workflow-rehearsal/corpus/legacy-input/lianxun_prospectus.txt`

### 审计说明

- PDF 页码定位和文本核对使用 `/Users/jowang/miniconda3/bin/python3` 与本地 `pypdf` 完成。
- 年报属于公司对自身产品、研发、认证和发货情况的正式披露，可直接支持“公司披露了什么”，但不能自动视为独立第三方技术比较。
- 两份招股书文本可支持发行人产品、设备和工艺披露；由于本地仅保留文本版本，结论中同时保留其印刷页码，不据此推断未披露的客户—设备—目标 SKU 绑定关系。
- 本轮没有使用券商研报、公众号或行业二手文章作为事实来源。
