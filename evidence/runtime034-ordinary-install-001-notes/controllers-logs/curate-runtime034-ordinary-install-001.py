"""Prepare the bounded text packet for completed runtime034 ordinary controls.

This controller copies existing proof; it never runs a Native check or a job.
"""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

notes = ROOT / 'evidence/runtime034-ordinary-install-001-notes'
destination = ROOT / 'evidence/runtime034-ordinary-install-001.json'
assert not notes.exists() and not destination.exists()
refs, files, material = {}, [], []
total = 0
previous = ROOT / 'evidence/runtime033-ordinary-install-001.json'
prior = f.read_json(previous)
index = ROOT / prior['files_index']['path']
assert p.sha(index) == prior['files_index']['sha256']
for row in f.read_json(index)['files'] + f.read_json(index)['material']:
    refs.setdefault(row['sha256'], row.get('path', row.get('retained')))
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('retain', 'tree', 'cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))

head = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
runtime = ROOT / '.runs/runtime-directory-034/runtime'
manifest = runtime / 'runtime-distribution.json'
manifest_sha = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
assert p.sha(manifest) == manifest_sha
distribution = f.read_json(manifest)
assert distribution['native_version'] == '10.0.7' and distribution['build_source']['git_head'] == head
assert len(distribution['immutable_files_sha256']) == 51
for name in ('full-integration-177', 'install-distribution-native-007'):
    base = ROOT / '.runs' / name
    execution = f.read_json(base / 'execution.json')
    assert execution['passed'] is True
    assert execution['process']['status'] == 'success' and execution['process']['exit_code'] == 0
    assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
    if name == 'full-integration-177':
        assert execution['sources_unchanged'] is True
        assert execution['log_sha256'] == p.sha(base / 'command.log')
        assert execution['controller_sha256'] == p.sha(ROOT / '.runs/run-full-integration-177.py')
    else:
        assert execution['source_unchanged'] is True
    tree(base, Path('integration-install') / name)
install_path = runtime.parent / 'result.json'
installation = f.read_json(install_path)
install_execution = f.read_json(ROOT / '.runs/install-distribution-native-007/execution.json')
assert install_execution['child_receipt'] == str(install_path)
assert install_execution['child_receipt_sha256'] == p.sha(install_path)
assert installation['passed'] is True and installation['git_head'] == head
assert installation['native_version'] == '10.0.7'
assert installation['source_provenance']['manifest_sha256'] == manifest_sha
assert installation['selected_source_unchanged'] is True and installation['installed_product_unchanged'] is True
retain(install_path, Path('installation/result.json'))
for name in ('runtime-distribution.json', 'RUNTIME_README.txt', 'LICENSE'):
    retain(runtime / name, Path('runtime') / name)
tree(runtime / '.runs/install-native-smoke', Path('installation/native-smoke'))
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
                                    sha256=hashlib.sha256(raw).hexdigest(),
                                    reason='NUL-delimited Git output; retained unchanged on Mac, not copied into text-only public packet.'))
    else:
        retain(path, Path('installation/source-git') / path.name)

