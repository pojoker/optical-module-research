# 交付报告 — A 包（CodeBuddy / hy4-preview）：国内增量与中断

范围：`domestic_daily/core.py`、`domestic_daily/cli.py`、`corpus/_fetch_qa.py`、`tests/test_domestic_daily.py`。
未触碰 canonical、B/C 包文件、其他 worktree。本报告为执行者自述，领域结论仍需人工复核。
（第二稿：按主代理审阅的 5 点正确性驳回修正，见第 1.6—1.9 节。第三稿：按主代理预检补三处漏网——m=0 截断漏判、manifest 非 dict 崩、PDF 提取失败落空 txt 永久跳过，并补 SSE/P5W 服务端无 since 过滤的诚实声明，见第 1.10 节与 §5.6。）

## 1. 修复了什么

### 1.1 互动易不再每轮无条件全量重抓（`core.py`）

- 现状：93 家每家固定 `since=2023-01-01`，每日串行重抓三年。
- 现在：`state/qa_watermarks.json` 记录每家**成功水位**（上次抓取成功的运行日）。
  起始日期 = `水位 - QA_OVERLAP_DAYS(7)`；无水位（首次/中断后重试）或水位非法 → 退回
  `BACKFILL_START=2023-01-01` 全量回填。
- **只有抓取成功才推进水位**；失败、分页截断、通道不可用均不推进，漏抓区间不会被固化成"已抓完"。
- 显式回填：`--backfill-since YYYY-MM-DD` 忽略水位，仅用于补历史。
- 与 `docs/plans/2026-09-domestic-daily-mirror-contract.md` 第 3 条（"每次从 2023-01-01 请求全量快照"）
  有意偏离：该契约禁止的是**固定 14 天窗口**，本次改为水位 + 重叠窗口，由本工作包 A 包修复要求 1 授权。
  合并语义未变：仍以源仓库 `qa.jsonl` 与镜像历史快照的**并集**为基线，按 `index_id` 只增不减。

### 1.2 抓取失败不再冒充"零增量"

- `_fetch_qa.py` 新增 `FetchFailure`：主通道不可用（secid/uid/pid 未找到、交易所归属未知）
  且 p5w 兜底也无产出时**抛错**，不再返回 `None`/`0`。返回 `0` 仍表示"查过，确实没有"。
- 北交所（92/8 开头）原生通道 p5w 无产出同样抛 `FetchFailure`。
- `_p5w_down` 增加 `reason`，失败原因随熔断一起上报。

### 1.3 分页有界，且**截断即失败**（`_fetch_qa.py`）

- `MAX_PAGES=40`：互动易、上证 e 互动、p5w 三处翻页统一封顶。
- 互动易原判据 `if page>=totalPage or not res` 在服务端不返回 `totalPage` 时第一页就停；
  改为 `not res` 才停，并新增**重复页签名**判据（服务端不翻页时立刻停止）。
- **截断不是成功**：模块级 `_trunc` 记录达上限或重复页，`fetch()` 在 `_p5w_guarded` 返回后、
  判断 `m` 之前**抛 `FetchFailure`**，调用方据此不计增量、**不推进水位**。
- **截断的新数据不持久化**：`RequestsClient.fetch_qa` 在隔离临时 ROOT 上跑抓取，
  `FetchFailure` 抛出后该临时目录被清理，p5w 翻页过程中经由 `_merge_write` 写下的"部分合并"
  一并丢弃。实际**保留的是既有快照**（真实源 `corpus/qa/<code>/qa.jsonl` 本轮未改动），
  下一轮重抓补齐。因此截断的后果是"本轮该家标记 partial、水位不前进、下次重抓"，
  不是"丢历史"也不是"截断页已入库"。
- 限速（1.25s 全站间隔、翻页 sleep）全部保留。

### 1.3.1 SSE / P5W 服务端**无 `since` 过滤**（诚实声明，不可笼统写"全部高效增量"）

