# TQ005–TQ008 四轴展开（draft_only 输出）

本文件严格按 `contract.md` 执行：未写 canonical、未改 coverage、未建 QID、未进入 TQ009/WHY/公司归群/路线优劣/落库。所有事实均引用 S1–S13，证据标签使用强制六类；凡只对应"候选/规范允许"者一律不写成"已观察/已量产"。

---

## TQ005：产品/链路标准轴

### 1. 一句话答案

该轴记录 host 与 media 两侧在无需知道对方模块内部实现的前提下必须约定的外部互操作链路边界——aggregate rate、host/media lane 数与 lane rate、modulation、FEC/PMD、media、reach、wavelength/parallel-vs-WDM organization——不能据此推出模块内部 DSP/linear（TQ006）、光子平台（TQ007）或封装位置（TQ008）（S1、S2、S3、S13）。

### 2. 操作性定义/字段

该轴约束的外部边界：host 侧为 host-module 高速差分电连接（S2 p.66 Host Interface；S13 §15.4 的 8 Tx/8 Rx 差分对与 lane-rate 模式）；media 侧为 optical signaling 参数与 PMD 边界（S1；S2 Media Interface；S3 定义的 host-module electrical 与 optical test boundaries）。S2 将 Host/Media Interface 分开并让 `MediaInterfaceID` 指向相关标准，说明该轴记录的是通用可互操作字段，不是某模块内部实现。

最小字段集：

| 最小字段 | 操作定义 | 来源锚点 |
|---|---|---|
| aggregate rate | 链路聚合速率 | S1（802.3df 规定 400/800 Gb/s MAC/PHY）；S4（观察 800G 产品） |
| host/media lane 数与 lane rate | host 电 lane 与 media 光 lane 的条数及每 lane 速率 | S1 官方解读（800G 复用 100G signaling、parallel ×8；8 lane 可配 1×8/2×4/4×2/8×1）；S3（1/2/4/8 × 100 Gb/s）；S2（Host/Media Interface 区分） |
| modulation | 每 lane 调制格式 | S3（53.125 GBd PAM4） |
| FEC/PMD | 链路 FEC 与 PMD 边界 | S3（RS(544,514)）；S1（PHY/PMD 层）；S2（MediaInterfaceID 指向相关标准，不替代 PMD） |
| media | 传输介质 | S3（parallel SMF）；S4（Single SMF） |
| reach | 可达距离 | S3（0.5–500 m）；S4（500 m） |
| wavelength / parallel-vs-WDM organization | 波长组织与并行/WDM 结构 | S3（1310 nm 附近、parallel SMF）；S2（p.197 Wavelength Information、p.248 Media Lane to Media Wavelength and Fiber Mapping） |

三类名称必须分栏：

| 层 | 定义 | 已锚定示例 | 证据 |
|---|---|---|---|
| 正式标准名 | IEEE 规范中的 PHY/PMD/层边界 | IEEE 802.3df-2024（Clause 169–173、Annex 172A/173A、400/800 Gb/s MAC/PHY/management） | S1，formal_standard |
| 具名 MSA profile | MSA 把 rate/lane/PAM4/FEC/SMF/1310/reach 与电接口联合成一个完整 profile 的 reference object | `n00G-DRn-LPO`（100G-DR-LPO Rev 1.0） | S3，msa_spec |
| 公司产品/演示后缀 | 产品名后缀或演示名称，不升格 | FTCE4517E1PxM 的 `DR+`（页面同时声明 OSFP MSA、IEEE 802.3bs、P802.3ck 合规） | S4，observed_product_or_demo |

### 3. 证据化示例

- **S1（formal_standard：官方摘要 + 官方解读）**：802.3df-2024 增加 Clause 169–173 并规定 400/800 Gb/s 的 MAC、PHY 与 management parameters；官方文章说明 800G 复用 100G signaling、parallel ×8、八 lane 端口可配 1×8/2×4/4×2/8×1。只支持：正式标准名与外部 PHY/PMD 边界归 TQ005、lane 组织结构。不支持：完整 PMD 数值表、模块内部职责、光子平台或封装位置。
- **S2（formal_standard：管理接口规范）**：CMIS 5.4 p.66 Host/Media Interface、p.197 Wavelength Information、p.248 Media Lane to Media Wavelength and Fiber Mapping。只支持：host/media 侧边界与可管理波长/光纤映射元数据。不支持：替代 PMD 给出某产品的 aggregate rate、reach、FEC 合规结论，或证明广告能力已量产。
- **S3（msa_spec）**：`n00G-DRn-LPO` 联合 1/2/4/8 × 100 Gb/s、53.125 GBd PAM4、RS(544,514)、parallel SMF、1310 nm、reach 0.5–500 m，并定义测试边界。只支持：TQ005 字段如何共同构成一个具名 profile。不支持：`-LPO` 升格为 IEEE PMD 名、所有 100G/lane 链路均 linear、所有被许可实现已量产。
- **S4（observed_product_or_demo）**：FTCE4517E1PxM 字段为 800G、500 m、1310 Band、Single SMF、MPO16，声明 OSFP MSA/802.3bs/P802.3ck 合规。只支持：已观察产品字段与 `DR+` 后缀需单独记录。不支持：`DR+` 为标准名、从该页单独建立完整链路画像。

### 4. 禁止外推

