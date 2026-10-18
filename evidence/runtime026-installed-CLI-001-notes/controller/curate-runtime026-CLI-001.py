"""Curate completed runtime026 controller deliveries, never run or admit a job.

Run only after the lead has confirmed the selected bounded process was reaped.
Reuse the existing runtime022 curation pattern and exact public byte references.
"""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.runs/runtime-directory-026/runtime'))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, provenance as pv, sexpr as sx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--case', choices=('whole', 'partial'), required=True)
args = parser.parse_args()
partial = args.case == 'partial'
suffix = '-partial' if partial else ''
case_name = 'partial' if partial else 'cli'
delivery_name = 'partial' if partial else 'production'
expected_route_seconds = 90 if partial else 420
expected_export_seconds = 90 if partial else 120
expected_protected = 4 if partial else 10
expected_warnings = 0 if partial else 6
BASE = ROOT / '.runs/runtime-directory-026'
RUNTIME = BASE / 'runtime'
CASE = BASE / (case_name + '-workflow-001-run')
OUT = RUNTIME / '.runs' / (delivery_name + '-delivery-001')
NOTES = ROOT / ('evidence/runtime026-installed' + suffix + '-CLI-001-notes')
SUMMARY = ROOT / ('evidence/runtime026-installed' + suffix + '-CLI-001.json')
EXPECTED_HEAD = '1117de080524072046a61522845facd5d4c68575'


def load(path):
    return json.loads(path.read_bytes())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Existing evidence differs: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(raw)


def measured_exit(path):
    values = dict(line.split() for line in path.read_text().splitlines() if line.strip())
    assert set(values) == {'real', 'user', 'sys'}
    values = {key: float(value) for key, value in values.items()}
    assert all(math.isfinite(value) and value >= 0 for value in values.values())
    return dict(wall_seconds=values['real'], user_seconds=values['user'],
                system_seconds=values['sys'], full_cpu_seconds=round(values['user'] + values['sys'], 2),
                resolution_seconds=0.01, measurement='External /usr/bin/time -p, complete process exit')


outer = load(CASE / 'execution.json')
protocol = load(CASE / 'protocol.json')
child = load(OUT / 'result.json')
setup = load(BASE / 'setup.json')
assert outer['passed'] and outer['sources_unchanged'] and child['workflow_delivered']
assert outer['process']['status'] == 'success' and outer['process']['exit_code'] == 0
assert outer['process']['cleanup_complete'] is True
assert outer['source_head'] == setup['source_head'] == EXPECTED_HEAD
assert setup['prepared'] and setup['installed_doctor'] and setup['immutable_module_count'] == 45
assert p.sha(OUT / 'result.json') == outer['child_receipt_sha256']
assert p.sha(CASE / 'protocol.json') == outer['protocol_sha256']
assert p.sha(RUNTIME / pv.MANIFEST) == setup['manifest_sha256'] == protocol['runtime_manifest_sha256']
assert child['settings']['seconds'] == protocol['route_seconds'] == expected_route_seconds
assert child['tools']['git_head'] == EXPECTED_HEAD
assert len(child['tools']['implementation_sha256']) == 45
assert child['actual_GUI'] is False and child['human_review'] is False
assert child['whole_budget_seconds'] == 240 and protocol['external_bound_seconds'] == 260
complete = measured_exit(ROOT / '.runs' / ('runtime026-' + ('partial' if partial else 'whole') + '-CLI-001-time.log'))
preparation_complete = measured_exit(ROOT / '.runs/runtime026-prepare-001-time.log')
assert max(complete['wall_seconds'], complete['full_cpu_seconds']) <= protocol['external_bound_seconds']
work = Path(child['workspace'])
source = Path(child['source'])
original = sx.read(source)
route = load(work / 'route/result.json')
export = load(work / 'export/export.json')
assert p.c.ROOT == RUNTIME and p.c.NATIVE_VERSION == '10.0.7'
with p.validation_readback_session():
    assert p.check_result(work/'route/result.json')['current'] is True
    from autorouter import review_export as ex
    assert ex.check_export(work/'export/export.json')['current'] is True
