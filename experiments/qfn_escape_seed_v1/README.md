# Experimental perimeter escape initialization

This is a bounded development hypothesis, outside the installed router and its
default policy. Owned Native controls are distinct from product acceptance or
routing-quality/support claims.
GPL-3.0-or-later covers the factory and its generated owned CAD.

The completed runtime050 Devobordo cohort delivered no candidate. Its engines
reported timeouts with remaining connections; 57 of 65 non-zone Native opens
touch its QFN. The original reference uses the same 0.2 mm tracks and 0.6/0.3 mm
vias as the unchanged Default targets. This motivates testing outward escape
initialization, without loosening constraints, selecting a policy by board name,
or supplying reference routes to the proposal. The frozen six-arm comparison
remains unchanged. The roomy owned fixture below is a contact/guard control,
not an independent board or evidence of better routing.

`seed.generate(task, original_protected, targets)` accepts a stripped task and
an explicitly bound target map. It emits unchanged-width, front-layer straight
stubs for a narrowly supported orthogonal perimeter geometry. It preserves
original protected copper, skips unsupported shapes visibly and refuses caps
rather than returning a prefix. It creates no vias and proves no clearance.
Footprint overrides, rotations, custom pads and noncanonical copper tables stay
outside this experiment. Version2 preserves noncopper display aliases and leaves
an explicitly solid-connected square centre pad untouched and unseeded. Other
pad overrides still refuse the package. Colliding seeds must fail subsequent
Native validation.

The caller must bind targets to the original rules. A seeded partial-completion
child treats stubs as protected; that child's pass alone cannot establish original
acceptance. Every final must also pass Native refill/full schematic/original
rules and exact Default targets against the immutable original, protecting only
the original protected copper. No generated seed may gain that exemption.

Before any new engine probe, `controls.py` runs one sequential finite batch:

1. Remove all 17 authored reference routes, retain only the locked KEEP, generate
   16 stubs, and add control-only tails to independent external anchors. Require
   actual full schematic Native 0 opens/0 blocking/0 exclusions; retain warnings.
   The version2 control also connects its unchanged solid-zone centre terminal
   using an authored control-only connector after proposal generation.
2. Add an identified cross-net short outside the package. Require actual Native
   errors bound to that short, no changed warning population and no acceptance.
3. Change one generated stub width by 1 nm. Require real refill followed by the
   original Default target guard's refusal, before a final Native acceptance.

The frozen batch reserves 120 s complete wall and full CPU, 105 s actor, 30 s per
Native step, 2 GiB per worker group, 256 KiB per Native log, and 32 MiB aggregate
output sampled at stage/publication boundaries. Shared process/snapshot/PRL/
publication/Native readers are reused. These cooperative sampled bounds do not
contain a hostile same-user writer, SIGKILL or power loss. Failure stops later
cases; no automatic retry or engine follows. No production acceptance is emitted.

Checkpoint and independently verify these sources before `prepare`. Preparation
freezes exact code, installed050 tools, original files, costs and disjoint output
paths. Use fresh names, never overwrite a completed protocol/output:

```sh
runtime=.runs/runtime-directory-050/runtime
"$runtime/.venv/bin/python" -B experiments/qfn_escape_seed_v1/controls.py prepare \
  --preparation "$PWD/.runs/qfn-escape-controls-preparation-002" \
  --output "$PWD/.runs/qfn-escape-controls-native-002" --head VERIFIED_COMMIT
# Inspect and retain the returned protocol/hash before the single bounded run.
"$runtime/.venv/bin/python" -B experiments/qfn_escape_seed_v1/controls.py run \
  --protocol "$PWD/.runs/qfn-escape-controls-preparation-002/protocol.json" \
  --sha256 FROZEN_SHA256 --output "$PWD/.runs/qfn-escape-controls-native-002"
```

Record external wall/CPU for preparation and run, including failures. A future
engine comparison needs a separately frozen finite protocol, unchanged inputs,
constraints and complete budgets, plus validation against the original. Positive
controls authorize no product integration or superiority claim by themselves.

[Version1 actual prerequisites](../../evidence/qfn-escape-native-prerequisites-001.json)
completed once: positive0/0/19/0, short0/2/19/0, generated width+1nm refused after
real refill/map before final DRC. Complete external run8.57wall/6.22CPU plus
preparation1.01/.52; warnings and two ignored checks remain. Those results do not
qualify changed version2. A source-only eligibility check stopped version1 on
noncopper display-name syntax before any engine test; centre-pad inspection found
the second selection blocker. Both failures are retained. Version2 changes source
grammar/selection, not targets, length policy or original boards. The changed
35-pad owned control needs its own fresh Native results.

`probe.py` is a single separately frozen exposed-development diagnostic using
the unchanged installed partial Route with420s allocation and450s complete method
cap. Derivation/queries/generation/selection and independent whole-original final
validation count; complete exit is bounded600s. Existing six-arm results remain
development references, not a fresh comparison. There are no length, via,
neckdown, optimizer or board-specific variants. Final protection includes only
original locked copper. Parent acceptance, production and delivery flags remain
false even for a clean diagnostic. No graphical/delivery implementation or
export is established by this probe; its120s export reserve is unspent.

Only run after current version2 prerequisites and reviewed source are checkpointed.
Freeze exact outputs before the single attempt. Record preparation with the
existing complete-exit format at `PREPARATION_PATH-time.log`; pass that file's
completed SHA with `--preparation-time-sha256` to `probe.py run`. The shared
comparison cost parser charges that complete preparation cost; the earlier
stored setup sample cannot substitute for it. Preserve failures and stop: no
automatic retry, policy selection, product integration or stronger quality claim.
