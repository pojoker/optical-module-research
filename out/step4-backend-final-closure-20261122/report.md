# Step 4 光模块数据底座三刀止血、旧锚与待判收口、海内外原件抓核与正式封版报告（2026-11-22）

## 结论先行：后端数据底座正式封版，可直接衔接前端 `研序` 集成

工作包 `OPTICAL-STEP4-BACKEND-FINAL-CLOSURE-20261122` 授权范围内的 **“三刀止血”机器门加固、`points.csv` 旧文字/Markdown 锚全归一化清零、`triage.csv` 待判尾项裁决、海内外待审 `DRQ` 一手全文抓核与 10–11 月海外季报补槽、以及全量派生层重算** 均已落盘并通过独立字节级幂等核验。

七道机器门与全仓测试——`scan.py --selftest`（**`153/153`**）、`scan.py --check`（语料距今 `1` 天、缺席年报 `0` 家、不变量 `①–⑭` 全绿）、`render.py --verify`、`participation.py --check`（宇宙 `466`、确认 **`94`**、待确认 **`13`**）、`-m calls check`（`39` 公司 / **`180`** 信源 / **`79`** 主张 / **`60`** 雷达事件）、`sync_daily_queue.py --check`（**`97`** 行零漂移，`0` 条未知披露被静默归入噪音）以及裸跑 `PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 -m pytest -q`（**`495 passed, 189 subtests passed`，0 收集错误、0 排除、0 失败**）——退出码全部为 `0`。

