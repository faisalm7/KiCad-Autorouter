# Installed comparison007 C_single: bounded cost diagnosis

**Recommendation: keep the existing 25-second finalization reserve and original-proof guards. One small general optimization is justified as a hypothesis: reject an already-proven warning regression before launching the separate metrics process. Larger apparent overheads are not attributed to a cause by these records.**

This task read only the current installed C_single subtree and the implementation called by CLI `improve`. It ran no Native/JVM, tests, reroutes, profiler, old-context qualification, archive scan, or delegation. Only this note was written. Source inspection is not new validation or a fresh timing experiment.

## Current outcome and exact scope

Read base is `.runs/runtime-directory-003/runtime/.runs/comparison007/C_single-enclosure/C_single/`; its job is `autorouter-gui-53541215dd8c4728a3d65fc312ccf17c/`. The installed runtime identifies build source `df20598f2f3089bb58495e9236ccdbae9f58cebf`, source provenance `runtime-directory-v1`. The CLI Native branch at `autorouter/__main__.py:174–178` calls `autorouter.strategy.prune`; the receipt says `proposal_policy=single`, ordinary tuned incumbent, no stronger-width policy. Placement-search allocation is not this path.

At read time the subtree's workflow `result.json` says completed, accepted, and workflow_delivered. Route and separately validated export both record **634.6433493547064 mm, 0 vias, 0 opens, 0 blocking, 26 warnings, 0 exclusions**; candidate SHA256 is `f49e456e6b926b3053a2394c86b7a9be1f7ca5118e27c210fe755d3e59654245`. It is not whole-project DRC clean, actual GUI qualification, human review, or electrical/physical validation. This task did not inspect the enclosing process outside the permitted subtree; the workflow explicitly requires complete external exit accounting. Do not substitute the prepublication sample for that final gate. Comparator figures supplied by the lead were not independently reread here.

## Recorded costs, without inventing phase attribution

All figures below are actual retained records. Inner accounting samples precede final guarded writes/returns.

| Scope | Wall s | CPU s | Meaning |
|---|---:|---:|---|
| Incumbent route receipt | 12.223932 | 12.065269 | 752.095975 mm / 0 vias accepted incumbent |
| Incumbent subprocesses, 8 steps | 11.601802 | 11.330337 | Includes engine 5.691297 wall / 7.625210 CPU |
| Incumbent validated checkpoint | 13.709601 | 13.524640 | C elapsed/full observed CPU including its setup/readback |
| Twenty trial subprocess sequences, 56 steps | 54.858748 | 30.162659 | Both rejected and accepted trials retained |
| Sum of trial start→finish intervals | 62.141217 | unavailable | Does not include every inter-trial/checkpoint gap |
| Final three subprocesses | 2.894996 | 1.604360 | Refill 1.210977, DRC 1.262513, metrics 0.421506 wall |
| Stored whole pruning receipt | 79.959955 | 54.439097 | Parent CPU 11.341741; child CPU 43.097356 |
| Complete CLI `route.process.json` | 87.286161 | unavailable | Actual CLI exit 0; GUI-style process receipt records wall only |
| Workflow method interval | 87.836418 | 61.276279 | Lead harness's outer method sample, wider than route receipt |
| Whole workflow prepublication sample | 146.956511 | 116.156035 | Required final enclosing exit remains separate |

Trials comprise 15 accepted improvements, four DRC rejections, and one quality rejection. Trial processes split into 20 refills **23.731247 wall / 11.391944 CPU**, 20 final DRCs **24.774001 / 12.515716**, and 16 metrics processes **6.353499 / 6.254999**. Full Native validation dominates the measured trial subprocess wall time; this note proposes no deletion of those checks.

Other recorded CLI wall times: preview 0.143916; review 12.420680; choice 8.041263; export 18.134946; export-check 8.117609. Their sum with route is 134.144575 seconds. Export's own stored sample is 13.429140 wall / 11.493173 CPU, with three fresh Native subprocesses totaling 3.106888 wall / 1.669907 CPU. These nested samples must not be added to their containing CLI times.

Unattributed residuals: all stored pruning step wall sums to 69.355546; the difference from stored pruning wall is **10.604409**. Trial start→finish intervals exceed their subprocess wall sums by **7.282469**. The complete route CLI exceeds stored pruning wall by **7.326206**. Those intervals include differing scopes/guards, file work, Python work, supervision, receipt publication and return, but the records do not divide them by function. Parent CPU is not proof that hashing, parsing, storage inspection, original checks, or any particular reader is redundant. No large readback/cache correction follows from these gaps.

