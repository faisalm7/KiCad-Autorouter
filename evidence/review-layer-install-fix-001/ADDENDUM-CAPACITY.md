# Capacity-test and documentation addendum

The narrow follow-up is clear. The frozen initial report covered the substituted-LIMIT tests in test_backup.py, but did not inspect test_backup_capacity.py. That omission missed two hardcoded2GiB assertions. ROOT correctly retained the failing40-test log before updating those expectations; this addendum corrects any implication that every capacity test was already parameterized.

The corrected test requires exactly3GiB and still100,000 files. It retains prior1GiB+1 and2GiB valid cases, adds2GiB+1 and the exact3GiB valid boundary, and rejects3GiB+1. The existing one-byte stream test verifies the last accepted byte at the cap and rejects the next byte without a large allocation. The reviewer reran only these three pure methods: all pass. ROOT’s separate retained targeted log records40 tests passing; no backup/archive/native work was run by this reviewer.

README now accurately says3GiB/100,000 files. The layer-mask documentation distinguishes the completed9ef0a64 import-only result from the separately measured production layer outcomes, records the clean-install005 failure and tracked basis correction, and keeps broader optimizer/multilayer/per-net claims unqualified. It does not turn the basis packaging fix into a new native observation.

Production backup/probe source is unchanged from the frozen initial review. This is an additive review record; the earlier report/manifest and failed log remain intact. Fresh installation006 and actual whole-chain restoration remain ROOT’s required next gates.
