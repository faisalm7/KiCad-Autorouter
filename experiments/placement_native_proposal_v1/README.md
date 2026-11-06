# Placement Native feasibility probe v1

**Probe004 passed source-preserving placement qualification; its exact candidate
then completed installed075 routing and fresh export.** [Placement evidence](../../evidence/placement075-native-proposal-004.json) and [routing evidence](../../evidence/placement075-installed-routing-001.json) retain the actual bounds and limitations. Probe003 passed Native capture and in-memory translation, then failed the strict SaveBoard comparison. Native serialization
changed the version, net representation and other source fields. The raw003
candidate and failed receipt remain preserved. Earlier001/002 capture failures
also remain preserved. This experiment
tests whether the existing constrained search can produce one faithfully saved
KiCad placement proposal. It does not route, accept a routing result, modify the
original project, apply changes to an editor, or confer human approval.

The prospective `multipad-preserve-v1` scope extends the same worker to multiple
offset circular PTH pads and straight retained segments. Selection and region
are explicit, hash-bound inputs. Every component sharing any routed net remains
fixed, and the movement region must avoid clearance-expanded retained segments
and zone envelopes. Arcs, vias, side changes, rotation and overlapping movement
regions remain outside this scope. No existing copper is removed.

The new project-owned complete-schematic fixture has two selected two-pin
connectors, four fixed terminals, eight pads, one locked KEEP segment and an
ordinary GND zone. Two fixed-seed alternatives are requested; the first returned
proposal is selected prospectively for Native qualification, without comparing
later routing outcomes. Other alternatives are geometric proposals only. This
is an exposed development fixture, not an unrelated or untouched family.
[Native006](../../evidence/placement075-native-proposal-006.json) passed this scope: two selected translations, four fixed components, eight pads and one exact retained locked KEEP segment. Source/refill/final full-SCH checks each retain two opens, zero blocking findings, warnings or exclusions. [Failed005](../../evidence/placement075-native-probe-005.json) remains refused for six authored Datasheet mismatches; source002 fixes only those fields prospectively. The installed075 runtime remains unchanged; installed placement/GUI support is not established. [Its later installed routing/export](../../evidence/placement075-installed-routing-002.json) also passed, retaining the original locked trace, with0 opens/blocks/warnings/exclusions.

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

Every proposal is independently constrained before and after quantization to
one nanometre. The entire candidate PCB AST must equal the original task with
only the two selected XY coordinates changed, except for derived top-level zone
fill. No version change, net remapping, field rewrite, UUID creation, rule change,
unselected movement or zone-intent change is exempted.

`native-save-v1` remains the default application policy. It uses the pinned
SWIG `SaveBoard` method and applies the original strict comparison. Its003
failure is unchanged. `source-translation-v1` is a separate prospective policy
bound explicitly in the command, protocol, worker request and receipts. It first
checks actual Native geometry and `SetPosition` in memory, then writes only the
translated source AST into the owned candidate and reloads that copy with Native.
It never writes the Native serialized board over the candidate.

For the new policy, `refill-preimage` retains the exact candidate project before
refill. Native full-SCH refill with `--save-board` runs on a separate
`refill-native` project. The shared `pipeline.transplant_fill` transfers only
derived top-level zone fill into the preserved candidate. The raw Native output
is retained even when it changes serialization. Final full-SCH Native checks,
actual geometry/flags/net-code readback and the strict source AST comparison
still apply to the exact candidate. Final freshness replays the shared saved
refill stage and reconstructs the candidate byte for byte from the retained
preimage and Native output. Every Native warning remains recorded.

`native_save_board_called` refers specifically to the SWIG application worker's
`SaveBoard` call. The separate Native CLI refill write is recorded as
`refill_save_board_requested` and `refill_saved_copy`; a false SWIG flag does not
mean that the separate refill copy was never saved. A crashed worker can leave
the SWIG flag unknown rather than falsely reporting that no call occurred.

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

The completed004 reproduction command is retained below. **Do not rerun it merely
to resume, and never reuse its output directory.** A deliberate reproduction needs
a fresh protocol/output bound to the intended source revision:

```sh
'.runs/runtime075 fresh install 001/.venv/bin/python' -B \
  experiments/placement_native_proposal_v1/driver.py \
  --runtime '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime075 fresh install 001' \
  --protocol '/Users/faisal/Projects/KiCad-Autorouter-local/experiments/placement_native_proposal_v1/protocol-004.json' \
  --protocol-sha256 8baade73f872119156fac76b9134de73ca92ac4da5b0561ba15085abbc6d7a8e \
  --output '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/placement-native-proposal-v1-004' \
  --application-policy source-translation-v1 \
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
The current source-translation preparation passes17 pure controls in0.063s using
installed075 imports first. The new controls cover explicit policy selection,
strict rejection of normalized Native output, fill-only reconstruction, changed
preimages/fill/candidate bytes, and missing/duplicate/extra zone identities. These
are synthetic pure controls. The later004 Native and place-to-route receipts above
supersede this preparation state; they do not qualify GUI placement or broader components.

Independent review found a missing post-worker runtime/tool freshness check. The
outer gate now rechecks the manifest, SWIG wrapper and actual tool pins, and
samples its budget after that work. Eleven pure controls pass, including actual
small-file mutation after worker exit and during the final tool read. The original
preparation record and protocol remain preserved at commit840c91c61. No Native
run preceded this correction.

Probe002 retains the same120s total/110s inner limits. Twelve pure controls
pass after the enum correction; the original protocol and all001 evidence stay
unchanged. Preparation now refuses to overwrite a protocol or reuse an output.

Probe002 also stopped before search or saving: its extra all-false check mistook
inactive ordinary-zone defaults for active keepouts. [Its failure is retained](../../evidence/placement075-native-probe-002.json).
The existing shared source-zone parser and [KiCad10.0.7 serializer](https://github.com/KiCad/kicad-source-mirror/blob/10.0.7/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp#L2712)
distinguish these from actual rule areas. Probe003 records all flags unchanged
before/after translation/save/refill and still refuses actual keepout/placement
areas. Thirteen pure controls pass; the same120/110s envelope remains.
