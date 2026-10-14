# Reproduce the ArcDice development input

ArcDice is an exposed development circuit, not an independent holdout or a physically qualified board. The fixed fetch downloads exactly five files at the recorded public revision: the board, project, schematic, MIT notice and README. It performs no routing or native approval, downloads no scripts/models/libraries, and needs no research cache. Unresolved TP4056 footprint and optional model origins remain visible.

```sh
.venv/bin/python -B scripts/fetch_led_demo.py --project arcdice --fetch --output .data/arcdice-demo-001
.venv/bin/python -B -m autorouter preview .data/arcdice-demo-001/native-project/hardware/ArcDice.kicad_pcb --adapter both
.venv/bin/python -B -m autorouter route .data/arcdice-demo-001/native-project/hardware/ArcDice.kicad_pcb --adapter both --profile tuned --seconds 120 --output .runs/arcdice-route-NEW
.venv/bin/python -B -m autorouter check-result .runs/arcdice-route-NEW/result.json
.venv/bin/python -B -m autorouter review-copy .runs/arcdice-route-NEW/result.json --render --output .runs/arcdice-review-NEW
```

Use fresh output names; existing attempts are never overwritten. `project` contains the five exact originals and original directory layout. `native-project` retains those files and adds two byte-identical notice copies under `hardware/_licenses/creator`. These copies carry notices into native snapshots without altering board/project/schematic bytes or model path semantics. Acquisition has five-GET, 595,346-byte network, 2MiB output and 300-second wall/full CPU caps. Native models/libraries, battery function, fabrication and electrical performance remain unqualified.

For experimental pruning, use the documented `improve BOARD --proposal-policy feedback --seconds 120 --output NEW` command. It obtains its own incumbent. The preview, saved preferences, cancellation and separate-project accept/reject/export flow are in [quickstart](quickstart.md) and [KiCad workflow](gui-workflow.md). All original design constraints and warnings remain enforced.

A fresh source benchmark can use the verified default packet:

```sh
.venv/bin/python -B scripts/experiment_paired.py --project arcdice --system native-all --external-reserve-seconds 40 --output .runs/arcdice-paired-NEW
```

The selector is read-only. A present but stale/incomplete packet rejects rather than falling back to retained research data. Keep native/JVM jobs sequential. Preserve all warnings, failed candidates and the complete four-arm population. Every new comparison requires its own final native/original-design readback and full accounting of prerequisite, outer and audit costs; the inner planning allowance alone is not a full120-second acceptance proof. The recorded continuation is an explicit cumulative-active-work comparison, not uninterrupted elapsed time. [Measured outcomes](../STATUS.md).

The primary fresh acquisition and current installation019 at `4b1e8713ecf93ec00373804206d53740d7eed55a` each completed the five real GETs. The installed distribution/venv completed all eight offline commands through fresh native export/check and rejection intent. Its corrected-adapter output is636.989098mm/zero vias,0opens/0blocking/26 unchanged library warnings; all source bytes and constraints stayed exact. [Actual qualification](../evidence/installation-019/SCOPE.md), [independent readback](../evidence/current-installation019-actual-review-001/REPORT.txt). This qualifies the command-line workflow on the existing Mac/tools/cache, not a fresh OS, new comparison, GUI, human or physical approval. The pruning581.295202mm result is separate frozen comparative evidence.
