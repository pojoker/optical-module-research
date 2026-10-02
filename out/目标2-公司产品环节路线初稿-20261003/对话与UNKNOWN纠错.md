# 为什么前稿缺产品、内部实现又有大量 UNKNOWN

前稿存在整理错误。它把六家公司的一部分代表配置做成主稿，却没有先展开完整的资料内产品目录；还把八类环节固定初始化为空，再用“资料未披露”解释空值。旧28张卡的560条检查中，372条被标UNKNOWN，311条来自统一默认句，八类永不赋值的字段就占224条。这个数字反映抽取方式，不能用来判断厂商公开程度。

本次保留完整读过的原对话为问题线索，并逐项找回原厂依据。网页抽取遗漏不等于原厂没有资料；产品族路线已知也不应因为缺SKU而整项未知。以下原对话主张为便于核对的概括，不是逐字引语。

| 缺口类别 | 修订后的表达 | 例子 |
|---|---|---|
| 漏收产品、漏读规格 | 补回已披露内容，撤销对应未知 | 新易盛FR8、Coherent 2FR4 EML/PIN |
| 网页读取或动态内容漏取 | 标明提取方式问题并补原页内容 | Lumentum 1.6T CW DFB；光迅JS规格表 |
| 产品族已知、具体型号未对齐 | 同时列族级已知路线和型号级缺口 | Source 1.6T EML/SiPh/InP PIC变体 |
| 本稿未取得环节资料 | 标为未提取/待检索，不称厂商未披露 | PCB、载体、时钟等没有专项资料的项目 |
| 所核来源未写、或来源相互冲突 | 写清已读哪份资料、缺哪项或冲突何处 | 激光颗数、具体驱动料号；Source 2FR4距离冲突 |
| 功能不适用 | 不计成未知 | 铜缆AEC不涉及激光器或光电探测器 |

这次“补全”有两个可核对层次：当前三份公司清单的名称均有目录入口；六家公司新增核对的产品族和型号进入产品目录及逐项纠错表。它没有证明各公司所有定制SKU、全部内部BOM或所有量产状态已公开。

## 原对话与前稿逐项对照

### D01 新易盛 · 800G FR8 EOLO-168HG-02-P内部实现

| 对照项 | 内容 |
|---|---|
| 原对话主张 | EML/CWDM、driver集成retimer、8PD+2四通道TIA |
| 前稿遗漏/未知 | 前稿未收此SKU与详细PDF；内部实现泛称UNKNOWN |
| 本次补回或修正 | PDF p1直接披露8×106.25G电输入输出、8 CWDM波长、EML发射、双向PAM4 retimer ASIC与EML/modulator driver集成；RX=8PD+两组4通道TIA+PAM4 retimer；Features=PIN，LC，2km，<16W。 |
| 差异原因 | 漏读原厂PDF |
| 剩余缺口 | 精确芯片厂商/制程、PD材料、WDM器件工艺、制造及量产；不能把integrated with解释为EML激光本体在CMOS DSP芯片上 |

