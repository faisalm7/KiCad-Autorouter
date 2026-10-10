# Initial acquisition004 review — promotion blocked

Reviewed frozen fetch.py d38ecb11280d94607dced256310f0de42d82f769b93e92411ed163afbff3eedf and all six proposed source/protocol documents. No network, native, engine, acquired-data change, or tracked edit occurred.

`reproduce.py` runs actual acquire/committed/publish code against tiny reviewer-owned real files with Git and HTTP mocked. `reproduction-001/review.json` preserves an unchanged success and three invalid successful receipts:

1. An already-read helper changes in the final Git show call. The last committed-material observation is not followed by a material-only recheck.
2. Source HEAD changes in that same final subprocess after the initial rev-parse. The returned HEAD remains stale.
3. A verified raw response changes during final output inventory. Its observed hash is discarded after the last response/source check.

All three leave the canonical status acquired_unqualified. Original baseline scratch bytes remain unchanged. The author and lead received the exact reproducer and are holding promotion for a fix plus unchanged-positive/rejection reruns.

The pinned metadata declares 312 existing files /32,392,408 bytes and 33 proposed files /5,016,162 bytes, under the proposed64MiB aggregate and unchanged10MiB project/response-body limits. No remote source rights or file contents were newly researched in this review. Static protocol scope correctly defers original-file notices, dependency closure, native eligibility, redistribution clearance and family independence.

Checks are finite consistency samples, not authentication or atomic protection against hostile concurrent rewrites.
