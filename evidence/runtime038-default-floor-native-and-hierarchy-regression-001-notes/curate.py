"""Bounded essential Runtime038 milestone/failure curation; no workers run."""
from pathlib import Path
from decimal import Decimal
import ast, datetime, hashlib, json, os, re, sys
ROOT = Path(__file__).resolve().parents[2]
notes = Path(__file__).resolve().parent
output = ROOT / 'evidence/runtime038-default-floor-native-and-hierarchy-regression-001.json'
assert not output.exists() and sorted(q.name for q in notes.iterdir()) == ['curate.py']
runtime = ROOT / '.runs/runtime-directory-038/runtime'
sys.dont_write_bytecode = True; sys.path.insert(0, str(runtime))
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
for name, expected in [
    ('evidence/default-targets-implicit-resolution-003.json', '7d4dca7a75c0d17712f4ef6c758a372773d9e62d100adb88f5dab0879bed6bc6'),
    ('evidence/default-targets-native-observation-priority-004.json', '9897ae4a0d400240df92a49f0afb757866991ec8a55f77a23a8517d1bba88019'),
    ('evidence/default-targets-full182-harness-failure-001.json', '88f51f0500d9ef775aeaa3be6d30ea6a92a53b135db18143b0bedd55d3d4664f'),
    ('evidence/runtime037-hierarchy-native-milestone-001.json', 'b5e53cad5e71e29b2dd80ab65eab34c699dd4dd39cad5d9c61f0c59dab3af868'),
]:
    q = ROOT / name; assert p.sha(q) == expected
    j = f.read_json(q); index = ROOT / j['files_index']['path']
    assert p.sha(index) == j['files_index']['sha256']
    x = f.read_json(index)
    for row in x['files']: refs.setdefault(row['sha256'], row['path'])
    for row in x['material']: refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=expected, files_index=j['files_index']))

HEAD = '3a71a124521ab1c051a9d772849d7913125518f0'
MANIFEST = '15efd44d677d99ba1ecdcf5c18188d06f76bde24bb97635acdc60dd6c7740ad8'
manifest = runtime / 'runtime-distribution.json'
assert p.sha(manifest) == MANIFEST
runtime_record = f.read_json(manifest)
assert runtime_record['build_source']['git_head'] == HEAD
immutable = runtime_record['immutable_files_sha256']
modules = [name for name in immutable if name.startswith('autorouter/') and name.endswith('.py')]
assert len(immutable) == 53 and len(modules) == 48
for name, digest in immutable.items():
    assert p.sha(runtime / name) == digest
    retain(runtime / name, Path('runtime038/immutable') / name)
retain(manifest, Path('runtime038/runtime-distribution.json'))

full_base = ROOT / '.runs/full-integration-183'
full = f.read_json(full_base / 'execution.json'); full_plan = f.read_json(full_base / 'protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status'] == 'success' and full['process']['exit_code'] == 0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
assert full_plan['tools']['git_head'] == HEAD and p.sha(full_base / 'command.log') == full['log_sha256']
assert p.sha(ROOT / '.runs/run-full-integration-183.py') == full['controller_sha256']
assert re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', (full_base / 'command.log').read_text(), re.M) == [('2289', '385.904')]
assert 'OK (skipped=1)' in (full_base / 'command.log').read_text()
for name, digest in runtime_record['build_source']['files_sha256'].items():
    if name in full_plan['source_sha256']: assert full_plan['source_sha256'][name] == digest
tree(full_base, Path('full183'))
discovery = ROOT / full_plan['discovery']; assert p.sha(discovery) == full_plan['discovery_sha256']
retain(discovery, Path('controllers') / discovery.name)

install_base = ROOT / '.runs/install-distribution-native-011'
install = f.read_json(install_base / 'execution.json'); install_plan = f.read_json(install_base / 'protocol.json')
build_path = runtime.parent / 'result.json'; build = f.read_json(build_path)
assert install['passed'] is True and install['source_unchanged'] is True
assert install['protocol_sha256'] == p.sha(install_base / 'protocol.json')
assert install['child_receipt'] == str(build_path) and install['child_receipt_sha256'] == p.sha(build_path)
assert build['passed'] is True and build['git_head'] == HEAD and build['native_version'] == '10.0.7'
assert build['source_installation_mode'] == 'distribution'
assert build['selected_source_unchanged'] is True and build['installed_product_unchanged'] is True
assert install_plan['source_head'] == HEAD
assert p.sha(ROOT / '.runs/run-install-distribution-native-011.py') == install_plan['controller_sha256']
assert install_plan['full_integration183']['execution_sha256'] == p.sha(full_base / 'execution.json')
assert install_plan['full_integration183']['protocol_sha256'] == p.sha(full_base / 'protocol.json')
tree(install_base, Path('installation/enclosure')); retain(build_path, Path('installation/result.json'))
retain(runtime.parent / 'source-tracked.json', Path('installation/source-tracked.json'))
for command in build['commands']:
    q = Path(command['log']); assert p.sha(q) == command['log_sha256']
    retain(q, Path('installation/command-logs') / q.name)
