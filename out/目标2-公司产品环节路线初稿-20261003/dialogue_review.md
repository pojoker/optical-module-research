# 指定对话的技术分类审阅

本审阅用于目标 2 初稿：从公司定位到具体产品，再沿通道、电处理、发射、光路、接收和封装，记录产品已经披露的实现。原对话提供了可用的拆解方法，但其中若干技术名词属于不同维度，不能直接当成相互排斥的路线；部分产品阶段和内部结构也超出了来源支持范围。

审阅范围：主代理已完整读取指定对话的 5 轮可读取正文。本审阅者收到主代理摘录的待核验原句及六家公司名称（中际旭创、Coherent、Lumentum、Source Photonics、光迅、新易盛），定向核验分类语义和公开技术资料；本文件不冒充对完整对话的独立逐轮读取记录，也不确认未提供的原始附件正文。读取日期为 2026-10-03。未修改 canonical。

## 可采用

**按功能分解，再落到具体产品。** 把完整模块分成电处理、驱动与发射、传光与合分波、探测与放大、载体和互连，有助于解释器件分工。但模块、Tx/Rx 光引擎、TOSA/ROSA、PIC、激光裸片、driver/TIA 芯片属于不同产品层级，应分别标注。不能把一家公司的器件能力拼成该公司某款完整模块的 BOM。

**电通道、光通道和波长分别记录。** 例如 8 路电接口不自动代表 8 个激光裸片，也不自动代表 8 根数据发送光纤；4 个波长可以合到同一根发送光纤，两个 FR4 光组又会有不同的总光路结构。初稿应保留电/光每路速率、通道数、波长数以及接口协议的原始表述，未披露的对应关系保持 UNKNOWN。

**把阶段与技术结构分开。** 产品页、规格书、展示、样品、一般供货、出货爬坡、批量出货，各自支持不同结论。资料披露了结构，不代表批量交付；公司报告披露了某速率整体出货，也不代表所有同速率路线都已量产。

## 需修正

| 原对话表述或分类 | 问题 | 初稿采用的修正 |
| --- | --- | --- |
| EML / SiPh / TFLN 同列 | EML 是含激光器和电吸收调制器的器件；SiPh 是硅光集成技术/平台；TFLN 是薄膜铌酸锂材料及相应光子平台。三者粒度不同，也不能据名称推断完全互斥。 | 如果比较发射路径，写成「EML 发射」「CW 光源 + 已披露类型的硅光调制器」「CW 光源 + TFLN 调制器」。集成平台另列，实际是否组合按产品来源确认。[S1–S3] |
| wire-bond / chip-on-carrier / flip-chip / optical interposer 作为四选一 | wire-bond 与 flip-chip 描述电互连/贴装；chip-on-carrier 描述芯片装在载体上的部件形态；optical interposer 描述承载电、光连接及器件的平台。同一组合可出现多个术语。 | 分别写「承载对象」「芯片朝向与固定」「电互连」「光连接」「装配规模」。例如 POET 光学中介层同时使用 flip-chip 有源器件和片内波导，不是二选一。[S4–S5] |
| MUX：TFF / AWG / PLC / SiPh integrated WDM | TFF、AWG 是合分波器件/结构；PLC 是平面光波回路技术；SiPh integrated WDM 描述在另一集成平台实现的波分功能，尚未给出具体结构。 | 先问是否需要波分合分波；需要时再记 TFF、AWG 或其他明确披露结构，并记分立/片内位置与材料平台。可以写「PLC 上实现的 AWG」。不能把 PLC 当成与 AWG 平行的排他项。[S6] |
| PD：InGaAs PIN / APD / Ge-on-Si PD | 结构、增益机制与材料混列。PIN/APD 说明器件结构或是否产生雪崩增益，InGaAs/Ge-on-Si 说明吸收材料与集成方式。 | 接收器拆成「材料」「PIN/APD/其他结构」「集成位置」「TIA 和后级处理」。InGaAs 可有 PIN 和 APD；某产品只披露 PIN 时，不补造 InGaAs。Ge-on-Si 也不能只凭名称归入未披露的具体结构。[S7–S8] |
| SiPh 图统一画 Modulator / MUX / DEMUX / Ge PD | 图把一种可能的波分收发实现误画成整个平台的必备 BOM。 | 调制结构按型号标注；MUX/DEMUX 只在实际波分结构披露时画入；探测器材料和位置必须有来源。Intel 官方同时提供并行 DR 与 WDM FR，已说明 SiPh 平台标签不能单独决定波分光路。[S2] |
| CPO 导致前面板连接消失 | 把光电转换位置变化与光纤连接取消混为一谈。 | 说明光引擎移到 ASIC 所在封装，使高速电路径变短；光纤仍需要连接到光引擎和系统外部。NVIDIA 的具体实现保留数据光纤、激光输入光纤和可拆光连接器。是否在面板、接口种类和光源所在位置仍按系统型号确认。[S10] |

