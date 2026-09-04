# 光模块数据质量与消融独立复核委托书

> 状态：待 Kimi / Cursor 独立复核
>
> 固定基线：`pojoker/optical-module-research@63d426b15b4c2e842ac9569f09febd6dd2d8ff5f`
>
> 审计时点：2026-09-04
>
> 性质：只读审计输入，不是修复授权，也不是已裁决结论

## 技术摘要

当前仓库的结构校验、引用闭合和主要主键总体可用，但初步画像显示，若直接把这些表用于公司比较、路线判断或投资结论，可能出现五类语义风险：分类字段被过程备注污染、不同技术能力被粗粒度节点等价、海外“资料槽位覆盖”被误读成“形成研究结论”、第一方主张被误读成独立证实，以及不同业务范围和单位的经营量被放入同一张“出货量”表。

本委托书不要求审阅者接受上述判断。Kimi 与 Cursor 必须分别复算基线数字、寻找反例，并对每项假设给出 `confirmed / partially_confirmed / rejected / insufficient_evidence` 四选一结论。任何消融只有在依赖、读者影响和回滚路径均被说明后，才可提交用户裁决。

## 一、审计目标与判定边界

### 1.1 要回答的问题

1. 当前数据是否足以安全回答“哪个公司具备什么能力、处于什么阶段、与哪条产品路线有关”？
2. 哪些字段或表会诱导读者作出比证据更强的结论？
3. 哪些结构没有承载真实生产数据，或者可以从更小的 canonical 集合确定性生成？
4. 删除、派生或合并这些结构后，哪些读者产品、校验器和日更流程会受到影响？

### 1.2 本轮不判定什么

- 不判断任何股票是否值得投资。
- 不自动把候选晋升为 canonical。
- 不因测试通过而判定领域结论正确。
- 不把公司第一方披露自动视为独立事实。
- 不把能力节点重合自动视为产品供货、路线采用或量产规模证据。

### 1.3 审计单位

| 数据集 | 预期粒度 | 主要用途 |
|---|---|---|
| `points.csv` | 一条公司 × 能力节点 × 证据判定 | 公司能力映射 |
| `edges.csv` | 一条供方 × 需方 × 期间 × 关系证据 | 具名关系观察 |
| `triage.csv` | 一次扫描命中或人工线索的处置 | 去重、驳回、待判 |
| `route_bom.csv` | 一条产品路线 × BOM分组 | 产品路线需求 |
| `shipments.csv` | 当前实际混有披露量、聚合量与情景量 | 经营量观察/推断 |
| `macro_evidence.csv` | 一条宏观量化主张 | 首页与路线背景 |
| `calls/sources.csv` / `claims.csv` | 海外来源槽位 / 原子主张 | 季度与技术情报 |
| `calls/disclosures.csv` / `event_claims.csv` / `events.csv` / `event_evidence.csv` | 披露件、主张、事件、证据关系 | 海外事件情报 |

## 二、必须独立复算的基线观察

以下数字是待核观察，不是既定事实。两位审阅者必须从固定提交重新计算，并报告分母、过滤条件与差异。

| ID | 待复算观察 | 初步值 |
|---|---|---:|
| B01 | `points.csv` 行数 / 公司数 | 271 / 155 |
| B02 | `判定等级` distinct 数 | 200 |
| B03 | `判定等级` 含括号型过程说明的行数 | 195 |
| B04 | `锚点URL` 以 `http` 开头的行数 | 193 / 271 |
| B05 | `triage.csv` 重复 `hit_id` / 缺会话日期 | 2组 / 19行 |
| B06 | `shipments.csv` 行数 / 公司数 / B级行数 | 103 / 36 / 100 |
| B07 | `shipments.csv` 已填写校准实际值 | 1 / 103 |
| B08 | 海外 enabled 公司 / 无 claim 公司 | 39 / 27 |
| B09 | 海外 claims 前5家公司占比 | 48 / 70 = 68.6% |
| B10 | 海外 events 中仅一条 evidence | 31 / 34 |
| B11 | event evidence 的 first-party 占比 | 34 / 37 |
| B12 | `macro_evidence.csv` 多URL字段 / C级主张 | 15 / 21（分母均为31） |

复算时至少检查：主键唯一性、空值率、枚举基数、时间范围、外键覆盖、业务键近重复、来源集中度、证据独立性和同表粒度一致性。

## 三、待证伪假设

### H1：`points.csv` 的“判定等级”不是稳定分类字段

**假设**：该字段同时装入等级、阶段、审阅者身份、取证过程、疑点和建议，导致无法稳定过滤，并让“已入点”与“仍待复核”同时存在。

