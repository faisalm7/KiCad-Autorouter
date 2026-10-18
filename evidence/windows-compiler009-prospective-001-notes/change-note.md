# Windows009 prospective compiler-only finalization

Decision: actual008 supplies the previously missing main-exit observation and justifies a narrow trusted compiler completion policy. Implemented prospectively in `scripts/windows_native_slice/windows_process.py`; no009/Windows/Native/GUI/CI execution occurred. Old008 remains failed.

## Actual prerequisite, unchanged

Retained run39138169277 at commit `0399b6dd2c5cd62d8467d1ee35035a1044274891` failed. The exact role1 `/W4 /WX` MSVC14.44.35207/SDK10.0.26100.0 compiler main PID3640 was observed signaled with exit0 at6.265 seconds. The same Job snapshot listed PID6840 and continued to list it at30.015 seconds. No child image identity was observed. Job status was `budget_exceeded`, exit0,30.047 seconds wall,1.125 full Job CPU seconds,cumulative4 processes, verified cleanup true. The compile log contained `appcontainer_probe.c` and no C4701 diagnostic. This establishes compiler-main success with an owned member remaining, not the image or function of that member. The provider reports46 seconds whole run duration and zero billable timing; whole CI CPU remains unknown. `dispatch.json` is the historical in-progress readback; completed failure is established by `run.json` and the CI log.

| Inspected actual path | SHA-256 |
| --- | --- |
| `.runs/windows-setup008-actual001/CI.log` | `f792c3c4822c9e92552c63fdd78dd66f26250cd11c1677e4331c59f9a97d59c5` |
| `.runs/windows-setup008-actual001/run.json` | `440fb485ab4509b6bef9fa7711875348e474b23a75167574055ad9f0c3e5731b` |
| `.runs/windows-setup008-actual001/timing.json` | `37a126b3b79825d7a7d46631e945345af46f2cc0be7ee6dc29091cb60ee435ba` |
| `.runs/windows-setup008-actual001/dispatch.json` | `10376ec1e742db89838af09c7251befa760ae57f42f1d424e2028d78e3da84cd` |

## Implemented boundary

`run_owned_setup` passes the actual `_setup_argv` authoring contract into the private Job lifecycle. Finalization requires its exact `fixed-owned-C-canary-build` kind and integer role1/2, owned setup and no AppContainer guard. `owned_setup=True` alone, DNS, unknown kind, boolean/unknown role, and ordinary public `run` cannot select compiler finalization. Existing exact compiler arguments/source/tool pins, fresh owned paths and protected-input handles remain in force.

Only an observed main exit0 with no prior failure or unknown observation can select finalization. The runner rechecks original wall/full-Job-CPU, cancellation, log, scratch and entry limits after diagnostic collection, including elapsed time/cancellation after directory accounting. It requests termination of only its own Job remainder and then continues the original polling, final zero-active verification, CPU accounting and `finally` handle/Job cleanup. Any later limit or cleanup failure still fails. Main nonzero, timeout, cancellation, diagnostic unknown and failed termination never become success. The unchanged30-second Job cap and original2GiB memory/256KiB log/128MiB scratch/4000-entry limits remain in place; no warning suppression or global setting changed.

The receipt explicitly records the policy, compiler role, observed main exit, bounded non-atomic member snapshot, termination request/API success, termination code130 and zero-active verification. It disclaims natural completion of the remaining members. Member images and individual child exit identities remain unobserved; no child PID is opened. A PID snapshot is not an atomic proof that each listed PID was killed. The existing diagnostic receipt marks the changed completion semantics only if this finalization path actually ran.

After `_run_job` has returned through successful reaping and its original `finally`, and only for a successful compiler setup, the exact fresh `probe-parent.exe`/`probe-child.exe` is validated under the existing write/delete-sharing-denied file guard. The cap is4MiB. Regular/canonical/single-link/no-reparse checks remain through existing helpers; DOS/PE headers must identify an AMD64 PE32+ executable, not a DLL. Output is hashed with file identity. Missing/unsafe/oversized/invalid output returns a failed setup status with diagnostic details. This is limited header/build-output validation; actual canary execution remains necessary. DNS/ordinary Native/AppContainer completion and cleanup contracts are unchanged. Setup `accepted`, product support and Native admission/execution remain false.

## Changed files and validation

| Changed source/test | Before SHA-256 | Final SHA-256 |
| --- | --- | --- |
| `scripts/windows_native_slice/windows_process.py` | `274b24537b259774a9f6004211104b6cc4aefa86e4c65ac9122741052ea66fd1` | `8d61277d1db5cc9d4e4c7ffb98a745d13fe55953d44531bdaaadcbc9b39cbb6d` |
| `tests/test_windows_probe_controls.py` | `70b48ca94e930d609f37c710cacc445e3ad4933b8e8bcf782e235071eded5451` | `407516121c73753a30a31a87bfb4ce18ba79f65a446a6fb06f68e68236f1bc35` |

Exact targeted command, invoked through a bounded30-second Python subprocess and captured unmodified to fresh logs:

```sh
.venv/bin/python -B -m unittest tests.test_windows_probe_controls tests.test_windows_firewall_diagnostics tests.test_windows_isolation_diagnostic
```

- `.runs/windows009-compiler-finalization-001-tests-001.log`:35 tests in0.578 seconds,34 passed/1 PowerShell skip; SHA-256 `00b9ea564ecfdef56f4c47cbf23bb8dac31c58cad141a29b8e24a6d4887c29cc`.
- `.runs/windows009-compiler-finalization-001-tests-002.log`: final36 tests in0.624 seconds,35 passed/1 PowerShell skip; SHA-256 `f479dbedef6ad8cce3beaeccc8ec22eaf1bb37790f93a6479547563a93c0085e`.

The second run followed the4MiB alignment and an added retained-finally cleanup-failure control. Controls cover exact authoring kind/typed roles, main-zero finalization, nonzero/running/unknown states, failed snapshots/termination, concurrent deadlines/cancellation, other bounds, post-reaping output-read order, malformed/oversized/missing PE output, DNS/ordinary behavior and cleanup failure overriding a pending success. `git diff --check` passed. These are synthetic API/control tests on Mac, not Windows proof. No workflow/protocol/version/source-board changes, network, installer, CI dispatch, Native, GUI or delegation occurred. Parent review and a separately authorized bounded actual009 remain pending; no Windows platform or all-network admission is established.
