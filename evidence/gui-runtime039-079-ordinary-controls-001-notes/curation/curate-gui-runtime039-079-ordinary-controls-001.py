"""Retain completed GUI079 controls; no validator or Native execution."""
from pathlib import Path
import ast, datetime, hashlib, json, resource, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

START = time.monotonic()
CPU0 = resource.getrusage(resource.RUSAGE_SELF)
notes = ROOT / 'evidence/gui-runtime039-079-ordinary-controls-001-notes'
output = ROOT / 'evidence/gui-runtime039-079-ordinary-controls-001.json'
assert notes.is_dir() and not output.exists()
base = ROOT / '.runs/runtime-directory-039/runtime/.runs/gui-session079'
runtime = base.parents[1]
cutoff = notes / 'cutoff/observations-001.json'
assert p.sha(cutoff) == '66e0431c2a09851be1664dfa5d6465cf83222203544a8e0b5bbd18016b7a0dd8'
observed = json.loads(cutoff.read_bytes())
assert observed['source_head'] == '57542e996f2b6e7704acd408ac99f6c72e70adc5'
assert observed['runtime_manifest_sha256'] == 'ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
assert observed['GUI_qualified'] is False

refs = {}; files = []; material = []; total = 0; dependencies = []
for name in [
    'gui-runtime039-079-positive-reject-001',
    'runtime039-native-floor-schema-milestone-001',
    'runtime039-mixer-default-failure-001',
    'runtime033-current-interf-Cdefault-001',
    'gui-runtime037-077-positive-001',
]:
    path = ROOT / 'evidence' / (name + '.json')
    record = json.loads(path.read_bytes())
    index = record['files_index']; ipath = ROOT / index['path']
    assert p.sha(ipath) == index['sha256']
    data = json.loads(ipath.read_bytes())
    for row in data.get('files', []): refs.setdefault(row['sha256'], row['path'])
    for row in data.get('material', []): refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), files_index=index))

helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
parsed = ast.parse(helper.read_bytes())
functions = [n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name in ('retain', 'tree', 'cost')]
assert [n.name for n in functions] == ['retain', 'tree', 'cost']
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'), globals())

raw = cutoff.read_bytes(); csha = hashlib.sha256(raw).hexdigest()
files.append(dict(path=str(cutoff.relative_to(ROOT)), bytes=len(raw), sha256=csha))
material.append(dict(original=str((base/'observations-001.json').relative_to(ROOT)),
    retained=str(cutoff.relative_to(ROOT)), bytes=len(raw), sha256=csha,
    scope='Frozen curation-start bytes; later live observations excluded.'))
refs[csha] = str(cutoff.relative_to(ROOT)); total = len(raw)
queue = []
def add(path, destination):
    path = Path(path); assert path.is_file() and ROOT in path.parents
    queue.append((path, Path(destination)))
