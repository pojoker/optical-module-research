# WQ001 attempt-2 收口稿（draft-only）

## 1. 结论摘要

本稿为 WQ001 attempt-2 收口稿：继承 `contract-wq001.md`，执行 `contract-wq001-attempt2.md`；只消费经 Codex 最终裁决的 `raw-output-tq002-attempt3.md`＋`adjudication-tq002-final.md` 与 `raw-output-pq002-attempt3.md`＋`adjudication-pq002-final.md` 及其冻结来源。

**对目标问题的机制性回答**：系统需求不会凭空“变成”物理约束。需求的验证只能落在物理层，因此场景参数必须经标准结构映射到可测量的约束集合——这是需求“变成”物理约束的结构性原因。在两套知识体系（route 体系 TQ002、physical 体系 PQ002）之间存在一层由标准/规范结构定义的“接口/链路约束层”：IEEE 802.3df-2024 的 lane 与 per-PMD 结构、OSFP Rev 5.22 的 power class、OIF CPF 的 engine-to-substrate 装配与 media-side 连接形态、CMIS 的 Host/Media 条件化接口骨架。route 侧按场景定义需求参数（带宽、距离、功耗、密度、维护），physical 侧以 lane 数／lane 速率／接口容量、介质与 PMD 联合定义、module power class 与 thermal 验证边界、拆卸/返工/现场 access 等机制承载，最终落到可观察指标。该转换是规范结构支持的结构映射，不是被直接证实的事实因果；因此每条候选关系都标注强度（直接证实／规范结构支持／受限推论），且只在证据足够处输出。

**本轮结果**：共形成五条 draft-only 候选关系，全部 `would_mark_covered: false`：

| 候选关系 | 关系强度 |
|---|---|
| B1 带宽 → host/media lane 与接口容量 | 规范结构支持（含单产品实例） |
| B2 距离/连接位置 → media 与 optical-budget | 受限推论（数值待 PQ009 验证） |
| B3 功耗 → module/host power 与 thermal-validation 边界 | 规范结构支持（CPO 侧仅框架目标语言） |
| B4 密度 → port configuration 与 physical footprint | 规范结构支持（单源双读，非独立证实） |
| B5 维护 → removability/rework/access | 规范结构支持（事实层；成本影响未闭合） |

**勘误吸收（继承 attempt 1）**：① PQ002 最终裁决对 `PQ002-a3-d01` 的有效勘误——全文改读为“本轮采用的 CMIS 条件化接口骨架”，不使用“唯一核心功能骨架”；② TQ002 最终裁决对 `TQ002-a3-d08` 的有效勘误——`hot-pluggable` 是产品/form-factor 能力、`hot-plug/hot-unplug` 是规范纳入处理的功耗瞬态事件，二者分开且均不能直接证明维护成本下降；“机架内/DC/园区”等部署分段标签仅作阅读提示，非冻结来源给出的标准部署分类。

**空缺**：成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值、ports/RU 单位面积密度等保持空缺；PQ009 仅作为 optical-budget 的待验证问题，未宣称已回答。全文无任何 EML/SiPh/LPO/CPO 路线、公司归群或份额结论。

## 2. 桥接关系表

