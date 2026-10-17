# Prospective caller-pinned 10.0.7 separate-project delivery

This is an unexecuted API proposal, not qualified support or a runnable Native
protocol. Root source, production pins, GUI and CLI flags remain unchanged.
The sole proposed Native slice is one fresh owned Route → rendered review copy
→ software accept intent → fresh Native export → export readback. It must wait
for source/protocol review, a clean checkpoint and the lead's Native lane.

## Caller authority and compatibility

Use the existing `pipeline.ExperimentalNativeToolchain` type. Do not introduce
another toolchain object or reconstruct one from a routing/review/export receipt.
The trusted controller may construct it from its independently frozen, explicitly
selected protocol and signed-bundle prerequisite. Every public delivery consumer
gets the same keyword-only arguments:

```python
native_toolchain=None, experimental_schematic_parity=False
```

Validate these using `p.experimental_route_record(native_toolchain,
experimental_schematic_parity)`. Thus explicit1007 without literal Boolean true,
parity true without a toolchain, wrong types, wrong version or changed tool bytes
refuse. Every source routing receipt still goes through
`p.check_experimental_route` and `p.check_result` with the caller's arguments.
The existing experimental scope stays native schema1/B0/standard/adapter-none,
whole-board, complete checked schematic, no preferences or strategy. This does
not enable flat class flags, hierarchy, selected nets, layer restrictions,
placement, pruning, free-angle or additional versions.

For experimental delivery receipts, add one field `native_delivery_context`
whose value is the exact dictionary returned by the existing
`p.experimental_route_record(nt, True)`. This is a source/tool context descriptor,
not evidence of a successful route, export or human review. A tiny handoff helper
may derive/check this field with the existing canonical comparator:

- Default context: require this field absent; keep existing production records
  readable. Never infer a context from fields, metrics versions or worker argv.
- Explicit context: require the field present and exactly equal in review,
  choice, export-input binding, export and rendered-preview metadata. Missing,
  mixed, downgraded or extra context values refuse even if other hashes match.
- The source route keeps its existing root experimental markers; do not call
  `check_experimental_route` on a review/choice/export-shaped record.
- Preserve current production call shapes when no context is supplied. Existing
  default calls must not start accepting experimental records.

## Exact consumer changes

1. **`handoff.review_policy`**: accept the two keywords and call
   `p.check_experimental_route(report, nt, parity)` before existing policy/schema
   dispatch. Default context must reject experimental source markers early.

2. **`handoff.review_copy` and `_review_copy`**: thread the same keywords through
   the public wrapper, private implementation, `review_policy`, every
   `central_check`/`check_result` call, optional `review_view.render` and published
   `native_delivery_context`. Retain the existing 30s wall/full-CPU accounting,
   session cleanup, exact captured complete project, ownership, inventories,
   publication/readback and signal handlers.

3. **`handoff.review_choice` and `_review_choice`**: validate the review's context
   before trusting its identity, propagate caller arguments to `review_policy`
   and every central readback, and publish identical context. Keep unchanged
   board/closed-review requirements, edit disclosure, all approval flags false,
   30s ceilings and invalidation. `accept` is software test intent only.

4. **`review_view.render`**: add the same keywords. Choose plotter solely from
   `nt.cli` and `nt.cli_sha256` when explicit; otherwise retain the existing lock
   and `c.CLI` check. Construct existing `f.FloorJob(..., native_toolchain=nt,
   experimental_schematic_parity=parity, protect_local_settings=True)` and use the
   caller plotter in existing protected SVG steps. Store context and exact plotter
   path in experimental preview metadata. Verify caller tool bytes before/after
   rendering; retain SVG/HTML bounds, no active content, exact layer census,
   source/candidate input copies, raw plots, PRL journals and no-validation claim.
   The same caller-selected plotter replaces `sha(c.CLI)` in `_review_copy`
   material, `_review_choice.preview_material` and `review_export.bind`.
   Experimental preview replay should reuse `f.process_check`/`ls.check_event`
   on its existing steps/bindings to require the sandbox + caller-CLI SVG argv,
   rather than treating a saved plotter path as authority.

