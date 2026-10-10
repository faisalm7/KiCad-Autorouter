# Minimal production integration proposal: placement-clearance-v1

Plan only; no implementation, tests or native jobs performed here. The measured
basis is the exposed multichannel v2 default-cost20µm arm at24ab168d2f62b89fd76c6bac80ede241df72a0c9:
0opens/0blocking/96warnings/0exclusions,21vias/2647.385728862638mm,
44.58072420800454charged wall/56.57206900000001charged CPU seconds. The candidate
SHA is36e778573b2c90dfca8f9d45597e6bd890cc45c7fc4c6c86a2673e2e7fef3bef.
The zero-margin and lower-via-cost variants were invalid. This supports a narrow
B1 input-adapter policy, not C novelty, general superiority, whole-project DRC
cleanliness, physical correctness, or a universal20µm geometry bound.

## Decision

Extend the existing `floor_route` lifecycle through ONE closed guidance-policy
parameter. Do not copy theapproximately300-line diagnostic driver into a second production
route. Keep `native` and `board-floors-v1` paths/receipts unchanged. Admit only
`placement-clearance-v1`, `adapter=both`, whole unlocked routing, exactly2Cu,
one Default class, the existing floor restrictions, one four-line axis-aligned
outer rectangle/no cutouts, and at least one all-five-explicit-allowed enabled
SHEETNAME board area. Reject genuine/disabled/unknown areas, image keepouts,
footprint zones, legacy modules, locked routes, custom rules and unsupported
geometry exactly as the reviewed transform does. Preserve all original areas.

Initially require `--profile completion-only` and fix explicit costs50/5 internally.
Reject scoring overrides, partial routing and other profiles under the new
policy until separately qualified. This is narrower than old floor-route,
whose existing three profiles and scoring=None contract remain unchanged.
The CLI needs an explicit command such as:

`python3 -B -m autorouter route BOARD --output NEW --seconds 120 --adapter both --profile completion-only --guidance placement-clearance-v1`

## Small module and worker boundary

1. Promote the reviewed pure `placement_transform.py` as a core pure module
   (approximately249lines). Preserve the tested source/native area census,
   rectangle proof, complete typed DSN attribution, ambiguous overlap rejection
   and all limits. Keeping its inner diagnostic provenance label is acceptable:
   it certifies a transformation, never overall routing. If renamed, change only
   that label explicitly and prove exact output equivalence with retained evidence.
2. Add a small `placement_clearance.py` composition module, not a route driver.
   It owns narrow-source admission, fixed20,000nm planning margin/default50/5
   constants, original-file inventory binding, deterministic chain derivation,
   and a small policy receipt. Reuse the v2 three-atom edit/verifier, restricting
   it to the sole supported setting. No synthetic native context, arbitrary
   margin, mutable callback policy registry or runtime monkeypatch.
3. Extend `floor_context.collect(mode,source,output,dsn=None,area_output=None)`
   with opt-in area observation on its SAME loaded/synchronized object. No second
   LoadBoard/export. Existing calls and JSON stay byte/semantically compatible
   when area_output is absent. Copy the reviewed strict native getter/census loop
   and AREA_LIMITS exactly:512footprints,16zones/outlines,10,000vertices. On the
   new branch validate fresh/distinct output paths and bounded nonempty regular
   nonsymlink DSN before hashes. Preserve the original final floor-context call.
   This removes the diagnostic combined worker's duplicated floor collector.
4. Extend floor_route's export/chain/check path with the fixed enum branch; its
   FloorJob, signal handlers, CPU/wall accounting, source freeze, import/refill,
   metrics, publication and completed-evidence inventory remain ONE lifecycle.
   Factor common result checks into a private helper only where needed to avoid
   duplicating transport/process/final-native checks; do not generalize old policy
   validation to accept arbitrary requested schema, scoring or engine argv.

## Keep the floor contract and acceptance intact

Always retain `native.dsn` → `floor-guided.dsn` → `placement-guided.dsn` →
`planning-guided.dsn` → `task.dsn`, with exact rederivation at readback. The
original `floor-policy.json` remains board-floors-v1 and continues to validate
original derived width/via/drill/clearance dimensions. It is an inner dependency
of the new policy, not a relabeled native context. The new policy receipt binds
all source/task/project/native context hashes, removed-area entries,20µm plan,
three edited atom addresses/values, explicit engine costs and every DSN hash.
Only those three planning clearance atoms differ; all other AST nodes/atoms
must match. Serialization may normalize whitespace.

`pipeline.validate_candidate(...guidance_contract=original_floor_contract)`
can remain unchanged: it already checks original geometry/rules before native
work, actual saved refill, generated floor dimensions, fresh final context and
final DRC. New chain admission must run before engine and be repeated in final
readback. Reuse audit_transport to reconstruct the final candidate from the
original task, retained SES/import and native saved fill. Preserve the original
p.native_accepted predicate;96warnings means whole_project_drc_clean=false.
Do not relax severities, exclusions, thermal rules, keepouts or source geometry.

## Receipt compatibility: separate schema3, no migration

