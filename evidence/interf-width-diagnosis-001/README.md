# Rejected native-class route: width diagnosis

Actual run `.runs/interf-native-002` remains rejected and unchanged. No routing or native-board job ran for this diagnosis. `diagnosis.json` binds the observed candidate, SES, DSNs, native maps and source/refill reports; `sources.json` binds official pinned source reads.

`/BIT5` is native Default class, target400000nm. Native and adapted DSNs both retain width400um in the global and class rules; their input wiring is empty. The actual SES has a width3000 path in resolutionum10, hence0.3mm. Imported, candidate and refill boards preserve that value exactly. This rules out import rounding. Across36nets,96generated segments are narrower than their class target (mostly0.3mm, also0.2mm).

The ordinary small-pad explanation does not match BIT5 endpoints: these are P1pin7 (1.6mm circular copper) and U9H12 (1.4mm circular copper), both wider than the requested0.4mm track. Pinned `FoundConnectionInserter` also has a micro-neckdown fallback that tries3/4,3/5 and1/2 of the class width. Its gate is `ctrl.isFanout || ctrl.withNeckdown`, so automatic-neckdown disable alone is insufficient during fanout. The observed0.3/0.2 widths match this mechanism. We did not instrument the individual routing call, so attributing each segment to that exact branch is a source-supported inference, not a captured call trace.

Primary sources:

- https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/path/FoundConnectionInserter.java#L232-L248
- https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/path/FoundConnectionInserter.java#L486-L518
- https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/maze/AutorouteControl.java#L168
- https://github.com/freerouting/freerouting/blob/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/autoroute/pipeline/AutorouteConnectionRouter.java#L125-L140

`static-targets.patch` is an ignored proposal only, touching pipeline, profile probe and profile controls. It adds `strict_class_targets` to the shared profile helper, invoked only when the existing literal-two-class qualification applies. Uniformly for all engine profiles in that scope it sets `--router.automatic_neckdown=false`, `--router.fanout.enabled=false`, `--router.neck_width_um=0`. Default-only established behavior remains unchanged. No original class, native rule, geometry, or validation gate changes. The lower trace count/completion implications are unknown; disabling these optional solver behaviors may leave opens.

The actual pinned JAR merged all three proposed flags correctly for standard/tuned/completion-only profiles. `.runs/static-target-profile-probe-001` retains request, actual values, process and result;67/67 actual settings checks and12pure profile controls passed. No router ran. `git apply --check` passed at preparation. After parent applies the reviewed patch, `python3 scripts/probe_engine_profiles.py --output <new absolute .runs child>` reproduces the expanded full24case profile audit.

A second native obstacle already exists: source DRC has two starved-thermal errors on zone`00000000-0000-0000-0000-00004cdec22b` and pad UUIDs`363a9f9a-0b01-4ef4-a972-9e6d1eab7c5a`/`7cc25ef2-8581-477e-8ad4-e0906ba743c8`; refill DRC has one on the same zone but new pad`a887d3fa-3fb6-43a1-8618-647e60045cbf` (U9G11). The latter is a different finding and remains blocking. Native connectivity reports zero opens; that does not override thermal rejection.

Next evidence: freeze reviewed static-target settings, route one bounded complete-copy qualification, verify every generated route dimension plus full native refill/final DRC. If widths now conform but thermals fail, retain rejection and diagnose/re-route GND copper against the original zone settings. Do not relax class targets, thermal-spoke minima, severities, exclusions, or counts to manufacture acceptance.