## Reserve conclusion

Finalization began at **76.758578 seconds** of the 105-second route budget, leaving **28.241422 seconds**. Its work stage requires at least 12 seconds remaining and all final acceptance caps remain strict. The actual three final Native subprocesses totaled **2.894996 wall / 1.604360 CPU**; final_validated checkpoint was 79.956152 seconds. The 25-second reserve was not exhausted, and C's incumbent used only 12.223932 of its assigned 79.780323 seconds. No evidence here supports reducing the reserve, increasing the cap, borrowing a completed comparator incumbent, or changing incumbent allocation. More budget could change proposal count, but that is an untested strategy choice.

## One demonstrated avoidable cost and bounded hypothesis

`strategy.py:884–898` launches Native metrics for every Native-valid trial before `_improves` at lines 212–217 evaluates the necessary condition that candidate warning signatures are a subset of the current incumbent's signatures.

Actual **trial-0002** is the counterexample. Its base is accepted trial-0001 (734.817575 mm / 0 vias, 26 warnings). The candidate has 720.562303 mm / 0 vias and 0 opens/0 blocking, but adds two `track_dangling` warnings for UUIDs `e72fb134-015b-438e-820b-3eb0c420509d` and `fb96c754-7b0f-4773-a868-4d85de0f1678`, reaching 28 warnings. Consequently the warning-subset conjunct is false regardless of any length/via measurement. The code nevertheless ran a successful `metrics` child costing **0.395878417 wall / 0.388274 CPU**, plus 0.005719 supervisor CPU already included in parent accounting, before recording `quality_rejected`.

Hypothesis: initially restrict to **single** policy. After the same full `validate_candidate`, candidate-hash binding, original freshness and protected/rule checks, evaluate the exact existing warning-signature subset. If false, retain the full Native evidence and record a quality rejection with an explicit metrics-not-measured reason; skip only the separate metrics subprocess. Retain candidate/original freshness calls at the same decision boundary and all finalization/refill/DRC/metrics, immutable-source, rule, PRL, tool and publication guards. Candidates whose warning signatures pass continue through current metrics and `_improves` unchanged. No warning is ignored or baseline expanded.

This is a scheduling change for a necessary rejection predicate, not permission to accept from partial evidence. Existing receipt consumers must explicitly support the missing rejected-trial metrics reason; do not silently fabricate metrics or omit evidence expected by a current reader. Single policy avoids changing feedback/adaptive control flow, whose replay currently consumes valid-trial metrics. A future bounded implementation should show that warning-subset failures preserve the incumbent, warning-clean candidates retain their current metrics/native path, stale/tampered source/candidate/native evidence still refuses, final acceptance stays unchanged, and the ordinary delivered budget includes all work. No implementation or tests ran in this diagnostic.

The direct opportunity demonstrated on this run is one approximately **0.396-second** process, not the entire 6.353499 seconds of metrics, the 7.326206-second CLI tail, or a promised additional successful proposal. Keep the same work cutoff and 25-second reserve in any later experiment. A speed/quality gain needs a separately frozen fresh comparison; do not revise completed comparison007 accounting.

## Read pins

Paths below are relative to the read base/job described above unless otherwise stated.

| Record | SHA256 |
|---|---|
| workflow | `7afeee57fd6a8a95cf56db01b42fc3f6d76c12155d9816c1b011d55ef3c5f785` |
| route | `949d8208aa9401ed475edc86cf80ad895f77de2967f704378b375cf79dc104bd` |
| trial0001 | `387e957ace1309c56d0c9a8021bef4ad30cb456c4e68fd953c1f59b6aa25dd0e` |
| trial0002 | `7f24fc569ce839178e41908d1e596890b8db836494abd31e03f380adfc5a1a72` |
| export | `789c4eafce61c7f00dc4eec0f3e601da673d843c9cc992c3c56fc2ff07f0a1e8` |
| implementation | `8a9ef351ff51df414245977d53cf68422d82fe4f9c94ccd8305c7025de073ea3` |
| CLI | `0b7928c455fea4c2632d91c7fe3888301d946d1258b34b0918bd5c446feaf62f` |

These pins identify the exact reads, not independent authentication or a full-tree rescan. Raw records remain in the installed C_single subtree; the lead owns final enclosing-exit qualification and backup. Stop here; no rerun or production change was authorized by this diagnostic.
