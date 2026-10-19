"""Prepare one fresh042 Sonde whole90/export90 development protocol.

PREPARATION ONLY: this file has not frozen or executed a workflow. Run after
full187/install015, all six current042 Native controls and invalid042 complete.
The prerequisite readback block is copied from historical prepare-runtime041-gui080.py;
its GUI/session/launcher preparation statements are not part of this file.
Exact039 Sonde source/settings/rights/bounds remain unchanged. No tuning,
new sources, downloads, source edits, Native execution or publication here.
"""
MANIFEST = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
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
assert manifest_pin == MANIFEST
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

# Reuse the exact previously frozen Sonde problem and unchanged shared driver.
previous_path = ROOT/'.runs/runtime039-ordinary-sonde-whole-001/protocol.json'
assert p.sha(previous_path) == '3d656a6aaac3d289eddd270cd3533c15f29062e8ca13dd47c1faf63af8704894'
previous = f.read_json(previous_path)
source = h.real_path(previous['source'])
assert source == ROOT/'.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb'
assert pc.inventory(source.parent) == previous['source_hashes']
settings = pref.validate(previous['settings'])
assert settings == dict(schema=1, scope='whole_board_unlocked_routing', seconds=90,
    adapter='both', profile='standard', guidance='native', layers='source_all', scoring_preference=None)
assert previous['budgets'] == dict(route=90, export=90)
assert previous['expected_counts'] is None and previous['warning_policy'] == 'retain_all_native_findings'
assert previous['expected_exclusions'] == 0 and previous['expected_protected_count'] == 0
assert previous['rights']['license'] == 'CC-BY-SA-4.0'
for notice in previous['rights']['notices']:
    path = h.real_path(ROOT/notice['path'])
    assert path.is_relative_to(source.parent) and path.stat().st_size == notice['bytes']
    assert p.sha(path) == notice['sha256']
assert previous['bounds'] == dict(route_seconds=90, export_seconds=90, complete_wall_seconds=240,
    complete_full_CPU_seconds=240, driver_stage_reserve_ceiling_seconds=225,
    outer_watchdog_seconds=255, max_log_bytes=524288,
    sampled_max_group_rss_bytes=4294967296, sampled_max_enclosure_workdir_bytes=536870912,
    resource_poll_seconds=0.25, resource_limits_OS_enforced=False)
assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py') == previous['driver_sha256'] == '0b1a3bc61e576d6475a4c922a7727b7831ccf28f3e0a9d2d80b557e3c1964034'
assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py') == previous['enclosure_sha256'] == '69d87dee41f94fe9e479e505093914325ed653cbb0cd58c9545272afefc1d59c'
base = ROOT/'.runs/runtime042-ordinary-sonde-whole-001'
output = runtime/'.runs/ordinary-sonde-whole-001'
assert not os.path.lexists(base) and not os.path.lexists(output)
assert shutil.disk_usage(ROOT).free > 2*1024**3
for path, pin in prerequisites.items(): assert p.sha(Path(path)) == pin
assert p.sha(ROOT/'.runs/prepare-runtime041-gui080.py') == '8a4b1d8aa235e3aa365be0177779416981d009a71f127e1b7372f8ef107dd9bb'
assert p.sha(previous_path) == '3d656a6aaac3d289eddd270cd3533c15f29062e8ca13dd47c1faf63af8704894'
assert p.sha(manifest) == MANIFEST and p.tool_manifest() == tools
assert pc.inventory(source.parent) == previous['source_hashes']
base.mkdir(mode=0o700)
p.save_json(base/'settings.json', settings)
plan = dict(previous)
plan.update(kind='runtime042-six-stage-exposed-development-breadth-regression',
    runtime=str(runtime), runtime_manifest_sha256=MANIFEST, source_head=HEAD,
    source=str(source), output=str(output), settings=settings,
    settings_sha256=p.sha(base/'settings.json'), expected_counts=None,
    warning_policy='retain_all_native_findings', expected_exclusions=0, expected_protected_count=0,
    prerequisite_receipts=[dict(path=str(Path(path).relative_to(ROOT)),
        bytes=Path(path).stat().st_size, sha256=pin) for path,pin in prerequisites.items()],
    unchanged_source_protocol=dict(path=str(previous_path), sha256=p.sha(previous_path),
        scope='Exact039 Sonde source, settings, original rules, rights/notices and bounds reused; prior failure remains unchanged.'),
    current_Native_prerequisites=native_positives, invalid_required=invalid_required,
    preparation=dict(freezer_sha256=p.sha(Path(__file__)),
        prerequisite_reader_template=str(ROOT/'.runs/prepare-runtime041-gui080.py'),
        prerequisite_reader_template_sha256='8a4b1d8aa235e3aa365be0177779416981d009a71f127e1b7372f8ef107dd9bb',
        prerequisite_reader_template_scope='Historical041 algorithm source only; all current042 source/manifest/Native/readback prerequisites are checked above, not inherited from this template.',
        wall_seconds_before_publication=time.monotonic()-START,
        actual_Native_executed=False, actual_GUI=False),
    historical_count_scope='Pinned10.0.0 historical whole B1 only; warnings/counts may change. Require own current042 final Route/export counts, opens=blocking=exclusions=0, all warnings retained. Never tune/retry to force this lead.',
    task_policy='Whole-board unlocked source routing removed; original source/project/rules/footprints/nets/zone intent/fields/model declarations remain immutable. Protected0 is not a protection claim.',
    scope='One unchanged-source current042 standard/B1 six-stage CLI exposed development attempt after the reporting-only parity-declaration correction. Native validation/admission, original rules/floors, protection, cancellation and all prior support restrictions remain unchanged; historical alias corrections are not new042 gains. No adjustment, tuning or restart after outcomes. Own fullSCH/final Native/source/original/floor/via/pour/material/process proof and complete240wall/fullCPU costs required. Not executed at freeze; no GUI, holdout, independent-family, speed, quality, comparison or broader completion claim. Preserve every failure and all warnings/exclusions; refusal is a result, not a predicted pass.')
p.save_json(base/'protocol.json', plan)
print(json.dumps(dict(protocol=str(base/'protocol.json'), sha256=p.sha(base/'protocol.json'),
    output=str(output), source=str(source), expected_counts=None,
    expected_exclusions=0, expected_protected_count=0, Native_executed=False)))
