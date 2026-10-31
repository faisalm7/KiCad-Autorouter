# Use experimental runtime067 on this Mac

**The current067 CLI/native and [actual GUI100 finite milestone](evidence/gui-runtime067-100-qualification-001.json) pass.** The workflow below was observed on067 in the declared two/four-layer and class-Improve scope. Historical066 evidence remains separate. Large Improve rendered delivery still fails30s; this is not a qualified release. [Evidence](evidence/runtime067-installed-native-milestone-001.json) · [Gates](STATUS.md).

The installed folder is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime067 fresh install 001'`. Source: `776cb8b0e50d2e8a202d30962ed674f7185b0ccd`; installed manifest: `20bcf247eaa3cb2e69992c2f24768465a2a50ffe90f0f91199dc10a422144bb7`. It uses isolated KiCad10.0.7 and existing local dependencies. Same Mac/account testing is not independent installation.

For the tested command-line workflow, follow [CLI instructions](docs/quickstart.md). Normal routing needs no AI account or network. Use fresh output folders and enter the installed directory before running commands.

The [actual067 GUI100 workflow](evidence/gui-runtime067-100-qualification-001.json) exercised finite two/four-layer and class-Improve controls. Keep the routing lane idle, use fresh outputs and preserve completed evidence:

1. Save work and close the old owned autorouter/KiCad test windows normally. Launch the new isolated manager with its child-only Edge setting:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime067 fresh install 001/.runs/gui-launcher100/Launch Autorouter.command'
   ```

2. Open the prepared inspection project in that manager, open PCB Editor and click the green bent-trace autorouter icon beside `>_`. The source project is `'.runs/runtime067 fresh install 001/.runs/gui-session100/ordinary-project/owned1007-transport.kicad_pcb'`; the preset is `ordinary-settings.json` in the GUI session folder. The four-layer role uses `four-copper-project` and `four-copper-settings.json`; keep those roles paired. Choose a fresh output. Save and close source editors before acknowledging the exact paths.
3. Choose scope, copper protection, supported layers, preferences and routing budget. Start routing, read progress or cancel. Unsupported settings refuse. Finish gaps protects every existing route; whole routing preserves locked copper.
4. Create review. Inspect front/back and all relevant layers, findings, warnings and ignored checks in **Microsoft Edge**. Close any review project editors before acknowledging review. Accept records intent; Reject disables export. Neither is electrical certification.
5. Fresh export performs new original-rule native checks into a separate project. Open checked export checks freshness before opening it. Editor metadata can stale proof even when PCB bytes stay unchanged. Originals are never overwritten; live application/undo is unavailable.

These finite steps were observed on067/GUI100; exact queued callback timing, every cancellation phase, thermal recovery and live undo remain unqualified. The frozen completed job folders are evidence; do not overwrite or rerun them. Separate four-layer/high-via and class-Improve source roles remain available for fresh jobs; do not mix their settings or use prior candidates as source. Preview is static support information, not Native acceptance. The routing budget, review and fresh-export costs are distinct; end-to-end comparisons charge them all. [Preferences](docs/routing-preferences.md) · [Installation](docs/install-existing.md).

Broader completion beyond corrected/tuned Freerouting, Windows native support, full restoration, independent installation, human cleanup and physical/electrical validation remain open. Backups stay on this Mac and provide no disk-failure protection. No formal release has been published.
