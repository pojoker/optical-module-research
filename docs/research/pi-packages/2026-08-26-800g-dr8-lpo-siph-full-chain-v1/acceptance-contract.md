# 800G DR8 LPO SiPh 完整路线链验收合同

目标链：

```text
上游场景需求/约束
→ 当前物理或工程瓶颈
→ 800G DR8 LPO SiPh 路线选择
→ 相对 800G DR8 retimed 基线的条件化优势与代价
→ 组件/接口/工序/设备/测试责任变化
→ 所需物理能力
→ 公司候选能力与路线级直接证据阶段
```

## 必须满足

1. 路线目标与比较基线都必须明确；没有同条件基线时，允许部分 `not_comparable`，禁止虚构总排名。
2. 上游原因至少覆盖：800G aggregate、host/media lane、reach、BER/FEC、功耗/热、通道损耗或链路预算。
3. 每条优势/代价都必须有 conditions、evidence stage、source anchor；公司营销语只标 company-stated。
4. 下游至少逐项检查组件、接口、工序、设备、测试五层；没有直接证据的变化保持 UNKNOWN 或 engineering-inference。
5. 公司服务至少区分 demo、listed_product、shipment、customer_adoption；不得由产品页面推客户或量产。
6. WHY 只在机制和两端事实均有证据时形成 draft candidate；本轮不写 `why_links`。
7. 不创建新 QID；所有研究问题挂现有 TQ002–TQ014、WQ001–WQ004。

## 完整链最低可交付状态

- `route_chain_card.md` 中每一段都有状态：supported / company-stated / engineering-inference / unknown / not-comparable；
- 至少一条从上游约束到路线选择的候选 WHY；
- 至少一条从路线选择到物理变化的候选 WHY；
- 至少一条从物理能力到公司证据阶段的候选 WHY；
- 公司的 evidence stage 不越级；
- Kimi 与 Cursor 只读审核无 P0。
