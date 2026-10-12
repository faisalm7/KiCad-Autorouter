# Corrected multichannel GUI/CLI comparison

This is an offline audit of retained evidence, not a new native or GUI run. The earlier statement that nine `connection_width` warnings occur only in the GUI is false. The historical summary remains unchanged and is hash-bound by this audit.

| Actual retained report | Library findings | Connection width | Other warnings | Total |
| --- | ---: | ---: | ---: | ---: |
| CLI final DRC | 81 `lib_footprint_mismatch` | 9 | 6 | 96 |
| GUI DRC | 114 `lib_footprint_issues` | 9 | 6 | 129 |

All fifteen nonlibrary records match exactly as a multiset, including severity, full description, item UUIDs and positions, and duplicate multiplicity. The six other warnings are four `silk_over_copper`, one `silk_edge_clearance`, and one `nonmirrored_text_on_back_layer`. Both reports have zero opens, errors and exclusions, the same seven ignored checks and KiCad 10.0.0. The connection-width descriptions in both use the same 0.3000 mm board minimum. There is no GUI-only connection-width failure to diagnose or justify changing production policy.

The CLI report SHA is `ce780053bb51d2b131db586c87ec02d81ea8619eaf5bbe8967439259e768d5a6`; GUI report SHA is `81c2b25dfc984a15c639756d475fe910728fa211b8089d3c10bda2b54a4077d2`. Both refer to the saved candidate `65dd3b0e6e0bfe6bf45a84b58d94eb4388a8b318967c47c40c26714b6777a0ef`. `audit.json` contains the full fifteen records, input bindings and process receipt. The original 17-file source, complete 175-file accepted run, and 53-file post-GUI disposable project equal their retained inventories before and after this audit. The CLI final process used network-denied `kicad-cli pcb drc --format json --severity-all --all-track-errors --refill-zones --exit-code-violations`, returned the expected violation exit 5 and retained its full count log; cleanup completed. The GUI observation was manually recorded separately from routing budgets.

## Actual library difference

The delta is **33**, entirely within library findings. GUI has exactly one issue for every one of the 114 board footprint UUIDs, all with the same message: the project library `multichannel_mixer` is not enabled in the current configuration. CLI instead compared against that library and reported mismatches on 47 resistor, 29 capacitor and five SOIC footprints. These 81 UUIDs are a subset of the GUI's 114; neither totals nor differing types are interchangeable.

Pinned KiCad 10.0.0 source establishes distinct branches: `drc_test_provider_library_parity.cpp` lines 1054–1068 gets the adapter from the board project; lines 1115–1127 report the exact GUI message when `HasLibrary(name, true)` fails, then skip that footprint's comparison. Lines 1156–1194 load and compare the actual library for the CLI mismatch path. A genuinely absent project would instead skip library parity entirely. The CLI DRC entry point, `pcbnew_jobs_handler.cpp` lines 2291–2295, explicitly calls `AsyncLoad()` and `BlockUntilLoaded()`.

The project `fp-lib-table` and all seven project footprint-library files are unchanged between original, CLI and GUI copies. The table has a `${KIPRJMOD}/multichannel_mixer.pretty` path and no disabled field. The CLI's retained runtime configured isolated KiCad configuration/cache/documents paths; the GUI used its existing local environment. This establishes different runtime library resolution. It does **not** establish why the GUI adapter considered this row disabled; neither a global-table setting, cache defect, missing project association nor load-order bug was captured. No unrelated configuration was read or changed.

## Project-setting differences

The actual `.kicad_pro` has sixteen JSON deltas, all independently reproduced against `multichannel-project-changes.json`. Every original hard-rule value and severity remains unchanged; the sole Default netclass has identical dimensions plus an empty `tuning_profile` field. Original/candidate project SHA is `ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538`; GUI disposable project SHA is `afd236cda75abd253a673c8190b0ad4245482220de523aeaebdeecb50e857864`.

The six newly explicit severity values match the pinned native defaults: `footprint_symbol_field_mismatch=warning`, `missing_tuning_profile=warning`, `text_on_edge_cuts=error`, `track_not_centered_on_via=ignore`, `track_on_post_machined_layer=error`, and `tuning_profile_track_geometries=ignore`. `board_design_settings.cpp` initializes errors generally and overrides the corresponding warning/ignore values; `drc_item.cpp` binds these exact setting names. Its getter serializes defaults while its loader only overrides present keys. The two added footprint-dimension/barcode preference values are both the documented false defaults. `net_settings.cpp` lines 479–491 explicitly defines schema 4→5 as adding empty tuning-profile names. These are source-backed default materializations, not evidence that original severities were weakened. Empty component assignments/tuning profiles, IPC export strings and schematic metadata do not supply a demonstrated changed routing constraint here.

No changed effective geometric constraint is evidenced: all hard-rule values, netclass dimensions and actual geometry findings match. This is narrower than complete native-state equivalence. The saved `.pro` bytes did change, the GUI library environment differed, and no complete GUI effective-state snapshot was obtained. This audit keeps `gui_qualified=false`; it does not retroactively qualify semantic migration, schematic parity, clean full-project DRC, electrical/manufacturing correctness, or physical review.

## Smallest useful follow-up

A single prospective GUI observation via the **project manager** is reasonable. The installed 10.0.0 manager bundle declares `.kicad_pro` as an owned project document; the previous protocol opened the disposable board directly. This supports feasibility, not a prediction of success. Prepare a new complete review copy through the existing handoff, verify the exact candidate/project/library hashes, open that copy's `.kicad_pro` in KiCad Manager, then open its PCB from that project. Observe exact project/window identity and wait for ordinary project initialization; do not toggle libraries or alter settings. Run the same refill/all-severity GUI DRC, save JSON, compare all fifteen geometric records, seven ignored checks and library UUID/type counts, and close/discard only this owned copy. Preserve prior runs and any fresh failure. Limit this manual diagnostic to one attempt, ten active minutes and 64 MiB of project outputs; report GUI time separately, with no routing CPU/performance claim. A reduction to the CLI's 81 mismatches with unchanged nonlibrary findings would support a project-entry-path explanation for this one session, not prove a universal cause. If the same 114 issues remain, preserve the limitation rather than change global configuration.

If effective project-default equivalence remains a specific gate, one separate two-arm **nonsaving DRC-only** diagnostic is enough: copy the original accepted candidate project twice; change only arm B's `.kicad_pro` to the exact already observed GUI bytes. Use one existing `pipeline.Job(output, 60)` and its `drc` method sequentially, with original-rule input binding, bounded runner, network denial, source/tool/code freezes, complete per-stage capture and shared 60-second wall/full-CPU acceptance ceilings. Bound complete outputs to 32 MiB, retain both raw reports and all generated PRL files, and compare exact nonlibrary findings and effective ignored checks. This tests default materialization under one isolated CLI environment; it cannot diagnose GUI adapter initialization. It is optional, unexecuted, and should not precede the cheaper single project-manager hypothesis merely to repeat the already matching connection findings.

Reproduce the offline audit from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .runs/placement-gui-discrepancy-analysis-001/audit.py
```

41 focused checks passed. No native, GUI, Java, engine, network or dataset script ran; no tracked/source/evidence files were edited. This review samples immutable local evidence and establishes consistency, not authenticity against a hostile concurrent writer.
