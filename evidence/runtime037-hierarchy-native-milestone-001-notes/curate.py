"""Curate only the completed runtime037 owned Native milestone; no workers."""
from pathlib import Path
import ast, datetime, hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
runtime = ROOT/'.runs/runtime-directory-037/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

notes = Path(__file__).parent
packet = ROOT/'evidence/runtime037-hierarchy-native-milestone-001.json'
assert not packet.exists() and set(notes.iterdir()) == {Path(__file__)}
helper = ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('retain', 'tree', 'cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))
refs = {}; files = []; material = []; total = 0; queued = []; dependencies = []
for name in ('evidence/runtime030-native-workflow-qualification-001.json',
             'evidence/runtime036-native-prerequisites-failure-001.json',
             'evidence/hierarchy-stamp-v2-correction-001.json'):
    source = ROOT/name; data = f.read_json(source); index = ROOT/data['files_index']['path']
    assert p.sha(index) == data['files_index']['sha256']
    idx = f.read_json(index)
    for row in idx.get('files', []): refs.setdefault(row['sha256'], row['path'])
    for row in idx.get('material', []): refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=p.sha(source), files_index=data['files_index']))
shared_retain = retain
def retain(source, name): queued.append((Path(source), Path(name)))

head = 'c3e7e8ef4dadce1f83f838322fb5d685ce3714ac'
manifest = runtime/'runtime-distribution.json'; md = f.read_json(manifest)
assert p.sha(manifest) == 'c1ef6a1e1f47d03e39ca63c3114707889d86a3269fbccf5dcc9cec9ccfcba940'
assert md['build_source']['git_head'] == head and md['native_version'] == '10.0.7'
assert len(md['immutable_files_sha256']) == 52
assert sum(name.startswith('autorouter/') and name.endswith('.py') for name in md['immutable_files_sha256']) == 47
for name, digest in md['immutable_files_sha256'].items():
    assert p.sha(runtime/name) == digest
    retain(runtime/name, Path('runtime/immutable')/name)
retain(manifest, Path('runtime/runtime-distribution.json'))
fullroot = ROOT/'.runs/full-integration-180'; full = f.read_json(fullroot/'execution.json')
fullplan = f.read_json(fullroot/'protocol.json')
installroot = ROOT/'.runs/install-distribution-native-010'; install = f.read_json(installroot/'execution.json')
installplan = f.read_json(installroot/'protocol.json')
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
assert fullplan['tools']['git_head'] == head and installplan['source_head'] == head
assert install['passed'] and install['source_unchanged'] and install['process']['cleanup_complete']
assert p.sha(fullroot/'command.log') == full['log_sha256']
assert 'Ran 2249 tests in 354.324s' in (fullroot/'command.log').read_text()
tree(fullroot, Path('full180')); tree(installroot, Path('install010/enclosure'))
installed = f.read_json(runtime.parent/'result.json')
assert installed['passed'] and installed['git_head'] == head and installed['check_result']['current']
assert p.sha(runtime.parent/'result.json') == install['child_receipt_sha256']
retain(runtime.parent/'result.json', Path('install010/runtime-result.json'))
for command in installed['commands']:
    log = Path(command['log']); assert log.parent == runtime.parent and p.sha(log) == command['log_sha256']
    retain(log, Path('install010/logs')/log.name)
tree(runtime/'.runs/install-native-smoke', Path('install010/native-smoke'))
tree(runtime.parent/'source-fixture', Path('install010/original-smoke-source'))

identityroot = ROOT/'.runs/hierarchy-native-controls-002'
identityplan = f.read_json(identityroot/'protocol.json'); identityout = Path(identityplan['output'])
identity = f.read_json(identityout/'result.json'); identityouter = f.read_json(identityroot/'enclosure/result.json')
assert identityplan['source_head'] == head and identityplan['runtime_manifest_sha256'] == p.sha(manifest)
assert p.sha(identityroot/'protocol.json') == identity['protocol_sha256'] == identityouter['protocol_sha256']
assert p.sha(identityout/'result.json') == identityouter['child_sha256']
assert identity['control_passed'] and identityouter['passed'] and len(identity['cases']) == 5
assert all(row['passed'] for row in identity['cases'])
assert all(identity[k] is False for k in ('accepted', 'production_admitted', 'project_complete', 'actual_GUI', 'human_review'))
assert p.tree_hash(Path(identityplan['source']).parent) == identityplan['source_hashes']
tree(identityroot, Path('identity002/enclosure')); tree(identityout, Path('identity002/cases'))
tree(Path(identityplan['source']).parent, Path('identity002/original-source'))

