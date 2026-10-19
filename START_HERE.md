# Use the local autorouter

The current **runtime039 / GUI079 experimental launcher** below has passed [Native/CLI qualification](evidence/runtime039-native-floor-schema-milestone-001.json). Its actual GUI has launched from KiCad, loaded the90-second Finish gaps preset, refused an invalid budget before creating a job, completed protected routing, shown inspected front/back review images in Edge, recorded explicit accept intent and freshly validated an export. Checked opening rendered that exported PCB in KiCad with0 unrouted and then closed it without requesting edits or a save. The fresh89-file preopen snapshot is preserved. After opening, KiCad changed export PRO/PRL and added a backup ZIP; current proof correctly refuses as stale, while PCB/source remain unchanged. Reject/cancel/freshness/recovery controls remain unfinished. This is a test build, not a dependable-production claim.

039 includes the general Default/floor input correction. Older037 and failed038 remain preserved as historical evidence. General completion and engineering-cleanup improvement beyond a competent Freerouting baseline is still unproved.

Keep this folder at `~/Projects/KiCad-Autorouter-local`. The launcher uses the existing pinned KiCad 10.0.7, Java and local Python environment at their fixed paths. Leave those paths intact. Routing runs locally without Codex, an AI subscription or internet once these dependencies are present.

On this Mac, open this existing file:

```text
~/Projects/KiCad-Autorouter-local/.runs/runtime-directory-039/runtime/.runs/gui-launcher079/Launch Autorouter.command
```

Close other KiCad applications, then double-click the launcher. It starts KiCad with isolated local settings, plugin and cache. Open a saved test project or a copy of your project in that manager, open PCB Editor and click the green autorouter icon. Save and close the source PCB/schematic editors before confirming their exact paths in the separate routing window. [Step-by-step workflow](docs/gui-workflow.md).

Start with the **90-second Finish gaps preset** used by the recorded GUI positive. Preview support before routing. Finish gaps protects existing copper; locked copper is always protected. Unsupported settings refuse with a reason. Other controls, including current-build cancellation and freshness cases, still need qualification.

Review before/after copper and every finding in the local review window, then record explicit accept or reject intent. The current recorded review used an owned Edge tab so the owner's active Chrome session stayed separate; that tab is now closed. Fresh export validates a separate candidate project. Opening or editing that export can change its project settings and make the proof stale; changed material needs fresh validation. The saved source stays separate. Acceptance intent is not human PCB approval, and there is no live overwrite or tested undo.

Runtime039 passed full integration, fresh installation, five native deliveries and real invalid controls. GUI079 fresh export has0opens/0blocking/0warnings/0exclusions and preserves all4 protected records; its [preopen check and copy](.runs/gui079-positive-preopen-001.log) passed on89 files. The checked export opened and rendered in KiCad, showing6 pads,1 via,6 segments,3 nets and0 unrouted, then closed without a requested edit/save. The post-open proof correctly refuses “export inputs/runtime/evidence changed” after export PRO/PRL/backup ZIP changes; PCB/source bytes remain unchanged. The remaining controls still need qualification; no access request is pending. The single bounded Mixer follow-up finished without an accepted route: it removed the prior width/clearance errors but retained160 opens and1 thermal error. Additional Mixer tuning is deferred. [Current limits and evidence](docs/experimental-rc.md).

Routing-scope acceptance, whole-project DRC cleanliness and human/electrical/manufacturing approval are separate. [Saved preferences](docs/routing-preferences.md), [status](STATUS.md), [requirements](REQUIREMENTS.md) and the [candidate matrix](docs/experimental-rc.md) retain their scopes and unmet gates. No formal release or package is published.

Source and essential owned proof have verified GitHub checkpoints. Full newer raw evidence remains on this Mac. The last recorded free space was13,594,936 KiB (about13.92 GB), below the18.64 GB restoration lower bound, which excludes newer raw work; a new full restore remains blocked.
