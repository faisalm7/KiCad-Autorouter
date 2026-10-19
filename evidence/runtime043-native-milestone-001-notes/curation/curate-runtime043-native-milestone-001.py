"""DRAFT: facts-only eight-case043 curation; never execute Native or proof readers.

Run only after the lead confirms all eight terminal deliveries. Missing/failed
cases refuse before any evidence output. CAD, DSN, SES, plots and raw findings
stay local; this packet is not a full raw backup or fresh validation replay.
"""
from pathlib import Path
from collections import Counter
import ast, datetime, hashlib, json, math, os, re, sys

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-043/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

HEAD = '6ec7ad2344ed060d5e0971965ef05bd9de68925d'
MANIFEST = '6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3'
FROZEN = 'a9ecd3aac2deeb58ab591ae53d59abe988e98cf8282a6dd2e770dfa3d072c8af'
SOURCE_PLAN = '45c843540431444397d7034b315fd07f4459498a8582d7b2eb41f6cc4869ba69'
ALIAS003 = '39cb57a54fbafeb80e8497a385e402358ace9c5701681d21a160375e4cb7bcff'
DRIVER = '0b1a3bc61e576d6475a4c922a7727b7831ccf28f3e0a9d2d80b557e3c1964034'
ENCLOSURE = '69d87dee41f94fe9e479e505093914325ed653cbb0cd58c9545272afefc1d59c'
base = ROOT / '.runs/runtime043-native-qualification-001'
notes = ROOT / 'evidence/runtime043-native-milestone-001-notes'
output = ROOT / 'evidence/runtime043-native-milestone-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
keys = ('opens', 'blocking', 'warnings', 'exclusions')
refs = {}; files = []; material = []; total = 0
helpers = [
    ('.runs/curate-runtime030-native-workflow-qualification-001.py', 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1', ['retain', 'cost']),
    ('.runs/curate-runtime042-current-comparison-001.py', 'd6d99941d9afe8d6a81e862d406d66b72f39fdf1c5241dc6cb7403154a61d974', ['complete_cost', 'counts', 'delivered_proof']),
    ('.runs/curate-gui-runtime042-081-recovery-deliveries-001.py', '340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9', ['read', 'own_final']),
]
for name, pin, names in helpers:
    source = ROOT / name; assert p.sha(source) == pin
    selected = [n for n in ast.parse(source.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert [n.name for n in selected] == names
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), globals())

dependencies = []
for name in ('runtime042-native-milestone-001', 'runtime043-general-corrections-native-001'):
    path = ROOT / 'evidence' / (name + '.json'); data = f.read_json(path)
    rows = data.get('files', [])
    if data.get('files_index'):
        index = data['files_index']; assert p.sha(ROOT / index['path']) == index['sha256']
        index_data = f.read_json(ROOT / index['path']); rows = index_data['files'] + index_data.get('material', [])
    for row in rows:
        refs.setdefault(row['sha256'], row.get('retained', row.get('path')))
    dependencies.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), scope='Prior public proof/rights; no historical outcome transferred.'))

selected_metadata = []; pins = {}
def metadata(path, target=None):
    path = Path(path)
    if target is None: target = Path(*path.relative_to(ROOT).parts[1:])
    selected_metadata.append((path, Path(target)))
def pin(path, expected=None):
    path = Path(path); value = p.sha(path)
    assert expected is None or value == expected
    assert path not in pins or pins[path] == value
    pins[path] = value
    return value
def successful(process):
    assert process['status'] == 'success' and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False

pin(runtime / 'runtime-distribution.json', MANIFEST)
manifest = f.read_json(runtime / 'runtime-distribution.json')
assert manifest['root'] == str(runtime) and manifest['native_version'] == '10.0.7'
assert manifest['build_source']['git_head'] == HEAD and len(manifest['immutable_files_sha256']) == 53
assert p.c.ROOT == runtime and p.c.NATIVE_VERSION == '10.0.7'
for name, digest in manifest['immutable_files_sha256'].items(): pin(runtime / name, digest)
metadata(runtime / 'runtime-distribution.json', 'runtime/runtime-distribution.json')
metadata(runtime / 'LICENSE', 'rights/LICENSE.GPL-3.0-or-later')
pin(base / 'frozen.json', FROZEN); frozen = f.read_json(base / 'frozen.json')
pin(ROOT / '.runs/runtime043-native-regression-source-plan-001.json', SOURCE_PLAN)
assert frozen['source_head'] == HEAD and frozen['runtime_manifest_sha256'] == MANIFEST
assert frozen['source_plan_sha256'] == SOURCE_PLAN
cases = ('alias2Cu', 'whole4Cu', 'partial2Cu', 'hierarchy-whole2Cu', 'floor-2Cu', 'floor-4Cu', 'sonde-whole', 'fractional-owned')
assert tuple(row['case'] for row in frozen['protocols']) == cases
tools = f.read_json(base / 'tools-defaults.json')['tools']
assert tools['kicad'] == '10.0.7' and tools['git_head'] == HEAD
assert tools['source_provenance']['manifest_sha256'] == MANIFEST
core = {name: digest for name, digest in manifest['immutable_files_sha256'].items() if name.startswith('autorouter/') and name.endswith('.py')}
assert len(core) == 48 and tools['implementation_sha256'] == core
for label in ('doctor', 'tools-defaults'):
    process = f.read_json(base / (label + '-process.json')); successful(process)
    assert process['cwd'] == str(runtime)
    for suffix in ('.json', '-process.json'): metadata(base / (label + suffix))
