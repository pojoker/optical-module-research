# 国内与海外日更修复及实跑结果（2026-09-09）

状态：本轮修复、两路真实运行、校验和日报合并已结束；采集仍为partial，组装complete。下列全量结果保留实际快照，不把后续AMZN单点补测冒充全量复跑。

## 修复前实况

- 国内：当日日报缺失；06:49:48 遗留 running，7/188 实为两个投关列表和五家公司问答。进程未正常收尾的具体原因未知。
- 海外：81 个归一主体仅7个有配置、8端点；成功3、失败5，74主体缺端点；2披露候选、1主张、0事件。采集与组装均partial。

## 已实施

1. 国内：默认每公司问答60秒墙钟预算；记录请求、公司、页码、PID和完整错误；SIGTERM/中断明确failed；成功QA检查点按日期、输入与代码指纹恢复。P5W从page0开始；失败前已落盘的部分问答保留为候选，不推进失败水位；主通道0且兜底不可用不再冒充成功零条。
2. 海外：完整JSON对象日期解析，工具页/日历/导航排除；公开Q4、Cisco内嵌数据适配；单次请求15秒、端点60秒预算，有限瞬时重试；采集不完整退出2并打印PARTIAL；无效JSON不能冒充健康空结果。
3. 覆盖与归属：IQE/Cisco自身公告可形成自身第一方候选；独立佐证必须基于具体引语明确目标，发行者自身动作及含混归属保留待审。修复customer sampling漏判和经营性demonstrated误判；增加真实官方列表、原稿托管源与窄站点日期模板。
4. 配置：78/81主体、79端点（39季度、32事件监控、7候选）。剩Freiberger、Polariton、Xscape明确缺口，配置数不代表采集成功或结论覆盖。

## 验证记录

- 国内最终45项测试通过。
- 海外最终完整calls测试238项通过；日报合并18项通过。
- 项目账本不变量、render --verify、participation --check、calls check通过；机器门不代表领域问题被回答。
- 主代理两次主动SIGTERM停止过渡验证运行以集成实跑发现的补修；均写出failed/interrupted和原因。此为主动验证，不与早晨未知中断混同。
- 第二阶段原7主体8端点实跑：成功6、失败2；4披露、5主张、0事件；verify通过，promoted=0。该中间快照已备份，不能充当最终扩池结果。

## 本次范围

仅本地代码、端点配置、测试、说明及仓库外状态。未授权也未实施canonical晋升、Git提交/推送、网页发布。原有网页和其他用户改动未纳入本次修改。

## 最终实跑

国内最终运行于23:06:14结束，651/651流程计数（2投关列表+93QA公司+93公告公司+463月筛对象；月筛实际checked=0、unresolved=463，计数不表示采集成功），退出1、状态partial；已生成日报。投关新增10份、问答增量116条、关注公告10条；失败来源中仍保留67条新增问答，失败水位不推进。70家公司QA失败：24个P5W第20页重复截断、42个因同一次P5W SSL错误触发的兜底不可用/熔断（不是42次独立连接失败）、4个上证接口SSL错误。另1项月度重筛因p_stock2110要求token返回401；总71项失败。这些公开源及凭证限制仍在，不得描述为全部抓取成功。

海外第一次扩池全量：79端点请求层成功53、失败26，51披露/31主张/23事件/31证据候选，0晋升；99条缺日期、13文章获取失败、6入口获取失败、20列表不支持、3主体缺端点。请求层成功不等于日期正文均合格。verify通过，快照另存backups/repair-20260909-overseas-expanded-first。实跑发现的官方API、目录过滤、窄日期和解析预算问题正在补修，最终复跑待填。

24份canonical账本目前逐个SHA-256与开工前一致。


## 最终全量与剩余缺口

| 指标 | 修复前7主体运行 | 首次扩池 | 最终全量 |
|---|---:|---:|---:|
| 已配置主体/81 | 7 | 78 | 78 |
| 端点数 | 8 | 79 | 79 |
| 请求层成功/失败 | 3/5 | 53/26 | 70/9 |
| 有效披露候选 | 2 | 51 | 70 |
| 主张/事件/证据候选 | 1/0/0 | 31/23/31 | 35/27/35 |
| 缺日期条目 | 未作同口径统计 | 99 | 43 |
| 晋升 | 0 | 0 | 0 |

最终全量退出2、partial；79端点中59个未报告采集或条目错误，20个仍有至少一项失败。70个请求层成功并不代表70个端点内容完整；未报告错误也不等于穷尽历史新闻。默认14天窗口、每端点最多20条文章、60秒预算，结果是有限切片。

- 9个入口层失败：HPE/Molex/PI列表不支持；Coherent404；Avicena/Ayar403；Ennostar证书链校验失败；LWLG未知JSON；AMZN单条跨域记录拖累全批（后续已单独修复，见下）。
- 43个缺日期条目分布：TEL10、SUSS9、OpenLight8、Semtech7、Source Photonics6、EVG3。窄模板修复仍未覆盖这些文章，不将测试通过表述为日期问题全部解决。Source Photonics至少一篇页头2026与电头2025冲突，继续待确认。
- 10项文章层失败：AAOI误选home链接404；ASMPT、Accton、Sicoya预算耗尽及收尾记录；Scintil3次429。保留部分结果，不推进为完整成功。
- 3个主体仍缺可用端点：Freiberger、Polariton、Xscape。AAOI目前为newsroom切片、Accton为月报切片，不代表财报或全部技术新闻完整。
- 国内剩余71项失败见上，月筛需有效token；不能把失败公司或月筛对象称为全部覆盖。

全量后AMZN最小补修：Q4逐项拒绝外域链接、PDF和坏结构，合法同域文章继续保留。隔离核验20条中17条同域HTML合法、3条拒绝；主仓库按近一年窗口补测保留8条，近14天合法0，仍partial。最终合并日报保留补修前真实全量快照，未手工篡改计数；单点验证另存仓库外 repair-20260909-amzn-followup.json。

最终verify通过；combined组装complete、采集partial。24份canonical文件SHA-256与开工前逐一相同；45+238+18项针对性测试、四项机器门和diff check通过。没有Git提交、推送、发布，也没有晋升研究事实。

结果文件：
- [合并日报](/Users/jowang/Downloads/workflow-rehearsal-daily-state/combined/daily/2026-09-09.md)
- [海外全量计数](/Users/jowang/Downloads/workflow-rehearsal-daily-state/overseas/staging/2026-09-09/run-summary.json)
- [海外失败清单](/Users/jowang/Downloads/workflow-rehearsal-daily-state/overseas/staging/2026-09-09/failures.csv)
- [国内最终状态](/Users/jowang/Downloads/workflow-rehearsal-daily-state/domestic/run-status.json)
- [AMZN独立补测](/Users/jowang/Downloads/workflow-rehearsal-daily-state/repair-20260909-amzn-followup.json)
