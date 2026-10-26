# Install the runtime066 artifact into a fresh same-Mac folder

The existing installation at `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime066 fresh install 001'` has manifest `12f888f072dfaf1e7a612c9d2b7b392d1777090bb75af50a005d4be54a97ac64`, source `8da6896f18432419c81caa28da03510de190b2c7`. Its [native13/invalid/class milestone](../evidence/runtime066-installed-native-milestone-001.json) passes; its separate large rendered delivery failed (see that packet). [Finite actual GUI099 controls](../evidence/gui-runtime066-099-qualification-001.json) also pass on this installed artifact; every phase/exact queued timing remain unqualified.

The installer copies an existing verified artifact, preserving54 immutable files, build/version/lock identities and engine, changing only the declared root. Old jobs, settings, venvs and launchers are excluded. It downloads or relocates no dependency and makes no global installation change.

For another installation, choose an unused owned destination with an existing real parent:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  AUTOROUTER_INSTALL='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 066 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-066/runtime' \
    --expected-manifest-sha256 300dc2762d8418df2c47293cb1c4e530a91c229eb243c0d4d4242768b81e23a2 \
    --output "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
  cd "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. Enter the new runtime before `-m autorouter`. Preserve its manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and destination collisions refuse. Failure preserves partial output; never reuse it. The installation receipt is descriptive and cannot authorize Native acceptance. Another root needs its own qualification.

Current066 testing uses the same Mac/account, copied no-pip Python3.11.9, private HOME/TMP and minimal PATH, with existing pinned external KiCad10.0.7 and Java dependencies. GUI imports use the exact selected KiCad Python3.9.13/wx. This is neither standalone packaging nor a cleanOS, relocated-dependency or independent-user test. No global KiCad or browser setting was changed.

The prepared current launcher is `'.runs/runtime066 fresh install 001/.runs/gui-launcher099/Launch Autorouter.command'`. Use it only with its bound runtime. A new root requires its own launcher. [Start here](../START_HERE.md) explains the child-only Microsoft Edge setting; leave personal/default-browser settings unchanged.

Every candidate retains actual Native refill/full schematic/original-rule, immutable/protected, class/field and PRL proofs. Installation costs and Native costs are distinct in the milestone packet; nested stage/trial samples are not added again. Every-phase/exact queued timing, Windows native, independent installation, full restoration, broader completion/confirmation, human cleanup and physical/electrical gates remain open. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
