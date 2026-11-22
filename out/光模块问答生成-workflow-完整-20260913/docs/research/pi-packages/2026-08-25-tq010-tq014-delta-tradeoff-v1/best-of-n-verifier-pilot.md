# Best-of-N + Verifier 在 Pi / CodeBuddy 研究流程中的小样

## 1. 结论

可以使用，但必须把任务按“可验证性”拆开。不是简单让 Pi/CodeBuddy 多写几份，再让同一个模型挑一篇最顺眼的。

```text
冻结问题、来源、schema
        ↓
确定性编译层
36 字段 comparison matrix / YAML / ID / UNKNOWN / cell closure
        ↓
多候选生成层
Pi × 3 独立草案 + CodeBuddy hy3 × 1 独立草案
        ↓
逐主张 verifier
证据蕴含、scope、状态、实例隔离、树映射、禁止外推
        ↓
claim-level selection / merge
        ↓
Kimi + Cursor + Codex 人工裁决
```

## 2. 哪些部分适合 Best-of-N

高度适合：

- 从同一冻结输入生成结构化 delta 候选；
- 发现遗漏的 UNKNOWN、promotion blocker 和验证问题；
- 为 observed difference 提议物理格/facet；
- 检测某一候选是否把 product label 当事实；
- YAML/schema、ID、来源、字段、状态等约束满足。

不适合由 self-verifier 单独决定：

- 某路线“更优”；
- 功耗、成本、良率、成熟度等无同条件对照结论；
- 公司受益、客户采用、供应关系；
- 多个候选共享同一行业假设时的真伪。

## 3. 本轮候选与角色

| 角色 | 运行 | 边界 |
|---|---|---|
| Generator P1–P3 | Pi / deepseek-v4-flash，3 次独立无 session | 同一合同和来源；只生成语义候选 |
| Generator C1 | CodeBuddy / **hy3**，1 次无工具无 session | 同一合同和来源；不写文件 |
| Deterministic verifier | Miniconda Python | 计算 36-field matrix、schema、ID、UNKNOWN、tree cell closure |
| Semantic verifier | CodeBuddy hy3 + Kimi + Cursor | 逐主张核 evidence entailment 与 scope，不选整篇文风 |
| Gate owner | Codex | 合并被证实的原子主张，冲突退回 UNKNOWN |

CodeBuddy 本轮及后续只允许 `--model hy3`，不允许 fallback 到其他模型。

## 4. 逐主张验证维度

每条 candidate claim 独立评分，不给整篇文档总分替代事实裁决：

| 维度 | 通过条件 |
|---|---|
| instance_identity | 左右实例与 comparison object 一致 |
| source_entailment | 冻结原文直接支持，或明确标 engineering_inference |
| scope_preservation | 公司、产品、端点、时间、条件、方向未扩大 |
| observation_state | observed/company-stated/normalized/unknown/inference 标对 |
| cross_instance_isolation | 未从相邻演示、对端或一般器件定义补值 |
| physical_mapping | cell ID 真实；无位置则 UNMODELED，不强塞 |
| comparison_fairness | 优劣主张有同速率/reach/BER/FEC/温度/功耗边界 |
| company_relation | 能力、供应、路线服务三类关系未混淆 |

裁决：

- 全部通过：accepted candidate claim；
- 可机械修正：corrected；
- 证据不足或 verifier 分歧：UNKNOWN / human review；
- 违反实例或因果边界：rejected。

## 5. 不采用“整篇 winner-takes-all”

某一候选可能在 36-field matrix 完整，但在物理映射上外推；另一候选可能漏字段，但正确识别 form factor 是 UNMODELED。

因此选择单位是原子主张：

```text
candidate documents
→ atomic claims
→ claim-level verification
→ accepted claim set
→ adjudicated effective text
```

不同候选冲突时不以多数票代替证据；若三份都共享同一错误假设，仍全部拒绝。

## 6. 评估方法

本轮记录：

- `candidate_valid_rate`：机械通过候选比例；
- `claim_accept_rate`：候选原子主张最终 accepted 比例；
- `unique_valid_claim_gain`：N>1 比单次多发现多少有效主张/缺口；
- `shared_error_count`：多个候选共同重复的同一错误；
- `verifier_false_accept`：人工 reviewer 推翻的 verifier 接受项；
- `selection_regret`：选择结果相对人工可接受 claim union 的遗漏。

这比宣称“多跑几次结果更好”更适合本项目。

## 7. 成功标准

只有以下同时满足，才认为 Best-of-N 值得进入常规流程：

1. 多候选增加有效缺口/主张，而不是只增加措辞；
2. deterministic + semantic verifier 能拦住跨实例和无证据外推；
3. Kimi/Cursor 推翻率低于单次 Pi 流程；
4. 总运行成本与人工复核时间可接受；
5. canonical、coverage、公司组仍由原有人工闸控制。
