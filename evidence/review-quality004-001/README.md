# Independent stored-evidence audit: quality-comparison-004

`python3 -B .runs/review-quality004-001/audit.py` passed 7,063 checks with no remaining failed assertions. No native or routing process was launched. All writes are confined to this ignored audit directory.

The audit verifies frozen commit `221f26f2808b1918aca2a1df3b3f70b345605eb1`, exact implementation/protocol/source/tool hashes, unchanged source and candidate invariants, 57 candidate/raw-native-report bindings, recomputed geometry metrics, every successful and failed trial's process/CPU accounting, 825 exact public subset files (5,074,025 bytes), repaired HH:mm:ss profile assignments, and the retained same-JAR settings probe. All full invocations stay below equal 120-second wall and measured CPU acceptance ceilings. The public subset is intentionally not the complete local run; it lacks the full original/native-input project trees required for local check-result.

| Arm | Native opens/blocking/warnings | Length mm | Vias | Invocation wall s | Invocation CPU s |
|---|---:|---:|---:|---:|---:|
| B0 | 3/7/1 | 566.453919 | 4 | 10.657401 | 10.649935 |
| B1 | 0/0/1 | 786.315536 | 3 | 13.537638 | 16.707341 |
| B2 | 0/0/1 | 786.315536 | 2 | 18.258331 | 26.202142 |
| C_single | 0/0/1 | 662.694144 | 2 | 104.668819 | 83.404883 |
| C_feedback | 0/0/1 | 644.548871 | 2 | 107.793957 | 85.632711 |

Both C incumbents have the same route geometry as independent B2 (apart from UUIDs), and exactly equivalent adapted DSN geometry/rules/network after only output-path and generated keepout-label normalization. C_single has 25 trials: 20 improvements, 4 native rejections and 1 warning rejection. C_feedback also has 25: 21 improvements, 3 native rejections and 1 warning rejection. All are retained and charged once.

The mechanism is concretely visible. Feedback trial0001 deletes one 14.255273 mm GND segment, retains zero opens/blocking/exclusions, but creates two dangling-track warnings and is rejected. Trial0002 uses the same unchanged validated base and removes that segment plus the exact two warning-identified 1.835 and 2.055 mm stubs. It passes actual stored native validation with only the inherited J2 library warning. All warning UUIDs resolve uniquely to eligible unprotected same-zone-net route objects. The final C_feedback versus C_single geometry differs **only** by those three segments, with no extra route additions or other geometry changes. The incremental measured gain is 18.145273 mm (2.7381%), the same two vias, 3.125138 more wall seconds and 2.227828 more CPU seconds. Against this fixed B2 profile the final length proxy is 18.0292% lower, at materially greater computation.

Internal profile syntax is repaired. Standard assigned job/optimizer60/30 seconds, standalone tuned77/77, and each C incumbent62/62 after its charged reserve. Actual engine wall times4.94–12.52 seconds stop below all these deadlines. No claim of tested deadline enforcement follows from these early completions. B2 remains one fixed tuned configuration, not an exhaustive equal-budget portfolio.

One metadata issue was found: `route.started_utc` is recorded after startup hashing/storage/code copying, but `wall_seconds` starts before them. Adding those unlike anchors produces an apparent0.118-second B2/C_single overlap. The frozen protocol loop is synchronous; this is not evidence of concurrent routing. Exact no-overlap cannot be proved from those UTC fields alone. `initial-audit.json` preserves the first too-strict timestamp assertion, and the final audit explicitly records the mismatch rather than hiding it. Future invocation begin/end monotonic and UTC anchors would improve evidence. Unrelated host/background contention remains uncontrolled and load averages were recorded.

This is consistency checking of retained evidence, not fresh native revalidation or authentication against an entirely forged history. It is one exposed development family and one order/trial per arm; there is no generalized completion-rate or independent-family superiority claim. The inherited library warning and original ignored DRC keys remain. Physical/electrical adequacy and schematic parity are unverified.
