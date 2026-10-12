# Protected routing and layer-mask evidence audit

All 85 narrow checks pass. This audit reuses the central receipt checker, native report parser, early protected-route guard and exact layer-observation validator. It launched no KiCad, JVM, router, GUI, network call or software suite. All original source and six retained run inventories remain unchanged.

| Actual retained run | Outcome | Stored wall / full CPU seconds | Scope |
|---|---|---:|---|
| partial002, 9ef0a64 | Accepted/current; 0 opens/errors/warnings/exclusions; 90 mm, 0 vias | 10.226936 / 5.896305 | v1; exact two original segments |
| locked002, 0aecd92 | Accepted/current; 0 opens/errors/warnings/exclusions; 90 mm, 0 vias | 9.702379 / 5.741185 | v2; exact two original locked nodes, including UUID and field placement |
| removal001, 9ef0a64 | Expected rejection: 1 open, 1 dangling-track warning, 0 other blocking violations/exclusions | 1.657020 / 0.734777 | Exact one-segment removal; original rules; protected guard rejects |
| layer-mask001, 9ef0a64 | Four actual imports/readbacks pass their expected predicates | 1.197039 / 1.774774 | No routing/native DRC; production layer support remains false |
| historical partial001 | Rejected: exact protected-node guard after UUID regeneration | 8.102920 / 4.712405 | Failure preserved |
| historical locked001 | Rejected: v1 exact match after native lock-field relocation | 6.424330 / 4.361278 | Failure preserved |

The two accepted receipts remain within their 120-second wall/CPU ceilings; the negative and layer diagnostics remain within their 60-second ceilings. Stored sample points and outer execution costs are retained separately in audit.json. Outer wall/whole waited-child CPU: partial002 10.663435/6.159402 s; locked002 9.986613/5.984558 s; removal001 1.715706/0.780968 s; layer001 1.324918/1.859303 s.

For both accepted boards, original/snapshot project hashes, exact protected nodes, immutable geometry, native final report bindings, unchanged ignored-check lists, metrics, code/tool receipt pins and budget accounting pass existing central validation. The removal board is exactly the accepted partial candidate minus its original 5 mm SIGNAL_A segment. Its complete native input/project, report and actual DRC process are bound; the early production guard independently returns `protected route changed` before accessing a worker. An open is a rejection even though the separate `blocking` counter is zero.

The existing layer validator reproduces all four saved comparisons: source-all, front-only and back-only map correctly through all three initialization boundaries; the reversed-mapping control transports B.Cu while requesting F.Cu and is rejected semantically. All 33 captured files, source snapshots, pinned basis records, raw observation hash, request, process and runtime record match. This is importer/settings evidence, not native layer-routing qualification or a comparative completion gain.

These results qualify the tested owned preservation fixtures. They do not establish generalized routing quality, human PCB approval or electrical/physical correctness. Earlier failed runs are not relabeled.

Reproduce: `python3 -B .runs/review-protected-native-001/audit.py`.
