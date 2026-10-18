# Curated local runtime directory

The current candidate is **runtime033**, source `a476a0a0647bc51889d291e3e6e2598f4ec24370`, manifest `115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987` (46 modules,51 immutable files). [Full176/install006 and ordinary whole/partial six-stage CLI](../evidence/runtime033-ordinary-install-001.json), [fresh invalid controls](../evidence/runtime033-native-invalid-001.json) and [same-account clean-environment trial](../evidence/runtime033-clean-environment-001.json) pass within recorded scopes. Every delivered final retains its own Native/full-schematic/original/protected proof.

On this Mac the existing directory is:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-033/runtime
```

Keep this directory and its pinned applications at their recorded paths. Ordinary jobs need no AI account, Git, network or research archive. Code, required resources, licences and the runtime manifest are immutable; only `.runs` and `.venv` are mutable and unattested. Source projects remain outside the product population. Changed product bytes require a new directory; documentation checkpoints do not require rebuilding this tested instance.

Current033 graphical qualification is still pending as fresh GUI074 is prepared/tested. Access now worked after the owner clicked the toolbar icon, opening preserved029/GUI073. [026/GUI072](../evidence/gui-runtime026-072-native-controls-001.json) remains the last actual GUI-qualified build and cannot qualify033. Use only the launcher recorded for the intended runtime; preparation alone does not prove GUI operation. Launchers use isolated settings/plugin/cache and refuse conflicting KiCad managers/editors without closing them or altering global installation/security settings. [Workflow](gui-workflow.md).

The [clean-environment033 trial](../evidence/runtime033-clean-environment-001.json) used the existing directory with a fresh owned HOME/TMP, minimal PATH, actual doctor and six CLI stages: partial90/export90, Native0/0/0/0, all four original routes protected,36.87wall/33.92CPU. This is same-user proof with existing dependencies and Python3.11.9 `.pyenv` base at fixed paths. It is not clean-OS/account, relocation, standalone or graphical installation qualification. [Installation scope](install-test.md).

To prepare a different directory, choose a fresh destination from a known committed source and select the exact native profile. These are reproduction commands, not a request to rebuild033:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/NEW-runtime --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip /absolute/NEW-runtime/.venv
mkdir /absolute/NEW-runtime/.runs
cd /absolute/NEW-runtime
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/NEW-runtime/.runs/NEW-launcher
```

The destination parent must already be a real owned directory. Existing outputs are never overwritten. Selected files must match committed source; the builder records actual HEAD and exact copied population. A different destination/source produces a new manifest and needs its own appropriate qualification; do not relabel033 receipts. `doctor` establishes readiness, not board acceptance, and launcher preparation is not actual GUI proof.

These commands download nothing. The selected profile uses the existing isolated official KiCad10.0.7 bundle pinned in `toolchain.lock.json`; Java25.0.2, Python3.11 and the lock-matching Freerouting2.5.0 JAR must already be available. The engine option copies only that existing JAR for local use. Omitting it leaves routing unavailable until separately authorized dependency preparation. Without `--native-version`, preparation remains the historical10.0.0 profile, not033. Use copied interpreters and `-B`/`PYTHONDONTWRITEBYTECODE=1`; symlinks and extra immutable files such as `__pycache__` refuse strict checks.

Ordinary selected10.0.7 Route/Preview/GUI supports corrected-standard/both, whole/partial completion, all source layers/default vias. Experimental CLI thermal recovery now has an own validated delivery on exposed Interf in the [completed033 comparison](../evidence/runtime033-current-interf-comparison-001.json); it remains opt-in, with B1 default unchanged. The comparison API requires an exact caller-owned non-admitting context; it does not widen ordinary CLI/GUI support. Improve, selected-net/layer restrictions and other unqualified combinations refuse in this profile. Historical10.0.0 evidence retains its exact scope. [Supported matrix and gates](experimental-rc.md).

Candidates, rendered review and fresh validated export remain separate from originals. Later edits can stale proof; no live overwrite or tested undo is offered. A manifest is a consistency witness, not an authenticated signature or protection from hostile same-user mutation/power loss. The directory remains path-bound, not a standalone or relocatable package. Formal release/tag/package publication and redistribution remain separate approval and qualification gates. [Status](../STATUS.md), [requirements](../REQUIREMENTS.md).
