# TQ004 一手来源发现：技术路线的正交选择轴

日期：2026-08-24
模式：`draft-only / source-discovery / no-canonical-write`

## 1. 研究边界

目标是为现有问题 `TQ004 比较路线时必须分开哪些正交选择轴？` 找到可交给后续 Pi 研究的一手来源。
本文件不回答路线胜负，不做公司归群，不生成新 QID，不改变 TQ004 或任何子问题的状态。

研究前已读取：

- `docs/research/pi-packages/2026-08-23-expansion-v1/post-review-effective-text.md`；
- `research_questions.yaml` 中 `TQ004`–`TQ010`；
- 本轮 `contract-tq004.md`。

这里的“正交”只表示：比较路线时必须分别记录，不能用一个词替代另一个维度。它不表示各轴在工程上
完全独立，也不表示所有轴值都能任意组合或已经量产。

## 2. 结论摘要

四个候选方向大体成立，但需要两处分类修正：

1. `产品/链路标准`、`电信号处理架构`、`光子实现`、`封装/放置架构`应分别记录；一手来源中已出现
   多组跨轴组合，足以否定把 EML、SiPh、LPO、CPO 放进一张平面“路线优劣表”的做法。
2. `EML/SiPh` 不是严格同层级：EML 是激光器与调制器的器件/发射实现，SiPh 是光子集成平台。
   TQ007 最好在一个“光子实现”大轴下继续分成“材料/集成平台”“光源与调制器件”“接收器件”等
   子字段，而不是把 EML、SiPh、VCSEL 当作互斥且完备的同级枚举。
3. `LPO` 也不是纯电接口轴值：它把 `linear` 电架构和 `pluggable` 放置形态组合在一个名字里。
   纯电架构更适合写成 `retimed / linear / transmit-retimed-linear-receive / half-retimed / direct-drive`
   等；纯封装轴再写 `pluggable / on-board or NPO / CPO`。
4. `pluggable / NPO / CPO` 可作为放置与封装层级的分析轴，但 `OSFP / QSFP-DD` 是
   pluggable 下更细的机械 form factor，不能与 CPO 直接作同粒度比较。NPO 的边界应注明采用哪份
   OIF 文件的定义，不能假设全行业只有一个机械实现。

## 3. 建议的轴字典

| 分析轴 | 它回答的问题 | 可观察字段 | 不能单独回答什么 | 主要对应问题 |
|---|---|---|---|---|
| 链路/接口画像 | 要互通的是什么链路？ | 协议、总速率、host/media lane 数与 lane rate、调制格式、FEC/PMD、介质、reach、波长/并行或 WDM 组织 | 模块内部用 EML 还是 SiPh、DSP 放在哪里、光学离 ASIC 多远 | TQ005 |
| 电信号处理架构 | retiming、FEC、均衡、数模/模数处理分别放在哪里？ | retimed、linear、Tx-retimed/Rx-linear、half-retimed、direct-drive；host 与 module/engine 的处理职责 | 光器件材料平台、机械 form factor、链路 reach | TQ006 |
| 光子实现（建议嵌套子字段） | 怎样产生、调制、传输和探测光？ | 平台（如 SiPh、InP）；光源位置；调制器/发射器件（如 MZM、EML、VCSEL）；接收器件（如 PIN）；集成方式 | ASIC 与光学的物理距离、电路是否 retimed、标准 reach | TQ007 |
| 封装/放置架构 | 光学相对 ASIC 在哪里，怎样连接和更换？ | front-panel pluggable、on-board/NPO、same-first-level-substrate CPO；其下再记 OSFP/QSFP-DD、socket/solder、pigtail/connector | 链路标准、光子平台、是否 linear/retimed | TQ008 |

`TQ009` 的具体路线画像应是上述字段的组合，而不是取一个热点术语当整条路线。`TQ010` 再比较组合变化
带来的组件、接口、工序和设备变化。

## 4. 来源账本

