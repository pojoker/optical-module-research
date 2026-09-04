# Pi 输出本地裁决

日期：2026-08-26
裁决：`PASS_WITH_LOCAL_FIXES`。

## 1. 证据强度修正

- WQ001：`candidate_mixed_support`。需求端是 MSA 场景陈述；lane/reach/FEC/channel-loss 端是 specification。
- WQ002：`candidate_framework_supported`。去 module DSP/retimer 的相对价值来自 MSA/OIF 机制和目标；功耗/时延幅度不是受控事实。
- WQ003：`candidate_specification_supported`。host FEC/equalization、module equalization、管理参数与 coupled testing 有规范支持；process/equipment 继续 UNKNOWN。
- WQ004：`candidate_role_stage_supported`。公司只能按 exact product、component offer、partial demo 和 ecosystem demo 挂载。
- `S5 <17 W` 与 `S6 ≤9 W` 都是 product observation；比较为 `not_causally_attributable`，不能写“LPO 节省 8 W”。

## 2. QID 修正

| 节点 | 正确挂载 |
|---|---|
| scenario requirements / aggregate / reach / thermal | TQ002 |
| channel loss、retimer/DSP power path、host capability bottleneck | TQ003 |
| lane/PMD/FEC/application | TQ005 |
| LPO/retimed、host FEC/equalization responsibility | TQ006 |
| SiPh platform raw binding | TQ007 |
| front-panel pluggable 封装位置 | TQ008 |
| OSFP/QSFP-DD/MPO 等产品与接口观察 | TQ005 |
| target 与 baseline route observations | TQ009 |
| component/interface/process/equipment/test delta | TQ010 |
| physical capability requirements | TQ011 |
| capability candidates | TQ012 |
| company direct evidence stage | TQ013 |
| conditional tradeoff | TQ014 |
| causal candidates | WQ001–WQ004 |

## 3. 公司修正

- Hyper Photonix：finished-module exact target，`listed_product`。
- DustPhotonics：800G DR8 SiPh PIC component，`listed_component_product`；LPO 是 application，不绑定 Hyper。
- MACOM：linear driver/TIA `production_available_component_offer`；不等于目标模块供货。
- Eoptolink：800G DR8 LPO `partial_route_demo`；DR8 的 platform 仍 UNKNOWN。
- OIF participants：`ecosystem_demo`；不构成供货或客户关系。
- InnoLight 800G-LPO-2xDR4 不属于 target，且本包未冻结其外部来源，删除该公司行。

## 4. “完整路线链”与“事实全闭合”的区别

本轮已经实现完整链的数据结构与证据状态：每一链节存在，UNKNOWN 没有被删除。但仍有三项事实缺口：

1. 同条件系统总功耗、时延、成本对照；
2. target module 的制造工序和生产设备 comparative delta；
3. shipment/customer adoption。

因此当前状态是 `complete_chain_draft_with_explicit_unknowns`，不是 `fully_evidenced_market_chain`，不能晋升知识库。

## 5. 有效读取顺序

`source-excerpts.md → route-chain-card.md → pi-adjudication.md`。`pi-output.md` 只记录 Pi 的结构审计摘要。
