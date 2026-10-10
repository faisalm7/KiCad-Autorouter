# KiCad-Autorouter — local reconstruction

Experimental offline CLI for routing a **separate copy** of a KiCad project with Freerouting and checking it using native KiCad. This is an early reconstruction, with no demonstrated improvement beyond Freerouting or an adapter baseline. See [STATUS.md](STATUS.md) for actual results and gaps.

The tested Mac has KiCad10.0.0 at `/Applications/KiCad`, its bundled Python3.9, Java25.0.2, and Python3.11. Installed applications are not changed. The pinned binaries are recorded in `toolchain.lock.json`.

```sh
python3 -m venv .venv
python3 scripts/setup_engine.py
.venv/bin/python -m autorouter doctor
.venv/bin/python -m autorouter route fixtures/smoke/smoke.kicad_pcb --output .runs/my-smoke --seconds 120
python3 -m autorouter check-result .runs/my-smoke/result.json
python3 -m unittest discover -s tests -v
python3 data/fetch.py
python3 data/fetch.py --verify
```

Use a new output directory for every run; existing results are never overwritten. Exit0 from `route` means routing-scope acceptance, not electrical or manufacturing approval. `result.json` contains native findings, tool/source/candidate hashes and timing. Failed candidates remain inspectable and explicitly rejected. `--keep-existing` protects every existing route for partial completion. Originals are never automatically replaced; inspect the separate candidate in KiCad before deciding what to keep. Actual GUI application/undo is not implemented or qualified.

Only the narrow constraints described in [architecture](docs/architecture.md) are currently supported experimentally. Custom rules/pads, netclass mappings, exclusions, advanced vias and net ties are blocked. No model, final evaluation corpus, release package, human review or physical validation exists. Research scope and operating instructions remain in MASTER_PROMPT.md and AGENTS.md.

Original code and diagnostic fixtures: GPL-3.0-or-later. Downloaded hardware: separate rights documented in [provenance](docs/data-provenance.md). Downloaded engines, datasets and `.local-reference/` are excluded from Git. `python3 scripts/backup.py` creates and tests a private local bundle and non-Git archive after a clean commit; it is **on-Mac-only** protection, independent of the audited source checkpoints on GitHub.
