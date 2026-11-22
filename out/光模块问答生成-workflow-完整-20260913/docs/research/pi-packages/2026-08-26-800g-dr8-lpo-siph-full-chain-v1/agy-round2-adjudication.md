# AGY Round 2 裁决：SiPh WHY、工序设备、公司采用

日期：2026-08-26
搜索模型：`gemini-3.7-flash-high`
状态：AGY raw 只作发现线索；以下裁决才是有效消费口径。

## 1. 可接受结论

| 结论 | 裁决 | 可用锚 |
|---|---|---|
| LPO specification 不要求 SiPh，并允许多种 opto-electronic implementation | ACCEPT_SPECIFICATION | S1 p.7（实时基线 v1p2 final file） |
| LPO/retimed 与 SiPh/EML/TFLN 不是同一技术轴 | ACCEPT_AXIS_MODEL | S1；既有 TQ004/TQ007 裁决；S12 |
| Intel 特定 SiPh 平台具备 8-lane 产品结构、片上激光、wafer-scale test/burn-in、KGD 与规模出货经验 | ACCEPT_COMPANY_PLATFORM_ONLY | S11 |
| EML 是 InP DFB + monolithically integrated EAM | ACCEPT_DEVICE_DEFINITION | S12 |
| 未找到 800G DR8 LPO SiPh 与 EML/TFLN 的同条件受控比较 | ACCEPT_SEARCH_RESULT_WITH_SCOPE | 本轮 AGY + 本地来源审计；不是产业不存在证明 |
| 没有 target-vs-baseline 的制造工序或生产设备直接差异证据 | ACCEPT_UNKNOWN_DELTA | S1/S2 仅规定接口测试；target 与 baseline 内部平台不等粒度 |
| Intel wafer-scale test/burn-in/KGD 是 company-specific platform implementation | ACCEPT_TYPICAL_OR_COMPANY_SPECIFIC | S11；不得继承给 Hyper |
| Credo 当前 Carmel8 页面直接绑定 800G/DR8/SiPh/QSFP/OSFP/LPO application，并标明 DustPhotonics L3C laser-coupling process | ACCEPT_LISTED_COMPONENT_CURRENT_PAGE | S8；不是 finished module，不继承到 Hyper |
| Eoptolink 当前 800G LPO OSFP 页面直接绑定 2xDR4/2xFR4、8x100G、OSFP | ACCEPT_NEAR_ROUTE_LISTING | `https://www.eoptolink.com/product-solutions/800g/800g-lpo-osfp`；页面没有 SiPh，也不是 DR8 exact target |
| 未找到 exact target shipment 或 named customer adoption | ACCEPT_SEARCH_RESULT_WITH_SCOPE | 只表示本轮公开一手来源未找到 |

## 2. 驳回或降级

| AGY 输出 | 处理 | 原因 |
|---|---|---|
| “SiPh 单 PIC 替代 8 个离散 EML，必然降低 BOM/对准复杂度/良率损失” | REJECT_AS_FACT | 没有等粒度产品结构与受控对照；只能作为待验证机制问题 |
| “共享 CW laser across 8 channels”作为 target 事实 | REJECT_TARGET_INHERITANCE | 可能是特定平台实现；S6 Hyper 内部结构 UNKNOWN |
| Broadcom BCM87800/BCM87812 支持 SiPh/EML/DML 的精确引文 | REJECT_UNVERIFIED | 未回到可复现官方原页/数据表 |
| Coherent 同时开发 SiPh/EML 800G DR8 的精确引文 | REJECT_UNVERIFIED | 未回到 AGY 给出的精确页面和原文 |
| TSMC/GF 页面与精确 HVM/3D stacking 引文 | DOWNGRADE_DISCOVERY_ONLY | AGY URL 不稳定或 404；本包不冻结、不消费 |
| Mycronic ±0.5 μm、FormFactor/ficonTEC 精确能力引文 | REJECT_EXACT_PARAMETER | AGY URL 错误/重定向或不可复现；只能保留“存在相关设备能力页面”的发现线索 |
| Keysight/MultiLane 型号与 target 生产测试要求 | REJECT_AS_PRODUCTION_REQUIREMENT | 即便仪器存在，也只能证明测试生态，不证明 Hyper 产线或 LPO 独占需求 |
| Eoptolink 800G LPO OSFP 页面绑定 SiPh/DR8 exact target | REJECT_PLATFORM_AND_PMD_BINDING | 实页只列 2xDR4/2xFR4；没有 SiPh |
| Hyper `1315` 是 800G target | REJECT_WRONG_INSTANCE | 实页是 1.6T OSFP224 DR8 |
| Cisco 指定博客绑定 800G LPO+Acacia SiPh | REJECT_DEAD_URL | AGY URL 返回 404 |
| InnoLight PRWeb demo 自动绑定 SiPh | REJECT_CROSS_STATEMENT_MERGE | demo 对象与平台陈述没有同实例直接绑定 |

## 3. 最窄可用 WHY

不能写：

```text
LPO → 必须 SiPh
```

可写为条件化平台假设：

```text
如果 8-lane 产品设计优先考虑 PIC 集成、wafer-scale test/burn-in、KGD 与已有平台规模经验
→ 具备这些公司特定能力的 SiPh 平台相对价值提高
→ SiPh 可成为光子平台候选
```

状态：`conditional_platform_selection_hypothesis`，不是 `supported WHY`。该结论由 S11 证明“能力存在”，由 S1 证明“不是规范必然”，由 S6/S8 证明 target 和 component listing 存在；但缺少 SiPh vs EML/TFLN 的同条件优劣证据。

## 4. 工序/设备有效结论

- LPO-specific：能支持的是 module DSP/retimer signal-path removal 与 end-to-end linear compliance/test responsibility；
- SiPh-specific：能支持 Intel 的公司特定 wafer/PIC test、burn-in、KGD，以及 Credo 当前 Carmel8 component capability；不能把历史 DustPhotonics 测试字段自动并入当前页面；
- comparative：target 相对 retimed baseline 的 SiPh fab、laser attach、fiber attach、active alignment、生产设备增删仍为 `UNKNOWN`；
- equipment companies：只能作为能力候选，不进入 target 公司服务关系。
