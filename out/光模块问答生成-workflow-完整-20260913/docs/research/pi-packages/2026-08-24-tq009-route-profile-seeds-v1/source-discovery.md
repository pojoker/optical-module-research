# TQ009 Route Profile Seed source discovery

> **Status: draft-only source synthesis.** This note records evidence support and gaps for exactly five allowed instances. It does **not** create Route Profiles, mark coverage, create company groups, or perform canonical writes.

## Scope and method

- G1 fixes the five-instance boundary, minimum TQ005–TQ008 fields, allowed observation states, and no-inference rules (G1 lines 26–95).
- G2 supplies the controlling axis vocabulary. In particular, names such as `DR8`, `DR+`, and `DR4+` do not fill missing lane, FEC, wavelength, or reach fields; OSFP/QSFP-DD are form-factor labels in the front-panel-pluggable taxonomy (G2 lines 20–33, 140–151, 176–183).
- Only S1–S4 are primary evidence. G1/G2 govern scope and normalization but are not substituted for missing instance evidence.
- `observed` means a product datasheet/page or the exact demo statement directly reports the value. `company-stated` is used for same-instance platform or architecture language. `unknown` always has value `UNKNOWN`; no platform capability, adjacent demo, product-name expansion, or common knowledge fills it.
- A composite field can contain a directly reported component and an explicitly `UNKNOWN` component. Such rows retain the reported component and list the missing subfield under `missing_fields`.
- `placement_class: front-panel pluggable` is a controlled G2 taxonomy mapping from a directly reported OSFP/QSFP-DD form factor, not a claim about an unreported internal architecture.

## Source registry

### Governing texts

| ID | Role | Local frozen path | Useful anchors |
|---|---|---|---|
| G1 | Package contract | `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/contract.md` | Five instances: lines 26–36; schema: 38–75; states: 77–86; anti-inference rules: 88–95; output boundary: 107–130 |
| G2 | Controlling TQ005–TQ008 vocabulary | `docs/research/pi-packages/2026-08-24-tq005-tq008-axis-values-v1/post-adjudication-effective-text.md` | TQ005: lines 16–33; TQ006: 58–74; TQ007: 99–115; TQ008: 140–151; cross-axis guardrails: 176–183 |

### Primary evidence (fixed IDs)

| ID | Source | Local frozen path | Useful anchors |
|---|---|---|---|
| S1 | Coherent FTCE4517E1PxM product HTML | `corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_product.html` | Product title: lines 1922–1922; compliance: 1996–1996; specifications: 2443–2506 |
| S2 | Coherent FTCE4517E1PxM product specification PDF | `corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf` | Product features and description: p. 1; electrical/optical characteristics: pp. 3–4; rate/reach: p. 5; pluggable form factor: p. 6 |
| S3 | Coherent OFC 2025 demo page | `corpus/web/2026-08-24/coherent.com__ofc-2025-multi-technology.html` | Company/event statement: line 1941; exact three-demo statement: lines 1976–1979 |
| S4 | Coherent ECOC 2022 interoperability page | `corpus/web/2026-08-24/coherent.com__ecoc-2022-interoperability.html` | Company/event statement: line 1941; exact two-endpoint statement: lines 1966–1967 |

## Five allowed instance support matrices

### RPS-D01 — FTCE4517E1PxM 800G-DR8/DR+ OSFP product

- `draft_only`: `true`
- `company`: Coherent (Finisar-branded product specification)
- `product_or_demo`: `product`
- `evidence_type`: `product_datasheet`
- `source_instance`: FTCE4517E1PxM only; S1 and S2 are two frozen documents for the same exact product.

