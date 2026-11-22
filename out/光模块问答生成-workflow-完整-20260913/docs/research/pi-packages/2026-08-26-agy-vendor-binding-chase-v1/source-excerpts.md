# 冻结来源摘录：三家公司 800G SiPh 路线绑定

检索日期：2026-08-26
用途：AGY 检索结果的本地核验与 Pi 最小交接；仅为 draft-only，不构成知识库写入。

## S-INNO-1 中际旭创 2022 年年度报告

- 发布者：中际旭创股份有限公司
- 文档：*中际旭创股份有限公司 2022 年度报告*
- 发布日期：2023-04-24
- URL：`https://static.cninfo.com.cn/finalpage/2023-04-24/1216523562.PDF`
- PDF 页数：222
- 文件大小：6181915 bytes
- SHA256：`f24b7dd4ccb4d9a98ab972ba286534705ae2f9c753c49b5abd6087f145f5abde`

| 位置 | 原子主张 | 短引文 |
|---|---|---|
| PDF p.26（报告页 25–26 跨页段落） | 公司在 OFC2022 展示了基于自主设计硅光芯片的 800G 可插拔产品族 | “在 OFC2022 现场展示基于自主设计硅光芯片 800G 可插拔 OSFP2*FR4 和 QSFP-DD800DR8+硅光光模块” |
| PDF p.21（产品表） | 800G OSFP/QSFP-DD 产品组合同时存在传统 EML 和硅光方案 | “除了传统的 EML 设计，还采取了以硅光为基础的方案来满足短距离传输需求” |
| PDF p.27 | 报告期末 800G 硅光模块处于开发成功、送测阶段 | “800G 硅光模块已开发成功并进入送测阶段” |

边界：

- 第一条是 `family_demo_binding`，绑定 `OSFP 2*FR4`、`QSFP-DD800 DR8+` 与自主设计硅光芯片。
- “现场展示”不得改写为商业销售、客户采用或量产。
- “开发成功并进入送测”是报告期末总体成熟度陈述，不自动绑定某个精确 SKU。
- 产品表的 EML/SiPh 并列是产品组合层声明，不能给具体 SKU 自动分配平台。

## S-EOPT-1 新易盛 OFC 2024 官方页面

- 发布者：Eoptolink Technology Inc., Ltd. / 成都新易盛通信技术股份有限公司
- 页面：*Eoptolink Demonstrates Industry 1st 200G per lane LPO 800G Optical Transceivers*
- 页面日期：2024-03-22
- URL：`https://eoptolink.com/news/13-new-products/348-eoptolink-demonstrates-industry-1st-200g-lane-lpos-with-100g-lane-800g-lpos-entering-mass-production`
- HTML 文件大小：53921 bytes
- SHA256：`f9a8df13c30ef53c890b000a84c6ed8d25a72ec7253d97c153cc4c672428c439`

| 页面位置 | 原子主张 | 短引文 |
|---|---|---|
| article body，第 2 段 | 800G OSFP DR4 LPO 产品族使用硅光 PIC，4×200 Gb/s | “Eoptolink 800G OSFP DR4 LPO transceivers utilize a silicon photonics PIC that transmits 4 parallel channels at 200Gb/s.” |
| article body，第 3 段 | 当前 200G/lambda LPO 是演示验证 | “The purpose of this demonstration is to show that LPO and half-retimed solutions are a viable alternative...” |
| article body，第 5 段 | 第一、二代 100G/lane 800G/400G LPO 已高量产 | “Both gen1 and gen2 LPOs are now available in high volume production.” |

边界：

- 第一条是 `family_demo_binding`，不是精确 SKU 绑定。
- 高量产句子的语法先行词是上一句的 100G/lane 800G/400G LPO 产品，不能转移给本页新展示的 200G/lane 800G OSFP DR4。
- 页面中的低功耗、低延迟是公司对 LPO 架构的表述；没有同条件对照，不能形成 TQ014 优势结论。
- AGY 提到的 `EOLO-138HG-5H-SM`、`EOLD-138HG-5H-SM` 未取得一手 exact-SKU→SiPh 绑定，状态只能是 `FAIL_NO_BINDING_IN_THIS_SEARCH`。