- 不能推出 DSP/linear（TQ006）、EML/SiPh（TQ007）、OSFP/CPO（TQ008）：S1 摘要、S2 的 MediaInterfaceID、S13 的 electrical signal boundary 都只约束外部边界。
- 具名 MSA profile（S3）不得作为第五根轴，不得在 TQ005/TQ006 双计。
- `DR+`（S4）不得升格为 IEEE 标准名；标准/规范沉默（如 S3 允许多种实现）不得写成已观察产品组合。
- S2 不能替代 PMD 给出合规结论，也不能据其结论推断任何 capability 已实现。

### 5. next_questions_without_new_qid

- parent_question_id: TQ005
  - question: 在 parallel SMF 的 DR 类 profile 之外，本地来源是否已有支持 WDM 组织（FR4/LR 类 wavelength mapping）的正式标准或已观察产品实例？
  - why_open: CMIS 提供 wavelength 信息与 media-lane-to-wavelength/fiber mapping 字段（S2），但本地语料只观察到 parallel DR 类实例，WDM 字段尚无产品/标准实例支撑。
  - needed_evidence: 同时给出 lane/波长组织与 product/standard 名的正式标准页或已观察产品/演示页。
- parent_question_id: TQ005
  - question: 已观察的 800G 链路是否都采用 8×100G 结构，还是存在 4×200G 或其他 lane-rate 的已观察实例？
  - why_open: IEEE 官方解读说明 8-lane 端口可配 1×8/2×4/4×2/8×1（S1），但本地来源没有逐一对应的产品实例。
  - needed_evidence: 明确记录 lane 数与 lane rate 的正式标准或已观察产品/演示。
- parent_question_id: TQ005
  - question: 800G 之外的 aggregate rate（400G、1.6T）链路画像是否已有本地来源支撑？
  - why_open: 1.6T 只出现在公司演示（S9），未给完整最小字段集；400G 无本地实例。
  - needed_evidence: 覆盖 400G 或 1.6T 的正式标准摘要，或带完整字段表的产品/演示页。
- parent_question_id: TQ005
  - question: 除 0.5–500 m 的 LPO profile（S3）与 500 m 的 DR+ 产品（S4）外，更长 reach（如 ≥2 km）出现在哪些正式标准或已观察产品？
  - why_open: reach 字段需要 DR 族之外的值范围，而本地语料无 2 km 以上实例。
  - needed_evidence: 同时声明 reach 与 PMD 名的正式标准或产品页。
- parent_question_id: TQ005
  - question: 把"正式标准名 / 具名 MSA profile / 公司产品与演示后缀"三类名称稳定分栏的规则能否从更多来源归纳？
  - why_open: S3 的 `-LPO` 与 S4 的 `DR+` 说明名称混杂是常见风险，但本地语料只有两个例子，不足以形成规则。
  - needed_evidence: 同时出现两类以上名称的规范/产品/演示页。

---

## TQ006：电接口架构轴

### 1. 一句话答案

该轴按 host、module/engine、optical path 之间的职责分配区分 retimed、linear、Tx-retimed/Rx-linear（LRO/RTLR）、half-retimed、direct-drive candidate，并必须为每一职责类标注证据层级，尤其不得把 framework/in-progress 候选写成量产菜单（S3、S5、S6、S7、S8、S9）。

### 2. 操作性定义/职责表

职责表（以 host、module/engine、optical path 为参照；证据层级按强制标签写出，S9 之外均为规范/框架/解释层定义，不构成量产菜单）：

| 职责类 | host 侧 | module/engine 侧 | optical path | 证据层级（来源） |
|---|---|---|---|---|
| retimed（full retimed） | 接收经 module 恢复的信号；FEC 归属本轮来源未单独披露 | Tx/Rx 两向由 module DSP 做复杂数字处理；engine/模块保留 retiming | 双向时钟恢复后驱动光/电 | observed_product_or_demo（S9：3nm DSP retimed 变体）；framework_or_in_progress（S6 Figure 5）；msa_spec（S5 官方 FAQ 对照定义） |
| linear（仅以 `linear + pluggable` 复合 alias 与 100G-DR-LPO 具名职责为证据） | 承担 error correction、retiming、DAC/ADC 与 FEC encode/decode，DSP-based SerDes 提供 equalization | 仅在电↔光之间线性转换、模块内无 DSP | 无数字处理路径 | msa_spec（S3 §5.1/§5.6/§5.10；S5 官方 FAQ）；framework_or_in_progress（S6 linear amplified） |
| Tx-retimed / Rx-linear（LRO / RTLR） | Rx 向由 host SerDes 作为 linear receiver 接收并 equalize | Tx 向 retimed（演示中 DSP 仅在 Tx 做 retime） | 接收向 linear、发送向 retimed | framework_or_in_progress（S7/S8：RTLR 项目 developing）；observed_product_or_demo（S9：LRO 变体）；msa_spec（S5：命名为 LRO/half-retimed） |
| half-retimed | 一侧处理留在 host（方向未展开） | 一侧处理留在 module（方向未展开） | 一侧时钟恢复 | framework_or_in_progress（S6 Figures 6–7 定义 linear amplified 与 half-retimed 候选）；msa_spec（S5 half-linear 讨论把 LPO-to-retimed 组合与全 linear 分开） |
| direct-drive candidate | host ASIC 直接驱动 modulator/laser，Rx 在 host 做 equalization | 只保留线性光通道所需功能 | 最简 engine 光通道 | framework_or_in_progress（S6 Figure 8；future IA 仍需补 test points/methodologies/criteria） |

