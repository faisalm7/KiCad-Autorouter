# Route and review with runtime050 / GUI086

Use the existing immutable runtime050 with isolated KiCad10.0.7 on this Mac. Source `aa0072c6b3d8090de2603e5ecb42a95968fb873b`, manifest `c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8`. [Seven CLI workflows passed](../evidence/runtime050-native-milestone-002.json); [current graphical evidence is partial](../evidence/gui-runtime050-086-progress-001.json), not full GUI or release qualification. Old042/049 observations do not qualify this build.

1. Save work and close conflicting KiCad sessions. Launch the existing session with a child-only Edge override:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-050/runtime/.runs/gui-launcher086/Launch Autorouter.command'
   ```

   Do not modify the launcher or owner Chrome/default-browser settings. Finder can open that same launcher; use **Edge → File → Open File…** for `review/preview.html` if no child override was supplied. The launcher isolates plugin/config/cache, reuses existing pinned dependencies and never closes unrelated apps for you.

2. In that manager, open the saved project, open PCB Editor and click the **green autorouter icon**. Select the exact saved source PCB and separate output folder. Keep the paired project, schematic and original rule files together. Save and close source editors, then acknowledge their paths. Unsaved buffers are outside this workflow’s observation.

3. Start with **Route / Finish gaps / 90 seconds**, standard profile, both corrections, all source copper layers and default via cost. Finish gaps preserves all existing tracks/vias; whole-board unlocked routing preserves locked copper. Supported ordinary two-/four-layer combinations must pass **Preview**; unknown constraints or unsupported settings refuse rather than being weakened.

4. Use **Preview**, then **Route**. Read progress and the completed findings. **Cancel** requests cleanup and retains partial evidence; cancellation cannot authorize review/export. The [current active-Java control](../evidence/gui-runtime050-086-active-engine-cancel-001.json) observed engine cancellation, CLI exit2, no positive UI and no owned survivor. It does not prove every cancellation phase, Native interruption or natural expiry.

5. Use **Create review** and inspect `review/preview.html` in Edge: both copper sides, all relevant layers, warnings and ignored checks. **Open review project** is a separate KiCad inspection copy. Close those editors and **File → Close Project** before acknowledging review. Then choose **Accept intent** or **Reject intent** explicitly. Accept records intent; it is not engineering certification. Reject disables delivery.

6. **Fresh export** runs fresh Native refill/connectivity/full-schematic, original-rule and immutable/protected-copper checks into another project. Export has its own 30–120-second allocation: captured90 gives export90; captured420 gives export120. The Route or whole-method budget does not change. If that allocation is insufficient, validation refuses.

7. **Open checked export** performs a current-proof check before opening the candidate project. The saved original is never overwritten; live apply/undo is unavailable. Opening/editing can alter PRO/PRL/backups and stale the export even when PCB bytes are unchanged. Changed source, captured settings or export material refuses; start a fresh session instead of editing receipts. Checks are cooperative, not an atomic transaction with subsequent editor reads.

For the owned ordinary example, source is `.runs/gui-session086/project/owned1007-transport.kicad_pcb`, settings `.runs/gui-session086/route-settings.json`, relative to runtime050. Inspection and jobs are separate. Keep original recorded files pristine and choose fresh output directories.

You can save/load JSON presets outside the source project and change the GUI budget from5–900 whole seconds. Check the displayed values after loading and Preview again after changes. Hidden `.runs` folders can be shown with **Command–Shift–Period** in a native picker. Standard missing-library/model notices are not silently repaired and nothing is downloaded. [Preference schema](routing-preferences.md).

Optional methods are narrower than ordinary Route:

| Method | Required scope and budget |
|---|---|
| **Improve (experimental)** | Selected10.0.7, qualified canonical2Cu/flat/single-Default source, whole-board/native/tuned/both/source_all/default via cost. GUI minimum90s. Its whole-method budget includes the tuned incumbent, pruning trials, final checks and25s internal return reserve; that reserve is not extra time or a completion guarantee. |
| **Thermal recovery (experimental)** | Selected10.0.7, supported2Cu source, whole-board/native/standard/both/source_all/default via cost,90–900s whole-method budget. Incumbent, repair attempts and final checks are included. Separate export remains capped; no failed/cancelled fallback is automatically accepted. Evidence remains limited to exposed development cases. |

Selecting Improve explicitly chooses tuned/both; task protection, layers, via preference and budget are not silently relaxed. Incompatible choices refuse. Ordinary standalone tuned Route is unsupported in this selected profile. Neither optional method establishes broad completion or electrical gains.

[Current controls](../evidence/gui-runtime050-086-controls-delta-001.json) include rejection and source/settings refusals. The [menu hold attempt](../evidence/gui-runtime050-086-queued-miss-001.json) opened only the manager while the menu remained visible; no mutation or exact queued-callback pass occurred, and that method stopped. Current GUI remains partial. The separate [negative escape experiment](../evidence/qfn-escape-development-probe-002.json) is deferred and outside runtime050.

For CLI use, enter the runtime directory first; an absolute interpreter path alone can still import the checkout’s module from the wrong working directory. [CLI](quickstart.md) · [Same-Mac fresh-folder install](install-existing.md) · [Status](../STATUS.md). No standalone/cleanOS/Windows, independent human, physical/electrical, full-GUI or general routing-quality claim. [Previous guide](history/2026-10-20-pre-runtime050-user-guides/gui-workflow.md).
