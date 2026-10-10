# Independent copper-path draft review

Reviewed ignored files are hash-bound in `audit.json`. No native or engine job
ran, no board was saved, and no tracked file changed. The audit uses synthetic
nanometre geometry, not reference routing. Five independent kernel/source
controls pass; two material wrapper gaps reproduce.

For a validated integer polygon and complete circular-drill population, the
`certified_leg` proof is sound: both endpoints have exact even-odd membership,
the complete segment stays strictly farther than the declared margin from
every boundary edge, and every drill remains farther than radius plus margin.
That establishes a positive-width local corridor without asserting that the
whole filled body is a robust connected component. Exact rational distance
comparisons preserve the observed subnanometre separations. Boundary tangency,
drill-center crossing, and valid interior controls behave as expected.

The current `attempt_paths_v2.run` is not ready to serve as a trusted complete
connection certificate:

1. Only the paths through existing fill are tested against drills. A controlled
   bridge from (0.375, -0.25) to (1.0, -0.25) mm is emitted through a 0.1 mm drill
   at (0.75, -0.25) mm, in the gap between the two fill bodies. The new bridge's
   centerline needs the same positive drill-clearance proof. This requirement
   does not require the new bridge to remain inside existing fill.
2. Changing the controlled target and destination body net codes from 100 to
   999 still emits four proposals labeled net 100. Target UUID uniqueness and
   net identity, selected body zone/net/layer/index consistency, pad logical
   identities, geometry/report/source bindings and physical-hole completeness
   must be checked by a trusted wrapper.
3. The work guard is not checked after final sorting/return; waypoint generation
   is not charged, and some preprocessing populations rely on the fixed
   observed input. A final guard check and explicitly bounded/charged work are
   needed before advertising the cap as an enforced certificate-generation
   limit. The actual saved v2 attempt took about 0.81 seconds, so this observation
   does not invalidate that run's measured timing.

The actual saved v1/v2 attempts emitted no path proposals and correctly kept
scene qualification, whole-body qualification, and routing acceptance false.
Their conservative outcomes remain valid. The data agent acknowledged the
reproductions and is preparing a separate v3 with guards, bridge checking and
bounded multibend search; v1/v2 and original evidence are to remain preserved.

Even a corrected geometric certificate will establish local copper existence
only. It is not a proof of ampacity, manufacturing sufficiency, fresh native
DRC, whole-project routing acceptance, or generalized routing improvement.