- New outer `schema=3,input_policy=placement-clearance-v1` plus fixed profile,
  costs, scope and policy hash fields. Reject mixed/missing/unknown policy fields.
  Keep old schema1/native/C and schema2/board-floors receipt predicates exact.
- Extend receipt_policy dispatch using BOTH schema/claim fields and top-level
  placement/planning evidence markers. A single-field rename/removal must never
  downgrade a new result to native or floor-only validation. Removing all new
  artifacts cannot make the padded task pass the old exact floor chain.
- Strict duplicate/nonfinite JSON parsing is mandatory for new policy receipts.
  Require new modules in the recorded implementation set only for schema3;
  old saved code directories MUST NOT be required to contain new files. Existing
  generic flat autorouter/*.py snapshot verification can cover new modules.
- Old source/code snapshot hashes remain historical. Do not require an old
  receipt's recorded HEAD to equal today's HEAD. Tools remain pinned and source
  must still be unchanged. Diagnostic schema2/routing_accepted receipts remain
  diagnostic; never promote or rewrite them into production accepted receipts.
- New native export argv gains the area output argument; all other subprocess
  argv/cwd/status/cleanup/input bindings remain exact. Old floor-export and
  final-context argv must remain unchanged. Common final DRC sandbox dispatch
  must recognize both explicit production guidance policies.
- New runs should require implementation/toolchain sources equal committed HEAD
  before native work, matching the reviewed diagnostic. Store a bounded
  policy-source-freeze record and lock snapshot outside the flat code directory;
  check it and hashes before/after publication. Charge Git/metadata subprocesses
  via existing waited-child accounting. The fixed core constants replace an
  experimental protocol file; no dynamic runtime experiment configuration.
- Preserve canonical expected JSON before write, repeated original/candidate/
  full-evidence freshness and post-readback wall/CPU cap checks. Add a new-policy
  receipt digest before/after standalone check_result to catch receipt changes
  during the check; the common publish guard already checks this independently.
- Return input_policy for schema3 from check-result. `handoff.review_copy` currently
  refuses only board-floors-v1 by name: explicitly refuse the new policy too,
  preferably all non-native policies until handoff qualification. Do not silently
  propagate this policy through strategy, recovery, portfolio or paired harnesses.

## Disjoint implementation ownership after lead approval

| Owner | Files | Main acceptance evidence |
|---|---|---|
|Pure/native specialist|NEW autorouter/placement_transform.py, NEW placement_clearance.py; floor_context.py opt-in collector; new pure/native-context tests|Exact v2 DSN output/area-loop parity; source/flags/unknown geometry controls; unchanged old collector action without new arg|
|Lead integrator|floor_route.py lifecycle and check dispatch; pipeline.py routing/schema/sandbox/readback branches; __main__.py guidance choice; handoff.py refusal; documentation|One routing lifecycle; old receipt compatibility; no new policy propagation; real full pipeline|
|Independent reviewer|NEW acceptance/compatibility tests and ignored review record only|Rehashed actual-evidence tampering, budget/cancellation/final freshness, policy downgrade attacks|

Do not split floor_route editing across agents. Agree the small composition API
first (narrow_source, derive_chain, fixed_settings, check_chain); use immutable
values/strict enum dispatch, not user-provided callables. Tests and final source
should be reviewed/frozen before native execution and pushed/read back first.

## Required tests and staged native qualification

1. Rerun relevant existing tests/test_board_floor_policy.py, empty-area, rule-area,
   result and handoff controls. Read back retained accepted native/thermal and
   board-floors-v1 receipts using new checker. Byte-identical old source/output
   preservation required; no historical receipt rewrite. Diagnostic v1/v2 checker
   output remains usable separately from production schemas.
2. Port44 pure placement controls and v2 actual-export margin/derive controls;
   test missing/duplicate/numeric-vs-name nets, exact32MB/source limits, rectangle
   holes/image keepouts, unknown flags/enums, footprint legacy alias, extra DSN
   keepout and wrong source/native area mapping. Rehash outer evidence after
   tampering to exercise semantic guards. Test schema3→2/1 downgrade, profile/
   via-low injection, changed native preferences, swapped stage bytes, changed
   source/rule severity and standalone receipt mutation. Confirm margins modify
   exactly3atoms and original derived width/via contract is unchanged.
3. Run one fresh owned placement+required-via production fixture under60seconds,
   fixed20µm/default50/5, full actual export/engine/import/refill/final/check-result.
   Reuse the meaningful production floor controls: clean positive, undersized
   track/via, missing via opens and changed-rule rejection under complete copies.
   The existing genuine keepout controls are FAILED, so test EARLY refusal;
   never demand a native false-negative become acceptance or weaken the source.
4. Exercise real owned SIGINT/SIGTERM cancellation in the new full route lane,
   plus stale/candidate/report/observer/protocol binding controls on actual saved
   evidence, with originals unchanged and no unrelated process kills.
5. Only then run a fresh full multichannel production replay with120wall/CPU.
   It is new production qualification of an exposed result, not a new fair
   comparison. Check all raw bindings and warnings; retain any regression.
   Independent review and checkpoint follow before updating supported policy docs.

This plan does not acquire boards or alter the14-board considered population.
