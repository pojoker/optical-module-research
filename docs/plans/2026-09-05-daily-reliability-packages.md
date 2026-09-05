# 日更可靠性修复分包

目标仓库：pojoker/optical-module-research。功能基线：c695614。
三个开发者在控制文档提交后的同一基线上隔离工作；主代理只做委托、检查、整合与验收。
禁止推送、合并 main、晋升候选、改 canonical 或现有生产日更状态目录。
仅测试临时状态目录。正式数据只读；不读 credentials、旧轨迹或其他 worker 输出。
统一 Python：/Users/jowang/miniconda3/bin/python3。提交格式：维护: ...

## 共同的逻辑合同

- 运行过不等于完成，完成不等于覆盖充分；零候选不等于没有相关新闻。
- 获取失败不能推进成功水位；重跑应保留已有数据并去重。
- 发布日期只来自可归属当前文章的官方字段，不能使用抓取日、版权年份、其他文章或作者注册日期。
- 不因抓取失败放松证据准入。未配置实体与实际端点失败分列。
- 现有成功路径与输出字段保持兼容，不新造调度器。

### 包间接口（最小兼容扩展）

国内可在现有 manifest 增加 run_status（complete/partial/failed），保留 logs。
国内若尚未产出当日日报，轻量 run-status.json 保存 run_date、status（running/complete/partial/failed）、updated_at、已处理/总数及错误摘要；中断后遗留 running 只证明未完成，不能凭时间推定谁终止进程。
海外保留 run-summary.json 的 endpoint_count、endpoint_failed、configured_entity_count、monitored_entity_count、missing_endpoint_count、failure_types；详情抓取失败新增 article_fetch_failure，日期缺失保留 invalid_item。可增加 endpoint_succeeded，但不能将 configured 当成功。
Pi 按这份合同兼容旧版输入；对字段缺失保持 UNKNOWN，不能默认为完整成功。

## A / CodeBuddy Hy4：国内增量与中断

WRITE：domestic_daily/core.py、domestic_daily/cli.py、corpus/_fetch_qa.py、tests/test_domestic_daily.py、docs/reviews/2026-09-05-daily-reliability-codebuddy.md。
READ：上述文件、调用依赖、测试、工作包、必要根级账本只读。

已确认：core.py 每家固定 since=2023-01-01，93 家串行抓取；底层翻页伴随 sleep；日报/日志仅整轮结束写出。9月5日 .run 临时目录遗留11家 QA、5份 PDF，没有当前进程和正式日报，具体终止机制 UNKNOWN。

修复要求：
1. 区分首次回填与日常增量：成功水位加合理重叠窗口；失败不推进、保留历史问答，支持显式回填而不每天重抓三年。
2. 检查底层 fetch 吞掉错误/空结果的语义，不能将抓取失败当成功无增量。分页不能无界，接口限流保留。
3. 运行开始及阶段进度可观察；中断后能确定未完成，错误日志不等整轮结束才可见。后续重跑保留去重和源目录只读边界；不要删除旧临时目录。
4. 局部失败不谎报成功；CLI 与报告清楚说明 partial/failed。不要求在本轮推断历史进程被谁终止。
5. 用临时目录/可控 client 验证首次、重复、增量、抓取失败、水位、运行中断。不得运行生产全量抓取。

## B / OpenCode Omen Alpha：海外 HTTP 与端点

WRITE：calls/http_discovery.py、calls/daily_discovery.py、calls/discovery_config.json、calls/tests/test_http_discovery.py、calls/tests/test_daily_discovery.py、docs/reviews/2026-09-05-daily-reliability-opencode.md。
READ：上述文件及直接 schema/registry 依赖、fixtures、工作包、calls 账本只读、公开官网。

已确认：
- Cisco /c/r/newsroom/en/us/a/y2026/m09、Hamamatsu /jp/en/newsroom.html、IQE /media/press-releases/2026 实测404。
- investors.macom.com 与 investors.poet-technologies.com TLS失败；https://ir.macom.com/overview/ 与 https://www.poet-technologies.com/news-media 同客户端可访问。
- Lumentum IR 原始 HTML 只选出新闻首页/SEC/FAQ/邮件订阅导航。
- Lumentum 博客 backbone-ai-infrastructure-why-optical-components-will-define-next-era-data-centers 正文可抓，field_date=2026-06-25 在字符80041附近；当前兜底只扫前20000字符且不识别该字段。
- 详情页 _get 失败被 except: continue 静默吞掉。

修复要求：
1. 核验并修正已配置7实体/8端点，依据官网真实链接，不猜URL；不新增其余实体。动态列表优先官方 feed/公开接口，确实无法采集则显式 unsupported，不冒充成功。
2. 只选文章链接，剔除导航/FAQ/alerts/索引；不能因同域就选。不得绕过登录、验证码、付费或反爬。
3. 按文章归属解析发布日期；支持真实站点嵌入字段，避免抓到作者时间、版权或其他节点。不能把全文首次日期当发布日期；无可信日期仍拒收并报告。
4. 详情失败可追踪；部分文章成功也保留失败计数，不能让整个端点结果看起来无错。
5. 测试真实形状的最小样例（无需复制整页）、错日期反例、导航、文章失败与混合成功；轻量真实 GET 核验端点。不要写生产 staging。

## C / Pi GLM 5.3 Flash：日报状态与覆盖语义

WRITE：daily_intelligence/core.py、daily_intelligence/cli.py、tests/test_daily_intelligence.py、docs/reviews/2026-09-05-daily-reliability-pi.md。
READ：上述文件、共同接口及现有国内/海外输入格式，只读；不要编辑 A/B 文件。

修复要求：
1. 输入文件存在不等于采集完整：当日 manifest/run summary 的失败、过期、缺失、未完成进度都必须反映到整体结果。
2. 将 assembly_status（组装完整性）与 collection_status（采集健康度）分开，缺旧字段不能推断成功。保留兼容字段，CLI 避免用 OK 掩盖 partial；确定合理非零退出并测试。
3. 7/81 是已配置实体覆盖，不是成功抓取或研究覆盖；8端点5失败另列，详情失败和格式拒收另列。
4. 降级场景写“本次未提取到事件，采集不完整，不能判断无新消息”，避免只写“无事件增量”。
5. 当前有日期但国内未完成时显示进度；不凭遗留 running 断言仍运行或被kill。报告组装失败与来源失败可区分。
6. 回归测试覆盖完整、缺日报、昨天manifest、今日未完成、端点部分失败、缺端点、零事件、旧版未知字段。

## 每包交付

完成代码与针对性测试，本地提交，然后在自己的允许报告中写：提交、行为变化、测试命令/结果、真实网络验证、UNKNOWN。若提交钩子因 worktree 缺语料阻塞，不用 --no-verify；报告后由主代理处理。完成后保留 TUI。

## 主代理验收

核查每包 diff 和边界，复跑针对性测试，并测试三个模块接口兼容与缺失输入反例。
在本地集成分支选择性整合，运行 scan --check、render --verify、participation --check、calls check。
生产 canonical 与 calls/out、九页前端不得变化。范围外发现列报告，不实现。
