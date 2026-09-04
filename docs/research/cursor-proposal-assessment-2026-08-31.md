# Cursor 八条建议与 workspace 真实状态独立审计

日期：2026-08-31
范围：只读检查当前 workspace；不修改 canonical、YAML、HTML 或代码
目标：判断 Cursor 八条建议哪些已经实现、哪些应在 PQ002 本轮使用、哪些属于后续架构

## 1. 结论先行

Cursor 对项目瓶颈的方向判断基本正确，但“建议尚待实现”已经不是当前 workspace 的准确描述。八项中：

- **已形成可运行小样**：晋升队列、最小语义蕴含合同、QX-03/Q-UP-04 公开通道结案、网页语义快照、公司能力格↔路线轴投影、主流排序分母闸、读者确定性分层；
- **仅局部实现**：claim 已成为多个研究包和晋升批次的原子单位，但还没有跨包的全局 claim 注册表、去重键或 claim graph；
- **尚未端到端闭合**：晋升闸没有接入一个可通过仓库总闸的 canonical 写入流程，问题验收仍是“任一 KN 关联即覆盖”的二元逻辑。

对 PQ002（“电→光→电的功能链如何工作？”）而言，本轮不应该再横向搜一批新材料。审计期间 workspace 并发新增了 `knowledge-append-candidate-pq002-v1.yaml` 和 `expert-questions-pq002-candidate.yaml`；前者已经把既有研究拆成 3 条物理知识候选，并通过现有结构检查器。因此当前动作应从“制作候选”进一步收敛为：

1. 对 3 条候选做独立人工语义蕴含审查，并裁决第三条 CPO 对象实例是否应成为 PQ002 整批验收的必要项；
2. 核对 PQ001 依赖、候选 ID、source hash 和 embedded review state 后再形成 receipt；
3. 明确 PQ002 只闭合功能链，不把完整 BOM、接口细节或测试要求偷渡进来；这些继续长到 PQ004、PQ005、PQ009。

公司—路线投影、主流排序、QX-03 内部实现追索和全局 claim graph 都不应塞进 PQ002 本轮。

## 2. 当前真实状态的关键发现

### 2.1 PQ002 已有 append candidate，但 canonical 仍未覆盖

`research_questions.yaml` 将 PQ002 定义为“电→光→电的功能链如何工作？”，验收条件仍是“有一条通过校验的 KN 显式关联本问题”。`knowledge.yaml` 当前没有任何 `PQ002` 引用。

既有 PQ002 研究包已经给出受限功能骨架，并经裁决明确：

- 可以解释 Host/Media 边界下的发送与接收功能链；
- EML/PIN 只能作为 Coherent 具名产品实例，不能泛化为统一 BOM；
- 完整器件连接、BOM 和接口测试分别留给 PQ004、PQ005、PQ009；
- 该包状态为 draft-only，没有 canonical write。

审计进行期间，workspace 又新增了：

- `knowledge-append-candidate-pq002-v1.yaml`：3 条候选，拟用 KN011–KN013；前两条为稳定解释，第三条为 OIF CPO 框架对象级候选；依赖 PQ001 的 KN008–KN010 批次先物化；
- `expert-questions-pq002-candidate.yaml`：把 Coherent 具名产品内部器件/集成边界保持为 `blocked_on_public_evidence`，未加入正式问题组合；
- 本次只读运行 `tools/research/check_knowledge_append_candidates.py` 后，3 条候选通过结构检查，且候选检查器构造的临时知识库通过 `scan.py --check`；真实 `knowledge.yaml` 没有变化。

这意味着 PQ002 已经不缺“候选生成”，当前缺的是人工语义裁决、依赖批次处理、真实仓库总闸恢复和用户决定。另一个状态一致性问题是：候选 YAML 内嵌的 `review_state.machine_preflight` 仍写 `pending`，与本次实际检查结果不一致；在形成 receipt 前必须校正状态来源，但本审计不修改该 YAML。

