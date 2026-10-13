# Actual multichannel paired review

The equal-budget pilot establishes an adapter gain over B0 and **no measured C gain**. B1 and the tested B2 candidate are accepted with 19 vias, 2,640.198553mm routing and all 96 warnings. C's inner candidate is native accepted and has tied metrics, but final delivery exceeds the 120 CPU-second budget and remains rejected.

| Arm | Delivered acceptance | Opens / blocking / warnings / exclusions | Charged wall / CPU seconds |
|---|---|---|---|
| B0 stock | Rejected | 160 / 49 / 125 / 0 | 75.122058 / 81.479304 |
| B1 corrected placement adapter | Accepted | 0 / 0 / 96 / 0 | 59.272764 / 74.427923 |
| B2 tuned portfolio | Accepted | 0 / 0 / 96 / 0 | 94.512034 / 110.510125 |
| C placement pruning | Rejected by delivery CPU budget | 0 / 0 / 96 / 0 | 105.521213 / 121.504365 |

The C candidate is identical in SHA256 to its fresh incumbent. It executed zero deletion trials and recorded zero improvements. Candidate-only inspection finds 163 eligible zone-net routes, two whole-net proposals and 163 individual proposals. The recorded incumbent already consumed 97.407190 CPU seconds. With the 114.634665-second inner allowance and 15-second final reserve, only 2.227475 CPU seconds remained before further checks—below the four-second minimum trial allowance. The pilot did not actually test whether deletion improves this board. It cannot support a positive or negative geometric pruning claim; it does demonstrate a delivery-cost regression under this allocation.

B2 truthfully ran its default-cost variant only and stopped when another attempt plus reserves could not fit. Low/high variants were predeclared but unexecuted; they were not converted into successes or omitted failures. Its selected trial allowance is 97.046971 seconds inside the shared 114.634665-second portfolio allowance. The first review assertion confused these two allowances; audit-001 retains that reviewer failure. Corrected audit-002 passes without changing benchmark evidence.

The paired summary's timings precede final publication. The enclosing actual wrapper records 331.774954 seconds wall and 390.484358 full CPU seconds, including all four sequential arms and supervision. Conservatively charging **all** outer shared overhead to every arm still preserves the same outcome: B1 costs 79.642963 CPU seconds, B2 115.725165 and C 126.719405. No outer compute was silently omitted to rescue C. C's `status` string carries its inner native status; its top-level delivered `accepted=false`, enclosing/charged budget flags and invalidated delivery observations govern the comparison.

The raw original-source DRC remains zero opens, 24 blocking findings, 93 warnings and no exclusions. The accepted outputs retain 81 library footprint mismatch, nine connection-width, four silk-over-copper, one silk-edge and one nonmirrored-text warnings. All seven effective ignored checks remain reported: five inherited project choices and two native defaults. None of these outputs is a clean whole project or an electrical/physical qualification. B0's short invalid length is not a usable-quality comparator.

The review binds every original project file, source snapshot, candidate, rule copy, final raw report, metrics, process/log and all stored compute. Exact frozen d429f39 checker copies were used because current pipeline, placement-clearance and paired wrapper code already changed during subsequent work. Their hashes match the run's frozen code; only config ROOT/JAR locations were rebound to this existing checkout. `subprocess.run` and `Popen` were prohibited, so no native, JVM, Git or network operation ran. The full 873-file /136,517,925-byte run and all 17 source files remain unchanged.

| Final candidate | Candidate SHA256 | Actual final report SHA256 |
|---|---|---|
| B0 | `3b834f25a022b1bc887910b8375d712ccdd06dec3821d9965c4b03b4b3d8118b` | `2c123faa05309c2a30a5d5a37d867701b338021158facb09acf35d357e4ec48f` |
| B1 | `72b5ba5d87782b18b2164a7dd99d1cc72a74f49bc03ae73ba2c6aea05cd90b2b` | `e9dd849f946a821048adfe7eb47a8f249dc1ffbdd781f03699471e4bf4c7a353` |
| B2 selected | `b12d46097b4f0240d1f745dbe79f985c84839a213d78141f75ab48139ffad1bf` | `f28dc11ffc32144dbcdcb45788fe0bcb983903cbc46487f057489bdfb29fd290` |
| C inner candidate, rejected delivery | `35d52e97621d0601481f5cf1378492c7aeabc420264c38088af784f6b7214677` | `9ef74a0f81be6f5eefd4ed53959466a25946026c3a6dbc398b10c2dd8b372ec0` |

`findings.json` stores machine checks and exact accounting; `run-inventory.json` binds all raw files. `EVIDENCE_SELECTION.json` suggests essential native/process/protocol evidence, with no omitted findings. It is a partial public selection, not a replacement for complete local raw runs or a portable accepted receipt tree. This is one exposed multichannel input, with no independent-family, population-superiority, novelty or human-review claim. The scoped review found no basis to admit C under the equal budgets.
