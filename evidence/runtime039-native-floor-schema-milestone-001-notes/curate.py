"""Bounded essential039 evidence curation and pure readback; no workers run."""
from pathlib import Path
from decimal import Decimal
import ast, datetime, hashlib, json, os, re, sys

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'evidence/runtime039-native-floor-schema-milestone-001.json'
notes = output.with_name(output.stem + '-notes')
assert not os.path.lexists(output) and not os.path.lexists(notes)
runtime = ROOT / '.runs/runtime-directory-039/runtime'
sys.dont_write_bytecode = True
sys.path.insert(0, str(runtime))
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from autorouter import config as c, review_export as ex, sexpr as sx
assert c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
assert Path(sys.prefix).resolve() == runtime / '.venv'
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
definitions = [n for n in ast.parse(helper.read_bytes()).body if isinstance(n, ast.FunctionDef)
               and n.name in {'retain', 'tree', 'cost'}]
assert {n.name for n in definitions} == {'retain', 'tree', 'cost'}
refs = {}; files = []; material = []; total = 0
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper), 'exec'))
real_retain = retain; selected = []
def retain(q, name): selected.append((Path(q), Path(name)))

dependencies = []
for name, digest in [
    ('evidence/default-targets-native-observation-priority-004.json', '9897ae4a0d400240df92a49f0afb757866991ec8a55f77a23a8517d1bba88019'),
    ('evidence/runtime038-default-floor-native-and-hierarchy-regression-001.json', 'aad3d5e61160baf3a4374ab8ed134c03120062088c77565789965721c7e50bc1'),
    ('evidence/native-map-floor-schema-correction-001.json', '31748bda25be62ae337631b64132d1c349fb4594316d633c1235345b8b838b81'),
]:
    q = ROOT / name; assert p.sha(q) == digest
    j = f.read_json(q); index = ROOT / j['files_index']['path']
    assert p.sha(index) == j['files_index']['sha256']
    x = f.read_json(index)
    for row in x['files']: refs.setdefault(row['sha256'], row['path'])
    for row in x['material']: refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=digest, files_index=j['files_index']))

HEAD = '57542e996f2b6e7704acd408ac99f6c72e70adc5'
MANIFEST = 'ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728'
manifest = runtime / 'runtime-distribution.json'
assert p.sha(manifest) == MANIFEST
runtime_record = f.read_json(manifest)
assert runtime_record['build_source']['git_head'] == HEAD
immutable = runtime_record['immutable_files_sha256']
modules = [name for name in immutable if name.startswith('autorouter/') and name.endswith('.py')]
assert len(immutable) == 53 and len(modules) == 48
for name, digest in immutable.items():
    assert p.sha(runtime / name) == digest
    retain(runtime / name, Path('runtime039/immutable') / name)
retain(manifest, Path('runtime039/runtime-distribution.json'))

full_base = ROOT / '.runs/full-integration-184'
full = f.read_json(full_base / 'execution.json'); full_plan = f.read_json(full_base / 'protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status'] == 'success' and full['process']['exit_code'] == 0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
assert full_plan['tools']['git_head'] == HEAD and p.sha(full_base / 'command.log') == full['log_sha256']
assert p.sha(ROOT / '.runs/run-full-integration-184.py') == full['controller_sha256']
full_text = (full_base / 'command.log').read_text()
assert len(re.findall(r'^Ran 2298 tests in [\d.]+s$', full_text, re.M)) == 1
assert 'OK (skipped=1)' in full_text
for name, digest in runtime_record['build_source']['files_sha256'].items():
    if name in full_plan['source_sha256']: assert full_plan['source_sha256'][name] == digest
tree(full_base, Path('full184'))
discovery = ROOT / full_plan['discovery']; assert p.sha(discovery) == full_plan['discovery_sha256']
retain(discovery, Path('controllers-and-cost') / discovery.name)

