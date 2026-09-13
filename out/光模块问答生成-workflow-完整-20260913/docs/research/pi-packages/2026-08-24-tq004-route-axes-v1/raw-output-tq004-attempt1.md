# TQ004 研究产出：路线轴字典与可比较规则

- 研究包：`2026-08-24-tq004-route-axes-v1`
- 状态：`draft-only`；未落库；不写 canonical；不改 TQ004 覆盖状态；不生成新问题 ID
- 冻结来源：S1–S9（S1–S6 为本批新增；S7/S8/S9 复用自 2026-08-23 冻结包）

---

## 1. 结论摘要

1. **TQ004 的答案**：比较技术路线时，至少要分开四条正交选择轴——`TQ005 产品/链路标准轴`（速率、lane/波长组织、介质、PMD、reach 等外部互操作边界）、`TQ006 电接口架构轴`（retiming/CDR、linear equalization、FEC、DAC/ADC 等信号处理放在 host 还是模块）、`TQ007 光子平台轴`（光如何产生、调制、传输与探测）、`TQ008 封装架构轴`（光学相对 host ASIC 的位置与可维护/可返工边界）。一条"技术路线"必须写成四轴值的组合；单一术语（EML、LPO、CPO…）不构成完整路线（d06）。

2. **正交的含义**：只表示"分析时必须分别回答"，不代表轴值可任意组合、没有工程耦合（d05）。本批记录了 LPO↔pluggable 在本批证据内的共现、规范命名携带多轴值（如 `100G-DR-LPO`）、PMD 与光子平台存在工程适配面等耦合事实；耦合不取消轴区分，反而要求"先拆轴、再谈耦合"（§2.5）。

3. **一手来源给出六组跨轴实例**（§4）：固定三轴后电架构仍可变（S3）；固定光子平台后封装位置仍可多选（S4）；固定链路目标后光子平台与 form factor 可不同且可互操作（S5）；规范层 LPO 与 form factor/光子平台解耦（S1/S2）；EML 定义无跨轴预测力（S6）；规范命名本身携带多轴值（S1/S3/S5）。这六组实例共同支持：本批来源所见的轴之间不存在"一轴值决定另一轴值"的固定映射（d14）。

4. **不可横向排名**：EML/SiPh（TQ007）、DSP/LPO（TQ006）、pluggable/CPO（TQ008）分属不同轴、回答不同问题、处于不同证据层，不能放入同一维度横向排名；任何此类排名要么是类别错误，要么超出本批证据（缺量产、成本、份额、同口径实测）（d13–d16，§5）。

5. **本批边界**：23 条原子主张全部 draft-only（`would_mark_covered: false`）；不写 canonical；不改 TQ004 覆盖状态；不生成新 QID；研究缺口只挂合同允许集合 `TQ005–TQ009、PQ010、WQ002、WQ003`（d20–d23）。

### 可比较规则（C1–C5）

- **C1 对象规则**：可比较的最小对象是"四轴值组合"；只有单一轴值的术语（如"EML 路线"）不是可比较对象，只能作为某完整组合中的一轴值出现。
- **C2 同轴规则**：任何"谁更好"的比较必须先声明发生在哪条轴上；跨轴优劣比较（如"EML 与 LPO 谁好"）在本批证据下被拒绝。
- **C3 同层规则**：同一轴内比较时证据层必须一致（规范对规范、演示对演示）；跨证据层比较被拒绝（S1 规范不能裁定 S3 演示，反之亦然）。
- **C4 组合规则**：允许枚举轴值组合，但枚举 ≠ 可行性；引用任何组合时必须标注来源与证据层；不能由"可组合"推"可量产或经济可行"。
- **C5 实例范围规则**：由公司演示推出的可组合性只覆盖该演示对象（如 S3 的 1.6T-DR8 三变体、S5 的互操作对）；不推广到同平台全部产品，更不推出市场主流或份额。

---

## 2. 路线轴字典

> 四轴只回答"是什么/在哪里/哪个边界"，不回答"好不好"：功耗、成本、性能、份额是**评估指标**，不是轴值；本批冻结来源无这些量的同口径数据（d16）。

### 2.1 TQ005 产品/链路标准轴

- **回答的问题**：这条产品/链路对外承诺什么可互操作边界？在什么速率、lane/波长组织、介质、PMD、reach 下可与同标准设备对接？
- **典型轴值**：
  - 速率等级：100G（S1）、800G（S5、S9）、1.6T（S3）；
  - lane 组织：1×100G（S1）、8×100G（S5）、8×200G（S3）等；
  - 波长组织：DR/DR8 类并行波长体系（命名携带；本批不展开具体波长数值）；
  - 介质：SMF/MMF 等（S9 摘要定义介质类别；具体介质表不展开）；
  - PMD：DR、DR8+、FR/LR 等（S1、S5、S9）；
  - reach：由 PMD 定义的目标 reach（S9；数值不展开）。