def add_tree(path, destination, *, full=False):
    for rel in io.inventory(path, max_bytes=64*1024**2):
        if not full and set(Path(rel).parts) & {'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:
            continue
        add(path/rel, Path(destination)/rel)

prepared = json.loads((base/'prepared-state.json').read_bytes())
assert p.sha(base/'prepared-state.json') == observed['prepared_state_sha256']
assert p.sha(runtime/'runtime-distribution.json') == observed['runtime_manifest_sha256']
source_hashes = observed['source_hashes']
assert all(p.sha(base/'project'/name) == sha for name, sha in source_hashes.items())
for name in ['prepared-state.json', 'route-settings.json']:
    add(base/name, Path('preparation')/name)
add(runtime/'runtime-distribution.json', 'runtime/runtime-distribution.json')
add(base/'freshness-controls-001/protocol-frozen-001.json', 'controls/protocol-frozen-001.json')
add(base/'recovery-controls-001/protocol-required-001.json', 'refusals/preparation-protocol-required-001.json')
add_tree(base/'recovery-controls-001/floor4Cu-layer-refusal-002', Path('refusals/floor4Cu-layer-refusal-002'))
add(base/'ordinary-cancel-engine-observed-001.json', 'cancel/ordinary-cancel-engine-observed-001.json')

ids = dict(source='9aada5357ec4450ebd2cf4e58ac494fc',
    settings='3ec45846ea384396b078586b113d26c6', export='f73a05fb499949cda0e013eb45ad526e')
roles = []
refusal_text = dict(source='Saved source project changed', settings='Captured settings changed',
    export='Checked export refused: current bounded fresh export proof required')
for role, identity in ids.items():
    workspace = base/'jobs'/('autorouter-gui-'+identity)
    control = base/'freshness-controls-001'/role
    before = control/'preopen-export'
    route = json.loads((workspace/'route/result.json').read_bytes())
    export = json.loads((before/'export.json').read_bytes())
    pre = json.loads((control/'preopen-001.json').read_bytes())
    mutation = json.loads((control/'mutation-001.json').read_bytes())
    choice = json.loads((workspace/'choice/choice.json').read_bytes())
    assert pre['workspace'] == mutation['workspace'] == str(workspace)
    assert pre['source_unchanged'] is True and pre['route']['current'] is True and pre['export']['current'] is True
    assert len(pre['snapshot_hashes']) == 89
    assert all(p.sha(before/name) == sha for name, sha in pre['snapshot_hashes'].items())
    assert p.sha(before/'export.json') == pre['export_receipt_sha256']
    if role == 'export':
        assert pre['export_receipt_sha256'] == mutation['before_sha256']
    assert p.sha(control/'preopen-001.json') == mutation['preopen_sha256']
    assert p.sha(Path(mutation['path'])) == mutation['after_sha256']
    assert mutation['original_source_untouched'] is True
    assert route['accepted'] is True and route['status'] == 'routing_accepted' and route['invariants_unchanged'] is True
    assert route['source_hashes'] == source_hashes and route['schematic_parity'] == 'checked by final native DRC'
    assert route['metrics']['version'] == '10.0.7' and len(route['protected_route_import']['matches']) == 4
    assert choice['choice'] == 'accept' and choice['applied'] is False
    assert export['export_accepted'] is True and export['applied'] is False and export['original_geometry_and_routing_unchanged'] is True
    assert export['inputs']['receipt_sha256'] == p.sha(workspace/'route/result.json')
    assert export['source_hashes'] == source_hashes and export['schematic_parity'] == 'checked by final native DRC'
    assert p.sha(Path(route['candidate'])) == route['candidate_sha256'] == export['candidate_sha256']
    assert p.sha(before/'validation/candidate/owned1007-transport.kicad_pcb') == export['candidate_sha256']
    assert all(route['native'][key] == export['native'][key] == 0 for key in ['opens','blocking','warnings','exclusions'])
    assert p.sha(workspace/'route/final-drc.json') == route['native_report_sha256']
    assert p.sha(before/'validation/final-drc.json') == export['native_report_sha256']
    for record in (route, export):
        final = next(s for s in record['steps'] if s['name'] == 'final-drc')
        assert '--schematic-parity' in final['argv'] and final['exit_code'] == 0
        assert all(s['cleanup_complete'] is True and s['log_truncated'] is False for s in record['steps'])
    if role == 'source':
        assert Path(mutation['path']).read_bytes() == (before/'validation/candidate/owned1007-transport.kicad_pro').read_bytes()+b'\n'
    elif role == 'settings':
        original_settings = base/'jobs'/('autorouter-gui-'+ids['source'])/'settings.json'
        assert p.sha(original_settings) == mutation['before_sha256']
        assert Path(mutation['path']).read_bytes() == original_settings.read_bytes()+b'\n'
    else:
        current_export = json.loads((workspace/'export/export.json').read_bytes())
        assert type(current_export['export_accepted']) is int and current_export['export_accepted'] == 1
        current_export['export_accepted'] = True
        assert current_export == export
    add_tree(workspace, Path('jobs')/role)
    add_tree(control/'project', Path('controls')/role/'project')
    for name in ['preopen-001.json','mutation-001.json']:
        add(control/name, Path('controls')/role/name)
    # Full preopen text census includes isolated Native preferences, as in the retained positive packet.
    add_tree(before, Path('controls')/role/'preopen-export', full=True)
    samples = []
    for process_path in sorted(workspace.glob('*.command.process.json')):
        log = process_path.with_name(process_path.name.replace('.process.json','.log'))
        process = json.loads(process_path.read_bytes())
        assert p.sha(log) and log.stat().st_size == process['log_bytes']
        samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'),
            receipt_sha256=p.sha(process_path), log_sha256=p.sha(log), sample=process))
    roles.append(dict(role=role, workspace=str(workspace), candidate_sha256=route['candidate_sha256'],
        route_receipt_sha256=p.sha(workspace/'route/result.json'), preopen_receipt_sha256=p.sha(control/'preopen-001.json'),
        export_receipt_before_mutation_sha256=p.sha(before/'export.json'), Native_before_mutation=route['native'],
        protected_original_items=4, full_schematic_parity='checked by own final native DRC for Route and fresh export',
        original_invariants_recorded=True, snapshot_files=89, current_at_preopen=True,
        mutation=mutation, actual_GUI_refusal=refusal_text[role], forced_queued_race_observed=False,
        route_nested_cost=dict(wall_seconds=route['wall_seconds'], CPU_seconds=route['total_cpu_seconds']),
        export_nested_cost=dict(wall_seconds=export['wall_seconds'], CPU_seconds=export['total_cpu_seconds']), CLI_samples=samples))

