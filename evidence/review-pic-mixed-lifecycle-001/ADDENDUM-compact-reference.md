# Compact-reference addendum

The original review and its manifest remain byte-identical. This addendum clears the subsequent representation fix at worker `93639677dfe99af7e84014dd9c6bdd2f383945a264e0fb46c20fa998de21647d`, driver `7ba01390f639fe8bf528b8322deff4a3c31459e8e517cf2943b8a48366fadb6b`, and tests `88f184763ce88db3d27f3f69ec56056954c2cb2ce81e21f725573301f0089308`.

The complete observations remain in the bounded 2 MiB sidecar. Custom geometry JSON contains only the fixed scope, three false qualification/execution flags, and SHA-256 of canonical complete stage content. The driver reconstructs that reference, requires exact fields and strict Boolean false values, rechecks all original/same-context terminal rows, and requires the complete before/after stages to agree. The captured sidecar itself remains in the existing immutable stage inventory; neither rows nor native geometry are discarded. The shared core cap and lifecycle/publication guards are unchanged.

Actual retained-data composition reproduced the original 1,082,101-byte custom JSON overflow. Compact JSON is 317,387 bytes under the unchanged 1,048,576-byte cap; complete sidecar is 468,136 bytes under 2,097,152. These are synthetic compositions of retained actual004 getter rows and original002 geometry, not a new native export.

Three focused existing methods and eleven independent cases passed. The unchanged positive remains valid. Ten negatives reject: forged digest, reference Boolean-as-zero, reference true qualification, sidecar Boolean-as-zero with recomputed hashes, sidecar true flag with recomputed hashes, rehashed wrong class, rehashed missing original terminal, stale sidecar content, rehashed after-export own-clearance change, and rehashed extra initialization claim. Thus the check is not limited to an outer hash mismatch. Reproduction: `python3 -B .runs/review-pic-mixed-lifecycle-001/compact-probe.py`.

No remaining scoped blocker was found. Earlier failed004 and the first review are preserved. Initialization/pairwise enforcement remain unqualified; no native/JVM/network/full-suite execution occurred in this addendum.
