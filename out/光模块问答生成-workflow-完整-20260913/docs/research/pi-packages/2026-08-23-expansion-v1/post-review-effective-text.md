# 扩展小样 post-review 唯一有效口径

日期：2026-08-23
状态：`draft-only；未落库；外部审阅修订版`

## 1. 消费规则

本文件是下一批研究唯一必须先读取的 controlling text。三个 `raw-output-*.md` 仅保存 Pi 原始输出，
不得单独作为后续研究输入；发生冲突时，本文件覆盖 raw，三个 final adjudication 作为裁决记录。

本文件不改变 PQ002、TQ002、WQ001 的覆盖状态，不生成新问题 ID，不授权写入
`knowledge.yaml#why_links` 或其他 canonical 文件。

## 2. PQ002 有效修订

1. `PQ002-a3-d01` 的 statement 中，“唯一核心功能骨架”替换为“本轮采用的 CMIS 条件化接口骨架”。
2. `PQ002-a3-d02` 保留“本轮只写模块在 Host/Media 两接口之间的 bridge/forwarding”边界；
   rejected inference 的理由改为“本稿选择不延伸到远端模块行为”，不得写“CMIS 未描述远端概念”。
3. 原注记 2 按缺口性质拆分挂接，但不新增 QID：
   - `PQ005`：连接形态、连接器位置、是否存在返工点以及返工实现方式；
   - `PQ009`：connector insertion loss、optical budget、TX power、RX sensitivity、margin 等量值。
4. EML/PIN 仍只属于 Coherent FTCE4517E1PxM 单产品实例；EIC/OIC/PIC、solder/socket、pigtail
   仍只属于 OIF Co-Packaging framework 实例。

## 3. TQ002 有效修订

1. IEEE 802.3df-2024 日期改为：`Board Approval 2024-02-15`；`Published 2024-03-15`。
   raw 中的 `2024-02-16 获批` 作废。
2. `TQ002-a3-d08` 改读为：`hot-pluggable` 是产品/form-factor 能力；
   `hot-plug/hot-unplug` 是 OSFP §15.8 纳入处理的功耗瞬态事件；二者均不能直接证明维护成本下降。
3. “机架内/DC/园区”只作研究阅读提示，不属于本轮冻结来源给出的标准部署分类。
4. raw 自检矩阵中的 `A01–A10`、`A09 注记` 统一对应 `d01–d10`、`d09 注记`，不得视为另一套 ID。

## 4. WQ001 有效关系

WQ001 仍有五个 draft relation ID，但 B2、B3、B5 必须按场景分支读取，不能把 OSFP 与 CPO
拼成同一条产品级因果链。

### WQ001-a2-b01：带宽

- 有效链：聚合带宽与 lane 拆分需求 → x8/lane 配置与 Host/Media 接口容量 →
  条件化接口骨架与单产品逐 lane 电/光收发 → aggregate rate、lane 数与 lane 速率。
- 强度：规范结构支持（含单产品实例）。
- 禁止：普遍必须增加 lane、x8 必优于 x4、由此选择光子平台。

### WQ001-a2-b02：距离

- 接受的可插拔场景链：目标 reach → 介质与 PMD 联合定义 → Coherent 500 m SMF/MPO-16
  单产品接口实例 → 介质类别、PMD、标称 reach。
- 强度：规范结构支持（含单产品实例），只支持 reach/media/PMD 映射。
- OIF mid-board optical connector → optical budget → TX/RX 参数只保留为 CPO 场景的物理注记，
  本轮没有独立 route-side 场景需求证据，因此不再并入 B2 的有效桥。
- 插损与 optical-budget 量值挂 `PQ009`；连接器形态与位置挂 `PQ005`。

### WQ001-a2-b03：功耗

- 接受的 OSFP 场景链：系统功耗/热约束 → power class、host enable、低/高功耗模式 →
  thermal design/validation → power class、产品 dissipation、热验证边界。
- 强度：规范结构支持，但 route-side 与核心 physical mechanism 均复用 OSFP §15.8；这是
  单源双侧使用，不是独立双源证实。PQ002-a3-d08 只补充供电/地物理路径分层。
- CPO“缩短高速电通道以降低损耗”仅作为 framework target，不能并入 OSFP 产品实测链，
  也不能写成 CPO 实测一定更省电。

### WQ001-a2-b04：密度

- 接受的 CPO framework 场景链：端口拆分与 substrate 面积需求 → lane flexibility 与
  footprint 取舍 → engine-to-substrate retention/solder/socket/rework/yield → 占位与返工指标。
- 强度：规范结构支持；OIF §7.2.1/Table 4 是单源双侧使用，不是两份独立证据。
- 禁止：换算 ports/RU、直接选择 solder/socket 或路线、把 Table 4 当 Media Interface。

### WQ001-a2-b05：维护

- 分支 A（可插拔产品）：现场更换需求 → hot-pluggable 能力 → Coherent OSFP 单产品实例 →
  是否 hot-pluggable。强度：受限推论。
- 分支 B（CPO framework）：返工/维修需求 → attach 与 connector access →
  solder/socket/pigtail 的 rework、yield、field access 属性 → 返工方式与现场访问限制。
  强度：受限推论。
- 两个分支不得合并成“所有光模块的通用维护物理”，也不得用于证明生命周期成本下降。

## 5. 仍未桥接

- 成本金额与路线成本排序；
- 维护成本定量；
- CPO 实测功耗；
- optical-budget、插损、TX power、RX sensitivity、margin 数值；
- ports/RU；
- 由任一约束直接推出 EML、SiPh、LPO、CPO 路线或公司受益。

## 6. 停止状态

- `canonical_write_performed: false`
- `coverage_status_changed: false`
- `new_question_ids_created: false`
- 所有原子主张与关系均为 draft-only，`would_mark_covered: false`。
