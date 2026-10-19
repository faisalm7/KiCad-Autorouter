"""Retain the completed CD898 prerequisites and failed first hierarchy control.

No worker, Native API, test, installation, GUI or current product code executes.
"""
from pathlib import Path
import ast, datetime, hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-036/runtime'
sys.path.insert(0, str(runtime))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

notes = ROOT / 'evidence/runtime036-native-prerequisites-failure-001-notes'
packet = ROOT / 'evidence/runtime036-native-prerequisites-failure-001.json'
assert not notes.exists() and not packet.exists()
refs = {}; files = []; material = []; total = 0; queued = []
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('retain', 'tree', 'cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))
shared_retain = retain
def retain(path, name):
    queued.append((Path(path), Path(name)))

head = 'cd898bf3c1c97e988a820c2bf1b783ab6f44864d'
fullroot = ROOT / '.runs/full-integration-179'
installroot = ROOT / '.runs/install-distribution-native-009'
controlroot = ROOT / '.runs/hierarchy-native-controls-001'
full = f.read_json(fullroot / 'execution.json')
fullplan = f.read_json(fullroot / 'protocol.json')
install = f.read_json(installroot / 'execution.json')
installplan = f.read_json(installroot / 'protocol.json')
plan = f.read_json(controlroot / 'protocol.json')
outer = f.read_json(controlroot / 'enclosure/result.json')
childroot = Path(plan['output'])
child = f.read_json(childroot / 'result.json')
manifest = runtime / 'runtime-distribution.json'
manifest_data = f.read_json(manifest)
installed = f.read_json(runtime.parent / 'result.json')
smoke = f.read_json(runtime / '.runs/install-native-smoke/result.json')
assert full['passed'] and full['sources_unchanged']
assert fullplan['tools']['git_head'] == head
assert install['passed'] and install['source_unchanged'] and installed['passed']
assert installplan['source_head'] == installed['git_head'] == head
assert manifest_data['build_source']['git_head'] == head and manifest_data['native_version'] == '10.0.7'
assert p.sha(manifest) == plan['runtime_manifest_sha256'] == '7f50a06aed2b80bca80b54b8cba3b806d39b80531694f458d0c34dde7298c754'
assert install['child_receipt_sha256'] == p.sha(runtime.parent / 'result.json')
assert installplan['full_integration179']['execution_sha256'] == p.sha(fullroot / 'execution.json')
assert installplan['full_integration179']['protocol_sha256'] == p.sha(fullroot / 'protocol.json')
assert p.sha(controlroot / 'protocol.json') == outer['protocol_sha256'] == child['protocol_sha256']
assert p.sha(childroot / 'result.json') == outer['child_sha256']
assert child['status'] == 'failed' and not child['control_passed'] and child['cases'] == []
assert child['error'] == 'ValueError: hierarchy parity: native unit UUID order/census differs'
assert child['Native_executed'] is True and outer['passed'] is False
assert all(child[key] is False for key in ('accepted', 'production_admitted', 'project_complete', 'actual_GUI', 'human_review'))
assert len(child['all_steps']) == 1
steps = child['all_steps'][0]['steps']
assert [row['name'] for row in steps] == ['export', 'task-classes-netlist']
assert all(row['status'] == 'success' and row['exit_code'] == 0 and row['cleanup_complete'] for row in steps)
assert outer['process']['exit_code'] == 2 and outer['process']['cleanup_complete'] is True
assert not (childroot / 'positive/task-classes-proof.json').exists()
assert not any((childroot / name).exists() for name in ('net-partition-mismatch', 'wrong-instance-path', 'unsupported-class-directive'))
assert p.tree_hash(Path(plan['source']).parent) == plan['source_hashes']
assert [smoke['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 0, 0]
assert installed['check_result']['current'] is True

tree(fullroot, Path('full179'))
tree(installroot, Path('install009/enclosure'))
tree(controlroot, Path('hierarchy001/enclosure-and-original-source'))
tree(childroot, Path('hierarchy001/failed-native-output'))
tree(runtime / '.runs/install-native-smoke', Path('install009/native-smoke'))
tree(runtime.parent / 'source-fixture', Path('install009/original-smoke-source'))
retain(runtime.parent / 'result.json', Path('install009/runtime-result.json'))
retain(manifest, Path('runtime036/runtime-distribution.json'))
for cmd in installed['commands']:
    log = Path(cmd['log'])
    assert log.parent == runtime.parent and p.sha(log) == cmd['log_sha256']
    retain(log, Path('install009/command-logs') / log.name)

# These are the old immutable runtime bytes, never current v2 product files.
for name, digest in manifest_data['immutable_files_sha256'].items():
    source = runtime / name
    assert p.sha(source) == digest
    retain(source, Path('runtime036/immutable') / name)

controllers = [
    ('run-full-integration-179.py', full['controller_sha256']),
    ('full-suite-local-root-019.py', fullplan['discovery_sha256']),
    ('run-install-distribution-native-009.py', installplan['controller_sha256']),
    ('enclose-runtime030-independent-control-001.py', plan['enclosure_sha256']),
]
for name, digest in controllers:
    source = ROOT / '.runs' / name
    assert p.sha(source) == digest
    retain(source, Path('controllers') / name)
controller = Path(plan['controller'])
assert controller.parent == runtime / '.runs' and p.sha(controller) == plan['controller_sha256']
retain(controller, Path('controllers') / controller.name)
for name in ('scripts/install_smoke.py', 'scripts/prepare_runtime.py',
             'experiments/schematic_hierarchy_native_v1/fixture.py',
             'experiments/native_schematic_transport_v1/fixture.py'):
    assert p.sha(ROOT / name) == fullplan['source_sha256'][name]
    retain(ROOT / name, Path('controllers/committed-cd898') / name)
for stem in ('full-integration-179', 'install-distribution-native-009', 'hierarchy-native-controls-001'):
    for suffix in ('-controller.log', '-time.log'):
        retain(ROOT / '.runs' / (stem + suffix), Path('costs') / (stem + suffix))
for suffix in ('-preparation.log', '-preparation-time.log'):
    retain(ROOT / '.runs' / ('hierarchy-native-controls-001' + suffix), Path('costs') / ('hierarchy-native-controls-001' + suffix))
review = ROOT / '.runs/hierarchy-native-stamp-contract-review-001.json'
assert p.sha(review) == '5bc336f8cd6e8ce7e96258d1fb9032822a8ab9799dad837f2c7b637c8d1e99d8'
retain(review, Path('independent-review') / review.name)
retain(helper, Path('controllers') / helper.name)
retain(Path(__file__), Path('controllers') / Path(__file__).name)

# Inspect all selected bytes before creating the fresh output. No raw archive census.
new = {}; seen_paths = {}; secret_findings = []
secret = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|(?i:Authorization:\s*Bearer\s+[A-Za-z0-9_.-]{20,})')
for source, name in queued:
    raw = io.read_bytes(source, 4 * 1024**2)
    assert b'\0' not in raw
    raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    if secret.search(raw): secret_findings.append(str(source.relative_to(ROOT)))
    assert name not in seen_paths or seen_paths[name] == digest
    seen_paths[name] = digest
    new.setdefault(digest, len(raw))
assert not secret_findings
assert sum(new.values()) < 16 * 1024**2 and len(new) < 2000
for source, name in queued:
    shared_retain(source, name)
assert total == sum(new.values()) and len(files) == len(new)

scope = notes / 'SCOPE.md'
scope_raw = ('''# Retention scope

This packet preserves source cd898bf3c1c97e988a820c2bf1b783ab6f44864d only:
full179, install009/runtime036 and the failed first hierarchy Native control.
The hierarchy control ran export and SCH netlist workers, then refused its
incorrect source-unit UUID ordering assumption. No class proof, source full-SCH
DRC or later three controls completed. No hierarchy/route/GUI admission follows.

All retained design bytes are project-owned generated smoke/hierarchy fixtures
under the retained GPL-3.0-or-later repository LICENSE. The original factory
and dependency factory retain explicit notices. No mixer/NUS/private source,
downloaded engine, KiCad application or JRE/JAR binary is copied.

Copies preserve original UTF-8 bytes and hashes, including failed records.
SHA-identical files share one retained payload with each original path indexed.
The independent review describes a prospective correction, not actual001 repair.
Current v2 product bytes are excluded; only immutable runtime036 and exact
full179-pinned controller/factory bytes enter this old-source packet.

Excluded: kicad-config, kicad-cache, kicad-documents, engine-config, tmp and
__pycache__; runtime venv/tools; repeated runtime-directory/source-git*.json/log
observations and empty Git template; bulk historical source/evidence and any
other runs. These exclusions are not an archive audit or a full raw backup.
Their raw files remain on this Mac outside backups008/010. No restoration retry
or external backup was performed. Original records are untouched.

External /usr/bin/time costs include child/controller work; nested observations
are retained for inspection and never added again to the same invocation.
Preparation and this curation are additional work; curation whole CPU/wall is
not measured here. No Native/test/CI/GUI/installation job was started by curation.

The first curator invocation stopped before creating outputs: its draft guessed
the wrong enclosure helper filename and refused the resulting SHA mismatch.
The actual001 enclosure is enclose-runtime030-independent-control-001.py with
the exact protocol SHA. That curation failure did not run or repair any Native
control. Its console traceback was not saved as a raw log; whole cost is unknown.
''').encode()
with scope.open('xb') as stream: stream.write(scope_raw)
files.append(dict(path=str(scope.relative_to(ROOT)), bytes=len(scope_raw), sha256=hashlib.sha256(scope_raw).hexdigest(), authored=True))
total += len(scope_raw)
assert total < 16 * 1024**2
index = notes / 'files.json'
p.save_json(index, dict(schema=1, files=files, material=material,
    excluded_patterns=['kicad-config/**', 'kicad-cache/**', 'kicad-documents/**', 'engine-config/**', 'tmp/**', '__pycache__/**', 'runtime/.venv/**', 'runtime/.tools/**', 'runtime-directory-036/source-git*.json', 'runtime-directory-036/source-git*.log', 'empty-git-template/**'],
    source_rights='Project-owned generated fixtures and authored runtime/controllers; GPL-3.0-or-later notices and LICENSE retained.',
    preflight=dict(unique_payload_files=len(new), unique_payload_bytes=sum(new.values()), max_new_bytes=16*1024**2, text_only=True, secret_pattern_findings=secret_findings)))

record = dict(schema=1, kind='runtime036-native-prerequisites-with-failed-hierarchy001',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=head, native_version='10.0.7', accepted=False, hierarchy_support_admitted=False,
    routing_accepted=False, project_complete=False, actual_GUI=False, human_review=False,
    runtime_manifest_sha256=p.sha(manifest), runtime_immutable_files=len(manifest_data['immutable_files_sha256']),
    runtime_modules=len([name for name in manifest_data['immutable_files_sha256'] if name.startswith('autorouter/') and name.endswith('.py')]),
    full179=dict(passed=True, tests=2247, skips=1, complete_external_cost=cost(ROOT/'.runs/full-integration-179-time.log'),
        nested_controller_wall_seconds=full['wall_seconds'], nested_controller_full_CPU_seconds=full['full_cpu_seconds'],
        scope='Complete integration suite; no installed hierarchy, actual GUI, fair comparison, physical/electrical or product completion proof.'),
    install009=dict(passed=True, mode='distribution', complete_external_cost=cost(ROOT/'.runs/install-distribution-native-009-time.log'),
        nested_controller_wall_seconds=install['complete_wall_seconds'], nested_controller_full_CPU_seconds=install['complete_full_CPU_seconds'],
        fixture_ownership=installed['fixture']['ownership'], smoke_native_counts=[0,0,0,0], smoke_candidate_sha256=smoke['candidate_sha256'],
        smoke_check_current=True, scope='Copied curated selected7 runtime/venv/doctor and owned unflagged smoke Route/check. No supplied SCH, hierarchy, clean OS, relocation, GUI or Windows qualification.'),
    hierarchy001=dict(passed=False, status=child['status'], error=child['error'], Native_executed=True,
        complete_external_cost=cost(ROOT/'.runs/hierarchy-native-controls-001-time.log'),
        nested_controller_wall_seconds=outer['complete_wall_seconds'], nested_controller_full_CPU_seconds=outer['complete_full_CPU_seconds'],
        nested_child_sample_wall_seconds=child['sampled_wall_seconds'], nested_child_sample_full_CPU_seconds=child['sampled_full_CPU_seconds'],
        workers=[dict(name=row['name'], status=row['status'], exit_code=row['exit_code'], cleanup_complete=row['cleanup_complete'], wall_seconds=row['wall_seconds'], CPU_seconds=row['cpu_seconds']) for row in steps],
        enclosing_exit_code=2, enclosing_cleanup_complete=True, class_proof_emitted=False, source_full_SCH_DRC_executed=False,
        completed_cases=0, intended_cases=4, attempted_case='positive (failed before qualification)',
        not_run_cases=['net-partition-mismatch','wrong-instance-path','unsupported-class-directive'],
        source_hashes=plan['source_hashes'], protocol_sha256=p.sha(controlroot/'protocol.json'),
        interpretation='Actual export and SCH worker both exit0; source proof correctly refuses the then-implemented incorrect unit-order contract. Raw failure remains failed. A source-informed future correction and its tests cannot repair or qualify runtime036.'),
    preparation_cost=cost(ROOT/'.runs/hierarchy-native-controls-001-preparation-time.log'),
    curation_preflight_failure=dict(command='python3 -B .runs/curate-runtime036-native-prerequisites-failure-001.py',
        status='AssertionError before any retained output was created',
        cause='Draft curator guessed enclose-native7-independent-control-004.py rather than the actual protocol-pinned enclose-runtime030-independent-control-001.py.',
        expected_enclosure_sha256=plan['enclosure_sha256'], wrong_helper_sha256='9a77bdc832988f45d3bd920dfeeed09288700569db8da7788d043308deb478e4',
        raw_console_log_retained=False, whole_wall_and_CPU_cost='not measured; not zero',
        actual_control_rerun=False, original_bytes_modified=False),
    accounting='External full179355.36/349.55, install00922.93/19.48 and hierarchy0011.90/1.50 wall/CPU seconds are separate invocations. Nested controller/child/step observations are included within each external cost, not additional charges. Preparation0.08/0.04 is separate. Interactive authoring/review/curation cost additional and not measured here, never zero.',
    preservation='Every retained invocation/result, original source, process/log and binding byte is unchanged. Missing proof and three unrun cases are explicit. Current v2 runtime/product files excluded.',
    public_safety='All selected payload bytes preflighted UTF-8/no NUL and known credential/private-key token patterns. Source and controllers are project-owned GPL text; no private board, unlicensed dataset, binary tool or global user configuration copied. Pattern scan is bounded evidence, not an authentication or general secret detector.',
    source_rights='Project-owned generated smoke and schematic_hierarchy_native_v1 fixtures under retained GPL-3.0-or-later repository LICENSE and factory notices; no unrelated board family gain.',
    review=dict(path=str(review.relative_to(ROOT)), sha256=p.sha(review), scope='Independent AI causal contract review, not human or fresh Native qualification; retained separately.'),
    limitations=['No hierarchy support/admission, routing completion/quality gain, family independence, fair B0/B1/B2/C, actual036GUI or human/electrical validation.',
        'Installation smoke alone is not a fresh actual hierarchy positive; full179 pure/constructed controls missed the Native UUID serialization mismatch.',
        'Full raw and caches/tools/venv/repeated Git observations remain Mac-only outside008/010; this is essential evidence curation, not backup/restoration or release completion.'],
    retention=dict(helper=str(helper.relative_to(ROOT)), helper_sha256=p.sha(helper), new_payload_files=len(files), new_payload_bytes=total,
        original_material_paths=len(material), max_new_bytes=16*1024**2, self_contained=True),
    files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
for row in material:
    assert p.sha(ROOT/row['original']) == p.sha(ROOT/row['retained']) == row['sha256']
p.save_json(packet, record)
print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), packet_sha256=p.sha(packet), index_sha256=p.sha(index),
    unique_payload_files=len(files), unique_payload_bytes=total, material_paths=len(material),
    packet_files_including_index_summary=len(files)+2, hierarchy_support_admitted=False)))
