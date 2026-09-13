# TQ010/TQ014 comparison source audit

> **Status: draft-only evidence audit.** This note uses only the effective seed file, the governing local texts, `tree.yaml`, and the same-instance frozen S3/S4 evidence. S1/S2 concern excluded RPS-D01 and are not used. No product-name expansion, adjacent-demo transfer, web/network evidence, or `archive/` evidence is used.

## 1. Audit basis and status rule

The 36 atomic fields are the 17 TQ005 external-link fields, 7 TQ006 electrical-responsibility fields, 10 TQ007 photonics fields, and 2 TQ008 placement fields in the effective seed. The matrix uses the contract's exclusive statuses: `same`, `different`, `unknown_left`, `unknown_right`, `unknown_both`, and `not_comparable`. A raw value pair is `not_comparable` when both labels exist but their semantic scope differs; it is not converted into a physical difference merely because the strings differ. Sources: `docs/research/pi-packages/2026-08-25-tq010-tq014-delta-tradeoff-v1/contract.md:25-59`; `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/post-adjudication-effective-text.md:5-15`; `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/next-round-acceptance-contracts.md:24-35`.

Local evidence anchors used below:

- **E-D02:** `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/route-profile-seeds-effective.yaml:231-429` (TQ005 `:245-318`; TQ006 `:319-351`; TQ007 `:352-393`; TQ008 `:394-404`).
- **E-D03:** same file `:430-628` (TQ005 `:444-517`; TQ006 `:518-547`; TQ007 `:548-589`; TQ008 `:590-600`).
- **E-D04:** same file `:629-828` (TQ005 `:644-713`; TQ006 `:714-742`; TQ007 `:743-786`; TQ008 `:787-797`).
- **E-D05:** same file `:829-1030` (TQ005 `:846-916`; TQ006 `:917-945`; TQ007 `:946-989`; TQ008 `:990-1000`).
- **S3:** `corpus/web/2026-08-24/coherent.com__ofc-2025-multi-technology.html:1976-1979`.
- **S4:** `corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html:1966-1967`.

## 2. CMP-D02-D03 — 36-field status matrix

Left is RPS-D02; right is RPS-D03. All values and UNKNOWN states are from E-D02/E-D03; the shared-group and per-module assignments are checked directly against S3. The raw-label row is `not_comparable`: `LRO` is an electrical-architecture/responsibility label, while `3 nm DSP` is a component/process-node label, and S3 does not disclose D03's normalized architecture. This follows the explicit controlling guardrail at `docs/research/pi-packages/2026-08-24-tq005-tq008-axis-values-v1/post-adjudication-effective-text.md:62-74`.

