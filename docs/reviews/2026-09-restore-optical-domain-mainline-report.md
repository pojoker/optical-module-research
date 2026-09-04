# 光模块领域主线恢复报告

日期：2026-09-02  
基线：`227f503`  
目标分支：`codex/restore-optical-domain-mainline-20260902`

## 结论

本分支从干净领域基线按路径恢复领域数据，没有合并 research graph closure pilot。

恢复后的主线仍是：canonical 账本 → 确定性读者投影；人工问题图 → 人工研究与晋升。新增的关系代码只把既有账本机械投影为轻量类型化关系和 relation lead，不保存问题状态，不自动关闭或重开问题，也不把生成物当事实源。

四条纪律已经进入领域合同与实现：

- `source_encoded != derived_candidate`
- `actual != planned`
- `lead != formal_question`
- `generated_output != canonical_data`

## 1. 路径级恢复清单

### 来自 `b233542`

| 文件 | 导入内容 | 变化 |
|---|---|---:|
| `knowledge.yaml` | KN008–KN010 canonical 知识条目 | +108 / -0 行；知识条目 7 → 10 |

KN008–KN010 的问题、物理格、路线条目、证据引用均由现有总闸复核；没有导入该提交的页面生成物。

### 来自 `5ec2153`

| 文件 | 用途 | 变化 |
|---|---|---:|
| `docs/research/knowledge-append-candidate-pq001-v1.yaml` | KN008 晋升依据与未决项 | +11 / -9 |
| `docs/research/knowledge-append-candidate-pq002-v1.yaml` | KN009 晋升依据与未决项 | +4 / -9 |
| `docs/research/knowledge-append-candidate-pq003-v1.yaml` | KN010 晋升依据与未决项 | +2 / -2 |
| `docs/research/光模块知识体系-当前任务控制文稿.md` | 当前任务控制与后续候选 | +73 / -30 |
| `docs/reviews/2026-08-31-kimi-review-knowledge-append-pq001-v1.md` | PQ001 审核记录 | +36 |
| `docs/reviews/2026-08-31-kimi-review-knowledge-append-pq002-v1.md` | PQ002 审核记录 | +36 |

这些文件保存“为何可以晋升”以及“下一步还要研究什么”，不承担自动问题状态。

### 来自 `3420f3c`

仅恢复 calls 正式账本增量及其直接校验支持。数据行变化均以 `227f503` 为分母：

| canonical / review ledger | 数据行变化 |
|---|---:|
| `calls/company_candidates.csv` | 0 → 64 |
| `calls/company_tier_reviews.csv` | 0 → 68 |
| `calls/disclosures.csv` | 38 → 50 |
| `calls/entity_relationships.csv` | 0 → 12 |
| `calls/event_claims.csv` | 23 → 37 |
| `calls/event_evidence.csv` | 23 → 37 |
| `calls/events.csv` | 21 → 34 |
| `calls/sources.csv` | 66 → 166 |
| `calls/universe.csv` | 14 → 39 |
| `calls/watch_entities.csv` | 2 → 47 |
| `calls/claims.csv` | 70 → 70（无变化） |
| `calls/validations.csv` | 12 → 12（无变化） |
| `calls/commitments.csv` | 9 → 9（无变化） |

`sources.csv` 是滚动四季度窗口：相对基线净增 100 行，同时移除 4 个已滚出窗口的旧季度槽位；不是静态追加。共享行除 `WATCH_DUST` 的说明更新外未改写原有领域主张。

为使正式增量可被当前分支读取和校验，同时按路径恢复：

- `calls/schema.py`
- `calls/event_intelligence.py`
- `calls/README.md`
- `calls/SPEC.md`
- `calls/tests/test_event_intelligence.py`

测试只核验真实生产账本计数和关系闭合，没有制造假产品、假事件或测试状态世界。

## 2. 明确未导入的内容

以下内容没有进入本分支：

- `29cc861` 的 slot/assertion closure pilot；
- `4150e55` 的 receipt、manifest、审核门和状态扩展；
- `d0ab510` 的 snapshot、replay、lineage、跨构建状态机；
- pilot 的 `relation_assertions.yaml`、通用 adapters 和 question-generation engine；
- `tools/research/build_relation_index.py`、`recompute_question_state.py`；
- `tests/fixtures/research_graph/` 及手工构造的状态历史；
- `out/relation_*.jsonl`、generated diagnostic questions 和其他生成页面；
- `calls/workbuddy.py` 及 calls 生成输出；
- closure pilot 的兼容 API、product registry、actor-role 或 semantic-entailment 机制。

原因一致：它们不直接增加光模块领域事实，或只在 fixture 世界中触发，或会把主线重新带回通用状态基础设施。

## 3. FIT / 汇聚科技语料分母诊断

结论：问题不是公司身份不一致，也不是当前主线缺少 corpus；是旧海外工作分支从较早提交分叉，所跟踪的 `corpus/_frozen.csv` 尚未包含这两条 denominator row，而共享的忽略目录中已经存在语料。

`227f503` 已经同时具备：

- `corpus/_frozen.csv` 中 FIT、汇聚科技的冻结分母行；
- 本地真实 annual corpus 文件。

新分支直接使用这套真实分母与语料，通过总闸；没有补假行、改公司身份或使用 `--no-verify`。

## 4. 最小领域模型

### 人工问题图