注意：LRO（S5/S9）、RTLR（S7/S8）与 OIF framework 的 half-retimed（S6）是否同义、scope 是否一致，本地来源未做逐词对照，见下方开放问题。

### 3. 证据化示例

- **S3 + S5（msa_spec + LPO MSA 官方 FAQ）**：100G-DR-LPO 中 host 承担 error correction、retiming、DAC/ADC 与 FEC，module 线性转换；FAQ 定义 LPO 为 module 内无 DSP chip 的 fully linear pluggable。只支持：具名 profile 职责与 `linear + pluggable` 复合 alias。不支持：所有行业 LPO 实现相同、低功耗/成本/鲁棒性主张替代实测。
- **S6（framework_or_in_progress）**：Figures 5–8 定义 re-timed、linear amplified、half-retimed、direct-drive 候选；direct-drive 由 host ASIC 直接驱动 modulator/laser。只支持：候选功能分配与 future IA 缺口。不支持：写成完整量产菜单、约 50 mm 作为跨封装统一阈值。
- **S7 + S8（framework_or_in_progress）**：CEI-224G-Linear、EEI、EEI-224G-RTLR/EEI-112G-RTLR 项目均为 in-progress；RTLR 定义为 Tx retimed、Rx 利用 host SerDes 的 linear receiver。只支持：OIF 当前研究范围与候选定义。不支持：`will support`/`is studying` 改写为已完成标准、已量产产品或市场采用率。
- **S9（observed_product_or_demo）**：同一 1.6T-DR8、OSFP、8×200G、silicon photonics 的三个演示中观察到 LRO（DSP 仅在 Tx retime）与 3nm DSP retimed。只支持：电职责可在其他已列条件相同时变化。不支持：三个演示量产、`ultra-low bit error rates` 描述独立判定职责类别、功耗或路线排名。
- **S5（msa_spec：官方 FAQ 解释层）**：区分 retimed module（Tx/Rx 双向 module DSP 数字处理）与 linear；把 linear receiver + retimed transmitter 命名为 LRO/half-retimed。只支持：命名与职责边界。不支持：FAQ 的 roadmap 证明产品均存在或量产。

### 4. 禁止外推

- direct-drive、half-retimed 等 OIF framework 候选不得写成完整、正式、量产的行业菜单（S6）。
- OIF 页面的 `will support`/`is studying`/`are developing` 不得改写为已完成标准、已量产产品或市场采用率（S7、S8）。
- LPO 只能作 `linear + pluggable` 复合 alias，具名 profile（S3）只作 reference；不得脱离 `pluggable` 把 LPO 当纯电架构同义词，不得吞并其他行业 LPO 用法（S5）。
- S5 的低功耗/低成本/鲁棒性陈述不能替代实测。
- S9 不证明量产；`ultra-low bit error rates` 描述不足以独立判定职责类别。

### 5. next_questions_without_new_qid

- parent_question_id: TQ006
  - question: 除 100G-DR-LPO 具名 profile（S3）外，本地来源是否还有其他 `linear + pluggable` 的已观察产品/演示实例？
  - why_open: LPO 泛称是复合 alias（S5），但本地语料只有一个具名 profile 和一个演示变体（S9），不足以支撑该职责类的值域。
  - needed_evidence: 明确声明 linear 职责与 pluggable 放置的已观察产品/演示页。
- parent_question_id: TQ006
  - question: OIF 的 direct-drive 候选在哪些具体接口/测试上确缺 test points、methodologies、criteria？
  - why_open: S6 声明 future IA 仍需补这些，但本地框架文件没有给出具体缺口清单。
  - needed_evidence: OIF 后续 IA 草案、项目更新页或其他 framework 文件。
- parent_question_id: TQ006
  - question: LRO（S5/S9）、RTLR（S7/S8）与 OIF framework 的 half-retimed（S6）是否是同一职责组合的不同命名，还是存在 scope 差异？
  - why_open: 三者都指向"Tx 侧 retimed、Rx 侧 linear"附近，但本地来源没有做逐词对照，无法确认是否同义。
  - needed_evidence: 能同时定义至少两个词且给出 scope 的 MSA/OIF 文件或术语表。
- parent_question_id: TQ006
  - question: 在同一 1.6T-DR8/OSFP/SiPh 演示（S9）中，LRO 变体与 3nm DSP 变体的其他字段（FEC、host SerDes、BER、驱动）是否一致？
  - why_open: 只有确认其他字段一致，才能把差异归因于电职责；当前演示摘要缺完整对照字段。
  - needed_evidence: 含完整链路与电接口字段的演示/白皮书或产品页。
- parent_question_id: TQ006
  - question: 在 host 承担 FEC 与 equalization 的 linear profile 中，host SerDes 的具体规格是否有已观察或已规定证据？
  - why_open: S3 说明 host 由 DSP-based SerDes 提供 equalization，但本地来源未给出 host SerDes 规格实例。
  - needed_evidence: 规定 host SerDes 规格的 MSA/标准条文或披露具体 host SerDes 的产品/系统页。

