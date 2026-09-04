# 产业链 v2 最小数据契约

## 1. `structure_nodes.csv`

字段：

```text
node_id,node_type,name_zh,name_en,definition,status,importance_class,importance_confidence,importance_basis,evidence_ids,as_of,notes
```

允许的 `node_type`：

- `application`
- `product_route`
- `function`
- `component`
- `material`
- `process`
- `equipment_category`

禁止把公司写入本表。禁止把测试工序写成 component；禁止把 CPO/LPO 等架构概念写成封装部件。

## 2. `structure_edges.csv`

字段：

```text
edge_id,source_node_id,target_node_id,relation_type,route_scope,requiredness,evidence_ids,notes
```

允许关系：

| relation_type | 合法 source → target |
|---|---|
| `drives` | application → product_route |
| `implements` | product_route → function |
| `requires` | product_route/function → component/material |
| `uses_process` | product_route/component → process |
| `uses_material` | component/process → material |
| `enabled_by` | process → equipment_category |
| `precedes` | process → process |
| `alternative_to` | 同类型节点 → 同类型节点 |
| `part_of` | function/component/process → 同类或上一级结构节点 |

`requiredness`：`mandatory / route_specific / optional / unknown`。

## 3. `organizations.csv`

```text
org_id,canonical_name,org_type,country,identifiers,aliases,status,notes
```

`org_type`：`company / institute / standards_body / customer / distributor`。

## 4. `capabilities.csv`

```text
capability_id,org_id,node_id,capability_status,route_scope,evidence_ids,as_of,review_status,notes
```

`capability_status`：

- `production`
- `sampling`
- `development`
- `planned`
- `agent_or_distributor`
- `historical`
- `unknown`

产品页、业务章节等 capability 证据不得自动生成 trade observation。

## 5. `trade_observations.csv`

```text
observation_id,supplier_org_id,customer_org_id,anonymous_endpoint,product_or_node_id,period,amount_or_share,evidence_ids,grade,review_status,notes
```

匿名端点不得伪造 org_id。历史 `edge_id` 可写入 notes 或未来 adapter 字段。

## 6. `evidence.csv`

```text
evidence_id,evidence_use,source_tier,title,publisher,url,publication_date,retrieved_at,as_of,quote,stance,verdict,notes
```

- `evidence_use`：`structure / capability / trade`
- `source_tier`：`T1 / T2 / T3`
- `stance`：`standard / issuer_self / counterparty / regulator / third_party`
- `verdict`：`supports / partial / conflicts / inaccessible / pending`

一条 evidence 可被多个记录引用，但用途必须匹配。

## 7. `gaps.csv`

```text
gap_id,node_id,route_scope,gap_type,priority,status,reason,next_question,completion_condition,owner,evidence_ids,updated_at,notes
```

`gap_type`：

- `structure_gap`
- `player_gap`
- `capability_gap`
- `trade_gap`
- `currentness_gap`
- `comparability_gap`

`priority`：`P0 / P1 / P2 / monitor`。

`status`：

`identified / scoped / researching / evidenced / resolved / blocked / out_of_scope`

## 8. 重要性判定纪律

重要性不是单一数值。至少记录：

1. 是否为路线必需；
2. 是否存在性能/功耗/产能/良率瓶颈证据或假设；
3. 替代性是否低；
4. 是否影响关键工序；
5. 依据状态：`verified / hypothesis / unknown`。

规则：

- `structural_critical`：至少在一条路线中 mandatory；
- `bottleneck_candidate`：必须有 verified 证据或显式 hypothesis；
- 无依据不得从 `unknown` 升级；
- 缺证据可以提高研究缺口优先级，但不能提高事实置信度。

## 9. 引用格式

多值字段统一使用分号分隔；空值留空，不使用“无”冒充结构化状态。

所有 ID 全局唯一、稳定、不可复用：

- `SN-` structure node
- `SE-` structure edge
- `ORG-` organization
- `CAP-` capability
- `TR-` trade observation
- `EV-` evidence
- `GAP-` gap