| # | Atomic field | Left: RPS-D02 | Right: RPS-D03 | Status |
|---:|---|---|---|---|
| 1 | `tq005.nominal_aggregate_rate` | `1.6T` | `1.6T` | `same` |
| 2 | `tq005.reported_aggregate_or_line_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 3 | `tq005.host_lane_count` | `8` | `8` | `same` |
| 4 | `tq005.host_lane_rate` | `200G` | `200G` | `same` |
| 5 | `tq005.media_lane_count` | `8` | `8` | `same` |
| 6 | `tq005.media_lane_rate` | `200G` | `200G` | `same` |
| 7 | `tq005.modulation_format` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 8 | `tq005.symbol_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 9 | `tq005.fec_code` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 10 | `tq005.pmd_or_application_reference` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 11 | `tq005.media_type` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 12 | `tq005.reach` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 13 | `tq005.nominal_wavelength` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 14 | `tq005.wavelength_range` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 15 | `tq005.lane_organization` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 16 | `tq005.optical_connector` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 17 | `tq005.fiber_mapping` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 18 | `tq006.normalized_architecture` | `Tx-retimed / Rx-linear` | `UNKNOWN` | `unknown_right` |
| 19 | `tq006.raw_architecture_label` | `LRO` | `3 nm DSP` | `not_comparable` |
| 20 | `tq006.tx_retiming` | `retimed (transmit direction)` | `UNKNOWN` | `unknown_right` |
| 21 | `tq006.rx_retiming` | `linear (no retiming)` | `UNKNOWN` | `unknown_right` |
| 22 | `tq006.fec_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 23 | `tq006.dac_adc_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 24 | `tq006.host_serdes_role` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 25 | `tq007.platform` | `silicon photonics` | `silicon photonics` | `same` |
| 26 | `tq007.material` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 27 | `tq007.light_source_type` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 28 | `tq007.light_source_wavelength` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 29 | `tq007.light_source_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 30 | `tq007.modulator_or_emitter_type` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 31 | `tq007.detector_type` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 32 | `tq007.device_integration` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 33 | `tq007.pic_eic_integration` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 34 | `tq007.laser_pic_integration` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 35 | `tq008.placement_class` | `front-panel pluggable` | `front-panel pluggable` | `same` |
| 36 | `tq008.form_factor` | `OSFP` | `OSFP` | `same` |

Status count: `same` 8; `different` 0; `unknown_left` 0; `unknown_right` 3; `unknown_both` 24; `not_comparable` 1.

## 3. CMP-D04-D05 — 36-field status matrix

Left is RPS-D04; right is RPS-D05. All values and UNKNOWN states are from E-D04/E-D05; endpoint assignment and shared traffic are checked directly against S4. The effective seed deliberately preserves D05's `EML laser` as a raw light-source phrase and leaves the independent `modulator_or_emitter_type` UNKNOWN (`route-profile-seeds-effective.yaml:13-15,955-977`).

| # | Atomic field | Left: RPS-D04 | Right: RPS-D05 | Status |
|---:|---|---|---|---|
| 1 | `tq005.nominal_aggregate_rate` | `800 Gbps` | `800 Gbps` | `same` |
| 2 | `tq005.reported_aggregate_or_line_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 3 | `tq005.host_lane_count` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 4 | `tq005.host_lane_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 5 | `tq005.media_lane_count` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 6 | `tq005.media_lane_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 7 | `tq005.modulation_format` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 8 | `tq005.symbol_rate` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 9 | `tq005.fec_code` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 10 | `tq005.pmd_or_application_reference` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 11 | `tq005.media_type` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 12 | `tq005.reach` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 13 | `tq005.nominal_wavelength` | `UNKNOWN` | `1310 nm` | `unknown_left` |
| 14 | `tq005.wavelength_range` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 15 | `tq005.lane_organization` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 16 | `tq005.optical_connector` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 17 | `tq005.fiber_mapping` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 18 | `tq006.normalized_architecture` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 19 | `tq006.raw_architecture_label` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 20 | `tq006.tx_retiming` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 21 | `tq006.rx_retiming` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 22 | `tq006.fec_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 23 | `tq006.dac_adc_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 24 | `tq006.host_serdes_role` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 25 | `tq007.platform` | `silicon photonics` | `UNKNOWN` | `unknown_right` |
| 26 | `tq007.material` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 27 | `tq007.light_source_type` | `UNKNOWN` | `laser` (raw: `EML laser`) | `unknown_left` |
| 28 | `tq007.light_source_wavelength` | `UNKNOWN` | `1310 nm` | `unknown_left` |
| 29 | `tq007.light_source_location` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 30 | `tq007.modulator_or_emitter_type` | `MZM` | `UNKNOWN` | `unknown_right` |
| 31 | `tq007.detector_type` | `UNKNOWN` | `photodetector` | `unknown_left` |
| 32 | `tq007.device_integration` | `MZM PIC` | `UNKNOWN` | `unknown_right` |
| 33 | `tq007.pic_eic_integration` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 34 | `tq007.laser_pic_integration` | `UNKNOWN` | `UNKNOWN` | `unknown_both` |
| 35 | `tq008.placement_class` | `front-panel pluggable` | `front-panel pluggable` | `same` |
| 36 | `tq008.form_factor` | `QSFP-DD800` | `OSFP` | `different` |

Status count: `same` 2; `different` 1; `unknown_left` 4; `unknown_right` 3; `unknown_both` 26; `not_comparable` 0.

## 4. Same-instance support and physical-tree disposition

### 4.1 Verified observed differences