tree(runtime.parent / 'source-fixture', Path('installation/original-smoke'))
tree(runtime / '.runs/install-native-smoke', Path('installation/native-smoke'))
smoke_path = Path(build['native_receipt']['path'])
assert p.sha(smoke_path) == build['native_receipt']['sha256']
smoke_readback = p.check_result(smoke_path); assert smoke_readback['current'] is True

readbacks = dict(installation_smoke=smoke_readback)
deliveries = []; failure = None; not_run = []
for label in ('floor-2Cu', 'floor-4Cu', 'hierarchy-whole2Cu', 'whole4Cu', 'partial2Cu'):
    base = ROOT / '.runs' / ('runtime038-ordinary-' + label + '-001')
    plan = f.read_json(base / 'protocol.json')
    assert plan['source_head'] == HEAD and plan['runtime'] == str(runtime)
    assert plan['runtime_manifest_sha256'] == MANIFEST
    source = Path(plan['source']); assert io.inventory(source.parent) == plan['source_hashes']
    tree(base, Path('workflow-enclosures') / label)
    for rel in plan['source_hashes']: retain(source.parent / rel, Path('original-inputs') / label / rel)
    child_dir = Path(plan['output']); execution_path = base / 'execution.json'
    if label in ('whole4Cu', 'partial2Cu'):
        assert not os.path.lexists(execution_path) and not os.path.lexists(child_dir)
        not_run.append(dict(case=label, state='FROZEN_NOTRUN', protocol_sha256=p.sha(base / 'protocol.json'),
            source_hashes=plan['source_hashes'], execution_absent=True, child_output_absent=True,
            reason='Sequential set-e batch stopped after the hierarchy refusal, as reported by the lead.'))
        continue
    completed = f.read_json(execution_path); child_path = child_dir / 'result.json'
    assert completed['protocol_sha256'] == p.sha(base / 'protocol.json')
    assert completed['child_receipt'] == str(child_path) and completed['child_sha256'] == p.sha(child_path)
    child = f.read_json(child_path); work = Path(child['workspace'])
    assert child['source_hashes'] == plan['source_hashes']
    tree(child_dir, Path('actual-workflows') / label)
    route_path = work / 'route/result.json'; route = f.read_json(route_path)
    if label == 'hierarchy-whole2Cu':
        assert completed['controls_passed'] is False and completed['workflow_delivered'] is False
        assert child['workflow_delivered'] is False and route['accepted'] is False
        assert route['status'] == 'rejected' and 'native class map source/schema differs' in child['error']
        assert 'engine' not in [step['name'] for step in route['steps']]
        assert not os.path.lexists(work / 'review') and not os.path.lexists(work / 'export')
        mapping = f.read_json(work / 'route/export-netclasses.json')
        old_header = {'schema', 'native_version', 'units', 'resolution', 'source', 'board_sha256', 'project_sha256', 'board_saved', 'nets'}
        assert set(mapping) - old_header == {'effective_floors_nm'} and old_header <= set(mapping)
        failure = dict(case=label, workflow_delivered=False, route_accepted=False,
            child_receipt_sha256=p.sha(child_path), source_hashes=plan['source_hashes'],
            error=child['error'], outer_error=completed['error'], route_reason=route['reason'],
            source_native=route['source_drc'], Native_export_map_sha256=p.sha(work / 'route/export-netclasses.json'),
            source_consumer_sha256=immutable['autorouter/schematic_hierarchy.py'],
            causal_boundary='The immutable hierarchy consumer requires an exact nine-field Native-map header; the new effective_floors_nm header field is refused before engine execution.',
            engine_executed=False, final_Native_or_export_reached=False,
            stages_run=[row['stage'] for row in child['processes']],
            complete_external_cost=cost(ROOT / '.runs/runtime038-ordinary-hierarchy-whole2Cu-001-time.log'),
            historical_six_source_opens_are_unrouted_not_invalidity=True)
        continue
    assert completed['controls_passed'] is True and completed['workflow_delivered'] is True
    assert child['workflow_delivered'] is True and child['status'] == 'completed'
    export_path = work / 'export/export.json'; exported = f.read_json(export_path)
    with p.validation_readback_session():
        rb = p.check_result(route_path); eb = ex.check_export(export_path)
    assert rb['current'] is True and eb['current'] is True
    assert route['accepted'] is True and exported['export_accepted'] is True
    assert route['candidate_sha256'] == exported['candidate_sha256'] == child['candidate_sha256']
    assert route['source_hashes'] == exported['source_hashes'] == plan['source_hashes']
    assert route['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
    counts = [route['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')]
    assert counts == [exported['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 6, 0]
    assert completed['protected_count'] == plan['expected_protected_count'] == 1
    board = sx.read(Path(exported['candidate'])); original = sx.read(source)
    protected = p.protected_for_record(route, original)
    assert len(protected) == 1 and all(node in p.routes(board) for node in protected)
    assert p.immutable(board) == p.immutable(original)
    widths = sorted({str(Decimal(sx.one(node, 'width')[1]).normalize()) for node in sx.children(board, 'segment')})
    vias = sorted({(str(Decimal(sx.one(node, 'size')[1]).normalize()), str(Decimal(sx.one(node, 'drill')[1]).normalize()))
                   for node in sx.children(board, 'via')})
    assert widths == ['0.3'] and vias == [('0.9', '0.4')]
    raw_project = f.read_json(source.with_suffix('.kicad_pro'))
    final_project = f.read_json(Path(exported['project_file']))
    assert raw_project['net_settings']['classes'] == final_project['net_settings']['classes']
    raw_Default = raw_project['net_settings']['classes'][0]
    assert {key:raw_Default[key] for key in ('track_width', 'clearance', 'via_diameter', 'via_drill')} == dict(track_width=.2, clearance=.1, via_diameter=.6, via_drill=.3)
    guide_path = work / 'route' / route['default_target_transport']['file']
    assert p.sha(guide_path) == route['default_target_transport']['sha256']
    guide = f.read_json(guide_path)
    readbacks[label] = dict(Route=rb, export=eb)
    deliveries.append(dict(case=label, workflow_delivered=True, source_hashes=plan['source_hashes'],
        final_candidate_sha256=exported['candidate_sha256'], route_candidate_sha256=route['candidate_sha256'],
        Native_counts=counts, Native_findings=route['native']['findings'], ignored_checks=route['native']['ignored_checks'],
        field_parity_policy=route['native']['field_parity']['policy'],
        whole_project_DRC_clean=route['whole_project_drc_clean'],
        full_schematic_parity=route['schematic_parity'], protected_count=1,
        original_geometry_rules_and_protected_unchanged=True, raw_Default_unchanged=True,
        raw_Default_mm={key:raw_Default[key] for key in ('track_width','clearance','via_diameter','via_drill')},
        final_segment_widths_mm=widths, final_via_diameter_drill_mm=vias, metrics=route['metrics'],
        default_transport_policy=route['default_target_transport']['policy'], default_transport_sha256=p.sha(guide_path),
        current_readback=True, actual_GUI=False, human_review=False,
        complete_external_cost=cost(ROOT / '.runs' / ('runtime038-ordinary-' + label + '-001-time.log')),
        nested_route_cost=dict(wall_seconds=route['wall_seconds'], CPU_seconds=route['total_cpu_seconds']),
        nested_export_cost=dict(wall_seconds=exported['wall_seconds'], CPU_seconds=exported['total_cpu_seconds']),
        scope='One predeclared owned floor/via functional control; not an independent benchmark family or a comparative completion/quality gain.'))

controllers = ['run-full-integration-183.py', 'full-integration-183-controller.log', 'full-integration-183-time.log',
    'run-install-distribution-native-011.py', 'freeze-install011-001.py', 'freeze-install011-001.log',
    'install-distribution-native-011-controller.log', 'install-distribution-native-011-time.log',
    'freeze-runtime038-workflow-plans-001.py', 'enclose-runtime030-ordinary-workflow-002.py']
for label in ('floor-2Cu', 'floor-4Cu', 'hierarchy-whole2Cu'):
    controllers += ['runtime038-ordinary-' + label + '-001' + suffix for suffix in ('-controller.log','-time.log')]
for name in controllers: retain(ROOT / '.runs' / name, Path('controllers-and-cost') / name)
driver = ROOT / 'scripts/qualify_runtime_workflow.py'
for label in ('floor-2Cu','floor-4Cu','hierarchy-whole2Cu'):
    plan = f.read_json(ROOT / '.runs' / ('runtime038-ordinary-'+label+'-001') / 'protocol.json')
    assert p.sha(driver) == plan['driver_sha256']
    assert p.sha(ROOT / '.runs/enclose-runtime030-ordinary-workflow-002.py') == plan['enclosure_sha256']
retain(driver, Path('controllers-and-cost/qualify_runtime_workflow.py'))
for name, digest in install_plan['source_files'].items():
    q = runtime / name if name in immutable else ROOT / refs[digest] if digest in refs else ROOT / name
    assert p.sha(q) == digest
    retain(q, Path('installation/controller-source') / name)
assert failure is not None and len(deliveries) == 2 and len(not_run) == 2
assert not os.path.lexists(runtime / '.runs/gui-session078')
assert not os.path.lexists(runtime / '.runs/native7-comparison-control-runtime038-invalid-001')

secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new = {}; checked = {}
for q, name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q, 4*1024**2); assert b'\0' not in raw and not secret.search(raw); raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest(); checked[str(q.relative_to(ROOT))] = dict(bytes=len(raw),sha256=digest)
    if digest not in refs: new.setdefault(digest,len(raw))
assert sum(new.values()) + 1024**2 < 16*1024**2, json.dumps(dict(required_unique_payload_bytes=sum(new.values()),index_reserve_bytes=1024**2,cap_bytes=16*1024**2))
assert len(selected) < 2000
print(json.dumps(dict(preflight_unique_payload_bytes=sum(new.values()), selected_occurrences=len(selected),
    distinct_original_files=len(checked), cap_bytes=16*1024**2)),flush=True)
for q, name in selected: real_retain(q,name)

scope = '''# Runtime038: two floor deliveries and a hierarchy regression

Immutable source3a71/runtime038 has48 Python modules and53 files, exact manifest
15efd44d677d99ba1ecdcf5c18188d06f76bde24bb97635acdc60dd6c7740ad8.
Full183 passed2,289 tests/one PowerShell skip; distribution install011 passed its
isolated venv/doctor/owned smoke Route/readback. Smoke has no schematic and does
not qualify fullSCH or GUI. Its five ignored checks remain in the raw receipt.

Both predeclared owned2Cu/4Cu floor cases completed six production CLI stages and
fresh Native/fullSCH export. Each final has0opens/0blocking/6warnings/0exclusions,
one protected KEEP route, actual.3mm segments and.9/.4mm via. Raw original Default
.2/.1/.6/.3 and original project/rules/protected copper remain unchanged. All six
Datasheet '~' versus empty warning records, exact field-parity evidence and two
ignored checks are retained. This is routing-scope functional qualification of two
related owned controls, not whole-project DRC cleanliness or family/quality gain.

The first current hierarchy delivery refused before engine execution: the old
exact Native-map header consumer omitted the new effective_floors_nm field. All
source/export/process/worker code and actual refusal evidence are retained. No
final Native/Route acceptance/review/intent/export occurred in that case. Its six
source opens are an unrouted source state, not proof of an invalid design. Frozen
whole4Cu/partial2Cu001 were NOTRUN when the sequential batch stopped. Invalid038,
GUI078 and Mixer038 were NOTRUN. Runtime038 is not fully qualified; a source fix
needs a new runtime039 and fresh gates, not mutation/promotion of this packet.

Complete external costs: full183387.16wall/378.99CPU; install01123.09/20.86;
floor2Cu28.18/25.46; floor4Cu30.45/27.28; hierarchy failure2.28/2.08. Nested
Route/export/process observations are retained and never added again. Authoring,
review, freeze and curation costs are additional unmetered where no separate raw
timing was retained; unknown is notzero.

Only explicit full/install/controller metadata, immutable runtime source and
essential selected workspaces are copied/hash-linked. Hundreds of duplicate
source-git observations, downloaded tools/JRE/JAR/venv, caches and job-generated
configuration/documents are omitted. The build result/source-tracked inventory and
Git source SHA preserve their scope; omission is not full raw backup/restoration.
All CAD inputs are project-owned GPL controls with inherited exact LICENSE/factory
notices. No private browser/CAD or third-party library/bitmap payload is selected.
This curator uses only pure central current-result readers in exact038; no Native,
engine, tests, build, GUI, CI, network or Git command runs. This is AI curation,
not human/electrical/physical review, Windows support or project completion.
'''
with (notes / 'SCOPE.md').open('x') as stream: stream.write(scope)
p.save_json(notes / 'current-readbacks.json',dict(schema=1,runtime_manifest_sha256=MANIFEST,
    source_head=HEAD,readbacks=readbacks,new_Native_run=False,scope='Pure existing central consistency readers; mutable local proof, not authentication/human review.'))
for q in (Path(__file__), notes/'SCOPE.md', notes/'current-readbacks.json'):
    raw=q.read_bytes();total+=len(raw);files.append(dict(path=str(q.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for row in material: assert p.sha(ROOT/row['original'])==row['sha256']==p.sha(ROOT/row['retained'])
for name,digest in immutable.items(): assert p.sha(runtime/name)==digest
assert p.sha(manifest)==MANIFEST
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material,
    excluded_scope=['Hundreds of duplicate source-git-*.json/log build observations: not copied/read as payload; compact build result/source-tracked inventory retained.',
        'Tools/JRE/JAR/venv/caches/job config/documents and unrelated .runs history omitted.'],
    preflight=dict(selected_occurrences=len(selected),distinct_original_files=len(checked),
        new_unique_payload_bytes=sum(new.values()),max_file_bytes=4*1024**2,packet_ceiling_bytes=16*1024**2,
        selected_material_secret_pattern_check=True,UTF8_no_NUL=True)))
costs=dict(full183=cost(ROOT/'.runs/full-integration-183-time.log'),
    install011=cost(ROOT/'.runs/install-distribution-native-011-time.log'))
assert costs['full183']==dict(wall_seconds=387.16,CPU_seconds=378.99)
assert costs['install011']==dict(wall_seconds=23.09,CPU_seconds=20.86)
summary=dict(schema=1,kind='runtime038-floor-functional-positives-and-hierarchy-regression',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,
    runtime_manifest_sha256=MANIFEST,native_version='10.0.7',runtime_modules=48,runtime_immutable_files=53,
    accepted=False,fully_qualified=False,production_qualified=False,project_complete=False,actual_GUI=False,
    human_review=False,physical_electrical_validation=False,Windows_qualified=False,
    full183=dict(passed=True,tests=2289,skips=1,sources_and_tools_unchanged=True,complete_external_cost=costs['full183']),
    install011=dict(passed=True,mode='distribution',complete_external_cost=costs['install011'],
        Native_smoke=build['native'],scope='Fresh selected7 curated venv/doctor/owned no-SCH smoke; not cleanOS/relocation/full sixstage/GUI qualification.'),
    floor_deliveries=deliveries,hierarchy_failure=failure,frozen_not_run=not_run,
    other_not_run=['Nativeinvalid038','GUI078','Mixer038'],
    disposition='Partial Native functional milestone with a demonstrated hierarchy regression. Runtime038 remains immutable and incomplete; new parity source requires039 and fresh full/install/native/GUI gates.',
    source_readback='Exact038 central check_result/check_export re-read both positive Route/fresh-export proofs; original input inventories and protected geometry match. No new Native execution.',
    accounting='Complete external exits are authoritative; child/Route/export samples are nested, not additional cost. Earlier003/004/182 failures/preparation remain separate dependencies. Authoring/freeze/review/curation costs additional unmetered unless retained separately; no zero-cost inference.',
    rights='Project-owned GPL fixture/code only; exact LICENSE in immutable source and prior factory/construction rights via004. No private or third-party CAD/library/bitmap payload.',
    limits=['Two related owned controls; no comparative/broader-family completion or quality gain.',
        'Six warnings and ignored checks remain visible; no human/electrical/physical approval.',
        'Hierarchy fails before engine; whole4Cu/partial2Cu/invalid/GUI/Mixer038 not run.',
        'Essential text packet only; full raw remains Mac-only, outside prior008/010 restoration scope. No release or restoration claim.'],
    dependencies=dependencies,curation_helper=dict(path=str(helper.relative_to(ROOT)),sha256=p.sha(helper)),
    retention=dict(new_payload_files=len(files),new_payload_bytes=total,material_occurrences=len(material),
        immutable_source_files=53,no_original_edits=True,no_Native_engine_tests_build_GUI_CI_network_Git_execution=True),
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(output,summary)
physical=[q for q in notes.rglob('*') if q.is_file()]+[output]
assert sum(q.stat().st_size for q in physical)<16*1024**2
assert max(q.stat().st_size for q in physical)<=4*1024**2
for row in files:assert p.sha(ROOT/row['path'])==row['sha256']
print(json.dumps(dict(path=str(output.relative_to(ROOT)),sha256=p.sha(output),
    files_index_sha256=p.sha(notes/'files.json'),physical_files=len(physical),
    physical_bytes=sum(q.stat().st_size for q in physical),new_payload_files=len(files),
    new_payload_bytes=total,material_occurrences=len(material),fully_qualified=False),sort_keys=True))
