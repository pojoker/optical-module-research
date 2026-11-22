**Verdict: `PASS_WITH_FIXES`**

这是可进入下一批的受控小样，不是已闭合知识。独立对照原稿、裁决、`research_questions.yaml`、`knowledge.yaml` 后：生长方向对，分层大体成立，**没有落库、没有新 QID**；但下游若只读 raw，仍会把已被裁决改读的句子当成正文，且 WQ001 有几条桥把不同产品族拼成一条 WHY。

---

## 仓库结构与 draft-only 隔离

**隔离成立。**

- 产物只在 `docs/research/pi-packages/2026-08-23-expansion-v1/`。`run.yaml`：`mode: draft_only`，`canonical_write_allowed: false`，`canonical_write_performed: false`，`coverage_status_changed: false`，`new_question_ids_created: false`。
- `knowledge.yaml` 无 PQ002/TQ002/WQ001；`why_links: []`。仓库里没有独立的 `why_links.yaml`，真正的 WHY 槽就是这个空列表。YAML/CSV 中搜不到 `PQ002-a3` / `WQ001-a2` / `would_mark_covered`。
- `research_questions.yaml` 仍是冻结树：PQ002←PQ001，TQ002←TQ001，WQ001 挂 TQ002/TQ003 × PQ001/PQ002/PQ009。本包没有改这份文件。
- `docs/plans/2026-08-question-queue.md` 是 v1 账本补集（QA–QE → points/knowledge/edges），与这份 PI 研究树不是同一套 ID。本包没有往 `knowledge.yaml` 交 KN 补丁，也没有销 QB。这是正确的停手，不是漏写。

快照声明在 `corpus/web/2026-08-23/`。本审核能看到若干 HTML 与 `PQ001-snapshot-manifest.md`；清单里的 CMIS/OSFP/OIF FD/Coherent datasheet 等 **PDF 未出现在可检索文件列表**。这不构成 canonical 写入，但本会话 **无法核 SHA256**。不要把“未落库”理解成“冻结 PDF 已在本工作区可复核”。

会话开始时的 git dirty（大量 `corpus/qa/**`、`CONTEXT.md` 等）**不在本包内**，本审核不给那些文件背书。

---

## 七项审核

### 一、是否从基础物理问题往下长，而不是随机生成

**大体是。** PQ002 停在功能链（PQ001 之后的下一层），缺口挂到已有 PQ004/PQ005；TQ002 只建六约束输入，明确不提前做 TQ004–TQ014 胜负；WQ001 只做 `need_to_constraint`，不长第三套主干。8+10 条主张和 5 条桥都绑在现有 QID 上。

摘要里“开始呈现生长形态”略满。生长是真的，但 WQ001 仍有跨族拼接（见下），不是已经干净的逐层加细。

### 二、物理 / 路线 / WHY 是否严格分层

**主干分层成立，桥接层有漏。**

- 物理：接口骨架 ≠ 公司口径 ≠ 单料号 ≠ CPO framework。
- 路线：标准摘要 ≠ 历史 objectives ≠ form-factor ≠ 单产品 ≠ framework target。
- WHY：固定四段链，空缺（金额、CPO 实测、ports/RU 等）没有用常识补。

漏点：B2 把 IEEE **可插拔以太网 PMD reach** 和 OIF **CPO mid-board connector 的 optical budget** 写成同一条物理机制；B5 把 **OSFP hot-pluggable 实例** 和 **CPO solder/socket 返工** 并进同一条维护桥。分层在 PQ/TQ 草稿里分清了，到 WQ 又被捏回去。

### 三、PQ002：共同骨架 / 单产品 / CPO；attach vs Media Interface

**通过，附必须绑定的勘误。**

