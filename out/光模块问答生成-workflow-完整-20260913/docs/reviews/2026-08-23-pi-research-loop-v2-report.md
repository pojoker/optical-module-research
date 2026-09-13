# Pi 研究循环 v2：返修方案、小规模测试与复核请求

日期：2026-08-23
状态：`accepted_as_process_poc_no_promotion`
审核对象：研究循环方案与 RQ000 流程 PoC；不是知识答案
前版：[Pi 研究循环小样与四个可行方向](./2026-08-23-pi-research-loop-pilot-four-directions.md)
返修依据：[Kimi 批注](./2026-08-23-kimi-review-pi-research-loop-pilot.md)、
[Cursor/Composer 批注](./2026-08-23-composer-review-pi-research-loop-pilot.md)、
[Cursor Auto v2 首轮复核](./2026-08-23-cursor-auto-review-pi-research-loop-v2.md)、
[Kimi v2 最终复核](./2026-08-23-kimi-review-pi-research-loop-v2.md)、
[Cursor v2 最终复核](./2026-08-23-cursor-final-review-pi-research-loop-v2.md)

## 1. 结论先行

前版提出的“待研究问题 → Pi 找资料并回答 → 证据缺口生成细问题 → 审核后继续”的方向保留，
但实现形态改为：

> **来源发现与答案起草分离；Pi 原始产出先进入非事实账本研究包；细问题默认成为既有问题的研究
> 注记；只有问题验收合同容不下且问题树升版本时才新增节点；知识与问题状态只能由单写者工作项
> 经 reviewer 验收后更新。**

本轮 RQ000 小样证明“冻结来源后的答案起草与注记控制”可行；attempt-3 还暴露了模型会为凑满
数量上限制造行政注记，attempt-4 在合同加入注记必要性后关闭了该问题。小样没有证明 Pi 自主
联网发现来源已经安全可控，也没有证明 RQ000 已经得到正式回答。当前状态应是：

- 流程 PoC：`pass`；
- 内容草案：`usable_draft_with_one_boundary_correction`；
- `knowledge.yaml`：无新增；
- `research_questions.yaml`：无新增、无状态变化；
- RQ000：继续 `[待研究]`。

## 2. 本轮目标、范围与非目标

### 2.1 目标

1. 吸收 Kimi K1–K10 和 Cursor C1–C12 的阻断/非阻断意见；
2. 明确角色、数据血缘、状态和验收合同；
3. 保存一个完整可复核的 Pi 研究包；
4. 用严格工具边界重跑 RQ000 小样；
5. 验证“默认研究注记、不自动长节点”是否可执行；
6. 把返修方案提交 Kimi 与 Cursor 独立复核。

### 2.2 本轮不做

- 不把 Pi 草案写入 `knowledge.yaml`；
- 不把研究注记写成 CQ/PQ/TQ/WQ 新节点；
- 不修改现有二元 `[待研究]/[已覆盖]` 渲染逻辑；
- 不原子化或迁移 KN001–KN007；
- 不实现路线画像 ID；
- 不启动技术路线、WHY、公司能力群或投资研究；
- 不宣称 Pi 自主发现来源的前半段已经通过测试。

## 3. 术语与事实边界

### 3.1 不再混称 canonical

- `knowledge.yaml` 等项目既有七文件：事实/能力账本 canonical；
- `research_questions.yaml`：研究导航配置，保存问题层级和合同，不是事实账本；
- `docs/research/pi-packages/**`：非事实账本审计包，保存研究过程，不参与读者页事实渲染；
- 研究注记：挂在既有问题下的聚焦缺口，不是新问题节点。

### 3.2 仍然只有两套知识体系

知识体系合法值仍是：

- `物理知识`；
- `技术路线`。

“研究框架”只能描述主张类型或展示方法，不能成为第三个 `system`。历史 attempt-2 的 D3 使用
`system: 研究框架`，已判为不合格；attempt-3/4 合同和输出均只允许“物理知识”。

### 3.3 路线框架、路线条目和路线画像分离

- 产品路线框架：当前 `route_bom.csv` 对 800G DR8、1.6T DR8、400ZR 的产品级投影；
- RB：路线框架下的 BOM/架构条目；
- 路线画像：正交轴取值均明确的完整工程组合；未来应有独立 `RP###` 标识。

