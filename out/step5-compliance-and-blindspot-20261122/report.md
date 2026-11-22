# Step 5 执行与核验报告 (`OPTICAL-STEP5-COMPLIANCE-AND-BLINDSPOT-CLOSURE-20261122`)

> 核验日期：`2026-11-22` | 执行架构：`Orchestrator (Carbon)` 双并行 Worker + 协调者七门终验

## 1. 合规一手原件归档与知识卡入库 (`KN011–KN014` · `DRQ0046` 办结)

1. **一手政府与司法原件抓核**（详见 `out/step5-compliance-and-blindspot-20261122/compliance_manifest.json`）：
   - 核验 9 条合规审计项共 `31` 个官方 URL，抓回 **`24` 份 HTTP 200 一手原件**（计算 `SHA256` 并逐字核实核心引语），复核 `3` 份既有本地公告，严守不绕反爬/证书底线诚实登记 `3` 份 EUR-Lex WAF 挑战页（`http_403_or_gated`）及 `1` 份商务部子站证书不匹配页（`error`），在 `knowledge.yaml` 中改用 `url` 锚。
   - 重点新增 `corpus/ir/301421/301421_2026-10-08_关于公司收到起诉书的公告_1225597511.PDF` 及其 `.PDF.txt`（`109` 行），精准定位波长光电涉两用光学镜片约 `2,010.85 万元` 公诉案。
2. **新增 `KN011–KN014`**（总知识卡 `10 -> 14`，零禁用词）：
   - **`KN011`**：美国 CBP“实质性转变”正反四案对照（`H335829` 新易盛、`N359369` 索尔思台湾两宗均因**主 PCBA SMT 在中国制成**判中国原产；对照 `N344720`、`N358465` 光迅泰国/马来西亚因**主 PCBA 在当地制成**判泰/马原产），叠加 `USTR` 178 项排除延至美东 `2027-01-09 23:59` 与中方对应关税安排延至 `2027-01-10`。
   - **`KN012`**：`FCC 26-50`（`91 FR 57798`，`2026-10-13` 生效，`47 CFR § 2.903(b)(2)`）与 `DA 26-1130A1`/`DA 26-1203A1` Covered List 均未列入通用商用光模块、无“3.2T / 65%”成文法条；参议院 `S.5548` 仅转交委员会且限联邦关键系统成法 `5 年` 后生效；11 月中旬行政扩围游说动向单列风险跟踪。
   - **`KN013`**：商务部/科技部 `2026 年第 48 号公告` 拟增列 `266507X`（`>10,000` 张加速卡、双向带宽 `≥800 GB/s` 集群互连技术）征求意见与出口前临时登记，与《两用物项出口管制条例》下 `301421 波长光电` 起诉案及 `002428 云南锗业/云南鑫耀` 磷化铟出口许可披露（`P202`）构成双向合规锚。
   - **`KN014`**：美 BIS `EAR § 734.9`（FDPR 按 ECCN/目的地/用途/用户四要素逐笔认定）与欧盟 `EED (EU) 2023/1791 Art.12` / `(EU) 2024/1364` / `C(2026) 3472`（`≥500kW` IT 功率数据中心年度报送与 PUE 评级程序，最低绩效标准尚在公开征询）。
3. **研究笔记与门禁升级**：
   - 更新 `refs/us-china-optical-transceiver-restrictions.md` 新增 `§12`（`refs/` 保持 `8` 个文件不变）。
   - `scan.py` 新增 `review_queue.kb_target_ref` 对 `knowledge:KN###` 前缀的闭合校验与 `--selftest` 正反例（`153 -> 155` 全过）。

## 2. 11 月中旬四大盲区线索核验与对称登记（`DRQ0098–DRQ0105`）

