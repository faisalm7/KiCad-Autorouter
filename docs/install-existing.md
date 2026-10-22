# Install the runtime060 artifact into a fresh same-Mac folder

The checkout's `scripts/prepare_runtime.py --install-existing` copies a still-bound verified artifact without rebuilding. Current060 source is `972b395878b734ccf47c7691d66435c42c032634`, original manifest `bb703d58271947e15430dc62187ace0afb1a5c70e3e76fe861933e717aa3becd`. The already tested root `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001'` has manifest `8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30`. [Full2122615tests/1skip,13 installed Native workflows/3 invalid controls](../evidence/runtime060-installed-native-milestone-001.json) and [GUI095 assigned core observations](../evidence/gui-runtime060-095-observations-001.json) are closed there. This is same-Mac/account/basePython/external-dependency evidence; fullGUI, independent installation and cleanOS remain unqualified.

The installer preserves the validated54-file census, build source/version/lock hashes and engine, changing only the manifest's absolute root. The new hash must be recorded. Old `.runs`, jobs, settings, venvs and launchers are excluded. No dependency is downloaded or relocated.

To make another installation, choose an unused owned destination with a real existing parent; never reuse partial output:

```sh
(
  set -eu
  cd '/Users/faisal/Projects/KiCad-Autorouter-local'
  NEW_RUNTIME='/Users/faisal/Projects/KiCad-Autorouter-local/.runs/Autorouter 060 user install 001'
  .venv/bin/python -B scripts/prepare_runtime.py --install-existing \
    --source '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-060/runtime' \
    --expected-manifest-sha256 bb703d58271947e15430dc62187ace0afb1a5c70e3e76fe861933e717aa3becd \
    --output "$NEW_RUNTIME"
  .venv/bin/python -B -m venv --copies --without-pip "$NEW_RUNTIME/.venv"
  cd "$NEW_RUNTIME"
  .venv/bin/python -B -m autorouter doctor
  .venv/bin/python -B scripts/install_gui.py --output "$PWD/.runs/gui-launcher-user001"
)
```

Run the installer from the checkout; it is not included in the curated runtime. **Enter the new runtime before `-m autorouter`** to avoid importing checkout code. Keep its manifest/process records. Changed/missing/extra files, symlinks/hardlinks, stale pins, moved sources and collisions refuse. Failure retains partial output; `.runs/install-existing-runtime-001.json` may survive late refusal and is descriptive, never Native acceptance. A further root needs its own qualification; the completed060 evidence is not a pass for any arbitrary destination.

Current installed060 doctor/privateHOME-TMP/minimalPATH/copied no-pip3.11.9 precede all13 CLI deliveries. Source preservation, refill/fullSCH/original/field/class/PRL/default/protected proofs and three invalid controls remain per-candidate. GUI095 ordinary/high/Improve roles retain4/4/1protected, Improve six warnings and all roles two ignored checks. Actual toolbar/settings, Edge F+B review/acknowledged Accept/fresh export/checked PCB0unrouted and close without save are observed. Editor-changed PRO/PRL/ZIP makes the live export stale; preopen proof does not renew it.

Use the existing `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001/.runs/gui-launcher095/Launch Autorouter.command'` only with its bound runtime. A new installation gets its own launcher from the command above. Never copy/move an old launcher or change Chrome/default-browser settings; use the child-only Edge override or manually open HTML in Edge. [GUI steps](gui-workflow.md).

Current installation costs are separate: copy0.48wall/0.33CPU, copied venv0.15/0.13, freeze/query/doctor3.41/2.68 and13-case batch757.17/722.95; Native invalids7.63/5.87 are additional. Stage/trial samples are nested, not added. GUI preparation16.96/16.66 and interactive manager2256.52wall/239reportedCPU overlap children and include pauses; reported manager CPU is not all-process CPU. Authoring/AI/other overhead is partly unknown, notzero. [Exact accounting](../evidence/runtime060-installed-native-milestone-001.json).

Historical [059 original-root Native](../evidence/runtime059-native-milestone-001.json)/[GUI094](../evidence/gui-runtime059-094-observations-001.json), [058 installed CLI](../evidence/runtime058-install-existing-001.json)/[GUI093](../evidence/gui-runtime058-install093-observations-002.json), [057 CLI](../evidence/runtime057-install-existing-001.json)/[GUI091](../evidence/gui-runtime057-install091-delivery-001.json) and [previous guide](history/2026-10-20-pre-runtime050-user-guides/install-existing.md) remain unchanged and version-specific.

CleanOS/account, dependency relocation, independent-user, standalone, fullGUI/exact queued timing and human/physical/electrical gates remain open. [Windows012](../evidence/windows012-policy-actual001.json) closed after compile/load/14NULL controls then WinError13, with no Native/token/denial/cancel case; no retry/installer. [Selected060](../evidence/backups/selected-runtime060-current-001.json) preserves its mapped raw cutoff onMac; actual012 CI/later comparison bytes are outside it. Full restoration remains [capacity-blocked](../evidence/backups/runtime041-receipt-capacity-001.json), with no disk-failure protection or formal package publication. [CLI](quickstart.md) · [Installation limits](install-test.md).
