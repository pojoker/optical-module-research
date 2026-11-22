## 1. PQ001 范围声明

本轮以 OSFP 可插拔模块为观察样本，考察光模块在主机电系统与外部光链路之间的系统功能与边界。所得边界结论仅适用于 OSFP/OSFP-RHS 形态，不代表全部光模块形态；cage、host PCB、riding heatsink 等 host 侧实体不写入模块本体。

## 2. 系统边界表

| 边界层 | 边界内容 | 依据 | 主张类型 |
|---|---|---|---|
| 系统级问题 | 光模块位于主机电系统与外部光链路之间，承担发送端电转光、接收端光转电的双向转换功能 | S1、S2（公司年度报告原文口径） | 公司口径 |
| 主机高速电信号边界 | OSFP 形态下模块 PCB 的 contact pads 与 host connector 配合形成模块 card-edge 电边界；60-contact edge connector 承载高速 TX/RX 差分对 | S3 §3.5（印刷页 30）、§15（印刷页 159–160） | OSFP形态规范事实 |
| 供电与低速管理边界 | 同一 60-contact 连接器承载低速控制、供电与地；管理接口内容不在 OSFP 规范正文，摘要指明另见 CMIS；CMIS 定义 host-to-module 两线管理通信（OIF 官方说明） | S3 p.1 摘要、§15；S5 | OSFP形态规范事实 + 组织官方口径 |
| 机械/热边界 | host cage/mating connector、host PCB layout 属 host 侧；OSFP-RHS 的 riding heatsink 明确属于 host；OSFP MSA 官方将 mechanical module、card cage、electrical interface and pinout 列为规范覆盖对象 | S3 印刷页 17 Scope；S4 | OSFP形态规范事实 |
| 外部光接口边界 | OSFP 规范对外部光接口仅给出示例性图示并明示为 guidelines，不定义完整光学信号标准 | S3 §14.4（印刷页 146） | OSFP形态规范事实 |
| OSFP 样本的适用限制 | 本轮电、机械/热、外部光边界结论均以 OSFP/OSFP-RHS 为样本得出，仅适用于该形态；公司口径仅证明发布主体自身表述，不承诺任何具体形态；不得把 S1–S5 拼合为所有光模块的统一标准边界 | S1–S5 来源组合规则 | 限制声明（非原子主张） |

## 3. 原子主张草案

### PQ001-D1

- draft_id：PQ001-D1
- system：物理知识
- question_id：PQ001
- claim_type：公司口径
- statement：中际旭创与博创科技在各自 2024 年年度报告中，均把光模块描述为承担光电转换的系统部件：发送端将电信号转换为光信号，经光纤传输后，接收端将光信号转换回电信号。
- evidence_ids：S1、S2
- boundary：仅证明两家发布主体对光模块系统功能与构成层级的自身表述，适用于主机电系统与外部光链路之间的系统级功能，不描述具体形态、接口或内部实现。
- rejected_inference：不能推出光模块存在行业唯一标准定义；不能推出所有光模块内部构成相同；不能把公司口径当成 OSFP 或其他任何形态的规范边界。
- would_mark_covered：false

### PQ001-D2

- draft_id：PQ001-D2
- system：物理知识
- question_id：PQ001
- claim_type：OSFP形态规范事实
- statement：OSFP/OSFP-RHS 形态下，模块 PCB 的 contact pads 与 host connector 配合形成模块 card-edge 电边界；该 60-contact edge connector 同时承载高速 TX/RX 差分对、低速控制、供电与地。
- evidence_ids：S3（§3.5，印刷页 30；§15，印刷页 159–160）
- boundary：仅适用于 OSFP/OSFP-RHS 可插拔形态的 host-module 电边界；描述的是模块与 host 之间的电接口层，不描述模块内部组件。
- rejected_inference：不能推出所有光模块采用相同电边界或相同连接器；不能把该连接器的承载关系推广为其他形态的共同电边界。
- would_mark_covered：false

### PQ001-D3

