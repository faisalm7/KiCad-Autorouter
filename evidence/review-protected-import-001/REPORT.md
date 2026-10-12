# Protected-route import identity review

No blocker found in the narrow exact-only matching change reviewed at pipeline SHA `986285cc841bf7efbfdd36fc615ae0d374429f384efcbab94259e7ecb4649fdf`. Fresh native qualification and the proposed reconciliation receipt extension were not part of this review.

The actual retained failed partial-completion import contains both original protected segments with regenerated UUIDs. Reconstruction preserves every non-UUID imported route atom and every original immutable object, substituting only the two exact original protected nodes after a unique net-normalized match. No geometry equivalence, splitting, merging or coordinate tolerance is admitted. The existing protected-route acceptance guard remains exact and unchanged.

Eight targeted existing methods pass (0.006 s). Fifteen independent checks against the unchanged actual public evidence pass: positive identity restoration and immutable/input preservation, plus rejected unknown field, route kind, start/end, numeric spelling and lock modifications. Full public run bytes and reviewed source hashes were checked before and after. These are pure tests, not a new native success.

The final collision guard covers route UUIDs, not global UUID uniqueness among unrelated board objects. The default no-protected call retains prior behavior; floor policies still reject retained routing and use the unchanged default call. The native route caller opts in with the complete protected task routes. A future receipt should bind the exact import and identity mapping rather than describe the imported board itself as having preserved original UUIDs.

One initial reviewer-only control reversed an equal x/y coordinate and consequently did not mutate geometry. Its script/log are retained. The corrected control applies a distinct start-coordinate offset and rejects as expected. This was not a product failure.

Reproduce: `python3 -B .runs/review-protected-import-001/audit.py`; `python3 -B -m unittest tests.test_protected_import -v`. No KiCad, Freerouting, network or GUI was run.
