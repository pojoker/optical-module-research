# 数据语义修复集成的独立实现复核（Cursor Fable 5.1）

> 复核者：Cursor Fable 5.1（独立结构 / 规格 / 回归复核）
> 工作包：`REMEDIATE-DQ-001`
> 固定点：`7ff3b25cfd0ff3b13fa834a0d775ae2879195`（工作包 baseline）
> 复核对象：集成 HEAD `c53b9bdf6d8a5146e145722744129dbd1f44d7df`（范围 `7ff3b25..c53b9bd`，7 个提交）
> 对照报告：`docs/reviews/2026-09-04-post-remediation-codex-review.md`、`docs/reviews/2026-09-04-product-direction-after-remediation.md`
> 未读取：`archive/**`、closure / 状态机材料、其他分支与 worktree 轨迹、Kimi 复核报告
> 本文件只做复核记录；未改任何代码、生成物或 canonical。

## 0. 复述与范围说明

- 北极星：单一、可审计的光模块领域研究系统；事实 / 派生 / 候选 / UNKNOWN 分列；人工复核结论才进 canonical。
- 本次交付物：本报告；核验 `7ff3b25..c53b9bd` 与 Codex 两份报告是否一致，重点是实现正确性、生成输出、canonical 与 schema 未变、无状态机、测试是否脆弱、验收是否真实满足。
- 非目标：不改代码 / 生成物 / canonical；不推远端；不把机器门通过说成领域结论完成。
- 允许写入路径：仅本文件（`docs/reviews/2026-09-04-cursor-fable-5-1-product-direction-review.md`，与工作包 `allowed_write_paths` 一致）。控制器最初下发的路径名有误（`...cursor-fable51-implementation-review.md`），用户已更正，本文件按工作包精确路径落盘。

## 1. 总判定

**代码与 reader 语义：可接受为本地候选，但有两项 P1 需用户裁决后才应视为"验收满足"。**
**canonical / schema / 状态机：范围内提交未触碰 canonical，未新增 schema、关系类型、状态机、第十页。** 但生成器存在一项"下次默认构建即改写受保护账本内容"的潜伏漂移（P1-2）。
**Codex 报告一致性：主体结论与 diff 一致；四处表述与实际不符（见第 4 节）。**
**远端动作：无。**

## 2. Findings（按严重度）

### P1-1 WP-C 的读者可见交付物没有进入受版本控制的读者页面

- 证据：
  - `git log -- out/全景.md` 最后提交为 `ae173d0`；`7ff3b25..c53b9bd` 未改 `out/全景.md` / `out/全景.html` / `out/研究问题树.md`。
  - 用 HEAD `render.py` 在临时目录重建，与已提交 `out/全景.md` 相差 **380 行**：新增 `## 出货观察（shipments.csv 只读转写，非比较面）` 一节（104 行数据）、82 处 `非URL锚（说明文本，非超链接）`、BOM 流向从"已证N边"改为"关系观察N条，非默认光模块供货"。
  - 用 baseline `render.py` 重建与已提交 `out/全景.md` 相差 0 行，说明基线时是同步的，本轮改了源码却没重建。
  - 同类：`output/pdf/光模块产业链公司能力明细.pdf`（`build_detailed_capability_report.py` 的默认 PDF 输出，git 跟踪）最后提交也是 `ae173d0`，不含 WP-A 的"准入依据"措辞。
- 根因：工作包 `allowed_write_paths` 只放开 `calls/out/**` 与 `out/光模块知识体系/**`，没有放开 `out/全景.*`、`out/研究问题树.md`、`output/pdf/**`。Codex 的 P1 修复因此只重建了 calls/out（47 文件，已核一致）与 `06-research.html`（已核一致）。
- 影响：工作包读者交付物第 3 条"出货量、锚点和关系边的页面展示明确不可比范围与证据边界"在**已提交的产品① 页面上尚未成立**，只在源码与测试夹具中成立。`render.py --verify` 只比较两次临时重建，不比较已提交 `out/`，所以机器门不会报出此差距。
- 建议：用户裁决二选一：(a) 扩展允许路径并授权重建 `out/全景.*`、`out/研究问题树.md`、`output/pdf/**`（纯派生物，无 canonical 风险）；(b) 明确接受产品① 页面滞后到下一次授权 render，并把验收第 2 条标为"部分满足"。不建议由执行者自行重建。

