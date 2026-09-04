# PQ001 冻结来源包：attempt-2

本轮只使用已经冻结的一手正文和本地定期报告。`admissible_for_draft: true` 只代表可用于
draft-only 草案，不代表允许 promotion。

## S1：中际旭创 2024 年年度报告

- 发布主体：中际旭创股份有限公司
- 来源类型：公司定期报告
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300308/300308__em_中际旭创_em__2024_2024年年度报告.pdf.txt:152-155`
- admissible_for_draft：`true`
- 完整上下文口径：发送端把电信号转换成光信号，经光纤传送后，接收端再把光信号转换成电信号。
- 可直接支持：中际旭创对光模块双向光电转换功能的公司口径。
- 不可直接支持：行业统一定义、Host/Media 标准接口、特定机械形态或内部实现。

## S2：博创科技 2024 年年度报告

- 发布主体：博创科技股份有限公司
- 来源类型：公司定期报告
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300548/300548__em_博创科技_em__2024_2024年年度报告.pdf.txt:160-164`
- admissible_for_draft：`true`
- 完整上下文口径：光模块由光电子器件和功能电路等组成，实现光电信号收发、转换；发送端电转光，
  接收端光转电。
- 可直接支持：博创科技对模块功能与构成层级的公司口径。
- 不可直接支持：完整 BOM、标准边界或所有模块均相同。

## S3：OIF CMIS Revision 5.4

- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：Implementation Agreement `OIF-CMIS-05.4`，创建并批准于 2026-05-21
- 状态核验：OIF 官方 IA 目录于本轮快照中列为 May 2026 版本
- 锚型：`web_snapshot`
- 原 URL：`https://www.oiforum.com/wp-content/uploads/OIF-CMIS-05.4.pdf`
- 存档路径：`corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`cd57ebb1cfb8e0a9e9c7b63862b5b261855e9b77844f4cf85bd36ea3808911db`
- admissible_for_draft：`true`
- 重点上下文：
  - PDF p.3 Abstract：CMIS 可用于 pluggable 或 on-board modules，以及基于 two-wire host-to-module
    management communication 的模块开发；
  - 印刷页 65 §6：本章默认 transmission module；resource module、cable assembly 等有例外；
  - 印刷页 66 §6.1：CMIS-managed transmission module 的 mission-related physical interfaces 为
    Host Interface 和 Media Interface；
  - 印刷页 66 §6.1.1：Host Interface 是 module 与 host system 间的高速电接口；
  - 印刷页 66 §6.1.2：Media Interface 是 module 与远端互连介质间的高速电或光接口；
  - 印刷页 67 §6.2.1.1：Application 是 host-side 与 media-side 信号间的 bridge/forwarding function。
- 原文短引：`a Host Interface and a Media Interface`；`bridge`。
- 可直接支持：仅在 CMIS-managed transmission module 条件下的 Host/Media 接口骨架和 bridge
  功能；Host Interface 是高速数据信号接口，不是低速管理通信本身。
- 不可直接支持：所有语境中的光模块；media 一定是光纤；所有模块实现 CMIS；具体 enclosure、
  cage、connector 或 heatsink。

## S4：OSFP Module Specification Rev 5.22

- 发布主体：OSFP MSA
- 来源类型：现行公开 MSA 规范，Rev 5.22，文档日期 2025-08-09
- 锚型：`web_snapshot`
- 原 URL：`https://www.osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_22.pdf`
- 存档路径：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- admissible_for_draft：`true`
- 重点上下文：
  - PDF p.1 摘要和印刷页 17 Scope：分列 OSFP module、host cage/mating connector、host PCB
    layout 与热要求；标准 OSFP 可有 integrated heatsink，OSFP-RHS 的 riding heatsink 属 host；
  - 印刷页 30 §3.5：module PCB card-edge pads 与 host connector 配合；
  - 印刷页 146 §14.4：可用于 OSFP module 的光接口图示为 guidelines；
  - 印刷页 159–160 §15：60-contact edge connector 承载高速 TX/RX、低速控制、供电和地。
- 原文短引：`Transmit differential pairs from host to module.`；
  `Receive differential pairs from module to host.`；`part of the host`。
- 可直接支持：OSFP/OSFP-RHS 可插拔形态的实体化 host/module 电、机械、热边界和外部光接口
  guideline。
- 不可直接支持：所有光模块采用 cage/card-edge；整份 OSFP 规范不含光学 PMD；外部连接器必然
  位于模块外壳前端；内部全部组件与工艺。

## S5：OIF 3.2T Co-Packaged Module IA

- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：Implementation Agreement `OIF-Co-Packaging-3.2T-Module-01.0`，2023-03
- 状态核验：OIF 官方 IA 目录仍列于 Energy Efficient Interfaces
- 锚型：`web_snapshot`
- 原 URL：`https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- 存档路径：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`586d0ed09f2e19d49bf92b23bb681c266d63db6c477d9c8e8c6cd6cf1d6a304f`
- admissible_for_draft：`true`
- 重点上下文：
  - 印刷页 7 §1：16 个 module 靠近 switch ASIC；optical module 把面向 ASIC 的 short-reach
    electrical interface 转换为 optical I/O；
  - 印刷页 9–10：module 的 host side 为 electrical、line side 为 optical；module 与 ASIC 可同处
    Co-Packaged Assembly Substrate，但仍作为不同对象；
  - 印刷页 24 §6：modules 可围绕 substrate，也可 embedded on board；optical module 为 pigtail，
    最终 optical connector 未由 IA 固定。
- 原文短引：`may be embedded on the board`；`close proximity to the switch ASIC`。
- 可直接支持：该特定 3.2T CPO IA 中 module 不依赖前面板 cage/card-edge；module 与 ASIC 可近邻
  或共 substrate，但仍是可区分对象；media-side 连接可经 pigtail 延伸到其他位置。
- 不可直接支持：所有 CPO 均相同；ASIC 属于 module；所有光模块均 embedded；所有外部光接口均
  是 pigtail；CPO 是唯一未来路线。

## 来源组合与状态

- S1/S2 只形成带主体的公司口径；
- S3 是条件化接口骨架，条件必须逐字保留为 CMIS-managed transmission module；
- S4 是 OSFP 可插拔实例；S5 是一份特定 CPO IA 反例；
- 不得把 OSFP 和 CPO 的机械实体拼成共同 BOM；
- OIF IA 目录快照：`corpus/web/2026-08-23/oiforum.com__implementation-agreements.html`，
  SHA256 `d6ff41cbd78583e500ffc4410451981b131b0dd87b9e726e46c3b4c09813717a`；仅用于版本状态核验；
- QSFP-DD Rev 7.1 未成功冻结，不在 attempt-2 来源集合。
