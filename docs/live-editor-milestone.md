# Copperpath in an open KiCad board

Keep the toolbar entry and a compact companion beside the board. Show the
current project and selection above a before/after diagram. One primary action
advances the task. Rejection clears the proposed change. After a verified
application, show what changed and point to KiCad’s native Undo. Keep advanced
constraints and full findings available below the main controls. The companion
should need neither a browser nor a second project selection for this task.

## Pinned interface

The existing 10.0.7 installation already supplies the official local IPC
client. The public PCB commands expose document identity, selection and
in-memory board serialization. Source shows that PCB commits can be pushed
or dropped. Commands are separate IPC requests and do not carry a board
revision precondition. The footprint update also replaces the footprint
through a protobuf conversion. Check exact metadata retention, partial failure,
user edits between requests and native Undo before offering a general live
write path. The initial experiment is restricted to a disposable owned PCB.
[PCB handler](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/pcbnew/api/api_handler_pcb.cpp) · [Transaction handler](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/common/api/api_handler_editor.cpp)

Capture the editor PCB in memory and keep the saved project/rules/schematic
identity separately. Validate a detached candidate with the shared placement
and Native checks before any approval permits a write. A board snapshot alone
cannot establish the state of an unsaved schematic or unsaved project settings.
The source project remains open during a bounded validation. Recheck the
editor and saved inputs before beginning a short transaction, after staging
and after commit. A failure drops only Copperpath’s uncommitted operation.
Reloading the project would destroy unrelated unsaved work.

## Preview, docking and schematic boundaries

