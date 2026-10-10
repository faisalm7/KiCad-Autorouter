# Ignored portfolio prototype — not executed on a board

`promotion.patch` proposes exactly three tracked paths: `autorouter/pipeline.py`, `scripts/experiment_portfolio.py`, and `tests/test_portfolio.py`. Nothing here was applied to the checkout. `git apply --check` succeeded against the recorded pipeline base. `draft-manifest.json` binds this proposal; `base.json` binds the original/proposed pipeline contents. Lead review, integration, tests, commit, and push precede any routing.

The pipeline change only adds optional named search-cost presets. Existing callers keep their current engine flags (`scoring_variant=None`). The portfolio explicitly chooses fixed `via_default` 50/5, `via_low` 25/3, and `via_high` 100/10, in that order, using the existing tuned profile and common adapter/native rules. Unknown names or arbitrary user-supplied flags are rejected.

`python3 .runs/baseline-strength-review-001/prototype/verify_draft.py` loads proposal modules only in that process. Eighteen pure controls pass; native stages are explicitly mocked in control-flow tests. These tests establish no native routing correctness or performance.

Actual pinned-JAR reflection was run with Java 256 MiB, network denied, and a 20-second supervisor cap. `profile-probe/result.json` records 539/539 checks across 18 complete settings combinations (three cost variants, three budget allocations, strict/non-strict target policy). Duration 0.705s wall / 1.182s child CPU, 137,871,360-byte peak RSS, successful cleanup. No board was loaded or routing job created. Raw argv, merged values, logs, input SHA256s, and the copied probe code are retained. To reproduce before promotion, choose a new output directory:

```sh
python3 .runs/baseline-strength-review-001/prototype/scripts/probe_portfolio.py --output "$PWD/.runs/baseline-strength-review-001/prototype/profile-probe-next"
```

Budget/selection behavior:

* One 120-second wall and 120-second measured CPU allowance covers source/code verification, setup, every trial, native checks, ranking, consistency checks, and final summary emission. CPU uses invocation `RUSAGE_SELF + RUSAGE_CHILDREN`, without adding nested receipt totals again. CPU is a postcompletion acceptance cap, not OS preemption.
* Before each trial, the remaining allowance is the lesser of wall and CPU remaining, minus 15 seconds for root finalization. The route helper separately keeps its existing 40-second grace/native reserve and rechecks after preparation. Trials may be skipped for insufficient reserves; every launched failed/cancelled trial is retained. Cancellation invalidates delivery rather than returning an old success.
* Every successful trial has its own native report and immutable result receipt. Final selection rechecks all eligible receipts, source/code freeze, exact scoring profile, actual engine argv/process, metrics, and chosen candidate hash. No selected geometry is copied or edited. It therefore retains its original native validation binding; selection does not produce an additional native rerun.
* Selection minimizes `(vias, track length, fixed attempt index)`. The complete Pareto frontier and all trial metrics remain visible; the selected candidate need not dominate every frontier candidate. Fair C comparisons must check that full frontier and grant the same baseline opportunity within C's own total budget.
* `portfolio-summary.json` is explicitly an experimental index, not a pipeline routing receipt. `comparison_eligible` requires global caps and final consistency. Its selected nested receipt charges only its own trial; global CPU/wall remain separate. Application still requires the normal fresh-validation handoff path, not this index.

After reviewed promotion and a new frozen checkpoint, the intended command is `python3 scripts/experiment_portfolio.py --project sonde --output "$PWD/.runs/portfolio-sonde-001"`. This command is not available in the tracked checkout until promotion. No quality result is claimed for the proposal. Independent AI review identified a final-publication cancellation gap; the draft now clears eligibility on cancellation during or immediately after final publication and preserves interrupted partial output. Three regression controls cover final/interim publication cancellation. This is AI review, not human PCB review.
