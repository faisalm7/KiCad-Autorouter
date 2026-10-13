# Native parity availability: diagnostic proposal

**The current production path does not distinguish requested parity from executed parity.** A pure shared `Job.drc` seam with an ordinary empty DRC report and an explicit synthetic skipped-parity log returns a native-accepted summary; `parity_declaration()` labels the complete same-basename SCH as checked. This is source/control-flow evidence, not an actual native false acceptance or complete accepted routing receipt.

Pinned KiCad10.0.0 source is explicit. `pcbnew_jobs_handler.cpp:2364–2368` reports failure and disables `checkParity` if no same-basename native/legacy schematic exists. Lines2379–2383 do the same if the annotation sentinel is unchanged; lines2396–2401 do so after netlist parser `IO_ERROR`. The ordinary DRC still runs (`2425`) and writes its ordinary report. Only `checkParity=true` emits the `Found N schematic parity issues` message (`2459–2464`). Its exit0/5 calculation does not encode parity availability.

Production `pipeline.Job.drc:407–439` binds the before/after project, requests `--schematic-parity`, checks ordinary report identity/exit status, and collects complete fields only when a native field finding exists. It does not inspect the explicit skipped-parity diagnostic. `pipeline.parse_report:298–321` treats an empty parity list as no findings. `selected_parity_required:856–864` proves only the captured declaration/argv. `schematic_field_evidence.check_processes:83–90` returns when no field finding exists. Final routing validation and review export share these paths, so fresh export alone does not demonstrate that native parity ran.

## Retraction of initially suggested intrinsic trigger

An invalid Footprint identifier looked promising because cached `kicad_netlist_reader.cpp:828–834` contains an explicit `IO_ERROR` branch. Bounded missing primary source was retrieved at the already-pinned KiCad commit: `common/lib_id.cpp`, 5,911 bytes, SHA256 `456899c2669c9e96540cadd996ef6b91c214357d520a33c77456682e3d552e0e`. `Parse(...,true)` sanitizes item characters; its first-colon split leaves the nickname without a colon. Thus that branch is not a demonstrated trigger for ordinary valid strings. It is not proposed as a native control. Similarly, unannotation is not sufficient proof for headless DRC: cached `eeschema.cpp:166–175` formats directly and has no annotation rejection. The annotation-sentinel branch may apply to the GUI-mail path. No intrinsic complete-SCH parse-failure trigger is claimed.

## One deterministic native control, not executed

`native_control.py` reuses the complete, already native-accepted NUS B2 default as its positive baseline. It verifies the retained positive report and explicit `Found 5 schematic parity issues` log and does **not repeat** its completed stages. It clones only the retained candidate project into a new owned output, then invokes exactly one shared `Job.drc` stage. Its narrow step seam temporarily renames the owned validation-copy `.kicad_sch` outside that input directory while the actual CLI runs, restoring it byte for byte immediately after the worker returns. No original input, board geometry, rules, library settings or existing evidence changes.

This is an explicit availability race, not an ordinary static malformed source and not an algorithm experiment. Before/after inventories remain complete; the actual CLI sees neither native nor legacy schematic and must log `Failed to fetch schematic netlist for parity tests.`. The control requires that diagnostic, absence of the positive parity-completion message, ordinary report version/source/full-severity checks, empty raw parity list, original project/bindings, restored complete schematic and unchanged retained baseline. If current `Job.drc` then returns a native-accepted summary, the first execution records `demonstrated_parity_availability_defect` and intentionally fails; it does not fabricate a routing receipt or claim correctness. If another native/parser rejection occurs or the intended skipped branch is not proven, it records a diagnostic failure instead of calling the gate fixed.

The fixture preserves every NUS proof and warning. Expected loss of native parity warnings in the deliberately skipped control is visible and must never be treated as an improvement. Existing actual NUS positives remain valid because their retained native logs, parity findings and complete effective field evidence demonstrate that parity did execute.

Suggested lead command, after source/protocol checkpoint and when the single native lane is free:

```text
/Users/faisal/Projects/KiCad-Autorouter-local/.venv/bin/python -B /Users/faisal/Projects/KiCad-Autorouter-local/.runs/parity-availability-draft-001/native_control.py --output /Users/faisal/Projects/KiCad-Autorouter-local/.runs/parity-unavailable-native-001
```

The lead should use the existing foreground resource runner and outer network-denying sandbox to record full startup/finalization costs. The draft caps wall/full CPU at30 seconds internally and executes no solver. The native diagnostic's initial exit2 is intentional when the defect is demonstrated. Do not rerun completed stages merely to change that status after fixing readback/acceptance.

## Narrow integration recommendation

When parity is required, refuse native output if parity is explicitly skipped or execution cannot be proved. Bind the availability evidence to the exact native stage/process/input/report and recheck it in accepted-result and fresh-export readback. A CLI flag and complete before/after source inventory alone are insufficient. Use the current shared DRC/reader helpers and bounded retained logs; do not broaden the Datasheet exception or weaken any parity finding/ignored-check policy. Unknown availability remains a refusal. Native qualification is pending the lead's single control execution.

No native, JVM, Git, backup or production edits occurred in this review. One narrowly bounded pinned primary file was fetched because the needed definition was absent from the cache. URL/hash metadata is retained locally; raw GPL source is excluded from the public selector. `pure-result.json` is explicitly synthetic and does not prove native or GUI behavior.