- **可观察字段**：标准/规范中的 PMD 命名与 lane configuration 表述（S9）；规范名携带的链路信息（如 `100G-DR-LPO` 中的 DR，S1）；演示页自述的速率与 lane 组织（S3：1.6T-DR8、8×200G；S5：800G-DR8+）。
- **不能回答**：模块内部用何种光子器件/平台（S5：同一 800G-DR8+ 可由 SiPh 或 EML 实现）；电信号处理放 host 还是模块（S3：固定 1.6T-DR8 下 LRO/DSP 可变）；光学相对 ASIC 的位置（S9 不能支持内部实现）。
- **证据层**：以 IEEE final-standard 摘要（S9）、MSA 规范命名（S1）为规范层；S3/S5 的速率/lane 自述为公司演示层的 TQ005 信息。

### 2.2 TQ006 电接口架构轴

- **回答的问题**：电信号处理（retiming/CDR、linear equalization、FEC、DAC/ADC）放在 host 还是模块内？host-模块电接口上传的是重定时数字信号还是模拟信号？链路对端是相同还是不同的电架构？
- **典型轴值**：
  - DSP-retimed（模块内 DSP）：信号处理在模块内完成（S3 的 3 nm DSP 实现属此类演示）；
  - LPO：模块内不含 DSP chip（S2），收发方向传 analog 信号，FEC/retiming/DAC-ADC 位于 host，host 使用 DSP-based SerDes/FEC（S1 §1、§5）；
  - LRO：线性接收（其对端可为 LPO 或 retimed），S2 区分 LPO-to-LPO、LPO-to-retimed、LRO；
  - 其他实现变体：S3"低 BER 实现"（本快照未展开其电架构细节，仅记录存在）。
- **可观察字段**：规范文本中 FEC/retiming/DAC-ADC 所在侧的表述（S1 §5：host）；"linear/analog" vs "retimed" 术语（S1、S2）；模块内是否含 DSP chip 的表述（S2）；演示页对 LRO/DSP 变体的标注（S3）。
- **不能回答**：取哪个 form factor（S1 §2 form-factor agnostic）；取哪个光子平台（S1 §2 允许多种 opto-electronic implementation）；某 PMD/reach 的可行性；功耗/成本孰优（S2、S3 不能支持）。
- **证据层**：规范正文（S1）+ 官方 FAQ（S2）+ 演示标注（S3）。

### 2.3 TQ007 光子平台轴

- **回答的问题**：光在发射/接收两端如何产生、调制、传输与探测？器件/平台层级的实现是什么？
- **典型轴值**：
  - EML：InP DFB 激光器 + 单片集成 EAM（S6 官方定义）；外调制发射器件，接收侧配 PD（S5 的 EML/PD）；
  - SiPh：硅光 PIC，可含 MZM 调制结构与集成 PD（S4 平台页、S5 的 SiPh MZM PIC、S3 的 SiPh architecture）；
  - VCSEL：按本合同纪律归入本轴；本批冻结来源无其器件定义，不展开。
- **可观察字段**：器件定义页中的材料与单片集成结构（S6）；平台页中的 PIC 类型、调制方式与收发探测描述（S4）；演示页对收发器件/平台的标注（S3、S5）。
- **不能回答**：封装位置（S4：同一 SiPh 跨 pluggable/on-board/co-packaged；S5：SiPh 用 QSFP-DD800、EML 用 OSFP）；电架构（S3：SiPh 固定下 LRO/DSP 可变；S6：EML 定义不含 DSP/LPO）；PMD/reach（S6）；性能/成本/份额排序（S4/S5/S6 不能支持）。
- **证据层**：器件定义页（S6）、公司平台页（S4）、公司演示页（S3/S5）。

### 2.4 TQ008 封装架构轴

- **回答的问题**：光学（光引擎/PIC）相对 host ASIC 放在哪里？系统的可维护/可返工边界、供电热边界与连接边界在哪里？
- **典型轴值**：
  - pluggable：可插拔模块，位于面板/接口侧；OSFP（S8）、QSFP-DD、QSFP 等为 form factor 取值（S1 §2 列为例；S5 出现 QSFP-DD800 与 OSFP）；
  - on-board/NPO：光学在板上/近封装，但不与 ASIC 共封装（S4：OCI chiplet stand-alone on-board；S7 一并讨论 NPO）；
  - co-packaged/CPO：光学与 host ASIC 共封装（S4：OCI chiplet co-packaged with CPU/GPU；S7：OIF framework）。
- **可观察字段**：form-factor 规范中的机械/连接器/供电/热/电接口边界（S8）；framework 中的光引擎相对 ASIC 位置、CPA/substrate attach、EIC/OIC/PIC、光纤连接与可返工性表述（S7）；平台页的位置自述（S4）。
- **不能回答**：光子平台（S8 不能支持 OSFP 内部必须 EML/SiPh；S4 显示同一 SiPh 跨多位置）；电架构（S1 §2 form-factor agnostic；S8 不能支持必须 DSP/LPO）；链路标准（S8 不能支持 OSFP 决定 PMD/reach）；成熟度/经济性排序（S4 不能支持）。
- **证据层**：form-factor 规范（S8）、OIF framework 文档（S7）、公司平台页（S4）。

