# Frozen three-arm comparator driver

Promote `experiment_thermal_ablation.py` unchanged to
`scripts/experiment_thermal_ablation.py` and `test_thermal_ablation.py` to
`tests/test_thermal_ablation.py`, then run the local suite and checkpoint before
native execution. The script verifies that its exact bytes are committed.

Proposed invocation (not executed by this reviewer):

```
python3 -B scripts/experiment_thermal_ablation.py --project interf_u \
  --prior-pair "$PWD/.runs/thermal-paired-001" \
  --output "$PWD/.runs/thermal-ablation-001"
```

The fixed fresh arms are stock DSN/standard, combined adapter/standard, and combined
adapter/completion-only. Each has its own 120-second wall/CPU acceptance ceiling.
Every measured shared setup, prior verification, freeze, artifact check and final
publication cost is charged to each new arm. No historical candidate is supplied to
any new engine. The earlier C/B2 keep their original complete charges and outcomes.

Production source/tool/existing-protocol bytes must match the prior pair exactly;
only recorded Git HEAD and this added harness differ. Read-only verification of the
actual 708-file prior tree and accepted C native receipts passed at current1fca3b9
versus priorcbae125; `actual-prior-readback.json` records this. It ran no native engine.
The complete prior tree, new completed arm evidence trees, frozen code copy and
protocol are checked before and after final summary publication. Native-rejected
arms still verify executed settings/argv/cwd/export hashes. Pre-engine failures
explicitly make no executed-engine contract claim. Cancellation, stale evidence or
postpublication cap crossing invalidates the canonical summary, preserving the old
index under an invalidated name before attempting a correction write.

32 pure controls passed in 0.189 seconds (`pure-tests-004.log`). Native/router stages
are mocked; these controls do not qualify routing. The suite includes an actual
SIGTERM to the bounded test process while the handler is installed. The two AI
reviewers read the final driver and found no remaining blocker; neither reran native
jobs. This is not human PCB review. Root remains responsible for promotion, full
suite, checked push, actual native arms and final evidence audit.

Comparators are separate allocation policies, not an exact thermal-only ablation.
The original fairness review explains the smaller within-candidate bridge-removal
control and remaining population/physical/electrical limits. No threshold or budget
was loosened to accommodate additional evidence checking.
