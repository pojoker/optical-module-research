# AGY source search: downstream physical changes and company evidence

Use Gemini 3.7 Flash web search. Source discovery only.

Target route: 800G DR8 LPO silicon-photonics front-panel pluggable, compared with an 800G DR8 retimed pluggable baseline.

Find public primary sources that explicitly support downstream consequences at five levels:

1. components: DSP/CDR/driver/TIA/PIC/laser/detector changes or UNKNOWN;
2. interfaces: host electrical channel, optical lane/fiber/connector, management and FEC responsibility;
3. process: integration, assembly, calibration or manufacturing changes;
4. equipment: production/test equipment changes, only when explicitly stated;
5. tests: host-module interoperability, link training, BER/FEC, electrical/optical compliance, thermal/power validation.

Then find company-level direct route evidence for the same route and classify only as `demo`, `listed_product`, `shipment`, or `customer_adoption`. Search Hyper Photonix/芯速联, Eoptolink/新易盛, InnoLight/中际旭创, and at most two additional companies, one company per evidence card.

For each candidate provide exact query, first-party URL, title/date/version, page/section, short quote, exact evidence subject, stage, and limitations. Do not infer manufacture, shipment, customer, internal components, process, equipment, or test steps from a product name.

No QID mapping, company groups, winner ranking, WHY links, canonical write, or generated synthesis as evidence.
