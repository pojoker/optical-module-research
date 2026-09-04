# PQ001 draft-only 来源发现

- 目标问题：`PQ001`「光模块在系统中解决什么问题，边界在哪里？」
- 研究阶段：来源发现；不是答案草案，不改变任何问题的覆盖状态
- 核对日期：2026-08-23（Asia/Shanghai）
- 来源准入：只接受官方 MSA/SDO 文件或页面、公司年报及公司官方产品/技术资料
- 本轮写入边界：只生成本文件；未生成 YAML，未修改 `knowledge.yaml` 或 `research_questions.yaml`
- 证据冻结状态：本轮没有制作 `web_snapshot`；以下网页/PDF 均不得直接提升到正式知识库

## 一、来源发现结论

目前找到的来源足以支撑下一步制作一份分层的 PQ001 草案，但不适合拼成一个不带限定条件的“行业唯一标准定义”。建议按四层组织后续草案：

1. 用公司年报回答光模块所解决的基本功能问题，但明确标为公司口径；
2. 用 OIF CMIS 的 Host Interface / Media Interface 划定受 CMIS 管理的传输模块两侧接口；
3. 用 OSFP、QSFP-DD 规范说明可插拔形态下 module、host PCB、cage、connector、heat sink 和 mating fiber plug 的边界；
4. 用 OIF CPO 规范作为反例约束泛化：模块可以靠近 ASIC、安装在共封装基板上，甚至嵌入板上，不一定处于前面板 cage 中。

最重要的限定是：

- “光电转换”可作为光收发模块的功能口径，但目前的一句话证据来自公司年报，不是 SDO 的通用定义；
- CMIS 5.4 同时适用于可插拔或板载模块，但其第 6 章结论有“CMIS managed transmission modules”等适用条件；
- OSFP/QSFP-DD 的 cage、可插拔连接器、前面板和特定散热结构只能用于描述相应可插拔形态；
- host ASIC 不属于光模块本体，但模块与 ASIC 之间的物理距离、承载基板和连接方式会随 pluggable、on-board、CPO 架构改变；
- heat sink 不能不加限定地判为模块内或模块外：OSFP 标准形态可集成散热器，OSFP-RHS 的 riding heatsink 则属于 host。

## 二、逐条来源卡

### S1｜中际旭创股份有限公司 2024 年年度报告全文