**必须核验**：

- 复算 distinct 值、标准前缀和自由文本比例。
- 全量检查包含 `待复核`、`锚待`、`可降`、`疑`、`证据强度弱` 的行。
- 至少核验 `P088`、`P137`、`P146`、`P164`、`P175`、`P225`。
- 判断这些行是数据错误、字段命名错误，还是仅界面误读风险。

**反例要求**：找出至少三类确实需要保留在等级字段内、且不能移到 `review_note` 的信息。找不到时明确写“未找到”。

### H2：粗粒度能力节点会制造错误技术等价

**假设**：`C5 = DSP/Driver/TIA/CDR/主控MCU` 把功能、设计难度和路线相关性不同的芯片合为一格；通过 cell overlap 生成的路线线索可能把 MCU 或泛称 IC 当成 DSP/TIA 能力。

**必须核验**：

- 比较 `tree.yaml:C5`、`route_bom.csv:RB003/RB004/RB008/RB009/RB013/RB014` 与全部 C5 points。
- 单独审阅 `P089`、`P195`、`P225` 是否足以支持相关 route item。
- 检查 `M1 = InP/GaAs/SOI`、`MOD1 = 800G/1.6T` 是否存在同类误等价。
- 区分“节点用于读者导航”与“节点用于机器推导”两种风险。

**反例要求**：证明当前任何机器或页面是否已经阻止了上述越级；若只能依靠备注而非结构阻止，应判为未阻止。

### H3：海外来源覆盖被误读成研究结论覆盖

**假设**：39家公司均有可用 source 槽位，但27家公司没有 claim；用“39家公司、166个来源”概括研究覆盖会掩盖高度集中的有效内容。

**必须核验**：

- 按 company 计算 available sources、reviewed claims、events 和最近日期。
- 计算 claims 的公司集中度，并列出零 claim 公司。
- 区分 `slot coverage`、`source retrieved`、`claim extracted`、`claim reviewed`、`event formed` 五级覆盖率。
- 判断当前页面和报告分别展示了哪一级覆盖。

**反例要求**：检查零 claim 是否代表“审阅后无实质信息”，而不是“没有研究”；两者必须分别计数。

### H4：reviewed / asserted / corroborated 容易被混读

**假设**：多数海外 event 只有单一第一方证据，因此“reviewed event”仅能表示原文已核，不能表示事件获独立证实。

**必须核验**：

- 复算每个 event 的证据数与 `independence_class`。
- 检查 `event_status` 与 evidence independence 是否一致。
- 核验 `EV001 → EE001 → ECL001 → D_AAOI_20260309_ORDER` 的完整链。
- 找出所有达到 counterparty 或独立交叉证实的事件。

**反例要求**：寻找至少三例多来源或对手方证据；不足三例时报告实际数量，不补造。

### H5：`shipments.csv` 混合了不可比较的测量粒度

**假设**：模块“万只”、器件“万个”、设备“台”、材料“千克”、PCB“平方米”和行业出口额同时进入出货表，使横向比较或聚合没有业务含义；同时表名“推断层”与100条B级直接披露不一致。

**必须核验**：

- 按 `单位`、`cell_id`、产品范围、直接披露/推断/情景重新分组。
- 检查所有B级行是否真为直接披露，并检查C/D行是否实际被读者使用。
- 对照 `docs/adr/0001-shipment-inference-layer.md`，判断实际数据是否偏离原设计。
- 检查 `校准实际值/误差/校准日期` 对B级披露行是否有用途。
- 明确哪些行可比较、哪些只能单行展示、哪些应退出生产表。

**反例要求**：给出至少一个安全的跨公司比较组，并写清共同业务范围、期间和单位；无法形成时明确说明。

### H6：证据锚字段格式不统一，存在不可追溯风险

**假设**：`points.csv.锚点URL` 中包含 `有锚`、Markdown链接、本地扫描说明和复用前一行等多种表示，字段名与内容合同不一致。

**必须核验**：

- 全量分类 direct URL、Markdown URL、local reference、ledger reference、placeholder、invalid。
- 对所有 placeholder 和非直接URL检查是否能通过其他字段唯一定位原文。
- 随机抽取10条 direct URL 和10条非 direct URL，验证可访问性与引语定位。
- 不得把“页面能打开”当作“引语被原文支持”。

### H7：`edges.csv` 同时承担关系与指标，可能误导供货判断

**假设**：实名关系、匿名客户槽位、客户集中度、跨年重复观测和解匿推断共存于一表，但没有显式 `relation_type` 与 `product_scope`，容易把公司整体客户关系投射为光模块具名供货。

