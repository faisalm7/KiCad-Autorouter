# Native-validated route pruning — development protocol

Current C obtains its own tuned B2 incumbent and charges conversion, engine work, all native tests, failed deletion attempts and final emission to one 120-second wall and measured-CPU ceiling. The CPU ceiling is an acceptance check, not kernel CPU preemption. It uses original copper-zone net identifiers, then tries whole-net route removal and individual segments/vias in longest-segment order. Locked source copper remains protected. A deletion is retained only if native refill/DRC remains connected with no blocking findings/exclusions, original geometry/rules remain intact, length/vias do not increase, and no new warning identities appear. Failed trials are retained. A final check runs on the actual emitted candidate.

This is greedy native-validated postprocessing, a familiar optimization pattern, not a novel geometric routing algorithm. It specifically targets extra wiring introduced by B1's conservative plane suppression. It does not yet model true native plane components during export; even a shorter native-valid result is not proof of return-path or electrical adequacy. There is no learned selector or reference-route scoring.

Prediction: redundant zone-net wiring can be removed while retaining the wires that bridge separate copper components. Falsification: no quality reduction, broken connectivity, altered constraints, higher via/warning count, budget exhaustion, or no advantage over the competent tuned baseline. Integration cost: repeated native processes and full-project copies. Regression risks: consuming the completion budget before final checks, missing unverified electrical requirements, and poor proposal ordering on other boards. B2 is now the direct no-pruning ablation; pilots 001/002 used B1 incumbents. B2 uses the identical corrected representation with larger pass limits and a lower optimizer stopping threshold.

The experiment includes B0/B1/B2/C sequentially, freezes source, protocol and implementation before engines, counts every considered outcome, and records host load. Desktop background contention is uncontrolled; one project heavy worker runs at a time. Only one previously exposed public development family is presently compared. C has actual incumbent checkpoints; other arms only have final validated observations, so earlier success curves are not invented. No family-level confidence or broad superiority claim is supported.

## Pilot001: tuning error retained

Commit7242466902578f0a52909c9693a63223994adea9, `.runs/quality-comparison-001`, executed all four arms. B0 rejected3opens/7blocking findings. B1 accepted786.315536mm/3vias. C accepted657.503980mm/3vias,0opens/0blocking findings/1warning,106.440109s wall and83.096060s measuredCPU. The whole-zone-net deletion was rejected by native connectivity; individual accepted deletions account for the reduction. These are exposed development observations.

The intended B2 tuning was **misconfigured**: CLI value0.1 becomes10 percent, and the native engine log explicitly stopped after its first optimizer pass at that threshold. Its accepted789.442607mm/5vias cannot establish a comparison with the intended more persistent tuned baseline. Do not use pilot001 as the main B2/C improvement claim. The raw protocol, rejected/accepted trials and logs remain unchanged; this interpretation records the error.

Freerouting2.5.0 `CliSettings.java` converts values between0 and1 into percentages. CorrectCLI value0.001 produces0.1 percent. A new frozen revision and run identifier are required for the corrected four-arm experiment. Source: https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/settings/sources/CliSettings.java#L149 . Runtime logs must confirm the actual behavior.

## Corrected pilot 002

Frozen commit `57db7878f7b69549736788b4fc7e8c9458733e85`, `.runs/quality-comparison-002`, completed all four arms under 120-second wall and measured-CPU caps. B2's engine log confirmed the corrected 0.1% stopping threshold. Source and frozen code remained unchanged; accepted receipts passed the strict checker.

| Arm | Accepted | Opens / blocking | Warnings | Length mm | Vias | Receipt wall seconds | Receipt CPU seconds |
|---|---|---|---:|---:|---:|---:|---:|
| B0 | No | 3 / 7 | 1 | 566.454 | 4 | 10.447 | 11.098 |
| B1 | Yes | 0 / 0 | 1 | 786.316 | 3 | 13.908 | 18.179 |
| B2 | Yes | 0 / 0 | 1 | 786.316 | 2 | 18.765 | 27.247 |
| C, standard incumbent | Yes | 0 / 0 | 1 | 660.099 | 3 | 105.920 | 83.229 |

The acceptance calculation additionally checks the full enclosing invocation: B1 13.910 s wall / 18.185 s CPU, B2 18.766 / 27.253, and C 105.924 / 83.243. The table shows inner receipt timing; the full invocation includes its small remaining emission overhead.

C shortened the accepted B1 route by 126.216 mm with unchanged vias and warning identities. Against corrected B2 it is shorter but has one extra via: **no Pareto improvement over B2**. It also consumes more time and CPU; this is not a speedup. All three accepted arms retain one library-footprint warning and lack electrical/physical qualification. One exposed family establishes no generalized superiority. Full raw outcomes and failed trials are retained locally; the audited public subset is `evidence/quality-comparison-002`.

