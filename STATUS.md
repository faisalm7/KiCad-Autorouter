# Current status

October15,2026. Existing local Mac checkout `/Users/faisal/Projects/KiCad-Autorouter-local`, branch `rebuild/local-20261010-015447`. Latest verified checkpoint `83c536e434e41bf52fe93a729c8606028216ae7c`. The project is experimental; representative evaluation and release gates remain open.

The CLI routes locally without an AI account or route-time network using pinned KiCad10.0.0, Freerouting2.5.0 and Java25.0.2. [Start here](START_HERE.md), [saved preferences](docs/routing-preferences.md), [KiCad workflow](docs/gui-workflow.md), [handoff qualification](docs/experimental-rc.md). Original rules, geometry, protected copper, warnings and ignored checks remain authoritative. Candidates are separate projects; no live overwrite, tested undo or unsaved-buffer inspection promise.

## Current experiment and implementation

[Actual Universal450](evidence/universal-own-low-pruning450-failure-001.json) remains rejected: final Native0opens/0blocking/81warnings at4415.567736mm/25vias, but final publication201.066591 exceeded200seconds. [Actual750](evidence/universal750-prelaunch-failure-001.json) remains rejected: standalone tuned B2longlow200 passes4556.133635mm/25vias/0opens0blocking81warnings; C finds4424.967736mm/25vias but a budget-expired trial leaves an unmatched DRC binding and immutable owned PRL. The final native counts do not override that evidence failure. Whole750276.146222wall293.111052CPU; latest C623.132819wall626.458838CPU includes all prior attempts. The new950 result below is separate; neither failed result is retroactively accepted.

The native optimizer reserves25seconds for final checks/publication; legacy placement keeps15. A measured preparation defect is fixed by rechecking remaining wall/CPU after source/storage inspection, and both the global budget and local trial deadline after candidate preparation. An expired DRC refuses before copying, freezing PRL or writing worker journals. Unknown/post-entry cleanup still fails closed; no acceptance or census rule was relaxed. [Source/regressions](evidence/native-trial-preparation-source-001.json): four old defects reproduced,110targeted controls pass including CPU-only cases. Full088 passes1378software controls128.452238wall119.028614CPU at e5135f5; software counts are not routing quality.

[Actual Universal950](evidence/universal-preparation950-actual-001.json) PASSES the final enclosing/source/material/readback gates: own fresh C200 finds4435.181635500422mm/25vias/0opens0blocking81warnings, with nine improvements. Retained tuned B2longlow200 is4556.133634603698mm/25vias with the same findings. C saves120.951999mm, with no via change; it costs more. Whole new232.029065wall218.952481CPU plus5startup/publication, within250. Equal cumulative950 rows: B0rejected237.270062wall226.041596CPU; B1rejected237.045079/240.381878; B2accepted461.700724/506.589491; Caccepted860.161884/850.411319. All earlier failed450/750costs remain. All52recorded workers and12actual final observations preserve source/rules/fullSCH/class/refill/warnings/fiveignored; Ccandidate4832519fc5820d98ae431dce10adf564c55504ac638de38aeb626ca5b5fbaf96, reportd942f85612b9a7e56286b33021cbb6fecd96263f0f8d6c4c46d3951b98eb812f. Nineaccepted exposed gains now; no broad/independent/untouched/speedupclaim. Installation035 and changed-source preview/export remain pending.

## Accepted exposed routing comparisons

Every result retains actual final Native/full-schematic checks, original design constraints and all inherited findings. C obtains and pays for its own incumbent. Track length is a geometry proxy.

| Exposed circuit | Corrected B1 mm/vias | Strong B2 mm/vias | C mm/vias | Final opens/blocking/warnings | Equal wall/full-CPU cap |
|---|---:|---:|---:|---|---:|
| NUS tutorial |71.884325/2|71.769712/2|35.128656/2|0/0/10|120s|
| Sonde |752.095975/0|746.345274/0|669.121554/0|0/0/26|120s|
| LED support |88.179474/0|88.179474/0|63.692565/0|0/0/7|120s|
| ArcDice |636.989098/0|602.587602/0|581.295202/0|0/0/26|120s|
| Analog fixed High |227.687488/1|229.480656/0|197.775756/0|0/0/14|120s|
| CellScan |5468.311758/111|5468.311758/111|5293.194194/111|0/0/209|360s cumulative|
| Roller |50.117649/0|50.117649/0|36.049463/0|0/0/1|240s cumulative|
| IR obstacle |170.232815/3|166.287122/3|149.375637/3|0/0/42|300s cumulative|
| Universal Shift |rejected1open1thermal|4556.133635/25|4435.181636/25|0/0/81|950s cumulative|

