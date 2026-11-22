# Kimi 只读审核：AGY vendor binding chase v1

- reviewer: Kimi Code
- model: `kimi-code/k3`
- verdict: `PASS_WITH_FIXES`
- P0: none

## 六项结论

1. 本地核验基本充分：冻结摘录包含 URL、页码、短引文、字节数与 SHA256；`T-OL8CNT-N00` 非 SiPh、芯速联不等于光梓信息、新易盛两个 SKU 无一手 SiPh 绑定均已纠正。
2. 阶段边界正确：中际旭创为 demo/送测，新易盛 200G/lane 为 demo 且不得继承 100G/lane HVM，芯速联为 listed_product 且 GA/量产/出货 UNKNOWN。
3. 芯速联中文页 title + body 足以形成同页 exact-product-page binding，但这是对原“单句”门槛的扩展，且不证明 GA/量产。
4. 最小 schema 是复用 `route_service_evidence` 并增加 `evidence_stage`；阶段升级追加记录，confirmed group 另设闸门。
5. Pi 后裁决对“配对 listings 不等于同族/同实现”及 Q1/Q6/Q8 的 QID 重映射正确。
6. 允许下一轮 draft-only 闭环；必须先证同条件，否则 TQ014 输出 `not_comparable`，不得新建 QID 或晋升知识库。

## P1

- 将 `exact_product_page_binding` 的 title+body 同页门槛书面化，并记录英文页缺少平台标签时的处理。
- 中际旭创 OFC2023/OFC2024 未冻结 PR 卡需显式标记不消费或后续冻结核验。

## P2

- 更新已完成 Pi/审核后的 run status。
- 新易盛 AGY 改写与冻结原文不一致时只消费冻结文本。
- 芯速联英文页无 SiPh/PIC，SiPh 锚仅中文页。
- 中际旭创产品族 SiPh demo 与 EML SKU 可并存，不能读成全族 SiPh。
- Pi 正文旧映射应以 `pi-adjudication.md` 为准。

结论：修正后允许以两款芯速联 exact listings 为检索起点，继续“上游约束→路线轴值→条件化优劣→物理变化→公司阶段证据”的 draft-only 闭环。
