**Verdict：`PASS_WITH_FIXES`**

四轴拆法对上了现有问题树，错层判断大体对，停止条件也守住了。挡下一步的不是“轴想错了”，而是 **controlling text 与证据包纪律仍会把下一轮执行带回错层**。没有发现新 QID 或 canonical 写入。允许展开 **TQ005–TQ008**，但必须带着下面的 P1 进合同，不能直接开 TQ009 / WQ002。

---

## 问题树：这轮到底填了哪一格

`research_questions.yaml` 已经把答案槽位写死了，不是本包发明的：

- `TQ004`：必须分开哪些轴
- 四个子问题就是四轴：`TQ005` 产品/链路标准，`TQ006` 电接口架构，`TQ007` 光子平台，`TQ008` 封装（光学离 ASIC 多远）
- `TQ009` 才是轴值组合而成的可比较画像
- `TQ010` 改组件/接口/工序/设备；`TQ014` 挂在 `TQ009` 下比代价/新瓶颈
- `WQ002` 的 route 端是 `TQ003+TQ009`；`WQ003` 是 `TQ009+TQ010`

因此：**四方向组合作为 TQ004 的答案形状是对的**，而且可执行——下一轮是填四个子问题的取值与定义，不是再开第五条主干，也不是把“光子实现五字段”拆成 TQ007a–e。

树与包之间有两处**必须在 TQ005–TQ008 合同里写死**的语义差，否则 controlling text 不够可执行：

1. YAML 的 `TQ007` 问的是「光子**平台**轴」；有效口径把它扩成 `platform / source / modulator / detector / integration`。这是 **TQ007 内部嵌套字段**，不是新问题。下一轮若按 YAML 字面只枚举 SiPh/InP/GaAs，会把本轮已纠正的 EML 错层打回去。
2. `LPO MSA profile` 被同时塞进 TQ005（接口画像）和 TQ006（电职责）。YAML 里 TQ005 是 PMD/产品标准，TQ006 是信号处理放哪。双挂作为 **alias 拆解**可以；作为两个轴的“典型轴值”会双计。下一轮规则应是：光 PMD/reach → TQ005；host–module 电信号类 → TQ006；具名 MSA 只作 alias，禁止当第三根独立轴。

生长顺序 `TQ004 → TQ005–008 → TQ009 → TQ010 → WQ002/WQ003 → TQ011–013` 与 parent_id 一致。`WQ002` 在没有 TQ009 画像时不可执行——包里把 WHY 往后推是对的。

---

## 七项核心检查

### 1) 四方向组合：同意，作为分析模型，不是行业规范事实

链路/接口、电架构、光子嵌套字段、封装/放置，分别对应 TQ005–TQ008，再在 TQ009 组合成 Route Profile。这消除了“EML / SiPh / LPO / CPO 一张平面表”的特殊情况。包已标明四轴是分析抽象，没有标准文本声明“行业共有四条正交轴”——这一点必须保住。

### 2) EML vs SiPh：确实错层，同意

Lumentum 定义把 EML 钉在 InP DFB+EAM；Intel 材料把 SiPh 钉在 PIC 平台。同级互斥枚举是错的。有效口径要求先写 platform 再写 source/modulator，这才是可执行的 TQ007。

### 3) LPO 拆成 linear + pluggable + MSA profile：分析上不过度，冻结口径过窄

拆复合标签是对的：`DSP vs LPO`、`LPO vs CPO` 在树里不可执行。纯电比较应是 `retimed vs linear`（及 LRO / Tx-retimed 等），放置单列。

**过度之处不在三字段，而在把 alias 冻成 `LPO MSA v1.2 / 100G-DR-LPO`。** 冻结规范只覆盖该 MSA 文本；行业口头的 800G LPO 不能被这一个 profile 吞掉。TQ006 应把 `linear` 当轴值，把具名 MSA 当 profile 实例，不要让 TQ004-a2-d05 变成全称定义。

### 4) pluggable / NPO / CPO 同轴：同意；真正错层是 OSFP/QSFP-DD vs CPO

OIF co-packaging framework 本来就是在比光学相对 ASIC 的位置。裁决把 raw §3「pluggable vs CPO 粒度错层」改掉，这是本轮最重要的合同勘误，**有效口径这边是对的**。

Raw 仍写着旧句。`run.yaml` 规定只消费 `post-adjudication-effective-text.md`，所以这是过程风险，不是内容结论错误。