---

## TQ007：光子平台/实现轴

### 1. 一句话答案

该轴在 TQ007 现有 QID 内部用 `platform/material`、`light source`、`modulator/emitter`、`detector`、`integration` 五个嵌套字段记录光子实现；SiPh/InP/GaAs 是平台/材料粒度，EML 是器件组合，MZM/VCSEL/PIN 是更细的调制器/emitter/detector 粒度，不同粒度不构成同级互斥枚举（S6、S9、S10、S11、S12、S4）。

### 2. 操作性定义/五嵌套字段

示例值非穷尽，均有一手来源支持：

| 嵌套字段 | 粒度/定义 | 示例值 | 来源与证据类型 |
|---|---|---|---|
| platform/material | PIC/集成平台或衬底材料体系 | silicon photonics（Intel 平台描述）；InP（EML 的 material 信息） | S10 company_platform_statement；S11 company_platform_statement（器件厂商官方定义）；S6 framework_or_in_progress（PIC 词汇、SiPh/VCSEL 候选） |
| light source | 光源及其集成方式：external / integrated / on-chip | on-chip DWDM lasers/SOAs；hybrid laser-on-wafer / direct coupling；external laser 分离式 | S10 company_platform_statement；S6 framework_or_in_progress（EIC、ELS、Integrated Light Source、On-chip Light Source） |
| modulator/emitter | 调制器或发射器器件粒度 | EML（InP DFB + EAM）；MZM（SiPh MZM PIC）；VCSEL（emitter） | S11 company_platform_statement（EML 定义）；S12 observed_product_or_demo（SiPh MZM PIC）；S9 observed_product_or_demo（200G VCSEL） |
| detector | 探测器粒度 | PIN | S4 observed_product_or_demo（Rx=PIN）；S6 framework_or_in_progress（PIC 可含 photodetectors）；S12 observed_product_or_demo（EML/PD 互操作） |
| integration | PIC 与 EIC、光源、ASIC 的集成方式 | PIC+CMOS EIC die stack；TX PIC/RX PIC；pluggable / on-board / co-packaged 安装 | S10 company_platform_statement；S6 framework_or_in_progress（Optical Chiplet；EIC 可含 laser/modulator driver、TIA/post-amplifier） |

粒度说明（分类推断，analytical_inference，锚于 S6/S9/S10/S11/S12/S4）：

- `SiPh`、`InP`、`GaAs`：platform/material 粒度。
- `EML`：跨 `light source` 与 `modulator/emitter` 的器件组合（DFB 出光 + EAM 调制），并带 InP material 信息。
- `MZM`：modulator 粒度；`VCSEL`：emitter 粒度；`PIN`：detector 粒度。
- 禁止制作 EML/SiPh/VCSEL 的同级互斥表。

三类证据必须分开：器件定义（S11，定义器件组合本身）、平台能力披露（S10，声称能力不等于产品实例）、产品实例/演示（S4、S9、S12，已观察组合）。

### 3. 证据化示例

- **S11（company_platform_statement：器件厂商官方定义页）**：EML = InP externally-modulated laser = DFB diode laser + 单片集成 EAM，DFB 连续波出光、EAM 调制为 NRZ 或 PAM4。只支持：EML 作为发射器件组合的定义及其 InP material 信息。不支持：EML 与 DSP/LPO、OSFP/CPO、特定 reach/PMD 的必然对应。
- **S10（company_platform_statement）**：Intel 把 silicon photonics 描述为平台，实例值含 PIC、on-chip DWDM lasers/SOAs、TX PIC、RX PIC、hybrid laser-on-wafer/direct coupling、PIC+CMOS EIC die stack。只支持：来源自有的平台级披露与实例值。不支持：外推所有 SiPh、给出通用 MZM/PIN 定义、判断平台优劣。
- **S6（framework_or_in_progress）**：glossary 区分 EIC、ELS、Integrated Light Source、On-chip Light Source、OIC/PIC、Optical Chiplet；PIC 可含 waveguides、splitters/combiners、modulators、photodetectors；举 SiPh integrated laser 与 VCSEL engine 为实现候选。只支持：光源与 PIC 实现粒度的分类词汇与候选。不支持：证明某组合已产品化或构成穷尽字典。
- **S4（observed_product_or_demo）**：FTCE4517E1PxM 参数表 Transmitter=EML、Receiver=PIN。只支持：一个已观察实例中 emitter/modulator 与 detector 分别记录。不支持：补全该产品 PIC platform/material 或 light-source integration，不外推所有 800G-DR+/OSFP/EML 产品。
- **S9 + S12（observed_product_or_demo）**：OFC 2025 分别观察 silicon photonics 架构的 1.6T-DR8 与 200G VCSEL 的 1.6T-SR8；ECOC 2022 观察 SiPh MZM PIC 与 EML/PD 在 800G-DR8+ 族互操作及 VCSEL AOC 实例。只支持：SiPh 是 platform/architecture 粒度、VCSEL 是 emitter 粒度、二者不同枚举层。不支持：性能/成本/成熟度排序、补全 detector/光源集成细节。

### 4. 禁止外推

