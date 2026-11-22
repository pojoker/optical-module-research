# TQ009 路线画像种子合同

## 1. 研究目标

回答 TQ009：一个可比较的具体路线画像由哪些轴值组合而成？

本轮只建立少量 **Route Profile Seed**，验证字段、观测状态、缺口和公司挂载接口；种子不是正式 Route Profile，也不表示 TQ009 已覆盖。

## 2. 强制边界

- mode: `draft_only`
- canonical write: forbidden
- coverage change: forbidden
- new QID: forbidden
- formal `RP###`: forbidden
- cross-instance splicing: forbidden
- inferred fill: forbidden
- WHY / route ranking / maturity / market share: forbidden
- confirmed company route group: forbidden unless the frozen source directly links that company and exact product/demo instance

上游唯一有效口径为：

- `../2026-08-24-tq004-route-axes-v1/post-adjudication-effective-text.md`
- `../2026-08-24-tq005-tq008-axis-values-v1/post-adjudication-effective-text.md`

## 3. 研究对象

只允许从下列已冻结、同一公司的一手产品或演示实例建立种子：

1. Coherent `FTCE4517E1PxM` 800G-DR8 OSFP 产品；
2. Coherent OFC 2025 1.6T-DR8 OSFP SiPh LRO 演示；
3. Coherent OFC 2025 1.6T-DR8 OSFP SiPh 3 nm DSP 演示；
4. Coherent ECOC 2022 800G-DR8+ QSFP-DD800 SiPh MZM PIC 互操作端点；
5. Coherent ECOC 2022 800G-DR8+ OSFP EML/photodetector 互操作端点。

Intel OCI 等平台能力披露不得转换为已观察路线画像种子。

## 4. 种子最小 schema

每个种子必须包含：

```yaml
seed_id: RPS-D##
draft_only: true
source_instance: 同一产品或演示实例的稳定描述
company: 公司名
product_or_demo: product | demo_endpoint
evidence_type: product_datasheet | company_demo_statement
axes:
  tq005_external_link:
    aggregate_rate: {value: ..., observation_state: ..., source_ids: [...]}
    host_lanes: {value: ..., observation_state: ..., source_ids: [...]}
    media_lanes: {value: ..., observation_state: ..., source_ids: [...]}
    modulation: {value: ..., observation_state: ..., source_ids: [...]}
    fec_pmd: {value: ..., observation_state: ..., source_ids: [...]}
    media: {value: ..., observation_state: ..., source_ids: [...]}
    reach: {value: ..., observation_state: ..., source_ids: [...]}
    wavelength_organization: {value: ..., observation_state: ..., source_ids: [...]}
  tq006_electrical_responsibility:
    architecture: {value: ..., observation_state: ..., source_ids: [...], raw_label: ...}
  tq007_photonics:
    platform_material: {value: ..., observation_state: ..., source_ids: [...]}
    light_source: {value: ..., observation_state: ..., source_ids: [...]}
    modulator_emitter: {value: ..., observation_state: ..., source_ids: [...]}
    detector: {value: ..., observation_state: ..., source_ids: [...]}
    integration: {value: ..., observation_state: ..., source_ids: [...]}
  tq008_placement:
    placement_class: {value: ..., observation_state: ..., source_ids: [...]}
    form_factor: {value: ..., observation_state: ..., source_ids: [...]}
alias_labels: []
missing_fields: []
promotion_blockers: []
would_create_route_profile: false
would_mark_covered: false
```

## 5. 观测状态

每个最小字段必须显式出现，状态只能为：

- `observed`：产品 datasheet 或同一演示实例直接披露；
- `company-stated`：公司对同一实例使用的平台/架构表述；
- `permitted`：规范或平台能力只说明可以这样做，不得用于填充本轮种子；
- `unknown`：同一实例未披露；此时 `value` 必须为 `UNKNOWN`。

本轮种子字段实际只允许 `observed`、`company-stated`、`unknown`。不得用 `permitted` 填空。

## 6. 实例级防错规则

- 不能因为产品名含 `DR8` 就补出未披露的 FEC、波长、lane 或 reach；
- 不能因为有 DSP 就自动写成 full-retimed；必须有 Tx/Rx 职责证据；
- 不能因为 EML 的一般器件定义就补出某产品的 InP、DFB+EAM 或 monolithic integration；
- 不能因为 SiPh 平台通常包含某器件就补出 light source、detector 或 integration；
- 互操作演示的两个端点必须拆成两个种子；共同传输不等于内部架构相同；
- `DR+`、`LRO` 等保留为 alias/raw label，并与规范化字段分开。

## 7. 公司挂载边界

本轮同时验证三种关系，但只允许前两种成为草案观察：

1. `physical_capability_point`：`points.csv` 的公司能力点挂物理格；
2. `capability_match_candidate`：只有种子完成 TQ010/TQ011、明确所需物理格后才可推导；当前默认阻断；
3. `route_service_evidence`：来源直接连接公司与精确产品/演示实例；本轮五个种子只可记录 Coherent 为实例主体，不外推客户、供应商或其他服务公司。

`edges.csv` 的供货/客户关系不能自动升级为路线服务证据。

## 8. 输出要求

Pi 必须：

1. 输出 5 个且仅 5 个 `RPS-D##` 草案种子；
2. 每个种子只使用同一实例来源；
3. 每个最小字段都显式给出观测状态；
4. 列出 `missing_fields` 和 `promotion_blockers`；
5. 输出 `cross_seed_comparison`，只比较“哪些字段已观察、哪些为 UNKNOWN”，不得排名；
6. 输出 `follow_up_questions_without_new_qid`，每条只能挂 TQ009、TQ010 或 TQ011，不创建新 ID；
7. 结尾声明三个布尔值均为 false：正式 RP、coverage、canonical write。

## 9. 失败条件

出现任一项即退回：

- 跨实例拼接；
- 从标准名、产品名或常识推断补值；
- UNKNOWN 被省略或写成否定值；
- 把 DSP 演示自动归为 full-retimed；
- 把两个互操作端点合并成一条路线；
- 把能力点或供货关系写成路线服务；
- 新建 QID、正式 RP ID、WHY、路线排名或公司受益判断；
- 写入 canonical 或改变覆盖状态。
