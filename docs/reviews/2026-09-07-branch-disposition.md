# 逐分支增量处置表（待用户审核）

盘点时间：2026-09-07T15:37:16+08:00。状态：建议稿；没有执行合并、推送、删除、重置或候选晋升。

## 审核先看这里

共覆盖 **34 个逻辑分支：旧仓库22个、当前仓库12个；22个登记工作树：旧12个、当前10个**。同名本地/远端引用归在一行，SHA不同则分别说明。实时远端分别18个和2个；本地分别19个和12个。

建议先批准三个方向：①保全旧主目录、回补和教学实验；②对已有逐字承接证据的日更/审阅工作树准备退役；③核清实时远端 main 后确定唯一开发基线。此处“退役”仅表示建议停止作为活动工作目录，实际删除仍需明确对象和授权。

每行最后一栏均为“待审”。可直接回复编号，例如“N01同意退役准备、O18保留实验、O16先保全”。批准建议方向不自动授权推送、删除或领域事实晋升。

## 证据口径与限制

- 当前承接比较点固定为 `b3e287e6ac88b0f87411bed1b13caef17e51a0b7`，不包含本轮工作包与报告改动。
- 旧仓库内部比较点为 `bacc7b523b320732db1de219d605f9fd69bd8b19`（旧恢复前端/日更基线），这是比较参照，不是旧仓库全部增量的总集。
- “基线独有/该支独有”来自 git rev-list --left-right --count；0个独有提交可证明历史包含，非0不能直接推出功能缺失（可能移植后SHA不同）。
- 两仓库对象库联合只读核对后未找到共同祖先。旧→新承接不能用merge判定；下方对允许路径做同路径Git blob哈希比较。相同只证明该文件快照一致，不同/缺失不证明应该移植。
- 不读取archive、闭环试点及raw agent材料的文件内容。此类路径只在Git状态/元信息中计数，必要时列为保全对象；闭环分支不展开提交和文件内容。
- 没有查调度器、运行进程、文件外部引用，没有运行领域机器门；所有删除建议都还缺运行依赖核验与恢复保全。
- N08未提交计数取报告创建前：工作包1项修改、原有报告1项未跟踪；交付本报告后增加1项未跟踪报告，这是本轮新增。
- 当前未提交内容与暂存区分别核对；目录级默认status会折叠新目录，本表用--untracked-files=all按文件计数，不能直接与Kimi的142条/8条相减。

### 实时远端变化（重要）

通过 git ls-remote --heads 只读查询：旧仓库18个远端分支与本地缓存一致；当前仓库远端 `main=b2ba8450f288f67c00fde51ec402655d417835a6`，本地main及origin/main缓存仍为 `7ff3b25`。远端remediate分支仍为 `c695614`。
本地没有b2ba845对象；GitHub CLI compare查询返回HTTP 404，因此该提交内容及其与b3e287e关系为UNKNOWN。没有fetch或更新任何Git引用。此未知项会阻挡最终主线裁决，但不阻挡其他增量盘点。

## 逐分支审核总表

### 旧仓库 workflow-rehearsal

| 编号 | 分支 | 本地 / 远端SHA | 基线独有 / 该支独有 | 未提交文件 | 建议 | 用户审核 |
|---|---|---|---|---|---|---|
| O01 | `codex/daily-domestic-mirror-opencode` | cb7f466 / cb7f466 | 14 / 3 | 0 | 冻结旧实现；按 domestic_daily 的功能差异挑选，不能整支覆盖当前日更。 | 待审 |
| O02 | `codex/daily-intelligence-mirror` | df0ea06 / df0ea06 | 49 / 21 | 0 | 冻结旧合并日报实现；仅评估是否仍需原样 TXT/HTML 出口，当前已有统一组装入口。 | 待审 |
| O03 | `codex/daily-news-adapters-codebuddy` | a6e1899 / a6e1899 | 14 / 3 | 0 | 历史适配器分支；核对巨潮能力是否已承接，勿按提交名称认定已完全包含。 | 待审 |
| O04 | `codex/daily-news-core-opencode` | 02dc640 / 02dc640 | 14 / 3 | 0 | 历史日更核心分支；与 adapters 是平行增量，优先核对 integration 的承接。 | 待审 |
| O05 | `codex/daily-news-integration` | cf0a8c5 / cf0a8c5 | 14 / 5 | 0 | 旧新闻集成实现；与 mirror 并非简单线性升级，不整支合并。 | 待审 |
| O06 | `codex/daily-overseas-mirror-codebuddy` | 8fd6181 / 8fd6181 | 49 / 16 | 0 | 旧海外发现实现；当前 calls.daily_discovery 已有后续可靠性修复，仅查漏。 | 待审 |
| O07 | `codex/domain-research-simplification-design` | 9ff64f7 / 9ff64f7 | 14 / 1 | 0 | 冻结设计实验，不继续推进；是否提取仍适用的建议由用户裁决。 | 待审 |
| O08 | `codex/goal-control-protocol-20260903` | a886a72 / — | 7 / 0 | 无工作树 | 旧恢复基线已含其历史；保留现行控制规则，不再作为开发入口。 | 待审 |
| O09 | `codex/industry-chain-v2` | 227f503 / 227f503 | 14 / 0 | 无工作树 | 历史基础；不作为继续开发基线，完成保全后可退役活动引用。 | 待审 |
| O10 | `codex/overseas-news` | 3d6f663 / 3d6f663 | 49 / 15 | 无工作树 | 旧海外基础；与当前仓库无共同历史，账本和功能需分别核对，不能直接删。 | 待审 |
| O11 | `codex/rescue-domain-data-20260902` | 5ec2153 / 5ec2153 | 14 / 3 | 648 | 优先保全脏工作树；逐项核对研究候选和救援成果，不能直接删或整批晋升。 | 待审 |
| O12 | `codex/rescue-overseas-calls-20260902` | 3420f3c / 3420f3c | 49 / 16 | 12 | 保全未提交专题文档、测试及生成物；账本救援增量单独复核。 | 待审 |
| O13 | `codex/research-graph-closure-pilot` | — / 29cc861 | 14 / 1 | 无工作树 | 仅登记元信息；按现行章程不恢复该架构，冻结保留历史，未展开内容。 | 待审 |
| O14 | `codex/research-graph-closure-pilot-fix-codebuddy` | — / d0ab510 | 14 / 4 | 无工作树 | 仅登记元信息；修正版不构成重新准入理由，冻结保留历史，未展开内容。 | 待审 |
| O15 | `codex/restore-frontend-daily-20260904` | bacc7b5 / bacc7b5 | 0 / 0 | 无工作树 | 旧恢复比较基线；作为历史快照保留，不再作为新开发入口。 | 待审 |
| O16 | `codex/restore-optical-domain-mainline-20260902` | 5e4c620 / 216e53f | 8 / 8 | 1 | 优先保全8个本地增量提交及问答文件；回补代码、原始材料、领域晋升、PQ009草案分开审核。 | 待审 |
| O17 | `cursor/dev-environment-setup-2990` | — / 53a1b06 | 130 / 2 | 无工作树 | 单独评估云端环境及字体修复的需要；不因独立小分支就自动丢弃。 | 待审 |
| O18 | `exp/pedagogical-foundation-20260905` | d0f6515 / — | 0 / 8 | 2 | 保留独立教学实验；用户决定是否吸收01B及教学叙事，候选知识另审，不整支覆盖。 | 待审 |
| O19 | `fix/foundation-page-rework-20260905` | de5592d / — | 0 / 1 | 无工作树 | 已是教学实验祖先；跟随实验保全，可列入后续退役候选。 | 待审 |
| O20 | `judge/empty-cells` | 39b6136 / — | 103 / 0 | 0 | 旧恢复基线已有提交历史；仅保留历史用途，退役前查运行引用。 | 待审 |
| O21 | `master` | fcc87b6 / fcc87b6 | 130 / 1 | 无工作树 | 旧默认分支；不作为承接目标；默认分支调整及远端删除须另审。 | 待审 |
| O22 | `remote/foreign-path2` | 2e5bc9d / 2e5bc9d | 141 / 1 | 无工作树 | 仍有独有提交，不能宣称已完全包含；只核对相关取证增量，历史保留。 | 待审 |

