# Lumentum：季度电话会卡

角色：`core_peer`。纳入理由：激光器与光通信器件核心同业

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：2/4 个季度槽有 `available` 材料
- 陈述登记：12 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：12 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：4 条已审核雷达事件（asserted 4 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2026Q4 | [S_LITE_2026Q4](https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Announces-Fourth-Quarter-and-Full-Fiscal-Year-2026-Results/default.aspx) | A | available | 公司官方季度及全年业绩新闻稿 |
| FY2026Q3 | [S_LITE_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/06/lumentum-lite-q3-2026-earnings-transcript/) | C | available | 免费公开第三方完整逐字稿；保留短引文和行号锚 |
| FY2026Q3 | [S_LITE_2026Q3](https://s21.q4cdn.com/377324469/files/doc_financials/2026/q3/Q3-FY26-Earnings-Presentation_final.pdf) | A | available | 公司官方Q3 FY26 earnings presentation |
| FY2026Q2 | S_LITE_2026Q2 | unknown | not_collected | MVP尚未采集并人工核验该槽位 |
| FY2026Q1 | S_LITE_2026Q1 | unknown | not_collected | MVP尚未采集并人工核验该槽位 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL020` · fact · scaled · [S_LITE_2026Q3](https://s21.q4cdn.com/377324469/files/doc_financials/2026/q3/Q3-FY26-Earnings-Presentation_final.pdf) `Q3 FY26 earnings presentation p.3`
  - 归纳：Lumentum披露200G EML收入环比增长超过一倍
  - 原文短引：“200G EML revenue more than doubled sequentially”
- `CL021` · fact · scaled · [S_LITE_2026Q3](https://s21.q4cdn.com/377324469/files/doc_financials/2026/q3/Q3-FY26-Earnings-Presentation_final.pdf) `Q3 FY26 earnings presentation p.3`
  - 归纳：Lumentum披露云光模块出货环比增长超过40%
  - 原文短引：“cloud transceiver shipments, which grew over 40% sequentially”
- `CL022` · forward_looking · ramping · [S_LITE_2026Q3](https://s21.q4cdn.com/377324469/files/doc_financials/2026/q3/Q3-FY26-Earnings-Presentation_final.pdf) `Q3 FY26 earnings presentation p.3`
  - 归纳：Lumentum预计1.6T光模块在FY26 Q4爬坡
  - 原文短引：“1.6T transceivers on track for Q4 FY26 ramp”
- `CL023` · forward_looking · ramping · [S_LITE_2026Q3](https://s21.q4cdn.com/377324469/files/doc_financials/2026/q3/Q3-FY26-Earnings-Presentation_final.pdf) `Q3 FY26 earnings presentation p.3 UHP laser bullet`
  - 归纳：Lumentum预计UHP CPO激光器在2026年12月季度产生有意义收入
  - 原文短引：“on schedule to deliver meaningful revenue exiting CY 2026”
- `CL024` · fact · unknown · [S_LITE_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/06/lumentum-lite-q3-2026-earnings-transcript/) `transcript prepared remarks / systems product category`
  - 归纳：Lumentum称关键组件约束使1.6T相关段落中的模块出货显著低于客户需求
  - 原文短引：“Despite these gains, supply constraints on critical components keep our shipments well below customer demand.”
- `CL025` · forward_looking · ramping · [S_LITE_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/06/lumentum-lite-q3-2026-earnings-transcript/) `transcript lines 243-248`
  - 归纳：Lumentum称Greensboro InP fab要到2028年初才可能形成显著收入贡献
  - 原文短引：“we're still 6 or so quarters away from seeing significant contribution from Greensboro”
- `CL026` · fact · unknown · [S_LITE_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/06/lumentum-lite-q3-2026-earnings-transcript/) `transcript lines 97-99`
  - 归纳：Lumentum称scale-out CPO与OCS已有初始贡献但仍相对较小，scale-up CPO仍处早期
  - 原文短引：“initial contributions from both scale-out CPO and OCS, they are still relatively modest”
- `CL027` · fact · unknown · [S_LITE_2026Q3_C](https://www.fool.com/earnings/call-transcripts/2026/05/06/lumentum-lite-q3-2026-earnings-transcript/) `transcript Q&A / Ryan Koontz response on EML supply`
  - 归纳：Lumentum在EML与激光器供给问答中称供需缺口可能超过30%
  - 原文短引：“The supply-demand imbalance is probably even higher than we reported in our last call, somewhere greater than 30%.”

## 公司官网技术作者陈述（与管理层商业确认隔离）

- `CL016` · technical_claim · unknown · [S_LITE_BLOG_20260430](https://www.lumentum.com/en/blog/enabling-next-phase-ai-optical-infrastructure) `official blog lines 19-21`
  - 技术归纳：Lumentum技术作者提出AI光学生态需要同时应对带宽功耗散热可靠性制造和供应链问题；不视为已证实行业瓶颈
  - 原文短引：“It is pushing the entire optical ecosystem to solve for scaling in bandwidth, power, thermal efficiency, reliability, manufacturability, and supply-chain resilience.”
  - 权限：只能作为技术证据，不能进入管理层商业 validations/commitments。
- `CL017` · technical_demo · demonstrated · [S_LITE_BLOG_20260430](https://www.lumentum.com/en/blog/enabling-next-phase-ai-optical-infrastructure) `official blog lines 24-30`
  - 技术归纳：Lumentum博客称现场演示两种NVIDIA 1.6T 2xDR4 OSFP：UHP CW加硅光和8x200G EML架构
  - 原文短引：“Lumentum demonstrated two live NVIDIA 1.6T 2xDR4 OSFP transceiver modules built on different optical architectures, but both enabled by Lumentum lasers”
  - 权限：只能作为技术证据，不能进入管理层商业 validations/commitments。
- `CL018` · technical_demo · demonstrated · [S_LITE_BLOG_20260430](https://www.lumentum.com/en/blog/enabling-next-phase-ai-optical-infrastructure) `official blog lines 31-32`
  - 技术归纳：Lumentum博客称演示4x400G EML可插拔模块并将其作为未来8x400G 3.2T路径
  - 原文短引：“Lumentum showed a live 4x400G EML-based pluggable module, illustrating a practical path to future 3.2T pluggable modules”
  - 权限：只能作为技术证据，不能进入管理层商业 validations/commitments。
- `CL019` · technical_demo · demonstrated · [S_LITE_BLOG_20260430](https://www.lumentum.com/en/blog/enabling-next-phase-ai-optical-infrastructure) `official blog lines 37-40`
  - 技术归纳：Lumentum博客称演示800mW超高功率激光器以支持更多光引擎功率分发
  - 原文短引：“we demonstrated an 800 mW Super High-Power (SHP) laser, designed to support higher optical power fan-out”
  - 权限：只能作为技术证据，不能进入管理层商业 validations/commitments。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
