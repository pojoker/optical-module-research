# Edge type/subtype schema 提案（D3 / C 项）

**状态**：提案，待终验；不修改现行 236 边台账。  
**目标**：把供货、股权、担保、裁判文书事件、产能事件和专利事件分层表达，避免“出现过关系”被误算成“当前供货关系”。

## 1. 总体设计

采用“共享核心字段 + 类型扩展字段”的两层 schema：

1. 现行 `output/edges.csv` 前 10 列保持不动，保证旧数据可读。
2. 新增共享字段；股权、担保等非供货记录进入独立 layer，终验通过前不写回正式供货台账。
3. `edge_type` 表示关系大类，`edge_subtype` 只表示同一大类内的事件/关系语义；主体角色、阈值、状态和期间另设字段，不把多维语义压进一个 subtype 字符串。
4. 所有非 `supply` 类型强制 `include_in_supply_concentration=false`。

建议的 `edge_type` 受控枚举：

| edge_type | 含义 | 可否进入供货集中度 |
|---|---|---|
| `supply` | 已有具名交易证据支持的供货/代工/分销关系 | 仅终验明确允许时 |
| `equity` | 持股、控制或历史股权阈值关系 | 否 |
| `guarantee` | 担保授权、实际担保敞口或解除事件 | 否 |
| `legal_event` | 裁判文书证明的历史合同或争议事件 | 否 |
| `capacity_event` | 环评/能评等披露的产能、设备类型和地点事件 | 否 |
| `patent_event` | 共同申请或权利转让事件 | 否 |
| `other` | 暂不能归入上述类别；必须有说明并进入治理复核 | 否 |

当前 D1 校验器中的 `legal_event/other` 可保留；建议终验将 `capacity_event`、`patent_event` 从 `other` 中拆出，防止后续规则无法按类型硬隔离。

## 2. 共享核心字段

| 字段 | 类型/枚举 | 必填 | 规则 |
|---|---|---:|---|
| `edge_id` | string | 是 | 全局唯一；同一证据中的不同事件不得共用一个 ID |
| `edge_type` | 上表枚举 | 是 | 大类 |
| `edge_subtype` | §3 受控枚举 | 是 | 必须与 `edge_type` 配对合法 |
| `from_entity_id` | registry entity_id | 是 | 按语义角色定方向，不按披露表左右位置定方向 |
| `to_entity_id` | registry entity_id | 是 | 同上 |
| `from_role` | string enum | 是 | 如 `shareholder/guarantor/supplier/assignor` |
| `to_role` | string enum | 是 | 如 `investee/guaranteed_party/customer/assignee` |
| `scope_id` | registry scope_id | 是 | 指向 E 项观察 scope；禁止只写自由文本“含关联方” |
| `effective_from` | `YYYY-MM-DD`/`YYYY-MM`/`YYYY`/unknown | 是 | 不得用披露日冒充生效日 |
| `effective_to` | 同上/open/unknown | 是 | 历史或终止关系必须尽量给出上界 |
| `relationship_status` | `current/historical/terminated/approved_not_drawn/disputed/unknown` | 是 | 与证据强度分离 |
| `amount_value` | decimal/null | 否 | 结构化数值；原文金额仍保留在现行“占比或金额” |
| `amount_currency` | ISO 4217/null | 否 | 如 `CNY/USD` |
| `amount_unit` | `yuan/wan_yuan/...` | 否 | 禁止只存裸数字 |
| `percentage_value` | decimal/null | 否 | 不把“5%以上”写成精确 5.00% |
| `percentage_operator` | `eq/gt/gte/lt/lte/range/unknown` | 否 | 与 `percentage_value` 配套 |
| `source_type` | enum | 是 | `annual_report/prospectus/court_judgment/environmental_filing/patent_record/...` |
| `source_year` | year/string | 是 | 证据文件年份，不等同于关系有效期 |
| `discloser` | entity/string | 是 | 明确谁披露 |
| `provenance` | `primary/secondary_with_citations/secondary_no_itemized_source` | 是 | 评级报告无逐项原始出处不得冒充发行人一手披露 |
| `evidence_file` | path/title | 是 | 证据文件 |
| `anchor_url` | URL | 是 | 锚点 URL |
| `retrieved_date` | `YYYY-MM-DD` | 是 | 四件套检索日期 |
| `hit_quote` | string | 是 | 命中引语；不得只写章节名 |
| `edge_grade` | 现行边等级/新证据等级 | 是 | 证据强弱，不表达 current/historical |
| `verification_status` | enum | 是 | `candidate/verified/rejected`；正式写入权归终验 |
| `include_in_supply_concentration` | boolean | 是 | 非 `supply` 必为 `false` |
| `notes` | string | 否 | 限制、冲突和可推翻条件 |

