# Original PIC schematic-field parity control proposal

Status: source/recipe design only. No native, Java, router, GUI, network request or dataset script ran; no copied or original board/schematic was written. Production support is unchanged. The pure source census and in-memory delta/reversal assertions passed. This is exposed development data, not a new board family or holdout.

Use the genuine complete original PIC project as the baseline. It contains 15 files totaling 1,366,598 bytes, including the root schematic, its one `pic_sockets.kicad_sch` child, embedded symbol definitions, local library/model files, original project and both license notices. The source hashes are in `recipe.json`. Static inspection found 63 board footprints and 66 on-board symbol units representing exactly the same 63 references (U2 has four units). Reference, Value, Footprint identifier, Datasheet and Description match for every corresponding source unit. This is encouraging source evidence, not a native netlist/connectivity/parity pass.

## Minimal fixed sequence

Keep the basename `pic_programmer` and the full original hierarchy in every fresh complete project copy. Never edit `.data`, a library definition, the original project, severities, exclusions, footprint/pad/net/route/zone geometry or the schematic circuit.

1. **original_parity:** unchanged complete original copy. Run real nonsaving DRC with `--schematic-parity` and refill. Require actual parity execution and zero parity findings before continuing. Retain all ordinary DRC results. Existing original DRC without parity was 0 opens, 0 blocking, 41 missing-library warnings and 0 exclusions; that earlier result is not this prerequisite.
2. **matched_custom_field:** add one hidden custom field named `AutorouterDiagnosticParity`, value `PIC_FIELD_MATCH_001`, to BOTH the placed R1 schematic instance and the R1 PCB footprint. Do not alter the symbol library. This is a genuine field-matched positive built on the unchanged circuit/hierarchy, not a stand-in schematic. Require zero parity findings and the same normalized non-parity DRC findings as case1.
3. **mismatched_custom_field:** copy case2, changing ONLY the added PCB field value to `PIC_FIELD_MISMATCH_001`. The schematic remains byte-identical to case2. Require exactly one nonexcluded `footprint_symbol_field_mismatch` of original severity `warning`, in `schematic_parity`, attached to the exact R1 footprint UUID. The raw description must identify the declared field and both declared values. Require all non-parity findings unchanged and no additional parity item or exclusion.

Original parity failure, custom-field export failure or an unexpected negative is an honest failed control. Stop and preserve the result. Do not repair the original schematic, switch target, lower severity, filter an unexpected item or reinterpret an empty parity list as a pass after execution.

## Exact declared target and delta

- Root schematic UUID: `2e45d1d2-c73f-46e5-98d6-3a9dc360bff5`.
- R1 placed symbol UUID: `00000000-0000-0000-0000-0000442a4cf4`; one unit, root sheet, current reference R1/value10K.
- R1 footprint UUID: `00000000-0000-0000-0000-00005a22ac23`; position87.63,118.11 mm; source path `/00000000-0000-0000-0000-0000442a4cf4`.
- R1 footprint library ID: `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal`.
- `recipe.json` stores both exact proposed property ASTs and a deterministic new PCB-field UUID. The new properties copy each target's existing hidden Description property's presentation; only name/value change and the new PCB field receives its own UUID. Thus there is no new visible drawing or copper.

For later implementation, use a bounded source-span insertion at the uniquely identified target, then reparse and prove that removing precisely the new property restores the complete original AST. Preserve every non-target file byte exactly. Reject duplicate references, UUIDs or field names, multiple/absent target instances, wrong unit/root sheet, missing hidden presentation, an already present diagnostic field, changed source hashes, or malformed S-expressions. For the negative, prove that replacing only the declared value restores the entire positive PCB AST and that all other positive project files are byte-identical. The current pure derivation checks these reversals in memory; it does not emit candidates.

Do not use a PCB-only extra field as the negative. The pinned provider iterates schematic fields and checks their PCB counterparts; an extra PCB field is not tested by this code. Do not change the built-in Value or Footprint fields: those exercise a different finding type. Do not use a field with a reserved `ki_` name, change field visibility between cases, or rename R1.

## Primary-source behavior and actual coverage requirement

