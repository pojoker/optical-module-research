# 内容台账（Content Ledger）— 工艺 / 技术参数 / 产品构成 / 代际事件 / 设备能力

## 1. 定位与边界红线（Schema v1 冻结纪律）

本目录承载光模块产业链**企业级客观技术与工艺内容台账**（含 `v1_salvage` 既有 5 家 377 条收编、`step2_expansion` 海内外 15 家龙头 220 条扩抽及 `step3_daily_2026q4` 2026Q4 投资者调研/互动问答/年报补录 36 条，全表合计 **633 条**、覆盖 **26 家**核心企业）。

1. **双闸物理隔离（最高红线）**：内容台账只记录工艺步骤、量化参数、产品构成、研发/量产代际事件与设备-工序能力，**严禁写入任何具名客户/供应商商业买卖订单、销售占比或采购金额主张**，且内容台账条目**永不作为 `edges.csv` 交易关系边的证据通道**。
2. **自夸隔离（`issuer_self` 永不承重）**：发行人或上市公司自我标榜“全球领先”“行业第一梯队”“国际一流”或单方援引第三方排名的竞争地位陈述，一律显式标记 `stance = issuer_self`，下游研究与渲染严禁将其作为客观承重结论；客观工艺指标标 `neutral`，行业共性原理或公开市场预测标 `industry`。
3. **叶格挂接纪律**：`cell_ids` 仅允许填写根目录 `tree.yaml` 冻结的 **41 个叶节点 `cell_id`**（多格以英文逗号分隔）或 `通用`（通用于全厂研发/生产管理制度或非光通信跨行业业务），严禁挂接父节点或关系边。
4. **行号计量与四档引语复核纪律（前端 `研序` 引用准入边界）**：
   - **统一 `\n` 计行**：全表所有 `local_source_path#Lstart..end` 与 `section_ref` 行区间一律按 `text.split('\n')`（1-based 闭区间）计量，严禁使用 `splitlines()` 将年报/招股书中的分页符 `\f` 误计为行分隔（例如科瑞技术 `CLG0632` 位于 `#L642..648`，`CLG0633` 位于 `#L630..631`）。
   - **`verified_local`（578 条）**：`re.sub(r'\s+', '', verbatim_quote)` 在本地原文**严格连续存在**，且所有声明行号区间切片 100% 闭环包含原话（其中 `step2_expansion` **220/220**、`step3_daily_2026q4` **36/36**、`v1_salvage` 连续原句 **322 条**）。**仅 `verified_local` 一档可直接作为前端 `研序` 已核引用**。
   - **`table_normalized`（37 条）**：`v1_salvage` 中因多列表格/流程图单元格合并而以 `" / "` 拼接的条目（对应 `table_cell_slash_normalized`；16 列冻结 Schema 不增设额外列，明细见 `quote_verification_report.json`），经拆分核验全部非空片段（含长度 `>=4` 片段）100% 存在于本地原文，无任何虚构；**仅作前端 `研序` 可定位候选，不得直接渲染为连续逐字原话**。
   - **`segmented_verified`（15 条）**：`v1_salvage` 中采用 `……` 节略连接（含跨页页眉节略）且拆分后各片段 100% 存在于本地原文的条目；**仅作前端 `研序` 可定位候选**。
   - **`inherited_v1_verified`（3 条：`C43, C48, C72`）**：`v1_salvage` 猎奇智能招股书多栏表格跨页表头嵌入词中导致的合规继承条目（首尾 `>=20` 字锚点均严格命中本地原文）；**仅作前端 `研序` 可定位候选**。

## 2. Schema 字段说明（16 列冻结）

