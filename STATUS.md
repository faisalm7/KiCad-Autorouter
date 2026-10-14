# Current status

Updated October 14, 2026 UTC in `/Users/faisal/Projects/KiCad-Autorouter-local`, on the existing Mac and `rebuild/local-20261010-015447` branch. Last verified GitHub checkpoint is `b7a9a1ceb119d302e1d4d21132e0b86724d40687`. This is an experimental local tool; broad evaluation and final release gates remain open. [Exact preceding status](docs/history/2026-10-14-c7ffada/STATUS.md) preserves earlier results, failures and changes in interpretation.

## What works

Routing runs without internet or an AI account using pinned KiCad 10.0.0, Freerouting 2.5.0 and Java 25.0.2. The CLI preserves complete source projects and original constraints, validates separate candidates, and reports unsupported cases. Persistent scope, layers, budgets and preferences, protected copper, cancellation, stale checks, before/after copper plots, acceptance/rejection intent and fresh native separate-project export are implemented. Use the [demo](docs/quickstart.md), [saved preferences](docs/routing-preferences.md) and [KiCad workflow](docs/gui-workflow.md). Intent is not human PCB approval. Live editor overwrite, undo and inspection of unsaved buffers are not qualified.

Guarded native class-parent dimensions now support ordinary two-layer whole and partial routing. Current owned positive/invalid/protected controls and production CLI routes retain original rules and class targets. Selected composite classes remain blocked. [Scope](docs/native-parent-classes.md), [actual production qualification](evidence/parent-class-production-native-001/SCOPE.md).

ArcDice's retained pruning candidate completed the real handoff: four native F/B copper plots, accept intent, fresh native separate-project export, export proof check and reject intent. Export has zero opens/blocking findings and the same 26 library warnings, 581.295202 mm/zero vias. Source/routing evidence stays exact. Failed environment/render and stdout-limit attempts remain, and completed plots were reused. Readback-only metadata mistakes also remain disclosed. [Workflow](evidence/arcdice-review-workflow-001/SCOPE.md). This is additional workflow qualification, not a routing-quality trial or GUI/human/physical approval.

## Measured development results

All four circuits below have complete schematic, actual native refill/final reports, original-design checks and unchanged warning signatures. C obtains its own incumbent; reference/B1/B2 routes are not given to it. Length is a geometry proxy.

| Circuit | Corrected adapter B1 | Strong tuned/restart B2 | Pruning C | Final opens / blocking / warnings |
|---|---:|---:|---:|---|
| NUS tutorial | 71.884325 mm / 2 vias | 71.769712 / 2 | 35.128656 / 2 | 0 / 0 / 10 |
| Sonde | 752.095975 / 0 | 746.345274 / 0 | 669.121554 / 0 | 0 / 0 / 26 |
| Small LED support circuit | 88.179474 / 0 | 88.179474 / 0 | 63.692565 / 0 | 0 / 0 / 7 |
| ArcDice | 636.989098 / 0 | 602.587602 / 0 | 581.295202 / 0 | 0 / 0 / 26 |

ArcDice's new gain is 21.292400 mm versus the strongest valid tuned output. Default and low completed stages were preserved; only unattempted low/high ran. Low rejects one starved thermal and has four vias. The first 100-second planning continuation again skipped high because of conservative reserves. High then received a prospectively frozen, unchanged profile with an explicit 48.602239-second inner planning allowance and a stronger 23.279574-second inherited outer deadline. Full costs, rather than that planning allowance, determine acceptance. B2 charges 112.047170 wall / 101.680803 full CPU seconds; C charges 108.389989 / 95.904073, below the same 120-second caps. All prior setup, shared, outer and failed work remains charged, with a new 15-second final audit allowance and two one-second bootstrap/publication allowances. [Actual continuation](evidence/arcdice-b2-continuation-001/SCOPE.md). Independent readback verifies all nine native/engine stages per new profile, final bindings and exact original warning details. Cumulative failed/successful audits, parser failure and bootstrap/emission allowances total 12.436338 wall / 12.076963 CPU seconds, within the charged 15. [Review and closure](evidence/arcdice-continuation-review-001/REPORT.txt).

The earlier ArcDice002 budget failure remains rejected: after review charges B2 is 124.144001 wall / 121.919503 CPU and C is 166.046639 / 150.090386. Its valid geometry is not a comparative win. [Failure and costs](evidence/arcdice-native-paired-complete-sch-002-review-costs/SCOPE.md). Stock B0 rejects on all four circuits; ArcDice has two real thermal errors. Other rejected trials, warning regressions, ties and budget losses remain visible. Historical multichannel board-only gains fail later complete-schematic acceptance with 115 additional warnings.

