# TQ004 draft-only 轴字典与可比较规则（attempt-2 收口版）

日期：2026-08-24
模式：`draft-only`；不写 canonical；不改变 TQ004 覆盖状态；不生成新问题 ID
控制文件：`contract-tq004.md` + `contract-tq004-attempt2.md`（冲突处以 attempt-2 为准）；已经吸收 `adjudication-tq004-attempt1.md` 的全部修正点

---

## 1. 结论摘要

TQ004「比较路线时必须分开哪些正交选择轴？」的本轮回答：

**技术路线必须写成四个分析轴的组合，且必须先拆复合标签、再归轴：**

1. **链路/接口画像（TQ005）**：要互通的是什么链路，外部互操作边界在哪；
2. **电信号处理架构（TQ006）**：retiming、FEC、均衡、DAC/ADC、DSP 的职责放在 host 还是 module/engine；
3. **光子实现（TQ007，嵌套字段）**：platform/material、light source、modulator/emitter、detector、integration；
4. **封装/放置架构（TQ008）**：光学相对 host ASIC 的位置、连接方式与更换边界。

本轮必须纠正的两处术语层级问题：

- **EML 与 SiPh 不是互斥同级枚举**：EML = InP DFB laser + 单片集成 EAM（S6），是「光源 + 调制器」的器件级发射实现；SiPh 是光子集成平台（S4），属于更高一层的 platform/material 字段。二者不得在同一维度横向排名。
- **LPO 不是纯电轴值**：它是 `linear 电架构 + pluggable 放置 + LPO MSA 接口 profile` 的复合 alias（S1、S2）。任何「DSP vs LPO」式比较必须改写为「retimed vs linear」的电职责比较，封装位置与接口 profile 单列。
- 同理，**CPO 只归 TQ008**，不固定 retimed/linear/direct-drive；**OSFP/QSFP-DD 是 pluggable 下的机械 form factor（S8）**，不与 CPO 同粒度。

跨轴结论只写已观察组合（本包共七组，见 §4），不写「每一轴值可与所有其他轴值共存」或「所有组合可量产」之类的全称命题。

本轮只回答轴字典与可比较规则。不回答路线胜负、公司归群、市场份额、完整路线画像；路线级功耗/成本/良率/密度排序只登记为 TQ014 后续依赖，不挂 PQ010。

---

## 2. 路线轴字典

### 轴 1：链路/接口画像（TQ005）

| 要素 | 内容 |
|---|---|
| 它回答的问题 | 要互通的是什么链路？外部互操作边界在哪里？链路级目标（速率、距离、介质、lane 组织、接口配对）是什么？ |
| 典型轴值 | 协议族（IEEE 802.3 Ethernet 等）；总速率（400G、800G、1.6T）；host/media lane 数与 lane rate（8×200G、8×100G 等）；调制格式（PAM4）；FEC/PMD（KP4、DR8、FR8 等）；介质（SMF、MMF、copper/backplane）；reach（如 500 m、2 km）；波长组织（1310 nm 并行、WDM）；接口 profile（如 LPO MSA 定义的 host-module + optical interface 配对，S1） |
| 可观察字段 | 规范/标准文本中的 PMD 名、lane 配置、介质、reach；MSA application/profile 名；产品页的速率/lane/reach 标注。必须区分三类名字：IEEE PMD 名、MSA 扩展名、公司自定义 `+` 后缀（如 `800G-DR8+`，S5） |
| 不能回答什么 | 模块/引擎内部用哪种光子实现（TQ007）、DSP/retiming 放在哪里（TQ006）、光学相对 ASIC 放哪里（TQ008） |
| 来源基础 | S9（IEEE 802.3df-2024 定义 lane 配置、介质与 PMD reach）、S1（接口 profile 为规范主体）、S8（form factor 规范不定义内部实现） |

### 轴 2：电信号处理架构（TQ006）

