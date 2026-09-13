# TQ002 最终候选稿（draft-only · a3）

- 体系：`route` ｜ 问题：`TQ002` ｜ 状态：仅草案 ｜ `would_mark_covered: false`

## 1. 结论摘要

- TQ002 的六约束（带宽、距离、功耗、密度、成本、维护）不是“800G”的单值属性，而是按场景、按证据层分别定义的多维比较输入；证据层分三：标准/规范层、单产品层、合作封装（CPO）框架层。
- 标准层（T1，IEEE 802.3df-2024，2024-02-16 获批）：800 Gb/s 的 x8 结构覆盖 AUI、backplane、copper、MMF 50/100 m、SMF 500 m/2 km；同一八 lane port 可配置 1×8、2×4、4×2、8×1。带宽与 lane 配置只作 port flexibility / 密度输入，不构成单位面积密度指标。
- 产品层（T5，Coherent FTCE4517E1PxM）：单一只 800G 级 OSFP 可同时接受带宽（850 Gb/s aggregate）、距离（500 m SMF）、功耗（<17 W）、维护接口（hot-pluggable、MPO-16）约束；不代表全部 800G。
- 规范层（T4，OSFP Rev 5.22）：power class 是系统热设计约束，host 在启用高功耗前读取；hot-plug/hot-unplug 是规范处理的功耗瞬态事件。
- 框架层（T6/T7，OIF FD 01.0 / 3.2T IA 01.0）：power savings 是 expected/target 语言，非实测；密度与 rework/access 存在实现层权衡；reliability/redundancy/repairability 须单独考虑。
- 证据分级：supported fact（hot-pluggable、power class 机制、PMD reach 表）与 not quantitatively closed（成本金额、维护费用、CPO 实测功耗、部署密度数值）明确分层；成本与维护定量显式标为“未闭合”，不用常识补数。
- 边界：本稿只建立六约束的比较输入；不含公司归群、市场份额、路线胜负判断；`would_mark_covered: false`。

## 2. 六约束定义矩阵

| 约束 | 可操作定义 | 场景需求 | 可观察指标 | 规范/产品实例（版本与范围） | 当前证据不能支持的推论 |
|---|---|---|---|---|---|
| 带宽 | 速率标签 × lane 结构 × 介质 × reach 的组合容量，非单一“800G”标签 | 按端口吞吐与 lane 拆分选 1×8/2×4/4×2/8×1 | 聚合速率、lane 数、PAM4 调制、MAC/PHY/管理参数 | T1：IEEE 802.3df-2024（IEEE SA 摘要表） | 单一“800G”代表全部；x8 永优于 x4；具体光模块内部路线 |
| 距离 | 标准定义的 per-PMD 标称 reach | 按部署分段（机架内/DC/园区）选介质与 reach | PMD 标称 reach、介质类别（MMF/SMF/copper/backplane/AUI） | T1：MMF 50/100 m、SMF 500 m/2 km；T5：500 m SMF 产品 | reach 名称→制造成本排序；T5 代表全部 800G；T2 10/40 km 视为 final |
| 功耗 | 分层定义：规范层 power class（系统热约束）；产品层 dissipation；框架层目标 savings；三层不混写 | host 在启用高功耗前读 module power class；系统 thermal design/validation | power class、低/高功耗模式、hot-plug/hot-unplug 瞬态、产品 dissipation 值 | T4：OSFP Rev 5.22 §15.8（pp.168–170）；T5：<17 W；T6：FD 01.0 §5（expected/target） | power class=实际功耗；<17 W 为行业通值；CPO 一定更省电 |
| 密度 | 分层：端口 lane 配置（灵活性输入）；substrate footprint（engine 尺寸/占位/rework 权衡） | 按 port 拆分需求与 substrate 面积/可返工需求取舍 | lane 配置项数、socket retention 占位、solder reflow 密度与 yield | T1：1×8/2×4/4×2/8×1；T6：FD 01.0 §7.2.1/Table 4（p.17） | lane 配置→ports/RU 单位面积数值；Table 4 为市场价格；socket/solder 单一更优 |
| 成本 | 维度清单（无金额）：known/balanced cost factors、installation、operational（含 energy）、架构/管理延续性；工程 tradeoff | 场景对比只比维度，不比金额 | 已支持维度项；定量金额：未闭合 | T3：P802.3df CSD（Economic Feasibility，p.8）；T6：FD 01.0 §7.2.1 | 任何模块价格/维护费金额；由 reach/hot-plug 推出制造成本或生命周期成本排序 |
| 维护 | 事实层：hot-pluggable/hot-unplug 为规范事件（supported fact）；推断层：生命周期成本影响（not closed） | 按服务方式需求（现场可插拔 vs rework/access 受限）分场景记录 | 是否 hot-pluggable、rework 方式、现场 access 限制、repairability 是否单列 | T4：§15.8；T5：hot-pluggable OSFP；T6：§7.8、§7.2.1；T7：IA 01.0 p.24 | hot-plug⇒维护成本更低；connector 未固定⇒服务方式未定/已定；所有 CPO 不可维护或不可更换 |