ec = base/'freshness-controls-001/export'
missed = json.loads((ec/'open-boundary-001.json').read_bytes())
assert missed['child_before'] == [] and all(missed[x] is False for x in ['paused','resumed','mutated','Native_executed_by_controller'])
manager = json.loads((ec/'manager-only-postopen-001.json').read_bytes())
assert manager['export_exactly_matches_fresh_preopen'] is True and manager['files'] == 89
for name in ['open-boundary-001.json','manager-only-postopen-001.json']:
    add(ec/name, Path('controls/export')/name)

workspace = base/'jobs/autorouter-gui-97c8800978724e978878308878bd5f4b'
cancel = json.loads((workspace/'route/result.json').read_bytes())
cli = json.loads((workspace/'route.command.process.json').read_bytes())
engine = next(s for s in cancel['steps'] if s['name'] == 'engine')
assert cancel['accepted'] is False and cancel['status'] == 'cancelled' and 'candidate' not in cancel
assert not (workspace/'export').exists()
assert cli['cancel_requested'] is True and cli['exit_code'] == 2 and cli['log_truncated'] is False
assert engine['status'] == 'cancelled' and engine['exit_code'] == -9 and engine['cleanup_complete'] is True
assert all(p.sha(Path(cancel['source']).parent/name) == sha for name,sha in cancel['source_hashes'].items())
add_tree(workspace, Path('jobs/cancel'))
cancel_summary = dict(workspace=str(workspace), accepted=False, status=cancel['status'],
    source_hashes_unchanged_now=True, route_receipt_sha256=p.sha(workspace/'route/result.json'),
    CLI=cli, route_nested_wall_seconds=cancel['wall_seconds'], route_nested_CPU_seconds=cancel['total_cpu_seconds'],
    engine=engine, source_findings=cancel['source_drc'], export_exists=False,
    scope='Actual owned engine phase and GUI Cancel. CLI exit2; engine exit-9 with recorded cleanup. Exact job workers absent afterward per lead observation; no SIGINT-only, all-phase or permanent-descendant claim.')