| 要素 | 内容 |
|---|---|
| 它回答的问题 | retiming、FEC、均衡、DAC/ADC、DSP 分别放在 host 还是 module/engine？host-module 电接口是重定时传输还是线性模拟传输？ |
| 典型轴值（规范化） | `retimed`（链路内有 DSP 重定时，模块内 DSP 实例见 S3）、`linear`（模块内无 DSP，向 host 传递模拟信号，见 S1 §5）、`Tx-retimed-Rx-linear`（仅发射侧重定时，LRO 属此类族，见 S2/S3）、`direct-drive`（OIF framework 内候选，见 S7）等职责分配；host 侧以 DSP-based SerDes/FEC 承担处理（S1 §1） |
| 可观察字段 | 模块内是否含 DSP chip；FEC/retiming/DAC-ADC 位置；规范对 host-module electrical interface 的 linear/re-timed 描述；接口 profile 名（如 100G-DR-LPO）；披露的电架构术语（如 LRO） |
| 不能回答什么 | 光器件材料/平台、机械 form factor、链路 reach、BER 实测量级 |
| 特别排除 | `LPO` 不是本轴轴值；`低 BER 实现` 不是本轴轴值（S3 未披露电架构） |
| 来源基础 | S1、S2、S3、S7 |

### 轴 3：光子实现（TQ007，嵌套字段）

| 要素 | 内容 |
|---|---|
| 它回答的问题 | 怎样产生、调制、传输和探测光？光信号在光子层面如何被实现？ |
| 典型轴值（至少五类嵌套字段） | ① `platform/material`：SiPh（S4）、InP、GaAs 等；② `light source`：DFB 激光器（EML 内含，S6）、外置/片上集成激光器等；③ `modulator/emitter`：MZM（S5）、EAM（EML 内含，S6）、VCSEL 等；④ `detector`：PIN（S5）、APD 等；⑤ `integration`：PIC 单片集成（S4/S5）、混合集成、分立器件等 |
| 可观察字段 | PIC 平台名、激光器类型与位置、调制器/发射器件名、探测器类型、集成方式描述。EML 至少记录为 `light source + modulator` 器件级组合（InP DFB + EAM，S6），不得替代 platform 字段 |
| 不能回答什么 | 电路是否 retimed/linear（TQ006）、机械 form factor/放置位置（TQ008）、链路 reach（TQ005）。S6 明确 EML 不天然意味着 DSP、LPO、OSFP、CPO 或某 PMD/reach |
| 来源基础 | S4、S6、S5 |

### 轴 4：封装/放置架构（TQ008）

| 要素 | 内容 |
|---|---|
| 它回答的问题 | 光学相对 host ASIC 放在哪里？怎样电气/光学连接？能否现场更换或返工？ |
| 典型轴值 | `pluggable`（front-panel 可插拔，S8/S2）、`on-board / NPO`（near-package 安排，定义来源注明 S7）、`CPO`（光学与 host ASIC 位于同一 first-level substrate，S7）；其下再记录具体 form factor（OSFP、QSFP-DD 等，S8）与连接实现（socket/solder/pigtail，S7） |
| 可观察字段 | 模块/引擎位置；connector/cage 类型；attach 方式与 retention/rework 描述；form-factor MSA 名；OIF framework 中的位置参照（S7 §5、§7.2） |
| 不能回答什么 | 链路标准（TQ005）、光子平台（TQ007）、retimed/linear/direct-drive（TQ006）。CPO 不固定电架构（S7） |
| 来源基础 | S7、S8、S4 |

---

## 3. 术语归轴表

| 术语/词组 | 归轴 | 规范化/备注 |
|---|---|---|
| 800G / 1.6T / 8×200G / 8×100G / PAM4 | TQ005 | 总速率、lane 组织、调制格式字段 |
| DR8 / DR4 / FR8 / `800G-DR8+` | TQ005 | 链路族/PMD 画像；`+` 为公司自定义后缀（S5），不是 IEEE PMD 名 |
| SMF 500 m / 2 km / MMF | TQ005 | 介质与 reach（S9） |
| 1310 nm、并行/WDM 波长组织 | TQ005 | 波长组织字段 |
| 100G-DR-LPO interface profile | TQ005 | LPO MSA 定义的 host-module + optical interface 配对（S1） |
| `retimed / linear / Tx-retimed-Rx-linear / direct-drive` | TQ006 | 规范化电职责分配值（S1、S3、S7） |
| LRO / half-retimed | TQ006 | 仅发射侧重定时类实现（S2、S3）；术语边界统一留给 TQ006 |
| module DSP / 3 nm DSP | TQ006 | module 内处理芯片实例（S3） |
| **LPO** | **复合 alias**（TQ006 + TQ008 + TQ005） | = `linear` + `pluggable` + `LPO MSA profile`（S1、S2） |
| **低 BER 实现** | **不归轴** | 未分类公司演示注记（S3），不得作 TQ006 轴值 |
| **EML** | TQ007（light source + modulator 器件级） | InP DFB + 单片 EAM（S6） |
| **SiPh** | TQ007（platform/material） | 光子集成平台（S4） |
| MZM | TQ007（modulator） | S5 |
| VCSEL | TQ007（emitter，字典待扩） | 本包冻结来源未点名，归 TQ007 后续字典扩充 |
| PIN | TQ007（detector） | S5（EML/PD 组合） |
| pluggable | TQ008 | 放置大类（S1/S2/S8） |
| OSFP / QSFP-DD / QSFP-DD800 | TQ008（pluggable 下 form factor 字段） | 机械/电/热边界（S8；S5 中的 QSFP-DD800 实例） |
| NPO | TQ008 | 定义来源以 S7 为准；不假设全行业单一机械实现 |
| CPO | TQ008 | 光学与 host ASIC 同一 first-level substrate（S7）；不固定电架构 |

