# 全球行业信号—国内能力定位层开发契约

## 1. 产品概述

- 阶段：现有海外电话会 MVP 的增量工包。
- 目标：把海外电话会中的需求、卡点和解法约束，与国内产业链已有能力点形成可追溯的“结构定位”，供 WorkBuddy 展示。
- 核心纪律：保存事实，运行时派生定位视图；结构对齐不升级为竞争、替代、合作、供货、满足需求、解决卡点或受益判断。
- 稳定锚：`cell_id` 与只读 `route_item_id`。`theme_id` 是可变化的研究假设，只作标注和血缘引用。

## 2. 目标与非目标

### 本轮目标

1. 将电话会中的约束要求原子化为带管理层 claim 锚的事实表。
2. 通过只读 adapter 将约束与 `points.csv` 的公司能力点按稳定节点机械对齐。
3. 生成确定性的 `capability_overlap`、`requirement_match`、`evidence_coverage_gap` 视图。
4. 对当前证据不足的 `structural_alternative` 与 `co_required` 显式返回 `unsupported`，而不是猜测。
5. 在 WorkBuddy 现有情报主题卡中显示国内能力定位、证据覆盖缺口和不支持原因。

### 非目标

- 不建设或恢复公司—公司供应链图。
- 不新增通用公司关系或人工商业判定账本。
- 不把同节点公司自动称为竞争对手。
- 不把同功能位自动称为商业替代。
- 不把结构共同需要自动称为公司合作。
- 不修改 `tree.yaml`、`knowledge.yaml`、`points.csv`、`edges.csv`、`route_bom.csv`、`capability_details.csv`、`corpus/_frozen.csv`。
- 不修改根 `scan.py`，新增校验全部归 `calls/validator.py`。

## 3. 角色与闭环工作流

| 角色 | 职责 | 权限边界 |
|---|---|---|
| 研究录入者 | 从 reviewed 管理层 claim 提取约束要求 | 只能写 candidate；不能填写商业关系结论 |
| 人工判定闸 | 核对节点、指标、引文与来源 | 可改为 reviewed/rejected；不得越过证据用途 |
| 定位模块 | 读取事实和 canonical adapter，派生视图 | 纯函数；不写 canonical；不产生商业禁词 |
| 渲染器/WorkBuddy | 展示定位结果和缺证状态 | 只读派生投影；不得二次推断 |

闭环：`reviewed claim → candidate requirement → 人工过闸 → 定位派生 → WorkBuddy 展示 → 缺证回到研究队列`。

## 4. 数据源与血缘

- 海外约束事实：`calls/claims.csv` 中 `review_status=reviewed` 的管理层 claim。
- 主题及稳定节点映射：`calls/themes.csv`。
- 国内公司能力事实：只读 `points.csv`。`capability_details.csv` 仅可展示，不参与模糊 join。
- 路线结构：只读 `route_bom.csv`。当前字段不足以证明功能位等价或必需共同项。
- 历史潜在匹配：`calls/solution_links.csv` 保留为 legacy，只用于旧报告兼容和迁移审计。

每个 requirement 必须引用真实 `claim_id`；每个定位结果必须引用真实 `point_id`。引文、URL 和文本内容不是 ID。

“国内能力宇宙”使用 `points.csv` 的现有上市标签保守过滤：仅纳入 `A股/新三板/未上市私企/未上市(母上市)/未上市国企`；`美股/日股/欧股/未解析` 和 `状态=宇宙外观察` 不进入国内定位。不得根据公司名称猜国别。

## 5. 新事实表

### `calls/constraint_requirements.csv`

```text
requirement_id,theme_id,cell_id,route_item_id,dimension,metric_name,comparator,target_value,unit,evidence_claim_ids,review_status,notes
```

规则：

- `requirement_id` 全局唯一，前缀 `CRQ`。
- `theme_id`、`cell_id`、可选 `route_item_id` 必须在现有只读账本中存在并闭合。
- `dimension` 复用现有 `affected_dimension` 枚举。
- `metric_name` 必填，可以是定性指标，如“稳定量产交付能力”或“InP/EML 有效产能”。
- `comparator,target_value,unit` 必须同时为空或同时非空；不因电话会没有数字而编造阈值。
- `evidence_claim_ids` 为分号分隔的 reviewed management claim；不得引用 analyst 或 corporate_author 作为约束事实。
- `review_status` 复用 `candidate/reviewed/rejected`。

