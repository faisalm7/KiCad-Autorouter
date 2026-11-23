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
| Design state and identity | Saved source inventory plus PCB UUIDs, exact names and nanometre geometry. Canvas transforms support component picks, pad and net inspection, and rectangular areas. | Show exact visible selections in the request and verify changed files and controls invalidate them. Keep saved inspection distinct from editor snapshots. |
| Language and AI | Local typed commands, reviewed hosted proposals and clarifications. Hosted conversation bounds context to three prior replies and 4,096 bytes. | Add a bounded local reading of selection references and same-composer revisions. Test varied wording, conflicting clauses, questions and missing context. Label each evidence source. |
| Planning and execution | Typed v2 placement proposal, copper policy, selected-net routing and separate explicit decisions bind to the current saved state. | Let the proposal carry whole task intent even when visible settings already match. Test cancellation and exact-plan invalidation. |
| Placement and routing | Qualified small-board search and Freerouting for selected connections. Search favors lower estimated connection cost on admissible geometry. | Verify the same task and fixed solver budgets. Report component movement, length, vias, connections and independent Native checks. TankSync exceeds existing placement limits. |
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
