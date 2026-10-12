# PIC copper-text omission and existing adapter reuse

The exact final native result is **1 open, 3 blocking clearance errors, 41 warnings and 0 exclusions**. Counts were rederived with the existing parser and compared with `summary.json.native_routing.final_native`. The earlier verbal zero-open count was incorrect.

All three clearance errors involve original front copper text `1=>>`: two at (202,48.7) against `/DATA-RB7` traces and one at (171.45,109.22) against `/pic_sockets/VCC_PIC`. Original text UUIDs/positions are present unchanged. The retained same-load native context already records 19 PCB_TEXT bounding rectangles: 17 `top_layer`, two `bottom_layer`. Each offending text position has a unique matching rectangle (indices14 and9). These rows have no UUID field, so that rectangle association is explicitly position-based, not a new native UUID observation.

The native DSN, mixed DSN and fully-unrouted DSN each contain zero structure keepouts and retain one original plane. The custom-body transport changes only its two padstack/body representations; it does not consume the captured graphic obstacles. This is a missing existing B1 adapter step, not a new search mechanism.

The separate open is U1 PTH pad4/GND to the original bottom GND zone, UUIDs `64e7deff-e627-4964-9855-70f97f6e85df` and `00000000-0000-0000-0000-00005b22134f`. It is not one of the JP1 custom pads. The finding alone does not prove the internal engine cause. ROOT is tracing that connection separately; plane suppression is the existing all-terminal routing surrogate to test, not proof of the cause or a fix.

## Smallest reuse

- `autorouter/floor_context.py:129–148` already observes copper graphics via native `GetBoundingBox`, binds them to original board/project/DSN bytes and retains them in context. No fresh native API is needed for this saved context.
- `autorouter/adapter.py:144–241` already adds conservative rectangle keepouts with exact DSN layer lookup, mm→µm/Y-sign conversion and exact allowed-edit proof. Here native labels are already `top_layer`/`bottom_layer`, exactly matching DSN labels. No guessed F.Cu alias is needed.
- Use `adapt_dsn(disposable_copy, 'both', context['obstacles'])` for the prospective corrected all-terminal B1 input. It removes only the original DSN plane and adds all19 captured rectangles. It does not remove native zones. Use of all19, rather than only the two failing texts, avoids a finding-specific obstacle selection.
- Do not invoke `board_floor.adapter_bytes` directly: its narrower F.Cu/B.Cu spelling gate and floor-guidance composition are different from this named-layer mixed-class diagnostic. Reuse the existing general adapter function instead. `floor_route.py:377–380` is the established caller pattern, not a request to admit PIC to that production policy.

The pure disposable-copy proof in `facts.json` shows both useful variants: graphics-only adds19 and preserves the plane; both adds19 and removes exactly one original plane. Removing the19 new nodes and reinserting the original plane at its original AST position reconstructs the entire input AST exactly. Original class/rule/network/library/placement/layer data, zero ordinary routing and the two protected custom polygons are unchanged. All inspected original/run/source files are unchanged. Native bounding boxes are **conservative rectangles, not exact glyph copper contours**; the engine still applies clearance. No next route has been executed or qualified.

## Minimal prospective shared-check change

Keep existing mixed derivation and ordinary-route removal unchanged. Add one explicit, hash-bound adapter-policy result after those steps, retain pre/post DSNs and transformation receipt, and require exactly1 plane removal plus19 context-derived keepouts with full reverse proof. The old mode must remain exact. Parameterize only the finite imported baseline's expected original-plane/graphic-obstacle population; do not generally skip geometry/area checks. Require the two exact custom bodies, local250 classes/matrix, terminal mapping and named physical layers unchanged. The new import baseline must explicitly witness the19 new keepouts and absent original engine plane before routing; retain the selective two-body activation checks and settings. Post-route checks compare against that corrected baseline, while final KiCad checks retain the original native GND zone, text, rules and all other immutable geometry. This is common B1 integration; it supplies no comparative/novelty claim.

One existing bounded diagnostic controller is sufficient: same180s wall/fullCPU and output bounds, fresh fixed protocol/source checkpoint, no retained-route seed. Original precision failure and native failed001 remain frozen. A new route can still fail connectivity, clearance, geometry or strict transport; do not relax those outcomes.

## Evidence and retained preparation error

`check_v2.py` completed in a pure local call to the existing adapter; no native/JVM/solver/network. `check.py` and `check.log` retain the first harness error: it treated the adapter's receipt dictionary as the transformation list. The corrected control inspects `receipt['transformations']`; no production fix was made. Derived proposal DSNs remain local and are excluded from compact public selection.
