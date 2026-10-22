# Install the runtime059 artifact into a fresh same-Mac folder

The checkout's `scripts/prepare_runtime.py --install-existing` copies a still-bound verified artifact without rebuilding. Current source is runtime059, source `50f63338a67cdbdb81e0392fff7dda5dceaf5b4d`, original manifest `3cb071002cdcba008801545bf0813e20118f142a98aa6bda84af32d0668604dc`. Full2112609tests/1skip and [twelve original-root Native workflows/three invalid controls](../evidence/runtime059-native-milestone-001.json) pass with canonical-receipt/40s return repairs. [GUI094 assigned core observations are closed](../evidence/gui-runtime059-094-observations-001.json) on that original root. **Fresh installation059 is pending; these instructions are not a completed059 install qualification.** FullGUI, independent installation, cleanOS and standalone remain unqualified; keep the Native lane idle before a new job.

The installer preserves the validated54-file census, build-source/version/lock hashes and engine, changing only the manifest's absolute root. The new manifest has a different hash. Old `.runs`, jobs, settings, venvs and launchers are excluded. No dependency is downloaded or relocated.

Use an unused owned destination with an existing real parent; do not reuse partial output:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  NEW_RUNTIME='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 059 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-059/runtime' \
    --expected-manifest-sha256 3cb071002cdcba008801545bf0813e20118f142a98aa6bda84af32d0668604dc \
    --output "$NEW_RUNTIME"
  .venv/bin/python -B -m venv --copies --without-pip "$NEW_RUNTIME/.venv"
  cd "$NEW_RUNTIME"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. **Enter the new runtime before `-m autorouter`**: an absolute interpreter alone can import checkout code from the current directory. Keep the new manifest and process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and collisions refuse. Failure retains partial output. `.runs/install-existing-runtime-001.json` may survive a late refusal; it is a non-authoritative installation record, never Native acceptance.

The historical tested058 fresh root is `.runs/runtime058 fresh install 001`, manifest `19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2`. [Its CLI packet](../evidence/runtime058-install-existing-001.json) records copied Python3.11.9/privateHOME-TMP/minimalPATH doctor/query and ordinary/high partial90 deliveries0/0/0/0/protected4, with two ignored checks. Complete default29.15wall/26.17CPU and high28.59/26.03 are separate from copy.48/.33, venv2.26/2.00 and preparation1.68/1.31. These observations do not qualify059. Doctor/launcher generation alone is not board or GUI qualification.

Historical058 GUI093 completes toolbar/settings, Edge F+B review, acknowledgement/Accept, fresh Native export, checked PCB0unrouted and close without save. Source/PCB remain unchanged; editor PRO/PRL/newZIP changes stale live export proof. Its immutable preopen snapshot remains the historical authority; no renewed validity follows after opening. [The observation packet](../evidence/gui-runtime058-install093-observations-002.json) contains journals/hash manifests, not every local Native proof byte or their full backup. Other root/method/version combinations do not transfer automatically.

The original059 GUI094 session closed its assigned ordinary/high/Improve delivery and refusal observations; it is not a fresh-root059 proof. Its Medium help defect still displays25s despite actual40s reserve, with [checkout patch applied; artifact pending](../.runs/gui-reserve-help-fix-draft-001.patch). Cancel hit validation after Javaexit0, not active-engine interruption. Native/preopen proofs stay local; the public journal packet is metadata only. A new install gets its own launcher from the command above. Do not copy/move old launchers or alter Chrome/default settings; Edge overrides apply only to the launcher child. [GUI steps](gui-workflow.md).

[Historical057 installation](../evidence/runtime057-install-existing-001.json) and [GUI091](../evidence/gui-runtime057-install091-delivery-001.json), [050 installation](../evidence/runtime050-install-existing-001.json)/[GUI087](../evidence/gui-runtime050-install087-delivery-001.json) and [042 vertical slice](../evidence/runtime042-install-existing-001.json) retain their original scope. They do not qualify059. Immutable058 also retains its [archived-reader High](../evidence/runtime058-archived-receipt-defect-001.json) and [25s-return failure](../evidence/runtime058-natural-expiry-001.json); the059 repairs do not alter it. [Previous guide](history/2026-10-20-pre-runtime050-user-guides/install-existing.md) remains unchanged.

Same Mac/account/basePython/external KiCad/Java paths are required. CleanOS/account, dependency relocation, independent-user, standalone, Windows, fullGUI/exact queued timing and human/physical/electrical gates remain open. Windows011 policy attempts closed after [owner1307](../evidence/windows011-lifetime-actual002.json) and [finalC4389 compile failure](../evidence/windows011-policy-attempt002-compile-failure-001.json); [build004](../evidence/windows011-build004-actual001.json) passes only the corrected compile/NULL ABI, not actual owner/policy/network/Native isolation. No third policy attempt or weakened guards. [Selected059](../evidence/backups/selected-runtime059-current-001.json) captures/restores mapped Native/GUI094 bytes onMac only; later ArcDice/progress work and omitted history remain outside it; [full restoration remains capacity-blocked](../evidence/backups/runtime041-receipt-capacity-001.json). No formal package is published. [CLI](quickstart.md) · [Status](../STATUS.md).