在 RP schema 落地前，技术路线 KN/WHY 不得拿一个 `architecture_only` RB 冒充完整路线。方向 C
继续冻结。

## 4. 角色与治理流程

| 角色 | 职责 | 禁止 |
|---|---|---|
| 研究发起人 | 选择 QID、冻结问题验收合同与来源发现范围 | 直接把草案当答案 |
| 来源整理者 | 发现来源、保存快照、建立来源清单与状态 | 解释来源含义、自动升级证据等级 |
| Pi 起草者 | 只基于冻结来源起草原子主张、注记和拒绝推论 | 写事实账本、发新问题 ID、自我验收 |
| 闸主/单写者 | 裁决证据和语义，认领 write_scope，准备落库变更 | 自己宣布 reviewer 通过 |
| Reviewer | 独立复核原始输出、锚点、合同和拟写变更 | 修改 owner 的 write_scope |
| 用户 | 对结构性 schema/路线画像/问题树升版本作最终决策 | — |

正式落库必须接入 `refs/CODEX-KIMI-COLLAB.md` 的既有机制：

1. 建工作项并写明 owner、reviewer、write_scope；
2. 单写者认领；
3. Pi 研究包作为 delivery 附件；
4. owner 只提交拟修改路径；
5. reviewer 给 `accepted` 或 `changes_requested` 回执；
6. 只有 accepted 后，单写者才更新事实账本或研究导航配置；
7. 用户要求的结构性变更仍由用户确认。

本报告不修改协作账本，避免在未认领 write_scope 时越权写入。

## 5. 数据来源与血缘

```text
研究导航配置中的 QID
  → 问题验收合同
  → 来源发现记录（尚未完成安全 PoC）
  → 冻结来源清单 / local_file / web_snapshot
  → Pi 原始输出
  → Codex/闸主裁决
  → Kimi/Cursor reviewer 回执
  → accepted 后的 KN/WHY 或研究注记
  → scan 校验
  → render 状态与读者页
```

每轮研究包固定目录：

```text
docs/research/pi-packages/YYYY-MM-DD-<qid>-<version>/
  contract-attempt-*.md
  sources.md
  run.yaml
  command-attempt-*.txt
  raw-output-attempt-*.md
  adjudication-attempt-*.md
  adjudication.md
```

选择 `docs/research/pi-packages/` 的原因：

- `refs/` 已达 8/8 上限，不可再塞；
- `tmp/` 不可版本化，不能作为审核锚；
- `docs/research/` 已存在且属于文档根白名单，不新增仓库顶层目录；
- 研究包明确非事实账本，不被 `render.py` 当成知识答案。

## 6. 来源政策

### 6.1 发布状态分级

不能只按“是否一手来源”二分。至少区分：

1. 已批准标准正文；
2. MSA/SDO 现行规范或官方页面；
3. 项目目标、草案、工作组动议；
4. 公司定期报告/官方技术口径；
5. 论文原文；
6. 二手材料（只作发现线索）。

例如 IEEE objectives 只能证明工作组目标，不证明已批准 PMD、物理极限或商业采用。

### 6.2 锚型

- 本地披露件：`local_file`，必须可定位到文件和行/页上下文；
- 官网/MSA：正式入库前必须形成 `web_snapshot`，包含原 URL、存档路径和抓取日期；
- 官网不得直接成为公司能力点锚；点仍遵守现有披露件纪律；
- 研究包可记录未快照 URL，但这种材料只能保持 draft。

### 6.3 预算

不再使用“整轮最多 3 个来源族”作为硬门槛，也不把 5 分钟墙钟当验收指标：

- 每条原子主张至少一个直接锚；可增加一个独立佐证；
- 单来源域但明确声明缺口，可以成为合格研究草案；
- 来源数量由问题验收合同决定，不为凑数补来源；
- 每轮最多 3 条原子主张、3 条研究注记，防止输出发散；
- 记录检索轮次、来源清单、输出条数；墙钟仅作运行诊断。

### 6.4 实时基线如何更新

实时基线可以更新，但不能覆盖历史研究包中的冻结来源。方案采用“双层时间语义”：

- `current baseline`：面向下一轮研究，可随新标准、公司披露和产品发布更新；
- `frozen snapshot`：面向复核，记录本轮实际看到的版本、抓取日期和锚点，永久不原地改写。