COC 的展开还需特别注意：初稿如果采用 chip-on-carrier，应按该来源确切用词记录，不能自动与 chip-on-submount、chip-on-chip 等名称互换。本文只提出层级修正，没有据此确认六家公司某个型号采用 COC、某种载体材料或特定电连接。

## 暂不能证明

**LPO 800G FR4 示例中「8×100G 或 4×200G 电 → 4×200G 光」。** 速率加总相等只说明总吞吐相同，不能证明有通道转换。LPO MSA 明确把移除模块 DSP 功能作为处理分工，并发布了 100G/lane 的并行单模链路规范；这些定义不自动赋予 8 路变 4 路的能力。若要保留 8×100G 电到 4×200G 光，必须取得该型号电接口、内部转换功能和兼容 LPO 声明；取得之前，此对应关系为 UNKNOWN。4×200G 电/光也必须有具体产品资料，不能由 LPO 名称自行推出。[S9]

**「Marvell 已经量产 200G/lane LPO TIA + driver chipset」。** 主代理核对的 2024-12-10 官方新闻稿明确宣布 general availability，可写为厂商宣布一般供货。仅凭这句话不能确认特定客户采用、量产出货规模或哪些 800G/1.6T 模块使用它；这些仍需对应产品或客户证据。不得以同一芯片组可支持 800G/1.6T，推定六家公司的具体产品 BOM。[S11]

**「硅光必有 Ge PD」「硅光必有 MUX/DEMUX」「EML 必须 wire-bond」「某厂具备路线就代表所有同速率产品采用该路线」。** 本轮没有取得支持这些全称判断的证据。应删除必然语气，回到特定型号的已披露字段。平台通用说明可以帮助解释动作，不能替代型号级来源。

## 初稿落表建议

每个产品先明确对象层级和产品名称，再记录七项：通道/接口，电处理，光源与调制，光路及合分波，探测与放大，载体/电光连接，商业阶段。每项附其来源锚；出处没有给出的字段写 UNKNOWN。将「公开披露事实」「按功能作出的解释或推导」「尚待核验」分别展示，不用图的完整性补齐事实。

优先追补具体型号的完整数据表和厂商架构图，其次追补内部连接与部件资料，最后核对阶段与出货。通用教材只能解释器件怎样工作；专利可以证明申请文本提出了某种实现，不能单独证明量产产品采用。

## agy 辅助记录

本轮按要求运行一次 `agy --mode plan --print-timeout 100s --print`，未指定模型/agent，未修改配置或权限。进程真实退出为 code 0，但工具明确返回 `no output produced`，原因是 headless 所需 `command` 权限被自动拒绝。没有可采用的 agy 检索结果；没有绕过权限、长等待或继续会话。本文技术核验由直接读取一手网页完成。

## 来源与支持范围

以下网页均于 2026-10-03 读取。页面没有明确发布日期的条目记为日期未知；网页的当前内容不能倒推原对话当时已公开相同信息。厂商自述结构与产品能力按其原有边界采用，不把宣传性的优劣或制造能力直接转为独立证实的表现。

