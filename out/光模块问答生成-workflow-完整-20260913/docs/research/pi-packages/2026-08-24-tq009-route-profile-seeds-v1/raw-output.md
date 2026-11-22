# TQ009 路线画像种子草案输出（五个且仅五个，全部 draft-only）

**受控与证据边界声明**

- 受控文本：G1 `contract.md` + G2 `post-adjudication-effective-text.md`（TQ005–TQ008 唯一有效口径）。
- 一手来源仅 S1–S4；每个种子只使用同一产品/演示实例，不做跨实例拼接。
- 本轮字段只使用 `observed`、`company-stated`、`unknown` 三种状态；未使用 `permitted` 填空。
- 不允许推断：`DR8`/`DR+`/`DR4+`/`LRO` 只作 alias/raw label；DSP 出现不构成 full-retimed；EML 不推导 InP/DFB+EAM；SiPh 不推导光源/探测器/集成。
- 公司挂载：仅记录 Coherent 为实例主体；不建立 capability_match_candidate、不建立 route_service_evidence，不把能力点或供货边升级为路线服务证据。
- 不生成正式 RP、不改变覆盖状态、不写 canonical、不新建 QID、不排名。

---

## 1. RPS-D01 — FTCE4517E1PxM 800G-DR8/DR+ OSFP 产品

```yaml
seed_id: RPS-D01
draft_only: true
source_instance: "Coherent FTCE4517E1PxM 800G-DR8/DR+ OSFP optical transceiver product; frozen S1 product page and S2 datasheet describe the same exact product instance, no other instance is spliced"
company: Coherent
product_or_demo: product
evidence_type: product_datasheet
axes:
  tq005_external_link:
    aggregate_rate:
      value: "Marketing class 800G; reported aggregate bit rate 850 Gb/s"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
    host_lanes:
      value: "8 x 106.25 Gb/s PAM4 electrical; 53.125 GBd per lane"
      observation_state: "observed"
      source_ids: ["S2"]
    media_lanes:
      value: "UNKNOWN count; per-lane optical signaling 53.125 GBd"
      observation_state: "observed"
      source_ids: ["S2"]
    modulation:
      value: "PAM4; 53.125 GBd per optical lane"
      observation_state: "observed"
      source_ids: ["S2"]
    fec_pmd:
      value: "PMD/reference 400GBASE-DR4 in a 2 x 400 DR4 application configuration; FEC code UNKNOWN"
      observation_state: "observed"
      source_ids: ["S2"]
    media:
      value: "SMF per G.652"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
    reach:
      value: "500 m"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
    wavelength_organization:
      value: "Parallel MPO-16 receptacle; lane wavelength 1304.5-1317.5 nm (1310 nm product value)"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
  tq006_electrical_responsibility:
    architecture:
      value: "retimed raw architecture label; detailed Tx/Rx and FEC responsibility split UNKNOWN"
      observation_state: "company-stated"
      raw_label: "8x100G PAM4 retimed ... electrical interface"
      source_ids: ["S2"]
  tq007_photonics:
    platform_material:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    light_source:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulator_emitter:
      value: "EML"
      observation_state: "observed"
      source_ids: ["S1"]
    detector:
      value: "PIN"
      observation_state: "observed"
      source_ids: ["S1"]
    integration:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq008_placement:
    placement_class:
      value: "front-panel pluggable"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
    form_factor:
      value: "OSFP"
      observation_state: "observed"
      source_ids: ["S1", "S2"]
alias_labels: ["800G-DR+", "800G-DR8", "DR8"]
missing_fields:
  - tq005.media_lanes.count
  - tq005.fec_pmd.fec_code
  - tq006.architecture.tx_rx_responsibility_detail
  - tq007.platform_material
  - tq007.light_source
  - tq007.integration
promotion_blockers:
  - "marketed 800G versus reported 850 Gb/s needs a stable nominal-versus-line-rate convention"
  - "DR+ versus DR8 naming needs reconciliation and is not a single formal PMD"
  - "exact FEC code and optical lane count are not directly reported"
  - "retiming responsibilities (Tx/Rx/FEC split) are not diagrammed"
  - "TQ007 platform material, light source and integration remain UNKNOWN"
would_create_route_profile: false
would_mark_covered: false
```

---

## 2. RPS-D02 — OFC 2025 1.6T-DR8 OSFP SiPh LRO 演示端点

