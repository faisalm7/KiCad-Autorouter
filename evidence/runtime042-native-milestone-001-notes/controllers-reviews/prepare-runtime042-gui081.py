"""Prepare fresh GUI081 fixtures/launcher only; no GUI or Native qualification.

Adapted from prepare-runtime039-gui079.py. Run only after the separate committed
042 build, full187 and install015 pass, plus independently verified current042
ordinary hierarchy/whole/partial/floor/alias Native positives and invalid042. This preparation
does not qualify those gates or infer them from old identity002. Existing037/077,
033/074 and original projects are read-only inputs. No tools, archives, candidate
boards or libraries copied. Actual042 manifest SHA is captured only at execution;
no future SHA or passed Native receipt is invented here.
"""
from pathlib import Path
import datetime, json, os, shutil, sys, time

START = time.monotonic()
ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT/'.runs/runtime-directory-042/runtime'
assert runtime.is_dir(), 'runtime042 must already be built; separate Native gates remain required'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, preferences as pref, provenance as pv
from autorouter import floor_route as f, placement_clearance as pc, handoff as h, gui, review_export as ex
from autorouter.runner import run

HEAD = '82aaa3b750007ef2ffaafd367ffcb718aa93865e'
GUI = '93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
PIPELINE = 'eb967f9bfb8643d1c8752fcab0efbab70b6b2a1d7e72daa147d55fa21e7e0da5'
MANIFEST = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
assert c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
TEMPLATE = ROOT/'.runs/prepare-runtime039-gui079.py'
TEMPLATE_SHA = '5660144cae8f67d2d6d419ab9f808950773f07d72ef81fff8462566858e8fe2f'
assert p.sha(TEMPLATE) == TEMPLATE_SHA
identity_receipt = ROOT/'.runs/hierarchy-native-controls-002/enclosure/result.json'
identity_sha = '8da372bcadd04b156dc8f06ffab9dac05926399bebc2c1cb4adbf49900a438d5'
assert p.sha(identity_receipt) == identity_sha
assert f.read_json(identity_receipt)['passed'] is True
fixture_identity = dict(receipt=str(identity_receipt), sha256=identity_sha,
    scope='Historical identity002 verifies fixture identity only; not current042 Native qualification.')
alias_preparation = ROOT/'.runs/native7-source-all-alias-controls-001/fixture-preparation.json'
alias_preparation_sha = '5ce022a7666c9140c07cba188def2016da588e63d8903a4e1cfa1a03bb5f60b1'
assert p.sha(alias_preparation) == alias_preparation_sha
alias_fixture = f.read_json(alias_preparation)
alias_board = h.real_path(alias_fixture['source'])
assert pc.inventory(alias_board.parent) == alias_fixture['source_hashes']
assert pc.inventory(h.real_path(alias_fixture['original_source'])) == alias_fixture['original_source_hashes']
required_current_Native_gates = [
    'Fresh current042 ordinary hierarchy whole2Cu fullSCH/closure/final/readback',
    'Fresh current042 ordinary whole4Cu and partial2Cu protected/final/export/readback',
    'Fresh current042 floor/implicit-Default positive and invalid Native controls',
    'Fresh current042 signal/display alias plus padless-census fullSCH/protected/final/export/readback',
]
# Exact six positive and existing004 invalid receipts are checked below. No
# protocol/manifest placeholder or unexecuted receipt is accepted as a pass.
assert h.real_path(runtime) == runtime
prerequisites = {str(alias_preparation): alias_preparation_sha}
for name in ('full-integration-187', 'install-distribution-native-015'):
    receipt = ROOT/'.runs'/name/'execution.json'
    data = f.read_json(receipt)
    assert data.get('passed') is True
    assert data.get('sources_unchanged', data.get('source_unchanged')) is True
    assert data['process']['status'] == 'success' and data['process']['exit_code'] == 0
    assert data['process']['cleanup_complete'] is True and data['process']['log_truncated'] is False
    prerequisites[str(receipt)] = p.sha(receipt)
