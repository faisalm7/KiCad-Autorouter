# Installation source-capacity correction

The installer now permits at most **256 MiB / 16,000 tracked files**. Byte and file-count failures name their ceiling, observed count and current path. Regular-file and unsafe-path checks precede capacity reporting, and the existing descriptor-bounded reader still rejects changed or oversized reads. No exception from that reader is converted into a misleading capacity error.

Installation007 remains a preserved failed attempt at `5d4703dc573d6f82469f1ef0066c702d4a01db45`: four source-inspection commands completed; no clone or native stage began. Its retained listing contains **12,327 unique files**; ROOT measured **211,119,074 bytes** at that run. The byte count is attributed to ROOT's measurement because the failed receipt did not save a completed inventory. The old limits were 192 MiB / 12,000 files; the first observed failure was the generic bounded-file exception. All five original run files have matching before/after hashes in before.json and verification.json.

The cached JAR is **64,599,107 bytes**. The reported source plus JAR leave **261,152,731 bytes** inside the unchanged **512 MiB** scratch allowance for clone Git metadata, virtual environment, native work and logs. This is a planning estimate, not an assurance that a future install fits. The actual scratch guard remains authoritative. The source ceiling itself leaves 256 MiB of the scratch budget before the other costs. The **600-second** wall cap, existing **4 GiB polling** worker guard, network denial, tracked-byte comparison and final freshness/publication checks are unchanged.

Twenty-four targeted tests pass in 0.749s. New controls exercise exact byte/file boundaries, cumulative excess rejected before payload reading, explicit ceiling reasons, and symlink/directory/missing-file errors even when capacity is exhausted. Existing lifecycle mutation and cancellation controls also pass. Running the four relevant controls against the saved old script retains one expected capacity failure and two generic-error mismatches; the unsafe/invalid-path control already passed.

Only scripts/install_smoke.py and tests/test_install_smoke.py changed. AST comparison verifies every other installer function and configuration assignment is unchanged. No PCB acceptance semantics, source projects, failed evidence, or installation qualification changed. No actual installation/native/JVM/network/Git command ran during this task. A fresh installation remains ROOT's next qualification step after a reviewed checkpoint. Current-capacity documentation at docs/install-test.md:74,76 needs ROOT's disjoint update; historical outcomes remain historical.

Reproduce focused controls from the project root:

```sh
python3 -B -m unittest discover -s tests -p test_install_smoke.py -v
```

Frozen evidence contains original/final source snapshots, exact patch, retained failed controls, passing log, and byte bindings. All artifacts remain on this Mac pending ROOT checkpoint/backup.