### 2.5 轴间耦合注记（正交与耦合并存）

- **(a) LPO↔pluggable 共现边界**：S1 §1 与 S2 在规范/官方解释层只把 LPO 定义为 pluggable 模块方案；同时 S1 §2 明示 form-factor agnostic。共现范围是"pluggable 大类内任意 form factor"，不是"任意封装位置"；LPO 在 on-board/CPO 形态是否有定义，不在本批证据内，不判定。
- **(b) 命名携带双轴值**：`100G-DR-LPO` 同时表达 TQ005（100G-DR）与 TQ006（LPO）；`800G-DR8+`、`1.6T-DR8` 携带速率与 lane/波长组织。规范命名系统需要两个轴才能完整描述对象，正说明分析时须拆开核对，不能按名词合并。
- **(c) PMD 与光子平台的适配面**：同一链路目标（S5）可由两种光子实现，说明适配不是唯一配对；耦合存在但不构成"固定配对"定律。
- **(d) 不同封装位置的边界由不同文档定义**：pluggable 的供电/热边界在 S8 form-factor 规范，CPO 的 attach/rework 边界在 S7 framework；TQ008 内不同取值的可观察字段口径不同，这是"不能把 OSFP 与 CPO 拼成同一条链条"的原因之一。
- 结论：正交=分析纪律，耦合=工程/证据现实；"正交=可自由组合"与"耦合=同义词"两种读法都被拒绝（d05、R13）。

---

## 3. 术语归轴表

| 术语/短语 | 归轴 | 词义层级（证据层） | 一句话定位 |
|---|---|---|---|
| EML | TQ007 | 器件定义（S6） | InP DFB + 单片集成 EAM 的发射器件；不蕴含其他三轴任何值 |
| SiPh | TQ007 | 公司平台描述（S4）+ 演示（S3/S5） | 硅光 PIC 平台；可含 MZM 调制与 PD 探测 |
| VCSEL | TQ007 | 合同纪律归轴（本批无冻结一手定义） | 属光子平台轴的值之一；本批不展开 |
| MZM | TQ007 | 演示层（S5） | SiPh 调制实现方式（SiPh MZM PIC） |
| EAM | TQ007 | 器件定义（S6） | EML 中单片集成的电吸收调制器 |
| PD（接收探测） | TQ007 | 演示层（S5 EML/PD） | 接收探测器件 |
| DSP-retimed（模块内 DSP） | TQ006 | 演示层（S3 3 nm DSP） | 信号处理放模块内的轴值 |
| LPO | TQ006 | 规范正文（S1）+ 官方解释（S2） | 模块无 DSP chip、电口传 analog、host 做 DSP/FEC/DAC/ADC |
| LRO | TQ006 | 官方解释（S2）+ 演示层（S3） | 线性接收（发射侧可 retimed）的轴值；链路对端可为 LPO 或 retimed |
| FEC/retiming/DAC/ADC 位置 | TQ006 | 规范正文（S1 §5） | "放 host"是 LPO 的可观察特征 |
| analog signals（电口） | TQ006 | 规范正文（S1 §5） | LPO 电信号形态的可观察字段 |
| pluggable | TQ008 | form-factor 规范（S8）+ MSA（S1 §2） | 光学以可插拔模块形态出现在面板/接口侧 |
| OSFP / QSFP-DD / QSFP | TQ008 | form-factor 规范（S8）+ MSA（S1 §2）+ 演示（S5） | pluggable 大类下的 form factor 取值 |
| on-board/NPO | TQ008 | 平台页（S4）+ framework（S7） | 光学在板上/近封装，不与 ASIC 共封装 |
| CPO / co-packaged | TQ008 | framework（S7）+ 平台页（S4） | 光学与 host ASIC 共封装的封装位置值 |
| CPA/substrate attach、solder/socket、pigtail、可返工性 | TQ008 | framework 层（S7） | co-packaging 的结构字段/可观察字段 |
| EIC/OIC/PIC | TQ008 | framework 层（S7） | co-packaging framework 的结构组成（本轴语境） |
| 速率（100G/800G/1.6T） | TQ005 | 规范层（S1/S9）+ 演示命名（S3/S5） | 链路速率等级 |
| lane 组织（8×100G、8×200G） | TQ005 | 规范层（S9）+ 演示命名（S3/S5） | lane 数与 lane 速率 |
| 波长组织（DR/DR8 体系） | TQ005 | 规范层（S1/S9）+ 演示命名（S3/S5） | DR 类命名携带的波长组织信息 |
| 介质（SMF/MMF 等） | TQ005 | 规范层（S9） | 介质类别 |
| PMD（DR/DR8+/FR/LR 等） | TQ005 | 规范层（S1/S9） | PMD 命名与 reach 目标 |
| reach | TQ005 | 规范层（S9） | 标称 reach 目标（数值不展开） |
| host-module electrical interface | TQ005×TQ006 接合面 | 规范正文（S1 §1） | TQ006 的电信号形态与 TQ005 的链路信令在同一接口定义中交织，分析时必须拆开 |
| optical interface | TQ005×TQ007 接合面 | 规范正文（S1 §1） | 携带 TQ005 的互操作边界，其物理实现落到某 TQ007 取值 |
| interoperability 互操作演示 | TQ005 的验证方式 | 演示层（S5） | 用于验证链路边界，不构成公司路线证据 |
| 低功耗/低成本主张（LPO FAQ） | 不属任何轴 | 官方解释层（S2） | 属待实测的量化主张；不是轴值，也不作排序依据 |

