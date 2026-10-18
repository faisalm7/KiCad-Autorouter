"""Freeze034 invalid controls only after both actual ordinary positives complete.

Authoring is not freezing/execution. Invoke this file later with the exact034
runtime interpreter, after lead review. It performs only bounded tool metadata
query/copy/protocol freezing; Native controls use the unchanged enclosure004.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runs/runtime-directory-034/runtime'
HEAD = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
MANIFEST = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
HELPER = 'qualify-runtime034-ordinary-native-invalid-001.py'
HELPER_SHA = '3b72b1e93d90e3b53cb05180866617f72bc9be9ee5149f7a7f0da893a6ec1680'
FIXED = {
    '.runs/full-integration-177/protocol.json': '8a12246a4ddf87a11dba42006d20f96dc4b44749d13417e5fbb3debc95ebf310',
    '.runs/full-integration-177/execution.json': 'e5ff00d2ff891aa55b1041c3f567980848619fd1aef8aa9de6f9de4aa7837efe',
    '.runs/install-distribution-native-007/protocol.json': '24527ae076d134fad3dc97e48ee6569405dfbedb7c891ce64208aaddbb171b48',
    '.runs/install-distribution-native-007/execution.json': '13b8d9a839c7db0fcd4ff44d7e0552b149ece4577a1fba4373c846b4f1a834f2',
    '.runs/runtime-directory-034/result.json': 'b4b99f940523f143fbda2b9ee242aac75bd89af135e70c3a52fdb9514cf51cd4',
    '.runs/runtime034-ordinary-whole4Cu-001/protocol.json': '907c9fdba4a77a15e55af6fe419cf5931384f8e851046f956dbe7666a61c6680',
    '.runs/runtime034-ordinary-partial2Cu-001/protocol.json': '12701f9b95e19e8a280f7e95c5c9b675a0a52cf05b34c15fb72a493cada47eac',
    '.runs/enclose-native7-independent-control-004.py': '9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4',
}
MODULES = {
    'autorouter/pipeline.py': '8a0276c178649ff76383865e125c63803a71a15b144ac29905a0c072c67480af',
    'autorouter/gui.py': '1d5f4f6f776e970c9d78a33f1e116c16c3333e880f1e4328a25338226bf9f827',
}
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_bytes())

assert Path(sys.executable).absolute() == RUNTIME / '.venv/bin/python'
assert Path(sys.prefix).resolve() == RUNTIME / '.venv' and sys.prefix != sys.base_prefix
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, preferences as pref
from autorouter.runner import run
from autorouter.gui import child_environment
assert p.c.ROOT == RUNTIME and p.c.NATIVE_VERSION == '10.0.7'
assert sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
for relative, pin in FIXED.items(): assert sha(ROOT / relative) == pin
for relative, pin in MODULES.items(): assert sha(RUNTIME / relative) == pin
full = load(ROOT / '.runs/full-integration-177/execution.json')
assert full['passed'] is True and full['sources_unchanged'] is True
full_protocol = load(ROOT / '.runs/full-integration-177/protocol.json')
for relative, pin in MODULES.items(): assert full_protocol['source_sha256'][relative] == pin
install = load(ROOT / '.runs/install-distribution-native-007/execution.json')
assert install['passed'] is True and install['source_unchanged'] is True
assert install['protocol_sha256'] == FIXED['.runs/install-distribution-native-007/protocol.json']
assert install['child_receipt'] == str(ROOT / '.runs/runtime-directory-034/result.json')
assert install['child_receipt_sha256'] == FIXED['.runs/runtime-directory-034/result.json']
installed = load(Path(install['child_receipt']))
assert installed['passed'] is True and installed['git_head'] == HEAD and installed['native_version'] == '10.0.7'

positives = {}
for label, scope, seconds, protected, counts in (
        ('whole4Cu', 'whole_board_unlocked_routing', 120, 10, [0, 0, 6, 0]),
        ('partial2Cu', 'partial_completion', 90, 4, [0, 0, 0, 0])):
    folder = ROOT / '.runs' / ('runtime034-ordinary-' + label + '-001')
    protocol, execution = folder / 'protocol.json', folder / 'execution.json'
    caller, completed = load(protocol), load(execution)
    settings = dict(schema=1, scope=scope, seconds=seconds, adapter='both', profile='standard',
                    guidance='native', layers='source_all', scoring_preference=None)
    output = RUNTIME / '.runs' / ('production-' + label + '-delivery-001')
    assert caller['kind'] == 'frozen-runtime033-ordinary-workflow'  # Existing schema marker, not runtime identity.
    assert caller['runtime'] == str(RUNTIME) and caller['source_head'] == HEAD
    assert caller['runtime_manifest_sha256'] == MANIFEST and caller['settings'] == settings
    assert caller['output'] == str(output) and caller['expected_counts'] == counts
    assert caller['expected_protected_count'] == protected
    assert completed['controls_passed'] is True and completed['workflow_delivered'] is True
    assert completed['protocol_sha256'] == sha(protocol) and completed['error'] is None
    assert completed['process']['status'] == 'success' and completed['process']['exit_code'] == 0
    assert completed['process']['cleanup_complete'] is True and completed['process']['log_truncated'] is False
    result = output / 'result.json'; data = load(result)
    assert completed['child_receipt'] == str(result) and completed['child_sha256'] == sha(result)
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
    positives[label + '_positive'] = item

original = ROOT / '.runs' / HELPER; child = RUNTIME / '.runs' / HELPER
base = ROOT / '.runs/runtime034-ordinary-native-invalid-002'
output = RUNTIME / '.runs/native7-comparison-control-runtime034-invalid-001'
assert sha(original) == HELPER_SHA and not child.exists() and not output.exists() and not base.exists()
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
for relative, pin in FIXED.items(): assert sha(ROOT / relative) == pin
for item in positives.values():
    for name in ('protocol', 'execution', 'result', 'route', 'export'):
        assert sha(Path(item[name + '_path'])) == item[name + '_sha256']
    assert p.tree_hash(Path(item['source']).parent) == item['source_hashes']
plan = dict(schema=1, kind='runtime034-ordinary-Native-invalid-controls-v1', runtime=str(RUNTIME),
    source_head=HEAD, runtime_manifest_sha256=MANIFEST, tools=tools, controller=str(child),
    helper_sha256=HELPER_SHA, controller_sha256=HELPER_SHA, controller_args=[], pass_key='control_passed',
    enclosure_sha256=FIXED['.runs/enclose-native7-independent-control-004.py'], output=str(output),
    whole_wall_full_cpu_seconds=180, scope='partial_completion', profile='standard', adapter='both',
    scoring_variant=None, route_seconds=90, protected_routes=4,
    source=positives['partial2Cu_positive']['source'], source_hashes=positives['partial2Cu_positive']['source_hashes'],
    prerequisite_files=FIXED, required_runtime_module_sha256=MODULES,
    preparation=dict(freezer_sha256=sha(Path(__file__)), tools_query_path=str(query_path),
        tools_query_sha256=sha(query_path), tools_query_process_sha256=sha(base / 'tools-defaults-process.json'),
        scope='Post-build actual034 interpreter metadata only; no Native control executed by freezer.'), **positives)
with child.open('xb') as stream: stream.write(original.read_bytes())
assert sha(child) == HELPER_SHA
path = base / 'protocol.json'
with path.open('x') as stream: json.dump(plan, stream, sort_keys=True, indent=2); stream.write('\n')
print(json.dumps(dict(protocol=str(path), sha256=sha(path), output=str(output), Native_executed=False)))
