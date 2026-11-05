# Runtime074 protected-gap development comparison

The shipped default completed EEPROM and left one STM32 connection open. Stock Freerouting completed STM32; the tuned/restart baseline completed both. Improve completed EEPROM but failed on STM32. **This study establishes no completion advantage over the strong baseline.** [Machine-readable facts](../evidence/protected-gap074-installed-comparison-001.json).

These are two synthetic geometric partial-routing tasks on exposed reference designs. A seed frozen before outcomes removed whole net groups while protecting all retained copper: 38 EEPROM records and 230 STM32 records. The actual source checks found 19 and 15 open connections respectively, zero blocking source findings, 36/72 warnings and seven/five ignored checks. Expected opens are task demand, not invalid source designs. No independent-family, difficult-board, electrical-suitability or practical engineering-cleanup claim follows.

All twelve arms were frozen before the first run, then executed sequentially without retries, per-board fixes or policy changes. Runtime074 build `6fbbbf22dfb8250f1578fb4d7a45ff0e161b3194` and all 54 installed files stayed unchanged. Each arm had 420 seconds routing, 450 seconds method and 600 seconds delivery, with export120, review60, choice60 and the existing 40-second internal return reserve. Baseline and CLI workload differences remain explicit below.

| Task | Method | Delivered | Final Native opens / blocking / warnings | Full external wall / CPU seconds |
|---|---|---|---|---|
| EEPROM | C default | Yes | 0 / 0 / 36 | 37.67 / 37.45 |
| EEPROM | B0 stock transport | No | 0 / 2 / 36 | 20.45 / 23.99 |
| EEPROM | B1 corrected | Yes | 0 / 0 / 36 | 102.76 / 100.62 |
| EEPROM | B2 tuned single | Yes | 0 / 0 / 36 | 114.32 / 120.50 |
| EEPROM | B2 tuned/restart | Yes | 0 / 0 / 36 | 190.62 / 212.37 |
| EEPROM | C Improve | Yes | 0 / 0 / 36 | 145.91 / 150.69 |
| STM32 | C default | No | 1 / 0 / 71 | 21.38 / 23.33 |
| STM32 | B0 stock transport | Yes | 0 / 0 / 72 | 115.56 / 112.00 |
| STM32 | B1 corrected | No | 1 / 0 / 71 | 22.88 / 24.13 |
| STM32 | B2 tuned single | No | 1 / 0 / 71 | 47.93 / 54.93 |
| STM32 | B2 tuned/restart | Yes | 0 / 0 / 71 | 262.54 / 277.76 |
| STM32 | C Improve | No | No qualified parent result; incumbent 1 / 0 / 71 | 47.98 / 52.93 |

All final exclusions were zero. EEPROM stock failed two actual `starved_thermal` checks; those errors were not waived. Corrected STM32 negatives retained a genuine NRST open. Improve needs a completed, verified incumbent before optional optimization and could not provide one on STM32. Its administration also refused to classify the parent as a qualified completed negative; the entire method remains an unqualified failure. It did not publish an invalid fallback.

Seven deliveries have their own candidate-bound Native refill, full schematic, original-rule/class/field/PRL and protected-copper checks. Four completed negatives and one unqualified method remain in the denominator. There was no observed false acceptance in this finite study; this is not a statistical false-acceptance estimate. Warnings and ignored rules prevent a claim of whole-project cleanliness or electrical approval.

Full external arm totals are **1,130.00 wall / 1,190.70 CPU seconds**, including conversion, all attempts, selection, validation and delivery. Nested process/Native samples overlap and are not added again. Setup, generation, source admission, proof replay, freeze, tests, reporting, authoring and AI review are additional; measured components are in the facts file and unmeasured components remain unknown. B0 retains shared fidelity and Native safeguards, so it is not untouched vanilla. Baseline API and C CLI delivery workloads differ; no generic speed claim is made.

EEPROM delivered copper lengths were 491.28 mm default/B1, 477.45 mm tuned single, and 307.20 mm Improve; shortening is geometric and does not establish improved electrical quality or reduced engineer cleanup. No best-per-board result was promoted to the product default. Default remains corrected-standard and Improve remains optional.

## Evidence and reproduction

The public [generator](../experiments/protected_gap_tasks_v1/generate.py), [v7 freezer](../scripts/freeze_current_comparison.py), [shared enclosure](../scripts/enclose_current_comparison.py) and [reporter](../scripts/report_current_comparison.py) record the mechanism and budgets. [Source admission](../evidence/protected-gap074-source-admission-001.json) and [administration proof replay](../evidence/comparison-v7-runtime074-replay-001.json) retain source and implementation identities. Seed is `protected-gap-v1-20261105`; ranking hashes UTF-8 seed, byte00 and net name, then removes the ceiling of half eligible whole groups. Existing locked groups are excluded. Retained reference geometry and zone intent are deliberate inputs; removed routes and the full reference solution are outside algorithm projects.

The local frozen population is `.runs/protected-gap-runtime074-comparison-001/population.json` (SHA256 `a04314302bd8b3963750fddb852dea1d6286d252c94a163cdb1f8689f38a9f3e`), and its twelve child bindings are in `frozen-children.json` (SHA256 `09a49117e6cbac0c5a32c94cdc42cad681ba797aa4427ffc56bbcf61ac62a421`). The actual final reporter command is retained in `.runs/protected-gap-development074-001/report-command.json`; running that command against the stored bytes only generates a fresh report and starts no Native/engine work. Its frozen output must not be overwritten.

An independent new Native reproduction needs the exact licensed source packets, generated task manifests, same qualified installed artifact/tools and a newly frozen output root. The source registration, generation, admission and freeze commands/receipts are retained locally. Raw CAD and reports have not been republished; asset rights and an independently reconstructed distributable benchmark remain open. Public facts and source hashes are not a backup or a claim of one-command independent reproduction.

The next bounded development question is whether blanket plane suppression creates false routing demand and changes search order. Existing logs show corrected stagnation, not time-budget exhaustion. A plane-only factor must preserve lawful clearances, engine flags, protected copper and fresh Native checks. The current losses remain unchanged whatever a later experiment finds.