assert f.read_json(base / 'doctor.json')['ready'] is True
metadata(base / 'frozen.json')

fullbase = ROOT / '.runs/full-integration-190'; full = f.read_json(fullbase / 'execution.json')
successful(full['process']); assert full['passed'] is True and full['sources_unchanged'] is True
pin(fullbase / 'command.log', full['log_sha256'])
pin(ROOT / '.runs/run-full-integration-190.py', full['controller_sha256'])
assert full['controller_sha256'] == 'a22979903ed7fc35587946df6b690fb799b0c6c4a98fdf6dc2ff414df1e6cac5'
full_log = io.read_bytes(fullbase / 'command.log', 4 * 1024**2).decode('utf8')
assert 'Ran 2353 tests' in full_log and 'OK (skipped=1)' in full_log
assert f.read_json(fullbase / 'protocol.json')['tools']['git_head'] == HEAD
for name in ('protocol.json', 'execution.json', 'command.log'): metadata(fullbase / name)
preparation = f.read_json(runtime.parent / 'preparation.json')
assert preparation['prepared'] is True and preparation['qualified'] is False
assert preparation['source_head'] == HEAD and preparation['runtime'] == str(runtime)
assert preparation['manifest_sha256'] == MANIFEST and preparation['full190_execution_sha256'] == pin(fullbase / 'execution.json')
venv = f.read_json(runtime.parent / 'venv-process.json'); successful(venv)
assert pin(runtime.parent / 'venv-process.json') == preparation['venv_process_sha256']
for name in ('preparation.json', 'venv-process.json', 'venv.log'): metadata(runtime.parent / name, Path('preparation') / name)

