# Selected placement in the design assistant

[Runtime087's finite GUI workflow](../evidence/runtime087-installed-GUI-core-001.json) demonstrates actual toolbar launch, Native-context placement inspection, protected copper rebuilding, coordinated edits, Native qualification, protected routing, Edge review, explicit acceptance/rejection, cancellation and fresh separate delivery. The owned task is exposed development evidence, not broad placement quality. Finder-only startup remains pending access. [Current start instructions](../START_HERE.md) identify the exact existing installation. Versioned sections below preserve their historical scope; later receipts supersede their old pending fields.

1. Save the complete PCB/project/schematic, then close its editors. Choose **Place components…** and **Inspect project**.
2. Select components to move. Unchecked components stay fixed; locked components and components sharing an existing routed net cannot be selected. Enter the allowed movement rectangle. **Save settings…** and **Load settings…** preserve these choices.
3. Choose **Find placement alternatives**. Review original/proposed positions, fixed parts, copper, zone and allowed-region boundaries. Choose an alternative or edit a selected component's X/Y, then **Update draft**. Invalid geometry refuses without changing the source.
4. Review the exact draft and limitations, acknowledge that the source editors are closed, then **Validate placement**. This runs actual KiCad checks on a separate copy. Expected unrouted connections are routing demand, not by themselves an invalid design.
5. **Open routing settings** and choose routing scope, protection and budget. Keep the placement review open and unchanged. Preview, route, inspect all findings and copper plots, then explicitly accept or reject. Acceptance remains intent, not electrical approval. **Fresh export** performs new validation; **Open checked export** checks freshness before opening the separate project.

Edits, rejection, cancellation and closing the placement review revoke its routing handoff. Changing the displayed source cannot detach that guard. Cancellation waits for owned cleanup; cancelled or stale results cannot be accepted. Original projects are never overwritten. No live editor apply, undo or unsaved-buffer synchronization is claimed.

The experimental geometry is bounded to16footprints/32pads and at least2selected movable components, on a rectangular two-copper-layer board. The older circular-PTH translation scope remains available. The explicit ordinary scope adds front two-pad rectangular/roundrect SMD parts at their original0/90/180/270-degree orientations. Movable parts need centred rectangular courtyards; eligible surrounding footprints use conservative fixed courtyard envelopes. Exact pad offsets, sizes, angles, nets and identities are preserved. Existing copper is retained and the movement rectangle must avoid its clearance-expanded bounds and zone envelopes. Groups, flips, rotation changes, cutouts and keepouts remain unsupported. Other library geometry can still refuse. Geometry proximity does not establish electrical suitability.

GUI107 verified saved presets, invalid edit refusal, reviewed coordinates, actual Native qualification, child-window return, protected routing, rendered Edge front/back plots/findings, explicit acceptance/rejection, fresh export, actual checked KiCad opening and stale guards. Its first cancellation attempt missed completion; the second stopped an active owned job and revoked the handoff. Both are retained. The exported PCB remained unchanged after inspection, but KiCad changed PRO/PRL; the next open correctly refused stale evidence. One owned task does not establish broad placement usefulness.

GUI108 now shows “Placement validated — routing pending” in both the diagram and current findings. Changing coordinate text preserves that pending edit while clearing qualification. Its actual edited SMD task routed and freshly exported with0opens/0blocking/1unchanged text-height warning, plus2ignored checks. Acceptance, rejection, active cancellation and source/settings/export freshness controls ran. One rapid routing-popup interaction left an old-scope preview visible; the next Route action refused before execution. Until corrected, let a selection settle and check the preview's stated scope before proceeding. This is a known UI defect, not permission to use mismatched settings. Native wx diagnostics remain in raw logs, distinct from DRC warnings. No live model or human PCB review occurred.

The [structured interface](structured-interface.md) uses the same deterministic intake, independent geometry checks, Native qualification and continuously bound source guard. Curated installation contains only necessary pinned MIT search/contract dependencies, not the historical research archive. Product browser choice is configurable; GUI107 used Microsoft Edge.

## Prospective079 controls

The new source batch is awaiting full installed/Native/GUI qualification. It adds **Preserve all existing copper** as the default and an explicit **Rebuild affected unlocked nets** option. Advanced protection lists exact net names or route UUIDs; locked and otherwise unsupported parts stay fixed. The review names every affected net and shows removed/retained route counts. It never infers that a net is electrically safe to reroute.

Numeric edits can be kept for several selected components and applied together with **Update all edits**. The final combined pose is checked once; failed edits retain the previous pose and revoke approval. Placement validation checks original, prepared and moved projects; its routing window visibly prefills the exact affected nets and a90-second budget. The same mandatory origin checks apply through the structured CLI and final export. Changing source, settings, plan, pose, protected copper or evidence revokes the result. This option does not yet qualify unrelated acquired boards or broaden rotation/side/group/keepout support.

## Fixed-context placement: prospective082

The explicit `ordinary-fixed-context-v1` scope extends source fidelity around selected front two-pad SMD parts. Rich passive circle/arc/polygon graphics and padless back artwork remain fixed; artwork is labelled as retained and omitted from the physical placement diagram. This is a source extension awaiting installed task/GUI qualification, not broad placement support.

Current intake uses the older parsers first, so this policy is presently reached only by sources whose richer fixed geometry requires it. An otherwise legacy-readable board cannot opt into it through ordinary controls yet; that coverage/usability limit remains open.

The settings bind `fixed_context_policy`, `zone_policy` and `metadata_finding_policy`. Unchanged fixed board-envelope/pair proxy conflicts can remain as source conditions. Every moving part still obeys board/region/obstacle checks. Different mandatory fixed regions and hard rectangular keepouts are checked. Preserved segment envelopes are checked against actual proposed poses rather than forbidding the whole search rectangle. Ordinary zone intent remains exact; Native refill can change derived copper. Explicitly named protected nets with a copper pour are refused because exact protected fill is not guaranteed. Route-UUID protection protects those routes only.

Only library/qualified Datasheet-placeholder warning anchors may follow exact selected-footprint translations. Source and candidate each need their own complete Native field proof; every other finding field, physical warning and ignored check stays exact. Raw reports remain unchanged, and this comparison grants no warning acknowledgement or acceptance. Actual blocking findings, invalid/unknown constraints, stale inputs or cancellation still refuse.

Bounds remain16footprints/32pads/64straight segments, two outer copper layers, rectangular board, fixed cardinal orientation and no actual rule areas/cutouts. Passive immutable artwork is bounded to256rich shapes/4096total polygon vertices/1024per polygon, checked in linear time against actual Native topology and exact point order; it never becomes movable geometry. No electrical/thermal/timing suitability is inferred. The unrelated IR development task is already routed at source; successful rearrangement would show task breadth, not a completion-rate or quality advantage.

## Native annotation checks: prospective083

The next source batch uses the same saved-project inspection for Native silkscreen and solder-mask bounds. The placement search and numeric edits reject new conservative label/mask conflicts before qualification. Faint blue boxes show selected silkscreen extents. These boxes are a prefilter: they do not approve placement, waive warnings or replace actual final KiCad checks.

On pinned10.0.7 the graphical Inspect action requests this detail for ordinary SMD placement. Previously saved presets retain their original policy when loaded; the displayed limits change with that policy. Native capture stays outside the editor/UI thread and can be cancelled. Subsequent source/evidence checks reuse the unchanged capture rather than rerunning KiCad for every edit.

The shared command is:

```sh
.venv/bin/python -B -m autorouter inspect-project /absolute/saved/board.kicad_pcb \
  --placement-context --seconds 60 --output /absolute/fresh-inspection
```

A scripted placement caller passes the resulting `inspection.json` as `native_context` to `placement_intent.inspect_saved`. Drafts bind that exact receipt, source and geometry hashes; altered or missing evidence refuses. Core routing/placement still requires no model account. This source batch is not installed/GUI-qualified yet. The earlier082 IR attempt remains failed, including both new physical warnings.

## Historical source-run lineage

The following developer commands describe the earlier075 source-run review/qualification experiment. Its then-pending statements are historical, superseded by the076 installed workflow above; the original evidence and failures remain unchanged.

The historical source-run experimental window below displays actual retained Native006 placement alternatives. It is not installed placement support or a finished placer. It never writes a PCB, starts routing, accepts a routing result or waives warnings. Ordinary routing remains available through the installed GUI.

The diagram shows original and proposed selected components, pad offsets, fixed components, preserved copper, zones and the allowed movement rectangle. Choose an alternative, select a component and edit X/Y. **Update draft** checks the existing independent geometric constraints. Pending edits clear acknowledgement and disable saving. Out-of-region, overlapping, fixed/locked/tracked-net moves and invalid numbers refuse.

A changed pose is explicitly **geometry-only** until fresh Native qualification. **Save reviewed draft** records the exact source/evidence/constraints/pose after fresh readback and a final material check. **Reject draft** records rejection. Neither grants execution authority or constitutes human PCB approval. The source-run qualification bridge now checks an exact saved draft before it can become a separate routing input.

For the prepared local development evidence, launch the new window with KiCad's bundled wx-enabled Python. The runtime and preserved evidence must remain at their verified paths; use a fresh output directory:

```sh
KICAD_PYTHON='.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9'
"$KICAD_PYTHON" -B experiments/placement_review.py \
  --runtime "$PWD/.runs/runtime075 fresh install 001" \
  --evidence "$PWD/.runs/placement-native-proposal-v1-006" \
  --protocol "$PWD/experiments/placement_native_proposal_v1/protocol-006.json" \
  --output "$PWD/.runs/my-new-placement-review"
```

This developer command is not the final KiCad toolbar workflow. General saved-project capture, installed placement, selection/region editing, grouping and routing handoff are still open. The current capture accepts only its narrow rectangular, unrotated front/PTH geometry and preserves every existing segment; most ordinary library footprints remain unsupported. No electrical requirements are inferred from names or geometric proximity.

[Observed GUI evidence](../evidence/placement075-graphical-review-001.json) retains the initial missing-label defect, failed font-API launch, corrected actual window, edited draft and rejected alternative. Existing Native006 and routing results remain unchanged; no new Native execution occurred in this review.

The subsequent [exact edited-draft qualification](../evidence/placement075-reviewed-native-choice-001.json) ran actual KiCad translation, separate refill, full schematic/board checks and final capture in 8.53 seconds. All six footprints, eight pads, fixed geometry and the locked trace were preserved. Two expected unrouted connections remain; there were no blocking findings, warnings or exclusions. This is a **pending placement candidate**, not a routed or accepted board.

The developer bridge requires an explicit draft hash, trusted installed runtime, fresh output and execution flag:

```sh
".runs/runtime075 fresh install 001/.venv/bin/python" -B experiments/placement_choice.py \
  --runtime "$PWD/.runs/runtime075 fresh install 001" \
  --evidence "$PWD/.runs/placement-native-proposal-v1-006" \
  --protocol "$PWD/experiments/placement_native_proposal_v1/protocol-006.json" \
  --draft "$PWD/.runs/YOUR-REVIEW/intent-YOUR-DRAFT.json" \
  --draft-sha256 YOUR_EXACT_SHA256 \
  --output "$PWD/.runs/YOUR-FRESH-PLACEMENT-QUALIFICATION" --qualify
```

The total wall/CPU limit is 120 seconds, with a 110-second child envelope. Initial source evidence is reused only while its full retained proof remains current; the changed candidate receives new Native checks. The independent `placement_choice.check(output, expected_runtime=runtime)` reads actual proof files and late metadata without launching KiCad. Missing, rejected, changed or cancelled drafts refuse. No routing, warning acknowledgement or approval follows automatically.

The prepared graphical handoff refused before opening after a restart changed the mount device number. The retained-evidence reader now separates historical request identity from current readback identity, while live workers remain strict. Original choice001 and its draft remain unchanged; current code pins require a fresh explicit review and prospective qualification under the corrected checker. No original Native run is relabelled. The current launcher verifies placement lineage at entry. The source GUI now has an internal `SourceGuard` that binds the exact candidate project and a trusted bounded, read-only origin verifier. The same guard stays attached to Request/Workflow through action, adoption and queued opening; edits cannot silently detach it. It accepts no approval return value and cannot be supplied through model output or preset JSON. This seam has file-mutation/cancellation regressions but is not yet installed or connected to the placement window. Qualification/continue controls and installed packaging remain the next integration work; this sequence of developer commands is not a finished graphical placement product.

The corrected-checker [same-pose GUI delivery](../evidence/placement075-reviewed-GUI-delivery-001.json) is now demonstrated: explicit graphical004 draft, Native choice002, installed gap-completion routing, Edge comparisons, acceptance intent, fresh export and actual checked KiCad opening. All original constraints and the locked trace remain; final routing findings are0/0/0/0. This was a source-run review/qualification plus installed routing handoff, not yet one installed placement workflow. KiCad changed exported project/session files on opening/closing; the subsequent checked-open refused those stale files, while the original source and pending placement proof stayed unchanged. The initial failed launcher and all earlier results remain retained.

## Rigid selected group — prospective088 source

The source extension adds **Keep selected parts together**. All2–16selected eligible parts form one explicit rigid group; the search changes only one shared translation. Spacing, source angles/sides, all fixed parts, original rules and protected copper remain mandatory. This is deterministic geometry and connectivity-based search, with no model call. It does not import KiCad group objects or infer membership/electrical intent from net names.

First-scope group delivery requires **Rebuild affected unlocked nets**, so it uses the existing persistent original-to-final placement origin and selected routing contract. Locked, explicitly protected or otherwise unsupported incident copper refuses. Preserve-all independent placement remains available; preserve-all grouping, multiple/nested/disjoint groups, group rotation, side changes and advanced geometry are deferred. No constraint is silently converted into a preference.

Version4settings add only `group_policy: rigid-selected-translation-v1` to the explicit affected-net settings. Presets keep that policy and exact selected identities. One-member coordinate edits translate every member; conflicting multi-member displacements refuse and revoke prior intent. **Review current group arrangement** starts an explicitly labelled original-layout review without running or claiming search. It is useful when rigid translation cannot improve internal-only connections; the user may still deliberately reposition the group. No cancelled or timed-out search is adopted through this action. The search reuses the pinned MIT annealer with atomic member-set moves/cost and rollback. Proxy arithmetic is independently constrained; one shared integer-nm displacement is then quantized, and exact actual member anchors are checked in the reviewed draft, Native proof and final routed delivery. Native DRC alone cannot detect every1nm group shear.

This source work has targeted pure/callback controls, not installed/Native/GUI qualification yet. The current installed candidate remains087. Fresh coherent installation, Native positive/invalid/group-shear controls, full relevant regression and actual changed-build GUI remain required. Failed source tests and unsupported synthetic geometry controls remain retained. No placement-quality or unrelated task-completion gain is claimed.