controls = []
for label, counts, protected in (('whole4Cu', [0, 0, 6, 0], 10), ('partial2Cu', [0, 0, 0, 0], 4)):
    name = 'runtime034-ordinary-' + label + '-001'
    base = ROOT / '.runs' / name
    plan = f.read_json(base / 'protocol.json')
    output = Path(plan['output'])
    assert plan['runtime'] == str(runtime) and plan['runtime_manifest_sha256'] == manifest_sha
    assert plan['source_head'] == head and output == runtime / '.runs' / ('production-' + label + '-delivery-001')
    assert plan['driver_sha256'] == p.sha(ROOT / 'scripts/qualify_runtime_workflow.py')
    assert plan['enclosure_sha256'] == p.sha(ROOT / '.runs/enclose-runtime030-ordinary-workflow-001.py')
    execution = f.read_json(base / 'execution.json')
    child = f.read_json(output / 'result.json')
    assert execution['controls_passed'] is True and execution['workflow_delivered'] is True
    assert execution['protocol_sha256'] == p.sha(base / 'protocol.json')
    assert execution['child_receipt'] == str(output / 'result.json') and execution['child_sha256'] == p.sha(output / 'result.json')
    assert execution['process']['exit_code'] == 0 and execution['process']['cleanup_complete'] is True
    assert execution['process']['log_truncated'] is False and execution['Native_counts'] == counts
    assert execution['protected_count'] == protected and child['status'] == 'completed' and child['workflow_delivered'] is True
    assert child['source'] == plan['source'] and child['source_hashes'] == plan['source_hashes']
    assert child['driver_sha256'] == plan['driver_sha256']
    assert child['tools']['git_head'] == head and child['tools']['source_provenance']['manifest_sha256'] == manifest_sha
    assert [row['stage'] for row in child['processes']] == ['preview', 'route', 'review', 'choice', 'export', 'verify_export']
    workspace = Path(child['workspace'])
    assert workspace.parent == output
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
    tree(base, Path('enclosures') / label)
    tree(output, Path('cases') / label)
    for suffix in ('-time.log', '-controller.log'):
        retain(ROOT / '.runs' / (name + suffix), Path('logs') / (name + suffix))
    controls.append(dict(case=label, passed=True, six_stages=[row['stage'] for row in child['processes']],
                         complete_cost=cost(ROOT / '.runs' / (name + '-time.log')),
                         Native_counts=counts, protected_count=protected, source_hashes=plan['source_hashes'],
                         source_Native_counts=[route['source_drc'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')],
                         settings=plan['settings'], budgets=plan['budgets'], candidate_sha256=child['candidate_sha256'],
                         route_receipt_sha256=p.sha(route_path), export_receipt_sha256=p.sha(export_path),
                         output_receipt_sha256=p.sha(output / 'result.json'), protocol_sha256=p.sha(base / 'protocol.json'),
                         actual_GUI=False, human_review=False))

controllers = ('run-full-integration-177.py', 'full-suite-local-root-019.py',
               'full-integration-177-time.log', 'full-integration-177-command.log',
               'run-install-distribution-native-007.py', 'freeze-install-distribution-native-007.py',
               'freeze-install-distribution-native-007-001.log', 'freeze-install-distribution-native-007-001-time.log',
               'install-distribution-native-007-time-001.log', 'install-distribution-native-007-controller-001.log',
               'freeze-runtime034-ordinary-001.py', 'freeze-runtime034-ordinary-001-controller.log',
               'freeze-runtime034-ordinary-001-time.log', 'enclose-runtime030-ordinary-workflow-001.py')
for name in controllers:
    retain(ROOT / '.runs' / name, Path('controllers-logs') / name)
retain(ROOT / 'scripts/qualify_runtime_workflow.py', Path('controllers-logs/qualify_runtime_workflow.py'))
retain(helper, Path('controllers-logs') / helper.name)
retain(Path(__file__), Path('controllers-logs') / Path(__file__).name)
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material, raw_binary_git_logs_not_copied=binary_git_logs))
record = dict(
    schema=1, kind='runtime034-gui-thermal-source-full-install-and-ordinary-six-stage-native-milestone',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), project_complete=False, accepted=False,
    actual_GUI=False, human_review=False, source_head=head, runtime_manifest_sha256=manifest_sha,
    runtime_modules=46, runtime_immutable_files=51,
    full177=dict(passed=True, tests=2198, skips=1, complete_cost=cost(ROOT / '.runs/full-integration-177-time.log'),
                 scope='Frozen full177 protocol retains exact implementation, tests, administration source pins, process and complete test log.'),
    installation=dict(passed=True, complete_cost=cost(ROOT / '.runs/install-distribution-native-007-time-001.log'),
                      scope='Fresh curated runtime/copied venv/doctor/actual Native Route/check on owned smoke fixture without supplied schematic. Existing Mac/tools/cache/fixed path; not clean OS, relocation, standalone, GUI or Windows.'),
    controls=controls,
    implementation='Runtime034 adds an explicit experimental graphical thermal-recovery method on the committed GUI source. This packet establishes full-suite, installation and unchanged ordinary Route workflow regressions only; it does not qualify actual graphical operation or recovery.',
    Native_and_original='Each ordinary Route and fresh export has its own selected10.0.7 refill/connectivity/all-severity/full-schematic/original-rule/semantic/protected proof. Whole retains6 warnings and10 protected records; partial retains0 final findings and4 protected records. Source findings and both original ignored checks remain visible. Expected source opens are not invalid source designs. Routing-scope acceptance is not electrical/physical approval.',
    historical_kind_labels='Frozen ordinary protocols retain literal kind frozen-runtime033-ordinary-workflow and enclosing receipts retain current-runtime030-ordinary-CLI from unchanged shared helpers. Explicit runtime034 path, d64 source commit,65aa manifest and captured controller pins determine this packet scope; those historical kind labels do not promote old results.',
    preparation_costs=dict(install_freeze=cost(ROOT / '.runs/freeze-install-distribution-native-007-001-time.log'),
                           ordinary_protocol_freeze=cost(ROOT / '.runs/freeze-runtime034-ordinary-001-time.log')),
    costs='Complete external exit wall and user+sys CPU are reported once per event; nested stored samples differ and remain raw. Authoring/research/review and curation costs are additional, not routing gain. Installer command_cpu_seconds excludes separately retained source-git observations, while its enclosing complete exit includes waited child costs. Interactive whole CPU is unknown, not zero.',
    source_rights='Owned generated PCB/schematic geometry and project code are under repository GPL. Original official KiCad demo project/settings retain their CC-BY-SA-4.0 notices and earlier033/SOURCE_LEDGER provenance. No private boards, local-reference, downloaded engine/app, venv or bulk data copied.',
    remaining=['Separate actual034 recovery repair/no-repair, invalid and cancellation evidence, plus new actual graphical qualification, are outside this packet;033 GUI074 remains historical and is not new-build proof',
               'Frozen broader licensed development and genuinely untouched confirmation; no general routing, cleanup or speed claim from these fixtures',
               'Windows010 lifetime-isolation blocker; clean OS/relocation/standalone; restoration capacity; independent human/physical review and separate formal publication approval'],
    backup_scope='This bounded text packet is intended for a later audited Git checkpoint. Full raw runtime034 artifacts, including excluded NUL-format Git output, remain on this Mac outside older008/010 backups. Curation is neither a new full backup nor a restoration test.',
    retention=dict(shared_helper=str(helper.relative_to(ROOT)), shared_helper_sha256=p.sha(helper),
                   text_only=True, raw_binary_git_logs_not_copied=binary_git_logs,
                   exclusions='Generated KiCad/engine preferences, caches, tmp and __pycache__ directories are omitted by the unchanged shared tree helper. Their original raw directories remain on Mac.'),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
p.save_json(destination, record)
print(json.dumps(dict(files=len(files), bytes=total, material=len(material), project_complete=False, actual_GUI=False)))
