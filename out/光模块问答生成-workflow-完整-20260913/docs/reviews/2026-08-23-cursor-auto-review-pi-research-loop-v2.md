# Cursor Auto 对 Pi 研究循环 v2 的首轮复核

日期：2026-08-23
Reviewer：Cursor Auto（`claude-fable-5-thinking-high` 与 `composer-2.5` 均因账户用量限制未能运行）
结论：`changes_requested`

## P1 阻断项

1. attempt-2 合同允许 `system: 研究框架`，与项目只有“物理知识/技术路线”两套体系的不变量冲突；
2. attempt-2 的 D3 同时存在第三体系、无快照却标直接事实、挂错 RQ000 三个问题，Codex 裁决只抓到其中一部分；
3. attempt-2 的停止结论声称没有跨体系污染，但正文 D3 与此矛盾；
4. 当前二元覆盖代码未改变，不能批准把 PQ001 草案提升到知识库；下一步最多只能另开 draft-only 包。

## P2 重要项

- “研究框架”应属于主张/展示类型，而非知识体系；
- RQ000 注记不应把 IEEE 项目目标带进基础定义的预期答案；
- attempt-2 注记把多个工作揉成一条；
- S5 的精细归属更接近 TQ005，但本轮不应提升进问题树；
- `run.yaml` 状态落后于实际进度；
- 只有运行自述，没有保存完整命令；
- 现有 append-ready 模板仍允许 `url` 与 RB 路线引用，正式提升前必须继续视为阻断；
- 存量 KN 方案所称 `legacy_narrative` 不是当前代码真实状态：当前扫描器只是把缺失体系默认成物理知识，并忽略缺失研究问题引用。

## 对报告第 15 节的回答

1. `docs/research/pi-packages/` 不污染事实账本；可复现性当时仅部分满足，因为缺完整命令；
2. `--no-tools --no-context-files` 能关闭 Pi 的通用工具边界问题；
3. Codex 裁决遗漏 D3 的主张类型/QID 问题和停止结论自相矛盾；
4. RQ000 合成状态与 A 阶段顺序合理；
5. 不机械映射存量 KN 可以防止虚假覆盖，但现有二元渲染仍然脆弱；
6. 默认写研究注记、不发 CQ 的方向合理，但仍需防止跨层注记；
7. RP 冻结范围基本完整；
8. 修复合同并补 S4 快照后，可以启动 PQ001 的 draft-only 研究包；不能批准 promotion。

## Reviewer 实际检查

Cursor 只读检查了研究包、报告、问题树、扫描/渲染实现和现有模板，并使用指定 Miniconda Python
运行项目扫描；当时不变量 ①–⑭ 全绿、`refs/` 8/8，文档差异检查通过。

## 本轮处理映射

- P1.1–P1.3：通过 attempt-3 合同与裁决关闭；
- P1.4：保留为实施阻断，报告明确禁止 promotion；
- 完整命令：新增 `command-attempt-3.txt`、`command-attempt-4.txt`；
- `run.yaml`：同步到 attempt-4；
- `legacy_narrative`：报告改为建议标签并写明当前真实代码行为；
- 模板、二元覆盖、S4 快照：仍列为进入正式落库前的阻断项。
