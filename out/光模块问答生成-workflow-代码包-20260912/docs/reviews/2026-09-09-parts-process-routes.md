# 光模块的零件、制造工艺与技术路线：从具体产品出发的24个问题

2026-09-09｜基于三段完整GPT问答的扩充研究稿｜待审阅，未写入canonical

本文承接《光模块技术需求》3轮、《光模块技术路线梳理》27轮、《光模块构成介绍1》10轮。原问答提供问题和质疑，不充当技术事实的证据。本稿重点扩充零件、工艺和技术路线；原问答提出的历史电话会、需求规模及投资收益，需要另有对应证据，本稿不冒充已完成这些研究。

阅读顺序：**一个真实模块 → 零件承担的功能 → 零件自身怎样制造 → 零件怎样连接成模块 → 不同路线改变什么。**重点是把“制造零件”与“装配模块”分开。国内、海外知识库没有参与本稿的内容组织。

文中“规格/规范”指所引文件直接披露的对象或要求；“工艺实例”只适用于被研究的器件；“厂商声明”没有自动获得第三方验证；“推论”会写出条件；“UNKNOWN”表示本轮未取得相应证据。引用编号对应文末的可点击来源、标题与短摘录。全部来源访问日为2026-09-09，未标发布日期的页面明确按“日期未标”处理。

## 1. 先选哪一只光模块？能知道它的完整BOM吗？

选Coherent **FTCE4527E1PCA，属于FTCE4527E1PxA系列的800G-DR8+ OSFP**作为参考对象。产品参数表明确列出EML发射器、PIN接收器、Dual MPO12接口和2 km单模光纤链路。选择理由是资料明确，不是认定它的市场份额最高。[1] 

规格书第1页进一步给出8×100G PAM4重定时电接口、每路106.25 Gb/s、3.3 V供电及I²C管理接口。速率口径说明：将8路相加得到850 Gb/s聚合线速，但不能当成850 Gb/s有效用户吞吐。[6]

**UNKNOWN：**这两份公开资料没有完整披露内部芯片型号、裸片数量、透镜数量、焊接方式和设备供应商。后面的功能图和制造实例都不会被拼成这只模块的“已知完整BOM”。

## 2. 零件之间怎样接力，怎样才算把产品组成讲完整？

下面是按公开接口和器件功能绘制的通用示意，未确认参考型号的模块DSP是否存在、位置及集成方式；Driver与EAM的具体连接也未披露。一个功能框可能由独立芯片、芯片内电路或多器件组件实现，框数不等于零件数。[2][3][26]

```text
发射信号：主机电接口 → 信号处理 → 驱动 → EML中的EAM → 光耦合 → 光纤
发射光源：供电 → EML中的DFB激光器 ──────────↑
接收信号：光纤 → 光耦合 → PIN光电探测器 → TIA → 信号处理 → 主机电接口
```

信号路径之外还有三组对象，不能从组成介绍中删掉：

| 对象 | 在产品里承担什么 | 能确认到哪一层 |
|---|---|---|
| 电接口、供电、管理接口 | 与主机交换高速信号、电能和管理信息 | 参考规格书披露接口功能，不等于披露独立PMIC、MCU或EEPROM型号。[6] |
| PCB、封装载板等承载互连结构 | 让芯片有承载位置和电连接路径 | PCB制造与芯片封装各有工艺；具体模块如何分配承载任务仍未知。[8][11] |
| 壳体、散热结构及接触面 | 满足机械配合和散热要求 | OSFP规范约束外形和热接触面的部分要求，不指定完整内部热设计。[7] |

## 3. EML里面已经有激光器，为什么还要Driver？

**器件功能。**Lumentum将EML描述为单片集成的DFB激光器与EAM电吸收调制器：DFB连续发光，EAM按信号调制光。Driver属于电路侧，要提供适合调制器的电驱动条件；“产生光”和“把高速电信号施加到调制器”是不同任务。[2][10]

由此可把待研究接口固定为：**Driver输出端—互连—EAM电极**。需要继续核对驱动摆幅、偏置、输入结构和匹配，不能把所有EML都简化成“用调制电流开关激光器”。Marvell的200G/lane LPO芯片组还明确包含TIA和laser driver，即去掉模块DSP也没有去掉这些模拟功能。[10]

## 4. PD与TIA为什么需要分开理解？

