# WQ001 冻结桥接来源包

只允许消费以下两份最终草案、裁决及其冻结一手来源：

- `raw-output-pq002-attempt3.md` + `adjudication-pq002-final.md`
- `raw-output-tq002-attempt3.md` + `adjudication-tq002-final.md`

## 可桥接候选

### B1 带宽需求 → host/media lane 与接口容量约束

- route-side：TQ002-a3-d01/d04，IEEE 802.3df x8 与单产品 8×100G PAM4。
- physical-side：PQ002-a3-d01/d04/d05，Host/Media Interface 方向与逐 lane 电/光收发实例。
- 可写：更高 aggregate rate 在本轮实例中落实为 lane 数、lane 速率、Host/Media interface
  capacity 的组合约束。
- 不可写：普遍必须增加 lane；x8 必然优于 x4；必选某光子平台。

### B2 距离/连接位置 → media 与 optical-budget 约束

- route-side：TQ002-a3-d02，reach 必须与介质/PMD 联合定义。
- physical-side：PQ002-a3-d07；OIF §7.3.4 说明 mid-board optical connector 增加 optical
  budget，TX 侧可能需提高 transmit power，RX 侧可能需改善 sensitivity 或减少 margin。
- 可写：距离和连接器路径要求会转化为介质、插损、发射功率/接收灵敏度等可验证约束。
- 不可写：某 reach 必须采用某器件；connector 数直接决定路线。

### B3 功耗约束 → module/host power 与 thermal-validation 边界

- route-side：TQ002-a3-d03/d05，form-factor power class 与 CPO power-savings target 分层。
- physical-side：OSFP Rev 5.22 §15.8；PQ001 的 module/host 条件边界。
- 可写：功耗上限在 OSFP 实例中变成 module power class、host enable 与系统级 thermal
  design/validation；CPO 只提供缩短电通道以降低损耗的 framework 机制目标。
- 不可写：CPO 实测一定更低功耗；power class 等于产品实际功耗。

### B4 密度需求 → port configuration 与 physical footprint 约束

- route-side：TQ002-a3-d06，port lane flexibility 与 substrate footprint 是两层输入。
- physical-side：OIF §7.2.1/Table 4，engine size、retention mechanism、solder/socket 占位/返工。
- 可写：密度要求会进入端口配置与封装占位/retention 的物理设计约束。
- 不可写：换算 ports/RU；由密度直接选定 solder/socket 或 CPO。

### B5 维护需求 → removability/rework/access 约束

- route-side：TQ002-a3-d08，hot-pluggable fact 与 lifecycle-cost gap 分层。
- physical-side：Coherent hot-pluggable OSFP；OIF Table 4 的 solder reflow limited rework/yield
  loss 与 socket rework/field access 限制。
- 可写：维护需求可映射到是否可热插拔、是否可返工、现场 access 等物理属性。
- 不可写：hot-plug 必然降低成本；所有 CPO 不可维护。

## 本轮禁止桥接

- 成本金额：只有维度，没有足够物理量化机制与公开金额；保持 unbridged。
- 公司/路线：不得从任一桥直接跳到 EML/SiPh/LPO/CPO 或公司群。
- 未完成问题：PQ009 尚无本轮独立研究稿，只能把 optical-budget 指标标为待 PQ009 验证，
  不能宣称 PQ009 已回答。
