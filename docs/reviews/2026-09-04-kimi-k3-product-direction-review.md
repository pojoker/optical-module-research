# Kimi K3 独立复核：数据语义修复集成与产品方向

> 复核者：Kimi K3（领域语义与产品方向）
> 日期：2026-09-04
> 固定基线：`7ff3b25cfd0ff3b13fa834a0d775ae2879195`
> 复核对象：集成 HEAD `c53b9bd`（分支 `codex/review-kimi-k3-20260904`，worktree `review-kimi-k3`）
> 输入：Kimi 语义审计、Cursor 契约审计、外包计划、Codex 集成审核与产品方向报告、7ff3b25..c53b9bd 全量 diff 与生成物
>
> **独立性声明**：本报告完成前未读取 Cursor Fable 5.1 复核报告（复核时该文件尚不存在）；未读取 `archive/**`、closure/状态机材料、旧分支轨迹与任何代理全量日志。
>
> **写入边界**：本文件是唯一写入产出。未修改 canonical、代码、测试或生成物。

---

## 1. 总体判定

**接受** `c53b9bd` 作为本地候选版本，**接受**产品方向报告作为下一阶段基准，但附两项保留：

1. 两条工作包宣称的"读者可见"交付物（能力明细表述、出货量/锚点/关系边页面边界）只到达**生成器、calls/out 与九页研究页**，未到达在库跟踪的 `out/全景.md` 与能力明细 PDF/HTML——因为这两个路径不在工作包允许写入列表内。交付物口径与允许写入路径自相矛盾，需用户裁决（见 F1）。
2. 本复核 worktree 缺失 `corpus/annual*`，`scan.py --check` 与 `participation.py --check` 无法在此复验；Codex 报告的"全绿"只能在完整仓库成立，本复核未能独立确认（见 F2）。

事实/派生/候选/UNKNOWN 分列在站点与 calls 渲染层均已落实；产品方向报告未引入任何架构（architecture_budget 全空被遵守），其"三稳定边界 + 垂直切片优先"的判断与宪章一致。

## 2. Findings（按严重度）

### F1【中】两条读者交付物未到达在库跟踪页面；Codex"已改善的读者行为"表述超出实际读者可见范围

证据（记录级）：

- `render.py` 的 WP-C 修复（`_fmt_anchor`、`_shipments_section`、关系观察措辞）存在于生成器与 `tests/test_render_data_quality_boundaries.py`（7/7 通过），但在库跟踪的 `out/全景.md` **未重建**：仍含假链接 `[锚](有锚；披露方产品列…)`（如第 33、63、64、68–73 行）、旧措辞 `**（已证2边）**`/`骨架外已证流向`（第 511–602 行），且无"出货观察"节。
- `build_detailed_capability_report.py` 的 WP-A 修复（准入路径抽取、粗粒度格边界）同样只在生成器；`output/pdf/光模块产业链公司能力明细.pdf` 与合并 HTML 未重建（diff 中无变化），在库 PDF 读者看到的仍是"证据等级：判定闸-生产中（过程备注）"。
- 根因：`out/全景.md` / `output/pdf/**` 不在工作包 `allowed_write_paths`（仅 `out/光模块知识体系/**`、`calls/out/**`）。Codex 守住写入纪律是正确的；但工作包 `reader_visible_deliverables` 第 1、3 条与允许写入路径不匹配——这两条交付物按当前授权**不可能**完整交付。
- Codex 集成审核"已改善的读者行为"六条中，能力卡准入依据、出货观察面、非直链锚、edges 措辞四条对 `全景.md`/PDF 读者不成立，仅对生成器与重建产物成立。

影响：任何直接打开在库 `out/全景.md` 的读者仍暴露于审计确认的假链接与"已证边"越级措辞；对外若表述"读者页面已修复"将构成过度主张。

建议：用户二选一——(a) 新授权重建 `out/全景.*` 与能力明细 PDF/HTML；或 (b) 明确把本工作包交付口径改为"仅生成器 + calls/out + 九页"，并在 Codex 报告中收窄"已改善的读者行为"的表述范围。

