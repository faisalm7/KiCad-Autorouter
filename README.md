# KiCad-Autorouter — local reconstruction

Experimental offline CLI for routing a **separate copy** of a KiCad project with Freerouting and checking it using native KiCad. Combined adapter corrections pass native checks on one public development board where the stock representation fails. Experimental pruning improves a route-length proxy there; bounded thermal recovery passes another exposed board where a fixed tuned portfolio remains rejected. Generalized improvement beyond the adapter is not established. See [STATUS.md](STATUS.md) for actual results and gaps.

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

Only the narrow constraints described in [architecture](docs/architecture.md) are currently supported experimentally. Custom rules/pads, arbitrary or composite netclass patterns, exclusions, advanced vias and net ties are blocked. A narrow literal two-class, two-layer mapping is supported with native membership and dimension checks. No model, untouched final evaluation corpus, formal release package, human review or physical validation exists. Research scope and operating instructions remain in MASTER_PROMPT.md and AGENTS.md.

Original code and diagnostic fixtures: GPL-3.0-or-later. Downloaded hardware: separate rights documented in [provenance](docs/data-provenance.md). Downloaded engines, datasets and `.local-reference/` are excluded from Git. `python3 scripts/backup.py` creates and tests a private local bundle and non-Git archive after a clean commit; it is **on-Mac-only** protection, independent of the audited source checkpoints on GitHub.

Development experiments (every output directory must be new):

```sh
python3 scripts/experiment_adapter.py --output .runs/adapter-ablation-NEW
python3 -m autorouter route '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --adapter both --profile tuned --seconds 120 --output .runs/tuned-NEW
python3 -m autorouter improve '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --seconds 120 --output .runs/prune-NEW
```

`improve` is an experimental strategy: obtain and charge a valid tuned B2 incumbent, then remove potentially redundant zone-net routes only when repeated native checks preserve completion, constraints, warnings and route quality. It is not a new geometric routing algorithm. The entire attempt, including failed trials and final checks, shares one wall budget. The acquired development population contains fourteen boards: seven complete manifested inputs and seven incomplete audit inputs. Three pass static preflight; eleven remain unsupported. Family independence remains unqualified. The fresh thermal experiment provides one narrow end-to-end two-class success. All exclusions remain in [current status](STATUS.md).

`recover` is an experimental completion strategy for a sole supported native thermal failure. It derives a short bridge from the freshly routed board and accepts only after another full native validation, within the same total budget:

```sh
python3 -m autorouter recover '.data/boards/kicad-interf-u/interf_u.kicad_pcb' --seconds 120 --output .runs/thermal-NEW
python3 scripts/experiment_paired.py --project interf_u --system thermal --output .runs/thermal-paired-NEW
```

Unsupported thermal geometry or any other blocking finding remains rejected. The saved copper-path witness does not qualify current capacity, heat flow or manufacturing. Original rule severities and ignored checks remain unchanged; native acceptance alone is not physical validation.

The [thermal experiment](docs/thermal-experiment.md) records fresh B0/B1/completion-only/B2 outcomes, the accepted recovery candidate, exact bridge-removal control, full costs and limitations.

`route --guidance board-floors-v1 --adapter both` explicitly honors original board minima when native Default-class preferences are smaller. This narrow two-layer whole-board policy passed an owned required-via fixture; multichannel still rejects with160opens/one thermal. It preserves original settings and is not yet available to `improve`, `recover`, portfolio or GUI handoff. See [floor guidance evidence](docs/board-floor-guidance.md).
