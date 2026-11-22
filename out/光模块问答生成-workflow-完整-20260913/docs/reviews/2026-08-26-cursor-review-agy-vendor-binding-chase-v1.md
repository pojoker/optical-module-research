# Cursor 只读审核：AGY vendor binding chase v1

- reviewer: Cursor
- model: `auto`
- mode: `ask` / read-only
- verdict: `PASS_WITH_FIXES`
- P0: none

## 六项结论

1. 有效消费链应固定为 `source-excerpts.md → adjudication.md → pi-handoff.md → pi-adjudication.md`；AGY raw 只作检索日志。现有身份、产品和阶段错配已被纠正。
2. 中际旭创 demo/送测、新易盛 200G/lane demo 与 100G/lane HVM、芯速联 listed_product 的边界正确。
3. 芯速联中文页同页 title + body 可做 draft exact-product-page SiPh binding，但强度低于单句 SKU+SiPh，不能证明 GA/量产。
4. 复用 `route_service_evidence + evidence_stage` 是最小变更；confirmed service group 必须保持独立门闸。
5. Pi 后裁决正确：两款 listing 不等于同一实现；Q1/Q6/Q8 重映射合理；8 条只是现有合同 refinement。
6. 允许下一轮 draft-only 闭环，必须保留 `not_comparable` 退路及全部禁止晋升项。

## P1

- 未冻结的一手 PR 不得回流，只消费冻结来源。
- Pi 中“同一族”残留必须由 `pi-adjudication.md` 的“配对 exact listings”覆盖。
- QID 以裁决后的映射为准。
- 芯速联 SiPh 绑定上限是中文 title + 同页 SKU，不能借此升级成熟度。

## P2

- 更新 `run.yaml` 状态。
- “唯一”只限本轮样本；`FNT` 保持 raw label。

结论：`PASS_WITH_FIXES`，允许下一轮 draft-only 闭环。
