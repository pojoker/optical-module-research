# Arista：季度电话会卡

角色：`downstream`。纳入理由：数据中心交换网络需求验证方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：4 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：4 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：0 条已审核雷达事件（asserted 0 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| 2026Q2 | [S_ANET_2026Q2](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000174/ex991q226-earningsrelease.htm) | A | available | 公司向SEC提交的Q2 2026业绩Exhibit 99.1 |
| 2026Q1 | [S_ANET_2026Q1_CALL](https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/) | C | available | 免费公开第三方完整逐字稿；仅保存管理层短引文和行号锚 |
| 2026Q1 | [S_ANET_2026Q1](https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-First-Quarter-2026-Financial-Results/default.aspx) | A | available | 公司官方季度业绩新闻稿 |
| 2025Q4 | [S_ANET_2025Q4](https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Fourth-Quarter-and-Year-End-2025-Financial-Results/default.aspx) | A | available | 公司官方季度及全年业绩新闻稿 |
| 2025Q3 | [S_ANET_2025Q3](https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2025/Arista-Networks-Inc--Reports-Third-Quarter-2025-Financial-Results/) | A | available | 公司官方季度业绩新闻稿 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL036` · fact · unknown · [S_ANET_2026Q1_CALL](https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/) `transcript prepared remarks lines 122-123`
  - 归纳：Arista称行业范围多类关键组件短缺且需求超过当年供给
  - 原文短引：“We are experiencing industry-wide shortages across the board, be it wafers, silicon chips, CPUs, optics, and, of course, memory”
- `CL037` · fact · scaled · [S_ANET_2026Q1_CALL](https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/) `transcript prepared remarks lines 94-96`
  - 归纳：Arista称800GbE累计部署客户已超过100家
  - 原文短引：“greater than 100 cumulative customers to date in 800 gigabit Ethernet deployments”
- `CL038` · forward_looking · ramping · [S_ANET_2026Q1_CALL](https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/) `transcript prepared remarks lines 94-96`
  - 归纳：Arista预计1.6T于2027年进入生产规模
  - 原文短引：“expect the addition of 1.6 terabit in 2027 at production scale”
- `CL039` · fact · unknown · [S_ANET_2026Q1_CALL](https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/) `transcript Q&A / Jayshree Ullal response lines 208-210`
  - 归纳：Arista称当时CPO仍偏实验且各供应商方案高度专有并把开放CPO放在数年后
  - 原文短引：“these are still science experiments, and they are very proprietary”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
