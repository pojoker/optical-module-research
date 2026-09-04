# Cursor 独立审计：数据契约、可复现性与消融影响

> 角色：数据契约 / 可复现性 / 消融依赖审计者（AUDIT-DQ-002）
> 审计时点：2026-09-04
> 基线：`HEAD=43d1d6cfa335e8693f33fa834a0d775ae2879195`（instruction commit）；canonical 快照祖先 `63d426b15b4c2e842ac9569f09febd6dd2d8ff5f`
> 性质：只读审计报告；**未修改**任何 canonical / 代码 / 测试 / 生成物
> 禁读确认：未读 `archive/**`、旧分支/worktree、代理轨迹、Kimi 报告

---

## 0. 启动指纹（复算前）

| 项 | 值 |
|---|---|
| branch | `main` |
| HEAD | `43d1d6cfa335e8693f33fa834a0d775ae2879195` |
| 工作树（本审前已有） | 仅 `M docs/control/ACTIVE_WORKPACK.yaml`（工作包授权路径） |
| `points.csv` sha256 | `a481a4527036c13dd87e2de8eae9d96f8089cedecd1a6455f480a4a9e3bdfde6` |
| `edges.csv` | `1e5c6739cd6ba1814da2a9186e131fa01e9502832aeec8230cd55dbef19fba1c` |
| `triage.csv` | `cc309eea2e99004465acc3f233e3b7948f67439a072f5a84c4e93ab3b8c8c111` |
| `shipments.csv` | `ab93cb1a98f49e50ffce2ea510ea227034cb6d3c87064aa18a8ebe2692d065cf` |
| `macro_evidence.csv` | `506411fad43e26e3f8a77b7568457d5fc8a328ecbb290da1b5ff4ea9b43238a4` |
| `calls/sources.csv` | `3268725d149270bde02b7fb465d2a1f857ab1ae0dfafdf22ed1ba1dfe32aee0f` |
| `calls/claims.csv` | `dfdaf14306e091ea7a6911d5bda4bacb3b7e7593d046edec87619e7e2214eab1` |
| `calls/events.csv` | `f77c87b6ff8d54c235d04eaa38de91a370e2e804ef8e4c671f91220b799a491f` |
| `calls/event_evidence.csv` | `8302b5b627c8b9dda4ace6428e9ad197cfe3da7281769f7eb9d7ef121e931df4` |

复算方式：只读 Python（`csv` + `utf-8-sig`），不写临时文件到仓库。

---

## 1. 独立结论摘要（≤10）

1. **B01–B12 与初步值一致**（B05 须用 `utf-8-sig` 读 `hit_id`，否则 BOM 会把重复组算成 0）。
2. **H1 confirmed / critical**：`判定等级` 不是稳定分类字段；200 个 distinct、195 行括号过程备注、零行以 A–D 开头；且被 `capability_details.csv` 直接抄成「证据等级」。
3. **H3 confirmed / high**：39 enabled × 166 sources 是 **slot/retrieved**；claims 仅 12 家 / 70 条，前 5 家 68.6%；27 家零 claim 中明确「审阅后无主张」标记极少。
4. **H9 confirmed / high**：`scan.py` 不校验 triage `hit_id` 唯一性、不强制 `会话日期`；2 组重复 + 19 条空日期已漏网。
5. **H10 partially_confirmed / medium**：空表与 frozen legacy 确属低价值；但 `universe/watch/candidates` 与 `sources/claims` vs `disclosures/events` **不是可立刻删除的重复**——有分层语义与真实多对多证据。
6. **H2 partially_confirmed**：C5 粗粒度 + `render.py` cell×points 能力群会把 MCU/泛 IC 与 DSP/TIA 并列；仅靠文案 disclaimer，无结构过滤。
7. **H4 confirmed**：34 event 中 31 仅单证；`corroborated` 仅 EV013/EV014；first_party 34/37。
8. **H5 confirmed**：单位/cell/粒度混表；100 条 B 级多为直接披露，偏离「推断层封顶 C」主叙事；校准列对 B 级几乎无用。
9. **消融可立刻做的只有死表/死代码清理**（`questions_manual` 空表保留门槛、`point_metrics` 空表）；其余须先改生成器或拆字段，否则会改 reader-visible 结论。
10. **当前数据不足以安全回答**「哪家具备什么可比较能力 / 处于什么可过滤阶段 / 与哪条路线有结构证据」——结构门可通过，语义 grain 与 enum 合同不足。

