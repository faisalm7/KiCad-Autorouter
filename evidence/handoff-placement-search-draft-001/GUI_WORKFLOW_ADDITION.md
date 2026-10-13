## Search/pruning handoff and persistent review choice (qualification pending)

After exact central validation, `review-copy` can prepare a separate complete review project for schema4 `placement-search-v1` and schema5 `placement-pruning-v1` receipts. The candidate's original rules and all saved findings remain visible. This policy extension still requires its own native copied-project positive/invalid controls before being described as qualified. Existing native/schema3 observations do not establish this new gate.

Open the printed `.kicad_pro` in KiCad project manager, then Tools → PCB Editor. Inspect the full design and run DRC with refill and every severity visible. Close the editor before recording a choice. Each destination must be new:

```sh
.venv/bin/python -m autorouter review-copy PATH_TO_RESULT_JSON --output .runs/new-review --render
.venv/bin/python -m autorouter review-choice .runs/new-review/review.json --choice reject --output .runs/new-rejection
.venv/bin/python -m autorouter review-choice .runs/new-review/review.json --choice accept --output .runs/new-accept-intent
```

These choices record intent only. Neither choice applies a board or records native, human PCB, electrical or manufacturing approval. Rejection preserves the original, review copy and evidence. Accept intent requires the exact review board to match the validated candidate; an edited board fails. KiCad may change project/local settings even after Discard Changes. Those actual changes are recorded as unvalidated and never replace original rules. Source, candidate, receipt, complete routing evidence and bound preview must still match; stale material or cancellation invalidates the choice record.

A successful accept-intent record explicitly requires fresh native validation before any separate accepted-project export. That exporter remains unfinished. It must start from the bound original candidate and unchanged complete original project/rules, preserve original geometry/protected routing and guidance constraints, refill/reload, and bind the actual final DRC to the exported final SHA. It must not copy changed GUI rules into the accepted design. An edited GUI board is a new unvalidated design.

The command retains the existing 30-second wall/full CPU and finite inventory limits. It starts no engine, native worker, editor or service. Successful exit means only that the intent record was written and read back; rejection intent is also a successful recorded choice. `choice.json` always has `routing_accepted=false`, `applied=false`, `native_validation_performed=false` and `human_pcb_approval_observed=false`.
