# PQ001 Pi 研究合同 v1：attempt-3 最终合同

状态：`draft_only`
目标问题：`PQ001 光模块在系统中解决什么问题，边界在哪里？`
本轮阶段：受控研究，不写事实账本，不改变问题覆盖状态

## 1. 三层答案

1. `条件化骨架`：对 CMIS-managed transmission module，Host Interface 是 module/host system
   间高速电接口，Media Interface 是 module/remote media 间高速电或光接口；Application 起 bridge
   作用；
2. `OSFP 可插拔实例`：card-edge pads 配 host connector，module 外壳配 host cage；标准 OSFP
   includes integrated heatsink，OSFP-RHS 接触属于 host 的 riding heatsink；module-side optical
   receptacle/connector 图示是 guideline；
3. `3.2T CPO 反例`：module 可靠近 ASIC、共 assembly substrate 或 embedded on board，光经
   pigtail；说明前面板 cage/card-edge 不是所有模块的必要边界。

公司年报只提供带主体的电↔光功能口径，不能替代上述规范边界。

## 2. 禁止

- 把 CMIS 条件骨架推广为所有光模块；
- 把高速 Host Interface 与低速 two-wire 管理通信混淆；
- 把 module card-edge 写成与 cage 直接配对；正确配对是 card-edge pads ↔ host connector；
- 把 cage、host connector、host PCB 或 host riding heatsink 写入 module 本体；
- 再提出“标准 OSFP 无 integrated heatsink 时归属不明”的注记；来源已明确 includes；
- 再提出“§14.4 未读取完整页”的注记；attempt-3 来源已给出完整上下文；
- 绝对化声称该 CPO IA 的所有实现均“无 cage/card-edge”；只能说它展示了不以前面板
  cage/card-edge 为必要边界的实现；
- 推断整份 OSFP 规范是否完整定义光学 PMD；本轮只写 §14.4 图示是 guideline；
- 回答 BOM、内部功能链、工艺、技术路线、WHY、公司能力或投资问题；
- 新增问题 ID、输出 YAML、修改覆盖状态或写文件；
- 联网、运行任何工具、shell、Python 或校验命令。

## 3. 主张与证据

- `system: 物理知识`，`question_id: PQ001`；
- `claim_type` 仅：`公司口径`、`CMIS规范事实`、`OSFP规范事实`、`CPO规范事实`；
- 只用 `sources-attempt-3.md`；每条保留主体、条件、边界和被拒绝推论；
- `would_mark_covered: false`；
- 接口层的比较结论可以进入边界表，但原子主张只能写来源直接支持的事实。

## 4. 输出格式

1. `PQ001 结论摘要`（≤220 字）；
2. `三层边界图`；
3. `系统边界表`，至少列条件骨架、OSFP、CPO、公司口径、不可泛化项；
4. `原子主张草案`，最多 5 条，每条含：
   `draft_id/system/question_id/claim_type/statement/evidence_ids/boundary/rejected_inference/
   would_mark_covered`；
5. `研究注记`，0–2 条，只能挂 PQ001/PQ003；必须先证明冻结来源完整上下文仍无法解决，且含
   证据触发、层级理由、下一步、停止条件；
6. `拒绝的推论`：至少拒绝 OSFP=全部、CMIS=全部、机械归属固定、Host Interface=管理接口；
7. `自检矩阵`：体系、QID、锚型、条件、实体配对、接口层级、上下文、注记必要性、覆盖状态；
8. `停止结论`：局部条件不成为其他 draft-only 轮次的门闩。

不得输出 append-ready YAML。

## 5. 验收

- card-edge/connector/cage 三个实体关系准确；
- OSFP 两类 heatsink 归属准确，不生成伪缺口；
- §14.4 只回答 module-side receptacle/connector guideline，不扩张 PMD；
- CPO 只作为特定 IA 反例，不绝对化；
- CMIS 条件和高速/低速层级不丢失；
- 没有新 ID/YAML/覆盖变化，全部 would_mark_covered=false；
- 自检与正文一致。
