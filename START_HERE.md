# Try the local experimental candidate

**Runtime074 passes its headless native checks; its actual GUI105 qualification is pending.** It is a development candidate, not a qualified release. [Current evidence and gates](STATUS.md) · [CLI instructions](docs/quickstart.md).

The current installation is `.runs/runtime074 fresh install 001` in this checkout, built from `6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194`, manifest `584ee929eaf3d277dc535556e42c71ac5196a74f1c5e3fd53a2cce5a67853d61`. It uses isolated KiCad10.0.7 and existing local dependencies. Normal routing requires no AI account or network. Independent installation and Windows routing remain unqualified.

1. Save your work and close other KiCad test managers/editors normally. From this project folder, launch the prepared isolated manager with Microsoft Edge for previews:

   ```sh
   './.runs/runtime074 fresh install 001/.runs/gui-session105/Launch Autorouter GUI105 Edge.command'
   ```

   This is the existing local qualification setup. For installing into another folder, use the separate [installation guide](docs/install-existing.md); this command does not establish a standalone installation.

2. Open a complete saved KiCad project and its PCB Editor. Click the small green bent-trace Autorouter icon beside the grey `>_` toolbar button. Routing opens in a separate window. Confirm the exact PCB and output paths, then close the source PCB and schematic editors before acknowledging them. Keep originals saved and closed throughout the job.
3. Choose routing scope and copper protection, supported layers, preferences and a time budget. Save settings for reuse or load a preset. **Finish gaps** preserves all existing routes; whole routing preserves locked copper. Explicit selected-net routing is narrow and experimental. Preview reports supported choices and reasons for refusal. Unsupported electrical or design requirements remain unresolved; net names and DRC cannot establish them.
4. Start routing, watch progress, or Cancel. Create review and inspect the before/after copper layers and every finding in **Microsoft Edge**. Close the review editors and project before acknowledging review. Choose Accept intent or Reject intent. Reject disables export; Accept records a decision and does not certify the PCB.
5. Fresh export performs new original-rule native validation into a separate project. Open checked export rechecks its current evidence before opening it. If a narrowly eligible warning-report change occurs, runtime074 requests explicit review of both finding lists within the original export deadline. Rejection, cancellation, expiry or changed inputs cannot produce an accepted export. This new graphical branch is not yet qualified.

Sources are never overwritten. Editor metadata can stale a proof even when PCB bytes do not change. Live application and undo are unavailable. Routing, review and export have separate ceilings; fair comparisons must count all of them. Use fresh output names and preserve failed jobs. [Settings](docs/routing-preferences.md) · [Graphical limits](docs/gui-workflow.md) · [Structured interface](docs/structured-interface.md).

For the prepared GUI105 qualification only, the inspection project is `.runs/runtime074 fresh install 001/.runs/gui-session105/inspection/owned-four-copper-forced-inner.kicad_pro`. Its ordinary, four-copper, parent-class and selected source/preset pairs are under the same session folder. They are test inputs, not passed graphical results. The current file-chooser input-tool blocker is recorded in STATUS; no security or sleep-setting change is required.

No broader completion gain beyond corrected/tuned/restart Freerouting has been demonstrated. Current large delivery, Windows safeguards/native routing, untouched confirmation, independent installation/full recovery, human review and physical/electrical validation remain open. Backups are on this Mac only. No formal release has been published.
