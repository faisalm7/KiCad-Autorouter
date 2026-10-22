# Runtime058 installed development comparison

The installed default and optional Improve each delivered all three exposed inputs. Corrected Freerouting, single tuned Freerouting and the restart portfolio also delivered all three. **There is no completion advantage over the corrected or tuned baselines.** Stock delivered DS18B20 and failed Native validation on IR and EEPROM. Improve reduced IR and EEPROM track length relative to the single-run baselines, at the same via counts; the restart portfolio produced fewer vias and longer tracks. These are geometric tradeoffs, not electrical approval or measured engineer cleanup.

This is one fresh, prospectively frozen **18-arm current-build qualification**, not new independent breadth or untouched confirmation. It does not replace the historical [057 two-input](benchmark-runtime057-default-improve.md) or [057 EEPROM](benchmark-runtime057-eeprom.md) results, including the latter's Improve export failure. The separate 058 single regressions were prerequisites, not substituted arms.

## Artifact and protocol

Use the [owned evidence packet](../evidence/runtime058-installed-three-family-001.json) and its [sanitized facts](../evidence/runtime058-installed-three-family-001-notes/facts/report.json) / [custody index](../evidence/runtime058-installed-three-family-001-notes/files.json). Raw CAD, DSN, SES, detailed findings and every actual final Native/original-design proof remain local. Public facts and hashes are not a backup of those bytes.

| Binding | Value |
|---|---|
| Runtime build source | `8f5e96b88dd22cd25919bb71ce47711612994efa` |
| Original runtime manifest | `4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74` |
| Installed root manifest | `19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2` |
| Frozen administration HEAD | `f832b0435ea231332de1ac3831d166bc71c10b12` |
| Population SHA256 | `7aa591a491b9358868c351b4cf357dcbe38351185bdfc5a7e91832a5330a71f8` |
| Frozen children SHA256 | `c0e04f9d0751cf1272abe00ed68ec3af9ccdea53759d32695c3d950fe0895b8f` |
| Sanitized report SHA256 | `af7ec718dfd4384c267e0af826d852b76cca13cd1fb01db67620a12868748c8a` |
| Toolchain | Isolated official KiCad 10.0.7 / macOS arm64; Freerouting 2.5.0; copied venv using host Python 3.11.9; same Mac/account/external dependencies |

All 54 immutable runtime files match the original build; only the installed root binding differs. The frozen family order was DS18B20, IR, EEPROM; arm order was default, stock, corrected, single tuned, restart, Improve. One worker ran at a time, without policy/source edits, retries, board-specific tuning or per-board method selection.

Each method retained a 420-second routing allocation, 450-second method wall/full-CPU cap, 600-second complete wall/full-CPU cap and 120-second export ceiling. Review and choice remained 30 seconds each. Improve retained its 25-second return reserve and 32-trial ceiling. The restart baseline used the fixed balanced default/low/high via-cost portfolio, including selection and delivery. These are acceptance and sampled process limits, not OS aggregate quotas or universal timing guarantees.

B0 disables the two adapter corrections but retains common fidelity, protection and Native safeguards. It is not qualification of an untouched official plugin. Baseline sealed API delivery and the actual product CLI perform different authority workloads. All external costs below are counted, but they do **not** establish a generic algorithmic speedup.

## Completion and geometry

Length is millimetres of track copper; vias are counts. Only delivered candidates are ranked. Every delivered input has zero opens and zero blocking findings, while retaining its original warnings and ignored checks.

| Method | DS18B20 length / vias | IR length / vias | EEPROM length / vias | Deliveries |
|---|---:|---:|---:|---:|
| B0 stock | 35.514 / 0 | Failed: 1 open, 6 blocking | Failed: 2 opens, 3 blocking | 1 / 3 |
| B1 corrected | 39.512 / 0 | 167.425 / 2 | 428.698 / 7 | 3 / 3 |
| B2 single tuned | 39.498 / 0 | 167.425 / 2 | 428.698 / 7 | 3 / 3 |
| B2 restart portfolio | 39.498 / 0 | 175.690 / 0 | 514.441 / 2 | 3 / 3 |
| C shipped default | 39.512 / 0 | 167.425 / 2 | 428.698 / 7 | 3 / 3 |
| C optional Improve | 39.498 / 0 | 138.267 / 2 | 270.008 / 7 | 3 / 3 |

The default matches B1 geometry on these inputs. Both C modes have two completion gains over B0 and three completion ties with B1 and each B2 method; no completion losses occurred within this cohort. Stock DS18B20 is the shortest DS result. Improve's DS result comes from its tuned incumbent: it attempted zero pruning trials. IR attempted 18 trials with 12 validated improvements; EEPROM attempted 32 with 30 improvements. Do not attribute the DS tuning difference to pruning.

