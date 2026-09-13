# 审核结论：PASS_WITH_FIXES

包内流水线（AGY 发现 → 裁决 → `source-excerpts` / `pi-handoff` → Pi → `pi-adjudication`）在有效消费口径下守住了证据边界；剩余问题是消费纪律与分层命名，不是把合成事实写进下游。

---

## 六问

### 1. AGY search ≠ 证据；generated synthesis 不晋升
**守住。**

- `run.yaml` 全关写入/晋升；注明 fluent AGY answer 不是证据。
- `pilot-v1-audit.md` 明确拒收首轮合成（错误料号、假 GA、TDECQ→TEC、跨实例拼 SiPh）。
- `adjudication.md`：Pi 只消费 `pi-handoff.md`，禁直接消费 AGY raw。
- Pi 声明只读 handoff；SiPh 不生成对称商业字段卡。

有效下游必须以 `source-excerpts.md` + `adjudication.md` + `pi-adjudication.md` 为准，**不得**回读 `agy-*-output.md` 的解释性段落。

### 2. EML：系列 / exact SKU / GA / TEC / FEC / 内部实现
**边界正确。**

| 项 | 口径 |
|---|---|
| 主体粒度 | `FTCE4527E1PxA-2N` = 产品系列；exact orderable SKU = UNKNOWN |
| EML/PIN | 仅系列层（S-EML-2）；不推 die/array/topology |
| GA/量产 | Preliminary → UNKNOWN |
| TEC | TDECQ/TECQ ≠ cooler → UNKNOWN |
| FEC | “with FEC”/BER 可记；code/终止位置 UNKNOWN |
| heatsink | `A: Closed Heatsink` vs `-2N: No Heat Sink` → `UNKNOWN_CONFLICTING_LABELS`，不自解 |
| 内部 | TOSA/ROSA/driver/TIA/lens 一律 UNKNOWN |

Pi 因 handoff 缺页码把功率/波长等写成“值 UNKNOWN”，**应用 `source-excerpts.md` 回补**（`pi-adjudication` 已点名）。

### 3. SiPh `FAIL_NO_SINGLE_INSTANCE`
**限制正确：本轮检索失败，非产业负向事实。**

`adjudication.md` 明确否定：市场无 800G SiPh、候选厂无产品、厂商必用/不用某平台、公开网无更强证据。候选表 = discovery log，≠ absence evidence。Pi / handoff 未做对称商业卡，也未把未命中写成负向。

### 4. Evidence subject 四层 vs 现有 Route Profile
**兼容为 TQ009 证据纪律细化，不是新轴；有轻微命名混淆。**

- 现有 RP Seed：`product_or_demo`、`evidence_type`、字段级 `observation_state`，且禁止平台/演示补实例。
- 四层（product / platform component / binding / demo）是**防继承规则的显式化**，挂 TQ009 合理；**不是** TQ005–TQ008 轴字典，也不应升成正式 RP 轴。
- Pi 把 S-EML-2 的系列级 EML/PIN 同时标成 L2 与 L3：产品页系列声明更接近 **L1 字段值（系列粒度）+ 弱绑定**，不宜当成独立 “platform component 器件实体”。属命名/分层清晰度问题，非合同冲突。

### 5. “1 新 + 3 合并”
**正确。**

| 注记 | 裁决 | 理由 |
|---|---|---|
| `TQ007-note-platform-binding` | 并入 TQ009 | TQ007 = 轴值字典；绑定标准 = 实例画像证据问题 |
| `TQ009-note-evidence-subject` | **唯一新增** | 四类 evidence subject 是否分账，现有 schema 未定型 |
| `TQ013-note-service-without-customer` | 合并既有 TQ013 | 合同已要求精确实例直接证据，禁供货/客户边自动升级 |
| `TQ014-note-controlled-comparison` | 合并既有 TQ014 | 合同已禁非同条件/无受控证据的优劣结论 |

Pi 原“四条均不重复”驳回正确；`new_qid_created: false` 正确。

### 6. 下一步 2–3 家 AGY exact-entity chase（draft-only）
**允许，附硬约束。**

- 一家一任务（禁 Pi 第 8 条九厂捆绑）
- 失败须完整检索轨迹；无轨迹不得当 absence / 负向事实
- 继续 `draft_only`；不写 canonical / coverage / WHY / 公司群 / 正式 RP

---

## 分级

### P0（消费闸；打开则整包失效）
- 无已打开的结构性 P0。
- **硬闸（必须保持）**：禁止消费 AGY raw 合成；禁止把 `FAIL_NO_SINGLE_INSTANCE` / 候选 FAIL 行写成产业或公司负向事实；禁止本包产出晋升 canonical / coverage / WHY / 公司群 / 正式 RP。

### P1（修后再当有效口径）
1. 长期锚点以 `source-excerpts.md` 为准，覆盖 Pi 字段卡里“页码/引文 UNKNOWN”及可回补的功率、波长等。
2. 注记口径固定为 **1 新（`TQ009-note-evidence-subject`）+ 3 合并**；勿沿用 Pi“四条均不重复”。
3. 澄清四层：系列级 EML/PIN ≠ 独立 platform-component 实体；binding 层主要服务“产品页静默、需跨源绑定”的情形（尤其 SiPh）。
4. 下轮查询：2–3 家、exact entity + fingerprint、可失败+轨迹。

### P2
- heatsink / `OSFP RHS` 标签冲突继续 UNKNOWN，勿工程化解释。
- AGY SiPh 分析里的绝对措辞（如 “never released”）仅作 search narrative，不得外溢。
- 证明标准（何为足够 binding）可作为 `TQ009-note-evidence-subject` 子条，不必恢复独立 TQ007 注记。

---

## 不批准

canonical 写入、覆盖状态变更、WHY、公司群、正式 Route Profile promotion。本包产出止于 draft-only 字段纪律与检索方法验证。
