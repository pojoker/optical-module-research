# 海外公司事件雷达 MVP 开发规格

状态：frozen for implementation
负责人：Codex（验收）、CodeBuddy（实现）、OpenCode（只读设计审查）、Kimi（独立边界复核）
工作项：`WI-20260809-CODEX-NEWS-01`

## 1. 产品边界

本模块不是泛新闻流，而是“披露件 → 原子主张 → 公司事件”的证据账本。页面同时提供事件时间线与主题影响视图，但新闻、官网博客和公司公告本身都不自动成为事实。

- 发现可以宽，进入主雷达必须严格。
- 自动化只生成候选；主雷达只展示人工完成原文锚点核验的事件。
- 第一方公告只能产生 `asserted` 事件；客户、交易对手、监管者或可观察结果的独立证据才可把事件提升为 `corroborated`。
- 公司博客按内容分为技术披露、演示披露、公司叙事；博客单独不能证明量产、客户采用、需求规模或行业卡点已经解决。
- 电话会季度覆盖公司与新闻监控实体分开，新闻涉及的上游、客户、伙伴或监管者不被强制补四季度槽位。
- 模块只读 canonical，不回写 `tree.yaml`、`points.csv`、`edges.csv` 等事实表。
- 本工作项不读、不写 `shipments.csv`；出货量推断与事件证据账本保持两条独立证据链，后续如需连接必须另立显式 ADR。

## 2. 深模块接口

对外仅暴露两个稳定入口：

```python
load_event_facts(root: Path) -> EventFacts
derive_event_projection(facts: EventFacts) -> EventProjection
```

CSV 解析、枚举、引用闭合、时间语义、证据权限、同源去重与事件状态判定都封装在模块内。renderer、WorkBuddy 和测试都消费同一 `EventProjection`，不得各自重算业务规则。

## 3. MVP 数据表

### `watch_entities.csv`

非季度覆盖实体登记表。季度公司继续复用 `universe.csv`，加载器在内部合并两类实体。

```text
entity_id,entity_name,entity_type,aliases,inclusion_reason,monitoring_status,promoted_company_id,source_ref,notes
```

### `disclosures.csv`

一个公开材料是一条披露件。发布者与事件主体必须分开。

```text
disclosure_id,publisher_entity_id,legacy_source_id,title,disclosure_type,content_class,provenance_class,canonical_url,local_path,content_hash,origin_group,published_at,updated_at,discovered_at,retrieved_at,reviewed_at,retrieval_status,processing_status,review_scope,notes
```

### `event_claims.csv`

一条可锚定、可复核的原子主张。

```text
event_claim_id,legacy_claim_id,disclosure_id,claimant_entity_id,claimant_role,statement_kind,quote,anchor,summary,review_status,reviewed_at,notes
```

### `events.csv`

一个现实世界的状态变化。阶段变化必须新增事件，通过 `previous_event_id` 连接到同一 `program_id`，不得覆盖历史事件。

```text
event_id,program_id,event_category,lifecycle_stage,event_status,primary_subject_id,counterparty_ids,theme_ids,occurred_start,occurred_end,date_precision,previous_event_id,site_country,target_market,policy_jurisdiction,summary,notes
```

### `event_evidence.csv`

明确 claim 对 event 的作用，以及是否构成独立证据。

```text
evidence_id,event_id,event_claim_id,relationship,independence_class,origin_group,notes
```

五表均落在 `calls/` 根目录，注册进 `calls/schema.py` 的 `FILES`/`ENUMS`，并由现有 `python -m calls check` 统一校验。不得建立绕开主 validator 的第二套校验入口。

实体 ID 使用同一命名空间：现有季度公司以 `universe.csv.company_id` 为准，`watch_entities.csv.entity_id` 不得与任何 `company_id` 重名；若监控实体升级为季度公司，原记录改为 `monitoring_status=promoted` 并在 `promoted_company_id` 指向新的 `company_id`，加载时只保留该季度公司作为活动实体。季度公司的 `enabled=no` 仅表示停止强制季度覆盖，不等于删除实体。

多值字段 `counterparty_ids` 与 `theme_ids` 使用分号分隔，空值表示未知或未显式映射，禁止据文本自动补全。`event_evidence.origin_group` 必须逐字等于其 claim 所属 disclosure 的 `origin_group`；validator 负责阻止冗余字段漂移。旧 `claims.review_status=reviewed` 迁移为新表的 `anchor_reviewed`，其余状态不得自行升级。

## 4. 受控枚举

