# Incremental backup review repairs

The independent reviewer reproduced two defects in the first draft: an archive replaced after audit could write a traversal path during extraction, and actual SIGTERM immediately after proof publication could leave a canonical positive verification record. Those original failed outputs and draft001 remain unchanged.

The repair shares exact member validation across both tar passes. Each header is checked before any payload or target is opened, including regular/directory type, normalized scoped path, declared size, duplicate detection and exact final population. Payload reads consume at most the recorded size plus one overflow sentinel. No extractall is used. A malformed archive may leave bounded partial data in its new disposable restore directory, but cannot pass verification.

Publication now temporarily converts SIGTERM to KeyboardInterrupt, using the existing invalidation path and restoring the previous handler in finally. The old positive proof is retained under a unique invalidated name. This is a scoped synchronous signal handler, with no background supervisor.

Forty small backup test methods pass (4.990 seconds), including seven archive replacements, truncated/overflow payload controls, and actual child self-SIGINT/SIGTERM after positive proof write. Both cancelled children leave no canonical success, retain exactly one invalidated proof and restore signal handlers. The unchanged child succeeds. Existing test_backup.py is byte-identical; no source secret exemptions or old backup schema changed.

Independent re-execution of the exact original reproducer is pending. No large archive, restoration, native test or network operation was run for this fix. Incremental chain restoration remains to be exercised by the lead at the integration checkpoint. These are mutable consistency checks, not authentication or atomic snapshots. All copies remain on the Mac and cannot protect against loss of the disk.
