# NVIDIA：季度电话会卡

角色：`downstream`。纳入理由：AI集群架构与互连需求方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：2 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：2 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：0 条已审核雷达事件（asserted 0 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2027Q1 | [S_NVDA_2026Q1_CALL](https://s201.q4cdn.com/141608511/files/doc_financials/2027/q1/NVDA-Q1-2027-Earnings-Call-20-May-2026-5_00-PM-ET.pdf) | A | available | NVIDIA IR托管的官方季度电话会校订逐字稿 |
| FY2027Q1 | [S_NVDA_2026Q1](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2027/default.aspx) | A | available | 公司官方季度业绩新闻稿 |
| FY2026Q4 | [S_NVDA_2025Q4](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/) | A | available | 公司官方季度及全年业绩新闻稿 |
| FY2026Q3 | [S_NVDA_2025Q3](https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Third-Quarter-Fiscal-2026/) | A | available | 公司官方季度业绩新闻稿 |
| FY2026Q2 | [S_NVDA_2025Q2](https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2026/default.aspx) | A | available | 公司官方季度业绩新闻稿 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL040` · fact · scaled · [S_NVDA_2026Q1_CALL](https://s201.q4cdn.com/141608511/files/doc_financials/2027/q1/NVDA-Q1-2027-Earnings-Call-20-May-2026-5_00-PM-ET.pdf) `Q1 FY27 corrected transcript p.3 / management discussion`
  - 归纳：NVIDIA称Spectrum-X规模已超过其他以太网网络同行合计
  - 原文短引：“Spectrum-X is now larger than all Ethernet network peers combined”
- `CL041` · fact · scaled · [S_NVDA_2026Q1_CALL](https://s201.q4cdn.com/141608511/files/doc_financials/2027/q1/NVDA-Q1-2027-Earnings-Call-20-May-2026-5_00-PM-ET.pdf) `Q1 FY27 corrected transcript p.3 / management discussion`
  - 归纳：NVIDIA称数据中心网络收入约150亿美元并同比接近三倍
  - 原文短引：“Data Center networking revenue of $15 billion nearly tripled year-over-year”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
