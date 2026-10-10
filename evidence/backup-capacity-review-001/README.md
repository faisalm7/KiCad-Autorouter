# Scoped backup capacity proposal

Recommend raising the one shared `LIMIT` from1GiB to2GiB. This is a four-line
patch: one numeric constant and three error messages. The inverse replacement
matches the original source byte-for-byte. No policy or validation code changes.

The same2GiB ceiling continues to govern each of: total logical non-Git source
bytes, one compressed non-Git archive, and one Git bundle. It is not an aggregate
backup disk allowance. `MAX_FILES=100000`, exact scopes, credential scanners and
reviewed exact exceptions, symlink/hardlink/special-file rejection, no-follow
opens, source-before/after freeze, full bundle requirements, exclusive receipt
writes, archive whitelist/streaming/hash checks and scratch restoration remain
unchanged. Separate cap parameters are unnecessary for this bounded change.

The latest3e2cce9 backup receipt is hash-bound to its existing verified restore
record:30,291files,1,017,693,214logical bytes. It leaves56,048,610bytes under1GiB,
less than a prospective two-arm60MiB evidence batch. The proposed cap leaves
1,129,790,434bytes against that same snapshot. Old schema1 receipts are unchanged;
the candidate's `check_manifest` accepted this exact existing inventory. No new
archive/restore was performed or claimed by this review.

`df -k .` on the selected project filesystem reported404.01GiB available at the
recorded review time. This is ample for the bounded next work and preservation;
it is a current observation, not a guarantee of future disk availability. The
existing bundle check still occurs after Git produces the bundle and retains
oversized output for review; this is not an OS disk quota. At a maximum logical
payload, incompressible tar framing can still cause the compressed guard to
reject before the source cap. Explicit rejection remains preferable to an
unbounded archive. Earlier backups are neither modified nor deleted.

Eight new pure/small-file controls passed in0.001s: exact2GiB bound and100k count,
old<=1GiB inventory compatibility, new range/exact boundary/over-bound rejection,
compressed stream boundary without large allocation, scaled file-count guard,
invalid manifest sizes, a four-byte actual inventory limit and path/credential
name checks. No large file, archive, Git bundle, native or engine job was made.

Lead integration: apply `capacity.patch`, copy `test_backup_capacity.py` to
`tests/test_backup_capacity.py`, then run the existing backup/restore adversarial
suite plus the new tests. Those existing tests exercise real tiny scratch
archives/Git restoration and were read, not rerun here under the no-archive
instruction. Commit/audit/push before using the new bounded capacity for another
full backup. A new actual archive/restore is a later lead action, not this
proposal's result. The on-Mac-only disk-failure limitation remains unchanged.

The draft is reproduced by `python3 -B .runs/backup-capacity-review-001/verify_proposal.py`.
All files are frozen; no tracked file or global/OS setting was changed.
