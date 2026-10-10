# Independent completed pic observation / default-path audit

The saved failure is honest and reproducible. At commit
9300c75a4e70b29a3f919edc5cb3ed0ee3566e3e the original-source native worker exited
0 and emitted the floor context, custom-pad context and DSN. The controller then
failed with `ValueError: invalid S-expression token` while its correspondence
helper used the generic parser on KiCad's `(string_quote ")` declaration.
Original-rule DRC was never reached: no DRC process, report, copied DRC input or
native result exists. The diagnostic is **failed**, not a routing or geometry
qualification. No original JP1 pad-to-pad native DRC verdict is available.

The independent audit passed 723 saved-evidence checks in actual-audit-001.json.
It verified all fifteen original files, their acquired Git blob/size/SHA256,
complete immutable observation copy, exact committed runtime and snapshot bytes,
current installed tool/wrapper hashes, same-object callback source and before /
after data, worker argv/network denial/cwd/process cleanup, stage hashes and
current inventories. Native calls were not repeated. Both audited raw run trees
and all original input files were unchanged across the audit.

All three explicit-layer APIs executed for the two original B.Cu custom pads.
Their merged five-vertex polygons equal the source polygons up to winding and
cyclic order. Transformed and effective world polygons agree exactly with the
local shape plus the native pad position in this zero-angle source. The entire
247-pad/63-footprint identity census and original 376 route UUIDs match. These
are useful geometry/API observations; the APIs share geometry implementation,
and this does not qualify connectivity, contact, arbitrary rotations, support
for custom pads, or the original severity semantics. Six retained no-layer via
GetWidth assertions were warnings in the worker log; worker exit0 and outputs
are explicit. Via geometry correctness is not newly established by this audit.

The controller's correspondence flag remains false. A separate read-only
inspection using the existing DSN-aware parser reproduces the reason for the
failure and recovers all 236 connected terminal identities plus JP1's two
placement/image/pin/padstack records. It does not rewrite the failed run or prove
that exported convex hulls equal native copper. The source-only JP1 witness of
0.2496150883013531 mm versus the original 0.25 mm clearance remains a geometric
concern awaiting original native DRC, not a measured native rejection.

Stored pre-publication pic samples are 2.531377125 seconds wall and 2.236132
seconds parent-plus-waited-child CPU under declared 60 second caps. Worker alone
is 0.730690458 seconds wall / 0.474166 CPU. Final acceptance caps include final
checks, but these samples are not measurements of the entire controller lifetime.
The launch shell ran `python3 ... > command.log 2>&1; cat command.log`; its exit0
belongs to cat. Controller exit was not separately measured. The exact external
execution record now explicitly retains that limitation. We do not infer a
controller exit code from either the shell status or source code.

The fresh callback-absent production placement regression is accepted and its
current strict pure `check_result` passes: zero opens/blocking/warnings/exclusions,
one via and 67.93373808491306 mm, candidate
f53cd67a131344619098a9e090a277ba3f32dfd1b5487d99dfeedf9e6d4a7db3.
All eight production stages, exact source/task/fill/DSN/native-report transport,
process and code bindings are checked. Its stored samples are 8.469667584 wall /
5.734430 CPU seconds; the separate execution record measures exit0, 8.788293167
outer wall and 6.008318 waited-child CPU seconds under 60 second caps. This
supports unchanged default-path operation after the observer callback addition;
it is not a new comparative gain, family result or C novelty.

The public-copy audit verifies all 36 selected files (940,062 bytes) exactly
against the raw evidence or original notices, including both execution records.
Both original LICENSE.README and CC-BY-SA-4.0 text remain present, and the former
explicitly assigns demos/* that license. Public scope records correctly retain
the failed diagnostic, no DRC, no custom-pad qualification, shell limitation and
separate default-path regression. Complete runtime/project copies and tools are
not claimed to be contained in these selected public records.

No remaining blocker was found to retaining or reporting these **existing**
results with the stated limits. Parser correction and a fresh original-rule DRC
are future work; neither can retroactively turn observation001 into a pass.
The earlier publication-order reproduction remains preserved as pre-run source
review history; executed driver9448e8ac has the corrected final scan/canonical /
in-memory/cap ordering. No native, engine, GUI or network calls occurred in this
independent review, and the frozen owned custom-pad control design is unchanged.
