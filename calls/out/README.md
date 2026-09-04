# 海外电话会与官网技术情报层 MVP

数据源仅为 `calls/*.csv`；本目录全部由渲染器重建。

> 覆盖边界：信源底账行数只是采集记录，不等于结论覆盖；结论覆盖必须逐级看“季度槽 → 可用来源 → 陈述 → 已核陈述 → 已核事件”五级。`reviewed` / `anchor_reviewed` 仅表示原文已核；`corroborated` 才表示存在与第一方不同来源（不同 origin_group 且独立于第一方）的交叉支持；同源双证（同一 origin_group 的多份材料）不得升级为 corroborated。

## 覆盖分级（五级，分母与公司数可复算）

分母：正式季度池 39 家 enabled 公司（`universe.csv` 中 `enabled=yes`）；watch 实体与发现候选不计入本表。

| 覆盖级别 | 定义 | 公司数 | 分母 |
|---|---|---:|---:|
| 季度槽登记 | 4 个季度槽均已登记（含 not_collected/unavailable 槽位） | 39 | 39 |
| 可用来源 | 4 个季度槽均有 `available` 材料 | 36 | 39 |
| 陈述登记 | 在 `claims.csv` 有至少 1 条陈述（含 candidate/rejected） | 12 | 39 |
| 已核陈述 | 有至少 1 条 `reviewed` 陈述（reviewed 仅表示原文已核） | 12 | 39 |
| 已核事件 | 有至少 1 条已审核雷达事件（证据经 `anchor_reviewed`） | 15 | 39 |

信源底账：`sources.csv` 共 166 行（季度槽材料 163 行、季度槽位 156 个）。这些行数是采集底账，不能单独用“N 家公司、M 行来源”表达研究结论覆盖；结论覆盖以上表五级为准。

## 事件状态（asserted / corroborated 分列）

- asserted：32 条 —— 第一方主张，原文已核，但没有独立来源交叉支持。
- corroborated：2 条 —— 存在与第一方不同 origin_group 且独立于第一方的来源支持（EV013、EV014）。
- 同源双证（同一 origin_group 的多份材料）不得升级为 corroborated；asserted 不代表已确认，corroborated 也不代表产能或卡点变化。

## 输出

- [公司事件雷达（JSON）](event-intelligence.json)
- [跨公司议题矩阵](theme-matrix.md)
- [受限需求链](limited-demand-chains.md)
- [承诺—兑现账本](commitments.md)
- [技术陈述—商业反馈](technology-feedback.md)
- [全景情报投影（CSV）](panorama-intelligence.csv)
- [国内能力定位投影（JSON）](positioning.json)

## 公司季度卡

- [ADTRAN](companies/adtn-adtran.md)
- [AIXTRON](companies/aixa-aixtron.md)
- [ASMPT](companies/asmpt-asmpt.md)
- [AXT](companies/axti-axt.md)
- [Applied Optoelectronics](companies/aaoi-applied-optoelectronics.md)
- [Arista](companies/anet-arista.md)
- [Broadcom](companies/avgo-broadcom.md)
- [Celestica](companies/cls-celestica.md)
- [Ciena](companies/cien-ciena.md)
- [Cisco](companies/csco-cisco.md)
- [Coherent](companies/cohr-coherent.md)
- [Corning](companies/glw-corning.md)
- [Credo](companies/crdo-credo.md)
- [Fabrinet](companies/fn-fabrinet.md)
- [FormFactor](companies/form-formfactor.md)
- [Furukawa Electric](companies/furukawa-furukawa-electric.md)
- [GlobalFoundries](companies/gfs-globalfoundries.md)
- [Jabil](companies/jbl-jabil.md)
- [Lightwave Logic](companies/lwlg-lightwave-logic.md)
- [Lumentum](companies/lite-lumentum.md)
- [MACOM](companies/mtsi-macom.md)
- [Marvell](companies/mrvl-marvell.md)
- [MaxLinear](companies/mxl-maxlinear.md)
- [Meta](companies/meta-meta.md)
- [Mycronic](companies/mycronic-mycronic.md)
- [NVIDIA](companies/nvda-nvidia.md)
- [Nokia](companies/nok-nokia.md)
- [Oxford Instruments](companies/oxig-oxford-instruments.md)
- [POET Technologies](companies/poet-poet-technologies.md)
- [Sanmina](companies/sanm-sanmina.md)
- [Semtech](companies/smtc-semtech.md)
- [Sivers Semiconductors](companies/sivers-sivers-semiconductors.md)
- [Smartoptics](companies/smop-smartoptics.md)
- [Soitec](companies/soi-soitec.md)
- [Sumitomo Electric](companies/sumitomo-sumitomo-electric.md)
- [Tower Semiconductor](companies/tsem-tower-semiconductor.md)
- [VIAVI](companies/viav-viavi.md)
- [Veeco](companies/veco-veeco.md)
- [Wiwynn](companies/wiwynn-wiwynn.md)