assert route['accepted'] is True and route['budget_seconds'] == expected_route_seconds
assert export['export_accepted'] is True and export['budget_seconds'] == expected_export_seconds
assert child['route_readback']['current'] is True and child['export_readback']['current'] is True
assert p.tree_hash(source.parent) == child['source_hashes'] == protocol['source_hashes']
assert json.loads((work / 'settings.json').read_bytes()) == child['settings']
expected_stages = ('preview', 'route', 'review', 'choice', 'export', 'verify_export')
assert tuple(row['stage'] for row in child['processes']) == expected_stages
for row in child['processes']:
    process = row['process']
    assert process['exit_code'] == 0 and process['cancel_requested'] is False
    assert process['log_truncated'] is False
    assert p.sha(OUT / (row['stage'] + '.log')) == row['log_sha256']
    argv = process['argv']
    if row['stage'] == 'route':
        assert argv[4] == 'route' and argv[argv.index('--settings') + 1] == str(work / 'settings.json')
    if row['stage'] == 'export':
        assert argv[4] == 'review-export'
        assert float(argv[argv.index('--seconds') + 1]) == expected_export_seconds

# Reference identical bytes in the two established022 packets. No archive scan.
references = {}
reference_records = []
for name in ('runtime022-installed-CLI-001.json', 'runtime022-installed-partial-CLI-001.json'):
    path = ROOT / 'evidence' / name
    previous = load(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path)))
    for row in previous['files']:
        references.setdefault(row['sha256'], row['path'])
whole_summary = ROOT / 'evidence/runtime026-installed-CLI-001.json'
if partial:
    whole = load(whole_summary)
    assert whole['passed'] and whole['source_head'] == EXPECTED_HEAD
    reference_records.append(dict(path=str(whole_summary.relative_to(ROOT)), sha256=p.sha(whole_summary)))
    for row in whole['files']:
        references.setdefault(row['sha256'], row['path'])
files, material = [], []
new_bytes = 0


def copy(path, target):
    global new_bytes
    raw = path.read_bytes()
    assert path.is_file() and not path.is_symlink() and len(raw) < 4 * 1024 ** 2 and b'\0' not in raw
    raw.decode('utf-8')
    pin = digest(raw)
    public = references.get(pin)
    if public is None:
        destination = NOTES / target
        publish(destination, raw)
        public = str(destination.relative_to(ROOT))
        references[pin] = public
        files.append(dict(path=public, bytes=len(raw), sha256=pin))
        new_bytes += len(raw)
        assert new_bytes < 12 * 1024 ** 2 and len(files) < 500
    else:
        assert p.sha(ROOT / public) == pin
    material.append(dict(original=str(path.relative_to(ROOT)), retained=public, bytes=len(raw), sha256=pin))


for name in ('setup.json', 'doctor-process.json', 'doctor.log'):
    copy(BASE / name, Path('preparation') / name)
copy(RUNTIME / pv.MANIFEST, Path('preparation') / pv.MANIFEST)
for name in ('runtime026-prepare-001-time.log',):
    copy(ROOT / '.runs' / name, Path('preparation') / name)
for name in ('protocol.json', 'process.json', 'execution.json', 'command.log'):
    copy(CASE / name, Path('controller') / name)
if (CASE / 'settings.json').is_file():
    copy(CASE / 'settings.json', Path('controller/settings.json'))
copy(ROOT / '.runs' / ('run-runtime026-' + case_name + '-workflow-001.py'), Path('controller/driver.py'))
copy(ROOT / '.runs' / ('runtime026-' + ('partial' if partial else 'whole') + '-CLI-001-time.log'), Path('controller/complete-exit-time.log'))
copy(OUT / 'result.json', Path('workflow/result.json'))
for path in sorted(OUT.glob('*.log')):
    copy(path, Path('workflow') / path.name)
copy(work / 'settings.json', Path('workflow/captured-settings.json'))
for name in child['source_hashes']:
    copy(source.parent / name, Path('original') / name)
