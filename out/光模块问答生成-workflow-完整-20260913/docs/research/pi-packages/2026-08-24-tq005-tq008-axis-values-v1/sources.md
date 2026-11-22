# TQ005–TQ008 冻结一手来源包

本文件只索引冻结快照。详细锚点、支持范围和拒绝外推见 `source-discovery.md`。

## TQ005 链路/产品标准

- **S1 IEEE 802.3df-2024 官方摘要与 IEEE 官方解读**
  - `corpus/web/2026-08-23/standards.ieee.org__802.3df-2024.html`
  - `corpus/web/2026-08-23/standards.ieee.org__ethernet_800g_article.html`
  - 类型：正式标准官方摘要 + 官方解释。
  - 只支持：MAC/PHY/PMD、lane 配置、media/reach 等外部链路边界。
- **S2 OIF CMIS 5.4**
  - `corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
  - 类型：正式管理接口规范。
  - 只支持：Host Interface / Media Interface、Application Descriptor 与 wavelength/fiber mapping 字段；不替代 PMD 标准。
- **S3 100G-DR-LPO Revision 1.0（下载文件名含 v1p2）**
  - `corpus/web/2026-08-24/lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`
  - 类型：具名 MSA profile。
  - 只支持：一个完整 profile 如何联合 rate/lane/PAM4/FEC/SMF/1310 nm/reach 与 host-module 电接口。
- **S4 Coherent FTCE4517E1PxM 产品页**
  - `corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_product.html`
  - 类型：已观察公司产品实例。
  - 只支持：800G-DR+、500 m、SMF、MPO16、OSFP、EML/PIN 等该产品字段；`DR+` 不升格为 IEEE 标准名。

## TQ006 电接口职责

- **S5 LPO MSA FAQ**
  - `corpus/web/2026-08-24/lpo-msa.org__faqs.html`
  - 类型：MSA 官方解释。
  - 只支持：LPO、retimed、LRO/half-linear 的职责边界与命名；价值主张不替代实测。
- **S6 OIF Co-Packaging Framework 01.0**
  - `corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
  - 类型：framework。
  - 只支持：re-timed、linear amplified、half-retimed、direct-drive 候选的功能分配；不代表完成 IA 或量产菜单。
- **S7 OIF Current Work**
  - `corpus/web/2026-08-24/oiforum.com__current-work.html`
  - 类型：官方在研项目页。
  - 只支持：CEI-224G-Linear、EEI、RTLR 与 NPO 项目的当前研究范围。
- **S8 OIF Energy Efficient Interfaces**
  - `corpus/web/2026-08-24/oiforum.com__energy-efficient-interfaces.html`
  - 类型：framework / 在研项目页。
  - 只支持：co-packaged、near-packaged、pluggable 与 retimed、Tx-retimed、linear 被交叉研究；不证明标准已完成。
- **S9 Coherent OFC 2025 演示**
  - `corpus/web/2026-08-24/coherent.com__ofc-2025-multi-technology.html`
  - 类型：已观察公司演示。
  - 只支持：同一 1.6T-DR8/OSFP/SiPh 中观察到 LRO 与 DSP-retimed；以及另一项 200G VCSEL 演示。

## TQ007 光子实现

- **S10 Intel Silicon Photonics 官方页**
  - `corpus/web/2026-08-24/intel.com__silicon-photonics.html`
  - 类型：公司平台能力披露与公司实例。
  - 只支持：SiPh/PIC、片上光源、pluggable/on-board/co-packaged 等 Intel 实现；不外推所有 SiPh。
- **S11 Lumentum EML 官方器件页**
  - `corpus/web/2026-08-24/lumentum.com__emls.html`
  - 类型：器件定义。
  - 只支持：EML = InP DFB + 单片集成 EAM。
- **S12 Coherent ECOC 2022 演示**
  - `corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html`
  - 类型：已观察公司演示。
  - 只支持：InP EML 定义、SiPh MZM PIC 与 EML/photodetector 的特定互操作演示、VCSEL AOC 实例。

## TQ008 封装/放置

- **S13 OSFP Module Specification Rev 5.22**
  - `corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
  - 类型：正式 form-factor MSA。
  - 只支持：OSFP 的机械、connector、power、thermal 与 electrical signal 边界；不能推出内部 PMD、光子平台或电职责。
- S2、S3、S4、S6、S10 同时提供 TQ008 的管理范围、form-factor 许可、产品实例、NPO/CPO 定义和平台能力披露。

## 强制证据标签

任何主张必须使用以下之一：`formal_standard`、`msa_spec`、`framework_or_in_progress`、`company_platform_statement`、`observed_product_or_demo`、`analytical_inference`。

规范允许或沉默不等于观察到产品；公司平台能力不等于量产产品；framework 候选不等于完成标准。
