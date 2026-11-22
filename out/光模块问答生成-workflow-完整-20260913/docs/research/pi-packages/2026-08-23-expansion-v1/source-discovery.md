# PQ002 / TQ002 一手来源发现

日期：2026-08-23
状态：`source_discovery_only`
用途：为 PQ002「电→光→电的功能链如何工作？」与 TQ002「不同场景的带宽、距离、功耗、密度、成本和维护约束是什么？」准备可审计的一手来源候选。本文不是问题答案，不代表任何主张获准落库。

## 1. 发现结论

现有一手来源足以支撑下一步分别起草：

1. 一个有条件的功能骨架：在 `CMIS-managed transmission module` 且 media side 为光接口时，数据从 host-side 高速电接口进入模块，经 Application 所代表的传播或处理功能到达 optical media side；远端模块执行反向过程，把 media-side 输入送回 host-side 高速电输出。
2. 若干实现实例：OIF CPO framework 展示 driver/modulator、photodetector/TIA 等功能映射；Coherent 800G-DR8 OSFP 展示 EML/PIN、逐 lane 电/光参数、I2C 管理与 500 m 产品实例。
3. 一个六约束证据框架：带宽与距离由 IEEE/OIF 接口规范直接限定；功耗、密度与维护需要同时看 form factor、产品规格和系统实现；成本目前只能找到标准开发阶段的成本维度，不能形成产品价格或路线成本排序。

不能据此形成的结论包括：所有光模块共有同一内部 BOM；所有 800G 都采用 EML/PIN；CPO 一定比 pluggable 低功耗或低成本；reach 可单独决定技术路线；hot-pluggable 自动等于低维护成本。

## 2. 候选来源总表

| ID | 层级 | 发布主体与文件 | 主要用途 | 主要限制 |
|---|---|---|---|---|
| SD01 | 条件化骨架 | OIF，CMIS Revision 5.4 | PQ002：Host/Media Interface、数据方向、Application bridge、管理/数据分层 | 只适用于 CMIS-managed transmission module；Media Interface 也可能是电接口 |
| SD02 | 实现实例 / framework | OIF，Co-Packaging Framework 01.0 | PQ002：optical engine 的 TX/RX 功能映射；TQ002：功耗、密度、返工与可靠性权衡 | framework 中大量为 expected/target/possible，不是所有 CPO 的实测结论 |
| SD03 | 产品实例 | Coherent，FTCE4517E1PxM 800G-DR8 OSFP | PQ002：一只产品的电侧、光侧、管理侧和 EML/PIN；TQ002：850 Gb/s、500 m、<17 W、hot-plug | 只对应一个料号，未披露完整内部 BOM/连线 |
| SD04 | form-factor 规范 | OSFP MSA，Module Specification Rev 5.22 | PQ002：高速 TX/RX、低速控制、供电分层；TQ002：power class、系统热验证、hot-plug 瞬态 | 不定义模块内部光电转换链；power class 不是实际产品功耗 |
| SD05 | 最终标准状态 + 官方解读 | IEEE SA，IEEE 802.3df-2024 | TQ002：400/800 Gb/s 标准范围；800G x8 在不同介质/reach 的组合 | 官方解读不是规范正文，不能替代 PMD 合规条款；不说明模块内部路线 |
| SD06 | 历史项目目标 | IEEE P802.3df Objectives，2022-03-17 | TQ002：展示 bandwidth、media、reach、lane 是多维输入 | 是历史目标，不等于最终标准已纳入全部目标 |
| SD07 | 标准开发经济性文件 | IEEE P802.3df CSD | TQ002：成本、安装、运营能耗、维护连续性是独立约束 | 不提供模块价格、成本数值或路线排名 |
| SD08 | coherent 场景规范 | OIF，800ZR IA 01.0 | TQ002：800G、80–120 km amplified DWDM DCI 场景；PQ002：coherent 数据路径实例 | 不限制具体 form factor；不能代表全部 800G、全部 coherent 或实际产品功耗 |
| SD09 | CPO 规范实例 | OIF，3.2T Co-Packaged Module IA 01.0 | TQ002：3.2T building block、靠近 ASIC、周边/嵌板和 pigtail 实例 | 只对应该 IA；不代表所有 CPO 的机械与维护方式 |