| Axis | Field | Value | Observation state | Same-instance support |
|---|---|---|---|---|
| TQ005 | `aggregate_rate` | Marketing class `800G`; reported aggregate/data rate `850 Gb/s` | `observed` | S1 lines 2453–2454, 2489–2490: “800G” and “850 Gb/s”; S2 p. 1: “Supports 850Gb/s aggregate bit rate.” |
| TQ005 | `host_lanes` | `8 × 106.25 Gb/s PAM4 electrical`; `53.125 GBd` per lane | `observed` | S2 p. 1: “8x100G PAM4 retimed 106.25Gb/s”; p. 3 gives `53.125 GBd` Tx/Rx electrical signaling. |
| TQ005 | `media_lanes` | Count `UNKNOWN`; per-lane signaling `53.125 GBd` | `observed` | S2 pp. 3–4 reports optical signaling “each lane” at `53.125 GBd` but does not directly state the optical lane count. `DR8` is not expanded to fill it. |
| TQ005 | `modulation` | `PAM4`, `53.125 GBd` per optical lane | `observed` | S2 pp. 3–4: “Modulation format PAM4” and `53.125 ... GBd`. |
| TQ005 | `fec_pmd` | PMD/reference: `400GBASE-DR4` in a two-application configuration; FEC code `UNKNOWN` | `observed` | S2 p. 1: “2 x 400 DR4 applications with FEC”; p. 3: “Meets 400GBASE-DR4.” No FEC code is named. |
| TQ005 | `media` | `SMF`, G.652 | `observed` | S1 lines 2485–2486: “Single SMF”; S2 p. 5: “SMF per G.652.” |
| TQ005 | `reach` | `500 m` | `observed` | S1 lines 2449–2450: “500 m”; S2 pp. 1 and 5 report up to/maximum `500m`. |
| TQ005 | `wavelength_organization` | Parallel MPO-16; lane wavelength `1304.5–1317.5 nm` (`1310 nm` product value) | `observed` | S2 p. 1: “Parallel MPO-16 receptacle”; pp. 3–4 give `1304.5 to 1317.5 nm`; S1 lines 2481–2482 and 2505–2506 give MPO16 and `1310 nm`. |
| TQ006 | `architecture` | `retimed` raw architecture label; detailed Tx/Rx and FEC responsibility split `UNKNOWN` | `company-stated` | S2 p. 1: “8x100G PAM4 retimed ... electrical interface.” The document does not separately diagram Tx/Rx responsibilities. |
| TQ007 | `platform_material` | `UNKNOWN` | `unknown` | S1/S2 do not report the product platform/material. EML is not expanded to InP. |
| TQ007 | `light_source` | `UNKNOWN` | `unknown` | S1 reports the transmitter as EML but does not identify DFB, external, integrated, or on-chip light-source architecture. |
| TQ007 | `modulator_emitter` | `EML` | `observed` | S1 lines 2477–2478: transmitter “EML.” |
| TQ007 | `detector` | `PIN` | `observed` | S1 lines 2465–2466: receiver “PIN.” |
| TQ007 | `integration` | `UNKNOWN` | `unknown` | S1/S2 do not report device/PIC/EIC/light-source integration. |
| TQ008 | `placement_class` | `front-panel pluggable` | `observed` | S1 line 1922 directly says “Hot Pluggable Optical Transceiver”; S2 pp. 1 and 6 identify a hot-pluggable OSFP form factor. G2 supplies the controlled class name. |
| TQ008 | `form_factor` | `OSFP` | `observed` | S1 lines 2457–2458: “OSFP”; S2 p. 1: “Hot-pluggable OSFP form factor.” |

- `alias_labels`: `800G-DR+` (S1 line 1922); `800G-DR8`/`DR8` (S2 pp. 1, 5–6).
- `missing_fields`: `tq005.media_lanes.count`, `tq005.fec_pmd.fec_code`, `tq006.architecture.tx_rx_responsibility_detail`, `tq007.platform_material`, `tq007.light_source`, `tq007.integration`.
- `promotion_blockers`: marketed `800G` versus reported `850 Gb/s` needs a stable nominal-versus-line-rate convention; `DR+` versus `DR8` naming needs reconciliation; exact FEC and optical lane count are not directly reported; retiming responsibilities are not diagrammed; TQ007 platform/light-source/integration remain missing.
- `would_create_route_profile`: `false`
- `would_mark_covered`: `false`

