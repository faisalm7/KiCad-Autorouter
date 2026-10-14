# Sensor support semantics review

Both `missing_tuning_profile` and `track_on_post_machined_layer` are valid pinned KiCad10 DRC enums, settings keys and project `rule_severities` fields. They are neither misspellings nor renamed aliases. Modern rule-area net omission is also intentional native serialization. These facts do not admit the unchanged sensor board: additional original metadata and a restricted footprint area remain unsupported.

This review executed no native/JVM/Git/network commands and changed no original/core/data files. Seven cached primary files were rehashed against their receipts at KiCad10.0.0 commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`; full locations, short excerpts, URLs and hashes are in `PRIMARY_LOCATIONS.json`.

## Two severity keys

`drc_item.cpp:305-315` maps `DRCE_MISSING_TUNING_PROFILE` to `missing_tuning_profile` and `DRCE_TRACK_ON_POST_MACHINED_LAYER` to `track_on_post_machined_layer`. Both appear in the configurable-severity item list at349/394 and native factory dispatch at472-473. `board_design_settings.cpp:337-375` loads/saves registered keys under `rule_severities`;167-168 initialize all checks to error, while209 explicitly sets missing tuning profile to warning. The unchanged sensor supplies warning and error respectively. Preserve these exact supplied values and all other keys; no project migration or repair is needed to recognize them.

The missing-profile provider at `drc_test_provider_misc.cpp:530-565` emits only when a class has a referenced profile absent from loaded profile definitions. The sensor's class profile is explicitly empty and definitions list empty; current `netclass.reject_tuning_intent` accepts that inactive state. Nonempty assignments/definitions remain independently unsupported, even if a severity key is recognized. Recognizing the key must not imply timing/impedance/tuning-profile support or suppress any finding.

`drc_test_provider_connectivity.cpp:117-178` checks tracks/arcs connected to pads/vias on backdrilled or post-machined layers. `IsBackdrilledOrPostMachined` identifies removed-copper layers before the exact native finding is emitted. This is an electrical constraint. Recommendation: recognize it and retain the supplied error; make its warning/ignored/excluded forms fail the same critical-check acceptance policy. Do not add a broad warning whitelist.

## Omitted zone net

For `keepout`, parser8156+ marks a native rule area. At8472-8478, `zone_has_net = zone->IsOnCopperLayer() && !zone->GetIsRuleArea()` determines that rule areas are unconnected and calls `SetNetCode(UNCONNECTED)`; the adjacent primary comment explicitly identifies netcode0. Formatter2854-2855 writes a net only for an ordinary copper zone with positive code, so it deliberately omits net from rule areas. The sensor root pour-only area has neither net nor legacy net_name; its five restrictions permit tracks/vias/pads/footprints and prohibit only copper pour.

A narrow future metadata extension could accept absent net only for an otherwise qualified rule area, retaining its original missing-token AST/hash. Keep rejecting explicit nonzero/unknown/malformed net and nonempty legacy net_name. The parser's legacy-name repair runs AFTER the reset at8480-8503 and can rebind the area to a named net; the existing empty-name guard is therefore material. Do not insert `(net0)` into the source or a published candidate merely to get past preflight.

That source-backed semantic equivalence still needs the smallest owned native observation: load an authored absent-net root area, verify UUID/flags/layer/outline and `GetNetCode()==0`, save and confirm deliberate omission, then reuse the existing saving-refill/native BooleanIntersection acceptance path. Retain original rules and all warnings. An intentionally intersecting saved fill must reject; nonsaving DRC alone is insufficient. Such a test has not run here and should not repeat any completed explicit-net control.

## Independent unchanged sensor blockers

Current actual preflight rejects the two unknown keys and explicit-net requirement. Scratch-only diagnosis revealed two additional gates in sequence; neither copy is a candidate or source repair:

- After adding net0 only to a copied root AST, `_metadata` rejects the original `(island_removal_mode0)` as unknown rule-area fill metadata. KiCad's formatter3005-3012 serializes this field. Its applicability/allowed scope remains unqualified here; do not remove it from the original.
- After removing that field only in the diagnostic copy, qualification still rejects U3's footprint zone. That `Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm`/MPU-6050 area forbids tracks, vias, pads and copper pour, with footprints allowed. Current native restriction policy does not qualify restricted footprint areas, and board-only pour auditing explicitly excludes any footprint zones. Preserve this restriction and unsupported reason; do not treat an exported keepout or unchanged polygon as independent native validation.

The original contains four root zones and one footprint zone. Its PCB/project/schematic hashes and complete source inventory are unchanged. No original native DRC/parity/roundtrip result or routing-quality measurement was produced or inferred. The clock board mentioned by the parent is a different lead and its failures are not sensor evidence.

## Smallest key-only regression/native qualification

For a different simple board blocked only by these names, make the change limited to recognized names plus conservative critical handling of the removed-copper check. Keep all original project values, rule files, net classes, severities/exclusions and actual native acceptance checks.

Use targeted pure regressions on an authored complete simple project containing warning/error for the two keys: preflight accepts the names without changing the file bytes; unsupported severity values and active tuning intent reject; track-on-post-machined warnings, ignored checks and exclusions reject; full raw warnings stay reported. Existing profile-assignment/definition regression helpers should be reused rather than replaced.

The smallest new native pair is one ordinary complete positive with those exact project entries and no active tuning/post-machining, plus one deliberately invalid authored track ending on a backdrilled pad/via layer. Run through shared native validation, original-project binding, all-severity DRC and final candidate hash checks; require the exact `track_on_post_machined_layer` finding with the intended item UUIDs/layer in the negative. Primary pad.cpp586-656 and serializer1733-1775 identify the backdrill/post-machining representation, but a correct executable fixture still needs native confirmation. No setter/API availability or negative emission is claimed tested here. Missing-profile warning emission could be a separate direct diagnostic if needed; it does not authorize active profile routing.

A positive key-only native control may establish metadata support for that simple lead. It cannot establish sensor footprint-keepout support, source cleanliness, production release readiness, or comparative routing gains. Keep any original findings visible and unsupported cases in the population.

`AUDIT_INITIAL_FAILED.py` and `INITIAL_FAILURE.txt` preserve the reviewer's premature expected-next-gate assertion; the corrected audit identifies the island metadata gate before the footprint gate. `AUDIT.py` is executable read-only reproduction. Public selection contains only owned code, aggregate metadata, hashes and this report; raw boards, geometry and upstream source are excluded.
