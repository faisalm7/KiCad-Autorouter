# Padstack native-controls review

Passed 190 read-only binding and predicate checks across retained runs001 and002. No native jobs were run by this reviewer. Exact candidate/project hashes, native input copies, raw reports, target UUID uniqueness, source/tool/implementation hashes, commands, logs, cleanup and verdicts agree.

Run001 remains failed: positive and wrong-paste warning controls work, but the SMD-hole recipe emits no findings. Run002 passes: positive has no findings; wrong-paste emits exactly a targeted `padstack` warning with zero native errors; the 2mm circular PTH pad with 0.000001mm drill emits targeted `padstack_invalid` and `drill_out_of_range` errors, with zero opens/exclusions. Both errors remain recorded. Runtime: 1.875649s wall / 1.465135s CPU.

The finding namespaces differ: the project configures `padstack` as warning; the invalid tiny drill emits `padstack_invalid` as error. A generic drill error is insufficient for this negative control. The exact padstack-invalid type, error severity and unique target pad UUID were checked independently.

No blocker to the diagnostic. Production remains unchanged and still refuses the source project's warning-severity padstack setting. A future support expansion must reject actual `padstack`/`padstack_invalid` findings independently of severity everywhere acceptance is evaluated; changing preflight alone would weaken validation. Keep native reports/severities and original rules unchanged. These one-pad/no-net controls do not qualify the full project or routing connectivity.

The scripts saved in each run match their execution receipts. Whether each script matches the recorded HEAD is explicit in review.json; corrected snapshots must not be mislabeled as precommitted source. No tracked edits.
