# WP-GROK notes — 产品路线与 BOM 骨架

- Owner: WP-GROK
- as_of: 2026-07-24
- 写入范围: `work/grok/structure_nodes.csv`, `work/grok/structure_edges.csv`, `work/grok/notes.md`
- 非范围: 公司/能力/供货、工序/设备、canonical `data/`、其他工包目录

## 1. 范围裁决

本包只建 **应用 → 产品路线 → 功能 → 部件/材料** 骨架。

刻意不写：

- `process` / `equipment_category`（属 WP-CLAUDE）
- `organizations` / capabilities / trade（禁止）
- 1.6T、LPO、CPO、OpenZR+、800ZR（SPEC 非本轮填满对象；仅在笔记中排除）

## 2. 三路线一句话

| 路线 | 检测体制 | 复用方式 | 典型光口 | 典型距离 | 标准锚点 |
|---|---|---|---|---|---|
| 800G DR8 | 直检 PAM4 | 8 路并行光纤 | MPO/MTP | ≤500 m SMF | IEEE 802.3df 800GBASE-DR8 |
| 800G 2×FR4 | 直检 PAM4 | 2×(4λ CWDM) | 双 LC duplex | 2 km SMF | IEEE 802.3cu 400GBASE-FR4 ×2 |
| 400ZR | 相干 DP-16QAM | 单载波 DWDM | 可插拔 DCO（MSA 另定） | DCI/城域黑链路 | OIF 400ZR IA |

## 3. 共同节点 vs 路线特有节点

### 共同（三路线或直检两路线）

- 应用之上的共享功能：`SN-FN-ELEC-HOST-IO`、`SN-FN-OPT-TX`、`SN-FN-OPT-RX`、`SN-FN-MODULE-MGMT`
- 直检共享：`SN-FN-PAM4-SIG`、`SN-FN-HOST-FEC-TARGET`；部件 `SN-COMP-DD-DSP`、`SN-COMP-PIN-PD`、`SN-COMP-TIA`、`SN-COMP-DRIVER`
- 可插拔共享：`SN-COMP-PLUG-HOUSING`、`SN-COMP-HPCB`、`SN-COMP-MCU-CMIS`
- 材料平台：`SN-MAT-INP`、`SN-MAT-SIGE-CMOS`（按实现选用）

### DR8 特有

- 功能：`SN-FN-PARALLEL-FIBER`
- 部件：`SN-COMP-EML-1310`、`SN-COMP-MPO-RECEPTACLE`；可选替代 `SN-COMP-SIPH-TX`

### 2×FR4 特有

- 功能：`SN-FN-CWDM-MUX`
- 部件：`SN-COMP-EML-CWDM4`、`SN-COMP-CWDM-MUXDEMUX`、`SN-COMP-LC-RECEPTACLE`
- 材料：`SN-MAT-SILICA-FILTER`

### 400ZR 特有

- 功能：`SN-FN-COH-MOD`、`SN-FN-COH-DETECT`、`SN-FN-COH-DSP-FEC`、`SN-FN-DWDM-TUNE`
- 部件：`SN-COMP-ITL`、`SN-COMP-IQ-MOD`、`SN-COMP-ICR`、`SN-COMP-COH-DSP`；实现相关 `SN-COMP-TEC`

## 4. 分类纪律（争议点）

1. **Silicon Photonics**
   - 不建成 `application` / `product_route` / 架构节点。
   - 建成可选部件 `SN-COMP-SIPH-TX` + 材料 `SN-MAT-SI-PLATFORM`，并以 `alternative_to` 相对 `SN-COMP-EML-1310`。

2. **主机侧 FEC**
   - 直检 FEC 在主机，不写成 module `component`。
   - 仅保留功能约束 `SN-FN-HOST-FEC-TARGET`。

3. **测试**
   - 无任何 test/ATE 工序写入 `component`。

4. **CPO / LPO / COB**
   - 未建节点。LPO 会移除/弱化模块侧 `SN-COMP-DD-DSP`，属另一路线，不混入 DR8/2×FR4。

5. **壳体 QSFP-DD/OSFP**
   - 收束为 `SN-COMP-PLUG-HOUSING`（机械/热封装部件），不把 MSA 名称拆成多条产品路线。

6. **2×FR4 命名**
   - 建模为“两路 400GBASE-FR4 聚合的 800G 模块”，不是虚构的单一 `800GBASE-FR8` 节点。

