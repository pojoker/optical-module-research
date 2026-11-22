# PQ001 冻结来源包：attempt-3

`admissible_for_draft: true` 只代表可进入 draft-only 草案，不代表允许 promotion。

## S1：中际旭创 2024 年年度报告

- 发布主体：中际旭创股份有限公司
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300308/300308__em_中际旭创_em__2024_2024年年度报告.pdf.txt:152-155`
- admissible_for_draft：`true`
- 完整上下文：发送端电转光，经光纤传送后，接收端光转电。
- 可支持：该公司的双向光电转换功能口径。
- 不可支持：行业统一定义、标准接口或机械边界。

## S2：博创科技 2024 年年度报告

- 发布主体：博创科技股份有限公司
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300548/300548__em_博创科技_em__2024_2024年年度报告.pdf.txt:160-164`
- admissible_for_draft：`true`
- 完整上下文：光模块由光电子器件和功能电路等组成，实现收发与光电转换。
- 可支持：该公司的功能/构成口径。
- 不可支持：完整 BOM、标准边界或所有模块相同。

## S3：OIF CMIS Revision 5.4

- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：Implementation Agreement `OIF-CMIS-05.4`，2026-05-21
- 锚型：`web_snapshot`
- 原 URL：`https://www.oiforum.com/wp-content/uploads/OIF-CMIS-05.4.pdf`
- 存档路径：`corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`cd57ebb1cfb8e0a9e9c7b63862b5b261855e9b77844f4cf85bd36ea3808911db`
- admissible_for_draft：`true`
- 完整上下文：
  - PDF p.3 Abstract：CMIS 可用于 pluggable/on-board modules，以及有 two-wire host-to-module
    management communication 的模块开发；这是管理协议适用范围；
  - 印刷页 65 §6：核心功能默认 transmission module，resource module/cable assembly 有例外；
  - 印刷页 66 §6.1：mission-related physical interfaces 为 Host Interface 和 Media Interface；
  - §6.1.1：Host Interface 是 module/host system 间高速电接口；
  - §6.1.2：Media Interface 是 module/remote media 间高速电或光接口；
  - 印刷页 67 §6.2.1.1：Application 是 host-side/media-side 间的 bridge/forwarding function。
- 可支持：只在 CMIS-managed transmission module 条件下的接口骨架和 bridge 功能；高速 Host
  Interface 与低速管理通信是不同层。
- 不可支持：所有光模块、media 必为光、具体 enclosure/cage/connector/heatsink。

## S4：OSFP Module Specification Rev 5.22

- 发布主体：OSFP MSA
- 来源类型：现行 MSA 规范，Rev 5.22，2025-08-09
- 锚型：`web_snapshot`
- 原 URL：`https://www.osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_22.pdf`
- 存档路径：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- admissible_for_draft：`true`
- 完整上下文：
  - 印刷页 17 §1 Scope：module form factor 与 host cage/mating connector、host PCB layout 分列；
    标准 OSFP/OSFP800/OSFP1600 module `includes` air-cooled integrated heatsink；OSFP-RHS 系列
    接触 `a riding heatsink which is part of the host`；标准 OSFP 还可选额外 riding heatsink；
  - 印刷页 30 §3.5：module PCB 的 card-edge contact pads 与 §5.10 host connector 配合；
  - 印刷页 146 §14.4：展示 module-side optical receptacle 和 channel orientation；Duplex LC 等
    connector 方案是可用示例，图示 `meant to be guidelines`，实际 module/connector 几何可不同；
  - 印刷页 159–160 §15：60-contact module edge connector 承载高速 TX/RX、低速控制、供电和地。
- 可支持：OSFP/OSFP-RHS 的实体化电、机械、热和 module-side optical receptacle 边界。
- 不可支持：所有模块采用 cage/card-edge/receptacle；整份 OSFP 规范是否完整定义 PMD；内部 BOM。

## S5：OIF 3.2T Co-Packaged Module IA

- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：Implementation Agreement `OIF-Co-Packaging-3.2T-Module-01.0`，2023-03
- 锚型：`web_snapshot`
- 原 URL：`https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- 存档路径：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`586d0ed09f2e19d49bf92b23bb681c266d63db6c477d9c8e8c6cd6cf1d6a304f`
- admissible_for_draft：`true`
- 完整上下文：
  - 印刷页 7 §1：module 近 switch ASIC；optical module 把 short-reach electrical 转 optical I/O；
  - 印刷页 9–10：host side electrical、line side optical；module 与 ASIC 可同处 Co-Packaged
    Assembly Substrate，但仍是不同对象；
  - 印刷页 24 §6：module 可围绕 substrate 或 embedded on board；optical module 为 pigtail，
    最终 optical connector 位置/实现未由 IA 固定。
- 可支持：该特定 IA 展示不以前面板 cage/card-edge 为 module 必要边界的 CPO 实现，以及不同
  media-side 衔接位置。
- 不可支持：所有 CPO 均如此；ASIC/substrate 属 module；所有光模块 embedded/pigtail；唯一路线。

## 组合规则

- S3 只作条件骨架，S4/S5 是不同实例，S1/S2 是公司口径；
- 不得把实例机械实体拼成共同 BOM；
- OIF 当前 IA 目录快照仅用于版本状态核验，不生成原子主张；
- QSFP-DD Rev 7.1 未冻结，不使用。
