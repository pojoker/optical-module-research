# 数据语义修复关灯工场外包方案

> 固定基线：`optical-module-research@7ff3b25cfd0ff3b13fa834a0d775ae2879195`
>
> 输入：Kimi 领域语义审计、Cursor 数据契约审计及 Codex 交叉裁决
>
> 原则：只修读者边界与派生层，不改 canonical，不实施 schema 重构或消融

## 一、共同问题定义

三方审计共同确认，当前产品的主要风险不是“数据完全不可用”，而是结构通过机器门后仍可能诱导更强的读者结论：过程型判定串被显示为证据等级、粗粒度 cell overlap 被理解成产品能力、海外资料槽位被理解成结论覆盖、第一方 reviewed event 被理解成独立证实，以及不同单位和业务范围的出货量被放在同一比较表面。

本轮选择先修读者可见边界和确定性的派生错误。C5 拆分、海外双主张 schema 合并、legacy 表删除及 canonical 纠错继续保留为用户裁决项。

## 二、四个独立开发包

### WP-A — CodeBuddy / Hy4：能力证据语义

**目标**：修复能力明细生成器把过程型 `判定等级` 冒充“证据等级”的问题，并阻止 cell overlap 被文案升级为产品或路线能力。

**写入**：

- `build_detailed_capability_report.py`
- `tests/test_capability_report_semantics.py`

**验收**：

- 带括号的判定串不会因精确枚举 miss 而落入错误默认 rank。
- 输出字段和标签准确表达“准入/判定依据”，不声称是 A–D 证据等级。
- C5/M1/MOD1 等粗粒度节点带有不可推出产品供货或完整路线能力的固定边界。
- 不修改 `points.csv` 或 `capability_details.csv`。

### WP-B — OpenCode / Omen Alpha：海外覆盖与事件证实层级

**目标**：让海外 reader 明确区分 slot、available source、claim、reviewed claim、event，以及 asserted/corroborated。

**写入**：

- `calls/renderer.py`
- `calls/README.md`
- `calls/tests/test_reader_semantics.py`

**验收**：

- 不再单独用“39家公司、166来源”表达研究结论覆盖。
- 五级覆盖的分母和公司数可复算。
- `reviewed` 固定解释为原文已核；`corroborated` 才表示独立来源交叉。
- 同源双证不能升级为 corroborated。
- 不修改任何 `calls/*.csv`。

### WP-C — Pi / GLM-5.3-Flash：出货、锚点与关系边安全渲染

**目标**：在现有 `render.py` 输出中阻止跨单位出货量比较、非 URL 假链接和关系边产品范围越级。

**写入**：

- `render.py`
- `tests/test_render_data_quality_boundaries.py`

**验收**：

- 出货量按单位/业务范围展示，明确禁止全表求和、排名或份额推导。
- 非 HTTP 锚点渲染为说明文本，不生成不可用超链接；“同上”不伪装成独立锚。
- `edges.csv` 被表述为关系观察，不默认写成光模块供货关系。
- 不新增 relation type、product scope schema，也不修改 CSV。

### WP-D — AGY / Gemini-3.8-Flash：九页产品透明度

**目标**：把审计后的“能回答/不能回答/证据层级”放进九页前端的既有审计和状态章节。

**写入**：

- `site/optical-module/sections/audit.html`
- `site/optical-module/sections/status.html`
- `tests/site/test_optical_module_reader.py`

**验收**：

- 页面明确列出事实、派生、候选和 UNKNOWN 的读法。
- 页面明确说明 capability overlap、source slot、reviewed event、shipment observation 分别不能推出什么。
- 不新增第十页，不恢复状态机，不把审计假设写成 canonical 事实。
- 现有九页/27章节合同保持。

## 三、集成与复核

四路各自在独立 worktree 提交。Codex 只读取最终 diff、测试结果和未解决项，逐分支审核后选择性 cherry-pick 到集成分支；不自动推送。

集成完成后，Codex 输出：

1. `docs/reviews/2026-09-04-post-remediation-codex-review.md`：代码、规范、领域边界和测试审核。
2. `docs/reviews/2026-09-04-product-direction-after-remediation.md`：当前产品能回答什么、仍不能回答什么、下一阶段应深化内容还是调整架构。

随后两路独立复核：

- Kimi K3：重点审查领域语义、证据边界、产品方向是否被代码便利性带偏。
- Cursor Fable 5.1：重点审查实现正确性、依赖影响、回归风险和报告是否与 diff 一致。

两位复核者完成前不得读取对方报告。任何进一步 canonical 修复、schema 变更、消融、合并 main 或推送均需用户新授权。
