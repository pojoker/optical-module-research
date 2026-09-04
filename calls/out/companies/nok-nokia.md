# Nokia：季度电话会卡

角色：`system_vendor`。纳入理由：光传输、相干可插拔与AI数据中心网络系统方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：10 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：10 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：4 条已审核雷达事件（asserted 4 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| 2026Q2 | [S_NOK_2026Q2](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/) | A | available | 公司官方季度及半年度报告 |
| 2026Q1 | [S_NOK_2026Q1](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) | A | available | 公司官方季度报告 |
| 2025Q4 | [S_NOK_2025Q4](https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/) | A | available | 公司官方季度及全年报告 |
| 2025Q3 | [S_NOK_2025Q3](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/) | A | available | 公司官方季度报告 |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL051` · fact · first_shipment · [S_NOK_2025Q3](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/) `CEO Q3 comments / Network Infrastructure paragraph`
  - 归纳：Nokia称800G ZR或ZR+相干可插拔已一般可用并开始向一家美国客户发货
  - 原文短引：“became generally available and have started shipping to a large US customer”
- `CL052` · forward_looking · announced · [S_NOK_2025Q3](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q3-2025-789295/) `CEO Q3 comments / Network Infrastructure paragraph`
  - 归纳：Nokia承诺在2026年底前于San Jose启用第二座InP半导体制造设施
  - 原文短引：“We are opening a second Indium Phosphide semiconductor fabrication facility in San Jose before the end of next year”
- `CL053` · fact · unknown · [S_NOK_2025Q4](https://www.nokia.com/newsroom/nokia-corporation-financial-report-for-q4-2025-and-full-year-2025/) `CEO Q4 comments / Network Infrastructure paragraph`
  - 归纳：Nokia称2025Q4 Optical Networks净销售额同比增长17%；不能视作单一模块出货
  - 原文短引：“Network Infrastructure delivered 7% net sales growth in the fourth quarter including 17% growth in Optical Networks”
- `CL054` · fact · announced · [S_NOK_2026Q1](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) `CEO Q1 comments / Network Infrastructure paragraph`
  - 归纳：Nokia称2026Q1取得多项AI与云设计定点及可插拔和线路系统订单
  - 原文短引：“We won a number of important AI & Cloud design wins and orders for both pluggables and line systems in the quarter”
- `CL056` · forward_looking · sampling · [S_NOK_2026Q1](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) `CEO Q1 comments / OFC optical conference paragraph`
  - 归纳：Nokia预计相关产品在2027年中开始送样
  - 原文短引：“Products will begin sampling in mid-2027”
- `CL057` · forward_looking · ramping · [S_NOK_2026Q1](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) `CEO Q1 comments / Network Infrastructure paragraph`
  - 归纳：Nokia重申San Jose新InP设施预计于2026年内开始爬坡
  - 原文短引：“Our new indium phosphide manufacturing facility online in San Jose California is on track to begin ramping production later this year”
- `CL058` · fact · unknown · [S_NOK_2026Q2](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/) `CEO Q2 comments / Network Infrastructure paragraph`
  - 归纳：Nokia称2026Q2 AI与云订单流入28亿欧元且销售额同比翻倍以上；只能作混合网络需求证据
  - 原文短引：“In Q2, our AI & Cloud order intake was EUR 2.8 billion, while sales more than doubled year-on-year”
- `CL059` · fact · announced · [S_NOK_2026Q2](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/) `CEO Q2 comments / Network Infrastructure paragraph`
  - 归纳：Nokia称2026Q2在光网络和IP网络均取得长期订单；不能换算相干模块数量
  - 原文短引：“we secured long-term orders in both Optical Networks and IP Networks”
- `CL061` · forward_looking · ramping · [S_NOK_2026Q2](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/) `CEO Q2 comments / Network Infrastructure paragraph`
  - 归纳：Nokia预计约一半相关订单在未来十二个月转化为收入
  - 原文短引：“We expect around half of these orders to convert to revenue over the next twelve months”
- `CL062` · forward_looking · ramping · [S_NOK_2026Q1](https://www.nokia.com/newsroom/nokia-corporation-interim-report-for-q1-2026/) `CEO Q1 comments / OFC optical conference paragraph`
  - 归纳：Nokia预计相关产品在2027年下半年开始量产
  - 原文短引：“with volume production starting in the second half”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