## 3. 场景实例矩阵

| 场景 | 介质/reach（版本） | 主要约束型态 | 实例证据 | 未闭合项（挂 TQ002） |
|---|---|---|---|---|
| 机架内/背板/近 ASIC 电互连 | AUI/backplane/copper（T1：802.3df-2024；摘要未给 copper reach 值） | 带宽、lane 配置密度、接口功耗 | T1 | copper reach 数值；该场景功耗/成本定量 |
| MMF 数据中心 | MMF 50/100 m（T1） | 带宽+距离+功耗 | T1 | MMF 场景成本/维护定量 |
| SMF 500 m | SMF 500 m（T1；T5） | 带宽+距离+功耗+维护接口联合约束 | T1；T5（FTCE4517E1PxM：850 Gb/s、<17 W、hot-plug、MPO-16） | 单产品不代表全部 800G；成本金额 |
| SMF 2 km | SMF 2 km（T1） | 距离扩展约束 | T1 | 2 km 产品级功耗/维护证据 |
| 10/40 km 单纤方向（注记行） | 仅 T2 历史 objectives（2022-03-17）；不入主结论 | — | T2（SHA256 b9c38e82…） | final 标准对 10/40 km 与 copper 距离的实际覆盖待核验 |
| CPO 近 ASIC（51.2T 交换 / 16×3.2T module） | 近 ASIC placement（T6：FD 01.0；T7：IA 01.0） | 密度+功耗目标+repairability | T6 §5/§7.2.1/§7.8；T7 p.7/p.24 | CPO 实测功耗、市场成本、服务方式定量 |

## 4. 原子主张草案（10 条，draft_id 唯一）

