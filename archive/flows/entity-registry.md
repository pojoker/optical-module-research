# flows/entity-registry.md — 节点实体归并登记册（v1.7-E 项）

**状态：随 ROADMAP-v1.7 草案建立，未冻结。** 规则：每个涉归并节点标注
法人/集团两级；裁决三选一——**集团口径合并 / 母子分列 / 按披露口径照录**——
逐条登记理由。时间轴别名表与 nodes.csv 统一引用本册，消除双标。

## 数据化两层契约（v1.7a 治理还债 · D1）

本册的 5 条归并裁决已数据化为机器可读两层契约：

> **`flows/entity-registry.yaml`** —— 身份层 + 观察 scope 层（YAML，PyYAML 可读）。

设计依据：`ROADMAP-v1.7a.md §E` + `flows/out/roadmap-v17-review-codex.md §E`
（三表合并为两层：实体主表/关系别名表 → 身份层；观察 scope 表 → scope 层）。
冻结基线：236 边 / 169 节点 (commit 6b6d491)。

### 第一层：身份层（identity_layer）
回答“这些名称是不是同一法人 / 是否属同一集团 / 何时生效”。
每个实体字段：

| 字段 | 含义 |
|---|---|
| `entity_id` | 稳定主键（GROUP_/LEGAL_ 前缀） |
| `identity_type` | `legal_entity` \| `group` |
| `canonical_name` / `legal_name` | 规范名 / 法定全称 |
| `identifiers` | 代码/证券/信源代码（待 S0b 补全） |
| `aliases[]` | `{name, effective_from, effective_to}` 别名与有效期 |
| `rename_evidence` | `{status: confirmed\|pending\|none, anchor, retrieved}` 更名证据锚 |
| `related` | `member_of` / `parent_of` / `possible_same_as` / `predecessor_of`（均指 entity_id） |
| `identity_decision` | `same_legal_entity` \| `distinct_legal_entities` \| `pending`（取代原三选一） |
| `registry_ruling` / `registry_status` | 原样保留本册下方表格的治理状态 |

### 第二层：观察 scope 层（observation_scope_layer）
回答“这一条披露数字究竟是集团 / 法人 / 分支口径”。
每条 scope 字段：

| 字段 | 含义 |
|---|---|
| `scope_id` | 稳定主键（SC_ 前缀） |
| `scope_level` | `group` \| `legal_entity` \| `branch` |
| `based_on_entity` | 指向身份层 entity_id |
| `members[]` | 构成该 scope 的成员 entity_id |
| `scope_effective_period` | `{start, end}` 期间 |
| `disclosure_basis` / `anchor` | 披露出处 / 锚点（URL 或同E引用；未补留空） |

**默认策略**：未显式声明 scope 的边默认按 `legal_entity` 口径；仅原文明示合并
（集团/分支）口径时才登记 `group` / `branch` scope。

> 下方表格为裁决原文（治理状态以 `registry_ruling` / `registry_status` 镜像进 YAML）。


| # | 涉及名称 | 法人层 | 集团层 | 裁决 | 理由 | 状态 |
|---|---|---|---|---|---|---|
| 1 | 海信集团（联讯客户 E087/E089/E092）vs 海信宽带（源杰客户） | 青岛海信宽带多媒体技术有限公司 ≠ 海信集团控股 | 同属海信系 | 待裁决 | 联讯招股书披露口径为"海信集团"（同一控制合并），源杰为具体法人——两披露口径不同 | 待办 |
| 2 | 旭创系（苏州旭创/成都旭创/储翰科技） | 三法人 | 中际旭创上市体系 | v1.6 已按披露口径合并（源杰招股书注明并表列示）——待复核是否与"储翰独立节点"冲突 | 源杰招股书原文注 | 待复核 |
| 3 | 长飞系（长飞光纤合并/YOFC 各海外子/汉川/潜江/石英等） | 十余法人 | 长飞光纤光缆股份 | v1.6 按博创年报"长飞光纤合并"披露口径聚合 | 博创年报关联方表自带合并行 | 待复核 |
| 4 | 武汉昱升光器件有限公司（源杰IPO）vs 武汉昱升光电股份有限公司（仕佳/博创） | 疑同一主体更名 | —— | v1.6 已合并为"武汉昱升光电"——**更名证据未查**，待补工商记录锚点 | 名称高度相似+同城同业 | 待补证 |
| 5 | 顺丰速运 vs 西安顺丰速运（源杰两处） | 母子 | 顺丰控股 | v1.6 合并为"顺丰速运" | 物流服务商，集团口径合理 | 待复核 |

新增归并裁决一律先登记后执行；未登记的归并视为违规（红队负空间审计三问之③）。

## 首批五组终裁（Claude，2026-07-24，依 flows/out/entity-evidence-q3.md）

| # | 裁决 identity_decision | 依据与限定 |
|---|---|---|
| 1 昱升 | **same_legal_entity**（曾用名+统一社会信用代码91420100731064366W一致） | 锚为聚合库(shuidi)，置信中高；标 pending_primary，一手工商记录到手后升 confirmed |
| 2 海信 | **distinct_legal_entities** + 海信宽带 member_of 海信集团 | 节点分列维持；联讯边scope=group，源杰边scope=legal_entity |
| 3 储翰 | 独立法人 + member_of 旭创系（**2025-10-29 旭光电子32.55%股权售予中际旭创，控制加强，置信高**） | 与"成都旭创→智禾"线索分开处理，不假设等价 |
| 4 长飞合并 | scope 登记维持 group，**成员清单=诚实缺口**（年报PDF两次抽取失败留痕） | members 字段留空待补，不编造 |
| 5 顺丰 | 集团口径照录（源杰招股书释义=T1锚："西安顺丰及其咸阳分公司"） | 二手佐证弱不影响，T1释义已足 |
