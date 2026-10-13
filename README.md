# KiCad-Autorouter — local reconstruction

Experimental offline CLI for routing a **separate copy** of a KiCad project with Freerouting and checking it using native KiCad. Combined adapter corrections pass native checks on one public development board where the stock representation fails. Experimental pruning improves a route-length proxy there; bounded thermal recovery passes another exposed board where a fixed tuned portfolio remains rejected. Generalized improvement beyond the adapter is not established. See [STATUS.md](STATUS.md) for actual results and gaps.

For a new checkout, use a Python3.11 interpreter to create the local environment. In this existing project the environment is already prepared; start with `.venv/bin/python -m autorouter doctor`. Do not replace it. A bare `python3` can resolve to an unsupported system interpreter.

The tested Mac has KiCad10.0.0 at `/Applications/KiCad`, its bundled Python3.9, Java25.0.2, and Python3.11. Installed applications are not changed. The pinned binaries are recorded in `toolchain.lock.json`.

```sh
python3.11 -m venv .venv
.venv/bin/python scripts/setup_engine.py
.venv/bin/python -m autorouter doctor
.venv/bin/python -m autorouter route fixtures/smoke/smoke.kicad_pcb --output .runs/my-smoke --seconds 120
.venv/bin/python -m autorouter check-result .runs/my-smoke/result.json
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python data/fetch.py
.venv/bin/python data/fetch.py --verify
```

Use a new output directory for every run; existing results are never overwritten. Exit0 from `route` means routing-scope acceptance, not electrical or manufacturing approval. `result.json` contains native findings, tool/source/candidate hashes and timing. Failed candidates remain inspectable and explicitly rejected. `--keep-existing` protects every existing route for partial completion. Originals are never automatically replaced; inspect the separate candidate in KiCad before deciding what to keep. The separate-copy GUI workflow opens the copied .kicad_pro in KiCad project manager, then Tools → PCB Editor; its multichannel report matches every CLI finding. Automatic application/undo is not implemented. See [GUI workflow and limitations](docs/gui-workflow.md).

Create reusable choices with `.venv/bin/python -B -m autorouter settings-init --output routing-settings.json`, then use `preview BOARD --settings routing-settings.json` before `route`. Explicit command options override only their named choices. See [saved routing preferences](docs/routing-preferences.md) for scope, budgets and optimization settings. Saved choices, partial completion, locked-route preservation and cancellation have native qualification on the recorded fixtures. Allowed new layers are supported only in the documented two-layer native completion mode; selected-net routing remains unsupported. Original rules and protected copper remain enforced.

Only the narrow constraints described in [architecture](docs/architecture.md) are currently supported experimentally. Custom rules/pads, arbitrary or composite netclass patterns, active tuning profiles, exclusions, advanced vias and net ties are blocked. A narrow literal two-class, two-layer mapping is supported with native membership and dimension checks. No model, untouched final evaluation corpus, formal release package, human review or physical validation exists. Research scope and operating instructions remain in MASTER_PROMPT.md and AGENTS.md.

Original code and diagnostic fixtures: GPL-3.0-or-later. Downloaded hardware: separate rights documented in [provenance](docs/data-provenance.md). Downloaded engines, datasets and `.local-reference/` are excluded from Git. `.venv/bin/python scripts/backup.py` creates a full private backup and tests restoration after a clean commit. Between major milestones, `.venv/bin/python scripts/backup.py --incremental PARENT_RECEIPT` creates a checkpoint from an existing restore-verified full backup chain: each checkpoint keeps a standalone all-refs Git bundle, archives only changed/new files in `.runs`, `.data`, and `.local-reference`, and records the complete expected inventory and explicit deletions. This checks chain/artifact integrity and the new delta payload; it **does not claim a complete restoration test**. Run `.venv/bin/python scripts/backup.py --verify RECEIPT` at major milestones, after backup implementation changes, and before release preparation to reconstruct the complete chain, verify every artifact and Git ref, and run the restored CLI help. Older full receipts remain supported. Chains are limited to16receipts (48MiB each,128MiB combined metadata); every target snapshot and archive retains4GiB/140,000file/directory limits. The current capacity change still needs the scheduled actual full restoration; a forecast is not a backup. Start a new full backup at the chain ceiling. Full backups, parent receipts, failed attempts and source evidence are never overwritten or deleted; explicit deletions apply only to a new restoration tree. Keep the entire parent chain and its bound full-restoration proof. These mutable local hashes provide consistency checks, not authentication or atomic protection from concurrent writers. All backups remain **on-Mac-only**, with no disk-failure protection, independently of audited source checkpoints on GitHub.

Development experiments (every output directory must be new):