## 5. 重要性初判说明

- `structural_critical`：该路线 mandatory 功能/关键部件（如并行光纤、CWDM、相干 DSP 功能）。
- `bottleneck_candidate`（均为 **hypothesis**，非 verified 产能证据）：
  - `SN-COMP-SIPH-TX`（激光集成/良率）
  - `SN-COMP-ITL`（线宽/功耗/调谐）
  - `SN-COMP-COH-DSP`（可插拔功耗与面积）
- 未把“常见紧张器件”在无结构依据时升格为 bottleneck。
- `importance_confidence=hypothesis/unknown` 的节点不假装 verified。

## 6. 结构证据检索轨迹（URL + 检索日期）

检索日期均为 **2026-07-24**。只采用标准/官方/原始技术资料或标准解读页；厂商营销博客不作为升格依据。

| 主题 | 来源 | URL | 用途 |
|---|---|---|---|
| 800GBASE-DR8 波长/并行/500m/MPO | TIA FOTC（IEEE 802.3df 应用解读） | https://www.tiafotc.org/ieee-802-3-ethernet-standards-update/singlemode-standards-update/800gbase-dr8/ | structure |
| 800G/400G PHY 修订 | IEEE SA 802.3df-2024 | https://standards.ieee.org/ieee/802.3df/11107/ | structure |
| DR8 模块形态与双 MPO 等实现 | Cisco OSFP 800G DS（实现例，不定义BOM全集） | https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/osfp-800g-transceiver-modules-ds.html | structure partial |
| 400GBASE-FR4 CWDM 网格 | IEEE 802.3cu 公开 baseline PDF | https://www.ieee802.org/3/cu/public/May19/lewis_3cu_01a_0519.pdf | structure |
| 800G 2×FR4 = 2×FR4 电/光接口 | Jabil 800G OSFP 2xFR4 DS | https://www.jabil.com/dam/jcr:c902fa95-6745-457f-bfdc-ac415f773367/Jabil_800G%20OSFP%202xFR4%20Optical%20Transceiver%20Datasheet_DIGITAL_08%20-%20Final.pdf | structure |
| 400ZR DP-16QAM / DSP / C-FEC / pluggable DCO | OIF 400ZR IA PDF | https://www.oiforum.com/wp-content/uploads/OIF-400ZR-03.0.1.pdf | structure |
| 400ZR IA 发布说明 | OIF 新闻稿 | https://www.oiforum.com/oif-publishes-implementation-agreement-for-400zr-coherent-optical-interface/ | structure |

未获取到的付费全文（如 IEEE 802.3df 条款 PDF 全文）标记为 **不可在本环境完整核验**；骨架字段因此大量保持 `proposed/admitted` + `hypothesis`，不写入伪造 `evidence_ids`（evidence 表不在本工包）。

## 7. 待核技术问题（给集成/下一轮）

1. DR8 发送以 EML 还是硅光为主路径？标准不规定器件，需 capability 层统计，不在本包裁决。
2. 2×FR4 的 100G/lane 与历史 50G/lane FR4 模式并存时，DSP/激光代际是否拆节点？本包未拆。
3. 400ZR 的 TX 激光与 LO 是否总是同一 ITL 组件？本包合并为 `SN-COMP-ITL`，可能过粗。
4. `SN-COMP-TEC` 是否 mandatory？保持 `unknown`。
5. IQ 调制器材料：InP PIC vs 硅光调制 + 外置激光，本包仅在材料边上标 optional。
6. 直检 `SN-COMP-DRIVER` 与激光器共封装比例未知，requiredness 用 `route_specific`。
7. 工序/设备轴未建：封装、耦合、老化、测试等留给 WP-CLAUDE，避免把测试写成部件。

## 8. 自检清单（本包）

本地 Python 契约抽检（2026-07-24）结果：**PASS**

- 节点 40：application 3 / product_route 3 / function 12 / component 18 / material 4
- 边 77：drives 5 / implements 22 / requires 39 / uses_material 9 / alternative_to 2
- 三路线均可从 application `drives` → route `implements` → function `requires` → component/material
- 无公司节点、无 trade/capability、无 `process`/`equipment_category`、无测试工序伪装 component
- 所有 `bottleneck_candidate` 的 `importance_confidence` 均为 `hypothesis`
- ID 前缀 `SN-` / `SE-`，CSV 头字段与 CONTRACT 一致
