# TQ005–TQ008 四轴展开合同

## 1. 目标与状态

目标：在不改变现有问题树的前提下，为 TQ005–TQ008 建立最小可用、可追溯、非穷尽的轴值字典，并检验这些问题是否能继续长出更细的研究缺口。

- mode: `draft_only`
- canonical write: forbidden
- coverage change: forbidden
- new QID: forbidden
- TQ009 Route Profile combination: forbidden
- WHY / company grouping / route ranking: forbidden

## 2. 上游强制口径

唯一上游口径为 `../2026-08-24-tq004-route-axes-v1/post-adjudication-effective-text.md`。

- TQ005 与 TQ006 不得重复计算具名 MSA profile；
- TQ007 只在现有 QID 内使用嵌套字段；
- TQ008 必须分开 `other on-board` 与 `near-package NPO`；
- observed product/demo、company platform statement、standard/framework boundary 必须分开；
- “候选/规范允许”不得写成“已量产/已观察”。

## 3. 各题验收合同

### TQ005：产品/链路标准轴

必须回答：

1. 该轴到底约束什么外部互操作边界；
2. 最小字段集：aggregate rate、host/media lane count 与 lane rate、modulation、FEC/PMD、media、reach、wavelength/parallel-vs-WDM organization；
3. 区分正式标准名、MSA profile、公司产品/演示后缀；
4. 明确它不能推出 DSP/linear、EML/SiPh、OSFP/CPO；
5. 生成 3–6 个仍挂 TQ005 的无 ID 细化问题。

### TQ006：电接口架构轴

必须回答：

1. 以 host、module/engine、optical path 为参照，分别说明 signal conditioning、retiming、FEC、DAC/ADC 等职责放在哪里；
2. 建立 `retimed / linear / Tx-retimed-Rx-linear(LRO/RTLR) / half-retimed / direct-drive candidate` 的职责表；
3. 每个值标注证据层级：正式规范、MSA、framework/in-progress、公司演示；
4. `direct-drive` 等候选不得写成完整量产菜单；
5. LPO 只作 `linear + pluggable` 复合 alias，具名 profile 只作 reference；
6. 生成 3–6 个仍挂 TQ006 的无 ID 细化问题。

### TQ007：光子平台/实现轴

必须在 TQ007 内部使用五个嵌套字段：

1. `platform/material`；
2. `light source`；
3. `modulator/emitter`；
4. `detector`；
5. `integration`。

要求：

- 给出有一手来源支持的示例值和定义，不声称穷尽；
- 明确 `SiPh`、`InP/GaAs`、`EML`、`MZM`、`VCSEL`、`PIN` 分属什么粒度；
- 禁止制作 EML/SiPh/VCSEL 的同级互斥表；
- 区分器件定义、平台能力披露和产品实例；
- 生成 3–6 个仍挂 TQ007 的无 ID 细化问题。

### TQ008：封装/放置架构轴

必须回答：

1. 用 optical engine 相对 host ASIC / first-level substrate / front panel 的位置建立操作性定义；
2. 至少区分 `front-panel pluggable / other on-board / near-package NPO / CPO`；
3. NPO 必须锚定 OIF 定义；CPO 必须锚定 same first-level substrate；
4. OSFP/QSFP-DD 只能作为 pluggable 子层 form factor；
5. `光学离 ASIC 多远` 先作定性位置分类，不虚构统一毫米阈值；
6. 生成 3–6 个仍挂 TQ008 的无 ID 细化问题。

## 4. 输出格式

按 TQ005、TQ006、TQ007、TQ008 四节输出。每节包含：

1. 一句话答案；
2. 操作性定义/字段或职责表；
3. 证据化示例（来源 ID、证据类型、只支持什么）；
4. 禁止外推；
5. `next_questions_without_new_qid`：3–6 条自然语言问题，每条只写 `parent_question_id`、`question`、`why_open`、`needed_evidence`，不得自造编号。

最后输出：

- `cross_axis_guardrails`；
- `observed_differences_so_far`，只列已观察实例；
- `stop_status`，三个布尔值均为 false；
- 原子主张使用唯一 `draft_id`，每题最多 7 条，总计不超过 24 条，全部 `would_mark_covered: false`。

## 5. 失败条件

出现任一项即退回：

- 把具名 MSA profile 当第五根轴或在 TQ005/TQ006 双计；
- 把 EML、SiPh、VCSEL 当同级互斥路线；
- 合并 other on-board 与 NPO；
- 把 framework/in-progress 候选写成量产事实；
- 把标准沉默写成已观察产品组合；
- 进入 TQ009、WHY、公司归群或路线优劣；
- 新建 QID、写 canonical 或改变 coverage。
