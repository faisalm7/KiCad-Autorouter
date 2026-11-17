# Installation and advanced CLI

**Use an existing installation and launcher when available.** [Start here](../START_HERE.md) and the [saved-project workflow](quickstart.md) use your project, not a prepared demonstration session. Reinstallation is unnecessary merely to resume.

The current experimental candidate is **runtime102**, source `52d0974f9ba82aed5311690243b8b8956729e713`, manifest `18b10dcf99fce0b6b208184b2a8536a3ec7030ce895ab8bb77d913a58ccbc114`. [Installation/full276 and the actual live placement/routing workflow](../evidence/copilot102-owned-live-delivery-001.json) pass on this Mac. [101graphical safety](../evidence/product101-GUI124-core-001.json) applies to unchanged GUI/engineering code; only the hosted client changed. The [094 licensed reference](../evidence/runtime094-GUI118-core-001.json) keeps its own scope. This is not standalone or independent-machine qualification.

The tested setup uses macOS 27.0.1 arm64, isolated official KiCad 10.0.7, Java 25.0.2, Freerouting 2.5.0, a no-pip Python 3.11.9 environment and KiCad's bundled Python 3.9.13/wx for the GUI. Exact dependency bytes and locations are pinned. A new environment still depends on its base Python/standard library; `--copies` does not bundle Python. Nothing here downloads or installs dependencies, changes global KiCad, or qualifies Windows Native support.

## Advanced: install a verified artifact at a fresh local root

Use the reviewed source checkout's `scripts/prepare_runtime.py`; the curated runtime does not ship that installer. Choose a verified source artifact and an unused owned destination below an existing real directory. Check available space against the operation's peak allocation plus the fixed 3 GiB reserve. Do not copy an old environment, jobs, settings or launcher to simulate a new installation.

The following is a command template, not a command executed or newly qualified by this guide. Replace the two artifact/destination paths deliberately. Run from the source checkout with an existing supported Python 3.11, and stop after any refusal:

```sh
(
set -eu
AUTOROUTER_ARTIFACT="/path/to/verified runtime102"
AUTOROUTER_INSTALL="/path/to/new owned installation"
python3.11 -B scripts/prepare_runtime.py --install-existing \
  --source "$AUTOROUTER_ARTIFACT" \
  --expected-manifest-sha256 18b10dcf99fce0b6b208184b2a8536a3ec7030ce895ab8bb77d913a58ccbc114 \
  --output "$AUTOROUTER_INSTALL"
python3.11 -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
cd "$AUTOROUTER_INSTALL"
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/launcher-user001"
)
```

Enter the selected runtime before every `-m autorouter` command: using its interpreter from another checkout can import the wrong code. Follow the new launcher's README. It binds the runtime, tools and isolated configuration/documents/cache/plugin area. Keep those locations intact; a moved or replaced launcher needs fresh preparation. The launcher is a cooperative boundary, not an OS sandbox.

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
