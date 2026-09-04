# Reviewer brief：全量公司数据可放置图

请对本包做只读审查，不修改任何文件。目标不是评价文风，而是判断：当前 271 条 `points.csv` 数据是否被安全地放入“物理知识 × 技术路线 × WHY”草稿图，同时没有把关键词、原格声明、子公司/参股关系、成熟度或相关 facet 误写成公司能力或路线服务事实。

必读：

- `contract.md`
- `full-facet-registry-draft.yaml`
- `all-company-attachments-draft.yaml`
- `coverage-and-gap-audit.md`
- `full-company-placeable-graph-draft.yaml`
- `full-company-placeable-tree.md`
- `validation-final.yaml`
- canonical read-only：`points.csv`、`tree.yaml`

重点抽检：

1. 13 条 cell-only 是否应该保持粗粒度，或有漏掉的明确 facet；
2. P040、P193 的阻断是否正确；集团、子公司、收购资产的 subject scope 是否仍有越权；
3. facet/role regex 是否产生明显语义误判，尤其“研发/生产/销售”是否属于同一对象；
4. point status 与 facet maturity 是否被错误继承；
5. 56 条路线试挂是否仍严格区分 candidate match、related facet、route service；
6. 全量覆盖数字、树、图、文档是否互相一致；
7. 是否遗漏了会阻止网页/后续 YAML 增量落库的关键字段或状态。

输出格式：

- Verdict：PASS 或 BLOCK
- Findings：按 P0/P1/P2 分级，给出文件、point/字段和具体理由
- Required fixes：仅列阻断或必须修复项
- Residual risks：可接受但需要后续人审的风险

不得因机械校验通过而自动 PASS，也不得要求本轮生成正式路线集团、WHY 因果边或 canonical 写入；这些明确不在本轮范围内。
