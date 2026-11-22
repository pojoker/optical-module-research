# PQ002 最终候选稿（attempt-3，draft-only）

**元信息**：`system: physical` ｜ `question_id: PQ002` ｜ 主张数：8 ｜ 注记：2（挂 PQ004/PQ005）｜ 全部 `would_mark_covered: false`

---

## 1. 结论摘要

PQ002 的功能链可在四个来源层级闭合：

- **条件骨架（P2）**：CMIS-managed transmission module 有 Host Interface 与 Media Interface 两个 mission-related 物理接口；Host 侧 host→module 为 transmitter input、module→host 为 receiver output；Media 侧 module→media 为 transmitter output、media→module 为 receiver input。Application 的本质是 host-side 与 media-side 之间的 bridge/forwarding，且 media 可为高速电或光。
- **公司功能口径（P1）**：发送端把电信号转为光信号，经光纤传送后，接收端把光信号转为电信号；光模块由光电子器件与功能电路组成，实现收发与转换。
- **OSFP 实例（P4）**：Coherent 800G-DR8 OSFP 中，TX 为电气 PAM4 输入 →（EML，官方产品页）→ 光 TX 输出（MPO-16/SMF）；RX 为光输入 →（PIN，官方产品页）→ 电气 PAM4 输出。
- **CPO 实例（P3）**：optical engine 完成 ASIC 电信号与光信号互转，EIC/OIC 承担驱动/调制与光电检测/TIA 功能映射；media-side 有 pigtail / built-in connector / mid-board optical connector 等形态。

管理（CMIS two-wire、I2C）、供电、低速控制独立成层，不进入高速 mission data path。

---

## 2. TX/RX 功能链图

```
TX 方向（本模块发送 → 远端接收；电→光→电）
本地 Host
 → [Host Interface] 电气 transmitter input（host→module，PAM4 逐 lane）
 → [模块内部] 电→光转换（host-side 与 media-side 之间的 bridge/forwarding）
 → [Media Interface] 光 transmitter output（module→media，经 MPO-16 → SMF）
 → [media] 光纤传送
 → [远端 Media Interface] 光 receiver input（media→module）
 → [远端模块内部] 光→电转换
 → [远端 Host Interface] 电气 receiver output（module→host）
远端 Host

RX 方向（远端发送 → 本模块接收；与 TX 链角色对调）
远端 Host
 → [远端 Host Interface] 电气 transmitter input
 → [远端模块内部] 电→光转换
 → [远端 Media Interface] 光 transmitter output
 → [media] 光纤传送
 → [本模块 Media Interface] 光 receiver input
 → [本模块内部] 光→电转换
 → [本模块 Host Interface] 电气 receiver output
本地 Host
```

**分段归属标注**：

- 接口名称与信号方向（两链中所有 Host/Media Interface 段）：CMIS-managed transmission module 条件骨架 [P2 §6.1.x]；其中"media 为高速电或光"是 CMIS 条件，图中光 media（光纤）来自 P1/P4 实例口径。
- "电→光""光→电"与"经光纤传送后接收端转回"：公司功能口径 [P1]。
- "bridge/forwarding"仅指模块内 host-side↔media-side [P2 §6.2.1.1]，不延伸解释远端行为。
- PAM4、MPO-16、SMF：Coherent 800G-DR8 OSFP 实例 [P4]，逐 lane 参数见 datasheet p.3–4。
- CPO 实例（engine 内部 EIC/OIC 映射、media-side pigtail/connector 形态）[P3] 属另一实例，不混入上图 OSFP 主链。
- 主链之外：CMIS two-wire（管理）[P2 Abstract]、OSFP 低速控制/供电/地 [P5 §15]、I2C [P4]，均不进入高速数据链。

---

## 3. 三层分解表（◎ CMIS 条件骨架 ｜ ◇ 公司口径 ｜ ◆ OSFP 实例 ｜ △ CPO 实例 ｜ ■ OSFP MSA 规格）