归轴纪律（合同"本轮分析纪律"原文映射）：`EML/SiPh/VCSEL`→TQ007；`DSP-retimed/LPO/LRO`→TQ006；`pluggable/on-board/NPO/CPO`→TQ008；`DR/FR、lane、wavelength、media、reach`→TQ005。

---

## 4. 跨轴组合实例

### 实例 1：同链路×同平台×同 form factor，电架构三变体（S3）

- **冻结来源**：S3 Coherent OFC 2025 官方演示页
- **固定轴**：TQ005=1.6T-DR8（8×200G optical/electrical interfaces）、TQ008=OSFP、TQ007=SiPh architecture
- **变化轴**：TQ006 ∈ {LRO，低 BER 实现，3 nm DSP 实现}
- **说明**：其余三轴固定后 TQ006 仍有可分辨变体；"低 BER 实现"的电架构细节未在本快照展开，但 LRO 与 3 nm DSP 的对立已足够支撑轴分离。
- **证据层**：公司单次官方演示。
- **受限范围**：不能推出三变体均已量产；不能推出 LRO/DSP 孰优；不能推出行业份额。

### 实例 2：同一 SiPh 平台跨三种封装位置（S4）

- **冻结来源**：S4 Intel Silicon Photonics 官方页
- **固定轴**：TQ007=SiPh（PIC 与 OCI chiplet 同平台描述）
- **变化轴**：TQ008 ∈ {pluggable transceivers, co-packaged with CPU/GPU, stand-alone on-board}
- **说明**：光子平台 ≠ 封装架构；同一平台描述横跨三位置。
- **证据层**：公司平台官方页（平台能力自述）。
- **受限范围**：不能推出所有 SiPh 均支持这三形态；不能推出三形态成熟度/经济性相同；不能由 Intel 平台页推出任何公司归群结论。

### 实例 3：同一链路目标，双光子平台×双 form factor 互操作（S5）

- **冻结来源**：S5 Coherent ECOC 2022 官方互操作演示
- **固定轴**：TQ005=800G-DR8+
- **变化轴**：TQ007 ∈ {SiPh MZM PIC, EML/PD}；TQ008 ∈ {QSFP-DD800, OSFP}
- **说明**：标准/链路轴固定时，光子平台与 form factor 均可不同且能互操作；TQ005 不决定 TQ007/TQ008。
- **证据层**：公司官方互操作演示（对端模块亦为演示对象）。
- **受限范围**：仅该互操作对被支持；不能推出 SiPh/EML 性能或成本排序；不能推出演示双方路线趋同或份额。

### 实例 4：规范层 LPO 与 form factor、光子平台解耦（S1/S2）

- **冻结来源**：S1 LPO MSA Spec v1.2、S2 LPO MSA FAQ（同源双侧使用，不是两份独立证据）
- **固定轴**：TQ006=LPO（模块内无 DSP chip、电口传 analog、host 侧 DSP/FEC/DAC/ADC）
- **变化轴**：TQ008 ∈ {QSFP, QSFP-DD, OSFP, …任意 pluggable form factor}；TQ007 ∈ 多种 opto-electronic implementation（规范未固定）
- **说明**：规范明示 form-factor agnostic 且允许多种光电子实现；"LPO"不等于某 form factor，也不等于某光子平台。
- **证据层**：MSA 规范正文 + MSA 官方 FAQ（规范/官方解释层）。
- **受限范围**：本批证据中 LPO 仅以 pluggable 形态被定义（§2.5a）；不覆盖 LPO-on-board/CPO 组合；FAQ 的功耗/成本主张不能替代同口径实测；不能推出全部组合已量产。

### 实例 5：单轴值（EML）无跨轴预测力——负向实例（S6）

- **冻结来源**：S6 Lumentum EML 官方产品技术页
- **固定轴**：TQ007=EML（InP DFB + 单片集成 EAM 的定义）
- **其余轴**：未被该来源决定——不蕴含 DSP/LPO（TQ006）、OSFP/CPO（TQ008）、某 PMD/reach（TQ005）
- **说明**：一条轴值成立，不等于其他轴任何值成立或成立；这是单轴值无跨轴预测力的负向可观察性实例。
- **证据层**：器件定义页。
- **受限范围**：只证明 EML 定义的信息边界，不证明 EML 的任何优劣。

### 实例 6：规范命名本身携带多轴值（S1/S3/S5）

