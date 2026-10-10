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
about every KiCad version or an upstream-confirmed defect. A no-placement
counterfactual remains pending to rule out the fixture's placement metadata.

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
closed. Its41 pure controls do not establish native or routing correctness.
Review found and fixed custom-rule filename case handling and quoted edge
parsing gaps; original snapshots and failures remain retained.

A prospective routing diagnostic will compare floor guidance with and without
this correction under equal budgets. It will reject every genuine keepout in
both arms and use actual unchanged-rule native validation. Any resulting gain
would be an adapter gain, not C novelty. No completion improvement, new eligible
family, GUI support or physical/electrical validation is established yet.

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