至此，光模块产业链后端数据底座已实现结构、引语、行号锚点与时间新鲜度全链收口并正式封版，可直接供前端 **`研序`** 按明确准入契约读取集成。依据 [AGENTS.md](file:///Users/jowang/Downloads/optical-module-research/AGENTS.md) 纪律，机器门与测试全绿仅证明账本结构闭合、引语与本地原文连续匹配及未核线索严格隔离，不代表开放研究问题自动结案。

---

## 本轮实打实消除的错漏与数据缺口

### 1. 第一刀止血：内容台账 633 行真伪四档分级与 `\n` 行号闭环（[content_ledger.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/content_ledger/content_ledger.csv)）
- **消除假 `verified_local` 混标**：将此前混标在 `630` 条 `verified_local` 中的非连续表格拼接与节略条目全部程序化剥离（保持 16 列冻结 Schema 不变、UTF-8 BOM + `\n` 共 `634` 物理行）：
  - **`verified_local = 578` 条**（`v1_salvage` `322` + `step2_expansion` `220/220` + `step3_daily_2026q4` `36/36`）：100% 满足 `re.sub(r'\s+', '', verbatim_quote)` 在本地原文连续命中且 `#Lx..y` 切片命中（同时修复 `SJ24-22/C38/C51/C29` 共 4 处标点与跨页微瑕）；**前端 `研序` 仅将本档直接渲染为已核原话引用**。
  - **`table_normalized = 37` 条**（表格/流程图单元格 `" / "` 拼接，100% 片段命中原文）、**`segmented_verified = 15` 条**（`……` 节略连接，100% 片段命中原文）、**`inherited_v1_verified = 3` 条**（`C43/C48/C72` 多栏跨页表头嵌入词中，首尾 `>=20` 字锚命中）：**前端 `研序` 严格降级为可定位候选，禁止伪装连续原句**。
- **消除 `splitlines()` 分页符错行**：全表统一按 `text.split('\n')`（严禁把 `\f` 当换行）计量行号；科瑞技术 `CLG0633` 由错位的 `#L642..648` 精准修正为 **`#L630..631`**（`CLG0632` 保持 `#L642..648`），校准 18 条 `section_ref` 区间使 **237/237（100%）** 闭环命中，并同步刷新 [quote_verification_report.json](file:///Users/jowang/Downloads/optical-module-research/corpus/content_ledger/quote_verification_report.json) 与 [README.md](file:///Users/jowang/Downloads/optical-module-research/corpus/content_ledger/README.md) 至真实 `633` 条 / `26` 家口径。
- **机器门锁死**：[scan.py](file:///Users/jowang/Downloads/optical-module-research/scan.py) `_check_content_ledger` 实时校验四档枚举及 `verified_local` 全文连续 + `#Lx..y`（`\n`）切片命中。

### 2. 第二刀止血：消除 Daily 未知条目默认静默丢噪音 + 挽救 10–11 月漏抓海外季报/并购（[sync_daily_queue.py](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/sync_daily_queue.py)）
- **根除默认归噪音黑洞**：在 `_classify_overseas_noise()` 中彻底废除 `routine_pr_without_state_transition` 默认兜底（现为 **`0` 条**），仅保留四类明确高置信噪音（`award_ranking_hr_csr`、`investor_lawsuit_spam`、`ir_calendar_or_index_page`、`non_optical_corporate_line`），其余未知通稿一律诚实返回 **`unclassified`**（全量 `354` 条 / `66.42%`，单列于 [triage_stats.json](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/triage_stats.json) 供人工抽检召回率）。
- **历史种子诚实更名与确定性正向规则入池**：原 `TRIGGERED_OVERSEAS_DC_IDS` 更名为 `SEEDED_OVERSEAS_DC_IDS`（保留旧名兼容别名），新增 `_classify_overseas_positive_rule()` 正向标题触发器，将此前被误折入噪音池的 9 项 10–11 月核心披露（`MTSI FY26Q4`、`TSEM Q3`、`GFS Q3`、`VECO Q3`、`VECO×ACLS`、`SOI FY27H1`、`ANET Q3`、`CRDO×ORCL`、`KEYS FY26Q4`）及全部正向命中项 100% 纳入 [review_queue.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/review_queue.csv)（全表 `97` 行：`ingested_to_kb=54`、`pending_primary_text=2`、`pending_filing_anchor=5`、`watch_deferred=36`）。

### 3. 第三刀止血：负向剔除表按 `cut_category` 分类防碰撞与公司简称归一（[scan.py](file:///Users/jowang/Downloads/optical-module-research/scan.py)）
- 在 [scan.py](file:///Users/jowang/Downloads/optical-module-research/scan.py) 新增 `_norm_co_name()`（剥离中英文括号及 `股份有限公司/有限责任公司/有限公司` 后缀）并升级 `_check_relationship_tables`：
  - `consolidated_into_group_edge`（`25` 条）：校验 `replacement_edge_ids`（`E154/E163`）非空且 100% 存在于 `edges.csv`，不再误当供货证伪去撞集团合并边；
  - `non_supply_relation`（`6` 条，如 `CUT030` 源杰科技与中际旭创间接股东关系、母子公司担保）：豁免供货边碰撞，仅校验 `leaked_in_edges_csv != true`；
  - `non_optical_related_or_bad_debt`（`40` 条）+ `non_optical_counterparty`（`3` 条）= **`43` 条真否定**：同时执行原名与 `_norm_co_name` 简称归一双向无碰撞拦截（实测 `0` 碰撞）。

### 4. `points.csv` 旧文字/Markdown 锚全清零、`triage.csv` 尾项裁决与海内外一手原件抓核
- **`points.csv` 裸文字/Markdown 包装锚清零（`66 -> 0` 条，全表 `271 -> 272` 行）**：`8` 条 `[标题](URL)` 与 `4` 条混排 URL 解包为可点击 `https://` 直链；`3` 条美股 10-K（`P001/P003/P020`）对齐 SEC EDGAR `.htm` 直链；`51` 条本地年报/招股书旧文字锚全部核定为真实 `corpus/<path>#L<start>..<end>`（按 `\n` 闭环），最终 **`193` 纯 HTTP + `20` 首位 HTTP 多锚 + `59` 首位 `corpus/` 路径 = `272/272`（100% 可机读定位）**；既有 `P001..P276` 引语零改动，`P074` `检索日期 == "2026-11-21"` 完整保留。
- **国内 11 条 `DRQ` 巨潮核查与 `triage` 收尾**：新落盘 `6` 份巨潮 `%PDF-1.7` 原件至 `corpus/ir/`；核获云南锗业深交所正式公告 `2026-057`（`1225676124.PDF`），将媒体概数“2.7 亿元”校准为精确法定值 **`18,856万元 -> 26,999万元`（调增 `8,143万元`，目标折合 4 英寸 `45万片/年`）** 更新 `P202`；核获天准科技（`688003`）2026 半年报 p.14（`1225482975.PDF#page=14`）工业富联 CPO 量产项目在线 AOI 首批小批量订单且部分已交付现场，新增 **`P277`（`EQ6, 生产中, A股`）**；东山精密（泛称小批量光芯片外售未细分 CW）、汇绿生态、联特科技、锐捷网络（仅 400G LPO 量产且捆绑自有交换机不单独外售）、景旺电子、华工科技（零原产地关税豁免表述）均核清边界转 `ingested_to_kb`；沪电股份（交换机/超节点树外 PCB）与经纬辉开（仅间接参股铱加 7.71% 不并表+科研原型验收）转 `watch_deferred`。同时在 [triage.csv](file:///Users/jowang/Downloads/optical-module-research/triage.csv) 将 `600552` 凯盛科技与 `688307` 中润光学裁决为 `驳回-非本格`，[参与识别.csv](file:///Users/jowang/Downloads/optical-module-research/out/参与识别.csv) 刷新为 **`已确认参与=94` 家、`待确认=13` 家**。
- **海外 32/33 篇官网 HTTP 200 全文归档与 `calls` 时间线推进至 2026-11-18**：在 `corpus/web/step4_20261122/` 落盘 `32` 篇 `.html + .txt` 快照与 SHA-256 清单；白纸黑字核实 **Lumentum FY27Q1（`DRQ0016`）** CEO 首段确有原句 `"During the quarter, we secured our second major NPO/CPO win, backed by purchase commitments exceeding $5 billion."`，并锁定四重严格边界（`NPO/CPO` 合并口径非纯 CPO、未披露客户与履约年限、属跨期承诺而非当季 `12.626亿美元` 净营收、无 `200G EML` 专项积压拆分）；录入 `Marvell×Lumentum` 全股票并购协议（`EV037/TL9006`，预计 `H1 CY2028` 交割、当前未交割）、`Tower×中际旭创` 正文逐字升级（`EV036/TL9002`，美加州厂 `PH18M` 早期生产）、`Tower Q3` 硅光年化 `11亿美元` 目标（`CL081/EV056`）、`GFS×Marvell` SiGe 扩产长约（`EV057/TL9008`）、`Soitec FY27H1` Photonics-SOI 约 `12亿美元` 带现金定金产能预留协议（`CL083/EV059`）、`POET Q3` 3 万只光引擎顺延至 `2027Q2`（`CL079/EV055`）、`Credo×Oracle` OCP 光模块遥测规范获批（`EV060/TL9011`）。[sources.csv](file:///Users/jowang/Downloads/optical-module-research/calls/sources.csv) 由 `167` 行扩至 **`180` 行**（最新 `published_date` 由 `2026-08-17` 推进至 **`2026-11-18`**，11 家公司无损滚动季度槽位），`events.csv` 扩至 **`60` 条**（`EV001..EV060`），[relationship_timeline.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/relationship_timeline.csv) 扩至 **`458` 行**。

---

## 客观仍留白的 7 项外部受限项（诚实挂起于 `review_queue.csv` `pending_*`）

除上述已全量闭环的条目外，以下 **7 项** 因源站动态空壳、法规公报待调、私企未公开、商业 NDA 保密或并购未交割等客观外部边界，严格留置于 `pending_primary_text`（2 项）与 `pending_filing_anchor`（5 项），绝不强绕反爬、绝不虚构锚点：

1. **`DRQ0037`（`pending_primary_text`）Lightwave Logic × 鸿海（`DC_4B0F75924A65`）**：QuoteMedia 源链静态 GET 返回 `p_chars=0` 空 JS 壳，LWLG 官网新闻页为 Issuer Direct 动态嵌入组件；严守不绕动态壳红线不入正史（公开元数据指向鸿海科技集团 Siphcomm 部门科技日 SOH 样机演示，非 `FIT 06088.HK` 量产）。
2. **`DRQ0046`（`pending_primary_text`）北美 CSP 与进出口合规政策池**：涉及 FCC 26-50 规则边界与商务部/科技部 2026 年第 48 号出口技术目录公告，待调取官方公报正式条文逐款核对，隔离二手游说报道。
3. **`DRQ0048`（`pending_filing_anchor`）微见智能（`UNLISTED_MV`）**：未上市私企（已纳管 `tree.yaml` 观察名单），暂缺第一方官网产品规格书存档、IPO 辅导/申报稿或上市客户具名法定公告。
4. **`DRQ0049`（`pending_filing_anchor`）镭神技术（`UNLISTED_LS`）**：未上市私企（已纳管 `tree.yaml` 观察名单），猎奇招股书转引 27% 全球光耦合台数份额属第三方估算，暂缺独立一手能力锚。
5. **`DRQ0050`（`pending_filing_anchor`）科瑞技术（`002957`）U11 具名客户归属**：2025 年报 p.15 能力点（`P275/P276`）已入库，但海外客户受 NDA 约束仅匿名披露为“海外头部客户/海外光器件品牌企业”，`Lumentum / Coherent` 具名边须待双方监管文件披露。
6. **`DRQ0052`（`pending_filing_anchor`）长光华芯（`688048`）200G EML 量产跃迁**：`2026-09-08` 互动易明确 `200G PAM4 EML` 仍在客户端验证阶段、未获批量大单，须待法定定期报告或投关书面确认认证量产后再升格。
7. **`DRQ0053`（`pending_filing_anchor`）利扬芯片（`688135`）拟购众望达光电 51% 股权**：`2026-11-14` 收购协议公告（`1225671802.PDF`）已归档 `corpus/ir/688135/`，但原件明确审计评估尚未定稿、尚待临时股东会审议批准且**尚未办理股权交割**，交割并表前禁入 `points.csv`。

（另：`triage.csv` 中 `FIT` 鸿腾精密 `06088.HK` 2025 年报仅见 CPO 合作与战略部署而无量产出货实证，以及 `三安光电+M2b` 扫描待判共 `12` 条历史 `triage` 待判项按既有口径诚实保留，对应参与识别 `待确认=13` 家；是德科技 `KEYS FY26Q4` 因属 `WATCH_KEYS` 事件监控主体归入 `watch_deferred` 留痕。）

---

## Step 0–Step 4 全周期封版总账对照表

| 账本 / 校验指标 | 初始基线（Step 0） | Step 2 收官 | Step 3 收官 | **Step 4 封版（当前）** | Step 4 收口增量说明 |
| --- | ---: | ---: | ---: | ---: | --- |
| `corpus/_frozen.csv` / `tree.yaml` 宇宙分母 | `463 / 461` | `463 / 463` | `466 / 466` | **`466 / 466`** | 宇宙内缺席年报 `0` 家 |
| `out/参与识别.csv` 确认 / 待确认 | `89 / —` | `90 / —` | `93 / 15` | **`94 / 13`** | 新增 `688003` 天准科技确认；驳回凯盛(`600552`)、中润(`688307`) |
| `points.csv` 能力点（无直链/路径裸锚数） | `271 (66)` | `269 (66)` | `271 (66)` | **`272 (0)`** | 66 条旧文字/Markdown 锚清零 + 新增 `P277` 天准科技，`P074` 日期保留 |
| `capability_details.csv` 细化能力表 | `181` | `183` | `187 (93司)` | **`188 (94司 / 38格)`** | 同步重建 PDF 与封版细化全景 HTML |
| `content_ledger.csv` 四档分级 | `0` | `597` | `633 (630/0/0/3)` | **`633 (578/37/15/3)`** | 剥离表格拼接/节略假连续行，修复 `CLG0633` `#L630..631`（`\n`） |
| `relationship_timeline.csv` / `edge_negative_cuts.csv` | `0 / 0` | `446 / 74` | `451 / 74` | **`458 / 74`** | 升级 `TL9002` + 新增 `TL9006..TL9012`；43 真否定简称归一 `0` 碰撞 |
| `daily_review/review_queue.csv` 审核池 | `0` | `0` | `55 (15/32/8/0)` | **`97 (54/2/5/36)`** | 废除默认静默噪音（改 `unclassified=354`），挽救 10–11 月季报/并购 |
| `calls` 信源 / 主张 / 披露 / 雷达事件 | `166/70/—/34` | `166/70/50/34` | `167/72/52/36` | **`180 / 79 / 82 / 60`** | 32/33 海外官网全文落盘，最新财报由 `08-17` 推至 **`2026-11-18`** |
| `scan.py --selftest` 内存回归用例 | `53` | `119` | `139` | **`153`** | 新增 `\n` 行切片、`verified_local` 真连续、`cut_category` 与简称归一单测 |
| 裸跑 `python3 -m pytest -q` | `exit 2` | 需忽略参数 | `487 passed` | **`495 passed, 189 subtests`** | 含新建 [test_step4_backend_closure.py](file:///Users/jowang/Downloads/optical-module-research/tests/test_step4_backend_closure.py)，全仓裸跑 `exit 0` |

---

## 衔接前端 `研序` 集成的读取契约与交付清单

1. **核心交付产物**：
   - 结构化终验摘要：[verification-summary.json](file:///Users/jowang/Downloads/optical-module-research/out/step4-backend-final-closure-20261122/verification-summary.json)
   - 封版细化全景 HTML：[光模块产业链全景图_公司能力细化版.html](file:///Users/jowang/Downloads/optical-module-research/out/step4-backend-final-closure-20261122/光模块产业链全景图_公司能力细化版.html)
   - 公司能力明细表与 PDF：[capability_details.csv](file:///Users/jowang/Downloads/optical-module-research/capability_details.csv)、[光模块产业链公司能力明细.pdf](file:///Users/jowang/Downloads/optical-module-research/output/pdf/光模块产业链公司能力明细.pdf)
   - 海外派生 JSON 投影：[event-intelligence.json](file:///Users/jowang/Downloads/optical-module-research/calls/out/event-intelligence.json)（`60` 事件）、[positioning.json](file:///Users/jowang/Downloads/optical-module-research/calls/out/positioning.json)
2. **前端 `研序` 对接四条读取准则**：
   - **内容台账引用分级**：读取 `corpus/content_ledger/content_ledger.csv` 时，仅 `quote_verification_status == "verified_local"`（`578` 条）可直接作为逐字已核原话展示；其余三档（`37 + 15 + 3 = 55` 条）仅作可回跳原文行号的线索候选；本地行号一律按 `text.split("\n")` 1-based 闭区间解析。
   - **能力点全可点击/定位**：`points.csv` 全部 `272` 行 `锚点URL` 均以 `https?://` 或 `corpus/` 真实路径开头，可直接绑定前端证据抽屉。
   - **海外事件状态显式透出**：渲染 `calls/out/event-intelligence.json` 时保留 `lifecycle_stage`（`announced / demonstrated / sampling / first_shipment / delayed / scaled`）与 `event_status`（`asserted / corroborated`），不把未交割并购（`EV037/EV058`）或展台演示（`EV045/EV046/EV052/EV054`）渲染为量产落地。
   - **待审池严格隔离**：`corpus/daily_review/review_queue.csv` 中 `pending_*`（`7` 条）与 `watch_deferred`（`36` 条）仅供研究台待办追踪抽屉展示，不混入已确认公司能力主视图。