- `entity_type`: `company | regulator | government | customer | partner | other`
- `monitoring_status`: `active | paused | promoted`
- `disclosure_type`: `official_release | regulatory_filing | technical_blog | product_page | datasheet | customer_release | government_record | media | other`
- `content_class`: `technical_disclosure | demonstration_disclosure | corporate_narrative | commercial_disclosure | regulatory_record`
- `provenance_class`: `first_party | counterparty | regulator | government | third_party | unknown`
- `retrieval_status`: `discovered | retrieved | unavailable | failed`
- `processing_status`: `unprocessed | candidate_extracted | anchor_reviewed | no_relevant_claims | rejected`
- `statement_kind`: `fact_assertion | forward_looking | technical_claim | technical_demo | corporate_narrative`
- `review_status`: `candidate | anchor_reviewed | rejected`
- `event_category`: `product_stage | capacity_constraint | commercial_adoption | capital_relationship | policy_market_access`
- `lifecycle_stage`: `announced | demonstrated | sampling | qualifying | volume_order | first_shipment | ramping | scaled | delayed | withdrawn | not_applicable`
- `event_status`: `asserted | corroborated | contradicted | corrected | withdrawn`
- `date_precision`: `exact | month | quarter | window | unknown`
- `relationship`: `reports | supports | contradicts | corrects | withdraws`
- `independence_class`: `same_origin | first_party | counterparty | regulator | observable_result | third_party`

## 5. 必须由代码强制的规则

1. 所有 ID 唯一，引用闭合；实体解析是 `universe.csv + watch_entities.csv` 的并集。
2. `retrieved_at`、`reviewed_at` 不得替代事件时间；页面同时显示事件、披露、检索和复核时间。
3. 主雷达事件至少有一条 `anchor_reviewed` claim，且该 claim 必须有非空原文短引、锚点和复核时间。
4. `no_relevant_claims` 必须带复核时间和 `review_scope`，不能把未处理材料写成“未提及”。
5. `technical_blog` 的技术/演示/叙事内容单独不得支撑 `volume_order`、`first_shipment`、`ramping` 或 `scaled`。
6. `corroborated` 至少要有一条 `counterparty | regulator | observable_result` 的支持证据，且其 `origin_group` 与第一方证据不同；同一底层公告的转载不得重复计票。
7. 相同 `program_id` 的阶段迁移必须生成新 `event_id`，并用 `previous_event_id` 指向前序；推导层不得修改历史记录。
8. 派生结果与 CSV 行顺序无关，所有列表稳定排序；无数据、未处理、读过无相关信息必须是不同状态。
9. 投影不能生成竞争、合作、供货或替代结论；显式关系披露也只作为候选事件和证据，不回写 canonical edges。

## 6. MVP 迁移样本

只迁移两个已存在的跨季材料，用来验证规则，不做全量重构：

1. AAOI `S_AAOI_1P6_ORDER_A`：2026-03-09 公司官方公告“收到首笔 1.6T 批量订单”。形成 `commercial_adoption / volume_order / asserted` 事件；第一方证据不能自行升级为已验证客户采用。公告中的预计发货时间保持 `forward_looking`，不得写成已经交付。
2. Lumentum `S_LITE_BLOG_20260430`：迁移现有 `CL017` 演示主张。形成 `product_stage / demonstrated / asserted` 事件；只证明公司展示了样机，不证明量产、客户验证或供应关系。

保留旧表和旧 ID 作为适配输入，不做不可逆迁移。

## 7. 派生输出

`EventProjection` 至少包含：

- `radar_events`：主雷达的已锚点核验事件；含主体、阶段、状态、四类时间、短引、锚点、来源链接和证据等级。
- `company_timelines`：按公司和 program 聚合的不可变事件序列。
- `theme_impacts`：事件对现有 theme 的候选影响，只显示显式 `theme_ids`。
- `discovery_queue`：未完成锚点核验或尚未晋级的候选。
- `coverage_summary`：材料处理状态、最近披露日和逾期/未处理提示。

## 8. 页面要求

- 事件时间线与主题卡并存；事件视图优先回答“本期发生了什么变化”。
- Actual / Guidance / Demo 必须有不同 badge，不能合并成“公司进展”。
- 每个事件可展开原文短引、锚点、发布者、材料类型、来源链接和各类时间。
- 第一方 `asserted` 与独立验证 `corroborated` 必须视觉分层。
- 国内能力只维持 `cell_only` 定位，不因新闻事件生成替代、合作、供货或竞争关系。

## 9. 验收门槛

1. 新增单元测试覆盖全部证据权限、时间、博客权限、同源去重和确定性规则。
2. `python -m calls check` 通过。
3. 全量 calls 测试通过。
4. 一条原子命令完成 validate → derive/render calls → build page，并断言页面包含事件视图、原文链接和数据版本。
5. `git diff --check` 通过。
6. Codex 检查变更只落在本工作项路径；Kimi 独立确认未污染 canonical 与 shipment 工作。

## 10. 本轮明确不做

- 不做全网自动爬虫或模糊实体学习。
- 不做自动置信度分数。
- 不从文本猜测合作、竞争、客户或供应关系。
- 不把所有历史电话会一次性迁入事件表。
- 不增加海外公司数量，先闭合数据、更新、展示和验收链路。

本 MVP 的原子网页构建命令为：

```bash
/Users/jowang/miniconda3/bin/python3 -B build_detailed_capability_report.py --html-only
```
