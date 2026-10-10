# Actual six-case custom-pad controls001 audit

The retained run truthfully remains **failed_controls**, controller exit **2**. Four controls met the frozen predicates. Both foreign-net intrusion controls produced the required actual copper short plus a same-pair solder-mask error, which the original strict predicate excludes. This audit does not relabel the run, relax any source rule, or qualify production custom-pad routing.

| Transform/case | Opens | Blocking | Warnings | Exclusions | Frozen predicate |
|---|---:|---:|---:|---:|---|
| front0 positive | 0 | 0 | 4 | 0 | pass |
| front0 false hull | 1 | 0 | 5 | 0 | pass |
| front0 foreign intrusion | 0 | 2 | 4 | 0 | fail |
| back90 positive | 0 | 0 | 4 | 0 | pass |
| back90 false hull | 1 | 0 | 5 | 0 | pass |
| back90 foreign intrusion | 0 | 2 | 4 | 0 | fail |

All twelve native stages completed: six observer/export stages exit0 and six DRC stages exit5. Every DRC report has warnings, so exit5 is consistent even for positives. The actual reports contain four `missing_courtyard` warnings per case; each false-hull case adds one `track_dangling` warning. All six retain the same four effective native ignored checks. The original project explicitly ignores three checks; `track_not_centered_on_via` is absent from the source severity map and is an additional observed native default. These are inherited unchanged settings, not four newly authored exclusions. No report has an excluded finding.

## Native geometry and failure interpretation

Each case uses an owned four-pad/two-track fixture derived from the original pic_programmer custom polygons, with the original complete project/settings files copied unchanged. It is not the original routed board or a new corpus family. The actual same-BOARD before/after observations are equal, and all three explicit-layer APIs returned geometry: `MergePrimitivesAsPolygon`, `TransformShapeToPolygon`, and `GetEffectivePolygon`. Both custom pads retain the 0.3×0.3mm rectangular anchor, no drill, one five-vertex polygon, no arcs/holes, and the exact predeclared world rings. The original Default class resolves CONTACT and FOREIGN to 0.5mm track width and 0.25mm clearance; the original board floors are unchanged.

Front placement is native F.Cu/0° and DSN `front 0`. Back placement is native B.Cu/flipped/90° and DSN `back 270`; exact retained world rings match the declared transformation. Both shapes are Y-symmetric, so these observations do not qualify arbitrary chiral reflection. Exported concave-pad copper is a hull; retained native connectivity, not hull membership, detects the false-contact control.

Each false-hull report identifies exactly the CONCAVE-pad and CONTACT_TRACK UUIDs in one `unconnected_items` finding. Each foreign intrusion identifies exactly the CONCAVE-pad and FOREIGN_TRACK UUIDs in both `shorting_items` and `solder_mask_bridge`. `checks.py` at the execution commit requires every foreign error to be `clearance` or `shorting_items`; the mask companion makes `expected_predicate_met=false`. A future revised diagnostic could require an actual copper short and permit only this same-pair mask companion, but that would be a new predeclared predicate/run. It would not erase this failed result, weaken original DRC settings, or establish general clearance/short enforcement.

## Provenance, costs and preservation

Execution commit: `34665498a2a4e3a0c017f7120f1352fa9e4f7d5e`; driver SHA256 `c53b1dc32c25c6b940c35e1fd8fd0e2986680edef55139f64bdf679a10700cc4`. Summary SHA256: `dadb2512fef6bc4147ae522868acdc983d1d36bc8363bf14cd140e422f2f07db`. The independent audit checks the saved code against that commit, all current pinned binary hashes, the complete frozen output inventory, native/process/log/binding hashes, exact argv/cwd/exit semantics, actual candidate hashes and nonsaving DRC input copies. The committed callback uses one `LoadBoard` and one `ExportSpecctraDSN` around the observer calls; no board save or engine invocation occurs.

All 15 original source files (1,366,598 bytes) match the acquisition manifest's size, Git blob and SHA256 identities before and after audit. Every complete observer copy equals the original project inventory except its explicitly owned board fixture. Every DRC copy preserves those exact files and adds only `pic_programmer.kicad_prl`. Source rules, severities, project files, notices and copied dependencies are unchanged. Native calls use the recorded network-denied sandbox and isolated case directories. The code's RSS/disk polling limits are measured guards, not hard OS quotas or peak-memory proofs.

Stored pre-publication samples are **15.271931 seconds wall / 12.885170 seconds full parent+waited-child CPU**, within the shared 180-second caps. Stored native-step CPU sums to 5.438537 seconds; the full total is larger because preparation and all parent/metadata work count. The independent outer wrapper records exit2, **15.781483 seconds wall / 13.340561 waited-child CPU**, no cleanup signals, and the exact command/log hashes. Stored inner totals precede final freshness checks; the driver checks the caps after them. This is not a routing speed comparison.

The offline audit passed 5,026 assertions, including repeated bounded file reads and inventory checks, without native/engine/network execution. `audit-001.log` and `audit-initial.py` retain the initial audit's overly strict equality assertion: it rejected the allowed generated `.kicad_prl`. The corrected audit permits only that exact extra filename and still requires every original file/hash unchanged. The raw native result was never modified. Assertion count is bookkeeping, not broader qualification.

## Public selection and remaining scope

`selected-public-proposal.json` lists **78 exact files / 641,151 bytes** for optional lead curation, with raw paths, destination names, SHA256, sizes and rights scope. No payload was copied to tracked evidence by this audit. Selection includes the six owned boards/original project settings, recipes, raw native observations/DSN/DRC/process receipts, execution metadata, and both upstream notices. It omits repeated full schematics/libraries/models, generated config, repeated DRC projects and code payloads; their original raw inventories remain preserved locally.

The source is the official KiCad `demos/pic_programmer` project at `69cafb907ebc09e7722a2a464b1d466fc2e3608d`. The upstream LICENSE.README explicitly places all `demos/*` under CC BY-SA4.0. Derived boards/DSN/geometric observations retain that attribution and both original notices; the owned fixture alterations are identified. Omitted third-party assets are not re-published under a blanket root grant.

No new production eligibility, arbitrary custom geometry, nondefault netclass resolution, new-severity enforcement, complete dependency closure, independent-family count, route-quality gain, C novelty, GUI or physical/electrical qualification follows. This is an exposed development diagnostic with a retained batch failure, not a new six-board routing result.
