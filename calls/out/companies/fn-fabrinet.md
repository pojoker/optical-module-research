# Fabrinet：季度电话会卡

角色：`core_peer`。纳入理由：光通信制造交付与产能验证方

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
| FY2026Q4 | [S_FN_2026Q4](https://investor.fabrinet.com/node/13666) | A | available | 公司官方季度及全年业绩新闻稿 |
| FY2026Q3 | [S_FN_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/04/fabrinet-fn-q3-2026-earnings-transcript/) | C | available | 免费公开第三方完整逐字稿；仅保存管理层短引文和行号锚 |
| FY2026Q3 | [S_FN_2026Q3](https://investor.fabrinet.com/news-releases/news-release-details/fabrinet-announces-third-quarter-fiscal-year-2026-financial) | A | available | 公司官方季度业绩新闻稿 |
| FY2026Q2 | [S_FN_2026Q2](https://investor.fabrinet.com/news-releases/news-release-details/fabrinet-announces-second-quarter-fiscal-year-2026-financial) | A | available | 公司官方季度业绩新闻稿 |
| FY2026Q1 | [S_FN_2026Q1](https://investor.fabrinet.com/news-releases/news-release-details/fabrinet-announces-first-quarter-fiscal-year-2026-financial) | A | available | 公司官方季度业绩新闻稿 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL032` · fact · unknown · [S_FN_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/04/fabrinet-fn-q3-2026-earnings-transcript/) `transcript prepared remarks lines 127-129`
  - 归纳：Fabrinet称datacom组件与材料短缺使出货和收入显著低于需求
  - 原文短引：“shipments and revenue were well below demand levels”
- `CL033` · fact · unknown · [S_FN_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/04/fabrinet-fn-q3-2026-earnings-transcript/) `transcript prepared remarks lines 128-130`
  - 归纳：Fabrinet称激光器是datacom供给波动的主要来源之一；同段另提内存和部分ASIC但不映射到C1
  - 原文短引：“It is mainly lasers”
- `CL034` · fact · ramping · [S_FN_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/04/fabrinet-fn-q3-2026-earnings-transcript/) `transcript Q&A lines 200-203`
  - 归纳：Fabrinet确认其向超大规模客户推进的两个datacom模块项目均为800G scale-out应用
  - 原文短引：“They are both 800G, but they are different applications and both scale-out.”
- `CL035` · fact · unknown · [S_FN_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/04/fabrinet-fn-q3-2026-earnings-transcript/) `transcript prepared remarks lines 129-131`
  - 归纳：Fabrinet称已有少量CPO收入并正与三家客户推进项目
  - 原文短引：“We are already seeing some CPO revenue, but the amounts are relatively small at this point.”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