### RPS-D02 — OFC 2025 1.6T-DR8 OSFP SiPh LRO demo

- `draft_only`: `true`
- `company`: Coherent
- `product_or_demo`: `demo_endpoint`
- `evidence_type`: `company_demo_statement`
- `source_instance`: the first of the three 1.6T-DR8 modules in S3 line 1979.

| Axis | Field | Value | Observation state | Same-instance support |
|---|---|---|---|---|
| TQ005 | `aggregate_rate` | `1.6T` | `observed` | S3 lines 1976–1979: “1.6T-DR8 transceiver modules.” |
| TQ005 | `host_lanes` | `8 × 200G electrical` | `observed` | S3 line 1979: “8x200G ... electrical interfaces.” |
| TQ005 | `media_lanes` | `8 × 200G optical` | `observed` | S3 line 1979: “8x200G optical ... interfaces.” |
| TQ005 | `modulation` | `UNKNOWN` | `unknown` | S3 does not state modulation format or symbol rate. `200G` is not converted into PAM4/baud. |
| TQ005 | `fec_pmd` | `UNKNOWN` | `unknown` | `1.6T-DR8` is retained as an alias; S3 gives no formal PMD or FEC. |
| TQ005 | `media` | `UNKNOWN` | `unknown` | S3 does not state fiber/media type. |
| TQ005 | `reach` | `UNKNOWN` | `unknown` | S3 does not state reach. `DR8` is not expanded to fill it. |
| TQ005 | `wavelength_organization` | `UNKNOWN` | `unknown` | S3 gives neither wavelength nor parallel/WDM mapping. |
| TQ006 | `architecture` | `Tx-retimed / Rx-linear`; raw label `LRO` | `company-stated` | S3 line 1979: “linear receive optics (LRO)” and DSP “retiming only in the transmit direction.” |
| TQ007 | `platform_material` | `silicon photonics` | `company-stated` | S3 line 1979: “silicon photonics architecture.” |
| TQ007 | `light_source` | `UNKNOWN` | `unknown` | S3 does not state light-source type or location. |
| TQ007 | `modulator_emitter` | `UNKNOWN` | `unknown` | S3 does not identify a modulator/emitter. |
| TQ007 | `detector` | `UNKNOWN` | `unknown` | S3 does not identify a detector. “Linear receive optics” is not expanded to a detector type. |
| TQ007 | `integration` | `UNKNOWN` | `unknown` | S3 does not report device/PIC/EIC/light-source integration. |
| TQ008 | `placement_class` | `front-panel pluggable` | `observed` | S3 line 1979 directly reports OSFP; G2 maps OSFP into the front-panel-pluggable class. |
| TQ008 | `form_factor` | `OSFP` | `observed` | S3 line 1979: “common OSFP form factor.” |

- `alias_labels`: `1.6T-DR8`, `LRO`.
- `missing_fields`: `tq005.modulation`, `tq005.fec_pmd`, `tq005.media`, `tq005.reach`, `tq005.wavelength_organization`, `tq007.light_source`, `tq007.modulator_emitter`, `tq007.detector`, `tq007.integration`.
- `promotion_blockers`: no exact modulation/FEC/PMD/media/reach/wavelength disclosure; no light-source/modulator/detector/integration disclosure; host FEC and SerDes responsibilities are not stated even though the Tx/Rx retiming split is.
- `would_create_route_profile`: `false`
- `would_mark_covered`: `false`

### RPS-D03 — OFC 2025 1.6T-DR8 OSFP SiPh 3 nm DSP demo

- `draft_only`: `true`
- `company`: Coherent
- `product_or_demo`: `demo_endpoint`
- `evidence_type`: `company_demo_statement`
- `source_instance`: the third of the three 1.6T-DR8 modules in S3 line 1979; it is not spliced with the first or second module.

