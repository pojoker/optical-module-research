# B 包交付报告（OpenCode Omen Alpha）— 海外 HTTP 与端点修复（最终版，实现已冻结）

- 日期：2026-09-05
- 基线：d413037（codex/daily-overseas-20260905 worktree）
- 状态：实现冻结。经两轮主代理复核修正后定格；改动全部在工作区/暂存区，
  本地 commit 被 worktree 语料饥饿钩子阻塞，由主代理整合（未使用 --no-verify）。
- 范围：calls/http_discovery.py、calls/daily_discovery.py、calls/discovery_config.json、
  calls/tests/test_http_discovery.py、calls/tests/test_daily_discovery.py、本报告。
  未触碰 canonical、calls/*.csv、fixtures、A/C 包文件。

## 提交

无本地提交（钩子阻塞见上）。暂存区 diff 即交付物，主代理负责整合提交与隔离全套验证。

## 行为变化（最终实现）

1. **详情失败可追踪**：`HttpFetchResult` 新增 `article_failures`（逐篇文章 URL + 原因）；
   `_get` 失败不再被 `except: continue` 静默吞掉。`daily_discovery` 以
   `article_fetch_failure` 入 failures.csv 与队列；`run-summary.json` 新增
   `endpoint_succeeded`（真实成功端点数，configured 不冒充成功）。端点级失败
   仍走 `failure` 字段；`unsupported_listing` 作为独立 failure_type 分列。
   旧结果形状（FixtureFetcher 无该字段）兼容。
2. **发布日期归属（严格绑定，无唯一性/邻域捷径）**，按序：
   - meta 日期键；
   - `<time>`：行情/更新类 class（price/share/ticker/market/quote/stock/update/modified/
     revision）一律排除，**对带时刻与裸日期一视同仁**——时间精度不证明归属
     （stock-update 全时间戳、IQE 股价挂件均拒收；无 market 痕迹的主文 `<time>` 合法）；
   - JSON-LD：仅认 @type 为文章类型的节点；只有块根/顶层列表/`@graph` 成员/顶层
     `mainEntity` 位置的节点算显式主节点（无定位字段可接受）；嵌套在 related/author
     等属性下的节点必须等值绑定，否则拒绝。有 URL 字段只认 URL 等值，明示 URL
     不匹配禁止标题兜底；无 URL 时标题等值（去 "| 站点后缀" 后规范化全等）；
   - 嵌入 JSON（field_date 等）：逐匹配解析其所属最内层 JSON 对象，仅用对象**顶层
     自标识字段**等值绑定（url/path.alias/@id/slug 与 canonical 等值，含单段语言
     前缀规范化；URL 存在但不匹配 → 拒绝，不用标题兜底）；无任何自标识字段
     （无法识别的 Drupal/嵌入结构）一律不绑定；多个绑定不唯一 → 留空；
   - class 含可信日期 token 的短元素（"Type--Date"、"blog-post-header2_date"；
     update/modified/market 类 token 拒收），同名标签深度收完整文本；
   - 官方电头：整段锚定 "城市, 地区 日期"（≤120 字符、前 8 段内）。
   - **无全文首日期兜底**；无可信日期留空，由下游 invalid_item 拒收并报告。
3. **文章链接过滤（按具体形态，不再 blanket）**：同域基础上排除 FAQ/alerts/SEC/
   索引/IR 子树（investor-relations、financial-information）/events 子树/附件；
   分页与筛选 query（page=、pt=、sort= 等）拒绝；**带文章 ID 的 query
   （articleId=、p= 等）与 Q4 真实文章路径（news-details/.../default.aspx）保留**；
   非 blog 端点跳过 `/blog/` 文章，防博客冒充官方公告披露类型；列表页自身仅在
   无任何文章链接时入候选，防列表页页面级 meta 日期被当作文章日期。
4. **JS 渲染列表显式 unsupported**：不做数量阈值猜测。结构性零（静态 HTML 无任何
   可解析文章链接且页面非日期化文章）如实报 `unsupported_listing`；
   **CSCO、AAOI 两个已证实端点在 discovery_config.json 显式标记
   `unsupported_listing: true`**，fetcher 直接返回显式失败，不冒充健康零增量。
5. **段落解析修复**：未闭合 `<p>`（IQE 压缩 HTML）按下一段切分；收尾 flush 最后一段。
6. **端点核验修正**（全部经真实 GET 验证，2026-09-05）：
   - MTSI：investors.macom.com TLS 失败 → `https://ir.macom.com/news-releases`（200，静态文章链接）
   - POET：investors.poet-technologies.com TLS 失败 → `https://www.poet-technologies.com/news-media`（200）
   - IQE：`/media/press-releases/2026` 404 → `https://www.iqep.com/media/press-releases`（200）
   - Hamamatsu：`/jp/en/newsroom.html` 404 → `https://www.hamamatsu.com/jp/en/news.html`（200，静态公告链接）
   - Cisco：`/a/y2026/m09` 404 → `https://newsroom.cisco.com/c/r/newsroom/en/us/index.html`（已证实 JS 渲染，显式 unsupported）
   - AAOI：URL 保持，已证实 JS 渲染列表且本客户端响应超时，显式 unsupported

## 测试

- 定向：`python3 -m unittest calls.tests.test_http_discovery calls.tests.test_daily_discovery`
  → **89 tests OK**。
- 全套：`python3 -m unittest discover -s calls/tests -t .` → **200 tests OK**
  （其余 111 个为既有 calls 测试，确认无跨模块回归）。
- 本包新增回归覆盖：IQE 股价挂件与 stock-update 全时间戳反例、主文裸日期 `<time>`
  正例、update 类 class 拒收、related 在前/URL 等值绑定、唯一相关节点不同 URL、
  短 URL 前缀不绑定、对象含主标题但自有 URL 明示不匹配、无法识别结构留空、
  JSON-LD typed primary（无定位可接受）/嵌套 related 无定位拒绝/嵌套绑定正例、
  作者节点日期拒收、Q4 news-details/default.aspx 与文章 ID query 保留、FAQ/分页
  拒绝、配置 unsupported 显式失败、article_fetch_failure 入账与旧形状兼容、
  未闭合段落。

## 真实网络核验（fetcher 级只读 GET，run_date=2026-09-05，未写任何 staging）

- POET：1 条在窗口（CIOE 2026-09-04）+ 4 条 404/1 条 SSL 死链逐条入 article_fetch_failure
- IQE：1 条在窗口（2026-09-03，电头）；1 条详情失败保留（share-price-tools 无正文）
- LITE_TECH_BLOG：1 条在窗口文章；日期经 Drupal 节点对象 path.alias 等值绑定
- MTSI：8/6 财报窗外 → 0 条为真实空，端点健康
- Hamamatsu：公告日期 class 元素解析正确；14 天窗口内无新公告 → 0 条为真实空
- LITE_IR_RELEASES：结构性 `unsupported_listing` 显式失败
- CSCO / AAOI：配置显式 `unsupported_listing`，不再出现"端点健康但 0 条"

## UNKNOWN / 剩余解析启发式限制

1. **CSCO / AAOOI 静态入口**：本客户端尚未找到可用静态采集入口（newsroom/rss-feeds
   页与 Q4 列表均为 JS 渲染）。不据此断言官网没有 feed；如后续发现官方静态源，
   更新 URL 并移除 `unsupported_listing` 标记即可。
2. **LITE 博客日期绑定覆盖不全**： Drupal 节点对象提取用括号平衡扫描，不解析字符串
   字面量；个别文章页（实测 featured 文章）对象无法闭合时按"无法识别结构"留空报
   invalid_item，不猜日期。能否 100% 覆盖待后续按真实页面结构增强提取器。
3. **嵌入 JSON 单节点不豁免绑定**：field_date 唯一出现也必须等值绑定；绑定失败即
   留空。真实站点若换排版导致 alias/标题不匹配，将诚实降级为 invalid_item。
4. **IQE 电头启发式**：IQE 文章无结构化日期字段，发布日期依赖整段锚定电头规则
   （≤120 字符、前 8 段内）；对官网未来排版变化无保证。
5. **class 日期 token 清单**：可信 token（date/field_date/*-date/*_date/publish*）与
   排除词（price/share/ticker/market/quote/stock/update/modified/revision）为具体
   形态清单，遇新形态需按证据扩充。
6. **提交钩子阻塞**：corpus 饥饿，主代理处理。

## 范围外发现（不实现）

- `calls/out`、canonical、fixtures 未动；14 天 lookback 窗口是否合适属产品决策。
- JS 渲染列表如需长期采集，由主代理决定是否引入官方静态源；本包未新增任何架构。

## 冻结

实现与测试均已定格于上述状态；后续由主代理整合、跑隔离全套并提交。本包不再改动。

### 最终冻结对表（2026-09-05，主代理复核后的最终版本）

说明：主代理抽验后，本 worker 曾在并发尾部做过一次 `_enclosing_json_object`
字符串感知尝试并已完整回退；**当前文件即最终冻结版本**（恢复为经主代理验证、
200 全套通过的括号平衡版）。自此不再有任何源码/测试编辑。

最终文件 SHA256：

```
500a7c2f713c880d3829f23dccb385a9680bb5b112fa825c7dce53d45c650ac2  calls/http_discovery.py
fd8e56389ea03abbf89136116cfe59b32608b2dd7a089f3ae0ac9a7a0ed3d6e1  calls/daily_discovery.py
63d5beda1b2a5eb44ab6e9d9142b3e8c2a468cc72083ac2f5dc8b2952ec9ffff  calls/discovery_config.json
42cb59085364e58669b3eef044aa6949fd4de89ac61c82f3756a86179821f88f  calls/tests/test_http_discovery.py
f36567905672e8e7ad48adf96dbdd1f75b57a53bbb70415968385c656872a7ed  calls/tests/test_daily_discovery.py
```

最终定向复跑（冻结版本）：

```
python3 -m unittest calls.tests.test_http_discovery calls.tests.test_daily_discovery
Ran 89 tests in 0.258s
OK
```

配套只读产物（fixture 全套）继续全绿：candidates/verify 输出与既有 200 全套
`unittest discover -s calls/tests -t .` → OK。以上即最终交付对表，主代理可按此 SHA256 校验整合。
