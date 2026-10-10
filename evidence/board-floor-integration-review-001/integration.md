# Narrow production floor-guidance integration

Proposal only, bound to current sources in read-boundary.json. No production edits,
new engine/native jobs, support expansion or native qualification is performed here.
Actual geometry001 remains an invalidated diagnostic until its publication failure
is repaired and fresh controls run. Forced-via DSN/SES import is a separate required
gate. Do not promote a broad routing feature from pure controls alone.

## API and ownership boundary

Use an explicit route-only keyword `guidance_policy='native'` by default, with a new
exact value such as `board-floors-v1`; the public CLI adds `route --guidance` with
those two choices. Reject unknown values before work. Keep the geometry adapter
(`none/graphics/planes/both`) separate from rule guidance. Do not auto-enable floors
because a board failed, and do not change stock/native exports implicitly.

The new option is a B1 rule-integration correction, not C novelty. A floor-guided
`adapter=none` result is a floor-only B1 variant, never B0. Plain/graphics/planes/both
must all preserve the same guided net rules and selected via definition; native mode
retains today's meaning and labels. A floor-enabled tuned or completion-only profile
records both axes explicitly. Existing benchmark scripts must reject undeclared
policy changes; no old arm is silently renamed or substituted.

Initial floor scope stays exactly the reviewed pure module: one effective Default
class, two outer copper layers, no assignments/patterns/extra classes/custom rules,
no original retained/protected routes, no partial completion, admitted pad/zone/net
syntax only, exact integer dimensions/grid. Reject `keep_existing`, locked routes,
literal two-class, four-layer and unknown override cases in this mode. Original
unlocked reference routes may be removed by the ordinary task definition; they
never enter guidance/selection. Reuse common preflight and add these scope checks.
Do not edit netclass.qualify_project/audit_native semantics to let floor mode pass.

## Smallest production file/function changes

1. **autorouter/board_floor.py (new)**: promote the independently reviewed pure
   transform/qualify/generated-route audit after controls pass. Add canonical JSON
   receipts (lists, no tuple-dependent equality), explicit policy/schema identity,
   and a reusable pure verifier of the retained raw→guided→adapter chain. Keep it
   independent of scripts and native imports. It computes tighter routing guidance
   while preserving raw class preferences and the original project bytes.
2. **autorouter/native.py**: add a bounded floor-context action alongside existing
   export/netclasses actions. One loaded BOARD supplies raw DSN, per-net raw class
   values, native design minima and exact pad UUID/ref/number/net/layer mapping;
   bind board/project hashes, before/after project inventory and native version.
   A separate read-only candidate-context action emits the same semantic context
   without another export. Reuse LoadBoard/Synchronize/GetNetClassSlow proven in
   controls; do not copy the fixture-only16-pad/1MiB scope into production silently.
   Select explicit project/native population limits and fail closed beyond them.
3. **pipeline.route**: branch on explicit policy after ordinary task reconstruction.
   Preserve native.dsn; write floor-guided.dsn; copy to task.dsn and then apply the
   chosen existing adapter. Keep raw/project preferences untouched. Validate and
   retain native context/process/input bindings, exact allowed guidance edits and
   final adapter network preservation. Force automatic_neckdown=false,
   fanout.enabled=false and neck_width_um=0 for every floor profile. Do not derive
   these flags only from `netclass_policy is not None`, since single-Default floor
   mode deliberately has no literal-two-class policy. Record effective assignment,
   all actual argv and outer budgets using the same existing budget helper.
4. **pipeline.validate_candidate**: accept a keyword-only validated guidance
   contract, default None for unchanged native behavior. Floor mode checks every
   generated route's exact derived width/diameter/drill and annulus, then performs
   ordinary refill and a fresh native final context bound to the final saved hash,
   audits raw preferences/floors/terminal identity and dimensions again, and runs
   final original-rule DRC. The exact floor path must not call the old class-target
   audit against preferred0.2mm values when derived guidance is0.3mm. That would
   confuse a preference with a hard floor. Unknown/contradictory contracts reject;
   a boolean `floor_validated` is never sufficient.
5. **pipeline.check_result**: independently reconstruct the stripped task from the
   source snapshot, then derive the same qualified policy from original project,
   retained native export context/process and raw DSN. Recompute the guidance,
   compare guided bytes/hash and adapter output/net invariance, verify final native
   context/process and all route dimensions against derived targets. Bind original
   files, final saved candidate/native input/report and context hashes. It does not
   run native tools or trust declared derived dimensions. The native acceptance
   parser and original DRC policy are unchanged.
6. **autorouter/__main__.py and focused tests**: dispatch the new route keyword only.
   `improve`/`recover` gain no floor option in this tranche. Their current native
   paths stay available, while any floor contract/receipt reaching their trials or
   finalization is explicitly unsupported until all contexts are propagated.
   Handoff's existing two check_result calls inherit the new receipt checks, but
   its copy/staleness regressions should include an accepted floor receipt.

No routing-engine edit, generic context framework or new geometry algorithm is
needed. Keep changes disjoint: pure policy + native acquisition, orchestration/
validator/CLI, and independent adversarial controls/review.

## Bound contract and downgrade prevention

Record explicit versioned input-policy identity, the raw preferred values and five
original native/project minima, derived values and exact named derivation, original
source inventory, stripped task hash, project hash, native-context hash, raw DSN,
guided DSN, adapter-input/output hashes, actual process provenance and engine flags.
Retain each file and fresh final context. Candidate project contents stay identical
to original project inventory except the permitted board routing/fill changes.
Store policy evidence outside the candidate directory so it cannot replace rules.