| 行 | 接口边界 | 模块内部功能 | 真实实例部件 |
|---|---|---|---|
| TX 发送 | Host Interface：电气 TX input（host→module）◎；Media Interface：光 TX output（module→media）◎ | 电→光转换 ◇；模块内 host-side↔media-side bridge/forwarding ◎ | 电气 PAM4 逐 lane 参数 ◆；EML（产品页）◆；MPO-16/SMF ◆；CPO 实例：EIC 驱动 laser/modulator、OIC modulator △ |
| RX 接收 | Media Interface：光 RX input（media→module）◎；Host Interface：电气 RX output（module→host）◎ | 光→电转换 ◇；bridge/forwarding ◎ | PIN（产品页）◆；PAM4 电气 RX 逐 lane ◆；CPO 实例：photodetector、TIA/post amplifier △ |
| 非 mission data（管理/供电/机械/热） | CMIS two-wire 管理接口 ◎；OSFP edge connector 低速控制/供电/地 ■；I2C ◆ | 与高速数据链分层，不参与收发 | 机械/热路径细节不在本轮冻结来源闭合范围（停止边界） |

**表注**：P3 §7.2.1 Table 4 的 solder reflow / removable socket 属 engine-to-CPA-substrate 封装/装配，不计入 Media Interface 行。

---

## 4. 原子主张草案

`claim_type` 取值：`conditional_skeleton`（P2 骨架）、`functional_claim`（P1 公司口径）、`instance_functional`（P3/P4 实例）、`path_separation`（路径分层）。

证据图例：`P1#300308-2024`/`P1#300548-2024`（年报）｜`P2#CMIS5.4:§6.x`/`Abstract`｜`P3#CPF01.0:Glossary/§7.3.2/§7.3.4`｜`P4#FTCE4517E1PxM:p1/p3-4/product-page`｜`P5#OSFP5.22:§15`。

### PQ002-a3-d01
- `draft_id`：PQ002-a3-d01
- `system`：physical
- `question_id`：PQ002
- `claim_type`：conditional_skeleton
- `statement`：CMIS-managed transmission module 的唯一核心功能骨架以 Host Interface 与 Media Interface 两个 mission-related physical interfaces 为端点：Host Interface 上 host→module 信号称 transmitter input、module→host 称 receiver output；Media Interface 上 module→media 称 transmitter output、media→module 称 receiver input；Media Interface 是高速电或光接口。
- `evidence_ids`：P2#CMIS5.4:§6、§6.1、§6.1.1、§6.1.2
- `boundary`：仅适用于 CMIS-managed transmission module；resource module、cable assembly 等存在例外；不含任何内部器件结构。
- `rejected_inference`：本冻结来源不支持"Media Interface 必为光"；不支持由该骨架推出具体 BOM 或器件型号。
- `would_mark_covered`：false

### PQ002-a3-d02
- `draft_id`：PQ002-a3-d02
- `system`：physical
- `question_id`：PQ002
- `claim_type`：conditional_skeleton
- `statement`：CMIS Application 以 host-side 与 media-side 之间的信号传播或处理为特征，本质上描述 module 内部的 bridge/forwarding function。
- `evidence_ids`：P2#CMIS5.4:§6.2.1.1
- `boundary`：只写模块内 host-side↔media-side 桥接；不描述远端行为。
- `rejected_inference`：不得延伸为"信号到达远端并反向返回"——CMIS 未描述该段；不得将 Application 等同于特定器件。
- `would_mark_covered`：false

### PQ002-a3-d03
- `draft_id`：PQ002-a3-d03
- `system`：physical
- `question_id`：PQ002
- `claim_type`：functional_claim
- `statement`：中际旭创 2024 年报口径：发送端把电信号转为光信号，经光纤传送后接收端把光信号转为电信号；博创科技 2024 年报口径：光模块由光电子器件和功能电路组成，实现光电信号收发、转换。二者共同支撑电→光→电收发链路的公司级功能描述。
- `evidence_ids`：P1#300308-2024:152-155、P1#300548-2024:160-164
- `boundary`：仅覆盖发送/接收方向的系统级功能转换，不覆盖模块内部器件顺序与完整 BOM。
- `rejected_inference`：不得据"电转光/光转电"补出未经来源支持的内部器件顺序；本冻结来源不支持行业统一内部结构。
- `would_mark_covered`：false

### PQ002-a3-d04
- `draft_id`：PQ002-a3-d04
- `system`：physical
- `question_id`：PQ002
- `claim_type`：instance_functional
- `statement`：Coherent FTCE4517E1PxM（800G-DR8 OSFP，hot-pluggable、850 Gb/s aggregate、retimed PAM4 electrical interface、MPO-16 receptacle、500 m SMF）的发送方向功能链为：Host Interface 电气 TX 输入（逐 lane 参数）→ 模块内部电→光转换 → Media Interface 光 TX 输出经 MPO-16 进入 SMF；该料号官方产品页标 transmitter=EML。
- `evidence_ids`：P4#FTCE4517E1PxM:p1、p3-4、product-page
- `boundary`：仅该料号实例；EML 来自官方产品页，非 datasheet 内部电路图；datasheet 未披露 TX 内部完整连线。
- `rejected_inference`：本冻结来源不支持 EML 或 DSP/driver 顺序为 800G 或所有光模块必备；不得把接口级参数当作内部电路结构。
- `would_mark_covered`：false

