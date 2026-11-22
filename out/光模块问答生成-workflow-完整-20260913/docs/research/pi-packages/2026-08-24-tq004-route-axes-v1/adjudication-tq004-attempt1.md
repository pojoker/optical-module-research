# TQ004 attempt-1 Codex 裁决

结论：`revise_and_rerun`。四轴方向、证据分层和跨轴实例可保留，但术语粒度尚未满足 TQ004 的
分类目标。

## 通过部分

- 产品/链路、电信号处理、光子实现、封装/放置四个分析方向成立；
- “正交是分析纪律，不是自由组合”成立；
- Coherent、Intel、LPO MSA 的跨轴实例可用，且没有推成量产、份额或优劣；
- 未生成新 QID，未写 canonical，未改变覆盖状态。

## 必须修正

1. `TQ007` 改名为“光子实现轴（嵌套字段）”。EML 是 InP DFB+EAM 的发射器件实现，SiPh 是
   PIC/集成平台，二者不是同粒度轴值。至少拆出 platform/material、light source、modulator/emitter、
   detector、integration 五类字段。
2. `LPO` 不得作为纯 TQ006 轴值。规范化表示为：
   `electrical_architecture=linear` + `packaging=pluggable` + `link/interface profile=LPO MSA profile`。
   `LPO` 只保留作复合 alias。比较 DSP/LPO 应改为比较 `retimed vs linear`。
3. `CPO` 是封装/放置值，不固定电架构；OIF framework 中可再区分 retimed、linear、half-retimed、
   direct drive 等电接口候选。
4. Coherent 的“低 BER 实现”没有披露电架构，不能作为 TQ006 第三个轴值；只保留未分类演示注记。
5. “每一轴值都与其他轴多个值共存”过强。只可写：已观察到的组合足以否定若干普遍的一一映射，
   不能外推所有轴值或所有组合。
6. 功耗/成本/良率/密度的路线级排序缺口不应挂 PQ010；应在形成 TQ009 路线画像后挂现有 TQ014，
   本轮只登记依赖，不回答。
7. 原子主张收敛到不超过 14 条，避免把自检纪律重复生成为知识主张。

## 状态

- canonical write：false
- coverage change：false
- new question IDs：false