| Comparison | Candidate delta | Same-instance support verdict | `tree.yaml` disposition |
|---|---|---|---|
| CMP-D02-D03 | D02 is disclosed as LRO with DSP retiming only in Tx; D03 is disclosed only as incorporating next-generation 3 nm DSPs. | **Directly supported as a contrast in raw implementation descriptions** by S3 `:1979`. It is **not** a directly supported normalized-architecture, Tx/Rx-responsibility, component-removal, measured-power, or process delta. The leaf status is therefore `not_comparable`, not `different`. | **Needs candidate facets under existing C5.** C5 contains DSP/CDR-class electrical chips (`tree.yaml:65`) but is too coarse for `tx_retiming`, `rx_retiming`, FEC, DAC/ADC, host-SerDes responsibility, or a raw DSP-node attribute. Candidate facets may record `tx_retiming_scope`, `rx_retiming_scope`, and `dsp_process_node_raw`; they are not canonical cell IDs. |
| CMP-D04-D05 | QSFP-DD800 versus OSFP. | **Directly supported** by the two endpoint phrases in S4 `:1967`; both values occupy the same form-factor field and are therefore `different`. | **UNMODELED: `form_factor`.** Do not force this delta into B1, B2, or D9 (`tree.yaml:92,99-100`); those cells denote PCB, structural parts, and FAU/MPO connection, not the OSFP/QSFP-DD form-factor taxonomy. MOD1 is also only the broad direct-detect module cell (`tree.yaml:101-105`), not a form-factor cell. |
| CMP-D04-D05 | D04 is disclosed as a silicon-photonics MZM PIC endpoint; D05 is disclosed as a 1310 nm raw EML-laser/photodetector endpoint. | **Directly supported at composite endpoint-description scope** by S4 `:1966-1967`. It is not an equal-grain leaf-by-leaf comparison: D04's light source and detector are UNKNOWN, while D05's platform, independent modulator/emitter type, and integration are UNKNOWN (E-D04/E-D05). | **Existing cells plus candidate facets:** D04's SiPh PIC maps to C4; `MZM` needs a modulator-type facet under C4. D05's raw EML-laser label maps to C1, and generic photodetector maps to C3; detector subtype remains UNKNOWN. See `tree.yaml:61-65`. The composite contrast does not map cleanly to one cell and does not justify filling missing C1/C3/C4 leaves. |

S3 also says the D03 module's 3 nm DSPs are intended “to reduce power consumption” (`corpus/web/2026-08-24/coherent.com__ofc-2025-multi-technology.html:1979`). This is a same-instance company statement, but it supplies no measured value, power boundary, method, or D02 comparator. It therefore supports neither a measured power delta nor an advantage/disadvantage; the controlling text reaches the same conclusion at `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/post-adjudication-effective-text.md:51-54,94-101`.

### 4.2 Explicit mapping audits

- **Form factor:** TQ008's `front-panel pluggable` is a frozen normalization from observed OSFP/QSFP-DD, not a direct source phrase and not an internal architecture claim (`docs/research/pi-packages/2026-08-24-tq005-tq008-axis-values-v1/post-adjudication-effective-text.md:140-151,176-183`; `route-profile-seeds-effective.yaml:15-20`). D02/D03 have the same OSFP form factor. D04/D05 have different form factors, but this dimension is UNMODELED in `tree.yaml`; B1/B2/D9 are rejected mappings.
- **Electrical responsibility:** C5 is a valid coarse parent for DSP-class components, not a complete model of Tx/Rx/FEC/DAC/ADC/host-SerDes responsibility. D02's Tx-retimed/Rx-linear split is directly stated; D03's corresponding responsibilities remain UNKNOWN. No DSP deletion, full-retimed D03 architecture, FEC migration, host transfer, or power outcome is inferred (`source-discovery.md:206-210,218-219`; S3 `:1979`).
- **Photonics labels:** C4 is used only for D04's disclosed silicon-photonics MZM PIC; C1 only for D05's raw EML-laser label; C3 only for D05's generic photodetector. EML is not expanded into InP, DFB+EAM, monolithic integration, or an independent modulator field; MZM PIC does not establish PIC/EIC or laser/PIC integration; generic photodetector does not establish PIN/APD (`source-discovery.md:152-162,183-195,206-220`; `tree.yaml:61-65`).

### 4.3 Component/interface/process/equipment/test audit

| Comparison | Component | Interface | Process | Equipment | Test |
|---|---|---|---|---|---|
| CMP-D02-D03 | Raw DSP/architecture descriptions differ, but no component add/delete/count/replacement delta is established: **UNKNOWN** beyond the labels. | D02 Tx/Rx split is known and D03's is not; comparative responsibility delta: **UNKNOWN**. Shared 8x200G electrical/optical interfaces are directly supported. | D03's raw `3 nm DSP` label is supported, but D02's DSP node/fabrication process is absent; comparative process delta: **UNKNOWN**. | **UNKNOWN**. | **UNKNOWN**. The separate second demo's BER statement and the page's unrelated test-instrument section cannot be transferred to D02/D03. |
| CMP-D04-D05 | Composite endpoint labels and form factors are supported; equal-grain component replacement and internal partitioning remain **UNKNOWN**. | Interoperation at 800 Gbps is supported, but host/media lane, connector, fiber mapping, direction-specific role, and electrical-responsibility deltas are **UNKNOWN**. | D05 is described as internally designed and fabricated, while D04 fabrication responsibility is not stated; comparative process delta: **UNKNOWN**. | **UNKNOWN**. | **UNKNOWN**. Interoperation/traffic is observed, but no differing test responsibility, method, condition, or metric is disclosed. |

