# Pi CodeBuddy 开发委托：研究问题树 v2

```
状态: 可开发
日期: 2026-08-23
模型: 必须 hy3
上游方案: docs/plans/2026-08-research-question-tree-v2.md
架构决策: docs/adr/0009-separate-physical-route-knowledge-with-why-links.md
```

## 0. 直接指令

请用 **hy3 模型**在当前工作区实现“研究问题树 v2”。你是本轮代码和数据结构变更的唯一写者；
其他模型只做只读评审。先完整阅读：

1. `CLAUDE.md`
2. `CONTEXT.md` 新增的“研究问题与路线能力”术语
3. ADR-0009
4. 上游方案全文
5. `render.py`、`scan.py`、`tree.yaml`、`knowledge.yaml`、`route_bom.csv`、`points.csv`
6. 现有问题队列方案与交接中关于单一事实源、YAML 回填、确定性渲染的边界

所有 Python 命令必须使用 `/Users/jowang/miniconda3/bin/python3`；禁止用系统 `python3` 报告 yaml
模块失败。不要读取 `archive/`，不要改无关 dirty 文件，不要 commit/push/stash/reset/clean，不要手改
`out/`。事实内容不得取自聊天；本轮只实现问题坐标、回填合同、校验和派生视图。

## 1. 必须交付

- 新建 `research_questions.yaml`，写入方案 §5 的 25 个树问题和 4 个 Why 桥问题。
- `knowledge.yaml` 增加空的兼容顶层 `why_links: []`；现有 KN 内容、ID、顺序不迁移。
- `render.py` 生成 `out/研究问题树.md`，保留现有全部输出和问题队列行为。
- `scan.py` 增加不变量⑭及相应 `--selftest`。
- 根目录白名单纳入 `research_questions.yaml`。
- `render.py --verify` 纳入 `研究问题树.md`。
- `README.md` 增加一段主入口说明：研究问题树 vs 维护问题队列，Python 示例用 Miniconda 完整路径。

## 2. 实现边界

### 2.1 `research_questions.yaml`

字段至少为：

- `meta.version/root_id/answer_target`
- `questions[]`: `id,parent_id,system,order,question,writeback,acceptance`
- `why_questions[]`: `id,order,route_question_ids,physical_question_ids,relation_type,question,writeback,acceptance`

问题文案和父子关系以方案 §5.1–§5.3 为准，不自行新增 EML/CPO/POET 等事实型叶子问题。

建议 ID 规则：`RQ000`、`PQ001..010`、`TQ001..014`、`WQ001..004`。`system` 只允许
`root/physical/route`；WQ 不进 parent 树。

### 2.2 `knowledge.yaml`

兼容读取：旧 KN 无 `体系` 时视为物理知识，无 `研究问题` 时不计问题覆盖。

新字段的校验合同严格按上游 §6：

- `体系`: `物理知识|技术路线`
- `研究问题`: RQ/PQ/TQ 引用
- `路线条目`: RB 引用
- `关联点`: P 引用
- 顶层 `why_links`: WHY 记录

不要为了展示覆盖而猜测旧 KN 对应哪个问题，也不要给旧 KN 批量补字段。

### 2.3 路线公司群

对每个 `route_bom.csv.产品路线`：

- 候选能力群 = 路线全部 mapped `cell_ids` 对应的 points，公司按格分组、组内去重排序。
- 确认服务群 = 技术路线 KN 的 `路线条目` 命中该产品路线任一 RB，且 `关联点` 指向真实 point；
  按公司去重并显示支撑 KN。
- 候选群标题和说明必须含“能力匹配，不是路线采用/供货证据”。
- 确认群无数据时逐字显示“尚无路线级直接证据条目”，不能把候选群顶上去。
- 800G/1.6T 候选格集合相同时，显式提示当前物理映射无法区分路线。

### 2.4 Why 链

按上游 §6.2 实现并校验。重点：

