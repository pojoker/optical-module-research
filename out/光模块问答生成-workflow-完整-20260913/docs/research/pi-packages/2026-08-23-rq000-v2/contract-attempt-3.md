# RQ000 Pi 小样 v2：attempt-3 最终研究合同

状态：`draft_only`
目标问题：`RQ000 什么是光模块？`
本轮阶段：流程 PoC，不写事实账本，不改变问题覆盖状态

## 1. 权限边界

### 可以读取

- `RQ000`：允许起草对象口径；
- `PQ001`、`PQ002`：只用于识别 RQ000 的下游边界，不允许替它们起草答案；
- 本研究包 `sources.md`。

### 可以输出

- 一段 RQ000 的对象口径声明；
- 最多 3 条物理知识原子主张草案；
- 最多 3 条研究注记，只能挂 `RQ000/PQ001/PQ002`，不得发新问题 ID；
- 对 S4/S5 的排除理由、证据不足和停止结论。

### 禁止

- 回答 PQ001、PQ002 或任何 TQ/WQ；
- 输出技术路线 KN、WHY、公司能力群、供货或投资结论；
- 新增 CQ/PQ/TQ/WQ 编号；
- 把“研究框架”写成 system；
- 把无 `web_snapshot` 的 S4 写成“直接事实”草案；
- 把 S5 写进 RQ000 的预期答案或研究注记；
- 联网、运行工具、shell、Python、校验命令或写文件。

## 2. 进程能力

不开放任何工具，并关闭项目 context 文件自动加载。`contract-attempt-3.md` 与 `sources.md` 作为
初始输入附件注入。

## 3. 体系、主张和来源口径

- 所有原子主张 `system` 必须逐字等于 `物理知识`；
- `claim_type` 只允许 `公司口径`；本轮没有已完成正式锚型的标准事实；
- S1–S3 只能证明相应公司的功能/构成表述；
- S4 没有 web snapshot，只能触发 PQ001 研究注记，不能成为原子主张；
- S5 是项目目标，只能进入“拒绝的推论”，不能挂到任何 QID；
- 不允许把 S1–S4 合成唯一标准定义；组合只能出现在 RQ000 口径声明中，并逐字标为
  “多个发布主体的并列口径”，不能标成事实。

## 4. 输出格式

1. `RQ000 口径声明`：不超过 180 字；
2. `原子主张草案`：最多 3 条，每条含：
   - `draft_id`
   - `system`（固定 `物理知识`）
   - `question_id`（固定 `RQ000`）
   - `claim_type`（固定 `公司口径`）
   - `statement`
   - `evidence_ids`（只能 S1/S2/S3）
   - `boundary`
   - `would_mark_covered`（固定 false）
3. `研究注记`：最多 3 条，每条含：
   - `attach_to`（只能 RQ000/PQ001/PQ002）
   - `note`
   - `trigger_evidence_ids`
   - `why_existing_question_can_hold_it`
   - `expected_answer_shape`
   - `stop_condition`
4. `拒绝的推论`：必须包含 S4 未快照、S5 项目目标、唯一标准定义三类拒绝；
5. `自检矩阵`：逐项列出体系、QID、证据、覆盖状态；
6. `停止结论`。

不得输出 append-ready `knowledge.yaml`。

## 5. 验收

- 原子主张全部为 `system: 物理知识`；
- 原子主张证据只来自 S1–S3；
- S4 只挂 PQ001 注记；
- S5 不挂任何问题，只出现在拒绝推论；
- 没有 TQ/WQ/CQ；
- 没有把草案称为直接事实、正式知识或已覆盖；
- `would_mark_covered` 全 false；
- 自检矩阵与正文一致。
