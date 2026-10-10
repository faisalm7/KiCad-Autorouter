# Board-floor publication repair draft 002

Preparation only. No native or engine subprocess was run for this draft. Lead review and a fresh actual run remain required. The prior `board-floor-geometry-001` run remains **invalidated**; its six individually passing native controls do not override its overall receipt.

The original `fixture_recipe.candidate` returns each negative control's expected finding as a Python tuple containing its finding type and UUID list. JSON encodes tuples as arrays, and the decoded receipt therefore contains lists. The prior `json.loads(...) != record` test compared different Python types after a faithful JSON roundtrip, producing `Rejected: summary changed` even though the stored data was unaltered. The exact executed driver and actual invalidated positive receipt reproduce this failure in a pure regression.

The new publication code captures a strict canonical JSON representation **before** writing, then compares the canonical representation of strictly decoded readback. This preserves tuples' correct JSON array semantics while retaining exact semantic content, numeric/Boolean distinctions, object-order independence, and all existing stability, budget, cancellation, invalidation and partial-receipt safeguards. It rejects duplicate JSON keys and nonfinite values. Snapshot-before-write also rejects a writer that mutates the supplied record. No native scope, constraints, geometry, case targets, or guidance policy changed.

Validation: 31 pure controls pass in `pure-tests-001.log`: all 23 retained adversarial controls plus 8 actual-record/strict-JSON regressions. The regression executes only the old `publish` function extracted by AST from the exact executed driver; it does not execute native code. These are publication controls, not new native qualification.

The fixture, recipe, guidance helper, native context worker and previous tests are byte-identical to draft 001. Draft 001 and actual run 001 were read only. The current draft-001 driver and the actual executed driver share SHA-256 ed7588640bddb25270a4a58819dfb2c972e29d07d112143a0f3d3ac038b9e9db. The older draft-001 manifest is retained as historical preparation evidence and is not silently updated to match the lead's later accounting edit.

The manifest inventories all actual run-001 and draft-001 files at draft freeze, plus every new draft file except the manifest itself. This inventory is a readback snapshot, not a replacement for the prior archive/restore or a claim of native success.

Lead-owned next commands, sequentially after review:

```sh
python3 -B -m unittest discover -s .runs/board-floor-native-draft-002 -p 'test_*.py' -v
python3 -B .runs/board-floor-native-draft-002/driver.py --out .runs/board-floor-geometry-002 --stage geometry --run-native
```

The optional forced-via engine/import stage remains unexecuted. No production eligibility gate changed, and this preparation establishes no routing or comparative success.
