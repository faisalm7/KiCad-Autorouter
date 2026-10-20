"""Retain all seven completed055 Native cases with unchanged shared030/042 helpers; no Native execution.

Shared030 retention, shared042 own-final checks and public complete-exit parsing.
Only owned metadata/log/net/PRL text is copied. CAD/plots/tools remain local.
GUI088 preparation is retained as preparation, never actual GUI qualification.
"""
from pathlib import Path
import ast, datetime, hashlib, json, math, os, re, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx, provenance as pv, floor_route as f
H = '38e193cdf94a814ee50baacb786e7f64214f02b8'
M = 'abadbf86758c7060be9a796f1ed58c6d3f08110b181481092bd15f47971774cb'
runtime = ROOT / '.runs/runtime-directory-055/runtime'
base = ROOT / '.runs/runtime055-native-qualification-002'
notes = ROOT / 'evidence/runtime055-native-milestone-001-notes'
target = ROOT / 'evidence/runtime055-native-milestone-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target), 'Fresh namespace; retain partial failure, never overwrite'
helpers = [
    (ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py', 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1', {'retain', 'cost'}),
    (ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-001.py', '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9', {'read', 'own_final'}),
    (ROOT / 'scripts/report_current_comparison.py', 'aa630b7d0aad9e7a2356ddc0fbb03894578fd4bff9a601e9a04c104fed86c9f7', {'require', 'digest', 'complete_cost'}),
]
for path, pin, names in helpers:
    assert p.sha(path) == pin
    nodes = [node for node in ast.parse(io.read_bytes(path, 4 * 1024**2)).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path) + '::retained-shared-functions', 'exec'), globals())
prior = ROOT / 'evidence/runtime055-ir-delivery-001.json'
assert p.sha(prior) == 'c4bde4bbf992480cd52468ed7cc76cd2b2a34cbfa2cd2d544f4e2d2312419daa'
pilot=read(prior);assert pilot['source_head']==H and pilot['runtime_manifest_sha256']==M
idx=ROOT/pilot['files_index']['path'];assert p.sha(idx)==pilot['files_index']['sha256']
refs = {}; files = []; material = []; total = 0; queue = {}; destinations = {}; omitted = []; sealed = {}
for row in read(idx)['files']:
    assert '.runs' not in Path(row['path']).parts
    refs.setdefault(row['sha256'], row['path'])
manifest = runtime / 'runtime-distribution.json'; assert p.sha(manifest) == M
frozen_path = base / 'frozen.json'
assert p.sha(frozen_path) == '0e10602c6268b4f1551dd2d9985cc6a38e82f1fab9ddaa79466cd4597a0ef955'
frozen = read(frozen_path)
assert frozen['source_head'] == H and frozen['runtime_manifest_sha256'] == M
cases = ['ordinary-npth2Cu', 'improve-pour-only', 'improve-fractional', 'improve-floor2Cu',
         'ordinary-alias2Cu', 'ordinary-whole4Cu', 'ordinary-hierarchy2Cu']
assert [row['case'] for row in frozen['protocols']] == cases


def add(path, name):
    path = Path(path); name = Path(name)
    assert path.is_file() and not path.is_symlink() and ROOT in path.parents
    assert not name.is_absolute() and not ({'.runs', '..'} & set(name.parts))
    if path in queue: return
    assert name not in destinations, ('Public destination collision', name, path, destinations.get(name))
    queue[path] = name; destinations[name] = path


def metadata(directory, name):
    """The old finite per-proof selection, covering every top-level text proof.

    Also retain job-owned PRL text needed by field/refill metadata proofs. No
    captured code, configuration cache, CAD geometry, DSN/SES or plot is copied.
    """
    for rel, pin in io.inventory(directory, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000).items():
        path = directory / rel; parts = Path(rel).parts
        keep = (len(parts) == 1 and path.suffix in ('.json', '.log', '.net')) or (
            len(parts) == 2 and parts[0].endswith('-input') and path.suffix == '.kicad_prl')
        if keep: add(path, Path(name) / rel)
        else: omitted.append(dict(original=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
            sha256=pin, reason='Raw CAD/transport/plot/code/cache remains local; metadata-only packet.'))


