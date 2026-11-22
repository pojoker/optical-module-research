# Step 2 归档遗珠打捞、龙头工艺扩抽与关系时间线贯通验收报告（2026-11-21）

## 结论先行

工作包 `OPTICAL-STEP2-ARCHIVE-SALVAGE-20261121` 授权范围内的历史资产清洗收编、15 家海内外核心龙头工艺扩抽、全量关系时间线拆解贯通、确定性校验门扩展及派生层全量重算均已落盘，并经独立程序化核验通过。全部 6 道机器门（`scan --selftest` 119/119、`scan --check` ①–⑭ 全绿、`render --verify`、`participation --check`、`-m calls check`、专项 `pytest` 77 项通过）与全仓活跃测试集（479 项通过、0 项失败）退出码均为 `0`。三份构建脚本二次重跑对全部 37 个目标输出文件呈字节级幂等（SHA-256 零漂移），`archive/` 下受 git 追踪文件零删改，`corpus/_frozen.csv`（463 家）与 `points.csv` 的 `P031`/`P209` 保持原样。

按照 [AGENTS.md](file:///Users/jowang/Downloads/optical-module-research/AGENTS.md) 第 4 节与第 7 节边界，需要明确区分机器验证与领域裁决：本轮机器门全绿只证明数据结构闭合、算术对账吻合、引语逐字命中本地原文以及负向剔除零泄漏，不代表领域研究问题自动结案。台账中的工艺摘录、双侧对账与验真闹钟仍属分层证据材料，任何向根级核心结论的进一步晋升仍须人工复核并由用户单列授权。

## 本轮落盘的核心资产与加固改动

### 1. 2023 年报去重核验、实体主数据与海关四维底表（Shard A）

通过幂等脚本 [build_customs_and_entities.py](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/build_customs_and_entities.py) 整理落盘了四块基础数据：

- **语料去重与全文旁车**：[corpus/annual-2023](file:///Users/jowang/Downloads/optical-module-research/corpus/annual-2023) 收纳 34 份 2023 年报 PDF；对 `archive/demo/data/` 全部 30 份 PDF 逐份重算 SHA-256，30/30 在本地 `corpus/{annual,annual-2024,annual-2023}` 命中同哈希原件（清单见 [demo-pdf-dedupe-manifest.json](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/demo-pdf-dedupe-manifest.json)），同时将 11 份 `_v16_txt_grok` 全文对齐补齐为 `corpus/legacy-input/v16/` 下对应 PDF 的 `.pdf.txt` 旁车文件。
- **真值断言与悬空路径清理**：[truth_regression_assertions.json](file:///Users/jowang/Downloads/optical-module-research/corpus/salvaged/truth_regression_assertions.json) 将 `truth.json` 全部 16 条基准断言（`T01–T16`）映射到当前根级 [edges.csv](file:///Users/jowang/Downloads/optical-module-research/edges.csv) 实时字段核验，16/16 全部吻合；[points.csv](file:///Users/jowang/Downloads/optical-module-research/points.csv) 中 `P013`、`P025`、`P026`、`P058` 原先指向归档目录的旧标记已全部改写为真实本地 `corpus/` 路径与内容台账锚点。
- **169 节点与夹层登记**：[entity_nodes.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/salvaged/entity_nodes.csv) 与 [entity-registry.yaml](file:///Users/jowang/Downloads/optical-module-research/refs/entity-registry.yaml) 吸收全部 169 个节点及 `PINEWAVE`、`浙江粮油`、`顺丰速运`、`金信诺`、`等离子体所`、`索恩格` 6 个历史遗漏主体，显式标注 12 个贸易/代理/结算夹层主体，并记录联讯仪器（`688808`，2026-04-24 科创板上市）、索尔思（东山精密 `002384` 并表）与波若威（台股上柜 `3163`）最新身份状态。
- **海关 HS `85177950` 四维底表与宏观证据**：[corpus/customs/](file:///Users/jowang/Downloads/optical-module-research/corpus/customs/README.md) 落地月度（30 行）、伙伴（2881 行，已清除原表 61 处引号内换行符）、省份（2246 行）、贸易方式（731 行）四张表及两张税号口径对照表；`202501–202606` 共 18 个月的美元与重量逐月汇总与月度主表误差为 `0.000%`。[macro_evidence.csv](file:///Users/jowang/Downloads/optical-module-research/macro_evidence.csv) 新增 `MC033`（2025 全年 `$5,189,328,259` = 51.89 亿美元）、`MC034`（2026H1 `$3,427,389,890` = 34.27 亿美元：马来西亚 41.80%、中国台湾 14.34%、泰国 9.00%、直接对美由 16.64% 降至 6.87%）与 `MC035`（Yole CPO Scale-Up 54 亿/121% 自洽口径与新闻稿 137% 跨表拼接核查）。

### 2. 20 家企业 597 条客观工艺内容台账与 `KN007` 毛利率实证（Shard B）

通过幂等脚本 [build_content_ledger.py](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/build_content_ledger.py) 生成 [content_ledger.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/content_ledger/content_ledger.csv)（共 597 条，物理行数 598 行，零内嵌换行）：

- **既有 5 家清洗收编（377 条，`batch=v1_salvage`）**：完整收纳仕佳光子（99）、源杰科技（108）、长光华芯（63）、太辰光（24）、猎奇智能（83），将早期样品旧分类统一映射至冻结五分枚举（`工序步骤 | 技术参数 | 产品构成 | 代际事件 | 设备-工序能力`），并剥离 `C11` 句尾具名客户交付短语以严守“内容台账不混入商业订单主张”的双闸红线。
- **海内外 15 家核心龙头扩抽（220 条，`batch=step2_expansion`）**：涵盖招股书/新股技术富矿 4 家（联讯仪器 16、炬光科技 15、长进光子 14、盛合晶微 14）、国内模块/器件/设备龙头 7 家（中际旭创 15、新易盛 14、天孚通信 15、光迅科技 15、华工科技 14、罗博特科/ficonTEC 16、东山精密/索尔思 14）以及海外 10-K 龙头 4 家（Coherent 15、Lumentum 15、Fabrinet 14、AAOI 14，保留英文原句引语并配中文原子提炼句）。独立测试直接读取本地源文本重跑去空白子串匹配，220/220 条（`100.0%`）逐字命中原文；39 条企业自评或单方援引排名陈述全部隔离标记为 `stance=issuer_self`。
- **`KN007` 老化设备毛利率实证增补**：经核对猎奇智能招股书分产品毛利率表（`1-1-228` 页），在 [knowledge.yaml](file:///Users/jowang/Downloads/optical-module-research/knowledge.yaml) 的 `KN007` 补入模块老化测试设备毛利率由 2023 年 `37.45%`、2024 年 `50.65%` 下滑至 2025 年 `12.55%`（对比同期贴片设备 `59.28%–60.51%`、耦合设备 `53.99%–60.45%`）的一手实证锚点，并已重算同步至 [知识库.md](file:///Users/jowang/Downloads/optical-module-research/out/知识库.md)。

### 3. 全量关系时间线、负向剔除记忆与 `#005` 解匿反面判例（Shard C）

通过幂等脚本 [build_timelines_and_refs.py](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/build_timelines_and_refs.py) 构建了关系层四张台账并原地更新判例库：

- **全量关系时间线贯通**：[relationship_timeline.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/relationship_timeline.csv) 共 446 行（204 对有向关系），236/236 完整拆解覆盖 `E001–E236`（含 `E100–E236` 多期打包边拆出的 290 行单期序列），并合入设备观察池 25 行（14 行原位关联免重计 + 11 行新增补充观测，含 `FT-OB-20241213` 在手订单 `4800 万欧元` 快照）。表中显式隔离 `confirmed_ended`（NeoPhotonics→华为 2021 归零）、`procedural_intermediary`（新易盛→浙江粮油出口代理）与 `bad_debt_frozen`（Kaiam→博创科技单项 100% 坏账冻结）三类特殊状态，将“跌出前五 / `<10%`”严格标为右截尾 `censored`，同时预留 `event_date`、`source_channel`、`daily_ref_id` 列并在 [corpus/relationships/README.md](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/README.md) 写明 Step 3 日更脉冲事件插入契约。
- **边负记忆、双侧对账与验真闹钟**：[edge_negative_cuts.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/edge_negative_cuts.csv) 收录 74 条剔除记录（长飞系子公司合并承载、华工非光链/坏账、非供货股权/担保、非光链房产出租），经与当前活跃 `edges.csv` 双向比对为 `0` 泄漏；[counterparty_audit.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/counterparty_audit.csv) 收录 15 对跨主体对账（含天孚→Fabrinet 弱一致、Fabrinet↔Lumentum 判例#004 B 级终态、光迅↔烽火服务费逐位确认及商品含税并表还原后差额缩至 `~4.9%`）；[sellside_watch_alarms.csv](file:///Users/jowang/Downloads/optical-module-research/corpus/relationships/sellside_watch_alarms.csv) 收录 7 条验真闹钟（更新 `W03` 联讯科创板上市与 `W06` Yole 口径结案，保留 5 条 2026–2027 活跃监测）。
- **解匿判例库更新**：[解匿判例库.md](file:///Users/jowang/Downloads/optical-module-research/refs/解匿判例库.md) 新增 `## 判例#005（已推翻反面教材）“旭创双流”假设为何不成立【RT-011 证伪留档】`，用 2026-06 海关三口径精确复算数（全国对马 `$260.431M`、江苏注册主体 `$221.643M`、全国进料加工 `$222.295M`）记录省份、贸易方式与单一企业混同的证伪过程，并为 `#004` 与 `#006` 补入定量边界与克制红线；`refs/` 目录严格保持 8 个文件未超限。

### 4. 校验器机器门加固与 Step 2 回归测试（Verifier）

在 [scan.py](file:///Users/jowang/Downloads/optical-module-research/scan.py) 与 [test_step2_archive_salvage.py](file:///Users/jowang/Downloads/optical-module-research/tests/test_step2_archive_salvage.py) 中新增了确定性防回退机制：

- 扩展 `_CORPUS_PATH_RE` 支持 `annual-2023`、`customs`、`content_ledger`、`relationships`、`salvaged` 子目录本地锚点核验（保持 `annual-2023`/`annual-2024` 排在 `annual` 之前）。
- 新增三个纯函数并接入 `invariants()`：`_check_customs_tables()`（不变量⑨扩展：拦截字段内/引号内换行符、重复主键及 18 个月月度美元对账偏差 `>=0.01%`）、`_check_content_ledger()`（不变量⑧扩展：拦截 `cid` 重复、五分 `fact_type` / 三分 `stance` 越界、非法叶格、空引语与缺失本地源文件）、`_check_relationship_tables()`（不变量②扩展：拦截重复 `timeline_id`、悬空 `source_edge_ids`、非法 `source_channel`、不平衡括号/尾标点半截截断及 74 对负向关系向活跃 `edges.csv` 泄漏）。`scan.py --selftest` 由 90 例扩充至 **119 例**且全部通过。

## 机器门与独立核验实测结果

| 校验项 | 结果 | 实测关键指标 |
| --- | --- | --- |
| `scan.py --selftest` | 通过（exit 0） | 合计 119 用例，通过 119，失败 0（原 90 例保留 + 新增 29 例） |
| `scan.py --check` | 通过（exit 0） | 最新语料距今 97 天，宇宙内缺席年报 0 家，不变量 ①–⑭ 全绿 |
| `render.py --verify` | 通过（exit 0） | 两次临时重建一致（`out/` 非 canonical） |
| `participation.py --check` | 通过（exit 0） | 全绿，宇宙 463，覆盖 463，确认 90，待确认 15 |
| `-m calls check` | 通过（exit 0） | 39 公司 / 166 信源 / 70 主张 / 21 主题 / 34 雷达事件引用闭合 |
| `pytest`（Step 1 + Step 2 + 能力报表） | 通过（exit 0） | `77 passed, 56 subtests passed` |
| `pytest`（全仓活跃测试集） | 通过（exit 0） | `479 passed, 1 deselected, 146 subtests passed`（仅排除写路径外旧 `OM-PHYS-001` ID 断言） |
| 三份构建脚本幂等重跑 | 通过 | 37 个目标输出文件二次重跑前后 SHA-256 零漂移 |
| 边界、编码与基线保护 | 通过 | `archive/` git 追踪文件 0 改动；`edges.csv` 与 `corpus/_frozen.csv` 哈希未变；`P031`/`P209` 未变；`refs/` 保持 8 文件；外部 `Workbuddy` 目录零触碰；无 `git commit` |

详细结构化核验数据见 [verification-summary.json](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/verification-summary.json)，重算生成的细化版全景图见 [光模块产业链全景图_公司能力细化版.html](file:///Users/jowang/Downloads/optical-module-research/out/step2-archive-salvage-20261121/光模块产业链全景图_公司能力细化版.html)。

## 机器门的边界声明（遵守 `AGENTS.md` §4 / §7）

上述 6 道机器门、479 项自动化测试与引语子串复核通过，只保证**台账结构合法、跨表算术对账闭合、引语在本地原文逐字存在、负向剔除对未混入活跃边表**。机器校验不能判断一条工艺陈述在产业竞争中的真实权重，不代表研究问题树上的问题已经结案，也不自动将内容台账或时间线中的候选观测晋升为根级主干定论。领域事实采信、竞争格局判断与后续晋升仍须人工复核并获用户明确授权。

## 留待用户决定的事项

1. **是否启动 Step 3（2026 年 9–11 月 Daily 高频情报增量并库）**：`relationship_timeline.csv` 已就绪 `daily_ir | daily_qa | daily_announcement` 挂接列与幂等写入契约（含罗博特科×NVIDIA `2026-11-16` 互动易确认量产订单交付、Tower×中际旭创 `2026-11-03` NPO 合作等高价值增量），请确认是否授权开展第三步并库。
2. **是否单列授权 `v6` 宇宙对称扩容**：联讯仪器（`688808`）已于 2026-04-24 在科创板上市（`entity_nodes.csv` 与 `W03` 已记录最新事实，但根级 `points.csv` 的 `P061` 受不扩充 `corpus/_frozen.csv` 463 家分母约束暂挂 `[待v6扩容同步]`）。请决定是否单列授权启动 `v6` 宇宙扩容，将联讯仪器、云南锗业、科瑞技术、微见智能、镭神技术等对称纳入 `_frozen.csv` 并同步根级上市标签。
3. **内容台账与时间线材料的后续晋升范围**：目前 `corpus/content_ledger/`（597 条）与 `corpus/relationships/`（446 条时序行）作为有锚证据台账层沉淀在 `corpus/` 下；若需从中遴选关键工艺或供应链演变结论写入根级 `knowledge.yaml`（新增 `KN###` 或 `WHY###`），请指定拟复核与晋升的专题范围。
4. **遗留旧测试清理与 Git 提交**：允许写路径外的 `tests/research/test_question_completion_semantics.py:92` 仍硬编码早期工作包编号 `OM-PHYS-001`；请确认是否授权修正该测试并配置 `pytest` 忽略 `out/` 历史归档包，以及是否对 Step 1 + Step 2 经核验的工作区改动执行 `git commit`。
