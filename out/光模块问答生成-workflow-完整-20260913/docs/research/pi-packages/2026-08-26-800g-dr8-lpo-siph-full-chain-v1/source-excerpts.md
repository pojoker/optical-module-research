# 冻结来源摘录：800G DR8 LPO SiPh 完整路线链

日期：2026-08-26
状态：draft-only source pack。

## S1 — LPO MSA 100G-DR-LPO Specification（实时基线已更新）

- 发布者：LPO MSA
- 文档：*Specification for 100 Gb/s per Lane Linear Pluggable Optics Single-Mode Optical Fiber Transmission*
- 文档内版本：`100G-DR-LPO Specification Revision 1.0`，正文版权日期 `March 2025`
- URL：`https://www.lpo-msa.org/files/live/sites/lpomsa/files/specs/LPO_MSA_Specification_v1p2_final.pdf`
- 冻结快照：`corpus/web/2026-08-24/lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`
- 页数：38；文件大小：1493695 bytes
- SHA256：`01e142336f001740f1f3c526c778b8fe7b4c5b6d9603e41e9795b2426f782282`

| PDF 位置 | 可支持主张 | 短引文 |
|---|---|---|
| p.7 §1–2 | 100G/lane、1/2/4/8 lanes、SMF、500 m、目标场景 | “n is the number of lanes ... 1, 2, 4 or 8” |
| p.7 Table 1 | 1310 nm、0.5–500 m、53.125 GBd、PAM4 | “Required operating range 0.5 to 500 m” |
| p.7 §1 | 规范允许多种 opto-electronic implementation approaches and technologies | “Enables a variety of opto-electronic implementation approaches and technologies” |
| p.10 §5.6 | FEC encode/decode 由 host 实现 | “relies on the host implementation of RS(544,514) FEC” |
| p.10–11 §5.11 | 传统电链路训练不能直接用于 LPO | “will not work with LPO mainly because of AGC circuits” |
| p.11 §5.11 | startup 配置/优化方法不在规范范围内 | “beyond the scope of this specification” |
| p.13 §6.9 | 模块 Tx 仍需 equalization function | “provide an equalization function in its transmit path” |
| p.14 §7.1–7.2 | raw BER、16 dB electrical channel loss | “extends ... from 13 dB to 16 dB” |
| p.21 Table 12 | `800G-DR8-LPO`、0–16 dB、0.5–500 m | `800G-DR8-LPO / LEI-800G-PAM4-8` |
| p.32 Figure 13 | host-to-host 或 stress generator + BER/error statistics 测试 | “measure BER / error statistics” |

边界：规范列出的 low power/cost/latency 是设计需求，不是实测优势；规范没有指定 SiPh、EML 或 TFLN，不能从 LPO profile 推出唯一光子平台；正式规范也不能证明市场成熟度。

## S2 — OIF CEI-112G-LINEAR-PAM4

- 发布者：OIF
- 文档：*Common Electrical I/O (CEI) 5.3*, Clause 29
- URL：`https://www.oiforum.com/wp-content/uploads/OIF-CEI-05.3.pdf`
- 创建/修订日期：2025-09-12
- 页数：685；文件大小：20058590 bytes
- SHA256：`1fa2417c96f06bc8115bcc79b7d2f7a160e35b8cc5bbebe7051fd446833e2f72`

| Printed page / clause | 可支持主张 | 短引文 |
|---|---|---|
| p.658 §29.2.3 | 电/光损伤共同影响 host receiver BER，FEC decoder 在后端 | “impairments of both the optical and electrical interfaces cause errors” |
| p.659 §29.3.1 | linear end-to-end channel 包含 host retimers、电通道、模块与光互连 | “end-to-end linear channel contains the host re-timers” |
| p.660 Figure 29-2 | linear 与 retimed module 可处于同一链路拓扑 | “Link with linear and retimed modules” |
| p.660–661 §29.3.3 | host 通过管理接口向模块传递 CTLE 参数 | “host uses the management interface to provide the module” |
| p.667 §29.3.12 | 采用 EECQ 及参考均衡器约束电眼 | “EECQ ... reference equalizer” |
| p.668–676 §29.4 | host/module output 和 stressed-input 分开测试 | “Host and module output and input tests” |
| p.676 §29.4.1.4.1.2 | 高/低损通道和 EECQ 校准 | “15.2 dB ... high loss channel and 4.0 dB ... low loss” |
| p.681 §29.A.1 | 推荐插损不等于互操作保证 | “does not signify compliance nor guarantee successful communication” |