| 列名 | 枚举/格式 | 说明 |
|---|---|---|
| `cid` | 字符串主键 | 唯一条目编号（v1 沿用 `SJZ/SJ24-/YJZ/YJ/CGHX/TCG24-/C` 前缀；Step 2 按公司缩写编号；Step 3 为 `CLG0598–CLG0633`） |
| `company` | 公司简称 | 全表覆盖 **26 家**海内外光模块产业链核心企业 |
| `stock_code_or_ticker` | 股票代码/状态 | A 股 6 位代码、美股 Ticker（`COHR/LITE/FN/AAOI`）或 `创业板IPO在审` |
| `source_doc` | 披露文件名称 | 招股说明书（注册稿/申报稿）、2023–2025 年年度报告、FY2025 Form 10-K、官网技术页快照、2026 年 IR 活动记录表与互动问答快照 |
| `doc_year` | 四位年份 | 来源披露文件所属年度（`2020–2026`） |
| `fact_type` | 五分互斥枚举 | `工序步骤 \| 技术参数 \| 产品构成 \| 代际事件 \| 设备-工序能力` |
| `stance` | 三分立场枚举 | `neutral`（企业客观工艺/参数）`\| industry`（行业原理/第三方预测）`\| issuer_self`（自评/排名，不承重） |
| `tense` | 三分时态枚举 | `current \| historical \| planned` |
| `cell_ids` | 叶格列表 | `tree.yaml` 41 个叶格（逗号分隔）或 `通用` |
| `atomic_fact` | 中文原子句 | 单条可独立核验的工艺/参数/产品/代际/设备能力事实（海外 10-K 统一提供中文提炼句） |
| `verbatim_quote` | 原文逐字引语 | 对应本地语料的逐字原句（海外 10-K 与 ficonTEC 网页保留英文原句） |
| `section_ref` | 章节与行号定位 | 披露文件章节路径、页码及按 `\n` 计量的本地文本行号区间 |
| `local_source_path` | 仓库相对路径 | 对应 `corpus/` 下的真实本地文本文件（支持可选 `#Lstart..end` 1-based `\n` 行区间锚点） |
| `anchor_url` | 官方链接 | 巨潮资讯、上交所、深交所、SEC EDGAR、上证 e 互动、深交所互动易或官网原始 URL |
| `quote_verification_status` | 四分复核状态 | `verified_local`（严格连续命中且行号闭合，可作研序直引）/ `table_normalized` / `segmented_verified` / `inherited_v1_verified`（后三档仅作可定位候选） |
| `batch` | 批次标识 | `v1_salvage`（377 条）/ `step2_expansion`（220 条）/ `step3_daily_2026q4`（36 条） |

## 3. 覆盖规模、四档验证状态与公司分布

- **总条目数**：**633 条**（物理 CSV 行数 **634 行**，唯一企业 **26 家**）
  - `v1_salvage`：**377 条**（5 家企业：`verified_local` 322 / `table_normalized` 37 / `segmented_verified` 15 / `inherited_v1_verified` 3）
  - `step2_expansion`：**220 条**（15 家企业：**220/220 = 100.0%** 严格连续 `verified_local`）
  - `step3_daily_2026q4`：**36 条**（16 家企业，`CLG0598–CLG0633`：**36/36 = 100.0%** 严格连续 `verified_local`）
- **四档验证汇总**：`verified_local` **578 条（91.31%）** ｜ `table_normalized` **37 条** ｜ `segmented_verified` **15 条** ｜ `inherited_v1_verified` **3 条**（异常未命中 **0 条**）
- **行号闭环核验（`text.split('\n')`）**：`#Lx..y` 路径锚点 **2/2** 命中；`section_ref` 行区间 **237/237** 命中。

