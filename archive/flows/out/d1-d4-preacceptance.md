# D1–D4 预验收报告（v1.7a 第1段治理还债四路交付）

**验收人**：预验收员（本稿只查错，不裁决，终验归主会话）
**验收日期**：2026-07-24
**方法**：对照 `flows/ROADMAP-v1.7a.md` 第1段逐项文本要求，逐条读码/读表 + 实跑脚本 +
抽样回源核实；不修改任何交付物。

---

## D1｜entity-registry 两层契约 + validate_edges.py 扩展

**结论：通过**

1. **字段齐全性**（`flows/entity-registry.yaml`，407行）：
   - 身份层（`identity_layer.entities`）：15 个实体条目，逐条含
     `entity_id / identity_type / aliases / rename_evidence / identity_decision`
     ——用 Python 脚本对全部 15 条做集合差校验，**缺失字段数=0**。
   - scope 层（`observation_scope_layer.scopes`）：6 条 scope 条目，逐条含
     `scope_level / members / scope_effective_period`——缺失字段数=0。
2. **PyYAML 解析**：本机 PyYAML 6.0.3，`yaml.safe_load()` 成功解析整份文件，
   顶层 6 个 key（`schema_version/source_doc/frozen_baseline/basis/
   identity_layer/observation_scope_layer`）均可读。
3. **5组实体覆盖**：`source_ruling` 字段在身份层与 scope 层均覆盖 `{1,2,3,4,5}`，
   对应 `entity-registry.md` 表格中的全部 5 条裁决（海信集团vs海信宽带 / 旭创系 /
   长飞系 / 武汉昱升更名 / 顺丰系）。
4. **validate_edges.py 扩展**：`demo/src/validate_edges.py` 已含
   `EDGE_TYPES / EDGE_SUBTYPES / SCOPE_LEVELS` 三个可选扩展字段的校验逻辑
   （第104–130行、第481–601行），且设计为"列缺失则跳过、零回归"。
5. **实跑现有 236 边**：
   ```
   python3 demo/src/validate_edges.py --edges output/edges.csv --nodes output/nodes.csv
   ```
   实测 `output/edges.csv`=237行(236边)、`output/nodes.csv`=170行(169节点)，
   与冻结快照数字一致。运行结果 **`RESULT: PASS structural=0 truth=0/0`**
   （另有5条锚点WARN + 32条节点引用WARN，均为WARN级不影响RESULT，与代码注释预期
   的"零回归"设计一致）。

**观察（非缺陷，供终验参考）**：
- `entity-registry.md` 顶部仍标注"未冻结"，与 D1 已把5条裁决数据化的完成度不完全
  对称——但文档本身已注明"随 ROADMAP-v1.7 草案建立，未冻结"是指登记册整体治理状态，
  非字段完整性问题，不构成本轮验收缺陷。
- `SC_SF_MERGED` 的 `scope_level` 标注为 `legal_entity`，但其 `notes` 提到"西安顺丰为
  子/分支，可走 branch scope 独立观察"——即当前落地是 legal_entity 口径、branch 口径
  仅在 notes 中作为待办提及，未落成独立 scope 条目。轻微不一致，不影响结构校验，建议
  终验裁决时留意。

---

## D2｜discovery_queue.py + discovery-queue-README.md

**结论：通过**

1. **六类裁决字段落地**：README 第51–61行明确六类裁决值域
   {生产中/拟生产/采购使用/销售代理/仅提及/无法判断}；源码第64行常量注释同步、
   第73/78行队列与台账schema均含该字段。
2. **owner/时间戳/理由三件套（连同闸裁决共四件套）**：README 第62–64行明确
   "裁决四件套：闸裁决/裁决人/裁决时间戳/理由 同空或同填，不允许半填"；源码
   第229–245行 `A5` 断言函数逐行校验四件套同空同填 + ISO8601时间戳格式，且带
   正例（MOCK正例必过）与3类反例（旧裁决词/半填/非ISO时间戳，必须被拦截）的
   内存自测（不落盘）。
3. **"原型-未准入"标注**：README标题行、正文第5行、源码文件头注释（第4行）、
   运行时打印（"== discovery_queue 原型自检（D2 硬化版，原型-未准入）=="）均一致
   标注，未见遗漏或矛盾表述。
4. **实跑自测**：
   ```
   python3 flows/src/discovery_queue.py
   ```
   退出码 **0**，输出：队列总量26行（media_lead 10 / customs_diff 14 / bom_scan 1
   [MOCK] / bfs_jump 1 [MOCK]）、全部待闸状态、闸台账空骨架、**"纪律断言 A1-A6:
   通过"**。产出3个 `proto-` 前缀文件（`proto-discovery-queue.csv` /
   `proto-gate-ledger-skeleton.csv` / `proto-coverage-mock.csv`），未覆盖任何既有
   正式产物，与README §2一致。

**观察**：无缺陷。README §9红线明确"代码零实体名"，抽查源码未见硬编码公司/实体名。

---

## D3｜s0b-candidates.csv + edge-subtype-schema-proposal.md

**结论：通过**

1. **字段含识别依据与置信**：`flows/out/s0b-candidates.csv`（67行，66条候选）
   表头为 `node_id,名称,市场,代码,识别依据,置信`，逐行均填写"识别依据"（多引用
   nodes.csv既有代码 / Wind基本档案查询结果 / 本地年报交叉）与"置信"
   （高/中/低三档）。
