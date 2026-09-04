# AGY 3.7 Flash 检索审计

检索日期：2026-08-26
模型：`gemini-3.7-flash-high`
状态：AGY 仅作 source discovery；本文件裁决后才能进入来源包。

## 1. 可用入口

| AGY 入口 | 本地结果 | 裁决 |
|---|---|---|
| LPO MSA 100G-DR-LPO specification | 找到官方 38 页 PDF；可复现版本、页码与原文 | `PASS_PRIMARY` |
| OIF CEI-112G-LINEAR-PAM4 | 找到官方 OIF-CEI-05.3，Clause 29；可复现 | `PASS_PRIMARY` |
| OIF OFC 2024 CEI-Linear demo | 找到官方 13 页 PDF；可复现 interop、测试点和公司名 | `PASS_PRIMARY_DEMO` |
| OIF CMIS-VCS 1.1 | 找到官方 77 页 IA；可复现 CDR bypass、均衡、host-channel-loss、NLC 控制 | `PASS_PRIMARY` |
| Hyper Photonix 两款产品 | 已在上一包冻结 exact product page + PDF | `PASS_LISTED_PRODUCT` |
| Coherent FTCE4517E1PxM | 已有冻结官方 retimed 800G DR8 OSFP PDF | `PASS_BASELINE_PRODUCT` |
| DustPhotonics Carmel8 | 找到官方产品页，可复现 800G DR8 SiPh PIC 与 LPO application | `PASS_COMPONENT_PRODUCT` |
| MACOM PURE DRIVE | 找到官方产品页，可复现 LPO driver/TIA production availability 与 SiPh 支持 | `PASS_COMPONENT_OFFER` |
| Eoptolink 800G LPO | 找到官方 OFC 2023 页面，可复现 800G DR8 LPO demo，但不能把 DR8 精确绑定到 SiPh | `PASS_PARTIAL_ROUTE_DEMO` |

## 2. 丢弃或降级的 AGY 主张

| AGY 主张 | 问题 | 裁决 |
|---|---|---|
| LPO MSA 规范给出“40–50% 功耗下降、7–9 W 对 14–17 W” | 官方规范没有该表述或对照表 | `REJECT_HALLUCINATED_QUOTE` |
| LPO MSA 2025-03-25 发布正式 v1.0 | PDF 内为 `Draft revision 1.0`，修订日 2025-03-19；文件创建日不能代替发布状态 | `CORRECTED_DRAFT_STATUS` |
| OIF EEI Framework PDF 直接解释 LPO 取舍 | 未找到 AGY 所给文件/精确锚 | `REJECT_UNVERIFIED` |
| 固定 retimed latency、LPO latency 数字 | 来源为二手或无同条件测试 | `REJECT_UNCONTROLLED_NUMERIC` |
| Cisco 主机 SerDes 增加 1–2 W、系统净功耗表 | 未找到可复现一手原文 | `REJECT_UNVERIFIED` |
| 特定 SiPh MZM、CW laser、Ge PIN 结构自动属于目标模块 | 从平台名补内部结构，跨产品推断 | `REJECT_CROSS_INSTANCE_INFERENCE` |
| Keysight/MultiLane 的具体设备型号是生产必需设备 | OIF demo 只显示测试生态，不证明生产工艺必需 | `REJECT_AS_REQUIREMENT` |
| Eoptolink 精确 DR8 LPO 使用 SiPh | 页面只说单模 LPO 组合有 SiPh/EML/TFLN，未给 DR8 分配平台 | `PARTIAL_ONLY` |
| InnoLight 800G-LPO-2xDR4 可代表 DR8 | 产品族不同 | `ALTERNATIVE_ROUTE_ONLY` |

## 3. AGY 的有效作用

- 找到了 LPO MSA、OIF CEI、CMIS-VCS、OIF demo、DustPhotonics 与 MACOM 的一手入口；
- 帮助暴露“优势数字”最容易被生成式搜索夸大；
- 不承担最终原子主张、路线比较、WHY、公司分组或知识库映射。
