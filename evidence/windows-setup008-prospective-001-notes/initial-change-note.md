# Windows008 prospective setup diagnostics

Implemented only diagnostic collection; no compiler-main completion shortcut. Changed files:

- `scripts/windows_native_slice/windows_process.py`: SHA-256 `4c72cd3a4eaa7916a9d8b0d316b5030edcb89b37bfae88248f86274085c0727d` (22938 bytes).
- `tests/test_windows_probe_controls.py`: SHA-256 `ced377102842cc64736a512dafcf5d3a0f1c9389df0c7a8498a1f657d653cc6f` (20768 bytes).
- This authored change note. No workflow, version, protocol, other production file, or old actual007 evidence changed.

The original source pin before this change was `5ebf596a953e195c75696e57043c66a15422d61584159f8384948e0b494c7fac`. The separately retained actual002 log remains `.runs/windows-appcontainer007-actual002-CI.log`, SHA-256 `3cfb0f49fb742b998a58750ce082187352963a9e35d3c47d55364d622c1630aa`; its compile failure/timeout is unchanged.

## Behavior and limits

Only existing `owned_setup` calls collect diagnostics; both fixed DNS and the exact allowlisted compiler setup remain non-admitting. Ordinary firewall/AppContainer/Native runs make no new diagnostic calls and return no new observation field. Each setup polling iteration uses `WaitForSingleObject` with timeout0 on the main process's retained handle. `GetExitCodeProcess` is called only after that handle is signaled, so numeric259 is not mistaken for an unknown running state. No PID is reopened.

At initial observation, main-state changes, natural Job inactivity, and immediately before first failure termination, a fixed32-PID `JobObjectBasicProcessIdList` query records the same owned Job's PID list, accounting active/cumulative counts, main state/exit code, trigger and elapsed time. At most4 snapshots are retained. Observations stop before the first termination, so a termination exit code is not presented as a prior natural main exit. Accounting, main state and membership snapshots are explicitly non-atomic.

Child executable images and child exit identities are **unobserved**. Opening a PID from a changing list would add a PID-reuse boundary; this change avoids that access and makes no stable child-identity claim. PID lists exceeding the fixed capacity, invalid/duplicate IDs, query failures and main poll/exit failures remain explicit unknown. Unknown diagnostics add a fail-closed `process_diagnostic_unknown` reason when there is no prior failure reason; they never produce success. Existing resource failure reasons remain failures and retain their original priority.

Main exit0 does not drain a Job or end its wait. Main exit nonzero likewise does not bypass the existing whole-Job lifecycle. Original wall/full-Job-CPU,2GiB memory,256KiB log,128MiB scratch and4000-entry limits remain unchanged. The original final reaping/cleanup and final CPU accounting block is unchanged. No timeout increase, warning suppression, compiler success override, global setting, installer, or isolation/admission flag was added.

## Actual validation and remaining scope

Final targeted command:

```sh
.venv/bin/python -B -m unittest tests.test_windows_probe_controls tests.test_windows_firewall_diagnostics tests.test_windows_isolation_diagnostic
```

Actual result:29 tests in0.468 seconds,28 passed and1 PowerShell-dependent test skipped. The probe module alone passed22 tests in0.451 seconds. New pure controls exercise main running/exited/unknown/error states, signaled exit259, owned Job-only PID queries, query failure/truncation/bad IDs, pre-termination ordering, no main-zero/nonzero shortcut, unknown refusal, natural bounded transitions, prior budget failure and zero diagnostic calls for ordinary jobs. Existing final-output/log/scratch/entry, authoring allowlist, network refusal and controller controls remain passing. `git diff --check` passed. Earlier development runs exposed only synthetic fixture mistakes (post-termination clock advancement overwrote the expected reason; a mocked snapshot omitted its trigger); those fixtures were corrected before the passing results. No standalone test log or receipt was saved; output was returned through the tool, and this note records it.

No Windows APIs, Native, GUI, CI, network, installs, downloads, or delegation were executed. No actual008 result or Windows platform qualification exists. Current C4701 zero-initializer correction remains untested on Windows. Main-state/Job-PID observations, cleanup and actual canary controls require a future separately authorized bounded run; child image/exit identity remains outside this diagnostic implementation.
