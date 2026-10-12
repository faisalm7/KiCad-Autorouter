# PIC pad-local clearance: source meaning and next four native controls

A positive pad/footprint **override** can replace POWER's0.28mm clearance with0.25mm for a track-to-pad pair. It does not compute `max(POWER, local)`. The maximum in the early override branch concerns the two items' *present local overrides*. A partner's netclass preference is not another local override. The board minimum still applies. This is pinned-source evidence, not yet qualification of this particular native pair.

## Exact cached primary source

All KiCad sources are commit `0feeca2a807f428ad2b3fa7c1e39625cb769f02c` (10.0.0), with original GPL-2.0-or-later headers. `bindings.json` binds original cache/receipts and confirms inspected bytes remained unchanged; no network or upstream source copy was needed.

- [PAD::GetLocalClearance / GetClearanceOverrides, pad.cpp1598–1615](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pad.cpp#L1598-L1615): a present pad-stack clearance wins; otherwise lookup delegates to the parent footprint. Cached SHA `585db35f7e35ac8f781e712507eedc90611708bc36a49606e31176ab7d86ace2`.
- [DRC_ENGINE::EvalRules, drc_engine.cpp1106–1174](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/drc/drc_engine.cpp#L1106-L1174): for copper clearance, read each connected item's override, choose the larger present value, clamp it to board minimum, then return early when nonzero. A zero-valued override does not follow this nonzero return. Noncopper and hole-clearance paths have separate conditions. Cached SHA `ddd99dc45baea9aa94997eb074e8529c34374b58492668ef80667f6d4a9ea775`.
- Same file1744–1801: without explicit/differential-pair overrides, the netclass fast path takes the maximum of the two class clearances. Thus ordinary POWER/Default is280µm before an eligible local override.
- Same file1869–1947: other local clearances, explicitly exemplified by zones, are later maxed with netclass clearance. This does **not** negate the earlier pad/footprint override return. Do not generalize pad override behavior to all nodes called clearance.
- [BOARD_CONNECTED_ITEM::GetOwnClearance, board_connected_item.cpp121–129](https://github.com/KiCad/kicad-source-mirror/blob/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/board_connected_item.cpp#L121-L129) returns0 when no engine is attached; otherwise it uses the cache. Cached SHA `0a004dffddb178c1da44b82e4b832724b9a83a0143a2ddbaab518cf1a77b17b9`. `DRC_ENGINE::GetCachedOwnClearance`, drc_engine.cpp2532–2548, evaluates against a null second item. Own clearance is not a pairwise query.

Earlier net-tie handling (EvalRules1065–1103), explicit rules, zones, NPTH/hole constraints and machining remain outside these four controls.

## What PIC005 actually observed

Both unchanged before/after-export getter lists report JP1/1 VCC as POWER with class preference280000nm, but footprint clearance250000nm, no pad-local value, effective override250000nm and own clearance250000nm. JP1/2's Default preference is250000nm and its same override/own values are250000nm. The original project board minimum is0, so this observation does not test minimum clamping. Exact rows and original raw-summary bindings are retained in `facts.json`.

The record still says initialization and pairwise-rule qualification are false; no WriteDRCReport ran in005. Nonzero getters and a separate prior successful native CLI report do not prove successful same-BOARD initialization or this prospective pair result. The old failed005 summary is unchanged.

## Smallest next native discrimination

Use ROOT's four fixed front0 cases in `PROSPECTIVE-CONTROLS.json`, extending the existing owned-control fixture/check functions and reusing its `ControlJob.drc`, source snapshots, process/binding capture, cancellation/publication and quotas. Keep the complete original project/rules/severities/exclusions byte-identical. Only generated owned board geometry/local fields change. Rename CONTACT to VCC so the existing project selects POWER; FOREIGN remains Default. Approach CONCAVE's flat upper edge with the existing500µm FOREIGN track.

| Case | Exact edge gap | CONCAVE footprint override | Prospective result |
|---|---:|---:|---|
| Wide baseline |290µm|absent|native positive at280µm requirement|
| Local positive |260µm|250µm|native positive at250µm requirement|
| Class negative |260µm|absent|exact target-pair clearance error at280µm requirement|
| Local negative |240µm|250µm|exact target-pair clearance error at250µm requirement|

Native reports, rather than a getter or inferred success, decide each result. Require exact target UUID pairs for negative errors, no unrelated blockers or exclusions, zero opens, preserved settings/geometry and all warnings. Unknown or critical warnings fail. Keep every failure; do not retune gaps or suppress solder-mask/other errors to obtain a pass. Margins are deliberately finite; native report geometry must confirm them.

If the CONTACT track remains500µm, record POWER's800µm *preferred* width separately: drc_engine.cpp299–306 sets width minimum to the unchanged250µm board floor and optimum to class width. This DRC-only fixture must not pretend to exercise the production exact-target route auditor. A future800µm geometry variant would need its own declared dimensions.

The four results can qualify only this footprint-override/mixed-class pair. Pad-local precedence, maximum of two opposing overrides and board-floor clamping remain source-backed until separate controls are justified. No new DSN/JVM/router invocation is required, and neither SES transport nor original PIC routing support follows from success.