P1：有效口径把 `on-board/NPO` 写成一个典型值。Intel stand-alone on-board ≠ OIF 近封装 NPO。TQ008 必须分成至少两级：放置大类 `pluggable / near-package(NPO) / CPO / other on-board`，NPO 必须点名定义来源。

### 5) 跨轴实例：没有笛卡尔积外推，但“实例”口径不齐

三组产品/演示观察可以用：

- 固定 1.6T-DR8 + OSFP + SiPh 下 LRO vs module DSP
- 同一 `800G-DR8+` 族上 SiPh+QSFP-DD800 与 EML+OSFP（两轴同时变，包没有假装只变光子）
- Intel SiPh 叙述跨 pluggable / on-board / co-packaged（不等于同一 die）

LPO MSA form-factor agnostic、OIF 电接口候选、OSFP/IEEE「规范不规定内部」是 **许可或沉默证据**，不是观察到的出货组合。包在表格里加了限定，没有写成全称命题。S5 不能外推成“固定 form factor 后 EML vs SiPh 已隔离比较”——他们也没这么写。

### 6) “已有路线差异观察、尚无 Route Profile”：准确，且问题树已经能引出差异

观察 ≠ TQ009。树的设计就是先拆轴再填值再组合。现在说“哪几条路线已在知识库”会假覆盖 TQ009。`answer-to-route-observation-question.md` 这句是对的。

### 7) 无新 QID、无 canonical：同意

`run.yaml` 与有效口径均为 `canonical_write_performed / coverage_status_changed / new_question_ids_created: false`；draft 停在 `TQ004-a2-d01`–`d14`，`would_mark_covered: false`。缺口只挂现有 TQ005–TQ009、TQ014、WQ002/WQ003；功耗排序不挂 PQ010，与 WQ002 的 `physical_question_ids: [PQ010]` 不抢跑。未见落库动作。

---

## P0 / P1 / P2

**P0**
无。不阻止本包作为 TQ004 draft 收口。

**P1（下一轮合同必须写死，否则 TQ005–TQ008 会不可执行或回退）**

1. **唯一消费** `post-adjudication-effective-text.md`。禁止单独用 raw §3「pluggable vs CPO 错层」，禁止用 `sources-tq004.md` 文末「分析纪律」（仍把 EML/SiPh/VCSEL 捆成同一光子轴、把 LPO 当作纯 TQ006 轴值）。
2. **TQ007 只加深字段，不改树、不加 QID**；禁止再输出 EML/SiPh/VCSEL 同级互斥表。
3. **LPO**：电轴值是 `linear`；`100G-DR-LPO v1.2` 只是冻结到的一个 profile 实例。
4. **TQ008**：`on-board` 与 `NPO` 不得写成同一轴值；NPO 必须带 OIF 文件锚。
5. **TQ005 与 TQ006 的接口 profile 边界**（见上）必须有一句话规则，否则 LPO 会在两轴重复计数。

**P2**

- 把规范沉默（S8/S9）称作“跨轴组合实例”，弱于演示实例；下一轮表格应分「已观察组合」和「规范不约束」。
- `direct-drive` / framework 候选进入“典型轴值”可以，TQ006 不得当量产菜单。
- source-discovery 里最强的电×封装交叉（OIF Current Work / CEI-224G-Linear）未进冻结包；不推翻四轴，但 TQ006×TQ008 的交叉证据目前偏 framework。

---

## 我同意的关键点（不复述摘要）

- 比较单位是字段元组，不是热词。
- 错层三件套：EML≠SiPh 同级；LPO≠纯电轴值；OSFP≠CPO 同级，而 pluggable 与 CPO **可以**在 TQ008 广义放置轴上比。
- 「正交」= 分别记账，≠ 笛卡尔积可制造。
- 低 BER 演示不是电架构。CPO 不绑定某种电接口。
- TQ014 / WQ002 / WQ003 在 TQ009 之前没有可执行输入。

---

## 是否允许 TQ005–TQ008

**允许，且应该现在做。** 不允许跳到 TQ009 路线库、不允许 WQ002/WQ003、不允许公司归群（TQ011–TQ013）、不允许路线级功耗/成本排名（TQ014）。

四轴可以分题写，但必须共用本轮字典，并且每轴合同写明：可观察字段、不能回答什么、禁止同级枚举、缺口仍挂现有 QID。这样 controlling text 才从“判断正确”变成“下一轮能执行”。