install_base = ROOT / '.runs/install-distribution-native-012'
install = f.read_json(install_base / 'execution.json'); install_plan = f.read_json(install_base / 'protocol.json')
build_path = runtime.parent / 'result.json'; build = f.read_json(build_path)
assert install['passed'] is True and install['source_unchanged'] is True
assert install['protocol_sha256'] == p.sha(install_base / 'protocol.json')
assert install['child_receipt'] == str(build_path) and install['child_receipt_sha256'] == p.sha(build_path)
assert build['passed'] is True and build['git_head'] == HEAD and build['native_version'] == '10.0.7'
assert build['source_installation_mode'] == 'distribution'
assert build['selected_source_unchanged'] is True and build['installed_product_unchanged'] is True
assert install_plan['source_head'] == HEAD
assert p.sha(ROOT / '.runs/run-install-distribution-native-012.py') == install_plan['controller_sha256']
assert install_plan['full_integration184']['execution_sha256'] == p.sha(full_base / 'execution.json')
assert install_plan['full_integration184']['protocol_sha256'] == p.sha(full_base / 'protocol.json')
tree(install_base, Path('installation/enclosure'))
retain(build_path, Path('installation/result.json'))
retain(runtime.parent / 'source-tracked.json', Path('installation/source-tracked.json'))
for command in build['commands']:
    q = Path(command['log']); assert p.sha(q) == command['log_sha256']
    retain(q, Path('installation/command-logs') / q.name)
tree(runtime.parent / 'source-fixture', Path('installation/original-smoke'))
tree(runtime / '.runs/install-native-smoke', Path('installation/native-smoke'))
smoke_path = Path(build['native_receipt']['path']); assert p.sha(smoke_path) == build['native_receipt']['sha256']
readbacks = {}; deliveries = []
CASES = [('hierarchy-whole2Cu','002',[0,0,0,0],0,31.23,28.07),
    ('whole4Cu','001',[0,0,6,0],10,35.21,32.23),
    ('partial2Cu','001',[0,0,0,0],4,31.26,27.85),
    ('floor-2Cu','001',[0,0,6,0],1,28.22,25.20),
    ('floor-4Cu','001',[0,0,6,0],1,29.73,26.67)]
