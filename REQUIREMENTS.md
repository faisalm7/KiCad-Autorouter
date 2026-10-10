# Requirements to evidence

| Requirement | Implementation / executable check | Evidence | Status |
|---|---|---|---|
| G0 local checkout and safe remote backup | Git + OS inspection; independent SHA and README read | evidence/backups/G0.json | Passed |
| Pinned Mac CLI and native interfaces | `python3 -m autorouter doctor` | toolchain.lock.json; evidence/doctor-initial.json | Actual10.0.0 interfaces exercised; packaging incomplete |
| G1 real routing + native refill/connectivity | `python3 -m autorouter route … --output NEW` | evidence/runs/smoke-stock-004; sonde-stock-002 | Diagnostic accepted; public development stock failed |
| Immutable original/native geometry/project/rules | pipeline.py structural and complete-file checks; test_validation.py | Native input bindings + source/candidate hashes | Exercised narrow scope; more constraints blocked |
| Fail closed missing/corrupt/disabled checks | parse_report; test_validation.py | docs/review-initial.md | Reproduced flaws fixed; parser tests passed |
| Native positive and deliberately invalid controls | `scripts/native_controls.py --valid … --output NEW` | .runs/native-controls-002/summary.json | 14 real native control cases passed; not population evidence |
| Cancellation, timeout, descendants, bounded logs | runner.py; test_runner.py | Actual disposable child processes | Passed; detached children/SIGKILL cleanup unqualified |
| Memory/disk guard and complete compute accounting | runner.py polling work in progress; pipeline.py counters | Run process receipts | Partial; polling is not OS enforcement |
| Licensed native source and preserved originals | `python3 data/fetch.py --verify` | data/sources.json; docs/data-provenance.md | 1 public family acquired; no training/holdout |
| Historical mechanism reconstruction | adapter.py; separate graphics/planes/both modes | Tests only so far | Native experiments pending |
| G3 representative failure audit + alternatives | Research + KRT spike preparation | docs/research-foundation.md | 30–50 family audit unmet |
| G4 B0/B1/B2/C fair improvement + ablations | No C strategy implemented | None | Unmet; no superiority claim |
| G5 CLI, supported scope and separate output | autorouter/__main__.py; README | Real CLI route commands | CLI exercised; GUI/undo/stale editor/selected nets unqualified |
| G6 learning decision | Failure audit still too small | docs/architecture.md | No model; training not presently justified |
| G7 frozen holdout + independent scrutiny | Initial adversarial AI review only | docs/review-initial.md | Confirmatory evaluation unmet |
| G8 backup/restore + fresh installation | scripts/backup.py; test_backup.py | Scratch backup tests | Actual checkpoint restoration pending |
| Release packaging/CI/support matrix | README + architecture initial scope only | None | Unmet; no published package/release |
| Human and physical/electrical validation | Later owner-approved execution required | None | Unmet |

Counts describe executed controls, not correctness breadth. Source preservation does not establish schematic parity or physical performance. Every unavailable capability remains excluded from acceptance claims.
