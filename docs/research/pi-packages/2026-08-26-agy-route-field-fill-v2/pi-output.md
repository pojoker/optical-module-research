# 800G EML 实例字段卡与 SiPh 绑定缺口 — draft-only 研究小样

> **裁决后勘误（2026-08-26）**：本文件是 Pi 原始结构小样，不是最终事实入口。页码、短引文、Type 2、符号速率、波长范围与功耗上限已由 `source-excerpts.md` 补齐；四条注记“均不重复”的原判断已由 `pi-adjudication.md` 改为 **1 新 + 3 合并**。下游必须先读 `README-FIRST.md`，不得单独消费本文件。

> **前置说明**：本小样仅消费随包提供的 `pi-handoff.md`（agy-route-field-fill-v2），未访问其他文件、网络或上下文，未补充任何记忆中的行业事实。全部内容为 draft-only，不落知识库；`canonical_write_performed: false`。
>
> **锚点约定**：handoff 未携带具体页码与逐字引文，因此凡 observed 字段以「来源标签 S-EML-1 / S-EML-2 + URL」为锚；页码/页码位置与短引文一律 `UNKNOWN`（回源待补），禁止虚构逐字引文。凡无来源支持的字段一律 `UNKNOWN`。

**源映射（URL 为本轮唯一锚点）**

| 标签 | 来源 | URL |
|---|---|---|
| S-EML-1 | Coherent preliminary datasheet，*Preliminary Product Specification 800G-DR8+ OSFP Optical Finisar Transceiver FTCE4527E1PxA-2N*，Oct. 2023 Rev A1 | `https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4527e1pxa-2n-transceiver-ds.pdf` |
| S-EML-2 | Coherent 产品页，*2x400G DR4+ OSFP Optical Transceiver* | `https://www.coherent.com/networking/transceivers/datacom/FTCE4527E1PxA-2N` |

---

## 第一部分：EML observed-instance 字段卡（保留 UNKNOWN）

> 注：本卡记录**产品系列** `FTCE4527E1PxA-2N` 的系列级声明，不构成 exact orderable SKU，不推断 GA/量产、TEC、内部芯片、内部光学耦合、FEC location 或 heatsink 解释。

### TQ005 — 产品/链路标准

| 字段 | 状态 | draft-only 值 | 来源 | 页码/短引文锚点 |
|---|---|---|---|---|
| 产品系列主张 | observed | `FTCE4527E1PxA-2N`（系列级，preliminary 文档） | S-EML-1、S-EML-2 | URL 已锚定；页码/引文 UNKNOWN（回源待补） |
| 链路标准候选 | observed | 800G DR8+（datasheet 标题及系列主张） | S-EML-1 | 同上 |
| 应用声明 | observed | 2×400G DR4+ 与 8×100G breakout 为同系列公开应用声明；不据此拆成两个独立 SKU | S-EML-1（DR8+/breakout applications）、S-EML-2（页面标题 2x400G DR4+） | 同上 |
| 标签一致性 | conflicting_labels | 同系列来源并存 2×400G DR4+ 与 800G DR8+ 标签（页面标题/datasheet 标题/applications） | S-EML-1 + S-EML-2 | 同上；只记录共存，不解释 |
| 精确标准归属 | unknown | 具体标准条目归属仍需后续核对 | — | — |
| exact orderable SKU | unknown | 系列声明 ≠ exact SKU；禁止改写 | — | — |

### TQ006 — 电接口 / FEC

| 字段 | 状态 | draft-only 值 | 来源 | 页码/短引文锚点 |
|---|---|---|---|---|
| 电接口 | observed | retimed 8×100G PAM4 electrical interface | S-EML-1 | URL 已锚定；页码/引文 UNKNOWN |
| 聚合速率 | observed | 850 Gb/s aggregate bit rate | S-EML-1、S-EML-2 | 同上 |
| lane signaling | observed（字段存在） | datasheet 定义 lane signaling；具体值本轮 UNKNOWN | S-EML-1 | 同上 |
| FEC location | unknown | FEC location UNKNOWN | — | — |

