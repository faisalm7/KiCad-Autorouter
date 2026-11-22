# Installation and advanced CLI

**Use an existing installation and launcher when available.** [Start here](../START_HERE.md) and the [saved-project workflow](quickstart.md) use your project, not a prepared demonstration session. Reinstallation is unnecessary merely to resume.

The latest checked delivery on this Mac uses source `30d914259dbd230aa1ebde9c4375a7da2321fecc` and manifest `4db1f1f6cdfdbf48e1455f418d395c67819f765585fc52205f5bf743d84f8e63`. The same-Mac first setup and the earlier actual toolbar check have separate receipts. Recent opening and review changes still need installed checks. Standalone and independent-machine installation are open. [Checked delivery](../evidence/product-round-cutout-checked-delivery-002.json) · [First setup](../evidence/product-direct-first-setup-and-keyboard-002.json) · [Toolbar check](../evidence/product104-usability-delivery-001.json).

The tested setup uses macOS 27.0.1 arm64, isolated official KiCad 10.0.7, Java 25.0.2, Freerouting 2.5.0, a no-pip Python 3.11.9 environment and KiCad's bundled Python 3.9.13/wx for the GUI. Exact dependency bytes and locations are pinned. A new environment still depends on its base Python/standard library; `--copies` does not bundle Python. Nothing here downloads or installs dependencies, changes global KiCad, or qualifies Windows Native support.

## First setup with existing Mac tools

From the reviewed committed source checkout, provide your locations for the
pinned KiCad 10.0.7 app, Java executable and Freerouting JAR. Choose a new
installation folder inside an existing directory you own.

```sh
python3.11 -B scripts/prepare_runtime.py --native-version 10.0.7 \
  --kicad-app "/path/to/KiCad.app" \
  --java-executable "/path/to/jdk/Contents/Home/bin/java" \
  --freerouting-jar "/path/to/freerouting-2.5.0.jar" \
  --output "/path/to/new/Copperpath" --with-launcher
```

Setup checks the existing dependencies against `toolchain.lock.json`, then
prepares and checks the local workspace. It leaves the original lock and
dependency files intact. Open the **Copperpath.app** at the printed
`workspace_launcher` location in Finder. A checked artifact and a research
archive are unnecessary for this setup.

## Advanced: install a verified artifact at a fresh local root

Use the reviewed source checkout's `scripts/prepare_runtime.py`; the curated runtime does not ship that installer. Choose a verified source artifact and an unused owned destination below an existing real directory. Check available space against the operation's peak allocation plus the fixed 3 GiB reserve. Do not copy an old environment, jobs, settings or launcher to simulate a new installation.

For one-step setup on the supported Mac, add `--with-launcher`. This creates a fresh local Python environment, checks dependencies and prepares the launcher. It uses the existing pinned tools and local engine. Replace the artifact and destination paths with your own verified source and new folder, and use the exact artifact manifest hash. Run from the source checkout with Python 3.11.

```sh
(
set -eu
AUTOROUTER_ARTIFACT="/path/to/verified Copperpath artifact"
AUTOROUTER_INSTALL="/path/to/new owned installation"
python3.11 -B scripts/prepare_runtime.py --install-existing \
  --source "$AUTOROUTER_ARTIFACT" \
  --expected-manifest-sha256 4db1f1f6cdfdbf48e1455f418d395c67819f765585fc52205f5bf743d84f8e63 \
  --output "$AUTOROUTER_INSTALL" --with-launcher
)
```

Open the `workspace_launcher` shown when setup completes. The current build prepares **Copperpath.app** in its launcher folder. Open it through Finder. Earlier artifacts prepare **Open Saved Project.command**. A refusal leaves the completed stages and logs under `.runs/launcher-setup` in the new folder. Fix the stated dependency or input and use a fresh destination. [Observed app launch](../evidence/product-workspace-context-finder-001.json)

Enter the selected runtime before every `-m autorouter` command: using its interpreter from another checkout can import the wrong code. Follow the new launcher's README. It binds the runtime, tools and isolated configuration/documents/cache/plugin area. Keep those locations intact; a moved or replaced launcher needs fresh preparation. The launcher is a cooperative boundary, not an OS sandbox.

