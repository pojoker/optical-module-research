# Cisco：季度电话会卡

角色：`downstream`。纳入理由：交换系统及光学产品需求验证方

## 五级覆盖（本公司在该公司数中可复算）

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

- 季度槽登记：4/4 个季度槽已登记（含未采集槽位）
- 可用来源：4/4 个季度槽有 `available` 材料
- 陈述登记：5 条 `claims.csv` 陈述（含 candidate/rejected）
- 已核陈述：5 条 `reviewed`（reviewed 仅表示原文已核，不代表独立来源交叉）
- 已核事件：0 条已审核雷达事件（asserted 0 / corroborated 0）

## 四季度覆盖

| 槽位 | 信源 | 等级 | 状态 | 缺失/说明 |
|---|---|---:|---|---|
| FY2026Q3 | [S_CSCO_2026Q3_A](https://s21.q4cdn.com/812015656/files/doc_earnings/2026/q3/transcript/Q3FY26-Prepared-Remarks.pdf) | A | available | 公司官方稳定prepared remarks PDF |
| FY2026Q2 | [S_CSCO_2026Q2_A](https://investor.cisco.com/files/doc_events/2026/02/Q2FY26-Prepared-Remarks-1.pdf) | A | available | 公司官方prepared remarks PDF |
| FY2026Q1 | [S_CSCO_2026Q1_A](https://investor.cisco.com/files/doc_events/2025/11/1/Q1FY26-Prepared-Remarks.pdf) | A | available | 公司官方prepared remarks PDF |
| FY2025Q4 | [S_CSCO_2025Q4_A](https://investor.cisco.com/files/doc_events/2025/08/1/Q4FY25-Prepared-Remarks.pdf) | A | available | 公司官方prepared remarks PDF |

## 已审核管理层陈述

> `reviewed` 仅表示原文已核（说话人、原文、锚点经人工复核），不代表独立来源交叉证实。

- `CL007` · fact · volume_order · [S_CSCO_2026Q2_A](https://investor.cisco.com/files/doc_events/2026/02/Q2FY26-Prepared-Remarks-1.pdf) `Q2 FY26 prepared remarks p.4`
  - 归纳：Cisco披露Q2来自超大规模客户的AI基础设施合计订单为21亿美元
  - 原文短引：“AI infrastructure orders taken from hyperscalers totaled $2.1B in Q2”
- `CL008` · fact · announced · [S_CSCO_2026Q2_A](https://investor.cisco.com/files/doc_events/2026/02/Q2FY26-Prepared-Remarks-1.pdf) `Q2 FY26 prepared remarks p.4 / first product atomic summary`
  - 归纳：Cisco宣布1.6T OSFP可插拔光模块；不与800G产品作跨代比较
  - 原文短引：“We also announced two new pluggable optics: a 1.6 terabits-per-second OSFP and an 800G LPO”
- `CL009` · forward_looking · scaled · [S_CSCO_2026Q1_A](https://investor.cisco.com/files/doc_events/2025/11/1/Q1FY26-Prepared-Remarks.pdf) `Q1 FY26 prepared remarks p.4`
  - 归纳：Cisco预计在FY26 Q2出货第100万颗Silicon One交换芯片
  - 原文短引：“We expect to ship our 1-millionth chip in Q2 FY26.”
- `CL010` · fact · scaled · [S_CSCO_2026Q2_A](https://investor.cisco.com/files/doc_events/2026/02/Q2FY26-Prepared-Remarks-1.pdf) `Q2 FY26 prepared remarks p.4`
  - 归纳：Cisco在下一季确认已出货第100万颗Silicon One交换芯片
  - 原文短引：“We shipped our one-millionth Silicon One chip in Q2”
- `CL012` · fact · announced · [S_CSCO_2026Q2_A](https://investor.cisco.com/files/doc_events/2026/02/Q2FY26-Prepared-Remarks-1.pdf) `Q2 FY26 prepared remarks p.4 / second product atomic summary`
  - 归纳：Cisco宣布800G LPO可插拔光模块；按800G线性电链映射
  - 原文短引：“We also announced two new pluggable optics: a 1.6 terabits-per-second OSFP and an 800G LPO”

## 公司官网技术作者陈述（与管理层商业确认隔离）

无已审核公司官网技术作者陈述。

## 分析师问题（不得视为管理层确认）

无已登记分析师问题；这不代表市场没有相关关注。

## 候选、驳回与未知

无候选或驳回陈述。未采集季度仍保持未知。
