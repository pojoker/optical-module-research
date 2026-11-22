# 可挂公司数据的问题树 / 知识图草案

## 当前判断

树已经从“问题列表”前进到“可以挂现有公司点的草稿图”，但还不能生成正式公司路线分组。正确结构不是把公司复制到每条路线下面，而是让一个公司实体通过有类型、有证据的关系连接两套知识体系。

```text
物理知识体系                                  技术路线体系

Physical Cell                                Route Profile Instance
  C1 激光器                                     TQ005 外部链路
    └─ facet: EML/DFB/CW                        TQ006 电职责
  C3 探测器                                     TQ007 光子实现
    └─ facet: generic/PD/APD                     TQ008 放置/形态
  C4 硅光 PIC                                      │
    └─ facet: SiPh/MZM/integration                  │ requires
  C5 电芯片                                        ▼
    └─ facet: DSP/Driver/TIA/retiming/node      Route Requirement
          ▲                                         │
          │ candidate match                         │ why（待证据）
Company ─ Point ─ Capability Assertion              ▼
                                             constraint → mechanism
                                             → trade-off → requirement
```

公司不是路线的孩子。公司仍是唯一实体；`points.csv` 的 point 先锚定物理格，再从原引语提取 capability facet 和 role，最后才可能形成 `candidate_match`。只有完整满足当前 requirement 字段、泛化 requirement 的 scope，或精确命中一个产品属性时才进入候选；仅共享一个 facet 的点停在 `related_facet_only`，不生成 requirement-match 边。两者都不等于供应、客户、采用或服务关系。

## 本轮已经细化到的可放置程度

现有 `points.csv` 中与 C1、C3、C4、C5、MOD1 相关的 56 个点（40 个公司字符串）已全部经过草稿匹配：

- 39 个点能从原引语提出至少一个明确 facet；
- 17 个点仍只能停在原物理格，不能安全细分；
- 6 个点与本轮 requirement/product-attribute 形成 generic-scope 或单属性候选匹配；
- 另有 14 个点只与某 requirement 共享相关 facet，不生成 requirement-match 边；
- 1 个点因引语主体是参股公司而被阻断；
- 0 个点被提升为“公司服务某路线”。

按当前证据：

| 路线要求/属性 | requirement/属性候选点 | 仅相关 facet 点 | 判断 |
|---|---:|---:|---|
| D02 C5 LRO/Tx-Rx responsibility | 0 | 3 | 有 DSP/重定时 facet，但无完整 Tx-retimed/Rx-linear 证据 |
| D03 C5 3 nm DSP | 0 | 2 | 有 DSP facet，无同一点的 3 nm 证据 |
| D04 C4 SiPh MZM PIC | 0 | 5 | 有 SiPh facet，无 MZM PIC；foundry/platform 点不会进入 requirement 桶 |
| D05 C1 1310 nm raw EML laser | 0 | 6 | 有 EML facet，无 1310 nm 同点证据 |
| D05 C3 generic photodetector | 5（generic scope） | 0 | 仅在泛探测器层候选，不能回填路线 subtype |
| D04 QSFP-DD800 | 0 | 0 | 当前相关点没有精确属性证据 |
| D05 OSFP | 1（单属性） | 0 | P254 只匹配 OSFP；其 1.6T 与 D05 的 800 Gbps 明确不同。P193 因参股公司主体被阻断 |

## “为什么要这么做”目前走到哪里

这一轮的两组实例都缺少同条件的 reach、FEC/BER、温度、功耗边界、密度、成本和维护数据，所以只能证明“实现描述不同”，不能证明优势/劣势，更不能建立因果 WHY 边。

WHY 应当单独长成：

```text
场景约束
→ 工程机制
→ 优势 / 代价 / 新瓶颈
→ 选择某个路线轴值
→ 需要哪些物理格与 facet
→ 哪些公司 point 可以候选匹配
```

当前最后两步已做出数据结构；前三步仍需新的、同条件且可溯源的技术资料。若现在直接写“LRO 更省电”“EML 路线成本更低”之类结论，会再次把一般行业印象当成实例事实。

## 下一轮应该补什么

下一轮不应继续泛化扩树，而应为两个可比路线对寻找受控 trade-off 证据，优先补：

1. 相同速率、reach、FEC/BER、温度与功耗边界下的电架构比较；
2. 相同 endpoint role 与 link 条件下的 SiPh MZM PIC / EML 实现比较；
3. 能把 advantage/disadvantage 连接到具体物理 facet 的机制证据；
4. 公司 point 的稳定 `company_id`、精确引语片段和角色复核。

在这些完成前，当前图适合网页小样展示“证据点—facet—候选 requirement”的链路，不适合展示正式路线集团或排名。
