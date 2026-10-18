# Curated local runtime directory

The current candidate is **runtime026**, source `1117de080524072046a61522845facd5d4c68575`, manifest `5371d08ccf5a0ae2e0c4024f752baca28f034c3b3cb50ade308e8e5e12e36fe5`. [Full167](../evidence/gui-budget-text-integration-001.json), fresh copied interpreter/doctor, [whole](../evidence/runtime026-installed-CLI-001.json)/[partial](../evidence/runtime026-installed-partial-CLI-001.json) six-stage CLI and the declared [GUI072 controls](../evidence/gui-runtime026-072-native-controls-001.json) pass within their recorded scopes. Each positive final has its own Native/full-schematic/original/protected proof. Old023 observations do not qualify026.

On this Mac use the existing directory:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-026/runtime
```

Its launcher is `.runs/gui-launcher072/Launch Autorouter.command` inside that runtime. Keep the directory and pinned applications at their recorded paths. Close other KiCad managers/editors before launching; the launcher refuses conflicts and never closes them. It uses isolated settings/plugin/cache, with no global installation or application replacement. [Workflow](gui-workflow.md).

To prepare a distinct directory from this source checkout, choose a new destination and use the explicit selected profile. These commands are a reproduction recipe, not a request to rebuild the already tested026 instance:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/NEW-runtime --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip /absolute/NEW-runtime/.venv
mkdir /absolute/NEW-runtime/.runs
cd /absolute/NEW-runtime
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/NEW-runtime/.runs/NEW-launcher
```

The destination parent must already be a real owned directory. Existing outputs are never overwritten. Selected product files must match committed source; the builder records the actual source HEAD and exact copied population. A different destination/HEAD produces a new manifest and needs its own appropriate qualification; do not relabel old026 receipts. `doctor` checks readiness, not board acceptance. Launcher preparation does not itself prove GUI behavior.

Nothing downloads. The explicit profile uses the already existing isolated official KiCad10.0.7 bundle pinned in `toolchain.lock.json`; Java25.0.2, Python3.11 and the lock-matching Freerouting2.5.0 JAR must already be available. The engine flag copies only that existing JAR for local use. Omitting it leaves routing unavailable until separate authorized dependency preparation. Without `--native-version`, source/default preparation remains10.0.0; it does not recreate026.

The runtime has code, necessary resources, license, manifest and instructions; ordinary jobs need no research archive, corpus, AI account, Git or internet. Only `.runs` and `.venv` are mutable and unattested. Use copied interpreters and `-B`/`PYTHONDONTWRITEBYTECODE=1`; links and extra immutable files such as `__pycache__` refuse strict checks. Keep source projects outside the product population; owned qualification sources under `.runs` have separate identities. Changed product bytes require a new directory.

Current ordinary10.0.7 supports corrected-standard/both Route, whole/partial completion, all source layers/default vias. Improve, selected-net/layer restrictions and other advanced combinations refuse in this profile. Historical10.0.0 qualifications retain their exact scope. This directory is path-bound, not a standalone application, relocatable package or clean-OS installation. [Installation scope](install-test.md), [matrix](experimental-rc.md).

Candidates, review and fresh validated export remain separate from originals. Later edits can stale their proof; no live overwrite or tested undo is offered. The manifest is a consistency witness, not an authenticated signature or protection from hostile same-user mutation/power loss. Public binary/package redistribution and formal release remain separately unqualified and unauthorized. [Status](../STATUS.md), [requirements](../REQUIREMENTS.md).