### F2【中】机器门在本复核 worktree 不可复验；`render.py --verify` 不覆盖在库 out/ 一致性

证据：

- 本 worktree 无 `corpus/annual*`。`scan.py --check` 在不变量⑧失败（KN003/KN005/KN008 等证据文件不存在），exit=1。
- `participation.py --check` 失败：临时重建得"年报已覆盖 0 家"（vs 在库 463），`out/参与识别.{csv,md,html}` 与重生成不一致，exit=1。差异由 corpus 缺失驱动（覆盖统计与引语提取依赖 corpus 文件），非集成错误。
- `render.py --verify` 只比较两次临时重建的确定性，**不比较在库 `out/`**；因此 F1 的 `全景.md` 陈旧不触发任何机器门。`out/问题队列.md` 页眉"勿手改（--verify 会拒绝）"的措辞超过 `--verify` 的实际保证——此为既有问题，非本 diff 引入，但与 F1 叠加后构成真实盲区。

影响：复核者无法独立复验 Codex 报告的 scan/participation 全绿结论；且即使未来在完整仓库，render 侧在库产物陈旧也不会被任何门发现。

建议：流程裁决项——是否让 render 侧也加入"在库产物与重生成一致"校验（类似 `participation.py --check`），提交用户决定，不在本工作包实施。

### F3【低】九页研究页一处偏强措辞；零 claim 公司卡行为变化未注明

- `site/optical-module/sections/audit.html`："清晰揭示不同损耗、热密度、通道数与故障域约束下的 Pareto 权衡与反转条件"——"清晰揭示"对"当前能回答什么"略强，这些内容是派生层解释而非已裁决事实；同页其余边界措辞（四大不可外推、四层读法、scope-lock）严谨准确。
- WP-B 渲染器现为全部 39 家 enabled 公司生成公司卡（此前按内容存在性门控仅 14 张，见 Kimi 审计 H3 反例）。零 claim 公司卡显式标 0/4、0 条陈述，不构成过度主张，且透明性更好；但这是读者可见的行为变化，Codex 报告与 calls/README 均未注明，建议补一句说明。

### F4【低】新增测试的运行入口脆弱

- `tests/site/test_optical_module_reader.py` 在默认 pytest 下因顶层 `site/` 目录同名冲突 collection 失败，需 `--import-mode=importlib`（18/18 通过）。
- `tests/` 无 `__init__.py`，`python -m unittest tests.test_capability_report_semantics` 失败，须直接执行文件（20/20 通过）。
- Codex 报告给出通过计数但未记录运行命令；后来者用默认命令会误判为回归。建议在测试文件 docstring 或 README 记录运行方式。

## 3. 确认成立的项（抽查证据）

- **四级分列落实**：`status.html` 改为 Fact/Derived/Candidate/UNKNOWN 四层并附读法；`audit.html` 列四大不可外推边界与机器门≠结论声明；Codex 首轮指出的"事实/稳定解释合并"与无锚"主流"已去除（06-research.html 中"最主流"仅以引号出现于"未回答"语境）。
- **准入路径修复正确**：`admission_path()` 截首个括号（含嵌套括号用例）、`ADMISSION_RANK` 只匹配路径前缀，195 行带括号判定串不再落入默认 rank；canonical schema 未动（`capability_details.csv` 列结构保留），测试含 canonical schema 不变约束（20/20 通过）。
- **五级覆盖与证实力度**：`calls/out/README.md` 五级表分母可复算（39 enabled；slot 39 / available 36 / claim 12 / reviewed 12 / event 15），asserted 32 / corroborated 2（EV013、EV014）分列且 corroborated 逐条列 ID；同源双证升级被 `calls/event_intelligence.py` 基线已有的 `lacks independent supporting origin` 校验拒绝，新测试实测覆盖。抽查 ADTRAN（零 claim）与 Lumentum（12 条 reviewed）公司卡，均无越级表述。
- **无 canonical 改动**：`git diff 7ff3b25..c53b9bd` 不涉及任何受保护账本；Codex 修复提交 `bcdb0ec` 与文档提交 `c53b9bd` 均在允许路径内。
- **日更/晋升边界与方向报告一致**：`calls/daily_discovery.py` 只写 staging 候选，`python -m calls check` 内置验证"0 行写入 calls/*.csv、calls/out 或 canonical"；`corpus/_daily_update.py` 产出 tmp/daily 日报与候选提示，不写 canonical；`domestic_daily` 只读源侧账本。晋升仍全人工，方向报告"发现与晋升拆开"的描述与代码现状相符。
- **产品方向报告无架构漂移**：未新增关系类型/schema/状态机/引擎；"暂不做"清单与宪章非目标逐项对应；优先级 1 的三个垂直切片（800G DR8 组件链、LPO 功耗、800G LPO 具名产品证据）是真实领域问题入口，符合"先真实切片、后架构裁决"的准入闸精神。

