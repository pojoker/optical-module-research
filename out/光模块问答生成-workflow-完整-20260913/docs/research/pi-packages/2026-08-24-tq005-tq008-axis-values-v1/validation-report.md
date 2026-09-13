# TQ005–TQ008 draft-only 验证报告

验证日期：2026-08-24。所有 Python 校验均使用 `/Users/jowang/miniconda3/bin/python3`。

## 结果

| 检查 | 结果 |
|---|---|
| `scan.py --check` | PASS：不变量 ①–⑭ 全绿 |
| `render.py --verify` | PASS：重渲一致 |
| `run.yaml` 与停止标志 | PASS |
| Pi raw 原子主张 | PASS：24 个唯一 draft_id，24 条 `would_mark_covered: false` |
| 细化问题 | PASS：20/20 均有 parent/question/why_open/needed_evidence |
| 四轴守门、器件定义 subtype、claim 索引 | PASS |
| 问题 ID | PASS：只引用 5 个既有 ID，0 个新子 QID |
| 冻结来源 | PASS：14/14 SHA256 匹配 |
| Kimi K3 二次复核 | PASS |
| Cursor 二次复核 | PASS |
| canonical 定向状态 | PASS：指定 canonical 文件无变更 |

## Canonical 零变更范围

`knowledge.yaml`、`research_questions.yaml`、`points.csv`、`edges.csv`、`why_links.yaml`、`route_bom.csv`、`companies.yaml`、`tree.yaml`、`questions_manual.csv`。

## 最终状态

本包完成 TQ005–TQ008 的 draft-only 最小轴值字典和 20 个轴内细化问题，没有落库、没有改变覆盖状态、没有创建新问题 ID。

下一阶段只获准使用 observed seed、缺格显式写 `UNKNOWN` 的 TQ009 单例 seed sketch；正式 Route Profile 库仍未放行。
