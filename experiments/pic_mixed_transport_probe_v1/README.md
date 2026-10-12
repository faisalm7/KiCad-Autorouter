# Original PIC mixed-class import prerequisite — prospective draft

This diagnostic has not been run in KiCad or Java. It does not route, write SES,
save a board, admit production support, or establish local-rule equivalence.
The ROOT lead must review, promote these seven files to
`experiments/pic_mixed_transport_probe_v1`, commit/push/read back, and hold the
single native/JVM lane before invoking:

```
python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --output .runs/pic-mixed-transport-probe-001
```

The explicit `--run-probe` is required. The shared foreground lock and 180-second
wall/full measured CPU ceiling cover native observation, compilation, both
sequential manager imports, checks and publication. Total output is bounded to
64 MiB/2,000 files/4,000 entries; Java has a 256 MiB heap and each process is
network denied with isolated HOME/TMP. Native/compile/import caps are 60/30/60
seconds additionally limited by remaining shared budget. CPU is a measured
acceptance cap, not hard preemption. Module import precedes the controller's
clock; reported samples precede final checks, whose cost is still capped.

## What this observes

1. Verify the existing 15-file licensed acquisition and copy the complete project.
   No original, rule, severity, library reference, routing or plane is removed.
2. Reuse the qualified same-load original custom-pad observer and floor context.
   Capture `GetOwnClearance(actual layer)` before explicit initialization. Call
   exposed `WriteDRCReport` once on that same BOARD, retaining its Boolean,
   exceptions and bounded raw text report, then capture the post-initialization
   getters and export. Before/after-export geometry and clearance observations
   must be identical. A side JSON retains initialization facts even if later
   work fails. There is no inferred clean-DRC verdict from this text report.
3. Record pad/footprint local optional getters only when the returned value is
   literally `None` or a nonnegative Python `int` excluding `bool`. Opaque SWIG
   objects, exceptions and other types remain unsupported. No pointer/repr or
   coercion is interpreted as a value. Own-clearance queries are not pairwise
   `EvalRules` and do not qualify the JP1 local override by themselves.
4. On a disposable DSN, replace only the two custom stack shapes with the native
   unchanged 300 µm square anchors and append their exact native world polygons
   as same-net protected wiring bodies on bottom_layer. The original B.Cu pads
   use a back placement with top_layer-local padstacks. Pin/placement identity
   is unchanged. An exact reverse-AST proof preserves every other field,
   including all 339 original wires, six vias, original GND plane, class rules,
   typed `smd_smd` exception and all 236 connected terminals. The native census
   remains 247 pads, while the exact placed DSN census is 240 pins: 236 assigned
   and four unassigned (`P3 @1/@2`, `J1 SH/SH@1`). The seven other netless native
   pads are not DSN pin declarations; this distinction is retained rather than
   relabelling them as imported pins or asserting they were lost. Every one of
   the 240 declared pin identities, net lists and positions must match import.
   Pin centers are derived from raw DSN image offsets and exact original
   orthogonal placements; unfamiliar transforms are rejected. This is a
   representation probe on a retained reference route; no solver sees it.
5. Merge DefaultSettings, actual DsnFileSettings and fixed CLI settings disabling
   autorouter/optimizer. Set `RoutingJob.routerSettings` **before** calling the
   actual HeadlessBoardManager loader. Require the explicit completed
   `post_load_awaited` marker and both router/optimizer disabled after loading,
   as well as the pre-load settings and top-level `ses_executed=false`. Use
   fresh loads with `plane_as_obstacle=false` and `true`; no manual board setter
   substitutes for the manager lifecycle. No input filename is installed, so
   the manager's counterpart-file lookup cannot read an adjacent board.
6. Retain complete bounded item/pin/net/class/matrix census, raw and compensated
   matrix entries, native-world body contours, anchor identity, contact IDs,
   original plane flags and foreign-pin obstacle predicates. The post-load
   matrix is an observation, never rewritten to match a preferred answer.
   Target areas must follow the actual requested obstacle mode. Record
   reciprocal anchor/body contacts rather than interpreting a hull as copper.

Raw imported trace normalization and original fixed-route connectivity remain
observations. This diagnostic does not assert exact imported trace union or
future SES survival. Original POWER and Default clearances may disagree with
the initialized own/local observations: retain that discrepancy as the next
transport blocker. Original plane flags are preserved and reported; there is
no claim that they are false or that plane shortcuts have been qualified.
Matrix class changes are not evidence of electrical legality.

## Existing source/API basis

`PROTOCOL.json` binds the actual pinned JAR/tool bytes, installed pcbnew wrapper
and the existing lock's exact `_pcbnew.so` native-extension bytes,
ROOT's successful public declaration receipt and cached primary sources. The
new six-class declaration log is SHA-256
`7eaddfca0f3ddff2624a3d11754131136a48975a70d0761497e9d3207335e1b0`.
No new network requests, native runs, JVM runs or compiler calls were made to
author this draft.

At Freerouting commit `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`,
`HeadlessBoardManager.loadFromSpecctraDsn` calls `applyParsedBoardResult`, then
`applyRouterSettingsForLoadedBoard`, including the plane-as-obstacle override.
Its deferred post-load processing is awaited and charged; no routing scheduler
is constructed. The source is cached in `.runs/pic-clearance-api-001/source/`.

At KiCad commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`, cached
`pcbnew_scripting_helpers.cpp` lines537–594 explicitly initialize the same
board's DRC engine in `WriteDRCReport`, returning false for rule parse errors;
the function then runs tests and writes the report without SaveBoard. The
LoadBoard initialization earlier in that file is best effort and catches
exceptions, so it is not credited as explicit successful initialization.
`BOARD_CONNECTED_ITEM::GetOwnClearance` returns zero without an engine; that
pre-initialization value alone is not a clearance measurement.

PIC original geometry is from the pinned KiCad demos acquisition and retains
its existing CC BY-SA notices (`data/sources.json` and the source `_licenses/`
files). No downloaded source, boards or binaries are proposed for new bulk
publication. Shared helper licensing/provenance remains unchanged.

## Checks and limitations

The targeted pure suite independently reverses the actual retained-export
transformation and rejects imported-name aliases, native identity tampering,
lost terminals, wrong class/width/body/matrix/settings observations, opaque
optional values, omitted/extra/moved unassigned importer pins, missing or false
post-load completion, enabled post-load routing/optimization, SES execution and
stale final evidence. The native-extension pin is tested against the existing
lock and a tiny real-file runtime mutation. A controlled whole-flow test uses
real small files and mocked worker stages to preserve a positive and reject
late source/helper/raw-observation edits, cancellation and cap expiry. A
post-worker capture failure retains the returned PID's truthful execution flag
and process receipt without accepting the run. These
controls qualify controller consistency only, never native or Java behavior.

Every stage is captured before parsing. All original sources, helper/core bytes,
tool/API pins, Git identity and frozen output are sampled again around final
publication. This detects sampled staleness; mutable files are not signatures
or atomic protection against arbitrary concurrent writers. Historical runs
remain unchanged and all new failed artifacts must be retained.
