# Use the autorouter on this Mac

Start with a saved test project or a copy of your project. This is the current **runtime041 / GUI080 experimental workflow** for the existing KiCad 10.0.7 installation.

1. **Launch KiCad.** Save your work and close other KiCad applications. In Finder, double-click [Launch Autorouter.command](</Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-041/runtime/.runs/gui-launcher080/Launch Autorouter.command>). To find it manually, use Finder’s **Go → Go to Folder…** and paste:

   ```text
   /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-041/runtime/.runs/gui-launcher080
   ```

   The launcher opens KiCad with its own local plugin, settings and cache. Open your saved project in that manager, open PCB Editor and click the **green autorouter icon**.

2. **Identify the source.** In the routing window, choose the exact saved PCB and an output folder. Keep the matching project, schematic and original rule files together. Save and close the source PCB and schematic editors before acknowledging their paths. The tool cannot inspect unsaved editor changes.

3. **Start with Finish gaps, 90 seconds.** Keep the default routing preferences and all source copper layers. Finish gaps protects all existing copper; locked copper is always protected. Click **Preview** to check support, then **Route**. Watch progress and findings. **Cancel** stops the request and retains evidence; a cancelled result cannot authorize export. Unsupported settings refuse with a reason.

4. **Review the candidate.** Click **Create review**, then **Open preview**. Inspect before/after copper on every layer and read the findings, warnings and ignored checks. If Chrome is busy, open the generated local review HTML in Edge using **File → Open File…**; there is no need to change the Mac’s default browser. Close any KiCad review editors/project before acknowledging review.

5. **Choose, validate and open.** **Reject intent** ends that candidate’s delivery. **Accept intent** records your choice, then **Fresh export** runs new KiCad checks into a separate candidate project. Use **Open checked export** to verify that proof before opening the exported board in KiCad. The saved source is not overwritten. Accept intent is not independent engineering approval, and live apply/undo is not offered.

Opening or editing an export can change its project settings and make its proof stale. That happened in the recorded positive: the PCB/source stayed unchanged, but later project/backup changes correctly refused the old proof. Preserve the source and use a fresh workflow when material has changed.

Keep this checkout, runtime and existing pinned tools at their recorded paths. Normal routing needs no Codex, AI subscription or internet. This fixed-path local setup is not a standalone installer, clean-OS or Windows qualification.

Current041 GUI080 has actual toolbar launch, protected ordinary and renamed-layer routing, Edge before/after review, explicit acceptance, fresh validation and checked KiCad opening with0unrouted. Explicit rejection and static recovery refusals also pass. The remaining freshness, cancellation, hierarchy/high-budget and optional recovery delivery roles are pending. Forced queued-opening timing and Native interruption remain unproved. Corrected-standard/B1 stays default; general completion/cleanup/electrical superiority and formal release remain unmet. Newer raw evidence is Mac-only and current restoration is capacity-blocked.

See the [detailed workflow](docs/gui-workflow.md), [saved settings](docs/routing-preferences.md), [CLI](docs/quickstart.md) and [structured interface](docs/structured-interface.md). [Current status](STATUS.md), [GUI progress](evidence/gui-runtime041-080-progress-001.json), [Native evidence](evidence/runtime041-native-milestone-001.json) and [support matrix](docs/experimental-rc.md) give the exact qualification limits.
