# Use experimental runtime060 on this Mac

**Installed060 is the current candidate.** [Full2122615tests/1skip,13 installed Native workflows and3 invalid controls](evidence/runtime060-installed-native-milestone-001.json) pass. [GUI095's assigned core observations are closed](evidence/gui-runtime060-095-observations-001.json). FullGUI, exact queued timing and broader release gates remain open. [Current status](STATUS.md).

Use `'.runs/runtime060 fresh install 001'`, source `972b395878b734ccf47c7691d66435c42c032634`, installed manifest `8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30`. The original manifest is `bb703d58271947e15430dc62187ace0afb1a5c70e3e76fe861933e717aa3becd`; its54 immutable files/build selection match except root. This is actual same-Mac fresh-folder CLI/GUI evidence, not cleanOS/account/dependency relocation or independent-user installation.

1. **Use the existing isolated launcher with the Native lane idle.** Save work and close conflicting KiCad managers/editors. Set Edge only for this child:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001/.runs/gui-launcher095/Launch Autorouter.command'
   ```

   Alternatively, open that same launcher in Finder and use **Microsoft Edge → File → Open File…** for generated `review/preview.html`. Leave Chrome/default-browser settings unchanged. Do not move or edit the launcher.

2. **Choose a saved complete project.** Open it in that manager, open PCB Editor and click the green autorouter toolbar icon. Select the exact source PCB and separate output folder; keep matching PRO/SCH/rules together. Save and close source editors, then acknowledge the paths. Unsaved buffers cannot be inspected.

3. **Begin with Route / Finish gaps /90seconds.** Keep standard/both/native, all source layers and engine-default via cost. Finish gaps preserves every existing route; whole-board routing preserves locked copper. Preview checks static support; Route performs the work. Unsupported input/settings refuse. Cancel retains unaccepted evidence and cannot authorize delivery.

4. **Review, then choose.** Create review and inspect front/back, all relevant layers, findings, warnings and ignored checks in Edge. If using Open review project, close its editors and **File → Close Project** before acknowledging review. Reject disables export; Accept intent is a software choice, not PCB approval.

5. **Validate and open a separate export.** Fresh export runs new original-rule Native checks. Open checked export checks current proof before opening that separate project. Originals are not overwritten. Editor PRO/PRL/backups can stale proof even when PCB bytes stay unchanged; the preserved preopen snapshot does not renew the changed live export.

The current owned example is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001/.runs/gui-session095/project/owned1007-transport.kicad_pcb'`; its preset is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001/.runs/gui-session095/route-settings.json'`. Preserve these prepared files and choose fresh outputs. Ordinary/high roles retain4protected routes; Improve retains1, six warnings and all roles two ignored checks. [GUI steps](docs/gui-workflow.md) · [CLI](docs/quickstart.md) · [Preferences](docs/routing-preferences.md).

GUI095 observed corrected40s Improve help, incumbent progress and a trial log in a separate cancellation control. A later actual active-engine Cancel matched engine−9/cleanup, CLI2/unaccepted/no downstream and unchanged sources. This does not prove graceful/all-phase cancellation or permanent descendant absence. Thermal Recover/fullGUI/exact queued timing remain unqualified.

Optional Improve is narrower than Route: canonical2Cu/flat/single-Default whole/native/tuned/both/source_all/default score. Its40s return reserve is inside the total budget, not a completion guarantee; no fallback follows stale/invalid/cancelled work. Corrected-standard/B1 remains default. Historical [059 Native](evidence/runtime059-native-milestone-001.json)/[GUI094](evidence/gui-runtime059-094-observations-001.json), [058 comparison](docs/benchmark-runtime058-installed.md) and immutable058's [archived-reader defect](evidence/runtime058-archived-receipt-defect-001.json)/[return failure](evidence/runtime058-natural-expiry-001.json) keep their original scope. New comparison preparation is not a result.

[Selected060 backup](evidence/backups/selected-runtime060-current-001.json) preserves the mapped cutoff onMac only; full restoration is capacity-blocked. [Windows012](evidence/windows012-policy-actual001.json) closed with WinError13/no Native. No standalone, cleanOS, fullGUI, broad quality, human or electrical qualification. [Installation](docs/install-existing.md) · [Previous guide preserved unchanged](docs/history/2026-10-20-pre-runtime050-user-guides/START_HERE.md).