### 当前仓库 optical-module-research

| 编号 | 分支 | 本地 / 远端SHA | 基线独有 / 该支独有 | 未提交文件 | 建议 | 用户审核 |
|---|---|---|---|---|---|---|
| N01 | `codex/daily-domestic-20260905` | d413037 / — | 5 / 0 | 5 | 当前未提交5个文件均与承接基线一致；保全并查运行依赖后，优先退役工作树。 | 待审 |
| N02 | `codex/daily-overseas-20260905` | d413037 / — | 5 / 0 | 6 | 当前文件已与承接基线一致；暂存区有中间态，需显式保全或放弃后退役工作树。 | 待审 |
| N03 | `codex/daily-report-20260905` | d413037 / — | 5 / 0 | 4 | 当前未提交4个文件均与承接基线一致；保全并查运行依赖后，优先退役工作树。 | 待审 |
| N04 | `codex/factory-agy-site-transparency-20260904` | 837fe1d / — | 15 / 1 | 0 | 已发现对应集成及后续文案修正；保留承接版，勿重新整支合并；完成核对后退役。 | 待审 |
| N05 | `codex/factory-codebuddy-capability-20260904` | 4c38622 / — | 15 / 1 | 0 | 已发现对应集成及schema保留修正；保留承接版，勿重新引入worker的字段改名。 | 待审 |
| N06 | `codex/factory-opencode-overseas-20260904` | e32e62d / — | 15 / 1 | 0 | 已发现对应集成及动态覆盖口径修正；保留承接版，勿恢复硬编码统计测试。 | 待审 |
| N07 | `codex/factory-pi-render-boundaries-20260904` | 6d662c9 / — | 15 / 1 | 0 | 已发现对应集成及锚点/业务口径后续修正；保留承接版，勿整支覆盖。 | 待审 |
| N08 | `codex/fix-daily-reliability-20260905` | b3e287e / — | 0 / 0 | 2 | 保留为本轮固定比较基线；远端main新提交核清前，不宣布其为最终唯一主线。 | 待审 |
| N09 | `codex/remediate-data-semantics-20260904` | c695614 / c695614 | 6 / 0 | 无工作树 | 提交已包含在承接基线；远端main核清并完成保全后，列入退役候选。 | 待审 |
| N10 | `codex/review-cursor-fable51-20260904` | c53b9bd / — | 9 / 0 | 1 | 审阅文件与承接基线逐字一致；保全及查依赖后优先退役工作树。 | 待审 |
| N11 | `codex/review-kimi-k3-20260904` | c53b9bd / — | 9 / 0 | 1 | 审阅文件与承接基线逐字一致；保全及查依赖后优先退役工作树。 | 待审 |
| N12 | `main` | 7ff3b25 / b2ba845（实时）；缓存7ff3b25 | 16 / 0 | 无工作树 | 本地及缓存均与实时远端不同（祖先关系未核实）；先核清b2ba845，暂不决定最终基线和合并方向。 | 待审 |

## 已核实的处置重点

1. 三个日更开发目录共15个当前未提交文件（国内5、海外6、日报4）与b3e287e逐字一致。两个独立审阅目录各1个报告也逐字一致。海外暂存区还保留不同中间态，见对应明细；不能用git reset/clean替代保全决定。
2. 四个factory worker各有1个独有提交，不能按Git祖先关系说已合并。当前基线历史存在对应集成提交：能力5a9b12d、海外f500e4d、渲染b0c6876、页面7f40544；随后bcdb0ec又收紧语义。直接diff显示承接版保留canonical字段、修正动态覆盖统计、收紧锚链接解析并补充出货业务口径、修正“原文核验=独立证实”等文案。建议保留承接版，勿重新整支合并worker。未重跑测试，不宣称全部功能验收。
3. 旧restore-optical本地5e4c620相对远端216e53f领先8个提交，且与旧restore-frontend基线各有8个独有提交。它不是旧frontend的单纯前一版。8个提交涵盖：关系合同削减、断档回补、问答去噪与回补、半年报判定、海外季度回补、PQ009草案、恢复入口；其中领域写入不能随工程移植自动接受。
4. exp/pedagogical有旧恢复基线之外8个提交，含01B投资者导读与候选知识；fix/foundation的de5592d已包含在exp历史。用户应审核教学方向，而不是在两个分支间二选一整仓覆盖。
5. 旧主目录的大批未跟踪研究包包含候选、控制草案、审阅和raw材料。本轮仅做允许路径哈希及元信息分组，未将其内容当作现行规则；保全和是否采纳是两个独立决定。

## 建议执行顺序（本轮未执行）

| 次序 | 下一项工作 | 交付给用户的结果 | 本轮状态 |
|---|---|---|---|
| 1 | 保全旧主目录、回补、海外专题、教学实验及暂存中间态 | 可恢复副本及对象清单；不自动推送 | 待授权实施 |
| 2 | 取得实时远端main对象并核对 | b2ba845与b3e287e的关系和最终基线建议 | UNKNOWN |
| 3 | 按本表批准方向核对/移植必要增量 | 代码、研究候选、已审核领域事实分开的diff | 待审核方向 |
| 4 | 核对调度/路径引用、运行验收 | 稳定入口不依赖待退役工作树 | 未执行 |
| 5 | 用户审核具体删除/合并/推送清单 | 明确对象与恢复位置后执行 | 未授权 |

## 分支证据明细

### O01 · codex/daily-domestic-mirror-opencode

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`cb7f466eee1122531edd3c27d55d6c1789189113`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-domestic-mirror`。
- 建议：冻结旧实现；按 domestic_daily 的功能差异挑选，不能整支覆盖当前日更。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - cb7f466 修复: 对齐国内日更采集与召回语义 +0点 +0边 空格2/41 驳回0
  - 64c5f7b 维护: 国内日更镜像隔离实现 +0点 +0边 空格2/41 驳回0
  - 29cc861 维护: 增加研究图闭环 pilot

- 两端快照差异：112个路径（含历史/禁读路径名称）；允许展示路径104个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同31、当前缺失14。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`contracts/question_generation_rules.yaml`、`contracts/relation_adapters.yaml`、`contracts/relation_types.yaml`、`docs/research/光模块知识体系-当前任务控制文稿.md`、`out/generated_diagnostic_questions.jsonl`、`out/relation_assertion_index.jsonl`、`out/relation_slot_states.jsonl`、`relation_assertions.yaml`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：26个路径；以下列允许路径前15项。
  - `M README.md`
  - `A contracts/question_generation_rules.yaml`
  - `A contracts/relation_adapters.yaml`
  - `A contracts/relation_types.yaml`
  - `A docs/plans/2026-09-domestic-daily-mirror-contract.md`
  - `A domestic_daily/__init__.py`
  - `A domestic_daily/__main__.py`
  - `A domestic_daily/cli.py`
  - `A domestic_daily/core.py`
  - `A out/generated_diagnostic_questions.jsonl`
  - `A out/relation_assertion_index.jsonl`
  - `A out/relation_slot_states.jsonl`
  - `A relation_assertions.yaml`
  - `M scan.py`
  - `A tests/__init__.py`
  - 其余7个允许路径未逐项展开；处置执行前须全量核对。

### O02 · codex/daily-intelligence-mirror

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`df0ea0690f513bbfca95add41b77869a1a99354b`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-daily-mirror-final`。
- 建议：冻结旧合并日报实现；仅评估是否仍需原样 TXT/HTML 出口，当前已有统一组装入口。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - df0ea06 维护: 原样发布国内TXT与海外HTML +0点 +0边 空格2/41 驳回0
  - 61a7b05 fix: preserve original daily report format
  - fda315f feat: combine domestic and overseas daily reports
  - e46a433 修复: 对齐国内日更采集与召回语义 +0点 +0边 空格2/41 驳回0
  - 95a791d 维护: 国内日更镜像隔离实现 +0点 +0边 空格2/41 驳回0
  - 8fd6181 维护: 海外事件日更镜像候选流水线 +0点 +0边 空格2/40 驳回0
  - 3d6f663 产出: +0点 +0边 空格2/40 驳回0 海外季度池新增LWLG与Smartoptics
  - b98c1db 产出: +0点 +0边 空格2/40 驳回0 海外候选分层复核：Microchip晋级事件监控，Hamamatsu保留发现队列
  - bb9518f 维护: 固化海外新闻扩容交接清单
  - acb03a6 维护: 海外事件成熟阶段要求实际证据

