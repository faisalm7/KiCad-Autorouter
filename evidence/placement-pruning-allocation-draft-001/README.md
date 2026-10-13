# Explicit standard incumbent and individual-first pruning allocation

Frozen ignored source proposal only. ROOT owns integration, committed helpers, actual sequential native execution and readback. No tracked edits, native/JVM/Git/network activity or delegation occurred in this task.

The unchanged legacy `ps.prune(source, output, seconds)` path retains its tuned incumbent, schema1 contract, whole-net-first order and15-second work reserve. Its contract serializes to the exact existing pair002 SHA `e2f71244b7f297cb8d5a858ae253ac35e123090fcb5592eff0123053945ea744`. Historical results stay under their original policy and interpretation.

The explicit `allocation='standard-85-v1'` variant uses its own fresh standard-profile SEARCH incumbent, default via scoring, an85-second maximum, individual-first proposals, and25-second final reserve. The assignment is `min(85, max(0, min(total−elapsed wall, total−elapsed full CPU)−25))`. The actual assignment observations are stored and central readback recomputes the exact value, checks both incumbent caps/profile, and reuses the full SEARCH/native checker. A schema2 allocation contract and root `pruning_allocation` marker prevent relabeling an old receipt. Native rules, original design and warning acceptance are unchanged.

The finite individual phase follows the existing longest-route ranking. The whole-net phase is built lazily from the then-selected candidate. Execution and central readback share `next_base_proposal(..., order=...)`. Every failed trial's actual process, CPU, warning/report artifacts and cleanup remain. There is no free use of a B1/B2 candidate and no new validator or benchmark audit system.

`scripts/experiment_paired.py --system placement-standard` preserves the same four sequential arms,120-second wall/full CPU budgets, complete freeze,5-second wrapper reserve, charged shared overhead, frontier and final-publication caps. `--system placement` keeps the old behavior. The shared quality summarizer binds the exact declared new contract/profile/allocation using the PS helper. The new variant is a composite allocation/order hypothesis, not a causal ablation or measured improvement.

Promote the three source files, one new test, and clear experimental documentation using `source.patch` or the replacement files (not both). No production preference or user-facing CLI option is added by this draft. ROOT may add concise experimental docs from this README and `protocol.json`.

```sh
/Users/faisal/Projects/KiCad-Autorouter-local/.venv/bin/python -B .runs/placement-pruning-allocation-draft-001/run_pure_controls.py
```

The final targeted log reports27 passing methods in0.059seconds:13 new and14 existing wrapper/summary methods. These mock native/engine/central calls and establish consistency only. Earlier logs remain, including the wrong expected proposal-kind name in control003; only that assertion was corrected to the existing `individual_segment` label. Actual comparison003 is still required under ROOT's bounded lane. A smaller85-second incumbent changes the engine's cooperative deadline after the unchanged40seconds of engine grace/native reserves; pair002 B1's quality is not guaranteed.