### PQ002-a3-d05
- `draft_id`：PQ002-a3-d05
- `system`：physical
- `question_id`：PQ002
- `claim_type`：instance_functional
- `statement`：同一料号的接收方向功能链为：Media Interface 光 RX 输入自 SMF 经 MPO-16 → 模块内部光→电转换 → Host Interface 电气 RX 输出（逐 lane PAM4 参数）给 host；官方产品页标 receiver=PIN。
- `evidence_ids`：P4#FTCE4517E1PxM:p1、p3-4、product-page
- `boundary`：仅该料号实例；datasheet 未披露 RX 内部完整连线。
- `rejected_inference`：本冻结来源不支持 PIN 为 800G 或全部光模块通例；不得由参数页推出内部 O/E 电路详图。
- `would_mark_covered`：false

### PQ002-a3-d06
- `draft_id`：PQ002-a3-d06
- `system`：physical
- `question_id`：PQ002
- `claim_type`：instance_functional
- `statement`：OIF Co-Packaging Framework 中，Optical Engine/Optical Chiplet 把 ASIC 的 electrical signals 转为 optical signals（反向亦然）；EIC 可含驱动 laser/modulator 的 electronics 与把 photodetector 的 photocurrent 转为 usable electrical signal 的 TIA/post amplifier；OIC/PIC 可含 modulator、photodetector、waveguide 等。这给出一个 CPO 实例的 TX 驱动/调制与 RX 光电检测/TIA 功能映射。
- `evidence_ids`：P3#CPF01.0:Glossary
- `boundary`：仅 CPO framework 实例；"may contain"为条件性描述。
- `rejected_inference`：本冻结来源不支持 EIC/OIC 部件为全部光模块必备；不支持 CPO 是唯一实现。
- `would_mark_covered`：false

### PQ002-a3-d07
- `draft_id`：PQ002-a3-d07
- `system`：physical
- `question_id`：PQ002
- `claim_type`：instance_functional
- `statement`：CPO media-side 连接形态实例：engine 可 assembled with pigtail 或 built-in connector 以把高速数据带入/带出 engine；pigtail 可为高密度光接口 ribbon fiber 或高密度电接口 copper cable assembly；"CPO Pigtail + jumper"可含 mid-board optical connector，会增加 optical budget，但可减少 pigtail 搬运损伤并为失败连接器/组件提供返工点。
- `evidence_ids`：P3#CPF01.0:§7.3.2、§7.3.4
- `boundary`：仅 CPO media-side 实例；engine-to-substrate 的 solder reflow/socket（P3 §7.2.1 Table 4）属封装/装配，不进入 Media Interface 行。
- `rejected_inference`：本冻结来源不支持所有 CPO 使用同一连接器；不支持额外/mid-board connector 为必选；不得把 §7.2.1 装配形态写成光纤连接形态。
- `would_mark_covered`：false

### PQ002-a3-d08
- `draft_id`：PQ002-a3-d08
- `system`：physical
- `question_id`：PQ002
- `claim_type`：path_separation
- `statement`：所涉实例与条件骨架中，mission data path 与管理/供电路径分层：CMIS 的 two-wire host-to-module 通信属管理接口适用范围；OSFP 模块 edge connector 分别承载 host→module TX differential pairs、module→host RX differential pairs，以及低速控制、供电和地；Coherent datasheet 把 I2C management interface 与高速 PAM4 electrical interface 分开列出。
- `evidence_ids`：P2#CMIS5.4:Abstract、P5#OSFP5.22:§15、P4#FTCE4517E1PxM:p1
- `boundary`：只声明信号类别分层，不定义模块内部管理电路实现。
- `rejected_inference`：不得把 I2C/CMIS 管理路径写入高速数据链；不得把低速控制与 Host Interface 高速电接口混为一谈。
- `would_mark_covered`：false

---

## 5. 研究注记（挂现有 QID，不生成新 ID）

