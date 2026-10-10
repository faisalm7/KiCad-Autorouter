# Current status

Updated October 10, 2026 (America/Los_Angeles). Active local reconstruction; the whole project is not complete. Native development evidence now shows a shorter route beyond both the adapter and tuned baseline on **one exposed family**, with equal vias against B2. Generalized improvement and electrical suitability remain unproved.

## Locality and recovery

Work runs on this Mac, Darwin 27 arm64, in `/Users/faisal/Projects/KiCad-Autorouter-local`, branch `rebuild/local-20261010-015447`. Initial safe commit `683e41a` and subsequent development checkpoints were pushed to the authorized repository and independently checked by remote SHA and file bytes. Latest verified checkpoint before this update: `7c7f35875620d079d24dac4f52460c1237ca4a32`; receipts are in `evidence/backups`. No cloud environment or global protection/preferences were changed.

An actual bundle and raw archive for `7c7f358` restored all Git refs and **11,060 non-Git files**, then ran restored CLI help successfully. `evidence/backups/restore-7c7f358.json` identifies the archive/verification. This covers artifacts before `interf-native-001` and `quality-comparison-003`; later work needs another archive. The raw backup is on this Mac only, so it provides no disk-loss protection. An owner-selected private off-Mac destination remains pending. Audited source and small public evidence are backed up on GitHub.

## Executed pipeline and controls

The pinned CLI uses installed KiCad 10.0.0 and its bundled Python, Freerouting 2.5.0, and Java 25.0.2. It snapshots complete projects, preserves original geometry/nets/terminal mapping/rules/zones/protected routing, exports and imports only routing, refills zones, and validates the exact final candidate with native DRC/connectivity. Per-job config, cache and documents are isolated. Missing, stale or unsupported checks reject. Receipt checking establishes stored consistency, not fresh native execution or cryptographic authenticity.

Fourteen actual native controls passed their expected outcomes: one positive and thirteen deliberate geometry, disconnect, short, protected-routing, zone and rule/severity failures. Independent reviews reproduced and verified fixes for receipt path escapes, setup symlinks and competing-file overwrite. SIGINT during a real engine run rejected the incomplete candidate, cleaned its owned process group and left sources/code unchanged (`evidence/native-cancellation-001`). Detached children, OS crashes, interstage and GUI cancellation remain unqualified.

Fresh installation attempt 001 failed because the sandbox denied the old setuid process monitor; all logs are retained. The replacement unprivileged macOS libproc monitor passed its focused subprocess controls. Fresh local clone/venv attempt 002 at `dd2cce9` passed setup, doctor, all 160 then-current tests, a real native fixture route and strict receipt check with network denied. It reused installed Mac tools and a verified JAR cache; it does not qualify a fresh Mac or package installation. The current timeout-repair revision passes **171 coordinator tests**; native tests are separately identified.

The actual PCB Editor opened a disposable complete B1 copy and ran zone refill/DRC: zero errors/opens, 25 library-disabled warnings, zero exclusions, four original ignored checks. Its warning configuration differs from the isolated CLI's one warning. Discard preserved board bytes but changed disposable project defaults and created preferences/history. The actual C pilot 001 `review-copy` operation also passed. These qualify a separate-copy review workflow only; live application, undo, stale editor detection and a plugin remain unimplemented/unqualified. See `docs/gui-workflow.md`.

## Measured development experiments

Frozen adapter ablation 001 at `7fef467` compared five arms on sonde under 120-second budgets. B0 had 3 opens / 7 blocking findings; graphics-only retained 3 opens; planes-only retained 3 blocking findings. Combined B1 accepted zero opens/blocking findings, 786.316 mm / 3 vias, and one library warning. Original native zones and constraints were preserved. This is adapter correction, not new routing strategy. Two bounded KRT alternative-engine spikes failed preservation/native validation; both raw and route-only outputs were rejected (`docs/krt-spike.md`).

The quality comparison charges conversion, routing, pruning and native checks to equal 120-second wall and measured-CPU acceptance caps. All outcomes and rejected trials are retained. C currently starts from its own tuned B2 incumbent and accepts only native-valid deletions that do not increase vias, length or warning identities.

| Development pilot | B1 length / vias | B2 length / vias | C length / vias | Interpretation |
|---|---|---|---|---|
| 001 | 786.316 mm / 3 | Invalid intended profile | 657.504 mm / 3 | B2 threshold mistake retained; not a primary B2 comparison |
| 002 at `57db787` | 786.316 mm / 3 | 786.316 mm / 2 | 660.099 mm / 3 | C shorter but one extra via against B2 |
| 003 at `7c7f358` | 786.316 mm / 3 | 786.316 mm / 2 | 662.694 mm / 2 | C shorter by 123.621 mm with equal vias against B2 |