- draft_id：PQ001-D3
- system：物理知识
- question_id：PQ001
- claim_type：OSFP形态规范事实
- statement：OSFP MSA 规范将 host cage/mating connector、host PCB layout 列为 host 侧对象，并明确 OSFP-RHS 的 riding heatsink 属于 host；OSFP MSA 官方把 mechanical module、card cage、electrical interface and pinout 概括为自身规范的覆盖范围。
- evidence_ids：S3（印刷页 17 Scope）、S4
- boundary：仅适用于 OSFP/OSFP-RHS 形态下 module 与 host 的机械/热归属划分；S4 只证明 OSFP MSA 官方对自身覆盖范围的概括。
- rejected_inference：不能推出 cage、host PCB 或 host-side riding heatsink 属于模块本体；不能推出其他 MSA 或板载形态的机械/热边界与 OSFP 相同。
- would_mark_covered：false

### PQ001-D4

- draft_id：PQ001-D4
- system：物理知识
- question_id：PQ001
- claim_type：OSFP形态规范事实
- statement：OSFP 规范摘要把管理接口内容划归 CMIS，正文不承载完整管理接口定义；规范对外部光接口仅给出示例性图示并明示为 guidelines，不定义完整光学信号标准；管理接口、形态规范与光学信号标准由此分属不同层级。
- evidence_ids：S3（p.1 摘要；§14.4，印刷页 146）
- boundary：仅说明 OSFP 规范自身对覆盖范围的分层表述，适用于 OSFP/OSFP-RHS 形态的管理接口归属与外部光接口表述。
- rejected_inference：不能把 form-factor MSA 写成完整光学信号标准；不能把管理接口与高速数据信号接口混为一层；不能推出 OSFP 规范涵盖光学 PMD 全部要求。
- would_mark_covered：false

### PQ001-D5

- draft_id：PQ001-D5
- system：物理知识
- question_id：PQ001
- claim_type：组织官方口径
- statement：OIF 于 2022-01-05 官方公告中说明 CMIS 适用于 pluggable 与 on-board modules，定义基于两线接口的 host-to-module 管理通信。
- evidence_ids：S5
- boundary：仅为 OIF 官方口径，不是 CMIS 规范正文；只证明 CMIS 的适用对象与 host-to-module 管理通信的官方说明，不替代 CMIS 规范要求。
- rejected_inference：不能推出任一模块均实现 CMIS；不能以 OIF 公告替代 CMIS 规范正文；不能把管理通信接口等同于高速数据信号接口。
- would_mark_covered：false

## 4. 研究注记

### 注记 1

- attach_to：PQ001
- note：S3 摘要（p.1）把管理接口内容划归 CMIS，但本轮来源集合中只有 OIF 公告（S5）转述 CMIS 定位，没有 CMIS 规范正文；因此"供电与低速管理边界"中管理接口一侧的规范级定义存在资料缺口，仅靠转述无法闭环。
- trigger_evidence_ids：S3（p.1 摘要）、S5
- why_existing_question_can_hold_it：供电与低速管理边界是 PQ001 系统边界表的既定条目，属系统边界问题；它不是 PQ003 的参考样机选型问题，也不涉及 RQ000 上游对象口径或 PQ002 下游功能链的内部展开。
- expected_answer_shape：以 CMIS 官方规范正文为准，说明 host-to-module 管理通信接口的定义范围，并确认其与高速数据信号接口是两个独立层。
- next_action：在后续证据允许时冻结一份现行 CMIS 官方规范正文，按其完整上下文核对管理边界条目。
- stop_condition：当能够直接引用 CMIS 规范正文说明 host-to-module 管理接口边界、无需再以 OIF 公告转述时停止；该条件是 PQ001 管理边界条目的局部判据。

### 注记 2

