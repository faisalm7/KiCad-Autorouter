# Board-floor guidance qualification

The explicit production adapter passes the owned required-via fixture, while full multichannel routing remains rejected. It is not a new routing strategy or a completed multichannel board. Original board/project rules, native class preferences and DRC severities remain unchanged.

The original multichannel export used preferred0.2mm tracks/clearance and0.6mm vias despite original board minima of0.3mm tracks/clearance,1.5mm vias,0.3mm drills and0.3mm annuli. Earlier native context001 proved those values and terminal mapping. The uncorrected full-board attempt remains rejected with160opens and95blocking findings.

The proposed explicit single-Default/two-layer policy derives guidance from the maximum of the raw preference and original native minimum; via diameter also covers drill+twice the minimum annulus. It changes only audited DSN rule/via fields, including the SMD clearance exception, and retains raw, guided and adapter output separately. It disables all three optional engine width-reduction paths. Raw native class values are never replaced with fabricated larger values. Final original-rule KiCad DRC remains mandatory.

## Actual native controls

Root executed each invocation sequentially on this Mac with pinned KiCad10.0.0, bundled native Python and Freerouting2.5.0/Java25.0.2 where applicable. Source and frozen helper/code/tool hashes are in each summary. These are owned development fixtures, not independent corpus families or confirmatory data.

| Invocation | Git/code identity | Stored wall / total CPU seconds | Outcome |
|---|---|---|---|
| geometry001 | 099cc8f; driver ed758864… |13.360307 /9.203077 |Invalidated at summary readback; all six individual native case predicates met |
| geometry002 | efc174e; driver12d4eac8… |13.469755 /9.037068 |Completed; all six native control predicates passed |
| forced-via001 | efc174e; driver12d4eac8… |6.759127 /4.816742 |Completed; real engine/SES/import plus native positive passed |

The geometry budget is60seconds wall and measured parent-plus-waited-child CPU; the separate forced-via budget is120seconds. Stored totals precede final summary publication/freshness recheck; acceptance caps include both. Diagnostic costs are not a routing benchmark. No native jobs were delegated or run concurrently.

Geometry002 has one clean positive and five deliberately invalid route variants. All preserve original source/project/pad/board geometry, all have zero opens/exclusions, and each negative requires the actual native error on the specified route UUID:

| Control | Blocking / warnings | Observed original-rule finding |
|---|---|---|
| Positive |0 /0 |No findings; seven0.3mm segments and one1.5/.3mm via |
|0.2mm track |1 /1 |track_width; additional unchanged-policy connection_width warning |
|0.2mm copper gap |3 /0 |clearance, including both targeted parallel segments |
|0.6mm via diameter |2 /0 |via_diameter and annular_width |
|0.2mm drill |1 /0 |drill_out_of_range |
|0.2mm annulus |1 /0 |annular_width |

The forced-via fixture connects one net between an F.Cu-only SMD terminal and a B.Cu-only SMD terminal with no other conductive interlayer object. Freerouting emitted an actual SES; route-only native import yielded eight route objects including one SIGNAL_A through-via. Fresh native readback confirmed1.5mm diameter and0.3mm drill, original floors/class/pad identity, and final refill/DRC had zero opens/blocking/warnings/exclusions. The original seven ignored checks remain unchanged. Zero vias, no SES, altered dimensions or a failed native report would reject this control.

Geometry001 is retained as an invalidated invocation. Its negative expected-findings tuples became JSON arrays; comparing decoded arrays against Python tuples caused a false difference. Draft002 snapshots a strict canonical JSON representation before writing, rejects duplicate/nonfinite fields and compares strict decoded content. Eight new regression controls reproduce the exact old failure and exercise semantic/boolean tamper rejection. Together with23 retained preparation controls,31 pass in both ignored and public diagnostic copies. These pure controls do not replace the native runs.

## Source and reproduction

The small four-terminal PCB geometry is project-owned. Its complete project settings are unchanged from the pinned licensed KiCad multichannel project, SHA256 `ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538`; source notices are retained under each `source/_licenses` and the diagnostic fixture. Fixture board SHA256 is `dc396dfab9dfbd51a0d75cc8d8457b91c3dbac55358c0f5f84dca83dea97ee38`. The exact executing helper snapshots are in each run's `code` directory.

The public diagnostic driver is runnable from this checkout after toolchain and manifested data verification. Use fresh output identifiers; never overwrite a prior run:

```sh
python3 -B -m unittest discover -s evidence/board-floor-native-draft-002 -p 'test_*.py' -v
python3 -B evidence/board-floor-native-draft-002/driver.py --out .runs/board-floor-geometry-reproduction-001 --stage geometry --run-native
python3 -B evidence/board-floor-native-draft-002/driver.py --out .runs/board-floor-via-reproduction-001 --stage forced-via --run-native
```

The two reproduction native commands above have not been executed; the actual runs used the byte-identical reviewed ignored driver at `.runs/board-floor-native-draft-002/driver.py`. Root did execute the public copy's31 pure tests. This driver is a diagnostic, not an installed routing feature.

Selected exact raw evidence is in `evidence/board-floor-geometry-001`, `002` and `board-floor-forced-via-001`, with scope and per-file hashes. Full raw trees remain in `.runs`; selected copies omit KiCad/engine configuration. The ebbb56c tested private archive covers all three native floor invocations and their independent reviews, with25,514non-Gitfiles restored and all Git refs verified. Archives are on this Mac only.

Independent read-only audits verified1,914 fresh geometry002 bindings,607 forced-via001 bindings and1,455 selected-public-copy checks. They independently decoded SES geometry and compared it through imported/final/native-readback objects. Review records are in `evidence/review-board-floor-geometry-002` and `evidence/review-board-floor-forced-via-001`; AI review is not human PCB or physical review.

