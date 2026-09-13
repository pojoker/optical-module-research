# PQ001 attempt-3 研究输出（draft_only）

## 1. PQ001 结论摘要

光模块解决电↔光转换与跨介质传输，边界依规范。CMIS 骨架：Host Interface 是模块/主机间高速电接口，Media Interface 是模块/远端介质间高速电或光接口，Application 作桥接。OSFP：金手指配主机连接器、外壳配机笼、集成散热器属模块、riding heatsink 属主机、光口图示为指引。3.2T CPO 反例：近 ASIC、共基板/嵌板、尾纤，机笼/金手指非必要。年报仅带主体功能口径。

## 2. 三层边界图

```text
        【公司口径 S1/S2】（带主体：电↔光转换；光电子器件+功能电路）——不替代规范边界
                                    │
┌───────────────────────────────────▼──────────────────────────────────┐
│ 层1 条件化骨架（S3 CMIS，仅 CMIS-managed transmission module）        │
│   Host Interface   = module/host system 间高速电接口（§6.1.1）        │
│        ↕ Application = host-side/media-side 间 bridge（§6.2.1.1）      │
│   Media Interface  = module/remote media 间高速电或光接口（§6.1.2）    │
│   高速 mission 接口 ≠ 低速 two-wire host-to-module 管理通信（不同层）   │
└───────────────────────────────────┬──────────────────────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                ▼                                       ▼
┌──────────────────────────────┐   ┌──────────────────────────────────┐
│ 层2 OSFP 可插拔实例（S4）      │   │ 层3 3.2T CPO 反例（S5）           │
│ module：card-edge pads ↔      │   │ module：近 switch ASIC；可与 ASIC │
│         host connector（§3.5） │   │         共 Co-Packaged Assembly  │
│ module：外壳 ↔ host cage       │   │         Substrate（仍不同对象），  │
│   （Scope 与 host 侧分列）      │   │         或 embedded on board     │
│ module：integrated heatsink   │   │ 光侧：pigtail，最终 optical      │
│         （标准 OSFP includes）  │   │         connector 位置/实现未固定 │
│ module：60-contact edge       │   │ 结论：前面板 cage/card-edge 不是  │
│         connector（§15，承载    │   │         所有模块的必要边界        │
│         高速 TX/RX、低速控制等）│   │                                  │
│ host：riding heatsink         │   │                                  │
│         （OSFP-RHS 接触，属 host）│   │                                  │
│ module-side optical receptacle：│   │                                  │
│         §14.4 图示为 guideline  │   │                                  │
└──────────────────────────────┘   └──────────────────────────────────┘
```

## 3. 系统边界表

| 条目 | 来源 | 归属（module 侧 / 系统侧） | 条件 | 拒绝的推论 |
|---|---|---|---|---|
| 条件骨架 | S3 | module/host 间：Host Interface（高速电）；module/remote media 间：Media Interface（高速电或光）；Application 为 bridge/forwarding | 仅 CMIS-managed transmission module | 推广到所有光模块；Host Interface=管理接口；media 必为光 |
| OSFP 电/机械 | S4 | module：card-edge pads、外壳、60-contact edge connector；host：host connector（§5.10）、host cage、host PCB layout | 仅 OSFP/OSFP-RHS | card-edge 与 cage 直接配对；cage/connector/PCB 写入 module 本体 |
| OSFP 热/光口 | S4 | module：integrated heatsink（标准 OSFP includes）；host：riding heatsink（OSFP-RHS 接触，属 host）；module-side receptacle 图示为 guideline | 仅 OSFP/OSFP-RHS | “标准 OSFP 无 integrated heatsink 归属不明”；§14.4 扩张为 PMD 完整定义 |
| CPO 反例 | S5 | module：近 ASIC、共 substrate 或 embedded on board；光侧 pigtail，最终 optical connector 位置/实现未固定；ASIC/substrate 为系统侧不同对象 | 仅 OIF 3.2T Co-Packaged Module IA | 所有 CPO 均无 cage/card-edge；ASIC/substrate 属 module；唯一路线 |
| 公司口径 | S1/S2 | 中际旭创：发端电转光、收端光转电（经光纤）；博创：光电子器件+功能电路等，收发与光电转换 | 仅对应发布主体 | 行业统一定义、标准接口、机械边界、完整 BOM |
| 不可泛化项 | 组合规则 | 实例机械实体不构成共同 BOM；OIF IA 目录快照仅版本核验；QSFP-DD Rev 7.1 未冻结不使用 | 全部来源包 | OSFP=全部、CMIS=全部、机械归属固定 |

