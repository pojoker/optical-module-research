PASS

  包：`docs/research/pi-packages/2026-08-25-tq010-tq014-delta-tradeoff-v1/`。全程只读，未修改任何文件，未读取 `archive/`。

  ## 逐问裁决与亲自核到的证据

  **1. 两套知识体系分离 / WHY 未被臆造 — 通过**
  - `company-placeable-graph-draft.yaml:9-63` 明确分 `physical_system`（tree.yaml cell_id 为稳定身份，facet 仅为 draft 扩展）与 `route_system`（route_profile_instance + 四轴）；`why_bridge.current_status: blocked_by_missing_controlled_tradeoff_evidence`，并列 `current_forbidden_edges` 含 `CONSTRAINT_CAUSES_CHOICE_WITHOUT_EVIDENCE`、`COMPANY_SERVES_ROUTE`（:59-63）。
  - WHY 没有被偷写的实证：S3:1979 确有 "3 nm digital signal processors … to reduce power consumption"，但 `comparison-source-audit.md:118` 明确将其判为"无测量值、无边界、无对照，不支持功耗 delta 或优劣"，两张 TQ014 卡 `advantages: [] / costs_and_disadvantages: []`（audit :152-153, :185-186）。我核对 S3 原文（行 1979）与 S4（行 1966-1967），与矩阵赋值逐字一致；S3/S4 的 SHA256 与 `snapshot-manifest.md` 完全吻合。

  **2. 三分法能否阻止错误归群 — 通过（draft 层级足够）**
  - `capability-requirement-schema-draft.yaml:10-20`：三类分别标 `company_matchable: true(product_only) / true(capability_only) / false`；`candidate_match_gate`(:46-60) 含 `no_supplier_or_customer_relation_inferred`、`no_route_service_conclusion_from_cell_match_alone`。
  - 残余风险（稳定 company_id、引语 span 偏移）已自列于 `company-placeable-graph-draft.yaml:167-173`，未掩盖。

  **3. 5+2+2 是否严格受冻结证据支持 — 通过，逐条核到原文**
  - PCR-D02-C5-001（LRO，Tx-retimed/Rx-linear）← S3:1979 "LRO with a DSP retiming only in the transmit direction" ✓
  - PCR-D03-C5-001（raw 3 nm DSP）← S3:1979 "next generation of 3 nm digital signal processors" ✓（raw label 保留，未推工艺归属）
  - PCR-D04-C4-001（SiPh MZM PIC）← S4:1967 "silicon photonics MZM PIC" ✓
  - PCR-D05-C1-001（1310 nm raw EML laser）与 PCR-D05-C3-001（generic photodetector）← S4:1967 "1310 nm EML lasers and photodetectors" ✓
  - 关键纪律验证：S4 相邻段（200G EML demo，约 :1964）明明写了 "monolithically integrated O-band DFB laser with an electro-absorption modulator"，本包**没有**把它跨实例转移到 D05（`capability-requirements-draft.yaml:58` 明确禁止 DFB+EAM/InP 扩展）。
  - 两个 RPA（QSFP-DD800/OSFP）← S4:1967 ✓；两个 VG 的 missing_fields 与 `comparison-matrix.yaml` 的 UNKNOWN 分布逐字段吻合 ✓。

  **4. 56 个 point 的 facet/role 提议 — 通过，但有明确误报/漏报需记录**
  - 计数全部复算一致：56 = 39 facet_explicit + 17 cell_only；21 个候选匹配点；七个 requirement 的 exact/partial 计数与逐点记录吻合；unique_company_strings=40 复算恰好 40。
  - 引语抽查 12 点（P003/P036/P088/P101/P128/P165/P193/P195/P222/P224/P253/P254）与 `points.csv` 逐字一致。
  - role 全部由引语关键词提出，未见由 cell 自动推断：cell_only 且无动词关键词的点（P016、P129、P263）均为 `role_unknown` ✓。
  - **误报（建议项 A）**：P195（国民技术，`company-capability-match-pilot.yaml:736-740`）从 "暂未形成实际**销售**订单" 中提出 `product_offer`——否定语境被关键词命中，与 point_status=在建 矛盾。虽有 `needs_human_review` 兜底，属明显误报。
  - **漏报（建议项 B）**：P165（永鼎）引语 "100mW**CW**-DFB" 未提出 `laser_type.CW`——`company-facet-rules-draft.yaml:11` 的 `(?<![A-Za-z])CW` 被前一个 ASCII 字母 'W' 挡住。不影响本轮匹配结论。
  - **规则缺口（建议项 C）**：P253（海信）"成功**开发**并批量生产…正在开发 100G/200G EML" — `开发` 只在 `module_integrate` 模式里（rules :64），组件格 C1 下未提出 `component_design`；且在研 EML 与量产 DFB 在 facet 层不加区分地进入 partial 匹配。

  **5. candidate_match 是否限于字段重合 — 通过**
  - 每条 match 均带 `match_level: exact/partial_keyword_candidate` + `limitation` + `promotion_status: needs_human_review`；`company-placeable-tree.md:35` "0 个点被提升为公司服务某路线"；graph :120 "a candidate match is not a route-service, supply, customer, or adoption conclusion"。未发现任何供应/客户/服务路线表述。
  - 附带观察（建议项 D）：P193（通宇通讯，实际主体为参股公司四川光为）、P130（东山精密，引语主体为索尔思）的公司范围注记存在于 points.csv 判定注记中，但未带入 match 的 `limitation` 字段。

  **6. Best-of-N 结论是否诚实 — 通过**
  - 确定性 verifier：`candidate-verification-deterministic.yaml` 报 valid 2/4，错误具体（P3/C1 的 YAML 1.1 `no`→bool 枚举错误；C1 把 D02/D03 raw label 误标 `observed_difference`），且 `verify_candidates.py:103-104` 确实硬编码了该拦截规则，可复现。
  - 语义文件内部一致：我复算 12 delta + 8 tradeoff + 20 requirement = 40 条 = `metrics.total_claims`；corrected=5、unique=14 与 `recommended_claim_union` 的 14 条逐一对应。
  - 诚实性的关键证据：hy3 verifier 自己 accepted 的 4 条（8×200G 轴值、CHAR-D03、FORMFACTOR、EQUALGRAIN）在 `adjudication-best-of-n.md:9-16` 被人工裁决为 domain-type 错误并重分类——裁决文本没有粉饰 self-verifier，明确 "不能直接 promotion"；并如实记录 P3 无新增有效主张。
  - 小瑕疵（建议项 E）：这 4 个 domain-type 错误只记录在 adjudication 文本里，`candidate-verification-semantic-codebuddy-hy3.yaml` 的 metrics 中没有 `verifier_domain_type_error_count` 字段，机器可读性不足。

  **7. 是否可进入下一轮且保持 draft-only — 通过**
  - 所有产出文件 `canonical_write_performed: false`；`git diff --name-only HEAD -- tree.yaml points.csv knowledge.yaml edges.csv out/` 为空——canonical/覆盖文件零改动；包本身为未跟踪新文件。
  - 提示（非本包问题）：工作区存在本包范围外的未提交改动（`corpus/qa/*/qa.jsonl` 约 90 个、`CONTEXT.md`、`refs/us-china-optical-transceiver-restrictions.md`），按约定我只看了 name-only，无法归属，建议包主确认来源。

  ## 必须修复项

  无。没有发现违反 contract.md 失败条件（跨实例补值、名称推结构、无条件优劣、差异写成工艺事实、公司名单、canonical 写入）的行为。

  ## 建议项（不阻塞，进入下一轮前宜处理）

  - A. P195 否定语境误提 `product_offer`（pilot :736-740）——role 规则需否定词窗口或人工复核时优先清掉。
  - B. P165 `laser_type.CW` 漏报——CW 正则的 ASCII lookbehind 对 "100mWCW-DFB" 失效。
  - C. `开发` 未覆盖组件格 design 角色；在研 vs 量产在 facet 层不加区分（P253）。
  - D. match 的 `limitation` 应继承 points.csv 已有的公司范围注记（P193 参股公司、P130 子公司、P224 消费电子语境）。
  - E. 把 `verifier_domain_type_error_count=4` 写进语义验证 YAML 的 metrics，而不只留在裁决散文里。

To resume this session: kimi -r session_ba0fca62-718b-4312-900d-27eea8b8fa9c