---

## 2. 基线复算表 B01–B12

| ID | 公式 / 过滤 | 分母 | 复算结果 | vs 初步值 | 差异原因 |
|---|---|---:|---|---|---|
| B01 | `len(points)` / `nunique(公司)` | — | **271 / 155** | 一致 | — |
| B02 | `nunique(判定等级)` 原文全串 | 271 | **200** | 一致 | — |
| B03 | `判定等级` 含 `(` 或 `（` | 271 | **195** | 一致 | — |
| B04 | `锚点URL.startswith('http')` | 271 | **193 / 271** | 一致 | 不含 Markdown/「有锚」等 |
| B05 | `Counter(hit_id)` 中 count>1 的组数；`会话日期` 空白 | 571 | **2 组 / 19 行** | 一致 | 须 `utf-8-sig`；否则 `\ufeffhit_id` 导致 groups=0 |
| B06 | rows / `nunique(公司)` / `证据等级=='B'` | — | **103 / 36 / 100** | 一致 | C=2, D=1 |
| B07 | `校准实际值` 非空 | 103 | **1 / 103** | 一致 | 仅 SE024 |
| B08 | `universe.enabled=='yes'`；enabled 中无任何 claim（经 `claims.source_id→sources.company_id`） | — | **39 / 27** | 一致 | 零 claim 名单见 §4 H3 |
| B09 | claims 按 company 计数 top5 之和 / `len(claims)` | 70 | **48 / 70 = 68.6%** | 一致 | LITE12+CIEN11+AAOI10+NOK10+CSCO5 |
| B10 | `events` 中恰好 1 条 `event_evidence` | 34 | **31 / 34** | 一致 | multi: EV013,014,027 |
| B11 | `independence_class=='first_party'` | 37 | **34 / 37** | 一致 | counterparty=2, same_origin=1 |
| B12 | `链接` 中 `http` 出现≥2；`证据等级` 以 C 开头 | 31 | **15 / 21** | 一致 | grade: A4 B5 C21 D1 |

### 附加机械检查（合同要求）

| 检查 | 结果 |
|---|---|
| 主键唯一 | points/edges/shipments/macro/route_bom/claims/sources/events/ee/ec/disclosures：**均唯一**；**triage.hit_id 不唯一**（2 组×2） |
| 空值率（关键） | triage.会话日期 19/571；shipments.校准实际值 102/103 空；constraint_requirements 数值三元组全空 |
| 枚举基数 | points.判定等级 200（失控）；points.状态 3；shipments.证据等级 3；events.event_status 2 |
| 时间范围 | triage 会话日期主要 2026-07-25..08-23；海外 sources/events 2026 披露为主 |
| 外键覆盖 | claims→sources 全覆盖；ee→events/event_claims 全覆盖；EV001 链完整 |
| 业务键近重复 | points 公司×cell 重复 4 组（含国民技术 C5×2、优迅 C5×2）；edges 同供需方重复 15 组 |
| 来源集中度 | claims 前 5 家 68.6%；events 主体也偏 AAOI/LITE/CIEN/CRDO/NOK |
| 证据独立 | event_evidence first_party 主导；macro 多 URL 同行 |
| 同表粒度 | shipments 单位 15 种 + 大量「聚合」cell；不一致 |

---

## 3. 假设裁决表 H1–H10

### H1 — `判定等级` 不是稳定分类字段