```yaml
seed_id: RPS-D02
draft_only: true
source_instance: "OFC 2025 1.6T-DR8 OSFP silicon-photonics LRO transceiver demo module; the first of the three 1.6T-DR8 modules in S3 line 1979 only, not spliced with the other two modules"
company: Coherent
product_or_demo: demo_endpoint
evidence_type: company_demo_statement
axes:
  tq005_external_link:
    aggregate_rate:
      value: "1.6T"
      observation_state: "observed"
      source_ids: ["S3"]
    host_lanes:
      value: "8 x 200G electrical interfaces"
      observation_state: "observed"
      source_ids: ["S3"]
    media_lanes:
      value: "8 x 200G optical interfaces"
      observation_state: "observed"
      source_ids: ["S3"]
    modulation:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    fec_pmd:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    reach:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    wavelength_organization:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq006_electrical_responsibility:
    architecture:
      value: "Tx-retimed / Rx-linear (LRO)"
      observation_state: "company-stated"
      raw_label: "LRO; linear receive optics; DSP retiming only in the transmit direction"
      source_ids: ["S3"]
  tq007_photonics:
    platform_material:
      value: "silicon photonics"
      observation_state: "company-stated"
      source_ids: ["S3"]
    light_source:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulator_emitter:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    detector:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    integration:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq008_placement:
    placement_class:
      value: "front-panel pluggable"
      observation_state: "observed"
      source_ids: ["S3"]
    form_factor:
      value: "OSFP"
      observation_state: "observed"
      source_ids: ["S3"]
alias_labels: ["1.6T-DR8", "LRO"]
missing_fields:
  - tq005.modulation
  - tq005.fec_pmd
  - tq005.media
  - tq005.reach
  - tq005.wavelength_organization
  - tq007.light_source
  - tq007.modulator_emitter
  - tq007.detector
  - tq007.integration
promotion_blockers:
  - "no exact modulation, FEC/PMD, media, reach or wavelength organization disclosure"
  - "no light source, modulator/emitter, detector or integration disclosure"
  - "host FEC and SerDes responsibilities are not stated even though the Tx/Rx retiming split is"
would_create_route_profile: false
would_mark_covered: false
```

---

## 3. RPS-D03 — OFC 2025 1.6T-DR8 OSFP SiPh 3nm DSP 演示端点

```yaml
seed_id: RPS-D03
draft_only: true
source_instance: "OFC 2025 1.6T-DR8 OSFP silicon-photonics demo module incorporating 3 nm digital signal processors; the third of the three 1.6T-DR8 modules in S3 line 1979 only, not spliced with the first or second module"
company: Coherent
product_or_demo: demo_endpoint
evidence_type: company_demo_statement
axes:
  tq005_external_link:
    aggregate_rate:
      value: "1.6T"
      observation_state: "observed"
      source_ids: ["S3"]
    host_lanes:
      value: "8 x 200G electrical interfaces"
      observation_state: "observed"
      source_ids: ["S3"]
    media_lanes:
      value: "8 x 200G optical interfaces"
      observation_state: "observed"
      source_ids: ["S3"]
    modulation:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    fec_pmd:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    reach:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    wavelength_organization:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq006_electrical_responsibility:
    architecture:
      value: "UNKNOWN"
      observation_state: "unknown"
      raw_label: "3 nm DSP (a DSP mention does not establish full-retimed architecture; Tx/Rx retiming, Rx architecture, FEC location and host SerDes responsibility are unreported)"
      source_ids: []
  tq007_photonics:
    platform_material:
      value: "silicon photonics"
      observation_state: "company-stated"
      source_ids: ["S3"]
    light_source:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulator_emitter:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    detector:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    integration:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq008_placement:
    placement_class:
      value: "front-panel pluggable"
      observation_state: "observed"
      source_ids: ["S3"]
    form_factor:
      value: "OSFP"
      observation_state: "observed"
      source_ids: ["S3"]
alias_labels: ["1.6T-DR8", "3 nm DSP"]
missing_fields:
  - tq005.modulation
  - tq005.fec_pmd
  - tq005.media
  - tq005.reach
  - tq005.wavelength_organization
  - tq006.architecture
  - tq007.light_source
  - tq007.modulator_emitter
  - tq007.detector
  - tq007.integration
promotion_blockers:
  - "3 nm DSP module architecture is UNKNOWN; it is not labeled full-retimed"
  - "Rx retiming, Tx retiming, FEC placement and host SerDes responsibility are unreported"
  - "exact modulation, FEC/PMD, media, reach and wavelength organization are missing"
  - "light source, modulator/emitter, detector and integration are missing"
would_create_route_profile: false
would_mark_covered: false
```

---