## 4. 不同意见

1. **对 Codex 集成审核**："已改善的读者行为"一节应限定为"生成器与已重建产物（calls/out、06-research.html）"，不应泛指读者页面——见 F1。这不构成拒绝集成的理由，但构成拒绝"读者侧已修复"这一表述的理由。
2. **对产品方向报告**：整体接受。一点排序异议：报告把 H9 类低成本完整性修复（triage 主键/日期）排在优先级 3 的逐项裁决中，置于三切片之后；我认为 H9 属机器门级修复、与领域切片无依赖，可与优先级 1 并行，不必排队。

## 5. 未决 UNKNOWN

1. 完整仓库的 `scan.py --check` / `participation.py --check` 是否全绿——本 worktree 缺 corpus，无法复验，仅能引用 Codex 报告（其指纹与命令未附）。
2. `calls/out` 47 个重建文件与基线的语义等价性——本复核只抽查 README 与 2 张公司卡，未逐文件比对。
3. `out/全景.*` 与能力明细 PDF/HTML 是否应在本工作包内重建——交付物与写入路径矛盾，属用户裁决（F1）。
4. render 侧是否增设"在库产物一致性"机器门——流程/架构裁决项（F2）。
5. 继承上游审计 UNKNOWN：H6 双重抽核缺口（引语定位 direct 3/10、non-direct 0/10）、archive 消融依赖、C5 拆分、海外双主张链合并、shipments 拆分等，本轮均未触及，维持待裁决状态。

## 6. 合规与测试记录

- 禁读遵守：未读 `archive/**`、closure/状态机材料、旧分支轨迹、代理全量日志、Cursor Fable 复核报告（不存在）。
- canonical：本复核零写入；`git status` 在本文件写入前干净。
- 只读测试（本 worktree，Python=/Users/jowang/miniconda3/bin/python3）：
  - `tests/test_capability_report_semantics.py`（直接执行）：20/20 通过
  - `pytest tests/test_render_data_quality_boundaries.py`：7/7 通过
  - `pytest --import-mode=importlib tests/site/test_optical_module_reader.py`：18/18 通过
  - `python -m unittest discover -s calls/tests`：169/169 通过（含 daily discovery"零写入 canonical"断言）
  - `pytest tests/test_daily_intelligence.py tests/test_domestic_daily.py`：13/13 通过
  - `render.py --verify`：通过（两次临时重建一致）
  - `python -m calls check`：通过
  - `scan.py --check` / `participation.py --check`：**失败**，原因均为本 worktree 缺失 `corpus/annual*`（见 F2），非集成错误
- 机器门通过仅证明结构、确定性与引用闭合，不代表领域数据问题已解决；canonical 侧 H1–H10 病灶全部保留待用户裁决。

## 7. 建议（提交用户裁决）

1. 裁决 F1：授权重建 `out/全景.*` 与能力明细 PDF/HTML，或收窄交付物口径表述。
2. 裁决 F2：是否在完整仓库重跑 scan/participation 门并记录指纹；是否增设 render 侧在库产物一致性校验。
3. 接受产品方向报告为下一阶段基准；优先级 3 的 canonical 修复逐项授权时，建议 H9（triage 完整性）可提前并行。
4. 集成版本维持本地候选状态，不推送远端，直到 F1/F2 裁决完成。