### `calls/point_metrics.csv`

```text
metric_id,point_id,metric_name,value,unit,as_of,review_status,notes
```

规则：

- 本轮允许只有表头；没有合格量化事实时，`metric_comparison` 应为空。
- `point_id` 必须存在；数值必须能由该 point 的原始引语与锚点直接支持。
- 不做自动单位换算；单位不完全一致即不可比。

### Legacy `calls/solution_links.csv`

- 本轮不删除、不移动、不改 schema，保证旧输出和测试不回归。
- validator 将当前 2 行冻结；不得新增。
- 两行只迁移出“全球约束要求”，不迁移其人工选中的国内公司关系语义。

迁移结果：

- `SL001` → `CRQ001`：T002 / MOD1；定性指标“800G 数通模块稳定量产与交付能力”；主要证据 `CL006`；`reviewed`。
- `SL002` → `CRQ002`：T007 / C1；定性指标“高速 InP/EML 激光器有效制造产能”；证据至少包含 `CL015`、`CL027`、`CL028`；`reviewed`。

原 `P074/P095` 仍保留在 legacy 文件中，但不作为 requirement 的证据。

## 6. 定位模块与 interface

新增 `calls/positioning.py`，外部 interface 保持小而稳定：

```python
load_positioning_facts(root) -> PositioningFacts
derive_positioning(facts) -> PositioningProjection
```

内部可拆纯函数，但 renderer、WorkBuddy 和测试只依赖上述 interface。

`PositioningProjection` 至少包含：

- `requirement_matches`
- `capability_overlaps`
- `metric_comparisons`
- `evidence_coverage_gaps`
- `structural_alternatives` 及 `unsupported_reason`
- `co_required` 及 `unsupported_reason`

## 7. 派生视图定义

### `requirement_match`

- 前置：requirement 为 `reviewed`；其 `cell_id` 存在；point 位于上述国内能力宇宙、状态为现有 `生产中/在建`；point `cell_id` 相同。
- 输出字段：`requirement_id,theme_id,company,listing_label,point_id,point_status,cell_id,route_item_id,basis,source_claim_ids,requirement_as_of,point_as_of`。
- 本轮 `basis` 只能为 `cell_only`。即使 requirement 有 `route_item_id`，也不得推断该公司能力已通过该路线验证。
- 语义仅为“已有能力证据与约束落在同一节点”，绝不包含 `satisfied` 或等价字段。

### `capability_overlap`

- 同一 requirement/cell 下至少两家不同公司有有效 point 时输出公司集合，不生成公司对。
- 输出必须带 `basis=cell_only` 与 `comparability=unverified`。

### `metric_comparison`

- requirement 的数值三元组完整，且 `point_metrics` 存在相同 `point_id/metric_name/unit` 的 reviewed 数值时才输出。
- 单位不一致、指标名不一致或任一侧缺值时不比较，登记 `skipped_reason`。
- 布尔比较只说明给定数字是否通过 comparator，不升级为技术、商业或行业结论。

### `evidence_coverage_gap`

- reviewed requirement 在相同 `cell_id` 下没有任何有效 point 时生成。
- 只表示当前 canonical 能力证据未覆盖，不能写“国内没有能力”或“产业能力缺失”。

### `structural_alternative` / `co_required`

- 当前 `route_bom.csv` 缺少经证据核验的功能等价组、必需共同组与 requiredness。
- 本轮必须返回空数组和固定 `unsupported_reason`；不得从 BOM 文本、相邻行或共享 cell 猜测。

## 8. 状态和人工判定闸

Requirement：`candidate → reviewed / rejected`。

- candidate 不进入 WorkBuddy 正式定位。
- reviewed 必须有 reviewed management claim 锚、合法节点和原子 metric。
- rejected 保留原因，不进入派生。

