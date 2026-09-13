# 海外详情访问与发布日期：43条拒收的定点复核

核验日期：2026-09-10。基线是 2026-09-09 最终 failures.csv；窗口为 2026-08-26 至 2026-09-09，含两端。当前代码已同步至主项目，未重跑全池、未覆盖过去日报或采集状态。

访问方法与日期抽取都需要改。旧“格式拒收”43条的直接错误全部是 `published_at is required`：程序未提取出发布日期，并不表示43个网站打不开，也不表示内容本身无效。

| 旧拒收来源 | 数量 | 本次核验与处理 |
|---|---:|---|
| OpenLight | 8 | 8个网页自身发布日期；标题截断导致JSON-LD绑定失败，已修 |
| EVG | 3 | 2个发布稿日期可读；1个仍缺明确发布日期 |
| Semtech | 7 | 5个同文章卡片日期；2个分页链接应排除 |
| Source Photonics | 6 | 5个发布稿日期可读；1个同篇年份冲突保留未知 |
| SUSS | 9 | 9个文章标题区发布时间，已补解析 |
| TE Connectivity | 10 | 普通浏览器核验9个明确Published字段；1个旧产品页面无该字段。当前HTTP403，自动访问尚未恢复 |

合计38条有可归属于文章的日期：24条来自本次HTTP详情全文，5条来自官网同URL列表卡片，9条来自普通浏览器可见DOM。38条均在原窗口之外，范围为2025-04-01至2026-08-20。另2条分页、3条未知/冲突/不适用。38是日期核验数，不能写成新增38条或自动抓取修复38条；其中9条仍依赖浏览器取证。

## 具体页面为什么被拒收

