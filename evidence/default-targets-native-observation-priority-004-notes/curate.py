"""Retain finite Native export observations and the narrow priority delta.

No Native, solver, test, build, GUI, network or Git execution by this curator.
Existing bounded retain/tree/cost functions are reused without running their
original controller. Selected bytes are preflighted before any payload copy.
"""
from pathlib import Path
import ast, datetime, hashlib, json, os, re, sys
ROOT = Path(__file__).resolve().parents[2]
notes = Path(__file__).resolve().parent
output = ROOT / 'evidence/default-targets-native-observation-priority-004.json'
assert not output.exists() and sorted(q.name for q in notes.iterdir()) == ['curate.py']
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / '.runs/runtime-directory-037/runtime'))
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
definitions = [n for n in ast.parse(helper.read_bytes()).body if isinstance(n, ast.FunctionDef)
               and n.name in {'retain', 'tree', 'cost'}]
assert {n.name for n in definitions} == {'retain', 'tree', 'cost'}
refs = {}; files = []; material = []; total = 0
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper), 'exec'))
real_retain = retain
selected = []
def retain(q, name): selected.append((Path(q), Path(name)))
dependencies = []
for name, expected in [
    ('evidence/default-targets-implicit-resolution-003.json', '7d4dca7a75c0d17712f4ef6c758a372773d9e62d100adb88f5dab0879bed6bc6'),
    ('evidence/default-targets-full182-harness-failure-001.json', '88f51f0500d9ef775aeaa3be6d30ea6a92a53b135db18143b0bedd55d3d4664f'),
]:
    q = ROOT / name; assert p.sha(q) == expected
    j = f.read_json(q); index = ROOT / j['files_index']['path']
    assert p.sha(index) == j['files_index']['sha256']
    x = f.read_json(index)
    for row in x['files']: refs.setdefault(row['sha256'], row['path'])
    for row in x['material']: refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=expected, files_index=j['files_index']))
v2 = f.read_json(ROOT / dependencies[0]['path'])
failure182 = f.read_json(ROOT / dependencies[1]['path'])
review = ROOT / '.runs/default-targets-priority-sentinel-review-001.json'
REVIEW = '7b558e4f3a315923ce4ec00efeabb5df8c670d0793925a184bfbe8733cd28e1f'
assert p.sha(review) == REVIEW
reviewed = f.read_json(review); assert reviewed['findings'] == []
changed = {
    'autorouter/default_targets.py': '5d3d514108944af63438e5f24b4a0f0384be28260d84107d8e60dbcf8ac089c2',
    'tests/test_default_targets.py': 'a97adb07c7178c1a2d523df884a8141be69b8a67048bbdd9e43ed7aac85f2ea6',
}
current_pins = {}
for name, row in reviewed['current_source_sha256'].items():
    assert p.sha(ROOT / name) == row['sha256'] and (ROOT / name).stat().st_size == row['bytes']
    current_pins[name] = row['sha256']
    if name in changed:
        assert row['sha256'] == changed[name]
        retain(ROOT / name, Path('current-source') / name)
    else:
        assert row['sha256'] == v2['source_sha256'][name]
        retain(ROOT / refs[row['sha256']], Path('unchanged-source') / name)
retain(review, Path('review') / review.name)
assert p.sha(ROOT / 'tests/test_four_copper_classes.py') == failure182['harness_only_correction']['sha256']

