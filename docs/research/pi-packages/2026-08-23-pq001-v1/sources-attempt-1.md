# PQ001 冻结来源包：attempt-1（历史输入）

本文件是 Pi 本轮唯一允许使用的事实材料。`admissible_for_draft: true` 仅表示可以进入
draft-only 草案，不表示已经满足知识库 promotion。

## S1：中际旭创 2024 年年度报告

- 发布主体：中际旭创股份有限公司
- 来源类型：公司定期报告
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300308/300308__em_中际旭创_em__2024_2024年年度报告.pdf.txt:152-155`
- admissible_for_draft：`true`
- 原文口径：光模块承担光电转换；发送端把电信号转换为光信号，经光纤传输后，接收端再把光信号
  转换为电信号。
- 可直接支持：中际旭创对光模块系统功能与双向转换的公司口径。
- 不可直接支持：行业唯一标准定义、具体 OSFP 边界、模块内部组件或所有产品实现。

## S2：博创科技 2024 年年度报告

- 发布主体：博创科技股份有限公司
- 来源类型：公司定期报告
- 锚型：`local_file`
- 锚：`corpus/annual-2024/300548/300548__em_博创科技_em__2024_2024年年度报告.pdf.txt:160-164`
- admissible_for_draft：`true`
- 原文口径：光模块由光电子器件和功能电路等组成，实现光电信号的收发与转换；发送端电转光，
  接收端光转电。
- 可直接支持：博创科技对模块功能和构成层级的公司口径。
- 不可直接支持：完整 BOM、特定形态接口、所有模块均有相同构成。

## S3：OSFP Module Specification Rev 5.22

- 发布主体：OSFP MSA
- 来源类型：现行公开 MSA 规范，Rev 5.22，文档日期 2025-08-09
- 锚型：`web_snapshot`
- 原 URL：`https://www.osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_22.pdf`
- 存档路径：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- 抓取日期：`2026-08-23`
- SHA256：`c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- admissible_for_draft：`true`
- 重点上下文：
  - PDF p.1 摘要：规范定义 OSFP/OSFP-RHS module、connector、cage system 的电连接、电信号、
    供电以及机械/热要求；管理接口另见 CMIS；
  - 印刷页 17 Scope：规范对象分列 module form factor、host cage/mating connector、电接口、
    host PCB layout、热要求；OSFP-RHS 的 riding heatsink 属于 host；
  - 印刷页 30 §3.5：module PCB 的 contact pads 与 connector 配合，形成模块 card-edge 电边界；
  - 印刷页 146 §14.4：列出可用于 OSFP module 的外部光接口示例，并明确这些图示是 guidelines；
  - 印刷页 159–160 §15：60-contact edge connector 承载高速 TX/RX、低速控制、供电和地。
- 原文短引：`Transmit differential pairs from host to module.`；
  `Receive differential pairs from module to host.`；`part of the host`。
- 可直接支持：仅 OSFP/OSFP-RHS 可插拔形态下的 host/module 电、机械、热和外部光接口边界。
- 不可直接支持：所有光模块共同边界、光学 PMD 的完整信号标准、模块内部全部组件和工艺。

## S4：OSFP MSA 官方 FAQ

- 发布主体：OSFP MSA
- 来源类型：官方现行页面
- 锚型：`web_snapshot`
- 原 URL：`https://www.osfpmsa.org/?scope=30713`
- 存档路径：`corpus/web/2026-08-23/osfpmsa.org__homepage.html`
- 抓取日期：`2026-08-23`
- SHA256：`09dd7e650ff6bfa30c5dcf1a532e147e813c2eb4adcd26cd96a963cf4c224509`
- admissible_for_draft：`true`
- 定位：HTML 约 117–122 行。
- 原文短引：`including the mechanical module, the card cage, the electrical interface and pinout.`
- 可直接支持：OSFP MSA 官方对自身规范覆盖范围的概括。
- 不可直接支持：cage 属于模块本体、其他 MSA 相同、完整光学信号规范或所有模块采用 OSFP。

## S5：OIF 接收 CMIS 工作的官方公告

- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：官方新闻稿，发布日期 2022-01-05；不是 CMIS 规范正文
- 锚型：`web_snapshot`
- 原 URL：`https://www.oiforum.com/oif-adopts-common-management-interface-specification-cmis-work-initiated-by-qsfp-dd-multi-source-agreement/`
- 存档路径：`corpus/web/2026-08-23/oiforum.com__cmis-adoption-2022.html`
- 抓取日期：`2026-08-23`
- SHA256：`894d0260fdb447b1bf63319adb1f79edd207d22210c7ded342b65f2949fa7be7`
- admissible_for_draft：`true`
- 定位：HTML 约 299–303 行。
- 原文短引：`host to module management communication based on a two-wire interface.`
- 可直接支持：OIF 对 CMIS 可用于 pluggable/on-board modules 及 host-to-module 管理通信的官方说明。
- 不可直接支持：CMIS 全部规范要求、任一模块均实现 CMIS、管理接口等同高速数据信号接口。

## 来源组合规则

- S1/S2 只能形成带发布主体的“公司口径”；
- S3/S4 的事实必须逐条标为 OSFP-specific；
- S5 只能形成“OIF 官方口径”，不能标成 CMIS 规范事实；
- 不得把 S1–S5 合成“所有光模块的统一标准边界”；
- QSFP-DD Hardware Rev 7.1 未成功冻结，不在本轮来源集合中。
