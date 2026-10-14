# Native task connectivity prototype

This is an exposed development diagnostic, not a routing method or accepted candidate.
It tests whether a fresh whole-board stripped task and saved native refill can certify
which entire nets have no unconnected native items. It preserves all DSN terminals and
class rules, uses completion-only engine settings in the proposed future comparator,
and never uses source/reference routing or previous C outcomes to select nets.

Current limits: at most64 complete nets, exact two outer copper layers, no footprint
zones or protected source routes, no all-connected/no-engine path. Unknown/ambiguous
UUIDs, mixed/null nets, omitted/reassigned terminals, modified rules, stale inputs,
excluded or disabled checks refuse. Probe001 refused the actual KiCad9-to10 saved representation change. The next
protocol uses existing validate_candidate: saved refill, exact original-shell
reconstruction and a fresh final original-rule/full-schematic DRC. Classification
uses that final shell/report, with strict immutable task and route equality. Both
actual report/process lineages and every companion remain mandatory.
Four-layer and CellScan85 coverage remain explicitly unqualified.

Run the first classification-only falsification after the milestone backup/heavy lane:

```
.venv/bin/python -B experiments/native_connected_v1/driver.py --run-native --output "$PWD/.runs/native-connected-task-probe-002"
```

The explicit action is bounded60seconds wall/fullCPU and performs no engine routing.
Shared Job/DRC/process readers, source snapshots, evidence inventory and guarded
publication bind actual native proof. `accepted` stays false. Targeted synthetic
controls test the classifier and shared publication, not native correctness.

Review found and fixed missing inner-only terminals, nested footprint fill and two
publication defects before execution. Any future routing integration must add central
receipt dispatch/activity markers, exact command/DSN/material readback, inactive-net
copper checks and mandatory final native/original/schematic validation. A paired
completion-only all-active comparator must pay the same task preparation costs;
existing corrected/tuned B2 and C evidence remains frozen and separately visible.
No quality, completion, speed, independence, GUI or electrical/physical claim follows.

Native export001 also exposed repeated same-net physical pads (J1-S1@1..@3,
SW1-1@1/2@1). The narrow alias witness retains one terminal per physical pad,
requires identical native net for the repeated reference/number, and refuses
real @ names/token collisions, missing/extra/reassigned aliases. Whole-net
activity never needs to guess which same-net physical pad owns each alias.
No engine comparison has run. The original strict failed001 remains immutable.
