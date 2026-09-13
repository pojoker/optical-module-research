• 我先读取审核包的主文件。

• 现在读取对照文件。

• 再快速核对 AGY 原始输出与 Pi prompt，确认边界描述与实际一致。

• # 审核结论：PASS_WITH_FIXES

  包：`docs/research/pi-packages/2026-08-26-agy-route-field-fill-v2/`（只读审核，未修改任何文件）。对照了 `research_questions.yaml`、TQ009 seeds 包（contract + post-adjudication-effective-text）和 TQ010/TQ014 合同。

  ## 逐问回答

  **1. AGY 边界：守住。**
  `run.yaml` 三条 notes、`pilot-v1-audit.md` 的 v2 硬门、`adjudication.md` 的"仅消费 `pi-handoff.md`，不得直接消费 AGY raw"形成三层一致约束；`source-excerpts.md` 用页码 + 短引文 + SHA256 提供独立可复核锚点，Pi 侧诚实声明了锚点缺口而非虚构引文。AGY 的任何 generated synthesis（如 v2 raw 里 `-2N` suffix override 解释、8 optical lanes 推断）均未进入下游口径。

  **2. EML 字段边界：正确。**
  - exact SKU：系列字符串 `FTCE4527E1PxA-2N` 与样例标签 `FTCE4527E1PCA-2N` 区分清楚，样例标签不晋升为可下单证明；
  - GA/量产：preliminary 文档只支持文档成熟度，GA 保持 UNKNOWN；
  - TEC：TDECQ/TECQ 正确排除，内部 TEC UNKNOWN；
  - FEC：存在性与 BER 门槛可记录，类型与终止位置 UNKNOWN；
  - 内部实现：EML die topology、TOSA/ROSA、driver/TIA、lens coupling 全部阻断；
  - EML/PIN 在**产品系列层**恢复是正确的本地修正——S-EML-2 官方产品页参数表对该系列明示 `Transmitter: EML / Receiver: PIN`，AGY v2 只查 datasheet 而标 UNKNOWN 属于过度保守，裁决纠正有据；
  - 温度 `x=C/L` 按条件化选项处理、heatsink 标签冲突冻结为 `UNKNOWN_CONFLICTING_LABELS`，均与来源一致。

  **3. SiPh `FAIL_NO_SINGLE_INSTANCE` 边界：正确。**
  `adjudication.md` 明确列出四条不支持的负向结论，并指出 AGY 未提供逐条查询串/抓取时间/升级阶梯，候选表只是 discovery log 而非可复现 absence evidence；`pi-adjudication.md` 修正项 4 进一步把负向发现的举证责任（完整检索轨迹）写实。两侧的 Intel MDDS/OFC 摘要/portfolio 页均只按各自证据等级入账，未拼合。

  **4. 四层 evidence subject 模型：兼容，是补层不是重复。**
  现有 TQ009 seed schema 的 `observation_state`（observed/company-stated/permitted/unknown）回答"字段值怎么来的"，`product_or_demo`/`evidence_type` 只区分产品 vs 演示；四层模型回答"证据描述的主体是什么"。映射关系：L1↔product instance seed、L4↔demo_endpoint（已有），L2 平台组件证据此前被合同正确排除（如 Intel OCI 不得转种子），L3 instance–platform binding 是真正的新维度——RPS-D05 的 `EML laser` raw label 正是缺这一层导致只能记 company-stated。`pi-output.md` 把四层与观测状态正交使用，没有错层。风险只在未来 schema 定型时若用四层**替换**观测状态词汇才会错层，注记本身已把定型留给后续裁决。

  **5. "1 新 + 3 合并"：正确。**
  - `TQ013-note-service-without-customer` 合并有据：TQ009 合同 §7 已要求 route_service_evidence 直接连接公司与精确实例、禁止供货/客户边自动升级，post-adjudication §6 已有同题开放问题；
  - `TQ014-note-controlled-comparison` 合并有据：TQ010/TQ014 合同 §4 已规定非同条件 → advantages/costs 为空、公司一般表述不得转移；
  - `TQ007-note-platform-binding` 归 TQ009 有据：TQ007 是轴值字典问题（"有哪些选择"），binding 证明标准属于实例画像证据结构，与 `TQ009-note-evidence-subject` 同域；
  - 新增注记计数为 1、不新建 QID，符合既有惯例。

  **6. 下一步 2–3 家厂商 AGY exact-entity source chase：允许。**
  `pi-adjudication.md` 修正项 3 已把 Pi 的第 8 条（9 家捆绑）拆成"一家一条任务、本批只做 2–3 家"，符合 exact entity + fingerprint 原则。继续保持 draft-only 的前提条件：沿用 v2 六条硬门、允许失败且失败须留完整检索轨迹、未命中不转负向事实、产物仍走 handoff → 裁决两级，不直接进字段表。

  ## 问题清单

  **P0：无。** 无 canonical 写入、无覆盖状态变更、无 WHY/公司群/正式 RP promotion，全部布尔声明与实际一致。

  **P1（下游消费前必须处理）：**
  - `pi-output.md` 的字段卡以"页码/引文 UNKNOWN、URL 为唯一锚"写成，且 TQ008 留有"回源未见 Type 2 字样时降级为 OSFP-only"的悬置 caveat；`source-excerpts.md` p.6 短引文已实际补齐 Type 2、符号速率、波长范围、功耗上限等锚点。裁决文件虽规定了消费顺序，但 `pi-output.md` 本体没有"锚点已由 source-excerpts 补齐、本卡 caveat 已解除"的就地标记，单独阅读该文件会错误降级多个 observed 字段。建议下次可写时在包内加一行 errata/状态标记。

  **P2：**
  - `source-excerpts.md` 记录了 S-EML-2 的 `form factor: OSFP RHS` 页面原值，但未把它与 heatsink 冲突关联；按 TQ009 的 alias/raw label 惯例，该字符串应作为原始标签保留并标注其属于冲突标签集的一部分（页面侧 RHS vs datasheet 侧 `A: Closed Heatsink`），否则下游可能静默丢失这一冲突证据。
  - `agy-eml-recheck-output.md` / `agy-siph-retry-output.md` 内仍含未被裁决确认的解释性文字（如 `-2N suffix overrides to flat-top`、"8 optical lanes"），目前仅靠消费纪律隔离，文件头无指向 `adjudication.md` 的警示；建议后续补一行头部声明。
  - 下一轮 source chase 建议把 Pi 查询建议 #1–#7（两个 Coherent 来源与三个 Intel 来源的回源锚点补齐）与 2–3 家厂商定向检索并行，而非只做厂商侧；EML 卡的多个 observed 字段仍欠页码级锚点。

  本审核仅为只读意见，不涉及也不建议任何 canonical 写入、覆盖状态变更、WHY 边、公司群或正式 Route Profile promotion。
