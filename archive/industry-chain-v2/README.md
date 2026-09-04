# 产业链研究分支 v2

本分支把“产业结构”放在“公司供货关系”之前，首先回答三个问题：

1. 产业由什么组成；
2. 哪些节点在具体产品路线中重要；
3. 哪些空白必须继续研究。

它不覆盖现有 `output/nodes.csv` 或 `output/edges.csv`。旧关系台账未来只能作为
`trade_observations.csv` 的候选输入，不能反向定义产业骨架。

## 当前样板

- 产品路线：800G DR8、800G 2×FR4、400ZR；
- 结构节点：112；
- 结构边：224；
- 显式研究缺口：55（P0 45，P1 10）；
- 公司、能力、供货关系：canonical 当前为空，防止在结构尚未取得正式证据时
  用公司名单制造“假完整”。

数据分成五层：

```text
应用 / 产品路线 / 功能 / BOM
                 ├─ 制造工序 / 设备类别
                 ├─ 组织 / 能力映射
                 ├─ 商业供货观察
                 └─ 结构 / 能力 / 交易证据
                              ↓
                         研究缺口队列
```

## 目录

- `SPEC.md`：产品范围、流程和验收门；
- `schema/CONTRACT.md`：七份 canonical CSV 的数据契约；
- `data/`：Codex 审核后的 canonical 快照；
- `work/grok/`：产品路线与 BOM；
- `work/claude/`：制造工序与设备类别；
- `work/hy3/`：validator 与缺口生成；
- `work/kimi/`：读者页渲染；
- `output/industry-chain-v2.html`：自包含读者报告；
- `REVIEW.md`：Codex 终验、退回项和下一轮研究顺序。

## 复现

```bash
python3 work/hy3/test_validate_model.py
python3 work/hy3/validate_model.py data --json
python3 work/hy3/generate_gaps.py data --reference-date 2026-07-24
python3 work/kimi/tests/test_render.py
python3 work/kimi/render_report.py data output/industry-chain-v2.html
```

缺口生成必须显式传入参考日期，避免相同数据在不同日期产生不同结果。

## 当前结论边界

所有 canonical 重要性判断最高只到 `hypothesis`，没有任何节点伪装成
`verified`。正式研究下一步应先补 structure evidence，再做玩家与能力映射，
最后叠加供货关系；顺序不可反转。