基线更新必须新建快照或新版本，并标注 `as_of`、变更原因、受影响 QID/RP 和是否触发“需复核”。
这样读者可以看到最新状态，reviewer 仍能重放旧结论当时依据的证据。

这套语义当前是“概念闭合、实施未闭合”：现有页面会从当前 YAML/CSV 重算实时基线，研究包也能
冻结来源，但 schema 与扫描器尚无上述时间字段、漂移检测或“需复核”触发，也没有当前基线到
历史研究包的机器链接。它是状态机实施项，不是本轮已完成能力。

## 7. 问题验收合同与状态

### 7.1 现状缺陷

当前每个问题的 acceptance 都是“有一条通过校验的 KN 显式关联本问题”。渲染器也只要看到
`研究问题` 引用就显示 `[已覆盖]`。这会奖励最快过 schema 的合成条目，不能证明问题已回答。

### 7.2 建议合同字段

未来 `research_questions.yaml` 每题至少需要：

- `allowed_system`；
- `answer_shape`；
- `required_claim_scopes`；
- `evidence_policy`；
- `coverage_requirements`；
- `stop_conditions`；
- `downstream_unlocks`；
- `contract_version`。

### 7.3 建议状态

- `待研究`：无有效工作包；
- `研究中`：工作项已认领；
- `有草案`：研究包已裁决，但尚未 accepted/promotion；
- `部分覆盖`：合同必需项部分 accepted；
- `已覆盖`：合同全部条件满足；
- `需复核`：来源失效、合同升版或证据被证伪。

本轮不实现状态机。RQ000 即使已有三个草案，仍是 `待研究`，因为合同和 accepted 知识均未落地。

### 7.4 RQ000 的特殊处理建议

RQ000 是综合导航根，不应由“一条直接引用 RQ000 的 KN”完成。建议后续改为合成状态：

- PQ001 的对象/系统边界合同满足；
- PQ002 的电→光→电功能链合同满足；
- 有一条明确的变体边界声明，说明具体样机不代表全家族；
- 根答案只聚合 accepted 子项，不另造四合一事实 KN。

因此第一阶段顺序固定为：`RQ000 口径声明 → PQ001 判界 → PQ002 功能链`。TQ001 推迟到 TQ004
正交轴和路线画像语义稳定之后。

## 8. 问题如何生长

### 8.1 默认不新增节点

证据矛盾、空白或聚焦问题先写成研究注记，并声明：

- 挂载到哪个现有 QID；
- 由哪条证据触发；
- 为什么现有问题可以承接；
- 预期答案形态；
- 停止条件。

数字“最多 3 条注记”只是防凑数上限，不是问题生长算法。

### 8.2 新节点的唯一入口

只有同时满足以下条件，才可提出问题树升版本：

1. 既有父问题验收合同确实容不下；
2. 明确声明 `parent_id`、`system`、顺序与答案形态；
3. 不与现有 PQ/TQ/WQ 重复；
4. 有证据触发、验收条件和停止条件；
5. 能解锁至少一个下游问题；
6. 用户批准升版本；
7. 通过 scan/render 的新增节点测试。

不再使用 CQ 编号空间。

## 9. 存量 KN001–KN007 兼容方案

前版要求新 KN 原子化，但没有处理存量复合叙事。v2 建议：

1. KN001–KN007 保持原 ID、原顺序、原文，不为了覆盖率机械补 `研究问题`；
2. `legacy_narrative` 只是建议增加的描述标签，不是当前代码已有状态；当前扫描器的真实行为是把
   缺失 `体系` 的条目默认成“物理知识”，并忽略缺失 `研究问题` 引用；
3. 在正式实现该标签前，KN001–KN007 只能按上述真实兼容行为读取；它们可以作为研究线索和页面
   解释，但不得自动满足新问题验收合同；
4. 新研究产生的 accepted 原子主张使用新 KN ID，不回收旧编号；
5. 如 legacy 中某个主张值得提升，新增原子 KN 并引用原条目的证据来源，不修改旧条目语义；
6. 等前三个物理问题跑通后，再决定是否批量建立 legacy→QID 的人工映射。

这在政策层避免一次性迁移与机械补映射，但当前没有机器防线：任何人给 legacy KN 增加一个
`研究问题` 引用，仍会瞬间翻转二元覆盖。状态机/扫描守卫未落地前，promotion 必须保持阻断。

