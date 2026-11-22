# WQ001 attempt 1 裁决

## 结论

`revise_and_rerun`。五条候选桥的方向基本正确，但尚未满足本包的严格停止条件。

## 保留

- 保留 B1–B5 五条候选关系及四段链条。
- 保留成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值、ports/RU 等为空缺。
- 保留 PQ009 只作为待验证问题、`would_mark_covered: false`。

## 必须修正

1. 全文只允许出现 `WQ001`、`TQ002`、`PQ001`、`PQ002`、`PQ009` 五个 QID；删除合同外 QID。
2. B1 的关系强度降为“规范结构支持（含单产品实例）”。标准与实例支持映射结构，但不能直接证明普遍因果。
3. B4 必须明确：route-side 需求来自 TQ002；physical-side 机制来自冻结的 OIF §7.2.1/Table 4，PQ002 裁决只用于确认该表属于 engine-to-substrate 物理装配层、不是 Media Interface。不得把“双方引用同一来源”描述成两份独立证据。
4. B5 删除“管理/供电路径分层使热插拔可作为服务事件独立处理”这类未由来源直接支持且非桥接必需的句子。
5. 不得写 WQ001 已覆盖；只可写“形成五条 draft-only 候选关系”。

## 状态

- canonical write：false
- coverage change：false
- new question IDs：false