Accepted arms in 002/003 have zero opens/blocking findings and one warning. Pilot 003 C consumed 105.066 seconds receipt wall / 83.722 seconds CPU; B2 consumed 19.525 / 28.064. This is a proxy-quality gain with more compute, not a speedup, whole-project DRC cleanliness, physical validation or generalized superiority. See `docs/quality-experiment.md` and the stored summaries for exact enclosing-invocation budgets.

An actual pinned-JAR settings probe subsequently found that earlier inner timeout strings (`60s`, `30s`, `100s`, `90s`) parse to null. Outer supervision and measured acceptance were real, but intended inner deadlines were ineffective. Sonde engines finished before those intended limits; larger-board behavior was affected. First production `interf_u` routing completed internally but timed out during optimization before writing an SES: 120.311 wall / 139.471 CPU seconds, rejected, cleanup complete, no final native candidate. This does not qualify multiclass routing.

The pending repair uses HH:mm:ss durations and reserves 30 seconds for cooperative engine shutdown plus 10 seconds for native finalization. Actual-JAR probe 002 passed **201 checks across 12 profile/budget cases** without routing a board. `completion-only` explicitly disables optimization for qualification and is distinct from B2. Reserves are planning allowances; the outer wall/CPU gates and final native checks remain authoritative. New native qualification and a prospective corrected comparison are next; prior records remain unchanged.

## Full considered data population

Six complete licensed source projects contain seven boards: 132 originals plus notices, **144 files / 13,654,726 bytes**, all hash-verified. Static audit 002 has **2 eligible, 5 unsupported, 0 parsing errors**; it performs no native execution. All are exposed development data; six directory family IDs do not establish ancestry independence.

| Board | Current static status |
|---|---|
| sonde xilinx | Eligible; native development comparisons above |
| interf_u | Literal two-class export checks passed; production native routing qualification pending |
| pic_programmer | Unsupported custom pads and four unqualified severity keys |
| complex_hierarchy | Unsupported class bindings and `zone_has_empty_net` severity semantics |
| ColdFire/Xilinx | Unsupported four-layer class scope, assignment pattern and original nonblocking thermal check |
| multichannel_mixer | Original required `padstack` check is nonblocking |
| multichannel_mixer-unrouted | Missing same-basename project binding and unqualified board version |

The multichannel siblings stay in one family despite placement differences. Original rules/severities/bindings are never modified to admit excluded inputs. A metadata-only candidate survey is ongoing; candidates are not acquired or independently qualified families. The required 30–50-family audit and untouched family-disjoint evaluation remain unmet.

## Continuation and unmet gates

G0 and a narrow G1/G2 vertical slice are evidenced. G3 representative coverage, generalized G4 improvement, full G5 application/installation matrix, G7 untouched evaluation and G8 release readiness remain open. Current data does not justify model training. Selected-net routing, schematic parity, human PCB review and electrical/physical validation are unestablished. The human review document is a protocol, not completed review. No formal release/package was published.

Use the same checkout, inspect active jobs and allow one heavy worker. Preserve failed runs and use fresh output directories:

```sh
python3 -m autorouter doctor
python3 data/fetch.py --verify
python3 -m unittest discover -s tests -v
python3 -m autorouter route .data/boards/kicad-interf-u/interf_u.kicad_pcb --adapter both --profile completion-only --seconds 120 --output .runs/interf-native-002
```

After an accepted multiclass result, execute `scripts/native_class_controls.py` against that receipt, then run the corrected frozen comparison. Audit, push and independently read back each milestone; `python3 scripts/backup.py` creates and actually restore-tests the next raw archive. No background or auto-resume work is scheduled.

After checkpoint `2751126530ba19bfce05867a9a5d032587578098` was pushed and independently read back, completion-only `interf-native-002` finished in25.439 wall /35.765 CPU seconds. It was rejected: the actual SES includes0.3mm tracks where the native Default target is0.4mm, preserved through import/refill. Raw refill also reports one blocking starved thermal and zero opens. Engine neckdown behavior is under investigation; no target or DRC rule is relaxed. The next strategy revision adds an explicit warning-feedback ablation;190 coordinator tests pass, native joint-deletion evidence pending.
