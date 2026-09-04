# Review round 2 non-blocking cleanup

Kimi 与 Cursor 均已 PASS。随后只做收紧、不扩大结论的建议项清理：

- P193 在主体阻断后不再输出任何 proposed role；
- P039 明标 `direct_named_subsidiary`，因为引语直接点名 row company 武汉钧恒；
- P130/P133 分别标记 acquired-business / group-via-acquisition scope，避免把子公司能力写成无范围的母公司直接制造能力；
- `capability-requirements-draft.yaml` 中的 generic DSP/SiPh/EML 统一改称 `related-facet-only`，与试点和图一致；
- 语义 verifier metrics 同时记录 self-verifier 报告 0 个 domain-type error、人工裁决后发现 4 个，明确表现 verifier false-accept。

统计未变化；所有修改仍为 draft-only。
