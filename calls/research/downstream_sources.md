# Downstream source audit: NVIDIA, Arista, Meta

Audit date: `2026-08-06`

Scope: source research only. This note does not change the canonical call-ledger CSVs. It uses the latest four **disclosed** quarter slots as of the audit date. Accordingly, Arista and Meta should roll forward to `2026Q2 / 2026Q1 / 2025Q4 / 2025Q3`; their old `2025Q2` placeholders should leave the active four-quarter window. NVIDIA's latest disclosed quarter remains `FY2027Q1`.

All quarterly sources below are stable first-party IR or SEC exhibits and therefore qualify as grade `A`. `accessed_date` is `2026-08-06` throughout. Quotes are deliberately short and anchors identify the nearby heading or PDF page/line.

## NVIDIA (`NVDA`)

### Four-quarter source window

| proposed source_id | quarter | period_end | published_date | material_type | grade | stable URL | short quote | anchor |
|---|---|---:|---:|---|---|---|---|---|
| `S_NVDA_2026Q1` | `FY2027Q1` | 2026-04-26 | 2026-05-20 | `earnings_release` | A | https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2027/default.aspx | “Data Center networking revenue was a record $14.8 billion” | `Data Center`, immediately before `Q1 Fiscal 2027 Summary` (HTML lines 117-120) |
| `S_NVDA_2025Q4` | `FY2026Q4` | 2026-01-25 | 2026-02-25 | `earnings_release` | A | https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/ | “large-scale deployment of NVIDIA CPUs, networking and millions of NVIDIA Blackwell and Rubin GPUs” | `Highlights > Data Center`, Meta partnership bullet (HTML line 190) |
| `S_NVDA_2025Q3` | `FY2026Q3` | 2025-10-26 | 2025-11-19 | `earnings_release` | A | https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Third-Quarter-Fiscal-2026/ | “Meta, Microsoft and Oracle will boost their AI data center networks” | `Highlights > Data Center`, Spectrum-X bullet (HTML line 154) |
| `S_NVDA_2025Q2` | `FY2026Q2` | 2025-07-27 | 2025-08-27 | `earnings_release` | A | https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2026/default.aspx | “Spectrum-XGS Ethernet to connect distributed data centers” | `Highlights > Data Center` (HTML lines 150-152) |

Optional A-grade call material for reviewed management claims:

- `S_NVDA_2026Q1_CALL`: https://s201.q4cdn.com/141608511/files/doc_financials/2027/q1/NVDA-Q1-2027-Earnings-Call-20-May-2026-5_00-PM-ET.pdf (`webcast_transcript`; hosted from NVIDIA IR's q4cdn; corrected transcript; anchor `Management Discussion`, PDF pp. 3-4).
- `S_NVDA_2025Q4_CALL`: https://s201.q4cdn.com/141608511/files/doc_financials/2026/q4/NVDA-Q4-2026-Earnings-Call-25-February-2026-5_00-PM-ET.pdf (`webcast_transcript`; anchor `Management Discussion`, PDF p. 4, and Jensen answer on pp. 9-10). The analyst question begins at PDF p. 9 and must not be captured as a claim.
- `S_NVDA_2026Q1_CFO`: https://www.sec.gov/Archives/edgar/data/1045810/000104581026000051/q1fy27cfocommentary.htm (`prepared_remarks`; A; SEC Exhibit 99.2; anchor `Data Center`).

### Reviewed-claim candidates

1. **Colette Kress, CFO; management; fact.** Spectrum-X was described as larger than all Ethernet networking peers combined, while InfiniBand grew more than fourfold year over year. Short quote: “Spectrum-X ... is now larger than all Ethernet network peers combined.” Anchor: Q1 FY27 corrected transcript, PDF p. 3, management discussion. This supports broad AI-Ethernet adoption, not optical-module demand by itself.
2. **Colette Kress, CFO; management; fact.** Data Center networking revenue was about $15 billion and nearly tripled year over year. Short quote: “Data Center networking revenue of $15 billion nearly tripled year-over-year.” Anchor: Q1 FY27 corrected transcript, PDF p. 3. This is a strong networking-demand datapoint but combines Ethernet, InfiniBand and NVLink.
3. **Colette Kress, CFO; management; fact.** Spectrum-X scale-up/scale-across momentum was tied to customers joining distributed sites into giga-scale AI factories. Short quote: “Momentum is strong with our Spectrum-X Ethernet scale up and scale across networking.” Anchor: Q4 FY26 corrected transcript, PDF p. 4, management discussion.
4. **NVIDIA corporate release; corporate_author; technical_claim / adoption fact.** Q1 FY27 disclosed strategic agreements with Coherent, Corning and Lumentum to accelerate advanced-optics innovation. Anchor: Q1 FY27 earnings release, `Highlights > Data Center`, HTML lines 156-157. Do not label this one `management`; it is useful as a downstream/supply-chain cross-check.

