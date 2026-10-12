# Failed SES native001: independent stored-evidence review

The recorded failure is correct and remains a failed diagnostic. The actual baseline DRC completed with 0 opens, 0 blocking errors, 41 `lib_footprint_issues` warnings and 0 exclusions. The positive SES import exited 0, but the next original-project file guard rejected its generated project. No positive DRC, negative import, negative DRC or candidate emission occurred.

The generated `.kicad_pro` has exactly three additional JSON fields: `/board/design_settings/rule_severities/track_not_centered_on_via` = `ignore`, `/board/ipc2581/bom_rev` = empty string, and `/board/ipc2581/sch_revision` = empty string. The generated project also adds `pic_programmer.kicad_prl`. The baseline native report already records the first check as ignored; this observation does not justify permitting changes to the original project. The proposed isolated import output followed by a complete original-project validation copy avoids using these generated settings.

All 15 original project files and the complete run remained unchanged during this readback. All 116 frozen artifact hashes and 45 recorded source snapshot hashes match. Both recorded process rows match their raw process receipts, cleanup completed and logs were not truncated. The copied observation input exactly matches the original project. The raw imported board's immutable AST equals the original; its route census is 368 segments versus 370 original segments, with exact via geometry equality. Prior precision and segment-survival failures remain failures; clean native DRC would not waive them.

Stored job cost is 4.074749 s wall / 2.985192 s full CPU. The outer wrapper records 4.315880 s wall / 3.168445 s waited CPU and exit 1. These include the two executed stages and the failed guard; they do not include the unexecuted stages.

Reproduction: `python3 .runs/review-pic-ses-native-001/audit_actual.py`. This performs only stored-file/shared-validator readback; no native, JVM, compiler, engine or network work. `actual.json` contains exact source/run and output hashes. A first reviewer assertion used the wrong JSON path spelling (`drc_severities` rather than `rule_severities`); its script and explanatory error note are preserved. That reviewer error did not alter any original evidence.

The review clears the stated failure diagnosis only. The finish-native continuation still requires a separate source review and a fresh ROOT-run native result.
