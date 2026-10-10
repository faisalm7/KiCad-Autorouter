# Independent offline review of actual native controls

The retained five-case native run passed 76 offline checks, plus two explicit final native context command/input bindings. The original positive receipt, complete source, and every native control artifact remained unchanged during review. All five expected observations are supported by actual raw KiCad reports and exact mutations:

- Positive: clean native report and unchanged forced-via route.
- Track reduced from 0.3 to 0.2 mm: target UUID receives native track_width error (plus a connection_width warning), and production rejects the exact derived-width mismatch before launching validation steps.
- Via reduced from 1.5 to 0.6 mm: target UUID receives native via_diameter and annular_width errors, and production rejects the exact derived-via mismatch.
- Removed only required via: native reports one open naming both adjacent route UUIDs and two dangling warnings; separate production final DRC matches and remains unaccepted.
- Original track-width severity changed only from error to warning: diagnostic board remains clean, but production rejects the altered project byte binding. The rule mutation is confined to disposable control copies.

This is independent AI consistency review of fresh native evidence, not an independent rerun or a human PCB review. The zero-zone exposed fixture qualifies these narrow gates and required-via connectivity; it is not a new router comparison, nonempty zone or electrical/physical qualification. Stored 8.913714208 wall / 6.324479 CPU seconds are pre-final-publication samples within the shared 60-second cap; reviewed driver enforces final caps, but there is no separate full enclosing invocation measurement. Child CPU sums correctly and is not added twice. No new native, engine, build or network command was run for this review.

Run from this checkout: `python3 -B .runs/review-board-floor-production-controls-native-001/audit.py` after directing output to a fresh review location; its existing audit.json intentionally refuses overwrite. Additional two context checks are recorded separately. This review and all original run artifacts are now write-frozen.
