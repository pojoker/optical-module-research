# Kimi 审核：PQ002 物理知识追加候选 v1

- 日期：2026-08-31
- continuity handle：`session_9b3c8af2-d10c-4713-a573-ed0e37e69a03`
- 审核对象：`docs/research/knowledge-append-candidate-pq002-v1.yaml`
- 问题对象：`docs/research/expert-questions-pq002-candidate.yaml`
- 审核方式：延续既有会话；只读审核；未修改文件
- 总裁决：`PASS`

## 逐条裁决

| 候选 | 裁决 | 语义判断 |
|---|---|---|
| `PQ002-KN-C01` / `KN011` | PASS | CMIS §6.1.1、§6.1.2、§6.2.1.1 直接覆盖 Host/Media 收发方向与模块内桥接；光纤条件下的电转光/光转电由中际旭创年报承担。候选明确写出 CMIS 不能单独证明 media 必为光纤，没有变宽。 |
| `PQ002-KN-C02` / `KN012` | PASS | OSFP §15 的高速 TX/RX、低速控制、供电和地，以及 CMIS 双线管理与高速任务接口，共同支持路径分层。候选明确声明管理和电源并非不重要，只是不属于电→光→电主链的串行处理步骤。 |
| `PQ002-KN-C03` / `KN013` | PASS | OIF Co-Packaging FD Glossary 的 EIC/PIC 条目保留 `may contain`；候选全程使用“可以包含”，并限定为单一 framework 实例，不升格为所有光模块的固定 BOM。`object_level_candidate` 是恰当的保守档位。 |

## 依赖与验收

- `atomic_after_dependency` 合理：PQ002 批只在 PQ001 的 KN008–KN010 批物化后成为 KN011–KN013。
- PQ002 要求 C01+C02+C03 整批通过，比当前问题树“一条 KN 即覆盖”的形式条件更严格。
- 三条分别覆盖收发方向、并行支撑路径和受限内部分工例子，只闭合功能链层；器件级 BOM、连接和测试仍留给 PQ004、PQ005、PQ009。
- PQ003、PQ004、PQ005、PQ009 保持 `unchanged_unresearched`，与 post-review effective text 一致。

## 新问题裁决

`PQ002-NQ01` 值得保留为 draft-only 对象解析问题：它追问 Coherent `FTCE4517E1PxM` 产品族中接口功能究竟映射为独立器件、同芯片/封装集成，还是仍未知。

- 与 `QUP06-NQ03` 不重复：后者追问 FR4-500 合分波实现，对象和功能域不同。
- 与 `QUP06-NQ08`、`QMID01-NQ03/NQ06` 的故障域和故障注入问题已主动去重，不另建 ID。
- `blocked_on_public_evidence` 合理：公开产品页和数据表只到接口/标签层，解锁件是同实物 CMIS 全页 dump、厂商框图、带 chain-of-custody 的拆解/X-ray/失效分析。
- 未发现器件只能保留 `UNKNOWN`，不能写成已删除或已集成。

## 最终状态

两个文件均可作为 draft-only 晋升候选进入用户决策。该结论不构成 canonical 写入授权；父批、子批的正式写入仍须用户明确批准，且写入前需重新核对 canonical hash、连续 ID 与仓库总闸。