with p.validation_readback_session():
    readbacks['installation_smoke'] = p.check_result(smoke_path)
    assert readbacks['installation_smoke']['current'] is True
    for label, attempt, expected, protection, wall, cpu in CASES:
        prefix = 'runtime039-ordinary-' + label + '-' + attempt
        base = ROOT / '.runs' / prefix
        plan = f.read_json(base / 'protocol.json'); completed = f.read_json(base / 'execution.json')
        assert plan['source_head'] == HEAD and plan['runtime'] == str(runtime)
        assert plan['runtime_manifest_sha256'] == MANIFEST
        source = Path(plan['source']); assert io.inventory(source.parent) == plan['source_hashes']
        tree(base, Path('workflow-enclosures') / (label+'-'+attempt))
        for rel in plan['source_hashes']: retain(source.parent / rel, Path('original-inputs') / label / rel)
        child_dir = Path(plan['output']); child_path = child_dir / 'result.json'
        assert completed['protocol_sha256'] == p.sha(base / 'protocol.json')
        assert completed['child_receipt'] == str(child_path) and completed['child_sha256'] == p.sha(child_path)
        assert completed['controls_passed'] is True and completed['workflow_delivered'] is True
        assert completed['process']['status'] == 'success' and completed['process']['cleanup_complete'] is True
        assert completed['process']['log_truncated'] is False
        child = f.read_json(child_path); work = Path(child['workspace'])
        assert child['workflow_delivered'] is True and child['status'] == 'completed'
        assert child['actual_GUI'] is False and child['human_review'] is False
        assert [row['stage'] for row in child['processes']] == ['preview','route','review','choice','export','verify_export']
        assert all(row['process']['exit_code'] == 0 and row['process']['log_truncated'] is False for row in child['processes'])
        assert child['source_hashes'] == plan['source_hashes']
        tree(child_dir, Path('actual-workflows') / (label+'-'+attempt))
        route_path = work / 'route/result.json'; export_path = work / 'export/export.json'
        route = f.read_json(route_path); exported = f.read_json(export_path)
        rb = p.check_result(route_path); eb = ex.check_export(export_path)
        assert rb['current'] is True and eb['current'] is True and eb['applied'] is False
        assert route['accepted'] is True and exported['export_accepted'] is True
        assert route['candidate_sha256'] == exported['candidate_sha256'] == child['candidate_sha256']
        assert route['source_hashes'] == exported['source_hashes'] == plan['source_hashes']
        assert route['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
        counts = [route['native'][key] for key in ('opens','blocking','warnings','exclusions')]
        assert counts == [exported['native'][key] for key in ('opens','blocking','warnings','exclusions')] == expected
        assert completed['protected_count'] == plan['expected_protected_count'] == protection
        original = sx.read(source); board = sx.read(Path(exported['candidate']))
        protected = p.protected_for_record(route, original)
        assert len(protected) == protection and all(node in p.routes(board) for node in protected)
        assert p.immutable(board) == p.immutable(original)
        external = cost(ROOT / '.runs' / (prefix + '-time.log'))
        assert external == dict(wall_seconds=wall,CPU_seconds=cpu)
        assert wall < 240 and cpu < 240
        item = dict(case=label,attempt=attempt,workflow_delivered=True,current_readback=True,
            source_hashes=plan['source_hashes'],protocol_sha256=p.sha(base/'protocol.json'),
            child_receipt_sha256=p.sha(child_path),route_receipt_sha256=p.sha(route_path),
            export_receipt_sha256=p.sha(export_path),candidate_sha256=exported['candidate_sha256'],
            source_native=route['source_drc'],final_Native=route['native'],export_Native=exported['native'],
            Native_counts=counts,whole_project_DRC_clean=route['whole_project_drc_clean'],
            full_schematic_parity=route['schematic_parity'],protected_count=protection,
            no_protection_claim=protection==0,original_geometry_rules_and_protected_unchanged=True,
            metrics=route['metrics'],settings=plan['settings'],budgets=plan['budgets'],
            complete_external_cost=external,actual_GUI=False,human_review=False,
            nested_route_cost=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),
            nested_export_cost=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']))
        if label.startswith('floor-'):
            widths = sorted({str(Decimal(sx.one(node,'width')[1]).normalize()) for node in sx.children(board,'segment')})
            vias = sorted({(str(Decimal(sx.one(node,'size')[1]).normalize()),str(Decimal(sx.one(node,'drill')[1]).normalize()))
                           for node in sx.children(board,'via')})
            assert widths == ['0.3'] and vias == [('0.9','0.4')]
            raw_project = f.read_json(source.with_suffix('.kicad_pro')); final_project = f.read_json(Path(exported['project_file']))
            assert raw_project['net_settings']['classes'] == final_project['net_settings']['classes']
            raw_Default = raw_project['net_settings']['classes'][0]
            raw_values = {key:raw_Default[key] for key in ('track_width','clearance','via_diameter','via_drill')}
            assert raw_values == dict(track_width=.2,clearance=.1,via_diameter=.6,via_drill=.3)
            item.update(raw_Default_unchanged=True,raw_Default_mm=raw_values,
                final_segment_widths_mm=widths,final_via_diameter_drill_mm=vias,
                default_target_transport=route['default_target_transport'])
        deliveries.append(item); readbacks[label] = dict(Route=rb,export=eb)

failed_base = ROOT / '.runs/runtime039-ordinary-hierarchy-whole2Cu-001'
failed_plan = f.read_json(failed_base/'protocol.json'); failed = f.read_json(failed_base/'execution.json')
assert failed['controls_passed'] is False and failed['workflow_delivered'] is False
assert failed['process']['exit_code'] == 1 and failed['process']['cleanup_complete'] is True
assert failed['protocol_sha256'] == p.sha(failed_base/'protocol.json') and failed['child_sha256'] is None
assert failed_plan['source_head'] == HEAD and failed_plan['runtime_manifest_sha256'] == MANIFEST
empty_child = Path(failed_plan['output']); assert empty_child.is_dir() and not list(empty_child.iterdir())
failed_log = (failed_base/'enclosure/command.log').read_text()
assert 'FileNotFoundError' in failed_log and '.runs/runtime039-ordinary-hierarchy-whole2Cu-001/settings.json' in failed_log
assert failed['process']['argv'][-1] == '.runs/runtime039-ordinary-hierarchy-whole2Cu-001/settings.json'
retry_plan = f.read_json(ROOT/'.runs/runtime039-ordinary-hierarchy-whole2Cu-002/protocol.json')
for key in ('source','source_hashes','settings','settings_sha256','budgets','driver_sha256','enclosure_sha256'):
    assert failed_plan[key] == retry_plan[key]
assert Path(retry_plan['output']).name != empty_child.name
tree(failed_base,Path('pre-Native-invocation-failures/hierarchy001'))
failures = [dict(case='hierarchy001',controls_passed=False,Native_executed=False,preview_executed=False,
    original_execution_sha256=p.sha(failed_base/'execution.json'),
    error='Relative settings path resolved under enclosure cwd; FileNotFoundError before preview or Native.',
    empty_child_directory_preserved=True,child_receipt_absent=True,
    retry='hierarchy002 uses absolute settings/protocol and fresh output; same code, source, settings and budgets.',
    complete_external_cost=cost(ROOT/'.runs/runtime039-ordinary-hierarchy-whole2Cu-001-time.log'))]
assert failures[0]['complete_external_cost'] == dict(wall_seconds=.37,CPU_seconds=.32)

invalid_base = ROOT/'.runs/runtime039-ordinary-native-invalid-001'
invalid_plan = f.read_json(invalid_base/'protocol.json'); invalid_out = Path(invalid_plan['output'])
invalid = f.read_json(invalid_out/'result.json'); invalid_outer = f.read_json(invalid_base/'enclosure/result.json')
assert p.sha(invalid_base/'protocol.json') == '943f29bdf4a9f0cabd06e4f177a637dd225d551499a87b8fdbab3b44fc0aa917'
assert invalid_plan['source_head'] == HEAD and invalid_plan['runtime_manifest_sha256'] == MANIFEST
assert invalid['protocol_sha256'] == invalid_outer['protocol_sha256'] == p.sha(invalid_base/'protocol.json')
assert p.sha(invalid_out/'result.json') == invalid_outer['child_sha256'] == '04dcf508f7d6f7f39fe584916a0532399caa613a5b7d103eda33b376f8ce028c'
assert invalid['control_passed'] is True and invalid_outer['passed'] is True
assert invalid_outer['process']['status'] == 'success' and invalid_outer['process']['cleanup_complete'] is True
assert all(invalid[k] is False for k in ('accepted','routing_accepted','export_accepted','production_admitted','Native_product_admission','actual_GUI','human_review'))
assert len(invalid['cases']) == 2
short, width = invalid['cases']
assert short['label'] == 'partial-short' and [short['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,4,0,0]
assert any(row['type']=='shorting_items' for row in short['native']['findings'])
assert width['label'] == 'partial-protected-width' and [width['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,0,0,0]
assert width['mutation']['added_nanometres'] == 1 and width['rejection'] == 'protected route changed'
assert width['no_additional_native_after_invariant_refusal'] is True and width['Native_diagnostic_routing_accepted'] is True
assert all(row['control_observed'] is True and row['accepted'] is False for row in invalid['cases'])
for row in invalid['cases']:
    board = Path(row['candidate']); directory = board.parent.parent
    name = 'final-drc' if row['label']=='partial-short' else 'diagnostic-full-drc'
    binding = f.read_json(directory/(name+'-binding.json'))
    verified = f.check_drc_stage(directory,row,name,board,Path(binding['input']),False,binding['before'],
        schematic_parity=True,sandboxed=False)
    assert verified == row['native'] and p.sha(board) == row['candidate_sha256']
    assert p.sha(directory/(name+'.json')) == row['native_report_sha256']
    assert io.inventory(Path(row['source']).parent) == row['source_hashes']
    assert p.immutable(sx.read(board)) == p.immutable(sx.read(Path(row['source'])))
    readbacks[row['label']] = dict(own_Native_process_binding_and_full_schematic=True,native=verified,
        accepted=False,no_new_Native=True)
tree(invalid_base,Path('native-invalid039/enclosure-and-protocol'))
tree(invalid_out,Path('native-invalid039/cases'))
invalid_time = ROOT/'.runs/runtime039-ordinary-native-invalid-001-time.log'
assert 'the following arguments are required: --protocol-sha256' in invalid_time.read_text()
assert cost(invalid_time) == dict(wall_seconds=.09,CPU_seconds=.08)
failures.append(dict(case='invalid-invocation001',controls_passed=False,Native_executed=False,
    child_or_enclosure_started=False,child_receipt_absent_at_invocation=True,
    error='Shared enclosure argparse refused missing --protocol-sha256 before child/enclosure.',
    original_log_sha256=p.sha(invalid_time),retry='attempt002 supplies frozen protocol SHA; first failure not overwritten.',
    complete_external_cost=cost(invalid_time)))

controllers = ['run-full-integration-184.py','full-integration-184-controller.log','full-integration-184-time.log',
    'run-install-distribution-native-012.py','freeze-install012-001.py',
    'install-distribution-native-012-controller.log','install-distribution-native-012-time.log',
    'freeze-runtime039-workflow-plans-001.py','runtime039-workflow-freeze-001.log','runtime039-workflow-freeze-001-time.log',
    'enclose-runtime030-ordinary-workflow-002.py','enclose-native7-independent-control-004.py',
    'freeze-runtime039-ordinary-native-invalid-001.py','qualify-runtime039-ordinary-native-invalid-001.py',
    'runtime039-ordinary-native-invalid-freeze-001.log','runtime039-ordinary-native-invalid-freeze-001-time.log']
for label,attempt,*_ in CASES:
    controllers += ['runtime039-ordinary-'+label+'-'+attempt+suffix for suffix in ('-controller.log','-time.log')]
controllers += ['runtime039-ordinary-hierarchy-whole2Cu-001'+suffix for suffix in ('-controller.log','-time.log')]
controllers += ['runtime039-ordinary-native-invalid-001'+suffix for suffix in
    ('-controller.log','-time.log','-attempt002-controller.log','-attempt002-time.log')]
for name in controllers: retain(ROOT/'.runs'/name,Path('controllers-and-cost')/name)
driver = ROOT/'scripts/qualify_runtime_workflow.py'
for label,attempt,*_ in CASES:
    plan = f.read_json(ROOT/'.runs'/('runtime039-ordinary-'+label+'-'+attempt)/'protocol.json')
    assert p.sha(driver) == plan['driver_sha256']
    assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py') == plan['enclosure_sha256']
retain(driver,Path('controllers-and-cost/qualify_runtime_workflow.py'))
assert p.sha(Path(invalid_plan['controller'])) == invalid_plan['controller_sha256']
retain(Path(invalid_plan['controller']),Path('native-invalid039/actual-controller.py'))
assert p.sha(ROOT/'.runs/enclose-native7-independent-control-004.py') == invalid_plan['enclosure_sha256']
assert p.sha(ROOT/'.runs/freeze-runtime039-ordinary-native-invalid-001.py') == invalid_plan['preparation']['freezer_sha256']
for name,digest in invalid_plan['prerequisite_files'].items(): assert p.sha(ROOT/name) == digest
for name,digest in install_plan['source_files'].items():
    q = runtime/name if name in immutable else ROOT/refs[digest] if digest in refs else ROOT/name
    assert p.sha(q) == digest
    retain(q,Path('installation/controller-source')/name)
for dirname,names in [
    ('runtime039-preparation-before-head-001', ['freeze-install012-001.py','run-install-distribution-native-012.py',
        'qualify-runtime039-ordinary-native-invalid-001.py','freeze-runtime039-workflow-plans-001.py',
        'freeze-runtime039-ordinary-native-invalid-001.py','substitution.json','run-full-integration-184.py']),
    ('runtime039-preparation-before-manifest-001', ['qualify-runtime039-ordinary-native-invalid-001.py','freeze-runtime039-ordinary-native-invalid-001.py']),
]:
    for name in names: retain(ROOT/'.runs'/dirname/name,Path('preparation')/dirname/name)

secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new = {}; checked = {}
for q,name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q,4*1024**2); assert b'\0' not in raw and not secret.search(raw); raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest(); checked[str(q.relative_to(ROOT))] = dict(bytes=len(raw),sha256=digest)
    if digest not in refs: new.setdefault(digest,len(raw))
assert sum(new.values())+2*1024**2 < 16*1024**2, dict(required_unique_payload_bytes=sum(new.values()),index_reserve_bytes=2*1024**2,cap_bytes=16*1024**2)
assert len(selected)<3000 and len(new)<2000
print(json.dumps(dict(preflight_unique_payload_bytes=sum(new.values()),selected_occurrences=len(selected),
    distinct_original_files=len(checked),packet_cap_bytes=16*1024**2)),flush=True)
notes.mkdir()
for q,name in selected: real_retain(q,name)
real_retain(Path(__file__),Path('curate.py'))

scope = '''# Runtime039: floor/schema Native functional milestone

Immutable source57542e996f2b6e7704acd408ac99f6c72e70adc5, selected KiCad10.0.7,
manifest ef7ea961238bf9d3e48e531dc3dcbd06700ac2fe5a270466e3d9365b81a6c728:
48 Python modules/53 immutable files. Full184 passed2,298 tests/one PowerShell
skip; install012 passed fresh curated venv/doctor/owned no-SCH smoke. This is not
clean-OS, relocation, standalone packaging or complete GUI qualification.

Five separately frozen ordinary CLI cases completed preview, Route, review,
choice, fresh Native export and checked export. Hierarchy002 has0/0/0/0 and zero
protected routes: no protection claim from that case. Whole4Cu001 has0/0/6/0 and
10 protected records; partial2Cu001 has0/0/0/0 and4 protected records. Floor2Cu and
floor4Cu each have0/0/6/0 and1 protected route, actual.3mm tracks/.9/.4mm via,
unchanged source/raw Default/rules. Counts are opens/blocking/warnings/exclusions.
Six Datasheet warnings in each affected owned case and all ignored checks remain
visible. Original inputs/full schematic/final own Native/process/class proofs
are retained or linked by exact byte SHA; exact039 pure central readers rechecked
both Route and export. Native acceptance is not human or electrical approval.

Invalid attempt002 observed a real full-SCH Native short (0/4/0/0), and a separate
one-nanometre protected-width change with clean Native diagnostic (0/0/0/0) that
the original-geometry guard refused. Both remain rejected, never exports. The
Native-clean diagnostic does not authorize changed protected copper.

Failed invocations are preserved separately: hierarchy001 supplied a relative
settings path, refused before preview/Native, and left an empty child directory.
Hierarchy002 used absolute paths/fresh storage with unchanged code/input/budgets.
Initial invalid001 lacked required protocol-SHA argv and argparse refused before
child/enclosure; attempt002 is the actual control run. A retry-preparation
assertion wrongly expected the empty hierarchy child directory to be absent;
lead reports it refused before new files/Native. That event exists only in the
active transcript: no file or measured duration is invented, and unknown is not0.

Authoritative external wall/fullCPU seconds: full184371.73/364.09;
install01224.31/20.06; hierarchy001.37/.32 then00231.23/28.07;
whole4Cu35.21/32.23; partial2Cu31.26/27.85; floor2Cu28.22/25.20;
floor4Cu29.73/26.67; invalid argv failure.09/.08 then actual00214.28/12.97.
Nested process/Route/export samples are included, never added again. Freeze
costs are retained separately; other authoring/review/curation remains additional
unmetered work. Polling resource observations are not OS-enforced hard limits.

This finite packet excludes future GUI079 and Mixer039 execution. They were
pending at this milestone's evidence cutoff and are neither read nor qualified
here. No performance comparison, independent family gain, route quality gain,
human review, physical validation, Windows qualification or release claim.
Earlier038 failure/prior001/002/003/004 evidence remains unchanged in dependencies.

Only project-owned GPL source/fixtures, bounded public-safe text logs/metadata and
essential Native workspaces are retained. Exact LICENSE/factory notices are
linked through immutable source and dependencies. No private or third-party CAD,
browser data, downloaded engines, DLLs/JRE/JAR, venv, caches, KiCad configuration
or job-generated documents are selected. Hundreds of redundant source-git
observations are omitted; compact build/source inventories preserve their scope.
Full raw039 data remains Mac-only outside earlier008/010 restoration; this packet
is essential evidence, not full backup/restoration. Originals are unchanged.
The curator runs pure retained-proof readers only, no Native/engine/test/build/
GUI/CI/network/Git commands. This is AI curation, not human PCB review.
'''
with (notes/'SCOPE.md').open('x') as stream: stream.write(scope)
p.save_json(notes/'current-readbacks.json',dict(schema=1,source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    readbacks=readbacks,new_Native_run=False,scope='Pure exact039 existing central consistency readers; no human or external authentication claim.'))
for q in (notes/'SCOPE.md',notes/'current-readbacks.json'):
    raw=q.read_bytes();total+=len(raw);files.append(dict(path=str(q.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for row in material: assert p.sha(ROOT/row['original']) == row['sha256'] == p.sha(ROOT/row['retained'])
for name,digest in immutable.items(): assert p.sha(runtime/name) == digest
assert p.sha(manifest) == MANIFEST
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material,
    excluded_scope=['Only explicit owned039 full/install/five final workflows/two invalid controls and invocation-failure metadata selected.',
        'Hundreds of source-git observations, KiCad config/cache/documents, downloaded tools/JRE/JAR/venv omitted.',
        'Future GUI079/Mixer039 outputs not read or included; transcript-only retry-prep failure has no fabricated log.'],
    preflight=dict(selected_occurrences=len(selected),distinct_original_files=len(checked),
        new_unique_payload_bytes=sum(new.values()),max_file_bytes=4*1024**2,packet_ceiling_bytes=16*1024**2,
        selected_material_secret_pattern_check=True,UTF8_no_NUL=True)))
costs=dict(full184=cost(ROOT/'.runs/full-integration-184-time.log'),install012=cost(ROOT/'.runs/install-distribution-native-012-time.log'),
    invalid_attempt002=cost(ROOT/'.runs/runtime039-ordinary-native-invalid-001-attempt002-time.log'),
    workflow_freeze=cost(ROOT/'.runs/runtime039-workflow-freeze-001-time.log'),
    invalid_freeze=cost(ROOT/'.runs/runtime039-ordinary-native-invalid-freeze-001-time.log'))
assert costs['full184'] == dict(wall_seconds=371.73,CPU_seconds=364.09)
assert costs['install012'] == dict(wall_seconds=24.31,CPU_seconds=20.06)
assert costs['invalid_attempt002'] == dict(wall_seconds=14.28,CPU_seconds=12.97)
invalid_cases = [{key:row[key] for key in ('label','control_observed','accepted','routing_accepted','production_admitted',
    'source_hashes','protected_routes','before_candidate_sha256','mutation','candidate_sha256','native_report_sha256','rejection','native')}
    for row in invalid['cases']]
invalid_cases[1].update(Native_diagnostic_routing_accepted=True,no_additional_native_after_invariant_refusal=True)
summary=dict(schema=1,kind='runtime039-native-floor-schema-functional-milestone',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,runtime_manifest_sha256=MANIFEST,
    native_version='10.0.7',runtime_modules=len(modules),runtime_immutable_files=len(immutable),
    accepted=False,fully_qualified=False,production_qualified=False,project_complete=False,actual_GUI=False,
    human_review=False,physical_electrical_validation=False,Windows_qualified=False,
    full184=dict(passed=True,tests=2298,skips=1,sources_and_tools_unchanged=True,complete_external_cost=costs['full184']),
    install012=dict(passed=True,mode='distribution',complete_external_cost=costs['install012'],
        Native_smoke=build['native'],scope='Fresh curated selected7 venv/doctor/owned no-SCH smoke; not cleanOS/relocation/GUI qualification.'),
    deliveries=deliveries,failed_invocations=failures,
    native_invalid=dict(control_passed=True,actual_Native_invocations=1,failed_pre_Native_invocations=1,
        protocol_sha256=p.sha(invalid_base/'protocol.json'),child_receipt_sha256=p.sha(invalid_out/'result.json'),
        cases=invalid_cases,accepted=False,export_accepted=False,production_admitted=False,
        complete_external_cost=costs['invalid_attempt002']),
    transcript_only_preparation_failure=dict(observed_by_lead=True,artifact=None,measured_cost=None,Native_executed=False,
        reason='Retry-prep absent-output assertion refused existing empty hierarchy001 child directory before new files or Native; no invented log/cost.'),
    additional_preparation_costs=dict(workflow_freeze=costs['workflow_freeze'],invalid_freeze=costs['invalid_freeze']),
    evidence_cutoff=dict(GUI079='Pending; no GUI execution inspected or included.',Mixer039='NOTRUN/pending; no outcome inferred.'),
    source_readback='Exact039 central check_result/check_export and retained invalid DRC/process/fullSCH bindings rechecked without new Native execution.',
    accounting='Complete external wall/fullCPU authoritative, including each failed invocation. Nested observations are not added again. Freeze costs separate; authoring/review/curation/transcript-only prep costs additional unmetered, never zero.',
    rights='Only project-owned GPL source/fixtures and public-safe text logs/metadata; exact LICENSE/factory notices retained or byte-linked through dependencies.',
    limits=['Exposed related owned controls, not independent-board generalization or fair comparative performance/quality proof.',
        'Hierarchy zero protected records gives no protection claim; whole10/partial4/floor1 are separate actual controls.',
        'Six warnings and ignored checks preserved; no human/electrical/physical/GUI/Windows/release qualification.',
        'Full raw039 remains Mac-only outside008/010 restoration; no new restoration claim.'],
    dependencies=dependencies,curation_helper=dict(path=str(helper.relative_to(ROOT)),sha256=p.sha(helper)),
    retention=dict(new_payload_files=len(files),new_payload_bytes=total,material_occurrences=len(material),
        immutable_source_files=len(immutable),no_original_edits=True,no_Native_engine_tests_build_GUI_CI_network_Git_execution=True),
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(output,summary)
physical=[q for q in notes.rglob('*') if q.is_file()]+[output]
assert sum(q.stat().st_size for q in physical)<16*1024**2
assert max(q.stat().st_size for q in physical)<=4*1024**2
for row in files: assert p.sha(ROOT/row['path']) == row['sha256']
print(json.dumps(dict(path=str(output.relative_to(ROOT)),sha256=p.sha(output),files_index_sha256=p.sha(notes/'files.json'),
    physical_files=len(physical),physical_bytes=sum(q.stat().st_size for q in physical),new_payload_files=len(files),
    new_payload_bytes=total,material_occurrences=len(material),fully_qualified=False),sort_keys=True))
