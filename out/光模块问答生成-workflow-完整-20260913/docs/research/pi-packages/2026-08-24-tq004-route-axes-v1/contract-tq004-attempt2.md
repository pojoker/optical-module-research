# TQ004 attempt-2 收口合同

继承 `contract-tq004.md`，以下条款覆盖冲突部分：

1. 四个大方向写为：链路/接口画像、电信号处理架构、光子实现（嵌套字段）、封装/放置架构。
2. 光子实现至少分 platform/material、light source、modulator/emitter、detector、integration；
   EML 与 SiPh 必须明确为不同粒度，禁止直接作为互斥同级枚举。
3. 电架构的规范化值写 `retimed / linear / Tx-retimed-Rx-linear / direct-drive` 等职责分配；
   `LPO` 是 `linear + pluggable + LPO MSA interface profile` 的复合 alias，不是纯电轴值。
4. `CPO` 只归封装/放置轴，不固定 retimed/linear/direct-drive。
5. “低 BER 实现”不得归为电架构值。
6. 跨轴结论只限已观察组合，不得写每一轴值或所有组合。
7. 路线级功耗/成本/良率/密度排序只登记为 TQ014 的后续依赖，不挂 PQ010。
8. 原子主张不超过 14 条；全部唯一 draft_id、`would_mark_covered: false`。
9. 只允许现有 QID：TQ004–TQ009、TQ014、PQ010、WQ002、WQ003；不生成新问题 ID。