- **冻结来源**：S1（`100G-DR-LPO`）、S5（`800G-DR8+`）、S3（`1.6T-DR8`）
- **说明**：`100G-DR-LPO` 同一名称内含 TQ005 值（100G-DR）与 TQ006 值（LPO）；`800G-DR8+`/`1.6T-DR8` 携带速率与 lane/波长组织。既然命名系统需要组合轴值才能完整描述一个规范对象，说明分析时须分别记录、不能省略任何一轴。
- **证据层**：规范命名/演示命名。
- **受限范围**：命名习惯不等于工程耦合定律；同一名称的双轴信息仍需回到规范正文核验。

---

## 5. 为什么 EML/SiPh、DSP/LPO、pluggable/CPO 不能同一维度横向排名

**论点 1：回答的问题不同（d13）。** EML/SiPh 回答"光如何产生、调制、探测"（TQ007）；DSP/LPO/LRO 回答"信号处理放在哪里、电口传什么信号"（TQ006）；pluggable/CPO 回答"光学相对 ASIC 放哪里、维护边界在哪"（TQ008）。把回答不同问题的名词放进同一条排名线，相当于比较"食材对烹饪方式对餐厅选址"，是类别错误。

**论点 2：来源中不存在"一轴值决定另一轴值"的固定映射（d14）。** S3（三轴固定后 TQ006 三变体）、S4（TQ007 固定后 TQ008 三位置）、S5（TQ005 固定后 TQ007×TQ008 双组合）、S1/S2（TQ006 固定后 TQ008/TQ007 自由）、S6（EML 定义对 TQ005/TQ006/TQ008 无预测力）。若两术语要在同一条排名线两端对阵，就必须存在"谁覆盖谁"的替代关系；这些实例显示的是"可独立取值"，不是"互相替代"。

**论点 3：证据层不同（d15）。** EML 来自器件定义页（S6），SiPh 来自公司平台页（S4），LPO 来自 MSA 规范+FAQ（S1/S2），CPO 来自 OIF framework（S7），OSFP 来自 form-factor 规范（S8），DR/FR 来自 IEEE PMD（S9）。跨层术语没有同一规范权威、同一统计口径、同一实测集合，不能同框排名，更不能把 OIF framework、MSA specification、产品演示与 IEEE final standard 混成同一证据层（合同禁止推论 5）。

**论点 4：排名需要的证据本批没有（d16）。** 横向排名至少需要同口径实测（功耗/时延/误码）、成本、成熟度（量产状态）、份额；每份来源的"不能支持"清单都排除这些。因此任何"EML 好于 SiPh""LPO 替代 DSP""CPO 替代 pluggable"的表述都是超证据层推论。

**若强行排名会发生什么**：产生伪替代关系（把 TQ007 值写成 TQ006 值的对手）；把"可组合"偷换为"可替换"；把某公司一次演示写成行业结论；把不同文档层级混成同一证据。

---

## 6. 原子主张

> 全部 23 条为 draft-only；`draft_id` 唯一；均含 `would_mark_covered: false`。

### 组 a1：轴定义与基本纪律

- `TQ004-a1-d01`（证据层：规范层与演示命名；would_mark_covered: false）TQ005 回答链路对外互操作边界（速率、lane/波长组织、介质、PMD、reach）；观察依据 S1（100G-DR）、S3（1.6T-DR8/8×200G）、S5（800G-DR8+）、S9（lane config/media/PMD reach）；不能回答内部光子平台、电架构、封装位置及优劣。
- `TQ004-a1-d02`（证据层：规范正文+官方 FAQ+演示标注；would_mark_covered: false）TQ006 回答电信号处理（retiming/CDR、linear equalization、FEC、DAC/ADC）放 host 还是模块、电口传数字还是模拟；取值含 DSP-retimed、LPO（S1/S2）、LRO（S2/S3）；不能回答 form factor、光子平台及优劣。
- `TQ004-a1-d03`（证据层：器件定义页/平台页/演示页；would_mark_covered: false）TQ007 回答光如何产生、调制、传输与探测；取值含 EML（S6：InP DFB+EAM）、SiPh（S4/S5）；VCSEL 按合同纪律归本轴，但本批无冻结一手来源定义其器件内容。
- `TQ004-a1-d04`（证据层：form-factor 规范+OIF framework+平台页；would_mark_covered: false）TQ008 回答光学相对 host ASIC 的位置与可维护/可返工边界；取值含 pluggable（OSFP/QSFP-DD/QSFP，S8/S5）、on-board/NPO（S4/S7）、co-packaged/CPO（S4/S7）；S7 的结构字段为光引擎位置、CPA/substrate attach、EIC/OIC/PIC、光纤连接与可返工性。
- `TQ004-a1-d05`（证据层：本合同定义；would_mark_covered: false）"正交"只表示分析时必须分别回答；不表示轴值可任意组合、没有工程耦合（合同 §2 末句）。
- `TQ004-a1-d06`（证据层：合同 §2 与分析纪律；would_mark_covered: false）一条具体技术路线 = 至少四轴值的组合；单一术语不构成完整路线；本批不构造完整路线画像。

