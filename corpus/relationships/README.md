# 供应链关系时间线与边级治理台账 (`corpus/relationships/`)

本目录承载光模块知识库 **关系层（Supply-Chain & Counterparty Layer）** 的四张核心结构化台账，连接根级静态快照 [`edges.csv`](../../edges.csv)（236 条边 `E001–E236`）与 Step 3 日更情报流（`domestic_daily` / `daily_intelligence` / `calls`）。

---

## 一、目录文件清单与统计快照

| 文件名 | 记录数 | 定位与核心作用 |
|---|---:|---|
| `relationship_timeline.csv` | **446 行**（覆盖 **204 对**关系） | 统一关系时间线主表：完整整合 `E001–E099` 基线、无损拆解 `E100–E236` 多期打包行（拆出 **290 条**分期行），并入设备观察池补充行（**11 条**）且预留 Step 3 Daily 挂接列 |
| `edge_negative_cuts.csv` | **74 行** | 边级负向剔除记忆表：收录长飞系个体合并承载（25 条）、华工非光链/坏账（40 条）、非供货方向（6 条）、非光链主体（3 条），经程序化核验在当前 `edges.csv` 中 **`0` 泄漏** |
| `counterparty_audit.csv` | **15 行**（`P01–P15`） | 跨主体双侧对账台账：含会计科目错位预判（原材料 vs 固定资产/在建工程）及已完结的 `P01`（天孚→Fabrinet 弱一致）、`P02`（Fabrinet↔Lumentum B级终态）、`P03`（光迅↔烽火服务费逐位确认、商品含税+并表还原后差 `~4.9%`） |
| `sellside_watch_alarms.csv` | **7 行**（`W01–W07`） | 卖方预测与缺席验真闹钟：`W03`（联讯仪器 `688808` 已于 `2026-04-24` 科创板上市）与 `W06`（Yole CPO `54亿/121%` Scale-Up 口径已结案并归入 `macro_evidence.csv#MC035`）已核实更新；`W01/W02/W04/W05/W07` 作为 2026–2027 到期验真闹钟持续生效 |

---

## 二、`relationship_timeline.csv` 统一 Schema（21 列）与生命周期红线

### 2.1 字段定义

| 列名 | 必填 | 受控枚举 / 格式 | 规则说明 |
|---|---|---|---|
| `timeline_id` | 是 | `TL0001`..`TL9999` | 时间线原子观测全局唯一主键 |
| `relation_id` | 是 | `R001`..`R999` | 归一化有向关系键（`R001–R070` 与历史基线严格兼容；默认匿名槽位按边独立不跨年串接，唯一同文件恒定代号例外为 `联讯仪器 -> 集团一(匿名)`） |
| `supplier` | 是 | 规范化供方名 | 经别名表归一化，严格遵守 `refs/entity-registry.yaml`（合并口径与法人单体分列，不硬并） |
| `customer` | 是 | 规范化需方名 | 同上，方向敏感（`A→B` 与 `B→A` 为不同 `relation_id`） |
| `supplier_point_id` | 否 | `P###` / `EXT` / `ANON` / 空 | 对齐 `points.csv` 能力点或边界外/匿名标识 |
| `customer_point_id` | 否 | `P###` / `EXT` / `ANON` / 空 | 同上 |
| `period` | 是 | `2025` / `2022H1` / `2025Q1` / `FY2025` / `2024-12-13` | 会计期间或时点日期，自然年与 `FY` 财年严禁混同 |
| `period_type` | 是 | `year \| half_year \| quarter \| month \| snapshot \| fiscal \| year_range \| event` | 历史财报用前七类；Step 3 高频日更事件统一填 `event`（或明确季度 `quarter`） |
| `event_date` | 否 | `YYYY-MM-DD` 或空 | 时点快照（如在手订单截止日）与 Step 3 日更事件必填精确发生/答复日；年度/半年度区间留空，严禁拿年报披露日冒充业务发生日 |
| `source_channel` | 是 | 历史：`annual_report \| prospectus \| sec_10k`<br>日更：`daily_ir \| daily_qa \| daily_announcement` | 区分定期财报/招股书静态基线与 Step 3 高频脉冲信源 |
| `metric_kind` | 是 | 历史：`sales_share \| purchase_share \| amount_rmb \| amount_usd \| order_backlog \| intermediary_disclosure \| bad_debt_writeoff`<br>日更扩展：`order_progress \| partnership_milestone \| qualification_status \| capacity_co_investment` | 明确区分**供方披露占营收比（`sales_share`）**与**需方披露占采购/成本比（`purchase_share`）**，防止分母倒置 |
| `value_raw` | 是 | 原文数值或事件摘要 | 完整保留原始披露字面串（如 `53.42%(37277.97万元)`），不丢单位、不丢口径括注 |
| `numeric_value` | 否 | 纯十进制数字或空 | 去千分位后的主数值；不等式（如 `<10%`）、跌出前五或定性事件留空，严禁把 `<10%` 写成 `10` |
| `unit` | 否 | `% \| 元 \| 万元 \| 万美元 \| 万欧元 \| 台` 或空 | 与 `numeric_value` 严格配对 |
| `observe_type` | 是 | 常规：`first_observed \| observed \| last_observed \| censored`<br>特殊：`confirmed_ended \| procedural_intermediary \| bad_debt_frozen`<br>日更：`event_disclosed` | **核心防误判闸门**（见 §2.2） |
| `edge_grade` | 是 | `实边 \| 推断A \| 推断B \| 半边` | 继承或按信源证据强度赋级 |
| `source_edge_ids` | 否 | `E###`（多边以 `;` 分隔） | 关联 `edges.csv` 边号；观察池未入前五补充行或纯日更事件可留空 |
| `daily_ref_id` | 否 | 上游事件唯一键或空 | 历史财报行固定为空 `""`；Step 3 日更事件必填（见 §3） |
| `anchor_url` | 是 | URL 或仓内规范锚点 | 统一指向一手 URL、`edges.csv#E###` 或 `corpus/...`，零归档悬空路径 |
| `conflict` | 是 | `true \| false` | 同关系同期间出现跨表/双侧口径冲突（如 `R012` `E038` vs `E068`、`E154` 前五大合并 vs 关联交易表）标 `true`；同源占比+补充金额或商品+劳务并行分项标 `false` |
| `notes` | 否 | 自由文本（分号分隔） | 记录同源配对金额、夹层警示（`intermediary_layer`）、观察池 `eq_watch_series_id` 及口径约束 |