Evidence paths：

- `research_questions.yaml`
- `knowledge.yaml`
- `docs/research/pi-packages/2026-08-23-expansion-v1/post-review-effective-text.md`
- `docs/research/pi-packages/2026-08-23-expansion-v1/adjudication-pq002-final.md`
- `docs/research/current-answerability-audit-2026-08-26.md`
- `docs/research/knowledge-append-candidate-pq002-v1.yaml`
- `docs/research/expert-questions-pq002-candidate.yaml`
- `tools/research/check_knowledge_append_candidates.py`

### 2.2 专项小样可运行，但仓库总闸当前失败

本次只读执行结果：

- `tools/research/check_promotion_queue.py`：5/5 通过结构预检，明确输出 `NOT PROMOTED`；
- `tools/research/check_promotion_receipt.py`：5/5 内部一致，canonical effect 全为 false；
- `tools/research/check_company_route_projection.py`：7/7 通过结构预检；
- `tools/research/check_web_semantic_snapshots.py`：2/2 快照可复验；
- `tools/research/check_knowledge_append_candidates.py docs/research/knowledge-append-candidate-pq002-v1.yaml`：3/3 结构上 append-ready，临时物化扫描通过；
- 对应单元测试：19 + 12 + 10 项全部通过；
- `tests/research/test_milestone_reader_page.py`：6/6 通过。

但是 `/Users/jowang/miniconda3/bin/python3 scan.py --check` 失败：不变量⑥报告 **25 个根目录白名单外文件**，其中包括上述检查器、测试和快照脚本。`.githooks/pre-commit` 又直接调用 `scan.py --check`，因此当前仓库总闸和 pre-commit 都不能通过。

候选检查器的临时扫描会有意只复制 `scan.py` 白名单允许的顶层文件，所以它证明“候选内容在隔离环境中满足 canonical 不变量”，不证明真实 workspace 的总闸已恢复。这不是八项建议本身的语义失败，而是新治理工具尚未完成仓库级集成。任何“已可正式晋升”的说法在这个问题解决前都不成立。

Evidence paths：

- `scan.py`（不变量⑥根目录白名单）
- `.githooks/pre-commit`
- `tools/research/check_promotion_queue.py`
- `tools/research/check_promotion_receipt.py`
- `tools/research/check_company_route_projection.py`
- `tools/research/check_web_semantic_snapshots.py`
- `tools/research/check_knowledge_append_candidates.py`（`SCAN_TOP_LEVEL_FILES` 与 `materialized_scan`）
- `tests/research/test_milestone_reader_page.py`

优先级：**P0，PQ002 请求正式写入之前必须解决**。
风险：专项测试全绿会制造“系统已经全绿”的错觉；实际 canonical 修改将被总闸阻断。

## 3. Cursor 八条建议逐项裁决

### 3.1 极小晋升闸 / promotion queue

判定：**已实现候选层；未完成 canonical 端到端集成。**

已有基础：

- `promotion-queue-candidate.yaml` 把批次限制为最多 5 条，并要求显式用户批准；
- `tools/research/check_promotion_queue.py` 检查原子主张、范围、证据边界、falsifier 和 locator；
- `promotion-receipt-stable-explanations-01.yaml` 记录 machine、主代理、外审、目标合同和用户决策状态；
- 首批 5 条虽然语义外审通过，但目标审计认定它们是研究治理规则，不是可写入 `knowledge.yaml` 的领域知识，已经退回 `hold_pending_canonical_target_contract`；
- `knowledge-append-candidate-pq001-v1.yaml` 证明系统已经开始改用“面向具体 canonical schema 的领域知识候选”，方向正确。

Evidence paths：

