# Use the local autorouter

Runtime025 passes ordinary10.0.7 Native/CLI delivery, but its actual GUI071 found a budget-input defect: leaving the native spin field coerced0 or invalid text to5 before Preview. Two preview-only jobs are retained; no Route/Native/export ran. The shared GUI now uses plain text with strict whole5–900 validation in development. Targeted controls and AI source review pass; a fresh committed build and actual focus-loss/full-workflow GUI qualification remain required. Old023 GUI observations stay historical and do not clear this newly demonstrated defect. [Failure evidence](evidence/runtime025-GUI071-budget-refusal-failure-001.json).

Keep this existing folder at `~/Projects/KiCad-Autorouter-local`. Do not reclone or replace its environment. Ordinary routing runs locally without Codex, an AI subscription or internet.

The historical GUI-qualified local candidate is **runtime023**, source `8c0c8468823751d9b5dc4c9a9c51b1d622269a27`, manifest `3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81`. [Whole4Cu CLI](evidence/runtime023-installed-CLI-001.json), [partial2Cu CLI](evidence/runtime023-installed-partial-CLI-001.json) and [declared GUI023/070 controls](evidence/gui-runtime023-070-native-controls-001.json) pass within their recorded scopes. Every final Route/export has its own Native/refill/full-schematic/original-design proof. Whole4Cu retains six warnings and ten protected items; the GUI2Cu partial case has0 opens/blocking/warnings/exclusions and all4 protected items. [Limits](docs/experimental-rc.md).

On this Mac, the prepared launcher is:

`.runs/runtime-directory-023/runtime/.runs/gui-launcher070/Launch Autorouter.command`

Close other KiCad applications, then double-click that file. It starts KiCad with isolated local settings, plugin and cache. Open your saved project in that manager, open PCB Editor and click the green autorouter icon. Save and close the source PCB/schematic editors before confirming their exact paths in the separate routing window. [Step-by-step workflow](docs/gui-workflow.md).

Choose scope/protection, supported layers, preferences and budget. Preview support, start routing and use Cancel when needed. Review before/after copper and all findings, close the review project, then record explicit accept or reject intent. Fresh export validates another separate project; opening/editing it may stale its proof. Acceptance intent is not PCB certification. There is no live overwrite or tested undo.

For the CLI, open Terminal in this checkout:

```sh
cd ~/Projects/KiCad-Autorouter-local
.venv/bin/python -B -m autorouter doctor
```

The [public LED demo](docs/quickstart.md) provides concrete commands. Only its explicit download needs internet; private boards are not uploaded. [Saved preferences](docs/routing-preferences.md) persist scope, new layers, budgets and optimization choices. Finish gaps protects all existing copper; locked copper is always protected. Unsupported combinations refuse with a reason.

This is experimental software. Routing-scope acceptance, whole-project cleanliness and human/electrical/manufacturing approval are separate. General completion/cleanup improvement beyond a strong Freerouting baseline remains unproved. [Status](STATUS.md), [requirements](REQUIREMENTS.md) and the [candidate matrix](docs/experimental-rc.md) retain all unmet gates. No formal release/package is published. Source/essential owned proof have verified GitHub checkpoints; raw archives remain on this Mac by your choice.