### P1-2 HEAD 生成器默认运行会改写受保护的 `capability_details.csv` 内容（31/181 行）

- 证据：`build_detailed_capability_report.py:1417-1445` 的 `main()` 默认调用 `write_capability_csv(DEFAULT_CSV, rows)`，`DEFAULT_CSV = ROOT/"capability_details.csv"`，该文件在工作包 `canonical_policy.protected` 中。
  - 用 HEAD `granular_rows()` 与已提交 CSV 逐行比对：列名一致（Codex P0 修复有效）；但 31 行内容变化，按列：`具体产品` 27、`证据等级` 5、`证据日期` 2、`来源锚点` 1、`材料与技术` 2、`工艺能力` 2、`当前阶段` 2、`原始披露摘要` 2；另有 +2 行（基线以来 points.csv 新增导致，非本轮引入）。
  - `具体产品` 的变化是 `coarse_cell_note()` 把整句展示文案（"粗粒度格：本行只表示公司能力与该格发生交集，不推出具体产品供货，也不构成完整路线能力（C5 多类电芯片子能力同格；子能力须逐条披露支撑）"）用 `｜` 拼进数据列（`build_detailed_capability_report.py:411-414`）。
  - `证据等级` 的 5 处变化是 `admission_rank` 修正选点后的正确结果（如 天孚通信/D12 从 `context_only` 变为 `判定闸-生产中(...)`）。
- 判断：Codex 对 P0 的修复只保住了 **schema**，没有保住**内容**；把 reader 边界文案写进数据列，与其自己对"准入依据"采取的"只在展示层抽取"的做法不一致。选点修正带来的 `证据等级` 变化是正确的，但同样会落到受保护文件里。
- 建议：(a) 把粗粒度边界文案从 `具体产品` 数据列移到 `capability_section()` / `build_pdf()` 展示层（与"准入依据"同一模式）；(b) 用户显式决定是否授权重建 `capability_details.csv`（含选点修正与 +2 行追平）；(c) 在此之前，任何人运行默认构建都应加 `--html-only`。这属于修复方向调整，不在本复核写入范围。

### P2-1 一条关键读者测试是空断言

- 证据：`tests/test_capability_report_semantics.py:263-266` `test_capability_card_shows_admission_path_not_process_note` 的夹具 `证据等级 = "判定闸-生产中(过程备注不应展示)"`，断言却是 `assertNotIn("锚待复核", html)`——夹具中根本没有"锚待复核"。
  - 复现：把 `report.admission_path` 打桩为恒等函数（不做任何剥离）后单独运行该测试，**仍然通过**。
- 影响：能力卡"不展示过程备注"的读者行为实际上没有被测试锁住；`AdmissionSemanticsTest` 只覆盖了纯函数，未覆盖 HTML 输出。
- 建议：断言 `assertNotIn("过程备注不应展示", html)`，并对 `build_pdf` 输出做同样检查。

### P2-2 海外 reader 测试仍锁死按公司的当日槽位数字

- 证据：`calls/tests/test_reader_semantics.py:131-136` 硬编码 `LITE 季度槽登记 4/4`、`LITE 可用来源 2/4`、`AAOI 可用来源 2/4`、`AXTI 可用来源 3/4`。
- 影响：任何合法日更（如 AAOI 补齐一份季度 transcript）都会造成无关失败，正是 Codex 标准轴 P2 想消除的那类脆弱性；Codex 报告"覆盖、来源和事件测试全部从当前账本动态复算，不再锁死当日数字"与此不符。其余 `_expected_levels` / `_source_inventory` / `_event_summary` 确实已改为动态复算。
- 建议：从 `sources.csv` 为这三家复算 `available` 槽位数后再断言。