详见 [blindspot_leads_verdicts.json](file:///Users/jowang/Downloads/optical-module-research/out/step5-compliance-and-blindspot-20261122/blindspot_leads_verdicts.json)（`16` 份 HTTP 200 一手原件：`corpus/ir/301314/` `3` 份 + 圈外 `corpus/web/step5_20261122/blindspots/` `13` 份，零越界建 `300916`/`301660` 目录）：

1. **`300916 朗特智能` 拟购 `成都奥捷通信技术有限公司` 51%（`DRQ0098`, `pending_filing_anchor`）**：核实 `2026-042` 公告，现金 `6.63 亿元` 对价、`10G–3.2T` 无源器件与隔离器、2026–2028 承诺净利 `0.8/1.2/1.6 亿元`，待 `2026-12-02` 临时股东会审议与工商交割。
2. **`301314 科瑞思` 拟购 `深圳市宏钢光电封装技术股份有限公司` 100%（`DRQ0099`, `pending_filing_anchor`）**：核实 `2026-10-26` 重组预案（标的前身即 `P258/N138` 深圳宏钢），覆盖光通信金属/HTCC 陶瓷气密管壳、50G PON/TOSA/ROSA 外壳及预置金锡热沉；审计评估与定价均未办结、未交割。
3. **`上海羲禾科技`（`DRQ0101`, `pending_filing_anchor`）与 `301660 粤芯半导体`（`DRQ0102`, `watch_deferred`）**：前者已获证监会同意注册批复（`证监许可〔2026〕2940号`），`1.6T NPO/CPO` 芯片有销售而 `3.2T/6.4T` 处验证与募投阶段，尚未挂牌；后者 `2026-10-13` 创业板上市，主营为 `25.11 亿元` 模拟/功率晶圆代工，`90nm SiPho` 累计投片超 `7,000` 片但 **`3.2T NPO` 仅处“正在导入”**、`65nm` 系募投研发。
4. **`OIF Q4`（`DRQ0103`, `watch_deferred`）、`NVIDIA × Lambda SC26 CPO`（`DRQ0104`, `ingested_to_kb` -> `calls:EV061`）与 `安费诺 SC26`（`DRQ0105`, `watch_deferred`）**：抓回 OIF 曼谷 Q4 七项新立项官稿及 NVIDIA + Lambda 双第一方 HTTP 200 博客正式入账 `EV061 (corroborated)`；安费诺因 `amphenol-cs.com` HTTP 403 诚实留置 `watch_deferred`。
5. **对称观察池与水位监控**：`tree.yaml`、`refs/entity-registry.yaml` 与 `corpus/salvaged/entity_nodes.csv` 对称更新 `N138` 并新增 `N174–N179`；`corpus/daily_review/sync_daily_queue.py` 将 `DRQ0046` 正式转 `ingested_to_kb`（全队列 `105` 行，待原文收口至 `1` 项 `DRQ0037`），并接入 `scan_gemini_cloud_snapshot()` 跟踪 `cloud-snapshot.json` 水位（`triaged_through_date=2026-11-18`，`untriaged_entry_dates=[]`）。

## 3. 七道机器门终验结果（全部退出码 `0`）

| 验证门 | 结果摘要 | 退出码 |
|---|---|---:|
| `scan.py --selftest` | `155/155` 用例全通过（新增 `knowledge:KN###` 正反例） | `0` |
| `scan.py --check` | 语料距今 `1` 天，缺席年报 `0` 家，不变量 `①–⑭` 全绿 | `0` |
| `render.py --verify` | 两次临时重建字节一致 | `0` |
| `participation.py --check` | 宇宙 `466 / 466`，确认 `94`，待确认 `13` | `0` |
| `-m calls check` | `39` 家公司 / `180` 条信源 / `79` 条主张 / `61` 条雷达事件闭合 | `0` |
| `sync_daily_queue.py --check` | `105` 行零漂移（入库 `57` / 待原文 `1` / 待法定锚 `8` / 观察 `39`） | `0` |
| `pytest -q`（仓库根目录裸跑） | **`499 passed, 189 subtests passed`**（含 `test_step5_compliance_and_blindspot.py`） | `0` |
