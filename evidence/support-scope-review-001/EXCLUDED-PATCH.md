# Minimal excluded-flag correction draft

`parse-report-excluded.patch` changes only the report parser. It validates `excluded` as an exact boolean when present and counts the union of `excluded: true` and legacy severity `exclusion`. It keeps error/warning counts and all preflight eligibility gates unchanged. Missing `excluded` means false: KiCad10 source `include/rc_json_schema.h:72–75` writes this key only when true. Actual saved sonde reports omit it for unexcluded warnings. A required-field rule would wrongly reject those native reports.

Primary source is the official10.0.0 tag commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`; serializer bytes and hash are in source-receipt.json. `common/rc_item.cpp:166–182` provides the boolean, `drc_report.cpp:174–177` restores excluded markers' original severity, and `pcb_marker.cpp:103–161` defines the serialized exclusion key. No source or report was altered to create these findings.

Seven focused pure tests passed against the ignored candidate parser: excluded-warning regression across all three report collections; missing/false compatibility; malformed flag types; legacy exclusion no double count; errors retained; unchanged padstack preflight rejection; and equality on the saved actual native sonde report. These are parser tests, not native exclusion qualification. Command: `python3 .runs/support-scope-review-001/test_excluded_proposal.py`. The test's explicit legacy-failure assertion is a review reproduction and must be adapted when promoting to the fixed production parser.

`native_exclusion_control.py` is a prospective two-native-call negative control, not yet executed. It first rechecks an accepted sonde receipt and runs native DRC on a disposable unmodified copy. It then adds one exact existing library-warning exclusion to a different disposable project, preserving all severity values and source board bytes, runs real DRC, and requires an actual warning with `excluded: true`. The proposed parser must count it and the existing acceptance predicate must reject it. Missing the marker is a control failure; the script does not invent a native flag or keep trying alternate exclusions. Original candidate and upstream source hashes are checked before/after. It uses no solver, two bounded20-second native jobs, isolated existing worker configuration, a new .runs output, and requires explicit `--run-native`.

After the lead releases native execution, proposed command:

```sh
python3 .runs/support-scope-review-001/native_exclusion_control.py --result .runs/adapter-ablation-001/combined/result.json --output .runs/exclusion-native-control-001 --run-native
```

The script reports parser rejection through `exclusions > 0`; parse_report is a summary function and does not normally throw for valid-schema errors or exclusions. Strict malformed booleans do throw. The script does not fabricate a full routing receipt or claim complete safe-application qualification. Existing source-exclusion preflight remains blocked; this direct native control intentionally exercises the raw report path underneath that guard. The serialization position/nil-UUID recipe is source-derived and remains unqualified until the actual native marker matches. Do not execute during active benchmark jobs. Both script ASTs parsed successfully; no native execution occurred.