**为什么 EML/SiPh、DSP/LPO、pluggable/CPO 不能放在同一维度横向排名：**

1. **EML vs SiPh：粒度错层。** EML 是 InP DFB + 单片 EAM 的发射器件实现（S6），落在 `light source + modulator` 子字段；SiPh 是 PIC/集成平台（S4），落在 `platform/material` 子字段，且同一 SiPh 平台上光源/调制器/集成方式仍可变。二者没有共同轴；必须先写 platform，再写 light source/modulator。
2. **DSP vs LPO：对象错层。** DSP 是信号处理功能/芯片（属 TQ006 观察对象）；LPO 是 `linear + pluggable + LPO MSA profile` 的复合标签，同时含电架构、封装与接口 profile 三层信息。正确比较是 `retimed vs linear`（TQ006），封装与接口 profile 单列。
3. **pluggable vs CPO：粒度错层。** pluggable 是放置大类；CPO 是「与 host ASIC 位于同一 first-level substrate」的具体放置架构（S7）；OSFP/QSFP-DD 又只是 pluggable 下的机械 form factor（S8）。应先比 pluggable / NPO / CPO，再在 pluggable 下比 form factor。

---

## 4. 跨轴组合实例

| 保持相同/共享的字段 | 发生变化的字段 | 来源 | 最小结论 | 限定 |
|---|---|---|---|---|
| linear 电职责 + host DSP/FEC（LPO 系统） | form factor：QSFP / QSFP-DD / OSFP；多种 opto-electronic implementation | S1 §2、S2 | LPO 规范不固定机械 form factor，也不固定光子实现 | 规范示例，非量产/份额 |
| 1.6T-DR8 + OSFP + SiPh + 8×200G | LRO 与 3 nm DSP retimed 并存（另有低 BER 未分类） | S3 | 链路、形态、光子平台相同时，电架构仍可不同 | 公司演示，非量产/优劣 |
| `800G-DR8+` 链路族 | 光子实现：SiPh MZM PIC vs EML/PD；form factor：QSFP-DD800 vs OSFP | S5 | 同一链路目标可跨不同光子实现与不同 pluggable form factor 互操作 | 公司演示；`+` 为公司后缀 |
| 同一 SiPh 平台 | pluggable transceiver / co-packaged OCI chiplet / stand-alone on-board | S4 | 光子平台可进入不同封装位置，光子平台 ≠ 封装架构 | 公司平台资料；不代表所有 SiPh |
| OIF co-packaging framework 的放置问题域 | re-timed / linear / half-retimed / direct-drive 电接口候选 | S7 | CPO/NPO/pluggable 位置问题不固定电架构 | framework 层候选，非正式 IA/量产 |
| OSFP form factor 边界 | 内部实现为空（规范不规定 EML/SiPh/DSP/LPO） | S8 | form factor 与内部实现分离 | 规范只定义边界 |
| IEEE 802.3df-2024 链路配置（lane/media/reach） | 内部实现为空（标准不规定） | S9 | 链路标准轴与内部实现轴分离 | final-standard 摘要层 |

以上七组已满足「至少两组一手来源支持的跨轴组合实例」验收条件；它们只证明「至少存在这些观察组合」，不能扩张成完整笛卡尔积，未观察到的组合不作判断。

