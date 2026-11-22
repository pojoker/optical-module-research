# Best-of-N + Verifier 人工裁决

## 结论

这个方法对当前 Pi / CodeBuddy 输出有明显帮助，但适用点是“发现遗漏与拦截结构化错误”，不是让模型多数票决定技术事实。

本轮四个独立候选共生成 40 条待审主张。确定性 verifier 只让 2/4 个候选完整通过，`candidate_valid_rate = 0.5`：P3 出现 YAML 枚举类型错误；CodeBuddy hy3 除同类枚举错误外，还把 D02/D03 的跨语义 raw label 对比误标为 `observed_difference`。这些错误都在语义合并前被拦住。

CodeBuddy hy3 语义 verifier 将 40 条主张归并为 14 个 normalized claim，并报告 5 条需纠正。但它仍把以下不同领域对象混成了 `capability_requirement`：

1. `8×200G` 是 Route Profile 外部链路轴值，不是 C5 物理能力刻面；
2. 补齐 D03 电职责是 `validation_gap`，不是已观察到的公司测试能力要求；
3. OSFP/QSFP-DD 是 `route_product_attribute`，当前物理树中 UNMODELED，不能直接变成物理能力格；
4. 补齐 D04/D05 等粒度器件披露是 `validation_gap`，不是该路线已证实需要的测试供应商能力。

因此 `verifier_domain_type_error_count = 4`。这证明 self-verifier 仍需领域模型和外部 reviewer，不能直接 promotion。

## 事实层裁决

保留以下三个差异/不可比结论：

- D02/D03：raw 描述形成可审计反差，但 `LRO` 与 `3 nm DSP` 不在同一语义层级；等粒度比较差异为 UNKNOWN。可提出 C5 内部候选刻面 `tx_retiming_scope`、`rx_retiming_scope`、`dsp_process_node_raw`。
- D04/D05：QSFP-DD800 与 OSFP 是直接观察到的 form-factor 差异；物理树当前没有对应格，保持 `UNMODELED`。
- D04/D05：SiPh MZM PIC 与 raw EML laser + generic photodetector 是复合端点描述差异；只能分别落到 C4/C1/C3 的候选刻面，不能当作等粒度器件替换或性能对照。

两张 TQ014 卡保留为 `partially_comparable`；优势、劣势、新瓶颈和替代方案继续为空。当前实例只能说明“路线描述不同”，尚不能说明“为什么一种更优”。

## 能力层裁决

不再使用一个笼统的 `capability_requirement` 容纳所有输出，改成三类：

- `physical_capability_requirement`：路线实例明确出现的物理格/刻面，可用于公司能力候选匹配；
- `route_product_attribute`：速率、lane、form factor、reach 等产品画像字段，可用于匹配公司产品，但不等于物理制造能力；
- `validation_gap`：为了完成比较而需要补充的资料或实验，不参与公司匹配。

本轮保留五个 physical requirement：C5 的 LRO 电职责刻面、C5 的 raw 3 nm DSP 刻面、C4 的 SiPh MZM PIC、C1 的 raw 1310 nm EML laser、C3 的 generic photodetector。form factor 重分类为 route product attribute；两项“补资料/测试”重分类为 validation gaps；`8×200G` 已在 Route Profile 轴中，不重复制造为 C5 requirement。

## 多候选的实际增益

- 单个 P1 覆盖了主要差异和 trade-off 边界，但把部分轴值/研究缺口错放到能力要求；
- P2 补出了 `LRO responsibility` 与 `3 nm DSP raw node` 两个有用刻面，并把 C1/C3/C4 的单侧观察标为 `axis_direct`；
- C1 补出了“等粒度器件披露缺口”，但需要重分类为 validation gap；
- P3 没有提供新的有效 normalized claim，且有枚举错误。

相对单次 P1，多候选增加 3 个独特且可保留/重分类的研究原子；但也显著增加运行和复核时间。建议只在“路线差异、WHY、公司归属”这类高风险节点使用 Best-of-N，普通格式化任务继续用单生成器 + 确定性 verifier。

## 状态

- canonical write：无；
- coverage change：无；
- formal RP：无；
- company group：无；
- new QID：无。
