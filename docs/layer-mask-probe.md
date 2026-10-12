# Import-only global layer-mask probe

This optional diagnostic is prospective until ROOT runs the committed helper against the pinned local Freerouting 2.5.0 JAR. It does not admit any production layer preference. The existing profile probe remains the default and retains its settings-only output. No routing, optimizer, fanout, SES or native KiCad process is requested by the new mode.

After source review, commit/push/readback and outside other measured work, ROOT can run:

```sh
python3 -B scripts/probe_engine_profiles.py --layer-mask --output .runs/layer-mask-probe-001
```

The output must be a fresh direct child of this checkout's `.runs`. One foreground JVM uses Java source mode, a 256 MiB maximum heap, one active processor, isolated HOME/tmp and the existing network-denying sandbox. The batch has shared 60-second observed wall and SELF + waited-CHILDREN CPU acceptance ceilings; CPU is not OS-preempted. Runner memory/disk/log guards are polled and can overshoot. Input DSN is capped at 64 KiB, request at 16 KiB, raw observations at 256 KiB, log at 1 MiB and complete output at 10 MiB. No JVM or compiler was run while authoring the draft.

The exact immutable input is `evidence/placement-production-native-001/native.dsn`, SHA-256 `53bcbd2c1978ce85ffaeeabdc28adf0c590d786de63345ccfc1e23b4b61eeb22`. This historical raw export is used only to observe settings transport. It is not a claim that its routing guidance meets board minima. It has four pins, two nets and the unchanged F.Cu/B.Cu physical layer order. All input bytes, pads, keepouts, rules and layers remain intact.

| Case | Requested names | Vector in physical F.Cu, B.Cu order | Required semantic result |
|---|---|---|---|
| source-all | F.Cu, B.Cu | true, true | Accept mapping |
| front-only | F.Cu | true, false | Accept mapping |
| back-only | B.Cu | false, true | Accept mapping |
| reversed-mapping-negative | F.Cu, using deliberately reversed mapping metadata | false, true | Reject mapping; retain successful B.Cu readback |

Each case creates fresh DefaultSettings + DsnFileSettings + CliSettings and a fresh imported board. Source class/name/priority and exact parsed CLI arguments are recorded. This is not complete scheduler parity: no API, environment, JSON, RULES or SES override source is present. Autorouter and optimizer are explicitly false. The native physical board is never edited or saved.

The observer separately records nullable `layers[i].routable` and `getLayerActive(i)` before initialization, after `applyBoardSpecificOptimizations` plus the no-op netclass-exclusion step, and after `applyBoardSpecificOptimizationsIfNeeded`. Both raw and accessor masks must be exact Booleans at all three boundaries. The complete bounded item identity/layer/net census and physical layer metadata must remain unchanged. The observer never calls `setLayerCount` or repairs a failed setting. Unexpected bounded counts and all four failed/successful raw case rows are retained.

The safe named-mask builder accepts exactly one Boolean per physical layer. Unknown/duplicate names, short/long vectors and Boolean aliases are rejected before argv construction. The fixed four-case request uses declared known orders directly; the safe generic builder is exercised by pure controls only. The negative deliberately uses the reversed order, proving that a valid numeric mask cannot be called front-only without its name/index binding.

The pinned primary-source basis is Freerouting commit `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`, with exact cached source/declaration digests in `LAYER_BASIS`. ReflectionUtil uses partial array assignment and permissive Boolean conversion; RouterSettings may resize/init the layer array and substitutes true for null. These are hypotheses motivating observation, not actual results. DsnFileSettings' InputStream/String constructor is confirmed by `.runs/layer-mask-api-001/javap.log`; DsnReader/Success/board/item APIs have prior pinned declarations. This diagnostic requires those local cached files and fails if any pin differs. The external GPL engine is not redistributed in this source change.

The runner reuses the existing bounded importer IO, strict JSON, cancellation and inventory helpers. It verifies committed helper/core bytes, HEAD and pinned tools, copies exact source/request/DSN, and captures the complete worker stage before parsing. Final checks read the HEAD witness before hashing tools/source/API/DSN material, retain bounded evidence scans on both sides of that material check, then check canonical and in-memory result equality and final resource caps. Positive/partial summaries invalidated by cancellation, stale material or cap crossing are preserved under unique names. SIGINT/SIGTERM handlers are scoped/restored. Stored timing precedes final publication; acceptance caps include the checks. These are finite samples of mutable files, not authentication or protection against an arbitrary concurrent writer.

Pure controls use explicitly synthetic worker output and real temporary files. They cover named mapping, null/accessor disagreement, bad identity/count/type, source/API pins, completed-stage mutation, final source/result mutation, correction failure, cap crossing and actual self-SIGINT/SIGTERM inside the scoped handler. They do not establish engine behavior. First authored tests correctly rejected the macOS `/var` alias in temporary paths; the tests now resolve that alias and keep the original failing log.

A passing actual batch would establish only this two-layer import/merge/initialization mask transport. Routing-stage enforcement, optimizer enforcement, via and terminal feasibility, multilayer boards, per-net constraints and original constraints/native validation remain separate gates. Saved routing preferences continue to accept only `layers: "source_all"` until those gates are measured.
