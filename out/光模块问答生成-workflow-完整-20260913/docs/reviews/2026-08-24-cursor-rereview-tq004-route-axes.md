# Cursor 二次复核：TQ004 技术路线轴

- reviewer: Cursor Agent
- model: `auto`
- mode: `ask`（read-only）
- verdict: `PASS`
- reviewed_at: 2026-08-24

## 结论

首轮 Cursor/Kimi 的 P1 已落在唯一 controlling text、显式 errata 与 `README-FIRST.md` 入口上。raw、旧合同和 discovery 中保留的废止句属于不可变审计原文，不再是下一轮字典。

逐项结论：

1. generic LPO 与特定 `100G-DR-LPO` profile 的边界已关闭。
2. `other on-board` 与 `near-package NPO` 的字典边界已关闭。
3. TQ005/TQ006 不双计具名 MSA profile 的规则已关闭。
4. 已观察组合、公司平台能力披露、规范许可/边界三类证据已分开。
5. raw 不可变、显式 errata 和唯一 controlling text 的入口纪律已关闭。
6. Revision 1.0 与文件名 v1p2 的命名解释已关闭。
7. TQ007 只加深嵌套字段、不新增 QID 的边界已关闭。
8. 未发现 canonical 写入、新 QID 或 coverage 状态变化。

## 剩余项

- P0：无。
- P1：无。
- P2：裁决正文前半仍保留历史过程口径，后续必须只消费补充裁决与 effective text；raw、旧合同及 discovery 继续仅作审计；Intel 的 on-board 只能作为平台披露，不能当 NPO 定义。

## 放行范围

允许下一轮只展开 TQ005–TQ008，并继续执行 NPO 的 OIF 锚、MSA 不双计和三类证据分列。仍禁止 TQ009、WHY、公司归群、TQ014、canonical 写入、coverage 状态变化和新建 QID。
