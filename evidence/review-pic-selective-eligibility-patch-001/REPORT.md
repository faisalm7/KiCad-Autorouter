# Witnessed tree eligibility amendment: source review

No scoped blocker found in the three source files pinned by `results.json`. The exact ComponentOutline class is accepted as unindexed only with on-board true, zero tile/tree shapes, null entries and raw validation false. Other item kinds require positive bounded shape count, matching nonnull entry-array length and raw manager validation true. The manager's pinned validator rejects null leaves; the Python readback checks strict field types, complete exact ID/kind population and before/after witness equality.

The patch retains every raw validation Boolean. `all_tree_entries_valid` remains its actual aggregate; `search_tree_population_verified`, indexed count and zero-shape-outline count are distinct checked fields. It does not turn raw outline failures into true or exempt all invalid outlines. Java's broader positive-shape/valid branch cannot make a positive-shape ComponentOutline pass the Python comparator, which requires the exact zero/null witness.

Seven small controls reused the existing synthetic fixture: unchanged positive, zero-shape trace, nonnull zero-shape outline, invalid indexed item, falsified raw-valid aggregate, altered counts and changed before/after witness. The positive passed and every contradiction rejected. No native/JVM/compiler execution, source edits or broad suite occurred. Fresh runtime witness collection is still required; failed selective001 remains failed and unchanged.

Reproduction: `python3 -B .runs/review-pic-selective-source-001/eligibility-patch-001/probe.py`.