- 两端快照差异：556个路径（含历史/禁读路径名称）；允许展示路径330个。只列前12个：
  - `.gitattributes`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/README.md`
  - `calls/entity_relationships.csv`
  - `calls/event_claims.csv`
  - `calls/event_evidence.csv`
  - `calls/events.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同93、当前缺失5。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/adr/0009-separate-entity-identity-from-tracking-tier.md`、`docs/handoffs/2026-08-13-kimi-overseas-news-expansion.md`、`docs/research/2026-08-15-overseas-lwlg-smartoptics.md`、`docs/research/2026-08-15-overseas-next-10.md`、`docs/research/2026-08-overseas-company-universe-candidates.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：76个路径；以下列允许路径前15项。
  - `M CONTEXT.md`
  - `M README.md`
  - `A calls/DAILY-DISCOVERY.md`
  - `M calls/README.md`
  - `M calls/SPEC.md`
  - `A calls/company_candidates.csv`
  - `A calls/company_tier_reviews.csv`
  - `A calls/daily_discovery.py`
  - `A calls/discovery_config.json`
  - `A calls/entity_relationships.csv`
  - `M calls/event_claims.csv`
  - `M calls/event_evidence.csv`
  - `M calls/event_intelligence.py`
  - `M calls/events.csv`
  - `A calls/fixtures/daily_discovery/AAOI_IR_RELEASES.json`
  - 其余60个允许路径未逐项展开；处置执行前须全量核对。

### O03 · codex/daily-news-adapters-codebuddy

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`a6e1899b31d9589ff6b13ef103c73f486e5886d0`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-codebuddy-news`。
- 建议：历史适配器分支；核对巨潮能力是否已承接，勿按提交名称认定已完全包含。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - a6e1899 工程: 新增巨潮公告日更适配器
  - e5da741 工程: 新增隔离式海内外日更核心模块
  - 29cc861 维护: 增加研究图闭环 pilot

- 两端快照差异：129个路径（含历史/禁读路径名称）；允许展示路径121个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同28、当前缺失29。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`contracts/question_generation_rules.yaml`、`contracts/relation_adapters.yaml`、`contracts/relation_types.yaml`、`docs/research/光模块知识体系-当前任务控制文稿.md`、`news_daily/__init__.py`、`news_daily/__main__.py`、`news_daily/adapters/__init__.py`、`news_daily/adapters/base.py`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：34个路径；以下列允许路径前15项。
  - `A contracts/question_generation_rules.yaml`
  - `A contracts/relation_adapters.yaml`
  - `A contracts/relation_types.yaml`
  - `A news_daily/__init__.py`
  - `A news_daily/__main__.py`
  - `A news_daily/adapters/__init__.py`
  - `A news_daily/adapters/base.py`
  - `A news_daily/adapters/cninfo.py`
  - `A news_daily/adapters/fixture.py`
  - `A news_daily/cli.py`
  - `A news_daily/config.py`
  - `A news_daily/config.toml`
  - `A news_daily/models.py`
  - `A news_daily/runner.py`
  - `A news_daily/storage.py`
  - 其余15个允许路径未逐项展开；处置执行前须全量核对。

### O04 · codex/daily-news-core-opencode

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`02dc640c41bc5b814399f785e2c1f1946fc70f29`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-opencode-news`。
- 建议：历史日更核心分支；与 adapters 是平行增量，优先核对 integration 的承接。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 02dc640 工程: 新增海外新闻来源适配器
  - e5da741 工程: 新增隔离式海内外日更核心模块
  - 29cc861 维护: 增加研究图闭环 pilot

- 两端快照差异：131个路径（含历史/禁读路径名称）；允许展示路径123个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同28、当前缺失31。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`contracts/question_generation_rules.yaml`、`contracts/relation_adapters.yaml`、`contracts/relation_types.yaml`、`docs/research/光模块知识体系-当前任务控制文稿.md`、`news_daily/__init__.py`、`news_daily/__main__.py`、`news_daily/adapters/__init__.py`、`news_daily/adapters/base.py`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：36个路径；以下列允许路径前15项。
  - `A contracts/question_generation_rules.yaml`
  - `A contracts/relation_adapters.yaml`
  - `A contracts/relation_types.yaml`
  - `A news_daily/__init__.py`
  - `A news_daily/__main__.py`
  - `A news_daily/adapters/__init__.py`
  - `A news_daily/adapters/base.py`
  - `A news_daily/adapters/fixture.py`
  - `A news_daily/adapters/rss_atom.py`
  - `A news_daily/adapters/sec_submissions.py`
  - `A news_daily/cli.py`
  - `A news_daily/config.py`
  - `A news_daily/config.toml`
  - `A news_daily/models.py`
  - `A news_daily/runner.py`
  - 其余17个允许路径未逐项展开；处置执行前须全量核对。

### O05 · codex/daily-news-integration

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`cf0a8c5d2071ec954c21846635cc699b819b293f`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-news-integration`。
- 建议：旧新闻集成实现；与 mirror 并非简单线性升级，不整支合并。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - cf0a8c5 工程: 完成海内外新闻日更集成
  - e249b89 工程: 新增巨潮公告日更适配器
  - 02dc640 工程: 新增海外新闻来源适配器
  - e5da741 工程: 新增隔离式海内外日更核心模块
  - 29cc861 维护: 增加研究图闭环 pilot

- 两端快照差异：137个路径（含历史/禁读路径名称）；允许展示路径129个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同28、当前缺失37。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`contracts/question_generation_rules.yaml`、`contracts/relation_adapters.yaml`、`contracts/relation_types.yaml`、`docs/research/光模块知识体系-当前任务控制文稿.md`、`news_daily/__init__.py`、`news_daily/__main__.py`、`news_daily/adapters/__init__.py`、`news_daily/adapters/base.py`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：42个路径；以下列允许路径前15项。
  - `A contracts/question_generation_rules.yaml`
  - `A contracts/relation_adapters.yaml`
  - `A contracts/relation_types.yaml`
  - `A news_daily/__init__.py`
  - `A news_daily/__main__.py`
  - `A news_daily/adapters/__init__.py`
  - `A news_daily/adapters/base.py`
  - `A news_daily/adapters/cninfo.py`
  - `A news_daily/adapters/fixture.py`
  - `A news_daily/adapters/rss_atom.py`
  - `A news_daily/adapters/sec_submissions.py`
  - `A news_daily/cli.py`
  - `A news_daily/config.live.example.toml`
  - `A news_daily/config.py`
  - `A news_daily/config.toml`
  - 其余23个允许路径未逐项展开；处置执行前须全量核对。

### O06 · codex/daily-overseas-mirror-codebuddy

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`8fd6181bdb24885442a587dca7ebde638f5a035f`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-overseas-mirror`。
- 建议：旧海外发现实现；当前 calls.daily_discovery 已有后续可靠性修复，仅查漏。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 8fd6181 维护: 海外事件日更镜像候选流水线 +0点 +0边 空格2/40 驳回0
  - 3d6f663 产出: +0点 +0边 空格2/40 驳回0 海外季度池新增LWLG与Smartoptics
  - b98c1db 产出: +0点 +0边 空格2/40 驳回0 海外候选分层复核：Microchip晋级事件监控，Hamamatsu保留发现队列
  - bb9518f 维护: 固化海外新闻扩容交接清单
  - acb03a6 维护: 海外事件成熟阶段要求实际证据
  - 85f33b2 产出: +0点 +0边 空格2/40 驳回0 新增同源去重与订单事件
  - 856e639 产出: +0点 +0边 空格2/40 驳回0 新增5条高价值海外事件
  - e585f8a 产出: +0点 +0边 空格2/40 驳回0 发现队列接入页面
  - f6bf159 产出: +0点 +0边 空格2/40 驳回0 长尾34家公司分层收录
  - 3df1c24 产出: +0点 +0边 空格2/40 驳回0 第二批20家公司分层落库