Pilot 003 below tests the subsequent hypothesis: begin C with the same tuned engine profile as B2, charging its complete generation and all pruning/native checks to the same total budget. Keep it separate from 001 and 002.

The current script additionally accepts `--project interf_u` for a separate four-arm development comparison. It verifies the complete selected project against the licensed acquisition manifest before freezing. Adding this option does not bypass preflight or qualify netclasses. Each family runs sequentially in its own new directory.

## Tuned-incumbent pilot 003 and timeout correction

At frozen `7c7f35875620d079d24dac4f52460c1237ca4a32`, `.runs/quality-comparison-003` completed all four arms. C generated its own tuned incumbent, then pruned under the unchanged 120-second outer wall and measured-CPU acceptance caps. B0 rejected 3 opens / 7 blocking findings. B1 accepted 786.315536 mm / 3 vias; B2 accepted 786.315536 mm / 2 vias; C accepted 662.694144 mm / 2 vias, 105.066025 seconds receipt wall and 83.722214 seconds CPU. Accepted arms had zero opens/blocking findings and one warning. C reduces length by 123.621392 mm against B2 with equal vias, and against B1 with one fewer via. This is a measured proxy-quality gain on one exposed family with increased compute; no generalized superiority, electrical adequacy or speedup follows.

A subsequent actual pinned-JAR probe found a second configuration mistake affecting all earlier profiles: timeout strings `60s`, `30s`, `100s`, and `90s` parse to null. The outer supervisor budgets and native acceptance records remain actual, but the intended inner engine deadlines were not enabled. Retain all original protocols and results; a corrected prospective comparison is required before describing the complete intended profile as qualified. On sonde, every engine completed well before those intended caps; that observation does not make malformed settings acceptable on other boards.

The same mistake was exposed by the first production `interf_u` attempt: routing and one optimization pass completed, then the outer supervisor killed the engine before any SES was written. The attempt is rejected (120.311234 seconds wall / 139.470787 seconds CPU), with complete cleanup recorded. It does not qualify multiclass routing. The engine's cumulative allocation counter is not resident memory; recorded peak RSS was about 1.62 GB.

Probe `.runs/optimizer-profile-probe-001` executed the actual classes in the pinned Freerouting 2.5.0 JAR: 57 of 57 assertions passed in 0.702 seconds wall / 1.176 CPU. It confirmed every existing profile setting, including tuned 0.1% optimizer threshold, and showed valid numeric or HH:mm:ss durations and supported `optimizer.enabled=false`. No board was routed by this probe. The corrected profiles will use valid durations and reserve documented cooperative timeout grace plus final native-validation time. These reserves are planning allowances; external caps and final native acceptance remain authoritative.

The repaired implementation was checked by `scripts/probe_engine_profiles.py`: actual-JAR probe 002 passed 201 checks across standard, tuned and completion-only profiles at four remaining budgets (120, 105, 45 and 900 seconds). It emits HH:mm:ss deadlines, reserves 30 seconds for documented cooperative shutdown and 10 seconds for native finalization, and rejects insufficient budgets. C's incumbent receives a smaller engine allocation within its charged total budget. `completion-only` is a separate qualification probe, never silently substituted for B2. Exact assigned/effective settings and process evidence are in `evidence/optimizer-profile-probe-002`. The current coordinator suite passed 171 tests; new production routing with repaired settings remains pending.

## Prospective warning-guided deletion ablation

The `--feedback-ablation` experiment option freezes five sequential arms: B0, B1, B2, C_single and C_feedback. Both C variants generate and pay for their own tuned incumbent. The sole proposal-policy difference is bounded compound deletion suggested by new native `track_dangling` warnings after a connected but quality-rejected deletion. Every referenced UUID must identify a unique, eligible tool-owned segment/arc on the same original zone net; protected, ambiguous or other-net items reject the proposal. At most two follow-ups and eight additional routes are allowed; each consumes the ordinary trial count and total wall/CPU budget and undergoes full native validation. No warning is waived. Acceptance checks the recorded policy to prevent a mislabeled arm.

Stored trial002/0001 motivates the hypothesis: deleting a long route left two small dangling segments. Joint deletion is unmeasured until this prospective experiment. Extra attempts may displace better proposals, so improvement is not promised. The existing single policy remains the CLI default. Independent code review and190 coordinator controls passed; substituted native stages in those tests do not establish routing correctness. Run after the exact sources are committed:

