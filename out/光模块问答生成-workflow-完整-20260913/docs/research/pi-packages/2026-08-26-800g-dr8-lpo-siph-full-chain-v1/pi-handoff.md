# Pi handoff：800G DR8 LPO SiPh 完整路线链

只允许消费本包以下文件：

1. `acceptance-contract.md`
2. `source-excerpts.md`
3. `route-chain-card.md`

不得消费 AGY 原始总结，不得联网或调用工具。

## 任务

将现有完整路线链重排为可机器检查的草稿结构，并审计是否真的覆盖：

```text
上游原因
→ 条件化优势/代价
→ 下游物理变化
→ 物理能力
→ 公司路线证据阶段
```

## 强制输出

1. 一段 Markdown 总结；
2. 一个且仅一个 YAML fenced block，根键为 `route_chain_draft`；
3. 四条 WHY candidate，分别对应 WQ001–WQ004；
4. 每个节点包含：`qid`、`claim`、`claim_status`、`conditions`、`evidence_refs`、`limitations`；
5. `tradeoff` 必须包含 advantages、costs、new_bottlenecks、alternatives、not_comparable_fields；
6. `physical_changes` 必须分别包含 component/interface/process/equipment/test；
7. `company_evidence` 必须包含 role、company、evidence_subject、evidence_stage、coverage_limit；
8. 最后给出 requirement-by-requirement completion audit。

## 禁止

- 不补 UNKNOWN；
- 不把 design target、consortium statement、product observation 混成事实；
- 不把 S6/S5 的功耗差归因于单一变量；
- 不把 Dust/MACOM 组件装入 Hyper 模块；
- 不创建新 QID、正式 RP、WHY、公司群、coverage 或 canonical write；
- 不给公司排名或客户推断。
