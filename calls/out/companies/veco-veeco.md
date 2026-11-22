# Veeco：季度电话会卡

角色：`upstream_enabler`。纳入理由：InP MOCVD与离子束设备订单观察激光产能约束

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：1 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：1 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：2 条已审核雷达事件（asserted 2 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| 2026Q3 | [S_VECO_2026Q3](https://ir.veeco.com/news-and-events/news-details/2026/Veeco-Reports-Third-Quarter-2026-Financial-Results/default.aspx) | A | available | 公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT；归档 corpus/web/step4_20261122/veco_20261104_2026q3_results.txt |
| 2026Q2 | [S_VECO_2026Q2](https://www.sec.gov/Archives/edgar/data/103145/000110465926091158/veco-20260630x10q.htm) | A | available | SEC 10-Q直接文件 |
| 2026Q1 | [S_VECO_2026Q1](https://www.sec.gov/Archives/edgar/data/103145/000110465926055672/veco-20260331x10q.htm) | A | available | SEC 10-Q直接文件 |
| 2025Q4 | [S_VECO_2025Q4](https://www.sec.gov/Archives/edgar/data/103145/000110465926019711/veco-20251231x10k.htm) | A | available | SEC 10-K直接文件 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL082` · fact · unknown · [S_VECO_2026Q3](https://ir.veeco.com/news-and-events/news-details/2026/Veeco-Reports-Third-Quarter-2026-Financial-Results/default.aspx) `CEO commentary, paragraph 1 (p3)`
  - 归纳：Veeco在2026Q3业绩稿称AI基础设施推动高速光连接等领域设备询单与订单活跃；未拆分MOCVD专项订单规模
  - 原文短引：“AI infrastructure investment is accelerating technology transitions across leading-edge logic and memory, advanced packaging, and high-speed optical connectivity. This is driving unprecedented customer engagement and order activity across our differentiated portfolio.”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