- WQ 只表示跨体系关系，不挂进第三主干。
- 每一步独立标主张类型与 KN/RB 证据引用。
- 条件、取舍、替代方案都不能为空列表。
- 不允许 `Investment` 越过 `CommercialAdoption` 和 `Economics`。
- 首版 `why_links` 为空是允许状态；页面显示 4 个待研究桥问题和“尚无已验证 Why 关联”。

## 3. 页面合同

`out/研究问题树.md` 必须按上游 §8 顺序稳定输出。树至少让用户直接看到：

```text
RQ000 什么是光模块？
├─ 物理知识体系
│  └─ 功能 → 参考样机 → 组件 → 接口 → 制造 → 设备
└─ 技术路线体系
   └─ 需求/约束 → 瓶颈 → 正交轴 → 路线画像 → 能力 → 公司能力群

Why 桥：需求/瓶颈 → 工程选择 → 物理变化 → 公司能力
```

每个问题显示 `[待研究]` 或 `[已覆盖: KN...]`；WQ 显示 WHY ID。实时基线从当前文件重算，
不写死数量或日期。页面尾部提供三段可复制 YAML 模板，但模板不得冒充答案。

## 4. 不变量⑭

实现一个可被真实校验和 selftest 复用的纯校验函数，错误统一 `fail('⑭', ...)`。至少覆盖：

1. 问题文件存在且可解析。
2. 唯一根 RQ000，ID/parent/order/体系合法，父引用闭合、无环。
3. PQ 只能处于 physical 分支，TQ 只能处于 route 分支。
4. WQ ID 唯一，路线侧仅 TQ，物理侧仅 PQ，引用均闭合。
5. KN 新字段类型与引用闭合；旧 KN 兼容。
6. 技术路线 KN 至少一个真实 RB；物理 KN 不得引用 TQ，路线 KN 不得引用 PQ。
7. `关联点` 只允许真实 P ID。
8. WHY 的 ID/WQ/RB/cell/证据引用闭合。
9. 因果链至少两步、顺序从 1 连续、枚举合法、文本和证据非空。
10. 条件/取舍/替代方案均为非空列表；Investment 顺序闸。

不得放宽现有不变量①–⑬。

## 5. 自测与真实验收

### `scan.py --selftest`

保留现有 33 个用例全绿，并新增至少 10 个⑭用例：正例、重复 ID、悬空 parent、环、WQ 跨侧、
KN 跨体系、悬空 RB、悬空 point、WHY 步骤乱序、空三项、Investment 越级。

### 真实工作区

按顺序执行：

```bash
/Users/jowang/miniconda3/bin/python3 scan.py --selftest
/Users/jowang/miniconda3/bin/python3 scan.py --check
/Users/jowang/miniconda3/bin/python3 render.py
/Users/jowang/miniconda3/bin/python3 render.py --verify
```

再计算两次 `out/研究问题树.md` SHA256，必须一致。

### 临时副本闭环

不得改真实 canonical 数据。复制最小工作区到临时目录后证明：

1. 追加物理 KN（关联 PQ004）后 PQ004 变已覆盖。
2. 追加路线 KN（关联 TQ013、至少一个 RB、至少一个 P）后确认群出现公司。
3. 追加 WHY（关联 WQ003）后 WQ003 变已覆盖并展示链。
4. 把任一引用改成不存在的 ID，`scan.py --check` 失败。

临时证据可使用已有真实 KN/RB/P 引用，不能伪造并写回真实库。

## 6. 交付回报

请报告：

- 改动文件清单与关键行为。
- 页面上的实时基线数字、问题数、候选/确认群口径。
- selftest 新旧用例数、check、verify、SHA256、临时闭环结果。
- 明确声明使用的模型是 `hy3`。
- 剩余限制，尤其是“产品路线框架尚不是完整路线画像”“候选能力群不等于路线服务/供货”。

不要提交 git commit；交付后停下，等待只读评审。
