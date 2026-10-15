# Larger local routing example

The Universal Shift Interface Board is a public, exposed development example.
It has77footprints,165pads, two copper layers, literal Default/Power classes and
a ground zone. Original rules, locked copper, PRL and the complete schematic
remain authoritative. Optional model files are not downloaded.

Use Terminal in `~/Projects/KiCad-Autorouter-local`:

```sh
.venv/bin/python -B -m autorouter doctor
```

The exact demo already exists in this project. Reuse it. For a separate installation that has not downloaded it, run:

```sh
.venv/bin/python -B scripts/fetch_led_demo.py --project universal-shift-interface --fetch
```

The download requires a fresh output directory. Preserve any existing demo. The pinned source revision is
[02a2698f](https://github.com/Natasha-Eman/32-bit-Universal-Shift-Register/tree/02a2698f962e3cd7c16d58167a455ad01c97e1b0).
The exact source/notice manifest retains the publisher's attribution and grant.
The README's merge markers and untested-hardware statement remain visible.

Route a new candidate with the tuned low-via configuration:

```sh
.venv/bin/python -B -m autorouter route \
  ".data/universal-shift-interface-demo-001/native-project/KiCad/Interface Board/USR_LED_Board.kicad_pcb" \
  --seconds 200 --adapter both --profile tuned --scoring-preference via_low \
  --output .runs/my-universal-route-001
```

Or obtain an independent incumbent and improve it through native-validated
pruning. This command does not consume the route created above:

```sh
.venv/bin/python -B -m autorouter improve \
  ".data/universal-shift-interface-demo-001/native-project/KiCad/Interface Board/USR_LED_Board.kicad_pcb" \
  --seconds 200 --proposal-policy feedback --scoring-preference via_low \
  --output .runs/my-universal-improve-001
```

Choose a new output name for every attempt. Press Control-C to cancel. Inspect
the actual result; time limits can reject an otherwise valid partial candidate.
Use [saved preferences](routing-preferences.md) for persistent routing choices
and [review/export](gui-workflow.md) to preview an accepted result, record intent
and create a fresh native-validated separate project. Acceptance is not human
PCB approval, and no live editor file is overwritten.

The [recorded cumulative950 comparison](../evidence/universal-preparation950-actual-001.json)
gives C4435.181636mm/25vias versus tunedB24556.133635mm/25vias, both0opens and
0blocking, retaining81original warnings and five ignored checks. C costs
860.161884wall/850.411319CPU including prior failed attempts, versus
B2461.700724/506.589491. The fresh200-second product commands above do not erase
that historical compute or reproduce the entire950protocol by themselves.
All raw final observations and the frozen controller/protocol are retained.

This is a configuration-specific exposed result with greater compute, not a
speedup, general completion claim or untouched confirmation. Native acceptance
is separate from whole-project cleanliness, electrical adequacy and physical
validation. Third-party CAD/models remain outside public Git.
