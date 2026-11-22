**verdict: PASS_WITH_CHANGES**

上一轮 7 条 non-blocking 里该改口径的都改了：36 叶、波长拆分、`placement_class=normalized`、TQ014 不再门闩 TQ011、WQ002/TQ014 分账、候选匹配关闭、TQ010/TQ014 验收合同、D01 电架构 UNKNOWN。没有新的阻断项。D05 的 `modulator_or_emitter_type: EML` 仍像半拆，但不构成 blocker。

---

### 八条核对

1. **36 叶 + 波长拆分** — 成立。TQ005 17 + TQ006 7 + TQ007 10 + TQ008 2。D01：`nominal_wavelength=1310 nm`，`wavelength_range=1304.5–1317.5 nm`。
2. **`placement_class` 全 `normalized`** — 成立。meta 写死 TQ008 映射规则；五个种子均为 `front-panel pluggable` / `normalized`，form factor 仍为 `observed`。
3. **D05 不拆 DFB/EAM** — 半成立。`light_source_type` 为 `laser (raw instance phrase: EML laser)`，blocker 禁止推激光器结构/EAM；**未**写 DFB/EAM。但 `modulator_or_emitter_type` 仍是 `EML`/`observed`，和“未拆组合词”不完全同口径。
4. **TQ010 → TQ011 直通；TQ014 并行只补新瓶颈/验证** — 成立（树、铰链、验收合同、有效文本一致）。
5. **WQ002 因果边 / TQ014 比较卡** — 成立，禁止同一主张双记。
6. **`capability_match_candidate` 关闭到 TQ010/TQ011 字段级要求** — 成立；§5.1 与 §6 不再打架。
7. **TQ010/TQ014 draft-only 验收与停止合同** — 成立；停 draft ≠ covered。
8. **D01 `normalized_architecture=UNKNOWN`** — 成立；只保留 raw `retimed`，Tx/Rx 未标范围，未升格。

先前两条语义修正仍在：D01 `53.125 GBd` 只在 `symbol_rate`；D04 `MZM PIC` 只在 `device_integration`。

---

### 剩余（非阻断）

D05 调制器格仍填 `EML`。若坚持未拆，该格应 UNKNOWN 或与光源同句 raw phrase，避免读成“已拆光源/调制器”。不影响下一轮 delta/不可比卡。

五个种子仍无同速率、同边界对照——包内已写明，TQ014 只能出 `not_comparable`，不能出 LRO vs retimed 功耗结论。这是证据边界，不是漏改。

---

### 下一轮

**可以**做 draft-only TQ010/TQ014 实验，边界不变：只用有效 yaml 同实例值；TQ014 优先 `not_comparable`；不改冻结 QID/父节点；公司匹配与覆盖继续关。

---

**不批准** canonical 写入、覆盖变更、正式 Route Profile、公司能力群或确认服务群。五个对象仍是 `draft_only` Route Profile Seed；Coherent 只是实例主体。
