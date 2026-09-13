# PQ001 Pi 研究合同 v1：attempt-2

状态：`draft_only`
目标问题：`PQ001 光模块在系统中解决什么问题，边界在哪里？`
本轮阶段：受控研究，不写事实账本，不改变问题覆盖状态

## 1. 答案结构

本轮采用三层回答，不追求无条件的行业唯一边界：

1. `条件化通用骨架`：只对 CMIS-managed transmission module，说明 Host Interface、Media
   Interface 和模块作为 bridge 的功能；
2. `可插拔实例`：用 OSFP 说明 module 与 host connector/cage/PCB/heatsink、外部光接口的边界；
3. `非可插拔反例`：用 OIF 3.2T CPO IA 说明 module 可靠近 ASIC、与 ASIC 共用 assembly
   substrate、甚至 embedded on board，因此前面板 cage/card-edge 不是所有光模块的共同边界。

### 只读上下文

- `RQ000`：不重新回答；
- `PQ002`：不展开内部电→光→电功能链；
- `PQ003`：只允许生成有证据触发的样机选择注记，不替它选型。

### 禁止

- 把 CMIS-managed transmission module 等同于所有语境中的光模块；
- 把 CMIS §6.1 的高速 `Host Interface` 与承载管理协议的低速 MCI/TWI 混为一层；
- 把 OSFP cage/card-edge/integrated heatsink 推广到 CPO、on-board optics 或所有模块；
- 把“靠近 ASIC/共用 substrate”写成 ASIC 属于模块本体；
- 把 pigtail、receptacle 或 front-panel connector 写成所有模块共同的 media-side 形态；
- 回答组件 BOM、工艺、技术路线、WHY、公司能力群、供货或投资问题；
- 新增问题 ID、输出 YAML、修改覆盖状态或声称 PQ001 已覆盖；
- 联网、运行工具、shell、Python、校验命令或写文件。

## 2. 主张类型和证据

- 所有原子草案 `system: 物理知识`、`question_id: PQ001`；
- `claim_type` 只允许：`公司口径`、`CMIS规范事实`、`OSFP规范事实`、`CPO规范事实`；
- 只使用 `sources-attempt-2.md` 中 `admissible_for_draft: true` 的来源；
- 必须按完整页上下文判断，不得从短引扩张；
- 每条主张必须写 `boundary` 与 `rejected_inference`；
- `would_mark_covered` 固定为 false。

## 3. 必须回答的边界

1. 对符合条件的 transmission module，系统问题是什么；
2. host-side 与 media-side 分界在“接口”层如何表达；
3. OSFP 可插拔模块的电/机械/热边界如何落到实体；
4. CPO 如何证明 enclosure/cage/card-edge 不是通用边界；
5. 外部光介质可能在 receptacle 或 pigtail 等不同位置衔接，边界为何不能只按连接器形态定义；
6. 哪些结论只是公司口径、CMIS 条件口径、OSFP 事实或特定 CPO IA 事实。

## 4. 输出格式

1. `PQ001 结论摘要`：不超过 220 字，必须包含条件和三层结构；
2. `三层边界图`：用简洁文本图表示“Host system ↔ module ↔ media/remote peer”，并分别标注
   OSFP 与 CPO 实例差异；
3. `系统边界表`：至少包含通用骨架、OSFP、CPO、不可泛化项；
4. `原子主张草案`：最多 5 条，每条含：
   - `draft_id`
   - `system`
   - `question_id`
   - `claim_type`
   - `statement`
   - `evidence_ids`
   - `boundary`
   - `rejected_inference`
   - `would_mark_covered`（固定 false）
5. `研究注记`：0–3 条，只能挂 PQ001/PQ003，必须包含证据触发、层级理由、下一步、停止条件；
6. `拒绝的推论`：至少拒绝“OSFP=全部”“CMIS=全部”“ASIC/cage/heat sink 归属无条件固定”；
7. `自检矩阵`：体系、QID、锚型、条件、接口层级、完整上下文、注记必要性、覆盖状态；
8. `停止结论`：局部停止条件不得成为其他 draft-only 轮次的全局门闩。

不得输出 append-ready YAML。

## 5. 注记必要性

注记必须同时满足：具体证据触发、实质缺口、可执行下一步、可判定停止条件、正确挂层。必须先用
冻结材料完整上下文尝试解决；能由现有证据解决时不得发注记。少于 3 条是正常结果。

## 6. 验收

- 条件化通用骨架、OSFP 实例、CPO 反例明确分层；
- 没有把高速 Host Interface 和低速管理通信混淆；
- 没有把特定机械实体推广成所有模块边界；
- 没有把 ASIC 或 host substrate 并入 module；
- 每条事实与其规范/公司主体逐字对应；
- 没有新增 ID、YAML、覆盖状态；
- `would_mark_covered` 全 false；
- 自检与正文一致。
