# 比较对象冻结

## CMP-D02-D03

共同已观察/公司表述：

- 1.6T；
- 8×200G electrical；
- 8×200G optical；
- silicon photonics；
- OSFP / normalized front-panel pluggable。

左侧 D02：`Tx-retimed / Rx-linear`、raw `LRO`。

右侧 D03：只披露 raw `3 nm DSP`；normalized architecture、Tx/Rx retiming、FEC/DAC/ADC/host SerDes 职责均 UNKNOWN。

因此：可以比较证据完整度和共同字段，不能把 D03 当 full-retimed，也不能形成 LRO vs retimed 的性能取舍。

## CMP-D04-D05

共同已观察/规范化：

- 同一互操作演示中的 800 Gbps traffic；
- front-panel pluggable（normalized）。

左侧 D04：QSFP-DD800、silicon photonics、MZM PIC。

右侧 D05：OSFP、1310 nm raw `EML laser`、generic photodetector；独立 modulator/emitter 类型 UNKNOWN。

因此：可以记录端点的已观察实现差异，但不能认为除这些字段外的速率、reach、FEC、功耗、成本和测试边界相同。

## 明确排除

- D01 不作为任一比较的事实基线；
- 不进行公司比较；
- 不进行路线成熟度、市场份额、功耗或成本排名。
