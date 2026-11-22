# 2026-09-12 自动任务等待规则修复

当前状态：现有自动任务等待规则已更新并回读验证；国内正式断点续跑已自然结束，今日日报已生成。合并组装状态由 partial 恢复为 complete，采集健康度由 failed 变为 partial，仍有真实请求失败和月度重筛鉴权缺口。

## 已确认的失败原因

9 月 12 日早晨的自动执行器因约 150 秒没有终端输出，提前中断国内采集；命令实际运行 168.596 秒后以 130 退出。06:52:31 刚保存完成第 25 家公司的断点，06:52:34 被中断，run-status 为 failed、27/188、error_count=0。当时采集仍有进度，不能据终端静默判断卡住。

早晨采集器指纹与 9 月 11 日修复后的代码一致，成功日期均为 9 月 11 日，实际增量起点为 9 月 4 日；华工科技在已完成的 25 家公司内。

## 本次修改

通过 Codex 的 automation_update 工具更新原任务 optical-daily-update，仅修改 prompt。已回读确认任务 ID、名称、启用状态、每日 06:47 时间、模型 gpt-5.6-luna、medium 推理配置、项目和通知设置均保持原样。

- 终端静默和单次工具等待结束不等于卡住，禁止沿用 90/120/150 秒中断整轮的做法。
- 每 30–60 秒观察进度、阶段、公司、请求及其时间，并核对进程。任一有变化就继续等待。
- 内部单公司 60 秒预算继续生效，个别公司失败不停止整轮。
- 连续 10 分钟无变化只触发诊断，不自动终止。终止前须核对阶段超时、两次间隔 60 秒的进程快照，以及是否仍有下载、提取或校验子进程。
- 命令真实退出并核对最终状态与当日产物后，才继续后续阶段；partial/failed 不得表述为成功。

未修改采集算法或新增调度器。没有改写旧自动化记忆；新任务规则明确指出旧的提前中断记录不能作为操作要求。

## 正式验证

运行前已备份 93 家公司的 44,830 条问答、25 家公司断点、成功日期、状态和合并日报。原始早晨审计目录保持不变。

在原项目中用现有命令重新执行 2026-09-12 国内日更，使用现有断点和文件锁。15:20:21 开始，15:30:28 自然结束，约 10 分 7 秒，退出码 1 对应 partial；未向采集器发送中断信号。过程快照显示持续换公司和请求，超过原 150 秒边界后仍正常推进。

| 项目 | 实际结果 |
| --- | --- |
| 公司问答 | 93 家均已尝试，90 家成功，3 家请求超时；含复用今早 25 家断点 |
| 本次新增问答记录 | 80 条，属于采集记录增量，不等于经人工确认的研究结论 |
| 历史保留 | 原 44,830 条主键全部保留，总计 44,910 条；974 条旧记录只更新 fetch_date，旧问答内容无变化 |
| 查询日期 | 90 家成功日期推进至 2026-09-12；失败 3 家保留 2026-09-11 |
| 公告查询 | 阶段结束，命中关注条件的公告 30 条 |
| 投关表 | 两路查询均超时，不能由新增 0 份推断没有新材料 |
| 月度重筛 | 接口返回需要 token，0/463 完成，仍未完成；最终进度计数不代表这 463 家已成功重筛 |
| 正式账本及源语料 | canonical 逐文件指纹不变，源仓库受保护内容指纹不变 |
| 当日合并 | 国内和海外输入齐全、日期匹配，assembly=complete；两侧均有采集缺口，collection=partial |

3 家问答超时：300456、300502、300548。2 路投关表超时，加上月度重筛缺 token，合计 6 项错误。如实保留于正式日报和状态文件，未作成功标记。

本次只改自动任务 prompt 和控制/交付文档，未更改采集代码，因此不新增重复实现的单元测试。验证为配置回读、工作包 YAML、git diff --check、正式采集和逐记录/指纹比较；采集器自身调用的 scan.py --check 显示不变量全绿。

本轮由当前任务按新规则监督原命令到结束；下一次 06:47 的自动执行尚未发生，不能据此宣称下一次定时运行已验收。

本次不重新采集海外；合并已复用今日早晨的海外最终结果，并继续保留其 7 个端点失败、5 条详情失败、10 条缺发布时间拒收和 3 个缺端点的状态。海外自动输出仍是候选，晋升为 0。

## 证据

- [本次任务配置草稿](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/automation-prompt.txt)
- [配置回读校验](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/automation-verification.json)
- [运行前备份与指纹](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/before.json)
- [续跑观察记录](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/progress.jsonl)
- [续跑日志](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/domestic.log)
- [正式结果与保留校验](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/validation.json)
- [旧记录字段比较](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/existing-row-changes.json)
- [最终汇总](/Users/jowang/Downloads/workflow-rehearsal-daily-state/audit/2026-09-12-wait-repair/final-result.json)
- [更新后的日报](/Users/jowang/Downloads/workflow-rehearsal-daily-state/combined/daily/2026-09-12.md)
