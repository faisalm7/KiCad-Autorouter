"""Retain eleven completed057 Native cases with unchanged shared030/042 helpers.

DRAFT ONLY: do not execute until all eleven cases, invalids and the separately
retained current057 IR regression are terminal. This never executes Native.
Only owned metadata/log/net/PRL text is copied. CAD/plots/tools remain local.
No current057 GUI preparation or qualification is implied. Completed batch,
invalid-enclosure/child, complete-time and IR packet pins are required CLI inputs;
never guess future hashes or reuse old-runtime results. The final IR kind is also
a required reviewed CLI input until its public packet exists.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, math, os, re, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx, provenance as pv, floor_route as f
H = 'ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
M = '9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
runtime = ROOT / '.runs/runtime-directory-057/runtime'
base = ROOT / '.runs/runtime057-native-qualification-001'
notes = ROOT / 'evidence/runtime057-native-milestone-001-notes'
target = ROOT / 'evidence/runtime057-native-milestone-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target), 'Fresh namespace; retain partial failure, never overwrite'
helpers = [
    (ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py', 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1', {'retain', 'cost'}),
    (ROOT / '.runs/curate-gui-runtime042-081-recovery-deliveries-001.py', '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9', {'read', 'own_final'}),
    (ROOT / 'evidence/runtime050-native-milestone-002-notes/shared-helpers/report_current_comparison.py', 'aa630b7d0aad9e7a2356ddc0fbb03894578fd4bff9a601e9a04c104fed86c9f7', {'require', 'digest', 'complete_cost'}),
]
for path, pin, names in helpers:
    assert p.sha(path) == pin
    nodes = [node for node in ast.parse(io.read_bytes(path, 4 * 1024**2)).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path) + '::retained-shared-functions', 'exec'), globals())
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--ir-packet-sha256', required=True)
ap.add_argument('--ir-packet-kind', required=True, help='Exact reviewed kind of the completed current057 public IR packet; not guessed while drafting.')
ap.add_argument('--native-batch-sha256', required=True)
ap.add_argument('--native-batch-time-sha256', required=True)
ap.add_argument('--invalid-enclosure-sha256', required=True)
ap.add_argument('--invalid-child-sha256', required=True)
ap.add_argument('--invalid-time-sha256', required=True)
args = ap.parse_args()
for value in (args.ir_packet_sha256,args.native_batch_sha256,args.native_batch_time_sha256,
              args.invalid_enclosure_sha256,args.invalid_child_sha256,args.invalid_time_sha256):
    assert re.fullmatch('[0-9a-f]{64}', value)
assert args.ir_packet_kind.startswith('runtime057-') and len(args.ir_packet_kind)<=160
prior = ROOT / 'evidence/runtime057-ir-delivery-001.json'
assert p.sha(prior) == args.ir_packet_sha256
pilot=read(prior)
assert pilot['kind']==args.ir_packet_kind
assert pilot['source_head']==H and pilot['runtime_manifest_sha256']==M
assert pilot['full207']['passed'] is True and pilot['workflow_delivered'] is True
assert pilot['actual_GUI'] is False and pilot['project_complete'] is False
idx=ROOT/pilot['files_index']['path'];assert p.sha(idx)==pilot['files_index']['sha256']
refs = {}; files = []; material = []; total = 0; queue = {}; destinations = {}; omitted = []; sealed = {}
for row in read(idx)['files']:
    assert '.runs' not in Path(row['path']).parts
    refs.setdefault(row['sha256'], row['path'])
manifest = runtime / 'runtime-distribution.json'; assert p.sha(manifest) == M
full_path=ROOT/'.runs/full-integration-207/execution.json';full_plan_path=ROOT/'.runs/full-integration-207/protocol.json'
assert p.sha(full_path)=='6e5f0046d7a19d8dd54bdd6ee1d473f25cdf06d137e097a44798800fd7d2ad5f'
assert p.sha(full_plan_path)=='06ad39d26d909b36e6eef213eeb39218bf33ba4274d4dd4ace5a980ee11a24d2'
full=read(full_path);full_plan=read(full_plan_path)
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status']=='success' and full['process']['exit_code']==0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
assert full_plan['tools']['git_head']==H
for name,pin in full_plan['tools']['implementation_sha256'].items():
    assert full_plan['source_sha256'][name]==p.sha(runtime/name)==pin
frozen_path = base / 'frozen.json'
assert p.sha(frozen_path) == 'ffb15deb4ead2725095dab6e745ad119bba721c3cc5ac594115cbfc6544d1733'
frozen = read(frozen_path)
assert frozen['source_head'] == H and frozen['runtime_manifest_sha256'] == M
cases = ['via-high-whole2Cu', 'via-high-partial2Cu', 'via-high-whole4Cu', 'via-high-partial4Cu',
         'ordinary-npth2Cu', 'improve-pour-only', 'improve-fractional', 'improve-floor2Cu',
         'ordinary-alias2Cu', 'ordinary-whole4Cu', 'ordinary-hierarchy2Cu']
assert [row['case'] for row in frozen['protocols']] == cases
assert p.sha(ROOT/'.runs/freeze-runtime057-native-qualification-001.py') == frozen['controller_sha256']
assert p.sha(ROOT/'.runs/qualify-runtime057-native-batch-001.py') == 'bdaa085a565c04ce8d655b6c801175b9f9fa065f85013c2bd3606c7e748fd454'
assert p.sha(ROOT/'.runs/enclose-runtime044-workflow-001.py') == frozen['enclosure_sha256']
assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py') == frozen['driver_sha256']
batch_path=base/'batch-result.json';assert p.sha(batch_path)==args.native_batch_sha256
batch = read(batch_path)
assert batch['passed'] is True and batch['actual_GUI'] is False
assert [row['case'] for row in batch['rows']] == cases and all(row['passed'] is True for row in batch['rows'])
assert batch['frozen_sha256'] == p.sha(frozen_path)
assert batch['controller_sha256'] == p.sha(ROOT/'.runs/qualify-runtime057-native-batch-001.py')


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
    assert plan['kind'] == 'runtime057-six-stage-route-or-improve-CLI' and plan['case'] == label
    assert plan['runtime'] == str(runtime) and plan['source_head'] == H and plan['runtime_manifest_sha256'] == M
    assert output == runtime / '.runs' / (label + '-001')
    source = Path(plan['source']); hashes = plan['source_hashes']
    assert io.inventory(source.parent) == hashes; source_snapshots[source.parent] = hashes
    execution = read(folder / 'execution.json'); child_path = output / 'result.json'; child = read(child_path)
    w = Path(child['workspace']); assert w.parent == output and re.fullmatch('autorouter-gui-[0-9a-f]{32}', w.name)
    assert execution['child_receipt'] == str(child_path) and execution['child_sha256'] == p.sha(child_path)
    assert execution['protocol_sha256'] == entry['protocol_sha256'] and execution['error'] is None
    batch_row=batch['rows'][cases.index(label)]
    assert batch_row['execution_sha256']==p.sha(folder/'execution.json')
    assert batch_row['process_sha256']==p.sha(folder/'batch-process.json')
    assert batch_row['complete_log_sha256']==p.sha(folder/'complete-command-and-time.log')
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
    if entry['method']=='route':
        expected_score='via_high' if label.startswith('via-high-') else None
        assert plan['settings']['scoring_preference']==expected_score and route['scoring_variant']==expected_score
        assert route['routing_preferences']['effective']==plan['settings']
        if expected_score is not None:
            assert route['engine_budget']['scoring']==dict(variant='via_high',via_costs=100,plane_via_costs=10,
                argv=['--router.scoring.via_costs=100','--router.scoring.plane_via_costs=10'])
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
        scoring_preference=plan['settings']['scoring_preference'],
        improvements=route.get('improvements'), trials=route.get('trials'), metrics=route['metrics']))

assert len(rows) == 11
complete = dict(wall_seconds=round(sum(row['complete_external_cost']['wall_seconds'] for row in rows), 2),
                CPU_seconds=round(sum(row['complete_external_cost']['CPU_seconds'] for row in rows), 2))
batch_time_path=ROOT/'.runs/runtime057-native-batch-001-time.log';assert p.sha(batch_time_path)==args.native_batch_time_sha256
batch_complete=complete_cost(batch_time_path)
invalid_base=ROOT/'.runs/runtime057-native-controls-001/invalid'
assert p.sha(invalid_base/'protocol.json')=='db8f43de6cce1dd9ae9cc0d99e8057b7316e010d684c7fc39f8db1278f2eef0c'
invalid_protocol=read(invalid_base/'protocol.json');invalid_frozen=read(invalid_base/'frozen.json')
assert invalid_protocol['kind']=='runtime057-via-high-NPTH-three-invalid-controls-v1'
assert invalid_protocol['source_head']==H and invalid_protocol['runtime_manifest_sha256']==M
assert invalid_protocol['runtime']==str(runtime) and invalid_protocol['expected_scoring']=='via_high'
assert invalid_frozen['protocol_sha256']==p.sha(invalid_base/'protocol.json')
invalid_enclosure_path=invalid_base/'enclosure/result.json';assert p.sha(invalid_enclosure_path)==args.invalid_enclosure_sha256
invalid_enclosure=read(invalid_enclosure_path);assert invalid_enclosure['passed'] is True and invalid_enclosure['status']=='completed'
assert invalid_enclosure['process']==read(invalid_base/'enclosure/process.json')
assert invalid_enclosure['process']['status']=='success' and invalid_enclosure['process']['exit_code']==0
assert invalid_enclosure['process']['cleanup_complete'] is True and invalid_enclosure['process']['log_truncated'] is False
invalid_path=Path(invalid_enclosure['child_receipt']);assert p.sha(invalid_path)==invalid_enclosure['child_sha256']==args.invalid_child_sha256
invalid=read(invalid_path)
assert invalid_path==Path(invalid_protocol['output'])/'result.json' and invalid['control_passed'] is True
assert invalid['status']=='completed' and invalid['accepted'] is False and invalid['production_admitted'] is False
assert invalid['source_head']==H and invalid['runtime_manifest_sha256']==M
assert invalid['protocol_sha256']==p.sha(invalid_base/'protocol.json')
assert invalid['controller_sha256']==invalid_protocol['controller_sha256']==p.sha(Path(invalid_protocol['controller']))
assert p.sha(ROOT/'.runs/qualify-runtime057-hole-safety-001.py')==invalid['controller_sha256']
assert invalid['tools']==read(base/cases[0]/'protocol.json')['tools']
positive_child=read(runtime/'.runs/via-high-whole2Cu-001/result.json')
assert invalid['positive_receipt']==str(Path(positive_child['workspace'])/'route/result.json')
assert p.sha(Path(invalid['positive_receipt']))==invalid['positive_sha256']==rows[0]['route_sha256']
assert io.inventory(Path(invalid['source']).parent)==invalid['source_hashes']
assert [row['case'] for row in invalid['cases']]==['short','protected-width','hole-clearance']
invalid_proofs={}
for row in invalid['cases']:
    assert row['passed'] is True and all(step['cleanup_complete'] is True for step in row['steps'])
    directory=invalid_path.parent/row['case']
    if row['case']=='protected-width':
        assert row['rejection']=='protected route changed'
        assert [row['diagnostic_native'][key] for key in ('opens','blocking','warnings','exclusions')][:2]==[0,0]
        invalid_proofs[row['case']]=dict(diagnostic_only=True,final_acceptance=False,
            diagnostic_report_sha256=p.sha(directory/'diagnostic-drc.json'),
            diagnostic_process_sha256=p.sha(directory/'diagnostic-drc-process.json'),
            diagnostic_binding_sha256=p.sha(directory/'diagnostic-drc-binding.json'))
    else:
        # Same actual row and shared042 own-final checker, with only the raw
        # controller's report_sha256 field mapped to the checker's spelling.
        view=dict(row,native_report_sha256=row['report_sha256'])
        candidate=directory/'candidate'/Path(invalid['source']).name
        invalid_proofs[row['case']]=own_final(view,directory,directory,invalid['source_hashes'],candidate)
        assert row['native']['blocking']>0
    metadata(directory,Path('invalid-controls')/row['case'])
output_snapshots[invalid_path.parent]=io.inventory(invalid_path.parent,max_bytes=256*1024**2,max_files=8000,max_entries=16000)
for path in (manifest,frozen_path,base/'batch-result.json',
 ROOT/'.runs/qualify-runtime057-native-batch-001.py',ROOT/'.runs/runtime057-native-batch-001.log',ROOT/'.runs/runtime057-native-batch-001-time.log',
 ROOT/'.runs/freeze-runtime057-native-qualification-001.py',ROOT/'.runs/freeze-runtime057-native-qualification-001.log',ROOT/'.runs/freeze-runtime057-native-qualification-001-time.log',
 base/'doctor.json',base/'doctor-process.json',base/'tools-defaults.json',base/'tools-defaults-process.json',
 ROOT/'.runs/enclose-runtime044-workflow-001.py',ROOT/'scripts/qualify_runtime_workflow.py',
 ROOT/'.runs/freeze-runtime057-native-invalid-001.py',ROOT/'.runs/freeze-runtime057-native-invalid-001.log',ROOT/'.runs/freeze-runtime057-native-invalid-001-time.log',
 ROOT/'.runs/qualify-runtime057-hole-safety-001.py',ROOT/'.runs/runtime057-native-invalid-001.log',ROOT/'.runs/runtime057-native-invalid-001-time.log',
 invalid_base/'protocol.json',invalid_base/'frozen.json',invalid_base/'enclosure/result.json',invalid_base/'enclosure/process.json',invalid_base/'enclosure/command.log',invalid_path,
 Path(__file__),ROOT/'LICENSE'):
 relative=path.relative_to(ROOT);safe=Path(*('retained-run' if part=='.runs' else part for part in relative.parts));add(path,Path('controls')/safe)
for path,pin,names in helpers:add(path,Path('shared-helpers')/path.name)
invalid_time_path=ROOT/'.runs/runtime057-native-invalid-001-time.log';assert p.sha(invalid_time_path)==args.invalid_time_sha256
additional=dict(native_plan_doctor_query=complete_cost(ROOT/'.runs/freeze-runtime057-native-qualification-001-time.log'),
 invalid_freeze001=complete_cost(ROOT/'.runs/freeze-runtime057-native-invalid-001-time.log'),
 invalid_complete001=complete_cost(invalid_time_path))
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
assert p.sha(prior)==args.ir_packet_sha256 and p.sha(idx)==pilot['files_index']['sha256']
assert p.sha(frozen_path)==batch['frozen_sha256'] and p.sha(manifest)==M
assert p.sha(batch_path)==args.native_batch_sha256 and p.sha(batch_time_path)==args.native_batch_time_sha256
assert p.sha(invalid_base/'protocol.json')=='db8f43de6cce1dd9ae9cc0d99e8057b7316e010d684c7fc39f8db1278f2eef0c'
assert p.sha(invalid_enclosure_path)==args.invalid_enclosure_sha256 and p.sha(invalid_path)==args.invalid_child_sha256
assert p.sha(invalid_time_path)==args.invalid_time_sha256
assert p.sha(full_path)=='6e5f0046d7a19d8dd54bdd6ee1d473f25cdf06d137e097a44798800fd7d2ad5f'
assert p.sha(full_plan_path)=='06ad39d26d909b36e6eef213eeb39218bf33ba4274d4dd4ace5a980ee11a24d2'
index = notes / 'files.json'
index_data = dict(schema=1, files=files, material=material, omitted=omitted)
assert total + len(json.dumps(index_data, indent=2).encode()) < 16 * 1024**2 and len(json.dumps(index_data).encode()) < 4 * 1024**2
p.save_json(index, index_data)
record=dict(schema=1,kind='runtime057-eleven-completed-native-workflows-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=H,runtime_manifest_sha256=M,Native_cohort_passed=True,release_qualified=False,accepted=False,project_complete=False,actual_GUI=False,human_review=False,cases=rows,complete_deliveries_external_cost=complete,complete_batch_external_cost=batch_complete,additional_setup_complete_external=additional,
 IR_delivery=dict(path=str(prior.relative_to(ROOT)),sha256=p.sha(prior),files_index=pilot['files_index'],scope='Separately completed single exposed IR default-score Improve, full207/build and costs; not a stitched comparison or an unchanged056 receipt transfer.'),
 invalid_controls=dict(passed=True,expected_scoring='via_high',receipt_sha256=p.sha(invalid_path),own_final_proofs=invalid_proofs,cases=[dict(case=row['case'],passed=row['passed'],native=row.get('native'),other={k:v for k,v in row.items() if k not in ('steps','native','case','passed')}) for row in invalid['cases']],scope='Fresh actual short/hole Native negatives and separately Native-clean protectedwidth+1nm original-copper refusal, all from the explicit via_high positive; no population falseacceptance rate.'),
 GUI=dict(state='UNQUALIFIED_CURRENT_RUNTIME',actual_GUI_qualified=False,scope='No057 GUI preparation or actual observations are supplied by this packet. Prior056 GUI observations transfer no GUI authority.'),
 result='All eleven frozen current057 workflows completed six actual CLI stages with own final/refill/fullSCH/original/protected/Default/fieldPRL evidence. Four explicit high-via-cost whole/partial2/4Cu controls precede seven unchanged default-score regressions. Default remains None; no reduced-via, completion or quality gain follows. Protected counts and all Native warnings/ignored checks remain per case; hierarchy0 is not a protection positive. Owned functionality regression, not unrelated-family routing/cleanup/electrical or fair-comparison gain.',
 accounting='Per-case complete -lp exits and batch complete -lp recorded separately; batch includes those events plus dispatch/cleanup overhead. Never add them together. Nested Native/workflow/parent/trial/export samples overlap. Full207/build/singleIR retain the separately pinned receipt costs. Doctor/query, the current057 invalid freeze and single completed001 invalid control are additional. No current057 failed attempt or Native repeat is asserted. Authoring/AI review/curation/interactive GUI partly unmetered, notzero.',
 backup_scope='Small owned metadata/log/net/PRL text for auditedGit; CAD/DSN/SES/plots/ZIP/JAR/tools/caches omitted and retained on thisMac/outside010. No fullrawbackup/restoration, cleanOS/standalone/Windows/human/physical/release claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
assert len(json.dumps(record, indent=2).encode()) < 4 * 1024**2
assert total + index.stat().st_size + len(json.dumps(record, indent=2).encode()) < 16 * 1024**2
p.save_json(target, record)
print(json.dumps(dict(path=str(target), sha256=p.sha(target), files=len(files), bytes=total, material=len(material), complete=complete, Native_executed=False, actual_GUI=False)))
