# Copperpath inside KiCad

The current goal is a pane inside the actual PCB and schematic editors.
The existing saved-project workflow remains the separate-delivery fallback.
The previous companion qualified an owned single PCB move and exact Undo
with a separate pane window. That provides a checked engineering operation
to reuse. [Saved workflow](direct-conversation-journey.md) ·
[Pinned companion move](../evidence/live-editor-1008-direct-002.json)

## Observed starting point

The local arm64 Mac has verified standalone payloads `27086bcf7` and
`ffcfebac1`, both using KiCad 10.0.7 validation. The prior checkpoint is
`b587dbd68100e53137590765c78bd7c6c3598944`. The isolated official 10.0.8
bundle has actual PCB and schematic editors and ships wxPython 4.2.2a1
with wxWidgets 3.2.8. Its public opcode and native frame behavior are
distinct interfaces. The 10.0.8 source tag resolves to
`e432beac2668303194ba2040274f9e5efe773fc0`.

## Choose the host

| Option | Exact scope and tradeoff |
| --- | --- |
| Public IPC | On 10.0.7/10.0.8 an add-on can obtain PCB identity, selection and unsaved board content, and stage or drop a commit. The calls are separate requests. Public API plug-ins launch as separate processes. KiCad 11 development adds sheet-aware schematic snapshots, selection, netlist and item interfaces. It still launches external plugin actions. [Official add-on API](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/) · [Schematic development API](https://docs.kicad.org/kicad-python/schematic.html) |
| Stock PCB hosting probe | The bundled Python can locate the existing native wxAUI manager and attach a child pane in an isolated PCB Editor. Treat that as the question to test. The regular SWIG action dispatch snapshots board items for its own Undo and can mark a nonempty board modified. Probe attachment at load on the GUI thread, with exact editor and project guards, independent of that dispatch. Eeschema has no equivalent legacy entry. [Pinned action lifecycle](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/pcbnew/python/scripting/pcbnew_action_plugins.cpp#L279) |
| Small pinned native extension | Both editors own an AUI manager and a native GAL view. Add a shared panel and thin editor-specific selection, overlay, serialization and transaction adapters. Use a private opt-in build. The binary and configuration upgrades have to be qualified per platform. A small upstream-compatible hook is a possible later distribution path. [PCB frame](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/pcbnew/pcb_edit_frame.cpp#L283) · [Schematic frame](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/eeschema/sch_edit_frame.cpp#L229) · [GAL overlay](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/common/view/view.cpp#L1779) |

**Decision.** Use pinned native frame adapters for the product. The
existing board/rules checks stay in the bounded foreground-owned worker.
The stock PCB probe can demonstrate native pane hosting and selection
while the build is prepared. It grants neither preview nor edit authority.
Keep the patch small, with original code and attribution. A distributed
modified KiCad build would need dependency notices and corresponding source,
Mac app signing and separate Windows and Linux builds/tests. Preserve the
normal signed installation and user configuration. The binary bundle
alone supplies no matching development headers. Xcode 27 and pkg-config
are present. CMake, Ninja and the required custom wx development build
were absent from the local tool inventory. Stage dependencies under this
project and inspect upstream bootstrap commands before use.
[Official macOS build guide](https://dev-docs.kicad.org/en/build/macos/) ·
[Upstream license information](https://www.kicad.org/about/licenses/)

The two frame files retain their original KiCad contributor notices and
GPL terms when patched. The added native headers use GPL-3.0-or-later,
compatible with the PCB frame's GPL-3.0-or-later and the schematic frame's
GPL-2.0-or-later notice. [Pinned upstream source](https://github.com/KiCad/kicad-source-mirror/tree/e432beac2668303194ba2040274f9e5efe773fc0) ·
[Repository license](../LICENSE)

The development source build has its own footprint. The official mac-builder
10.0 branch was checked at `0977c0f44b2f37243c1ecd38ba0c2ae08c8300c6`. Its
ordinary build estimate is about 30 GB and several hours. A narrower local
build can skip packaging and wxPython and build ARM64 dependencies and the
two editor modules sequentially. Its peak usage remains unmeasured. Keep
the current 10 GiB cache/data limit until there is a measured plan or an
explicit exception. The signed app and normal KiCad settings do not serve
as the build prefix. Use the locally pinned toolchain and test from a
dedicated build directory. The configure probe must establish dependency
versions and missing packages before a full build is dispatched.
[Mac builder](https://gitlab.com/kicad/packaging/kicad-mac-builder/-/tree/0977c0f44b2f37243c1ecd38ba0c2ae08c8300c6) ·
[CMake release assets](https://github.com/Kitware/CMake/releases/expanded_assets/v3.31.8)

CMake 3.31.8 now runs from a verified project-local package. Its official
78,373,419-byte archive matched the publisher's SHA-256. The archive and
expanded tool together used 327,796 KiB. Dependency configuration and both
editor builds still need separate qualification.

## Interaction and authority

Flux documents real canvas selection as request context, a persistent
conversation, placement with explicit physical constraints, approval for
changes to protected copper or rules, and job interruption. Bring those
principles to the native KiCad layout with one visible selection summary,
one composer and a short checked plan. Show original and target positions,
effective movement limit and findings. Keep Stop and Discard available
while a job can be interrupted. Keep the native canvas prominent, show
actual state and progress, and use native keyboard focus and Undo. These
are documented interaction references. No Flux run or model call is part
of the scope. [Canvas](https://docs.flux.ai/reference/reference-pcb-editor) ·
[Conversation](https://docs.flux.ai/reference/copilot) ·
[Placement](https://docs.flux.ai/reference/pcb-placement) ·
[Routing and review](https://docs.flux.ai/reference/route-with-flux) ·
[Interruption](https://docs.flux.ai/reference/flux-agent)

The editor thread binds document, sheet where applicable, exact object
identity, units, live state and request generation. A worker can propose
from a detached captured snapshot and validate under the original rules.
A result is evidence for review. The editor owns approval and rechecks
exact live state in the same event as the native transaction. Keep
view-only overlays outside the board or schematic model and retire them
on changes, cancellation, failure and close. Neither stale responses nor
an exact JSON plan carry approval. Run expensive validation and future
model calls asynchronously. Known commands and selection facts use
deterministic handling. Model-based intent may eventually supply the same
typed plan with separate consent. Do not emulate interaction with desktop
automation in shipped code.

The detached checker publishes one result in the private job directory.
It binds exact request and captured PCB bytes to the validated before and
after bytes. The editor verifies those hashes before showing a proposal
and requires the same current revision at approval. Stop revokes the
proposal first. A normal close defers while the checker retires. This
boundary assumes custody of the private project and job files by the
local account. Forced process termination and the real editor rollback
remain qualification cases.

## Acceptance and continuation

The shared approval gate passed with Apple Clang. The detached checker
refused a changed selected position and an unsupported impedance request
using the retained installed runtime. Neither request started a Native
worker. Changes during a live transaction, native Undo/Redo, rendering
and editor responsiveness all need actual editor runs. The stock PCB
probe is staged in a separate private configuration. Its four resource
admission attempts recorded refusals before launch.

1. **PCB.** Use the exact owned placement fixture from the checked move.
   Select J1 in the PCB canvas. Bind and review one checked translation of
   at most 1 mm in the existing region. Show the real original item and
   proposed bounds through native view-only geometry. Approve the move
   in the pane and read the changed board without saving it. Preserve its
   unit and field metadata, nets, original rules, and protected copper.
   Plant an unrelated unsaved J2 edit before capture. Native Undo must
   recover the exact pre-move state and keep that edit. Check native Redo
   against the same applied operation.
2. **Negative controls.** Exercise changed selection, a manual edit after
   capture, Stop, cancelled delivery of a result, worker failure, project
   switch and native transaction failure. Verify no new editing history
   from attaching or previewing the pane, and no overwrite of unrelated
   work or source files. Record what actually occurred.
3. **Schematic.** On the same pinned source build, select a connected
   symbol on a disposable real sheet. Preview a small reference-field
   position change and apply it through the same open schematic editor.
   Preserve text, symbol and pin positions, identity and connectivity.
   Compare detached before/after native ERC and netlists, then verify
   native Undo/Redo with an unrelated unsaved edit. Sheet identity is part
   of the approval boundary.
4. **Evidence.** Save real editor screens for selection, view-only proposal,
   verified change and Undo. Record build identity, current host versions,
   actual step waits and measured memory, failed trials and limits. Only
   one engineering worker, within existing memory, disk and time limits.
   A pane-only or PCB-only result leaves the subsequent native gates open.
