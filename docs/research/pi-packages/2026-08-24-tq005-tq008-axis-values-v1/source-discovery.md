# TQ005–TQ008 本地一手来源发现

## 范围与口径

- 仅使用任务指定的本地快照；未联网、未扩搜。
- 本文件是 `draft_only` 的来源发现，不改 canonical、不改变 coverage、不新建 QID。
- 不进入 TQ009、WHY、公司归群或路线排名。
- `contract.md` 是本轮验收合同；`post-adjudication-effective-text.md` 是唯一上游有效口径；`sources-tq004.md` 是既有来源索引。三者用于约束解释，不作为外部技术事实证据。
- 页面锚点中的“页”均指 PDF 文件页码；HTML 以页面标题、栏目标题、问答题干或可唯一识别的段落起句定位。

## TQ005：产品/链路标准轴

**最小结论：** 该轴描述 host/media 两侧可互操作的链路边界，最小记录 aggregate rate、host/media lane 数与 lane rate、modulation、FEC/PMD、media、reach，以及 wavelength/parallel-vs-WDM organization；它不能推出模块内部 DSP/linear、光子平台或封装位置。

### `standards.ieee.org__802.3df-2024.html`

- **证据类型：** IEEE 正式标准官方摘要（final-standard summary）。
- **精确定位：** 标题 `IEEE 802.3df-2024`；副标题 `IEEE Standard for Ethernet Amendment 9...`；正文起句 `This amendment includes changes to IEEE Std 802.3-2022...`。
- **能支持：** IEEE 802.3df-2024 增加 Clause 169–173、Annex 172A/173A，并规定 400/800 Gb/s 的 MAC 参数、Physical Layers 与 management parameters；因此正式标准名及其外部 PHY/PMD 边界应归 TQ005。
- **不能支持：** 本地摘要没有列出各 PMD 的完整 lane、modulation、FEC、media、reach、wavelength 数值；也不能推出 retimed/linear、EML/SiPh、OSFP/CPO。

### `standards.ieee.org__ethernet_800g_article.html`

- **证据类型：** IEEE 官方标准解读文章（官方解释层，不替代规范正文）。
- **精确定位：** 标题 `Ethernet’s Next Bar is Now – 800 Gb/s!`；段落起句 `Given industry acceptance of 8-lane electrical and optical solutions...`；Table 1；段落起句 `IEEE 802.3df™-2024, with its parallel x8 structure...`；Figure 2 前后段落。
- **能支持：** 802.3df 的 800 Gb/s 实现复用 100 Gb/s signaling，采用 parallel ×8 结构；八 lane 端口可配置为 1×8、2×4、4×2 或 8×1，并可承载标准化 100/200/400/800 GbE 组合。文章还区分 chip-to-module/chip-to-chip 电接口与 SMF 光 signaling。
- **不能支持：** 不能把文章中的架构说明当成完整 PMD 参数表；不能据此判断模块内部职责、光子器件、form factor 或放置架构。

### `oiforum.com__OIF-CMIS-05.4.pdf`

- **证据类型：** OIF 正式管理接口规范（management specification；边界/字段证据，不是 optical PMD 标准）。
- **精确定位：** p.30 §1.1 `Purpose and Scope`；p.66 §§6.1.1–6.1.2 `Host Interface` / `Media Interface`；p.197 §8.4.3 `Wavelength Information`；p.248 §8.14.8 `Media Lane to Media Wavelength and Fiber Mapping`。
- **能支持：** host lane 是 host-module 高速差分电连接；media lane 可由铜差分对、光纤上的 wavelength/carrier 或 subcarrier 承载；CMIS 可表达 wavelength 及 media-lane-to-wavelength/fiber mapping，适合作为 TQ005 字段边界与可管理元数据来源。
- **不能支持：** CMIS 明确让 `MediaInterfaceID` 指向相关标准；它自身不能替代 PMD 标准给出某产品的 aggregate rate、reach、FEC 或合规结论，也不能证明任何 advertised capability 已实现或量产。

### `lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`

