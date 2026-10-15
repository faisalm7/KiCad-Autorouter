# Local experimental source handoff

Use the existing local checkout. The current installed qualification is source
`dddc3415f06cb4054c3f3355093826c074feada7`, with its source distribution and venv
at `.runs/installation-030/checkout`. Keep that environment at its tested path.
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
| Current source integration | [mandatory import/refill guards](../evidence/normal-selected-saved-refill-source-001.json), [final observer/full074](../evidence/cancellation-observer-source-001.json) | Original selected copper and saved-refill route nets remain exact; strict stale-result checks; source/software controls are not routingquality |
| Current installation | [installation030](../evidence/installation030-native-001.json) |22offlinecommands/72fixed controls,20775original/615initialdistributionfiles; actual Native60mm/0via/0findings; existingMac/apps/cache |
| Selected installed checks | [installation030](../evidence/installation030-native-001.json) |176targeted installedchecks; one exact67060Bhistoricalsource test-only fixture separately copied; no fullsuite/freshOS/package claim |
| Persistent settings/pruning | [actual preset/stale controls](../evidence/pruning-preferences-native-product-003/SCOPE.md) |Whole/native/tuned/both/source_all; fresh own incumbent and all failed compute charged |
| Normal preview/export/cancellation | [actualfourpaths](../evidence/normal-selected-native001-actual-001.json), [missing-only realcancel002](../evidence/normal-selected-cancellation002-native-001.json) |Protected22signal NUS0/0/10/0, authoredzero/selectedlocked/legacywhole0/0/0/0; testintents/freshNativeexports and realSIGINT/cleanup; original001observerfailure/cost retained, no humanapproval |
| Actual GUI | [complete-schematic GUI006](../evidence/normal-prl-export-gui006-001.json) |Actual refill/parity/all filters, zero GUI findings/five original ignored checks; isolated CLI library warnings remain; no live apply/undo or human approval |
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

Representative30–50family audit, untouched pedigreed confirmation,
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

The [major restored snapshot](../evidence/backups/restore-minimum-installation029-fdbff8a.json) verifies272571files/8423268906B, allGitrefs and restoredCLI throughfdbff8a. The [later verified incremental](../evidence/backups/incremental-contact-flipper-a661348.json) covers273504files/8442841170B througha661348 with its delta integrity check. New004005/normalworkflow/full071–074/installation030 are after those cutoffs and await the next incremental; no new fullrestoration is implied.

The [verified current incremental](../evidence/backups/incremental-normal-selected-installation030-3ec32b5.json) now includes actual004005, currentnormalworkflows/cancellation andinstallation030 through3ec32b5:276071files/8571402650B, delta integritypass, boundedchain2. This closes that pending incremental, without implying another fullrestore. Later006preparation is aftercutoff.
