# 全量公司挂载合同

## 输入

- canonical 只读：`tree.yaml`、`points.csv`；
- 路线匹配只读：`../2026-08-25-tq010-tq014-delta-tradeoff-v1/company-capability-match-pilot.yaml`；
- 禁止读取 `archive/`；
- 所有 Python 必须为 `/Users/jowang/miniconda3/bin/python3`。

## 每个 point 的输出

每个 `points.csv` point 必须恰好生成一条 attachment proposal：

```yaml
point_id: P...
company_string: ...
physical_cell: ...
subject_scope: direct_or_unresolved | direct_named_subsidiary | controlled_subsidiary | group_via_acquisition | affiliate_only | acquired_asset_or_business | definition_only | other
attachment_eligible: true | false
facet_assertions:
  - facet: namespace.value
    evidence_spans: [{start: 0, end: 3, text: ...}]
    facet_maturity_state: not_inferred
role_assertions:
  - role: ...
    evidence_spans: []
    review_status: needs_human_review
maturity_markers: []
route_relation: null | object
# object = {route_pilot_ref, requirement_candidates, related_facet_evidence,
#           route_service_conclusion: false}
review_status: needs_human_review | blocked_attachment_scope
```

## 领域边界

1. physical cell 来自 `points.csv`，必须存在于 `tree.yaml`；
2. facet 必须来自公开 registry，且必须在引语中找到精确 span；完整引语仍以 `points.csv#point_id` 为唯一引用，不在 proposal 中重复复制；
3. 无 facet 的 point 仍可挂原 cell，标 `cell_only`；
4. role 必须同时满足 cell family 与动作 span，不能仅由 cell 推断；
5. 否定销售、未来规划、送样、验证、小批量和量产必须分开保留，不由 point 状态覆盖；
6. affiliate-only 或 definition-only point 不生成 facet/role/maturity assertion；
7. controlled subsidiary/group-via-acquisition 可保留 group-scope proposal，但必须人审；
8. `related_facet_only` 不生成 route requirement match；
9. 公司字符串归一化只生成 alias candidate，不自动合并公司实体。

## 全量验收

- 271/271 point 有且仅有一个 proposal；
- 39/39 已占用 cell 在 registry 中；
- 0 unknown cell；
- 所有 facet/role span 可在原引语按 offset 复现；
- subject blocked 的 point 无 facet/role assertion；
- graph/tree 统计与 proposal 文件一致；
- canonical、coverage、正式 RP、公司组零改动；
- Kimi k3 与 Cursor auto 只读复审通过。