- 禁止制作 EML/SiPh/VCSEL 的同级互斥表（S11/S10/S9/S12 粒度不同）。
- EML（S11）不必然对应 DSP/LPO、OSFP/CPO、特定 reach 或 PMD。
- Intel 平台能力（S10）不得外推为所有 SiPh；`hybrid laser-on-wafer/direct coupling` 等是公司披露，不等于通用标准。
- 候选 light-source/PIC 实现（S6）不得写成产品化或穷尽字典。
- 已观察演示（S9/S12）不做性能、成本、成熟度排序。

### 5. next_questions_without_new_qid

- parent_question_id: TQ007
  - question: 除 Lumentum 页（S11）外，本地来源是否有第二个一手来源支撑 EML = InP DFB + 单片集成 EAM 的定义？
  - why_open: 字典需要至少两个独立一手来源，当前只有一个器件厂商定义。
  - needed_evidence: 第二个器件或平台厂商的官方 EML 定义页。
- parent_question_id: TQ007
  - question: Intel 披露的 on-chip DWDM lasers/SOAs 与 hybrid laser-on-wafer / direct coupling（S10）分别对应 OIF glossary 的 external / integrated / on-chip light source 中的哪一类？
  - why_open: S10 提到多种光源集成方式，但未与 S6 的分类词汇逐项对照。
  - needed_evidence: 逐项对照 light-source 类别的公司披露或 framework。
- parent_question_id: TQ007
  - question: 已观察的 SiPh MZM PIC（S12）与 1.6T-DR8 SiPh 演示（S9）中，modulator driver 放在 EIC 还是 module 其他位置？
  - why_open: S6 说明 EIC 可含 modulator driver，但已观察来源未披露 driver 位置。
  - needed_evidence: 披露 driver 放置的产品/演示页或 framework。
- parent_question_id: TQ007
  - question: 除 PIN 外，本地来源是否观察到其他 detector 类型（如 APD）的产品/演示实例？
  - why_open: detector 字段目前只有 PIN 一个值，不足以形成最小字典。
  - needed_evidence: 声明 detector 类型的已观察产品/演示页。
- parent_question_id: TQ007
  - question: 200G VCSEL 1.6T-SR8 演示（S9）是否披露了 detector、light source 集成与 platform/material？
  - why_open: S9 只给了 VCSEL emitter 与 SR8 目标，其余四个嵌套字段缺失。
  - needed_evidence: 含五字段披露的演示/白皮书或产品页。

---

## TQ008：封装/放置架构轴

### 1. 一句话答案

该轴以 optical engine 相对 host ASIC、first-level substrate 与 front panel 的位置做定性分类，至少区分 `front-panel pluggable / other on-board / near-package NPO / CPO`；OSFP/QSFP-DD 只是 pluggable 子层 form factor，NPO 必须锚定 OIF 定义、CPO 必须锚定 same first-level substrate（S6、S13、S10、S2、S3）。

### 2. 操作性定义/位置分类表

| 类别 | 操作性判据（相对 host ASIC / first-level substrate / front panel） | 来源锚点 |
|---|---|---|
| front-panel pluggable | transceiver 插入系统 rack front panel 的 socket；机械/热/connector/power/electrical signal 边界由 form-factor MSA 定义；SFP/QSFP/QSFP-DD/OSFP 为 form-factor 例子 | S6 glossary `Pluggable Optics`；S13（OSFP 机械/电边界、§15.4 的 8 Tx/8 Rx 差分对与 lane-rate 模式） |
| other on-board | 不插 front panel、也不位于 host ASIC 的 first-level substrate 上的板上放置；如 Intel stand-alone on-board OCI；不得与 NPO 合并 | S6（单独提到 on-board optical/electrical engine，不与 NPO 自动合并）；S10（stand-alone on-board OCI）；S2（CMIS §1.1.1 管理范围含 onboard，但不定义 NPO 位置边界） |
| near-package NPO | OIF Figure 2d：packaged ASIC 与 engine 通过 socket 接入 common substrate，便于装配/返工（socketed NPO）；锚定 OIF 文件 | S6（p.10 Figure 2d 说明；glossary `Optical Chiplet` 等） |
| CPO | optical/electrical communications device 与 host ASIC 位于同一 first-level substrate；glossary 释为 active optical components attached to a common substrate containing ASICs | S6（p.9 §5、Figure 1、glossary `CPO`/`Co-Packaged Assembly Substrate`） |

距离只作定性位置分类，不虚构统一毫米阈值；OIF 框架中约 50 mm 的讨论是特定 first-level substrate 接口语境，不是跨封装统一标准（S6）。

### 3. 证据化示例