```yaml
hypothesis_id: H1
verdict: confirmed
severity: critical
confidence: high
evidence:
  - file: points.csv
    record_ids: [ALL]
    observation: "271行判定等级distinct=200；以A-D字母开头=0；括号过程说明=195；去括号后仅7类前缀（判定闸-生产中180/edge_backed42/node_wide_gate23/判定闸-在建19/判定闸-宇宙外观察4/cross_reference2/context_only1）"
  - file: points.csv
    record_ids: [P088, P137, P146, P164, P175, P225]
    observation: "全部为「判定闸-生产中(…过程/疑点/可降/锚待…)」；字段同时承载阶段、审阅者、取证过程、置信度建议"
  - file: build_detailed_capability_report.py
    record_ids: [EVIDENCE_RANK, L356]
    observation: "把判定等级当证据等级写入 capability_details.csv；且EVIDENCE_RANK只精确匹配无括号前缀，172条「判定闸-生产中(…)」全部miss→默认rank=1"
  - file: capability_details.csv
    record_ids: [中兴通讯-C5等]
    observation: "列名「证据等级」实际值为判定闸过程串，读者会被字段名误导"
  - file: scan.py
    record_ids: [§⑤]
    observation: "只校验状态/上市标签枚举，完全不校验判定等级词汇表"
counterexamples:
  - search: "至少三类必须保留在等级字段且不能移到review_note的信息"
    result: "未找到。阶段信息与状态列完全一致（mismatch=0），应留在状态；edge_backed/node_wide_gate等是准入路径枚举，应独立闭集字段；括号内过程/疑点/可降属于review_note或confidence，不应叫「等级」。"
reader_impact: "无法按证据强度过滤；「已入点」与「仍待复核/可降/锚待」同字段共存；能力明细PDF/HTML把过程备注标成证据等级；参与识别页按状态聚合尚可，但任何「按等级筛选」必错。"
recommended_action: remediate_only
```

**判定类型**：字段合同错误 + 展示误读风险（非单纯数据录入错误）。

---

### H2 — 粗粒度能力节点制造错误技术等价

```yaml
hypothesis_id: H2
verdict: partially_confirmed
severity: high
confidence: high
evidence:
  - file: tree.yaml
    record_ids: [C5]
    observation: "名称=电芯片(DSP/Driver/TIA/CDR/主控MCU)，单格并列异构能力"
  - file: route_bom.csv
    record_ids: [RB003, RB004, RB008, RB009, RB013, RB014]
    observation: "接收链映射TIA→C5；数字链映射DSP/Retimer→C5；相干DSP→C5；机器路径无子类型"
  - file: points.csv
    record_ids: [P089, P195, P225, P129, P161]
    observation: "国民技术MCU送样/导入、Coherent泛称ICs、贝岭存储器/SoC、思瑞浦控制芯片均在C5；不足以单独支撑RB003/RB004的TIA或DSP需求"
  - file: render.py
    record_ids: [L338-L378]
    observation: "路线能力群=cell_ids×points公司集合；disclaimer写明非供货，但无结构排除MCU/泛IC"
  - file: tree.yaml
    record_ids: [M1, MOD1]
    observation: "M1=InP/GaAs/SOI同类粗粒；MOD1=800G/1.6T速率粗粒——导航可接受，机器推导同风险"
counterexamples:
  - search: "机器或页面是否已结构阻止越级"
    result: "未阻止。仅render文案与out/研究问题树警告；solution_links.match_stage=node_overlap且evidence_status=insufficient是人工冻结，不是通用拦截器。"
reader_impact: "读者在全景/研究问题树看到国民技术等出现在800G/1.6T/400ZR候选能力群旁，易读成DSP/TIA能力。"
recommended_action: remediate_only
```

---

### H3 — 海外来源覆盖被误读成研究结论覆盖（主审）

