# Skeptical review: final plot-input PRL replay

This supplements the unchanged initial PROPOSAL.md, SHA256
`b5dda210cb6f7f312e2e4d152b2ff962efd13bad3b4bc0647acc5defaeed70be`.
It does not replace that proposal, qualify Native support or authorize execution.

The last non-byte guard must cover **every retained plot-work/*-input PRL** in
review-copy, review-choice and export bind/readback/stable publication. Replaying
only the source route and fresh export PRLs misses a plot-input flag/hardlink
change made by a later tool or material callback. Byte hashes cannot detect it.

Reuse the existing check_experimental_preview to derive exact caller-pinned SVG
process/input pairs. Retain each (root, binding, process), finish all source and
additional export semantic/tool checks, then run a byte-material callback after
those checks. Finally replay existing local_settings.check_event on the source,
export and plot pairs. No tool-reading/material callback may follow that final
PRL-only pass. Source DRC pairs include the exact ordinary bare [nt.cli, pcb, drc]
prefix as well as sandboxed export prefixes; require existing process_check
before check_event, never an argv substring inference.

Focused controls must mutate a plot-input PRL flag after the preview/tool check,
and a bare source-refill PRL during the additional export-packet callback. A late
nt.check callback that changes original source bytes must also fail the final
material witness. These are authored fixture controls, not Native proof. Keep
original context, fullSCH, process, budget and publication requirements intact.
