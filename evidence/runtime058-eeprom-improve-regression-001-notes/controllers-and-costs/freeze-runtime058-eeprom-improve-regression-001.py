"""Freeze one fresh058 EEPROM Improve delivery regression; never execute it.

Port of the057 singleton IR freezer. The unchanged shared six-name contract
reserves unused siblings; only Cimprove is authorized by this preparation.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
        (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import copy, json, os, shutil, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, provenance as pv, preferences as pref, handoff as h
from scripts.freeze_current_comparison import query_runtime, administration, save_new

HEAD = '8f5e96b88dd22cd25919bb71ce47711612994efa'
OLD_PIN = 'eae806695d2bd18534ed81c8bc0f353d6562589a92f5aefd0e35f5bfb576cf69'
SOURCE_PIN = '5d00eef20403051eefbab36cd52b1f3c30266844cc051da22910caf81dbb4563'
runtime = ROOT/'.runs/runtime-directory-058/runtime'
base = ROOT/'.runs/runtime058-eeprom-improve-regression-001'
old = ROOT/'.runs/runtime057-eeprom-development-001/eeprom/Cimprove/protocol.json'
sources_path = ROOT/'.runs/development-eeprom-001/comparison-sources.json'
manifest = runtime/pv.MANIFEST
full_path = ROOT/'.runs/full-integration-209/execution.json'
prep_path = runtime.parent/'preparation.json'
LIMITS = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
    delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120)
assert sys.platform == 'darwin' and not os.path.lexists(base) and shutil.disk_usage(ROOT).free >= 4*1024**3
tracked = administration(HEAD)
assert p.sha(old) == OLD_PIN and p.sha(sources_path) == SOURCE_PIN
plan = copy.deepcopy(f.read_json(old))
assert plan['kind'] == 'installed-native7-current-method-v2' and plan['arm'] == 'Cimprove'
assert plan['population'] == ['B0','B1','B2single_tuned','B2_portfolio','Cdefault','Cimprove']
assert plan['limits'] == LIMITS and plan['whole_wall_full_cpu_seconds'] == 600 and plan['pass_key'] == 'controls_passed'
full = f.read_json(full_path); prepared = f.read_json(prep_path)
assert full['passed'] is True and full['sources_unchanged'] is True
assert full['process']['status'] == 'success' and full['process']['exit_code'] == 0
assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
MANIFEST = p.sha(manifest)  # Actual completed preparation, never a guessed future pin.
assert prepared['prepared'] is True and prepared['source_head'] == HEAD and prepared['runtime'] == str(runtime)
assert prepared['manifest_sha256'] == MANIFEST and prepared['full209_execution_sha256'] == p.sha(full_path)
m = f.read_json(manifest)
implementation = {n:pin for n,pin in pv._file_map(m['immutable_files_sha256']).items() if n.startswith('autorouter/')}
identity = pv._runtime_identity(runtime, implementation)
assert identity['git_head'] == HEAD and identity['manifest_sha256'] == MANIFEST and identity['native_version'] == '10.0.7'
assert p.tree_hash(Path(plan['source']).parent) == plan['source_hashes']
assert plan['default_settings'] == pref.validate(dict(pref.DEFAULTS, seconds=420))
assert plan['improve_settings'] == dict(plan['default_settings'], profile='tuned')
entry = f.read_json(sources_path)['families']['eeprom']
assert all(entry[key] == plan[key] for key in ('source','source_hashes','source_rights'))
child = runtime/'.runs/qualify-current-method-002.py'
payload = pv.read_bytes(ROOT/'scripts/qualify_current_method.py')
assert pv._directory(runtime/'.runs').stat().st_uid == os.getuid()
if os.path.lexists(child): assert child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload
outputs = {name:str(runtime/'.runs'/(
    ('native7-comparison-' if name.startswith('B') else 'native7-method-')+
    'runtime058-eeprom-improve-regression-001-'+name)) for name in plan['population']}
assert len(set(outputs.values())) == 6 and not any(os.path.lexists(value) for value in outputs.values())
# The old protocol binds only the unchanged task/rights definition. No old
# execution, qualification, tools query or candidate supplies current authority.
prereqs = {str(ROOT/name):pin for name,pin in tracked.items()}
prereqs.update({str(old):OLD_PIN, str(sources_path):SOURCE_PIN})
sources = p.tree_hash(Path(plan['source']).parent)
base.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, base)
def remaining():
    left = min(90-(time.monotonic()-START), 90-(cpu()-CPU0))
    if left <= 0: raise p.Rejected('preparation90s wall/fullCPU budget exceeded')
    return left
query, query_pins = query_runtime(runtime, base); tools = query['tools']; remaining()
assert query['runtime'] == str(runtime) and query['interpreter'] == str(runtime/'.venv/bin/python')
assert query['prefix'] == str(runtime/'.venv') and query['defaults'] == dict(pref.DEFAULTS)
assert tools['source_provenance'] == identity and tools['implementation_sha256'] == implementation
assert tools['git_head'] == HEAD and tools['kicad'] == '10.0.7'
assert tools['comparison_route_policy'] == 'selected-native7-fixed-comparison-v2'
if not os.path.lexists(child):
    with child.open('xb') as stream: stream.write(payload)
assert child.stat().st_uid == os.getuid() and pv.read_bytes(child) == payload
for path in (manifest, child, full_path, prep_path, Path(__file__)):
    prereqs[str(path)] = p.sha(path)
prereqs.update(query_pins); assert 0 < len(prereqs) <= 32
plan.update(runtime=str(runtime), runtime_manifest_sha256=MANIFEST, source_head=HEAD, tools=tools,
    controller=str(child), controller_sha256=p.sha(child), controller_args=['--runtime',str(runtime)],
    outputs=outputs, output=outputs['Cimprove'], population_protocol_path=None, population_protocol_sha256=None,
    prerequisite_sha256=prereqs, enclosure_sha256=tracked['scripts/enclose_current_comparison.py'],
    qualifier_sha256=tracked['scripts/qualify_installed_workflow.py'],
    scope='Fresh058 single exposed EEPROM default-score Improve delivery regression. Unchanged source,420wholeImprove/450method/600complete wall+fullCPU/export120,30s review/choice and existing32-trial cap including25s return reserve. Only Cimprove executes; sibling namespaces are reserved, not run. No tuning, old-result substitution, stitched cost, six-arm comparison, GUI/family/holdout/quality or general qualification claim.',
    qualification_context='Prospective058 EEPROM singleton after export replay repair; query/preparation is not Native or delivery qualification.')
def fresh():
    remaining(); assert h.owned_destination(owner) == base and administration(HEAD) == tracked
    assert p.sha(old) == OLD_PIN and p.sha(manifest) == MANIFEST and pv._runtime_identity(runtime,implementation) == identity
    assert p.tree_hash(Path(plan['source']).parent) == sources == plan['source_hashes']
    assert not any(os.path.lexists(value) for value in outputs.values())
    for name,pin in prereqs.items(): assert p.sha(Path(name)) == pin
    for name,pin in tools['files'].items(): assert pv.file_digest(Path(name),pv.MAX_ENGINE_BYTES)[0] == pin
fresh(); pin = save_new(base/'protocol.json', plan)
command = [str(ROOT/'scripts/enclose_current_comparison.py'),'--protocol',str(base/'protocol.json'),'--protocol-sha256',pin]
record = dict(schema=1, kind='runtime058-single-exposed-EEPROM-Improve-regression-preparation-v1',
    prepared=True, executed=False, Native=False, engine=False, actual_GUI=False, accepted=False,
    project_complete=False, not_a_comparison=True, only_arm='Cimprove', source_head=HEAD, runtime=str(runtime),
    manifest_sha256=MANIFEST, protocol_sha256=pin, template_protocol_sha256=OLD_PIN,
    controller_sha256=p.sha(Path(__file__)), source_hashes=plan['source_hashes'], query_sha256=query_pins,
    sampled_preparation_wall_seconds=time.monotonic()-START, sampled_preparation_full_CPU_seconds=cpu()-CPU0,
    complete_external_cost='Separate /usr/bin/time complete exit; nested samples overlap, never added.',
    later_lead_owned_enclosure_argv=command)
save_new(base/'frozen.json', record); fresh(); assert p.sha(base/'protocol.json') == pin
print(json.dumps(dict(protocol=str(base/'protocol.json'), protocol_sha256=pin,
    freezer_sha256=p.sha(Path(__file__)), manifest_sha256=MANIFEST, query_only=True, Native=False, engine=False, prepared=True)))