```yaml
hypothesis_id: H3
verdict: confirmed
severity: high
confidence: high
evidence:
  - file: calls/universe.csv
    record_ids: [enabled=yes]
    observation: "39家全部enabled"
  - file: calls/sources.csv
    record_ids: [n=166]
    observation: "enabled公司slot覆盖39/39；availability=available的公司39/39；总sources=166（available160）"
  - file: calls/claims.csv
    record_ids: [n=70]
    observation: "仅12家有claim；reviewed=69/candidate=1；前5家48/70=68.6%"
  - file: calls/events.csv
    record_ids: [n=34]
    observation: "primary_subject在enabled内形成事件的公司15家（含WATCH_*路径外的主体）"
  - file: calls/README.md
    record_ids: [L87-L90]
    observation: "文档写「正式季度池39家」并定义no_relevant_claims；但README同时承认材料可用≠全文提取"
  - file: README.md
    record_ids: [L129]
    observation: "根README明确：海外日更端点只登记7个实体，「每日运行≠覆盖39家」——页面/报告若只报39/166会与此冲突"
counterexamples:
  - search: "零claim是否=审阅后无实质信息"
    result: |
      分别计数：
      (A) slot+retrieved但claims层无提取：27家（ADTN,AIXA,ASMPT,AXTI,CLS,FORM,FURUKAWA,GFS,GLW,JBL,LWLG,MRVL,MTSI,MXL,MYCRONIC,OXIG,POET,SANM,SIVERS,SMOP,SMTC,SOI,SUMITOMO,TSEM,VECO,VIAV,WIWYNN）；27/27的available sources均有accessed_date。
      (B) disclosures.processing_status=no_relevant_claims：8条，仅涉及MTSI(4)/MRVL(2)/CRDO(2)——这是「该披露件审阅无相关主张」，不是公司级「无研究价值」结论；且CRDO有claims，MRVL/MTSI仍有events路径材料。
      (C) 真正公司级「审阅后确认无相关claim」账本字段：claims层不存在；不能把(A)当成(B)。
reader_impact: "用「39家公司、166来源」概括研究会严重高估有效结论覆盖；真实claim研究集中在约12家。"
recommended_action: remediate_only
```

**五级覆盖率（enabled=39 为分母）**

| 级别 | 定义 | 公司数 | 率 |
|---|---|---:|---:|
| slot coverage | 有≥1 source 行 | 39 | 100% |
| source retrieved | 有≥1 available | 39 | 100% |
| claim extracted | 有≥1 claims 行 | 12 | 30.8% |
| claim reviewed | 有≥1 reviewed claim | 12 | 30.8% |
| event formed | events.primary_subject∈enabled | 15 | 38.5% |

**当前展示层级判断**：`calls/README` / SPEC 偏 **slot+池规模**；`calls/renderer`+event projection 偏 **disclosure/event 处理状态**；根 README 对日更有正确降级提示。九页光学模块站点（`site/optical-module`）**不直接**渲染 39/166，误读风险主要在 calls 报告与口头摘要。

---

### H4 — reviewed/asserted/corroborated 易混读

```yaml
hypothesis_id: H4
verdict: confirmed
severity: high
confidence: high
evidence:
  - file: calls/events.csv + event_evidence.csv
    record_ids: [EV001-EV034]
    observation: "asserted=32, corroborated=2；单证事件31/34；status与独立性一致：仅EV013/014为counterparty+first_party且corroborated；EV027双证但是first_party+same_origin仍为asserted"
  - file: calls/event_evidence.csv → event_claims → disclosures
    record_ids: [EV001, EE001, ECL001, D_AAOI_20260309_ORDER]
    observation: "链完整；ECL notes明示不等于客户确认或已发货；event_status=asserted"
counterexamples:
  - search: "≥3例多来源或对手方证据"
    result: "不足三例。仅EV013、EV014达到counterparty交叉；EV027为同origin双证，不算独立交叉。实际独立交叉=2。"
reader_impact: "「reviewed event」只能读作原文已核，不能读作独立证实。"
recommended_action: retain
```

---

### H5 — shipments 混合不可比较粒度

```yaml
hypothesis_id: H5
verdict: confirmed
severity: high
confidence: high
evidence:
  - file: shipments.csv
    record_ids: [ALL]
    observation: "单位15种（万只/万个/台/千克/万平方米/万美元/KK…）；cell含大量「×聚合」；证据等级B100/C2/D1；推导式103/103非空但多数B级实为年报产销表直接披露"
  - file: docs/adr/0001-shipment-inference-layer.md
    record_ids: [设计]
    observation: "设计=推断层封顶C+校准列防老化；例外允许量价齐露标B。生产表100/103为B，表名/ADR叙事仍强调推断——合同漂移"
  - file: shipments.csv
    record_ids: [SE024]
    observation: "唯一校准实际值是合同金额叙述，不是对出货量推断的回算；对B级直接披露行校准列无业务用途"
counterexamples:
  - search: "安全的跨公司比较组"
    result: |
      条件候选：同单位+非聚合cell+同期+B级 → 找到7组。
      相对最安全：EQ3×台×同年度（凯格精机/博众精工/新益昌，SE025/031/037等）——同为贴片/固晶设备出货台数口径较近。
      MOD1×万只×同年度（中际旭创 vs 新易盛）产品标签仍不同（「光通信收发模块」vs「光互联产品」），只能单行展示或附口径差，不宜无注释聚合。
      行业聚合/情景D行（SE006）禁止与公司行比较。
reader_impact: "任何sum/排名/份额计算无业务含义；前端若当「出货量排行」展示即过强结论。"
recommended_action: collapse
```