## 4. 原子主张草案

**草案 1**
- **draft_id**：`a3-d01`
- **system**：物理知识
- **question_id**：PQ001
- **claim_type**：CMIS规范事实
- **statement**：在 CMIS-managed transmission module 条件下，mission-related physical interfaces 为 Host Interface 与 Media Interface；Host Interface 是 module/host system 间的高速电接口，Media Interface 是 module/remote media 间的高速电或光接口；Application 是 host-side/media-side 间的 bridge/forwarding function。CMIS 亦适用于带 two-wire host-to-module management communication 的模块开发，该低速管理通信与 mission-related 高速接口属不同层。
- **evidence_ids**：S3（OIF-CMIS-05.4；Abstract p.3；印刷页 65 §6；印刷页 66 §6.1/§6.1.1/§6.1.2；印刷页 67 §6.2.1.1）
- **boundary**：仅 CMIS-managed transmission module；resource module/cable assembly 有例外；不延伸 enclosure/cage/connector/heatsink。
- **rejected_inference**：不得推广为所有光模块的骨架或边界；不得把 Host Interface 与低速 two-wire 管理通信混淆；不推出 media 必为光。
- **would_mark_covered**：false

**草案 2**
- **draft_id**：`a3-d02`
- **system**：物理知识
- **question_id**：PQ001
- **claim_type**：OSFP规范事实
- **statement**：OSFP 规范把 module form factor 与 host cage/mating connector、host PCB layout 分列；module PCB 的 card-edge contact pads 与 §5.10 host connector 配合，module 外壳与 host cage 配合；§15 的 60-contact module edge connector 承载高速 TX/RX、低速控制、供电与地。
- **evidence_ids**：S4（OSFP Module Specification Rev 5.22；印刷页 17 §1；印刷页 30 §3.5；印刷页 159–160 §15）
- **boundary**：仅 OSFP/OSFP-RHS form factor 实例。
- **rejected_inference**：不得写成 card-edge 与 cage 直接配对；不得把 host cage、host connector、host PCB 写入 module 本体；不得拼成共同 BOM。
- **would_mark_covered**：false

**草案 3**
- **draft_id**：`a3-d03`
- **system**：物理知识
- **question_id**：PQ001
- **claim_type**：OSFP规范事实
- **statement**：标准 OSFP/OSFP800/OSFP1600 module includes air-cooled integrated heatsink，并可选的额外 riding heatsink；OSFP-RHS 系列接触属于 host 的 riding heatsink。§14.4 展示 module-side optical receptacle 与 channel orientation，Duplex LC 等 connector 方案是可用示例，图示 meant to be guidelines，实际 module/connector 几何可不同。
- **evidence_ids**：S4（OSFP Module Specification Rev 5.22；印刷页 17 §1；印刷页 146 §14.4）
- **boundary**：仅 OSFP/OSFP-RHS；integrated heatsink 属 module，riding heatsink 属 host。
- **rejected_inference**：不再提出“标准 OSFP 无 integrated heatsink 时归属不明”；§14.4 只回答 module-side receptacle/connector guideline，不判定整份 OSFP 规范是否完整定义光学 PMD。
- **would_mark_covered**：false

**草案 4**
- **draft_id**：`a3-d04`
- **system**：物理知识
- **question_id**：PQ001
- **claim_type**：CPO规范事实
- **statement**：OIF 3.2T Co-Packaged Module IA 中，optical module 把 short-reach electrical 转为 optical I/O；module 近 switch ASIC，可与 ASIC 同处 Co-Packaged Assembly Substrate（仍为不同对象）或 embedded on board；光侧为 pigtail，最终 optical connector 位置/实现未由 IA 固定。
- **evidence_ids**：S5（OIF-Co-Packaging-3.2T-Module-01.0；印刷页 7 §1；印刷页 9–10；印刷页 24 §6）
- **boundary**：仅该特定 IA 展示的不以前面板 cage/card-edge 为必要边界的实现；ASIC/substrate 属系统侧。
- **rejected_inference**：不得绝对化“所有 CPO 均无 cage/card-edge”；不得把 ASIC/substrate 写入 module 本体；不得推出所有光模块 embedded/pigtail 或唯一技术路线。
- **would_mark_covered**：false