### P2-3 站点测试在默认收集方式下无法运行

- 证据：`python3 -m pytest tests/` 与 `python3 -m pytest tests/site/test_optical_module_reader.py` 均报 `ModuleNotFoundError: No module named 'site.test_optical_module_reader'; 'site' is not a package`；`python3 -m unittest tests.site.test_optical_module_reader` 报 `No module named 'tests.site'`（本机 `site-packages/tests` 遮蔽了仓库 `tests`）。只有 `python3 -m pytest --import-mode=importlib ...` 可跑通，45/45 通过（20 + 7 + 18，与 Codex 计数一致）。
- 性质：`tests/site/__init__.py` 自 `ae173d0` 就存在，是**既有基础设施脆弱性**，非本轮引入；但 WP-D 新增的 6 条测试继承了它，且仓库无任何文档说明运行方式。Codex 报告"九页 reader 测试 18/18 通过"可复现，但未说明所用命令。
- 建议：在 README 记录运行命令，或加 `pytest.ini` 指定 `--import-mode=importlib`（不在本轮范围）。

### P3-1 WP-D 删除了 5 个仍然有效的读者链接

- 证据：`site/optical-module/sections/audit.html` 旧版含 PQ002 / PQ003 候选批次、PQ003 Kimi 审核、Cursor 建议独立审计、动态网页语义快照 5 个链接，新版全部移除；对应目标文件在 HEAD 仍存在。外包方案 WP-D 只要求"放进证据层级与不可外推边界"，未要求删链接。
- 影响：读者失去到候选批次的导航；不影响正确性。建议用户决定是否恢复。

### P3-2 `render.py` 出货节嵌入静态单位枚举

- 证据：`render.py:71`：`（万只/万件/台/台套/万个/万片/千只/千克/万平方米/KK/万颗/万美元等）` 为写死文案；行数与单位数则是动态的。
- 影响：与 Codex 在站点章节里消除的"会随日更失效的静态数量"同类，只是有"等"字兜底。低风险，建议改为从 `units` 动态拼接。

### P3-3 `git diff --check` 未通过

- 证据：`git diff --check 7ff3b25..c53b9bd` 报 6 处 trailing whitespace，全部在 `c53b9bd` 新增的两份 Codex 报告（Markdown 双空格换行）。Codex 表格写"`git diff --check` 通过"——对其审核时的范围可能成立，对最终 HEAD 不成立。无功能影响。

### P3-4 `calls/out` 大体量 diff 属基线追平，不是 WP-B 语义

- 证据：`event-intelligence.json` +6693 行；基线跟踪的 JSON 有 21 条 radar_events、14 张公司卡，HEAD 为 34 条、39 张，且新增 `company_candidates` / `company_tier_reviews` / `entity_relationships` 三个顶层键——这三个键的生成代码在基线 `calls/event_intelligence.py` 已存在，本轮 `event_intelligence.py` / `schema.py` / `positioning.py` 未改。
- 判断：基线时 `calls/out` 已严重过期，本轮重建是在 `calls/out/**` 授权路径内的合法追平；已在临时目录用 HEAD renderer 重建并与提交内容逐文件比对，47 个文件完全一致。建议在报告中把这部分标注为"追平"，避免复核者把 6.7k 行差异误读为 WP-B 改动。

### P3-5 范围外既有过期（parking lot 候选）

- `out/研究问题树.md` 与 baseline render 相差 44 行、`out/知识库.md` 相差 116 行——基线时就已过期，与本轮无关。

### P3-6 `ADMISSION_RANK` 未覆盖 `判定闸-在建` / `判定闸-宇宙外观察`

- 证据：points.csv 中这两类共 23 行；`granular_rows()` 先按 `状态=="生产中"` 过滤，248 行生产中点全部映射成功（0 未映射），因此当前无影响。若日后放宽状态过滤，这些点会落到 rank 1（低于 `context_only`）。仅记录。

