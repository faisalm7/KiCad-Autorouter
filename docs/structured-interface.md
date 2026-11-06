# Local structured interface

The graphical controller calls the same offline CLI as Terminal users. It passes argument arrays, exact saved project paths and an explicit captured JSON preset; it does not invoke a shell or send a board to a service. The CLI prints JSON and writes durable receipts in a fresh output directory. See [saved settings](routing-preferences.md) for the versioned input contract.

Runtime075 adds [saved-project inspection and routing proposals](design-workflow.md): `inspect-project`, `inspect-project-check`, `propose-route` and `design-tool-schema`. These reuse the existing Native/process/snapshot/preview checks. Proposals grant no execution or approval authority. The optional explicit local model client can request only `propose_route`; it has no route, accept, warning-acknowledgement, shell or file-write tool. Runtime074 does not contain these commands. Runtime075 has installed Native/CLI subset evidence; its GUI106 finite core is recorded; live model qualification remains pending.

| Action | CLI | Result / authority |
|---|---|---|
| Check environment | `doctor` | Actual pinned tool/version/hash readiness, successful KiCad/Python/Java probes and recognizable Java version output; no board validation. |
| Preview support and choices | `preview BOARD --settings FILE` | Resolved source identity/settings/protected-route counts; static only. |
| Route a copied project | `route BOARD --settings FILE --output NEW` | `NEW/result.json`; `accepted`, status, source/candidate hashes, tools, all native findings and compute. Exit0 alone is insufficient. |
| Experimental Improve | `improve BOARD --settings FILE --seconds 420 --output NEW` | Narrow KiCad10.0.7 whole/native/tuned/both/source_all/default-score2Cu/flat method; see the exact [settings admission](routing-preferences.md). Incumbent, trials, final checks and40s internal return reserve share the whole budget; no guaranteed improvement or fallback on stale/cancel/refusal. |
| Experimental thermal recovery (CLI) | `recover BOARD --seconds 420 --output NEW` | Fixed selected7 whole/native/standard/both/all-source method;90–900 seconds cover incumbent, repair and final validation. It accepts no arbitrary `--settings` preset. Own parent/Native/original checks remain authoritative; no automatic fallback after stale/cancel/refusal. |
| Verify retained result | `check-result RESULT` | Complete shared source/evidence/original-design consistency checks; does not run a new DRC. |
| Build a disposable review | `review-copy RESULT --render --output NEW` | `review.json`, complete project, before/after copper plots and local HTML; original routing is review-only. |
| Record explicit intent | `review-choice REVIEW --choice accept\|reject --output NEW` | `choice.json`; user intent is not a PCB/electrical certificate. Rejection cannot authorize export. |
| Produce a handoff | `review-export CHOICE --seconds 120 --output NEW` | `export.json` and separate complete project after fresh Native refill/fullSCH/original-rule validation. |
| Experimental live warning review | Add `--warning-review-stdio` to `review-export` | Opt-in same-process exchange described below. Strict refusal remains the CLI default; a pending challenge is not an export. |
| Check handoff evidence | `review-export-check EXPORT` | Current candidate/source/report and file consistency. Any later edit requires new validation. |

Commands returning failure, cancellation, stale inputs, unsupported features or exhausted budgets cannot authorize a positive next step. SIGINT/SIGTERM requests cancellation; the CLI's existing worker supervisor owns process-group cleanup. The GUI waits for CLI completion and retains logs, and never promotes an exit0 received after its cancellation request. This is a finite local workflow; no daemon or resume loop is installed.

The runtime preserves schema-specific readers for historical evidence. New preference snapshots use schema2 with `defaults_policy: corrected-standard-v1`; schema1 retains original stock defaults. A preset remains schema1 and fully names its chosen settings. No schema migration edits old receipts or source projects. Unsupported fields/unknown policies reject instead of falling back.

Keep review copies and authoritative exports distinct. The separate-project interface requires saved, correctly identified, closed source editors; it cannot detect arbitrary unsaved buffers, modify a live editor transactionally or promise undo. A future client must use these same guards, not treat a displayed success message as independent validation.

