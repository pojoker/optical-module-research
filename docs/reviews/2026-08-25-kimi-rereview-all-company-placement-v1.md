• 我先读取该包目录结构和核心文档。

• 再读构建/校验脚本，并从 points.csv 抽取 8 条待检 point。

• points.csv 抽取为空，检查表头字段名。

• 现在抽取 attachments YAML 中这 8 条提案。

• 再看构建脚本与 registry 相关改动是否结构性修复。

• 做一次独立的 span 复现与计数交叉核对（只读）。

• # 复审结论：全量公司挂载包 v1（2026-08-25）

  **Verdict：PASS**

  本轮在 Cursor 评审之后的修复版上做了只读复核：合同、registry、构建/校验脚本、8 个重点 point 逐条对照 `points.csv` 原引语（span 独立复现全过）、graph 汇总与文档数字交叉一致，canonical 目标 `git status` 零改动。Cursor 评审的 3 条 Required fixes 全部落地且是结构性修复（registry/override/聚合过滤），不是补丁式硬编码。

  ## 未解决 P0/P1

  - 无 P0，无 P1。

  ## Fixes verified（对照 `docs/reviews/2026-08-25-cursor-review-all-company-placement-v1.md`）

  - **P039 跨引号角色**：`module_integrate` 正则已排除引号与句读边界（registry `role_rules.module.module_integrate` 的 `[^，。；;：:"“”\n]{0,60}`），span 收为 41–58「光模块为主的光通信产品的研发、制造」；`product_offer`/maturity 的「销售」「研发」均落在第一段引语内，不再跨界。
  - **P244 对象锚定**：span 99–110「光模块全产业链生产制造」，不再把机加工/无源/封装焊进 module_integrate；MOD3 cell-only 保持正确。
  - **P199 主体与 foundry facet**：`subject_overrides` 标为 `controlled_subsidiary`；C4 `foundry_platform` 模式删去「工艺开发」（现仅 `Foundry`/`工艺平台`），facet 只剩 `platform.silicon_photonics`（人审候选，合规）。与 P178 GouMax 主体规则对称。
  - **P193 阻断净化**：`affiliate_only`、无 facet/role/maturity；`build_full_placeable_graph.py:60` 的 cell 成熟度聚合显式过滤 `attachment_eligible`，MOD1 节点 `observed_maturity_marker_types` 不含 `small_batch`，参股「小批量交付」未漏入行公司汇总。
  - **P217 / P256 过标角色**：经 `blocked_roles` 分别拿掉 `equipment_supply`、`component_manufacture`，role_assertions 均为空；P256 仅保留 `planned_or_future` marker，未来投产未写成当前制造。
  - **P245 截断 facet**：无 `ferrule_type.sleeve`（「套管」模式不命中「插芯套组件」），保留 ceramic_ferrule / fiber_connector。
  - **合同一致性**：`contract.md` 的 `route_relation: null | object` 已与实现对齐（原 `none | see_route_pilot` 表述已改）。
  - **数字一致性**：271/269/2 阻断、258 facet-explicit、13 cell-only、484 facet / 272 role、56 试挂、6+16 边、0 WHY/0 路线服务边，在 summary、graph readiness、树文档、audit、validation-final 间一致；`semantic_review_fix_invariants` 7 项全 true。（Cursor 评审表中写的 486/275 与现行 484/272 之差正是上述修复移除的 2 facet + 3 role，非不一致。）

  ## Residual risks（可接受，需后续人审）

  - **P193 仍带 route_pilot_ref 空指针**（候选为空、`route_service_conclusion: false`）：网页必须按 `attachment_eligible` 过滤，不能把阻断点渲染成路线关联。
  - **合格点上的 point 级 marker 仍是粗正则**：如 P217 残缺收入句仍挂 `actual_offer_or_delivery`（销售）、P039 的 研发/销售 marker；不继承到 facet，但 cell 级成熟度展示需人审。
  - **role_negative_patterns 覆盖有限**，未来/否定语境的角色误判只能靠 101 条 role unknown/blocked + 170 条 role-explicit 的人审队列消化。
  - **稳定 `company_id` 仍缺**（155 字符串/154 key、云岭光电 alias 未合并），不得作为实体主键增量落库。
  - 本轮范围边界保持正确：无正式路线集团、无 WHY 因果边、canonical 未写，均不应视为缺口。
