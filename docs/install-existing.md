# Install runtime057 into a fresh same-Mac folder

The checkout’s `scripts/prepare_runtime.py --install-existing` copies a still-bound verified artifact without rebuilding it. Current source artifact is runtime057, source `ac1a48c3b25b2217e0f8252e0e6da21905f144a4`, manifest `9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e`. Its [eleven CLI workflows](../evidence/runtime057-native-milestone-001.json) belong to the original root. [Fresh-folder installation](../evidence/runtime057-install-existing-001.json) passes default/high partial2Cu Native CLI delivery, and [one actual new-root GUI091 slice](../evidence/gui-runtime057-install091-delivery-001.json) completes ordinary partial90 through checked opening and close. These do not qualify every original-root combination, fullGUI, cleanOS or standalone operation.

The installer preserves the exact validated immutable-file census, build-source/version/lock hashes and local engine, changing only the manifest’s absolute root. The resulting manifest gets a different hash. Old `.runs`, jobs, settings, virtual environments and launchers are excluded. No dependency is downloaded or relocated.

Use a fresh owned destination whose parent already exists. The example below stops on failure inside a subshell. Replace the destination with an unused path; do not reuse a partial installation:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  NEW_RUNTIME='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 057 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-057/runtime' \
    --expected-manifest-sha256 9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e \
    --output "$NEW_RUNTIME"
  .venv/bin/python -B -m venv --copies --without-pip "$NEW_RUNTIME/.venv"
  cd "$NEW_RUNTIME"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not part of the curated runtime. After creating the copied Python environment, **change into the new runtime before `-m autorouter`**. An absolute interpreter alone does not prevent importing checkout code from the current directory. Keep the returned new-root manifest hash and installer/process records for qualification.

Changed/missing/extra immutable files, symlinks/hardlinks, wrong pins, an already moved source and existing destinations refuse. Source, installer, destination and record are rechecked before a successful return. Failure preserves partial output. `.runs/install-existing-runtime-001.json` may remain after a late refusal: it is a **non-authoritative installation record**, not an acceptance, completion or Native-qualification marker.

Doctor and launcher generation alone do not qualify routing or GUI. Actual057 installation at `.runs/runtime057 fresh install 001` has manifest `b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51`, unchanged54immutable files/build/source/engine and copied Python3.11.9. Private HOME/TMP/minimalPATH doctor plus both90s partial2Cu CLI cases preserve4routes and deliver0/0/0/0 through their own original-rule/refill/fullSCH/export proofs; two ignored checks remain. Complete default27.52wall/24.37CPU and high27.98/24.70; copy.34/.26, venv2.11/1.81 and preparation/query/doctor1.33/1.18 are separate. Actual GUI091 then completed Edge F+B/ackAccept/fresh export/check/checked PCB0unrouted/close without save; source/PCB unchanged, editor PRO/PRL/newZIP changes caused stale refusal. Preopen proof is retained; no validity renewed after opening. Its planned post-reader metadata control aborted before mutation, GUI resumed, no exact queued timing pass; STOP method stays stopped. This is one same-Mac GUI installation slice, not fullGUI or all combinations.

The [historical050 installation test](../evidence/runtime050-install-existing-001.json) and [actual GUI087 vertical slice](../evidence/gui-runtime050-install087-delivery-001.json) retain their own scope. GUI087 completed toolbar/settings, protected partial routing, rendered Edge review, acceptance, fresh Native export and checked opening; subsequent editor metadata changes refused old proof. Historical GUI087 does not transfer qualification to another build. Do not repeat completed CLI work or copy an old launcher. Use the new launcher README. For Edge, launch that command with a child-only `BROWSER='/usr/bin/open -a "Microsoft Edge" %s'` override, or open `review/preview.html` manually in Edge. Leave Chrome/default settings unchanged.

The [historical042 fresh-root vertical slice](../evidence/runtime042-install-existing-001.json) qualified its own ordinary Native/GUI path on this Mac. It remains historical evidence, not proof for another root or all GUI roles. Current057 graphical scope is limited to the published090 roles and091 slice; historical050 [active-Java cancellation](../evidence/gui-runtime050-086-active-engine-cancel-001.json) and the separate [negative, deferred escape probe](../evidence/qfn-escape-development-probe-002.json) retain their own scopes.

Existing pinned KiCad10.0.7/Java/Python locations on the same Mac remain required. This does not establish standalone, cleanOS/account, relocated dependencies, Windows, fullGUI, general quality, independent human or physical/electrical qualification. No package is published. Sources and candidates stay separate; explicit review choice and fresh original-rule export checks remain mandatory. [CLI](quickstart.md) · [GUI](gui-workflow.md) · [Current status](../STATUS.md). [Previous guide preserved unchanged](history/2026-10-20-pre-runtime050-user-guides/install-existing.md).
