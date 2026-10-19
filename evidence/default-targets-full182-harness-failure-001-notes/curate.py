"""Retain failed full182 and its separate test-harness-only correction."""
from pathlib import Path
import ast, datetime, hashlib, json, re, sys
ROOT = Path(__file__).resolve().parents[2]
notes = Path(__file__).resolve().parent
output = ROOT / 'evidence/default-targets-full182-harness-failure-001.json'
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
dependencies = []
for name, expected in [
    ('evidence/default-targets-implicit-resolution-003.json', '7d4dca7a75c0d17712f4ef6c758a372773d9e62d100adb88f5dab0879bed6bc6'),
    ('evidence/default-targets-full181-001.json', '32a00ddcfda35daa3956fb74343c499f291925117605eb83634f092b20cd2bf3'),
]:
    q = ROOT / name; assert p.sha(q) == expected
    j = f.read_json(q); index = ROOT / j['files_index']['path']
    assert p.sha(index) == j['files_index']['sha256']
    x = f.read_json(index)
    for row in x['files']: refs.setdefault(row['sha256'], row['path'])
    for row in x['material']: refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=expected, files_index=j['files_index']))
v2 = f.read_json(ROOT / dependencies[0]['path'])
base = ROOT / '.runs/full-integration-182'
protocol = f.read_json(base / 'protocol.json'); execution = f.read_json(base / 'execution.json')
HEAD = 'f2077c149b83eb3fea317dd89ba2791c71ef7b85'
assert protocol['tools']['git_head'] == HEAD and len(protocol['source_sha256']) == 295
assert protocol['bounds_seconds'] == 480
assert execution['passed'] is False and execution['sources_unchanged'] is True
assert execution['process']['status'] == 'nonzero_exit' and execution['process']['exit_code'] == 1
assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert p.sha(base / 'command.log') == execution['log_sha256'] == '973a668318e3b55884bffe24d0371e8b74c60d25cbf57b7253effe0f38e3a738'
log = (base / 'command.log').read_text()
assert re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', log, re.M) == [('2288', '372.375')]
assert re.findall(r'^FAILED \(errors=(\d+), skipped=(\d+)\)$', log, re.M) == [('2', '1')]
assert log.count("NameError: name 'observe_floors' is not defined") == 2
errors = re.findall(r'^ERROR: (.+)$', log, re.M)
assert len(errors) == 2 and all('test_four_copper_classes.FourCopperNativeCensus.' in e for e in errors)
controller = ROOT / '.runs/run-full-integration-182.py'
discovery = ROOT / protocol['discovery']
assert p.sha(controller) == execution['controller_sha256'] == '6032422f1de92f652adefd5938d3c5529a42f87253f289fb2602e4f5c33767ec'
assert p.sha(discovery) == protocol['discovery_sha256']
old_harness = ROOT / '.runs/raw-harness-before-fix-001.py'
new_harness = ROOT / 'tests/test_four_copper_classes.py'
OLD = '4d4244e169b19ad331799679d904e027ba24e6a6199668bd811f629472bf4881'
NEW = '3e94625367d269103df9875953c1bb5ebf60a8e873b43f784aec2fe0f40302da'
assert p.sha(old_harness) == OLD == protocol['source_sha256']['tests/test_four_copper_classes.py']
assert p.sha(new_harness) == NEW
target_stdout = ROOT / '.runs/default-targets-four-copper-harness-001.log'
target_time = ROOT / '.runs/default-targets-four-copper-harness-001-time.log'
assert target_stdout.read_bytes() == b''
target_text = target_time.read_text()
assert re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', target_text, re.M) == [('22', '0.250')]
assert re.findall(r'^OK$', target_text, re.M) == ['OK']
assert cost(target_time) == dict(wall_seconds=.36, CPU_seconds=.33)
external = cost(ROOT / '.runs/full-integration-182-time.log')
assert external == dict(wall_seconds=373.59, CPU_seconds=366.20)

selected = [(base / name, Path('failed182') / name)
            for name in ['protocol.json', 'execution.json', 'command.log']]
for q in [controller, discovery, ROOT / '.runs/full-integration-182-controller.log',
          ROOT / '.runs/full-integration-182-time.log']:
    selected.append((q, Path('controller-and-cost') / q.name))
selected += [(old_harness, Path('failed-source/tests/test_four_copper_classes.py')),
             (new_harness, Path('harness-only-correction/tests/test_four_copper_classes.py')),
             (target_stdout, Path('harness-only-correction') / target_stdout.name),
             (target_time, Path('harness-only-correction') / target_time.name)]
source_refs = []
for name, digest in v2['source_sha256'].items():
    assert protocol['source_sha256'][name] == digest and p.sha(ROOT / name) == digest
    q = ROOT / refs[digest]; assert p.sha(q) == digest
    selected.append((q, Path('v2-source') / name))
    source_refs.append(dict(source=name, sha256=digest, retained=refs[digest]))
license_sha = '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986'
license_path = refs[license_sha]; assert p.sha(ROOT / license_path) == license_sha
selected.append((ROOT / license_path, Path('rights/LICENSE')))
secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new_bytes = {}
for q, name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q, 4 * 1024**2)
    assert b'\0' not in raw and not secret.search(raw); raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in refs: new_bytes.setdefault(digest, len(raw))
assert sum(new_bytes.values()) + 256 * 1024 < 16 * 1024**2
for q, name in selected: retain(q, name)

