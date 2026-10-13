# GUI/native library-warning difference

The reports are not equivalent warning sets. GUI reports **0 opens / 0 errors / 6 warnings**; authoritative native validation reports **0 / 0 / 10**. Both preserve exactly the same five legacy Datasheet parity findings and the same two ignored checks. The copied PCB bytes, authoritative candidate project inventory and authoritative export proof are unchanged. Neither result is whole-project clean.

## Exact difference

| Footprint | Authoritative native | GUI |
|---|---|---|
| D1 | LED_SMD library missing from current configuration | No library finding |
| R1, R2, R3 | Resistor_SMD library missing from current configuration | No library finding |
| J1 | Connector_USB library missing from current configuration | Loaded library footprint does not match board copy |
| SW1 | No library finding | No library finding |

J1's GUI finding is **`lib_footprint_mismatch`**, not the native **`lib_footprint_issues`** absent-library finding. All five Datasheet findings retain their exact descriptions, UUID/item records and warning severity. No finding was filtered by this audit. Ignored-check equivalence is exact: `track_not_centered_on_via` and `tuning_profile_track_geometries`. The earlier Roller-list hypothesis does not apply to these reports.

## Primary-source diagnosis

Pinned KiCad10 `drc_test_provider_library_parity.cpp:1088–1112` gets a footprint-library row by nickname and emits the missing-configuration finding only when that row is absent. It separately checks library enabled/loaded status and loads the particular library footprint. Only after those succeed does `1179–1188` call `FootprintNeedsUpdate(...,DRC)` and emit the mismatch finding. Thus the GUI J1 result proves the GUI provider reached a loaded Connector_USB footprint comparison, while native J1 stopped at an absent row. The available footprint-library context differs between those processes.

The four disappearing findings are consistent with GUI availability and matching library copies for Resistor_SMD and LED_SMD; the native process deliberately has isolated KiCad settings. This is a library-context diagnostic change, not routing improvement. The report alone does not record the exact GUI table rows, loaded stock-file hashes/revisions or provider limit state. Consequently, exact loaded-copy identity and why J1 differs remain unqualified. It would be too strong to infer a particular library release or exact J1 geometry difference without those observations.

The actual shared `Job` initializes fresh run-local `KICAD_CONFIG_HOME`, `KICAD_CACHE_HOME` and `KICAD_DOCUMENTS_HOME` directories. The complete project table contains only the project-local `usb_led` switch library. The retained native isolated configuration contains no global footprint table for the missing stock nicknames. Primary `pcbnew_jobs_handler.cpp:2291–2294` explicitly loads the footprint adapter before CLI DRC; this is not simply a provider skipped in CLI.

The missing definition of `PROJECT_PCB::FootprintLibAdapter` was fetched once from the already-pinned KiCad commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`: `pcbnew/project_pcb.cpp`,3916bytes, SHA256`9d04c71a43bbf2f6e7cadbed852d7b153be701b1588ac1749c4a7d61870258a7`. Its `39–59` returns/registers a footprint adapter on the process's `Pgm().GetLibraryManager()`. The separate3D cache/resolver path begins at62. No user/global personal table was read and no library/model asset downloaded.

## Model-path hypothesis

**Legacy3D model-path migration is not a demonstrated cause of these disappearing warnings.** The pinned `FootprintNeedsUpdate` DRC comparison (`773–1049`) compares footprint type/mask-bridge settings, stackup/layers, net ties, graphic shapes, barcodes, pads and rule areas. It ignores all text and does not compare `Models()` or model filenames. Its informational footprint-versus-board stackup helper also does not inspect3D models. Missing-library-row detection happens before any footprint comparison. A separate GUI3D migration may occur, but it does not explain these particular provider branches from the source inspected. J1 may differ in a compared property; that exact property has not been observed.

## Working-copy project metadata

Every originally explicit board rule, severity and netclass property still compares exactly. GUI serialization adds default keys, including the five current severity defaults. The class list changes structurally only by adding empty `tuning_profile` to Default, with net-settings schema4→5; all original class values remain unchanged. This corrects an overly coarse claim that the entire severity map/class array stayed byte-identical: the explicit original constraints are preserved, while GUI default materialization is visible. The authoritative project/proof remain untouched.

This audit does not authorize updating the source footprint from the stock library or suppressing J1's mismatch. A future equality claim must bind the relevant GUI library rows, resolved stock footprint revisions/hashes and native setting context; do not copy unrelated private library configuration or external models into evidence. Keep GUI0/0/6 and authoritative native0/0/10 separately reported. No complete GUI/application, electrical, physical or release qualification follows from this diagnostic comparison.

`gui-access.json` retains an earlier blocked access attempt and is not rewritten here. This report compares the actual stored DRC and current project metadata; it does not fabricate new GUI process/access evidence. `AUDIT.py` uses only existing read/hash helpers. `RESULT.json` contains safe aggregate findings, reference/UUID-free library summaries, metadata-key differences and exact report/input hashes. Raw board/library/model geometry is not included in the public selector. No native, JVM, GUI, Git, unrelated-file access or recursive delegation occurred; only the missing pinned primary source was retrieved.
