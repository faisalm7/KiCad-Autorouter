# Installation and advanced CLI

**Use an existing installation and launcher when available.** [Start here](../START_HERE.md) and the [saved-project workflow](quickstart.md) use your project, not a prepared demonstration session. Reinstallation is unnecessary merely to resume.

The installed saved-project and review reference is **runtime104** from source `53cb267606cb7db64528c59c2e084db793234d47` with manifest `ae1a3fb439ea32c67b947d2f42a8a6311c25c6b7547adadeccd76f485e8c4123`. Same-Mac setup, direct inspection and the toolbar-to-export workflow passed. Runtime103 remains the ordinary placement-to-delivery reference. The live copilot task remains documented on runtime102. Standalone and independent-machine installation are open. [104 workflow](../evidence/product104-usability-delivery-001.json) · [103 placement](../evidence/product103-GUI126-ordinary-delivery-001.json) · [102 copilot](../evidence/copilot102-owned-live-delivery-001.json).

The tested setup uses macOS 27.0.1 arm64, isolated official KiCad 10.0.7, Java 25.0.2, Freerouting 2.5.0, a no-pip Python 3.11.9 environment and KiCad's bundled Python 3.9.13/wx for the GUI. Exact dependency bytes and locations are pinned. A new environment still depends on its base Python/standard library; `--copies` does not bundle Python. Nothing here downloads or installs dependencies, changes global KiCad, or qualifies Windows Native support.

## Advanced: install a verified artifact at a fresh local root

Use the reviewed source checkout's `scripts/prepare_runtime.py`; the curated runtime does not ship that installer. Choose a verified source artifact and an unused owned destination below an existing real directory. Check available space against the operation's peak allocation plus the fixed 3 GiB reserve. Do not copy an old environment, jobs, settings or launcher to simulate a new installation.

The following is a command template, not a command executed or newly qualified by this guide. Replace the two artifact/destination paths deliberately. Run from the source checkout with an existing supported Python 3.11, and stop after any refusal:

```sh
(
set -eu
AUTOROUTER_ARTIFACT="/path/to/verified runtime104"
AUTOROUTER_INSTALL="/path/to/new owned installation"
python3.11 -B scripts/prepare_runtime.py --install-existing \
  --source "$AUTOROUTER_ARTIFACT" \
  --expected-manifest-sha256 ae1a3fb439ea32c67b947d2f42a8a6311c25c6b7547adadeccd76f485e8c4123 \
  --output "$AUTOROUTER_INSTALL"
python3.11 -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
cd "$AUTOROUTER_INSTALL"
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/launcher-user001"
)
```

Enter the selected runtime before every `-m autorouter` command: using its interpreter from another checkout can import the wrong code. Follow the new launcher's README. It binds the runtime, tools and isolated configuration/documents/cache/plugin area. Keep those locations intact; a moved or replaced launcher needs fresh preparation. The launcher is a cooperative boundary, not an OS sandbox.

Before inspecting or routing, save and close the source PCB/schematic editors, then choose **File → Close Project** in KiCad manager. Closing only the editor windows leaves the project open. Existing launcher copies may omit this instruction; keep their bound files unchanged and follow this step here.

## Saved-project launcher and optional toolbar handoff

Launchers prepared by the saved-project update include **Open Saved Project.command**. It opens Copperpath. Choose the `.kicad_pro` file while that project is closed. Keep its matching PCB, schematic and rules together. The direct launcher uses the existing runtime, with no extra Python packages.

Fresh preparation provisions an empty private job directory for inspection
and validation. Installing an existing artifact preserves its checked program
files and starts with a fresh private job directory. Past job contents stay
with the original installation.

For local placement suggestions, inspect the project in the workspace and
open **Request**. Earlier launchers start in routing. In those builds choose
**Place components** to reach the placement workspace.
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

Installation copies only the declared immutable payload and matching local JAR. It preserves the original lock/source provenance and writes a new root-bound manifest. Unsafe links, changed/missing/extra payload, stale pins and existing destinations refuse. Failed partial output is retained; use a fresh destination. A successful copy/doctor is preparation, not qualification of that new root or machine.

## Current artifact-import qualification boundary

The source batch includes two bounded options alongside `--install-existing`:

- `--import-artifact` verifies a transported artifact using the exact original manifest SHA256, while treating its old root/host locations as provenance. It does not permit ordinary execution at an unbound location or bypass payload checks.
- `--host-paths-json` supplies all four canonical locations: `kicad_cli`, `kicad_python`, `pcbnew` and `java`. It changes locations only, preserving the known profile, role hashes/sizes and common KiCad app layout. New live bindings must pass alias, executable-role and actual-byte checks.

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

Run each only after its predecessor succeeds. Save and close source editors first. A preview is static support; only current canonical proof can support routing acceptance. Review, explicit choice and fresh export remain separate; see [routing preferences](routing-preferences.md) and [the structured interface](structured-interface.md) for advanced settings. Ctrl-C requests cancellation and retains unaccepted work. Never edit receipts or relax original rules to obtain a pass.

Same-Mac qualification, whole-project DRC cleanliness and electrical/physical review remain distinct. The opened101GUI124export correctly became stale after a KiCad backup/file-set change;102’s live-task export is retained unopened/current. After opening or editing, save further edits as a separate complete working project, choose it as a new source task and revalidate. Full current recovery/off-Mac protection and formal release remain open. [Current requirements](../REQUIREMENTS.md).
