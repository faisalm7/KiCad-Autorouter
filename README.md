# KiCad-Autorouter — local reconstruction

Experimental offline CLI for routing a **separate copy** of a KiCad project with Freerouting and checking it using native KiCad. Combined adapter corrections pass native checks on one public development board where the stock representation fails. Generalized improvement beyond the adapter is not established. See [STATUS.md](STATUS.md) for actual results and gaps.

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

Use a new output directory for every run; existing results are never overwritten. Exit0 from `route` means routing-scope acceptance, not electrical or manufacturing approval. `result.json` contains native findings, tool/source/candidate hashes and timing. Failed candidates remain inspectable and explicitly rejected. `--keep-existing` protects every existing route for partial completion. Originals are never automatically replaced; inspect the separate candidate in KiCad before deciding what to keep. The separate-copy GUI workflow has been exercised in PCB Editor; automatic application/undo is not implemented. See [GUI workflow and limitations](docs/gui-workflow.md).

Only the narrow constraints described in [architecture](docs/architecture.md) are currently supported experimentally. Custom rules/pads, netclass mappings, exclusions, advanced vias and net ties are blocked. No model, untouched final evaluation corpus, formal release package, human review or physical validation exists. Research scope and operating instructions remain in MASTER_PROMPT.md and AGENTS.md.

Original code and diagnostic fixtures: GPL-3.0-or-later. Downloaded hardware: separate rights documented in [provenance](docs/data-provenance.md). Downloaded engines, datasets and `.local-reference/` are excluded from Git. `python3 scripts/backup.py` creates and tests a private local bundle and non-Git archive after a clean commit; it is **on-Mac-only** protection, independent of the audited source checkpoints on GitHub.

Development experiments (every output directory must be new):

```sh
python3 scripts/experiment_adapter.py --output .runs/adapter-ablation-NEW
python3 -m autorouter route '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --adapter both --profile tuned --seconds 120 --output .runs/tuned-NEW
python3 -m autorouter improve '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --seconds 120 --output .runs/prune-NEW
```

`improve` is an experimental strategy: obtain and charge a valid tuned B2 incumbent, then remove potentially redundant zone-net routes only when repeated native checks preserve completion, constraints, warnings and route quality. It is not a new geometric routing algorithm. The entire attempt, including failed trials and final checks, shares one wall budget. The corpus currently contains seven boards in six provisional families; two pass static preflight, with native multiclass routing qualification still pending. All exclusions remain in [current status](STATUS.md).