- attach_to：PQ001
- note：S3 §14.4 表明 OSFP 规范对可用于 OSFP 模块的外部光接口仅给出 guideline 级示例，未定义完整光学信号标准；PQ001 的"外部光接口边界"缺少确定"由哪类文档定义外部光信号/连接器标准"的资料依据。
- trigger_evidence_ids：S3（§14.4，印刷页 146）
- why_existing_question_can_hold_it：外部光接口边界属于 PQ001 范围声明与系统边界表的既定内容，是确定系统边界的问题；它不是 PQ003 替下游样机选型的问题，也不属于 PQ002 的功能链内部展开。
- expected_answer_shape：明确外部光接口（连接器与 PMD 光信号层）由哪类标准文档定义，以及它与 OSFP 形态规范构成何种引用关系。
- next_action：在后续证据轮次冻结承载外部光接口定义的文档类别，逐条比对后再写入草案。
- stop_condition：当能引用具体标准说明 OSFP 外部光接口边界、不再存在需猜测的文档类别时停止；该条件是局部条件，不构成开启其他轮次的门闩。

## 5. 拒绝的推论

1. 拒绝"OSFP = 所有光模块"：S3/S4 全部事实均已限定于 OSFP/OSFP-RHS；S1/S2 公司口径只描述功能层级，不承诺形态。任何把 OSFP 的 card-edge 电边界、60-contact 承载关系、cage/热归属推广为所有光模块共同边界的推论均被拒绝。
2. 拒绝"cage / host PCB / host-side riding heatsink = 模块本体"：S3 印刷页 17 将 host cage/mating connector、host PCB layout 列为 host 侧对象，并明确 OSFP-RHS riding heatsink 属于 host；S4 仅把 card cage 列为规范覆盖对象之一。host 侧实体不得写入模块本体。
3. 拒绝"form-factor MSA = 完整光学信号标准"：S3 p.1 把管理接口划归 CMIS，§14.4 把外部光接口图示限定为 guidelines；OSFP 形态规范只覆盖 form factor、连接、供电、机械/热等，不构成完整光学 PMD 信号标准。
4. 拒绝"管理接口 = 高速数据信号接口"：S3 §15 在同一连接器中分别承载高速 TX/RX、低速控制、供电与地；S3 p.1 与 S5 表明管理通信是独立于高速数据的两线 host-to-module 接口。
5. 拒绝"S1–S5 拼合成无主体的行业统一标准"：来源组合规则禁止把不同发布主体的句子焊成一个行业事实；公司口径、OSFP 规范事实、OIF 官方口径必须保持各自发布主体与层级。

## 6. 自检矩阵

| 检查项 | 结果 | 说明 |
|---|---|---|
| 体系 | 通过 | 5 条草案 system 均为"物理知识" |
| QID | 通过 | 全部 question_id 为 PQ001；未新增任何 CQ/PQ/TQ/WQ 编号 |
| 锚型 | 通过 | 仅使用 S1–S5 且全部 admissible_for_draft: true；S1/S2 为 local_file 公司报告，S3–S5 为 web_snapshot；QSFP-DD Rev 7.1 未使用 |
| 适用边界 | 通过 | OSFP 特有结论（D2–D4）、公司口径（D1）、组织官方口径（D5）逐条分开；每条草案均有来源、boundary 与 rejected_inference |
| 上下文 | 通过 | 注记基于 S3 p.1、§14.4、S5 的完整上下文提出，未用短引人为制造矛盾；D1 明示两家公司各自表述，未焊成无主体行业事实 |
| 注记必要性 | 通过 | 2 条注记均通过五项必要性检查（证据触发、实质缺口、可执行下一步、可判定停止条件、层级归属说明）；少于 3 条属正常结果；未输出"本轮未研究某问题"类行政注记 |
| 覆盖状态 | 通过 | 所有草案 would_mark_covered 均为 false；未输出任何 YAML；未声称 PQ001 已覆盖 |

## 7. 停止结论

两条注记的停止条件（可直接引用 CMIS 规范正文说明管理边界、可引用具体标准确定外部光接口边界）均为 PQ001 内部边界条目的局部判据，只用于判定对应资料缺口何时闭合。

局部停止条件不得被解释为开启其他 draft-only 轮次的全局门闩；PQ003 等下游问题是否进入研究，由其自身合同与证据触发另行决定。

本轮为受控研究：未新增问题编号、未输出 append-ready YAML、未改变任何问题覆盖状态，PQ001 维持 draft_only。