scope = '''# Failed full182 and separate test-harness correction

Full182 at f207 ran 2,288 tests: two errors and one PowerShell skip. It failed,
with stable captured tools/source, untruncated log, nonzero exit and clean child
reaping. Both errors are NameError: observe_floors in the AST-extracted netclasses
test namespace. The old harness is the exact f207 protocol-pinned source retained
before editing; it is not reconstructed from the new test or a later product.

The correction changes only test_four_copper_classes.py: it injects the real
observe_floors helper and a scalar GetDesignSettings stand-in, then checks one
read and all five exact values. The separate targeted 22-test run passed. It is
not a repaired full182 pass or actual KiCad/Native API proof. The six v2 product
modules and three associated tests still match packet003 and the failed182 pins;
their published bytes are reused rather than duplicated. Full183 is required.

Complete external failure cost is 373.59 wall / 366.20 CPU seconds. Nested wrapper
and child observations are preserved but not added again. The corrective target
cost is a separate .36 wall / .33 CPU. Test stderr and time are in -time.log;
empty stdout is genuine and retained by hash reference. Target logs do not carry
an independent source-stability manifest, so they are not a substitute full gate.

No install011/runtime038/Native/GUI qualification occurred. GUI078 preparation
stays unexecuted and its old full182/HEAD prerequisites must be updated later.
Historical full181 passed only its old f54 scope; packet003 remains source and
constructed controls. No source field, original board, rule or problem was changed
to make this failure pass. New test plumbing does not qualify product behavior.

Only project-owned GPL code/tests and explicit local test/process metadata are
published; the GPL LICENSE is a verified prior payload link. No private CAD or
browser payload, downloaded tools, cache or unrelated archive is selected. This
curator executes no tests, Native, builds, GUI, CI, network or Git commands. Raw
originals remain unmodified on Mac. Curation/authoring cost is additional unmetered,
not zero. Essential text retention is not a full backup/restoration or release.
'''
with (notes / 'SCOPE.md').open('x') as stream: stream.write(scope)
for q in [Path(__file__), notes / 'SCOPE.md']:
    raw = q.read_bytes(); total += len(raw)
    files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
for row in material: assert p.sha(ROOT / row['original']) == row['sha256'] == p.sha(ROOT / row['retained'])
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
    v2_source_references=source_refs, preflight=dict(max_file_bytes=4 * 1024**2,
        packet_ceiling_bytes=16 * 1024**2, selected_material_secret_pattern_check=True,
        UTF8_no_NUL=True, selected_material_occurrences=len(selected), new_unique_bytes=sum(new_bytes.values()))))
summary = dict(schema=1, kind='default-targets-full182-failed-harness-and-test-only-correction',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=HEAD,
    full_suite_passed=False, tests=2288, errors=2, skips=1, unittest_seconds=372.375,
    source_and_tools_stable_during_run=True, captured_source_pins=295,
    error_tests=errors, error="NameError: name 'observe_floors' is not defined",
    cause='AST-extracted native.netclasses test namespace omitted its new observe_floors dependency; failure occurred in the scalar API-double harness, not an actual Native invocation.',
    failed_harness=dict(source='tests/test_four_copper_classes.py', sha256=OLD,
        exact_f207_protocol_match=True, original=str(old_harness.relative_to(ROOT))),
    harness_only_correction=dict(source='tests/test_four_copper_classes.py', sha256=NEW,
        change='Inject real observe_floors and scalar GetDesignSettings stand-in; assert one settings read and five exact values.',
        product_source_changed=False, targeted_tests=22, targeted_passed=True,
        unittest_seconds=.250, complete_external_cost=cost(target_time),
        test_double_is_not_Native_proof=True, does_not_repair_full182=True),
    complete_external_cost=dict(**external, user_seconds=306.66, system_seconds=59.54),
    controller_observation=dict(wall_seconds=execution['wall_seconds'], full_CPU_seconds=execution['full_cpu_seconds']),
    child_observation=dict(wall_seconds=execution['process']['wall_seconds'], CPU_seconds=execution['process']['cpu_seconds'],
        status='nonzero_exit', exit_code=1, cleanup_complete=True, log_truncated=False),
    accounting='External complete exit is authoritative; wrapper/child are nested and not added again. Corrective targeted cost is separate. Authoring/review/curation additional unmetered, notzero.',
    resource_guards=execution['process']['resource_guards'], resource_accounting=execution['process']['resource_accounting'],
    v2_sources_unchanged_from003=source_refs, dependencies=dependencies,
    install011_executed=False, runtime038_executed=False, Native_qualified=False,
    actual_GUI=False, GUI078_preparation_executed=False, production_qualified=False,
    routing_accepted=False, project_complete=False, human_review=False,
    next_gate='New checkpoint and full183 after this test-only correction; install011/current runtime/Native/GUI gates remain separate and unexecuted.',
    rights=dict(license='Repository GPL; project-owned source/tests and local test metadata only.', retained_LICENSE=license_path, LICENSE_sha256=license_sha),
    curation_helper=dict(path=str(helper.relative_to(ROOT)), sha256=p.sha(helper)),
    retention=dict(new_payload_files=len(files), new_payload_bytes=total, material_occurrences=len(material),
        reused_v2_source_files=9, no_original_edits=True, no_tests_Native_build_GUI_CI_network_Git_execution=True),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
p.save_json(output, summary)
physical = [q for q in notes.rglob('*') if q.is_file()] + [output]
assert sum(q.stat().st_size for q in physical) < 16 * 1024**2
for row in files: assert p.sha(ROOT / row['path']) == row['sha256']
print(json.dumps(dict(path=str(output.relative_to(ROOT)), sha256=p.sha(output),
    files_index_sha256=p.sha(notes / 'files.json'), physical_files=len(physical),
    physical_bytes=sum(q.stat().st_size for q in physical), new_payload_files=len(files),
    new_payload_bytes=total, material_occurrences=len(material), full182_passed=False,
    complete_external_cost=external, Native_qualified=False), sort_keys=True))
