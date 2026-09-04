# 关系级时间聚合数据契约（R3，Claude 定稿，2026-07-23）

依 codex O2（roadmap-review-codex.md）：先契约后实现，防止关系视图制造伪连续性。

## 1. 关系键

- **不用显示名 groupby**。建别名映射表（实现内置 dict）：`Fabrinet(解匿)→Fabrinet`、
  `Ciena(解匿)→Ciena`、`Google(解匿)→Google`、`中际旭创(作为客户)→中际旭创`、
  `华为+海思→华为(含海思)`、`华为→华为(含海思)`、`博通(客户)→博通(Broadcom)`、
  `Broadcom→博通(Broadcom)`、`NVIDIA(客户)→NVIDIA`、`ficonTEC(罗博特科)→罗博特科/ficonTEC`、
  `PINEWAVE(关联方)→PINEWAVE`、`浙江粮油(出口代理)→浙江粮油`、
  `索尔思(Source Photonics)→索尔思(Source Photonics)`、`苏世博→索恩格(SEG Automotive)`、
  `罗博特科→罗博特科/ficonTEC`（v1.1 补，2026-07-24：R3 实现如实报告裸名 E076 未归一，
  经核 E076 与 E011/E012 为同一主体，补此规则）
- 匿名端点（含"匿名"字样）**不聚合**——v1.2 精确化（2026-07-24，修复红队 T01
  "R3 实现按同名标签跨期串接了 7 个匿名关系"）：**排名/代号标签跨年同名不等于
  同一法律主体**（不同年份年报的"客户一"可以是不同公司）。规则：
  - 默认：匿名端点关系**逐观测独立**——关系键追加 source_edge_id，每行独立成
    事件，observe_type 一律 `observed`，**不赋 first/last/censored 跨期语义**；
  - **例外表**（同一份文件内代号恒定、身份连续性由文件本身担保，可跨期聚合，
    须引用文件）：`集团一(匿名)`——联讯仪器 IPO 招股书同一文件内 2022/2023/
    2024/2025Q1 使用同一代号（E096-E098 同源），跨期同一性可审计。例外仅此
    一条；新增例外须修订契约并给出文件级依据。
- 关系键 =（规范化供方, 规范化需方），方向敏感（A→B 与 B→A 是两条关系）。

## 2. 期间键

- FY 与自然年**不混同**：year 字段区分 `2023`（自然年）与 `FY2023`（财年）两种
  period_type；同一关系两种口径并存时不去重、不比较大小，各自成序列。
- `2025Q1` 等季度期照原样保留，period_type=quarter。
- **排序键（v1.2 新增，修复红队 T02 "R069 输出 2023 observed→2024 last→
  2025Q1 first 时间倒置"）**：期间排序一律按**期末月**数值键——自然年
  `YYYY`→YYYY×100+12；季度 `YYYYQn`→YYYY×100+3n；FY 期间在自身序列内按
  FY 年份排序。排序键逐期间计算，禁止用循环外泄变量推断类型。实现必须内置
  固定断言：`2023 < 2024 < 2025Q1` 且同一序列 first/last 各仅出现一次。
- **first/last 按 (关系键, period_type) 分序列计算（v1.2 新增，红队 T03）**：
  同一关系的 year 与 fiscal 两条序列各自有独立的 first/last，不共用排序序列。

## 3. 同年多边冲突

- 同一关系键+同一期间出现多个事件（如 E010 与 E045 都载猎奇→旭创 2024）：
  金额/占比一致则合并为一行并列出全部来源边ID；不一致则保留多行并标
  `conflict=true`（不擅自择一）。

## 4. 关系级状态裁决

- first_observed/last_observed 在**关系级**重算（跨边）。
- 同期间某边 observed、另一边 censored：关系级取 **observed 优先**（有观测即非截尾）。
- confirmed_ended 仅当该关系**全部有效来源边**均达 confirmed_ended（v1.2
  强调，修复红队 T06：实现原为"任一边 ended 即判死"，多边关系会被过早判死；
  须改为全边判定。现实上仍只有 NeoPhotonics→华为，单边关系不受影响）。
- confirmed_started 需文件明示起始年（联讯"2018年起合作"型），标注来源。

## 5. 证据链保留

- 每个聚合事件行必须带 `source_edge_ids`（分号分隔）——禁止为连续性丢证据链。

## 输出

flows/out/relationship-timeline.csv：
`relation_id,供方,需方,period,period_type,pct_or_amt,observe_type,source_edge_ids,conflict`
自测：打印关系数/事件数/conflict 计数；抽验 猎奇→中际旭创（应跨 E010+E045 连成
2023-2025 序列）与 Fabrinet→Lumentum（E005+E068 与 E038 的 FY 序列）。
