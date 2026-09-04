# flows/SPEC-v1.4.md — v1.4 工单：红队 + 版本冻结 + 方法论重构

**来源**：output/Fable项目忽略项答复点评-Codex.md，优先序全盘采纳。
**本版总纪律（新增，适用所有产出）**：每个结论句必须可归类为"数据"或"推断"，
推断必须带等级与可推翻条件；禁用无证据的最高级修辞（"唯一/全网没人有/坐实/
定生死"类）；单侧未披露只能表述为"不可见"。

## 分工（kimi 配额耗尽本轮缺席）

| 路 | 承包方 | 任务 | 产出 |
|---|---|---|---|
| Y1 独立红队 | **codex** | 以推翻承重结论为唯一目标的全库措辞与推断审计 | flows/out/redteam-v1.4.md（只报告不改文件） |
| Y2 版本修正+报告 | Claude | README/易读版数字修正；报告 v1.4（待 Y1 结果并入） | 报告与修正提交 |
| Y3 回测协议 | claude sonnet | 无前视偏差回测协议设计+选一个试点事件 | flows/out/backtest-protocol-v1.md |
| Y4 时间观察模型 | codebuddy hy3 | edges.csv→关系事件表（五态模型） | flows/src/edge_timeline.py + flows/out/edge-timeline.csv |
| Y5 对手方候选审计 | cursor grok | 候选式（非蛮力）双侧核对清单 | flows/out/counterparty-audit-candidates.csv |
| Y6 设备观察池 | grok（并入Y5交付） | 设备指标同口径序列登记（仅登记禁结论） | flows/out/equipment-watch-pool.csv |

## Y1 红队契约（codex）

对象与火力分配（按影响加权，不平均用力）：
1. **推断边优先**：E036/E037/E038（判例#003/#004）、判例#002（PINEWAVE）、
   判例#005 素材（旭创双流）、判例#006（集团一C级候选）——每个主动构造至少
   一个替代解释，评估现有证据能否排除；排除不了的写明。
2. **结构性结论**：迁移拐点 2025-04、进料加工判"非纸面转口"、光芯片"真实技术源"
   一般贸易口径、省域代理（江苏≈旭创/四川≈新易盛）——逐条核数据与推断边界。
3. **全库越级措辞扫描**：output/*.md、flows/VERIFICATION-*.md、flows/out/*-NOTES.md、
   README、demo/DEMO-LOG.md——凡"坐实/证明/唯一/必然/全网/零成本/实证/合拢"类
   措辞逐处列 file:line，判定"措辞恰当/需降级/需删除"并给替换句。
4. 对实边只查披露口径混淆（占比分母/财年错位/币种），不重复逐位复核。
产出格式：发现={file:line, 原文, 问题类型, 严重度, 建议改写}；只写报告
flows/out/redteam-v1.4.md，**禁止直接修改任何其他文件**——裁决与执行归 Y2。

## Y3 回测协议契约（sonnet）

设计 flows/out/backtest-protocol-v1.md：
1. 协议模板：信息截止日/预测对象/方向与幅度阈值/期限/对照基准/成功失败判据
   六要素的定义规范 + 历史信息集重建规则（防前视：只用截止日前已披露文件，
   披露日以文件披露时间为准而非报告期）
2. 从项目现有数据中选**一个**可行试点事件并写出完整六要素实例。选择约束：
   所需历史信息集必须真实存在（注意：注册地四维海关数据 2025-01 起才有；
   2024 只有单维月度）。给出 2-3 候选、比较可行性、选定一个。
3. 明确写出"本协议未运行，试点为设计非结果"。禁止在本文档中预告回测会成功。

## Y4 时间观察模型契约（hy3）

flows/src/edge_timeline.py 读 output/edges.csv（含备注中压缩的多年序列，如
"2021:14.1%/2022:18.4%"与"FY2023:42.5%/FY2024:30.3%"格式），产出
flows/out/edge-timeline.csv：
`edge_id,供方,需方,year,pct_or_amt,observe_type`
observe_type ∈ {first_observed, observed, last_observed, confirmed_started,
confirmed_ended, censored}。判定规则（保守）：
- 仅 E008（NeoPhotonics-华为，有季度归零+终止依赖披露）标 confirmed_ended
- 其余序列首尾标 first/last_observed；跌出披露表的年份标 censored（不标 ended）
- confirmed_started 仅当文件明示合作起始年（如联讯"2018年起合作"）
自测：打印各 observe_type 计数 + 抽 3 条多年序列展开核对；解析不了的备注格式
如实列入 warnings，禁止硬凑。

## Y5+Y6 契约（grok）

Y5 counterparty-audit-candidates.csv：从 99 边台账筛**双侧核对候选**，字段：
`pair_id,A方,B方,A方披露(边ID),B方是否有披露渠道,产品匹配度,期间重叠,金额是否
可能过B方披露阈值,会计科目预判(原材料/固定资产/在建工程),优先级,理由`
规则：金额过阈值可能性低或科目为固定资产的直接标"预期不可见"；产出候选≤15 条
按优先级排序；**禁止任何"虚报"类预判**——本表只回答"哪里值得看"。
Y6 equipment-watch-pool.csv：登记设备类指标序列：
`series_id,主体,指标名,口径(订单签署/在手/发货/验收/收入确认),期间,数值,单位,
证据锚点,备注`——只登记已有数据点（ficonTEC 两个时点在手订单、联讯四期收入、
猎奇三年收入等），口径列如实标注，**表头注释声明"观察池：领先性未验证"**。

## 终验线（Y2，Claude）

Y1 发现逐条裁决（接受→改文件/驳回→记理由）；Y3 协议审查六要素完备性与
前视防护；Y4 抽 3 条对原文；Y5 抽 3 条候选评理由成立性；全量校验器 PASS；
报告 v1.4 落盘（数字 99/48+数据推断分离表述）。
