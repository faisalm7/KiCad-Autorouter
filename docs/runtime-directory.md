# Curated local runtime directory

Current candidate **runtime056**, source `a03b5e8b6ae523d9f099cf211815900053629fe3`, manifest `b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded`, contains49Python modules/54immutable files and an existing pinned local engine. [Eleven Native CLI deliveries/invalid controls](../evidence/runtime056-native-milestone-001.json), full206 and [fresh exposed IR Improve delivery](../evidence/runtime056-ir-delivery-002.json) pass. [Fresh-root installation](../evidence/runtime056-install-existing-001.json) additionally passes default and high-cost partial2Cu Native CLI delivery. [GUI089 is prepared only](../evidence/gui-runtime056-089-preparation-001.json); graphical and release qualification remain open.

On this Mac use:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime
```

Enter that directory before invoking `.venv/bin/python -B -m autorouter`. An absolute interpreter path alone can import checkout code from the wrong working directory. Keep the runtime and pinned applications at their recorded paths. Normal jobs need no AI account, Git, network or research archive. Code, necessary resources, licences and the manifest are immutable; `.runs` and `.venv` are mutable and unattested. Original source projects remain separate. Documentation or benchmark-administration changes do not require rebuilding the unchanged runtime.

The prepared056 launcher is `.runs/gui-launcher089/Launch Autorouter.command`, relative to this runtime. Its original-source roles, separate inspection projects,90s presets and jobs are bound by `.runs/gui-session089/prepared-state.json`. The launcher isolates configuration/plugin/cache and refuses observed conflicting KiCad applications without terminating them. Use Microsoft Edge through the per-launch override in the [workflow](gui-workflow.md); do not change Chrome or global settings. Preparation is not GUI proof.

[Install the exact existing artifact into a fresh folder](install-existing.md) instead of rebuilding to change its destination. The installer preserves the immutable census/build source/lock and rebinds only the absolute root; a new manifest and appropriate qualification are required. Do not copy old jobs, launchers or virtual environments. Current fresh root `.runs/runtime056 fresh install 001` has manifest `6416d003b92b522fcb81aeb28bbd4ebe44dbb1a4c53f18dc896fe679f4d8749c`; its two actual partial2Cu CLI slices each preserve4routes and deliver0/0/0/0. GUI and other combinations remain unqualified there. [Historical050 fresh-root CLI](../evidence/runtime050-install-existing-001.json) and [GUI087 ordinary slice](../evidence/gui-runtime050-install087-delivery-001.json) retain their own scope and do not qualify056.

For intentional development builds only, choose a fresh destination from reviewed committed product source:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/NEW-runtime --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip /absolute/NEW-runtime/.venv
cd /absolute/NEW-runtime
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/NEW-runtime/.runs/NEW-launcher
```

These are reproduction commands, not instructions to rebuild056. The destination parent must exist and be a real owned directory. Existing outputs refuse; partial output remains after failure. Required bytes must match committed source. A different source/root needs its own evidence; do not relabel historical receipts. Doctor establishes readiness, not board acceptance, and launcher generation does not qualify GUI behavior.

Nothing downloads. The selected profile uses the existing official KiCad10.0.7 bundle pinned in `toolchain.lock.json`, Java25.0.2, Python3.11.9 base and lock-matching Freerouting2.5.0 JAR. `--copy-local-engine` copies only that existing JAR for local use. Without explicit `--native-version`, preparation uses historical10.0.0 rather than selected10.0.7. Copied interpreters and `-B` avoid extra immutable bytecode; symlinks/extra files refuse.

Same-Mac/account/base-Python and fixed external dependency locations do not establish standalone, cleanOS/account, relocation, Windows or independent-user support. The manifest is a consistency witness, not a signature or protection from hostile same-user rewrites/power loss. Separate review/export candidates never overwrite originals; live apply/undo remains unqualified. [Installation evidence](install-test.md) · [Preferences](routing-preferences.md) · [Status](../STATUS.md) · [Requirements](../REQUIREMENTS.md). Formal release/tag/package publication needs separate approval. Earlier version details remain in immutable evidence and Git history.
