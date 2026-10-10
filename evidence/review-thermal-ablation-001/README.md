# Independent thermal ablation evidence review

Read-only audit of `.runs/thermal-ablation-001` at frozen commit `cc71a5103f32b97274fb82a9494501b0b823d541`, cross-bound to `.runs/thermal-paired-001` at `cbae1254f00d3470d98ba18d24a09e99874f0cc2`.

**Result: 4,769 checks passed, no failures.** The reviewer launched no native or routing jobs and changed no source, draft, run, or public evidence files. Reproduce from the project root with `python3 .runs/review-thermal-ablation-001/audit.py`; this rewrites only this review's audit JSON.

| Policy | Native opens | Native blocking | Warnings / exclusions | Charged wall seconds | Charged CPU seconds | Accepted |
|---|---:|---:|---|---:|---:|---|
| B0 standard | 14 | 3 | 0 / 0 | 42.733323 | 64.191857 | No |
| B1 standard | 0 | 1 thermal | 0 / 0 | 59.577230 | 80.119067 | No |
| B1 completion-only | 0 | 1 thermal | 0 / 0 | 28.831796 | 42.258588 | No |

Each arm includes the entire shared preparation, evidence verification, freeze, and publication overhead in its own 120-second wall and measured CPU ceilings. The native engine contracts, actual settings/argv/processes, raw and adapted DSN, source/project copies, final input/report/candidate hashes, route metrics, class dimensions, immutable geometry, protected routing, and seven original ignored checks were verified. The frozen source files were also matched to their Git blobs and pinned tools. Complete prior-pair and new-arm inventories remained bound. The public subset has 107 byte-identical raw files (3,253,680 bytes), plus its generated scope and manifest.

The B1 standard engine retained a validly produced SES after its optimizer's 30-second internal timeout; the eventual original-rule native rejection is preserved. B0 and B1 completion-only had no engine timeout log. None of the failed candidates supplies accepted-route quality evidence.

The prior C outcome remains accepted and cross-bound by identical production code, source, tools, and pre-existing protocol bytes. These are separately timed sequential runs, not a fresh joint randomized comparison. B1 completion-only reproduces C's pre-repair route geometry up to generated UUIDs and the same thermal native outcome. Together with the separately preserved exact bridge-removal negative control, that supports the local repair mechanism on this exposed board. It does not establish generalized superiority, physical/electrical qualification, or human PCB review.

Stored totals are sampled before the final summary write/freshness work; the frozen harness checks the full charged acceptance caps after that work. This sample-point limitation is explicit in the original evidence. All original severity/ignored-check settings remain unchanged; a zero-finding result is interpreted under those original settings.

No blockers or unexplained evidence inconsistencies were found. Detailed hashes, exact native outcomes, engine timeout lines, accounting, and claim boundaries are in `audit.json`.
