# Installation006 independent readback

Passed: 389 checks using the adapted installation004 audit and the shared checker in the installation clone's own cwd/venv. No native, engine, installation, JVM, GUI or network work was run by this review.

The actual run at `eae1f398f5769851247acc01c6d0566d216563d5` completed all 20 commands and 608 tests (16.568 s). The detached local clone contains 10,699 exact tracked files / 154,825,605 bytes, below 12,000 files / 192 MiB. Its separate copied venv, offline verified JAR copy, bootstrap, process/log bindings, complete native source/snapshot/project invariants, strict planning derivation, final DRC, metrics and captured code/tool pins all check. The complete installation tree (10,894 files / 235,010,166 bytes) stayed identical during this review and remains below the 512 MiB scratch cap.

The original-rule native result has zero opens, blocking findings, warnings and exclusions, one via and 67.93373808491306 mm of track. Candidate SHA-256 is `6f3b180c431773fed2d7308bf562b2d3f3f40094418cf650a22e50b633a62597`. Native stored cost is 6.744306875 s wall / 4.706822 s CPU, under its separate 60 s caps. Installation stored prepublication cost is 46.702745584 s wall / 44.033093 s CPU; the independent outer wrapper measured 51.742342084 s wall / 49.253543 s waited-child CPU through completion. Installation has a 600 s wall cap and observed CPU, not a CPU ceiling.

All 162 selected raw public files / 1,013,799 bytes match their originals; the separately copied outer wrapper, execution receipt and command log also match. Complete source inventory and NUL filename logs remain local with public omission hashes; this review does not duplicate those large inventories. Only a compact complete-tree inventory digest is retained here.

The first lead checker invocation from the main checkout correctly rejected `floor process provenance differs: floor-export`; it is retained as a wrong-cwd invocation, not a native routing failure. Fresh clone-cwd readback passes. The run's original clean Git observations remain historical evidence. Current main-checkout differences found during review are only subsequent reporting edits to PLANS.md, REQUIREMENTS.md, STATUS.md and evidence/claims.json; the installation clone and original run stayed exact.

This establishes one owned placement-fixture installation in a fresh local checkout/venv on the existing Mac, reusing its installed KiCad/Java/base Python and verified dependency cache. It does not establish a fresh-Mac installation, package release, generalized board coverage, physical validation or hostile-concurrency authentication. Failed installation005 and its missing ignored-basis dependency remain preserved separately.

Reproduction: `python3 -B .runs/review-installation-006/audit.py` uses saved evidence and refuses existing audit output. To repeat, copy this small audit into a fresh sibling review directory and retain all previous records.
