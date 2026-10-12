# Installation009 and installed preview audit

**Passed.** At `339e539600798a221f423a7e70b53242f17a062f`, installation009 records 20 successful network-denied commands, **643 passing tests** in the fresh clone/venv, an actual accepted placement route, and a successful native receipt readback. Independent fresh `check-result` from the installed clone also passes; this audit launched no native/engine job and did not repeat the suite.

The current source and clone exactly match the captured **12,548 tracked files / 216,097,268 bytes**. Read-only HEAD/ref/index witnesses, Python/venv hashes, copied cached JAR, native tools, captured implementation, command logs and final freshness logs match their records. The entire installation including its preview remains unchanged across the audit: **12,838 inventory entries / 300,484,533 bytes**. This is below the 512 MiB scratch cap; the source is below 256 MiB / 16,000 files.

The exact native candidate is `cf03ed76cacfac942087af70fca32f8f75ab72518e66013b48ce774659a593cd`, bound to report `96bb87ff6dc33a4ea9aa03d4be69cee7f6205a2f297986ce8b84ad5c6e48fc7a`. Raw final DRC has **0 opens / 0 blocking / 0 warnings / 0 exclusions**, with **1 via / 67.93373808491305 mm**. Complete source/snapshot and candidate project/rule bytes, immutable geometry, floor/placement evidence and raw process receipts remain exact.

Seven effective ignored checks are retained and shown in HTML. **Five are explicit original project settings**: footprint_filters_mismatch, footprint_type_mismatch, missing_courtyard, npth_inside_courtyard, pth_inside_courtyard. The other two, track_not_centered_on_via, tuning_profile_track_geometries, are native defaults present identically in original-source and final DRC. No severity bytes were changed. Zero reported findings is scoped to those settings; this is not an assertion that every check ran.

The installed `review-copy --render` finishes `ready_for_manual_review` using the same clone/venv and exact accepted receipt. Its four successful pinned KiCad plotter commands cover before/after F.Cu and B.Cu plus Edge.Cuts. The advertised complete source and candidate copies remain unchanged. Each separate disposable plotting input gains only a PRL; every pre-existing file remains byte-identical. Raw native SVGs are retained, and each display SVG differs only by removing the observed SVG1.1 DOCTYPE. Exact output, process, input-binding, runtime and HTML hashes all verify. HTML retains the ignored-check list and limited scope. Plotting performs no new refill or DRC; no live board was applied or GUI interaction qualified.

| Measurement | Stored wall / CPU seconds | Enclosing wall / waited-child CPU seconds |
|---|---:|---:|
| Installation | 51.365890 / 49.224024 | 58.060935 / 55.496116 |
| Preview | 2.947392 / 2.222810 | 3.237173 / 2.472345 |

Stored samples precede final freshness/publication. The external wrappers include that later work and remain below 600 seconds installation wall and 30 seconds preview wall/full CPU. The installation has no CPU acceptance cap. Native route sample was 7.217526 wall / 4.751602 CPU within its separate 60-second caps. Polling resource guards are not OS-enforced quotas.

Installation008 remains **failed**: the 643-test run had one stale backup-capacity expectation (`120000 != 100000`), and its native route stage was not reached. Its failure receipt and raw test log were unchanged during this audit. It is not relabelled by installation009's success.

The first audit attempt incorrectly equated all seven effective ignored checks with explicit project keys. That failed assertion and original audit source/log are retained. Corrected checking binds five explicit keys plus two native defaults and source-to-final equality; the completed audit passes. An unexecuted log-message assumption was also corrected to the actual `Plotted to ... Done.` output. Neither was a routing or preview defect.

This qualifies a fresh local clone/venv and the owned fixture's installed plotting path on the existing Mac with reused pinned KiCad/Java/Python and JAR. It does not qualify a fresh OS, download/install acquisition, ordinary copper-zone GUI behavior, physical/electrical correctness, or a general routing improvement. Evidence checks are finite mutable-file samples, not hostile-writer authentication. ROOT owns publication/backup; full local clone/venv/binaries are hash-bound rather than copied into this compact selection.

Reproduction (offline readback only; outputs stay in this review directory): `python3 -B .runs/review-installation009-preview-001/audit.py`. A fresh evidence folder should be used for a later audit to preserve this frozen review.
