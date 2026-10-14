# Native task connectivity prototype

This is an exposed development diagnostic, not a routing method or accepted candidate.
It tests whether a fresh whole-board stripped task and saved native refill can certify
which entire nets have no unconnected native items. It preserves all DSN terminals and
class rules, uses completion-only engine settings in the proposed future comparator,
and never uses source/reference routing or previous C outcomes to select nets.

Current limits: at most64 complete nets, exact two outer copper layers, no footprint
zones or protected source routes, no all-connected/no-engine path. Unknown/ambiguous
UUIDs, mixed/null nets, omitted/reassigned terminals, modified rules, stale inputs,
excluded or disabled checks refuse. Native saved immutable geometry/routes must
match the stripped task exactly; a conversion mismatch is a recorded failure.
Four-layer and CellScan85 coverage remain explicitly unqualified.

Run the first classification-only falsification after the milestone backup/heavy lane:

```
.venv/bin/python -B experiments/native_connected_v1/driver.py --run-native --output "$PWD/.runs/native-connected-task-probe-001"
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
