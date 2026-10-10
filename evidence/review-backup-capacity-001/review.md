# Independent backup capacity review

Cleared the four-line change: one shared limit changes from 1 GiB to 2 GiB and three error strings follow it. The promoted script exactly matches the proposal. Reversing those exact replacements reproduces the recorded original script SHA256. The promoted eight-test file also exactly matches the reviewed proposal.

The 100,000-file bound, exact backup scopes, credential scanning and exact-path/hash exceptions, symlink/hardlink/special-file restrictions, no-follow reads, input freeze checks, exclusive writes, archive whitelist/hash validation and restoration logic are byte-for-byte unchanged. Prior schema1 archives remain compatible because validation logic is unchanged and the limit only increases. This review did not open/create an archive or rerun restoration.

The retained `df -k .` output independently converts to 404.010864 GiB available at 2026-10-10T12:03:48Z. It is a time-specific observation. Each logical-payload, compressed-archive and Git-bundle cap is separately 2 GiB; this is not an aggregate quota. The existing bundle guard remains a post-creation check. Lead-reported 27 backup controls passed in 1.435s; their native/archive work was not repeated here.

No blocking issue found in this scoped change. No native/engine job, archive operation, tracked edit or large allocation occurred.