来源：[EFR](https://www.eoptolink.com/pdf/800G/OSFP/Brief%20EOLO-168HG-02-P%20V1.b.pdf)

### D02 新易盛 · 800G LPO光学四路线

| 对照项 | 内容 |
|---|---|
| 原对话主张 | MMF VCSEL；SMF EML/SiPh/TFLN |
| 前稿遗漏/未知 | 前稿只列OIF2024硅光LPO版本，其他路线未进目录 |
| 本次补回或修正 | 2023官方发布稿Chrome当前正文明确四路线、无DSP/CDR、OSFP/QSFP-DD800；应记产品族直接披露，SKU映射待补。 |
| 差异原因 | 漏读发布稿；web工具源访问异常；过严SKU匹配把产品族已知写成UNKNOWN |
| 剩余缺口 | 每一路线完整SKU、各自距离/功耗/连接器、是否持续在售及量产；2024 SiPh/PIN-TIA内容不能套全部四路线 |

来源：[EL](https://eoptolink.com/news/341-eoptolink-launches-innovative-800g-linear-drive-pluggable-optics-during-ofc-2023)；[EOIF](https://www.oiforum.com/wp-content/uploads/OIF_PLL_Demo_Eoptolink_OFC2024.pdf)

### D03 新易盛 · 1.6T目录、距离、通道、连接器

| 对照项 | 内容 |
|---|---|
| 原对话主张 | DR8/DR8-2/2FR4多配置 |
| 前稿遗漏/未知 | 把搜索缓存留线索；Gen2 PR稿缺距程导致500m/2km泛UNKNOWN |
| 本次补回或修正 | Chrome当前Ordering information可读完整4族；DR8/DR8-2/2FR4精确型号、8×200G、波长、距离、连接器直接恢复，2VR4仍TBD。 |
| 差异原因 | 源访问层问题＋未展开订货表 |
| 剩余缺口 | Gen2变体后缀与现订货表映射、每SKU DSP代际、SiPh/EML后缀；NRZ电口不能套全族 |

来源：[E16](https://www.eoptolink.com/product-solutions/16t/16t-osfp)；[EG](https://www.prnewswire.com/news-releases/eoptolink-launches-its-gen2-1-6t-osfp-and-osfp-rhs-transceiver-family-at-ofc-2025--302414882.html)

### D04 光迅 · 800G DR4/FR4 200G/lane SiPh

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 200G-lane硅光800G DR4/FR4 |
| 前稿遗漏/未知 | 前稿以800G DR8/2FR4老型号为主要样本，漏新一代族 |
| 本次补回或修正 | 2025-09-28/30官方稿直接披露OSFP112/OSFP224 DR4/FR4，200G/通道硅光，并已动态演示；产品族路线可成立。 |
| 差异原因 | 漏读新发布稿；代际和产品族覆盖不足 |
| 剩余缺口 | 各P/N、电通道、Driver/TIA、MUX、连接器、量产；不能直接把1.6T 3nm DSP套800G |

来源：[A25](https://www.accelink.com/en/lighting_your_dreams/1972134410522226689.html)；[A25D](https://www.accelink.com/lighting_your_dreams/1972923533839314946.html)

### D05 光迅 · 1.6T OSFP224 2DR4/2FR4

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 3nmDSP+SiPh |
| 前稿遗漏/未知 | 前稿仅DR8 2025 OFC升级版及RTXM700-502旧规格 |
| 本次补回或修正 | ECOC2025族2DR4/2FR4直接3nmDSP+硅光；厂商说功耗比上代降30%，不能视为当前P/N实测 |
| 差异原因 | 新一代产品族漏读，不能跨代合并 |
| 剩余缺口 | P/N、绝对功耗、基线、距离、PD/TIA及量产 |

来源：[A25](https://www.accelink.com/en/lighting_your_dreams/1972134410522226689.html)；[A25D](https://www.accelink.com/lighting_your_dreams/1972923533839314946.html)

### D06 中际 · 800G SR8 VCSEL

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G短距VCSEL路线 |
| 前稿遗漏/未知 | 上轮JSON未纳SR8，代表样本不等完整公司目录 |
| 本次补回或修正 | 新官网OSFP112与QSFP112-DD SR8均直接VCSEL、8×100G电/并行光、双MPO12、OM3 30m/OM4 50m。 |
| 差异原因 | 产品样本选取漏列，不是路线未公开 |
| 剩余缺口 | PIN/TIA、DSP及量产未直接披露 |

来源：[I1](https://www.innolight.com/data-center-networking/800g-osfp112)；[I2](https://www.innolight.com/data-center-networking/800g-qsfp112-dd)

### D07 中际 · 800G 2xFR4 EML+CWDM

| 对照项 | 内容 |
|---|---|
| 原对话主张 | EML/CWDM两组4波长 |
| 前稿遗漏/未知 | 该路线前稿已部分写明，需公司目录展示，避免读者以其他项UNKNOWN误读 |
| 本次补回或修正 | OSFP112和QSFP112-DD均官网直接EML+8×100G电、两组4波长CWDM MUX/DEMUX，2km；不需等P/N方可确认产品配置路线。 |
| 差异原因 | 呈现层级问题，已知配置未扩目录 |
| 剩余缺口 | AWG/薄膜实现、PD/TIA当前页不列；旧表PIN另列缓存 |

来源：[I1](https://www.innolight.com/data-center-networking/800g-osfp112)；[I2](https://www.innolight.com/data-center-networking/800g-qsfp112-dd)

### D08 中际 · 800G EML/PIN和SiPh产品族

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G EML/SiPh路线及EML/PIN型号 |
| 前稿遗漏/未知 | 旧官网实时502，全部降线索；没有清楚保留已支持的族 |
| 本次补回或修正 | 旧官网缓存列EML/PIN三型号、SiPh TX/RX AOC型号模式；当前QSFP112-DD DR8/2DR4直接EML。记旧官网缓存支持/当前待核，而非抹掉；SiPh族直接披露、当前SKU映射待补。 |
| 差异原因 | 源访问限制＋证据层级被合并成UNKNOWN |
| 剩余缺口 | 缓存表当前真实性、旧SKU是否持续在售、与新官网代际映射；SiPh AOC不能推SiPh DR8 exactSKU |

来源：[IC](https://products.zj-innolight.com/en/goods/solution/cid/18.html)；[I2](https://www.innolight.com/data-center-networking/800g-qsfp112-dd)

### D09 光迅 · 800G OSFP224 DR4具体P/N和实现

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G200G-laneSiPh |
| 前稿遗漏/未知 | 前稿没有DR4型号；后来仅恢复2025产品族发布稿 |
| 本次补回或修正 | 当前官网RTXM700-546直接SiPh modulator、4双工光通道、每路212.5GbpsPAM4、MPO12APC、500m、16W、0–70°C。此SKU光学路线有直接锚，不再仅族级。 |
| 差异原因 | 目录漏读＋JS加载抽取漏正文 |
| 剩余缺口 | 该页没有逐字电通道/DSP/PD/TIA，不把OSFP224封装名当电通道表；量产未知 |

来源：[ADR4](https://www.accelink.com/en/lighting_your_dreams/2084555909131960322.html)

### D10 光迅 · 1.6T OSFP224 2FR4 RTXM700-532具体实现

| 对照项 | 内容 |
|---|---|
| 原对话主张 | SiPh CWDM与200G通道 |
| 前稿遗漏/未知 | 前稿未纳当前新目录型号 |
| 本次补回或修正 | 当前页直接8×200G SiPh CWDM发射、8×200G1600GAUI8电口、DualDuplexLC、2km、26W、0–70°C；补齐具体P/N |
| 差异原因 | 目录漏读＋JS正文访问问题 |
| 剩余缺口 | DSP、CW激光器、PD/TIA、WDM器件工艺、量产；不认作2025发布稿3nm升级版 |

来源：[A2FR](https://www.accelink.com/en/lighting_your_dreams/2084552858237173762.html)

### D11 新易盛 · 800G DR8 / 8x100G LR电芯片集成

| 对照项 | 内容 |
|---|---|
| 原对话主张 | Driver/TIA与DSP集成 |
| 前稿遗漏/未知 | 前稿仅浸没冷却SKU有该实现，普通DR8未覆盖 |
| 本次补回或修正 | 当前目录链接DR8 EOLO-138HG-5H-xDx及并行LR EOLO-138HG-10-xDx PDF均直接Driver/TIA集成DSP。DR8=8×106.25G电/光，500m；LR=8EML+8ch driver/retimer，8PD+integratedTIA，10km。 |
| 差异原因 | 漏读当前二级目录原厂PDF |
| 剩余缺口 | DR8该PDF未明光源；DSP型号/制程、PD类型、量产；LR虽名称含LR但并行8路，不是LR8 WDM |

来源：[EDPDF](https://www.eoptolink.com/pdf/800G/OSFP/Brief%20EOLO-138HG-5H-xDx%20V1.b.pdf)；[ELPDF](https://www.eoptolink.com/pdf/800G/OSFP/Brief%20EOLO-138HG-10-xDx%20V1.b.pdf)

### D12 新易盛 · 800G 2FR4内部MUX/接收链

| 对照项 | 内容 |
|---|---|
| 原对话主张 | EML、MUX/DEMUX、PD/TIA/retimer |
| 前稿遗漏/未知 | 前稿只写LPO族及浸没DR8代表款，普通DSP 2FR4缺失 |
| 本次补回或修正 | 当前链接2FR4 PDF：8×106.25G电口，两组4 CWDM；TX=双向PAM4retimer+8ch driver、8EML、2MUX；RX=2DEMUX、8PD、2×4chTIA及retimer，Features PIN；双LC，2km，<16W。 |
| 差异原因 | 漏读详细PDF；SKU别名映射待补不等内部结构未知 |
| 剩余缺口 | 目录EOLO-168HG-02-XX与PDF内部-02-1别名待补；MUX技术、芯片型号及量产 |

来源：[E2FPDF](https://www.eoptolink.com/pdf/800G/OSFP/Brief%20EOLO-168HG-02-XX%20V1.a.pdf)

### D13 新易盛 · 800G VR8内部VCSEL/PIN/driver/TIA

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 短距VCSEL及PIN/TIA |
| 前稿遗漏/未知 | 前稿未列VR8 |
| 本次补回或修正 | EOLO-858HG-01-M PDF直接850nmVCSEL/PIN；TX PAM4retimer+2×4ch驱动与8激光器；RX8PD+2×4chTIA及retimer；8×106.25G电口，MPO16APC，OM3 30m/OM4 50m，<15W，15–70°C。 |
| 差异原因 | 代表型号目录漏列 |
| 剩余缺口 | 不能把VR8直改SR8；目录C范围与PDF15–70°C差异保留；芯片型号/量产未知 |

来源：[EVPDF](https://www.eoptolink.com/pdf/800G/OSFP/Brief%20EOLO-858HG-01-M%20V1.c.pdf)

### D14 中际 · 800G SiPh 2FR4/DR8+与5nmDSP版本

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G SiPh路线与DSP |
| 前稿遗漏/未知 | 前稿防错把历史/族路线一概排出主表，没有保留族级已知 |
| 本次补回或修正 | 旧官网当前缓存明确EML/SiPh族及SiPh AOC；2021历史报告缓存描述OFC2022具体SiPh OSFP2FR4/QSFPDDDR8+；2023官方稿直接第2代OSFPDR8+/2FR4 5nmDSP<14W。应各按历史版本显示，不把当前新页所有DR8/2FR4归同代。 |
| 差异原因 | 证据层级显示问题＋历史与当前型号映射不足 |
| 剩余缺口 | 当前P/N、光子平台变体映射与当期量产；历史送样不升当前量产 |

来源：[IC](https://products.zj-innolight.com/en/goods/solution/cid/18.html)；[ICQ](https://products.zj-innolight.com/en/goods/solution/cid/19.html)；[ICSH](https://www.innolight.com/uploads/aboutfiile75/1671780229984674.pdf)；[IN23](https://www.innolight.com/en/news/newsinfo/179.html)

### D15 Coherent · 800G 2FR4 EML/PIN

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G 2FR4已有EML/PIN实现 |
| 前稿遗漏/未知 | 首稿只取DR8+ EML，漏2FR4 |
| 本次补回或修正 | FTCE4717E1PCB：8×100G PAM4 CWDM EML；PIN；8×106.25Gb/s重定时电接口；2km；双LC；3.3V；17W最大值。PDF的15–70°C与网页0–70°C冲突保留。 |
| 差异原因 | 代表型号选样遗漏 |
| 剩余缺口 | DSP品牌/工艺、驱动/TIA型号、MUX/DEMUX器件结构和内部封装未公开 |

来源：[OG02](https://www.coherent.com/networking/transceivers/datacom/FTCE4717E1PCB)；[OG03](https://www.coherent.com/resources/datasheet/networking/optical-transceivers/osfp/ftce4717e1pcb-transceiver-ds.pdf)

### D16 Coherent · 800G 2×400G FR4 Lite SiPh/CW

| 对照项 | 内容 |
|---|---|
| 原对话主张 | FR4 Lite采用SiPh及CW |
| 前稿遗漏/未知 | 首稿漏整族 |
| 本次补回或修正 | 500m；SiPh PIC＋CW激光＋光电探测器＋无源光学；无需TEC；波分型。2025-03-20声称已有样品、GA计划2025-04-01；计划日期不当作已兑现。 |
| 差异原因 | 产品族遗漏 |
| 剩余缺口 | SKU、CW数量/功率、PD类型、DSP架构、MUX器件、连接器及当前出货量未逐项公开 |

来源：[OG04](https://www.coherent.com/news/press-releases/uncooled-silicon-photonics-based-2x400g-fr4-lite)

### D17 Coherent · 1.6T SiPh/CW与FRO/TRO

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T有SiPh/CW full-retime路线 |
| 前稿遗漏/未知 | 精确SKU卡把光学全UNKNOWN，缺少旁边产品族层 |
| 本次补回或修正 | OFC26披露1.6T涵盖SiPh PIC＋高功率InP CW等平台；2026-03-17演示第17页直接列FRO/TRO三DSP供应商。保留族级光路线及电处理，不将两条名单拼成某SKU BOM。 |
| 差异原因 | 产品族事实与SKU事实未分层 |
| 剩余缺口 | FRO/TRO逐变体与SiPh、EML、VCSEL的配对及FTCF2519E3PCA/E1PCM的型号配对未知 |

来源：[OG07](https://www.coherent.com/news/press-releases/coherent-demonstrates-next-gen-pluggable-transceiver-ofc-2026)；[OG31](https://www.coherent.com/content/dam/coherent/site/en/documents/investors/investor-presentations/2026/march-17/OFC-2026-Investor%20event-deck-vf.pdf)

### D18 Coherent · 1.6T DR8 SiPh LRO

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T SiPh LRO已公开 |
| 前稿遗漏/未知 | 首稿有演示卡，但没有公司全目录及CW平台上下文 |
| 本次补回或修正 | OFC25明确8×200G电/光、OSFP、SiPh，LRO的DSP仅Tx重定时；同新闻3nmDSP属于另一演示，不能合成LRO=3nm。SiPh需CW属于公司平台说明，具体激光未知。 |
| 差异原因 | 需保留已核族级路线，且防止跨演示拼接 |
| 剩余缺口 | 该演示SKU、光源数量/波长/功率、接收TIA/PD内部实现、当前认证/出货未知 |

来源：[OG05](https://www.coherent.com/news/press-releases/coherent-to-showcase-innovative-products-and-technologies-at-ofc2025)；[OG08](https://www.coherent.com/news/blog/enabling-ai-next-gen-datacenters)

### D19 Coherent · 800G DR4差分EML

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800G DR4使用200G D-EML |
| 前稿遗漏/未知 | 首稿已有演示卡，产品目录遗漏 |
| 本次补回或修正 | ECOC24：8×100G电→4×200G光，200G差分EML，500m/4对SMF，OSFP。 |
| 差异原因 | 目录整合遗漏，非光路线缺资料 |
| 剩余缺口 | 演示SKU和DSP型号未知；不能与目录404的FTCE3517L1PCM强绑 |

来源：[OG06](https://www.coherent.com/news/press-releases/coherent-demonstrates-two-advanced-transceiver-modules)

### D20 Coherent · 1.6T EML与VCSEL产品族

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 多光学平台并行，而非单一SiPh |
| 前稿遗漏/未知 | 首稿列SiPh样本，漏家族其他平台 |
| 本次补回或修正 | OFC26明确200G InP EML和200G GaAs VCSEL；OFC25明确1.6T SR8 OSFP为8×200G电/光VCSEL演示。 |
| 差异原因 | 产品族覆盖遗漏 |
| 剩余缺口 | EML版的DR/FR具体族和SKU、VCSEL版SKU/量产阶段未知 |

来源：[OG07](https://www.coherent.com/news/press-releases/coherent-demonstrates-next-gen-pluggable-transceiver-ofc-2026)；[OG05](https://www.coherent.com/news/press-releases/coherent-to-showcase-innovative-products-and-technologies-at-ofc2025)

### D21 Coherent · 1.6T 2FR4 6km

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T波分长一些的IMDD路线 |
| 前稿遗漏/未知 | 首稿漏族 |
| 本次补回或修正 | ECOC25演示1.6T 2×800G FR4到6km，模块内含小型色散补偿。 |
| 差异原因 | 产品族遗漏；相邻段器件不能借用 |
| 剩余缺口 | 未直接披露光源/调制、DSP和SKU；不能把同新闻300G/lane的D-EML搬入此卡 |

来源：[OG09](https://www.coherent.com/news/press-releases/coherent-showcases-next-generation-optical-innovations-at-ecoc2025)

### D22 Coherent · 精确1.6T SKU内部实现

| 对照项 | 内容 |
|---|---|
| 原对话主张 | FTCF2519可代表1.6SiPh全retime |
| 前稿遗漏/未知 | 族路线未对齐SKU就被全擦除 |
| 本次补回或修正 | FTCF2519E3PCA与E1PCM目录都明示1.6T DR8、8×200G主机/光接口、500m、双MPO12、1310nm、OSFP；网页未将任一SKU绑定SiPh/CW或某DSP。旁设族级已知路线。 |
| 差异原因 | 源的对象粒度不同；若对话直接强绑为过推 |
| 剩余缺口 | 精确SKU→SiPh/EML、FRO/LRO/TRO和DSP的关联未知 |

来源：[OG28](https://www.coherent.com/networking/transceivers/datacom/FTCF2519E3PCA)；[OG29](https://www.coherent.com/networking/transceivers/datacom/FTCF2519E1PCM)；[OG07](https://www.coherent.com/news/press-releases/coherent-demonstrates-next-gen-pluggable-transceiver-ofc-2026)；[OG31](https://www.coherent.com/content/dam/coherent/site/en/documents/investors/investor-presentations/2026/march-17/OFC-2026-Investor%20event-deck-vf.pdf)

### D23 Coherent · 800DR8+连接器

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 并行模块连接器应有确定规格 |
| 前稿遗漏/未知 | 网页MPO12与PDF MPO16矛盾 |
| 本次补回或修正 | FTCE4527E1PxM的矛盾仍在，不能静默择一。 |
| 差异原因 | 原厂不同资料冲突 |
| 剩余缺口 | 现售硬件/版本连接器需原厂确认 |

来源：[OG27](https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxm-transceiver-ds.pdf)；[OG01](https://www.coherent.com/networking/transceivers/datacom)

### D24 Coherent · 驱动/TIA/无源组件

| 对照项 | 内容 |
|---|---|
| 原对话主张 | Coherent全垂直集成可推出模块内部BOM |
| 前稿遗漏/未知 | 能力表容易被当某模块用料 |
| 本次补回或修正 | OFC26第16页是公司能力表，列driver/TIA/MUX/DEMUX/探测器，不是SKU用料表；8002FR4只有器件大类EML/PIN获得型号锚。 |
| 差异原因 | 把能力误当采用会过推 |
| 剩余缺口 | 具体SKU器件品牌、数量、内部工艺未知 |

来源：[OG31](https://www.coherent.com/content/dam/coherent/site/en/documents/investors/investor-presentations/2026/march-17/OFC-2026-Investor%20event-deck-vf.pdf)；[OG02](https://www.coherent.com/networking/transceivers/datacom/FTCE4717E1PCB)

### D25 Lumentum · 800/1.6T自有数通目录

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 应有按公司展开的产品清单 |
| 前稿遗漏/未知 | 首稿三卡但未给目录覆盖范围 |
| 本次补回或修正 | 当前原厂数通目录HTML列800G2DR4、1.6T2DR4全Tx/Rx重定时、1.6T2DR4 TRO；另列400GAOC。三个高速族有明确产品页；SKU未列。 |
| 差异原因 | 代表卡片没有转成公司目录 |
| 剩余缺口 | 该公开目录以外的客户定制版本、SKU与全在售组合未知 |

来源：[OG10](https://www.lumentum.com/en/products/data-center/datacom-transceivers)；[OG11](https://www.lumentum.com/en/products/800g-2dr4-osfp-transceiver-module)；[OG12](https://www.lumentum.com/en/products/16t-2dr4-osfp-transceiver-module)；[OG13](https://www.lumentum.com/en/products/16t-2dr4-tro-osfp-transceiver-module)

### D26 Lumentum · 800G2DR4 SiPh/4CW

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 四颗1311nm CW DFB＋SiPh＋DSP |
| 前稿遗漏/未知 | 首稿已填光路线，full-retime/监测漏 |
| 本次补回或修正 | 800页及嵌入Features：4×1311nm CW DFB＋SiPh，8×106.25Gb/s电/光，Tx/Rx均重定时；800GAUI8，500m，2×MTP12/APC；CMIS5.2。 |
| 差异原因 | overview外的Features抽取遗漏 |
| 剩余缺口 | 具体SiPh调制器结构、CW分光方式、PD/TIA/driver及DSP型号未知 |

来源：[OG11](https://www.lumentum.com/en/products/800g-2dr4-osfp-transceiver-module)

### D27 Lumentum · 1.6T全retime光源

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T SiPh/CW实现已有 |
| 前稿遗漏/未知 | 首稿CW写UNKNOWN |
| 本次补回或修正 | 同产品页HTML嵌入Features直接披露1311nm CW DFB；SiPh＋DSP与全Tx/Rx重定时已明示。8×212.5Gb/s电/光、500m、双MPO16/APC、CMIS5.3、22W典型、20–70°C。 |
| 差异原因 | web文字抽取丢Features，属于漏读 |
| 剩余缺口 | CW颗数、调制器结构、PD/TIA/driver、DSP型号未知；不得移植800G四颗 |

来源：[OG12](https://www.lumentum.com/en/products/16t-2dr4-osfp-transceiver-module)

### D28 Lumentum · 1.6T TRO光源及电处理

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T TRO是SiPh/CW且只Tx重定时 |
| 前稿遗漏/未知 | 首稿CW写UNKNOWN |
| 本次补回或修正 | 同产品页HTML嵌入Features直接披露1311nm CW DFB；SiPh＋DSP、仅Tx重定时；8×212.5Gb/s电/光、500m、双MPO16/APC、CMIS5.3、16W典型、20–60°C。 |
| 差异原因 | web文字抽取丢Features，属于漏读 |
| 剩余缺口 | CW颗数、PD/TIA、DSP型号未知；22W与16W规格不构成同条件功耗试验 |

来源：[OG13](https://www.lumentum.com/en/products/16t-2dr4-tro-osfp-transceiver-module)

### D29 Lumentum · 监测/管理

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 资料中控制与监测比概述更细 |
| 前稿遗漏/未知 | 首稿只列CMIS，未列监测功能 |
| 本次补回或修正 | 三款Features均披露RSSI与Tx功率监测；800G另披露VDM；CMIS版本为800G5.2、1.6T两款5.3。 |
| 差异原因 | 未读取Features，不能把功能和芯片料号混为一项 |
| 剩余缺口 | MCU/监测芯片、电源IC/电压、偏置控制回路结构未知 |

来源：[OG11](https://www.lumentum.com/en/products/800g-2dr4-osfp-transceiver-module)；[OG12](https://www.lumentum.com/en/products/16t-2dr4-osfp-transceiver-module)；[OG13](https://www.lumentum.com/en/products/16t-2dr4-tro-osfp-transceiver-module)

### D30 Lumentum · driver、接收与电源内部链

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 对话仅称datasheet比概述更细，未提供真实datasheet URL；不能当已核资料 |
| 前稿遗漏/未知 | 首稿广义UNKNOWN没有说明是没取得资料 |
| 本次补回或修正 | 公开三页Features已复核；资源列表为空，文档中心本轮98资源未检得800/1.6T模块datasheet。保留驱动、PD/TIA、MCU/PMIC/供电的检索缺口；不能宣称原厂从未披露。 |
| 差异原因 | 资料取得不全；若用通用块图确定型号BOM则过推 |
| 剩余缺口 | 没有可回核的原对话datasheet URL；驱动、PD/TIA、MCU/PMIC/电源细分待真实型号资料。无需继续从占位符推断。 |

来源：[OG11](https://www.lumentum.com/en/products/800g-2dr4-osfp-transceiver-module)；[OG12](https://www.lumentum.com/en/products/16t-2dr4-osfp-transceiver-module)；[OG13](https://www.lumentum.com/en/products/16t-2dr4-tro-osfp-transceiver-module)；[OG15](https://www.lumentum.com/en/products/product-documentation-center)

### D31 Lumentum · 800ZR+ hybrid

| 对照项 | 内容 |
|---|---|
| 原对话主张 | Lumentum800ZR+用InP+SiPh混合集成 |
| 前稿遗漏/未知 | 首稿限数通，未另附相干目录 |
| 本次补回或修正 | 800ZR+ QSFP-DD/OSFP，hybrid PIC包含InP PIC与SiPh；合作方相干DSP。用于DCI/城域/区域，400/600模式是同族性能模式。 |
| 差异原因 | 范围界定未另列相干，族事实可补 |
| 剩余缺口 | SKU、DSP型号、相干调制器/接收器细分、模块出货阶段未知 |

来源：[OG14](https://www.lumentum.com/en/products/800g-zr-coherent-pluggable-transceivers)；[OG32](https://investor.lumentum.com/financial-news-releases/news-details/2024/Lumentum-Enhances-Performance-in-800ZR-Transceivers-for-Broader-Applications/default.aspx)

### D32 Lumentum · NVIDIA1.6T EML合作演示

| 对照项 | 内容 |
|---|---|
| 原对话主张 | Lumentum200G EML出现在NVIDIA模块 |
| 前稿遗漏/未知 | 若把合作模块作为Lumentum自有1.6T SKU会错 |
| 本次补回或修正 | Lumentum自有三族产品页明确SiPh/CW；NVIDIA合作EML演示应单列组件采用/合作演示，不能替换自有产品光路线。 |
| 差异原因 | 把元件合作演示混成自有模块会过推 |
| 剩余缺口 | 合作演示供应量、Lumentum内部整模块BOM未知 |

来源：[OG11](https://www.lumentum.com/en/products/800g-2dr4-osfp-transceiver-module)；[OG12](https://www.lumentum.com/en/products/16t-2dr4-osfp-transceiver-module)；[OG13](https://www.lumentum.com/en/products/16t-2dr4-tro-osfp-transceiver-module)；[OG34](https://www.lumentum.com/en/events/ofc-2026)

### D33 Source Photonics · 800G DR4/FR4/LR4 4×200G EML

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 800DR4/FR4/LR4以200G单波EML实现 |
| 前稿遗漏/未知 | 首稿DR4/FR4有卡，漏LR4和完整族目录 |
| 本次补回或修正 | OFC25与ECOC25明确三族4×200G光、O-band CWDM/LWDM EML、OSFP或QSFP-DD，覆盖至10km。各SKU及具体波长分组未逐一配。 |
| 差异原因 | 产品族目录遗漏；SKU未知不应抹去EML平台 |
| 剩余缺口 | 主机电通道、DSP、PD/TIA、FR/LR具体MUX实现、具体SKU及逐族阶段未知 |

来源：[OG18](https://www.sourcephotonics.com/news/source-photonics-announce-the-product-availability-of-its-200g-per-lane-based-1-6t-and-800g-pam4-transceiver-family-products-at-ofc25/)；[OG19](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-at-ecoc-2025/)

### D34 Source Photonics · 1.6T DR8 EML/SiPh/InP PIC

| 对照项 | 内容 |
|---|---|
| 原对话主张 | Source新1.6T有多平台变体 |
| 前稿遗漏/未知 | 首稿只列EML两个型号造成EML排他印象 |
| 本次补回或修正 | OFC25直接列DR8 EML/SiPh/InP PIC三变体；2026-03-17直接列DR8 EML、SiPh测试与DR8 EBO EML；DR8两光学变体production volume为原厂自述。 |
| 差异原因 | 公司路线标签过窄、产品族遗漏 |
| 剩余缺口 | 三平台SKU未匹配；InP PIC内部激光/调制结构不能等同EML；不能独立确认量产量 |

来源：[OG18](https://www.sourcephotonics.com/news/source-photonics-announce-the-product-availability-of-its-200g-per-lane-based-1-6t-and-800g-pam4-transceiver-family-products-at-ofc25/)；[OG21](https://www.sourcephotonics.com/news/source-photonics-and-delta-electronics-join-force-to-demo-1-6t-transceiver-and-switch-products-at-ofc26/)

### D35 Source Photonics · 1.6T2FR4 EML与SiPh

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T2FR4不仅EML样本 |
| 前稿遗漏/未知 | 首稿型号页冲突致整族实现不完整 |
| 本次补回或修正 | ECOC25列3nmDSP+200G CWDM EML的retimed 2FR4；OFC26 Delta测试清单另外直接列2FR4 SiPh。族实现可分别保留，型号页距离/标准冲突不让整个族归UNKNOWN。 |
| 差异原因 | 族级新闻与SKU详情冲突未分层 |
| 剩余缺口 | EML/SiPh对应SKU、SiPh光源细节、实际reach和型号PDF需澄清 |

来源：[OG19](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-at-ecoc-2025/)；[OG21](https://www.sourcephotonics.com/news/source-photonics-and-delta-electronics-join-force-to-demo-1-6t-transceiver-and-switch-products-at-ofc26/)；[OG23](https://www.sourcephotonics.com/product/spq-he2-8fo-cob/)

### D36 Source Photonics · 1.6T2LR4 EML

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T2LR4已列产品族 |
| 前稿遗漏/未知 | 首稿漏族 |
| 本次补回或修正 | 2025-09-26列retimed OSFP、3nmDSP和200G CWDM EML的2LR4；2026-03-17 traffic tests再次直接列2LR4(EML)。 |
| 差异原因 | 产品族遗漏 |
| 剩余缺口 | SKU、波长/温控、MUX/DEMUX、PD/TIA和当前出货量未知；不把‘至10km’跨段绑定全部1.6族 |

来源：[OG19](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-at-ecoc-2025/)；[OG21](https://www.sourcephotonics.com/news/source-photonics-and-delta-electronics-join-force-to-demo-1-6t-transceiver-and-switch-products-at-ofc26/)

### D37 Source Photonics · 1.6T4FR2 EML

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 高速产品目录应避免漏族 |
| 前稿遗漏/未知 | 首稿漏族 |
| 本次补回或修正 | ECOC25明确retimed OSFP、3nmDSP、200G PAM4 CWDM EML支持4FR2。 |
| 差异原因 | 产品族遗漏；OFC26短列表不证明该族停产 |
| 剩余缺口 | SKU、具体reach/连接器、接收BOM、当前出货未知 |

来源：[OG19](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-at-ecoc-2025/)

### D38 Source Photonics · 1.6T LRO DR8 SiPh

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T LRO应区别全DSP |
| 前稿遗漏/未知 | 首稿未给此族卡 |
| 本次补回或修正 | 2026-03-17测试清单明确1.6T LRO DR8 SiPh；此前OFC26目录列2DR4 LRO OSFP。 |
| 差异原因 | 产品族及电处理变体遗漏 |
| 剩余缺口 | LRO具体DSP型号/Tx结构和SKU未披露，不把EML样本3nmDSP搬入 |

来源：[OG20](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-announce-to-receive-two-industry-awards-for-two-product-families-during-ofc26/)；[OG21](https://www.sourcephotonics.com/news/source-photonics-and-delta-electronics-join-force-to-demo-1-6t-transceiver-and-switch-products-at-ofc26/)

### D39 Source Photonics · 1.6T InP PIC retimed/LPO

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 公司不能简单标EML派 |
| 前稿遗漏/未知 | 首稿只取EML会遗漏新平台 |
| 本次补回或修正 | OFC26获奖族表列InP PIC的1.6T IMDD retimed与LPO；应作为另一路线族，和DR8 EML/SiPh、LRO分别记。 |
| 差异原因 | 平台名单不能代替SKU，排他公司分类会过推 |
| 剩余缺口 | 具体PMD/接口、SKU、InP PIC内部实现未知；不能把InP PIC当纯SiPh或一定EML |

来源：[OG20](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-announce-to-receive-two-industry-awards-for-two-product-families-during-ofc26/)

### D40 Source Photonics · 新8004x200族与旧800DR8目录

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 目录可映射新产品SKU |
| 前稿遗漏/未知 | 8DO/8FO/8LO标签被误认新DR4/FR4/LR4有风险 |
| 本次补回或修正 | 当前800目录多数是8×100G DR8及2×400G FR4/LR4旧族；SPQ1/2标签点入正文更换为SPQ-8E8-DR-CDFO或SPQ-8E2-FR/LR-CDFOB。不能仅凭标签绑定2025年4×200G族。 |
| 差异原因 | 原厂分类/标题/正文料号错配与两代产品混淆 |
| 剩余缺口 | 新版4×200G精确SKU未可靠对齐 |

来源：[OG16](https://www.sourcephotonics.com/product-category/800g-transceivers/)；[OG24](https://www.sourcephotonics.com/product/spq1-8e8-8d0-coa/)；[OG25](https://www.sourcephotonics.com/product/spq2-8e2-8fo-coa/)；[OG26](https://www.sourcephotonics.com/product/spq2-8e2-8lo-coa/)

### D41 Source Photonics · 1.6T SKU规格冲突

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 1.6T2FR4/DR8有确切EML/PIN实现 |
| 前稿遗漏/未知 | 冲突不能使EML/PIN全部UNKNOWN |
| 本次补回或修正 | SPQ-HE8-8DO-COD及SPQ-HE2-8FO-COD页一致披露EML、PIN、3nmDSP。2FR4标题2km但特性500m/DR8；COE页也有同类复制冲突，冲突只留在reach/PMD/身份映射。 |
| 差异原因 | 矛盾字段需隔离，不能否定一致字段 |
| 剩余缺口 | 厂商修正后的PMD/reach/型号身份和PDF；TIA及MUX类型未知 |

来源：[OG22](https://www.sourcephotonics.com/product/spq-he8-8do-cob/)；[OG23](https://www.sourcephotonics.com/product/spq-he2-8fo-cob/)；[OG30](https://www.sourcephotonics.com/product/spq-he8-8do-coe-2/)

### D42 Source Photonics · 800SR8 VCSEL/PIN

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 完整目录包括短距类 |
| 前稿遗漏/未知 | 首稿只挑单模EML漏SR类 |
| 本次补回或修正 | SPQ-8E8-8SO-CQA：QSFP-DD SR8，VCSEL＋PIN、8通道电/光标准接口、双MPO12/APC、CMIS5.0，功耗<16W；目录另有OSFP短距标签。 |
| 差异原因 | 产品族目录遗漏 |
| 剩余缺口 | 其他短距标签逐型号核对及生产阶段未知 |

来源：[OG33](https://www.sourcephotonics.com/product/spq-8e8-8so-cqa/)；[OG16](https://www.sourcephotonics.com/product-category/800g-transceivers/)

### D43 Source Photonics · 800LPO/LRO与1.6AEC

| 对照项 | 内容 |
|---|---|
| 原对话主张 | 电处理/铜缆不能等同光学平台 |
| 前稿遗漏/未知 | 完整族目录未列线性与铜互连 |
| 本次补回或修正 | OFC25/26均列800LPO/LRO演示族，未明确具体PMD/光平台；OFC26列1.6TAEC OSFP铜互连。AEC发射激光、MUX、PD/TIA不适用。 |
| 差异原因 | 独立维度没有进入公司目录 |
| 剩余缺口 | 800LPO/LRO对应SKU/光路线未知；AEC具体规格未知 |

来源：[OG18](https://www.sourcephotonics.com/news/source-photonics-announce-the-product-availability-of-its-200g-per-lane-based-1-6t-and-800g-pam4-transceiver-family-products-at-ofc25/)；[OG20](https://www.sourcephotonics.com/news/source-photonics-to-spotlight-its-latest-optical-innovations-announce-to-receive-two-industry-awards-for-two-product-families-during-ofc26/)

## 仍缺什么

当前资料只给公司角色或工艺能力的条目，仍缺具体产品目录；目录已有产品但没有规格书的，缺环节路线；环节路线已知的，可能仍缺器件型号、材料牌号、制造设备、测试条件和量产状态。各项放在公司目录与型号卡边界中，不再统一归为“内部实现未知”。

目标3仍须同速率、距离、温区、主机条件和误码率要求的对比资料。例如Lumentum的22W与16W是不同版本典型值，温区亦不同，不能直接把6W全部归因于TRO。目标4还需产品与实际工序、设备、材料、测试逐条关联；某设备商有相关设备，不等于已证明某模块采用它。