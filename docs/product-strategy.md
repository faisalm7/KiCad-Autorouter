# Product decision — November 5, 2026

Build one local KiCad design assistant around the existing engineering core. Routing, constrained placement and an optional copilot share the same inspection, constraints, execution, validation, preview, approval, delivery, progress and cancellation operations. Ordinary graphical controls remain fully usable without AI. This owner-directed revision supersedes the old placement/copilot prohibition and algorithmic-superiority gate; the original routing research ambition is unmet/deferred, not achieved.

## Native editors — November 23 owner clarification

Copperpath's primary workspace lives inside KiCad's PCB and schematic
editors. A persistent native pane uses the current canvas selection and
unsaved document. Proposed changes appear on the KiCad canvas. Explicit
approval applies a checked change to that document through a native
transaction with verified Undo and Redo. The separate-project workflow
remains available as a tested fallback.

Start with the bounded component move and the same preservation checks.
Then qualify a sheet-aware reference-field move with actual connectivity
and ERC. An isolated native extension may be needed where the public API
lacks hosting and overlays. Keep optimization, validation and optional
model inference off the editor thread. Document exact app and tool versions,
worker limits and upgrade costs before broader deployment.
[Native architecture and proof criteria](native-editor-foundation.md)

## Earlier companion milestone — November 18

Copperpath should feel like part of the active design. The intended workspace
keeps a persistent assistant beside the board, offers Auto-place and Auto-route
without a model, and keeps visual controls and conversational constraints in sync.
Users should be able to see proposed changes and findings, approve specific
changes, watch them appear in the editor and use KiCad Undo. Schematic assistance
is part of the product. Start with grounded context from saved schematic files,
then qualify reversible, sheet-aware editing with netlist and ERC checks on a
supported KiCad version.

The next milestone is one selected component on an owned disposable PCB.
Copperpath reads its actual editor and current selection, shows a move in its
own companion window, and tests an explicitly approved transaction and native
Undo. Unsaved PCB bytes, unrelated edits, protected copper and the original
project settings matter to this test. Group placement and routing reuse the
qualified deterministic tools as live application becomes supportable. The
runtime104 saved-project workflow remains a supported fallback. The
[integration capability record](live-editor-milestone.md) tracks the pinned
interface and the conditions for expanding scope.

Add a versioned intent contract for changes to selection, region and preferences.
Show those edits before adopting them in the ordinary controls. Locks, fixed
components, copper permissions, rules and execution authority stay with the
shared engineering workflow. Keep the earlier contracts and recorded model
results intact. New model or data-transfer permission is a separate decision.

The two entry points are a new project created in native KiCad and a continued
saved or open design. Keep their steps and remaining checks current in the
[design journeys](design-lifecycle.md).

## Board workspace · November 23

Make the saved-project companion feel like one workspace from choosing a
design through checked delivery. Keep a request, the conversation and its
board context together. Put next actions and recoverable refusals where the
user is working, with implementation details available on demand. Retain the
guarded 10.0.8 live operation while the public KiCad interface limits docking
and schematic editing. The [workspace decision](board-workspace-decision.md)
specifies the installed checks and records the named Finder result. The tested
build opens Request beside a closed saved board and keeps the adopted settings
visible through checked delivery. Improve the keyboard path and the next
action after recovery before expanding the separate live-editor scope.

| Existing part | Reuse decision and evidence boundary |
|---|---|
| Freerouting | Keep as primary search/routing dependency. It handles DSN routing and SES output; our imported result still needs actual KiCad/original-design validation. Reuse useful upstream integrations where their interfaces and licenses fit. |
| Corrected adapter (B1) | Keep demonstrated fidelity protections: original syntax/rules, generated copper transport, graphics obstacles, class/floor checks and Native refill/connectivity. Plane suppression is an optional-transformation concern requiring bounded evidence before changing it; the failed plane experiment stays failed. |
| Tuned/restart search (B2) | Shared reusable configuration, not a proprietary rival. Finish the current fixed tuned/low-via-cost optional mode through bounded source and Native qualification. Search cost never authorizes changed dimensions or protection. Default stays corrected-standard until a prospective task-based decision. |
| Experimental pruning/repair | Keep outside the normal completion path. Pruning can shorten admissible ground copper on exposed cases but needs a completed incumbent and has no broad completion gain. Protected-gap default/Improve lost a case that restartB2 completed. Both recent plane and empty-net pilots failed; do not retry them for a favorable result. |
| Validation/protection/process core | Retain mandatory current candidate/report/source binding, complete project/rules, protected copper, actual Native checks, bounded execution, cancellation and stale refusal. Share existing helpers; avoid another orchestration/archival framework. |
| GUI/CLI/structured interface | Keep the separate-project workflow and develop the live PCB companion alongside it. Task intent, changes and findings come first. Scope active-state synchronization, apply, Undo, overlays and docking to observed capabilities. |

