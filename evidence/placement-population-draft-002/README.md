# Outcomes002 reporting draft

Ignored draft only; no tracked/public evidence modified and no native/engine jobs executed. The original scaffold and six-control log remain in `review-snapshot-001`. Twelve pure controls now pass in `pure-tests-003.log` (0.090 seconds): the original six helpers plus six groups that create actual synthetic JSON files and exercise the full reporting function. `pure-tests-002-before-fix.log` preserves the newly reproduced 13 failures and one missing-field error against the original scaffold. These are reporting tests, not native evidence.

The generator reads the exact historical outcomes001 index and its pinned dependencies, then overlays the named 14-board support audit by source path and SHA. All 14 rows, prior experiments and production pair outcomes remain. Static support remains 3 eligible / 11 unsupported; accepted production-policy inputs remain 2. Original source board bytes and all read inputs are rechecked before returning JSON. The four added genuine-rule-area reasons do not change eligibility.

Explicit optional inputs:

- Repeat `--fixture-result EXISTING_CANONICAL_RESULT.json` to include each failed or accepted owned control. Full canonical receipts are retained, including costs, metrics, candidate identity and failure details. A pre-engine failure need not contain native fields. Owned fixtures remain outside the corpus denominator. An accepted fixture must have a consistent accepted status, clean native findings/counters, a required via and consistent recorded wall/CPU budgets.
- Supply `--pair-summary EXISTING_CANONICAL_SUMMARY.json` only after the pair exists. Adjacent protocol and both canonical arm receipts follow the fixed harness layout and their recorded SHA256 values must match. Missing explicit inputs fail; no automatic newest-run discovery occurs.
- Without a pair, all 14 boards remain unevaluated for this comparison. An invalidated, failed or cancelled pair cannot contribute accepted-input counts, gains or losses, even when earlier arm receipts contain successful diagnostics. A completed, eligible pair with two rejected native outputs is a recorded tie-invalid, not an unavailable pair.

For an eligible pair, acceptance, status, native counters, length and via counts are cross-checked against each canonical arm receipt. Whole source inventories, code/helper/tool freezes and assigned budgets must agree with the pair protocol; the accepted fixture must match its frozen code/tool and original fixture inventory. Invocation costs cannot undercount arm costs, every arm pays all shared overhead, and charged wall/CPU remain at most 120 seconds. Stored comparison deltas must agree. No gain can be inferred solely from unchecked summary verdicts. Length/via comparisons require both outputs accepted.

The output separates production outcomes/counts from placement diagnostic outcomes/counts. No placement production promotion, C novelty or tuned-B2 superiority follows. This reporting code does not import the native pipeline, run the actual check-result command, authenticate arbitrarily rewritten histories, or replace the lead's current native receipt audit.

Six stored-receipt test groups cover an early fixture failure without native fields; gain/loss/valid and invalid ties; invalidated pairs retaining historical arm results without a gain; summary/native verdict/status/counter/length/via mismatches; false accepted fixture status/findings/costs; and source/project/code/tool/budget/invocation inconsistencies. Existing helpers separately reject truthy non-Booleans, duplicate/nonfinite JSON, invalid costs and missing explicit paths.

Actual read-only reporting control (no pair):

```text
python3 -B .runs/placement-population-draft-002/generate.py --fixture-result .runs/placement-routing-fixture-001/result.json --fixture-result .runs/placement-routing-fixture-002/result.json
```

The retained `actual-fixtures-only-index.json` / `actual-fixtures-only-readback.json` keep fixture001 rejected before native routing (3.013809875 wall / 1.957058 CPU seconds), and fixture002 accepted (8.577736375 wall / 5.535336 CPU seconds; 1 via). This is reading the lead's stored actual evidence, not rerunning it. Population remains 14 / 3 / 11, production accepted-input count 2, placement diagnostic count 0, and pair pending at that invocation. No nonexistent future pair was supplied.

After the lead reviews actual pair evidence, create a new immutable `evidence/development-outcomes-002` snapshot containing this exact generator, resulting index and fresh files.json; preserve outcomes001. `stale-reference-suggestions.json` provides exact old/new replacements for historical REQUIREMENTS/coverage references and source-file hashes. Review those hashes before applying suggestions. Result-dependent STATUS/PLANS/claims/diagnostic-table edits must wait for the actual pair, include both arms and full costs, and retain earlier unmatched full-board attempts as historical exploration.

No 30–50-family, untouched-holdout, general keepout-enforcement, GUI or physical/electrical claim follows. Current source restrictions remain unchanged.

Later actual pair readback: after the lead supplied the completed canonical `.runs/placement-routing-pair-001/summary.json`, the same generator ran with both fixture results and that pair. `actual-pair-index.json` and `actual-pair-readback.json` retain the outcome: both arms rejected, tie-invalid, no gain/loss or length/via quality delta. Native counters are floor 160 opens / 1 blocking / 94 warnings / 0 exclusions and placement 8 / 2 / 94 / 0. Charged wall/CPU seconds are 65.278253125 / 72.920478 versus 46.451122417 / 59.604769. This is an exploratory B1 adapter diagnostic; the extra blocking finding is retained, not hidden by the reduction in open connections. Population remains 14 / 3 / 11, production accepted-input count 2, diagnostic accepted count 0. This second invocation also only read stored files and did not run native tools.

```text
python3 -B .runs/placement-population-draft-002/generate.py --fixture-result .runs/placement-routing-fixture-001/result.json --fixture-result .runs/placement-routing-fixture-002/result.json --pair-summary .runs/placement-routing-pair-001/summary.json
```