| 候选关系（draft_id） | 关系类型 | route-side 需求证据 | physical-side 机制证据 | 关系强度 | 固定链条（场景需求→接口/链路约束→物理机制→可观察指标） | 状态 |
|---|---|---|---|---|---|---|
| B1 带宽→host/media lane 与接口容量（WQ001-a2-b01） | need_to_constraint | TQ002-a3-d01／d04（IEEE 802.3df-2024 x8 与 lane 配置；单产品 850 Gb/s、8×100G PAM4） | PQ002-a3-d01／d04／d05（CMIS 条件化接口骨架的 Host/Media Interface 方向；逐 lane 电/光收发与 EML/PIN 单实例） | 规范结构支持（含单产品实例） | 端口吞吐/lane 拆分 → x8 lane 结构与逐 lane PAM4 Host/Media 接口 → 逐 lane 电→光→电收发机制 → aggregate rate、lane 数/速率、接口容量 | draft-only 候选 |
| B2 距离/连接位置→media 与 optical-budget（WQ001-a2-b02） | need_to_constraint | TQ002-a3-d02（per-PMD 标称 reach，reach 与介质/PMD 联合定义） | PQ002-a3-d07（OIF CPF §7.3.4：mid-board optical connector 增加 optical budget，TX power／RX sensitivity／margin 方向） | 受限推论（数值待 PQ009 验证） | 部署分段 reach/连接路径 → 介质与 PMD 联合定义、connector 路径 → optical-budget 增减机制 → 介质、插损、TX power、RX sensitivity、PMD reach | draft-only 候选 |
| B3 功耗→module/host power 与 thermal-validation 边界（WQ001-a2-b03） | need_to_constraint | TQ002-a3-d03／d05（form-factor power class 与 CPO power-savings target 分层） | OSFP Rev 5.22 §15.8（经 TQ002-a3-d03）；PQ002-a3-d08（edge connector 供电/地物理路径分层）；PQ001 module/host 条件边界（按冻结包标注） | 规范结构支持（CPO 侧仅框架目标语言） | power class/target 分层 → power class、host 启用前读取、热插拔瞬态 → 系统级 thermal design/validation、耗电路径、缩短电通道降损耗目标 → power class、功耗模式、产品 dissipation、thermal 验证边界 | draft-only 候选 |
| B4 密度→port configuration 与 physical footprint（WQ001-a2-b04） | need_to_constraint | TQ002-a3-d06（port lane 灵活性与 substrate footprint 两层输入） | 冻结 OIF CPF §7.2.1/Table 4（engine-to-substrate 装配层；PQ002 裁决仅用于该层属确认） | 规范结构支持（单源双读，非独立证实） | 端口拆分与 substrate 面积需求 → lane 配置、socket/solder footprint 权衡 → engine-to-substrate 装配：retention 占位、solder reflow 返工/yield → 占位、密度/yield、lane 配置项数 | draft-only 候选 |
| B5 维护→removability/rework/access（WQ001-a2-b05） | need_to_constraint | TQ002-a3-d08（hot-pluggable 事实层与 lifecycle-cost gap 分层） | PQ002-a3-d04（Coherent hot-pluggable OSFP 实例）；OIF CPF §7.2.1/Table 4（solder reflow 返工/yield loss、socket 返工与现场 access 限制） | 规范结构支持（事实层；成本影响未闭合） | 服务方式需求（现场可插拔 vs 受限） → hot-pluggable 能力、hot-plug/unplug 瞬态事件分开、socket/solder 返工属性 → 可热拔插连接器、solder reflow 返工/yield、socket 现场 access → 是否 hot-pluggable、返工方式、现场 access 限制、repairability 单列 | draft-only 候选 |

## 3. 关系草案

### WQ001-a2-b01（B1：带宽需求 → host/media lane 与接口容量约束）

**draft_id**：WQ001-a2-b01
**relation_type**：need_to_constraint
**strength**：规范结构支持（含单产品实例）——标准与实例支持映射结构，不能直接证明普遍因果；依合同不得写“直接证实”。
**route_side_evidence**：TQ002-a3-d01（IEEE 802.3df-2024 下 800 Gb/s 一个八 lane port 可配置为 1×8/2×4/4×2/8×1）、TQ002-a3-d04（单产品 850 Gb/s aggregate、8×100G PAM4 retimed 电接口）
**physical_side_evidence**：PQ002-a3-d01（CMIS 条件化接口骨架：Host Interface 上 host→module 为 transmitter input、module→host 为 receiver output，Media Interface 上 module→media 为 transmitter output、media→module 为 receiver input）、PQ002-a3-d04／d05（逐 lane 电→光→电收发链；TX=EML、RX=PIN 仅为该料号实例）
**chain（场景需求 → 接口/链路约束 → 物理机制 → 可观察指标）**：

1. 场景需求：按端口吞吐与 lane 拆分选择 1×8/2×4/4×2/8×1；单产品实例需 850 Gb/s aggregate。
2. 接口/链路约束：IEEE 802.3df-2024 下 800 Gb/s 的一个八 lane port lane 结构；CMIS 条件化接口骨架的 Host/Media Interface 方向；单产品 Host Interface 为 8×100G PAM4 retimed 电接口。
3. 物理机制：逐 lane PAM4 调制下，发送端电→光转换经 Media Interface 进入 media、接收端光→电转换回 host；该料号 TX=EML、RX=PIN 仅为单产品实例机制，不构成行业结构。
4. 可观察指标：aggregate rate（850 Gb/s）、lane 数（8）、lane 速率（100G PAM4/lane）、Host/Media interface capacity。

