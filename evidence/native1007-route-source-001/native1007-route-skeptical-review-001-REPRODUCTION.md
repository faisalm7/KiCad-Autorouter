# Prospective controls; unexecuted

## Default task audit producer/reader contract

Use the existing controlled route scaffold with an explicit pinned synthetic nt and the integrated Default fixture; retain all expected helper calls. Substitute only Native/engine boundary results as the existing portable tests do. Assert the actual route producer records `netclass_policy is None`, `netclass_export_audit`, `netclass_task_audit` and the forced final-netclasses audit; pass that record to the explicit shared checker. Before the corrected task-audit condition, publication must reject the absent audit; after correction it must reach the checker normally. Default1000 without named classes retains its previous no-map branch. A Native test must separately establish actual routing.

Minimal source witness of the original mismatch (not a substitute for actual-path test):

```python
policy = None                  # new fixture uses only Default
native_toolchain = object()    # caller-selected explicit context
# old producer conditional: policy is not None -> False
# shared reader conditional: policy is not None or native_toolchain is not None -> True
```

## Late PRL flag mutation through actual publication path

Reuse existing fake-flags/owned-temp PRL tests and an accepted, otherwise consistent explicit receipt; no Native worker required. Invoke actual `route` guarded publication with its real stable/account closures (or AST-extract that actual stable, as existing source controls do). Inject the mutation only after the last real `check_event`/`fields.check_local_settings` check: use the late `tool_manifest` or full-tree read hook to set a restored protected input PRL's fake flags to UF_IMMUTABLE/nonzero, leaving file bytes/process journals unchanged. Assert the current implementation leaves all material hashes unchanged. Required fixed result: guarded publication becomes invalidated and accepted false. Also retain a no-mutation positive and an exact changed-byte negative so the flag check cannot be accidentally substituted by another byte check.

The mutation targets metadata, not receipt bytes. `tree_hash`/evidence_inventory cannot see it; `local_settings.check_preserved`/`check_event` can. Every affected source/refill/final field stage must retain its exact binding/event policy.

## Entry context setup costs

Substitute nt.check with a controlled advancing monotonic/process-time clock during `experimental_route_record`, preserving a typed actual nt object in the existing test scaffold. Record clock advancement before Job exists, then let the controlled route complete. The published route wall/parent CPU must include that advancement (and must reject if it alone crosses the assigned cap). Keep an inherited preference-clock control to prevent rebasing an already-started operation. This proves accounting scope only, not actual host cost.
