# Human PCB review and bounded physical-validation plan

Prepared October10,2026; current addendum October14,2026. The original protocol text below describes its earlier state. Actual local Analog review inputs are now prepared at `.runs/analog-human-review-pack-001/reviewer-pack`; authoritative index `.runs/analog-human-review-pack-closure-002/result.json`. All3complete projects have fresh bound native refill/full-schematic checks and14unchanged warnings, with blankforms/no human review. Matched source/rules/budgets reuse completed baselines plus separately fixed exposed High C; this amended development case study is not an untouched single-run primary comparison. Failed publisher/firstclosure and all cost/exposure caveats remain. [Actual preparation](../evidence/analog-human-review-pack-001/SCOPE.md), [original protocol](history/2026-10-14-high-audit-closure/human-review-plan.md). **Protocol only: no human review, cleanup timing,
fabrication, electrical test, reviewer contact, order or spending has occurred
under this plan.** Current incremental external spending remains $0. AI code
review and native KiCad DRC are separate evidence; neither supplies a human PCB
review or an electrical-performance result.

## Inputs and eligibility

Use accepted B1, corrected B2 and C candidates from the same frozen experiment,
source project, placement, rules, preparation and end-to-end budgets. The first
development review may use the sonde family after the corrected four-arm run
finishes and is audited. Do not assemble a primary pack by mixing the best arms
from different runs.

Pilot `.runs/quality-comparison-001` is exposed diagnostic evidence. Its B1/B2/C
receipts report native routing acceptance with one warning each; B0 is rejected.
The B2 configuration accidentally used a 10% stopping threshold instead of the
intended 0.1%. Therefore **001 B2 is not the primary tuned baseline**. Preserve
all 001 artifacts; do not silently relabel or substitute its B2 result. The
corrected experiment's outcomes were pending when this plan was prepared.

Before accepting a group into the review pack, the lead/custodian must:

1. Check each receipt and its exact candidate/native-report hashes with the
   current strict checker. Independently audit the frozen experiment's budgets
   and complete population, including rejected/unsupported arms.
2. Confirm identical original project-file hashes and task scope across the
   group, including original rules, libraries, zones, protected routes, net/pad
   mapping, placement, edges and stackup. A changed problem is not a matched
   comparison.
3. Create separate complete project copies using the qualified external review
   workflow, outside originals and evidence runs. Match the pinned KiCad version
   and isolated configuration for every case. Refill zones and rerun native DRC
   on a disposable validation copy before packaging; bind reports to delivered
   bytes. A GUI normalization or changed project file requires a new validation
   record, not reuse of the previous claim.
4. Retain warnings, exclusions, ignored checks and unsupported semantics. Do not
   clear warnings, alter severities, hide rule files or move copper text for
   presentation. Routing acceptance is distinct from whole-project cleanliness.
5. Keep schematic-parity and electrical-intent status explicit. The current
   receipts say schematic parity was not checked. Reviewers may investigate
   that gap; they must not assume the automated pipeline already established it.

The primary quality/cleanup comparison includes only groups with all compared
methods accepted. Newly solved cases and rejected candidates form separately
labelled diagnostic panels. Every population member remains in the ledger; a
method's failures do not disappear because its output is ineligible for the
primary quality panel. Later representative sampling must be fixed before human
scores are seen, with family-level provenance and the selection rule retained.
One exposed sonde group supports a development case study only.

## Blinded pack construction

The custodian prepares two local directories under a new ignored run directory:

```text
.runs/human-review-PILOT_ID/
  custodian/                 # withheld from reviewers; never public Git
    mapping.json             # opaque case ID -> arm, run and exact file hashes
    allocation.json          # recorded randomization and presentation order
    full-evidence-index.json # untouched receipts, costs, metrics and provenance
  reviewer-pack/
    instructions.md
    cases/CASE_ID/project/   # complete copied native project, unchanged board bytes
    cases/CASE_ID/constraints.md
    cases/CASE_ID/native-findings.json
    forms/
```

This layout is a specification, not a claim these files already exist. The
custodian assigns unpredictable opaque IDs, records the random draw and its
mapping, and keeps that mapping outside the distributed reviewer pack. The
custodian must not be a blinded reviewer. Retain source/license attribution;
blinding does not permit deleting notices.

Use the same native board/project basenames within each matched family and vary
only the opaque outer case directory. Do not rename nets, UUIDs, components,
layers or native files to hide a method. Supply identical schematic, project,
custom-rule, symbol/footprint/library-table and notice files required by the
project. Do not supply optimizer logs, algorithm names, full run paths, earlier
route screenshots, predicted winners or automated quality rankings. Present
native findings through a custodian-generated view that removes method/run-path
labels while preserving every finding and its exact source-report binding in
the private index. Removing a display label must never modify the validated PCB
or rules.