```sh
python3 scripts/experiment_quality.py --project sonde --feedback-ablation --output .runs/quality-comparison-004
```

## Corrected five-arm pilot 004

Frozen `221f26f2808b1918aca2a1df3b3f70b345605eb1`, all five arms completed sequentially under120second wall/CPU acceptance ceilings. Exact native input/source/code/receipt hashes and full invoking costs are retained in `.runs/quality-comparison-004`; the reduced public pack is `evidence/quality-comparison-004`. Corrected inner timeouts are recorded per run.

| Arm | Native opens / blocking | Warnings | Length mm | Vias | Receipt wall / CPU seconds | Accepted |
|---|---|---:|---:|---:|---|---|
| B0 | 3 / 7 | 1 | 566.453919 | 4 | 10.655905 /10.643505 | No |
| B1 | 0 / 0 | 1 | 786.315536 | 3 | 13.536024 /16.701032 | Yes |
| B2 | 0 / 0 | 1 | 786.315536 | 2 | 18.256663 /26.195744 | Yes |
| C_single | 0 / 0 | 1 | 662.694144 | 2 | 104.665355 /83.391587 | Yes |
| C_feedback | 0 / 0 | 1 | 644.548871 | 2 | 107.789295 /85.618350 | Yes |

All accepted arms passed full enclosing-invocation budgets and strict receipts. C_feedback is141.766665mm shorter than B2 with equal vias, and18.145273mm shorter than C_single. The combined deletion was actually accepted at feedback trial0002: one preceding segment plus the two exact native-identified dangling stubs. C_feedback had25trials and21accepted improvements. The retained parent failure and every follow-up received real native checks. The modest extra compute versus C_single is measured; no speedup over B2, broad completion gain, electrical adequacy or general superiority is established. This is one exposed family, one fixed-order trial per arm. Stronger equally charged restart/tuning baseline research remains open.

## Subsequent interf_u qualification failures

Strict-target engine settings (automatic neckdown disabled, fanout disabled, neck override0) were frozen at80acfa8 and preserve original rules and class targets. Completion-only run003 finished27.436752wall/41.615390CPU; standard-optimizer run004 finished59.468540/80.370603. Both pass generated class-dimension checks and native connectivity (zero opens), but both have one blocking `starved_thermal` on U9C4: a spoke connects to an isolated island. Their metrics4994.887951mm/35vias are rejected outputs and are not usable quality results. Optimizer004 did not resolve the native failure. These are separate qualification probes, not a frozen B0/B1/B2/C population comparison. No rule, thermal setting, pad or zone intent changed.

## Prospective stronger baseline

The fixed search-cost portfolio (`scripts/experiment_portfolio.py`) tries regular/plane via costs50/5,25/3,100/10 in that order from the same original task, under one shared120-second wall and measured-CPU allowance. All attempts, setup, checks and selection are charged. It selects fewer vias then shorter track and retains the entire Pareto frontier. The actual JAR accepted all539 configuration checks, but this is not a routing result. Independent review reproduced and fixed a final-publication cancellation gap. A fresh same-code paired comparison with C_feedback follows the reviewed checkpoint. The portfolio index is not a routing receipt; a selected trial receipt alone does not represent total portfolio cost.

The native excluded-warning control002 showed why exclusion must be counted independently of severity. The repaired parser counts the actual `excluded: true` flag; malformed flags reject. Original excluded projects remain unsupported. The first control recipe001 used a footprint anchor rather than native marker center and failed; both attempts remain evidence.

## Isolated thermal-bridge diagnostic

At655207c, `scripts/native_thermal_bridge_control.py --output .runs/interf-thermal-bridge-002 --validate` tested the first predeclared2.1mm GNDbridge on the stored rejected003candidate. Actual refill, fresh native class audit and final DRC passed with0opens/blocking/exclusions and no extra vias; length4996.987951mm. Repair-only5.576698wall/4.499296CPU seconds excludes original routing cost and is explicitly ineligible for system comparison. Failure001 stopped before native execution on an overly broad dimension/text UUID guard and remains retained. This is a board-specific diagnostic, not production recovery. Geometry certification, a negative counterfactual and a general proposal method remain next. Original thermal rules/pad/zone intent are unchanged.

The paired harness now freezes common code and source for a fresh B2portfolio then C_feedback run. C uses its own default-cost tuned incumbent; it receives no free result from B2. Both receive120secondwall/CPU caps, and the complete shared freeze/copy/publication overhead is conservatively charged to each arm. Six additional control-flow checks cover failures, frontier tradeoffs, shared charging and final-publication interruptions. No native paired outcome exists at this checkpoint.
