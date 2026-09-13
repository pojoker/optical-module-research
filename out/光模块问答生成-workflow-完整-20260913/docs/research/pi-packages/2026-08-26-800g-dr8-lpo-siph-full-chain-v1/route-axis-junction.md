# 技术路线轴汇合：为什么不能从 LPO 单线推出 SiPh

状态：draft-only；证据结构补充，不写正式 RP/WHY 或知识库。

## 1. 结论

`800G DR8 LPO + SiPh + front-panel pluggable` 不是一根轴上的单项选择，而是“一个链路约束画像 + 三条决策轴”的组合：

```text
上游场景与链路约束
        │
        ├─ TQ005 链路画像：800G / DR8 / 8×100G-class / 500 m / SMF / FEC
        │
        ├─ TQ006 电职责：linear（LPO） vs retimed
        │
        ├─ TQ007 光子实现：platform / light source / modulator / detector / integration
        │                     └─ 本实例观察到 SiPh；EML 是另一粒度的发射器件实现
        │
        └─ TQ008 放置/封装：front-panel pluggable；OSFP/QSFP-DD 是具体产品形态
                              ↓
                    组合成一个 Route Profile 草稿
```

S1 明确允许多种 opto-electronic implementation approaches；因此规范支持 `LPO` 与多个光子实现组合，不支持 `LPO → 必然 SiPh`。S12 又证明 EML 是 InP DFB+EAM 发射器件组合，而不是与 SiPh 严格同层的互斥平台枚举。

## 2. 两条上游因果支路

### A. 为什么选择 linear/LPO，而不是 retimed

```text
模块功耗/时延/成本目标
+ capable host ASIC/equalization
+ 允许 host-module 联合配置和端到端 BER/FEC 验证
→ 去掉 module signal-path DSP/retimer 的相对价值提高
→ 选择 linear + pluggable（LPO）成为候选
```

状态：`candidate_framework_supported`。该支路由 S1/S2/S3/S10 支持，但没有同条件系统总功耗、成本和时延数值。

### B. 为什么在光子实现中考虑 SiPh

```text
8-lane parallel PIC 集成诉求
+ 希望把 laser/PIC test 与 burn-in 尽量前移到 wafer/KGD 阶段
+ 需要已有高量产平台与 pluggable deployment 经验
→ 具备相应集成与 wafer-scale test 能力的 SiPh 平台相对价值提高
→ SiPh 成为光子平台候选
```

状态：`conditional_platform_selection_hypothesis`。

支持端：S11 直接证明 Intel 自身 SiPh 平台具备 8-lane 产品结构、片上激光、wafer-scale test/burn-in、known-good-die 和规模出货经验；S8 证明 Credo 当前提供独立 800G DR8 SiPh PIC 产品；S6 证明目标 finished-module listing 明确绑定 SiPh。

限制端：

- S11 是 Intel company-specific implementation，不能继承为 Hyper 内部结构；S8 也不能证明 Credo Carmel8 进入 Hyper；
- 没有同条件 800G DR8 LPO SiPh vs EML/TFLN 的受控比较；
- S1 明确允许多种光电实现，因此上游链路约束不唯一决定 SiPh；
- S12 的 EML 证明替代发射实现存在，但并未提供与 SiPh 的等粒度优劣数据。

因此这条支路暂时只能写“何种条件下 SiPh 可进入光子平台候选池”，不能写“LPO 必须采用 SiPh”或“SiPh 优于 EML”。这些前提是否适用于 Hyper 仍未验证；增加更多 listing、组件页或平台陈述都不能把它升为 supported WHY，唯一晋升路径是同条件 800G DR8 LPO SiPh vs EML/TFLN 受控比较。

## 3. 汇合后才能谈下游物理变化

