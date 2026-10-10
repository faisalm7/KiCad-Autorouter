# Disposable placement review-copy native qualifier

This helper has passed independent source review and33 root pure/read-only controls. No native KiCad, engine or GUI was run in preparing it. It does not implement review-copy or admit another routing policy. Root has integrated the exact reviewed helper/tests and created the actual `.runs/placement-review-copy-001` from the separately checkpointed production handoff. After this helper checkpoint, run the sole native lane below.

## Exact experiment

The only permitted accepted receipt is `.runs/placement-production-native-001/result.json` (SHA256 `166050372738e25335db8261753c433c921a0a71857148c7a4d8cadf2669df7d`); its candidate SHA256 is `4c118026360d23ecfffad6b4c8638aabf592f9534ca1e8cb999a77316dee09e1`. The new `review.json` must be a direct `.runs` child with schema1, `ready_for_manual_review`, exact schema3 placement policy/receipt/candidate identity, original full project inventory, and the declared successful 30-second handoff resource sample. Those metadata fields do not establish native or GUI acceptance.

Two fresh independent complete copies are derived from that exact review project: byte-identical positive, and negative removing only the one qualified required through via. The inherited pure recipe binds that via's UUID, SIGNAL_A,1.5mm diameter/0.3mm drill, both copper layers and adjacent route UUIDs. No other route, pad, area, edge, net, rule or project file changes. The negative must yield native unconnected items involving the exact adjacent route UUIDs and remain rejected; arbitrary unrelated opens do not satisfy it. The positive requires no findings and unchanged original ignored-check list. Reference source routing is not changed or mistaken for the stripped task.

Each case uses production `FloorJob` setup/`Job.drc` with a complete second input copy and `save=False`, the production bounded runner, isolated KiCad10 config/cache/documents/TMP, and sandbox network denial. The only subprocess argv permitted is native CLI DRC with all severities, all track errors, refill, and violations exit code; no SaveBoard, DSN export, engine, GUI or live apply. Raw report/log/process bytes freeze immediately after the worker, before parsing. Candidate/native input/project, raw report/process argv/status and saved binding are rechecked through final publication using the existing qualified control's pure `check_drc`/predicate helpers.

Shared predeclared acceptance caps are 60seconds wall and measured parent+all waited-child CPU, including preparation, metadata subprocesses and final checks; max20MiB total output payload,512files/1024entries; each native worker RSS2GiB/log256KiB. Four complete payload copies are reserved before work (two cases and two DRC-input copies), plus1MiB overhead and saved source code. This fixture payload is58,140bytes per copy. The runner monitors the remaining output allowance. Acceptance includes final postpublication checks; stored totals are explicitly a prepublication sample. Cooperative timeouts/polling can overshoot, and no OS aggregate CPU quota is claimed. Failure/corrective rejection may finish outside the cap.

Input evidence reads are bounded100MiB/2000files/4000entries. Runtime source includes every production module, toolchain lock, reused prior control helper, and the new driver/tests, all required byte-identical to their current committed HEAD before native execution. That current freeze is rechecked afterward; future legitimate unrelated code changes can run after a new checkpoint rather than being pinned to today's draft HEAD. Original source, candidate, accepted full evidence and handoff trees cannot rebase after validation. All original material hashes are repeated after subprocess-bearing checks. A shared nonblocking experiment lock prevents concurrent native jobs.

Cancellation/staleness/final cap failures archive any canonical/partial positive summary before best-effort negative publication. Scoped SIGINT/SIGTERM handlers restore previous handlers. A successful control receipt always retains `routing_accepted:false`, `gui_qualified:false`, `live_apply_qualified:false` and `new_engine_execution:false`: this is a bounded copy-boundary diagnostic, not another routing/comparison result or human PCB review.

## Pure preparation checks

`python3 -B -m unittest discover -s .runs/placement-handoff-native-draft-001 -p test_driver.py -v`

33 controls passed in the final run (`pure-controls-005.log`). These include actual accepted-receipt readback, exact via removal, full tiny file-copy flow with explicitly fake native worker and checker, project/source/report/case mutations at stage and publication boundaries, required-UUID rejection, code/argv/caps/path/schema guards, failed corrective writes, and actual Python selfSIGINT/selfSIGTERM under scoped handlers. They are lifecycle/recipe evidence, not fresh native qualification. Earlier successful21/28/30/32control logs are retained. Reviewer reproduced a late size-scan publication race against the original driver7c37b2f7: a canonical mutation or budget consumption during the final size scan escaped the old order. Original source/tests/docs/manifest are retained byte-for-byte in snapshot-001. Final size scanning now precedes the exact canonical/in-memory comparison and final cap sample; both reviewer falsifiers and a returned-record mutation have regression controls. No native finding is inferred.

## Lead command after promotion/checkpoint and real handoff creation

Suggested promotion path: `experiments/placement_handoff_native_v1/{driver.py,test_driver.py,README.md}`. Root substitutes the newly created real handoff's exact path and a fresh output ID; this command has NOT been executed:

```sh
python3 -B experiments/placement_handoff_native_v1/driver.py --receipt .runs/placement-production-native-001/result.json --handoff .runs/placement-review-copy-001/review.json --output .runs/placement-handoff-native-001 --run-native
```

The helper refuses reuse and refuses uncommitted runtime source/tests. Preserve failures unchanged. The following GUI fixture and full multichannel observations remain separate pending work; native controls do not qualify GUI edits, undo, live board application or older formats.
