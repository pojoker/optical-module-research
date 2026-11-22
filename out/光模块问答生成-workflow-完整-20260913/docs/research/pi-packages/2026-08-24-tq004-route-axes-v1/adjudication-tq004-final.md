# TQ004 attempt-2 Codex 最终裁决

流程结论：`process_pass`
内容结论：`usable_draft_with_one_contract_erratum`
知识库动作：无；TQ004 不改变状态

## 通过

- 四个大方向已规范化为链路/接口画像、电信号处理架构、光子实现嵌套字段、封装/放置架构；
- EML 与 SiPh 已按器件实现和集成平台分层；
- LPO 已拆成 `linear + pluggable + LPO MSA profile` 的复合 alias；
- “低 BER 实现”未被冒充为电架构；
- CPO 未被绑定到单一电架构；
- 跨轴结论只限已观察组合；
- 14 条唯一 draft ID，全部 `would_mark_covered: false`，无新问题 ID。

## 合同有效勘误

基础合同 §3.3 中“解释为什么 `pluggable/CPO` 不能放在同一维度横向排名”是错误要求，改读为：

- `pluggable / NPO / CPO` 可以在 TQ008 的广义放置/封装轴上比较；
- `OSFP / QSFP-DD` 是 pluggable 之下的具体 form factor，不能与 CPO 作同粒度枚举；
- `LPO / CPO` 不能直接比较，是因为 LPO 是 `linear + pluggable + interface profile` 的复合标签，
  必须先拆出其中 `packaging=pluggable`，再与 `packaging=CPO` 比较。

因此 raw 中“pluggable vs CPO 粒度错层”改读为“OSFP/QSFP-DD vs CPO 粒度错层；
pluggable vs CPO 是同一广义放置轴上的比较”。

## 停止状态

- canonical write：false
- coverage change：false
- new question IDs：false

下一批不得单独消费 raw，统一先读 `post-adjudication-effective-text.md`。

## 外部审阅后补充裁决

- LPO 泛称只拆为 `linear + pluggable`；`100G-DR-LPO Revision 1.0（下载文件名含 v1p2）`
  是本轮冻结的具名 profile 实例，不是 LPO 全称定义。
- TQ008 分开 `other on-board` 与 `near-package NPO`；NPO 定义必须锚定 OIF 文档。
- TQ005 记录光 PMD/media/reach 等链路边界，TQ006 记录 host-module 电信号与处理职责；
  MSA profile 只作 alias/reference object，不双计为轴值。
- 规范不规定内部实现属于边界证据，不得称作已观察出货组合。
- raw 不改写，废止句由 `raw-output-tq004-attempt2.errata.md` 统一标注。
