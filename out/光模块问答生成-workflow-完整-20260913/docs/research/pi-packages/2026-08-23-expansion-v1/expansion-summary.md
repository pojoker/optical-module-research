# PQ002 / TQ002 / WQ001 扩展小样审阅摘要

日期：2026-08-23
状态：`draft-only；未落知识库；Kimi K3 与 Cursor 复核 PASS；最终验证通过`

## 一句话判断

这次扩展已经开始呈现“基础物理问题逐步长出细节，同时由技术路线需求建立 WHY 关系”的形态，
但它仍只是受控小样：形成了 18 条分支主张与 5 条关系草案，没有改变任何问题覆盖状态，也没有
生成新的问题编号。

## 1. 物理知识分支：PQ002

本轮不再把某一种 800G 产品结构冒充所有光模块的共同结构，而是分成四层：

1. CMIS-managed transmission module 的条件化 Host/Media 接口骨架；
2. 公司对“电转光 / 光转电”功能的产品口径；
3. Coherent 800G DR8 OSFP 的 EML/PIN 单产品实例；
4. OIF CPO optical engine 的 EIC/OIC/PIC 框架实例。

产物为 8 条原子主张。它回答了收发方向、Host/Media 边界、接口级 TX/RX 功能链、管理与供电路径
和高速 mission data path 的分层；没有把 EML、PIN、EIC、OIC 或某种 attach 方式升格为共同必备。

由证据缺口触发的细化方向只挂到已有问题：

- `PQ004`：单产品 datasheet 没有披露 EML/PIN 两侧的完整器件级连线与 BOM；
- `PQ005`：mid-board optical connector 的形态、位置、是否存在返工点与返工实现方式；
- `PQ009`：connector insertion loss、optical budget、TX power、RX sensitivity、margin 等量值。

有效勘误：`PQ002-a3-d01` 中“唯一核心功能骨架”统一改读为“本轮采用的 CMIS 条件化接口骨架”。

## 2. 技术路线分支：TQ002

本轮先建立路线比较所需要的六种约束输入，而不是提前比较 EML、SiPh、LPO、CPO 的胜负：

| 约束 | 本轮建立的口径 | 未闭合内容 |
|---|---|---|
| 带宽 | 速率、lane 结构、介质与 reach 的组合 | 不能由 800G 标签直接推出最佳 lane 架构 |
| 距离 | 按介质与 PMD 联合定义的标称 reach | 铜互连、10/40 km 的 final 文本仍待核验 |
| 功耗 | form-factor power class、产品 dissipation、framework target 分层 | CPO 实测节能比较缺失 |
| 成本 | 建立成本、安装、运营与维护维度 | 缺公开金额和同口径路线比较 |
| 密度 | port lane flexibility 与 substrate footprint 分层 | 缺 ports/RU 等量化结果 |
| 维护 | hot-pluggable、rework、field access 与 repairability 分层 | 缺生命周期成本量化证据 |

产物为 10 条原子草案。final standard、历史 objectives、form-factor 规范、单产品与 framework 文本
被明确分层；没有生成公司群、路线胜负或市场份额结论。

有效勘误：`hot-pluggable` 是产品/form-factor 能力；`hot-plug/hot-unplug` 是 OSFP 规范处理的
功耗瞬态事件，二者均不能直接证明维护成本下降。“机架内/DC/园区”只作阅读提示。

日期勘误：IEEE 802.3df-2024 为 `Board Approval 2024-02-15`、`Published 2024-03-15`。

## 3. WHY 关系分支：WQ001

WQ001 没有形成第三套知识树，而是给前两套体系建立五条候选关系：

| 需求侧 | 中间约束 | 物理侧 | 强度 |
|---|---|---|---|
| 带宽 | lane 与 Host/Media 接口容量 | 逐 lane 电/光收发 | 规范结构支持，含单产品实例 |
| 距离 | 介质与 PMD | 标称 reach、500 m SMF 单产品接口实例 | 规范结构支持；CPO connector budget 退回注记 |
| 功耗 | power class、host enable | thermal design/validation | 规范结构支持；OSFP 单源双侧使用，CPO 仅目标语言 |
| 密度 | port configuration、footprint | retention、solder/socket、yield | 规范结构支持；同一 OIF 来源双侧使用 |
| 维护 | 按可插拔产品 / CPO framework 分支 | 可插拔、返工与现场访问属性 | 两个分支均为受限推论；成本未闭合 |

这里的“为什么”不是一句目的论解释，而是可审计链条：

`场景需求 → 接口/链路约束 → 物理机制 → 可观察指标`

成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值和 ports/RU 均未桥接。任何一条关系都
不能被用于直接推出技术路线选择、公司归群或受益顺序。

## 4. 本轮拦截的外行错误

- 把某只 800G DR8 OSFP 的 EML/PIN 结构写成所有光模块的共同结构；
- 把 engine-to-substrate 的 solder/socket 装配表误当 Media Interface；
- 把历史 IEEE objectives 当作 802.3df-2024 final standard；
- 把 power class 当产品实测功耗，把 CPO 节能目标当实测结论；
- 把 hot-pluggable 能力、hot-plug 功耗瞬态与维护成本下降混为一谈；
- 从带宽、距离、密度或维护要求直接跳到某条路线或某类公司受益；
- 为了让问题树“长得快”而补造新问题编号。

## 5. 建议审核者重点判断

1. PQ002 的“共同骨架 / 单产品 / CPO framework”分层是否足够清楚；
2. TQ002 的六约束能否作为后续路线比较的共同输入，而不隐含路线结论；
3. WQ001 的五条桥是否真正有双侧证据，B2/B5 场景拆分与 B3 单源披露是否充分；
4. PQ 研究注记是否按“形态→PQ005、量值→PQ009”正确挂接；
5. 在不落库的前提下，这个循环是否已经足以进入下一批问题扩展。

## 6. 状态与下一步门槛

- canonical write：false
- coverage status change：false
- new question IDs：false
- 首轮 Kimi 与 Cursor 均为 `PASS_WITH_FIXES`；修正已汇总到 `post-review-effective-text.md`；
  二次复核两者均为 `PASS`，允许进入下一批 draft-only 扩展。
- 本轮即使复核通过，也不自动落知识库。
