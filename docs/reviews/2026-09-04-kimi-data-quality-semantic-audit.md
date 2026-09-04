# Kimi 独立审计报告：光模块数据质量——领域语义与证据审计

> 审计者：Kimi（领域语义与证据审计角色）
> 日期：2026-09-04
> 固定基线：`pojoker/optical-module-research@43d1d6cfa335e8693f33fa834a0d775ae2879195`（instruction commit，已核对 HEAD 一致）
> canonical 快照承诺：`63d426b15b4c2e842ac9569f09febd6dd2d8ff5f`
> 审计委托书：`docs/reviews/2026-09-04-data-quality-ablation-independent-review-brief.md`
>
> **独立性声明**：本报告完成前未读取 Cursor 审计报告（截至写入时该文件不存在/未打开）；未读取 `archive/**`、旧分支、旧 worktree、完整代理轨迹。联网核验仅使用公司 IR/SEC/巨潮/标准组织等一手来源。
>
> **写入边界**：本文件是唯一写入产出。未修改任何 canonical、代码、测试、网页、工作包。canonical 指纹（SHA-256，9 个根级账本 + calls CSV 目录清单）在审计前后各记录一次，结果一致（见文末核验记录）。

---

## 1. 独立结论摘要（10 条）

1. **B01–B12 全部复算命中**，12/12 与委托书初步值完全一致；唯一需要说明的分母细节是 B03 的"括号型"正则口径与 B09 的公司归属映射方式（见 §2）。
2. **H2（C5 粗粒度等价）confirmed，high**。`tree.yaml:65` 把 DSP/Driver/TIA/CDR/主控MCU 五种设计难度与路线相关性完全不同的芯片装入一格；`route_bom.csv` RB003/004/008/009/013/014 的 mapping_note 直接写着"TIA→C5""DSP/Retimer/线性驱动均属C5电芯片"；P089 的判定备注自承"C5格定义同步放宽含主控MCU"。国民技术（MCU，在建）与 Marvell（DSP 全覆盖，生产中）在同一格内结构上等价，只有备注文本阻止越级，结构上没有任何阻止。
3. **H4（reviewed≠corroborated）confirmed，high**。34 个 event 中 31 个仅一条 evidence，37 条 evidence 中 34 条 first_party；达到 counterparty 交叉证实的只有 EV013、EV014 两例（不足委托书要求的三例反例，按实际数报告）。EV001 全链核验到 AAOI 官网新闻稿原文，属实但确为单方公告，且订单交付"预计 2026Q3 开始"——属前瞻口径。
4. **H5（出货量表混合不可比较粒度）confirmed，high**。103 行出现 15 种单位（万只/万件/万个/台/台套/千克/万平方米/KK/万美元…），cell_id 含"行业聚合""D系聚合"等跨层聚合；100/103 为 B 级年报直接披露，与 ADR-0001 设计的"C 级封顶推断层"定位整体偏离，校准列 1/103 填写且唯一填写行（SE024）内容不是校准值而是合同公告。
5. **H6（锚点字段合同不一致）confirmed，medium-high**。`锚点URL` 字段 271 行中仅 193 行为直接 URL；39 行是占位文字"有锚"、20 行描述性引用、9 行 Markdown 链接、8 行本地语料引用、2 行"同上"（非 direct 合计 78 行 = 28.8%）。抽核的 direct URL 可访问性 10/10 通过，但原文逐字核验（引语定位）只完成 3/10，其余 7 条仅核可访问性；非 direct 类多数可经 corpus 唯一复原（逐条记录 4 条），但 10 条均未完成引语定位——委托书要求的"可访问性+引语定位"双重抽核未完整完成，缺口按 insufficient_evidence 处理（详见 §3 H6 与 §8）。此外"同上"依赖行序、`全景.md` 把"有锚"占位渲染成了假超链接。
6. **H7（edges 缺 relation_type/product_scope）confirmed，medium-high**。表头确无关系类型与产品范围列；236 条边混合实名关系、34 条匿名半边、45 条公司级客户集中度占比、4 条解匿推断边、15 组跨年重复观测。E026 Lumentum→Apple 实为 3D 传感/消费端（仅备注注明），整体客户关系存在被投射为光模块供货的结构性风险。
7. **H8（宏观证据非原子来源）confirmed，high**。31 条中 21 条 C 级；15 条链接字段含多 URL；MC012/MC027 的"链接"是百度搜索页；多条来源为"ssgsmarketing@xueqiu.com"伪 URL 的雪球帖；MC004/MC013/MC014 口径备注自承回声室互引；MC024 主张"4周以内"与原文"12周压到8周"存在口径跳跃；MC009/MC010 标 A 级但"来源"是内部账本自引用，不符合 A 级语义。
8. **H3（海外覆盖误读）partially_confirmed，medium**。"27/39 公司无 claim"对 `claims.csv` 成立，但其中 9 家（MRVL/MTSI/POET/GLW 等）在 `event_claims.csv` 有主张，真正零主张为 18 家；渲染层（`calls/out/companies/`）只生成 14 张公司卡，已按内容存在性门控，未把 39 家槽位直接展示为研究覆盖。两套主张结构并存本身就是 H10 的病灶。
9. **H1/H9/H10 confirmed 或 partially_confirmed**（详见 §3）：H1 判定等级字段 200 个 distinct 值/271 行，确为过程备注污染；H9 两组重复 hit_id 是同一命中的截断片段双录，19 条缺日期中 10 条集中于三安光电问询函批次且可从 hit_id 文件名恢复；H10 中空表与 legacy 表属实，但三套海外主体表的生命周期语义差异部分真实，宜 collapse 而非全删。
10. **未发现需要 stop_and_escalate 的"读者可见错误结论正在输出"情形**：out/ 下页面未展示 MC024 的 4 周口径、未把 166 来源槽位写成研究覆盖、C5 各公司卡均附带原文引语可人工纠偏。风险均为"结构不阻止、靠备注兜底"的潜在误读，非既成错误输出。

