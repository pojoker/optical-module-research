# Meta：季度电话会卡

角色：`downstream`。纳入理由：超大规模数据中心部署与资本开支验证方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：3 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：3 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：0 条已审核雷达事件（asserted 0 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| 2026Q2 | [S_META_2026Q2](https://www.sec.gov/Archives/edgar/data/1326801/000162828026050596/meta-06302026xexhibit991.htm) | A | available | 公司向SEC提交的Q2 2026业绩Exhibit 99.1 |
| 2026Q1 | [S_META_2026Q1_CALL](https://s21.q4cdn.com/399680738/files/doc_financials/2026/q1/META-Q1-2026-Earnings-Call-Transcript.pdf) | A | available | Meta IR直接链接的官方季度电话会逐字稿 |
| 2026Q1 | [S_META_2026Q1](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/) | A | available | 公司官方季度业绩新闻稿 |
| 2025Q4 | [S_META_2025Q4](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Fourth-Quarter-and-Full-Year-2025-Results/) | A | available | 公司官方季度及全年业绩新闻稿 |
| 2025Q3 | [S_META_2025Q3](https://investor.atmeta.com/investor-news/press-release-details/2025/Meta-Reports-Third-Quarter-2025-Results/) | A | available | 公司官方季度业绩新闻稿 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL042` · fact · unknown · [S_META_2026Q1_CALL](https://s21.q4cdn.com/399680738/files/doc_financials/2026/q1/META-Q1-2026-Earnings-Call-Transcript.pdf) `Q1 2026 official transcript p.4 / management discussion`
  - 归纳：Meta称Q1资本开支包含服务器数据中心与网络基础设施投资
  - 原文短引：“investments in servers, data centers, and network infrastructure”
- `CL043` · forward_looking · ramping · [S_META_2026Q1_CALL](https://s21.q4cdn.com/399680738/files/doc_financials/2026/q1/META-Q1-2026-Earnings-Call-Transcript.pdf) `Q1 2026 official transcript pp.7-8 / management discussion`
  - 归纳：Meta称将显著扩大自有数据中心版图并通过供应链协议锁定未来组件
  - 原文短引：“substantially expanding our own data center footprint”
- `CL044` · forward_looking · ramping · [S_META_2026Q1_CALL](https://s21.q4cdn.com/399680738/files/doc_financials/2026/q1/META-Q1-2026-Earnings-Call-Transcript.pdf) `Q1 2026 official transcript pp.7-8 / management discussion`
  - 归纳：Meta称多年期云协议的容量将在2026年与2027年陆续上线
  - 原文短引：“cloud deals that are scheduled to come online over the course of this year and 2027”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