PD是光电探测器，接收光后输出光电流；TIA是跨阻放大电路，把电流信号转换、放大为后续可使用的电压信号。TI的电路资料可以直观看到这种关系，但该示例的目标带宽仅300 kHz，**这里只用于解释原理，不能用于800G选型**。[26]

高速产品另看Coherent的TIA器件表：它分别给出符号率、输入噪声、噪声带宽、通道数和封装。这样就能把“接收器性能”拆成探测器、放大电路及二者连接的问题，而不把它们当成一颗无法解释的黑盒。[17]

## 5. EML芯片本身怎样制造？哪一步会因技术路线改变？

**公开工艺实例，不是现代800G代工配方。**NTT在2010年论文中公开了1.55 μm、10/40-Gbit/s EML的两种结构。其制造链可读成：在InP上外延生长功能层 → 选择性去层及再生长 → 干湿法刻蚀脊波导 → 钝化和平坦化 → 接触焊盘 → 晶圆减薄、解理和端面镀膜 → 安装到AlN热沉。[4]

对应设备的作用分别是生长材料层、选择性去除材料、形成表面与电接触、分离芯片和处理光学端面。该论文明确使用MOVPE外延；具体曝光设备、镀膜设备型号没有据此确定。[4]

**真正的工序变化：**该实例中TWG结构省去EAM量子阱再生长；BJ结构则让激光段与调制段获得更独立的设计空间。这是“结构选择改变制造步骤”的直接例子。[4]

**UNKNOWN：**不能把上述年代、波长、层结构和封装直接移植到参考800G模块的EML。

## 6. PIN探测器也需要外延、刻蚀和镀膜吗？

**需要看具体实例。**Ho等人1995年的InGaAs/InP PIN论文公开了MOVPE外延、通过氮化硅掩膜局部Zn扩散成结、接触窗口刻蚀和金属化，以及湿法刻蚀形成隔离与空气桥、SiNₓ钝化和增透膜。[9]

可以据此理解设备任务：外延设备形成吸收层及接触层；扩散和图形化工艺定义电学区域；刻蚀和金属化建立接触并控制寄生；镀膜保护表面、处理光学反射。论文中的平面结与用于隔离的mesa刻蚀可以共存，不能简单当成互斥标签。[9]

**范围：**这是超过14 GHz带宽的早期样品工艺，证明制造动作如何衔接，不证明现代100G/200G-lane PIN采用同样结构或性能。

## 7. DSP、Driver和TIA这些电子芯片又怎样制造？

对这些电子IC，先借助硅芯片制造说明分开“晶圆上做出电路”和“把裸芯片装进封装”；这不是对其实际材料体系或InP器件的工艺确认。ASML的制造说明覆盖薄膜沉积、光刻胶与曝光、刻蚀、离子注入，以及后续切割和封装。它们是理解硅集成电路制造的工序族，不是某颗光模块IC的完整工艺表。[8]

在这些工序里，沉积形成材料层，光刻定义图形，刻蚀转移图形，掺杂调整局部电学性质。装配设备随后处理已经制成的die；它不会替代前面制造晶体管与电路的步骤。[8][27]

**UNKNOWN：**没有具体器件型号和厂商披露，不能指定某个Driver必为SiGe、某个TIA必为CMOS，也不能从模块总速率反推出制程节点。

## 8. 硅光PIC是把零件放到硅板上，还是在晶圆上做出光路？

**平台实例。**AIM Photonics的Low-Loss PDK明确提供硅及氮化硅波导、注入层、Ge探测器和金属布线层。这表示部分光路和电光功能由晶圆工艺形成；它不同于仅把离散光学件粘在普通载板上。[5]

制造研究因此要检查波导和有源区的工艺、金属互连，以及芯片外的光电装配。PDK说明可制造的结构和规则，但公开简介不等于完整工艺配方。[5]

**激光器边界。**也不能把“硅光”限定为一律采用封装外激光器：Intel的2024年OCI原型披露PIC中集成激光器和光放大器，并与电芯片结合。这仅限该厂商原型，不是所有硅光PIC的普遍结构。激光材料和集成方式必须另查；这不表示硅材料本身成为高效激光增益材料。[25]

## 9. VCSEL路线的制造差异能具体落到哪个工序？

