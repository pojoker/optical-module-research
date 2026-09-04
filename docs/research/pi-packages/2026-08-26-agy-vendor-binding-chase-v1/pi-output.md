# 交付：公司—产品—SiPh 路线绑定（2026-08-26 轮）

> **后裁决勘误（以 `pi-adjudication.md` 为准）**：两款芯速联产品只能称“同一供应商的配对 exact listings”，未证明属于同一产品族或内部实现完全相同；“唯一”仅限本轮样本。Q1 应映射 TQ002/TQ003 + WQ002，Q6 应映射 TQ010/TQ011 + WQ003，Q8 应收窄到 TQ013 + WQ004。第四部分所有问题都是现有问题合同的细化，不是新的问题节点。

仅消费 `pi-handoff.md`；未读取 AGY raw、未联网、未调用工具。未新建 QID、未写知识库、未补全 UNKNOWN、无路线优劣排序、无客户/出货推断。

---

## 一、公司—路线观察卡

### 1.1 中际旭创（中际旭创股份有限公司 / 苏州旭创）

| 字段 | 值 |
|---|---|
| observation / evidence id | **E-INNO-1** |
| URL | `https://static.cninfo.com.cn/finalpage/2023-04-24/1216523562.PDF` |
| evidence_subject | OFC2022 现场展示"基于自主设计硅光芯片"的 800G 硅光模块：`800G 可插拔 OSFP 2*FR4` 与 `QSFP-DD800 DR8+` |
| product_or_family | 800G 可插拔硅光模块（OSFP 2*FR4 / QSFP-DD800 DR8+） |
| platform_raw | 硅光（SiPh，基于自主设计硅光芯片） |
| electrical_architecture_raw | UNKNOWN（未给出 DSP/LPO/重定时等标签） |
| form_factor_raw | OSFP（标签 2*FR4）、QSFP-DD800（标签 DR8+） |
| lane_raw | 模块级 800G；per-lane 速率 UNKNOWN（标签含 FR4/DR8+，不自行换算） |
| reach_raw | UNKNOWN |
| power_raw | UNKNOWN |
| maturity_evidence | **demo**（OFC2022 现场展示）；PDF p.27 仅支持"开发成功并进入送测"，不支持量产 |
| 补充边界 | 无 exact SKU；量产/出货/客户 UNKNOWN；不推断 modulator/laser/detector/process/yield/cost |

### 1.2 新易盛（Eoptolink）

| 字段 | 值 |
|---|---|
| observation / evidence id | **E-EOPT-1** |
| URL | `https://eoptolink.com/news/13-new-products/348-eoptolink-demonstrates-industry-1st-200g-lane-lpos-with-100g-lane-800g-lpos-entering-mass-production` |
| evidence_subject | OFC2024 官方演示 `800G OSFP DR4 LPO`，使用 silicon photonics PIC，4×200 Gb/s；页面明确称本次为 demonstration |
| product_or_family | 800G OSFP DR4 LPO（4×200G） |
| platform_raw | silicon photonics PIC（SiPh） |
| electrical_architecture_raw | LPO（200G/lane 标签）— 不推断电芯片存在/缺失、FEC 位置 |
| form_factor_raw | OSFP |
| lane_raw | 4×200 Gb/s |
| reach_raw | UNKNOWN |
| power_raw | UNKNOWN |
| maturity_evidence | **demo**（官方页面 demonstration） |
| 禁止线 | 同页后文 100G/lane LPO 的 high-volume production 不得转移给 200G/lane DR4；`EOLO-138HG-5H-SM` / `EOLD-138HG-5H-SM` 不绑定为 SiPh |
| 补充边界 | reach、特定 SKU 的 SiPh 绑定、工艺/良率/成本、量产/出货/客户 UNKNOWN |

### 1.3 芯速联（Hyper Photonix）

身份边界：芯速联与光梓信息为不同公司身份，本轮不合并、不关联。

| 字段 | E-HYPER-1 | E-HYPER-2 |
|---|---|---|
| URL | `https://www.hyperphotonix.com/product_detail/1254.html` | `https://www.hyperphotonix.com/product_detail/1253.html` |
| evidence_subject | 精确型号 `HSO6-800-LP-P8S`；页面标题 `800G OSFP112 DR8 LPO FNT 硅光模块` | 精确型号 `HSD2-800-LP-P8S`；页面标题 `800G QSFP112-DD DR8 LPO 硅光模块` |
| product_or_family | HSO6-800-LP-P8S | HSD2-800-LP-P8S |
| platform_raw | 硅光（SiPh） | 硅光（SiPh） |
| electrical_architecture_raw | LPO（DR8 LPO；"FNT"保留为 raw label，语义不自行解释） | LPO（DR8 LPO） |
| form_factor_raw | OSFP（OSFP112） | QSFP-DD（QSFP112-DD） |
| lane_raw | 8×106.25 Gb/s | 8×106.25 Gb/s |
| reach_raw | 500 m SMF | 500 m SMF |
| connector_raw（→TQ008） | 双 MPO-12/APC | MTP/MPO-16 APC |
| power_raw | ≤9 W（PDF 标称，单产品 datasheet 上限） | ≤9 W（同左） |
| maturity_evidence | **listed_product**；GA/量产/出货 UNKNOWN | **listed_product**；GA/量产/出货 UNKNOWN |

