# Kimi 增量语义复核：系统需求→placement 覆盖缺口候选

日期：2026-08-31
continuity handle：`session_9b3c8af2-d10c-4713-a573-ed0e37e69a03`
会话方式：延续原 Kimi 会话；未创建替代会话
对象：`COVERAGE-GAP-CANDIDATE-01`
初审 verdict：`PASS_WITH_FIXES`
delta verdict：`PASS`
canonical 变更：`0`

## 已核对材料

- `docs/research/expert-question-coverage-audit-v1.yaml`
- `docs/research/expert-question-coverage-gap-candidate-v1.yaml`
- `docs/research/expert-question-coverage-gap-human-audit.md`
- QUP05-NQ01、QUP05-NQ03
- QMID01-NQ09
- `docs/research/expert-question-contract-v1.yaml`

## A–F 结论

| 项目 | verdict | 结论 |
|---|---|---|
| A 真实缺口/去重 | PASS | 近邻问题分别处理电通道、同系统功耗闭合和电职责路线；本候选处理 fabric 服务目标到 placement 决策边界，研究对象不同 |
| B 变量逻辑 | PASS | 修订后以服务目标为控制量、topology/radix/port/reach/placement 为场景变量、switch/stage/port count 为结果，不再恒等锁死 |
| C 决策规则 | PASS | 无权重只报 Pareto；只有显式权重、硬约束和成本边界才允许总排序或反转 |
| D 验收/证伪/分支 | PASS_WITH_FIXES | `合理敏感性范围` 未锚定，必须在读取模型输出前预注册区间和权重集 |
| E 证据计划 | PASS | 公开参考架构→可复现参数模型→保留 private/measurement dependency 的三级计划现实 |
| F 是否入队 | conditional yes | 修复、用户显式批准、分配不覆盖现有 30 问的新正式 ID 后才可进入 portfolio |

## 必修项

把敏感性区间与任何权重集改为在建模输出可见之前预注册并冻结，防止事后调参制造“反转/不反转”。

## 状态建议

- `research_status: ready_for_research`：公开参考架构与参数模型足以启动第一阶段；若关键故障率、维护或成本输入无法闭合，再降为 `requires_private_or_factory_data`。
- `portfolio_admission: false` 保持到用户显式批准。
- 本次评审只确认候选值得继续，不构成正式问题或 canonical 授权。

## 增量复核

必修项落实后已在同一 continuity handle 请求 delta review。Kimi 核对 `preregistration_rule`、新增 acceptance 条款、falsifier、research status 与 admission 状态后给出 `PASS`：

- 唯一必修项准确关闭，无残余；
- 允许 `review_status` 升为 `externally_reviewed`；
- `research_status: ready_for_research` 仍准确；
- `portfolio_admission` 必须继续为 `false`，外审通过不构成用户入队授权；
- canonical 保持 0。