- `docs/research/promotion-queue-candidate.yaml`
- `docs/research/minimal-entailment-contract-v1.yaml`
- `tools/research/check_promotion_queue.py`
- `docs/research/promotion-receipt-stable-explanations-01.yaml`
- `docs/research/promotion-target-audit-stable-explanations-01.md`
- `docs/research/knowledge-append-candidate-pq001-v1.yaml`
- `docs/research/knowledge-append-candidate-pq002-v1.yaml`

PQ002 本轮：**P0，直接复用并审查现有候选。** 3 条 PQ002 候选已经存在；下一步是人工蕴含审查、依赖/ID/状态复核和 receipt，不再创建平行候选。
后续架构：把“已审候选→目标合同→临时副本全量校验→用户批准→receipt”做成稳定流水线。
风险：当前问题验收仍是一条 KN 即覆盖；如果 PQ002 只晋升一句“模块会光电转换”，形式上可能覆盖，实质上仍未回答完整功能链。

### 3.2 最小语义蕴含门

判定：**已实现，而且机器边界表达正确；尚未成为 `scan.py` 的正式不变量。**

现有合同要求 atomic claim、`applies_when`、`does_not_apply_when`、`supports`、`does_not_support` 和 falsifier。检查器明确承认机器只做结构与显式冲突检查，真正的蕴含、共同分母、成熟度和反证裁决仍由人工完成。

Q-UP-06 对 KN006 的拆分是有效样例：结构校验曾经全绿，但证据卡只支持 splitter 工艺，不能承载标题中的 AWG/WDM；后来形成三条窄 claim 和 grows-question。

Evidence paths：

- `docs/research/minimal-entailment-contract-v1.yaml`
- `tools/research/check_promotion_queue.py`
- `tests/research/test_check_promotion_queue.py`
- `docs/research/pi-packages/2026-08-30-q-up-06-parallel-vs-wdm-v1/semantic-entailment-gate-proposal.md`
- `docs/research/promotion-batch-kn006-split-candidate.yaml`
- `docs/research/qx-11-kn006-evidence-split-adjudication.md`

PQ002 本轮：**P0，必须执行。** 现有 3 条候选已填写 supports、does-not-support、适用范围和反证条件；现在必须逐条人工判断证据是否真的覆盖标题和解释，尤其审查 C03 的 OIF CPO 框架实例是否属于 PQ002 必选知识，而不是 PQ004 的对象例子。
后续架构：只有当 claim 审查结果能被 canonical KN 引用并由总闸验证时，才算正式接入。
风险：把“机器预检通过”误写成“证据语义支持”；或把单产品 EML/PIN 实例泛化为所有光模块。

### 3.3 QX-03 / Q-UP-04 公开通道结案

判定：**已执行；不应在 PQ002 重开。**

QX-03 已找到 Juniper exact SKU 与 FR4/FR4-500 application 差分，但 mux/demux、TEC、laser/filter 架构仍缺 SKU-linked 一手证据。专利、认证照片、ODM 披露和 teardown 公开追索未命中，状态为 `public_evidence_insufficient`，解锁条件是实物 CMIS dump、vendor page dump、teardown 或正式内部披露。

QUP05-NQ02 也已把 NPO/CPO engine 可服务性标为 `blocked_on_public_evidence`，并把网页监控、私有数据和受控实验分 lane。

Evidence paths：

- `docs/research/pi-packages/2026-08-30-qx-03-fr4-500-sku-v1/adjudication.md`
- `docs/research/pi-packages/2026-08-30-qx-03-fr4-500-sku-v1/run.yaml`
- `docs/research/pi-packages/2026-08-30-qx-03-fr4-500-sku-v1/cmis-observable-map.md`
- `docs/research/qup05-nq02-serviceability-adjudication.md`
- `docs/research/npo-cpo-serviceability-matrix-seeds-v1.yaml`

PQ002 本轮：**P2 / 不执行**；只尊重既有 UNKNOWN，不用它填功能链。
后续架构：建立 blocked lane 的事件监控和实物实验入口。
风险：继续换关键词搜索会积累材料却不改变验收状态；反过来，把“没搜到”写成“不存在”也属于错误结案。

