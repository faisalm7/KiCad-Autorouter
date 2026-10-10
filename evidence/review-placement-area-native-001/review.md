# Independent review of actual placement native001

47 offline evidence checks passed against the retained run, with zero new native or engine jobs. This is a consistency audit of a **failed four-case native qualification**, not a pass for the controls. The sole positive allowed-placement case was native-clean and emitted two generic keepouts. Track-prohibited, via-prohibited and mixed cases all reported zero findings despite correct exact source flags, same-load observations, expected typed DSN objects, unchanged project/rules, error severity, and the intended routes crossing the areas. Full source/run/case/code inventories and native process/argv/input/report bindings were verified unchanged.

Recorded totals:6.785365541wall/4.759377CPU seconds within60shared limits, sampled before final publication/freshness checks. No independent enclosing invocation timing was recorded. Actual summary SHA `c61d54b5508f0508528e1236ead7bf97ad21ef336e32448994c6239db56b058f`.

## Source-backed diagnosis, bounded claim

The exact pinned10.0.0 provider's `checkDisallow` returns without reporting implicit rules. Its separate anti-track path obtains zones through DRC_RTREE and queries only tracks/arcs. `ZONE::GetEffectiveShape` returns stored filled polygons (or SHAPE_NULL), not the rule-area outline; `SetLayerSet` initializes empty polygon sets. The native zone filler expressly skips rule areas. These paths strongly explain this observed missed-prohibition behavior. They contain no relevant check of placement_enabled or placement-source sheet name. Source files/hashes are retained in diagnosis-sources.json. This is not a blanket claim that every KiCad check or every geometry is defective; the actual missed controls are the measured result.

A minimal fresh no-placement diagnostic can remove only the placement node from disposable prohibited-track/via cases, preserving every rule flag/UUID/route/project, to falsify the fixture-condition hypothesis. It must not fabricate filled polygons, change severities or be called a qualified negative when DRC still misses. All001 evidence remains immutable.

## Immediate safe scope

Agree with lead's common preflight restriction: retain ordinary copper zones, but reject original board/footprint rule areas with any prohibition or unknown, missing or duplicated keepout flag; placement-only without explicit five fields also rejects. Permit only all five distinct explicitly allowed fields. Apply common source preflight to acceptance and readback/strategy callers; a clean native report alone cannot substitute. This declines unsupported constraints rather than altering them. A policy-negative can pass by documented unsupported rejection while the native-negative remains failed.

Independent source census finds no rule areas in the known sonde/interf source boards and exactly four all-five-allowed board placement areas in multichannel; bound source hashes are in known-source-area-census.json. This is a source-scope check, not rerun qualification or a claim every archived receipt is unaffected.

## Transform condition remains narrow

The frozen pure transform493616a7 was run offline against these actual same-load area observations and original byte inventories. Allowed-placement removes exactly2; track/via cases reject for no eligible areas; mixed rejects for overlap ambiguity. `audit.json` records outcomes. This pure attribution probe passes rawDSN also as guided input, so it does not qualify a raw→floor-guidance chain or routing acceptance. It shows that unexpected clean native negatives do not cause prohibited areas to be removed. Production promotion still needs the scoped caller guard, bound full pipeline and prospective native evidence; board-floors-v1 remains unchanged.

Independent AI review only. All original/run/author artifacts remained read-only; only this new review directory was written and is now frozen.
