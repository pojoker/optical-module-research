# TQ005–TQ008 post-adjudication 唯一有效口径

本文件是本包唯一 controlling text。Pi raw 只作审计，冲突句见 `raw-output.errata.md`。

## 1. 总结判断

这一轮证明：现有提问方式能够继续引出技术路线差异。它先长出四类可比较字段，再长出字段内部的定义、证据缺口和术语边界；当前仍不把这些字段组合成 TQ009 Route Profile。

四轴的最小答案是：

1. TQ005：外部要互通什么；
2. TQ006：电信号处理职责放在哪里；
3. TQ007：光怎样产生、调制、探测及集成；
4. TQ008：光学相对 ASIC、基板和前面板放在哪里。

## 2. TQ005：产品/链路标准轴

### 操作性定义

TQ005 记录 host/media 两侧的外部互操作边界。当前最小字段集为：

| 字段 | 当前含义 | 已冻结例证 |
|---|---|---|
| aggregate rate | 链路聚合速率 | IEEE 400/800 Gb/s 摘要；Coherent 800G 产品实例（S1、S4） |
| host/media lane count + lane rate | host 电 lane 与 media lane 的条数和每 lane 速率 | IEEE 800G parallel ×8；100G-DR-LPO 的 1/2/4/8×100G（S1、S3） |
| modulation | 每 lane 调制格式/符号率 | 100G-DR-LPO 的 53.125 GBd PAM4（S3） |
| FEC / PMD | 纠错与物理介质相关边界 | IEEE PHY/PMD；100G-DR-LPO 的 RS(544,514)（S1、S3） |
| media + reach | 铜/光纤、MMF/SMF 与距离 | 100G-DR-LPO 0.5–500 m SMF；FTCE 产品 500 m SMF（S3、S4） |
| wavelength / parallel-vs-WDM | 波长、光纤与 lane 的组织方式 | CMIS wavelength/fiber mapping；100G-DR-LPO parallel 1310 nm 实例（S2、S3） |

正式 IEEE 标准名、具名 MSA profile、公司产品/演示后缀必须分栏。`100G-DR-LPO` 是 reference profile，`DR+` 是公司产品后缀；二者都不能自动升格为 IEEE PMD 名。

该轴不能推出：DSP/linear、EML/SiPh、OSFP/CPO。

### 下一层开放问题（无新 QID）

- parent_question_id: TQ005
  - question: 怎样用正式标准和产品实例补齐 parallel 与 WDM 两类 wavelength organization？
  - why_open: 当前只有 CMIS 映射字段和 parallel DR 类实例，尚无完整 WDM profile 实例。
  - needed_evidence: 同时给出 lane/波长组织与标准或产品名的一手资料。
- parent_question_id: TQ005
  - question: 800G 的 8×100G 与 4×200G 产品实例分别在哪里？
  - why_open: 已冻结来源证明 8×100G 和 8×200G 演示，但没有完整的 800G 4×200G 产品字段。
  - needed_evidence: 明确披露 media lane 数和 lane rate 的标准或产品页。
- parent_question_id: TQ005
  - question: 400G、1.6T 是否能按同一最小字段集完整填写？
  - why_open: 当前 1.6T 只有部分演示字段，400G 没有独立完整实例。
  - needed_evidence: 正式标准摘要或完整产品参数页。
- parent_question_id: TQ005
  - question: DR、FR、LR、厂商 `+` 后缀和 MSA 后缀怎样建立稳定命名分层？
  - why_open: 当前只有 `100G-DR-LPO` 与 `DR+` 两类反例，不足以归纳稳定命名规则。
  - needed_evidence: 同时出现正式 PMD、MSA profile 与产品后缀的多组一手材料。
- parent_question_id: TQ005
  - question: 500 m 之外的 2 km、10 km 等 reach 如何与 media、FEC、wavelength 联合记录？
  - why_open: 当前冻结的完整 link-field 实例集中在 500 m SMF。
  - needed_evidence: 明确 PMD 名与完整 link fields 的正式标准或产品页。