### TQ007 — 发射/接收组件（光子平台相关）

| 字段 | 状态 | draft-only 值 | 来源 | 页码/短引文锚点 |
|---|---|---|---|---|
| 发射/接收（系列级） | observed | Transmitter = EML；Receiver = PIN | S-EML-2 | URL 已锚定；页码/引文 UNKNOWN |
| 波长带 | observed | 1310 band | S-EML-2 | 同上 |
| 传输距离 | observed | 2 km（G.652 SMF） | S-EML-1、S-EML-2 | 同上 |
| 内部实现 | unknown | 内部 EML topology、TEC、TOSA/ROSA、driver/TIA、lens coupling 一律 UNKNOWN（S-EML-1 明确不可消费；S-EML-2 只到系列级） | — | — |

### TQ008 — 封装 / 热

| 字段 | 状态 | draft-only 值 | 来源 | 页码/短引文锚点 |
|---|---|---|---|---|
| 可插拔形态 | observed | hot-pluggable OSFP | S-EML-1 | URL 已锚定；页码/引文 UNKNOWN |
| OSFP Type 细分 | observed（授权 draft-only 值） | OSFP Type 2（handoff TQ008 授权行值；注意 S-EML-1 可消费范围仅列 "OSFP"→回源未见 "Type 2" 字样时降级为 OSFP-only） | S-EML-1 | 同上；需回源复核 |
| 光学连接器 | observed | Dual MPO-12 APC | S-EML-1 | 同上 |
| 温度选项 | observed | 温度选项 schema 存在（S-EML-1）；具体值 0–70°C（S-EML-2） | S-EML-1、S-EML-2 | 同上 |
| heatsink 状态 | conflicting_labels | `UNKNOWN_CONFLICTING_LABELS`；不解释冲突原因 | — | — |

### TQ009 — observed instance seed（annex，非正式 RP）

| 字段 | 值 |
|---|---|
| instance key | 产品系列 `FTCE4527E1PxA-2N`（series-level；非 exact orderable SKU） |
| 文档成熟度 | Preliminary（S-EML-1，Oct. 2023 Rev A1）→ 不据此推断 GA/量产 |
| 观测包 | agy-route-field-fill-v2 / 2026-08-26 |
| 证据来源 | S-EML-1、S-EML-2（URL 见源映射；页码/逐字引文 UNKNOWN） |
| 保留 UNKNOWN 字段 | GA/量产状态、TEC、内部 EML topology、TOSA/ROSA、driver/TIA、lens coupling、FEC location、factory test coverage、heatsink 解释、精确标准归属、module power ceiling 具体值、wavelength range 具体值、exact SKU |

**同源补充 observed 字段（S-EML-1，仅记录字段存在性，具体值一律 UNKNOWN）**
- wavelength range：字段存在；具体数值 UNKNOWN
- module power ceiling：字段存在；具体数值 UNKNOWN
- CMIS/I2C：字段存在；细节 UNKNOWN
- regulatory fields：字段存在；条目 UNKNOWN

---

## 第二部分：Evidence-subject 分层示意

```
L4  demo evidence（demo 证据）
    Intel OFC 2022 M2D.7 公开摘要：
    800G 2×FR4/DR8 SiPh transmitter demo；
    8 个 heterogeneous DFB lasers；0–70°C；最长 2 km
    【本轮 SiPh 侧唯一可锚定证据，仅 demo 级】

L3  instance–platform binding（实例-平台绑定）
    EML ：系列级绑定已建立 = FTCE4527E1PxA-2N ↔ EML TX / PIN RX（S-EML-2）；
         exact-SKU 级绑定未建立
    SiPh：无合格绑定【保持阻断】

L2  platform component（平台组件）
    EML/PIN（系列级声明，S-EML-2）
    Intel SiPh portfolio（平台级组件组合 + 累计出货；不绑定某一 800G SKU）

L1  product instance（产品实例）
    EML ：FTCE4527E1PxA-2N（系列级 preliminary；非 exact SKU）
    SiPh：本轮无合格 exact commercial product；
          Intel 800G 2×400G FR4 OSFP MDDS 仅证明产品身份 + MM 编号（identity，非 binding）
```

