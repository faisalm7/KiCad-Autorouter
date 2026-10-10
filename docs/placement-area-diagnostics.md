# Placement areas and pinned native keepout limits

The current production router rejects board and footprint rule areas with any
prohibition, or missing/unknown/duplicate prohibition flags. KiCad10.0.0 did not
report the deliberate track/via violations in the actual controls below.
Preserving an engine obstacle cannot replace an independent constraint check.
`pipeline.check_rule_area_support` runs at preflight and candidate validation;
receipt readback also repeats preflight. Original boards/rules are never edited
to enter this narrower scope. Ordinary copper zones and areas with all five
flags explicitly `allowed` remain eligible for the other existing gates.

## Actual control result

At `fdf499d8c45c281fa2f85c13e2d5930cc7427523`, four owned fixtures derived
from the accepted floor fixture were exported and checked by pinned native
KiCad, using original project rules. Each fixture only adds declared diagnostic
areas; all original geometry/routes/project bytes remain intact.

| Case | Same-load native/DSN observation | Actual DRC | Control |
|---|---|---|---|
| All-allowed placement | Five false native prohibition flags; two generic keepouts | No findings | Passed export-mismatch observation |
| Prohibited track | Track flag true; two wire keepouts; actual track crosses area | No findings | Failed expected violation |
| Prohibited via | Via flag true; two via keepouts; actual via inside area | No findings | Failed expected violation |
| Mixed | All six exact exported entries, all flags retained | No findings | Failed expected violations |

The overall suite **failed** and remains `controls_passed: false`.
Stored time was6.785365541wall /4.759377CPU seconds under shared60secondcaps.
No engine or selective DSN transformation ran. Raw subset:
[`placement-area-native-001`](../evidence/placement-area-native-001/summary.json).
An independent offline audit verified47 bindings; that does not turn the native
negative controls into passes. The audit also applied the pure transform to
actual observations: the allowed case removes two entries; prohibited-only
cases reject as ineligible, and overlapping mixed areas reject as ambiguous.
This is not a routed candidate or production placement-policy qualification.

## Source explanation and limits

Pinned source is KiCad10.0.0 commit
`0feeca2a807f428ad2b3fa7c1e39625cb769f02c`; installed binary hashes are separately
pinned and are not a reproducible-build proof. The exporter emits generic
keepouts even when neither tracks nor vias are prohibited. Source tracing also
provides a plausible explanation for the native omissions: the disallow
provider skips implicit-rule reports in its general path; its separate track
index uses a zone's effective filled shape, which can be empty for a rule area.
The track-only indexed path cannot independently rescue the via check.
This is a source-based explanation of the observed10.0.0 workflow, not a claim
about every KiCad version or an upstream-confirmed defect. The actual no-placement
counterfactual002 subsequently reproduced the omission for all three cases:
removing only disabled placement nodes left the prohibited flags, geometry and
project intact, yet every report still had zero findings. Stored4.873878583wall
/3.710146CPU seconds stayed within shared60secondcaps. Its omission controls
pass; constraint qualification explicitly remains false. See
[`native002`](../evidence/placement-area-native-002/summary.json).

Primary files and exact retained hashes are listed in
[`diagnosis-sources.json`](../evidence/review-placement-area-native-001/diagnosis-sources.json):
[disallow provider](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_test_provider_disallow.cpp),
[zone shape](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/zone.cpp),
[spatial index](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_rtree.h).
No native app or global settings were changed.

## Narrow correction under development

The multichannel source has four enabled placement areas with all five flags
allowed and no genuine keepout restriction. Those exactly match eight generic
export obstacles. The reviewed pure transform requires a same-load native
census, complete unchanged original project, simple rectangular board boundary,
exact source/DSN layer and integer geometry mapping, and unambiguous provenance.
It preserves every nonremoved AST entry. Unknown/custom/overlapping cases fail
closed. Its44 pure controls do not establish native or routing correctness.
Review found and fixed custom-rule filename case handling and quoted edge
parsing gaps; original snapshots and failures remain retained.

