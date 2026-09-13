# 海外事件雷达日更镜像契约（CodeBuddy / hy4-preview 工包）

## 目标

给现有 `calls/` 增加“每日发现与候选入队”能力。它不是 SEC、央行或 RSS 泛新闻流；产品模型必须保持 `披露件 → 原子主张 → 公司事件 → 事件证据`，并严格遵守现有人工判定闸和证据独立性。

## 只读输入与监控范围

- 读取 `calls/universe.csv` 中启用公司、`calls/watch_entities.csv` 中 active 实体，以及尚未晋级的 `company_candidates.csv`。
- 读取 `entity_relationships.csv` 做品牌、并购和前身去重。
- 读取现有 `disclosures.csv`、`event_claims.csv`、`events.csv`、`event_evidence.csv` 做 URL/hash/origin 去重。
- 来源只允许公司 IR/官网、监管/交易所、具名客户或交易对手、政府记录等可追溯公开页面；不得把宏观泛新闻源当产品主体，不绕过登录或付费墙。

## 候选输出与权限

1. 所有自动发现只写独立 `state_root`，绝不直接改 `calls/*.csv`、`calls/out/` 或根 canonical。
2. 输出 schema-shaped staging CSV/JSON，至少覆盖 disclosure candidate、atomic claim candidate、event candidate、evidence candidate，并保留 canonical URL、发布时间、抓取时间、content hash、origin group、锚点和来源类型。
3. 自动主张只能是 `candidate`；不得写 `anchor_reviewed`。自动事件默认至多建议 `asserted`，不得直接写正式事件状态。
4. 第一方公告不能作为独立证据；同一底层公告的转载必须归入同一 origin group。只有 `counterparty | regulator | observable_result` 且 origin 不同的证据，才可在候选中提出 `corroborated` 建议，仍须人工批准。
5. 技术博客/演示不得推导量产、客户采用、订单规模、供货关系或需求规模。forward-looking 不得写成已兑现。
6. 未解析实体、低置信度映射、冲突、抓取失败和无相关内容必须显式留在队列/日志，不能静默删除。

## 接口与运行产物

- 提供可测试 CLI，建议：`python3 -m calls.daily_discovery run --source-root <repo> --state-root <dir> --date YYYY-MM-DD --config <file>`。
- 配置按 entity 指定官方/监管 discovery endpoints；不能拿无关通用 feed 替代公司覆盖。
- 产出 `daily/YYYY-MM-DD.txt`、候选 CSV/JSON、去重 manifest、失败日志、`queue-latest`/`queue-prev` 差分。
- 同日重复运行幂等，采用锁、临时文件、原子替换；网络可 fixture 化。
- 提供只读验证命令，证明 staging 可映射到现有 schema，但绝不自动 promote。
- 不安装 cron，不修改当前调度。

## 验收

1. 测试覆盖监控池并集、实体别名解析、URL/hash/origin 去重、第一方不可 corroborate、不同 origin 的独立证据仅生成建议、技术博客权限、forward-looking 边界、失败显式化、锁和原子写。
2. 测试证明运行前后 `calls/*.csv`、`calls/out/` 和根 canonical 字节不变。
3. fixture 至少包含：第一方产品公告、同源转载、具名对手方独立披露、技术演示、未来交付承诺；重复运行输出确定。
4. `python3 -m calls check` 与 `python3 -m unittest discover -s calls/tests -v` 继续通过。
5. README 逐项说明它如何映射现有事件账本与人工过闸流程。

使用 CodeBuddy 模型 `hy4-preview` 完成，运行测试并提交到当前分支；不要改动别的工作树，不要安装或启动定时任务。
