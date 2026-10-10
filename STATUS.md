# Current status

Updated October 10, 2026 (America/Los_Angeles). **Active local reconstruction; incomplete.** Native experiments show shorter routes beyond a stronger adapter baseline on sonde, and automatic thermal-repair completion beyond tested baselines on interf_u. A later margin-based adapter diagnostic completes multichannel while its zero-margin reference fails; its explicit production command now also passes fresh native replay. Different frozen code/strategies on these exposed inputs do not establish a pooled completion rate, independent-family result, generalized superiority or electrical qualification.

## Durable local work and backup boundary

Checkout: `/Users/faisal/Projects/KiCad-Autorouter-local` on this Mac; branch `rebuild/local-20261010-015447`. Latest verified push/read-back is **`1ed5ea0037466d3c5b3028cf9519a128174550f9`** (local receipt `.runs/checkpoint-1ed5ea0.json`; prior published receipt [ee431c0](evidence/backups/checkpoint-ee431c0.json)). G0 began at `683e41a`; no cloud/worktree was used.

Latest **full** archive: **ee431c0**. Restore verified all Git refs, **45,973 non-Git files / 1,454,884,745 bytes**, and CLI help ([verification](evidence/backups/restore-ee431c0.json)). Location: `.local-backups/checkpoint-20261010T140100Z-fece3bf3f7e04192920f6b7a079f753c`. This covers all previously archived production/data evidence, complete installation003 clone/venv/raw records, final installer fixes/reviews, both LiPo native attempts, their source research and independent reviews, and the frozen placement handoff plan. New handoff implementation/control drafts started after this snapshot and are outside it. GitHub holds audited source and selected evidence. Full archives remain on this Mac only; an independent off-Mac destination awaits the owner. No original or prior archive was removed.

## Implemented validation and measured results

Pinned tools: KiCad **10.0.0**, matching Python, Freerouting **2.5.0**, Java **25.0.2**. Separate complete project copies preserve geometry/nets/pads/rules/severities/zones/protected copper; native refill/DRC/connectivity binds exact candidate bytes. Unsupported, stale, corrupt or excluded validation rejects, as do critical findings regardless of severity. Original ignored checks remain unchanged. Receipt readback checks consistency, not fresh native execution or authenticity. CPU ceilings are measured acceptance caps, not OS aggregate quotas; receipts identify their accounting sample point.

The stronger **sonde** [pair001](evidence/portfolio-paired-001/paired-summary.json), frozen at `2f36e2c`, charges setup, all attempts, validation and full shared overhead to each arm under **120-second wall and measured-CPU ceilings**:

| Arm | Native opens / blocking / warnings / exclusions | Length / vias | Charged wall / CPU seconds |
|---|---|---|---|
| B2 fixed cost portfolio, selected low-cost variant | 0 / 0 / 1 / 0 | 749.441643 mm / 2 | 55.895249 / 75.892260 |
| C warning-guided route pruning, own tuned incumbent | 0 / 0 / 1 / 0 | 648.045171 mm / 2 | 105.425579 / 85.349779 |

All three B2 variants produced valid candidates. C is **101.396471 mm shorter with equal vias**, using more compute. Prior five-arm [quality004](evidence/quality-comparison-004/summary.json) separately shows the compound-deletion ablation: 644.549 mm versus single-deletion 662.694 mm, both two vias. The frozen [adapter ablation](evidence/adapter-ablation-001/summary.json) retains B0's 3 opens/7 blocking findings and independent graphics/plane failure controls. These distinguish adapter correction from post-route improvement; invalid shorter outputs are never quality comparators. See [experiment details](docs/quality-experiment.md).

The fresh **interf_u** [thermal pair](evidence/thermal-paired-001/paired-summary.json), frozen at `cbae125`, includes C's own failed incumbent, geometry observation, proposals, repair and final delivered-board validation. Later [allocation ablations](evidence/thermal-ablation-001/summary.json) at `cc71a51` preserve identical production/source/tool bytes, with the changed HEAD/new harness recorded:

