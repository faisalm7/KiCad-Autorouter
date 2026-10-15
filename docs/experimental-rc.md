# Local experimental source handoff

Use the existing checkout at `~/Projects/KiCad-Autorouter-local`. Routing runs
locally without an AI account or route-time network access. This is experimental
source; representative coverage and confirmatory release gates remain open.

[Start here](../START_HERE.md), [quickstart](quickstart.md), [saved settings](routing-preferences.md)
and [KiCad workflow](gui-workflow.md) describe the implemented commands. Whole,
qualified partial and selected routing, allowed layers, time budgets and
optimization preferences are persistent. Unsupported constraints or choices
block the task. Original rules and protected copper remain authoritative.

Candidates are separate projects. Preview, accept/reject test intent, fresh native
export and Control-C cancellation have actual controls. Save editor changes
first: this external workflow cannot inspect unsaved buffers or provide verified
live-editor undo. Test intent is not human PCB approval.

| Gate | Executed evidence | Current limit |
|---|---|---|
| Routing quality | [Nine exposed comparisons](../STATUS.md) | Fixed configurations and equal budgets within each comparison; Roller ties raw B0. No broad completion or speedup claim; zero established independent pedigrees |
| New optimizer scheduling | [Reservation source/full087](../evidence/universal-native-reserve750-source-001.json), [preparation regressions](../evidence/native-trial-preparation-source-001.json) | Native reserve25, legacy placement15; preparation CPU/wall/local deadlines rechecked. Full088/currentNative950 now qualify; [installation035](../evidence/installation035-native-001.json) and [current workflow/GUI](../evidence/universal-current-workflow-gui001.json) now qualify |
| Current larger-board failure | [Actual Universal750](../evidence/universal750-prelaunch-failure-001.json) | Old750 remains rejected at worker lineage; [new950](../evidence/universal-preparation950-actual-001.json) qualifies4435.181636mm/25vias vs4556.133635/25,0/0/81, all failed costs retained |
| Installation | [042complete](../evidence/installation042-native-001.json), earlier041/failed040 retained |6e68702b/22068source709installed/22offline82fixed117focused/all7groups. Actualdefault1000partial and explicit1007whole4Cu fullSCH/protected/innertrack/throughvia; reader277102592B<1GiB. SameMac/cache, no freshOS/fullinstalledsuite |
| Optional chains | [IR240 gain](../evidence/ir-chain-native240-actual-001.json), [Arc300 regression](../evidence/arcdice-chain-native300-actual-001.json) | Chains saves9.587788mm versus freshIRfeedback but loses11.582315mm onArc at matched allowances. Remains optional; no newfamily/generalizedgain/default promotion |
| Optional adaptive allocation | [IR240](../evidence/ir-adaptive-native240-actual-001.json), [Arc300](../evidence/arcdice-adaptive-native300-actual-001.json) | IR ties chains; Arc loses20mm to feedback. Every failed cost and historical control retained. Optional only; no default promotion or new circuit gain |
| Review and export | [Installed fourCu042](../evidence/installed-fourcu-workflow042-001.json), prior IR/Roller/Universal records | Eightactual plots/all4layers, softwareaccept/rejecttestintents, freshoriginal-rule/fullSCH export0/0/6/twoignored. No reroute/newGUI/liveapply/undo/humanPCB approval |
| Protected copper and cancellation | [Four real paths](../evidence/normal-selected-native001-actual-001.json), [actual cancel002](../evidence/normal-selected-cancellation002-native-001.json) | Exact protected signals/locked copper, SIGINT/cleanup. Sampled controls, no power-loss guarantee |
| Actual GUI | [LED006](../evidence/normal-prl-export-gui006-001.json), [Roller001](../evidence/roller-export-gui001-001.json), IR above | Real refill/parity/all filters; disposable GUI metadata changes recorded, authoritative exports exact. No human/electrical/physical approval |
| Current KiCad diagnostic | [FullSCH/hiddenfields](../evidence/native-schematic-hidden1007-001.json), [current042](../evidence/installation042-native-001.json) | Explicit1007 route/class/SES/import/refill/fullSCH/metrics plus installedsharedreader actualqualified onownedcontrol; default10.0.0 remains. Broaderfeatures/comparison/GUI remainunqualified |
| Four-copper classes | [Actual dual-version transport/full107](../evidence/four-cu-class-native-001.json) and [pad census](../evidence/four-copper-pad-count-actual-001.json) | Exact owned canonical modern4Cu/threeclasses/fullthrough/ROUTE+GND innertracks/SCH/protected10 and same-rule shorting negatives pass1000and1007. Sixwarnings retained; [Installed042](../evidence/installation042-native-001.json) alsoqualifies partial4/all10traces including1unlocked. No newfamily/gain/HFE/selected4/mask4 qualification |
| Restoration | [Compact/full chain](../evidence/backups/compact-full-chain-0e58f4f.json) | Full legacy006 plusnewcompactdelta2node restoration through0e58f4f:305403files/10491684184B/allrefs/restoredCLI; compactformat/310kfinitecapacity qualified. Receipt78974104B<80MiB; allsecurity/byte/chainguards retained. OnMaconly byownerchoice |

Every accepted comparison retains its actual final native reports, original
design checks, warnings and ignored checks. Unsupported boards and all failed
attempts remain in the population and evidence. Native acceptance, whole-project
DRC cleanliness and electrical/manufacturing approval are separate.

The current mechanism is deterministic native-validated pruning beyond measured
adapter/tuned configurations. Invalid shorter routes do not count as gains.
Native-connectivity-only and broader PAW probes failed their recorded native
constraints. No learned model or chat runtime is justified.

The representative30–50family audit, untouched pedigreed confirmation, actual
human PCB review and electrical/physical validation remain unmet. The human pack
is blank; nobody was contacted. Raw CAD/model redistribution remains excluded.
No formal release, tag or package was published.

Audited source and small evidence are pushed and independently read back on the
authorized development branch. Raw archives remain on this Mac by owner choice;
this does not protect against disk failure. Each receipt states its exact
cutoff. Full restoration is repeated at major milestones, backup-system changes
and before release; minor checkpoints use verified incrementals.

Earlier chronological handoff text is preserved in
[history](history/2026-10-15-native-preparation/experimental-rc.md).

Current additional temperature-interface source: [DS18B20 original](../evidence/ds18b20-original-native-001.json) passes real saved/fullSCH checks0/0/11/0/sevenignored with unchangedoriginalshell/source/PRL/rules. Saved nonfill/route AST migrations remain unqualified. [Actual fourarm comparison](../evidence/ds18b20-native240-actual-001.json) ties C/B2at35.511106323mm/0vias; broader support, not another gain. Full089 records its historical1387-method software qualification; later runtime changes and the current installed qualification have separate source bindings above.

The latest complete installed milestone is042 at6e68702b; prior041andfailed040 remain recorded. HFE original Native reports18net_conflict warnings and remainsrejected despite0opens/0blocking. FourCu transport and workflow qualification adds no unrelated circuit or measuredqualitygain.

The actual compact/full two-node restoration now covers0e58f4f, including current042/preview/export and earlier failures. It qualifies the existing compact helper and310kfinitefile capacity without changing byte/security/scope guards. Later drafts inside.local-backups are excluded from that frozen capture. OnMaconly byownerchoice; no diskfailure protection.
