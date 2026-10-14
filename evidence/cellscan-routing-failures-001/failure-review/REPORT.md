# CellScan completed-run failure review

Read-only skeptical review of the already completed four-arm development batch. No KiCad, Java, HTTP request, source routing, source edit, or Git mutation was performed. Only this new private report directory was written. `result.json` and `inputs.json` pin 35 inspected records/code files; `source-warning-supplement.json` additionally pins the actual original-native receipt and checks warning identity with the existing strategy helper. All 209 original warning signatures remain, with exactly 12 new `via_dangling` signatures. The executable diagnostic uses the existing bounded JSON reader, DSN parser, engine-profile/journal checker and hashing helpers; it does not provide a new acceptance validator. Lead integration still must finish full final-candidate/original-design readback and comparative accounting.

## Exact findings

| Actual candidate | Native opens / blocking / warnings / exclusions | Assigned internal job deadline | Engine outcome |
|---|---|---|---|
| B0 stock | 32 / 3 / 221 / 0 | 27 seconds | Incomplete timeout |
| B1 corrected standard | 1 / 0 / 221 / 0 | 28 seconds | Timeout, 1 unrouted |
| B2 attempted `via_default` | 52 / 0 / 258 / 0 | 9 seconds | Timeout, 60 unrouted |
| C own fresh tuned incumbent | 43 / 1 / 253 / 0 | 10 seconds | Timeout, 51 unrouted |

All four actual engine argv/cwd/process journals pass the existing profile checker. Exit zero means the engine successfully wrote its partial SES, not that routing completed. Exact candidate/native-report hashes match their receipts. B2 attempted only Default; its remaining Low and High alternatives were skipped for insufficient budget and reserves. It is not a completed strong B2 portfolio. C never entered its pruning trial loop because its own incumbent was rejected.

The B1 source warning total is 209 in the bound full-schematic original record. Its 221 final warnings add exactly 12 `via_dangling` findings. Its sole open is `Net-(RED1-A)`, between the LED-side F.Cu track at (97.1282, 21.1282) and U7 pad 7 at (185.675, 37.065). The DSN still contains both terminals, `(pins U7-7 RED1-2)`. The SES for that net contains only the LED-side F.Cu stub and one via; it contains neither a U7-side wire nor an intervening B.Cu bridge. The imported final candidate preserves that same stub and via. This is concrete engine incompletion, not a terminal dropped by the adapter, an importer-created break, or a GND/zone thermal gap.

B1 progresses from 51 unrouted after pass 1 to 20, 15, 8, 3, 2, then 1 after pass 7. Passes 8–14 retain 1. The engine then logs last-mile removal of 24 blocking traces/vias around the remaining connection and reaches its deadline. The log does not identify the removed objects or prove a geometric solution. Its reported one remaining connection agrees with final native connectivity. An extra general optimizer pass was never reached, so this is not evidence that the optimizer degraded a previously complete route.

All 12 native dangling-via UUIDs match exactly one same-net SES via at the same coordinate, within the declared 0.000071 mm rounding tolerance. Each has only F.Cu center vertices in the SES and only F.Cu segment endpoints in the final candidate. They are unlocked. This establishes that the engine generated these objects and the importer preserved them. The endpoint correspondence is not an independent proof of copper connectivity or safe removal; the actual native findings remain authoritative.

The incomplete B2 Default and C results have additional unused fanout vias: 49 and 44 native `via_dangling` findings respectively. Native open counts need not equal the engine's internal unrouted-item count. The current thermal-only recovery cannot repair this signal connection. Existing pruning feedback accepts only new `track_dangling` findings on its eligible zone-net deletion proposal, and requires already valid connectivity. It does not implement incomplete signal routing or dangling-via cleanup.

## Geometry evidence and limits

