# 包 C / Pi 交付报告 — 日报状态与覆盖语义

日期：2026-09-05 · 基线：d413037 · 分支：`codex/daily-report-20260905`（隔离 worktree `/Users/jowang/Downloads/optical-daily-report`）

> 修订 2：按主代理/控制器复核修复三处 false-complete（见「控制器反例修复」一节）。
> 修订 3：缺/非 dict 的 failure_types 视为诊断未知；负数计数拒用；publish 分支恢复 return 0（见「修订 3」）。

## 修订 3（第三审）

1. **缺 failure_types 不再当作空**：run-summary 缺少 `failure_types` 键或其非 dict（如 `"none"`）→ collection `unknown` + 注记「失败诊断未知，不推断无失败」；显式 `{}` 才可表示无记录失败（恢复 complete）。
2. **负数计数拒用**：`_int_field` 拒绝负数（视同字段缺失 → unknown），同时拒绝 bool/非 int。
3. **publish 分支恢复 `return 0`**（原 main 返回 None 违反 int 合同）。

## 提交

- 本地提交由主代理/控制器处理（pre-commit 钩子因 worktree 缺 corpus 语料阻塞，未用 --no-verify、未无限等待；全部改动已 staged）。建议提交信息：`维护: 日报区分组装完整性与采集健康度，零候选不冒充无新闻`。
- 写入范围：`daily_intelligence/core.py`、`daily_intelligence/cli.py`、`tests/test_daily_intelligence.py`、本报告。未触碰 A/B 包文件与 canonical。

## 控制器反例修复（修订 2）

1. **manifest complete 被当日 running 覆盖**：当存在有效当日 run-status（run_date 必须精确匹配，缺 run_date 拒用并报错）且 status=running 时，不再被 manifest 的 complete 声明覆盖：报告存在 → `unknown` + 冲突说明；报告缺失 → `partial`（running 只证明未完成）。
2. **run-status errors 与 manifest logs 失败条目被 complete 吸收**：run-status `errors` 非空或 manifest `logs` 含「失败」条目时，complete 降为 `partial` 并注明条数（logs 匹配「失败」是保守启发式，格式以 A 包实现为准）。
3. **海外缺覆盖字段冒充 complete**：`endpoint_count`/`endpoint_failed`/`configured_entity_count`/`monitored_entity_count`/`missing_endpoint_count` 任一缺失 → `unknown`（不推断零缺口）；`endpoint_succeeded` 缺失仍为 UNKNOWN 注记。
4. **未归类失败类型被忽略**：`failure_types` 中除 `no_relevant_content`（显式非失败）外的任何 count>0 条目都使采集降为 `partial` 并注明类型与次数。
5. 冲突声明（manifest 与 run-status 完成度不一致）按更保守结果记录并注明。

回归测试新增 5 个（见下），三处控制器复核直接核验通过。

## 行为变化

1. **assembly_status 与 collection_status 分列**（`combine_daily_reports` JSON 与 Markdown「## 汇总状态」段）：
   - `assembly_status`：两份日报与输入文件是否齐全、可读、日期匹配（原语义保留，兼容字段不变）。
   - `collection_status`：采集健康度，取国内/海外两侧较严重者，取值 `complete/unknown/partial/failed`。
   - 字段缺失一律 `unknown`，不推断成功；JSON 新增 `collection.domestic` / `collection.overseas` 明细。
2. **国内采集完成度**（新）：
   - 读 manifest `run_status`（complete/partial/failed）与轻量 `run-status.json`（run_date/status/processed/total/updated_at/errors）。
   - 当日报告缺失且 run-status=running → collection `partial`，报告显示进度（如「已处理 11/93」）并注明「遗留 running 只证明未完成，不能推断进程仍在运行或已被终止」。
   - 旧版 manifest 无 `run_status` → `unknown`，不推断成功；manifest 日期过期 → 拒用并 `unknown`（先校验日期再判完成度）。
3. **海外覆盖语义修正**：
   - 「已配置端点覆盖 7/81 个监控实体」显式标注为配置覆盖，不代表采集成功或研究覆盖。
   - 端点行拆为「端点 N 个：成功 X / 失败 Y」；`endpoint_succeeded` 缺失时显示 UNKNOWN（已配置不等于成功）。
   - 详情抓取失败（`article_fetch_failure`，顶层或 failure_types）与格式拒收（`invalid_item`）单独成行；字段缺失显示 UNKNOWN。
   - `no_relevant_content` 不计为失败。
4. **零候选不再冒充无新闻**：事件为零且海外采集不完整时，输出「本次未提取到事件，采集不完整，不能判断无新消息」；仅采集明确 complete 才写「无事件增量」。
5. **CLI 诚实退出**（`python3 -m daily_intelligence combine`）：
   - 组装 complete 且采集 complete → `OK: combined daily ...`，退出码 0。
   - 否则 → `PARTIAL: ... assembly=... collection=...`，退出码 1；不用 OK 掩盖 partial。
6. 兼容性：既有输出字段（`assembly_status`、summary 计数、publish 子命令）不变；对无新字段的旧版输入保持 `unknown` 而非报错。

## 测试命令与结果

```
PYTHONPATH=. /Users/jowang/miniconda3/bin/python3 tests/test_daily_intelligence.py
Ran 18 tests ... OK
```

- 原 5 个测试全部保留并通过（含 publish 子命令、输入只读校验、disjoint 校验）。
- 修订 3 新增 3 个：failure_types 缺失/非 dict/显式空三态、负数与非 int 计数拒用、publish CLI 返回 0。
- 修订 2 新增 5 个：manifest complete + 当日 running 不冒充 complete、缺 run_date 的 run-status 拒用、run-status errors/manifest logs 失败条目降级 complete、海外缺覆盖字段保持 unknown、failure_types 未归类失败降级而 no_relevant_content 不降级。
- 修订 1 新增 5 个：昨日 manifest 拒用、国内 running 进度与中断语义、海外端点部分失败零事件（8 端点 5 失败/7-81/invalid_item 12）、旧版字段 unknown、CLI 退出码 0/1。

## 真实数据核验（只读）

用 `/Users/jowang/Downloads/workflow-rehearsal-daily-state`（只读）跑 `combine --date 2026-09-05` 到临时输出目录：
国内无当日日报/manifest 为 09-04 → assembly partial；海外 8 端点 5 失败、7/81、零事件 → collection partial，报告输出「本次未提取到事件，采集不完整，不能判断无新消息」，CLI 退出 1。行为符合工作包第 4/5 条要求。

## UNKNOWN 与范围外发现

- 国内「遗留 running 被谁终止、是否仍有进程」不可由本包判定（合同明确不推断）；仅标注未完成。
- `run-status.json` 的 `processed/total` 字段名以 A 包实现为准，本包按合同命名读取，缺失时进度显示为 `?/?`。
- 海外 `article_fetch_failure` 顶层字段名若与 B 包实际输出不同，本包同时读 `failure_types.article_fetch_failure` 兜底；若两者都缺则显示 UNKNOWN（不猜）。
- 范围外发现（未实现，仅记录）：演练目录国内 manifest 仍是 2026-09-04 旧版格式、无 run_status，A 包交付后需用新输入复跑一次核验。
