# Routing foundation research

Checked October 9, 2026 (America/Los_Angeles). This is a primary-source inspection,
not a benchmark, native integration qualification, or proof of geometry fidelity.
No engine was installed, built, or run by this research subtask. Runtime evidence
belongs in the lead integrator's run receipts. Historical results remain leads.

## Foundation decision for the first experiment

Use the released Freerouting 2.5.0 JAR in a bounded local worker, then import into
the installed KiCad and validate against preserved project rules. This selects a
baseline, not the eventual research architecture. The current release is a more
appropriate B0 than an old Freerouting release. Keep an engine-neutral candidate
contract so KiCadRoutingTools can be tested without replacing the validator.

The strongest next inexpensive alternative is KiCadRoutingTools 0.23.0: native
KiCad-file input, a small macOS arm64 prebuilt, and explicit congestion recovery
operators. PCBWorld-Engine offers deeper push-and-shove control but requires a
KiCad 9.0.8-derived build and a format-compatibility experiment before use with
KiCad 10. Topola is useful as a complementary planar experiment; the inspected
CLI routes layer 0. tscircuit has a useful topology/capacity architecture but needs
a substantial geometry/rules adapter. OrthoRoute declares a specialized backplane
scope, so it is not the default alternative for ordinary two/four-layer boards.

These rankings are engineering inferences from the sources below. They must be
revised after short capability experiments and the development failure audit.

## Freerouting acquisition and runtime contract