两条证据是两个独立产品型号；连接器等规格不得互相拼装。≤9 W 为单产品字段，不与其他公司产品功耗直接比较。

---

## 二、TQ009→TQ013 挂载建议

### 设计判断 1：是否复用 `route_service_evidence` 并增加 `evidence_stage`？

**结论：复用，不新增第二套关系。**

1. 四条证据结构同构——均为"公司 × 产品/型号 × 路线 × 直接观察"，差异只在证据阶段；阶段是证据属性而非关系语义差异。
2. 单一关系类型 + `evidence_stage = demo | listed_product | shipment | customer_adoption` 枚举，可同集纵向比较（如 demo 观察 vs listed_product 观察的覆盖），未来阶段证据只需追加记录，不改 schema。
3. 阶段升级用**新增记录**实现（不原地改写旧记录），保证证据可追溯；`confirmed service group` 的创建是独立决策，不随 evidence_stage 自动触发。
4. 本轮四条全部只到观察层：demo 与 listed_product 均不等于 shipment/customer service。

### 挂载表

| QID | 挂载内容 | 禁止线 |
|---|---|---|
| TQ006 | LPO raw label + lane raw：E-EOPT-1 "200G/lane LPO, 4×200 Gb/s"；E-HYPER-1/2 "DR8 LPO, 8×106.25 Gb/s" | 只存标签与 lane；不补电架构内部职责；不推断电芯片存在/缺失与 FEC 位置 |
| TQ007 | SiPh platform_raw：E-INNO-1 "基于自主设计硅光芯片"；E-EOPT-1 "silicon photonics PIC"；E-HYPER-1/2 "硅光模块" | 仅平台绑定；不推断 modulator/laser/detector/process/yield/cost |
| TQ008 | 封装/连接器：E-INNO-1 OSFP 2*FR4、QSFP-DD800 DR8+；E-EOPT-1 OSFP；E-HYPER-1 OSFP112 + 双 MPO-12/APC + ≤9 W；E-HYPER-2 QSFP112-DD + MTP/MPO-16 APC + ≤9 W | ≤9 W 为单产品字段，不跨厂比较；两款芯速联型号不互拼 |
| TQ009 | 三条路线画像观察（非正式 RP）：① 中际旭创 800G SiPh 可插拔双形态（demo）；② 新易盛 800G OSFP DR4 LPO + SiPh（demo）；③ 芯速联 800G DR8 LPO + SiPh 双封装（listed_product） | 不创建正式 Route Profile；按产品/族记录，不合并为公司层画像 |
| TQ013 | 四条 `route_service_evidence`：E-INNO-1（demo）、E-EOPT-1（demo）、E-HYPER-1（listed_product）、E-HYPER-2（listed_product） | 不创建 confirmed service group；芯速联与光梓信息不合并 |
| TQ014 | 仅挂第四部分 Q4/Q5（取得同条件比较证据的研究问题） | 不输出优势结论 |
| WQ002/WQ003/WQ004 | 本轮保持空；所需证据见第三部分 | 不写 WHY |

（证据 URL 均见第一部分对应卡片。）

---

## 三、双体系 + WHY 差距表

| 层 | 本轮新增 | 仍缺 |
|---|---|---|
| 物理体系 | raw 字段落地：SiPh 平台 4 条；LPO 标签 3 条；封装/连接器 4 条；lane raw 两种（4×200 Gb/s、8×106.25 Gb/s）；reach（芯速联 500 m×2；另两家 UNKNOWN）；功耗（芯速联 ≤9 W×2，单产品字段） | 调制器/激光器/探测器集成、工艺、良率、成本；功耗统一测量口径（≤9 W 不可跨厂比）；中际旭创/新易盛的距离字段；FEC 位置与电芯片配置（LPO 不推断）；一切"同条件可比"的物理量 |
| 路线体系 | 三家公司—路线直接观察：中际旭创（demo）、新易盛（demo）、芯速联（listed_product×2）；覆盖 demo/listed_product 两类证据阶段；公司身份保持独立 | shipment 与 customer_adoption 两个阶段；confirmed service group；正式 Route Profile；跨厂同条件路线画像；路线优劣（本轮不答） |
| WHY 桥 | 零新增；WQ002/WQ003/WQ004 保持空 | 端到端证据链：上游需求/约束证据（→WQ002 口径）、条件化优势/代价的同条件实测（→WQ003 口径）、下游组件/工艺/公司角色证据（→WQ004 口径）；WHY 语句本身 |