边界：该 IA 定义电接口与测试方法，不证明某个产品功耗、成本、良率或量产。

## S3 — OIF CEI-112G-Linear OFC 2024 Demo

- 发布者：OIF
- URL：`https://www.oiforum.com/wp-content/uploads/OIF_CEI_Demo_OFC2024_Final.pdf`
- 页数：13；文件大小：1849001 bytes
- SHA256：`564a236dbf9499040cff86b8ecb118b812164d7add953cd29964bac65a139b3e`

| p. | 可支持主张 | 限制 |
|---|---|---|
| 3–4 | OIF demo 将 LPO 描述为无模块 DSP/SerDes，并宣称最多 50% module power savings | consortium/demo claim；没有完整同条件基线 |
| 5 | demo 使用 TP1a/TP2/TP4 conformance、BER/FEC margin、多厂商 host/module/test ecosystem | 证明 demo 和测试关系，不证明产品量产 |
| 5 | Eoptolink、AOI、Accelink、Luxshare 等出现 DR8 endpoint | 未把每个 DR8 endpoint 绑定到 SiPh |

## S4 — OIF CMIS-VCS 1.1

- 发布者：OIF
- 文档：`OIF-CMIS-VCS-01.1`，2025-07-17
- URL：`https://www.oiforum.com/wp-content/uploads/OIF-CMIS-VCS-01.1.pdf`
- 页数：77；文件大小：1198327 bytes
- SHA256：`1d0c2c59d1eab2efca8a7cf17c5964050a976838fd98e7556ea567ca7a7bde1c`

| p. | 可支持主张 |
|---|---|
| 34–35 §5.7–5.8 | Tx/Rx CDR 可通过 VCS enable 或 bypass |
| 51–52 §5.17–5.18 | host 向 module 提供 Rx/Tx host-channel-loss 值，模块据此设 equalization |
| 53–55 §5.19 | 模块可向 host 提供 Tx nonlinear-compensation target |

边界：VCS 是可配置管理能力，不证明目标产品实现了每一参数。

## S5 — Retimed baseline：Coherent FTCE4517E1PxM

- 产品：800G-DR8 OSFP retimed transceiver
- 来源：`corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf`
- 官方 URL 记录见 `docs/research/pi-packages/2026-08-23-expansion-v1/sources-tq002.md`
- 版本：Oct. 2024 Rev B3；7 页；421421 bytes
- SHA256：`82aa77513e788205ceae163a40fe5d7c1788a43b2bdad886267b3c8d40ae6621`

可支持：850 Gb/s、8×106.25 Gb/s retimed electrical interface、500 m SMF、OSFP、MPO-16、module power <17 W、FEC application。平台和内部 DSP 细节仍 UNKNOWN。

## S6 — Target listed products：Hyper Photonix

沿用已审核冻结证据：

- `HSO6-800-LP-P8S`：`https://www.hyperphotonix.com/product_detail/1254.html`
- `HSD2-800-LP-P8S`：`https://www.hyperphotonix.com/product_detail/1253.html`
- 上一包：`docs/research/pi-packages/2026-08-26-agy-vendor-binding-chase-v1/source-excerpts.md`

可支持：800G DR8 LPO 硅光、8×106.25 Gb/s、500 m SMF、OSFP/QSFP-DD、连接器、module power ≤9 W、`listed_product`。不支持 GA/量产/客户、内部 SiPh 结构或两款同内部实现。

## S7 — Eoptolink 800G LPO demo

- 页面：*Eoptolink Launches Innovative 800G Linear-drive Pluggable Optics During OFC 2023*
- 日期：2023-03-06
- URL：`https://eoptolink.com/news/341-eoptolink-launches-innovative-800g-linear-drive-pluggable-optics-during-ofc-2023`
- HTML：53749 bytes；SHA256：`01398c9a5af88ccdfec048f24ac7723731ad4e1821e9b41d1d291f931f2a1521`

可支持：800G LPO portfolio、无 DSP/CDR 的公司表述、OSFP/QSFP-DD、DR8 图片标签、OFC live demo；单模 portfolio 包含 SiPh/EML/TFLN。不能把 DR8 精确分配给 SiPh，因此只是 `partial_route_demo`。

