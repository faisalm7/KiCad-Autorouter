# Current status

Updated October 13, 2026. Active local reconstruction, not release-ready. This is the durable Mac checkout `/Users/faisal/Projects/KiCad-Autorouter-local`, on `rebuild/local-20261010-015447`. No cloud environment or managed worktree was used. [Previous complete status](docs/history/2026-10-13-b6688de/STATUS.md) preserves the experiment chronology and failures.

## Latest outcome

Acquisition006 completed the five pinned Devobordo source files, retaining every prior input. The population is **21 acquired development boards: 4 statically eligible, 17 unsupported**. There are 22 board files because the coldFire audit copy is byte-identical to its already counted original; both remain visible. Static eligibility is not native acceptance. Three prior accepted inputs come from the same KiCad demo collection; no independent designer pedigrees or generalized completion rate is established. [Population](evidence/licensed-acquisition-006/population.json).

The new RP2040 board is **native-invalid**: real original-rule refill/DRC reports 0 opens, 1 USB-shield starved-thermal error and 40 library warnings. Schematic parity adds 34 field-mismatch warnings. DSN export, metrics and native save ran once. Its strict protected-route readback then rejected the extra via fields emitted by KiCad10. All619 route UUIDs remain; after existing net conversion, all573 segments/arcs are exact, while all46 vias acquire capping/covering/plugging/filling=no fields. No wider normalization, PCB acceptance or electrical equivalence is inferred. Original source and notices remain exact. Five workers cost4.200633wall/3.064917fullCPU seconds. [Actual evidence](evidence/devobordo-original-native-001/SCOPE.md). Preserve this failed diagnostic; do not repeat it.

Selected-net routing is newly implemented across saved preferences, preview, native pipeline, central readback and separate-project export. It reroutes only selected unlocked copper, preserves every nonselected/unnamed route and locked selected route, rejects other-net additions, and keeps full native original-rule acceptance. It uses native completion-only profile and source_all layers; other combinations reject. Complete native schematics require final schematic-parity DRC. **New native qualification is prepared, not executed yet.** Targeted100controls pass2.486s; these are software checks, not routing-quality evidence. The prepared two-case protocol is `.runs/selected-net-native-input-001/protocol.json`, SHA1048fd95d81f02e63e6eef86c4cea56a3b235ad9ddef2621864cb5c6671a38d9. Skeptical integration review is active.

The conservative Devobordo LED task selects GPIO25 and Net-(D4-A), removes15 selected routes and preserves604 others, including all USB/QSPI/crystal/power/ground and uncertain GPIO/debug copper. It is source-invalid and not a superiority experiment: current zone-net pruning has no eligible new mechanism on this scope. No repair outside this scope is authorized by task preparation. Creator battery and electrical cautions remain in the source README.

## What works now

The offline CLI snapshots full projects, runs Freerouting2.5.0 with pinned KiCad10.0.0/Java25.0.2, imports, refills, validates original rules and emits separate candidates. It needs no AI account at runtime. Existing narrowly qualified paths provide saved whole/partial routing settings, protected original routes, allowed-new-layer lists, actual native before/after plots, cancellation, stale-result checks, persistent accept/reject intent and fresh native separate-project export. Intent is not human PCB approval. [Preferences](docs/routing-preferences.md), [GUI procedure](docs/gui-workflow.md).

```sh
.venv/bin/python -B -m autorouter doctor
.venv/bin/python -B -m autorouter settings-init --output routing-settings.json
.venv/bin/python -B -m autorouter preview /path/to/board.kicad_pcb --settings routing-settings.json
.venv/bin/python -B -m autorouter route /path/to/board.kicad_pcb --settings routing-settings.json --output .runs/my-route-001
.venv/bin/python -B -m autorouter review-copy .runs/my-route-001/result.json --render --output .runs/my-review-001
```

