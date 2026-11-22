# AGY search: why SiPh within an 800G DR8 LPO route

Use only Google search and public first-party sources: standards/MSAs, official product pages, foundry/platform owner pages, official technical papers or investor filings. Do not use media, brokers, distributors, reposts, or generated summaries as evidence.

Model task: determine whether upstream requirements for an `800G DR8 LPO, 8x100G-class, 500m SMF, front-panel pluggable` route actually imply Silicon Photonics rather than EML or TFLN. Treat `LPO/retimed` as an electrical-architecture axis and `SiPh/EML/TFLN` as a photonic-platform axis unless direct evidence proves coupling.

Find at most 10 atomic evidence cards. For each card provide:

1. exact first-party URL and document title;
2. publisher and publication/revision date if stated;
3. exact section/page/line anchor;
4. quotation no longer than 20 words;
5. `supports` and `does_not_support`;
6. evidence stage: specification / official platform statement / exact product observation / company claim;
7. causal role: upstream_constraint / platform_mechanism / conditional_advantage / platform_limit / counterevidence.

Required questions:

- Does an LPO specification require SiPh, or can it use multiple optical platforms?
- What first-party evidence supports SiPh integration, lane density, wafer-scale manufacturing/test, known-good-die, or volume maturity?
- What first-party evidence establishes EML as an InP monolithic DFB+EAM alternative and any performance/application boundary?
- Is there any controlled, like-for-like first-party comparison of SiPh versus EML/TFLN for 800G DR8 LPO? If absent, say `NO_CONTROLLED_COMPARISON_FOUND`.
- State the narrowest defensible WHY candidate. Never write “LPO therefore SiPh” without direct evidence.

Reject product-family merging, cross-company component inheritance, fixed percentage advantages without a controlled baseline, and any claim based only on search snippets.