**必须核验**：

- 复算实边、半边、推断A/B及有无数值的分布。
- 抽查20条实边、全部4条推断边、所有同供需方重复组。
- 判断每条是否明确到光模块/器件/设备产品范围。
- 检查九页前端和其他读者是否把后台 edge 直接表述成光模块供应关系。

### H8：宏观证据不是原子来源记录

**假设**：单行多URL、混合“机构报告/厂商规格”、搜索页与二手互引造成来源独立性不可计算。

**必须核验**：

- 全量审阅31条，因为样本较小。
- 对每条拆分 claim、source、source type、primary/secondary、publication date、retrieval date。
- 检查 `MC001`、`MC002`、`MC003`、`MC004`、`MC011`、`MC012` 是否存在口径跳跃或回声室。
- A/B等级只在一手材料直接支持同一口径时通过。

### H9：存在低成本基础完整性缺口

**假设**：`triage.csv` 的2组重复 hit ID 与19条缺日期说明现有扫描门没有覆盖最基本的事件键和时间完整性。

**必须核验**：

- 判断重复行是同一命中的截断片段、合法多片段，还是主键设计错误。
- 判断缺日期是否集中在同一批次，并能否从来源恢复。
- 提出最小稳定测试，但不要在本轮实现。

### H10：存在未承载生产价值的结构

**假设**：空表、两行 legacy 表和多套实体/证据注册表的维护成本超过当前数据规模带来的价值。

**必须核验**：

- `questions_manual.csv`：0行，但被 `scan.py` / `render.py` 读取。
- `calls/point_metrics.csv`：0行，但有 schema、validator 和测试。
- `calls/solution_links.csv`：2行，均为 `insufficient` 且被精确冻结。
- `calls/constraint_requirements.csv`：2行，数值三元组全空。
- `calls/technology_feedback.csv`：4行。
- `company_candidates.csv`、`watch_entities.csv`、`universe.csv` 的名称重叠与生命周期语义。
- `sources/claims` 与 `disclosures/event_claims/event_evidence` 的真实职责是否重复。

**反例要求**：每个建议保留的表必须指出一个当前正在使用、且无法从其他表确定性派生的读者可见结论。

## 四、候选消融方案——只供核验，不是执行清单

审阅者必须把每一项归入以下一种，不允许只写“建议优化”：

- `remove_now`：没有生产数据或读者价值，删除后仅需清理死代码。
- `derive_not_store`：仍有读者价值，但可由 canonical 确定性生成。
- `collapse`：真实语义存在，但当前拆表超过规模需要，应合并。
- `retain`：承载不可替代的生产事实、审计边界或多对多关系。

| 候选 | 初步分类 | 必须核验的依赖 |
|---|---|---|
| `questions_manual.csv` | remove_now | `scan.py`、`render.py`、相关测试 |
| `calls/point_metrics.csv` | remove_now | positioning schema/validator/tests |
| `calls/solution_links.csv` | remove_now 或冷冻文档 | renderer、validator、legacy报告 |
| `calls/constraint_requirements.csv` | remove_now 或 collapse | positioning 输出是否有真实读者 |
| `calls/technology_feedback.csv` | collapse | 能否并入 claim/event review note |
| 三套海外主体表 | collapse | 日更监控层级、候选晋级、季度完整性 |
| 两套海外来源/主张结构 | collapse 或 retain | 多主张、多来源、证据独立性是否真实发生 |
| `shipments.csv` 推断/校准结构 | collapse | 直接披露量与真实推断应否分离 |
| `capability_details.csv` | derive_not_store | PDF/HTML构建、macro指标引用 |
| `archive/**` | remove_now（从新生产仓库） | 证明无运行时与证据锚依赖 |
| 九页网页 | retain | 用户已明确要求跟踪发布快照；仍标非 canonical |

## 五、Kimi 独立审计任务

### 角色

你是领域语义与证据审计者。优先判断“原文究竟支持到哪里”，而不是代码是否接受这条记录。

### 必读范围

1. `AGENTS.md`
2. `docs/control/PROJECT_CHARTER.md`
3. 本委托书
4. `tree.yaml`、`points.csv`、`route_bom.csv`、`edges.csv`
5. `shipments.csv`、`macro_evidence.csv`
6. `calls/universe.csv`、`calls/sources.csv`、`calls/claims.csv`
7. `calls/disclosures.csv`、`calls/event_claims.csv`、`calls/events.csv`、`calls/event_evidence.csv`