rows = []; originals = []; failures = []
for item in frozen['protocols']:
    case = item['case']; original_folder = base / case
    assert Path(item['protocol']) == original_folder / 'protocol.json'
    pin(Path(item['protocol']), item['protocol_sha256'])
    original_plan = f.read_json(Path(item['protocol']))
    folder = base / ('alias2Cu-retry003' if case == 'alias2Cu' else case)
    plan = f.read_json(folder / 'protocol.json'); plan_pin = pin(folder / 'protocol.json', ALIAS003 if case == 'alias2Cu' else item['protocol_sha256'])
    for key in ('case', 'source', 'source_hashes', 'settings', 'expected_counts', 'expected_protected_count', 'budgets', 'runtime', 'runtime_manifest_sha256', 'source_head', 'tools', 'driver_sha256', 'enclosure_sha256'):
        assert plan[key] == original_plan[key]
    assert plan['case'] == case and plan['kind'] == 'runtime043-six-stage-ordinary-CLI'
    assert plan['runtime'] == str(runtime) and plan['source_head'] == HEAD and plan['runtime_manifest_sha256'] == MANIFEST
    assert plan['driver_sha256'] == DRIVER and plan['enclosure_sha256'] == ENCLOSURE and plan['tools'] == tools
    source = Path(plan['source']); hashes = plan['source_hashes']
    assert io.inventory(source.parent) == hashes
    originals.append((source.parent, hashes))
    assert pin(folder / 'settings.json') == plan['settings_sha256']
    assert f.read_json(folder / 'settings.json') == plan['settings']
    out = runtime / '.runs' / ('ordinary-alias2Cu-003' if case == 'alias2Cu' else 'ordinary-' + case + '-001')
    assert plan['output'] == str(out)
    outer = f.read_json(folder / 'execution.json'); successful(outer['process'])
    assert outer['controls_passed'] is True and outer['workflow_delivered'] is True and outer['error'] is None
    assert outer['protocol_sha256'] == plan_pin and outer['child_receipt'] == str(out / 'result.json')
    pin(out / 'result.json', outer['child_sha256']); child = f.read_json(out / 'result.json')
    assert child['status'] == 'completed' and child['workflow_delivered'] is True
    assert child['source'] == str(source) and child['source_hashes'] == hashes and child['tools'] == tools
    assert child['settings'] == plan['settings'] and child['settings_sha256'] == plan['settings_sha256']
    assert child['settings_path'] == str(folder / 'settings.json') and child['driver_sha256'] == DRIVER
    assert child['route_readback']['current'] is True and child['export_readback']['current'] is True
    assert [row['stage'] for row in child['processes']] == ['preview', 'route', 'review', 'choice', 'export', 'verify_export']
    for stage in child['processes']:
        assert stage['process']['exit_code'] == 0 and stage['process']['log_truncated'] is False
        pin(out / (stage['stage'] + '.log'), stage['log_sha256'])
    work = Path(child['workspace']); assert work.parent == out and work.name.startswith('autorouter-gui-')
    proofs = {}; records = {}
    for label, exporting in (('route', False), ('export', True)):
        receipt = work / label / ('export.json' if exporting else 'result.json')
        proof = delivered_proof(receipt, export=exporting, source_hashes=hashes, allowed=[out])
        record = f.read_json(receipt); records[label] = record
        assert record['tools'] == tools and record['budget_seconds'] == plan['budgets'][label]
        directory = receipt.parent / 'validation' if exporting else receipt.parent
        proof['own_final'] = own_final(record, directory, directory, hashes, record['candidate'])
        proof['finding_types'] = dict(Counter(str(v['severity']) + ':' + str(v['type']) for v in record['native']['findings']))
        for path, digest in ((receipt, proof['receipt_sha256']), (Path(record['candidate']), proof['candidate_sha256']), (directory / 'final-drc.json', proof['native_report_sha256']), (directory / 'final-drc-process.json', proof['own_final']['process_sha256']), (directory / 'final-drc-binding.json', proof['own_final']['binding_sha256'])): pin(path, digest)
        proofs[label] = proof
    route = records['route']; exported = records['export']; native = proofs['route']['Native_counts']
    assert proofs['route']['receipt_sha256'] == child['route_receipt_sha256']
    assert proofs['route']['candidate_sha256'] == proofs['export']['candidate_sha256'] == child['candidate_sha256']
    assert native == proofs['export']['Native_counts'] == outer['Native_counts'] and native[:2] == [0, 0] and native[3] == 0
    if plan['expected_counts'] is not None: assert native == plan['expected_counts']
    else: assert plan['warning_policy'] == 'retain_all_native_findings' and native[3] == plan['expected_exclusions']
    assert proofs['route']['protected_count'] == outer['protected_count'] == plan['expected_protected_count']
    assert {q.name for q in (work / 'route/code').iterdir()} == {Path(name).name for name in core}
    for name, digest in core.items(): pin(work / 'route/code' / Path(name).name, digest)
    elapsed = complete_cost(folder / 'outer-time.log'); assert max(elapsed['wall_seconds'], elapsed['CPU_seconds']) <= 240
    edge = route.get('native_edge_correction', {}).get('inward_boundary')
    if case == 'fractional-owned': assert edge and edge['native_host_version'] == '10.0.7' and edge['output_within_original_boundary'] is True
    rows.append(dict(case=case,first_attempt=case != 'alias2Cu',protocol_sha256=plan_pin,execution_sha256=pin(folder / 'execution.json'),child_sha256=outer['child_sha256'],source_hashes=hashes,source_unchanged=True,captured_RuntimeCore_sha256=core,Native_counts=native,protected_count=outer['protected_count'],no_positive_protection_claim=outer['protected_count']==0,own_final=proofs,metrics=exported['metrics'],complete_cost=elapsed,workflow_stages=child['processes'],fractional_edge_proof=({k:edge[k] for k in ('policy','grid_um','observed_input_discrepancy_guard_um','native_host_version','input_boundary_ast_sha256','output_boundary_ast_sha256','output_within_original_boundary','native_design_modified')} if edge else None)))
    for name in ('protocol.json', 'settings.json', 'execution.json', 'outer.log', 'outer-time.log', 'enclosure/process.json', 'enclosure/command.log'): metadata(folder / name)

for label, expected in (('alias2Cu', 'e513985691fe5245946a875d5446efa2f93e94527a392eddcf0eb6147ee2d977'), ('alias2Cu-retry002', '19e70e0ba4c6f65fac62e502a62429def7bcffb4bcc02543f8c6a8b72001a16b')):
    folder = base / label; pin(folder / 'protocol.json', expected)
    plan = f.read_json(folder / 'protocol.json'); failed = f.read_json(folder / 'execution.json')
    assert failed['controls_passed'] is False and failed['workflow_delivered'] is False and failed['child_sha256'] is None
    assert failed['protocol_sha256'] == expected and failed['process']['cleanup_complete'] is True
    assert failed['process']['status'] == 'nonzero_exit' and failed['process']['log_truncated'] is False
    out = Path(plan['output']); assert not (out / 'result.json').exists()
    if out.exists(): assert not io.inventory(out, max_bytes=2*1024**2, max_files=64, max_entries=128)
    failures.append(dict(attempt=label,protocol_sha256=expected,execution_sha256=pin(folder/'execution.json'),complete_cost=complete_cost(folder/'outer-time.log'),error=failed['error'],child_receipt_absent=True,Native_invocations=0,scope='Preserved pre-Native setup/caller failure; not a rejected Native candidate or erased first attempt.'))
    for name in ('protocol.json', 'settings.json', 'execution.json', 'outer.log', 'outer-time.log', 'enclosure/process.json', 'enclosure/command.log'): metadata(folder / name)
