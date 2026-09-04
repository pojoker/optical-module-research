# TQ009 最终裁决

## 结论

- process: `pass`
- evidence boundary: `pass`
- cross-instance isolation: `pass`
- atomic schema mechanics: `pass after round 2`
- semantic use: `usable draft with reviewer corrections`
- formal Route Profile promotion: `blocked`
- company capability matching: `blocked pending TQ010/TQ011`

第一轮正确生成五个实例种子，但有 7 个复合字段混合已知与 UNKNOWN。第二轮把每个种子拆为 35 个原子叶字段；
reviewer 进一步要求拆开名义波长与波长窗口，当前有效 schema 为 36 个叶字段。

## 人工语义修正

第二轮 raw 不直接作为有效数据，采用 `route-profile-seeds-effective.yaml` 的五类修正：

1. RPS-D01：`53.125 GBd` 只保留为 `symbol_rate`；`media_lane_rate` 改回 UNKNOWN，避免把符号率重复当作 bit/data lane rate；
2. RPS-D04：`MZM PIC` 只支持 device-in-PIC 组合标签；`pic_eic_integration` 改回 UNKNOWN，不能从 MZM PIC 推出 PIC/EIC 集成方式；
3. `placement_class` 由 observed form factor 通过冻结 TQ008 字典映射，状态改为 `normalized`；
4. `nominal_wavelength` 与 `wavelength_range` 分开，D01 保留 1310 nm 名义值和 1304.5–1317.5 nm 窗口；
5. D05 把来源短语保留为 `laser (raw instance phrase: EML laser)`，`modulator_or_emitter_type` 回退 UNKNOWN，
   不把 EML 假装拆成已知激光器结构和调制器结构。

## 当前证据完整度

这里只表示 36 个 schema 叶字段中有多少被同实例来源填充或受控规范化，不表示路线成熟度或优劣：

| Seed | 已观察/公司表述 | UNKNOWN | 证据字段完整度 |
|---|---:|---:|---:|
| RPS-D01 | 18 | 18 | 50.0% |
| RPS-D02 | 12 | 24 | 33.3% |
| RPS-D03 | 9 | 27 | 25.0% |
| RPS-D04 | 6 | 30 | 16.7% |
| RPS-D05 | 7 | 29 | 19.4% |

这证明“产品名 + 四个大轴文本”不足以直接形成正式 Route Profile；必须保留原子 UNKNOWN 和 promotion blocker。

## 公司挂载裁决

- 五个种子可以把 Coherent 记为精确产品/演示实例主体；
- 不能由此生成客户、供应商或“服务该路线”的其他公司；
- 不能将现有 83 家粗能力候选挂到 800G/1.6T 种子；
- 必须先完成 TQ010 物理变化和 TQ011 能力要求，才能进入 TQ012；
- `edges.csv` 不自动升级为路线服务证据。

## 有效文件

- 种子数据：`route-profile-seeds-effective.yaml`；
- 解释与下一步：`post-adjudication-effective-text.md`。

第一、二轮 raw 均只作审计。