| Axis | Field | Value | Observation state | Same-instance support |
|---|---|---|---|---|
| TQ005 | `aggregate_rate` | `1.6T` | `observed` | S3 line 1979 says all three are “1.6T-DR8 transceiver modules.” |
| TQ005 | `host_lanes` | `8 × 200G electrical` | `observed` | S3 line 1979 says the three modules share “8x200G ... electrical interfaces.” |
| TQ005 | `media_lanes` | `8 × 200G optical` | `observed` | S3 line 1979 says the three modules share “8x200G optical ... interfaces.” |
| TQ005 | `modulation` | `UNKNOWN` | `unknown` | S3 does not state modulation format or symbol rate. |
| TQ005 | `fec_pmd` | `UNKNOWN` | `unknown` | `1.6T-DR8` is an alias only; S3 gives no formal PMD or FEC. |
| TQ005 | `media` | `UNKNOWN` | `unknown` | S3 does not state fiber/media type. |
| TQ005 | `reach` | `UNKNOWN` | `unknown` | S3 does not state reach. |
| TQ005 | `wavelength_organization` | `UNKNOWN` | `unknown` | S3 gives neither wavelength nor parallel/WDM mapping. |
| TQ006 | `architecture` | `UNKNOWN` | `unknown` | S3 line 1979 only says the third demo “incorporates ... 3 nm digital signal processors.” It does not disclose Tx/Rx retiming, Rx architecture, FEC location, or host SerDes responsibility. **A DSP mention does not establish full-retimed architecture.** Raw label: `3 nm DSP`. |
| TQ007 | `platform_material` | `silicon photonics` | `company-stated` | S3 line 1979 says the three modules share a “silicon photonics architecture.” |
| TQ007 | `light_source` | `UNKNOWN` | `unknown` | S3 does not state light-source type or location. |
| TQ007 | `modulator_emitter` | `UNKNOWN` | `unknown` | S3 does not identify a modulator/emitter. |
| TQ007 | `detector` | `UNKNOWN` | `unknown` | S3 does not identify a detector. |
| TQ007 | `integration` | `UNKNOWN` | `unknown` | S3 does not report device/PIC/EIC/light-source integration. |
| TQ008 | `placement_class` | `front-panel pluggable` | `observed` | S3 line 1979 directly reports OSFP; G2 maps OSFP into the front-panel-pluggable class. |
| TQ008 | `form_factor` | `OSFP` | `observed` | S3 line 1979: “common OSFP form factor.” |

- `alias_labels`: `1.6T-DR8`, `3 nm DSP` (the source text later contains the typo `DPSs`).
- `missing_fields`: `tq005.modulation`, `tq005.fec_pmd`, `tq005.media`, `tq005.reach`, `tq005.wavelength_organization`, `tq006.architecture`, `tq007.light_source`, `tq007.modulator_emitter`, `tq007.detector`, `tq007.integration`.
- `promotion_blockers`: **3 nm DSP architecture is UNKNOWN**; Rx retiming, Tx retiming, FEC placement, and host SerDes responsibility are unreported; exact modulation/FEC/PMD/media/reach/wavelength and most TQ007 implementation fields are missing.
- `would_create_route_profile`: `false`
- `would_mark_covered`: `false`

### RPS-D04 — ECOC 2022 800G-DR8+ QSFP-DD800 SiPh MZM PIC interoperability endpoint

- `draft_only`: `true`
- `company`: Coherent
- `product_or_demo`: `demo_endpoint`
- `evidence_type`: `company_demo_statement`
- `source_instance`: the QSFP-DD800 silicon-photonics MZM-PIC endpoint only in S4 line 1967.

