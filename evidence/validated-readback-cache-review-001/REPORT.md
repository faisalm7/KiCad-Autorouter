# Scoped validated-readback cache design review

Recommendation: a small per-invocation in-memory cache around the existing full `pipeline.check_result` is defensible if it reuses successful consistency decisions only under an exact complete witness. Every emitted candidate still needs its own fresh native refill/final DRC/context/metrics, and the full checker must run at least once for each cached receipt. No implementation, cache speedup, newly accepted route or gain is established by this design review. No tracked edit/native/JVM/Git/network process or delegation ran.

The recorded first multichannel pair explains the efficiency target: B1/B2 are accepted at19vias/2640.198552639mm/96warnings, while C has the same own incumbent, zero trials, and is rejected after enclosing/shared charges reach121.504365CPU seconds under120. C's accepted inner receipt cannot override that failed delivery budget. Those actual results remain immutable. Caching might recover useful time; a new frozen measured run must demonstrate whether it does.

## Reproduced unsafe edge

**File hashes alone do not describe the complete tree.** `pc.inventory` returns regular-file hashes but omits empty-directory membership. `empty-trial-directory-001.json` uses the actual helper and extracts the exact trial-population predicate from the current full pruning checker. Adding `trials/9999` leaves the file inventory unchanged but makes that checker predicate reject. A cache keyed only by those file hashes would hit and skip a required check. This is a design counterexample, not a demonstrated defect in an implemented cache.

Capture directory membership/entry types in the existing bounded `pc.inventory` traversal, with defaults preserving current callers. Bind every directory including empty ones. Keep special files/symlinks/entry/file/byte bounds fail-closed. Use the full raw evidence tree, including result/partial/invalidated files, rather than filtered `floor_evidence_hashes` or pruning inventories; filtered inventories deliberately omit files and are insufficient cache witnesses.

## Minimal API

Keep the old full checker privately unchanged, for example `_check_result_uncached(path)`. Add one context manager such as `validation_readback_session(max_entries=8)` and a wrapper at the existing `check_result` entry point. Default calls outside that context remain uncached. The paired invocation owns the context; nested calls inherit its table and it ends/clears in `finally`. No persistent cache, background process, pickle, disk record, native process result or cross-session reuse.

On a miss, capture a bounded strict receipt and witness **before** the full checker, execute that same checker, capture the witness again, and reject any difference before storing a deep copy of its successful output. Do not snapshot a changed post-check tree as the new positive baseline. Cache only canonical accepted bounded placement schema3/4/5 receipts after their actual policy checker accepts; malformed/mixed/downgraded markers still use the same fail-closed full path. Legacy schema1/2/native receipts receive no cache.

On a hit, require the same canonical receipt path, exact receipt bytes/digest, complete source tree, complete evidence files/directories, and current checker/toolchain identity. Recheck the full witness before returning a deep copy. A changed witness drops the entry and requires full checking, or rejects immediately where appropriate. A mutation during either capture/check/readback rejects and clears the table. Clear all entries on exceptions including KeyboardInterrupt, even if a surrounding caller later catches the error. Never return the table's mutable result object to callers.

Use the existing source32MiB/2000files/4000entries and schema3/4 evidence100MiB/2000files/4000entries bounds; schema5 uses its existing512MiB/16000files/32000entries bounds. Eight entries keeps this finite. Store digests and bounded membership, not file contents. Reject unsupported path aliases/symlinks before canonicalization can hide them; regular-file readers keep the existing descriptor/type/size race checks. No size/mtime-only or inode-only shortcut: equal-size edits and replaced reports must invalidate reuse.

Identity must include current checker implementation bytes/file set, the live uncached callable identity, the toolchain lock bytes and the actual pinned tool paths/content hashes. Reuse existing trusted identity helpers where suitable. If callable/helper replacement or hot reload is supported, live helper identities must also invalidate the session; otherwise explicitly disallow such mutation within an active transaction. File-only identity cannot establish that a monkeypatched checker is the same checker. Identity capture and full tree hashing are real charged CPU/wall work; do not subtract them from benchmark budgets or call polling limits OS quotas.

Schema5's repeated separately checked incumbent is a useful cache target: the nested incumbent tree is immutable while a new trial/final candidate is built elsewhere. The C root receipt becomes eligible only after its own full replay/final checks. Shared caches must never mark a new candidate checked because it resembles an incumbent or shares its native report name. Source/rules/code/report/receipt/runtime changes force fresh checking or rejection. Root's current completed-arm and returned/stored receipt checks remain in place.

## Targeted regression cases

- A correct bounded placement receipt executes the full checker once; a later unchanged readback returns the same value through a verified hit. The actual output stays separate from any stored cache object.
- Same-size source board, rule/project, report, receipt, retained-code and external toolchain/runtime edits miss or reject. Added/removed files, empty `trials` directories, symlinks, special files and exact/over limits remain detected.
- A full checker that returns after an injected late mutation cannot populate the cache. A mutation during a hit's final witness cannot return a positive.
- Mutating the returned dictionary cannot change the next checked answer. Underlying checker identity changes require a miss; no stale decision survives context exit, handled failure, cancellation or nested-context exception.
- Entry bound and schema1/2 fallback retain existing behavior. Schema3/4/5 downgrade/mixed policy failures are not made cacheable.

Use existing complete receipt fixtures and tamper helpers for these pure controls, then one real fresh matched native comparison to measure end-to-end effect. No repeated native controls merely to populate a cache. Full integration/restoration cadence remains unchanged.