5. **`review_export.bind`**: add the keywords and check choice/review context
   equality, pass them to `h.review_policy` and `p.check_result`, validate preview
   using caller-selected plotter, and include identical context in the returned
   binding. Every later re-bind must receive the original caller arguments.

6. **`review_export.lineage`**: add the keywords for explicit refusal, not feature
   widening. An explicit toolchain must have native policy, no guidance contract,
   captured layer contract or selected-net task. Production strategy branches
   remain unchanged; do not pass experimental context into placement helpers.

7. **`review_export.export`**: add the keywords, validate context at entry and
   propagate to every `bind`, `lineage`, `check_stage`, `_check_export`,
   `check_class_evidence`, `p.tool_manifest` and late stable/readback closure.
   Construct existing `ExportJob` with caller toolchain, literal parity and PRL
   protection; inherited `FloorJob` already supports those keywords. Publish
   matching context and keep `production_admitted=False` inside the descriptor.
   Do not alter original-rule copying, protected copper, geometry/route equality,
   warning/ignored-check checks, 30–120s export contract or publication guards.

8. **`review_export.ExportJob.step`**: preserve its current stage allowlist,
   sandbox, remaining budget, cancellation and 30s/512KiB-log/2GiB-RSS caps.
   Reuse `p.experimental_native_version(self.native_toolchain)` before and after
   the worker, because this override bypasses `p.Job.step`'s equivalent checks.
   No solver/import/export stages are added.

9. **`review_export.check_stage`**: add the keywords and use existing context-aware
   readers. Both saved refill and final `f.check_drc_stage` calls receive
   `native_toolchain=nt, experimental_schematic_parity=parity` and retain
   `sandboxed=True`. Final still requires actual `schematic_parity=True`.
   Audit/census `final-netclasses` when either `p.netclass_policy(candidate)` is
   non-None **or `nt is not None`**: `validate_candidate` already emits that stage
   for every explicit toolchain, including the Default-only owned fixture. Pass
   nt to `p.audit_candidate_netclasses`; exact metrics/netclasses argv is
   `[*f.SANDBOX, *p.native_prefix(nt), action, ...]`, not c.PYTHON. Compare metrics
   to exact `p.experimental_native_version(nt)`, original route metrics and stored
   bytes. Keep complete stage order, fields proof, original severity/ignore
   settings, warnings subset, protected copper and finite resource algebra.

10. **`review_export.check_class_evidence`**: add the keywords and give nt to
    `p.class_context_for_record`; explicit1007 must get no ordinary flat-class
    admission. Unexpected class artifacts remain refused. Do not modify the
    qualified production1000 class comparator.

11. **`review_export._check_export` and `check_export`**: add the keywords;
    validate export context before context-dependent dispatch; propagate it to
    bind, lineage, check_stage, class check, tool_manifest and every late re-bind.
    Pass nt to `ls.check_normal_policy` with existing export byte/file ceilings.
    Readback stays read-only: no fresh Native work, tool discovery or solver.
    Its returned experimental result should carry the checked context and
    `production_admitted=False`, while `applied` remains false.

Late non-byte guards matter: after the final tool/source/evidence/receipt reads,
recheck caller tools and existing `p.check_experimental_local_settings` for the
source route in handoff material closures, and for the fresh export after late
export re-bind/material checks. This closes context/PRL changes at late read
callbacks; a byte witness alone does not witness flags or hardlinks. Preserve
the helper's existing limits; the proposed owned packet is small. Existing
reader results are mutable local consistency evidence, never authentication
against a party replacing the entire history or protection from power loss.

## Deliberately bounded exclusions

`p.check_pour_evidence` still embeds production-only auxiliary Native argv.
For this prospective slice, explicitly refuse experimental delivery when
`pour_rule_area.qualify(original)` is nonempty before creating/validating an
export. The owned fixture has one ordinary B.Cu zone, not a pour rule area. Do
not waive that check or broaden pipeline.py to make this slice fit. Other
unqualified transport/version cases retain their existing refusals.

