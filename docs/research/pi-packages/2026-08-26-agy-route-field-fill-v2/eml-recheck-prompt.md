Audit one exact Coherent 800G EML pluggable transceiver instance using Gemini 3.7 Flash search capabilities.

Start with these public first-party candidate sources, but verify every URL before using it:

- Coherent product family `FTCE4527E1PxA-2N`
- Official PDF likely named `ftce4527e1pxa-2n-transceiver-ds.pdf`

This is a correction run. The prior answer may have omitted the `-2N` suffix, confused DR8+ with 2x400G DR4+, contradicted the heatsink code, inferred commercial maturity from certifications, misread TDECQ as TEC evidence, and invented undisclosed internal assembly details.

Hard rules:

1. Resolve the exact selectable SKU syntax. If only a configurable family is public, state `EXACT_ORDERABLE_SKU_UNKNOWN` and retain the family string exactly.
2. Use only Coherent first-party product pages and PDFs for product facts. Standards may be used only for separately labeled standard requirements.
3. Do not infer GA, mass production, active ordering, internal TEC, TOSA/ROSA, array topology, lens coupling, driver/TIA, FEC location, factory-test coverage, or heatsink construction unless the exact source says so.
4. TDECQ means transmitter and dispersion eye closure for PAM4; it is not evidence for a thermoelectric cooler.
5. Treat `Preliminary Product Specification` as preliminary. Regulatory certification does not prove production maturity.
6. Every supported field must include exact source title, publisher, direct retrievable URL, PDF page/section/table, and a short quote. If any anchor piece is missing, mark the field `UNKNOWN`.
7. Do not use authorized distributors, search snippets, cached summaries, or a different connector/heatsink variant to fill fields.

Return only:

- exact-instance resolution;
- a field ledger with `SUPPORTED / STANDARD_ONLY / UNKNOWN / CONTRADICTED`;
- a contradiction ledger;
- unresolved gaps;
- source list.

Do not map PQ/TQ/WQ, do not assess company route service, do not create WHY claims, and do not recommend knowledge-base writes. Current date: 2026-08-26.