**本轮可建立的关系（弱证据，仅记录）**

| 关系 | 证据 | 说明 |
|---|---|---|
| L1(EML family) → L2(EML/PIN) | S-EML-2 | family-level 弱绑定；不升级为 exact-SKU 级 |
| L1(Intel MDDS) → identity 字段 | Intel MDDS | 只作产品身份 + MM 编号记录 |
| L4(OFC M2D.7) → demo evidence 类型 | OFC 2022 摘要 | 按 demo 类型入账 |
| L2(Intel portfolio) → 平台聚合事实 | portfolio 页 | 组件组合/累计出货；不绑定 SKU |
| AGY 候选公司（Jabil/Cisco/Acacia/Marvell/Coherent/Eoptolink/InnoLight/Hyper Photonix/SiFotonics）→ 后续搜索候选 | handoff 附录 | 候选，非事实 |

**必须保持阻断的关系**

| 阻断项 | 原因 |
|---|---|
| L4 demo → L3 binding | demo 不能证明商业产品平台绑定 |
| L2 portfolio → 具体 800G SKU 绑定 | 平台级声明不含 SKU 粒度 |
| SiPh 生成 L1 商业产品实例字段卡 | 本轮无合格 exact commercial product |
| L1 Intel MDDS → L3 binding | 身份 ≠ 光子平台绑定 |
| EML 系列级绑定 → exact SKU 身份 | 不得把系列声明改写成 exact orderable SKU |
| AGY 候选公司 → 负向事实 | 未命中 ≠ 负向 |
| EML 商业产品 vs SiPh demo 的成本/功耗/良率/成熟度直接比较 | 证据等级不对称（见 TQ014-note-controlled-comparison） |

---

## 第三部分：四条细化研究注记去重判断

> 结论：四条均与现有 QID 一一对应，**均不重复**，不创建新 QID（`new_qid_created: false`）。

| 注记 | 归属 | 去重判断 | 触发条件 | 停止条件 |
|---|---|---|---|---|
| `TQ007-note-platform-binding` | 挂现有 **TQ007** | 不重复。与 TQ009-note（记录结构）、TQ014-note（比较许可）正交：本条问“什么证据足以把 exact product instance 与 EML/SiPh 光子平台绑定”的**证明标准** | 出现新的 product–platform binding 证据候选（exact SKU 官方材料声明内部 EML/TOSA、拆解/逆向证据、同一 SKU 的供应链证据）；或需裁决某 exact product 的光子平台归属时 | 形成可执行证据等级判定表并获裁决；或该裁决完成，注记注销 |
| `TQ009-note-evidence-subject` | 挂现有 **TQ009** | 不重复。与 TQ007-note 互补（记录结构 vs 证明标准）；本轮 EML family binding + SiPh demo/portfolio 并存正是其触发场景 | 首次需把 product、platform component、demo、binding 四类 evidence subject 同时写入 Route Profile 时 | Route Profile 证据字段 schema 定型并回写；或裁决明确四类不必分离 |
| `TQ013-note-service-without-customer` | 挂现有 **TQ013** | 不重复。本轮 Q 树中无同题问题 | 首次以公司官方产品/出货证据主张“服务某路线”而无具名客户；或官方出货证据与具名客户证据并存需定优先级时 | 确定证据等级阈值（官方出货何时足够、何时需具名客户）并用于裁决 |
| `TQ014-note-controlled-comparison` | 挂现有 **TQ014** | 不重复。与本轮 TQ014 现有约束“没有受控优势/代价证据不得填 advantages/disadvantages”一致，是对其的操作化细化 | 出现任何 EML 商业产品 vs SiPh transmitter demo 在成本/功耗/良率/成熟度上的直接比较行为或请求 | 取得同证据等级（same evidence-grade）的双侧资料后重新评估；或裁决禁止成立。答案在取得同证据等级资料前保持开放 |

---

## 第四部分：下一轮 AGY 查询建议（≤8 条，exact entity + fingerprint）

