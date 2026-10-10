# Board-floor guidance qualification

This is a native-tested diagnostic and an integrated adapter correction awaiting its first production CLI native run. It is not a new routing strategy or a completed multichannel board. Original board/project rules, native class preferences and DRC severities remain unchanged.

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

Production CLI integration, final receipt reconstruction and policy downgrade protection are implemented under the explicit `route --guidance board-floors-v1 --adapter both` option. All 364 software tests passed in the main checkout; independent review cleared two reproduced publication/transport defects after fixes. Selected review records are in `evidence/review-board-floor-production-001`. These software checks do not qualify actual production routing. Full-board floor routing, native production qualification and strategy propagation remain pending; floor GUI handoff is deliberately unsupported. No source eligibility, completion-rate or physical/electrical claim is added by this diagnostic.
