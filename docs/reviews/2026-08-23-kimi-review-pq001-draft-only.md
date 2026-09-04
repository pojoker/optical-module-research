# Kimi 对 PQ001 draft-only 研究包的只读审核

审核日期：2026-08-23
审核模型：Kimi K3
最终结论：`accepted`
知识库动作：无

## 核验范围

- `raw-output-attempt-3.md`
- `adjudication.md`（显式勘误加入前版本）
- `sources-attempt-3.md`
- `run.yaml`
- `corpus/web/2026-08-23/PQ001-snapshot-manifest.md`
- S1–S5 原始材料及 6 份网页快照

使用 `/Users/jowang/miniconda3/bin/python3` 复算快照 SHA256，并抽取 OSFP、CMIS、CPO PDF
关键页。6 份快照均与清单一致。

## 五项结果

1. **CMIS 条件通过**：`CMIS-managed transmission module` 条件、resource module / cable
   assembly 例外、高速 mission 接口与低速 two-wire 管理通信分层均与原文一致。
2. **OSFP 归属通过**：card-edge pads ↔ host connector、module form factor 与 host
   cage 分列、标准 OSFP integrated heatsink 属 module、OSFP-RHS riding heatsink 属 host、
   §14.4 仅为 optical-interface guideline，均经关键页核验。
3. **CPO 范围通过**：草案明确限于 OIF 3.2T CPO IA，没有把近 ASIC、共 substrate、
   embedded、pigtail 推广为所有 CPO 或所有光模块。
4. **0 条研究注记基本合理**：现有冻结来源可以关闭本轮粒度的主张；标准 OSFP 可选
   extra riding heatsink 还可由印刷页 47 §5.5 的 cage 语境进一步支持。
5. **无 canonical 写入**：`knowledge.yaml`、`research_questions.yaml` 和 canonical CSV
   未修改；PQ001 没有 KN 关联，所有 `would_mark_covered` 均为 `false`。

## 观察

- 原稿中的“riding heatsink 属主机”若脱离 OSFP/OSFP-RHS 语境会显得过宽；当时的
  `adjudication.md` 已收窄，但有效口径分散在两个文件。
- 旧裁决选择“不独立主张”标准 OSFP 可选 extra riding heatsink 的归属，安全但偏保守；
  §5.5 写明 extra riding heatsink 位于 OSFP cage，可支持 host/cage-side 的窄主张。
- “module 外壳 ↔ host cage”是规范结构给出的低风险关系判断，不是逐字引文。

综合结论：没有发现事实锚点错误；研究包作为 draft-only 草案可用，但后续消费必须服从
裁决中的 OSFP 条件边界。