The initial prospective routing diagnostic compared floor guidance with and without
this correction under equal budgets, rejecting every genuine keepout in both arms
and using unchanged-rule native validation. Its failed pair and subsequent v2
completion result are documented below. These remain adapter work, not C novelty,
new independent families, GUI support or physical/electrical validation.

The safety gate also rejects legacy `module` footprint syntax after review found
that parser alias could hide a footprint-local restriction. It passed372 software tests after adjusting the budget-control
fixture to the new supported scope. The first run's15 failures are retained;
they were old synthetic control-flow inputs containing genuine keepouts, not
native routing results. Actual earlier sonde/interf/floor receipts still pass
readback with their source/evidence unchanged. The named sources contain no
genuine rule-area restrictions. The independent full14-board gate audit keeps
overall eligibility at3eligible/11unsupported. Four already unsupported inputs
now also receive the rule-area reason. All complete input inventories remain
unchanged (`evidence/review-rule-area-scope-001/population-001.json`).

A subsequent [stable-source review](../evidence/keepout-upstream-fix-review-001/REPORT.md) found fixes for both native omission paths in10.0.7, while its board-area DSN fallback is unchanged. This supplies a future toolchain-qualification candidate. No binary was downloaded or installed, and current experiments remain pinned to10.0.0 with the stricter support gate.

## Committed diagnostic execution gate

The standalone [harness](../experiments/placement_diagnostic_v1/README.md) compares floor guidance with and without exact placement correction. Root and independent review each passed37 pure controls; the separate observer review passed28 source-composition checks. At that initial freeze, native execution was pending; the following sections record its later actual runs. Each runtime helper/protocol/core/tool pin must match committed HEAD. The owned fixture must pass actual engine/import/refill/DRC plus independent readback before the same-HEAD full-board pair can execute. The pair charges all shared overhead to both equal120second wall/CPU caps, retains both failures and requires final source/code/evidence freshness. Detailed commands and scope are in its README.

Actual routing fixture001 at8497654 passed native source DRC and same-load floor/area export, then rejected before engine with an unqualified net-reference error. The original named-pad-net board also contains `(net 0) (net_name "")` on its all-allowed rule area. The strict identity parser did not recognize that native-readable empty-area representation. This is a retained implementation failure, not a native routing result; no original file is changed to work around it.

The reviewed identity fix accepts that exact empty field only on a board-level all-allowed rule area, with unique net/net_name fields and all five explicit allowed flags. Pads/routes, genuine keepouts, ordinary copper zones, ambiguous names and nonzero aliases gain no support.387 root tests and37 diagnostic controls pass; independent review verified43 saved-export bindings and23 targeted controls. These were offline prerequisites; fresh native fixture002 subsequently passed as recorded below.

## Actual routing and matched comparison

At `73107be`, corrected fixture002 passed real engine → SES import → native refill → final DRC, with zero findings, one required via and 67.926667 mm of track. Stored wall/CPU was 8.577736 / 5.535336 seconds under60-second caps. Its SIGNAL_B track crosses the unchanged allowed-area interior. Independent review checked50 bindings, exact crossing geometry and127 public files. The failed001 source/rules and all evidence remain unchanged.

The same-HEAD full [pair001](../evidence/placement-routing-pair-001/summary.json) produced:

| Policy | Opens | Blocking | Warnings | Exclusions | Charged wall / CPU seconds |
|---|---:|---:|---:|---:|---:|
| Floor reference | 160 | 1 thermal | 94 | 0 | 65.278253 / 72.920478 |
| Floor plus placement | 8 | 2 clearance | 94 | 0 | 46.451122 / 59.604769 |