| Policy / experiment | Opens / blocking / warnings / exclusions | Charged wall / CPU seconds | Accepted |
|---|---|---|---|
| B2 tuned cost portfolio / pair001 | 0 / 1 thermal / 0 / 0 | 72.948518 / 91.882070 | No |
| C automatic thermal recovery / pair001 | 0 / 0 / 0 / 0 | 42.044862 / 54.759604 | Yes |
| B0 standard / ablation001 | 14 / 3 / 0 / 0 | 42.733323 / 64.191857 | No |
| B1 standard / ablation001 | 0 / 1 thermal / 0 / 0 | 59.577230 / 80.119067 | No |
| B1 completion-only / ablation001 | 0 / 1 thermal / 0 / 0 | 28.831796 / 42.258588 | No |

Every policy fits its 120-second wall/CPU ceilings. Only B2's first variant fit its budget/reserves; the other two were not run. C delivered 4,996.393150 mm / 35 vias with unchanged fill/constraints. B1 completion-only reproduces C's pre-repair geometry apart from generated UUIDs. [Exact bridge removal](evidence/thermal-production-negative-001/negative-summary.json) restores the failed incumbent hash and sole thermal error under fresh native checks. This supports local completion; invalid baselines supply no quality delta. Separate sequential ablations are not a randomized population study. See [thermal scope](docs/thermal-experiment.md).

## Common board-floor adapter: fixture pass, full board rejected

The original **multichannel** run rejected **160 opens / 95 blocking / 138 warnings / 0 exclusions**, 73.187888 wall / 81.858311 CPU seconds. Source: 24 clearance errors/93 warnings. Native export preferred 0.2 mm width/clearance and 0.6 mm vias despite original minima of 0.3/0.3/1.5 mm. A transform alone does not establish feasibility.

The diagnostic path is now qualified on an owned exposed fixture: [geometry002](evidence/board-floor-geometry-002/summary.json) passed the positive plus five targeted width/clearance/via/drill/annulus negatives (13.469755 wall / 9.037068 CPU seconds); [forced-via001](evidence/board-floor-forced-via-001/summary.json) passed real engine → SES → native import/refill/DRC (6.759127 / 4.816742), with one required 1.5 mm / 0.3 mm via and zero native findings. Independent audits verified raw/source/candidate/report/SES bindings and exact public copies. [Geometry001](evidence/board-floor-geometry-001/summary.json) remains invalidated by its tuple/JSON publication defect; corrected002 is a separate fresh run.

**Production code is promoted and independently reviewed.** At `e12cdc4`, the [actual CLI fixture](evidence/board-floor-production-native-001/result.json) passed native validation and receipt readback: zero findings, 67.926667 mm / one via, stored pre-publication 7.277325 wall / 5.137059 CPU seconds within 60-second caps. The [full multichannel run](evidence/board-floor-multichannel-001/result.json) remains **rejected: 160 opens, one thermal error, 94 warnings, zero exclusions**, 57.378238 wall / 64.509057 CPU seconds within 120-second caps. Its 75 width, 13 clearance, three annulus and three via-diameter errors from the older run are absent. This historical comparison is descriptive, not a fresh matched experiment or completion gain. No new eligible/accepted input follows. Strategy/recovery/portfolio propagation remains blocked. This is B1 correction, not C novelty ([scope](docs/board-floor-guidance.md)).

## Earlier placement correction: fewer opens, both matched arms rejected

The owned fixture002 at `73107be` passed the complete real diagnostic route and independent readback: zero native findings, one required via, 67.926667 mm, stored 8.577736 wall / 5.535336 CPU seconds under 60-second caps. Its actual track crosses the original unrestricted placement area. Fixture001 remains a pre-engine identity-parser failure; the narrow empty-area-net fix leaves all source bytes intact. Independent review checked 50 bindings plus the crossing and public copies. Fourteen actual-evidence tampering controls reject consistently after rehashing, with original/relocated/restored positives passing; these are offline consistency checks.

The same-HEAD [full-board pair](evidence/placement-routing-pair-001/summary.json) then completed both policies. Every arm pays all shared overhead under equal 120-second wall/CPU caps:

| Diagnostic policy | Opens / blocking / warnings / exclusions | Charged wall / CPU seconds | Accepted |
|---|---|---|---|
| Board-floor reference | 160 / 1 thermal / 94 / 0 | 65.278253 / 72.920478 | No |
| Same policy plus exact placement correction | 8 / 2 clearance / 94 / 0 | 46.451122 / 59.604769 | No |

