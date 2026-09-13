# 冻结来源摘录：Coherent FTCE4527E1PxA-2N

检索日期：2026-08-26
用途：本轮 draft-only 小样的可复现来源锚；不构成 canonical 写入。

## S-EML-1 官方 PDF

- 标题：*Preliminary Product Specification 800G-DR8+ OSFP Optical Finisar Transceiver FTCE4527E1PxA-2N*
- 发布者：Coherent Corp. / Finisar
- 版本：Oct. 2023 Rev A1
- URL：`https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-2n-transceiver-ds.pdf`
- PDF 页数：7
- 文件大小：436640 bytes
- SHA256：`284168df99e4b8ec9837a2a47a7e533fc18d6a42ad09346cd8db69d3a3eeaf8d`

| 字段 | PDF 位置 | 短引文 |
|---|---|---|
| 文档成熟度 | p.1 标题 | “Preliminary Product Specification” |
| 产品系列 | p.1 标题 | “FTCE4527E1PxA-2N” |
| form factor | p.1 Product Features | “Hot-pluggable OSFP form factor” |
| aggregate rate | p.1 Product Features | “Supports 850Gb/s aggregate bit rate” |
| module power | p.1 Product Features；p.3 Electrical Characteristics | “Power dissipation <17W (c-temp)”；“Module total power ... 17 W” |
| 温度变体 | p.1 Product Features / Product Selection；p.2 | “C = Commercial 70-0C or L = Limited 20-60C” |
| electrical interface | p.1 Product Features | “8x100G PAM4 retimed 106.25Gb/s PAM4 electrical interface” |
| connector | p.1 Product Features | “DUAL MPO-12, APC receptacles” |
| applications | p.1 Applications | “800G DR8+ applications with FEC” |
| breakouts | p.1 Applications | “8 x 100GbE breakout applications” |
| alternate application | p.1 Applications | “2 X 400 DR4+ applications with FEC” |
| reach / fiber | p.1 Description；p.5 General Specifications | “up to 2km of single mode fiber”；“SMF per G.652 ... 2 km” |
| symbol rate | p.3 Optical Characteristics | “53.125 ± 100 ppm GBd” |
| optical modulation | p.3 Optical Characteristics | “Modulation format PAM4” |
| wavelength range | p.3 Optical Characteristics | “1304.5 to 1317.5 nm” |
| FEC boundary | p.1 Applications；p.5 | “with FEC”；“Bit Error Ratio ... 2.4E-4” |
| management | p.5 Digital Diagnostics / Memory Contents | “support the I2C-based diagnostics interface”；“CMIS 4.0 Per MSA” |
| placement detail | p.6 Mechanical Specifications | “pluggable form factor type 2 modules” |

## S-EML-2 官方产品页

- 页面：*2x400G DR4+ OSFP Optical Transceiver*
- 发布者：Coherent Corp.
- URL：`https://www.coherent.com/networking/transceivers/datacom/FTCE4527E1PxA-2N`
- 检索日期：2026-08-26

| 字段 | 页面位置 | 页面值 |
|---|---|---|
| product family | Datasheet parameter table | `FTCE4527E1PxA-2N` |
| operating distance | Datasheet parameter table | `2 km` |
| data transfer rate | Datasheet parameter table | `800G` |
| form factor | Datasheet parameter table | `OSFP RHS` |
| receiver | Datasheet parameter table | `PIN` |
| transmitter | Datasheet parameter table | `EML` |
| connector | Datasheet parameter table | `Dual MPO12` |
| temperature | Datasheet parameter table | `0°C` to `70°C` |
| data rate | Datasheet parameter table | `850 Gb/s` |

## 解释边界

- S-EML-2 支持产品系列层 EML/PIN 绑定，不支持内部 die/array/topology。
- `OSFP RHS` 必须原样保留为产品页 raw label，并与 S-EML-1 的 `A: Closed Heatsink`、`2N: No Heat Sink Design` 一起进入 unresolved heatsink label set；本轮不展开 RHS、不裁决哪一个标签覆盖另一个。
- S-EML-1 的 TDECQ/TECQ 是信号眼图指标，不支持 thermoelectric cooler。
- `A: Closed Heatsink` 与 `2N: No Heat Sink Design` 标签冲突保持 UNKNOWN，不自行解释。
- 文档为 preliminary；安全认证、样例标签和参数完整度不证明 GA 或量产。
- “with FEC” 与 BER 门槛不证明具体 FEC code 或终止位置。
