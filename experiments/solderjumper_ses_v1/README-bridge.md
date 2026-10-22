# Two-scene nonrouting SES selector

The first current-Native source prerequisite stopped before compilation/routing:
[retained failure](../../evidence/solderjumper-ses-native-prerequisite-001.json).
KiCad rejected two quoted pin-type enum atoms in each newly authored schematic.
Fresh002 fixtures correct only those tokens; PCB/PRO/PRL bytes and every other
schematic atom remain unchanged. The first failed verifier's incorrect expectation
of four changed atoms is also retained. Current controller/worker pins select the
002 preparation explicitly, with unchanged180s/30s/25s/resource limits. No result
or production admission is inferred from the correction or pure checks.

The corrected002 source checks are retained in
[the second prerequisite receipt](../../evidence/solderjumper-ses-native-prerequisite-002.json):
positive0opens/0blocking/4warnings/0exclusions and deliberate false-contact
negative1/0/5/0, with current full-schematic Native checks and original rules.
The following compile failed on the new selector's POSIX permission-attribute
argument, before any Java observation, SES roundtrip or routing. The one-line
type correction is not evidence that compilation or later stages pass.
The explicitly pinned execution002 continuation reuses those actual source
proofs through the shared readback helpers, retaining both failed runs and
deducting their complete5.64wall/4.85CPU from the original180s limits. It has a
fresh output directory, the same25s reserve/one30s engine attempt, aggregate
resource caps across old and new artifacts, and no implicit retry.

The [completed diagnostic](../../evidence/solderjumper-ses-native-diagnostic-001.json)
now records both actual nonrouting SES roundtrips and one route-empty positive
CLI attempt. Positive and generated finals are0/0/4/0; the unchanged negative is
1/0/5/0 with its expected concave-notch open. All preserve four ignored checks,
original project/schematic/rules, exact body geometry and final Native bindings.
The generated route reaches the bodies beyond their anchors. Three complete
executions including failures cost26.56wall/23.78CPU; preparation, pure tests,
reporting and authoring/review are additional. The [stored-material AI review](../../evidence/solderjumper-ses-native-material-review-001.json)
and shared final-DRC readback found no material discrepancy. These are narrow
diagnostic results, with every accepted/production flag false. Different-net
solder-jumper separation, Cheapino and production custom pads remain unqualified.
Do not replay these completed scenes as new experiments.

`SesBridge.java` remains experimental. It selects
only `back90-positive` or `back90-false_hull`, then delegates to the retained
`MixedClassProbe.run(raw, true, row, false, sesPath)`. This uses the existing
HeadlessBoardManager load, SettingsMerger, awaited post-load work, observation and
bounded SES writer. It does not copy that lifecycle or invoke routing, Native,
optimization, the local250 matrix rewrite or the adapter mode. The old main
entry point couples SES output to the original-PIC local250 mode; this selector
exists solely to call the already available nonlocal overload for the two tiny
Default scenes.

The controller must freeze the complete paired PCB/PRO/SCH fixtures, exact
source-faithful target and DSN edits, input/code/tool/runtime hashes, output
ownership and shared budget before execution. The selector validates the scene
name and input filename; those names do not authenticate geometry or source.
Its JSON always has `accepted=false`, `production_admitted=false` and
`custom_pad_support_qualified=false`. Both a successful process exit and the
controller's independent material/SES/Native checks are required.

## Compilation inputs and pinned APIs

Compile these existing source files together into one fresh class directory:

- `experiments/custom_pad_area_probe_v1/AreaContactProbe.java`
  SHA256 `5c5a86fff2f9b6a145db3a521c0187217180b7aef7119c69be4acc2941fdf924`.
- `experiments/pic_mixed_transport_probe_v1/MixedClassProbe.java`
  SHA256 `04bbc93e2803516064f61ef7cae1b41050502f5e56d597da5c4e572a74b2d9e9`.
- `experiments/pic_mixed_transport_probe_v1/ExactPointWitness.java`
  SHA256 `662607bbd68a7e45682014bc5af8c05798c177fd3a645c5e73650b5e8ddc7f46`.
  This same-package source is required by the retained MixedClassProbe class
  even though this selector does not enable its optional exact/adapter mode.
- `experiments/solderjumper_ses_v1/SesBridge.java`, whose actual source hash must
  be added to the frozen controller protocol.

Use only the pinned JAR
`.tools/freerouting-2.5.0.jar`, SHA256
`f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7`.
The existing compiler convention is `javac -J-Xmx256m -proc:none -classpath JAR
-d FRESH_CLASSES` followed by all four source paths. Preserve their package
layout, freeze every generated class and use the retained pinned Temurin25
compiler/runtime records. No engine source or binary is vendored here.