All cited files are already cached at KiCad10.0.0 commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`; this task rehashed six files against their prior source receipts. The demo revision is separately pinned at `69cafb907ebc09e7722a2a464b1d466fc2e3608d`.

- [`drc_test_provider_schematic_parity.cpp:214–268`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_test_provider_schematic_parity.cpp#L214-L268) compares component fields with PCB fields. It omits Reference/Value/Footprint/Component Class from the component comparison and Reference/Value/Component Class from PCB fields. A differing value creates DRCE_SCHEMATIC_FIELDS_PARITY and attaches the footprint. Visibility is not a skip condition here. Only the first mismatch per component is reported, which is another reason to require clean positive parity first.
- The same provider's `Run()` requires both `GetTestFootprints()` and a supplied netlist. If no netlist is supplied it can skip successfully. A zero report alone proves no coverage.
- [`pcbnew_jobs_handler.cpp:2337–2402`](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcbnew_jobs_handler.cpp#L2337-L2402) finds a same-basename `.kicad_sch` (then legacy `.sch`) and obtains the CLI netlist through Eeschema's KIFACE. Missing, unannotated or failed netlist loading sets `checkParity=false` while ordinary DRC can still run. The source explicitly notes CLI netlister limitations. At2449–2457 the `Found N schematic parity issues` log line is emitted only when parity remains enabled.
- `pcb_marker.cpp:71–80` classifies this code as MARKER_PARITY; `drc_report.cpp:194–205` writes that provider to the JSON `schematic_parity` array. `drc_item.cpp:208–210` maps its exact key to `footprint_symbol_field_mismatch`. Original project severity is `warning`; `board_design_settings.cpp:191` also defaults to warning. Original settings remain authoritative.
- `pcbnew_jobs_handler.cpp:2480–2492` saves the board only when BOTH refill and save-board options are requested. Omit `--save-board`; hash every source copy before/after. The violation exit includes ordinary/parity warnings, so expected process exits are0/5 according to the complete report, not universally0.

The candidate CLI recipe is the already used original-rule DRC argv plus the single parity flag:

```text
sandbox-exec -p '(version 1)(allow default)(deny network*)' <pinned-kicad-cli>
  pcb drc --format json --severity-all --all-track-errors --refill-zones
  --schematic-parity --exit-code-violations --output <case/raw-drc.json>
  <case/project/pic_programmer.kicad_pcb>
```

This command is prospective. There is no cached actual `pcb drc --help` receipt establishing the installed flag spelling in this investigation; the lead should capture that bounded help before the first actual run. Do not silently drop an unsupported flag. No native Python API or netlist-export API is required to implement the minimal CLI control. Actual KIFACE custom-field propagation, hierarchy/annotation handling and library resolution remain unobserved. This task did not obtain cached exporter/reader implementation source, so it does not infer their detailed field filtering. Case3's exact field/value/UUID finding, together with positive cases and explicit parity-enabled logs, is the functional observation needed. A future standalone native netlist observation can be proposed only if that specific gap blocks the actual control.

## Later controller obligations

Reuse the reviewed foreground runner and complete project-copy/binding helpers. One shared experiment lock; three sequential CLI stages; predeclare60 seconds wall and full parent-plus-waited-child CPU for the entire diagnostic,20 MiB output, the existing bounded per-process RSS guard, no router, isolated project KiCad config/cache/documents and explicit network denial. Three source copies are4,099,794 bytes before tiny field additions; charge every helper/config/report/copy. Do not label memory polling a hard OS limit. Actual child CPU plus full-parent/metadata CPU and final publication checks must fit; the recorded sample point must be explicit.

Require exact current committed helper/core/tool/HEAD pins, all15 source-file hashes, fresh output, no symlinks/case collisions/path escapes, complete copied project inventories, strict JSON, exact argv/cwd/log/process status, and both original and copied byte/semantic guards. Freeze each completed raw report/process/log before parsing. Retain all three result rows even when a prerequisite prevents later execution. Bind final report bytes to the exact case PCB/project/schematics and every dependency; do not let final scans rebase mutated data. Final scans precede last current-material/canonical comparison and deadline checks; cancellation invalidates any positive receipt and restores handlers.

The report parser must inspect **all three arrays** (`violations`, `unconnected_items`, `schematic_parity`), preserve each raw severity/excluded value, reject unknown schema/duplicate/nonfinite data, and never hide the targeted warning. Require the parity-enabled count in the log to equal the raw array, and reject explicit missing-netlist/annotation/skip diagnostics. Warning fingerprints should include type, severity, excluded flag and item UUIDs, with description differences retained and inspected; do not normalize away field values or unrelated findings. Source explicit ignored keys are three; prior effective native ignored keys added `track_not_centered_on_via`. Bind that distinction unchanged rather than equating source and loaded settings.

Pure controller falsifiers to add later: missing parity argv; missing child schematic; same-basename mismatch; duplicate R1/field; positive field absent from schematic; extra PCB-only negative; changed field on wrong UUID; missing target warning; extra unrelated parity item; fake complete with no parity-enabled log; field/name/value or raw report mutation after stage parsing; source change during final metadata checks; final-size overrun/cancellation. An actual native report is mandatory for qualification; these pure checks alone are not parity evidence.

All control receipts must keep `routing_accepted=false`, `custom_pad_support_qualified=false`, `schematic_parity_qualified=false` until this narrowly scoped sequence actually passes; even then any qualification is limited to this field/provider contract. The warning is a deliberate diagnostic negative, not an electrically invalid PCB or a reason to relabel the board as routed. No production severity admission, custom-pad transport, population rate, family independence or C-novelty claim follows.
