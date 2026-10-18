# Windows008 owned compiler setup assessment

Decision: a compiler-only, non-admitting completion path is defensible prospectively, but attempt002 does not establish its trigger or identify a lingering process. Do not reclassify attempt002, increase timeouts, suppress warnings, or dispatch another007. No production patch is supplied.

## Actual evidence and missing observation

The retained007 attempt002 log records source commit `363a5877b26b17fe7256e8fdcebf765771a16847`. The exact role1 MSVC14.44.35207 build, SDK10.0.26100.0, retained `/W4 /WX` and failed with C2220/C4701: potentially uninitialized `process`. Its Job receipt is `budget_exceeded`, exit_code2,30.047 seconds wall,0.859375 full Job CPU seconds, `process_count=3`, and verified cleanup true. DNS setup separately succeeded.

`windows_process.py:89–103` records `process_count` from `ACCOUNT.TotalProcesses`: cumulative membership, not three remaining processes. It reads the main exit code only after `ActiveProcesses==0`; a deadline first calls `TerminateJobObject(...,2)`. Consequently exit_code2 does not establish whether the compiler had already exited nonzero or was terminated. No pre-termination main-exit, active-member count, member image identity, or member exit evidence was retained. No particular compiler service/linker cause is established.

The controller reported no canary cases, Native execution, or admission. Cleanup reported owned Jobs reaped, profile deletion HRESULT0, profile storage absent, and owned server reaped. ACL sealing had not been reached; `original_dacls_restored=false` is not a successful restoration observation. Registry absence was not queried. The current C zero-initializer is an untested correction.

## Small prospective008 boundary

1. Restrict any new completion behavior to `_setup_argv`'s exact `fixed-owned-C-canary-build` authoring result and role1/2 commands, pinned compiler/source, fresh owned output paths, and captured setup-directory identity. `owned_setup=True` alone is insufficient: the DNS helper also uses it. Ordinary Native/firewall/AppContainer jobs and DNS retain their existing lifecycle.
2. Within the existing30-second wall/full-Job-CPU envelope and existing log, scratch, memory, cancellation and cleanup limits, sample the main process nonblocking. Retain its PID, observed signaled state/exit code and observation time, plus bounded same-Job member identities/counts before any termination. Observation failure remains unknown. A prior or simultaneous failure reason is never cleared.
3. Only an observed main exit zero while no limit/cancellation/failure reason applies may trigger termination of that exact owned Job's remaining members. Main nonzero, still-running/unknown, or timeout never succeeds. Require verified zero active members and existing handle/Job cleanup; charge descendant CPU through reaping and retain cleanup failures as failures. Report controller-terminated members explicitly.
4. Inspect/copy/hash the exact fresh role EXE only after verified reaping; refuse missing, unsafe, oversized or invalid output. Preserve source/tool pins and distinct role outputs. Compiler success alone does not qualify the payload: the actual token, TCP-positive/denial and cancellation controls remain necessary and non-admitting.

This can preserve the guarantee that no owned Job member remains and preserve resource/accounting limits. It deliberately changes setup success semantics from natural completion of every descendant to observed compiler-main success followed by verified owned cleanup. It is not equivalent evidence of natural descendant success and must not be generalized to a Native worker. Existing source does not prove the required main-exit observation; a future bounded008 must collect it before attributing the timeout or exercising this branch. Pure controls should distinguish main-zero/remaining-member cleanup from main-nonzero, timeout, unknown exit, failed cleanup and DNS/ordinary-job behavior. None ran for this assessment.

## Exact inspected pins and scope

| Local path | SHA-256 |
| --- | --- |
| `.runs/windows-appcontainer007-actual002-CI.log` | `3cfb0f49fb742b998a58750ce082187352963a9e35d3c47d55364d622c1630aa` |
| `scripts/windows_native_slice/windows_process.py` | `5ebf596a953e195c75696e57043c66a15422d61584159f8384948e0b494c7fac` |
| `scripts/windows_native_slice/appcontainer_probe.c` | `31359d8cb82e674e56f3ec9829511dfaa716b5446b8686a0ec74f49f05cbdaf4` |

Current-source assessment covers `_run_job`, `_owned_setup_root`, `_setup_argv`, `run_owned_setup`, and the C initializer. The log independently records its actual Windows runner source hash `99e2b459fb8febf9553a86d22e112ac5fe8f78aff4b3954455e641027456af62` and actual C hash `2299df045949673d26176bd960ec125a543a25e84be47b79ba0a9bb8d8d95d02`; these differ from current local bytes. Read-only source/log inspection and authoring this note only: no tests, Windows APIs, Native, GUI, CI, network, installers, downloads, or delegation. No infrastructure-unavailability claim, network-isolation pass, or Windows product support claim.
