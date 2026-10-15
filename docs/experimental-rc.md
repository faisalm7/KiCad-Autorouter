# Local experimental source handoff

Use the existing local checkout. The current installed qualification is source
`5f1ba4cea6bbec2a5a70e2cfd30942a53da47b9a`, with its source distribution and venv
at `.runs/installation-032/checkout`. Keep that environment at its tested path.
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
| Current source integration | [Full078/cache correction](../evidence/native-readback-cache-source-001.json) | Full first validation, complete byte witnesses and original constraints retained; software counts do not establish routing quality |
| Current installation | [installation032](../evidence/installation032-native-001.json) |22offline/73fixed plus8focused controls,20820source/639distributionfiles; actual Native60mm/0via/0findings, sameMac/apps/cache, zero supplements; failed reader001 plus missing-only tail002 retained |
| Persistent settings/pruning | [actual preset/stale controls](../evidence/pruning-preferences-native-product-003/SCOPE.md) |Qualified whole/native/tuned/both/source_all; own fresh incumbent and failed compute charged |
| Current preview/export | [Roller workflow002](../evidence/roller-current-workflow002-native-001.json) |Four real Native copper plots, accept/reject test intents and fresh fullSCH export;0opens/0blocking/1warning/9ignored, original001failure retained |
| Protected routing/cancellation | [four real paths](../evidence/normal-selected-native001-actual-001.json), [real cancel002](../evidence/normal-selected-cancellation002-native-001.json) |Exact protected signals/locked copper, actual SIGINT and process cleanup; no repeat or human approval |
| Actual GUI | [Roller GUI001](../evidence/roller-export-gui001-001.json), [LED GUI006](../evidence/normal-prl-export-gui006-001.json) |Real refill/parity/all filters; disposableGUI metadata changes recorded, authoritative export exact; no liveapply/undo/human approval |
| Routing improvement | [seven exposed comparisons](../STATUS.md) |Fixed configurations/equal budgets, Roller ties B0; zero established independent pedigrees, no broad completion/speedup claim |
| Broader source failure | [SUNX original001](../evidence/sunx-original-native-001.json), retained PAW/CP2102 and other failures |Source DNP/duplicate mechanical-hole parity findings and unsupported features remain blocked; no waiver or engine trial |

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

A later raw incremental througha1f8467 covers276271files. Current workflow002/SUNX/installation032 and new support records are afterthat cutoff. Actual8GiB refusal prompted only a finite9GiB byte limit; a new full snapshot/restoration is REQUIRED now and pending. Existing280000file/80MiBreceipt/192MiBchain guards remain. Owner chose on-Mac-only; no disk-failure protection or formal publication is implied.