### S1. IEEE 802.3df-2024 与 IEEE SA 官方解读

- 来源类型：正式标准范围页 + IEEE SA 官方工作组解读。
- 证据等级：**规范事实**；解读页中的配置说明属于 **IEEE 官方说明**。
- 链接：
  - [IEEE 802.3df-2024 标准页](https://standards.ieee.org/ieee/802.3df/11107/)
  - [Ethernet’s Next Bar is Now – 800 Gb/s](https://standards.ieee.org/beyond-standards/ethernets-next-bar/)
- 已冻结快照：
  - `corpus/web/2026-08-23/standards.ieee.org__802.3df-2024.html`
  - `corpus/web/2026-08-23/standards.ieee.org__ethernet_800g_article.html`
- 能支持：800 Gb/s 不是一个完整内部技术路线。IEEE 分别规定 MAC/PHY/management，并把 AUI、
  backplane、copper、MMF 50/100 m、SMF 500 m/2 km 作为不同接口/PMD 边界；八 lane port 还可
  形成不同拆分配置。由此可把速率、lane、介质和 reach 视为链路画像字段。
- 不能支持：EML/SiPh、DSP/LPO、pluggable/CPO 的选择；也不能证明某个链路标准只有一种产品实现。

### S2. OIF CMIS 5.4

- 来源类型：OIF Implementation Agreement，`OIF-CMIS-05.4`。
- 证据等级：**规范事实**。
- 链接：[OIF CMIS 5.4](https://www.oiforum.com/wp-content/uploads/OIF-CMIS-05.4.pdf)
- 已冻结快照：`corpus/web/2026-08-23/oiforum.com__OIF-CMIS-05.4.pdf`
- 关键位置：印刷页 66 §6.1；印刷页 67–71 §6.2.1。
- 能支持：CMIS 把 Host Interface 与 Media Interface 分开；一个 Application 通常由一对 host/media
  industry standards 描述，字段包括 signaling rate、modulation、lane count 及适用的数字处理。
  同一个 HostInterfaceID 或 MediaInterfaceID 可出现在多个 Application Descriptor 中。这直接支持
  “接口组合不是模块内部实现的唯一标识”。
- 不能支持：模块内部必须采用何种 DSP、激光器、PIC 或封装；CMIS 也不提供“正交轴”这一研究术语。

### S3. OIF Co-Packaging Framework 01.0

- 来源类型：OIF 官方 Framework Document；不是最终产品规范。
- 证据等级：文中定义和列举为 **行业抽象/官方 framework**，不是普遍产品事实。
- 链接：[OIF Co-Packaging Framework](https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-FD-01.0.pdf)
- 已冻结快照：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
- 关键位置：印刷页 9–10 §5、Figure 1/2；印刷页 14–17 §7.2、Figure 5–8。
- 能支持：
  - CPO 的定义边界是 optical/electrical engine 与 host ASIC 位于同一 first-level substrate；
  - 文中把 socketed、靠近封装的安排称作 NPO 的一个实例；
  - 在同一 co-packaging framework 内又分别讨论 re-timed、linear amplified、half-retimed、direct
    drive 电接口。因此“电处理架构”与“封装/放置架构”必须分开。
- 不能支持：所有 CPO/NPO 产品都采用图中的机械实现；也不能把 framework 中的候选界面写成已量产
  或已形成统一标准。

### S4. OIF Energy Efficient Interfaces / Current Work

- 来源类型：OIF 官方在研项目页。
- 证据等级：**官方工作范围披露**，不是完成的 IA。
- 链接：
  - [OIF Current Work](https://www.oiforum.com/technical-work/current-work/)
  - [OIF Energy Efficient Interfaces](https://www.oiforum.com/technical-work/hot-topics/energy-efficient-interfaces/)
- 能支持：OIF 明确把 co-packaged、near-packaged、pluggable 与 retimed、transmit-retimed、linear
  交叉列出；CEI-224G-Linear 项目还明确称 full-linear electrical specifications 面向 LPO、CPO、NPO。
  这是目前最直接的“电架构轴 × 封装轴”可交叉证据。
- 不能支持：所有交叉组合已经完成规范、通过互操作或具备量产经济性；在研项目目标不能当正式 IA。

### S5. LPO MSA 100G-DR-LPO Specification Rev. 1.0 与 FAQ

- 来源类型：LPO MSA 正式公开规范 + 官方 FAQ。
- 证据等级：规范要求为 **MSA 规范事实**；低功耗/低成本等价值表述为 **MSA 目标**。
- 链接：
  - [100G-DR-LPO Specification Rev. 1.0](https://www.lpo-msa.org/files/live/sites/lpomsa/files/specs/LPO_MSA_Specification_v1p2_final.pdf)
  - [LPO MSA FAQ](https://www.lpo-msa.org/home/faqs.html)
- 本轮状态：仅发现 live URL；受“只新增一个文件”限制，未另建网页/PDF 快照。
- 关键位置：规范印刷页 7–10 §1、§4、§5；FAQ “What is LPO?”。
- 能支持：
  - LPO 模块不含 DSP，host 承担 FEC、retiming、DAC/ADC 等功能，host-module path 是 linear；
  - 规范明确 form-factor agnostic，并列 QSFP、QSFP-DD、OSFP；
  - 规范明确允许多种 opto-electronic implementation approaches and technologies。
  因而 LPO 的电架构不能用于替代封装 form factor 或光子实现字段。
- 不能支持：任一 LPO 产品实际采用 EML、SiPh 或其他特定光器件；也不能由 MSA 目标直接认定 LPO
  在所有场景都比 retimed 方案低成本、低功耗或更可靠。

### S6. QSFP-DD MSA Hardware Specification Rev. 7.1

- 来源类型：form-factor MSA hardware specification。
- 证据等级：**MSA 规范事实**。
- 链接：
  - [QSFP-DD Specification 目录](https://www.qsfp-dd.com/specification/)
  - [QSFP-DD Hardware Rev. 7.1 PDF](https://www.qsfp-dd.com/wp-content/uploads/2024/07/QSFP-DD-Hardware-Rev7.1.pdf)
- 本轮状态：官方 live URL 可定位；受单文件约束未生成快照。
- 能支持：QSFP-DD 定义八路 pluggable connector/cage、电连接、供电、机械与热边界；MSA 官方说明
  optical/copper physical-layer specifications 在 form-factor MSA 之外定义。由此可把 QSFP-DD/OSFP
  与 DR/FR/SR 等链路标准分层。
- 不能支持：某个 QSFP-DD 模块一定是 EML、SiPh、retimed 或 linear；form factor 也不等于 reach。

### S7. Coherent：800G-DR8+ SiPh 与 EML 互操作演示

- 来源类型：公司官方技术演示公告。
- 证据等级：**官方披露**；是演示事实，不是标准定义或市场份额证据。
- 链接：[Coherent ECOC 2022 demonstrations](https://www.coherent.com/news/press-releases/coherent-thought-leaders-to-present-at-ecoc-2022)
- 本轮状态：live URL，未生成快照。
- 能支持：Coherent 披露同一 `800G-DR8+` 链路中，一端是基于 silicon-photonics MZM PIC 的
  QSFP-DD800，另一端是基于 1310 nm EML/photodetector 的 OSFP。它直接证明同一链路族可以跨
  不同光子实现和 pluggable form factor 互通。
- 不能支持：EML 与 SiPh 是严格同层级术语；不能证明任意 EML 与任意 SiPh 产品均互通，也不能证明
  两者市场地位或成本高低。

### S8. Coherent：同一 1.6T-DR8 OSFP/SiPh 下的不同电架构演示

- 来源类型：公司官方技术演示公告。
- 证据等级：**官方披露**；prototype/demo，不是量产或标准事实。
- 链接：[Coherent OFC 2025 demonstrations](https://www.coherent.com/news/press-releases/coherent-to-showcase-innovative-products-and-technologies-at-ofc2025)
- 本轮状态：live URL，未生成快照。
- 能支持：三款演示模块共享 `1.6T-DR8`、OSFP、8×200G 光/电接口和 SiPh 架构，其中一款是
  LRO（只在 Tx 做 DSP retiming），另一款采用 3 nm DSP。它是“链路/形态/光子实现相同，而电处理
  架构不同”的公司级实例。
- 不能支持：这三种实现已同等量产，或 LRO/DSP 的性能、成本、可靠性排序。

### S9. Intel Silicon Photonics 官方产品页

- 来源类型：公司官方技术/产品资料。
- 证据等级：**官方披露**。
- 链接：
  - [Intel Silicon Photonics](https://www.intel.com/content/www/us/en/products/details/network-io/silicon-photonics.html)
  - [Intel Silicon Photonics Pluggable Transceivers](https://www.intel.com/content/www/us/en/ark/products/series/96621/intel-silicon-photonics-pluggable-optical-transceivers.html)
- 本轮状态：live URL，未生成快照。
- 能支持：Intel 同一 SiPh platform 已用于 pluggable transceiver，并把 OCI chiplet 描述为可与
  CPU/GPU/IPU/SoC co-package，也可 standalone on-board。SiPh 因此不能等同于 pluggable 或 CPO；
  它可跨放置/封装形态。
- 不能支持：所有 SiPh 技术都能无修改跨三种封装，或 Intel 的某款 pluggable 与 OCI chiplet 使用
  完全相同的 die、光源、接口和制造流程。

### S10. Coherent 400G DR4 QSFP-DD EML 产品页

- 来源类型：公司单产品官方资料。
- 证据等级：**官方披露**。
- 链接：[Coherent FTCD4533E3PCM](https://www.coherent.com/networking/transceivers/datacom/FTCD4533E3PCM)
- 本轮状态：live URL，未生成快照。
- 能支持：单一产品同时具有 400G、DR4/QSFP-DD、EML transmitter、PIN receiver、SMF、MPO12、
  reach 等字段，说明一个可比较产品画像天然是多字段组合。
- 不能支持：代表全部 400G DR4，或由这一个产品推出 EML 与 SiPh 的普遍优劣。

## 5. 已被一手来源直接观察到的跨轴组合

| 保持不变或共享的字段 | 发生变化的字段 | 来源 | 可以得到的最小结论 |
|---|---|---|---|
| OIF co-packaging 场景 | re-timed / linear amplified / half-retimed / direct-drive | S3 | 封装位置不能替代电处理架构字段 |
| full-linear electrical interface | LPO / CPO / NPO | S4 | linear 不等于 pluggable；电架构与放置形态可交叉 |
| LPO 的 linear 系统 | QSFP / QSFP-DD / OSFP；多种 opto-electronic implementation | S5 | LPO 规范本身不固定机械 form factor，也不固定光子实现 |
| 800G-DR8+ link family | SiPh MZM + QSFP-DD800 / EML + OSFP | S7 | 同一链路族可出现不同光子实现和 form factor |
| 1.6T-DR8 + OSFP + SiPh + 8×200G | LRO / module DSP retimed | S8 | 在链路、形态、光子平台相同条件下，电处理架构仍可不同 |
| Intel SiPh platform | pluggable / on-board / co-packaged OCI | S9 | 光子平台与封装/放置形态不是同一轴 |

这些实例只证明“至少存在这些组合或官方目标”。它们不能扩张成完整笛卡尔积，也不能证明未观察到的
组合不可行。

## 6. 不能直接横向比较的术语

| 错误比较 | 原因 | 应怎样改写 |
|---|---|---|
| `800G DR8 vs EML` | 前者是链路/PMD 画像，后者是发射器件实现 | 先固定 800G DR8，再比较其光子实现 |
| `DSP vs LPO` | DSP 是处理功能/芯片；LPO 是 linear + pluggable 的复合标签 | 比较 retimed 与 linear 的处理职责，再单列封装 |
| `LPO vs CPO` | LPO 同时含电架构与 pluggable；CPO 主要是放置/封装 | 比较 linear/retimed 与 pluggable/NPO/CPO 的组合 |
| `EML vs SiPh` | EML 是器件/调制实现；SiPh 是材料与 PIC 平台 | 将 TQ007 拆成平台、光源、调制器、接收器等子字段 |
| `OSFP vs CPO` | OSFP 是 front-panel pluggable 的具体 form factor；CPO 是系统级放置架构 | 先比 pluggable/NPO/CPO，再在 pluggable 下比 OSFP/QSFP-DD |
| `DR8 vs OSFP` | DR8 描述 optical PMD/lane 组织；OSFP 描述机械、电、热 form factor | 作为一个路线画像中的两个字段记录 |
| `SiPh vs CPO` | 一个是光子平台，一个是封装位置 | 记录为 `platform=SiPh, packaging=CPO` 这样的组合 |

## 7. 事实、抽象与推论边界

- **事实/规范定义**：IEEE、CMIS、LPO MSA、QSFP-DD MSA 文本明确规定的接口、字段、职责和机械边界。
- **官方披露**：Coherent、Intel 对具体产品或演示的说明；只对披露对象成立。
- **行业抽象**：OIF Framework/Current Work 中对 CPO/NPO 和电接口候选的组织方式；适合建立研究词典，
  但不自动等于已完成规范。
- **本轮推论**：把这些来源整理成四类分析轴，并指出复合标签和错层术语。没有任何一个标准正式声明
  “行业共有四条正交轴”；这是为 TQ004 建立的分析模型，必须保持该标签。

## 8. 后续研究缺口（只挂现有问题）

- `TQ005`：把 link profile 的最小字段集正式冻结；尤其区分 Ethernet PMD、MSA 扩展名和公司自定义
  `+` 后缀，避免把 marketing name 当标准名。
- `TQ006`：为 retimed、linear、LRO/RTLR、half-retimed、direct-drive 建立统一的处理职责表；确认
  各术语在 OIF、LPO MSA 与公司材料中的边界是否一致。
- `TQ007`：把“光子平台”改成嵌套模型，至少区分 platform/material、laser source、modulator、
  detector、integration；特别处理 EML 与 SiPh 不同层级的问题。
- `TQ008`：冻结 pluggable、on-board、NPO、CPO 的操作性定义与位置参照点；NPO 必须注明定义来源。
- `TQ009`：路线画像需要显式保存各轴值及来源，复合词只能作为 alias，不能替代字段。
- `WQ002/WQ003`：轴之间存在工程耦合，但“为什么某约束提高某组合的价值”必须另找双侧证据，不能由
  本文件的分类关系直接推出。

## 9. 拒绝的推论

- 不接受“EML、SiPh、LPO、CPO 是四条互斥路线”。
- 不接受“正交”意味着所有组合都可制造、可互操作或经济可行。
- 不接受由 OIF 在研项目推出产品已经满足正式 IA。
- 不接受由公司演示推出行业主流、份额、成本或性能排名。
- 不接受由 pluggable、NPO、CPO 的位置关系直接推出维护成本或可靠性高低。
- 不接受由某个链路标准直接推出光子平台、电接口架构或受益公司。

## 10. 停止结论

一手来源发现已足以让后续 Pi 对 TQ004 建立 draft-only 轴字典，并且已经满足至少两组跨轴实例的
来源条件。当前最重要的质量控制不是继续增加“路线名字”，而是把复合标签拆回字段，尤其是：

`LPO = linear electrical architecture + pluggable placement`（仍需记录具体规范版本），以及
`EML ≠ SiPh 的严格同级概念`。

本文件未写 canonical、未改变覆盖状态、未生成新问题 ID。