At U7 pad 7, neighboring generated F.Cu geometry occupies the direct rightward channel. The RED1-A pad center is (185.675, 37.065), with a 1.95 × 0.6 mm roundrect. At its mid-height, the right boundary is x=186.65. A 0.2 mm GREEN1-A vertical track runs at x=186.9692, y=31.6658–37.5924; a 0.2 mm CELL1_POS vertical track runs at x=187.3892, y=28.1978–38.2807. Their center separation is 0.4200 mm and copper gap 0.2200 mm. An additional 0.2 mm track with 0.2 mm clearance on each side requires 0.6000 mm between those copper boundaries. These actual front-layer routes explain a plausible escape bottleneck and justify investigating shove/reroute or a different fanout ordering. They do not prove impossibility: other layers, alternative exit directions and changes to tool-owned routes remain available. No source reference route was examined.

## Next justified experiment

The first question is completion scheduling, before quality pruning. The current engine helper retains a 30-second graceful-stop reserve and 10-second native-finalization reserve; B2 and C additionally reserve 15 seconds at the parent level. In this small equal-budget execution allocation that leaves only 9–10 seconds inside their engines, versus B1's 28. Their larger incomplete counts therefore do not establish that tuning is intrinsically worse. Preserve these attempts and all their costs. Any new continuation must be prospectively frozen, use the unchanged source/rules/warnings/protection and common wall/full-CPU caps, and charge the previous failed work. If a meaningful remaining engine trial cannot fit, record that budget failure; do not silently remove reserves or label unattempted variants strong B2.

For the next new architecture experiment, a concrete hypothesis is: obtain an own fresh completion-focused route, then use actual native unconnected terminals to route a bounded affected signal net while retaining the other tool-owned copper and all protected copper. The falsifying outcome is continued native opens, new blocking findings/warnings, original-design drift, or a cap overrun. Compare with a competent corrected-engine completion/restart configuration receiving the same total budgets; a longer first engine run alone is a B2 scheduling improvement, not a new C mechanism. The current B1 candidate may be used as a diagnostic, but must not be supplied to C for free as its incumbent.

A separate narrow cleanup operator is justified by the 12 real unused fanout vias. Deletion must require a unique native-warning UUID, an exact matching tool-owned candidate via, unlocked/unprotected status, and fresh whole-candidate native refill/connectivity plus immutable source checks. It must preserve the exact original warning signatures; do not waive or suppress the dangling findings. This can improve a completed candidate's quality or admissibility, but cannot by itself connect U7 pad 7 and is not a substitute for completion. If adopted as ordinary adapter cleanup, grant it to B1/B2 too rather than attributing all gain to C.

## Minimal regression controls

1. Native positive: a redundant single-layer fanout via can be removed with identical original terminals/rules/protection and no connectivity loss. Native negative: deleting a real two-layer connection must introduce an open and reject.
2. Protected/locked via, original non-tool-owned via, wrong-net object, duplicated UUID and report UUID pointing to a pad/zone must refuse deletion. Report/candidate/source hash drift must reject before and after the operation.
3. Partial signal completion must preserve the other nets and designated protected routing. Native negative controls must catch a new short, moved pad/footprint, changed allowed layer, altered rule or exclusion, and cancellation before publication.
4. Retain all actual native warnings and failed candidates; acceptance must be bound to the emitted final hash. A non-native correspondence check or mock test cannot establish that these repairs work.

## Inspection errors retained

`inspection-corrections.json` records two initial interpretations caused by truncated multi-arm output: 27 seconds belonged to B0, and the two-stub RED1-A excerpt belonged to C. Focused re-read gives the exact B1 28-second/one-stub facts above and no duplicate SES net sections. `inspect-failed-001.py` retains the initial generic KiCad-parser invocation which failed on DSN's bare quote declaration before creating results. The corrected diagnostic reuses `adapter._parse_dsn`; this is an inspection preparation error, not a routing-file defect. Failed diagnostic command wall 0.039278083 seconds remains visible.

The successful diagnostic reports 0.158206 seconds wall and 0.157288 seconds process CPU before its final metadata writes. This covers the recorded diagnostic only, not preceding shell reads or AI latency. No final comparison or release eligibility is asserted by this report. All boards remain exposed development evidence; none of the new CellScan candidates is accepted.