## 3. TQ006：电接口架构轴

### 操作性定义

TQ006 用 host、module/engine 和 optical path 三个参照点记录职责。当前可证实的最小字典为：

| 值 | 当前可接受定义 | 证据边界 |
|---|---|---|
| retimed | module/engine 侧存在 Tx/Rx retiming 的架构类；具体 DSP/FEC 职责按来源实例记录 | LPO FAQ 对照定义 + OIF framework；不是所有产品的统一实现（S5、S6） |
| linear | module/engine 不承担数字 retiming/CDR 或只保留线性模拟功能的架构类 | 100G-DR-LPO 的 host FEC/retiming/DAC/ADC 只对该 profile 成立（S3、S5、S6） |
| Tx-retimed / Rx-linear | Tx 侧 retimed、Rx 侧利用 host SerDes 的 linear receiver | OIF RTLR 在研定义；Coherent LRO 演示为已观察实例（S7、S8、S9） |
| half-retimed | 一方向 retimed、另一方向 linear 的 framework 类 | OIF Figure 7；与 LRO/RTLR 的命名 scope 尚未正式对齐（S6） |
| direct-drive candidate | host ASIC 直接驱动 modulator/laser，Rx equalization 也主要在 host；engine 极简 | 仅 OIF framework candidate，future IA 尚需测试点和方法（S6） |

S9 只证明同一 1.6T-DR8/OSFP/SiPh/8×200G 演示组内同时存在 LRO 与包含 3 nm DSP 的变体；它没有披露后一变体 Rx 是否 retimed，因此不得称作已证实的 full-retimed 对照。

LPO 继续只作 `linear + pluggable` 复合 alias；具名 100G-DR-LPO profile 只作 reference object。

### 下一层开放问题（无新 QID）

- parent_question_id: TQ006
  - question: LRO、RTLR、half-retimed 在 OIF、LPO MSA 和公司材料中是否完全同义？
  - why_open: 三个词都接近 Tx-retimed/Rx-linear，但来源没有给出统一 scope 对照。
  - needed_evidence: 同时定义至少两个词并给出 Tx/Rx scope 的正式文件。
- parent_question_id: TQ006
  - question: 3 nm DSP 演示的 Rx 是否 retimed，FEC 和 host SerDes 职责分别在哪里？
  - why_open: 公司摘要只披露包含 3 nm DSP，没有说明 Rx 与 FEC 职责。
  - needed_evidence: 完整演示白皮书或产品 block diagram。
- parent_question_id: TQ006
  - question: 除 100G-DR-LPO profile 外，哪些已观察 pluggable 产品明确披露 full-linear 职责？
  - why_open: 当前 generic linear 字典主要依赖一个具名 MSA profile，产品实例不足。
  - needed_evidence: 产品/演示页同时披露 linear path 和 pluggable form factor。
- parent_question_id: TQ006
  - question: direct-drive 从 framework candidate 走向可互操作 IA 还缺哪些 test points、methods 和 criteria？
  - why_open: OIF framework 明确这些内容留待 future IA，但未给出完成状态。
  - needed_evidence: OIF 后续项目或 IA 文件。
- parent_question_id: TQ006
  - question: generic linear 中哪些职责一定在 host，哪些只属于特定 profile？
  - why_open: 100G-DR-LPO 的 host FEC/retiming/DAC/ADC 不能自动推广到全部 linear 实现。
  - needed_evidence: 两个以上 linear 规范/profile 的逐项职责对照。

## 4. TQ007：光子平台/实现轴

### 五个嵌套字段

