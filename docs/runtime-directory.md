# Curated local runtime directory

The current immutable experimental directory is **runtime042**, source `82aaa3b750007ef2ffaafd367ffcb718aa93865e`, manifest `1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e`, selected isolated KiCad10.0.7;48Python/53immutable files. [Native milestone](../evidence/runtime042-native-milestone-001.json) and [assigned GUI081 roles](../evidence/gui-runtime042-081-functional-summary-001.json) define its bounded evidence. They do not establish full GUI, release, cleanOS or broad superiority. Older041 artifacts remain immutable historical evidence.

On this Mac the existing directory is:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime
```

Keep this directory and its pinned applications at their recorded paths. Ordinary jobs need no AI account, Git, network or research archive. Code, required resources, licences and the runtime manifest are immutable; only `.runs` and `.venv` are mutable and unattested. Source projects remain outside the product population. Changed product bytes require a new directory; documentation checkpoints do not require rebuilding this tested instance.

The usable042 launcher is `.runs/gui-launcher081/Launch Autorouter.command`, with `.runs/gui-session081/project`, `inspection`, `alias-project` and `jobs`, relative to this runtime. The ordinary pristine control is `.runs/gui-session081/project/owned1007-transport.kicad_pro`; its preset is `.runs/gui-session081/route-settings.json`. Actual toolbar, canonical/alias delivery, explicit rejection, source/settings/export-material refusals, Java Cancel, hierarchy/high-budget and optional recovery roles are recorded. Launchers use isolated settings/plugin/cache and refuse conflicting KiCad applications without changing global installation/security settings. Preparation alone is not GUI proof. [Exact workflow](gui-workflow.md).

The [historical039 fresh-environment trial](../evidence/runtime039-clean-environment-001.json) passed doctor and six-stage partial90/export90 delivery at36.27wall/33.71CPU,0all/protected4. It used the same Mac/user/existing pinned dependencies and Python base. The updated checkout now offers [explicit manifest-pinned installation into a fresh root](install-existing.md), without rebuilding042 or copying old mutable state. Current042 fresh-root/native/GUI and fresh-environment qualification remain pending; cleanOS/account, dependency relocation and standalone qualification remain open. The strict absolute-root guards remain; a copied launcher can start its original runtime and produce a false relocation positive. [Installation scope](install-test.md).

To prepare a different directory, choose a fresh destination from a known committed source and select the exact native profile. These are reproduction commands, not a request to rebuild042:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/NEW-runtime --copy-local-engine --native-version 10.0.7
.venv/bin/python -B -m venv --copies --without-pip /absolute/NEW-runtime/.venv
mkdir /absolute/NEW-runtime/.runs
cd /absolute/NEW-runtime
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/NEW-runtime/.runs/NEW-launcher
```

The destination parent must already be a real owned directory. Existing outputs are never overwritten. Selected files must match committed source; the builder records actual HEAD and exact copied population. A different destination/source produces a new manifest and needs its own appropriate qualification; do not relabel historical receipts. `doctor` establishes readiness, not board acceptance, and launcher preparation is not actual GUI proof.

These commands download nothing. The selected profile uses the existing isolated official KiCad10.0.7 bundle pinned in `toolchain.lock.json`; Java25.0.2, Python3.11 and the lock-matching Freerouting2.5.0 JAR must already be available. The engine option copies only that existing JAR for local use. Omitting it leaves routing unavailable until separately authorized dependency preparation. Without `--native-version`, preparation remains the historical10.0.0 profile, not the selected10.0.7 runtime. Use copied interpreters and `-B`/`PYTHONDONTWRITEBYTECODE=1`; symlinks and extra immutable files such as `__pycache__` refuse strict checks.

Runtime042 includes optional fixed-method thermal recovery, requiring selected10.0.7/two-layer/whole/native/standard/both/all-source/default-via settings and90–900seconds whole-method budget plus separate capped export. [Current081 recovery](../evidence/gui-runtime042-081-recovery-deliveries-001.json) retains repair420/export120 with22warnings/seven ignored/protected0 and no-repair90/export90 with0all/protected1. Hierarchy420/export120 is ordinary Route and protects0; canonical/alias partial90 protects4. Forced Native Cancel verifies the corrected interrupted-parent reporting only at one held interval. No natural/SIGINT-only/all-phase/CallAfter-already-queued proof. Later editor metadata/backups do not renew Native validity. Corrected-standard/B1 stays default. [Functional scope](../evidence/gui-runtime042-081-functional-summary-001.json) and [current gates](../STATUS.md).

Candidates, rendered review and fresh validated export remain separate from originals. Later edits can stale proof; no live overwrite or tested undo is offered. A manifest is a consistency witness, not an authenticated signature or protection from hostile same-user mutation/power loss. The directory remains path-bound, not a standalone or relocatable package. Formal release/tag/package publication and redistribution remain separate approval and qualification gates. [Status](../STATUS.md), [requirements](../REQUIREMENTS.md).