### 组 a2：跨轴组合实例

- `TQ004-a2-d07`（证据层：公司演示 S3；would_mark_covered: false）固定 TQ005=1.6T-DR8（8×200G O/E）、TQ008=OSFP、TQ007=SiPh 后，TQ006 仍可取 LRO、低 BER、3 nm DSP 三值；TQ006 不被其余三轴决定。受限：三变体量产状态、孰优、份额均不支持。
- `TQ004-a2-d08`（证据层：公司平台页 S4；would_mark_covered: false）同一 SiPh 平台（TQ007 固定）被官方描述用于 pluggable transceivers、co-packaged with CPU/GPU、stand-alone on-board（TQ008 多值）；TQ007 ≠ TQ008。受限：三形态成熟度/经济性相同与否不支持。
- `TQ004-a2-d09`（证据层：公司互操作演示 S5；would_mark_covered: false）同一链路目标 800G-DR8+（TQ005 固定）由 SiPh MZM PIC+QSFP-DD800 与 EML/PD+OSFP 两种组合（TQ007×TQ008 不同）实现并互操作；TQ005 不决定 TQ007/TQ008。受限：仅该互操作对。
- `TQ004-a2-d10`（证据层：MSA 规范+FAQ S1/S2；would_mark_covered: false）LPO（TQ006 取 LPO 值）在规范层被明示 form-factor agnostic 且允许多种 opto-electronic implementation；TQ006 不等于 TQ008、不固定 TQ007。受限：本批仅定义 pluggable 形态下的 LPO。
- `TQ004-a2-d11`（证据层：器件定义页 S6；would_mark_covered: false）EML 定义（InP DFB+单片集成 EAM）只承载 TQ007 发射器件信息，不蕴含 DSP/LPO/OSFP/CPO 或某 PMD/reach；该轴值单独无跨轴预测力。
- `TQ004-a2-d12`（证据层：规范命名 S1/S3/S5；would_mark_covered: false）`100G-DR-LPO` 同一名称携带 TQ005 值（100G-DR）与 TQ006 值（LPO）；规范命名对象需要多轴值才能完整描述，分析时须分别记录。

### 组 a3：不可横向排名论证

- `TQ004-a3-d13`（证据层：合同 §2 各轴问题 + 本文轴字典；would_mark_covered: false）EML/SiPh、DSP/LPO、pluggable/CPO 分别回答 TQ007、TQ006、TQ008 三个不同问题；横向排名是类别错误。
- `TQ004-a3-d14`（证据层：S3/S4/S5/S1/S2/S6 综合；would_mark_covered: false）本批来源中每一轴值都可与另一轴多个值共存；不存在"一轴值决定另一轴值"的固定映射，因此不存在把两轴合并为一条排名线的依据。
- `TQ004-a3-d15`（证据层：来源层级分析；would_mark_covered: false）EML（器件定义）、SiPh（平台页）、LPO（MSA 规范+FAQ）、CPO（OIF framework）、OSFP（form-factor 规范）、DR/FR（IEEE PMD）处于不同证据层，无同一统计口径与权威，不能同维排名。
- `TQ004-a3-d16`（证据层：各来源"不能支持"清单；would_mark_covered: false）横向排名所需的同口径实测、成本、量产状态、份额数据在本批全部缺失；任何此类排名均为超证据层推论。

### 组 a4：证据层纪律

- `TQ004-a4-d17`（证据层：合同验收 4；would_mark_covered: false）本批证据层分五级：规范正文（S1/S8；S9 为 final-standard 摘要层、S7 为 framework 层）、官方解释（S2）、公司单产品或演示（S3/S5/S6；S4 为公司平台描述）、分析抽象（四轴框架本身）、受限推论（如 d09 仅覆盖该互操作对）；跨层混同被拒绝。
- `TQ004-a4-d18`（证据层：S2 自述；would_mark_covered: false）S2（FAQ）是 MSA 官方解释层，证据强度低于 S1（规范正文）；S2 的低功耗/低成本主张不能替代同口径实测。
- `TQ004-a4-d19`（证据层：合同 §4；would_mark_covered: false）合同 §4 五项禁止推论本批均未触发，且在"拒绝推论"节被显式拒绝。

### 组 a5：缺口与边界

- `TQ004-a5-d20`（证据层：来源覆盖范围；would_mark_covered: false）轴内枚举缺口：TQ005 的 1.6T lane/波长/PMD/reach 全表与数值；TQ006 的 LRO 规范正文边界与 S3"低 BER 实现"的电架构归类；TQ007 的 VCSEL 一手来源定义；TQ008 的 NPO/CPO 统一边界。分别挂 TQ005/TQ006/TQ007/TQ008，不新增 QID。
- `TQ004-a5-d21`（证据层：来源缺失；would_mark_covered: false）跨轴定量排序缺口（功耗/成本/良率/端口密度等量值）挂 PQ010（合同允许集合内；以既有 scope 为准）。插损/光学预算数值在上一批既有 PQ 系列归属（如已登记的插损/预算项）不再重复挂接。
- `TQ004-a5-d22`（证据层：耦合注记；would_mark_covered: false）轴间耦合的机制/因果解释缺口（如 LPO 为何在本批仅以 pluggable 形态被定义、PMD 与光子平台适配机制）挂 WQ002/WQ003（合同允许集合内；以既有 scope 为准），不新增 QID。
- `TQ004-a5-d23`（证据层：合同 §1；would_mark_covered: false）四轴组合成完整路线画像的合成规则本批明确不做，登记为缺口，挂 TQ009（合同允许集合内；以既有 scope 为准），不新增 QID。

