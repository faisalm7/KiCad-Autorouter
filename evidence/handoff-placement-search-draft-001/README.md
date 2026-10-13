# Search/pruning review handoff proposal — frozen ignored draft

This is a source proposal for ROOT integration, not native or GUI qualification. It adds exact SEARCH/schema4 and placement-pruning/schema5 policy dispatch to the existing disposable `review-copy` command. The central checker remains authoritative. Missing, mixed, diagnostic, unknown and downgraded markers remain rejected; schema2 remains blocked. No existing rendering, capture, 30-second wall/full CPU, evidence or transaction limits change.

A new `review-choice` command records `accept` or `reject` as persistent separate-project intent. It uses the existing path/inventory/receipt/checker/publication helpers. Exact source, receipt, candidate and complete evidence freshness remain required. Accept intent additionally requires the actual review board SHA to equal the bound validated candidate. The observed GUI's project/local-settings changes may be recorded, but are explicitly unvalidated and never adopted as rules authority. Reject intent may retain an edited copy without deleting anything.

Every successful choice has `routing_accepted=false`, `applied=false`, `native_validation_performed=false`, `human_pcb_approval_observed=false` and `fresh_native_validation_required=true`. There is no accepted-project exporter, live editor application, undo, plugin, GUI opening or electrical approval in this proposal. A later exporter must freshly validate the bound original candidate with unchanged complete original rules and the original guidance basis before writing a separate project. Saving an edited board requires a new supported routing/validation flow.

`source.patch` contains the two source edits. Promote `handoff.py` to `autorouter/handoff.py`, `__main__.py` to `autorouter/__main__.py` and `test_handoff_search_choice.py` to `tests/test_handoff_search_choice.py`; use either replacement files or the patch, not both. `GUI_WORKFLOW_ADDITION.md` is a proposed documentation addition; retain its qualification gate until actual native evidence exists. `manifest.json` binds exact base/proposal/helper hashes. No tracked source was edited by this agent.

Offline targeted verification, using explicit supervisor Python and no bytecode writes:

```sh
/Users/faisal/Projects/KiCad-Autorouter-local/.venv/bin/python -B .runs/handoff-placement-search-draft-001/run_pure_controls.py
```

The final log reports 45 passing methods (16 new policy/disposition controls plus 29 existing handoff controls). Central/native checks are mocked in these pure controls. They prove consistency and failure handling only. The real self-SIGTERM control targets its own foreground test process, restores signal handlers, and leaves no current successful disposition. Prior logs remain present. Actual native qualification is ROOT's single worker lane after the active benchmark. See `protocol.json` for the prospective gate.