## 10. 路线画像 ID 的后续设计要求

方向 C 启动前新增 `RP###` 一等对象，至少包含：

- `profile_id`；
- 所属产品路线框架；
- 产品/链路标准轴值；
- 电接口架构轴值；
- 光子平台轴值；
- 封装架构轴值；
- 适用条件与证据状态；
- 对应 RB 物理变化条目。

同时必须一次性修改：

- `route_bom.csv` 的路线画像映射/schema；
- 技术路线 KN 的路线引用；
- WHY 的路线引用；
- `scan.py` 不变量⑭；
- 候选能力群的选择轴/路线渲染；
- 确认服务群渲染逻辑；
- append-ready 模板；
- 自测与 `--verify`。

在这组改动完整设计并验收前，禁止用 `RB001/RB006/RB011` 代表整条路线画像。

## 11. RQ000 小规模测试

研究包：[`docs/research/pi-packages/2026-08-23-rq000-v2/`](../research/pi-packages/2026-08-23-rq000-v2/)

### 11.1 attempt-1：工具面仍过宽

- 模型：`opencode-go/deepseek-v4-flash`；
- 禁用 shell/网络/写入，但仍开放 read/grep/find/ls；
- 因理论上仍可读工作区其他文件，只保留为历史记录。

### 11.2 attempt-2：机械边界通过，语义合同失败

- 参数：`--no-tools --no-context-files --no-session`；
- 输入仅历史合同与冻结来源；
- Pi 未写 YAML、未新增问题 ID、未改覆盖状态；
- 但合同错误地允许第三体系，输出也把无快照 S4 标成直接事实并挂错 QID；
- Cursor 指出 Codex 初次裁决遗漏了这些组合错误和停止结论的自相矛盾。

结论：历史失败样本，不能作为最终 PoC。

### 11.3 attempt-3：关闭硬边界，暴露“凑注记”问题

- 合同只允许“物理知识”，S4 只挂 PQ001 注记，S5 只进拒绝推论；
- 输出遵守体系、QID、证据和覆盖边界；
- 但为了凑满“最多 3 条”，生成一条“本轮未研究 PQ002”的行政注记；
- Codex 判 `process_pass / minor_changes_requested`。

结论：数量上限不能替代注记必要性标准。

### 11.4 attempt-4：最终流程小样

- 模型：`opencode-go/deepseek-v4-flash`；
- 完整命令：`command-attempt-4.txt`；
- 参数：`--no-tools --no-context-files --no-session`；
- 输入：仅 `contract-attempt-4.md` 与 `sources.md`；
- exit code：0，观察墙钟约 53 秒，仅作诊断；
- 输出：3 条 RQ000 公司口径草案、2 条证据触发注记、4 类拒绝项；
- 未生成新问题 ID、未输出 YAML，所有 `would_mark_covered` 为 false；
- S1–S3 本地锚已由 Codex 回读上下文核对；
- 未修改事实账本或研究导航配置。

### 11.5 Codex 最终裁决

流程 `pass`，内容 `usable_draft_with_one_boundary_correction`。保留的一处人工修正是：Pi 在停止
结论中把 S5 说成“整体拒绝为任何问题的证据”，范围过宽。正确口径是 S5 不能进入本轮 RQ000，
但未来可在 TQ005 独立合同中以“项目目标”身份受审。

两位 reviewer 还确认：N2 的“口径张力”偏弱，只宜保留为 draft 注记；S4 在旧来源清单里的
“可直接支持”措辞不等于可作正式证据；N1/N2 的停止条件是各自局部条件，不是阻止 PQ001
draft-only 开始的全局门闩。

因此小样证明的是：冻结来源后的受控起草能够把真实证据缺口沉淀为既有问题的研究注记，并阻止
自动长节点。它没有证明答案已经可落库，也没有证明自主来源发现环节已经安全。

## 12. 四个推进方向（返修版）

### A. 对象定义与物理边界

顺序固定：`RQ000 口径声明 → PQ001 判界表 → PQ002 功能链`。不含 TQ001/TQ002。

### B. 参考产品纵切

先完成 PQ003 的选型表与否决项，再打开 PQ004–PQ009。样机事实、家族共性、典型实现、工程
推论分层记录。

### C. 路线画像与 Why

