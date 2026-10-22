# Runtime057 default and Improve development comparison

The [completed public packet](../evidence/runtime057-default-improve-development-001.json), SHA `b7a38910aae7cdb3c9664fc662ce662afd454815891a19b09e70c45c83366abe`, records **11 deliveries and one stock IR Native rejection** across the same two exposed development families and twelve prospectively frozen arms. Default, B1, tuned, restart and Improve each delivered both families; stock delivered one. **There is no completion advantage over B1/B2.** Corrected-standard/B1 remains the default. The [historical056 study](benchmark-runtime056-default-improve.md) is unchanged.

The actual fresh installation is `.runs/runtime057 fresh install 001`, source `ac1a48c3b25b2217e0f8252e0e6da21905f144a4`, manifest `b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51`. It differs from the original057 manifest `9c667b15…` only in root. All54 immutable files, engine, source/build identity and rules remain unchanged. This is a same-Mac installed workflow qualification, not a new family, holdout, tuning cycle or cleanOS test. [Native](../evidence/runtime057-native-milestone-001.json), [installation](../evidence/runtime057-install-existing-001.json) and [actual GUI091 slice](../evidence/gui-runtime057-install091-delivery-001.json) retain their separate scopes; the comparison itself is CLI-only.

| Family | Arm | Delivered | Copper mm / vias | Complete wall s | Complete CPU s |
|---|---|---|---:|---:|---:|
| DS18 | Cdefault | Yes | 39.512 / 0 | 35.69 | 27.14 |
| DS18 | B0 stock | Yes | 35.514 / 0 | 85.42 | 82.37 |
| DS18 | B1 corrected | Yes | 39.512 / 0 | 85.14 | 81.83 |
| DS18 | B2 single tuned | Yes | 39.498 / 0 | 84.17 | 81.50 |
| DS18 | B2 restart portfolio | Yes | 39.498 / 0 | 119.61 | 113.93 |
| DS18 | Cimprove | Yes | 39.498 / 0 | 110.39 | 105.98 |
| IR | Cdefault | Yes | 167.425 / 2 | 33.76 | 32.31 |
| IR | B0 stock | No | Unranked negative | 13.40 | 12.80 |
| IR | B1 corrected | Yes | 167.425 / 2 | 93.24 | 91.85 |
| IR | B2 single tuned | Yes | 167.425 / 2 | 92.90 | 91.53 |
| IR | B2 restart portfolio | Yes | 175.690 / 0 | 138.30 | 138.42 |
| IR | Cimprove | Yes | 138.267 / 2 | 320.96 | 305.93 |

Values are rounded here; the [stored sanitized report](../evidence/runtime057-default-improve-development-001-notes/facts/report.json) preserves exact metrics and every outcome. DS18 stock is shortest. DS18 Improve used zero pruning trials and returned its tuned incumbent. IR Improve used18 trials and shorter copper at the same two vias as B1/B2 single; the restart winner uses zero vias with longer copper. Neither geometry tradeoff establishes electrical suitability, engineer cleanup or broad route quality.

DS18 deliveries retain Native0/0/11/0 and IR deliveries0/0/42/0. Stock IR is a completed, validated negative at1/6/42/0 and has no delivery; its geometry is not ranked. Each family retains seven ignored checks. Original-source, full-schematic, refill, Default dimensions, fields/PRL, candidate hashes and process/custody evidence remain bound to each actual final, including Improve incumbent/trials/parent/export. Original protected-route count is zero, so this is not a positive protection control. Warnings/ignored checks are not waived or electrical approval.

Each arm had420s routing,450s method wall/fullCPU,600s complete wall/fullCPU,120s fresh export and unchanged30s review/choice ceilings. Improve's420s includes its tuned incumbent, trials and25s return reserve. The fixed three-way restart portfolio uses via_default/via_low/via_high, balanced allocation,30s per-trial readback and15s root finalization reserves. No arm was dropped, rerun or stitched, and no source/policy/budget changed after the first arm.

