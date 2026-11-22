# 全景网日期筛选修复与华工科技验证

2026-09-11。华工科技原先的重复翻页报错涉及采集逻辑错误：程序未带官网日期筛选参数，也未按响应的 `total` 停止分页。之前只解释为“网站第20页重复”没有解释到原因。

## 官网实际行为

- [华工科技问答页面](https://ir.p5w.net/c/000988/questionlist.shtml)提供时间筛选。页面实际加载的 [companyMoreQuestion.js](https://ir.p5w.net/resources/js/company/companyMoreQuestion.js?v=20260520) 将表单发往 `POST https://ir.p5w.net/interaction/getNewR.shtml`。
- 请求参数为 `companyBaseinfoId`、`isPagination=1`、`page=0` 起算、`rows=10`、`questionerTimeBegin`、`questionerTimeEnd`。查询结果上限为100条；`total=100`不能证明历史只有100条。
- 浏览器和接口均验证：华工科技筛选2026-08-29至2026-09-11，返回0条；筛选2026-08-07当天，返回69条，分7页。
- 日期筛选针对**提问时间**。富士达（920640）问答 `e74db67b4a7349109254932cf57b3a7b` 提问于2026-05-19 14:18:52，回复于2026-05-20 16:17:23。筛选5月19日返回这条；筛选5月20日的首屏未返回这条，首屏记录的提问时间均在20日。结合官网实际参数与原生记录，不能把提问日期当回复日期。原始响应保存在下述证据目录的 `920640-ask_day.json`、`920640-reply_day.json`。

## 实现

`corpus/_fetch_qa.py` 先查指定提问日期窗口，小于100条时按总数停止，达到100条则二分日期窗口。当天仍达上限时保留结果并报不完整；所有窗口与补查共用40次查询上限和原有单公司60秒预算。

日更水位按回复日期计算，因此另查官网“最新回复”，检查观测到的回复时间是否倒序，直到遇到早于水位起点的记录或查询结果结束。该步骤补回“旧提问、新回复”，不会把日期筛选0条直接当作回复增量0条。若最新100条仍未覆盖起点，继续报不完整。

重复或重叠ID、响应无效、总数变化、日期筛选未生效、预算耗尽均不能成为成功空结果。已取得的窗口内回复在网络异常或超时前合并到隔离快照，由调用方保留部分记录并保持失败水位。

## 验证结果

| 验证 | 结果 | 耗时 |
|---|---|---:|
| P5W 2026-08-29至09-11 | 0条；2次问答查询及1次公司页面请求；完整性检查通过 | 3.76秒 |
| P5W 2026-08-07当天 | 69条；7页筛选结果与落盘ID集合完全一致；去重后69条；另7页最新回复补查 | 24.31秒 |
| 日更真实 `RequestsClient.fetch_qa`，起点08-29 | 互动易主通道与P5W兜底共5次请求，无异常；原快照219条全部保留，新增0条 | 8.18秒 |

真实请求在授权的隔离工作树执行，代码已同步到主项目。浏览器筛选8月7日也显示“共69条”。上述记录仅用于采集验证，不是新增领域结论。

回归覆盖日期参数、精确总数停止、日期拆分、单日上限、旧问题新回复、回复补查上限、排序异常、总数变化、重复页、网络异常后保留部分记录、预算恰好耗尽和真实69条响应重放。新增13项测试与原国内45项测试，在隔离工作树和集成后的主项目全部通过。

执行命令：

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 -m unittest discover -s tests -p test_p5w_date_windows.py -q
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 -m unittest discover -s tests -p test_domestic_daily.py -q
git diff --check
```

## 证据与边界

原始页面、脚本、请求/响应、诊断快照均在 [本次证据目录](/Users/jowang/Downloads/workflow-rehearsal-daily-state/diagnosis-20260911/p5w/)。关键文件：`live-recent-result.json`、`live-aug7-result.json`、`live-caller-result.json`。仓库内 `tests/fixtures/p5w/huagong-20260807.json` 保留真实总数、ID与时间的投影，正文省略；完整响应在诊断目录。

24个 canonical 账本及6个正式日更状态/报告文件共30项 SHA256 前后相同，详见 `protected-before.json`、`protected-after.json`。本次没有推进正式水位、覆盖正式日报或晋升候选，没有提交、推送或修改定时任务。

这次证明华工科技两个窗口及真实单公司调用通过。单日100条、最新回复上限前无法覆盖水位、站点排序或内容动态变化仍有明确限制；不据此声称历史全量或其他公司全部恢复。全池日更需另以实际最终运行状态判断。