## S-HYPER-1 芯速联 800G OSFP112 DR8 LPO 产品页与 PDF

- 发布者：Hyper Photonix / 芯速联
- 页面标题：*芯速联 800G OSFP112 DR8 LPO FNT 硅光模块*
- URL：`https://www.hyperphotonix.com/product_detail/1254.html`
- 页面检索日期：2026-08-26
- HTML 文件大小：19363 bytes
- HTML SHA256：`2a6722b70056d214cd85ea6b09161bab83ef02c26f871ab1d4ca4e94afc0c7bc`
- PDF：`https://www.hyperphotonix.com/uploads/image/20250108/677e0e8119e45.pdf`
- PDF 创建时间：2025-01-08；1 页；284961 bytes
- PDF SHA256：`4fb42e88fc678c4d981d00429ce564452bec02590892ece0f4f7633be9b1c3e5`

| 位置 | 原子主张 | 短引文 |
|---|---|---|
| HTML title | 产品页将 800G OSFP112 DR8 LPO FNT 明确标为硅光模块 | “芯速联 800G OSFP112 DR8 LPO FNT 硅光模块” |
| HTML description/body | 同一产品页绑定精确型号、500 m SMF、LPO、8×106.25 Gb/s、双 MPO-12/APC | “芯速联 HSO6-800-LP-P8S 收发器专为 500 米单模光纤...” |
| PDF p.1 | PDF 绑定精确型号、LPO、500 m、连接器和功耗上限 | “HSO6-800-LP-P8S uses LPO solution”；“Power dissipation ≤ 9W” |

## S-HYPER-2 芯速联 800G QSFP112-DD DR8 LPO 产品页与 PDF

- 发布者：Hyper Photonix / 芯速联
- 页面标题：*芯速联 800G QSFP112-DD DR8 LPO 硅光模块*
- URL：`https://www.hyperphotonix.com/product_detail/1253.html`
- 页面检索日期：2026-08-26
- HTML 文件大小：22467 bytes
- HTML SHA256：`014f053a566d6ecd25513b65cdd393ec017b8503c5eeffa7b57bd04cd8455f5f`
- PDF：`https://www.hyperphotonix.com/uploads/image/20250108/677e0d6fc4e49.pdf`
- PDF 创建时间：2025-01-08；1 页；280709 bytes
- PDF SHA256：`ceee24d73ea62f7edaa5ab6c3e5c31cc49cfe6e7a1361efc774c7da3e34da172`

| 位置 | 原子主张 | 短引文 |
|---|---|---|
| HTML title | 产品页将 800G QSFP112-DD DR8 LPO 明确标为硅光模块 | “芯速联 800G QSFP112-DD DR8 LPO 硅光模块” |
| HTML description/body | 同一产品页绑定精确型号、500 m SMF、LPO、8×106.25 Gb/s、MTP/MPO-16 APC | “芯速联 HSD2-800-LP-P8S 收发器专为 500 米单模光纤...” |
| PDF p.1 | PDF 绑定精确型号、LPO、500 m、连接器和功耗上限 | “HSD2-800-LP-P8S uses LPO solution”；“Power dissipation ≤ 9W” |

共同边界：

- 中文产品页的标题与正文属于同一精确产品上下文，因此可形成 `exact_product_page_binding`：型号 ↔ 产品族 ↔ 硅光标签。
- 英文 PDF 的 `Hyper Silicon™ Optical Transceiver` 品牌语本身不作为通用“silicon photonics”定义；硅光绑定以中文官方产品页为锚，PDF 只补产品参数。
- 公开产品页/规格页证明 `listed_product`，不自动证明 GA、量产、实际出货、客户采用或市场份额。
- “低功耗、低延迟、高性价比”属于未受控营销描述；本轮不晋升为路线优势。
- Hyper Photonix 的中文主体按官网为“芯速联”；不得与“光梓信息”合并。
