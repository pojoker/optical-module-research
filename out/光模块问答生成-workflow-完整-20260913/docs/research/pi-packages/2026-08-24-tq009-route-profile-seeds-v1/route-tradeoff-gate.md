# 技术路线优劣的中间闸门

## 判断

“不同路线分别有哪些优势和劣势”应成为公司挂载前的中间步骤，但比较对象必须是完整 Route Profile/Seed，而不是把 EML、SiPh、LPO、OSFP、CPO 等不同维度名词放在同一张优劣表中。

现有问题树已有 TQ014，可承接这一层，不必新增 QID。建议执行关系为：

```text
TQ002/TQ003 场景约束与瓶颈
  ↓
TQ009 具体路线画像
  ↓
TQ010 相对基线的物理变化
  ├─→ TQ011 能力要求 → TQ012/TQ013 公司挂载
  └─→ TQ014 条件化取舍卡
          └─ 新瓶颈/验证问题可补充 TQ011
```

TQ014 的父问题仍可保持 TQ009；这里只调整研究执行顺序，不修改冻结问题树。

## 上游输入、铰链与下游生长

```text
上游：为什么产生这项取舍
TQ002 场景约束
  + TQ003 当前瓶颈
  + TQ009 路线画像
  + TQ010 物理变化
          ↓
中间：TQ014 条件化取舍铰链
  ├─ 在哪些条件下形成优势
  ├─ 为优势付出什么代价
  └─ 产生哪些新瓶颈与替代路线
          ↓
下游：这项取舍造成什么后果
  ├─ 优势 → 新的适用场景、采用价值与待验证假设
  ├─ 劣势 → 新瓶颈、改进问题、测试要求与替代路线
  ├─ 物理变化直接 → TQ011 能力要求，不等待取舍卡完成
  ├─ 新瓶颈/验证问题 → 补充 TQ011 能力要求
  └─ 能力要求 → TQ012/TQ013 公司候选与直接证据

反馈：new_bottleneck → TQ003 → 下一代 Route Profile
```

因此它不是简单的线性目录项，而是一个有多条入边、多条出边的因果节点。问题树提供主导航，Why Link 保存这些跨枝依赖；TQ014 不构成 TQ011 的前置门闩。

## 最小取舍卡

```yaml
route_profile_or_seed: RPS-D##
comparison_baseline: 明确的另一画像或参考样机
scenario_constraints: [距离, 带宽, 功耗, 密度, 成本, 维护]
solves:
  - claim: 解决什么约束或瓶颈
    evidence_status: fact | industry_consensus | engineering_inference
    evidence_refs: []
advantages:
  - dimension: power | density | reach | cost | manufacturability | serviceability | interoperability
    claim: ...
    conditions: []
    evidence_status: ...
    evidence_refs: []
costs_and_disadvantages:
  - dimension: ...
    claim: ...
    conditions: []
    evidence_status: ...
    evidence_refs: []
new_bottlenecks: []
alternatives: []
downstream_consequences:
  newly_suitable_scenarios: []
  adoption_hypotheses_to_test: []
  capability_requirements_to_research: []
  validation_questions: []
feedback_to_tq003: []
unknowns: []
no_unconditional_ranking: true
```

## 强制防错

- 优势/劣势必须相对一个基线和一组场景约束，不能写成路线固有属性；
- 一个 Route Profile 可能在功耗上占优、在可维护性上吃亏，不压缩成总分；
- 公司公告中的“降低功耗”等表述先记为 `company-stated`，没有可比测试不升级为普遍事实；
- 规范许可不证明可制造、量产、成本更低或市场占优；
- 不能从物理能力匹配倒推路线一定更优，也不能从路线优势倒推某公司必然受益；
- UNKNOWN 继续保留，不能用行业常识补齐。

## 与 Why 桥的关系

TQ014 记录条件化比较结果，WQ002/Why Link 记录“瓶颈为何提高某项工程选择的相对价值”的因果边，两者不得复制同一对象。Why 链解释：

```text
场景约束
→ 物理瓶颈
→ 某轴值/画像为何更有相对价值
→ 组件/接口/工艺如何变化
→ 获得什么优势、付出什么代价
→ 需要什么公司能力
```

这样“为什么采用某路线”与“哪个公司能服务它”之间有可审核的中间层，不会直接从技术名词跳到公司结论。
