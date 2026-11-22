**Verdict：PASS**

18/18 `validation-final.yaml` 全过。数字口径一致：271 点 / 269 合格 / 2 阻断 / 258 facet-explicit / 13 cell-only / 484 facet / 272 role / 56 路线试挂 / 6+16 边 / 0 服务边 / 41 格（M2c、EQ8 空）——`attachments`、`graph`、`tree.md`、`audit.md`、校验脚本对齐。Facet/role 由 486/275 降到 484/272，与收紧后的断言一致。`canonical_write_performed: false`。本轮不要求正式路线集团、WHY 边或 canonical 写入。

## 未解 P0 / P1

无。

## 已核先前必改（含原 P1 语义项）

| 项 | 现状 |
|---|---|
| P039 `module_integrate` 禁跨引号 | span 仅为 `光模块为主的光通信产品的研发、制造`；registry 正则已禁 `，。；:"“”` |
| P244 角色锚定同一产品对象 | 仅 `光模块全产业链生产制造`，不再吞机加工/封装清单 |
| P193 阻断点不输出行公司成熟度 | `maturity_markers: []`；图 MOD1 `observed_maturity_marker_types` 只聚合 `attachment_eligible` |
| P199 子公司 + 去掉工艺开发→foundry | `controlled_subsidiary`；无 `foundry_platform`；registry 已改为 `Foundry`/`工艺平台`，包内无「工艺开发」 |
| P217 残缺收入句无设备角色 | `role_assertions: []`（「销售」仅作 marker） |
| P256 未来投产无当前制造角色 | 无 role，仅 `planned_or_future` |
| P245 截断套管 | 无 `ferrule_type.sleeve` |
| `route_relation` 合同 | 已改为 `null \| object`，与 YAML 一致 |

P040/P193 仍阻断且无 facet/role；路线服务边仍为 0。

## 残留风险

- P193 仍挂空 `route_relation`（候选空、`route_service_conclusion: false`），不是能力结论，网页须当阻断指针。
- P039 的 `product_offer` 仍是句内单独「销售」，人审角色队列合理。
- 无稳定 `company_id`（155 串 / 154 key，云岭 alias 未合并）；官网锚点仍是既有点问题。
- 6 条 requirement candidate 须保持虚线；角色「销售/生产」在收入/规划句中仍可能误触发，须人审。
