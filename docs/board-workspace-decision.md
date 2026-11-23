# Copperpath board workspace

## Decision · November 23, 2026

Make the saved-board journey easier to follow from opening through checked delivery. Keep project identity, the board, a request and its review together. Use a distinct Copperpath application identity for the ordinary Finder entry if the pinned wx runtime can run inside a small native host. The optional live companion will continue to use KiCad’s public add-on interfaces and its qualified single-footprint scope.

## Observed baseline

The public checkpoint is `998ad74c8`. The installed Finder and checked companion payload is `060c3c497` with manifest `8091fc0ceea45ee0dab8f4cdc606929fb81c1870e2b99a2913d8d90bb988c1f6`. The tested host is an eight-core Apple silicon Mac with 16 GiB RAM and macOS 27.0.1. Saved delivery uses pinned KiCad 10.0.7, Python 3.9.13/wx and Freerouting 2.5.0. The isolated 10.0.8 editor supplies the checked live move. [Installed qualification](../evidence/product-integrated-rc-editor-001.json)

The installed welcome view spends most of the window on a blank canvas. An absolute path competes with the design name and actions afterward. Conversation and request controls occupy separate areas, so the operator has to choose Request before entering a placement request. The review keeps the conversation beside the copper, though its colored legend is hard to read on the dark host. The operating system identifies the GUI process as Python because the Finder wrapper opens KiCad’s bundled Python application. Earlier tests selected the wrong Python window when the active fixture had the same platform identity. The separate live and saved frames have verified handoff and draft retention. [Handoff and layout evidence](../evidence/product-integrated-rc-handoff-001.json)

The MIT PushButtonLed walkthrough took 23 operator-equivalent actions, including three deliberate edit checks. Delivery was observed by 256.421 seconds and verified by 267.465 seconds, including observer pauses. It moved R1 and R2, routed three approved nets and kept 13 protected tracks, seven inherited warnings and the original files. It needed zero manual CAD edits. The known STM32 refusal combines a footprint rule area, eight USB net conflicts and a PCB/schematic field mismatch. Page design cannot admit that task safely. [Licensed walkthrough](../evidence/product-integrated-rc-pushbutton-001.json) · [STM32 findings](../evidence/product-distinct-licensed-route-intake-001.json)

## What informs the design

