# Current status

Updated October 10, 2026 (America/Los_Angeles). **Active local reconstruction; incomplete.** Native experiments show shorter routes beyond a stronger adapter baseline on sonde, and automatic thermal-repair completion beyond tested baselines on interf_u. Different frozen code/strategies on two exposed inputs do not establish a pooled completion rate, independent-family result, generalized superiority or electrical qualification.

## Durable local work and backup boundary

Checkout: `/Users/faisal/Projects/KiCad-Autorouter-local` on this Mac; branch `rebuild/local-20261010-015447`. Latest verified push/read-back is **`8497654be1f9d011eedea746e27bd6798f078cf5`** ([receipt](evidence/backups/checkpoint-8497654.json)). G0 began at `683e41a`; no cloud/worktree was used.

Latest **full** archive: **8799c54**. Restore verified all Git refs, **28,416 non-Git files /940,519,944 bytes**, and CLI help ([verification](evidence/backups/restore-8799c54.json)). Location: `.local-backups/checkpoint-20261010T111408Z-1858532d2b2a47fbbf697c612a30b81d`. Covers all floor production/native/receipt/regression/cancellation evidence and reviews, source-closure002, the deferred pair draft/review, placement diagnosis/research and explicitly partial placement drafts at freeze. Later placement edits are outside it. Initial guard stop was a byte-identical public synthetic-key-header test copy; the exact path/hash exception passed positive and changed-content/path rejection controls. GitHub holds audited source/selected evidence. Full archives remain on this Mac only; an independent off-Mac destination awaits the owner.

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

## Entire considered population and provenance

**14 acquired boards remain in the denominator: 7 manifested inputs plus 7 incomplete expansion inputs; 3 statically eligible, 11 unsupported.** Three inputs were routed; two have an accepted policy. Eligibility is not native acceptance. All are development-exposed; independent families are unverified. The [complete per-board index](evidence/development-outcomes-001/index.json) retains all reasons, attempts and pair gains/losses without pooling different policies/versions.

| Manifested board | Current recorded condition |
|---|---|
| sonde xilinx | Static eligible; accepted quality experiments above |
| interf_u | Static eligible; automatic C accepted; tested B0/B1/B2 rejected |
| multichannel_mixer | Static eligible; floor-guided routing still rejected, 160 opens / one thermal |
| pic_programmer | Unsupported custom pads and severity semantics |
| complex_hierarchy | Unsupported class assignments and empty-net zone severity semantics |
| ColdFire/Xilinx | Unsupported class assignment/nonblocking thermal constraints; four-layer scope unqualified |
| multichannel_mixer-unrouted | Missing matching project binding and unqualified board format |

The seven incomplete inputs are **FDC2214, VEML7700, ADS1219, SFA40, Roller Encoder, LIS3DH Micro and LIS3DH**. Recorded class/rule/net-tie/exclusion/custom-pad gaps and external dependency closure remain unresolved ([audit](evidence/corpus-expansion-policy-audit-001.json)). Roller model blobs are pinned, but custom-footprint/model rights remain unresolved ([closure002](evidence/source-closure-review-002/review.md)). Shared templates or different product functions do not prove circuit independence. Forty-eight metadata-only repositories are a separate search denominator. No original rule was relaxed to admit inputs.

## Controls, installation and preserved failed hypotheses

The integrated root suite passed **387 tests in 6.076 seconds** ([log](evidence/tests/placement-net-identity-root-tests-001.log)). The unchanged native smoke and six literal-class native regression controls passed. Real floor-engine SIGTERM left a cancelled receipt, cleaned its process group and preserved sources. Other native controls remain separate evidence. Mocked stages/AI audits do not establish native correctness or human review.

Fresh clone/venv **installation002** passed 160 then-current tests, doctor, native routing and receipt checking with network denied, reusing installed tools/JAR cache. Current code has not repeated it. Actual PCB Editor and `review-copy` observations qualify separate-copy review only: GUI refill/DRC differed in library warnings, and discard changed disposable project defaults. Live apply/undo, stale-editor protection, detached-process/OS-crash/interstage/GUI cancellation, selected-net routing, full schematic parity and a plugin remain unqualified ([installation](docs/install-test.md), [GUI](docs/gui-workflow.md)).

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

Five actual production floor controls and nine offline receipt controls pass. Placement native001 confirmed the all-allowed export mismatch but **failed all three genuine-prohibition negative controls**: pinned KiCad returned no findings. Production now rejects genuine/ambiguous board or footprint rule areas and legacy module syntax. Three actual earlier accepted receipts still pass readback. A fresh14-board static audit keeps3eligible/11unsupported; four previously unsupported boards gain this additional reason. Native002 reproduced the omission in all3cases after removing only disabled placement metadata (4.873879wall/3.710146CPU); constraint qualification remains false. Next test the narrowly unrestricted placement correction in an explicit diagnostic pipeline and matched budget experiment. No causal routing gain or broader keepout support is claimed. See `docs/placement-area-diagnostics.md`; preserve failed001 unchanged.

At the next native milestone, freeze ignored writes, commit/audit/push and run `python3 -B scripts/backup.py` again. Existing-archive check: `python3 -B scripts/backup.py --verify .local-backups/checkpoint-20261010T111408Z-1858532d2b2a47fbbf697c612a30b81d/receipt.json`. Keep spending at $0, one bounded worker, originals untouched and private/unlicensed material out of Git. No background/auto-resume work or formal release/package publication.

The explicit `experiments/placement_diagnostic_v1` harness is now implemented, with37 pure controls and independent review. Actual fixture001 then passed source DRC and the combined export but rejected before engine because its named-net board retains an empty numeric rule-area net field. This failure is retained unchanged. Next checkpoint these exact helpers, run the owned allowed-placement/required-via fixture, then only if accepted run the same-HEAD floor versus floor-plus-placement pair. This is an adapter diagnostic, with no production promotion or C novelty claim.

The empty-area identity fix now passes387 root tests and37 diagnostic controls; three earlier accepted receipts remain unchanged and pass readback. Independent review passed43 actual export bindings and23 targeted identity controls. It recognizes only the exact empty net0/name pair on a board-level all-allowed rule area; terminal aliases and malformed/conflicting identities still reject. Fresh fixture002 native routing is next.