The only pre-adapter difference is removal of eight DSN obstacles attributed to four explicitly unrestricted original placement areas. All original areas/rules remain. This reduced opens by 152 but added one blocking finding; both outputs remain invalid. It is an adapter diagnosis, with no completion gain, valid-route quality delta, production promotion or C/B2 superiority claim. Independent review passed 81 checks. The remaining clearance reports are 0.2994/0.2995 mm against the unchanged 0.3000 mm minimum. The engine stopped on stagnation with nine internal unrouted items; native refill reports eight opens. The subsequent declared v2 experiment below follows that geometry/search diagnosis.

## Entire considered population and provenance

**16 acquired boards remain in the denominator: 7 manifested inputs plus 9 incomplete expansion inputs; 3 statically eligible, 13 unsupported.** Three inputs were routed and now have accepted production-policy evidence from separate strategies and experiments. Eligibility is not native acceptance. All are development-exposed; independent families are unverified. The immutable [prior14 per-board index](evidence/development-outcomes-003/index.json) and [two-board acquisition extension](evidence/licensed-acquisition-003/population-extension.json), followed by the [current qualification snapshot](evidence/placement-production-qualification-001/summary.json), retain every considered input and all prior attempts without pooling different policies/versions.

| Manifested board | Current recorded condition |
|---|---|
| sonde xilinx | Static eligible; accepted quality experiments above |
| interf_u | Static eligible; automatic C accepted; tested B0/B1/B2 rejected |
| multichannel_mixer | Static eligible; production placement guidance and v2 diagnostic each accept 0 opens / 0 blocking / 96 warnings; zero-margin and low-via-cost diagnostic variants remain rejected |
| pic_programmer | Unsupported custom pads and severity semantics |
| complex_hierarchy | Unsupported class assignments and empty-net zone severity semantics |
| ColdFire/Xilinx | Unsupported class assignment/nonblocking thermal constraints; four-layer scope unqualified |
| multichannel_mixer-unrouted | Missing matching project binding and unqualified board format |

Seven earlier incomplete inputs are **FDC2214, VEML7700, ADS1219, SFA40, Roller Encoder, LIS3DH Micro and LIS3DH**. Recorded class/rule/net-tie/exclusion/custom-pad gaps and external dependency closure remain unresolved ([audit](evidence/corpus-expansion-policy-audit-001.json)). Roller model blobs are pinned, but custom-footprint/model rights remain unresolved ([closure002](evidence/source-closure-review-002/review.md)). Shared templates or different product functions do not prove circuit independence. Forty-eight metadata-only repositories are a separate search denominator. No original rule was relaxed to admit inputs.

PMOD-to-Qwiic and LiPo Disconnector add two incomplete development inputs. The bounded pinned acquisition verified 81 files / 7,858,011 bytes. PMOD has no native or engine execution; LiPo now has the two non-routing native observations recorded below. Both reject the unchanged format gate; PMOD also has unqualified legacy class/severity mappings. The independent [closure audit](evidence/licensed-closure-audit-003/REPORT.md) verifies three missing local model blobs totaling510,932bytes and unresolved stock-library identities; both originals remain incomplete. No source file or rule was relaxed, and neither is an untouched evaluation input. Their complete raw acquisitions are now covered by verified archive4795010.

## Controls, installation and preserved failed hypotheses

The current integrated root suite passed **517 tests in 9.530 seconds** ([log](evidence/placement-handoff-source-001/root-suite.log)); separate v2 and fixed-counterfactual suites passed56 and18 controls respectively. The unchanged native smoke and six literal-class native regression controls passed. Real floor-engine SIGTERM left a cancelled receipt, cleaned its process group and preserved sources. Other native controls remain separate evidence. Mocked stages/AI audits do not establish native correctness or human review.

Historical fresh clone/venv **installation002** passed 160 then-current tests, doctor, native routing and receipt checking with network denied, reusing installed tools/JAR cache. Installation003 below subsequently qualifies the placement integration with 494 tests and a fresh native route. Actual PCB Editor and `review-copy` observations qualify separate-copy review only: GUI refill/DRC differed in library warnings, and discard changed disposable project defaults. Live apply/undo, stale-editor protection, detached-process/OS-crash/interstage/GUI cancellation, selected-net routing, full schematic parity and a plugin remain unqualified ([installation](docs/install-test.md), [GUI](docs/gui-workflow.md)).

