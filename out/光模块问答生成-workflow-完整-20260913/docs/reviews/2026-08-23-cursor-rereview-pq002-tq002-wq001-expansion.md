# Cursor 复核报告（PASS_WITH_FIXES 修订闭合）

审核日期：2026-08-23
范围：`docs/research/pi-packages/2026-08-23-expansion-v1/` 的 controlling text / 摘要 / 三份 final adjudication / `run.yaml`；对照 `docs/reviews/2026-08-23-cursor-review-pq002-tq002-wq001-expansion.md`
raw 按审计原文处理，未要求改写

**Verdict: `PASS`**

本轮要修的是下游误读闸，不是把 raw 改成第二份正文。`post-review-effective-text.md` + `run.yaml` 的 `controlling_text` / `raw_outputs_are_audit_only: true` 已经把那扇闸钉死：冲突以 controlling text 为准，三份 final 只作裁决记录。上一轮 P1 里“只改裁决段不够”这一条，在**禁止改 raw** 的前提下已经闭合。

---

## 逐项

| 项 | 结论 |
|---|---|
| IEEE 日期 → Board Approval `2024-02-15`（Published `2024-03-15`） | **闭合。** controlling text §3.1、`adjudication-tq002-final.md` 补充裁决、`expansion-summary.md` 日期勘误一致；raw/`sources-tq002.md` 里的 `2024-02-16 获批` 被明确作废。 |
| B3 披露 OSFP §15.8 单源双侧使用 | **闭合。** controlling text §4 B3：route 与核心 physical 均复用 §15.8，标成单源双侧、非独立双源；CPO 缩短电通道只作 framework target。WQ final 补充裁决第 2 条同文。 |
| B2 不再拼接可插拔 reach 与 CPO connector budget | **闭合。** 有效桥只保留 reach → media/PMD → 500 m SMF 单产品实例；CPO mid-board connector → optical budget 退回 CPO 物理注记，且写明本轮无独立 route-side 场景需求。强度改为该窄链上的规范结构支持，合理，不是把旧跨族链升格。 |
| B5 可插拔 / CPO 两场景拆分，均受限推论 | **闭合。** 分支 A/B 分开，强度均为受限推论；禁止合成通用维护物理、禁止推生命周期成本。摘要表已对齐。 |
| PQ005 形态 vs PQ009 量值分流 | **闭合。** PQ002 注记 2 与 B2 注记同一口径：形态/位置/返工实现 → PQ005；插损、optical budget、TX/RX、margin → PQ009。无新 QID。 |
| 真实 canonical 槽写作 `knowledge.yaml#why_links` | **闭合。** controlling text §1、WQ final 补充裁决第 4 条。旧句“不授权写入 `why_links.yaml`”仍留在 WQ final 前半，已被后文纠正，不构成槽位误写。 |
| 无 canonical 写入、无新 QID | **成立。** `run.yaml`：`draft_only`，`canonical_write_allowed/performed: false`，`coverage_status_changed: false`，`new_question_ids_created: false`。`knowledge.yaml` 无 PQ002/TQ002/WQ001；`why_links: []`。 |

---

## controlling text 是否够挡住下游误读

**够。** 消费规则是硬规则，不是脚注：下一批必须先读该文件；raw 不得单独当研究输入。B2/B3/B5、日期、CMIS“唯一骨架”、d08 事件类型、PQ005/PQ009 分流都写在同一份可执行口径里，而不是散落在三份裁决的“通过”段。

残留误读面只在**不遵守消费规则**时存在：raw 仍写 `2024-02-16`、B5 原稿强度、CMIS“唯一”、B2 跨族句。这是审计原文的预期状态，不是未修。

WQ/PQ final 前半“通过”段仍有过时概括（例如 PQ002 只写挂 PQ004/PQ005、WQ 仍写五条都有双侧证据）。只要下一批合同继续指向 `post-review-effective-text.md`，这不构成未闭合 P1。

---

## 未关闭问题（均不阻断本包闭合）

1. **冻结 PDF 路径+SHA256**（上一轮 P1-5）：本包文本修订未处理；仍不能在本工作区独立核清单 PDF。这是取证能力缺口，不是口径缺口。下一批若继续引用同一快照，应能核哈希；**不因此否决本轮文本闭合**。
2. **WQ final 仍并列 `why_links.yaml` 旧称**：已被 `knowledge.yaml#why_links` 纠正；下一批合同只用后者。
3. **`sources-tq002.md` 仍写 2024-02-16**：非 controlling text；下一批禁止从 sources 行摘日期。

无 P0。无未闭合的跨族 WHY、无未降档的 B5、无未分流的 PQ005/PQ009。

---

## 是否允许下一批 draft-only 扩展

**允许。**

约束不变：只加深已有子问题（优先 PQ004 / PQ009 / TQ002 定量空缺或 TQ003）；禁止新 QID；禁止写 `knowledge.yaml#why_links` 或任何 canonical；禁止改覆盖状态；输入以 `post-review-effective-text.md` 为唯一有效口径；Kimi 若在结构/证据边界上否决，以否决为准。本轮通过**不自动 promotion**。
