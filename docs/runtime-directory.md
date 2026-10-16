# Curated local runtime directory

This experimental Mac installation path keeps the product separate from the retained research archive. Source controls pass; actual Native and graphical qualification of this artifact is pending. It is a directory using existing pinned applications, not a standalone app or published package.

Use the existing supported Mac arm64 tools in `toolchain.lock.json`: KiCad10.0.0, Java25.0.2, Freerouting2.5 and Python3.11. The builder downloads nothing and changes no installed applications. From a committed source checkout:

```sh
.venv/bin/python -B scripts/prepare_runtime.py --output /absolute/new-runtime --copy-local-engine
cd /absolute/new-runtime
python3.11 -m venv .venv
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output /absolute/new-runtime/.runs/new-launcher
```

Create `.runs` first if absent. The output and launcher paths must be new. The optional engine flag copies only the existing lock-matching JAR for local use. Leave it out for a source-only directory; routing then remains unavailable until the dependency is provided through an authorized local preparation. Nothing here authorizes binary redistribution or a formal release.

The generated launcher instructions explain opening KiCad, clicking the Autorouter icon, choosing the exact saved source and separate output, saving/closing source editors, previewing, routing, reviewing findings, cancelling and recording accept/reject intent. Close the review editors and use File > Close Project before acceptance. Fresh export runs Native checks again; opening that mutable project can stale its proof. There is no live overwrite or tested undo.

The same structured CLI and explicit JSON settings remain underneath. Use `-B` or `PYTHONDONTWRITEBYTECODE=1`. New files such as `__pycache__` are outside the immutable product population and refuse. Keep this directory at its prepared absolute path. A changed product requires a new directory. Only `.runs` and `.venv` are reserved mutable directories; their contents are not attested by the unsigned build manifest. Keep source projects outside the runtime directory.

Ordinary Native routing and optimization are the qualification target. Placement guidance that requires committed source blobs explicitly refuses here; use the source checkout for those experiments. Unknown electrical requirements, original-rule conflicts, unsupported semantics, warnings and ignored checks retain their existing treatment. No research history, benchmark corpus, model or AI account is needed by the runtime.

[Source controls](../evidence/runtime-directory-source-001.json), [current status](../STATUS.md) and [mandatory gates](../REQUIREMENTS.md) distinguish implementation from qualification. The build manifest records the real source commit and exact product file hashes, not an independently authenticated source claim. This protects against ordinary accidental changes, not a hostile same-user writer or power loss.
