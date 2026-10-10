# Independent graph003 saved-geometry audit

All 1,313 checks passed. No native/router job ran. This audit does not call the
draft geometry predicates: it uses a separate exact rational projection and
segment-distance implementation plus integer winding membership.

All 379 pad centers were reconstructed directly from saved board geometry using
exact quadrantal footprint transforms. Drill geometry matches all native pad
observations, and all 35 native vias match the saved board. The complete physical
hole census is 352. All 27 observed zone contours exactly match saved fill.
Current complete source, failed candidate, original project, native report,
input binding, exporter files and graph code hashes were rechecked.

All four proposed bridges join verified source and destination paths. Each
existing-fill leg has greater than 10 micrometres clearance from every contour
edge and physical hole, and each new bridge centerline clears all holes by the
same margin. The smallest existing-path boundary clearance is about 32.3315
micrometres; smallest drill clearance is 146.6268 micrometres. Witness endpoints
lie strictly in the target C4 and distinct L7 terminal annuli, on the same GND
net and B.Cu layer. Generated width is the unchanged 0.5 mm class value.

There is no geometric blocker to a bounded repair-only native diagnostic that
rechecks the exact input bindings, inserts only the selected new track, preserves
all original constraints and protected routing, and requires full native final
validation. Final saved fill must remain identical to the witnessed fill;
otherwise this certificate is stale and cannot be reused without requalification.

This proves a local positive-width path in the saved geometry. It does not prove
ampacity, manufacturing sufficiency, a 0.5 mm corridor through the existing fill,
clearance of the full new track capsule from unrelated objects, whole-body
topology, native routing acceptance, or end-to-end algorithm improvement.