| 编号 | 一手来源与资料日期 | 可定位锚点及本文支持范围 |
| --- | --- | --- |
| S1 | [Lumentum EML 产品页](https://www.lumentum.com/en/products/data-center/modulated-lasers/emls)，日期未知 | Explore Our Products 第一段：同一 EML 集成 DFB 激光器和单片电吸收调制器。支持器件层级；不支持六家模块内部型号。 |
| S2 | [Intel Silicon Photonics](https://www.intel.com/content/www/us/en/products/details/network-io/silicon-photonics.html)，日期未知 | What Is Silicon Photonics；High-Speed Photonics Components：并行 DR、WDM FR 和片上集成激光阵列。支持平台与产品结构须分开核对；不指定其他厂商的调制器或探测器。 |
| S3 | [HyperLight Company / Technology](https://www.hyperlightcorp.com/company)，日期未知 | What is TFLN：薄膜铌酸锂光学材料；TFLN Chiplet Platform。支持材料/平台层级，不支持六家模块实际采用 TFLN 或性能排序。 |
| S4 | [Amkor Flip Chip](https://amkor.com/technology/flip-chip/)，日期未知；[Amkor Interposer PoP](https://amkor.com/packaging/laminate/interposer-pop/)，日期未知 | flip-chip interconnect；interposer 平台支持 flip-chip connection。作为封装名词层级实例，不代表光模块实际封装。 |
| S5 | [POET Technology](https://www.poet-technologies.com/technology)，日期未知 | What is an Optical Interposer；How does…achieve chip-scale integration…：中介层、waveguide、flip-chip active devices、可选 driver/TIA。支持平台和贴装工艺可并存；不是六家产品的 BOM。 |
| S6 | [NTT：PLC 实现的 AWG 获 IEEE 里程碑](https://group.ntt/jp/newsrelease/2026/02/18/260218a.html)，2026-02-18 | 第 2 节「石英系PLCを用いた…AWGとは」：PLC 实现 AWG 波长合分波器。支持结构与平台非排他；不证明目标模块采用石英 PLC。 |
| S7 | [Hamamatsu InGaAs photodiode arrays](https://www.hamamatsu.com/us/en/product/optical-sensors/photodiodes/ingaas-photodiode-array.html)，日期未知 | Segmented InGaAs photodiodes：4-segmented InGaAs PIN photodiodes，证明材料与器件结构可组合。不是高速模块接收器型号证据。 |
| S8 | [Hamamatsu InGaAs APDs](https://www.hamamatsu.com/us/en/product/optical-sensors/infrared-detector/ingaas-apd.html)，日期未知；[Hamamatsu APD 原理](https://hub.hamamatsu.com/us/en/ask-an-engineer/detectors/detection-questions-and-answers.html)，日期未知 | 产品类别及 What is an APD：InGaAs APD 与雪崩内部增益。用于分类解释，不把偏压数值或性能套入未披露型号。 |
| S9 | [LPO MSA 首页](https://www.lpo-msa.org/home.html)，日期未知；[LPO MSA 规范发布公告](https://www.lpo-msa.org/news/lpo-msa-announces-release-of-specification-for-linear-pluggable-optica)，2025-03-25 | DSP function removed from pluggable module；100G/lane、最高 800G、parallel single-mode links。支持处理分工和已发布范围；不证明 8×100G 到 4×200G。规范 PDF 初次返回可读元数据，后续正文请求超时，未依赖未读到的 PDF 图表。 |
| S10 | [NVIDIA：How Industry Collaboration Fosters NVIDIA CPO](https://developer.nvidia.com/blog/?p=104930)，2025-08-26 | 正文 How modular optical subassemblies… 及随后 Spectrum-X 段落：发送/接收/供光光纤、可拆光连接器。未依赖网页 AI-Generated Summary。可作为仍有光连接的实例，不确认任意 CPO 的面板结构。 |
| S11 | [Marvell 1.6T LPO 芯片组公告](https://www.marvell.com/company/newsroom/marvell-introduces-1-6-tbps-lpo-chipset.html)，2024-12-10 | 主代理已直接核对开头 general availability、200G/lane TIA/laser driver；本审阅按该锚修正阶段，本轮未重复正文核验。GA 不单独证明客户量产。 |

本轮还找到一篇 2025 年 EML COC 论文及 Hamamatsu G8195 PIN 数据表的检索摘要，但直接正文读取分别失败和返回 404，未把两者的摘要加入上述证据。chip-on-carrier 的详细制造动作、材料和电互连仍需可读取的具体来源。
