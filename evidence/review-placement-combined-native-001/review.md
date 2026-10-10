# Combined native observer review

No remaining source-composition blocker found at native_combined.py SHA `3fb123a8a1fdbe119a7de60e97677940e26a15b5562a822599d854ba04553a70`. This clearance covers the bounded diagnostic observer only; it does not qualify a native result, routing policy, receipt checker, or matched comparison.

The full source was read against production floor_context.py (`d346e3b552328d370b4c18c20bd55074702ec53198aef0d47f38b05a0aff7f4a`) and the actual qualified native_areas.py (`1c20e255b69eea8bb9ddd0ae864bbed5ac7797719866de4fc51e3bc326913771`). A separate AST audit passed28 checks without importing or executing pcbnew. It confirms:

- Exactly one LoadBoard, one net/class synchronization, and one native DSN export, using the same loaded board for both observations.
- Exact area getter loops, all four source enums, strict Boolean handling, native integer geometry conversion, UUID/census checks, hole/arc/closure observations, and footprint zone census; only the explicit footprint ceiling changes100→512.
- Complete production floor collection remains AST-identical after removing only the documented composition statements and restoring the existing DSN guard. Floors, project/population limits, pads, net/class values, routes, graphics, and context schemas are unchanged.
- Both contexts bind the same source board, project, complete before/after file inventories, sole raw DSN, units/version, and no-save/no-acceptance flags. Canonical paths, symlink guards, fresh outputs, and complete project requirements remain.

The initial draft omitted the area's post-export DSN guard. That omission was reported before any native run. The author restored the exact guard: reject symlinks, non-files, empty files, and sizes above20MiB before input inventory or context hashing. I read the new pure tests for real empty/symlink exports, simulated oversize stat without large allocation, and both-context binding to one mock native object. The author reports37 total pure controls passed; I did not duplicate the suite. My independent source audit confirms the final guard is present exactly once.

The explicit100→512 footprint bound is an unqualified population expansion until the lead runs the bounded native diagnostic. It does not admit genuine rule-area prohibitions, disabled placement, footprint areas, or legacy module aliases; those remain caller source-scope obligations reviewed separately. The caller must also prove exact process/tool/argv paths, enforce wall/CPU limits, and validate final candidate constraints through native DRC. This helper alone cannot authenticate a rewritten history or establish native keepout enforcement.

Snapshot001 retains the initial helper and finding. Snapshot002 binds final reviewed sources. parity-001.log is a failed first invocation of the review harness caused by literal_eval rejecting a multiplication expression in a constant dictionary; it is not a helper failure. The corrected AST-only parity-002.log and audit.json contain the successful28 checks. No native subprocess, engine, network request, full-suite run, or tracked edit occurred during this review.
