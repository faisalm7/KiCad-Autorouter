# Receipt, setup, and evidence follow-up review

Reviewed October 9, 2026, in the local Mac project. This is an AI review of
filesystem behavior and stored experimental artifacts. No routing engine or
native KiCad command was executed by this reviewer during the lead's sequential
adapter experiment or the separate KRT experiment.

## Reproduced findings and fixes

| Finding | Risk | Verification |
|---|---|---|
| `check_result` accepted a candidate directory replaced by a symlink outside its run. Ownership was checked lexically, and the tree hasher followed a symlink at its root. | P1 applicability boundary | Actual filesystem reproduction failed the initial test. The lead added root-symlink rejection and resolved ownership checking. Independent rerun: all 12 receipt tests passed. |
| Engine setup followed a `.tools` directory symlink and wrote outside the intended destination. | P1 setup boundary | Reproduced with a tiny in-memory download and reviewer-owned scratch directories. The lead's symlink check now refuses it; the outside directory remains untouched. |
| Engine setup's final `os.replace` overwrote a destination created while the download was in progress. | P1 data preservation | Reproduced with a controlled competing file. The lead switched publication to exclusive `os.link`; the repeat refuses publication and preserves the competing file. |

The receipt suite at `tests/test_result.py` exercises real file edits: changed
source boards/rules, newly added rule files, changed candidate files, changed or
missing native reports, malformed report content, a report containing a blocking
finding, failed receipts, and candidate paths outside the run. Its consistent
synthetic receipt is only a test of receipt checks; it does not represent a native
DRC success. The checks do not apply anything to a live editor.

Run the repeatable receipt controls:

```sh
python3 -m unittest discover -s tests -p test_result.py -v
```

The independent fixed run completed all 12 tests in 0.034 seconds. Evidence is in
`.runs/review-followup-001/result-tests-initial.log` and
`result-tests-fixed.log`. The setup controls and their before/after receipts are
`setup-reproduce.py`, `setup-results.json`, and `setup-results-fixed.json` in the
same directory. The fixed setup source SHA256 was
`d5c46b6f0c39751887ae6da09290294be43a5f0824283fbcc36ea26d05d8a5dc`.
Reviewer-created symlinks were removed after recording their targets in
`test-symlink-cleanup.json`; target files were preserved. No unrelated data was
changed.

Receipt hashes detect stale files and inconsistent reports. They are not a
cryptographic signature, an independent rerun of DRC, or protection against a
person deliberately rewriting both a receipt and every claimed artifact.

## Frozen adapter experiment audit

The reviewer independently checked all five arms of
`.runs/adapter-ablation-001`. Every protocol implementation hash matches Git
commit `7fef4675006bc35e59c1dc566b9cff07f2dbd5d9`. Every arm's saved code and
receipt implementation manifest matches that protocol. Source inventories match;
candidate and native-report hashes match the actual files; CPU totals equal
parent plus worker plus monitor CPU; and every arm has the declared 120-second
budget. The audit is `.runs/review-followup-001/ablation-binding-audit.json`.

| Arm | Native opens | Blocking findings | Warnings | Routing accepted |
|---|---:|---:|---:|---|
| Stock A | 3 | 7 | 1 | No |
| Graphics correction | 3 | 0 | 1 | No |
| Plane correction | 0 | 3 | 1 | No |
| Combined adapter | 0 | 0 | 1 | Yes |
| Stock B | 3 | 7 | 1 | No |

These stored results support an adapter recovery on one exposed development
family, consistent with the individual failure mechanisms. They do not establish
a new strategy C, an improvement beyond B1/B2, a generalized completion rate, a
speedup, or a whole-project clean result. The combined candidate still has one
warning. Its 786.315536 mm of tracks and three vias compare with 566.453919 mm and
four vias for invalid stock candidates, so this is not a quality comparison among
equally valid outputs. The fixed arm order also does not establish independent
timing uncertainty. No tuned equal-budget B2 result is part of this experiment.

The earlier public `smoke-stock-004` and `sonde-stock-002` records retain useful
native findings but lack per-run code snapshots. Four implementation-file hashes
in each differ from the frozen commit. Those earlier records are provisional
development evidence, not fully reproducible frozen-code claims. The audit is
`early-evidence-audit.json`; use the new pinned ablation for the adapter claim.

## Publication audit and remaining limits

The reviewer scanned 104 tracked files at the frozen checkpoint and manually
checked the only credential-pattern match. It was a 27-byte private-key header
literal in a negative backup test, with no private-key body. No tracked binary,
downloaded engine, bulk dataset, `.local-reference`, `.private`, `.runs`, `.tools`,
or `.local-backups` file was found. This is a scoped pattern/manual audit, not a
guarantee that arbitrary secrets can never appear in future changes.

Thirty-four tracked files contain absolute local project or installed-tool paths.
They reveal the local account name; the reviewed paths do not identify private
board inputs. Public evidence therefore must not be described as path-free.
The scan and manual resolution are in `publication-audit-reviewed.json`. Newly
staged files and history still require the lead's publication audit before each
push. The review did not authenticate GitHub, push commits, alter repository
settings, or publish a release.

Fresh native positive/negative reruns by this reviewer, GUI qualification, an
independent human PCB review, physical validation, broad licensed-family coverage,
and a strategy improving beyond the adapter remain outside this follow-up's
completed work. The local `.runs` review receipts require the normal separate
backup process; paths alone are not backups.
