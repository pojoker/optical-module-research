# 海外事件雷达日更镜像（daily discovery mirror）

按实体扫描官方/监管/对手方/政府端点，把“每日发现”写成**候选**，落在一个独立的
`state_root` 里。它是事件账本的**输入端镜像**，不是第二个账本：`calls/*.csv`、
`calls/out/` 与根 canonical 全部只读，任何情况下都不会被本模块写入。

```bash
# 扫描并写候选（state-root 必须在 source-root 之外）
python3 -m calls.daily_discovery run \
  --source-root . --state-root /path/to/state \
  --date 2026-09-01 \
  --config calls/discovery_config.json

# 离线演练/测试（不访问公网）
python3 -m calls.daily_discovery run \
  --source-root . --state-root /path/to/test-state \
  --date 2026-09-01 --config calls/discovery_config.json \
  --fixtures calls/fixtures/daily_discovery

# 只读验证 staging 能映射到现有 schema（不 promote、不写任何账本文件）
python3 -m calls.daily_discovery verify \
  --source-root . --state-root /path/to/state --date 2026-09-01
```

不安装 cron，不改动现有调度，`run` 只做一次扫描。

---

## 1. 监控池并集

`load_entity_registry()` 取三类的并集，任何一类不合格都不进池：

| 来源 | 入池条件 | 当前配置用到的样本 |
| --- | --- | --- |
| `universe.csv` | `enabled=yes` 的季度覆盖公司 | `AAOI`、`LITE`、`CSCO`、`MTSI`、`POET` |
| `watch_entities.csv` | `monitoring_status=active` 的事件监控实体 | `WATCH_IQE` |
| `company_candidates.csv` | `verification_status != promoted` 的未晋级候选 | `CAND_HAMAMATSU` |

已晋级（`monitoring_status=promoted` / `verification_status=promoted`）、已暂停
（`paused`）和已停用（`enabled=no`）的行都不在池内，避免与正式池重复计票。

## 2. 实体别名与身份解析

- 别名来自 `watch_entities.csv` 的 `entity_name` 与 `aliases`（分号分隔）。
- 身份去重只用 `entity_relationships.csv` 中 `review_status=reviewed` 且类型属于
  `parent_of / subsidiary_of / acquired_by / brand_of / predecessor_of /
  business_transferred_to` 的关系；并查集按“季度公司 → 在监实体 → 已晋级实体 → 候选”
  的优先级选主身份。仍为 `candidate` 的关系不参与身份合并。
- 例：`WATCH_OCLARO --acquired_by--> LITE`（reviewed），因此正文中出现 “Oclaro”
  时解析到主身份 `LITE`，而不是新增一家公司。
- 别名匹配使用词边界正则，命中后统一折叠到主身份再入候选。

## 3. 端点配置（`calls/discovery_config.json`）

按实体声明端点，`load_discovery_config()` 强制以下约束：

- 允许的 `endpoint_kind`：`official_ir`、`official_blog`、`regulatory_filing`、
  `counterparty_release`、`government_record`、`product_page`。
- **拒绝** `media`、`generic_news`、`aggregator`、`macro_news`；`disclosure_type=media`
  同样被拒绝。宏观泛新闻流不能代替公司覆盖。
- 端点 URL 必须是可追溯的 http/https 页面；不绕过登录或付费墙。
- 实体必须在监控池内。
- `first_party` 端点不得声明 `corroborates_entity_ids`；非 `first_party` 端点
  **必须**声明 `corroborates_entity_ids`（对手方/监管材料要说明它在为谁作证）。

## 4. 产出物（全部只在 `state_root` 下）

```
<state_root>/
  .daily-discovery.lock          运行锁（O_EXCL，异常也会释放）
  daily/YYYY-MM-DD.txt           当日人类可读报告
  staging/YYYY-MM-DD/
    disclosure_candidates.csv    表头 = calls/disclosures.csv
    claim_candidates.csv         表头 = calls/event_claims.csv
    event_candidates.csv         表头 = calls/events.csv
    evidence_candidates.csv      表头 = calls/event_evidence.csv
    dedupe-manifest.csv          run_date,item_url,endpoint_id,decision,detail,
                                 target_id,origin_group,content_hash
    failures.csv                 run_date,failure_type,endpoint_id,item_url,
                                 entity_id,detail
    candidates.json              机器可读明细（含 corroboration 建议与 caveat）
    run-summary.json             计数与 promoted=0
  queue-latest.json / queue-prev.json / queue-diff.json
```