install = f.read_json(ROOT/'.runs/install-distribution-native-015/execution.json')
assert install['child_receipt'] == str(runtime.parent/'result.json')
assert p.sha(runtime.parent/'result.json') == install['child_receipt_sha256']
installed = f.read_json(runtime.parent/'result.json')
assert installed['passed'] is True and installed['git_head'] == HEAD and installed['native_version'] == '10.0.7'
prerequisites[str(runtime.parent/'result.json')] = install['child_receipt_sha256']
tools = p.tool_manifest(); manifest = runtime/pv.MANIFEST; manifest_pin = p.sha(manifest)
assert manifest_pin == MANIFEST, 'exact observed042 manifest required'
assert tools['git_head'] == HEAD and tools['source_provenance']['kind'] == pv.KIND
assert tools['source_provenance']['manifest_sha256'] == manifest_pin
assert tools['source_provenance']['native_version'] == '10.0.7'
assert f.read_json(manifest)['build_source']['git_head'] == HEAD
for name, digest in (('autorouter/gui.py', GUI), ('autorouter/pipeline.py', PIPELINE)):
    assert p.sha(runtime/name) == tools['implementation_sha256'][name] == digest

full_protocol = ROOT/'.runs/full-integration-187/protocol.json'
full_data = f.read_json(full_protocol)
assert full_data['tools']['git_head'] == HEAD
for name, digest in tools['implementation_sha256'].items():
    assert full_data['source_sha256'][name] == digest
prerequisites[str(full_protocol)] = p.sha(full_protocol)
install_protocol = ROOT/'.runs/install-distribution-native-015/protocol.json'
install_plan = f.read_json(install_protocol)
assert p.sha(install_protocol) == install['protocol_sha256']
assert install_plan['source_head'] == HEAD and install_plan['output'] == str(runtime.parent)
assert install_plan['full_integration187']['protocol_sha256'] == p.sha(full_protocol)
assert install_plan['full_integration187']['execution_sha256'] == prerequisites[str(ROOT/'.runs/full-integration-187/execution.json')]
prerequisites[str(install_protocol)] = p.sha(install_protocol)

