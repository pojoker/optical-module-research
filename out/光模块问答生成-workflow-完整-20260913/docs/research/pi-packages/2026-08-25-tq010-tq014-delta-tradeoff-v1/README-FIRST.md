# TQ010 / TQ014 物理变化与条件化取舍小样

本包使用已通过 reviewer 的五个 Route Profile Seed，验证两件事：

1. 哪些路线差异可以落到现有物理树，哪些只能标 UNKNOWN 或 `UNMODELED`；
2. 没有同条件对照时，TQ014 能否稳定输出 `not_comparable`，并从缺口长出下一层能力/验证问题。

边界：

- draft-only；
- 不补新产品事实；
- 不创建正式 RP、新 QID、coverage、canonical、公司组；
- 不从轴值差异自动推出工序、设备、功耗、成本或公司受益；
- TQ010 可直接进入 TQ011；TQ014 与其并行，不作门闩。

## 阅读顺序

1. `contract.md`
2. `comparison-objects.md`
3. `comparison-source-audit.md`
4. `comparison-rules.yaml` + `comparison-matrix.yaml`
5. `best-of-n-verifier-pilot.md`
6. `candidate-p1.yaml` / `candidate-p2.yaml` / `candidate-p3.yaml` / `candidate-c1.yaml`
7. `candidate-verification-deterministic.yaml` + `candidate-verification-semantic-codebuddy-hy3.yaml`
8. `adjudication-best-of-n.md`
9. `capability-requirement-schema-draft.yaml` + `capability-requirements-draft.yaml`
10. `company-capability-match-pilot.yaml`
11. `company-placeable-graph-draft.yaml` + `company-placeable-tree.md`
12. `review-fixes-round1.md` + `review-fixes-round2.md`
13. `validation-final.yaml`
