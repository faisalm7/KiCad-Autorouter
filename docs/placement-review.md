# Selected-placement review prototype

This source-run experimental window displays actual retained Native006 placement alternatives. It is not installed placement support or a finished placer. It never writes a PCB, starts routing, accepts a routing result or waives warnings. Ordinary routing remains available through the installed GUI.

The diagram shows original and proposed selected components, pad offsets, fixed components, preserved copper, zones and the allowed movement rectangle. Choose an alternative, select a component and edit X/Y. **Update draft** checks the existing independent geometric constraints. Pending edits clear acknowledgement and disable saving. Out-of-region, overlapping, fixed/locked/tracked-net moves and invalid numbers refuse.

A changed pose is explicitly **geometry-only** until fresh Native qualification. **Save reviewed draft** records the exact source/evidence/constraints/pose after fresh readback and a final material check. **Reject draft** records rejection. Neither grants execution authority or constitutes human PCB approval. The next bridge qualifies a chosen pose before it can become a separate routing input.

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
