# Use experimental runtime073 on this Mac

**Headless native qualification passed; actual GUI104 qualification is pending.** This is an experimental development candidate. [Evidence](evidence/runtime073-installed-native-milestone-001.json) · [Current gates](STATUS.md) · [CLI instructions](docs/quickstart.md).

The installation is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime073 fresh install 001'`. Source: `346b241e38e172d7a1478f7eeb535288e496d999`; manifest: `d12be29349b01dcd9693f4fbb8e6f00faaa285e15bb5a8f0bed84857350aa6b5`. It uses isolated KiCad 10.0.7 and existing local dependencies, with no AI account or normal routing network requirement. Same-Mac/account checks are not independent installation.

GUI104 has fresh owned sources, settings and an isolated launcher. These are prepared test inputs; their existence is not a GUI pass. Keep the routing lane idle, use fresh job outputs and preserve completed evidence.

1. Save work and close other KiCad managers/editors normally. Launch the prepared isolated manager with its child-only Edge setting:

   ```sh
   '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime073 fresh install 001/.runs/gui-session104/Launch Autorouter GUI104 Edge.command'
   ```

2. In that manager open `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime073 fresh install 001/.runs/gui-session104/inspection/owned-four-copper-forced-inner.kicad_pro'`, open PCB Editor and click the green bent-trace autorouter icon beside `>_`. The ordinary source is `ordinary-project/owned1007-transport.kicad_pcb` under the same GUI session; load its paired `ordinary-settings.json`. Four-layer and class roles have separate source folders and presets. Keep each pair together. Save and close source editors before acknowledging exact paths in the routing window.
3. Choose scope, copper protection, supported layers, preferences and budget. Preview support, start routing, read progress or cancel. Finish gaps protects every existing route; whole routing preserves locked copper. Unsupported combinations refuse. The older ordinary example cannot qualify the new narrow selected-net policy.
4. Create review and inspect every layer, finding, warning and ignored check in **Microsoft Edge**. Close review editors and use File → Close Project before acknowledging review. Accept records intent; Reject disables export. Neither certifies the board.
5. Fresh export performs new original-rule native checks into a separate project. Open checked export rechecks freshness. Editor metadata can stale proof even with unchanged PCB bytes. Originals are never overwritten; live application/undo is unavailable.

Routing, review and export have separate ceilings; comparisons must count all of them. Use fresh output names rather than repeating completed qualification. [Settings](docs/routing-preferences.md) · [Installation](docs/install-existing.md) · [Graphical limits](docs/gui-workflow.md).

Broader completion beyond strong corrected/tuned Freerouting, Windows native support, independent installation/full current recovery, human review and physical/electrical validation remain open. Backups are Mac-only. No formal release has been published.
