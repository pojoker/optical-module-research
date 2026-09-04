# TQ004 draft-only 验证报告

验证日期：2026-08-24。

所有 Python 校验均使用 `/Users/jowang/miniconda3/bin/python3`。

## 结果

| 检查 | 结果 |
|---|---|
| `scan.py --check` | PASS：不变量 ①–⑭ 全绿 |
| `render.py --verify` | PASS：重渲结果一致 |
| `run.yaml` YAML 解析 | PASS |
| draft-only 三个停止标志 | PASS：canonical write / coverage change / new QID 均为 false |
| 问题 ID 引用 | PASS：17 个既有 ID，0 个未知 ID，0 个新子 QID |
| attempt 2 草稿声明 | PASS：恰好 `TQ004-a2-d01`–`TQ004-a2-d14`，各出现一次 |
| 冻结来源 | PASS：6 个新增快照与 3 个复用快照均存在，9/9 SHA256 匹配 |
| canonical 文件工作区状态 | PASS：指定 canonical 文件均无变更 |
| Kimi 二次复核 | PASS（`kimi-code/k3`） |
| Cursor 二次复核 | PASS（read-only ask mode） |

## Canonical 零变更范围

以下文件经定向状态检查均无变更：

`knowledge.yaml`、`research_questions.yaml`、`points.csv`、`edges.csv`、`why_links.yaml`、`route_bom.csv`、`companies.yaml`、`tree.yaml`、`questions_manual.csv`。

## 最终状态

本包是 draft-only 研究产物。没有落库、没有覆盖状态变化、没有创建新问题 ID。下一轮只获准展开 TQ005–TQ008。
