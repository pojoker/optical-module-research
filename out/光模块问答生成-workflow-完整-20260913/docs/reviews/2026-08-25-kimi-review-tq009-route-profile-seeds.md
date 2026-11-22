kimi version 0.38.0
Warning: [loop_control] 'max_retries_per_step' is deprecated and no longer used; rename it to 'max_attempts_per_step'. Run /update-config to fix it.
• Read the review request file.This is a substantial read-only review task requiring reading many files completely. Good candidate for delegation to an explore subagent... But the review requires deep reading and returning a structured verdict. The instruction says I should do the review. I could delegate to an explore agent, but the review requires careful judgment — actually a subagent could do it, but the verdict quality matters. The files are numerous but I can read them directly. Let me read files in parallel batches. Some may be large; I'll read and page as needed.

  Let me start: CONTEXT.md glossary section (need to find it), the package files, upstream file, question tree.

  Let me first list the package directory and read CONTEXT.md.

• 我先读取审查请求列出的全部文件，然后给出结构化结论。total 360
drwxr-xr-x  22 jowang  staff    704 Aug 25 00:00 .
drwxr-xr-x   8 jowang  staff    256 Aug 24 23:33 ..
-rw-r--r--   1 jowang  staff   1297 Aug 24 23:59 README-FIRST.md
-rw-r--r--   1 jowang  staff   1855 Aug 24 23:48 adjudication-round1.md
-rw-r--r--   1 jowang  staff   2016 Aug 24 23:59 adjudication.md
-rw-r--r--   1 jowang  staff   4307 Aug 24 23:41 candidate-tree.md
-rw-r--r--   1 jowang  staff    610 Aug 24 23:55 command-round2.txt
-rw-r--r--   1 jowang  staff    735 Aug 24 23:41 command.txt
-rw-r--r--   1 jowang  staff   3809 Aug 24 23:39 company-placement-pilot.md
-rw-r--r--   1 jowang  staff   1689 Aug 24 23:33 company-placement-rules.md
-rw-r--r--   1 jowang  staff   3368 Aug 24 23:48 contract-round2-atomic.md
-rw-r--r--   1 jowang  staff   5760 Aug 24 23:33 contract.md
-rw-r--r--   1 jowang  staff   5760 Aug 24 23:59 post-adjudication-effective-text.md
-rw-r--r--   1 jowang  staff  25158 Aug 24 23:57 raw-output-round2.md
-rw-r--r--   1 jowang  staff  19949 Aug 24 23:47 raw-output.md
-rw-r--r--   1 jowang  staff   2693 Aug 25 00:00 review-request.md
-rw-r--r--   1 jowang  staff  28064 Aug 24 23:58 route-profile-seeds-effective.yaml
-rw-r--r--   1 jowang  staff   3506 Aug 24 23:41 route-tradeoff-gate.md
-rw-r--r--   1 jowang  staff    529 Aug 24 23:59 run.yaml
-rw-r--r--   1 jowang  staff   1229 Aug 24 23:36 snapshot-manifest.md
-rw-r--r--   1 jowang  staff  24881 Aug 24 23:39 source-discovery.md
-rw-r--r--   1 jowang  staff   1121 Aug 24 23:36 sources.md