The derivation is width=max(preference,min_track_width), clearance=max(preference,
min_clearance), drill=max(preference,min_through_hole_diameter), diameter=max(preference,
min_via_diameter,drill+2*min_annular_width). Keep native DSN's typed smd_smd exception
at least the board floor too, and audit every selected/alternative via or reject it.
Unsupported local/legacy/custom/unknown overrides reject; original native DRC remains
the authority for additional untransformed constraints, including zones and thermals.
No rounding to a nearby representable value is silently authorized by this scope.

A floor receipt must fail when policy identity, any stage/context/process file or
original rule binding is absent. Unknown versions and mixed literal-two-class/floor
contracts reject. Do not use the existing `baseline != C-prototype` exception to
skip floor provenance. Reconstruct source/task from source inventory, not final
routed board or attacker-selected paths. Compare stable semantic pad/net identities
and raw dimensions, not arbitrary native iteration order or transient netcodes
between independent loads; each context must internally bind its netcodes correctly.

Choose a versioned new receipt contract with a required input-policy discriminator
for new route receipts; preserve old native receipt interpretation as explicitly
legacy. Reject contradictory floor artifacts/claims in the legacy path, and tie
new-format expectations to retained implementation/provenance rather than treating
a missing policy field as a request to bypass checks. Add explicit one-field removal/
version-downgrade regressions. This is consistency over mutable local evidence, not
cryptographic authentication against rewriting an entire history.

## Final publication lifecycle is part of this feature

The existing direct route checks source before its final positive receipt write,
then only rechecks costs. For the new explicit floor path, use the already reviewed
recovery publication pattern: scoped SIGINT/SIGTERM handling throughout the operation,
full source/snapshot/code/tool and completed evidence checks before and after final
publication, strict receipt consistency readback, and total wall/CPU cap check after
all of that. Archive a previous canonical positive/partial before a rejected
correction; a second write failure must not leave accepted=true at the canonical path.
Include failed steps and metadata children once in enclosing accounting. Report the
sample point honestly. Keep current limits; do not inflate them to fund validation.

Implement and test this on the new floor path first if that is the minimal safe
change. Do not claim an untested generalized lifecycle repair for all existing route
modes. If common code changes, rerun their cancellation/staleness regressions too.
The receipt has no accepted state while export, SES import or final checking remains
unfinished. Pure map success and native geometry controls alone never accept a board.

## Minimal promotion and actual-test sequence

A. Repair diagnostic JSON normalization and rerun the native geometry positive plus
all five exact negatives on fresh IDs. Preserve invalidated001. Then run the genuine
opposite-side forced-via engine→SES→import control, including zero-via/missing-SES
rejection, raw/guided/task hashes and native final dimensions/DRC under original rules.
If transport fails, diagnose before production edits; do not weaken target audit.

B. Promote the pure module/native acquisition with mocked process and pure tamper
controls, then integrate explicit route/final/check-result/CLI and reviewed floor-only
publication. Reject unsupported strategies. Keep legacy Default and literal-two-class
regressions unchanged. Freeze/checkpoint before actual routing.

C. Run one production CLI positive on the owned forced-via fixture with full strict
check-result, and exact invalid floor/readback controls. Verify both `adapter=none`
and `both` under explicit floor mode or restrict the advertised geometry-adapter
combinations until actually qualified. Re-run an unchanged native-policy smoke and
literal-two-class positive/negative control to detect branch regressions. All steps
remain bounded/sequential and every failure is retained.

D. Only then run a prospective original multichannel development attempt with the
same120-second wall/CPU caps and unchanged source/project. Its prior native task had
160opens plus width/via/clearance/thermal failures. Floor guidance can remove an
interchange defect; it does not promise completion or fix thermals. A source pad-to-
unlocked-track violation is not proof of immutable pad geometry impossibility.
Keep this an integration B1 result, not a C completion gain.

E. Defer strategy/portfolio/paired propagation until each passes policy end-to-end:
fresh baseline acquisition, every proposal/trial, finalization, receipt checker,
portfolio selection and comparison contract checks must share the identical rule
representation and budget. C receives no improved DSN that B1/B2 cannot use. New
benchmarks use a new freeze and run ID; no historical result is overwritten.

## Minimal falsifying controls

- Missing/renamed policy; unknown version; floor fields spliced into native receipt;
  claimed C/legacy path attempting to skip context; dropped guided file.
- Raw preferred values/native minima tampered independently; missing project produces
  native defaults; source rule/board/context process changes at any stage.
- Duplicate/extra/missing DSN net, pin permutation, via alternative, smd_smd below
  floor, class width changed after guidance, or adapter changing guided rules.
- Final track above native hard floor but below the declared derived preference;
  via width/drill/annulus mismatch and unknown net; raw native map still preserved.
- Literal-two-class or retained/protected route request in floor mode rejected before
  native work; original native policy continues to use its existing exact semantics.
- Candidate/refilled board, final native context, native input/report/process,
  source snapshot/code/tool and final receipt mutations invalidate.
- Signal/cancellation during export/import/final publication; publication over cap;
  failed correction cannot leave a positive canonical receipt. Test total CPU without
  nested double-counting and include all new native acquisition/validation steps.

Actual native controls are required for the physical rule/transport claims. These
proposed tests are an implementation checklist, not executed evidence or approval
to publish a production release.
