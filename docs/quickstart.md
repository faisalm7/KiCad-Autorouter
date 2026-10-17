# Run a local demo

Current installed CLI qualification is [runtime019](../evidence/runtime019-production-CLI-delivery-001.json), built from `321bc5bfdcb85c6975ee5b7e2accf09b6f43da84`, on an owned protected four-layer source. Its [prepared GUI](../evidence/gui-runtime019-067-prepared-001.json) is not live-tested. The public LED demonstration below retains its separately identified historical installation/evaluation evidence; it was not rerun or relabelled as runtime019. See [installation limits](install-test.md).

This experimental tool runs on the qualified Mac with KiCad10.0.0, Java25.0.2 and Python3.11. Normal routing needs no AI account or internet. Installation and the explicit public demo download use the internet; private boards are not uploaded. Original files stay unchanged and every route goes into a separate project.

Use Terminal in the checkout. In the existing project, keep the prepared `.venv`; start with the doctor command. In a new checkout, create it with `python3.11 -m venv .venv` and run `.venv/bin/python scripts/setup_engine.py` first. The installer verifies the pinned engine. Existing Mac applications are reused.

```sh
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B scripts/fetch_led_demo.py --fetch --output .data/led-demo-001
.venv/bin/python -B -m autorouter preview .data/led-demo-001/project/PushButtonLed.kicad_pcb --adapter both
.venv/bin/python -B -m autorouter route .data/led-demo-001/project/PushButtonLed.kicad_pcb --adapter both --seconds 120 --output .runs/led-route-001
.venv/bin/python -B -m autorouter check-result .runs/led-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/led-route-001/result.json --render --output .runs/led-review-001
```

Choose a fresh output name whenever repeating a command. Existing downloads and results are never overwritten. The demo download contains only five exact public hardware/documentation files, including its original MIT notice. It does not download models or libraries or claim that the board is physically qualified. Seven library warnings remain in the recorded native comparison; inspect all findings.

Open the separate review project's `.kicad_pro` in KiCad Project Manager, then open PCB Editor. Inspect the original and candidate copper plots and the native findings. Accepting records your intent; it does not overwrite a live editor or establish electrical or manufacturing approval.

```sh
.venv/bin/python -B -m autorouter review-choice .runs/led-review-001/review.json --choice accept --output .runs/led-intent-001
.venv/bin/python -B -m autorouter review-export .runs/led-intent-001/choice.json --seconds 120 --output .runs/led-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/led-export-001/export.json
```

The export runs fresh native validation and creates another separate project. Use `--choice reject` with a fresh output to record rejection. Press Control-C in the routing terminal to cancel; interrupted output remains rejected. Save editor changes before starting and close the source PCB editor during routing; the external workflow cannot inspect unsaved buffers.

For your own complete project, replace the demo board path. Use `--keep-existing` to protect every existing route during partial completion. Locked routes stay protected in whole-board routing. Save reusable scope, layer, time and optimization choices with `settings-init`; the [preferences guide](routing-preferences.md) lists supported combinations. Original rules, keepouts, net ties, zones, geometry and warning policies are not weakened to satisfy those choices. Unsupported constraints block the task with a reason.

Selected-net routing is available narrowly with `--scope selected --nets EXACT_NAME --profile completion-only` and all source layers; other copper stays protected and other-net failures still reject. The [guarded parent-class scope](native-parent-classes.md) has two-layer whole/partial qualification and a closed four-copper whole-board/source_all transport control with locked protected copper. The narrow canonical four-copper partial path is also qualified on the owned installation042 control, preserving all ten existing tracks. Four-copper selected routing and explicit layer restrictions remain unqualified; selected composite classes remain unsupported.

For experimental pruning on a qualified unlocked whole-board source, use `improve BOARD --proposal-policy feedback --seconds 120 --output NEW`. It obtains and validates its own incumbent before attempting deletions. The [measured results](../STATUS.md) are exposed development evidence, including this small support case; generalized completion superiority and physical validation remain open.

The fixed-source benchmark can be reproduced from the default downloaded demo without the ignored research cache:

```sh
.venv/bin/python -B scripts/experiment_paired.py --project push-button-led --system native-all --output .runs/led-paired-NEW
```

Keep other native/engine jobs idle. Its four arms use identical original constraints and120second wall/fullCPU budgets. Preserve every failed candidate and warning. The reported historical numbers additionally include conservative prerequisite/audit/startup charges documented with their protocol; a new run gets its own evidence and must not overwrite that record.

These commands were run in fresh local installation017 at `2d456f9a798ed6875cdfe153795b96cfec65dd73`: actual five-file download, eight offline workflow commands and native export0opens/0blocking/7unchanged warnings, with source files preserved. [Qualification](../evidence/installation-017/SCOPE.md). Existing Mac applications and verified engine cache were reused; this is not a fresh OS or human PCB review.

The subsequent [installed LED GUI003 observation](../evidence/installed-led-export-gui-003/SCOPE.md) opened the separate export through KiCad Manager and PCB Editor, with refill/full schematic parity/all severity filters enabled: zero opens/errors/parity findings/warnings and five unchanged ignored checks. Its library context differs from the isolated CLI, whose seven library warnings remain in acceptance evidence; exact GUI asset equivalence is unobserved. Earlier access/preparation failures remain preserved. Closing with Discard Changes preserved PCB/SCH/export but added one schematic setting to the disposable project; use fresh original-rule `review-export`, not changed GUI settings, as the authoritative export. [Closure record](../evidence/installed-led-export-gui-003-closure/SCOPE.md). No live apply/undo, human or physical approval is implied.

The new [ArcDice fixed-source workflow](arcdice-demo.md) preserves the original hardware hierarchy and notices, with guarded native class-parent dimensions. Its actual installation019 fiveGET/eight-command native qualification is [recorded separately](../evidence/installation-019/SCOPE.md) from earlier LED017. All26 ArcDice warnings remain visible.

For experimental native pruning with saved optimization choices, use `settings-init --purpose improve` and `improve BOARD --settings FILE --proposal-policy feedback --output .runs/improve-NEW`. Whole-board/source_all only; locked copper and all original rules remain. Use `route` for qualified partial/selected/layer constraints. [Saved improvement settings](routing-preferences.md) describes explicit budgets/scoring. The actual preset-driven LED control, stale-preset rejection, copper preview, accept/reject intent and fresh native export passed. All seven warnings remain. [Product evidence](../evidence/pruning-preferences-native-product-003/SCOPE.md). Pruning has measured geometry gains on exposed development circuits; broad completion and physical claims remain unproven.
