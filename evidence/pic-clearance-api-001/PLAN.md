# PIC mixed clearance and SES: next bounded transport probe

**Observe the original mixed-class import before routing it.** Reuse the existing
area helper and native observer/import stages. The next useful gate is a compact
extension with original pad-local clearance observation, actual headless loading,
complete item-class/matrix readback and SES roundtrip. Do not repeat the six
completed polygon/native controls or enable production support.

## What the retained evidence establishes

PIC observer002 retained 247 native pads, 111 declared nets and 236 assigned DSN
terminals. JP1 pad1 is VCC/POWER (preferred width800 µm, clearance280 µm); pad2 is
/pic_sockets/VCC_PIC/Default (500/250). The original footprint explicitly sets
clearance250 µm, with no pad-level clearance nodes. A fresh static census of all
63 original footprints found this is the only footprint/pad clearance override.
The native original report has0 opens/0 blocking/41 library warnings. The static
249.615 µm pad-gap estimate does not establish a native violation or explain the
native result. Source/project bytes are preserved and bound in `bindings.json`.

Area002 already established exact contours, reciprocal/all-terminal contact,
trace-union accounting, raw250 µm matrix versus251.6 µm compensated API, and
foreign-obstacle behavior on the fixed owned Default scenes. It directly called
`changePlaneAsObstacle`; it did not use the original POWER class, actual headless
loading, routing or SES output. Those remain distinct gates.

## Native rule precedence and API limits

Pinned KiCad10 source [pad.cpp1598–1635](../support-scope-review-001/source/pcbnew/pad.cpp)
returns the pad override when present, otherwise delegates override lookup to its
footprint. [drc_engine.cpp1106–1171](../support-scope-review-001/source/pcbnew/drc/drc_engine.cpp)
evaluates those overrides before implicit netclass rules, taking the larger
present item override and applying the board minimum. Consequently, simply
using `max(POWER280, local250)` is not the source's pad override rule. For the
narrow original JP1 copper interaction,250 is the source-backed expectation,
not an observed initialized native pair-rule value. Custom/user rules, holes,
noncopper cases and other constraints must remain separately checked.

New pinned [board_connected_item.cpp121–129](source/board_connected_item.cpp)
shows `GetOwnClearance(layer)` returns0 when no DRC engine is attached. When
initialized, the cache evaluates the item against a null second item
([drc_engine.cpp2532–2548](../support-scope-review-001/source/pcbnew/drc/drc_engine.cpp));
this is still not a universal pairwise rule query. Installed `pcbnew.py` declares
`PAD.GetOwnClearance(layer, source=None)->int`, optional-return
`GetClearanceOverrides(source)`/`GetLocalClearance`, and
`WriteDRCReport(board,filename,units,allTrackErrors)->bool`. No same-load
initialization or Python optional-value conversion was executed here. A0 value,
opaque SWIG optional, or unproven initialization must be recorded as unqualified,
not interpreted as zero required clearance. The existing CLI original-rule DRC
stays authoritative; do not substitute these getters for it.

## Importer classes and matrix

The native exporter writes class clearances from each netclass; it also writes a
global `smd_smd` exception equal to one-quarter of Default clearance,62.5 µm
([specctra_export.cpp1170–1186,1751–1754](../support-scope-review-001/source/pcbnew/specctra_import_export/specctra_export.cpp)).
It does not serialize JP1's footprint override in these rules. Exact raw DSN is
retained; no inferred local rule may silently replace it.

Pinned [Network.java730–827](source/Network.java) creates netclass clearance
classes, initializing new cross-class entries with the maximum of the new rule
and existing value; item-specific classes copy their parent row. Cached
[Wiring.java438–486](../custom-pad-transport-options-001/Wiring.java) assigns an
area its netclass AREA default unless an explicit clearance class resolves.
An unknown class can fall back. Therefore Default/POWER areas and their anchor
pins require observed class IDs/names and raw matrix entries in both directions,
not just a successful DSN parse or equal net names. The SMD exception is not
permission to apply62.5 µm to area↔trace, area↔via or arbitrary area pairs.

Actual API006 already declares `ClearanceMatrix.getValue(i,j,layer,boolean)`;
its bytecode and area002 distinguish `false` raw values from `true` safety-margin
values. Keep both. Also observe `Item.clearanceClassIndex()`, class count/names,
item kind/net/layer and netclass preferred widths. Require no case-insensitive
class-name collision or silent unresolved-class fallback. Do not disable the
engine's margin to make the fixed JP1 pair appear acceptable. An engine-only
fixed-body conflict is a transport limitation, not evidence the native source is
illegal. A future dedicated local class must cover both body AND anchor, preserve
all unrelated matrix entries and be justified per item-pair semantics before use.

## Real loader and SES source facts

