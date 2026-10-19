"""Retain the completed full181 test event; no tests or Native execution."""
from pathlib import Path
import ast, datetime, hashlib, json, re, sys
ROOT = Path(__file__).resolve().parents[2]
notes = Path(__file__).resolve().parent
output = ROOT / 'evidence/default-targets-full181-001.json'
assert not output.exists()
assert sorted(q.name for q in notes.iterdir()) == ['curate.py']
sys.dont_write_bytecode = True
# Immutable prior runtime supplies only the established read/hash/save helpers.
sys.path.insert(0, str(ROOT / '.runs/runtime-directory-037/runtime'))
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
definitions = [n for n in ast.parse(helper.read_bytes()).body
               if isinstance(n, ast.FunctionDef) and n.name in {'retain', 'tree', 'cost'}]
assert {n.name for n in definitions} == {'retain', 'tree', 'cost'}
refs = {}; files = []; material = []; total = 0
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper), 'exec'))

dependencies = []
for name, expected in [
    ('evidence/default-targets-integration-correction-002.json', '49990479ac677638f5bee214ea22c16350ef5ccf7fe5c05580b4837f6b024c60'),
    ('evidence/default-targets-integration-draft-001.json', 'd9b4298a71025f559d53902489f69cb627e84df0c33564cbbf3ccac55709e22d'),
]:
    q = ROOT / name
    assert p.sha(q) == expected
    j = f.read_json(q); idx = ROOT / j['files_index']['path']
    assert p.sha(idx) == j['files_index']['sha256']
    x = f.read_json(idx)
    for row in x.get('files', []): refs.setdefault(row['sha256'], row['path'])
    for row in x.get('material', []): refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=expected, files_index=j['files_index']))

base = ROOT / '.runs/full-integration-181'
protocol = f.read_json(base / 'protocol.json')
execution = f.read_json(base / 'execution.json')
assert protocol['tools']['git_head'] == 'f54cefbc80ad70b4fabd67d7dd18e9d9affdae98'
assert execution['passed'] is True and execution['sources_unchanged'] is True
assert execution['process']['status'] == 'success' and execution['process']['exit_code'] == 0
assert execution['process']['cleanup_complete'] is True
assert execution['process']['log_truncated'] is False
assert protocol['bounds_seconds'] == 480
assert len(protocol['source_sha256']) == 295
log = base / 'command.log'
assert p.sha(log) == execution['log_sha256'] == 'c84cbb423fea49d261cacd9e1b3cf04fb1e0621b6f098618353393217d7275a0'
text = log.read_text()
assert re.findall(r'^Ran (\d+) tests in ([\d.]+)s$', text, re.M) == [('2281', '384.628')]
assert re.findall(r'^OK \(skipped=(\d+)\)$', text, re.M) == ['1']
skip = [line for line in text.splitlines() if ' ... skipped ' in line]
assert len(skip) == 1 and 'PowerShell absent; mocked script execution remains unrun' in skip[0]
controller = ROOT / '.runs/run-full-integration-181.py'
discovery = ROOT / protocol['discovery']
assert p.sha(controller) == execution['controller_sha256'] == '527a7667bdb93e66d00a8582a42713241b06a1cfd4fa878072b4d75c36855e34'
assert p.sha(discovery) == protocol['discovery_sha256'] == 'fa41a94d258e17a63272c2e3af2c58d7808b34240d6786356b9156e231d1b815'

selected = [(base / name, Path('actual181') / name)
            for name in ['protocol.json', 'execution.json', 'command.log']]
for q in [controller, discovery, ROOT / '.runs/full-integration-181-controller.log',
          ROOT / '.runs/full-integration-181-time.log']:
    selected.append((q, Path('controller-and-cost') / q.name))
source_bytes = []
for name in ['autorouter/default_targets.py', 'autorouter/netclass.py',
             'autorouter/pipeline.py', 'autorouter/review_export.py',
             'tests/test_default_targets.py', 'tests/test_default_target_integration.py']:
    digest = protocol['source_sha256'][name]
    q = ROOT / refs[digest]
    assert p.sha(q) == digest
    selected.append((q, Path('source') / name))
    source_bytes.append(dict(source=name, sha256=digest, retained=refs[digest],
        relation='Exact full181 protocol pin; prior immutable public payload reused.'))

secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new = {}
for q, name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q, 4 * 1024**2)
    assert b'\0' not in raw and not secret.search(raw)
    raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in refs: new.setdefault(digest, len(raw))
assert sum(new.values()) + 256 * 1024 < 16 * 1024**2
for q, name in selected: retain(q, name)