first = ROOT / '.runs/native-default-floor-observation-001'
second = ROOT / '.runs/native-default-floor-observation-002'
plan1 = f.read_json(first / 'protocol.json'); plan2 = f.read_json(second / 'protocol.json')
result2 = f.read_json(second / 'result.json')
assert not os.path.lexists(first / 'result.json') and not os.path.lexists(first / '4Cu')
assert result2['observation_passed'] is True and result2['installed_qualified'] is False
assert result2['routing_accepted'] is False and result2['actual_GUI'] is False
assert plan2['prior_protocol_sha256'] == p.sha(first / 'protocol.json')
assert result2['protocol_sha256'] == p.sha(second / 'protocol.json')
assert plan2['reuse'] == ['implicit', '2Cu'] and plan2['only_new_Native_case'] == '4Cu'
assert plan2['current_helper_sha256'] == changed['autorouter/default_targets.py']
assert plan1['toolchain']['mode'] == 'experimental-native-qualification'
assert plan1['toolchain']['expected_version'] == '10.0.7'
assert [row['label'] for row in plan1['cases']] == ['implicit', '2Cu', '4Cu']
assert [row['label'] for row in result2['cases']] == ['implicit', '2Cu', '4Cu']
assert p.sha(ROOT / '.runs/probe-native-default-floor-observation-001.py') == plan1['controller_sha256']
assert p.sha(ROOT / '.runs/resume-native-default-floor-observation-002.py') == plan2['controller_sha256']
rows = []
for source_case, row in zip(plan1['cases'], result2['cases']):
    label = row['label']; folder = (first if label in ('implicit', '2Cu') else second) / label
    assert row['directory'] == str(folder) and row['source_unchanged'] is True
    assert row['reused_prior_export'] is (label != '4Cu')
    source = Path(source_case['source']); board = folder / 'source' / source.name
    assert io.inventory(source.parent) == io.inventory(board.parent) == source_case['source_hashes']
    process = f.read_json(folder / 'process.json'); mapping = f.read_json(folder / 'native-map.json')
    for name, key in [('process.json', 'process_sha256'), ('native-map.json', 'map_sha256'), ('native.dsn', 'dsn_sha256')]:
        assert p.sha(folder / name) == row[key]
    assert process['status'] == 'success' and process['exit_code'] == 0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
    assert mapping['source'] == str(board) and mapping['board_sha256'] == p.sha(board)
    assert mapping['project_sha256'] == p.sha(board.with_suffix('.kicad_pro')) and mapping['board_saved'] is False
    assert mapping['native_version'] == '10.0.7'
    assert mapping['effective_floors_nm'] == row['dimensions']['original_floors_nm']
    priorities = sorted({parent['priority'] for net in mapping['nets'] for parent in net['parameter_parents'].values()})
    assert priorities == row['priorities']
    rows.append(dict(label=label, Native_export_invocation=1 if label in ('implicit', '2Cu') else 2,
        reused_in_002=row['reused_prior_export'], source=str(source.relative_to(ROOT)),
        source_hashes=source_case['source_hashes'], source_unchanged_verified_in002=True,
        current_original_and_copied_source_hashes_match=True, native_nets=len(mapping['nets']),
        map_sha256=row['map_sha256'], dsn_sha256=row['dsn_sha256'], process_sha256=row['process_sha256'],
        board_sha256=mapping['board_sha256'], project_sha256=mapping['project_sha256'],
        board_saved=False, priorities=priorities, dimensions=row['dimensions'],
        dimension_resolution=row['dimension_resolution'], Native_process=process,
        scope='Loaded-board export/map plus source scalar resolution only; not Native DRC/Route qualification.'))
    for rel in io.inventory(source.parent): retain(source.parent / rel, Path('original-inputs') / label / rel)
tree(first, Path('observation001')); tree(second, Path('observation002'))
for path, digest in plan1['worker_pins'].items():
    name = str(Path(path).relative_to(ROOT))
    q = ROOT / refs[digest] if digest in refs else Path(path)
    assert p.sha(q) == digest
    retain(q, Path('worker001-source') / name)

construction_root = ROOT / '.runs/default-floor-owned-controls-001'
construction = f.read_json(construction_root / 'construction.json')
generator = ROOT / '.runs/default-floor-owned-fixture-001.py'
assert p.sha(generator) == construction['generator_sha256']
factory = ROOT / construction['base_factory']['path']
assert p.sha(factory) == construction['base_factory']['sha256']
tree(construction_root, Path('owned-fixture'))
for q in [generator, ROOT / '.runs/default-floor-owned-fixture-001-authoring-original-001.py', factory]:
    retain(q, Path('fixture-controllers') / q.name)
