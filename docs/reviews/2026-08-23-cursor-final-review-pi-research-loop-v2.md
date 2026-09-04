# Cursor 对 Pi 研究循环 v2 attempt-4 的最终复核

日期：2026-08-23
Reviewer：Cursor Auto，`ask` 只读模式
Verdict：`accepted`

> accepted 仅指流程 PoC。审核对象是研究循环方案与 RQ000 流程小样，不是知识答案。不允许任何
> canonical promotion；RQ000 继续 `[待研究]`；批准下一轮只做 PQ001 draft-only。

## 1. Verdict 边界

| 对象 | 结论 |
|---|---|
| 流程 PoC | `accepted` |
| 内容草案 | `usable_draft_with_one_boundary_correction` |
| `knowledge.yaml` / `research_questions.yaml` 写入 | 禁止 |
| RQ000 状态 | 继续 `[待研究]` |
| PQ001 draft-only | 批准 |
| canonical promotion | 不批准 |

## 2. 已关闭的历史问题

- attempt-2 的第三体系、D3 无快照直接事实、挂错层和停止结论矛盾已经关闭；
- attempt-3 的 PQ002 行政注记凑数已经关闭；
- 缺完整命令、`run.yaml` 滞后和 `legacy_narrative` 误述已经关闭；
- Cursor 首轮 `changes_requested` 针对 attempt-2，不能继续作为当前 attempt-4 的总评。

## 3. 当前 promotion 阻断

1. `render.py` 仍只按 KN 的 `研究问题` 引用翻转二元覆盖，没有验收合同检查；
2. S4 没有 `web_snapshot`，不能成为正式锚；
3. append-ready 模板仍允许裸 `url`，路线 KN/WHY 仍以 `RB###` 引用路线，没有 RP。

## 4. P2：未来实施项

- 双层时间语义是“概念闭合、实施未闭合”：没有 `as_of`、漂移检测或当前基线到历史包的链接；
- legacy 防双轨没有机器守卫；给旧 KN 增加问题引用仍会直接翻转覆盖状态；
- `sources.md` 对无快照 S4 仍写“可直接支持”，冻结来源包自身口径偏松；下一轮应改成“仅线索/
  不可直接支持”；
- 无工具边界仍信任 Pi CLI 旗标，没有进程级工具调用审计日志。

## 5. P3：内容与文档卫生

- N2 的 S2/S3“张力”较弱；完整上下文更支持观察角度差异，但它形式上仍是合格 draft 注记；
- S5 的全局拒绝句已被人工裁决充分收窄：本轮 RQ000 不用，未来 TQ005 可按“项目目标”受审；
- `run.yaml` 状态在 Kimi 通过后再次滞后；
- Pi 停止结论把 N1/N2 当成开启下一轮的全局门闩，与 reviewer 批准 PQ001 draft-only 有软冲突；
- 报告当前已点名 `route_bom.csv` schema 和候选能力群渲染，Kimi 对此的旧 P3 已关闭。

## 6. 报告第 15 节八问

1. 研究包可复核且不污染事实账本：是；
2. 无工具参数机械上关闭 K1/K6 边界，安全证明层仍依赖 CLI 旗标；
3. 无新的硬语义遗漏；N1 必要，N2 形式合格但张力弱；
4. RQ000 合成状态与 A 阶段顺序合理；
5. legacy 方案政策层够、机器层不够；
6. 默认注记、不发 CQ 基本闭合，挂层仍需合同与人工判断；
7. RP 方案层已覆盖 KN、WHY、候选/确认能力群、校验器和 `route_bom` schema；
8. 当前报告不必继续返修才能开 PQ001 draft-only；不批准 promotion。

## 7. 与 Kimi 的一致性

Cursor 同意 Kimi 的主判断：流程 `accepted`、无新 P1、三项 promotion 阻断为真、批准 PQ001
draft-only、拒绝 canonical promotion。新增差分是 S4 来源清单口径偏松、run 状态滞后，以及 Pi
停止句不应成为全局门闩。

## 8. 下一轮条件

- 新目录、新合同，仍为 `draft_only`；
- 不写七文件 canonical，不改变问题状态；
- 强烈建议先保存 OSFP 页的 `web_snapshot`；
- 合同增加“先核冻结材料完整上下文再声明缺口”；
- 注记停止条件是局部研究条件，不是整个队列的全局开启门槛；
- 研究包进入协作工作项时只作 delivery 附件。

## 9. Reviewer 环境说明

Cursor `ask` 模式未获 shell 权限，未自行运行 `scan.py --check`；它静态核对了实现与文档，并明确
要求由 Codex 最后用指定 Miniconda Python 重跑扫描。
