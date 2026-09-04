# TQ005–TQ008 Pi 草稿裁决

## Verdict

`usable_after_codex_corrections`。

Pi 成功完成四轴最小字典、证据分层和无新 QID 的细化问题生成；没有越过 TQ009、WHY、公司归群或落库边界。但 raw 不能直接作为下一轮输入，必须由 `post-adjudication-effective-text.md` 覆盖以下问题。

## 接受项

1. TQ005/TQ006 的 MSA profile 没有被创建成第五根轴。
2. LPO 被拆为 `linear + pluggable`，OSFP/QSFP-DD 保持为 pluggable 子层。
3. TQ007 使用五个嵌套字段，没有新增子 QID。
4. other on-board 与 NPO 已分开，NPO/CPO 均有 OIF 锚。
5. framework/in-progress、公司平台披露、已观察产品/演示已经分层。
6. 共生成 20 个细化问题，全部只挂 TQ005–TQ008，不自造编号。
7. raw 中 24 个 draft_id 唯一且全部 `would_mark_covered: false`。

## 必须纠正

1. **删除无来源的 GaAs。** 当前冻结来源支持 SiPh 与 InP 例子，也支持 VCSEL 器件实例，但没有把 GaAs 明确写成已证实的 platform/material 值。GaAs 只能保留为待研究问题，不能进入当前字典。
2. **TQ007 integration 不收纳封装位置。** `pluggable / on-board / CPO` 属 TQ008。TQ007 integration 只记录器件/PIC/EIC/光源之间的 monolithic、on-chip、hybrid、die-stack 等集成关系。
3. **EML 第二来源已经存在。** S12 的 Coherent ECOC 2022 页面也把 InP EML 定义为 DFB + EAM，因此 raw 中“当前只有一个器件厂商定义”的开放问题作废。新问题改为：两家来源是否足以建立跨厂术语边界，以及不同 EML 结构/封装是否需要继续细分。
4. **不得把 3 nm DSP 演示自动写成 full-retimed。** S9 明确 LRO 变体只在 Tx retime，并披露另一变体包含 3 nm DSP；但摘要没有明确后一变体 Rx 是否 retimed。有效表述只能是“LRO 与 DSP-based 变体并存，精确 RX 职责仍待证据”。
5. **generic linear 不继承一个 profile 的全部职责。** host 承担 FEC、retiming、DAC/ADC 等只对冻结的 100G-DR-LPO profile 成立；不能把它写成所有 linear 实现的全称定义。
6. **LRO、RTLR、half-retimed 暂不合并同义词。** 当前来源显示职责邻近，但命名 scope 未做正式对照；必须保留为 TQ006 开放问题。
7. **other on-board 使用保守定义。** Intel 只披露 stand-alone on-board 能力，没有给 first-level substrate 细节。有效口径是“已知不是 front-panel pluggable，且未被来源证明满足 OIF NPO/CPO 定义”，不能反向断言其所有基板关系。
8. **公司器件定义标签需加 subtype。** S11/S12 的 EML 定义仍可放在强制六标签中的 `company_platform_statement`，但必须注明 `official_device_definition subtype`，避免与平台能力声明混淆。

## 停止状态

- canonical_write_performed: false
- coverage_status_changed: false
- new_question_ids_created: false
- TQ005–TQ008 均未标记覆盖。