```yaml
draft_id: TQ002-a3-d01
system: route
question_id: TQ002
claim_type: definition
statement: "带宽约束的可操作定义是“速率标签 × lane 结构 × 介质 × reach”的组合容量，而不是单一“800G”标签；IEEE 802.3df-2024 下 800 Gb/s 的一个八 lane port 可配置为 1×8、2×4、4×2 或 8×1。"
evidence_ids: ["T1: IEEE 802.3df-2024（2024-02-16 获批；IEEE SA 摘要表）"]
boundary: "仅指标准接口组合；不涉及具体光模块内部路线；lane 配置只作 port flexibility 输入。"
rejected_inference: "单一“800G”标签代表全部带宽形态；x8 永优于 x4；由 lane 配置直接推出单位面积密度。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d02
system: route
question_id: TQ002
claim_type: definition
statement: "final-standard 层的距离可观察口径是 per-PMD 标称 reach：800 Gb/s x8 覆盖 MMF 50/100 m 与 SMF 500 m/2 km，另有 AUI/backplane/copper 类别（T1 摘要未给 copper 距离值）；产品层存在 500 m SMF 实例。"
evidence_ids: ["T1: IEEE 802.3df-2024（IEEE SA 摘要表）", "T5: Coherent FTCE4517E1PxM 规格（PDF p.1，500 m SMF）"]
boundary: "主结论限 T1 final-standard 摘要范围；T2 历史 objectives（copper 1/2 m、10/40 km）只入 A09 注记。"
rejected_inference: "reach 标准名称直接解释为制造成本排序；T5 的 500 m 代表全部 800G。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d03
system: route
question_id: TQ002
claim_type: definition
statement: "功耗在 form factor 层是系统热设计约束：OSFP Rev 5.22 定义 power classes 与低/高功耗模式，host 在启用高功耗前读取 module power class；最大额定功耗的使用需系统级 thermal design/validation；hot-plug/hot-unplug 是规范处理的功耗瞬态事件。"
evidence_ids: ["T4: OSFP Module Specification Rev 5.22（§1 p.17；§15.8 pp.168–170）"]
boundary: "规范约束层；不对应任一具体模块实测功耗；与其他功耗证据层不混写。"
rejected_inference: "power class 等于具体模块实际功耗；hot-plug 自动等于低维护成本。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d04
system: route
question_id: TQ002
claim_type: 联合实例（产品）
statement: "一个真实产品同时接受多项约束：Coherent FTCE4517E1PxM 为 hot-pluggable OSFP，850 Gb/s aggregate、8×100G PAM4 retimed electrical interface、500 m SMF、MPO-16、power dissipation <17 W。"
evidence_ids: ["T5: Coherent FTCE4517E1PxM 800G DR8 OSFP 产品规格（PDF p.1，存档快照 2026-08-23）"]
boundary: "单产品实例；用于说明约束可联合出现；不代表行业通值或路线证据。"
rejected_inference: "<17 W 是所有 OSFP/DR8 的通值；该产品的速率/距离结构代表全部 800G。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d05
system: route
question_id: TQ002
claim_type: 规范/目标层定义
statement: "OIF CPO framework 将“engine 靠近 host ASIC 以降低高速电通道损耗/不连续、目标高带宽与显著 power savings”列为 expected/target；框架同时要求对 reliability、redundancy、repairability 单独考虑。"
evidence_ids: ["T6: OIF Co-Packaging Framework FD 01.0（§5 p.9；§7.8 pp.26–27）"]
boundary: "框架目标语言，非实测结果；不覆盖所有 CPO 实现或服务方式。"
rejected_inference: "CPO 一定比 pluggable 低功耗；所有 CPO 不可维护或不可更换。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d06
system: route
question_id: TQ002
claim_type: definition
statement: "密度约束分两层：端口层由 lane 配置（1×8/2×4/4×2/8×1）提供灵活性输入；substrate 层由总带宽、布线密度、光纤接口、热管理决定 engine 尺寸，removable socket 的 retention mechanism 占面积并限制密度，solder reflow footprint 密度高但 rework 受限且有 yield loss。"
evidence_ids: ["T1: IEEE 802.3df-2024（lane/port 配置）", "T6: OIF CPO FD 01.0（§7.2.1/Table 4，p.17）"]
boundary: "只作密度输入/工程权衡；不换算为 ports/RU 单位面积数值；Table 4 非市场成本数据。"
rejected_inference: "lane 配置直接等于单位面积密度；socket 或 solder reflow 整体胜出。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d07
system: route
question_id: TQ002
claim_type: definition（维度，未闭合）
statement: "成本证据仅支持维度清单、不支持金额：P802.3df CSD 的经济可行性考虑 known/balanced cost factors、installation cost、operational cost（含 energy consumption），并借架构/管理/软件延续降低维护成本；CPO 框架提供 rework/yield 工程权衡。模块价格、维护费用与路线成本排序无公开定量一手证据，标为“未闭合”。"
evidence_ids: ["T3: IEEE P802.3df CSD（Economic Feasibility，p.8）", "T6: OIF CPO FD 01.0（§7.2.1/Table 4）"]
boundary: "维度已支持 / 数值未闭合两层分开；不以常识补数。"
rejected_inference: "任何模块价格、维护费用金额；由 reach 或 hot-plug 推出制造成本或生命周期成本排序。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d08
system: route
question_id: TQ002
claim_type: definition（事实，未闭合）
statement: "维护证据分事实与推断：hot-pluggable/hot-unplug 是规范处理的接口事件（supported fact）；“热插拔⇒现场维护成本更低”无数值证据（not quantitatively closed）；CPO 的 repairability 需单独考虑，socket 可 rework 但现场 access 受限；T7 中光侧 pigtail、最终 connector 未固定，属规范/接口开放项。"
evidence_ids: ["T4: OSFP Rev 5.22（§15.8）", "T5: Coherent FTCE4517E1PxM（hot-pluggable OSFP）", "T6: OIF CPO FD 01.0（§7.8；§7.2.1）", "T7: OIF 3.2T IA 01.0（p.24）"]
boundary: "connector 位置/实现未固定 ≠ service/replacement method 未固定；不推出全生命周期成本高低。"
rejected_inference: "hot-plug⇒维护成本一定更低；connector 未固定⇒服务方式未定（或已排除）；所有 CPO 均不可维护。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d09
system: route
question_id: TQ002
claim_type: 研究注记
statement: "T2（IEEE P802.3df objectives，2022-03-17）显示 800 Gb/s 项目目标为多维组合（copper 1/2 m、MMF 50/100 m、SMF 500 m/2 km、10/40 km 单纤方向等）；仅作为“场景输入是多维组合”的历史注记挂 TQ002；final 状态以 T1 核验为准。"
evidence_ids: ["T2: IEEE P802.3df objectives 2022-03-17（SHA256 b9c38e82…，印刷页 3）"]
boundary: "历史项目目标文件；10/40 km 与 copper 距离不入主结论。"
rejected_inference: "目标全部由同一物理实现完成；由 objectives 的 reach 直接推导成本或路线胜负；T2 取代 T1 作为 final 状态。"
would_mark_covered: false
```

