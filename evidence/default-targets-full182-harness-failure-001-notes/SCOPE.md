# Failed full182 and separate test-harness correction

Full182 at f207 ran 2,288 tests: two errors and one PowerShell skip. It failed,
with stable captured tools/source, untruncated log, nonzero exit and clean child
reaping. Both errors are NameError: observe_floors in the AST-extracted netclasses
test namespace. The old harness is the exact f207 protocol-pinned source retained
before editing; it is not reconstructed from the new test or a later product.

The correction changes only test_four_copper_classes.py: it injects the real
observe_floors helper and a scalar GetDesignSettings stand-in, then checks one
read and all five exact values. The separate targeted 22-test run passed. It is
not a repaired full182 pass or actual KiCad/Native API proof. The six v2 product
modules and three associated tests still match packet003 and the failed182 pins;
their published bytes are reused rather than duplicated. Full183 is required.

Complete external failure cost is 373.59 wall / 366.20 CPU seconds. Nested wrapper
and child observations are preserved but not added again. The corrective target
cost is a separate .36 wall / .33 CPU. Test stderr and time are in -time.log;
empty stdout is genuine and retained by hash reference. Target logs do not carry
an independent source-stability manifest, so they are not a substitute full gate.

No install011/runtime038/Native/GUI qualification occurred. GUI078 preparation
stays unexecuted and its old full182/HEAD prerequisites must be updated later.
Historical full181 passed only its old f54 scope; packet003 remains source and
constructed controls. No source field, original board, rule or problem was changed
to make this failure pass. New test plumbing does not qualify product behavior.

Only project-owned GPL code/tests and explicit local test/process metadata are
published; the GPL LICENSE is a verified prior payload link. No private CAD or
browser payload, downloaded tools, cache or unrelated archive is selected. This
curator executes no tests, Native, builds, GUI, CI, network or Git commands. Raw
originals remain unmodified on Mac. Curation/authoring cost is additional unmetered,
not zero. Essential text retention is not a full backup/restoration or release.