## 3. 标准与规格结论

| 检查项 | 结论 | 证据 |
|---|---|---|
| canonical 未变 | ✅ | `git diff 7ff3b25..c53b9bd -- knowledge.yaml points.csv edges.csv triage.csv route_bom.csv tree.yaml shipments.csv macro_evidence.csv company_segment_revenue.csv capability_details.csv calls/*.csv` 为空 |
| schema 未变 | ✅（提交层）/ ⚠（潜伏） | `FIELDNAMES` 保留 `证据等级`；`calls/schema.py` 未改；`event-intelligence.json` 新顶层键来自基线既有代码。潜伏漂移见 P1-2 |
| 无新增状态机 / receipt / manifest / lineage / 引擎 / 关系类型 | ✅ | 代码 diff 新增行中仅站点测试的 `assertNotIn` 提到这些词；`build-manifest.yaml` 为基线既有 |
| 写入范围与 worker_write_scopes 一致、互不重叠 | ✅ | `5a9b12d` / `f500e4d` / `b0c6876` / `7f40544` 各自路径集合两两不交且在对应 scope 内；`bcdb0ec` / `c53b9bd` 在 `allowed_write_paths` 内 |
| 生成物与源码同步 | ⚠ | `calls/out/**`（47 文件）与 `out/光模块知识体系/**` 重建后逐文件一致；`out/全景.*`、`out/研究问题树.md`、`output/pdf/**` 未重建（P1-1） |
| WP-A 实现正确性 | ✅（逻辑）/ ⚠（落点） | `admission_path` 首括号截断处理嵌套备注正确；选点修正后 5 行 `证据等级` 变化合理；边界文案落进数据列是落点问题（P1-2） |
| WP-B 实现正确性 | ✅ | `_compute_coverage` 分母、五级、asserted/corroborated 与测试独立复算一致；`reviewed_event` 只计 anchor_reviewed 事件；同源双证被 `load_event_facts` 拒绝 |
| WP-C 实现正确性 | ✅（源码） | `_fmt_anchor` 仅 fullmatch 直链才生成链接；`同上` / Markdown 链接 / `URL；说明` 均落为转义说明文本；出货节无小计/合计/排名，聚合与非 base 行有标记 |
| WP-D 实现正确性 | ✅ | 27 章节 / 9 页合同保持；`06-research.html` 含四层读法与四条不可外推边界；`../../docs/...` 链接目标全部存在 |
| 越级推导 | ✅ 未发现 | 所有新增文案均为收窄性边界声明，未把候选写成事实 |

## 4. 与 Codex 报告的一致性

一致：canonical diff 为空；P0（列名）已修；calls/out 与 06-research.html 已重建且确定性成立；`同上`/非 URL 锚/出货口径/五级覆盖/asserted-corroborated 的读者行为改善确实存在于源码与（部分）生成物中；"仍未解决"清单与代码现状一致。

不一致（均已在第 2 节给出证据）：

1. "源码语义变化没有同步到受版本控制生成物"只修了一半——`render.py` 与 PDF 生成物未重建（P1-1）。
2. "保留既有列结构"成立，但"下次默认构建改写受保护文件"这一风险并未消除，只是从 schema 变成了内容（P1-2）。
3. "测试全部从当前账本动态复算，不再锁死当日数字"——按公司的槽位数字仍硬编码（P2-2）。
4. "`git diff --check` 通过"——对 HEAD 不成立（P3-3）。

产品方向报告：对"能回答 / 不能回答 / 暂不做 / 待用户决定"的分列清晰；对验收标准要求的"已修复 / 仍属数据问题 / 需架构裁决 / UNKNOWN"四分，前三类在文中可辨，**没有独立的 UNKNOWN 小节**（UNKNOWN 只出现在 Codex 审核报告"仍未解决"中的 archive 一条）。建议补一节显式 UNKNOWN。

## 5. 测试结果（本 worktree，只读）