---

## 5. 原子主张（共 14 条，全部 draft-only）

- **TQ004-a2-d01**：技术路线必须写成链路/接口画像（TQ005）、电信号处理架构（TQ006）、光子实现（TQ007）、封装/放置架构（TQ008）四个分析轴的组合；任何单一轴值或单一术语（仅 SiPh、仅 LPO、仅 OSFP）不足以代表一条完整路线。来源：S1/S2/S3/S4/S5/S7/S8/S9 跨轴实例的组合；类型：分析抽象。`would_mark_covered: false`
- **TQ004-a2-d02**：「正交」只表示分析时必须分别回答这四个问题，不能用一个词替代另一个维度；不表示所有轴值可任意组合、可互操作或已具备量产经济性。来源：S1 §2、S2、S7 的限定表述；类型：分析抽象。`would_mark_covered: false`
- **TQ004-a2-d03**：TQ005 链路/接口画像轴回答「要互通的是什么链路」，可观察字段包括协议、总速率、host/media lane 数与 lane rate、调制格式、FEC/PMD、介质、reach 与波长组织；它给出外部互操作边界，不规定模块内部光子平台、电架构或封装位置。来源：S9、S8、S1；类型：规范事实 + 分析抽象。`would_mark_covered: false`
- **TQ004-a2-d04**：TQ006 电信号处理架构轴的规范化值为 `retimed / linear / Tx-retimed-Rx-linear / direct-drive` 等职责分配，可观察字段是 FEC、retiming、DAC/ADC、DSP 位于 host 还是 module/engine；该轴不回答光器件材料、机械 form factor 或链路 reach。来源：S1、S3、S7；类型：规范 + framework + 演示。`would_mark_covered: false`
- **TQ004-a2-d05**：LPO 是复合 alias，规范化表达为 `electrical_architecture=linear` + `packaging=pluggable` + `interface_profile=LPO MSA v1.2 (100G-DR-LPO)`；任何「DSP vs LPO」式比较都应改写为 retimed 与 linear 的电职责比较，再单列封装位置与接口 profile。来源：S1、S2；类型：分析抽象（由 MSA 文本归纳）。`would_mark_covered: false`
- **TQ004-a2-d06**：LPO MSA v1.2 明确规范 form-factor agnostic，QSFP、QSFP-DD、OSFP 只是示例，并允许多种 opto-electronic implementation approaches and technologies；FAQ 说明任何 pluggable form factor 都可用于 LPO。因此 LPO 不固定机械 form factor，也不固定 EML/SiPh/VCSEL 等光子实现。来源：S1 §2、S2；类型：MSA 规范事实。`would_mark_covered: false`
- **TQ004-a2-d07**：Coherent OFC 2025 演示中的「低 BER 实现」未披露电架构，只登记为未分类公司演示注记，不得作为 TQ006 轴值。来源：S3；类型：单公司演示受限事实。`would_mark_covered: false`
- **TQ004-a2-d08**：TQ007 光子实现轴必须嵌套记录 platform/material、light source、modulator/emitter、detector、integration 至少五类字段；同一平台（SiPh）之上光源/调制器/集成方式仍可变，而 EML 本身只是 light source + modulator 的器件级组合。来源：S4、S6；类型：分析抽象（基于器件定义与平台资料）。`would_mark_covered: false`
- **TQ004-a2-d09**：EML 与 SiPh 不是互斥同级枚举：EML = InP DFB laser + 单片集成 EAM，属发射器件实现（S6）；SiPh 是光子集成平台，可承载不同光源与调制器并进入不同封装形态（S4）。二者粒度不同，不得放在同一维度横向排名。来源：S6、S4；类型：器件定义 + 公司平台资料。`would_mark_covered: false`
- **TQ004-a2-d10**：TQ008 封装/放置架构轴回答光学相对 ASIC 的位置、连接方式与更换/返工边界；值域为 front-panel pluggable / on-board/NPO / CPO（光学与 host ASIC 位于同一 first-level substrate，定义以 S7 为准），其下再记录 OSFP/QSFP-DD 等 form factor 与 socket/solder/pigtail 等连接实现。该轴不回答链路标准、光子平台或电架构。来源：S7、S8、S4；类型：framework + 规范 + 公司平台资料。`would_mark_covered: false`
- **TQ004-a2-d11**：CPO 只归 TQ008，不固定电架构：OIF co-packaging framework 内同时区分 re-timed、linear、half-retimed、direct-drive 等电接口候选（S7），且同一 OSFP pluggable 形态内已观察到 LRO 与 DSP retimed 并存（S3）。来源：S7、S3；类型：framework + 演示。`would_mark_covered: false`
- **TQ004-a2-d12**：OSFP 是 front-panel pluggable 的机械/连接/供电/热/电接口 form factor（S8），CPO 是系统级放置架构（S7）；OSFP vs CPO 不是同级比较，应先比 pluggable / NPO / CPO，再在 pluggable 下比 OSFP / QSFP-DD。来源：S8、S7；类型：规范 + framework。`would_mark_covered: false`
- **TQ004-a2-d13**：已观察跨轴组合（仅限以下，不推所有组合）：(a) 固定 1.6T-DR8 + OSFP + SiPh + 8×200G 下 LRO 与 3 nm DSP retimed 并存（S3）；(b) 同一 `800G-DR8+` 链路族由 SiPh MZM PIC 的 QSFP-DD800 与 EML/PD 的 OSFP 实现并互操作（S5）；(c) 同一 SiPh 平台进入 pluggable、co-packaged（OCI chiplet）与 on-board 形态（S4）。这些组合足以否定若干普遍的一一映射，但不能推出所有轴值或所有组合成立。来源：S3、S5、S4；类型：公司演示/平台资料 + 受限推论。`would_mark_covered: false`
- **TQ004-a2-d14**：证据必须分层：IEEE final standard 摘要（S9）、form-factor MSA（S8）、LPO MSA 规范与官方 FAQ（S1/S2）、OIF framework（S7）、公司演示（S3/S5）、公司产品/器件页（S4/S6）属于不同证据层；公司演示与 framework 候选不得推出量产、主流、份额、成本或性能排序。来源：全部来源；类型：研究纪律（分析抽象）。`would_mark_covered: false`