# Reuse the ordinary central readback readers; do not rerun Native or routing.
native_positives = {}
for label in ('hierarchy-whole2Cu', 'whole4Cu', 'partial2Cu', 'floor-2Cu', 'floor-4Cu', 'alias2Cu'):
    revision = '001'
    base = ROOT/'.runs'/('runtime042-ordinary-'+label+'-'+revision)
    protocol = base/'protocol.json'; execution_path = base/'execution.json'
    plan = f.read_json(protocol); completed = f.read_json(execution_path)
    assert completed['controls_passed'] is True and completed['workflow_delivered'] is True
    assert completed['error'] is None and completed['protocol_sha256'] == p.sha(protocol)
    assert max(completed['complete_wall_seconds'], completed['complete_full_CPU_seconds']) <= 240
    process = completed['process']
    assert process['status'] == 'success' and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
    assert plan['runtime'] == str(runtime) and plan['runtime_manifest_sha256'] == manifest_pin
    assert plan['source_head'] == HEAD
    assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py') == plan['driver_sha256']
    assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py') == plan['enclosure_sha256']
    assert p.sha(base/'settings.json') == plan['settings_sha256']
    source = h.real_path(plan['source'])
    assert pc.inventory(source.parent) == plan['source_hashes']
    if label == 'alias2Cu':
        assert source == alias_board and plan['source_hashes'] == alias_fixture['source_hashes']
        assert plan['settings'] == alias_fixture['settings']
        assert plan['expected_counts'] == [0, 0, 0, 0] and plan['expected_protected_count'] == 4
    output = runtime/'.runs'/('ordinary-'+label+'-'+revision)
    assert plan['output'] == str(output)
    child_path = output/'result.json'
    assert completed['child_receipt'] == str(child_path) and completed['child_sha256'] == p.sha(child_path)
    child = f.read_json(child_path)
    assert child['workflow_delivered'] is True and child['method'] == 'route'
    assert child['tools'] == tools and child['source'] == str(source)
    assert child['source_hashes'] == plan['source_hashes'] and child['settings'] == plan['settings']
    work = h.real_path(child['workspace']); assert work.parent == output
    assert [row['stage'] for row in child['processes']] == ['preview', 'route', 'review', 'choice', 'export', 'verify_export']
    for row in child['processes']:
        observed = row['process']; stage = row['stage']
        assert observed['exit_code'] == 0 and observed['cancel_requested'] is False and observed['log_truncated'] is False
        assert p.sha(output/(stage+'.log')) == row['log_sha256']
    route_path = work/'route/result.json'; export_path = work/'export/export.json'
    with p.validation_readback_session():
        route_current = p.check_result(route_path); export_current = ex.check_export(export_path)
    assert route_current['current'] is True and export_current['current'] is True
    route = f.read_json(route_path); exported = f.read_json(export_path)
    assert route['accepted'] is True and exported['export_accepted'] is True
    assert route['source_hashes'] == exported['source_hashes'] == plan['source_hashes']
    assert route['candidate_sha256'] == exported['candidate_sha256'] == child['candidate_sha256']
    assert route['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
    counts = [route['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')]
    assert counts == [exported['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')]
    assert counts == completed['Native_counts']
    if plan['expected_counts'] is None:
        assert plan['warning_policy'] == 'retain_all_native_findings' and counts[:2] == [0, 0]
        assert counts[3] == plan['expected_exclusions']
    else:
        assert counts == plan['expected_counts']
    assert completed['protected_count'] == plan['expected_protected_count']
    for q in (protocol, execution_path, child_path, route_path, export_path): prerequisites[str(q)] = p.sha(q)
    native_positives[label] = dict(protocol=str(protocol), protocol_sha256=p.sha(protocol),
        execution=str(execution_path), execution_sha256=p.sha(execution_path),
        child_receipt=str(child_path), child_sha256=p.sha(child_path),
        source=str(source), source_hashes=plan['source_hashes'],
        candidate_sha256=route['candidate_sha256'], native=route['native'],
        protected_count=completed['protected_count'], route_current=True, export_current=True,
        scope='Fresh current042 Native prerequisite only; not actual GUI qualification.')

invalid_base = ROOT/'.runs/runtime042-ordinary-native-invalid-001'
invalid_protocol = invalid_base/'protocol.json'
invalid_receipt = invalid_base/'enclosure/result.json'
invalid_plan = f.read_json(invalid_protocol); invalid_run = f.read_json(invalid_receipt)
assert invalid_plan['kind'] == 'runtime042-ordinary-Native-invalid-controls-v1'
assert invalid_plan['runtime'] == str(runtime) and invalid_plan['source_head'] == HEAD
assert invalid_plan['runtime_manifest_sha256'] == manifest_pin and invalid_plan['tools'] == tools
assert invalid_plan['pass_key'] == 'control_passed'
assert invalid_run['passed'] is True and invalid_run['status'] == 'completed'
assert invalid_run['accepted'] is False and invalid_run['production_admitted'] is False
assert invalid_run['protocol_sha256'] == p.sha(invalid_protocol)
invalid_process = invalid_run['process']
assert invalid_process['status'] == 'success' and invalid_process['exit_code'] == 0
assert invalid_process['cleanup_complete'] is True and invalid_process['log_truncated'] is False
invalid_output = runtime/'.runs/native7-comparison-control-runtime042-invalid-001'
assert invalid_plan['output'] == str(invalid_output)
invalid_child = invalid_output/'result.json'
assert invalid_run['child_receipt'] == str(invalid_child) and invalid_run['child_sha256'] == p.sha(invalid_child)
invalid_data = f.read_json(invalid_child)
assert invalid_data['control_passed'] is True and invalid_data['status'] == 'completed'
assert invalid_data['accepted'] is False and invalid_data['production_admitted'] is False
assert f.evidence_inventory(invalid_output) == invalid_run['completed_evidence']
assert invalid_run['material_roots'] == [] and invalid_run['completed_material_roots'] == {}
assert invalid_plan['source'] == native_positives['partial2Cu']['source']
assert invalid_plan['source_hashes'] == native_positives['partial2Cu']['source_hashes']
assert pc.inventory(h.real_path(invalid_plan['source']).parent) == invalid_plan['source_hashes']
invalid_controller = h.real_path(invalid_plan['controller'])
assert invalid_controller.parent == runtime/'.runs'
assert p.sha(invalid_controller) == invalid_plan['controller_sha256'] == invalid_plan['helper_sha256']
assert p.sha(ROOT/'.runs/enclose-native7-independent-control-004.py') == invalid_plan['enclosure_sha256']
for name, digest in invalid_plan['required_runtime_module_sha256'].items(): assert p.sha(runtime/name) == digest
for name, digest in invalid_plan['prerequisite_files'].items():
    assert p.sha(ROOT/name) == digest
    prerequisites[str(ROOT/name)] = digest
for q in (invalid_protocol, invalid_receipt, invalid_child, invalid_controller): prerequisites[str(q)] = p.sha(q)
invalid_required = dict(protocol=str(invalid_protocol), protocol_sha256=p.sha(invalid_protocol),
    receipt=str(invalid_receipt), receipt_sha256=p.sha(invalid_receipt),
    child_receipt=str(invalid_child), child_sha256=p.sha(invalid_child),
    scope='Actual existing004 invalid-control pass with source/runtime/material binding; not actual GUI qualification.')

references = {
    'partial': (ROOT/'.runs/runtime033-ordinary-partial2Cu-001/protocol.json',
        'e542752678a3005a20f06ea2833673c8c9ff01f5b4d99b4ba1de7cecdd7003dc'),
    'repair': (ROOT/'.runs/runtime033-interf-current-comparison-001/population.json',
        '8ae47cf2d28bfdd63a349364e9c814fb60a0d36d99d11c80dc1658bbcc66b33e'),
    'hierarchy': (ROOT/'.runs/hierarchy-native-controls-002/protocol.json',
        '29d2e45a6c90e01d301ba5de1f4ff3218aea535145fec0a908fa9ebe58212851'),
    'four_copper': (ROOT/'.runs/runtime033-ordinary-whole4Cu-001/protocol.json',
        '6c991bd99927d03bb9a1170bf27a729cc97616d46ee6e99151ab26ca6a7cc84c'),
}
sources = {}
for label, (path, pin) in references.items():
    assert p.sha(path) == pin
    data = f.read_json(path); board = h.real_path(data['source']); hashes = data['source_hashes']
    assert pc.inventory(board.parent) == hashes
    sources[label] = dict(board=board, hashes=hashes, protocol=str(path), protocol_sha256=pin)
sources['alias'] = dict(board=alias_board, hashes=alias_fixture['source_hashes'],
    protocol=str(alias_preparation), protocol_sha256=alias_preparation_sha)
partial = sources['partial']; repair = sources['repair']; four = sources['four_copper']
assert partial['board'] == ROOT/'.runs/task-copper-fixed-alias-native-004/source/owned1007-transport.kicad_pcb'
assert partial['hashes'][partial['board'].name] == '62cb74bf329f3eb259b595881a24ef2ac320b930ca738f732461ca38831f0128'
assert four['board'] == ROOT/'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'
assert four['hashes'][four['board'].name] == '1fe544f2ace54e74bb48e88633ae6688a48ba32dee33d1737c93a2fe9dca883e'
assert repair['board'] == ROOT/'.data/boards/kicad-interf-u/interf_u.kicad_pcb'
assert len(repair['hashes']) == 25 and repair['hashes'][repair['board'].name] == 'a740ce7fde77ab6af191e23ece21e57d36bb3c29325879248520dcd9ab47b57e'
assert shutil.disk_usage(ROOT).free > 2*1024**3
session = runtime/'.runs/gui-session081'; launcher = runtime/'.runs/gui-launcher081'
assert h.real_path(session, existing=False) == session and h.real_path(launcher, existing=False) == launcher
assert not os.path.lexists(session) and not os.path.lexists(launcher)
session.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, session)
for label in ('project', 'inspection'):
    shutil.copytree(partial['board'].parent, session/label)
    assert pc.inventory(session/label) == partial['hashes']
