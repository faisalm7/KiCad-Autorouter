# Run runtime074 locally

The [installed074 headless milestone](../evidence/runtime074-installed-native-milestone-001.json), [finite GUI105 core](../evidence/gui-runtime074-105-core-001.json) and [one large CLI delivery](../evidence/runtime074-large-delivery-qualified-001.json) pass their recorded gates. Full GUI qualification remains open for the genuine updated-warning dialog and exact queued-open interval. Enter the installed directory before every `-m autorouter` session: an absolute interpreter alone can import the wrong checkout. Keep the routing lane idle and use fresh outputs.

From this checkout, the prepared owned example and 90-second partial preset retain four protected routes:

```sh
cd './.runs/runtime074 fresh install 001'
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter preview \
  .runs/gui-session105/ordinary-project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session105/ordinary-settings.json
.venv/bin/python -B -m autorouter route \
  .runs/gui-session105/ordinary-project/owned1007-transport.kicad_pcb \
  --settings .runs/gui-session105/ordinary-settings.json --output .runs/my-route-001
.venv/bin/python -B -m autorouter check-result .runs/my-route-001/result.json
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json \
  --render --output .runs/my-review-001
```

Run each command only after its predecessor succeeds. Do not repeat completed qualification jobs to read evidence. For your own project, supply its absolute saved PCB and unchanged paired PRO/SCH/rule files; save and close source editors first. Preview checks static support. Only canonical `result.json` can supply acceptance; archived provisional reports cannot.

Open `.runs/my-review-001/preview.html` in **Microsoft Edge**, inspect all layers/findings/warnings/ignored checks, and close any separately opened review project before choosing:

```sh
.venv/bin/python -B -m autorouter review-choice .runs/my-review-001/review.json \
  --choice accept --output .runs/my-choice-001
.venv/bin/python -B -m autorouter review-export .runs/my-choice-001/choice.json \
  --seconds 90 --output .runs/my-export-001
.venv/bin/python -B -m autorouter review-export-check .runs/my-export-001/export.json
```

Use `--choice reject` with a fresh output to refuse delivery. Accept records software intent; fresh export runs new native validation. Export check verifies current retained proof without new DRC. Editor changes can stale proof without changing PCB bytes; never edit receipts to renew acceptance. Control-C requests cancellation and retains unaccepted output.

`settings-init --output .runs/my-settings-001.json` creates a persistent preset. Ordinary Route supports qualified whole/partial2/4Cu, standard/both/native/all source layers, default or explicit via_high. Whole routing preserves locked copper; partial routing protects all existing routes. Unsupported settings refuse. [Preference schema and structured interface](routing-preferences.md).

Optional Improve uses `settings-init --purpose improve`, `preview --purpose improve`, then `improve` with that preset. Its narrower qualified2Cu/flat/whole/tuned/default-score path retains original native-resolved classes;40 seconds remain reserved inside its routing budget. It needs a valid incumbent and cannot establish completion gains by itself. No fallback follows stale/invalid/cancelled work. Native13 and owned three-class controls retain their own scopes; no every-failure/literal-expiry guarantee follows.

The [074 ArcDice CLI run](../evidence/runtime074-large-delivery-qualified-001.json) used unchanged 420-second routing, 450-second method and 600-second delivery limits. Complete wall/CPU totals, including the retained launch-failure debit, were 556.86/512.24 seconds. Complete review CLI was 33.473/30.882 seconds and choice CLI 28.391/27.456 seconds, each below the required 45-second wall/CPU headroom target; these are not receipt samples. All 29 internal trials, including four thermal rejections, and the final 26 warnings/five ignored checks remain recorded. This qualifies one exposed delivery path, not comparative routing quality.

Routing, review and export ceilings are distinct observed operation limits, not an OS aggregate quota. CLI intake/readback and delivery costs also count in the reported end-to-end comparisons. Normal operation needs no AI, Git, network or research archive. [Current status](../STATUS.md) · [Start here](../START_HERE.md) · [Installation](install-existing.md).
