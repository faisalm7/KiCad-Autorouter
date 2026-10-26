# Curated local runtime directory

Current **runtime065**, source `4ed438a14f89e684bfdf9211039b02ee35cc8853`, has original manifest `5919a204157c9a8e65acfac9b9479c1b9ec497caea00cc0aa3d86fc660b52741`. Its fresh installed manifest is `e881abd82a06a30828999b55e6c9301ea845f1d6e8b252d36751efe6b21d38fa`;54 immutable files/build source/engine match except the declared root. [Installed Native milestone](../evidence/runtime065-installed-native-milestone-001.json), [fixed delivery](../evidence/runtime065-single-delivery-001.json) and [finite actual GUI098](../evidence/gui-runtime065-098-qualification-001.json) pass. Actual four-layer GUI, exact queued timing, every cancellation phase and independent installation remain open. Runtime066 presentation changes are under development and do not replace this qualified artifact yet.

Use the already tested installed runtime:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime065 fresh install 001'
.venv/bin/python -B -m autorouter doctor
```

Enter this CWD before `-m autorouter`; an absolute interpreter alone can import checkout code from the wrong directory. Immutable code/resources/licences/manifest are separate from mutable `.runs`/`.venv`. Sources stay separate from candidates. Normal jobs need no AI/network/Git/research archive. Documentation changes do not require rebuilding this unchanged artifact.

The existing isolated launcher is `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime065 fresh install 001/.runs/gui-launcher098/Launch Autorouter.command'`; prepared source/preset/jobs are under `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime065 fresh install 001/.runs/gui-session098'`. GUI098 closed normally. Keep the Native lane idle before new work; use the child-only Edge override in [GUI steps](gui-workflow.md), or open review HTML manually in Edge. Leave Chrome/default settings unchanged. Do not move/edit launchers or copy old jobs/venvs to simulate installation.

[Install-existing](install-existing.md) copies a still-bound artifact without rebuilding and excludes old mutable state. Current same-Mac fresh-folder evidence is real; cleanOS/account/dependency relocation/standalone/independent-user axes are not. GUI098 observed protected ordinary/high routing, class Improve with one completed trial, Edge plots/findings, accept/reject, fresh Native export/checked opening, active-Java−9/cleanup/CLI2 and stale-input refusals. Exact queued timing, all-phase cancellation and thermal Recover remain unqualified.

For intentional development builds only, choose a fresh destination from reviewed committed source:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local'
.venv/bin/python -B scripts/prepare_runtime.py --output '/absolute/NEW-runtime' --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip '/absolute/NEW-runtime/.venv'
cd '/absolute/NEW-runtime'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output '/absolute/NEW-runtime/.runs/NEW-launcher'
```

These are build reproduction commands, not instructions to rebuild065. Parents must be real/owned; collisions refuse, and failed partial output remains. A changed build/root requires its own evidence. Doctor proves readiness and launcher generation proves preparation, not board/GUI acceptance.

Nothing downloads. Existing official KiCad10.0.7/macOS arm64, Java25.0.2, Python3.11.9 and Freerouting2.5.0 remain pinned. Copy-local-engine copies the existing matching JAR. Without explicit `--native-version`, build preparation selects historical10.0.0; install-existing preserves selection. Copied interpreters/`-B` avoid immutable bytecode; unexpected files/symlinks refuse.

Historical [059 Native](../evidence/runtime059-native-milestone-001.json)/[GUI094](../evidence/gui-runtime059-094-observations-001.json) and [058 install](../evidence/runtime058-install-existing-001.json)/[GUI093](../evidence/gui-runtime058-install093-observations-002.json) keep their original scope. Immutable058's [archived-reader High](../evidence/runtime058-archived-receipt-defect-001.json)/[return failure](../evidence/runtime058-natural-expiry-001.json) are unchanged. [Selected060](../evidence/backups/selected-runtime060-current-001.json) captures/subset-restores the8411-file mapped Native/GUI/admissions cutoff onMac only; actual012 CI/later comparison work are outside it. Full restoration remains [capacity-blocked](../evidence/backups/runtime041-receipt-capacity-001.json). No release, fullGUI, Windows, human/electrical or full reconstruction claim. [Installation limits](install-test.md) · [Status](../STATUS.md).