---

## 7. 研究注记

1. **本批定位**：draft-only 研究包；合同 §1 只要求"轴字典 + 可比较规则"；本文所有内容不得视为 canonical 或覆盖证据。
2. **轴命名直接采用合同给定 QID**（TQ005–TQ008）；轴取值的描述只在本批冻结来源（S1–S9）范围内有效，不扩张到未冻结资料。
3. **正交与耦合并存**（§2.5）；四轴不回答"好不好"——功耗/成本/性能/份额是评估指标，不是轴值，本批无同口径数据。
4. **复用说明**：S7/S8/S9 来自 2026-08-23 冻结包；本批只在"术语归轴"限度内复用，不把 OIF framework、OSFP spec、IEEE 802.3df 摘要当作公司路线或市场证据。
5. **与上一批控制文本的边界**：上一批（2026-08-23 post-review effective text）已登记的 PQ 系列量化缺口（插损/光学预算/TX/RX/margin 数值）仍存在且已有归属；本批合同允许集合不含 PQ009，故不重复挂接；本批新增的跨轴定量缺口挂 PQ010（以既有 scope 为准）。本批不引用 PQ002/TQ002/WQ001 的实质结论作为 TQ004 轴定义依据。
6. **LPO↔pluggable 边界**：规范层只定义了 pluggable 形态下的 LPO（S1 §1、S2）；form-factor agnostic（S1 §2）只覆盖 pluggable 大类。LPO-on-board/CPO 不判定（§2.5a）。
7. **S3"低 BER 实现"** 未展开电架构细节，本批仅记录其作为第三变体存在，不将其归入 LPO/LRO/retimed 任一细分。
8. **VCSEL** 归轴来自合同纪律，本批无一手来源；后续如需 VCSEL 主张，须在 TQ007（或既有相关 QID）下补充冻结来源。
9. **实例只用于轴分离论证**，不构成完整路线画像（合同 §1）；实例中出现的公司（Coherent、Intel、Lumentum）只作为来源归属，不构成任何归群推论。S3 与 S5 同属 Coherent 但为不同年份/不同演示，不得合并为"Coherent 路线"；S1 与 S2 为同一 MSA 组织的规范+FAQ，是同源双侧使用，不是两份独立证据。

### 来源×证据层索引

| 来源 | 层级 | 本批用途 |
|---|---|---|
| S1 LPO MSA Spec v1.2 | 规范正文 | TQ006 定义、TQ005 命名（100G-DR）、form-factor agnostic（TQ008 解耦）、host 端 DSP/FEC/DAC/ADC |
| S2 LPO MSA FAQ | 官方解释 | LPO 无 DSP chip、LPO-to-LPO/LPO-to-retimed/LRO、任意 pluggable form factor |
| S3 Coherent OFC 2025 | 公司演示 | 三轴固定后 TQ006 三变体 |
| S4 Intel SiPh 官方页 | 公司平台描述 | TQ007 固定后 TQ008 三位置 |
| S5 Coherent ECOC 2022 | 公司互操作演示 | TQ005 固定后 TQ007×TQ008 双组合互操作 |
| S6 Lumentum EML 页 | 器件定义 | EML 定义边界（无跨轴预测力） |
| S7 OIF Co-Packaging FD | framework 文档 | TQ008 结构字段（位置、attach、可返工性；含 NPO） |
| S8 OSFP Spec Rev5.22 | form-factor 规范 | TQ008=pluggable 的机械/连接器/供电/热/电接口边界 |
| S9 IEEE 802.3df-2024 摘要 | final-standard 摘要层 | TQ005 互操作边界（lane config/media/PMD reach） |

---

## 8. 拒绝推论

