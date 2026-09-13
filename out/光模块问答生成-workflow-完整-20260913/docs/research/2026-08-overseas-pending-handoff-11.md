# 境外待判 11 家主体核验与海外雷达处置建议（2026-08-22）

## 结论先行

对 `MSG-20260822-KIMI-OVERSEAS-PENDING-HANDOFF-01` 所列 11 家主体逐条核验，并按海外层“新名称先进入 discovery；只有持续产生高价值事件后才晋级 watch”的闸门处理后，建议分为：

- `discovery` 8 家：ALFAFONET、FOSTEC、Fibracem Teleinformática、Kumpulan Abex Sdn Bhd、Out Line S.r.l.、SHARPNFLAT/S-MODUL、ATX Networks、Power Master Semiconductor Co., Ltd.；
- `历史/附属身份` 2 家：Cloud Light Technology Limited、Prime World International Holdings, Ltd.；
- `主体退出经营/资产处置` 1 家：Kaiam Corporation；
- **本批不直接新增 watch，也无需继续把任何一家留在主树待判。**

其中两个先手判断一项确认、一项需要校正措辞：

1. **Cloud Light 已确认纳入历史身份。** Lumentum 于 2023-11-07 宣布完成收购；海外工作树也已用 `WATCH_CLOUDLIGHT → LITE` 登记 `acquired_by`，不应与 Lumentum 重复计票。
2. **Kaiam 的经营主体退出可以确认，但不宜写成“2019 年 Chapter 11 破产”。** 美国联邦法院文件证明 Kaiam Corporation 已进入 California `assignment for the benefit of creditors`（ABC）清算式程序；英国两家子公司先后进入 administration/liquidation 并已注销，PLC 业务资产亦在 2019 年完成出售。建议核销值写成 `驳回-主体退出经营/资产处置`；若主树枚举值只能使用 `主体消亡`，应在备注中保留“ABC，不是已证实的 Chapter 11”这一法律口径。

## 核验范围与证据口径