The bounded source review chooses **composition around the existing guarded core**, plus an isolated reusable placement proposer. It does not adopt another whole application:

| Inspected upstream | Decision |
|---|---|
| [Freerouting](https://github.com/freerouting/freerouting/tree/ceb56c6f17db1dc587dca1de11827a9b88267db6) — active, GPLv3 | Keep our qualified pinned CLI/DSN/SES binary. Upstream already has real KiCad SWIG/IPC and Java MCP/REST interfaces; a future adapter can reuse them after qualification. Its Node MCP proxy defaults to a public API and direct supplied-path I/O, so it is not our private local tool boundary. No engine upgrade merely to match current master. |
| [KiCad-Autoplace](https://github.com/DTU-EKB/KiCad-Autoplace/tree/12bb5556fc5c1db287285425aea49a1d79dc8ffa) — MIT, last source August14 | Select its separable Python search/Board model for a bounded placement-proposal spike, not its native writer/CLI. Source inspection found project-rule and zone changes; a small pure test reproduced pad-name loss in serialization and an out-of-board placement with zero pair overlaps. Our UUID/terminal/geometry/constraint validator must remain authoritative. Preserve the MIT notice for copied modules. |
| [biosshot/kicad-copilot](https://github.com/biosshot/kicad-copilot/tree/505081d6a264bc4bdc4fac11364699d90b079a57) — MIT, last source August23 | Do not import its Node/Electron/Python stack to obtain intent translation. Its inspected layout path sends PCB data to a remote service and immediately applies responses; routing can write despite failed native verification. Reuse schema/checkpoint ideas, not its editing authority. These are source findings, not reproduced Native failures. |
| [Open Konnect](https://github.com/mixelpixx/Konnect/tree/676efce43c9779f9f9e59a9181cb0746c6452650) — archived, AGPL-3.0-only | Use revision-bound plans, narrow tools and IPC readback/rollback as design references. Its broad Rust/NNG server and post-apply DRC do not replace our acceptance boundary. Bulk automatic placement is explicitly blocked in inspected code. Copying AGPL modules would require separate compatibility/distribution review; none are imported. The closed Konnect-EDA successor is excluded. |

Only Autoplace's tiny geometry/serialization behavior was executed (0.017 seconds, no KiCad/model/build); other upstream behavior is static inspection. None is qualified as our supported integration. Dependency/maintenance and exact source records are retained locally and summarized in [source ledger](../SOURCE_LEDGER.md). The concrete immediate implementation is a small typed inspection/proposal layer and replaceable bounded model client over existing CLI/GUI functions, not another agent framework. Models receive compact consented summaries and may propose routing or scoped selected-placement/routing intent; run/accept/reject/warning decisions remain explicit ordinary controls.

The first delivery milestone is one real saved-project inspection → visible proposed settings → explicit run approval → guarded routing → readable preview/findings → explicit acceptance/rejection → freshly validated separate export. The same steps must work without AI. A model may propose only; it cannot approve, execute arbitrary commands or silently acknowledge changed warnings. If no authorized endpoint exists, deterministic integration can pass while live copilot remains an explicit access gate. No paid calls or large model download.

Next, selected/group placement becomes a first-class workflow: inspect connectivity and geometry; distinguish hard fixed/region/orientation/side/edge/keepout/existing-track constraints from preferences; generate a bounded set of alternatives; allow visual edits and explicit approval; route a bounded shortlist. Use deterministic validation and specialized search for geometry; AI only for ambiguous intent, planning and context-grounded suggestions. No inference of electrical intent from net names.

Success is scoped task completion, preserved intent, clear changes/findings, few user actions and measured manual repair when real reviewers exist, installation, predictable complete runtime/model cost and recoverable failures. Compare official upstream workflows prospectively; the historical guarded B0 is not the untouched official plugin. Preserve exposed development/untouched confirmation separation. Windows Native installation/routing/validation/cancellation/export, independent install/recovery and human/physical claims remain separate gates.

Retain compact incremental evidence and one owned temporary verification workspace. No old cleanup/restoration restart, mass relocation, new framework, model training or formal publication. Runtime074/GUI105 and its large-board delivery retain their exact qualified scope; [077 installed placement/routing](../evidence/runtime077-installed-placement-001.json) and [GUI108](../evidence/gui-runtime077-108-placement-001.json) now qualify a narrow owned ordinary-SMD task. They do not establish broad placement usefulness, live model access or Windows Native support.