- 两端快照差异：567个路径（含历史/禁读路径名称）；允许展示路径341个。只列前12个：
  - `.gitattributes`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/README.md`
  - `calls/daily_discovery.py`
  - `calls/entity_relationships.csv`
  - `calls/event_claims.csv`
  - `calls/event_evidence.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同93、当前缺失5。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/adr/0009-separate-entity-identity-from-tracking-tier.md`、`docs/handoffs/2026-08-13-kimi-overseas-news-expansion.md`、`docs/research/2026-08-15-overseas-lwlg-smartoptics.md`、`docs/research/2026-08-15-overseas-next-10.md`、`docs/research/2026-08-overseas-company-universe-candidates.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：64个路径；以下列允许路径前15项。
  - `M CONTEXT.md`
  - `A calls/DAILY-DISCOVERY.md`
  - `M calls/README.md`
  - `M calls/SPEC.md`
  - `A calls/company_candidates.csv`
  - `A calls/company_tier_reviews.csv`
  - `A calls/daily_discovery.py`
  - `A calls/discovery_config.json`
  - `A calls/entity_relationships.csv`
  - `M calls/event_claims.csv`
  - `M calls/event_evidence.csv`
  - `M calls/event_intelligence.py`
  - `M calls/events.csv`
  - `A calls/fixtures/daily_discovery/AAOI_IR_RELEASES.json`
  - `A calls/fixtures/daily_discovery/CSCO_IR_RELEASES.json`
  - 其余48个允许路径未逐项展开；处置执行前须全量核对。

### O07 · codex/domain-research-simplification-design

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`9ff64f72998cb5c9e19aa832f09b2f83e8b01219`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-simplification`。
- 建议：冻结设计实验，不继续推进；是否提取仍适用的建议由用户裁决。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 9ff64f7 产出: +0点 +0边 空格2/41 驳回0 研究主线架构削减设计

- 两端快照差异：99个路径（含历史/禁读路径名称）；允许展示路径95个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同27、当前缺失2。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/plans/2026-09-domain-research-mainline-reduction-design.md`、`docs/research/光模块知识体系-当前任务控制文稿.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：1个路径；以下列允许路径前15项。
  - `A docs/plans/2026-09-domain-research-mainline-reduction-design.md`

### O08 · codex/goal-control-protocol-20260903

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`a886a72f9bb90dbc5937784fb05e3e642b5728ad`。
- 无登记工作树。
- 建议：旧恢复基线已含其历史；保留现行控制规则，不再作为开发入口。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：63个路径（含历史/禁读路径名称）；允许展示路径60个。只列前12个：
  - `AGENTS.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/fixtures/daily_discovery/AAOI_IR_RELEASES.json`
  - `calls/fixtures/daily_discovery/CSCO_IR_RELEASES.json`
  - `calls/fixtures/daily_discovery/HAMAMATSU_IR_RELEASES.json`
  - `calls/fixtures/daily_discovery/IQE_RNS_RELEASES.json`
  - `calls/fixtures/daily_discovery/LITE_IR_RELEASES.json`
  - `calls/fixtures/daily_discovery/LITE_TECH_BLOG.json`
  - `calls/fixtures/daily_discovery/MTSI_IR_RELEASES.json`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同10、当前缺失0。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：无
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### O09 · codex/industry-chain-v2

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`227f5037b73669aa490097924b273c0295698766`。
- 无登记工作树。
- 建议：历史基础；不作为继续开发基线，完成保全后可退役活动引用。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：98个路径（含历史/禁读路径名称）；允许展示路径94个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同27、当前缺失1。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/research/光模块知识体系-当前任务控制文稿.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### O10 · codex/overseas-news

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`3d6f6637f3d5afe1d8ddddb1d15aa4ca57f7e632`。
- 无登记工作树。
- 建议：旧海外基础；与当前仓库无共同历史，账本和功能需分别核对，不能直接删。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 3d6f663 产出: +0点 +0边 空格2/40 驳回0 海外季度池新增LWLG与Smartoptics
  - b98c1db 产出: +0点 +0边 空格2/40 驳回0 海外候选分层复核：Microchip晋级事件监控，Hamamatsu保留发现队列
  - bb9518f 维护: 固化海外新闻扩容交接清单
  - acb03a6 维护: 海外事件成熟阶段要求实际证据
  - 85f33b2 产出: +0点 +0边 空格2/40 驳回0 新增同源去重与订单事件
  - 856e639 产出: +0点 +0边 空格2/40 驳回0 新增5条高价值海外事件
  - e585f8a 产出: +0点 +0边 空格2/40 驳回0 发现队列接入页面
  - f6bf159 产出: +0点 +0边 空格2/40 驳回0 长尾34家公司分层收录
  - 3df1c24 产出: +0点 +0边 空格2/40 驳回0 第二批20家公司分层落库
  - 3201357 产出: +0点 +0边 空格2/40 驳回0 第二批20家公司两期晋级复核

- 两端快照差异：578个路径（含历史/禁读路径名称）；允许展示路径352个。只列前12个：
  - `.gitattributes`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
  - `calls/event_claims.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同89、当前缺失5。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/adr/0009-separate-entity-identity-from-tracking-tier.md`、`docs/handoffs/2026-08-13-kimi-overseas-news-expansion.md`、`docs/research/2026-08-15-overseas-lwlg-smartoptics.md`、`docs/research/2026-08-15-overseas-next-10.md`、`docs/research/2026-08-overseas-company-universe-candidates.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：49个路径；以下列允许路径前15项。
  - `M CONTEXT.md`
  - `M calls/README.md`
  - `M calls/SPEC.md`
  - `A calls/company_candidates.csv`
  - `A calls/company_tier_reviews.csv`
  - `A calls/entity_relationships.csv`
  - `M calls/event_claims.csv`
  - `M calls/event_evidence.csv`
  - `M calls/event_intelligence.py`
  - `M calls/events.csv`
  - `M calls/out/README.md`
  - `A calls/out/companies/adtn-adtran.md`
  - `A calls/out/companies/aixa-aixtron.md`
  - `A calls/out/companies/asmpt-asmpt.md`
  - `A calls/out/companies/axti-axt.md`
  - 其余33个允许路径未逐项展开；处置执行前须全量核对。

### O11 · codex/rescue-domain-data-20260902

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`5ec2153414a0eb08298421944c62a895c125eade`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal`。
- 建议：优先保全脏工作树；逐项核对研究候选和救援成果，不能直接删或整批晋升。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 5ec2153 维护: 保存KN008至KN010晋升依据与后续依赖候选
  - b233542 产出: +0点 +0边 空格2/41 驳回0 保存KN008至KN010领域知识晋升
  - 29cc861 维护: 增加研究图闭环 pilot

- 两端快照差异：109个路径（含历史/禁读路径名称）；允许展示路径101个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/company_candidates.csv`
  - `calls/company_tier_reviews.csv`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/entity_relationships.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同24、当前缺失14。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`contracts/question_generation_rules.yaml`、`contracts/relation_adapters.yaml`、`contracts/relation_types.yaml`、`docs/research/光模块知识体系-当前任务控制文稿.md`、`out/generated_diagnostic_questions.jsonl`、`out/relation_assertion_index.jsonl`、`out/relation_slot_states.jsonl`、`relation_assertions.yaml`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - ` M` `.gitignore`：与承接点不同。
  - ` M` `CONTEXT.md`：与承接点不同。
  - ` M` `README.md`：与承接点不同。
  - ` M` `out/知识库.html`：与承接点不同。
  - ` M` `out/知识库.md`：与承接点不同。
  - ` M` `out/研究问题树.md`：与承接点不同。
  - ` M` `scan.py`：与承接点不同。
  - ` M` `site/optical-module/pages.yaml`：与承接点不同。
  - ` M` `site/optical-module/sections/answer.html`：与承接点相同。
  - ` M` `site/optical-module/sections/audit.html`：与承接点不同。
  - ` M` `site/optical-module/sections/status.html`：与承接点不同。
  - ` M` `tests/site/test_optical_module_reader.py`：与承接点不同。
  - `??` `corpus/web/2026-08-31/semantic/eoptolink__EOLO-138HG-E-5H-XDX.html`：承接点无同路径。
  - `??` `corpus/web/2026-08-31/semantic/juniper__ORHS-2X800G-FR4-P.html`：承接点无同路径。
  - `??` `docs/plans/2026-08-optical-module-knowledge-sequence-plan.md`：承接点无同路径。
  - `??` `docs/plans/2026-08-research-operating-model-v2.md`：承接点无同路径。
  - `??` `docs/plans/2026-09-optical-module-next-round-four-options.md`：承接点无同路径。
  - `??` `docs/research-evidence-pipeline.dataflow.html`：承接点无同路径。
  - `??` `docs/research-evidence-pipeline.dataflow.json`：承接点无同路径。
  - `??` `docs/research-evidence-pipeline.dataflow.visual-check.1440x900.dark.png`：承接点无同路径。