### 2.2 三类特殊关系生命周期/性质标签（下游前端硬过滤红线）

任何下游图谱渲染、集中度统计或“当前活跃供应商”查询，**必须过滤以下三类特殊 `observe_type`**，严禁将其与常规活跃边混算：

1. **`confirmed_ended`（确认终结边）**：有明确监管断供或官方终止披露（如 `E008` `NeoPhotonics -> 华为(含海思)` 2019-05 BIS 实体清单管制后于 `2021` 归零）。注意：单纯“跌出前五 / `<10%` 退出披露表”只标 **`censored`（右截尾不可见）**，严禁误判为关系死亡！
2. **`procedural_intermediary`（程序性代理夹层）**：仅在收入确认政策等程序段落点名的出口代理/通关通道（如 `E016` `新易盛 -> 浙江粮油`），并非真实终端买家。对于有明确金额的结算平台/分销商（如 `PINEWAVE`、`Digicomm`、`讯速信远`、`南央国际`、`津微光电`、`陕西电子信息国际商务有限公司`），保留其时序 `observe_type` 并在 `notes` 强制打标 `intermediary_layer:...`。
3. **`bad_debt_frozen`（坏账核销/冻结遗留项）**：来自资产负债表应收账款单项计提坏账准备附注（如 `E146` `Kaiam Corporation -> 博创科技` 2023–2025 连续三年 `100.00%` 单项计提坏账约 `1,059–1,093 万元`），代表历史破产冻结余额而非当期供货交易。

---

## 三、Step 3 Daily 高频事件挂接契约（Insertion Contract）

Step 3 日更管线（境内互动易 `corpus/qa/`、投资者关系活动记录表 `corpus/ir/`、巨潮公告及海外新闻稿/季报电话会 `calls/` / `workflow-rehearsal-daily-state/`）在捕获到具名供应链合作、订单进展、客户验证或联合扩产事件时，**无需另建孤立事件表，直接按以下契约追加至 `relationship_timeline.csv` 同一根时间线上**：

### 3.1 写入与幂等挂接规则

1. **关系键复用与新开（`relation_id`）**：
   - 先将事件供需双方按 `ALIAS_MAP` 与 `refs/entity-registry.yaml` 归一化：
     - 若归一化 `(supplier, customer)` 已存在于非匿名 `relation_id` 中（例如 `罗博特科/ficonTEC -> NVIDIA` 已存在 **`R057`**），**必须直接复用该 `relation_id`**，使高频事件自然接续在历史年报/招股书/在手订单序列之后！
     - 若为历史财报尚未覆盖的新具名组合（例如晶圆代工厂 `Tower Semiconductor -> 中际旭创`），按序分配新 `R###`（建议日更分配区间或顺延最大 `R###`）。
