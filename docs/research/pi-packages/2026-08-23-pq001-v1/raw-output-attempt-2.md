# PQ001 研究输出（attempt-2，draft-only）

## 1. PQ001 结论摘要

对 CMIS-managed transmission module：核心问题是把 host 电信号与远端介质信号互转，并经 bridge 功能连接两侧。骨架层：Host Interface 与 Media Interface 为任务相关物理接口；实例层：OSFP 以 card-edge 配 host cage，heatsink 归属依形态，光接口仅 guideline；反例层：OIF 3.2T CPO IA 中 module 近 ASIC、共 substrate 或 embedded，光经 pigtail。三层不可互推，机械边界不由单一形态固定。

## 2. 三层边界图

```
【骨架层】（S3，条件限 CMIS-managed transmission module）
Host System ──Host Interface(高速电)──> [module：Application = bridge/forwarding] ──Media Interface(高速电或光)──> 远端互连介质
注：承载管理协议的低速 MCI/TWI 不是 §6.1 的 Host Interface 层

【OSFP 实例】（S4）
电：host PCB/ASIC ──host connector ←→ module card-edge pads（60-contact，含高速 TX/RX、低速控制、供电、地）
机械：host cage ←→ module 外壳
热：integrated heatsink 可属 module；OSFP-RHS 的 riding heatsink 属 host
光：module 侧光接口（§14.4 仅 guideline）──> 外部光连接

【CPO 反例】（S5，OIF 3.2T IA）
Switch ASIC ──short-reach electrical──> [module（近 ASIC；module 与 ASIC 同处 Co-Packaged Assembly Substrate 或 module
embedded on board，仍为不同对象）] ──pigtail(optical)──> 最终光连接器（IA 未固定）
差异：无前面板 cage/card-edge；media-side 衔接经 pigtail 延伸至他处。
```

## 3. 系统边界表

| 层级/项 | 边界表述 | 来源 | 不可泛化点 |
|---|---|---|---|
| 通用骨架 | CMIS-managed transmission module 的任务相关物理接口为 Host Interface（module 与 host system 间的高速电接口）与 Media Interface（module 与远端互连介质间的高速电或光接口）；Application 是 host-side 与 media-side 信号间的 bridge/forwarding | S3（§6、§6.1、§6.1.1、§6.1.2、§6.2.1.1） | 仅该条件成立；Host Interface 不是低速管理接口；接口表述不推出机械形态 |
| OSFP 实例 | 电：60-contact edge connector/card-edge pads 与 host connector 配合，承载高速 TX（host→module）、RX（module→host）、低速控制、供电、地；机械：module 与 host cage 配合；热：integrated heatsink 可属 module、OSFP-RHS riding heatsink 属 host；光：§14.4 仅为 guideline | S4（Scope、§3.5、§14.4、§15） | 只适用于 OSFP/OSFP-RHS；cage/card-edge/heatsink 归属不推广到 CPO、on-board 或全部模块；光接口形态非强制 |
| CPO 反例 | 16 个 module 近 switch ASIC；module 把 short-reach electrical interface 转换为 optical I/O；module 与 ASIC 可同处 Co-Packaged Assembly Substrate，仍为不同对象；module 可 embedded on board；host side 电、line side 光，光经 pigtail，最终 optical connector 未由 IA 固定 | S5（§1、页 9–10、§6） | 仅该 3.2T IA；ASIC 不归 module；embedded/pigtail 不推广为所有 CPO 或所有模块形态 |
| 公司口径层 | 中际旭创与博创科技均表述光模块发送端电转光、接收端光转电的双向转换；博创另表述模块由光电子器件和功能电路等组成 | S1、S2 | 带发布主体的公司口径，非行业统一定义、非标准边界、非 BOM |
| 不可泛化项 | 前面板 cage/card-edge≠通用边界；pigtail/receptacle≠共同 media-side 衔接形态；heatsink 归属依实例形态而定；media≠必为光纤 | S3/S4/S5 对照 | 各结论只能回到对应主体、条件、实例复用 |

## 4. 原子主张草案

**draft_id**：`PQ001-attempt2-draft-01`
**system**：物理知识
**question_id**：PQ001
**claim_type**：CMIS规范事实
**statement**：对 CMIS-managed transmission module，其任务相关物理接口为 Host Interface 与 Media Interface；Host Interface 是 module 与 host system 间的高速电接口，Media Interface 是 module 与远端互连介质间的高速电或光接口；Application 是 host-side 与 media-side 信号间的 bridge/forwarding 功能。
**evidence_ids**：S3（§6、§6.1、§6.1.1、§6.1.2、§6.2.1.1）
**boundary**：条件逐字保留为"CMIS-managed transmission module"；Host Interface 指高速数据接口；Media Interface 为"电或光"，不断言必为光纤。
**rejected_inference**：不推广为所有语境中的光模块；不将 Host Interface 与承载管理协议的低速 MCI/TWI 混为同一层；不由接口表述推出 cage/connector/receptacle/pigtail 等机械形态。
**would_mark_covered**：false