Oxford Instruments公开介绍了一类氧化孔径VCSEL的工序：先通过p-mesa干法刻蚀暴露富铝层，再通过高温氧化形成孔径；刻蚀要停在目标外延层，终点控制因而成为明确的设备任务。这里只采用网页公开段落，不声称已取得需填写表单下载的完整白皮书、端点控制配方或设备流程；也不适用于所有VCSEL。[20]

Coherent在2024年公布的另一条研发方向使用光刻孔径，目标是提升器件带宽、面向200G/lane。它提示我们，升级有时改变的是**孔径形成方法和尺寸控制**，不能只写成“采购更快的贴片机”。该公告中的带宽改善和成熟度属于当时厂商披露。[21]

## 10. FAU本身怎样制造？与把FAU接到PIC上是不是同一件事？

FAU是光纤阵列组件。Corning的2019年规格书列出V槽基体与盖板、纤芯间距、端面角度等参数；第5页展示基座研磨、V槽切割、放置光纤和UV粘接，第1页说明切割设备及纤芯间距测量设备的作用。[12]

第一条制造线的输出是**几何位置受控的光纤阵列**。第二条线再把这个阵列与PIC的光学端口对上；同一份资料分别展示端面耦合和光栅耦合，但不证明参考模块采用其中任何一种。[12]

所以要分开研究：FAU内部纤芯间距是否合格，以及FAU相对芯片的位置是否合适。前者做对了，不自动证明后者的耦合损耗合格。这个判断来自两种不同接口的区别，不是新增的产品测试结果。

## 11. 透镜本身由什么设备做出来？

以非球面透镜制造为例，Edmund Optics介绍了两条路线：精密玻璃模压将加热后的玻璃压成模具形状；精密研磨、抛光则通过受控去除材料形成曲面。形状测量可使用轮廓测量或干涉测量。[24]

对应研究对象是模具、镜面形状和测量结果；把做好的透镜装到发射器前方，则是后面的定位与固定工序。两者需要分别核对设备能力。[24][19]

**UNKNOWN：**参考800G模块是否含独立透镜、其尺寸与曲面、材料和制造方式都未披露。上述实例不等于所有微透镜均采用非球面玻璃模压。

## 12. MUX复用器是一个独立零件吗？技术路线怎样改变它？

不一定。三菱电机2019年的400G EML-TOSA实例使用独立空间光学结构：每个TOSA中的四路光通过透镜，以及由带通滤光片和反射镜组成的复用器合并。该系统属于400GBASE-LR8相关设计，不能套给800G-DR8。[15]

另一种实现是波导式复用：POET的1.6T发射PIC说明中列出两个AWG作为MUX。在所引三菱400G TOSA实例中，需要装配和定位空间光学件；在POET所述1.6T发射PIC实例中，复用功能放进波导结构。两者并非同代产品的直接替换对比；功能仍在，但制造对象、装配接口发生变化。[23]

**推论边界：**能确认两种实现存在，不能直接推出独立滤光片设备总需求下降。还需要路线采用量、工序节拍和设备共用情况。

## 13. PCB自身制造与把电子器件装上PCB有什么不同？

Eurocircuits公开的多层板流程包括内层成像与蚀刻、层间定位、叠层压合、钻孔、孔导电处理、电镀、外层成像蚀刻、阻焊、表面处理、电测与成型。它的产物首先是一块**具有线路和焊盘的裸板**。[11]

其中曝光或成像设备形成线路图形，蚀刻去掉多余铜，钻孔和电镀建立层间连接，AOI与电测检查制造结果。随后把芯片和器件安装到承载结构属于后续装配阶段；这些来源没有证明参考模块采用何种PCB表面贴装、固晶或键合组合。不能把“PCB设备”与“封装贴装设备”合并成同一类。[11][27]

**UNKNOWN：**参考模块的板材、层数、铜粗糙度、走线损耗与具体板厂未披露。普通多层板流程只提供理解基础，不能直接证明其满足200G/lane要求。

## 14. Die attach、wire bond与flip-chip分别做什么？

ASMPT把die attach、wire bond等列为不同后段工序，并列出环氧、共晶、软焊料及flip-chip等贴装类别。[27]

| 工序概念 | 面向读者的动作解释 | 不应混淆之处 |
|---|---|---|
| Die attach，固晶/芯片贴装 | 把已经制造好的裸die定位、固定在承载结构上 | 固定芯片不等于已经完成其所有信号连接 |
| Wire bond，引线键合 | 通过细金属线连接芯片与外部焊盘 | 是电互连；不是把光从芯片送进光纤 |
| Flip-chip，倒装连接 | 把芯片连接面朝向载体，以凸点等结构实现连接 | 在具体工艺中可同时承担固定与电互连；不是所有固晶步骤都必须再单独做一遍 |