- 全量分类计数：与承接点不同=16；与承接点相同=20；承接点无同路径=172；仅元信息，未读内容=440。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。
- 未提交路径分组（全量计数，非内容审阅）：`out/光模块知识体系-当前任务完整资料包-2026-08-26` 351；`docs/research` 190；`docs/reviews` 28；`out/光模块知识体系` 18；`tests/research` 14；`tools/research` 14；`site/optical-module` 9；`docs/plans` 3；`corpus/web` 2；`.gitignore` 1；`CONTEXT.md` 1；`README.md` 1；`out/知识库.html` 1；`out/知识库.md` 1；`out/研究问题树.md` 1；`scan.py` 1；`tests/site` 1；`docs/research-evidence-pipeline.dataflow.html` 1；`docs/research-evidence-pipeline.dataflow.json` 1；`docs/research-evidence-pipeline.dataflow.visual-check.1440x900.dark.png` 1；`docs/research-evidence-pipeline.dataflow.visual-check.1440x900.light.png` 1；`docs/research-evidence-pipeline.dataflow.visual-check.2048x1320.dark.png` 1；`docs/research-evidence-pipeline.dataflow.visual-check.2048x1320.light.png` 1；`docs/research-evidence-pipeline.dataflow.visual-check.html` 1；`docs/research-evidence-pipeline.dataflow.visual-check.json` 1；`out/光模块知识体系-当前任务完整资料包-2026-08-26.zip` 1；`out/光模块知识体系第一里程碑.html` 1；`out/技术路线审阅.html` 1。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：26个路径；以下列允许路径前15项。
  - `A contracts/question_generation_rules.yaml`
  - `A contracts/relation_adapters.yaml`
  - `A contracts/relation_types.yaml`
  - `M docs/research/knowledge-append-candidate-pq001-v1.yaml`
  - `M docs/research/knowledge-append-candidate-pq002-v1.yaml`
  - `M docs/research/knowledge-append-candidate-pq003-v1.yaml`
  - `M docs/research/光模块知识体系-当前任务控制文稿.md`
  - `A docs/reviews/2026-08-31-kimi-review-knowledge-append-pq001-v1.md`
  - `A docs/reviews/2026-08-31-kimi-review-knowledge-append-pq002-v1.md`
  - `M knowledge.yaml`
  - `A out/generated_diagnostic_questions.jsonl`
  - `A out/relation_assertion_index.jsonl`
  - `A out/relation_slot_states.jsonl`
  - `A relation_assertions.yaml`
  - `M scan.py`
  - 其余7个允许路径未逐项展开；处置执行前须全量核对。

### O12 · codex/rescue-overseas-calls-20260902

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`3420f3c74ee41d6f531ffe81ea3fa403258a0e08`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-overseas-news`。
- 建议：保全未提交专题文档、测试及生成物；账本救援增量单独复核。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 3420f3c 产出: +0点 +0边 空格2/40 驳回0 保存海外事件账本增量
  - 3d6f663 产出: +0点 +0边 空格2/40 驳回0 海外季度池新增LWLG与Smartoptics
  - b98c1db 产出: +0点 +0边 空格2/40 驳回0 海外候选分层复核：Microchip晋级事件监控，Hamamatsu保留发现队列
  - bb9518f 维护: 固化海外新闻扩容交接清单
  - acb03a6 维护: 海外事件成熟阶段要求实际证据
  - 85f33b2 产出: +0点 +0边 空格2/40 驳回0 新增同源去重与订单事件
  - 856e639 产出: +0点 +0边 空格2/40 驳回0 新增5条高价值海外事件
  - e585f8a 产出: +0点 +0边 空格2/40 驳回0 发现队列接入页面
  - f6bf159 产出: +0点 +0边 空格2/40 驳回0 长尾34家公司分层收录
  - 3df1c24 产出: +0点 +0边 空格2/40 驳回0 第二批20家公司分层落库

- 两端快照差异：571个路径（含历史/禁读路径名称）；允许展示路径346个。只列前12个：
  - `.gitattributes`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/fixtures/daily_discovery/AAOI_IR_RELEASES.json`
  - `calls/fixtures/daily_discovery/CSCO_IR_RELEASES.json`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同83、当前缺失5。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/adr/0009-separate-entity-identity-from-tracking-tier.md`、`docs/handoffs/2026-08-13-kimi-overseas-news-expansion.md`、`docs/research/2026-08-15-overseas-lwlg-smartoptics.md`、`docs/research/2026-08-15-overseas-next-10.md`、`docs/research/2026-08-overseas-company-universe-candidates.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - ` M` `calls/out/companies/aaoi-applied-optoelectronics.md`：与承接点不同。
  - ` M` `calls/out/companies/cohr-coherent.md`：与承接点不同。
  - ` M` `calls/out/companies/fn-fabrinet.md`：与承接点不同。
  - ` M` `calls/out/companies/lite-lumentum.md`：与承接点不同。
  - ` M` `calls/out/event-intelligence.json`：与承接点相同。
  - ` M` `calls/tests/test_event_intelligence.py`：与承接点不同。
  - `??` `docs/research/deep-dive/2026-08-active-watch-companies.md`：承接点无同路径。
  - `??` `docs/research/deep-dive/2026-08-core-demand-companies.md`：承接点无同路径。
  - `??` `docs/research/deep-dive/2026-08-upstream-companies.md`：承接点无同路径。
  - `??` `docs/research/deep-dive/2026-08-watch-and-candidates.md`：承接点无同路径。
  - `??` `out/光模块产业链全景图_公司能力细化版_海外情报更新_2026-08-23.html`：承接点无同路径。
- 全量分类计数：与承接点不同=5；与承接点相同=1；承接点无同路径=5；仅元信息，未读内容=1。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：49个路径；以下列允许路径前15项。
  - `M CONTEXT.md`
  - `M calls/README.md`
  - `M calls/SPEC.md`
  - `A calls/company_candidates.csv`
  - `A calls/company_tier_reviews.csv`
  - `A calls/entity_relationships.csv`
  - `M calls/event_claims.csv`
  - `M calls/event_evidence.csv`
  - `M calls/event_intelligence.py`
  - `M calls/events.csv`
  - `M calls/out/README.md`
  - `A calls/out/companies/adtn-adtran.md`
  - `A calls/out/companies/aixa-aixtron.md`
  - `A calls/out/companies/asmpt-asmpt.md`
  - `A calls/out/companies/axti-axt.md`
  - 其余33个允许路径未逐项展开；处置执行前须全量核对。

### O13 · codex/research-graph-closure-pilot

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`29cc861bf78821af1a0193bc7081de97521f7695`。
- 无登记工作树。
- 建议：仅登记元信息；按现行章程不恢复该架构，冻结保留历史，未展开内容。
- 仅登记分支及计数；内容未展开。

### O14 · codex/research-graph-closure-pilot-fix-codebuddy

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`d0ab510d97e197cfba5de6c2f18d3b5a664b12de`。
- 无登记工作树。
- 建议：仅登记元信息；修正版不构成重新准入理由，冻结保留历史，未展开内容。
- 仅登记分支及计数；内容未展开。