(session/'jobs').mkdir(mode=0o700)
hierarchy = sources['hierarchy']; shutil.copytree(hierarchy['board'].parent, session/'hierarchy-project')
assert pc.inventory(session/'hierarchy-project') == hierarchy['hashes']
alias = sources['alias']
for label in ('alias-project', 'alias-inspection'):
    shutil.copytree(alias['board'].parent, session/label)
    assert pc.inventory(session/label) == alias['hashes']
alias_settings = pref.validate(alias_fixture['settings'])
assert alias_settings == pref.validate(dict(pref.DEFAULTS, scope='partial_completion', seconds=90))
p.save_json(session/'alias-route-settings.json', alias_settings)
alias_required = dict(role='ordinary_alias_positive', method='route',
    source=str(session/'alias-project'/alias['board'].name), source_hashes=alias['hashes'],
    original_source=str(alias['board']),
    inspection=str(session/'alias-inspection'/alias['board'].with_suffix('.kicad_pro').name),
    settings=alias_settings, settings_path=str(session/'alias-route-settings.json'),
    settings_sha256=p.sha(session/'alias-route-settings.json'), output_parent=str(session/'jobs'),
    fixture_preparation=str(alias_preparation), fixture_preparation_sha256=alias_preparation_sha,
    current_Native_prerequisite=native_positives['alias2Cu'],
    required_observation='Separate fresh GUI alias-source Route/review/fresh Native export/checked KiCad opening and inspection; '
        'same-load display identity and all four original protected routes remain mandatory. No source rename or type/mask/class widening.',
    actual_GUI_qualified=False)