### 3.4 raw response + normalized semantic object + semantic hash

判定：**通用候选合同和双对象 pilot 已实现；尚未覆盖所有动态网页来源。**

当前合同同时保存原始响应、归一化对象、normalizer/version、语义哈希和 `supports/does_not_support`。Juniper 与 Eoptolink 各做了三次抓取：raw hash 漂移，semantic hash 稳定；检查器会重算哈希，并在语义变化时要求字段级 diff 和人工裁决。

Evidence paths：

- `docs/research/web-semantic-snapshot-contract-v1.yaml`
- `docs/research/web-semantic-snapshot-pilot-v1.yaml`
- `tools/research/capture_web_semantic_snapshots.py`
- `tools/research/check_web_semantic_snapshots.py`
- `tests/research/test_check_web_semantic_snapshots.py`
- `corpus/web/2026-08-31/semantic/`

PQ002 本轮：**P1，按来源触发。** 既有冻结 PDF/静态快照可继续使用；若新增动态网页证据，再采用该合同，不必为了形式重抓全部来源。
后续架构：把快照合同接入统一 source/evidence ingestion，并定义 normalizer 版本迁移。
风险：归一化对象只证明被提取字段稳定，不证明整页语义不变；normalizer 漏字段会造成“稳定但不完整”。

### 3.5 claim 作为一等公民

判定：**研究包内已广泛采用；全局层面仅部分实现。**

Q-UP-03、Q-UP-05、Q-UP-06、Q-MID-01 等包已经用 `claim_id`、scope、evidence status、falsifier、unknown 和 grows-question 表达原子主张；晋升批次也已形成 `claim → evidence → status → grows_question` 的局部闭环。

但 workspace 没有独立的全局 claim registry/graph，也没有跨包唯一 ID、同义 claim 去重、claim→KN/WHY 的正式反向索引。研究包仍是主要存储边界，同一规则可能在多个包中重复表达。

Evidence paths：

- `docs/research/pi-packages/2026-08-30-q-up-06-parallel-vs-wdm-v1/claim-schema.yaml`
- `docs/research/pi-packages/2026-08-30-q-up-06-parallel-vs-wdm-v1/candidate-claims-and-why.yaml`
- `docs/research/pi-packages/2026-08-30-q-up-03-host-electrical-architecture-v1/candidate-claims.yaml`
- `docs/research/pi-packages/2026-08-31-q-up-05-npo-cpo-boundaries-v1/candidate-claims.yaml`
- `docs/research/promotion-batch-stable-explanations-01-grows-questions.yaml`

PQ002 本轮：**P0（局部使用），不做全局迁移。** PQ002-KN-C01 至 C03 和 PQ002-NQ01 已建立局部连接；需要审查其 scope 与去重，不再另起一套 ID。
后续架构：**P1** 建全局 claim registry/graph、去重键、provenance 和 promotion target 映射；研究包只保留 batch/run 元数据。
风险：现在直接宣称“claim 已是一等公民”会掩盖跨包复用与去重缺失；此时大规模目录迁移又可能制造新的平行系统。

### 3.6 公司能力格 ↔ 路线轴只读投影

判定：**已实现并完成首批候选裁决；不属于 PQ002。**

当前投影有 7 个官方对象，区分 `route_served_candidate`、`capability_match`、`related_facet_only`，并强制 `supply_claim: not_supported`。检查器要求 legal entity、exact product identity、route binding、maturity/event 与同证据单元闭合；测试还确认“零个 route-served 正例”也可以合法通过，避免把预期结果写进门。

Evidence paths：

- `docs/research/company-route-projection-seeds-v1.yaml`
- `docs/research/qx12-company-route-primary-research.md`
- `docs/research/qx12-company-route-projection-adjudication.md`
- `tools/research/check_company_route_projection.py`
- `tests/research/test_check_company_route_projection.py`

