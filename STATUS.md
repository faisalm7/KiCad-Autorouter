# Current status

Updated October 10, 2026 (America/Los_Angeles). Active local reconstruction; the project is not complete. Native development evidence shows shorter routes beyond the adapter and tuned baseline on **one exposed family**, with equal vias against B2. Generalized superiority and electrical suitability remain unproved.

## Locality and recovery

Work runs on this Mac, Darwin 27 arm64, in `/Users/faisal/Projects/KiCad-Autorouter-local`, branch `rebuild/local-20261010-015447`. Initial safe commit `683e41a` and later development checkpoints were pushed and independently checked. Latest verified checkpoint before this update: **`1cad16dacf118e002b5fdd6fc9793ed2273f0bcf`**, with remote SHA and `scripts/native_thermal_bridge_control.py` bytes matched (`evidence/backups/checkpoint-1cad16d.json`). The parser and portfolio harness are in that checkpoint; current documentation changes require the next audit. No failed cloud environment, global preferences or safety controls were changed.

The latest actual bundle/raw archive is still **`7c7f358`**. Restoration verified all Git refs and **11,060 non-Git files**, then ran restored CLI help (`evidence/backups/restore-7c7f358.json`). It predates interf-native-001 and quality-comparison-003; newer runs and corpus audits are **not covered by that raw backup**. A fresh archive and restoration are next. Raw archives remain on this Mac only; an owner-selected private off-Mac destination is pending. GitHub holds audited source and small public evidence, not complete raw artifacts.

## Executed pipeline, controls and integration

The pinned CLI uses KiCad 10.0.0 and its bundled Python, Freerouting 2.5.0, and Java 25.0.2. It snapshots complete projects, preserves original geometry/nets/terminal mapping/rules/zones/protected routing, imports routing, refills zones, and validates the exact final candidate with native DRC/connectivity. Per-job config, cache and documents are isolated. Missing, stale or unsupported checks reject. Receipt checking verifies stored consistency; it is not fresh native execution or cryptographic authenticity.

Fourteen original native controls passed expected outcomes: one positive and thirteen deliberate geometry, disconnect, short, protected-routing, zone and rule/severity failures. A real engine SIGINT control rejected incomplete output, cleaned its owned process group and preserved sources/code (`evidence/native-cancellation-001`). Reviews reproduced and verified fixes for receipt path escapes, setup symlinks and competing-file overwrite. Detached children, OS crashes, interstage and GUI cancellation remain unqualified.

Additional **native-exclusion-002** passed on disposable copies: fresh positive DRC had 0 opens, 0 blocking findings, 1 warning and 0 exclusions; the deliberately excluded warning was emitted by KiCad with `excluded: true`. The old parser counted 0 exclusions; the corrected production parser counts 1 and rejects it. Sources and original severities stayed unchanged. This validates parsing/rejection, not candidate promotion or a new routing success. Failed control 001 remains retained. Present exclusion flags now require a Boolean; existing severity behavior and eligibility gates remain unchanged (`evidence/native-exclusion-002`).

The latest full coordinator suite passed **222 tests** (`.runs/tests-paired-integrated-001.log`). These do not replace native evidence. Fresh local clone/venv installation002 at `dd2cce9` passed setup, doctor, all 160 then-current tests, a real native fixture route and strict receipt checking with network denied. It reused installed Mac tools and verified JAR cache, so it is not fresh-Mac or package qualification. Installation001's sandbox-denied setuid monitor failure remains retained; its replacement unprivileged libproc monitor passed focused controls. Current changes have not repeated installation qualification.

The actual PCB Editor opened a disposable B1 project and ran refill/DRC: 0 errors/opens, 25 library-disabled warnings, 0 exclusions and four original ignored checks. This differs from isolated CLI warning configuration. Discard preserved board bytes but changed disposable project defaults and created history/preferences. An actual C pilot001 `review-copy` also passed. These qualify a separate-copy review workflow only; live application, undo, stale editor detection and a plugin remain unqualified (`docs/gui-workflow.md`).

## Measured development experiments

Frozen adapter ablation001 at `7fef467` reproduced both interchange defects on sonde: B0 had 3 opens / 7 blocking findings; graphics-only retained 3 opens; planes-only retained 3 blocking findings; combined B1 accepted with 786.316 mm / 3 vias and one library warning. Native zones and constraints were preserved. This is adapter correction. Two bounded KRT alternative-engine spikes failed preservation/native validation (`docs/krt-spike.md`). Early smoke records before the frozen ablation remain provisional.

**Quality comparison004**, frozen at `221f26f2808b1918aca2a1df3b3f70b345605eb1`, completed all five fresh arms under equal **120-second wall and measured-CPU acceptance ceilings**, including conversion, failed proposals, strategy work and native validation:

