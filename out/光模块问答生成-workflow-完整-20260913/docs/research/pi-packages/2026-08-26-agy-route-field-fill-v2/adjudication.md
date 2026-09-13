# AGY 3.7 Flash v2 最终裁决

日期：2026-08-26
状态：draft-only；不落知识库；不改变任何 PQ/TQ/WQ 覆盖状态。

## 裁决

| 任务 | AGY 结果 | Codex 裁决 | 可否交给 Pi |
|---|---|---|---|
| Coherent 800G EML | 找到准确系列与官方 PDF，保守重填字段 | `PASS_WITH_LOCAL_FIXES` | 仅消费 `pi-handoff.md`，不得直接消费 AGY raw |
| 800G SiPh exact SKU | `FAIL_NO_SINGLE_INSTANCE` | `PASS_AS_RECORDED_SEARCH_FAILURE` | 不生成实例字段；只消费缺口和候选来源 |

## EML 本地修正

1. `FTCE4527E1PxA-2N` 是公开系列字符串；样例标签可见 `FTCE4527E1PCA-2N`，但当前不把样例标签自动当成可下单状态证明。
2. Coherent 官方产品页把同一产品系列明确列为 `Transmitter: EML`、`Receiver: PIN`。因此 AGY v2 将 transmitter technology 记为 UNKNOWN 过于保守；可在产品系列层恢复 EML/PIN，但不得继续推导 EML die topology、DFB+EAM 结构、PIN array 或内部封装。
3. `x=C/L` 表示温度变体。0–70°C 与 20–60°C 是条件化选项，不是事实矛盾；具体实例必须随 `x` 决定。
4. `A: Closed Heatsink` 与 `-2N: No Heat Sink Design` 在同一 preliminary 文档中存在命名冲突。保持 `thermal_top: UNKNOWN_CONFLICTING_LABELS`，不得自行解释为 suffix override、flat-top 或 riding heatsink。
5. `Preliminary Product Specification` 只能支持文档成熟度；产品 GA、量产和 active ordering 继续 UNKNOWN。
6. TDECQ/TECQ 是信号眼图指标，不支持 thermoelectric cooler。内部 TEC 保持 UNKNOWN。
7. FEC 的存在和目标 BER 可记录；FEC 精确类型与终止位置保持 UNKNOWN，除非产品文档或 CMIS 配置明确说明。

## SiPh 失败边界

`FAIL_NO_SINGLE_INSTANCE` 只表示：AGY 在本轮公开检索中没有找到同时满足“exact product + first-party product document + explicit SiPh binding”的实例。

它不支持以下负向结论：

- 市场上没有 800G SiPh 商业模块；
- 候选公司没有相关产品；
- 厂商一定采用或不采用某种平台；
- 公开互联网不存在更强证据。

AGY 输出未提供逐条完整查询串、命中页面抓取时间和每一候选的升级阶梯，因此候选表属于 discovery search log，不属于可复现的 absence evidence。

## 对研究模型的启示

商业模块的内部光子平台经常没有在 exact-SKU datasheet 中披露。路线模型必须分开：

1. `product_instance_evidence`：产品型号、PMD、接口、功耗、温度等；
2. `platform_component_evidence`：PIC/laser/modulator 等平台器件；
3. `instance_platform_binding_evidence`：把产品实例与平台器件连接起来的独立证据；
4. `demo_evidence`：论文或展会演示，不自动继承给商业 SKU。

缺少第 3 类证据时，产品画像的 `photonic_platform` 必须保持 UNKNOWN；不能用公司平台能力或 demo 补齐。

## 禁止动作

- 不消费 `agy-eml-recheck-output.md` 中未经本裁决确认的解释性字段；
- 不把 `FAIL_NO_SINGLE_INSTANCE` 写成产业事实；
- 不生成正式 Route Profile、公司服务群或 WHY 边；
- 不写 `knowledge.yaml`、`why_links` 或 canonical question 状态。