**statement**：更高 aggregate rate 在本轮实例中落实为 lane 数、lane 速率与 Host/Media interface capacity 的组合约束；IEEE 802.3df-2024 的 x8 结构与单产品 8×100G PAM4 实例共同支持这一映射结构。
**boundary**：仅覆盖标准接口组合与单产品实例；不涉及模块内部完整连线/BOM；不涉及光子平台选择。
**rejected_inference**：普遍必须增加 lane；x8 必然优于 x4；必选某光子平台（EML/SiPh/LPO/CPO）。
**would_mark_covered**：false

### WQ001-a2-b02（B2：距离/连接位置 → media 与 optical-budget 约束）

**draft_id**：WQ001-a2-b02
**relation_type**：need_to_constraint
**strength**：受限推论——介质/PMD 联合定义部分有规范结构支持（IEEE 802.3df per-PMD 标称 reach），但连接器路径→optical-budget 的机制来自 OIF CPF §7.3.4 的条件性框架文本，无量值闭合；本桥不把受限推论伪装成事实。
**route_side_evidence**：TQ002-a3-d02（final-standard 层距离口径为 per-PMD 标称 reach，reach 必须与介质/PMD 联合定义；产品层存在 500 m SMF 实例）
**physical_side_evidence**：PQ002-a3-d07（CPO media-side 连接形态：pigtail／built-in connector／mid-board optical connector；OIF CPF §7.3.4 的 optical-budget 增减机制）
**chain（场景需求 → 接口/链路约束 → 物理机制 → 可观察指标）**：

1. 场景需求：按部署分段选择介质与 reach（部署分段标签仅作阅读提示，非冻结来源给出的标准部署分类）。
2. 接口/链路约束：per-PMD 标称 reach（MMF 50/100 m、SMF 500 m/2 km）；连接器路径/位置（如 mid-board optical connector 形态）。
3. 物理机制：mid-board optical connector 增加 optical budget；TX 侧可能需提高 transmit power，RX 侧可能需改善 sensitivity 或减少 margin。
4. 可观察指标：介质类别、插损、TX power、RX sensitivity、PMD 标称 reach。

**statement**：距离与连接器路径要求会转化为介质、插损、发射功率/接收灵敏度等可验证约束；其中 optical-budget 数值标为待 PQ009 验证项，本桥不宣称 PQ009 已回答。
**boundary**：只使用 final-standard 的 per-PMD 口径；历史 objectives（如 10/40 km 单纤方向、copper 1/2 m）不入桥接证据；不写某 reach 必须采用某器件。
**rejected_inference**：某 reach 必须采用某器件；connector 数直接决定路线；reach 标准名称→制造成本排序；单产品 500 m SMF 实例代表全部 800G。
**would_mark_covered**：false

### WQ001-a2-b03（B3：功耗约束 → module/host power 与 thermal-validation 边界）

**draft_id**：WQ001-a2-b03
**relation_type**：need_to_constraint
**strength**：规范结构支持——OSFP Rev 5.22 §15.8 直接机制化为 power class 与系统级 thermal design/validation 边界；CPO 侧仅为框架 expected/target 目标语言，不构成实测支持。
**route_side_evidence**：TQ002-a3-d03（form-factor 层 power class、低/高功耗模式、host 启用前读取、hot-plug/hot-unplug 功耗瞬态事件）、TQ002-a3-d05（CPO power-savings target 分层）
**physical_side_evidence**：PQ002-a3-d08（OSFP edge connector 供电/地物理路径与 mission data path 分层）；PQ001 的 module/host 条件边界（按冻结桥接来源包 B3 标注，仅作边界引用，本包不消费 PQ001 草案正文）；OSFP Rev 5.22 §15.8（经 TQ002-a3-d03 挂接的冻结规范）
**chain（场景需求 → 接口/链路约束 → 物理机制 → 可观察指标）**：