- 互动易（irm.cninfo.com.cn）的请求带 `startDate=<since>`，服务端按日期过滤，增量窗口有效。
- **上证 e 互动（SSE）与北交所全景网（P5W）的抓取请求本身不带 `since` 参数**：它们每次都从
  列表头开始翻页，直到返回空页或达到 `MAX_PAGES` 上限；"增量"只发生在本地按 `answer_date`
  过滤（`if ad and ad<since: continue`）之后。
- 因此本包修复**没有**让 SSE/P5W 变成服务端增量：它们的网络负载仍是"翻历史直至空/上限"，
  只是失败的判定（无产出 / 截断）变得诚实、且不再误报成功。**保守失败可接受**——
  分页策略（是否/如何在服务端侧截断、上限是否需下调）留待下一轮生产观察后再调，
  本轮不扩大架构。这与 §1.1 的"93 家不再每家每天重抓三年"并不矛盾：后者靠的是
  互动易的 `since` 与水位模型；SSE/P5W 仍走全量翻页，只是失败语义正确。

### 1.4 运行可观察、中断可判定（`core.py`）

- `state/run-status.json`（轮次开始即写，阶段切换与每家处理完都更新）：
  `run_date`、`status`(running/complete/partial/failed)、`updated_at`、`processed`/`total`、
  `stage`、`error_count`、`errors`、`prior_run_interrupted`。
- `state/run.log`：**错误随发生即落盘**，不再等整轮结束才可见。
- 遗留 `running` 只证明"上次没正常结束"；下一轮写入 `prior_run_interrupted` 并在日报日志区
  说明"不据此推断终止原因"。不猜测是谁/什么终止了进程。
- 只清理本轮自己创建的 staging 目录，不删旧临时目录。

### 1.5 局部失败不谎报成功

- `run_status`：complete / partial（有失败项，日报仍产出）/ failed（异常中断，日报未产出）。
  manifest 新增 `run_status`、`errors`、`qa_failed_codes`、`qa_backfill_codes`、`prior_run_interrupted`。
- 日报新增 `## 运行状态 <status>` 栏；非 complete 时列出失败项并写明"不能据此判断今日无新增"，
  判定闸建议改为"本次运行不完整，不能判断无新增"（complete 时措辞不变）。
- CLI 退出码：complete=0、partial=1、failed=2，并打印失败清单。

### 1.6 降级统一登记（审阅点 2）

原先只 `logs.append` 因而仍判 complete 的三处，全部改走 `_emit`（记 logs + 错误摘要 + 立即落盘），
因此都会让本轮变成 partial：

| 场景 | 位置 | 现在 |
|---|---|---|
| 非 PDF 响应 | 投关表下载后 | `[投关表] <code> 非PDF响应,未入库` |
| PDF 文本提取失败 / `pdftotext` 不可用 | `subprocess.run` 包 `try/OSError` | `[投关表] <code> PDF文本提取失败,正文不参与扫描` |
| 月度重筛 401（需 token） | 重筛循环 | `[重筛] p_stock2110 需token(401), 本月重筛未完成(降级,不计为成功)` |

### 1.7 同日复用只在持久化状态一致时发生（审阅点 3）

- `unchanged_replay` 增加前置条件 `prior_complete`：**持久化的 manifest 本身必须是 `run_status == "complete"`**；
  旧的 partial 产物、升级前没有 `run_status` 字段的遗留 manifest 一律**不复用、重写**，
  避免磁盘产物与本次运行状态不一致。
- 保留的复用路径仍写 `run-status.json` 与 `qa_watermarks.json`，日报字节不变（幂等性不破坏）。

### 1.8 状态文件与水位的可信边界（审阅点 4）

- `_read_json` 拒绝非 dict 载荷（list/str/数字）→ 返回 `None`，不允许拿去 `.get()`。
- **未来水位不跳过回填区间**：`_qa_since` 取 `min(水位, run_date) - 7 天`，
  水位因时钟偏移或回填日倒退跑到未来时，退回以 run_date 为终点的正常重叠窗口，
  绝不返回零宽或未来窗口；结果早于 `BACKFILL_START` 时仍退回全量回填。

