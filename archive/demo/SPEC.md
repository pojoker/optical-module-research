# demo/SPEC.md — 光模块图谱管线 Demo 规格 v1

**目标**：把 SOP.md v1.0 的 S2（A股披露侧）流程做成可运行管线的最小演示：
研报域公司名单 → 年报下载 → 表格抽取 → 边生成 → 图可视化。

**范围**：只做 A股侧（S2）。美股侧（S1）、解匿（S3）不在本 demo；
下载环节直接用 `assets/download_annual_reports.py`（用户提供，禁止重复开发）。

## 管线

```
名单(companies.csv) ─→ [Stage1 下载] assets/download_annual_reports.py
                         └→ demo/data/<code>/<年报>.pdf + annual_reports.csv
                    ─→ [Stage2 抽取] src/extract_tables.py  (开发: cursor grok)
                         └→ demo/out/extracted.json
                    ─→ [Stage3 边生成] src/build_edges.py    (开发: codex)
                         └→ demo/out/edges.csv + nodes.csv
                    ─→ [Stage4 可视化] src/make_graph.py     (开发: claude sonnet)
                         └→ demo/out/graph.html
             编排: src/run_pipeline.py (开发: codex)  终验: Claude(本会话)
```

## 公司名单（来自光模块收割库覆盖名单）

| 代码 | 名称 | 角色 |
|---|---|---|
| 300308 | 中际旭创 | 真值集公司 |
| 300502 | 新易盛 | 真值集公司 |
| 300394 | 天孚通信 | 真值集公司 |
| 002281 | 光迅科技 | **泛化测试公司**（彩排未抽取过，无真值先验） |

财年范围：2023-2025（以披露日最新为准）。

## Stage2 抽取器契约（extract_tables.py）

输入：`--data-dir demo/data --out demo/out/extracted.json`
对每份 PDF（pdftotext 转文本后）抽取：
1. **前五大客户表**：每行 {rank, name_raw, is_anonymous, amount_yuan, pct}
   + 合计 {total_amount, total_pct} + **关联方销售占比 related_party_pct**
2. **前五大供应商表**：同构
3. **程序段落**：
   - 收入确认政策中的实名主体（正则：与"××公司/××股份有限公司"的销售…确认收入）
   - 重大关联交易表中的 {关联方名, 金额, 币种}
输出 JSON schema：
```json
{"reports":[{"stock_code":"300308","company":"中际旭创","fiscal_year":2025,
  "source_pdf":"...","customers":{"rows":[...],"total_pct":..,"related_party_pct":..},
  "suppliers":{...},"procedural":{"revenue_recognition_names":[...],
  "related_party_sales":[...]},"warnings":[...]}]}
```
硬要求：金额逐位保留（字符串或 Decimal，禁止浮点丢精度）；抽取失败的字段置
null 并写 warnings，不许静默丢弃；pdftotext 的表格列错位是已知陷阱（彩排 T5）。

## Stage3 边生成器契约（build_edges.py）

输入 extracted.json，输出彩排 schema 的 edges.csv（10列：edge_id,供方,需方,
占比或金额,财年,边等级,证据文件,锚点,验证状态,备注）与 nodes.csv（6列）。
规则（SOP S2.2/S2.3）：
- 客户实名 → 实边（供方=公司，需方=客户名）；供应商实名 → 实边（方向反转）
- 匿名 → 半边槽位（需方="客户第N名(匿名)"）
- **关联方检查**：|related_party_pct - 某客户pct| < 0.005 → 该行备注"关联方
  锁定候选"，若程序段落有关联交易实名且金额指纹在汇率带内（6.5-7.5 折算差
  <3%）→ 备注升级"解匿线索:<名>"（不改边等级——判定留给人）
- 锚点=下载元数据里的 pdf_url；验证状态="demo管线自动生成-未人工复核"

## Stage4 可视化契约（make_graph.py）

输入 edges.csv/nodes.csv → 自包含 graph.html（零外链，内联 JS/CSS）：
供应链分层布局（设备/器件/模块/代工/终端），实边实线、槽位虚线灰、解匿线索
高亮；hover 显示四件套。

## 终验标准（Claude 执行，过线才算 demo 完成）

1. `run_pipeline.py` 从空 out/ 一键跑通全链。
2. **真值比对（彩排手工核对值，逐位）**：
   - 旭创2025客户：24.06/18.26/14.22/11.34/8.10%；客户A金额 9,201,495,755.91；
     客户E金额 3,096,780,769.22；related_party_pct=8.10；供应商A 35.76%
   - 新易盛2025客户：22.97/16.64/15.63/10.96/6.15；2024：31.74/12.39/12.15/9.14/5.68；
     2023第一名 36.79%（1,139,711,326.47）；供1 23.87%
   - 天孚2025：客户1 实名"Fabrinet" 63.31%（3,268,843,594.94）；客户2 11.66% 匿名
   - 新易盛收入确认实名含"浙江省粮油食品进出口股份有限公司"（2023/2024/2025 三份）
   - 旭创关联交易含 PINEWAVE（43,378万美元）且客户E行出现"解匿线索"备注
3. 泛化：002281 三份年报抽取无 crash，客户/供应商表结构完整或字段级 warnings。
4. edges.csv 四件套完备性脚本检查零缺失。

## 开发纪律

- 各开发代理只写自己负责的文件，不改他人产出与本 SPEC。
- Python 3.11+ 标准库 + requests；不新增第三方依赖（pdftotext 走 subprocess）。
- 所有开发/修复轮次记录 demo/DEMO-LOG.md。

## 增补 v1.1（正式版扩量，2026-07-23）

**公司名单扩至 10 家**：新增 300757罗博特科/688516奥特维/301338凯格精机/688097博众精工/603203快克智能/688337普源精电。

**Stage2 增补——上交所模板（688xxx/603xxx 实测）**：
- 叙述句：`前五名客户销售额X万元，占年度销售总额Y%；其中前五名客户销售额中关联方销售额Z万元，占年度销售总额W%` → total_amount=X万元换算元、total_pct=Y、related_party_pct=W
- 表格：`单位：万元`（金额×10000 换算为元，Decimal 字符串）；pdftotext 列打散为"序号组+客户名称组+销售额组+占比与关联关系交错组"，占比列与"是/否"（是否与上市公司存在关联关系）交错
- schema 增字段：row 级可选 `related_flag`("是"/"否"/null，来自上交所行级关联列)；report 级 `template`("szse"/"sse")
- 深交所分支零回归：旧 12 份输出不得变化（真值 16/16 保持）

**Stage3 增补**：
- 公司映射扩 6 家：罗博特科=耦合封装设备商/奥特维=组件封装设备商/凯格精机=组装设备商/博众精工=自动化设备商/快克智能=焊接设备商/普源精电=测试测量仪器，国别中国
- row.related_flag=="是" → 备注加"年报关联关系列=是"