---

## 2. 基线复算表（B01–B12）

复算方法：Python3 + csv 模块（utf-8-sig 去 BOM），只读脚本，未写临时文件入仓库。

| ID | 公式 / 过滤条件 | 初步值 | 复算值 | 差异说明 |
|---|---|---|---|---|
| B01 | `len(points.csv 数据行)` / `len(set(公司))` | 271 / 155 | **271 / 155** | 无差异 |
| B02 | `len(set(判定等级))` | 200 | **200** | 无差异。前缀归并后实际语义类仅 7 个：判定闸-生产中180、edge_backed 42、node_wide_gate 23、判定闸-在建19、宇宙外观察4、cross_reference 2、context_only 1 |
| B03 | 判定等级匹配 `[（(].+[)）]` 的行数 | 195 | **195** | 无差异（含半角/全角括号） |
| B04 | `锚点URL.strip().startswith('http')` | 193 / 271 | **193 / 271** | 无差异。其余 78 行分类见 H6 |
| B05 | `hit_id` 计数>1 的组数 / `会话日期` 为空的行数 | 2 组 / 19 行 | **2 组 / 19 行** | 无差异。重复组=`仕佳光子+D8+2025年报`、`仕佳光子+D9+2025年报`；缺日期分布：600703 批次 10 行 + 8 家各 1–2 行 |
| B06 | `len(shipments)` / `len(set(公司))` / `证据等级=='B'` | 103 / 36 / 100 | **103 / 36 / 100** | 无差异。另：C 级 2、D 级 1 |
| B07 | `校准实际值` 非空行数 | 1 / 103 | **1 / 103** | 无差异。唯一行 SE024 的内容并非校准值（见 H5） |
| B08 | universe `enabled=='yes'` 公司数 / 这些公司中无任何 `claims.csv` 记录（经 sources.source_id→company_id 映射）的公司数 | 39 / 27 | **39 / 27** | 无差异，但口径警示：9 家"零 claim"公司在 `event_claims.csv` 有主张，真正全零为 18 家（见 H3） |
| B09 | claims 按 source 归属公司计数，前 5 家合计 / 70 | 48 / 70 = 68.6% | **48 / 70 = 68.6%** | 无差异。前5：LITE 12、CIEN 11、AAOI 10、NOK 10、CSCO 5 |
| B10 | events 中 event_evidence 计数恰为 1 的事件数 | 31 / 34 | **31 / 34** | 无差异。零 evidence 事件 0 个 |
| B11 | event_evidence 中 `independence_class=='first_party'` | 34 / 37 | **34 / 37** | 无差异。余：counterparty 2、same_origin 1 |
| B12 | `链接` 字段含多 URL（；/；/多次 http）行数 / `证据等级=='C'` 行数，分母均为 31 | 15 / 21 | **15 / 21** | 无差异 |

附加机械检查（委托书 §二末段要求）：points 主键 point_id 无重复；shipments row_id 无重复；triage 571 行；sources availability = available 160 / not_collected 5 / unavailable 1；claims review_status = reviewed 69 / candidate 1；event_claims 全部 anchor_reviewed。

---

## 3. 假设裁决表（H1–H10）

