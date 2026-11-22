# TQ009 reviewer corrections rereview

Read the prior review you authored and re-check only the corrected draft. Read-only; do not edit or browse.

Corrected files:

- `CONTEXT.md`
- `route-profile-seeds-effective.yaml`
- `adjudication.md`
- `post-adjudication-effective-text.md`
- `candidate-tree.md`
- `route-tradeoff-gate.md`
- `company-placement-pilot.md`
- `next-round-acceptance-contracts.md`

Corrections to verify:

1. candidate schema now has 36 leaves; nominal wavelength and wavelength range are separate;
2. all `placement_class` leaves use `normalized`, with a frozen TQ008 mapping rule;
3. D05 preserves `EML laser` as an unsplit raw instance phrase and does not infer DFB/EAM;
4. TQ010 physical deltas may flow directly to TQ011; TQ014 runs in parallel and only supplements TQ011 with new bottlenecks/validation needs;
5. WQ002 stores the causal relative-value edge; TQ014 stores the conditional comparison card;
6. `capability_match_candidate` remains closed until TQ010/TQ011 produce field-level requirements;
7. TQ010/TQ014 now have draft-only acceptance and stopping contracts;
8. D01 normalized architecture remains UNKNOWN deliberately because the raw `retimed` label lacks Tx/Rx scope; this is conservative, not a promotion.

Mechanical validation already reports: five seeds; 36 leaves each; zero state/missing-field issues; all placement states normalized; 271/271 points close to physical cells; `scan.py --check` all green; `render.py --verify` consistent; canonical diff empty.

Return a concise Chinese verdict: PASS / PASS_WITH_CHANGES / FAIL; any remaining blocker; whether safe for next draft-only TQ010/TQ014 experiment; and an explicit no-approval statement for canonical/coverage/formal RP/company groups.