**Boundary:** the earnings-call evidence strongly validates AI networking deployment and the scale-up/scale-out/scale-across architecture. It does **not** isolate 800G/1.6T pluggable volumes, laser demand, or CPO production. NVIDIA's March 2025 photonics launch is technically explicit, but it lies outside these four quarterly calls; it can be a separate official technical/commitment source, not proof that CPO shipment volume was realized in the audited window.

## Arista Networks (`ANET`)

### Four-quarter source window

| proposed source_id | quarter | period_end | published_date | material_type | grade | stable URL | short quote | anchor |
|---|---|---:|---:|---|---|---|---|---|
| `S_ANET_2026Q2` | `2026Q2` | 2026-06-30 | 2026-08-04 | `earnings_release` | A | https://www.sec.gov/Archives/edgar/data/1596532/000159653226000174/ex991q226-earningsrelease.htm | “Introduced 1.6 Tbps AI fabric platforms” | Exhibit 99.1, opening bullets; filed company highlights |
| `S_ANET_2026Q1` | `2026Q1` | 2026-03-31 | 2026-05-05 | `earnings_release` | A | https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-First-Quarter-2026-Financial-Results/default.aspx | “XPO reduces networking racks by up to 75%” | `Company Highlights`, XPO bullet |
| `S_ANET_2025Q4` | `2025Q4` | 2025-12-31 | 2026-02-12 | `earnings_release` | A | https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Fourth-Quarter-and-Year-End-2025-Financial-Results/default.aspx | “We exceeded both our AI networking and campus expansion goals” | CEO quote directly below dateline |
| `S_ANET_2025Q3` | `2025Q3` | 2025-09-30 | 2025-11-04 | `earnings_release` | A | https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2025/Arista-Networks-Inc--Reports-Third-Quarter-2025-Financial-Results/ | “well-positioned as a strategic networking provider” | CEO quote directly below dateline |

`S_ANET_2025Q2` should be removed from the active four-slot window; it is superseded by `S_ANET_2026Q2`.

Optional grade-C complete transcript for speaker-level claims:

- `S_ANET_2026Q1_CALL`: https://www.fool.com/earnings/call-transcripts/2026/05/05/arista-anet-q1-2026-earnings-transcript/ (`transcript`; C; anchor `Full Conference Call Transcript`, Jayshree Ullal prepared remarks, HTML lines 89-102). The Q&A begins later; analyst questions are excluded.

### Reviewed-claim candidates

1. **Jayshree Ullal, CEO; management; fact.** Arista had more than 100 cumulative customers in 800GbE deployments. Short quote: “greater than 100 cumulative customers ... in 800 gigabit Ethernet deployments.” Anchor: Q1 2026 transcript, prepared remarks, HTML line 95.
2. **Jayshree Ullal, CEO; management; forward_looking.** Management expected 1.6T to enter production-scale deployments in 2027. Short quote: “expect the addition of 1.6 terabit in 2027 at production scale.” Same anchor as claim 1.
3. **Jayshree Ullal, CEO; management; forward_looking.** Scale-up was positioned as a 2027-and-beyond entry using co-packaged copper or open CPO, while XPO was described as a long-lived bridge for higher-speed scale-out/scale-across. Short quote: “XPO has a ten-year run.” Anchor: Q1 2026 transcript, prepared remarks line 93 and management answer line 241; keep the analyst question separate.
4. **Arista corporate release; corporate_author; technical_claim.** The Q2 2026 7060XE7 family supports 1.6T and LPO, claiming about 60% lower interconnect power than traditional pluggables. Anchor: SEC Exhibit 99.1, `Company Highlights`. This is not a named management claim and must use `corporate_author`.

**Boundary:** Arista supplies unusually direct evidence for 800G deployment breadth, a 2027 production-scale 1.6T timetable and the coexistence path among OSFP/XPO/CPO. The Q2 release confirms product availability/specification, not customer volume, field reliability, or realized LPO/CPO shipments. It also does not identify laser/EML suppliers.

## Meta Platforms (`META`)

### Four-quarter source window

