# 全量公司可放置树 / 图草案

## 当前判断

现在已经可以把当前采集到的全部 271 条公司数据放进同一张草稿图。这里的“放进去”有三种不同结果：269 条进入人工复核、其中 258 条可细分到引语支持的 facet，另有 11 条合格但只能停在原物理格；剩余 2 条进入阻断队列。系统没有为了追求满覆盖而制造公司能力事实。

公司不是物理格或路线的子节点，而是通过证据断言连接它们：

```text
物理知识体系                          技术路线体系

Physical Cell                        Route Profile
  └─ Capability Facet                  └─ Route Requirement
       ▲                                      ▲
       │ POINT_PROPOSES_FACET                 │ candidate match
Company ─ Evidence Point ─ Capability Assertion
       │
       ├─ subject scope
       ├─ capability role
       └─ maturity marker（不自动继承）

WHY 桥：scenario constraint → mechanism → trade-off → requirement
```

`POINT_DECLARED_CELL` 只表示源数据原来声明的格位；`POINT_PROPOSES_FACET` 和 `POINT_PROPOSES_ROLE` 才是带精确引语 span 的候选能力断言。它们仍需人审。`ASSERTION_CANDIDATE_MATCHES_REQUIREMENT` 也不等于 `COMPANY_SERVES_ROUTE`。

## 全树可放置程度

| 层次 | 当前结果 | 边界 |
|---|---:|---|
| 源公司证据点 | 271 | 每条恰有一个 graph disposition |
| 原物理格声明 | 271 | 来源于 `points.csv`，不是新增推断 |
| 合格挂载候选 | 269 | 仍需人审 |
| 阻断队列 | 2 | P040 定义性材料；P193 参股公司主体 |
| facet-explicit point | 258 | 引语精确 span 支撑 |
| cell-only point | 13 | 含 2 条 blocked，不强行细分 |
| facet assertion | 484 | 216 个不同 facet |
| role-explicit point | 170 | 共 272 个 role assertion |
| 路线试挂 point | 56 | 沿用上一轮裁决 |
| requirement/属性候选边 | 6 | 泛 scope 或单属性候选 |
| related-facet 边 | 16 | 不形成 requirement match |
| WHY 因果边 | 0 | 缺少受控 trade-off 证据 |
| 公司服务路线边 | 0 | 缺少 Route Service Evidence |

## 物理树

以下括号为 `point / facet-explicit / cell-only`：

```text
材料
├─ M1 衬底 (6/6/0)
├─ M2a InP 量子阱外延/掩埋再生长 (4/4/0)
├─ M2b GaAs/VCSEL 外延 (1/1/0)
├─ M2c 锗/硅基选区外延 (0/0/0) [无数据]
├─ M3 靶材/MO源/特气/光刻耗材 (16/16/0)
├─ M4 无源材料 (7/7/0)
└─ M5 高速板材 (3/3/0)

芯片
├─ C1 激光器芯片 (12/12/0)
├─ C2 VCSEL (6/6/0)
├─ C3 探测器芯片 (5/5/0)
├─ C4 硅光 PIC (6/5/1)
├─ C5 电芯片 (10/10/0)
├─ C6 可调谐激光器/相干光组件 (5/5/0)
└─ C7 时钟/频控器件 (1/1/0)

封装与组件
├─ P1 芯片封装 (9/9/0)
├─ D1 TOSA (6/4/2)
├─ D2 ROSA (4/3/1)
├─ D3 BOSA (6/5/1)
├─ D4 陶瓷管壳/TO 管座 (4/4/0)
├─ D6 隔离器 (6/6/0)
├─ D7 透镜/微光学 (8/8/0)
├─ D8 AWG/波分复用 (8/8/0)
├─ D9 FAU/MPO 连接 (17/17/0)
├─ D10 陶瓷插芯/套管 (3/3/0)
├─ D11 滤波片/薄膜 (4/4/0)
├─ D12 光引擎/COB 组件 (10/9/1)
├─ D13 温控元件 (2/2/0)
├─ B1 光模块 PCB (17/16/1)
└─ B2 结构件 (9/8/1)

模块与制造服务
├─ MOD1 数通直检模块 (23/20/3)
├─ MOD2 相干模块 (8/8/0)
├─ MOD3 电信/接入模块 (15/14/1)
└─ EMS1 模块代工 EMS (3/3/0)

设备
├─ EQ1 外延设备 (4/4/0)
├─ EQ2 光刻/刻蚀 (5/5/0)
├─ EQ3 贴片/固晶 (5/5/0)
├─ EQ4 耦合设备 (3/3/0)
├─ EQ5 键合设备 (1/1/0)
├─ EQ6 AOI/在线检测 (3/3/0)
├─ EQ7 测试设备与仪器 (6/5/1)
└─ EQ8 气密封装设备 (0/0/0) [无数据]
```

## 两套知识与 WHY 桥的真实进度

物理体系已经能承载全部当前数据，但路线体系仍只对 C1、C3、C4、C5、MOD1 的 56 条 point 做过试挂。6 条 requirement/product-attribute 候选和 16 条 related-facet 关系可以展示为虚线候选，不应解释为某公司服务某路线。

优势/劣势应处在 WHY 桥中间，而不是直接挂在公司或组件名下：上游问题解释“什么场景约束和工程机制带来该优势/代价”，下游问题解释“该权衡为何要求某路线属性、物理 capability 和制造/测试变化”。当前受控比较证据不足，所以这部分保持 0 条实例化因果边是正确状态。

## 下一步不是继续扩关键词

要让这棵树真正支持公司路线分组，下一轮应优先完成：

1. 给 155 个公司字符串建立稳定 `company_id` 与集团/子公司/参股关系；
2. 人审 484 个 facet assertion 和 272 个 role assertion，优先处理 13 条 cell-only；
3. 为技术路线补 Route Service Evidence，而不是从物理格重合推断路线服务；
4. 为优势/劣势补同条件比较证据，实例化 constraint → mechanism → trade-off → requirement；
5. 通过验收后再决定哪些 draft assertion 可以增量写入 YAML，不覆盖 canonical。
