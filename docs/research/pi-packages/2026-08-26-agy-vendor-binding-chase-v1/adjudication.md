# AGY 公司—产品—SiPh 路线绑定裁决

日期：2026-08-26
状态：draft-only；不落知识库；不改变 TQ/PQ/WQ 覆盖状态。

## 1. 总裁决

| 公司 | 最强合格绑定 | 证据阶段 | 本轮允许表达 | 本轮禁止表达 |
|---|---|---|---|---|
| 中际旭创 / InnoLight | `OSFP 2*FR4`、`QSFP-DD800 DR8+` ↔ 自主设计硅光芯片 | `family_demo_binding`；另有 800G SiPh 开发送测 | 公司曾展示这些硅光产品族；报告期末 800G SiPh 总体进入送测 | 精确 SKU、量产、客户服务、出货、一般性优劣 |
| 新易盛 / Eoptolink | `800G OSFP DR4 LPO` ↔ silicon photonics PIC ↔ 4×200 Gb/s | `family_demo_binding` | 公司在 OFC 2024 展示该产品族 | 把 100G/lane LPO 的高量产转移到 200G/lane DR4；把具体 EOLO/EOLD SKU 标为 SiPh |
| 芯速联 / Hyper Photonix | `HSO6-800-LP-P8S`、`HSD2-800-LP-P8S` ↔ 产品页“硅光模块” | `exact_product_page_binding` / `listed_product` | 公司官网公开列出两个精确 SiPh LPO DR8 产品 | GA、量产、销量、具名客户、低功耗/成本路线优势 |

## 2. AGY 输出修正

### 中际旭创

- `T-OL8CNT-N00` 不能作为 SiPh 实例；官方目录检索结果将其列为 EML CWDM/PIN 2×FR4。
- 年报的 OFC2022 句子足以形成产品族—SiPh—公司展示角色三元绑定，但成熟度只能是 `demo`。
- AGY 所列 OFC2023 PRNewswire 与 OFC2024 PRWeb 三条候选主张本轮未冻结全文锚点，统一标记 `not_consumed_unfrozen`；它们不进入 Pi handoff。
- “800G 产品批量出货”与“800G 硅光模块进入送测”在相邻段落中共存；不得把前者偷换成 800G SiPh 批量出货。
- OFC2022 的 `OSFP 2*FR4` SiPh 展示与现行目录中的 EML SKU 可以同时成立；产品族展示绑定不得读作该产品族全线均为 SiPh。
- AGY 的 “Remaining next query: None” 不成立。若要升级，仍需搜精确 SKU 一手产品页、送样/供货/量产主体与时间边界。

### 新易盛

- AGY 给出的 OFC 2023 来源卡只有新闻归档 URL，不足以冻结具体句子，本轮不消费该卡。
- OFC 2024 精确 URL 和正文已经本地核实，可消费。
- AGY 对 OFC2024 候选句的改写与网页原文不完全一致；本包只消费 `source-excerpts.md` 中冻结的网页原文。
- `EOLO-138HG-5H-SM`、`EOLD-138HG-5H-SM` 只保留为失败线索，不能用于产品—平台绑定。
- “Both gen1 and gen2 LPOs ... high volume production”只绑定 100G/lane LPO，不绑定刚展示的 200G/lane DR4。

### 芯速联

- AGY 正确纠正公司中文主体：Hyper Photonix = 芯速联，不是光梓信息。
- 中文产品页的标题与正文共同形成 exact-product-page binding；不是跨页面拼接。
- 对应英文产品页未出现 SiPh/PIC 字样，英文 PDF 的 `Hyper Silicon™` 也不用于补强；SiPh 锚仅为中文官方产品页。
- 产品页和 PDF 可形成产品字段卡，但只证明公开列品，不证明实际商业成熟度。

## 3. 对“服务某路线”的临时分层

本轮不创建公司群，也不晋升正式 `route_service_evidence`。为了避免把“展示”写成“服务”，Pi 只能使用以下草稿级观察标签：

1. `route_family_demo_observation`：公司一手材料把公司、产品族、平台和展示动作连在一起；只说明参与展示/验证。
2. `route_exact_product_listing_observation`：公司官方产品页把精确型号与路线轴值连在一起；只说明公开列品。
3. `route_shipment_or_customer_service_observation`：必须另有同主体、同产品/产品族、同阶段的供货/出货/客户证据；本轮三家公司均不创建。

这些是证据阶段标签，不是第三套知识体系。它们最终应作为 TQ013 关系的状态/证据字段，而不是新增主轴。

## 4. 与两套知识体系和 WHY 桥的关系

- 物理知识体系：本轮只观察模块级字段（SiPh PIC、LPO、form factor、lane、连接器、功耗上限），不反推 PIC 内部器件、工艺或设备。
- 技术路线体系：本轮形成产品族/实例对 TQ006–TQ009 轴值的候选绑定，并形成 TQ013 的公司参与证据草稿。
- WHY 桥：本轮没有受控比较或物理机制证据，因此不生成 WHY；“低功耗/低延迟/高性价比”也不晋升。

## 5. 停止边界

- 不写 `knowledge.yaml`、`why_links`、公司服务群或正式 Route Profile。
- 不把公开列品等同于 GA/量产，不把展示等同于客户服务。
- 不根据 LPO 推断 DSP/CDR 的精确位置，除非同产品资料明确披露。
- 不根据 SiPh 推断光源集成方式、调制器、探测器、foundry、良率或成本。
