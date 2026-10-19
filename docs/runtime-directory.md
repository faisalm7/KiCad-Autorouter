# Curated local runtime directory

The current experimental directory is **runtime041**, source `f7524d7bbfb4824640c8ca51dc978769b2fab98b`, manifest `3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399`, selected isolated KiCad10.0.7;48Python/53immutable files. [Native milestone](../evidence/runtime041-native-milestone-001.json) and [actual GUI080 progress](../evidence/gui-runtime041-080-progress-001.json) retain their scope. Canonical/alias GUI delivery includes protected4, Edge F+B review, fresh export0all and checked KiCad0unrouted; separate Reject passes. Remaining GUI roles, queued timing and Native interruption are pending. No broad superiority or release claim.

On this Mac the existing directory is:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-041/runtime
```

Keep this directory and its pinned applications at their recorded paths. Ordinary jobs need no AI account, Git, network or research archive. Code, required resources, licences and the runtime manifest are immutable; only `.runs` and `.venv` are mutable and unattested. Source projects remain outside the product population. Changed product bytes require a new directory; documentation checkpoints do not require rebuilding this tested instance.

The current launcher is `.runs/gui-launcher080/Launch Autorouter.command`, with `.runs/gui-session080/project`, `inspection`, `alias-project` and `jobs`, relative to this runtime. Actual toolbar and partial functional roles are observed; remaining roles stay pending. Launchers use isolated settings/plugin/cache and refuse conflicting KiCad applications without changing global installation/security settings. Preparation alone is not GUI proof. [Workflow](gui-workflow.md).

The [historical039 fresh-environment trial](../evidence/runtime039-clean-environment-001.json) passed doctor and six-stage partial90/export90 delivery at36.27wall/33.71CPU,0all/protected4. It used the same Mac/user/existing pinned dependencies and Python base. Current041 fresh-environment, cleanOS/account, relocation and standalone qualification remain open. The strict absolute-root guards must remain; a copied launcher can start its original runtime and produce a false relocation positive. [Installation scope](install-test.md).

To prepare a different directory, choose a fresh destination from a known committed source and select the exact native profile. These are reproduction commands, not a request to rebuild041:

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

Runtime041 includes optional fixed-method thermal recovery, requiring selected10.0.7/two-layer/whole/native/standard/both/all-source/default-via settings and90–900seconds whole-method budget plus separate capped export. Current041 partial/89-second and unsupported-schematic refusals are observed; positive recovery delivery/cancellation/no-repair/hierarchy roles remain pending. [Historical039 recovery](../evidence/gui-runtime039-079-recovery-repair-001.json) is an exposed Interf result with22warnings and cannot qualify041. Corrected-standard/B1 remains default. [Current gates](../STATUS.md).

Candidates, rendered review and fresh validated export remain separate from originals. Later edits can stale proof; no live overwrite or tested undo is offered. A manifest is a consistency witness, not an authenticated signature or protection from hostile same-user mutation/power loss. The directory remains path-bound, not a standalone or relocatable package. Formal release/tag/package publication and redistribution remain separate approval and qualification gates. [Status](../STATUS.md), [requirements](../REQUIREMENTS.md).