表格是工序功能解释；具体实现可由器件披露验证。Coherent的TIA表同时列有引线键合、铜柱倒装以及支持堆叠PD的AuSn凸点；不能仅凭“高速接收器”四个字判断工艺。[17]

## 15. 主动对准、被动对准以及固定，为什么要拆开？

**主动对准实例：**Newport应用笔记让光纤连接功率计，再移动光纤寻找较好的耦合位置；其980 nm泵浦激光器实例之后通过激光焊固定。它说明了“测光—运动—固定”的关系，不是800G生产线说明。[19]

**厂商能力说明：**ficonTEC的被动预对准依靠相机、机器视觉和几何校准；主动对准把光功率等性能量与位置关联。它还描述粘接期间监测并校正位置偏移。因此被动预定位、主动搜索和固定可以在同一流程中先后出现。[22]

**关键区别：**被动对准不是“不需要精度”，主动对准也不是设备名称。要问清具体接口、反馈量和固定方式，才有依据列设备。

## 16. 壳体、散热接触面有什么可核查的工艺要求？

OSFP Rev5.0对散热接触面的平面度和粗糙度给出要求，还展示不同散热片形态及气流约束；例如表3-2列有0.12 mm或更好的平面度，并对超过20 W的模块给出更严格的可选建议。这里的数值属于该版规范，不是所有封装的统一公差。[7]

**工艺推论：**制造和装配需要分别控制表面几何、配合位置及实际热接触；机械尺寸合格也不能替代整机散热验证。规范并没有指定壳体必须采用CNC或压铸，参考模块的壳体工艺、内部导热材料与热阻仍为UNKNOWN。[7]

## 17. 800G升到1.6T，零件数量会翻倍吗？

不会仅由总速率决定。Coherent在2024年同一公告里给出两个明确案例：[16]

| 当时公布的演示对象 | 电侧 | 光侧 | 披露的光学路线 |
|---|---|---|---|
| 800G-DR4 | 8×100G | 4×200G | 差分EML |
| 1.6T-DR8 | 8×200G | 8×200G | 硅光 |

由此可见，电lane数、光lane数及单lane速率必须分别记录。**8×100G升级为8×200G**的算术例子增加的是每lane容量，不能自动推出透镜、FAU或贴装次数翻倍。[6][16]

再区分Gb/s与GBd：参考800G规格书给出每lane 106.25 Gb/s。按PAM4每符号2 bit换算，得到53.125 GBd；这是由线路比特率推导出的符号率，未扣除FEC/PCS等开销，仍需与有效数据速率区分。[6][15]

## 18. 更高lane速率会让电互连怎样变化？一定淘汰wire bond吗？

有实际反例：Coherent CHR1074 TIA标示112 GBaud，同时列出“Die, Wire Bonded, with AuSn bumps for stacked PD”，应用包含1.6T DR8。它足以否定“200G/lane必然不再打线”这种绝对说法，但不证明所有高频连接都适合引线键合。[17]

更可靠的问题是：选定器件的带宽、噪声、通道损耗及连接匹配能否满足要求。Marvell在200G/lane LPO芯片组中明确提供可调均衡；它说明提高链路能力可能涉及模拟电路和通道联合设计，不只是缩短几何距离。[10]

**UNKNOWN：**没有同条件封装比较，就不能给wire bond减少比例、倒装设备增量或统一微米公差。

## 19. EML改成硅光，究竟哪些工序迁移了？调制器会减少吗？

**有据的比较范围：**EML把激光与电吸收调制集成在器件内；硅光平台可在晶圆中形成光路和探测等结构，并与光源、电芯片及光纤接口组合。两者要比较的是功能位于哪个器件、接口如何实现。[2][5][25]

**条件推论：**若原先独立装配的某个光学功能被芯片内结构实现，相应独立装配动作可能减少，同时增加或加强PIC制造、测试和芯片外连接任务。功能转移不等于制造工作全部消失。

同理，假设仍传输N路独立调制的数据，就不能仅凭“集成到一个PIC”宣称只剩一个调制功能。独立die数、激光源数、调制通道数应分别统计；激光源能否共享还要核对波长与光功率分配。本段是功能分解推论，不是对某款未披露PIC的器件计数。