for name in ['probe-native-default-floor-observation-001.py', 'resume-native-default-floor-observation-002.py',
             'native-default-floor-observation-001-controller.log', 'native-default-floor-observation-001-time.log',
             'native-default-floor-observation-002-controller.log', 'native-default-floor-observation-002-time.log',
             'default-targets-priority-targeted-001.log', 'default-targets-priority-targeted-001-time.log',
             'default-floor-owned-fixture-prepare-001.log', 'default-floor-owned-fixture-prepare-001-time.log',
             'default-floor-owned-fixture-prepare-002.log', 'default-floor-owned-fixture-prepare-002-time.log']:
    retain(ROOT / '.runs' / name, Path('controllers-and-cost') / name)
license_sha = construction['base_factory']['license_sha256']; license_path = refs[license_sha]
assert p.sha(ROOT / license_path) == license_sha
retain(ROOT / license_path, Path('rights/LICENSE'))
costs = {}
for label, name, expected in [
    ('observation001_failed', 'native-default-floor-observation-001-time.log', (1.68, 1.34)),
    ('observation002_resumption', 'native-default-floor-observation-002-time.log', (.74, .64)),
    ('targeted39', 'default-targets-priority-targeted-001-time.log', (1.45, 1.36)),
    ('fixture_preparation001_failed', 'default-floor-owned-fixture-prepare-001-time.log', (.36, .11)),
    ('fixture_preparation002', 'default-floor-owned-fixture-prepare-002-time.log', (.12, .10)),
]:
    costs[label] = cost(ROOT / '.runs' / name)
    assert costs[label] == dict(wall_seconds=expected[0], CPU_seconds=expected[1])
assert 'ValueError: Default parameter parent differs from raw source class' in (ROOT / '.runs/native-default-floor-observation-001-time.log').read_text()
targeted = (ROOT / '.runs/default-targets-priority-targeted-001-time.log').read_text()
assert re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', targeted, re.M) == [('39', '1.281')]
assert re.findall(r'^OK$', targeted, re.M) == ['OK']
replay_path = ROOT / '.runs/default-targets-actual-dsn-replay-001.json'
replay = f.read_json(replay_path)
assert replay['pure_replay_passed'] is True and replay['helper_sha256'] == changed['autorouter/default_targets.py']
assert replay['observation_receipt_sha256'] == p.sha(second / 'result.json')
assert [row['label'] for row in replay['cases']] == ['implicit', '2Cu', '4Cu']
for observation, replay_case in zip(rows, replay['cases']):
    assert replay_case['input_sha256'] == observation['dsn_sha256']
    assert replay_case['derived_nm'] == observation['dimensions']['derived_nm']
    assert replay_case['input_unchanged'] is True
for suffix in ('.json', '.log', '-time.log'):
    q = ROOT / '.runs' / ('default-targets-actual-dsn-replay-001' + suffix)
    retain(q, Path('pure-actual-input-replay') / q.name)
replay_cost = cost(ROOT / '.runs/default-targets-actual-dsn-replay-001-time.log')
assert replay_cost == dict(wall_seconds=.14, CPU_seconds=.10)

secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new_bytes = {}
for q, name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q, 4 * 1024**2)
    assert b'\0' not in raw and not secret.search(raw); raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in refs: new_bytes.setdefault(digest, len(raw))
assert sum(new_bytes.values()) + 256 * 1024 < 16 * 1024**2 and len(selected) < 2000
for q, name in selected: real_retain(q, name)

