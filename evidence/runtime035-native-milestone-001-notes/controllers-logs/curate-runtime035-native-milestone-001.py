"""PREPARED ONLY: retain completed035 Native/install evidence after lead review.

Run with runtime035/.venv/bin/python -B. No Native, GUI, routing or test is
launched. Existing030 retention and034 proof readers are reused; all candidate
proof belongs to035. Unique new text is estimated before any packet is written.
"""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-035/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from autorouter import review_export as ex, local_settings as local

HEAD = '7edc7229ea905e6734bf6cec8ff926a92e6a8613'
MANIFEST = '8f0c455d7db2beb64e23283081fe788cfc26ee4d49cd95c8fd152b8e45ccb677'
notes = ROOT / 'evidence/runtime035-native-milestone-001-notes'
packet = ROOT / 'evidence/runtime035-native-milestone-001.json'
assert not notes.exists() and not packet.exists() and p.c.ROOT == runtime
refs, files, material, queued = {}, [], [], []
total = 0
references = []
for name, pin in (
        ('runtime034-ordinary-install-001', 'a72eeb6196326003182ee144630b6e774a00963a3870bd42c835a5755c3f4aee'),
        ('runtime034-native-invalid-001', '59be6a26b8c9f617efaa7a2e776ebf5cbb3c45c222bbe2628aa9e97e2dfad3e3')):
    path = ROOT / ('evidence/' + name + '.json')
    assert p.sha(path) == pin
    previous = f.read_json(path); index = ROOT / previous['files_index']['path']
    assert p.sha(index) == previous['files_index']['sha256']
    rows = f.read_json(index)
    for row in rows['files'] + rows['material']:
        target = row.get('path', row.get('retained'))
        assert (ROOT / target).resolve().is_relative_to(ROOT / 'evidence')
        refs.setdefault(row['sha256'], target)
    references.append(dict(path=str(path.relative_to(ROOT)), sha256=pin,
        files_index=previous['files_index'], scope='Exact-byte deduplication only; no inherited034 qualification.'))
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
helper_pin = p.sha(helper)
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('retain', 'tree', 'cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))
shared_retain = retain
# Queue the unchanged tree/retain operations so the shared cap cannot fail only
# after copying a partial packet. The shared retain still enforces the same cap.
def retain(path, name):
    queued.append((Path(path), Path(name)))

manifest = runtime / 'runtime-distribution.json'
assert p.sha(manifest) == MANIFEST
runtime_data = f.read_json(manifest)
assert runtime_data['native_version'] == '10.0.7' and runtime_data['build_source']['git_head'] == HEAD
assert len(runtime_data['immutable_files_sha256']) == 51
for name, pin in runtime_data['immutable_files_sha256'].items():
    assert p.sha(runtime / name) == pin
assert runtime_data['immutable_files_sha256']['autorouter/gui.py'] == '93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
assert runtime_data['immutable_files_sha256']['autorouter/pipeline.py'] == '8a0276c178649ff76383865e125c63803a71a15b144ac29905a0c072c67480af'
tools = p.tool_manifest()
assert tools['git_head'] == HEAD and tools['kicad'] == '10.0.7'
assert tools['source_provenance']['manifest_sha256'] == MANIFEST
pins = [(manifest, MANIFEST), (helper, helper_pin)]
packets, pairs, originals, complete_material = [], [], [], []
for name in ('full-integration-178', 'install-distribution-native-008'):
    base = ROOT / '.runs' / name; execution = f.read_json(base / 'execution.json')
    assert execution['passed'] is True
    process = execution['process']
    assert process['status'] == 'success' and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
    pins.extend((path, p.sha(path)) for path in (base / 'protocol.json', base / 'execution.json'))
    if name == 'full-integration-178':
        assert execution['sources_unchanged'] is True and execution['log_sha256'] == p.sha(base / 'command.log')
        assert execution['controller_sha256'] == p.sha(ROOT / '.runs/run-full-integration-178.py')
        full_plan = f.read_json(base / 'protocol.json')
        for relative, pin in full_plan['source_sha256'].items():
            assert p.sha(ROOT / relative) == pin
            pins.append((ROOT / relative, pin))
        log = (base / 'command.log').read_text()
        assert 'Ran 2200 tests' in log and 'OK (skipped=1)' in log
    else:
        assert execution['source_unchanged'] is True
    tree(base, Path('integration-install') / name)
installation_path = runtime.parent / 'result.json'; installation = f.read_json(installation_path)
installed = f.read_json(ROOT / '.runs/install-distribution-native-008/execution.json')
assert installed['child_receipt'] == str(installation_path) and installed['child_receipt_sha256'] == p.sha(installation_path)
assert installation['passed'] is True and installation['git_head'] == HEAD and installation['native_version'] == '10.0.7'
assert installation['source_provenance']['manifest_sha256'] == MANIFEST
assert installation['selected_source_unchanged'] is True and installation['installed_product_unchanged'] is True
retain(installation_path, Path('installation/result.json'))
for name in ('runtime-distribution.json', 'RUNTIME_README.txt', 'LICENSE'):
    retain(runtime / name, Path('runtime') / name)
smoke = runtime / '.runs/install-native-smoke'; smoke_result = f.read_json(smoke / 'result.json')
assert installation['native_receipt'] == dict(path=str(smoke / 'result.json'), sha256=p.sha(smoke / 'result.json'))
with p.validation_readback_session():
    assert p.check_result(smoke / 'result.json')['current'] is True
packets.append((smoke, smoke_result))
originals.append((Path(smoke_result['source']).parent, smoke_result['source_hashes']))
tree(smoke, Path('installation/native-smoke'))
tree(runtime.parent / 'source-fixture', Path('installation/source-fixture'))
for command in installation['commands']:
    assert p.sha(Path(command['log'])) == command['log_sha256']
    retain(Path(command['log']), Path('installation/logs') / Path(command['log']).name)
binary_git_logs = []
for path in sorted(runtime.parent.glob('source-git-*')):
    assert path.is_file() and not path.is_symlink() and path.suffix in ('.json', '.log')
    raw = io.read_bytes(path, 4 * 1024**2)
    if b'\0' in raw:
        binary_git_logs.append(dict(original=str(path.relative_to(ROOT)), bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(), reason='NUL-delimited Git output remains exact on Mac; text-only public packet excludes it.'))
    else:
        retain(path, Path('installation/source-git') / path.name)

controls = []
for label, attempt, counts, protected in (
        ('whole4Cu', '002', [0, 0, 6, 0], 10), ('partial2Cu', '001', [0, 0, 0, 0], 4)):
    name = 'runtime035-ordinary-' + label + '-' + attempt
    base = ROOT / '.runs' / name; plan = f.read_json(base / 'protocol.json'); output = Path(plan['output'])
    assert plan['kind'] == 'frozen-runtime033-ordinary-workflow'
    assert plan['runtime'] == str(runtime) and plan['runtime_manifest_sha256'] == MANIFEST and plan['source_head'] == HEAD
    assert output == runtime / '.runs' / ('production-' + label + '-delivery-' + attempt)
    assert plan['driver_sha256'] == p.sha(ROOT / 'scripts/qualify_runtime_workflow.py')
    assert plan['enclosure_sha256'] == p.sha(ROOT / '.runs/enclose-runtime030-ordinary-workflow-001.py')
    execution = f.read_json(base / 'execution.json'); child = f.read_json(output / 'result.json')
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True and execution['error'] is None
    assert execution['protocol_sha256'] == p.sha(base / 'protocol.json')
    assert execution['child_receipt'] == str(output / 'result.json') and execution['child_sha256'] == p.sha(output / 'result.json')
    assert execution['process']['status'] == 'success' and execution['process']['exit_code'] == 0
    assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
    assert execution['Native_counts'] == counts and execution['protected_count'] == protected
    assert child['status'] == 'completed' and child['workflow_delivered'] is True
    assert child['source'] == plan['source'] and child['source_hashes'] == plan['source_hashes']
    assert child['driver_sha256'] == plan['driver_sha256'] and child['tools'] == tools
    assert [row['stage'] for row in child['processes']] == ['preview', 'route', 'review', 'choice', 'export', 'verify_export']
    workspace = Path(child['workspace']); assert workspace.parent == output
    route_path, export_path = workspace / 'route/result.json', workspace / 'export/export.json'
    route, export = f.read_json(route_path), f.read_json(export_path)
    assert route['accepted'] is True and export['export_accepted'] is True
    assert route['invariants_unchanged'] is True and export['original_geometry_and_routing_unchanged'] is True
    assert route['schematic_parity'] == export['schematic_parity'] == 'checked by final native DRC'
    assert route['source_hashes'] == export['source_hashes'] == plan['source_hashes']
    assert len(route['protected_route_import']['matches']) == protected
    for report in (route, export):
        assert [report['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == counts
    assert route['candidate_sha256'] == export['candidate_sha256'] == child['candidate_sha256']
    assert child['route_readback']['current'] is True and child['export_readback']['current'] is True
    with p.validation_readback_session():
        assert p.check_result(route_path)['current'] is True
        assert ex.check_export(export_path)['current'] is True
    packets.extend(((route_path.parent, route), (workspace / 'export/validation', export)))
    preview = f.read_json(workspace / 'review/review.json')['preview']; plot = workspace / 'review/plot-work'
    for step in preview['steps']:
        assert step['cwd'] == str(plot)
        process = f.process_check(plot, preview, step['name'], step['argv'])
        pairs.append((plot, f.read_json(plot / (step['name'] + '-input-binding.json')), process))
    originals.append((Path(plan['source']).parent, plan['source_hashes']))
    complete_material.append((output, io.inventory(output, max_bytes=256*1024**2, max_files=8000, max_entries=16000)))
    pins.extend((path, p.sha(path)) for path in (base / 'protocol.json', base / 'execution.json', output / 'result.json', route_path, export_path))
    tree(base, Path('enclosures') / label); tree(output, Path('cases') / label)
    tree(Path(plan['source']).parent, Path('originals') / label)
    for suffix in ('-time.log', '-controller.log'):
        retain(ROOT / '.runs' / (name + suffix), Path('logs') / (name + suffix))
    controls.append(dict(case=label, attempt=attempt, passed=True, complete_cost=cost(ROOT / '.runs' / (name + '-time.log')),
        six_stages=[row['stage'] for row in child['processes']], Native_counts=counts, protected_count=protected,
        source_Native_counts=[route['source_drc'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')],
        source_hashes=plan['source_hashes'], settings=plan['settings'], budgets=plan['budgets'],
        candidate_sha256=child['candidate_sha256'], route_receipt_sha256=p.sha(route_path),
        export_receipt_sha256=p.sha(export_path), output_receipt_sha256=p.sha(output / 'result.json'),
        protocol_sha256=p.sha(base / 'protocol.json'), actual_GUI=False, human_review=False))

base = ROOT / '.runs/runtime035-ordinary-native-invalid-001'
assert p.sha(base / 'protocol.json') == 'dabdf57c288ca987d79aa6572dfc580e8ee28b4e62daf54ec8661c8a1bb6058b'
plan = f.read_json(base / 'protocol.json'); out = Path(plan['output'])
assert out == runtime / '.runs/native7-comparison-control-runtime035-invalid-001'
assert plan['runtime'] == str(runtime) and plan['source_head'] == HEAD and plan['runtime_manifest_sha256'] == MANIFEST
assert plan['kind'] == 'runtime035-ordinary-Native-invalid-controls-v1'
assert p.sha(Path(plan['controller'])) == plan['controller_sha256'] == plan['helper_sha256'] == 'c0c8a8332f912e6ee8476bac47dfd04830226dbeedfb8c815c821c92b8e6cbdf'
assert plan['whole_wall_full_cpu_seconds'] == 180 and plan['route_seconds'] == 90
assert plan['scope'] == 'partial_completion' and plan['profile'] == 'standard'
assert plan['adapter'] == 'both' and plan['scoring_variant'] is None and plan['protected_routes'] == 4
assert plan['tools'] == tools
outer = f.read_json(base / 'enclosure/result.json'); invalid = f.read_json(out / 'result.json')
assert p.sha(out / 'result.json') == 'a6a00e7b4d83bdefa0ea7e663fb0c5f469ce08a6ac01e5f7e5c73b0d910ac050'
assert outer['passed'] is True and outer['status'] == 'completed' and outer['protocol_sha256'] == p.sha(base / 'protocol.json')
assert outer['child_receipt'] == str(out / 'result.json') and outer['child_sha256'] == p.sha(out / 'result.json')
assert outer['process']['status'] == 'success' and outer['process']['exit_code'] == 0
assert outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False
assert max(outer['complete_wall_seconds'], outer['complete_full_CPU_seconds']) < 180
assert invalid['control_passed'] is True and invalid['status'] == 'completed'
assert invalid['accepted'] is invalid['routing_accepted'] is invalid['export_accepted'] is invalid['production_admitted'] is False
assert invalid['source_head'] == HEAD and invalid['runtime_manifest_sha256'] == MANIFEST and invalid['tools'] == tools
assert invalid['protocol_sha256'] == p.sha(base / 'protocol.json')
assert f.evidence_inventory(out) == invalid['evidence_sha256'] == outer['completed_evidence']
assert [row['label'] for row in invalid['cases']] == ['partial-short', 'partial-protected-width']
assert all(row['control_observed'] is True and row['protected_routes'] == 4 and row['accepted'] is False
           and row['routing_accepted'] is False for row in invalid['cases'])
short, width = invalid['cases']
assert short['native']['blocking'] > 0 and 'shorting_items' in {row['type'] for row in short['native']['findings']}
assert width['Native_diagnostic_routing_accepted'] is True and width['mutation']['added_nanometres'] == 1
assert width['rejection'] == 'protected route changed' and width['no_additional_native_after_invariant_refusal'] is True
assert [width['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
query_path = Path(plan['preparation']['tools_query_path']); query = f.read_json(query_path)
assert query_path == base / 'tools-defaults.json' and query['tools'] == tools
assert p.sha(query_path) == plan['preparation']['tools_query_sha256']
assert p.sha(base / 'tools-defaults-process.json') == plan['preparation']['tools_query_process_sha256']
query_process = f.read_json(base / 'tools-defaults-process.json')
assert query_process['status'] == 'success' and query_process['exit_code'] == 0
assert query_process['cleanup_complete'] is True and query_process['log_truncated'] is False
for label in ('whole4Cu', 'partial2Cu'):
    item = plan[label + '_positive']
    for name in ('protocol', 'execution', 'result', 'route', 'export'):
        path = Path(item[name + '_path']); assert p.sha(path) == item[name + '_sha256']
        pins.append((path, item[name + '_sha256']))
for row in invalid['cases']:
    candidate = Path(row['candidate']); validation = candidate.parent.parent
    assert p.sha(candidate) == row['candidate_sha256']
    before = dict(plan['source_hashes']); before[candidate.name] = row['candidate_sha256']
    name = 'final-drc' if row['label'] == 'partial-short' else 'diagnostic-full-drc'
    assert f.check_drc_stage(validation, row, name, candidate, validation / (name + '-input') / candidate.name,
        False, before, schematic_parity=True, sandboxed=False) == row['native']
    if row['label'] == 'partial-short':
        refill = validation / 'refill' / candidate.name
        before[candidate.name] = row['mutation']['pre_native_sha256']
        assert f.check_drc_stage(validation, row, 'refill-drc', refill, refill, True, before,
            schematic_parity=False, sandboxed=False) == p.parse_report(validation / 'refill-drc.json', candidate.name)
    packets.append((validation, row))
pins.extend((path, p.sha(path)) for path in (base / 'protocol.json', base / 'enclosure/result.json', out / 'result.json'))
tree(base, Path('invalid/enclosure-and-preparation')); tree(out, Path('invalid/cases'))

failed_base = ROOT / '.runs/runtime035-ordinary-whole4Cu-001'
failed = f.read_json(failed_base / 'execution.json')
failed_output = runtime / '.runs/production-whole4Cu-delivery-001'
assert failed['controls_passed'] is False and failed['workflow_delivered'] is False and failed['child_sha256'] is None
assert failed['process']['status'] == 'nonzero_exit' and failed['process']['exit_code'] == 1
assert failed['process']['cleanup_complete'] is True and failed['process']['log_truncated'] is False
assert failed_output.is_dir() and not any(failed_output.iterdir())
assert 'FileNotFoundError' in (failed_base / 'enclosure/command.log').read_text()
assert '.runs/runtime035-ordinary-whole4Cu-001/settings.json' in (failed_base / 'enclosure/command.log').read_text()
corrected_whole = f.read_json(ROOT / '.runs/runtime035-ordinary-whole4Cu-002/protocol.json')
assert 'preparatory assertion' in corrected_whole['invocation_correction']
argparse_log = ROOT / '.runs/runtime035-ordinary-native-invalid-001-time.log'
assert 'required: --protocol-sha256' in argparse_log.read_text()
tree(failed_base, Path('failed-invocations/whole001'))
prepared_path = runtime / '.runs/gui-session076/prepared-state.json'; prepared = f.read_json(prepared_path)
assert prepared['source_head'] == HEAD and prepared['runtime_manifest_sha256'] == MANIFEST and prepared['tools'] == tools
assert prepared['actual_GUI_qualified'] is False and prepared['Native_qualified'] is False
for relative in ('prepared-state.json', 'route-settings.json', 'prepare-launcher.log', 'prepare-launcher-process.json',
                 'recovery-controls-001/protocol-required-001.json'):
    retain(prepared_path.parent / relative, Path('GUI076-preparation-only') / relative)
controllers = (
    'run-full-integration-178.py', 'full-suite-local-root-019.py', 'full-integration-178-controller-001.log', 'full-integration-178-time-001.log',
    'run-install-distribution-native-008.py', 'freeze-install-distribution-native-008.py',
    'freeze-install-distribution-native-008-command.log', 'freeze-install-distribution-native-008-time.log',
    'install-distribution-native-008-controller-001.log', 'install-distribution-native-008-time-001.log',
    'freeze-runtime035-ordinary-001.py', 'freeze-runtime035-ordinary-001-command.log', 'freeze-runtime035-ordinary-001-time.log',
    'runtime035-ordinary-whole4Cu-001-controller.log', 'runtime035-ordinary-whole4Cu-001-time.log',
    'enclose-runtime030-ordinary-workflow-001.py', 'enclose-native7-independent-control-004.py',
    'qualify-runtime035-ordinary-native-invalid-001.py', 'freeze-runtime035-ordinary-native-invalid-001.py',
    'freeze-runtime035-ordinary-native-invalid-001-command.log', 'freeze-runtime035-ordinary-native-invalid-001-time.log',
    'runtime035-ordinary-native-invalid-001-controller.log', 'runtime035-ordinary-native-invalid-001-time.log',
    'runtime035-ordinary-native-invalid-001-controller-002.log', 'runtime035-ordinary-native-invalid-001-time-002.log',
    'prepare-runtime035-gui076.py', 'prepare-runtime035-gui076-command.log', 'prepare-runtime035-gui076-time.log',
    'gui-thermal-budget-display-targeted-001.log', 'gui-thermal-budget-display-targeted-001-time.log',
    'gui-thermal-budget-display-targeted-002.log', 'gui-thermal-budget-display-targeted-002-time.log')
for name in controllers:
    retain(ROOT / '.runs' / name, Path('controllers-logs') / name)
retain(ROOT / 'scripts/qualify_runtime_workflow.py', Path('controllers-logs/qualify_runtime_workflow.py'))
retain(ROOT / 'tests/test_gui_thermal_budget_display.py', Path('controllers-logs/test_gui_thermal_budget_display.py'))
retain(helper, Path('controllers-logs') / helper.name)
retain(Path(__file__), Path('controllers-logs') / Path(__file__).name)

# Exact-byte preflight only: same4MiB text read limit and the unchanged shared
# strict<16MiB/<2000 new-file limits, before creation of notes or the packet.
new_payload = {}; queue_pins = []
for path, name in queued:
    raw = io.read_bytes(path, 4 * 1024**2); pin = hashlib.sha256(raw).hexdigest()
    assert b'\0' not in raw; raw.decode('utf-8')
    queue_pins.append((path, name, pin))
    if pin in refs:
        assert p.sha(ROOT / refs[pin]) == pin
    else:
        new_payload.setdefault(pin, len(raw))
assert sum(new_payload.values()) < 16 * 1024**2 and len(new_payload) < 2000
for path, name, pin in queue_pins:
    assert p.sha(path) == pin
    shared_retain(path, name)
assert total == sum(new_payload.values()) and len(files) == len(new_payload)
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
    raw_binary_git_logs_not_copied=binary_git_logs))
record = dict(schema=1, kind='runtime035-captured-budget-display-fix-full-install-ordinary-and-invalid-native-milestone',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=True, project_complete=False,
    accepted=False, production_admitted=False, actual_GUI=False, human_review=False,
    source_head=HEAD, runtime_manifest_sha256=MANIFEST, runtime_modules=46, runtime_immutable_files=51,
    full178=dict(passed=True, tests=2200, skips=1, complete_cost=cost(ROOT / '.runs/full-integration-178-time-001.log')),
    installation=dict(passed=True, complete_cost=cost(ROOT / '.runs/install-distribution-native-008-time-001.log'),
        scope=installation['qualification'], command_cpu_scope=installation['command_cpu_scope']),
    source_regression=dict(scope='Actual controlled user-visible recovery summary regression, not actual GUI qualification.',
        before_fix=dict(passed=False, tests=2, failed_subtests=3, complete_cost=cost(ROOT / '.runs/gui-thermal-budget-display-targeted-001-time.log')),
        after_fix=dict(passed=True, tests=38, complete_cost=cost(ROOT / '.runs/gui-thermal-budget-display-targeted-002-time.log'))),
    ordinary_controls=controls,
    invalid_controls=dict(passed=True, complete_cost=cost(ROOT / '.runs/runtime035-ordinary-native-invalid-001-time-002.log'),
        protocol_sha256=p.sha(base / 'protocol.json'), result_sha256=p.sha(out / 'result.json'),
        cases=[dict(label=row['label'], control_observed=row['control_observed'],
            Native_counts=[row['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')],
            rejection=row['rejection'], protected_routes=row['protected_routes'],
            Native_diagnostic_routing_accepted=row.get('Native_diagnostic_routing_accepted')) for row in invalid['cases']]),
    preparation_costs=dict(installation_freeze=cost(ROOT / '.runs/freeze-install-distribution-native-008-time.log'),
        ordinary_freeze=cost(ROOT / '.runs/freeze-runtime035-ordinary-001-time.log'),
        invalid_freeze_with_metadata_query=cost(ROOT / '.runs/freeze-runtime035-ordinary-native-invalid-001-time.log'),
        GUI076_preparation_only=cost(ROOT / '.runs/prepare-runtime035-gui076-time.log')),
    failed_invocations=dict(whole001=dict(complete_cost=cost(ROOT / '.runs/runtime035-ordinary-whole4Cu-001-time.log'),
        before_Native=True, empty_output_preserved=True, reason='Relative settings path resolved under enclosure cwd; no child Route/result.'),
        whole002_preparation=dict(before_Native=True, measured_complete_CPU=None,
            reason=corrected_whole['invocation_correction'], accounting='Authoring/preparatory assertion CPU was not separately measured; unknown is not zero.'),
        invalid_enclosure001=dict(complete_cost=cost(argparse_log), before_enclosure_and_Native=True,
            reason='Required --protocol-sha256 omitted; argparse refused. Corrected invocation002 is a distinct retained event.')),
    implementation='Committed035 presentation-only GUI correction preserves captured recovery method420/export120 text across merged review/choice/export receipts. This packet qualifies full-suite/install and ordinary Native six-stage regressions plus deliberate invalid controls, not actual new GUI or recovery operation.',
    Native_and_original='Own selected10.0.7 source/refill/full-schematic/all-severity/original-rule/semantic/protected proof for each ordinary Route and fresh export. Whole retains6 warnings/10 protected records; partial0 final findings/4 protected. Installer smoke has no supplied schematic and retains its original ignored checks. Deliberate short is Native rejected; locked width+1nm is separately Native-clean but protected invariant rejected. Expected source opens and every source/final warning/exclusion/ignored check remain raw; no electrical or physical approval.',
    historical_kind_labels='Ordinary frozen-runtime033-ordinary-workflow and enclosing current-runtime030-ordinary-CLI are unchanged shared schema/history labels. Actual035 path/source7ed/manifest8f0/tools/candidate and controller pins are mandatory. ROOT documentation checkpoint10be is separate from immutable035 source and is not asserted to equal7ed.',
    GUI_gate='GUI076 source/settings/launcher prepared only, no actual035 GUI run; actual Mac locked was reported and owner asked once. Historical034/033 evidence never qualifies035. GUI recovery display and actual repair/cancel remain new-build gates.',
    accounting='Complete external exit wall and user+sys CPU are retained once for full178/install008/each ordinary attempt/each invalid invocation/freezers/GUI preparation. Nested runner/query/prepublication samples are separate raw observations, not additional sums. Installer command_cpu_seconds covers CLI commands only; its external complete exit includes waited Git observations. Curation, source authoring, AI review and unknown interactive/preparatory costs are additional, not zero. Failed callers are not routing losses or hidden first-attempt successes.',
    source_rights='Project-owned generated geometry/schematic and code retain repository GPL LICENSE. Original official demo project/settings keep separately attributed CC-BY-SA-4.0 provenance through exact034 references. No private boards, local-reference, downloaded tools/apps/engine, venv, pixels, bulk data or new binary material copied.',
    limits='Mac Native/install/correctness qualification only. No actual035 GUI, broader routing-quality/superiority, cleanup/speed, freshOS, relocation, standalone, Windows, human/physical, restoration or formal release claim. Independent AI review is still required; no human review fabricated.',
    backup_scope='Sanitized essential text proof intended for later audited Git checkpoint. Full raw035 and excluded NUL Git logs remain on this Mac outside older full backups. This packet is not a new full artifact backup or restoration test.',
    references=references, retention=dict(shared_helper=str(helper.relative_to(ROOT)), shared_helper_sha256=helper_pin,
        max_new_bytes=16*1024**2, max_new_files=2000, preflight_new_bytes=sum(new_payload.values()),
        preflight_new_files=len(new_payload), raw_binary_git_logs_not_copied=binary_git_logs,
        exclusions='Unchanged shared tree helper omits generated KiCad/engine preferences, caches, tmp and __pycache__; full raw remains local.'),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
# All central/tool/source/material callbacks precede the final shared all-root
# PRL metadata replay. Only writing the already built public record follows it.
assert p.tool_manifest() == tools and p.sha(helper) == helper_pin
for relative, pin in runtime_data['immutable_files_sha256'].items():
    assert p.sha(runtime / relative) == pin
for path, pin in pins: assert p.sha(path) == pin
for folder, hashes in originals: assert p.tree_hash(folder) == hashes
for folder, hashes in complete_material:
    assert io.inventory(folder, max_bytes=256*1024**2, max_files=8000, max_entries=16000) == hashes
assert failed_output.is_dir() and not any(failed_output.iterdir())
assert f.evidence_inventory(out) == invalid['evidence_sha256'] == outer['completed_evidence']
for row in material:
    assert p.sha(ROOT / row['original']) == p.sha(ROOT / row['retained']) == row['sha256']
for row in binary_git_logs: assert p.sha(ROOT / row['original']) == row['sha256']
assert p.sha(notes / 'files.json') == record['files_index']['sha256']
local.check_final_events(packets, p.c.CLI, pairs=pairs)
p.save_json(packet, record)
print(json.dumps(dict(files=len(files), bytes=total, material=len(material), passed=True,
    actual_GUI=False, project_complete=False)))