- **证据类型：** 具名 MSA profile 规范；只作 profile/reference object，不另成轴值。
- **精确定位：** p.1 Abstract；p.7 §§1–2（Table 1）；p.8 §5.1；pp.9–10 §§5.2–5.6；pp.21–22 §8、Tables 12–13；p.27 §9.2。
- **能支持：** `n00G-DRn-LPO` 覆盖 1/2/4/8 条 100 Gb/s lane，53.125 GBd PAM4，RS(544,514) FEC，parallel SMF，1310 nm 附近，reach 0.5–500 m；同时定义 host-module electrical 与 optical test boundaries。这是 TQ005 字段如何共同形成一个具名 profile 的实例。
- **不能支持：** 不能把 `-LPO` 当成正式 IEEE PMD 名或第五根轴；不能推出所有 100G/lane 链路均 linear，也不能证明所有允许的 form factor/光子实现已量产。

### `coherent.com__FTCE4517E1PxM_product.html`

- **证据类型：** 公司产品实例页（observed product instance）。
- **精确定位：** 页面标题 `800G-DR+OSFP Hot Pluggable Optical Transceiver`；产品说明段落起句 `They are compliant with...`；参数表 `FTCE4517E1PxM`。
- **能支持：** 已观察实例字段包括 800G、500 m、1310 Band、Single SMF、MPO16，并声明 OSFP MSA、IEEE 802.3bs 与 P802.3ck 合规；可作为产品后缀 `DR+` 与正式标准/接口引用必须分栏记录的例子。
- **不能支持：** `DR+` 不能据此升格为 IEEE 正式标准名；页面未给出完整 host/media lane、FEC 和 PMD 参数，不能单独建立完整标准画像，也不能外推同系列全部产品。

## TQ006：电接口架构轴

**最小结论：** 该轴按 host、module/engine、optical path 之间的职责分配区分 retimed、linear、Tx-retimed/Rx-linear（LRO/RTLR）、half-retimed 与 direct-drive candidate；证据层级必须保留，尤其不能把 framework/in-progress 候选写成量产菜单。

### `lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`

- **证据类型：** 具名 MSA profile 规范。
- **精确定位：** p.8 §5.1 `System Description` 与 Figure 1；p.9 §5.2/§5.2.1；p.10 §5.6 `Host FEC Requirements` 与 §5.10 `Host Nonlinear Compensation Function`。
- **能支持：** 该 profile 的 module Tx/Rx data path 为 linear；host 承担 FEC encode/decode，并由 DSP-based SerDes 提供 equalization；§5.1 把 error correction、retiming、DAC/ADC 放在 host。模块只在电信号与光信号之间线性转换。
- **不能支持：** 只支持该具名 100G-DR-LPO profile 的规范职责，不能证明行业内所有 LPO 实现相同；也不能把低功耗目标写成同口径实测结果。

### `lpo-msa.org__faqs.html`

- **证据类型：** LPO MSA 官方 FAQ（MSA 官方解释层）。
- **精确定位：** `What is the focus of the LPO MSA?`、`What is Linear Pluggable Optics (LPO)?`、`How is an LPO module different to a module using retimers?`、`Do you have a nomenclature defined yet?` 四组问答。
- **能支持：** LPO 是 module 内无 DSP chip 的 fully linear pluggable；retimed module 在 Tx/Rx 两向由 module DSP 做复杂数字处理；FAQ 还把 LPO-to-LPO、LPO-to-retimed 与 half-linear 架构分开，并将 linear receiver + retimed transmitter 称为 LRO/half-retimed。
- **不能支持：** FAQ 的低功耗、低成本、鲁棒性陈述不能替代实测；其 roadmap 不能证明相关产品均已存在或量产；LPO 不能脱离 `pluggable` 被当作纯电架构同义词。

### `oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`

- **证据类型：** OIF framework document（候选接口框架，不是完成的产品菜单）。
- **精确定位：** pp.14–16 §7.2 `Electrical Interfaces`，Figures 5–8。
- **能支持：** Figure 5 的 re-timed 在 engine 保留 retiming；Figures 6–7 分别定义 linear amplified 与 half-retimed；Figure 8 的 direct drive 仅保留线性光通道所需 engine 功能，由 host ASIC 直接驱动 modulator/laser 并在 Rx 做 equalization。文中明确 future IA 仍需补 test points/methodologies/criteria。
- **不能支持：** 不能把 direct drive 或 half-retimed 写成完整、正式、量产的行业菜单；文中的约 50 mm 是特定 first-level substrate 接口讨论，不是跨封装统一阈值。

### `oiforum.com__current-work.html`