PQ002 本轮：**P2 / 不执行**。PQ002 是物理功能链，不能为了公司投影把路线或供货字段带进来。
后续架构：把投影接入正式 RP/公司 attachment 前，仍需用户批准 schema，并保留 capability 与 route-served、manufacturer、named supply 的分离。
风险：`route_served_candidate` 容易被读者误读成实体制造、供货、量产或客户部署；当前 HTML 已提示，但 canonical 仍无正式承载对象。

### 3.7 推迟“最主流”与分母闸

判定：**研究状态闸已实现；通用机器闸尚未实现。**

主流快照已经固定市场、速率、reach、placement 和 metric，并把 denominator 标为 `UNKNOWN_PUBLIC`、状态标为 `UNKNOWN_NO_DENOMINATOR`。它明确拒绝在缺少同分母出货数据时对 retimed EML、retimed SiPh 与 LPO SiPh 排名。

Evidence paths：

- `docs/research/pi-packages/2026-08-26-foundation-to-mainstream-v1/mainstream-snapshot-candidate.yaml`
- `docs/research/pi-packages/2026-08-26-foundation-to-mainstream-v1/run.yaml`
- `docs/research/current-answerability-audit-2026-08-26.md`
- `out/光模块知识体系第一里程碑.html`（`#mainstream`）

PQ002 本轮：**P2 / 不执行**；功能链不需要市场份额分母。
后续架构：**P1** 把 denominator schema 与排序请求绑定；没有 metric、universe、time、rate/reach/placement 时，机器直接拒绝生成排名候选。
风险：当前是文件和文稿纪律，不是所有研究包共享的硬门；后续代理仍可能在别处把产品 listing、SKU 数或 demo 数量写成“主流”。

### 3.8 读者面按确定性分层

判定：**已实现，Cursor 原判断“尚未完成”已过时。**

当前里程碑 HTML 已有四类标签与 section 属性：稳定解释、对象级候选、机理候选、未知/阻断；页面还明确“展示层稳定解释不等于 canonical”。对应测试验证四类标签、公司投影行、问题状态计数、非 canonical 边界和语义快照链接。

Evidence paths：

- `out/光模块知识体系第一里程碑.html`
- `tests/research/test_milestone_reader_page.py`
- `docs/research/光模块知识体系-当前任务控制文稿.md`（§4.18）

PQ002 本轮：**P1，沿用而非重做。** 若 PQ002 候选进入网页，必须显示为“候选/待晋升”，不能因文字基础而自动显示为 canonical stable。
后续架构：从结构化 verdict 自动生成标签，减少 HTML 手工状态漂移。
风险：目前标签由 HTML 文稿承载；若源状态变化而页面未同步，仍可能出现展示与候选状态不一致。

## 4. 五个重点机制的实现深度汇总

| 机制 | 文件/代码基础 | 当前深度 | PQ002 本轮 | 后续工作 |
|---|---|---|---|---|
| 晋升闸 | queue、checker、receipt、target audit、PQ001/PQ002 append candidate | PQ002 结构候选已通过；canonical 未闭合 | P0：人工审查现有 3 条并形成 receipt | 修复总闸；稳定 canonical transaction |
| 语义蕴含最小门 | contract、checker、tests、人工审计样例 | 机器结构门 + 人工语义门已成立 | P0：逐条审 PQ002 claim，重点裁决 C03 scope | 让 KN 正式引用已裁决 claim |
| claim 一等公民 | 多包 claim schema、promotion batch、grows-question | 包内成熟；PQ002 已局部 claim 化；无全局 registry/graph | P0：审查现有 ID/去重/问题生长 | P1：全局 ID、去重、反向索引 |
| 公司能力格↔路线轴 | seed、checker、tests、QX-12 adjudication | 只读候选投影已完成 | 不进入 PQ002 | 与正式 RP/company attachment 对接 |
| 主流排序分母闸 | mainstream snapshot、UNKNOWN 状态、网页展示 | 研究纪律已落地；无通用机器门 | 不进入 PQ002 | 建 denominator schema 与拒答门 |

