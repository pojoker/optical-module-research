# Review round 1 fixes

针对 Cursor FAIL 与 Kimi 建议，已做以下 draft-only 修订：

1. role extraction 变成 cell-aware 且增加否定语境：P195 的“暂未形成实际销售订单”不再生成 `product_offer`。
2. `module_integrate` 不再由“批量/研发/生产”等孤立词触发，必须在有限窗口内与“光模块/光收发模块/transceiver”共同出现。P119 只保留 `product_offer`。
3. 增加证据主体闸：P193 明确为 `affiliate_only`、`attachment_eligible: false`，不再形成 OSFP attribute match；图中只作为 blocked 示例。
4. requirement candidate 与 related facet 拆分：DSP、SiPh、EML 等不完整命中只进入 `related_facet_only`，不创建 requirement-match 边。P101 只留在 SiPh platform facet，不进入 MZM PIC requirement 桶。
5. C3 detector 改为 `generic_scope_candidate`，明确不能回填 RPS-D05 的 PIN/APD subtype。
6. P254 保留 `attribute_exact_candidate`，但 limitation 明写同一点为 1.6T，而 RPS-D05 是 800 Gbps；只匹配 OSFP 单属性。
7. 组件格 design role 加入“开发”；CW regex 修复附着在速率字符串后的漏报；P130 标为 acquired-business scope。
8. 每个 facet 明写 `facet_maturity_state: not_inferred_from_point_status`，避免把混合引语里的在研 EML 继承为 point 的“生产中”。
9. 语义 verifier YAML 增加人工裁决后的 `verifier_domain_type_error_count_post_human_adjudication: 4`。

修订后统计：56 point；39 facet-explicit；17 cell-only；6 个 generic-scope/单属性候选；14 个 related-facet-only；1 个 subject-scope blocked；0 个公司路线服务结论。