Nine exposed configuration-specific gains beyond the measured adapter/tuned or restart baselines. Roller ties the raw-DSN B0 safety wrapper. These are not independent statistical replications: zero independent pedigrees or untouched confirmation are established. No broad completion superiority or speedup is claimed. IR C is slower than its B2. Analog's older shorter route/one-via result is a tradeoff; its combined exploration exceeds120. Failed budgets, warnings and invalid shorter candidates stay visible in [claims/evidence](evidence/claims.json), [IR003](evidence/ir-native300-003.json), [Roller240](evidence/roller-normal-native240-001.json) and the retained history.

## Usability and qualification

Persistent scope, allowed new layers, bounded time and optimization settings are implemented. Selected/partial routing protects existing or locked copper; unsupported combinations refuse. Preview, accept/reject test intent, fresh native export and real cancellation have actual controls. [Four protected paths](evidence/normal-selected-native001-actual-001.json), [actual SIGINT/cleanup](evidence/normal-selected-cancellation002-native-001.json), [IR workflow/GUI](evidence/ir-current-workflow-gui001.json), [Roller workflow002](evidence/roller-current-workflow002-native-001.json), [complete-schematic LED GUI006](evidence/normal-prl-export-gui006-001.json). GUI tests preserve authoritative exports; any disposable project metadata migration is recorded and unvalidated. Test intent is not human PCB approval.

[Installation034](evidence/installation034-native-001.json) is the latest executed installation: a local source distribution/independent venv,22offline commands,144focused controls, real Native60mm/0via/0findings and all seven reader groups. It predates the new reservation/preparation fixes. New035 is prepared for current code, with244planned focused controls; nothing is counted as executed until it runs. SameMac/apps/cache, no freshOS/full installed suite or installed larger-board claim.

## Broader coverage and open gates

Unsupported and rejected inputs remain visible: SUNX duplicate mechanical-hole/DNP schematic parity; CP2102 fixed pad gaps.18mm versus required.2mm plus missing footprints; PAW thermal/connectivity failures; Audio/Navigation inherited courtyard errors; UV schematic/area constraints; ColdFire4Cu/class/thermal; custom pads, net ties, genuine footprint areas, complex edges/hierarchy and advanced rules outside qualified scope. [SUNX](evidence/sunx-original-native-001.json), [CP2102](evidence/cp2102-original-native-001.json), [PAW](evidence/paw-minimum-native002-001.json). Native-connectivity-only and whole-GND-deletion hypotheses failed real native checks; their shorter invalid routes are not gains.

Additional DS18B20 temperature-interface source has an explicit pinned publisher design grant and a five-original/six-file native-packet draft. It is not integrated/acquired/native-tested. Missing standalone license body, optional models/embedded-asset title and ancestry caveats remain; public CAD redistribution is deferred. No models, firmware or upstream scripts execute. Other new rights leads retain concrete blockers.

The30–50representative-family audit, untouched family-disjoint confirmation, actual human PCB review and electrical/physical validation remain unmet. The human review pack is blank; nobody was contacted. No chatbot or trained model is justified. Formal release/tag/package, spending, external contacts, private uploads and background/auto-resume loops remain unauthorized.

## Backups and continuation

Audited source/small evidence has verified GitHub checkpoints. [Full restoration003](evidence/backups/full-restore-current-2c35f5e.json) verifies287340files/9277781494B/allrefs/independent empty-repository restore/restored CLI through2c35f5e, within finite300kfiles/directories/9GiB/80MiBreceipt/192MiBchain guards. Raw450/750/current-source/950/installation artifacts are after that cutoff and await the next verified incremental. Owner chose on-Mac-only raw backups, which do not protect against disk failure. No evidence was deleted.

Continue [PLANS.md](PLANS.md) from actual files/processes. The950native command has completed successfully; do not rerun it. Next qualify current installation035 and existing review/export helpers on an actually accepted candidate, checkpoint results, then incremental backup and the new source-family gate. Do not repeat completed Native workers/readers. Full restoration is reserved for major milestones, backup-system changes and before release.

Earlier chronological status and requirement observations are preserved verbatim under [history](docs/history/2026-10-15-native-preparation/STATUS.md); their old next-step statements are superseded by this status and actual receipts.