> 通用失败要求：每条均允许失败；失败须返回完整搜索轨迹（检索词、引擎/来源、检索日期、命中 URL、判定）。未命中一律不转化为负向事实。

| # | 检索目标（exact entity） | fingerprint | 目标证据类型 | 失败处理 |
|---|---|---|---|---|
| 1 | S-EML-1 原始 PDF 回源（FTCE4527E1PxA-2N preliminary datasheet，Oct. 2023 Rev A1） | PDF 文件名 + "800G-DR8+" + "Preliminary Product Specification" + "FTCE4527E1PxA-2N" + "Rev A1" | 补齐各 observed 字段的页码/页码位置与逐字引文；核对 OSFP "Type 2" 字样、wavelength range 值、module power ceiling 值、CMIS/I2C、regulatory 字段位置 | 允许失败；记录重定向/失效/镜像轨迹 |
| 2 | S-EML-2 产品页回源 | 页面标题 "2x400G DR4+ OSFP Optical Transceiver" + SKU 串 + "EML"/"PIN"/"850 Gb/s"/"0-70°C" | 逐字摘录 EML/PIN、2 km、1310 band、850 Gb/s、0–70°C 的页面位置；确认 2×400G 与 800G 标签共存原文 | 允许失败；记录轨迹 |
| 3 | FTCE4527E1PxA-2N 系列 exact orderable SKU 枚举（ordering information） | "FTCE4527E1P"A"-2N"（通配）+ "ordering"/"Ordering Information"/"part number" | 升级 L1 product instance（exact SKU 级） | 允许失败（可能无公开 ordering 附录）；记录轨迹 |
| 4 | 第三方拆解/逆向报告（Coherent/Finisar 800G DR8 OSFP 模块内部） | "800G DR8 OSFP" + ("teardown" OR "disassembly" OR "TOSA" OR "EML") + (Coherent OR Finisar) | 内部 EML topology / TOSA / lens coupling 物理证据 → TQ007 强绑定证据候选 | 允许失败；未命中不转负向事实 |
| 5 | Intel 800G 2×400G FR4 OSFP MDDS 文档回源 | Intel + "2x400G FR4 OSFP" + "MDDS" + "800G" + MM 编号 | 锚定产品身份 + MM 编号原文；检查是否含光子平台声明 | 允许失败；记录轨迹 |
| 6 | Intel OFC 2022 M2D.7 摘要全文回源 | "M2D.7" + "OFC 2022" + "800G" + "transmitter" + "SiPh" | 锚定 demo 四字段原文（2×FR4/DR8、8×heterogeneous DFB、0–70°C、最长 2 km）；确认无产品化 SKU 声明 | 允许失败；记录轨迹 |
| 7 | Intel SiPh portfolio 官方页回源 + 页内 800G SKU 绑定检查 | 页面 URL + "cumulative shipment"/"shipped" + 页内检索 "800G" | 平台组件组合/累计出货原文位置；验证该页**不**绑定具体 800G SKU（预期无绑定） | 允许失败/允许“无绑定”命中；记录“无绑定”为轨迹而非负向事实 |
| 8 | AGY 九家候选厂商逐家定向检索：Jabil、Cisco、Acacia、Marvell、Coherent、Eoptolink、InnoLight、Hyper Photonix、SiFotonics | "<候选厂商>" + "800G" + ("DR8" OR "DR8+") + ("EML" OR "SiPh" OR "silicon photonics") + "OSFP"；每家独立执行 | 寻找可证实的商业产品 → 光子平台绑定声明（EML 或 SiPh 侧） | 允许失败；每家记录完整搜索轨迹；未命中一律不转化为负向事实 |

---

## 附：输出边界

```text
would_mark_covered: false
canonical_write_performed: false
why_generated: false
company_group_generated: false
new_qid_created: false
```

- 未回答路线优劣；未生成公司服务群；未生成 WHY 边；未修改问题覆盖状态；未落知识库。
- 未生成任何成本/功耗/良率/成熟度或客户采用结论；SiPh 侧本轮不生成商业产品实例字段卡。