deliveries = []
for label, native_counts, protected_count in (
        ('hierarchy-whole2Cu', [0,0,0,0], 0), ('whole4Cu', [0,0,6,0], 10), ('partial2Cu', [0,0,0,0], 4)):
    base = ROOT/('.runs/runtime037-ordinary-'+label+'-001')
    plan = f.read_json(base/'protocol.json'); outer = f.read_json(base/'execution.json')
    child = Path(plan['output']); result = f.read_json(child/'result.json'); workspace = Path(result['workspace'])
    route = f.read_json(workspace/'route/result.json'); export = f.read_json(workspace/'export/export.json')
    assert plan['source_head'] == head and plan['runtime_manifest_sha256'] == p.sha(manifest)
    assert p.sha(base/'protocol.json') == outer['protocol_sha256'] and p.sha(child/'result.json') == outer['child_sha256']
    assert outer['controls_passed'] and outer['workflow_delivered'] and outer['process']['cleanup_complete']
    assert outer['Native_counts'] == native_counts and outer['protected_count'] == protected_count
    assert result['workflow_delivered'] and result['status'] == 'completed'
    assert [row['stage'] for row in result['processes']] == ['preview','route','review','choice','export','verify_export']
    assert all(row['process']['exit_code'] == 0 and row['process']['cancel_requested'] is False
               and row['process']['log_truncated'] is False for row in result['processes'])
    assert route['accepted'] and route['status'] == 'routing_accepted' and export['export_accepted']
    assert [export['native'][k] for k in ('opens','blocking','warnings','exclusions')] == native_counts
    assert [route['native'][k] for k in ('opens','blocking','warnings','exclusions')] == native_counts
    assert route['schematic_parity'] == export['schematic_parity'] == 'checked by final native DRC'
    assert route['invariants_unchanged'] and export['original_geometry_and_routing_unchanged']
    assert len(route['protected_route_import']['matches']) == protected_count
    assert result['route_readback']['current'] and result['export_readback']['current']
    assert p.sha(Path(route['candidate'])) == route['candidate_sha256'] == result['candidate_sha256']
    assert p.sha(Path(export['candidate'])) == export['candidate_sha256'] == result['export_readback']['candidate_sha256']
    assert p.tree_hash(Path(plan['source']).parent) == plan['source_hashes'] == route['source_hashes'] == export['source_hashes']
    for row in result['processes']:
        assert p.sha(child/(row['stage']+'.log')) == row['log_sha256']
    tree(base, Path('deliveries')/label/'enclosure'); tree(child, Path('deliveries')/label/'workflow')
    tree(Path(plan['source']).parent, Path('deliveries')/label/'original-source')
    deliveries.append(dict(label=label, attempt='001', workflow_delivered=True,
        route_accepted=True, export_accepted=True, Native_counts=native_counts,
        protected_count=protected_count, noProtectionClaim=protected_count == 0,
        candidate_sha256=result['candidate_sha256'], export_candidate_sha256=export['candidate_sha256'],
        source_hashes=plan['source_hashes'], route_readback=result['route_readback'], export_readback=result['export_readback'],
        ignored_checks=export['native']['ignored_checks'], warnings=export['native']['findings'],
        whole_project_drc_clean=export['whole_project_drc_clean'], metrics=result['metrics'],
        route_seconds=plan['budgets']['route'], export_seconds=plan['budgets']['export'], whole_budget_seconds=result['whole_budget_seconds'],
        complete_cost=cost(ROOT/('.runs/runtime037-ordinary-'+label+'-001-time.log')),
        nested_controller_wall_seconds=outer['complete_wall_seconds'], nested_controller_full_CPU_seconds=outer['complete_full_CPU_seconds'],
        actual_GUI=False, human_review=False, applied=False))

