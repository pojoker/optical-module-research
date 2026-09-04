# 海关月度量价通道说明

- 抓取日期：2026-07-23
- 验证状态：v1.1管线产出-未人工复核
- 主站：`http://stats.customs.gov.cn`
- 请求区间：`2024-01` 至 `2026-07`
- 服务端有效截止月：未取得（入口页被拦截）
- 请求 HS 编码：`85177950,85176229`
- 实得月份数：0
- 实得编码：无
- CSV 数据行数：0

## 结论

通道未打通：English query form / metadata: WAF JavaScript challenge; X-Via-JSL='68ec4ad,-'

`customs-monthly.csv` 只有表头时，不代表相关商品出口为零；只代表本次没有从官方查询接口取得可核验数据。

## 编码口径

- `85177950`：光通信设备的激光收发模块（首选、最精确）。
- `85176229`：其他光通讯设备（较宽口径，可能包含非模块设备）。
- `85177990`：税目8517设备用其他零件（更宽，不作为默认抓取项）。
- 任务示例中的 `85176230/85177090` 不是 2024 年官方税则附件中对应的现行 8 位光收发号列，因此没有把示例直接当成查询事实。

编码核验来源：

- [2024税则公告](https://gss.mof.gov.cn/gzdt/zhengcefabu/202312/t20231229_3924577.htm)
- [2024官方税率附件（列出85176229、85177950、85177990）](https://gss.mof.gov.cn/gzdt/zhengcefabu/202404/P020240419426389451413.pdf)
- [2026官方税率附件（用于检查编码延续）](https://gss.mof.gov.cn/gzdt/zhengcefabu/202603/P020260326610286964491.pdf)

## 探测轨迹

### 1. English query form / metadata

- URL：`http://stats.customs.gov.cn/queryDataForEN/queryDataByWhereEn`
- 参数：无
- HTTP：412
- Content-Type：`text/html; charset=utf-8`
- 返回摘要：WAF JavaScript challenge; X-Via-JSL='68ec4ad,-'

### 2. easy query page (.htm)

- URL：`http://stats.customs.gov.cn/easyquery.htm`
- 参数：无
- HTTP：412
- Content-Type：`text/html; charset=utf-8`
- 返回摘要：WAF JavaScript challenge; X-Via-JSL='b8801a4,-'

### 3. easy query page (.html)

- URL：`http://stats.customs.gov.cn/easyquery.html`
- 参数：无
- HTTP：412
- Content-Type：`text/html; charset=utf-8`
- 返回摘要：WAF JavaScript challenge; X-Via-JSL='d048423,-'

### 4. result API diagnostic request (metadata values are placeholders)

- URL：`http://stats.customs.gov.cn/queryDataForEN/queryDataListEn?codeLength=8&currentStartTime=202401&currentEndTime=202607&currentDateBySource=202607&pageSize=100&selectTableState=1&currencyType=usd&year=2024&startMonth=1&endMonth=1&outerField1=CODE_TS&outerValue1=85177950%2C85176229&outerField2=ORIGIN_COUNTRY&outerValue2=&outerField3=TRADE_MODE&outerValue3=&outerField4=TRADE_CO_PORT&outerValue4=&monthFlag=1&pageNum=1&orderType=CODE+ASC+DEFAULT&iEType=0`
- 参数：`{'codeLength': '8', 'currentStartTime': '202401', 'currentEndTime': '202607', 'currentDateBySource': '202607', 'pageSize': '100', 'selectTableState': '1', 'currencyType': 'usd', 'year': '2024', 'startMonth': '1', 'endMonth': '1', 'outerField1': 'CODE_TS', 'outerValue1': '85177950,85176229', 'outerField2': 'ORIGIN_COUNTRY', 'outerValue2': '', 'outerField3': 'TRADE_MODE', 'outerValue3': '', 'outerField4': 'TRADE_CO_PORT', 'outerValue4': '', 'monthFlag': '1', 'pageNum': '1', 'orderType': 'CODE ASC DEFAULT', 'iEType': '0'}`
- HTTP：412
- Content-Type：`text/html; charset=utf-8`
- 返回摘要：WAF JavaScript challenge; X-Via-JSL='8fcc560,-'

### 5. retired IP mirror named in task

- URL：`http://43.248.49.97/`
- 参数：无
- HTTP：502
- Content-Type：``
- 返回摘要：(empty body)

## 替代路径

- 在可正常打开该站点的人工浏览器中访问 `http://stats.customs.gov.cn/queryDataForEN/queryDataByWhereEn`，通过正常页面查询并导出；若出现验证码，按站点规则人工处理。
- 若需要自动复跑，可在站点不再对 requests 返回 412 后直接运行本脚本；脚本已固化公开表单的真实参数格式。
- [`43.248.49.97` 已由海关总署 2023 年第6号公告宣布停止使用](http://www.customs.gov.cn/customs/302249/302266/302267/4835768/index.html)，本次仅按任务要求保留一次探测，不应再作为生产镜像。

## 终验补记（Claude 浏览器复试，2026-07-23）

在真实浏览器（非 requests）中复试：主页与 EN 查询页均白屏；网络面板显示
412（WAF JS 挑战）→ 挑战 JS 加载 200 → 重试查询页 400 Bad Request ×2。
结论：当前该站对本环境整体不可达，与 codex 探测一致，非脚本层问题。
通道状态：**未打通（诚实失败）**，进观察名单。复试条件：更换网络环境/工作时段
人工浏览器访问；打通后 fetch_customs.py 参数已就绪可直接复跑。
未触发验证码；未尝试任何反爬绕行。

## 终验补记2（HTTP假设检验，2026-07-23）

用户提示该站仅有 HTTP——假设成立且重要：https 侧只有代理 CONNECT 应答（源站
无有效 TLS），任何静默升级 HTTPS 的工具（如 WebFetch）在此站必失败。
浏览器复试确认 scheme 全程保持 http；WAF 加速乐挑战在真实浏览器中**已通过**
（412 消失、clearance cookie 建立），但其后 /queryData、/queryDataForEN、
/indexEn 全部 400 Bad Request 或空体。
**精确诊断**：不是 HTTPS 升级问题（已排除）、不是 JS 挑战问题（已通过），是
应用层对本环境出口 IP/地域的策略拒绝。复试条件收窄为：更换网络出口（境内
IP/非数据中心 IP）后人工浏览器访问；届时 http 明文 + fetch_customs.py 参数
即插即用。

## 通道打通实录（2026-07-23，用户 Chrome + Claude 协同）

**最终工作流程**（通道状态：**已打通**，人机协同模式）：
1. 用户真实 Chrome（claude-in-chrome 扩展）访问 http://stats.customs.gov.cn/queryData/queryDataByWhere —— 真实浏览器指纹过 WAF；无头 Chromium（gstack browse/Playwright）确认被应用层拒绝（400）
2. 表单填写可由 Claude 驱动（form_input/点击）；**验证码（滑块拼图）必须用户亲手完成**——纪律红线，且实测放行是"每次查询"级不是会话级，纯改 URL 参数不触发数据加载
3. 查询结果页 queryDataList 的 URL 携带全部查询参数（year/startMonth/outerField1-4/outerValue1-4/iEType/currencyType）——同一次放行内的翻页/导出可自动化
4. "导出数据"按钮直接落 CSV 到 ~/Downloads（GBK 编码，金额千分位），比翻页抓取可靠

**已采集数据**（flows/input/ 原始件 + flows/out/ 聚合件）：
- 2024 全年月度（RMB+USD 双版直查）
- 2025 年 1 月四维分拆（伙伴×方式×注册地，804 行，RMB）
- 2026 年 1-6 月四维分拆（5011 行，USD）
- **缺口如实声明：2025 年 2-12 月未采**（需一次用户滑块配合，随时可补）

**关键口径**：HS 85177950 计量单位为千克（无只数第二计量），均价只能做 $/kg；
四维分拆聚合与单维直查在 2024/202501 交叉点未做对账（2025-01 两种口径来自不同币种文件）。

**首批发现**（数据 A 级 / 归因 C 级分离）：
- 2026H1 出口月度 $4.99亿→$7.11亿 加速（数据）
- 去向结构迁移：202501 美国第一（¥13.9亿/月）→ 2026H1 马来西亚第一（$14.3亿/半年）、
  美国跌至第四（数据）；归因（关税/东南亚封测中转）为 C 级推断，不承重

## 2025 缺口补齐（v1.2 W6，2026-07-23 用户滑块一次）

2025 全年四维分拆（10112 行）已采，customs-monthly 升至 30 月（202401-202606 连续），
customs-partners 升至 2881 行。工艺同前：Claude 填表→用户滑块一次→URL 导出。

**观测窗内首次交叉（月度美国 vs 马来西亚，百万美元；红队 Y1-F13 修正命名）**：
- 2025-01 美国 $194M（第一）
- **2025-04 马来西亚 $123M 首次超过美国 $95M**（观测内交叉点，非"产业迁移拐点"）
- 2025-12 美国 $0M / 马来 $253M
- 2026-06 美国 $62M / 马来 $260M
数据（A级）：这是现有 2025-01—2026-06 国别月度序列内的首次交叉，其后 14 个月马来
持续领先（交叉具持续性）。边界：2024 无同维度国别底稿，不能称"历史首次"；月度交叉
可由报关/库存/价格/一次性发运造成；归因产能迁移（对美关税/东南亚封测扩产）为 C 级
推断，不承重。

## 进口侧采集（v1.3 X6，2026-07-23 用户滑块一次）

**首次进口通道打通**：进口方向(iEType=1)×三码(85414900光敏半导体/85177950模块/
85177990零件)×贸易伙伴×贸易方式，2024全年分月，4462行。归档
flows/input/customs-import-3codes-2024-usd.csv。工艺同出口：填表→用户滑块→导出。

**2024 进口总额（百万美元，数据A级=海关金额；口径解释见下）**：
- 85177990零件 $3207M（**口径坑：8517所有设备零件，非光模块专用，不可直接当"光模块零件进口"，仅作上限参考**）
- 85414900 $1427M（**税则名"其他光敏半导体器件"，宽口径，含激光二极管/光电探测器
  及光伏/传感/工业等其他用途器件；无十位码或申报要素拆分，只能作光模块相关上游的
  混合口径参考——红队 Y1-F14**）
- 85177950整模块 $853M

**上游依赖·混合口径参考（85414900，海关金额A级 / 归因边界见注）**：
- 全口径来源：中国22%/泰国20%/日本18%/台湾13%/马来9%/菲律宾6%/瑞士3%/美国2%/韩2%/德1%
- 贸易方式拆分：$1427M 中一般贸易 $782M、海关特殊监管+进料加工 $599M。
  **红队 Y1-F15 纠正**：贸易方式与来源地描述的是采购路径，不能识别技术产权来源，
  也不能区分晶圆制造与封测——一般贸易同样可采购封测成品/贸易商货/跨国公司境外
  工厂产品。原"真正技术源头=日+台+瑞+美+德"名单**删除**（且该名单跳过了一般贸易
  来源前两名中国 $216.8M、泰国 $152.8M，与自身筛选规则冲突）。可保留的事实：
  一般贸易来源前列为中国/泰国/台湾/日本，各自占比见 customs-trademode.csv。
- 整模块85177950进口 $853M 中泰国 $320M 居首。**红队 Y1-F16 纠正**：数据只含
  国别×贸易方式、无企业与交易对手，泰国进口不能归因单一企业；与 Fabrinet 泰国
  业务仅方向相容，不构成"Fabrinet 回流"或"钱货闭环"（且 2024 泰国进口与
  2025-2026 江苏→马来出口非同年同向，不成镜像）。

**缺口如实声明**：进口仅采2024一年（2025/2026待后续滑块）；85177990/85414900 口径过宽未细分。