Audit the pack for leaked arm names in outer paths, instructions, reports and
application titles before distribution. If native geometry or metadata lets a
reviewer infer the method, record that limitation; do not distort geometry to
force blindness. For later multi-board projects, check whether another included
PCB reveals a reference answer. Resolve that design before inclusion; do not
quietly remove required project files and still claim a complete project.

Supply one constraints sheet per family, identical for all its variants:

| Field | Required content |
|---|---|
| Identity and scope | Opaque family ID, task scope, supported-feature boundary |
| Immutable content | Placement, pad geometry, outline/cutouts, layers, nets, protected routes, zones/keepouts |
| Enforced constraints | Original project/rule origin, severity mapping, known exclusions and ignored checks |
| Native status | KiCad version, errors/opens/warnings; inherited findings kept visible |
| Electrical intent | Only documented requirements with their origin; every missing requirement marked unknown |
| Review objective | Find defects and estimate actual human cleanup under the frozen endpoint definition |

A future share requires the owner's explicit authorization to contact the
reviewer and send the specific pack. Audit redistribution rights and contents
then. No private boards, credentials or withheld mapping may accompany it.

## Reviewer instructions and defect sheet

Use a person with relevant PCB design experience who did not produce these
routes. Record experience and any prior exposure to this project. Do not invent
credentials, independence or agreement. Two independent reviewers are desirable
for a pilot if access and any cost are approved; neither has been recruited.

Start with each case independently, before viewing its matched alternatives.
Keep a fresh editable working copy for cleanup and a byte-identical read-only
input. Use the same workstation configuration, layer visibility and task
instructions. Review findings before looking at comparative length/via/runtime
summaries. The reviewer may inspect actual geometry; those quantities cannot be
made completely invisible.

Record each finding as an observation, an evidenced defect, or a question that
needs an electrical requirement. Do not turn a guessed current or signal speed
into a fabricated design violation. The defect sheet contains:

```text
reviewer_id, case_id, finding_id, category, severity,
evidence_status, layer, location_xy_mm, item_uuids,
description, requirement_source, native_finding_reference,
required_change, confidence, resolved_in_working_copy, notes
```

Use these categories consistently:

| Category | Examples and reporting boundary |
|---|---|
| Constraint or identity violation | Wrong net/pad, moved component, changed rule/zone/protected copper; reject rather than trade against shorter length |
| Connectivity or clearance | Opens, shorts, copper/hole/edge clearance; confirm with original-rules native checks |
| Route geometry and repairability | Unnecessary detours, avoidable vias, awkward junctions, inaccessible repair points; distinguish preference from defect |
| Zone/thermal/return connection | Islands, thermal connection concerns, disrupted plane continuity; electrical implications need explicit requirements |
| Documented electrical requirement | A specified width/current, impedance, matching, isolation or return-path requirement with a source; missing specifications remain unknown |
| Assembly, fabrication and service | Documented fab limits, solder access, inspection/rework access; do not invent a manufacturer's capabilities |
| Project usability | Missing libraries/rules, confusing handoff, failed opening, unexpected metadata changes |

Severity is critical, major, minor, or preference. Critical means a confirmed
hard constraint/functional-safety violation that blocks use. Major requires a
substantive repair before the declared handoff endpoint. Minor is local cleanup.
Preference has no demonstrated requirement violation. Record disagreement rather
than averaging a critical issue into an acceptable score.

After all independent case sheets are closed, the reviewer may compare matched
variants and give pairwise preference plus reasons and confidence. Ties and
"insufficient information" are valid. Record a method-identity guess and why it
was made before revealing the mapping. Freeze the review sheets and their hashes
before the custodian unblinds the arms.

## Actual human cleanup timing

Human cleanup time is **not measured yet**. All timing/result fields must remain
empty/null until an actual reviewer performs the work. AI estimates, simulated
edits, machine runtime and time spent preparing this protocol are not human
cleanup observations.

Freeze an endpoint before starting: required connectivity/constraints preserved,
no new blocking native findings, and all reviewer-confirmed major repairs for
the stated handoff objective completed. This does not mean electrical adequacy
when necessary requirements are unknown. Record inherited warnings and unresolved
questions separately. A reviewer may conclude that the endpoint cannot be
assessed; that is not zero cleanup time.

For the pilot, cap work at **30 minutes of active cleanup per case**, plus a
separately timed independent inspection. This is a resource limit, not a predicted
cleanup duration. Stop early for an unsafe/unsupported condition. Use an actual
clock and event sheet:

```text
reviewer_id, case_id, inspection_start_utc, inspection_end_utc,
cleanup_start_utc, cleanup_stop_utc, active_edit_seconds,
tool_wait_seconds, break_seconds, elapsed_cleanup_seconds,
stop_reason, endpoint_reached, censored, edits_summary,
input_hash, edited_output_hash, original_rules_preserved,
post_edit_native_report_hash, remaining_findings, blinding_notes
```

