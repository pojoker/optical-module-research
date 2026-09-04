# Kimi / Cursor 只读审核请求

请审核 `docs/research/pi-packages/2026-08-26-agy-vendor-binding-chase-v1/`，只读，不修改文件。

优先读取：

1. `run.yaml`
2. `shared-contract.md`
3. `source-excerpts.md`
4. `adjudication.md`
5. `pi-handoff.md`
6. `pi-output.md`
7. `pi-adjudication.md`

必要时对照：

- `research_questions.yaml` 中 TQ006–TQ014 与 WQ002–WQ004；
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/company-placement-rules.md`；
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/next-round-acceptance-contracts.md`。

请回答：

1. AGY 原始输出是否经过充分本地核验，是否仍有公司身份、产品、阶段或来源错配？
2. 中际旭创 demo/送测、新易盛 200G/lane demo 与 100G/lane HVM、芯速联 listed_product 的边界是否正确？
3. 芯速联中文产品页 title + body 是否足以形成 exact-product-page SiPh binding，同时仍不证明 GA/量产？
4. 是否应复用现有 `route_service_evidence` 并增加 `evidence_stage`，还是 demo/listed_product 应用另一关系类型？请以最小 schema 变更为标准。
5. Pi 后裁决是否正确处理“两款 listing 不等于同一内部实现”与 QID 映射？
6. 是否允许下一轮以两款芯速联 listing 为检索起点，跑一个“上游约束→路线轴值→条件化优劣→物理变化→公司阶段证据”的 draft-only 闭环？

输出 `PASS / PASS_WITH_FIXES / FAIL`，列出 P0/P1/P2。不得建议 canonical 写入、coverage 变化、WHY 写入、公司群或正式 Route Profile 晋升。
