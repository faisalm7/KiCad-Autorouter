# Paired portfolio evidence audit

Read-only audit of `.runs/portfolio-paired-001`, frozen commit `2f36e2cba1c1fb580226a4a5d840f0290145f173`. No native or engine commands were run. This is receipt/geometry consistency review, not human PCB or electrical review.

**Passed 4,579 checks**, covering 29 native final candidate/report bindings, every baseline attempt, all 24 C trials, original source/rule hashes, frozen committed implementation, exact native inputs, candidate invariants, analytic route metrics, process receipts, shared budget arithmetic, selected unchanged baseline candidate, and public subset hashes. The public pack contains 526 exact copied raw files (3,980,743 bytes), plus its scope note and manifest; omitted full source/native-input trees remain local.

Selected B2 `via_low`: 749.4416426125838 mm, 2 vias. C feedback: 648.0451713373182 mm, 2 vias. Difference: -101.39647127526564 mm (13.529601974316966%). Both have zero opens/blocking/exclusions and retain the inherited J2 library mismatch warning. C costs an additional 49.53032983299636 wall seconds and 9.457519 CPU seconds; charged totals remain below each arm's 120-second ceilings. This single exposed family does not establish generalized superiority.

C retained 20 improvements, three native DRC rejections and one warning rejection. Its one feedback move removes the exact two newly dangling GND stubs together with their triggering segment from the unchanged incumbent. All failed work is charged. C acquired its own default-cost tuned incumbent; it did not use the portfolio winner.

`via_high` reached its correctly assigned cooperative 6-second job limit at 6.06 seconds and saved valid SES. Its process exited successfully, and native validation passed within its outer 48.866885-second allocation. It is a valid time-limited attempt, not proof of optimizer convergence. The initial audit required every job log to say COMPLETED; `initial-audit.json` and `initial-audit.log` preserve that overly strict failed assumption. The final audit records TIMED_OUT explicitly. This fixed three-variant baseline is not exhaustive tuning.

The frozen paired wrapper predates the subsequent cancellation/publication observation-metadata correction. The actual pair had neither cancellation nor a final cap crossing; observation acceptance agrees with final acceptance. Frozen artifacts were not replaced with newer code.

Rerun: `python3 -B .runs/review-portfolio-paired-001/audit.py`. Raw receipts are mutable and establish consistency, not cryptographic authenticity. No candidate has been applied.
