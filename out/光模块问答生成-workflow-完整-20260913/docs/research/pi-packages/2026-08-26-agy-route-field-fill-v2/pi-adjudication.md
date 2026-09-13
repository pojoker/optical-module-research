# Pi 小样裁决

日期：2026-08-26
输入：`pi-handoff.md` + `pi-prompt.md`；Pi 无工具、无上下文文件、无外部搜索。
状态：`PASS_WITH_FIXES`；不落知识库。

## 通过项

- 保留产品系列粒度，没有把 `FTCE4527E1PxA-2N` 写成已确认可下单 SKU；
- EML/PIN 只写到系列级；
- GA、量产、TEC、内部器件、FEC location、heatsink 解释保持 UNKNOWN/冲突；
- SiPh 没有生成伪对称商业产品字段卡；
- evidence subject 四层分离方向正确；
- 没有产生路线优劣、WHY、公司群或覆盖状态变化。

## 必须修正

### 1. 来源锚不是长期 UNKNOWN

Pi 因只收到 handoff 而诚实地把页码/短引文写为 UNKNOWN。现已由 `source-excerpts.md` 补齐官方 PDF 页码、SHA256 和短引文。后续消费必须同时读取 `source-excerpts.md`；不能仅靠 URL。

### 2. 细化问题去重结果改为 1 新 + 3 合并

Pi 的“四条均不重复”不成立：

| Pi 注记 | 最终裁决 |
|---|---|
| `TQ007-note-platform-binding` | 与下条合并，归 TQ009；这是实例画像证据绑定问题，不是 TQ007 轴值字典问题 |
| `TQ009-note-evidence-subject` | 保留为唯一新增研究注记：Route Profile 分开 product / platform component / instance-platform binding / demo evidence |
| `TQ013-note-service-without-customer` | 合并进既有 TQ013 开放问题；现有合同已要求公司与精确实例的直接路线证据，并禁止供货/客户边自动升级 |
| `TQ014-note-controlled-comparison` | 合并进既有 TQ014 比较合同；现有合同已禁止非同条件实例和无受控证据的优势/代价结论 |

不创建新 QID；新增注记计数为 1。

### 3. AGY 查询建议拆分

Pi 的第 8 条把 9 家候选厂商捆在同一条检索任务，不符合 exact entity + fingerprint。下一轮必须一家公司一条任务；本批只先挑 2–3 家做小样，不一次扩到 9 家。

### 4. 负向发现仍需检索轨迹

“页面没有 SiPh 字样”“没有公开 datasheet”等不得直接成为事实。只有记录查询串、目标站点、检索日期、命中 URL 和升级阶梯后，才可作为可复现 absence evidence；否则只是 search lead status。

## 唯一有效下游口径

1. EML 字段事实：`source-excerpts.md`；
2. 研究边界：`adjudication.md`；
3. Pi 的结构小样：`pi-output.md`，但本文件的修正优先；
4. 新增细化注记：仅 `TQ009-note-evidence-subject`；
5. SiPh 状态：未找到合格 exact-SKU binding，不等于不存在。