```yaml
- hypothesis_id: H1
  verdict: confirmed
  severity: medium
  confidence: high
  evidence:
    - file: points.csv
      record_ids: [全量]
      observation: 判定等级 distinct=200/271 行；195 行带括号过程说明；语义前缀归并后仅 7 类
    - file: points.csv
      record_ids: [P088]
      observation: "判定闸-生产中(kimi取证:自研+外代工流片,fab-lite;锚待codex复核)" — 等级+取证人+工艺判断+待办指令混装
    - file: points.csv
      record_ids: [P146, P175]
      observation: 含"闸内可降档"/"可降待判"降级建议；P175 另含"证据强度弱于MOD1"
    - file: points.csv
      record_ids: [P137, P164, P225]
      observation: 分别含"建议判定闸复核归格""宁严可改在建""疑Driver/TIA类"等疑点与改写建议
  counterexamples:
    - 反例搜索结果：要求找出"至少三类必须留在等级字段、不能移到 review_note 的信息"。结论：**未找到三类**。唯一必须留在该字段的是等级枚举本身（判定闸-生产中/在建、edge_backed、node_wide_gate、宇宙外观察、cross_reference、context_only）；括号内的取证人、疑点、降级建议、归格建议均可无损移入备注字段。"注记从严"（P225）看似修饰等级语义，实际表达的是判定口径选择，同样可以备注承载。
  reader_impact: 无法对"等级"做稳定机器过滤（如"列出所有待降档点"需解析自由文本）；但 状态 列（生产中/在建）独立存在且干净，读者按状态过滤不受污染。属字段合同错误，非事实错误。
  recommended_action: remediate_only（冻结等级枚举、括号内容迁备注；不扩 schema）

- hypothesis_id: H2
  verdict: confirmed
  severity: high
  confidence: high
  evidence:
    - file: tree.yaml
      record_ids: ["tree.C5 (第65行)"]
      observation: "电芯片(DSP/Driver/TIA/CDR/主控MCU)，路线: 共用" — 五种芯片一格
    - file: route_bom.csv
      record_ids: [RB003, RB004, RB008, RB009, RB013, RB014]
      observation: mapping_note 明写"TIA→C5""DSP/Retimer/线性驱动均属C5电芯片""相干DSP/FEC属C5电芯片"；C5 是 800G DR8/1.6T DR8/400ZR 三条路线接收链与数字电路的唯一电芯片格
    - file: points.csv
      record_ids: [P089, P195]
      observation: 国民技术主控 MCU（在建，无订单）与 Marvell P003（DSP+Driver+TIA 全覆盖）、优迅 P118（TIA/Driver/CDR 全线）同格；P089 备注自承"C5格定义同步放宽含主控MCU"——格定义是被数据反向撑宽的
    - file: points.csv
      record_ids: [P225]
      observation: Coherent 10-K 原文经联网核验逐字命中："including lasers, detectors, ICs, and passive optics"，IC 类型未明示；该点仍入 C5，与 DSP 供应商结构等价
    - file: points.csv
      record_ids: [P129, P161]
      observation: 上海贝岭（存储/SoC/电源/AFE）、思瑞浦（光模块控制芯片=偏置控制，非信号链）亦在 C5
    - file: out/参与识别.md
      record_ids: ["第17/51/53/56/99/102/104/116行"]
      observation: 读者页面把上述公司平铺在同一"C5"标签下，仅靠引语文本区分
    - file: tree.yaml + points.csv
      record_ids: [M1, MOD1]
      observation: 同类误等价：M1 混 InP/GaAs/SOI 三种衬底（沪硅产业 12寸SOI 在建 vs 云南鑫耀 GaAs/InP 生产中）；MOD1 混 800G 量产与 1.6T 送样（P133 东山精密备注自承"800G/1.6T具体速率级多处于方案验证/样品阶段"仍标生产中；P229 AAOI 1.6T 客户测试认证中）
  counterexamples:
    - 反例搜索结果：**未阻止**。检查了 tree.yaml（无子格结构）、route_bom mapping_note（反而在 canonical 层断言等价）、claims.csv 的 route_item_id 挂接（全表仅 4 条，其中 C5×RB004 1 条 CL012/Cisco）、读者页面（平铺展示）。阻止越级的只有 points 备注文本与引语，属"只能依靠备注"情形，按委托书规则判为未阻止。部分缓解：P089/P195 状态为"在建"而非"生产中"，且页面标注"2条非量产证据"；CL012 的 RB004 挂接对象是 Cisco（真实 DSP/模块厂），未发生 MCU 公司挂 DSP 路线项的既成事实。
  reader_impact: 若任何人用 cell overlap 回答"谁能供 800G DSP/TIA"，国民技术/上海贝岭/思瑞浦会被错误命中；路线覆盖度统计会把 MCU 计入"数字与模拟电路已有国产供给"。
  recommended_action: collapse 的逆操作不在本轮授权内；本轮仅记录：C5 需要拆分（如 C5a 信号链 DSP/Driver/TIA/CDR、C5b 控制类 MCU/电源/SoC），属架构变更，提交用户裁决，不实施

- hypothesis_id: H3
  verdict: partially_confirmed
  severity: medium
  confidence: high
  evidence:
    - file: calls/universe.csv + calls/sources.csv + calls/claims.csv
      record_ids: [B08, B09]
      observation: 39 enabled、166 源槽位、claims 集中于 12 家公司（前5占68.6%）
    - file: calls/event_claims.csv + calls/disclosures.csv
      record_ids: [MRVL, MTSI, POET, GLW, AXTI, GFS, TSEM, VECO]
      observation: 27 家"零 claim"中 9 家在 event_claims 有主张（MTSI 3、POET 2 等）；真正零主张=18 家（ADTN/AIXA/ASMPT/CLS/SUMITOMO 等连 disclosures 都为 0）
    - file: calls/disclosures.csv
      record_ids: [processing_status]
      observation: anchor_reviewed 42 / no_relevant_claims 8 — "审阅后无实质信息"在 disclosures 层可区分（如 MTSI 4 份披露通读后标记 no_relevant_claims），部分满足反例要求的分别计数
    - file: calls/out/companies/
      record_ids: [目录]
      observation: 渲染层只生成 14 张公司卡，按内容存在性门控；未把 39 家槽位展示为研究覆盖
  counterexamples:
    - calls/out/companies 仅 14 卡且与 claims/event_claims 覆盖一致，是"页面未夸大覆盖"的直接反例；disclosures.no_relevant_claims 状态区分了"审过无货"与"没审"。
  reader_impact: 若有人用"39 家公司、166 个来源"概括海外情报覆盖（如对外介绍），会比实际 claim 级覆盖（12–21 家）强约 2 倍；当前读者页面未犯此错。五级覆盖（slot/retrieved/claim/reviewed/event）在数据层可算、在展示层未分级标注。
  recommended_action: remediate_only（任何覆盖率表述须注明级别；两套主张结构问题并入 H10）

- hypothesis_id: H4
  verdict: confirmed
  severity: high
  confidence: high
  evidence:
    - file: calls/events.csv + calls/event_evidence.csv
      record_ids: [全量]
      observation: 31/34 事件仅一条 evidence；independence_class = first_party 34、counterparty 2、same_origin 1；event_status = asserted 32 / corroborated 2，与证据独立性完全一致（2 个 corroborated 恰是 2 个有 counterparty 证据的事件）
    - file: calls/events.csv, calls/event_evidence.csv, calls/event_claims.csv, calls/disclosures.csv
      record_ids: [EV001, EE001, ECL001, D_AAOI_20260309_ORDER]
      observation: 完整链核验通过：EV001(asserted/volume_order) → EE001(first_party/OG_AAOI_20260309_ORDER/单方公司公告) → ECL001(anchor_reviewed) → D_AAOI_20260309_ORDER(first_party, investors.ao-inc.com/node/16751)
    - file: 联网一手核验
      record_ids: [D_AAOI_20260309_ORDER]
      observation: 2026-09-04 抓取 AAOI 官网新闻稿原文，引语逐字命中（"received its first volume order for its 1.6T data center transceivers"）；注意原文称"shipments are expected to begin early in the third quarter of 2026"——订单为实、交付为前瞻，event 的 volume_order 阶段标注准确但读者易把 order 读成 shipment
  counterexamples:
    - 委托书要求≥3 例多来源/对手方证据，**实际仅 2 例达标，按实际数量报告**：EV013/EV014（MACOM×IQE 投资与长期供应协议，双方各自披露交叉）；另 EV027 有两条 evidence 但 same_origin（同一 OG_GLW_NVDA_20260506），按共同规则不算独立。不足三例本身即是 H4 的强化证据。
  reader_impact: "reviewed/anchor_reviewed"只保证原文已核，不保证事件被独立证实；32 个 asserted 事件若被概括为"已确认事件"即越级。
  recommended_action: retain（events/event_evidence 的 independence_class 结构是必要审计边界）；展示层须把 asserted 与 corroborated 分列

- hypothesis_id: H5
  verdict: confirmed
  severity: high
  confidence: high
  evidence:
    - file: shipments.csv
      record_ids: [全量]
      observation: 15 种单位并存：万只15/万件24/台21/台套7/万个6/万片6/支套3/万支3/片个3/千只3/千克3/万平方米3/KK3/万颗2/万美元1；cell_id 含"D系聚合""行业聚合(D7在册)""C1/C2/C3/C4/D3/D8/MOD1/MOD3/C6聚合"等跨层聚合
    - file: shipments.csv
      record_ids: [SE001, SE015, SE023, SE028, SE006]
      observation: 同表混有：模块销量（旭创2109万只）、传输类聚合销量（德科立170万支/套，含电信+数通）、溅射靶材千克数（阿石创）、PCB 平方米（博敏电子）、行业出口额美元（SE006，D级情景行）
    - file: shipments.csv
      record_ids: [100条B级行]
      observation: 证据等级 B=100/103，推导式列实为"年报产销表直接披露"说明；ADR-0001 设计为"C级封顶推断层"，例外条款仅允许"量价齐露"标 B——实际 100 条 B 意味着例外吃掉规则，表名"推断层"与内容整体不符
    - file: shipments.csv
      record_ids: [SE024]
      observation: 唯一填写"校准实际值"的行内容是"与美国公司签订量产化耦合设备合同1,620.65万美元"——不是出货量校准值，校准列被挪用；误差 0/103、校准日期 6/103
    - file: shipments.csv
      record_ids: [SE071, SE072]
      observation: 2 条 C 级行为同比反算（2024=2025值/(1+增速)），恰是 ADR 设想中的推断行，反而被海量 B 级直接披露稀释
    - file: docs/adr/0001-shipment-inference-layer.md
      record_ids: [全文]
      observation: ADR 要求推断行必填推导式+收入锚+ASP锚+双检查锚；实际 B 级行 ASP输入 55/100 为"-"、海关上限检 86/100 为"-"，推断链字段对直接披露行大面积占位
  counterexamples:
    - 安全跨公司比较组（委托书要求至少一个）：**SE001 中际旭创 × SE002 新易盛**——2025年度、万只、年报产销表直接披露、数通光模块为主业。但仍有口径残留：旭创口径"光通信收发模块"vs 新易盛"光互联产品"，且旭创营收含海外产能出货（行内注记已自承"不直接可比"）。故安全组存在但仅存于"同期间+同单位+同披露表型+相近业务边界"的极小交集内，聚合任何跨单位/跨聚合行均无业务含义。
  reader_impact: 把本表直接做横向排名或加总会产生无意义数字（如 万只+千克+万美元 同列）；"推断层"表名使 100 条硬披露被低估为推断，或反向使 2 条真推断被高估为披露——双向误导。
  recommended_action: collapse（直接披露行与推断行分离；校准列仅约束真推断行；不新增字段，靠行级标记或分表，提交用户裁决）

- hypothesis_id: H6
  verdict: confirmed
  severity: medium
  confidence: high
  evidence:
    - file: points.csv
      record_ids: [全量]
      observation: 锚点URL 分类：direct_url 193 / 占位"有锚" 39 / 描述性引用 20 / markdown_url 9 / 本地语料引用 8 / "同上" 2。字段名承诺 URL，78/271 = 28.8% 的行不是 URL
    - file: points.csv
      record_ids: [P001, P002, P004, P006]
      observation: "有锚；发行人自述（Fabrinet 10-K）""有锚；披露方产品列（长光华芯招股书供应商表）"——声称有锚但字段内无定位信息
    - file: points.csv
      record_ids: [P042, P043]
      observation: 锚点="同上"，依赖 P041 的行序位置才能解析，排序即断链
    - file: points.csv
      record_ids: [P003, P009]
      observation: 描述性引用"FY2026 10-K产品段(sec.gov mrvl-20260131.htm,补锚2026-07-24)""S0a本地扫描2025年报（002384__em_东山精密...pdf）"
    - file: out/全景.md
      record_ids: ["第435行(Fabrinet)"]
      observation: 占位文字被渲染为假超链接 "[锚](有锚；发行人自述（Fabrinet 10-K）)"，读者点击无处可去
  counterexamples:
    - 抽核 10 条 direct URL（cninfo×4、sec.gov×3、10jqka、p5w、ieee802）：HTTP GET 全部 200（注：SEC 与同花顺对 HEAD 请求返回 403/404，GET 正常，自动化检查须用 GET）。其中 3 条做原文逐字核验全部命中：Fabrinet 10-K "contributed 27.6% and 18.2%"（E001/E003 锚）、AAOI 新闻稿（EV001 链）、Coherent 10-K "lasers, detectors, ICs, and passive optics"（P225）。**完成度声明（不得夸大）**：可访问性 10/10 完成；引语定位（原文逐字核验）仅完成 3/10，其余 7 条只做了可访问性检查、未做引语定位。委托书要求的"可访问性 + 引语定位"双重抽核在 direct 样本上仅 3 条完整完成，其余 7 条的引语定位部分按 **insufficient_evidence** 处理，不计入双重抽核完成数。
    - 抽核 10 条非 direct：逐条记录了 4 条的可复原性结果——corpus/qa 本地引用 2 条（P187 锐捷、P195 国民技术）indexId 均在 jsonl 中命中；"S0a本地扫描"类 2 条（P009 东山精密、P041 永鼎）文件均存在于 corpus/annual/<代码>/<代码>/ 下可复原；另有分类级结论："有锚"占位类（P001/P002 等 39 行）无法从字段自身定位原文，需依赖备注或外部记忆，不满足"字段内唯一定位"。**完成度声明（不得夸大）**：上述检查属于可复原性/可访问性层面；非 direct 样本**均未完成"引语在原文中的逐字定位"**（indexId 命中只定位到语料条目、文件存在性只证明可复原，均不等于引语定位），且 10 条中仅 4 条有逐条记录，其余 6 条仅有分类级判断。故非 direct 10 条的"可访问性 + 引语定位"双重抽核未完整完成，未完成的引语定位与未逐条记录部分按 **insufficient_evidence** 处理，不得计为已完成。
  reader_impact: 直接 URL 部分质量良好（可访问性抽检 10/10 通过；引语逐字核验已做的 3 条全命中，但仅覆盖 3/10，其余按 insufficient_evidence）；风险集中在 39 行"有锚"占位与 2 行"同上"——审计重放时这 41 行需人工重建锚。
  recommended_action: remediate_only（最小动作：把 2 行"同上"替换为被引用行的实际锚；39 行"有锚"补全为真 URL 或本地路径；渲染层对非 URL 值不生成 <a>。不新增字段）

- hypothesis_id: H7
  verdict: confirmed
  severity: medium
  confidence: high
  evidence:
    - file: edges.csv
      record_ids: [表头]
      observation: 列=edge_id/供方/需方/供方point_id/需方point_id/数值类型/数值/单位/占比或金额原文/财年/边等级/证据文件/锚点/验证状态/备注——无 relation_type、无 product_scope
    - file: edges.csv
      record_ids: [全量]
      observation: 236 边=实边198+半边34+推断A 2+推断B 2；171 边无数值；数值型中 45 占比+20 金额多为 10-K/年报">10%客户"或前五大客户披露——是公司级收入集中度，非光模块产品线口径
    - file: edges.csv
      record_ids: [E026, E027, E028]
      observation: Lumentum→Apple 占比边，备注"3D传感/消费端非光通信"——产品范围纠偏只在备注
    - file: edges.csv
      record_ids: [E036, E037, E038, E232]
      observation: 4 条解匿推断边（Lumentum→Ciena/Google、Fabrinet→Lumentum、太辰光→Corning）与实名边同表同级展示，等级区分仅在 边等级 列
    - file: edges.csv
      record_ids: [E090, E144, E174, E224]
      observation: 抽样 20 条实边中混有：测试仪器销售（联讯仪器→旭创）、关联交易购销（湖北瑞创信达→华工）、委托加工（昱升→源杰）、外协采购（京瓷→长光华芯）——关系类型各异且大部分未明示是否光模块产品
    - file: edges.csv
      record_ids: [E001/E002/E069 等15组]
      observation: 同供需方跨年重复观测 15 组（Fabrinet→NVIDIA 3 期、Lumentum→Ciena 4 期等），实体解析良好，但"多期打包待展开"备注说明期间粒度未完全规整
  counterexamples:
    - 缓解事实：E026 的备注确实写明"非光通信"；E033 Lumentum→华为边备注含"跨境边…第二条对华断边时间序列"的分析性标注；out/全景.md 引用边时写作"供货边 E110"（仕佳光子→Intel，招股书客户披露），该例产品范围无误。未发现页面把 E026 Apple 边表述为光模块供货的既成错误。
  reader_impact: 结构不阻止"Fabrinet→NVIDIA 27.6%（公司级）"被读成"光模块代工占 NVIDIA 采购 27.6%"之类的投射；解匿边与实名边并存要求读者注意 边等级。
  recommended_action: retain（表本身承载真实多类型关系）；relation_type/product_scope 属新增架构，提交用户裁决，不在本轮实施

- hypothesis_id: H8
  verdict: confirmed
  severity: high
  confidence: high
  evidence:
    - file: macro_evidence.csv
      record_ids: [全量31条]
      observation: 21/31 C 级；15 条链接字段多 URL；证据类型混"机构报告/厂商规格/二手汇总/多型号混合口径"
    - file: macro_evidence.csv
      record_ids: [MC012, MC027]
      observation: 链接为百度搜索页（baidu.com/s?wd=...），不是来源
    - file: macro_evidence.csv
      record_ids: [MC015, MC016, MC017, MC018, MC020, MC028, MC030]
      observation: 来源为雪球用户帖，链接写作 "ssgsmarketing@xueqiu.com/..." 伪 URL（@前为用户名，非可访问地址）
    - file: macro_evidence.csv
      record_ids: [MC004, MC013, MC014]
      observation: 口径备注自承"同花顺/东方财富/雪球互引=回声室""C114/头条/雪球/高盛多家二手互引=回声室"——来源独立性不可计算在表内已被自认
    - file: macro_evidence.csv
      record_ids: [MC024]
      observation: 主张"交付周期8-10周压缩至4周以内"，备注自承原文为"传统12周压缩到8周甚至更短"——口径跳跃，4周无原文支持
    - file: macro_evidence.csv
      record_ids: [MC009, MC010]
      observation: 证据等级 A 但来源="capability_details.csv"（内部账本自引用）——A 级语义应为一手外部证据直接支持，自引用不满足
    - file: macro_evidence.csv
      record_ids: [MC001, MC002, MC011]
      observation: B 级但链接混 c-light（讯石，二手转载）/新浪/东方财富；MC002"60%"是"2024前十排名+2026预测合计"的推导值
  counterexamples:
    - MC006（IEEE 802.3df 800G DR8=8×100G）、MC008（OIF 400ZR IA）为标准组织一手材料直接支持同一口径，A 级合格；MC007（P802.3dj 邮件列表）为一手制定中材料，B 级合理。证明表内存在正确的分级样本，问题是分级执行不一致。
  reader_impact: 首页/路线背景若引用 MC024"4周"或 MC002"60%"即输出过强结论；本次检查 out/*.md 未发现这些口径已被渲染（检索"4周/228亿/60%"无命中），属潜伏风险非既成输出。
  recommended_action: remediate_only（MC009/MC010 降级或改标内部指标类型；MC024 改回原文口径；百度/伪 URL 链接替换或标注"检索入口非来源"）

- hypothesis_id: H9
  verdict: confirmed
  severity: low
  confidence: high
  evidence:
    - file: triage.csv
      record_ids: ["仕佳光子+D8+2025年报 ×2", "仕佳光子+D9+2025年报 ×2"]
      observation: 2 组重复均为同一命中不同截断片段双录（同一处置、同一日期 2026-07-25、引语互为前后文片段）——是主键设计不含片段标识导致的业务键碰撞，内容无害（均驳回），但说明扫描门未覆盖事件键唯一性
    - file: triage.csv
      record_ids: [19条缺日期行]
      observation: 10/19 集中于 600703 三安光电问询函批次（hit_id 含 sanan-inquiry-20260810.pdf，日期可从文件名恢复为 2026-08-10）；其余 9 条散布 7 家（鹏鼎/东田微/一博/仕佳/强达/中富/广合）
  counterexamples:
    - 571 行中仅 2 组碰撞、19 行缺日期（3.3%），主体完整性良好；重复组两行的处置结论一致，未造成矛盾裁决。
  reader_impact: 低。triage 是去重/驳回台账，读者不可见；风险在于后续统计"扫描命中率"时分母轻微失真。
  recommended_action: remediate_only（建议最小稳定测试：unique(hit_id, 片段哈希) 与 not-null(会话日期)；本轮不实现）

- hypothesis_id: H10
  verdict: partially_confirmed
  severity: medium
  confidence: medium
  evidence:
    - file: questions_manual.csv
      record_ids: [全量]
      observation: 0 数据行（仅表头）；scan.py/render.py 依赖情况属 Cursor 审计范围，本方未核代码
    - file: calls/point_metrics.csv
      record_ids: [全量]
      observation: 0 数据行（仅表头 schema）
    - file: calls/solution_links.csv
      record_ids: [SL001, SL002]
      observation: 2 行均 evidence_status=insufficient；且 constraint_requirements CRQ001/CRQ002 备注明写"迁移自legacy SL001/SL002"——内容已被迁移，原表为冻结 legacy
    - file: calls/constraint_requirements.csv
      record_ids: [CRQ001, CRQ002]
      observation: 2 行，comparator/target_value/unit 数值三元组全空——约束的量化部分从未填充
    - file: calls/technology_feedback.csv
      record_ids: [TF001, TF002 等4行]
      observation: 4 行承载真实独有问题（如 TF001：官网博客证明 1.6T 可现场运行≠已商业部署，stage 从 demonstrated 降为 planned_ramp），且有读者可见输出 calls/out/technology-feedback.md
    - file: calls/universe.csv + calls/company_candidates.csv + calls/watch_entities.csv
      record_ids: [三表]
      observation: universe 39 / candidates 64（57 已 promoted）/ watch 47；universe∩candidates=23 家重复登记；但 watch_entities 语义明确不同（"仅用于显式事件证据；不进入四季度电话会覆盖池"），生命周期差异部分真实
    - file: calls/claims.csv + calls/disclosures.csv + calls/event_claims.csv
      record_ids: [MRVL, MTSI 等]
      observation: 两套"来源→主张"结构职责真实重复且各覆盖一部分公司（12 家只在旧结构、9 家只在新结构），任何覆盖率统计跨两表才能算全——split-brain 已在 B08/B09 复算中实测发生
  counterexamples:
    - 须为"建议保留"指出不可替代读者价值的反例：events/event_evidence 的 independence_class/origin_group 无法从其他表派生（retain）；technology_feedback 有 reader-visible 输出且内容不可派生（retain）；claims.csv 承载 70 条 reviewed 原子主张且是 calls/out 公司卡数据源（retain）。相反 questions_manual/point_metrics/solution_links 三方均找不到"当前正在使用且不可派生的读者可见结论"——未找到保留理由。
  reader_impact: 空表本身不输出错误结论，但维护面与认知负担真实；双主张结构直接影响 H3 覆盖率口径的正确性。
  recommended_action: 见 §5 消融矩阵
```

