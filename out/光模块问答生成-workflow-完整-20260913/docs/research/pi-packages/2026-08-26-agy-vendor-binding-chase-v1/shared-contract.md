# AGY exact-entity product-to-platform binding contract

You are performing source discovery, not knowledge synthesis. Use Gemini 3.7 Flash search capabilities.

For one named company only, investigate whether a public first-party source explicitly binds one exact 800G single-mode pluggable product or exact public product family to a silicon-photonics transmitter/PIC implementation.

Required procedure:

1. Log every executed query string verbatim with retrieval date 2026-08-26.
2. Search the company's official domain first. Then search official press releases, first-party conference materials, and official regulatory/IR documents. Third-party pages may be listed only as leads.
3. Resolve exact product string, URL, page title, document date/version, product vs demo status, and accessibility.
4. A binding passes only if one retrievable first-party sentence contains or unambiguously connects the product/family and SiPh/silicon photonics/PIC implementation.
5. Corporate platform capability, brand names, a separate demo, distributor text, supplier announcement, or a different SKU cannot bind the target product.
6. If full text is gated, record `PUBLICLY_UNVERIFIABLE`; do not paraphrase inaccessible sections.
7. If no binding passes, return `FAIL_NO_BINDING_IN_THIS_SEARCH`. This is a search result only, not a claim that the company has no such product.
8. A negative result requires a reproducibility trail: queries, target pages, URLs, access result, and why each failed the gate. Without that trail, return `INCOMPLETE_SEARCH`, not FAIL.

## Post-review amendment: exact-product-page binding

For this draft-only package, a first-party exact product page may pass at `exact_product_page_binding` level when all of the following are true:

1. the page title explicitly names the route/platform label (for example `硅光模块`);
2. the body or metadata on that same page names one exact product string;
3. the page has a single unambiguous product subject;
4. no separate page, adjacent SKU, brand slogan, or corporate capability statement is needed to make the connection.

This is weaker than a single-sentence exact-SKU binding. It proves only a public product listing and must not prove GA, mass production, shipment, customer adoption, or internal implementation. If an English counterpart omits the route/platform label, retain that asymmetry as a source limitation; do not erase the first-party Chinese-page claim or upgrade its strength.

Output only:

- target identity resolution;
- query trail;
- first-party source cards;
- candidate binding sentences with `PASS / FAIL / PUBLICLY_UNVERIFIABLE`;
- final search status;
- remaining next query, if any.

Do not output PQ/TQ/WQ mapping, maturity inference, customer adoption, route service, route advantages, WHY links, company groups, or knowledge-base recommendations.
