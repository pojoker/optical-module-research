# 800G DR8 LPO SiPh 完整路线链草稿

状态：draft-only；不是正式 RP、WHY 或公司服务群。

本路线由多轴汇合而成，详见 `route-axis-junction.md`。LPO/retimed 是电职责选择；SiPh 是光子平台观察；front-panel pluggable 是放置/封装选择，三者不得互相自动推出。

状态词映射：`specification`、`architecture-supported`、`exact-product-page observation`、`listed-component observation`、`production-available offer` 属于不同对象层级的 `supported` 子类；`consortium-stated` 属于 `company-stated`/组织主张子类；`framework` 属于受边界限制的 `engineering-inference`；无法比较或没有直接证据时分别使用 `not-comparable`、`unknown`。

## 0. 路线对象与基线

### Target

`800G-DR8-LPO + SiPh + front-panel pluggable + 8×106.25 Gb/s + 500 m SMF`

- 路线规范边界来自 S1；
- finished-product observation 来自 S6；
- 两款 S6 listing 不预设同族或同内部实现。

### Baseline

`800G-DR8 retimed + front-panel OSFP + 8×106.25 Gb/s + 500 m SMF`

- observed baseline 为 S5；
- baseline platform、connector 和供应商不同，因此功耗只作产品包络观察，不能把差值全归因于 LPO。

## 1. 上游原因：场景约束与瓶颈

| 链节 | 状态 | 主张 | 证据 |
|---|---|---|---|
| 场景需求 | consortium-stated | AI/data-center link 同时追求高带宽、低模块功耗、端口密度、成本和时延 | S1 p.7 |
| 热约束 | unknown | 本轮没有冻结来源把 target 的温度/散热边界与 retimed baseline 放在同条件下比较 | UNKNOWN；不由模块功耗数字反推热结论 |
| 产品边界 | specification | 800G-DR8-LPO = 8×53.125 GBd PAM4，1310 nm，0.5–500 m SMF | S1 p.7、p.21 |
| FEC 约束 | specification | RS(544,514) encode/decode 由 host 实现 | S1 p.10 |
| 电通道约束 | specification | 目标把 OIF linear channel loss 从 13 dB 扩展到 16 dB；模块仍需 Tx equalization | S1 p.13–14 |
| 当前瓶颈 | framework | retimed 架构在模块中进行数字处理；LPO 试图利用 host equalization，去掉模块 DSP/retimer | S2 p.659–660；S3 p.3–4 |
| 可采用前提 | specification / MSA statement | 需要 capable host ASIC、良好 transmission lines、host/module 联合参数与 BER/FEC 闭环 | S1、S2、S10 |

### 候选 WQ001：need → constraint

```text
AI/数据中心的 800G、低模块功耗/时延与高密度需求
→ 8×100G-class、500 m SMF、host FEC、受限 host-module channel-loss 的系统约束
```

状态：`candidate_mixed_support`。第一端是 MSA 场景陈述，不是全市场统计。

### 候选 WQ002：bottleneck → choice

```text
模块内 retimer/DSP 的功耗和处理路径
+ host ASIC 已具备 equalization 能力
→ 提高“去模块 DSP、采用 end-to-end linear channel”的相对价值
```

状态：`candidate_framework_supported`。只证明设计机制；不证明任何固定百分比、系统总功耗或所有端口都适用。

## 2. 条件化优势、代价与新瓶颈

| 维度 | 条件化结论 | 状态 | 来源锚 | 边界 |
|---|---|---|---|---|
| 模块功耗机制 | 去掉 module signal-path DSP/retimer 减少一条模块内数字处理与耗电路径 | engineering-inference | S2 p.659–660；S3 p.3–4 | 只说明机制，不给幅度，也不等于系统总功耗降低 |
| 产品功耗观察 | S6 ≤9 W；S5 <17 W | product-observation + not-comparable | S5；S6 | 两产品供应商、平台、连接器、温度/实现不完全同条件；不能把两者功耗上限差异归因于 LPO |
| 时延 | 去掉模块数字决策/retiming 路径被描述为降低 module-path latency | consortium-stated | S1 p.7；S10 | 没有合格同条件数值；不写 ns 数字或端到端时延结论 |
| 成本 | 去 DSP 被描述为 lower-cost target | consortium-stated | S1 p.7；S10 | 没有 BOM、ASP、良率、host 成本边界；不形成成本事实 |
| 协议 | LPO MSA 称 compliant module protocol agnostic | consortium-stated | S10 | 不证明所有 host、模块和协议即插即用 |
| host 要求 | host FEC、equalization、channel-loss 配置承担更多责任 | supported/specification | S1 p.10–14；S2 p.659–661；S4 p.51–55 | 不是“全部 DSP 功能都转移”；只记录已定义职责 |
| 互操作 | LPO-to-LPO 由 MSA规范化；LPO-to-retimed 被界定为 engineered link / MSA scope 外 | supported/specification-scope | S10 | OIF demo 证明某些 interop，不证明普遍互操作 |
| 启动/训练 | 802.3ck electrical link training 主要因 driver/TIA AGC 不能直接用于 LPO | supported/specification | S1 p.10–11 | 可用 startup protocol 但配置/优化方法超出 S1 范围 |
| 测试耦合 | 必须在 TP1a/TP4、EECQ、stressed input、host-to-host BER 下联合验证 | supported/specification | S1 p.32；S2 p.667–681；S3 p.5 | 不证明生产 test time、成本或设备价值量必然上升 |

