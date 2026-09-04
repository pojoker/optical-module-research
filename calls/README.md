# 海外电话会与官网技术情报层 MVP

独立的假设与验证队列。它读取根目录的 `tree.yaml`、`route_bom.csv` 和
`points.csv` 来核验引用，但不会修改任何 canonical 文件。

在项目根目录运行一条命令完成校验与重建：

```bash
python3 -m calls all
```

输出位于 [`calls/out/`](out/README.md)。单独运行校验或渲染：

```bash
python3 -m calls check
python3 -m calls render
python3 -m unittest discover -s calls/tests -v
```

## 数据账本

- `universe.csv`：可调整的 14 家核心同业、上游使能方、系统设备商与下游验证公司池。
- `company_candidates.csv`：尚未晋级的发现候选。候选可以完成一手来源核验，但不进入
  公司时间线、主事件雷达或四季度覆盖率；只有人工批准后才迁移到 `universe.csv` 或
  `watch_entities.csv`。
- `company_tier_reviews.csv`：候选逐期正式披露复核。至少两个不同披露期且存在直接光学或
  邻近业务信号，才允许进入 `promotion_ready/promoted`；产品博客不能代替正式材料。
- `watch_entities.csv`：按事件持续监控、但不承担四季度材料义务的实体。
- `entity_relationships.csv`：带生效时间的一手来源实体关系，用于母子公司、品牌、并购、
  前身和业务承接去重；关系不生成 canonical 供货边，也不把品牌视为第二个经营主体。
- `sources.csv`：每家最近四个季度的槽位。一个槽位可登记多个 A/B/C 材料；
  尚未采集的槽位使用 `unknown` 类型/等级并填写缺失原因；公司官网署名技术博客
  作为 `official_technical_blog` 的 interquarter 来源登记；SEC/交易所等法定披露平台的
  季度或年度报告以 `regulatory_filing` 登记，与 transcript、earnings release 分开。
- `claims.csv`：原子陈述。`analyst_question` 与管理层事实/前瞻机械隔离；
  `corporate_author` 的 `technical_claim/technical_demo` 也与管理层商业确认机械隔离。
- `themes.csv`：受限需求、卡点、候选解法与双轨节点映射；可行性、稀缺性、
  可替代性始终分列。
- `validations.csv`：两条 claim 的支持、冲突、独立或证据不足关系。
- `commitments.csv`：前瞻承诺及后续正式材料兑现状态。
- `solution_links.csv`：只读引用现有 `point_id` 的潜在匹配；早期匹配必须写明缺证。
  该文件冻结为恰好 2 行（`SL001`/`SL002`），validator 拒绝新增。
- `constraint_requirements.csv`：把 reviewed 管理层 claim 原子化为带锚的全球约束要求
  （`CRQ*`）。`evidence_claim_ids` 只能引用 reviewed management claim，不能引用
  analyst/corporate_author；`comparator/target_value/unit` 必须同时为空或同时非空。
- `point_metrics.csv`：point 的量化事实（`PM*`）。本轮允许只有表头；数值必须能由该
  point 的原始引语与锚点直接支持，且 value 出现时必须带 unit 与 as_of。
- `technology_feedback.csv`：技术主张与后续管理层商业陈述的反馈账本。前瞻指引只能
  保持 `pending`；`confirmed/partially_confirmed/contradicted` 必须由管理层事实支持。
- `disclosures.csv`、`event_claims.csv`、`events.csv`、`event_evidence.csv`：把官网公告、
  官网博客等材料拆成“披露件 → 原子主张 → 公司事件 → 证据链接”。第一方公告默认只形成
  `asserted`，不会因为来自官网或已经人工核锚就自动升级为独立证实。

渲染器另生成 `technology-feedback.md`、机器可读的 `out/panorama-intelligence.csv`
和确定性派生 `out/positioning.json`。后者由 `build_detailed_capability_report.py`
可选读取，在 WorkBuddy HTML 中显示“海外电话会与官网技术情报”，并在各主题卡尾部追加
“国内能力定位”区块；没有定位文件时安全跳过。定位模块只输出 `basis=cell_only` 的同节点
对齐、真正可比的数值对比、证据覆盖缺口与固定 unsupported 原因，绝不生成公司对、
竞争/替代/合作/供货等商业结论。

CSV 是事实源，`out/` 只由渲染器生成，禁止手改。`raw/` 可保存合法取得的材料，
但默认被 Git 忽略；不得绕过付费墙或登录。

## 如何补齐季度材料与事件证据

1. 先把 `sources.csv` 中 `not_collected` 槽位替换或追加为真实 A/B/C 来源；同一
   槽位的多份材料保留不同 `source_id`。
2. 自动提取只能写 `candidate`。人工核对说话人、原文、定位、事实/前瞻属性和
   产品代际后，才改为 `reviewed`；驳回项保留为 `rejected`。
3. 能映射现有本体时填写 `cell_id`/`route_item_id`；不能映射时使用
   `mapping_track=unmapped` 并解释原因。
4. 跨公司判断写入 `validations.csv`。分析师问题可以展示关注点，但不得作为
   管理层确认或兑现证据。
5. 运行 `python3 -m calls all`。缺失、未知、冲突与证据不足会继续显示，不会被
   渲染器静默过滤。

## 公司升级闸门

1. 新名称先进入 `company_candidates.csv`；取得一手来源并人工复核后可标
   `source_verified`，但仍不算正式覆盖。
2. 只有持续产生高价值事件、且不需要连续季度经营材料时，晋级 `watch_entities.csv`。
3. 只有上市主体、最近四个可得正式期间均能逐槽登记，并能持续回答产品阶段、供给卡点、
   技术路线或需求兑现问题时，才晋级 `universe.csv`；晋级必须同一批补齐四个季度槽。
4. 被收购公司、子公司和品牌先登记 `entity_relationships.csv`；历史事件可以保留原主体，
   但公司数与独立证据不重复计算。

当前正式季度池为 39 家，事件监控层为 37 家，另有 7 家停留在发现队列。季度公司的
`universe.csv` 晋级必须同批登记四个不同季度槽；事件监控公司的晋级只要求连续两期一手
来源复核，不强制制造无意义的四季度材料。Ciena 四季使用公司 IR 托管的完整逐字稿；
`no_relevant_claims` 只表示已按登记范围复核后没有相关主张，不等于行业负面证据。产品公告
中的送样、GA、出货和试验默认仍是第一方 `asserted`；只有不同起源的独立来源支持才提升为
`corroborated`，且不代表有效产能增加或卡点解除。Lumentum 样本继续区分官网技术作者演示、
官方业绩材料和第三方逐字稿；系统没有独立验证 AAOI 所称的 MOCVD backlog。
