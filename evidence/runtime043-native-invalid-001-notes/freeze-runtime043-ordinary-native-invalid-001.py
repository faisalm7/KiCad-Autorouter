"""Freeze043 invalid metadata after full190, actual preparation/doctor and current positives.

Actual043 manifest and fractional-edge correction source are pinned. The existing004
180-second invalid control is unchanged; this freezer makes no Native pass.
Run only with the exact built043 interpreter after lead review and after both
current whole4Cu/partial2Cu deliveries pass all existing source/proof gates.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runs/runtime-directory-043/runtime'
HEAD = '6ec7ad2344ed060d5e0971965ef05bd9de68925d'
MANIFEST = '6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3'
HELPER = 'qualify-runtime043-ordinary-native-invalid-001.py'
HELPER_SHA = 'e424ff00d401fcca75f80e88617743ef66db78ffdfdf26af3ec51c311cd3f462'
ENCLOSURE = '.runs/enclose-native7-independent-control-004.py'
ENCLOSURE_SHA = '9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4'
MODULES = {
    'autorouter/pipeline.py': 'eb967f9bfb8643d1c8752fcab0efbab70b6b2a1d7e72daa147d55fa21e7e0da5',
    'autorouter/gui.py': '93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e',
}
PREREQUISITES = (
    '.runs/full-integration-190/protocol.json', '.runs/full-integration-190/execution.json',
    '.runs/prepare-runtime043-001.py', '.runs/runtime-directory-043/preparation.json',
    '.runs/runtime-directory-043/venv-process.json', '.runs/runtime-directory-043/venv.log',
    '.runs/runtime043-native-qualification-001/doctor.json',
    '.runs/runtime043-native-qualification-001/doctor-process.json',
    '.runs/runtime043-native-qualification-001/tools-defaults.json',
    '.runs/runtime043-native-qualification-001/tools-defaults-process.json',
    '.runs/runtime043-native-qualification-001/whole4Cu/protocol.json',
    '.runs/runtime043-native-qualification-001/partial2Cu/protocol.json',
    'scripts/qualify_runtime_workflow.py', ENCLOSURE,
)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_bytes())


assert re.fullmatch('[0-9a-f]{64}', MANIFEST), 'fill actual043 manifest in both new helpers before freezing'
assert re.fullmatch('[0-9a-f]{64}', HELPER_SHA), 'pin controller after replacing its manifest placeholder'
assert Path(sys.executable).absolute() == RUNTIME / '.venv/bin/python'
assert Path(sys.prefix).resolve() == RUNTIME / '.venv' and sys.prefix != sys.base_prefix
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, preferences as pref
from autorouter.runner import run
from autorouter.gui import child_environment
assert p.c.ROOT == RUNTIME and p.c.NATIVE_VERSION == '10.0.7'
assert sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
assert sha(ROOT / ENCLOSURE) == ENCLOSURE_SHA
for relative, pin in MODULES.items(): assert sha(RUNTIME / relative) == pin

# Future values are observed only here, after actual files exist. No historical
# pass/hash or guessed result is installed into this prospective protocol.
fixed = {relative: sha(ROOT / relative) for relative in PREREQUISITES}
full = load(ROOT / '.runs/full-integration-190/execution.json')
full_protocol = load(ROOT / '.runs/full-integration-190/protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status'] == 'success' and full['process']['exit_code'] == 0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
assert full_protocol['tools']['git_head'] == HEAD
for relative, pin in MODULES.items(): assert full_protocol['source_sha256'][relative] == pin
prepared = load(ROOT / '.runs/runtime-directory-043/preparation.json')
assert type(prepared['schema']) is int and prepared['schema'] == 1
assert prepared['kind'] == 'runtime043-existing-local-preparation-v1'
assert prepared['prepared'] is True and prepared['qualified'] is False and prepared['actual_GUI'] is False
assert prepared['source_head'] == HEAD and prepared['runtime'] == str(RUNTIME)
assert prepared['manifest_sha256'] == MANIFEST
assert prepared['full190_execution_sha256'] == fixed['.runs/full-integration-190/execution.json']
assert prepared['controller_sha256'] == fixed['.runs/prepare-runtime043-001.py']
recipe = prepared['recipe']; identity = recipe['source_provenance']
assert recipe['root'] == str(RUNTIME) and recipe['local_engine_copied'] is True
assert recipe['standalone'] is False and recipe['published'] is False
assert identity['kind'] == 'runtime-directory-v1' and identity['git_head'] == HEAD
assert identity['manifest_sha256'] == MANIFEST and identity['native_version'] == '10.0.7'
assert identity == p.tool_manifest()['source_provenance']
venv = load(ROOT / '.runs/runtime-directory-043/venv-process.json')
assert prepared['venv_process_sha256'] == fixed['.runs/runtime-directory-043/venv-process.json']
assert sha(Path(prepared['base_python']['path'])) == prepared['base_python']['sha256']
assert venv['argv'] == [*f.SANDBOX, prepared['base_python']['path'], '-B', '-m', 'venv', '--copies', str(RUNTIME / '.venv')]
assert venv['cwd'] == str(RUNTIME.parent)
for name in ('venv', 'doctor', 'tools-defaults'):
    folder = RUNTIME.parent if name == 'venv' else ROOT / '.runs/runtime043-native-qualification-001'
    process = venv if name == 'venv' else load(folder / (name + '-process.json'))
    log = folder / ('venv.log' if name == 'venv' else name + '.json')
    assert process['status'] == 'success' and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
    assert process['log'] == str(log) and process['log_bytes'] == log.stat().st_size
    if name != 'venv':
        assert process['cwd'] == str(RUNTIME)
        assert process['argv'][:5] == [*f.SANDBOX, str(RUNTIME / '.venv/bin/python'), '-B']
doctor = load(ROOT / '.runs/runtime043-native-qualification-001/doctor.json')
assert doctor['ready'] is True and doctor['workspace'] == str(RUNTIME)
assert doctor['checks']['runtime_provenance'] == {'verified': True, 'identity': identity}
for name in ('kicad_version', 'pcbnew_version'):
    assert doctor['checks'][name] == {'exit': 0, 'output': '10.0.7'}
assert load(ROOT / '.runs/runtime043-native-qualification-001/doctor-process.json')['argv'] == [
    *f.SANDBOX, str(RUNTIME / '.venv/bin/python'), '-B', '-m', 'autorouter', 'doctor']
initial_query = load(ROOT / '.runs/runtime043-native-qualification-001/tools-defaults.json')
assert initial_query == {'tools': p.tool_manifest(), 'defaults': dict(pref.DEFAULTS)}

positives = {}
for label, scope, seconds, protected, counts in (
        ('whole4Cu', 'whole_board_unlocked_routing', 120, 10, [0, 0, 6, 0]),
        ('partial2Cu', 'partial_completion', 90, 4, [0, 0, 0, 0])):
    folder = ROOT / '.runs/runtime043-native-qualification-001' / label
    protocol, execution = folder / 'protocol.json', folder / 'execution.json'
    caller, completed = load(protocol), load(execution)
    settings = dict(schema=1, scope=scope, seconds=seconds, adapter='both', profile='standard',
                    guidance='native', layers='source_all', scoring_preference=None)
    output = RUNTIME / '.runs' / ('ordinary-' + label + '-001')
    assert type(caller['schema']) is int and caller['schema'] == 1
    assert caller['kind'] == 'runtime043-six-stage-ordinary-CLI'
    assert caller['runtime'] == str(RUNTIME) and caller['source_head'] == HEAD
    assert caller['runtime_manifest_sha256'] == MANIFEST and caller['settings'] == settings
    assert caller['output'] == str(output) and caller['expected_counts'] == counts
    assert caller['expected_protected_count'] == protected
    assert caller['budgets'] == dict(route=seconds, export=seconds)
    assert caller['settings_sha256'] == sha(folder / 'settings.json')
    assert load(folder / 'settings.json') == settings
    assert caller['driver_sha256'] == fixed['scripts/qualify_runtime_workflow.py']
    assert completed['controls_passed'] is True and completed['workflow_delivered'] is True
    assert completed['protocol_sha256'] == sha(protocol) and completed['error'] is None
    assert completed['process']['status'] == 'success' and completed['process']['exit_code'] == 0
    assert completed['process']['cleanup_complete'] is True and completed['process']['log_truncated'] is False
    result = output / 'result.json'; data = load(result)
    assert completed['child_receipt'] == str(result) and completed['child_sha256'] == sha(result)
    assert type(data['schema']) is int and data['schema'] == 1
    assert data['status'] == 'completed' and data['workflow_delivered'] is True
    assert data['accepted'] is False and data['actual_GUI'] is False and data['human_review'] is False
    assert data['source'] == caller['source'] and data['source_hashes'] == caller['source_hashes']
    assert p.tree_hash(Path(caller['source']).parent) == caller['source_hashes']
    workspace = Path(data['workspace'])
    assert workspace.is_absolute() and workspace.resolve() == workspace
    assert workspace.parent == output and workspace.name.startswith('autorouter-gui-') and workspace.is_dir()
    item = dict(source=caller['source'], source_hashes=caller['source_hashes'], output=str(output), workspace=str(workspace))
    for name, path in dict(protocol=protocol, execution=execution, result=result,
                           route=workspace / 'route/result.json', export=workspace / 'export/export.json').items():
        item[name + '_path'] = str(path); item[name + '_sha256'] = sha(path)
    # The independent control child repeats these shared current positive
    # readers before its first Native invalid mutation and after completion.
    positives[label + '_positive'] = item

original = ROOT / '.runs' / HELPER; child = RUNTIME / '.runs' / HELPER
base = ROOT / '.runs/runtime043-ordinary-native-invalid-001'
output = RUNTIME / '.runs/native7-comparison-control-runtime043-invalid-001'
assert sha(original) == HELPER_SHA and not child.exists() and not output.exists() and not base.exists()
assert 'ROOT_TO_FREEZE_' not in original.read_text()
assert shutil.disk_usage(ROOT).free > 2 * 1024**3
base.mkdir()
query_path = base / 'tools-defaults.json'
code = ('import json,sys;sys.path.insert(0,' + repr(str(RUNTIME)) + ');'
        'from autorouter import pipeline as p,preferences as pref;'
        'print(json.dumps(dict(runtime=str(p.c.ROOT),interpreter=sys.executable,prefix=sys.prefix,'
        'tools=p.tool_manifest(),defaults=dict(pref.DEFAULTS)),sort_keys=True))')
query_process = run([*f.SANDBOX, str(RUNTIME / '.venv/bin/python'), '-B', '-c', code],
    cwd=base, env=child_environment(), log=query_path, timeout=30, max_log_bytes=512*1024,
    max_group_rss_bytes=1024**3, max_workdir_bytes=2*1024**2)
p.save_json(base / 'tools-defaults-process.json', query_process)
assert query_process['status'] == 'success' and query_process['exit_code'] == 0
assert query_process['cleanup_complete'] is True and query_process['log_truncated'] is False
query = load(query_path); tools = query['tools']
assert query['runtime'] == str(RUNTIME) and query['interpreter'] == str(RUNTIME / '.venv/bin/python')
assert query['prefix'] == str(RUNTIME / '.venv') and query['defaults'] == dict(pref.DEFAULTS)
assert tools == p.tool_manifest() and tools['git_head'] == HEAD and tools['kicad'] == '10.0.7'
assert tools['source_provenance']['manifest_sha256'] == MANIFEST
assert shutil.disk_usage(ROOT).free > 2*1024**3 and sha(original) == HELPER_SHA
for relative, pin in fixed.items(): assert sha(ROOT / relative) == pin
for item in positives.values():
    for name in ('protocol', 'execution', 'result', 'route', 'export'):
        assert sha(Path(item[name + '_path'])) == item[name + '_sha256']
    assert p.tree_hash(Path(item['source']).parent) == item['source_hashes']
plan = dict(schema=1, kind='runtime043-ordinary-Native-invalid-controls-v1', runtime=str(RUNTIME),
    source_head=HEAD, runtime_manifest_sha256=MANIFEST, tools=tools, controller=str(child),
    helper_sha256=HELPER_SHA, controller_sha256=HELPER_SHA, controller_args=[], pass_key='control_passed',
    enclosure_sha256=ENCLOSURE_SHA, output=str(output),
    whole_wall_full_cpu_seconds=180, scope='partial_completion', profile='standard', adapter='both',
    scoring_variant=None, route_seconds=90, protected_routes=4,
    source=positives['partial2Cu_positive']['source'], source_hashes=positives['partial2Cu_positive']['source_hashes'],
    prerequisite_files=fixed, required_runtime_module_sha256=MODULES,
    preparation=dict(freezer_sha256=sha(Path(__file__)), tools_query_path=str(query_path),
        tools_query_sha256=sha(query_path), tools_query_process_sha256=sha(base / 'tools-defaults-process.json'),
        scope='Post-build actual043 interpreter metadata only; no Native control executed by freezer.'), **positives)
with child.open('xb') as stream: stream.write(original.read_bytes())
assert sha(child) == HELPER_SHA
path = base / 'protocol.json'
with path.open('x') as stream: json.dump(plan, stream, sort_keys=True, indent=2); stream.write('\n')
print(json.dumps(dict(protocol=str(path), sha256=sha(path), output=str(output), Native_executed=False)))