## 4. RPS-D04 — ECOC 2022 800G-DR8+ QSFP-DD800 SiPh MZM PIC 互操作端点

```yaml
seed_id: RPS-D04
draft_only: true
source_instance: "ECOC 2022 800G-DR8+ QSFP-DD800 silicon-photonics MZM PIC transceiver module interoperability endpoint; the QSFP-DD800 SiPh MZM-PIC endpoint only in S4 line 1967, the opposite OSFP EML endpoint is not spliced in"
company: Coherent
product_or_demo: demo_endpoint
evidence_type: company_demo_statement
axes:
  tq005_external_link:
    aggregate_rate:
      value: "800 Gbps"
      observation_state: "observed"
      source_ids: ["S4"]
    host_lanes:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media_lanes:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulation:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    fec_pmd:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    reach:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    wavelength_organization:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq006_electrical_responsibility:
    architecture:
      value: "UNKNOWN"
      observation_state: "unknown"
      raw_label: ""
      source_ids: []
  tq007_photonics:
    platform_material:
      value: "silicon photonics"
      observation_state: "company-stated"
      source_ids: ["S4"]
    light_source:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulator_emitter:
      value: "MZM"
      observation_state: "observed"
      source_ids: ["S4"]
    detector:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    integration:
      value: "MZM PIC (internally designed); finer PIC/EIC/light-source structure UNKNOWN"
      observation_state: "company-stated"
      source_ids: ["S4"]
  tq008_placement:
    placement_class:
      value: "front-panel pluggable"
      observation_state: "observed"
      source_ids: ["S4"]
    form_factor:
      value: "QSFP-DD800"
      observation_state: "observed"
      source_ids: ["S4"]
alias_labels: ["800G-DR8+", "2x400G-DR4+"]
missing_fields:
  - tq005.host_lanes
  - tq005.media_lanes
  - tq005.modulation
  - tq005.fec_pmd
  - tq005.media
  - tq005.reach
  - tq005.wavelength_organization
  - tq006.architecture
  - tq007.light_source
  - tq007.detector
  - tq007.integration.finer_structure
promotion_blockers:
  - "most TQ005 external-link details are absent (host/media lanes, modulation, FEC/PMD, media, reach, wavelength organization)"
  - "architecture (DSP/linear/retimed and Tx/Rx responsibility) is absent"
  - "light source and detector are absent"
  - "MZM-PIC internal partitioning is not disclosed"
  - "the opposite EML endpoint cannot supply the missing fields"
would_create_route_profile: false
would_mark_covered: false
```

---

## 5. RPS-D05 — ECOC 2022 800G-DR8+ OSFP EML/photodetector 互操作端点

```yaml
seed_id: RPS-D05
draft_only: true
source_instance: "ECOC 2022 800G-DR8+ OSFP 1310 nm EML/photodetector transceiver module interoperability endpoint; the OSFP EML/photodetector endpoint only in S4 line 1967, the opposite QSFP-DD800 SiPh endpoint and the adjacent 200G EML demo are not imported"
company: Coherent
product_or_demo: demo_endpoint
evidence_type: company_demo_statement
axes:
  tq005_external_link:
    aggregate_rate:
      value: "800 Gbps"
      observation_state: "observed"
      source_ids: ["S4"]
    host_lanes:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media_lanes:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    modulation:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    fec_pmd:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    media:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    reach:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    wavelength_organization:
      value: "Wavelength 1310 nm; parallel/WDM and lane/fiber mapping UNKNOWN"
      observation_state: "observed"
      source_ids: ["S4"]
  tq006_electrical_responsibility:
    architecture:
      value: "UNKNOWN"
      observation_state: "unknown"
      raw_label: ""
      source_ids: []
  tq007_photonics:
    platform_material:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
    light_source:
      value: "1310 nm EML lasers; DFB/external/integrated/on-chip detail UNKNOWN"
      observation_state: "observed"
      source_ids: ["S4"]
    modulator_emitter:
      value: "EML"
      observation_state: "observed"
      source_ids: ["S4"]
    detector:
      value: "generic photodetectors; detector subtype UNKNOWN"
      observation_state: "observed"
      source_ids: ["S4"]
    integration:
      value: "UNKNOWN"
      observation_state: "unknown"
      source_ids: []
  tq008_placement:
    placement_class:
      value: "front-panel pluggable"
      observation_state: "observed"
      source_ids: ["S4"]
    form_factor:
      value: "OSFP"
      observation_state: "observed"
      source_ids: ["S4"]
alias_labels: ["800G-DR8+", "2x400G-DR4+"]
missing_fields:
  - tq005.host_lanes
  - tq005.media_lanes
  - tq005.modulation
  - tq005.fec_pmd
  - tq005.media
  - tq005.reach
  - tq005.wavelength_organization.organization_and_mapping
  - tq006.architecture
  - tq007.platform_material
  - tq007.light_source.substructure_and_location
  - tq007.detector.subtype
  - tq007.integration
promotion_blockers:
  - "most TQ005 external-link details are absent (host/media lanes, modulation, FEC/PMD, media, reach, wavelength organization/mapping)"
  - "architecture (DSP/linear/retimed and Tx/Rx responsibility) is absent"
  - "platform/material and integration are absent"
  - "light-source and detector subtypes are incomplete"
  - "the adjacent 200G EML demo and the opposite SiPh endpoint cannot fill the gaps"
would_create_route_profile: false
would_mark_covered: false
```