| 变化来源 | 已支持的物理变化 | 未支持的变化 |
|---|---|---|
| linear/LPO 支路 | module signal path 不用 DSP/retimer；host FEC/equalization/channel-loss 参数；coupled BER/FEC test | 系统总功耗、成本、时延幅度；生产工序和设备价值量 |
| SiPh 支路 | PIC 平台；目标产品 SiPh binding；独立 PIC 产品；Intel 特定平台的 wafer-scale test/burn-in/KGD | Hyper 的 laser/modulator/detector 结构；Hyper 具体 wafer/fiber attach/assembly 流程 |
| front-panel pluggable 支路 | OSFP/QSFP-DD/MPO 为具体产品观察 | 不能把 form factor 当成 LPO 或 SiPh 的必然值 |
| 组合耦合 | linear analog IC、host-module 联合管理和端到端测试成为角色需求 | 不能从角色需求推定具体供应链关系 |

## 4. 公司服务应按“角色 × 证据对象”挂载

| 路线层 | 角色 | 公司与直接对象 | 阶段 | 禁止外推 |
|---|---|---|---|---|
| 完整组合产品 | finished-module integrator | Hyper Photonix：两款 800G DR8 LPO SiPh listing（S6） | listed_finished_product | 不推 shipment/customer |
| SiPh PIC | PIC/product platform | Credo Carmel8；DustPhotonics L3C 技术来源（S8） | listed_component_product | 不推进入 Hyper |
| SiPh platform maturity | integrated SiPh platform | Intel SiPh platform（S11） | platform_shipment/company-stated | 不推 exact LPO target |
| linear analog | driver/TIA | MACOM PURE DRIVE（S9） | production_available_component_offer | 不推进入 Hyper |
| alternative emitter implementation | InP EML device | Lumentum EML（S12） | production_device_platform | 不推等粒度 SiPh 胜负或 target inclusion |
| module demo | partial route integrator | Eoptolink DR8 LPO demo（S7） | partial_route_demo | SiPh 未绑定到该 DR8 demo |
| SiPh wafer test equipment | wafer/PIC test system | 联讯仪器 SiPh wafer test system（S16） | production_equipment_company_disclosed | 不推进入 Hyper 或 LPO 独占 |
| advanced photonic assembly | bonding/process equipment R&D | 猎奇 laser-assisted bonding / reflow / thermocompression（S16） | equipment_process_rnd | 不推 target 量产采用 |
| host/interop/test | ecosystem | OIF participants（S3） | ecosystem_demo | 不推供货或客户采用 |

### 近邻路线的采用/出货证据

| 公司 | 已闭合字段 | 阶段 | 缺失字段 |
|---|---|---|---|
| 剑桥科技（S13） | SiPh + 800G + OSFP + DR8/DR8+ + 海外客户认证 + 大批量发货 | near-route shipment / company disclosure | LPO、客户名称、具体 reach |
| 新易盛（S14） | LPO 规模量产；另有 800G LPO 与 800G SiPh 直驱项目验收 | company production + project acceptance | 两项目是否同 SKU、DR8、客户 |
| 联特科技（S15） | 800G + SiPh + LPO + 2×DR4/2×FR4 + NPI；真实客户联合设计 | near-route NPI / customer collaboration | DR8、规模量产、认证/出货 |

这些证据证明公司服务已从“能力匹配”走到不同成熟度阶段，但没有一条能把 `800G + DR8 + LPO + SiPh + shipment/customer` 全部绑定到同一 SKU。

## 5. 对“完整路线链”的结构修正

完整链不应写成：

```text
上游需求 → LPO → SiPh → 公司
```

而应写成：

```text
上游需求
  ├─ 为什么选 linear/retimed
  ├─ 为什么选某个光子实现组合
  └─ 为什么选 pluggable/on-board/CPO
          ↓ 在 TQ005 链路画像约束下，三条决策轴汇合
条件化优劣势
          ↓
组件/接口/工序/设备/测试变化
          ↓
能力角色
          ↓
公司直接证据对象与成熟度阶段
```

这一结构既保留“为什么要这么做”，又避免把不同粒度术语强行做成一张胜负表。
