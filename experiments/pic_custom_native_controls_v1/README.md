# Owned custom-pad native controls

The original six geometry controls completed as recorded in
`evidence/pic-custom-native-controls-002/summary.json`; failed001 is retained.
The additional `--suite local-clearance` is a prospective four-case diagnostic
specified in `CLEARANCE_PROTOCOL.json`. It reuses this runner, exact geometry
observer, process limits, original-rule native DRC and report checks.

All four new cases are front0. VCC uses the original POWER class (preferred
width0.8mm/clearance0.28mm); FOREIGN uses Default (0.5mm/0.25mm). Existing0.5mm
tracks remain legal relative to the original0.25mm hard width floor. No project
setting changes. A foreign track approaches CONCAVE's flat top with an exact
capsule gap of0.29,0.26 or0.24mm. The two override cases add only the original
JP1-style0.25mm footprint clearance to CONCAVE. Expected outcomes:0.29 without
override passes;0.26 with override passes;0.26 without override and0.24 with
override each produce exactly one targeted clearance error. Every negative
requires its corresponding positive. All warnings remain recorded.

This tests one footprint override against a Default foreign track. It does not
qualify pad-local precedence, two local overrides, board-floor clamping,
zone-local rules, Freerouting equivalence, SES survival or production custom
support. Source reading informs these hypotheses; only actual native outputs
can qualify the four predicates. No `WriteDRCReport` call is used.

Run only after a committed source snapshot, on ROOT's sequential native lane:

```sh
python3 -B experiments/pic_custom_native_controls_v1/driver.py --suite local-clearance --run-native --output .runs/pic-local-clearance-native-001
```

The remaining text describes the original default `--suite geometry`.

These fixed development fixtures test the two exact five-point custom primitives
from official KiCad `pic_programmer` under the complete original project rules.
They are owned diagnostics, not new corpus members or a routing result. Production
custom-pad support and the four unqualified severity-provider gates remain closed.
The 15-file original source is immutable; each disposable complete project changes
only the board to the authored fixture, keeping all other 14 files byte-identical.
Retain the source's CC BY-SA 4.0 notices with derived board artifacts.

Six prospective cases are ordered front0 positive/false-hull/foreign-intrusion,
then back90 with the same three cases. The frozen `recipes.py` is unchanged from
the independently checked design. There are four pads, four unique footprint
references, two nets and two 0.5mm tracks. CONTACT and FOREIGN both use the original
Default class (0.5mm preferred width, 0.25mm clearance). The unused POWER class,
all netclass patterns, floors, severities and ignored checks remain unchanged;
nondefault-class resolution is explicitly unexercised.

The source explicitly ignores three checks. Actual original observation002 also
reports the default `track_not_centered_on_via` ignored check; its exact raw report
SHA is pinned in the protocol and copied committed evidence. Each control requires
the same four effective native ignored keys, with source-explicit and observed
sets recorded separately. Missing, duplicated or unexpected keys reject. Unknown
finding types, including the four still-unqualified providers, reject locally;
known noncritical library warnings remain visible. No severity is rewritten.

The positive route touches actual custom copper away from both small anchors.
False-hull changes only its endpoint so the complete track capsule is separated
from the concave copper, despite landing inside the export hull. Intrusion changes
only the FOREIGN route endpoint to contact the concave pad away from its anchor
and the CONTACT track. Negatives require actual error findings with precise UUID
pairs in the correct raw DRC section, not mere failure or unrelated violations.
Every negative needs its same-orientation positive. All six rows remain visible
even when a native/API/budget failure prevents execution or qualification.

The back90 world recipe is fixed at `T(x,y)=(40-y,40-x)`mm. Footprints and pads
have nonzero 90-degree native orientation on B.Cu; local primitive Y reflection
combines with KiCad's clockwise quarter-turn. Exact observed world polygons,
positions, layers and flags must match before interpreting DRC. The source-derived
DSN back placement expectation is 270 degrees. These two polygons are Y-symmetric,
so this does not qualify arbitrary chiral reflections or rotated custom geometry.
The native observer is the previously exercised getter body with only its census
bounds narrowed to 4/4/2. Existing strict DSN parsing is reused; custom hull/terminal
checks do not mistake a DSN hull for native concave copper.

Each case uses the existing same-loaded-board floor callback/export, followed by
the existing nonsaving original-rule refill/DRC on another complete copy. No engine,
SES import, GUI, board save, rule relaxation or new production validator is added.
All raw outputs/process/logs freeze before caller parsing. Completed case trees
are captured once, never rebound. Final checks compare original/runtime/tool/code,
all frozen case trees and raw-derived summaries after subprocess metadata. Strict
summary publication includes the final bounded scan before canonical equality and
budget checks; failed/cancelled corrections archive any former positive first.
Finite observations are not atomic authentication against hostile concurrent writes.

One lock and one ROOT-owned worker lane; no competing native jobs. Shared limits
include preparation, snapshots, all failed attempts, both stages, and publication:
180 seconds wall and full parent+waited-child CPU, 32MiB complete batch output,
256KiB logs/stage, 2GiB polled process-group RSS. Each native stage is also bounded
to 30 seconds or the remaining shared cap. Twelve full source copies plus 2MiB
headroom and actual code-snapshot bytes must fit before work starts. Original
copies alone are conservatively 16,399,176 bytes. CPU/RSS limits are measured or
polled acceptance controls, not hard OS resource guarantees. Cancellation handlers
are scoped and restore prior handlers.

Pure reproduction (no native import or execution):

```sh
python3 -B -m unittest discover -s .runs/pic-custom-native-controls-draft-001 -p 'test_*.py' -v
```

After independent review, ROOT integrates all nine helper/protocol files into
`experiments/pic_custom_native_controls_v1`, verifies source checkpoint and backup,
then alone invokes a fresh output:

```sh
python3 -B experiments/pic_custom_native_controls_v1/driver.py --run-native --output .runs/pic-custom-native-controls-002
```

No native result is promised. Original observation002 establishes that the pinned
APIs worked on the original two B.Cu pads and original ordinary DRC had no opens or
blocking findings; it does not substitute for these new front/back contact controls.
Imported route transport, production support, severity-provider semantics and a
fair full-board B0/B1/B2/C comparison remain later gates.

## Exposed diagnostic amendment v1.1

Native controls001 at34665498 completed all twelve stages and matched all six
fixed geometries. Both positives and both false-hull negatives passed. Each foreign
intrusion produced the required exact-pair `shorting_items:error` plus an exact-pair
`solder_mask_bridge:error`; the original predicate rejected that companion error.
The failed001 receipt and all raw findings remain unchanged.

This revision changes only the diagnostic expectation: at least one nonexcluded
same-pair copper short/clearance error remains required, and at most one same-pair
solder-mask error may accompany it. Mask-only findings, wrong pairs, unrelated
errors, opens, exclusions and unknown/critical warnings still fail. Geometry,
project rules/severities, source files, budgets and production policies are unchanged.
Every raw error remains an error; these invalid boards are never accepted routing.
A fresh002 execution after reviewed-source checkpoint will test the revised
controller. This is an exposed diagnostic correction, not a comparative gain.
