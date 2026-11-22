# PQ002 draft-only 研究合同

## 1. 目标与边界

- 唯一回答目标：`PQ002 电→光→电的功能链如何工作？`
- 体系：`physical`
- 只读上文：PQ001 的条件化系统边界；不得重写 PQ001。
- 只生成研究草案，不写 `knowledge.yaml`、`research_questions.yaml`、CSV 或任何 canonical。
- 不生成新问题 ID，不改变覆盖状态；所有草案均写 `would_mark_covered: false`。

## 2. 验收条件

1. 分别给出发送方向和接收方向的端到端**功能链**，从 Host Interface 走到 Media
   Interface，再从远端 Media Interface 返回 Host Interface。
2. 明确区分三层：接口边界、模块内部功能、某个真实产品采用的实现部件。
3. 标出哪些只是 CMIS-managed transmission module 的条件骨架，哪些是光模块公司口径，
   哪些是具体 OSFP 产品实例。
4. 区分 mission data path 与管理、供电、机械、热路径；不得把 I2C/CMIS 管理路径写入
   高速数据链。
5. 每条原子主张必须包含：`draft_id`、`system`、`question_id`、`claim_type`、
   `statement`、`evidence_ids`、`boundary`、`rejected_inference`、
   `would_mark_covered: false`。
6. 明确停止边界：本题不回答完整 BOM、组件材料、制造工艺、设备、技术路线优劣。

## 3. 禁止推论

- 不得把 DSP、driver、TIA、EML、PIN、lens、FAU 等写成所有光模块必备。
- 不得把 EML/PIN 的产品实例写成行业共同结构。
- 不得把 Host Interface 与低速管理接口混淆。
- 不得把 Media Interface 一概写成可拆卸光纤接口；CMIS 允许电或光 media，CPO 也有不同机械实现。
- 不得因为公司年报写“电转光/光转电”，就补出未经来源支持的内部器件顺序。

## 4. 输出格式

只输出中文 Markdown，包含：

1. 结论摘要；
2. TX/RX 功能链图；
3. 三层分解表（接口/功能/实例部件）；
4. 原子主张草案；
5. 研究注记（只有冻结来源完整上下文仍不能解决时才产生，挂现有 QID，不发明新 ID）；
6. 拒绝的推论；
7. 自检矩阵；
8. 停止结论。
