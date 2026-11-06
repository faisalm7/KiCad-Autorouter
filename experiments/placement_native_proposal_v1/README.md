# Placement Native feasibility probe v1

Prepared for lead review; **no Native execution has occurred**. This experiment
tests whether the existing constrained search can produce one faithfully saved
KiCad placement proposal. It does not route, accept a routing result, modify the
original project, apply changes to an editor, or confer human approval.

The pinned seed is GUI105's project-owned ordinary transport fixture. Its PCB,
project, complete schematic and local settings are copied into a new owned task.
Only the four top-level route items are removed from that new task; their UUIDs,
lock states and AST hashes are recorded. The original four-file source remains
hash-bound and immutable. The derivation is explicit and is not an improvement
claim over the routed seed.

Scope is deliberately narrow: two selected footprint UUIDs (J1/J2), translation
only, unchanged zero rotation and front side; six other footprints are fixed.
The source has a rectangular outline, no cutouts or keepouts, symmetric
rectangular courtyards and zero or one centred circular PTH pad per footprint.
The selected region is disjoint from the preserved ordinary copper zone. No
tracks or vias remain in the derived task. Groups, other outlines, pad stacks,
custom or offset pads, flips and rotations are refused. Integer nanometres are
authoritative; the proxy validator also refuses extents below one nanometre.
Duplicate reference labels are allowed because footprint and pad UUIDs supply
identity.

The installed 075 runtime is imported before source experiment modules. It pins
KiCad 10.0.7 and uses its existing `FloorJob`, process runner, isolated settings,
full schematic parity checks, Native refill, DRC evidence readers and receipt
publication helpers. The Native worker independently observes actual outline,
footprint, pad/net, courtyard and zone geometry before calling the constrained
prototype. That prototype reuses the unmodified MIT upstream search pinned in
`../constrained_placement_v1/upstream.json`; it supplies no KiCad writer.

Only the isolated pinned SWIG worker may translate the owned candidate copy.
Every proposal is independently constrained before and after quantization to
one nanometre. The entire saved PCB AST must equal the original task with only
the two selected XY coordinates changed, except for derived top-level zone fill.
No serializer normalization, UUID creation, rule change, net remapping, field
rewrite, unselected movement or zone-intent change is exempted. Such changes
retain the raw candidate and a failure. In particular, API coordinate semantics
and Native SaveBoard preservation remain unqualified until this actual probe.

A successful probe requires actual full-SCH Native checks on the derived task
and final saved candidate, actual refill, unchanged non-open Native findings,
unchanged sidecars, exact identity/geometry comparison and successful process
cleanup. Unrouted demand remains explicit. `accepted`, `routing_accepted` and
`human_approval` remain false; the strongest outcome is a bounded placement
proposal for review. Failure does not trigger an automatic retry.

The prospective envelope is 120 seconds total wall/parent-plus-waited-child CPU,
with 110 seconds for the inner work and one second reserved for publication.
Temporary output is capped at 512 MiB with the existing 3 GiB disk reserve.
The existing 2 GiB process-group RSS polling limit is retained; it is not an OS
memory quota. The controller reads the completed worker result and exit status.
Its final receipt reports that its own exit has not been measured.

The reviewed command must retain the protocol digest below. Run it **once only
after lead review and a pinned checkpoint** from the selected checkout:

```sh
'.runs/runtime075 fresh install 001/.venv/bin/python' -B \
  experiments/placement_native_proposal_v1/driver.py \
  --runtime '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime075 fresh install 001' \
  --protocol '/Users/faisal/Projects/KiCad-Autorouter-local/experiments/placement_native_proposal_v1/protocol.json' \
  --protocol-sha256 257dc89b11813a2b87ae366d5532eb14377584e3c4ef73074106c116ef88ac99 \
  --output '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/placement-native-proposal-v1-001' \
  --execute-native
```

The output directory must not exist. The existing quality-experiment lane lock
must be free. All outputs, including failed Native stages and process logs,
remain there. Read `execution.json`, then `work/result.json`; never interpret a
proposal or worker observation alone as successful qualification.

Small pure checks, with the installed runtime first and no Native module import:

```sh
'.runs/runtime075 fresh install 001/.venv/bin/python' -B -c \
'import sys,unittest; from pathlib import Path; r=Path.cwd(); sys.path[:0]=[str(r/".runs/runtime075 fresh install 001"),str(r)]; unittest.main(module="experiments.placement_native_proposal_v1.test_contract",verbosity=2)'
```

`preparation-evidence.json` records the ten passing pure controls and the actual
static seed census. These checks are not evidence of Native or GUI correctness.