- **Flux** documents a request beside its own web editor, selection-aware assistance, findings focused on the affected geometry and distinct Undo and version-restore actions. Bring the selected components and explicit proposal review beside Copperpath’s board. Flux owns its editor and document state. These are documented vendor workflows, reviewed November 23, with no independent service run. [PCB editor](https://docs.flux.ai/reference/reference-pcb-editor) · [Routing](https://docs.flux.ai/reference/route-with-flux) · [Review](https://docs.flux.ai/tutorials/pcb-design-review) · [History](https://docs.flux.ai/flux/Introduction/reference-version-control)
- **Quilter** documents candidates with completion, constraint checks and separate export choices. That supports an actionable review which keeps warnings visible alongside changed copper. Its bypass checks include geometric measures such as pin distances, route length and layer changes. Its impedance workflow requires a selected net, frequency, target impedance, material stackup and reference plane. A vendor test measured EMI on selected fabricated samples after engineering cleanup. It does not establish electrical correctness of arbitrary automated results. A future task could check an explicitly declared bypass pin pair and threshold against Native evidence. Model or simulation work offers little value for the current workflow gap. [Candidate review](https://docs.quilter.ai/using-quilter/review-layout-candidates) · [Bypass checks](https://docs.quilter.ai/physics-constraints/bypass-capacitors) · [Impedance checks](https://docs.quilter.ai/physics-constraints/single-ended-impedance-control) · [EMI measurements](https://www.quilter.ai/blog/ai-designed-pcb-emi-test-ken-wyatt)
- **KiCanvas** has MIT-licensed viewer source. Its documented experimental embedding API lacks implemented selection events, and its roadmap excludes editing and visual diffs. Adopting it would add a web host and a second rendering and parsing surface. Retain the existing trusted board and review data and native controls. Reconsider a viewer when there is a measured rendering or interaction bottleneck. [Embedding](https://kicanvas.org/embedding/#events) · [Roadmap](https://kicanvas.org/roadmap/) · [Inspected source](https://github.com/theacodes/kicanvas/commit/b031159eb74aaa7eef2b026fd85d35bc05ff2095) · [Notices](https://kicanvas.org/license/)
- **KiCad 10** launches stand-alone add-on actions. Its own panes live inside the editor. PCB IPC offers document identity, synchronous selection and native transactions. Commit requests lack a board revision precondition. Keep exact source, editor snapshot, selection and readback checks. A real dock requires an upstream interface or a maintained fork, with distribution and upgrade costs. The 10.0.8 schematic handler supplies limited document identity. Official documentation places schematic add-on actions, headless IPC and IPC export in 11. Treat these as future qualification targets. [Official version boundaries](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/#api-status-and-goals) · [Pinned pane implementation](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/pcbnew/pcb_edit_frame.cpp#L283) · [Transactions](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/common/api/api_handler_editor.cpp#L62) · [Schematic handler](https://gitlab.com/kicad/code/kicad/-/blob/10.0.8/eeschema/api/api_handler_sch.cpp#L34)

## Implementation boundary

Retain wx, the existing canvas, local request parser and all engineering operations. Use a quiet welcome view with three clear entry actions. Keep a compact project header and one board-first layout. Place the request composer next to the conversation by default after inspection. Keep editing, findings and schematic context within reach. Make readiness, read-only restrictions and recovery explicit. Keep technical paths and settings available on demand. Use short labels, system typography, distinct status text and readable copper changes on light and dark system themes.

Test one small Mach-O prototype against the bundled 3.9 framework. A script wrapper and wx naming can improve window labels. macOS application identity requires measuring the process’s actual bundle name and menu. Embedding can provide a named foreground app while retaining the launcher checks. It costs a small macOS-specific source file and a compile step during setup. Use the existing local compiler and unchanged signed KiCad. The diagnostic launcher remains available. Record a failed experiment and keep the identity limitation visible if the local prototype or guarded install cannot support this path. [Apple application naming](https://developer.apple.com/library/archive/qa/qa1544/_index.html) · [Python embedding](https://docs.python.org/3.9/c-api/init_config.html)

## Prospective installed acceptance

1. Open through the verified Finder artifact. Check the blank, loading, ready, proposal, busy, review and delivered views at 880 × 610 and a larger size. Inspect actual renders, readable contrast, Tab focus and a keyboard action. Verify which process owns the window and measure the application name and identifier separately from its title. Preserve earlier exact native Undo readback on the unchanged checked live path. Native Undo restores the recorded editor state. Opening or delivering a checked copy does not change KiCad’s Undo history.
2. Use the exact previously admitted MIT PushButtonLed task at the frozen source and constraints. Approve only the two selected moves, the established allowed affected copper and the three listed nets at 90 seconds. Inspect the changed constraints and copper before approval. Deliver a fresh checked separate copy with independent readback and the same protected records, original files, findings and support decisions as required by the frozen task. Retain actual outcomes. Remove at least the Request-tab detour from the ordinary path. Keep deliberate approval, warning review and fresh validation.
3. Use a separate complete copy of the owned example. Exercise a stale settings proposal by changing only the disposable project after preview. The old proposal must refuse without dispatch. Refresh the saved capture, re-preview and adopt only fresh settings. Test the visible project-lock or unsupported-input refusal. Verify the original three design files and marker/recovery handling. Test cancellation or retain working cancellation evidence for unaffected execution and scope the changed UI controls explicitly.
4. Record the actual interaction count, visible waits, responsiveness and RSS with the same installed observer and normal resource checks. Distinguish engineering wall/CPU time from operator and automation pauses. Report CAD corrections actually made and compare the scoped outcome, including all findings. Use new local artifacts with no hosted requests, new purchases or altered original design requirements.

## Installed result

The fresh `ccd7a4073` build ran on macOS 27.0.1 arm64 with pinned KiCad
10.0.7 and Freerouting 2.5.0. The corrected probe opened with its own name,
then the installed Finder app registered as **Copperpath** with identifier
`org.copperpath.workspace`. Actual renders cover the welcome and loading
views at both sizes, saved and proposal views, active review preparation,
review before acceptance at 1040 × 720 and the delivered findings at both
sizes. At 880 × 610, long findings wrap into a scrollable area. **Use
settings**, **Discard** and **Open checked export** were visible in their
respective views. Editing a suggestion can require scrolling at that size.
[Installed evidence](../evidence/product-board-workspace-001.json)

The frozen MIT task made R1 and R2 eligible within the approved region. The
selected alternative moved R2 and left R1 and the other five footprints in
place. One attempt with a 90-second limit closed the three approved nets. All 13
protected tracks, the original project files and the ground-zone intent
stayed exact. Fresh KiCad validation and independent readback reported zero
opens, zero blocking findings, seven inherited footprint-library warnings
and five ignored checks. The operator made zero manual CAD corrections.

Both walkthroughs recorded 23 operator-equivalent actions. Direct Request
entry removed the tab switch, and one automated keyboard re-entry used the
saved action. Delivery and independent verification were observed by 330.4
and 347.9 seconds, compared with 256.4 and 267.5 seconds in the reference.
These upper bounds include admission sampling and observer pauses. The
current routing worker took 13.09 seconds wall and 11.03 CPU seconds. App
RSS was about 268 MiB at the proposal and 85 MiB at delivery. Those are
samples at the named views.

The disposable test refused a stale proposal, adopted a fresh one after
refresh and showed the last saved board under a project lock. Removing the
test marker restored the workspace with Findings selected. Choosing Request
restored the composer. Active inspection cancellation discarded the result
and a fresh inspection recovered. Command+O and Command+L worked. Tab
moved focus from the request field to the window in the Accessibility
readback. A predictable path between visible controls remains the next
keyboard priority.

Delivery here creates a separate checked project. The earlier native Undo
test applies to one checked move in the pinned KiCad 10.0.8 companion.
Native docking, schematic writes, independent installation and physical
validation retain their own qualification gates.
[Native Undo evidence](../evidence/product-integrated-rc-editor-001.json)