scope = '''# Native Default/floor observation and priority-sentinel correction004

Observation001 successfully exported the implicit smoke and owned2Cu sources with
the explicitly pinned experimental10.0.7 worker. The implicit scalar resolution
completed. Owned2Cu then refused in the old pure resolver at unanimous parent
priority-1. The controller stopped before that case's source checks/final checks;
no001 result or4Cu invocation existed. This failure is retained, not relabeled.

The narrow source correction permits-1 only when original source Default priority
is absent. Present priorities still require exact built-in integer0..INTMAX; every
parent/field/net must be Default, specified, exact-valued and unanimous. No source
priority, class or floor is written back. The39 constructed tests passed; source
and AI review are exact-pinned. AI source review is not human engineering review.

Observation002 reused both existing exports, executed only a new4Cu export, then
completed all three source-hash/map/Default/floor resolutions with unchanged inputs.
Smoke observed INTMAX priority; owned2Cu/4Cu observed-1. Maps retain exact raw
Default dimensions and effective loaded floors; derived planning dimensions are
stored separately. Both original and copied input inventories are retained and
rehash-match. This is three Native export invocations total, not five. Reused
process costs are references and are not added again to002's complete cost.
The separate pure transform/check replay on all three actual DSN/map/source inputs
also passed at .14 wall/.10 CPU. Its JSON/log/time retain input/output hashes;
this packet contains no separate replay controller or transformed-output DSN bytes.
It is a pure actual-input replay and performs no additional Native export.

Fixture preparation001 failed a pure layer-return assertion before project files
were created. Its original authoring source/log/cost remains visible. Preparation002
reused only the empty owned output root and generated GPL owned2/4Cu cases. Their
front/back SMD transition and authored below-floor Default/five floors are prospective
qualification controls, not benchmark families or proved routed/protected outcomes.

No Route, import, engine, refill, DRC, fullSCH parity, install011/runtime038, GUI,
production support or routing/quality improvement is qualified here. Smoke's input
has no schematic and is used only for this API precondition. Full182 remains failed;
new complete-source full/integration/install/Native and GUI gates remain separate.
The new4Cu harness is unchanged from its separately retained182 correction packet.

Only owned GPL fixture/source/test payload and explicit process/controller metadata
are selected; exact base factory and GPL LICENSE are preserved/hash-linked. No
downloaded apps/JRE/JAR, private CAD/browser data or unrelated archive is published.
This curator performs no Native, test, build, GUI, CI, network or Git execution and
changes no original source/project. All external complete costs are separate from
nested process observations; authoring/review/curation CPU is additional unmetered,
notzero. Essential text retention is not a full raw backup/restoration or release.
'''
with (notes / 'SCOPE.md').open('x') as stream: stream.write(scope)
for q in [Path(__file__), notes / 'SCOPE.md']:
    raw = q.read_bytes(); total += len(raw)
    files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
for row in material: assert p.sha(ROOT / row['original']) == row['sha256'] == p.sha(ROOT / row['retained'])
assert p.sha(review) == REVIEW
for name, digest in current_pins.items(): assert p.sha(ROOT / name) == digest
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
    preflight=dict(max_file_bytes=4 * 1024**2, packet_ceiling_bytes=16 * 1024**2,
        selected_material_secret_pattern_check=True, UTF8_no_NUL=True,
        selected_material_occurrences=len(selected), new_unique_bytes=sum(new_bytes.values())),
    exclusions=['Native applications/Python shared libraries/downloaded engine/venv and isolated caches/configuration are not distributed.',
                'No Route/import/refill/DRC/install/GUI artifacts exist for this limited observation; no missing stage is fabricated.']))