scope = '''# Default targets: completed full181, exact f54 source

This is the completed 2,281-test / one-skip integration event. The complete
untruncated log, protocol, execution, controller, discovery, controller stdout
and external timing are retained byte-for-byte. Six relevant module/test sources
are exact hash references to the previous correction002/draft001 payloads, not
copies of evolving working source. All 295 tested source pins remain in protocol.
Unrelated code and downloaded tools are not duplicated. Project-owned code/tests
are covered by the repository GPL and prior source packets; logs contain owned
local test/process metadata, not private board/browser inputs or credentials.

The suite passed at f54cefbc80ad70b4fabd67d7dd18e9d9affdae98 with source stability
and clean child reaping. PowerShell was absent; its mocked script execution is
the one skipped test. The outer wall/CPU cost is 386.04/377.27 seconds; wrapper
and nested subprocess observations are retained but are not added a second time.
Resource guards are polling bounds, not OS memory quotas; their limitations are
preserved in execution.json.

A later static inspection by the lead found an implicit-Default compatibility
blocker: the normal corrected7 single-Default selector admits the valid minimal
fixtures/smoke/smoke.kicad_pro, which omits net_settings.classes and
design_settings.rules. The f54 source_dimensions helper requires explicit fields
and would refuse before routing. This is a static finding, not an actual failed
install/Native run. Full181 neither covers nor resolves that case. A proposed
same-load Native absent-field observation correction is outside this packet.

No install011/runtime038, Native, GUI, routing, Windows, family improvement or
production qualification follows from this test result. No new test/Native/build/
GUI/CI/network/Git execution occurred during curation. Authoring/curation cost is
additional and unmetered, not zero. Original raw evidence remains unmodified on
Mac; this is essential text retention, not a full raw backup or restoration test.
'''
with (notes / 'SCOPE.md').open('x') as stream: stream.write(scope)
for q in [Path(__file__), notes / 'SCOPE.md']:
    raw = q.read_bytes()
    files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    total += len(raw)
for row in material:
    assert p.sha(ROOT / row['original']) == row['sha256'] == p.sha(ROOT / row['retained'])
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
    exact_tested_source_bytes=source_bytes,
    exclusions=['Unrelated old module/test payloads: exact full181 SHA inventory retained in protocol, not recopied.',
                'Installed tools/JRE/JAR/venv, caches, datasets and unrelated historical runs: not selected or published.'],
    preflight=dict(selected_material_occurrences=len(selected), new_unique_bytes=sum(new.values()),
        UTF8_no_NUL=True, selected_material_secret_pattern_check=True,
        max_file_bytes=4 * 1024**2, packet_ceiling_bytes=16 * 1024**2)))
external = cost(ROOT / '.runs/full-integration-181-time.log')
assert external == dict(wall_seconds=386.04, CPU_seconds=377.27)
summary = dict(schema=1, kind='default-targets-full181-completed-test-evidence',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=protocol['tools']['git_head'], full_suite_passed=True,
    sources_unchanged_during_run=True, tests=2281, skips=1,
    skip_reason='PowerShell absent; mocked script execution remains unrun',
    unittest_seconds=384.628, source_pin_count=295, exact_relevant_source_bytes=source_bytes,
    complete_external_cost=dict(**external, user_seconds=315.61, system_seconds=61.66),
    controller_observation=dict(wall_seconds=execution['wall_seconds'],
        full_CPU_seconds=execution['full_cpu_seconds']),
    child_observation=dict(wall_seconds=execution['process']['wall_seconds'],
        CPU_seconds=execution['process']['cpu_seconds'],
        cleanup_complete=True, exit_code=0, log_truncated=False),
    accounting='External complete exit is authoritative. Controller/child observations are nested and not added again; authoring/curation costs are additional unmetered, notzero.',
    bounds=dict(seconds=480, resource_guards=execution['process']['resource_guards'],
        resource_accounting=execution['process']['resource_accounting']),
    later_static_blocker=dict(status='Unresolved by full181', actual_failed_Native_or_install_run=False,
        source='fixtures/smoke/smoke.kicad_pro',
        finding='Normal corrected7 single-Default selector admits this valid minimal source, which omits net_settings.classes and design_settings.rules; f54 source_dimensions requires explicit fields and would refuse before routing.',
        basis='Lead static source inspection after full181; no rerun performed for this record.',
        fix_scope='Proposed same-load pinned Native observations for absent fields, preserving source bytes; not part of this test result.'),
    installation_qualified=False, Native_qualified=False, actual_GUI=False,
    production_qualified=False, routing_accepted=False, project_complete=False,
    human_review=False, physical_electrical_validation=False,
    install011_or_runtime038_executed=False,
    limitations='Passing source tests do not close the later implicit-Default compatibility blocker or qualify installed Native, GUI, Windows, broader completion/quality or release. No source changes or new execution during curation.',
    dependencies=dependencies,
    retention=dict(new_payload_files=len(files), new_payload_bytes=total,
        material_occurrences=len(material), source_payloads_reused=6,
        scope='Finite actual181 outputs and exact relevant source references only; raw originals unchanged.'),
    curation_helper=dict(path=str(helper.relative_to(ROOT)), sha256=p.sha(helper)),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
p.save_json(output, summary)
physical = [q for q in notes.rglob('*') if q.is_file()] + [output]
assert sum(q.stat().st_size for q in physical) < 16 * 1024**2
for row in files: assert p.sha(ROOT / row['path']) == row['sha256']
print(json.dumps(dict(summary=str(output.relative_to(ROOT)), sha256=p.sha(output),
    files_index_sha256=p.sha(notes / 'files.json'), physical_files=len(physical),
    physical_bytes=sum(q.stat().st_size for q in physical),
    new_payload_files=len(files), new_payload_bytes=total, material_occurrences=len(material),
    complete_external_cost=external, Native_qualified=False), sort_keys=True))
