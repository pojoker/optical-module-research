# PARKING LOT — 范围内发现但不实现

> 用途：执行当前工作包时发现的好想法，一律记在这里，**不实现、不设计、不写进工作包**。
> 记下就够；是否立项由用户裁决。
> 需要升级为架构时，必须先过 `PROJECT_CHARTER.md` 第 5 节的四闸，四闸全过才提交用户。

## 条目模板（每条不得超过一屏）

```yaml
- id: PL-###
  date: YYYY-MM-DD
  discovered_in: <工作包 ID 或触发场景>
  one_line: <一句话说清这个想法是什么>
  # 四闸自评（全部 yes 才允许提交用户裁决；任一 no 则留在本文件）
  gate_1_blocked_in_two_real_slices: yes|no   # 列出两个真实切片 ID
  gate_2_used_by_production_data: yes|no      # 指出已出现的真实数据字段
  gate_3_replaces_existing_step_or_impl: yes|no  # 指出替换哪个既存人工步骤/实现
  gate_4_necessary_for_reader_visible_conclusion: yes|no  # 指出缺它就不成立的读者结论
  verdict: parked                             # parked | escalated_to_user | rejected
```

## 已记录条目

```yaml
- id: PL-001
  date: 2026-09-03
  discovered_in: OM-PHYS-001（准备阶段，元认知反射）
  one_line: 让系统记录"自己是如何判断的"（元认知层：把每次判定依据、证据强度与不确定来源一并留痕）。
  gate_1_blocked_in_two_real_slices: no   # 尚未举出两个现有架构无法表达的真实领域切片
  gate_2_used_by_production_data: no      # canonical 中无对应字段
  gate_3_replaces_existing_step_or_impl: no  # 现有 triage.csv 备注与人工复核已承担该职责
  gate_4_necessary_for_reader_visible_conclusion: no  # 读者结论不依赖它
  verdict: parked
  why_parked: >
    听起来能提升可审计性，但当前判定依据已经写在 triage.csv 与审阅记录里；
    再造一层会制造第二套平行档案，正落入 PROJECT_CHARTER 第 3 节非目标。

- id: PL-002
  date: 2026-09-03
  discovered_in: OM-PHYS-001（准备阶段，问题状态机）
  one_line: 给研究问题加状态机，自动在"待研究 / 已有材料 / 已完成"之间流转。
  gate_1_blocked_in_two_real_slices: no
  gate_2_used_by_production_data: no      # research_questions.yaml 明确不保存自动状态
  gate_3_replaces_existing_step_or_impl: no
  gate_4_necessary_for_reader_visible_conclusion: no
  verdict: parked
  why_parked: >
    问题完成度是人工复核判断，不是机器可判属性。自动流转会把"已有材料"冒充为"已完成"，
    正是本轮要修的语义缺陷。禁止实现。

- id: PL-003
  date: 2026-09-03
  discovered_in: OM-PHYS-001（准备阶段，产品登记表）
  one_line: 建一张产品登记表，自动派生 offers_product / implements_route 关系。
  gate_1_blocked_in_two_real_slices: no
  gate_2_used_by_production_data: no
  gate_3_replaces_existing_step_or_impl: no
  gate_4_necessary_for_reader_visible_conclusion: no
  verdict: parked
  why_parked: >
    产品—路线归属需要路线级直接证据，自动派生会产生未经复核的关系主张；
    与 PROJECT_CHARTER 第 3 节"无产品登记表、无自动 offers_product/implements_route"直接冲突。

- id: PL-004
  date: 2026-09-03
  discovered_in: OM-PHYS-001（准备阶段，通用控制面）
  one_line: 抽象出通用 Agent Control Plane，统一管理工作包、回执、快照血统与取代关系。
  gate_1_blocked_in_two_real_slices: no
  gate_2_used_by_production_data: no
  gate_3_replaces_existing_step_or_impl: no  # 当前靠 AGENTS.md + 三份 control 文件人工控制即可
  gate_4_necessary_for_reader_visible_conclusion: no
  verdict: parked
  why_parked: >
    当前人工控制成本低于维护一套引擎的成本；本轮目标正是"不加工作流引擎"。
```

## 使用规则

1. 发现 → 按模板记一条，**停止**，回到工作包。
2. 不因为记了条目就顺手实现、设计或写方案文档。
3. 四闸全 `yes` 时，把条目交给用户裁决，并在条目里写 `verdict: escalated_to_user` 与日期。
4. 用户否决后写 `verdict: rejected` 并保留，避免同一想法反复被重新发现。
