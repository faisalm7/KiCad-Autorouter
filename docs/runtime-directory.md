# Curated local runtime directory

The current local candidate is **runtime019**, source `321bc5bfdcb85c6975ee5b7e2accf09b6f43da84`. [Fresh preparation/full156/installed doctor](../evidence/runtime019-preflight-full156-001.json) and [actual installed CLI delivery](../evidence/runtime019-production-CLI-delivery-001.json) pass. Route and fresh export each retain their own Native/full-schematic/original-design proof, zero opens/blocking findings, six warnings, two ignored checks and ten protected items. The [019 GUI launcher](../evidence/gui-runtime019-067-prepared-001.json) is prepared only; latest actual GUI evidence remains [014/064](../evidence/gui-runtime014-064-native-opening-001.json).

On this Mac the existing directory is `.runs/runtime-directory-019/runtime`. Keep it at that absolute location and use its copied `.venv/bin/python -B`. Its prepared launcher is `.runs/gui-launcher067/Launch Autorouter.command` inside that directory. Close other KiCad applications before launch; the installer refuses conflicts and does not kill them. See the [workflow](gui-workflow.md) and [installation limits](install-test.md).

To prepare another directory from committed selected source, use the existing supported Mac arm64 tools in `toolchain.lock.json`: KiCad 10.0.0, Java 25.0.2, Freerouting 2.5.0 and Python 3.11. The builder downloads nothing and changes no installed applications:

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