---

## 6. 研究注记

1. **术语层级控制（本轮重点）**
   - EML/SiPh 错层处理：以 `platform/material` 与 `light source/modulator/detector` 两个嵌套层面记录，禁止直接互斥枚举。
   - LPO 复合标签：任何出现 LPO 的句子必须能拆回 `linear + pluggable + LPO MSA profile（注明 v1.2 / 100G-DR-LPO）`。
   - 「低 BER 实现」仅保留为 S3 未分类演示注记，不进入任何轴的枚举值。
2. **证据范围**：本文件只使用 `sources-tq004.md` 冻结的 S1–S9；source-discovery 中未冻结的 live URL（OIF Current Work、QSFP-DD Rev 7.1 等）不进入证据。
3. **分析抽象声明**：没有任何标准正式声明「行业共有四条正交轴」；四轴模型是 TQ004 的分析工具，必须保持该标签，不得当作既有规范事实。
4. **后续缺口挂接（只使用现有 QID）**
   - TQ005：冻结 link profile 最小字段集；区分 Ethernet PMD 名、MSA 扩展名与公司自定义 `+` 后缀。
   - TQ006：统一 retimed / linear / Tx-retimed-Rx-linear / direct-drive（及 LRO / RTLR / half-retimed）在 OIF、LPO MSA 与公司材料中的边界。
   - TQ007：将嵌套字段正式落为字典；补充 VCSEL 等发射器件与激光器位置的冻结来源。
   - TQ008：冻结 pluggable / on-board / NPO / CPO 的操作性定义与位置参照点；NPO 注明定义来源。
   - TQ009：路线画像须显式保存各轴字段与来源，复合词只作 alias。
   - TQ014：路线级功耗/成本/良率/密度排序，待 TQ009 路线画像形成后登记为依赖；本轮只登记、不回答。
   - WQ002/WQ003：轴间工程耦合的「某约束提高某组合价值」论证需要双侧证据，不能由本文件的轴分类关系直接推出。
   - PQ010：本轮不挂任何排序类缺口（按 attempt-2 §7，功耗/成本等不挂 PQ010）。
5. **状态标志**：`canonical_write_performed: false`；`coverage_status_changed: false`；`new_question_ids_created: false`。

---