The reviewer records starts, stops and pauses contemporaneously. Keep tool-wait
time visible rather than silently subtracting it from practical turnaround.
If the cap is reached, report a censored observation (`>=30 minutes active`,
endpoint not reached), not a successful 30-minute cleanup. Preserve every working
copy and edit summary. Independently recheck invariants and native DRC against
the unchanged rules after edits; failures remain failures. Any changed requirement
starts a separately labelled task and cannot improve the original score.

Use recorded, balanced presentation orders across reviewers to reduce ordering
effects. Review of one variant can teach a reviewer how to fix its siblings, so
use first-exposure timing as the primary cleanup observation and mark later
same-family timings as exposed crossover observations. Do not claim comparative
human speed from one reviewer seeing three variants in sequence. Report raw
paired findings, order, censoring, disagreement and sample size; with one exposed
family, no population-level inference is justified.

## Bounded physical-validation proposal

No board is presently selected as physically validated. Before any fabrication,
an appropriately qualified person must determine whether a candidate is suitable
for a low-voltage, current-limited bench demonstration and provide the actual
schematic/BOM, component limits, supply/interface conditions, loads and functional
requirements. Net names and demo provenance do not establish those facts.
High-voltage, mains, RF/high-speed, isolation-critical or safety-critical designs
stay outside this small demonstration unless separately qualified.

Use at most one suitable exposed development family for an initial feasibility
pilot. If all B1/B2/C variants remain admissible and a comparison is justified,
plan matched boards with the same component BOM, stackup, copper specification,
fabricator and assembly process. One physical instance per arm would be only a
feasibility observation, confounded by build variation; it would not establish
manufacturing yield or general reliability. Replication requires a new scoped
plan and budget. If current sources cannot support a meaningful safe test, retain
this as a blocked physical gate and continue software work.

| Stage | Objective | Required evidence and stop condition |
|---|---|---|
| Design readiness | Confirm schematic parity, component ratings and documented test conditions | Signed human review, BOM/rule/stackup identities, resolved blocking issues; stop on missing intent |
| Fabrication-file review | Check exports preserve the frozen physical design | Exact PCB/Gerber/drill/assembly hashes, independent export inspection and applicable fab limits; export is not manufacture |
| Unpowered inspection | Identify fabrication/assembly defects before energizing | Photos, continuity/isolation checks against expected nets, component/polarity checks; stop on unexpected conduction or assembly errors |
| Initial power | Observe behavior within documented supply/current limits | Qualified operator, measured voltage/current and equipment identifiers; stop at predeclared abnormal-current/temperature criteria |
| Functional checks | Exercise only specified functions and interfaces | Input/load conditions, expected outputs, measured outputs, uncertainty and failures; do not substitute "powers on" for function |
| Constraint-specific checks | Measure documented voltage drop, thermal rise or signal behavior where required | Suitable instruments/method and explicit limits; unmeasured requirements remain unverified |

The detailed bench procedure must be authored after the actual electrical
requirements and equipment are known. This protocol supplies no guessed supply
voltage, current limit, acceptable temperature, timing margin or pass threshold.
Record operator, date, board serial/arm code, assembly revision, firmware if any,
instrument identity/calibration status, setup photos and raw readings. Distinguish
routing-caused findings from component, assembly or test-fixture failures. Never
infer all three variants work from measuring just one.

## Costs, authorization and deliverables

No quote, purchase, reviewer booking or shipment has been requested. The cost of
each item below is **unknown**, not zero:

| Item | Current estimate | Required before execution |
|---|---|---|
| Human PCB review/cleanup | Unknown | Availability, scope, compensation and contact/share approval |
| Bare PCBs for chosen variants | Unknown | Selected stackup, quantity, fabrication quote and owner approval |
| Components/assembly | Unknown | Checked BOM, availability, assembly method and quote |
| Bench equipment/fixtures | Unknown | Inventory of suitable existing equipment; quote only for missing items |
| Shipping, tax, consumables, rework | Unknown | Explicit line items and contingency within approved total |
| Total incremental external cost | Unknown; **$0 currently authorized** | Concrete capped total and separate owner approval |

The lead may prepare local manifests, forms, export-validation instructions and
an approval-ready cost sheet without spending. Do not contact a reviewer/vendor,
upload a board for quoting, place an order or energize hardware on this plan's
authority. Approval must identify the actual board pack, recipients, work and
maximum incremental cost. No formal release or public review-result publication
is authorized here.

When executed, preserve the withheld mapping, delivered-pack hashes, completed
human forms, unblinding record, edited projects/native reports and any physical
raw data in the durable local run directory and verified backup. Publish only
audited project-owned summaries with rights/consent checked. Until actual approved
execution occurs, the status remains: **human cleanup unmeasured; independent
human PCB review pending; physical/electrical validation not performed**.
