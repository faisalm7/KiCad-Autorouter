# Storage and verification retention

Authoritative material consists of original inputs, unique successful **and failed**
results, unfinished work, licensed resources, archives/bundles, their dependency
chains and compact verification records. An expanded verification copy is not an
additional independent backup. All current backups remain on this Mac.

`scripts/backup.py` keeps its existing receipt/archive formats, capture scopes and
finite byte/file/chain limits. Historical folders are never collected automatically.
Their removal requires an exact owner-approved list and fresh content, readable
recovery-source, dependency and active-use checks. Keep private storage audits and
deletion lists outside Git.

Approved derived data retirement uses actual descendant metadata, not a blanket
extended-attribute refusal. The macOS helper records permissions, executable bits,
ownership/link information, ACLs and readable xattr bytes, including resource forks,
in a private, hash-verified gzip supplement outside the disposable copy. When the
owner accepts it for the relevant scope, `com.apple.provenance` is recorded with its
location but not replayed. Other unreadable or oversized attributes identify the
exact affected path and retain that candidate. Metadata records do not excuse
extra or changed file contents lacking independently verified recovery coverage.

Future `verify()` and `checkpoint()` calls default to one exclusively created
`.local-backups/verification-workspace` slot. After success, independently checked
archive/Git contents are compared with the exact workspace. Only the creating
process may remove that new, unchanged, inactive, non-required copy. Ownership,
coverage and removal records stay in `.local-backups/verification-records`; the
verification/integrity proof stays beside its archive receipt. A proof's historical
`restore_directory` or `scratch_directory` may therefore no longer exist: consult
`workspace_policy` and `workspace_removal_receipt`.

Failure or uncertain cleanup retains scratch and blocks the next nonessential
verification. Do not remove a blocked slot by name alone. The low-level Python API
accepts `pinned_reason` for an explicitly required recovery base or inspection;
routine jobs must not use it to accumulate copies.

Disposal preflights directory owner write/execute permissions across the workspace
and its parent before any unlink, then rechecks after metadata/activity inspection.
It never changes permissions to force removal. Read-only files can be removed
when their containing directory permits it. ACL denials, filesystem errors or
concurrent changes can still stop a deletion partway; retain the remainder and
its complete pre-deletion recovery proofs. This is not an atomic tree deletion.

On macOS, successful owned-slot disposal also retains its metadata supplement in
the external verification records and binds its path/SHA to the removal receipt.
Actual small fixtures check ACL, executable and resource-fork recovery after
disposal, late changes and activity refusal. Supplements are bounded to 32 MiB
compressed (384 MiB decoded), with 1 MiB per xattr and 16 MiB aggregate xattr data;
the Mac verification space forecast includes the compressed bound. These are
metadata-retirement controls, not qualification of historical virtual environments,
an independent OS or a full-size recovery. Capture/chain limits remain unchanged.

Existing commands remain:

```sh
.venv/bin/python -B scripts/backup.py --incremental /absolute/path/to/receipt.json
.venv/bin/python -B scripts/backup.py --verify /absolute/path/to/receipt.json
```

A first capture can use the no-argument command. Once checkpoints exist, an implicit
repeated full capture refuses: select the exact retained incremental parent. An
exceptional new full capture requires explicit `--full "reviewed milestone reason"`.
This is not permission to bypass coverage review or raise limits. Restoration of a
chain does not require making another full archive.

Before capture, packed Git import, full expansion, integrity extraction or
installation, a prospective peak-space forecast must fit alongside the fixed 3 GiB
reserve. Full recovery first imports bounded packed Git metadata, then measures the
tree from that recovered store before checkout/extraction; it works without the
original repository. These are forecasts and cooperative-process checks, not disk
reservations, hostile-administrator isolation or power-loss guarantees.

Installation smoke tests now default to curated distribution mode. Full-source
qualification is explicit `--source-mode full`. Old installation trees can contain
unique Native/GUI/failed-run evidence. They remain in capture scope until exact
reconstruction and all nested-evidence dependencies are verified; no folder-name
exclusion has been introduced. Full installation-tree deduplication remains open.

Small actual Git/tar and fault fixtures qualify these guards, including original
Git loss, real open-file use, modifications, unknown files, dependency aliases and
directory replacement. They do **not** replace the later full-size recovery gate.
Native routing constraints and validation are unchanged. Automatic scratch cleanup
has Mac/Linux process-inspection paths; Windows remains refused/unqualified.