| 批次 | 公司 | 代码/Ticker | 条目数 | `verified_local` | 候选三档 (`table`/`seg`/`inh`) | 主要挂接叶格 |
|---|---|---|---:|---:|---:|---|
| `v1_salvage` | 仕佳光子 | `688313` | 99 | 87 | `10/2/0` | `D8,C1,通用,M4,D9,M2a` |
| `v1_salvage` | 源杰科技 | `688498` | 108 | 107 | `1/0/0` | `C1,M2a,通用,P1` |
| `v1_salvage` | 长光华芯 | `688048` | 63 | 40 | `23/0/0` | `通用,C1,C2,M2b,C3` |
| `v1_salvage` | 太辰光 | `300570` | 24 | 22 | `2/0/0` | `通用,D9,MOD1,D10,D8` |
| `v1_salvage` | 猎奇智能 | `创业板IPO在审` | 83 | 66 | `1/13/3` | `EQ3,EQ4,EQ7,通用,EQ5,MOD1` |
| `step2_expansion` | 联讯仪器 | `688808` | 16 | 16 | `0/0/0` | `EQ7,P1,C1,EQ6,C4` |
| `step2_expansion` | 炬光科技 | `688167` | 15 | 15 | `0/0/0` | `D7,B2,P1,M4,D11,D9` |
| `step2_expansion` | 长进光子 | `688635` | 14 | 14 | `0/0/0` | `M4,通用` |
| `step2_expansion` | 盛合晶微 | `688820` | 14 | 14 | `0/0/0` | `P1,EQ7` |
| `step2_expansion` | 中际旭创 | `300308` | 15 | 15 | `0/0/0` | `MOD1,MOD2,C4,MOD3,C1,C5` |
| `step2_expansion` | 新易盛 | `300502` | 14 | 14 | `0/0/0` | `MOD1,C4,D12,MOD2,MOD3,B1` |
| `step2_expansion` | 天孚通信 | `300394` | 15 | 15 | `0/0/0` | `D12,D9,D10,D7,D8,D6` |
| `step2_expansion` | 光迅科技 | `002281` | 15 | 15 | `0/0/0` | `MOD1,MOD2,MOD3,D8,C1,C4` |
| `step2_expansion` | 华工科技 | `000988` | 14 | 14 | `0/0/0` | `MOD1,D12,C4,MOD2,MOD3,D3` |
| `step2_expansion` | 罗博特科/ficonTEC | `300757` | 16 | 16 | `0/0/0` | `EQ4,EQ7,EQ3,C4,EQ6,D7` |
| `step2_expansion` | 东山精密/索尔思 | `002384` | 14 | 14 | `0/0/0` | `C1,MOD1,M2a,MOD3,B1,C4` |
| `step2_expansion` | Coherent | `COHR` | 15 | 15 | `0/0/0` | `C1,C2,MOD1,MOD2,MOD3,C5` |
| `step2_expansion` | Lumentum | `LITE` | 15 | 15 | `0/0/0` | `C1,MOD1,MOD2,C6,C4,MOD3` |
| `step2_expansion` | Fabrinet | `FN` | 14 | 14 | `0/0/0` | `EMS1,M4,MOD1,D7,MOD2,MOD3` |
| `step2_expansion` | AAOI | `AAOI` | 14 | 14 | `0/0/0` | `C1,MOD1,MOD3,D12,M2a,C5` |
| `step3_daily_2026q4` | 中际旭创 | `300308` | 4 | 4 | `0/0/0` | `MOD1,D12,C4,C1,C5,D9` |
| `step3_daily_2026q4` | 罗博特科/ficonTEC | `300757` | 4 | 4 | `0/0/0` | `EQ7,EQ4` |
| `step3_daily_2026q4` | 天孚通信 | `300394` | 3 | 3 | `0/0/0` | `D9,D12` |
| `step3_daily_2026q4` | 新易盛 | `300502` | 3 | 3 | `0/0/0` | `MOD1,D12` |
| `step3_daily_2026q4` | 华工科技 | `000988` | 2 | 2 | `0/0/0` | `MOD1,D12` |
| `step3_daily_2026q4` | 剑桥科技 | `603083` | 3 | 3 | `0/0/0` | `MOD1,D12,C4` |
| `step3_daily_2026q4` | 博众精工 | `688097` | 2 | 2 | `0/0/0` | `EQ3,EQ4` |
| `step3_daily_2026q4` | 长光华芯 | `688048` | 3 | 3 | `0/0/0` | `C1` |
| `step3_daily_2026q4` | 光迅科技 | `002281` | 2 | 2 | `0/0/0` | `MOD1,C5,D6` |
| `step3_daily_2026q4` | 景旺电子 | `603228` | 2 | 2 | `0/0/0` | `B1` |
| `step3_daily_2026q4` | 炬光科技 | `688167` | 1 | 1 | `0/0/0` | `D7,D9` |
| `step3_daily_2026q4` | 凯格精机 | `301338` | 1 | 1 | `0/0/0` | `EQ3,EQ4` |
| `step3_daily_2026q4` | 东山精密/索尔思 | `002384` | 2 | 2 | `0/0/0` | `C1,MOD1,EQ1,M2a` |
| `step3_daily_2026q4` | 仕佳光子 | `688313` | 1 | 1 | `0/0/0` | `M1,D8` |
| `step3_daily_2026q4` | 汇绿生态 | `001267` | 1 | 1 | `0/0/0` | `MOD1` |
| `step3_daily_2026q4` | 科瑞技术 | `002957` | 2 | 2 | `0/0/0` | `EQ3,EQ4` |

## 4. 重建与幂等复核命令

```bash
# Step 4 全表 633 行 \n 行号闭环、四档真伪分级与报告/README 幂等同步
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 out/step4-backend-final-closure-20261122/remediate_content_ledger.py
```
