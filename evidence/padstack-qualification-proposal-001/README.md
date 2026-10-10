# Padstack warning qualification — draft, no native run yet

Scope: three small real native diagnostic controls before any production gate
widening. This independent AI source review does not establish native correctness,
human PCB approval, source-board DRC cleanliness, or a completed routing task.
Only this ignored directory was written. No download, router or KiCad process ran.

## Exact source distinction

All sources were already present in `../support-scope-review-001/source/`; their
pinned URL/hash inventory is `../support-scope-review-001/source-receipt.json`.
The official KiCad 10.0.0 tag resolves to
`0feeca2a807f428ad2b3fa7c1e39625cb769f02c`.

- [drc_item.cpp lines 144–150](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_item.cpp#L144)
  defines distinct stable report types `padstack` (questionable) and
  `padstack_invalid` (invalid). [Lines 383–401](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_item.cpp#L383)
  put only the latter in the internal group with no user-editable severity.
- [board_design_settings.cpp lines 167–183](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/board_design_settings.cpp#L167)
  initializes errors, then specifically makes `padstack` a warning. The project
  setting is legitimate native behavior, not evidence the check was disabled.
- [drc_engine.cpp lines 890–900](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_engine.cpp#L890)
  assigns zero error limit only to ignored checks. [footprint checks lines 87–103](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_test_provider_footprint_checks.cpp#L87)
  runs pad checks and forwards each returned code unless that code is disabled.
- [pad.cpp lines 2870–2891](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pad.cpp#L2870)
  predicts `padstack_invalid` for an SMD hole and `padstack` for front copper with
  back paste. The wording of `padstack` is not a sufficient safety classifier:
  [line 2961](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pad.cpp#L2961)
  also uses it for a PTH hole leaving no copper. Conservatively reject every
  occurrence; do not whitelist by translated description.
- [rc_json_schema.h](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/include/rc_json_schema.h)
  specifies finding `type`, `severity`, `items`, and optional `excluded: true`.
  Preserve original warning severities and descriptions. The production parser
  already counts the native boolean exclusion flag; this is not a new defect.

## Minimal controls ready for lead execution

`probe.py` derives three new one-pad boards from the project's original GPL smoke
fixture. It removes all other pads, nets, routes and zones while creating these
new diagnostic inputs; it never edits the fixture. All three retain the same
closed outline, ordinary 2 mm square front SMD pad, and no connectivity demand.
This deliberately isolates pad validity. No claim of meaningful routing follows.

Each board is paired with the **entire byte-identical original multichannel
`.kicad_pro`**, including every minimum, severity, netclass setting and exclusion
list. The script pins its existing SHA-256 and refuses a new `.kicad_dru` instead
of silently omitting it. These are owned diagnostic board geometries under real
unchanged source settings, not modified copies of multichannel copper.

| Control | Newly created input | Required actual evidence |
|---|---|---|
| positive | F.Cu/F.Mask/F.Paste; no hole | Zero errors, opens, exclusions or policy-critical findings; all ordinary warnings retained |
| wrong_paste | Only paste changes to B.Paste | Exact target pad UUID in native `padstack` **warning**, zero native errors/opens/exclusions, explicit policy rejection |
| smd_hole | Front layers, 0.8 mm hole | Exact target UUID in native `padstack_invalid` **error**, explicit rejection |

The invalid input is itself the immutable source for its control. A changed-pad
invariant rejection cannot substitute for the required actual warning. If the
native loader normalizes the hole or a different error masks the warning, that
control fails; inspect raw results instead of treating predicted source behavior
as observed. The wrong-paste check explicitly requires zero native errors.

Lead command, **not executed by this agent** (ordinary host Python 3.11+):

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' python3 .runs/padstack-qualification-draft-001/probe.py --out .runs/padstack-native-controls-001
```

One shared 120-second native Job bounds all three DRC commands. Each actual CLI
invocation uses the pinned KiCad 10.0.0 binary, isolated settings,
`--severity-all --all-track-errors --refill-zones --exit-code-violations --format json`.
It validates an exact scratch copy, verifies unchanged project/board hashes,
retains raw reports, process status/log, input/report binding, target pad UUID,
warning counts, policy findings and tool/code manifest. Existing output refuses
collision; nothing is removed. This is a diagnostic budget, not a quality
comparison. `routing_accepted` remains false even if all three controls pass.

## Proposed production change, only after those controls

1. Preflight may admit only original `padstack: warning` in addition to error.
   Keep `padstack: ignore`, every other unsupported critical severity, exclusions,
   custom rules, unknown keys and advanced padstacks gated. Do not treat
   `padstack_invalid` as a newly editable project setting merely because it is a
   known native finding type: use separate setting-key and finding-type sets.
2. Add a separate policy-critical finding count/list to the report summary.
   Reject `padstack` and `padstack_invalid` regardless of warning/error severity;
   conservatively cover other established critical finding types as well.
   Preserve `blocking` as actual native errors and `warnings` as actual native
   warnings. Never rewrite the raw report. Require all severities and no disabled
   required check. `excluded: true` remains independently rejecting.
3. Wire one shared acceptance predicate into refill/final validation,
   `check_result`, strategies, benchmark eligibility and handoff. A preflight-only
   exception is unsafe with today's parser: it counts warning findings but does
   not independently reject critical warning types. Native receipt rechecking
   must reproduce policy counts from the retained bound report; no trusted JSON
   summary fields. Preserve old receipts, version new evidence.
4. Supplement real controls with lightweight malformed/stale report and
   missing-warning/ignored/excluded controls. Then natively audit a scratch copy
   of the unchanged original multichannel board. That audit is not routing and
   must retain preexisting failures. No corpus support claim before further gates.

## Independent next gate: multichannel target/floor mismatch

Original preferred width/clearance/via diameter/drill are 0.2/0.2/0.6/0.3 mm.
Original board minima include width/clearance 0.3/0.3 mm, via diameter 1.5 mm,
annular width 0.3 mm, and through-hole drill 0.3 mm. This mismatch is separate from
padstack severity. Today's Default-only path does not invoke the strict new
literal-netclass auditor, so passing static preflight does not certify export.

Pinned [DSN export lines 1169–1184](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/specctra_import_export/specctra_export.cpp#L1169)
uses Default targets directly, including a smaller `smd_smd` clearance exception.
[Lines 1547–1549](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/specctra_import_export/specctra_export.cpp#L1547)
and [1747–1768](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/specctra_import_export/specctra_export.cpp#L1747)
use original class width/clearance and via dimensions, not a blanket maximum with
board minima. Actual native export for this board has not been run in this task.

A future B1 adapter can derive scratch DSN guidance with width and clearance
`max(preferred, original minimum)`, drill `max(preferred drill, drill minimum)`,
and via diameter `max(preferred diameter, minimum diameter, drill + 2*minimum
annular width)`. For these settings that gives 0.3/0.3/1.5/0.3 mm. Audit *all*
applicable DSN rule scopes and padstack definitions, including lower `smd_smd`
overrides, so a narrower exception cannot undermine the floor. Do not rewrite the
original project; final native DRC remains authoritative for all unmodeled rules.
This is corrected-adapter work common to B1/B2/C, not C novelty. Qualify exported
effective values and real below-floor native counterexamples before routing.

No production patch is included. Native outcomes remain pending.
