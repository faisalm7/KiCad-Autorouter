# Portfolio continuation skeptical review

Reviewed draft SHA-256: `d6abc2a42766e8052d54011f6cd2a150a3e7393509b3f909d2c53d081c05834e`.
This is a pure control-flow/source review. No native, solver, JVM, Git, network, production edits, or delegation occurred. No routing result is qualified here. The closed NUS pair002 review and all actual source/evidence remain untouched.

## Material findings

1. **A failed final correction can leave a positive comparison index.** The completed summary is saved before the final retained-tree check. When that check rejects an actual late mutation of the old frozen-code tree and the corrective summary write raises, `experiment()` propagates the write failure while the current `portfolio-summary.json` remains `status=completed`, `comparison_eligible=true`, with a selected candidate. `retained-source-controls.json`, case `retained-late-corrective-failure`, demonstrates this using the existing draft fixture and a clean original code copy. The simpler post-publication rejection seam is also preserved in `controls.json`. Archive the owned current positive index before attempting a corrective write, retain interrupted/failure evidence, and ensure repeated corrective write failures cannot recreate an unqualified positive current index. Reuse the existing lifecycle publication pattern; no new audit framework is needed.

2. **Pre-entry corruption of archived code becomes the initial witness.** The prospective plan pins five JSON artifacts but not the completed directory inventory. `resume_basis()` captures the current old-directory inventory without first checking `frozen-code` against `prior_freeze.files_sha256`. In `retained-initial-mutation`, the prior copy initially matches every declared file digest, then its `core` file changes before continuation. All plan artifact pins remain unchanged and the resumed experiment succeeds. Verify each declared old frozen-code file digest before accepting the initial full-tree witness. Keep the existing full-tree checks afterward. The actual retained NUS B2 frozen-code files currently match their original declared digests; this counterexample mutates only an owned synthetic fixture.

## Accounting scope

The under-cap final-publication seam records 56 CPU / 50 wall seconds while the enclosing synthetic invocation actually consumes 60 CPU / 53 wall seconds. This is openly declared by `accounting_point` as a pre-write sample, and the post-write cap check catches over-budget completion. It is therefore not a demonstrated cap bypass when the parent wrapper charges the complete foreground invocation. The parent must include this successful suffix, full startup, old paired B2 invocation prefix, original shared charges, and original outer excess exactly once. Do not replace that enclosing measurement with the portfolio's pre-write sample. Calendar pause and active execution wall time remain distinct.

## Checked contract

The compatibility exception removes only the Git HEAD and portfolio checker-script hash; all other frozen source, tool, implementation, and protocol file hashes must compare exactly. The retained default row is rechecked under its original freeze, while fresh low/high rows use the current freeze. Exact retained-row replay, completed-directory inventory including empty directories, fixed profile order/scoring, failed-history rejection, full measured prior invoice, and rolling global wall/CPU allocation are present. Existing controls show late retained mutation rejects when the corrective write succeeds. The two findings above concern preservation/publication, not a license to weaken native candidate acceptance.

Six narrow pure seam outcomes are retained, including controlling positives for both the original and correctly populated archival fixture. Native stages and previously completed experiments were not repeated. The actual B2 default must remain immutable, low/high remain the only permitted new attempts, and the original failed paired/portfolio summaries must retain their status. Comparative gains beyond a completed strong B2 remain an open gate.

## Reproduction and evidence

Use the project Python in a **fresh copy of this review directory**, because each control creates exclusive retained fixture paths:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.venv/bin/python -B controls.py
/Users/faisal/Projects/KiCad-Autorouter-local/.venv/bin/python -B retained-source-controls.py
```

Both scripts reuse `.runs/portfolio-resume-draft-001/test_resume.py` and `tests/test_portfolio.py`; native and Git subprocess entry points are explicitly forbidden. `reviewed-experiment_portfolio.py` preserves the exact reviewed draft. `source-bindings.json` pins all context files. Synthetic fixture trees are retained locally and excluded from the public selector. They are not real board data or native correctness proof.