**设计判断 2 的回答**：本轮补到了"物理体系 raw 字段层 + 路线体系的 demo/listed_product 观察层"；尚缺"路线体系的 shipment/customer_adoption 层"以及"连接两体系的 WHY 证据链"（其最小前提是同一产品族内的同条件比较（TQ014）与至少一条阶段升级证据（TQ013））。

---

## 四、下一轮单一最小闭环

**选择配对产品清单：芯速联两款 800G DR8 LPO SiPh exact listings**（E-HYPER-1 `HSO6-800-LP-P8S`，URL `…/1254.html`；E-HYPER-2 `HSD2-800-LP-P8S`，URL `…/1253.html`）。是否属于同一正式产品族、内部实现是否相同均为 UNKNOWN。

选择理由（仅证据结构角度，非优劣判断）：

1. 在本轮样本中，这两款清单证据相对完整（lane、reach、连接器、功耗均有 raw 值），可作为 TQ014 受控比较的检索起点；但当前只证明公开字段相同/不同，不能断言“仅封装不同”。
2. 上游可查约束集中：106.25G/lane 电生态下 DR8 的选择（对照面即新易盛演示的 4×200G 路线）、SiPh 平台选择边界、双封装的系统取舍。
3. 下游物理变化可检验（连接器损耗预算、LPO 功耗包络），且公司角色证据缺口明确（listed_product → shipment 的推进路径）。

### 研究问题（8 条，按"上游约束 → 路线选择 → 条件化优势/代价 → 下游物理变化 → 公司角色证据"排序；本轮不回答）

| # | 环节 | 研究问题 | 映射 QID | 重复判断 |
|---|---|---|---|---|
| Q1 | 上游约束 | 要判定 800G 选 DR8（8×106.25G，E-HYPER-1/2）而非 DR4（4×200G，E-EOPT-1）的上游选择约束，需收集什么证据（交换机 SerDes 代际规格、客户对距离/功耗的公开要求、模块功耗测试方法）？ | TQ002/TQ003 + WQ002 | 现有问题合同的细化；本轮不写 WHY |
| Q2 | 上游约束 | 检验 SiPh 平台选择边界需要哪些证据（平台成本、耦合损耗、良率口径）？本轮四条只证明"SiPh 被选择"，不证明"为何选择"。 | TQ007（细化：platform_raw 之外的边界证据收集项） | 不重复；仍不推断内部构成 |
| Q3 | 路线选择 | 同一供应商的两款 exact listings 分别采用 OSFP112（双 MPO-12/APC，E-HYPER-1）与 QSFP112-DD（MPO-16，E-HYPER-2）；在不预设同族/同实现的前提下，各自对应哪些下游系统约束（面板空间、散热路径、接线方式）？ | TQ008（细化：封装字段 → 系统约束） | 现有问题合同的细化 |
| Q4 | 条件化优势/代价 | 先验证除公开字段外是否同条件；若成立，再比较双 MPO-12/APC 与 MPO-16 的差异代价如何测（插损、面板密度、布线复杂度）；若不成立则输出 `not_comparable`。 | TQ014 | 现有问题合同的细化 |
| Q5 | 条件化优势/代价 | 若未来把新易盛 4×200G DR4 LPO（E-EOPT-1，demo）纳入比较，必须先取得哪些等条件字段（距离、功耗口径、测试方法、链路预算）？ | TQ014 | 不重复；禁止把 100G/lane 量产主张转嫁给 200G/lane；禁止把 EOLO/EOLD SKU 绑定 SiPh |
| Q6 | 下游物理变化 | 在 LPO 前提下，≤9 W 功耗包络与 500 m 链路预算对电芯片组件、SiPh 工艺、FEC 位置分别施加哪些“可检验约束”？（只列检验项，不推断答案） | TQ010/TQ011 + WQ003 | 现有问题合同的细化；本轮不写 WHY |
| Q7 | 公司角色证据 | listed_product（E-HYPER-1/2，GA/量产/出货 UNKNOWN）升级到 shipment/customer_adoption 需要哪类证据（官方量产公告、datasheet 修订、客户公开验证）？ | TQ013（细化：evidence_stage 升级路径） | 不重复 |
| Q8 | 公司角色证据 | 三条公司观察（中际旭创 demo/送测、新易盛 demo、芯速联 listed_product）若要支撑公司角色的 WHY，各自还缺哪一层证据（设计能力 vs 量产 vs 客户采纳）？ | TQ013 + WQ004 | 现有问题合同的细化；只列证据类型不写 WHY |

未新建任何 QID；全部问题均为现有问题合同的研究注记/细化。