1. 场景需求：form-factor 层 power class 与 CPO power-savings target 分层。
2. 接口/链路约束：power classes、低/高功耗模式，host 在启用高功耗前读取 module power class；hot-plug/hot-unplug 是规范纳入处理的功耗瞬态事件（勘误吸收：hot-pluggable 能力与瞬态事件分开）。
3. 物理机制：系统级 thermal design/validation 边界；OSFP edge connector 的供电/地物理路径；module/host 条件边界（PQ001 标注）；CPO 框架机制目标为缩短高速电通道以降低损耗。
4. 可观察指标：power class、低/高功耗模式、产品 dissipation（单实例 <17 W）、系统 thermal 验证边界。

**statement**：功耗上限在 OSFP 实例中变成 module power class、host enable 与系统级 thermal design/validation 边界；CPO 在框架层只提供缩短电通道以降低损耗的机制目标，非实测结果。
**boundary**：power class 是热设计约束而非具体模块实测功耗；<17 W 为单产品 dissipation 实例，非行业通值。
**rejected_inference**：CPO 实测一定更低功耗；power class 等于产品实际功耗；<17 W 为所有 OSFP/DR8 通值。
**would_mark_covered**：false

### WQ001-a2-b04（B4：密度需求 → port configuration 与 physical footprint 约束）

**draft_id**：WQ001-a2-b04
**relation_type**：need_to_constraint
**strength**：规范结构支持（单源双读，非独立证实）——route-side 与 physical-side 引用同一份冻结 OIF CPF 来源的不同内容，不构成两份独立证据。
**route_side_evidence**：TQ002-a3-d06（port lane 灵活性（1×8/2×4/4×2/8×1）与 substrate footprint 两层输入，socket/solder 的密度与返工权衡）
**physical_side_evidence**：冻结 OIF CPF §7.2.1/Table 4（engine size、retention mechanism、solder/socket 占位与返工；经 `adjudication-pq002-final` 确认属 engine-to-substrate 物理装配层，不是 Media Interface；PQ002 裁决仅用于该层属确认）
**chain（场景需求 → 接口/链路约束 → 物理机制 → 可观察指标）**：

1. 场景需求：端口 lane 拆分需求与 substrate 面积/可返工需求分层取舍。
2. 接口/链路约束：lane 配置提供 port 层灵活性；removable socket retention mechanism 占面积并限制密度；solder reflow footprint 密度高但 rework 受限且有 yield loss。
3. 物理机制：engine-to-CPA-substrate 装配层——engine size、retention mechanism、solder/socket 占位与返工/yield 限制。
4. 可观察指标：socket retention 占位、solder reflow 密度与 yield、lane 配置项数。

**statement**：密度要求进入端口配置与封装占位/retention 的物理设计约束。route-side 需求来自 TQ002；physical-side 机制来自同一份冻结 OIF §7.2.1/Table 4 的 engine-to-substrate 装配内容；两侧使用该来源的不同内容，不是两份独立证据。
**boundary**：不换算 ports/RU 单位面积数值；不由密度直接选定 solder/socket 或路线；Table 4 非市场成本数据。
**rejected_inference**：lane 配置→ports/RU 数值；socket 或 solder reflow 整体胜出；由密度直接选定路线。
**would_mark_covered**：false

### WQ001-a2-b05（B5：维护需求 → removability/rework/access 约束）

**draft_id**：WQ001-a2-b05
**relation_type**：need_to_constraint
**strength**：规范结构支持（事实层）——属性映射停留在事实层（是否可热插拔、可返工、现场 access 限制）；成本影响无数值证据，未闭合。
**route_side_evidence**：TQ002-a3-d08（hot-pluggable 事实层与 lifecycle-cost gap 分层；socket 可 rework 但现场 access 受限；connector 未固定属规范/接口开放项）
**physical_side_evidence**：PQ002-a3-d04（Coherent FTCE4517E1PxM 为 hot-pluggable OSFP 的可热拔插连接器实例）；冻结 OIF CPF §7.2.1/Table 4（solder reflow 返工受限与 yield loss、socket 返工与现场 access 限制；经 PQ002-a3-d07 boundary 与 TQ002-a3-d08 读同一来源）
**chain（场景需求 → 接口/链路约束 → 物理机制 → 可观察指标）**：

