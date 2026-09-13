Search for one exact 800G single-mode pluggable optical transceiver whose exact product documentation explicitly identifies a silicon-photonics PIC or silicon-photonics transmitter implementation.

This is a strict single-instance source-discovery run. The previous attempt incorrectly combined an Intel 800G 2x400G FR4 OSFP material declaration, an OFC transmitter demonstration covering 2xFR4/DR8, Intel platform-level portfolio statements, and MaxLinear/Jabil partner material into one supposed SKU.

Hard gates:

1. First build a candidate table. Each candidate needs manufacturer, exact model/SKU or exact public family, direct first-party product URL, direct first-party datasheet URL, and an exact first-party sentence binding that product to silicon photonics.
2. Select a candidate only if the product-to-platform binding is explicit and independently retrievable. A portfolio page, family-level platform statement, conference transmitter demo, material declaration, or partner product cannot be inherited by a commercial SKU.
3. If no candidate passes, return exactly `FAIL_NO_SINGLE_INSTANCE` followed by the candidate table and missing binding for each candidate. This is a valid result.
4. Do not combine FR4 and DR8, commercial product and demo, transmitter-only and full transceiver, or sources from different companies.
5. Paid or login-gated paper text may support only title/abstract facts visible publicly. Do not invent section-level quotations from inaccessible full text.
6. Standards support standard requirements only; they do not prove the selected product's DSP, FEC location, connector, lane mapping, receiver, power, or maturity.
7. For every populated product field require source title, publisher, direct URL, page/section/table, and a short quote explicitly tied to the selected instance. Otherwise write `UNKNOWN`.
8. Never infer TIA, detector integration, driver, PIC/EIC integration, mux/demux, coupling, TEC, assembly/test process, commercial maturity, customer adoption, or route service.

If and only if a candidate passes, return:

- selected exact instance and binding quote;
- a conservative field ledger with `SUPPORTED / STANDARD_ONLY / UNKNOWN`;
- source ledger;
- unresolved gaps.

Do not map PQ/TQ/WQ, generate WHY claims, or recommend knowledge-base writes. Current date: 2026-08-26.