| Axis | Field | Value | Observation state | Same-instance support |
|---|---|---|---|---|
| TQ005 | `aggregate_rate` | `800 Gbps` | `observed` | S4 line 1967: “The modules carry 800 Gbps traffic.” |
| TQ005 | `host_lanes` | `UNKNOWN` | `unknown` | S4 does not report host electrical lane count/rate. |
| TQ005 | `media_lanes` | `UNKNOWN` | `unknown` | S4 does not directly report optical lane count/rate; `DR8+`/`DR4+` names are not expanded. |
| TQ005 | `modulation` | `UNKNOWN` | `unknown` | S4 does not report modulation format or symbol rate for this endpoint. |
| TQ005 | `fec_pmd` | `UNKNOWN` | `unknown` | `800G-DR8+` and `2x400G-DR4+` remain aliases; no formal PMD or FEC is stated. |
| TQ005 | `media` | `UNKNOWN` | `unknown` | S4 does not state fiber/media type. |
| TQ005 | `reach` | `UNKNOWN` | `unknown` | S4 does not state reach. |
| TQ005 | `wavelength_organization` | `UNKNOWN` | `unknown` | The `1310 nm` phrase modifies the opposite EML endpoint. Interoperability is not used to transfer wavelength or organization to this endpoint. |
| TQ006 | `architecture` | `UNKNOWN` | `unknown` | S4 does not state DSP, linear, retimed, or Tx/Rx responsibility for this endpoint. |
| TQ007 | `platform_material` | `silicon photonics` | `company-stated` | S4 line 1967: “silicon photonics MZM PIC.” |
| TQ007 | `light_source` | `UNKNOWN` | `unknown` | S4 does not identify the SiPh endpoint’s light source. |
| TQ007 | `modulator_emitter` | `MZM` | `observed` | S4 line 1967 directly calls it an “MZM PIC.” |
| TQ007 | `detector` | `UNKNOWN` | `unknown` | The photodetector phrase modifies the opposite EML endpoint and is not transferred. |
| TQ007 | `integration` | `MZM PIC`; all finer PIC/EIC/light-source integration `UNKNOWN` | `company-stated` | S4 line 1967 directly states an internally designed “silicon photonics MZM PIC,” but supplies no block diagram. |
| TQ008 | `placement_class` | `front-panel pluggable` | `observed` | S4 line 1967 directly reports QSFP-DD800; G2 maps QSFP-DD into the front-panel-pluggable class. |
| TQ008 | `form_factor` | `QSFP-DD800` | `observed` | S4 line 1967: “QSFP-DD800 transceiver module.” |

- `alias_labels`: `800G-DR8+`, `2x400G-DR4+`.
- `missing_fields`: `tq005.host_lanes`, `tq005.media_lanes`, `tq005.modulation`, `tq005.fec_pmd`, `tq005.media`, `tq005.reach`, `tq005.wavelength_organization`, `tq006.architecture`, `tq007.light_source`, `tq007.detector`, `tq007.integration.finer_structure`.
- `promotion_blockers`: most TQ005 external-link details are absent; architecture is absent; light source and detector are absent; MZM-PIC internal partitioning is not disclosed. The opposite endpoint cannot supply these fields.
- `would_create_route_profile`: `false`
- `would_mark_covered`: `false`

### RPS-D05 — ECOC 2022 800G-DR8+ OSFP EML/photodetector interoperability endpoint

- `draft_only`: `true`
- `company`: Coherent
- `product_or_demo`: `demo_endpoint`
- `evidence_type`: `company_demo_statement`
- `source_instance`: the OSFP 1310 nm EML/photodetector endpoint only in S4 line 1967.

