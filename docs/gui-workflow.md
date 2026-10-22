# Route and review with runtime057 / GUI090

The current immutable runtime057 uses isolated KiCad10.0.7 on this Mac. Source `ac1a48c3b25b2217e0f8252e0e6da21905f144a4`, manifest `9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e`. [Eleven CLI workflows](../evidence/runtime057-native-milestone-001.json), [ordinary GUI090](../evidence/gui-runtime057-090-ordinary-001.json), [high/Improve and safety roles](../evidence/gui-runtime057-090-controls-deliveries-001.json) and [one fresh-root GUI091 vertical slice](../evidence/gui-runtime057-install091-delivery-001.json) have actual evidence. Sessions are closed normally; there is no current access blocker or requested owner action. These are scoped functional observations, not full GUI/release, independent-user or electrical qualification.

1. Save work and close conflicting KiCad sessions. Launch the existing session with a child-only Edge override:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-057/runtime/.runs/gui-launcher090/Launch Autorouter.command'
   ```

   Do not modify the launcher or owner Chrome/default-browser settings. Finder can open that same launcher; use **Edge → File → Open File…** for `review/preview.html` if no child override was supplied. The launcher isolates plugin/config/cache, reuses existing pinned dependencies and never closes unrelated apps for you.

2. In that manager, open the saved project, open PCB Editor and click the **green autorouter icon**. Select the exact saved source PCB and separate output folder. Keep the paired project, schematic and original rule files together. Save and close source editors, then acknowledge their paths. Unsaved buffers are outside this workflow’s observation.

3. Start with **Route / Finish gaps / 90 seconds**, standard profile, both corrections, all source copper layers and default via cost. Finish gaps preserves all existing tracks/vias; whole-board unlocked routing preserves locked copper. Supported ordinary two-/four-layer combinations must pass **Preview**; unknown constraints or unsupported settings refuse rather than being weakened.

4. Use **Preview**, then **Route**. Read progress and the completed findings. **Cancel** requests cleanup and retains partial evidence; cancellation cannot authorize review/export. The [current GUI090 active-engine control](../evidence/gui-runtime057-090-controls-deliveries-001.json) records SIGINT/cancelled/cleanuptrue, CLI exit2, an unaccepted parent and no downstream review/export. It does not prove algorithm entry, every phase, permanent descendant absence or natural expiry. The [historical050 control](../evidence/gui-runtime050-086-active-engine-cancel-001.json) retains its own scope.

5. Use **Create review** and inspect `review/preview.html` in Edge: both copper sides, all relevant layers, warnings and ignored checks. **Open review project** is a separate KiCad inspection copy. Close those editors and **File → Close Project** before acknowledging review. Then choose **Accept intent** or **Reject intent** explicitly. Accept records intent; it is not engineering certification. Reject disables delivery.

6. **Fresh export** runs fresh Native refill/connectivity/full-schematic, original-rule and immutable/protected-copper checks into another project. Export has its own 30–120-second allocation: captured90 gives export90; captured420 gives export120. The Route or whole-method budget does not change. If that allocation is insufficient, validation refuses.

7. **Open checked export** performs a current-proof check before opening the candidate project. The saved original is never overwritten; live apply/undo is unavailable. Opening/editing can alter PRO/PRL/backups and stale the export even when PCB bytes are unchanged. Changed source, captured settings or export material refuses; start a fresh session instead of editing receipts. Checks are cooperative, not an atomic transaction with subsequent editor reads.

For the owned ordinary example, source is `.runs/gui-session090/project/owned1007-transport.kicad_pcb`, settings `.runs/gui-session090/route-settings.json`, relative to runtime057. Inspection and jobs are separate. Keep original recorded files pristine and choose fresh output directories.

You can save/load JSON presets outside the source project and change the GUI budget from5–900 whole seconds. Check the displayed values after loading and Preview again after changes. Hidden `.runs` folders can be shown with **Command–Shift–Period** in a native picker. Standard missing-library/model notices are not silently repaired and nothing is downloaded. [Preference schema](routing-preferences.md).

Optional methods are narrower than ordinary Route:

| Method | Required scope and budget |
|---|---|
| **Improve (experimental)** | Selected10.0.7, qualified canonical2Cu/flat/single-Default source, whole-board/native/tuned/both/source_all/default via cost. GUI minimum90s. Its whole-method budget includes the tuned incumbent, pruning trials, final checks and25s internal return reserve; that reserve is not extra time or a completion guarantee. |
| **Thermal recovery (experimental)** | Selected10.0.7, supported2Cu source, whole-board/native/standard/both/source_all/default via cost,90–900s whole-method budget. Incumbent, repair attempts and final checks are included. Separate export remains capped; no failed/cancelled fallback is automatically accepted. Evidence remains limited to exposed development cases. |

Selecting Improve explicitly chooses tuned/both; task protection, layers, via preference and budget are not silently relaxed. Incompatible choices refuse. Ordinary standalone tuned Route is unsupported in this selected profile. Neither optional method establishes broad completion or electrical gains.

[Historical050 controls](../evidence/gui-runtime050-086-controls-delta-001.json) include rejection and source/settings refusals. The [menu hold attempt](../evidence/gui-runtime050-086-queued-miss-001.json) opened only the manager while the menu remained visible; no mutation or exact queued-callback pass occurred, and that method stopped. Current GUI090 ordinary/high/Improve delivery, Reject, source/settings refusal and active-engine Cancel are retained in the public controls above. One [GUI091 fresh-root slice](../evidence/gui-runtime057-install091-delivery-001.json) completes the ordinary partial90 workflow. Its planned post-reader mutation control aborted before mutation on an identity/status assertion and resumed the GUI: no actual guard or exact queued timing pass. STOP method stays stopped with no retry. The separate [negative escape experiment](../evidence/qfn-escape-development-probe-002.json) remains deferred and outside runtime057.

For CLI use, enter the runtime directory first; an absolute interpreter path alone can still import the checkout’s module from the wrong working directory. [CLI](quickstart.md) · [Same-Mac fresh-folder install](install-existing.md) · [Status](../STATUS.md). No standalone/cleanOS/Windows, independent human, physical/electrical, full-GUI or general routing-quality claim. [Previous guide](history/2026-10-20-pre-runtime050-user-guides/gui-workflow.md).
