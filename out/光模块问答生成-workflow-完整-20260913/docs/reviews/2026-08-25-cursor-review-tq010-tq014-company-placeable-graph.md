**FAIL**

Delta / 两套知识体系 / WHY 冻结、三分法和 Best-of-N 自述大体诚实，也仍是 draft-only。不能过闸的是公司侧：role 规则在造假角色，匹配规则会把不该进 SiPh MZM 桶的公司打成 partial。按 brief 第 4、5 问，这就是必须修，不是下一轮再漂。

---

### 1. 两套知识 + WHY

**结论：分开了；WHY 没有被编成因果。**

- 物理侧：`tree.yaml` 的 C1/C3/C4/C5/MOD1；form-factor 明确 **UNMODELED**，并拒绝塞进 B1/B2/D9（`comparison-source-audit.md` §4.1–4.2；S4 `:1967` 只支持 QSFP-DD800 vs OSFP 字段差）。
- 路线侧：seed 36 叶 + `route_product_attribute`（速率/lane/形态）。
- WHY：`capability-requirement-schema-draft.yaml` `why_bridge.promotion_rule` 写死「邻接 ≠ 因果」；`company-placeable-graph-draft.yaml` `why_bridge.current_status: blocked_by_missing_controlled_tradeoff_evidence`，禁止 `ROUTE_IS_BETTER_THAN_ROUTE` / `COMPANY_SERVES_ROUTE`。
- S3 `:1979`「3 nm DSP … reduce power consumption」被审计挡掉，未写成 D02/D03 功耗优势（`comparison-source-audit.md` L118）。

---

### 2. 三分法够不够挡住错归群

**类型层够；匹配层不够。**

分对了：

| 类型 | 本包实例 | `company_matchable` |
|---|---|---|
| `physical_capability_requirement` | 5 条 PCR | true，且带 `matching_limit` |
| `route_product_attribute` | QSFP-DD800 / OSFP | 只匹配产品字段 |
| `validation_gap` | VG 电职责、VG 光子等粒度 | false |

挡不住的洞：`PCR-D04-C4-001` 的 `partial_any` 含 `platform.SiN` / `platform.SOI`（`company-facet-rules-draft.yaml` L80）。**P101 燕东微**引语是 8 英寸 SiN 产线 + 12 英寸 SOI 硅光工艺平台，被打成 D04 **SiPh MZM PIC** 的 `partial_keyword_candidate`（`company-capability-match-pilot.yaml` L303–330）。Foundry 平台 ≠ MZM PIC。limitation 写了「generic SiPh ≠ MZM」，但规则仍把 SiN/SOI 送进同一 requirement 桶——三分法被 keyword 规则打穿。

---

### 3. 5 PCR / 2 RPA / 2 VG 是否被冻结证据撑住

**PCR/RPA/VG 条目本身：PASS。** 我核对了 S3 `:1976-1979`、S4 `:1966-1967`：

- PCR-D02 C5 LRO Tx-retimed / Rx-linear：S3 第一项 demo。
- PCR-D03 C5 raw `3 nm DSP`：同句；未推断 D03 架构/删 DSP/FEC。
- PCR-D04 C4 SiPh MZM PIC：S4 D04 端点。
- PCR-D05 C1 raw 1310 nm EML laser；C3 generic photodetector：S4 D05。未展开 DFB+EAM / InP / PIN-APD。
- RPA：QSFP-DD800 vs OSFP，UNMODELED。
- VG：D03 电职责 UNKNOWN；D04/D05 不等粒度光子叶。

`8×200G` 没有做成 C5 PCR（裁决 `adjudication-best-of-n.md` L36）。D01 未进比较。

---

### 4. 56 point 的 facet/role：明显误报（本 FAIL 主因）

**Cell 单独不推 role：成立。** 例：P016 光迅 MOD1 产品罗列 → `role_unknown`；P036 C3「激光器和探测器」→ `role_unknown`；P003 Marvell DSP 引语无设计/制造动词 → `role_unknown`。

**Role 规则在乱贴，brief 点名要查的就是这个。**

