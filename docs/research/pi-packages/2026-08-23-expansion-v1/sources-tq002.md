# TQ002 冻结来源包

`admissible_for_draft: true` 仅允许进入草案，不表示 promotion。

## T1：IEEE 802.3df-2024 状态与摘要

- 标准页快照：`corpus/web/2026-08-23/standards.ieee.org__802.3df-2024.html`
- IEEE SA 解读快照：`corpus/web/2026-08-23/standards.ieee.org__ethernet_800g_article.html`
- Task Force 页快照：`corpus/web/2026-08-23/ieee802.org__802.3df_taskforce.html`
- 802.3df-2024 已于 2024-02-16 获批，覆盖 400 Gb/s 与 800 Gb/s MAC/PHY/management 参数。
- IEEE SA 摘要表：800 Gb/s 的 x8 结构覆盖 AUI、backplane、copper、MMF 50/100 m、
  SMF 500 m/2 km；同一八 lane port 可配置为 1×8、2×4、4×2 或 8×1 的实现。
- 可支持：带宽不是单一“800G”标签，还需介质、reach、lane 结构；端口 lane 结构与配置密度有关。
- 不可支持：任一具体光模块内部路线、制造成本排序、x8 永远优于 x4。

## T2：IEEE P802.3df 项目目标（2022-03-17）

- 存档：`corpus/web/2026-08-23/ieee802.org__P802.3df_objectives_2022-03-17.pdf`
- SHA256：`b9c38e82a985ec5e73c26702a49afb1859f0c8775dc25f5bafd9be9422292a4b`
- 印刷页 3：800 Gb/s 目标分别包括 copper 1/2 m、MMF 50/100 m、SMF 500 m/2 km，
  以及 10/40 km 单纤方向等不同介质/reach/lane 组合。
- 边界：这是项目目标历史文件；最终标准状态由 T1 核验。只用来展示“场景输入是多维组合”。
- 不可支持：所有目标均由同一物理实现完成，或 reach 可直接推导成本和路线胜负。

## T3：IEEE P802.3df Criteria for Standards Development

- 存档：`corpus/web/2026-08-23/mentor.ieee.org__P802.3df_CSD.pdf`
- SHA256：`19a49fe2998c2c0f6221279444cabc08d34d079848c351c1c39ded375d469c25`
- 印刷页 8 Economic Feasibility：成本分析考虑 known/balanced cost factors、installation cost、
  operational cost（含 energy consumption）；维护成本通过保留 network architecture、management、
  software 来降低；项目会比较 PMD complexity、power、latency、implementation constraints。
- 可支持：成本和维护是场景约束，且至少包含安装、运营能耗、架构/管理延续性等维度。
- 不可支持：任何模块价格、维护费用数值或路线成本排序；该文件是项目经济可行性论证。

## T4：OSFP Module Specification Rev 5.22

- 存档：`corpus/web/2026-08-23/osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`
- SHA256：`c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- 印刷页 17 §1：规范定义 module form factor、host cages/mating connector、电/机械/热边界。
- 印刷页 168–170 §15.8：OSFP 有 power classes、低/高功耗模式，host 可在启用高功耗前读取
  module power class；最大额定功耗的使用需要系统级 thermal design/validation；功耗瞬态包括
  hot-plug/hot-unplug。
- 可支持：form factor 功耗等级是系统热设计约束，hot-plug 是规范处理的事件。
- 不可支持：power class 等于任一产品实际功耗；hot-plug 自动等于低维护成本。

## T5：Coherent FTCE4517E1PxM 产品规格

- 存档：`corpus/web/2026-08-23/coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf`
- PDF p.1：hot-pluggable OSFP、850 Gb/s aggregate、power dissipation <17 W、500 m SMF、
  8×100G PAM4 retimed electrical interface、MPO-16。
- 可支持：一只真实产品同时接受带宽、reach、功耗、form factor/维护接口约束。
- 不可支持：代表全部 800G，或 `<17 W` 是 OSFP/DR8 行业通值。

## T6：OIF Co-Packaging Framework 01.0

- 存档：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-FD-01.0.pdf`
- SHA256：`1d614845b92471ae50dd1c6d80a4070515bd4ef369ded9d42fe5e3df4c8457af`
- 印刷页 9 §5：CPO 把 engine 靠近 host ASIC，以降低高速电通道损耗/不连续，目标是高带宽与显著
  power savings；这是 framework 的 expected/target language，不是所有产品实测结果。
- 印刷页 17 §7.2.1/Table 4：engine 尺寸受总带宽、布线密度、光纤接口和热管理决定；removable
  socket 的 retention mechanism 会占 substrate 面积并限制密度；solder reflow footprint 密度高但
  rework 受限且有 yield loss，socket 可 rework 但现场 access 受限。
- 印刷页 26–27 §7.8：CPO 需单独考虑 reliability、redundancy、repairability。
- 可支持：在该 CPO framework 中，功耗、密度、可返工/可维护之间存在实现层权衡。
- 不可支持：所有 CPO 不可维护、CPO 一定比 pluggable 低功耗，或 Table 4 是市场成本数据。

## T7：OIF 3.2T Co-Packaged Module IA

- 存档：`corpus/web/2026-08-23/oiforum.com__OIF-Co-Packaging-3.2T-Module-01.0.pdf`
- SHA256：`586d0ed09f2e19d49bf92b23bb681c266d63db6c477d9c8e8c6cd6cf1d6a304f`
- 印刷页 7：3.2T module 是 51.2T switch assembly 的 building block，16 个 module 近 ASIC；
  optical module 将 short-reach electrical 转 optical I/O。
- 印刷页 24：module 可在 substrate 周边或 embedded，光侧 pigtail，最终 connector 未固定。
- 可支持：高 aggregate bandwidth 与 placement/density/维护边界的一个规范实例。
- 不可支持：所有 CPO 采用相同机械实现或服务方式。

## 六约束证据规则

- 带宽/距离：可用 T1/T2 的规范维度和 T5 产品实例。
- 功耗：可用 T4 form-factor constraint、T5 产品值、T6 framework 目标，三者不得混写。
- 密度：可用 T1 lane/port 配置与 T6 substrate footprint 权衡，不能直接转成 ports/RU 数值。
- 成本：只写 T3 的经济可行性维度和 T6 的工程 tradeoff，不生成产品价格或路线成本排名。
- 维护：只写 T4/T5 hot-plug 事实与 T6 rework/access 权衡，不推出全生命周期成本高低。
- 本题不做具体路线选择、公司归群或市场份额判断。