Both are rejected. This is a both-invalid completion tie; no valid-route length/via delta is computed. Each received the same113.758-second invocation allowance and paid every shared cost under120-second outer caps. The raw native tasks match apart from display names; removing exactly eight attributed keepouts is the sole pre-adapter AST change. Final candidates preserve the original complete project and all areas/rules. Independent audit passed81 checks.

The second arm's candidate is `87b82041c0b6fbdbf21cd0ba2b3c08e56195facc984f2a93febc919432ae66e3`. Native DRC reports0.2994/0.2995mm clearances near RV13's rounded mounting pad against the original0.3000mm minimum. Freerouting stopped after19 passes because its best score had stagnated; it reported nine internal unrouted items and native refill reports eight opens. These measured failures justify further conservative geometry/search diagnosis, not an accepted routing claim.

Fourteen rehashed tampering controls on copied actual fixture evidence reject through semantic guards; original, relocated and restored positives pass. These offline checks cover source/rules, observer/process, DSN derivation, candidate transport and native verdict consistency. They do not replace native controls or authenticate rewritten evidence. See [controls](../evidence/placement-diagnostic-receipt-controls-001/README.md). The complete [population index002](../evidence/development-outcomes-002/index.json) retains all14 inputs and records zero accepted placement diagnostics separately from two earlier accepted production inputs.

The [curve analysis](../evidence/placement-clearance-research-001/REPORT.md) now reproduces both clearance errors analytically: the saved DSN polygon understates the pad by approximately2.235µm. A fixed20µm additive engine-planning margin became the next conservative hypothesis, not a universal numerical guarantee. Independent direct finite-line/circular-corner calculations agree with native values. The [search analysis](../evidence/placement-search-research-001/README.md) identifies a hardcoded ten-pass stagnation stop and verifies the existing lower-via-cost preset. The declared three arms separate margin and scoring effects. The separate fixed native counterfactual moves only two offending segments; its failure is retained below.

## Actual v2 margin/search ablation

At24ab168d the strongest-policy required-via owned fixture passed actual routing with zero native findings. The subsequent [three-arm001](../evidence/placement-search-three-arm-001/summary.json) preserved identical raw, floor and placement tasks; only three planning-clearance atoms changed300→320µm. The two margin arms have identical DSN ASTs and differ only in explicit via costs50/5 versus25/3.

The zero-margin/default reference rejected8opens/2clearance/94warnings.20µm/default accepted0opens/0blocking/96warnings,2647.385729mm/21vias, charged44.580724wall/56.572069CPU seconds.20µm/low rejected0opens/1starved_thermal/95warnings at C2. All exclusions are zero; all fully charged wall/CPU totals fit120second caps. Final accepted candidate SHA is36e778573b2c90dfca8f9d45597e6bd890cc45c7fc4c6c86a2673e2e7fef3bef.

This supports one exposed diagnostic adapter completion gain; search-path changes accompany the margin, so completion is not assigned solely to the two local geometric discrepancies. Lower costs caused a lost completion. No comparison has two accepted outputs, so no usable length/via delta is emitted. The accepted result has9connection-width warnings, versus6in the original source, and remains unsuitable for a whole-project-clean/electrical claim. Production integration and broader qualification are separate work. Root receipt readbacks pass; the independent raw audit passed167 checks. The counterfactual/public-copy audit separately passed344 checks. These are evidence-consistency reviews, not new native execution or human PCB review.

## Failed local-move counterfactual

At897add4 [counterfactual001](../evidence/placement-clearance-controls-001/summary.json) preserved the earlier rejected candidate and rules. Its unchanged negative reproduced8opens/two RV13-pad clearance errors. Moving both selected segments outward by21.2132034µm perpendicular to their direction removed those pad errors but caused four new clearances against adjacent GND tracks;8opens remain. The predeclared positive therefore failed. All raw evidence is retained without recipe retuning. Shared costs12.501076wall/10.826642CPU fit60secondcaps. This result argues against that simple local move as a valid repair and illustrates the need to account for neighboring copper. It does not qualify a general repair or invalidate the separately measured full reroute.
