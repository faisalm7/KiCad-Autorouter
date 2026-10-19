# Use the autorouter on this Mac

Start with a saved test project or a copy of your project. This is the current **runtime042 / GUI081 experimental workflow** for the existing KiCad 10.0.7 installation.

1. **Launch KiCad.** Save your work and close other KiCad applications. In Finder, double-click [Launch Autorouter.command](</Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime/.runs/gui-launcher081/Launch Autorouter.command>). To find it manually, use Finder’s **Go → Go to Folder…** and paste:

   ```text
   /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime/.runs/gui-launcher081
   ```

   The launcher opens KiCad with its own local plugin, settings and cache. Open your saved project in that manager, open PCB Editor and click the **green autorouter icon**.

2. **Identify the source.** In the routing window, choose the exact saved PCB and an output folder. Keep the matching project, schematic and original rule files together. Save and close the source PCB and schematic editors before acknowledging their paths. The tool cannot inspect unsaved editor changes.

3. **Start with Finish gaps, 90 seconds.** Keep the default routing preferences and all source copper layers. Finish gaps protects all existing copper; locked copper is always protected. Click **Preview** to check support, then **Route**. Watch progress and findings. **Cancel** stops the request and retains evidence; a cancelled result cannot authorize export. Unsupported settings refuse with a reason.

4. **Review the candidate.** Click **Create review**, then open the generated `review/preview.html` in Microsoft Edge using **File → Open File…**. The workspace is displayed in the routing window. Inspect before/after copper on every layer and read the findings, warnings and ignored checks. Leave Chrome and the default browser setting unchanged. Close any KiCad review editors/project before acknowledging review.

5. **Choose, validate and open.** **Reject intent** ends that candidate’s delivery. **Accept intent** records your choice, then **Fresh export** runs new KiCad checks into a separate candidate project. Use **Open checked export** to verify that proof before opening the exported board in KiCad. The saved source is not overwritten. Accept intent is not independent engineering approval, and live apply/undo is not offered.

Opening or editing an export can change its project settings and make its proof stale. That happened in the recorded positive: the PCB/source stayed unchanged, but later project/backup changes correctly refused the old proof. Preserve the source and use a fresh workflow when material has changed.

Keep this checkout, runtime and existing pinned tools at their recorded paths. Normal routing needs no Codex, AI subscription or internet. This fixed-path local setup is not a standalone installer, clean-OS or Windows qualification.

Current042 GUI081 has actual toolbar launch, saved settings, refusal, protected ordinary/display-alias routing, Edge review, Accept+Reject, fresh validation, checked opening, hierarchy/high-budget and optional recovery deliveries. Ordinary Java cancellation, a forced Native cancellation and source/settings/after-reader export refusal are recorded. These are assigned functional roles, not full GUI or independent user qualification. Exact queued-callback timing, natural/all-phase cancellation, general routing superiority and formal release remain unmet. Corrected-standard/B1 stays default. New raw evidence is Mac-only; current restoration remains capacity-blocked.

See the [detailed workflow](docs/gui-workflow.md), [saved settings](docs/routing-preferences.md), [CLI](docs/quickstart.md) and [structured interface](docs/structured-interface.md). [Current status](STATUS.md), [GUI evidence](evidence/gui-runtime042-081-functional-summary-001.json), [Native evidence](evidence/runtime042-native-milestone-001.json) and [support matrix](docs/experimental-rc.md) give the exact qualification limits.
