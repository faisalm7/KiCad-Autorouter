# Design journeys

Copperpath uses KiCad for project and library editing. Placement, routing and
review share the checked engineering path. Ordinary controls work without
inference. The saved-project workspace stays available beside the live PCB
companion. [Product strategy](product-strategy.md)

| Step | Current evidence | Next acceptance check |
|---|---|---|
| Start a design | The installed start action opened KiCad 10.0.7, used its built-in libraries and created the Default PCB, project and schematic. Copperpath opened those files and showed setup guidance. [Installed check](../evidence/product-native-new-design-002.json) | Use that exact project for the stock-library circuit and PCB preparation. |
| Prepare the schematic | Saved schematic context is read-only. Symbols, wiring, footprint assignments and ERC are native KiCad operations. | Use installed libraries and bring annotated footprints into the PCB with **Update PCB from Schematic**. |
| Place parts | The installed workspace can place selected parts subject to reviewed boundaries, fixed parts and copper protection. [Scope](current-placement-scope.md) | Use a small supported PCB from the new-project journey. |
| Route | Pinned KiCad 10.0.7 and Freerouting have completed selected and protected Finish gaps tasks. The installed 8996 workspace showed actual progress and stopped an active engine. [Checks](routing-preferences.md) · [Installed controls](../evidence/product-8996-routing-controls-001.json) | Admit the circuit created through the native entry. |
| Modify | The installed workspace displays saved designs. One exact owned PCB passed a checked live move and Undo in 10.0.8. [Editor scope](live-editor-milestone.md) | Revise and approve a small move in Conversation, refuse stale state, and verify live application and Undo. |
| Review and deliver | The installed separate-project flow verified original intent, protected copper, KiCad findings and fresh export. [Checked delivery](../evidence/product-round-cutout-checked-delivery-002.json) | Keep board, findings and Conversation visible through review and recovery at laptop size. |

## Start a new design

Use **Start a new design** to hand off to the prepared KiCad Manager. When
KiCad shows first-use setup, choose the built-in KiCad libraries. If a
manager is already open, work there after saving any active design. Choose
**File → New Project…**, select **Default** and save in a new project folder.
**Continue an existing design** opens those saved files in Copperpath. A
new PCB needs footprints and a closed outline before engineering work.
In KiCad, add a small circuit using installed symbols and footprints, review
ERC, transfer the footprints to PCB Editor and draw the intended outline.
Save and close the project before separate placement or routing. The bundled
example is available as its own walkthrough. [Native project creation](https://docs.kicad.org/10.0/en/kicad/kicad.html#_creating_a_new_project) · [Schematic-to-board workflow](https://docs.kicad.org/10.0/en/getting_started_in_kicad/getting_started_in_kicad.html#_importing_changes_from_schematic)

KiCad 10 supports native schematic editing and saved schematic inspection.
Automatic schematic edits need an installed version with sheet-aware typed
commands, verified readback and Undo. KiCad 11 documents that interface. The
pinned 10.0.8 schematic handler reports incomplete project and sheet identity.
[Official IPC support](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html) · [10.0.8 handler](https://github.com/KiCad/kicad-source-mirror/blob/10.0.8/eeschema/api/api_handler_sch.cpp#L34-L79) · [KiCad 11 schematic API](https://docs.kicad.org/kicad-python/schematic.html)

## Continue an existing design

The saved picker retains board context and shows support limits. The checked
live companion uses the exact owned 10.0.8 example and its PCB toolbar.
Bind proposals to the launching editor, exact live PCB and current selection.
Read the selection again after an edit or refusal. Keep native Undo explicit
and verify the prior PCB before reporting restoration. The pinned API has
separate transaction requests without a compare-and-swap revision. Keep the
first journey to a single isolated PCB editor and one checked translation.
[Pinned transactions](https://github.com/KiCad/kicad-source-mirror/blob/10.0.8/common/api/api_handler_editor.cpp#L42-L155)

## Visual checks

Keep the board dominant at 880 × 610 and above. Use native system type,
consistent margins, a clear project and selection label, and one primary
action for the current stage. Highlight the selected part and proposed
position. Keep advanced settings under a disclosure. Verify loading,
clarification, refusal, cancellation and recovery on installed screens.
Record operator-equivalent actions and waiting separately from automation
gaps. The receiver view showed the board and its exact limit together. Its
long path clipped the project name in the header.

## Dependency decision

Keep wx, the isolated placement search and Freerouting. KiCanvas is an MIT
browser viewer with an alpha embed API. Its roadmap leaves editing and visual
diffs out, and its host selection events are unimplemented. A second parser
and WebGL surface would need KiCad-version and memory checks. Its latest
checked commit was April 2026. [Embed API](https://kicanvas.org/embedding/#events) · [Roadmap](https://kicanvas.org/roadmap/) · [License](https://github.com/theacodes/kicanvas/blob/main/LICENSE.md) · [Revision](https://github.com/theacodes/kicanvas/commit/b031159eb74aaa7eef2b026fd85d35bc05ff2095)

Clipper2 is a maintained Boost-licensed integer-polygon library for a future
measured containment or offset bottleneck. KiCad 10.0.8 vendors it without a
shared binding. Copperpath would need a binding and verified conservative
curve approximation. The retained NUS trial also hit protected copper and
other scope limits. Both dependencies have unmeasured memory costs here.
This milestone adds zero dependencies. [Geometry interface](https://angusj.com/clipper2/Docs/Overview.htm) · [Pinned KiCad build](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.8/thirdparty/CMakeLists.txt#L22-L39) · [Maintained revision](https://github.com/PolyClipping/Clipper2/commit/884ba821abc002d895ce72dcc21fe139c207229f) · [License](https://github.com/PolyClipping/Clipper2/blob/main/LICENSE)
