# flows/content-ledger-schema-v1.md — 内容台账 Schema v1（终审冻结版，2026-07-24）

字段：{cid, 类型[工序步骤|技术参数|产品构成|代际事件|设备-工序能力], 内容(原子句),
stance[issuer_self|industry|neutral], 时态[current|historical|planned], 命中引语,
章节位置, 锚点URL, source_chain(文件→章节→句), 验证态[引语级机械验证|人工复核|未验],
关联(仅允许: 公司节点属性/BOM树节点, **禁止关联交易边**)}
红线：issuer_self 永不承重；内容条目不得作为关系边证据；每条原子化单事实。
