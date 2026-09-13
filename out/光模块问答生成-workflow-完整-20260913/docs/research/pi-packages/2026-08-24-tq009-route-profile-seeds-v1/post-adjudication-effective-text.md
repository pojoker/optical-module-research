# TQ009 路线画像种子：唯一有效口径

## 1. 本轮回答

现有 TQ005–TQ008 四轴可以组成具体路线画像，但只有在以下条件同时满足时才可比较：

1. 所有轴值来自同一产品或同一演示实例；
2. 每个字段独立记录值、观测状态和证据；
3. 未披露字段保留 UNKNOWN；
4. 公司平台能力、规范许可和相邻演示不能补实例字段；
5. 正式 Route Profile 还需满足 promotion contract，本轮五个对象都只是 Seed。

有效草案数据位于 `route-profile-seeds-effective.yaml`。

reviewer 后的候选 schema 有 36 个叶字段；`placement_class` 使用 `normalized` 状态，明确表示它由已观察 form factor 经冻结 TQ008 字典映射，不是假装成实例直接披露。

## 2. 五个种子显示出的真实差异

| Seed | 同实例已证实的主要差异 | 关键 UNKNOWN |
|---|---|---|
| RPS-D01 | 800G/850 Gb/s、8-lane host、PAM4、500 m SMF、parallel MPO-16、retimed raw label、EML/PIN、OSFP | optical lane bit rate/count、FEC、Tx/Rx 职责、平台/材料、光源与集成 |
| RPS-D02 | 1.6T、8×200G optical/electrical、Tx-retimed/Rx-linear（LRO）、SiPh、OSFP | modulation、FEC/PMD、media/reach/wavelength、光源/调制/探测/集成 |
| RPS-D03 | 1.6T、8×200G optical/electrical、3 nm DSP raw label、SiPh、OSFP | **normalized electrical architecture**、modulation/FEC/media/reach、光子细节 |
| RPS-D04 | 800G、SiPh MZM PIC、QSFP-DD800 | host/media lane、FEC/reach/wavelength、electrical architecture、光源/detector、PIC/EIC 集成 |
| RPS-D05 | 800G、1310 nm `EML laser` 原始组合词、generic photodetector、OSFP | host/media lane、FEC/reach、electrical architecture、platform/material、独立 modulator/emitter 类型、detector subtype、integration |

因此现有问法确实能引出技术路线差异，但差异首先表现为**原子轴值与 UNKNOWN 的不同组合**，不是公司名单，也不是单个技术名词的优劣排名。

## 3. 取舍铰链

用户补充的“优势/劣势”应成为上下游问题之间的因果铰链：

```text
上游原因
TQ002 场景约束 + TQ003 当前瓶颈 + TQ009 路线画像 + TQ010 物理变化
                         ↓
TQ014 条件化取舍（与 TQ011 并行，不作门闩）
在什么条件下获得什么优势、付出什么代价、产生什么新瓶颈
                         ↓
下游后果
优势 → 适用场景/采用价值待验证
劣势 → 新瓶颈/改进问题/验证要求/替代路线
TQ010 物理变化 → TQ011 能力要求 → TQ012/TQ013 公司挂载
TQ014 新瓶颈/验证问题 → 补充 TQ011

反馈：新瓶颈 → TQ003 → 下一代路线画像
```

这不是第三套知识体系。TQ014 保存条件化比较结果；WQ002/Why Link 保存“瓶颈为何提高工程选择相对价值”的因果边，避免同一主张双记。

## 4. 为什么现在不能直接写优势/劣势

本轮五个种子还缺少完整比较基线和 TQ010 物理变化。尤其 D01 是 800G raw retimed，D02 是 1.6T LRO，D03 电架构 UNKNOWN，不能组成“同速率 LRO vs retimed”事实对照。
公司公告中的“降低功耗”等表述也没有同条件对照测试。因此本轮只建立 `route-tradeoff-gate.md` 的 schema，不生成路线优劣结论。

合格的取舍卡至少要求：

- 明确比较的两个 Route Profile/Seed；
- 明确距离、带宽、功耗、密度、成本、维护等场景约束；
- 指明物理变化如何产生优势或代价；
- 区分事实、公司表述、行业共识和工程推论；
- 记录新瓶颈、替代方案和 UNKNOWN；
- 不压缩成总分或无条件排名。

## 5. 公司数据如何进入

现有 271 条能力点可以全部挂物理体系，覆盖 155 个唯一公司实体。公司侧采用四类关系：

1. `physical_capability_point`：现有能力点到物理格；
2. `supply_observation`：现有供应/客户观察，保持独立；
3. `capability_match_candidate`：TQ011 能力要求与能力点的字段级匹配；
4. `route_service_evidence`：公司与精确路线实例的直接证据。

当前 800G DR8 与 1.6T DR8 都机械推出同一组 83 家公司，Jaccard = 1.0，说明粗 `cell_ids` 不能区分路线。五个种子现在只允许挂 Coherent 为实例主体，其他公司等待 TQ010–TQ013。

## 6. 下一轮细化问题（不新增 QID）

### TQ009：补完整实例字段

- RPS-D01 的 optical lane count/bit rate、FEC code、Tx/Rx retiming 与平台集成由哪份同产品 block diagram/datasheet 直接披露？
- RPS-D02/D03 的 modulation、FEC、media、reach、wavelength 和 SiPh 内部器件由哪份同演示技术材料披露？
- RPS-D03 的 DSP 到底承担 Tx、Rx、FEC、DAC/ADC 中哪些职责？
- RPS-D04/D05 的互操作端点分别有哪些完整 host/media lane、reach 和内部架构参数？

### TQ010：形成可比较的物理变化

- 选择哪一个字段更完整的 seed 作为参考基线？
- LRO 相对同速率 retimed 画像，明确删除、迁移或新增了哪些 DSP/CDR/FEC/测试职责？
- 800G SiPh MZM PIC 与 EML/photodetector 端点在组件、接口、装配、测试上分别改变了什么？
- 哪些变化是来源直接披露，哪些只是待验证工程推论？

TQ010 的能力变化研究可以直接并行进入 TQ011，不等待 TQ014 完成。

### TQ014：上下游取舍

- 在同一速率、reach、BER/FEC、温度和测试口径下，LRO 相对 retimed 画像的功耗优势与系统代价是什么？
- SiPh MZM PIC 与 EML 路线的优势/代价是否能在同场景、同边界条件下比较？
- 每项劣势产生什么新瓶颈，并回填到 TQ003 的哪类约束？
- 每项优势打开哪些适用场景，仍需什么采用证据验证？

当前证据不足时，TQ014 只允许输出 UNKNOWN/不可比判断和缺证问题，不允许生成 LRO 相对 retimed 的功耗结论。

### TQ011–TQ013：公司挂载

- 每个已证实物理变化需要什么设计、制造、封装、测试能力和验收指标？
- `points.csv` 现有字段能否表达这些要求，缺少哪些能力维度？
- 哪些来源能把某公司、精确产品/演示和具体 Seed 直接连起来，而不是只证明一般能力或供货关系？

## 7. 状态

- formal_route_profiles_created: false
- canonical_write_performed: false
- coverage_status_changed: false
- new_question_ids_created: false
- company_groups_created: false
- TQ009: draft-only, not covered
