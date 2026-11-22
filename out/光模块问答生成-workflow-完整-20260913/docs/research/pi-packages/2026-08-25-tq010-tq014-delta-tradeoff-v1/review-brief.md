# Reviewer brief

请只读审查本包，不修改任何文件。禁止读取 `archive/`。

重点文件：

- `contract.md`
- `comparison-source-audit.md`
- `comparison-matrix.yaml`
- `adjudication-best-of-n.md`
- `capability-requirement-schema-draft.yaml`
- `capability-requirements-draft.yaml`
- `company-facet-rules-draft.yaml`
- `company-capability-match-pilot.yaml`
- `company-placeable-graph-draft.yaml`
- `company-placeable-tree.md`
- `best-of-n-verifier-pilot.md`
- `candidate-verification-deterministic.yaml`
- `candidate-verification-semantic-codebuddy-hy3.yaml`

只读引用：根目录 `tree.yaml`、`points.csv`；不要读取 canonical knowledge/coverage 文件的内容，除非为了检查是否被改动，只允许看 `git diff --name-only`。

请回答：

1. 两套知识体系（物理知识、技术路线）是否被正确分开？WHY 是否只作为有证据的桥，而没有被臆造？
2. `route_product_attribute`、`physical_capability_requirement`、`validation_gap` 三分法是否足以阻止公司错误归群？
3. 五个 physical requirements、两个 product attributes、两个 validation gaps 是否严格受冻结证据支持？
4. 56 个 point 的 facet/role 关键词提议是否存在明显误报、漏报或错误角色？特别检查 role 不应由 cell 自动推断。
5. `candidate_match` 是否被清楚限制为字段重合，而非供应/客户/服务路线事实？
6. Best-of-N 实验的结论是否诚实：哪些增益有效，哪些 verifier 仍不可靠？
7. 是否足以进入下一轮“受控 trade-off / WHY 证据研究”，仍保持 draft-only？

输出 `PASS` 或 `FAIL`，并列出必须修复项、建议项、你亲自核到的文件/行或 point_id。不要泛泛总结。