### O15 · codex/restore-frontend-daily-20260904

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`bacc7b523b320732db1de219d605f9fd69bd8b19`。
- 无登记工作树。
- 建议：旧恢复比较基线；作为历史快照保留，不再作为新开发入口。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：0个路径（含历史/禁读路径名称）；允许展示路径0个。只列前12个：
  - 无。
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同0、当前缺失0。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：无
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### O16 · codex/restore-optical-domain-mainline-20260902

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`5e4c6207c7b76943658620b04ce984ff715d7512`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-domain-mainline`。
- 建议：优先保全8个本地增量提交及问答文件；回补代码、原始材料、领域晋升、PQ009草案分开审核。
- 本地相对同名远端缓存的远端独有/本地独有：0 / 8；实时main例外见上文。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 5e4c620 产出: +0点 +0边 空格2/41 驳回0 更新日更恢复入口
  - 723a631 产出: +0点 +0边 空格2/41 驳回0 推进PQ009接口指标草案
  - 7a7ad9d 产出: +0点 +0边 空格2/41 驳回0 海外季度检索回补
  - 2b8358a 产出: +2点 +0边 空格2/41 驳回0 半年报与问答回补判定
  - 4cb56b7 维护: 回补八月二十三日以来问答快照
  - 33171e6 维护: 降低问答回补差异噪音
  - dfeb035 维护: 支持日更断档回补
  - af96e3e 维护: 消融重复领域关系合同

- 两端快照差异：168个路径（含历史/禁读路径名称）；允许展示路径163个。只列前12个：
  - `AGENTS.md`
  - `CLAUDE.md`
  - `README.md`
  - `RESTART-v2.md`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/README.md`
  - `calls/SPEC.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/event_claims.csv`
  - `calls/event_evidence.csv`
  - `calls/event_intelligence.py`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同104、当前缺失2。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`corpus/qa/002049/qa.jsonl`、`docs/research/光模块知识体系-当前任务控制文稿.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - ` M` `corpus/qa/003031/qa.jsonl`：与承接点不同。
- 全量分类计数：与承接点不同=1。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：98个路径；以下列允许路径前15项。
  - `M README.md`
  - `M RESTART-v2.md`
  - `M calls/README.md`
  - `M calls/SPEC.md`
  - `M calls/event_claims.csv`
  - `M calls/event_evidence.csv`
  - `M calls/event_intelligence.py`
  - `M calls/events.csv`
  - `M calls/out/README.md`
  - `M calls/out/companies/aaoi-applied-optoelectronics.md`
  - `A calls/out/companies/adtn-adtran.md`
  - `A calls/out/companies/aixa-aixtron.md`
  - `A calls/out/companies/asmpt-asmpt.md`
  - `M calls/out/companies/avgo-broadcom.md`
  - `A calls/out/companies/axti-axt.md`
  - 其余81个允许路径未逐项展开；处置执行前须全量核对。

### O17 · cursor/dev-environment-setup-2990

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`53a1b0622bce16cec0a8165646b82b1c39eaf126`。
- 无登记工作树。
- 建议：单独评估云端环境及字体修复的需要；不因独立小分支就自动丢弃。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 53a1b06 维护: 搭建云端开发环境 (.cursor/environment.json + install.sh) 并修复PDF中文字体跨平台
  - fcc87b6 Merge pull request #1 from pojoker/codex/industry-chain-v2

- 两端快照差异：649个路径（含历史/禁读路径名称）；允许展示路径419个。只列前12个：
  - `.cursor/environment.json`
  - `.cursor/install.sh`
  - `.gitattributes`
  - `.githooks/commit-msg`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `RESTART-v2.md`
  - `annual_reports/300308/annual_reports.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同18、当前缺失3。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`.cursor/environment.json`、`.cursor/install.sh`、`refs/kimi客户端任务-20260725.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：3个路径；以下列允许路径前15项。
  - `A .cursor/environment.json`
  - `A .cursor/install.sh`
  - `M make_participation_pdf.py`

### O18 · exp/pedagogical-foundation-20260905

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`d0f65159dd2d06f848529ff57003607221af1f6f`。
- 工作树：`/Users/jowang/Downloads/workflow-rehearsal-goal-control`。
- 建议：保留独立教学实验；用户决定是否吸收01B及教学叙事，候选知识另审，不整支覆盖。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - d0f6515 维护: 01B 投资者版图文口径对齐
  - ab71fd0 维护: 新增基础信息投资者导读版页面（01B）
  - 9b050db 维护: 基础知识页术语物理落地与图文互接
  - 3795889 维护: 补充PD光电流量级候选知识并修正TIA卡表述
  - e891901 维护: 基于第一性原理与边界守恒修正制造章节分工表述
  - 21c8ba0 维护: 修复 exp 改写物理硬伤并沉淀教程层写作纪律
  - 28c8fdb 维护: 基于教学工程与认知预算重构基础知识入门叙事
  - de5592d 维护: 重构基础知识页的光路叙述与制造分工

- 两端快照差异：38个路径（含历史/禁读路径名称）；允许展示路径37个。只列前12个：
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/guides/pedagogical-harness-playbook.md`
  - `docs/policies/tutorial-layer.md`
  - `docs/research/knowledge-append-candidate-photocurrent-v1.yaml`
  - `out/光模块知识体系/01-foundation.html`
  - `out/光模块知识体系/01b-foundation-investor.html`
  - `out/光模块知识体系/02-demand.html`
  - `out/光模块知识体系/03-routes.html`
  - `out/光模块知识体系/04-cases.html`
  - `out/光模块知识体系/05-companies.html`
  - `out/光模块知识体系/06-research.html`
  - `out/光模块知识体系/07-decision-dossier.html`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同19、当前缺失18。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`docs/guides/pedagogical-harness-playbook.md`、`docs/policies/tutorial-layer.md`、`docs/research/knowledge-append-candidate-photocurrent-v1.yaml`、`out/光模块知识体系/01b-foundation-investor.html`、`out/光模块知识体系/assets/figures/01b-function-chain.svg`、`out/光模块知识体系/assets/figures/02b-manufacturing-layers.svg`、`out/光模块知识体系/assets/figures/06-tx-coupling-path.svg`、`out/光模块知识体系/assets/figures/06b-tx-coupling-path.svg`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - `??` `out/光模块知识体系 2.zip`：承接点无同路径。
  - `??` `out/光模块知识体系.zip`：承接点无同路径。
- 全量分类计数：承接点无同路径=2。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：38个路径；以下列允许路径前15项。
  - `M docs/control/ACTIVE_WORKPACK.yaml`
  - `A docs/guides/pedagogical-harness-playbook.md`
  - `A docs/policies/tutorial-layer.md`
  - `A docs/research/knowledge-append-candidate-photocurrent-v1.yaml`
  - `M out/光模块知识体系/01-foundation.html`
  - `A out/光模块知识体系/01b-foundation-investor.html`
  - `M out/光模块知识体系/02-demand.html`
  - `M out/光模块知识体系/03-routes.html`
  - `M out/光模块知识体系/04-cases.html`
  - `M out/光模块知识体系/05-companies.html`
  - `M out/光模块知识体系/06-research.html`
  - `M out/光模块知识体系/07-decision-dossier.html`
  - `M out/光模块知识体系/08-concept-primer.html`
  - `A out/光模块知识体系/assets/figures/01b-function-chain.svg`
  - `M out/光模块知识体系/assets/figures/02-manufacturing-layers.svg`
  - 其余22个允许路径未逐项展开；处置执行前须全量核对。

### O19 · fix/foundation-page-rework-20260905

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`de5592d426e6520adf1ab34c227b2e585dc1cfa8`。
- 无登记工作树。
- 建议：已是教学实验祖先；跟随实验保全，可列入后续退役候选。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - de5592d 维护: 重构基础知识页的光路叙述与制造分工

