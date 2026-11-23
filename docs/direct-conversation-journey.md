# Direct requests beside the board

The documented Cursor workflow attaches a selection in place and keeps
follow-up instructions with the plan. Flux documents attaching selected PCB
objects to requests and keeping partial-routing intent visible near the
canvas. Copperpath can use the same interaction principles in its existing
wx workspace. A small context summary and a revisable proposal are enough
for this task. Copperpath retains its own separate approval, Native checks
and delivery. These references describe vendor behavior. Copperpath has
tested its own workflow. [Cursor Design Mode](https://cursor.com/docs/agent/design-mode) ·
[Cursor Plan Mode](https://cursor.com/docs/agent/plan-mode) ·
[Flux PCB editor](https://docs.flux.ai/reference/reference-pcb-editor) ·
[Route with Flux](https://docs.flux.ai/reference/route-with-flux)

## Capability map

| Layer | Implemented and tested scope | Limit and next verification |
| --- | --- | --- |
| Design state and identity | Saved source inventory, PCB UUIDs, exact names and nanometres bind canvas picks and requests. The installed composer showed selected parts, the checked area and the saved layer. | Keep saved inspection distinct from editor snapshots. Extend verified schematic parity to explicit global power symbols before connecting the retained licensed cases to active selection. |
| Language and AI | The installed local parser resolved the two selected parts, the named outline and a time revision in one composer. Exact board questions and explicit commands still work. Hosted context remains bounded to three prior replies and 4,096 bytes. | Local wording is deliberately limited. Tests exercise varied wording, conflicting clauses and missing context. General interpretation requires its own authorized live evidence. |
| Planning and execution | The shared proposal checked the complete local task even when current settings already matched. Display, edits, explicit adoption and later approvals remained separate. | Saved files, ordinary controls and newer edits supersede older proposals. Test current editor identity separately before carrying an active selection into new execution paths. |
| Placement and routing | The constrained search uses estimated connection length and rectangle geometry. The first checked alternative moved R2. Freerouting rebuilt only the approved nets under unchanged budgets. | The task achieved the same geometry as the reference. TankSync exceeds the supported placement limits. Broader changes need separate licensed cases and measured comparisons. |
| Physics and electrical | KiCad rules and design invariants cover configured geometric and connectivity checks. | An electrical claim needs defined terminals and limits, actual stackup and geometry, and an independent calculation or measurement. For a future explicit length task, verify the specified path and via conventions against independent CAD measurements before supporting a limit. |
| Verification and recovery | Separate validated candidates, exact source and protected copper checks, explicit rejection and fresh export. One scoped live move with native Undo on isolated KiCad 10.0.8. | Test revoked request and candidate states, active cancellation and independent readback. KiCad 9/10 documented IPC is online and PCB-only. Schematic editing, public docking and broader live writes require separate verification. [KiCad add-on API](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html) · [Live move evidence](../evidence/product-integrated-rc-editor-001.json) |

## Frozen licensed task and comparison

Use the retained MIT PushButtonLed project at upstream commit
`29c46b7c03d2afd9fe3a58fe2070309b12f94b42`. It is an exposed workflow case.
Keep all five source hashes from the retained protocol
`246442d0c999e76dd5f791dc754be1b2674efe8215cebd348ad715611a699e6e`.
Select R1 and R2 in the board view. Allow movement inside the existing
outline rectangle from (23, 24.5) to (42.5, 43.5) mm, explicitly named as the
board outline in the request. C1, D1, J1, R3 and SW1 stay in place without
changing their KiCad lock flags. Only the three affected nets may be rebuilt
under the same existing-copper permission. Retain the 13 protected tracks,
all rules, schematic and zone intent. Use the first alternative, seed 7,
160 steps, two alternatives and a two-second search. The final routing
budget stays 90 seconds. The 420-second task envelope, 15-second return
reserve and stage limits from the frozen protocol still apply.

The direct request describes moving these two parts within the board outline,
leaving the others in place, preserving protected copper and reconnecting
only affected nets. Request 80 seconds initially, then revise the budget to
90 seconds in the same composer. The scope, area and protection must carry
over. The 80-second version is a preview and runs no engineering operation.
Use the ordinary adopted settings path, review the proposed moves, validate,
route, review findings, accept and freshly export a separate project.

The installed `79be782a6` reference took 13 ordinary actions plus two optional
finding-location actions, with independent readback at 340.0 seconds including
observer recovery. Its result has zero open connections, zero blockers, seven
inherited warnings, 28 segments including 13 preserved, 93.786421 mm of track
and zero vias. The connected publisher layout has 88.395766 mm. This is a
constraint-preserving modification task. [Reference and scope](design-review-refinement.md)

The additional TankSync receiver case uses the already retained licensed
project, layer and item navigation. Select an actual pad or net and ask
about the selection. The response must identify the saved observation and
its scope. A placement request must explain the actual refusal, including
U2's 38 pads against the qualified eight-pad limit. The native source has
zero open connections. The read-only control shall run no routing.

## Required observations

- Actual installed board and composer at 880 × 610 and 1040 × 720, with
  visible context, an editable plan, readable findings and an obvious next
  action. Save before and after screens. Record user actions and waits
  separately from any observation/control interruptions.
- Exercise a missing or ambiguous reference, unsupported electrical request,
  exact unit conversion, intervening source or controls change, and active
  cancellation on disposable owned inputs. Prior drafts must have no
  authority when context changes. The explicit decisions for moves,
  routing and delivery still apply.
- Count whole-task and individual waits, CPU/memory observations, manual
  CAD corrections, route geometry, any unsupported result and every warning.
  The local parser uses zero model calls and no new spend. Existing
  saved-response and controlled-reply tests retain their original scope.
  No new hosted call is authorized.

## Installed outcome

On macOS arm64, `27086bcf7` completed the task using KiCad 10.0.7 and
Freerouting 2.5.0. The first preview displayed R1 and R2, the exact outline
and the protected copper. Revising from 80 to 90 seconds kept all of that
scope. The viewport kept the board beside the request through review. The
final copper comparison retained 13 original tracks and placed all 15 new
segments on the three approved nets. R2 moved 0.327 mm. R1 and the five
unselected components stayed at their original poses. All five source
files, checked project/rules, schematic and zone intent matched.

| Observation | Prior installed reference | Direct request |
| --- | ---: | ---: |
| Ordinary actions | 13 | 17 |
| Independent readback from task start | 340.0 s | 275.6 s |
| Trace length | 93.786 mm | 93.786 mm |
| Opens / blockers / inherited warnings | 0 / 0 / 7 | 0 / 0 / 7 |
| Vias | 0 | 0 |
| Manual CAD corrections | 0 | 0 |

The extra four actions were two visible component picks and one two-action
revision. The direct run includes one missed observer click, an interruption
observing export and a later confirmed delivery by 264.4 seconds. Native
preview, route, review, choice and export commands took 4.9, 18.2, 12.4,
10.7 and 32.9 seconds respectively. Independent readback took 10.9 seconds.
The sampled engine and readback process-group peaks were 212.3 and 227.9
MiB. Admission observed normal pressure and 3.26–3.77 GiB available RAM.
Treat the wall times as observations of separate sessions with different
observer interruptions. They establish no solver or speed gain.

TankSync's saved +3V3 selection identified 25 displayed items and actual
pad labels on B.Cu. Its placement refusal names U2 and the 38-versus-8 pad
limit. The additional case produced no engineering job. On an owned copy,
missing selection and an unspecified electrical workflow produced refusals.
A keyboard edit required a fresh preview. A deliberate saved project change
withheld adoption and refresh kept the request for a fresh check. Cancelling
an active Native routing preview withheld its result and export.

The `ffcfebac1` presentation follow-up displayed the proposed parts and
exact area at both declared laptop sizes, accepted Command–Return for a
review, and removed the expired suggestion note after refresh. The follow-up
ran no routing. The 79be782a6 structured entry, direct revision, delivered
copper and the final layout are retained as local screens with checked
hashes. No model call, new spend or human PCB approval was recorded.
[Run and screen index](../evidence/product-direct-conversation-001.json)

To use the local workflow, open a saved project, choose the existing-copper
policy, and click the parts you want to move. Draw a region or name the
board outline in the request. Preview, edit or revise, then use the checked
settings to find alternatives. Review the actual moves, routing and
findings before accepting a separate project. Try “What is this net?” after
selecting a net in a saved board view.