- 对表文件只读：海外工作树 `calls/company_candidates.csv`、`calls/watch_entities.csv`、`calls/entity_relationships.csv`（工作树 HEAD `3d6f663`）。精确名称/常见别名检索结果只有 Cloud Light 命中；其余 10 家在三表中均无现成记录。
- 海外层 `calls/README.md` 的升级闸门规定：新名称先进入 `company_candidates.csv`；只有持续产生高价值事件且不需要连续季度经营材料时才晋级 `watch_entities.csv`。因此“官网当前仍在经营”只足以支持 `source_verified discovery`，不单独构成 watch 晋级证据。
- [仕佳光子上交所问询回复](https://static.sse.com.cn/stock/disclosure/announcement/c/202005/000355_20200528_S6GW.pdf)第 43–44 页列出该批供应商/客户的全名、国家、成立年份和业务简介，作为交接短名与法定/营业名称的共同身份基线；再以各主体官网、SEC、法院或注册文件核验当前状态。
- `watch`：主体已被证明能持续产生高价值事件，适合正式进入事件雷达；本批当前均未越过这一晋级闸门。
- `discovery`：主体身份和当前经营活动已由一手来源定位，但尚未证明能持续产生高价值事件；可先进入发现候选，不进事件雷达或覆盖率。
- `历史/附属身份`：已并入现有覆盖公司，或本来就是其并表子公司；只用于解析身份和历史事件，不作为独立公司重复计票。
- 名称连续性仍有窄缺口时可以在 discovery notes 保留 `legal rename pending registry verification`，不必继续占用主树待判。
- 公司官网可证明“公司当前对外宣称并经营这些产品”，不能单独证明法定 good standing；监管申报、法院文件、官方注册记录和收购方完成公告的证据强于公司自述。

## 逐条处置表

| # | 交接名称 | 身份/存续核验 | 建议分类 | 处置理由与边界 | 一手来源与质量 |
|---:|---|---|---|---|---|
| 1 | ALFAFONET（土耳其） | 官网法律页给出完整主体 `ALFAFONET ENDUSTRIYEL TELEKOM URUNLERI A.S.`；公司页称 2011 年成立，总部在 Istanbul、制造活动在 Eskişehir，制造光纤连接产品；当前官网仍提供产品目录、数据表和联系方式。未见并购或消亡信号。 | `discovery` | 直接覆盖光纤跳线、配线架、ODF、机柜、接续盒等被动连接，但本轮只有身份/产品核验，尚无持续高价值事件序列，先进入发现候选；不能把被动连接产品外推为高速光模块制造。 | [公司介绍](https://www.alfafonet.com/alfafonet_company.html)、[官网法律主体页](https://market.alfafonet.com/tr/gizlilik-sozlesmesi)、[官方资料下载页](https://www.alfafonet.com/downloads.html)。质量：B+（公司官网给出完整主体与当前产品；法定 good standing 未独立调取）。 |
| 2 | Cloud Light Technology Limited | Lumentum 于 2023-11-07 明示完成收购，交易值约 7.5 亿美元。海外层已有 `WATCH_CLOUDLIGHT` 和 `REL_CLOUDLIGHT_LITE`，生效日同为 2023-11-07。 | `历史身份` | 已闭合为 Lumentum 的并购能力来源，只保留别名与历史事件，不再建立独立 watch 或重复计票。 | [Lumentum 完成收购公告](https://investor.lumentum.com/financial-news-releases/news-details/2023/Lumentum-Announces-Completion-of-Cloud-Light-Acquisition/default.aspx)。质量：A（收购方完成公告，并已与本地关系表交叉一致）。 |
| 3 | FOSTEC（韩国） | 官网历史页记录 2001 年设立；公司现有光通信器件、线缆和设备制造能力，并明确覆盖数据中心、国防及光网络。未见并购或消亡信号。 | `discovery` | 直接光连接和硅光相关发现价值足够，但尚未按海外层形成持续高价值事件序列；先作发现候选，只记录具名产品、订单、合作和产线证据，不补季度槽。 | [官方历史页](https://www.fostec.co.kr/user/page/history)、[公司介绍](https://www.fostec.co.kr/user/page/about)、[官方英文产品目录](https://www.fostec.co.kr/ucommon/assets/catalog/fostec-comprehensive-catalogue-eng.pdf)。质量：B（公司官网；经营活动强、法定存续中等）。 |
| 4 | Fibracem Teleinformática（巴西） | 官网给出法定名 `Fibracem Teleinformática Ltda` 与 CNPJ `02.010.281/0001-99`，称自 1993 年经营光网络基础设施；官网在 2026 年仍发布新品和数据中心合作消息。 | `discovery` | 光缆、接续、终端、机架等被动基础设施有官方事件源，但尚未建立持续高价值事件记录；先作发现候选，只按无源连接/FTTx/数据中心基础设施观察，不归类为光模块厂。 | [公司介绍](https://www.fibracem.com/institucional)、[官方主页与 2026 动态](https://www.fibracem.com/)、[官方联系/法定名](https://www.fibracem.com/solucao-connect/)。质量：B+（公司官网含注册号和当年动态；未独立调取巴西注册状态）。 |
| 5 | Kumpulan Abex Sdn Bhd（马来西亚） | 官网给出公司注册号 `198801000020 (167376-M)`，称 1988 年成立，现为 E&E、photonics、telco 的供应和服务商，核心业务包括光纤测试仪器、校准、网络审计及培训。未见并购或消亡信号。 | `discovery` | 身份清楚但更像仪器分销/服务与项目商，不是核心光模块或光器件制造主体；先作为发现候选，只有出现具名制造、独家产品或重大光通信事件再升 watch。 | [公司介绍与注册号](https://www.kabex.com.my/aboutus)、[官网条款中的法定主体](https://www.kabex.com.my/termsandconditions)。质量：B+（公司官网含注册号；产品角色是公司自述）。 |
| 6 | Kaiam Corporation | 2019-05-08 的美国联邦法院命令允许 `Kaiam (assignment for the benefit of creditors), LLC` 以 Kaiam Corporation 债权人受让人身份介入诉讼，证明母公司已进入 ABC 资产清算程序。英国 `Kaiam UK Limited` 于 2019 年进入 administration、2020 年转债权人自愿清算、2022 年注销；`Kaiam Europe Limited` 于 2018-12-21 进入 administration，后清算并于 2024 年注销。博创科技监管披露还确认 2019 年完成收购 Kaiam PLC 业务相关资产。 | `主体退出经营/资产处置` | 不应移交 active watch。`主体消亡` 可作业务层核销枚举，但严格法律表述应为“母公司进入 California ABC、核心资产出售、英国子公司已注销”；本轮未取得 Delaware 最终注销证明，因此不要写“美国母公司已依法注销”，也不要写“Chapter 11”。 | [美国联邦法院 2019-05-08 命令](https://www.govinfo.gov/content/pkg/USCOURTS-cand-3_18-cv-01070/pdf/USCOURTS-cand-3_18-cv-01070-1.pdf)、[Kaiam UK 官方 filing history](https://find-and-update.company-information.service.gov.uk/company/SC444524/filing-history)、[Kaiam Europe 官方 insolvency 记录](https://find-and-update.company-information.service.gov.uk/company/03517183/insolvency)、[博创科技 2019 收购进展监管披露](https://static.cninfo.com.cn/finalpage/2019-04-30/1206200720.PDF)、[博创科技 2019 年报](https://static.cninfo.com.cn/finalpage/2020-04-17/1207514673.PDF)。质量：A（法院、官方注册/破产记录、交易所指定披露）。 |
| 7 | Out Line S.r.l.（意大利） | 官网给出 Out Line S.r.l. 的现行地址、联系方式和光纤/电信产品分类，并披露其参加 ANGA 2025 获 Lazio 区域/欧盟基金支持；Lazio 2026 官方文件亦列出该主体。未见并购或消亡信号。 | `discovery` | 直接覆盖 FTTH/FTTR、光缆、配线盒、机柜及 data center/data room，但尚未按海外层证明持续高价值事件；先作发现候选，不应视作有源光模块厂。 | [公司光纤/电信主页](https://outline.company/en/outline-company-fiber-optics/)、[2025 公司资料](https://outline.company/wp-content/uploads/2025/02/Company-Profile-2025.pdf)、[Lazio 2026 官方支持文件](https://fesr.regione.lazio.it/app/uploads/2026/05/DE-G05971_2026.pdf)。质量：A-/B（政府文件确认当期主体，公司官网确认产品角色）。 |
| 8 | Prime World International Holdings, Ltd. | Applied Optoelectronics（AAOI）2026 年 SEC 申报称 Prime World 是其在 BVI 设立的全资子公司，是 Global Technology, Inc. 的母公司，并通过台湾分部制造光收发器和开展研发。该实体仍是当前并表子公司，不是独立外部公司，也不是已消亡的旧主体。 | `历史/附属身份` | 最接近现有枚举的处理是“历史/附属身份”，但备注必须写成 `current consolidated subsidiary of AAOI`，不能误写成被收购后消亡；由现有 AAOI 覆盖，不重复计票。若未来 schema 支持 `subsidiary_of`，应改用附属关系而非 `acquired_by`。 | [AAOI 2026 SEC 招股补充文件](https://www.sec.gov/Archives/edgar/data/1158114/000110465926061146/tm2614157-1_424b5.htm)、[TL 9000 公共认证档案](https://portal.questforum.org/tl9000/public_profile.jsf?tlid=7152)。质量：A（SEC 对当前股权/经营范围的法定披露）+ B（行业认证补充台湾制造地点）。 |
| 9 | SHARPNFLAT INC | 上交所材料称其 2010 年成立、为韩国光通信企业；现行官方站点仍在文案中使用 `Sharp-N-Flat` 并把 `S-MODUL` 描述为其光纤模块品牌，另一现行站点自称 `S-MODUL Inc.` 并持续经营。产品经营连续性很强，但本轮没有韩国注册文件直接证明 `Sharp-N-Flat Inc. → S-MODUL Inc.` 是同一法人的更名、承继还是品牌/关联公司关系。 | `discovery` | 以当前展示名 `S-MODUL Inc.` 进入发现候选，`SHARPNFLAT INC` 作 alias，并在 notes 写 `legal rename pending registry verification`。该窄缺口不再占用主树待判，但在韩国登记补齐前不登记 `predecessor_of` 或 `renamed_to`。 | [现行英文品牌页](https://en.s-modul.kr/custom/brandstory.html)、[现行 S-MODUL 公司/产品主页](https://www.s-modul.com/)、[现行站点 Sharp N Flat 隐私声明](https://en.s-modul.kr/board/urgency/urgency.html)。质量：B（第一方经营连续性强；法律身份连续性不足）。 |
| 10 | ATX Networks | 官网法律页给出主体 `ATX Networks Corp.`；公司定位为宽带接入和媒体分发解决方案提供商，现有数字光传输、光节点、EDFA、光交换与无源器件产品，官方新闻页在 2026-08-18 仍发布活动/产品消息。未见并购或消亡信号。 | `discovery` | 官方通道和产品边界清楚，但本轮没有复核到足以直接晋级 watch 的持续高价值事件序列；先作发现候选，并把 CATV/HFC/FTTH 与 AI 数据中心内部高速光模块分开。 | [公司介绍](https://atx.com/company/)、[官网法律主体页](https://atx.com/legal/)、[数字光传输产品页](https://atx.com/products/digital-optical-transport/)、[2026 官方新闻](https://atx.com/company/press-release/atx-networks-showcases-network-reliability-and-real-world-experience-at-scte-techexpo-2026/)。质量：B+（当年公司官网动态与明确法律/产品主体）。 |
| 11 | Power Master（功率器件封测） | 上交所身份基线与官网相互匹配，对应韩国 `Power Master Semiconductor Co., Ltd.`。官网称 2018 年成立，是拥有韩国 fab 和研发中心的 integrated power device manufacturer，当前产品为 SiC MOSFET/diode/module、SJ/MV MOSFET 与 IGBT；Hana Microelectronics 官网把它列作 100% ultimate holding 的韩国 Si/SiC wafer-device 公司。官网不支持“纯封测厂”这一标签。 | `discovery` | 主体活跃，但只与服务器/电信电源、数据中心供配电相邻，不属于光通信雷达核心。建议以更正后的法定名和 `integrated power-device manufacturer with in-house fab / foundry services` 角色保留 discovery；在没有明确光电子封测或光通信产品证据前不升 watch。 | [Power Master 公司介绍](https://powermastersemi.com/eng/about/about-us.html)、[官方产品主页](https://powermastersemi.com/eng/)、[Hana Microelectronics 集团公司档案](https://www.hanagroup.com/AboutUs/CompanyProfile/1000)。质量：B+（公司与母公司双方一手材料交叉；具体股权变动日未在本轮闭合）。 |

## 建议给主树的核销措辞

不建议把 11 条统一写成 `驳回-移交海外雷达(见calls/<file>)`：本轮没有创建任何 `calls/<file>`，而且历史/附属身份与主体退出并不等同于“移交 active radar”。建议分流：

| 类别 | 建议处置值 | 适用主体 |
|---|---|---|
| discovery | `驳回-移交海外雷达-discovery（见 docs/research/2026-08-overseas-pending-handoff-11.md）` | ALFAFONET、FOSTEC、Fibracem、Kumpulan Abex、Out Line、SHARPNFLAT/S-MODUL、ATX、Power Master Semiconductor |
| 历史/附属身份 | `驳回-海外历史或附属身份已覆盖（见 docs/research/2026-08-overseas-pending-handoff-11.md）` | Cloud Light、Prime World |
| 主体退出 | `驳回-主体退出经营/资产处置（见 docs/research/2026-08-overseas-pending-handoff-11.md）` | Kaiam Corporation |

如果 triage schema 只允许 Kimi 提议的单一枚举，可对已吸收的 10 家使用 `驳回-移交海外雷达`，但必须在 notes 中区分 `discovery / historical_or_subsidiary`；Kaiam 不应套用该枚举。

## 不影响本次归口的两个窄问题

1. **SHARPNFLAT/S-MODUL 法人连续性**：需要韩国企业登记原件或等效官方查询，确认法人号、旧名、新名和变更日；当前可在 discovery notes 留缺口，不应建立历史关系。
2. **Kaiam Corporation 法定注销日**：业务退出和资产清算已充分证明，但本轮没有取得 Delaware registry 的最终 dissolution 文件。该缺口不妨碍“退出 active watch”的结论，只影响能否使用最严格的“法人已注销”措辞。

## 不应外推的关系

- 纳入海外 watch/discovery 不自动生成任何海外—国内合作、供货、竞争或替代 edge。
- Prime World 的制造活动只能归入 AAOI 合并范围，不能新增第二家公司计票。
- Power Master 的服务器/电信电源应用不等于光模块、光器件封装或光通信客户采用。
- 被动光连接、FTTH/HFC/CATV 产品不得与数据中心 800G/1.6T 模块混为同一产品层。