The twelve complete external exits total **1212.98s wall /1165.59s CPU**. These include startup, conversion, selection, Native checks, review, choice, export and readback. Method, trial and process samples overlap those exits and are not added again. B0 retains shared fidelity/protection/Native safeguards, so it is not untouched official-plugin qualification. Baselines use sealed API delivery while Cdefault/Improve use actual product CLI authority paths; the workloads differ and these timings support no generic speed claim.

| Separate additional event | Wall s | CPU s |
|---|---:|---:|
| Setup001: pre-query schema refusal | 0.57 | 0.44 |
| Setup002: pre-query classification-schema refusal | 0.47 | 0.44 |
| Setup003: pre-query export-header assumption refusal | 0.59 | 0.54 |
| Setup004: successful freeze/query | 1.91 | 1.75 |
| Initial35 parser regressions | 7.93 | 7.59 |
| Final36 parser regressions | 9.19 | 8.89 |
| Actual057 pure metadata admission | 0.43 | 0.37 |
| Successful shared report invocation | 3.24 | 2.66 |
| Public retention | 0.30 | 0.24 |

The first three setup failures launched no Native or engine. Full207/build/Native/install/GUI costs are separately linked in the packet; authoring, AI review and whole interactive costs are partly unmetered, unknown rather than zero. No nested samples are summed into an apparent total.

The [population](../evidence/runtime057-default-improve-development-001-notes/frozen/population.json) SHA is `cb39bc8fd63b77c44f5ee96bb0d9bdf5f8571500f53c91cf19c24e0904bc5e4e`; [frozen children](../evidence/runtime057-default-improve-development-001-notes/frozen/frozen-children.json) SHA is `aeb1379bb7e34066517043c4a9dd517a5de45e1100044892ce696db7ed45b485`. Execution administration was `ac6575b6ee5c26bfce557859a0d0ec8653208046`. The [retained identity porter](../evidence/runtime057-default-improve-development-001-notes/administration/freeze-runtime057-default-improve-development-001.py) and [report launcher](../evidence/runtime057-default-improve-development-001-notes/administration/run-runtime057-comparison-report-001.py) preserve the actual setup and final invocation. All six execution controllers/enclosure and the reporter are byte-identical to056; only the strict IR dependency metadata adapter changed.

Recorded per-arm execution used the following shared command, with each exact path/hash taken from `frozen-children.json`; its12 manual commands also specify the separate outer logs:

```sh
/usr/bin/time -lp .venv/bin/python -B scripts/enclose_current_comparison.py \
  --protocol ABSOLUTE_FROZEN_PROTOCOL --protocol-sha256 EXACT_PROTOCOL_SHA
```

Reporting used the public `scripts/report_current_comparison.py` with pinned population/children, a fresh output and `--public-sanitize`, enclosed by the retained launcher using the existing runner. It completed exit0/cleanuptrue/untruncated; report SHA `566f4c3d2a6e5d4747cd4b21516dcc2ba204e90f9c65bc4e212ffc74df0b72ad`, process SHA `718e9480e72f95ea1b6093b1f262942bfe2b0b668f1d83b5ccc189240f01d22e`. These are completed exclusive paths, not commands to overwrite or rerun. A new prospective replication needs a fresh namespace and the pinned runtime, dependencies and licensed private source caches; public sanitized facts are not a CAD/raw-data distribution or full restore.

Broader30–50 licensed unrelated development families, genuinely untouched frozen-policy confirmation, engineer cleanup, physical/electrical review, full GUI/exact queued timing, Windows and restoration gates remain open. The [separate EEPROM six-arm study](benchmark-runtime057-eeprom.md) is now terminal with4deliveries, stock Native rejection and Improve export-budget failure. It is not a result in this two-family cohort or electrical/independent-ancestry approval. This study authorizes no default, release or general-superiority change.