---

### H6 — 证据锚字段格式不统一

```yaml
hypothesis_id: H6
verdict: confirmed
severity: medium
confidence: high
evidence:
  - file: points.csv
    record_ids: [ALL]
    observation: "分类：direct_url193 / placeholder_youmao39 / other_non_url19 / markdown_url10 / local_reference8 / ledger_reuse2；字段名「锚点URL」与非URL内容合同不一致"
  - file: points.csv
    record_ids: [P001, P042, P009, P187]
    observation: "「有锚；…」/「同上」/本地扫描文件名/corpus qa.jsonl 均非直接URL；部分可经命中引语+检索日期弱定位，但机器不可统一解析"
counterexamples:
  - search: "本轮对20条URL做可达性与引语定位抽核"
    result: "insufficient_evidence（本审主责契约/依赖，未做外网抽核；不把「能打开」当引语支持）。机械分类已完成。"
reader_impact: "自动化溯源与批量复核失败率高；「有锚」占位会被当成已落链。"
recommended_action: remediate_only
```

---

### H7 — edges 同时承担关系与指标

```yaml
hypothesis_id: H7
verdict: partially_confirmed
severity: medium
confidence: medium
evidence:
  - file: edges.csv
    record_ids: [ALL]
    observation: "边等级：实边198/半边34/推断A2/推断B2；数值类型空171/占比45/金额20；无relation_type、无product_scope列"
  - file: edges.csv
    record_ids: [E036, E037, E038, E232]
    observation: "4条推断边均为解匿客户/代工槽位，备注含判例，不是模块供货证明"
  - file: edges.csv
    record_ids: [text scan]
    observation: "备注+原文含光模块/optics等关键词仅约3/236——产品范围多依赖外部上下文"
counterexamples:
  - search: "九页前端是否把edge直接写成光模块供应"
    result: "site/optical-module 公司页强调availability claim边界；render研究树写明供货只读edges。未发现九页把后台edge直接渲染为模块供货。风险主要在分析者直接聚合edges.csv。"
reader_impact: "表本身可被误读为模块供货网；当前主站有部分防护文案。"
recommended_action: remediate_only
```

---

### H8 — 宏观证据非原子来源记录

```yaml
hypothesis_id: H8
verdict: confirmed
severity: medium
confidence: high
evidence:
  - file: macro_evidence.csv
    record_ids: [ALL 31]
    observation: "单行多URL=15；C级=21；证据类型常为「机构报告/厂商规格」混合"
  - file: macro_evidence.csv
    record_ids: [MC001, MC002, MC003, MC004, MC011, MC012]
    observation: "MC001/002 B级但链接含二手转载；MC003/004 C级同花顺/雪球/头条互引；MC012含百度搜索页——独立性不可逐origin计算"
counterexamples:
  - search: "A/B是否均有一手同口径支持"
    result: "机械上A=4/B=5存在，但多URL与二手混链使「一手直接支持同一口径」无法在表内证明 → 对A/B语义保持怀疑，不在本审改等级。"
reader_impact: "首页宏观数字易成回声室。"
recommended_action: collapse
```

---

### H9 — 低成本基础完整性缺口（主审）

```yaml
hypothesis_id: H9
verdict: confirmed
severity: high
confidence: high
evidence:
  - file: triage.csv
    record_ids: ["仕佳光子+D8+2025年报", "仕佳光子+D9+2025年报"]
    observation: "各2行：同hit_id、同公司/cell/来源/日期；引语为同一年报相邻截断片段；处置同为驳回。属扫描窗口切片重复写入，不是合法多片段主键设计——主键本应唯一，片段应进子字段或新hit_id后缀"
  - file: triage.csv
    record_ids: [19 empty 会话日期]
    observation: "集中：三安光电10（hit_id前缀600703+*+sanan-inquiry-20260810.pdf）+其他7家；来源扫描12/人工7；理由中可正则找回日期仅5/19"
  - file: scan.py
    record_ids: [§⑤⑦, done=set(hit_id)]
    observation: "只查来源/处置枚举与「已入点→points公司」；hit_id用set去重净队列会吞掉重复但从不fail；会话日期无非空校验"
counterexamples:
  - search: "重复是否可能为故意多片段"
    result: "否。同一hit_id重复违反「hit_id=公司+cell+文件」合同；若需多片段应 hit_id#fragN 或独立行不同id。"
reader_impact: "去重账本不可信；缺日期批次无法按会话审计。"
recommended_action: remediate_only
```

