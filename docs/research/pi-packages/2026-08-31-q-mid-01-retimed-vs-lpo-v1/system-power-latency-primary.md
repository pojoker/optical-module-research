# Q-MID-01：Host 与系统总功耗／时延边界（一手资料核验）

> 日期：2026-08-31  
> 状态：research candidate / draft-only  
> 研究对象：retimed、Tx-retimed/Rx-linear（下称 LRO/TRO）与 LPO  
> 证据范围：官方标准与 MSA、芯片／系统／模块厂商一手资料、官方白皮书、可复核论文  
> 禁止用途：本文不能直接作为三条路线的系统功耗或时延排名，也不能据此推断部署份额、客户采用或供货关系。

## 1. 结论先行

**没有找到满足本合同的公开 controlled comparison。**

公开资料中，没有一项实验同时满足以下条件：同一 1.6 Tb/s 主机、同一 2×DR4/500 m 链路、同一环境与 FEC/traffic、分别替换 retimed、LRO/TRO、LPO，并同时披露 module、host SerDes 增量、board/regulator/PSU、cooling，以及定义清楚的 latency measurement points。

目前能得到的最强证据分成三层：

1. **同厂同规格产品口径：只得到模块铭牌功耗，不是受控测量。** Amphenol/XGIGA 的三个明确料号均为 1.6T OSFP、2×DR4、500 m、8×212.5 Gb/s、0–70°C；公开上限依次为 retimed `<30 W`、LRO `<20 W`、LPO `<11 W`。LRO 与 LPO 另列 typical 18 W、10 W；retimed 未列 typical。三份 datasheet 只能支持“该厂商发布的模块功耗规格上限不同”，不能支持系统节能比例，也不能把上限和 typical 混算。
2. **系统级相邻证据：Cisco 展示过 64 端口 800G 交换机的 retimed 与 LPO 对照。** 两台相同 Silicon One G200 交换机分别插满 retimed 与 LPO、全端口满流量，展示的整机差约 700 W。这是公开资料中最接近受控系统对照的一项，但它不是 1.6T/200G-lane，不含 LRO，并且没有披露具体光模块、reach、FEC、流量模式、入口温度、风扇策略、PSU 测点和重复测量，因此只能记为 **adjacent measured demo**，不能移植成合同对象的系统功耗结论。
3. **Host 增量功耗与路线时延：公开数据不足。** 没有找到同一 Host 在三种模式下的 SerDes rail power 或 pJ/bit 增量，也没有找到三路线、同速率同 reach、测点/FEC/traffic 明确的时延对照。Cisco 同一演示文稿中的 `93 ns vs 4 ns` 没有给出测点、方向、包长/PRBS、FEC 路径和测试方法，故不接纳为 controlled latency 结论。

因此，Q-MID-01 当前最稳妥的判断是：

> **公开一手资料足以确认“模块内取消或减少 retiming/DSP 会降低模块铭牌功耗，并把部分信号完整性责任推回 Host 与系统设计”；但不足以量化在相同 1.6T/500 m 边界下的系统净功耗节省，也不足以给出可比的端到端时延差。**

## 2. 共同分母：同厂 1.6T / 2×DR4 / 500 m 产品

| 路线 | 明确料号 | 相同边界 | 模块功耗公开值 | Host/FEC 公开边界 | 证据成熟度 | 本文允许得出的结论 |
|---|---|---|---|---|---|---|
| Retimed | OP13PI8-005D | 1.6T OSFP；2×DR4；8×212.5 Gb/s PAM4；106.25 GBd；500 m SMF；0–70°C；dual MPO-12/APC | `<30 W`；3.3 V 最大电流 9090 mA；未列 typical | Host FEC required | product listing / datasheet | 只支持该料号的公开功耗上限 |
| LRO/TRO | OP13TI8-005D | 同上 | `<20 W`；typical `18 W` | Host FEC required；Tx retimed、Rx linear | product listing / datasheet | 只支持该料号的公开上限与 typical |
| LPO | OP13LI8-005D | 同上；datasheet 另注明 0–70°C without airflow | `<11 W`；typical `10 W`；3.3 V 最大电流 3333 mA | Host FEC required；linear electrical interface / no module CDR | product listing / datasheet | 只支持该料号的公开上限与 typical |

