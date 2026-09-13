# TQ002 attempt-1 Codex 裁决

结论：`changes_requested`

## 通过部分

- 六类约束已经分开；
- OSFP form-factor、单产品值、CPO framework 目标三类功耗证据没有混成一个数字；
- 成本和维护没有编造金额；
- 没有跳到路线选择、公司归群或市场份额。

## 必须修正

1. **原子主张未遵守字段合同**：缺少显式 `draft_id/system/question_id/claim_type/statement/
   evidence_ids/boundary/rejected_inference` 字段，不能进入统一审阅器。
2. **历史目标与最终标准距离混在主结论**：10/40 km 只出现在 T2 历史 objectives；最终
   802.3df 摘要未列出。主矩阵只使用 T1 已核验范围，10/40 km 放 TQ002 研究注记。
3. **缺口挂错 QID**：G3 不应挂 TQ001/PQ001；成本、维护、最终 reach 核验都仍属于 TQ002。
4. **“未闭合”层级混乱**：hot-pluggable 等事实可以证实，但“是否降低生命周期成本”未闭合。
   必须把事实支持状态与决策充分性分开。
5. **由 connector 未固定推导服务方式未固定过强**：只能说 optical connector 位置/实现未由
   该 IA 固定；不能直接得出替换/维修方式。
6. **lane 配置不是密度指标本身**：可写成 port configuration flexibility 或潜在密度输入，
   不能等同于单位面积密度。

## 最终稿要求

- 不超过 14 条原子主张；
- 所有研究注记只挂 `TQ002`；
- 每条明确区分“事实已支持”与“定量比较未闭合”。
