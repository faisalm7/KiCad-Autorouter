# Install the runtime065 artifact into a fresh same-Mac folder

The existing installation at `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime065 fresh install 001'` has manifest `e881abd82a06a30828999b55e6c9301ea845f1d6e8b252d36751efe6b21d38fa`, source `4ed438a14f89e684bfdf9211039b02ee35cc8853`. Its [native13/invalid/class milestone](../evidence/runtime065-installed-native-milestone-001.json) and [fixed delivery regression](../evidence/runtime065-single-delivery-001.json) pass. [Finite actual GUI098 controls](../evidence/gui-runtime065-098-qualification-001.json) also pass on this installed artifact; every phase/exact queued timing remain unqualified.

The installer copies an existing verified artifact, preserving54 immutable files, build/version/lock identities and engine, changing only the declared root. Old jobs, settings, venvs and launchers are excluded. It downloads or relocates no dependency and makes no global installation change.

For another installation, choose an unused owned destination with an existing real parent:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  AUTOROUTER_INSTALL='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 065 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-065/runtime' \
    --expected-manifest-sha256 5919a204157c9a8e65acfac9b9479c1b9ec497caea00cc0aa3d86fc660b52741 \
    --output "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
  cd "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. Enter the new runtime before `-m autorouter`. Preserve its manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and destination collisions refuse. Failure preserves partial output; never reuse it. The installation receipt is descriptive and cannot authorize Native acceptance. Another root needs its own qualification.

Current065 testing uses the same Mac/account, copied no-pip Python3.11.9, private HOME/TMP and minimal PATH, with existing pinned external KiCad10.0.7 and Java dependencies. GUI imports use the exact selected KiCad Python3.9.13/wx. This is neither standalone packaging nor a cleanOS, relocated-dependency or independent-user test. No global KiCad or browser setting was changed.

The prepared current launcher is `'.runs/runtime065 fresh install 001/.runs/gui-launcher098/Launch Autorouter.command'`. Use it only with its bound runtime. A new root requires its own launcher. [Start here](../START_HERE.md) explains the child-only Microsoft Edge setting; leave personal/default-browser settings unchanged.

Every candidate retains actual Native refill/full schematic/original-rule, immutable/protected, class/field and PRL proofs. Installation costs and Native costs are distinct in the milestone packet; nested stage/trial samples are not added again. Actual four-layer GUI/every-phase/exact queued timing, Windows native, independent installation, full restoration, broader completion/confirmation, human cleanup and physical/electrical gates remain open. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
