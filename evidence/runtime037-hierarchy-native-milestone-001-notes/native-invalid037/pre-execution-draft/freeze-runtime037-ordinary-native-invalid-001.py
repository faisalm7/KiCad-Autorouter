"""Prepare a frozen037 invalid protocol only after actual future prerequisites.

PREPARATION ONLY. Replace ROOT_TO_FREEZE_MANIFEST_SHA in both new037 helpers,
then replace ROOT_TO_FREEZE_CONTROLLER_SHA below with the resulting controller
raw hash. Run only with the exact built037 interpreter after lead review.
This freezer queries metadata; Native invalid controls use unchanged004/180s.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runs/runtime-directory-037/runtime'
HEAD = 'c3e7e8ef4dadce1f83f838322fb5d685ce3714ac'
MANIFEST = 'ROOT_TO_FREEZE_MANIFEST_SHA'
HELPER = 'qualify-runtime037-ordinary-native-invalid-001.py'
HELPER_SHA = 'ROOT_TO_FREEZE_CONTROLLER_SHA'
ENCLOSURE = '.runs/enclose-native7-independent-control-004.py'
ENCLOSURE_SHA = '9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4'
MODULES = {
    'autorouter/pipeline.py': 'bdb8dac630f9d38c6ba832484eb67ec50ee9cde6a5caf60dccf99e455682d017',
    'autorouter/gui.py': '93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e',
}
PREREQUISITES = (
    '.runs/full-integration-180/protocol.json', '.runs/full-integration-180/execution.json',
    '.runs/install-distribution-native-010/protocol.json', '.runs/install-distribution-native-010/execution.json',
    '.runs/runtime-directory-037/result.json',
    '.runs/runtime037-ordinary-whole4Cu-001/protocol.json',
    '.runs/runtime037-ordinary-partial2Cu-001/protocol.json',
    'scripts/qualify_runtime_workflow.py', ENCLOSURE,
)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_bytes())


assert re.fullmatch('[0-9a-f]{64}', MANIFEST), 'fill actual037 manifest in both new helpers before freezing'
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
full = load(ROOT / '.runs/full-integration-180/execution.json')
full_protocol = load(ROOT / '.runs/full-integration-180/protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status'] == 'success' and full['process']['exit_code'] == 0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
assert full_protocol['tools']['git_head'] == HEAD
for relative, pin in MODULES.items(): assert full_protocol['source_sha256'][relative] == pin
install_protocol_path = ROOT / '.runs/install-distribution-native-010/protocol.json'
install_protocol = load(install_protocol_path)
assert install_protocol['source_head'] == HEAD and install_protocol['selected_native_version'] == '10.0.7'
assert install_protocol['output'] == str(RUNTIME.parent)
install = load(ROOT / '.runs/install-distribution-native-010/execution.json')
assert install['passed'] is True and install['source_unchanged'] is True
assert install['process']['status'] == 'success' and install['process']['exit_code'] == 0
assert install['process']['cleanup_complete'] is True and install['process']['log_truncated'] is False
assert install['protocol_sha256'] == fixed['.runs/install-distribution-native-010/protocol.json']
assert install['child_receipt'] == str(ROOT / '.runs/runtime-directory-037/result.json')
assert install['child_receipt_sha256'] == fixed['.runs/runtime-directory-037/result.json']
installed = load(Path(install['child_receipt']))
assert installed['passed'] is True and installed['git_head'] == HEAD and installed['native_version'] == '10.0.7'

positives = {}
for label, scope, seconds, protected, counts in (
        ('whole4Cu', 'whole_board_unlocked_routing', 120, 10, [0, 0, 6, 0]),
        ('partial2Cu', 'partial_completion', 90, 4, [0, 0, 0, 0])):
    folder = ROOT / '.runs' / ('runtime037-ordinary-' + label + '-001')
    protocol, execution = folder / 'protocol.json', folder / 'execution.json'
    caller, completed = load(protocol), load(execution)
    settings = dict(schema=1, scope=scope, seconds=seconds, adapter='both', profile='standard',
                    guidance='native', layers='source_all', scoring_preference=None)
    output = RUNTIME / '.runs' / ('ordinary-' + label + '-001')
    assert type(caller['schema']) is int and caller['schema'] == 1
    assert caller['kind'] == 'runtime037-six-stage-ordinary-CLI'
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
base = ROOT / '.runs/runtime037-ordinary-native-invalid-001'
output = RUNTIME / '.runs/native7-comparison-control-runtime037-invalid-001'
assert sha(original) == HELPER_SHA and not child.exists() and not output.exists() and not base.exists()
assert 'ROOT_TO_FREEZE_MANIFEST_SHA' not in original.read_text()
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
plan = dict(schema=1, kind='runtime037-ordinary-Native-invalid-controls-v1', runtime=str(RUNTIME),
    source_head=HEAD, runtime_manifest_sha256=MANIFEST, tools=tools, controller=str(child),
    helper_sha256=HELPER_SHA, controller_sha256=HELPER_SHA, controller_args=[], pass_key='control_passed',
    enclosure_sha256=ENCLOSURE_SHA, output=str(output),
    whole_wall_full_cpu_seconds=180, scope='partial_completion', profile='standard', adapter='both',
    scoring_variant=None, route_seconds=90, protected_routes=4,
    source=positives['partial2Cu_positive']['source'], source_hashes=positives['partial2Cu_positive']['source_hashes'],
    prerequisite_files=fixed, required_runtime_module_sha256=MODULES,
    preparation=dict(freezer_sha256=sha(Path(__file__)), tools_query_path=str(query_path),
        tools_query_sha256=sha(query_path), tools_query_process_sha256=sha(base / 'tools-defaults-process.json'),
        scope='Post-build actual037 interpreter metadata only; no Native control executed by freezer.'), **positives)
with child.open('xb') as stream: stream.write(original.read_bytes())
assert sha(child) == HELPER_SHA
path = base / 'protocol.json'
with path.open('x') as stream: json.dump(plan, stream, sort_keys=True, indent=2); stream.write('\n')
print(json.dumps(dict(protocol=str(path), sha256=sha(path), output=str(output), Native_executed=False)))
