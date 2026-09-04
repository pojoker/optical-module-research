# Kimi 对 Pi 研究循环 v2 attempt-4 的独立复核

日期：2026-08-23
Reviewer：Kimi Code `kimi-code/k3`
Session：`session_2ff1e3d7-2312-4275-a0fe-3027f593847c`
Verdict：`accepted`

> accepted 仅指流程 PoC 与报告本身作为审核对象成立；不延伸至任何内容落库。未发现新的 P1。
> 报告自列的三项 promotion 阻断全部经代码核实为真，维持有效。

## 1. 已关闭的历史问题

- attempt-2 的第三体系、无快照直接事实与挂错层问题，已由 attempt-3/4 合同关闭；
- attempt-3 的 PQ002 行政注记凑数问题，已由 attempt-4 的注记必要性四条件关闭；
- `legacy_narrative` 误述已改成真实代码行为；
- `run.yaml` 滞后和缺完整命令的问题已关闭。

## 2. 当前 promotion 阻断

1. `render.py` 仍是二元覆盖：任意 KN 引用问题即可翻转 `[已覆盖]`，没有验收合同检查；
2. S4 没有 `web_snapshot`，不具备正式入库锚型；
3. append-ready 模板仍允许 `url`，路线 KN 仍引用 `RB###`，没有 RP 概念。

## 3. P2：未来实施前必须处理

- 双层时间语义只在政策层闭合：缺 `as_of`、变更原因、受影响 QID/RP、需复核触发和漂移检测；
- legacy KN 防双轨目前只靠纪律，扫描器不阻止给旧 KN 补一个问题引用后瞬间翻转覆盖状态。

## 4. P3：内容质量与完备性

- N2 的 S2/S3“张力”前提偏弱；完整上下文更像观察角度差异。未来合同应要求先核冻结材料完整
  上下文，再声明缺口；
- S4 的“抓取核对日期”没有快照或响应头凭证，只能视为访问声称；
- `--no-tools` 的零调用结论仍信任 Pi CLI 旗标语义，没有进程级工具调用审计日志；
- RP 冻结清单还应点名候选能力群/选择轴渲染及 `route_bom.csv` schema；
- `run.yaml` 的 `exit_code` 应明确属于哪个 attempt。

## 5. 报告第 15 节八问

1. 研究包可复核且不污染事实账本：是；
2. `--no-tools --no-context-files` 机械上关闭工具边界：是，残余为 CLI 旗标信任；
3. 未发现 attempt-4 裁决的新遗漏；N1 必要，N2 形式合格但内容偏弱；
4. RQ000 合成状态与 A 阶段顺序合理；
5. legacy 方案政策层足够、机器层无防线；
6. 注记默认且不发 CQ 基本闭合，挂层正当性仍依赖合同与人工判断；
7. RP 冻结条件基本覆盖，应补候选能力群渲染和 `route_bom` schema；
8. 批准下一轮 PQ001 draft-only，不批准 promotion。

## 6. 特别检查

- N1 真实且必要；N2 可保留，但未来应加强“先核完整上下文”要求；
- S5 人工边界修正足够，未来归入 TQ005 时只能以“项目目标”身份受审；
- 实时基线是“概念闭合、实施未闭合”；
- legacy KN 描述与 `scan.py`、`knowledge.yaml` 真实行为一致；
- 四个方向与两套知识体系、Why 桥和问题树一致。

## 7. 批准决定

- 下一轮 PQ001 draft-only 研究包：`accepted`；建议先补 S4 的 `web_snapshot`；
- 任何 canonical promotion：`rejected`，须先关闭三项 promotion 阻断。

## 8. Reviewer 只读核验记录

- S1–S3 三条本地锚逐行命中；
- `/Users/jowang/miniconda3/bin/python3 scan.py --check`：不变量 ①–⑭ 全绿；
- RQ000 在派生页仍为 `[待研究]`；
- `knowledge.yaml`、`research_questions.yaml` 未因小样修改；
- 口径声明计数为 100 字；
- 文档差异检查通过。
