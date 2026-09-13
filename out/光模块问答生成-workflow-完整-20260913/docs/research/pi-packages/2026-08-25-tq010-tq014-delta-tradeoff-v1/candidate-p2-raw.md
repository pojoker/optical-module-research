```yaml
meta:
  generator_id: P2
  mode: draft_only
  canonical_write_performed: false
physical_delta_candidates:
  - delta_id: P2-D02D03-01
    comparison_id: CMP-D02-D03
    basis_fields:
      - tq006_electrical_responsibility.raw_architecture_label
    left_observation: 'D02 raw label LRO; normalized architecture Tx-retimed / Rx-linear (company-stated, S3#D02)'
    right_observation: 'D03 raw label "3 nm DSP"; normalized architecture UNKNOWN (company-stated raw label only, S3#D03)'
    delta_status: unknown
    existing_physical_cells:
      - C5
    candidate_facets:
      - tx_retiming_scope
      - rx_retiming_scope
      - dsp_process_node_raw
    unmodeled_dimension: electrical_responsibility
    component_delta: 'UNKNOWN: LRO (electrical-architecture label) and 3 nm DSP (component/process-node label) answer different field-level questions; no equal-grain component add/delete/count/replacement delta is established.'
    interface_delta: 'No delta observed on shared 8x200G host/media lane interface fields; D03 Tx/Rx electrical responsibility split is UNKNOWN.'
    process_delta: UNKNOWN
    equipment_delta: UNKNOWN
    test_delta: UNKNOWN
    evidence_refs:
      - S3#D02
      - S3#D03
  - delta_id: P2-D04D05-01
    comparison_id: CMP-D04-D05
    basis_fields:
      - tq008_placement.form_factor
    left_observation: 'QSFP-DD800 (observed, S4#D04)'
    right_observation: 'OSFP (observed, S4#D05)'
    delta_status: observed_difference
    existing_physical_cells: []
    candidate_facets: []
    unmodeled_dimension: form_factor
    component_delta: UNKNOWN
    interface_delta: 'UNKNOWN: only shared 800 Gbps link traffic is observed; no host/media lane, connector, or fiber-mapping delta is established.'
    process_delta: UNKNOWN
    equipment_delta: UNKNOWN
    test_delta: UNKNOWN
    evidence_refs:
      - S4#D04
      - S4#D05
  - delta_id: P2-D04D05-02
    comparison_id: CMP-D04-D05
    basis_fields:
      - tq007_photonics.platform
      - tq007_photonics.modulator_or_emitter_type
      - tq007_photonics.device_integration
      - tq007_photonics.light_source_type
      - tq007_photonics.light_source_wavelength
      - tq007_photonics.detector_type
    left_observation: 'D04 disclosed as silicon-photonics MZM PIC endpoint (S4#D04)'
    right_observation: 'D05 disclosed as 1310 nm raw EML-laser label plus generic photodetector endpoint (S4#D05)'
    delta_status: unknown
    existing_physical_cells:
      - C1
      - C3
      - C4
    candidate_facets:
      - mzm_modulator_type
      - eml_laser_raw
    unmodeled_dimension: photonic_device_detail
    component_delta: 'Composite endpoint implementation descriptions differ at descriptor scope, but equal-grain component delta is UNKNOWN (D04 light source and detector are UNKNOWN; D05 platform, independent modulator/emitter type, and integration are UNKNOWN).'
    interface_delta: UNKNOWN
    process_delta: UNKNOWN
    equipment_delta: UNKNOWN
    test_delta: UNKNOWN
    evidence_refs:
      - S4#D04
      - S4#D05
tradeoff_cards:
  - comparison_id: CMP-D02-D03
    comparison_status: partially_comparable
    scenario_constraints:
      aggregate_rate: 'same; 1.6T observed'
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
      - 'Obtain same-condition modulation, symbol-rate, PMD/FEC/BER, media, reach, wavelength, and connector/fiber-mapping controls.'
      - 'Obtain D03 Tx/Rx retiming, FEC, DAC/ADC, and host-SerDes responsibilities.'
      - 'Obtain measured power with a common boundary, workload, temperature, instrumentation, and uncertainty.'
      - 'Obtain common density/thermal, cost, reliability, and maintenance definitions.'
    feedback_to_tq003: []
    unknowns:
      - 'D03 normalized architecture and electrical responsibility'
      - 'all listed non-rate/non-lane comparison controls'
    no_unconditional_ranking: true
  - comparison_id: CMP-D04-D05
    comparison_status: partially_comparable
    scenario_constraints:
      aggregate_rate: 'same link traffic; 800 Gbps observed'
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
      - 'Obtain endpoint direction/role and a symmetric test topology for an alternative-design comparison.'
      - 'Obtain host/media lane count and rate, modulation/symbol rate, formal PMD/FEC/BER, media, reach, wavelength range, connector, and fiber mapping for each endpoint.'
      - 'Obtain Tx/Rx/FEC/DAC/ADC/host-SerDes responsibilities for both endpoints.'
      - 'Obtain common temperature, measured power, density/thermal, cost, reliability, and maintenance boundaries.'
      - 'Obtain equal-grain light-source, modulator, detector, material, and integration disclosures for both endpoints.'
    feedback_to_tq003: []
    unknowns:
      - 'whether opposite interoperability endpoints are substitutable under the same directional role'
      - 'all listed controls except shared 800 Gbps traffic and normalized front-panel placement'
    no_unconditional_ranking: true
capability_requirement_candidates:
  - requirement_id: P2-REQ-D02D03-01
    comparison_id: CMP-D02-D03
    basis_type: axis_direct
    basis_fields:
      - tq006_electrical_responsibility.normalized_architecture
      - tq006_electrical_responsibility.tx_retiming
      - tq006_electrical_responsibility.rx_retiming
    target_physical_cell: C5
    candidate_facet: tx_retimed_rx_linear
    capability_action: design
    requirement_statement: 'Design the DSP-class electrical chip responsibility such that Tx is retimed and Rx is linear, as disclosed for D02; D03 corresponding responsibilities remain UNKNOWN and are not inferred.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover Tx/Rx retiming and electrical-responsibility scope at electrical-chip level; no company matching is performed.'
    evidence_refs:
      - S3#D02
  - requirement_id: P2-REQ-D02D03-02
    comparison_id: CMP-D02-D03
    basis_type: axis_direct
    basis_fields:
      - tq006_electrical_responsibility.raw_architecture_label
    target_physical_cell: C5
    candidate_facet: dsp_process_node_raw
    capability_action: integrate
    requirement_statement: 'Integrate a DSP-class electrical chip whose raw disclosed label is 3 nm DSP; the raw label is recorded without asserting a comparative process or fabrication delta.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover a raw DSP process-node label; no company matching is performed.'
    evidence_refs:
      - S3#D03
  - requirement_id: P2-REQ-D04D05-01
    comparison_id: CMP-D04-D05
    basis_type: delta_direct
    basis_fields:
      - tq008_placement.form_factor
    target_physical_cell: UNMODELED
    candidate_facet: null
    capability_action: integrate
    requirement_statement: 'Integrate front-panel pluggable modules in both OSFP and QSFP-DD800 form factors as observed at the two endpoints of the same interoperability demonstration; the form-factor dimension has no canonical physical cell.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover module placement/form factor (OSFP, QSFP-DD800); no company matching is performed.'
    evidence_refs:
      - S4#D04
      - S4#D05
  - requirement_id: P2-REQ-D04D05-02
    comparison_id: CMP-D04-D05
    basis_type: axis_direct
    basis_fields:
      - tq007_photonics.platform
      - tq007_photonics.modulator_or_emitter_type
      - tq007_photonics.device_integration
    target_physical_cell: C4
    candidate_facet: mzm_modulator_type
    capability_action: integrate
    requirement_statement: 'Integrate a silicon-photonics PIC bearing an MZM modulator per D04 disclosed MZM PIC; PIC/EIC and laser/PIC integration remain UNKNOWN.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover photonic platform (silicon photonics), modulator type (MZM), and device integration (PIC); no company matching is performed.'
    evidence_refs:
      - S4#D04
  - requirement_id: P2-REQ-D04D05-03
    comparison_id: CMP-D04-D05
    basis_type: axis_direct
    basis_fields:
      - tq007_photonics.light_source_type
      - tq007_photonics.light_source_wavelength
    target_physical_cell: C1
    candidate_facet: eml_laser_raw
    capability_action: integrate
    requirement_statement: 'Integrate a 1310 nm laser light source as disclosed by the raw label EML laser for D05; the raw label is not expanded into internal emitter structure or an independent modulator field.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover light-source type and wavelength; no company matching is performed.'
    evidence_refs:
      - S4#D05
  - requirement_id: P2-REQ-D04D05-04
    comparison_id: CMP-D04-D05
    basis_type: axis_direct
    basis_fields:
      - tq007_photonics.detector_type
    target_physical_cell: C3
    candidate_facet: null
    capability_action: integrate
    requirement_statement: 'Integrate a generic photodetector as disclosed for D05; detector subtype remains UNKNOWN and is not inferred.'
    acceptance_metric_state: observed
    existing_points_matchable: partial
    match_basis: 'Could be grounded by a point whose evidence fields cover detector type; no company matching is performed.'
    evidence_refs:
      - S4#D05
validation_questions:
  - comparison_id: CMP-D02-D03
    related_field: tq006_electrical_responsibility.raw_architecture_label
    related_requirement_id: P2-REQ-D02D03-01
    question: 'Does D03 disclose a normalized electrical architecture and Tx/Rx retiming responsibilities, permitting a same-dimension comparison with D02 Tx-retimed/Rx-linear split?'
  - comparison_id: CMP-D02-D03
    related_field: tq005_external_link.reach
    question: 'What reach, media, PMD/FEC/BER, wavelength, and connector/fiber-mapping conditions apply to both D02 and D03?'
  - comparison_id: CMP-D02-D03
    related_field: tq007_photonics.light_source_type
    question: 'What are D02 light-source type, wavelength, modulator/emitter type, detector type, and integration disclosures?'
  - comparison_id: CMP-D04-D05
    related_field: tq008_placement.form_factor
    related_requirement_id: P2-REQ-D04D05-01
    question: 'Under what test topology and directional roles are the OSFP and QSFP-DD800 endpoints exercised, and do these roles permit symmetric interchange?'
  - comparison_id: CMP-D04-D05
    related_field: tq007_photonics.light_source_wavelength
    related_requirement_id: P2-REQ-D04D05-03
    question: 'What are D04 light-source type and wavelength, so that an equal-grain light-source comparison with D05 1310 nm raw EML laser is possible?'
  - comparison_id: CMP-D04-D05
    related_field: tq007_photonics.detector_type
    question: 'What is D04 detector type and D05 detector subtype, to enable equal-grain detector comparison?'
```
