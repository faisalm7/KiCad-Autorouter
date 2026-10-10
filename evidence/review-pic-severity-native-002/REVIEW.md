# Fresh severity002 audit

All six declared diagnostic predicates completed successfully at `2a987f2275c071c3788e46dfa17dcfb9bd4c80fb`. Independent offline review passed 231 checks over all314 raw files, the original15-file project, committed code snapshots, tool pins, wrapper/log, twelve exact sandboxed native processes, complete project copies, observations, DRC inputs/reports and final summary. Both original source and full001/002 evidence trees remained unchanged during review.

| Case | Opens | Native errors | Warnings | Meaning |
|---|---:|---:|---:|---|
| Positive | 0 | 0 | 4 | Matched baseline for these controls |
| Missing named profile | 0 | 0 | 5 | Exact POWER/profile warning detected |
| Missing Default profile | 0 | 0 | 4 | Profile loaded in both nets; missing-profile finding omitted |
| Board Edge.Cuts text | 0 | 1 | 4 | Exact board-text error detected |
| Footprint Edge.Cuts text | 0 | 1 | 4 | Exact footprint-text error detected |
| Front counterbore | 0 | 1 | 4 | Exact SIGNAL_A track/P3 pad error detected |

Every case has zero exclusions and an empty unrequested parity list. The four ordinary warnings are **`missing_courtyard`**, not library warnings. The named-profile case adds one `missing_tuning_profile` warning. `warning-correction.json` corrects the wording in the frozen001 review; its counts, byte checks and failed disposition do not change.

Actual002 text observations include integer layer IDs17/25/35 alongside exact native names. All six board and project byte sequences match failed001. The case-specific composite `POWER,Default` and inherited profile are observed while original POWER dimensions remain exact. The Default omission is a completed coverage probe only: `default_profile_enforcement_qualified` remains false. All three deliberately invalid cases still have their original error severities. Passing their diagnostic predicates does not convert them into acceptable routed boards.

Native stage CPU sums to6.330716 seconds. Stored whole-job accounting is15.808914416 seconds wall /14.038842 full self-plus-waited-child CPU; the outer wrapper reports16.347974667 wall /14.535938 waited-child CPU, exit0 and no cleanup signals. These are below both90-second ceilings; stored sampling precedes final checks as declared. Every observer exited0 and each DRC exited5 with retained findings. DRC refilled in memory without board save; each second input copy added only the permitted project-local `.kicad_prl`. All rules, profile deltas, stackup and original ignored3/native ignored4 distinctions remained intact. No engine ran.

The selected public subset independently matches all76 declared raw files byte for byte, totaling573,291 bytes. Its48 omitted isolated generated default files remain in local raw evidence. Public scope/license notices are authored metadata, not claimed raw copies.

This audit ran no native, engine, Java, compiler, GUI or network task. The result qualifies only these fixed diagnostic observations and error predicates. Default enforcement, schematic parity, arbitrary machining, custom routing/format admission, electrical adequacy and human PCB review remain unqualified; production support flags remain false. Historical001 remains failed.
