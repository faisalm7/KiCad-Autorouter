# Try the local experimental candidate

**Runtime075 has completed its installed CLI and finite GUI106 core checks.** It offers saved-project inspection, protected routing, review, cancellation and fresh separate-project export on this tested Mac setup. It remains an experimental development candidate. Genuine changed-warning GUI interaction, the exact queued-open interval and live model use remain unqualified. [Current evidence and gates](STATUS.md) · [CLI instructions](docs/quickstart.md).

The tested installation is `.runs/runtime075 fresh install 001`, built from `b91520b90cdfeb86aba1dd1e9458e941f2c810a7`, manifest `f0b304061ab1f5e30f2514b4bcbd5ab5b31636e5872bb4927928acb7e29cc810`. It uses isolated KiCad10.0.7 and existing dependencies. Core routing needs no AI account or network. Independent installation and Windows routing remain unqualified.

**Known interface issue in this installation:** changing the source/output path leaves the saved/closed acknowledgement checked. Uncheck it, verify the new paths and closed editors, then check it again. A source fix has targeted tests but is not installed here yet. Native validation and freshness guards remain mandatory. Placement has a [source-run review prototype](docs/placement-review.md), not installed placement support.

1. Save your work and close other KiCad test managers/editors normally. From this project folder, launch the prepared isolated manager with Microsoft Edge for previews:

   ```sh
   './.runs/runtime075 fresh install 001/.runs/gui-session106/Launch Autorouter GUI106 Edge.command'
   ```

   This is the existing local qualification setup. For installing into another folder, use the separate [installation guide](docs/install-existing.md); this command does not establish a standalone installation.

2. Open a complete saved KiCad project and its PCB Editor. Click the small green bent-trace Autorouter icon beside the grey `>_` toolbar button. Routing opens in a separate window. Confirm the exact PCB and output paths, then close the source PCB and schematic editors before acknowledging them. Keep originals saved and closed throughout the job.
3. Choose routing scope and copper protection, supported layers, preferences and a time budget. Save settings for reuse or load a preset. **Finish gaps** preserves all existing routes; whole routing preserves locked copper. Explicit selected-net routing is narrow and experimental. Preview reports supported choices and reasons for refusal. Unsupported electrical or design requirements remain unresolved; net names and DRC cannot establish them.
4. Start routing, watch progress, or Cancel. Create review and inspect the before/after copper layers and every finding in **Microsoft Edge**. Close the review editors and project before acknowledging review. Choose Accept intent or Reject intent. Reject disables export; Accept records a decision and does not certify the PCB.
5. Fresh export performs new original-rule native validation into a separate project. Open checked export rechecks its current evidence before opening it. If a narrowly eligible warning-report change occurs, runtime075 requests explicit review of both finding lists within the original export deadline. Rejection, cancellation, expiry or changed inputs cannot produce an accepted export. The genuine updated-warning dialog remains unexercised in GUI106; headless controls do not qualify that graphical branch.

Sources are never overwritten. Editor metadata can stale a proof even when PCB bytes do not change. Live application and undo are unavailable. Routing, review and export have separate ceilings; fair comparisons must count all of them. Use fresh output names and preserve failed jobs. [Settings](docs/routing-preferences.md) · [Graphical limits](docs/gui-workflow.md) · [Structured interface](docs/structured-interface.md).

The GUI106 inspection project is `.runs/runtime075 fresh install 001/.runs/gui-session106/inspection/owned1007-transport.kicad_pro`. Closed jobs and the deliberate stale-source/export faults remain preserved. Use fresh outputs; do not rerun those tests merely to try the interface. The [nine-job record](evidence/gui-runtime075-106-core-001.json) separates successful deliveries, rejection, active cancellation and two missed cancellation-control attempts. The selected export became stale after editor project writes; its earlier pristine success does not authorize reopening the changed packet.

The [current large CLI delivery](evidence/runtime074-large-delivery-qualified-001.json) meets its fixed delivery/headroom limits; no broader completion or quality gain beyond corrected/tuned/restart Freerouting is established. Every cancellation phase, Windows routing, untouched confirmation, independent installation/full recovery, human review and physical/electrical validation remain open. The [GUI106 compact backup](evidence/backups/selected-runtime075-gui106-001.json) verifies an exact subset on this Mac only. No formal release has been published.
