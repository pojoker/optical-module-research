# Kimi / Cursor 只读审核请求

请审核 `docs/research/pi-packages/2026-08-26-agy-route-field-fill-v2/`，只读，不修改任何文件。

优先读取：

1. `run.yaml`
2. `pilot-v1-audit.md`
3. `adjudication.md`
4. `source-excerpts.md`
5. `pi-handoff.md`
6. `pi-output.md`
7. `pi-adjudication.md`

必要时对照：

- `research_questions.yaml`
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/post-adjudication-effective-text.md`
- `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/contract.md`
- `docs/research/pi-packages/2026-08-25-tq010-tq014-delta-tradeoff-v1/contract.md`

请回答：

1. 是否守住 AGY search result 不等于证据、generated synthesis 不晋升的边界？
2. EML 产品系列字段与 exact SKU、GA、TEC、FEC、内部实现边界是否正确？
3. SiPh `FAIL_NO_SINGLE_INSTANCE` 是否被正确限制为本轮搜索失败，而非产业负向事实？
4. evidence subject 四层模型是否与现有 Route Profile 兼容，还是重复/错层？
5. Pi 的 4 条注记裁决成“1 新 + 3 合并”是否正确？
6. 是否允许下一步做 2–3 家厂商的 AGY exact-entity source chase，并继续保持 draft-only？

输出 PASS / PASS_WITH_FIXES / FAIL，列出 P0/P1/P2。不得建议 canonical 写入、覆盖状态变更、WHY、公司群或正式 Route Profile promotion。