最低准入仍满足项目红线：`证据文件 + 年份 + 披露方 + 占比或金额 + 锚点URL + 边等级`；本提案额外把检索日期、命中引语、来源类型和期间结构化。

## 3. subtype 注册表与语义

### 3.1 `supply`

| edge_subtype | 精确定义 |
|---|---|
| `current_supply` | 一手披露支持报告期内发生的具名供货关系 |
| `historical_supply` | 一手披露支持过去期间发生供货，但已有明确终止/死亡边界 |
| `contract_manufacturing` | 明确为代工/委托加工 |
| `distribution` | 明确为代理或分销夹层，不把分销商下游自动外推为客户 |
| `equipment_supply` | 仅在环评/能评原文具名供应商且交易语义明确时使用；否则不得由 `capacity_event` 转换 |

### 3.2 `equity`

| edge_subtype | 精确定义 |
|---|---|
| `equity_direct` | 披露方明确为直接持股 |
| `equity_indirect` | 披露方明确为间接持股；不得默认等于穿透后精确经济权益 |
| `equity_control` | 有控制/共同控制认定，但持股比例不是承重事实 |

股权专属扩展字段：

| 字段 | 枚举/类型 | 规则 |
|---|---|---|
| `ownership_method` | `direct/indirect/control/unknown` | 与 subtype 一致 |
| `shareholder_entity_id` | entity_id | 应与 `from_entity_id` 一致 |
| `investee_entity_id` | entity_id | 应与 `to_entity_id` 一致 |
| `ownership_chain` | entity_id array/string | 间接持股必须保留链条；缺中间主体则标 unknown |
| `voting_rights_percentage` | decimal/null | 与持股比例分开 |
| `calculation_basis` | `disclosed/calculated/not_calculated` | 禁止把链条各层比例机械相乘后冒充披露值 |

示例 EG-01 应编码为：

- `edge_type=equity`
- `edge_subtype=equity_indirect`
- `from=中际旭创`，`to=源杰科技`
- `percentage_value=5`，`percentage_operator=gte`
- `relationship_status=historical`
- `effective_to=2023-03-09`（2023-03-10 稀释事件的前一日；若终验不接受日级推定则写 `2023-03`）
- `calculation_basis=not_calculated`
- `include_in_supply_concentration=false`

招股书的 6.71% 与 86.46%只进入 `ownership_chain` 说明，不能相乘生成“中际旭创精确持股比例”。

### 3.3 `guarantee`

| edge_subtype | 精确定义 |
|---|---|
| `guarantee_authorization` | 只有审批额度/上限；实际发生额或余额为 0、未知 |
| `guarantee_exposure` | 披露期内存在实际发生额或担保余额 |
| `guarantee_release` | 原文明确解除、履行完毕或终止的事件 |

“母对子”“关联方为发行人担保”“共同担保”是主体角色/上下文，不做 subtype，以免与授权/实际敞口两个正交维度组合爆炸。

担保专属扩展字段：

| 字段 | 枚举/类型 | 规则 |
|---|---|---|
| `guarantor_entity_ids` | entity_id array | 共同担保不得压成一个虚构法人 |
| `guaranteed_party_entity_id` | entity_id | 应与 `to_entity_id` 一致 |
| `creditor_entity_id` | entity_id/null | 未披露则 null，不猜 |
| `guarantee_context` | `parent_to_subsidiary/related_party_for_issuer/joint_guarantors/other` | 关系上下文 |
| `guarantee_form` | `joint_liability/general/pledge/mortgage/repurchase_obligation/unknown` | 保证形式 |
| `approved_limit` | decimal/null | 审批额度 |
| `actual_incurred_amount` | decimal/null | 实际发生额 |
| `ending_balance` | decimal/null | 期末余额 |
| `released_flag` | `yes/no/partial/unknown` | 原表“是/否”与叙事冲突时为 `unknown` 并在 notes 逐字保留 |

