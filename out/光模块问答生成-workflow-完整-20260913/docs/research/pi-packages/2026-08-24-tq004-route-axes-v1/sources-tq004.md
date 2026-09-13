# TQ004 冻结一手来源包

## S1：100G-DR-LPO Specification Revision 1.0（下载文件名含 v1p2，规范层）

- 快照：`corpus/web/2026-08-24/lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`
- §1：100G-DR-LPO 定义 host-module electrical interface 与 optical interface；host 使用 DSP-based
  SerDes/FEC，模块为低功耗 pluggable。
- §2：规范明确 `form-factor agnostic`，QSFP、QSFP-DD、OSFP 只是例子；并写明允许多种
  opto-electronic implementation approaches and technologies。
- §5：模块在收发方向传递 analog signals；FEC、retiming、DAC/ADC 位于 host。
- 能支持：`LPO` 回答信号处理位置，不等于某个 form factor，也不等于某种光子平台。
- 不能支持：所有 form factor/光子平台组合都已量产；LPO 一定优于 retimed；市场主流度。

## S2：LPO MSA FAQ（MSA 官方解释层）

- 快照：`corpus/web/2026-08-24/lpo-msa.org__faqs.html`
- FAQ 将 LPO 定义为 module 内不含 DSP chip 的 pluggable solution；同时区分 LPO-to-LPO、
  LPO-to-retimed、LRO 等架构。
- FAQ 明称任何 pluggable module form factor 都可用于 LPO，并说明其建立在 IEEE/OIF 与
  OSFP/QSFP-DD 等规范之上。
- 能支持：LPO/LRO 属电信号处理架构轴，pluggable/form factor 属另一轴。
- 不能支持：FAQ 中低功耗/低成本主张不能替代同口径实测；不能外推到全部产品。

## S3：Coherent OFC 2025 官方演示（公司实例层）

- 快照：`corpus/web/2026-08-24/coherent.com__ofc-2025-multi-technology.html`
- 同一组 1.6T-DR8 transceiver 共享 OSFP、8×200G optical/electrical interfaces 与 SiPh
  architecture，但分别包括 LRO、低 BER 实现与 3 nm DSP 实现。
- 能支持：固定产品/链路、form factor 与光子平台后，电架构仍可不同；这是轴分离的强实例。
- 不能支持：三个演示均已量产；LRO 或 DSP 哪个更优；行业份额。

## S4：Intel Silicon Photonics 官方页（公司平台实例层）

- 快照：`corpus/web/2026-08-24/intel.com__silicon-photonics.html`
- 官方页同时描述 SiPh PIC 已用于 pluggable transceivers，以及 OCI chiplet 可 co-packaged with
  CPU/GPU 等，也可 stand-alone on-board。
- 能支持：同一 SiPh 平台可以进入 pluggable、on-board、co-packaged 等不同封装位置，光子平台
  不等于封装架构。
- 不能支持：所有 SiPh 均支持这些形态；这些形态已具有相同成熟度或经济性。

## S5：Coherent ECOC 2022 官方互操作演示（公司实例层）

- 快照：`corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html`
- 官方演示让 SiPh MZM PIC 的 800G-DR8+ QSFP-DD800 与 EML/PD 的 800G-DR8+ OSFP 互操作。
- 能支持：相同链路目标可由不同光子实现和不同 pluggable form factor 实现；标准/链路轴不等于
  光子平台轴或封装 form-factor 轴。
- 不能支持：SiPh 与 EML 性能、成本或份额排序。

## S6：Lumentum EML 官方产品技术页（器件定义层）

- 快照：`corpus/web/2026-08-24/lumentum.com__emls.html`
- 官方定义 EML 为 InP DFB laser + monolithically integrated EAM。
- 能支持：EML 是发射光器件/光子实现信息。
- 不能支持：EML 天然意味着 DSP、LPO、OSFP、CPO 或某个 PMD/reach。

## S7：OIF Co-Packaging Framework Document（framework 层，复用）

- 快照：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
- 光引擎与 host ASIC 的位置、CPA/substrate attach、EIC/OIC/PIC、光纤连接与可返工性属于
  co-packaging framework 的结构问题。
- 能支持：CPO/NPO/pluggable 关注的是光学相对 ASIC 的位置和系统封装边界。
- 不能支持：固定 SiPh/EML、固定 DSP/LPO、实测功耗优势、具体公司路线。

## S8：OSFP Module Specification Rev 5.22（form-factor 规范层，复用）

- 快照：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- 定义机械、连接器、供电、热与电接口边界。
- 能支持：OSFP 是 pluggable form factor，不是光子平台或 DSP 架构。
- 不能支持：OSFP 内部必须是 EML、SiPh、DSP 或 LPO。

## S9：IEEE 802.3df-2024 官方摘要（final-standard 摘要层，复用）

- 快照：`corpus/web/2026-08-23/standards.ieee.org__ethernet_800g_article.html`
- 定义 800 Gb/s lane configuration、介质与 PMD reach 等互操作目标。
- 能支持：产品/链路标准轴给出外部可互操作边界。
- 不能支持：模块内部采用哪种光子平台、电架构或封装位置。

## 本轮分析纪律

- `TQ007` 使用嵌套字段：SiPh/InP/GaAs 属 platform/material；EML 属 InP DFB+EAM 的器件级
  source+modulator 组合；VCSEL 属 emitter，三者不得直接作同级互斥枚举；
- `retimed/linear/Tx-retimed-Rx-linear/direct-drive` → `TQ006` 电职责；LPO 是
  `linear + pluggable` 复合 alias，具名 MSA profile 只作实例；
- `pluggable/other on-board/near-package NPO/CPO` → `TQ008` 放置轴；OSFP/QSFP-DD 是
  pluggable 下的 form factor；
- `DR/FR、lane、wavelength、media、reach` → `TQ005` 产品/链路标准轴；
- 一条具体路线必须是这些轴值的组合；轴之间存在耦合，但不能混成一个名词列表。
