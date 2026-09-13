# Cursor 对 PQ001 draft-only 研究包的只读审核

审核日期：2026-08-23
审核模式：Ask / read-only
最终结论：`accepted`
知识库动作：无

## 第一轮：changes_requested

第一轮认可 CMIS 条件、card-edge/connector/cage 分型、CPO 反例范围以及无 canonical 写入，
但认为旧裁决只在一段文字中收窄了 riding heatsink，没有逐一覆盖原稿中的摘要、草案 3
`boundary`、拒绝推论和自检。下游若只读原稿，仍可能把“riding heatsink 属 host”误当作
全部光模块的通则。

第一轮还指出，0 条研究注记的理由不能写成未分型的“heatsink 归属已闭合”；要么提供
标准 OSFP 可选 extra riding heatsink 的证据，要么明确拒绝该主张。

## 修订

`adjudication.md` 随后增加逐位置显式勘误，并核入冻结 S4 的两处不同证据：

- 印刷页 17：OSFP-RHS 接触的 riding heatsink 是 host 的一部分；
- 印刷页 47 §5.5：标准 OSFP 的可选 extra riding heatsink 位于 OSFP cage 侧。

裁决同时规定：上述判断只适用于本轮核验的 OSFP/OSFP-RHS；任何脱离条件单独复制的
“riding heatsink 属 host”全称句作废。

## 第二轮：accepted

Cursor 复核后确认：

1. 摘要、草案 3 `boundary`、§6 第 3 条和自检均已有可执行覆盖口径；
2. 0 条注记改由印刷页 17 与印刷页 47 §5.5 分别闭合，内部一致；
3. `run.yaml` 仍为 `draft_only`、`canonical_write_allowed: false`；
4. `knowledge.yaml` 无 PQ001 关联，`research_questions.yaml` 中 PQ001 未被本包改写。

残余阻断：无。不落库。
