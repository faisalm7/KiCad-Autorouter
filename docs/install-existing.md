# Install the runtime074 artifact into a fresh same Mac folder

The current installation is `'.runs/runtime074 fresh install 001'`, manifest `584ee929eaf3d277dc535556e42c71ac5196a74f1c5e3fd53a2cce5a67853d61`, source `6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194`. Its [fixed headless milestone](../evidence/runtime074-installed-native-milestone-001.json), [finite GUI105 core](../evidence/gui-runtime074-105-core-001.json) and [one large CLI delivery](../evidence/runtime074-large-delivery-qualified-001.json) pass their recorded gates. The genuine updated-warning dialog and exact queued-open interval remain unexercised; full GUI qualification is open. These results belong to this exact installed root.

The installer copies an existing verified artifact, preserving 54 immutable files, build/version/lock identities and engine, changing only the declared root. Old jobs, settings, venvs and launchers are excluded. It downloads or relocates no dependency and makes no global installation change.

From this checkout, for another installation choose an unused owned destination with an existing real parent:

```sh
(
  set -eu
  AUTOROUTER_PROJECT="$PWD"
  AUTOROUTER_INSTALL="$AUTOROUTER_PROJECT/.runs/Autorouter 074 user install 001"
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source "$AUTOROUTER_PROJECT/.runs/runtime-directory-074/runtime" \
    --expected-manifest-sha256 b4e77cc905dd4e068f9e57476e17211f319d068034fdef4ea77be952dd13d90f \
    --output "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m venv --copies --without-pip "$AUTOROUTER_INSTALL/.venv"
  cd "$AUTOROUTER_INSTALL"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. Enter the new runtime before `-m autorouter`. Preserve its manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and destination collisions refuse. Failure preserves partial output; never reuse it. The installation receipt is descriptive and cannot authorize Native acceptance. Another root needs its own qualification.

Current074 testing uses the same Mac/account, copied no-pip Python 3.11.9, private HOME/TMP and minimal PATH, with existing pinned external KiCad 10.0.7 and Java dependencies. GUI imports use the exact selected KiCad Python 3.9.13/wx. This is neither standalone packaging nor a cleanOS, relocated-dependency or independent-user test. The installer makes no explicit global KiCad or browser setting changes. Prior normal-profile startup writes were unmeasured.

For the tested current root, use the GUI105 Edge wrapper in [Start here](../START_HERE.md). It starts the unchanged bound launcher at `'.runs/runtime074 fresh install 001/.runs/gui-launcher105/Launch Autorouter.command'` with the Microsoft Edge setting confined to that process. Leave personal/default-browser settings unchanged. A new root requires its own launcher and qualification; the old GUI jobs and evidence do not transfer.

Every candidate retains actual Native refill/full schematic/original-rule, immutable/protected, class/field and PRL proofs. Installation costs and Native costs are distinct in the milestone packet; nested stage/trial samples are not added again. The [latest 3,314-file evidence subset](../evidence/backups/selected-runtime074-gui105-delivery-001.json) restored exactly and its own temporary copy was retired; this is not full current restoration or environment recovery. Genuine updated-warning GUI interaction, every-phase/exact queued timing, Windows native, independent installation, broader completion/confirmation, human cleanup and physical/electrical gates remain open. [Platform matrix](supported-platforms.md) · [Requirements](../REQUIREMENTS.md).
