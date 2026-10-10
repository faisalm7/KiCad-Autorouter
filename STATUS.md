# Current status

Updated October 10, 2026 (America/Los_Angeles). This is an active local experimental reconstruction. The adapter recovery below is measured; a substantive improvement beyond the adapter remains unproved.

## Locality and recoverability

G0 passed on macOS 27.0.1 arm64, with 16 GiB RAM, in `/Users/faisal/Projects/KiCad-Autorouter-local`, branch `rebuild/local-20261010-015447`. The initial push `683e41aab756cfb5c6a0c7c0f0ed37b8e18dc704` was independently verified by remote SHA and README byte read-back. The subsequent checkpoint `7fef4675006bc35e59c1dc566b9cff07f2dbd5d9` was pushed and independently verified by remote SHA and `autorouter/pipeline.py` byte read-back. Receipts: `evidence/backups/G0.json` and `evidence/backups/checkpoint-7fef467.json`.

An actual Git bundle and non-Git archive for checkpoint `7fef467` were restored into a separate local directory. All Git refs and 1,185 archived files were verified, and the restored CLI help exited successfully. The receipt names the archive and hashes. This is on-Mac recovery evidence, without protection against loss of this disk. A private off-Mac archive destination awaits the owner. Later corpus, adapter, KRT and review artifacts still need inclusion in the next verified archive; the earlier receipt does not cover work created afterward. Existing Git identity was retained. No cloud environment, global protection, or global preference was changed.

## Working pipeline and validation

The CLI runs installed KiCad 10.0.0, its bundled Python, Freerouting 2.5.0, and Java 25.0.2. It copies complete projects, hashes sources and rules, exports/imports routes, refills native zones, runs native DRC/connectivity, and binds acceptance to the candidate and report hashes. Originals remain unchanged. Project-local config/cache/documents directories avoid personal preferences; the exact cause of the earlier isolated-config crash remains unresolved.

G1 has a licensed, native-validated routing success and a real native control suite: all 14 cases in `evidence/native-controls-002/summary.json` passed their expected outcomes. One positive was accepted; 13 deliberate disconnection, short, geometry, protected-route, zone and rule/severity changes were rejected. Each case executed native KiCad. Some tampering is detected by preservation checks even when native DRC alone is clean. These controls establish a narrow exercised scope, not broad correctness or physical validity.

Independent follow-up review reproduced and verified fixes for candidate-directory symlink escape, engine setup symlink escape, and competing-file overwrite. Twelve receipt checks passed against actual filesystem edits. Synthetic receipts in those tests are not native routing evidence. The review also checked the frozen experiment's source/code/candidate/report bindings and CPU accounting. See `docs/review-initial.md` and `docs/review-followup.md`. CLI stale-file checks exist; applying a candidate to a live editor is not implemented or qualified.

The actual KiCad 10.0.0 PCB Editor also opened a disposable complete copy of the accepted B1 candidate and ran native DRC with zone refill: 0 errors, 0 unconnected, 25 library-disabled warnings and 0 exclusions. Four original ignored checks remained visible. This differs from the isolated CLI's one-warning library configuration and is not an identical validation configuration. Closing with Discard preserved board bytes but rewrote the disposable `.kicad_pro` defaults/version and created `.kicad_prl` / `.history`. Originals and accepted evidence were preserved. This narrowly qualifies external review of a separate copy, not plugin execution, automatic application, undo, unsaved-edit detection or GUI cancellation. Evidence: `evidence/gui-inspection/gui-native-drc.rpt`, `observation.json`, and `docs/gui-workflow.md`. The CLI `review-copy` completed its end-to-end check on accepted C pilot 001; `evidence/gui-inspection/review-copy-C-001.json` binds the copied project. This does not apply changes to a live editor.

## Frozen development adapter experiment

`.runs/adapter-ablation-001/protocol.json` froze the implementation at `7fef467`, one exposed sonde family, 120 seconds per arm, one worker, and the following fixed order. All constraints and native source zones were retained. CPU includes parent, workers and monitor; times include conversion and validation.

| Arm | Native opens | Blocking findings | Warnings | Track length mm | Vias | Wall seconds | CPU seconds | Routing accepted |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Stock A (B0) | 3 | 7 | 1 | 566.454 | 4 | 11.178 | 11.469 | No |
| Graphics correction | 3 | 0 | 1 | 586.069 | 3 | 10.089 | 11.196 | No |
| Plane correction | 0 | 3 | 1 | 785.816 | 3 | 13.297 | 17.626 | No |
| Combined adapter (B1) | 0 | 0 | 1 | 786.316 | 3 | 13.358 | 17.523 | Yes |
| Stock B (B0 repeat) | 3 | 7 | 1 | 566.454 | 4 | 10.290 | 11.254 | No |

Exact metrics and receipt paths are in `.runs/adapter-ablation-001/summary.json`. Graphics keepouts remove the observed collisions; suppressing exported plane declarations makes the router connect all terminals, with a wire-length cost. Native zones remain intact. This is a transparent B1 adapter correction, not a new routing strategy. The accepted candidate retains one library-footprint warning, so routing-scope acceptance is distinct from whole-project cleanliness. Invalid stock outputs are not a valid route-quality comparator. Fixed order and one family support no speedup, generalization, B2, or C claim.

