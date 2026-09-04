# Broadcom：季度电话会卡

角色：`upstream_enabler`。纳入理由：交换ASIC、SerDes、光DSP、EML与CPO上游平台

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：4 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：4 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：1 条已审核雷达事件（asserted 1 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2026Q2 | [S_AVGO_2026Q2](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2026-financial) | A | available | 公司官方季度业绩与电话会入口 |
| FY2026Q1 | [S_AVGO_2026Q1](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial) | A | available | 公司官方季度业绩与电话会入口 |
| FY2025Q4 | [S_AVGO_2025Q4](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2025) | A | available | 公司官方季度及全年业绩与电话会入口 |
| FY2025Q3 | [S_AVGO_2025Q3](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2025-financial) | A | available | 公司官方季度业绩与电话会入口 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL045` · fact · unknown · [S_AVGO_2025Q3](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2025-financial) `CEO quote in official FY2025 Q3 results`
  - 归纳：Broadcom称FY2025Q3 AI收入同比增长63%至52亿美元；只作为非光学需求背景
  - 原文短引：“Q3 AI revenue growth accelerated to 63% year-over-year to $5.2 billion”
- `CL046` · fact · unknown · [S_AVGO_2025Q4](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-fourth-quarter-and-fiscal-year-2025) `CEO quote in official FY2025 Q4 results`
  - 归纳：Broadcom称FY2025Q4 AI半导体收入同比增长74%；不能换算光模块需求
  - 原文短引：“AI semiconductor revenue increasing 74% year-over-year”
- `CL047` · fact · unknown · [S_AVGO_2026Q1](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-first-quarter-fiscal-year-2026-financial) `CEO quote in official FY2026 Q1 results`
  - 归纳：Broadcom称FY2026Q1 AI收入84亿美元并同比增长106%；只作为非光学需求背景
  - 原文短引：“Q1 AI revenue of $8.4 billion grew 106% year-over-year above our forecast”
- `CL048` · fact · unknown · [S_AVGO_2026Q2](https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-second-quarter-fiscal-year-2026-financial) `CEO quote in official FY2026 Q2 results`
  - 归纳：Broadcom称FY2026Q2 AI半导体收入108亿美元并同比增长143%；不能换算光模块需求
  - 原文短引：“Q2 semiconductor revenue from AI of $10.8 billion grew 143% year-over-year above our forecast”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
