# TQ004 post-adjudication 唯一有效口径

本文件是本包唯一 controlling text；必须先读 `README-FIRST.md`。raw 仅作审计原文。

## 1. 当前答案

技术路线不是一个热词，而是四组字段的组合：

1. `TQ005 链路/接口画像`：速率、lane/波长、介质、PMD、reach；
2. `TQ006 电信号处理架构`：retimed、linear、Tx-retimed/Rx-linear、direct-drive 等职责分配；
3. `TQ007 光子实现`：platform/material、light source、modulator/emitter、detector、integration；
4. `TQ008 封装/放置架构`：pluggable、other on-board、near-package NPO、CPO；
   pluggable 下再记 OSFP/QSFP-DD。

“正交”只表示分析时分别记录，不表示任意组合均可行。

## 2. 三个最重要的术语修正

- `EML` 是 InP DFB+EAM 的发射器件实现；`SiPh` 是 PIC/集成平台。二者属于 TQ007 内不同
  子字段，不是互斥同级枚举。
- `LPO` 泛称是复合 alias：`electrical=linear + packaging=pluggable`。本轮冻结的
  `100G-DR-LPO Revision 1.0（下载文件名含 v1p2）` 只是一个具名 profile 实例，不能吞掉其他
  行业 LPO 用法。正确的电架构比较是 `retimed vs linear`。
- `pluggable / NPO / CPO` 可以在 TQ008 广义放置轴上比较；真正错层的是
  `OSFP/QSFP-DD vs CPO`。比较 `LPO vs CPO` 前，必须先把 LPO 拆出 `packaging=pluggable`。

## 3. 已经观察到的路线差异

本轮已经有实例级观察，但还没有建立完整路线画像库：

- 已观察组合：同一 1.6T-DR8、OSFP、SiPh、8×200G 条件下，Coherent 官方演示同时出现 LRO 与 3 nm DSP
  retimed，说明电架构可独立变化；
- 已观察组合：同一 800G-DR8+ 链路族中，SiPh MZM PIC + QSFP-DD800 与 EML/PD + OSFP 可以互操作，说明
  链路目标不唯一决定光子实现和 form factor；
- 公司平台能力披露：Intel 官方页同时把 SiPh 描述用于 pluggable transceiver、stand-alone on-board 和 co-packaged
  OCI，说明光子平台不等于封装位置；
- 规范许可/边界证据：LPO MSA 明确 form-factor agnostic，并允许多种 opto-electronic implementation，说明 linear
  电架构不固定具体 pluggable form factor 或光子实现。

这些只能证明已观察组合，不证明完整笛卡尔积、量产成熟度或路线优劣。

## 4. 问题树现在处于哪里

- 已有：TQ004 的轴字典与少量跨轴实例；
- 尚未展开：TQ005–TQ008 每一轴的完整取值、定义与证据；
- 尚未形成：TQ009 的具体 Route Profile；
- 尚未比较：TQ010 相对基线改变的组件/接口/工序/设备；
- 尚未解释：WQ002/WQ003 的瓶颈→选择、选择→物理变化；
- 尚未进入：TQ011–TQ013 的供应链能力和公司群。

所以，“技术路线不同”已经有了少量观察和完整的数据槽位，但还没有成为可系统比较的路线画像。

## 5. 后续生长顺序

`TQ004 轴字典 → TQ005–TQ008 轴值 → TQ009 路线画像 → TQ010 物理差异 → WQ002/WQ003 WHY → TQ011–TQ013 公司能力`

路线级功耗、成本、良率、密度与新瓶颈只有在 TQ009 画像固定后才能进入 TQ014 比较，不能在
TQ004 阶段提前排名。

## 6. 下一轮 TQ005–TQ008 强制边界

1. `TQ007` 只在现有问题内部加深五类嵌套字段，不改问题树、不生成子 QID。
2. `TQ008` 至少分为 `pluggable / other on-board / near-package NPO / CPO`；不得把 Intel
   stand-alone on-board 与 OIF NPO 合并，NPO 必须标注 OIF 文件锚。
3. `TQ005` 记录 optical PMD、media、reach、lane/wavelength 等链路边界；`TQ006` 记录
   host-module electrical signal 与处理职责。具名 MSA profile 只作 alias/reference object，
   不得在两轴各计为一个独立轴值，也不得生成第五根轴。
4. `direct-drive` 等 OIF framework 候选只写候选，不写成量产菜单。
5. 必须分开“已观察产品/演示组合”“公司平台能力披露”“规范许可或沉默边界”。

## 7. 状态

- `canonical_write_performed: false`
- `coverage_status_changed: false`
- `new_question_ids_created: false`
- 本文件与 raw 均为 draft-only，TQ004 未标记覆盖。