**注记 1（挂现有 QID：PQ004）**
- 触发证据：P4#FTCE4517E1PxM（p1、p3-4、product-page）
- 缺口：datasheet 只给接口级与收发端逐 lane 参数，未披露该料号内部完整连线/BOM；"retimed PAM4"只支持接口级重定时，不能闭合实例中电气 TX→EML、PIN→电气 RX 之间的器件级功能顺序。本轮冻结来源无法闭合，保留为注记；不改覆盖状态。

**注记 2（挂现有 QID：PQ005）**
- 触发证据：P3#CPF01.0:§7.3.4
- 缺口：CPO "Pigtail + jumper"的 mid-board optical connector 只给出存在性与权衡方向（增加 optical budget、减少 pigtail 损伤、提供返工点），未给出具体型号、插损数值与返工判定标准。本轮冻结来源无法闭合，保留为注记；不改覆盖状态。

---

## 6. 拒绝的推论

| # | 被拒绝的推论 | 拒绝理由 | 依据 |
|---|---|---|---|
| 1 | DSP、driver、TIA、EML、PIN、lens、FAU 为所有光模块必备 | 本冻结来源只提供实例与"可含"描述，不支持必备性主张 | P3 Glossary、P4 |
| 2 | EML/PIN 产品实例 = 行业共同结构 | EML/PIN 来自 Coherent 官方产品页，属单料号实例 | P4 product-page |
| 3 | Host Interface 与低速管理接口混淆 | 两者适用范围与信号类别不同 | P2 Abstract、§6.1.1 |
| 4 | Media Interface 一概为可拆卸光纤接口 | CMIS 允许高速电或光 media | P2 §6.1.2 |
| 5 | 据年报"电转光/光转电"补出未经来源支持的内部器件顺序 | P1 只有公司级功能口径 | P1 |
| 6 | 由来源缺席推出"某部件绝不是所有模块必备" | 本轮只断言"来源不支持必备性"，不做否定式通则 | attempt-2 合同 #4 |
| 7 | §7.2.1 solder reflow/socket 是 Media Interface 或光纤连接形态 | 该表是 engine-to-CPA-substrate 封装/装配 | attempt-2 合同 #2 |
| 8 | CMIS bridge/forwarding 延伸为"到达远端并反向返回" | §6.2.1.1 只描述 host-side/media-side 间桥接 | 裁决项 2 |
| 9 | 把 I2C/CMIS 管理路径写入高速数据链 | 管理路径与 mission data path 分层 | P2 Abstract、P4、P5 §15 |

---

## 7. 自检矩阵

| # | 检查项 | 本稿回应 |
|---|---|---|
| 1 | 禁止推论 1（器件升格为必备） | d04/d05/d06 限定实例来源并写"来源不支持必备性" |
| 2 | 禁止推论 2（EML/PIN 实例写成行业结构） | d04/d05 boundary 写明单料号；d06 的 CPO 部件与之分离 |
| 3 | 禁止推论 3（Host Interface 与管理接口混淆） | d01/d08 明确接口方向与路径分层 |
| 4 | 禁止推论 4（Media Interface 一概为可拆卸光接口） | d01 保留"高速电或光"；d07 区分电 pigtail（copper cable assembly）与光 pigtail |
| 5 | 禁止推论 5（年报口径补内部器件顺序） | d03 只写公司级功能；内部器件仅出现在 P3/P4 实例主张 |
| 6 | 裁决项 1：字段体显式唯一 `draft_id` | 8 条主张首字段均为 `PQ002-a3-dNN` |
| 7 | 裁决项 2：CMIS 只写 bridge/forwarding，不延伸远端返回 | d02 只写模块内桥接；跨 media 链路由 P1/P4 支撑，不挂 CMIS |
| 8 | §7.2.1 与 media-side 分离 | d07 boundary + 表注 |
| 9 | CPO media-side 只用 §7.3.2/§7.3.4 文本 | d07 evidence 仅这两节 |
| 10 | 注记约束 | 2 条，仅挂 PQ004/PQ005，无新 QID，证据触发 |
| 11 | 数量与字段 | 8 条，9 字段齐全，`would_mark_covered: false` |
| 12 | 停止边界 | 见第 8 节 |

---

## 8. 停止结论

PQ002 覆盖到**功能链层级**即停止：完整 BOM、组件材料、制造工艺、设备、技术路线优劣以及实例内部器件顺序/接口参数细节不回答（属 PQ004–PQ009 方向，分别由第 5 节两条注记挂接具体缺口）。

本稿为 draft-only：未写 `knowledge.yaml`、`research_questions.yaml`、CSV 或任何 canonical；未生成新问题 ID；未改变任何覆盖状态。