settings = pref.validate(dict(pref.DEFAULTS, scope='partial_completion', seconds=90))
p.save_json(session/'route-settings.json', settings)
controls = session/'recovery-controls-001'; controls.mkdir(mode=0o700)
recovery = {}
for label, source, seconds, expected in (
        ('repair', repair, 420, 'fresh validated repair or truthful refusal; no assumed completion'),
        ('no-repair', partial, 90, 'fresh validated incumbent; no repair if unnecessary'),
        ('unsupported4Cu', four, 90, 'GUI refusal before workspace or worker creation')):
    directory = controls/label; directory.mkdir(mode=0o700)
    shutil.copytree(source['board'].parent, directory/'project')
    assert pc.inventory(directory/'project') == source['hashes']
    chosen = pref.validate(dict(pref.DEFAULTS, scope='whole_board_unlocked_routing', seconds=seconds))
    gui.check_thermal_settings(chosen)
    p.save_json(directory/'route-settings.json', chosen)
    recovery[label] = dict(source=str(directory/'project'/source['board'].name),
        original_source=str(source['board']), source_hashes=source['hashes'],
        source_protocol=source['protocol'], source_protocol_sha256=source['protocol_sha256'],
        method='recover', settings=chosen, settings_path=str(directory/'route-settings.json'),
        settings_sha256=p.sha(directory/'route-settings.json'), output_parent=str(session/'jobs'),
        whole_method_seconds=seconds, additional_export_seconds=gui.export_validation_seconds(seconds),
        required_observation=expected, actual_GUI_qualified=False)