- 来源标题：中际旭创股份有限公司 2024 年年度报告全文
- 发布主体：中际旭创股份有限公司
- 来源类型：公司定期报告
- 原 URL：[深圳证券交易所披露 PDF](https://disc.static.szse.cn/disc/disk03/finalpage/2025-04-21/bf311531-d931-48ba-be78-47ed91beba9a.PDF)
- 文档状态：2025-04-21 披露的 2024 年年度报告全文；正式公司公告。它是公司口径，不是行业标准或 MSA 定义。
- 精确锚点：PDF 第 6 页，第一节“重要提示、目录和释义”的“光模块/光通信模块”释义行。
- 短引：`光模块的作用就是光电转换`
- 可直接支持：
  - 中际旭创把光模块的作用概括为光电转换；
  - 该释义进一步分别描述发送端电转光、经光纤传送以及接收端光转电，可作为 PQ001 的功能口径，并给 PQ002 留下功能链线索。
- 不可直接支持：
  - 不能单独证明这是行业唯一、标准化的定义；
  - 不能定义 module 与 host ASIC、host board、cage、heat sink 或外部连接器的边界；
  - 不能推出所有被称作“module”的器件都同时包含双向收发功能。
- 建议 QID 归属：`PQ001`（主：解决什么问题）；`PQ002`（次：发送/接收功能链，后续单独研究）。

### S2｜OIF Common Management Interface Specification (CMIS), Revision 5.4

- 来源标题：Common Management Interface Specification (CMIS), Revision 5.4
- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：OIF Implementation Agreement
- 原 URL：[OIF-CMIS-05.4 PDF](https://www.oiforum.com/wp-content/uploads/OIF-CMIS-05.4.pdf)
- 状态核验页：[OIF Implementation Agreements](https://www.oiforum.com/technical-work/implementation-agreements-ias/)
- 文档状态：OIF-CMIS-05.4，2026-05-21 创建并批准；截至本轮核对日为 OIF 列出的最新 CMIS 主版本。正式 IA，不是说明性白皮书。
- 精确锚点：
  - PDF 第 3 页 Abstract：适用对象包括 pluggable 或 on-board modules；
  - PDF 第 66 页，§6.1“Transmission Module Management Basics”、§6.1.1“Host Interface”、§6.1.2“Media Interface”。
- 短引：`a Host Interface and a Media Interface`
- 可直接支持：
  - 对受 CMIS 管理的传输模块，模块使命相关的两侧物理接口可分为 Host Interface 和 Media Interface；
  - Host Interface 是 module 与 host system 之间的高速电接口，承载进入模块的发送输入和返回 host 的接收输出；
  - Media Interface 位于 module 与通往远端的互连介质之间；介质可为电缆、光纤、波长或子载波；
  - CMIS 的适用范围并不限于可插拔模块，也包含板载模块，因此这个两侧接口框架比 OSFP/QSFP-DD 的机械边界更可泛化。
- 不可直接支持：
  - 不能把 CMIS 管理的 transmission module 等同于所有语境下的“光模块”；规范明确另有 resource module、cable assembly 等例外；
  - 不能仅凭该规范断言 media side 一定是可拆卸光纤接口，因为 media 也可能是铜缆，cable assembly 的介质还可能固定不可拆；
  - 不能从管理接口规范推出模块内部完整 BOM、特定 cage、heat sink 或前面板结构；
  - 不能证明 host ASIC 就是 Host Interface 的机械分界面，规范使用的是更宽的 host system。
- 建议 QID 归属：`PQ001`（主：系统边界）；`PQ002`（次：host/media 信号传播）；`PQ003`（次：板载与可插拔参考样机的代表性边界）。

### S3｜OSFP MSA Specification for OSFP Octal Small Form Factor Pluggable Modules, Rev 5.22

- 来源标题：Specification for OSFP Octal Small Form Factor Pluggable Modules, Rev 5.22
- 发布主体：OSFP MSA
- 来源类型：MSA 硬件/形态规范
- 原 URL：[OSFP Module Specification Rev 5.22 PDF](https://osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_22.pdf)
- 状态核验页：[OSFP MSA Specification](https://osfpmsa.org/specification.html)
- 文档状态：OSFP 官方规范页列出的最新 OSFP 主规范。规范页发布日期为 2025-08-14，PDF 封面日期为 2025-08-09；版本号均为 Rev 5.22，此日期差异应在制作快照时保留。
- 精确锚点：
  - PDF 第 1 页 Abstract：规范对象为 OSFP/OSFP-RHS module、connector 和 cage systems 的电气、机械与热要求；
  - PDF 第 17 页，§1“Scope”：分别列出 module form factor、host cages with mating connector、PCB layout 和 thermal requirements；同页区分 integrated heatsink 与 host-owned riding heatsink；
  - PDF 第 30 页，§3.5“Card-edge Design”：module PCB 上的 contact pads 与规范 §5.10 的 connector 配对；
  - PDF 第 159–160 页，§15.1“Module Electrical Connector”：给出 module card-edge 的发送、接收、控制、电源和地触点分类；
  - PDF 第 172 页，§15.7、Figure 15-7“Host board and Module block diagram”。
- 短引：`a riding heatsink which is part of the host`
- 可直接支持：
  - 在 OSFP 形态中，module、host cage、mating connector 和 host PCB 是可区分的系统对象；
  - module 内 PCB 的 card-edge pads 是模块侧电边界，并与另一侧 connector 配对；
  - 标准 OSFP/OSFP800/OSFP1600 模块包含集成风冷散热器；OSFP-RHS 系列则接触属于 host 的 riding heatsink；
  - 规范显式给出 host board 与 module 的连接关系，适合界定 OSFP 可插拔模块的电气和机械边界。
- 不可直接支持：
  - 不能把 OSFP 的 cage、card-edge、pinout、前面板、热结构或模块外形推广到 QSFP-DD、板载光学或 CPO；
  - 不能笼统声称“heat sink 一定属于模块”或“一定属于 host”；归属依 OSFP 机械变体而变；
  - 不能从形态规范推出模块内部全部功能组件或技术路线；
  - 不能证明所有外部光纤都采用同一种 connector，规范列出了多种光接口示例。
- 建议 QID 归属：`PQ001`（主：可插拔边界）；`PQ003`（次：参考样机形态）；`PQ005`（次：电/机械/热接口）。

### S4｜QSFP-DD MSA Hardware Specification Rev 7.1

- 来源标题：QSFP-DD/QSFP-DD800/QSFP-DD1600 Hardware Specification for QSFP Double Density 8X Transceivers, Rev 7.1
- 发布主体：QSFP-DD MSA
- 来源类型：MSA 硬件/形态规范
- 原 URL：[QSFP-DD Hardware Rev 7.1 PDF](https://www.qsfp-dd.com/wp-content/uploads/2024/07/QSFP-DD-Hardware-Rev7.1.pdf)
- 状态核验页：[QSFP-DD Specification](https://www.qsfp-dd.com/specification/)
- 文档状态：2024-06-25 发布的 Rev 7.1；截至本轮核对日仍是 QSFP-DD 官方规范页列出的最新硬件规范。正式 MSA 规范，不是媒体解读。
- 精确锚点：
  - PDF 第 13 页，§3“Introduction”第 1–26 行及 §3.1 第 29–44 行；
  - PDF 第 45 页，§5“Optical Port Mapping and Optical Interfaces”、§5.1 及 Table 15：电输入/输出到 optical ports 的映射及适用限制。
- 短引：`correct mating of the module and host sides of the connector`
- 可直接支持：
  - 该可插拔规范把 host PCB layout、module、cage、connector system 和 thermal requirements 分项规定；
  - 它把 optical receptacle 与 mating fiber plug 分别列出，可用于识别模块侧光口与外部配对插头的接口边界；
  - 它明确区分 module side 和 host side of the connector；
  - 它把模块电输入/输出映射到 optical ports，同时明确 WDM 应用并不存在由该表规定的电通道到具体波长映射；
  - 它明确声明 optical signaling specifications 不在该硬件规范内，说明形态/接口规范与链路物理层规范不是同一个边界。
- 不可直接支持：
  - 不能把 QSFP-DD 的双排电接点、cage、host PCB footprint、散热结构或前面板边界推广到所有光模块；
  - 不能据此定义具体 DR/FR/LR 光链路性能，文档明确把 optical signaling 交给适用的行业标准；
  - 不能单独断言 cage 或 heat sink 在所有实现中的商业 BOM 归属；
  - 不能证明所有光模块的 media interface 都是可拆卸 fiber plug。
- 建议 QID 归属：`PQ001`（主：可插拔边界）；`PQ003`（次：与 OSFP 的样机边界比较）；`PQ005`（次：电/光/机械/热接口）。

### S5｜OIF Implementation Agreement for a 3.2Tb/s Co-Packaged (CPO) Module

- 来源标题：Implementation Agreement for a 3.2Tb/s Co-Packaged (CPO) Module
- 发布主体：Optical Internetworking Forum（OIF）
- 来源类型：OIF Implementation Agreement
- 原 URL：[OIF-Co-Packaging-3.2T-Module-01.0 PDF](https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-3.2T-Module-01.0.pdf)
- 状态核验页：[OIF Implementation Agreements](https://www.oiforum.com/technical-work/implementation-agreements-ias/)
- 文档状态：OIF-Co-Packaging-3.2T-Module-01.0，2023-03-29 创建并批准；截至本轮核对日仍列在 OIF 正式 IA 清单中。
- 精确锚点：
  - PDF 第 7 页，§1.1“Scope”与 §1.2“Introduction”：模块靠近 switch ASIC，并把短距电接口转换为面向 ASIC 的 optical I/O；
  - PDF 第 10 页，Figure 5 前段：module 与 ASIC/package 可位于同一 Co-Packaged Assembly Substrate；
  - PDF 第 24 页，§6“Mechanical”：模块可围绕基板布置或嵌入板上；该 IA 不定义最终 optical connector。
- 短引：`may be embedded on the board`
- 可直接支持：
  - “光模块”并不必然是插在前面板 cage 中的独立可插拔盒体；正式 OIF IA 存在靠近 switch ASIC 的共封装 optical module；
  - 在该 CPO 实现中，module 和 switch ASIC 是可区分对象，但可以共同安装在 Co-Packaged Assembly Substrate 上；
  - 该 optical module 处理 ASIC 的短距电接口与 optical I/O 之间的转换；
  - 该 IA 的模块可采用 pigtail，最终 optical connector 位置和实现未被 IA 固定。
- 不可直接支持：
  - 不能把这一 3.2T CPO 实现当作所有 CPO、板载光学或所有光模块的通用结构；
  - 不能从该规范推出前面板 cage、电连接器或 OSFP/QSFP-DD pinout 是通用必备件；
  - 不能据此断言所有 CPO 都无可拆光连接器，文档只是未规定具体连接器；
  - 不能把“靠近 ASIC”改写成“光模块等于 ASIC”或“ASIC 属于光模块本体”。
- 建议 QID 归属：`PQ001`（主：反证可插拔边界不可泛化）；`PQ003`（次：参考样机的代表性边界）。

## 三、三项研究目标的来源覆盖

| 研究目标 | 首选来源 | 覆盖判断 | 尚存缺口 |
|---|---|---|---|
| 1. 光模块在 host 电系统与光纤链路之间解决什么问题 | S1 + S2 + S5 | 可形成带条件的功能描述：公司口径的光电转换、CMIS 的 Host/Media 两侧接口、CPO 的电接口到 optical I/O | 尚未找到一个 SDO 文件给出对“所有光模块”都成立的一句话定义；后续不能伪造这种统一口径 |
| 2. module 与 ASIC/host board/cage/heat sink/外部光纤的边界 | S2 + S3 + S4 + S5 | 已能分别说明通用接口骨架、OSFP/QSFP-DD 可插拔边界及 CPO 边界 | ASIC 到 module 的具体电连接和外部光连接器所有权随形态变化，后续草案必须按形态分别写 |
| 3. 哪些结论只能用于 OSFP/QSFP-DD | S3 + S4，并用 S2 + S5 交叉约束 | 已确认 cage、前面板、特定 card-edge/footprint、可插拔 mating 结构和散热器归属不能泛化 | 若后续要覆盖更多形态，还需另开针对 COBO、ELSFP 或其他 on-board optics 的来源发现；本轮不扩问题树 |

## 四、后续 draft-only 使用规则

1. PQ001 草案应把“功能边界”“接口边界”“特定形态的机械边界”分栏，不能焊成一个层级。
2. 每条主张必须带适用条件，例如“中际旭创公司口径”“CMIS-managed transmission module”“OSFP Rev 5.22”“QSFP-DD Rev 7.1”或“OIF 3.2T CPO module”。
3. host ASIC、host board、cage、connector、heat sink 与 fiber plug 不得凭行业常识判定归属，只能按相应规范逐项写。
4. 后续若形成“光模块的一般边界”研究框架，应同时保留 pluggable 与 CPO 两种实例，防止把前面板可插拔样机冒充总体定义。
5. 在正式裁决或入库前，应为 S2–S5 制作冻结快照，记录原 URL、抓取时间、文档版本和 SHA256；S1 可复用现有年度报告本地文件，但仍需核对其来源 URL 与文件哈希。
6. 本轮不建议新增问题 ID。细化出的电/光/机械/热接口材料可回挂既有 `PQ005`；发送/接收链材料回挂 `PQ002`；样机形态差异回挂 `PQ003`。

## 五、已排除或降级的候选来源

- OSFP/QSFP-DD FAQ：仅用来核对最新版规范入口；涉及边界的正式主张优先引用 PDF 正文。
- OIF CMIS 5.0/5.3：已被 5.4 主版本取代，本轮不作为首选锚点。
- Coherent 官方博客：虽能支持光电转换口径，但证据等级低于正式 IA/MSA 和公司年度报告，本轮不需要重复加入。
- 卖方研报、媒体、百科、培训材料：全部排除。

## 六、停止结论

来源发现阶段完成。当前证据足以进入 PQ001 的 draft-only 答案生成与语义裁决，但不足以改变 `PQ001` 的覆盖状态，也不足以写入正式知识库。下一步只应在本研究包内制作验收合同、冻结快照和答案草案。
