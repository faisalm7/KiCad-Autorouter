# Independent severity diagnostic review: initial blocker

Reviewed author manifest `f2bf2a19f9ade8ab71c9c27e28042147f3a5cace477fd63188b0465a1607967f`, driver `d2581afb55029d74c2e0c7d2ce6c2589a546d3aeb8b33f6450480e2e62411883`.

`publish()` sampled final source/evidence material before its last complete output-size scan. A change to the original project or retained raw report during that later scan was not rechecked before a successful canonical summary remained on disk. The independent three-case reproduction preserves its unchanged positive and both incorrect positive outcomes under `publication-001/`. It uses tiny actual files and mocks only scan timing, with no worker, native tool, network, or subprocess execution.

Required correction: perform the final bounded output-size scan before the final material check, then compare the in-memory and strict canonical records and sample the remaining wall/CPU budget. Preserve the old source and this failing evidence. This closes the reproduced ordering gap; it does not provide atomic authentication against concurrent changes at arbitrary instruction boundaries.

The other reviewed boundaries had no additional execution blocker: fixed six-case geometry, copied original stackup and project settings, exactly one declared class-profile value change in each profile case, source-backed target predicates, complete capture before report parsing, cancellation invalidation, bounded one-lock execution and the distinction between source ignored3/native ignored4. Native APIs and target findings remain unexecuted at review time. Default-profile omission is a completed coverage observation only, never enforcement qualification. The copied schematic intentionally does not match the fixture and parity is not requested.

An independent pure audit made 48 assertions against all six recipes and targeted predicates; it preserved the complete 15-file original source. These invented reports establish control logic only, not KiCad behavior or routing correctness.