Before inspecting or routing, save and close the source PCB/schematic editors, then choose **File → Close Project** in KiCad manager. Closing only the editor windows leaves the project open. Existing launcher copies may omit this instruction; keep their bound files unchanged and follow this step here.

## Saved-project launcher and optional toolbar handoff

The Finder app shows the failed startup check if the launcher or its pinned
tools change. Open Copperpath from the launcher folder created during setup.
For an installation you moved, prepare a fresh copy from the verified artifact
using the same dependency checks. The local Python fallback also points to
**Open Saved Project.command** for diagnostics.
[Observed startup and fault controls](../evidence/product-finder-startup-recovery-001.json)

Double-click **Copperpath.app** to open the workspace. Use **Open Saved Project.command** from the same folder when you need startup diagnostics. Choose the `.kicad_pro` file while the project is closed. Inspection starts automatically. Keep its matching PCB, schematic and rules together. After edits, save and choose **Refresh inspection** before continuing. Both launchers use the same checked local runtime.

Fresh preparation provisions an empty private job directory for inspection
and validation. Installing an existing artifact preserves its checked program
files and starts with a fresh private job directory. Past job contents stay
with the original installation.

For local placement suggestions, open a saved project, wait for its board, then
open **Conversation**. Earlier workspace builds call this tab **Request**.
If the launcher starts in routing, choose **Place components** to reach the
placement workspace.
Enter one or more example lines and preview the
selection, movement area or routing time. Edit the suggestion if needed,
preview the edits and choose **Use settings**. Search, validation, routing and
export remain explicit steps from the usual controls.
[Example and tested workflow](live-editor-milestone.md#placement-constraints-from-a-request)

Use **Schematic** to see the current saved sheet, component and pad-net
details on the board-first build. [Board-first workspace](saved-project-workspace.md)

**Launch Autorouter.command** opens the isolated KiCad manager for the optional PCB toolbar. For automatic project selection, install the official KiCad Python IPC client in the runtime’s existing Python 3.11 environment. The following command pins the wheels for macOS arm64. Set the paths to the verified local runtime and the source checkout that supplied it.

```sh
python3.11 -m pip --isolated --python "/path/to/runtime/.venv" install \
  --index-url https://pypi.org/simple --only-binary=:all: --require-hashes \
  -r "/path/to/source/docs/kicad-toolbar-macos-arm64.txt"
```

The toolbar reads the single open PCB identity from the invoking KiCad instance over its local socket. Copperpath confirms a matching saved project and prompts you to close it before work. A missing client, unavailable connection or mismatched project leaves the picker empty with an explanation. Pick the saved project to continue. The package wheels and their notices are supplied by PyPI and are outside the curated runtime payload. The client is MIT-licensed and includes generated protocol modules carrying KiCad license notices. [KiCad IPC developer notes](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html) · [Pinned client](https://pypi.org/project/kicad-python/0.8.0/) · [Wheel pins](kicad-toolbar-macos-arm64.txt).

### Try the checked move on the supplied example

For a build that includes `--checked-move-editor`, use a fresh launcher and
the already verified, isolated KiCad 10.0.8 application. Keep the existing
KiCad 10.0.7 Native dependencies for detached checks. Run from the runtime
after installing the pinned IPC wheels above.

```sh
.venv/bin/python -B scripts/install_gui.py \
  --output "$PWD/.runs/launcher-checked-move" \
  --checked-move-editor "/absolute/path/to/isolated/KiCad.app"
```

Open **Launch Autorouter.command**, open PCB Editor for its disposable
example, then select J1 or J2 and click the Copperpath toolbar icon. Widen
the editor if the green trace icon is outside the visible toolbar. The
companion shows the current selection and lets you preview, check and
explicitly apply one move. Use KiCad **Edit → Undo Copperpath checked
component move**, then **Verify KiCad Undo** in Copperpath. Use **Open Saved
Project.command** for your own boards. This checked example runs in a
separate companion window. The ordinary launcher and toolbar passed the
move and Undo test on the isolated Mac setup.
[Current installed result](../evidence/product-workspace-live-toolbar-2427-001.json) · [Editor scope](live-editor-milestone.md#checked-move-on-1008)

**Open saved-project workspace…** carries the current example's saved path
into the ordinary controls. Save and close the editors and then close the
project in KiCad before inspection. Copperpath leaves that choice to you.

Installation copies only the declared immutable payload and matching local JAR. It preserves the original lock/source provenance and writes a new root-bound manifest. Unsafe links, changed/missing/extra payload, stale pins and existing destinations refuse. Failed partial output is retained; use a fresh destination. A successful copy/doctor is preparation, not qualification of that new root or machine.

## Current artifact-import qualification boundary

The source batch includes two bounded options alongside `--install-existing`:

- `--import-artifact` verifies a transported artifact using the exact original manifest SHA256, while treating its old root/host locations as provenance. It does not permit ordinary execution at an unbound location or bypass payload checks.
- `--host-paths-json` supplies all four canonical locations: `kicad_cli`, `kicad_python`, `pcbnew` and `java`. It changes locations only, preserving the known profile, role hashes/sizes and common KiCad app layout. New live bindings must pass alias, executable-role and actual-byte checks.
- For a compatible artifact, use `--kicad-app "/absolute/path/to/KiCad.app"`
  and `--java-executable "/absolute/path/to/bin/java"` in place of
  `--host-paths-json`. Supply both flags together with `--install-existing`
  and `--import-artifact`. Setup resolves the canonical KiCad roles within
  that app and checks the exact pinned bytes. The same-Mac trial passed fresh
  setup and Finder app launch. A wrong executable refused before the new
  installation was created. [Observed setup](../evidence/product-findings-host-intake-001.json)

[One actual097 moved-artifact import](../evidence/product097-artifact-installation-001.json) now passes on the same Mac, with strict root refusal before import, schema3 binding, a fresh no-pip environment and isolated-Python doctor. This tests artifact movement/new installation root with the existing dependency locations. External tool relocation, another OS/account/machine, Native board delivery and actual097GUI remain unqualified. Rebinding requires a new compatible product build. Immutable runtime096 cannot gain that support by changing its manifest; it retains its existing dependency locations. The newer102candidate has its own installed/live-task evidence; this does not relabel097relocation evidence as a current independent installation. No turnkey installer, standalone package, independent-machine or Windows support is claimed.

## Advanced: ordinary routing CLI

Use absolute paths for your saved project, persistent settings and fresh outputs. These are the same guarded operations as ordinary controls:

```sh
.venv/bin/python -B -m autorouter settings-init --output /path/to/new-settings.json
.venv/bin/python -B -m autorouter preview /path/to/project.kicad_pcb --settings /path/to/new-settings.json
.venv/bin/python -B -m autorouter route /path/to/project.kicad_pcb \
  --settings /path/to/new-settings.json --output /path/to/new-route-job
.venv/bin/python -B -m autorouter check-result /path/to/new-route-job/result.json
```

Run each only after its predecessor succeeds. Save and close source editors first. For Finish gaps, choose `--scope partial` and add `--gap-inspection-output /path/to/new-source-check` to Preview. Inspect `gap_plan` for the verified target nets or source blockers. With a `ready` plan, pass its `binding_sha256` as `--expected-gap-plan` to Route with the same scope. Route checks the current source again before dispatch. The regular preview checks static support. Routing acceptance, explicit review and fresh export retain their own requirements. See [routing preferences](routing-preferences.md) and [the structured interface](structured-interface.md). Ctrl-C requests cancellation and retains unaccepted work.

Same-Mac qualification, whole-project DRC cleanliness and electrical/physical review remain distinct. The opened101GUI124export correctly became stale after a KiCad backup/file-set change;102’s live-task export is retained unopened/current. After opening or editing, save further edits as a separate complete working project, choose it as a new source task and revalidate. Full current recovery/off-Mac protection and formal release remain open. [Current requirements](../REQUIREMENTS.md).