finals = []
protected = p.protected_for_record(route, original)
assert len(protected) == expected_protected
for label, folder, data in (('route', work / 'route', route), ('export', work / 'export/validation', export)):
    candidate = Path(data['candidate'])
    tree = sx.read(candidate)
    assert data['metrics']['version']=='10.0.7'
    assert p.sha(candidate) == data['candidate_sha256']
    assert p.immutable(tree) == p.immutable(original)
    assert all(item in p.routes(tree) for item in protected)
    assert [data['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, expected_warnings, 0]
    assert data['schematic_parity'] == 'checked by final native DRC'
    assert p.sha(folder / 'final-drc.json') == data['native_report_sha256']
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix in ('.json', '.log', '.net'):
            copy(path, Path(label) / path.name)
    for path in sorted(candidate.parent.iterdir()):
        if path.is_file() and path.suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_prl', '.kicad_sch', '.kicad_dru'):
            copy(path, Path(label) / 'candidate' / path.name)
    finals.append(dict(stage=label, candidate_sha256=data['candidate_sha256'],
        native_report_sha256=data['native_report_sha256'], native=data['native'], metrics=data['metrics'],
        protected_routes=len(protected), protected_routes_unchanged=True,
        schematic_parity=data['schematic_parity'], original_nonrouting_design_preserved=True))
copy(work / 'export/export.json', Path('export/export.json'))
for folder, name in (('review', 'review.json'), ('choice', 'choice.json')):
    copy(work / folder / name, Path(folder) / name)
assert p.tree_hash(source.parent) == child['source_hashes']

scope = f'''# Runtime026 installed {'partial' if partial else 'four-copper-layer'} CLI workflow

This packet retains the completed six-stage installed controller workflow: preview, routing, rendered review generation, software accept intent, fresh Native export and checked export. It exercises the actual production Request/Workflow/CliJob and CLI code, not an actual wx window, toolbar interaction, human review or physical/electrical qualification. Software acceptance intent is test state.

The captured routing allocation is {expected_route_seconds} seconds; the separate Native export-validation allocation is {expected_export_seconds} seconds. Neither rewrites the routing settings. The qualification controller retains its own 240-second wall/full-CPU delivery cap and the outer supervisor has a 260-second bound; these bounds are separate from the captured routing and export allocations. All actual processes, repeated readbacks and delivery work are counted in the complete external time. Runtime preparation and installed doctor costs are separate and retained. Authoring, AI review and curation are additional, not measured as zero.

Both route and export carry their own fresh KiCad10.0.7 Native checks, complete schematic proof, original rules and semantic checks. Each retains {expected_protected} protected route items. Native results are 0 opens, 0 blocking findings, {expected_warnings} warnings and 0 exclusions; all original ignored checks remain visible. The source project bytes remain unchanged. This is an exposed owned fixture regression, not a routing-quality gain, board-family breadth result or generalized superiority claim.

Files with new proof paths are retained; identical owned CAD/source bytes and preparation files reference exact existing public copies through files.json. Runtime source is the verified immutable commit {EXPECTED_HEAD}; the manifest and all 45 module pins are retained, without copying the runtime source tree again. No engine, interpreter, application, .venv, generated config/cache/documents, private board or binary asset is copied. Original022 evidence and raw results remain unchanged. The packet is not a relocated standalone executable proof, full raw-workspace backup or new restoration test. Newer raw artifacts remain on this Mac and are not retroactively covered by older backups.

Fixture and controller code are project-owned under the repository LICENSE. No Windows, clean-OS installation, GUI qualification, human engineer review, fabrication, live application or formal-release claim follows from this packet.
'''
publish(NOTES / 'SCOPE.md', scope.encode())
copy(NOTES / 'SCOPE.md', Path('SCOPE.md'))
copy(Path(__file__).resolve(), Path('controller/curate-runtime026-CLI-001.py'))
index = dict(schema=1, files=files, material=material,
             scope='Exact byte curation only. Source, candidate and repeated stage files may reference identical prior public bytes. No acceptance or Native verifier is introduced.')
publish(NOTES / 'files.json', (json.dumps(index, indent=2) + '\n').encode())
full_path = ROOT / '.runs/full-integration-167/execution.json'
assert p.sha(full_path) == setup['full167_sha256']
full = load(full_path)
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
record = dict(schema=1,
    kind='actual-runtime026-mixed-lock-free-via-alias-partial-installed-CLI-v1' if partial else 'actual-runtime026-protected-four-cu-installed-CLI-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=True,
    curation_note='Fresh026 curation uses its own completed six-stage Native deliveries and full167 module pins.025 GUI failure and earlier curation history remain separate and unchanged. Byte readbacks introduce no new Native execution.',
    project_complete=False, accepted=False, actual_GUI=False, human_review=False,
    routing_quality_improvement_claim=False, source_head=outer['source_head'],
    runtime_manifest_sha256=setup['manifest_sha256'], immutable_module_count=45,
    runtime_module_sha256=child['tools']['implementation_sha256'],
    full_integration=dict(raw_receipt=str(full_path.relative_to(ROOT)), sha256=setup['full167_sha256'], passed=True),
    complete_controller=complete,
    complete_controller_wall_seconds=complete['wall_seconds'], complete_controller_cpu_seconds=complete['full_cpu_seconds'],
    stored_enclosure_sample=dict(wall_seconds=outer['whole_wall_seconds'], full_cpu_seconds=outer['whole_full_cpu_seconds']),
    runtime_preparation=dict(source_head=setup['source_head'], manifest_sha256=setup['manifest_sha256'],
        prepared=setup['prepared'], installed_doctor=setup['installed_doctor'],
        stored_sample_wall_seconds=setup['wall_seconds'], stored_sample_full_cpu_seconds=setup['full_CPU_seconds'],
        complete_exit=preparation_complete,
        cost_scope='Separate preparation/installed doctor cost; not hidden in or added to nested workflow CPU.'),
    budgets=dict(captured_routing_seconds=expected_route_seconds, separate_export_validation_seconds=expected_export_seconds,
        controller_wall_full_cpu_cap_seconds=child['whole_budget_seconds'], supervisor_wall_seconds=protocol['external_bound_seconds']),
    workflow=['preview', 'route', 'rendered review generation', 'software accept intent', 'fresh Native export', 'checked export'],
    processes=child['processes'], own_final_proofs=finals, source_hashes=child['source_hashes'],
    original_source_project_bytes_unchanged=True, route_readback=child['route_readback'], export_readback=child['export_readback'],
    whole_project_drc_clean=export['whole_project_drc_clean'],
    producer_helper=dict(path='scripts/qualify_runtime_workflow.py', source_head=EXPECTED_HEAD,
        sha256=protocol['helper_sha256'], bound_child_driver_sha256=child['driver_sha256']),
    accounting='Complete external wall/user/system exit measurements include actual conversion, routing, validation, rendered review, test intent, export, repeated checks, publication and exit. Stored earlier samples remain separate; never sum nested process CPU. Authoring, AI review and curation costs are additional and uninstrumented, not zero.',
    limits=['Actual GUI is not exercised by this packet. No toolbar/window/human qualification claim.',
        'Owned exposed regression fixture only; no comparative routing-quality, completion-breadth or electrical suitability claim.',
        'Same pinned Mac/applications/cache/fixed runtime path; no Windows, clean-OS, relocation or standalone-install claim.',
        'Essential proof bytes only; no full-workspace backup or restoration test. Raw artifacts remain on this Mac. Older backups do not cover new artifacts retroactively.'],
    reference_records=reference_records, files=files,
    files_index=dict(path=str((NOTES / 'files.json').relative_to(ROOT)), sha256=p.sha(NOTES / 'files.json')),
    new_material_bytes=new_bytes)
publish(SUMMARY, (json.dumps(record, indent=2) + '\n').encode())
print(json.dumps(dict(case=args.case, summary=str(SUMMARY.relative_to(ROOT)), summary_sha256=p.sha(SUMMARY),
                     files_index_sha256=record['files_index']['sha256'], files=len(files), bytes=new_bytes,
                     complete_controller=complete, actual_GUI=False)))