summary = dict(schema=1, kind='Native-Default-floor-API-observation-and-priority-sentinel-correction',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    accepted=False, routing_accepted=False, production_qualified=False, Native_routing_qualified=False,
    installed_qualified=False, actual_GUI=False, project_complete=False, human_review=False,
    Native_qualified=False,
    limited_Native_export_scalar_precondition_passed=True, Native_export_invocations=3,
    toolchain=plan1['toolchain'], current_source_sha256=current_pins, changed_source_sha256=changed,
    observation001=dict(status='failed in pure2Cu resolver after two successful Native exports',
        error='Default parameter parent differs from raw source class',
        implicit_scalar_resolution_completed=True, owned2Cu_export_completed=True,
        four_copper='NOTRUN', result_published=False, final_source_tool_checks_reached=False,
        failed_case_source_check_reached=False, complete_external_cost=costs['observation001_failed']),
    observation002=dict(observation_passed=True, reused_exports=['implicit', '2Cu'],
        only_new_Native_export='4Cu', source_hash_checks_completed=3,
        original_and_copied_sources_unchanged=True, complete_external_cost=costs['observation002_resumption'],
        sampled_wall_seconds=result2['sampled_wall_seconds'], sampled_full_CPU_seconds=result2['sampled_full_CPU_seconds']),
    cases=rows,
    source_delta='Allow Native parent priority-1 only if original sole-Default source priority is absent. Explicit0..INTMAX exactness, scalar types/values and all-row/all-field unanimity remain mandatory; no source writeback.',
    targeted=dict(tests=39, passed=True, unittest_seconds=1.281, complete_external_cost=costs['targeted39'],
        scope='Constructed source guards; not Native routing or installed qualification.'),
    pure_actual_input_replay=dict(passed=True, result_sha256=p.sha(replay_path),
        helper_sha256=replay['helper_sha256'], observation_receipt_sha256=replay['observation_receipt_sha256'],
        cases=replay['cases'], complete_external_cost=replay_cost,
        new_Native_invocations=0,
        retention_limit='JSON/log/time and input/output hashes retained; separate replay controller and transformed-output DSN bytes not included.',
        scope='Pure transform/check on retained actual inputs; not routing/import/refill/DRC/install qualification.'),
    fixture_preparation=dict(preparation001='Failed pure ID/name-pair assertion before any project creation; original source retained.',
        preparation002='Reused still-empty owned root; generated two paired GPL fixtures without Native.',
        construction_sha256=p.sha(construction_root / 'construction.json'), generator_sha256=p.sha(generator),
        failed001_cost=costs['fixture_preparation001_failed'], successful002_cost=costs['fixture_preparation002'],
        independent_benchmark_families=False, actual_required_via_routing='NOTRUN'),
    review=dict(path=str(review.relative_to(ROOT)), sha256=REVIEW, findings=[],
        disposition=reviewed['disposition'], current_source_pins_match=True, human_review=False),
    unchanged_four_copper_harness=dict(sha256=failure182['harness_only_correction']['sha256'], packet=dependencies[1]['path'],
        retested_in_this_slice=False),
    stages_not_run=['Route/engine', 'session import', 'zone refill', 'Native DRC/fullSCH parity',
                    'install011/runtime038', 'GUI', 'invalid/cancel/delivery qualification'],
    accounting='Complete external costs are separate actual events. Nested/reused Native process costs are observations only and are not added again. Review/authoring/curation costs additional unmetered, notzero.',
    remaining=['Fresh complete source full suite', 'Isolated selected7 installation/smoke',
        'Actual guided2/4Cu Route/import/refill/final/fullSCH/source/protected/floor and invalid/cancel/export controls',
        'Fresh GUI for changed build and other broader project gates'],
    dependencies=dependencies,
    rights=dict(grant=construction['base_factory']['grant'], retained_LICENSE=license_path, LICENSE_sha256=license_sha,
        inputs='Project-owned generated fixtures and owned smoke source only; no private or third-party CAD payload.'),
    curation_helper=dict(path=str(helper.relative_to(ROOT)), sha256=p.sha(helper)),
    retention=dict(new_payload_files=len(files), new_payload_bytes=total, material_occurrences=len(material),
        no_original_edits=True, no_Native_tests_build_GUI_CI_network_Git_execution=True),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
p.save_json(output, summary)
physical = [q for q in notes.rglob('*') if q.is_file()] + [output]
assert sum(q.stat().st_size for q in physical) < 16 * 1024**2
for row in files: assert p.sha(ROOT / row['path']) == row['sha256']
print(json.dumps(dict(path=str(output.relative_to(ROOT)), sha256=p.sha(output),
    files_index_sha256=p.sha(notes / 'files.json'), physical_files=len(physical),
    physical_bytes=sum(q.stat().st_size for q in physical), new_payload_files=len(files),
    new_payload_bytes=total, material_occurrences=len(material), Native_export_invocations=3,
    Native_routing_qualified=False), sort_keys=True))
