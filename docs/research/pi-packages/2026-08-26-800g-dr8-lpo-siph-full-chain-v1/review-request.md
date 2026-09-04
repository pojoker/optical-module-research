# Kimi / Cursor 只读审核请求

请只读审核 `docs/research/pi-packages/2026-08-26-800g-dr8-lpo-siph-full-chain-v1/`，不得修改任何文件。

优先读取：

1. `run.yaml`
2. `acceptance-contract.md`
3. `agy-search-audit.md`
4. `source-excerpts.md`
5. `route-chain-card.md`
6. `pi-output.md`
7. `pi-adjudication.md`

必要时对照：

- `research_questions.yaml`；
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/route-tradeoff-gate.md`；
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/company-placement-rules.md`；
- `docs/research/pi-packages/2026-08-26-agy-vendor-binding-chase-v1/source-excerpts.md`。

请回答：

1. 是否真的形成“上游原因→条件化优劣→下游物理变化→物理能力→公司证据阶段”的完整链，而不是只把栏目排齐？
2. WQ001–WQ004 candidate 是否各自有机制和两端证据，证据强度是否仍有越级？
3. S5/S6 功耗比较、LPO lower power/cost/latency、host responsibility 与 link-training 代价边界是否正确？
4. component/interface/process/equipment/test 五层是否完整检查，UNKNOWN 是否被正确保留？
5. Hyper/Dust/MACOM/Eoptolink/OIF demo participants 的公司角色和 evidence stage 是否正确，是否混入供应关系或客户推断？
6. 当前是否达到 `complete_chain_draft_with_explicit_unknowns`，还是存在结构性 P0？

输出 `PASS / PASS_WITH_FIXES / FAIL`，列 P0/P1/P2。不得建议 canonical、coverage、正式 RP、WHY、公司群或知识库晋升。
