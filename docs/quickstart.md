# Run the current local CLI

**Safety hold:** immutable058 can report an archived provisional receipt as current; use only the named canonical `result.json`. A separate 90-second Improve control timed out during final proof/publication. The [source identity fix](../evidence/routing-receipt-identity-repair-001.json) has targeted tests and an actual CLI refusal, but new Native/install/GUI qualification and return-cost repair remain pending. [Current gates](../STATUS.md).

Use immutable **runtime058**, source `8f5e96b88dd22cd25919bb71ce47711612994efa`, original manifest `4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74`. [Eleven Native workflows](../evidence/runtime058-native-milestone-001.json), [IR Improve](../evidence/runtime058-ir-delivery-001.json) and [EEPROM Improve](../evidence/runtime058-eeprom-improve-regression-001.json) pass within recorded scopes. [GUI092 ordinary](../evidence/gui-runtime058-092-ordinary-001.json)/[observations](../evidence/gui-runtime058-092-observations-001.json) and [installed GUI093](../evidence/gui-runtime058-install093-observations-002.json) are actual functional evidence, not fullGUI or release qualification.

**Enter the runtime directory before every `-m autorouter` session.** An absolute interpreter while staying in the checkout can import the wrong source/tool profile. Keep other Native/engine jobs idle. This owned original-root example uses its preserved alias source/partial90 preset and fresh output names:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-058/runtime'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter preview \
  .runs/gui-session092/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session092/route-settings.json
.venv/bin/python -B -m autorouter route \
  .runs/gui-session092/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session092/route-settings.json --output .runs/my-route-001
.venv/bin/python -B -m autorouter check-result .runs/my-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json \
  --render --output .runs/my-review-001
```

Run each command only after its predecessor succeeds. Do not rerun completed jobs to read their evidence. For your project, supply an absolute saved PCB and keep paired PRO/SCH/rules together. Save/close source editors first; unsaved buffers cannot be inspected. Preview is static support information, not Native acceptance.

Open `.runs/my-review-001/preview.html` through **Microsoft Edge → File → Open File…**, leaving Chrome/default settings unchanged. Inspect before/after copper, all layers, findings, warnings and ignored checks. If inspecting the KiCad review project, close its editors and **File → Close Project** before recording intent.

After review, accept and create a separately validated export:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-058/runtime'
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json \
  --choice accept --output .runs/my-choice-001
.venv/bin/python -B -m autorouter review-export .runs/my-choice-001/choice.json \
  --seconds 90 --output .runs/my-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/my-export-001/export.json
```

Use `--choice reject` instead of accept, with a fresh output, to refuse delivery. Intent does not overwrite the original or certify a PCB. Review-export runs fresh Native checks; review-export-check checks stored current consistency without fresh DRC. Export budgets are30–120s. Editor metadata changes can stale proof even with unchanged PCB bytes. Never edit receipts to recover acceptance. Control-C requests cancellation and retains unaccepted output.

Create an editable preset with `settings-init --output .runs/my-settings-001.json`, then pass `--settings`. Whole routing preserves locked copper; `--keep-existing`/`--scope partial` protects every original route. Current ordinary scope is standard/both/native/source_all on supported2/4Cu, engine-default or explicit `via_high` search costs. Selected nets/layer subsets/other scores/ordinary tuned refuse. [Preferences](routing-preferences.md).

Optional Improve requires qualified2Cu/flat/single-Default whole/native/tuned/both/source_all/default score and includes an internal25s return reserve. Thermal recovery has a separate narrow contract and is not current GUI-qualified. Neither changes B1 default or promises completion/electrical gain. [GUI method requirements](gui-workflow.md).

Current GUI092 engine Cancel records−9/cleanup/CLI2/unaccepted/no downstream; the first small-job Cancel hit validation after Java finished. No graceful/all-phase/algorithm-entry guarantee follows. Exact queued timing remains unproved. [Historical057 comparisons](benchmark-runtime057-default-improve.md) and [EEPROM failure](benchmark-runtime057-eeprom.md) remain unchanged by058 singleton successes. The [negative escape experiment](../evidence/qfn-escape-development-probe-002.json) remains deferred, outside the product.

Normal jobs need no AI/network/Git/archive, but pinned same-Mac/account/basePython/external tools remain required. Standalone/cleanOS/Windows/independent-user/fullGUI/human/physical gates remain open. [Status](../STATUS.md) · [Installation](install-existing.md) · [Historical guide preserved unchanged](history/2026-10-20-pre-runtime050-user-guides/quickstart.md).