```sh
.venv/bin/python scripts/experiment_adapter.py --output .runs/adapter-ablation-NEW
.venv/bin/python -m autorouter route '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --adapter both --profile tuned --seconds 120 --output .runs/tuned-NEW
.venv/bin/python -m autorouter improve '.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb' --seconds 120 --output .runs/prune-NEW
```

`improve` is an experimental strategy: obtain and charge a valid tuned B2 incumbent, then remove potentially redundant zone-net routes only when repeated native checks preserve completion, constraints, warnings and route quality. It is not a new geometric routing algorithm. The entire attempt, including failed trials and final checks, shares one wall budget. The acquired development population contains twenty boards. Three pass static preflight; seventeen remain unsupported. All are development-exposed; no untouched evaluation set or proven independent-family count is established. Family independence remains unqualified. The fresh thermal experiment provides one narrow end-to-end two-class success. All exclusions remain in [current status](STATUS.md).

`recover` is an experimental completion strategy for a sole supported native thermal failure. It derives a short bridge from the freshly routed board and accepts only after another full native validation, within the same total budget:

```sh
.venv/bin/python -m autorouter recover '.data/boards/kicad-interf-u/interf_u.kicad_pcb' --seconds 120 --output .runs/thermal-NEW
.venv/bin/python scripts/experiment_paired.py --project interf_u --system thermal --output .runs/thermal-paired-NEW
```

Unsupported thermal geometry or any other blocking finding remains rejected. The saved copper-path witness does not qualify current capacity, heat flow or manufacturing. Original rule severities and ignored checks remain unchanged; native acceptance alone is not physical validation.

The [thermal experiment](docs/thermal-experiment.md) records fresh B0/B1/completion-only/B2 outcomes, the accepted recovery candidate, exact bridge-removal control, full costs and limitations.

`route --guidance board-floors-v1 --adapter both` explicitly honors original board minima when native Default-class preferences are smaller. This narrow two-layer whole-board policy passed an owned required-via fixture; multichannel still rejects with160opens/one thermal. It preserves original settings and is not yet available to `improve`, `recover`, portfolio or GUI handoff. See [floor guidance evidence](docs/board-floor-guidance.md).

Pinned KiCad10.0.0 missed deliberate track/via keepout violations in new native controls. Routing therefore rejects genuine or ambiguous board/footprint rule-area restrictions and legacy `module` footprint syntax. Original constraints are preserved, never removed to pass preflight. Ordinary copper zones and explicitly unrestricted areas remain subject to all other checks. See [native limitations and current diagnostic](docs/placement-area-diagnostics.md).

`route --guidance placement-clearance-v1 --adapter both --profile completion-only` combines the floor correction with exact handling of explicitly unrestricted placement areas and a fixed 20 µm planning clearance margin. The owned fixture and full multichannel development board pass fresh native checks; the full board retains 96 warnings. This adapter improvement is separate from the pruning and thermal strategies. A bounded schema3 `review-copy` can prepare a complete disposable project; its native positive/invalid copy controls pass, and the actual separate-copy GUI observation reproduces every CLI finding when opened through the project manager. Live application/undo remain blocked. Schema4 search/schema5 pruning now retain the same guidance constraints, with their separate workflow qualification pending. See [placement guidance and exact evidence](docs/placement-clearance-guidance.md).

The latest recorded local clone/venv installation at `339e539` passed offline setup,643then-current tests, an actual placement-guided native route/readback and four native preview plots. Later development changes still require installation qualification at the next integration milestone. It reused the installed KiCad, Java and base Python plus a verified engine cache. This is an installation check on this Mac, not qualification of a fresh Mac or a released package. See [installation scope](docs/install-test.md).

Saved preferences and static preview cover scope, budgets and optimization choices. On qualified two-layer boards, `--profile completion-only --layers F.Cu` restricts new routing to the front while preserving exact original protected copper. See [saved settings, allowed layers and limits](docs/routing-preferences.md); actual native positives and required-via/forbidden-layer negatives are retained.

The newest multichannel comparison measures72.9833mm shorter routing than both corrected B1 and tunedB2 at the same19vias/all96warnings under equal120second wall/fullCPU caps. It uses more compute and remains one exposed development input. Earlier Cbudget failure and tie remain visible. The measured allocation is explicit and experimental:

```sh
.venv/bin/python -B -m autorouter improve BOARD.kicad_pcb --guidance placement-search-v1 --seconds 120 --output .runs/improved-NEW
```

This narrow placement path obtains its own standard incumbent and validates each individual removal natively. Original rules remain authoritative; protected/partial/layer-restricted optimization is unsupported and blocks rather than weakening the task. Use ordinary `route` for the documented protected-copper scopes. Persistent `review-choice` records accept/reject intent for a separate review project; it does not apply a design or grant approval. `review-export` now implements fresh native validation of a separate project after that intent; its actual native qualification remains pending. Follow [current outcomes and remaining gates](STATUS.md); no release-ready or generalized-superiority claim is made.