**最小稳定测试（不实现，仅提案）**

1. `test_triage_hit_id_unique`：`len(rows)==len({hit_id})`
2. `test_triage_session_date_required`：每行 `会话日期` 匹配 `YYYY-MM-DD`
3. （可选）`test_triage_hit_id_charset`：禁止空 hit_id

---

### H10 — 未承载生产价值的结构（主审）

```yaml
hypothesis_id: H10
verdict: partially_confirmed
severity: medium
confidence: high
evidence:
  - file: questions_manual.csv
    record_ids: [0 rows]
    observation: "仅表头；scan.py⑬ / render.py 问题队列仍读取——空表充当白名单必备文件"
  - file: calls/point_metrics.csv
    record_ids: [0 rows]
    observation: "schema+validator+positioning+tests 全套；无生产数值"
  - file: calls/solution_links.csv
    record_ids: [SL001, SL002]
    observation: "2行全部evidence_status=insufficient；validator字节级冻结；renderer仍展示"
  - file: calls/constraint_requirements.csv
    record_ids: [CRQ001, CRQ002]
    observation: "2行；comparator/target_value/unit全空；仅有theme/cell与claim引用——定位层无真正可比较度量"
  - file: calls/technology_feedback.csv
    record_ids: [TF001-TF004]
    observation: "4行真实反馈状态；价值在，但可折叠进claim/review note"
  - file: calls/company_candidates.csv + watch_entities.csv + universe.csv
    record_ids: [64/47/39]
    observation: "名称重叠大（cand∩uni名25；cand∩watch名32；promoted仍留candidates57）——生命周期分层真实存在，但是维护成本高、易被读成三份公司名单"
  - file: calls/sources+claims vs disclosures+event_*
    record_ids: [schema]
    observation: "职责不重复：季度槽/电话会原子claim vs 公告事件多主张多证据；H4已证明多证据独立性字段只在事件链上发生"
counterexamples:
  - search: "每个建议保留表的不可替代读者结论"
    result: |
      retain universe：enabled季度池是日更与覆盖率分母，不可由candidates派生。
      retain watch_entities：IQE等对手方事件主体不进四季度义务（EV013/014依赖）。
      retain sources/claims：12家70条季度主张与事件链并行。
      retain disclosures/event_*：34事件+独立性类，无法从claims.csv确定性生成。
      retain technology_feedback（或collapse后仍保留语义）：TF001等区分技术演示与管理层前瞻。
      questions_manual / point_metrics：找不到当前读者可见结论 → 见消融矩阵。
reader_impact: "空表与frozen insufficient行制造「体系完整」幻觉；三套主体表增加错误join风险。"
recommended_action: collapse
```

---

## 4. 证据与反例（主审补强）

### 4.1 H1 必核六行（摘要）

| ID | 公司 | cell | 判定等级要点 | 不能推出 |
|---|---|---|---|---|
| P088 | 光迅科技 | C4 | 生产中 + kimi取证 + **锚待codex复核** | 证据已终审 |
| P137 | 中瓷电子 | B2 | 子代理起草 + 建议复核归格 | 已确认归格终态 |
| P146 | 光库科技 | D7 | **闸内可降档** | 与同批生产中点同权 |
| P164 | 明阳电路 | B1 | 比照先例计生产中；宁严可改在建 | 阶段无争议 |
| P175 | 联特科技 | MOD3 | **证据强度弱**于MOD1，可降待判 | 与MOD1同强度 |
| P225 | Coherent | C5 | IC类型未明示（**疑**Driver/TIA），自用为主 | 独立电芯片供货/DSP能力 |

### 4.2 H3 零 claim 公司完整名单（27）

