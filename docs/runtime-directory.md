# Curated local runtime directory

The current qualified local candidate is **runtime023**, source `8c0c8468823751d9b5dc4c9a9c51b1d622269a27`, manifest `3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81`. [Whole4Cu CLI](../evidence/runtime023-installed-CLI-001.json), [partial2Cu CLI](../evidence/runtime023-installed-partial-CLI-001.json) and [declared GUI023/070 controls](../evidence/gui-runtime023-070-native-controls-001.json) pass within their recorded scopes. Every final Route/export has its own Native/refill/full-schematic/original-design proof. Whole4Cu retains six warnings and ten protected items; the GUI2Cu partial case has0 opens/blocking/warnings/exclusions and all4 protected items. [Limits](experimental-rc.md).

On this Mac the existing directory is `.runs/runtime-directory-019/runtime`. Keep it at that absolute location and use its copied `.venv/bin/python -B`. Its prepared launcher is `.runs/gui-launcher070/Launch Autorouter.command` inside that directory. Close other KiCad applications before launch; the installer refuses conflicts and does not kill them. See the [workflow](gui-workflow.md) and [installation limits](install-test.md).

To prepare another default-profile directory from committed selected source, use the existing supported Mac arm64 tools in `toolchain.lock.json`: KiCad 10.0.0, Java 25.0.2, Freerouting 2.5.0 and Python 3.11. The builder downloads nothing and changes no installed applications:

```sh
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/new-runtime --copy-local-engine
cd /absolute/new-runtime
python3.11 -m venv --copies --without-pip .venv
mkdir .runs
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/new-runtime/.runs/new-launcher
```

Use fresh destination names. Doctor establishes dependency readiness, not board acceptance. The optional engine flag copies only the existing lock-matching JAR for local use; without it, routing remains unavailable until authorized local dependency preparation. This is a fixed-path directory using existing applications, not a standalone or relocatable installer. A new directory needs appropriate installation/Native qualification.

Use interpreter copies: the strict artifact backup refuses symbolic links. Use `-B` or `PYTHONDONTWRITEBYTECODE=1`; generated `__pycache__` is outside the immutable product population and causes refusal. A changed product requires a new directory. Only `.runs` and `.venv` are mutable and unattested. Keep user source projects outside the runtime directory; owned qualification fixtures under `.runs` have separately recorded identities.

The runtime contains code, necessary resources, license and generated instructions. Ordinary jobs need no research history, benchmark corpus, model, AI account, Git or internet. Placement guidance requiring source blobs refuses here; use the source checkout for those experiments. Unsupported semantics, warnings and ignored checks retain their treatment.

Save and close source editors, then preview, route, review and record intent through the [GUI](gui-workflow.md) or [structured CLI](structured-interface.md). Fresh export validates another separate project. Opening/editing it can change metadata and stale its proof. No live overwrite or tested undo is offered. The manifest identifies bytes and source commit; it is not an authenticated signature or protection from hostile same-user modification or power loss.

No binary redistribution, formal release or package publication is authorized by these local preparation instructions. [Status](../STATUS.md) and [mandatory gates](../REQUIREMENTS.md) remain authoritative.

A separate **unqualified engineering profile** can be selected with `scripts/prepare_runtime.py --native-version 10.0.7 --output /absolute/new-runtime --copy-local-engine`. It uses the exact existing isolated official app pinned in `toolchain.lock.json`; no app download/replacement occurs. Manifest schema2 records this explicit selection while code and lock remain exact committed bytes. Default preparation/schema1 remains10.0.0. A profile is not qualification: fresh normal Native/GUI/install controls are required. The1007 candidate currently refuses optimization, selected-net/layer restrictions and other combinations outside corrected-standard whole/partial Route on all source layers. Existing1000 support is retained separately. No environment variable or candidate receipt selects tools.
