# Initial adversarial acceptance review

Reviewed October 9, 2026, in the selected local Mac checkout. This is an AI
implementation review, not independent human PCB review, native qualification,
or evidence of improved routing. The reviewer did not edit `pipeline.py` or
`sexpr.py` and did not run an engine or native KiCad concurrently with the lead.

The review targeted false acceptance, changed project rules, protected copper,
malformed reports, unknown constraints, and replacement of existing evidence.
Its checks are in `tests/test_validation.py`. Native controls remain a separate
required gate.

## Findings and their evidence

| Finding | Severity | Observed status |
|---|---|---|
| Malformed ignored-check records can be treated as a clean report. An absent, null, or numeric `key` survived `parse_report`; the returned counts were zero. | P1 acceptance integrity | Reproduced, fixed by lead, and reviewer regression rerun passed. |
| An unknown disabled check such as `future_unqualified_constraint` survived report parsing, so unknown validation semantics did not fail closed. | P1 acceptance integrity | Reproduced, fixed by lead with a known-check allowlist, and reviewer regression rerun passed. |
| Candidate integrity originally compared only source-listed files, before final validation. That misses newly added rule files and changes after that check. | P1 acceptance integrity | Identified by inspection. Lead fixed before fault-injection execution; added `.kicad_dru` and late `.kicad_pro` changes now reject in the exercised revision. No claim that the original implementation was executed. |
| Required-check list originally omitted hole clearance checks. | P1 acceptance coverage | Identified by inspection. Lead expanded the list before the exercised reproduction; disabled `hole_clearance` now rejects in preflight and report parsing. |
| Run records identified native tools but initially lacked implementation file hashes / Git revision information. | P2 reproducibility | Fixed by lead: new records include every `autorouter/*.py` hash and Git HEAD. Those hashes identify uncommitted implementation content; Git HEAD alone does not. Old records are not retroactively upgraded. |

The malformed string ignored-check case raises `AttributeError`; the top-level
pipeline catches it and rejects, so that particular shape does **not** create a
false pass. The regression test nevertheless requires an explicit validation
rejection instead of an accidental exception.

The implemented policy for intentionally disabled, non-routing checks uses a
known-check allowlist. Rejecting an unknown check should not require enabling unrelated
courtyard or library checks that are deliberately disabled by the preserved
project. Unknown fields in the board must remain preserved; this is distinct
from asserting that an unknown disabled validator check is safe.

## What was actually exercised

The fault-injection script at
`.runs/review-20261009-acceptance/reproduce.py` replaces every native stage. Its
purpose is to attack control flow and integrity checks, **not** to present a
mock native pass as valid routing. Its `results.json` records pipeline SHA256
`2114a8fa322a86f41c876f0f6a4a724eadd0950e3fecaa94793cd55593912e46`
and S-expression implementation SHA256
`c65b209def530fab9ca1481c67ed2d8217a294b73df8e5e41458e269f917b6dd`.
The inert injected control reached acceptance; added rule files, late rule-file
mutation, and removed protected tracks were rejected. Malformed and unknown
ignored-check entries were accepted by the report parser.

The structural review at `.runs/review-20261009-structural/results.json` records
pipeline SHA256
`f873fbc2629881e14af74c140af2ee8b9ee48cc70cdca8524443361ef33d2dcd`.
It verified preservation of unknown fields and quoted Unicode/escape content;
rejection of truncated, multiple-root, excessively nested, and malformed
S-expressions; rejection of project symlinks; and preservation of existing output
evidence. No data-loss behavior was observed in those controls.

The first durable regression run is
`.runs/review-20261009-acceptance/validation-test-log.txt`: 16 tests ran, with four
failing subcases and one error, all in the two known ignored-check parser tests.
Other tests rejected changed pad geometry, terminal nets, footprint position,
board outline, zones, unknown fields, protected tracks, project rules, stale
candidate hashes, and pre-existing output directories before any native call.

After the lead's parser fix, the reviewer reran all 16 controls: all passed in
0.013 seconds. The fresh log is
`.runs/review-20261009-acceptance/validation-test-log-fixed.txt`, for pipeline
SHA256 `2e2b29fccb26b07a601dae187a9f7aec19dd1c922e48c551d90bd0fc6f234723`.

The reviewer also inspected the lead's actual `sonde-stock-002` artifacts without
executing a second native run. The original and emitted candidate retain format
`20241229`; KiCad 10's disposable refill uses `20260206`. The emitted candidate
preserves original zone intent and legacy `filled_areas_thickness` metadata,
transfers eight derived fill objects, and is byte-identical to the final DRC
input copy. Structural immutable trees match. The recorded actual native result
is correctly rejected with three opens, seven blocking findings, and one warning.
This inspection finds no concrete transplant defect on that board; it does not
qualify the mixed-version serialization for other boards or KiCad 9. The evidence
is `.runs/review-20261009-acceptance/cross-version-summary.json` and the lead's
`.runs/sonde-stock-002/result.json`.

These `.runs` receipts are local artifacts, excluded from Git. They require the
project's separate evidence backup; their paths alone are not backups.

## Reproduction and remaining review scope

Run the preserved acceptance-boundary tests from the repository root:

```sh
python3 -m unittest discover -s tests -p test_validation.py -v
```

The receipt-generating one-shot scratch scripts deliberately refuse to overwrite
their case directories. Use a new `.runs/review-*` directory when repeating them;
the tracked regression tests are the normal repeatable entry point.

Native positive/negative control execution, actual zone refill execution, current
rule-exit-code experiments, GUI operation, source licenses, and restored-install
qualification were outside this review's execution scope. The lead must finish
those checks; the reviewer has inspected one real failed run's artifacts and
obtained the passing regression rerun described above. There is no
claim of final release readiness or comparative routing improvement.