## 5. 建议的 PQ002 本轮最小执行合同

本轮目标不是“再研究一次 PQ002”，也不是再生成候选。现有文件已经产出 3 条：

1. C01：CMIS 条件下的 Host/Media 收发方向，加上光纤型模块的电→光→电解释；
2. C02：高速数据、低速管理和供电/地是并行路径，不应画成一条串行流水线；
3. C03：OIF CPO 框架中 EIC/OIC/PIC 可承担的发送/接收功能，是对象级框架实例。

结构字段已经齐全；本轮人工合同应重点回答：

- C01 的两类来源是否共同覆盖标题中的方向与电光转换，而没有把 CMIS 的电介质可能性抹掉；
- C02 是否仍严格限定在 CMIS/OSFP 证据范围，标题会不会被误读为所有光模块的统一三路径实现；
- C03 是帮助读者理解功能分工的必要对象例子，还是应转到 PQ004；若它只是可选例子，就不应让 `PQ002 acceptance_complete` 依赖整批三条全部晋升；
- 3 条候选是否足以覆盖 TX、RX、边界条件和“功能骨架≠统一 BOM”，还是仍缺一条更直接的 TX/RX 功能拆解；
- `review_state` 应由 checker/receipt 的单一来源生成，避免 YAML 写 pending、实际运行已 pass；
- PQ001 依赖批次尚未 canonical 化，KN011–KN013 也未保留，任何写入决定都必须重新核对 canonical hash 与连续 ID。

候选已经有本地 `question_acceptance_effect`，但它目前只规定“全批三条晋升即完成”。建议在 receipt 前把实质 AC 写清：至少要求 TX 链、RX 链、边界条件、功能骨干/产品实例区分和证据覆盖全部通过。正式问题状态模型可在后续 schema 变更中统一处理。

## 6. 优先级总表

### P0：PQ002 本轮或晋升前必须做

1. 对现有 PQ002 三条候选做人工语义审计，并决定 C03 是否属于整批验收必要项；
2. 复核 PQ001 依赖、KN ID、source hash 和 embedded review state，形成可追踪 receipt；
3. 在任何 canonical 请求前解决 `scan.py --check` 的 25 个白名单失败，并验证 pre-commit 总闸；
4. 不把“一条 KN 关联”或“临时物化扫描通过”当作真实仓库已晋升；
5. 把 TX、RX、边界和实例/骨干区分写成实质 acceptance contract。

### P1：紧随其后的架构工作

1. 建立全局 claim registry/graph 与 KN/WHY 映射；
2. 将动态网页语义快照接入统一来源流程；
3. 把 denominator 变为排名请求的通用硬门；
4. 让读者标签由结构化 verdict 自动生成。

### P2：不要混入 PQ002

1. 继续 exact-SKU 公开网搜 QX-03 内部实现；
2. 扩展公司—路线投影或供货关系；
3. 排名“最主流”路线；
4. 大规模迁移历史研究包目录。

## 7. 最终判断

Cursor 的核心主张“停止横向扩题，优先纵向闭合”适用于 PQ002。但当前 workspace 已经比这八条建议所描述的状态更靠前：大多数小样已经存在，读者确定性分层也已经完成。真正应补的不是更多 proposal，而是三件事：

1. 对已经生成的 PQ002 三条领域知识候选完成语义与 scope 裁决；
2. 让 claim/蕴含/receipt 流程穿过真实仓库总闸，而不是只通过隔离的临时扫描；
3. 修正“一条 KN 即覆盖”以及“全批三条即完成”都可能过粗的验收语义，避免形式晋升替代实质回答。

在这三件事完成前，PQ002 可以进入候选晋升审查，但不能称为 canonical 已覆盖。