---

## 6. cross_seed_comparison

只比较每个种子“哪些最小字段已有 observed/company-stated 证据、哪些仍为 UNKNOWN”，不做路线优劣、成熟度、公司或市场份额判断。

| Seed | 已 observed / company-stated 的最小字段 | 仍为 UNKNOWN 的字段或子字段 |
|---|---|---|
| RPS-D01 | aggregate rate；host lanes；media lane per-lane 速率；modulation (PAM4)；PMD/reference；media；reach；wavelength organization (parallel/MPO-16 + 1310 nm)；retimed 原始架构标签；EML；PIN；placement/form factor | media lane count；FEC code；Tx/Rx/FEC 职责细节；platform/material；light source；integration |
| RPS-D02 | aggregate rate；host/media lanes（8×200G 电/光）；Tx-retimed/Rx-linear 架构；silicon photonics；placement/form factor | modulation；FEC/PMD；media；reach；wavelength organization；host FEC/SerDes 职责；light source；modulator/emitter；detector；integration |
| RPS-D03 | aggregate rate；host/media lanes（8×200G 电/光）；silicon photonics；placement/form factor | modulation；FEC/PMD；media；reach；wavelength organization；architecture（含 Tx/Rx retiming 与 FEC/host 职责）；light source；modulator/emitter；detector；integration |
| RPS-D04 | aggregate rate；silicon photonics；MZM；MZM-PIC 标签；placement/form factor | host/media lanes；modulation；FEC/PMD；media；reach；wavelength organization；architecture；light source；detector；finer integration |
| RPS-D05 | aggregate rate；1310 nm 波长；EML 光源；generic photodetector；placement/form factor | host/media lanes；modulation；FEC/PMD；media；reach；wavelength organization/mapping；architecture；platform/material；light-source 细节；detector subtype；integration |

---

## 7. follow_up_questions_without_new_qid

以下问题不创建新 QID，只挂 TQ009 / TQ010 / TQ011。

- `parent_question_id: TQ009`
  - question: 哪些同实例产品规格或演示 block diagram 能填补当前每个 UNKNOWN 的 TQ005–TQ008 字段，而不引入平台级或相邻演示的主张？
  - why_open: 当前五个种子均有多个最小字段停留在 UNKNOWN，现有 S1–S4 无法补齐。
  - needed_evidence: 同一精确产品/演示实例的完整规格表、白皮书或 block diagram。
- `parent_question_id: TQ010`
  - question: 一旦缺失轴值被直接证据补齐，某个种子要成为 capability_match_candidate 之前，需要哪些明确给出的物理格要求？
  - why_open: 合同要求能力匹配候选只能在种子完成 TQ010/TQ011 且明确所需物理格后推导，当前全部默认阻断。
  - needed_evidence: 对物理格（physical capability point）的显式、可验证的要求描述。
- `parent_question_id: TQ011`
  - question: 什么一手证据能把精确产品/演示实例直接连接到路线服务，而不依赖供货/客户边、也不创建公司路线群组？
  - why_open: 本轮五个种子只记录 Coherent 为实例主体，供货/客户边不能自动升级为路线服务证据。
  - needed_evidence: 直接连接公司与精确实例并明确服务角色的第一方材料。

---

## 8. 终态声明

```yaml
formal_route_profiles_created: false
coverage_status_changed: false
canonical_write_performed: false
companies_groups_created: false
new_question_ids_created: false
```

本输出为 draft-only。未创建正式 Route Profile（无 `RP###`）、未改变覆盖状态、未执行 canonical write、未创建公司群组、未新建 QID；所有 UNKNOWN 均显式保留，未做推断补值或跨实例拼接。
