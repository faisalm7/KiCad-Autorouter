# Next evidence milestone: qualify pic_programmer, then test existing C

**Recommendation after disposable-handoff qualification:** qualify the existing
licensed `pic_programmer` input's narrow custom-polygon pad transport and original
rule semantics, then prospectively compare the existing feedback-pruning C with
B0/B1 and the stronger B2 portfolio on that complete board. Do not acquire another
project first, invent a mechanism, or remove custom pads to make it eligible.
This is a bounded go/no-go milestone, not a prediction that C will win.

This planning audit performed no native/engine/network work or tracked edits.
`audit.py` verified all 15 manifested pic files (1,366,598 B including notices) and
19 complex_hierarchy files against the acquisition SHA-256/size records, then
rechecked all sampled inputs. `audit.json` retains the exact source/code/evidence
pins and static geometry. Population remains **16 acquired, 3 statically eligible,
13 unsupported, zero untouched holdouts**; independent-family count is unknown.

## Why this input first

| Candidate | Local evidence and decision |
|---|---|
| **pic_programmer** | Complete official project; 63 footprints, 247 pads, one ordinary zone, two custom pads; configured Default/POWER assignments already use supported literal `GND`/`VCC`. Four unknown severity keys exist explicitly in pinned KiCad10 source. Best bounded path to another nontrivial full-board input. |
| complex_hierarchy | Complete licensed project, but static inspection finds **165 pad/via teardrop zones plus one ordinary zone**, not merely two parser exclusions. Punctuation-bearing class assignments and retired/unknown `zone_has_empty_net` semantics need qualification; teardrops need preserved-intent versus reference-derived-copper analysis before a fair unrouting task. Do not delete or retain them blindly. |
| ColdFire / remaining seven expansion inputs | Four-layer/class/critical-warning qualification or custom/net-tie/exclusion/genuine-keepout gaps compound dependency closure. Native genuine-keepout controls already failed; do not weaken those gates. |
| LiPo / PMOD | Both remain incomplete/legacy-format. LiPo's actual002 only observes retained original routing; export001 fails and four padless duplicate references, implicit ignored checks and saved-format semantics remain unresolved. PMOD has no native result and legacy rule/class mappings. These are useful audits, not the fastest representative routing additions. |
| New official video lead | Existing pinned metadata identifies 47 files/8,266,208 B plus notices and 32 local footprints, but KiCad6 stock-library identity, PCI/high-speed intent, actual layer/scope and per-asset closure remain gates. No acquisition has established usable routing support. Defer this additional closure workload until the existing tractable input is tested. |

The already exposed multichannel low-cost variant is another later mechanism
transfer lead, but it has **32 vias / 2624.012120 mm and a thermal error**, versus
the valid default's **21 vias / 2647.385729 mm**. Repair alone would not establish
dominance, and placement-policy propagation into C/B2 is currently unqualified.
It adds no new eligible input. Preserve this lead rather than calling it an easy win.

## Exact support gap and minimal change

Source: `data/sources.json`, official KiCad commit
`69cafb907ebc09e7722a2a464b1d466fc2e3608d`, `demos/pic_programmer`.
Board SHA `1ca70b620506818eb0227e2863bbd573d1fec1672072dc43d0dbe8475e69c8fb`;
project SHA `3b0ac39da5af86d0baa2a64da55a89c39ba00148dc82b54f3062f5c3650a5cc5`.
Thirteen original files include both schematics, project, library tables, local
symbol library, four footprints and two WRL models; two CC-BY-SA4 notices are
retained. This verifies the manifested complete project, **not** installed stock
library parity or independent ancestry. Keep unavailable-library warnings visible;
do not rewrite tables, fetch unreviewed assets or claim whole-schematic parity.

Both custom pads belong to JP1, on B.Cu/B.Mask, anchor rectangle 0.3×0.3 mm,
`clearance outline`, one filled width-zero five-vertex polygon, no hole/arc:

- Pad1 UUID `3acb5a29-7227-4ce2-8aa0-d92094ccdfdc`, VCC, local pad offset (-0.725,0): polygon (1,0),(.5,-.75),(-.5,-.75),(-.5,.75),(.5,.75).
- Pad2 UUID `5b196d03-cd44-4c2b-9a91-fadc24ae5f4b`, `/pic_sockets/VCC_PIC`, offset (.725,0): (.5,-.75),(-.65,-.75),(-.15,0),(-.65,.75),(.5,.75). This polygon is concave.

Cached pinned10.0.0 source at `0feeca2a807f428ad2b3fa7c1e39625cb769f02c`
is under `.runs/support-scope-review-001/source/`. `drc_item.cpp` explicitly maps:

