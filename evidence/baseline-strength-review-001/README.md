# Baseline strength review — research, not a benchmark

Read-only AI review on this Mac during quality004. No routing or native KiCad jobs were launched; no production code or historical run was changed. This is an exposed-family research proposal, not evidence that the proposed portfolio improves routing.

## What is actually supported

Pinned Freerouting source commit: `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76` (2.5.0). Download URLs and SHA256s are in `sources.json`, `additional-sources.json`, and the earlier `.runs/optimizer-budget-research-001/sources.json`.

* `BatchAutorouter.java:142` initializes `Random(0)`. `AutoroutePassRunner.java:257–318` normally sorts signal items by net number and item ID; after stagnation it shuffles them with a seed derived from pass number and net count. No public random-seed setting was found in the inspected RouterSettings, AutorouterSettings, or OptimizerSettings. Do not invent a `--seed` argument.
* Saved B2 outputs from quality002 and quality003 contain the same 258 route objects after removing UUIDs and sorting objects. Both normalized geometry digests are `2cafa60313dd05707ee3a1d428aff6ec33ff1d1c4b6896f6038e4f92c82e3ac3`; both have two vias and 786.315536093038 mm of track. Full candidate/result hashes are in `repeated_b2.json`. These runs used the old ineffective internal timeout strings, while external caps were still enforced. They show that identical repeats did not diversify this example; they do not prove all runs deterministic.
* Optimizer `item_selection_strategy` supports `SEQUENTIAL` and `PRIORITIZED`. `BatchOptimizer.java:588–621` uses prioritized ordering only with a nonempty previous-pass result map; the first pass uses the normal coordinate-based order. It is a real option but could be a no-op for an early-stopping board.
* `RoutingCostSettings.java` exposes `via_costs`, `plane_via_costs`, and `start_ripup_costs`. Defaults in `DefaultSettings.java` are 50, 5, and 100. `AutorouteConnectionRouter.java` passes regular/plane via costs into route search; these are heuristic costs, not altered clearance/width rules. `CliSettings.java:116–164` resolves nested router properties through reflection. Actual JAR verification subsequently passed 539/539 checks across 18 settings combinations; see `prototype/profile-probe/result.json`. No routing was executed for that verification.

Primary source entry points:

* [Deterministic routing order](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/pipeline/AutoroutePassRunner.java#L257)
* [Fixed initial random seed](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/pipeline/BatchAutorouter.java#L142)
* [Search cost fields](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/settings/RoutingCostSettings.java)
* [Optimizer ordering](https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/pipeline/BatchOptimizer.java#L588)

## Proposed fixed portfolio

Use up to three attempts, in this predeclared order, from the same stripped immutable source snapshot. All other tuned settings, engine version, adapter, original constraints, neckdown policy, single-worker policy, and acceptance gates stay identical.

| Attempt | Explicit regular via cost | Explicit plane via cost | CLI additions |
|---|---:|---:|---|
| Standard tuned | 50 | 5 | `--router.scoring.via_costs=50 --router.scoring.plane_via_costs=5` |
| Lower via cost | 25 | 3 | `--router.scoring.via_costs=25 --router.scoring.plane_via_costs=3` |
| Higher via cost | 100 | 10 | `--router.scoring.via_costs=100 --router.scoring.plane_via_costs=10` |

These simple symmetric search perturbations are hypotheses, not tuned against a reference route. The no-routing actual-JAR probe has now verified each complete variant argv at three budget allocations and both target policies; original source constraints remain subject to native qualification when routing is eventually run. Retain the raw probe and all attempted routes. Do not call these seeded restarts.

The portfolio gets one 120-second wall deadline and one 120-second measured CPU acceptance cap. It pays for all preparation, engine startup, failed attempts, native checks, candidate copying, selection, and final validation. Before each attempt, use the lesser of remaining wall and remaining CPU allowance, withholding an explicit root-finalization reserve; the existing helper also withholds its 30-second engine grace and 10-second native planning reserve. Only start another attempt if that leaves a positive engine allowance. A two- or three-attempt maximum does not promise all will fit. Splitting into three fixed 40-second calls would fail the current reserve policy and is not the proposal.

Maintain already validated candidates while later attempts run, but never present a candidate accepted by a stale or over-budget receipt. Parent/global accounting must include child CPU exactly once, including preparation and final receipt costs. No parallel competitors. Recheck source staleness and the exact selected receipt inside the same global budget. The implemented draft selects the unchanged native-validated trial candidate without copying or editing it, so it retains that trial's bound native report; any later candidate mutation requires fresh native validation.

Retain the complete baseline Pareto frontier in track length and via count. A simple operational tie policy is fewer vias, then shorter track, then fixed attempt order; report it explicitly and also compare C against every non-dominated baseline, so a chosen scalar cannot hide a stronger B2 candidate. C should receive the same portfolio opportunity within its own equal total budget, with pruning time charged from what remains. Any alternate allocation must be frozen and reported as an ablation. This is the next stronger baseline to test, not a superiority claim.
