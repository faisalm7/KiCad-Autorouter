# Fresh-checkout installation test

Current clean installation016 at1156596 passes20network-denied commands/full886 suite and native placement route/check0opens/0blocking/0warnings67.933738mm1via. Outer91.488196wall/96.415649CPU includes final checks. Seven additional installed complete-schematic NUS commands pass route/check/fourplots/acceptintent/freshnativeexport/proofcheck/reject; original0/0/10 retained,2vias71.884325mm, whole-project cleanliness false. Outer39.294178wall/42.072631CPU under180caps. Existing Mac/tools/cache reused; no freshOS/GUI/physical/package claim. [Actual qualification](../evidence/installation-016/SCOPE.md).

Earlier qualification: installation003 at `6c34110262795bb029dbecdcb62cb95d971faa17` passed all20 actual commands in a fresh local clone/venv,494 controls, the explicit placement fixture route and strict readback under network denial. The candidate has zero findings, one via and67.933738mm. All7,673 tracked source/clone files match; the independent217-check audit passes. See `evidence/installation-003` and `evidence/review-installation-003`. This is one clean checkout/venv on the existing Mac, not a fresh Mac installation. Use a fresh output for future qualifications; do not overwrite completed003.

Historical failure: installation 001 at `e1e585f` stopped after clone/setup/doctor because the sandbox denied the old `/bin/ps` monitor. Its 19 failed controls and original logs remain in `evidence/installation-001`. The scoped libproc fix and actual installation 002 resolved that failure without disabling network denial.
```sh
 .venv/bin/python -B scripts/install_smoke.py --output .runs/installation-NEW --guidance placement-clearance-v1
```

Omitting `--guidance` preserves the legacy `native` smoke choice (120 seconds). The explicit `placement-clearance-v1` choice runs exactly one owned placement fixture with the existing fixed 20 µm planning margin, default 50/5 costs, both adapter fixes and completion-only profile (60-second native wall/CPU caps). Both choices run the full clean-venv test suite; the installer creates an empty clone `.runs` before tests. This placement invocation does not repeat the larger-board comparison, all diagnostic native controls or cancellation experiments.

Use Python 3.11 and a new output directory. The source checkout must have no
tracked changes or nonignored untracked files. The script refuses an existing
output and preserves partial outputs and command logs on failure or cancellation.
It never removes or modifies the original checkout's tracked files, Git identity,
global Git configuration, installed applications or private preferences.

The test clones the exact committed local HEAD into the output directory with
`--no-local --no-hardlinks`, checks out that commit detached, and compares every
tracked file against a source hash inventory. This is a disposable test fixture,
not a competing development checkout or managed worktree. Git hooks are disabled
for these commands; no user/global Git configuration is written. A newly created
Python virtual environment uses interpreter copies and no pip installation;
the coordinator has only standard-library dependencies.

The official Freerouting JAR is copied from the existing verified cache and
checked for the pinned hash and independent file identity. The copied checkout's
`setup_engine.py` runs with network denied and must verify that cached asset.
The test then runs doctor, the full lightweight unit suite, one real native route
of the selected project-owned fixture, and `check-result`. All child commands,
including Git and venv setup, run under the existing network-denial sandbox. The native receipt must
bind to the tested commit and unchanged source. Final tracked inventories,
clean status and HEAD are checked for both checkouts.

`result.json` records every command's arguments, working directory, exit/status,
time, CPU, RSS, log path and log hash; it also records the source inventory,
virtual-environment identity, dependency reuse, doctor and native results.
Raw command logs and native artifacts remain under the output. Final publication
checks both source and clone tracked bytes, clean Git status and HEAD, the
complete native result tree, tools, original and venv Python executable/configuration, command logs
and source inventory before and after writing the canonical receipt. Material files are rechecked
after the final Git subprocesses as well; bounded local HEAD/ref/index witnesses
detect changed commit/staging state during those observations. Strict JSON
readback rejects duplicate/nonfinite values or semantic changes. Interruption,
staleness, cap crossing or failed correction archives the old canonical/partial
file before recording failure; no successful canonical is retained on a failed
rewrite. Separate `freshness-*.json/log` files retain the final Git observations.
Wall and total waited-process CPU are sampled before final publication checks;
the 600-second wall acceptance cap includes those checks and the final write.
CPU is measured for installation diagnosis, not capped as a routing comparison. The script uses
a 10-minute overall command budget, 2 MB capped command logs, 4 GiB process-group
RSS polling and a 512 MiB scratch ceiling. Polling can overshoot; it is not an OS
filesystem or memory quota. Nested native workers also use the pipeline's own
bounds. The current tracked source inventory is bounded to18,000files and320MiB; all files are compared. Earlier bounds and their actual failures are retained below. A shared project experiment lock prevents overlapping cooperating
harnesses; the lead keeps all other heavy workers idle. These polling and
post-completion checks are not hard kernel resource guarantees.

Passing establishes relocation into a fresh checkout and virtual environment
on this Mac. The installed KiCad, bundled pcbnew, Java and base Python are reused;
the engine download is reused after verification. It does not establish a fresh
Mac installation, independent dependency acquisition, package installation,
GUI support on a new host, or broad routing correctness. No formal package or
release is produced. Failed steps must remain reported as failed rather than
editing the disposable checkout to make its original commit appear to pass.

The scoped macOS monitor fix passed 22 runner controls both normally and with the actual fresh-venv interpreter under unchanged network denial. Those include a real memory-limit kill, network EPERM and descendant cleanup. Metadata-denial behavior has a separate mocked-error control and is not described as a real OS failure. Evidence: `evidence/review-install-monitor-001`. Those scoped monitor controls are separate from the completed full installation002 and003 runs.

