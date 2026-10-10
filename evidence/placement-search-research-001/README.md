# Placement search diagnosis — exposed multichannel case

Independent AI read-only review, 2026-10-10. No native/JVM/router process, download, installation, input edit, or new experiment was performed. Reproduce the saved-data analysis with `python3 -B .runs/placement-search-research-001/analyze.py`. The input receipts, exact endpoint UUIDs, pass history and SHA bindings are in `analysis.json`; primary source URLs and locally rechecked hashes are in `source-receipt.json`. This is a hypothesis for the next baseline experiment, not qualification or a C mechanism.

## What actually failed

Corrected placement pair arm 1 at frozen `73107be01a4e561d68d85a99ef8efab08ce4161c` remains rejected: eight native opens, two clearance errors, 94 warnings, zero exclusions. The opens are on six nets: vbias (three), +12V, Net-(IC4A-OUT), Net-(IC4B-IN-), Net-(IC5A-OUT), and Net-(IC5B-IN-). Three open records name IC2/IC4 pad 5; the others connect pairs of existing routed components. These are not eight wholly unrouted nets.

All **770** final candidate track segments match the SES track multiset exactly after unit/layer/net conversion. The native endpoint UUIDs resolve to original pads or retained engine-derived routes. There is no observed lost-track import explanation. This comparison does not prove electrical connectivity or explain the different counting conventions of nine internal incompletes versus eight native opens; native DRC is authoritative. It does not prove that the original geometry is routable or impossible.

The engine reached its best score (940, nine internal incompletes) at pass 9, then stopped at pass 19 after ten passes without a >0.5 score improvement. It did not reach max_passes=30 or its 60-second internal job timeout; its routing stage took about 20 seconds. The printed list of 24 GND connections describes the **last attempted board before best-history restoration**, not the final saved SES. AutorouteBatchLoop lines 559–579 builds that report before lines 598–624 restore the best board. Treating the GND list as the final native defect list would be wrong.

The pinned engine already has deterministic pass-order diversification and a last-mile rip-up mechanism. The latter requires 1–8 internal incompletes; every logged completed pass here had at least nine, and no last-mile invocation is logged. Raising that threshold would require a separately pinned engine change, not an existing verified CLI option.

The two native clearance failures remain a separate gate: Net-(IC5B-IN-) tracks near the netless RV13 MP pad have reported 0.2994/0.2995 mm clearance against the unchanged 0.3000 mm minimum. Cost changes cannot be presumed to fix this export-geometry issue. Any conservative guidance correction must be fixed and shared across all proposed cost arms, with original native rules unchanged.

## Verified settings and limited alternatives

The engine is Freerouting 2.5.0 JAR SHA-256 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`, source commit `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`.

| Fixed variant | Exact extra arguments | Evidence and interpretation |
| --- | --- | --- |
| Default control | `--router.scoring.via_costs=50 --router.scoring.plane_via_costs=5` | Existing actual-JAR merged-settings probe observed both values. |
| Low via cost, recommended first perturbation | `--router.scoring.via_costs=25 --router.scoring.plane_via_costs=3` | Same actual-JAR probe verified both values. May open different layer/rip-up choices; benefit is unmeasured on this case. |
| High via cost, optional symmetric third control | `--router.scoring.via_costs=100 --router.scoring.plane_via_costs=10` | Same actual-JAR probe verified both values. Useful bounded sensitivity control, not a prediction of superiority. |

The retained actual-JAR probe reports 539/539 checks across 18 profiles and is bound to the same JAR. This review rechecked its receipt and actual-settings hash, without rerunning it. It proves settings merge, not routing effectiveness. RoutingCostSettings lines 33–41 and AutorouteConnectionRouter lines 36–46 show these costs reach maze routing; they do not change DRC constraints.

A later alternative is `--router.scoring.start_ripup_costs=50` (default 100, hold via costs at 50/5). The exact serialized field is in RoutingCostSettings lines 43–51, CLI reflection applies canonical router properties, and the pinned JAR contains the field. AutorouteConnectionRouter multiplies it by pass number; MazeSearchEngine lines 79–80 also derives its random generator seed from that cost. It changes both a rip-up tradeoff and deterministic search behavior. **No actual-JAR merge probe for this new value is retained**: verify that value with the bounded nonrouting profile probe before selecting it. Do not silently add it to the first already-verified three-profile batch.

`STAGNATION_PASS_LIMIT=10`, score threshold 0.5, and last-mile incomplete limit 8 are source constants in BatchAutorouter lines 49–64, not fields in AutorouterSettings. Increasing max_passes alone cannot bypass the observed stop. No public seed or stagnation-limit option was found in the inspected pinned settings/CLI source; do not invent one. AutoroutePassRunner lines 272–311 sorts by net/item, and at stagnation >=2 uses seed `passNo*1000003 + maxNetNumber`. Repeating the identical input and settings does not provide a justified diversity claim. This is not a universal bitwise determinism proof.

## Smallest defensible next experiment

Freeze the common corrected adapter and any separately reviewed conservative clearance guidance first. Keep source, terminal identity, board floors, target widths/vias, no-neckdown/fanout/neck-width settings, optimizer-disabled completion-only profile, engine binary, thread cap, and native acceptance identical. Run default then low via costs as two fresh **independent 120-second wall and 120-second measured-CPU arms**, or add the predeclared high-cost control for three arms. Every arm must include preparation, engine, import/refill, native DRC, all failed attempts and final readback; charge shared setup/selection/publication overhead to each as in the existing pair. Preserve the complete denominator and raw failure metrics. Fewer opens is diagnostic progress, not routing acceptance or route-quality superiority.

This is an exposed-board parameter study. Two/three independent 120-second runs must not be reported as one 120-second portfolio. A later deployment portfolio must give all restarts one rolling 120 wall/CPU budget and include unsuccessful attempts and candidate selection. The current default arm already consumed 59.604769 charged CPU seconds; with the shared helper's 40-second cooperative/native planning reserve, another fully validated attempt is not guaranteed to fit. Three nominal 40-second subcalls leave no engine allowance. Do not silently skip validation to obtain more search time.

Current arm 1 charged totals were 46.451122417 wall / 59.604769 CPU seconds, versus receipt totals sampled before enclosing verification of 36.872887208 / 50.187142. The difference is real overhead and must remain charged. No proposed setting receives hidden extra budget. No reference route was used, no support gate is widened, and no C novelty is claimed.

## Scope limits

Eight opens and two clearance failures remain unresolved. The existing corpus unsupported reasons and genuine-keepout rejection remain unchanged. The source-backed explanation identifies a search stopping condition and candidate perturbations, not a guarantee that costs solve the opens. Native zero-open/zero-blocking acceptance, unchanged rules and full final hash chains are still required for any future accepted result.
