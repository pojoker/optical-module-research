# Step 1 账本修复与确定性校验门加固验收报告（2026-11-21）

## 结论先行

工作包 `OPTICAL-STEP1-LEDGER-AND-GATES-20261121` 授权范围内的核心账本修复、解析代码缺陷修复、确定性校验门加固以及派生视图重算已全部完成，并经独立脚本核验确认达标。核心 5 道 CLI 机器门全部退出码为 0，Step 1 新增与修改的 64 项回归测试（含 28 项子测试）全部通过，修复脚本 `remediate_ledgers.py` 二次重跑呈完全幂等（0 处改动、`git diff` SHA-256 零漂移）。

同时需要如实说明两项约束与遗留情况。第一，在全仓 `pytest` 中暴露出两处**非 Step 1 引入的既有问题**：仓库未配置 `pytest.ini`，裸跑 `pytest` 会误扫 `out/` 下的历史打包副本导致收集报错；排除 `out/` 与 `archive/` 后，467 项测试通过 466 项（含 118 项子测试），唯一失败项是 `tests/research/test_question_completion_semantics.py` 第 92 行仍硬编码旧工作包编号 `OM-PHYS-001`。由于该测试文件不在本次 `allowed_write_paths` 内，按 `AGENTS.md` §3 纪律未越权改写，留待用户决定处理方式。第二，因 Claude 5.5 全档额度仅剩 1%（预计 2026-11-27 15:59 UTC 重置），本次终验由 `gemini-4-neon-high` 执行；如需坚持 Claude Opus 独立视角复签，可在额度重置后重跑。

## 本轮修掉了哪些硬伤