```yaml
draft_id: TQ002-a3-d10
system: route
question_id: TQ002
claim_type: 范围声明
statement: "本稿只建立六约束的比较输入；不进行公司归群、市场份额判断或路线胜负判断；不生成公司群、不生成新问题 ID、不改变覆盖状态。"
evidence_ids: ["sources-tq002.md §六约束证据规则（冻结包）", "T1 不可支持边界", "T3 不可支持边界"]
boundary: "公司路线服务群等归属后续问题（如 TQ012/TQ013），本稿不回答；对 TQ001 存在性与 PQ001 系统边界无新增表述。"
rejected_inference: "本稿任何条目可被引用为路线、公司或份额结论的证据。"
would_mark_covered: false
```

## 5. 证据缺口与研究注记（仅挂 TQ002）

1. 历史 reach 补核（挂 TQ002）：T2 的 10/40 km 单纤方向与 copper 1/2 m 只存在于 2022-03-17 目标文件；T1 摘要未展开，需核验 final 标准文本后才可讨论。
2. 成本定量（挂 TQ002）：模块价格、维护费用、路线成本排序无公开定量一手证据；未闭合。
3. 维护定量（挂 TQ002）：hot-plug 事件与“维护成本更低”之间无数值证据链；未闭合。
4. CPO 功耗实测（挂 TQ002）：T6 的 power savings 是 expected/target，无实测功耗报告；未闭合。
5. 部署密度（挂 TQ002）：规范仅给 lane 配置与 substrate tradeoff，无 ports/RU 等公开数值；未闭合。
6. AUI/backplane/copper 场景细节（挂 TQ002）：T1 摘要未展开其功耗/维护参数；未闭合。

## 6. 拒绝的推论

