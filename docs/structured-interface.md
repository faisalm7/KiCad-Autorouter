# Local structured interface

The graphical controller calls the same offline CLI as Terminal users. It passes argument arrays, exact saved project paths and an explicit captured JSON preset; it does not invoke a shell or send a board to a service. The CLI prints JSON and writes durable receipts in a fresh output directory. See [saved settings](routing-preferences.md) for the versioned input contract.

| Action | CLI | Result / authority |
|---|---|---|
| Check environment | `doctor` | Actual pinned tool/version/hash readiness, successful KiCad/Python/Java probes and recognizable Java version output; no board validation. |
| Preview support and choices | `preview BOARD --settings FILE` | Resolved source identity/settings/protected-route counts; static only. |
| Route a copied project | `route BOARD --settings FILE --output NEW` | `NEW/result.json`; `accepted`, status, source/candidate hashes, tools, all native findings and compute. Exit0 alone is insufficient. |
| Experimental thermal recovery (CLI) | `recover BOARD --seconds 420 --output NEW` | Fixed selected7 whole/native/standard/both/all-source method;90–900 seconds cover incumbent, repair and final validation. It accepts no arbitrary `--settings` preset. Own parent/Native/original checks remain authoritative; no automatic fallback after stale/cancel/refusal. |
| Verify retained result | `check-result RESULT` | Complete shared source/evidence/original-design consistency checks; does not run a new DRC. |
| Build a disposable review | `review-copy RESULT --render --output NEW` | `review.json`, complete project, before/after copper plots and local HTML; original routing is review-only. |
| Record explicit intent | `review-choice REVIEW --choice accept\|reject --output NEW` | `choice.json`; user intent is not a PCB/electrical certificate. Rejection cannot authorize export. |
| Produce a handoff | `review-export CHOICE --seconds 120 --output NEW` | `export.json` and separate complete project after fresh Native refill/fullSCH/original-rule validation. |
| Check handoff evidence | `review-export-check EXPORT` | Current candidate/source/report and file consistency. Any later edit requires new validation. |

Commands returning failure, cancellation, stale inputs, unsupported features or exhausted budgets cannot authorize a positive next step. SIGINT/SIGTERM requests cancellation; the CLI's existing worker supervisor owns process-group cleanup. The GUI waits for CLI completion and retains logs, and never promotes an exit0 received after its cancellation request. This is a finite local workflow; no daemon or resume loop is installed.

The runtime preserves schema-specific readers for historical evidence. New preference snapshots use schema2 with `defaults_policy: corrected-standard-v1`; schema1 retains original stock defaults. A preset remains schema1 and fully names its chosen settings. No schema migration edits old receipts or source projects. Unsupported fields/unknown policies reject instead of falling back.

Keep review copies and authoritative exports distinct. The separate-project interface requires saved, correctly identified, closed source editors; it cannot detect arbitrary unsaved buffers, modify a live editor transactionally or promise undo. A future client must use these same guards, not treat a displayed success message as independent validation.

Current039 [installed/native CLI proof](../evidence/runtime039-native-floor-schema-milestone-001.json) includes five own-final deliveries and real critical controls; [freshHOME/TMP/minimalPATH](../evidence/runtime039-clean-environment-001.json) doctor/six-stage delivery also passes. The queued opener rechecks source/settings/export witnesses at delivery; it does not provide atomic live-editor application. Current preopen change refusals are observed, while the one forced queued-timing attempt missed its interval. Full184 callback tests remain separate software evidence.

Current039 includes optional graphical recovery and the captured-budget display fix. [Repair420/export120](../evidence/gui-runtime039-079-recovery-repair-001.json), [no-repair90/export90](../evidence/gui-runtime039-079-recovery-no-repair-001.json) and [hierarchy normal420/export120](../evidence/gui-runtime039-079-hierarchy-high-budget-001.json) complete review, explicit software intent, fresh Native export and checked KiCad opening. [Post-incumbent Cancel](../evidence/gui-runtime039-079-postincumbent-cancel-001.json) preserves the verified incumbent and blocks positive adoption; Native workers completed normally, so their interruption is unproved. Incompatible settings refuse before work. No automatic fallback, wider electrical scope or general superiority follows. [Earlier interface evidence](https://github.com/faisalm7/KiCad-Autorouter/blob/aba14a978c13c222983fead1bdf30427c46b7f66/docs/structured-interface.md) preserves previous build scopes.