自动输出禁词：`竞争/competition、替代/substitute、合作/collaboration/partnership、供应商/供货、满足需求、解决卡点、受益于`。validator 应扫描派生字段和 WorkBuddy 生成区块；原始引文中的合法原话不因此失败。

## 9. 派生输出与 WorkBuddy

- `calls/renderer.py` 通过定位 interface 生成 `calls/out/positioning.json`；它是确定性派生产物，不是事实源，禁止手改。
- 现有 `calls/out/panorama-intelligence.csv` 保持兼容。
- `calls/workbuddy.py` 可选读取定位投影，在每个主题卡尾部增加“国内能力定位”区块：
  - 同节点能力证据：公司、point、状态、`cell_only` 标签，以及 requirement/point 两个截止日期；
  - 数值对比：仅显示真正可比记录；
  - 证据覆盖缺口：明确写“当前能力证据未覆盖”；
  - structural alternative / co-required：显示固定 unsupported 原因。
- 没有 `positioning.json` 时安全跳过，不影响原页面。

## 10. 模块与文件改动范围

新增：

- `calls/POSITIONING-SPEC.md`
- `calls/constraint_requirements.csv`
- `calls/point_metrics.csv`
- `calls/positioning.py`
- `calls/out/positioning.json`（生成）

修改：

- `calls/schema.py`
- `calls/validator.py`
- `calls/renderer.py`
- `calls/workbuddy.py`
- `calls/tests/test_calls.py` 或新增定位测试文件
- `calls/README.md`

禁止修改 canonical 七文件、根 `scan.py`、`archive/`、`corpus/` 与无关文件。

## 11. 非功能要求

- Python 标准库；无新依赖。
- 相同输入生成字节一致的 JSON 与 HTML 区块。
- 所有列表按稳定主键排序。
- 缺失、不可比和 unsupported 不得静默消失。
- 定位模块纯读；canonical 写保护继续通过。
- 现有 33 项测试与 14 个派生文件不得回归；新增输出后文件计数相应更新测试。

## 12. 测试矩阵

至少覆盖：

1. requirement schema、ID 和引用闭合正反例；
2. 数值三元组半空被拒；定性指标被接受；
3. analyst/corporate_author claim 不能作为 requirement 证据；
4. legacy `solution_links` 新增行被拒；
5. `requirement_match` 仅按 cell 产生并固定 `basis=cell_only`；
6. 国内能力宇宙过滤正确，海外/未解析 point 不进入定位；
7. 定性 requirement 不产生 metric comparison；
8. 单位不一致产生 skipped reason；
9. 没有 point 时只产生 evidence coverage gap；
10. alternative/co-required 恒空且有 unsupported reason；
11. capability overlap 是公司集合，不是公司对；
12. requirement/point 双日期进入投影和页面；
13. 派生两次字节一致；
14. WorkBuddy 无定位文件时安全跳过，有文件时显示定位区块；
15. 自动区块不得出现商业禁词；
16. canonical 七文件 hash 不变；
17. 旧 solution link 报告继续存在。

## 13. 分阶段开发与验收

1. **P1：事实表与 validator**。新表可校验，坏引用/半空数值/legacy 新增均被拒。
2. **P2：两条 requirement 迁移**。`CRQ001/CRQ002` 血缘正确；不把 P074/P095 当需求证据。
3. **P3：定位 module**。纯函数 interface、确定性投影、unsupported/不可比语义正确。
4. **P4：renderer 与 WorkBuddy**。定位区块可选、安全、可追溯，不改变现有主题卡语义。
5. **P5：全量验收**。现有与新增测试全绿，`python3 -m calls all` 通过，WorkBuddy HTML 集成通过，canonical hash 不变，`git diff --check` 通过。

## 14. 风险与开放问题

- `points.csv` 能力点较粗，同节点不代表同规格；因此本轮只输出 cell-only 定位。
- `route_bom.csv` 当前不能证明结构替代与共同必需；两视图保持 unsupported，等待未来独立结构证据工包。
- 国内能力时效与海外电话会时效可能不一致，页面必须同时显示 point 日期与 requirement 来源日期。
- 未来若要输出竞争、替代或合作，必须另立人工研究工包和证据契约，不能扩展本自动定位 module 偷渡实现。