required = dict(schema=1, state='PREPARED_ONLY_NOT_EXECUTED', source_head=HEAD,
    runtime_manifest_sha256=manifest_pin, ordinary_method='route', ordinary_settings=settings,
    fixture_identity_prerequisite=fixture_identity,
    required_separate_current_Native_gates=required_current_Native_gates,
    current_Native_prerequisites=native_positives, invalid_required=invalid_required,
    alias_required=alias_required,
    current_Native_qualification_provided_by_preparation=False,
    ordinary_required_roles=['positive', 'high_budget', 'source_control', 'settings_control',
                             'export_control', 'cancel', 'reject', 'alias_positive'],
    recovery=recovery, recovery_required_roles=['repair', 'no-repair', 'incompatible_settings_refusal',
        'unsupported4Cu_refusal_before_workspace', 'cancel_with_incumbent_retained'],
    ordinary_cancel=dict(method='route', source=recovery['repair']['source'],
        settings=pref.validate(dict(pref.DEFAULTS, seconds=90)),
        scope='Reuse the original Interf copy for an observable ordinary engine interval; no source mutation.'),
    recovery_settings_refusal_examples=[dict(scope='partial_completion'), dict(profile='tuned'),
        dict(adapter='none'), dict(layers=['F.Cu']), dict(scoring_preference='via_low'), dict(seconds=89)],
    recovery_cancel_scope='Use a fresh recovery job. Observe its saved incumbent receipt and an owned active '
        'repair/final-validation process before Cancel, then retain that exact incumbent, actual process/journal '
        'cleanup, rejected/cancelled parent and absence of accepted export. No all-phase or SIGINT-only claim.',
    preserved_boundaries='Exact source/protected/rule/fullSCH and own fresh Native proof; explicit review intent; '
        'no stale/cancel/invalid fallback or electrical claim. Recover budgets cover the whole method; '
        'export remains separate. Actual observed cancellation phase only; forced queued race not presumed.',
    repair_source_rights=f.read_json(references['repair'][0])['source_rights'],
    owned_source_rights='Original project-owned fixtures; canonical/recovery sources retain frozen033 bytes; alias source retains exact frozen fixture-preparation bytes.',
    actual_GUI_qualified=False, Native_qualified=False, project_complete=False)
p.save_json(controls/'protocol-required-001.json', required)
env = {key:value for key,value in os.environ.items()
       if key not in ('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN')}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
process = run([*f.SANDBOX, str(runtime/'.venv/bin/python'), '-B', str(runtime/'scripts/install_gui.py'),
    '--output', str(launcher)], cwd=session, env=env, log=session/'prepare-launcher.log', timeout=30,
    max_log_bytes=512*1024, max_workdir_bytes=128*1024**2, max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json', process)
assert process['status'] == 'success' and process['exit_code'] == 0
assert process['cleanup_complete'] is True and process['log_truncated'] is False
assert h.owned_destination(owner) == session and p.sha(manifest) == manifest_pin and p.tool_manifest() == tools
for source in sources.values(): assert pc.inventory(source['board'].parent) == source['hashes']
for path, pin in prerequisites.items(): assert p.sha(Path(path)) == pin
for path, pin in references.values(): assert p.sha(path) == pin
assert p.sha(identity_receipt) == identity_sha and p.sha(TEMPLATE) == TEMPLATE_SHA
record = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=HEAD, runtime_manifest_sha256=manifest_pin, tools=tools,
    template=dict(path=str(TEMPLATE), sha256=TEMPLATE_SHA),
    fixture_identity_prerequisite=fixture_identity,
    required_separate_current_Native_gates=required_current_Native_gates,
    current_Native_prerequisites=native_positives, invalid_required=invalid_required,
    alias_required=alias_required,
    current_Native_qualification_provided_by_preparation=False,
    hierarchy_source=str(session/'hierarchy-project'/hierarchy['board'].name), hierarchy_source_hashes=hierarchy['hashes'], hierarchy_role='FreshGUI route/review/freshNative export after ordinary protected controls; no new family/comparisonclaim',
    source=str(session/'project'/partial['board'].name), source_hashes=partial['hashes'],
    inspection=str(session/'inspection'/partial['board'].with_suffix('.kicad_pro').name),
    settings=settings, settings_path=str(session/'route-settings.json'),
    settings_sha256=p.sha(session/'route-settings.json'), jobs=str(session/'jobs'),
    launcher=str(launcher/'Launch Autorouter.command'), prerequisites_sha256=prerequisites,
    recovery_protocol=str(controls/'protocol-required-001.json'),
    recovery_protocol_sha256=p.sha(controls/'protocol-required-001.json'),
    preparation_wall_seconds_before_publication=time.monotonic()-START,
    actual_GUI_qualified=False, Native_qualified=False, project_complete=False,
    scope='Prepared fresh042/081 ordinary partial90, separate owned source-all alias partial90 inspection role and experimental recovery fixtures only. '
        'All inputs are original source copies, never routed candidates. Historical037/077,033/074 and034/075 unchanged. '
        'GUI/native/no-repair/invalid/cancel qualification and measured complete exit costs remain required.')
p.save_json(session/'prepared-state.json', record)
print(json.dumps(record))
