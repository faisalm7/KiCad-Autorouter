# Use experimental runtime068 on this Mac

**The current068 CLI/native and [actual GUI101 finite milestone](evidence/gui-runtime068-101-qualification-001.json) pass.** The workflow below was observed on068 in the declared two/four-layer and class-Improve scope. Historical066 evidence remains separate. Large Improve delivery still fails the30s acceptance stage after review completes inside60s; this is not a qualified release. [Evidence](evidence/runtime068-installed-native-milestone-001.json) · [Gates](STATUS.md).

The installed folder is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime068 fresh install 001'`. Source: `b2092507b0518d238b884a2812d64802bd3e531a`; installed manifest: `b47afc0389174c86acb1484e191e0e11c607fafac614188d3143ec481c18151c`. It uses isolated KiCad10.0.7 and existing local dependencies. Same Mac/account testing is not independent installation.

For the tested command-line workflow, follow [CLI instructions](docs/quickstart.md). Normal routing needs no AI account or network. Use fresh output folders and enter the installed directory before running commands.

The [actual068 GUI101 workflow](evidence/gui-runtime068-101-qualification-001.json) exercised finite two/four-layer and class-Improve controls. First resolve the current disk-reserve gate (at least5GiB free requested). Then keep the routing lane idle, use fresh outputs and preserve completed evidence:

1. Save work and close the old owned autorouter/KiCad test windows normally. Launch the new isolated manager with its child-only Edge setting:

   ```sh
   BROWSER='/usr/bin/open -a "Microsoft Edge" %s' \
     '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime068 fresh install 001/.runs/gui-launcher101/Launch Autorouter.command'
   ```

2. Open the prepared inspection project in that manager, open PCB Editor and click the green bent-trace autorouter icon beside `>_`. The source project is `'.runs/runtime068 fresh install 001/.runs/gui-session101/ordinary-project/owned1007-transport.kicad_pcb'`; the preset is `ordinary-settings.json` in the GUI session folder. The four-layer role uses `four-copper-project` and `four-copper-settings.json`; keep those roles paired. Choose a fresh output. Save and close source editors before acknowledging the exact paths.
3. Choose scope, copper protection, supported layers, preferences and routing budget. Start routing, read progress or cancel. Unsupported settings refuse. Finish gaps protects every existing route; whole routing preserves locked copper.
4. Create review. Inspect front/back and all relevant layers, findings, warnings and ignored checks in **Microsoft Edge**. Close any review project editors before acknowledging review. Accept records intent; Reject disables export. Neither is electrical certification.
5. Fresh export performs new original-rule native checks into a separate project. Open checked export checks freshness before opening it. Editor metadata can stale proof even when PCB bytes stay unchanged. Originals are never overwritten; live application/undo is unavailable.

These finite steps were observed on068/GUI101; exact queued callback timing, every cancellation phase, thermal recovery and live undo remain unqualified. The frozen completed job folders are evidence; do not overwrite or rerun them. Separate four-layer/high-via and class-Improve source roles remain available for fresh jobs; do not mix their settings or use prior candidates as source. Preview is static support information, not Native acceptance. The routing budget, review and fresh-export costs are distinct; end-to-end comparisons charge them all. [Preferences](docs/routing-preferences.md) · [Installation](docs/install-existing.md).

Broader completion beyond corrected/tuned Freerouting, Windows native support, full restoration, independent installation, human cleanup and physical/electrical validation remain open. Backups stay on this Mac and provide no disk-failure protection. No formal release has been published.
