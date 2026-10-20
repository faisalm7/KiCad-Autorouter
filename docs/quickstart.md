# Run the current local CLI

Use immutable **runtime056**, source `a03b5e8b6ae523d9f099cf211815900053629fe3`, manifest `b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded`. Its [eleven actual six-stage Native workflows](../evidence/runtime056-native-milestone-001.json) and [exposed IR Improve delivery](../evidence/runtime056-ir-delivery-002.json) passed on this Mac with isolated KiCad10.0.7. Normal routing needs no AI account or network. Existing pinned dependencies remain necessary; this is not standalone, clean-OS or Windows qualification. [Current graphical preparation](../evidence/gui-runtime056-089-preparation-001.json) remains unqualified.

**Enter the runtime directory before every `-m autorouter` session.** Running its absolute Python while staying in the checkout can import the wrong source/tool profile. Keep other Native/engine jobs idle. These commands use the existing owned alias-layer example and partial90 preset; they create fresh results, not overwrite earlier evidence:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter preview \
  .runs/gui-session089/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session089/route-settings.json
.venv/bin/python -B -m autorouter route \
  .runs/gui-session089/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session089/route-settings.json --output .runs/my-route-001
.venv/bin/python -B -m autorouter check-result .runs/my-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json \
  --render --output .runs/my-review-001
```

Run each command only after its predecessor succeeds. Choose unused output names. Preserve the sample’s source/preset bytes. For your project, replace the PCB path with an absolute saved path and keep paired PRO/SCH/rule files together. Save and close source editors before routing; unsaved buffers cannot be inspected. Preview is static support information, not Native acceptance.

Open `.runs/my-review-001/preview.html` with **Microsoft Edge → File → Open File…**, without changing Chrome or the default browser. Inspect before/after copper, all layers, findings, warnings and ignored checks. If inspecting the KiCad review project, close its editors and **File → Close Project** before recording your choice.

Only after that review, record acceptance and create a separately validated export:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime-directory-056/runtime'
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json \
  --choice accept --output .runs/my-choice-001
.venv/bin/python -B -m autorouter review-export .runs/my-choice-001/choice.json \
  --seconds 90 --output .runs/my-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/my-export-001/export.json
```

Use `--choice reject` **instead of acceptance**, with a fresh output, to refuse delivery. Intent does not overwrite the original or certify a PCB. `review-export` runs fresh Native checks; `review-export-check` checks stored current consistency without fresh DRC. Explicit export budgets must be30–120s. Later editor changes can stale that proof even if the PCB stays unchanged. Do not alter receipts to recover acceptance. Control-C requests cancellation and retains unaccepted output.

For customization, `settings-init --output .runs/my-settings-001.json` writes a new editable preset; supply it through `--settings`. Keep presets outside the source. Route `--keep-existing` or `--scope partial` protects every original route; whole-board routing preserves locked copper. The selected10.0.7 ordinary path uses native guidance, standard/both, source_all and default via cost or explicit `via_high`. The higher cost is optional and does not guarantee fewer vias. Unsupported selected-net/layer/other-score/tuned combinations refuse; do not use old10.0.0 examples as this profile’s support contract. [Preferences](routing-preferences.md) · [Current scope](experimental-rc.md).

Optional Improve is a distinct narrow whole-board2Cu/flat/single-Default method with a tuned incumbent and internal25s return reserve. Thermal recovery is a separate supported2Cu whole-method path. Neither changes the default Route method or silently weakens original rules/protection. See [GUI method requirements and budgets](gui-workflow.md); current GUI089 is prepared only. [Historical050 active-Java Cancel](../evidence/gui-runtime050-086-active-engine-cancel-001.json) does not qualify056. Exact queued-callback timing remains unproved. The [separate escape-seed diagnostic is negative and deferred](../evidence/qfn-escape-development-probe-002.json), not a shipped strategy or quality gain.

Routing-scope acceptance, whole-project DRC cleanliness and physical/electrical suitability are different. Warnings remain visible; no broad completion, independent human or release claim follows from these controls. [Current status](../STATUS.md) · [Install a fresh same-Mac runtime](install-existing.md). [Historical LED/ArcDice commands and results remain in the unchanged previous guide](history/2026-10-20-pre-runtime050-user-guides/quickstart.md); they are not runtime056 qualification.
