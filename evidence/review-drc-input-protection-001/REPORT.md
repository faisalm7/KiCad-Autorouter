The completed protected-input diagnostic at recorded checkpoint `13d8db4d10cccaca715151184ecbaf16eb55d02f` passes this independent readback. No native, JVM, network or Git operation was repeated.

The actual canary exited0: all ten attempted writes returned EPERM, including atomic replacement, chmod and input-directory rename, while the external report/replacement-source writes succeeded. Each of the three DRC commands used the same network-denied, literal-plus-subpath input-write restriction, exact nonsaving/refill argv, isolated outputs, and recorded cleanup-complete process evidence.

| Case | Exit | Opens | Blocking | Warnings | Exclusions |
|---|---:|---:|---:|---:|---:|
| Owned legacy-PRL positive | 0 | 0 | 0 | 0 | 0 |
| Required via removed | 5 | 1 | 0 | 2 | 0 |
| Original PAW, protected copy | 5 | 0 | 0 | 17 | 0 |

The negative's sole raw unconnected error names exactly the two separated SIGNAL_A route UUIDs, `91c6777a-91e9-49aa-bccc-465e81fabbbe` and `e0e96db1-7033-4eaa-a505-eb55f5730467`. Its two warnings are `track_dangling`; it is not clean. The shared recipe reconstructs only the required-via deletion, with immutable board fields and project bytes preserved.

PAW's full parsed native report is equal to retained failed001: all17 warnings are `lib_footprint_issues`, with the exact eight effective ignored checks and five original explicit ignored settings. Both owned controls retain their separate exact five explicit/seven effective settings. PAW's original14 files and its actual validation14-file copy are identical, including the original PRL SHA `59ef02a971d7d463743b8d497c0f10b6a9546f5c687f68f6eb464204bbd3a486`. Both owned copies preserve their previously generated legacy PRL SHA `f5a290eeefb3583de916429190cd85bb88081b8bb40444139364df8e8bfdb49d`. No PRL was omitted, restored, normalized or exempted.

The audit reused `check_capture`, `drc_readback`, `negative_check`, `canary_check`, the original fixture recipe and shared report/process/project helpers. All captured code/runtime source hashes, tool binary hashes, reports/logs/processes, before/after input inventories, wrapper execution/log bindings and case recipes match. Current `pipeline.py` differs from the saved code; the exact ASTs of shared functions used for readback still match the captured version. Six original trees (258 files total) and the actual run (140 files,3,260,607bytes) stayed unchanged during this readback.

Stored costs are5.310857792wall/3.171531fullCPU seconds; the outer wrapper records5.565150167wall/3.384021waitedCPU, exit0 and no cleanup signals. Both are below the shared30-second limits; output is below20MiB. Stored totals precede final publication checks; the successful wrapper measurement includes completion. Captured evidence and source are finite consistency samples, not atomic authentication or an OS-enforced aggregate CPU quota.

This establishes the tested write-protection hypothesis on these fixed inputs: unchanged disposable project bytes coexisted with complete native DRC and the deliberate connectivity failure remained detectable. It does not qualify legacy in-memory interpretation, `zone_has_empty_net` enforcement, library closure, saved-fill/import equivalence, production support or routing acceptance. All qualification flags remain false. Original PAW001 remains explicitly failed at `native DRC modified input or rules: paw3395.kicad_prl`; this fresh protected observation does not reclassify that failure. No material mismatch was found in the requested actual readback scope.

Reproduction is read-only except its compact audit output:

```sh
python3 -B .runs/review-drc-input-protection-001/audit.py
```

The public selector contains only this report, the audit script, compact facts, audit log and hash manifest. It contains no raw boards, project/settings copies, media, installed binaries or downloaded source.
