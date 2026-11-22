# Step 3 高价值 Daily 并库、持久待审池、v6 宇宙扩容与全仓机器门终验报告（2026-11-21）

## 结论先行

工作包 `OPTICAL-STEP3-DAILY-AND-V6-20261121` 授权范围内的 2026 年 9–11 月国内/海外一手已核增量并库、科瑞技术（`002957`）2025 年报能力点收编、Daily 95/5 持久待审池建设、`v6` 宇宙分母对称扩容（`463 -> 466`）、遗留硬编码测试修复与全量派生层重算均已落盘，并通过独立程序化核验。七道机器门——`scan.py --selftest`（`139/139`）、`scan.py --check`（语料距今 `0` 天、缺席年报 `0` 家、不变量 `①–⑭` 全绿）、`render.py --verify`、`participation.py --check`（宇宙 `466`、确认 `93`、待确认 `15`）、`-m calls check`（`39` 公司 / `167` 信源 / `72` 主张 / `36` 雷达事件）、`sync_daily_queue.py --check`（`55` 行零漂移）以及裸命令 `python3 -m pytest -q`（**`487 passed, 157 subtests passed`，0 收集错误、0 排除、0 失败**）——退出码全部为 `0`。

依据 [AGENTS.md](file:///Users/jowang/Downloads/optical-module-research/AGENTS.md) 第 4 节与第 7 节纪律，机器门与自动化测试全绿只代表账本结构闭合、引语在本地原文逐字存在、引用键不悬空及未核线索隔离到位，不代表领域研究问题自动结案。未经一手全文或法定公告核证的海外并购/指引与媒体扩产线索均严格留置于待审队列，未混入正式实证主张。

---

## Step 3 核心交付内容与证据边界

### 1. 国内一手 9–11 月增量并库与科瑞技术（`002957`）年报收编

幂等脚本 [ingest_domestic_daily.py](file:///Users/jowang/Downloads/optical-module-research/out/step3-daily-and-v6-20261121/ingest_domestic_daily.py) 将只读日更源中经核实的 `81` 个股票代码共 `332` 份投关 PDF 及 `.pdf.txt` 旁车同步至 `corpus/ir/`，并对 `93` 个代码的互动易/上证 e 互动问答执行确定性去重（`46,276 -> 45,639` 行，剔除 `637` 条无日期预抓或同文重复记录，全量 `113` 个 `qa.jsonl` 通过七键与引语锚校验）。

根级 [points.csv](file:///Users/jowang/Downloads/optical-module-research/points.csv) 共更新 `15` 条既有能力点并追加 `2` 条新能力点（总行数 `269 -> 271`）：联讯仪器 `P061` 上市标签由 `未上市私企` 更新为 `A股`（科创板 `688808`）；云南鑫耀 `P202` 挂接母公司云南锗业（`002428`）2025 年报逐字原句（全年生产磷化铟晶片 `10.01万片`）；罗博特科 `P059/P172/P173` 补入现款 INS2/INS3 批量交付、INS4 尚处 NPI、`2026-11-16` 首次书面确认“英伟达系 ficonTEC 的客户之一”（批量归属与 TH6 独供仍受商业秘密限制）及瑞士约 `7,867` 万元整线属 OCS 而非 CPO；天孚通信 `P271/P155` 严格分列 CPO 配套稳定量产交付与 NPO 预计 `2027` 年逐步上量；中际旭创 `P074/P138`、新易盛 `P073`、剑桥科技 `P077`、炬光科技 `P117/P169`（大于 36 通道 V 型槽转批量与 MPLA 技术许可区分）、博众精工 `P206`（中南鸿思 `60%` 股权交割耦合设备与苏州博众半导体共晶贴片分主体建档及“订单并不直接等同于收入”警示）以及华工科技 `P209`（保留原引语与原锚不变，仅在备注说明前三季度“光互联业务” `65.39亿元` 与年报分部统计边界）均按一手原件落盘；景旺电子 `P031` 与珠海鼎泰芯源 `P257` 保持字节级零改动。

针对巨潮新抓入库的 [002957__em_科瑞技术_em__2025_2025年年度报告.pdf](file:///Users/jowang/Downloads/optical-module-research/corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf) 第 15 页披露，[points.csv](file:///Users/jowang/Downloads/optical-module-research/points.csv) 末尾新增 `P275`（`EQ3`，光模块芯片共晶贴片设备）与 `P276`（`EQ4`，`50nm` 精度光耦合设备并获海外头部客户验证和认可），并在 [content_ledger.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/content_ledger/content_ledger.csv) 同步新增 `CLG0632` 与 `CLG0633`。全批次 `batch=step3_daily_2026q4` 共 `36` 条（`CLG0598–CLG0633`，全表 `597 -> 633` 行），经独立读取本地源文本去空白核对，**`36/36`（`100.0%`）逐字命中**。因科瑞技术 2025 年报全篇仅匿名披露“海外头部客户/海外光器件品牌企业”而未出现 Lumentum 或 Coherent 字样，`P275/P276` 明确注记匿名边界，严禁在获监管文件具名印证前写入供需边。

### 2. 海外承诺裁决、事件雷达增补与供应链关系时间线脉冲

幂等脚本 [ingest_overseas_and_timeline.py](file:///Users/jowang/Downloads/optical-module-research/out/step3-daily-and-v6-20261121/ingest_overseas_and_timeline.py) 对齐一手官网材料更新海外账本与时间线，同时保持 [solution_links.csv](file:///Users/jowang/Downloads/optical-module-research/calls/solution_links.csv) 字节级冻结：

在 [commitments.csv](file:///Users/jowang/Downloads/optical-module-research/calls/commitments.csv) 与 [claims.csv](file:///Users/jowang/Downloads/optical-module-research/calls/claims.csv) 中，`CM001`（Cisco 百万颗 Silicon One）补充精确锚点；`CM002`（AAOI 800G Q2 放量）修复 `S_AAOI_Q1_RESULT_A` 永久链接、新增 `CL075` 并裁决为 `fulfilled`（将 Q3 披露的 2027 扩产延期单列为后续独立事件）；`CM007`（Ciena Vesta 200 CPX 样品）按 `interquarter` 口径新增 `S_CIEN_2026_FORUM` 与 `CL076`，由 `not_observed` 更新为 `partially_fulfilled`（确认进入多客户送样评估，同时如实保留 Q2 首次可用日未知）。在 [events.csv](file:///Users/jowang/Downloads/optical-module-research/calls/events.csv) 中新增 `EV035`（Cisco OCP 2026 官宣 `102.4T Silicon One G300` 开放送样且首批系统向客户出货）与 `EV036`（Tower Semiconductor × 中际旭创联合推进 AI 近封装光学 NPO 标题级锚定，配 `WATCH_INNOLIGHT`）。在 [relationship_timeline.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/relationship_timeline.csv) 中追加 `TL9001–TL9005` 共 `5` 条高频事件脉冲（总行数 `446 -> 451`，含 `R057` 罗博特科→NVIDIA `2026-11-16` 与 `R205` Tower→中际旭创 `2026-11-03`），与 `74` 条边负记忆零碰撞。

### 3. `v6` 宇宙分母对称扩容与 Daily 95/5 持久待审池

幂等脚本 [build_v6_and_daily_queue.py](file:///Users/jowang/Downloads/optical-module-research/out/step3-daily-and-v6-20261121/build_v6_and_daily_queue.py) 与 [sync_daily_queue.py](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/sync_daily_queue.py) 完成了宇宙对称扩容与日常流量分流固化：

首先，`corpus/annual` 原顶层软链已安全展开为 `463` 个逐公司软链加上 `688808`（联讯仪器招股书与 2026 半年报）、`002428`（云南锗业 2024/2025 年报）、`002957`（科瑞技术 2025 年报）三个真实子目录，外部只读源 `/Users/jowang/Downloads/workflow-rehearsal/corpus/annual` 精确保持 `463` 项零改动。[corpus/_frozen.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/_frozen.csv) 与 [tree.yaml](file:///Users/jowang/Downloads/optical-module-research/tree.yaml) 同步扩容至 `466` 家；重算后的 [参与识别.csv](file:///Users/jowang/Downloads/optical-module-research/out/参与识别.csv) 中联讯仪器、云南锗业、科瑞技术三家全部进入 `已确认参与`，全库确认参与公司由 `90` 家增至 **`93` 家**，细化能力明细表 [capability_details.csv](file:///Users/jowang/Downloads/optical-module-research/capability_details.csv) 同步扩至 `93` 家公司 / `187` 条能力记录。未上市同行**微见智能**与**镭神技术**不入 `_frozen.csv`，同步纳管至 `tree.yaml` `observation_list`、[entity_nodes.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/salvaged/entity_nodes.csv)（`169 -> 173` 节点，其中 `N171` 科瑞技术对齐 `P275;P276`）及 [entity-registry.yaml](file:///Users/jowang/Downloads/optical-module-research/refs/entity-registry.yaml)（`refs/` 严格保持 `8` 个文件）。

其次，对海外 `staging/` 全部 `65` 期快照统计，9–11 月唯一披露 `504` 条中自动折叠常规公关/非光业务/律所广告/日历通知噪音 `479` 条（**`95.04%`**），命中四类状态跃迁触发器 `25` 条（**`4.96%`**），并将 `21` 条已滑出 14 天滚动窗的关键披露永久挽留入 [review_queue.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/review_queue.csv)。持久队列共 **`55` 行**（`DRQ0001–DRQ0055`）：`15` 行 `ingested_to_kb`（含 `DRQ0055` 科瑞技术能力点收编，所有 `;` 拆分引用在五张主表 100% 闭合）、`32` 行 `pending_primary_text`（承接 `Marvell×Lumentum`、`Lumentum FY27Q1`、`AXT Q3/通美融资`、`Tower×InnoLight 正文`、`东山精密外售光芯片` 等未获全文项）、`8` 行 `pending_filing_anchor`（含 `DRQ0047` 云南锗业 `2.7亿元` 媒体线索、`DRQ0048/0049` 微见智能与镭神技术、以及专门保留的 `DRQ0050` 盯防科瑞技术之 `Lumentum/Coherent` 具名客户归属 `U11`）。

### 4. 机器门加固、遗留测试修复与全仓裸 `pytest` 配置

在 [scan.py](file:///Users/jowang/Downloads/optical-module-research/scan.py) 中扩展 `_CORPUS_PATH_RE` 纳入 `daily_review`，新增纯函数 `_check_daily_review_queue` 接入 `invariants()`（不变量⑦）校验非空、零内嵌换行、`DRQ\d{4}` 唯一、四类 `T1–T4` 触发枚举、四状态枚举、`pending_*` 必填验证门槛及 `ingested_to_kb` 跨五表引用闭环，并将根目录白名单 `WL` 纳入 [pytest.ini](file:///Users/jowang/Downloads/optical-module-research/pytest.ini)。同步修复 [test_question_completion_semantics.py](file:///Users/jowang/Downloads/optical-module-research/tests/research/test_question_completion_semantics.py#L92) 旧工作包 ID 硬编码、收口 [test_step2_archive_salvage.py](file:///Users/jowang/Downloads/optical-module-research/tests/test_step2_archive_salvage.py#L200-L213) Step 2 批次断言、对齐 [test_event_intelligence.py](file:///Users/jowang/Downloads/optical-module-research/calls/tests/test_event_intelligence.py#L96-L132) 与 [test_positioning.py](file:///Users/jowang/Downloads/optical-module-research/calls/tests/test_positioning.py#L464-L473) Step 3 快照断言，并新增 [test_step3_daily_and_v6.py](file:///Users/jowang/Downloads/optical-module-research/tests/test_step3_daily_and_v6.py)。

---

## Step 1–Step 3 全周期总账演进对照表

| 账本 / 校验指标 | 初始基线（Step 0） | Step 1 收官后 | Step 2 收官后 | Step 3 收官后（当前） | 演进说明 |
| --- | ---: | ---: | ---: | ---: | --- |
| `corpus/_frozen.csv` 宇宙分母 | `463` | `463` | `463` | **`466`** | `v6` 对称补录 `688808`、`002428`、`002957` |
| `tree.yaml` `universe.count` | `461` | `463` | `463` | **`466`** | 消除历史漏同步并与 `_frozen.csv` 实时锁齐 |
| `out/参与识别.csv` 已确认参与公司 | `89` | `90` | `90` | **`93`** | 新增联讯仪器、云南锗业（归并鑫耀）、科瑞技术 |
| `points.csv` 能力点行数 | `271` | `269` | `269` | **`271`** | Step 1 合并 2 对重号；Step 3 更新 15 点并新增 `P275/P276` |
| `capability_details.csv` 细化能力行 | `181` | `183` | `183` | **`187`** | 覆盖 `93` 家已确认参与公司 / `38` 个叶格节点 |
| `edges.csv` 供应链边行数 | `236` | `236` | `236` | **`236`** | Step 1 清零 11 处截断/失衡括号；Step 2/3 严守匿名红线 |
| `shipments.csv` / `macro_evidence.csv` | `103 / 31` | `103 / 32` | `103 / 35` | **`103 / 35`** | Step 1 修正算术与等级；Step 2 合入海关 18 个月与 Yole 对账 |
| `content_ledger.csv` 客观工艺台账 | `0` | `0` | `597` | **`633`** | Step 2 收编 20 家 597 条；Step 3 新增 16 家 36 条（100% 逐字命中） |
| `relationship_timeline.csv` 时序行 | `0` | `0` | `446` | **`451`** | Step 2 拆解 `E001–E236` 全集；Step 3 新增 `TL9001–TL9005` |
| `edge_negative_cuts.csv` 负向剔除记忆 | `0` | `0` | `74` | **`74`** | 活跃边与新增时间线双向比对保持 `0` 泄漏 |
| `entity_nodes.csv` 实体主数据节点 | `0` | `0` | `169` | **`173`** | Step 3 更新 `N43` 联讯并新增 `N170–N173`（含 `N171=P275;P276`） |
| `daily_review/review_queue.csv` 待审池 | `0` | `0` | `0` | **`55`** | 固化 `15` 入库 + `32` 待全文 + `8` 待法定锚（挽留 21 条滑出项） |
| `calls` 信源 / 主张 / 雷达事件 | `166 / 70 / 34` | `166 / 70 / 34` | `166 / 70 / 34` | **`167 / 72 / 36`** | 兑现裁决 `CM002/CM007`，增补 `EV035` Cisco G300 与 `EV036` Tower×中际 |
| `scan.py --selftest` 内存回归用例 | `53` | `90` | `119` | **`139`** | 覆盖算术、海关、内容台账、时间线负记忆与持久待审池硬门 |
| 裸跑 `python3 -m pytest -q` | `exit 2`（9 收集错 + 1 失败） | 需手动传 `--ignore` 与 `-k` | 需手动传 `--ignore` 与 `-k` | **`exit 0`（`487 passed, 157 subtests`）** | 全仓零排除参数直接裸跑全绿 |

---

## 七道机器门与幂等核验实测结果

| 机器门 / 核验项 | 状态 | 实测输出摘要 |
| --- | --- | --- |
| `scan.py --selftest` | 通过（exit 0） | `[selftest] 合计 139 用例, 通过 139, 失败 0` |
| `scan.py --check` | 通过（exit 0） | `[语料] 最新文件距今0天; 宇宙内缺席年报 0 家 \| 不变量全绿(①-⑭)` |
| `render.py --verify` | 通过（exit 0） | `--verify: 两次临时重建一致(out/非canonical)` |
| `participation.py --check` | 通过（exit 0） | `参与识别: 全绿 \| 宇宙 466 \| 覆盖 466 \| 确认 93 \| 待确认 15` |
| `-m calls check` | 通过（exit 0） | `39 companies / 167 sources / 72 claims / 36 reviewed radar events OK` |
| `sync_daily_queue.py --check` | 通过（exit 0） | `queue=55 (ingested=15, pending_text=32, pending_anchor=8) \| staging_sep_nov=504 (95.04% / 4.96%)` |
| `python3 -m pytest -q`（全仓裸跑） | 通过（exit 0） | `487 passed, 157 subtests passed`（0 收集错误、0 跳过排除、0 失败） |
| 四份构建脚本二次幂等重跑 | 通过 | 23 个核心目标文件重跑前后 SHA-256 零漂移 |
| 保护基线与只读边界核验 | 通过 | `edges/triage/knowledge/macro/shipments/solution_links` 哈希未变；`archive/` 与历史 `out/step1-*`、`out/step2-*` 零修改；`workflow-rehearsal/corpus/annual` 精确 `463` 项；`refs/` 精确 `8` 文件；无 `git commit` |

结构化核验明细见 [verification-summary.json](file:///Users/jowang/Downloads/optical-module-research/out/step3-daily-and-v6-20261121/verification-summary.json)，最新细化版全景图见 [光模块产业链全景图_公司能力细化版.html](file:///Users/jowang/Downloads/optical-module-research/out/step3-daily-and-v6-20261121/光模块产业链全景图_公司能力细化版.html)，公司能力明细 PDF 见 [光模块产业链公司能力明细.pdf](file:///Users/jowang/Downloads/optical-module-research/output/pdf/光模块产业链公司能力明细.pdf)。

---

## 未解决 UNKNOWN 与留待用户决定的事项

1. **待审队列 `32` 条 `pending_primary_text` 一手全文拉取优先级**：`Marvell × Lumentum` 并购条款（`DRQ0015`）、`Lumentum FY27Q1` 在手订单承诺原文（`DRQ0016`）、`AXT 2026Q3` 出口许可证与通美融资公告全文（`DRQ0017/DRQ0018`）、`Tower × 中际旭创` NPO 新闻稿正文技术细节（`DRQ0019`）及东山精密外售光芯片具体品类（`DRQ0020`）均已永久固化在 [review_queue.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/daily_review/review_queue.csv) 中。请指示下一阶段优先补拉并人工复核哪些一手原件。
2. **待审队列 `8` 条 `pending_filing_anchor` 法定披露追踪**：云南锗业 `2.7亿元` 磷化铟投资额调增媒体线索（`DRQ0047`，缺巨潮董事会公告 PDF）、科瑞技术对 `Lumentum / Coherent` 的具名客户归属（`DRQ0050`，2025 年报仅匿名披露“海外头部客户/海外光器件品牌企业”，仍属 `UNKNOWN`）、以及微见智能（`DRQ0048`）与镭神技术（`DRQ0049`）的一手产品规格或上市客户披露锚，均需取得法定文件后方可入点或建边。
3. **证据台账向根级知识库的专题提炼授权**：目前 `content_ledger.csv`（`633` 条）与 `relationship_timeline.csv`（`451` 条）已具备完整的 2023–2026Q4 工艺与供需脉冲脉络；如需就 NPO/CPO 量产分化、200G EML 扩产工艺瓶颈或高精度封测设备国产替代提炼新增 `KN###` / `WHY###` 条目写入 [knowledge.yaml](file:///Users/jowang/Downloads/optical-module-research/knowledge.yaml)，请指定复核与晋升范围。
4. **Git 提交决策**：按工作包非目标约束，Step 1–Step 3 全部改动均保留在工作区未执行 `git commit`；请确认审阅无误后是否授权按仓库提交规范归档提交。
