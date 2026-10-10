# Actual diagnostic receipt consistency controls

Final attempt004 passed: original, relocated and restored positives accepted by
`diagnostic_route.check_result`; all14 deliberate corruptions rejected. No
KiCad, router, engine or native helper was executed. This is offline consistency
testing of actual retained fixture002 evidence, not a new native qualification
or authentication against replacement of an entire forged evidence collection.

The original run is `.runs/placement-routing-fixture-002` at73107be. The script
copies its complete evidence (~1MiB) and original project into this owned review
folder. Only top-level historical path metadata is rebased to the disposable
copy; original reports, native DSNs, all boards/project rules and code snapshots
remain byte exact for the positive. Derived context-content receipts and outer
inventories are recalculated to reflect the explicit path relocation. Historical
native timing and process claims remain historical, never a new invocation.

`attempt-004/audit.json` reports all outcomes. Before/after inventories bind the
original run, original source, runtime helpers, production code/HEAD and tool
hashes; they are identical. Each negative updates the outer evidence inventory,
and relevant report, candidate, observer or process/step hashes where specified.
No negative merely passes because the outer inventory was left stale.

| Control | Semantic rejection |
| --- | --- |
| Stale disposable original | Source/snapshot identity |
| Candidate rule severity | Original project/rule file set |
| Reidentified original severity | Core check no longer blocking |
| Placement removal provenance | Recomputed transform receipt |
| Weaker floor guidance | Raw-to-floor derivation |
| Rehashed native preference | Original raw project preferences |
| Rehashed observer flags | Original/native area flags |
| Rehashed executed observer | Frozen observer code pin |
| Changed observer process and matching step | Exact command provenance |
| Changed report and matching process/step | Native failure contradicts accepted receipt |
| Rehashed candidate routing | Task/import/refill reconstruction |
| Rehashed pad size | Original immutable geometry |
| Changed ignored critical check | Disabled required native check |
| Changed engine process and matching step | Exact engine command |

The final working copy is restored to its valid relocated baseline. Every
negative's exact modified files, receipt and exception are retained under
`attempt-004/cases/<name>`; reapply those deltas to that baseline to inspect a
case. One shared working copy avoids14 redundant full evidence trees.

Measured final attempt:1.094754541seconds wall, under the60second CPU/wall
controls limit. The whole owned review folder was3,799,901bytes before these
final notes/manifests, well below its10MiB ceiling. Execution uses normal
read-only/local filesystem helpers and the actual checker; it does not mock the
checker, native results or routing stages.

Failures are retained honestly: initial syntax typo prevented attempt001 from
starting; attempt002 reserialized a copied raw report, causing the positive to
reject by hash; attempt003 reached a valid relocated positive then stopped on a
wrong project severity field name in the mutation harness. Original evidence
was untouched. Source versions and logs remain. Final script preserves raw
reports byte-for-byte and uses actual `rule_severities`. These harness failures
are not pipeline failures or evidence of native behavior.

Reproduce as a fresh bounded offline attempt only:

```sh
python3 -B .runs/placement-diagnostic-receipt-controls-001/controls.py --run-controls attempt-005
```

No native or comparison claim should be derived from the relocated historical
receipt. The authoritative original accepted native run remains unchanged.
