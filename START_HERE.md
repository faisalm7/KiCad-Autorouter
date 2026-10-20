# Use runtime056 on this Mac

The current immutable experimental runtime is **056**, source `a03b5e8b6ae523d9f099cf211815900053629fe3`, manifest `b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded`. Its [eleven Native CLI workflows completed](evidence/runtime056-native-milestone-001.json). [GUI089 is prepared only](evidence/gui-runtime056-089-preparation-001.json), and the latest tool check reports Mac locked. The workflow below is implemented but still needs current graphical qualification. This is not a finished or release-qualified product.

1. **Start the existing isolated launcher.** Save work and close conflicting KiCad managers/editors first. To use Edge without changing Chrome or the default browser, run this in Terminal:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime/.runs/gui-launcher089/Launch Autorouter.command'
   ```

   The override belongs only to that child session. Alternatively, double-click the same launcher in Finder and open generated `review/preview.html` manually through **Microsoft Edge → File → Open File…**. Do not change the system browser. The existing launcher is path-bound; do not move or edit it.

2. **Choose a saved complete project.** Open the project in that KiCad manager, open PCB Editor and click the green autorouter toolbar icon. In the routing window, select the exact saved PCB and a separate output folder. Keep matching PRO/SCH/rule files together. Save and close source PCB/schematic editors before acknowledging their paths; the tool cannot inspect unsaved buffers.

3. **Begin with Route / Finish gaps / 90 seconds.** Keep corrected-standard/B1, both corrections, all source layers and default via cost. Finish gaps protects every existing route; whole-board routing removes only unlocked routing and preserves locked copper. **Preview** checks static support, then **Route** performs the work. Unsupported inputs/settings refuse. **Cancel** retains evidence and cannot authorize a positive outcome.

4. **Review, then choose.** Use **Create review**, inspect front/back and every relevant layer in Edge, and read all findings, warnings and ignored checks. If using **Open review project**, close its editors and **File → Close Project** before acknowledging review. **Reject intent** prevents export. **Accept intent** records a software choice, not independent PCB approval.

5. **Validate a separate export.** **Fresh export** runs new original-rule Native checks into another project. **Open checked export** checks current proof before opening it in KiCad. The original is not overwritten; live apply/undo is not offered. Opening an export can change PRO/PRL/backups and stale its proof even if the PCB is unchanged. A refusal does not repair or renew that evidence.

The owned starting source is runtime056’s `.runs/gui-session089/project/owned1007-transport.kicad_pcb`, with `.runs/gui-session089/route-settings.json`. Preserve its original bytes and use fresh output names. [Detailed GUI steps](docs/gui-workflow.md) explain customization and the narrower optional methods; [CLI instructions](docs/quickstart.md) always enter the runtime directory before `-m autorouter`.

Historical050 evidence includes [actual active-Java cancellation](evidence/gui-runtime050-086-active-engine-cancel-001.json), source/settings/stale-export refusals and checked ordinary/Improve opening. The [single menu-timing attempt missed its interval](evidence/gui-runtime050-086-queued-miss-001.json); it is not queued-callback proof. The separate [escape-seed probe was negative and deferred](evidence/qfn-escape-development-probe-002.json); it is not a runtime056 feature or routing gain.

Normal routing needs no AI account or internet. Existing pinned KiCad10.0.7, Java and Python paths on this same Mac remain required. No standalone, clean-OS, Windows, full-GUI, broad routing-quality, human or electrical qualification is claimed. [Current status](STATUS.md) · [Support limits](docs/experimental-rc.md) · [Fresh-folder installation](docs/install-existing.md). [Previous guide preserved unchanged](docs/history/2026-10-20-pre-runtime050-user-guides/START_HERE.md).

Optional Improve remains experimental. [Fresh056 exposed IR delivery](evidence/runtime056-ir-delivery-002.json) passes after the general review-scaling repair, but it does not repair or replace the failed [frozen050 comparison](docs/benchmark-runtime050-default-improve.md). A fresh current comparison remains required. Keep corrected-standard Route as the default.
