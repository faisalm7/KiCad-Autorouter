# Selected-placement review prototype

This source-run experimental window displays actual retained Native006 placement alternatives. It is not installed placement support or a finished placer. It never writes a PCB, starts routing, accepts a routing result or waives warnings. Ordinary routing remains available through the installed GUI.

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

## Current product integration work

Runtime076 source work replaces fixture-specific intake with `autorouter.placement_intent`: inspect a saved complete project, explicitly select movable UUIDs and a movement rectangle, preserve all existing copper, generate bounded alternatives, edit coordinates and save review intent. Settings are strict JSON; extra permissions, changed source and unsupported geometry refuse. The curated package selects only the reused contract/observer, pure search, its exact MIT dependencies and bounded retained-identity helpers; historical drivers, protocols, tests and research runs are excluded. Source and packaging controls pass; the new Native qualifier and graphical integration still require qualification in one installed candidate. Runtime075 and its historical results are unchanged.
