# flows/SPEC-v1.3.md — v1.3 工单：零成本维度挖掘 + 进口侧 + 台账晋级

**核心洞察（本轮起点）**：已采集的四维数据里"贸易方式"与"注册地"两个字段从未分析——
①贸易方式可判马来西亚迁移是真产能转移还是保税转口（A级判定器）；②注册地×去向
可做公司级出口的 C 级代理（新易盛=四川、光迅=湖北等省域错位）。进口侧（上游依赖
量化）全程未采，是结构性遗漏。

**红线修订**：linkage 层"禁止公司级份额分配"修订为——禁止无依据分配；**允许注册地
代理推断，强制标注 C 级+代理逻辑+可推翻条件**。

## 六路分工

| 路 | 承包方 | 任务 | 产出 |
|---|---|---|---|
| X1 维度挖掘 | cursor grok | 贸易方式拆解+注册地×去向交叉（纯聚合，不下判定） | flows/out/customs-trademode.csv + customs-province.csv |
| X2 图谱 v1.3 | **codex**（接替 kimi 前端） | 30月流向滑条+贸易方式层+linkage可视化 | output/光模块产业图谱-v1.3.html |
| X3 进口HS研究 | claude sonnet | 光芯片/EML/激光器件进口 HS 编码清单（税则锚点） | flows/out/import-hs-codes.md |
| X4 集团一侦察 | kimi k3 | 联讯"集团一"解匿的公开线索收集（只收线索不判定） | flows/out/jituanyi-leads.md |
| X5 晋级预检 | codebuddy hy3 | lianxun-extract.json→待复核边草稿生成器 | flows/src/lianxun_to_edges.py + 草稿CSV |
| X6 判定+采集+终验 | Claude(+用户) | 联讯边人工复核晋级E082+；集团一B工序判定；进口侧采集（用户滑块）；终验 | 台账更新+判例+VERIFICATION-v1.3 |

## X1 契约（grok）

输入（只读）：flows/input/customs-85177950-{2025,2026H1}-breakdown-usd.csv。
产出两表（纯聚合，字符串金额，禁止任何推断性列）：
1. customs-trademode.csv：`月份,贸易伙伴,贸易方式,出口量kg,金额USD`——伙伴取
   全月金额 top8+“其他”合并；另附打印：马来西亚按贸易方式的月度占比表（一般贸易
   vs 海关特殊监管区域物流 vs 进料加工等）
2. customs-province.csv：`月份,注册地,贸易伙伴,出口量kg,金额USD`——注册地全保留，
   伙伴 top8+其他
自测：两表行数、各月合计与 customs-monthly 对应月吻合（对账打印，容差<0.5%）。

## X2 契约（codex，前端）

output/光模块产业图谱-v1.3.html，不改 v1.0/v1.2。可读 flows/src/build_atlas_v12.py
参考但重新实现。要求：自包含/原生SVG+JS/中文，三层结构+顶部切换：
1. 关系层：81 边（沿用 v1.2 处理：含 E014 半边与苏世博补节点）
2. 流向层：**30 月滑条**（customs-monthly+customs-partners 全量），2025-04 拐点
   月份特殊标记；伙伴 top10+其他
3. 维度层（新）：读 X1 的 customs-trademode.csv——马来西亚/美国/泰国三个去向的
   贸易方式堆叠条形（月度），直观回答"迁移是转口还是真移"
图例：数据等级标注 + 夹层警示照写。X1 未交付时该层显示"数据待 X1"占位不崩溃。
自测断言（svg/零外链/关键实体/滑条月份 202404 与 202606 在位）打印。

## X3 契约（sonnet）

产出 flows/out/import-hs-codes.md：光模块上游器件的现行进口 HS 编码清单——
激光二极管/光电探测器/光收发组件外购件等相关 8 位编码（8541 系 + 85177950 自身
进口口径），每个编码给：中文品名、税则依据锚点（gss.mof.gov.cn 附件 PDF 或海关
税则库 URL）、与光模块 BOM 的对应关系（对应 flows-seed 哪类构成项）、建议查询
优先级。红线：编码必须出自税则原文，禁止凭记忆写编码不给锚。

## X4 契约（kimi）

产出 flows/out/jituanyi-leads.md：围绕联讯仪器"集团一"（2023:9.90%→2024:16.92%
→2025Q1:35.51%）收集公开线索：①联讯 IPO 问询函回复是否已公开（上交所审核页）
及其中对第一大客户的问询；②招股书其他段落的集团一特征（销售区域/产品对应/回款
条款）——从 flows/input/lianxun_prospectus.txt 检索；③行业报道对联讯大客户的
表述。每条线索带来源+T1路径。**禁止下判定、禁止写候选名单**——判定是 X6 的活。

## X5 契约（hy3）

flows/src/lianxun_to_edges.py：读 lianxun-extract.json，把 2022-2025Q1 各期
客户行转为 edges.csv 10 列 schema 草稿（edge_id 留空占位 EXXX，验证状态=
"v1.3待人工复核"，锚点=招股书承载 URL 从 meta 取，匿名行按半边槽位格式）；
输出 flows/out/lianxun-edges-draft.csv + 打印行数。不碰 output/edges.csv——
晋级由 X6 人工执行。

## X6 终验线（Claude）

X1 对账抽检；X2 断言+亲验三层；X3 编码逐个回访锚点；X4 线索红线检查；
X5 草稿逐行对 lianxun-extract.json；台账晋级后全量校验器 PASS；进口采集视
用户时间安排。