## 20. LPO、LRO分别少了什么？会把问题转移到哪里？

LPO MSA FAQ把LPO定义为不含模块DSP的线性可插拔方案，把LRO定义为**接收线性、发射重定时**。因此LRO不能笼统写成“DSP全去掉”，也不能仅凭TRO等简称认定另一种相反架构。[3]

100G-DR-LPO规范的功能描述把FEC、重定时及数模/模数转换放在主机侧，模块传递模拟信号。这个实例说明信号处理的分工改变，不能推成“系统不再需要均衡或FEC”。[18]

**工艺推论：**少一个模块DSP可能减少相应贴装与供电散热工作，但模拟链路、主机和模块的联合验证仍需完成；减掉的功耗也不能直接等于整机节省量。具体节省需要同条件测量。

## 21. CPO改变的是零件种类，还是零件的位置？3.2T是不是同一个概念？

CPO首先改变光引擎与主芯片的封装关系。Intel在2024年披露与CPU共同封装的光I/O原型；这是一个共同封装光I/O原型实例，不是所有CPO均采用同样器件或工艺。[25]

OIF在2023年的3.2T共封装模块协议中列出32×CEI-112G-XSR主机接口、8×400Gb/s光学接口选项（采用DR4或FR4连接），以及光机、电气和管理要求。**这个3.2T是聚合模块定义，不等于8×400G/lane的未来可插拔模块。**[14]

另一方面，Marvell在2025年公告中描述224 GBaud的400G/lane电到光演示，包含DSP、TIA、调制器Driver和光子器件。演示证明的范围、协议规定的范围与量产出货是三件事。本稿不以这些历史文件裁定2026年全行业量产状态。[13]

## 22. POET能否落到具体零件和工序，而不只说“集成平台”？

能。POET于2025-12-08介绍的1.6T 2×FR4发射PIC明确列出四个2×200G EML阵列、八个Driver及两个AWG，并称EML阵列倒装到Optical Interposer上，采用无透镜、无主动对准的被动装配。[23]

这让原问答的问题变得具体：**EML阵列—电互连—波导复用—光纤耦合**怎样在平台上完成？被省去的独立光学装配，换成了哪些预制结构和定位要求？

**证据边界：**以上是POET对所述发射PIC的披露，不能扩成整个收发模块的所有工序都不用主动对准。良率、成本和稳定量产规模仍需独立证据；“具备量产准备”不是已实现规模出货。

## 23. 装好后到底测什么？为什么看见光或漂亮眼图还不够？

先区分对象：参考模块规格书分别规定发射与接收光学参数；FAU规格书另有几何和光学参数。这些检查对应不同制造环节，不能相互替代。[6][12]

端到端链路还要看错误统计。100G-DR-LPO规范第10.2节给出不同通道损耗和光衰减条件下的主机到主机测试，并区分PRBS31Q与实际FEC编码信号的测试方法。规范分别定义PRBS31Q的BER/t-count统计和真实FEC编码信号的pre-FEC BER/FEC bin统计；前者不等于执行了FEC纠错。[18]

**工艺推论：**测试工位应按被测对象与判据配置。装配几何检查、器件频响、模块光学测试和系统误码测试各有目的；本稿没有证据把它们合并成一台“高速测试机”或确定统一产测时长。

## 24. 工序更难，能不能直接推导设备价值量增加？

不能直接推导。现有设备资料已经展示固晶、键合、检测等不同任务，以及被动预定位与主动搜索的组合；路线资料则展示部分光学功能可以集成。它们证明制造实现存在变化，不提供完整设备采购或收益数据。[22][23][27]

**分析模型，不是市场测算：**在单一瓶颈工位、不计返工的简化假设下，可写为：

`所需设备数 ≈ 向上取整〔目标合格产量 ÷（单机额定投入处理速率 × 可用工时 × 稼动率 × 良率）〕`

所以更难的工序可能降低处理速率，也可能被并行化、被动定位或减少步骤抵消。设备收入还涉及新增购买数量和售价；设备价值、单模块成本与供应商利润不是同一个量。

**UNKNOWN：**各路线实际处理速率、良率、返工率、稼动率、设备共用比例和成交价。本稿不沿用原问答中的“设备价值量↑↑”结论。