---

**draft_id**：`PQ001-attempt2-draft-02`
**system**：物理知识
**question_id**：PQ001
**claim_type**：OSFP规范事实
**statement**：OSFP 规范 Scope 分列 OSFP module、host cage/mating connector、host PCB layout 与热要求；module 以 PCB card-edge pads 与 host connector 配合；标准 OSFP 可有 integrated heatsink，OSFP-RHS 的 riding heatsink 属 host（"part of the host"）；可用于 OSFP module 的外部光接口仅以 §14.4 guideline 给出。
**evidence_ids**：S4（Scope、§3.5、§14.4）
**boundary**：仅 OSFP/OSFP-RHS 可插拔形态；heatsink 归属依形态（integrated 可属 module、RHS riding 属 host）；光接口为 guideline。
**rejected_inference**：不把 cage/card-edge/integrated heatsink 推广到 CPO、on-board optics 或所有模块；不把 guideline 当成 OSFP 强制光接口形态；不把"card-edge pads"推广为所有模块的电边界。
**would_mark_covered**：false

---

**draft_id**：`PQ001-attempt2-draft-03`
**system**：物理知识
**question_id**：PQ001
**claim_type**：CPO规范事实
**statement**：在 OIF 3.2T Co-Packaged Module IA 中，optical module 把面向 switch ASIC 的 short-reach electrical interface 转换为 optical I/O；module 位于 close proximity to the switch ASIC，可与 ASIC 同处 Co-Packaged Assembly Substrate（仍为不同对象），甚至 "may be embedded on the board"；module host side 为 electrical、line side 为 optical，光侧经 pigtail 延伸，最终 optical connector 未由该 IA 固定。
**evidence_ids**：S5（§1、页 9–10、§6）
**boundary**：仅该 3.2T CPO IA；module 与 ASIC 近邻/共 substrate 但对象分离；该实例不依赖前面板 cage/card-edge。
**rejected_inference**：不把 ASIC 或 host substrate 写成 module 本体；不把 embedded/pigtail 推广为所有 CPO 或所有光模块形态；不把该 IA 当作唯一路线或普适边界依据。
**would_mark_covered**：false

---

**draft_id**：`PQ001-attempt2-draft-04`
**system**：物理知识
**question_id**：PQ001
**claim_type**：公司口径
**statement**：中际旭创（S1）与博创科技（S2）在 2024 年年度报告中均表述：光模块在发送端把电信号转换为光信号、经光纤传送后接收端再把光信号转换为电信号，实现双向光电转换；博创另表述光模块由光电子器件和功能电路等组成。
**evidence_ids**：S1、S2
**boundary**：带发布主体的公司口径；描述模块在电↔光转换中的系统作用与构成层级，不预设 Host/Media 标准接口或机械形态。
**rejected_inference**：不将两家公司口径上升为行业统一定义；不由"光电转换"推出完整 BOM、工艺或标准边界；不用 S1/S2 充当 Host/Media 接口层依据。
**would_mark_covered**：false

---

**draft_id**：`PQ001-attempt2-draft-05`
**system**：物理知识
**question_id**：PQ001
**claim_type**：CMIS规范事实
**statement**：CMIS 基于 two-wire host-to-module management communication 支持模块开发，且可用于 pluggable 或 on-board modules。
**evidence_ids**：S3（Abstract）
**boundary**：描述 CMIS 适用范围与低速管理信道形态；不限定模块的可插拔性。
**rejected_inference**：不推出"所有光模块都实现 CMIS"或"CMIS-managed 必为 pluggable"；不把低速 two-wire 管理通信当作 §6.1 的 Host Interface。
**would_mark_covered**：false

## 5. 研究注记

先以冻结材料完整上下文尝试解决下列候选粒度问题，两处均无法由现有证据闭合；其余候选可由现有证据解决或不影响本轮结论，故不发注记。共 2 条，少于 3 条属正常结果。

**注记 1**（挂层：PQ001）
- 证据触发：S4 对 §14.4 的冻结表述仅为"可用于 OSFP module 的光接口图示为 guidelines"，未含该页图示的衔接实体细节（是否含模块侧 receptacle、连接器类型、安装位置）。
- 层级理由：属 PQ001 的 media-side 边界粒度。本轮结论只能把 OSFP 光接口限定为"guideline、非强制形态"并区分于 CPO 的 pigtail，无法在 promotion 粒度回答"OSFP 光介质具体从哪里衔接"。
- 下一步：后续受控轮次读取 OSFP Rev 5.22 印刷页 146 §14.4 完整页上下文（不联网、不运行工具），逐字记录图示与实际衔接实体。
- 停止条件：若该页给出明确衔接实体（如 receptacle 或指定连接器），则更新 OSFP 行边界表述；若确认仅保持 guideline 而不固定形态，则将"OSFP 光接口形态不固定"固化为来源边界并关闭本注记。

