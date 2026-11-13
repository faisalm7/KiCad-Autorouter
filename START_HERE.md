# Try the local experimental candidate

Runtime087 demonstrates selected placement, protected Freerouting routing, readable review, cancellation and fresh separate-project delivery on this Mac. It works without AI. It is an experimental development candidate with narrow placement support; unrelated-board usefulness, independent installation and Windows Native routing remain unproved. [Evidence and open gates](STATUS.md).

The existing installation is `.runs/runtime087 fresh install 001`, source `aa6b10186776e786eb64b6f4314f0674aa13ef9c`, manifest `fca9d1180b5e32b5d89875009e9f5ae4e3a0db0c1adc9982fd73843b29e07462`. It uses isolated KiCad10.0.7 and pinned existing dependencies. Do not reinstall or rerun completed qualification just to resume.

1. Save work and close KiCad test editors/managers normally. From this checkout, run the prepared command:

   ```sh
   './.runs/runtime087 fresh install 001/.runs/gui-session113/Launch Design Assistant GUI113 Edge.command'
   ```

   Command-based startup was observed. **Finder-only double-click startup remains pending** because GUI access is locked. The launcher refuses an already-running KiCad rather than guessing which process owns a project. Its configuration and PCM root are isolated; it does not change personal plugins or browser settings.

2. Open the prepared inspection project in its PCB Editor and click the small green trace icon beside `>_`. The assistant opens in a separate window. This demo launcher is bound to the saved source under `gui-session113/source`; the inspection project is a separate copy. Confirm the displayed source/output paths, keep original source editors closed, and use fresh outputs. Existing jobs, source-fault copies and the edited export are retained test evidence.
3. Use **Placement** to inspect the saved project and its findings. Choose eligible components and an allowed rectangle, load/save settings, inspect alternatives and edit coordinates. Fixed and protected components remain fixed. Rebuilding affected unlocked copper requires explicit settings and review of the exact plan; preserve-all is the default. Current support is fixed-angle front translation with conservative geometry/annotation checks. Groups, orientation/side changes and advanced keepouts are not supported yet.
4. Explicitly review the draft, validate it with KiCad, then continue to Routing. Routing can also be used directly. Confirm scope, protected copper, supported layers, preferences and time budget. **Finish gaps** preserves all existing routes; whole routing preserves locked copper. Selected-net routing is narrow and experimental. Preview explains refused inputs. Start the job or Cancel while it runs.
5. Create review, inspect both copper layers and every finding in **Microsoft Edge**, then choose Accept intent or Reject intent. Acceptance records intent; it is not PCB engineering approval. Fresh export validates again and writes a separate project. **Open checked export** checks the exact current evidence before opening. Editor sidecar writes may stale the packet even when PCB bytes stay unchanged; the next opening must refuse it.

Original projects are not overwritten. Native checks, rules, connectivity and protected-copper checks remain mandatory. A changed-warning offer, when eligible, requires a new explicit acknowledgement of that exact candidate/report within the original deadline; it cannot waive blocking findings. The genuine changed-warning GUI branch and exact queued-open interval remain unexercised. Software-test acceptance is not human PCB approval.

[GUI113 evidence](evidence/runtime087-installed-GUI-core-001.json) records actual toolbar launch, presets, invalid edits, protected routing, Edge previews/findings, acceptance/rejection, active cancellation, export, PCB opening and source/settings/export refusal. Both missed cancellation attempts remain recorded. Its export is now correctly stale after KiCad changed project sidecars. CLI work totalled151.80seconds across18operations; full interaction and CPU costs are additional and unknown. These are correctness/workflow observations, not routing superiority or placement-quality measurements.

[Installation](docs/install-existing.md) · [CLI](docs/quickstart.md) · [Settings](docs/routing-preferences.md) · [Structured interface](docs/structured-interface.md) · [Platform matrix](docs/supported-platforms.md). No live model endpoint is configured. Human/physical/electrical review, full current recovery and formal publication remain open. New raw evidence is currently on this Mac only.
