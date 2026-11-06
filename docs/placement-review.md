# Selected placement in the design assistant

Runtime077's [installed evidence](../evidence/runtime077-installed-placement-001.json) and actual GUI108 extend the earlier [076 milestone](../evidence/runtime076-placement-product-milestone-001.json) to a bounded ordinary SMD task. The following workflow runs locally without an AI account.

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