Preserved historical failures include two [KRT spikes](docs/krt-spike.md), invalid early profiles/timeouts and extra-via tradeoffs, failed SMD-drill/exclusion recipes, installation001's sandbox monitor failure, thermal geometry attempts and floor001. Corrected prospective004 used verified deadlines. Old unsnapshotted smoke evidence stays provisional; no historical receipt was rewritten to claim a later fix.

## Continuation and gates

G0 and the real G1/measurement slice are evidenced. G2 needs broader failure/constraint controls; G3's 30–50-family audit, generalized G4 improvement, full G5 integration, G7 untouched family-disjoint evaluation and G8 release readiness remain open. G6 currently favors measured deterministic mechanisms; no justified training task/model exists. Physical/electrical validation and human PCB review are not established.

Resume in this checkout, with one lead owning the single native/engine lane. These commands exist now; check current sources before using old receipts after implementation changes:

```sh
cd /Users/faisal/Projects/KiCad-Autorouter-local
git status --short
python3 -m autorouter doctor
python3 data/fetch.py --verify
python3 -m unittest discover -s tests -v
python3 -m autorouter check-result .runs/thermal-paired-001/C_thermal/result.json
```

After the lane is idle, this fresh-output command reproduces the passed fixture (do not repeat without a new verification need):

```sh
python3 -m autorouter route tests/fixtures/board-floor/fixture.kicad_pcb --guidance board-floors-v1 --adapter both --profile completion-only --seconds 60 --output .runs/board-floor-production-followup-001
python3 -m autorouter check-result .runs/board-floor-production-followup-001/result.json
```

Five actual production floor controls and nine offline receipt controls pass. Placement native001 confirmed the all-allowed export mismatch but **failed all three genuine-prohibition negative controls**: pinned KiCad returned no findings. Production now rejects genuine/ambiguous board or footprint rule areas and legacy module syntax. Three actual earlier accepted receipts still pass readback. A fresh14-board static audit keeps3eligible/11unsupported; four previously unsupported boards gain this additional reason. Native002 reproduced the omission in all3cases after removing only disabled placement metadata (4.873879wall/3.710146CPU); constraint qualification remains false. The explicit diagnostic fixture and same-HEAD pair are now recorded above: fewer opens, both arms invalid, no completion gain or broader keepout support. See `docs/placement-area-diagnostics.md`; preserve failed001 unchanged.

At the next native milestone, freeze ignored writes, commit/audit/push and run `python3 -B scripts/backup.py` again. Existing-archive check: `python3 -B scripts/backup.py --verify .local-backups/checkpoint-20261010T140100Z-fece3bf3f7e04192920f6b7a079f753c/receipt.json`. Keep spending at $0, one bounded worker, originals untouched and private/unlicensed material out of Git. No background/auto-resume work or formal release/package publication.

Before further native batches, the project backup ceiling is raised from1GiB to2GiB: the verified1,017,693,214-byte raw inventory leaves only56,048,610bytes under the old cap, less than the next bounded comparison. The filesystem has approximately404GiB free. The100,000-file cap, credential/path/source-freeze guards and streaming writer remain unchanged;27 backup controls pass in1.435seconds. This did not change OS protections. The subsequent 00fde8f full archive and restoration passed under the new ceiling.

## Placement/search v2: measured diagnostic completion

At `24ab168d`, the new strongest-policy owned fixture passed actual engine/import/refill/final DRC: zero findings, one required via,67.933738mm;8.284335 wall/5.466622 CPU seconds. The same-code [three-arm experiment](evidence/placement-search-three-arm-001/summary.json) then completed with all shared overhead charged to every arm under equal120second caps:

| Policy | Opens / blocking / warnings / exclusions | Charged wall / CPU seconds | Accepted |
|---|---|---|---|
| Placement/floor, zero margin, default via costs | 8 / 2 clearance / 94 / 0 | 47.237442 / 60.386719 | No |
| Same pipeline,20µm planning margin, default via costs | 0 / 0 / 96 / 0 | 44.580724 / 56.572069 | Diagnostic only |
| Same20µm margin, lower via costs | 0 / 1 thermal / 95 / 0 | 34.131237 / 38.634855 | No |

