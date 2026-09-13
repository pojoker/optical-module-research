# PQ001 attempt-3 Codex 最终裁决

裁决日期：2026-08-23
流程结论：`process_pass`
内容结论：`usable_draft_after_explicit_boundary_errata`
知识库动作：无；PQ001 继续 `[待研究]`

## 1. 已通过

- 采用“CMIS 条件骨架 + OSFP 可插拔实例 + 3.2T CPO 反例 + 公司口径”四层来源；
- 所有 CMIS 主张保留 `CMIS-managed transmission module` 条件；
- 高速 Host Interface 与低速 two-wire 管理通信分层；
- card-edge pads ↔ host connector、module 外壳 ↔ host cage 的实体关系准确；
- 标准 OSFP integrated heatsink 与 OSFP-RHS host riding heatsink 分开；
- CPO module 与 ASIC/substrate 仍为不同对象；
- §14.4 只写 module-side optical receptacle/connector guideline，没有扩张 PMD；
- 没有新问题 ID、YAML、知识库写入或覆盖状态变化；
- 0 条研究注记是合理结果：S4 印刷页 47 §5.5 已关闭标准 OSFP 可选额外
  riding heatsink 的安装侧问题；本轮不存在必须派生新问题才能回答 PQ001 的剩余缺口。

## 2. 人工边界修正

草案 3 同时提到标准 OSFP 的“可选额外 riding heatsink”和 OSFP-RHS 的 host-side riding
heatsink，随后在 `boundary` 中笼统写“riding heatsink 属 host”。印刷页 17 的直接“part of the
host”表述针对 OSFP-RHS；复核时进一步检查 S4 印刷页 47 §5.5，该节把标准 OSFP 的可选额外
riding heatsink 放在 OSFP cage 上。因此两类 riding heatsink 都可归在 OSFP 规范的 host/cage
侧，但证据锚点不同，且这个结论只适用于本轮核验的 OSFP/OSFP-RHS 形态。

后续使用时采用以下收窄口径：

> 标准 OSFP module includes integrated heatsink；OSFP-RHS 接触的 riding heatsink 是 host
> 的一部分；标准 OSFP 的可选额外 riding heatsink 安装在 OSFP cage 侧。以上只描述
> OSFP/OSFP-RHS，不推广为所有光模块的共同热边界。

原始输出保持不动，以保留 Pi 的原始审计记录；后续消费必须应用下面的显式勘误：

| 原始位置 | 原始表述 | 有效口径 |
|---|---|---|
| §1 摘要 | “riding heatsink 属主机” | 仅在本轮 OSFP/OSFP-RHS 语境成立，不是全部光模块的通则 |
| 草案 3 `boundary` | “riding heatsink 属 host” | OSFP-RHS 由印刷页 17 支持；标准 OSFP 可选额外件由印刷页 47 §5.5 的 cage 语境支持 |
| §6 第 3 条 | “host 侧 riding heatsink” | 仅指上述两种 OSFP 规范实例，不得推广到其他 form factor |
| §7 实体配对 | “riding heatsink 属 host，配对准确” | 改读为“在本轮核验的 OSFP/OSFP-RHS 两种实例中成立” |
| §5 注记理由 | “heatsink 归属已在边界内闭合” | 改读为“归属由印刷页 17 与印刷页 47 §5.5 分别闭合，因此无需派生研究注记” |

任何脱离这些条件单独复制的“riding heatsink 属 host”全称句均作废。

## 3. 本轮真正得到的边界

可复用的不是“光模块等于一个前面板盒子”，而是条件化接口骨架：

```text
Host system ──高速 Host Interface── [module / bridge] ──Media Interface── remote media
```

它在 OSFP 中落实为 host connector/cage 与 module card-edge/enclosure/receptacle；在该 3.2T CPO
IA 中则落实为近 ASIC、共 substrate/embedded module 与 pigtail。由此可以拒绝把某一形态的
机械实体当成所有光模块的定义。

## 4. 状态

本包可作为 PQ001 的可用研究草案和后续 PQ002/PQ003 的边界上下文，但不写入 canonical，不把
PQ001 标为已覆盖。任何 promotion 仍需问题验收状态机、独立 reviewer 和现有落库阻断全部处理。