| Arm | Opens / blocking | Track length | Vias | Receipt wall / CPU seconds | Accepted |
|---|---|---|---|---|---|
| B0 stock | 3 / 7 | 566.454 mm | 4 | 10.656 / 10.644 | No |
| B1 combined adapter | 0 / 0 | 786.316 mm | 3 | 13.536 / 16.701 | Yes |
| B2 tuned | 0 / 0 | 786.316 mm | 2 | 18.257 / 26.196 | Yes |
| C_single | 0 / 0 | 662.694 mm | 2 | 104.665 / 83.392 | Yes |
| C_feedback | 0 / 0 | 644.549 mm | 2 | 107.789 / 85.618 | Yes |

Every accepted arm retained one warning and zero exclusions. C starts from its own tuned incumbent and permits only native-valid deletions that do not increase vias, length or warning identities. Warning-guided compound deletion improved 18.145 mm over the single-deletion ablation and 141.767 mm over tuned B2, with equal vias and more compute. B0's invalid shorter output is not a quality comparator. This is one-family proxy-quality evidence, not a speedup, whole-project DRC cleanliness, physical validation or generalized superiority. Exact invocation budgets and rejected trials are in `docs/quality-experiment.md` and `evidence/quality-comparison-004`.

Earlier pilots remain retained with their limitations: pilot001 had an invalid intended B2 profile; pilot002 traded shorter length for an extra via; earlier inner timeout strings parsed to null despite effective outer supervision. Corrected HH:mm:ss deadlines were prospectively used in 004. No old receipt was rewritten.

**Interf-native-003 and 004**, frozen at `80acfa8`, both pass strict generated netclass width/via targets after optional engine width-reduction paths were disabled. Completion-only used 27.437 wall / 41.615 CPU seconds; standard optimization used 59.469 / 80.371. Both have zero opens but **one blocking U9 C4 isolated-island `starved_thermal`**, so both remain rejected. Their 4,994.888 mm / 35-via outputs are not accepted quality results. Original thermal checks, pad/zone intent and source files were preserved; the source also has inherited thermal findings. The first repair diagnostic stopped before native execution because its global UUID uniqueness guard also counted dimension child labels; that failed invocation is retained. After the guard correction was audited/pushed at655207c, diagnostic002 passed the first2.1mm bridge: zero opens/blocking/exclusions, strict targets pass, no added vias,5.577wall/4.499CPU seconds. This repair-only result excludes acquisition of the failed incumbent and is not a production routing receipt or fair comparison.

The stronger **B2 portfolio harness is implemented but has no native routing result yet**. It tries three predeclared via-cost settings in fixed order under one shared 120-second wall/CPU allowance, charges all attempts and selection, selects fewer vias then shorter length, and retains the Pareto frontier. Eighteen portfolio controls and **539 actual-JAR settings checks** passed; settings checks route no board. Review reproduced and fixed final-publication cancellation handling. A fresh paired comparison with C_feedback on the same frozen code is next; quality004 is not a same-code portfolio comparison.

## Full considered development population

Keep the full denominator of **14 acquired boards: 7 complete manifested boards plus 7 incomplete audit inputs**. Current static gates admit 2 and reject 12; static eligibility is not native routing acceptance. All are exposed development material; family independence is unverified.

The complete manifest contains six licensed projects, 132 original files plus notices, **144 files / 13,654,726 bytes**, all hash-verified. `evidence/corpus-audit-002.json` records its seven-board audit:

| Complete board | Current status |
|---|---|
| sonde xilinx | Statically eligible; accepted native experiments above |
| interf_u | Statically eligible; exact two-class/target checks pass, native thermal acceptance fails |
| pic_programmer | Unsupported custom pads and four unqualified severity keys |
| complex_hierarchy | Unsupported class bindings and `zone_has_empty_net` severity semantics |
| ColdFire/Xilinx | Unsupported four-layer class scope, assignment pattern and nonblocking thermal check |
| multichannel_mixer | Original required `padstack` check is nonblocking; stronger acceptance policy unqualified |
| multichannel_mixer-unrouted | Missing same-basename project binding and unqualified board version |

The fixed six-project expansion audit acquired seven more boards in 35 original/notice files (6,495,334 bytes). All seven remain statically unsupported, external library/model closure is incomplete, and none is promoted (`evidence/corpus-expansion-audit-001`). Shared-template ancestry is recorded; multichannel siblings and related audit variants are not independent families. Forty-eight metadata-only repositories form a separate search denominator. No original rules/severities/bindings were changed to admit inputs. The 30–50-family development audit and untouched family-disjoint evaluation remain unmet.

## Next execution and open gates

Audit/checkpoint current changes, verify remote SHA/file bytes, create and restore-test a current raw archive, then freeze code for a fresh B2-portfolio/C_feedback comparison. Preserve full 120-second wall/CPU accounting and failed attempts. Next investigate the interf thermal failure without relaxing rules, and qualify broader padstack/unused-class support with native controls before changing eligibility. `PLANS.md` contains the concrete sequence and commands.

G0 and a narrow G1/G2 vertical slice are evidenced. G3 representative coverage, generalized G4 improvement, full G5 application/installation qualification, G7 untouched evaluation and G8 release readiness remain open. Current evidence does not justify model training. Selected-net routing, schematic parity, human PCB review and physical/electrical validation are unestablished. No formal release/package, paid service or background/auto-resume work was initiated.
