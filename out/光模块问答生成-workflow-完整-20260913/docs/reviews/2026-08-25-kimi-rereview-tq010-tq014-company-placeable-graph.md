**PASS**

  三个必须修复项均已真正关闭，统计/图/试点三处口径一致。核对过程只读，未触碰 `archive/`，未修改任何文件。

  ## 必须修复项核销

  **必须修 1（role 规则）— 已关闭**
  - `company-facet-rules-draft.yaml:66-70`：`module_integrate` 改为窗口共现正则，要求 `光模块|光收发模块|transceiver|optical module` 与研发生产动词同现，词表中已无孤立的「批量/研发/生产」。
  - 否定语境：`:72-75` 新增 `role_negative_patterns`（`暂未.{0,20}销售订单` 等），`:86-88` 对 P195 加 `suppress_roles: [product_offer]`；试点 P195（L900-918）只保留 `component_design`，不再生成 `product_offer`。
  - P119（pilot L498-515）只保留 `product_offer`，`module_integrate` 已消失。
  - 「开发」已进 `component_design`（rules L62）。

  **必须修 2（P193 通宇↔四川光为）— 已关闭**
  - Pilot L879-899：`subject_scope: affiliate_only`、`attachment_eligible: false`、`requirement_matches: []`、`promotion_status: blocked_subject_scope`，OSFP exact 命中已移除。
  - 图 `company-placeable-graph-draft.yaml:175-179` 中 P193 仅作为 blocked 示例，不再当 OSFP 挂点；RPA-D05-FORM-001 的 attribute_exact 只剩 P254（pilot L62-64 与 L1297-1324 一致），且 P254 limitation 明写 1.6T vs 800 Gbps 速率冲突。

  **必须修 3（PCR-D04-C4-001 partial_any 含 SiN/SOI）— 已关闭**
  - Rules L101-105：`partial_any` 已删除，只留 `related_any: [platform.silicon_photonics]`。P101（pilot L385-416）只进 `related_facet_only`（`not_a_requirement_match`），不再落入 requirement 桶。SiN/SOI 仍作为 facet 保留在 P101 的 `proposed_facets`，属证据描述而非匹配。

  ## 统计一致性（三处对账全部吻合）

  - 56 point（实际逐条数过 56 条）、40 unique companies（数过 40 个）、39 facet-explicit / 17 cell-only（cell-only 逐条数 = 17）。
  - 6 个 candidate match = 5×generic_scope（P036/P037/P148/P224/P235）+ 1×attribute_exact（P254），与 grep 命中 6 处一致。
  - 14 个 related-facet-only：D02=3（P003/P118/P134）、D03=2（P003/P134）、D04=5（P088/P101/P102/P199/P212）、D05-C1=6（P128/P147/P165/P201/P222/P253），去重 = 14；requirement_coverage 分项数字与逐条记录相符。
  - blocked_subject_scope = 1（P193）、full_route_service_conclusions = 0；pilot summary、graph `current_attachment_summary`、review-fixes-round1.md 三处一致。
  - `verifier_domain_type_error_count_post_human_adjudication: 4` 确认存在于语义 verifier YAML L580。
  - draft-only 保持：三份 YAML 均 `canonical_write_performed: false`。

  ## 残留问题（建议级，不阻 PASS）

  1. **P133 vs P130 口径不一致**：同属东山精密/索尔思收购，P130 标了 `controlled_subsidiary_or_acquired_business`，P133（"通过收购索尔思光电，公司跻身…光模块核心供应商"）仍是 `direct_or_unresolved` 且带 `module_integrate`。可辩解为 P133 是集团层面自述，但建议人审时标注。
  2. **语义 verifier 的 pre-adjudication 键消失**：fixes 说明写「增加」post 字段，但原 `verifier_domain_type_error_count` 键已不在文件里（grep 仅命中 L580 的 post 版），前后对比无法自证。若 post=4 恰等于原值，建议补回 pre 字段或注明。
  3. **P193 仍展示 proposed_facets 和 product_offer role**：虽已 `attachment_eligible: false` + blocked promotion，UI 若直接渲染 facet 列表仍可能误读，属既有 `next_schema_gaps` 已覆盖的展示问题。
  4. `component_manufacture` 词表仍含孤立「批量」（P141/P165 的 C1 激光器因此得 manufacture role）——对芯片量产语境尚可接受，但若下轮要收紧需一并处理。

  结论：可以进入下一轮受控 trade-off / WHY 证据研究，公司匹配试点仍须保持 draft-only + human review 门。

To resume this session: kimi -r session_f584e3cf-6369-43b6-8f80-9e1f150a910e
