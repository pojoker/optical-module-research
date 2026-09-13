# PQ002 attempt-1 Codex 裁决

结论：`changes_requested`

## 通过部分

- CMIS Host/Media 接口与 TX/RX 方向语义基本准确；
- 电→光→电被限制在 optical-media 条件；
- 管理、供电与高速 mission data path 有意识分层；
- Coherent EML/PIN、retimed、MPO-16 被标成单料号实例。

## 必须修正

1. **CPO 装配接口被误写成 Media Interface**：OIF Table 4 的 solder reflow/socket 描述
   optical engine 与 CPA substrate 的封装/主机侧装配，不是光 media 接口。attempt-1 的三层表、
   draft-015、draft-019、N3 和 RJ-04 均受影响。
2. **“全部都不构成必备”是由证据缺席推出本体否定**：只能写“本冻结来源包不支持把这些
   部件声明为所有光模块必备”，不能写成宇宙范围事实。
3. **双向对称条件不充分**：端到端双向链应限定为本轮讨论的 bidirectional optical
   transceiver，不能从 CMIS transmission module 无条件推广。
4. **机械/热路径证据混写**：hot-plug、socket/reflow 可支持机械/装配分层，但来源摘录未直接
   支持 attempt-1 对所有“热路径”的概括。
5. 原子主张过多且重复；最终稿应压缩为不超过 12 条，以功能链为主，不提前写 PQ004/PQ005。

## 正确口径

- CPO 的 media-side 实例应使用 OIF §7.3.2/§7.3.4 的 pigtail/built-in connector/
  mid-board optical connector，而不是 §7.2.1 的 engine-to-substrate attach。
- §7.2.1 Table 4 只允许用于说明非数据路径的封装/返工实现。
