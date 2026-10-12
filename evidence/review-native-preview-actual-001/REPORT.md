# Actual native preview and failure-evidence audit

Disposition: the five retained outcomes are consistent with their raw artifacts. No material gap found in this scoped readback. All nine inspected run/source trees remained byte-identical. No native, plot, JVM, GUI, Git or network command was executed by this review.

All outer records identify verified source checkpoint `5d4703dc573d6f82469f1ef0066c702d4a01db45`. Wrapper/log hashes match. Current helper source matches recorded source pins. Both existing routing receipts pass the shared central checker; this is evidence consistency, not repeated DRC.

| Control | Actual outcome | Stored wall / full CPU (s) | Outer wall / waited CPU (s) |
|---|---|---:|---:|
| Fixture preview 003 | Ready; four successful native SVG plots | 2.270462 / 1.958191 | 2.514372 / 2.159179 |
| Multichannel preview 001 | Ready; four successful native SVG plots; 96 saved warnings | 11.273587 / 10.702060 | 15.361793 / 14.704250 |
| Display tamper 001 | Rejected after two successful plots; no ready HTML | 1.304761 / 1.020813 | 1.439505 / 1.117539 |
| Cancellation 001 | Native cancelled with SIGTERM/exit −15; review rejected; no ready HTML | 0.172548 / 0.154738 | 0.352304 / 0.254627 |
| DRC failure-evidence control 001 | Clean unchanged positive; clean raw legacy-PRL DRC nevertheless rejected by preservation guard | 1.624837 / 0.871564 | 1.820614 / 1.022689 |

Stored totals precede final checks as declared by the records; the outer costs are retained separately. Each complete outer invocation is below the 30-second wall/full-CPU ceiling. Polling/resource samples are not hard OS quotas.

For both ready previews, the complete original, candidate and advertised review copies match their inventories. All eight complete private plot inputs match before/after bindings, with only the allowed new basename PRL added. Existing original boards, project files, rules and routing evidence remain unchanged. All 65 fixture / 93 multichannel bound preview files match; displayed SVGs equal the exact saved native SVG with only the observed standard DOCTYPE removed. Every plot argv names its own private input and performs SVG export only: no refill, DRC, route or apply step.

The fixture's saved native counts are all zero. Multichannel retains 0 opens, 0 blocking, 96 warnings and 0 exclusions: 81 `lib_footprint_mismatch`, 9 `connection_width`, 4 `silk_over_copper`, 1 `silk_edge_clearance`, 1 `nonmirrored_text_on_back_layer`. A ready preview is not whole-project cleanliness or visual/electrical approval.

The tamper control preserves the first display's original bytes; they match the raw-to-display derivation. The intentionally altered display differs and triggers the completed-stage guard. Cancellation records the actual supervisor SIGTERM, matching native process PID and `cleanup_complete=true`; the bound controller checks the process group is gone before its successful outer exit. This audit does not query an old PID that could have been reused.

Both actual DRC reports in the failure-evidence control have 0 opens/blocking/warnings/exclusions. The negative is an owned synthetic existing version-3 PRL fixture; its validation copy changes only `fixture.kicad_prl`. The shared preservation guard still rejects it. `legacy-prl-failure.json` retains the exact project-preservation error, before/after copies, raw report/log/process sizes and hashes, with no capture errors. The original fixture and synthetic input remain unchanged. Clean raw findings do not override this failed validation; PAW was not rerun.

The retained browser attempt was blocked by the browser's file-URL policy. `visual_inspection_performed=false` and `workaround_attempted=false` are preserved byte-for-byte in `browser-attempt.json`. There is no browser visual-inspection claim.

Reproduce this offline audit with `python3 -B .runs/review-native-preview-actual-001/audit.py`. The first audit attempt completed substantive assertions but hit a reviewer bookkeeping TypeError while hashing canonical JSON text; that log and earlier script are preserved. The corrected audit encodes that text and passes. The selection excludes boards, libraries, SVG/HTML media, generated settings and duplicate payload trees; ROOT curates actual run evidence separately.
