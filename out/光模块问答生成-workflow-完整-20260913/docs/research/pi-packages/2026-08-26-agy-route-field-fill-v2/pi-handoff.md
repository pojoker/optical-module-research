# Pi 最小交接：800G EML 实例与 SiPh 绑定缺口

本文件是本轮唯一允许交给 Pi 的消费入口。Pi 不得直接读取 AGY raw output 形成事实。

## 任务边界

- 只形成 draft-only 字段卡和研究注记；
- 不回答路线优劣；
- 不生成公司服务群；
- 不生成 WHY 边；
- 不修改问题覆盖状态；
- 不落知识库。

## EML 可消费来源

### S-EML-1：Coherent preliminary datasheet

- 主体：Coherent / Finisar
- 产品系列：`FTCE4527E1PxA-2N`
- 文档：*Preliminary Product Specification 800G-DR8+ OSFP Optical Finisar Transceiver FTCE4527E1PxA-2N*
- 版本：Oct. 2023 Rev A1
- URL：`https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-2n-transceiver-ds.pdf`
- 可消费范围：产品系列、文档成熟度、DR8+/breakout applications、OSFP、retimed 8×100G PAM4 electrical interface、850 Gb/s aggregate bit rate、Dual MPO-12 APC、2 km G.652 SMF、lane signaling、wavelength range、module power ceiling、temperature option schema、CMIS/I2C、regulatory fields。
- 不可消费范围：GA/量产、内部 EML topology、TEC、TOSA/ROSA、driver/TIA、lens coupling、FEC location、factory test coverage、heatsink 冲突解释。

### S-EML-2：Coherent first-party product page

- 主体：Coherent
- 产品系列：`FTCE4527E1PxA-2N`
- 页面：*2x400G DR4+ OSFP Optical Transceiver*
- URL：`https://www.coherent.com/networking/transceivers/datacom/FTCE4527E1PxA-2N`
- 可消费范围：Transmitter = EML；Receiver = PIN；2 km；800G；OSFP；1310 band；Dual MPO12；0–70°C；850 Gb/s。
- 注意：页面标题、datasheet 标题和 applications 同时出现 2×400G DR4+ 与 800G DR8+。只记录产品系列声明，不擅自把它们拆成两个独立 SKU。

## EML 对应真实问题树

| QID | 允许形成的 draft-only 内容 |
|---|---|
| TQ005 | 产品/链路标准候选值：800G DR8+；2×400G DR4+ 与 8×100G breakout 是同系列公开应用声明，精确标准归属仍需后续核对 |
| TQ006 | 8×100G PAM4 retimed electrical interface；FEC location UNKNOWN |
| TQ007 | product-family-level EML transmitter / PIN receiver；内部实现 UNKNOWN |
| TQ008 | hot-pluggable OSFP Type 2、Dual MPO-12 APC；heatsink 状态 UNKNOWN_CONFLICTING_LABELS |
| TQ009 | 可形成 observed instance seed，不形成正式 RP；缺失字段必须保留 UNKNOWN |
| TQ014 | 本轮没有受控优势/代价证据，不得填 advantages/disadvantages |

## SiPh 结果

本轮没有合格的 exact commercial product → SiPh platform 公开绑定。不得建立与 EML 对称的商业产品字段卡。

可以保留的来源线索：

- Intel 800G 2×400G FR4 OSFP MDDS：只证明产品身份与 MM 编号；
- Intel OFC 2022 M2D.7 公开摘要：只证明 800G 2×FR4/DR8 SiPh transmitter demo、8 个 heterogeneous DFB lasers、0–70°C、最长 2 km；
- Intel SiPh portfolio page：只证明平台级组件组合与累计出货，不绑定某一 800G SKU；
- AGY 候选表中的 Jabil、Cisco、Acacia、Marvell、Coherent、Eoptolink、InnoLight、Hyper Photonix、SiFotonics：仅作为后续搜索候选，不作为负向事实。

## 由缺口生成的细化研究注记

以下只挂现有 QID，不新建 QID：

1. `TQ007-note-platform-binding`：什么证据足以把 exact product instance 与 EML/SiPh 光子平台绑定？
2. `TQ009-note-evidence-subject`：Route Profile 是否必须分别保存 product、platform component、demo 和 binding 四类 evidence subject？
3. `TQ013-note-service-without-customer`：公司官方产品/出货证据何时足以证明服务某路线，何时才需要具名客户？
4. `TQ014-note-controlled-comparison`：若 EML 侧是商业产品、SiPh 侧只有 transmitter demo，是否应禁止直接比较成本、功耗、良率和成熟度？答案在取得同证据等级资料前保持开放。

## Pi 输出要求

Pi 只输出：

1. 一张保留 UNKNOWN 的 EML observed-instance 字段卡；
2. 一张 evidence-subject 分层示意；
3. 四条研究注记的去重判断；
4. 下一轮 AGY 精确搜索查询建议。

任何字段必须携带来源 URL、页码/页面位置和短引文。没有锚点的字段写 UNKNOWN。
