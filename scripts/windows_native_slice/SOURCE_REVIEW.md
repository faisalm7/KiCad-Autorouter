# Windows substrate draft: narrow source review

2026-10-16 UTC, started08:55:59; final source clock08:57:48 (109seconds), plus note/communication tail. Review CPU unmeasured. No imports, compilation, tests, Windows/Native/JVM/CI execution, network, Git mutations or delegation. Only this note written. Reviewed README, all six proposed sources/workflow/pins and relevant current pure factory/adapter/native imports. This is not an observed Windows capability or launch qualification.

## Concrete findings

1. **Final resource checks can be skipped.** `windows_process.py:58–68` queries accounting and immediately breaks at ActiveProcesses==0, before log/scratch/entry checks. A fast child can create>256KiB log or>128MiB scratch/>4000entries and exit between polls; return74 still says success and advertises those limits. Check complete final output bounds before the inactive break and before successful return. Lead accepted this minimal correction; it was not yet in reviewed3eb3b671 source. A meaningful control is a quick owned child that writes beyond each final limit and exits0; no Native needed.

2. **Live firewall predicate admits unrelated/inapplicable rules.** `slice.py:16–19` accepts any enabled ActiveStore block matching program and direction. An existing Domain-only block can pass while the active interface is Public, if the bootstrap Any rule disappears; scoped protocol/address/port/service rules also do not prove universal outbound/inbound block. Bootstrap creates its own Any-profile rules, but their exact identities/scopes are not passed to the worker or required on final replay. Lead will freeze the owned inbound/outbound names, exact program/ProfileAny/protocol/all-address/all-port/service scopes and require the same actual ActiveStore rules before/after. No enabling firewall or global protection change is needed. Actual hosted firewall/admin availability remains an honest early gate.

3. **Cancellation classification needs130.** Initially read slice dbfdbdda allowed late error/KeyboardInterrupt after native_transport_observed=True to preserve that flag and exit0. Refreshed final bcd6ee16456858c483aea1a3338a182178f4bd8a145d96f96d1b8e5140e64618 now clears it and latches cancelled, closing false completion, but final89 still exits2 for cancellation. Lead accepted terminal130 before ordinary2. Preserve the flag even if subsequent publication fails; ordinary negative/control errors stay2. This is a source-path finding, not an actual cancellation observation.

4. **Original report is discarded, not fully retained.** `slice.py:83–85` prints owned candidate/final Native/disconnect Native, while bootstrap42 deletes the entire scratch. Original Native report survives only as a hash and counts in step/result metadata. Its full findings/ignored array/open-item identity cannot subsequently be inspected or replayed. Add original-drc.json to the same bounded owned-payload projection if reporting an original/fullSCH transport observation. Keep overflow a truthful failure, not silent truncation. Exported class/SES proof currently also stays ephemeral; retain them if the future claim depends on independent replay of those transforms.

The first three findings were sent promptly and accepted by lead as narrow corrections. They are planned corrections, not source-verified applied fixes in this note. Do not label this draft launch-qualified before those exact changes are tested/reviewed by lead.

## Scope that is appropriately closed

- Official installer exact968953784B/SHA/Authenticode signer/issuer/serial are required before execution, with a fresh RunnerTemp application target, documented ephemeral registry/shortcut effects and15-minute standard-runner envelope. No extra/private boards or global Mac changes are involved. Setup is online-capable; normal Native/Java work has a separate live-deny gate. No fallback Python/Java ABI guess is offered. Lack of expected bin/python.exe or exactJava25.0.2 truthfully stops the attempt.
- Win32 signatures and x64 Job Object/accounting structure declarations appear consistent on source inspection; this does not establish actual ABI, nested-job permission, handle inheritance or cleanup. CreateProcess is suspended before assignment and resumed only afterward; kill-on-close/no-breakaway and per-job memory are explicit. Failure before assignment terminates the suspended direct child. Actual positive/cancel/error controls remain required.
- Source/PRO/SCH/PRL use read-only sharing handles, file identity and unique-link/reparse checks; incompatible Native sharing must refuse. Original PCB shell plus locked KEEP is retained and only new ROUTE/derived filled-zone polygons transplanted; final Native0/0, unchanged full warning records and deliberate disconnect are required. Original rules are not edited. The freshly authored fixture has one original locked segment, so the explicit segment-preservation check matches this deliberately narrow owned fixture; it is not a generic arbitrary-arc/via protection proof.
- Source/fixture and native_worker avoid pipeline/resource/fcntl imports on inspected paths. Native.netclasses only imports the scalar class observer at module scope. This inspection does not prove Windows imports/pcbnew ABI.
- Every result remains accepted=False/product_support=False/passed=False/whole_cpu_qualification=False. PowerShell query/setup/controller CPU and final process-exit publication are explicitly incomplete. Child-job CPU is not whole setup/CI CPU. A successful command may report only the owned partial substrate observation, not Windows product support, GUI operation, original-board admission or route quality.
- `HttpClient.Timeout` with ResponseHeadersRead is not a complete body-read deadline: synchronous stream.Read can wait beyond the declared three-minute client timeout. The15-minute CI job is the actual outer bound; retain that distinction or use the already-existing metadata probe's cancellation-token reads if a strict per-download deadline is claimed. This need not be expanded into a new installer framework.

## Reviewed pins

```
slice.py bcd6ee16456858c483aea1a3338a182178f4bd8a145d96f96d1b8e5140e64618
windows_process.py 3eb3b6710055a79f0e2c6ee93baf3f5b8d9f629961f95177404ab67ba10a6bcc
bootstrap.ps1 efd509cfaea2b9615f3413879bac7480cf7146ecb0bfbf9bda9950116f413e3f
native_worker.py b3e8674f9649453b95de3931d895fa0ce55cd6798d8943f3d058993694e506be
workflow.yml 860272997803d6fc1d4b98d4e6c06ee4493af9eb2828116371c398e0d0e36be6
```
