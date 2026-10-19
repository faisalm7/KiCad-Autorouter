# Use the autorouter on this Mac

Start with a saved test project or a copy of your project. This is the current **runtime039 / GUI079 experimental workflow** for the existing KiCad 10.0.7 installation.

1. **Launch KiCad.** Save your work and close other KiCad applications. In Finder, double-click [Launch Autorouter.command](</Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-039/runtime/.runs/gui-launcher079/Launch Autorouter.command>). To find it manually, use Finder’s **Go → Go to Folder…** and paste:

   ```text
   /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-039/runtime/.runs/gui-launcher079
   ```

   The launcher opens KiCad with its own local plugin, settings and cache. Open your saved project in that manager, open PCB Editor and click the **green autorouter icon**.

2. **Identify the source.** In the routing window, choose the exact saved PCB and an output folder. Keep the matching project, schematic and original rule files together. Save and close the source PCB and schematic editors before acknowledging their paths. The tool cannot inspect unsaved editor changes.

3. **Start with Finish gaps, 90 seconds.** Keep the default routing preferences and all source copper layers. Finish gaps protects all existing copper; locked copper is always protected. Click **Preview** to check support, then **Route**. Watch progress and findings. **Cancel** stops the request and retains evidence; a cancelled result cannot authorize export. Unsupported settings refuse with a reason.

4. **Review the candidate.** Click **Create review**, then **Open preview**. Inspect before/after copper on every layer and read the findings, warnings and ignored checks. If Chrome is busy, open the generated local review HTML in Edge using **File → Open File…**; there is no need to change the Mac’s default browser. Close any KiCad review editors/project before acknowledging review.

5. **Choose, validate and open.** **Reject intent** ends that candidate’s delivery. **Accept intent** records your choice, then **Fresh export** runs new KiCad checks into a separate candidate project. Use **Open checked export** to verify that proof before opening the exported board in KiCad. The saved source is not overwritten. Accept intent is not independent engineering approval, and live apply/undo is not offered.

Opening or editing an export can change its project settings and make its proof stale. That happened in the recorded positive: the PCB/source stayed unchanged, but later project/backup changes correctly refused the old proof. Preserve the source and use a fresh workflow when material has changed.

Keep this checkout, runtime and existing pinned tools at their recorded paths. Normal routing needs no Codex, AI subscription or internet. This fixed-path local setup is not a standalone installer, clean-OS or Windows qualification.

The ordinary GUI079 positive, reject, three independent source/settings/export-change refusals and engine cancellation have been observed. Actual forced queued-opening timing was **not** captured; that interval remains covered by software controls only. [Optional recovery](evidence/gui-runtime039-079-recovery-repair-001.json) has also completed review, explicit accept intent, fresh validation and checked KiCad opening on one exposed board with 22 warnings. Current [post-incumbent cancellation](evidence/gui-runtime039-079-postincumbent-cancel-001.json), [no-repair delivery](evidence/gui-runtime039-079-recovery-no-repair-001.json) and [hierarchy/high-budget delivery](evidence/gui-runtime039-079-hierarchy-high-budget-001.json) are also observed. Cancellation blocked positive adoption after preserving the accepted incumbent; the observed Native workers had finished normally, so Native interruption is not proved. The default ordinary method is unchanged. General completion or cleanup superiority, electrical/manufacturing approval and a formal release remain unproved. Full newer raw evidence remains Mac-only and a new full restoration is still capacity-blocked.

See the [detailed workflow](docs/gui-workflow.md), [saved settings](docs/routing-preferences.md), [CLI](docs/quickstart.md) and [structured interface](docs/structured-interface.md). [Current status](STATUS.md), [GUI positive/reject evidence](evidence/gui-runtime039-079-positive-reject-001.json), [Native/CLI evidence](evidence/runtime039-native-floor-schema-milestone-001.json) and the [support matrix](docs/experimental-rc.md) give the exact qualification limits.