D4 五条的建议映射：

- GG-01（博创→成都蓉博）：`guarantee_authorization`；额度 2 亿元、实际发生额 0、余额 0、`relationship_status=approved_not_drawn`。不能写成已发生担保敞口。
- GG-02（河南仕佳信息技术→仕佳光子）：按两档金额拆两行；银行借款档和回购义务档不得合并。
- GG-03（葛海泉→仕佳光子）：银行借款档与回购义务档拆行。
- GG-04（葛海泉、耿树霞→仕佳光子）：`guarantor_entity_ids` 保留两名共同担保人；以 2024 年报具名更完整版本为准，避免与 2023 行双计。

### 3.4 `legal_event`

| edge_subtype | 精确定义与禁止外推 |
|---|---|
| `historical_contract` | 裁判文书只证明特定历史期间存在合同/履行事实。必须给 `effective_from/effective_to` 或最窄可证期间；**不得外推为当前、主要或持续供货关系**，也不得进入供货集中度。 |
| `dispute_event` | 只证明诉讼/仲裁/争议发生。争议双方不自动构成供需双方；如需生成供货边，必须另有具名交易证据并单独建 `supply` 记录。 |

`historical_contract` 是确认审冻结条款中的机器值；不建议只用中文“历史合同”，否则无法与路线图契约逐字对接。当前 D1 校验器的中文枚举可作为显示标签，但存储值应统一为英文 canonical value。

### 3.5 `capacity_event`

唯一 subtype 为 `capacity_event`；`equipment_type` 与 `site` 是事件字段，不是公司间交易边：

- `equipment_type`：设备/工序类型；
- `site`：项目地点；
- `capacity_value/unit`：产能及单位；
- `project_status`：`planned/approved/under_construction/operating/unknown`。

只有原文同时具名供应商且交易语义明确，才另建 `supply/equipment_supply`，两条记录用 `derived_from_event_id` 关联。

### 3.6 `patent_event`

| edge_subtype | 精确定义与禁止外推 |
|---|---|
| `co_application` | 共同申请/共有权事件，只证明共同权利关系 |
| `assignment` | 专利申请权或专利权转让事件，方向为 `assignor → assignee` |

两者均不得转换为供货边，也不得承担单向技术流或商业合作结论。

## 4. 校验不变式

1. `edge_type/edge_subtype` 必须满足一对多白名单；跨类型 subtype 直接 FAIL。
2. `edge_type != supply` 时，`include_in_supply_concentration` 必须为 `false`。
3. `relationship_status=historical|terminated` 时，`effective_to` 不得为 `open`；确实无法取得时写 `unknown` 并记录检索轨迹。
4. `historical_contract` 的 `source_type` 必须为裁判文书类，且不得被当前供货查询默认返回。
5. `guarantee_authorization` 若 `actual_incurred_amount>0` 或 `ending_balance>0`，必须改为/另建 `guarantee_exposure`。
6. `percentage_operator!=eq` 时，前端和报告不得渲染成精确百分比。
7. 共同担保、合并 scope 和关联方集合必须引用 registry，不创建逗号拼接的伪主体。
8. 同一事实的后年重述用于更新期间/状态，不重复计边；需要保留多证据时采用 evidence 子表或 `same_fact_id`。

## 5. 与现行文件的最小兼容落地

终验若只做最小改动，可先：

1. 保留 `edge_type/edge_subtype/scope` 三个可选扩展列；
2. 将存储值改为本提案英文 canonical 枚举，中文仅作展示标签；
3. 为非供货 layer 增加 `effective_from/effective_to/relationship_status/include_in_supply_concentration`；
4. 股权与担保类型字段先存在独立扩展表，以 `edge_id` 1:1 连接；
5. 回收 D4 的 1 股权 + 4 担保证据时，只写候选层，终验裁决后再入正式独立层。

这一路径与 D1 的向后兼容原则相容，同时补上现行三个枚举列无法表达的阈值、期间、零发生额和历史语义。