- **S6（framework_or_in_progress）**：CPO = 同一 first-level substrate；Figure 2d = socketed NPO；glossary 区分 `CPO`、`Co-Packaged Assembly Substrate`、`Optical Chiplet`、`Pluggable Optics`。只支持：NPO/CPO 定义锚与定性位置分类。不支持：统一毫米阈值、固定光子平台/电职责、量产状态。
- **S13（msa_spec）**：OSFP = Octal Small Form Factor Pluggable Module；规范机械/热、connector、power 与 electrical signal 边界；§15.4 规定 8 Tx/8 Rx 高速差分对与若干 lane-rate 模式。只支持：OSFP 作为 pluggable 子层 form factor 与 host 电边界。不支持：内部 PMD、光子平台或 retimed/linear 职责。
- **S10（company_platform_statement，含公司自述演示声明）**：同一 Intel SiPh 平台披露用于 pluggable transceivers、stand-alone on-board OCI 与 co-packaged OCI，并自述曾现场演示 OCI chiplet 与 Intel CPU co-packaged。只支持：光子平台≠封装位置、`other on-board` 与 CPO 分开。不支持：`can also be supported` 等于已量产、stand-alone on-board 改写为 OIF NPO。
- **S2 + S3（formal_standard + msa_spec）**：CMIS §1.1.1 物理范围同时含 pluggable 与 onboard（QSFP-DD、OSFP、COBO）；100G-DR-LPO 明确 form-factor agnostic、QSFP/QSFP-DD/OSFP 仅列为例。只支持：管理接口与 linear profile 不绑定单一 form factor。不支持：generic onboard 仅凭 CMIS 判为 NPO、所有被许可组合均已量产。
- **S4（observed_product_or_demo）**：FTCE4517E1PxM Form Factor=OSFP，为 front-panel pluggable 的已观察产品实例。只支持：一个已观察 pluggable 实例的 form factor 记录。不支持：推出该产品电职责或光子平台、比较 pluggable/NPO/CPO 优劣。

### 4. 禁止外推

- `other on-board` 与 `near-package NPO` 不得合并；Intel stand-alone on-board OCI（S10）不得改写为 OIF NPO（S6）。
- 不虚构统一毫米阈值；S6 的约 50 mm 仅为特定 first-level substrate 接口讨论。
- OSFP/QSFP-DD（S13/S6）不能推出内部 PMD、光子平台或 retimed/linear 职责。
- `can also be supported`（S10）是平台能力，不等于已观察量产产品。
- 已观察 pluggable 产品（S4）不用于比较三种放置的优劣。

### 5. next_questions_without_new_qid

- parent_question_id: TQ008
  - question: OIF Figure 2d 的 socketed NPO 与 Figure 2 其他 arrangement 的操作性区分判据是什么（socket、可返修、on-substrate 走线等）？
  - why_open: S6 提供定义锚与图，但本地来源缺少逐图判据列表，实际操作时可能误并。
  - needed_evidence: OIF framework 的图注/正文细节或其他截获说明。
- parent_question_id: TQ008
  - question: Intel stand-alone on-board OCI（S10）与 host ASIC 的相对位置、substrate 关系与连接方式是否有已观察披露？
  - why_open: S10 只声明"可以支持"stand-alone on-board，未给布局细节，无法与 NPO/CPO 定义核对。
  - needed_evidence: 披露 on-board OCI 布局的产品/演示/白皮书页。
- parent_question_id: TQ008
  - question: 自述的 OCI chiplet + CPU co-packaged 演示（S10）是否披露 first-level substrate 与 socketed 与否？
  - why_open: 公司只自述演示过 co-packaged，没有基板级细节，无法与 OIF CPO 定义逐项核对。
  - needed_evidence: 含共封装基板细节的演示/白皮书或可核实图片。
- parent_question_id: TQ008
  - question: 除 OSFP（S4/S13）与 QSFP-DD（S2/S12）外，本地来源是否观察到 front-panel pluggable 的第三种 form factor 实例（如 QSFP、SFP-DD）？
  - why_open: pluggable 子层需要多于两个已观察 form factor 才能成字典。
  - needed_evidence: 声明 form factor 的已观察产品/演示页。
- parent_question_id: TQ008
  - question: 除 Intel 平台能力披露（S10）外，是否有第二家来源观察到"同一光子平台用于 pluggable、on-board、co-packaged 三位置"的实例或披露？
  - why_open: S10 是唯一的跨位置平台声明，单来源不足以支撑"光子平台≠放置位置"的归纳。
  - needed_evidence: 第二家公司的多位置平台披露或已观察产品组合。

---

## 原子主张（draft_id）

每题 6 条，共 24 条；全部 `would_mark_covered: false`。

### TQ005

- `draft_id`: `tq005-001`
  - claim: TQ005 只约束外部互操作边界——host 侧 host-module 高速差分电连接、media 侧 optical PMD/media 参数；不含模块内部电架构、光子实现或封装位置。
  - evidence: S1（formal_standard）、S2（formal_standard）、S13（msa_spec，host 电边界对照）
  - would_mark_covered: false
- `draft_id`: `tq005-002`
  - claim: 最小字段集为 aggregate rate、host/media lane 数与 lane rate、modulation、FEC/PMD、media、reach、wavelength/parallel-vs-WDM organization；字段联合成一个可互操作链路画像。
  - evidence: S3（msa_spec，字段联合实例）、S1（formal_standard，lane 组织）、S2（formal_standard，波长映射元数据）
  - would_mark_covered: false
- `draft_id`: `tq005-003`
  - claim: IEEE 802.3df-2024 提供 400/800 Gb/s 的 MAC/PHY/PMD 与 management 边界；800G 复用 100G signaling、parallel ×8，八 lane 端口可配 1×8/2×4/4×2/8×1。
  - evidence: S1（formal_standard + 官方解读）
  - would_mark_covered: false
- `draft_id`: `tq005-004`
  - claim: 具名 MSA profile（100G-DR-LPO / n00G-DRn-LPO）是字段联合成完整 profile 的 reference object，覆盖 1/2/4/8×100G、53.125 GBd PAM4、RS(544,514)、parallel SMF、1310 nm、0.5–500 m；不是正式 IEEE PMD 名，也不构成第五根轴。
  - evidence: S3（msa_spec）
  - would_mark_covered: false