本轮通过确定性脚本 [remediate_ledgers.py](file:///Users/jowang/Downloads/optical-module-research/out/step1-ledger-remediation-20261121/remediate_ledgers.py) 完成了 9 份账本共 174 处有审计留痕的修改（逐条记录见 [ledger-changes.json](file:///Users/jowang/Downloads/optical-module-research/out/step1-ledger-remediation-20261121/ledger-changes.json)），并同步修复了 3 份核心 Python 脚本的解析与拦截漏洞。

### 1. 出货与算术口径（`shipments.csv`，51 处）

- **修正 1000 倍 ASP 错算**：`SE056`（意华股份 2024）原先漏乘 `千只` 倍率导致单价误写成 661.2 元/只，现更正为 `隐含混合ASP≈0.66元/只(即661.2元/千只;2024连接器全口径量价同表)`，并将收入出处由分产品表更正为年报第 644 行分行业表连接器全口径。
- **区分产能利用率与销量/产能比**：全表不再把“销量 ÷ 产能”混称为利用率。`SE001`（中际旭创 2025）改为 `产量2,376万只≤产能2,806万只(产能利用率84.7%;销量/产能比75.2%;产销率88.8%)`，`SE010`（光库科技 2025）按产量 5,169,575 件与产能 5,200,000 件核算为真实利用率 `99.4%`，`SE016`（剑桥科技 2025）产销率舍入由 101.3% 修正为 `101.2%`。
- **清零科学计数法、错配单位与错标 `同比反算`**：8 行科学计数法全部按收入 ÷（出货量 × 单位倍率）重算为普通数字；硬编码的 `元/件` 按实际单位列修正为 `元/个`、`元/台`、`元/片` 等，全表 44 条有 ASP 行复算偏差均低于 5%；16 行标有 `同比反算` 且为 B 级的记录中，15 行经 2024 年报原文核实为直接披露绝对值而去掉误标、保留 B 级，真正由同比反算的 `SE089` 已降为 C 级。

### 2. 关系截断、错挂与重复实体（`edges.csv` 24 处、`points.csv` 32 处、`triage.csv` 9 处、`corpus/_restart_watchlist.csv` 7 处）

- **恢复截断与补正错挂**：`edges.csv` 中 11 处不平衡括号与尾标点截断全部按 `archive/output/edges.csv` 及招股书原文恢复（现为 0 处）；`E044`（中际旭创 → PINEWAVE）补齐 `43378 万美元` 并注记人民币 `3,096,780,769.22 元`；`E165`/`E232` 由在研点 `P026` 改挂量产点 `P156`；`E137`/`E141` 指向合并后的 `P037`。
- **清理重复点、错锚与陈旧标签**：`points.csv` 由 271 行合并至 269 行（`P036` 并入 `P037`，`P204` 并入 `P055`），同时原样保留了 2026-11-10 的 `P031`（景旺电子）与 `P209`（华工科技）更新；`P026`（太辰光 D8）由量产改回 `在建`；`P084`（徕木股份）撤销误贴的深南电路年报链接并改挂徕木 2025 年报 `1225206931.PDF`；`P264`/`P265`（波若威）更正为 `台股`；`P061`（联讯仪器）引语更新至 2026-08-27 半年报与 2026-01-07 申报稿，因 Step 1 不扩充 `_frozen.csv` 分母，上市标签暂保 `未上市私企` 并加注 `[待v6扩容同步]`（注明其已于 2026-04-24 登陆科创板 `688808`）。
- **去重与观察表对齐**：`triage.csv` 清理 2 条重复 `hit_id`（571 → 569 行）；`corpus/_restart_watchlist.csv` 修正非法格位。

### 3. 宏观证据、知识条目与结构配置（`macro_evidence.csv` 34 处、`knowledge.yaml` 7 处、`tree.yaml` 9 处、`refs/entity-registry.yaml` 1 块）

- **宏观与知识口径校准**：`macro_evidence.csv` 增至 32 行（新增 `MC032`），清理 9 条畸形雪球带认证前缀链接与百度搜索占位链接，修正 `MC001`/`MC002`/`MC011` 等级与一手锚点。`knowledge.yaml` 渲染全部 10 条 `KN001`–`KN010` 到 [知识库.md](file:///Users/jowang/Downloads/optical-module-research/out/知识库.md)：`KN001` 更正为 `创业板IPO在审`；`KN007` 明确拆分三个不可互换的精度物理量（国产厂商最小运动增量 `50nm`、分辨率猎奇 `10nm` vs ficonTEC `5nm`、重复定位精度 `±50nm` vs `±20nm`）并撤回跨口径互证。
- **YAML 合法性与分母同步**：`tree.yaml` 的 `universe.count` 由 461 同步至 463（与 `corpus/_frozen.csv` 一致），修复 6 条流式值逗号解析缺陷；`refs/entity-registry.yaml` 修复结构并通过 `yaml.safe_load`，`refs/` 目录保持 8 个文件未超限。

### 4. 代码缺陷修复与机器门加固（`participation.py`、`build_detailed_capability_report.py`、`scan.py`）

- **公司名消歧与结构化读取**：`participation.py` 补齐别名与无歧义去括号/双向子串匹配，使 [参与识别.csv](file:///Users/jowang/Downloads/optical-module-research/out/参与识别.csv) 463 家宇宙中已确认参与公司由 89 家恢复为 **90 家**（`汇聚科技(Huiju Technology)`、`江苏南大光电材料股份有限公司` 不再静默丢失）。`build_detailed_capability_report.py` 改用 `yaml.safe_load` 解析 `tree.yaml` 并调整 `stage_detail()` 优先级，使 [capability_details.csv](file:///Users/jowang/Downloads/optical-module-research/capability_details.csv) 增至 183 行且 `技术路线 == '未标'` 由 38 行降为 **0 行**，正确包含汇聚科技 `D9`、南大光电 `M3`（`1225087469.PDF`）、东田微 `D7`、紫光国微 `C7`，并排除改为在建的太辰光 `D8`。
- **校验门加固**：`scan.py --selftest` 用例由 53 条增至 **90 条**（全部通过），新增隐含 ASP 算术与单位匹配、科学计数法拦截、同比反算不得标 B、利用率口径校验、YAML 合法性与分母同步、`triage` 去重、`edges` 截断检测、`macro` URL 校验及异司共锚检查。

## 机器门与独立审计实测结果

| 校验项 | 结果 | 关键实测输出 |
| --- | --- | --- |
| `scan.py --selftest` | 通过（exit 0） | 合计 90 用例，通过 90，失败 0 |
| `scan.py --check` | 通过（exit 0） | 最新语料距今 97 天，缺席年报 0 家，不变量 ①–⑭ 全绿 |
| `render.py --verify` | 通过（exit 0） | 两次临时重建一致（`out/` 非 canonical） |
| `participation.py --check` | 通过（exit 0） | 全绿，宇宙 463，覆盖 463，确认 90，待确认 15 |
| `-m calls check` | 通过（exit 0） | 39 公司 / 166 信源 / 70 主张 / 21 主题 / 34 雷达事件闭合 |
| `pytest`（Step 1 专项） | 通过（exit 0） | `tests/test_step1_ledger_gates.py` + `tests/test_capability_report_semantics.py`：64 passed, 28 subtests passed |
| `pytest`（全仓活跃测试） | 1 项遗留失败（exit 1） | `--ignore=tests/site --ignore=out --ignore=archive`：466 passed, 118 subtests passed, 1 failed（仅旧 `OM-PHYS-001` ID 断言） |
| `remediate_ledgers.py` 幂等性 | 通过 | 重跑输出 `change_count: 0`，`git diff` 与 `ledger-changes.json` SHA-256 完全不变 |
| 写路径与工作区纪律 | 通过 | 本轮改动 100% 落在 `allowed_write_paths` 内；无 `git commit`；根目录白名单无新增；`refs/` 保持 8 文件 |

## 机器门的边界声明（遵循 `AGENTS.md` §4）

上述 5 道核心 CLI 门与 466 项自动化测试通过，仅说明本仓库的**数据结构、算术关系、链接/路径格式、编码规范与主键去重已经闭合**，并不意味着光模块领域研究问题已经完成，也不能替代人工对领域事实、竞争格局或投资判断的最终复核。账本中标注的 `生产中`、`在建`、`待确认` 与 `尚未发现已过闸证据` 属于分层证据状态，研究问题树上的 `KN/WHY` 挂载仅表示已有材料，不构成问题结案或 canonical 晋升授权。

## 留待用户决定的事项

1. **`v6` 宇宙扩容与联讯仪器标签同步**：联讯仪器已于 2026-04-24 登陆科创板（`688808`），本轮受不扩充 `corpus/_frozen.csv` 分母的边界约束，暂将 `P061` 保持为 `未上市私企` 并标记 `[待v6扩容同步]`。是否授权启动 `v6` 宇宙扩容，将联讯仪器、云南锗业、科瑞技术、微见智能、镭神技术等按对称规则补录入 `_frozen.csv` 并同步切换标签。
2. **修复历史遗留 `pytest` 阻塞项**：是否授权修改 `tests/research/test_question_completion_semantics.py` 第 92 行（将硬编码的旧工作包编号 `OM-PHYS-001` 改为校验非空或当前工作包结构），并在仓库配置 `pytest` 忽略 `out/` 历史打包目录，使裸跑 `pytest` 恢复全绿。
3. **后续阶段推进与提交策略**：是否继续执行 Step 2（`archive/` 历史数据资产成批打捞）与 Step 3（9–11 月 Daily 情报增量并库），以及是否将当前工作区改动按模块整理并执行 `git commit`（本轮按要求未提交）。
4. **Claude Opus 独立复签需求**：如流程上必须保留 Claude Opus 5.5 模型的独立验收签名，请在 2026-11-27 额度重置后重跑独立验收脚本。
