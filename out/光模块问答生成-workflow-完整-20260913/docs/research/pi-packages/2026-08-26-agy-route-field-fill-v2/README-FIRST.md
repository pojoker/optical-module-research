# READ FIRST

本包是 AGY 3.7 Flash 来源搜索与 Pi 安全消费小样，状态为 draft-only。

## 唯一有效消费顺序

1. `run.yaml`
2. `adjudication.md`
3. `source-excerpts.md`
4. `pi-adjudication.md`
5. `pi-output.md`（只消费结构；其中页码 UNKNOWN 和 4 条均不重复的原始判断已被裁决修正）

## 禁止直接消费

- `agy-eml-recheck-output.md`
- `agy-siph-retry-output.md`
- `pilot-v1-audit.md` 中转述的首轮 AGY 合成内容

AGY raw 仅用于审计搜索行为，内含未获裁决的解释性文字。任何字段事实必须回到 `source-excerpts.md`；任何结构判断必须服从 `pi-adjudication.md`。

## 当前有效结果

- EML：产品系列级 observed seed，可用来源锚见 `source-excerpts.md`；不是 exact orderable SKU，不证明 GA/量产。
- SiPh：本轮未找到合格 exact-SKU platform binding；这是搜索结果，不是产业负向事实。
- 新增研究注记：仅 `TQ009-note-evidence-subject` 一条；另三条并入既有 TQ009/TQ013/TQ014 合同。
- canonical、coverage、WHY、公司群、正式 Route Profile promotion：全部禁止。
