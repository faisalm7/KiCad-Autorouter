# Run the current local CLI

**Use experimental installed060**, source `972b395878b734ccf47c7691d66435c42c032634`, manifest `8f385b397ddb6379ce35bab92d62ceff55029c6a796f7d3269c5c5b34ed1ba30`, at `'/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001'`. [Full2122615tests/1skip,13 installed Native workflows/3 invalid controls](../evidence/runtime060-installed-native-milestone-001.json) and [GUI095 assigned core observations](../evidence/gui-runtime060-095-observations-001.json) are closed. FullGUI/exact queued timing and broader release gates remain open. Keep the Native lane idle. [Current gates](../STATUS.md).

**Enter the runtime directory before every `-m autorouter` session.** An absolute interpreter while staying in the checkout can import the wrong source/tool profile. This preserved owned alias source/partial90 preset uses fresh output names:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter preview \
  .runs/gui-session095/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session095/route-settings.json
.venv/bin/python -B -m autorouter route \
  .runs/gui-session095/project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session095/route-settings.json --output .runs/my-route-001
.venv/bin/python -B -m autorouter check-result .runs/my-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json \
  --render --output .runs/my-review-001
```

Run each command only after its predecessor succeeds. Do not rerun completed jobs to read evidence. For your project, supply an absolute saved PCB with paired PRO/SCH/rules; save/close source editors first. Preview is static support information, not Native acceptance. Only canonical `result.json` is an acceptance source; archives are not.

Open `.runs/my-review-001/preview.html` through **Microsoft Edge → File → Open File…**, leaving Chrome/default settings unchanged. Inspect all layers/findings/warnings/ignored checks. If inspecting the KiCad review project, close its editors and **File → Close Project** before intent.

After review, accept and create a separately validated export:

```sh
cd '/Users/faisal/Projects/KiCad-Autorouter-local/.runs/runtime060 fresh install 001'
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json \
  --choice accept --output .runs/my-choice-001
.venv/bin/python -B -m autorouter review-export .runs/my-choice-001/choice.json \
  --seconds 90 --output .runs/my-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/my-export-001/export.json
```

Use `--choice reject` with a fresh output to refuse delivery. Intent neither overwrites originals nor certifies a PCB. Review-export runs fresh Native checks; review-export-check checks stored current consistency without new DRC. Export budgets are30–120s. Editor metadata can stale proof with unchanged PCB bytes; never edit receipts to restore acceptance. Control-C requests cancellation and retains unaccepted output.

Create a preset with `settings-init --output .runs/my-settings-001.json`, then pass `--settings`. Whole routing preserves locked copper; `--keep-existing`/`--scope partial` protects every original route. Current ordinary scope is standard/both/native/source_all on supported2/4Cu, engine-default or explicit `via_high`. Selected nets/layer subsets/other scores/ordinary tuned refuse. [Preferences](routing-preferences.md).

Optional Improve requires canonical2Cu/flat/single-Default whole/native/tuned/both/source_all/default score. Use `settings-init --purpose improve` for its starter preset, `preview --purpose improve` and the `improve` command with that preset. Its whole budget includes incumbent/trials/final checks and40s internal return reserve, without enlarging caps or guaranteeing completion. GUI095 observed corrected help, incumbent and separate trial-log progress, and actual active-engine−9 cancellation. No fallback for stale/invalid/cancelled work; thermal Recover remains distinct and GUI-unqualified. [GUI method requirements](gui-workflow.md).

Current singleton and preparation evidence do not establish new comparative gains. Historical [058 comparison](benchmark-runtime058-installed.md), [057 comparison](benchmark-runtime057-default-improve.md)/[EEPROM failure](benchmark-runtime057-eeprom.md) and immutable058 [archived-reader defect](../evidence/runtime058-archived-receipt-defect-001.json)/[return failure](../evidence/runtime058-natural-expiry-001.json) remain unchanged. B1 stays default. [Windows012](../evidence/windows012-policy-actual001.json) is closed at WinError13/no Native; fullGUI/queue/all-phase/independent-user/cleanOS/human/physical/broad-quality gates remain open. [Installation](install-existing.md) · [Previous guide](history/2026-10-20-pre-runtime050-user-guides/quickstart.md).
