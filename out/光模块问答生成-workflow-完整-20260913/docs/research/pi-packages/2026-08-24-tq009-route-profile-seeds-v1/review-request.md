# Reviewer request: TQ009 Route Profile Seeds + trade-off hinge

Please perform a read-only architecture/domain/evidence review. Do not edit files, do not browse the web, and do not propose canonical promotion.

Read these files completely:

1. `CONTEXT.md` glossary section for Physical/Technology Route/Route Profile Seed/Company Attachment/Why/Conditional Trade-off Hinge;
2. `docs/research/pi-packages/2026-08-24-tq009-route-profile-seeds-v1/README-FIRST.md`;
3. `contract.md`, `source-discovery.md`, `adjudication-round1.md`, `contract-round2-atomic.md`, `raw-output-round2.md`, `adjudication.md`;
4. `route-profile-seeds-effective.yaml` and `post-adjudication-effective-text.md`;
5. `candidate-tree.md`, `route-tradeoff-gate.md`, `company-placement-rules.md`, `company-placement-pilot.md`;
6. upstream `docs/research/pi-packages/2026-08-24-tq005-tq008-axis-values-v1/post-adjudication-effective-text.md`;
7. frozen question definitions in `docs/plans/2026-08-research-question-tree-v2.md` around TQ001–TQ014 and WQ001–WQ004.

Do not read `archive/`.

Review questions:

1. Is the model still exactly two knowledge systems, with Why as bridge and companies as unique external entities?
2. Is the user's new insight modeled correctly: upstream constraints/bottlenecks/profile/physical changes generate conditional advantages/disadvantages; downstream questions arise from those trade-offs; new bottlenecks feed back to TQ003?
3. Is TQ014 correctly used without changing frozen QIDs/parents? Should any dependency/order be changed before the next research round?
4. Are 35 atomic seed fields sufficient, missing an essential field, or over-modeled? Check the two semantic corrections carefully.
5. Did any seed still infer from DR8, DSP, EML, SiPh, form factor, adjacent demos, or interoperability?
6. Is company placement correctly blocked until TQ010/TQ011, and is `route_service_evidence` correctly separated from capability match and supply observations?
7. Does the candidate structure genuinely grow from “what is an optical module?” into physical knowledge, route choices, conditional trade-offs, capabilities, and companies?
8. Identify any likely outsider/domain-modeling errors, hidden circularity, missing acceptance contract, or premature abstraction.

Return:

- verdict: PASS / PASS_WITH_CHANGES / FAIL;
- blockers;
- non-blocking corrections;
- assessment of the trade-off hinge (upstream inputs, downstream outputs, feedback loop);
- assessment of the 35-field atomic schema;
- explicit answer whether this draft is safe to use for the next **draft-only** TQ010/TQ014 experiment;
- explicit statement that no canonical/coverage/formal RP/company group is approved.
