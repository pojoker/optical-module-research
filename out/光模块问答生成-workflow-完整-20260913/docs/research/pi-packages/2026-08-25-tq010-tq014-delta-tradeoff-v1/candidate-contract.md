# 多候选统一输出合同

只输出一个可由 PyYAML 解析的 YAML 文档，不使用 Markdown 代码围栏，不写正文说明。

## 顶层结构

```yaml
meta:
  generator_id: P1 | P2 | P3 | C1
  mode: draft_only
  canonical_write_performed: false
physical_delta_candidates: []
tradeoff_cards: []
capability_requirement_candidates: []
validation_questions: []
```

## physical_delta_candidates

每条严格包含：

```yaml
delta_id: <generator-local unique id>
comparison_id: CMP-D02-D03 | CMP-D04-D05
basis_fields: [<comparison-matrix field>]
left_observation: <string>
right_observation: <string>
delta_status: observed_difference | normalized_difference | engineering_inference | unknown
existing_physical_cells: [<tree.yaml cell id>]
candidate_facets: [<draft-only facet label>]
unmodeled_dimension: null | form_factor | electrical_responsibility | photonic_device_detail | other
component_delta: <string or UNKNOWN>
interface_delta: <string or UNKNOWN>
process_delta: UNKNOWN
equipment_delta: UNKNOWN
test_delta: UNKNOWN
evidence_refs: [<S3/S4 or seed anchor>]
```

只列有意义的原子候选，不复制 36 行矩阵。一个候选可以诚实地是 `unknown`，但不得用 UNKNOWN 的另一侧反推差异。

## tradeoff_cards

必须恰好两张，每个 comparison 一张，并严格遵循 `contract.md` 第 4 节。当前证据下 `comparison_status` 只能是 `partially_comparable` 或 `not_comparable`；`advantages`、`costs_and_disadvantages`、`new_bottlenecks`、`alternatives` 必须为空数组。

## capability_requirement_candidates

每条严格包含：

```yaml
requirement_id: <generator-local unique id>
comparison_id: CMP-D02-D03 | CMP-D04-D05
basis_type: axis_direct | delta_direct | engineering_inference | unknown
basis_fields: [<comparison-matrix field>]
target_physical_cell: <tree.yaml cell id> | UNMODELED
candidate_facet: <draft-only facet label> | null
capability_action: design | manufacture | integrate | test
requirement_statement: <string>
acceptance_metric_state: observed | defined_but_value_missing | unknown
existing_points_matchable: yes | partial | no
match_basis: <only describe which point evidence fields could match; no company names>
evidence_refs: []
```

`engineering_inference` 不可标为 `existing_points_matchable: yes`。不得生成公司名单、公司分组、供应关系或“服务某路线”结论。

## validation_questions

问题必须与某个 comparison、字段或 requirement 绑定；只生成下一轮验证问题，不创建新 QID。

## 失败条件

- 改写 deterministic comparison matrix；
- 将 raw `LRO` 与 raw `3 nm DSP` 写成同维度 `different`；
- 将 D03 补成 full-retimed，或推导 DSP 删除/FEC 迁移/功耗优势；
- 将 D04/D05 的互操作端点当作同角色、同条件性能对照；
- 把 OSFP/QSFP-DD 强塞入 B1/B2/D9/MOD1；
- 扩展 EML 为 DFB+EAM/InP，或把 generic photodetector 补成 PIN/APD；
- 将过程、设备或测试差异写成非 UNKNOWN；
- 任何无条件优劣、公司匹配、canonical/coverage/formal RP/new QID 写入。