rows = []; source_snapshots = {}; output_snapshots = {}
for entry in frozen['protocols']:
    label = entry['case']; protocol = Path(entry['protocol']); folder = base / label
    assert protocol == folder / 'protocol.json' and p.sha(protocol) == entry['protocol_sha256']
    plan = read(protocol); output = Path(plan['output'])
    assert plan['kind'] == 'runtime055-six-stage-route-or-improve-CLI' and plan['case'] == label
    assert plan['runtime'] == str(runtime) and plan['source_head'] == H and plan['runtime_manifest_sha256'] == M
    assert output == runtime / '.runs' / (label + '-001')
    source = Path(plan['source']); hashes = plan['source_hashes']
    assert io.inventory(source.parent) == hashes; source_snapshots[source.parent] = hashes
    execution = read(folder / 'execution.json'); child_path = output / 'result.json'; child = read(child_path)
    w = Path(child['workspace']); assert w.parent == output and re.fullmatch('autorouter-gui-[0-9a-f]{32}', w.name)
    assert execution['child_receipt'] == str(child_path) and execution['child_sha256'] == p.sha(child_path)
    assert execution['protocol_sha256'] == entry['protocol_sha256'] and execution['error'] is None
    process = execution['process']
    assert process['status'] == 'success' and type(process['exit_code']) is int and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True
    assert all(type(n) in (int, float) and math.isfinite(n) and 0 <= n <= 240
               for n in (execution['complete_wall_seconds'], execution['complete_full_CPU_seconds']))
    assert child['status'] == 'completed' and child['workflow_delivered'] is True and child['accepted'] is False
    assert child['actual_GUI'] is False and child['source'] == str(source) and child['source_hashes'] == hashes
    assert child['method'] == plan['method'] == entry['method'] and child['tools'] == plan['tools']
    assert child['settings'] == plan['settings'] == read(folder / 'settings.json')
    assert p.sha(folder / 'settings.json') == plan['settings_sha256'] == child['settings_sha256']
    assert [stage['stage'] for stage in child['processes']] == ['preview', 'route', 'review', 'choice', 'export', 'verify_export']
    for stage in child['processes']:
        assert stage['process']['exit_code'] == 0 and stage['process']['cancel_requested'] is False
        assert stage['process']['log_truncated'] is False
        log = output / (stage['stage'] + '.log'); assert p.sha(log) == stage['log_sha256']
        add(log, Path('cases') / label / 'workflow' / log.name)
    counts = execution['Native_counts']
    assert execution['protected_count'] == plan['expected_protected_count']
    if plan['expected_counts'] is None:
        assert plan['warning_policy'] == 'retain_all_native_findings' and counts[:2] == [0, 0] and counts[3] == plan['expected_exclusions']
    else: assert counts == plan['expected_counts']
    route_path = w / 'route/result.json'; export_path = w / 'export/export.json'
    route = read(route_path); exported = read(export_path)
    assert route['accepted'] is True and exported['export_accepted'] is True
    assert route['candidate_sha256'] == exported['candidate_sha256'] == child['candidate_sha256']
    assert route['tools'] == exported['tools'] == plan['tools']
    for name, pin in plan['tools']['implementation_sha256'].items(): assert p.sha(runtime / name) == pin
    assert exported['inputs']['source'] == str(source) and exported['inputs']['receipt'] == str(route_path)
    assert exported['inputs']['receipt_sha256'] == p.sha(route_path) and exported['original_geometry_and_routing_unchanged'] is True
    original = sx.read(source); protected = p.protected_for_record(route, original)
    assert len(protected) == execution['protected_count']
    packets = [('parent', route, w / 'route'), ('export', exported, w / 'export/validation')]
    if entry['method'] == 'improve':
        inc = w / 'route/incumbent/result.json'
        assert route['incumbent']['receipt'] == str(inc)
        packets.append(('incumbent', read(inc), inc.parent))
        assert type(route['trials']) is list and len(route['trials']) <= 32
        for index, trial in enumerate(route['trials']):
            directory = w / 'route/trials' / ('trial-%04d' % index)
            assert trial['id'] == directory.name and trial['receipt'] == str(directory / 'result.json')
            data = read(directory / 'result.json')
            assert trial['status'] == data['status'] and trial['accepted'] is data['accepted']
            packets.append((trial['id'], data, directory))
    cli = [path for path in plan['tools']['files'] if Path(path).name == 'kicad-cli']
    assert len(cli) == 1
    proofs = {}
    for label2, data, directory in packets:
        candidate = directory / 'candidate' / source.name
        # Trial result.json is a final-validation record, not a Route receipt:
        # it has no source/tools/parity header. Caller hashes are bound by the
        # shared own_final input inventory, flags/report/process/candidate proof.
        # Parent, incumbent and export still require their complete headers.
        if directory.parent != w / 'route/trials':
            assert data['source_hashes'] == hashes and data['tools'] == plan['tools']
            assert data['schematic_parity'] == 'checked by final native DRC'
        else:
            assert data['id'] == directory.name and data['accepted'] is True
        assert p.sha(candidate) == data['candidate_sha256'] and p.immutable(sx.read(candidate)) == p.immutable(original)
        assert all(item in p.routes(sx.read(candidate)) for item in protected)
        proof = own_final(data, directory, directory, hashes, candidate)
        native_argv = read(directory / 'final-drc-process.json')['argv']
        assert native_argv[:3] == [cli[0], 'pcb', 'drc'] or native_argv[:len(f.SANDBOX) + 3] == [*f.SANDBOX, cli[0], 'pcb', 'drc']
        aux = [dict(name=path.name, sha256=p.sha(path)) for path in sorted(directory.iterdir())
               if path.is_file() and path.suffix in ('.json', '.log', '.net')]
        metadata(directory, Path('cases') / label / label2)
        proofs[label2] = dict(candidate_sha256=data['candidate_sha256'], accepted=data['accepted'] if 'accepted' in data else data['export_accepted'],
            Native_counts=[data['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')],
            ignored_checks=data['native']['ignored_checks'], own_final=proof, retained_auxiliary=aux,
            source_and_tool_lineage='Caller-frozen source hashes via shared own_final original-input binding; own final journal uses the exact case-pinned Native CLI. Trial headers are not synthesized.')
    assert counts == proofs['parent']['Native_counts'] == proofs['export']['Native_counts']
    review = read(w / 'review/review.json'); choice = read(w / 'choice/choice.json')
    assert review['receipt_sha256'] == choice['receipt_sha256'] == p.sha(route_path)
    assert choice['choice'] == 'accept' and choice['applied'] is False
    assert choice['review_sha256'] == p.sha(w / 'review/review.json')
    for path in (protocol, folder / 'settings.json', folder / 'execution.json', folder / 'enclosure/process.json', folder / 'enclosure/command.log'):
        add(path, Path('cases') / label / 'workflow' / path.relative_to(folder))
    add(child_path, Path('cases') / label / 'workflow/child-result.json')
    for path in (w / 'settings.json', w / 'review/review.json', w / 'choice/choice.json', export_path):
        add(path, Path('cases') / label / 'workflow/job' / path.relative_to(w))
    metadata(w / 'review/plot-work', Path('cases') / label / 'workflow/review-plot-metadata')
    timing=folder/'complete-command-and-time.log';add(timing,Path('cases')/label/timing.name)
    add(folder/'batch-process.json',Path('cases')/label/'batch-process.json')
    complete=complete_cost(timing)
    output_snapshots[output] = io.inventory(output, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000)
    rows.append(dict(case=label, method=entry['method'], protocol_sha256=entry['protocol_sha256'],
        execution_sha256=p.sha(folder / 'execution.json'), child_sha256=p.sha(child_path),
        route_sha256=p.sha(route_path), export_sha256=p.sha(export_path), source_hashes=hashes, source_unchanged=True,
        controls_passed=True, workflow_delivered=True, actual_GUI=False, complete_external_cost=complete,
        enclosure_sample_wall_seconds=execution['complete_wall_seconds'], enclosure_sample_full_CPU_seconds=execution['complete_full_CPU_seconds'],
        Native_counts=counts, protected_count=execution['protected_count'], own_finals=proofs,
        improvements=route.get('improvements'), trials=route.get('trials'), metrics=route['metrics']))