## 7. 拒绝推论

1. 不得声称 EML、SiPh、LPO、CPO 互为完整替代路线。
2. 不得由「可组合」推出所有组合可量产、可互操作或经济可行。
3. 不得把同一家公司演示多个方案写成市场主流或份额。
4. 不得从轴定义直接推出受益公司。
5. 不得把 OIF framework、MSA specification、公司产品演示与 IEEE final standard 混成同一证据层。
6. 不得把 EML 与 SiPh、OSFP 与 CPO、DSP 与 LPO 直接横向排名（粒度/对象错层）。
7. 不得把「低 BER 实现」归为 TQ006 电架构值。
8. 不得写「每一轴值都与其他轴多个值共存」或「所有组合皆可行」的全称命题。
9. 不得由 OIF framework 的机械安排推出所有 CPO/NPO 已量产或已完成正式 IA。
10. 不得由链路标准（如 `800G-DR8+`）直接推出光子平台、电架构、封装位置或受益公司。
11. 路线级功耗/成本/良率/密度排序本轮不回答、不挂 PQ010。

---

## 8. 自检矩阵

| 合同条款 | 要求 | 本文件落实 |
|---|---|---|
| attempt-2 §1 | 四方向写为链路/接口画像、电信号处理架构、光子实现（嵌套）、封装/放置架构 | §2 四轴（符合） |
| attempt-2 §2 | 光子实现至少五类嵌套字段；EML 与 SiPh 不同粒度、禁止同级枚举 | §2 轴3、d08/d09、§3 归轴表（符合） |
| attempt-2 §3 | 电架构规范化值；LPO 为复合 alias、非纯电轴值 | §2 轴2、d04/d05/d06、§3 归轴表（符合） |
| attempt-2 §4 | CPO 只归 TQ008，不固定电架构 | §2 轴4、d10/d11（符合） |
| attempt-2 §5 | 「低 BER 实现」不归电架构 | d07、§3 归轴表「不归轴」（符合） |
| attempt-2 §6 | 跨轴结论只限已观察组合 | §4 限定、d13、拒绝推论 8（符合） |
| attempt-2 §7 | 功耗/成本/良率/密度排序挂 TQ014 依赖、不挂 PQ010 | 研究注记 4（符合） |
| attempt-2 §8 | 原子主张 ≤14、唯一 draft_id、`would_mark_covered: false` | §5 共 14 条（符合） |
| attempt-2 §9 | 仅允许现有 QID；不生成新 QID | 研究注记 4（符合） |
| 基础合同 §3.1 | 每轴写清问题、典型轴值、可观察字段、不能回答什么 | §2 四轴（符合） |
| 基础合同 §3.2 | 至少两组一手来源支持的跨轴实例 | §4 七组（符合） |
| 基础合同 §3.3 | 解释 EML/SiPh、DSP/LPO、pluggable/CPO 不能同维度排名 | §3 末三组解释（符合） |
| 基础合同 §3.4 | 区分规范/单产品/分析抽象/受限推论 | d14、研究注记 2/3（符合） |
| 基础合同 §3.5 | 缺口只挂现有 QID | 研究注记 4（符合） |
| 基础合同 §3.6 | 所有原子主张唯一 draft_id、`would_mark_covered: false` | §5（符合） |
| 基础合同 §4 | 禁止推论清单 | §7 全部未触发（符合） |
| 基础合同 §1 | 不写 canonical、不改覆盖、不生成新 QID | §9 停止结论（符合） |

---

## 9. 停止结论

TQ004 本轮 draft-only 收口完成：**轴字典 + 可比较规则**已建立，语义核心为「四个轴分开记录 + 复合标签拆回字段 + 只使用已观察组合」。

- `canonical_write_performed: false`
- `coverage_status_changed: false`
- `new_question_ids_created: false`

后续依赖已在现有 QID 挂接：TQ005–TQ009 字段冻结、TQ014 排序依赖、WQ002/WQ003 双侧证据；PQ010 本轮无挂接。

下一轮进入 TQ009 路线画像之前，必须执行的质量检查清单：**任何路线名字先拆字段、再归轴**，尤其是 LPO（拆回 linear + pluggable + LPO MSA profile）与 EML/SiPh（严格按嵌套字段分层）；凡无法归轴的标签一律只留作未分类注记。
