**verdict: PASS_WITH_CHANGES**

本包把两套知识体系、实例级种子和取舍铰链说清楚了，也没有把种子升格成正式路线画像。它还不能当下一轮的完整比较样本：五个种子缺少同速率、同边界的对照基线；`placement_class` 仍由封装外形做分类映射。

---

### blockers

无。不阻断把本包当作 **draft-only** 的上游输入。不得据此改覆盖、写 canonical、发正式 `RP###`、建公司群。

---

### non-blocking corrections

1. **`placement_class: front-panel pluggable` 不是实例直接观测。** 五个种子都由 OSFP / QSFP-DD800 套 TQ008 分类词，状态却标成 `observed`。包内已声明这是受控分类，不是内部封装推断；下一轮应单独标成分类映射，避免和 datasheet 实测混为一谈。除此以外，未见用 DR8 补 lane/FEC/reach、用 DSP 写成 full-retimed、用 EML 补 InP/DFB+EAM、用 SiPh 补器件、用相邻演示或对端互操作补字段。
2. **这五个种子撑不起「同速率 LRO vs retimed」取舍卡。** D01 是 800G、仅有 raw `retimed`；D02 是 1.6T LRO；D03 电架构仍是 UNKNOWN。TQ014 实验只能练卡片与 UNKNOWN，不能拿 D01/D02 当对照事实。
3. **D01 的 `wavelength: 1310 nm` 压缩了来源里的 `1304.5–1317.5 nm` 区间。** 原子化之后，名义中心波长和 lane 窗口应分开，或把窗口留在 UNKNOWN/raw。
4. **D05 把同一句 “EML lasers” 同时写入 `light_source_type` 和 `modulator_or_emitter_type`。** 没有补 DFB+EAM，这是对的；但两格同值容易被当成已拆开的光源/调制器。应用 raw 标签说明这是未拆的器件组合词。
5. **执行顺序不要写成 TQ014 卡死后才允许 TQ011。** 冻结树里 TQ011 的父节点仍是 TQ010。物理变化 → 能力要求可以与取舍卡并行起草；否则公司侧会假门闩。
6. **缺问题验收合同。** 冻结树把「一条 KN」当验收，CONTEXT 里的验收合同要求覆盖条件与停止条件。TQ009/TQ010/TQ014 下一轮草稿应写明：多少叶字段、何种基线、何种证据状态才算该问可停，而不是有种子就算覆盖。
7. **`company-placement-pilot.md` 第 6 节**写「TQ013 之前路线侧只能标候选能力匹配」，第 5.1 节又写 TQ010/TQ011 完成前连候选都阻断。应以 5.1 为准：现在连 `capability_match_candidate` 也关闭。

两处语义修正成立，应保留：D01 的 `53.125 GBd` 只进 `symbol_rate`，`media_lane_rate` 为 UNKNOWN；D04 的 `MZM PIC` 只进 `device_integration`，`pic_eic_integration` 为 UNKNOWN。

---

### 取舍铰链

上游：TQ002 场景约束、TQ003 瓶颈、TQ009 画像、TQ010 物理变化。
中间：TQ014 记录有条件的优势、代价、新瓶颈、替代；Why Link 管因果，不是第三套知识。
下游：优势 → 适用场景/采用假设；代价 → 新瓶颈/验证/替代；物理变化与新瓶颈 → TQ011 → TQ012/TQ013。
反馈：新瓶颈 → TQ003 → 下一轮画像。

这与 CONTEXT 里的条件化取舍铰链一致。本轮只建 schema、不填优劣，也正确：五个种子没有共同基线，公司「降功耗」类表述也没有同条件对照。隐藏环是：用不完整种子编造取舍，再把「新瓶颈」写回 TQ003。下一轮卡片必须带 `evidence_status` 和 UNKNOWN，禁止无基线排名。

冻结 QID/父节点不必改：TQ014 父节点仍是 TQ009；研究顺序可以是 TQ009 →（TQ010 与 TQ014 并行）→ TQ011。不要为铰链新建 QID。冻结 WQ 没有单独对应 TQ014，取舍应进 Why 的条件/取舍/替代字段，或挂在 TQ014 的研究注记下。

---

### 35 字段原子 schema

够用，作为种子验证层，不是过度本体。第一轮 7 个复合格把已知和 UNKNOWN 绑在同一状态上，拆开是对的。TQ005 16 + TQ006 7 + TQ007 10 + TQ008 2 = 35。完整度约 17%–49%，说明「四轴名词」组不成正式画像。

不是缺本质字段，是缺**同实例证据**。取舍所需的 BER/温度/测试口径属于 TQ014 卡，不应塞进种子。`platform`/`material` 与三档 integration 在多数种子上全是 UNKNOWN，略偏细，但这是复合格的代价，可接受。

---

### 是否可做下一轮 draft-only TQ010/TQ014 实验

**可以，仅限草稿，且必须带边界：**

- TQ010：优先 D01（字段最全）做「相对参考样机改了什么」；D04/D05 只能做互操作两端的组件对比，不是其余条件相同。
- TQ014：只跑卡片、证据分级和 UNKNOWN；不要输出 LRO 相对 retimed 的功耗结论。
- 公司匹配、路线服务群、覆盖状态全部继续关闭。
- 不改冻结 QID/父节点。

---

### 明确声明

**不批准任何 canonical 写入、覆盖变更、正式 Route Profile，或公司能力群/确认服务群。** 五个对象仍是 `draft_only` 的 Route Profile Seed；Coherent 只是实例主体，不是已确认路线服务结论。