2. **必填高频溯源四件套**：
   - `source_channel`：严格取值 `daily_qa`（深交所互动易/上证e互动）、`daily_ir`（投资者关系活动记录表/路演纪要）、`daily_announcement`（上市公司正式公告、海外发行人官网 Press Release / SEC 8-K）。二手媒体传闻未获一手段落印证前**严禁入表**。
   - `daily_ref_id`：**非空唯一上游事件幂等键**（如互动易 `qa:<stock_code>:<index_id>`、海外披露候选 `DC_<hash>` 或正式事件 `EV###`）。重跑日更同步脚本时以 `(source_channel, daily_ref_id)` 唯一键幂等更新（Upsert），防止重复追加。
   - `period` / `period_type` / `event_date`：日更点事件统一填 `period = YYYY-MM-DD`、`period_type = event`、`event_date = YYYY-MM-DD`（**必须填官方答复日 `answer_date` 或新闻稿发布日 `published_date`**，严禁填爬虫抓取日 `fetch_date` 或提问日 `ask_date`）。
   - `observe_type`：日更定性/脉冲事件统一填 **`event_disclosed`**（除非公告明确宣布合作终止填 `confirmed_ended`），**不篡改**同关系下历史财报序列原有的 `first_observed` / `last_observed` 边界，确保财报定量序列与高频事件脉冲同轴展示、互不污染。
3. **数值克制纪律**：
   - 若互动易/新闻稿仅确认合作或量产交付状态而未披露具体金额/台数，`metric_kind` 填 `order_progress` / `partnership_milestone` / `qualification_status`，`numeric_value` 与 `unit` **必须留空 `""`**，摘要原话写入 `value_raw`；若正式公告披露精确合同金额，则填 `amount_rmb` / `amount_usd` / `order_backlog` 并提取精确数值与单位。

### 3.2 标准挂接实例（可直接作为 Step 3 测试样例）

#### 实例 A：罗博特科 × 英伟达 `2026-11-16` 深交所互动易确认量产订单交付与收入确认（接续既有 `R057`）
- **上游原件**：`domestic/qa/300757/qa.jsonl`（`index_id = 2402040011815366656`, `answer_date = 2026-11-16`）
- **与历史序列同轴效果**：直接挂入 **`R057`（`罗博特科/ficonTEC -> NVIDIA`）**，排在 `2024-07-31`（在手订单 `2433.83万欧元`）与 `2024-12-13`（在手订单 `4800万欧元`）之后，形成“2024 在手订单快照 → 2026-11 晶圆/晶粒测试设备多笔量产订单陆续交付确收”的完整证据链：

```csv
timeline_id,relation_id,supplier,customer,supplier_point_id,customer_point_id,period,period_type,event_date,source_channel,metric_kind,value_raw,numeric_value,unit,observe_type,edge_grade,source_edge_ids,daily_ref_id,anchor_url,conflict,notes
TL9001,R057,罗博特科/ficonTEC,NVIDIA,P059,EXT,2026-11-16,event,2026-11-16,daily_qa,order_progress,"英伟达系ficonTEC客户之一；2025年配合完成双面晶圆及晶粒测试设备开发验证后相继取得多笔量产化订单，部分已完成交付及收入确认",,,event_disclosed,实边,E012,qa:300757:2402040011815366656,corpus/qa/300757/qa.jsonl#indexId=2402040011815366656,false,"深交所互动易官方回复(ask_date=2026-11-11,answer_date=2026-11-16)；定性确认量产订单交付确收，具体金额涉密未披露"
```

#### 实例 B：Tower Semiconductor × 中际旭创(Innolight) `2026-11-03` 联合新闻稿推进 AI 近封装光学（NPO）合作（新开关系号）
- **上游原件**：`overseas/staging/2026-11-10/disclosure_candidates.csv`（`DC_430D7977BA22`, `published = 2026-11-03`）
- **挂接写法**：供方为硅光代工厂 `Tower Semiconductor`，需方归一化为 `中际旭创`，`source_channel = daily_announcement`，`daily_ref_id = DC_430D7977BA22`：

```csv
timeline_id,relation_id,supplier,customer,supplier_point_id,customer_point_id,period,period_type,event_date,source_channel,metric_kind,value_raw,numeric_value,unit,observe_type,edge_grade,source_edge_ids,daily_ref_id,anchor_url,conflict,notes
TL9002,R205,Tower Semiconductor,中际旭创,EXT,,2026-11-03,event,2026-11-03,daily_announcement,partnership_milestone,"Tower Semiconductor与中际旭创(Innolight)宣布联合推进面向AI基础设施的高性能近封装光学(NPO)产品合作",,,event_disclosed,实边,,DC_430D7977BA22,https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/,false,"Tower官网一手新闻稿(2026-11-03)；技术与商业生态合作里程碑，不含定量采购额"
```
