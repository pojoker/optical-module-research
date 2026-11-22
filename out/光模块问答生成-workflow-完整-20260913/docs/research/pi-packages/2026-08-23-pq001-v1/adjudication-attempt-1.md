# PQ001 attempt-1 Codex 裁决

裁决日期：2026-08-23
流程结论：`process_pass`
内容结论：`changes_requested`
知识库动作：无；PQ001 继续未覆盖

## 已通过

- Pi 只使用冻结来源，未调用工具、未生成 YAML、未新增问题 ID；
- 5 条草案均为物理知识、只挂 PQ001、`would_mark_covered: false`；
- OSFP-specific 与公司/OIF 口径分开；
- cage、host PCB、host-side riding heatsink 没有被写成模块本体；
- 两条注记都有证据、下一步和局部停止条件。

## 返修项

### A1：外部光接口指南被过度推成“规范不定义完整光学信号标准”

S3 §14.4 可以直接证明外部光接口图示是 guidelines，但 OSFP Rev 5.22 同时包含 PMD block
diagrams。仅凭 §14.4 不能把整份规范概括成“只覆盖 form factor/连接/供电/机械热”或直接证明
它完全不定义光学信号层。D4、边界表、注记 2 和拒绝推论 3 都有同一范围扩张。

裁决：下一版只保留两个直接事实——管理接口另见 CMIS；§14.4 的连接器图示是 guidelines。
是否、由哪份文档定义完整光学 PMD，必须引用对应标准正文后再答。

### A2：OIF 公告的“可用于”被强化成“定义”

S5 官方公告说明 CMIS 可用于 pluggable/on-board modules，并描述基于 two-wire interface 的
host-to-module management communication；公告本身不是 CMIS 正文。D5 使用“定义”超出来源。

裁决：将主张降为“OIF 官方说明”；若要写规范级 Host/Media/management 边界，使用已发现的
OIF CMIS 5.4 正文快照。

### A3：缺少跨形态反例，仍不足以回答“一般边界”

attempt-1 能回答 OSFP 可插拔边界，但 PQ001 问的是光模块在系统中的边界。来源发现已找到 OIF
CMIS 5.4 的 Host/Media Interface 以及 OIF 3.2T CPO IA；后者可直接反证“光模块必然位于前面板
cage 中”。

裁决：冻结这两份官方正文后重跑 attempt-2。仍不追求行业唯一一句话定义，而采用“通用接口
骨架 + OSFP 可插拔实例 + CPO 反例”的答案形状。