**草案 5**
- **draft_id**：`a3-d05`
- **system**：物理知识
- **question_id**：PQ001
- **claim_type**：公司口径
- **statement**：中际旭创 2024 年年报：发送端电转光，经光纤传送后接收端光转电；博创科技 2024 年年报：光模块由光电子器件和功能电路等组成，实现收发与光电转换。
- **evidence_ids**：S1（corpus/annual-2024/300308/…txt:152-155）；S2（corpus/annual-2024/300548/…txt:160-164）
- **boundary**：仅对应发布主体的功能/构成口径；S1 中的光纤传送属该口径的介质路径表述。
- **rejected_inference**：不构成行业统一定义、标准接口或机械边界；不支撑完整 BOM 或“所有模块相同”。
- **would_mark_covered**：false

## 5. 研究注记

0 条。说明：本轮全部原子主张皆由冻结来源的完整上下文直接支持（CMIS 骨架、OSFP 电/机械/热/光口、CPO 反例、公司口径均已在 sources-attempt-3.md 给出印刷页/锚点完整上下文）；heatsink 归属、§14.4 范围、CPO 绝对化等疑点已在边界与拒绝推论内闭合，不存在“冻结来源完整上下文仍无法解决”的证据触发，故不产生需挂 PQ001/PQ003 的注记。

## 6. 拒绝的推论

1. **拒绝「OSFP=全部」**：S4 只定义 OSFP/OSFP-RHS form factor 的边界，不得推广为所有光模块共用 cage/card-edge/receptacle。
2. **拒绝「CMIS=全部」**：S3 骨架仅在 CMIS-managed transmission module 条件下成立，resource module/cable assembly 有例外；CMIS 不定义 enclosure/cage/connector/heatsink，不等于物理边界全集。
3. **拒绝「机械归属固定」**：OSFP（card-edge+cage+integrated heatsink）与 3.2T CPO（近 ASIC/substrate/embedded+pigtail）的机械边界机制不同，归属随实例与规范而定；host 侧 cage、host connector、riding heatsink、host PCB 不得写入 module 本体。
4. **拒绝「Host Interface=管理接口」**：Host Interface 是 mission-related 高速电接口，与低速 two-wire host-to-module 管理通信分属不同层。
5. **拒绝「card-edge 与 cage 直接配对」**：正确配对是 card-edge pads ↔ host connector（§3.5），cage 与 module 外壳配合。
6. **拒绝「标准 OSFP 无 integrated heatsink 归属不明」**：来源明确 includes。
7. **拒绝「所有 CPO 均无 cage/card-edge」**：S5 仅展示该特定 IA 不以前面板 cage/card-edge 为必要边界的实现。
8. **拒绝「§14.4 扩张为 PMD 完整定义」**：该节只回答 module-side optical receptacle/connector guideline。
9. **拒绝「公司口径替代规范边界」**：S1/S2 为带主体功能口径，不构成标准接口或机械边界；也不得拼成共同 BOM。

## 7. 自检矩阵

| 检查项 | 结果 |
|---|---|
| 体系 | 物理知识；S3 条件骨架、S4/S5 实例、S1/S2 公司口径分层归位，未混用 |
| QID | 全部主张 question_id=PQ001；无新增问题 ID |
| 锚型 | 主张均挂 S1–S5 原始锚型（local_file/web_snapshot）与锚/印刷页完整上下文 |
| 条件 | 每条主张保留条件：CMIS-managed transmission module、OSFP/OSFP-RHS、OIF 3.2T CPO IA、对应公司主体 |
| 实体配对 | card-edge pads↔host connector、外壳↔cage、integrated heatsink 属 module、riding heatsink 属 host，配对准确 |
| 接口层级 | mission-related 高速 Host/Media 接口与低速 two-wire 管理通信分层；OSFP §15 高速 TX/RX、低速控制、供电与地分层保留 |
| 上下文 | §14.4 只答 guideline；标准 OSFP includes integrated heatsink 无伪缺口；CPO 只作特定 IA 反例不绝对化 |
| 注记必要性 | 0 条；无冻结来源完整上下文无法解决的事项 |
| 覆盖状态 | 全部 would_mark_covered=false；不改覆盖状态、不写文件、无 YAML |

## 8. 停止结论

本轮 attempt-3 为 draft-only 受控研究，其结论由本轮冻结来源（S1–S5）与条件边界（CMIS 骨架、OSFP/OSFP-RHS 实例、OIF 3.2T CPO 反例、公司口径）约束。这些局部条件只对本轮输出成立，不成为其他 draft-only 轮次的门闩；其他轮次应依据各自冻结来源独立评估，不得引用本轮的实例机械实体或条件作为前置锁闭。
