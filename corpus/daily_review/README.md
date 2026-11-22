# Daily 状态跃迁过滤（种子 + 正向规则 + 高置信噪音 + Unclassified）与持久审核池 (`corpus/daily_review/`)

## 1. 设计目标与三条硬边界铁律

日常监控流（海外官网/新闻室 RSS、国内深沪投关记录表与互动易问答、云端日更摘要）每日产生大量非结构化文本。本目录建立确定性的 **四桶透明分流 + 持久审核池** 机制，严格执行三条硬边界铁律：

1. **严禁未知条目静默归噪音**：`_classify_overseas_noise()` 仅识别四类高置信度明确噪音（律所征集、获奖/人事/CSR、IR 日历/电话会预告页、综合巨头非光业务线）；凡未命中正向规则亦未命中高置信噪音的条目，一律诚实标为 **`unclassified`** 单独统计（`353` 条，`66.23%`），供人工定期抽检召回率，杜绝把未覆盖财报或并购伪装成已审噪音。
2. **防滚动窗滑出丢失（永不过期挂起）**：`overseas/staging/` 的 14 天滚动窗口仅作采集缓冲（全量 `533` 条唯一披露候选中已有 `419` 条滑出最新日窗口）。全部 **`68`** 条触发项（历史种子 `25` 条 + 正向标题规则命中 `43` 条，含 10–11 月挽救的 `MTSI FY26Q4`、`TSEM Q3`、`GFS Q3`、`VECO Q3`、`VECO×ACLS`、`SOI FY27H1`、`ANET Q3`、`CRDO×ORCL`、`KEYS FY26Q4`）100% 固化入 `review_queue.csv`，退出滚动窗后永不自动删除。
3. **防未核传闻/动态空壳/未交割协议污染正史**：凡源站返回动态空 JS 壳（`DRQ0037` LWLG QuoteMedia）、未上市私企缺独立一手规格书/IPO 稿（`DRQ0048` 微见智能、`DRQ0049` 镭神技术）、具名客户保密未披露（`DRQ0050` 科瑞技术 U11）、股权收购/重组尚未过会交割（`DRQ0053` 利扬芯片拟购众望达 51%、`DRQ0098` 朗特智能拟购成都奥捷 51%、`DRQ0099` 科瑞思拟购宏钢光电 100% 预案）、科创板注册生效尚未挂牌（`DRQ0101` 上海羲禾科技）或仅处验证未获大单（`DRQ0052` 长光华芯 200G EML），一律诚实留置 `pending_*` 并写明 `missing_verification_gate`，严禁虚挂引用。

---

## 2. 海外 Staging 四桶透明分流规则 (`seeded_plus_positive_rules_split`)

- **正向入队桶（`SEEDED_OVERSEAS_DC_IDS` + `_classify_overseas_positive_rule`）**：除 `25` 条历史种子外，对全部受追踪海外实体执行确定性标题触发规则（命中 `Financial Results / Quarter / Half-Year / Full-Year / Interim Results / 10-Q / 10-K / 8-K / Merger / Acquire / Combine / 800G / 1.6T / 3.2T / 6.4T / CPO / NPO / InP / EML / Silicon Photonics / Transceiver / Co-packaged` 等），100% 纳入 `review_queue.csv`。
- **四类明确高置信噪音（`HIGH_CONFIDENCE_NOISE_CLASSES`）**：
  - `non_optical_corporate_line`：综合巨头非光通信产品线通稿（VMware/Splunk/Webex/游戏显卡/5G FWA/汽车电子等）。
  - `award_ranking_hr_csr`：企业获奖榜单（Forbes/TIME）、高管任免、高校捐赠、社会责任与招聘公关稿。
  - `investor_lawsuit_spam`：美股证券律所集体诉讼征集广告。
  - `ir_calendar_or_index_page`：财报发布日期预告、业绩电话会排期通知、静态 SEC Filings 列表页。
- **未分类抽检池（`unclassified`）**：未命中正向触发词亦不属于上述四类明确噪音的一般企业通稿，单独保留计数供召回率抽检。
- **Gemini 云端日更快照水位监控（`cloud-snapshot.json` 只读对账）**：共检测到 `81` 条 `[YYYY-MM-DD]` 逐日纪要（`2026-08-27` 至 `2026-11-18`），人工分流核对水位 `triaged_through_date=2026-11-18`，水位后未分流新增日期 `untriaged_entry_dates=[]`（`0` 条）。

### 实测分流统计（截至 `2026-11-22`）

