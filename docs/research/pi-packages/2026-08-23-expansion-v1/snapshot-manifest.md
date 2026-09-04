# PQ002 / TQ002 扩展轮次快照清单

抓取日期：2026-08-23。快照是 draft-only 证据锚，不表示允许落库。

## 新增快照

| 文件 | 原 URL | 字节 | SHA256 | 用途 |
|---|---|---:|---|---|
| `coherent.com__FTCE4517E1PxM_800G_DR8_OSFP.pdf` | `https://www.coherent.com/content/dam/coherent/site/en/resources/datasheet/networking/optical-transceivers/osfp/ftce4517e1pxm-transceiver-ds.pdf` | 421421 | `82aa77513e788205ceae163a40fe5d7c1788a43b2bdad886267b3c8d40ae6621` | 一只真实 800G DR8 OSFP 的速率、距离、功耗、接口实例 |
| `coherent.com__FTCE4517E1PxM_product.html` | `https://www.coherent.com/networking/transceivers/datacom/FTCE4517E1PxM` | 148251 | `019247e5a9881f6b4663ad7d3d99738b492f490d0ba6cb6114e2e10ae80771dd` | 产品页版本与 EML/PIN/500 m 参数交叉核验 |
| `standards.ieee.org__ethernet_800g_article.html` | `https://standards.ieee.org/beyond-standards/ethernets-next-bar/` | 141061 | `c583cd1400b21e5d05bcd3f3e8c689299515463f88b3b1c3b66375d05ccc1d5a` | IEEE 802.3df-2024 速率、lane、介质、reach 摘要 |
| `standards.ieee.org__802.3df-2024.html` | `https://standards.ieee.org/ieee/802.3df/11107/` | 267492 | `19e6f90e30ef048cd6fae59b854555725a29d3c8179e28e103680d52a82a7fcf` | 最终标准状态与范围核验 |
| `ieee802.org__802.3df_taskforce.html` | `https://www.ieee802.org/3/df/index.html` | 5239 | `2993aad8f337917139ff813ef8a2b57bf2a1256c3e7b975325ca6aea3ec8cbcb` | 任务组完成状态核验 |
| `ieee802.org__P802.3df_objectives_2022-03-17.pdf` | `https://www.ieee802.org/3/df/proj_doc/objectives_P802d3df_220317.pdf` | 142512 | `b9c38e82a985ec5e73c26702a49afb1859f0c8775dc25f5bafd9be9422292a4b` | 项目目标中的 800G 多介质、多 reach 实例；不是最终标准正文 |
| `mentor.ieee.org__P802.3df_CSD.pdf` | `https://mentor.ieee.org/802-ec/dcn/21/ec-21-0306-01-ACSD-p802-3df.pdf` | 152873 | `19a49fe2998c2c0f6221279444cabc08d34d079848c351c1c39ded375d469c25` | 成本、安装、维护、运营功耗的标准开发约束口径 |
| `oiforum.com__OIF-Co-Packaging-FD-01.0.pdf` | `https://www.oiforum.com/wp-content/uploads/OIF-Co-Packaging-FD-01.0.pdf` | 3567968 | `1d614845b92471ae50dd1c6d80a4070515bd4ef369ded9d42fe5e3df4c8457af` | CPO 功耗、密度、可返工性及 optical-engine 功能实例 |

## 复用快照

- `oiforum.com__OIF-CMIS-05.4.pdf`：SHA256
  `cd57ebb1cfb8e0a9e9c7b63862b5b261855e9b77844f4cf85bd36ea3808911db`
- `osfpmsa.org__OSFP_Module_Specification_Rev5_22.pdf`：SHA256
  `c8e80dda50e85b1d4ec96c88642d8a9ed0ed254124f9442f20c51559533850eb`
- `oiforum.com__OIF-Co-Packaging-3.2T-Module-01.0.pdf`：SHA256
  `586d0ed09f2e19d49bf92b23bb681c266d63db6c477d9c8e8c6cd6cf1d6a304f`

复用快照路径均为 `corpus/web/2026-08-23/`。