**注记 2**（挂层：PQ001）
- 证据触发：S4 摘要"标准 OSFP 可有 integrated heatsink，OSFP-RHS 的 riding heatsink 属 host"中"可有"留下未确定态——标准 OSFP 不带 integrated heatsink 时的散热/热边界归属未在冻结材料中表述。
- 层级理由：属 PQ001 的热边界归属粒度。本轮只能断言 heatsink 归属依实例而定，不能无证据断言"标准 OSFP 无集成散热时必由 host 承担"。
- 下一步：后续受控轮次读取 OSFP 规范 Scope 与热要求章节完整页，确认标准形态下热边界/散热件归属表述。
- 停止条件：若找到标准 OSFP 无 integrated heatsink 时的归属语句，则纳入边界表；若规范对归属不作强制规定，则在边界表注明"归属未由规范统一固定"并关闭本注记。

## 6. 拒绝的推论

1. **拒绝"OSFP=全部"**：OSFP 的 cage/card-edge/integrated heatsink 均按 S4 限定在 OSFP/OSFP-RHS 形态；S5 的 3.2T CPO 模块无前面板 cage/card-edge 即不成立；S3 Abstract 亦表明 CMIS 覆盖 pluggable 与 on-board。推论"所有光模块都有 cage/card-edge 边界"无证据支持。
2. **拒绝"CMIS=全部"**：CMIS 骨架仅在"CMIS-managed transmission module"条件下成立（S3 §6 默认 transmission module，resource module、cable assembly 等有例外）；S1/S2 公司口径描述模块功能时不含 CMIS 条件。推论"所有光模块都是 CMIS-managed transmission module"无证据支持。
3. **拒绝"ASIC/cage/heatsink 归属无条件固定"**：S5 中 module 与 ASIC 近邻/共 substrate 但仍是可区分对象，ASIC 不属于 module 本体；S4 中 cage/mating connector 属 host，heatsink 依形态归属（integrated 可属 module、RHS riding 属 host）。推论"ASIC 必归 module"或"heatsink 必归单一侧"均无证据支持。
4. **拒绝"media 必为光纤、media-side 衔接必为同一连接器形态"**：S3 表述 Media Interface 是高速电或光接口；S4 光接口仅 guideline；S5 光经 pigtail 且最终 connector 未固定。推论"receptacle 或 front-panel connector 是所有模块共同的 media-side 形态"无证据支持。
5. **拒绝"Host Interface=低速管理通信"**：S3 §6.1.1 明确定义 Host Interface 为高速电接口；承载管理协议的低速 MCI/TWI（two-wire）是另一层。推论"管理接口即 Host Interface"属层级混淆。

## 7. 自检矩阵

| 检查项 | 结果 | 说明 |
|---|---|---|
| 体系 | 通过 | 5 条草案 `system` 全为 `物理知识`；正文无 BOM、工艺、技术路线、WHY、公司能力群、供货投资内容 |
| QID | 通过 | 草案 `question_id` 全为 PQ001；注记挂 PQ001；未新增问题 ID |
| 锚型 | 通过 | 引用仅来自 S1–S5 中 admissible 来源，锚型与来源包一致（S1/S2 为 local_file 定期报告，S3/S4/S5 为 web_snapshot 规范/IA） |
| 条件 | 通过 | CMIS 骨架保留"CMIS-managed transmission module"条件；OSFP/CPO 主张限定对应规范/IA 主体；未把特定机械实体推广为通用边界 |
| 接口层级 | 通过 | 高速 Host Interface 与低速管理（MCI/TWI、低速控制引脚）未混为同层 |
| 完整上下文 | 通过 | 各主张均在来源"重点上下文"的完整节/页范围内表述，无短引扩张 |
| 注记必要性 | 通过 | 2 条注记均满足证据触发+实质缺口+可执行下一步+可判定停止条件+正确挂层；可由现有证据解决的问题未发注记 |
| 覆盖状态 | 通过 | 全部 `would_mark_covered` 为 false；未输出 append-ready YAML；未声称 PQ001 已覆盖或改变问题覆盖状态 |

## 8. 停止结论

本轮局部停止条件为：在冻结来源集合内，PQ001 三层边界（条件化骨架、OSFP 实例、CPO 反例）已能以 draft-only 方式表达，且"OSFP=全部""CMIS=全部""ASIC/cage/heatsink 归属无条件固定"三类推论均已拒绝。该停止仅关闭本轮 PQ001 草案的增量写作；它不构成其他 draft-only 轮次（PQ002、PQ003 或未来 PQ001 再验证轮）的全局门闩，也不因注记 1、2 尚未达到停止条件而阻止其他轮次推进。
