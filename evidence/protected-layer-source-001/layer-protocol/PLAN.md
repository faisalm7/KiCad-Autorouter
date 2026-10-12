# Bounded global layer-mask observation plan

Status: proposed only. No Java/JVM, native, routing, compilation, network or tests ran for this plan. No production preference/support changes are proposed here. Source pins are in `source-pins.json`.

## Minimum implementation

Extend the existing `EngineProfileProbe.java` and `probe_engine_profiles.py` with an explicit optional import-only layer-mask mode; preserve the current settings-only mode and receipt meaning. Reuse `autorouter.runner.run`, its process-group cleanup and existing sandbox invocation. Add array-aware observation only for the exact `router.layers.routable` field, not a generic reflection rewrite or new job framework.

Use one immutable, already exposed, owned two-copper-layer fixture DSN: `evidence/placement-production-native-001/native.dsn`. Copy its exact bytes once into the new bounded run. Its declared signal-layer order is F.Cu index 0, B.Cu index 1. Do not remove layers, reorder DSN declarations, rewrite stackup, filter pads/vias, or save a board. Keep the original board/project and complete existing evidence unchanged. This is settings transport observation, so importing this historical raw DSN does not assert its routing constraints are sufficient.

One JVM, four sequential cases, fresh settings and a fresh imported board for each. Reuse the proven `DsnReader.readBoard(new ByteArrayInputStream(raw), null, null)` / `BoardReadResult.Success` / `RoutingBoard` / `awaitPostLoad()` sequence from `AreaContactProbe.java`. Record importer warnings. Never instantiate or start `RoutingJobScheduler`, routing threads, optimizer, fanout or a board editor. Explicitly disable autorouter and optimizer in each CLI request as an additional guard; no output SES is requested.

## Cases and exact expectations

| Case | Requested allowed names | CLI mask in unchanged F.Cu,B.Cu order | Expected post-init result |
|---|---|---|---|
| source-all | F.Cu, B.Cu | true,true | both active |
| front-only | F.Cu | true,false | only F.Cu active |
| back-only | B.Cu | false,true | only B.Cu active |
| reversed mapping negative | F.Cu, but deliberately mapped through reversed B.Cu,F.Cu metadata | false,true | engine observes B.Cu active; semantic/name contract rejects |

The fourth case is an expected mapping rejection, not an engine-parser failure. It uses the same board bytes as the others and proves why a syntactically valid vector cannot be called “front-only” without name/index binding. Retain its successful raw import/readback and the explicit rejection separately. No physical layer-order mutation is necessary. A pure companion test should show that a correctly name-keyed builder gives true,false regardless of the order of an input dictionary/list of name-value entries.

For every case, read raw nullable `layers[i].routable` values and independently `getLayerActive(i)`; the latter alone substitutes true for null. Read before board initialization and after `applyBoardSpecificOptimizations(board)` (and its ordinary no-op exclusions step with no exclusions requested). Repeat the “if needed” initialization once to detect a reset. Require exact layer count, unique names, index, signal status and enabled/disabled set, strict Boolean values, and identical physical layer metadata/item census before/after settings initialization. Do not call `setLayerCount` or setters to repair a failed observed mask.

## Merge fidelity and known traps

The current probe merges only DefaultSettings + CliSettings and never loads a board. Production scheduler additionally includes DsnFileSettings, any explicitly enabled sources, and highest-priority per-job ApiSettings before board initialization. For the narrow isolated probe, use Default + DSN + CLI with no JSON, environment, RULES, SES or API overrides, and record that exact source list. Do not claim this reproduces the full scheduler or proves later preferences integration preserves the mask. If the preference path adds ApiSettings, a separate same-request readback at that integration boundary will be required before routing.

The cached scheduler proves DsnFileSettings is constructed from a new input stream and filename, but its public constructor declaration is not among the captured API listings examined here. ROOT should confirm that declaration with one bounded actual-JAR javap request before writing the direct call, or treat a reflective missing-method error as failed qualification; do not invent a signature or silently drop the DSN source. Existing DsnReader/Success/board APIs already have retained actual declarations/import observations.

Pinned source explains the hypotheses, not an actual mask result: ReflectionUtil splits comma arrays and uses `min(existing length, token count)`, so short or long masks can be partially applied. Its Boolean conversion accepts 0/1 and turns other invalid strings into false. Enforce exact typed Boolean count and exact known layer-name set before constructing argv; reject duplicate/unknown names, missing entries, extra entries and non-Boolean tokens. RouterSettings preserves explicit false on signal layers, defaults null to true, disables non-signal layers, and may resize mismatched arrays. Its public `layers` field is transient: observe it explicitly rather than trusting whole-object Gson output. Calling `setLayerCount` later can reset flags.

## Bounds, capture and focused falsifiers

ROOT promotes reviewed source/protocol and verifies its checkpoint before execution. One foreground batch: 60 seconds shared observed wall and full parent+waited-child CPU acceptance ceilings, one worker, Java `-Xms32m -Xmx256m -XX:ActiveProcessorCount=1`, isolated HOME/user.home/tmp, existing network-denying sandbox. Input DSN <=64 KiB, exactly four cases/two layers, log <=1 MiB, total new output <=10 MiB; retain raw failures/cancellation. Use runner group memory/disk guards explicitly, with honest polling overshoot; do not describe measured CPU acceptance as OS preemption.

Freeze source/HEAD, request, original DSN, copied DSN, JAR and Java pins before starting. Capture complete worker JSON/process/log inventories immediately on return, before parsing them; validate exact case denominator and no duplicate JSON keys/nonfinite values. Recheck source, tools and captured material after subprocess metadata calls and before/after final summary publication. Preserve invalidated positive summaries and publish failed/cancelled on stale evidence, cap crossing, interrupted write or failed final checks. Use existing guarded publication pattern rather than another helper framework. The old profile script's simpler final checks alone do not establish these guarantees.

Pure tests: exact/reversed name mapping, bad vector arity/types, nullable-field versus getLayerActive disagreement, wrong imported layer order/name/count, changed DSN/process/result bytes after capture, and interruption/cap crossing during final publication. Actual batch success requires the first three masks to remain exact after board setup and the fourth semantic mismatch to be rejected while raw readback remains truthful. No extra routing controls run in this phase.

## Claim limit and next gate

A passing observation would establish only pinned-JAR CLI/merge/global-mask transport through initialization for this two-layer fixture. It does not prove all router/optimizer stages honor the mask, that vias/terminal access remain feasible, four-layer behavior, per-net layer rules, native routing validity, route quality or current production support. The next separate gate is one controlled end-to-end routing case plus forbidden-layer copper readback and native validation under unchanged original constraints. Do not generalize layer-mask support or widen production gates from this probe alone.
