# Board-floor native draft review

Independent AI read-only review of the driver, native context worker, recipe,
23 test definitions, README and retained pure logs. No production edits, native
imports, native/engine jobs or repeated test execution by this reviewer. This is
not native qualification or human PCB review.

No immediate blocker was found to the lead's proposed geometry stage after backup.
Run it before the forced-via stage and retain any actual failure without loosening
rules or predicates. Eleven of twelve original manifest entries match; the lead's
accounting-only driver change is separately bound below, with original retained.

The owned fixture has one SIGNAL_A terminal only on F.Cu and its mate only on B.Cu;
all four pads are SMD without drills, with no source routes/zones/plated interlayer
objects. A completed SIGNAL_A therefore needs generated interlayer copper. The
engine test requires an actual native-observed via on that net and zero native
opens; a same-side route or zero-via output cannot qualify transport. The second net
is front-side and supplies the deliberate foreign-net clearance counterexample.

The positive dimensions meet the unchanged native floors. Deliberate cases preserve
original pads, poses, nets and board edges and alter only routes:0.2mm width versus
0.3mm minimum,0.2mm copper gap versus0.3mm clearance,0.6mm via versus1.5mm minimum,
0.2mm drill versus0.3mm minimum, and0.2mm radial annulus with otherwise sufficient
1.5mm diameter/1.1mm drill. Each negative requires its specific unexcluded native
error on the exact object UUIDs, zero opens/exclusions and actual native rejection.
Secondary errors remain visible; the controls correctly do not promise one isolated
finding per negative. Source project SHA is fixed, copied whole, with retained
license notices; a new original custom rule file rejects the context.

Installed pcbnew.py source confirms the worker's questioned APIs exist:
`LayerName(int)` at3709, `PCB_VIA.GetDrillValue()` at16517, `GetWidth()` at16188,
`GetViaType()` at16098, and `ExportSpecctraDSN(BOARD,path)` at9869. Exact local wrapper
hash/signatures are in review.json. Reading these wrappers proves declared bindings,
not runtime semantics or behavior on the proposed fixture. Fresh context must still
verify actual native floors/classes/terminals and route readback; geometry controls
must actually trigger their expected native findings.

The forced-via path retains raw/guided/adapted DSNs, uses the original bounded
production engine profile with all three width-reduction paths disabled, requires
a nonempty SES, imports through pinned native code, transfers only routes, applies
exact derived-dimension checks, and performs original-rule refill/DRC and native
route readback. Missing/import-invalid data or any remaining native error fails.
A passed geometry stage alone would not qualify engine via selection/SES transport.

The shared timing callback uses complete process wall and self+waited-child CPU,
covering setup, helper/native/engine calls, errors and final checks. Shared step
receipts append once even when calls fail or cancel. Engine calls hold20seconds for
native follow-up, and native calls are individually capped at20seconds; these are
planning/cooperative bounds, not aggregate OS CPU preemption. The native lock and
network denial remain active for every child. Completed case trees, originals and
copied code are rehashed before/after summary publication; invalidation vacates the
positive canonical index before a potentially failing correction write.

The requested accounting clarification is resolved. The lead added only an explicit
`accounting_point` field: stored totals precede final summary publication/freshness
recheck, while acceptance caps include both. Current driver SHA is
`ed7588640bddb25270a4a58819dfb2c972e29d07d112143a0f3d3ac038b9e9db`.
`driver-before-accounting-note.py` matches the old manifest hash and the exact change
is preserved in `lead-driver-diff.patch`; the lead reran23 pure tests successfully.
Review.json binds the separate lead receipt and log. No budget was changed.
The raw total CPU includes metadata children; child/monitor subtotals are not a
separately complete parent/child decomposition.

Remaining gates are actual KiCad geometry positive and all five native negatives,
then actual forced-via engine/import acceptance under one charged budget. These are
owned diagnostic controls, not another independent board family, routing comparison
or production eligibility expansion. All summary routing/comparison/production/
electrical qualification flags correctly stay false. Source review cannot turn
mocked positive predicates or API signatures into actual native qualification.