• Now read the package files. Read in parallel: contract.md, source-discovery.md, adjudication-round1.md, contract-round2-atomic.md, raw-output-round2.md, adjudication.md, route-profile-seeds-effective.yaml, post-adjudication-effective-text.md, candidate-tree.md, route-tradeoff-gate.md, company-placement-rules.md, company-placement-pilot.md, upstream TQ005-TQ008 post-adjudication-effective-text.md, and docs/plans/2026-08-research-question-tree-v2.md.

  Given the number of files and need for a detailed verdict, I'll read them all myself since the review requires careful judgment and cross-checking (semantic corrections, 35 fields, etc.). Files are small except raw-output-round2 (25K), yaml (28K), source-discovery (25K). That's manageable.Now read raw-output-round2.md, upstream TQ005-TQ008 post-adjudication-effective-text.md, and the frozen question tree TQ001–TQ014/WQ001–WQ004 sections.Now the frozen question tree around TQ001–TQ014 and WQ001–WQ004.Let me also read a bit more context in the tree doc around TQ001–TQ003 and the structure (to confirm parent definitions and TQ014 wording). Let me read lines 140–175.All required files read. Also should quickly check: the two semantic corrections — verify against raw-output-round2: yes, raw round 2 had media_lane_rate: "53.125 GBd" observed, and pic_eic_integration: "MZM PIC" company-stated; effective yaml corrected both. Also missing_fields in effective yaml updated accordingly (D01 gained media_lane_rate; D04 lost nothing? check D04 effective missing_fields includes pic_eic_integration — yes line 753 pic_eic_integration unknown, and device_integration has MZM PIC company-stated; missing_fields D04 includes detector_type, pic_eic_integration, laser_pic_integration but not device_integration — correct).

  Now I can also check counts: 35 fields per seed? Schema: TQ005 has 16, TQ006 has 7, TQ007 has 10, TQ008 has 2 → 35. Good.

  Check the completeness table in adjudication.md: D01 17 observed/company-stated of 35. Count D01 effective: tq005: nominal, reported, host_lane_count, host_lane_rate, modulation, symbol_rate, pmd, media_type, reach, wavelength, lane_organization, optical_connector = 12 known; unknown: media_lane_count, media_lane_rate, fec_code, fiber_mapping = 4. tq006: raw_architecture_label known (1), 6 unknown. tq007: modulator EML, detector PIN = 2 known, 8 unknown. tq008: 2 known. Total known = 12+1+2+2 = 17. ✓ matches 48.6%.

  D02: tq005: nominal, host_lane_count, host_lane_rate, media_lane_count, media_lane_rate = 5; tq006: normalized, raw_label, tx, rx = 4; tq007: platform = 1; tq008: 2 → 12 ✓.

  D03: tq005: 5; tq006: raw_label =1; tq007: platform=1; tq008: 2 → 9 ✓.

  D04: tq005: nominal=1; tq006: 0; tq007: platform, modulator, device_integration = 3; tq008: 2 → 6 ✓.

  D05: tq005: nominal, wavelength = 2; tq006: 0; tq007: light_source_type, light_source_wavelength, modulator, detector = 4; tq008: 2 → 8 ✓.

  Consistency check: raw round 1 output (raw-output.md) — not required to read per request? Request item 3 lists contract.md, source-discovery.md, adjudication-round1.md, contract-round2-atomic.md, raw-output-round2.md, adjudication.md. Raw-output.md round 1 not required. Fine.

  Now check review question 5: did any seed still infer from DR8/DSP/EML/SiPh/form factor/adjacent demos/interoperability? Check effective yaml:
  - D02/D03: media_lane_count 8 / host_lane_count 8 from S3 — S3 directly states "8x200G electrical interfaces" and "8x200G optical" per source-discovery. OK, not inferred from DR8.
  - placement_class "front-panel pluggable" marked observed — it's a controlled G2 taxonomy mapping from OSFP, marked observed. Source-discovery acknowledges this is a normalization; arguably it should be distinguished (it's derived from a controlled mapping rather than directly observed). Minor note.
  - D01 media_lane_count UNKNOWN despite DR8 and MPO-16 (which would imply 8 fibers tx+8 rx) — good discipline.
  - D05 light_source_type: EML — from S4 "1310 nm EML lasers". EML is both a light source (laser) and modulator/emitter — recorded in both fields, consistent with source statement "EML lasers". Hmm, light_source_type EML and modulator_or_emitter_type EML both. Fine per source.
  - D03 raw_architecture_label "3 nm DSP" company-stated — that's actually a component statement, not an architecture label, but contract says raw label preserved. Not inference.
  - D02 tx_retiming "retimed (transmit direction)" — company-stated, supported.

  One subtlety: D02/D03 share S3 line 1979 which states shared descriptors for all three modules; the package justifies sharing because the sentence directly says shared. The second module (2nd of three demos) is skipped — contract allows exactly 5 seeds, and the second demo isn't in the instance list. The contract listed only first (LRO) and third (3nm DSP) demos. What is the second demo? Not in scope; contract says 5 instances only. OK.

  Question 3: TQ014 usage — frozen TQ014 parent is TQ009, question text "该路线解决了什么、代价是什么、新瓶颈在哪里、替代方案是什么？" The gate uses TQ014 as trade-off hinge with execution order TQ002/TQ003 → TQ009 → TQ010 → TQ014 → TQ011–TQ013, keeping parent TQ009. No QID/parent changes. Consistent. One tension: execution order places TQ014 after TQ010 and before TQ011–TQ013, but the frozen tree has TQ011's parent as TQ010 and TQ014 as sibling of TQ010 under TQ009. The candidate-tree lists TQ014 before TQ011 in the route trunk. The gate says "TQ014 的父问题仍可保持 TQ009；这里只调整研究执行顺序，不修改冻结问题树" — that's explicit and consistent. However note TQ011's inputs in the new flow now include TQ014 outputs ("物理变化/新瓶颈 → TQ011 能力要求"), which extends TQ011's dependency beyond its frozen parent TQ010. Not a tree violation (parents define navigation, Why Links express cross edges), but worth flagging as non-blocking: the execution-order dependency TQ014→TQ011 isn't expressed in the frozen parent structure; data layer must carry it via Why Link.

  Also potential hidden circularity: feedback new_bottleneck → TQ003 → next-gen route profile. Is there circularity TQ003 → (constraints) → TQ009 → TQ010 → TQ014 → new bottlenecks → TQ003? It's a generational feedback loop, declared as iteration across rounds, not within-round circular reasoning. Fine but note that within a single round, TQ014's upstream includes TQ003's current bottlenecks, and its output feeds TQ003; need to distinguish "current bottleneck snapshot" vs "newly generated bottleneck" to avoid self-referential loops within one round. They do distinguish (new_bottleneck feedback to next round). OK.

  Question 8: likely outsider errors, hidden circularity, missing acceptance contract, premature abstraction:

  - Missing acceptance contract: CONTEXT.md defines 问题验收合同 (Question Acceptance Contract). The package doesn't define one for TQ009 — promotion_blockers exist but no formal acceptance contract for when a seed becomes RP, or when TQ014 trade-off card is complete. The gate lists minimum requirements for a trade-off card (informal). This is a genuine gap: TQ009/TQ014 lack acceptance contracts before the next round. Also route-tradeoff-gate.md is schema-only; no gate on who fills evidence_status or what blocks trade-off claims besides "no baseline". Actually there are 强制防错 rules. But formal acceptance contract (Question Acceptance Contract vocabulary) not instantiated for TQ014. Non-blocking or blocking? The question asks to identify "missing acceptance contract" — I'll flag it as non-blocking correction: before the next draft-only TQ010/TQ014 experiment, write acceptance contracts.

  - 35-field schema: Is it sufficient/missing/over-modeled? Potential issues:
    - tq005 has both nominal_aggregate_rate and reported_aggregate_or_line_rate — good, captures 800G vs 850Gb/s.
    - media_lane_count/media_lane_rate split — good (D01 correction).
    - Missing: lane-direction? Tx/Rx asymmetry in lane counts (e.g., breakout 2x400)? Probably fine for seeds.
    - Possible over-modeling: light_source_wavelength duplicates tq005.wavelength? Not exactly (per-lane vs source). For a seed schema it's fine.
    - Possibly missing: power consumption / thermal fields? But those belong to TQ014 trade-offs, not axis values. Deliberately excluded.
    - fec_location in TQ006 plus fec_code in TQ005 — fine.
    - One redundancy: tq006.normalized_architecture is derivable from tx_retiming/rx_retiming + dac_adc; but normalization field is useful as controlled vocabulary. OK.
    - Over-modeling risk: 35 fields with UNKNOWN for demo statements means most fields permanently UNKNOWN for demos — acceptable, that's the point (exposing gaps).

  - Semantic corrections check (question 4):
    1. D01 media_lane_rate → UNKNOWN, symbol_rate keeps 53.125 GBd: correct — symbol rate ≠ bit rate per lane (PAM4 → 106.25 Gb/s per optical lane if 8 lanes, but lane count unknown; bit rate isn't directly reported). Correct conservative fix.
    2. D04: device_integration gets "MZM PIC" company-stated; pic_eic_integration → UNKNOWN. Correct: "MZM PIC" says modulator is in a PIC (device-in-PIC) but says nothing about PIC/EIC stacking. Wait — is "MZM PIC" placed under device_integration correct? device_integration = integration among devices; "MZM PIC" states the modulator is integrated in a photonic integrated circuit — that's device-level integration. Reasonable. Both corrections are sound and conservative. Note adjudication.md says D04 correction moves MZM PIC from pic_eic to device-integration label — consistent.

  - Question 5: check for residual inference. One candidate: D01 lane_organization "parallel" observed from S2 "Parallel MPO-16 receptacle" — directly stated "Parallel", OK. D01 host_lane_rate 106.25 Gb/s from "8x100G PAM4 retimed 106.25Gb/s" OK. D02/D03 host_lane_rate "200G" — "8x200G" directly stated. No inference from DR8 names. placement_class "front-panel pluggable" — this is a taxonomy mapping from form factor (G2), marked observed; strictly it's normalized/derived, not directly observed. G2 vocabulary mapping is controlled and documented; but observation_state "observed" slightly overstates — could argue for a fourth state or company-stated. Minor non-blocking note.

  - Company placement (Q6): blocked correctly; route_service_evidence separated; Jaccard 1.0 evidence supports the granularity alarm. The pilot says knowledge.yaml has 0 route KN, so confirmed group = 0. Good. One check: company-placement-rules says "271 条记录应全部只挂物理格" and pilot verified 271/271 closure, 0 nonexistent cells. Consistent.

  - Q7: candidate structure growth — yes: RQ000 → physical tree (PQ) + route tree (TQ) + Why bridge; seeds under TQ009; TQ010/TQ014/TQ011-13 layered; companies as external entities with typed attachments. Consistent with glossary.

  - Q1: two knowledge systems + Why bridge + unique company entities — maintained in candidate-tree.md sections 1, 2, 4. Yes.

  - Q2: user insight modeling — hinge models upstream (TQ002 constraints + TQ003 bottlenecks + TQ009 profile + TQ010 physical changes) → TQ014 conditional trade-offs → downstream (scenarios, new bottlenecks, capability requirements, alternatives) → feedback to TQ003. Matches glossary definition of Conditional Trade-off Hinge. Correct.

  Also check: does anything violate "no new QID"? follow_up_questions hang on TQ009/TQ010/TQ011 — wait, source-discovery follow-ups attach to TQ009, TQ010, TQ011; contract item 6 says only TQ009, TQ010, TQ011 allowed. Post-adjudication text section 6 adds TQ014 and TQ011–TQ013 notes — still no new QIDs. OK.

  One inconsistency: contract.md §7 says capability_match_candidate derivable "只有种子完成 TQ010/TQ011" — and company-placement-pilot says block until TQ010/TQ011. Consistent.

  Another check: adjudication.md claims "Miniconda 检查为 0 个结构问题" — I can't verify mechanically but can sanity check the yaml: all seeds have 35 leaf fields? D01 tq005: 16 fields (count: nominal, reported, host_lane_count, host_lane_rate, media_lane_count, media_lane_rate, modulation_format, symbol_rate, fec_code, pmd, media_type, reach, wavelength, lane_organization, optical_connector, fiber_mapping = 16 ✓), tq006: 7 ✓, tq007: 10 ✓, tq008: 2 ✓. 35 total ✓. missing_fields mechanical: D01 lists 18 unknown paths ✓ (4+6+8=18). ✓

  D02 missing_fields count: 11 tq005 + 3 tq006 + 9 tq007 = 23 ✓ (35-12=23 ✓).

  Also potential issue: D01 raw_architecture_label "retimed" company-stated but normalized_architecture UNKNOWN — that's odd: "retimed" is itself a normalized dictionary value in TQ006 (G2 lists "retimed" as an architecture class). Why is normalized UNKNOWN while raw is "retimed"? Because the raw label doesn't specify Tx/Rx scope so normalization withheld. Slightly conservative/inconsistent — G2's "retimed" class exists precisely as "module 侧存在 Tx/Rx retiming 的架构类；具体职责按实例记录". One could argue normalized_architecture: retimed (company-stated) is legitimate per G2. But withholding is conservative, not an error. Non-blocking note.

  D05: detector_type "photodetector" observed — generic, fine. light_source_type "EML" — EML is a transmitter device (DFB+EAM); calling it light_source_type is a bit loose but the source says "EML lasers", so the laser is an EML. Fine.

  Q8 additional: premature abstraction — the 35-field schema is quite detailed for 5 seeds; but adjudication shows fill rates 17–49%, which justifies fields as gap exposure. The trade-off gate schema (route-tradeoff-gate.md) is designed before any real trade-off card exists — a risk of premature abstraction; but it's explicitly schema-only, gated, and minimal. Note it.

  Hidden circularity: TQ009 needs TQ010 baseline ("选择哪一个字段更完整的 seed 作为参考基线？" is under TQ010) — TQ010's parent is TQ009, fine. The feedback loop TQ014→TQ003→next-gen TQ009 is cross-generational; within-round, no circularity. Also WQ002 connects TQ003/TQ009 → PQ010 "瓶颈为什么提高某种工程选择的相对价值" — overlaps conceptually with TQ014 (conditional relative value). Potential overlap/duplication between WQ002 (relative value of a choice given bottleneck) and TQ014 (advantages/costs). Worth flagging: boundary between WQ002 and TQ014 should be clarified to avoid double-booking the same causal claim. That's a genuine modeling observation.

  Also: "missing acceptance contract" — glossary defines 问题验收合同; no TQ009/TQ014 acceptance contract instantiated; promotion criteria exist informally (promotion_blockers, gate requirements). Non-blocking but should be done before next round? The review asks whether safe for next draft-only TQ010/TQ014 experiment — I'd say yes, conditionally: safe for draft-only, with recommended (non-blocking) fixes.

  Verdict: PASS_WITH_CHANGES (no blockers; several non-blocking corrections).

  Now write the structured verdict in Chinese. Cover:
  - verdict
  - blockers: none
  - non-blocking corrections
  - hinge assessment
  - 35-field schema assessment
  - explicit safe-for-draft-only answer
  - explicit statement no canonical/coverage/formal RP/company group approved

  Answer the 8 questions within those sections.

• 所有要求的文件已读完（CONTEXT.md 术语、包内 12 个文件、上游 TQ005–TQ008 有效口径、冻结问题树 5.2/5.3 节）。未读 `archive/`，未编辑任何文件，未联网。以下为结构化审查结论。

  ---

  # TQ009 Route Profile Seeds + 取舍铰链审查结论

  ## Verdict: PASS_WITH_CHANGES

  无阻断问题；有若干非阻断修正建议，均不影响下文的 draft-only 放行结论。

  ## Blockers

  无。逐项核验结果：

  - **两轮裁决链完整自洽**：第一轮正确识别 7 个复合字段混合已知/UNKNOWN 的问题，第二轮 35 叶字段原子化，`route-profile-seeds-effective.yaml` 中我逐种子复核了字段数（16+7+10+2=35）与 `missing_fields` 机械列表（D01=18、D02=23、D03=26、D04=29、D05=27），与 `adjudication.md` 完整度表（17/12/9/6/8）完全吻合。
  - **两处语义修正均正确且保守**：① D01 把 `53.125 GBd` 仅留在 `symbol_rate`、`media_lane_rate` 回退 UNKNOWN——符号率不等于每 lane 比特率，在 lane count 未知时不能回填，修正成立；② D04 把 `MZM PIC` 从 `pic_eic_integration` 移到 `device_integration`、前者回退 UNKNOWN——"MZM PIC" 只支持"调制器在 PIC 内"，不蕴含 PIC/EIC 集成方式，修正成立。
  - **问题 5（残余推断）专项核查通过**：DR8/DR8+/DR4+ 全程只作 alias；D03 的 3 nm DSP 未写成 full-retimed；D01 未从 EML 推 InP/DFB+EAM、未从 SiPh 惯例补光源/探测器；D04/D05 互操作两端点严格拆分，1310 nm 与 photodetector 未跨端点转移；D02/D03 的 8×200G 共享字段有 S3 原文"三个模块共享"的直接支持，不构成跨实例拼接；相邻 200G EML 演示（S4 line 1965）明确未并入 D05。

  ## 非阻断修正

  1. **`placement_class: front-panel pluggable` 的观测状态标记偏高**。它是从 OSFP/QSFP-DD 经 G2 受控词表映射而来，本质是规范化推导而非实例直接观察，却标为 `observed`。建议：或在观测状态中增加 `normalized` 一类，或在种子层显式注明该字段经 G2 映射。当前四态（observed/company-stated/permitted/unknown）没有它的准确位置。
  2. **D01 的 `normalized_architecture: UNKNOWN` 与 G2 字典存在张力**：TQ006 字典中 `retimed` 本身就是受控类（"具体职责按实例记录"），D01 有 raw label `retimed` 却拒绝规范化。保守方向没错，但应在种子里写明"拒绝规范化"的判据，否则下游会怀疑规范化规则本身不稳定。
  3. **WQ002 与 TQ014 的职责边界需澄清**：WQ002 问"瓶颈为什么提高某种工程选择的相对价值"，TQ014 记录条件化优势/代价——二者都承接"瓶颈→相对价值"这层因果。若不划清（例如 WQ002 存 Why 因果边、TQ014 存条件化比较结果卡片），同一主张可能被双记。
  4. **TQ014→TQ011 的执行依赖未落在冻结结构中**：执行序变成 TQ002/003→TQ009→TQ010→**TQ014**→TQ011–013，但冻结树里 TQ011 父问题仍是 TQ010，TQ014 是 TQ009 下的平行节点。包内已声明"只调执行顺序、不改冻结树"，方向正确；但"新瓶颈作为 TQ011 输入"这条边必须显式以 Why Link 承载，否则下一轮的依赖审计会丢边。
  5. **缺少正式的问题验收合同（Question Acceptance Contract）实例**：CONTEXT.md 已有该术语，但 TQ009/TQ014 目前只有分散的 promotion_blockers 和取舍卡最低要求，没有成文的验收合同（允许答案体系/覆盖条件/停止条件）。下一轮 draft 实验前建议补齐，哪怕只是一页。
  6. **轻微过早抽象风险**：`route-tradeoff-gate.md` 在尚无任何真实取舍卡的情况下定义了完整 schema。风险被"本轮只建 schema、不产出优劣结论"的纪律对冲，可接受；但第一张真实取舍卡落地时应预留 schema 修订窗口，不要把 v1 字段当冻结。

  ## 取舍铰链评估（问题 1/2/3/7）

  - **两体系结构保持**：candidate-tree.md 维持物理知识体系 + 技术路线体系两套坐标，Why 明确不是第三主干而是桥（WQ001–WQ004 只存跨枝因果边），公司为树外唯一实体、经带类型关系挂入、不因多格复制节点。问题 1 通过。
  - **用户新洞察建模正确**：铰链的上游（TQ002 场景约束 + TQ003 瓶颈 + TQ009 画像 + TQ010 物理变化）、中段（TQ014 条件化优势/代价/新瓶颈/替代）、下游（适用场景、验证问题、能力要求→TQ011→TQ012/013）、反馈（new_bottleneck→TQ003→下一代画像）与 CONTEXT.md 的"条件化取舍铰链"定义逐项对应。反馈环是跨代际的（当前瓶颈快照 vs 新生瓶颈有区分），不构成单轮内的循环论证——未发现隐藏循环。
  - **TQ014 使用合规**：QID、父问题（TQ009）、文案均未改；执行顺序调整被显式声明为研究顺序而非树修改。问题 3 通过，无需在下轮前改动依赖/顺序（但建议落实上面第 4 条）。
  - **候选树生长路径真实**：RQ000→物理格（PQ001–PQ010）与路线轴（TQ001–TQ009）→种子→物理变化（TQ010）→取舍（TQ014）→能力（TQ011）→公司（TQ012/013），且明确"缺口先生成研究注记、反复出现才提议新 QID"，是从基础问题逐层长出而非被产品名打散。问题 7 通过。

  ## 35 字段原子 schema 评估（问题 4）

  - **充分性**：覆盖 TQ005–TQ008 四轴的最小可比较字段，且 nominal/reported 双速率、lane count/rate 分离、symbol_rate 独立、raw label 与规范化值分栏——恰好吸收了 D01 暴露的 800G/850 Gb/s、DR+/DR8 等真实歧义。
  - **无关键缺失**：功耗/热/成本刻意不在内是正确的——它们属于 TQ014 取舍维度，不是轴值。 fec_code（TQ005 链路边界）与 fec_location（TQ006 职责）的分置也合理。
  - **无实质过度建模**：`normalized_architecture` 可由 tx/rx/dac_adc 推出，但作为受控词表槽位有存在价值；17%–49% 的填充率恰恰证明字段集在暴露缺口而非堆砌。两处语义修正后，UNKNOWN 纪律在有效 YAML 中无例外（我复核了全部 5×35 个叶字段）。

  ## 公司挂载评估（问题 6）

  阻断逻辑正确且被证据支撑：`capability_match_candidate` 在 TQ010/TQ011 完成前默认阻断；`route_service_evidence` 与能力匹配、供货观察三者分栏，`edges.csv` 不自动升级；五个种子仅挂 Coherent 为实例主体。800G DR8 与 1.6T DR8 粗映射推出完全相同的 83 家公司（Jaccard=1.0）是对"粒度不足以区分路线"的硬证据，试挂报告的 271/271 闭合、155 去重公司、43 家跨格公司数据支持"唯一实体+带类型关系"而非树内复制的结论。

  ## 是否安全用于下一轮 draft-only TQ010/TQ014 实验

  **安全，可以放行为 draft-only 实验输入。** 前提条件：下一轮仍保持 draft_only、禁止 canonical/覆盖变更；TQ014 只按 `route-tradeoff-gate.md` 的取舍卡 schema 产出草案、不出优劣结论；公司挂载阻断维持到 TQ010/TQ011 完成之后。上述 6 条非阻断修正建议在下一轮实验前或随实验一并落实，其中第 3、4、5 条（WQ002/TQ014 边界、TQ014→TQ011 依赖边、验收合同）对下一轮质量影响最大。

  ## 明确声明

  本审查**不批准**任何 canonical 写入、覆盖状态变更、正式 `RP###` Route Profile、公司能力群/服务群或新 QID。五个 `RPS-D##` 对象仍为 draft-only 种子，TQ009 未标记覆盖，83 家粗候选不构成任何公司分组依据。

To resume this session: kimi -r session_cd580a3c-a091-4a54-8e23-4ab624a30384
