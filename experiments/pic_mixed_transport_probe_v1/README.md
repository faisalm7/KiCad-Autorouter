# Original PIC mixed-class import prerequisite — load-only amendment

Actual001–003 failed on native API/type handling before initialization/export.
Actual004 captured all247pad own/local/class observations, then crashed during
`WriteDRCReport` (native exit-11, Pgm process assertion). All failures remain
preserved. This exposed amendment removes that unavailable reporting path;
initialized-rule success remains explicitly unqualified. It does not route,
write SES, save a board, admit production support, or establish rule equivalence.
After review and verified source checkpoint, ROOT alone runs a fresh output:

```
python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --output .runs/pic-mixed-transport-probe-005
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
   Capture `GetOwnClearance(actual layer)` and local/class metadata on that same
   loaded BOARD before/after export, preserving exact equality and side JSON
   even if later work fails. Raw return types are recorded. There is no DRC
   report call or successful-initialization claim. The actual pre-call004
   observations established API availability, not pairwise enforcement.
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
the load-only own/local observations: retain that discrepancy as the next
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
`pcbnew_scripting_helpers.cpp` lines247–256 attempt InitEngine in LoadBoard,
catching exceptions. Successful initialization is therefore not inferred.
Lines537 onward explicitly initialize then run tests in WriteDRCReport, but
actual004 crashed with a Pgm assertion during that call on this Mac. This
amendment keeps load-only observations; it does not pretend that removing the
unavailable diagnostic call qualifies native rules. GetOwnClearance returns
zero without an engine, and nonzero values alone do not prove pairwise rules.

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

## Prospective post-load local-clearance mode

`--local-clearance` reuses the exact native observation/export from failed005;
it does not run KiCad again or change005's failed receipt. Both original manager
loads run anew with routing disabled. The proposed operation creates a distinct
clearance class after manager initialization, assigns only JP1's two anchors and
their synthetic copper bodies, and refreshes the search trees. Netclasses and
preferred widths stay unchanged. Exact old matrix cells, other observed item
state, contacts, fixed flags and original planes must remain identical. This
observer does not export every original trace polyline; complete routing
geometry preservation is not established by this matrix experiment.

The native four-case control at1f983c1 now supports the250µm footprint-override
interpretation for its specific mixed-class pair. This new experiment checks
matrix/item transport only; neither initialized pair-collision behavior, SES
survival nor production custom-pad routing is established. All earlier plane
collision warnings remain visible. Only originalJP1 has the two observed local
values; other245pads have no observed local override. The raw null-class row
remains0, while the engine's compensated getter still reports its+1.6µm margin.

After committing the reviewed source, ROOT may run one bounded foreground job:

```sh
python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --local-clearance --output .runs/pic-local-clearance-transport-001
```

The source, tool, cached run and native-control basis are pinned in
`LOCAL_CLEARANCE_PROTOCOL.json`. Shared180wall/fullCPU seconds,64MiB output,
256MiB Java heap, network denial and process cleanup remain in force.


### Retained SES diagnostic

`--ses-roundtrip` uses the fixed `SES_PROTOCOL.json`. It reuses the completed005 native export and runs a fresh bounded writer, then native original-rule baseline/import/refill/DRC on complete copies. The raw SES retains both custom polygons. Exact original immutable content is checked before any route transplant; exact segment/via geometry, warnings, exclusions and final candidate/report hashes remain obligations. A safely parsed route mismatch may receive raw native DRC to diagnose it, but cannot produce a qualified reconstructed candidate.

Pure preparation already exposes original sub-micrometre track coordinates quantized by the retained KiCad DSN export. This remains a failed exact-survival obligation; no tolerance is widened. The pure positive fixture uses explicitly reconstructed DSN coordinates and is not native evidence. A fresh native negative removes only ordinary paths/vias on `/pic_sockets/VCC_PIC`; it must produce new named-net opens on actual original terminals. No solver, PIC production support or comparative routing claim follows.

ROOT command after exact source checkpoint/review:

```sh
python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --ses-roundtrip --output .runs/pic-custom-ses-roundtrip-001
```

Actual SES001 successfully compiled/imported/wrote59,412bytes, then failed a fractional-width checker before native execution. The retained failed receipt is immutable. The source-backed package label/angle and exact JSON-decimal corrections now allow offline structural analysis of those same bytes. Native→DSN31segment quantization and two DSN→engine collinear merges remain failed exact obligations. Engine→SES368segments and6vias match exactly.

`--native-from-ses` selects `SES_NATIVE_PROTOCOL.json`, binds the complete saved001 inventory and its actual successful process/Java/tool/source records, and executes only the fresh native stages. It does not repeat the compiler or engine writer, or relabel001 as passed:

```sh
python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --native-from-ses --output .runs/pic-custom-ses-native-001
```

### Finish the retained native diagnostic

`python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --finish-native --output .runs/pic-custom-ses-native-002` uses the fixed `SES_FINISH_PROTOCOL.json`. It verifies complete saved native001 evidence and reuses its actual baseline DRC and positive imported PCB. It runs only the missing positive DRC, negative import and negative DRC. Raw imports are isolated from the complete original-project validation copies; no generated project defaults are admitted. Original failed receipts, prior costs, route-survival failures and all warnings remain visible. No solver or production custom-pad admission follows.

### Selective custom-body obstacle observation

`python3 -B experiments/pic_mixed_transport_probe_v1/driver.py --run-probe --selective-obstacles --output .runs/pic-selective-area-observation-001` uses fixed `SELECTIVE_PROTOCOL.json`. It reuses completed005native and local250baseline evidence; one new manager import observes exactly two enabled custom bodies and an unchanged nonblocking original GND plane. Complete state, imported route geometry, all item tree entries and ordinary-route predicates are compared. No solver/SES/new native run or production support is requested. Original retained-route precision failures stay unresolved.
