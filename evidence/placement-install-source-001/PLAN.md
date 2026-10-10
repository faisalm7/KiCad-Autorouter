# Current placement installation qualification — proposed, not executed

Base source binding: `eab7540924b5c8d68263fb68eb4bce6ab9540783`; see `base-bindings.json`. This ignored draft changes only the installation harness, its focused tests and installation documentation when promoted. The lead owns promotion, checkpointing and execution. No tracked source edits, installs, native/engine jobs, network access, spending or global changes occurred in drafting. Pure controls import the draft and project modules.

## What is already established

* Historical installation 001 cloned/setup/doctor correctly but failed 19 runner controls under network denial; native routing was not reached. The old setuid ps monitor caused the failure. The scoped libproc fix preserved network denial.
* Historical installation 002 at `dd2cce9` passed 160 then-current tests, native legacy smoke and strict readback in a fresh local checkout/venv. Its complete receipt and raw logs remain preserved. It does not qualify today's code or placement mode.
* Current production placement has a real owned-fixture success, deliberately invalid native controls and independent byte/receipt audits. The lead also reported a successful full-board production replay. Those are distinct evidence; the next install asks only whether the committed code, full suite and one fixed placement route work after relocation into a fresh clone/venv. It does not need to repeat the larger-board experiment or all native counterfactuals.
* `tests/test_thermal_contract.py` creates a temporary directory inside `ROOT/.runs`. A fresh clone lacks that ignored root. This patch creates it once before the suite, refusing preexisting paths instead of silently repairing an altered test checkout.

## Minimal proposed change

`--guidance native` remains the default and preserves the legacy 120-second smoke command. `--guidance placement-clearance-v1` selects the tracked owned fixture at `evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb`, both adapter corrections, completion-only, fixed default costs 50/5 and existing 20 µm planning margin, with 60-second native wall/CPU ceilings. The receipt must identify that exact source, schema, policy, scope, parameters and commit; the cloned production `check-result` remains authoritative.

The same installation lifecycle makes a clean exact-HEAD local clone using `--no-local --no-hardlinks`, checks all committed source bytes, creates an independent Python 3.11 venv without pip, copies only the verified official engine cache, and runs setup/doctor/full suite/one selected route/readback. All child commands run with network denied. Installed KiCad, Java, bundled pcbnew and base Python are reused: this is not a fresh Mac, download, package or release qualification.

Before/after final canonical receipt publication, recheck original/clone tracked bytes and Git status/HEAD, complete native evidence, original fixture, pinned tools, copied venv executable/config, source-inventory file and command log hashes. Preserve failed/interrupted canonical/partial bytes before correction. Strict readback plus final wall/disk checks can invalidate success; a failed corrective write leaves no canonical success. Final Git checks have separate process/log receipts. Stored totals precede final verification; acceptance caps include it. Total CPU includes parent and waited child/monitor processes, without claiming an installation CPU quota.

## Bounds and preparation

Keep 600 seconds wall, 512 MiB scratch, 10,000 tracked files, 128 MiB tracked bytes, 2 MB per command log and 4 GiB group-memory polling. Keep one heavy worker under the shared experiment lock. Initial metadata was 6,811 tracked files / 97,079,970 bytes; the lead's later staged evidence inventory is 7,591 / 128,306,098, leaving 5,911,630 bytes under 128 MiB before this small patch. Recompute after the actual checkpoint. No cap increase is justified. Check current disk and raw-backup headroom before execution; installed dependency cache copying and Git/venv scratch still count toward 512 MiB and may cause an honest failure.

Do not modify installation 001/002 or any accepted fixture. Use `.runs/installation-003` only if absent. If any fresh-clone test fails, preserve logs and investigate; do not patch that disposable checkout into an apparent success.

## Reproduction after review/promotion

```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .runs/placement-install-plan-001/tests -v
# Lead promotes the patch, runs required checks, audits/publicly checkpoints,
# independently verifies the push, and verifies a clean source checkout.
python3 scripts/install_smoke.py --output .runs/installation-003 --guidance placement-clearance-v1
```

The actual invocation must use Python 3.11. Await completion and inspect every command/final freshness receipt, clone/source HEAD and hashes, native policy/result/code/tool bindings and strict readback. A pass qualifies exactly one local cloned installation of the selected policy. No comparative routing superiority, GUI support, package installation, manufacturing validation or project completion follows.

## Draft validation and limits

20 tiny pure/filesystem tests pass (`tests-007.log`), including one whole-flow test with 13 mocked-command / actual-file scenarios, including post-write signal, partial write, stale source, tampered receipt during final checker, duplicate/nonfinite/Boolean receipt corruption, post-write cap failure, failed corrective write and bootstrap collision/symlink controls. They are harness controls, not installation or native validation. Historical logs remain in this directory. Independent review reproduced a final-check ordering gap in the earlier 17-test draft; that complete version is preserved in `review-snapshot-001`. Seven late file mutations and two late HEAD changes during the last owned Git command could leave its mocked installation accepted. The corrected helper checks all bound material again after the final Git commands and binds the original invoking Python plus bounded HEAD/ref/index witnesses. The whole-flow control now keeps its unchanged positive and rejects eleven file/HEAD/index mutations. This is consistency checking, not atomic authentication against concurrent hostile replacement. A second independent reproduction changed a native receipt after parsing but before evidence capture; the snapshot now precedes parsing and its equality check follows actual result verification. The final independent whole-flow and receipt-capture reruns pass against script `9b02ec5f...`; the reviewer is finishing its bound report. This remains pure mocked-command evidence, not installation qualification. No native job was executed by this agent.
