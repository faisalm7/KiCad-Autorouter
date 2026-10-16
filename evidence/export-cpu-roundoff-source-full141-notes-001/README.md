# Export CPU roundoff correction — source and full141 software record

Commit `76d2c666f3fe8f009e46f5421c77e18eaacbf7b2` corrects the demonstrated
GUI058 false refusal in resource accounting. The saved verifier records the same
remote SHA and the exact `review_export.py` hash at
2026-10-16T17:59:18.780789Z. Curation read that retained verifier receipt; it did
not repeat a push or remote readback.

The old producer subtracted the ordinary sum of seven step CPU samples from the
waited-child aggregate. GUI058 stored a control residual of
`-4.440892098500626e-16`, which the strict reader correctly refused. The new
shared helper uses `math.fsum`, validates finite nonnegative components, refuses
deficits beyond the existing 1e-6-second algebra tolerance, and uses zero for an
in-tolerance negative residual. Total CPU still includes parent, every recorded
step, monitor and nonnegative control-child CPU. It rejects meaningful deficits,
invalid numbers and overflow. `producer-correction.patch` is the exact two-module
delta against the retained installed runtime007 source. The strict accounting
reader function is exactly unchanged. The source-only skeptical review found no
blocker; no PCB behavior follows from that review.

The six targeted accounting tests passed, including actual seven GUI058 samples
and step walls, threshold/nextafter refusal, positive control and monitor CPU,
invalid numeric values, overflow and unchanged strict-reader rejection. The
first new test fixture omitted required step wall values and failed. The lead
reported adding the actual saved walls to the test fixture, without a production
change for that failure. No separate raw failure log or complete timing was
saved; neither is invented here. The six-pass log reports 0.000 test seconds,
which is not a complete external CPU/wall measurement.

The 42 export-related tests passed in 6.071 test seconds; the complete external
wrapper measured **6.26 s wall / 5.96 s CPU**. The new synthetic-process test
exercises the actual export transaction, publication and strict reader; it does
not establish Native PCB correctness. The retained time log contains both test
stderr and timing; its separate stdout command log was empty.

Full141 passed **1,832 test methods in 215.004 test seconds**. The complete
external wrapper measured **216.22 s wall / 206.92 s CPU**. The internal controller
sample was 216.02819329197519 s wall / 206.80268 s full CPU. Its waited child was
215.60941500001354 s wall / 206.00245900000002 s CPU. These are nested samples and
must not be added. The retained execution record binds all tool/implementation
pins, 299 additional source hashes, controller, log and process metadata. Those
source, implementation, controller and log hashes matched during curation.
Common019 discovery is unchanged. The controller and lead report no overlapping
Native/JVM/GUI/CI/backup work during full141; curation performed no new process
audit. Existing sampled RSS/workdir/log caps and polling limitations remain
visible; no OS aggregate quota is claimed.

The full141 controller, common019 discovery and targeted tests are copied
verbatim as source as run. Do not run these relocated copies in place: their ROOT
calculation/fixed completed outputs belong to the historical `.runs` layout.
The source commit and bound hashes, rather than a rewritten controller, identify
the executed code. No project module was imported and no test, Native, JVM or GUI
process was launched during curation.

The related GUI058 export remains rejected and unchanged. The original Mixer
hierarchy diagnostic remains production-deferred, with its actual source
findings, below-floor Default width and prototype identity/empty-net limitations
retained. This accounting correction neither repairs nor waives them. Runtime008
and GUI059 qualification are separate and excluded from this record; at task
handoff the lead had built008 and started059 route. No partial result is treated
as a pass. This is a false-refusal fix and software regression evidence, with no
measured routing gain, new Native proof, end-to-end GUI qualification, human PCB
approval or physical/electrical validation.

Only project-owned source/tests, their logs and exact provenance records are
copied. No screenshots, incidental Finder/browser contents, credentials, source
boards/schematics, tool binaries or third-party demo material are included.
Project-authored code remains under the repository GPL-3.0-or-later license.
