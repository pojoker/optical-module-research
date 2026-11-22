# Q-UP-05：NPO/CPO 边界总裁决

日期：2026-08-31  
状态：`draft-only / pending external review`  
canonical 写入：`0`

## 1. 最短答案

NPO 与 CPO 不是两份固定 BOM，也不是“离 ASIC 多少毫米”的两个档位。当前公开资料支持把它们理解为 placement/substrate 关系，再把 attach、电接口、光源、光纤、散热和维修单元逐轴填写：

- OIF 的 CPO 定义锚是 communications device 与 host ASIC 位于同一 `first-level substrate`；
- OIF Figure 2d 的 NPO 只是一个 socketed reference instance：packaged ASIC 与 engine 经 socket 接到 common substrate；
- 同为 NPO，Lightmatter Passage L20 的公开产品形态却是 PCB/mezzanine 上的 1827-ball BGA、reflow-compatible module；
- 同为 CPO，OIF 3.2T IA 规定 LGA/socket，NVIDIA 官方又披露 socket-based 与 solder-reflow 的不同 exact CPO 实现；
- 因而 `placement ≠ attach ≠ electrical architecture ≠ photonic platform ≠ serviceability`。

真正的因果链是：高速 electrical channel 的 loss/impairment 约束收紧，使光引擎向 ASIC 附近或 first-level substrate 迁移；这可能缩短电路径，同时把原来由独立前面板模块吸收的 attach、thermal、fiber、laser、management 与 replacement 责任迁入板级/封装级/系统级设计。是否因此改善功耗、可靠性、成本或维护性，必须另做同边界实验，不能由 NPO/CPO 标签直接推出。

## 2. 三路研究的采纳与驳回

### 2.1 OIF 定义与电接口轨：采纳

采纳以下主张：

1. CPO 的冻结定义是 same-first-level-substrate，不是统一毫米值。
2. Figure 2d 是 socketed NPO reference instance，不是全行业必要充分定义。
3. `common substrate` 也不能单独区分 NPO/CPO；必须记录 host package state、substrate level 与 attach path。
4. CEI-112G-XSR 与 XSR+ 是不同的完整电合规对象：XSR 的 0–50 mm 与 8/10 dB categories、XSR+ 的 13 dB + COM/ERL/T/R boundary 不能抽成一个 NPO/CPO 距离阈值。
5. 12.8T/6.4T NPO Module 截至 2026-08-31 仍是 OIF active IA-development project；3.2T CPO Module 已有 final IA。
6. `CEI-CPO` 不是本轮可核验的 OIF exact project/IA 名称；使用时必须回填具体 CEI clause。

### 2.2 物理、光学与热轨：大部分采纳

采纳以下主张：

1. solder、socket、LGA 是实现轴，不是 NPO/CPO 的定义轴。
2. pigtail、engine connector、mid-board connector、front-panel data connector 与 external-laser connector 是不同光学/维修边界。
3. OIF 3.2T IA 的 heat spreader、TIM、Tcase 与 module power 是该 IA 的热合同，不能外推为所有 NPO/CPO 的通用常数。
4. ASIC↔OE 热耦合需以 power、junction/case temperature、transfer coefficient 与 cooling overhead 测量，不能由“更近”推导可靠性或系统功耗。
5. NVIDIA 官方披露的 socket-based 与 solder-reflow CPO 对象构成 attach 正交性的产品级反例。

保留限制：该轨中的厂商产品页和厂商 demo 只能证明公开实现/演示，不直接证明量产良率、长期可靠性或部署。

### 2.3 可服务性与产品/部署轨：部分采纳、两项纠偏

采纳：

1. `hot-pluggable`、powered replacement 与 traffic-hitless 必须分开。
2. serviceability 必须拆成 optical engine、ELS/laser、external cable、internal fiber/harness、cooling assembly、substrate/package 与 whole system，并记录 operator/vendor/depot/factory 服务权限。
3. BCM78909/Bailly、Q3450-LD、SN6800/SN6810 等 CPO exact objects 可用于证明不同 attach、laser 与 fiber boundary；不得相互继承未披露字段。
4. Broadcom/Tencent 对 BCM56999/Humboldt 提供了官方具名 `field deployment` 声明，但没有公开 fleet size、上线日期、运行时长和运维统计；只保留为 `official_named_deployment_claim`，不写成已独立验证的规模化长期运行。

驳回/纠偏：