---

## 4. 证据与反例（联网一手核验记录）

仅使用一手来源；二手材料未用于任何裁决支持。

| 核验对象 | 来源 | 结果 |
|---|---|---|
| E001 Fabrinet→NVIDIA 27.6%（FY2025） | [Fabrinet 10-K, SEC](https://www.sec.gov/Archives/edgar/data/1408710/000140871025000039/fn-20250627.htm) | 原文 "contributed 27.6% and 18.2%" 命中，E003 Cisco 18.2% 同句命中 |
| EV001 AAOI 1.6T 首笔批量订单 | [AAO 官网新闻稿 2026-03-09](https://investors.ao-inc.com/node/16751) | 引语逐字命中；原文称交付"expected to begin early in Q3 2026"——订单属实、出货为前瞻 |
| P225 Coherent C5（ICs 类型未明示） | [Coherent 10-K FY2025, SEC](https://www.sec.gov/Archives/edgar/data/820318/000082031825000014/iivi-20250630.htm) | "including lasers, detectors, ICs, and passive optics" 逐字命中，IC 类型确未明示 |
| 10 条 direct URL 可访问性 | cninfo×4 / sec.gov×3 / 10jqka / p5w / ieee802 | GET 全部 200（可访问性 10/10）；SEC/10jqka 对 HEAD 返 403/404 属反爬假象，自动化核验须用 GET。**引语定位仅完成 3/10**（即上三行 Fabrinet/AAOI/Coherent），其余 7 条未做引语定位，按 insufficient_evidence |
| 非 direct 锚可复原性 | corpus/qa/301165、corpus/qa/300077 indexId grep；corpus/annual/600105、002384 文件名匹配 | 逐条记录 4 条：本地语料引用可唯一复原；"有锚"占位 39 行不可从字段自身复原。**未完成逐条引语定位**（indexId/文件存在性 ≠ 引语定位），双重抽核缺口按 insufficient_evidence |

**支持范围声明**：上述核验只证明"完成逐字核验的 3 条锚（Fabrinet/AAOI/Coherent）真实且引语存在于原文"以及"10 条 direct URL 可访问、非 direct 样本多数可复原"，不证明任何公司经营结论正确；AAOI 订单为单方披露（first_party），按 H4 不能升级为独立证实。

---

## 5. 消融矩阵

| 候选 | 委托书初步分类 | 本审计分类 | 依据（记录级） |
|---|---|---|---|
| `questions_manual.csv` | remove_now | **remove_now** | 0 数据行；无任何读者可见结论引用（out/*.md 无命中） |
| `calls/point_metrics.csv` | remove_now | **remove_now** | 0 数据行；schema/validator/测试的删除依赖属 Cursor 范围 |
| `calls/solution_links.csv` | remove_now 或冷冻文档 | **remove_now**（内容已迁移，无信息损失） | SL001/SL002 均被 CRQ001/CRQ002 显式迁移且原表精确冻结；唯二信息是 negative verdict 史，已留在 CRQ 备注 |
| `calls/constraint_requirements.csv` | remove_now 或 collapse | **collapse** | 2 行、数值三元组全空；语义（约束需求）真实但无量化内容，应并入 claim/event 评审备注而非独立成表 |
| `calls/technology_feedback.csv` | collapse | **retain** | 4 行承载不可派生的降级判定（TF001 demonstrated→planned_ramp），且有读者可见输出 technology-feedback.md；collapse 会丢 claim 配对结构 |
| 三套海外主体表 | collapse | **collapse（universe+company_candidates）；watch_entities retain** | universe∩candidates=23 家重复登记且 57/64 已 promoted（管道使命基本完成）；watch 的"仅事件证据、不进覆盖池"语义不可并入 |
| 两套海外来源/主张结构 | collapse 或 retain | **collapse** | split-brain 实测：12 家只在 claims.csv、9 家只在 event_claims 链；B08/B09 跨表才能算全，覆盖率统计已被实际污染 |
| `shipments.csv` 推断/校准结构 | collapse | **collapse** | 100/103 为直接披露，与 ADR-0001 推断层定位偏离；校准列 1/103 且唯一行被挪用；直接披露与推断应分离 |
| `capability_details.csv` | derive_not_store | **derive_not_store**（本审计仅间接支持） | 由 build_detailed_capability_report.py 从 points 生成；MC009/MC010 以其为来源恰证明其是投影非事实层 |
| `archive/**` | remove_now（从新生产仓库） | **insufficient_evidence** | 本审计禁读 archive，无法核验"无运行时与证据锚依赖"；已知 tree.yaml 元注释引用 archive/industry-chain-v2 为底稿（文档性引用）。需他方以允许读 archive 的授权核验 |
| 九页网页 | retain | **retain** | 用户明确要求跟踪发布快照；非 canonical 标注应保持 |

---

## 6. 依赖与迁移风险

本审计按角色分工不深读代码（scan.py/render.py/validators 的逐行依赖属 Cursor 范围），以下为数据侧实测依赖：

- **`points.csv` 判定等级改动**：影响 out/参与识别.md、out/全景.md 的"已确认参与/待确认"列与证据计数（页面显示"7条生产中证据"等由 状态+判定等级 派生）；`capability_details.csv` 重建；MC009/MC010 的"已确认公司数/能力记录数"口径。回滚点：等级括号文本迁备注是可逆的纯数据搬迁，原串可保留在备注首行。
- **`shipments.csv` 拆分**：out/问题队列.md 第 12/87/88 行有 QC 规则直接引用 shipments.csv 校准三字段（QC-SE071/SE072），拆分时该校验需同步迁移；回滚点：行级拆分可逆（row_id 稳定）。
- **海外双主张结构合并**：直接影响 calls/out/companies 14 张公司卡、theme-matrix.md、event-intelligence.json 的生成输入；claims.csv 的 source_id→sources 外键与 event_claims 的 disclosure_id→disclosures 外键需一次映射对齐；回滚点：两表现状各自闭合，合并可先在导出层做 union 视图验证再动 canonical。
- **空表删除（questions_manual/point_metrics）**：数据侧零风险（0 行），风险全在代码/测试引用侧（Cursor 主审）。
- **九页网页**：retain，无迁移；但 `out/全景.md` 对非 URL 锚渲染假链接的问题属于渲染规则修正，不涉及 canonical。

---

## 7. 最小修复顺序（每步只解决一个语义问题，不扩 schema）

1. **展示层先分级**：海外事件与页面把 `asserted`/`corroborated` 分列展示（H4，最高读者风险，零 canonical 改动）。
2. **macro_evidence 口径纠错**：MC024 改回"12→8周"原文口径；MC009/MC010 从 A 降级或改标内部指标（H8，纯数据修正）。
3. **锚点止血**：2 行"同上"替换为实锚；渲染层对非 http 值不生成超链接（H6 中可立即执行的部分）。
4. **shipments 行级标记**：用既有 情景标记/推导式 文本把 100 条直接披露与 3 条推断/情景行显式区分，校准列仅限推断行（H5，数据值级修正）。
5. **判定等级搬迁**：冻结 7 类等级枚举，括号过程文本迁入备注（H1，可逆数据搬迁）。
6. **triage 完整性**：补 19 行会话日期（10 行可从 hit_id 文件名恢复）；新增唯一性/非空测试（H9，测试新增属用户授权范围）。
7. **提交用户裁决的架构项（本轮不实施）**：C5 拆分（H2）、edges 增 relation_type/product_scope（H7）、海外双主张结构合并与主体表 collapse（H3/H10）、空表删除（H10）。

---

## 8. 未解决问题（insufficient_evidence / 待裁决）

1. **archive/** 消融：禁读边界内无法核验运行时依赖，标记 insufficient_evidence，需专项授权。
2. **39 家 enabled 公司的 slot 获取深度**：sources.csv 标 available=160 但"retrieved 且通读"与"retrieved 未通读"的区分只在 disclosures 层部分存在（8 份 no_relevant_claims），claims.csv 侧无等价状态——"审过无货 vs 未审"的全量分别计数无法在当前 schema 下完整给出。
3. **国民技术 C5 点的最终归格**：若 C5 拆分获批，P089/P195 应落入控制类子格；但"主控 MCU 是否算光模块 BOM 关键组成"是领域判断，超出本审计裁决权。
4. **P003 Marvell 等 20 行描述性锚的原文复核**：本审计抽核了其中 2 行可复原，未逐行核 20 行。
5. **E033 Lumentum→华为"对华断边时间序列"备注**：含分析性结论，其推导是否达到派生标准未在本轮展开。
6. **calls/out 渲染器对零 claim 公司的门控逻辑**：实测 14 张卡与内容覆盖一致，但门控规则源码未读（代码属 Cursor 范围），不排除其他输出（如 panorama-intelligence.csv）按槽位口径展示。
7. **H6 双重抽核未完整完成（insufficient_evidence）**：委托书要求 direct 10 条与 non-direct 10 条各自完成"可访问性 + 引语定位"双重抽核。实际完成：direct 可访问性 10/10、引语定位仅 3/10；non-direct 逐条可复原性记录 4/10、引语定位 0/10（indexId 命中与文件存在性不等于引语定位）。缺口明细见 §3 H6 counterexamples 与 §4 表。如需闭环，须补做 direct 余 7 条与 non-direct 10 条的引语逐字定位，并将 non-direct 余 6 条补做逐条可复原性记录。

---

## 9. 合规核验记录

- 基线：`git rev-parse HEAD` = `43d1d6cfa335e8693f33fa834a0d775ae2879195` ✓ 与 instruction commit 一致。
- canonical 指纹（审计前，SHA-256 前 16 位）：knowledge.yaml `ecb9f6ef…`、points.csv `a481a452…`、edges.csv `1e5c6739…`、triage.csv `cc309eea…`、route_bom.csv `3328983d…`、tree.yaml `88ab14a1…`、shipments.csv `ab93cb1a…`、macro_evidence.csv `506411fa…`、company_segment_revenue.csv `4cc7807e…`。
- 审计后指纹复核（2026-09-04 收尾）：上述 9 个 canonical 账本 SHA-256 与审计前逐一相同；`git status` 显示本会话新增文件仅本报告（ACTIVE_WORKPACK.yaml 的修改在审计启动前即已存在，非本会话所为；同目录下出现的 Cursor 报告文件为另一路审计产出，本审计未读取）。HEAD 保持 `43d1d6c…` 未变。
- 禁读遵守：未打开 archive/、旧分支/worktree、closure-pilot 材料、完整代理轨迹、Cursor 报告。
- 联网使用：仅 sec.gov、investors.ao-inc.com、cninfo、p5w、10jqka、ieee802（均一手/准一手）；未使用登录、验证码或付费来源。
- stop_and_escalate：未触发（未发现读者可见错误结论正在输出；潜在误读风险均已在 H2/H4/H7/H8 的 reader_impact 中列明）。
