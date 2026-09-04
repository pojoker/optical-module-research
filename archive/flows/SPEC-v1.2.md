# flows/SPEC-v1.2.md — v1.2 工单：连接层 + 流向图谱 + 原文升级

**目标**：还 v1.1 三笔债（连接层/集采原文/2025缺口）+ 图谱吃进海关流向数据 +
边表吃进第二家 IPO 双侧实名样本。纪律沿用（四件套/金额逐位/T3不入图/诚实降级）。

## 六路分工

| 路 | 承包方 | 任务 | 产出 |
|---|---|---|---|
| W1 流向图谱 | kimi k3 | 图谱 v1.2：保留 81 边关系层，新增"出口流向层"（海关数据） | output/光模块产业图谱-v1.2.html |
| W2 连接层 | codex | linkage.csv：公司↔产品线↔HS编码↔出口去向的连接表 + 生成器 | flows/out/linkage.csv + flows/src/build_linkage.py |
| W3 集采原文 | claude sonnet | 把 5 条转载记录升级到原文 T1：省级阳光采购/公共资源交易平台镜像探测 | procurement-awards.csv 升级 + 通道卡增补 |
| W4 联讯仪器 | cursor grok | 定位并抽取联讯仪器 IPO 招股书（双侧实名+原材料构成），产出新边与 flow | flows/out/lianxun-extract.json |
| W5 校验扩展 | codebuddy hy3 | validate_edges.py 扩展：新增 --flows/--linkage/--catalog 模式的 schema 校验 | demo/src/validate_edges.py 升级 |
| W6 2025缺口+终验 | Claude+用户 | 海关 2025 年 2-12 月补采（用户滑块一次）；六路终验 | customs 更新 + VERIFICATION-v1.2 |

## W1 流向图谱契约（kimi）

输入（只读）：output/edges.csv(81边)/nodes.csv(42节点) + flows/out/customs-monthly.csv
+ flows/out/customs-partners.csv。产出全新文件 output/光模块产业图谱-v1.2.html，
不改 v1.0 文件。要求：
1. 自包含（零外链）、原生 SVG+vanilla JS、中文正常——同 v1.0 标准
2. **双层结构 + 顶部切换**：①关系层=v1.0 的 81 边图（可重用你的布局思路，重新实现）；
   ②流向层=中国→各出口目的地的桑基式流向（数据源 customs-partners，取 202501 与
   2026H1 各月，伙伴取金额 top10 + "其他"合并），边宽∝金额，hover 显示 月份/kg/金额/币种
3. 流向层须直观呈现"美国第一→马来西亚第一"的迁移（如 202501 vs 202606 对比或月度滑条）
4. 图例注明：流向层=HS 85177950 海关出口数据（A级）；目的地≠终端客户（转运存在，
   夹层警示照写）
5. 自测断言（含"马来西亚""85177950"字符串在位、零外链）打印结果

## W2 连接层契约（codex）

linkage.csv 十列：`link_id,公司,公司代码,产品线,速率档,HS编码,出口相关性(直接/间接/无),
去向佐证(伙伴国),证据锚点,备注`。数据源（只读）：flows/out/catalog.csv、
flows/out/flows-seed.json、output/edges.csv、flows/out/customs-partners.csv。
规则：只做**证据可锚**的连接——旭创/新易盛/光迅的光模块产品线→85177950（直接，锚=
海关商品名"光通信设备的激光收发模块"+产品目录页）；天孚（器件，非整模块）→间接；
设备商→无。**禁止编造公司级出口份额**——海关数据不分公司，公司↔去向只能标"佐证"
（如天孚→Fabrinet 实名边 ↔ 泰国流向共存），不得写成定量分配。生成器脚本可复跑。

## W3 集采原文契约（sonnet）

对 procurement-awards.csv 现有 5 条：逐条尝试找到**免登录的公示原文或权威镜像**
（省电信阳光采购网详情页、地方公共资源交易中心、运营商省公司官网公告）。找到→
升级该行验证状态并替换锚点；找不到→保持降级态并在通道卡记录尝试轨迹。
不注册账号、不绕登录墙。

## W4 联讯仪器契约（grok）

联讯仪器=收割库 IPO 在途名单第二家（上交所科创板方向，S03 通道）。步骤：
①WebSearch/上交所审核页定位招股书申报稿 PDF（认 static.sse.com.cn 或权威承载页）；
②下载到 flows/input/；③抽取：前五大客户表（预期实名）、前五大供应商表、原材料
采购构成、主营产品结构；④输出 lianxun-extract.json（沿用 extracted.json 的 schema
+flows-seed 的 flow 结构）。硬规矩同前：数字逐位、匿名如实、抽不到写 warnings；
若 IPO 文件不可得（撤回/未受理），如实报告检索轨迹即止。

## W5 校验扩展契约（hy3）

validate_edges.py 增加三个子命令模式（不破坏现有 edges/nodes/truth 功能，零回归）：
`--check-flows flows/out/flows-seed.json`（字段齐全/占比字符串/warnings数组）、
`--check-catalog flows/out/catalog.csv`（9列/URL列http校验/抓取日期格式）、
`--check-linkage flows/out/linkage.csv`（10列/出口相关性枚举{直接,间接,无}/锚点非空）。
自测跑现有三个文件并打印结果；旧模式回归（output/edges.csv PASS 不变）。

## 终验线（W6，Claude）

- W1：结构断言+我亲验双层切换与迁移呈现；W2：抽 3 条 linkage 反查锚点；
- W3：升级成功的行亲访新 URL；W4：数字抽检对 PDF 原文（若取到）；
- W5：新旧模式各跑一遍零回归；
- 海关 2025：等用户在场滑块一次，按既定 URL 工艺采集归档。
