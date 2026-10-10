# Native-validated route pruning — development protocol

C obtains its own B1 incumbent and charges conversion, engine work, all native tests, failed deletion attempts and final emission to one 120-second wall and measured-CPU ceiling. The CPU ceiling is an acceptance check, not kernel CPU preemption. It uses original copper-zone net identifiers, then tries whole-net route removal and individual segments/vias in longest-segment order. Locked source copper remains protected. A deletion is retained only if native refill/DRC remains connected with no blocking findings/exclusions, original geometry/rules remain intact, length/vias do not increase, and no new warning identities appear. Failed trials are retained. A final check runs on the actual emitted candidate.

This is greedy native-validated postprocessing, a familiar optimization pattern, not a novel geometric routing algorithm. It specifically targets extra wiring introduced by B1's conservative plane suppression. It does not yet model true native plane components during export; even a shorter native-valid result is not proof of return-path or electrical adequacy. There is no learned selector or reference-route scoring.

Prediction: redundant zone-net wiring can be removed while retaining the wires that bridge separate copper components. Falsification: no quality reduction, broken connectivity, altered constraints, higher via/warning count, budget exhaustion, or no advantage over the competent tuned baseline. Integration cost: repeated native processes and full-project copies. Regression risks: consuming the completion budget before final checks, missing unverified electrical requirements, and poor proposal ordering on other boards. B1 is the no-pruning ablation. B2 uses the identical corrected representation with larger pass limits and a lower optimizer stopping threshold.

The experiment includes B0/B1/B2/C sequentially, freezes source, protocol and implementation before engines, counts every considered outcome, and records host load. Desktop background contention is uncontrolled; one project heavy worker runs at a time. Only one previously exposed public development family is presently compared. C has actual incumbent checkpoints; other arms only have final validated observations, so earlier success curves are not invented. No family-level confidence or broad superiority claim is supported.

## Pilot001: tuning error retained

Commit7242466902578f0a52909c9693a63223994adea9, `.runs/quality-comparison-001`, executed all four arms. B0 rejected3opens/7blocking findings. B1 accepted786.315536mm/3vias. C accepted657.503980mm/3vias,0opens/0blocking findings/1warning,106.440109s wall and83.096060s measuredCPU. The whole-zone-net deletion was rejected by native connectivity; individual accepted deletions account for the reduction. These are exposed development observations.

The intended B2 tuning was **misconfigured**: CLI value0.1 becomes10 percent, and the native engine log explicitly stopped after its first optimizer pass at that threshold. Its accepted789.442607mm/5vias cannot establish a comparison with the intended more persistent tuned baseline. Do not use pilot001 as the main B2/C improvement claim. The raw protocol, rejected/accepted trials and logs remain unchanged; this interpretation records the error.

Freerouting2.5.0 `CliSettings.java` converts values between0 and1 into percentages. CorrectCLI value0.001 produces0.1 percent. A new frozen revision and run identifier are required for the corrected four-arm experiment. Source: https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/settings/sources/CliSettings.java#L149 . Runtime logs must confirm the actual behavior.

## Corrected pilot 002

Frozen commit `57db7878f7b69549736788b4fc7e8c9458733e85`, `.runs/quality-comparison-002`, completed all four arms under 120-second wall and measured-CPU caps. B2's engine log confirmed the corrected 0.1% stopping threshold. Source and frozen code remained unchanged; accepted receipts passed the strict checker.

| Arm | Accepted | Opens / blocking | Warnings | Length mm | Vias | Wall seconds | CPU seconds |
|---|---|---|---:|---:|---:|---:|---:|
| B0 | No | 3 / 7 | 1 | 566.454 | 4 | 10.447 | 11.098 |
| B1 | Yes | 0 / 0 | 1 | 786.316 | 3 | 13.908 | 18.179 |
| B2 | Yes | 0 / 0 | 1 | 786.316 | 2 | 18.765 | 27.247 |
| C, standard incumbent | Yes | 0 / 0 | 1 | 660.099 | 3 | 105.920 | 83.229 |

C shortened the accepted B1 route by 126.216 mm with unchanged vias and warning identities. Against corrected B2 it is shorter but has one extra via: **no Pareto improvement over B2**. It also consumes more time and CPU; this is not a speedup. All three accepted arms retain one library-footprint warning and lack electrical/physical qualification. One exposed family establishes no generalized superiority. Full raw outcomes and failed trials are retained locally; the audited public subset is `evidence/quality-comparison-002`.

Next prospective hypothesis: begin C with the same tuned engine profile as B2, charging its complete generation and all pruning/native checks to the same total budget. Pruning's no-via-increase rule would then preserve that incumbent's via advantage. This is a proposed experiment, not a measured outcome; do not pool it retrospectively with 001 or 002.