Use fresh output paths. Open a disposable review `.kicad_pro` through KiCad project manager, then Tools → PCB Editor. Actual earlier GUI checks are narrow; new exporter GUI qualification is blocked by the locked Mac. No live-editor application/undo or human/physical review is claimed. Continue independent work while the unlock request is pending.

## Measured routing contribution

Multichannel pair003 at3f757c0 assigns all B0/B1/B2/C arms equal120second wall/fullCPU caps. B1/tunedB2 accept2640.198552639mm/19vias; C accepts2567.215252639mm/19vias, **72.9833mm shorter**, with0opens/0blocking/all96identical warnings. C charges its own standard85 incumbent and two separately native-valid deletions. Conservative fullouter C111.25304CPU remains below120; it uses more compute. B0 rejects160opens/49blocking/125warnings. Pair001's C budget rejection and pair002's tie remain. [Actual pair003](evidence/placement-paired-003/SCOPE.md). This is one exposed, explicitly nonworking audio layout demo, not generalized or independent-family superiority.

Other exposed KiCad-demo experiments: sonde nativeC648.045171mm/2vias versus stronger equal-budget B2749.441643mm/2vias; interf_u thermalC accepts while tested B0/B1/B2 reject under equal120caps. [Quality](docs/quality-experiment.md), [thermal](docs/thermal-experiment.md). Different mechanisms and exposed inputs cannot be pooled into a confirmed completion-rate claim. No physical/electrical validation or human cleanup-time measurement exists.

## Integration and backups

Latest full production suite before modern/selected changes:763tests pass30.805s. Installation010 atd1c40cc passed20network-denied commands, a clean local clone/venv suite and real native0findings/1via/67.933738mm. Complete outer76.455530wall/79.126278CPU. Installed review/intent/fresh-export/check/reject and four plots passed, but its stored16.805164wall/18.366797CPU omits initial/final file scans; full workflow envelope is unmeasured. It does not qualify the subsequent early cancelled-budget fix, modern guards or selected scope. Current full suite, native selected controls and installation011 are due at integration.

Latest independently read-back GitHub checkpoint before these changes: **b6688de93b81ac7910e8cf7ae2625d340f370bc7**; remote SHA and acquisition-controller bytes match. No formal release/package was published.

Full backup/restoration atbe0732ad1dd59035c4d57cdef66ab6bf5df20d02 passes138215non-Git files/4116993307bytes, allGitrefs/bundle/restoredCLI and retained threat-link representation. [Receipt](evidence/backups/restore-be0732a.json). Incremental parent `.local-backups/checkpoint-20261013T151235Z-0e3fdfe54f8b489ca5d5c7fe24830e98/receipt.json`, SHAca4afbd6761b0e9ef921bb908e6592327a65f37f79d3d83c2add5e073100fcbe. A later read-only census observes138770files/4132311812bytes; current finite4GiB/140000file bounds can preserve intervening small work, but another retained installation will require a measured capacity change and full restoration. Never delete evidence or exclude scopes to fit.

GitHub preserves audited source and selected evidence. Complete raw runs/data/private references/archives remain **on this Mac only**; off-Mac protection is still unmet. Incremental integrity is not full restoration. Run full restore at major integration/cap changes/pre-release, not every minor edit.

## Remaining gates

G3 representative30–50-family failure audit, generalized G4 gains beyond B1/B2, full G5 integration/GUI and current install, G7 untouched family-disjoint evaluation, and G8 experimental release candidate remain open. Source-invalid Devobordo, protected via serialization, custom pads/net ties/rules/legacy formats, library/model closure and electrical checks remain visible. Modern semantic native001 stays failed on its literal hole-threshold predicate; separate source-bound readback verifies observations without rewriting or rerunning it. Learning is not justified; no model exists.

Next: execute the prepared selected-net positive/unselected-open controls once with current committed code, diagnose actual failures, finish skeptical review and safe workflow checks, then broaden supported board families and matched experiments. See PLANS.md. No auto-resume loop or background benchmark is running.