The companion has its own preview. KiCad's manifest launches a separate
process, and the pinned API exposes selection and viewport controls. It does
not register third-party dock panes or a general preview layer. Built-in PCB
panes use KiCad's internal docking manager. A small upstream pane/overlay
interface would keep deployment compatible with stock KiCad. Maintaining a
fork would require ongoing rebases, platform builds and signing, and GPL
source and notice obligations. Continue with the companion and evaluate an
upstream extension before any decision to maintain a fork.
[Pinned manifest](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/api/schemas/api.v1.schema.json) · [Native panes](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/pcbnew/pcb_edit_frame.cpp#L324) · [Licenses](https://www.kicad.org/about/licenses/)

KiCad 10.0.7 includes partial schematic IPC code. Its document query lacks
full project and sheet identity and item operations are incomplete. Start
with saved schematics. KiCad 11 development exposes hierarchy, sheet-aware
selection, netlist, ERC and typed writes. Revisit a narrow edit and Undo
after an installable target can be qualified. Its development manifest still
uses plugin actions.
[Pinned schematic handler](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/eeschema/api/api_handler_sch.cpp) · [Schematic IPC development](https://docs.kicad.org/kicad-python/schematic.html)

## What happened in the editor

The experimental action opened a 486 × 455-point companion beside the
disposable PCB. Selecting J1 in KiCad supplied its reference and position.
Copperpath captured the unsaved PCB without saving it. The IPC serializer
wrapped each footprint in a redundant copy of the version and generator
headers. The detached validator removes only these exact duplicate headers.
Its checks preserve the full footprint, original rules, protected copper and
the rest of the source. The isolated pinned checks found two existing open
connections, zero blocking findings, one inherited text-height warning and
two original ignored checks, with refill and schematic parity.

| Experiment | Observed result |
|---|---|
| Direct IPC footprint update | The commit moved J1 exactly. Readback found the missing footprint `units` node. KiCad's named Undo restored the exact prior PCB. This write is absent from the default experiment. |
| Rejection, stale state and drop | Discard returned the same PCB hash. An unsaved J2 edit changed the snapshot and refused the old J1 plan. A staged update and a mixed update with a missing second item both dropped to the exact original state. |
| Interactive tool handoff | The IPC call returned without an observed active move tool. A later call returned an API error. The companion uses user-controlled native **Move Exactly** for the guided check. |
| Same-editor manual move | After review, the operator-equivalent action used KiCad **Move Exactly** to shift J1 from X 14 to 15 mm at Y 10 mm. Exact readback verified every other item, including the unsaved J2 position at X 25.5 mm. The saved PCB, project and schematic stayed unchanged. Cancelling the native properties dialog in the earlier guided check also left the PCB unchanged. |
| Undo | The earlier footprint-properties Undo did not restore the reviewed board. The later named **Undo Move Exactly** restored J1's position and kept the unsaved J2 edit, but four J1 field UUIDs changed. Exact readback refused restoration in both cases. |

The final guided attempt took 64.49 seconds and nine observed actions from
preview to verified readback, then 72.72 seconds through the failed Undo check.
Those observations include pauses between automated controls. The two detached
KiCad operations took 1.61 seconds combined.
The native move took one deliberate coordinate entry and one native
confirmation. A keyboard attempt before the canvas regained focus did not open
the dialog. The log distinguishes that automation issue from the loss of
metadata. The companion and local IPC process used roughly 161 MiB combined
resident memory in a single sample. The largest detached KiCad process peaked
at about 202 MiB. No paid or local inference ran.
[Structured receipt](../evidence/live-editor-capability-001.json)

Automatic placement and routing in the open editor need a supported, lossless
transaction and an exact Undo proof. A representative native test must also
cover edits during computation, concurrency at write time, interruption and
several editor inputs. Keep runtime104's existing separate-project path for
ordinary delivery. The companion's actual preview remains a separate window.

## Reproduce the owned-board companion

### Checked move on 10.0.8

The bounded continuation verified one approved IPC translation in the isolated
10.0.8 editor, followed by exact native Undo. KiCad 10.0.7 ran the detached
validation with the original rules and schematic parity. J1 moved one
millimetre. Its unit and pin grouping, IDs and metadata survived along with
the locked trace, zone, original files and J2's unsaved edit. The earlier
stale-state, cancellation and mixed-update controls retain their original
scope. [Direct move receipt](../evidence/live-editor-1008-direct-002.json)

Prepare the companion with the same pinned 10.0.7 runtime and add
`--direct-1008-trial` to the command below. Open the generated **Launch Checked
Live Move.command**. It verifies the exact isolated 10.0.8 manager and app
signature and opens the disposable fixture in a private KiCad profile.
Open PCB Editor, select J1 or J2, and use the Copperpath live-check toolbar
action. **Preview move**, **Check move** and **Apply checked move** are separate
actions. Use KiCad **Edit → Undo Copperpath checked component move**, then
**Verify KiCad Undo**. One application is supported per companion session
on this exact fixture. The same operation is now available from the ordinary
launcher when prepared with the pinned checked-move editor option. The
saved-project workflow still uses the pinned 10.0.7 validation tools. KiCad
can show a modified indicator even after Copperpath verifies that Undo
restored the prior board. [Ordinary launch](install-existing.md#try-the-checked-move-on-the-supplied-example) · [Installed result](../evidence/product-workspace-live-toolbar-2427-001.json)

Use the unchanged local runtime with KiCad 10.0.7 and the pinned
`kicad-python` client described in [installation](install-existing.md).
Prepare a fresh scoped launcher with that runtime's Python.

```sh
"$runtime/.venv/bin/python" -B experiments/live_editor_v1/prepare.py \
  --runtime "$runtime" --run "$PWD/.runs/live-editor-owned-reproduction"
```

Open the prepared **Launch Autorouter.command** and the project under its
`inspection` folder. In PCB Editor choose the **Copperpath: open board**
toolbar action. Select a footprint such as J1 in KiCad, then use **Read
selection**, **Preview move** and **Check move**. **Review in KiCad** explains
the manual native operation. **Check KiCad move** only reports success if the
reviewed result matches the open board. Use this test only on the supplied
disposable copy. The pinned test had an Undo metadata failure. The default
companion issues read/check requests and performs no PCB writes. The
`--diagnostics` option adds two scoped dropped-transaction controls.

## Placement constraints from a request

V2 accepts one or more exact observed reference labels, a movement rectangle and routing
time. A null field leaves its visible value alone. The review returns the
before/after settings and the prospective copper plan. The same placement
validator binds fixed components, original policy, protection and region limits.
The consumer must pass the currently displayed saved project, request and
control revision at receipt and explicit adoption. A source change is checked
again at adoption. The placement window's **Conversation** tab uses this path for
explicit local requests. For example, enter the following three lines through
the ordinary interface.

```text
Select J1, J2
Area 14, 8 to 22, 13 mm
Routing time 75 s
```

Preview the changes against the saved board, edit the proposed values if
needed, then choose **Preview edits** and **Use settings**. The text review
lists the exact changes and any affected copper alongside the map. Approval
updates the ordinary controls. Finding alternatives, validation, routing and
delivery still require their own user actions. Discard leaves the ordinary
settings alone. This entry point uses deterministic parsing of explicit
settings. The saved-project companion and optional hosted workflow use the same
guarded settings. The earlier hosted pilot retains its measured result and scope.
The single-part extension was verified with local controls and controlled data.
[Installed single-part request](../evidence/product-conversation-single-part-001.json)

## Bounded follow-up on live writes

Scope was a 12-minute source and captured-board check, with no native rebuild
or rerun. The direct IPC update and the guided native Undo have distinct
causes. Exact comparison of the stored owned-board inputs and outputs
preserved the footprint UUIDs, schematic symbol paths, pad identities and
net records, protected copper and the unrelated J2 position in both cases.

- **IPC replacement.** The lost node was `(units (unit (name "A") (pins "1" "2")))`,
  a symbol-unit and pin grouping used by gate swapping. Existing connectivity
  on this sample does not establish equivalence for that engineering content.
  KiCad 10.0.7's protobuf omitted the field. KiCad 10.0.8 adds
  `FootprintInstance.symbol_units` and serializes it in both directions.
  A synthetic binary round trip through the current Python client retained the
  unknown field. Actual editor readback and Undo still need qualification.
  [10.0.8 release notes](https://www.kicad.org/blog/2026/10/KiCad-10.0.8-Release/#ipc-api) ·
  [Upstream report](https://gitlab.com/kicad/code/kicad/-/work_items/25859) ·
  [10.0.8 footprint implementation](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/pcbnew/footprint.cpp)
- **Native Move Exactly Undo.** In the observed sample, the changed nodes
  were the UUIDs of J1's Reference, Value, Datasheet and Description fields.
  Their values and rendering geometry stayed equal. The native commit
  snapshots a footprint using a copy constructor that assigns those fields
  to newly created objects. Assignment keeps the new UUID. Development
  source explicitly restores the originals. Four field identities changed
  even though the parent footprint, pad identities and schematic association
  stayed intact. Downstream consumers that refer to those field identities
  have not been qualified.
  [Pinned snapshot implementation](https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/pcbnew/board_commit.cpp#L699) ·
  [Development copy implementation](https://gitlab.com/kicad/code/kicad/-/blob/master/pcbnew/footprint.cpp#L285)

The official 10.0.8 Mac application was acquired and placed in an isolated
project folder with its published image digest, Apple signature, notarization
and arm64 command verified. The supported 10.0.7 installation stayed in place.
The real 10.0.8 editor reported J1's unit and pin grouping and showed the
unrelated unsaved J2 move. Cancelling a full stage and dropping a mixed update
(statuses 1 and 4) preserved the exact board. After a second unsaved J2 edit,
the old move failed the freshness check before Native work. The original three
files stayed exact, and the last test edit was retained via a separate
**Save a Copy** before closing the owned editor.

The planned direct apply and Undo needed fresh isolated Native validation.
macOS kept memory pressure at warning level during admission. The 25-minute
trial ended with zero positive apply attempts and no Undo. Unit preservation
after replacement and exact Undo are still open. Keep both preservation
checks and the separate-project fallback. The lab switch in
`experiments/live_editor_v1` is for this exact owned fixture. The product
launcher still pins 10.0.7.
[10.0.8 transaction implementation](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/pcbnew/api/api_handler_pcb.cpp#L496)