- `draft_id`: `tq005-005`
  - claim: CMIS 5.4 区分 host interface 与 media interface，提供 wavelength 信息与 media-lane-to-wavelength/fiber mapping 元数据，但 MediaInterfaceID 指向相关标准，不能替代 PMD 给出 rate/reach/FEC 合规结论。
  - evidence: S2（formal_standard）
  - would_mark_covered: false
- `draft_id`: `tq005-006`
  - claim: 已观察产品实例 FTCE4517E1PxM（800G-DR+ OSFP、500 m、1310 Band、Single SMF、MPO16）中的 `DR+` 是产品后缀，须与页面声明的 OSFP MSA / IEEE 802.3bs / P802.3ck 引用分栏记录。
  - evidence: S4（observed_product_or_demo）
  - would_mark_covered: false

### TQ006

- `draft_id`: `tq006-001`
  - claim: 电接口架构轴按 host、module/engine、optical path 之间的职责分配区分 retimed、linear、Tx-retimed/Rx-linear（LRO/RTLR）、half-retimed、direct-drive candidate。
  - evidence: S5（msa_spec 官方 FAQ）、S6（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq006-002`
  - claim: 在 100G-DR-LPO 具名 profile 中，host 承担 error correction、retiming、DAC/ADC 与 FEC encode/decode，DSP-based SerDes 提供 equalization；module 仅在电↔光之间线性转换。
  - evidence: S3（msa_spec）、S5（msa_spec 官方 FAQ）
  - would_mark_covered: false
- `draft_id`: `tq006-003`
  - claim: retimed module 在 Tx/Rx 两向由 module DSP 做复杂数字处理；linear receiver + retimed transmitter 被命名 LRO/half-retimed，且已观察该变体。
  - evidence: S5（msa_spec 官方 FAQ）、S9（observed_product_or_demo）
  - would_mark_covered: false
- `draft_id`: `tq006-004`
  - claim: OIF framework 的 re-timed、linear amplified、half-retimed、direct-drive 是候选功能分配；direct-drive 由 host ASIC 直接驱动 modulator/laser、Rx 在 host equalize；future IA 仍需 test points/methodologies/criteria。
  - evidence: S6（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq006-005`
  - claim: OIF current-work 与 EEI 页面中 CEI-224G-Linear、EEI、EEI-224G-RTLR/EEI-112G-RTLR 项目均处于 developing/studying 状态；RTLR = Tx retimed、Rx 利用 host SerDes 的 linear receiver。
  - evidence: S7（framework_or_in_progress）、S8（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq006-006`
  - claim: 已观察演示中，同一 1.6T-DR8/OSFP/SiPh/8×200G 条件下 LRO 与 3nm DSP retimed 并存，证明电职责可独立于已列链路/平台字段变化；不证明量产。
  - evidence: S9（observed_product_or_demo）
  - would_mark_covered: false

### TQ007

- `draft_id`: `tq007-001`
  - claim: TQ007 在现有 QID 内使用五个嵌套字段：platform/material、light source、modulator/emitter、detector、integration；SiPh/InP/GaAs 属于平台/材料粒度。
  - evidence: S10（company_platform_statement）、S6（framework_or_in_progress）、S11（company_platform_statement 器件定义）
  - would_mark_covered: false
- `draft_id`: `tq007-002`
  - claim: EML 是 InP DFB diode laser + 单片集成 EAM 的发射器件组合，跨 light source 与 modulator/emitter 字段并带 InP material 信息。
  - evidence: S11（company_platform_statement 器件厂商官方定义）
  - would_mark_covered: false
- `draft_id`: `tq007-003`
  - claim: MZM 是调制器粒度、VCSEL 是 emitter 粒度、PIN 是 detector 粒度；它们与 SiPh/InP 平台粒度不构成同级互斥枚举。
  - evidence: S12（observed_product_or_demo）、S9（observed_product_or_demo）、S4（observed_product_or_demo）、S6（framework_or_in_progress）；分类为 analytical_inference
  - would_mark_covered: false
- `draft_id`: `tq007-004`
  - claim: OIF glossary 区分 EIC、ELS、Integrated Light Source、On-chip Light Source、OIC/PIC、Optical Chiplet；PIC 可含 waveguides、splitters/combiners、modulators、photodetectors。
  - evidence: S6（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq007-005`
  - claim: Intel 平台披露把 silicon photonics 描述为平台，实例含 on-chip DWDM lasers/SOAs、TX/RX PIC、hybrid laser-on-wafer/direct coupling、PIC+CMOS EIC die stack；这是公司声明，不外推所有 SiPh。
  - evidence: S10（company_platform_statement）
  - would_mark_covered: false
- `draft_id`: `tq007-006`
  - claim: 已观察实例中，FTCE4517E1PxM 产品 Tx=EML、Rx=PIN；OFC 2025 演示含 SiPh 1.6T-DR8 与 200G VCSEL 1.6T-SR8；ECOC 2022 观察 SiPh MZM PIC 与 EML/PD 互操作及 VCSEL AOC。
  - evidence: S4、S9、S12（observed_product_or_demo）
  - would_mark_covered: false

### TQ008

