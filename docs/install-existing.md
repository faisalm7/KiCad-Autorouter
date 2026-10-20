# Install runtime056 into a fresh same-Mac folder

The checkout’s `scripts/prepare_runtime.py --install-existing` copies a still-bound, verified artifact without rebuilding it. Current source artifact is runtime056, source `a03b5e8b6ae523d9f099cf211815900053629fe3`, manifest `b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded`. Its [eleven CLI workflows](../evidence/runtime056-native-milestone-001.json) belong to the original root. Current GUI089 and new-root installation remain unqualified; preparation and older installation results do not transfer that authority.

The installer preserves the exact validated immutable-file census, build-source/version/lock hashes and local engine, changing only the manifest’s absolute root. The resulting manifest gets a different hash. Old `.runs`, jobs, settings, virtual environments and launchers are excluded. No dependency is downloaded or relocated.

Use a fresh owned destination whose parent already exists. The example below stops on failure inside a subshell. Replace the destination with an unused path; do not reuse a partial installation:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  NEW_RUNTIME='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 056 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime' \
    --expected-manifest-sha256 b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded \
    --output "$NEW_RUNTIME"
  .venv/bin/python -B -m venv --copies --without-pip "$NEW_RUNTIME/.venv"
  cd "$NEW_RUNTIME"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not part of the curated runtime. After creating the copied Python environment, **change into the new runtime before `-m autorouter`**. An absolute interpreter alone does not prevent importing checkout code from the current directory. Keep the returned new-root manifest hash and installer/process records for qualification.

Changed/missing/extra immutable files, symlinks/hardlinks, wrong pins, an already moved source and existing destinations refuse. Source, installer, destination and record are rechecked before a successful return. Failure preserves partial output. `.runs/install-existing-runtime-001.json` may remain after a late refusal: it is a **non-authoritative installation record**, not an acceptance, completion or Native-qualification marker.

Doctor and launcher generation alone do not qualify routing or GUI. The [historical050 installation test](../evidence/runtime050-install-existing-001.json) passes doctor and all six Native CLI stages on one owned partial2Cu project:0opens/0blocking/0warnings/0exclusions,4protected routes,39.10wall/33.94CPU plus setup1.61/.89. Its new manifest is `8fdf819606e2345b932139f1c16c330825fd8634caef1b611b5e105b97be22a4`. This is one installation axis, not all-combination transfer. [Actual GUI087 vertical slice](../evidence/gui-runtime050-install087-delivery-001.json) now completes toolbar/settings, protected4 partial90 routing, rendered EdgeF+B review, accept, fresh Native export and checked PCB opening0unrouted. Exact pre-editor files are preserved; actual editor metadata changes then refused old proof. This is one ordinary installation path, not allGUI transfer. Do not repeat completed CLI work or reuse launcher086 in the new folder. Use the new launcher README. For Edge, launch that command with a child-only `BROWSER='/usr/bin/open -a "Microsoft Edge" %s'` override, or open `review/preview.html` manually in Edge. Leave Chrome/default settings unchanged.

The [historical042 fresh-root vertical slice](../evidence/runtime042-install-existing-001.json) qualified its own ordinary Native/GUI path on this Mac. It remains historical evidence, not proof for a new056 root or all GUI roles. Current056 GUI is unperformed; historical050 [active-Java cancellation](../evidence/gui-runtime050-086-active-engine-cancel-001.json) and the separate [negative, deferred escape probe](../evidence/qfn-escape-development-probe-002.json) retain their own scopes.

Existing pinned KiCad10.0.7/Java/Python locations on the same Mac remain required. This does not establish standalone, cleanOS/account, relocated dependencies, Windows, fullGUI, general quality, independent human or physical/electrical qualification. No package is published. Sources and candidates stay separate; explicit review choice and fresh original-rule export checks remain mandatory. [CLI](quickstart.md) · [GUI](gui-workflow.md) · [Current status](../STATUS.md). [Previous guide preserved unchanged](history/2026-10-20-pre-runtime050-user-guides/install-existing.md).