1. 不同 reach 的标准名称 → 制造成本排序。
2. hot-plug → 现场维护成本一定更低。
3. CPO 靠近 ASIC → 所有 CPO 不可维护或不可更换。
4. form factor 最大功率等级 → 任一具体模块实际功耗。
5. 单产品 500 m、EML、PIN 等参数 → 全部 800G。
6. connector 位置/实现未固定 → service/replacement method 未固定。
7. lane 配置（1×8/2×4/4×2/8×1） → 单位面积密度指标（ports/RU 数值）。
8. 任何“因此应选 EML/SiPh/LPO/CPO”的句子。
9. T2 历史 objectives → 最终标准状态或 10/40 km 实际覆盖。
10. 本稿任何条目 → 公司归群/市场份额/路线胜负证据（归属 TQ012/TQ013 等）。

## 7. 自检矩阵

| # | 检查项 | 结果 | 位置 |
|---|---|---|---|
| 1 | 每条唯一 `draft_id: TQ002-a3-dNN`，无重复（裁决残项修复） | ✓ | §4（d01–d10） |
| 2 | 原子主张总数 ≤ 10 | ✓ | §4（10 条） |
| 3 | 九字段齐全（draft_id/system/question_id/claim_type/statement/evidence_ids/boundary/rejected_inference/would_mark_covered） | ✓ | §4 每条 |
| 4 | 全部 `would_mark_covered: false` | ✓ | §4 |
| 5 | 六约束逐项存在，未合并消失（矩阵 6 行 + 主张覆盖） | ✓ | §2；A01–A08 |
| 6 | supported fact / not quantitatively closed 分层保留 | ✓ | §1；A03/A04/A07/A08/A09 |
| 7 | 主结论 IEEE reach 只用 T1；T2 10/40 km 只入 TQ002 注记 | ✓ | A02/A09；§3 注记行 |
| 8 | connector 未固定 ≠ service/replacement method 未固定 | ✓ | A08；§6-6 |
| 9 | lane 配置只作 port flexibility，不作单位面积密度 | ✓ | A01/A06；§6-7 |
| 10 | 研究注记只挂 TQ002 | ✓ | §3 未闭合列；§5 |
| 11 | 无路线选择/公司归群/市场份额/成本金额 | ✓ | A07/A10；§6 |
| 12 | 成本与维护定量显式“未闭合” | ✓ | A07/A08；§5 |
| 13 | IEEE reach/lane、OSFP 功耗/热或 hot-plug、OIF CPO 三类实例齐备且保留版本与范围 | ✓ | T1；T4/T5；T6/T7 |
| 14 | 全文无“因此应选 EML/SiPh/LPO/CPO”句 | ✓ | 全文 |
| 15 | attempt-1 六类错误逐项回应（对照 attempt-2 合同六项硬约束） | ✓ | 见下表 |

attempt-1 六类错误逐项回应（对应 attempt-2 六项硬约束）：① 原子主张字段缺失/不完整 → 九字段齐备（§4）；② 历史 objectives 混入主结论 → 隔离至 A09 注记（§6-9）；③ supported fact 与决策充分性混淆 → §1/A07/A08 分层；④ connector ⇒ service method 误推 → §6-6 拒绝；⑤ lane 配置当单位面积密度 → §6-7 拒绝；⑥ 注记挂错 QID → 全部只挂 TQ002。

## 8. 停止结论

- 本稿为 TQ002 最终候选稿（draft-only），`would_mark_covered: false`；不写 canonical、不生成公司群、不生成新问题 ID、不改变覆盖状态。
- 对目标问题“TQ002 不同场景的带宽、距离、功耗、密度、成本和维护约束是什么？”：六约束的可操作定义、场景实例矩阵与证据分级已给出，可作后续比较输入；成本与维护定量未闭合，依赖未来公开定量一手证据补全。
- 未提前回答 TQ004–TQ014；对 TQ001 存在性与 PQ001 系统边界无新增表述。
- 停止：不得由本稿推出任何技术路线（EML/SiPh/LPO/CPO）选择、公司归群或市场份额结论；不得在成本/维护/CPO 实测等定量证据闭合前将本稿提升为 canonical。