## 怎样沿这份稿继续扩充

下表是研究安排，表示本稿尚未回答的具体问题，不是行业已经没有答案。

| 需要展开的节点 | 为什么值得继续 | 要找到什么证据 |
|---|---|---|
| Driver—EML的电互连 | 把高速要求与实际装配工艺连接起来 | 同一器件的封装图、驱动条件、S参数和不同连接方案测量 |
| EML/PIC—光纤耦合 | 区分独立透镜、FAU、波导耦合器和被动定位 | 明确结构的耦合公差曲线、固定后漂移、损耗与可靠性数据 |
| PD—TIA组合 | 避免“越靠近越好”停留在口号 | 光敏区、结电容、TIA输入条件及连接寄生的联合测试 |
| 现代200G EML/PIN制造 | 把早期工艺教学实例推进到当前器件 | 现代原始论文、厂商剖面或工艺披露；不能用旧样品参数替代 |
| 波导MUX、薄膜滤光片、外壳和连接器本身制造 | 本稿只展开了部分实现和要求 | 对应产品材料、制造流程、验收参数；尤其不能从名称猜工艺 |
| 同带宽2×800G与1×1.6T | 保留原问答对“多加模块/扩大面板”的质疑 | 同代系统下功耗、端口、布线、可维护性与总成本的可比数据 |
| 工序变化到设备需求 | 判断难度是否转成采购量 | 同口径设备数量、节拍、良率、价格和真实扩产披露 |

最值得先深入的一条线是：**Driver → EML → 光耦合 → 光纤**。本稿已经分别为器件功能、EML制造、连接工序和路线变化找到实例；下一步需要把同一具体产品上的这些接口连起来，而不是继续用多家公司的零散能力拼出一个不存在的完整模块。

## 来源定位与使用限制

下面给出正文中来源的定位。末尾Sources提供可点击原文及用于复查的短摘录。摘录是入口，完整结论仍应对照对应章节，而不是只看摘录。

| 编号 | 原文定位 | 使用限制 |
|---|---|---|
| 1 | Coherent产品表，FTCE4527E1PCA | 日期未标；产品类型与接口，不是完整BOM |
| 2 | Lumentum EMLs，Overview | 日期未标；器件功能，不证明参考模块使用其芯片 |
| 3 | LPO MSA FAQ，定义及nomenclature问题 | 日期未标且页面保留2024年计划语句；只采用定义，不采用过期计划 |
| 4 | NTT 2010年8月，§2与图2/3 | 早期1.55 μm、10/40-Gbit/s器件工艺实例 |
| 5 | AIM Low-Loss PDK，Overview | 日期未标；平台能力，不是特定模块的工艺 |
| 6 | Coherent规格书，第1、3—4页 | March Rev B2，年份未标；网页PDF标题抓取异常，以封面FTCE4527E1PxA为准 |
| 7 | OSFP Rev5.0，2022-10-02，§3.3、表3-2、§10 | 固定版本要求，不声称它是最新版 |
| 8 | ASML，2023-10-04更新，制造步骤 | 通用硅芯片工序族，不推断特定芯片制程 |
| 9 | Ho等，1995年7月，§2，期刊页1295—1296 | 作者上传全文；DOI 10.1016/0038-1101(94)00264-G；早期PIN实例 |
| 10 | Marvell，2024-12-10，公告首段及Key Features | 厂商芯片组声明，不等于全系统量产验证 |
| 11 | Eurocircuits，各制造步骤标题 | 日期未标；普通多层板实例 |
| 12 | Corning OEM-039-AEN，2019-09-03，PDF第1、2、5页 | 特定FAU系列，公差不外推其他组件 |
| 13 | Marvell，2025-03-31，公告首三段 | 当时的400G/lane演示公告，不证明2026年产业成熟度 |
| 14 | OIF，2023-04-05，IA规格列表 | 聚合CPO模块接口，与单lane速率分开 |
| 15 | 三菱ADVANCE Vol168，2019年12月，印刷页5—6（PDF第7—8页） | 400G EML-TOSA，不是800G DR8 |
| 16 | Coherent，2024-09-23，两个Transceiver小节 | 演示配置，不推断量产规模 |
| 17 | Coherent TIA参数表，CHR1074/CHR1065等 | 日期未标；器件可用封装，不证明具体模块选型 |
| 18 | LPO规范封面、修订记录、§4、§10.2 | URL含v1p01，文内为Revision1.0、2025-03-19；部分页脚保留Draft字样，按所读版本使用 |
| 19 | Newport App Note6，PDF第2—4页 | 页脚12/04；980 nm激光器及对准算法示例 |
| 20 | Oxford Instruments，白皮书入口公开的三段正文 | 日期未标；未取需填写表单的完整白皮书，不声称全文已读 |
| 21 | Coherent，2024-03-25，孔径技术说明 | 厂商研发公告，非普适VCSEL极限 |
| 22 | ficonTEC，Motion Systems For Passive & Active Alignment | 日期未标；网页读取超时后直接取得HTML正文；厂商能力说明 |
| 23 | POET，2025-12-08，Product Overview与Technology Foundation | 厂商自述，限该发射PIC；TSV compatibility不等于已实装TSV |
| 24 | Edmund Optics，Asphere Manufacturing Methods与Metrology | 日期未标；非球面制造示例，不指定模块微透镜 |
| 25 | Intel，2024-06-26，How It Works与What's Next | 当时的OCI原型，不是参考模块或当前出货判断 |
| 26 | TI CIRCUIT060041，Overview与Features | 日期未标；300 kHz原理例子，不是高速接收器选型 |
| 27 | ASMPT IC & Discrete，Die Bonding与Wire Bonding | 日期未标；设备工序分类，不是任何模块厂采购名单 |