Attempt 002 at `dd2cce9` passed the complete workflow in 14.935349 seconds: all 160 tests, actual native fixture routing and strict result checking passed under network denial. Both checkouts retained their tracked inventories and HEAD. See `evidence/installation-002`; later source changes require separately scoped qualification.

Attempt003 stored32.868175wall/29.866697CPU before final publication; the600-second wall acceptance cap includes final operations. Its native stored sample is6.413382wall/4.442717CPU under60-second caps. Full scratch is205,739,841bytes after publication. Public evidence is a selected exact subset with original paths; the complete local clone/venv/engine/raw tree requires the full local archive. The reviewer retained one wrong-cwd readback attempt, which correctly rejected clone-specific provenance; the actual clone-cwd readback passed without native rerouting.


October 11 capacity update: the audited tracked checkout has 8,985 files / 143,033,406 bytes, exceeding the previous 128 MiB source-inventory cap. The helper now permits at most 192 MiB / 12,000 tracked files, retains the 512 MiB total scratch cap and compares every tracked byte. Twenty-one targeted tests pass, including cumulative-byte and file-count rejection. A fresh actual installation is pending a clean source checkpoint; the historical installation below is not current-version qualification.

Current resumed qualification: installation004 at4807b39 passed all20 commands and535 fresh-venv tests, then real placement routing and central receipt readback. Candidate zero findings/one via/67.933738mm. Installation stored39.983485wall/36.883169CPU seconds and222,833,178scratch bytes; native6.614863wall/4.674714fullCPU within60. Final publication/freshness checks remain included in the600second wall acceptance cap, beyond its stored sample. Source inventory ceiling is now192MiB/12,000files (actual tracked source exceeded the prior128MiB), with no omissions; output512MiB remains unchanged. Selected exact [evidence](../evidence/installation-004/result.json) omits the repeated full tracked-file listing, recorded by hash in omissions.json; full raw clone remains local. Existing Mac/toolchain/cache were reused under network denial. No fresh OS or formal package claim. Future checks must use a new output such as installation005.

October12 capacity follow-up: installation007 at5d4703d stopped before clone because the audited tracked tree reached12,327files/211,119,074bytes, beyond the then192MiB/12,000source cap. The current source allowance is256MiB/16,000files;512MiB scratch,600seconds,4GiB worker polling and network denial remain. Twenty-four targeted controls pass, including exact/excess boundaries and unsafe-file precedence. This permits the retained evidence population; it does not change native acceptance. Fresh installation008 is pending.

Installation008 at71440d8 progressed through the isolated clone/venv/doctor and full643-test suite, then failed solely because test_backup_capacity still expected100000files.642other tests passed; no native route ran. The expectation is corrected to the reviewed120000file ceiling, retaining scaled exact/over-limit controls. Fresh009 remains pending; failed008 stays intact.

Installation009 at339e539 passed20network-denied commands and643tests from its isolated clone/venv, actual native0opens/0blocking/0warnings/0exclusions,1via/67.933738mm and current receipt readback. All7effective ignoredchecks remain (5explicit original settings plus2native defaults). Stored51.365890wall/49.224024CPU precede publication; outer58.060935/55.496116 includes it. A separate command from the same clone/venv produced four valid before/after native plots in3.237173wall/2.472345CPU. [Actual evidence](../evidence/installation-009/result.json), [independent audit](../evidence/review-installation009-preview-001/REPORT.md). Existing Mac and cached dependencies were reused; no fresh OS or package-publication claim.

Current integration: source at3f757c0 has727passing root tests and new pruning/handoff safety fixes. Installation009 remains qualification of339e539, not this source. Run a fresh installation010 after the current sequential native comparisons and accepted-project integration; preserve every failed tree. Use the existing `.venv/bin/python`3.11.9 to invoke the helper, since this Mac's barepython3 currently resolves to3.9.6. Full restoration follows at the scheduled major integration/capacity-change gate.

Installation010 preparation measures287200372tracked bytes before3945880bytes of new workflow curation, above the prior256MiB source allowance. The same installer now retains all source under a finite320MiB/16000file cap;512MiB scratch/600seconds/networkdenial and every native acceptance check remain. Existing exact/excess/unsafe-path capacity regressions remain; targeted24controls pass. Actual fresh installation is pending.

Installation010 atd1c40cc64a97dde7f0b6e85eafbfaeb012cec040 passes20networkdeniedcommands/763tests32.668s and actual native0findings/1via/67.933738mm; completeouter76.455530wall/79.126278CPU, scratch378767185bytes. Installed CLI fourplots/acceptintent/fresh nativeexport/proofcheck/reject passes; its stored16.805164wall/18.366797CPU excludes initial/final tracked-byte checks. The complete envelope is unmeasured and cannot establish budget fairness. [Evidence](evidence/installation-010/SCOPE.md). Subsequent review identifies cancelled-export missingbudget fields (safe rejection); early bound initialization/regression is implemented, new actual final-DRC cancellation control passes3.859929wall/3.193144CPU with120second bounds and shared accounting; real group terminates, no native-algorithm entry inferred. This minor post-install patch is not yet installed qualification. Full restoration is due after writers freeze; current forecast138082files/4115919831bytes fits existing4GiB/140000bounds.

Current installation013 at79c4c78 stops before clone/fullsuite/native:16,624trackedfiles/302,098,185B exceeds16,000file cap. Finite source cap now17,000files with unchanged320MiBsource/512MiBscratch/600seconds/networkdenial/native gates; existing exact/overlimit/path guards retained. New014 is due; no evidence deletion.

Current016 source allowance18000files/320MiB preserves all audited evidence; scratch512MiB/time600/networkdenial remain unchanged. Prior013cap,014acquired-board unit dependency and015overstrict no-SCH parity guard failures remain exact. No failed clone was edited or reused.
