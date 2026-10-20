# Use runtime050 on this Mac

The current immutable experimental runtime is **050**, source `aa0072c6b3d8090de2603e5ecb42a95968fb873b`, manifest `c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8`. Its [seven Native CLI workflows completed](evidence/runtime050-native-milestone-002.json). [GUI086 qualification is partial](evidence/gui-runtime050-086-progress-001.json); this is not a finished or release-qualified product.

1. **Start the existing isolated launcher.** Save work and close conflicting KiCad managers/editors first. To use Edge without changing Chrome or the default browser, run this in Terminal:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-050/runtime/.runs/gui-launcher086/Launch Autorouter.command'
   ```

   The override belongs only to that child session. Alternatively, double-click the same launcher in Finder and open generated `review/preview.html` manually through **Microsoft Edge → File → Open File…**. Do not change the system browser. The existing launcher is path-bound; do not move or edit it.

2. **Choose a saved complete project.** Open the project in that KiCad manager, open PCB Editor and click the green autorouter toolbar icon. In the routing window, select the exact saved PCB and a separate output folder. Keep matching PRO/SCH/rule files together. Save and close source PCB/schematic editors before acknowledging their paths; the tool cannot inspect unsaved buffers.

3. **Begin with Route / Finish gaps / 90 seconds.** Keep corrected-standard/B1, both corrections, all source layers and default via cost. Finish gaps protects every existing route; whole-board routing removes only unlocked routing and preserves locked copper. **Preview** checks static support, then **Route** performs the work. Unsupported inputs/settings refuse. **Cancel** retains evidence and cannot authorize a positive outcome.

4. **Review, then choose.** Use **Create review**, inspect front/back and every relevant layer in Edge, and read all findings, warnings and ignored checks. If using **Open review project**, close its editors and **File → Close Project** before acknowledging review. **Reject intent** prevents export. **Accept intent** records a software choice, not independent PCB approval.

5. **Validate a separate export.** **Fresh export** runs new original-rule Native checks into another project. **Open checked export** checks current proof before opening it in KiCad. The original is not overwritten; live apply/undo is not offered. Opening an export can change PRO/PRL/backups and stale its proof even if the PCB is unchanged. A refusal does not repair or renew that evidence.

The owned starting source is runtime050’s `.runs/gui-session086/project/owned1007-transport.kicad_pcb`, with `.runs/gui-session086/route-settings.json`. Preserve its original bytes and use fresh output names. [Detailed GUI steps](docs/gui-workflow.md) explain customization and the narrower optional methods; [CLI instructions](docs/quickstart.md) always enter the runtime directory before `-m autorouter`.

Current evidence includes [actual active-Java cancellation](evidence/gui-runtime050-086-active-engine-cancel-001.json), source/settings/stale-export refusals and checked ordinary/Improve opening. The [single menu-timing attempt missed its interval](evidence/gui-runtime050-086-queued-miss-001.json); it is not queued-callback proof. The separate [escape-seed probe was negative and deferred](evidence/qfn-escape-development-probe-002.json); it is not a runtime050 feature or routing gain.

Normal routing needs no AI account or internet. Existing pinned KiCad10.0.7, Java and Python paths on this same Mac remain required. No standalone, clean-OS, Windows, full-GUI, broad routing-quality, human or electrical qualification is claimed. [Current status](STATUS.md) · [Support limits](docs/experimental-rc.md) · [Fresh-folder installation](docs/install-existing.md). [Previous guide preserved unchanged](docs/history/2026-10-20-pre-runtime050-user-guides/START_HERE.md).
