# HFE one-export parity probe: narrow review and draft corrections

Reviewed frozen probe399efc300a63825cd5e7299035b9a300c6f37f59e68b9fbbce34816a9ff9d0d1, its NOTES, current shared API sources, two existing raw warning examples and the lead's prospective enclosure as data only. No project/draft imports, tests, Native/JVM, shared checker, Git/network, source/.runs mutation or delegation occurred. Only this ignored review directory was written. Both corrected sources and the four-control source were AST parsed, never executed.

## Concrete corrections

1. Child stable() replayed check_preserved and then read the netlist hash. A flag-only PRL mutation triggered during that later hash can survive the last metadata check: byte witnesses remain unchanged. Corrected copy moves netlist hashing before check_preserved so actual PRL metadata/event checking is its final file guard.
2. Enclosure fresh() originally checked only source/tools/byte witnesses/literal child and never replayed current PRL metadata after child publication. PRL flag changes do not change bytes. Corrected tail reads the pinned child protocol, derives the original-named board and exact export name/argv with existing field_evidence helpers and caller Nt, replays f.process_check against the retained actual child step/process, then calls actual ls.check_preserved with protocol.input_with_owned_prl_sha256 and actual process.local_settings_protection. This is the last file guard. It adds no worker, new parsing policy or audit framework and does not reacquire the child's quality lock.
3. Shared BoundJob can return a cancelled step as a rejected-worker Exception, not only KeyboardInterrupt. Probe's handler then labeled it failed. Corrected copy also checks actual job.steps status=='cancelled', exactly like the existing original diagnostic; ordinary nonzero/parse/quality failures remain failed. This was a classification defect; old passed already stayedFalse.

`changes.patch` contains only these edits. Corrected probe454a18003f29e6d170bbf1a75214541ea7803de7657aa72d26c978a6f556d93c; enclosuree02e676d223cd41a413ad7e08dfc0eab2cd68470268a78cf828e56a395d07d63. Do not edit frozen originals or repeat either completed DRC.

## Focused prospective controls

`test_probe_publication.py` SHA9097e7157d242cc6debdb5a3a725d006060c06f05144bf51fad214336491ef02 is pure synthetic exact-AST control source, not Native evidence. It extracts literal child stable/enclosure fresh/actual protected-step exception-handler bodies, substitutes fixed provenance/material inputs, and uses the real shared process and check_preserved implementations. Two controls use an actual owned regular PRL and os.chflags(UF_IMMUTABLE), always restoring flags in finally/cleanup: flip during the last child netlist hash, and flip after child publication before outer fresh. Other controls exercise actual cancelled-step classification and ordinary-negative classification. No source board, Native command or fixture engine runs. Platform absence is an explicit skip, not a pass.

Expected before3fail/after4pass is a prediction only. Lead commands, not executed here:

```sh
HFE_PROBE="$PWD/.local-backups/hfe-parity-probe-preparation-001/probe.py" HFE_ENCLOSURE="$PWD/.local-backups/run-hfe-parity-probe-enclosure-001.py" .venv/bin/python -B .local-backups/hfe-parity-probe-review-001/test_probe_publication.py
.venv/bin/python -B .local-backups/hfe-parity-probe-review-001/test_probe_publication.py
```

## API/census assessment and remaining limits

No additional concrete launch blocker was found. Existing arguments(...)[0] is the exact schematic export API; paths/names agree; protected_step uses the SCH stem's PRL, which equals the authored owned PRL path, and current shared process/event signatures match the draft. The child owns the sole quality lock; outer does not acquire it. Nested child output is inside the outer monitored cwd. Caller Native/context/source/controller/material pins remain, accepted/production_support_qualified stayFalse, and all timing/cap/cancellation paths retain negative evidence.

The parser checks exact exportE/Eeschema10.0.7/source pairing, complete component fields, native libpart pin declarations, component/footprint reference sets, library-vs-PCB terminal keys, one exported membership per logical terminal, nonzero named partitions and forward/reverse net-name bijection. Duplicate library numbers and export nodes, missing declarations/memberships, unknown net/node grammar and no-net numbered pads create unqualified reasons. Positive graph partitions and independently derived mismatch pad UUIDs must cover the complete retained warning population, with exact warning descriptions; warning prose does not create the rename map. Every physical pad remains in output. Same-number/same-net physical multiplicity is explicitly recorded, rather than becoming a claim that distinct physical pads were individually native-connected; this remains a logical-terminal diagnostic only.

No-connect prefixes/attributes are labels only; missing nodes are not accepted as NC, and no-net terminals are never merged. Item layer/position, pin function/type, schematic paths and full electrical intention are not independently validated by this graph comparison. Fixed original report/receipt pins remain authoritative prior Native observations; no findings are normalized or removed. Unknown actual exporter grammar may still cause a safe parse failure/unqualified hypothesis; one export remains prospective. A completed diagnostic need not have rename_only_hypothesisTrue, and even true cannot admit HFE's current4Cu/rule-area/schema blockers or repair the original net names.

Review/draft elapsed wall through note preparation: 357.869 seconds, including requested enclosure review and controls drafting. Full reviewer CPU/model work unmeasured; external spend$0. Base and final draft pins are retained alongside this note. Actual Native, controls and whole-process cost remain unmeasured by this reviewer.
