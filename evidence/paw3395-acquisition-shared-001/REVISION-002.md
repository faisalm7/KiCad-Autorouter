# Final acquisition freshness correction

The prior shared draft remains preserved by manifest.json and snapshot-before-freshness-fix-001. No profiles, protocol bytes, destinations, acquisition scope, caps or payload rights claims changed. The only runtime change repeats the existing bounded .data inventory and frozen raw-response comparison immediately after the final material/HEAD witness; no expected hashes are rebased.

The reviewer's whole-controller falsifier changed real tiny original/acquired/response files during that final HEAD read, after their earlier scan. The original controller wrongly retained acquired_unqualified. The new permanent three-case test first reproduced all three failures (freshness-test-before-003.log), then passed with the fix. The combined v2 and unchanged legacy suite passes 41 methods in 0.236 seconds (v2-tests-003.log). Independent reviewer reran the unchanged five-case probe with normal/original/response/acquired/shared scenarios: the normal result passes and every mutation invalidates the canonical receipt and clears original_inputs_unchanged; its copied 41 methods also pass.

This is bounded finite sampling, not atomic protection against arbitrary concurrent writers. Every required sample and final deadline still applies; no new background process, network operation, actual acquisition or dataset edit occurred. Root will checkpoint the exact reviewed bytes before the separately authorized real fetch.

Only shared v1 fetch.py and the v2 regression test changed after the previous freeze. Existing v1 behavior/defaults and all six fixed v2 profile/data bindings remain covered; no downloaded blobs or board payloads are included in this review.
