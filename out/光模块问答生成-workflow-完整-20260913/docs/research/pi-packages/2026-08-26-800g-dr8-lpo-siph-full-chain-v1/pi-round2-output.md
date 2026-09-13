# Pi Round 2 结构审核

- 模型：`opencode-go/deepseek-v4-flash`
- thinking：high
- 模式：no-tools / no-session
- verdict：无 P0；结构闭合，P1/P2 修复后复核。

## 主要结论

1. 正交轴结构比 `800G → LPO → SiPh → 公司` 单线更准确：LPO/retimed 是电职责，SiPh/EML/TFLN 属光子实现字段，front-panel pluggable 属放置/封装。
2. `conditional_platform_selection_hypothesis` 可保留为 engineering-inference，但 target 是否真的优先 PIC 集成、wafer test/burn-in/KGD 未验证。
3. 唯一晋升路径是同条件 800G DR8 LPO SiPh vs EML/TFLN 受控比较；更多 listing、组件页或平台陈述不能升级 WHY。
4. 必须保持 UNKNOWN：热、工序 delta、生产设备 delta、Hyper 内部 SiPh 结构、Dust/Credo 或 MACOM 进入 Hyper 的关系、shipment/customer adoption、功耗/时延/成本幅度。

## 修复已应用

- 将功耗机制与 S5/S6 产品包络观察拆成两行；后者为 `not-comparable`。
- 为 SiPh 条件假设增加 target 前提未验证和唯一晋升路径护栏。
- 将规范测试责任与 multi-vendor demo 观察分开。
- WQ003 明确只支持组件/接口/测试责任子链，工序设备仍 UNKNOWN。

有效状态建议：`complete_multi_axis_route_chain_draft_with_explicit_unknowns`。
