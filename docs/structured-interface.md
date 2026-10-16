# Local structured interface

The graphical controller calls the same offline CLI as Terminal users. It passes argument arrays, exact saved project paths and an explicit captured JSON preset; it does not invoke a shell or send a board to a service. The CLI prints JSON and writes durable receipts in a fresh output directory. See [saved settings](routing-preferences.md) for the versioned input contract.

| Action | CLI | Result / authority |
|---|---|---|
| Check environment | `doctor` | Actual pinned tool/version/hash readiness; no board validation. |
| Preview support and choices | `preview BOARD --settings FILE` | Resolved source identity/settings/protected-route counts; static only. |
| Route a copied project | `route BOARD --settings FILE --output NEW` | `NEW/result.json`; `accepted`, status, source/candidate hashes, tools, all native findings and compute. Exit0 alone is insufficient. |
| Verify retained result | `check-result RESULT` | Complete shared source/evidence/original-design consistency checks; does not run a new DRC. |
| Build a disposable review | `review-copy RESULT --render --output NEW` | `review.json`, complete project, before/after copper plots and local HTML; original routing is review-only. |
| Record explicit intent | `review-choice REVIEW --choice accept\|reject --output NEW` | `choice.json`; user intent is not a PCB/electrical certificate. Rejection cannot authorize export. |
| Produce a handoff | `review-export CHOICE --seconds 120 --output NEW` | `export.json` and separate complete project after fresh Native refill/fullSCH/original-rule validation. |
| Check handoff evidence | `review-export-check EXPORT` | Current candidate/source/report and file consistency. Any later edit requires new validation. |

Commands returning failure, cancellation, stale inputs, unsupported features or exhausted budgets cannot authorize a positive next step. SIGINT/SIGTERM requests cancellation; the CLI's existing worker supervisor owns process-group cleanup. The GUI waits for CLI completion and retains logs, and never promotes an exit0 received after its cancellation request. This is a finite local workflow; no daemon or resume loop is installed.

The runtime preserves schema-specific readers for historical evidence. New preference snapshots use schema2 with `defaults_policy: corrected-standard-v1`; schema1 retains original stock defaults. A preset remains schema1 and fully names its chosen settings. No schema migration edits old receipts or source projects. Unsupported fields/unknown policies reject instead of falling back.

Keep review copies and authoritative exports distinct. The separate-project interface requires saved, correctly identified, closed source editors; it cannot detect arbitrary unsaved buffers, modify a live editor transactionally or promise undo. A future client must use these same guards, not treat a displayed success message as independent validation.