1. 场景需求：按服务方式需求分场景记录：现场可插拔 vs rework/access 受限。
2. 接口/链路约束：hot-pluggable 是产品/form-factor 能力；hot-plug/hot-unplug 是规范纳入处理的功耗瞬态事件；二者分开、均不证明维护成本下降（勘误吸收）；socket/solder 决定可返工性与现场 access。
3. 物理机制：可热拔插连接器能力实例；solder reflow 金属装配返工受限与 yield loss；socket 提供返工点与现场 access。
4. 可观察指标：是否 hot-pluggable、rework 方式、现场 access 限制、repairability 是否单列。

**statement**：维护需求可映射到是否可热插拔、是否可返工、现场 access 等物理属性；本桥不含“管理/供电路径分层使热插拔可作为服务事件独立处理”推论，也不含维护成本下降结论（该层无数值证据，未闭合）。
**boundary**：连接器位置/实现未固定 ≠ 服务方式未定；全生命周期成本高低不由此桥推出。
**rejected_inference**：hot-plug 必然降低成本；所有 CPO 不可维护；connector 未固定⇒服务方式未定（或已排除）；管理/供电路径分层⇒服务事件可独立处理。
**would_mark_covered**：false

## 4. 未桥接项

| # | 未桥接项 | 保留原因 | 处理 |
|---|---|---|---|
| 1 | 成本金额（模块价格、维护费用、路线成本排序） | 只有维度清单（IEEE P802.3df CSD，Economic Feasibility），无物理量化机制与公开金额 | 空缺，不补写 |
| 2 | 维护成本定量（hot-plug ⇒ 维护成本更低） | 无数值证据链 | 空缺；B5 只停留在事实层 |
| 3 | CPO 实测功耗/功率节省 | OIF 为 expected/target 语言，无实测报告 | 空缺；B3 只写框架目标 |
| 4 | optical-budget 数值（插损、TX power、RX sensitivity、margin 具体值） | OIF CPF §7.3.4 只给方向性机制 | 标为待 PQ009 验证；不宣称已回答 |
| 5 | ports/RU 单位面积部署密度数值 | 只有 lane 配置与 substrate tradeoff | 空缺；B4 不换算 |
| 6 | 铜缆 reach 数值、10/40 km 单纤方向覆盖 | IEEE 802.3df-2024 摘要未展开；历史 objectives 不入桥接证据 | 空缺；待 final 文本核验 |
| 7 | “机架内/DC/园区”部署分类 | 仅阅读提示，非冻结来源给出的标准部署分类（勘误吸收） | 不进入桥接证据 |

## 5. 拒绝的推论

| # | 被拒绝的推论 | 拒绝理由 | 依据 |
|---|---|---|---|
| 1 | 任一桥 → EML/SiPh/LPO/CPO 路线选择 | 本包只建立需求与约束之间的关系，不回答路线选择 | contract-wq001.md §3；TQ002-a3-d10 范围声明 |
| 2 | 路线选择 → 公司受益/归群/份额 | 超出 need_to_constraint 关系类型；无冻结证据 | contract-wq001.md §3 |
| 3 | 普遍必须增加 lane；x8 必然优于 x4；必选某光子平台（B1） | 标准只给 x8 结构与 lane 配置选项，无普遍比较；EML/PIN 为单料号实例 | TQ002-a3-d01；PQ002-a3-d04/d05 |
| 4 | 某 reach 必须采用某器件；connector 数直接决定路线（B2） | 机制为条件性框架文本，无量值支持 | PQ002-a3-d07 |
| 5 | reach 标准名称 → 制造成本排序；单产品 500 m 代表全部 800G（B2） | 无物理量化机制与金额证据 | TQ002-a3-d02 |
| 6 | CPO 实测一定更低功耗；power class 等于实际功耗；<17 W 为行业通值（B3） | CPO 为 expected/target；power class 是热设计约束非实测功耗 | TQ002-a3-d03/d05 |
| 7 | 由密度直接选定 solder/socket 或路线；换算 ports/RU（B4） | 密度只作输入与工程权衡；无单位面积换算与选择证据 | TQ002-a3-d06 |
| 8 | hot-plug 必然降低成本；所有 CPO 不可维护；connector 未固定 ⇒ 服务方式未定（B5） | 维护只有事实层；connector 开放项 ≠ 服务方式开放项 | TQ002-a3-d08；TQ002 最终裁决勘误 |
| 9 | 管理/供电路径分层使热插拔可作为服务事件独立处理（B5） | 来源未直接支持且非桥接必需 | adjudication-wq001-attempt1 修正项 4 |
| 10 | 同一份 OIF 来源两侧引用 = 两份独立证据（B4） | 单份冻结来源的不同内容，非独立证实 | adjudication-wq001-attempt1 修正项 3 |
| 11 | CMIS“唯一核心功能骨架”为普遍事实（B1 证据读法） | PQ002 最终裁决勘误：改读“本轮采用的 CMIS 条件化接口骨架” | adjudication-pq002-final |
| 12 | PQ009 已回答 optical-budget 指标 | PQ009 无本轮独立研究稿；只作待验证标引 | sources-wq001.md |
| 13 | 把相关性写成因果性；证据不足的桥输出 | 证据不足只保留空缺，不补写 | contract-wq001.md §3 |
| 14 | WQ001 生成第三套知识主干 / 写 canonical / 改变覆盖状态 | WQ001 仅是两套知识体系之间的关系 | contract-wq001.md §1/§3 |

