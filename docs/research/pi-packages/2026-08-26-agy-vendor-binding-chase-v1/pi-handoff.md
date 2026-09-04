# Pi 最小交接：公司—产品—SiPh 路线绑定

本文件是本轮唯一允许交给 Pi 的事实入口。不得直接消费三个 AGY raw output。

## 任务

将已裁决的一手证据整理为：

1. 三家公司的路线参与/列品观察卡；
2. 一张“公司证据如何挂到 TQ009/TQ013”的关系草图；
3. 下一轮需要研究的问题，优先把上游原因—优势/代价—下游新问题串起来；
4. 对现有问题树的去重判断，不新建 QID。

本轮不回答路线优劣，不生成 WHY，不创建正式公司群，不写知识库。

## 可消费证据

### E-INNO-1 中际旭创

- 公司：中际旭创股份有限公司 / 苏州旭创
- 来源：2022 年年度报告，PDF p.26
- URL：`https://static.cninfo.com.cn/finalpage/2023-04-24/1216523562.PDF`
- 可消费主张：OFC2022 现场展示“基于自主设计硅光芯片”的 `800G 可插拔 OSFP 2*FR4` 和 `QSFP-DD800 DR8+` 硅光模块。
- 成熟度：`demo`。
- 补充边界：PDF p.27 只支持“800G 硅光模块开发成功并进入送测”，不支持量产；没有 exact SKU。

### E-EOPT-1 新易盛

- 公司：Eoptolink / 新易盛
- 来源：OFC 2024 官方页面，2024-03-22
- URL：`https://eoptolink.com/news/13-new-products/348-eoptolink-demonstrates-industry-1st-200g-lane-lpos-with-100g-lane-800g-lpos-entering-mass-production`
- 可消费主张：`800G OSFP DR4 LPO` 使用 silicon photonics PIC，4×200 Gb/s；页面明确称本次为 demonstration。
- 成熟度：`demo`。
- 禁止：把同页后文 100G/lane 第一、二代 LPO 的 high-volume production 转移给 200G/lane DR4；把 `EOLO-138HG-5H-SM` / `EOLD-138HG-5H-SM` 绑定为 SiPh。

### E-HYPER-1 芯速联 OSFP

- 公司：Hyper Photonix / 芯速联
- 来源：官方中文产品页 + 同页 PDF
- URL：`https://www.hyperphotonix.com/product_detail/1254.html`
- 可消费主张：精确型号 `HSO6-800-LP-P8S`；产品页标题为 `800G OSFP112 DR8 LPO FNT 硅光模块`；500 m SMF；8×106.25 Gb/s；双 MPO-12/APC；PDF 标称功耗 ≤9 W。
- 成熟度：`listed_product`；GA/量产/出货 UNKNOWN。

### E-HYPER-2 芯速联 QSFP-DD

- 公司：Hyper Photonix / 芯速联
- 来源：官方中文产品页 + 同页 PDF
- URL：`https://www.hyperphotonix.com/product_detail/1253.html`
- 可消费主张：精确型号 `HSD2-800-LP-P8S`；产品页标题为 `800G QSFP112-DD DR8 LPO 硅光模块`；500 m SMF；8×106.25 Gb/s；MTP/MPO-16 APC；PDF 标称功耗 ≤9 W。
- 成熟度：`listed_product`；GA/量产/出货 UNKNOWN。

## 字段与关系边界

- `company`、`product_or_family`、`evidence_subject`、`platform_raw`、`electrical_architecture_raw`、`form_factor_raw`、`lane_raw`、`reach_raw`、`maturity_evidence` 分开保存。
- `SiPh` 不推断 modulator、laser integration、detector、process、yield、cost。
- `LPO` 不推断每个电芯片的存在/缺失或 FEC 位置。
- `≤9 W` 是单产品 datasheet 上限，不能与其他公司产品功耗直接比较。
- `demo` 与 `listed_product` 是不同证据阶段；均不等于 shipment/customer service。
- 公司身份关系不得把芯速联与光梓信息合并。

## 允许挂载的现有问题

| QID | 本轮用途 |
|---|---|
| TQ006 | 保存 LPO raw label、lane raw；不补电架构内部职责 |
| TQ007 | 保存 SiPh / SiPh PIC raw platform binding；不补内部构成 |
| TQ008 | 保存 OSFP/QSFP-DD、连接器等公开封装字段 |
| TQ009 | 保存同一产品/产品族的路线画像观察，不创建正式 RP |
| TQ013 | 保存 demo/listed-product 两类公司—路线直接观察；不晋升 confirmed service group |
| TQ014 | 只生成取得同条件比较证据的研究问题；不输出优势结论 |
| WQ002/WQ003/WQ004 | 本轮保持空，仅说明未来什么证据才能建立 WHY |

## Pi 必须回答的设计判断

1. TQ013 的关系对象是否可以保持一个 `route_service_evidence` 类型，同时通过 `evidence_stage=demo|listed_product|shipment|customer_adoption` 区分，而不新增另一套关系？
2. 对用户最初的“双体系 + WHY”目标，本轮四条证据分别补到了哪一层，尚缺哪一层？
3. 下一轮最小研究闭环应选哪一个产品族：从上游需求/约束，经过条件化优势代价，再到下游组件/工艺/公司角色问题？只选一个，不实际回答。

## 输出要求

- 输出中文 Markdown。
- 每条事实都带 evidence id 与 URL。
- UNKNOWN 显式保留。
- 提出的问题必须映射现有 QID，并说明是否重复；不得新建 QID。
- 不得给出公司优劣、受益排序、客户名单或市场结论。