The [latest-release endpoint](https://api.github.com/repos/freerouting/freerouting/releases/latest)
returned `v2.5.0`, published `2026-10-05T15:58:39Z`. Its
[tag](https://api.github.com/repos/freerouting/freerouting/git/ref/tags/v2.5.0)
points to `b647a2f824cfbc54bc4dcaee71b03b7cd945eb76`. The separately inspected
moving `master` was `853ce4f21377669d77daeafbab0f504cc7ae063a`; do not silently use
that newer source as the released binary's specification.

| Official artifact | Compressed/download bytes | SHA-256 from release API |
|---|---:|---|
| [JAR](https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar) | 64,599,107 | `f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7` |
| [macOS arm64 CLI tarball](https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-cli-2.5.0-macos-arm64.tar.gz) | 20,891,568 | `515eded3c615c13eaa336d5044f5df042bdb8d67181aac30fd0f7a457f1f93a7` |
| [macOS x64 CLI tarball](https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-cli-2.5.0-macos-x64.tar.gz) | 20,295,019 | `7a0d039902469d21766f953da01c463479e374e190797ce4a8b0bbaf2fe1a990` |

Verify downloaded bytes independently. Keep binaries outside Git. The
[tagged license](https://github.com/freerouting/freerouting/blob/v2.5.0/LICENSE)
contains GPL version 3. Distribution needs appropriate source and notices; using
a child process does not by itself settle every distribution obligation.

The [release notes](https://github.com/freerouting/freerouting/releases/tag/v2.5.0)
describe revised optimization, plane handling, native binaries, and KiCad IPC.
Their PCBench results are upstream claims, not this project's measured native
acceptance rates. They do not establish that original KiCad constraints survived
every interchange. The old adapter mechanisms require fresh ablations.

### Offline operation requires more than `-da`

The source has an important gap between local computation and no networking:

* [`GlobalSettings.java`](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/GlobalSettings.java)
  maps `-da` to `usageAndDiagnosticData.disableAnalytics=true`.
* [`AnalyticsBootstrap.java`](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/startup/AnalyticsBootstrap.java)
  uses that flag and profile consent to disable analytics, but initializes the
  analytics machinery separately from version checking.
* [`Freerouting.java`, lines 627–631](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/Freerouting.java#L627)
  unconditionally starts a version-check thread. The
  [dedicated CLI entry point, lines 61–65](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/cli/FreeroutingCli.java#L61)
  does the same. Calling the CLI main class alone does not avoid it.
* [`VersionChecker.java`](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/util/VersionChecker.java)
  sends a request to GitHub's release API. No offline flag was found in these
  inspected startup paths.

Therefore use an actual per-process network-denial mechanism and test it. On this
Mac the lead selected an additional `sandbox-exec` network restriction; its
verification receipt, not this source inspection, establishes enforcement.
Do not describe a proxy setting or an analytics flag as an OS network boundary.
No server, API account, public board upload, or model call is needed for routing.

### Bounded settings and command template

Source-checked knobs, requiring a runtime smoke test:

| Setting | Source and interpretation |
|---|---|
| `--user_data_path=ABS_DIRECTORY` | [CLI documentation](https://github.com/freerouting/freerouting/blob/v2.5.0/docs/command_line_arguments.md); equal-sign form, isolates settings and job data from the user's normal profile |
| `--router.autorouter.max_passes=30` | [AutorouterSettings](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/AutorouterSettings.java); zero is unlimited |
| `--router.optimizer.max_threads=1` | [OptimizerSettings](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/OptimizerSettings.java); limits the optimization pool |
| `--router.optimizer.max_passes=10` | Same optimizer source; a pass cap is not a wall-time cap |
| `--router.optimizer.timeout=30s` | Same optimizer source; optimizer-stage timeout |
| `--router.job_timeout=60s` | [RouterSettings](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/settings/RouterSettings.java); internal job-timeout setting |

`AutorouterSettings` explicitly says its `max_threads` field is not read by the
autorouter pass. Do not infer that this one knob controls all engine concurrency.
The older CLI documentation lists optimizer strategies removed by the 2.5.0
release; prefer current source and runtime help over copying those examples.
`-drc` selects DRC-only mode, so do not append it to the normal route invocation.

Proposed invocation shape (replace uppercase placeholders with audited absolute
paths; this is an engine recipe, not a shipped project command):

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  JAVA25 -Xms128m -Xmx2g -XX:ActiveProcessorCount=1 -Djava.awt.headless=true \
  -jar FREEROUTING_JAR \
  --gui.enabled=false --api_server.enabled=false --mcp_server.enabled=false \
  -da --user_data_path=ABS_RUN_CONFIG --logging.file.enabled=false \
  --router.autorouter.max_passes=30 --router.optimizer.max_threads=1 \
  --router.optimizer.max_passes=10 --router.job_timeout=60s \
  --router.optimizer.timeout=30s -de ABS_INPUT_DSN -do ABS_OUTPUT_SES
```

Still enforce an external process-tree deadline, bounded output, disk budget, and
RSS observation. Java heap size is not total process RSS. Inspect unknown-setting
warnings, output existence, exit semantics, and native acceptance. Count startup,
failed attempts, import, refill, and validation in equal-budget comparisons.

## Alternative engines: checked facts and missing proof

### KiCadRoutingTools

Latest release [v0.23.0](https://github.com/drandyhaas/KiCadRoutingTools/releases/tag/v0.23.0)
was published October 8, 2026; moving main was
`7adb13fece3c1f3187592e5747213abb668534e9`. The
[license](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/LICENSE)
is MIT. The arm64
[Rust extension](https://github.com/drandyhaas/KiCadRoutingTools/releases/download/v0.23.0/grid_router-macos-arm64.so)
is 1,039,632 bytes, SHA-256
`ed667cfbde051e3824c25a21635b322b5adec10d5b1475ad80f1c3e4d066d8d7`.
The full plugin archive is 14,844,957 bytes, SHA-256
`d325f617492bd69943e50dd9f5a9119d328c854e33ab54cac4c96e90d05c52a1`.

The [README](https://github.com/drandyhaas/KiCadRoutingTools/blob/7adb13fece3c1f3187592e5747213abb668534e9/README.md)
describes grid A* routing, native `.kicad_pcb` CLI inputs, KiCad 9/10 support,
plane repair, and per-net control. Those capabilities have not been qualified in
this reconstruction. Avoid its placement, pad-swap, and inferred power-rule
workflows when testing fixed constraints.

[`rust_router/Cargo.toml`](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/rust_router/Cargo.toml)
uses PyO3 `abi3-py39`, making the existing KiCad Python 3.9 a plausible loader,
subject to an actual import. The
[requirements](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/requirements.txt)
list NumPy, SciPy, Shapely and rendering-related Pillow. Audit and pin dependency
resolution in a project environment; do not run its installer into KiCad's bundle.

The [rip-up documentation](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/docs/rip-up-reroute.md)
already describes frontier blocker attribution, endpoint and bidirectional
ranking, a soft-cost mincut probe, corridor avoidance, escalation, and restoration.
These are substantial prior art for our proposed repair hypotheses. It also
warns that current defaults may rip small pre-existing nets, and that selected-net
scope alone does not protect other copper. `KICAD_RIP_PREEXISTING=0` and
`KICAD_FINALIZE_RIP=0` disable two paths; oracle reconnect escalation requires
additional inspection. Never substitute its improvement gate for our invariants.

The [net-ordering documentation](https://github.com/drandyhaas/KiCadRoutingTools/blob/v0.23.0/docs/net-ordering.md)
documents crossing-aware maximum-planar-subset ordering, inside-out BGA order,
manual order, reverse rounds, and layer swaps. A portfolio of these established
operators must be compared with equal-budget uniform selection before any claim
that our selector contributes useful strategy.

### PCBWorld and PCBWorld-Engine

Inspected environment revision:
`b3d62f5c37e7528670d112e03d9a90029f23f4f3` (README version 1.0.1). Its
[engine gitlink](https://api.github.com/repos/LGAI-Research/PCBWorld/contents/engine?ref=b3d62f5c37e7528670d112e03d9a90029f23f4f3)
pins `7a31e0c982a84fcda75be3ce69966027135bd7c1`. GitHub latest-release endpoints
returned 404; a README version is not a GitHub release binary.

The environment [license](https://github.com/LGAI-Research/PCBWorld/blob/b3d62f5c37e7528670d112e03d9a90029f23f4f3/LICENSE)
is BSD-3-Clause; the engine
[license](https://github.com/LGAI-Research/PCBWorld-Engine/blob/7a31e0c982a84fcda75be3ce69966027135bd7c1/LICENSE)
is GPLv3. Dataset board rights remain separate.

The [environment README](https://github.com/LGAI-Research/PCBWorld/blob/b3d62f5c37e7528670d112e03d9a90029f23f4f3/README.md)
exposes net selection, start-route, make-line, and end-net actions, including a
routing-mode parameter. It supports a deterministic controller experiment without
training or paid model access. Its setup script performs much more work than
needed for a capability spike and must not be run blindly.

The [engine README](https://github.com/LGAI-Research/PCBWorld-Engine/blob/7a31e0c982a84fcda75be3ce69966027135bd7c1/README.md)
describes a KiCad 9.0.8 fork, a pybind11 module and separate Unix-socket worker.
Requests use length-prefixed pickles and have no per-call timeout; keep the socket
private and kill the worker on deadline. The upstream build-time number is for a
64-core machine, not this Mac. Native KiCad 10 round-trip compatibility, protected
item semantics, dependency footprint, and buildability here remain untested.

### Topola

The [official site](https://topola.dev/) links
[Codeberg `topola/topola`](https://codeberg.org/topola/topola), with the
[`mikwielgus/topola` GitHub repository](https://github.com/mikwielgus/topola)
identified by its README as a mirror. The default branch is `develop`, inspected
at `666e06cfd7ba1f1e5daf700288acb9e0a4f84ceb`; Cargo package version is 0.1.0.

The [README](https://codeberg.org/topola/topola/src/commit/666e06cfd7ba1f1e5daf700288acb9e0a4f84ceb/README.md)
identifies MIT code with specific dual-licensed asset/math-file exceptions, backed
by [MIT license text](https://codeberg.org/topola/topola/src/commit/666e06cfd7ba1f1e5daf700288acb9e0a4f84ceb/LICENSES/MIT.txt).
Retain per-file SPDX notices when copying code.

The [installation guide](https://codeberg.org/topola/topola/src/commit/666e06cfd7ba1f1e5daf700288acb9e0a4f84ceb/INSTALL.md)
documents a Cargo CLI build and DSN-to-SES execution. The inspected
[CLI source](https://codeberg.org/topola/topola/src/commit/666e06cfd7ba1f1e5daf700288acb9e0a4f84ceb/crates/topola-cli/src/main.rs)
selects layer 0 and passes `principal_layer: 0` to planar autorouting. Thus do not
assume this CLI is a drop-in general multilayer competitor. A planar subset may
test topological complementarity, but arc/clearance/session round trips need native
verification. No local build was attempted.

### tscircuit autorouter

Inspected revision `c81d1a8864081bd4226ef1b831c05b8284ae63a8`;
[`package.json`](https://github.com/tscircuit/tscircuit-autorouter/blob/c81d1a8864081bd4226ef1b831c05b8284ae63a8/package.json)
names `@tscircuit/capacity-autorouter`, version 0.0.965. Its
[license](https://github.com/tscircuit/tscircuit-autorouter/blob/c81d1a8864081bd4226ef1b831c05b8284ae63a8/LICENSE)
is MIT. A package source version is not proof of an audited published artifact.

The [README](https://github.com/tscircuit/tscircuit-autorouter/blob/c81d1a8864081bd4226ef1b831c05b8284ae63a8/README.md)
describes a hypergraph/capacity pipeline with stepwise solver operation and
`getOutputSimpleRouteJson()`. The
[actual input types](https://github.com/tscircuit/tscircuit-autorouter/blob/c81d1a8864081bd4226ef1b831c05b8284ae63a8/lib/types/srj-types.ts)
carry rectangular obstacles, bounds, layer-accessible terminals, trace widths,
and via information. They do not constitute an established faithful native KiCad
rules/project interface. Arbitrary outlines, copper graphics, custom pads,
regional rules and planes need mapping or explicit rejection. This makes a
restricted geometry spike more sensible than immediate whole-corpus integration.

### OrthoRoute

Latest [release](https://github.com/bbenchoff/OrthoRoute/releases/tag/v1.0.0)
was v1.0.0; inspected moving main was
`9e06f2d567f66187240472e12838d42378753ab1`. The
[license](https://github.com/bbenchoff/OrthoRoute/blob/v1.0.0/LICENSE) is MIT.

The [README](https://github.com/bbenchoff/OrthoRoute/blob/9e06f2d567f66187240472e12838d42378753ab1/README.md)
explicitly targets regular, large multilayer backplanes and BGA escape using a
Manhattan lattice and PathFinder. It describes CUDA and Apple Metal paths, KiCad
10 IPC, and ORP/ORS exchange. These are upstream descriptions, not this project's
Mac or GUI tests. Its stated workload and blind/buried-via examples are outside
our initial ordinary through-via scope. No cloud workflow is needed or authorized.
Keep it as a later specialized comparator if corpus evidence warrants it.

## Next falsifiable spikes

Run these sequentially after the native validator can reject invalid candidates.
Use development fixtures only and record all failures and unsupported inputs.

1. **Freerouting fidelity audit:** stock, graphics-only, planes-only and combined
   variants on identical frozen native snapshots; 60 seconds per engine attempt,
   with the complete pipeline capped separately. Prediction: particular native
   obstacles/plane cases expose input loss. Falsification: current stock already
   preserves the required geometry/connectivity or a correction introduces false
   connectivity. A one-board gain establishes only a development regression.
2. **KRT capability spike:** load the pinned extension, route one simple project,
   then one copper-graphics/plane/protected-track fixture. Keep original rules and
   compare only candidate tracks/vias. Prediction: complementary A* ordering/ripup
   solves at least some Freerouting failure classes. Falsification: import/geometry
   failures, equivalent-cost results, or regressions dominate. Stop after a bounded
   15-minute exploratory batch; do not let a setup fallback start an unbounded build.
3. **Repair/selection hypothesis:** only after actual failure classification,
   compare a small deterministic operator selector against a uniform equal-budget
   portfolio and longer B1. Include failed work and validation costs. Prediction:
   failure-frontier features identify useful repairs early enough to improve valid
   completion. Falsification: no advantage over uniform allocation, or selection
   overhead erases gains. Remove the selector if unsupported. The operators above
   are prior art; any contribution would need measured selection or constraint-
   preserving integration value, not a renamed rip-up method.

No fresh benchmark result, general improvement, trained model, native GUI
qualification, physical validation, or third-party endorsement is established by
this document. Data acquisition and artifact-specific licensing remain separate
gates; repository licenses do not automatically clear every included board.