- 两端快照差异：12个路径（含历史/禁读路径名称）；允许展示路径12个。只列前12个：
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `out/光模块知识体系/01-foundation.html`
  - `out/光模块知识体系/assets/figures/02-manufacturing-layers.svg`
  - `out/光模块知识体系/assets/figures/06-tx-coupling-path.svg`
  - `site/optical-module/assets/figures/02-manufacturing-layers.svg`
  - `site/optical-module/assets/figures/06-tx-coupling-path.svg`
  - `site/optical-module/sections/answer.html`
  - `site/optical-module/sections/connections.html`
  - `site/optical-module/sections/manufacturing.html`
  - `site/optical-module/sections/physical-gallery.html`
  - `site/optical-module/sections/physical.html`
  - `tests/site/test_optical_module_reader.py`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同10、当前缺失2。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`out/光模块知识体系/assets/figures/06-tx-coupling-path.svg`、`site/optical-module/assets/figures/06-tx-coupling-path.svg`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：12个路径；以下列允许路径前15项。
  - `M docs/control/ACTIVE_WORKPACK.yaml`
  - `M out/光模块知识体系/01-foundation.html`
  - `M out/光模块知识体系/assets/figures/02-manufacturing-layers.svg`
  - `A out/光模块知识体系/assets/figures/06-tx-coupling-path.svg`
  - `M site/optical-module/assets/figures/02-manufacturing-layers.svg`
  - `A site/optical-module/assets/figures/06-tx-coupling-path.svg`
  - `M site/optical-module/sections/answer.html`
  - `M site/optical-module/sections/connections.html`
  - `M site/optical-module/sections/manufacturing.html`
  - `M site/optical-module/sections/physical-gallery.html`
  - `M site/optical-module/sections/physical.html`
  - `M tests/site/test_optical_module_reader.py`

### O20 · judge/empty-cells

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`39b6136c165765bb933fce258789379528840f45`。
- 工作树：`/Users/jowang/Downloads/wr-judge`。
- 建议：旧恢复基线已有提交历史；仅保留历史用途，退役前查运行引用。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：613个路径（含历史/禁读路径名称）；允许展示路径383个。只列前12个：
  - `.gitattributes`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `RESTART-v2.md`
  - `build_detailed_capability_report.py`
  - `calls/.gitignore`
  - `calls/DAILY-DISCOVERY.md`
  - `calls/POSITIONING-SPEC.md`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同34、当前缺失1。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`refs/kimi客户端任务-20260725.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### O21 · master

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`fcc87b6b328a8c958bce7e08ca13abde253049db`。
- 无登记工作树。
- 建议：旧默认分支；不作为承接目标；默认分支调整及远端删除须另审。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - fcc87b6 Merge pull request #1 from pojoker/codex/industry-chain-v2

- 两端快照差异：646个路径（含历史/禁读路径名称）；允许展示路径416个。只列前12个：
  - `.gitattributes`
  - `.githooks/commit-msg`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `README.md`
  - `RESTART-v2.md`
  - `annual_reports/300308/annual_reports.csv`
  - `annual_reports/300308/annual_reports.json`
  - `annual_reports/600498/annual_reports.csv`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同17、当前缺失1。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`refs/kimi客户端任务-20260725.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### O22 · remote/foreign-path2

- 仓库：`/Users/jowang/Downloads/workflow-rehearsal`；所比较tip：`2e5bc9d19e7cd86fd3c5f76b438fdb5d3df60f45`。
- 无登记工作树。
- 建议：仍有独有提交，不能宣称已完全包含；只核对相关取证增量，历史保留。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 2e5bc9d 产出: +0点 +0边 驳回0 境外路径②远程取证(待本地判定闸)

- 两端快照差异：652个路径（含历史/禁读路径名称）；允许展示路径422个。只列前12个：
  - `.gitattributes`
  - `.githooks/commit-msg`
  - `.githooks/pre-commit`
  - `.gitignore`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `CONTEXT.md`
  - `FOREIGN-PATH2-FINDINGS.md`
  - `README.md`
  - `RESTART-v2.md`
  - `annual_reports/300308/annual_reports.csv`
  - `annual_reports/300308/annual_reports.json`
- 上述允许路径中该分支仍存在的文件，与当前承接点同路径比较：相同0、不同16、当前缺失1。分支删除的路径不在这三个数中；不是功能承接率。
- 当前缺失的差异文件（前8项，仅标明核对对象，不建议自动恢复）：`FOREIGN-PATH2-FINDINGS.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：1个路径；以下列允许路径前15项。
  - `A FOREIGN-PATH2-FINDINGS.md`

### N01 · codex/daily-domestic-20260905

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`d413037d029555aa62b8ad9d74b12af83787a988`。
- 工作树：`/Users/jowang/Downloads/optical-daily-domestic`。
- 建议：当前未提交5个文件均与承接基线一致；保全并查运行依赖后，优先退役工作树。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：17个路径（含历史/禁读路径名称）；允许展示路径17个。只列前12个：
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/reviews/2026-09-05-daily-reliability-codebuddy.md`
  - `docs/reviews/2026-09-05-daily-reliability-opencode.md`
  - `docs/reviews/2026-09-05-daily-reliability-pi.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - ` M` `corpus/_fetch_qa.py`：与承接点相同。
  - ` M` `domestic_daily/cli.py`：与承接点相同。
  - ` M` `domestic_daily/core.py`：与承接点相同。
  - ` M` `tests/test_domestic_daily.py`：与承接点相同。
  - `??` `docs/reviews/2026-09-05-daily-reliability-codebuddy.md`：与承接点相同。
- 全量分类计数：与承接点相同=5。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N02 · codex/daily-overseas-20260905

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`d413037d029555aa62b8ad9d74b12af83787a988`。
- 工作树：`/Users/jowang/Downloads/optical-daily-overseas`。
- 建议：当前文件已与承接基线一致；暂存区有中间态，需显式保全或放弃后退役工作树。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：17个路径（含历史/禁读路径名称）；允许展示路径17个。只列前12个：
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/reviews/2026-09-05-daily-reliability-codebuddy.md`
  - `docs/reviews/2026-09-05-daily-reliability-opencode.md`
  - `docs/reviews/2026-09-05-daily-reliability-pi.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - `MM` `calls/daily_discovery.py`：与承接点相同。
  - `MM` `calls/discovery_config.json`：与承接点相同。
  - `MM` `calls/http_discovery.py`：与承接点相同。
  - `M ` `calls/tests/test_daily_discovery.py`：与承接点相同。
  - `MM` `calls/tests/test_http_discovery.py`：与承接点相同。
  - `AM` `docs/reviews/2026-09-05-daily-reliability-opencode.md`：与承接点相同。
- 全量分类计数：与承接点相同=6。
- 暂存区与承接点不同的路径：`calls/daily_discovery.py`、`calls/discovery_config.json`、`calls/http_discovery.py`、`calls/tests/test_http_discovery.py`、`docs/reviews/2026-09-05-daily-reliability-opencode.md`。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N03 · codex/daily-report-20260905

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`d413037d029555aa62b8ad9d74b12af83787a988`。
- 工作树：`/Users/jowang/Downloads/optical-daily-report`。
- 建议：当前未提交4个文件均与承接基线一致；保全并查运行依赖后，优先退役工作树。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：17个路径（含历史/禁读路径名称）；允许展示路径17个。只列前12个：
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/reviews/2026-09-05-daily-reliability-codebuddy.md`
  - `docs/reviews/2026-09-05-daily-reliability-opencode.md`
  - `docs/reviews/2026-09-05-daily-reliability-pi.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - `M ` `daily_intelligence/cli.py`：与承接点相同。
  - `M ` `daily_intelligence/core.py`：与承接点相同。
  - `A ` `docs/reviews/2026-09-05-daily-reliability-pi.md`：与承接点相同。
  - `M ` `tests/test_daily_intelligence.py`：与承接点相同。
- 全量分类计数：与承接点相同=4。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N04 · codex/factory-agy-site-transparency-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`837fe1d94f3f65c4c68208c8b56b9c1ed219df1c`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/agy-gemini38-flash`。
- 建议：已发现对应集成及后续文案修正；保留承接版，勿重新整支合并；完成核对后退役。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 837fe1d 维护: 明确九页证据读法与不可外推边界

- 两端快照差异：75个路径（含历史/禁读路径名称）；允许展示路径75个。只列前12个：
  - `AGENTS.md`
  - `build_detailed_capability_report.py`
  - `calls/README.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/out/README.md`
  - `calls/out/companies/aaoi-applied-optoelectronics.md`
  - `calls/out/companies/adtn-adtran.md`
  - `calls/out/companies/aixa-aixtron.md`
  - `calls/out/companies/anet-arista.md`
  - `calls/out/companies/asmpt-asmpt.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：3个路径；以下列允许路径前15项。
  - `M site/optical-module/sections/audit.html`
  - `M site/optical-module/sections/status.html`
  - `M tests/site/test_optical_module_reader.py`

### N05 · codex/factory-codebuddy-capability-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`4c3862282f13dbbc447b94b5fab7a56654171065`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/codebuddy-hy4`。
- 建议：已发现对应集成及schema保留修正；保留承接版，勿重新引入worker的字段改名。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 4c38622 维护: 修正能力准入与粗粒度格展示边界

