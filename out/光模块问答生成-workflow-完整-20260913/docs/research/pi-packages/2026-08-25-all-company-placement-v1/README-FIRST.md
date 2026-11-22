# 全量公司数据挂载草稿 v1

目标：证明当前 `points.csv` 的全部 271 个公司证据点都能进入同一棵“物理知识 × 技术路线 × WHY”图，而不把关键词、子公司、产品阶段或格位重合误写成路线服务事实。

本包只做 draft-only 规范化：

- `tree.yaml` 的物理格保持不变；
- `points.csv` 保持不变；
- facet 是格内候选刻面，不是 canonical cell；
- company string 暂不冒充稳定 company ID；
- 每个 facet/role 保留引语 span；
- point 的“生产中/在建”不自动继承给每个 facet；
- 参股/子公司/收购业务保留主体范围；
- 不生成公司路线集团、供应、客户或受益结论。

阅读顺序：

1. `contract.md`
2. `full-facet-registry-draft.yaml`
3. `all-company-attachments-draft.yaml`
4. `coverage-and-gap-audit.md`
5. `full-company-placeable-graph-draft.yaml`
6. `full-company-placeable-tree.md`
7. `validation-final.yaml`

当前结果：271/271 point 有唯一处置，269 条可进入人工复核，2 条阻断；258 条 facet-explicit，13 条 cell-only；484 个 facet assertion、272 个 role assertion。Miniconda 校验 18/18 通过。

独立复审：

- `../../../reviews/2026-08-25-kimi-rereview-all-company-placement-v1.md`：PASS；
- `../../../reviews/2026-08-25-cursor-rereview-all-company-placement-v1.md`：PASS。

上一轮路线要求与 56 点试挂仍以 `../2026-08-25-tq010-tq014-delta-tradeoff-v1/` 为准；本包不改写其证据裁决。