- **R0（合同级）**：本批不回答路线胜负、公司归群、市场份额；不构造完整路线画像（合同 §1）。
- **R1**：拒绝"EML、SiPh、LPO、CPO 互为完整替代路线"。依据：合同禁止推论 1；它们分属 TQ007/TQ006/TQ008，非同一轴上的替代项（d13、d14）。
- **R2**：拒绝"可组合 → 所有组合均可量产或经济可行"。依据：合同禁止推论 2；C4；S1/S3/S5 无量产/成本证据。
- **R3**：拒绝"同一家公司演示多个方案 → 市场主流或份额"。依据：合同禁止推论 3；S3/S5 是演示页。
- **R4**：拒绝"由轴定义直接推出受益公司"。依据：合同禁止推论 4；轴是分析抽象。
- **R5**：拒绝"把 OIF framework、MSA specification、产品演示与 IEEE final standard 混成同一证据层"。依据：合同禁止推论 5；d17。
- **R6**：拒绝"LPO 规范/FAQ 的低功耗低成本主张作为排序依据"。依据：S2 不能支持；需同口径实测。
- **R7**：拒绝"LPO=form factor 或 LPO=pluggable 的唯一正确电架构"。依据：S1 §2 form-factor agnostic；S8 不决定内部实现。
- **R8**：拒绝"OSFP 内部必须是 EML、SiPh、DSP 或 LPO"。依据：S8 不能支持。
- **R9**：拒绝"EML 天然意味着 DSP、LPO、OSFP、CPO 或某 PMD/reach"。依据：S6 不能支持。
- **R10**：拒绝"互操作演示 → 两方路线趋同或份额"。依据：S5 不能支持。
- **R11**：拒绝"所有 SiPh 均支持 pluggable+on-board+co-packaged 三形态且成熟度相同"。依据：S4 不能支持。
- **R12**：拒绝"OFC 三变体均已量产、LRO/DSP 孰优、行业份额"。依据：S3 不能支持。
- **R13**：拒绝"正交=可任意组合"与"耦合=同轴/同义词"两个方向的读法。依据：合同 §2 末句、§2.5。

---

## 9. 自检矩阵

### 表 A：验收条件自检（合同 §3）

| 验收条件 | 要求 | 本批对应 | 状态 |
|---|---|---|---|
| §3.1 | 每轴写清问题/轴值/可观察字段/不能回答 | §2.1–2.4 四节各含四要素 | ✅ |
| §3.2 | ≥2 组一手来源支持的跨轴实例 | §4 实例 1–6（对应 d07–d12，共 6 组） | ✅ |
| §3.3 | 解释 EML/SiPh、DSP/LPO、pluggable/CPO 不可同维排名 | §5（对应 d13–d16） | ✅ |
| §3.4 | 区分标准/规范、公司产品/演示、分析抽象、受限推论 | §7 来源×证据层表（对应 d17） | ✅ |
| §3.5 | 缺口只挂 TQ005–TQ009、PQ010、WQ002、WQ003，不创新 QID | d20–d23 挂接集合 ⊆ 允许集；未触及其它 QID | ✅ |
| §3.6 | 原子主张唯一 draft_id + would_mark_covered: false | d01–d23 唯一且全部含标记 | ✅ |

### 表 B：禁止推论自检（合同 §4）

| 禁止项 | 本批处置 |
|---|---|
| 1. EML/SiPh/LPO/CPO 互为完整替代路线 | 未出现；R1 显式拒绝 |
| 2. 可组合 → 可量产/经济可行 | 未出现；C4、R2 显式拒绝 |
| 3. 公司演示多方案 → 主流/份额 | 未出现；R3 与实例受限范围显式拒绝 |
| 4. 轴定义 → 受益公司 | 未出现；R4 显式拒绝 |
| 5. 证据层混同 | 未出现；d17、R5 显式拒绝 |

### 表 C：目标边界自检（合同 §1）

| 不做的事项 | 本批状态 |
|---|---|
| 路线胜负 | 未回答（R0） |
| 公司归群 | 未回答；S4/S5 仅作实例不作归群 |
| 市场份额 | 未涉及（各来源不能支持） |
| 完整路线画像 | 未构造（d06；d23 登记为缺口） |
| 写 canonical / 改覆盖 / 新 QID | 停止结论全 false |

---

## 10. 停止结论

- **唯一产出**：TQ004 的"路线轴字典"（§2）与"可比较规则"（§1 C1–C5），及其支撑的 23 条 draft 原子主张（d01–d23）。
- `canonical_write_performed: false`
- `coverage_status_changed: false`（TQ004 覆盖状态未改变）
- `new_question_ids_created: false`
- 所有原子主张 draft-only，`would_mark_covered: false`。

### 遗留缺口（仅挂合同允许集合，不新增 QID）

- **TQ005**：1.6T lane/波长/PMD/reach 全表与数值；
- **TQ006**：LRO 规范正文边界、S3"低 BER 实现"的电架构归类；
- **TQ007**：VCSEL 一手来源定义；
- **TQ008**：NPO/CPO 统一边界、LPO 非 pluggable 形态的覆盖问题；
- **TQ009**：四轴组合成完整路线画像的合成规则（候选挂接，以既有 scope 为准）；
- **PQ010**：跨轴定量排序量值（功耗/成本/良率/端口密度；候选挂接，以既有 scope 为准）；
- **WQ002/WQ003**：轴间耦合的机制/因果解释（候选挂接，以既有 scope 为准）。

**停止理由**：合同唯一目标（轴字典 + 可比较规则）已达成；路线胜负、市场份额、公司归群、完整路线画像均不在本轮授权范围，且所需证据（量产、成本、同口径实测、份额数据）未在本批冻结来源中出现。