names = ['gui079-preopen-001.py','gui079-mutate-control-001.py','gui079-export-open-boundary-001.py',
    'gui079-export-open-boundary-plan-001.json','gui079-export-open-boundary-001.log','gui079-export-open-boundary-001-time.log',
    'prepare-gui079-controls-001.py','prepare-gui079-controls-001.log','prepare-gui079-controls-001-time.log',
    'prepare-runtime039-gui079.py','runtime039-gui079-preparation-001.log','runtime039-gui079-preparation-001-time.log']
for role in ids:
    names.extend(['gui079-'+role+'-preopen-001.log','gui079-'+role+'-preopen-001-time.log'])
for name in names: add(ROOT/'.runs'/name, Path('helpers-logs')/name)
add(helper, 'curation/retention-helper030.py')
add(Path(__file__), 'curation/curate-gui-runtime039-079-ordinary-controls-001.py')
add(ROOT/'LICENSE', 'rights/LICENSE')

# Exact prospective size check prevents partial cap overruns; shared retain remains authoritative.
known = set(refs); planned_bytes = total; planned_files = len(files); omissions = []
filtered = []
for path, dest in queue:
    raw = io.read_bytes(path,4*1024**2); sha = hashlib.sha256(raw).hexdigest()
    if sha not in known:
        try:
            assert b'\0' not in raw; raw.decode('utf-8')
        except (AssertionError,UnicodeDecodeError):
            omissions.append(dict(original=str(path.relative_to(ROOT)), bytes=len(raw), sha256=sha,
                reason='No new binary payload; retain locally. No screenshots or unrelated browser content published.'))
            continue
        planned_bytes += len(raw); planned_files += 1; known.add(sha)
    filtered.append((path,dest))
assert planned_bytes < 16*1024**2 and planned_files < 2000, (planned_bytes,planned_files)
for path,dest in filtered: retain(path,dest)

