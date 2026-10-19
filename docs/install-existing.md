# Install a pinned local runtime in a new folder

The checkout's `scripts/prepare_runtime.py --install-existing` copies an existing verified runtime into a fresh owned folder without rebuilding its router. It preserves the source commit, exact immutable files, selected native version, lock and local engine, changing only the manifest's absolute root. The original folder remains intact. This is an explicit same-Mac installation operation; moving a folder or copying its launcher does not repair its identity.

The source must still be at its manifest-bound path, with a verified local engine. Supply its exact manifest SHA256 from the trusted qualification record. Changed/missing files, links, extra immutable files, a wrong manifest pin and existing destinations refuse. Source, installer and destination are checked again before returning. A failure preserves any partial destination; choose a new destination for a later attempt. A `.runs/install-existing-runtime-001.json` record may remain after a late refusal and is **not a completion or native-qualification marker**.

Run this helper from the updated source checkout. The older immutable runtime's own builder need not contain the new installation mode. For example, using the current042 source artifact and a fresh destination whose parent already exists:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
.venv/bin/python -B scripts/prepare_runtime.py --install-existing \
  --source /Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-042/runtime \
  --expected-manifest-sha256 1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e \
  --output '/absolute/NEW Autorouter runtime'
.venv/bin/python -B -m venv --copies --without-pip '/absolute/NEW Autorouter runtime/.venv'
cd '/absolute/NEW Autorouter runtime'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/install_gui.py --output '/absolute/NEW Autorouter runtime/.runs/NEW-launcher'
```

Only continue after each command exits successfully. The install creates `.runs` for its record; old jobs, settings, virtual environments and launchers are deliberately excluded. Create a fresh launcher and use its README. Keep saved projects outside the immutable product files and retain their original constraints. Every new candidate still needs preview, explicit choice and fresh native-validated separate-project export. Doctor and launcher generation alone do not qualify actual routing or GUI operation.

Existing pinned KiCad/Java/Python locations on this same Mac remain required. No dependency is downloaded or relocated; no global app, security setting or repository is changed. This is not standalone, cleanOS, other-account or Windows qualification. No formal package is published. [Preparation](runtime-directory.md) · [Installation evidence and limits](install-test.md).