No process, equipment, or test **delta** is source-supported for either comparison. All such comparative deltas remain `UNKNOWN`, as required by `contract.md:53-59` and `next-round-acceptance-contracts.md:24-31`.

## 5. TQ014 comparability audit

### CMP-D02-D03

```yaml
comparison_id: CMP-D02-D03
comparison_status: partially_comparable
scenario_constraints:
  aggregate_rate: "same; 1.6T observed"
  reach: UNKNOWN
  media: UNKNOWN
  fec_ber: UNKNOWN
  temperature: UNKNOWN
  power_boundary: UNKNOWN
  density_boundary: UNKNOWN
  cost_boundary: UNKNOWN
  maintenance_boundary: UNKNOWN
advantages: []
costs_and_disadvantages: []
new_bottlenecks: []
alternatives: []
validation_questions:
  - "Obtain same-condition modulation, symbol-rate, PMD/FEC/BER, media, reach, wavelength, and connector/fiber-mapping controls."
  - "Obtain D03 Tx/Rx retiming, FEC, DAC/ADC, and host-SerDes responsibilities."
  - "Obtain measured power with a common boundary, workload, temperature, instrumentation, and uncertainty."
  - "Obtain common density/thermal, cost, reliability, and maintenance definitions."
feedback_to_tq003: []
unknowns:
  - "D03 normalized architecture and electrical responsibility"
  - "all listed non-rate/non-lane comparison controls"
no_unconditional_ranking: true
```

`partially_comparable` is limited to the directly shared group controls: 1.6T, 8x200G host and media lanes, silicon photonics, OSFP, and normalized front-panel placement (S3 `:1976-1979`; `comparison-objects.md:3-17`). It is not comparable for performance trade-offs because reach, FEC/BER, environmental, power, density, cost, maintenance, and D03 architecture controls are missing.

### CMP-D04-D05

```yaml
comparison_id: CMP-D04-D05
comparison_status: partially_comparable
scenario_constraints:
  aggregate_rate: "same link traffic; 800 Gbps observed"
  reach: UNKNOWN
  media: UNKNOWN
  fec_ber: UNKNOWN
  temperature: UNKNOWN
  power_boundary: UNKNOWN
  density_boundary: UNKNOWN
  cost_boundary: UNKNOWN
  maintenance_boundary: UNKNOWN
advantages: []
costs_and_disadvantages: []
new_bottlenecks: []
alternatives: []
validation_questions:
  - "Obtain endpoint direction/role and a symmetric test topology for an alternative-design comparison."
  - "Obtain host/media lane count and rate, modulation/symbol rate, formal PMD/FEC/BER, media, reach, wavelength range, connector, and fiber mapping for each endpoint."
  - "Obtain Tx/Rx/FEC/DAC/ADC/host-SerDes responsibilities for both endpoints."
  - "Obtain common temperature, measured power, density/thermal, cost, reliability, and maintenance boundaries."
  - "Obtain equal-grain light-source, modulator, detector, material, and integration disclosures for both endpoints."
feedback_to_tq003: []
unknowns:
  - "whether opposite interoperability endpoints are substitutable under the same directional role"
  - "all listed controls except shared 800 Gbps traffic and normalized front-panel placement"
no_unconditional_ranking: true
```

`partially_comparable` is limited to the same interoperability demonstration, shared 800 Gbps traffic, and normalized front-panel placement; form factor and endpoint implementation labels can be audited descriptively (S4 `:1966-1967`; `comparison-objects.md:19-30`). The evidence does not establish symmetric endpoint roles or any controlled performance, power, density, cost, reliability, or maintenance comparison. Accordingly, no advantages or disadvantages are recorded.

## 6. Draft-only terminal statement

- `canonical_write_performed: false`
- `coverage_status_changed: false`
- `formal_route_profiles_created: false`
- `new_question_ids_created: false`
- `company_groups_created: false`

This audit is draft-only: no canonical write, coverage change, formal Route Profile, new QID, or company group is created.
