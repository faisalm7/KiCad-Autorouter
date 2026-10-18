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

Current installed CLI evidence is [runtime033 ordinary qualification](../evidence/runtime033-ordinary-install-001.json), [fresh-environment delivery](../evidence/runtime033-clean-environment-001.json) and the [completed six-arm comparison](../evidence/runtime033-current-interf-comparison-001.json), whose sole thermal-recovery delivery is one exposed-family result. The [queued-open guard](../evidence/gui-queued-open-source-001.json) checks source/settings and export byte witnesses at GUI delivery; it does not replace the worker reader or establish atomic live-editor application. [Actual033/GUI074](../evidence/gui-runtime033-074-native-controls-001.json) qualifies its declared seven-role interaction set on two functional fixtures, including six positive protected Routes/five pre-open exports and an Interf engine-cancellation role. Three freshness mutations occurred before Open; no forced queued-callback hold was observed. Full176 callback regressions remain software-boundary proof, not a timed actual GUI race.

The ROOT-source graphical recovery extension is an unbuilt, unqualified next candidate with 65 targeted checks. It is not part of runtime033’s graphical contract; current033 recovery remains CLI-only. Its future GUI must refuse incompatible settings before work, preserve exact captured budgets/constraints and reuse these existing recovery, review/export and cancellation checks. Fresh integration/install/Native repair/no-repair/invalid/cancel and actual GUI qualification are required before advertising it.