NUS/Sonde/LED accepted C full costs are 58.214645/57.272633, 113.536396/108.065042 and 75.998432/70.096449 wall/CPU seconds. Strong B2 costs are 88.112877/90.472093, 72.770682/83.688574 and 92.010792/83.812493. [NUS](evidence/nus-b2-continuation-001/SCOPE.md), [Sonde](evidence/sonde-native-paired-complete-sch-001/SCOPE.md), [LED](evidence/push-button-led-native-paired-complete-sch-001/SCOPE.md). These are cumulative active costs, not uninterrupted elapsed time or a speedup claim.

Different circuits/publishers do not prove independent ancestry. Zero independent pedigrees are established; every circuit is exposed development data. Broad completion-rate superiority, untouched confirmation, human cleanup time and electrical/manufacturing quality remain unproven.

## Coverage and correctness

The current complete managed population is 394 files / 41,512,070 bytes: 25 canonical boards, 26 physical copies including one exact duplicate, eight statically eligible and 17 unsupported. ArcDice is tracked separately as a new source lead. Static eligibility is not native success. [Current census](evidence/corpus-population-011-parent-current-001/SCOPE.md). Custom pads/contacts, net ties, advanced constraints, genuine footprint restrictions, active profiles, machining and unknown semantics stay blocked. Clock's real schematic/footprint mismatches remain rejected; Roller remains a diagnostic with strict DSN rounding failure, not production admission. Asset/model origins and all warnings remain visible; no raw third-party artwork/assets are redistributed.

Full integration026 at `6da5c4b7` passed 958 software tests with source/tool hashes unchanged. Later completed-prefix and publication controls pass targeted checks. Skeptical review found a final report-write failure path; the shared readback now invalidates positive publication and restores handlers on write failure/cancellation, including failed corrective writes. Actual Native stages were not repeated to repair reports. The next full suite runs at the source portability/integration milestone. [Full checks](evidence/full-integration-026/SCOPE.md).

## Installation and GUI

Installation017 at `2d456f9` qualified a fresh local clone/venv, offline commands/full then-current suite and native placement route/check, using existing Mac apps and verified engine cache. It also fetched the five pinned public LED files without research-cache access and passed the complete offline workflow, preserving seven library warnings. [Qualification](evidence/installation-017/SCOPE.md). This predates current class-parent/storage changes. A current fresh installation remains required; ArcDice still depends on a retained source cache until its prepared fixed-source fetch is integrated.

Actual installed LED GUI003 opened the separate export through KiCad Manager/PCB Editor, refilled zones and checked full schematic parity with all severity filters: zero findings and five unchanged ignored checks. The isolated CLI's seven library warnings remain authoritative; exact GUI library context is unobserved. Closing with Discard Changes preserved PCB/SCH/export but added one schematic setting to the disposable project. [GUI](evidence/installed-led-export-gui-003/SCOPE.md), [closure](evidence/installed-led-export-gui-003-closure/SCOPE.md). Earlier access failures remain. No unlock gate remains for that completed test, and no human/physical/undo qualification is claimed.

## Backups and next work

GitHub source/checkpoints are verified independently by branch SHA and file readback. Private incremental backup at `0fd644dc` verifies 250,275 files / 6,751,684,004 bytes, 875 delta files / 9,787,297 bytes and chain integrity. It is not a new full restore. [Incremental](evidence/backups/incremental-0fd644d.json). Full restoration at `9f1f59e` verifies 249,401 files / 6,741,896,761 bytes, all Git refs and restored CLI. [Full restoration](evidence/backups/restore-9f1f59e.json). New comparison/workflow artifacts are outside those cutoffs. Next private incremental and full restoration are due at this major comparison milestone. Archives are on this Mac only, without disk-failure protection elsewhere.

Continue with the [active plan](PLANS.md): close independent comparison review, verify the safe checkpoint, run existing incremental/full restore helpers with writers idle, integrate the prepared bounded ArcDice fetch, and qualify current installation and reproducibility. Do not repeat completed native comparisons/GUI/original observations. The existing `.runs/portable-arcdice-fetch-implementation-draft-001/proposal.patch` is a draft, not verified implementation. Full tracked source now exceeds the old installation inventory cap and another full evidence clone would exceed the backup file ceiling; use a clearly documented fresh distribution checkout without duplicating historical evidence, preserving the complete original suite/evidence.

Representative 30–50-family audit, independently pedigreed untouched confirmation, current final installation/RC, human PCB review and off-Mac private protection remain gates. No spending, formal release/tag/package publication, external contact, cloud access or automatic resume loop is authorized.
