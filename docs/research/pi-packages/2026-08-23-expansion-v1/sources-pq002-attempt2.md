# PQ002 attempt-2 来源补充

完整继承 `sources-pq002.md`。唯一新增上下文来自同一冻结 P3：

## P3 补充：OIF Co-Packaging Framework §7.3.2–§7.3.4（印刷页 20–21）

- optical/electrical engine 可 assembled with pigtail 或 built-in connector，把高速数据带入/带出
  engine；pigtail 可为高密度光接口 ribbon fiber，或高密度电接口 copper cable assembly。
- connectorized engine 需要额外 connector 到 front panel；pigtail 足够长时可不需要额外
  connector。额外 connector 会增加 insertion loss。
- `CPO Pigtail + jumper` 可包含 mid-board optical connector；该 connector 会增加 optical
  budget，但有助于减少 pigtail 搬运损伤，并可为 failing optical connectors/components 提供返工点。
- 此补充可支持：CPO framework 的 media-side pigtail/connector 实例与 optical-budget 权衡。
- 不可支持：所有 CPO 使用同一 connector；service cost；engine-to-substrate attach 属
  Media Interface。

组合禁令：P3 §7.2.1 Table 4 只属于 engine-to-substrate 封装/返工，不进入 Media Interface 行。