- `draft_id`: `tq008-001`
  - claim: TQ008 以 optical engine 相对 host ASIC、first-level substrate、front panel 的位置分类，至少分 front-panel pluggable、other on-board、near-package NPO、CPO。
  - evidence: S6（framework_or_in_progress）、S10（company_platform_statement）
  - would_mark_covered: false
- `draft_id`: `tq008-002`
  - claim: CPO 定义为 optical/electrical communications device 与 host ASIC 位于同一 first-level substrate；glossary 释为 active optical components attached to a common substrate containing ASICs。
  - evidence: S6（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq008-003`
  - claim: NPO 锚定 OIF Figure 2d 的 socketed arrangement：packaged ASIC 与 engine 经 socket 接入 common substrate、便于装配/返工；不得与 other on-board 合并。
  - evidence: S6（framework_or_in_progress）
  - would_mark_covered: false
- `draft_id`: `tq008-004`
  - claim: OSFP/QSFP-DD/QSFP 是 front-panel pluggable 下的 form-factor 子层；OSFP 规范只定义机械/热/connector/power/electrical signal 边界与 8 Tx/8 Rx 差分对，不决定内部 PMD、光子平台或电职责。
  - evidence: S13（msa_spec）、S6（framework_or_in_progress，Pluggable Optics 例子）
  - would_mark_covered: false
- `draft_id`: `tq008-005`
  - claim: 100G-DR-LPO 是 form-factor agnostic 的 `linear + pluggable` profile，QSFP/QSFP-DD/OSFP 只是例子；不能把 LPO 绑定到 OSFP，也不能与 CPO 同层直接比较。
  - evidence: S3（msa_spec）、S5（msa_spec 官方 FAQ）
  - would_mark_covered: false
- `draft_id`: `tq008-006`
  - claim: 位置距离先作定性分类，不设统一毫米阈值；OIF framework 中的约 50 mm 是特定 first-level substrate 接口讨论，不是跨封装统一标准。
  - evidence: S6（framework_or_in_progress）；归纳为 analytical_inference
  - would_mark_covered: false

---

## cross_axis_guardrails

- 轴边界：TQ005 只记录外部互操作边界，TQ006 只记录 host-module/optical path 电职责分配，TQ007 只记录光子实现，TQ008 只记录放置位置；任一轴取值不自动决定其他轴（S1/S2/S3/S13 边界证据 + S9 已观察差异）。
- 具名 MSA profile（S3）只作 reference object：可在 TQ005 作为字段联合实例引用、在 TQ006 作为 `linear + pluggable` 具名职责引用，不构成独立轴值、不制造第五根轴、不在两轴双计。
- 粒度守门：EML（器件组合，S11）、SiPh/InP/GaAs（平台/材料，S10/S6）、MZM/VCSEL（调制器/emitter，S12/S9）、PIN（detector，S4/S6）分属 TQ007 不同嵌套字段；LPO 必须拆为 electrical=linear + packaging=pluggable（S5/S3）。
- 层次守门：OSFP/QSFP-DD 是 pluggable 子层 form factor（S13/S6），不能与 CPO 同层比较；比较 LPO vs CPO 前先把 LPO 拆出 packaging=pluggable（S3/S6）。
- 证据守门：六标签（formal_standard / msa_spec / framework_or_in_progress / company_platform_statement / observed_product_or_demo / analytical_inference）强制使用；"候选/规范允许"≠"已观察/已量产"（S6/S10/S3）；标准沉默不写成已观察产品组合。
- 位置守门：`other on-board` 与 `near-package NPO` 分开（S10 vs S6），NPO 锚 OIF Figure 2d、CPO 锚 same first-level substrate，不设统一毫米阈值（S6）；generic onboard 不能仅凭 CMIS 归为 NPO（S2）。

## observed_differences_so_far

仅列已观察实例（observed_product_or_demo；唯一例外为带自述演示声明的公司平台披露，已注明）：

- 电架构：同一 1.6T-DR8、OSFP、SiPh、8×200G 条件下，Coherent 演示观察 LRO 与 3nm DSP retimed 并存（S9，observed_product_or_demo）。
- 光子实现 + form factor：800G-DR8+ 链路族中，SiPh MZM PIC + QSFP-DD800 与 EML/PD + OSFP 互操作（S12，observed_product_or_demo）。
- 产品级字段组合：FTCE4517E1PxM = 800G-DR+ OSFP、500 m、1310 Band、Single SMF、MPO16、Tx=EML、Rx=PIN（S4，observed_product_or_demo）。
- emitter 差异：OFC 2025 演示同时含 SiPh 架构 1.6T-DR8 与 200G VCSEL 1.6T-SR8（S9，observed_product_or_demo）。
- 位置差异（公司自述演示声明）：Intel 页自述曾现场演示 OCI chiplet 与 Intel CPU co-packaged，并披露同一平台支持 pluggable / stand-alone on-board / co-packaged（S10，company_platform_statement，含自述演示；非独立观察）。

以上只能证明已观察组合，不证明完整笛卡尔积、量产成熟度或路线优劣。

## stop_status

- canonical_write_performed: false
- coverage_status_changed: false
- new_question_ids_created: false
- 本输出为 draft_only Markdown，未执行任何落库/写入操作；未进入 TQ009、WHY、公司归群或路线优劣。
