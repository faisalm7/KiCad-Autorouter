"""Prepare exact034 critical-control retention; lead reviews before execution.

Reuse033's bounded retention functions. Existing readers inspect recorded
Native proof only: this curator never launches Native, routing, GUI or tests.
"""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-034/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from autorouter import review_export as ex, local_settings as local

HEAD = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
MANIFEST = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
notes = ROOT / 'evidence/runtime034-native-invalid-001-notes'
packet = ROOT / 'evidence/runtime034-native-invalid-001.json'
assert not notes.exists() and not packet.exists()
refs = {}; files = []; material = []; total = 0
reference_records = []
for name, pin in (
        ('runtime034-ordinary-install-001', 'a72eeb6196326003182ee144630b6e774a00963a3870bd42c835a5755c3f4aee'),
        ('runtime033-native-invalid-001', '2a0ee04a4959ae98c46111ddc7468e201d1126f1c531e1e5d7edd4d233d9baa3')):
    path = ROOT / ('evidence/' + name + '.json'); assert p.sha(path) == pin
    data = f.read_json(path); index = ROOT / data['files_index']['path']
    assert p.sha(index) == data['files_index']['sha256']; idx = f.read_json(index)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=pin,
        files_index=data['files_index'], scope='Exact-byte retention only; no inherited033 qualification.'))
    for row in idx.get('files', []) + idx.get('material', []):
        target = row.get('path', row.get('retained'))
        assert (ROOT / target).resolve().is_relative_to(ROOT / 'evidence')
        refs.setdefault(row['sha256'], target)
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
retention_pin = p.sha(helper)
functions = [n for n in ast.parse(helper.read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name in ('retain', 'tree', 'cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))

base = ROOT / '.runs/runtime034-ordinary-native-invalid-002'
assert p.sha(base / 'protocol.json') == '63c7402c77d7c787f54b462bb035c32c5f910845d98d17e8aac3b95d28fb1545'
plan = f.read_json(base / 'protocol.json'); out = Path(plan['output'])
assert out == runtime / '.runs/native7-comparison-control-runtime034-invalid-001'
assert plan['runtime'] == str(runtime) and plan['source_head'] == HEAD
assert plan['runtime_manifest_sha256'] == p.sha(runtime / 'runtime-distribution.json') == MANIFEST
assert plan['kind'] == 'runtime034-ordinary-Native-invalid-controls-v1'
assert p.sha(Path(plan['controller'])) == plan['controller_sha256'] == plan['helper_sha256'] == '3b72b1e93d90e3b53cb05180866617f72bc9be9ee5149f7a7f0da893a6ec1680'
assert plan['whole_wall_full_cpu_seconds'] == 180 and plan['route_seconds'] == 90
assert plan['scope'] == 'partial_completion' and plan['profile'] == 'standard'
assert plan['adapter'] == 'both' and plan['scoring_variant'] is None and plan['protected_routes'] == 4
tools = p.tool_manifest(); assert tools == plan['tools'] and tools['git_head'] == HEAD
assert p.sha(out / 'result.json') == '16e393de8d11d02e777fff8c2d4ac6f11291b7d970c930d91ee50268c6ee1ce4'
outer = f.read_json(base / 'enclosure/result.json'); result = f.read_json(out / 'result.json')
assert outer['passed'] is True and outer['status'] == 'completed'
assert outer['protocol_sha256'] == p.sha(base / 'protocol.json')
assert outer['child_receipt'] == str(out / 'result.json') and outer['child_sha256'] == p.sha(out / 'result.json')
assert outer['process']['status'] == 'success' and outer['process']['exit_code'] == 0
assert outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False
assert max(outer['complete_wall_seconds'], outer['complete_full_CPU_seconds']) < 180
assert result['control_passed'] is True and result['status'] == 'completed'
assert result['accepted'] is result['routing_accepted'] is result['export_accepted'] is result['production_admitted'] is False
assert result['source_head'] == HEAD and result['runtime_manifest_sha256'] == MANIFEST
assert result['tools'] == tools and result['protocol_sha256'] == p.sha(base / 'protocol.json')
assert f.evidence_inventory(out) == result['evidence_sha256'] == outer['completed_evidence']
assert [row['label'] for row in result['cases']] == ['partial-short', 'partial-protected-width']
assert all(row['control_observed'] is True and row['protected_routes'] == 4
           and row['accepted'] is False and row['routing_accepted'] is False for row in result['cases'])
short, width = result['cases']
assert short['native']['blocking'] > 0 and 'shorting_items' in {q['type'] for q in short['native']['findings']}
assert width['Native_diagnostic_routing_accepted'] is True and width['mutation']['added_nanometres'] == 1
assert width['rejection'] == 'protected route changed' and width['no_additional_native_after_invariant_refusal'] is True
assert [width['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]

failed_base = ROOT / '.runs/runtime034-ordinary-native-invalid-001'
failed = f.read_json(failed_base / 'tools-defaults-process.json')
assert failed['status'] == 'nonzero_exit' and failed['exit_code'] == 1
assert failed['cleanup_complete'] is True and not failed['log_truncated']
assert 'ModuleNotFoundError' in (failed_base / 'tools-defaults.json').read_text()
assert not (failed_base / 'protocol.json').exists()
query_path = Path(plan['preparation']['tools_query_path']); query = f.read_json(query_path)
assert query_path == base / 'tools-defaults.json' and query['tools'] == tools
assert p.sha(query_path) == plan['preparation']['tools_query_sha256']
assert p.sha(base / 'tools-defaults-process.json') == plan['preparation']['tools_query_process_sha256']
query_process = f.read_json(base / 'tools-defaults-process.json')
assert query_process['status'] == 'success' and query_process['exit_code'] == 0
assert query_process['cleanup_complete'] is True and not query_process['log_truncated']

pins = [(base / 'protocol.json', p.sha(base / 'protocol.json')),
        (out / 'result.json', p.sha(out / 'result.json')),
        (base / 'enclosure/result.json', p.sha(base / 'enclosure/result.json'))]
packets = []; pairs = []; originals = []; positive_material = []
for label in ('whole4Cu', 'partial2Cu'):
    item = plan[label + '_positive']; workspace = Path(item['workspace'])
    for name in ('protocol', 'execution', 'result', 'route', 'export'):
        path = Path(item[name + '_path']); assert p.sha(path) == item[name + '_sha256']
        pins.append((path, item[name + '_sha256']))
    caller = f.read_json(Path(item['protocol_path']))
    assert caller['kind'] == 'frozen-runtime033-ordinary-workflow'
    assert caller['runtime'] == str(runtime) and caller['source_head'] == HEAD and caller['runtime_manifest_sha256'] == MANIFEST
    assert caller['source'] == item['source'] and caller['source_hashes'] == item['source_hashes']
    source = Path(item['source']); assert p.tree_hash(source.parent) == item['source_hashes']
    originals.append((source.parent, item['source_hashes']))
    with p.validation_readback_session():
        assert p.check_result(Path(item['route_path']))['current'] is True
        assert ex.check_export(Path(item['export_path']))['current'] is True
    packets.extend([(Path(item['route_path']).parent, f.read_json(Path(item['route_path']))),
                    (workspace / 'export/validation', f.read_json(Path(item['export_path'])))])
    preview = f.read_json(workspace / 'review/review.json')['preview']; plot = workspace / 'review/plot-work'
    for step in preview['steps']:
        assert step['cwd'] == str(plot)
        process = f.process_check(plot, preview, step['name'], step['argv'])
        pairs.append((plot, f.read_json(plot / (step['name'] + '-input-binding.json')), process))
    folder = Path(item['output'])
    positive_material.append((folder, io.inventory(folder, max_bytes=256*1024**2, max_files=8000, max_entries=16000)))
for row in result['cases']:
    candidate = Path(row['candidate']); validation = candidate.parent.parent
    assert p.sha(candidate) == row['candidate_sha256']
    before = dict(plan['source_hashes']); before[candidate.name] = row['candidate_sha256']
    name = 'final-drc' if row['label'] == 'partial-short' else 'diagnostic-full-drc'
    assert f.check_drc_stage(validation, row, name, candidate, validation / (name + '-input') / candidate.name,
        False, before, schematic_parity=True, sandboxed=False) == row['native']
    if row['label'] == 'partial-short':
        refill = validation / 'refill' / candidate.name
        before[candidate.name] = row['mutation']['pre_native_sha256']
        native = p.parse_report(validation / 'refill-drc.json', candidate.name)
        assert f.check_drc_stage(validation, row, 'refill-drc', refill, refill, True, before,
            schematic_parity=False, sandboxed=False) == native
    packets.append((validation, row))

tree(failed_base, Path('preparation/failed-freezer001'))
tree(base, Path('enclosure-and-preparation002')); tree(out, Path('cases'))
for name in ('qualify-runtime034-ordinary-native-invalid-001.py',
        'freeze-runtime034-ordinary-native-invalid-001.py', 'freeze-runtime034-ordinary-native-invalid-002.py',
        'runtime034-ordinary-native-invalid-preparation-001.json',
        'freeze-runtime034-ordinary-native-invalid-001-command.log', 'freeze-runtime034-ordinary-native-invalid-001-time.log',
        'freeze-runtime034-ordinary-native-invalid-002-command.log', 'freeze-runtime034-ordinary-native-invalid-002-time.log',
        'runtime034-ordinary-native-invalid-002-controller-001.log', 'runtime034-ordinary-native-invalid-002-time-001.log'):
    retain(ROOT / '.runs' / name, Path('controllers-reviews') / name)
retain(Path(__file__), Path('controllers-reviews') / Path(__file__).name)
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material))
record = dict(schema=1, kind='runtime034-ordinary-actual-native-critical-invalid-controls-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=True, project_complete=False,
    accepted=False, production_admitted=False, actual_GUI=False, human_review=False,
    source_head=HEAD, runtime_manifest_sha256=MANIFEST, protocol_sha256=p.sha(base / 'protocol.json'),
    result_sha256=p.sha(out / 'result.json'), complete_cost=cost(ROOT / '.runs/runtime034-ordinary-native-invalid-002-time-001.log'),
    preparation_costs=dict(failed_freezer001=cost(ROOT / '.runs/freeze-runtime034-ordinary-native-invalid-001-time.log'),
        corrected_freezer002=cost(ROOT / '.runs/freeze-runtime034-ordinary-native-invalid-002-time.log'),
        failed_query_status=failed['status'], failed_query_exit_code=failed['exit_code'],
        corrected_query_status=query_process['status'], corrected_query_exit_code=query_process['exit_code']),
    cases=[dict(label=row['label'], control_observed=row['control_observed'],
        Native_counts=[row['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')],
        rejection=row['rejection'], protected_routes=row['protected_routes'],
        Native_diagnostic_routing_accepted=row.get('Native_diagnostic_routing_accepted')) for row in result['cases']],
    prerequisites={label:plan[label + '_positive'] for label in ('whole4Cu', 'partial2Cu')},
    implementation='Unchanged033 controller algorithm with034 names/source/manifest only. Fresh owned copy of034 partial standard90/both positive preserves all4 original routes. Actual full-schematic original-rule Native rejects added short. Locked-width+1nm stays Native-clean but exact protected invariant refuses before more normalization. Both own ordinary positives retain current central Route/export and final shared group metadata checks.',
    historical_kind_labels='Positive protocol kind frozen-runtime033-ordinary-workflow and shared helper030/004 names are unchanged schema/history labels. Actual source/runtime/tools/manifest034 are separately mandatory; no033 qualification promoted.',
    preparation_failure='Freezer001 metadata child lacked runtime sys.path and failed ModuleNotFoundError before controller copy, protocol or Native.001 raw logs/process remain unchanged. New002 adds only explicit runtime import path and fresh preparation namespace; controller/output001 and caps unchanged.',
    accounting='External complete Native-control exit17.95wall/13.90CPU is separate from freezer0010.41wall/0.18CPU and freezer0020.58wall/0.49CPU. Nested stored/query process costs are not added again. Full177/install007/ordinary positives are separately retained prerequisites. Authoring/AI review/curation and unknown interactive costs are additional, notzero.',
    source_rights='Project-owned generated geometry/schematic GPL; original demo project/settings preserve separate CC-BY-SA-4.0 notices in linked ordinary milestone. No private inputs, downloaded tools/apps/engines or binary payload newly exposed.',
    limits='Two correctness controls only. No engine rerun, new routing quality, actual graphical thermal workflow, Windows, human/physical, restoration or release qualification. AI readback is not human PCB review.',
    backup_scope='Essential sanitized proof only; full raw remains Mac-local and no new full backup/restoration is claimed.',
    references=reference_records, retention_helper_sha256=retention_pin,
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
assert p.sha(helper) == retention_pin and p.tool_manifest() == tools
for path, pin in pins: assert p.sha(path) == pin
for folder, hashes in originals: assert p.tree_hash(folder) == hashes
for folder, hashes in positive_material:
    assert io.inventory(folder, max_bytes=256*1024**2, max_files=8000, max_entries=16000) == hashes
assert f.evidence_inventory(out) == result['evidence_sha256'] == outer['completed_evidence']
for row in material: assert p.sha(ROOT / row['original']) == row['sha256']
# Last shared evidence callback: all fields/process reads precede all PRL events.
local.check_final_events(packets, p.c.CLI, pairs=pairs)
p.save_json(packet, record)
print(json.dumps(dict(files=len(files), bytes=total, material=len(material), passed=True, routing_gain=False)))