### TQ014 结论

- `comparison_status: partially_comparable`
- 允许的优势：module-level power/latency/cost **目标与机制**；不允许无条件幅度和总系统结论。
- 已定义的责任变化与工程代价候选：host/electrical-channel/equalization/configuration/test coupling 增加；startup/link-training 产生新问题。尚无同条件实测代价值。
- 新瓶颈：host compatibility、channel-loss margin、equalization ownership、startup protocol、end-to-end BER/FEC margin。
- 替代方案：retimed module；LPO↔retimed engineered link；LRO/RTLR（本轮不展开）。
- `no_unconditional_ranking: true`

## 3. 下游物理变化

### 3.1 组件

| 变化 | 状态 | 证据/限制 |
|---|---|---|
| module DSP/retimer 不在 LPO signal path | architecture-supported | S2/S3；不等于模块内没有 MCU、控制逻辑或任何 CDR-capable block |
| host retimer/equalization/FEC 继续承担端到端职责 | specification | S1/S2 |
| module Tx equalization function、driver/TIA AGC 相关行为仍存在 | specification | S1 p.10–13；不推断具体芯片数量/型号 |
| target photonic platform = SiPh | exact-product-page observation | S6；内部 laser/modulator/detector UNKNOWN |
| 可用 800G DR8 SiPh PIC 组件实例 | listed-component observation | S8；不得转移到 S6 模块 |
| 可用 SiPh linear driver/TIA 组件能力 | production-available offer | S9；不得转移到 S6 模块 |

### 3.2 接口与管理

状态：`supported/specification + product observations`。

- host FEC：RS(544,514) encode/decode；
- electrical：LEI-800G-PAM4-8、0–16 dB host-loss class；
- optical：8 lanes、53.125 GBd PAM4、1310 nm、0.5–500 m SMF；
- management：CTLE/equalization、host-channel-loss、可选 NLC 等参数需通过规范接口表达；
- form factor/connector：S6 的 OSFP/QSFP-DD 与 MPO 方案是产品观察，不是 LPO 必然值。

### 3.3 工序

`UNKNOWN_COMPARATIVE_DELTA`。

- S8 当前页面可证明 Credo Carmel8 PIC 与 DustPhotonics L3C laser-coupling process；历史 post-burn-in/electrical-optical-test 字段本轮不消费；
- S11 可证明 Intel 特定 SiPh 平台使用 wafer-scale test、laser burn-in 与 known-good-die；
- S9 可证明某些 driver 提供 wirebond/flip-chip 形态；
- 不能据此推断 S6 模块的 die attach、wirebond、active alignment、calibration 或良率变化。

### 3.4 设备

`UNKNOWN_PRODUCTION_EQUIPMENT_DELTA`。

OIF demo 出现 BERT、oscilloscope、HCB/MCB 等测试生态，只能支持研发/互操作/合规测试需求，不能证明生产线设备增删或价值量。

AGY 新找到的 Mycronic、FormFactor、ficonTEC、Keysight、MultiLane 等页面只保留为设备能力发现线索；由于链接/参数未形成冻结且不能绑定 target，不进入本卡的生产设备事实。

S16 可补充两个公司级设备能力观察：联讯仪器披露 SiPh wafer test system 的设备构成及商业化；猎奇披露面向 SiPh 的先进键合工艺研发。二者仍不能证明 target 产线采用，也不能构成 LPO 相对 retimed 的设备净变化。

### 3.5 测试

规范支持的测试责任：

- TP1a/TP4 EECQ 与 reference equalizer；
- host/module output 与 stressed input；
- 高/低损 channel calibration；
- crosstalk 活跃条件；
- host-to-host 或 stress generator 的 BER/error statistics；
- FEC tail margin。

状态：`specification_supported_test_responsibility`。

演示观察：S3 记录 multi-vendor interop demo、BER/FEC margin 与测试生态。状态：`ecosystem_demo_observation`；不能升级为普遍互操作或生产测试要求。

### 候选 WQ003：choice → physical

```text
选择 LPO end-to-end linear channel
→ 模块信号路径不使用 retimer/DSP
→ host 承担 FEC/equalization，并与 module 交换 channel/equalizer 参数
→ 合规验证从解耦模块字段扩展到 host-module stressed input 与 end-to-end BER
```

状态：`candidate_specification_supported`，只覆盖组件/接口/测试责任子链；整体工序和生产设备变化仍 UNKNOWN，不升为整条 physical chain supported。

## 4. 物理能力与公司服务证据

