# Backup capacity review

Read-only review; no archive, restoration, Native/JVM, benchmark or tests were executed by this reviewer. The lead owns targeted/full checks and the actual incremental backup/full restoration. The stat forecast is not a backup.

The forecast contains260,600files and7,498,045,240bytes. It already exceeds the old260,000file limit by600 and leaves only18,147,528bytes below7GiB before the stock trial's further artifacts. Finite8GiB/270,000 limits give1,091,889,352bytes and9,400files headroom at that observation; actual final sizes still require checking.

Static AST comparison confirms all executable code is unchanged except the two capacity assignments and two diagnostic strings. The old misleading4GiB archive/bundle errors now say configured byte ceiling. Exact path/scope restrictions, credential names/suffixes/content scanning, synthetic-secret-source exceptions, symlink/hardlink/special-file rejection, streaming payload hashes and extraction checks, immutable archive receipts, Git/ref/source freshness and restore-collision checks remain intact. Single-receipt80MiB, chain-receipt192MiB and chain-length16 caps are unchanged. Raising file/byte capacity does not guarantee a growing receipt chain fits these separate memory limits; failure must remain visible, without treating an unverified archive as a parent.

The capacity tests retain old ranges and exact new byte boundary, first-overflow rejection, count enforcement, path/credential refusal, invalid sizes and a tiny bounded inventory. Their assertions now name8GiB/270,000 and the correct configured-ceiling message. The reviewer did not execute them. No routing acceptance code, original board/project/rule file, scope or privacy/publication boundary changed. Backups stay on this Mac by owner choice.

Run the existing incremental from the verified fullcfa base only after writers are idle, then perform the required full restoration because backup-system capacity changed. All earlier evidence and failed archives must remain. Forecast/headroom and source review alone cannot satisfy either verification gate. No blocker was found in this narrow change.

`post-diagnostic-002.json` is the successful static comparison at source SHA256 `3d85ccd9ef655070d05158a628a4913597884577862d0fd374be48aa0d80e153`. Earlier false comparisons are retained: one observed the parent's concurrent diagnostic fix, and another matcher omitted the actual word `the` and bundle suffix. They are reviewer preparation issues, not weakened backup guards.

Separate accounting caveat retained without editing prior Native/review packets: B2 final console audit13.868180wall/13.588323CPU exceeds its pre-tail stored JSON13.504991/13.225460; both remain within15. C final console13.802494/13.630227 remains within15. Final public accounting must identify the later measured values rather than presenting pre-tail JSON as the final measurement.