- **证据类型：** OIF 当前项目页（framework/in-progress 项目状态）。
- **精确定位：** `Common Electrical I/O-224G-Linear (CEI-224G-Linear)`；`Energy Efficient Interfaces`；`EEI-224G-RTLR and EEI-112G-RTLR Projects` 三段。
- **能支持：** OIF 正在研究/开发 full linear 与 RTLR；RTLR 被定义为 Tx retimed、Rx 利用 host SerDes 的 linear receiver，并明确项目仍在 developing specifications。EEI framework 同时列出 retimed、transmit retimed 与 linear interfaces。
- **不能支持：** `will support`、`is studying`、`are developing` 都是候选/在研状态，不能改写为已完成标准、已量产产品或市场采用率。

### `oiforum.com__energy-efficient-interfaces.html`

- **证据类型：** OIF 专题项目页（framework + in-progress project）。
- **精确定位：** 首屏项目说明中的 `Energy Efficient Interfaces Framework Project` 与 `Retimed Tx Linear Rx (RTLR) Project` 两个项目段落。
- **能支持：** framework 的研究范围包含 co-packaged、near-packaged、pluggable，以及 retimed、transmit-retimed、linear；RTLR 项目面向最高 200G/lane，并计划开发 200G/lane DRn/800G-FR4-500 与 100G/lane 若干介质/profile 的规范。
- **不能支持：** 不能把计划中的覆盖范围当成已发布 IA；不能推出这些职责组合的量产成熟度、功耗优劣或适用排名。

### `coherent.com__ofc-2025-multi-technology.html`

- **证据类型：** 公司现场演示实例（observed demo）。
- **精确定位：** 小节 `Silicon Photonics based 1.6T Transceivers tailored to diverse environments`；段落起句 `Live demonstrations of three different 1.6T-DR8...`。
- **能支持：** 同为 1.6T-DR8、OSFP、8×200G optical/electrical interfaces、silicon photonics 的三个演示中，至少观察到 LRO（DSP 只在 Tx retime）与 3 nm DSP 实现；因此电职责可在其他已列条件相同的实例中变化。
- **不能支持：** 不能证明三个演示均量产；第二个 `ultra-low bit error rates` 描述不足以独立判定其职责类别；不能据此做功耗或路线排名。

## TQ007：光子平台/实现轴

**最小结论：** 必须在同一 TQ007 内分别记录 `platform/material`、`light source`、`modulator/emitter`、`detector`、`integration`；SiPh/InP/GaAs 是平台或材料粒度，EML 是 DFB+EAM 的发射器件组合，MZM/VCSEL 是调制器或 emitter 粒度，PIN 是 detector 粒度，不能做同级互斥表。

### `lumentum.com__emls.html`

- **证据类型：** 器件厂商官方器件定义页。
- **精确定位：** 页面标题 `EMLs`；小节 `High-performance lasers for data center and telecom applications`；段落起句 `Lumentum manufactures indium phosphide (InP) externally-modulated lasers...`。
- **能支持：** EML 在此被定义为 InP 器件，由 DFB diode laser 与单片集成的 electro-absorption modulator（EAM）组成；DFB 连续波出光，EAM 调制为 NRZ 或 PAM4。因此 EML 跨 `light source` 与 `modulator/emitter` 的器件组合字段，并带 InP material 信息。
- **不能支持：** 不能把 EML 与 SiPh 平台或 VCSEL emitter 作为同级互斥路线；不能推出 EML 必然对应 DSP/LPO、OSFP/CPO、特定 reach 或 PMD。

### `intel.com__silicon-photonics.html`

- **证据类型：** 公司平台能力披露与公司实现实例；不是通用 SiPh 标准。
- **精确定位：** `What Is Silicon Photonics?`；`Optical Compute Interconnect (OCI)` 的 features 段；`High-Speed Photonics Components`；`High Volume-proven Silicon Photonics Platform`。
- **能支持：** Intel 把 silicon photonics 描述为平台；实例值包括 PIC、on-chip DWDM lasers/SOAs、TX PIC、RX PIC、hybrid laser-on-wafer/direct coupling，以及 PIC+CMOS EIC die stack。页面还区分无需 external laser 的 on-chip source 与可集成电路组合，适合分别记录 platform、light source 与 integration。
- **不能支持：** 不能把 Intel 的特定集成能力外推为所有 SiPh；页面没有给出通用 MZM、PIN 或材料体系的完整定义；不能据此判断平台优劣。