ID 前缀：`DC_` 披露候选、`CC_` 主张候选、`EC_` 事件候选、`VC_` 证据候选、
`OGC_` origin group、`PRGC_` program。全部由 `sha1` 派生，同输入同 ID。

## 5. 逐项映射到现有事件账本

| 现有账本 | 对应候选 | staging 保留了什么 | 人工过闸后才允许写什么 |
| --- | --- | --- | --- |
| `disclosures.csv` | `disclosure_candidates.csv` | canonical URL、`published_at`、`retrieved_at`、`content_hash`、`origin_group`、`provenance_class`、`disclosure_type`/`content_class`、锚点 | 人工核锚后 `processing_status=anchor_reviewed` 并填 `reviewed_at`/`review_scope`；本模块永远只写 `candidate_extracted` 或 `unprocessed` |
| `event_claims.csv` | `claim_candidates.csv` | 逐段 `quote` + `anchor`、`statement_kind`、`claimant_role` | 人工核对说话人、原文、定位、事实/前瞻后改 `anchor_reviewed`；自动结果**只能是 `candidate`**，永不为 `anchor_reviewed` |
| `events.csv` | `event_candidates.csv` | `event_category`、`lifecycle_stage`、`occurred_start/end`、`primary_subject_id`、`counterparty_ids` | `event_status` 自动固定为 `asserted`；`corroborated` 只在 `candidates.json` 里作为**建议**出现，批准后才由人工改；`previous_event_id` 留空（阶段串联是人工判定） |
| `event_evidence.csv` | `evidence_candidates.csv` | `relationship`、`independence_class`、与披露一致的 `origin_group` | 独立性判定与证据采纳由人工复核；第一方材料永不标成独立证据 |

`verify` 命令给出的只读证明即上表：四张候选表逐一按 `calls/schema.py` 的枚举与引用
完整性校验，并打印“curated ledger read-only”与“verify never promotes: 0 rows
written”。

## 6. 去重与证据独立性

manifest 的 `decision` 取值与含义：

- `new_disclosure_candidate`：新候选。
- `duplicate_url`：canonical URL 已在 `disclosures.csv` 或本轮出现过。
- `duplicate_hash`：正文规范化后的 `content_hash` 已存在（不同 URL 的逐字转载）。
- `duplicate_origin_group`：同一 `origin_key` 的转载。同一底层公告的多处转载归入
  同一 origin group，**不重复计票**，也不算独立来源。
- `duplicate_claim` / `duplicate_event`：quote/anchor 或
  (subject, category, stage, date) 已在账本中。

独立性规则：

- `provenance_class=first_party` → `independence_class=first_party`。第一方公告
  **不是独立证据**。
- `counterparty → counterparty`、`regulator → regulator`、
  `government → observable_result`、`third_party → third_party`、`unknown → same_origin`。
- 只有同时存在（a）第一方 asserted origin 与（b）不同 origin 的
  `counterparty | regulator | observable_result` 证据时，`candidates.json` 才会给出
  `suggested_event_status=corroborated`；写入 CSV 的 `event_status` 仍是 `asserted`，
  并进入队列等待人工批准。

## 7. 权限边界（自动发现的硬约束）

1. 自动主张**只能**是 `candidate`，不写 `anchor_reviewed`。
2. 自动事件**至多** `asserted`；`corroborated` 只是建议。
3. 技术博客/演示（`technical_blog`/`product_page`/`datasheet` 或
   `demonstration_disclosure`）不得推导量产、客户采用、订单规模、供货关系或需求规模。
   越界时写 `permission_denied` 失败并说明原因，不生成事件候选。演示本身
   （`demonstrated` 阶段）仍是合法候选。
4. forward-looking 不写成已兑现：命中成熟商业动词但整句带前瞻语气（expects /
   plans / will / by Q4 …）时，降级为 `announced` + `forward_looking`，
   `realized=false`，并在事件 caveat 中留下 `forward_looking_not_realized`。
5. 未解析实体、低置信度映射（同时命中多个实体）、抓取失败、非法条目、未来发布日期、
   无相关内容，全部显式写入 `failures.csv` 与 `queue-latest.json`，不静默丢弃。

