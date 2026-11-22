# Soitec：季度电话会卡

角色：`upstream_enabler`。纳入理由：Photonics-SOI材料平台与硅光底座需求观察方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：1 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：1 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：1 条已审核雷达事件（asserted 1 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2027H1 | [S_SOI_2027H1](https://www.soitec.com/home/group/corporate/newsroom/press-releases/content/2026/11/18/soitec-reports-second-quarter-revenue-and-half-year-results-of-fiscal-year-2027) | A | available | 公司官网FY2027Q2收入及H1半年度业绩公告；本地存档HTML与清洗TXT；归档 corpus/web/step4_20261122/soi_20261118_fy27h1_results.txt |
| FY2027Q1 | [S_SOI_2027Q1](https://www.soitec.com/home/group/resource-library/content/docs/default-source/financial-documents/2026-2027/en/soitec---cp-q1%2727---en) | A | available | 公司正式季度收入公告 |
| FY2026 | [S_SOI_2026FY](https://www.soitec.com/home/group/resource-library/content/docs/default-source/financial-documents/2025-2026/en/soitec-fy%2726-pr---en) | A | available | 公司正式全年业绩公告 |
| FY2026Q3 | [S_SOI_2026Q3](https://www.soitec.com/home/group/resource-library/content/docs/default-source/financial-documents/2025-2026/en/soitec-q3%2726-pr---en) | A | available | 公司正式季度收入公告 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL083` · fact · scaled · [S_SOI_2027H1](https://www.soitec.com/home/group/corporate/newsroom/press-releases/content/2026/11/18/soitec-reports-second-quarter-revenue-and-half-year-results-of-fiscal-year-2027) `CEO commentary, paragraph 1 (p21)`
  - 归纳：Soitec在FY27H1业绩稿披露Photonics-SOI半年度收入约1.25亿美元，多数客户已签带现金定金的产能预留协议（未来数年总额约12亿美元）并将Bernin 4厂转向SOI扩产
  - 原文短引：“Looking ahead, most of our Photonics-SOI customers have committed through 2028 under capacity reservation agreements backed by cash deposits, with talks underway for extra volumes beyond. We are now pivoting our existing Bernin 4 fab to SOI to serve that demand”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
