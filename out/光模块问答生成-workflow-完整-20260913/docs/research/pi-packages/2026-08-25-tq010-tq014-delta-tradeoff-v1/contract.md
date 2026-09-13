# TQ010 / TQ014 draft-only 合同

## 1. 输入

唯一种子数据：

`../2026-08-24-tq009-route-profile-seeds-v1/route-profile-seeds-effective.yaml`

唯一解释和验收口径：

- `../2026-08-24-tq009-route-profile-seeds-v1/post-adjudication-effective-text.md`
- `../2026-08-24-tq009-route-profile-seeds-v1/next-round-acceptance-contracts.md`

物理树只读参考：`tree.yaml`。来源证据只复用上一包的 S1–S4 冻结快照。

## 2. 比较对象

只允许两个比较：

- `CMP-D02-D03`：同一 OFC 2025 演示组的 1.6T SiPh OSFP LRO 与 3 nm DSP 模块；
- `CMP-D04-D05`：同一 ECOC 2022 互操作链路的 QSFP-DD800 SiPh MZM PIC 与 OSFP EML/photodetector 两端点。

不得加入 D01 作为性能基线；D01 与上述演示不是同条件对照。

## 3. TQ010 delta card

每个比较必须对 36 个 seed 叶字段输出一个且仅一个状态：

- `same`：两侧均有可比值且相同；
- `different`：两侧均有可比值且不同；
- `unknown_left` / `unknown_right` / `unknown_both`；
- `not_comparable`：值存在但语义/单位/边界不相同。

确定性矩阵不得仅凭字符串是否相等判断 `different`。字段语义不等价时，必须通过公开的 `comparison-rules.yaml` 规则标为 `not_comparable`，并留下原因与证据引用。

然后输出 `physical_delta_candidates`。每条必须包含：

```yaml
delta_id: draft-local
basis_fields: []
left_observation: ...
right_observation: ...
delta_status: observed_difference | normalized_difference | engineering_inference | unknown
existing_physical_cells: []
candidate_facets: []
unmodeled_dimension: null | form_factor | electrical_responsibility | photonic_device_detail | other
component_delta: ...
interface_delta: ...
process_delta: ...
equipment_delta: ...
test_delta: ...
evidence_refs: []
```

规则：

- `process/equipment/test` 没有实例证据时必须是 UNKNOWN；
- `existing_physical_cells` 只可引用 `tree.yaml` 已有 ID；
- 不能把 OSFP/QSFP-DD 强塞到 B1/B2/D9；没有合适节点时使用 `unmodeled_dimension: form_factor`；
- 不能从 LRO 或 DSP 名称自动推出 DSP 被删除、功耗下降、FEC 移位等；
- 候选 facet 只是物理格内更细的能力标签，不是 canonical cell ID。

## 4. TQ014 trade-off card

每个比较必须生成一张卡，字段至少为：

```yaml
comparison_id: CMP-...
comparison_status: comparable | partially_comparable | not_comparable
scenario_constraints:
  aggregate_rate: ...
  reach: ...
  media: ...
  fec_ber: ...
  temperature: ...
  power_boundary: ...
  density_boundary: ...
  cost_boundary: ...
  maintenance_boundary: ...
advantages: []
costs_and_disadvantages: []
new_bottlenecks: []
alternatives: []
validation_questions: []
feedback_to_tq003: []
unknowns: []
no_unconditional_ranking: true
```

没有同条件对照证据时：

- `comparison_status` 必须为 `not_comparable` 或 `partially_comparable`；
- `advantages`、`costs_and_disadvantages` 只能为空；
- 公司“降低功耗”等一般表述不得转移到该比较；
- 可以生成验证问题和下一轮 TQ003 研究注记，但不能修改事实状态。

## 5. TQ011 前置输出

本包允许提出 `capability_requirement_candidates`，但每条必须区分：

- `axis_direct`：由 observed/company-stated/normalized seed 字段直接要求；
- `delta_direct`：由两侧 observed/normalized difference 直接要求；
- `engineering_inference`：需后续证据，不能用于公司匹配；
- `unknown`。

每条至少包含：物理格、facet、能力动作（design/manufacture/integrate/test）、验收指标状态、可否用现有 `points.csv` 匹配。

## 6. 停止与失败

合格停止可以是“无法比较，但缺口已完整列出”。出现以下任一项即失败：

- 跨实例补值；
- 用 DR8/SiPh/EML/DSP 名称补内部结构；
- 生成无条件优劣；
- 把差异自动写成工艺/设备事实；
- 直接生成公司名单；
- 新 QID、正式 RP、canonical、coverage 或公司组。
