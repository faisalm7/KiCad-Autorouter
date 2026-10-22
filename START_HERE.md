# Use runtime058 on this Mac

**Experimental safety hold:** runtime058 accepts some archived provisional receipts and can fail Improve's reserved return. Use only the named canonical job receipts; do not promote archives or rely on a timeout fallback. The [source fix](evidence/routing-receipt-identity-repair-001.json) is tested narrowly but is not a newly qualified runtime. [Status and next repair](STATUS.md).

Current source `8f5e96b88dd22cd25919bb71ce47711612994efa`, original manifest `4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74`. [Native058](evidence/runtime058-native-milestone-001.json), [ordinary GUI092](evidence/gui-runtime058-092-ordinary-001.json), [closed core-role observations](evidence/gui-runtime058-092-observations-001.json), [fresh-root CLI](evidence/runtime058-install-existing-001.json) and [installed GUI093](evidence/gui-runtime058-install093-observations-002.json) establish their recorded scopes. FullGUI, exact queued timing, independent installation, broad quality and human/electrical qualification remain incomplete.

1. **Start the existing isolated launcher.** Save work and close conflicting KiCad managers/editors. Use a child-only Edge override:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime058 fresh install 001/.runs/gui-launcher093/Launch Autorouter.command'
   ```

   Alternatively, double-click that same launcher in Finder and open generated `review/preview.html` through **Microsoft Edge → File → Open File…**. Leave Chrome/default-browser settings unchanged. The launcher is bound to the fresh runtime; do not move or edit it.

2. **Choose a saved complete project.** Open the project in that manager, open PCB Editor and click the green autorouter toolbar icon. Select the exact PCB and separate output folder. Keep matching PRO/SCH/rule files together. Save and close source editors before acknowledging paths; unsaved buffers cannot be inspected.

3. **Begin with Route / Finish gaps /90seconds.** Keep corrected-standard/B1, both corrections, all source layers and default via cost. Finish gaps preserves every existing route; whole-board routing preserves locked copper. Preview checks static support; Route performs the work. Unsupported inputs/settings refuse. Cancel retains unaccepted evidence.

4. **Review, then choose.** Use Create review and inspect front/back, all relevant layers, findings, warnings and ignored checks in Edge. If using Open review project, close its editors and **File → Close Project** before acknowledging review. Reject intent prevents export; Accept intent is a software choice, not PCB approval.

5. **Validate a separate export.** Fresh export runs new original-rule Native checks into another project. Open checked export checks current proof before opening it. The original is never overwritten. Editor changes to PRO/PRL/backups can stale proof even when PCB bytes remain unchanged; a refusal does not renew it.

The verified starting source is `/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime058 fresh install 001/.runs/gui-session093/project/owned1007-transport.kicad_pcb`, with `route-settings.json` beside the session's `project/` directory. Preserve those files and use fresh outputs. The fresh-root manifest is `19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2`. [Detailed GUI](docs/gui-workflow.md) · [CLI](docs/quickstart.md) · [Preferences](docs/routing-preferences.md).

GUI092 records an actual active-engine Cancel with engine−9/cleanup/CLI2/unaccepted/no downstream; a first small-job Cancel interrupted incumbent validation after Java finished. These do not prove graceful cancellation, every phase, algorithm entry or permanent descendant absence. Exact queued-callback timing remains unproved; the aborted STOP method stays stopped without retry. Thermal Recover is not a current GUI qualification.

Optional Improve remains experimental and narrower than Route. [IR058](evidence/runtime058-ir-delivery-001.json) and [EEPROM058](evidence/runtime058-eeprom-improve-regression-001.json) are successful exposed single regressions. The [historical057 comparison](docs/benchmark-runtime057-default-improve.md) shows no completion advantage overB1/B2; the [failed057 EEPROM arm](docs/benchmark-runtime057-eeprom.md) stays failed. Keep corrected-standard Route as default. No completed job needs rerunning to read stored evidence.

Existing same-Mac/account/basePython/external tool paths remain necessary. No standalone, cleanOS, Windows, fullGUI, broad routing-quality, human or electrical qualification is claimed. Restoration remains capacity-blocked. [Status](STATUS.md) · [Installation](docs/install-existing.md) · [Previous guide preserved unchanged](docs/history/2026-10-20-pre-runtime050-user-guides/START_HERE.md).