### `coherent.com__FTCE4517E1PxM_product.html`

- **证据类型：** 公司产品实例页。
- **精确定位：** 参数表 `FTCE4517E1PxM` 中 `Transmitter: EML`、`Receiver: PIN`。
- **能支持：** 在一个已观察 800G-DR+ OSFP 产品实例中，transmitter 为 EML、detector 为 PIN；证明 emitter/modulator 与 detector 应分别记录。
- **不能支持：** 页面没有披露完整 PIC platform/material、light-source integration 或 EML/PIN 内部结构；不能外推所有 800G-DR+、OSFP 或 EML 产品。

### `coherent.com__ofc-2025-multi-technology.html`

- **证据类型：** 公司演示实例。
- **精确定位：** `Silicon Photonics based 1.6T Transceivers...`；`1.6T Optical Transceivers Based on 200G VCSEL`。
- **能支持：** 页面分别观察到 silicon photonics architecture 的 1.6T-DR8 演示，以及采用 200G VCSEL 的 1.6T-SR8 演示；SiPh 是 platform/architecture 粒度，VCSEL 是 emitter 粒度，二者不构成同一枚举层。
- **不能支持：** 页面未给出完整 detector、light-source integration 或 material stack；不能从不同演示做性能、成本或成熟度排序。

### `oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`

- **证据类型：** OIF framework 的术语与实现边界证据。
- **精确定位：** p.18 §7.3 `Optical Interfaces`；pp.28–30 §10 `Appendix A: Glossary` 中 `EIC`、`ELS`、`Integrated Light Source`、`OIC/PIC`、`On-chip Light Source`、`Optical Chiplet`。
- **能支持：** PIC 可包含 waveguides、splitters/combiners、modulators 与 photodetectors；EIC 可含 laser/modulator driver、TIA/post-amplifier；framework 明确区分 external、integrated、on-chip light source，并举出 SiPh integrated laser 与 VCSEL engine 的不同实现候选。
- **不能支持：** glossary/framework 不能证明某组合已产品化，也不能把候选 light-source 或 PIC 实现写成穷尽字典。

### `lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`

- **证据类型：** MSA 规范许可边界。
- **精确定位：** p.7 §2，项目符号 `Opto-electronic implementation`。
- **能支持：** 规范明确允许多种 opto-electronic implementation approaches and technologies；因此 linear 电架构不固定某个 TQ007 实现。
- **不能支持：** 规范沉默不能证明任一具体 EML/SiPh/VCSEL/PIN 组合已被观察、合规或量产。

## TQ008：封装/放置架构轴

**最小结论：** 以 optical engine 相对 host ASIC、first-level substrate 与 front panel 的位置分类：front-panel pluggable、other on-board、near-package NPO、CPO 必须分开；OSFP/QSFP-DD 只作为 pluggable 子层 form factor，不设统一毫米阈值。

### `oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`

- **证据类型：** OIF co-packaging framework（TQ008 的主要定义锚）。
- **精确定位：** p.9 §5 `Introduction` 与 Figure 1；p.10 Figure 2 说明；pp.28–30 §10 Glossary 中 `CPO`、`Co-Packaged Assembly Substrate`、`Optical Chiplet`、`Pluggable Optics`。
- **能支持：** CPO 是 optical/electrical communications device 与 host ASIC 位于同一 first-level substrate；glossary 将 CPO 定义为 active optical components attached to a common substrate containing ASICs。p.10 将 packaged ASIC 与 engine 通过 socket 接到 common substrate、便于装配/返工的 Figure 2d 明称 socketed NPO。`Pluggable Optics` 则是插入系统 rack front panel 的 transceiver，并列 SFP/QSFP/QSFP-DD/OSFP 为 form-factor 例子。
- **不能支持：** p.10 另行提到 `on-board optical or electrical engine`，不能把它自动并入 NPO；framework 没有给出跨实现统一毫米阈值，也不能推出固定光子平台、电职责或量产状态。

### `osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`