assert len(rows) == 7
complete = dict(wall_seconds=round(sum(row['complete_external_cost']['wall_seconds'] for row in rows), 2),
                CPU_seconds=round(sum(row['complete_external_cost']['CPU_seconds'] for row in rows), 2))
batch_complete=complete_cost(ROOT/'.runs/runtime055-native-batch-001-time.log')
prepared_path=runtime/'.runs/gui-session088/prepared-state.json';prepared=read(prepared_path)
assert prepared['source_head']==H and prepared['runtime_manifest_sha256']==M and prepared['actual_GUI_qualified'] is False
invalid_base=ROOT/'.runs/runtime055-native-controls-001/invalid';invalid_enclosure=read(invalid_base/'enclosure/result.json');assert invalid_enclosure['passed']
invalid_path=Path(invalid_enclosure['child_receipt']);invalid=read(invalid_path);assert invalid['control_passed']
for path in (manifest,frozen_path,base/'batch-result.json',prepared_path,runtime/'.runs/gui-session088/protocol-required-001.json',
 ROOT/'.runs/qualify-runtime055-native-batch-001.py',ROOT/'.runs/runtime055-native-batch-001-controller.log',ROOT/'.runs/runtime055-native-batch-001-time.log',
 ROOT/'.runs/freeze-runtime055-native-qualification-001.py',ROOT/'.runs/freeze-runtime055-native-qualification-001.log',ROOT/'.runs/freeze-runtime055-native-qualification-001-time.log',
 ROOT/'.runs/freeze-runtime055-native-qualification-002.py',ROOT/'.runs/freeze-runtime055-native-qualification-002.log',ROOT/'.runs/freeze-runtime055-native-qualification-002-time.log',
 ROOT/'.runs/runtime055-native-qualification-001/frozen.json',base/'doctor.json',base/'doctor-process.json',base/'tools-defaults.json',base/'tools-defaults-process.json',
 ROOT/'.runs/prepare-runtime055-gui088.py',ROOT/'.runs/prepare-runtime055-gui088.log',ROOT/'.runs/prepare-runtime055-gui088-time.log',
 ROOT/'.runs/freeze-runtime055-native-invalid-001.py',ROOT/'.runs/freeze-runtime055-native-invalid-001.log',ROOT/'.runs/freeze-runtime055-native-invalid-001-time.log',
 ROOT/'.runs/qualify-runtime055-hole-safety-001.py',ROOT/'.runs/runtime055-native-invalid-001.log',ROOT/'.runs/runtime055-native-invalid-001-time.log',
 invalid_base/'protocol.json',invalid_base/'frozen.json',invalid_base/'enclosure/result.json',invalid_base/'enclosure/process.json',invalid_base/'enclosure/command.log',invalid_path,
 Path(__file__),ROOT/'LICENSE'):
 relative=path.relative_to(ROOT);safe=Path(*('retained-run' if part=='.runs' else part for part in relative.parts));add(path,Path('controls')/safe)
