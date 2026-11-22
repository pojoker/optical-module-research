# TQ002 attempt-2 修订合同

完整继承 `contract-tq002.md`，并增加以下硬约束：

1. 所有原子主张必须显式包含：`draft_id`、`system: route`、`question_id: TQ002`、
   `claim_type`、`statement`、`evidence_ids`、`boundary`、`rejected_inference`、
   `would_mark_covered: false`。
2. 主结论/主矩阵中 IEEE reach 只使用 T1 已核验的 final-standard 摘要范围；T2 的 10/40 km
   历史 objectives 只进入一条挂 `TQ002` 的研究注记。
3. 事实支持状态与决策充分性分开：例如 hot-pluggable 是 supported fact，但“降低维护成本”
   是 not quantitatively closed。
4. connector 位置/实现未固定，不等于 service/replacement method 未固定。
5. lane configuration 只能写 port flexibility / density input，不得作为单位面积密度指标。
6. 所有研究注记只挂 `TQ002`；不得挂 TQ001、PQ001 或未来问题。
7. 原子主张不超过 14 条；不生成路线选择或公司结论。
8. 最终自检逐项回应 attempt-1 六个错误。