禁止读取 `archive/**`、旧分支、旧 worktree、完整 agent 轨迹或其他审阅者输出。需要联网抽核时，只使用公司披露、监管文件、标准组织和其他一手来源；二手材料只能用于发现，不能单独支持 A/B 级裁决。

### 重点任务

- 主审 H2、H4、H5、H6、H7、H8。
- 对 H1、H3、H9、H10 提供语义层反例和风险判断。
- 不得因备注“已核”“通过”而跳过原文核验。
- 对每个 `confirmed` 结论至少给出两个具体行例；对每个 `rejected` 结论至少给出一个反例。

### 输出

写入：`docs/reviews/2026-09-04-kimi-data-quality-semantic-audit.md`

只写该文件，不修改 canonical、代码、测试或生成物。

## 六、Cursor 独立审计任务

### 角色

你是数据契约、可复现性和消融影响审计者。优先判断 grain、key、enum、join、lineage 与删除后的真实依赖。

### 必读范围

1. `AGENTS.md`
2. `docs/control/PROJECT_CHARTER.md`
3. 本委托书
4. 本委托书涉及的 CSV/YAML
5. `scan.py`、`render.py`、`participation.py`
6. `calls/schema.py`、`calls/validator.py`、`calls/event_intelligence.py`、`calls/positioning.py`
7. `calls/daily_discovery.py`、`build_detailed_capability_report.py`
8. 对应测试文件

禁止读取 `archive/**`、旧分支、旧 worktree、完整 agent 轨迹或 Kimi 输出。不要修改代码来证明方案；使用临时目录或只读脚本复算。

### 重点任务

- 主审 H1、H3、H9、H10。
- 对 H2、H4、H5、H6、H7、H8 复算机械证据和依赖影响。
- 为每个候选消融项列出读取者、写入者、测试、生成物和迁移顺序。
- 区分“删除表即可”“须先改变生成器”“会改变 reader-visible 结论”三类影响。

### 输出

写入：`docs/reviews/2026-09-04-cursor-data-quality-contract-ablation-audit.md`

只写该文件，不修改 canonical、代码、测试或生成物。

## 七、两位审阅者共同输出合同

每份报告必须包含以下结构：

1. **独立结论摘要**：不超过10条。
2. **基线复算表**：B01–B12，包含公式、分母、结果和差异原因。
3. **假设裁决表**：H1–H10逐项填写 verdict、severity、confidence。
4. **证据与反例**：具体文件、ID、原文锚、支持范围和不能推出什么。
5. **消融矩阵**：`remove_now / derive_not_store / collapse / retain`。
6. **依赖与迁移风险**：受影响代码、测试、页面、日更流程和回滚点。
7. **最小修复顺序**：每一步只解决一个语义问题，禁止顺带扩 schema。
8. **未解决问题**：证据不足时使用 `insufficient_evidence`，不得猜测。

裁决字段固定为：

```yaml
hypothesis_id: H1
verdict: confirmed | partially_confirmed | rejected | insufficient_evidence
severity: critical | high | medium | low
confidence: high | medium | low
evidence:
  - file: points.csv
    record_ids: [P088]
    observation: ...
counterexamples: [...]
reader_impact: ...
recommended_action: remove_now | derive_not_store | collapse | retain | remediate_only
```

## 八、交叉裁决规则

1. 两位审阅者在提交前不得读取对方输出。
2. 机械计数分歧由可复现脚本、固定提交和明确分母裁决。
3. 领域语义分歧由同一主体、同一对象、同一时间、同一产品范围的一手证据裁决。
4. 不能用“链接数量更多”替代来源独立性；同源转载只算一个 origin group。
5. Kimi/Cursor 一致不等于自动授权。任何删除、合并、重判或 canonical 修改仍须用户新授权。
6. 若一方认为 `remove_now`、另一方认为 `retain`，默认保留，直到明确指出读者价值和不可替代数据。
7. 若一方发现当前读者已经输出错误或过强结论，立即标记 `stop_and_escalate`，不要顺手修复。

## 九、验收标准

本轮双审只有在下列条件同时满足时才算完成：

- B01–B12全部复算，有差异时解释过滤条件。
- H1–H10全部裁决，没有空白项。
- 每个高严重度结论都有记录级证据和至少一个反例搜索结果。
- 每个消融项都有依赖清单、reader impact 和回滚策略。
- 明确区分事实错误、字段合同错误、展示误读风险和架构过重。
- 两份报告均确认未修改 canonical 文件。

下一步应先比较两份独立报告，再由用户选择：只修数据质量、只做低风险消融，或另立受控迁移工作包。不要在审计阶段开始实现。