assert len(rows) == 8

for name in ('run-full-integration-190.py','full-integration-190-controller.log','full-integration-190-time.log','prepare-runtime043-001.py','prepare-runtime043-001.log','prepare-runtime043-001-time.log','freeze-runtime043-native-001.py','freeze-runtime043-native-001.log','freeze-runtime043-native-001-time.log','runtime043-native-regression-source-plan-001.json'):
    metadata(ROOT / '.runs' / name)
metadata(ROOT / 'scripts/qualify_runtime_workflow.py', 'controllers/qualify_runtime_workflow.py')
metadata(ROOT / '.runs/enclose-runtime030-ordinary-workflow-002.py', 'controllers/enclose-runtime030-ordinary-workflow-002.py')
metadata(Path(__file__), 'curation/' + Path(__file__).name)
sonde = Path(next(row['source'] for row in f.read_json(ROOT / '.runs/runtime043-native-regression-source-plan-001.json')['cases'] if row['case'] == 'sonde-whole'))
for name in ('LICENSE.CC-BY-SA-4.0', 'LICENSE.README'): metadata(sonde.parent / '_licenses' / name, Path('rights/Sonde') / name)
assert len(selected_metadata) == len(set(path for path, _ in selected_metadata)) and len(selected_metadata) < 128
known = set(refs); required_bytes = required_files = 0
for path, target in selected_metadata:
    raw = io.read_bytes(path, 4*1024**2); raw.decode('utf8'); assert b'\0' not in raw
    digest = pin(path)
    if digest not in known: known.add(digest); required_bytes += len(raw); required_files += 1
assert required_bytes < 16*1024**2-8192 and required_files < 1999, (required_bytes, required_files)
for directory, hashes in originals: assert io.inventory(directory) == hashes
for path, digest in pins.items(): assert p.sha(path) == digest
for path, target in selected_metadata: retain(path, target)
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material))
for directory, hashes in originals: assert io.inventory(directory) == hashes
for path, digest in pins.items(): assert p.sha(path) == digest
record = dict(schema=1,kind='runtime043-eight-ordinary-Native-regressions-facts-only-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head=HEAD,runtime_manifest_sha256=MANIFEST,immutable_files_sha256=manifest['immutable_files_sha256'],RuntimeCore_sha256=core,full190=dict(passed=True,tests=2353,skips=1,complete_cost=complete_cost(ROOT/'.runs/full-integration-190-time.log')),preparation=dict(prepared=True,complete_cost=complete_cost(ROOT/'.runs/prepare-runtime043-001-time.log'),doctor_and_freeze_complete_cost=complete_cost(ROOT/'.runs/freeze-runtime043-native-001-time.log')),Native_deliveries=rows,pre_Native_failures=failures,negative_controls='Separate additive qualification pending; no new043 invalid-control result is assumed.',GUI='Pending; old042 GUI roles are not transferred.',rights='Owned diagnostic/source/code GPL-3.0-or-later. Sonde is CC-BY-SA4 with exact prior042 licensed source pins and retained original notices. This packet retains facts/control metadata and owned controllers only; no original/derived CAD, DSN, SES, rendered plots or raw DRC findings.',publication='All unique raw Native/source/workspace proof remains Mac-only/outside010. Hash references are not a remote raw backup or tested restoration. Free-form terminal logs still require staged public-content audit.',scope='Eight fresh ordinary standard/B1 six-stage deliveries, each with own final Native/fullSCH/source/original-rule/protected proof. Zero protected count has no positive protection claim. Reporting and edge corrections do not establish broad quality, comparative/independent-family gain, human/physical/GUI/Windows/cleanOS/standalone or release qualification.',accounting='Each complete external exit includes routing/refill/validation/readback/software-intent/delivery; nested samples are not added. Failed attempts, full190, runtime preparation and doctor/freeze costs are additional. Authoring/review/curation and incompletely metered administrative work are unknown, not zero.',reporting_helpers=[dict(path=name,sha256=digest,functions=names) for name,digest,names in helpers],dependencies=dependencies,files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
assert not os.path.lexists(output)
p.save_json(output, record)
print(json.dumps(dict(summary=str(output),summary_sha256=p.sha(output),cases=len(rows),new_files=len(files),retained_bytes=total,material=len(material))))