| proposed source_id | quarter | period_end | published_date | material_type | grade | stable URL | short quote | anchor |
|---|---|---:|---:|---|---|---|---|---|
| `S_META_2026Q2` | `2026Q2` | 2026-06-30 | 2026-07-29 | `earnings_release` | A | https://www.sec.gov/Archives/edgar/data/1326801/000162828026050596/meta-06302026xexhibit991.htm | “Capital expenditures ... were $31.08 billion” | Exhibit 99.1, `Operational and Other Financial Highlights`, line 29 |
| `S_META_2026Q1` | `2026Q1` | 2026-03-31 | 2026-04-29 | `earnings_release` | A | https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/ | “additional data center costs to support future year capacity” | `CFO Outlook Commentary`, HTML lines 150-157 |
| `S_META_2025Q4` | `2025Q4` | 2025-12-31 | 2026-01-28 | `earnings_release` | A | https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Fourth-Quarter-and-Full-Year-2025-Results/ | “increased investment to support our Meta Superintelligence Labs efforts” | `CFO Outlook Commentary`, HTML lines 180-189 |
| `S_META_2025Q3` | `2025Q3` | 2025-09-30 | 2025-10-29 | `earnings_release` | A | https://investor.atmeta.com/investor-news/press-release-details/2025/Meta-Reports-Third-Quarter-2025-Results/ | “A central requirement ... is infrastructure capacity” | `CFO Outlook Commentary`, HTML lines 167-171 |

`S_META_2025Q2` should be removed from the active four-slot window; it is superseded by `S_META_2026Q2`.

Optional A-grade official call transcript:

- `S_META_2026Q1_CALL`: https://s21.q4cdn.com/399680738/files/doc_financials/2026/q1/META-Q1-2026-Earnings-Call-Transcript.pdf (`webcast_transcript`; A; linked directly by Meta IR; management discussion is PDF pp. 1-8 and Q&A begins on p. 9).

Independent, official adoption cross-check (not a Meta quarterly slot):

- https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Spectrum-X-Ethernet-Switches-Speed-Up-Networks-for-Meta-and-Oracle/default.aspx (`official_release`; A; 2025-10-13). Meta VP Gaya Nagarajan says Meta is integrating Spectrum Ethernet into Minipack3N and FBOSS. This validates an Ethernet-switch architecture choice, **not** a particular optical module or CPO deployment.

### Reviewed-claim candidates

1. **Susan Li, CFO; management; fact.** Q1 capital spending included servers, data centers and network infrastructure. Short quote: “investments in servers, data centers, and network infrastructure.” Anchor: Q1 2026 official transcript, PDF p. 4, management discussion.
2. **Susan Li, CFO; management; forward_looking.** Meta was expanding its owned data-center footprint and using supply-chain agreements to secure future components. Short quote: “substantially expanding our own data center footprint.” Anchor: Q1 transcript, PDF pp. 7-8, management discussion.
3. **Susan Li, CFO; management; forward_looking.** Multi-year cloud deals were scheduled to add capacity during 2026 and 2027. Short quote: “cloud deals ... come online over ... this year and 2027.” Same anchor as claim 2.
4. **Meta corporate representative (Gaya Nagarajan, VP Networking Engineering); corporate_author / technical_claim.** Meta disclosed integration of NVIDIA Spectrum Ethernet into Minipack3N and FBOSS for next-generation AI infrastructure. Anchor: NVIDIA official release dated 2025-10-13, Meta quotation. This is direct downstream adoption evidence for Spectrum Ethernet, but not management-call evidence and not optical confirmation.

**Boundary:** Meta's four earnings windows consistently establish a rapid data-center/network-capacity build and future component procurement. They do not name 800G, 1.6T, pluggable optics, CPO, LPO, OCS, lasers or module vendors. The Spectrum Ethernet disclosure confirms a switching-platform adoption only. Therefore Meta should remain `insufficient` for optical-route validation; generic capex must not be promoted into an optics-demand claim.

## Cross-company read-through

- **Strong downstream validation:** Arista supplies direct 800G installed-customer breadth and a concrete 1.6T production timetable. NVIDIA supplies strong Ethernet/network revenue and distributed-AI-factory deployment evidence.
- **Architecture evidence, not component evidence:** NVIDIA's Spectrum-X and Meta's Minipack3N/FBOSS disclosures validate accelerated Ethernet adoption, but neither identifies transceiver technology, laser source, module vendor, CPO attach rate or OCS usage.
- **CPO/LPO status:** Arista's statements place open CPO in a 2027-and-beyond scale-up path and XPO as a bridge at 1.6T/3.2T; the Q2 product release adds an LPO-capable 1.6T platform. This supports technical feasibility/roadmap, not mature field deployment.
- **No false optical confirmation:** Meta's capex and capacity statements remain a broad demand backdrop only. They should not independently validate Coherent/Lumentum/AAOI optical capacity claims.
- **Analyst isolation:** none of the recommended reviewed claims is an analyst question. Where a management answer is used, the anchor explicitly begins at the named executive's response.
