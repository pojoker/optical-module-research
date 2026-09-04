# Applied Optoelectronics：季度电话会卡

角色：`core_peer`。纳入理由：800G与1.6T模块供给和产能信息密度高

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：2/4 个季度槽有 `available` 材料
- 陈述登记：10 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：9 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：1 条已审核雷达事件（asserted 1 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| 2026Q2 | [S_AAOI_2026Q2](https://investors.ao-inc.com/news-releases/news-release-details/applied-optoelectronics-reports-second-quarter-2026-results) | A | available | 公司官方季度业绩新闻稿 |
| 2026Q1 | [S_AAOI_Q1_RESULT_A](https://investors.ao-inc.com/node/17011) | A | available | 公司官方季度业绩材料；与C级逐字稿并列登记 |
| 2026Q1 | [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) | C | available | 免费公开第三方逐字稿；仅保存短引文和定位 |
| 2025Q4 | S_AAOI_2025Q4 | unknown | not_collected | MVP尚未完成逐字稿人工核验 |
| 2025Q3 | S_AAOI_2025Q3 | unknown | not_collected | MVP尚未完成逐字稿人工核验 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL001` · fact · first_shipment · [S_AAOI_Q1_RESULT_A](https://investors.ao-inc.com/node/17011) `CEO quote paragraph`
  - 归纳：AAOI称Q1完成对一家大型超大规模客户的首次800G批量交付
  - 原文短引：“We completed our first volume shipment of our 800G products to one of our large hyperscale customers in Q1.”
- `CL002` · fact · scaled · [S_AAOI_Q1_RESULT_A](https://investors.ao-inc.com/node/17011) `CFO quote paragraph`
  - 归纳：AAOI称Q1末800G模块月产能接近10万只
  - 原文短引：“exiting Q1 with total manufacturing capacity of nearly 100,000 units of 800G transceivers per month”
- `CL003` · forward_looking · ramping · [S_AAOI_Q1_RESULT_A](https://investors.ao-inc.com/node/17011) `CEO quote paragraph`
  - 归纳：AAOI预计800G从Q2开始明显放量
  - 原文短引：“we continue to anticipate a strong volume ramp of our 800G products starting in Q2”
- `CL005` · fact · unknown · [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `Q&A / response lines 227-230`
  - 归纳：管理层把名义产能到实际收入的时差归因于制造周期
  - 原文短引：“It is just timing on how long it takes to do the manufacturing process, really.”
- `CL006` · fact · unknown · [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `prepared remarks line 150`
  - 归纳：AAOI称其2026收入水平受产能与供应链而非市场需求限制
  - 原文短引：“this revenue level is limited by our production capacity and supply chain, not market demand”
- `CL013` · fact · unknown · [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `Q&A lines 231-233`
  - 归纳：AAOI称800G或1.6T 2xFR4每只模块需要四颗激光器，使供给更难
  - 原文短引：“it would be very tough for 800G or 1.6T 2xFR4, because you need four lasers”
- `CL014` · fact · unknown · [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `Q&A lines 231-233`
  - 归纳：AAOI称当时MOCVD设备处于全面积压状态
  - 原文短引：“Right now MOCVD is on complete backlog”
- `CL015` · fact · unknown · [S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `Q&A lines 172-182`
  - 归纳：AAOI管理层称行业存在InP激光器制造产能短缺
  - 原文短引：“We see a shortage of indium phosphide laser manufacturing capacity across the industry right now”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

- `CL004` Timothy Savageaux：分析师追问名义产能与收入预测之间的差异；这只是问题而非事实确认（[S_AAOI_2026Q1_C](https://www.fool.com/earnings/call-transcripts/2026/05/07/aaoi-q1-2026-earnings-call-transcript/) `Q&A / Timothy Savageaux lines 224-226`）

## 候选、驳回与未知

- `CL011` `candidate`：AAOI提到不同客户可能采用不同流程；尚待人工扩展上下文和第二来源
