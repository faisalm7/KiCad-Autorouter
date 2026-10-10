# Separate adversarial review

Use in a separate local review session against a preserved code checkpoint and available evidence. This is an AI review, not independent human electrical review. Work read-only except disposable test copies. Do not modify the accepted benchmark protocol, branch, originals, or implementation during review.

Read `MASTER_PROMPT.md`, the architecture, code, tests, native validation reports, data provenance/splits, method configurations, run records, backup receipts, and public claims. Try to falsify the project's claims. Do not issue approval based on the author's summary or a passing unit-test count.

1. Try to get an invalid candidate accepted: disconnection, short, changed pad net, moved footprint, altered pad/keepout/stackup, missing protected copper, invalid via, relaxed rule, changed severity/exclusion, missing native refill, stale JSON, or an absent validator. Check the emitted artifact rather than only the in-memory candidate.
2. Check native geometry and rule fidelity, including custom/non-convex pads, copper text, zone islands, plane-connected terminals, net ties, and netclass assignments/patterns. Identify where a conservative obstacle blocks valid routes or a simplification permits invalid ones.
3. Reproduce at least one documented success and one honest failure using exact commands. Prove deliberate invalid-output controls fail for the intended reason, not an unrelated setup error.
4. Compare B0, adapter-only B1, equal-budget tuned/restart B2, and full C. Is the proposed novelty merely an adapter correction, additional hardware, extra retries, different geometry, or an unfairly weakened baseline? Charge all selection, validation, and preprocessing costs.
5. Audit coverage, exclusions, lost as well as gained boards, family grouping, holdout exposure, leaked reference routes, uncertainty, quality tradeoffs, and any claims about Flux. Trace every headline number to raw artifacts and actual commands.
6. Examine resource limits, process-tree cancellation, crash safety, unsaved/stale editor state, native undo or separate-output acceptance, installation, command injection, archive traversal, supply-chain hooks, and offline runtime behavior.
7. Verify permission and licensing claims for code, boards, libraries, and any model weights. Do not infer permissions from public availability. Check that private/reference files and credentials are absent from newly public Git history.
8. Verify a real remote SHA and restored checkpoint. Determine which evidence is in Git, only on this Mac, reproducible from manifests, or not backed up. A bundle cannot prove recovery of ignored/untracked artifacts it does not contain.
9. Check README/package claims against the actual supported platform and executed GUI/installation tests. Separate implemented, run, passed, AI-reviewed, externally reviewed, and physically validated.

For each finding provide severity, exact source/artifact references, a minimal reproduction or evidence trace, the affected claim, and a remedy. Mark unverified suspicions as hypotheses. List attempted checks that could not execute. Do not weaken tests to approve a release.

Conclude with a bounded judgment: evidence supports the stated experimental claim; release needs specified fixes; or evidence is insufficient. Supply the reason and remaining external-review gates, not a generic endorsement.