`ADTN, AIXA, ASMPT, AXTI, CLS, FORM, FURUKAWA, GFS, GLW, JBL, LWLG, MRVL, MTSI, MXL, MYCRONIC, OXIG, POET, SANM, SIVERS, SMOP, SMTC, SOI, SUMITOMO, TSEM, VECO, VIAV, WIWYNN`

### 4.3 H9 重复行指纹

- `仕佳光子+D8+2025年报`：两段 PLC/AWG 定义句截断，同处置「驳回-非本格」
- `仕佳光子+D9+2025年报`：两段 FAU 定义句截断，同处置「驳回-证据不足」

---

## 5. 消融矩阵

| 候选 | 裁决 | 理由（一句话） | 影响类 |
|---|---|---|---|
| `questions_manual.csv` | **retain**（空壳门槛）或后续 `remove_now` | 0行但仍在 scan 白名单+⑬校验+render 合并；删表前须改生成器 | 须先改变生成器 |
| `calls/point_metrics.csv` | **remove_now** | 0行；无读者结论；仅 schema/validator/positioning/tests | 删除表即可（+清代码） |
| `calls/solution_links.csv` | **remove_now**（或冷冻到 docs） | 2行 insufficient 且字节冻结；无正向读者结论 | 须先改变生成器/validator |
| `calls/constraint_requirements.csv` | **collapse** → 并入 themes/claims 注记或等有数值再单表 | 无 comparator/value/unit；positioning 产出多为 gap 而非比较 | 会改变 reader-visible（定位页变空/改形） |
| `calls/technology_feedback.csv` | **collapse** | 4行有语义，可并入 claim pair / event notes | 须先改变生成器 |
| 三套海外主体表 | **retain** 分层，**collapse** 存储（视图化） | universe/watch/candidates 生命周期不同；但 promoted 残留造成名单膨胀 | 须先改变生成器/日更 |
| 两套来源/主张结构 | **retain** | 季度 claim 与事件多证据是真实多对多；H4 依赖 event_evidence | 删除会改变 reader-visible |
| `shipments.csv` 推断/校准结构 | **collapse** | B级直接披露与C/D推断/情景应分表或分视图；校准列对B无用 | 会改变 reader-visible |
| `capability_details.csv` | **derive_not_store** | 可由 points 确定性生成；且当前错误继承判定等级 | 须先改变生成器 |
| `archive/**` | **remove_now**（新生产克隆） | 运行时代码无业务依赖（仅 scan 白名单豁免与一处 package 校验提到路径） | 删除即可（本审未读 archive 内容） |
| 九页网页 | **retain** | 用户要求跟踪发布快照；非 canonical | — |

---

## 6. 依赖与迁移风险

### 6.1 逐项依赖清单