The required nonrouting signatures already exist in the cached
`.runs/pic-clearance-api-observation-001/javap.log` (SHA256
`7eaddfca0f3ddff2624a3d11754131136a48975a70d0761497e9d3207335e1b0`)
and the previously compiled retained helpers. They include
`HeadlessBoardManager(RoutingJob)`, `loadFromSpecctraDsn`, `getRoutingBoard`,
`RoutingJob()` and `SesWriter.write`. No additional javap class is required for
this selector. The manager's save calls the actual SesWriter; its returned value,
stream close, bytes/hash and post-write observations remain in the delegated row.
The retained writer uses the literal design name `original-mixed.dsn`; the
controller must bind that actual SES metadata and its source mapping explicitly.
The selector records it rather than pretending it equals the scene filename.

## Invocation and observations

The interface is one scene per child:

```text
SesBridge back90-positive /frozen-inputs/back90-positive.dsn /fresh-output/positive
SesBridge back90-false_hull /frozen-inputs/back90-false_hull.dsn /fresh-output/negative
```

The output parent must exist and each scene output directory must be absent.
The selector creates it exclusively with0700 permissions. Inputs must be regular,
single-link files without symlink ancestors, at most64KiB, with stable inode,
size, modification time and content across the child. It writes only `raw.ses`
and `observations.json`; failed partial output is retained. The unchanged writer
limits each SES to4MiB before writing and uses CREATE_NEW; JSON is limited to
256KiB. These bounds do not replace the controller's original10MiB aggregate,
1024-file/2048-entry limits or its owner/inode/material/final publication seals.

The controller supplies the existing no-network sandbox, fresh private HOME/TMP,
256MiB Java heap,262144-byte stage logs,1GiB polled group RSS, one worker and
`min(existing stage cap, shared remaining)` child timeouts. All compilation,
deferred loader work, both scene children, later Native checks and publication
consume the shared180s wall/full-parent-plus-reaped-child-CPU envelope; reserve25s
before work that needs finalization. Java's await has no independent hard
deadline: the existing runner must enforce timeout/cancellation and reap the
owned process group. A killed/nonzero/truncated child or generic exception is
not the deliberately negative Native result. This source authoring ran none of
these commands.

The delegated row records actual settings before Headless loading and after its
loader adjustments and awaited post-load work. It records item/net/layer/fixed
class IDs, class names, raw and compensated clearance matrices, area contours,
anchor/item contacts, net terminal IDs and connected sets. It also preserves
route geometry before/after SES and actual area obstacle predicates. This is the
available observation contract; it does not invent a new final internal-graph
API or establish a scheduler's later final settings merge. The caller must audit
these observations against the exact frozen source/target and use actual Native
connectivity as final authority. The selector additionally refuses if routing or
optimization is enabled, obstacle handling is not true, the local250 rewrite is
reported, awaited loading is absent or SES writing/closing is incomplete.

Only the controller may remove the exactly matched two generated area records
from a separate import SES, with exact reverse-edit and all-other-route/atom
accounting; preserve raw SES. Existing fixed-placement handling removes only
placement. The positive must preserve its known non-anchor landing; no routing
may heal the unchanged false-hull negative. Import into a route-empty copy,
restore the exact original tree and run current original-rule refill/full-SCH,
field/PRL, Default, metrics and final candidate-bound Native checks. This bridge
does not perform or waive any of them.

## Existing evidence and routing boundary

Historical `.runs/pic-custom-ses-roundtrip-001/summary.json` (SHA256
`c27b3b5203b915b0b974d42b028060bcf4bdbdb34d871f08c05a7813d34b87ca`)
is the full original PIC source, not these two owned scenes; it failed before
Native with `engine route shape metadata differs`. Follow-up native001
(`72e336678b22eaa3ad1a592fc4bb387514a5e9db380cbc7267ea7f801c173b23`)
failed the project/rule/file-set check. Native002
(`acc1153af85f76fe37fd7aab02b399aa9d19d71dd6358fefc56c21bd6ccbf0e3`)
remains `observed-incomplete`, not routing/custom-pad qualification. These are
performed historical boundaries, never relabeled as wholly unperformed work or
rerun by this selector. The exact current10.0.7 full-SCH two-scene boundary still
requires its separately frozen execution and cannot reuse those Native results.

There is no Java routing mode here. Existing SelectiveRoutingProbe hardcodes a
60s original-PIC selective path; its cached RoutingPipeline signature alone does
not justify silently converting that path to this30s experiment. After both
roundtrips pass, the lead may use exactly one separately frozen existing
standard CLI30s attempt on the positive route-empty task, with pinned settings,
network denial and the same shared budget. This selector does not claim its
loader observations describe the CLI's final routing state. Preserve and audit
the actual emitted SES and imported candidate; final Native remains decisive.

The two custom bodies in these scenes share CONTACT. Cheapino's matching
SolderJumper pad pairs use different source nets; this slice does not establish
their separation, Cheapino eligibility or product admission. An anchor-only
generated landing is limited routing evidence; the prewired roundtrip separately
tests the non-anchor contact. No mixed-class/local-override/arbitrary-pose/holes,
electrical, routing-quality, comparison, C novelty, human or release claim follows.
Fixture/source rights and immutable originals remain the controller's existing
requirements; this directory contains only owned selector code and metadata.