| Original severity key | Original setting | Native identity / source line |
|---|---|---|
| `footprint_symbol_field_mismatch` | warning | `DRCE_SCHEMATIC_FIELDS_PARITY`, line210; schematic field parity, not demonstrated by ordinary routing DRC alone |
| `missing_tuning_profile` | warning | `DRCE_MISSING_TUNING_PROFILE`, line307; unsupported tuning intent must still reject |
| `text_on_edge_cuts` | error | `DRCE_TEXT_ON_EDGECUTS`, line66; do not discard outline violations |
| `track_on_post_machined_layer` | error | `DRCE_TRACK_ON_POST_MACHINED_LAYER`, line315; advanced padstack/layer scope stays excluded |

`specctra_export.cpp` lines68–74 and543–573 explicitly export the **convex hull**
of merged custom-pad primitives. A hull is a conservative obstacle envelope but
can present false connection locations inside the concave notch. Do not call it
exact native copper or infer valid connectivity from an engine success.

Add one reusable narrow custom-pad qualifier/auditor, not another route lifecycle:
one filled simple polygon with bounded vertices, no holes/arcs/multiple primitives,
anchor wholly contained, ordinary one-copper-side SMD, known options/layers only.
Reject everything else. Preserve the actual original pad AST in all candidates;
same-loaded-board observation must bind native polygon/anchor, UUID/net/terminal,
footprint rotation/reflection and DSN padstack/pin correspondence. Qualify actual
export hull/transform without altering native geometry. Reuse existing task
construction, native class/dimension checks, adapter, import, refill, final DRC,
invariant/receipt checker and handoff. No production gate opens from source reading
alone, and no assertion that the four new names imply every provider executed.

## Required bounded qualification and comparison

1. Freeze/review source and checkpoint before native work. First native-only
   observation of a complete immutable project copy: original-rule report and
   same-load native/DSN custom-pad identity, both classes and dimensions. Inspect
   actual returned ignored checks and original-source findings. Stop on unexpected
   semantics, unsupported electrical intent, missing project attachment or shape
   mismatch; retain the failure without blanket whitelisting.
2. Small owned native controls use the same polygon class: actual route/import/
   refill positive landing on real copper; deliberately false contact entirely
   inside the concave hull notch must yield exact targeted unconnected findings;
   different-net intrusion must yield targeted clearance/short findings. Bound
   negative rules/settings/UUIDs and preserve originals. Add rotated/back-side
   transformation and changed-pad/pin/net/DSN-hull/report/rule receipt negatives.
   Source/class/ignored-check tampering must reject independently of outer hashes.
   The false-contact control must show that native connectivity closes the hull
   approximation gap, rather than merely trigger an unrelated invariant rejection.
3. Only after those controls pass, freeze a fresh **four-arm development protocol**:
   B0 stock export, B1 corrected common adapter, B2 existing tuned cost portfolio,
   C existing feedback pruning with its own tuned incumbent. Same custom-pad
   transport and original native acceptance in every arm; 120 seconds wall and
   full measured CPU per arm including shared setup/failed trials/checks. Reuse
   current paired/portfolio verifiers; extend only their declared source choice
   and baseline rows. Do not initialize C from B2 for free or choose C's algorithm
   after seeing this board. Keep failures and Pareto tradeoffs; quality deltas
   require valid outputs on both sides. If no gain, report no gain and diagnose
   the actual bottleneck before proposing new mechanisms.

Initial native batch cap: **60 seconds** observation plus **180 seconds** shared
control wall/CPU; no solver until native controls pass. Comparison: four sequential
120-second arms, ≤15 minutes total including bounded setup; one heavy worker,
existing4GiB process-group RSS/512MiB job guards, ≤250MiB new retained artifacts
for the batch, measured early stop if caps approach. No acquisition/spending.
One bounded implementation/review iteration should precede the probe; stop at a
new unqualified geometry/rule mechanism rather than expanding into a general CAD
kernel. This is an engineering scope bound, not a promised elapsed development time.

G3 gains one representative full-board custom-geometry/class failure audit and,
conditionally, a fourth supported input; it does **not** satisfy30–50 independent
families. G4 gains a falsifiable new-input test of existing C beyond strongerB2,
with adapter corrections explicitlyB1; superiority remains conditional on results.
G5 gains real CLI/import/validation/receipt and disposable handoff coverage for
custom pads after the current handoff milestone. GUI, electrical/human review,
family-disjoint evaluation and release remain separate unmet gates.

Reproduction of this static audit: run `python3 -B audit.py` only in a **new copy
of this audit directory without audit.json**; it refuses to overwrite its result.
No earlier result, support classification, source project or history was changed.