**必须修 1 — 否定句当 `product_offer`**
`P195 国民技术` 引语：「暂未形成实际销售订单」；`basis_patterns: 销售` → `product_offer`（match-pilot L726–741）。这是假销售角色。

**必须修 2 — `module_integrate` 词表与 cell 门控**
`company-facet-rules-draft.yaml` L64：`module_integrate: ['研发','开发','设计','生产','制造','量产','批量', …]`，与 design/manufacture 大量重叠。MOD1 上几乎凡「研发/生产」就贴集成。

- `P119 长芯博创`：「多模400GSR4、800GSR8产品具备**批量供货**能力」→ `module_integrate` 仅因「批量」（L399–412）。这是供货口径，不是模块集成证据。
- `P193 通宇通讯`：引语主体是「**参股公司四川光为**」的 800G OSFP；`设计` 来自「低功耗设计」，`批量` 来自「小批量交付」→ `module_integrate` + 还 exact 命中 `RPA-D05-FORM-001`（L700–725）。挂的是通宇，活是参股子公司。`company-placeable-graph-draft.yaml` 示例还用 P193 当 OSFP 挂点，会把错公司写进图。

Facet 误报相对轻：P147 EML 无 1310 nm → partial，limit 正确；P148 PD/APD 打 C3 generic **exact** 偏松，但 limitation 禁止回填 D05 subtype，可降为建议。

漏报：points.csv 无 LRO / 3 nm / MZM 字符串，对应 PCR exact=0 与语料一致，不算漏。

---

### 5. `candidate_match` 是否只是字段重合

**契约写对了，试点输出会让人读成「能供这条路线」。**

Schema 门：`no_supplier_or_customer_relation_inferred`、`no_route_service_conclusion_from_cell_match_alone`（schema L54–55）。图边 `ASSERTION_CANDIDATE_MATCHES_REQUIREMENT` 要人审。

仍必须修：P193 的 OSFP **exact_keyword_candidate** 挂在通宇公司字符串上——字段重合在引语里成立，**公司主体不成立**。`candidate_match` 没有公司实体闸。

---

### 6. Best-of-N 是否诚实

**PASS。** 增益：P2 补 LRO / 3 nm 刻面；C1 补等粒度缺口（后改 VG）。代价：P3 无新有效 claim + 枚举错；CodeBuddy hy3 把 LRO vs 3 nm DSP 标成 `observed_difference`，机械 verifier 拦住（`candidate-verification-deterministic.yaml` L41–44，`candidate_valid_rate = 0.5`）。语义 verifier 仍把 8×200G / form-factor / 补测缺口混成 `capability_requirement`（`verifier_domain_type_error_count = 4`）。明确说不能靠多数票定技术事实、不能直接 promotion。

---

### 7. 能否进下一轮受控 trade-off / WHY（仍 draft-only）

**Delta/TQ014 缺口清单可以进。公司匹配试点不能作为下一轮输入，除非先修 role/匹配。**

Draft-only：包内 `canonical_write_performed: false`；会话初始 `git status` 无 knowledge/coverage 改动（Ask 模式未跑 `git diff --name-only`）。

---

### 必须修复

1. Role 规则：否定/范围（「暂未销售」「参股/子公司」）；`批量` 不得单独 → `module_integrate`；`module_integrate` 与 design/manufacture 词表拆开，禁止「MOD1 + 研发生产 ⇒ 集成」。证据：P195、P119、P193 + `company-facet-rules-draft.yaml` L59–64。
2. 从 exact/图示例中拿掉或降级 **P193 通宇↔四川光为** OSFP 命中。
3. `PCR-D04-C4-001` 的 `partial_any` 去掉 SiN/SOI（或改成「仅平台、单独桶」）。证据：P101。

### 建议

- P148：generic photodetector 不要因 PD/APD 升 exact。
- P254 1.6T OSFP vs D05 800G OSFP：属性命中可以，UI 必须写速率不同。
- `CONSTRAINT_EXPLAINS_REQUIREMENT` 只留在 schema，下一轮未拿到同条件证据前不要实例化边。

物理比较与 WHY 冻结可以留；**公司图按现状推广会把通宇、燕东微、国民技术装进错误桶。先修匹配，再谈下一轮。**
