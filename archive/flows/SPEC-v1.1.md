# flows/SPEC-v1.1.md — 供应链微观倒推升级规格

**目标**：在 v1.0 关系图（"谁和谁有关系"）之上补三个维度——配方(BOM)、量价分离、
传导时间差——使图谱能回答"一头动了，另一头动多少、什么时候动"。

**纪律沿用**：四件套边准入、金额逐位、T3 只作线索不入图、橱窗机构零引用、
warnings 不静默。所有产出验证状态标"v1.1管线产出-未人工复核"，晋级须经终验。

## 新数据结构

**flows.csv**（配方层，与 edges.csv 平行的第二张表）：
`flow_id,产品,构成项,构成类型(原材料/器件/设备),系数或占比,计价单位,期间,证据文件,锚点,验证状态,备注`
例：`FL001,光模块封装测试设备,光学器件类,原材料,XX%,采购额占比,2024,猎奇招股书,<URL>,...`

**catalog.csv**（产品目录层）：
`cat_id,公司,产品型号,速率,封装,技术路线,来源URL,抓取日期,备注`

**customs-monthly.csv**（量价层）：
`月份,HS编码,商品名称,出口量,量单位,出口额美元,均价,来源URL,抓取日期`

**procurement-awards.csv**（集采实名量价层）：
`award_id,招标方,中标人,标的(速率/型号),数量,单位,金额或单价,公示日期,来源URL,备注`

**leads-pool.csv**（T3 线索池，永不入图）：
`lead_id,线索描述,涉及公司,线索来源(媒体/公众号名+URL),报道日期,待验证的T1路径,状态(待验证/已验证/证伪)`

## 五路分工

| 路 | 承包方 | 输入 | 产出 |
|---|---|---|---|
| A BOM抽取 | cursor grok | flows/input/lieqi_prospectus.txt（在手） | flows/out/flows-seed.json + 抽取说明 |
| B 海关通道 | codex | stats.customs.gov.cn 探测 | flows/src/fetch_customs.py + flows/out/customs-monthly.csv |
| C 集采通道 | claude sonnet 子代理 | 运营商招标网站探测 | flows/out/procurement-awards.csv + 通道卡 markdown |
| D 产品目录 | codebuddy hy3 | 旭创/新易盛/天孚官网 | flows/out/catalog.csv |
| E 线索池 | kimi k3 | 行业媒体近期报道 | flows/out/leads-pool.csv |
| 终验 | Claude 本会话 | 全部产出 | 抽检+汇合报告 |

## 各路验收标准

- A：原材料构成表数字与招股书原文逐位一致（终验抽检）；抽不到的字段 warnings 明示
- B：任一光模块相关 HS 编码拿到 ≥12 个月的量价序列即过线；接口不可达则给出探测轨迹
  与替代路径（诚实失败可接受，编数字不可接受）
- C：≥5 条实名中标记录，每条带公示页 URL；找不到则给检索轨迹
- D：三家公司各 ≥5 个型号，字段齐全，每行带来源 URL
- E：≥8 条线索，每条必须填"待验证的T1路径"列；禁止把线索写成结论
- 通用红线：所有数字必须带来源 URL+抓取日期；网络不可达/登录墙如实标注不绕行