## 3. 来源卡片

### SD01 — OIF CMIS Revision 5.4

- 发布主体：Optical Internetworking Forum（OIF）
- 标题/版本：*Common Management Interface Specification (CMIS), Revision 5.4*，`OIF-CMIS-05.4`，2026-05-21
- 官方 URL：<https://www.oiforum.com/wp-content/uploads/OIF-CMIS-05.4.pdf>
- 本地冻结件：`corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
- 精确锚点：
  - PDF p.3 Abstract：CMIS 的 two-wire host-to-module management communication；
  - 印刷页 65 §6：核心描述默认 transmission module，并列出 resource module、cable assembly 等例外；
  - 印刷页 66 §6.1–6.1.2：Host Interface、Media Interface 及四种信号方向；
  - 印刷页 67 §6.2.1.1：Application 是 host-side 与 media-side 之间的传播/处理和 bridge/forwarding function。
- 可支持：
  - 在 CMIS-managed transmission module 条件下，host side 是高速电接口，media side 是高速电或光接口；
  - host→module 是 transmitter input，module→media 是 transmitter output；media→module 是 receiver input，module→host 是 receiver output；
  - 高速 mission-related interface 与低速 two-wire 管理通信属于不同层。
- 不能支持：
  - 所有光模块都受 CMIS 管理；
  - Media Interface 必然是光；
  - 模块内部必须依次存在 DSP、driver、laser、modulator、PD、TIA；
  - 任何机械形态、功耗、reach 或成本结论。
- 适用问题：PQ002 为主；TQ002 的管理/维护分层可辅助使用。

### SD02 — OIF Co-Packaging Framework Document 01.0

- 发布主体：OIF
- 标题/版本：*Co-Packaging Framework Document*，`OIF-Co-Packaging-FD-01.0`，2022-02-03
- 官方 URL：<https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-FD-01.0.pdf>
- 本地冻结件：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
- 精确锚点：
  - 印刷页 9 §5：把 engine 靠近 host ASIC 的目的与 expected power-saving 表述；
  - 印刷页 13 Table 1：不同应用的 energy-efficiency、engine 数量、switch capacity、reliability/lifetime 目标；
  - 印刷页 14 Table 2–3：dense/sparse endpoint、thermal、fiber count、signaling/protocol 示例；
  - 印刷页 15–17 §7.2–7.2.1、Table 4：retimed/linear/direct-drive 等候选接口及 solder/socket 的 footprint、rework 权衡；
  - 印刷页 18 §7.3.1：integrated/external laser 的条件化比较；
  - 印刷页 21–26 §7.3.4、§7.4、§7.5、§7.8：光预算、系统冷却、功耗密度、可靠性和 repairability；
  - 印刷页 28–30 Glossary：EIC、OIC/PIC、Optical Engine、TIA、ROSA 等功能定义。
- 可支持：
  - 在该 CPO framework 的 optical-engine 实例中，EIC 可含 laser/modulator driver，photodetector 的 photocurrent 可经 TIA/post amplifier 转为可用电信号；PIC 可含 modulator、photodetector、waveguide 等；
  - engine 总带宽、布线密度、光纤接口和热管理共同影响 footprint；socket 的 retention mechanism 会占面积；
  - solder reflow 与 socket 在密度、返工和现场 access 上存在明确工程权衡；
  - framework 明确说 co-packaged engine 天生比 front-panel pluggable 更不易现场维护，因此需要 reliability/redundancy/repairability 框架。
- 不能支持：
  - 上述部件是全部光模块的共同 BOM；
  - 所有 CPO 都采用相同 EIC/PIC/laser 布局；
  - expected power savings 等于已测得产品节能；
  - CPO 必然更低成本、更高可靠或不可维护；
  - Table 1 的 pJ/bit 目标等于量产产品实测值。
- 适用问题：PQ002 的实现实例；TQ002 的功耗、密度、维护权衡。

### SD03 — Coherent FTCE4517E1PxM 800G-DR8 OSFP

- 发布主体：Coherent Corp. / Finisar
- 标题/版本：*800G-DR8 OSFP Optical Finisar Transceiver FTCE4517E1PxM Product Specification*，Rev B3，2024-10
- 官方 datasheet：<https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4517e1pxm-transceiver-ds.pdf>
- 官方产品页：<https://www.coherent.com/networking/transceivers/datacom/FTCE4517E1PxM>
- 本地冻结件：
  - `corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf`
  - `corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_product.html`
- 精确锚点：
  - PDF p.1 Product Features / Applications：hot-pluggable OSFP、850 Gb/s aggregate、<17 W、8×100G PAM4 retimed electrical interface、MPO-16、I2C、500 m SMF；
  - PDF p.3–4 §III–IV：electrical transmitter/receiver 与 optical transmitter/receiver 分表；
  - PDF p.5 §V：850 Gb/s aggregate 与 500 m SMF；
  - 产品页参数表：Transmitter=`EML`、Receiver=`PIN`、Operating Distance=`500 m`。
- 可支持：
  - 一只真实模块同时具有 host-side 高速电 TX/RX、optical TX/RX、独立 I2C 管理接口；
  - EML 发射、PIN 接收是该料号的实现；
  - 该产品在规定温度/电压范围的 maximum total power 为 17 W，支持最长 500 m SMF。
- 不能支持：
  - EML/PIN 是所有 800G、DR8 或光模块的必选路线；
  - `<17 W` 是 OSFP 或 800G 的通用值；
  - datasheet 没有披露的完整内部 BOM、器件连接顺序、制造方式或成本。
- 适用问题：PQ002 与 TQ002，均仅作产品实例。

### SD04 — OSFP Module Specification Rev 5.22

- 发布主体：OSFP MSA
- 标题/版本：*OSFP Module Specification Rev 5.22*，文档日期 2025-08-09，官网发布记录 2025-08-14
- 官方 URL：<https://www.osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_22.pdf>
- 官方版本目录：<https://osfpmsa.org/specification.html>
- 本地冻结件：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- 精确锚点：
  - 印刷页 17 §1 Scope：module/cage/connector/electrical/mechanical/thermal 范围以及 CMIS 单列；
  - 印刷页 159–160 §15：host→module TX pairs、module→host RX pairs、低速控制、power/ground；
  - 印刷页 168–170 §15.6、Table 15-7、Table 15-8：power classes、低/高功耗模式、host 读取 power class、系统级 thermal validation 和 hot-plug/hot-unplug 瞬态。
- 可支持：
  - 在 OSFP 实例中，高速 TX/RX、低速控制和供电是不同类别；
  - power class 是 host/module 协调及系统热设计约束；
  - hot-plug/hot-unplug 是规范明确处理的电源瞬态事件。
- 不能支持：
  - OSFP 规范定义模块内部电→光→电器件链；
  - power class 等于某款产品实际功耗；
  - hot-plug 单独证明维修时间、维护成本或可靠性更优。
- 适用问题：PQ002 的接口分层；TQ002 的功耗和维护事件。

### SD05 — IEEE 802.3df-2024 与 IEEE SA 官方解读

- 发布主体：IEEE Standards Association / IEEE 802.3 Working Group
- 标题/版本：*IEEE 802.3df-2024 — Media Access Control Parameters for 800 Gb/s and Physical Layers and Management Parameters for 400 Gb/s and 800 Gb/s Operation*；2024-02-15 批准，2024-03-15 发布，Active Standard
- 标准页：<https://standards.ieee.org/ieee/802.3df/11107/>
- 官方解读：<https://standards.ieee.org/beyond-standards/ethernets-next-bar/>
- Task Force 页面：<https://www.ieee802.org/3/df/index.html>
- 精确锚点：
  - 标准页 Abstract / Scope：400 Gb/s 与 800 Gb/s 的 MAC、PHY 和 management parameters；
  - 官方解读 Table 2：800 Gb/s x8 的 AUI、backplane、copper、MMF 50/100 m、SMF 500 m/2 km；
  - 官方解读 Figure 2 前后：八 lane port 可作 1×8、2×4、4×2、8×1 配置。
- 可支持：
  - “800G”不是完整场景定义，还需 media、reach、lane/configuration；
  - 同一 aggregate rate 可对应不同介质与距离档；
  - lane configuration 提供逻辑端口配置灵活性。
- 不能支持：
  - 官方解读替代标准正文的 PMD 合规条款；
  - x8 必然比 x4 更优；
  - lane 配置直接等于 faceplate ports/RU 物理密度；
  - 任一模块内部路线、实际功耗或成本。
- 适用问题：TQ002。

### SD06 — IEEE P802.3df Objectives（历史项目目标）

- 发布主体：IEEE P802.3df Task Force
- 标题/版本：*IEEE P802.3df Task Force Objectives*，2022-03-17
- 官方 URL：<https://www.ieee802.org/3/df/proj_doc/objectives_P802d3df_220317.pdf>
- 本地冻结件：`corpus/web/2026-08-23/ieee802.org__P802.3df_objectives_2022-03-17.pdf`
- 精确锚点：印刷页 2–4；其中印刷页 3 列出 800 Gb/s 的 AUI、copper、backplane、MMF、SMF 以及不同 lane/reach 目标。
- 可支持：项目定义阶段把 rate、lane count、media 与 reach 当作独立且组合使用的设计输入。
- 不能支持：
  - 历史 objectives 中每一个 10 km/40 km 等目标都已进入最终 802.3df-2024；
  - 一个 PMD 同时完成全部 reach；
  - reach 直接决定功耗、成本或路线胜负。
- 适用问题：TQ002；只作历史设计输入材料，最终状态必须回到 SD05 或标准正文。

### SD07 — IEEE P802.3df Criteria for Standards Development

- 发布主体：IEEE 802.3 Ethernet Working Group
- 标题/版本：P802.3df CSD；官方任务组邮件指向 `ec-21-0306-01-ACSD-p802-3df.pdf`，本地 PDF 内部页眉为修订后的 `ec-22-0197-03-00EC`
- 官方 URL：<https://mentor.ieee.org/802-ec/dcn/21/ec-21-0306-01-ACSD-p802-3df.pdf>
- 本地冻结件：`corpus/web/2026-08-23/mentor.ieee.org__P802.3df_CSD.pdf`
- 精确锚点：印刷页 8，*Economic Feasibility*。
- 可支持：
  - 标准开发中的 cost-for-performance 至少区分 known/balanced cost factors、installation cost 和 operational cost（包括 energy consumption）；
  - 文件明确把保留 network architecture、management、software 与降低 design/installation/maintenance cost 联系起来；
  - 项目比较 PMD complexity、power、latency 与 implementation constraints。
- 不能支持：
  - 任一模块售价、BOM 成本或维护费用；
  - 任何路线成本排名；
  - “复用旧架构”在所有部署中必然最低成本。
- 适用问题：TQ002 的成本与维护维度。

### SD08 — OIF 800ZR Coherent IA 01.0

- 发布主体：OIF
- 标题/版本：*Implementation Agreement for 800ZR Coherent Interfaces*，`OIF-800ZR-01.0`，2024-10-08
- 官方 URL：<https://www.oiforum.com/wp-content/uploads/OIF-800ZR-01.0.pdf>
- 精确锚点：
  - PDF p.2 Abstract：面向 single-span amplified DWDM DCI；
  - 印刷页 9 §1–2：single-wavelength 800G、80–120 km、point-to-point、DWDM noise-limited links；最多 800G aggregate Ethernet clients；不限定 physical form factor；
  - 印刷页 10 §3 Table 1：100G/200G/400G/800G client interfaces。
- 可支持：
  - 800G aggregate bandwidth 可以服务 80–120 km coherent DCI 场景；
  - reach、amplification、DWDM、client mapping 与 interoperability 构成场景约束组合；
  - 相同“800G”标签可落在与 500 m DR8 完全不同的接口规范中。
- 不能支持：
  - 所有 800G 都使用 coherent；
  - 所有 DCI 都是 80–120 km；
  - IA 的 cost-effective/low-power 目标等于任一产品的实测功耗或售价；
  - 特定 module form factor。
- 适用问题：TQ002 为主；PQ002 可作为 coherent signal-processing 路径实例，但不能并入通用骨架。

### SD09 — OIF 3.2T Co-Packaged Module IA 01.0

- 发布主体：OIF
- 标题/版本：*Implementation Agreement for a 3.2Tb/s Co-Packaged (CPO) Module*，`OIF-Co-Packaging-3.2T-Module-01.0`，2023-03-29
- 官方 URL：<https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf>
- 本地冻结件：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- 精确锚点：
  - 印刷页 7 §1：3.2T module 是 51.2T switch assembly 的 building block，optical module 把 short-reach electrical 转为 optical I/O；
  - 印刷页 24 §6：module 可在 substrate 周边或 embedded on board；optical module 为 pigtail，最终 connector 未由 IA 固定；
  - 印刷页 26–29 Figure 14–18：module/socket footprint 与 abutment 规范实例。
- 可支持：一条高 aggregate-bandwidth CPO 实现中，module placement、footprint、socket/attach 和 optical pigtail 共同参与密度与维护边界。
- 不能支持：
  - 所有 CPO 都采用相同 footprint、pigtail 或 connector；
  - 所有高密度系统都必须 CPO；
  - 3.2T/51.2T 数值本身证明功耗、成本或可维护性优于 pluggable。
- 适用问题：TQ002；PQ002 仅作边界反例。

## 4. PQ002 可形成的条件化骨架草案

下面只表示来源能够共同支持的最小功能方向，不是待落库答案：

```text
条件：CMIS-managed transmission module，且 Media Interface 为 optical

