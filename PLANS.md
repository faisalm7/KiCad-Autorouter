# Execution plan

Active specification: `MASTER_PROMPT.md`, read completely October 9, 2026. The selected local checkout and existing `rebuild/local-20261010-015447` branch remain the integration location.

## Completed evidence and decisions

1. **G0:** Initial and subsequent checkpoint pushes and independent remote read-backs passed. An actual bundle and non-Git archive at `7fef467` were restored and checked on this Mac. Receipts are in `evidence/backups`. Off-Mac preservation of private raw artifacts awaits an owner-selected destination.
2. **G1:** The pinned KiCad/Freerouting pipeline produced a licensed native-validated route. Fourteen real native positive/negative controls passed their expected outcomes. Sources, original rules, native refill/connectivity and candidate hashes participate in acceptance.
3. **G2, narrow scope:** The frozen five-arm sonde ablation reproduced the graphics and plane failure mechanisms. Only combined B1 passed routing acceptance; it retained one warning. Independent artifact review verified bindings and accounting. Receipt/setup boundary flaws were reproduced and fixed. Early smoke/stock records remain provisional because their code snapshots are incomplete.
4. **Initial G3 work:** Six licensed projects, seven boards and their complete originals/notices were acquired and hash-verified. Static coverage now retains seven: two eligible, five unsupported; the new multiclass path still requires native routing qualification. Family independence is unverified. Two KRT spikes failed preservation or native validation; these results favor fixing measured geometry/interchange gaps before adding complexity.
5. **Narrow G5 GUI observation:** PCB Editor opened a disposable B1 project copy and performed native refill/DRC: 0 errors, 0 opens, 25 library-disabled warnings, 0 exclusions. Discard preserved board bytes but changed disposable project metadata and created history/preferences. This supports a separate-copy review workflow; it does not qualify automated application or undo. The CLI `review-copy` completed an actual end-to-end check on accepted C pilot 001.

## Active and next work

1. **Improve and broaden the strategy comparison.** Corrected pilot 002 completed: C is shorter than B2 but uses one extra via; overall superiority remains unproved. Next test a tuned incumbent for C, retaining all previous outcomes. Freeze the code, hypothesis, planned 120-second wall / 120-second measured CPU caps, and selection policy before measurement. Include B0, B1 and equal-budget B2, count conversion, validation, restarts and selection costs, and retain rejected outputs. Test an ablation that distinguishes the proposed mechanism from the adapter. A failed or neutral result requires revising the hypothesis, not relabeling B1 as C.
2. **Checkpoint and preserve current evidence.** Audit explicitly staged project-owned files and newly exposed history, push without rewriting history, then verify remote SHA and a file independently. Create and restore-test a new bundle/raw archive after the checkpoint. The `7fef467` archive does not cover later runs. Keep downloaded engines, bulk datasets and private references outside public Git; small public evidence requires explicit rights/content audit.
3. **Expand representative development coverage.** Keep the current seven-board denominator and unsupported reasons. Qualify legitimate netclass, pad, version and project-binding support with native controls before broadening the gate; never modify originals or relax rules to admit a board. Acquire further licensed projects toward the required 30–50-family audit, include baseline successes, deduplicate ancestry and reference routes, and keep exposed data out of a future holdout. The multichannel variants remain one family despite placement differences.
4. **Complete G2 and G4 evidence.** Broaden validation controls for remaining supported constraints, failed refill, stage-specific cancellation and application boundaries. Compare the strongest justified mechanism with B0/B1/B2 under equal total budgets across eligible development families. Report gains, losses, failures, unsupported cases and usable quality among valid candidates. Neither the current one-family adapter gain nor rejected KRT lengths establish superiority.
5. **G5 integration.** Retain the completed CLI review-copy check and qualify installation and failure recovery. Preserve the observed separate-project GUI workflow and its configuration differences. Test stale editor state, undo/application and cancellation on the real GUI before claiming those capabilities. Receipt checking alone does not apply a board. Keep unsupported advanced constraints and selected-net routing explicit.
6. **G6 learning decision.** Current evidence does not justify training. Revisit only if the larger failure audit identifies a learnable, licensed and measurable gap. Compare against a non-learning baseline and account for training/data cost if learning is introduced.
7. **G7 confirmatory evaluation.** After development decisions stabilize, freeze code/protocol and a genuinely untouched family-disjoint set. Run once, retain the full population, compute paired outcomes and limitations, and obtain skeptical review. The existing AI reviews are useful defect finding, not human PCB or physical validation.
8. **G8 handoff and release preparation.** Complete fresh-install, demo/test/benchmark entry points, notices, package tests, failure examples and current restore receipts. Prepare an honest local release candidate and owner-facing continuation. Formal public releases/packages, external spending and physical fabrication need separate authorization.

## Execution limits and entry points

Use one heavy worker, sequential competing engines, bounded runs and a 10 GiB project cache/data ceiling. Existing adapter/KRT runs used 120-second pipeline budgets. Preserve failed runs and never reuse their directories. Resource polling has limits and is not an OS memory sandbox. Use no paid services or background/auto-resume loops; do not silently upgrade KiCad or change global preferences.

Existing entry points, run only when the lead has no competing native job:

```sh
python3 -m autorouter doctor
python3 data/fetch.py --verify
python3 -m unittest discover -s tests -v
python3 -m autorouter check-result .runs/adapter-ablation-001/combined/result.json
```

`scripts/experiment_adapter.py --output NEW_RUN_DIRECTORY` repeats the five-arm development ablation using the then-current code. `scripts/experiment_krt.py --output NEW_RUN_DIRECTORY` runs the native-engine spike; `--pretty-input` selects the semantically equivalent formatted input. New runs are separate evidence, not replacements for the frozen results. `python3 scripts/backup.py` creates a checkpoint archive and verifies an actual local restoration; use `--verify RECEIPT` to restore-check a named existing receipt. Record exact commands and new paths for each completed experiment.
