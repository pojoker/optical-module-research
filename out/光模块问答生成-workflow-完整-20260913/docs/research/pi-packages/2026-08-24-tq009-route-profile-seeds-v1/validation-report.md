# TQ009 路线画像种子验证报告

验证日期：2026-08-25。

## 1. 数据与 schema

使用 `/Users/jowang/miniconda3/bin/python3` 解析 `route-profile-seeds-effective.yaml`：

- seeds: 5（`RPS-D01`–`RPS-D05`）；
- atomic leaves per seed: 36；
- unknown 叶均严格为 `value: UNKNOWN`、`source_ids: []`；
- 非 unknown 值不含字符串 UNKNOWN；
- `missing_fields` 与 unknown 叶路径逐种子完全相等；
- 五个 `placement_class` 状态均为 `normalized`；
- D05 `modulator_or_emitter_type` 为 UNKNOWN，不拆 EML 原始组合词；
- issues: 0。

最终字段计数：

| Seed | known/company-stated/normalized | unknown | total |
|---|---:|---:|---:|
| RPS-D01 | 18 | 18 | 36 |
| RPS-D02 | 12 | 24 | 36 |
| RPS-D03 | 9 | 27 | 36 |
| RPS-D04 | 6 | 30 | 36 |
| RPS-D05 | 7 | 29 | 36 |

## 2. 公司数据试挂

Miniconda 复核：

- `points.csv`: 271 条；
- unique companies: 155；
- point cells: 39；
- 不闭合到 `tree.yaml` 的能力格: 0；
- 当前只允许物理能力点挂载，路线候选匹配继续关闭。

## 3. 项目校验

| 命令 | 结果 |
|---|---|
| `/Users/jowang/miniconda3/bin/python3 scan.py --check` | 不变量 ①–⑭ 全绿 |
| `/Users/jowang/miniconda3/bin/python3 render.py --verify` | 一致 |
| `git diff --check`（本包、CONTEXT、review） | 通过 |
| canonical 文件差异检查 | `knowledge.yaml`、`research_questions.yaml`、`points.csv`、`edges.csv`、`route_bom.csv`、`tree.yaml` 均无本轮差异 |

## 4. Reviewer

- Kimi 首审：`PASS_WITH_CHANGES`；模型固定 `kimi-code/k3`；
- Cursor 首审：`PASS_WITH_CHANGES`；只读 ask 模式；
- Kimi 复审：`PASS`；
- Cursor 复审：`PASS_WITH_CHANGES`，仅剩 D05 未拆组合词一致性；
- D05 回退 UNKNOWN 后 Cursor 最终复审：`PASS`。

回执：

- `docs/reviews/2026-08-25-kimi-review-tq009-route-profile-seeds.md`
- `docs/reviews/2026-08-25-cursor-review-tq009-route-profile-seeds.md`
- `docs/reviews/2026-08-25-kimi-rereview-tq009-route-profile-seeds.md`
- `docs/reviews/2026-08-25-cursor-rereview-tq009-route-profile-seeds.md`
- `docs/reviews/2026-08-25-cursor-final-rereview-tq009-route-profile-seeds.md`

## 5. 最终边界

- safe_for_next_draft_only_TQ010_TQ014_experiment: true
- formal_route_profiles_created: false
- canonical_write_performed: false
- coverage_status_changed: false
- new_question_ids_created: false
- company_groups_created: false