No CLI/context auto-discovery, GUI propagation, toolchain.lock edits, c.CLI/
c.PYTHON/c.PCBNEW monkeypatches, installed application changes or Windows work
are part of this proposal. A 10.0.7 SVG grammar difference remains a visible
rendering failure, not an excuse to relax SVG safety.

## Required focused regressions before Native

Reuse fixtures in tests/test_handoff.py, test_review_view.py,
test_review_export.py, test_experimental_route_context.py,
test_native_import_toolchain.py and test_native_schematic_transport.py.
Constructed worker/receipt tests do not establish Native correctness.

- Production defaults still refuse experimental route, review, choice and
  export receipts, including after deletion/downgrade of context fields.
- Explicit context without parity; parity without context; wrong version/type;
  different caller path/hash; changed tool bytes; mixed route/review/choice/export
  context all refuse. A receipt cannot select or authorize binaries.
- Default-only source still requires final-netclasses, exact nt worker prefix,
  complete full-SCH/effective-field/PRL proof and exact10.0.7 metrics. Remove each
  proof/step/binding separately and require refusal.
- Preserve source/snapshot/candidate/route/rule/ignored-setting invariants and
  stale readback witnesses; late source/evidence/context/tool/PRL mutation must
  invalidate. Wrong root argv or absent sandbox is not a compatible process.
- Cancellation at workers and positive publication, timeout/full CPU ceiling,
  malformed/duplicate/nonfinite JSON and replaced output identity must not leave
  accepted canonical export or recorded accept intent.
- Production1000 helper regressions, class guards and native-only export stage
  allowlist remain unchanged. Explicit1007 strategy/class/pour expansion refuses.

## One fresh owned slice after qualification

Freeze a new source/protocol before exposure. Reuse
experiments/native_schematic_transport_v1/fixture.py (GPL-3.0-or-later grant
expressly covers the generated packet) and its complete four-file packet:
owned1007-transport.{kicad_pcb,kicad_sch,kicad_pro,kicad_prl}. It has six numbered
terminals, three nets, one locked KEEP segment, an initially open ROUTE pair and
one unfilled ordinary GND zone. No DRU is removed; no class flag is introduced.

The controller must run in the newly qualified frozen runtime, construct nt only
from its independently pinned protocol/signed-bundle prerequisite and freshly
written source, then call:

```python
ctx = dict(native_toolchain=nt, experimental_schematic_parity=True)
p.route(board, new_route_dir, seconds=120, **ctx)
h.review_copy(new_route_dir / 'result.json', new_review_dir, render=True, **ctx)
h.review_choice(new_review_dir / 'review.json', new_choice_dir, 'accept', **ctx)
e.export(new_choice_dir / 'choice.json', new_export_dir, seconds=export_cap, **ctx)
e.check_export(new_export_dir / 'export.json', **ctx)
```

These signatures are proposed, not currently implemented. No currently runnable
qualification command exists. Preserve default-context refusals and deliberately
missing/stale evidence controls with owned copies; never modify the accepted
packet to manufacture a negative. Do not relocate/rebind installed041 paths or
rerun its old primitive diagnostics. The prior six field warnings remain raw
findings; expected source1open/final0opens0blocking/6warnings is a frozen
prediction, not a result of this proposal. A mismatch is retained and diagnosed.

Whole slice acceptance ceiling: 180s wall **and** full parent-plus-waited-child
CPU from before controller imports/preparation through final readback,
publication and cleanup. Route subcap120; export subcap at most60 and at least
the unchanged30 minimum. Reserve final readback/publication time before assigning
export_cap. Check remaining budget before each step; if the existing contracts
cannot fit, retain the earlier work and defer without raising ceilings. Use the
existing bounded foreground enclosure, one Native lane, network denial,
128MiB aggregate scratch, 4GiB outer group-RSS and existing inner worker/log caps;
polling overshoot and lack of a hard aggregate CPU quota stay explicit.

Count route, context/tool checks, copying/rendering, choice, every validation,
readback and delivery step. Record this proposal/review cost separately (wall/CPU
not measured), not as routing runtime. A pass closes only caller-pinned
experimental10.0.7 owned delivery. It does not establish production promotion,
GUI support, family superiority, human review or physical/electrical validation.
