# 全量公司可放置图草稿审查

**Verdict：PASS**

15/15 机械校验只能证明双射、span 可复现、阻断点无 facet/role、成熟度未继承、canonical 未写。本结论建立在语义抽检上：**271 条都有图处置，路线服务边为 0，P040/P193 阻断方向正确，13 条 cell-only 的粗粒度大体站得住。** 仍有若干正则/主体误判，必须当成人审草案，不能当公司能力或路线服务事实渲染。

本轮不要求正式路线集团、WHY 因果边或 canonical 写入。

---

## Findings

### P1

1. **`all-company-attachments-draft.yaml` · P039 · `role_assertions.module_integrate`**
   第二段 span 是 `研发、制造和销售"；"光模块`（offset 53–67），正则跨过两条引语的引号边界，把“光通信产品的研发、制造和销售”与后一句“光模块业务收入占比”焊成同一对象。`product_offer`/`maturity_markers` 的“销售”同理。Facet 停在 `cell_only` 是对的；角色不是。

2. **同文件 · P244 · `role_assertions.module_integrate`**
   span `设计平台，以及具备精密机加工、无源组件、SMT、TO-CAN、OSA光器件、COB、BOX、光模块` 把机加工/无源/封装与光模块收进同一 `module_integrate`。这不是“漏 facet”（MOD3 没有泛称光模块刻面，cell-only 正确），而是研发/生产动作未锚定同一产品对象。

3. **同文件 · P199 · `subject_scope` + `manufacturing_mode.foundry_platform`**
   引语主语是“赛莱克斯北京”的工艺开发及产品验证，行公司是赛微电子，却标成 `direct_or_unresolved`。`工艺开发` 被 registry 映射为 `foundry_platform`，把验证级工艺开发写成代工平台能力。对照 P178（GouMax → `controlled_subsidiary`）主体规则不对称。硅光子作为枚举项提出 `platform.silicon_photonics` 可保留为人审候选。

4. **同文件 · P193 · `maturity_markers` + `route_relation`**
   阻断正确：`affiliate_only`、无 facet/role、`attachment_eligible: false`。但“小批量交付”仍挂在通宇通讯提案上，且仍链到路线试挂（候选为空、`route_service_conclusion: false`）。图里 MOD1 的 `observed_maturity_marker_types` 会吃进这条参股交付。网页若按 cell 汇总成熟度，会把参股事实记到行公司。

5. **同文件 · P256 · `role_assertions.component_manufacture`**
   “有望…2027年正式投入生产”同时有 `planned_or_future` 与由“生产”打出的制造角色。未把 point「在建」继承给 facet（好），但角色把未来投产写成当前制造。未从判定闸偷硅光 Foundry（正确）。

6. **同文件 · P217 · `equipment_supply`**
   残缺收入句里的“销售”打成设备供应角色。cell-only 正确（无仪器类型），角色过标。

### P2

7. **`full-facet-registry-draft.yaml` · `C4.manufacturing_mode.foundry_platform` 含 `工艺开发`**
   任何 C4 引语里的“工艺开发”都会变成 foundry 刻面。P199 是实例，不是孤例风险。

8. **`contract.md` vs 提案 YAML**
   合同写 `route_relation: none | see_route_pilot`，实现是 `null` 或带 `requirement_candidates` 的对象。增量落库需要适配，否则网页/下游 schema 对不上。

9. **`P245` · `ferrule_type.sleeve` ←「套组件」**
   多半是“插芯套组件”截断，语义偏了，尚未升成公司能力结论。

10. **稳定 `company_id` 缺失**
    155 字符串 / 154 key、云岭光电 alias 未合并，包内已声明。网页可展示字符串，不能当实体主键增量写入。

---

## 抽检对照（简报 7 问）

| 项 | 判断 |
|---|---|
| 13 条 cell-only | 应保持粗粒度。P075 无 TOSA；P168 无 PCB；P217 无仪器类型；P241–P243 OSA 不拆 TOSA/ROSA/BOSA（D12 才有 OSA 刻面）；P244 无电信/接入刻面；P256 引语无 SiPh/PIC。未见应提却未提的明确 facet。P040/P193 计入 13 条是文档口径，合格 cell-only 实为 11。 |
| P040 / P193 | P040 定义性内部结构，阻断 `evidence_scope` 正确。P193 参股四川光为，阻断 `subject_scope` 正确。集团/收购：P009/P069/P130–P133/P178/P261 有 scope 且需人审。缺口是 **P199** 未标子公司。 |
| 研发/生产/销售同一对象 | **P039、P244 失败**；P069 并购后 FAU 的研产销同一对象，可接受。 |
| 成熟度继承 | `point_status_inherited_by_facets: false`，facet 均为 `not_inferred`。问题是 **marker 仍打在阻断点/未来投产角色上**，不是 status 复制。 |
| 56 条路线试挂 | 6 条 `generic_scope`/`attribute_exact` candidate，16 条 related-only，`COMPANY_SERVES_ROUTE`/`route_service_conclusion` 为 0。未把 related 升成 requirement。P193 仍挂空试挂指针。 |
| 数字一致性 | 271 / 269 合格 / 2 阻断 / 258 facet / 13 cell-only / 486 facet / 275 role / 56 路线 / 6+16 边 / M2c·EQ8 空格，树、图、audit、validation 一致。 |
| 网页/YAML 增量 | `canonical_write_performed: false`，无公司组。缺 `company_id`、`route_relation` 枚举与实现不一致。有 `review_status`/`attachment_eligible`，可做草稿层，不可当正式能力库。 |

---

## Required fixes

无 **P0 阻断项**。若网页要展示角色或 cell 级成熟度汇总，增量前应处理：

1. 收紧模块 `module_integrate` 正则，禁止跨引号/跨产品清单（至少 P039、P244）。
2. P193：阻断点不要输出行公司成熟度，cell 汇总排除 blocked。
3. P199：标 `controlled_subsidiary`（或等价），拿掉由「工艺开发」推出的 `foundry_platform`。

---

## Residual risks

- 官网锚点（P241–P244、P259 等）是既有 points 问题，本包未新造能力。
- 角色「销售/供应商/生产」在收入、客户名单、未来投产句中仍会误触发；人审队列（99 条 role unknown/blocked、74 条多类 marker）是正确状态。
- 6 条 requirement candidate 全是泛 scope 或单属性，展示必须保持虚线。
- 无 WHY 边、无正式路线集团：应保持，不是缺口。
