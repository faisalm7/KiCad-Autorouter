# Use the local autorouter

Keep this existing folder at `~/Projects/KiCad-Autorouter-local`. Do not reclone or replace its environment. Ordinary routing runs locally without Codex, an AI subscription or internet.

The current installed CLI candidate is **runtime019**, source `321bc5bfdcb85c6975ee5b7e2accf09b6f43da84`. [Native qualification](evidence/runtime019-production-CLI-delivery-001.json) covers protected four-layer routing, review and fresh separate-project export. Its [GUI launcher](evidence/gui-runtime019-067-prepared-001.json) is prepared; current GUI interaction still needs qualification. The latest actual graphical evidence remains [014/064](evidence/gui-runtime014-064-native-opening-001.json). [Limits](docs/install-test.md).

On this Mac, the prepared launcher is:

`.runs/runtime-directory-019/runtime/.runs/gui-launcher067/Launch Autorouter.command`

Close other KiCad applications, then double-click that file. It starts KiCad with isolated local settings, plugin and cache. Open your saved project in that manager, open PCB Editor and click the green autorouter icon. Save and close the source PCB/schematic editors before confirming their exact paths in the separate routing window. [Step-by-step workflow](docs/gui-workflow.md).

Choose scope/protection, supported layers, preferences and budget. Preview support, start routing and use Cancel when needed. Review before/after copper and all findings, close the review project, then record explicit accept or reject intent. Fresh export validates another separate project; opening/editing it may stale its proof. Acceptance intent is not PCB certification. There is no live overwrite or tested undo.

For the CLI, open Terminal in this checkout:

```sh
cd ~/Projects/KiCad-Autorouter-local
.venv/bin/python -B -m autorouter doctor
```

The [public LED demo](docs/quickstart.md) provides concrete commands. Only its explicit download needs internet; private boards are not uploaded. [Saved preferences](docs/routing-preferences.md) persist scope, new layers, budgets and optimization choices. Finish gaps protects all existing copper; locked copper is always protected. Unsupported combinations refuse with a reason.

This is experimental software. Routing-scope acceptance, whole-project cleanliness and human/electrical/manufacturing approval are separate. General completion/cleanup improvement beyond a strong Freerouting baseline remains unproved. [Status](STATUS.md), [requirements](REQUIREMENTS.md) and the [candidate matrix](docs/experimental-rc.md) retain all unmet gates. No formal release/package is published. Source/essential owned proof have verified GitHub checkpoints; raw archives remain on this Mac by your choice.