1. **驳回“NPO exact object = public_evidence_insufficient”。** Lightmatter 官方 Passage L20 产品页明确把对象称为 NPO/OBO solution，并给出 NPO placement、6.4 Tb/s each direction、212.5 Gb/s PAM4、37.5×26.4 mm、1827-ball BGA、reflow compatible 与 cold-plate cooling。它已通过本轮所需的 exact product-listing 身份门；仍不能推出 qualification、deployment、field replacement 或完整 channel contract。
2. **驳回“Q3450-LD 已公开多个非 ES 子 SKU”的无定位说法。** 截至 2026-08-31 当前公开 NVIDIA 手册订购表只列 `920-9B36M-00MX-8ES`，Lifecycle Phase 为 `Prototype`。手册同时已有详细规格、ELS 服务流程和软件入口，这形成“详细 exact manual + Prototype ordering row”的成熟度组合；不能因手册完整而升级 deployment，也不能把整个未来型号永远锁死为 ES。

## 3. 当前可接受的原子结论

### 3.1 稳定解释候选

1. NPO/CPO placement 标签不能自动填充 attach、电处理、光子平台、光源或维修字段。
2. electrical reach 必须以 interface + T/R/reference plane + channel elements + loss/COM/ERL/BER 表达，不能只写距离。
3. socket 证明可分离/返工机制，不自动证明 field replaceable 或 hot-swap。
4. serviceability 必须绑定 replacement unit、service actor、location、power state、downtime 与 post-replacement test。
5. framework、active project、final IA、product listing、demo、qualification 与 deployment 不能靠叙述合并。

### 3.2 对象级候选

1. OIF Figure 2d：socketed NPO reference instance；只限 framework 对象。
2. Lightmatter Passage L20：BGA/reflow NPO product listing；qualification/deployment unknown。
3. OIF 3.2T CPO IA：LGA/socket、CEI-112G-XSR、pigtail 与 heat-spreader/Tcase 合同；不等于商业产品部署。
4. NVIDIA Q3450-LD：当前公开订购表 exact SKU 为 Prototype；ELS 有 authorized-service powered replacement，optical subassembly field FRU 未公开。
5. Broadcom/Tencent Humboldt：有官方具名 field-deployment claim；规模、运行时长和现场运维结果 unknown。

### 3.3 仍是机制候选或 unknown

- shorter electrical path 对 system power、latency、reliability 与 TCO 的净效应；
- socket 相对 solder/BGA 的量产良率、返工成本和信号/热惩罚；
- external laser 的服务性/热隔离收益是否覆盖耦合损耗、额外 source power 与 fiber complexity；
- NPO/CPO 同边界 field failure rate、MTTR、MTBF 与 TCO；
- 12.8T/6.4T NPO final mechanical/electrical/thermal/management/service contract。

## 4. 为什么这比“NPO 优于 CPO”更有用

```text
上游：lane rate、ASIC I/O escape、channel loss/BER、前面板密度、热流密度
→ placement：front panel → board/near-package → same first-level substrate
→ 责任迁移：attach、channel compliance、fiber/laser boundary、cooling、repair 进入系统
→ 可观察量：loss/COM/BER、attach/rework、Tcase/Tj/cooling power、FRU/MTTR
→ 优势/代价：只能在同速率、reach、FEC、温度、服务单元与测量边界下比较
→ 下游：哪一种 exact stack 在什么故障/成本/温度分布下更优？
```

这条链同时服务两套知识体系：物理体系记录 stack、attach、fiber、laser 和 thermal；技术路线体系记录 placement、electrical architecture、光子平台与成熟度；`WHY` 边只在共同分母和可观察结果存在时连接两者。

## 5. 文件分工

- `oif-definition-electrical-primary.md`：OIF 定义、电接口、测试参考面与成熟度；
- `physical-optical-thermal-primary.md`：attach、光学可拆点、thermal ownership 与实验合同；
- `serviceability-products-deployment-primary.md`：产品、FRU、服务权限与成熟度原始研究；其中 NPO exact-object 与 Q3450 SKU 两点以上述裁决为准；
- `exact-object-and-counterexample-table.md`：面向读者的对象/反例摘要；
- `responsibility-and-observable-matrix.md`：责任迁移与共同分母；
- `candidate-claims.yaml`：8 条主代理裁决后的候选主张；
- `expert-questions-candidate.yaml`：9 条可证伪后续问题。

正式知识库写入：`0`。
