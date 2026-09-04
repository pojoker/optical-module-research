# WP-HY3 — 校验器、重要性与缺口状态机

所有者：CodeBuddy `--model hy3`（HY3）
写入范围（仅此目录，不修改其他工包 / SPEC / CONTRACT / WORKPACKAGES / logs / output / 现有台账）：

- `validate_model.py` — 基于 Python 标准库的 CSV 模型校验器
- `generate_gaps.py` — 六类研究缺口生成器
- `test_validate_model.py` — 自检（≥1 正例 + ≥6 反例，不写死公司名）
- `README.md` — 本文件

## 1. 运行

```text
# 校验一个包含 canonical CSV 的目录（默认 data/）
python validate_model.py <data_dir>
python validate_model.py <data_dir> --json      # 机器可读输出

# 生成缺口
python generate_gaps.py <data_dir> [-o gaps.csv] [--stale-days 365] --reference-date YYYY-MM-DD

# 自检
python test_validate_model.py
```

校验失败返回非零退出码（符合 SPEC §9“校验失败返回非零退出码”）。

## 2. 契约覆盖（对照 schema/CONTRACT.md）

| 校验维度 | 实现 | 错误码 |
|---|---|---|
| 字段 / 表头 | 每张表的列集合必须与 CONTRACT 完全一致（缺列/多列均报错） | `HEADER_MISSING` `HEADER_EXTRA` |
| ID 前缀 + 唯一性 | `SN-/SE-/ORG-/CAP-/TR-/EV-/GAP-` 前缀 + 表内唯一 | `ID_EMPTY` `ID_PREFIX` `ID_DUP` |
| 枚举（类型/关系/状态） | node_type、relation_type、status、org_type、capability_status、evidence_use、source_tier、stance、verdict、gap_type、priority、gap_status 等 | `ENUM` |
| 合法关系 | CONTRACT §2 的 source→target 表；`alternative_to` 须同类型，`part_of` 须同类或更高级节点 | `REL_ILLEGAL` |
| 混层 | `part_of` 不得指向“子级”节点（破坏层级） | `LAYER_MIX` |
| 引用 / 孤儿 | 边/能力/交易/缺口/证据的 ID 引用必须存在 | `REF_ORPHAN` `GAP_ORPHAN` `GAP_BAD_ROUTE` |
| 证据用途匹配 | structure/capability/trade 证据用途须与引用它的表一致（CONTRACT §6“用途必须匹配”） | `EVID_USE_MISMATCH` |
| 证据四件套 | 事实类 verdict 需 url + quote + retrieved_at（CONTRACT 四件套 / 诚实边界） | `EVID_NO_URL` `EVID_FACT_INCOMPLETE` |
| 匿名端点 | `anonymous_endpoint` 非空时不得同时伪造 org_id | `TRADE_ANON_FAB` |
| 重要性纪律 | CONTRACT §8：非 `unknown` 不得无依据升级；`bottleneck_candidate` 须 verified/hypothesis 且有支撑证据或假设文本；`structural_critical` 须在至少一条路线中 mandatory | `IMP_NO_BASIS` `IMP_BN_CONF` `IMP_BN_EVID` `IMP_BN_HYP` `IMP_SC_NOT_MANDATORY` |
| 状态机不变量 | `verified` 节点须有 supports/partial 的 structure 证据；`resolved` 缺口须有证据；capability 的 evidenced/reviewed/admitted/rejected/stale 须有 capability 证据 | `STATE_VERIFIED_NO_EVID` `GAP_RESOLVED_NO_EVID` `STATE_CAP_NO_EVID` |

> 状态机为**快照式**校验：只检查记录“当前状态”是否满足契约规定的合法终点（如 `verified` 必须有证据），不观测历史跳变——这是有意为之（无历史日志时无法判断跃迁来源）。

## 3. 缺口生成（generate_gaps.py）

覆盖 CONTRACT §7 的五类 + 时间有效性：

| 缺口类型 | 触发条件 |
|---|---|
| `structure_gap` | 路线无 `implements` 分解；功能无 `requires` 部件/材料；`structural_critical` 节点无证据覆盖 |
| `player_gap` | 可映射的关键节点（路线/部件/材料/工序/设备类别）没有任何组织能力映射；应用与抽象功能不制造“玩家”噪声 |
| `capability_gap` | 关键节点已有映射，但状态未知、未审核或缺 capability 用途证据 |
| `trade_gap` | `production/sampling/planned` 能力但无观测到的供货关系（**仅生成研究缺口，不伪造交易记录**） |
| `currentness_gap` | `as_of` 缺失 / 非 ISO 日期 / 超过 `--stale-days` |
| `comparability_gap` | 仅检查显式声明为 `all/common` 的共同覆盖不对称；路线特有差异不报缺口。路线数 < 2 时保留分母消失守卫 |

生成器要求显式 `--reference-date`，不读取系统日期；按 `gap_type, node_id, route_scope, reason` 排序后分配 `GAP-0001…`，输出可直接通过 `validate_model.py` 复校。

## 4. 解释性决策（在 CONTRACT 留白处的合理约定）

1. `importance_confidence` 字段承载 CONTRACT §8.5 的“依据状态” `verified / hypothesis / unknown`；“无依据不得从 unknown 升级” ⇒ 当 `importance_class != unknown` 时 `importance_confidence` 不得为 `unknown`。
2. `bottleneck_candidate` + `verified` ⇒ 须引用至少一条 `use=structure` 且 verdict 为 `supports/partial` 的证据；`hypothesis` ⇒ `importance_basis` 或 `notes` 中须有假设文本。
3. `structural_critical` ⇒ 必须位于至少一条产品路线的 mandatory 结构骨架；可通过 `drives/implements/requires/uses_process/uses_material/part_of/precedes/enabled_by` 到达，覆盖应用、路线、功能、部件、工序与设备层。
4. `part_of` 层级：目标须为同类型或一个更“高层”的节点（`LEVEL` 序：application<product_route<function<component/material/process/equipment_category）。
5. `trade_observations.grade` 在 CONTRACT 未枚举，采用 AGENTS.md 四级（`real/half/inferred/forbidden`），仅在有值时校验。
6. `comparability_gap` 不把路线特有节点的缺失视为错误；仅对显式共享节点检查不对称，并通过“路线数 < 2 即生成缺口”与真实路线引用双重守卫。

## 5. 已知边界 / 限制

- **公司写入结构节点**无法自动识别（结构节点表无“是否公司”字段）；该纪律由 WP-GROK 人工验收，不在本校验器拦截范围。
- 校验器为快照式，不能发现“先 deprecated 再 admitted”等历史级非法跃迁；需 Codex 集成阶段结合变更日志判断。
- `deprecated` 节点的迁移关系（`part_of`/`alternative_to`）仅作告警（warning），不阻断，以避免过度约束。
- 所有阈值（stale-days 等）可配置，默认 365 天。

## 6. 自检结果约定

`python test_validate_model.py` 全绿表示：正例通过、六类反例（非法关系/孤儿/重复ID/混层/瓶颈无依据/非法状态转换）及缺口分母消失均被拦截、六类缺口均可生成且生成结果可二次校验通过、且本文件不含写死的光模块公司名。