| 字段 | 当前示例值 | 粒度与证据边界 |
|---|---|---|
| platform/material | silicon photonics、InP | SiPh 是平台；InP 当前由 EML 器件定义支持。GaAs 尚未进入已证实字典（S10、S11、S12） |
| light source | external、integrated、on-chip；DFB、on-chip laser 等实例 | 分类来自 OIF framework，具体 Intel/EML 实现只对公司披露成立（S6、S10、S11） |
| modulator/emitter | EML 的 EAM、MZM、VCSEL | EML 是 DFB+EAM 器件组合；MZM 是 modulator；VCSEL 是 emitter（S9、S11、S12） |
| detector | PIN、generic photodetector | PIN 有 Coherent 产品实例；其他 detector 类型尚未展开（S4、S6、S12） |
| integration | monolithic、on-chip、hybrid laser-on-wafer/direct coupling、PIC+CMOS EIC die stack | 只记录器件/PIC/EIC/光源之间的集成；pluggable/on-board/CPO 不属于本字段（S6、S10、S11） |

两家官方来源都把 EML 描述为 InP DFB laser + EAM（S11、S12）。在强制六标签内，这两条属于
`company_platform_statement`，并明确加注 `official_device_definition subtype`；它们不是一般的平台能力声明。
这足以支持当前器件定义，但不能证明所有 EML 的结构、集成和性能完全一致。

禁止制作 EML/SiPh/VCSEL 同级互斥表；禁止从 Intel 平台能力外推所有 SiPh。

### 下一层开放问题（无新 QID）

- parent_question_id: TQ007
  - question: 不同厂商 EML 在器件结构、光源/调制器集成关系和可观察接口边界上还需要哪些子字段？
  - why_open: 两家来源支持 DFB+EAM 核心定义，但没有形成跨厂结构与 integration 字段表。
  - needed_evidence: 两家以上器件厂商的技术页、datasheet 或工艺说明。
- parent_question_id: TQ007
  - question: GaAs 应在哪些一手来源支持后进入 platform/material 字典，它与 VCSEL 的关系怎样记录？
  - why_open: 当前只有 VCSEL emitter 实例，没有冻结 material/platform 的官方定义。
  - needed_evidence: VCSEL 厂商对 material/platform 的官方定义。
- parent_question_id: TQ007
  - question: external、integrated、on-chip 与 Intel 的 hybrid laser-on-wafer/direct coupling 如何逐项对齐？
  - why_open: OIF 给出分类词，Intel 给出实现词，但两套词汇尚未逐项映射。
  - needed_evidence: 同时使用 OIF 分类与公司实现术语的官方材料。
- parent_question_id: TQ007
  - question: SiPh MZM PIC 中 driver、TIA 与 detector 分别位于 PIC、EIC 还是其他位置？
  - why_open: 当前演示只披露 MZM PIC/photodetector，没有完整电光 block diagram。
  - needed_evidence: 产品 block diagram 或封装技术说明。
- parent_question_id: TQ007
  - question: 除 PIN 外，APD 等 detector 是否出现在同类 datacom 产品实例中？
  - why_open: detector 字典当前只有 PIN 一个明确产品值。
  - needed_evidence: 明确标出 detector 类型的厂商 datasheet。

## 5. TQ008：封装/放置架构轴

### 操作性定义

| 类别 | 当前判据 | 证据边界 |
|---|---|---|
| front-panel pluggable | transceiver 插入系统 front panel；OSFP/QSFP-DD 等为其子层 form factor | OIF glossary + OSFP MSA；不决定内部 PMD/光子/电职责（S6、S13） |
| other on-board | 已知不是 front-panel pluggable，且来源尚未证明符合 OIF NPO/CPO 定义的板上实现 | Intel 仅披露 stand-alone on-board 能力，精确基板关系待查（S10） |
| near-package NPO | OIF Figure 2d：packaged ASIC 与 engine 通过 socket 接到 common substrate，便于装配/返工 | 这是本轮采用的 OIF 定义实例，不声称行业只有一种 NPO（S6） |
| CPO | optical/electrical communications device 与 host ASIC 位于同一 first-level substrate | OIF framework 定义（S6） |

“离 ASIC 多远”当前只作定性位置分类。OIF 的约 50 mm 是特定 first-level substrate 接口讨论，不是跨封装统一阈值。

### 下一层开放问题（无新 QID）

