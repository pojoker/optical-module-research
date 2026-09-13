# PQ001 attempt-2 Codex 裁决

裁决日期：2026-08-23
流程结论：`process_pass`
内容结论：`minor_changes_requested`
知识库动作：无；PQ001 继续未覆盖

## 已通过

- 成功形成“CMIS 条件骨架 + OSFP 可插拔实例 + 3.2T CPO 反例”；
- Host Interface 保持为高速数据接口，没有与低速管理通信混淆；
- CPO module 与 ASIC 虽可近邻/共 substrate，仍写成不同对象；
- OSFP/CPO/公司口径均保留主体和条件；
- 无新问题 ID、YAML 或覆盖状态变化。

## 返修项

### B1：摘要把 card-edge 错配到 cage

摘要写“OSFP 以 card-edge 配 host cage”，而规范 §3.5 的直接配对关系是 module card-edge pads 与
host connector；cage 是机械容纳/配合对象。正文图和 D2 已写对，但摘要必须改。

### B2：来源摘要的“可有 integrated heatsink”不准确并制造无效注记

OSFP Rev 5.22 印刷页 17 明确：标准 OSFP/OSFP800/OSFP1600 module `includes` air-cooled
integrated heatsink；OSFP-RHS 系列接触属于 host 的 riding heatsink；标准 OSFP 还可选额外 riding
heatsink。`sources-attempt-2.md` 写成“标准 OSFP 可有”，导致注记 2 虚构“无 integrated heatsink
时归属不明”。

裁决：attempt-3 修正来源上下文并删除该注记。

### B3：§14.4 完整上下文已经能关闭注记 1

本地快照印刷页 146 明确展示 module-side optical receptacle/channel orientation，并说明接口图示
为 guidelines；不同连接器方案和安装几何可变。无需再声称“未读取完整页”。

裁决：attempt-3 把这一信息直接放入 OSFP 实例边界，删除注记 1；不继续推断完整 PMD 标准范围。

### B4：CPO “无前面板 cage/card-edge”应写成证据支持的比较句

S5 直接证明 module 可靠近 ASIC、共 assembly substrate 或 embedded on board，并使用 pigtail；
它足以反证“前面板 cage/card-edge 是通用必要边界”，但不需要声称该 IA 每个实现都绝对“无”
这些实体。

裁决：改为“该 IA 展示了不以前面板 cage/card-edge 作为模块必要边界的实现”。