## S8 — Credo Carmel8（当前产品页；DustPhotonics 技术来源）

- 当前页面：*Carmel8 — 800G DR8 Silicon Photonics Chip - Credo*
- 当前 URL：`https://credosemi.com/products/silicon-photonics/carmel8/`
- 实时核对：2026-08-26；页面 publisher/site owner 为 Credo，页面写明 integrated lasers 使用 `DustPhotonics Low-Loss Laser Coupling (L3C™) process`；Credo 官网同时链接“Credo Completes Acquisition of DustPhotonics”公告。

可支持：Credo 当前列出的 800G DR8 SiPh Tx PIC、8×100G PAM4/53.125 Gbaud、integrated lasers（DustPhotonics L3C process）、QSFP/OSFP 与 LPO/LRO applications。阶段：`listed_component_product`。不能证明它进入 S6 的芯速联模块；历史 DustPhotonics 页面中的 post-burn-in/electrical-optical-test 字段在当前页面未重新核验，因此不在实时口径中使用。

## S9 — MACOM PURE DRIVE

- 页面：*MACOM PURE DRIVE — Linear Drive Optical Solutions*
- URL：`https://www.macom.com/pure-drive-linear-architecture`

可支持：PURE DRIVE TIA/laser drivers 对 LPO 的 production availability；支持 Silicon Photonics/EML/TFLN；`MAOM-005408` 为 4×106G PAM4 linear SiPh driver、wirebond interface、SMF application。阶段：`production_available_component_offer`。不能证明进入 S6 模块或覆盖完整 DR8 module。

## S10 — LPO MSA FAQ

- 发布者：LPO MSA
- URL：`https://www.lpo-msa.org/home/faqs.html`
- 冻结快照：`corpus/web/2026-08-24/lpo-msa.org__faqs.html`
- 文件大小：12034 bytes
- SHA256：`f9e55874fdb8fd937177765c1956a90ea6ae35f480dfca960f1022ada7e99762`

| 快照行 | 可支持主张 | 边界 |
|---|---|---|
| 60–66 | capable ASIC、well-designed transmission lines；利用 host equalization；组织方称无 DSP 可降低功耗、成本和时延 | MSA/组织陈述，不是同条件系统实测 |
| 68–69 | LPO-to-retimed 可实现，但属于 engineered link 且在该 MSA specification scope 外 | 只界定规范范围，不证明所有组合能互操作 |
| 75 | LPO MSA-compliant modules 被描述为 protocol agnostic | 不等于任意 host/module 即插即用 |
| 90–93 | LPO-to-retimed、LRO 等属于后续路线/命名边界 | 不证明成熟度、产品供应或采用 |

## S11 — Intel Silicon Photonics 平台页

- 发布者：Intel
- URL：`https://www.intel.com/content/www/us/en/architecture-and-technology/silicon-photonics/silicon-photonics-overview.html`
- 冻结快照：`corpus/web/2026-08-24/intel.com__silicon-photonics.html`
- SHA256：`0850e9466775f258ce5a092f05bc049aa2ad97f19ee0ac95807ac5553a924b71`

| 快照行 | 可支持主张 | 边界 |
|---|---|---|
| 3230–3244 | Intel 公司平台覆盖 400G/800G/1.6T、DR/FR；公司称 8-lane 可实现低成本结构 | Intel 平台陈述，不是所有 SiPh，也不是与 EML 的受控比较 |
| 3238–3241 | Intel 实现片上 laser array、wafer-scale test、laser burn-in 与 photonics known-good-die | company-specific implementation；不能继承给 S6 Hyper 产品 |
| 3242、3489–3491 | Intel 称已出货超过 800 万 PIC、3200 万片上激光器，并用于 pluggable transceiver | 证明 Intel SiPh 平台成熟度/出货，不证明 800G DR8 LPO 出货 |
| 3489–3491 | hybrid laser-on-wafer direct coupling 支持 wafer-scale manufacturing and testing | 只支持 Intel 工艺能力；不证明行业统一工序或设备 |

## S12 — Lumentum EML 官方器件页