### 1.9 运行级熔断与缩水兜底（审阅点 5）

- `RequestsClient` 原来每家公司都 `importlib` 重新加载 `_fetch_qa`，并逐家把 `_p5w_down["v"]` 置 False，
  运行级熔断形同虚设（2026-08-21 p5w 不可达 → 60min 超时的成因之一），且 `_LAST_REQUEST` 被重置使限速失效。
  现改为**按客户端（即按运行）缓存模块**，不再重置熔断；隔离 seed（临时 ROOT）仍逐家独立。
- **缩水兜底只在全量快照请求时比较**：新增 `FULL_SNAPSHOT_SINCE`，仅当 `since <= 2023-01-01`
  才做 `n < 0.5*snap` 判定。增量窗口天然远小于历史快照，不再每家每天都触发 p5w 兜底。
- **兜底失败显式化**：缩水成立且 p5w 已熔断 → 抛 `FetchFailure`（"增量不完整"）；
  p5w 可达但无更多数据 → 仅打印，不判失败。

### 1.10 第三稿预检补三处漏网（m=0 截断、manifest 非 dict、PDF 永久跳过）

- **m=0 仍须判截断（预检漏网）**：原先 `_trunc` 检查写在 `if m:` 之内。
  当 p5w 翻到历史但 `since` 过滤后 `m=0`、而翻页已重复/达上限（`_trunc['v']=True`）时，
  `if m:` 为假 → 截断被漏过，整轮被当成"无新增/成功"。
  现改为**每次 `_p5w_guarded` 返回后立即检查 `_trunc`，再判断 `m`**：主通道 0 条路径与
  缩水兜底路径都覆盖。新增反例 `test_p5w_fallback_truncation_with_zero_filtered_still_fails`、
  `test_shrink_fallback_truncation_with_zero_filtered_still_fails`（外加 m>0 的
  `test_p5w_repeat_page_raises_fetch_failure` / `test_p5w_fallback_truncation_raises_fetch_failure` /
  `test_shrink_fallback_truncation_raises_fetch_failure` 共 5 个反例）。
- **manifest 非 dict 不再崩（漏网#2）**：`prior_manifest` 已统一走 `_read_json`，后者拒绝非 dict
  （list/str/数字）→ `None`，故遗留一个 list 形状的 `manifest.json` 时 `prior_complete` 回落
  `False`、本轮重写一致的 dict 产物，不触发 `.get` 崩溃。反例
  `test_manifest_non_dict_list_is_rewritten_not_crashed`。
- **PDF 提取失败落空 txt 不再永久跳过（漏网#3）**：原跳过条件只看 `existing_path.exists()`，
  一次提取失败留下空 `*.txt` 后，次日 `existing_path` 命中即永远跳过、反而判 complete。
  现跳过条件收紧为 `PDF 与正文都已落盘且正文非空`；`_extract_pdf` 在 `pdftotext` 退出码非 0、
  未安装（OSError）、或退出码 0 但**正文空白/缺失**（用 `strip()` 判定，避免换行符误判有正文）
  时均登记为降级（partial），并规范写出空串使调用方 `new_ir` 读取不 `FileNotFoundError`、重试可判。
  反例：`test_pdf_text_extraction_failure_is_registered_as_degradation`（rc=1）、
  `test_pdf_empty_text_layer_is_registered_as_degradation`（rc=0 但无文本层）、
  `test_pdf_extraction_failure_rerun_recovers_not_permanently_skipped`
  （Day1 提取失败留空 txt → Day2 重跑重新提取并真实写出非空正文、被扫描召回，不被跳过）。
- 顺带修正 `unchanged_replay` 分支一处 `manifest_path` 未定义（删 `_read_json` 旧变量遗留的引用）
  导致的 `NameError`，定位为 `state/manifest.json`。

