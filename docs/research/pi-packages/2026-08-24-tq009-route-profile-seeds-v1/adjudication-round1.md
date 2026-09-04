# TQ009 第一轮裁决

## 结论

- process: `pass`
- evidence boundary: `pass`
- seed count and identity: `pass`
- no cross-instance splicing: `pass`
- no canonical/coverage/formal RP/company group: `pass`
- schema atomicity: `changes_required`

Pi 生成了 5 个且仅 5 个种子，保留了 UNKNOWN，也正确拒绝把 3 nm DSP 演示写成 full-retimed。内容边界可用，但首轮 schema 不能作为最终 controlling text。

## 机械检查

Miniconda YAML 检查结果：

- YAML fenced blocks: 6；
- seed objects: 5；
- seed IDs: `RPS-D01`–`RPS-D05`；
- `would_create_route_profile: false`: 5/5；
- `would_mark_covered: false`: 5/5；
- seed company: Coherent only。

## 阻断问题：字段不原子

以下 7 个对象把已观察值和 UNKNOWN 子字段放进同一 `value`，却只给一个观测状态：

1. D01 `media_lanes`：每 lane rate 已知，lane count 未知；
2. D01 `fec_pmd`：PMD/reference 已知，FEC code 未知；
3. D01 `architecture`：raw `retimed` 已知，Tx/Rx/FEC 职责未知；
4. D04 `integration`：MZM PIC 标签已知，细分 integration 未知；
5. D05 `wavelength_organization`：1310 nm 已知，parallel/WDM 与 mapping 未知；
6. D05 `light_source`：EML/1310 nm 已知，源类型与位置细分未知；
7. D05 `detector`：generic photodetector 已知，subtype 未知。

这不只是格式问题。若路线字段以后用于 TQ010/TQ011 和公司能力匹配，一个“部分已知”的复合值会造成错误匹配或错误覆盖。

## 裁决动作

第二轮不增加来源、不增加实例，只把 schema 拆成原子字段。每个叶字段各自拥有：

- `value`；
- `observation_state`；
- `source_ids`；
- 可选 `raw_label`。

UNKNOWN 必须只出现在 `observation_state: unknown` 的叶字段中。首轮原始输出保留审计，不直接采用。
