# AGY 3.7 Flash 首轮小样审计

日期：2026-08-26
状态：draft-only；不落知识库；不改变问题覆盖状态。

## 总结

首轮证明 AGY 能快速找到高价值的一手候选来源，但不能直接承担实例合成。两份回答都出现了把来源中没有明示的字段补成产品事实的问题。

## EML 小样

AGY 找到的有效上游是 Coherent 官方 `FTCE4527E1PxA-2N` 产品页和 2023 Rev A1 初步规格书。官方材料可以直接支持：800G-DR8+、OSFP、2 km SMF、8×100G PAM4 retimed electrical interface、Dual MPO-12、EML transmitter、PIN receiver、0–70°C、最高 17 W 等字段。

首轮输出不可直接消费的内容包括：

- 把准确料号写成缺少 `-2N` 后缀的 `FTCE4527E1PCA`；
- 一边引用 `2N: No Heat Sink Design`，一边断言 closed-top heatsink；
- 从规格书与监管认证推断 GA、量产和 active ordering；
- 把 TDECQ 误当作 TEC 证据；
- 未经披露补入 TOSA/ROSA、PIN array、free-space lens array、内部 TEC、100% factory test；
- 把标准层 FEC 位置与具体模块实现混为产品事实；
- 使用错误或不完整的官方 PDF URL。

裁决：`PARTIAL_RETRY`。保留来源，不保留 AGY 的实例合成结论。

## 硅光小样

AGY 找到的有效上游包括 Intel 800G 2×400G FR4 OSFP 的 MDDS、Intel 硅光产品组合页，以及 Intel 作者的 OFC 2022 800G SiPh transmitter 论文摘要。

首轮输出违反单实例约束：

- MDDS 只能确认商业产品身份和 MM 编号，不能证明内部 MZM、laser、receiver、DSP、TIA、coupling 与封装结构；
- OFC 论文公开摘要描述的是 800G transmitter demonstration，不是完整商业收发模块；
- 把 2×FR4 商业产品、DR8 transmitter demo、Intel 平台级资料和 MaxLinear/Jabil 合作资料拼成同一 SKU；
- 把 receiver、Ge PIN、TIA、DSP、FEC、连接器、功耗、量产状态等未绑定到该 SKU 的字段写成产品事实；
- 论文全文公开不可访问时，仍给出无法由第三方复核的章节引语。

裁决：`REJECT_CROSS_INSTANCE_SYNTHESIS`。不得交给 Pi 作为字段表；仅保留来源定位线索。

## v2 硬门

1. 先验证 exact SKU 与 direct URL，再填字段。
2. 一个字段必须由明确绑定该 SKU 的来源支持；系列级、平台级或演示级资料不得继承给 SKU。
3. 标准只支持标准要求，不自动证明产品实现。
4. 论文正文不可公开访问时，只能使用公开摘要，不能生成章节级引语。
5. 找不到合法实例时返回 `FAIL_NO_SINGLE_INSTANCE`。
6. 不输出置信度百分比，不以来源数量代替证据强度。
