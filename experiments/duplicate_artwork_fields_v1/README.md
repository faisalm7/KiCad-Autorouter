# Duplicate artwork field-census prerequisite

This bounded study addresses repeated reference labels on source-proved non-electrical board-only artwork. It does not admit net ties, hierarchy or a new routing family by itself. The owned fixture preserves all ordinary components and original rules, with two added padless Silk/Fab artworks. Only J1 Description differs in the invalid control.

After a clean verified source checkpoint, run the preparation and Native stages sequentially through the shared bounded runner, with the study directory as its output subtree. No other Native/JVM/backup/full-suite worker may overlap.

```sh
.venv/bin/python -B experiments/duplicate_artwork_fields_v1/driver.py prepare --preparation /absolute/fresh/study/preparation
.venv/bin/python -B experiments/duplicate_artwork_fields_v1/driver.py run --preparation /absolute/fresh/study/preparation --output /absolute/fresh/study/native
```

The lead enclosure must enforce30seconds for preparation, at most120seconds across preparation/run,128MiB whole-study output,2GiB sampled group RSS and256KiB logs. The worker additionally reserves finalization time, caps its whole wall/fullCPU at110seconds and each Native step at30seconds. Polling limits may overshoot; they are not an OS sandbox. The shared Native lock and network denial remain mandatory. Charge actual complete external timings separately from authoring/review.

Require actual production KiCad10.0.0 saved refill and original-rule/full-schematic Native validation, retained complete field observations, exact six-footprint/four-component/two-artwork census, exact duplicate UUID-group proof and all four original Datasheet sentinel warnings. The old source must refuse the same positive observations for the exact duplicate-reference reason. The ordinary hidden Description mismatch must remain rejected. Every candidate retains Native/process/PRL/original-design evidence; no finding is removed or downgraded. Initial Native1000 behavior remains unqualified until the run completes.

Fixture and study source: GPL-3.0-or-later. No third-party CAD, installed library changes, external account or downloaded dependencies are required beyond the pinned local KiCad toolchain.