原稿 `PQ002-a3-d01` 仍写“**唯一**核心功能骨架”。裁决改读为“本轮采用的 CMIS **条件化**接口骨架”，这是对的：CMIS 只管 CMIS-managed transmission module 的 Host/Media，不能当全部光模块的共同骨架。`d04/d05` 把 EML/PIN 钉在 FTCE4517E1PxM；`d06/d07` 把 EIC/OIC、pigtail/connector 钉在 CPO framework；表注和 `d07` 明确 **§7.2.1 Table 4 solder/socket = engine-to-substrate，不是 Media Interface**。管理/供电与 mission data path 分开（`d08`）。

`d03` 用两家年报“共同支撑”电→光→电，只要不升格为行业内部结构就可以；目前 boundary 挡住了。

### 四、TQ002：final / objectives / form-factor / 产品 / framework

**通过，附 d08 勘误。**

`d02` 主结论只用 802.3df-2024 摘要的 per-PMD reach；`d09` 把 2022-03-17 objectives（含 10/40 km、copper 1/2 m）隔离为历史注记。功耗三层清楚：OSFP power class + host 读取 + thermal validation（`d03`）、产品 &lt;17 W（`d04`）、CPO expected/target（`d05`）。密度把 lane 配置当 port flexibility，不换算 ports/RU。成本只给 CSD 维度。`d10` 禁止当路线/公司证据。

原稿 `d08` 仍把 `hot-pluggable/hot-unplug` 写成“规范处理的接口事件”。裁决拆开是对的：**能力** vs **功耗瞬态**，都不能证明维护成本下降。“机架内/DC/园区”只作阅读提示，也成立。

### 五、WQ001 五条桥、强度、B5

| 桥 | 双侧证据？ | 强度（以最终裁决为准） |
|---|---|---|
| B1 | 有。IEEE x8 + 单产品 PAM4 × CMIS 方向 + 该料号逐 lane 收发 | 规范结构支持（含实例）。未写成直接证实。同意。 |
| B2 | 形式上有，**机制不是同一族**。route=PMD reach；physical=CPO connector budget | 受限推论。同意不强升；但应拆成两条链，而不是一条“距离→optical budget”。 |
| B3 | 部分同义反复。route 已是 OSFP §15.8；physical 再引用同一节 + `d08` 供电/地 + PQ001 边界 | 规范结构支持可接受；CPO 侧保持目标语言。同意不升格。 |
| B4 | 有，且写明 **同一份 OIF Table 4 双读、非两份独立证据** | 规范结构支持（单源）。同意。engine-to-substrate 层属与 Media Interface 已分开。 |
| B5 | 两侧都有引用，但是 **OSFP 可插拔 + CPO 返工** 的合成 | 裁决改读为 **受限推论**。同意。原稿摘要/表/草案仍写“规范结构支持（事实层）”，**不得再升格**。 |

B5 最终裁决：hot-pluggable / rework / field access **作为属性**有规范或实例；“维护需求映射到这些属性”是跨来源合成；成本未闭合。这是本包最重要的一次降档。摘要表已吸收；**raw 未吸收**。

另外两处裁决勘误也成立：不得把“需求的验证只能落在物理层”泛化到商业/组织/监管；`OIF CPF` 应读作冻结文件 `OIF-Co-Packaging-FD-01.0.pdf`。

### 六、研究注记：只挂已有 QID、未造新号

**未造新号。** 出现的 QID 都在冻结树里：PQ001–PQ009、TQ001–TQ014、WQ001。

挂接有一处不准：PQ002 注记 2 把 mid-board connector 的 **插损数值、返工判定** 挂 `PQ005`（衔接形态）；WQ001 把同一类 **optical-budget 数值** 标给 `PQ009`（接口指标）。按 `research_questions.yaml`，量值缺口应挂 PQ009；形态/是否存在仍可挂 PQ005。TQ002 缺口全部挂 TQ002 是保守且允许的。

### 七、是否写入 canonical

**没有。** 见隔离节。裁决写“不授权写入 `why_links.yaml`”与仓库实际槽位用词不一致（实际是 `knowledge.yaml` 的 `why_links`），不影响“没写进去”这一事实。

---

## P0 / P1 / P2

### P0