来源：Amphenol/XGIGA 官方 [retimed OP13PI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-2xdr4-op13pi8-005d.pdf)、[LRO OP13TI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-2xdr4-op13ti8-005d.pdf)、[LPO OP13LI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-lpo-op13li8-005d.pdf)。

### 2.1 可以接受的观察

- 三个料号提供了目前找到的最佳“同厂、同形态、同速率、同 reach”产品横截面。
- 在各自 datasheet 的公开规格中，模块功耗上限呈 `<30 W`、`<20 W`、`<11 W` 的顺序。
- 这与 retimed → LRO → LPO 逐步减少模块内重定时/接收 DSP 功能的机制方向一致。

### 2.2 不可以接受的推论

- 不能计算“LPO 比 retimed 节省 63.3%”：`<30 W` 和 `<11 W` 是上限，不是同条件实测值。
- 不能把 LRO/LPO 的 typical 与 retimed 的 maximum 比较。
- 不能把模块功耗差直接等同于交换机、机框或数据中心功耗差。
- 不能因 LPO datasheet 写有 `without airflow`，就推断另外两个料号需要相同或更多风量；其热设计条件没有在三份文件中形成受控对照。
- 不能由 Host FEC required 推断三者使用完全相同的 Host SerDes 配置、FEC 实现或固件参数。
- 不能由同厂三份 datasheet 推断三者具有相同光器件、driver/TIA、PCB、固件、良率或生产成熟度。

## 3. 系统级证据：Cisco 800G 对照演示

Cisco Live 2025 的官方材料展示了两台相同 Silicon One G200、51.2 Tb/s、64×800G 交换机：一台使用 100% retimed optics，另一台使用 100% LPO optics，两台均在所有端口运行满流量；材料给出的 overall power reduction 约为 700 W。[Cisco Live BRKOPT-2699，第 69–70 页](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2025/pdf/BRKOPT-2699.pdf)

