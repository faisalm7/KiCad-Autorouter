# Shared native acceptance policy proposal

Ignored draft only. No production file, source project, archived result, native
binary or engine was edited or executed by this task. The lead owns integration.

`policy.patch` is ready against the file hashes in `base.json`; `git apply --check`
passed. `patch-manifest.json` binds the patch and confirms the `parse_report`
function's AST is unchanged. The unmodified native dictionary remains:
`opens`, `blocking`, `warnings`, `exclusions`, `ignored_checks`, `findings`.

## Proposed behavior

- Preflight permits original `padstack: warning` or `error`, without rewriting
  project settings. `ignore`, every other unqualified critical warning/ignore,
  unknown keys, exclusions, custom rules and unsupported geometry remain gated.
- `native_rejection_reasons()` and `native_accepted()` are the one shared policy.
  They reject malformed/missing summary data, disabled critical checks, actual
  errors, exclusions, opens, and any critical finding regardless of its native
  severity. Raw warnings remain warnings. Finding type `padstack_invalid` is
  critical but is **not** added as an editable project-severity key.
- Route acceptance, receipt readback and strategy trial/final acceptance use
  that policy. Rejection reasons are separate receipt fields; native counts and
  findings are untouched. `drc_rejected` denotes the application refusing the
  native findings, not a claim that a warning became a native error.
- Native diagnostic controls, thermal-bridge diagnostic acceptance, and both
  raw/adapted KRT spike acceptance use the same helper on future executions.
  The padstack control retains its exact expected-type/UUID checks, while its
  policy result delegates to the shared helper. Frozen historical scripts and
  reports remain unchanged.

No DSN floor, netclass dimension or source-rule changes are included.

## Acceptance path audit

| Path | Policy entry / disposition |
|---|---|
| B0/B1/B2/completion-only route | `pipeline.route` → shared helper |
| C deletion trial and final | `strategy._valid` → shared helper |
| C incumbent | `route` plus actual `check_result` |
| Receipt readback / CLI | `pipeline.check_result` reparses hash-bound raw report, then shared helper |
| Manual review copy | Both existing `handoff.review_copy` checks call `check_result`; no copied files on initial rejection |
| Quality B2 and paired C | `quality.summarize` calls actual `check_result` before eligibility |
| Portfolio ranking and selection | `portfolio.verify_row` calls actual `check_result` |
| Paired B2 frontier | `paired.verify_portfolio` checks every eligible row through `verify_row` |
| Native validation worker | `validate_candidate` returns diagnostic raw findings, including rejected ones; callers enforce acceptance |
| Source DRC / thermal negative control | Observation/expected-failure checks, not candidate acceptance; kept unchanged |
| Netclass auditor | Mapping validation only, explicitly `routing_accepted: false`; no DRC acceptance path |

This design preserves rejected candidate evidence. It does not make the native
report parser throw merely because a validly formed report contains a warning.

## Verification performed

`focused-tests.log` records **111 passing controls**, including **13 new tests**.
These are pure, filesystem, or mocked-stage controls. They do not establish new
native routing correctness. The original first staged run had 110 passing tests
and one missing-public-fixture error; its log is retained with the
`.staging-missing-fixture` suffix. Copying that existing raw report into the
ignored stage fixed the test environment; no production test was weakened.

The new tests exercise unchanged parser shape/native counts; warning-only
preflight exception; missing/malformed helper inputs; required-check suppression;
ordinary warning acceptance; consistently rehashed fraudulent accepted receipts;
handoff rejection before copying; quality/paired C rejection; portfolio selection
and paired frontier rejection. These paths use the real filesystem readback
function, not a mocked `check_result`. One existing strategy feedback fixture was
completed with its missing warning/ignored metadata; the helper does not default
missing evidence to clean.

`archived-summary-compatibility.json` records actual equality against retained
native summaries from the adapter combined result and all padstack001/002 cases.
No result was relabelled or altered. In particular, the failed SMD-hole001 recipe
still has an empty native report. The report-only helper cannot recover fields
that native loading discarded; this draft does not claim that all malformed
serialized padstacks have been independently screened. A future structural
guard may reject nonzero SMD/CONN drill tokens explicitly as a separate scope.

Lead-run padstack002 is actual native support for this narrow change: clean
positive, exact target-UUID `padstack` **warning** with zero native errors/opens/
exclusions, and target-UUID `padstack_invalid` **error** on a PTH 1 nm hole with
the independent `drill_out_of_range` error also retained. The lead reports this
was a frozen diagnostic script delta on dcb0a44, not a clean-code benchmark.
The failed run001 remains available; neither run establishes route completion.

Rerun after integration with the native lane assigned by the lead: focused/full
tests, a fresh actual native diagnostic control/smoke, then any separately gated
whole-board experiment. None is performed automatically by this draft.

## Exact primary sources and license provenance

All links pin KiCad 10.0.0 commit
`0feeca2a807f428ad2b3fa7c1e39625cb769f02c`. Previously acquired source files and
hashes remain in `../support-scope-review-001/source-receipt.json`.

The loader diagnosis uses
[pcb_io_kicad_sexpr_parser.cpp lines 5487–5494](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L5487):
after reading a drill token, SMD/CONN attributes force the hole dimensions to
zero. PTH preserves its parsed dimensions. [Lines 185–197](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L185)
convert millimetres to internal units; [lines 5335–5341](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp#L5335)
also deliberately initialize PTH with a 1 nm fallback drill. Its header identifies
GPL-2.0-or-later and CERN/KiCad developers. This file was read through the web tool;
no source payload was copied into the patch or downloaded into this draft.

[pad.cpp lines 2933–2940](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pad.cpp#L2933)
reports `padstack_invalid` for a positive drill no larger than 4 internal units;
the retained source header is GPL-2.0-or-later. This explains the replacement
control without disguising its additional ordinary drill-size error.

[drc_item.cpp lines 144–150](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_item.cpp#L144)
distinguishes the report types, and [lines 396–401](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_item.cpp#L396)
lists the invalid variant as having no editable severity. The retained header is
GPL-2.0-or-later. [board_design_settings.cpp lines 167–183](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/board_design_settings.cpp#L167)
sets ordinary padstack to warning by default; its retained header is
GPL-2.0-or-later. These are source-based explanations, not imported third-party
implementation code. Native002 is the separate actual behavioral evidence.