Earlier `smoke-stock-004` and `sonde-stock-002` records remain provisional development evidence: they lack per-run code snapshots and differ from the frozen implementation. Their native findings are retained, but are not presented as frozen-code reproducibility results.

## Alternative engine and full considered population

Two bounded KiCadRoutingTools 0.23.0 native-input spikes completed. Both raw outputs changed eight copper texts and failed immutable preservation and native DRC. Separately recorded route-only transfers restored source geometry but had 8 and 12 blocking copper collisions. All four outputs were rejected. A formatting-dependent zone-parser omission was isolated and corrected in the second input; acceptance still failed. See `docs/krt-spike.md` and `.runs/krt-spike-001` / `.runs/krt-spike-002`. These rejected candidates establish no quality or speed advantage.

Six licensed source projects containing seven native boards are now acquired at one pinned revision: 132 original files plus notices, 144 files and 13,654,726 bytes total. All are exposed development data. Historical `evidence/coverage.json` retains the prior six-board audit; the new reproducible `scripts/audit_corpus.py` records the complete promoted population. Current static preflight has **2 eligible boards, 5 unsupported boards, 0 parsing errors**. Static eligibility executes no native subprocesses and is not routing acceptance.

| Considered board | Current static eligibility |
|---|---|
| sonde xilinx | Eligible for native audit; separate development routing evidence is above |
| pic_programmer | Unsupported custom pads and four unqualified rule-severity keys |
| complex_hierarchy | Unsupported netclass bindings and `zone_has_empty_net` severity semantics |
| interf_u | Statically eligible through literal two-class checks; production native routing qualification pending |
| ColdFire/Xilinx | Unsupported four-layer netclass scope, non-identifier pattern and nonblocking original thermal check |
| multichannel_mixer | Required `padstack` check is not blocking in the original project |
| multichannel_mixer-unrouted | Missing same-basename project binding and unqualified board format |

The multichannel siblings share terminal connectivity but differ in 19 footprint poses; they stay in one family. Six directory-based family identifiers do not establish ancestry independence. The requested 30–50-family audit, a family-disjoint holdout, and a generalized comparison remain unmet. No original rule, severity, geometry or project binding was changed to admit excluded boards.

## Remaining work and continuation

G2 has the narrow validator controls, receipt bindings and historical adapter reconstruction above; broader validation qualification remains open. G3 has an initial corpus and alternative-engine spike, not the required representative audit. Corrected four-arm pilot 002 completed at frozen `57db787` under equal 120-second wall and measured-CPU caps. B1 accepted 786.316 mm / 3 vias, B2 accepted 786.316 mm / 2 vias, and C accepted 660.099 mm / 3 vias. Each retained one warning. C improves length beyond B1 but trades shorter length for an extra via against B2; no overall superiority or speedup is established. Pilot 001 had a B2 threshold error and remains explicitly labelled. See `docs/quality-experiment.md`. G4 superiority, complete G5 application/installation qualification, G7 untouched evaluation, and G8 release preparation remain unmet. No model has been trained; the current small failure audit does not justify training. Selected-net routing, schematic parity, human PCB review, and physical/electrical validation remain unestablished. No formal release or package has been published.

Resume from this checkout, first inspecting any active run before launching another heavy worker:

```sh
python3 -m autorouter doctor
python3 data/fetch.py --verify
python3 -m unittest discover -s tests -v
```

Legacy runs without an explicit measured-CPU ceiling are retained as historical evidence but the strengthened `check-result` refuses to qualify them for the new review workflow. New runs must carry the explicit cap.

Next: execute the prepared installation and native cancellation tests, then test C with a tuned incumbent and qualify literal netclass support for a second family. Audit and push checkpoints, and run `python3 scripts/backup.py` to create and restore-test a new archive. `PLANS.md` records the remaining gates. Reproduction scripts require new output directories; preserve all failed runs. No background or auto-resume work is scheduled.

Actual engine-stage cancellation control 001 passed: SIGINT to the owned routing CLI rejected the candidate, the engine recorded cancellation and complete cleanup, and its process group was absent. Source/code remained unchanged. See `evidence/native-cancellation-001/control.json`. Interstage/GUI cancellation and OS crashes remain unqualified.

The current pending revision adds literal two-class native export/target checks and switches C to a tuned incumbent. These code changes still await native multiclass qualification and a new frozen comparison. The failed fresh-install attempt 001 is retained; 19 subprocess tests failed because the sandbox denied the setuid process monitor. The replacement unprivileged monitor passed 22 focused controls under both ordinary execution and the same sandboxed fresh venv; full retest remains pending.

A separately bounded acquisition audit retained the complete ColdFire/Xilinx project (50 originals plus two license notices, 4,384,337 bytes) under the pinned official demo license. It has now been promoted into the seven-board acquisition manifest; it has not been routed. Its four copper layers and non-identifier assignment pattern remain outside the new literal two-layer class scope. Acquisition/ancestry receipts remain in `.runs/coldfire-audit-001`; no family independence is established.

Fresh installation attempt 002 at `dd2cce9` passed all 160 tests, native smoke routing and receipt validation in a new local clone/venv with network denied. It reused installed Mac tools and the verified JAR cache; it does not qualify a fresh Mac or package installation. Full workflow took 14.935349 seconds. `evidence/installation-002` preserves command logs and scope.