Cisco G200 官方规格说明其具有 512×112G LR SerDes 并支持 LPO，但没有公布 retimed 与 LPO 模式之间的 Host SerDes 功耗差。[Cisco Silicon One G200 datasheet](https://www.cisco.com/c/en/us/solutions/collateral/silicon-one/silicon-one-g200-ds.html)

### 3.1 这项演示实际覆盖了什么

| 边界字段 | 是否公开 | 能否用于合同结论 |
|---|---:|---|
| 相同交换 ASIC / 相同端口数 | 是 | 可确认系统平台大体相同 |
| 端口速率 | 是：64×800G | 仅为 100G/lane 相邻对象，不是合同的 1.6T/200G-lane |
| Traffic | 仅称所有端口 full traffic | 缺流量模式、包长、方向、持续时间，不能完整复现 |
| 模块具体料号与 reach | 否 | 不能确认模块自身可比边界 |
| FEC 模式、pre/post-FEC BER | 否 | 不能比较纠错路径和链路裕量 |
| 模块功耗实测 | 否 | 不能从整机差额拆出模块贡献 |
| Host SerDes 增量 | 否 | 不能判断 LPO 将多少功耗转移到 ASIC |
| Board / regulator / PSU | 否 | 不能拆 DC rail、转换损耗和墙上功耗 |
| Cooling / fans | 否 | 不能量化模块降热后带来的风扇节能 |
| 环境温度与风量策略 | 否 | 不能外推到其他机框热设计 |
| 测量点、重复次数、误差 | 否 | 不能形成可复核的 measurement contract |
| LRO/TRO 对照组 | 否 | 不能形成三路线比较 |

### 3.2 700 W 应如何解释

该数值最多支持：**在 Cisco 展示的特定 64×800G G200 系统中，LPO 配置的观测整机功耗低于 retimed 配置约 700 W。**

它不能回答 700 W 由多少模块功耗、Host SerDes、供电转换效率、风扇转速或其他系统状态组成。演示文稿相邻页面另给出一般化的 `16 W vs 8 W` 模块功耗和 `93 ns vs 4 ns` 时延，但没有证明这些数值就是 64 端口演示中所用模块的同批实测值。因此，不应以 `64 × (16−8) W` 反推“剩余 188 W 为 cooling”，也不应把 93 ns/4 ns 写成该整机演示的受控时延结果。

## 4. 强制拆解：当前知道什么、缺什么

### 4.1 Module power

**已知：** 同厂 1.6T 三个明确料号的 datasheet 上限；LRO/LPO 另有 typical。Cisco 有 800G 系统演示和一般化模块数字。

**未知：** 三个 1.6T 料号在相同 inlet temperature、相同 link load、相同 fiber、相同 FEC/BER、相同固件下的实测 DC 功耗；各 rail 功耗；启动、空闲、满载与温度扫描；误差与样本差异。

### 4.2 Host SerDes incremental power

**已知：** 路线改变了责任位置。LPO 需要 Host 直接面对更完整的 C2M/光链路响应；LRO 保留 Tx retiming 而将 Rx 线性接回 Host；retimed 在模块内恢复信号。Google 在 OFC 2024 的官方演示材料中把 non-retimed LPO 的代价列为更复杂的 Host SerDes、die area、power/cost 与更严格的 electrical channel，并用 106.25 GBd PAM4 模型说明 channel loss、peaking 与 optical penalty 的耦合。[Google PIE：Linear Pluggable Optics Beyond 112G](https://storage.googleapis.com/gweb-research2023-media/pubtools/pdf/a24b1eb65b05494e874ffe72c66e360c7861d605.pdf)

**未知：** 同一颗 224G Host SerDes 在 retimed、LRO、LPO 三种设置下的 rail power、ADC/DSP/FFE/DFE 开启状态、firmware、tap 数、摆幅和 pJ/bit 增量。Google 的材料是模型与架构判断，不是完整模块/系统功耗测量；不能用其百分比替代绝对 Host 增量。

### 4.3 Board / regulator / PSU / cooling

**已知：** Cisco 的约 700 W 是 overall power 差，理论上已经混合了模块、Host/board、供电转换和 cooling 的系统响应。

**未知：** 测点是在墙上 AC、PSU DC 输出、机框 telemetry 还是板级 rail；PSU 效率曲线；风扇转速与风量；ASIC/板温；模块笼附近局部热阻；其他组件是否因温度或 SerDes 模式改变功耗。

因此，当前不能做如下闭合：

`system saving = module saving + host increment + board conversion + cooling response`

每一项都缺少至少一个可复核测量值。

### 4.4 FEC / traffic

三份 1.6T datasheet 均要求 Host FEC，并提供基于 PRBS31Q 的 BER 条件；这说明 FEC 与误码边界不能从时延或功耗比较中删除。Cisco 演示只披露 full traffic，未给出帧长、方向、负载生成、FEC 模式及 pre/post-FEC BER。

OIF《System Vendor Requirements Document》把前面板接口的 PMD latency 目标写为 `<20 ns + d×5 ns/m + FEC delay`，并明确其讨论聚焦 PMD、排除 MAC 与 flow control。这份文件同时把“link + host energy efficiency”和前面板“end-to-end power saving target”列为 ND（未定义）。这直接说明：即使标准需求文件给出光电链路的 pJ/bit 目标，也不能把它自动解释成 Host 加模块的系统总功耗。[OIF-EEI-Requirements-RD-01.0](https://www.oiforum.com/wp-content/uploads/OIF-EEI-Requirements-RD-01.0.pdf)

### 4.5 Latency measurement point

当前没有被本文接纳的三路线受控时延数据。

要使时延数字可比较，至少必须公开：

- 单向还是往返；
- 电输入到电输出、Host die-to-die、模块 cage-to-cage、PMD，还是完整 Ethernet packet path；
- 是否包含 PCS、FEC encode/decode、gearbox、MAC、queue 和 flow control；
- PRBS/码字还是 Ethernet 流量，包长与负载；
- fiber 长度及是否扣除约 5 ns/m 的传播时延；
- 仪器、触发、去嵌、重复次数和误差。

Cisco 的 `93 ns vs 4 ns` 缺少这些边界，故只保留为“vendor-stated, method undisclosed”，不晋升为结论。OIF 的公式是 requirement target，也不是产品实测。

## 5. 可接受的 WHY 链与反证条件

### W1：为什么模块铭牌功耗会下降

- **上游约束：** 200G/lane 下模块功耗与热密度受前面板形态限制。
- **责任转移：** retimed → LRO → LPO 逐步将接收恢复／均衡与链路闭合责任从模块移向 Host。
- **机制：** 减少模块内 CDR/DSP/retiming 功能及其相关供电和散热。
- **可观察结果：** 同厂同规格料号的公开模块功耗上限依次降低。
- **成熟度：** product listing；不是 controlled measurement。
- **反证条件：** 同条件实测显示模块功耗无显著差异，或料号内部实现并不对应所标架构。
- **下一问：** 三个料号在同一台 224G Host 上的满载 DC rail 功耗分别是多少？

### W2：为什么模块节能不等于系统同比节能

- **上游约束：** 线性链路必须由端到端电光预算共同闭合。
- **责任转移：** Host 可能承担更强均衡、摆幅、校准、channel management 与更严格板级约束。
- **机制：** 模块减少的功能可能部分转化为 ASIC SerDes 增量、板级损耗或 bring-up 复杂度；较低热负载也可能反过来减少风扇功耗。
- **可观察结果：** Cisco 看到整机差，但没有公开分项；OIF 仍将 link+host 和 end-to-end 指标列为未定义。
- **成熟度：** adjacent measured demo + requirements gap。
- **反证条件：** 同一系统的 rail telemetry 证明 Host/board/cooling 完全不随路线变化，且系统差额与模块差额在误差内闭合。
- **下一问：** 能否取得 ASIC rail、module rail、fan rail 与 PSU 输入的同步测量？

### W3：为什么时延优势目前仍不能量化

- **上游约束：** retiming 与 DSP 会引入处理延迟，但总链路还包含传播、FEC、PCS/MAC 和排队。
- **责任转移：** LPO 删除模块内重定时，不代表删除 Host 侧所有均衡/FEC，也不自动缩短完整 packet path。
- **机制：** 不同测点会得到 PMD、PHY 或系统级不同数字。
- **可观察结果：** 公开材料存在厂商数值和标准目标，但缺少同边界测试方法。
- **成熟度：** mechanism / vendor-stated；controlled result absent。
- **反证条件：** 出现同 Host、同 reach、同 FEC/traffic、统一测点的三路线重复实验。
- **下一问：** 对投资或架构判断真正需要的是 PMD latency、PHY latency，还是应用可见的 packet latency？

## 6. 搜索失败记录

截至 2026-08-31，针对官方标准/MSA、模块厂商 datasheet、Cisco/Google 等系统与芯片厂商材料以及可复核论文的搜索，没有找到以下公开资料：

1. 1.6T、2×DR4、500 m 条件下 retimed/LRO/LPO 三路线的同平台 A/B/C 实验；
2. 三个明确料号的 measured module power，而非 nameplate maximum/typical；
3. 同一 224G Host SerDes 在三种路线下的增量功耗；
4. 模块、Host、board/regulator/PSU、fans/cooling 的同步分项；
5. LRO/TRO 的系统级功耗和时延对照组；
6. 明确 measurement points、方向、FEC、traffic、fiber length 与误差的三路线 latency 数据；
7. 可将 Cisco 约 700 W 分解至各责任域的原始测量表。

这不是“尚未整理”，而是本轮在允许来源范围内的 **public evidence insufficient**。后续若只继续搜索泛化营销文章，预计不会补上这些测量合同字段。

## 7. 最小可复现实验合同

若要把 Q-MID-01 从“机制 + 产品规格”晋升为 controlled comparison，建议实验至少满足：

| 类别 | 必须固定或记录的字段 |
|---|---|
| Host | 同一 224G/lane ASIC/板卡、同一端口、BIOS/firmware、SerDes mode、tap/FFE/DFE、摆幅、温度 |
| Modules | OP13PI8-005D、OP13TI8-005D、OP13LI8-005D；各至少 3 只样本；记录版本与序列号 |
| Link | 1.6T 2×DR4；同一 500 m SMF、连接器与清洁状态；同一对端与 cable loss |
| Traffic/FEC | PRBS31Q 与 Ethernet 两套；固定帧长/方向/负载；记录 FEC 类型、pre/post-FEC BER、uncorrectable codewords |
| Module power | 3.3 V rail 同步采样；idle/full load；启动与稳态；模块温度与 telemetry |
| Host power | ASIC/SerDes 相关 rails；若不能独立测 rail，至少做同板差分并记录其他功能状态 |
| Board/PSU | 板级输入 DC、PSU 输出与墙上 AC 三层测点；记录转换效率 |
| Cooling | 风扇 rail、RPM、PWM、入口/出口温度、环境温度；固定与自动风扇策略各做一轮 |
| Latency | 分开测 PMD/PHY 单向延迟与 packet RTT；明确是否含 FEC/PCS/MAC；扣除或单列 fiber propagation |
| 统计 | 预热时间、采样周期、重复次数、均值/分位数/标准差、仪器精度与异常处理 |

只有在上述测量中，才能计算：

`ΔP_system = ΔP_module + ΔP_host + ΔP_board/PSU + ΔP_cooling`

并进一步判断模块功耗下降是否被 Host 增量抵消、是否被 cooling 放大，以及 LRO 是否形成位于 retimed 与 LPO 之间的稳定系统折中。

## 8. 来源与证据角色

1. Amphenol/XGIGA，[1.6T OSFP 2×DR4 Retimer OP13PI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-2xdr4-op13pi8-005d.pdf)——同规格 retimed 产品边界与铭牌上限。
2. Amphenol/XGIGA，[1.6T OSFP 2×DR4 LRO OP13TI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-2xdr4-op13ti8-005d.pdf)——同规格 LRO 产品边界与铭牌上限/typical。
3. Amphenol/XGIGA，[1.6T OSFP LPO OP13LI8-005D datasheet](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/opticalinterconnect/1.6t-osfp-lpo-op13li8-005d.pdf)——同规格 LPO 产品边界与铭牌上限/typical。
4. Cisco Live 2025，[BRKOPT-2699: Linear Pluggable Optics](https://www.ciscolive.com/c/dam/r/ciscolive/global-event/docs/2025/pdf/BRKOPT-2699.pdf)——64×800G retimed/LPO 整机相邻演示；分项和复现实验参数不足。
5. Cisco，[Silicon One G200 datasheet](https://www.cisco.com/c/en/us/solutions/collateral/silicon-one/silicon-one-g200-ds.html)——确认演示平台的 112G SerDes/LPO 能力；不提供路线间 Host 功耗差。
6. OIF，[System Vendor Requirements Document, OIF-EEI-Requirements-RD-01.0](https://www.oiforum.com/wp-content/uploads/OIF-EEI-Requirements-RD-01.0.pdf)——能耗与 PMD latency 的边界定义及未定义项；属于 requirement，不是实测。
7. Google PIE/OFC 2024，[Linear Pluggable Optics Beyond 112G: Where are use cases?](https://storage.googleapis.com/gweb-research2023-media/pubtools/pdf/a24b1eb65b05494e874ffe72c66e360c7861d605.pdf)——106.25 GBd 下责任转移、Host/通道代价的模型证据；不是系统功耗实验。
8. LPO MSA，[LPO MSA Specification v1.2](https://www.lpo-msa.org/files/live/sites/lpomsa/files/specs/LPO_MSA_Specification_v1p2_final.pdf)——100G/lane 线性接口规范背景；不能移植为 200G/lane 功耗/时延数据。

## 9. 最终判定

| 问题 | 当前答案 | 状态 |
|---|---|---|
| 同一 1.6T/500 m 边界下，三路线模块功耗是否不同？ | 同厂 datasheet 上限明显不同，但缺同条件实测 | partially supported / product-level |
| LPO 的系统总功耗是否按模块比例下降？ | 无法回答；Host、board/PSU、cooling 未拆 | public evidence insufficient |
| LRO 是否在系统功耗上稳定居中？ | 无法回答；只有模块铭牌，无系统对照 | public evidence insufficient |
| 三路线 Host SerDes 增量功耗分别是多少？ | 未找到公开绝对值 | public evidence insufficient |
| 三路线同边界时延分别是多少？ | 未找到测点/FEC/traffic 完整的受控数据 | public evidence insufficient |
| Cisco 800G 演示是否证明系统级方向？ | 支持特定相邻平台的方向性观察，不支持 1.6T 数值移植 | adjacent measured demo |

**本轮不生成系统节能百分比和时延排名。** 下一阶段应优先获取厂商原始测量表或按第 7 节做实物实验，而不是继续累积无边界的营销数字。