invalidroot = ROOT/'.runs/runtime037-ordinary-native-invalid-001'
invalidplan = f.read_json(invalidroot/'protocol.json'); invalidout = Path(invalidplan['output'])
invalid = f.read_json(invalidout/'result.json'); invalidouter = f.read_json(invalidroot/'enclosure/result.json')
assert invalidplan['source_head'] == head and invalidplan['runtime_manifest_sha256'] == p.sha(manifest)
assert p.sha(invalidroot/'protocol.json') == invalid['protocol_sha256'] == invalidouter['protocol_sha256']
assert p.sha(invalidout/'result.json') == invalidouter['child_sha256']
assert invalid['control_passed'] and invalidouter['passed'] and len(invalid['cases']) == 2
assert all(invalid[k] is False for k in ('accepted','routing_accepted','export_accepted','production_admitted','Native_product_admission','actual_GUI','human_review'))
short, width = invalid['cases']
assert [short['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,4,0,0]
assert any(row['type'] == 'shorting_items' for row in short['native']['findings'])
assert [width['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,0,0,0]
assert width['mutation']['added_nanometres'] == 1 and width['rejection'] == 'protected route changed'
assert width['no_additional_native_after_invariant_refusal'] and width['Native_diagnostic_routing_accepted']
assert all(row['control_observed'] and row['accepted'] is False for row in invalid['cases'])
tree(invalidroot, Path('native-invalid037/enclosure-and-protocol'))
tree(invalidout, Path('native-invalid037/cases'))
tree(ROOT/'.runs/runtime037-invalid-preparation-draft-001', Path('native-invalid037/pre-execution-draft'))
retain(ROOT/'.runs/runtime037-ordinary-native-invalid-preparation-001.json', Path('native-invalid037/preparation-note.json'))

access = ROOT/'.runs/gui-runtime037-077-access-001.json'; gui = f.read_json(access)
assert gui['actual_GUI_qualified'] is False and gui['GUI_jobs'] == [] and gui['runtime_manifest_sha256'] == p.sha(manifest)
session = ROOT/gui['prepared_session']; launcher = Path(gui['prepared_launcher']).parent
if not launcher.is_absolute(): launcher = ROOT/launcher
state = f.read_json(session/'prepared-state.json')
assert state['actual_GUI_qualified'] is False and state['runtime_manifest_sha256'] == p.sha(manifest)
assert state['source_head'] == head
gui_selected = [access, session/'prepared-state.json', session/'prepare-launcher-process.json', session/'prepare-launcher.log',
    session/'route-settings.json', session/'recovery-controls-001/protocol-required-001.json',
    session/'recovery-controls-001/no-repair/route-settings.json', session/'recovery-controls-001/repair/route-settings.json',
    session/'recovery-controls-001/unsupported4Cu/route-settings.json', launcher/'Launch Autorouter.command', launcher/'README.txt', launcher/'install.json']
for source in gui_selected:
    relative = source.relative_to(runtime/'.runs') if source.is_relative_to(runtime/'.runs') else Path(source.name)
    retain(source, Path('GUI077/preparation')/relative)
for folder in ('project','inspection','hierarchy-project','recovery-controls-001/no-repair/project','recovery-controls-001/unsupported4Cu/project'):
    tree(session/folder, Path('GUI077/owned-project-copies')/folder)
gui_selected_paths = {str(source) for source, _ in queued if source.is_relative_to(session) or source.is_relative_to(launcher)}
gui_excluded = []
for base in (session, launcher):
    for name, digest in io.inventory(base, max_bytes=64*1024**2).items():
        source = base/name
        if str(source) not in gui_selected_paths:
            gui_excluded.append(dict(path=str(source.relative_to(ROOT)), bytes=source.stat().st_size, sha256=digest,
                reason='Preparation-only metadata suffices; omit Interf recovery CAD/bitmap payload, generated config/documents/icons. No GUI qualification.'))

controllers = [
    (ROOT/'.runs/run-full-integration-180.py', full['controller_sha256']),
    (ROOT/'.runs/full-suite-local-root-019.py', fullplan['discovery_sha256']),
    (ROOT/'.runs/run-install-distribution-native-010.py', installplan['controller_sha256']),
    (ROOT/'.runs/enclose-runtime030-independent-control-001.py', identityplan['enclosure_sha256']),
    (Path(identityplan['controller']), identityplan['controller_sha256']),
    (ROOT/'.runs/enclose-runtime030-ordinary-workflow-001.py', f.read_json(ROOT/'.runs/runtime037-ordinary-whole4Cu-001/protocol.json')['enclosure_sha256']),
    (ROOT/'scripts/qualify_runtime_workflow.py', f.read_json(ROOT/'.runs/runtime037-ordinary-whole4Cu-001/protocol.json')['driver_sha256']),
    (ROOT/'.runs/enclose-native7-independent-control-004.py', invalidplan['enclosure_sha256']),
    (Path(invalidplan['controller']), invalidplan['controller_sha256']),
    (ROOT/'.runs/freeze-runtime037-ordinary-native-invalid-001.py', invalidplan['preparation']['freezer_sha256'])]
for source, digest in controllers:
    assert p.sha(source) == digest
    retain(source, Path('controllers')/source.name)
for name in ('scripts/install_smoke.py','scripts/prepare_runtime.py','experiments/schematic_hierarchy_native_v1/fixture.py',
             'experiments/native_schematic_transport_v1/fixture.py'):
    assert p.sha(ROOT/name) == fullplan['source_sha256'][name]
    retain(ROOT/name, Path('controllers/source-c3e7')/name)
for name in ('.runs/freeze-runtime037-workflow-plans-001.py','.runs/prepare-runtime037-gui077.py',
             '.runs/prepare-runtime037-gui077-001.log','.runs/prepare-runtime037-gui077-001-time.log',
             '.runs/runtime037-native-invalid-freeze-001.log','.runs/runtime037-native-invalid-freeze-001-time.log'):
    retain(ROOT/name, Path('controllers-and-preparation')/Path(name).name)
for stem in ('full-integration-180','install-distribution-native-010','hierarchy-native-controls-002',
             'runtime037-ordinary-hierarchy-whole2Cu-001','runtime037-ordinary-whole4Cu-001','runtime037-ordinary-partial2Cu-001',
             'runtime037-ordinary-native-invalid-001'):
    for suffix in ('-controller.log','-time.log'):
        retain(ROOT/'.runs'/(stem+suffix), Path('costs')/(stem+suffix))
review = ROOT/'.runs/runtime037-hierarchy-native-result-review-001.json'
assert p.sha(review) == 'e8a79bc28ddea1fe8b04dae69bc6a994443b3f82e7d622627dbf2c6674247d1c'
retain(review, Path('independent-AI-review')/review.name); retain(helper, Path('controllers')/helper.name)

# Validate every selected byte before retaining any additional payload.
new = {}; names = {}; findings = []
secret = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|(?i:Authorization:\s*Bearer\s+[A-Za-z0-9_.-]{20,})')
for source, name in queued:
    raw = io.read_bytes(source, 4*1024**2); assert b'\0' not in raw; raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    assert name not in names or names[name] == digest; names[name] = digest
    if secret.search(raw): findings.append(str(source.relative_to(ROOT)))
    if digest in refs: assert p.sha(ROOT/refs[digest]) == digest
    else: new.setdefault(digest, len(raw))
assert not findings and sum(new.values()) + Path(__file__).stat().st_size < 16*1024**2 and len(new) < 1900
for source, name in queued: shared_retain(source, name)
assert total == sum(new.values()) and len(files) == len(new)
curator_raw = Path(__file__).read_bytes()
files.append(dict(path=str(Path(__file__).relative_to(ROOT)), bytes=len(curator_raw), sha256=hashlib.sha256(curator_raw).hexdigest(), authored=True)); total += len(curator_raw)
scope = '''# Retention scope

Completed source c3e7e8ef4dadce1f83f838322fb5d685ce3714ac/runtime037 only:
full180, install010, five identity002 controls, three ordinary sixstage
deliveries, one actual two-case invalid037 invocation and GUI077 preparation.
No unfinished trial or Mixer outcome was read. Earlier failed identity001,
full179/install009 and causal correction remain linked and are not rewritten.

All copied design payloads are small project-owned generated fixtures under
the retained GPL-3.0-or-later LICENSE and factory notices. GUI077 preparation
metadata refers to an existing licensed Interf recovery project, but its CAD,
library and bitmap payload is excluded. No private input, dataset, downloaded
tool, KiCad/JRE/JAR/venv binary or global user configuration is copied.

Original text bytes are preserved; identical SHA bytes reference prior public
030/036/correction payloads. files.json records every original and retained
path. Unique current037 immutable source bytes are copied where not already
retained. Commit/source/manifest pins do not authenticate mutable evidence.

Hierarchy has protected0 and noProtectionClaim=true. Whole4Cu and partial2Cu
separately retain protected10/protected4 actual original/final proof. Whole4Cu
has six warnings, not whole-project DRC cleanliness. Two ignored owned Native
checks remain explicit. Identity source opens are not a routing win or a
blanket invalid-source diagnosis. Only one exposed owned hierarchy fixture
was completed; no independent-family/quality/comparison superiority follows.

The pre-execution invalid drafts/placeholder/field corrections are preparation,
not failed Native invocations. Actual invalid001 observed a full-SCH short
(0/4/0/0); the +1nm protected-width mutant was Native-clean (0/0/0/0) and still
refused by the invariant guard before more Native. Neither was admitted.

GUI077 was prepared; the access receipt reports locked Mac, no launch/input,
no GUI jobs and actual_GUI_qualified=false. Old GUI evidence does not qualify037.

Excluded: per-job kicad-cache/config/documents, engine-config, tmp, __pycache__,
runtime tools/venv and repeated source-git logs/template. GUI excluded-file
hashes are explicit in files.json. This bounded text-only curation is not a
whole-archive audit, full raw backup, restoration, clean-OS test or release.
Full raw newer material remains on this Mac outside backups008/010.

External costs count each completed invocation once. Nested controller/step/
route/export samples are not added again. Invalid freeze and GUI preparation
are separate measured costs. Interactive authoring/review/curation cost is
additional and whole CPU/wall is unmeasured, not zero. Curation started no
Native/tests/routing/GUI/CI/build/install/network/delegation work.
'''
scope_path = notes/'SCOPE.md'; scope_raw = scope.encode(); scope_path.open('xb').write(scope_raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)), bytes=len(scope_raw), sha256=hashlib.sha256(scope_raw).hexdigest(), authored=True)); total += len(scope_raw)
assert total < 16*1024**2
index = notes/'files.json'
p.save_json(index, dict(schema=1, files=files, material=material, dependencies=dependencies,
    GUI077_excluded=gui_excluded, excluded_patterns=['kicad-cache/**','kicad-config/**','kicad-documents/**','engine-config/**','tmp/**','__pycache__/**','runtime/.venv/**','runtime/.tools/**','source-git*.json','source-git*.log','empty-git-template/**'],
    preflight=dict(text_only=True, max_file_bytes=4*1024**2, max_new_bytes=16*1024**2, new_unique_payload_bytes=sum(new.values()), secret_pattern_findings=findings),
    rights='Project-owned GPL-3.0-or-later design/source/controller payload only. Interf recovery project appears only as preparation metadata and excluded-file hashes; no recovery CAD/library/bitmap copied.'))
identity_cases = []
for row in identity['cases']:
    native = row.get('Native')
    identity_cases.append(dict(case=row['case'], passed=row['passed'], Native_counts=[native[k] for k in ('opens','blocking','warnings','exclusions')] if native else None,
        rejection=row.get('rejection'), proof_sha256=row.get('proof_sha256'), ignored_checks=native.get('ignored_checks') if native else None))
invalid_cases = []
for row in invalid['cases']:
    invalid_cases.append({key: row[key] for key in ('label','control_observed','accepted','routing_accepted','production_admitted','protected_routes','before_candidate_sha256','mutation','candidate_sha256','native_report_sha256','rejection')})
    invalid_cases[-1].update(Native_counts=[row['native'][k] for k in ('opens','blocking','warnings','exclusions')], ignored_checks=row['native']['ignored_checks'], findings=row['native']['findings'])
record = dict(schema=1, kind='runtime037-owned-hierarchy-and-regression-Native-milestone',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=head,
    runtime_manifest_sha256=p.sha(manifest), native_version='10.0.7', runtime_modules=47, runtime_immutable_files=52,
    accepted=False, project_complete=False, actual_GUI=False, human_review=False, physical_electrical_validation=False,
    observations='Actual selected7 ordinary software delivery of one exposed owned Default hierarchy fixture plus prior whole/partial owned protection regressions. This is functionality, not an algorithmic routing gain or broad family/hierarchy/GUI/Windows qualification.',
    prior_records=dependencies,
    full180=dict(passed=True, tests=2249, skips=1, complete_cost=cost(ROOT/'.runs/full-integration-180-time.log'), nested_controller_wall_seconds=full['wall_seconds'], nested_controller_full_CPU_seconds=full['full_cpu_seconds']),
    install010=dict(passed=True, mode='distribution', complete_cost=cost(ROOT/'.runs/install-distribution-native-010-time.log'), scope='Fresh copied selected7 runtime/venv/doctor/owned smoke Route/check, not cleanOS/relocation/GUI/Windows.'),
    identity002=dict(passed=True, accepted=False, production_admitted=False, cases=identity_cases,
        complete_cost=cost(ROOT/'.runs/hierarchy-native-controls-002-time.log'),
        interpretation='Wrong sibling-instance PCB remains Native6opens/0blocking but binder-refused. Source unitUUID-exchange with unchangedPCB passes v2proof and sourceNative6/0/0/0. Source opens are unrouted connectivity, not invalidity or routing superiority.'),
    deliveries=deliveries,
    native_invalid037=dict(control_passed=True, actual_invocations=1, accepted=False, production_admitted=False, cases=invalid_cases,
        no_additional_native_after_protected_refusal=True, complete_cost=cost(ROOT/'.runs/runtime037-ordinary-native-invalid-001-time.log'),
        freeze_cost=cost(ROOT/'.runs/runtime037-native-invalid-freeze-001-time.log'),
        preparation='Prospective drafts and agent note retained unchanged; lead corrected nonexistent selected_native_version field and filled actual manifest/controller pins before execution. No failed invalid Native invocation is invented.'),
    GUI077=dict(prepared=True, actual_GUI_qualified=False, GUI_jobs=[], access_receipt=str(access.relative_to(ROOT)), access_receipt_sha256=p.sha(access),
        observation='Mac locked response after inventory; no window/input/app launch achieved. No noWindowsAvailable substitution.',
        preparation_cost=cost(ROOT/'.runs/prepare-runtime037-gui077-001-time.log'), excluded_payloads=len(gui_excluded)),
    independent_review=dict(path=str(review.relative_to(ROOT)), sha256=p.sha(review), AI_not_human=True,
        scope='Fresh exact037 shared class/process/fullSCH/PRL/refusal/Route/export readback on hierarchy delivery, no new Native; bounded review has no material binding/accounting discrepancy. Generic protected-copper scope wording does not confer protection qualification.'),
    accounting='Complete external wall/CPU seconds: full180355.44/349.72; install01021.23/19.46; identity0026.99/6.41; hierarchy29.21/26.86; whole33.78/31.15; partial29.40/26.26; invalid13.89/12.51. Nested observations are included, not added again. Invalid freeze0.65/0.44 and GUI preparation0.76/0.67 are separate. Authoring/review/curation and other work additional, whole CPU unknown, notzero.',
    public_safety='Bounded selected files preflighted UTF8/noNUL/4MiB each and known credential/private-key patterns. No findings. This is a pattern check, not authentication or a general secret guarantee. All original/retained hashes checked again after copying.',
    source_rights='Only project-owned GPL generated design payloads with repository LICENSE and factory notices. No third-party recovery CAD/library/bitmap or private source published by this packet.',
    limits=['No comparative routing/quality win, unrelated-family gain or generalized hierarchy claim.','Hierarchy protected0 explicitly gives no protection proof; whole/partial protection evidence is separate.','Six whole4Cu warnings and two ignored Native checks retained.','Actual037GUI and new GUI controls pending; no human/electrical/physical/Windows admission.','Full raw newer evidence remains Mac-only outside008/010; no restoration or full backup performed.'],
    retention=dict(new_payload_files=len(files), new_payload_bytes=total, original_material_paths=len(material), max_new_bytes=16*1024**2, max_file_bytes=4*1024**2, source_copies_unchanged=True),
    files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
for row in material: assert p.sha(ROOT/row['original']) == p.sha(ROOT/row['retained']) == row['sha256']
p.save_json(packet, record)
print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), packet_sha256=p.sha(packet), index_sha256=p.sha(index),
    new_payload_files=len(files), new_payload_bytes=total, original_material_paths=len(material), physical_files_including_summary_index=len(files)+2)))
