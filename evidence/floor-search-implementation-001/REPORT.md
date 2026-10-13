# Shared floor-search hooks

Implemented only `autorouter/floor_route.py` and new `tests/test_floor_search.py`. No native, JVM, network, Git command or full suite ran. ROOT owns pipeline/schema-5 pruning integration and subsequent native qualification.

`SEARCH_POLICY='placement-search-v1'` introduces schema 4, separate from unchanged schema 3. It permits only standard/tuned/completion-only and default/low/high named via scoring; omitted runtime scoring resolves explicitly to `via_default`. Whole-board `both` is required; preferences and retained routing are refused. Every effective engine configuration still requires all three width-reduction restrictions. The ordinary SES reconstruction and exact eight-stage check remain mandatory.

`placement-search.json` contains `search_contract(profile, scoring_variant)` and is bound by `placement_search={file,sha256}` plus the completed evidence inventory. File/field/schema markers reject single-selector downgrade or mixed policy. It identifies the base placement policy and actual search/scoring settings separately: the original placement/floor composition, fixed 20 µm margin, and base planning-parameter record remain byte-identical. The base record's default scoring labels are provenance of the base transform, not the effective schema-4 engine settings. Historical schema 3 still rejects nondefault scoring and non-completion profiles.

Shared APIs:

```python
validate_contract(original, candidate, source_hashes, protected, contract, out,
                  *, guidance_basis=None) -> (task, context)
final_context(job, original, candidate, source_hashes, protected, contract,
              *, guidance_basis=None)
check_final_context(directory, data, original, candidate, protected, contract,
                    guidance_basis=None) -> audit_dict
check_drc_stage(directory, data, name, source, input_path, saved, before) -> native_summary
```

An external basis supplies only the original export context/raw/floor-guided bytes. The exact contract is rederived against the source and unchanged candidate project; symlink bases and modified preferences/guidance/source hashes reject. Fresh final context and audit are written/read in the current job directory. **The strategy caller must separately bind and validate the accepted incumbent receipt and its complete tree before/after use.** This hook does not authenticate an arbitrary directory or replace ancestry/readback validation.

The extracted DRC-stage body is AST-identical to the former nested function after replacing its `candidate.name` closure with the same board filename from `source.name`; `extraction-check.json` records the check. Original source/refill callers retain the same arguments, original-rule input inventories, report parsing, exact CLI argv, status/exit/cleanup, and step/hash bindings.

Validation: 15 new methods passed in 1.943 seconds (`tests-001.log`). Combined new and existing floor/placement subset: **76 methods passed in 5.843 seconds** (`tests-002.log`). The new controls use copied retained fixtures with synthetic process/settings records, not new native observations. They cover all nine named combinations, unchanged DSN chain, selector/marker downgrade, preference/mixed-mode rejection, mismatched engine arguments, all width-reduction guards, missing SES/extra stage, changed import, separate guidance basis, final context/project binding, and extracted DRC input/process preservation. Existing schema-2/3, native input, transport, and publication controls passed unchanged.

Exact source snapshots are retained under `before/` and `after/`; `floor-route.patch` is generated without Git. No source inputs or historical evidence were changed. Native validity of new standard/tuned placement runs, schema-5 pruning lineage, and integrated accounting remain ROOT's next gates; this report makes no routing improvement claim.
