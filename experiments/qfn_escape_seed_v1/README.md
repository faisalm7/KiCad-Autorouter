# Experimental perimeter escape initialization

This is a bounded development hypothesis, outside the installed router and its
default policy. It has no routing-quality, Native acceptance or support claim.
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
Footprint overrides, rotations, custom pads and noncanonical layer tables stay
outside this experiment. Colliding seeds must fail subsequent Native validation.

The caller must bind targets to the original rules. A seeded partial-completion
child treats stubs as protected; that child's pass alone cannot establish original
acceptance. Every final must also pass Native refill/full schematic/original
rules and exact Default targets against the immutable original, protecting only
the original protected copper. No generated seed may gain that exemption.

Before any new engine probe, `controls.py` runs one sequential finite batch:

1. Remove all 16 authored reference routes, retain only the locked KEEP, generate
   16 stubs, and add control-only tails to independent external anchors. Require
   actual full schematic Native 0 opens/0 blocking/0 exclusions; retain warnings.
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
  --preparation "$PWD/.runs/qfn-escape-controls-preparation-001" \
  --output "$PWD/.runs/qfn-escape-controls-native-001" --head VERIFIED_COMMIT
# Inspect and retain the returned protocol/hash before the single bounded run.
"$runtime/.venv/bin/python" -B experiments/qfn_escape_seed_v1/controls.py run \
  --protocol "$PWD/.runs/qfn-escape-controls-preparation-001/protocol.json" \
  --sha256 FROZEN_SHA256 --output "$PWD/.runs/qfn-escape-controls-native-001"
```

Record external wall/CPU for preparation and run, including failures. A future
engine comparison needs a separately frozen finite protocol, unchanged inputs,
constraints and complete budgets, plus validation against the original. Positive
controls authorize no product integration or superiority claim by themselves.