| 数据源分母 | 唯一候选总数 | 种子+正向规则触发数 (占比) | 高置信明确噪音数 (占比) | `unclassified` 待抽检数 (占比) |
|---|---:|---:|---:|---:|
| 海外 `staging/` 9–11月披露日口径 (`published_at >= 2026-09-01`) | `504` | `66` (`13.1%`: 种子 `25` + 规则 `41`) | `102` (`20.24%`) | `336` (`66.67%`) |
| 海外 `staging/` 全量 `66` 期快照唯一 `DC_*` | `533` | `68` (`12.76%`: 种子 `25` + 规则 `43`) | `112` (`21.01%`) | `353` (`66.23%`) |
| 历史回填审阅 `daily-backfill-review-20261109` (`D-/O-/G-`) | `3063` | 去重高优样本全部并入持久队列（保留 `D-/O-/G-` 映射） | `2839` (`92.69%` 线索/待定位/机械召回) | `0` |

---

## 3. 四类状态跃迁触发门槛 (`trigger_type`)

1. **`T1_lifecycle_shift`（代际/认证/量产/产能、合规法条与季度财报跃迁）**：800G/1.6T/3.2T/6.4T、200G EML、CPO/NPO、LPO/ALC、InP/Photonics-SOI 衬底扩产、进出口法规判例及最新季度正式财报（如 `DRQ0046` 挂 `KN011-KN014`、`DRQ0100` 波长光电两用镜片诉讼挂 `KN013`、`DRQ0104` NVIDIA×Lambda 魁北克万卡级 CPO 集群双源互证 `EV061`、云南锗业 `2026-057` 公告 `18,856->26,999万元`、Soitec `~12亿美元` 产能预留协议）。
2. **`T2_supply_relationship_or_ma`（供应链实名绑定、并购协议/交割与标准合作）**：具名上下游关系（GFS×Marvell SiGe 扩产长约、Tower×中际旭创 NPO 早期生产、IQE×Quintessent QDL 外延协议、Credo×Oracle OCP 遥测标准）及重大并购（Marvell×Lumentum 全股票协议未交割、Veeco×Axcelis 顺延至 `2027Q1` 末、利扬芯片拟购众望达 51% 未交割、朗特智能拟购成都奥捷 51% 待股东会与交割、科瑞思拟购宏钢光电 100% 预案审计评估进行中）。
3. **`T3_commitment_verification`（管理层公开承诺与长期采购承诺原文裁决）**：`calls/commitments.csv` 到期核验及 Lumentum FY27Q1 逾 `50亿美元` `NPO/CPO win` 四重边界锁定。
4. **`T4_universe_blindspot`（公司宇宙补录、设备层对称性与观察池纳管）**：联讯仪器 `688808`、云南锗业 `002428`、科瑞技术 `002957`、天准科技 `688003`（`P277` CPO 在线 AOI 小批量交付）及圈外新核实主体（上海羲禾科技、粤芯半导体 `301660`、成都奥捷、安费诺 `APH`、Lambda）观察池追踪。

---

## 4. 队列状态机与机器门约束 (`review_queue.csv`)

当前持久队列共 **`105`** 行（`P0=29`、`P1=30`、`P2=46`）：

- **`ingested_to_kb`（`57` 行）**：经一手原件（巨潮 `%PDF-` / 政府公报 / 官网 HTTP 200 静态存档）逐字核对并写入主账本；**硬门要求 `kb_target_ref` 非空且在六类主表（`points` / `edges` / `content` / `timeline` / `calls` / `knowledge`）真实存在**。
- **`pending_primary_text`（`1` 行）**：受源站动态 JS 空壳限制暂未入正史（仅 `DRQ0037` LWLG 在列；原 `DRQ0046` 合规政策池已取一手公报写入 `KN011-KN014` 办结）；**硬门要求 `missing_verification_gate` 非空**。
- **`pending_filing_anchor`（`8` 行）**：客观受限于未上市私企披露、客户 NDA 保密、产品仍在客户端验证、科创板注册生效尚未挂牌或收购重组尚未过会交割（`DRQ0048/0049/0050/0052/0053/0098/0099/0101`）；**硬门要求 `missing_verification_gate` 非空**。
- **`watch_deferred`（`39` 行）**：经核查属树外系统板（`DRQ0032` 沪电交换机 PCB）、极小比例不并表参股科研验收（`DRQ0054` 经纬辉开 7.71%）、观察池非季度槽主体（`DRQ0064` Keysight `WATCH_KEYS`）、圈外新上市综合晶圆代工/标准立项/展会演示线索（`DRQ0102` 粤芯半导体、`DRQ0103` OIF Q4 标准立项、`DRQ0105` 安费诺 SC26 展台）及正向标题规则入池留痕的泛半导体/EMS/展前预告项，永久保留防滑出丢失且零虚挂引用。

### 幂等构建与机器校验命令

```bash
# 确定性重建 review_queue.csv / triage_stats.json / README.md
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --build

# 零写入校验磁盘文件与重算结果字节级一致及全部硬门不变量
PYTHONDONTWRITEBYTECODE=1 /Users/jowang/miniconda3/bin/python3 corpus/daily_review/sync_daily_queue.py --check
```