- 两端快照差异：76个路径（含历史/禁读路径名称）；允许展示路径76个。只列前12个：
  - `AGENTS.md`
  - `build_detailed_capability_report.py`
  - `calls/README.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/out/README.md`
  - `calls/out/companies/aaoi-applied-optoelectronics.md`
  - `calls/out/companies/adtn-adtran.md`
  - `calls/out/companies/aixa-aixtron.md`
  - `calls/out/companies/anet-arista.md`
  - `calls/out/companies/asmpt-asmpt.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：2个路径；以下列允许路径前15项。
  - `M build_detailed_capability_report.py`
  - `A tests/test_capability_report_semantics.py`

### N06 · codex/factory-opencode-overseas-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`e32e62dbb6a7fb93fc6e8fcbae3d9dbcd417359d`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/opencode-omen-alpha`。
- 建议：已发现对应集成及动态覆盖口径修正；保留承接版，勿恢复硬编码统计测试。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - e32e62d 维护: 海外 reader 五级覆盖与 asserted/corroborated 语义分列（仅渲染与语义层）

- 两端快照差异：75个路径（含历史/禁读路径名称）；允许展示路径75个。只列前12个：
  - `AGENTS.md`
  - `build_detailed_capability_report.py`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/out/README.md`
  - `calls/out/companies/aaoi-applied-optoelectronics.md`
  - `calls/out/companies/adtn-adtran.md`
  - `calls/out/companies/aixa-aixtron.md`
  - `calls/out/companies/anet-arista.md`
  - `calls/out/companies/asmpt-asmpt.md`
  - `calls/out/companies/avgo-broadcom.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：3个路径；以下列允许路径前15项。
  - `M calls/README.md`
  - `M calls/renderer.py`
  - `A calls/tests/test_reader_semantics.py`

### N07 · codex/factory-pi-render-boundaries-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`6d662c9f2c2c1cce3e06f483ea18581df1e8fd5a`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/pi-glm53-flash`。
- 建议：已发现对应集成及锚点/业务口径后续修正；保留承接版，勿整支覆盖。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 6d662c9 维护: WP-C 出货锚点关系边安全渲染（非URL锚说明文本、同上非独立锚、BOM边关系观察措辞、出货观察节按单位/业务范围并禁止求和排名份额）

- 两端快照差异：76个路径（含历史/禁读路径名称）；允许展示路径76个。只列前12个：
  - `AGENTS.md`
  - `build_detailed_capability_report.py`
  - `calls/README.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/out/README.md`
  - `calls/out/companies/aaoi-applied-optoelectronics.md`
  - `calls/out/companies/adtn-adtran.md`
  - `calls/out/companies/aixa-aixtron.md`
  - `calls/out/companies/anet-arista.md`
  - `calls/out/companies/asmpt-asmpt.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：2个路径；以下列允许路径前15项。
  - `M render.py`
  - `A tests/test_render_data_quality_boundaries.py`

### N08 · codex/fix-daily-reliability-20260905

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`b3e287e6ac88b0f87411bed1b13caef17e51a0b7`。
- 工作树：`/Users/jowang/Downloads/optical-module-research`。
- 建议：保留为本轮固定比较基线；远端main新提交核清前，不宣布其为最终唯一主线。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：0个路径（含历史/禁读路径名称）；允许展示路径0个。只列前12个：
  - 无。

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - ` M` `docs/control/ACTIVE_WORKPACK.yaml`：与承接点不同。
  - `??` `docs/reviews/2026-09-05-current-status.md`：承接点无同路径。
- 全量分类计数：与承接点不同=1；承接点无同路径=1。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N09 · codex/remediate-data-semantics-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`c695614ae1587168dd31d98d5eed8a9521ada94f`。
- 无登记工作树。
- 建议：提交已包含在承接基线；远端main核清并完成保全后，列入退役候选。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：18个路径（含历史/禁读路径名称）；允许展示路径18个。只列前12个：
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/plans/2026-09-05-daily-reliability-packages.md`
  - `docs/reviews/2026-09-05-daily-reliability-codebuddy.md`
  - `docs/reviews/2026-09-05-daily-reliability-opencode.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N10 · codex/review-cursor-fable51-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`c53b9bdf6d8a5146e145722744129dbd1f44d7df`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/review-cursor-fable51`。
- 建议：审阅文件与承接基线逐字一致；保全及查依赖后优先退役工作树。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：22个路径（含历史/禁读路径名称）；允许展示路径22个。只列前12个：
  - `AGENTS.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/control/PROJECT_CHARTER.md`
  - `docs/plans/2026-09-05-daily-reliability-packages.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - `A ` `docs/reviews/2026-09-04-cursor-fable-5-1-product-direction-review.md`：与承接点相同。
- 全量分类计数：与承接点相同=1。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N11 · codex/review-kimi-k3-20260904

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`c53b9bdf6d8a5146e145722744129dbd1f44d7df`。
- 工作树：`/Users/jowang/Downloads/optical-module-factory/review-kimi-k3`。
- 建议：审阅文件与承接基线逐字一致；保全及查依赖后优先退役工作树。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：22个路径（含历史/禁读路径名称）；允许展示路径22个。只列前12个：
  - `AGENTS.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/tests/test_daily_discovery.py`
  - `calls/tests/test_http_discovery.py`
  - `corpus/_fetch_qa.py`
  - `daily_intelligence/cli.py`
  - `daily_intelligence/core.py`
  - `docs/control/ACTIVE_WORKPACK.yaml`
  - `docs/control/PROJECT_CHARTER.md`
  - `docs/plans/2026-09-05-daily-reliability-packages.md`

- 未提交内容（工作区最终文件；与当前承接点逐字比较）：

  - `A ` `docs/reviews/2026-09-04-kimi-k3-product-direction-review.md`：与承接点相同。
- 全量分类计数：与承接点相同=1。
- 暂存区与承接点不同的路径：未发现（只核对允许读取且有暂存变更的路径）。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

### N12 · main

- 仓库：`/Users/jowang/Downloads/optical-module-research`；所比较tip：`7ff3b25cfd0ff3b137ec55471c7ad33dd5060510`。
- 无登记工作树。
- 建议：本地及缓存均与实时远端不同（祖先关系未核实）；先核清b2ba845，暂不决定最终基线和合并方向。
- 相对内部比较基线的独有提交（最多10条；标题是提交者描述，不是审阅结论）：

  - 无。

- 两端快照差异：77个路径（含历史/禁读路径名称）；允许展示路径77个。只列前12个：
  - `AGENTS.md`
  - `build_detailed_capability_report.py`
  - `calls/README.md`
  - `calls/daily_discovery.py`
  - `calls/discovery_config.json`
  - `calls/http_discovery.py`
  - `calls/out/README.md`
  - `calls/out/companies/aaoi-applied-optoelectronics.md`
  - `calls/out/companies/adtn-adtran.md`
  - `calls/out/companies/aixa-aixtron.md`
  - `calls/out/companies/anet-arista.md`
  - `calls/out/companies/asmpt-asmpt.md`
- 未发现登记工作树的未提交文件；不等于无外部运行依赖。


- 该分支自共同祖先起的净改动（不是与较新基线的反向差异）：0个路径；以下列允许路径前15项。
  - 无允许路径净改动。

## 复核方式与本轮变更

证据命令：`git for-each-ref`、`git ls-remote --heads origin`、`git worktree list --porcelain`、`git status --porcelain=v1 -z --untracked-files=all`、`git rev-list --left-right --count BASE...TIP`、`git log BASE..TIP`、`git diff --name-only BASE TIP`、`git ls-tree -r TIP`、`git hash-object -- PATH`、`git rev-parse :PATH`。hash-object未使用-w，不写对象。

本轮仅修改ACTIVE_WORKPACK.yaml和本报告；原有2026-09-05-current-status.md未改。canonical与生成物未改，未做提交。所有处置均待审，任何领域问题是否完成不在本表判定范围。
