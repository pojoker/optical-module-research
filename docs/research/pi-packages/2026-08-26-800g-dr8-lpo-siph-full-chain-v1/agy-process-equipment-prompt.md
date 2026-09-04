# AGY search: SiPh LPO manufacturing and equipment deltas

Use only public first-party sources: silicon-photonics platform/foundry owners, module/component makers, production/test-equipment makers, standards/MSAs, official technical papers and filings. No media, brokers, distributors, reposts, or generic AI summaries.

Target route: `800G DR8 LPO + SiPh + front-panel pluggable`. Baseline: `800G DR8 retimed pluggable`; optical platform of baseline is unknown. Do not invent a comparative delta when the baseline platform or target internal design is undisclosed.

Find atomic evidence for these layers:

- SiPh PIC wafer fabrication/integration;
- laser integration or external-laser attachment;
- wafer-level optical/electrical test, burn-in, known-good-die;
- die attach, flip-chip/wirebond, fiber attach/active alignment, packaging;
- module calibration and end-to-end linear-channel testing;
- equipment-provider capabilities that directly serve one of those steps.

For each card provide exact URL/title/publisher/date, section/page anchor, <=20-word quote, object level (platform/process/equipment/product), maturity stage, supports, does_not_support, and whether it is:

- `target_necessary_by_specification`
- `SiPh_platform_typical`
- `company_specific_implementation`
- `test_ecosystem_only`
- `unknown_comparative_delta`

Never infer that a named tool is used on Hyper Photonix's line. Never turn a demo instrument into a production requirement. If no first-party source proves a target-vs-baseline manufacturing or equipment change, output `NO_TARGET_SPECIFIC_DELTA_FOUND` and retain UNKNOWN.
