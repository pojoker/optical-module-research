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

- `universe.csv`：可调整的 39 家核心同业、上游使能方、系统设备商与下游验证公司池。
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

## 覆盖分级与证实力度语义（读者必读）

- **五级覆盖**：`out/README.md` 与每张公司卡显式分列「季度槽登记 → 可用来源 →
  陈述登记 → 已核陈述 → 已核事件」五级，分母固定为 `universe.csv` 中
  `enabled=yes` 的正式季度池公司数，watch 实体与发现候选不计入。每级公司数
  可从 `calls/*.csv` 直接复算。
- **信源底账 ≠ 结论覆盖**：`sources.csv` 的总行数（例如“39 家公司、166 行来源”）
  只是采集底账，不得单独用来表达研究结论覆盖；结论覆盖必须逐级看上表。
- **reviewed / anchor_reviewed 仅表示原文已核**：说话人、原文短引与锚点经人工
  复核；它不表示独立来源交叉证实。
- **corroborated 才表示独立来源交叉**：只有存在与第一方不同 `origin_group` 且
  独立于第一方（counterparty/regulator/observable_result）的已核证据支持时，
  事件才可标 `corroborated`；同一 `origin_group` 的多份材料（同源双证）不得
  升级为 corroborated。`asserted` 事件是第一方主张，不得表述为“已确认”。
- 事件状态在 `out/README.md` 和 `event-intelligence.json` 中 asserted/corroborated
  分列计数，corroborated 事件逐条列出 event_id 供复算。

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


## 日更抓取入口与覆盖边界（2026-09-09）

`daily_discovery.py` 从季度池、active watch 和未晋升候选读取监控名单，再按已核实体关系
归一化；抓取入口独立登记在 `discovery_config.json`。名单登记不会自动生成 URL。
此次配置覆盖 78/81 个归一化主体：39 个季度主体、32 个 watch 主体、7 个候选主体。
缺口为 Freiberger（未找到官方新闻目录）、Polariton（原域名跳转 Marvell，未冒充自有发行者）、
Xscape（混合媒体/博客栏目，已核公告详情缺正文）。配置数不能代替真实获取成功数或研究结论覆盖率。

IQE 和 Cisco 的具名对手方端点按每篇材料解析：命中已配置目标时保留 counterparty 路径；
未命中时仅这两个显式启用 `publisher_fallback` 的发行者来源回到自身 first_party。
同一篇 URL 不重复产生两份披露，第一方候选不会变成独立确认；所有结果仍需人工核验。
独立佐证还要求实际引句唯一点名目标，且不混有发行者自身名称或第一人称；全文其他段落提及
不构成支持。归属不清的引句保留主张候选并报告 `unresolved_claim_subject`，不产生独立证据。
`customer sampling` 可进入送样候选，`demonstrated our ability` 等经营措辞不再当作技术演示。

新列表优先设置 `article_path_pattern`，在截取前排除导航；设置该规则的列表不能用自身
meta 日期冒充文章。新闻栏目混博客而无符合配置类型的文章、未知 JSON 结构、缺少可解析
文章入口均显式报告失败，不作为健康零增量；窗口外的合法文章仍可产生真正的零增量。
Lumilens 只收官方卡片标记 Press release 的同域文章；Sivers 使用官方 press-only JSON
封装中的 HTML。季度 PDF 目录与 SEC submissions 没有冒充受支持的通用 JSON 数据源。

AAOI 改用实测可采的官方 newsroom，只代表该站公告；IR 财报覆盖仍需单独验证。
POET 使用公司专属 GlobeNewswire 原始发行托管列表，限定其 organization 和新闻详情路径，
不使用泛新闻聚合。FOC 和 Lumilens 按已核自有网站迁移入口，未更改监控实体或 CSV 关系账本。

HTTP 运行会输出逐端点 START/结果；`missing_endpoint`、列表失败、文章失败继续分列。
完整实跑与人工审阅之前，不得把本节的配置修复表述为全池有效覆盖或领域问题已回答。
离线演练使用 `calls/tests/daily_discovery_config.json` 对应固定测试实体；真实配置加载另有测试，
扩池不会要求原来的八份离线样本假装覆盖所有新端点。

首轮 79 端点实跑暴露的动态 IR 列表，按已核官方导航/接口切换 Q4 或 RSS；
显式文章路径可穿过 investor-relations 目录并允许空卡片链接，详情仍须提供标题、日期与正文。
坏 href 单条跳过，避免 ficonTEC 的外部链接拼写错误终止整页。Delta 仅解析官方数字 press
详情中的唯一 srcdoc 正文和发布日期；Mitsubishi 仅展开官网声明的新闻 JSON 数组，再取详情。
ASE、Semtech 的日期使用各自官方文章模板，未放宽为全文任意日期。网络超时、未支持列表、
文章缺日期仍是失败或待审，配置替换和本地回归通过不代表这些站点已全部恢复。

HTTP 请求成功数不等于有效采集数：缺发布日期或正文的响应仍会进入 invalid_item / 失败队列；
只有有效文章落在窗口内才计入披露候选，合法文章全部在窗口外时允许健康零项。
endpoint 总预算同时约束网络与解析；耗尽时保留已完成文章并标记 partial。

### 页面发布日期与详情请求（2026-09-10）

ASMPT、Accton、Semtech 按官网逐篇卡片绑定 URL 和发布日期，在详情请求以及条数截断之前
筛选时间窗口；日期未知的真实详情仍保留。Accton 的年标记只在同一时间轴内沿用，月报所属月
不当作发布日期；Semtech 的 P10/P20 分页和 AAOI 的 home 导航不当作文章。
429 会停止该端点本批后续文章，保留已完成记录及 Retry-After；此改动没有新增跨批冷却调度。
预算耗尽直接返回 partial，不再把同一次耗尽重复记为详情和列表解析两次事故。

补充 SUSS 文章标题区时间、EVG 具名发布稿日期、Source Photonics 正文发布行，以及 TE 明确
标注 Published 的时间。Source Photonics 同一篇发布行年份冲突时保留 UNKNOWN。
OpenLight 的站点专用 JSON-LD 规则用完整 h1 绑定标题，仍要求显式 URL 归属于当前文章；
读取本页面 datePublished 不表示外部媒体原文或活动在同日发布、发生。

页面发布时间与正文稿件日期可不同。三个受支持列表中的同 URL 卡片日期用于日更窗口；
不同的详情日期保存在原始结果 detail_date_observed，并写入现有 note，进入披露候选备注。
TE 的明确 Published 字段优先于正文日期。不得用图片路径、展会日程或全文第一个数字补日期。
现有事件候选仍按披露日期分组，其事件日期需要人工核验；本次没有重构事件日期模型。

本次 43 条旧拒收中核验到 38 个文章日期（HTTP 页面/列表 29 个、浏览器可见内容 9 个），
全在原 2026-08-26 至 2026-09-09 窗口外；另有 2 个分页、3 个日期未知或不适用的页面。
TE 当前 HTTP403 而普通浏览器可读，浏览器取证未接入定时任务；Sicoya403、Scintil限流及
Semtech间歇超时仍需分别观察。详见 `../docs/reviews/2026-09-10-overseas-details-dates.md`。
