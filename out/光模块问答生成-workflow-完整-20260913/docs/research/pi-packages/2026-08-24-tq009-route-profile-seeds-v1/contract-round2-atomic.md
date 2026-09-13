# TQ009 第二轮：原子字段重排合同

## 1. 目标

仅将第一轮五个同实例种子重排为原子字段；不补来源、不补事实、不改变实例边界。

第一轮裁决：`adjudication-round1.md`。证据边界：`source-discovery.md`。

## 2. 强制状态

- exactly 5 seeds: `RPS-D01`–`RPS-D05`
- draft only: true
- new sources: forbidden
- inferred fill: forbidden
- formal RP / coverage / canonical / new QID: forbidden
- TQ014 trade-off claims: forbidden in this round
- company capability or service groups: forbidden

## 3. 统一叶字段结构

每个叶字段必须严格为：

```yaml
field_name:
  value: value-or-UNKNOWN
  observation_state: observed | company-stated | unknown
  source_ids: []
```

规则：

- `observation_state: unknown` 时 `value` 必须严格等于 `UNKNOWN`，`source_ids` 必须为空；
- 非 unknown 叶字段的 `value` 不得包含字符串 `UNKNOWN`；
- 一个叶字段不得同时表达已知和未知子信息；
- alias/raw label 与规范化值分开；
- 不得因拆字段而补充 source-discovery 未支持的事实。

## 4. 原子 schema

```yaml
axes:
  tq005_external_link:
    nominal_aggregate_rate: observation
    reported_aggregate_or_line_rate: observation
    host_lane_count: observation
    host_lane_rate: observation
    media_lane_count: observation
    media_lane_rate: observation
    modulation_format: observation
    symbol_rate: observation
    fec_code: observation
    pmd_or_application_reference: observation
    media_type: observation
    reach: observation
    wavelength: observation
    lane_organization: observation
    optical_connector: observation
    fiber_mapping: observation
  tq006_electrical_responsibility:
    normalized_architecture: observation
    raw_architecture_label: observation
    tx_retiming: observation
    rx_retiming: observation
    fec_location: observation
    dac_adc_location: observation
    host_serdes_role: observation
  tq007_photonics:
    platform: observation
    material: observation
    light_source_type: observation
    light_source_wavelength: observation
    light_source_location: observation
    modulator_or_emitter_type: observation
    detector_type: observation
    device_integration: observation
    pic_eic_integration: observation
    laser_pic_integration: observation
  tq008_placement:
    placement_class: observation
    form_factor: observation
```

`observation` 代表第 3 节统一叶结构，不是字符串。

## 5. 输出

1. 一个 YAML fenced block，顶层 `route_profile_seeds`，内含五个种子；
2. 每个种子保留 `source_instance`、`company`、`product_or_demo`、`evidence_type`、`alias_labels`、`promotion_blockers`；
3. `missing_fields` 必须由所有 unknown 叶字段路径机械列出；
4. 末尾给 `atomicity_self_check`：
   - `known_value_contains_UNKNOWN: false`
   - `unknown_value_not_exact_UNKNOWN: false`
   - `cross_instance_splicing: false`
   - `formal_route_profiles_created: false`
   - `coverage_status_changed: false`
   - `canonical_write_performed: false`

## 6. 失败条件

- 少于或多于 5 个种子；
- 省略 schema 中任何叶字段；
- 非 unknown 值中包含 UNKNOWN；
- unknown 值不是严格 `UNKNOWN`；
- 改变证据边界或补入新事实；
- 进入路线优劣、Why、公司匹配、正式 RP 或 canonical。