## 2. 行为变化清单（给主代理合并时核对）

| 位置 | 变化 |
|---|---|
| `DailyMirror.run()` | 新增可选参数 `backfill_since`；返回值不变，manifest 新增 5 个字段 |
| `state_root` | 新增 `run-status.json`、`run.log`、`qa_watermarks.json` |
| 日报文本 | 新增 `## 运行状态` 栏；非 complete 时判定闸建议措辞改变 |
| `_fetch_qa.fetch()` | 通道全部无产出、分页截断、缩水且兜底不可用 → 抛 `FetchFailure` |
| 互动易翻页 | `totalPage` 缺失时继续翻页（原第一页即停），封顶 40 页 |
| p5w 熔断 | 跨公司保留（原逐家重置）；限速状态同样跨公司保留 |
| CLI 退出码 | partial=1、failed=2（原恒为 0） |
| 降级判定 | 非 PDF、文本提取失败、重筛 401 由"记日志但仍 complete"变为 partial |

旧字段全部保留（`logs`、`digest`、`outliers`、`rescreen`、`queue_sha256` 等），
Pi 按合同对缺失字段保持 UNKNOWN 即可。

## 3. 测试

```bash
cd /Users/jowang/Downloads/optical-daily-domestic
/Users/jowang/miniconda3/bin/python3 -m pytest tests/test_domestic_daily.py -q
```

| 测试 | 覆盖的失败模式 |
|---|---|
| `test_qa_since_backfills_once_then_uses_overlap_window` | 首次回填 2023-01-01，次日走水位-7 天 |
| `test_qa_failure_keeps_watermark_and_marks_partial` | 抓取失败不推进水位、partial、失败窗口下次重抓 |
| `test_explicit_backfill_since_overrides_watermark` | 显式回填覆盖水位 |
| `test_complete_run_reports_complete_status` | 完整运行的 status 与日报措辞 |
| `test_partial_run_report_avoids_no_news_claim` | partial 日报不写"无增量"、错误进 run.log |
| `test_interrupted_prior_run_is_reported_without_blaming_a_process` | 遗留 running 可观察且不降级本轮 |
| `test_fatal_failure_marks_failed_and_keeps_prior_snapshot` | failed、日志先行落盘、不破坏上次快照 |
| `test_non_pdf_ir_response_is_registered_as_degradation` | 非 PDF 未入库 → partial（审阅点 2） |
| `test_pdf_text_extraction_failure_is_registered_as_degradation` | pdftotext 失败 → partial（审阅点 2） |
| `test_rescreen_401_is_registered_as_degradation` | 重筛 401 → partial（审阅点 2） |
| `test_stale_partial_manifest_is_rewritten_not_reused` | 同日重跑不复用旧 partial 产物（审阅点 3） |
| `test_legacy_manifest_without_run_status_is_rewritten` | 遗留无状态 manifest 被重写（审阅点 3） |
| `test_future_watermark_does_not_skip_backfill_interval` | 未来水位不产生零宽窗口（审阅点 4） |
| `test_corrupt_or_non_dict_state_files_are_not_trusted` | 非 dict / 非法日期 → 全量回填（审阅点 4） |
| `test_requests_client_keeps_run_level_p5w_breaker` | 熔断跨公司保留、模块按运行缓存（审阅点 5） |
| `test_all_channels_unavailable_raises_fetch_failure` | 通道全挂必须报错而非零条 |
| `test_page_cap_raises_fetch_failure` | 翻页达上限 → 报错、不推进水位（审阅点 1） |
| `test_repeated_page_raises_fetch_failure` | 重复页截断 → 报错、不推进水位（审阅点 1） |
| `test_incremental_window_does_not_trigger_snapshot_shrink_fallback` | 增量小结果不触发缩水兜底（审阅点 5） |
| `test_p5w_repeat_page_raises_fetch_failure` | 北交所原生通道翻页重复 → 截断失败（第三稿漏网#1） |
| `test_p5w_fallback_truncation_raises_fetch_failure` | 主通道 0 条 + p5w 兜底重复页(m>0) → 失败（第三稿漏网#1） |
| `test_shrink_fallback_truncation_raises_fetch_failure` | 全量快照缩水 + p5w 兜底重复页(m>0) → 失败（第三稿漏网#1） |
| `test_p5w_fallback_truncation_with_zero_filtered_still_fails` | 主通道 0 条 + p5w 兜底重复页且 since 过滤后 m=0 → 失败（第三稿预检 m=0 漏判） |
| `test_shrink_fallback_truncation_with_zero_filtered_still_fails` | 全量快照缩水 + p5w 兜底重复页且 m=0 → 失败（第三稿预检 m=0 漏判） |
| `test_manifest_non_dict_list_is_rewritten_not_crashed` | 遗留 manifest 为 list 不崩、重写为 dict（第三稿漏网#2） |
| `test_pdf_empty_text_layer_is_registered_as_degradation` | pdftotext 退出 0 但无文本层 → 降级（第三稿漏网#3） |
| `test_pdf_extraction_failure_rerun_recovers_not_permanently_skipped` | Day1 提取失败留空 txt → Day2 重跑重新提取并恢复、不永久跳过（第三稿漏网#3） |