Current074 [thirteen installed Native deliveries and invalid/class controls](../evidence/runtime074-installed-native-milestone-001.json) and [six genuine live-warning controls](../evidence/runtime074-warning-native-controls-001.json) qualify their recorded headless cases. The [settings contract](routing-preferences.md) separates schema values from currently admitted combinations: ordinary high via cost is explicit and optional, and hard design constraints remain unchanged. [Actual074 GUI105 finite core](../evidence/gui-runtime074-105-core-001.json) passed; genuine changed-warning interaction and the exact queued callback interval remain unexercised. Those results do not qualify the new source build.

With `--warning-review-stdio`, a narrowly eligible reporting change emits one newline-delimited JSON event of kind `autorouter.warning-review-required.v1`. It names a nonaccepted `warning-review.json` record, its `pending_sha256`, `delta_sha256`, a fresh `nonce`, the remaining time, and the previous/fresh findings with the actual copper witness. Eligibility requires identical candidate bytes, metrics, counts and ignore settings; one connection-width warning member may change on verified same-net outer-layer copper. The finding lists are not declared equivalent. Other changes still refuse.

A client must show both reports and obtain an explicit decision. The only accepting response is one JSON line with exactly `kind: "autorouter.warning-review-response.v1"`, `decision: "accept_updated_findings"`, and the current event's exact `nonce`, `pending_sha256` and `delta_sha256`. Never generate acceptance automatically. The response is bounded to4,096bytes; unknown/duplicate keys, wrong bindings, closed input, rejection, cancellation or expiry cannot authorize export. The original30–120second export wall/full-CPU budget includes this wait and final checks; no continuation or second allocation is granted. The process must finish successfully and the ordinary final export reader must pass before a client adopts an export. Pending records cannot be resumed after exit.

The queued opener rechecks source/settings/export witnesses before delivery; this is not atomic live application. Current actual queued-interval qualification is pending. Historical050 active-engine cancellation and stale-input refusals retain their scope. Unit callback tests, instrumented barriers and actual natural GUI timing must remain separately labelled. [Current gates](../STATUS.md) · [CLI](quickstart.md) · [Graphical workflow](gui-workflow.md). Earlier interface details remain in immutable evidence and Git history.

## Selected placement (runtime076 experimental workflow)

The new placement controls call `autorouter.placement_intent` for saved-project inspection, strict settings, bounded alternatives and reviewed pose intent. They call the same `autorouter.placement` command for Native qualification. [Installed076 Native/GUI107 qualification](../evidence/runtime076-placement-product-milestone-001.json) passes the finite owned task, including protected delivery and cancellation/stale guards;075 does not contain this interface. Broader geometry and independent installation remain unqualified.

```sh
.venv/bin/python -B -m autorouter.placement \
  --draft /absolute/reviewed-draft.json --draft-sha256 EXACT_SHA256 \
  --output /absolute/runtime/.runs/NEW_JOB --qualify
.venv/bin/python -B -m autorouter.placement --check /absolute/runtime/.runs/NEW_JOB
```

The explicit execution flag starts a120-second total wall/full-CPU qualification, including a105-second worker envelope and reserved delivery checks. It requires a saved and closed complete project, a fresh owned output, current installed tool hashes and measured space for512MiB temporary work plus3GiB reserve. Native source/candidate observations, separate refill and full schematic/board checks bind the actual result. Exit0 is insufficient; readback must confirm `placement_qualified: true`, `current: true`, and all approval/acceptance fields remain false. Expected unrouted connections are not blocking source defects.

Qualification yields a pending placement project. Routing settings, route review, explicit acceptance and fresh validated separate export remain necessary. The graphical handoff carries a continuous original-project and exact-review guard; editing, rejection, cancellation, closure or changed source/evidence revokes it. No model receives an execution, editing or approval tool. Current geometry and workflow limits are described in [placement review](placement-review.md).
