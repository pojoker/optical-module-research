# Ciena：季度电话会卡

角色：`system_vendor`。纳入理由：相干光系统、DCI与CPO光引擎观察方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：11 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：11 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：5 条已审核雷达事件（asserted 5 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2026Q2 | [S_CIEN_2026Q2](https://s25.q4cdn.com/550667411/files/content_files/Ciena-Fiscal-Q2-2026-Financial-Results-Call.pdf) | A | available | 公司IR托管的完整电话会逐字稿 |
| FY2026Q1 | [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) | A | available | 公司IR托管的完整电话会逐字稿 |
| FY2025Q4 | [S_CIEN_2025Q4](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q4/Cienas-Fiscal-4th-Quarter-and-Year-End-2025-Financial-Results-Conference-Call.pdf) | A | available | 公司IR托管的完整电话会逐字稿 |
| FY2025Q3 | [S_CIEN_2025Q3](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q3/Transcript-Cienas-Fiscal-Third-Quarter-2025-Financial-Results-Conference-Call.pdf) | A | available | 公司IR托管的完整电话会逐字稿 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL063` · fact · first_shipment · [S_CIEN_2025Q3](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q3/Transcript-Cienas-Fiscal-Third-Quarter-2025-Financial-Results-Conference-Call.pdf) `prepared remarks p.3 / scale-across project paragraph`
  - 归纳：Ciena称首个scale-across项目已开始产生收入出货
  - 原文短引：“Initial revenue shipments are underway.”
- `CL064` · forward_looking · ramping · [S_CIEN_2025Q3](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q3/Transcript-Cienas-Fiscal-Third-Quarter-2025-Financial-Results-Conference-Call.pdf) `prepared remarks p.3 / scale-across project paragraph`
  - 归纳：Ciena预计首个scale-across项目未来数季爬坡至数亿美元
  - 原文短引：“we expect this to ramp to hundreds of millions of dollars over the next several quarters”
- `CL065` · fact · first_shipment · [S_CIEN_2025Q4](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q4/Cienas-Fiscal-4th-Quarter-and-Year-End-2025-Financial-Results-Conference-Call.pdf) `prepared remarks p.4 / WL6 Nano paragraph`
  - 归纳：Ciena称WL6 Nano 800G相干可插拔已进入初始收入出货
  - 原文短引：“our WaveLogic 6 Nano 800-gig pluggables are shipped for initial revenue”
- `CL066` · fact · unknown · [S_CIEN_2025Q4](https://s25.q4cdn.com/550667411/files/doc_financials/2025/q4/Cienas-Fiscal-4th-Quarter-and-Year-End-2025-Financial-Results-Conference-Call.pdf) `Q&A pp.13-15 / supply discussion`
  - 归纳：Ciena称光子部件供应形成约束
  - 原文短引：“constraint on the photonics parts”
- `CL067` · fact · announced · [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) `prepared remarks p.3 / hyperscaler scale-across paragraph`
  - 归纳：Ciena称首个hyperscaler追加多个集群订单
  - 原文短引：“additional orders for multiple additional clusters from the first hyperscaler we announced in Q3 2025”
- `CL068` · fact · unknown · [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) `prepared remarks pp.6-7 / supply constraint discussion`
  - 归纳：Ciena称供应约束实际压低第一季度可实现收入
  - 原文短引：“our revenue in the first quarter would have been higher but for these constraints”
- `CL069` · forward_looking · sampling · [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) `prepared remarks p.5 / Nubis and Vesta paragraph`
  - 归纳：Ciena预计Vesta样品于2026年第二季度可提供
  - 原文短引：“Samples of the Vesta product will be available in calendar Q2 2026”
- `CL070` · forward_looking · announced · [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) `prepared remarks p.5 / Hyper-Rail paragraph`
  - 归纳：Ciena预计Hyper-Rail在2026年底开始标准化
  - 原文短引：“we expect will begin standardization at the end of '26”
- `CL071` · forward_looking · ramping · [S_CIEN_2026Q1](https://s25.q4cdn.com/550667411/files/doc_events/2026/03/Q1-2026-Earnings-Call-Transcript.pdf) `prepared remarks p.5 / Hyper-Rail paragraph`
  - 归纳：Ciena预计Hyper-Rail于2027年开始爬坡
  - 原文短引：“will ramp in 2027”
- `CL072` · fact · announced · [S_CIEN_2026Q2](https://s25.q4cdn.com/550667411/files/content_files/Ciena-Fiscal-Q2-2026-Financial-Results-Call.pdf) `prepared remarks p.3 / Hyper-Rail paragraph`
  - 归纳：Ciena称获得首个Hyper-Rail多轨订单
  - 原文短引：“we've been awarded the industry's first multi-rail order from a leading hyperscaler”
- `CL073` · fact · announced · [S_CIEN_2026Q2](https://s25.q4cdn.com/550667411/files/content_files/Ciena-Fiscal-Q2-2026-Financial-Results-Call.pdf) `prepared remarks p.4 / coherent modules paragraph`
  - 归纳：Ciena称赢得大型hyperscaler相干模块项目
  - 原文短引：“new win with a major hyperscaler for our high-performance Coherent modules”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