## Sources

[1] [Coherent — 800G-DR8+ OSFP Optical Transceiver](https://www.coherent.com/networking/transceivers/datacom/FTCE4527E1PxA)

> Receiver | PIN

[2] [Lumentum — EMLs](https://www.lumentum.com/en/optical-communications/products/source-lasers-ics-and-photodiodes/emls)

> a distributed feedback (DFB) diode lasers followed by a monolithically integrated electro-absorption modulator (EAM).

[3] [LPO MSA — Frequently Asked Questions](https://www.lpo-msa.org/home/faqs.html)

> Links that use a linear receiver and a retimed transmitter

[4] [NTT — Uncooled Operation of 10-/40-Gbit/s EML; Aug 2010; section 2](https://www.ntt-review.jp/archive/ntttechnical.php?contents=ntr201008le2.html)

> The advantage of the TWG structure is that the EAM MQW regrowth process can be omitted.

[5] [AIM Photonics — Low-Loss Process Design Kit; undated; Overview](https://www.aimphotonics.com/low-loss-pdk)

> a Ge photodetector, two copper wiring levels, and an Al termination pad level.

[6] [Coherent — FTCE4527E1PxA Product Specification; Rev B2; pp 1,3](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-transceiver-ds.pdf)

> 8x100G PAM4 retimed 106.25Gb/s

[7] [OSFP MSA — Module Specification Rev 5.0; 2022-10-02; sections 3,10](https://www.osfpmsa.org/assets/pdf/OSFP_Module_Specification_Rev5_0.pdf)

> The thermally conductive area in Figure 3-13 should have surface flatness and roughness

[8] [ASML — Six crucial steps in semiconductor manufacturing; updated 2023-10-04](https://www.asml.com/en/company/stories/2021/semiconductor-manufacturing-process-steps)

> deposition, photoresist, lithography, etch, ionization and packaging.

[9] [Ho et al. — InGaAs PIN photodiodes; July 1995; Device structure; author-uploaded full text](https://www.researchgate.net/publication/222370921_InGaAs_PIN_photodiodes_on_semi-insulating_InP_substrates_with_bandwidth_exceeding_14_GHz)

> Besides, a self-aligned lift-off process is used for the n-contact recess and metallization.

[10] [Marvell — 1.6 Tbps LPO Chipset; 2024-12-10](https://www.marvell.com/company/newsroom/marvell-introduces-1-6-tbps-lpo-chipset.html)

> TIA and laser driver chipset provide adjustable equalization to compensate for channel loss.

[11] [Eurocircuits — Making a PCB; undated; process sections](https://www.eurocircuits.com/technical-guidelines/pcb-manufacturing-technology/making-a-pcb-pcb-manufacture-step-by-step)

> Now we drill the holes for leaded components and the via holes that link the copper layers together.

[12] [Corning — FAU Series OEM-039-AEN; 2019-09-03; pp 1,2,5](https://www.corning.com/microsites/coc/oem/documents/OEM-039-AEN.pdf)

> advanced dicing machines and core pitch measurement machines.

[13] [Marvell — 400G/lane demonstration announcement; 2025-03-31](https://www.marvell.com/company/newsroom/marvell-to-demonstrate-industrys-first-400g-lane-pam4-electrical-to-optical-link-technology-at-ofc-2025.html)

> complete electrical to optical link operating at 224 Gbaud

[14] [OIF — 3.2T Co-Packaged Module IA announcement; 2023-04-05](https://www.oiforum.com/oif-launches-the-industrys-first-co-packaging-standard-the-3-2t-co-packaged-module-implementation-agreement)

> 32 x CEI-112G-XSR host interface

[15] [Mitsubishi Electric ADVANCE Vol168; Dec2019; 400G EML-TOSA, printed pp5-6](https://www.advance.mitsubishielectric.com/advance/pdf/2019/168_complete.pdf)

> a lens and a spatial optical multiplexer are integrated.

[16] [Coherent — 1.6T-DR8 and 800G-DR4 at ECOC; 2024-09-23](https://www.coherent.com/news/press-releases/coherent-demonstrates-two-advanced-transceiver-modules)

> eight electrical and eight optical lanes each running at 200 Gbps

[17] [Coherent — TIA product table; undated; CHR1074 and CHR1065](https://www.coherent.com/networking/optoelectronic-devices/integrated-circuits/transimpedance-amplifiers)

> Die, Wire Bonded, with AuSn bumps for stacked PD

[18] [LPO MSA — 100G-DR-LPO Revision 1.0; 2025-03-19; file v1p01; sections 4,10](https://www.lpo-msa.org/files/live/sites/lpomsa/files/specs/LPO_MSA_Specification_v1p01.pdf)

> The LPO optical module performs transmit and receive functions that convey analog signals between the host and the medium.

[19] [Newport — Fiber to Waveguide Alignment Algorithm; App Note 6; footer 12/04; PDF pp 2-4](https://www.newport.com/medias/sys_master/images/images/h57/hc5/9135932669982/DS-03002-App-Note-6.pdf)

> A power meter is used to accurately measure and display the optical power level.

[20] [Oxford Instruments — Advanced Endpoint Control Techniques for VCSEL Mesa Manufacture; public introduction; undated](https://plasma.oxinst.com/media-centre/wp/s2-vcsel-advanced-endpoint)

> The dry etching process of the p mesa then aims to expose the Aluminium rich layer before the oxidation.

[21] [Coherent — Lithographic-aperture VCSEL; 2024-03-25](https://www.coherent.com/news/press-releases/significant-advancement-in-vcsel-performance-next-gen-ai-networks)

> This improvement comes in the form of lithographic-aperture VCSELs

[22] [ficonTEC — Capabilities; undated; Motion Systems For Passive and Active Alignment; direct HTML retrieved](https://www.ficontec.com/capabilities)

> Here, a coupled optical parameter such as power is correlated with positioning in motion space.

[23] [POET — Hybrid-Integrated 1.6T 2xFR4 Transmitter PIC; 2025-12-08](https://www.poet-technologies.com/blog/poet-technologies-redefines-optical-integration-with-its-hybrid-integrated-1-6t-2xfr4-transmitter-pic)

> Four 2x200G EML arrays flip-chip bonded on POET’s optical interposer.

[24] [Edmund Optics — All About Aspheric Lenses; undated; manufacturing techniques](https://www.edmundoptics.com/knowledge-center/application-notes/optics/all-about-aspheric-lenses)

> After the cores cool down to room temperature, the resulting lenses maintain the shape of the mold.

[25] [Intel — Optical I/O Chiplet; 2024-06-26; How It Works and Whats Next](https://www.intel.com/content/www/us/en/newsroom/news/intel-unveils-first-integrated-optical-io-chiplet.html)

> Intel’s current OCI chiplet is a prototype.

[26] [TI — AC-coupled transimpedance amplifier circuit; Overview; low-speed principle example](https://www.ti.com/tool/CIRCUIT060041)

> This circuit uses an op amp configured as a transimpedance amplifier to amplify the AC signal of a photodiode

[27] [ASMPT — IC and Discrete; undated; die attach, wire bond, flip chip categories](https://semi.asmpt.com/en/products/icd)

> including die attach, wire bond, AOI, encapsulation, trim & form and test handler.