| Axis | Field | Value | Observation state | Same-instance support |
|---|---|---|---|---|
| TQ005 | `aggregate_rate` | `800 Gbps` | `observed` | S4 line 1967: “The modules carry 800 Gbps traffic.” |
| TQ005 | `host_lanes` | `UNKNOWN` | `unknown` | S4 does not report host electrical lane count/rate. |
| TQ005 | `media_lanes` | `UNKNOWN` | `unknown` | S4 does not directly report optical lane count/rate; `DR8+`/`DR4+` names are not expanded. |
| TQ005 | `modulation` | `UNKNOWN` | `unknown` | S4 does not report modulation format or symbol rate for this endpoint. |
| TQ005 | `fec_pmd` | `UNKNOWN` | `unknown` | `800G-DR8+` and `2x400G-DR4+` remain aliases; no formal PMD or FEC is stated. |
| TQ005 | `media` | `UNKNOWN` | `unknown` | S4 does not state fiber/media type. |
| TQ005 | `reach` | `UNKNOWN` | `unknown` | S4 does not state reach. |
| TQ005 | `wavelength_organization` | Wavelength `1310 nm`; parallel/WDM and lane/fiber mapping `UNKNOWN` | `observed` | S4 line 1967: “1310 nm EML lasers.” No organization or mapping is given. |
| TQ006 | `architecture` | `UNKNOWN` | `unknown` | S4 does not state DSP, linear, retimed, or Tx/Rx responsibility for this endpoint. |
| TQ007 | `platform_material` | `UNKNOWN` | `unknown` | S4 does not state this endpoint’s platform/material. EML is not expanded to InP. |
| TQ007 | `light_source` | `1310 nm EML lasers`; DFB/external/integrated/on-chip detail `UNKNOWN` | `observed` | S4 line 1967 directly says “1310 nm EML lasers.” The adjacent, separate 200G EML demo at line 1965 is not imported. |
| TQ007 | `modulator_emitter` | `EML` | `observed` | S4 line 1967: “EML lasers.” No EAM substructure is inferred. |
| TQ007 | `detector` | Generic `photodetectors` | `observed` | S4 line 1967 directly says “photodetectors”; detector subtype is not reported. |
| TQ007 | `integration` | `UNKNOWN` | `unknown` | “Internally designed and fabricated” does not state monolithic, on-chip, hybrid, or PIC/EIC integration. |
| TQ008 | `placement_class` | `front-panel pluggable` | `observed` | S4 line 1967 directly reports OSFP; G2 maps OSFP into the front-panel-pluggable class. |
| TQ008 | `form_factor` | `OSFP` | `observed` | S4 line 1967: “800G-DR8+ OSFP module.” |

- `alias_labels`: `800G-DR8+`, `2x400G-DR4+`.
- `missing_fields`: `tq005.host_lanes`, `tq005.media_lanes`, `tq005.modulation`, `tq005.fec_pmd`, `tq005.media`, `tq005.reach`, `tq005.wavelength_organization.organization_and_mapping`, `tq006.architecture`, `tq007.platform_material`, `tq007.light_source.substructure_and_location`, `tq007.detector.subtype`, `tq007.integration`.
- `promotion_blockers`: most TQ005 external-link details are absent; architecture is absent; platform/material and integration are absent; light-source and detector subtypes are incomplete. The adjacent 200G EML demo and the opposite SiPh endpoint cannot fill these gaps.
- `would_create_route_profile`: `false`
- `would_mark_covered`: `false`

## Observed/company-stated versus inference

No inferred value is used to fill a seed field.

- Direct product/demo quantities, components, and form factors are `observed`.
- Same-instance architecture/platform descriptions (`retimed`, `LRO`, `silicon photonics`, `MZM PIC`) are `company-stated` where they characterize implementation rather than merely enumerate a measured field.
- The G2 mapping from observed OSFP/QSFP-DD to `front-panel pluggable` is an explicit controlled taxonomy normalization. It does not infer TQ005, TQ006, or TQ007 values.
- Shared descriptors in S3—1.6T-DR8, OSFP, 8×200G optical/electrical, and SiPh—apply to the three modules because S3 directly says they are shared. The first module’s LRO/Tx-retimed statement is not transferred to the third module.
- Shared 800 Gbps traffic in S4 applies to both endpoints because the sentence says “The modules.” Internal architecture, wavelength, detector, and platform details remain endpoint-specific.
- `DR8`, `DR8+`, `DR4+`, and `DR+` remain raw/alias labels. They do not supply FEC, lane count, media, reach, or wavelength organization.
- EML does not supply InP, DFB+EAM, or monolithic integration unless the exact instance states those values. S4 line 1965 describes a different 200G EML demo and is not spliced into RPS-D05.
- The 3 nm DSP demo architecture is `UNKNOWN`; it is not labeled full-retimed.

## Ambiguities and conflicts

