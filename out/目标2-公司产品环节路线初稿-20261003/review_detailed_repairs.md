# 详细配置补值独立审阅

核验日：2026-10-03。范围为当前 `repair_draft.py`、`build_draft.py`、`domestic_gap_repair.json`；仅对照现有证据，不新增网页搜索。行号对应本次读取的脚本版本。

新增七款配置的光学平台、距离、接口和功耗大体符合补核记录。光迅 RTXM700-546/532 没有误套发布稿中的 3nm DSP；VR8 没改名为 SR8，10km LR 保持八路并行。交付前仍需修正环节拆分、未知状态和版本边界，否则“逐环节”表会把接收、驱动和电处理重复计为已知。

## 必须修正

1. **TX/RX 聚合字符串不能直接充当每个环节的内容。** `repair_draft.py:47–48` 将 `dsp_driver_tia` 同时赋给 `dsp`、`receiver`、驱动补值；`build_draft.py:103、106–107` 又复制到驱动、探测器、接收放大。结果包括：2FR4/VR8 的探测器行含发射驱动，DR8 的接收字段只有“Driver/TIA集成DSP”，LR 的驱动行含接收 PD。建议保留产品卡的联合链路概括，同时给驱动、PD、TIA 三行具体补值。最小改法为使用现有 `extra_stages`，无需改数据架构。

2. **`extra()` 的统一直接披露状态会把缺口升格。** `repair_draft.py:11` 强制所有补值为“厂商直接披露”，覆盖 `build_draft.py:120–121` 已算出的状态。DR8“本PDF未列探测器具体结构/材料”因此被标成直接披露。应允许显式状态；纯缺口写“UNKNOWN：所核PDF未列”，已知与缺口混合写“部分披露/有保留”。CMIS 已知、MCU 未取得的联合行同样不能被计为全部实现已披露。

3. **状态函数仍漏判“未列”“未取得”。** 当前 `build_draft.py:41–48` 的纯函数核验中，“SiPh调制器；激光器未列”和“器件实现未列”返回直接披露；“本PDF未列探测器…”也返回直接披露。仅靠扩大关键词仍会漏判，建议对这些新增配置显式指定字段/补值状态。DR8 的发光字段只有“PDF未列EML/SiPh”，应为未知而非“部分披露”。

4. **光迅已读页面的缺项，被初始化成了未检索。** `repair_draft.py:37、50–51` 使 546 的电口/DSP/PD/TIA、532 的 DSP/PD/TIA 为默认“尚未取得专项资料”。但补核记录已明确 ADR4、A2FR 页面分别未列这些字段。应写“UNKNOWN：所核 ADR4/A2FR 产品页未列；其他来源待补”，保留源 URL 作已读范围，避免把已检查的缺项与尚未检索的 PCB、时钟混为一类。

5. **缺口与别名冲突没有完整进入新卡边界。** `repair_draft.py:38` 统一使用一般边界，漏掉 FR8 当前目录 `-PX` 与 PDF `-P`、VR8 目录 `-MX` 与 PDF `-M`、目录 C 温区与 PDF 15–70°C 的差异。2FR4 的 `-XX/-1` 已保留在名称中，但仍应在边界明确“别名待补”。建议从相应 correction 的 `remaining` 继承，不将缺 SKU 映射变成光学路线未知。

## 各款最小修正值

| 配置与主证 | 正确保留 | 环节拆分/边界建议 |
|---|---|---|
| FR8 EOLO-168HG-02-P，EFR | 8×106.25G 电口；8 CWDM/EML；8 PD，PIN；2×4ch TIA；2km/LC/<16W | 驱动与 retimer 的集成描述按原文限定；已加“不是激光器与CMOS同芯片”的边界，保留。目录 -PX/PDF -P 别名待补。MUX 工艺继续未知。 |
| 2FR4 EOLO-168HG-02-XX / PDF -1，E2FPDF | 8 EML；2 MUX/2 DEMUX；8 PIN/PD；2×4ch TIA；双LC/2km/<16W | 电处理=双向PAM4 retimer；驱动=8ch modulator driver；PD=8/PIN；TIA=2×4ch。不可把本款 TIA 说成集成 DSP。合波行只写2 MUX，分波行只写2 DEMUX。 |
| VR8 EOLO-858HG-01-M，EVPDF | 850nm VCSEL；8 PIN/PD；MPO16APC；OM3 30m/OM4 50m；<15W，15–70°C | 驱动=2×4ch driver，TIA=2×4ch。去掉统一补值中的“驱动集成关系”，该记录未披露 Driver/TIA 集成DSP；保留型号和温区差异。 |
| DR8 EOLO-138HG-5H-xDx，EDPDF | 8×106.25G；1310nm并行；Driver/TIA 集成DSP；双MPO12；500m/<14.5W | 驱动=Driver 集成DSP，接收放大=TIA 集成DSP；光源平台、PD结构/材料未知。不能由“8光通道”补写具体 PD 类型。 |
| 并行8×100G LR EOLO-138HG-10-xDx，ELPDF | 8 EML/1310nm并行；8 PD+integrated TIA；Driver/TIA 集成DSP；双MPO12/10km/<14.5W | PD=8个，结构/材料未列；TIA 集成关系单列。保持“并行LR”，不改成波分 LR8，不套用其他PDF的 PIN。 |
| 800G DR4 RTXM700-546，ADR4 | SiPh modulator；4双工光通道，212.5Gbps/路；MPO12APC/500m/16W/0–70°C | 电通道、DSP、PD/TIA 为“本页未列”；不由 OSFP224 名称推电通道；CW光源继续未知。 |
| 1.6T 2FR4 RTXM700-532，A2FR | 8×200G电口/1600GAUI8；SiPh CWDM；双LC/2km/26W/0–70°C | DSP、CW激光、PD/TIA 为“本页未列”；保持与2025 ECOC 3nm产品族未对齐的边界。 |

以上七款“原厂产品页/规格书登记；不等于逐型号当前量产”的成熟阶段正确，当前证据不支持升级为量产或在手订单状态。

## 阶段补值和引用还需核对的两处

- `repair_draft.py:17–20` 新加中际三款 CMIS 5.x 与 0–70°C。当前 `domestic_gap_repair.json` 的 I1/I4 与对应 correction 没有这些字段的局部锚；`domestic_verified.json` 也未收录。不能仅从补核JSON证实这两组补值。若根代理另有直接页面读回，应附具体分段原句/位置；否则先撤回这两组补值。该建议是当前资料间一致性检查，不等于断言原厂页面不存在这些信息。
- `repair_draft.py:8` 会丢掉源状态（当前取回、旧缓存、别名冲突）和核对日期；`build_draft.py:114、139` 默认给字段挂全部产品来源，再给每行挂全部产品日期。新七款多数单来源，暂不造成跨源混配；中际和旧多来源卡则会把更新后的管理页一并列成旧路线主证。应保留源状态；有 `source_map` 的逐环节行仅显示该行实际源及日期。当前海外光接口行组合 `package+optical` 来源的处理正确，应保留。

核验方法：静态逐行对照，并在内存中复现状态函数和环节输出；未执行完整渲染或机器门。审阅中一次脚本前缀执行意外触发现有 `write_comparison()`，重写了《对话与UNKNOWN纠错.md》《对话主张差异表.csv》，已立即告知根代理；未改 canonical、源 JSON 或脚本。后续函数核验改为 AST 只提取定义，未再触发顶层写入。
