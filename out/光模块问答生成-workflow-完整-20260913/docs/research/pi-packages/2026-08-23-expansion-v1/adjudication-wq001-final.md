# WQ001 attempt-2 Codex 最终裁决

流程结论：`process_pass`
内容结论：`usable_draft_with_three_reading_errata`
知识库动作：无；WQ001 不改变状态

## 通过

- 五条候选桥均采用“场景需求 → 接口/链路约束 → 物理机制 → 可观察指标”；
- 每条均列 route-side 与 physical-side 证据，B4 对同一 OIF 来源的两侧使用作了披露；
- 未从约束跳到 EML、SiPh、LPO、CPO 路线选择或公司受益；
- 成本金额、维护成本定量、CPO 实测功耗、optical-budget 数值、ports/RU 等证据缺口保持为空；
- PQ009 只标作待验证问题，未被宣称已回答；
- 五个唯一 relation draft ID，全部 `would_mark_covered: false`，未生成新问题 ID。

## 有效勘误

1. `WQ001-a2-b05` 的关系强度改读为“受限推论”。其中 hot-pluggable、rework、field
   access 等物理属性有事实或规范支持，但“维护需求映射到这些属性”是跨来源合成，不能整体升格为
   “规范结构支持”。
2. 摘要中的“需求的验证只能落在物理层”改读为：“本轮讨论的五类工程需求，需要进一步映射成
   可验证的接口与物理指标。”原句不能泛化到商业、组织或监管需求。
3. 文中的 `OIF CPF` 统一改读为 `OIF Co-Packaging Framework Document`（本包冻结文件
   `OIF-Co-Packaging-FD-01.0.pdf`），不把临时缩写当成正式文档名。

其余草案按原稿边界使用。上述裁决不代表 WQ001 已覆盖，不授权写入 `why_links.yaml` 或其他
canonical 文件。

## 外部审阅后补充裁决

1. B2 不再把 IEEE 可插拔 PMD reach 与 OIF CPO mid-board connector budget 拼成同一条有效桥。
   有效 B2 只保留 reach → media/PMD → 500 m SMF 单产品接口实例；CPO connector budget
   退回物理注记，量值挂 `PQ009`、形态挂 `PQ005`。
2. B3 的 OSFP §15.8 在 route/physical 两侧重复使用，必须披露为“单源双侧使用、非独立双源
   证实”；CPO target 不并入 OSFP 产品链。
3. B5 拆成可插拔产品与 CPO framework 两个场景分支，二者强度均为受限推论，不得合成通用
   维护物理或成本结论。
4. 仓库实际 WHY canonical 槽位是 `knowledge.yaml#why_links`；本轮未写入该槽位。
5. 下一批不得单独消费 raw；统一先读 `post-review-effective-text.md`。