The accepted candidate is `36e778573b2c90dfca8f9d45597e6bd890cc45c7fc4c6c86a2673e2e7fef3bef`,2647.385729mm/21vias. Exactly three engine-planning clearance atoms gain20µm; source/native rules, pad geometry, width/via dimensions and final acceptance stay unchanged. The new reference reproduces the earlier8opens/two clearance errors. Margin changes also change search behavior, so the completion gain is not attributed solely to the two local geometric discrepancies. Lower via costs produced a thermal-relief error at C2 and are not selected as an improvement. No pair has two valid outputs: there is no valid route-quality delta. The accepted route has96warnings, including9connection-width warnings; routing acceptance is not whole-project or electrical cleanliness.

All three exact receipts passed root readback. Independent raw review passed167 checks; the separate counterfactual/public-copy audit passed344 checks. All130 fixture,140 three-arm and19 counterfactual selected public files match their exact raw bytes. This is one exposed adapter/search result, not C novelty, production promotion, a new independent family or generalized superiority. At that historical checkpoint the14-board denominator was3eligible/11unsupported; two production-policy inputs and one distinct diagnostic input had accepted evidence. The current16-board state is recorded above. The new immutable outcomes003 index records this state, retains all14 inputs and prior outcomes002, and reproduces byte-identically after25 root controls and independent review. The review reproduced and fixed a bounded-final-read gap; its tiny-file falsifiers and unchanged index are preserved.

The separate fixed two-segment clearance counterfactual is integrated and independently source-reviewed;18 root pure controls pass. Its actual native run at897add4 failed the fixed positive predicate: the two original pad violations disappear, but four new clearances against adjacent GND tracks arise; eight opens remain. The unchanged negative reproduced the original errors. Both candidates are rejected;12.501076wall/10.826642CPU fit the shared60second caps. No recipe was retuned. It cannot establish route acceptance or a universal margin guarantee. The completed 00fde8f full archive now preserves all of this raw evidence and passed restoration.

## Fresh production placement qualification

The explicit command now passes the owned fixture and full multichannel replay. Fixture at d6f7f81: zero findings, seven segments, one required via; stored 8.037944 wall / 5.298197 CPU seconds. Multichannel at eab7540: zero opens / zero blocking / 96 warnings / zero exclusions; 2,647.385729 mm and 21 vias; stored 36.878350 wall / 51.577022 CPU under 120-second caps. Root standalone receipt checking passes both. This is integration of the earlier adapter/search result, not a new C mechanism or comparative speed claim. Nine connection-width warnings remain, compared with six in the original; the other 87 warnings match in count and category. No electrical adequacy is inferred.

Five real native fault controls pass; the first attempt remains a pre-native harness failure. Both actual engine-stage cancellation signals pass. Twelve rehashed semantic receipt negatives reject after valid relocated controls. Native-control timings are 9.452607 wall / 6.336963 CPU under shared 60-second caps. Cancellation controller wall time is recorded, but full controller CPU was not measured. No full GUI, interstage/OS-crash, electrical or human-review qualification follows.

The [new saved-evidence summary](evidence/placement-production-qualification-001/summary.json) retains all 16 acquired development inputs: 7 complete / 9 incomplete; 3 statically eligible / 13 unsupported; 3 inputs now have accepted production-policy evidence using different strategies in separate experiments. Family independence remains unestablished and no pooled rate is reported. Old index003 and acquisition extension are immutable. Current installation qualification and the bounded original-format observations are recorded below; complete raw qualification evidence is covered by the verified full archives.

Independent production review is complete: fixture83, cancellation40, native-controls168, full-board83 and population/public912 checks passed. All747 selected public files /31,006,534 bytes match exact raw originals;54 repeated dependency omissions are hash-listed. The full production route matches the prior diagnostic normalized topology, with the same96warnings. This verifies evidence/integration, not a new quality or speed gain (`evidence/review-placement-production-native-001/REVIEW.md`).

The current installer source is promoted after independent falsifiers exposed and fixed late-Git material changes and native-receipt capture ordering. It preserves the native default, adds fixed placement qualification, creates clean-clone scratch explicitly, and guards final success publication. Root494 tests passed before actual installation003, which now also passes as recorded below.

## Current fresh-clone installation

