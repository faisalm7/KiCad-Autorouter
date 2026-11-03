# Install the runtime073 artifact into a fresh same Mac folder

The current installation is `'.runs/runtime073 fresh install 001'`, manifest `d12be29349b01dcd9693f4fbb8e6f00faaa285e15bb5a8f0bed84857350aa6b5`, source `346b241e38e172d7a1478f7eeb535288e496d999`. Its [fixed headless milestone](../evidence/runtime073-installed-native-milestone-001.json) passes. GUI104 is prepared and unqualified; older GUI evidence does not transfer.

The installer copies an existing verified artifact, preserving 54 immutable files, build/version/lock identities and engine, changing only the declared root. Old jobs, settings, venvs and launchers are excluded. It downloads or relocates no dependency and makes no global installation change.

For another installation, choose an unused owned destination with an existing real parent:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  AUTOROUTER_INSTALL='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 073 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-073/runtime' \
    --expected-manifest-sha256 3f1723f12b582448efa695de82231f30baefb898da80240092ec38f569204044 \
    --output "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
  cd "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. Enter the new runtime before `-m autorouter`. Preserve its manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and destination collisions refuse. Failure preserves partial output; never reuse it. The installation receipt is descriptive and cannot authorize Native acceptance. Another root needs its own qualification.

Current073 testing uses the same Mac/account, copied no-pip Python 3.11.9, private HOME/TMP and minimal PATH, with existing pinned external KiCad 10.0.7 and Java dependencies. GUI imports use the exact selected KiCad Python 3.9.13/wx. This is neither standalone packaging nor a cleanOS, relocated-dependency or independent-user test. The installer makes no explicit global KiCad or browser setting changes. Prior normal-profile startup writes were unmeasured.

The prepared current launcher is `'.runs/runtime073 fresh install 001/.runs/gui-launcher104/Launch Autorouter.command'`. Use it only with its bound runtime. A new root requires its own launcher. [Start here](../START_HERE.md) explains the child-only Microsoft Edge setting; leave personal/default-browser settings unchanged.

Every candidate retains actual Native refill/full schematic/original-rule, immutable/protected, class/field and PRL proofs. Installation costs and Native costs are distinct in the milestone packet; nested stage/trial samples are not added again. Every-phase/exact queued timing, Windows native, independent installation, full restoration, broader completion/confirmation, human cleanup and physical/electrical gates remain open. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
