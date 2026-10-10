# Pinned Freerouting padstack import review

The saved Freerouting 2.5.0 bytecode supports the lead’s concern: this padstack import path converts a polygon to its convex hull and stores one convex shape per board layer. Several shape clauses on the same layer overwrite each other; they are not united. A pure DSN substitution therefore cannot be assumed to preserve the two custom copper shapes. No engine import or route was executed by this review.

## Exact evidence

The five saved javap outputs all match their receipt hashes. The receipt’s JAR SHA256 `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7` matches the project tool lock; this review did not freshly rehash or execute that JAR. The failed lookup of `io.specctra.parser.Padstack` is retained as an exit-1 observation; the actual parser method resides in `Library.readPadstackScope`.

- `Library.txt` lines327–389: allocates `ConvexShape[]`, transforms the parsed shape, calls `PolygonShape.convexHull`, then `splitToConvex`. It warns if the split length differs from one and takes element zero.
- `Polygon.txt` lines74–128: `transformToBoardRel` rounds transformed coordinates to integer points and constructs `PolygonShape`; it does not itself make that shape convex.
- `PolygonShape.txt` lines863–964: `convexHull` recursively discards non-left-turn vertices. The library has a separate decomposition operation, but the padstack reader calls the hull operation before that decomposition.
- `Library.txt` lines439–454: each named layer is assigned with `aastore`; a later shape replaces the prior value for that layer. PCB/SIGNAL shapes call `Arrays.fill`, also in input order.
- Core `Padstack.txt` lines11 and249–267: the field and public getter hold/return a single `ConvexShape` for each layer. There is no per-layer collection in this representation.
- `Library.txt` lines313–319: an already-existing padstack identifier returns success without rebuilding it. The earlier name normalization also removes decimal suffix patterns; unique simple probe identifiers avoid confounding a shape test with name aliasing.

These are static conclusions about this pinned importer and representation. They do not establish runtime behavior for every malformed polygon, coordinate overflow, layer alias, hole/window, transform or other engine subsystem. The reviewed path does not support a claim that every use of `PolygonShape` elsewhere is convexified.

## Small next falsifiable probe — proposed, unexecuted

Use one reviewed import-only Java harness against the pinned JAR, never its router. Resolve and verify the actual scanner/importer and padstack construction APIs first; no constructor signatures are assumed from the current five outputs. Call the real `Library.readPadstackScope` (or the normal complete-DSN importer if required), then inspect the returned padstack through `getShape(layer)`. Calling only `PolygonShape.convexHull` would not test transport.

One bounded invocation should load five tiny owned fixtures: a convex polygon positive; the exact five-vertex concave recipe; disjoint same-layer rectangles A then B; the same rectangles B then A; and A/B assigned to distinct layers. Preserve exact input bytes, transform units/scale, parser return status, resulting shape class, corners or equivalent boundary representation, area/bounds and point-membership observations. For the concave recipe, the local point(-0.4mm,0) is inside the hull but outside the original copper and anchor; compare it with an interior body point. For disjoint rectangles, test an interior point in each rectangle and the gap. Static expectations are hull inclusion and last-shape-only membership, with cross-layer storage as a control; do not adjust expectations after observing results.

Keep all five fixtures below32KiB total and retained output below1MiB, with one process, a30-second shared wall/full-CPU acceptance cap,512MiB Java heap, bounded child memory/logs, and no network/telemetry/native workers. Bind the JAR, Java/compiler, harness and inputs before/after. Preserve failed parsing and unexpected results. This can qualify or falsify the representation hypothesis only; it does not qualify custom-pad routing, native connectivity, clearance, backside placement or severity-provider semantics.

If the pinned importer confirms these limits, a simple concave-polygon or same-layer-piece adapter is insufficient. Any engine change or multi-pin decomposition is a separate hypothesis requiring exact terminal identity and copper-union proofs plus the already-qualified native contact/false-hull/intrusion controls. No production support gate should change based on this static review.
