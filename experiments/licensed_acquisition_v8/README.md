# Fixed CP2102 source acquisition v8

This promoted profile reuses the existing bounded acquisition helper. Default
execution only checks the plan; `--fetch` requires the reviewed committed source.
No Native support or routing result follows from acquisition.

The exact original packet is `MAATHES-THILAK-K/USB_TO_UART-CP2102@eecf7bb08afbd1494f3136a5124f4b6b6ea6c63e`: root CP2102.kicad_pcb, CP2102.kicad_sch, CP2102.kicad_pro, LICENSE and README.md, five files347,566B. Git blob/SHA256/size/raw URL pins live in protocol.json (SHA256 `4a398878909d5807107d6c760cbbc0a0ff39f17ee13f0704dc9f62a4a6edab55`). All files stay at their original relative paths under fixed `.data/expansion011/cp2102-uart/`. README explicitly licenses this hardware under MIT; LICENSE names copyright2025MAATHES-THILAK-K. Keep both exact notices.

Actual existing shared.inventory read/hash-only captured the complete current baseline518files53,919,680B, under unchanged finite caps, in0.184076wall/0.072599CPU seconds. No existing source was mutated or root omitted. The frozen inventory is in existing-data-inventory.json. Actual shared `execute` compares the complete on-disk inventory before even plan-only completion and before any GET. It must fail on source drift, new files or mismatches; do not silently refresh baseline. Successful acquisition would give523files54,267,246B and canonical25→26 with all existing dispositions retained.

The wrapper uses existing `shared.main('v8', HERE)` and the unchanged shared cancellation/alarm/lock/material/committed-source/payload/publication helpers: default offline; explicit `--fetch` makes exactly five pinned raw GETs, no retries/redirects/cache fallback. Existing caps remain300wallseconds,30seconds/request,10MiB invocation/project payload,64MiB aggregate `.data`,2048files/4096entries,24MiB outputs. The source packet's exact expected census is347,566B, not a larger substituted input. CPU is not independently limited by this acquisition helper; the lead's established bounded process wrapper must account for actual whole cost if run. No arbitrary source/destination option is added. No archive/model/library/script payload is included.

After integration, targeted tests, audit and a verified committed checkpoint, lead-only prospective commands from the project root:

```sh
.venv/bin/python -B experiments/licensed_acquisition_v8/test_fetch.py
.venv/bin/python -B experiments/licensed_acquisition_v8/fetch.py
.venv/bin/python -B experiments/licensed_acquisition_v8/fetch.py --fetch --output .runs/licensed-acquisition-011-run-001
```

The tests use tiny authored temporary inputs with explicit Git/transport seams; they cannot establish Native quality or an actual download. First run existing shared tests and affected legacy profile tests too. The patch moves their unknown-profile sentinel v8→v9 only, preserving their intended rejection once v8 is registered. Shared material includes v8's six files and the existing shared fetch/test helper only; no dynamic source capture dependency.

Keep missing author-local3D references, embedded LOGO.preety/library provenance, same-function SolderParty reserved source ancestry, USB electrical performance and the line/arc contour unqualified. Source edge minimum0.5mm is unchanged; single-rectangle edge correction does not apply. Native source formatsPCB20241229/SCH20250114 are retained exactly. No source repair, ignored warnings, weakened constraints, family-independence, routing/Native-support or public raw-payload approval follows from acquisition. Previous research wall/CPU is unmeasured and not invented. Actual new work must receive its own receipt and outer costs.