- [OpenLight与Advantest合作](https://openlightphotonics.com/newsroom/advantest-partners-with-openlight-to-develop-silicon-photonics-test-solutions-for-high-volume-manufacturing)：网页内有datePublished=2026-06-23，但分享用og:title被截断，旧代码要求标题一致而读不到日期。改用完整h1校验，同时要求JSON-LD显式URL属于该文章。
- [SUSS的Ameriprise投票权披露](https://www.suss.com/en/news/voting-rights/ameriprise-financial-inc.-wilmington-delaware-united-states-of-america-usa6)：标题上方有Jul 6, 2026 18:00:04，旧模板只认识另一类EQS文案。现在读取本篇article-header内唯一时间，不借网站通用页头日期。
- [EVG与Xanadu合作](https://www.evgroup.com/company/news/detail/xanadu-and-ev-group-partner-to-build-industrial-scale-photonic-quantum-hardware)：发布稿开头是Toronto, ON及May 5th, 2026；旧规则没覆盖这类发布行及序数词。已识别为2026-05-05。
- [TE COMPUTEX页面](https://www.te.com/en/about-te/news-center/computex-2026.html)：明确Published为05/27/26，正文另有June 1, 2026。采集窗口使用2026-05-27这一页面日期，不把正文其他日期覆盖到Published上。
- [Source Photonics的OFC 2026获奖页面](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-announce-to-receive-two-industry-awards-for-two-product-families-during-ofc26/)：发布时刻行写March 16, 2026，紧接的发布稿开头却写March 16, 2025。两个同类日期矛盾，继续保留未知，未猜测哪个年份正确。
- [EVG与NTT-AT的SmartNIL页面](https://www.evgroup.com/company/news/detail/ntt-at-and-evg-demonstrate-the-feasibility-of-applying-high-refractive-index-resins-to-ar-optical-devices-using-the-srrartnilr-process)：页面有CIOE展会日程与带日期的图片路径，但都不足以确定发布时间，继续待核验。

OpenLight有4条本公司站内媒体摘要，其页面日期仅代表OpenLight的页面发布，不代表外部媒体原文发布日或独立证据。Tower PH18DA页面的datePublished=2026-08-11，正文另有含义不明的07 09 2026；只读取明确的页面datePublished，未解释正文数字或推定事件时间。TE旧AMP charging页面标记Featured Product，无Published字段，正文January 29th 2021未用来伪造页面发布时间。

## 详情访问为什么失败，改了什么

原10条详情失败由以下事故组成，并不是10个不同站点：

| 旧记录 | 根因证据 | 本次处理与边界 |
|---|---|---|
| AAOI 1条 | Logo的home链接被当作文章，产生404 | 排除home导航，保留真实仅含图片的文章链接 |
| ASMPT、Accton、Sicoya共6条 | 3次端点预算耗尽，每次又记详情和列表解析两条 | 直接返回已完成文章，消除同次预算耗尽的重复错误记录 |
| Scintil 3条 | HTTP429 | 429后停止该端点本批其余文章，保留Retry-After。单篇当前200不能证明持续恢复；未新增跨批冷却调度 |

ASMPT、Accton、Semtech原来先抓前20个详情，再判断日期，预算会花在旧页面和分页上。现在从已核模板读取逐篇卡片日期，在请求详情及截取数量之前过滤窗口；未知日期仍要取详情，不能当成过期排掉。

三站保存的列表有92、80、10个链接记录，其中日期已知为90、80、10个；套用现有端点文章路径和窗口后，详情请求仅2、1、2个。ASMPT保留两条无卡片日期的真实详情入口。没有扩大Accton既有月报入口到其他披露类别。

TE本次普通HTTP请求10/10返回403，普通浏览器10/10能打开，无登录或挑战操作。这是已证实的访问方式差异；日期解析已补，但浏览器访问尚未接入定时任务。Sicoya本次入口403，不能验证其文章日期布局。未绕过访问控制或轮换身份。

## 修复后看到的结果

- ASMPT定点联网：13.53秒，列表加2个详情，窗口内0条，详情错误0。
- Accton定点联网：7.47秒，列表加1个详情，窗口内1条，详情错误0。8月营收报告的页面发布日期是2026-09-07，不能用报告所属月份代替。
- Semtech首次联网：6.12秒成功拿到列表及2篇详情，但旧日期优先级把它们排出了窗口。官网列表标注2026-09-08，两篇正确正文的发布稿日期均为2026-08-25，属于不同日期口径。
- 修复后的完整原始网页回放：正确返回2篇，published_at=2026-09-08，另保留detail_date_observed=2026-08-25；两种日期和含义进入已有披露备注字段。两篇为[10G PON芯片组](https://www.semtech.com/company/press/semtech-delivers-10g-pon-chipset-for-triple-generation-50g-olt-modules)和[224G光连接](https://www.semtech.com/company/press/semtech-sets-bar-for-224g-optical-connectivity)。这2篇不属于原43条拒收清单。
- Semtech后续联网复测仍不稳定：一轮60秒预算耗尽、0条；最后一次限25秒预算的复测在16.02秒以列表超时结束。日期逻辑验证通过，实时访问恢复未通过；未把回放结果算进正式日报。

253项calls测试及 `python -m calls check` 通过；测试覆盖36个真实页面的精简样本、卡片逐URL日期绑定、年份切换、窗口先筛再截取、日期冲突拒收、429停止并保留已完项。26个本次HTTP详情全文实际回放得到24个日期及2个未知，与精简样本一致。独立审阅未发现阻断问题。

本次只改calls/http_discovery.py、三份新测试/样本、calls/README.md及控制/核验文档。24份根级及calls canonical文件前后SHA-256一致，promoted=0。未提交、推送、发布，未改写过去的70条披露候选快照。

仍待处理：TE定时采集的访问方式、Sicoya403、Scintil跨批退避与实际限流频率、Semtech间歇超时、3个日期未决页面。既有事件候选仍以披露日期分组并填入候选时间；页面日期不证明事件发生日，本次没有重构该模型，正式采纳事件前须单独核对日期。

## 43条逐项记录

“窗口外”表示日期可确定且不在本次日报区间；浏览器核验并不表示HTTP任务已恢复。

| 来源 | 页面 | 核验日期 | 证据取得方式 | 处置 |
|---|---|---|---|---|
| OPENLIGHT | [Advantest Partners with OpenLight to Develop Silicon Photonics Test…](https://openlightphotonics.com/newsroom/advantest-partners-with-openlight-to-develop-silicon-photonics-test-solutions-for-high-volume-manufacturing) | 2026-06-23 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [Electro Optics: OpenLight showcased 400G-per-lane III-V silicon…](https://openlightphotonics.com/newsroom/electro-optics-openlight-showcased-400g-per-lane-iii-v-silicon-photonics-at-ofc-2026) | 2026-04-09 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [IEEE Journal: Adam Carter discusses success in 3D PIC design,…](https://openlightphotonics.com/newsroom/ieee-journal-of-selected-topics-in-quantum-electronics) | 2026-05-19 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [Lightwave: OpenLight pushes photonic integration as AI networks drive…](https://openlightphotonics.com/newsroom/lightwave-openlight-pushes-photonic-integration-as-ai-networks-drive-optical-scaling) | 2026-04-02 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [OpenLight and Tower Semiconductor Expand PH18DA Photonics Ecosystem…](https://openlightphotonics.com/newsroom/openlight-and-tower-semiconductor-expand-ph18da-photonics-ecosystem-to-accelerate-photonic-ic-development) | 2026-08-11 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [OpenLight Secures $50 Million in Series A-1 Funding to Accelerate…](https://openlightphotonics.com/newsroom/openlight-secures-50-million-in-series-a-1-funding-to-accelerate-global-deployment-of-next-generation-photonics) | 2026-04-28 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [OpenLight to Highlight Heterogeneous Silicon Photonics at Four Key…](https://openlightphotonics.com/newsroom/openlight-to-highlight-heterogeneous-silicon-photonics-at-four-key-global-industry-events) | 2026-08-20 | HTTP详情全文 | 窗口外 |
| OPENLIGHT | [Solving the heat problems: How silicon photonics is redefining…](https://openlightphotonics.com/newsroom/solving-the-heat-problems-how-silicon-photonics-is-redefining-thermal-efficiency-in-data-centers) | 2026-03-27 | HTTP详情全文 | 窗口外 |
| EVG | [Imec and EV Group demonstrate wafer-to-wafer hybrid bonding with 200nm interconnect pitch and rec…](https://www.evgroup.com/company/news/detail/imec-and-ev-group-demonstrate-wafer-to-wafer-hybrid-bonding-with-200nm-interconnect-pitch-and-record-high-overlay-accuracy) | 2026-05-28 | HTTP详情全文 | 窗口外 |
| EVG | [NTT-AT and EVG Demonstrate the Feasibility of Applying High-Refractive-Index Resins to AR Optical…](https://www.evgroup.com/company/news/detail/ntt-at-and-evg-demonstrate-the-feasibility-of-applying-high-refractive-index-resins-to-ar-optical-devices-using-the-srrartnilr-process) | 未知/不适用 | HTTP详情全文 | 发布时间未知 |
| EVG | [Xanadu and EV Group partner to build industrial-scale photonic quantum hardware](https://www.evgroup.com/company/news/detail/xanadu-and-ev-group-partner-to-build-industrial-scale-photonic-quantum-hardware) | 2026-05-05 | HTTP详情全文 | 窗口外 |
| SMTC | [P10](https://www.semtech.com/company/press/P10) | 未知/不适用 | HTTP官网列表 | 分页排除 |
| SMTC | [P20](https://www.semtech.com/company/press/P20) | 未知/不适用 | HTTP官网列表 | 分页排除 |
| SMTC | [Semtech Announces First Quarter of Fiscal Year 2027 Conference Call](https://www.semtech.com/company/press/semtech-announces-first-quarter-of-fiscal-year-2027-conference-call) | 2026-05-13 | HTTP官网逐篇卡片 | 窗口外 |
| SMTC | [Semtech Announces First Quarter of Fiscal Year 2027 Results](https://www.semtech.com/company/press/semtech-announces-first-quarter-of-fiscal-year-2027-results) | 2026-05-26 | HTTP官网逐篇卡片 | 窗口外 |
| SMTC | [Semtech Announces Second Quarter of Fiscal Year 2027 Conference Call](https://www.semtech.com/company/press/semtech-announces-second-quarter-of-fiscal-year-2027-conference-call) | 2026-08-11 | HTTP官网逐篇卡片 | 窗口外 |
| SMTC | [Semtech Corporation to Host Data Center Teach-in Event on Oct. 15, 2026](https://www.semtech.com/company/press/semtech-corporation-to-host-data-center-teach-in-event-on-oct-15-2026) | 2026-08-17 | HTTP官网逐篇卡片 | 窗口外 |
| SMTC | [Semtech Expands LoRa Plus™ Family: LR2022 and LR2012 Now in Production](https://www.semtech.com/company/press/semtech-expands-lora-plus-family-lr2022-and-lr2012-now-in-production) | 2026-08-19 | HTTP官网逐篇卡片 | 窗口外 |
| SOURCEPHOTONICS | [Source Photonics and Delta Electronics Join Force to demo 1.6T Transceiver and Switch Products at…](https://www.sourcephotonics.com/news/source-photonics-and-delta-electronics-join-force-to-demo-1-6t-transceiver-and-switch-products-at-ofc26/) | 2026-03-17 | HTTP详情全文 | 窗口外 |
| SOURCEPHOTONICS | [Source Photonics Announce the Product Availability of its 200G per Lane based 1.6T and 800G PAM4 …](https://www.sourcephotonics.com/news/source-photonics-announce-the-product-availability-of-its-200g-per-lane-based-1-6t-and-800g-pam4-transceiver-family-products-at-ofc25/) | 2025-04-01 | HTTP详情全文 | 窗口外 |
| SOURCEPHOTONICS | [Source Photonics Announce to Receive Industry Awards for Two Product Families at 2025 Lightwave+B…](https://www.sourcephotonics.com/news/source-photonics-announce-to-receive-industry-awards-for-two-product-families-at-2025-lightwavebtr-innovation-reviews-duing-ofc25/) | 2025-04-01 | HTTP详情全文 | 窗口外 |
| SOURCEPHOTONICS | [Source Photonics to Spotlight its Latest Optical Innovations & Announce to Receive Two Industry A…](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-announce-to-receive-two-industry-awards-for-two-product-families-during-ofc26/) | 未知/不适用 | HTTP详情全文 | 同篇年份冲突 |
| SOURCEPHOTONICS | [Source Photonics to Spotlight its Latest Optical Innovations at ECOC 2025](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-at-ecoc-2025/) | 2025-09-26 | HTTP详情全文 | 窗口外 |
| SOURCEPHOTONICS | [Source Photonics Unveil the Tri-mode 50G PON OLT SFP-DD Optical Transceivers with Live Demonstrat…](https://www.sourcephotonics.com/news/source-photonics-unveil-the-tri-mode-50g-pon-olt-sfp-dd-optical-transceivers-with-live-demonstration-during-ofc25/) | 2025-04-01 | HTTP详情全文 | 窗口外 |
| SUSS | [Ameriprise Financial, Inc., Wilmington, Delaware, United States of America (USA)](https://www.suss.com/en/news/voting-rights/ameriprise-financial-inc.-wilmington-delaware-united-states-of-america-usa6) | 2026-07-06 | HTTP详情全文 | 窗口外 |
| SUSS | [JANUS HENDERSON GROUP Ltd, St. Helier, Jersey](https://www.suss.com/en/news/voting-rights/janus-henderson-group-ltd-st.-helier-jersey) | 2026-08-12 | HTTP详情全文 | 窗口外 |
| SUSS | [JANUS HENDERSON UK (HOLDINGS) LIMITED, London, United Kingdom](https://www.suss.com/en/news/voting-rights/janus-henderson-uk-holdings-limited-london-united-kingdom) | 2026-08-12 | HTTP详情全文 | 窗口外 |
| SUSS | [Kempen Oranje Participaties N.V., Amsterdam, Netherlands](https://www.suss.com/en/news/voting-rights/kempen-oranje-participaties-n.v.-amsterdam-netherlands2) | 2026-06-25 | HTTP详情全文 | 窗口外 |
| SUSS | [T. Rowe Price Group, Inc., Baltimore, Maryland, United States of America (USA)](https://www.suss.com/en/news/voting-rights/t.-rowe-price-group-inc.-baltimore-maryland-united-states-of-america-usa) | 2026-07-17 | HTTP详情全文 | 窗口外 |
| SUSS | [UBS Group AG, Zurich, Switzerland](https://www.suss.com/en/news/voting-rights/ubs-group-ag-zurich-switzerland13) | 2026-07-22 | HTTP详情全文 | 窗口外 |
| SUSS | [UBS Group AG, Zurich, Switzerland](https://www.suss.com/en/news/voting-rights/ubs-group-ag-zurich-switzerland14) | 2026-07-23 | HTTP详情全文 | 窗口外 |
| SUSS | [Universal-Investment-Gesellschaft mit beschränkter Haftung, Frankfurt am Main, Germany](https://www.suss.com/en/news/voting-rights/universal-investment-gesellschaft-mit-beschraenkter-haftung-frankfurt-am-main-germany) | 2026-08-14 | HTTP详情全文 | 窗口外 |
| SUSS | [Van Lanschot Kempen Investment Management N.V., Amsterdam, Netherlands](https://www.suss.com/en/news/voting-rights/van-lanschot-kempen-investment-management-n.v.-amsterdam-netherlands) | 2026-06-25 | HTTP详情全文 | 窗口外 |
| TEL | [TE News: TE Connectivity launches 56G MezzaWave connectors and cable assemblies](https://www.te.com/en/about-te/news-center/56g-mezzawave.html) | 2026-03-16 | 普通浏览器可见DOM | 窗口外 |
| TEL | [Featured Product: Next Generation AMP+ Charging Inlets](https://www.te.com/en/about-te/news-center/amp-charging-cables-and-inlets-next-gen-npi.html) | 未知/不适用 | 普通浏览器可见DOM | 无Published的产品页 |
| TEL | [TE News: Powering next generation AI data centers at COMPUTEX 2026](https://www.te.com/en/about-te/news-center/computex-2026.html) | 2026-05-27 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: Embedded World 2026](https://www.te.com/en/about-te/news-center/embedded-world-2026.html) | 2026-02-25 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: HENN Connector](https://www.te.com/en/about-te/news-center/henn-connector-group.html) | 2026-08-04 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: Next2OEM](https://www.te.com/en/about-te/news-center/next2oem.html) | 2026-01-29 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: Phoenix Contact](https://www.te.com/en/about-te/news-center/phoenixcontact.html) | 2026-02-28 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: TE Connectivity introduces 3D printing process to streamline catheter manufacturing](https://www.te.com/en/about-te/news-center/propelus-prototyping-3d-printing-process.html) | 2026-07-27 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: TE Connectivity to acquire advanced power solutions leader Astrodyne TDI](https://www.te.com/en/about-te/news-center/te-connectivity-acquisition-astrodyne.html) | 2026-07-23 | 普通浏览器可见DOM | 窗口外 |
| TEL | [TE News: Advancing end-to-end optical infrastructure for next-generation AI data centers at OFC 2026](https://www.te.com/en/about-te/news-center/te-ofc-2026.html) | 2026-03-13 | 普通浏览器可见DOM | 窗口外 |

## 证据与可复核结果

- [逐项JSON](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910/case-results.json)
- [原始HTTP/浏览器证据目录](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910)
- [Semtech完整网页回放](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910/SMTC_OFFICIAL_RELEASES-captured-page-replay.json)
- [Semtech最后联网复测](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910/SMTC_OFFICIAL_RELEASES-bounded-live-retest.json)
- [主项目文件集成校验](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910/integration.json)
- [canonical前后校验](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260910/canonical-after.json)
