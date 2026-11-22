## 1. RQ000 口径声明

RQ000“什么是光模块”的对象口径（多个发布主体的并列口径，非事实）：中际旭创称光模块作用为光电转换；博创科技称其由光电子器件和功能电路等组成；腾景科技称其由光学元组件、光纤器件封装而成。三家口径并列保留，本轮不合成唯一标准定义。

## 2. 原子主张草案

### 草案 1

- `draft_id`：`draft-rq000-001`
- `system`：`物理知识`
- `question_id`：`RQ000`
- `claim_type`：`公司口径`
- `statement`：按中际旭创 2024 年年度报告口径，光模块的作用是光电转换。
- `evidence_ids`：`[S1]`
- `boundary`：仅为中际旭创一家公司的功能口径；不推广为行业唯一功能定义，不支撑模块构成、可插拔形态或技术路线结论。
- `would_mark_covered`：`false`

### 草案 2

- `draft_id`：`draft-rq000-002`
- `system`：`物理知识`
- `question_id`：`RQ000`
- `claim_type`：`公司口径`
- `statement`：按博创科技 2024 年年度报告口径，光模块由光电子器件和功能电路等组成。
- `evidence_ids`：`[S2]`
- `boundary`：仅为该公司对构成的概括口径；不等于完整 BOM，不能推断所有实现均采用同一构成，不涉及具体接口或工艺。
- `would_mark_covered`：`false`

### 草案 3

- `draft_id`：`draft-rq000-003`
- `system`：`物理知识`
- `question_id`：`RQ000`
- `claim_type`：`公司口径`
- `statement`：按腾景科技 2024 年年度报告口径，光模块由光学元组件、光纤器件封装而成。
- `evidence_ids`：`[S3]`
- `boundary`：仅为该光学元件供应商的公司口径；不能推断光模块只含光学元件，或完整模块不含电路与结构件。
- `would_mark_covered`：`false`

## 3. 研究注记

### 注记 1

- `attach_to`：`RQ000`
- `note`：S1–S3 是三家公司的并列口径，功能、电学构成、光学构成三种侧重并存，本轮不合成唯一事实定义。
- `trigger_evidence_ids`：`[S1, S2, S3]`
- `why_existing_question_can_hold_it`：RQ000 正是“什么是光模块”的对象口径问题，口径并列与不足以注记形式挂载于此，不改变覆盖状态。
- `expected_answer_shape`：按发布主体逐条开列的并列口径清单，每条附来源锚点与边界说明。
- `stop_condition`：出现经 `local_file`/`web_snapshot` 锚定的权威标准定义后，再评估是否收敛。

### 注记 2

- `attach_to`：`PQ001`
- `note`：S4（OSFP MSA 官方页面）尚无 `web_snapshot`，其“mechanical module / card cage / electrical interface and pinout”口径本轮只能作为研究包材料，不能成为原子主张证据。
- `trigger_evidence_ids`：`[S4]`
- `why_existing_question_can_hold_it`：S4 属于形态/构成维度，用于识别 RQ000 下游边界，仅注记附着于 PQ001，不替 PQ001 起草答案。
- `expected_answer_shape`：补齐 `corpus/web/` 快照并核对原文后，在 PQ001 研究包中形成带来源锚的形态构成口径清单。
- `stop_condition`：完成 web 快照并与原文上下文核对后关闭本注记。

### 注记 3

- `attach_to`：`PQ002`
- `note`：本轮 S1–S3 公司口径仅为 RQ000 口径声明服务，未对 PQ002 起草任何内容；也未新增任何 CQ/PQ/TQ/WQ 编号。
- `trigger_evidence_ids`：`[S1, S2, S3]`
- `why_existing_question_can_hold_it`：PQ002 作为 RQ000 下游边界问题，需要一条“本轮未触碰”的边界注记，防止 RQ000 口径被误用到下游问题。
- `expected_answer_shape`：PQ002 应拥有独立的冻结来源包与证据清单，由后续轮次另行研究。
- `stop_condition`：PQ002 建立自己的来源包并完成锚型核对后关闭。

## 4. 拒绝的推论

| 编号 | 被拒绝的推论 | 拒绝理由 |
|---|---|---|
| R1 | 把 OSFP MSA 页面（S4）当作“直接事实”或原子主张证据 | S4 没有 `web_snapshot`，不能被写成直接事实草案，只能触发 PQ001 研究注记 |
| R2 | 把 IEEE P802.3df 项目目标（S5）挂入任何问题，或推成 RQ000 答案/铜光分界事实 | S5 是项目目标而非已批准标准正文，只能进入“拒绝的推论”，不挂任何 QID |
| R3 | 把 S1–S4 合成唯一标准定义，或以任一发布主体口径替代全部 | 组合只允许以“多个发布主体的并列口径”出现于 RQ000 口径声明，不能标成事实 |

## 5. 自检矩阵

| 检查项 | 合同要求 | 本轮输出 | 结果 |
|---|---|---|---|
| 体系 | 原子主张 `system` 逐字等于 `物理知识` | 全部为 `物理知识` | 通过 |
| QID | 仅 RQ000/PQ001/PQ002，无新增 CQ/PQ/TQ/WQ | 主张仅挂 RQ000；注记挂 RQ000/PQ001/PQ002；无新编号 | 通过 |
| 证据 | 主张证据只来自 S1–S3；S4 只挂 PQ001 注记；S5 不挂任何问题 | 主张证据 `[S1]/[S2]/[S3]`；S4 仅出现于注记 2 与拒绝推论；S5 仅出现于拒绝推论 | 通过 |
| 覆盖状态 | `would_mark_covered` 全 false；不称草案为事实/已覆盖；不输出 `knowledge.yaml` | 全部 false；草案标注为“公司口径/草案”；无 `knowledge.yaml` 输出 | 通过 |

## 6. 停止结论

本轮为流程 PoC：完成 RQ000 口径声明、3 条公司口径原子主张草案与 3 条研究注记。S4 因缺快照仅挂 PQ001 注记，S5 仅列入拒绝推论。不写事实账本、不改变问题覆盖状态、不输出 append-ready `knowledge.yaml`，停止。
