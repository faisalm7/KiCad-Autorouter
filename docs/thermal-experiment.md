# Thermal completion experiment

Fresh automatic recovery solved the exposed interf_u input under original KiCad rules where the tested stock representation, corrected adapter and tuned portfolio remained rejected. This is one development-input completion gain, with no general superiority, novel algorithm, human-review or physical/electrical claim.

## Recorded outcomes

Each policy receives independent 120-second wall and measured-CPU acceptance ceilings. Costs below include preparation, every engine/native attempt, failed proposals, receipt checks and the entire shared experiment overhead charged to each arm.

| Policy | Native opens / blocking / warnings / exclusions | Charged wall / CPU seconds | Accepted |
|---|---|---|---|
| B0 stock DSN representation, standard profile | 14 / 3 / 0 / 0 | 42.733323 / 64.191857 | No |
| B1 corrected adapter, standard profile | 0 / 1 thermal / 0 / 0 | 59.577230 / 80.119067 | No |
| B1 corrected adapter, completion-only profile | 0 / 1 thermal / 0 / 0 | 28.831796 / 42.258588 | No |
| B2 fixed tuned cost portfolio | 0 / 1 thermal / 0 / 0 | 72.948518 / 91.882070 | No |
| C fresh completion plus bounded thermal recovery | 0 / 0 / 0 / 0 | 42.044862 / 54.759604 | Yes |

B0 denotes the raw stock export under the common strict-target/runtime wrapper; it is not a reproduction of every vendor GUI default. B2 attempted only the default-cost variant: the remaining wall/CPU allowance could not fit another variant plus mandatory validation reserves. Its low/high variants have no outcomes. C used its own fresh completion-only incumbent and no reference route or free B2 candidate.

The B2/C pair ran at `cbae1254f00d3470d98ba18d24a09e99874f0cc2`. The three fresh baseline ablations ran separately at `cc71a5103f32b97274fb82a9494501b0b823d541`, with exact production, tool-binary, original-project and existing-protocol bytes checked equal. The new harness and Git HEAD differ explicitly. This is a separate cross-HEAD experiment, not a rerandomized five-arm trial. Each baseline is a separate policy; their combined union is not one 120-second portfolio.

## What changed in the board

C's own failed incumbent had one isolated-island thermal finding. Fresh native geometry and bounded rational path checks produced a 1.505199 mm bridge of the original 0.5 mm class width. The first trial passed actual refill, class checks and final native DRC, followed by another validation of the delivered copy. No via was added. Original pads, rules, severities, exclusions and ignored checks were preserved, and the target-zone saved fill remained exact.

The final candidate is `be7694040a84aaac331981cd121ac66774284df30923550c5054691fe302dabb`, with 4,996.393150 mm of track and 35 vias. Removing exactly the generated segment on a disposable copy recreated failed incumbent `f3469b34e2d7724d65ade7b1a5b3353c75b67c54f525f54b88c3626cd8531b0a`; fresh native checks restored the identical sole thermal error. That diagnostic's stored cost was 6.491124 wall / 5.019699 CPU seconds, before its final freshness check; the diagnostic cap includes that check. It is separate from comparative budgets.

The fresh completion-only baseline also fails the thermal, so allocation alone did not yield acceptance in these runs. The removal control provides local evidence that the bridge caused this candidate's native acceptance. It does not establish ampacity, heat flow, manufacturing safety or performance on another board. Rejected baseline track lengths cannot be usable-quality comparators; no such quality delta is claimed.

## Evidence and reproduction

- `evidence/thermal-paired-001`: both original arms, all attempted/omitted variants, raw reports/processes/exports, candidate bytes and fully charged costs.
- `evidence/thermal-ablation-001`: all three fresh baseline outcomes and cross-HEAD binding.
- `evidence/thermal-production-negative-001`: exact production bridge-removal counterfactual.
- `evidence/review-thermal-paired-001`: independent raw audit, 4,122 checks; this is AI consistency review, not human PCB review.
- `evidence/development-outcomes-001`: all 14 acquired boards and unsupported reasons. Two inputs have accepted recorded policies at different frozen versions; that is not an aggregate completion rate.

Complete raw native input trees and code snapshots remain in `.runs`; public subsets are intentionally smaller. Use new output directories. At unchanged production bytes, the reviewed commands are:

```sh
python3 -B scripts/experiment_paired.py --project interf_u --system thermal --output .runs/thermal-paired-NEW
python3 -B scripts/experiment_thermal_ablation.py --project interf_u --prior-pair .runs/thermal-paired-NEW --output .runs/thermal-ablation-NEW
```

Run sequentially with PCB Editor and other native/engine jobs idle. The harness rejects source, code, tool, candidate or retained-evidence changes. Do not reuse these exposed boards as an untouched final test set.