scope = '''This packet freezes completed runtime039 GUI079 ordinary source/settings/typed-export refusals and engine cancellation, plus two observed recovery-input refusals. It does not qualify the running recovery job, hierarchy GUI, high-budget GUI or the full GUI candidate. The prior positive/reject packet remains immutable.

Each of the three independent freshness jobs retains its own Route, rendered Native SVG/HTML review, accept intent, fresh Native export/full-schematic/original/protected-four proof and all 89 byte-exact preopen files as text or existing exact references. Later source-PRO/settings-newline and typed export_accepted true-to-integer1 changes are declared and retained. Refusals were pre-open. The one 15-second planned reader-pause controller MISSED its reader interval, sent no STOP/CONT, made no mutation and exited2; its intended-scope text is not an actual queued-race result. The intermediate manager-only open/close left all89 export bytes exact. Full184 queued-callback software regressions are separate from actual GUI timing.

Cancellation used an owned copy of the licensed exposed Interf source. Source DRC's two repairable thermal findings are retained. Cancel occurred during the actual owned Java engine: GUI CLI exit2/cancel-requested, parent cancelled/no accepted candidate/no export, engine exit-9 and cleanup recorded. This is not SIGINT-only, all-phase or perpetual descendant absence. There is no final candidate/DRC from this cancelled route to promote.

The 89-second recovery input was refused before a workspace. The original prepared four-copper fixture refused at schematic-class qualification first, so it does not prove the layer guard. A separately frozen original owned floor-four-copper fixture refused explicitly at the two-copper recovery guard. Recovery job8258a46a7da54e2aa3fdff49ac24f183 is mentioned only as pending in the frozen observations: NO job files/results are inspected or retained here.

GUI/Edge/KiCad observations are the lead's actual CUA transcript observations, not human PCB review. Native SVG/HTML is retained. No screenshots, unrelated browser content or new binary payloads are published. New project-owned code/generated fixtures use repository LICENSE; exposed Interf source is CC-BY-SA-4.0 with retained original notices and Larry Ewing/The GIMP Tux attribution through exact prior evidence references. No private boards or downloaded engines/apps/venvs are included. Generated caches/preferences are excluded except the complete isolated preopen snapshots required for before-mutation proof.

No Native commands, engines, tests or production acceptance readers were rerun by curation. All original raw jobs remain on this Mac outside older raw backups. Interactive wall/CPU and unmetered authoring costs are unknown, not zero. Nested samples are not an end-to-end total. No new routing-quality/completion/speed/electrical/Windows/cleanOS/relocation/release claim is made.
'''
scope_path = notes/'SCOPE.md'; scope_path.open('x').write(scope)
raw=scope_path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha)); total+=len(raw)
material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index = notes/'files.json'
p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions))
u = resource.getrusage(resource.RUSAGE_SELF)
summary = dict(schema=1,kind='actual-runtime039-GUI079-completed-ordinary-controls-partial-cutoff',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,
    actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
    source_head=observed['source_head'],runtime_manifest_sha256=observed['runtime_manifest_sha256'],native_version='10.0.7',
    cutoff=dict(path=str(cutoff.relative_to(ROOT)),sha256=csha,recorded_utc=observed['recorded_utc'],
        scope='Immutable curation-start observations. Later recovery results excluded.'),
    prepared_state_sha256=p.sha(base/'prepared-state.json'), pristine_base_source_hashes=source_hashes,
    pristine_base_source_unchanged_now=True,roles=roles,ordinary_cancellation=cancel_summary,
    missed_open_boundary_control=dict(observed=False,child_before=[],paused=False,resumed=False,mutated=False,
        complete_external_cost=cost(ROOT/'.runs/gui079-export-open-boundary-001-time.log'),
        manager_only_open_left_89_export_files_exact=True,
        scope='Missed reader interval, exit2; no actual pause/queued-race claim. Subsequent typed mutation was a separate pre-open refusal.'),
    recovery_input_refusals=dict(budget89_before_workspace=True,
        original_prepared4Cu='Schematic-class qualification refusal, not a layer-guard test.',
        separate_original_owned_floor4Cu='Actual two-copper recovery guard refusal before a new workspace.',
        actual_recovery_job_files_or_results_included=False),
    actual_UI_scope=dict(browser='Microsoft Edge at owner request',Native_SVG_HTML_retained=True,
        screenshots='CUA transcript only; no local pixels or unrelated browser AX retained.',
        source_and_settings_refusals=True,typed_export_refusal=True,forced_queued_race_observed=False),
    accounting=dict(preopen_verifications_additional={role:cost(ROOT/'.runs'/('gui079-'+role+'-preopen-001-time.log')) for role in ids},
        preparation_additional_already_reported_in_prior_positive_packet=cost(ROOT/'.runs/runtime039-gui079-preparation-001-time.log'),
        shared_controls_preparation_already_reported_in_prior_positive_packet=cost(ROOT/'.runs/prepare-gui079-controls-001-time.log'),
        interactive_whole_wall_CPU='Unknown, not zero. CLI samples and nested Native costs are retained separately; do not sum as whole interactive cost.',
        research_authoring_review_CPU='Unmetered/unknown, not zero; not included in runtime samples.'),
    pending=['Actual recovery repair/no-repair and post-incumbent cancellation','Hierarchy actual GUI role','Other final079 roles/qualification and clean-environment/breadth/external gates'],
    rights='Project-owned GPL code/generated fixtures and exact licensed Interf CC-BY-SA-4.0 source/notices; no private CAD, unrelated browser content or new binaries.',
    limits='Partial GUI controls only. No forced queued race, SIGINT-only/all-phase/permanent-descendant, human/physical/electrical, broad routing-quality/superiority, Windows, cleanOS, relocation or formal-release qualification.',
    dependencies=dependencies,retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=p.sha(helper),
        functions=['retain','tree','cost'],max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
        new_payload_files=len(files),new_payload_bytes=total,material_rows=len(material),omitted_binary_payloads=len(omissions),
        counts_exclude_index_summary=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
# Replay retained byte/hash mappings only, never any validation/Native API.
for row in files:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),
    new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binaries=len(omissions),actual_GUI_fully_qualified=False)))