- **证据类型：** form-factor MSA 正式规范。
- **精确定位：** p.1 Abstract；p.30 §3.5 `Card-edge Design (Module Electrical Interface)`；p.162 §15.4 `High-Speed Signals`。
- **能支持：** OSFP 是 `Octal Small Form Factor Pluggable Module`，规范机械/热、connector、power 与 electrical signal 边界；§15.4 规定 8 Tx/8 Rx differential pairs 及若干 lane-rate 模式。因此 OSFP 只能作为 front-panel pluggable 下的 form-factor/host electrical 子层信息。
- **不能支持：** 不能把 OSFP 当作 optical PMD、光子平台或 retimed/linear 架构；规范所列可连接 PMD configuration 不证明模块内部采用 EML、SiPh、DSP 或 LPO。

### `oiforum.com__OIF-CMIS-05.4.pdf`

- **证据类型：** OIF 管理接口规范的适用范围证据。
- **精确定位：** p.30 §1.1.1，段落起句 `The physical form factor scope of CMIS includes...`。
- **能支持：** CMIS 的物理适用范围同时包括 pluggable 与 onboard form factors，并举 QSFP-DD、OSFP、COBO；这支持“管理接口可跨放置/form factor”，也提示 generic onboard 不能仅凭 CMIS 归为 NPO。
- **不能支持：** CMIS 不定义 CPO/NPO 的操作性位置边界，也不能把被其管理的 onboard module 判定为 near-package。

### `intel.com__silicon-photonics.html`

- **证据类型：** 公司平台能力披露 + observed demo statement。
- **精确定位：** `Optical Compute Interconnect (OCI)` features 中 `Designed to be co-packaged... Stand-alone on-board implementations can also be supported`；随后关于 pluggable transceivers 的段落；页面后部 OFC live demonstration 段。
- **能支持：** 同一 Intel SiPh 平台被公司分别披露用于 pluggable transceivers、stand-alone on-board OCI 与 co-packaged OCI；页面另称曾现场演示 OCI chiplet 与 Intel CPU co-packaged。该来源直接要求把 `other on-board` 与 CPO 分开。
- **不能支持：** `can also be supported` 是平台能力，不等于已观察量产产品；不能把 stand-alone on-board 改写为 OIF NPO，也不能外推所有 SiPh 平台。

### `coherent.com__FTCE4517E1PxM_product.html`

- **证据类型：** 公司产品实例。
- **精确定位：** 页面标题 `800G-DR+OSFP Hot Pluggable Optical Transceiver`；参数表 `Form Factor: OSFP`。
- **能支持：** 观察到一个 front-panel pluggable 产品实例，其 form factor 为 OSFP。
- **不能支持：** 不能从 OSFP 推出该产品的电职责或光子平台，也不能据此比较 pluggable、NPO、CPO 的优劣。

### `lpo-msa.org__LPO_MSA_Specification_v1p2_final.pdf`

- **证据类型：** 具名 MSA profile 的规范许可边界。
- **精确定位：** p.7 §2，项目符号 `Compact transceiver form factor`；p.9 §5.2.1 关于 hardware/mechanical definitions。
- **能支持：** 100G-DR-LPO 明确 `transceiver form-factor agnostic`，仅把 QSFP、QSFP-DD、OSFP 列作例子；机械尺寸由相应 form-factor MSA 定义。因此 LPO 只能拆为 `linear + pluggable`，不能绑定 OSFP。
- **不能支持：** 规范许可多个 form factor 不证明每个组合均已有产品或量产，也不能把 LPO 与 CPO 直接当同层电架构比较。

## 跨轴守门结论

- IEEE/PMD 或具名 MSA profile 负责外部链路字段，不自动决定 module/engine 的 retiming、光子实现或位置。
- retimed、linear、LRO/RTLR、half-retimed、direct-drive candidate 是职责分配；其中 OIF current-work/framework 的 future/developing/studying 内容只记候选或在研。
- SiPh/InP/GaAs、EML/MZM/VCSEL、PIN 与 integration 必须进入 TQ007 的不同嵌套字段；当前本地来源不足以形成穷尽字典。
- `front-panel pluggable / other on-board / near-package NPO / CPO` 分开；CPO 锚定 same first-level substrate，NPO 锚定 OIF Figure 2d 的 socketed common-substrate arrangement；不虚构统一距离阈值。
- OSFP/QSFP-DD 是 pluggable form factor；标准允许、公司平台能力与 observed product/demo 三类证据不得互相替代。

## 停止状态

- `canonical_write_performed: false`
- `coverage_status_changed: false`
- `new_question_ids_created: false`