Native counts are **0/0/11/0** for delivered DS18B20, **0/0/42/0** for delivered IR and **0/0/36/0** for delivered EEPROM, in opens/blocking/warnings/exclusions order. The stock negatives retain **1/6/42/0** and **2/3/36/0**. All retain seven original ignored checks. No output is whole-project DRC clean. Required full-schematic, original-rule, Default-map, field/PRL, invariant and own-final candidate-hash checks remain bound to each route and export; negative outputs were not accepted or exported as successes.

These inputs have no locked source routing and therefore supply no positive protected-copper control. Current positive protection evidence remains in the separately linked [Native cohort](../evidence/runtime058-native-milestone-001.json) and [GUI/install](../evidence/runtime058-install-existing-001.json) packets. No electrical suitability follows from a net name, fewer vias, a zone connection or DRC acceptance.

Three previously exposed inputs with unclosed ancestry/title questions cannot support a population completion estimate, a meaningful family-independent confidence interval, broad superiority or an unseen first-attempt claim. All registered arms remain in the denominator; the separately documented unsupported acquisitions remain unsupported. Broader licensed development coverage, frozen-policy untouched confirmation, alternative-engine evaluation and actual human cleanup remain open.

## Complete costs

Each cell is complete external **wall / CPU seconds**, including conversion, attempts, selection, validation and delivery. Nested method/Native samples are already included and must not be added again.

| Method | DS18B20 | IR | EEPROM |
|---|---:|---:|---:|
| B0 | 84.39 / 82.21 | 13.48 / 13.00 | 15.88 / 17.82 |
| B1 | 86.81 / 84.35 | 95.05 / 93.28 | 100.80 / 105.74 |
| B2 single tuned | 87.75 / 84.88 | 94.42 / 92.99 | 101.55 / 106.24 |
| B2 restart | 120.93 / 116.17 | 140.34 / 140.68 | 160.30 / 178.21 |
| C default | 28.45 / 25.83 | 33.57 / 32.60 | 40.70 / 45.36 |
| C Improve | 95.99 / 93.30 | 278.63 / 263.69 | 442.70 / 426.54 |

All 18 exits total **2021.74 wall / 2002.89 CPU seconds**. Additional administration: freeze/query **1.80 / 1.69**, stored-evidence reporting **5.41 / 4.36**, retention **0.28 / 0.25**. Reporting and retention ran no Native or routing work. These sum to 2029.23 / 2009.19 seconds for the recorded arms and those three administrative executions. Research, authoring, AI review and interactive pauses are additional and partly unmetered, unknown rather than zero. Build, full209, Native, GUI and installation prerequisites retain their separate costs in the linked packets; old 057 costs are not rewritten or transferred into these arms.

## Reproduction and decision

The [frozen child record](../evidence/runtime058-installed-three-family-001-notes/frozen/frozen-children.json) preserves all 18 exact executed command arrays, protocol hashes, output paths and complete timing logs. The packet retains the reviewed freezer, unchanged shared reporter, report launcher and retainer. Source revisions/rights and all six policies are pinned in the [population](../evidence/runtime058-installed-three-family-001-notes/frozen/population.json) and [source manifest](../evidence/runtime058-installed-three-family-001-notes/frozen/sources.json).

The original local recipe is:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
# For each row, in recorded order: /usr/bin/time -lp + argv;
# send stdout/stderr to that row's two recorded files.
.venv/bin/python -B -m json.tool \
  .runs/runtime058-installed-three-family-001/frozen-children.json
```

Do not rerun into those used output roots or rewrite the old evidence. A new execution needs a fresh registered base, reviewed controller pin, exact licensed inputs/toolchain, current installation qualification and frozen administration HEAD. The commands are a host-bound reproduction record, not a claim of clean-machine or one-command independent reproduction; that release gate remains open. The [normal CLI](quickstart.md) and [GUI](gui-workflow.md) do not require this research archive.

**Decision:** keep corrected-standard as the default and Improve as a narrow opt-in mode. Do not select a different default per board. Preserve the verified candidate and all failures/warnings. Natural-time return safety, the larger exposed CellScan regression and unrelated development breadth require separate evidence; none is asserted by this completed comparison.

Subsequently, the [separate 90-second return control](../evidence/runtime058-natural-expiry-001.json) timed out during proof/publication, and the [archived-positive reader control](../evidence/runtime058-archived-receipt-defect-001.json) demonstrated a receipt-identity bypass. The [working source fix](../evidence/routing-receipt-identity-repair-001.json) has targeted tests and an actual CLI refusal; it is not a new Native/GUI-qualified artifact. These safety gates block promotion of058. The canonical final evidence and all outcomes in this comparison remain unchanged.