## 6. 自检矩阵

| # | 检查项 | 本稿回应 |
|---|---|---|
| 1 | 只消费经裁决的两份草案与冻结来源 | 全文证据均挂 TQ002-a3-dNN／PQ002-a3-dNN 及其证据；PQ001 仅按冻结包标注引用，不消费其正文；未引入包外来源 |
| 2 | 五个 QID 白名单 | 全文仅出现 WQ001、TQ002、PQ001、PQ002、PQ009；未出现任何其他 QID |
| 3 | 固定链条四段 | B1–B5 每条均含 场景需求→接口/链路约束→物理机制→可观察指标 |
| 4 | 双侧证据 | 每条候选关系均列 route-side 需求证据与 physical-side 机制证据 |
| 5 | B1 强度 | 仅写“规范结构支持（含单产品实例）”，未写“直接证实” |
| 6 | B4 单源说明 | route-side 来自 TQ002；physical-side 来自冻结 OIF §7.2.1/Table 4；PQ002 裁决仅用于装配层层属确认；明示“同一来源不同内容，非两份独立证据” |
| 7 | B5 删除管理/供电分层推论 | 该句只出现在第 5 节被拒推论中；B5 链条与 statement 不含 |
| 8 | 两处勘误吸收 | PQ002-a3-d01 改读 CMIS 条件化接口骨架（B1）；TQ002-a3-d08 改读 hot-pluggable 能力与 hot-plug/unplug 瞬态事件分开（B3/B5）、均不证明维护成本下降；部署分段标签仅阅读提示（B2/未桥接项 7） |
| 9 | 空缺保留（attempt 1） | 成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值、ports/RU 均未桥接（第 4 节） |
| 10 | 不把受限推论伪装成事实 | B2 明示条件性框架文本与未闭合数值；每条关系均显式标注强度 |
| 11 | PQ009 只作待验证 | optical-budget 标为待 PQ009 验证；无“已回答”表述 |
| 12 | 无路线/公司/份额推论 | 全文无“因此应选 EML/SiPh/LPO/CPO”、无公司归群或份额句（第 5 节拒绝） |
| 13 | 结论收口 | 本节只写“形成五条 draft-only 候选关系”；未写 WQ001 已覆盖或已完成 |
| 14 | 草案字段 | 每条关系草案含 `relation_type`、双侧证据、固定链条、强度、`would_mark_covered: false` |
| 15 | 无 canonical/新 QID/覆盖变更 | 见第 7 节停止结论 |

## 7. 停止结论

本稿形成五条 draft-only 候选关系（WQ001-a2-b01–b05），全部 `would_mark_covered: false`。WQ001 未标记覆盖、未写 canonical／why_links.yaml／knowledge.yaml／CSV、未生成新问题 ID、未改变任何覆盖状态；本稿不代表 WQ001 已覆盖或已完成。WQ001 仅是 route 体系与 physical 体系之间的关系，未生成第三套知识主干。

未桥接项（成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值、ports/RU、铜缆 reach/10-40 km 覆盖等）在获得物理量化机制或公开定量一手证据前，保持空缺而非补写；optical-budget 数值待 PQ009 的独立研究稿验证，本稿不宣称 PQ009 已回答。

五条候选关系不得被引用为 EML/SiPh/LPO/CPO 路线选择、公司归群或市场份额结论的证据。在相应定量证据闭合且经独立验收前，本包任何内容不得提升为 canonical。