Installation003 at `6c34110262795bb029dbecdcb62cb95d971faa17` passed all 20 actual commands: a new local clone/venv, offline setup/doctor, 494 tests, the explicit placement fixture route and saved-result readback. Eight final Git observations and all 7,673 source/clone tracked files remained consistent. The new native candidate has zero findings, one via and 67.933738 mm. The independent audit passed 217 checks and verified all 160 selected public files against raw originals. See `evidence/installation-003/result.json` and `evidence/review-installation-003/REVIEW.md`.

Stored installation samples are 32.868175 wall / 29.866697 CPU seconds before final publication; the 600-second wall acceptance cap includes final checks. Native samples are 6.413382 wall / 4.442717 CPU under 60-second caps. This reused installed KiCad/Java/base Python and the verified cached JAR on this Mac under network denial. It qualifies a fresh local checkout/venv, not a fresh Mac, package, GUI workflow or broader routing success. Complete scratch evidence, later installer fixes/reviews and both LiPo diagnostics are now covered by archiveee431c0.

The independently reviewed LiPo original-format observation helper is promoted at `experiments/lipo_native_diagnostic_v1`. It permits only unchanged complete copies, same-load export/observation and nonsaving original-rule DRC under shared 30-second wall/CPU and 20 MiB caps. Review falsifiers exposed and fixed both stage capture ordering and late material changes. Its actual native results are recorded below; production format support and dependency closure remain false.

## Original-format LiPo diagnostic: export failed

Actual001 at `7ecc1b3004831aea614fbc8c7d42babd1571bdbd` ran one bounded KiCad observer/export and failed when `ExportSpecctraDSN` returned false. No observation JSON, DSN or DRC result was produced; the DRC stage was not reached. All 26 original files and copied project bytes remained unchanged, and process cleanup completed. Stored 2.305342 wall / 1.973175 total CPU seconds fit the shared 30-second limits. The independent 161-check audit confirms the failed record and exact source/tool/runtime bindings (`evidence/lipo-native-diagnostic-001`, `evidence/review-lipo-native-001`).

The native log also records two no-layer via-width assertions before the export failure; they did not stop execution and are not established as its cause. Original static references and pinned exporter source identify duplicate padless footprint references as a source-backed failure hypothesis. The separately selected context-only observation followed by nonsaving original-rule DRC is reviewed and promoted with52 pure controls plus6 independent methods; its actual002 run completed as recorded below. No original renaming, format migration, route removal or support expansion is authorized by this failure.

The separate context-only002 at `dbea85e796a1024ade7346568369283719289d86` completed both actual nonsaving native stages. Ten pad identities, three nonempty nets and eight original route identities match; all 26 original files and their existing bytes in both complete copies remain unchanged. DRC adds only the allowed disposable `lipo_disconnector.kicad_prl`. Original-rule DRC with in-memory refill reports zero opens / zero blocking / seven warnings / zero exclusions. Warnings are three unavailable footprint libraries and four silkscreen overlaps. All three nets load as Default with 0.25 mm preferred width, 0.20 mm clearance and 0.80/0.40 mm via/drill; native global minimum clearance is zero.

KiCad reports seven ignored checks versus four explicit ignores in the older project: `footprint_filters_mismatch`, `track_not_centered_on_via` and `tuning_profile_track_geometries` are additional native defaults, absent as keys in the original file. No original severity bytes were changed. This distinction remains a semantic-support gap; it is not silently equated with a qualified original-rule migration. The source's existing routes were retained, so this is not autorouting completion. No DSN or saved board was emitted. Complete native padless-footprint census, saved geometry/zone/teardrop equivalence, dependency closure and format support remain unqualified. Stored pre-publication 3.917796 wall / 2.776591 CPU seconds fit shared 30-second caps; the independent raw audit passes197 checks and confirms all92 retained run files remain unchanged. `evidence/lipo-native-diagnostic-002/summary.json`.

The ee431c0 archive/restoration is complete and the write freeze is released. The next active milestone is the narrowly scoped placement disposable review-copy extension, with independent adversarial source review and a separate native-control helper in development. The reviewed source is now integrated: strict schema3 placement and native receipts can produce complete bounded disposable copies; schema2 floor/unknown/diagnostic receipts remain blocked. Root517 software tests pass. Fresh native copy controls and actual GUI qualification remain pending; no live-board application is implemented.
