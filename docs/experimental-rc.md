# Local experimental source handoff

Use the existing local checkout. The current installed qualification is source
`663cd1cb5454958384c7d6d8e28a71a7e8a08d92`, with its source distribution and venv
at `.runs/installation-027/checkout`. Keep that environment at its tested path.
Normal routing runs offline without an AI account. This is an experimental
source handoff; representative coverage and confirmatory release gates remain.

[Start here](../START_HERE.md), [quickstart](quickstart.md),
[saved settings](routing-preferences.md), and the
[KiCad separate-project workflow](gui-workflow.md) explain the usable commands.
The normal workflow snapshots the complete project, preserves original rules
and protected copper, produces a separate candidate, and requires fresh native
validation. Preview, accept/reject intent, export and Control-C cancellation are
implemented. Source-editor save/close steps remain necessary because this
external workflow cannot inspect unsaved buffers or provide live-editor undo.

| Executed gate | Evidence | Limits |
|---|---|---|
| Current source integration | [fixed-placement source/full064](../evidence/fixed-placement-ses-source-001.json) | Actual48nm SES pose change fixed without tolerance; software checks are not routing-quality evidence; failed062063 retained |
| Current installation | [installation027](../evidence/installation027-native-001.json) |22offlinecommands/72fixed controls,20676original/554initialdistribution files and actual Native60mm/0via/0findings; existingMac/apps/cache |
| Selected installed checks | [installation027](../evidence/installation027-native-001.json) |232successes+12setup errors, then12missing-only successes after101supplemental authored fixtures;256attempts, no fullsuite/freshOS/package claim |
| Persistent settings/pruning | [actual preset/stale controls](../evidence/pruning-preferences-native-product-003/SCOPE.md) |Whole/native/tuned/both/source_all; fresh own incumbent and all failed compute charged |
| Normal preview/export/cancellation | [actual current workflow](../evidence/normal-prl-native-workflow-001.json) |PRL/rules remain exact; actual0/0/7/0 positive,9/0/7/0 invalid, fourSVG workers and realengineSIGINT/cleanup; no human approval |
| Actual GUI | [installedLED GUI003](../evidence/installed-led-export-gui-003/SCOPE.md) |Earlier actual refill/parity/allfilters; later access remains locked, no newGUI/liveapply/undo claim |
| Routing improvements | [six exposed circuit comparisons](../STATUS.md) |Configuration-specific length/via evidence under equal per-comparison budgets; zero established independent pedigrees, no broadcompletion/speedup claim |
| Broader-board failure | [PAW exact-import failure](../evidence/fixed-placement-ses-native003-001.json), [via-low failure](../evidence/paw-via-low-native-001.json) |Native10opens and14opens; originalformat remains blocked, all17warnings and constraints retained |

Whole, qualified partial and selected routing, allowed new layers, time budgets
and optimization preferences are persistent. Use `settings-init` then `route`
or `improve` as described in the preferences guide. Locked copper remains
protected. Unsupported geometry, rules and settings combinations block the task;
no preference weakens an original design constraint.

The current routing gains come from deterministic native-validated pruning
beyond the fixed measured adapter/tuned configurations. A candidate's shorter
geometry is useful only after original-rule native acceptance. The
native-connected-only alternative failed a real thermal constraint. The
broader PAW via-cost probe also failed; neither invalid shorter routes nor
software test counts count as routing improvement.

Representative30–50family audit, untouched pedigreed confirmation, latest GUI,
actual human PCB review and physical validation remain unmet. The Analog review
pack is prepared but blank; nobody was contacted. No learned model is justified
or required. Third-party model/asset and ancestry rights remain incomplete, and
raw board/model redistribution is excluded. No formal release/tag/package,
contacts, spending, private uploads or automatic background continuation occurred.

Audited source and small evidence are pushed and independently read back on the
authorized development branch. Unique raw artifacts and archives remain on this
Mac by explicit owner choice. Backup/restoration receipts state their exact
cutoff; a local second copy does not protect against disk failure. Later prepared
or executed artifacts do not inherit an older cutoff.

The [current major restored snapshot](../evidence/backups/restore-fixed-placement-installation027-2bcebf.json) verifies269340files/8164238130B, allGitrefs and restoredCLI at2bcebf. Laternewsource/retained-plane preparation and execution are outside that cutoff.
