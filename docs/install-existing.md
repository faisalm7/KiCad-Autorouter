# Install runtime058 into a fresh same-Mac folder

The checkout's `scripts/prepare_runtime.py --install-existing` copies a still-bound verified artifact without rebuilding. Current source is runtime058, source `8f5e96b88dd22cd25919bb71ce47711612994efa`, original manifest `4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74`. [Original-root Native workflows](../evidence/runtime058-native-milestone-001.json), [two actual installed CLI slices](../evidence/runtime058-install-existing-001.json) and [one installed GUI093 slice](../evidence/gui-runtime058-install093-observations-002.json) have separate evidence. FullGUI, independent installation, cleanOS and standalone remain unqualified.

The installer preserves the validated54-file census, build-source/version/lock hashes and engine, changing only the manifest's absolute root. The new manifest has a different hash. Old `.runs`, jobs, settings, venvs and launchers are excluded. No dependency is downloaded or relocated.

Use an unused owned destination with an existing real parent; do not reuse partial output:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  NEW_RUNTIME='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 058 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-058/runtime' \
    --expected-manifest-sha256 4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74 \
    --output "$NEW_RUNTIME"
  .venv/bin/python -B -m venv --copies --without-pip "$NEW_RUNTIME/.venv"
  cd "$NEW_RUNTIME"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. **Enter the new runtime before `-m autorouter`**: an absolute interpreter alone can import checkout code from the current directory. Keep the new manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and collisions refuse. Failure retains partial output. `.runs/install-existing-runtime-001.json` may survive a late refusal; it is a non-authoritative installation record, never Native acceptance.

The actual tested fresh root is `.runs/runtime058 fresh install 001`, manifest `19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2`. Copied Python3.11.9/privateHOME-TMP/minimalPATH doctor/query and both ordinary/high partial90 CLI slices deliver0/0/0/0, preserve4routes and retain two ignored checks. Complete default29.15wall/26.17CPU and high28.59/26.03 are separate from copy.48/.33, venv2.26/2.00 and preparation1.68/1.31. Doctor/launcher generation alone is not board or GUI qualification.

Actual GUI093 then completes toolbar/settings, Edge F+B review, acknowledgement/Accept, fresh Native export, checked PCB0unrouted and close without save. Source/PCB remain unchanged; editor PRO/PRL/newZIP changes stale live export proof. Its immutable preopen snapshot remains the historical authority; no renewed validity follows after opening. [The observation packet](../evidence/gui-runtime058-install093-observations-002.json) contains journals/hash manifests, not every local Native proof byte or their full backup. Other root/method combinations do not transfer automatically.

Use the existing launcher at `/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime058 fresh install 001/.runs/gui-launcher093/Launch Autorouter.command` with the child-only Edge override in [GUI steps](gui-workflow.md), or open review HTML manually in Edge. Do not copy/move old launchers or alter Chrome/default settings.

[Historical057 installation](../evidence/runtime057-install-existing-001.json) and [GUI091](../evidence/gui-runtime057-install091-delivery-001.json), [050 installation](../evidence/runtime050-install-existing-001.json)/[GUI087](../evidence/gui-runtime050-install087-delivery-001.json) and [042 vertical slice](../evidence/runtime042-install-existing-001.json) retain their original scope. They do not qualify058. [Previous guide](history/2026-10-20-pre-runtime050-user-guides/install-existing.md) remains unchanged.

Same Mac/account/basePython/external KiCad/Java paths are required. CleanOS/account, dependency relocation, independent-user, standalone, Windows, fullGUI/exact queued timing and human/physical/electrical gates remain open. Windows011's finite isolation blocker is closed with failures, not support. New raw stays Mac-only/outside010; [full restoration remains capacity-blocked](../evidence/backups/runtime041-receipt-capacity-001.json). No formal package is published. [CLI](quickstart.md) · [Status](../STATUS.md).