Production CLI integration, final receipt reconstruction and policy downgrade protection are implemented under the explicit `route --guidance board-floors-v1 --adapter both` option. All 364 software tests passed in the main checkout; independent review cleared two reproduced publication/transport defects after fixes. Selected review records are in `evidence/review-board-floor-production-001`. Actual production execution is recorded below. Strategy propagation and floor GUI handoff remain unsupported. No source eligibility, completion-rate or physical/electrical claim is added by this diagnostic.

## Actual production execution at e12cdc4

The `route --guidance board-floors-v1 --adapter both --profile completion-only` option completed all eight actual stages on the owned fixture. `evidence/board-floor-production-native-001/result.json` accepts zero opens/blocking/warnings/exclusions, seven segments plus one required 1.5/.3 mm via, 67.926667 mm total length. Candidate SHA256 is `79c46687d355a60f3917794f277ef41fb839088622123784dddc55c13e23af06`; receipt readback passed. Stored pre-publication totals are 7.277325 wall / 5.137059 CPU seconds under60secondcaps; caps include final publication/checks but this invocation has no separate enclosing timer. Independent review passed30binding checks and all116selected public files match raw evidence. This fixture has zero zones, so the real refill stage alone adds no nonempty-zone coverage.

The full multichannel exploratory run also completed all native stages under original settings, including six zones. `evidence/board-floor-multichannel-001/result.json` remains rejected with160opens,1blocking thermal,94warnings,0exclusions; candidate SHA256 `b5da43c9fc38cc1d5e006f144cc8747528313137cb114e37c27d86a5bf3938a3`. Stored pre-publication totals are57.378238wall/64.509057CPU under120secondcaps. None of the older attempt's75track_width,13clearance,3annular_width or3via_diameter errors remain. Opens did not improve. This descriptive historical comparison is not a fresh equal-budget pair, a valid-quality comparison, or C novelty. A prospective matched development repetition is pending.

Integration regression: the original native-policy smoke accepted with a nonempty zone (7.878404wall/4.795079recordedCPU), and all six actual literal-class controls passed (17.161423wall/13.096545enclosingCPU). Real SIGTERM during the floor engine yielded cancelled/false, complete cleanup and immediate absence of its owned process group; original source/code stayed unchanged. The cancellation control's inherited key `engine_cancelled_by_sigint` is misnamed: frozen code and the engine receipt actually require and record SIGTERM. These are scoped controls, not OS-crash or GUI qualification.

Reproduce only when needed with new output identifiers:

```sh
python3 -B -m autorouter route tests/fixtures/board-floor/fixture.kicad_pcb --output .runs/floor-fixture-NEW --seconds 60 --adapter both --profile completion-only --guidance board-floors-v1
python3 -B -m autorouter check-result .runs/floor-fixture-NEW/result.json
```

All production raw runs and new reviews are newer than the latest ebbb56c full private archive and await the next tested archive. The public selected text copies are individually hashed; originals remain in this durable checkout.

## Additional production controls and next diagnosed export defect

Five fresh controls at2ea2b48 passed with the actual production validator: clean positive;0.2mmtrack native width error and exact-guidance rejection;0.6mmvia native diameter/annulus errors and exact-guidance rejection; sole required via removed, producing native opens and rejection; and changed project width severity, rejected despite a clean diagnostic DRC. All share60seconds wall/CPU; stored pre-publication8.913714208wall/6.324479CPU. Exact evidence is in `evidence/board-floor-production-controls-native-001`. The diagnostic helper's23pure controls pass both from its frozen ignored draft and public copy.

Nine offline relocated-receipt controls also passed. Every negative first passed full readback after deliberate path/hash relocation of actual evidence. Missing SES/import/refill, consistently forged source command, policy downgrade, wrong width, changed candidate rules and stale disposable source all then rejected for intended reasons. These are consistency tests, not new native execution/authentication (`evidence/board-floor-receipt-controls-001`).

Remaining160opens led to a new diagnosis: four original enabled placement areas explicitly allow all five keepout categories but correspond exactly to eight generic DSN keepouts. Version-matched exporter source confirms that fallback, while native DRC applies no implicit keepout prohibition when all five flags allow. `evidence/placement-area-diagnosis-001` and `evidence/placement-area-export-review-001` bind the observation and primary sources. Selective correction is not implemented or causally tested. Genuine restrictions and original placement areas must remain untouched; same-load native controls, conservative unambiguous mapping and an explicit new policy are prerequisites. The reviewed two-arm floor-only pair remains unexecuted; a future matched ablation should include the placement correction after qualification.

## Preservation update

The full8799c54 private archive was actually restored: all Git refs,28,416non-Gitfiles /940,519,944bytes and CLIhelp passed. It covers every floor run/control/review above, source-closure002, deferred pair draft/review, placement source diagnosis and partial placement drafts at freeze. Later placement edits are outside the snapshot. `evidence/backups/restore-8799c54.json` records the verified restore; complete private artifacts remain on this Mac only. An initial secret-guard stop was traced to an exact copy of the public synthetic-header unit test; only its exact path+digest exception was added, with altered-content/path rejections and367full-suite tests passing.

Placement native001 subsequently confirmed the allowed-area mismatch but **failed** its genuine-prohibition controls: native KiCad reported no violations. The production common support gate now rejects all genuine/ambiguous rule areas. A pure selective transform and41 controls exist, but no routing result yet. New diagnostic work is limited to explicit all-allowed placement areas; see [scope and raw evidence](placement-area-diagnostics.md). The earlier pending-work paragraph is retained as chronology.
