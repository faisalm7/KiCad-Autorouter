# Stronger stock incumbent experiment

The private `strategy.prune` option `_incumbent_policy='free-angle-clearance20-v1'`
obtains its own fresh Freerouting incumbent, then uses the existing native-validated
pruning proposals. It requires `incumbent_scoring='via_default'`. Public settings
and the default pruning configuration are unchanged.

The child uses free angles, disabled fanout and optimization, and the qualified
experimental 20 µm planning-clearance correction. That correction belongs to the
adapter baseline. It changes neither the original design nor the native rules.
The current subset requires native KiCad 10.0.0, both adapter corrections,
whole-board scope and derived non-strict class/width targets. Other cases refuse.

The parent has a separate incumbent contract and retains the exact charged child
journal. It is not a direct free-angle producer. Missing or altered policy,
engine-input, journal, candidate, rules or native evidence rejects the result.

`native_control.py` prepares and runs one fresh owned-board integration control
and an actual short under the same original rules. This is not a quality
benchmark. The parent budget is 120 seconds; its child receives the remaining
work allowance after the unchanged 25-second finalization reserve. The whole
control has a 180-second wall and total CPU cap. Complete external command costs
must also be retained; sampled receipt values exclude some publication work.

Run `--mode prepare --source-head <verified-clean-HEAD>` first, then
`--mode run --source-head <same-HEAD> --protocol-sha256 <prepared-protocol-hash>`
using the project Python and the bounded command envelope retained with the
evidence. Outputs use new fixed `.runs/stronger-incumbent-*001` paths and refuse
existing directories. Never remove an old run to rerun these names.

Software controls and source review do not establish native acceptance or a gain.
Fresh native integration and equal-budget comparisons have separate receipts.