只在 RP schema、TQ004 轴语义和 WQ/RP 引用合同完成后启动。比较完整路线画像，不比较错位名词。

### D. 公司能力群与路线服务

最后启动。候选能力群继续只表示能力匹配；确认服务群必须闭合 RP、路线级 KN 与真实 point；供货
仍只读 `edges.csv`。

推荐顺序：A → B → C → D。

## 13. 尚未验证的部分

### 13.1 Pi 自主来源发现

attempt-4 使用冻结来源包，因此没有验证 Pi 自主联网发现来源。要验证前半段，需要一个只有搜索、
打开网页、保存快照和记录查询能力的 web-only 工具面；不能重新开放通用 bash。

在该能力实现前，来源发现由受控检索者完成，Pi 只做冻结来源后的起草。不得把本轮称为“全自动
找资料闭环”。

### 13.2 问题状态机

当前代码仍是二元覆盖。状态机和验收合同只完成方案设计，尚未实现或测试。

### 13.3 路线画像

RP schema 尚未落地，技术路线和 WHY 研究继续冻结。

## 14. 验证记录

| 操作 | 结果 |
|---|---|
| 读取 Kimi、Cursor 前版批注与 Cursor v2 首轮复核 | 全文读取；阻断项纳入本报告 |
| Pi attempt-2/3/4 | 均保存合同与原始输出；attempt-4 exit 0 |
| 最终工具边界 | 无工具、无 context、无 session；完整命令已落盘 |
| 最终原始输出 | `raw-output-attempt-4.md` |
| Codex 最终裁决 | `adjudication.md`；process pass / usable draft with one boundary correction |
| S1–S3 本地锚 | 已人工回读所列行及上下文 |
| Kimi 最终复核 | accepted，仅流程 PoC；批准 PQ001 draft-only；拒绝 promotion |
| Cursor 最终复核 | accepted，仅流程 PoC；同意 Kimi 主判断；拒绝 promotion |
| Miniconda 扫描 | `/Users/jowang/miniconda3/bin/python3 scan.py --check`：不变量 ①–⑭ 全绿 |
| 渲染一致性 | `/Users/jowang/miniconda3/bin/python3 render.py --verify`：一致 |
| 研究包引用 | Miniconda YAML 解析及合同/输出/命令/裁决/reviewer 路径检查通过 |
| 文档差异 | `git diff --check` 对本轮已跟踪文档无错误 |
| 当前事实账本 | 未因本小样修改 |
| 当前研究导航配置 | 未新增问题、未改变覆盖状态 |
| Python 约束 | 本轮 Pi 无 Python；项目验证仍只允许 Miniconda 解释器 |

## 15. 请 Kimi 与 Cursor 重点复核

1. `docs/research/pi-packages/` 是否满足可复现且不污染事实账本；
2. `--no-tools --no-context-files` 是否真正关闭了 K1/K6 类工具边界问题；
3. attempt-4 裁决是否还遗漏 Pi 的语义错误，尤其是 N1/N2 是否真有必要；
4. RQ000 合成状态和 A 阶段顺序是否合理；
5. legacy KN 兼容方案是否足以防止新旧双轨；
6. 研究注记默认、不发 CQ 的规则是否闭合；
7. RP schema 的冻结条件是否覆盖 KN、WHY、确认服务群和校验器；
8. 是否可以批准下一轮只研究 PQ001 的 draft-only 包，还是仍需返修。

当前即使 reviewer 通过流程，仍有三项 promotion 阻断：现有二元覆盖渲染未改、S4 无
`web_snapshot`、append-ready 模板仍允许 `url` 和 RB 冒充完整路线引用。

## 16. 批准标准

本报告只有在以下条件同时满足后才可视为通过：

- Kimi 与 Cursor 均完成独立复核；
- 所有新 P1 有明确处理；
- 两位 reviewer 不再指出研究包不可复核、问题自动生长或路线引用混乱；
- Miniconda `scan.py --check` 仍全绿；
- `git diff --check` 对本轮文档无错误；
- 未误改事实账本、问题树或现有用户数据。

最终结果：以上条件对“流程 PoC”已经满足，故状态为 `accepted_as_process_poc_no_promotion`。
三项 promotion 阻断仍然开放，因此该 accepted 不得被解释成 RQ000 已回答或允许写入 canonical。