for path,pin,names in helpers:add(path,Path('shared-helpers')/path.name)
additional=dict(GUI088_preparation=complete_cost(ROOT/'.runs/prepare-runtime055-gui088-time.log'),native_plan001_doctor_query=complete_cost(ROOT/'.runs/freeze-runtime055-native-qualification-001-time.log'),native_plan002_label_correction=complete_cost(ROOT/'.runs/freeze-runtime055-native-qualification-002-time.log'),invalid_freeze=complete_cost(ROOT/'.runs/freeze-runtime055-native-invalid-001-time.log'),invalid_complete=complete_cost(ROOT/'.runs/runtime055-native-invalid-001-time.log'))
# Preflight deduplicated payload before the first new public file. Reserve a
# conservative allowance for the small index/summary; never raise original caps.
omitted = list({row['original']: row for row in omitted if ROOT / row['original'] not in queue}.values())
known = set(refs); planned = 0; count = 0
for path in queue:
    raw = io.read_bytes(path, 4 * 1024**2); assert b'\0' not in raw; raw.decode('utf8')
    pin = hashlib.sha256(raw).hexdigest(); sealed[path] = (len(raw), pin)
    if pin not in known: known.add(pin); planned += len(raw); count += 1
assert count < 1998 and planned + sum(512 + 3 * len(str(path)) + 3 * len(str(name)) for path, name in queue.items()) + len(json.dumps(omitted, indent=2).encode()) + 512 * 1024 < 16 * 1024**2, 'Split meaningful packets before writing; never raise caps'
notes.mkdir()
for path, name in queue.items(): retain(path, name)
for path, (size, pin) in sealed.items(): assert path.stat().st_size == size and p.sha(path) == pin
for path, hashes in source_snapshots.items(): assert io.inventory(path) == hashes
for path, hashes in output_snapshots.items(): assert io.inventory(path, max_bytes=256 * 1024**2, max_files=8000, max_entries=16000) == hashes
index = notes / 'files.json'
index_data = dict(schema=1, files=files, material=material, omitted=omitted)
assert total + len(json.dumps(index_data, indent=2).encode()) < 16 * 1024**2 and len(json.dumps(index_data).encode()) < 4 * 1024**2
p.save_json(index, index_data)
record=dict(schema=1,kind='runtime055-seven-completed-native-workflows-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,Native_cohort_passed=True,release_qualified=False,accepted=False,project_complete=False,actual_GUI=False,human_review=False,cases=rows,complete_deliveries_external_cost=complete,complete_batch_external_cost=batch_complete,additional_setup_complete_external=additional,
 IR_repair=dict(path=str(prior.relative_to(ROOT)),sha256=p.sha(prior),files_index=pilot['files_index'],scope='Separately completed single exposed IR repair, full205/build and costs; not a stitched comparison.'),
 invalid_controls=dict(passed=True,receipt_sha256=p.sha(invalid_path),cases=[dict(case=row['case'],passed=row['passed'],native=row.get('native'),other={k:v for k,v in row.items() if k not in ('steps','native','case','passed')}) for row in invalid['cases']],scope='Fresh actual short/hole Native negatives and protectedwidth+1nm original-copper refusal; no population falseacceptance rate.'),
 GUI088=dict(state='PREPARED_ONLY',prepared_state_sha256=p.sha(prepared_path),actual_GUI_qualified=False,scope='Two fresh roles prepared from these own current Native proofs; actual GUI/installation/cancellation/freshness observations remain pending. No050 GUI transfer.'),
 preparation_correction='Population001 was never dispatched.002 corrects only a stale explanatory installed053 ordinal to055 and reuses its completed doctor/query. Original001 and costs retained; all binding fields/settings/constraints/budgets/outputs unchanged. No duplicated Native experiment.',
 result='All seven frozen current055 workflows completed six actual CLI stages with own final/refill/fullSCH/original/protected/Default/fieldPRL evidence. Protected NPTH1, three Improve1each, alias4, whole4Cu10; hierarchy0 is not a protection positive. All warnings and two original ignored checks retained. Owned functionality regression, not unrelated-family routing/cleanup/electrical or fair-comparison gain.',
 accounting='Per-case complete -lp exits and batch complete -lp recorded separately; batch includes those events plus dispatch/cleanup overhead. Never add them together. Nested Native/workflow/parent/trial/export samples overlap. Full205/build/singleIR retain earlier receipt costs. Doctor/query, label correction, invalids and GUI preparation additional. Authoring/AI review/curation/interactive GUI partly unmetered, notzero.',
 backup_scope='Small owned metadata/log/net/PRL text for auditedGit; CAD/DSN/SES/plots/ZIP/JAR/tools/caches omitted and retained on thisMac/outside010. No fullrawbackup/restoration, cleanOS/standalone/Windows/human/physical/release claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
assert len(json.dumps(record, indent=2).encode()) < 4 * 1024**2
assert total + index.stat().st_size + len(json.dumps(record, indent=2).encode()) < 16 * 1024**2
p.save_json(target, record)
print(json.dumps(dict(path=str(target), sha256=p.sha(target), files=len(files), bytes=total, material=len(material), complete=complete, Native_executed=False, actual_GUI=False)))
