# TQ009 路线画像种子小样

本包验证一个问题：现有 TQ005–TQ008 四轴能否在**不跨产品实例拼接**的前提下，组成可比较的路线画像种子，并为后续公司数据挂载暴露真实缺口。

状态边界：

- `draft_only: true`
- 不创建正式 `RP###`；
- 不写 `knowledge.yaml`、`research_questions.yaml`、`points.csv`、`edges.csv`、`route_bom.csv`、`tree.yaml`；
- 不改变覆盖状态；
- 不把能力匹配写成路线服务；
- 不做路线优劣、成熟度、市场份额或受益公司判断。

阅读顺序：

1. `contract.md`：Pi 与人工裁决共同遵守的边界；
2. `source-discovery.md`：冻结一手来源能支持哪些实例字段；
3. `raw-output.md` / `raw-output-round2.md`：Pi 两轮原始草案；
4. `adjudication-round1.md` / `adjudication.md`：复合字段问题与最终裁决；
5. `route-profile-seeds-effective.yaml`：本包唯一有效的种子数据草案；
6. `post-adjudication-effective-text.md`：本包唯一有效解释；
7. `route-tradeoff-gate.md`：优势/劣势的上下游因果铰链；
8. `next-round-acceptance-contracts.md`：TQ010/TQ014 的允许答案、覆盖条件与停止条件；
9. `company-placement-pilot.md`：现有公司数据试挂结果；
10. `candidate-tree.md`：下一版树的候选结构；
11. `validation-report.md`：机械校验与 canonical 零变更记录。