近端 Host
  └─ transmitter input（高速电）
       ↓ Host Interface
    [module Application：传播或处理 / bridge]
       ↓ transmitter output
    Optical Media Interface
       ↓ optical fiber / optical carrier
    远端 Optical Media Interface
       ↓ receiver input
    [remote module Application：传播或处理 / bridge]
       ↓ receiver output（高速电）
远端 Host

旁路：two-wire / I2C 管理通信，不是上述高速 mission data path。
```

可在“实现实例”层另加：

- OIF CPO framework：TX 侧可出现 driver + laser/modulator，RX 侧可出现 photodetector + TIA/post amplifier；这是 optical engine 的可选组成描述。
- Coherent FTCE4517E1PxM：该 800G-DR8 OSFP 的 transmitter=EML、receiver=PIN；datasheet 只把 electrical/optical TX/RX 参数并列，不披露完整内部链。
- OIF 800ZR：coherent 路径还有 client mapping、FEC、DSP framing 和 coherent optical interface，不能把这些步骤反向塞入所有 direct-detect 模块。

本轮不能把 `DSP → driver → EML → fiber → PIN → TIA → DSP` 写成通用骨架。该串联最多是待进一步核验的某类产品实现表达，而且不同架构会改变器件、集成层级和顺序。

## 5. TQ002 六类约束证据矩阵

| 约束 | 可直接使用的一手证据 | 当前可写到的粒度 | 不能跨越的边界 |
|---|---|---|---|
| 带宽 | SD05 IEEE 802.3df；SD03 Coherent DR8；SD08 OIF 800ZR；SD09 OIF 3.2T CPO | aggregate rate、lane/client 配置、特定标准或产品的速率 | 不由 aggregate rate 单独推导内部路线、功耗或成本 |
| 距离 | SD05 的 MMF 50/100 m、SMF 500 m/2 km；SD03 的 500 m 产品值；SD08 的 80–120 km amplified DWDM | 不同 media/reach/application code 是不同场景输入 | SD06 的历史 10/40 km objectives 不能冒充最终 802.3df；不能用 reach 单变量决定路线 |
| 功耗 | SD04 OSFP power class/thermal validation；SD03 `<17 W`；SD02 CPO 5–15 pJ/bit 目标与 power-density 示例 | 分开写 form-factor 上限机制、单品最大功耗、framework target | 三种口径不能混成行业平均；不能声称 CPO 实测必然更低功耗 |
| 密度 | SD05 lane configuration；SD02 footprint/retention/thermal/fiber-count；SD09 3.2T footprint/placement 实例 | 区分逻辑端口配置、封装 footprint、带宽集成与散热/光纤接口约束 | lane 数不等于 ports/RU；3.2T 不自动证明系统级最高密度 |
| 成本 | SD07 IEEE CSD；SD02 的工程 tradeoff | 只列元件/系统、安装、运营能耗、维护连续性和实现复杂度等成本维度 | 没有官方产品价格、BOM 或全生命周期成本数据，不能排序 EML/SiPh/CPO/pluggable |
| 维护 | SD04 hot-plug 电源事件；SD03 hot-pluggable 与 I2C diagnostics；SD02 socket/reflow、field access、repairability；SD07 管理/软件连续性 | 区分可插拔事件、可观测性、返工能力、现场 access、可靠性/冗余 | hot-plug 不等于低维护成本；socketable 不等于现场一定可修；不能无数据比较 MTTR/TCO |

## 6. 来源间必须保留的差异

1. **规范正文、官方解读、历史目标不是同一证据等级。** SD05 的 active-standard 页面确认最终状态；IEEE SA 文章是官方但非规范性摘要；SD06 只是 2022 年项目目标。
2. **共同骨架与实现实例不能合并。** SD01 给接口和方向骨架；SD02、SD03、SD08、SD09 分别描述 CPO optical engine、DR8 direct-detect 产品、800ZR coherent 接口和 3.2T CPO 机械实例。
3. **功耗有三种不同口径。** OSFP power class 是 form-factor 约束，`<17 W` 是单品最大规格，pJ/bit 是 framework 目标/估计；不得比较成同一统计量。
4. **距离必须带介质与应用。** 500 m DR8 SMF、2 km IEEE SMF PMD、80–120 km amplified DWDM 不是只改一个数字的同类产品。
5. **密度至少有三种含义。** lane/port 的逻辑配置、module/engine footprint 的物理密度、单位机架或系统总带宽密度需要分别取证。
6. **维护至少有四种含义。** hot-plug、管理可观测性、assembly rework、field serviceability 不得互相替代。

## 7. 证据空白与风险

- **成本最大空白**：当前官方资料没有可横向比较的 EML、SiPh、coherent、pluggable、CPO 产品 BOM、采购价、安装成本或 TCO；本轮只能建立成本科目，不能形成路线成本结论。
- **维护缺少量化指标**：没有同口径 MTTR、故障率、备件策略、现场更换时间和维护人力数据；OIF framework 的 repairability 只能作为工程约束。
- **最终 IEEE 正文仍需冻结**：SD05 的官方解读足以做来源发现，但正式回答具体 PMD 时应冻结 IEEE 802.3df-2024 GET Program 正文并引用 Clause/Table，而不是只引官方文章。
- **历史目标污染风险**：SD06 包含后来可能调整或转移到其他项目的目标；任何使用都必须显式标注 `historical_project_objective`。
- **framework 语言风险**：SD02 中 `expected`、`target`、`possible`、`may` 不能改写为已实现、必然或行业平均。
- **单品外推风险**：SD03 的 EML/PIN、500 m、17 W 只对应 FTCE4517E1PxM；不能代表 800G 类别。
- **路线归群尚无证据**：本轮没有研究公司群、市场份额或“哪些公司服务哪条线路”，不得从这些规范来源建立公司—路线映射。

## 8. 停止声明

- 本轮只做一手来源发现。
- 未生成任何新问题 ID。
- 未提出 YAML/CSV/canonical 落库或 promotion。
- 本文件不改变 PQ002、TQ002 的覆盖状态。
- 除本文件外，本轮不应产生或修改任何项目文件；`archive/` 不在读取范围内。
