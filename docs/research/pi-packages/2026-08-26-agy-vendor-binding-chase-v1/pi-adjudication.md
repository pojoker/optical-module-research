# Pi 输出裁决

日期：2026-08-26
裁决：`PASS_WITH_LOCAL_FIXES`；仍为 draft-only。

## 接受

- 正确保留 demo、listed_product、shipment/customer_adoption 的阶段边界。
- 正确把四条证据分别挂到 TQ006–TQ009，并禁止 SiPh/LPO 语义扩展。
- 正确建议公司—路线关系复用既有 `route_service_evidence` 语义，但通过 `evidence_stage` 区分；阶段升级采用追加记录，不覆盖旧证据。
- 正确识别本轮只补到物理 raw 字段和路线观察层，WHY 仍为空。
- 正确选择芯速联两款 exact listings 作为下一轮最小受控检索起点，而不是直接拿不同厂商 demo 做优劣比较。

## 本地修正

1. `HSO6-800-LP-P8S` 与 `HSD2-800-LP-P8S` 只证明同一供应商下的两个精确公开产品；未证明属于同一正式 product family，也未证明内部实现完全相同。因此“同一族”“仅封装不同”改为“配对 exact listings；待验证其余实现是否相同”。
2. “唯一”只能解释为本轮四条证据中的样本内判断，不能推广到市场。
3. Q1 的上游需求/瓶颈应挂 `TQ002/TQ003 + WQ002`，不是只挂 WQ002。
4. Q6 从路线架构到组件/工艺/能力要求，应挂 `TQ010/TQ011 + WQ003`，不是只挂 TQ006。
5. Q8 的公司阶段证据缺口应挂 `TQ013 + WQ004`；不得笼统占用全部 WHY。
6. 第四部分 8 条均为现有问题合同的 `research_note/refinement`，不新建 QID；“不重复”改读为“不是重复节点，但属于现有问题的细化”。

## 下一轮最小闭环（经裁决）

对象：芯速联两款 800G DR8 LPO SiPh exact listings，先补“除 form factor/connector 外是否同条件”的证据，不预设只差封装。

顺序：

1. TQ002/TQ003：目标应用、SerDes、reach、链路预算、温度与功耗约束；
2. TQ006–TQ009：核对两个型号的电架构、平台、封装和同实例字段；
3. TQ014：只有相同条件被证实时，才研究连接器/封装的条件化优势与代价；否则输出 `not_comparable`；
4. TQ010/TQ011 + WQ003/WQ004：把可证实差异映射到物理变化和公司角色证据；
5. TQ013：另搜 shipment/customer adoption，仍不创建 confirmed group。

## 禁止晋升

- 不写 canonical、coverage、WHY、正式 RP 或公司群。
- 不把产品页面营销语句变成优势。
- 不把 demo/listed_product 变成量产、出货或客户采用。
