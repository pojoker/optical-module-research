# 下一轮 TQ010 / TQ014 draft-only 验收合同

## 1. 共同边界

- 只使用 `route-profile-seeds-effective.yaml` 中的同实例值；
- `normalized` 必须带冻结映射规则，不能冒充直接观测；
- UNKNOWN 不补全；
- 不创建正式 RP、新 QID、coverage、canonical、公司群或路线排名；
- TQ010 与 TQ014 可并行起草；TQ014 不是 TQ011 的前置门闩。

## 2. TQ010：相对基线的物理变化

### 允许的答案形态

一张 `baseline_seed → target_seed` 的 delta card，逐项记录：

- 比较条件是否相同；
- 轴值差异；
- 组件、接口、工序、设备、测试职责的变化；
- 主张状态：observed / company-stated / normalized / engineering-inference / unknown；
- 证据引用与反证；
- 不能比较的字段及原因。

### 验收条件

1. 明确基线和目标实例，禁止跨实例拼接；
2. 对 36 个轴字段逐项判定 same / different / unknown / not-comparable；
3. 每个 physical delta 都引用至少一个轴差异或明确标为 engineering-inference；
4. 组件、接口、工序、设备、测试五层至少逐层检查，不要求每层都有变化；
5. 不从产品名或平台名推物理变化；
6. 输出所有 unresolved delta，并说明需要什么一手证据。

### 停止条件

当所有轴字段和五类 physical delta 都有状态，且没有未标注推论时，可以停止 draft；不能因此标记 TQ010 covered。

## 3. TQ014：条件化优势/劣势

### 允许的答案形态

使用 `route-tradeoff-gate.md` 的 trade-off card；如果基线不成立，允许且优先输出 `not_comparable` 卡。

### 验收条件

1. 明确比较画像/种子、场景约束和比较基线；
2. 至少检查速率、reach、BER/FEC、温度、功耗边界、密度、成本边界和维护边界是否同口径；
3. 每条优势/代价包含 conditions、evidence_status、evidence_refs；
4. 公司营销表述只能标为 company-stated，不升级为普遍事实；
5. 明确 `new_bottlenecks`、`alternatives`、`unknowns`；
6. 优势产生的适用场景/采用假设与劣势产生的新瓶颈/验证问题分栏；
7. 新生瓶颈写成反馈给下一轮 TQ003 的研究注记，不修改当前 TQ003 事实状态；
8. 不输出总分、无条件优劣或公司受益结论。

### 停止条件

满足以下任一条件即可停止 draft：

- 有同条件对照证据，完成带条件的 trade-off card；
- 证据不足，完成 `not_comparable` 卡并列清缺失字段与下一步来源。

两种情况都不能自动标记 TQ014 covered。

## 4. WQ002 与 TQ014 边界

- TQ014 保存比较对象、条件、优势、代价、新瓶颈和替代方案；
- WQ002/Why Link 保存“哪个瓶颈通过什么物理机制提高哪个工程选择的相对价值”的有序因果边；
- TQ014 可以引用 WQ002，不复制同一条因果主张为另一份事实对象。

## 5. 公司侧门槛

- TQ010 的 physical delta 可以直接进入 TQ011；
- TQ014 发现的新瓶颈/验证问题只作为 TQ011 的补充输入；
- TQ010/TQ011 未完成前，`capability_match_candidate` 关闭；
- TQ013 路线直接证据未完成前，不产生 confirmed route service。