| 命令 | 结果 | 备注 |
|---|---|---|
| `python3 -m pytest --import-mode=importlib tests/test_capability_report_semantics.py tests/test_render_data_quality_boundaries.py tests/site/test_optical_module_reader.py` | 45 passed | 20 + 7 + 18，与 Codex 计数一致 |
| `python3 -m pytest tests/`（默认模式） | 收集失败 | `tests/site` 与 stdlib `site` 冲突（P2-3） |
| `python3 -m unittest discover -s calls/tests` | Ran 169, OK | 与 Codex 一致 |
| `python3 render.py --verify` | 通过 | 只证两次临时重建一致，不比较已提交 `out/` |
| `python3 -m calls check` | 通过 | 39 公司 / 166 来源 / 70 claims / 34 reviewed events；无 canonical 写入 |
| `python3 scan.py --check` | **失败** | `[饥饿] corpus/annual 无语料`，⑧ 6 条证据文件不存在——本 worktree 缺 `corpus/`，环境性 |
| `python3 participation.py --check` | **失败** | `out/参与识别.*` 与重生成不一致——`participation.py:106` 依赖 `corpus/annual/<代码>` 目录，环境性 |
| `git diff --check 7ff3b25..c53b9bd` | 6 处 trailing whitespace | 均在 Codex 两份 md（P3-3） |
| 临时目录重建 `calls/out` 与提交比对 | 47/47 一致 | 确定性成立 |
| 临时目录重建 `out/光模块知识体系` 与提交比对 | 一致 | 确定性成立 |
| 临时目录重建 `out/全景.md` 与提交比对 | 380 行差异 | P1-1 |
| HEAD `granular_rows()` 与提交 `capability_details.csv` 比对 | 31/181 行内容变化，+2 行 | P1-2 |
| 打桩 `admission_path=identity` 后运行 `test_capability_card_shows_admission_path_not_process_note` | 仍通过 | P2-1 |

## 6. 未决 UNKNOWN

1. **scan / participation 机器门在完整仓库是否通过**：本 worktree 无 `corpus/`，两门均因环境失败；只能采信 Codex 在完整仓库的通过记录，本复核无法独立复现。
2. **四个外包分支是否"从同一基线建立"**：涉及其他 worktree / 分支历史，属禁读范围；只核验了拣入提交的路径互不重叠。
3. **`capability_details.csv` 的身份**：工作包把它列为受保护 canonical，代码把它当默认输出的派生物；这个矛盾决定 P1-2 的严重度是"潜伏漂移"还是"设计即如此"，需用户裁决。
4. **`archive/**` 依赖与消融结论**：沿用 Codex 的 UNKNOWN，本复核未读。

## 7. 接受 / 拒绝建议

- **接受**（作为本地候选，不推远端）：`5a9b12d`、`f500e4d`、`b0c6876`、`7f40544`、`bcdb0ec`、`c53b9bd` 的代码与 reader 语义改动；canonical、schema、状态机边界均守住。
- **不接受为"验收满足"**，直到用户裁决：
  - P1-1：是否扩展允许路径并授权重建 `out/全景.*` / `out/研究问题树.md` / `output/pdf/**`；否则验收第 2 条只能记"部分满足"。
  - P1-2：是否要求把粗粒度边界文案移到展示层，以及是否授权重建 `capability_details.csv`。
- **建议后续小修**（另立授权，非本轮）：P2-1 空断言、P2-2 硬编码槽位、P2-3 测试运行方式文档化、P3-1 恢复链接、P3-2 动态单位列表。
- **不需要动作**：P3-3 ~ P3-6 记录即可；P3-5 建议进 `docs/control/PARKING_LOT.md`（本复核无该路径写权限，未写）。

## 8. 收尾声明

- 改动文件：仅本文件。
- 领域 / canonical 影响：无。
- 机器门通过（render --verify、calls check、45 + 169 测试）只证明结构与确定性，不证明任何领域结论完成；本报告不宣称任何审计中列出的数据问题已解决。