无。没有落库、没有新问题号、没有把 EML/PIN/CPO attach 写成共同必备、没有把 objectives 写成 final、没有从约束跳到路线或公司。

### P1

1. **裁决未回写 raw，下游会读错。** 文件：`raw-output-pq002-attempt3.md` §4 `PQ002-a3-d01`；`raw-output-tq002-attempt3.md` §1/§2/§4 `d08`；`raw-output-wq001-attempt2.md` §1 表、§2 表、§3 B5。与 PQ001 第一轮同类：只改裁决段不够。下一批前必须规定 **controlling text = 裁决后口径**，或把勘误写进 raw 的 statement/strength。
2. **B2 跨族拼接。** `raw-output-wq001-attempt2.md` §3 B2。IEEE 802.3df reach 与 OIF CPO connector budget 不是同一条物理链。保持受限推论不够，应拆链或把 CPO 段标成仅 CPO 场景。
3. **B5 强度：摘要已降、raw 未降。** `adjudication-wq001-final.md` vs `raw-output-wq001-attempt2.md`。禁止再升回“规范结构支持”。
4. **同一证据缺口挂两个父问题。** PQ002 注记 2 → PQ005；WQ001 B2 → PQ009。插损/budget **量值**应对齐 PQ009。
5. **快照 PDF 在本工作区不可检索。** `snapshot-manifest.md`、`sources-pq002.md`。隔离仍成立；独立核 SHA 未完成。下一批前应能对冻结 PDF 做路径+哈希复核。

### P2

- `expansion-summary.md` 把生长说得比 WQ 原稿更干净；审阅以 raw+裁决为准。
- B3 physical 侧大量复用 route 侧 OSFP §15.8，接近 B4 那种单源双读，未同等披露。
- B5 一条桥里并陈两种维护体制，即使强度已降，后读仍易当成“可插拔模块的通用维护物理”。
- `d03`“两家年报共同支撑”易被读成行业口径；现有 boundary 够用，不必再升。
- 裁决文件名 `why_links.yaml` vs 实际 `knowledge.yaml#why_links`。

---

## 同意的关键点

- 不再用一只 800G DR8 OSFP 的 EML/PIN 冒充全部光模块结构。
- engine-to-substrate attach ≠ Media Interface。
- 802.3df-2024 摘要与 2022 objectives 分开。
- power class ≠ 产品功耗 ≠ CPO 节能目标。
- hot-pluggable ≠ hot-plug 瞬态 ≠ 维护成本下降。
- WQ 不是第三套知识树；五条都是候选，全部 `would_mark_covered: false`。
- B1 不作直接证实；B4 单源双读已披露；B5 降为受限推论。
- 成本金额、CPO 实测、ports/RU、optical-budget 数值保持空缺。
- 本轮即使外部审阅通过，也 **不自动 promotion**。

---

## 是否进入下一批；前置条件

**可以进入下一批扩展，条件如下。不满足则停在本包修补，不要扩题。**

1. 把 P1 勘误做成 **唯一可读口径**（改 raw 或强制“摘要+裁决覆盖 raw”），尤其 B5 强度和 CMIS“唯一骨架”。
2. 拆开或重标 B2（以及必要时 B5）的跨族拼接；禁止用一条 WHY 同时服务可插拔 OSFP 与 CPO engine。
3. 注记挂接：量值→PQ009，形态→PQ005。
4. 冻结 PDF 可核路径与 SHA256。
5. 下一批只加深 **已有子问题**（优先 PQ004 器件级缺口、PQ009 指标、或 TQ002 定量空缺/TQ003 瓶颈），**禁止新 QID、禁止写 knowledge/why_links、禁止改覆盖状态**。
6. Kimi 若在结构/证据边界上否决，以否决为准，不因本 Cursor 结论强行扩批。

【品味】主干分层是好品味；WQ 把已经分开的实例捏回一条因果，是特殊情况补丁。把特殊情况拆开，比再加一条“强度脚注”干净。