**第三稿复跑：32 项全部通过**（主代理在代码工作区代跑，含上述新增反例与既有用例）。
全部使用 FixtureClient / 打桩 `request`，**不发真实网络请求、不跑生产全量抓取**。

## 4. 真实网络验证

**未执行**（本会话 Bash 被安全分类器阻断，由主代理代跑）。本包修复点（水位、分页、失败语义）
均可用 fixture 判定；端点级真实核验属于 B 包范围。

## 5. UNKNOWN / 未解决

1. **3 天 IR / 公告流窗口（单独列为 UNKNOWN）**：投关表与公告流仍是固定 3 天窗口
   （契约 `2026-09-domestic-daily-mirror-contract.md` 第 2、4 条要求"最近三天"）。
   若两次运行间隔超过 3 天，中间日期的投关表与公告流**不会被补抓**。
   本包**未**加 IR 水位：那属于新增状态语义，超出"避免无条件全量重抓"的授权表述，
   需要用户/主代理裁决后再做。目前无证据判断该缺口在生产中的实际发生频率。
2. **9 月 5 日遗留 `.run` 临时目录（11 家 QA、5 份 PDF）的终止机制仍为 UNKNOWN**——
   按修复要求 5，本轮不推断历史进程被谁终止；新代码只能保证后续中断留下可判定痕迹。
3. **重叠窗口 7 天是工程选择**，不是从数据推出的结论：若互动易存在回答日晚于提问日 7 天以上
   且延迟入库的情况，仍可能漏抓。需生产一轮比对才能判定，目前无证据。
4. **`FetchFailure` 会让原本静默通过的公司在日报里显式变 partial**，失败条目数量可能上升；
   这是暴露原先被吞掉的失败，不是新增故障，但需人工确认升幅是否符合预期。
   尤其：p5w 真出故障时，所有需要兜底的公司都会报失败——这是诚实降级，不是新故障。
5. 未改动 `README.md`（不在本包写入范围）。退出码、新增状态文件与降级语义需主代理在整合时
   补进 README 的国内日更小节。

## 6. 执行说明

- 本会话 Bash 工具被 auto-mode 安全分类器阻断（与命令内容无关，重试同样失败）。
  按你的指示**未绕过安全模式**：测试与提交由主代理（controller）代执行。
- 本会话无 `apply_patch` 工具（ToolSearch 未检索到），编辑改用 Edit/Write，效果等价。
- 提交范围仅限本包 5 个文件，格式 `维护: ...`，不推送、不合并。
- **代码已冻结**：第三稿 32 项全部通过后不再做任何编辑或提交，由主代理在产品工作区按正常钩子本地提交。