| 角色/所需能力 | 公司 | 直接证据对象 | evidence stage | 是否完整覆盖 target |
|---|---|---|---|---|
| finished module integration | Hyper Photonix / 芯速联 | `HSO6-800-LP-P8S`、`HSD2-800-LP-P8S` 800G DR8 LPO SiPh listings | `listed_product` | 是，产品层；量产/客户 UNKNOWN |
| SiPh Tx PIC | Credo（当前产品页；DustPhotonics L3C 技术来源） | Carmel8 800G DR8 SiPh PIC；LPO application | `listed_component_product` | 组件层；未绑定 S6 模块 |
| integrated SiPh platform | Intel | 8-lane component portfolio、wafer-scale test/burn-in/KGD、PIC shipment company statement | `platform_shipment_company_stated` | 平台成熟度；未绑定 exact LPO target |
| linear driver/TIA | MACOM | PURE DRIVE production-available LPO ICs；SiPh/800G SM support | `production_available_component_offer` | 能力层；未绑定具体 DR8 module |
| DR8 LPO module demo | Eoptolink | 800G DR8 LPO demo/portfolio | `partial_route_demo` | 平台未精确绑定 SiPh |
| host/interop/test ecosystem | OIF demo participants | multi-vendor SerDes、modules、BERT/scope、conformance | `ecosystem_demo` | 测试生态，不是供货/客户关系 |
| SiPh wafer/PIC test equipment | 联讯仪器 | wafer test system + coupling/probe/handler；发行人披露商业化 | `production_equipment_company_disclosed` | SiPh 平台能力；未绑定 target |
| advanced bonding/process equipment R&D | 猎奇智能设备 | laser-assisted bonding/reflow/thermocompression R&D | `equipment_process_rnd` | 研发阶段；未绑定 target |

### 4.1 近邻路线采用阶段

| 公司 | 已证对象 | evidence stage | 不可补字段 |
|---|---|---|---|
| 剑桥科技 | SiPh 800G OSFP DR8/DR8+ 获海外客户认证并于 2025 年大批量发货（S13） | `near_route_shipment_company_disclosed` | 未披露 LPO；不能升 exact-target shipment |
| 新易盛 | 公司称 LPO 模块规模量产；800G LPO 与 800G SiPh 直驱项目分别验收（S14） | `company_lpo_production + separate_project_acceptance` | 不合并成同一 DR8 SiPh LPO SKU |
| 联特科技 | 800G SiPh 2×DR4/2×FR4 LPO 开发与 NPI；LPO 客户联合设计（S15） | `near_route_npi_customer_collaboration` | PMD 非 DR8；不升 shipment/customer adoption |

本轮仍没有 `exact_target_shipment` 或 named-customer adoption。近邻路线证据用于显示不同公司服务到什么成熟度，不用于拼接目标路线。

本轮不创建 confirmed company group。只有 Hyper 是 finished-module exact target 绑定；Dust/MACOM 是角色级服务能力，Eoptolink 是 platform-unknown partial route。

阶段映射：`partial_route_demo`、`ecosystem_demo` → `demo`；`listed_component_product`、`production_available_component_offer` → 组件/能力对象的 `listed_product` 扩展阶段。它们都不等于 finished-module `shipment` 或 `customer_adoption`。

### 候选 WQ004：physical → capability/company evidence

```text
LPO SiPh 的模块集成、SiPh PIC、linear analog IC、host equalization 与联合合规测试要求
→ 分别需要 finished-module integrator、PIC provider、linear driver/TIA provider、host/interop/test ecosystem
→ 公司只能按直接证据对象和阶段挂载，不能从能力匹配推已供货
```

状态：`candidate_role_stage_supported`。

## 5. 完整性与未闭合字段

| 链节 | 当前状态 |
|---|---|
| 上游需求 → 约束 | 已有 MSA/specification 支持，场景普遍性仍有限 |
| 瓶颈 → LPO 选择 | 已有 OIF/MSA 机制支持，缺系统总功耗/成本受控对照 |
| LPO → 优势/代价 | 条件化草稿成立；数值优势多数保持 not-comparable |
| LPO → 组件/接口/测试 | 已支持；工序/生产设备 delta 仍 UNKNOWN |
| 能力 → 公司 | 已形成 role-scoped evidence stages；无 customer adoption |
| WHY | 已形成 4 条 candidate；未写 `why_links` |
| SiPh 轴 | 已形成 `conditional_platform_selection_hypothesis`：若 target 真的优先 8-lane PIC 集成、wafer test/burn-in/KGD 与平台成熟度，SiPh 可进入候选池；这些前提对 Hyper 未验证。除同条件 SiPh vs EML/TFLN 受控比较外，任何 listing/组件页/平台陈述堆叠都不能升 supported WHY |

## 6. 禁止解释

- 不说 LPO 普遍降低 50% 功耗或必然更便宜；
- 不把 S6 ≤9 W 与 S5 <17 W 的差全部归因于 LPO；
- 不把 Dust/MACOM 组件自动装进 Hyper 产品；
- 不把 demo/listing/production-available component 变成客户采用；
- 不把测试仪器生态写成生产设备投资结论；
- 不改 canonical、coverage、正式 RP、WHY 或公司群。
