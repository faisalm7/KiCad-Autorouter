# Acquisition004 static audit

`audit.py` is an offline, read-only source and reference inspector. The default command reads only the frozen protocol and prior baseline metadata; it does not read planned new payloads. Explicit `--audit-acquired --receipt ... --output ...` is permitted only after the lead announces completed acquisition. No downloaded script, native tool, engine, rendering program, network request, dependency substitution or input rewrite occurs. The copied `sexpr_snapshot.py` is the exact pinned project-owned parser, SHA c65b209def530fab9ca1481c67ed2d8217a294b73df8e5e41458e269f917b6dd.

The program independently verifies original Git blobs, expected size/SHA256, recorded receipt identities, retained HTTP response bytes and committed acquisition helper hashes. It inventories every old and new `.data` file before/after, retains all three projects/planned board records on missing or invalid acquisitions, and records unresolved references and per-file notice evidence. Complete acquisition is separate from dependency closure, redistribution clearance, production support and family independence. Embedded geometry/symbol definitions are not evidence of a pinned external library revision. Bare generated identifiers are not automatically a claim that an external file is missing.

Resource limits: each read≤10MiB, all-data≤64MiB,2,048 files/4,096 entries,500,000 AST nodes,60-second measured audit ceiling, each Git metadata subprocess≤3seconds, final report≤10MiB. The local source snapshot is checked again before publication; a changed source/receipt/helper invalidates canonical output. These finite checks are not an atomic filesystem snapshot or hard OS CPU/RSS quota. The analyzer's structured legacy INI reader can reject a legal unsectioned `.pro` preamble; the report must preserve that as an analyzer limitation and inspect exact literal lines separately, never call the original invalid or silently migrate it.

Pure tests:

```sh
python3 -B .runs/licensed-acquisition-004-static-audit-draft-001/test_audit.py
```

The lead announced acquisition004 complete at0dc3aa57546cc20f7083cdda15a9d98e7fee2052. The following actual read-only audit was run and is retained; do not reuse its output:

```sh
python3 -B .runs/licensed-acquisition-004-static-audit-draft-001/audit.py --audit-acquired --receipt .runs/licensed-acquisition-004-run-001/receipt.json --output .runs/licensed-acquisition-004-static-audit-draft-001/actual-001
```

`REPORT.md` and `compact-records.json` are the proposed small public metadata. `actual-001/audit.json` and supplementary exact source lines contain more source-derived detail and remain ignored unless separately curated. Original data assets/model bodies are not selected for redistribution. No new library crawl is authorized; repeated unresolved SparkFun aliases stop the closure branch.
