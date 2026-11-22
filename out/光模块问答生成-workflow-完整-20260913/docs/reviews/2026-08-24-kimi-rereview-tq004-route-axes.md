# Kimi 二次复核：TQ004 技术路线轴

- reviewer: Kimi Code
- model: `kimi-code/k3`
- mode: read-only
- verdict: `PASS`
- reviewed_at: 2026-08-24

## 结论

首轮两份评审提出的修正项已经在补充裁决、显式 errata、唯一入口与 controlling text 中落地；没有残留 P0 或 P1。

八项检查均已关闭：

1. 泛称 LPO 已归一为 `linear + pluggable`，`100G-DR-LPO Revision 1.0（下载文件名含 v1p2）` 仅是具名 profile 实例。
2. `other on-board` 与 `near-package NPO` 已分开，NPO 必须锚定 OIF 定义。
3. TQ005 记录 optical PMD/media/reach/lane 等链路边界；TQ006 记录 host-module 电信号及处理职责；具名 MSA 只作 alias/reference，不双计。
4. 已观察组合、公司平台能力披露、规范许可/边界证据已经分开。
5. raw 保持不可变，`README-FIRST.md`、显式 errata 与 `run.yaml` 共同确定唯一 controlling text。
6. 正式标题 Revision 1.0 与下载文件名 v1p2 已统一解释。
7. TQ007 只在现有问题内增加嵌套字段，不新增子 QID。
8. 未发现 canonical 写入、新 QID 或 coverage 状态变化。

## 剩余项

- P0：无。
- P1：无。
- P2：TQ005 可补冻结 CMIS；TQ006×TQ008 可补更强的电架构与封装交叉证据；TQ007 落字典前补 VCSEL 等器件的冻结来源。

## 放行范围

允许下一轮只展开 TQ005–TQ008。仍禁止 TQ009、WQ002/WQ003、TQ011–TQ013、TQ014、canonical 落库、coverage 状态变化和新建 QID。