- parent_question_id: TQ008
  - question: OIF Figure 2d 的 NPO 与其他 on-board arrangements 有哪些可操作判据？
  - why_open: 当前只有 Figure 2d 的 socketed/common-substrate 定义实例，缺少跨实现判据。
  - needed_evidence: socket、common substrate、走线和可返工边界的正式定义。
- parent_question_id: TQ008
  - question: Intel stand-alone on-board OCI 的 host ASIC 距离、substrate 和 connector 关系是什么？
  - why_open: Intel 只披露可支持 on-board，没有给出布局与 substrate 细节。
  - needed_evidence: 布局图、白皮书或产品封装说明。
- parent_question_id: TQ008
  - question: Intel 自述 co-packaged OCI 演示是否逐项满足 OIF same-first-level-substrate 定义？
  - why_open: 公司自述演示缺少能与 OIF 定义逐项核对的封装剖面。
  - needed_evidence: 演示封装剖面、substrate 说明或官方技术论文。
- parent_question_id: TQ008
  - question: OSFP、QSFP-DD 等 form factor 如何在 pluggable 子层统一记录机械、热、电和连接器字段？
  - why_open: 当前只冻结 OSFP 正式 MSA，QSFP-DD 仅以产品/规范引用出现。
  - needed_evidence: 两份以上 form-factor MSA 的字段对照。
- parent_question_id: TQ008
  - question: 是否存在第二份独立一手来源支持同一光子平台可跨 pluggable、on-board、CPO 三种位置？
  - why_open: 当前跨位置能力主要依赖 Intel 单一公司平台披露，需要证据多样性而非公司归群。
  - needed_evidence: 独立公司官方平台页或多个已观察产品实例；不得生成公司对照表。

## 6. cross_axis_guardrails

- TQ005 只记录外部互操作字段；TQ006 只记录电处理职责；TQ007 只记录光子器件与集成；TQ008 只记录放置位置。
- 具名 MSA profile 只作 reference object，不在 TQ005/TQ006 各生成一个轴值。
- EML、SiPh、VCSEL、PIN 分属不同粒度；LPO 必须拆成 linear + pluggable。
- OSFP/QSFP-DD 只在 pluggable 子层；other on-board、NPO、CPO 不合并。
- 规范允许、framework 候选、公司平台能力、已观察产品/演示不得互相替代。
- 本轮不生成 TQ009 组合，不由缺失字段推断补全。

## 7. effective draft claim 索引

Pi raw 保留 24 个唯一 draft_id：`tq005-001`–`tq005-006`、`tq006-001`–`tq006-006`、
`tq007-001`–`tq007-006`、`tq008-001`–`tq008-006`。这些 ID 只作审计索引，主张内容必须经
`raw-output.errata.md` 过滤并以本 controlling text 为准；全部 `would_mark_covered: false`。

## 8. 已观察到的差异

当前可以保留的实例级观察：

- Coherent 同一 1.6T-DR8/OSFP/SiPh/8×200G 演示组中有 LRO 和 DSP-based 变体，但后一变体完整 Rx 职责未披露（S9）；
- 800G-DR8+ 族中，SiPh MZM PIC + QSFP-DD800 与 EML/PD + OSFP 互操作（S12）；
- FTCE4517E1PxM 是 800G-DR+、OSFP、500 m、SMF、MPO16、EML/PIN 的单产品实例（S4）；
- OFC 2025 分别展示 SiPh 1.6T-DR8 与 VCSEL 1.6T-SR8，但这不是隔离单变量比较（S9）；
- Intel 披露 SiPh 平台覆盖 pluggable、stand-alone on-board 和 co-packaged 能力；只有其自述 co-packaged 演示属于演示声明，其余不能自动视为已观察产品（S10）。

这些仍不足以形成 TQ009 Route Profile 库，也不支持路线优劣、成熟度或市场份额判断。

## 9. 状态

- canonical_write_performed: false
- coverage_status_changed: false
- new_question_ids_created: false
- TQ005–TQ008 均为 draft-only，未标记覆盖。
