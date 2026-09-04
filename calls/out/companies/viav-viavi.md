# VIAVI：季度电话会卡

角色：`upstream_enabler`。纳入理由：1.6T测试验证需求与量产测试卡点观察方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：0 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：0 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：0 条已审核雷达事件（asserted 0 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2026Q3 | [S_VIAV_2026Q3](https://investor.viavisolutions.com/news-events/news-releases/news-details/2026/VIAVI-Announces-Third-Quarter-Fiscal-2026-Results/default.aspx) | A | available | 公司官方季度业绩与电话会入口 |
| FY2026Q2 | [S_VIAV_2026Q2](https://investor.viavisolutions.com/news-events/news-releases/news-details/2026/VIAVI-Announces-Second-Quarter-Fiscal-2026-Results/) | A | available | 公司官方季度业绩与电话会入口 |
| FY2026Q1 | [S_VIAV_2026Q1](https://investor.viavisolutions.com/news-events/news-releases/news-details/2025/VIAVI-Announces-First-Quarter-Fiscal-2026-Results/default.aspx) | A | available | 公司官方季度业绩与电话会入口 |
| FY2025Q4 | [S_VIAV_2025Q4](https://investor.viavisolutions.com/news-events/news-releases/news-details/2025/VIAVI-Announces-Fourth-Quarter-and-Fiscal-Year-2025-Results/default.aspx) | A | available | 公司官方季度及全年业绩入口 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

未知：本 MVP 尚无已审核管理层陈述。

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