1. **FTCE nominal versus aggregate rate:** S1 markets the product as `800G` but also lists `850 Gb/s`; S2 calls it an 800G product and reports support for `850Gb/s aggregate bit rate` (S1 lines 2453–2454 and 2489–2490; S2 p. 1). Both are retained without adjudicating nominal versus encoded/line rate.
2. **FTCE route label:** S1 uses `800G-DR+`; S2 uses `800G-DR8`/`DR8`. They are retained as aliases, not silently treated as one formal PMD.
3. **FTCE PDF metadata:** the PDF metadata title is `FTRJ-8519-1 Specifications`, while the document body and filename identify `FTCE4517E1PxM` (S2 metadata and p. 1). The body is used for instance evidence; the metadata mismatch is a provenance caution.
4. **FTCE retiming scope:** S2 says “retimed” but does not separately state Tx/Rx/FEC responsibilities. The raw architecture label is supported; finer responsibility allocation remains `UNKNOWN`.
5. **OFC three-demo sentence:** S3 clearly assigns LRO/Tx-only retiming to the first demo and 3 nm DSPs to the third. It does not say whether the third demo retimes Tx, Rx, both, or neither; nor where FEC resides (S3 line 1979).
6. **OFC source typo:** S3 line 1979 writes `DPSs` after spelling out digital signal processors. This note normalizes only the obvious abbreviation to `DSPs`; it does not infer architecture.
7. **ECOC endpoint asymmetry:** `1310 nm EML lasers and photodetectors` grammatically modifies only the OSFP endpoint. It is not applied to the QSFP-DD800 SiPh endpoint (S4 line 1967).
8. **ECOC naming scope:** `800G-DR8+` and `2x400G-DR4+` are company demo labels/configurations, not enough evidence for a formal PMD, FEC, lane count, reach, or wavelength organization.

## Cross-seed comparison

This table compares evidence completeness only; it does not rank routes, maturity, or companies.

| Seed | Observed/company-stated minimum fields | Fields or subfields remaining `UNKNOWN` |
|---|---|---|
| RPS-D01 | aggregate rate; host lanes; optical lane rate; modulation; PMD/reference; media; reach; wavelength organization; retimed raw architecture; EML; PIN; placement/form factor | optical lane count; FEC code; detailed Tx/Rx/FEC responsibility; platform/material; light source; integration |
| RPS-D02 | aggregate rate; host/media lanes; Tx-retimed/Rx-linear; silicon photonics; placement/form factor | modulation; FEC/PMD; media; reach; wavelength organization; light source; modulator/emitter; detector; integration |
| RPS-D03 | aggregate rate; host/media lanes; silicon photonics; placement/form factor | modulation; FEC/PMD; media; reach; wavelength organization; **architecture**; light source; modulator/emitter; detector; integration |
| RPS-D04 | aggregate rate; silicon photonics; MZM; MZM-PIC label; placement/form factor | host/media lanes; modulation; FEC/PMD; media; reach; wavelength organization; architecture; light source; detector; finer integration |
| RPS-D05 | aggregate rate; 1310 nm; EML laser; generic photodetector; placement/form factor | host/media lanes; modulation; FEC/PMD; media; reach; wavelength organization/mapping; architecture; platform/material; light-source detail; detector subtype; integration |

## Follow-up questions without new QID

- `parent_question_id: TQ009` — Which exact-instance product specification or demo block diagram can fill every currently `UNKNOWN` TQ005–TQ008 field without importing platform-level or adjacent-demo claims?
- `parent_question_id: TQ010` — Once missing axis values are directly evidenced, what explicit physical-grid requirements are needed before any seed can become a capability-match candidate?
- `parent_question_id: TQ011` — What first-party evidence would directly connect an exact product/demo instance to a route service without relying on supply/customer edges or creating a company route group?

## Draft-only terminal status

- `formal_route_profiles_created: false`
- `coverage_status_changed: false`
- `companies_groups_created: false`
- `canonical_write_performed: false`

This source-discovery note is draft-only. It creates no Route Profile, no coverage, no companies group, and no canonical write.