- 发布者：Lumentum
- 页面：*EMLs — High-performance lasers for data center and telecom applications*
- URL：`https://www.lumentum.com/en/optical-communications/products/source-lasers-ics-and-photodiodes/emls`
- 冻结快照：`corpus/web/2026-08-24/lumentum.com__emls.html`
- SHA256：`8a71d2b3b3deb8cb7e991846a76b2f8f2b840c1adb8813b25c3ed3ba8399c899`

可支持：Lumentum 在内部 InP wafer foundry 制造 EML；EML 由 DFB laser 与单片集成 EAM 构成。它证明 EML 是另一种发射器件/集成实现，不是 SiPh 的同粒度平台值，也不天然绑定 retimed、LPO、OSFP 或特定 reach。

## S13 — 剑桥科技 2025 年年度报告

- 文件：`corpus/annual/603083/603083/603083__em_剑桥科技_em__2025_2025年年度报告.pdf`
- SHA256：`cf464ac57cf9c4566c57c611385faae02a774206fc4db61e53db8cddeb952c6d`

术语边界：下表中的 `LPO/TRO` 为年报原文。本包只做逐字保留，不把 `TRO` 规范化成其他架构术语，也不据此外推产品属性。

| PDF 页 | 可支持主张 | 边界 |
|---|---|---|
| 12 | 100G/lane SiPh 800G 产品族列有 DR8/FR8/LR8、2×DR4/FR4/LR4 与 800G LPO/TRO | 同一产品族并列项不能自动求交集成 DR8 LPO SKU |
| 14 | 公司称全系列 SiPh 800G 产品实现海外核心客户批量发货 | 公司披露；不证明每个 SKU、LPO 或 DR8 均出货 |
| 22 | 公司称 SiPh 800G OSFP DR8/DR8+ 获海外大客户认证并于 2025 年大批量发货 | 支持 `SiPh + 800G + DR8/DR8+ + certification/shipment`；不支持 LPO、客户名称或具体 reach |

## S14 — 新易盛 2025 年年度报告

- 文件：`corpus/annual/300502/300502/300502__em_新易盛_em__2025_2025年年度报告.pdf`
- SHA256：`3432905a431a8254c2274c2188269e94cfc5a69e92c7d34332a5a3a7da8b15b6`

可支持：公司称已规模量产 LPO 模块；研发项目分别披露 800G LPO 项目和采用 SiPh 的 800G 直驱 QSFP-DD/OSFP 项目通过验收。不能把两个项目合并为同一 DR8 LPO SiPh SKU，也不能推出客户或出货量。

## S15 — 联特科技 2025 年年度报告

- 文件：`corpus/annual/301205/301205/301205__em_联特科技_em__2025_2025年年度报告.pdf`
- SHA256：`5c63e5465728d6863cc58535f369698e367ccf0aaa6248b8c4d0d8df33972bcb`

可支持：公司与客户在 LPO 方案上联合设计；完成 800G SiPh 2×DR4/2×FR4 LPO 开发与 NPI 转产。它证明另一 PMD 的 `800G + SiPh + LPO + NPI`，不证明 DR8、规模量产、客户认证或出货。

## S16 — SiPh 工序/设备发行人披露

### 猎奇智能设备招股书文本

- 文件：`corpus/legacy-input/lieqi_prospectus.txt`
- SHA256：`edd8d6c13a76825375029e0b4c7dc94bccf06a307c5b669eddf97df3b1a56e81`
- 印刷页 1-1-89 至 1-1-94：贴片、wirebond、光学耦合、点胶/UV 固化与老化测试等通用光模块封测骨干。
- 印刷页 1-1-102：发行人针对 SiPh 集成研发 laser-assisted bonding、local laser reflow、flip-chip thermocompression 等工艺。

### 联讯仪器招股书文本

- 文件：`corpus/legacy-input/lianxun_prospectus.txt`
- SHA256：`5f27213b0f8e45f5d3f657e4700f68f974a7cc39186cb2de45ed36e7ac0f89b1`
- 印刷页 1-1-93：SiPh wafer test system 包括测试机、耦合测试模组、probe station、wafer handler 与 optical/DC/RF probes。
- 印刷页 1-1-22 至 1-1-23：发行人披露该类系统在 2024 年实现收入，800G 核心测试仪器已大规模量产供货。

边界：S16 只能证明通用/SiPh 平台的工序和设备能力以及发行人披露的成熟度，不能证明 Hyper 使用这些设备，也不能形成 target-vs-baseline 设备净增删表。
