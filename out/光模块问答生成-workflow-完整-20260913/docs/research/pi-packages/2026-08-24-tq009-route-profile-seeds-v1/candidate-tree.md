# 可挂公司数据的问题树候选结构

## 1. 目标形态

问题树继续只有两套知识体系；Why 是二者之间的桥，公司是树外唯一实体，通过关系挂入。

```text
RQ000 什么是光模块？
├─ 物理知识体系
│  ├─ PQ001–PQ003：系统边界与参考样机
│  ├─ PQ004：组件
│  ├─ PQ005 / PQ009：接口与验收指标
│  ├─ PQ006：材料与结构
│  ├─ PQ007：制造/装配工序
│  ├─ PQ008：设备
│  └─ PQ010：通用骨干与路线可变部分
│
├─ 技术路线体系
│  ├─ TQ001–TQ003：约束与瓶颈
│  ├─ TQ004–TQ008：正交选择轴及轴值字典
│  ├─ TQ009：同一实例的 Route Profile Seed / Route Profile
│  ├─ TQ010：相对基线的物理变化
│  ├─ TQ011：变化要求的物理能力
│  ├─ TQ012：能力匹配候选公司
│  ├─ TQ013：路线直接证据确认公司
│  └─ TQ014：有条件的优势、代价、新瓶颈与替代方案（与 TQ011 并行，不作门闩）
│
└─ Why 桥（不是第三套知识体系）
   ├─ WQ001：系统需求 → 物理约束
   ├─ WQ002：瓶颈 → 路线选择相对价值
   ├─ WQ003：路线选择 → 组件/接口/工序/设备变化
   └─ WQ004：物理变化 → 公司能力要求与证据门槛
```

## 2. 树与数据对象分离

```text
问题节点
   ↓ answered_by
知识主张 / 路线画像 / Why 链
   ↓ references
物理格、证据快照、公司挂载关系
   ↓ points_to
唯一公司实体
```

树负责导航“接下来问什么”；对象负责保存“已经知道什么”；公司关系负责表达“证据把哪家公司连到哪里”。三者不互相冒充。

## 3. Route Profile Seed 下的内部结构

```text
RPS-D##（同一产品或演示实例）
├─ TQ005 外部链路字段
├─ TQ006 电处理职责
├─ TQ007 光子实现
│  ├─ platform/material
│  ├─ light source
│  ├─ modulator/emitter
│  ├─ detector
│  └─ integration
├─ TQ008 放置位置与 form factor
├─ UNKNOWN 字段清单
├─ TQ010 物理变化（下一轮）
├─ TQ011 能力要求（下一轮）
├─ TQ014 条件化取舍卡（与 TQ011 并行；需引用 TQ002/TQ003/TQ010）
└─ 公司挂载
   ├─ 实例主体：直接来源
   ├─ 候选能力匹配：TQ011 × points（尚未开放）
   └─ 已确认路线服务：路线级直接证据（当前为空）
```

## 4. 公司实体建议

公司只保留一份注册信息，页面按关系投影视图：

```yaml
company_entity:
  company_id: future-stable-id
  canonical_name: Coherent
  aliases: []

attachments:
  - relation_type: physical_capability_point
    target_id: C1
    point_id: P...
    evidence_status: ...
  - relation_type: route_service_evidence
    target_id: RPS-D01
    source_ids: [S1]
    scope: exact_product_instance
```

这里仅示意未来 schema；本轮不创建公司 ID、不改 CSV/YAML。

## 5. 这棵树如何继续长细

每个种子的 UNKNOWN 和 `promotion_blockers` 会产生挂在既有问题下的研究注记，而不是立即增加 QID。例如：

- TQ009：3 nm DSP 演示的 Rx 是否 retimed？
- TQ009：SiPh MZM 互操作端点的 detector 与 light source 是什么？
- TQ010：LRO 相对 retimed 参考样机减少、迁移或新增了哪些部件和测试点？
- TQ014：在 500 m 数据中心互连约束下，该画像相对基线的功耗、可维护性和制造代价是什么？
- TQ011：支持 8×200G SiPh OSFP 需要哪些可验证的设计、制造和测试能力？

当多个种子反复暴露同一种缺口，并且既有 TQ 无法表达时，再提议新 QID。这样问题树从基础问题逐层长出，而不是被产品名和公司名打散。

## 6. 取舍铰链不是普通叶子

TQ014 有多条上游依赖：TQ002/TQ003 提供场景与瓶颈，TQ009 提供比较对象，TQ010 提供物理变化。它的输出再分流：

- 优势长出适用场景和采用价值的验证问题；
- 劣势长出新瓶颈、改进问题、验证要求与替代路线；
- TQ010 物理变化可直接进入 TQ011，不等待取舍卡；
- TQ014 产生的新瓶颈和验证问题可补充 TQ011；
- 新瓶颈反馈到 TQ003，触发下一代路线研究。

因此展示仍可保留树形主干，但数据层应以 Why Link 表达这个有入边、出边和反馈边的因果图。