## 8. 幂等、锁与原子写

- 锁：`<state_root>/.daily-discovery.lock`，`O_CREAT|O_EXCL`；持锁时再跑会报
  `lock is held`，异常路径也会释放锁。
- 原子写：`tempfile.NamedTemporaryFile` + `fsync` + `os.replace`，同目录临时文件，
  运行结束后不留 `.tmp`。
- 同日重复运行：四张候选表、`candidates.json`、`dedupe-manifest.csv`、`failures.csv`
  与 `daily/YYYY-MM-DD.txt` 逐字节一致。
- 队列差分：`queue-latest` 写入前先把上一版另存为 `queue-prev`，再写 `queue-diff`
  （`added` / `removed` / `unchanged_count`）。第二次同日运行的 diff 应为 0/0。

## 9. Fixture 客户端

正常运行使用 `HttpFetcher`：对配置中的公开 URL 做无登录 GET，支持 fixture-shaped
JSON、RSS/Atom 和普通 HTML 列表/文章页；只跟随同站公开文章链接，默认查看运行日前
14 天、每端点最多 20 个条目。动态站点、登录墙、反爬或无法解析的页面会成为显式
`fetch_failure`，不会伪装成“无更新”，也不会绕过访问限制。

`FixtureFetcher` 读 `<fixtures>/<endpoint_id>.json`，实现相同的 `fetch(endpoint)` 接口，
供断网演练、CI 与测试使用。

`calls/fixtures/daily_discovery/` 覆盖的场景（运行日期固定 `2026-09-01`）：

| fixture | 场景 |
| --- | --- |
| `AAOI_IR_RELEASES` | 第一方产品公告 + 同源转载 + 同 URL 重复 + 同内容（不同 URL）重复 |
| `LITE_IR_RELEASES` | 第一方正式公告，与对手方材料构成 corroborated 建议 |
| `LITE_TECH_BLOG` | 技术演示（合法）+ 越界推导量产（被 `permission_denied` 拦截） |
| `CSCO_IR_RELEASES` | 具名对手方独立披露；另有一条同时点名两家公司 → 低置信度映射 |
| `MTSI_IR_RELEASES` | 未来交付承诺 → 降级为 forward-looking |
| `IQE_RNS_RELEASES` | 只有对手方证据的事件仍为 asserted；另有一条未解析实体 |
| `HAMAMATSU_IR_RELEASES` | 抓取失败（HTTP 504）显式入队 |
| `POET_IR_RELEASES` | 无相关内容、非法条目、发布日期晚于运行日期 |

## 10. 人工过闸流程（staging → 账本）

1. 看 `daily/YYYY-MM-DD.txt` 与 `failures.csv`：先处理未解析实体、低置信度映射和
   抓取失败，这些不会自动消失。
2. 打开 `candidates.json`，逐条检查 `claim_candidates` 的 `quote`/`anchor` 是否
   真在原页面、说话人与事实/前瞻属性是否正确。
3. 逐条核锚无误后，由人工把主张改成 `anchor_reviewed` 并写入 `calls/event_claims.csv`
   与对应的 `disclosures.csv`（`processing_status=anchor_reviewed`）。
4. 事件只以 `asserted` 入账；只有当 `candidates.json` 里
   `suggested_event_status=corroborated` 且人工确认存在不同 origin 的独立证据时，
   才升为 `corroborated`。
5. `corroboration_suggestion_pending_approval` 队列项必须逐条人工处理，
   不接受批量批准。
6. 新主体先走 `company_candidates.csv` 与晋级闸门，不因“日更发现过”而直接进池。

本模块**不做** promote：没有把 staging 行写回 `calls/*.csv` 的代码路径，
`verify` 是只读的。

## 11. 测试

`calls/tests/test_daily_discovery.py` 覆盖：监控池并集、别名与身份解析、配置拒绝
泛新闻与非法端点、URL/hash/origin 去重、第一方不独立、corroborated 仅为建议、
技术博客权限、forward-looking 边界、失败显式化、锁与原子写、同日幂等，以及
“运行前后 `calls/*.csv`、`calls/out/`、根 canonical 字节不变”。

```bash
python3 -m unittest discover -s calls/tests -v
python3 -m calls check
```
