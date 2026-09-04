**PASS**

三个必须修复项在规则、试点和图上已对上号；`review-fixes-round1.md` 的计数与 `company-capability-match-pilot.yaml`、`company-placeable-graph-draft.yaml`、`company-placeable-tree.md` 一致。未改文件，未读 `archive/`。

---

### 必须修复项（对照 Cursor FAIL）

**1. Role：否定句 / `批量` 不得单独当 `module_integrate` — 已关**

- **P195** `国民技术`：`product_offer` 已去掉；现为 `component_design`（「设计」）+ `suppress_roles: [product_offer]` + 否定正则 `暂未.{0,20}销售订单`。见 `company-capability-match-pilot.yaml` L900–918，`company-facet-rules-draft.yaml` L72–88。
- **P119** `长芯博创`：「批量供货」只出 `product_offer`（「供货」），无 `module_integrate`。见试点 L498–515。
- `module_integrate` 现要求有限窗口内同时出现「光模块/光收发模块/transceiver」与研发/生产类词，不再用孤立「批量/研发/生产」。见规则 L66–70。

**2. P193 通宇↔四川光为 OSFP exact/图挂点 — 已关**

- `subject_scope: affiliate_only`，`attachment_eligible: false`，`requirement_matches: []`，`promotion_status: blocked_subject_scope`。试点 L879–899。
- 图示例只作 blocked，无 `candidate_matches`。图 L175–179。
- 树表 D05 OSFP 候选 = 1（P254），并写明 P193 被阻断。树 L49。

**3. `PCR-D04-C4-001` 不再把 SiN/SOI 打进 requirement 桶 — 已关**

- `partial_any` 已删；现为 `exact_all: [silicon_photonics, MZM]`，`related_any: [platform.silicon_photonics]`。规则 L101–105。
- **P101** 仍可抽 `platform.SiN` / `SOI` / `silicon_photonics`（facet 层合理），但 `requirement_matches: []`，只留 `related_facet_only`，limitation 为 generic SiPh ≠ MZM PIC。试点 L385–416。
- 覆盖：D04 exact/generic/attribute 全 0，related 5，`gap_status: no_candidate_point`。试点 L31–37；树 L45。

---

### 统计 / 图 / 试点

| 口径 | 试点 summary | 图 `current_attachment_summary` | 树 |
|---|---|---|---|
| 点数 | 56 | 56 | 56 |
| 公司串 | 40 | 40 | 40 |
| facet-explicit / cell-only | 39 / 17 | 39 / 17 | 39 / 17 |
| requirement/属性候选 | 6 | 6 | 6（5 generic C3 + 1 OSFP） |
| related-facet-only（点） | 14 | 14 | 14 |
| 主体阻断 | 1 | 1 | 1 |
| 公司服务路线结论 | （warning 明文禁止） | 0 | 0 |

复算：`^- point_id:` = 56；`facet_explicit` = 39；`cell_only` = 17；`match_level:` 恰好 6 条（5×`generic_scope_candidate` + 1×`attribute_exact_candidate` P254）。`related_facet_only` **边** 16 条（3+2+5+6），因 **P003、P134** 各挂 D02+D03，去重后 **14 点**，三处写的是点数不是边数。

P254 limitation 三处都写了 1.6T vs D05 800 Gbps。语义 YAML L580：`verifier_domain_type_error_count_post_human_adjudication: 4`。

---

### 残留（不重开三闸，下一轮再清）

1. **P193 仍提出 `product_offer`（「交付」）**，只是匹配/图被主体闸挡住。否定/范围规则还没把 affiliate 引语的角色一并压掉。
2. **子公司闸仍是点覆盖不是规则**：P130 有 override；**P039**「控股子公司武汉钧恒…光模块…研发、制造和销售」仍 `attachment_eligible: true` 且打出 `module_integrate`。图 L185 自己承认「beyond the current explicit P193 override」。
3. **`capability-requirements-draft.yaml` L46** 仍写 generic SiPh 是 “partial”；试点已改成 `related_facet_only` / `not_a_requirement_match`。术语滞后，读 requirement 草稿会以为还在 requirement 桶里。

这三项都不把燕东微送回 MZM 候选，也不把通宇送回 OSFP 候选。公司匹配试点可以当下一轮输入；不要把 `related_facet_only` 或 P193 角色当供应事实。