Pinned [HeadlessBoardManager.java623–632,817–856](source/HeadlessBoardManager.java)
actually applies the configured plane-obstacle override after parsing a board.
`replaceRoutingBoard` alone only assigns a reference. The cached scheduler loads
before its final settings merge; therefore capture `planeAsObstacle` before load,
after final merge, and actual area flags/search-tree behavior after both.
Loading also performs immediate normalization and starts deferred checks: await
post-load completion and charge/terminate all owned work. Do not assume a final
parsed CLI value retroactively changed the board. These are source findings;
compiled entrypoint declarations and actual observations remain pending.

Pinned [SesWriter.java51–63,331–363,382–416,514–550](source/SesWriter.java) exposes
`write(BasicBoard,OutputStream,String)`. It emits non-SYSTEM_FIXED signal areas as
wire polygons. Existing derived `type protect` areas are USER_FIXED, so expect
two synthetic bodies in raw SES; they are not automatically omitted. Trace
endpoints can snap to contacted drill-item centers before integer rounding.
Record exact emitted endpoints and area/net/layer identity. Preserve raw SES;
if KiCad import needs route-only SES, remove only the exactly matched two
synthetic area records with a strict allowed-difference proof, retaining every
other route. Never drop arbitrary polygon records or alter original KiCad pads.

## Minimal prospective execution, after review/checkpoint

Extend the existing shared helper, not a new controller. One fixed180-second
wall/full-CPU batch, one foreground worker, network denial, bounded JVM heap and
existing process-tree cleanup; ≤64MiB output. All preparation, compilation,
loader deferred work, imports, verification, failures and publication cost are
charged. Use complete disposable projects and current guarded capture/publication.

1. **Native/API observation, no routing.** Add same-load own/local override
   observations to the existing original observer, recording initialization and
   returned types honestly. Preserve all247 pad/terminal records, exact pads,
   footprint poses, original project/rules/ignored categories and original DRC.
   Do not reroute or rewrite the source to resolve an API gap.
2. **Original mixed import, no routing.** Strip only task-selected unlocked
   routes as usual; keep all nets, required terminals, protected routes and
   original geometry. Bind raw native→existing common adapter→exact-area DSN.
   Reuse proven integer contours/trace-union checks, extending census obligations
   explicitly to the original board. Load through the real headless manager
   with the desired settings already assigned, await deferred work, then record
   before/after merge state, all item classes, raw/compensated matrices, fixed
   collision pairs, widths, plane-net flags and real search-tree obstacles.
   No plane-net shortcuts. An unresolved local-rule mapping or fixed-body
   mismatch stops solver work. Preserve a negative result; do not normalize it
   into the already passed Default-scene contract.
3. **New SES boundary, not repeated geometry controls.** First roundtrip the
   existing owned back90 positive and unchanged false-hull scene through actual
   SesWriter→KiCad import→original primitive reconstruction. The positive should
   retain native acceptance; the false landing must remain the targeted concave
   open. Validate every actual SES endpoint/width/net/layer and exactly accounted
   synthetic area record. Reuse existing raw reports and native predicates. A
   generic error, unintended geometry mutation, or repaired negative is not a
   pass. This pair tests the new boundary, not the completed native/import tests.
4. Only after1–3 pass, consider the previously proposed single original routing
   attempt under a separately frozen equal-budget protocol. This plan does not
   authorize an extra attempt or call the transport an algorithmic C gain.

**Strong clearance falsifier:** with the captured original import held fixed,
changing either synthetic body's net/class to the wrong existing class must
fail the exact item/matrix binding even after superficial receipt hash updates.
If a local-class correction becomes necessary, predeclare two new owned
mixed-class clearance distances (for example240 and260 µm true capsule gaps),
original POWER/Default project and JP1-style250 µm footprint override; require
native and engine results to agree on the targeted pad↔foreign-route pair.
Those new scenes are prospective, not results or a substitute for native
initialization. Do not guess a geometry recipe or weaken margins to obtain them.

## Small API prerequisite and limits

`api-request.json` lists only missing pinned public declarations needed to write
the extension: HeadlessBoardManager, RoutingJob, SesWriter, NetClass,
DefaultItemClearanceClasses and its ItemClass enum. Existing RoutingBoard,
ClearanceMatrix, Item, DsnReader and settings declarations are already retained.
ROOT may inspect these exact classes; this task ran no javap, Java, compiler,
KiCad, router or tests. No new source implementation or acceptance path was added.

Five exact official primary-source texts totaling149,919 bytes were acquired;
`network-receipt.json` records URLs, hashes and size limits. KiCad source retains
its GPL-2.0-or-later header. Freerouting files have no inline license header;
the earlier tagged GPL-3.0 source-license observation remains a separate cached
record, not a new licensing determination. Raw sources stay ignored; only this
plan and compact bindings are proposed for later public curation.