`research_questions.yaml` 仍是人工策划的 canonical 问题图：

- 25 个研究问题、4 个 WHY 桥问题；
- `parent_id` 仅用于页面树形展示；
- `depends_on[]` 保存真实理解依赖，当前 26 条依赖边；
- 不保存自动 resolution status，不由任一 KN 引用自动关闭。现有页面的“已覆盖”仅表示已有 KN/WHY 引用，不等同于问题已完整回答。

### 轻量关系视图

`contracts/domain_relation_types.yaml` 只定义八种领域关系：

`part_of`、`connects_to`、`requires`、`has_capability`、`offers_product`、`implements_route`、`has_stage`、`supported_by`。

`tools/research/build_relation_leads.py` 是唯一机械适配入口：

```text
build_domain_projection(repo_root) -> relations + leads
```

生产账本当前机械投影出 474 条 source-encoded 关系：

| relation type | 数量 |
|---|---:|
| `part_of` | 45 |
| `connects_to` | 88 |
| `requires` | 30 |
| `has_capability` | 271 |
| `has_stage` | 11 |
| `supported_by` | 29 |
| `offers_product` | 0（只允许人工晋升） |
| `implements_route` | 0（只允许人工晋升） |

其中 modality 为 actual 258、planned 20、unspecified 196。公司能力与路线需求的单格交集产生 284 条 lead（248 个 actual 命中、36 个 planned 命中）。lead 文案明确声明：交集不等于完整路线能力、具名产品、路线实现或客户采用。

默认命令只打印统计；只有显式指定输出路径才写生成文件。生成结果不参与 canonical 校验，也不提交到 Git。

## 5. 总闸与测试

| 验证 | 结果 |
|---|---|
| `python scan.py --check` | 通过，不变量 ①–⑭ 全绿 |
| `python render.py --verify` | 通过；两次临时重建一致，完全不依赖 `out/` |
| `python participation.py --check` | 通过；宇宙 463、覆盖 463、确认 89、待确认 14 |
| `python -m calls check` | 通过；39 companies / 166 sources / 70 claims / 34 reviewed events |
| calls 领域测试 | 106 项通过 |
| relation 领域测试 | 5 项通过 |
| site 领域测试 | 临时构建后 10 项通过 |
| scan 反例自测 | 53 项通过 |

站点验收的可复现顺序是“临时构建 → 运行 10 项测试 → 删除生成目录”，构建器报告 `canonical_unchanged=true`。所有测试生成物均已清理，未提交 `out/`。

## 6. 当前 canonical 计数

| 数据 | 数量 |
|---|---:|
| 物理格 | 41 |
| 能力点 `points.csv` | 271 |
| 公司关系边 `edges.csv` | 236 |
| 路线 BOM 条目 | 15 |
| 知识条目 | 10 |
| WHY links | 0 |
| calls 公司 | 39 |
| calls 来源 | 166 |
| calls claims | 70 |
| calls disclosures | 50 |
| calls reviewed events | 34 |
| event claims / evidence | 37 / 37 |

## 7. 仍然存在的 UNKNOWN

- `why_links` 仍为 0；LPO 功耗下降到系统责任转移的完整因果链尚未正式写回。
- canonical 中尚无由机械视图确认的 `offers_product` 或 `implements_route`；单个 capability overlap 不足以证明它们。
- 哪些公司具有“800G LPO、具名 SKU、产品级、原始披露”的证据，仍需人工逐条晋升。
- 产品展示、客户验证、量产出货和客户部署仍必须分开，当前不少材料无法确认 exact stage。
- LPO 与 retimed 方案的受控系统级功耗、成本、时延和可维护性比较仍缺强证据。
- 路线变化对应的工序与设备增量仍不完整。
- calls 候选发现队列仍有 7 项需要人工判断；39 家季度公司中 36 家具备完整四槽来源覆盖。

## 8. 接下来三个垂直研究切片

### A. 800G DR8 物理组件链

入口：`tree.yaml` 的发送/接收/连接与封装格、`route_bom.csv` 的 RB001–RB005、`points.csv` 的组件证据。先回答完整电→光→电链以及每个部件的功能边界；自动化只做 `part_of / connects_to / requires` 投影，部件取舍与系统边界由人审核。

### B. LPO 为什么降低模块功耗及责任如何转移

入口：TQ002、TQ003、TQ006、TQ010、TQ014 与 WQ001–WQ003，以及现有 route-chain 研究候选。最终产物应是带约束、替代方案和反证的 WHY 链；因果方向、适用条件与竞争解释必须人工判断。

### C. 哪些公司有 800G LPO 具名产品级证据

入口：`points.csv`、calls 的 disclosures / claims / events / evidence，以及 TQ012、TQ013、WQ004。自动化可找公司、LPO、800G、产品名称之间的候选共现；只有人工核对原始披露后，才能晋升 `offers_product`、`implements_route` 或产品阶段结论。

## 9. 精简后的验收含义

本分支没有减少领域研究能力：已有 KN008–KN010、calls 增量、人工问题依赖和机械关系视图均可直接使用。它删除的是尚无生产调用者的通用状态机制。

后续每个研究切片只需证明三件事：读到真实 canonical 证据；产出人能核验的领域答案；经人工审核写回唯一事实源。不能因为 lead 数量、页面数量或状态迁移测试通过，就宣称研究问题已经回答。