| 对象 | 读取者 | 写入者 | 测试 | 生成物 | 回滚点 |
|---|---|---|---|---|---|
| questions_manual.csv | `scan.py`⑬、`render.py` 问题队列 | 人工 | scan selftest 内嵌 | `out/问题队列.md` | 恢复空表头文件即可 |
| point_metrics.csv | `positioning.py`、`validator.py` | 无生产写入 | `calls/tests/test_positioning.py` | positioning 空 comparisons | 恢复空表+schema |
| solution_links.csv | `renderer.py`、`validator.py`（冻结） | 禁止改 | `test_positioning`/`test_calls` 冻结用例 | calls/out 链接节 | 恢复 SL001/002 字节 |
| constraint_requirements.csv | `positioning.py`、`validator.py` | 人工 | test_positioning | requirement_matches / gaps | 恢复2行 |
| technology_feedback.csv | `renderer.py`、`validator.py` | 人工 | test_calls | feedback 节 | 恢复4行 |
| universe/watch/candidates | `daily_discovery.py`、`event_intelligence.py`、`renderer.py` | 日更+人工晋级 | test_daily_discovery、test_event_intelligence | 覆盖率/雷达/公司页 | 分层状态机回滚 |
| sources/claims | validator、renderer、positioning | 人工提取 | test_calls | 公司时间线 | 按 source_id 回滚 |
| disclosures/event_* | event_intelligence、workbuddy、validator | 日更候选+人工 | test_event_intelligence | 事件雷达 | 按 event_id 回滚 |
| shipments 校准列 | `render.py` QC 销号逻辑 | 人工 | （弱） | 问题队列 QC | 忽略校准列即可 |
| capability_details.csv | PDF/HTML 构建 | `build_detailed_capability_report.py` | 无强契约测 | PDF/HTML | 从 points 重生成 |
| archive/** | 无运行时业务读 | — | package 校验提及 | — | 不删主仓则零风险 |

### 6.2 迁移顺序（若用户日后授权）

1. **只加测试不改数据**：triage hit_id 唯一 + 会话日期非空（H9）
2. **字段拆分不删行**：points 判定等级 → `admission_path` + `review_note`；capability_details 重生成（H1）
3. **删除空生产表**：point_metrics + 清理 positioning 分支（H10）
4. **冷冻/移除 solution_links** 并改 renderer（H10）
5. **shipments 分视图**：direct_disclosure / inference / scenario（H5）
6. **主体表视图化**：candidates 归档 promoted（H10）
7. **最后才动** event/claims 双链与九页

回滚策略：每步单独 commit；canonical 指纹对比；机器门 `scan.py --check` + `python -m calls check` 只证明结构未毁，不证明语义修复。

---

## 7. 最小修复顺序（每步一语义问题；本轮不实施）

1. **H9**：triage 主键唯一 + 会话日期必填（机器门补测）
2. **H1**：拆 `判定等级`；禁止写入「证据等级」别名；修 `EVIDENCE_RANK`
3. **H3**：覆盖率 API/报告强制五级分列；禁止单独输出「39/166」
4. **H4**：读者文案固定 asserted≠corroborated；UI 显示 evidence independence
5. **H5**：B级披露与推断分视图；禁用跨单位聚合
6. **H2**：路线能力群按 route_item 所需子功能过滤，或降级为人工清单
7. **H10**：删 point_metrics；冻/撤 solution_links；questions_manual 决定留白名单或改 scan
8. **H6/H8**：锚类型枚举化；macro 一行一 origin

禁止在同一步扩 schema 开新关系类型。

---

## 8. 未解决问题 / insufficient_evidence

| 项 | 状态 | 缺什么 |
|---|---|---|
| H6 外网可达性与引语定位抽核（10+10） | `insufficient_evidence` | 本审未做联网原文核（交语义审/后续） |
| H7 全部实边产品范围人工标注 | `insufficient_evidence` | 需逐条年报产品段，超出契约主审 |
| 零 claim 公司是否「已全文精读无信息」 | 部分可知 | 缺公司级 `review_status=no_relevant_claims` 字段；现有只有披露件级 |
| archive 内部是否被证据锚引用 | 未深读（禁读） | 仅证明运行时 py 无业务依赖；删前需用户授权扫锚 |
| Kimi 语义裁决分歧 | 不适用 | 本审完成前未读对方报告 |

---

## 9. stop_and_escalate 观察（不修复）

- **H1→capability_details「证据等级」列**：读者产品已输出过强/错误字段语义 → 标记升级，但不在本轮改文件。
- **H3**：若任何对外材料单独使用「39家/166来源」作为研究完成度 → 升级。
- 本轮**未**发现必须改工作包范围才能继续审计的事项。

---

## 10. 收尾声明

- **只写入本文件**；未修改 canonical、代码、测试、网页、日更状态。
- **未读取** Kimi 报告、`archive/**`、旧分支/worktree、代理轨迹。
- canonical 指纹与启动时一致（本审无写）。
- 机器门未替代本审计；B/H 裁决仅供用户交叉比较后授权。

**对审计目标四问的契约层回答**

1. **是否足以安全回答公司能力/阶段/路线？** 否——过滤键污染（H1）、节点过粗（H2）、海外覆盖层级混淆（H3）。
2. **哪些字段诱导过强结论？** `判定等级`、`capability_details.证据等级`、`sources` 池规模、`event_status` 字面、`shipments` 表名与混单位。
3. **哪些结构无生产数据或可派生？** `point_metrics`（空）、`questions_manual`（空门槛）、`capability_details`（可派生）、`solution_links`（frozen insufficient）。
4. **消融影响？** 见 §5–§6；可立刻删的只有空指标表类；其余须先改生成器或会改读者结论。
