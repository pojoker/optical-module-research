# PQ002 冻结来源包

`admissible_for_draft: true` 仅允许进入草案，不表示 promotion。

## P1：两家公司年报中的功能口径

- 中际旭创 2024 年年报，`corpus/annual-2024/300308/...pdf.txt:152-155`：发送端把电信号
  转为光信号，经光纤传送后，接收端把光信号转为电信号。
- 博创科技 2024 年年报，`corpus/annual-2024/300548/...pdf.txt:160-164`：光模块由光电子
  器件和功能电路等组成，实现光电信号收发、转换。
- 可支持：对应公司对电→光→电和收发功能的口径。
- 不可支持：行业统一内部部件顺序、完整 BOM、任一器件必备。

## P2：OIF CMIS Revision 5.4

- 存档：`corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
- SHA256：`cd57ebb1cfb8e0a9e9c7b63862b5b261855e9b77844f4cf85bd36ea3808911db`
- 印刷页 65 §6：本章核心功能默认 transmission module，resource module、cable assembly 等有例外。
- 印刷页 66 §6.1：CMIS-managed transmission module 有 Host Interface 和 Media Interface
  两个 mission-related physical interfaces。
- §6.1.1：Host Interface 是 module 与 host system 之间的高速电接口；host→module 信号称
  transmitter input，module→host 信号称 receiver output。
- §6.1.2：Media Interface 是 module 与连接远端 peer 的 media 之间的高速电或光接口；
  module→media 为 transmitter output，media→module 为 receiver input。
- 印刷页 67 §6.2.1.1：Application 以 host-side 与 media-side 间的信号传播或处理为特征，
  本质上描述二者之间的 bridge/forwarding function。
- PDF p.3 Abstract：CMIS 的 two-wire host-to-module communication 是管理接口适用范围。
- 可支持：条件化的数据方向与接口骨架，以及高速 mission data path 与低速管理路径分层。
- 不可支持：所有光模块、Media Interface 必为光、具体内部 BOM。

## P3：OIF Co-Packaging Framework 01.0

- 存档：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
- SHA256：`1d614845b92471ae50dd1c6d80a4070515bd4ef369ded9d42fe5e3df4c8457af`
- 印刷页 28–29 Glossary：
  - Optical Engine/Optical Chiplet 是把 ASIC 的 electrical signals 转为 optical signals，反向亦然；
  - EIC 可含驱动 laser/modulator 的 electronics，以及把 photodetector 产生的 photocurrent
    转为 usable electrical signal 的 TIA/post amplifier；
  - OIC/PIC 可含 waveguide、splitter、combiner、modulator、photodetector。
- 印刷页 17 Table 4：co-packaged engine 可采用 solder reflow 或 removable socket；这是具体 CPO
  实现的装配/返工实例。
- 可支持：一个 CPO optical-engine 实例中，TX 驱动/调制与 RX photodetection/TIA 的功能映射。
- 不可支持：这些部件为全部光模块必备，或 CPO 是唯一实现。

## P4：Coherent FTCE4517E1PxM 产品规格

- 存档：`corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf`
- SHA256：`82aa77513e788205ceae163a40fe5d7c1788a43b2bdad886267b3c8d40ae6621`
- PDF p.1：一只 800G-DR8 OSFP 产品，hot-pluggable，850 Gb/s aggregate，retimed
  PAM4 electrical interface，MPO-16 receptacle，I2C management interface，500 m SMF。
- PDF p.3–4：分别列出 electrical transmitter/receiver 和 optical transmitter/receiver 参数；
  electrical 与 optical 两侧都采用逐 lane 信号指标。
- 官方产品页另列该料号 transmitter=EML、receiver=PIN。
- 可支持：真实产品把高速 electrical interface 与 optical transmitter/receiver 放在同一 OSFP
  module 中；EML/PIN 只属于该料号实例；I2C 与高速数据接口分层。
- 不可支持：EML/PIN 是 800G 或所有光模块通则；datasheet 未披露完整内部连线/BOM。

## P5：OSFP Module Specification Rev 5.22

- 存档：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- SHA256：`c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- 印刷页 159–160 §15：module edge connector 分别承载 host→module TX differential pairs、
  module→host RX differential pairs、低速控制、供电和地。
- 可支持：OSFP 实例中高速 TX/RX 与低速控制、供电是不同信号类别。
- 不可支持：OSFP connector 定义模块内部光电转换过程。

## 组合规则

- P2 是条件骨架；P1 是带主体功能口径；P3/P4/P5 是不同实例。
- 原子主张若写 DSP、driver、TIA、EML、PIN 等，必须明确实例来源，不得升格为共同骨干。
- 本题停止在功能链，不回答 PQ004–PQ009 的部件、接口、制造、设备和测试细节。