2. **抽3行核实证券代码与公司名匹配**（凭已知信息核实，未发现错配）：
   - N33 源杰科技 → `688498.SH`（科创板）—— 匹配（陕西源杰半导体科技股份有限公司）。
   - N94 华工科技 → `000988.SZ`（深市主板）—— 匹配（华工科技产业股份有限公司）。
   - N159 锐科激光 → `300747.SZ`（创业板）—— 匹配（武汉锐科光纤激光技术股份有限公司）。
   三行代码与公司名核实一致，未发现明显错配；未做任何改动。
3. **unknown 如实标注**：抽查11行 `代码=unknown` 或 `市场=unknown` 的记录
   （如N75上海飞博激光、N106广东瑞谷光网、N133洛阳中超新材料等），"识别依据"栏均
   如实说明"Wind同名查询无结果/误配/法人名称不一致故拒绝赋码"等具体原因，且多数
   同步标"置信=低"，未见强行赋码冒充已核实的情况。
4. **edge-subtype-schema-proposal.md 覆盖度**：`flows/out/edge-subtype-schema-proposal.md`
   （190行）§3含独立小节 3.2 `equity`（股权：equity_direct/indirect/control）、
   3.3 `guarantee`（担保：guarantee_authorization/exposure/release）、
   3.4 `legal_event`（含 `historical_contract` 与 `dispute_event` 两个subtype，
   并明确"不得外推为当前/主要/持续供货关系"）、3.5 `capacity_event`
   （产能事件，含equipment_type/site字段，明确"非公司间交易边"）——五个
   ROADMAP点名的subtype全部覆盖，另外还补充了3.6 `patent_event`（v1.8预留）。

**观察（非缺陷，供终验参考）**：
- 该提案的 subtype 命名体系为英文canonical值（如`equity_direct`），与
  `demo/src/validate_edges.py` 当前已实现的 `EDGE_SUBTYPES` 受控词表
  （中文值如"股权直持/股权间持/担保/历史合同/纠纷事件/产能事件/设备供货"）不是
  逐字对应——提案第146行已自行指出此落差并建议终验将存储值统一为英文canonical
  value，中文仅作展示标签。这是提案与已落地校验器之间的已知、已声明的差异，
  不构成本轮验收缺陷，但终验裁决时两份交付物需要对齐。

---

## D4｜equity-guarantee-evidence.md

**结论：通过**

1. **四件套齐全性**：`flows/out/equity-guarantee-evidence.md` 对 EG-01（1条股权）
   + GG-01/GG-02/GG-03/GG-04（4条担保）共5条，逐条均给出
   "证据文件 / 年份 / 命中引语 / 锚点"四件套（部分条目如EG-01、GG-02、GG-03还
   额外附加了"期间边界""同主体更名锚""招股书交叉"等辅助证据段落，主证据四件套
   本身完整）。锚点均为巨潮资讯网(cninfo.com.cn)或上交所(sse.com.cn)公开PDF直链。
2. **与裁剪台账对照**：`flows/out/v16-cuts-ledger.csv` 中"非供货方向"规则下
   恰好6行，其中5行（1股权+4担保）与本文档ID一一对应，第6行"华工科技→武汉华工
   正源"（子公司/集团内，非股权担保subtype）被文档正确排除在范围外（文档第4行
   明确声明"不含"该行）——范围界定准确，"1股权+4担保"数字吻合。
3. **抽1条回源核实**（额外核实2条以加强信心）：
   - **GG-04**（葛海泉、耿树霞→仕佳光子）：用 `pdftotext -layout` 从
     `flows/input/v16/688313/688313/688313__em_仕佳光子_em__2024_2024年年度报告.pdf`
     提取全文，检索到与文档命中引语**逐字一致**的行：
     `葛海泉、耿树霞 15,210,000.00 2015/12/29 2025/12/28 是`
     （文本行号11411，按`\f`分页符估算页码≈216，与文档标注"约p217"基本吻合）。
   - **EG-01**（中际旭创→源杰科技）：从
     `flows/input/v16/688498/688498/688498__em_源杰科技_em__2023_...2023年年度报告.pdf`
     提取全文，检索到与命中引语一致的行：
     `中际旭创股份有限公司 间接持股 5%以上的股东` 及紧邻的
     `苏州旭创科技有限公司 中际旭创股份有限公司之子公司`。
   两条引语均在源PDF中原文存在，非编造或误引。

**观察**：无缺陷。文档明确"备证完成，准入归终验；本稿不写edges/nodes，不改冻结
图谱"，未发现越权写入正式产物的情况。

---

## 汇总

| 路 | 结论 | 严重问题 | 观察项（非缺陷） |
|---|---|---|---|
| D1 | 通过 | 无 | SC_SF_MERGED branch scope未独立落地条目（notes中提及，未建条） |
| D2 | 通过 | 无 | 无 |
| D3 | 通过 | 无 | subtype中英文命名体系提案与已落地校验器未对齐（提案自述） |
| D4 | 通过 | 无 | 无 |

四路交付均实测通过：D1的PyYAML解析与236边零回归实跑通过；D2脚本A1-A6自检退出码0；
D3抽样3行证券代码核实无错配、5个必需subtype全覆盖；D4抽样2条引语回源比对与源PDF
逐字一致。未发现阻断级或高严重度缺陷，仅2项观察性差异供终验参考，均已在交付物自身
声明中体现，非隐藏问题。
